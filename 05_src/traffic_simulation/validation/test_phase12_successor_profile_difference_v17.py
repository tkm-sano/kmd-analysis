from __future__ import annotations

from pathlib import Path
import copy
import json

from jsonschema import Draft202012Validator
import pytest

import yaml

from traffic_simulation.network.validate_v17_phase12_successor_run import (
    build_profile_population_difference,
)
from traffic_simulation.network.validate_v17_phase12_profile_difference_contract import (
    validate_profile_difference_contract,
)


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = yaml.safe_load((
    ROOT / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
).read_text(encoding="utf-8"))
DECISION = yaml.safe_load((
    ROOT / "reproducibility/config/traffic_simulation/decisions/phase12_decision_a_formal_only_profile_difference_v1_1.yml"
).read_text(encoding="utf-8"))


def _stage(*, rule_id: str, formal: bool, permission: bool = True) -> dict:
    segment = "ds:1:10:11:forward"
    result = {
        "directional_lanes": {
            "segment_lanes": [{
                "directed_segment_id": segment,
                "source_way_id": 1,
                "source_direction": "forward",
                "moving_lane_count": 1,
                "value_origin": "rule_derived" if formal else "model_assumed",
                "rule_ids": [rule_id] if formal else [],
                "assumption_ids": [] if formal else ["BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"],
                "formal_eligible": formal,
                "lanes": [{"lane_position": 0, "sumo_lane_index": 0, "source_vector_values": {"turn:lanes": "through"}}],
            }]
        },
        "final_permission": {"permission_records": []},
    }
    if permission:
        result["final_permission"]["permission_records"].append({
            "permission_record_id": "a" * 64,
            "source_way_id": 1,
            "directed_segment_id": segment,
            "lane_position": 0,
            "vehicle_class": "delivery",
            "resolution_status": "resolved",
            "value_origin": "rule_derived",
            "maximal_rule_ids": ["access:1"],
        })
    return result


def _empty_stage() -> dict:
    return {
        "directional_lanes": {"segment_lanes": []},
        "final_permission": {"permission_records": []},
    }


def test_profile_difference_authority_bundle_is_consistent() -> None:
    assert validate_profile_difference_contract()["result"] == "passed"


def test_adopted_rule_derived_formal_only_lane_and_permission_are_allowed() -> None:
    result = build_profile_population_difference(
        _empty_stage(),
        _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True),
        registry=REGISTRY,
        decision=DECISION,
    )

    assert result["lane_identities"]["authorized_formal_only_count"] == 1
    assert result["permission_identities"]["authorized_formal_only_count"] == 1
    assert result["unauthorized_formal_only_count"] == 0
    assert result["gate_result"] == "passed"


def test_unapproved_rule_formal_only_difference_fails_closed() -> None:
    result = build_profile_population_difference(
        _empty_stage(),
        _stage(rule_id="UNREGISTERED_FORMAL_RULE", formal=True),
        registry=REGISTRY,
        decision=DECISION,
    )

    assert result["unauthorized_formal_only_count"] == 2
    assert result["gate_result"] == "failed"


def test_missing_rule_provenance_is_not_treated_as_source_evidence() -> None:
    formal = _stage(
        rule_id="OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1", formal=True
    )
    formal["directional_lanes"]["segment_lanes"][0]["rule_ids"] = []

    result = build_profile_population_difference(
        _empty_stage(), formal, registry=REGISTRY, decision=DECISION
    )

    assert result["lane_identities"]["unauthorized_formal_only_count"] == 1
    assert result["permission_identities"]["unauthorized_formal_only_count"] == 1
    assert result["gate_result"] == "failed"


def test_unresolved_permission_identity_may_be_explained_but_stays_unresolved() -> None:
    formal = _stage(
        rule_id="OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1", formal=True
    )
    permission = formal["final_permission"]["permission_records"][0]
    permission.update({
        "resolution_status": "unresolved",
        "value_origin": None,
        "maximal_rule_ids": [],
    })

    result = build_profile_population_difference(
        _empty_stage(), formal, registry=REGISTRY, decision=DECISION
    )

    record = result["permission_identities"]["records"][0]
    assert record["classification"] == "authorized_formal_only"
    assert result["gate_result"] == "passed"


