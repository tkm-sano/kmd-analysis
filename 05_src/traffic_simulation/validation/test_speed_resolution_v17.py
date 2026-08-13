from __future__ import annotations

from pathlib import Path

import pytest

from traffic_simulation.network.speed_resolution_v17 import (
    SpeedResolutionError,
    build_speed_production_artifact,
    evaluate_conditional_speed,
    load_japan_speed_registry,
    normalize_numeric_speed,
    resolve_japan_speed_rule,
    resolve_segment_speed,
    write_artifact_atomic,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "speed_phase9_production.osm.xml"
)
POINT_CONTEXT = {"weekday": "Mo", "time": "08:00"}
INTERVAL_CONTEXT = {
    "scenario_context_id": "ota_ward_delivery_20260716_0900_1700_jst_v1",
    "start_timestamp": "2026-07-16T09:00:00+09:00",
    "end_timestamp": "2026-07-16T17:00:00+09:00",
    "timezone": "Asia/Tokyo",
}


def test_numeric_speed_is_canonical_kmh() -> None:
    assert normalize_numeric_speed("50") == 50.0
    assert normalize_numeric_speed("50.0") == 50.0


def test_directional_asymmetry_is_preserved() -> None:
    tags = {"maxspeed:forward": "50", "maxspeed:backward": "40"}
    forward = resolve_segment_speed(
        tags, direction="forward", profile="formal", scenario_context=POINT_CONTEXT
    )
    backward = resolve_segment_speed(
        tags, direction="backward", profile="formal", scenario_context=POINT_CONTEXT
    )
    assert (forward["speed_kmh"], backward["speed_kmh"]) == (50.0, 40.0)


def test_general_explicit_speed_has_priority_over_conditional() -> None:
    result = resolve_segment_speed(
        {"maxspeed": "50", "maxspeed:conditional": "30 @ (Mo-Fr 07:00-09:00)"},
        direction="forward",
        profile="formal",
        scenario_context=POINT_CONTEXT,
    )
    assert result["speed_kmh"] == 50.0
    assert result["source_key"] == "maxspeed"


def test_registered_conditional_speed_matches() -> None:
    result = resolve_segment_speed(
        {"maxspeed:conditional": "30 @ (Mo-Fr 07:00-09:00)"},
        direction="forward",
        profile="formal",
        scenario_context=POINT_CONTEXT,
    )
    assert result["speed_kmh"] == 30.0
    assert result["speed_kind"] == "conditional_source_maxspeed"


def test_missing_conditional_context_stops() -> None:
    with pytest.raises(SpeedResolutionError) as caught:
        evaluate_conditional_speed("30 @ (Mo-Fr 07:00-09:00)", {})
    assert caught.value.stop_code == "SPEED_CONDITIONAL_CONTEXT_MISSING"


def test_within_interval_change_stops_without_averaging() -> None:
    with pytest.raises(SpeedResolutionError) as caught:
        evaluate_conditional_speed(
            "30 @ (07:00-09:00)", {"interval": "08:30/09:30"}
        )
    assert caught.value.stop_code == "SPEED_WITHIN_INTERVAL_CHANGE"


@pytest.mark.parametrize(
    ("value", "stop_code"),
    [
        ("-20", "SPEED_VALUE_INVALID"),
        ("0", "SPEED_VALUE_INVALID"),
        ("signals", "SPEED_VALUE_UNSUPPORTED"),
        ("50 mph", "SPEED_VALUE_UNSUPPORTED"),
    ],
)
def test_invalid_and_unsupported_values_stop(value: str, stop_code: str) -> None:
    with pytest.raises(SpeedResolutionError) as caught:
        resolve_segment_speed(
            {"maxspeed": value},
            direction="forward",
            profile="formal",
            scenario_context=POINT_CONTEXT,
        )
    assert caught.value.stop_code == stop_code


def test_phase2_symbolic_fixture_registry_resolves_independently() -> None:
    result = resolve_segment_speed(
        {"maxspeed": "JP:urban"},
        direction="forward",
        profile="formal",
        scenario_context=POINT_CONTEXT,
        japan_registry={"JP:urban": 40},
    )
    assert result["speed_kmh"] == 40.0


