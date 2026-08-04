from __future__ import annotations

from pathlib import Path

import pytest

from traffic_simulation.network.conditional_access_v17 import (
    ConditionalAccessError,
    build_conditional_access_production_artifact,
    evaluate_conditional_access_rules,
    evaluate_conditional_value,
    parse_conditional_value,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)
BASE_TAGS = {"highway": "residential", "oneway": "yes", "lanes": "2"}


def _context(**overrides):
    return {
        "vehicle_class": "delivery",
        "weekday": "Mo",
        "time": "08:00",
        "trip_purpose": "delivery",
        "permit_ids": [],
        "authorization_ids": [],
        **overrides,
    }


def test_registered_weekday_and_clock_condition_matches() -> None:
    selected = evaluate_conditional_value(
        "no @ (Mo-Fr 07:00-09:00)", _context()
    )
    assert selected is not None
    assert selected.value == "no"


def test_nonmatching_condition_emits_no_conditional_result() -> None:
    assert (
        evaluate_conditional_value(
            "no @ (Mo-Fr 07:00-09:00)", _context(time="10:00")
        )
        is None
    )


def test_last_matching_clause_applies_only_inside_one_tag() -> None:
    selected = evaluate_conditional_value(
        "no @ (Mo-Fr); yes @ (Mo 07:00-09:00)", _context()
    )
    assert selected is not None
    assert selected.value == "yes"
    assert selected.source_order == 1


def test_missing_required_context_is_not_false() -> None:
    with pytest.raises(ConditionalAccessError) as caught:
        evaluate_conditional_value("no @ (Mo-Fr 07:00-09:00)", {})
    assert caught.value.stop_code == "ACCESS_CONTEXT_MISSING"


def test_unsupported_sunrise_syntax_stops() -> None:
    with pytest.raises(ConditionalAccessError) as caught:
        parse_conditional_value("no @ (sunrise-sunset)")
    assert caught.value.stop_code == "ACCESS_CONDITIONAL_SYNTAX_UNSUPPORTED"


def test_permission_change_inside_interval_stops() -> None:
    with pytest.raises(ConditionalAccessError) as caught:
        evaluate_conditional_value(
            "no @ (07:00-09:00)", {"interval": "08:30/09:30"}
        )
    assert caught.value.stop_code == "ACCESS_WITHIN_INTERVAL_CHANGE"


def test_constant_permission_through_interval_is_allowed() -> None:
    selected = evaluate_conditional_value(
        "no @ (07:00-09:00)", {"interval": "07:15/08:45"}
    )
    assert selected is not None
    assert selected.value == "no"


def test_same_permission_across_clause_boundary_does_not_stop() -> None:
    selected = evaluate_conditional_value(
        "no @ (07:00-08:00); no @ (08:00-09:00)",
        {"interval": "07:30/08:30"},
    )
    assert selected is not None
    assert selected.value == "no"


def test_weekday_change_inside_timestamp_interval_stops() -> None:
    with pytest.raises(ConditionalAccessError) as caught:
        evaluate_conditional_value(
            "no @ (Mo)",
            {
                "start_timestamp": "2026-08-03T23:30:00+09:00",
                "end_timestamp": "2026-08-04T00:30:00+09:00",
                "timezone": "Asia/Tokyo",
            },
        )
    assert caught.value.stop_code == "ACCESS_WITHIN_INTERVAL_CHANGE"


def test_boolean_or_requires_context_for_each_registered_operand() -> None:
    with pytest.raises(ConditionalAccessError) as caught:
        evaluate_conditional_value(
            "no @ (delivery OR PH)",
            {"vehicle_class": "delivery"},
        )
    assert caught.value.stop_code == "ACCESS_CONTEXT_MISSING"


def test_vehicle_irrelevant_rule_does_not_require_temporal_context() -> None:
    result = evaluate_conditional_access_rules(
        source_way_id=1001,
        conditional_tags={"hgv:conditional": "no @ (07:00-09:00)"},
        tags=BASE_TAGS,
        lane_counts={"forward": 2},
        context={"vehicle_class": "delivery"},
    )
    assert result["rules"] == []
    assert result["evaluations"][0]["outcome"] == "vehicle_not_applicable"


def test_matching_conditional_rule_is_schema_valid_and_pending_phase8() -> None:
    result = evaluate_conditional_access_rules(
        source_way_id=1001,
        conditional_tags={
            "access:conditional": "no @ (Mo-Fr 07:00-09:00)"
        },
        tags=BASE_TAGS,
        lane_counts={"forward": 2},
        context=_context(),
    )
    assert len(result["rules"]) == 1
    rule = result["rules"][0]
    assert rule["effect"] == "denied"
    assert rule["source_order"] == 0
    assert rule["temporal_domain"][0].startswith("condition:")


def test_conditional_lane_vector_preserves_local_positions() -> None:
    result = evaluate_conditional_access_rules(
        source_way_id=1001,
        conditional_tags={
            "access:lanes:conditional": "yes @ (Mo)||no @ (Mo)"
        },
        tags=BASE_TAGS,
        lane_counts={"forward": 3},
        context=_context(),
    )
    positions = sorted(
        rule["target_scope"]["lane_scope"]["positions"][0]
        for rule in result["rules"]
    )
    assert positions == [0, 2]


def test_production_fixture_integrates_conditional_candidates() -> None:
    artifact = build_conditional_access_production_artifact(
        FIXTURE,
        profile="formal",
        scenario_context={"weekday": "Mo", "time": "08:00"},
    )
    assert artifact["blockers"] == []
    assert artifact["upstream_static_access_blockers"] == []
    assert artifact["upstream_lane_blockers"] == []
    assert artifact["upstream_relation_blockers"] == []
    assert artifact["counts"] == {
        "source_ways_with_conditional_tags": 1,
        "normalized_conditional_source_ways": 1,
        "normalized_conditional_rules": 1,
        "conditional_access_lane_tuples": 14,
        "lane_tuples_with_applicable_conditional_rules": 1,
        "conditional_access_blockers": 0,
        "upstream_static_access_blockers": 0,
        "upstream_lane_blockers": 0,
        "upstream_relation_blockers": 0,
    }
    matched = [
        item
        for item in artifact["access_candidates"]
        if item["applicable_conditional_rule_ids"]
    ]
    assert len(matched) == 1
    assert matched[0]["conditional_effects"] == ["denied"]
    assert matched[0]["pending_final_permission_resolution"] is True


def test_production_fixture_is_deterministic() -> None:
    context = {"weekday": "Mo", "time": "08:00"}
    first = build_conditional_access_production_artifact(
        FIXTURE, profile="formal", scenario_context=context
    )
    second = build_conditional_access_production_artifact(
        FIXTURE, profile="formal", scenario_context=context
    )
    assert first == second
