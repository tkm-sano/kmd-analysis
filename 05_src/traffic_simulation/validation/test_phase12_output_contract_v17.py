from __future__ import annotations

import copy

import pytest
import yaml

from traffic_simulation.network.validate_v17_phase12_output_contract import (
    CONTRACT_PATH,
    Phase12OutputContractError,
    validate_adoption_record,
    validate_output_contract,
)


def contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_fixed_contract_and_adoption_record_pass() -> None:
    result = validate_adoption_record()
    assert result["required_artifact_count"] == 8
    assert result["determinism_artifact_count"] == 5
    assert result["required_run_count"] == 2


def test_artifact_paths_are_unique() -> None:
    value = contract()
    value["artifact_catalog"][1]["path_template"] = value["artifact_catalog"][0][
        "path_template"
    ]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_required_artifact_cannot_be_omitted() -> None:
    value = contract()
    value["artifact_catalog"] = value["artifact_catalog"][:-1]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_formal_model_assumption_is_rejected() -> None:
    value = contract()
    value["profiles"]["formal"]["allow_model_assumed"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_structural_profile_cannot_become_acceptance_eligible() -> None:
    value = contract()
    value["profiles"]["structural"]["acceptance_eligible"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_cross_unit_simple_sum_is_rejected() -> None:
    value = contract()
    value["population_accounting"]["cross_unit_simple_sum_allowed"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_upstream_and_permission_simple_sum_is_rejected() -> None:
    value = contract()
    value["population_accounting"][
        "upstream_and_permission_blockers_simple_sum_allowed"
    ] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_determinism_set_must_match_catalog() -> None:
    value = contract()
    value["determinism"]["compare_artifact_ids"] = value["determinism"][
        "compare_artifact_ids"
    ][:-1]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_contract_validation_does_not_mutate_input() -> None:
    value = contract()
    before = copy.deepcopy(value)
    validate_output_contract(value)
    assert value == before
