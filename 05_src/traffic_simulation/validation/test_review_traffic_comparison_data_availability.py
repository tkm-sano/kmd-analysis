import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "review_traffic_comparison_data_availability.py"
SPEC = importlib.util.spec_from_file_location("traffic_availability", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_out_of_population_observation_mapping_is_processing_omission():
    status, primary, causes, _ = MODULE.classify_availability(
        "LOCATION_MAPPING_MISSING", "observation", False, False, False, False
    )
    assert status == "UNRESOLVED"
    assert primary == "PROCESSING_OMISSION"
    assert causes == ["PROCESSING_OMISSION"]


def test_old_official_observation_is_found_but_year_mismatched():
    status, primary, causes, _ = MODULE.classify_availability(
        "OFFICIAL_LOCATION_MISSING", "", False, False, True, True
    )
    assert status == "UNRESOLVED"
    assert primary == "YEAR_MISMATCH"
    assert causes == ["FOUND_IN_OTHER_SOURCE", "YEAR_MISMATCH"]


def test_no_observed_location_across_three_years_is_data_not_available():
    status, primary, causes, _ = MODULE.classify_availability(
        "OFFICIAL_LOCATION_MISSING", "", False, False, False, True
    )
    assert status == "DATA_NOT_AVAILABLE"
    assert primary == "TRULY_NOT_AVAILABLE"
    assert causes == ["TRULY_NOT_AVAILABLE"]


def test_existing_but_policy_unusable_mapping_is_not_processing_omission():
    status, primary, causes, _ = MODULE.classify_availability(
        "LOCATION_MAPPING_MISSING", "observation", True, False, False, False
    )
    assert status == "UNRESOLVED"
    assert primary == "OTHER"
    assert causes == ["OTHER"]


def test_late_found_usable_mapping_resolves_without_assumption():
    status, primary, causes, _ = MODULE.classify_availability(
        "LOCATION_MAPPING_MISSING", "observation", True, True, False, False
    )
    assert status == "NO_ASSUMPTION_NEEDED"
    assert primary == "FOUND_IN_OTHER_SOURCE"
    assert causes == ["FOUND_IN_OTHER_SOURCE"]
