from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    build_static_access_production_artifact,
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
    resolve_maximal_static_effect,
    static_rule_dominates,
    write_artifact_atomic,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)
BASE = {"highway": "residential", "oneway": "yes", "lanes": "2"}
PHASE13_NON_GOVERNED_FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "phase13_non_governed_vehicle_domain_fixture.yml"
)
PHASE13_NON_GOVERNED_ORACLE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "phase13_non_governed_vehicle_domain_oracle.yml"
)


def _rules(tags: dict[str, str], *, lane_counts=None, candidate_keys=None):
    return normalize_static_access_rules(
        source_way_id=1001,
        tags={**BASE, **tags},
        lane_counts=lane_counts or {"forward": 2},
        candidate_keys=candidate_keys,
    )["rules"]


def _maxima(rules, *, lane_position=0, context=None):
    return maximal_static_rules_for_tuple(
        rules,
        direction="forward",
        lane_position=lane_position,
        lane_count=2,
        vehicle_class="delivery",
        context=context or default_scenario_context(),
    )


def test_general_access_normalizes_to_schema_valid_rule() -> None:
    rules = _rules({"access": "yes"})
    assert len(rules) == 1
    assert rules[0]["effect"] == "allowed"
    assert rules[0]["target_scope"] == {
        "direction_scope": "both",
        "lane_scope": {"type": "all", "positions": []},
    }
    assert "delivery" in rules[0]["vehicle_domain"]


def test_vehicle_subset_dominates_general_access() -> None:
    rules = _rules({"access": "no", "goods": "yes"})
    maxima = _maxima(rules)
    assert len(maxima) == 1
    assert maxima[0]["source_key"] == "goods"
    assert maxima[0]["effect"] == "allowed"


def test_direction_scope_is_separate_from_vehicle_domain() -> None:
    rules = _rules({"access:forward": "no"})
    rule = rules[0]
    assert rule["target_scope"]["direction_scope"] == "forward"
    assert rule["spatial_domain"] == ["way:1001"]
    assert "forward" not in rule["spatial_domain"]


def test_lane_rules_keep_local_positions_and_empty_values() -> None:
    rules = _rules({"access:lanes": "yes||no"}, lane_counts={"forward": 3})
    assert [(r["target_scope"]["lane_scope"]["positions"], r["source_value"]) for r in rules] == [
        ([2], "no"),
        ([0], "yes"),
    ]


def test_lane_rule_dominates_general_rule_for_same_vehicle_domain() -> None:
    rules = _rules({"access": "yes", "access:lanes": "|no"})
    lane_zero = _maxima(rules, lane_position=0)
    lane_one = _maxima(rules, lane_position=1)
    assert [item["source_key"] for item in lane_zero] == ["access"]
    assert [item["source_key"] for item in lane_one] == ["access:lanes"]


def test_contextual_delivery_is_allowed_for_managed_scenario() -> None:
    maxima = _maxima(_rules({"access": "delivery"}))
    assert maxima[0]["effect"] == "allowed"
    assert maxima[0]["authorization_requirement"] == "trip_purpose_delivery"


def test_known_negative_context_evaluates_to_denied() -> None:
    maxima = _maxima(_rules({"access": "destination"}))
    assert maxima[0]["effect"] == "denied"
    assert maxima[0]["provenance"]["context_evaluation"]["matched"] is False


def test_missing_context_does_not_become_false() -> None:
    rules = _rules({"access": "destination"})
    with pytest.raises(StaticAccessError) as caught:
        _maxima(rules, context={"vehicle_class": "delivery"})
    assert caught.value.stop_code == "ACCESS_CONTEXT_MISSING"


def test_empty_permit_assignment_is_known_negative() -> None:
    maxima = _maxima(_rules({"access": "permit"}))
    assert maxima[0]["effect"] == "denied"


@pytest.mark.parametrize(
    ("value", "stop_code"),
    [("yes;no", "ACCESS_VALUE_INVALID"), ("variable", "ACCESS_VALUE_UNSUPPORTED")],
)
def test_invalid_and_unsupported_values_stop(value: str, stop_code: str) -> None:
    with pytest.raises(StaticAccessError) as caught:
        _rules({"access": value})
    assert caught.value.stop_code == stop_code


def test_unregistered_vehicle_hierarchy_stops() -> None:
    tags = {**BASE, "hovercraft": "no"}
    with pytest.raises(StaticAccessError) as caught:
        normalize_static_access_rules(
            source_way_id=1001,
            tags=tags,
            lane_counts={"forward": 2},
            candidate_keys={"hovercraft"},
        )
    assert caught.value.stop_code == "ACCESS_VEHICLE_HIERARCHY_MISSING"


