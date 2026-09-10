from __future__ import annotations

import copy

import pytest
import yaml

from traffic_simulation.network.validate_v17_network_completion_policy import (
    NetworkCompletionPolicyError,
    REGISTRY_PATH,
    validate_network_completion_policy,
)


def registry() -> dict:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def method(value: dict, method_id: str) -> dict:
    return next(item for item in value["methods"] if item["method_id"] == method_id)


def test_adopted_network_completion_policy_validates() -> None:
    result = validate_network_completion_policy()
    assert result["network_completion_policy"] == "passed"
    assert result["gated_methods_activated"] == 0
    assert result["production_actions_performed"] is False


def test_type_default_cannot_enter_formal_allowlist() -> None:
    changed = copy.deepcopy(registry())
    method(changed, "SUMO_TYPEMAP_DEFAULT")["status"] = "FORMAL_ALLOWED_NOW"
    with pytest.raises(NetworkCompletionPolicyError):
        validate_network_completion_policy(changed)


def test_prohibited_method_status_is_normatively_fixed() -> None:
    changed = copy.deepcopy(registry())
    method(changed, "ML_LEGAL_ACCESS_GRANT")["status"] = "FORMAL_ALLOWED_NOW"
    with pytest.raises(NetworkCompletionPolicyError, match="normative method status allowlist"):
        validate_network_completion_policy(changed)


def test_simulation_method_cannot_claim_formal_output() -> None:
    changed = copy.deepcopy(registry())
    method(changed, "ROAD_TYPE_DEFAULT")["formal_value_producer"] = True
    with pytest.raises(NetworkCompletionPolicyError, match="non-activated method"):
        validate_network_completion_policy(changed)


def test_gated_model_requires_missing_domain_validation() -> None:
    changed = copy.deepcopy(registry())
    target = method(changed, "VALIDATED_STATISTICAL_ML_PREDICTION")
    target["required_validation"].remove("missing_domain_validation")
    with pytest.raises(NetworkCompletionPolicyError, match="omits promotion gate"):
        validate_network_completion_policy(changed)


def test_formal_and_simulation_epistemic_classes_must_be_separate() -> None:
    changed = copy.deepcopy(registry())
    changed["epistemic_classes"]["formal"].append("TYPE_DEFAULTED")
    with pytest.raises(NetworkCompletionPolicyError):
        validate_network_completion_policy(changed)


def test_prohibited_method_cannot_appear_in_formal_hierarchy() -> None:
    changed = copy.deepcopy(registry())
    changed["resolution_hierarchies"]["permission_access"]["formal_priority"].append("ML_LEGAL_ACCESS_GRANT")
    with pytest.raises(NetworkCompletionPolicyError, match="non-Formal method"):
        validate_network_completion_policy(changed)


def test_governance_fallback_status_is_normatively_fixed() -> None:
    changed = copy.deepcopy(registry())
    method(changed, "GOVERNANCE_FALLBACK")["status"] = "PROHIBITED"
    with pytest.raises(NetworkCompletionPolicyError, match="normative method status allowlist"):
        validate_network_completion_policy(changed)


def test_authority_artifacts_are_hash_locked() -> None:
    changed = copy.deepcopy(registry())
    changed["authority_artifacts"][0]["sha256"] = "0" * 64
    with pytest.raises(NetworkCompletionPolicyError, match="authority artifact hash mismatch"):
        validate_network_completion_policy(changed)
