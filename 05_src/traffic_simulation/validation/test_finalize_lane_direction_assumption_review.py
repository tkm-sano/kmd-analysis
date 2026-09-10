import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "finalize_lane_direction_assumption_review.py"
SPEC = importlib.util.spec_from_file_location("finalize_lane_review", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def evidence(reverse=1):
    return {"reverse_sumo_lane_count": reverse}


def edge(source="MODEL_ASSUMPTION_MATERIALIZED", osm="", sumo="1"):
    return {
        "sumo_lane_count_source_type": source,
        "sumo_lane_count_normalized": sumo,
        "osm_lanes_normalized": osm,
    }


def test_model_pair_numerically_matching_census_still_requires_assumption():
    result = MODULE.classify_decisive_edge("UNRESOLVED", 2, evidence(), edge())
    assert result[0] == "MODEL_ASSUMPTION_REQUIRED"
    assert result[1] == "NUMERIC_MATCH_WITH_MODEL_PROVENANCE"


def test_model_pair_disagreeing_with_census_is_data_conflict():
    result = MODULE.classify_decisive_edge("UNRESOLVED", 1, evidence(), edge())
    assert result[0] == "DATA_CONFLICT"
    assert result[1] == "CENSUS_SUMO_MATERIALIZED_CONFLICT"


def test_explicit_osm_disagreeing_with_census_is_data_conflict():
    result = MODULE.classify_decisive_edge(
        "UNRESOLVED", 2, evidence(reverse=2), edge("OSM_EXPLICIT_TRANSFORMED", osm="4", sumo="2")
    )
    assert result[0] == "DATA_CONFLICT"
    assert result[1] == "CENSUS_OSM_EXPLICIT_CONFLICT"


def test_netconvert_numlanes_default_requires_model_assumption():
    result = MODULE.classify_decisive_edge(
        "ASSUMPTION_MAY_BE_NEEDED", 6, evidence(reverse=None), edge("SUMO_TYPE_DEFAULT")
    )
    assert result[0] == "MODEL_ASSUMPTION_REQUIRED"
    assert result[1] == "NETCONVERT_IMPORTER_DEFAULT_NOT_FORMAL_EVIDENCE"
