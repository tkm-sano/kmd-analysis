from __future__ import annotations

import json
from copy import deepcopy

import jsonschema
import pytest
import yaml

from traffic_simulation.network.approved_attribute_resolution_policy import (
    AccessRule,
    ApprovedPolicyError,
    build_way_directions,
    dominates,
    resolve_access_rules,
    validate_approved_policy,
)
from traffic_simulation.paths import REPOSITORY_ROOT


def _rule(
    rule_id: str,
    *,
    spatial: str = "way",
    vehicle: str = "access",
    temporal: str = "unconditional",
    purpose: str = "general",
    result: str = "yes",
    applicable: bool = True,
) -> AccessRule:
    return AccessRule(
        rule_id=rule_id,
        spatial_scope=spatial,
        vehicle_scope=vehicle,
        temporal_scope=temporal,
        purpose_scope=purpose,
        result=result,
        applicable=applicable,
    )


def test_machine_readable_policy_and_vehicle_profile_validate() -> None:
    """RS-TST-018/RS-TST-020: validate vehicle and permission authority policy."""
    policy = validate_approved_policy()
    assert policy["policy_id"] == "ota_ward_attribute_resolution_policy_v17"
    assert policy["formal_build_ready"] is False
    assert (
        policy["managed_vehicle_profile"]["profile_id"]
        == "managed_urban_ev_delivery_v1"
    )


def test_policy_schema_rejects_a_changed_directed_road_contract() -> None:
    policy_path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/"
        "approved_attribute_resolution_policy_v17.yml"
    )
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    changed = deepcopy(policy)
    changed["directed_road_model"]["reverse_oneway_generation"] = "forward_only"
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "reproducibility/config/traffic_simulation/schemas/"
            "approved_attribute_resolution_policy.schema.json"
        ).read_text(encoding="utf-8")
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(changed)


def test_access_rule_pareto_dominance_uses_every_axis() -> None:
    """RS-TST-015: compare all four specificity coordinates."""
    general = _rule("GENERAL")
    lane_vehicle = _rule(
        "LANE-VEHICLE", spatial="lane", vehicle="vehicle_class"
    )
    purpose_only = _rule("PURPOSE", purpose="delivery")
    assert dominates(lane_vehicle, general)
    assert not dominates(lane_vehicle, purpose_only)
    assert not dominates(purpose_only, lane_vehicle)


def test_equal_maximal_access_results_are_adopted_once() -> None:
    result = resolve_access_rules(
        [
            _rule("LANE", spatial="lane", result="yes"),
            _rule("DELIVERY", purpose="delivery", result="yes"),
            _rule("GENERAL", result="no"),
        ]
    )
    assert result == {
        "resolution_status": "resolved",
        "resolved_value": "yes",
        "selected_rule_ids": ["DELIVERY", "LANE"],
        "maximal_rule_ids": ["DELIVERY", "LANE"],
        "stop_code": None,
    }


def test_different_maximal_access_results_stop_as_conflict() -> None:
    result = resolve_access_rules(
        [
            _rule("LANE", spatial="lane", result="yes"),
            _rule("DELIVERY", purpose="delivery", result="no"),
        ]
    )
    assert result["resolution_status"] == "conflict"
    assert result["stop_code"] == "ACCESS_SPECIFICITY_CONFLICT"
    assert result["maximal_rule_ids"] == ["DELIVERY", "LANE"]


def test_inactive_conditional_rule_is_not_applicable() -> None:
    result = resolve_access_rules(
        [
            _rule("BASE", result="yes"),
            _rule(
                "CONDITIONAL",
                temporal="conditional",
                result="no",
                applicable=False,
            ),
        ]
    )
    assert result["resolved_value"] == "yes"
    assert result["selected_rule_ids"] == ["BASE"]


def test_unknown_access_axis_value_fails_closed() -> None:
    with pytest.raises(ApprovedPolicyError, match="unknown spatial_scope"):
        resolve_access_rules([_rule("BAD", spatial="edge")])


def test_reverse_oneway_builds_only_backward_directed_segment() -> None:
    """RS-TST-017: map reverse one-way input to one backward segment."""
    segments = build_way_directions(
        source_way_id=123,
        source_segment_index=7,
        source_node_ids=[10, 20, 30],
        oneway="-1",
    )
    assert len(segments) == 1
    segment = segments[0]
    assert segment["directed_segment_id"] == (
        "way/123/segment/0007/direction/B"
    )
    assert segment["source_node_ids"] == [10, 20, 30]
    assert segment["travel_node_ids"] == [30, 20, 10]
    assert segment["travel_from_node"] == 30
    assert segment["travel_to_node"] == 10


def test_bidirectional_way_uses_stable_forward_and_backward_ids() -> None:
    """ARC-TST-007: derive stable direction IDs from source lineage."""
    first = build_way_directions(
        source_way_id=456,
        source_segment_index=0,
        source_node_ids=[1, 2],
        oneway="no",
    )
    second = build_way_directions(
        source_way_id=456,
        source_segment_index=0,
        source_node_ids=[1, 2],
        oneway="no",
    )
    assert first == second
    assert [item["direction_relative_to_way"] for item in first] == [
        "forward",
        "backward",
    ]


def test_invalid_directed_segment_input_fails_closed() -> None:
    with pytest.raises(ApprovedPolicyError, match="at least two nodes"):
        build_way_directions(
            source_way_id=1,
            source_segment_index=0,
            source_node_ids=[10],
            oneway="yes",
        )


def test_v17_resolution_schema_accepts_two_fields_and_rejects_legacy() -> None:
    """RS-TST-016: enforce the v17 two-field state contract."""
    schema_path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/schemas/"
        "attribute_resolution_v2.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    record = {
        "resolution_action": "adopt_explicit",
        "resolution_rule_id": None,
        "resolution_status": "resolved",
        "value_origin": "source_explicit",
        "resolved_value": 2,
        "unit": "lane",
        "review_status": "machine_classified",
        "stop_failure_codes": [],
        "assumption_id": None,
        "formal_eligible": True,
    }
    jsonschema.Draft202012Validator(schema).validate(record)

    legacy = dict(record, value_state="explicit_osm")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(legacy)


def test_v17_resolution_schema_rejects_formal_model_assumption() -> None:
    """RS-TST-019: prohibit a structural lane assumption as formal."""
    schema_path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/schemas/"
        "attribute_resolution_v2.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    record = {
        "resolution_action": "apply_structural_placeholder",
        "resolution_rule_id": "BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1",
        "resolution_status": "resolved",
        "value_origin": "model_assumed",
        "resolved_value": 1,
        "unit": "lane",
        "review_status": "machine_classified",
        "stop_failure_codes": [],
        "assumption_id": "BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1",
        "formal_eligible": True,
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(record)
