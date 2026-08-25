"""Stable-population and formal-state comparators for Phase 13 fallback."""

from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


SCENARIOS = ("conservative", "baseline", "high_capacity")


def _load(path: Path) -> Any:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    return json.loads(path.read_text(encoding="utf-8"))


def compare_stable_population(
    *, expected_dry_run: Path, live_directory: Path
) -> dict[str, Any]:
    expected = _load(expected_dry_run)
    expected_by_scenario: dict[str, dict[int, Mapping[str, Any]]] = {
        scenario: {} for scenario in SCENARIOS
    }
    for record in expected["records"]:
        expected_by_scenario[record["scenario"]][int(record["source_way_id"])] = record

    results = {}
    passed = True
    for scenario in SCENARIOS:
        live = _load(live_directory / f"simulation_{scenario}.json.gz")
        live_by_id = {
            int(record["source_way_id"]): record
            for record in live["assumption_records"]
        }
        expected_ids = set(expected_by_scenario[scenario])
        live_ids = set(live_by_id)
        added = sorted(live_ids - expected_ids)
        removed = sorted(expected_ids - live_ids)
        value_mismatches = []
        for way_id in sorted(expected_ids & live_ids):
            old = expected_by_scenario[scenario][way_id]
            new = live_by_id[way_id]
            old_counts = {
                "total": int(old["assumed_total_lanes"]),
                "forward": int(old["assumed_forward_lanes"]),
                "backward": int(old["assumed_backward_lanes"]),
                "both_ways": int(old["assumed_both_ways_lanes"]),
            }
            if old_counts != new["chosen_lane_count"]:
                value_mismatches.append(
                    {"source_way_id": way_id, "expected": old_counts, "actual": new["chosen_lane_count"]}
                )
        manifest = live["manifest"]
        scenario_passed = (
            not added
            and not removed
            and not value_mismatches
            and manifest["assumed_way_count"] == 22627
            and manifest["by_fallback_level"] == {
                "class_directionality_calibrated_default": 22410,
                "global_directionality_fallback": 217,
            }
            and manifest["formal_blockers_preserved"] == 22627
        )
        passed = passed and scenario_passed
        results[scenario] = {
            "expected_way_count": len(expected_ids),
            "actual_way_count": len(live_ids),
            "added_way_ids": added,
            "removed_way_ids": removed,
            "value_mismatch_count": len(value_mismatches),
            "value_mismatch_sample": value_mismatches[:20],
            "status": "passed" if scenario_passed else "failed",
        }
    return {
        "schema_version": 1,
        "comparator": "phase13_missing_lane_fallback_stable_population",
        "status": "passed" if passed else "failed",
        "by_scenario": results,
    }


def _blocker_keys(artifact: Mapping[str, Any]) -> list[tuple[int, str]]:
    return sorted(
        (int(item["source_way_id"]), str(item["stop_code"]))
        for item in artifact["blockers"]
    )


def compare_formal_state(
    *,
    baseline_lane: Path,
    actual_lane: Path,
    blocker_inventory: Path,
    baseline_static: Path | None = None,
    actual_static: Path | None = None,
) -> dict[str, Any]:
    before = _load(baseline_lane)
    after = _load(actual_lane)
    inventory = _load(blocker_inventory)
    checks = {
        "source_equal": before["source"] == after["source"],
        "road_direction_semantic_hash_equal": before["directed_segment_semantic_sha256"] == after["directed_segment_semantic_sha256"],
        "formal_counts_equal": before["counts"] == after["counts"],
        "formal_semantic_hash_equal": before["semantic_sha256"] == after["semantic_sha256"],
        "blocker_ids_equal": _blocker_keys(before) == _blocker_keys(after),
        "resolutions_equal": before["resolutions"] == after["resolutions"],
        "source_semantic_records_equal": before["source_semantic_records"] == after["source_semantic_records"],
        "materialization_attempts_equal": before["materialization_attempts"] == after["materialization_attempts"],
        "segment_lanes_equal": before["segment_lanes"] == after["segment_lanes"],
        "upstream_relation_blockers_equal": before["upstream_blockers"] == after["upstream_blockers"],
    }
    after_blockers = dict(_blocker_keys(after))
    cluster_results = {}
    for cluster in (
        "L1_BIDIRECTIONAL_NO_LANE_COUNT",
        "L4_ONEWAY_COUNT_MISSING",
        "L5_PARTIAL_DIRECTIONAL_OR_BOTH_WAYS",
        "L6_LANE_VECTOR_LENGTH_CONFLICT",
        "L7_LANE_COUNT_CONFLICT",
        "L2_BIDIRECTIONAL_EVEN_TOTAL_ONLY",
    ):
        ids = sorted(
            int(item["source_way_id"])
            for item in inventory["records"]
            if item["cluster_id"] == cluster
        )
        missing = [way_id for way_id in ids if way_id not in after_blockers]
        changed = [
            way_id
            for way_id in ids
            if way_id in after_blockers
            and after_blockers[way_id]
            != next(
                item["stop_code"]
                for item in inventory["records"]
                if int(item["source_way_id"]) == way_id
            )
        ]
        cluster_results[cluster] = {
            "expected_count": len(ids),
            "present_count": len(ids) - len(missing),
            "missing_way_ids": missing,
            "changed_stop_code_way_ids": changed,
        }
        checks[f"{cluster}_preserved"] = not missing and not changed

    shared_after = sorted(
        way_id
        for way_id, stop_code in _blocker_keys(after)
        if stop_code == "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
    )
    shared_before = sorted(
        way_id
        for way_id, stop_code in _blocker_keys(before)
        if stop_code == "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
    )
    checks["shared_180_preserved"] = shared_before == shared_after and len(shared_after) == 180

    static_result = None
    if baseline_static is not None and actual_static is not None:
        static_before = _load(baseline_static)
        static_after = _load(actual_static)
        static_checks = {
            "counts_equal": static_before["counts"] == static_after["counts"],
            "semantic_hash_equal": static_before["semantic_sha256"] == static_after["semantic_sha256"],
            "normalized_rules_equal": static_before["normalized_rules"] == static_after["normalized_rules"],
            "static_maxima_equal": static_before["static_maxima"] == static_after["static_maxima"],
            "blockers_equal": static_before["blockers"] == static_after["blockers"],
            "upstream_lane_blockers_equal": static_before["upstream_lane_blockers"] == static_after["upstream_lane_blockers"],
        }
        static_result = {
            "checks": static_checks,
            "status": "passed" if all(static_checks.values()) else "failed",
        }
        checks["static_access_equal"] = all(static_checks.values())

    passed = all(checks.values())
    return {
        "schema_version": 1,
        "comparator": "phase13_missing_lane_fallback_formal_state",
        "status": "passed" if passed else "failed",
        "checks": checks,
        "formal_counts": after["counts"],
        "cluster_results": cluster_results,
        "shared_materialization_count": len(shared_after),
        "blocker_stop_codes": dict(Counter(stop for _way, stop in _blocker_keys(after))),
        "static_access": static_result,
    }
