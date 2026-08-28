import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "inventory_research_assumptions.py"
SPEC = importlib.util.spec_from_file_location("assumption_inventory", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def final(**changes):
    row = {"section_id": "s1", "final_edge_ids": "e1", "usable_for_lane_projection": "True", "usable_for_traffic_assignment": "True"}
    row.update(changes)
    return row


def edge(**changes):
    row = {
        "edge_id": "e1", "sumo_lane_count_normalized": "2", "osm_lanes_normalized": "4",
        "osm_lanes_forward_normalized": "2", "osm_lanes_backward_normalized": "2",
        "osm_lanes_both_ways_normalized": "", "osm_oneway_normalized": "no",
        "osm_maxspeed_missing_status": "PRESENT", "osm_maxspeed_normalized": "50",
        "sumo_speed_mps_normalized": "13.89", "sumo_speed_source_type": "OSM_EXPLICIT_TRANSFORMED",
    }
    row.update(changes)
    return row


def test_explicit_directional_lanes_need_no_assumption():
    census = {"lane_count": "4", "lane_direction_scope": "BOTH_DIRECTIONS_TOTAL"}
    row = MODULE.classify_lane_direction(final(), census, [edge()])
    assert row["classification"] == "NO_ASSUMPTION_NEEDED"


def test_missing_directional_tags_may_need_assumption():
    census = {"lane_count": "4", "lane_direction_scope": "BOTH_DIRECTIONS_TOTAL"}
    row = MODULE.classify_lane_direction(final(), census, [edge(osm_lanes_forward_normalized="", osm_lanes_backward_normalized="")])
    assert row["classification"] == "ASSUMPTION_MAY_BE_NEEDED"


def test_sumo_default_speed_may_need_assumption():
    row = MODULE.classify_speed(final(), [edge(osm_maxspeed_missing_status="MISSING", osm_maxspeed_normalized="", sumo_speed_source_type="SUMO_TYPE_DEFAULT")])
    assert row["classification"] == "ASSUMPTION_MAY_BE_NEEDED"


def test_partial_day_observation_still_locates_comparison_cross_section():
    rows = [
        {"small_vehicle_count": "10", "large_vehicle_count": "2", "total_vehicle_count": "12"},
        {"small_vehicle_count": "", "large_vehicle_count": "", "total_vehicle_count": "0"},
    ]
    assert MODULE.observed_counts_available(rows)
