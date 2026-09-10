from __future__ import annotations

import json
from pathlib import Path

import yaml

from traffic_simulation.network.compare_phase13_lanes2_formal_probe import compare
from traffic_simulation.network.directional_lanes_v17 import LANES2_FORMAL_RULE_ID


DECISION = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_lane_bidirectional_lanes2_formal_decision.yml"
)
FIXED_POPULATION = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_lanes2_formal_rule_probe/lanes2_fixed_population_v2.json"
)
INVESTIGATION_POPULATION = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_lane_blocker_investigation/lane_blocker_fixed_population.json"
)
BASELINE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_foot_use_sidepath_full_population_probe_v2/static_access_formal.json"
)
PROBE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_lanes2_formal_rule_probe/static_access_formal.json"
)
SOURCE_OSM = Path(
    "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)


def test_lanes2_decision_boundary_is_new_formal_rule_derived_semantics() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))

    assert decision["decision_method"]["selected_method"] == "new_independent_decision"
    assert decision["decision"]["rule_id"] == LANES2_FORMAL_RULE_ID
    assert decision["decision"]["project_level_semantics"] == {
        "backward_moving_lanes": 1,
        "both_ways_moving_lanes": 0,
        "forward_moving_lanes": 1,
        "source_preservation": True,
        "total_moving_lanes": 2,
        "value_origin": "rule_derived",
    }
    assert decision["decision"]["arithmetic_complement"]["general_unlock"] is False
    assert "lanes_4_or_higher_even_totals" in decision["responsibility_boundary"][
        "explicitly_out_of_scope"
    ]


def test_fixed_lanes2_population_contains_expected_1196_ways() -> None:
    population = json.loads(FIXED_POPULATION.read_text(encoding="utf-8"))

    assert population["population_count"] == 1196
    assert len(population["source_way_ids"]) == 1196
    assert population["successor_candidate_way_ids"] == [1034365453]
    assert all(
        record["cluster_id"] == "L2_BIDIRECTIONAL_EVEN_TOTAL_ONLY"
        and record["oneway_canonical"] == "no"
        and record["lane_related_tags"]["lanes"] == "2"
        for record in population["records"]
    )


def test_real_lanes2_probe_passes_stable_id_comparator() -> None:
    result = compare(
        decision_path=DECISION,
        fixed_population_path=FIXED_POPULATION,
        investigation_population_path=INVESTIGATION_POPULATION,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    assert result["status"] == "passed"
    assert all(result["acceptance"].values())
    assert result["stable_id_diff"]["affected_way_count"] == 1196
    assert result["stable_id_diff"]["removed_blocker_id_count"] == 1196
    assert result["stable_id_diff"]["direct_resolution_count"] == 1195
    assert result["stable_id_diff"]["new_blocker_ids"] == [
        "blocker:directional_lanes:source_way:1034365453:LANE_VECTOR_LENGTH_MISMATCH"
    ]


def test_persisted_lanes2_comparator_matches_recomputed_result() -> None:
    persisted = json.loads(
        (PROBE.parent / "lanes2_formal_stable_id_diff_v2.json").read_text(
            encoding="utf-8"
        )
    )
    recomputed = compare(
        decision_path=DECISION,
        fixed_population_path=FIXED_POPULATION,
        investigation_population_path=INVESTIGATION_POPULATION,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    assert persisted == recomputed
