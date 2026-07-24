"""Build a deterministic exception queue and summary from Resolver artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from traffic_simulation.network.resolve_osm_attributes import AUDIT_FIELDS
from traffic_simulation.paths import REPOSITORY_ROOT


EXCEPTION_FIELDS = (
    *AUDIT_FIELDS,
    "failure_code",
    "formal_blocker",
    "failure_message",
)
REVIEW_EXCEPTION_STATES = {
    "conflict",
    "invalid",
    "unresolved",
    "valid_but_unsupported",
}


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside the repository: {path}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ordered_counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _failure_key(failure: Mapping[str, Any]) -> tuple[str, str]:
    parts = str(failure.get("location", "")).split("/")
    if len(parts) != 4 or parts[:2] != ["osm", "way"]:
        raise ValueError(f"unsupported Resolver failure location: {failure.get('location')}")
    return parts[2], parts[3]


def build_outputs(
    audit_path: Path,
    failure_report_path: Path,
    permission_expectations_path: Path,
    input_osm_path: Path,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    with audit_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != AUDIT_FIELDS:
            raise ValueError("audit CSV columns do not match the governed contract")
        audit_rows = list(reader)

    failure_report = _load_json(failure_report_path)
    permissions = _load_json(permission_expectations_path)
    failures = failure_report.get("failures")
    if not isinstance(failures, list):
        raise ValueError("failure report must contain a failures array")
    failure_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for failure in failures:
        if not isinstance(failure, dict):
            raise ValueError("failure report contains a non-object failure")
        key = _failure_key(failure)
        if key in failure_by_key:
            raise ValueError(f"duplicate Resolver failure location: {key}")
        failure_by_key[key] = failure

    stop_rows = [row for row in audit_rows if row["decision"] == "stop"]
    stop_keys = {(row["osm_way_id"], row["attribute"]) for row in stop_rows}
    if stop_keys != set(failure_by_key):
        raise ValueError("audit stop rows and failure report locations do not match")

    exception_rows: list[dict[str, str]] = []
    for row in stop_rows:
        failure = failure_by_key[(row["osm_way_id"], row["attribute"])]
        exception_rows.append(
            {
                **row,
                "failure_code": str(failure["code"]),
                "formal_blocker": str(failure["formal_blocker"]).lower(),
                "failure_message": str(failure["message"]),
            }
        )

    oneway_rows = [row for row in audit_rows if row["attribute"] == "oneway"]
    review_rows = [
        row for row in stop_rows if row["value_state"] in REVIEW_EXCEPTION_STATES
    ]
    summary = {
        "artifact_type": "resolver_dry_run_summary",
        "schema_version": 1,
        "config_id": failure_report.get("config_id"),
        "config_version": failure_report.get("config_version"),
        "profile": permissions.get("profile"),
        "inputs": {
            "input_osm": {
                "path": _relative_path(input_osm_path),
                "sha256": _sha256(input_osm_path),
            },
            "audit": {
                "path": _relative_path(audit_path),
                "sha256": _sha256(audit_path),
            },
            "failure_report": {
                "path": _relative_path(failure_report_path),
                "sha256": _sha256(failure_report_path),
            },
            "permission_expectations": {
                "path": _relative_path(permission_expectations_path),
                "sha256": _sha256(permission_expectations_path),
            },
        },
        "counts": {
            "candidate_way_count": len(oneway_rows),
            "audit_row_count": len(audit_rows),
            "stop_row_count": len(stop_rows),
            "stop_way_count": len({row["osm_way_id"] for row in stop_rows}),
            "bulk_missing_row_count": sum(
                row["value_state"] == "missing" for row in stop_rows
            ),
            "rule_or_data_exception_row_count": len(review_rows),
            "permission_way_count": len(permissions.get("ways", [])),
            "permission_blocker_count": len(permissions.get("blockers", [])),
            "permission_complete": permissions.get("complete"),
            "normalized_osm_published": False,
        },
        "distributions": {
            "decision": _ordered_counts(row["decision"] for row in audit_rows),
            "value_state": _ordered_counts(row["value_state"] for row in audit_rows),
            "failure_code": _ordered_counts(
                row["failure_code"] for row in exception_rows
            ),
            "stop_attribute": _ordered_counts(row["attribute"] for row in stop_rows),
            "stop_highway": _ordered_counts(row["highway"] for row in stop_rows),
            "oneway_value_state": _ordered_counts(
                row["value_state"] for row in oneway_rows
            ),
            "oneway_derivation_method": _ordered_counts(
                row["derivation_method"] for row in oneway_rows
            ),
            "review_exception_state": _ordered_counts(
                row["value_state"] for row in review_rows
            ),
            "review_exception_attribute_state": _ordered_counts(
                f"{row['attribute']}|{row['value_state']}" for row in review_rows
            ),
            "review_exception_derivation_method": _ordered_counts(
                row["derivation_method"] for row in review_rows
            ),
        },
    }
    return exception_rows, summary


def _write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".part",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=EXCEPTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".part",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize one governed Resolver Dry Run"
    )
    parser.add_argument("--audit-csv", required=True, type=Path)
    parser.add_argument("--failure-report-json", required=True, type=Path)
    parser.add_argument("--permission-expectations-json", required=True, type=Path)
    parser.add_argument("--input-osm", required=True, type=Path)
    parser.add_argument("--exception-queue-csv", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = (
        args.audit_csv,
        args.failure_report_json,
        args.permission_expectations_json,
        args.input_osm,
        args.exception_queue_csv,
        args.summary_json,
    )
    for path in paths:
        _relative_path(path)
    rows, summary = build_outputs(
        args.audit_csv,
        args.failure_report_json,
        args.permission_expectations_json,
        args.input_osm,
    )
    _write_csv(args.exception_queue_csv, rows)
    summary["outputs"] = {
        "exception_queue": {
            "path": _relative_path(args.exception_queue_csv),
            "sha256": _sha256(args.exception_queue_csv),
        }
    }
    _write_json(args.summary_json, summary)
    print(json.dumps(summary["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
