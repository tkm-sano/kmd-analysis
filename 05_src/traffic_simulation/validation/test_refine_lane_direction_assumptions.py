import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "refine_lane_direction_assumptions.py"
SPEC = importlib.util.spec_from_file_location("refine_lane", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def edge(**changes):
    row = {
        "edge_id": "e", "sumo_lane_count_normalized": "2", "osm_lanes_normalized": "2",
        "osm_lanes_forward_normalized": "", "osm_lanes_backward_normalized": "",
        "osm_oneway_normalized": "yes", "reverse_edge_id_normalized": "",
        "osm_way_ids_raw": "10", "sumo_lane_count_source_type": "OSM_EXPLICIT_TRANSFORMED",
        "sumo_lane_count_extraction_rule_id": "NETCONVERT_OSM_LANE_TRANSFORMATION_V1",
    }
    row.update(changes)
    return row


def test_explicit_oneway_lane_resolves_without_equal_split():
    result = MODULE.classify_edge(edge(), 4, {"e": 2}, {})
    assert result["classification"] == "NO_ASSUMPTION_NEEDED"
    assert result["primary_cause_code"] == "OTHER"


def test_realized_symmetric_pair_resolves_when_totals_agree():
    row = edge(osm_oneway_normalized="", osm_lanes_normalized="4", reverse_edge_id_normalized="r")
    result = MODULE.classify_edge(row, 4, {"e": 2, "r": 2}, {})
    assert result["classification"] == "NO_ASSUMPTION_NEEDED"
    assert result["primary_cause_code"] == "SUMO_SYMMETRIC"


def test_default_provenance_remains_assumption_candidate():
    row = edge(sumo_lane_count_source_type="MODEL_ASSUMPTION_MATERIALIZED")
    result = MODULE.classify_edge(row, 4, {"e": 2}, {})
    assert result["classification"] == "ASSUMPTION_MAY_BE_NEEDED"


def test_pair_total_conflict_is_unresolved():
    row = edge(osm_oneway_normalized="", osm_lanes_normalized="3", reverse_edge_id_normalized="r")
    result = MODULE.classify_edge(row, 4, {"e": 2, "r": 1}, {})
    assert result["classification"] == "UNRESOLVED"
    assert "CENSUS_OSM_SUMO_CONFLICT" in result["cause_codes"]


def test_realized_asymmetric_pair_is_supported_without_equal_split():
    row = edge(
        sumo_lane_count_normalized="2", osm_oneway_normalized="",
        osm_lanes_normalized="5", reverse_edge_id_normalized="r",
    )
    result = MODULE.classify_edge(row, 5, {"e": 2, "r": 3}, {})
    assert result["classification"] == "NO_ASSUMPTION_NEEDED"
    assert result["primary_cause_code"] == "SUMO_ASYMMETRIC"