def test_unregistered_symbolic_value_stops() -> None:
    with pytest.raises(SpeedResolutionError) as caught:
        resolve_segment_speed(
            {"maxspeed": "JP:unregistered"},
            direction="forward",
            profile="formal",
            scenario_context=POINT_CONTEXT,
        )
    assert caught.value.stop_code == "SPEED_RULE_NOT_REGISTERED"


def test_pre_change_japan_rule_is_dated_and_evidence_bound() -> None:
    result = resolve_japan_speed_rule(
        symbolic_value="JP:urban",
        context=INTERVAL_CONTEXT,
        road_state_evidence={
            "road_category": "general_road",
            "vehicle_category": "automobile",
            "designated_speed_present": False,
        },
    )
    assert result["speed_kmh"] == 60.0
    assert result["rule_ids"] == ["JP_GENERAL_AUTOMOBILE_PRE_20260901_STATUTORY_60"]


def test_post_change_living_road_rule_is_not_retroactive() -> None:
    result = resolve_japan_speed_rule(
        symbolic_value="JP:urban",
        context={"start_timestamp": "2026-09-01T09:00:00+09:00"},
        road_state_evidence={
            "road_category": "general_road",
            "vehicle_category": "automobile",
            "designated_speed_present": False,
            "centerline_or_vehicle_lane_present": False,
            "directions_structurally_separated": False,
        },
    )
    assert result["speed_kmh"] == 30.0


def test_jp_urban_without_road_state_evidence_stops() -> None:
    with pytest.raises(SpeedResolutionError) as caught:
        resolve_segment_speed(
            {"maxspeed:type": "JP:urban"},
            direction="forward",
            profile="formal",
            scenario_context=INTERVAL_CONTEXT,
        )
    assert caught.value.stop_code == "SPEED_RULE_NOT_REGISTERED"


def test_structural_typemap_candidate_never_enters_formal() -> None:
    with pytest.raises(SpeedResolutionError):
        resolve_segment_speed(
            {},
            direction="forward",
            profile="formal",
            scenario_context=INTERVAL_CONTEXT,
            structural_typemap_speed_kmh=30,
        )
    structural = resolve_segment_speed(
        {},
        direction="forward",
        profile="structural",
        scenario_context=INTERVAL_CONTEXT,
        structural_typemap_speed_kmh=30,
    )
    assert structural["value_origin"] == "model_assumed"
    assert structural["assumption_ids"] == ["STRUCTURAL_TYPEMAP_SPEED_DEFAULT_V1"]


def test_production_fixture_resolves_and_separates_advisory_speed() -> None:
    artifact = build_speed_production_artifact(
        FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    assert artifact["formal_speed_complete"] is True
    assert artifact["counts"] == {
        "governed_directed_segments": 4,
        "speed_records": 4,
        "resolved_speeds": 4,
        "unresolved_speeds": 0,
        "invalid_speeds": 0,
        "unsupported_speeds": 0,
        "conflicting_speeds": 0,
        "model_assumed_speeds": 0,
        "speed_blockers": 0,
        "upstream_relation_blockers": 0,
    }
    by_way = {
        (item["source_way_id"], item["source_direction"]): item
        for item in artifact["speed_records"]
    }
    assert by_way[(3001, "forward")]["speed_kmh"] == 50.0
    assert by_way[(3001, "backward")]["speed_kmh"] == 40.0
    assert by_way[(3002, "forward")]["speed_kmh"] == 60.0
    assert by_way[(3002, "forward")]["advisory_speed"] == {
        "source_value": "40",
        "speed_kmh": 40.0,
        "legal_maxspeed": False,
    }
    assert by_way[(3003, "forward")]["speed_kmh"] == 30.0
    assert by_way[(3002, "forward")]["speed_mps"] == pytest.approx(60 / 3.6)


def test_production_artifact_is_deterministic() -> None:
    first = build_speed_production_artifact(
        FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    second = build_speed_production_artifact(
        FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    assert first == second


def test_registry_is_schema_valid_and_versioned() -> None:
    registry = load_japan_speed_registry()
    assert registry["registry_id"] == "JAPAN_SPEED_RULES_V17"
    assert registry["registry_version"] == "1.0.0"
    assert len(registry["rules"]) == 4


def test_writer_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    artifact = build_speed_production_artifact(
        FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    output = tmp_path / "speed.json"
    write_artifact_atomic(artifact, output)
    with pytest.raises(FileExistsError):
        write_artifact_atomic(artifact, output)
