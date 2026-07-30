"""Classify governed Resolver exception rows with fail-closed rules."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DEFAULT_TABLE = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "resolver_exception_decision_table.yml"
)


class ExceptionClassificationError(ValueError):
    """Raised when the decision table or its application is not deterministic."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ExceptionClassificationError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_table(path: Path = DEFAULT_TABLE) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.load(handle, Loader=_UniqueKeyLoader)
    if not isinstance(value, dict):
        raise ExceptionClassificationError("decision table root must be a mapping")
    return value


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def select_exception_population(
    rows: Iterable[Mapping[str, str]], table: Mapping[str, Any]
) -> list[Mapping[str, str]]:
    policy = table["baseline"]["exception_population"]
    states = set(policy["included_value_states"])
    selected = [
        row
        for row in rows
        if row["decision"] == policy["decision"]
        and row["formal_blocker"].lower() == str(policy["formal_blocker"]).lower()
        and row["value_state"] in states
    ]
    return selected


def _source_tags(row: Mapping[str, str]) -> Mapping[str, Any] | None:
    try:
        parsed = json.loads(row["source_value"])
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def row_matches_entry(
    row: Mapping[str, str], entry: Mapping[str, Any]
) -> bool:
    if row["attribute"] != entry["attribute"]:
        return False
    if row["value_state"] != entry["observed_state"]:
        return False
    if row["failure_code"] != entry["failure_code"]:
        return False

    for field, expected in entry["match"].items():
        if field == "source_tags":
            tags = _source_tags(row)
            if tags is None or any(tags.get(key) != value for key, value in expected.items()):
                return False
        elif row.get(field) != str(expected):
            return False
    return True


def matching_rule_ids(
    row: Mapping[str, str], entries: Iterable[Mapping[str, Any]]
) -> list[str]:
    return [
        str(entry["id"])
        for entry in entries
        if row_matches_entry(row, entry)
    ]


def classify_rows(
    rows: Iterable[Mapping[str, str]], table: Mapping[str, Any]
) -> list[dict[str, str]]:
    entries = table["entries"]
    results: list[dict[str, str]] = []
    errors: list[str] = []
    for row in rows:
        matched = matching_rule_ids(row, entries)
        locator = (
            f"way={row.get('osm_way_id', '<missing>')} "
            f"attribute={row.get('attribute', '<missing>')}"
        )
        if len(matched) != 1:
            errors.append(f"{locator}: matched {len(matched)} rules {matched}")
            continue
        results.append(
            {
                "osm_way_id": row["osm_way_id"],
                "attribute": row["attribute"],
                "rule_id": matched[0],
            }
        )
    if errors:
        preview = "\n".join(errors[:20])
        suffix = "" if len(errors) <= 20 else f"\n... {len(errors) - 20} more"
        raise ExceptionClassificationError(preview + suffix)
    return results


def validate_baseline(
    table_path: Path = DEFAULT_TABLE,
    queue_path: Path | None = None,
) -> dict[str, Any]:
    table = load_table(table_path)
    baseline = table["baseline"]
    resolved_queue = queue_path or REPOSITORY_ROOT / baseline["exception_queue"]
    actual_sha256 = sha256_file(resolved_queue)
    if actual_sha256 != baseline["exception_queue_sha256"]:
        raise ExceptionClassificationError(
            "exception queue SHA-256 mismatch: "
            f"expected {baseline['exception_queue_sha256']}, got {actual_sha256}"
        )

    selected = select_exception_population(load_csv_rows(resolved_queue), table)
    expected_rows = baseline["rule_or_data_exception_rows"]
    if len(selected) != expected_rows:
        raise ExceptionClassificationError(
            f"selected {len(selected)} rows, expected {expected_rows}"
        )

    classified = classify_rows(selected, table)
    counts = Counter(record["rule_id"] for record in classified)
    expected_counts = {
        entry["id"]: entry["baseline_rows"] for entry in table["entries"]
    }
    if dict(counts) != expected_counts:
        raise ExceptionClassificationError(
            f"per-rule counts differ: expected {expected_counts}, got {dict(counts)}"
        )

    return {
        "decision_table_id": table["decision_table_id"],
        "decision_table_sha256": sha256_file(table_path),
        "exception_queue_sha256": actual_sha256,
        "selected_rows": len(selected),
        "classified_rows": len(classified),
        "unmatched_rows": 0,
        "overlapping_rows": 0,
        "exactly_one_rule_per_row": True,
        "counts_by_rule": dict(sorted(counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate one-to-one classification of Resolver exception rows."
    )
    parser.add_argument("--decision-table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--exception-queue", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = validate_baseline(args.decision_table, args.exception_queue)
    text = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
