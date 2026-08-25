from __future__ import annotations

import json
from pathlib import Path

import yaml

from traffic_simulation.network.compare_phase13_oneway_road_lane_vector_probe import (
    compare,
)
from traffic_simulation.network.directional_lanes_v17 import (
    APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS,
    ONEWAY_ROAD_LANE_VECTOR_RULE_ID,
)


DECISION = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_lane_count_from_road_lane_vector_decision.yml"
)
FIXED = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_oneway_road_lane_vector_probe/e1a_fixed_population.json"
)
LANE_INVESTIGATION = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_lane_blocker_investigation/lane_blocker_fixed_population.json"
)
L4_INVESTIGATION = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_l4_oneway_count_missing_investigation/"
    "l4_oneway_count_missing_fixed_population_v2.json"
)
BASELINE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_lanes2_formal_rule_probe/static_access_formal.json"
)
PROBE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_oneway_road_lane_vector_probe/static_access_formal.json"
)
SOURCE_OSM = Path(
    "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)
PERSISTED = PROBE.parent / "oneway_road_lane_vector_stable_id_diff.json"


def _compare() -> dict[str, object]:
    return compare(
        decision_path=DECISION,
        fixed_population_path=FIXED,
        lane_investigation_path=LANE_INVESTIGATION,
        l4_investigation_path=L4_INVESTIGATION,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )


def test_decision_and_runtime_vector_scope_are_exactly_synchronized() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))

    assert decision["decision"]["rule_id"] == ONEWAY_ROAD_LANE_VECTOR_RULE_ID
    assert set(decision["decision"]["approved_vector_keys"]) == set(
        APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS
    ) == {"turn:lanes", "destination:lanes", "destination:ref:lanes"}


def test_real_probe_passes_stable_id_comparator() -> None:
    result = _compare()

    assert result["status"] == "passed"
    assert all(result["acceptance"].values())
    assert result["stable_id_diff"] == {
        "affected_way_count": 9,
        "removed_blocker_id_count": 9,
        "new_blocker_id_count": 0,
        "direct_resolution_count": 9,
        "successor_blocker_count": 0,
        "removed_blocker_ids": json.loads(PERSISTED.read_text(encoding="utf-8"))[
            "stable_id_diff"
        ]["removed_blocker_ids"],
        "new_blocker_ids": [],
    }


def test_persisted_comparator_matches_recomputed_result() -> None:
    assert json.loads(PERSISTED.read_text(encoding="utf-8")) == _compare()


def test_runtime_uses_no_way_specific_target_ids() -> None:
    runtime = Path(
        "05_src/traffic_simulation/network/directional_lanes_v17.py"
    ).read_text(encoding="utf-8")
    fixed = json.loads(FIXED.read_text(encoding="utf-8"))

    assert all(str(way_id) not in runtime for way_id in fixed["source_way_ids"])
