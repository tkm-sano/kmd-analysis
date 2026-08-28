import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "refine_speed_assumptions.py"
SPEC = importlib.util.spec_from_file_location("refine_speed", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def edge(**changes):
    row = {
        "edge_id": "e", "sumo_speed_source_type": "SUMO_TYPE_DEFAULT",
        "sumo_speed_mps_normalized": "13.89", "osm_maxspeed_missing_status": "MISSING",
        "osm_maxspeed_normalized": "", "osm_maxspeed_raw_json": "{}", "sumo_type_raw": "highway.primary",
        "sumo_osm_defaults_raw": "speed", "sumo_speed_source_id": "highway.primary",
        "sumo_speed_source_file": "network.net.xml", "sumo_speed_extraction_rule_id": "DEFAULT",
    }
    row.update(changes)
    return row


def test_census_designated_speed_resolves_matching_default_without_assumption():
    result = MODULE.classify_edge(edge(), 50.0, True, {"highway.primary": ""})
    assert result["classification"] == "NO_ASSUMPTION_NEEDED"
    assert result["primary_cause_code"] == "CENSUS_COMPARABLE"


def test_census_designated_speed_resolves_different_default_but_records_remediation():
    result = MODULE.classify_edge(edge(), 40.0, True, {"highway.primary": ""})
    assert result["classification"] == "NO_ASSUMPTION_NEEDED"
    assert "requires later remediation" in result["reason"]


def test_travel_speed_does_not_replace_missing_limit_speed():
    result = MODULE.classify_edge(edge(), None, True, {"highway.primary": ""})
    assert result["classification"] == "ASSUMPTION_MAY_BE_NEEDED"
    assert result["primary_cause_code"] == "DEFINITION_NOT_COMPARABLE"


def test_osm_and_census_limit_speed_conflict_is_unresolved():
    row = edge(
        sumo_speed_source_type="OSM_EXPLICIT_TRANSFORMED", sumo_speed_mps_normalized="13.89",
        osm_maxspeed_missing_status="PRESENT", osm_maxspeed_normalized="50",
    )
    result = MODULE.classify_edge(row, 40.0, True, {"highway.primary": ""})
    assert result["classification"] == "UNRESOLVED"
    assert result["primary_cause_code"] == "SOURCE_CONFLICT"
