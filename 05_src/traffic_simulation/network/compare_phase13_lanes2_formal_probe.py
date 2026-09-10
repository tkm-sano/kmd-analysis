"""Audit the Phase 13 bidirectional lanes=2 formal-rule full-population probe."""

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
    LANES2_FORMAL_RULE_ID,
    build_lane_production_artifact,
)


class Lanes2FormalProbeComparisonError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Lanes2FormalProbeComparisonError(f"JSON root is not an object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Lanes2FormalProbeComparisonError(f"YAML root is not an object: {path}")
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


def _semantic_hash(probe: Mapping[str, Any]) -> str:
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


def _cluster_ids(
    population: Mapping[str, Any], *, cluster_id: str, lanes_value: str | None = None
) -> set[int]:
    result: set[int] = set()
    for record in population["records"]:
        if record["cluster_id"] != cluster_id:
            continue
        if lanes_value is not None and record["lane_related_tags"].get("lanes") != lanes_value:
            continue
        result.add(int(record["source_way_id"]))
    return result


def compare(
    *,
    decision_path: Path,
    fixed_population_path: Path,
    investigation_population_path: Path,
    baseline_path: Path,
    probe_path: Path,
    source_osm_path: Path,
) -> dict[str, Any]:
    decision = _yaml(decision_path)
    fixed_population = _json(fixed_population_path)
    investigation = _json(investigation_population_path)
    baseline = _json(baseline_path)
    probe = _json(probe_path)
    affected = {int(value) for value in fixed_population["source_way_ids"]}
    successor_candidates = {
        int(value) for value in fixed_population.get("successor_candidate_way_ids", [])
    }

    if decision["decision"]["rule_id"] != LANES2_FORMAL_RULE_ID:
        raise Lanes2FormalProbeComparisonError("decision rule ID differs from runtime")
    if len(affected) != 1196:
        raise Lanes2FormalProbeComparisonError(f"expected 1196 Ways, got {len(affected)}")
    if _sha256(fixed_population_path) != decision["fixed_population"]["byte_sha256"]:
        raise Lanes2FormalProbeComparisonError("fixed population hash differs")
    if _sha256(baseline_path) != decision["comparison_baseline"]["byte_sha256"]:
        raise Lanes2FormalProbeComparisonError("baseline hash differs")
    source_hash = decision["source_osm"]["byte_sha256"]
    if _sha256(source_osm_path) != source_hash:
        raise Lanes2FormalProbeComparisonError("source OSM differs from decision")
    if baseline["source"]["sha256"] != source_hash or probe["source"]["sha256"] != source_hash:
        raise Lanes2FormalProbeComparisonError("probe source lineage differs")
    if probe["semantic_sha256"] != _semantic_hash(probe):
        raise Lanes2FormalProbeComparisonError("probe semantic hash is invalid")

    baseline_blockers = baseline["upstream_lane_blockers"]
    probe_blockers = probe["upstream_lane_blockers"]
    baseline_ids = {_blocker_id(item) for item in baseline_blockers}
    probe_ids = {_blocker_id(item) for item in probe_blockers}
    baseline_by_way = _by_way(baseline_blockers)
    expected_removed = sorted(_blocker_id(baseline_by_way[way_id]) for way_id in affected)
    removed = sorted(baseline_ids - probe_ids)
    new = sorted(probe_ids - baseline_ids)
    successor_records = [
        item for item in probe_blockers if int(item["source_way_id"]) in affected
    ]
    successor_ids = {_blocker_id(item) for item in successor_records}
    direct_resolution_ids = sorted(affected - {int(item["source_way_id"]) for item in successor_records})

    probe_rules_by_way = _by_way(probe["normalized_rules"])
    direct_rules = [probe_rules_by_way.get(way_id) for way_id in direct_resolution_ids]
    source_tags = _source_tags(source_osm_path, affected)
    lane_artifact = build_lane_production_artifact(source_osm_path, profile="formal")
    lane_resolutions = _by_way(lane_artifact["resolutions"])
    lane_segments = [
        item for item in lane_artifact["segment_lanes"]
        if int(item["source_way_id"]) in affected
    ]
    invalid_lane_segments = [
        item for item in lane_segments
        if item["moving_lane_count"] != 1
        or item["value_origin"] != "rule_derived"
        or item["rule_ids"] != [LANES2_FORMAL_RULE_ID]
        or item["assumption_ids"] != []
        or item["formal_eligible"] is not True
        or item["lanes"] != [
            {"lane_position": 0, "sumo_lane_index": 0, "source_vector_values": {}}
        ]
    ]
    invalid_resolutions = [
        lane_resolutions[way_id]
        for way_id in direct_resolution_ids
        if lane_resolutions[way_id]["effective_value"] != {
            "total": 2,
            "forward": 1,
            "backward": 1,
            "both_ways": 0,
        }
        or lane_resolutions[way_id]["value_origin"] != "rule_derived"
        or lane_resolutions[way_id]["rule_ids"] != [LANES2_FORMAL_RULE_ID]
        or lane_resolutions[way_id]["assumption_ids"] != []
        or lane_resolutions[way_id]["source_lane_tags"].get("lanes") != "2"
    ]

    cluster_checks = {
        "L1_population_unchanged": _cluster_ids(
            investigation, cluster_id="L1_BIDIRECTIONAL_NO_LANE_COUNT"
        ),
        "L2_lanes4_population_unchanged": _cluster_ids(
            investigation, cluster_id="L2_BIDIRECTIONAL_EVEN_TOTAL_ONLY", lanes_value="4"
        ),
        "L3_population_unchanged": _cluster_ids(
            investigation, cluster_id="L3_BIDIRECTIONAL_ODD_OR_SINGLE_TOTAL_ONLY"
        ),
        "L4_population_unchanged": _cluster_ids(
            investigation, cluster_id="L4_ONEWAY_COUNT_MISSING"
        ),
        "L5_population_unchanged": _cluster_ids(
            investigation, cluster_id="L5_PARTIAL_DIRECTIONAL_OR_BOTH_WAYS"
        ),
        "L6_population_unchanged": _cluster_ids(
            investigation, cluster_id="L6_LANE_VECTOR_LENGTH_CONFLICT"
        ),
        "L7_population_unchanged": _cluster_ids(
            investigation, cluster_id="L7_LANE_COUNT_CONFLICT"
        ),
    }
    cluster_acceptance = {
        name: {f"blocker:directional_lanes:source_way:{way_id}:{baseline_by_way[way_id]['stop_code']}" for way_id in way_ids}
        <= probe_ids
        for name, way_ids in cluster_checks.items()
    }

    access_blocker_codes = Counter(item["stop_code"] for item in probe["blockers"])
    acceptance = {
        "fixed_population_count_is_1196": len(affected) == 1196,
        "expected_removed_allocation_blocker_ids_match": removed == expected_removed,
        "direct_resolution_count_is_1195": len(direct_resolution_ids) == 1195,
        "successor_blocker_count_is_1": len(successor_records) == 1,
        "successor_is_expected_way_and_code": successor_records == [
            {
                "message": "lane vector length 2 differs from 1",
                "resolution_status": "conflict",
                "scope": "source_way",
                "source_way_id": 1034365453,
                "stop_code": "LANE_VECTOR_LENGTH_MISMATCH",
            }
        ],
        "new_unrelated_blocker_ids_are_zero": set(new) == successor_ids,
        "unaffected_blocker_ids_unchanged": baseline_ids - set(expected_removed) <= probe_ids,
        "l1_l3_l4_l5_l6_l7_and_lanes4_unchanged": all(cluster_acceptance.values()),
        "unaffected_normalized_rules_unchanged": _records_without(
            baseline["normalized_rules"], affected
        )
        == _records_without(probe["normalized_rules"], affected),
        "unaffected_static_maxima_unchanged": _records_without(
            baseline["static_maxima"], affected
        )
        == _records_without(probe["static_maxima"], affected),
        "affected_rules_materialized_only_for_direct_resolutions": all(
            item is not None for item in direct_rules
        )
        and 1034365453 not in probe_rules_by_way,
        "lane_resolutions_are_rule_derived_and_source_preserving": len(invalid_resolutions) == 0,
        "lane_order_and_sumo_index_formula_hold": len(invalid_lane_segments) == 0,
        "source_osm_unchanged": all(
            tags.get("lanes") == "2" for tags in source_tags.values()
        ),
        "static_access_blockers_remain_zero": access_blocker_codes == Counter(),
        "static_access_counts_are_unchanged_for_blockers": probe["counts"]["static_access_blockers"] == 0,
        "no_way_specific_exception_field": "source_way_ids" not in decision["decision"],
    }
    result = {
        "schema_version": 1,
        "comparison_id": "phase13_lane_l2_bidirectional_lanes2_formal_stable_id_diff_20260820",
        "decision_id": decision["decision_id"],
        "decision_version": decision["decision_version"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "sources": {
            "decision": {"path": str(decision_path), "byte_sha256": _sha256(decision_path)},
            "fixed_population": {
                "path": str(fixed_population_path),
                "byte_sha256": _sha256(fixed_population_path),
            },
            "investigation_population": {
                "path": str(investigation_population_path),
                "byte_sha256": _sha256(investigation_population_path),
            },
            "baseline_probe": {"path": str(baseline_path), "byte_sha256": _sha256(baseline_path)},
            "probe": {"path": str(probe_path), "byte_sha256": _sha256(probe_path)},
            "source_osm": {"path": str(source_osm_path), "byte_sha256": _sha256(source_osm_path)},
        },
        "stable_id_diff": {
            "affected_way_count": len(affected),
            "removed_blocker_id_count": len(removed),
            "new_blocker_id_count": len(new),
            "direct_resolution_count": len(direct_resolution_ids),
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
        "successor_blockers": {
            "records": [
                {
                    **item,
                    "source_tags": source_tags.get(int(item["source_way_id"]), {}),
                }
                for item in successor_records
            ]
        },
        "cluster_acceptance": cluster_acceptance,
        "invalid_lane_resolutions": invalid_resolutions,
        "invalid_lane_segments": invalid_lane_segments,
        "acceptance": acceptance,
    }
    result["semantic_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--fixed-population", required=True, type=Path)
    parser.add_argument("--investigation-population", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--source-osm", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = compare(
        decision_path=args.decision,
        fixed_population_path=args.fixed_population,
        investigation_population_path=args.investigation_population,
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
