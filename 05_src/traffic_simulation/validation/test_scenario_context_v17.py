from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
)
from traffic_simulation.network.scenario_context_v17 import (
    ScenarioContextError,
    load_governed_runtime_context,
    validate_governed_runtime_context,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONTEXT_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_governed_runtime_interval_context.yml"
)
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "governed_runtime_context_phase7.json"
)
PRODUCTION_FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)


def _context_artifact() -> dict:
    return yaml.safe_load(CONTEXT_PATH.read_text(encoding="utf-8"))


def test_governed_context_matches_independent_positive_oracle() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"][0]
    actual = load_governed_runtime_context()
    for field, expected in fixture["oracle"].items():
        assert actual[field] == expected


def test_interval_and_vehicle_fields_are_machine_validated() -> None:
    actual = load_governed_runtime_context()
    assert actual["simulation_interval_seconds"] == 8 * 60 * 60
    assert actual["maximum_permissible_mass_kg"] > 0
    assert actual["width_m"] > 0
    assert actual["height_m"] > 0
    assert actual["length_m"] > 0


def test_holiday_calendar_establishes_runtime_date_is_not_holiday() -> None:
    actual = load_governed_runtime_context()
    assert actual["holiday_calendar_id"] == "japan_national_holidays_2026_v1"
    assert actual["public_holiday"] is False


def test_empty_authorization_array_is_distinct_from_missing_field() -> None:
    actual = load_governed_runtime_context()
    assert "authorization_ids" in actual
    assert actual["authorization_ids"] == []
    assert actual["private_authorization"] is False


def test_missing_authorization_field_matches_negative_oracle() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"][1]
    context = _context_artifact()
    del context["vehicle_context"]["authorization_ids"]
    with pytest.raises(ScenarioContextError) as caught:
        validate_governed_runtime_context(context)
    assert caught.value.stop_code == fixture["oracle"]["stop_code"]
    assert caught.value.status == fixture["oracle"]["resolution_status"]


def test_profile_mismatch_stops_instead_of_overriding() -> None:
    context = copy.deepcopy(_context_artifact())
    context["vehicle_context"]["width_m"] = 1.8
    with pytest.raises(ScenarioContextError) as caught:
        validate_governed_runtime_context(context)
    assert caught.value.stop_code == "ACCESS_CONTEXT_MISSING"


def test_holiday_assertion_mismatch_stops() -> None:
    context = copy.deepcopy(_context_artifact())
    context["holiday_calendar"]["public_holiday"] = True
    with pytest.raises(ScenarioContextError) as caught:
        validate_governed_runtime_context(context)
    assert caught.value.stop_code == "ACCESS_CONTEXT_MISSING"


def test_phase7_fixture_uses_governed_context_by_default() -> None:
    artifact = build_conditional_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal"
    )
    assert artifact["scenario_context"]["scenario_context_id"] == (
        "ota_ward_delivery_20260716_0900_1700_jst_v1"
    )
    assert artifact["blockers"] == []
    assert artifact["counts"]["lane_tuples_with_applicable_conditional_rules"] == 0