def test_phase13_non_governed_vehicle_domains_do_not_change_delivery_permission() -> None:
    fixture = yaml.safe_load(PHASE13_NON_GOVERNED_FIXTURE.read_text(encoding="utf-8"))
    oracle = yaml.safe_load(PHASE13_NON_GOVERNED_ORACLE.read_text(encoding="utf-8"))
    for case in fixture["cases"]:
        tags = {
            **fixture["base_tags"],
            case["source_key"]: case["source_value"],
        }
        rules = normalize_static_access_rules(
            source_way_id=fixture["source_way_id"],
            tags=tags,
            lane_counts=fixture["lane_counts"],
        )["rules"]
        non_governed_rule = next(
            item for item in rules if item["source_key"] == case["source_key"]
        )
        assert non_governed_rule["vehicle_domain"] == oracle[
            "expected_non_governed_vehicle_domain"
        ]
        maxima = maximal_static_rules_for_tuple(
            rules,
            direction="forward",
            lane_position=0,
            lane_count=2,
            vehicle_class=oracle["governed_vehicle_class"],
            context=default_scenario_context(),
        )
        assert [item["source_key"] for item in maxima] == oracle[
            "expected_maximal_source_keys"
        ]
        assert resolve_maximal_static_effect(maxima)["effect"] == oracle[
            "expected_effect"
        ]


def test_conditional_tags_are_deferred_without_static_fallback_claim() -> None:
    result = normalize_static_access_rules(
        source_way_id=1001,
        tags={**BASE, "access:conditional": "no @ (Mo-Fr 07:00-09:00)"},
        lane_counts={"forward": 2},
    )
    assert result["rules"] == []
    assert result["deferred_conditional_tags"] == {
        "access:conditional": "no @ (Mo-Fr 07:00-09:00)"
    }


def test_incomparable_same_effect_maxima_preserve_both_provenances() -> None:
    rules = _rules({"goods": "yes", "access:lanes": "yes|"})
    maxima = _maxima(rules, lane_position=0)
    result = resolve_maximal_static_effect(maxima)
    assert len(result["maximal_rule_ids"]) == 2
    assert result["effect"] == "allowed"
    assert result["pending_final_resolution"] is True


def test_incomparable_different_effect_maxima_report_conflict() -> None:
    rules = _rules({"goods": "no", "access:lanes": "yes|"})
    maxima = _maxima(rules, lane_position=0)
    with pytest.raises(StaticAccessError) as caught:
        resolve_maximal_static_effect(maxima)
    assert caught.value.stop_code == "ACCESS_SPECIFICITY_CONFLICT"


def test_rule_order_does_not_change_maximal_set() -> None:
    rules = _rules({"access": "no", "goods": "yes"})
    first = _maxima(rules)
    second = _maxima(list(reversed(rules)))
    assert {item["rule_id"] for item in first} == {item["rule_id"] for item in second}


def test_dominance_requires_at_least_one_strict_subset() -> None:
    rule = _rules({"access": "yes"})[0]
    assert not static_rule_dominates(rule, deepcopy(rule), lane_count=2)


def test_production_fixture_normalizes_static_rules_without_finalizing_permissions() -> None:
    artifact = build_static_access_production_artifact(FIXTURE, profile="formal")
    assert artifact["blockers"] == []
    assert artifact["upstream_lane_blockers"] == []
    assert artifact["upstream_relation_blockers"] == []
    assert artifact["counts"] == {
        "source_ways_with_lane_tuples": 5,
        "normalized_source_ways": 5,
        "normalized_rules": 8,
        "static_lane_tuples": 14,
        "empty_static_maxima": 0,
        "static_conflict_candidates": 0,
        "deferred_conditional_tags": 1,
        "static_access_blockers": 0,
        "upstream_lane_blockers": 0,
        "upstream_relation_blockers": 0,
    }
    assert all(
        item["pending_final_permission_resolution"]
        for item in artifact["static_maxima"]
    )


def test_production_fixture_is_deterministic() -> None:
    first = build_static_access_production_artifact(FIXTURE, profile="formal")
    second = build_static_access_production_artifact(FIXTURE, profile="formal")
    assert first == second


def test_writer_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    artifact = build_static_access_production_artifact(FIXTURE, profile="formal")
    output = tmp_path / "static-access.json"
    write_artifact_atomic(artifact, output)
    assert json.loads(output.read_text(encoding="utf-8"))["semantic_sha256"] == artifact[
        "semantic_sha256"
    ]
    with pytest.raises(FileExistsError):
        write_artifact_atomic(artifact, output)
