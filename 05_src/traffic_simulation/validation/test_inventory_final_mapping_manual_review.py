from __future__ import annotations

from traffic_simulation.calibration.inventory_final_mapping_manual_review import (
    Inventory,
    inventory_lane_projection,
    passenger_allowed,
    simple_maxspeed_kmh,
    survey_date_is_specific,
    traffic_quality,
)


def _final() -> dict[str, str]:
    return {
        "section_id": "S1",
        "final_edge_ids": "e1",
        "final_confidence": "high",
        "usable_for_lane_projection": "True",
    }


def test_lane_inventory_uses_directional_semantics_for_oneway_osm() -> None:
    inv = Inventory()
    inventory_lane_projection(
        inv,
        _final(),
        {"total_lanes": "4", "oneway_flag": "0"},
        {"e1": {"lanes": "2", "sumo_lane_count": "2", "oneway": "yes"}},
    )
    rows = inv.rows()
    assert {row["issue_type"] for row in rows} == {"LANE_CENSUS_OSM_CONSISTENT"}
    assert rows[0]["classification"] == "AUTO_RESOLVED"


def test_lane_inventory_records_conflict_and_odd_directional_split() -> None:
    inv = Inventory()
    inventory_lane_projection(
        inv,
        _final(),
        {"total_lanes": "5", "oneway_flag": "0"},
        {"e1": {"lanes": "3", "sumo_lane_count": "3", "oneway": "yes"}},
    )
    assert "DIRECTIONAL_LANE_SPLIT_REQUIRED" in {row["issue_type"] for row in inv.rows()}


def test_observation_quality_flags_missing_counts_without_repairing_them() -> None:
    quality = traffic_quality([{
        "small_vehicle_count": "",
        "large_vehicle_count": "",
        "total_vehicle_count": "0",
        "observation_flag": "1",
        "survey_date": "20211000",
        "weather_code": "",
        "direction": "up",
    }])
    assert quality == {
        "counts_missing": True,
        "nonobserved": False,
        "date_nonspecific": True,
        "weather_missing": True,
        "direction_metadata_missing": True,
    }


def test_attribute_parsers_are_deliberately_conservative() -> None:
    assert simple_maxspeed_kmh("50") == 50
    assert simple_maxspeed_kmh("50 km/h") == 50
    assert simple_maxspeed_kmh("50;40") is None
    assert survey_date_is_specific("20211013")
    assert not survey_date_is_specific("20211000")
    assert passenger_allowed({"allow": "passenger taxi bus"})
    assert not passenger_allowed({"allow": "taxi bus"})
