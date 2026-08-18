"""Audit the Phase 13 motorcar full-population probe."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


EXPECTED_DOMAIN = [
    "passenger",
    "taxi",
    "bus",
    "coach",
    "delivery",
    "truck",
]
SUCCESSOR_WAYS = {783347228, 1051964008}


class MotorcarProbeComparisonError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:static_access:static_access:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def _canonical_records(records, excluded_ways):
    selected = [
        item for item in records
        if int(item["source_way_id"]) not in excluded_ways
    ]
    return sorted(
        selected,
        key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False),
    )


def compare(
    *,
    extraction_path: Path,
    baseline_path: Path,
    probe_path: Path,
) -> dict[str, Any]:

    extraction = _load(extraction_path)
    baseline = _load(baseline_path)
    probe = _load(probe_path)

    motorcar_records = [
        item for item in extraction["records"]
        if item["selected_blocking_base_key_after_decision_001"] == "motorcar"
    ]

    if len(motorcar_records) != 154:
        raise MotorcarProbeComparisonError(
            f"expected 154 fixed motorcar records, got {len(motorcar_records)}"
        )

    fixed_ways = {int(item["source_way_id"]) for item in motorcar_records}
    affected_ways = fixed_ways | SUCCESSOR_WAYS

    expected_osm_sha = extraction["sources"]["osm_population"]["byte_sha256"]

    if baseline["source"]["sha256"] != expected_osm_sha:
        raise MotorcarProbeComparisonError("baseline OSM differs from fixed extraction")

    if probe["source"]["sha256"] != expected_osm_sha:
        raise MotorcarProbeComparisonError("probe OSM differs from fixed extraction")

    baseline_blockers = {
        int(item["source_way_id"]): item
        for item in baseline["blockers"]
    }
    current_blockers = {
        int(item["source_way_id"]): item
        for item in probe["blockers"]
    }

    baseline_affected = {
        way_id: baseline_blockers[way_id]
        for way_id in affected_ways
        if way_id in baseline_blockers
    }

    current_affected = {
        way_id: current_blockers[way_id]
        for way_id in affected_ways
        if way_id in current_blockers
    }

    baseline_motorcar_hierarchy = [
        item for item in baseline["blockers"]
        if item["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING"
        and "motorcar" in item.get("message", "")
    ]

    current_motorcar_hierarchy = [
        item for item in probe["blockers"]
        if item["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING"
        and "motorcar" in item.get("message", "")
    ]

    baseline_ids = {_blocker_id(item) for item in baseline["blockers"]}
    current_ids = {_blocker_id(item) for item in probe["blockers"]}

    new_blocker_ids = sorted(current_ids - baseline_ids)
    removed_blocker_ids = sorted(baseline_ids - current_ids)

    expected_removed_ids = sorted(
        _blocker_id(item)
        for item in baseline_affected.values()
    )

    # Outside the 156 expected motorcar-affected Ways, normalized rules
    # and final static maxima must remain byte-semantically identical.
    unaffected_normalized_equal = (
        _canonical_records(baseline["normalized_rules"], affected_ways)
        == _canonical_records(probe["normalized_rules"], affected_ways)
    )

    unaffected_maxima_equal = (
        _canonical_records(baseline["static_maxima"], affected_ways)
        == _canonical_records(probe["static_maxima"], affected_ways)
    )

    normalized_by_way = {
        int(item["source_way_id"]): item
        for item in probe["normalized_rules"]
    }

    missing_motorcar_rules = []
    wrong_domains = []

    for way_id in sorted(affected_ways):
        record = normalized_by_way.get(way_id)

        if record is None:
            missing_motorcar_rules.append(way_id)
            continue

        motorcar_rules = [
            rule for rule in record["rules"]
            if rule["source_key"].split(":", 1)[0] == "motorcar"
        ]

        if not motorcar_rules:
            missing_motorcar_rules.append(way_id)
            continue

        for rule in motorcar_rules:
            if sorted(rule["vehicle_domain"]) != sorted(EXPECTED_DOMAIN):
                wrong_domains.append(
                    {
                        "source_way_id": way_id,
                        "source_key": rule["source_key"],
                        "vehicle_domain": rule["vehicle_domain"],
                    }
                )

    acceptance = {
        "fixed_motorcar_record_count_is_154":
            len(motorcar_records) == 154,
        "expected_affected_way_count_is_156":
            len(affected_ways) == 156,
        "baseline_motorcar_hierarchy_blocker_count_is_156":
            len(baseline_motorcar_hierarchy) == 156,
        "current_motorcar_hierarchy_blockers_are_zero":
            len(current_motorcar_hierarchy) == 0,
        "all_affected_ways_are_unblocked":
            len(current_affected) == 0,
        "new_blocker_ids_are_zero":
            len(new_blocker_ids) == 0,
        "removed_blocker_ids_are_exactly_expected":
            removed_blocker_ids == expected_removed_ids,
        "unaffected_normalized_rules_unchanged":
            unaffected_normalized_equal,
        "unaffected_static_maxima_unchanged":
            unaffected_maxima_equal,
        "all_affected_ways_preserve_motorcar_rule":
            len(missing_motorcar_rules) == 0,
        "all_motorcar_rules_use_exact_governed_domain":
            len(wrong_domains) == 0,
    }

    result = {
        "schema_version": 1,
        "comparison_id": "phase13_motorcar_full_population_stable_id_diff_20260818",
        "decision_id": "DEC-P13-MOTORCAR-ONTOLOGY-001",
        "status": "passed" if all(acceptance.values()) else "failed",
        "sources": {
            "extraction": {
                "path": str(extraction_path),
                "byte_sha256": _sha256(extraction_path),
            },
            "baseline_probe": {
                "path": str(baseline_path),
                "byte_sha256": _sha256(baseline_path),
            },
            "motorcar_probe": {
                "path": str(probe_path),
                "byte_sha256": _sha256(probe_path),
            },
        },
        "stable_id_diff": {
            "fixed_motorcar_record_count": len(motorcar_records),
            "fixed_motorcar_way_count": len(fixed_ways),
            "successor_way_count": len(SUCCESSOR_WAYS),
            "affected_way_count": len(affected_ways),
            "baseline_motorcar_hierarchy_blocker_count":
                len(baseline_motorcar_hierarchy),
            "remaining_motorcar_hierarchy_blocker_count":
                len(current_motorcar_hierarchy),
            "remaining_affected_blocked_way_count":
                len(current_affected),
            "new_blocker_id_count": len(new_blocker_ids),
            "removed_blocker_id_count": len(removed_blocker_ids),
            "new_blocker_ids": new_blocker_ids,
            "removed_blocker_ids": removed_blocker_ids,
        },
        "permission_guard": {
            "unaffected_normalized_rules_unchanged":
                unaffected_normalized_equal,
            "unaffected_static_maxima_unchanged":
                unaffected_maxima_equal,
            "missing_motorcar_rule_ways":
                missing_motorcar_rules,
            "wrong_motorcar_domains":
                wrong_domains,
        },
        "acceptance": acceptance,
    }

    payload = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    result["semantic_sha256"] = hashlib.sha256(payload).hexdigest()

    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    result = compare(
        extraction_path=args.extraction,
        baseline_path=args.baseline,
        probe_path=args.probe,
    )

    if args.output.exists():
        raise FileExistsError(
            f"refusing to overwrite comparison artifact: {args.output}"
        )

    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": result["status"],
        "stable_id_diff": {
            key: value
            for key, value in result["stable_id_diff"].items()
            if key.endswith("_count")
        },
        "permission_guard": result["permission_guard"],
        "acceptance": result["acceptance"],
    }, ensure_ascii=False, indent=2, sort_keys=True))

    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
