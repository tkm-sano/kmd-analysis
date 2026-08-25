from __future__ import annotations

import json
from pathlib import Path

from traffic_simulation.network.compare_phase13_shared_single_lane_probe import compare


ROOT = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17"
)
PREVIOUS = ROOT / (
    "phase13_20260821_bidirectional_single_shared_lane_semantics_v2/"
    "population_inventory.json"
)
BASELINE_LANE = ROOT / (
    "phase13_20260821_lane_blocker_osm_first_reclassification_v4/"
    "live_directional_lane_formal.json"
)
BASELINE_STATIC = ROOT / (
    "phase13_20260820_oneway_road_lane_vector_probe/static_access_formal.json"
)
PROBE_ROOT = ROOT / "phase13_20260822_shared_single_lane_source_resolution_tdd"
PROBE_LANE = PROBE_ROOT / "directional_lane_formal.json"
PROBE_STATIC = PROBE_ROOT / "static_access_formal.json"
SOURCE = Path(
    "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)


def test_persisted_shared_single_lane_comparator_is_reproducible() -> None:
    population, result = compare(
        previous_population_path=PREVIOUS,
        baseline_lane_path=BASELINE_LANE,
        probe_lane_path=PROBE_LANE,
        baseline_static_path=BASELINE_STATIC,
        probe_static_path=PROBE_STATIC,
        source_osm_path=SOURCE,
    )
    persisted_population = json.loads(
        (PROBE_ROOT / "strict_population.json").read_text(encoding="utf-8")
    )
    persisted_result = json.loads(
        (PROBE_ROOT / "stable_comparator.json").read_text(encoding="utf-8")
    )

    assert population == persisted_population
    assert result == persisted_result
    assert result["status"] == "passed"
    assert all(result["acceptance"].values())
    assert population["population_count"] == 180
    assert result["population"]["added_way_ids"] == []
    assert result["population"]["removed_way_ids"] == []
    assert result["blocker_counts"]["before_total"] == 22934
    assert result["blocker_counts"]["after_total"] == 22934
    assert result["blocker_counts"]["before_stop_codes"][
        "LANE_DIRECTIONAL_ALLOCATION_MISSING"
    ] == 22909
    assert result["blocker_counts"]["after_stop_codes"][
        "LANE_DIRECTIONAL_ALLOCATION_MISSING"
    ] == 22729
    assert result["blocker_counts"]["after_stop_codes"][
        "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
    ] == 180