def test_structural_only_identity_without_registered_assumption_fails_gate() -> None:
    structural = _stage(rule_id="", formal=False)
    structural["directional_lanes"]["segment_lanes"][0]["assumption_ids"] = []

    result = build_profile_population_difference(
        structural, _empty_stage(), registry=REGISTRY, decision=DECISION
    )

    assert result["gate_result"] == "failed"
    assert result["gate_result"] == "failed"


def test_missing_decision_is_rejected() -> None:
    decision = copy.deepcopy(DECISION)
    decision["decision_id"] = "UNKNOWN"
    with pytest.raises(ValueError, match="Decision A identity"):
        build_profile_population_difference(_empty_stage(), _empty_stage(), registry=REGISTRY, decision=decision)


def test_unauthorized_formal_assumption_fails() -> None:
    formal = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True)
    formal["directional_lanes"]["segment_lanes"][0]["assumption_ids"] = ["BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"]
    result = build_profile_population_difference(_empty_stage(), formal, registry=REGISTRY, decision=DECISION)
    assert result["unauthorized_formal_only_count"] == 2


def test_permission_only_divergence_without_lane_difference_fails() -> None:
    structural = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=False, permission=False)
    formal = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=False, permission=True)
    result = build_profile_population_difference(structural, formal, registry=REGISTRY, decision=DECISION)
    assert result["permission_identities"]["unauthorized_formal_only_count"] == 1
    assert result["gate_result"] == "failed"


def test_permission_lane_lineage_mismatch_fails() -> None:
    formal = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True)
    formal["final_permission"]["permission_records"][0]["source_way_id"] = 99
    result = build_profile_population_difference(_empty_stage(), formal, registry=REGISTRY, decision=DECISION)
    assert result["permission_identities"]["unauthorized_formal_only_count"] == 1


def test_accounting_counts_are_recomputable_not_tamperable() -> None:
    result = build_profile_population_difference(
        _empty_stage(), _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True), registry=REGISTRY, decision=DECISION
    )
    assert result["lane_identities"]["formal_count"] == result["lane_identities"]["common_count"] + result["lane_identities"]["formal_only_count"]


def test_v17_2_identity_schema_and_lineage_include_source_way_id() -> None:
    result = build_profile_population_difference(
        _empty_stage(), _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True), registry=REGISTRY, decision=DECISION
    )
    schema = json.loads((ROOT / "reproducibility/config/traffic_simulation/schemas/phase12_population_accounting_v17_2.schema.json").read_text())
    identity_schema = schema["$defs"]["identity"]
    for section in ("lane_identities", "permission_identities"):
        identity = result[section]["records"][0]["identity"]
        Draft202012Validator(identity_schema).validate(identity)
        assert identity["source_way_id"] == 1
    assert result["lane_identities"]["records"][0]["identity"]["source_way_id"] == result["permission_identities"]["records"][0]["identity"]["source_way_id"]


def test_missing_source_way_provenance_fails_instead_of_null_fallback() -> None:
    formal = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True)
    del formal["directional_lanes"]["segment_lanes"][0]["source_way_id"]
    with pytest.raises((KeyError, ValueError)):
        build_profile_population_difference(_empty_stage(), formal, registry=REGISTRY, decision=DECISION)


def test_fabricated_permission_source_way_id_is_rejected_by_lineage() -> None:
    formal = _stage(rule_id="OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", formal=True)
    formal["final_permission"]["permission_records"][0]["source_way_id"] = 999
    result = build_profile_population_difference(_empty_stage(), formal, registry=REGISTRY, decision=DECISION)
    assert result["permission_identities"]["unauthorized_formal_only_count"] == 1
    assert result["permission_identities"]["records"][0]["identity"]["source_way_id"] == 999
