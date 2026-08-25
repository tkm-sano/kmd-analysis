"""Audit the Phase 13 bicycle=use_sidepath full-population probe."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


EXPECTED_GOVERNED_VCLASSES = [
    "passenger",
    "taxi",
    "bus",
    "coach",
    "delivery",
    "truck",
    "motorcycle",
]


class UseSidepathProbeComparisonError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise UseSidepathProbeComparisonError(f"JSON root is not an object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise UseSidepathProbeComparisonError(f"YAML root is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _probe_semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {
        "normalized_rules": copy.deepcopy(value.get("normalized_rules", [])),
        "static_maxima": copy.deepcopy(value.get("static_maxima", [])),
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:static_access:static_access:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def _canonical_records(records: Sequence[Mapping[str, Any]], excluded: set[int]):
    return sorted(
        [
            copy.deepcopy(item)
            for item in records
            if int(item["source_way_id"]) not in excluded
        ],
        key=lambda item: _canonical_bytes(item),
    )


def _source_tags(source_path: Path, target_ids: set[int]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for _, element in ET.iterparse(source_path, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in target_ids:
                result[way_id] = {
                    tag.attrib["k"]: tag.attrib["v"]
                    for tag in element.findall("tag")
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return result


def compare(
    *,
    decision_path: Path,
    registry_path: Path,
    baseline_path: Path,
    probe_path: Path,
    source_osm_path: Path,
) -> dict[str, Any]:
    decision = _yaml(decision_path)
    registry = _yaml(registry_path)
    baseline = _json(baseline_path)
    probe = _json(probe_path)
    fixed = decision["fixed_population"]
    affected = {int(value) for value in fixed["source_way_ids"]}

    if len(affected) != 27:
        raise UseSidepathProbeComparisonError(
            f"expected 27 fixed C1 Ways, got {len(affected)}"
        )
    if _sha256(baseline_path) != fixed["baseline_probe_byte_sha256"]:
        raise UseSidepathProbeComparisonError("baseline probe differs from decision")
    if _sha256(source_osm_path) != fixed["source_osm_byte_sha256"]:
        raise UseSidepathProbeComparisonError("source OSM differs from decision")
    if baseline["source"]["sha256"] != fixed["source_osm_byte_sha256"]:
        raise UseSidepathProbeComparisonError("baseline source OSM hash differs")
    if probe["source"]["sha256"] != fixed["source_osm_byte_sha256"]:
        raise UseSidepathProbeComparisonError("probe source OSM hash differs")
    if probe["semantic_sha256"] != _probe_semantic_hash(probe):
        raise UseSidepathProbeComparisonError("probe semantic hash is invalid")

    baseline_ids = {_blocker_id(item) for item in baseline["blockers"]}
    current_ids = {_blocker_id(item) for item in probe["blockers"]}
    baseline_by_way = {
        int(item["source_way_id"]): item for item in baseline["blockers"]
    }
    current_by_way = {
        int(item["source_way_id"]): item for item in probe["blockers"]
    }
    baseline_c1 = {
        way_id: baseline_by_way[way_id]
        for way_id in affected
        if way_id in baseline_by_way
    }
    current_c1 = {
        way_id: current_by_way[way_id]
        for way_id in affected
        if way_id in current_by_way
    }
    expected_removed_ids = sorted(
        _blocker_id(item) for item in baseline_c1.values()
    )
    removed_ids = sorted(baseline_ids - current_ids)
    new_ids = sorted(current_ids - baseline_ids)

    unaffected_normalized_equal = _canonical_records(
        baseline["normalized_rules"], affected
    ) == _canonical_records(probe["normalized_rules"], affected)
    unaffected_maxima_equal = _canonical_records(
        baseline["static_maxima"], affected
    ) == _canonical_records(probe["static_maxima"], affected)
    unaffected_blocker_ids_equal = (
        baseline_ids - set(expected_removed_ids) == current_ids
    )

    normalized_by_way = {
        int(item["source_way_id"]): item for item in probe["normalized_rules"]
    }
    missing_rules: list[int] = []
    invalid_rules: list[dict[str, Any]] = []
    c1_rule_ids: set[str] = set()
    for way_id in sorted(affected):
        record = normalized_by_way.get(way_id)
        rules = [] if record is None else [
            item
            for item in record["rules"]
            if item["source_key"] == "bicycle"
            and item["source_value"] == "use_sidepath"
        ]
        if len(rules) != 1:
            missing_rules.append(way_id)
            continue
        rule = rules[0]
        c1_rule_ids.add(rule["rule_id"])
        provenance = rule["provenance"]
        if (
            rule["vehicle_domain"] != []
            or provenance.get("access_value_semantics")
            != "parallel_way_required"
            or provenance.get("permission_effect_on_governed_vclasses") != "none"
            or provenance.get("source_value_rewritten") is not False
        ):
            invalid_rules.append({"source_way_id": way_id, "rule": rule})

    maxima_citing_c1 = [
        item
        for item in probe["static_maxima"]
        if set(item["maximal_rule_ids"]) & c1_rule_ids
    ]

    use_sidepath_registry = next(
        item
        for item in registry["access_values"]
        if item["source_value"] == "use_sidepath"
    )
    governed_vclasses = registry["vehicle_ontology"]["governed_vclasses"]
    motorcar_hierarchy = [
        item
        for item in probe["blockers"]
        if item["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING"
        and "motorcar" in item.get("message", "")
    ]

    source_ids = affected | {
        int(item["source_way_id"]) for item in probe["blockers"]
    }
    tags_by_way = _source_tags(source_osm_path, source_ids)
    fixed_source_tags_valid = all(
        tags_by_way.get(way_id, {}).get("bicycle") == "use_sidepath"
        for way_id in affected
    )
    successor_records = []
    for item in probe["blockers"]:
        way_id = int(item["source_way_id"])
        successor_records.append(
            {
                "source_way_id": way_id,
                "stop_code": item["stop_code"],
                "message": item.get("message"),
                "source_tags": tags_by_way.get(way_id, {}),
                "is_new_stable_id": _blocker_id(item) in new_ids,
            }
        )
    successor_records.sort(key=lambda item: (item["source_way_id"], item["stop_code"]))
    c2_specificity_exposed = any(
        item["stop_code"] == "ACCESS_SPECIFICITY_CONFLICT"
        and item["source_tags"].get("foot") == "use_sidepath"
        for item in successor_records
    )

    acceptance = {
        "expected_affected_way_count_is_27": len(affected) == 27,
        "baseline_c1_access_value_blocker_count_is_27": (
            len(baseline_c1) == 27
            and all(
                item["stop_code"] == "ACCESS_VALUE_UNSUPPORTED"
                for item in baseline_c1.values()
            )
        ),
        "c1_access_value_blockers_are_zero": len(current_c1) == 0,
        "removed_blocker_ids_are_exactly_expected": (
            removed_ids == expected_removed_ids
        ),
        "new_blocker_ids_are_zero": len(new_ids) == 0,
        "unaffected_blocker_ids_unchanged": unaffected_blocker_ids_equal,
        "unaffected_normalized_rules_unchanged": unaffected_normalized_equal,
        "unaffected_static_maxima_unchanged": unaffected_maxima_equal,
        "all_c1_source_rules_preserved": len(missing_rules) == 0,
        "all_c1_rules_have_approved_semantics": len(invalid_rules) == 0,
        "c1_rules_do_not_change_governed_static_maxima": (
            len(maxima_citing_c1) == 0
        ),
        "source_osm_unchanged": fixed_source_tags_valid,
        "bicycle_vehicle_domain_remains_empty": (
            registry["vehicle_ontology"]["domains"]["bicycle"] == []
        ),
        "governed_vclasses_unchanged": (
            governed_vclasses == EXPECTED_GOVERNED_VCLASSES
        ),
        "motorcar_hierarchy_blockers_remain_zero": len(motorcar_hierarchy) == 0,
        "registry_is_key_scoped_without_way_exceptions": (
            "bicycle" in use_sidepath_registry["applicable_base_keys"]
            and "source_way_ids" not in use_sidepath_registry
        ),
    }

    result = {
        "schema_version": 1,
        "comparison_id": (
            "phase13_bicycle_use_sidepath_full_population_stable_id_diff_20260820"
        ),
        "decision_id": decision["decision_id"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "sources": {
            "decision": {"path": str(decision_path), "byte_sha256": _sha256(decision_path)},
            "registry": {"path": str(registry_path), "byte_sha256": _sha256(registry_path)},
            "baseline_probe": {"path": str(baseline_path), "byte_sha256": _sha256(baseline_path)},
            "probe": {"path": str(probe_path), "byte_sha256": _sha256(probe_path)},
            "source_osm": {"path": str(source_osm_path), "byte_sha256": _sha256(source_osm_path)},
        },
        "stable_id_diff": {
            "affected_way_count": len(affected),
            "baseline_c1_blocker_count": len(baseline_c1),
            "remaining_c1_blocker_count": len(current_c1),
            "removed_blocker_id_count": len(removed_ids),
            "new_blocker_id_count": len(new_ids),
            "removed_blocker_ids": removed_ids,
            "new_blocker_ids": new_ids,
        },
        "permission_guard": {
            "unaffected_normalized_rules_unchanged": unaffected_normalized_equal,
            "unaffected_static_maxima_unchanged": unaffected_maxima_equal,
            "missing_c1_rule_ways": missing_rules,
            "invalid_c1_rules": invalid_rules,
            "governed_maxima_citing_c1_rules": maxima_citing_c1,
        },
        "successor_blockers": {
            "count": len(successor_records),
            "stop_code_counts": dict(sorted(
                {
                    code: sum(item["stop_code"] == code for item in successor_records)
                    for code in {item["stop_code"] for item in successor_records}
                }.items()
            )),
            "c2_access_specificity_conflict_exposed": c2_specificity_exposed,
            "records": successor_records,
        },
        "acceptance": acceptance,
    }
    result["semantic_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--source-osm", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = compare(
        decision_path=args.decision,
        registry_path=args.registry,
        baseline_path=args.baseline,
        probe_path=args.probe,
        source_osm_path=args.source_osm,
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite comparator: {args.output}")
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "stable_id_diff": result["stable_id_diff"],
        "successor_blocker_counts": result["successor_blockers"]["stop_code_counts"],
        "acceptance": result["acceptance"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
