from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


DECISION = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_lane_count_from_road_lane_vector_decision.yml"
)
FIXED_POPULATION = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_oneway_road_lane_vector_probe/e1a_fixed_population.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_decision_is_independent_and_does_not_amend_l2() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))

    assert decision["decision_id"] == "DEC-P13-LANE-COUNT-FROM-ROAD-LANE-VECTOR-001"
    assert decision["decision_method"]["selected_method"] == "new_independent_decision"
    assert (
        decision["decision_method"]["rejected_method"]
        == "amend_DEC-P13-LANE-BIDIRECTIONAL-TOTAL-2-FORMAL-001"
    )
    assert "absent_lane_count_derivation" in decision["responsibility_boundary"][
        "existing_L2_decision"
    ]["does_not_own"]


def test_decision_approves_only_three_exact_vector_keys() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))

    assert decision["decision"]["approved_vector_keys"] == [
        "turn:lanes",
        "destination:lanes",
        "destination:ref:lanes",
    ]
    assert "general_star_lanes_inference" in decision["responsibility_boundary"][
        "explicitly_out_of_scope"
    ]
    assert decision["decision"]["rule_id"] == (
        "OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1"
    )


def test_fixed_population_is_exact_nine_way_set() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))
    population = json.loads(FIXED_POPULATION.read_text(encoding="utf-8"))

    assert _sha256(FIXED_POPULATION) == decision["fixed_population"]["byte_sha256"]
    assert population["population_count"] == 9
    assert population["source_way_ids"] == [
        815706174,
        990655363,
        1073479844,
        1073479845,
        1073479847,
        1089862560,
        1107307949,
        1134174349,
        1302654456,
    ]
    assert population["inferred_lane_count_distribution"] == {
        "1": 4,
        "2": 4,
        "3": 1,
    }
    assert all(
        set(record["approved_source_vectors"])
        <= {"turn:lanes", "destination:lanes", "destination:ref:lanes"}
        for record in population["records"]
    )
