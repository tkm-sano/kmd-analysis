import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "finalize_traffic_comparison_cross_section_review.py"
SPEC = importlib.util.spec_from_file_location("finalize_traffic_review", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def prior(series=True, flag="1"):
    return {
        "direction": "up", "official_observation_section_id": "s", "official_location": {"bbox_wgs84": [1, 2, 3, 4]},
        "official_observation_flag": flag, "official_direction_semantics": "TERMINUS_TO_ORIGIN",
        "series": {"raw_row_count": 2 if series else 0, "vehicle_class_codes": ["1", "2"] if series else [],
                   "hours_with_any_value": 24 if series else 0, "observation_flags": [flag], "survey_dates": ["20211001"]},
    }


def mapping(edges):
    return {"usable_for_traffic_assignment": "True", "final_edge_ids": ";".join(edges), "final_corridor_id": "c"}


def edge(reverse=""):
    return {"reverse_edge_id_normalized": reverse, "reverse_edge_status": "RESOLVED_EXACT_SAME_WAY" if reverse else "NOT_AVAILABLE_ONEWAY"}


def test_multiple_corridor_edges_require_researcher_selection():
    result = MODULE.classify_direction(
        prior(), "official place", mapping(["e1", "e2"]), {"oneway": "BIDIRECTIONAL"},
        {"e1": edge("r1"), "e2": edge("r2")},
    )
    assert result["final_classification"] == "MODEL_ASSUMPTION_REQUIRED"
    assert "MULTIPLE_CANDIDATE_CROSS_SECTION" in result["cause_codes"]


def test_missing_location_mapping_is_unresolved_not_model_assumption():
    result = MODULE.classify_direction(prior(), "official place", None, {"oneway": "BIDIRECTIONAL"}, {})
    assert result["final_classification"] == "UNRESOLVED"
    assert "LOCATION_MAPPING_MISSING" in result["cause_codes"]


def test_bidirectional_series_with_only_one_carriageway_is_mapping_missing():
    result = MODULE.classify_direction(prior(), "official place", mapping(["e"]), {"oneway": "BIDIRECTIONAL"}, {"e": edge()})
    assert result["final_classification"] == "UNRESOLVED"
    assert "LOCATION_MAPPING_MISSING" in result["cause_codes"]
    assert "DATA_CONFLICT" not in result["cause_codes"]


def test_missing_observation_series_is_unresolved():
    result = MODULE.classify_direction(prior(series=False), "official place", mapping(["e"]), {"oneway": "ONEWAY"}, {"e": edge()})
    assert result["final_classification"] == "UNRESOLVED"
    assert "OBSERVATION_MISSING" in result["cause_codes"]
