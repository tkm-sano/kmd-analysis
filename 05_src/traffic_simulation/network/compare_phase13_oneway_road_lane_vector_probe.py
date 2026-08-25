"""Audit the Phase 13 one-way road-lane-vector count full-population probe."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS,
    ONEWAY_ROAD_LANE_VECTOR_RULE_ID,
    build_lane_production_artifact,
)


class OnewayRoadLaneVectorComparisonError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OnewayRoadLaneVectorComparisonError(f"JSON root is not an object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OnewayRoadLaneVectorComparisonError(f"YAML root is not an object: {path}")
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


def _probe_semantic_hash(probe: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            {
                "normalized_rules": copy.deepcopy(probe.get("normalized_rules", [])),
                "static_maxima": copy.deepcopy(probe.get("static_maxima", [])),
            }
        )
    ).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:directional_lanes:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def _by_way(records: Sequence[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {int(item["source_way_id"]): item for item in records}


def _records_without(
    records: Sequence[Mapping[str, Any]], excluded: set[int]
) -> list[Mapping[str, Any]]:
    return sorted(
        [copy.deepcopy(item) for item in records if int(item["source_way_id"]) not in excluded],
        key=_canonical_bytes,
    )


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
    *,
    decision_path: Path,
    fixed_population_path: Path,
    lane_investigation_path: Path,
    l4_investigation_path: Path,
    baseline_path: Path,
    probe_path: Path,
    source_osm_path: Path,
) -> dict[str, Any]:
    decision = _yaml(decision_path)
    fixed = _json(fixed_population_path)
    investigation = _json(lane_investigation_path)
    l4_investigation = _json(l4_investigation_path)
    baseline = _json(baseline_path)
    probe = _json(probe_path)
    affected = {int(value) for value in fixed["source_way_ids"]}
    fixed_by_way = _by_way(fixed["records"])

    if decision["decision"]["rule_id"] != ONEWAY_ROAD_LANE_VECTOR_RULE_ID:
        raise OnewayRoadLaneVectorComparisonError("decision rule ID differs from runtime")
    if set(decision["decision"]["approved_vector_keys"]) != set(
        APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS
    ):
        raise OnewayRoadLaneVectorComparisonError("decision vector scope differs from runtime")
    if len(affected) != 9:
        raise OnewayRoadLaneVectorComparisonError(f"expected 9 Ways, got {len(affected)}")
    if _sha256(fixed_population_path) != decision["fixed_population"]["byte_sha256"]:
        raise OnewayRoadLaneVectorComparisonError("fixed population hash differs")
    if _sha256(baseline_path) != decision["comparison_baseline"]["byte_sha256"]:
        raise OnewayRoadLaneVectorComparisonError("baseline hash differs")
    source_hash = decision["source_osm"]["byte_sha256"]
    if _sha256(source_osm_path) != source_hash:
        raise OnewayRoadLaneVectorComparisonError("source OSM differs from decision")
    if baseline["source"]["sha256"] != source_hash or probe["source"]["sha256"] != source_hash:
        raise OnewayRoadLaneVectorComparisonError("probe source lineage differs")
    if probe["semantic_sha256"] != _probe_semantic_hash(probe):
        raise OnewayRoadLaneVectorComparisonError("probe semantic hash is invalid")

    baseline_blockers = baseline["upstream_lane_blockers"]
    probe_blockers = probe["upstream_lane_blockers"]
    baseline_by_way = _by_way(baseline_blockers)
    baseline_ids = {_blocker_id(item) for item in baseline_blockers}
    probe_ids = {_blocker_id(item) for item in probe_blockers}
    expected_removed = sorted(fixed["expected_removed_blocker_ids"])
    removed = sorted(baseline_ids - probe_ids)
    new = sorted(probe_ids - baseline_ids)
    successor_records = [
        item for item in probe_blockers if int(item["source_way_id"]) in affected
    ]
    successor_ids = {_blocker_id(item) for item in successor_records}
    direct = affected - {int(item["source_way_id"]) for item in successor_records}

    source_tags = _source_tags(source_osm_path, affected | {221603369, 45681076, 46148379})
    lane_artifact = build_lane_production_artifact(source_osm_path, profile="formal")
    resolutions = _by_way(lane_artifact["resolutions"])
    segments_by_way: dict[int, list[Mapping[str, Any]]] = {}
    for item in lane_artifact["segment_lanes"]:
        way_id = int(item["source_way_id"])
        if way_id in direct:
            segments_by_way.setdefault(way_id, []).append(item)

    invalid_resolutions = []
    invalid_segments = []
    for way_id in sorted(direct):
        expected = int(fixed_by_way[way_id]["inferred_active_lane_count"])
        canonical_oneway = fixed_by_way[way_id]["oneway_canonical"]
        active = "backward" if canonical_oneway == "-1" else "forward"
        inactive = "forward" if active == "backward" else "backward"
        resolution = resolutions.get(way_id)
        if (
            resolution is None
            or resolution["effective_value"] != {
                "total": expected,
                active: expected,
                inactive: 0,
                "both_ways": 0,
            }
            or resolution["value_origin"] != "rule_derived"
            or resolution["rule_ids"] != [ONEWAY_ROAD_LANE_VECTOR_RULE_ID]
            or resolution["assumption_ids"] != []
            or resolution["formal_eligible"] is not True
            or resolution["source_lane_tags"] != fixed_by_way[way_id]["source_lane_tags"]
        ):
            invalid_resolutions.append({"source_way_id": way_id, "resolution": resolution})
        for segment in segments_by_way.get(way_id, []):
            lanes = segment["lanes"]
            if (
                segment["moving_lane_count"] != expected
                or segment["value_origin"] != "rule_derived"
                or segment["rule_ids"] != [ONEWAY_ROAD_LANE_VECTOR_RULE_ID]
                or segment["assumption_ids"] != []
                or segment["formal_eligible"] is not True
                or [item["lane_position"] for item in lanes] != list(range(expected))
                or [item["sumo_lane_index"] for item in lanes]
                != [expected - 1 - position for position in range(expected)]
            ):
                invalid_segments.append(segment)

    cluster_acceptance: dict[str, bool] = {}
    for cluster_id in (
        "L1_BIDIRECTIONAL_NO_LANE_COUNT",
        "L2_BIDIRECTIONAL_EVEN_TOTAL_ONLY",
        "L3_BIDIRECTIONAL_ODD_OR_SINGLE_TOTAL_ONLY",
        "L4_ONEWAY_COUNT_MISSING",
        "L5_PARTIAL_DIRECTIONAL_OR_BOTH_WAYS",
        "L6_LANE_VECTOR_LENGTH_CONFLICT",
        "L7_LANE_COUNT_CONFLICT",
    ):
        way_ids = {
            int(record["source_way_id"])
            for record in investigation["records"]
            if record["cluster_id"] == cluster_id
        } - affected
        expected_ids = {
            _blocker_id(baseline_by_way[way_id])
            for way_id in way_ids
            if way_id in baseline_by_way
        }
        cluster_acceptance[f"{cluster_id}_remaining_unchanged"] = expected_ids <= probe_ids

    l4_by_way = _by_way(l4_investigation["records"])
    e1b_id = l4_by_way[221603369]["stable_blocker_id"]
    e2_ids = {l4_by_way[way_id]["stable_blocker_id"] for way_id in (45681076, 46148379)}
    access_codes = Counter(item["stop_code"] for item in probe["blockers"])
    acceptance = {
        "fixed_affected_way_count_is_9": len(affected) == 9,
        "expected_removed_blocker_ids_match_exactly": removed == expected_removed,
        "new_unrelated_blocker_ids_are_zero": set(new) == successor_ids,
        "unaffected_blocker_ids_unchanged": baseline_ids - set(expected_removed) <= probe_ids,
        "E1B_mode_specific_vector_way_unchanged": e1b_id in probe_ids,
        "E2_conflicting_vector_ways_unchanged": e2_ids <= probe_ids,
        "L1_to_L7_remaining_populations_unchanged": all(cluster_acceptance.values()),
        "affected_resolutions_are_rule_derived_source_preserving": not invalid_resolutions,
        "lane_order_and_sumo_index_formula_hold": not invalid_segments,
        "unaffected_normalized_rules_unchanged": _records_without(
            baseline["normalized_rules"], affected
        )
        == _records_without(probe["normalized_rules"], affected),
        "unaffected_static_maxima_unchanged": _records_without(
            baseline["static_maxima"], affected
        )
        == _records_without(probe["static_maxima"], affected),
        "static_access_blockers_remain_zero": access_codes == Counter(),
        "source_osm_unchanged": _sha256(source_osm_path) == source_hash,
        "approved_source_vectors_unchanged": all(
            {
                key: source_tags[way_id][key]
                for key in fixed_by_way[way_id]["approved_source_vectors"]
            }
            == fixed_by_way[way_id]["approved_source_vectors"]
            for way_id in affected
        ),
        "no_way_specific_exception_in_decision_rule": "source_way_ids"
        not in decision["decision"],
    }
    result = {
        "schema_version": 1,
        "comparison_id": "phase13_oneway_road_lane_vector_stable_id_diff_20260820",
        "decision_id": decision["decision_id"],
        "decision_version": decision["decision_version"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "sources": {
            "decision": {"path": str(decision_path), "byte_sha256": _sha256(decision_path)},
            "fixed_population": {"path": str(fixed_population_path), "byte_sha256": _sha256(fixed_population_path)},
            "lane_investigation": {"path": str(lane_investigation_path), "byte_sha256": _sha256(lane_investigation_path)},
            "l4_investigation": {"path": str(l4_investigation_path), "byte_sha256": _sha256(l4_investigation_path)},
            "baseline_probe": {"path": str(baseline_path), "byte_sha256": _sha256(baseline_path)},
            "probe": {"path": str(probe_path), "byte_sha256": _sha256(probe_path)},
            "source_osm": {"path": str(source_osm_path), "byte_sha256": _sha256(source_osm_path)},
        },
        "stable_id_diff": {
            "affected_way_count": len(affected),
            "removed_blocker_id_count": len(removed),
            "new_blocker_id_count": len(new),
            "direct_resolution_count": len(direct),
            "successor_blocker_count": len(successor_records),
            "removed_blocker_ids": removed,
            "new_blocker_ids": new,
        },
        "lane_blocker_counts": {
            "before_total": len(baseline_blockers),
            "after_total": len(probe_blockers),
            "before_stop_codes": dict(sorted(Counter(item["stop_code"] for item in baseline_blockers).items())),
            "after_stop_codes": dict(sorted(Counter(item["stop_code"] for item in probe_blockers).items())),
        },
        "successor_blockers": [
            {**item, "source_tags": source_tags[int(item["source_way_id"])]}
            for item in successor_records
        ],
        "affected_lane_resolutions": [resolutions[way_id] for way_id in sorted(direct)],
        "cluster_acceptance": cluster_acceptance,
        "invalid_lane_resolutions": invalid_resolutions,
        "invalid_lane_segments": invalid_segments,
        "acceptance": acceptance,
    }
    result["semantic_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--fixed-population", required=True, type=Path)
    parser.add_argument("--lane-investigation", required=True, type=Path)
    parser.add_argument("--l4-investigation", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--source-osm", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = compare(
        decision_path=args.decision,
        fixed_population_path=args.fixed_population,
        lane_investigation_path=args.lane_investigation,
        l4_investigation_path=args.l4_investigation,
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
    print(
        json.dumps(
            {
                "status": result["status"],
                "stable_id_diff": result["stable_id_diff"],
                "lane_blocker_counts": result["lane_blocker_counts"],
                "acceptance": result["acceptance"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
