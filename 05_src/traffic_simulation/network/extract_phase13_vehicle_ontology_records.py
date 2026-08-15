"""Extract Phase 13 vehicle-ontology records from the fixed Phase 12 inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import yaml


TARGET_BASE_KEYS = ("psv", "motorcar", "horse")
TARGET_STOP_CODE = "ACCESS_VEHICLE_HIERARCHY_MISSING"


class ExtractionError(RuntimeError):
    """Raised when a fixed-input or extraction invariant is violated."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _semantic_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExtractionError(f"JSON root must be an object: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExtractionError(f"YAML root must be an object: {path}")
    return value


def _locked_artifact(lock: Mapping[str, Any], artifact_id: str) -> Mapping[str, Any]:
    matches = [
        item
        for item in lock["publication"]["artifacts"]
        if item["artifact_id"] == artifact_id
    ]
    if len(matches) != 1:
        raise ExtractionError(f"fixed artifact is not unique: {artifact_id}")
    return matches[0]


def _target_occurrences(tags: Mapping[str, str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source_key in sorted(tags):
        base_key = source_key.split(":", 1)[0]
        if base_key not in TARGET_BASE_KEYS:
            continue
        parts = source_key.split(":")
        result.append(
            {
                "base_key": base_key,
                "source_key": source_key,
                "source_value": tags[source_key],
                "direction_scope": next(
                    (part for part in parts if part in {"forward", "backward"}),
                    "both",
                ),
                "lane_scoped": "lanes" in parts,
            }
        )
    return result


def extract_records(
    *,
    input_lock_path: Path,
    inventory_path: Path,
    formal_population_path: Path,
    osm_path: Path,
) -> dict[str, Any]:
    lock = _load_yaml(input_lock_path)
    if lock.get("status") != "fixed" or not lock["publication"].get("locked"):
        raise ExtractionError("Phase 13 input lock is not fixed and locked")

    locked_inventory = _locked_artifact(lock, "complete_blocker_inventory")
    actual_inventory_sha256 = _sha256(inventory_path)
    if actual_inventory_sha256 != locked_inventory["byte_sha256"]:
        raise ExtractionError("blocker inventory byte SHA-256 differs from input lock")

    inventory = _load_json(inventory_path)
    if inventory.get("semantic_sha256") != locked_inventory["semantic_sha256"]:
        raise ExtractionError("blocker inventory semantic SHA-256 differs from input lock")

    population = _load_json(formal_population_path)
    locked_population = _locked_artifact(lock, "formal_full_population")
    actual_population_sha256 = _sha256(formal_population_path)
    if actual_population_sha256 != locked_population["byte_sha256"]:
        raise ExtractionError("formal full population byte SHA-256 differs from input lock")
    if population.get("semantic_sha256") != locked_population["semantic_sha256"]:
        raise ExtractionError(
            "formal full population semantic SHA-256 differs from input lock"
        )
    source = population["stage_outputs"]["static_access"]["source"]
    actual_osm_sha256 = _sha256(osm_path)
    if actual_osm_sha256 != source["sha256"]:
        raise ExtractionError("OSM source SHA-256 differs from fixed formal population")

    inventory_entries = {
        int(item["source_way_id"]): item
        for item in inventory["entries"]
        if item["stop_code"] == TARGET_STOP_CODE
    }
    if len(inventory_entries) != 492:
        raise ExtractionError(
            f"expected 492 fixed vehicle-ontology blockers, got {len(inventory_entries)}"
        )

    records: list[dict[str, Any]] = []
    for _event, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way":
            source_way_id = int(element.attrib["id"])
            inventory_entry = inventory_entries.get(source_way_id)
            if inventory_entry is not None:
                tags = {
                    item.attrib["k"]: item.attrib["v"]
                    for item in element.findall("tag")
                }
                occurrences = _target_occurrences(tags)
                if occurrences:
                    # The resolver visits source keys in lexical order. After the
                    # already-approved empty-domain rule, the first remaining target
                    # occurrence is therefore the observed probe blocker.
                    selected = occurrences[0]
                    records.append(
                        {
                            "source_way_id": source_way_id,
                            "blocker_id": inventory_entry["blocker_id"],
                            "record_id": inventory_entry["record_id"],
                            "attribute_name": inventory_entry["attribute_name"],
                            "stop_code": inventory_entry["stop_code"],
                            "root_cause_category": inventory_entry[
                                "root_cause_category"
                            ],
                            "selected_blocking_base_key_after_decision_001": selected[
                                "base_key"
                            ],
                            "selected_blocking_source_key_after_decision_001": selected[
                                "source_key"
                            ],
                            "target_occurrences": occurrences,
                            "source_tags": dict(sorted(tags.items())),
                        }
                    )
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()

    records.sort(key=lambda item: item["source_way_id"])
    selected_counts = Counter(
        item["selected_blocking_base_key_after_decision_001"] for item in records
    )
    membership_counts = Counter(
        occurrence["base_key"]
        for item in records
        for occurrence in item["target_occurrences"]
    )
    way_membership_counts = Counter(
        base_key
        for item in records
        for base_key in {
            occurrence["base_key"] for occurrence in item["target_occurrences"]
        }
    )
    expected_selected = {"horse": 130, "motorcar": 154, "psv": 16}
    if dict(sorted(selected_counts.items())) != expected_selected:
        raise ExtractionError(
            "post-decision selected counts differ: "
            f"{dict(sorted(selected_counts.items()))}"
        )

    result = {
        "schema_version": 1,
        "extraction_id": "phase13_psv_motorcar_horse_fixed_blocker_records_20260814",
        "status": "extracted_from_fixed_input",
        "input_lock": {
            "input_lock_id": lock["input_lock_id"],
            "path": str(input_lock_path),
            "status": lock["status"],
        },
        "sources": {
            "complete_blocker_inventory": {
                "path": str(inventory_path),
                "inventory_id": inventory["inventory_id"],
                "byte_sha256": actual_inventory_sha256,
                "semantic_sha256": inventory["semantic_sha256"],
            },
            "formal_full_population": {
                "path": str(formal_population_path),
                "byte_sha256": actual_population_sha256,
                "semantic_sha256": population["semantic_sha256"],
            },
            "osm_population": {
                "path": str(osm_path),
                "byte_sha256": actual_osm_sha256,
                "population_version": inventory["population_version"],
            },
        },
        "selection": {
            "inventory_stop_code": TARGET_STOP_CODE,
            "fixed_inventory_candidate_count": len(inventory_entries),
            "target_base_keys": list(TARGET_BASE_KEYS),
            "source_key_matching_rule": "source_key.split(':', 1)[0] in target_base_keys",
            "post_decision_rule": "lexically_first_remaining_target_source_key",
        },
        "counts": {
            "unique_source_ways": len(records),
            "selected_blocker_after_decision_001": dict(
                sorted(selected_counts.items())
            ),
            "source_way_memberships": dict(sorted(way_membership_counts.items())),
            "source_key_occurrences": dict(sorted(membership_counts.items())),
            "multi_target_source_ways": sum(
                len(
                    {
                        occurrence["base_key"]
                        for occurrence in item["target_occurrences"]
                    }
                )
                > 1
                for item in records
            ),
        },
        "interpretation": {
            "record_unit": "one fixed blocker inventory source Way",
            "membership_counts_are_not_additive": True,
            "reason": "A source Way may contain more than one target base key.",
            "phase13_probe_counts_reproduced": True,
            "ontology_decisions_completed": False,
        },
        "managed_scenario_context": population["stage_outputs"]["static_access"][
            "managed_scenario_context"
        ],
        "records": records,
    }
    result["semantic_sha256"] = _semantic_sha256(result)
    return result


def _write_csv(path: Path, records: list[Mapping[str, Any]]) -> None:
    fields = [
        "source_way_id",
        "blocker_id",
        "record_id",
        "stop_code",
        "root_cause_category",
        "selected_blocking_base_key_after_decision_001",
        "selected_blocking_source_key_after_decision_001",
        "target_source_keys_and_values_json",
        "source_tags_json",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in records:
            writer.writerow(
                {
                    **{field: item[field] for field in fields[:7]},
                    "target_source_keys_and_values_json": json.dumps(
                        item["target_occurrences"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "source_tags_json": json.dumps(
                        item["source_tags"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-lock", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--formal-full-population", type=Path, required=True)
    parser.add_argument("--osm", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    result = extract_records(
        input_lock_path=args.input_lock,
        inventory_path=args.inventory,
        formal_population_path=args.formal_full_population,
        osm_path=args.osm,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(args.output_csv, result["records"])
    print(f"extraction_status={result['status']}")
    print(f"unique_source_ways={result['counts']['unique_source_ways']}")
    for key, count in result["counts"]["selected_blocker_after_decision_001"].items():
        print(f"selected_{key}={count}")
    print(f"output_json={args.output_json}")
    print(f"output_csv={args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
