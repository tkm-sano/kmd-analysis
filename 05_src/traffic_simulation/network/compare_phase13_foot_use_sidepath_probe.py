"""Audit the Phase 13 C2 foot=use_sidepath full-population probe."""

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
    "passenger", "taxi", "bus", "coach", "delivery", "truck", "motorcycle"
]
C1_WAY_IDS = {
    28017223, 28017225, 28017419, 32593172, 32594002, 114032569,
    114957787, 254078689, 262946958, 262946966, 262946979, 685242503,
    685242504, 1039808256, 1040009077, 1040009078, 1073072898,
    1073072900, 1073072903, 1073072907, 1073072910, 1073072911,
    1190349699, 1303438915, 1308092138, 1308092144, 1308092145,
}


class FootUseSidepathProbeComparisonError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FootUseSidepathProbeComparisonError(f"JSON root is not an object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FootUseSidepathProbeComparisonError(f"YAML root is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _semantic_hash(probe: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes({
        "normalized_rules": copy.deepcopy(probe.get("normalized_rules", [])),
        "static_maxima": copy.deepcopy(probe.get("static_maxima", [])),
    })).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:static_access:static_access:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def _records_without(records: Sequence[Mapping[str, Any]], excluded: set[int]):
    return sorted(
        [copy.deepcopy(item) for item in records if int(item["source_way_id"]) not in excluded],
        key=_canonical_bytes,
    )


def _by_way(records: Sequence[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {int(item["source_way_id"]): item for item in records}


def _source_tags(path: Path, target_ids: set[int]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in target_ids:
                result[way_id] = {
                    tag.attrib["k"]: tag.attrib["v"] for tag in element.findall("tag")
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return result


def compare(
    *, decision_path: Path, registry_path: Path, baseline_path: Path,
    probe_path: Path, source_osm_path: Path,
) -> dict[str, Any]:
    decision = _yaml(decision_path)
    registry = _yaml(registry_path)
    baseline = _json(baseline_path)
    probe = _json(probe_path)
    affected = {int(value) for value in decision["fixed_population"]["source_way_ids"]}
    if len(affected) != 4:
        raise FootUseSidepathProbeComparisonError(f"expected 4 fixed C2 Ways, got {len(affected)}")
    if _sha256(baseline_path) != decision["comparison_baseline"]["byte_sha256"]:
        raise FootUseSidepathProbeComparisonError("specificity-green baseline hash differs")
    source_hash = decision["fixed_population"]["source_osm_byte_sha256"]
    if _sha256(source_osm_path) != source_hash:
        raise FootUseSidepathProbeComparisonError("source OSM differs from decision")
    if baseline["source"]["sha256"] != source_hash or probe["source"]["sha256"] != source_hash:
        raise FootUseSidepathProbeComparisonError("probe source lineage differs")
    if probe["semantic_sha256"] != _semantic_hash(probe):
        raise FootUseSidepathProbeComparisonError("probe semantic hash is invalid")

    baseline_ids = {_blocker_id(item) for item in baseline["blockers"]}
    probe_ids = {_blocker_id(item) for item in probe["blockers"]}
    baseline_by_way = _by_way(baseline["blockers"])
    c2_baseline = {way_id: baseline_by_way[way_id] for way_id in affected if way_id in baseline_by_way}
    expected_removed = sorted(_blocker_id(item) for item in c2_baseline.values())
    removed = sorted(baseline_ids - probe_ids)
    new = sorted(probe_ids - baseline_ids)

    baseline_rules = _by_way(baseline["normalized_rules"])
    probe_rules = _by_way(probe["normalized_rules"])
    tags_by_way = _source_tags(source_osm_path, affected)
    invalid_c2: list[dict[str, Any]] = []
    c2_foot_rule_ids: set[str] = set()
    c2_motor_vehicle_rule_ids: dict[int, str] = {}
    for way_id in sorted(affected):
        record = probe_rules.get(way_id, {})
        rules = record.get("rules", [])
        by_key = {rule["source_key"]: rule for rule in rules}
        foot = by_key.get("foot")
        motor_vehicle = by_key.get("motor_vehicle")
        vehicle = by_key.get("vehicle")
        conditional = record.get("deferred_conditional_tags", {})
        valid = (
            foot is not None and foot["source_value"] == "use_sidepath"
            and foot["vehicle_domain"] == []
            and foot["provenance"].get("access_value_semantics") == "parallel_way_required"
            and foot["provenance"].get("permission_effect_on_governed_vclasses") == "none"
            and foot["provenance"].get("source_value_rewritten") is False
            and motor_vehicle is not None and motor_vehicle["source_value"] == "yes"
            and vehicle is not None and vehicle["source_value"] == "no"
            and conditional.get("foot:conditional") == "no @ (roadway); yes @ (sidewalk)"
        )
        if not valid:
            invalid_c2.append({"source_way_id": way_id, "record": record})
        if foot is not None:
            c2_foot_rule_ids.add(foot["rule_id"])
        if motor_vehicle is not None:
            c2_motor_vehicle_rule_ids[way_id] = motor_vehicle["rule_id"]

    c2_maxima = [item for item in probe["static_maxima"] if int(item["source_way_id"]) in affected]
    invalid_c2_maxima = [
        item for item in c2_maxima
        if item["vehicle_class"] != "delivery"
        or item["effects"] != ["allowed"]
        or item["maximal_rule_ids"] != [c2_motor_vehicle_rule_ids.get(int(item["source_way_id"]))]
    ]
    maxima_citing_foot = [
        item for item in probe["static_maxima"]
        if set(item["maximal_rule_ids"]) & c2_foot_rule_ids
    ]
    c1_unchanged = all(baseline_rules.get(way_id) == probe_rules.get(way_id) for way_id in C1_WAY_IDS)
    registry_value = next(item for item in registry["access_values"] if item["source_value"] == "use_sidepath")
    motorcar_blockers = [
        item for item in probe["blockers"]
        if item["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING" and "motorcar" in item.get("message", "")
    ]
    successor_records = [
        {
            "source_way_id": int(item["source_way_id"]),
            "stop_code": item["stop_code"],
            "message": item.get("message"),
            "source_tags": _source_tags(source_osm_path, {int(item["source_way_id"])}).get(int(item["source_way_id"]), {}),
            "is_new_stable_id": _blocker_id(item) in new,
        }
        for item in probe["blockers"]
    ]
    specificity_conflicts = [item for item in probe["blockers"] if item["stop_code"] == "ACCESS_SPECIFICITY_CONFLICT"]

    acceptance = {
        "expected_affected_way_count_is_4": len(affected) == 4,
        "baseline_c2_access_value_blocker_count_is_4": len(c2_baseline) == 4 and all(item["stop_code"] == "ACCESS_VALUE_UNSUPPORTED" for item in c2_baseline.values()),
        "removed_blocker_ids_are_exactly_expected": removed == expected_removed,
        "new_blocker_ids_are_zero": len(new) == 0,
        "access_specificity_conflicts_are_zero": len(specificity_conflicts) == 0,
        "unaffected_blocker_ids_unchanged": baseline_ids - set(expected_removed) == probe_ids,
        "unaffected_normalized_rules_unchanged": _records_without(baseline["normalized_rules"], affected) == _records_without(probe["normalized_rules"], affected),
        "unaffected_static_maxima_unchanged": _records_without(baseline["static_maxima"], affected) == _records_without(probe["static_maxima"], affected),
        "c2_rules_and_conditional_provenance_preserved": len(invalid_c2) == 0,
        "motor_vehicle_child_is_the_only_c2_governed_maximum": len(c2_maxima) == 8 and len(invalid_c2_maxima) == 0,
        "foot_empty_domain_rules_do_not_affect_governed_maxima": len(maxima_citing_foot) == 0,
        "source_osm_unchanged": all(tags_by_way.get(way_id, {}).get("foot") == "use_sidepath" for way_id in affected),
        "governed_vclasses_unchanged": registry["vehicle_ontology"]["governed_vclasses"] == EXPECTED_GOVERNED_VCLASSES,
        "motorcar_hierarchy_blockers_remain_zero": len(motorcar_blockers) == 0,
        "c1_27_ways_unchanged": c1_unchanged,
        "registry_is_key_scoped_without_way_exceptions": registry_value["applicable_base_keys"] == ["bicycle", "foot"] and "source_way_ids" not in registry_value,
    }
    result = {
        "schema_version": 1,
        "comparison_id": "phase13_foot_use_sidepath_full_population_stable_id_diff_20260820",
        "decision_id": decision["decision_id"],
        "decision_version": decision["decision_version"],
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
            "baseline_c2_blocker_count": len(c2_baseline),
            "remaining_c2_blocker_count": sum(int(item["source_way_id"]) in affected for item in probe["blockers"]),
            "removed_blocker_id_count": len(removed),
            "new_blocker_id_count": len(new),
            "removed_blocker_ids": removed,
            "new_blocker_ids": new,
        },
        "specificity_guard": {
            "c2_static_maxima_count": len(c2_maxima),
            "invalid_c2_maxima": invalid_c2_maxima,
            "invalid_c2_rules": invalid_c2,
            "governed_maxima_citing_foot_rules": maxima_citing_foot,
        },
        "successor_blockers": {
            "count": len(successor_records),
            "stop_code_counts": {
                code: sum(item["stop_code"] == code for item in successor_records)
                for code in sorted({item["stop_code"] for item in successor_records})
            },
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
        decision_path=args.decision, registry_path=args.registry,
        baseline_path=args.baseline, probe_path=args.probe,
        source_osm_path=args.source_osm,
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite comparator: {args.output}")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "stable_id_diff": result["stable_id_diff"], "acceptance": result["acceptance"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
