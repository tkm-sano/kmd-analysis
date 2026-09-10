"""Compare the approved shared-single-lane source-resolution population and probe."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.directional_lanes_v17 import (
    SHARED_SINGLE_LANE_KIND,
    SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
    SHARED_SINGLE_LANE_RULE_ID,
    is_formal_shared_single_lane_candidate,
)


class SharedSingleLaneComparisonError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SharedSingleLaneComparisonError(f"JSON root is not an object: {path}")
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


def _semantic_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:directional_lanes:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def extract_population(source_osm_path: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for _event, element in ET.iterparse(source_osm_path, events=("end",)):
        if element.tag == "way":
            tags = {
                item.attrib["k"]: item.attrib["v"] for item in element.findall("tag")
            }
            if is_formal_shared_single_lane_candidate(tags):
                records.append(
                    {
                        "source_way_id": int(element.attrib["id"]),
                        "source_tags": dict(sorted(tags.items())),
                    }
                )
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    records.sort(key=lambda item: item["source_way_id"])
    return {
        "schema_version": 1,
        "population_id": "phase13_shared_single_lane_strict_source_population_v1",
        "predicate_rule_id": SHARED_SINGLE_LANE_RULE_ID,
        "population_count": len(records),
        "stable_way_ids": [item["source_way_id"] for item in records],
        "records": records,
        "semantic_sha256": _semantic_hash(records),
        "source": {"path": str(source_osm_path), "sha256": _sha256(source_osm_path)},
    }


def compare(
    *,
    previous_population_path: Path,
    baseline_lane_path: Path,
    probe_lane_path: Path,
    baseline_static_path: Path,
    probe_static_path: Path,
    source_osm_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    previous = _json(previous_population_path)
    baseline_lane = _json(baseline_lane_path)
    probe_lane = _json(probe_lane_path)
    baseline_static = _json(baseline_static_path)
    probe_static = _json(probe_static_path)
    population = extract_population(source_osm_path)

    previous_strict = sorted(
        int(item["source_way_id"])
        for item in previous["records"]
        if is_formal_shared_single_lane_candidate(item["source_tags"])
    )
    current = population["stable_way_ids"]
    affected = set(current)
    added = sorted(affected - set(previous_strict))
    removed = sorted(set(previous_strict) - affected)
    if added or removed:
        raise SharedSingleLaneComparisonError(
            f"strict population differs: added={added}, removed={removed}"
        )

    baseline_blockers = baseline_lane["blockers"]
    probe_blockers = probe_lane["blockers"]
    baseline_by_way = {
        int(item["source_way_id"]): item for item in baseline_blockers
    }
    probe_by_way = {int(item["source_way_id"]): item for item in probe_blockers}
    source_records = {
        int(item["source_way_id"]): item
        for item in probe_lane["source_semantic_records"]
    }
    attempts = {
        int(item["source_way_id"]): item
        for item in probe_lane["materialization_attempts"]
    }
    affected_segment_lanes = [
        item for item in probe_lane["segment_lanes"]
        if int(item["source_way_id"]) in affected
    ]

    invalid_before = [
        way_id for way_id in current
        if baseline_by_way.get(way_id, {}).get("stop_code")
        != "LANE_DIRECTIONAL_ALLOCATION_MISSING"
    ]
    invalid_after = [
        way_id for way_id in current
        if probe_by_way.get(way_id, {}).get("stop_code")
        != SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE
    ]
    invalid_records = []
    for way_id in current:
        record = source_records.get(way_id)
        attempt = attempts.get(way_id)
        blocker = probe_by_way.get(way_id)
        if (
            record is None
            or attempt is None
            or blocker is None
            or record["resolution_status"] != "resolved"
            or record["value_origin"] != "rule_derived"
            or record["effective_value"]
            != {
                "kind": SHARED_SINGLE_LANE_KIND,
                "physical_moving_lane_count": 1,
                "usable_source_directions": ["forward", "backward"],
                "dedicated_moving_lane_count": {"forward": 0, "backward": 0},
            }
            or attempt["source_semantic_record_id"] != record["record_id"]
            or blocker["source_semantic_record_id"] != record["record_id"]
            or attempt["record_id"] != blocker["materialization_attempt_id"]
            or not attempt["child_directed_segment_ids"]
            or attempt["child_directed_segment_ids"]
            != blocker["child_directed_segment_ids"]
        ):
            invalid_records.append(way_id)

    baseline_unaffected = sorted(
        (_blocker_id(item), copy.deepcopy(item))
        for item in baseline_blockers
        if int(item["source_way_id"]) not in affected
    )
    probe_unaffected = sorted(
        (_blocker_id(item), copy.deepcopy(item))
        for item in probe_blockers
        if int(item["source_way_id"]) not in affected
    )
    baseline_source_hash = baseline_lane["source"]["sha256"]
    source_hash = _sha256(source_osm_path)
    accounting = {
        "cluster_before": {
            "source_semantic_blockers": len(affected),
            "canonical_representation_blockers": len(affected),
            "simulation_materialization_blockers": 0,
            "overall_acceptance_blockers": len(affected),
        },
        "cluster_after": {
            "source_semantic_blockers": 0,
            "canonical_representation_blockers": 0,
            "simulation_materialization_blockers": len(affected),
            "overall_acceptance_blockers": len(affected),
        },
        "cluster_delta": {
            "source_semantic_blockers": -len(affected),
            "canonical_representation_blockers": -len(affected),
            "simulation_materialization_blockers": len(affected),
            "overall_acceptance_blockers": len(probe_blockers) - len(baseline_blockers),
        },
        "live_before": {"overall_acceptance_blockers": len(baseline_blockers)},
        "live_after": {
            "source_semantic_blockers": probe_lane["counts"]["source_semantic_blockers"],
            "canonical_representation_blockers": probe_lane["counts"]["canonical_representation_blockers"],
            "simulation_materialization_blockers": probe_lane["counts"]["simulation_materialization_blockers"],
            "overall_acceptance_blockers": len(probe_blockers),
        },
    }
    acceptance = {
        "strict_population_matches_previous_180_set": len(current) == 180 and not added and not removed,
        "baseline_predecessor_blockers_are_exact": not invalid_before,
        "successor_blockers_are_exact": not invalid_after,
        "resolved_record_attempt_and_blocker_chain_is_complete": not invalid_records,
        "no_affected_segment_lane_tuple": not affected_segment_lanes,
        "unaffected_lane_blockers_unchanged": baseline_unaffected == probe_unaffected,
        "overall_lane_blocker_count_unchanged": len(baseline_blockers) == len(probe_blockers),
        "unaffected_static_normalized_rules_unchanged": baseline_static["normalized_rules"] == probe_static["normalized_rules"],
        "unaffected_static_maxima_unchanged": baseline_static["static_maxima"] == probe_static["static_maxima"],
        "static_access_blockers_unchanged": baseline_static["blockers"] == probe_static["blockers"] == [],
        "source_osm_unchanged": baseline_source_hash == source_hash == probe_lane["source"]["sha256"],
        "four_layer_cluster_accounting_is_exact": accounting["cluster_delta"]
        == {
            "source_semantic_blockers": -180,
            "canonical_representation_blockers": -180,
            "simulation_materialization_blockers": 180,
            "overall_acceptance_blockers": 0,
        },
    }
    result = {
        "schema_version": 1,
        "comparison_id": "phase13_shared_single_lane_source_resolution_stable_id_v1",
        "status": "passed" if all(acceptance.values()) else "failed",
        "population": {
            "previous_strict_count": len(previous_strict),
            "current_count": len(current),
            "added_way_ids": added,
            "removed_way_ids": removed,
            "canonical_semantic_sha256": population["semantic_sha256"],
        },
        "stable_id_diff": {
            "removed_predecessor_blocker_ids": sorted(
                _blocker_id(baseline_by_way[way_id]) for way_id in current
            ),
            "added_successor_blocker_ids": sorted(
                _blocker_id(probe_by_way[way_id]) for way_id in current
            ),
        },
        "blocker_counts": {
            "before_total": len(baseline_blockers),
            "after_total": len(probe_blockers),
            "before_stop_codes": dict(sorted(Counter(item["stop_code"] for item in baseline_blockers).items())),
            "after_stop_codes": dict(sorted(Counter(item["stop_code"] for item in probe_blockers).items())),
        },
        "four_layer_accounting": accounting,
        "invalid_before_way_ids": invalid_before,
        "invalid_after_way_ids": invalid_after,
        "invalid_record_chain_way_ids": invalid_records,
        "affected_segment_lane_tuple_count": len(affected_segment_lanes),
        "samples": {
            "source_semantic_records": [source_records[way_id] for way_id in current[:3]],
            "materialization_attempts": [attempts[way_id] for way_id in current[:3]],
            "successor_blockers": [probe_by_way[way_id] for way_id in current[:3]],
        },
        "acceptance": acceptance,
    }
    result["semantic_sha256"] = _semantic_hash(result)
    return population, result


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite comparator output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-population", required=True, type=Path)
    parser.add_argument("--baseline-lane", required=True, type=Path)
    parser.add_argument("--probe-lane", required=True, type=Path)
    parser.add_argument("--baseline-static", required=True, type=Path)
    parser.add_argument("--probe-static", required=True, type=Path)
    parser.add_argument("--source-osm", required=True, type=Path)
    parser.add_argument("--population-output", required=True, type=Path)
    parser.add_argument("--comparison-output", required=True, type=Path)
    args = parser.parse_args(argv)
    population, result = compare(
        previous_population_path=args.previous_population,
        baseline_lane_path=args.baseline_lane,
        probe_lane_path=args.probe_lane,
        baseline_static_path=args.baseline_static,
        probe_static_path=args.probe_static,
        source_osm_path=args.source_osm,
    )
    _write_new(args.population_output, population)
    _write_new(args.comparison_output, result)
    print(json.dumps({"population": population["population_count"], "status": result["status"]}, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
