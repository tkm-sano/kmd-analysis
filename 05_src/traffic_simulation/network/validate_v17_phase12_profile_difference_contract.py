"""Validate the approved Phase 12 v1.1 profile-difference authority bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DECISION_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/decisions/"
    "phase12_decision_a_formal_only_profile_difference_v1_1.yml"
)
AMENDMENT_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/"
    "v17_phase12_output_contract_profile_difference_v1_2.yml"
)
BASE_CONTRACT_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml"
)
SCHEMA_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "phase12_population_accounting_v17_2.schema.json"
)
DETERMINISM_SCHEMA_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "phase12_successor_determinism_report_v1.schema.json"
)
LANE_DECISIONS = (
    REPOSITORY_ROOT / (
        "reproducibility/config/traffic_simulation/"
        "v17_phase13_lane_bidirectional_lanes2_formal_decision.yml"
    ),
    REPOSITORY_ROOT / (
        "reproducibility/config/traffic_simulation/"
        "v17_phase13_lane_count_from_road_lane_vector_decision.yml"
    ),
)


class ProfileDifferenceContractError(ValueError):
    pass


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProfileDifferenceContractError(f"YAML root is not an object: {path}")
    return value


def _repo_path(value: str) -> Path:
    path = (REPOSITORY_ROOT / value).resolve()
    if not path.is_relative_to(REPOSITORY_ROOT.resolve()) or not path.is_file():
        raise ProfileDifferenceContractError(f"invalid repository reference: {value}")
    return path


def validate_profile_difference_contract(
    *,
    decision_path: Path = DECISION_PATH,
    amendment_path: Path = AMENDMENT_PATH,
) -> Mapping[str, Any]:
    decision = _yaml(decision_path)
    amendment = _yaml(amendment_path)
    base_contract = _yaml(BASE_CONTRACT_PATH)
    if decision.get("decision_id") != "DEC-P12-FORMAL-ONLY-PROFILE-DIFFERENCE-002":
        raise ProfileDifferenceContractError("decision identity differs")
    if decision.get("status") != "adopted" or decision.get("adopted_by") != "repository_owner_directive":
        raise ProfileDifferenceContractError("decision is not owner-approved")
    if amendment.get("status") != "fixed" or amendment.get("effective_contract_version") != "1.2.0":
        raise ProfileDifferenceContractError("contract amendment state/version differs")
    if _repo_path(amendment["base_contract"]) != BASE_CONTRACT_PATH.resolve():
        raise ProfileDifferenceContractError("base contract reference differs")
    if _repo_path(amendment["decision"]) != decision_path.resolve():
        raise ProfileDifferenceContractError("decision reference differs")
    if _repo_path(amendment["normative_specification"]) != _repo_path(decision["normative_specification"]):
        raise ProfileDifferenceContractError("normative specification references differ")

    approved_rule_ids = set(decision["authorized_rules"])
    authoritative_rule_ids = {
        _yaml(path)["decision"]["rule_id"] for path in LANE_DECISIONS
    }
    if approved_rule_ids != authoritative_rule_ids:
        raise ProfileDifferenceContractError(
            "Formal-only lane allowlist differs from approved lane decisions"
        )
    for rule_id, spec in decision["authorized_rules"].items():
        if not spec.get("formal_applicable") or spec.get("value_origin") != "rule_derived":
            raise ProfileDifferenceContractError(f"authorized rule is not Formal-applicable: {rule_id}")
        if not any(
            _yaml(path).get("decision_id") == spec.get("decision_id")
            for path in LANE_DECISIONS
        ):
            raise ProfileDifferenceContractError(f"authorized rule decision is not traceable: {rule_id}")
    conditions = set(decision["authorized_formal_only"]["required_conditions"])
    required_conditions = set(decision["authorized_formal_only"]["required_conditions"])
    if not required_conditions.issubset(conditions):
        raise ProfileDifferenceContractError("required fail-closed conditions are absent")
    gate = amendment["overrides"]["profile_difference_gate"]
    if gate.get("unauthorized_formal_only_count_must_equal") != 0 or gate.get("same_identity_inconsistent_count_must_equal") != 0:
        raise ProfileDifferenceContractError("Decision A zero gates are not zero")
    if amendment["overrides"]["execution_output_root"] == base_contract["execution"]["output_root"]:
        raise ProfileDifferenceContractError("successor output would overwrite v1.0 output")
    if _repo_path(amendment["overrides"]["population_accounting_schema"]) != SCHEMA_PATH.resolve():
        raise ProfileDifferenceContractError("accounting Schema reference differs")
    if _repo_path(amendment["overrides"]["determinism_report_schema"]) != DETERMINISM_SCHEMA_PATH.resolve():
        raise ProfileDifferenceContractError("determinism Schema reference differs")

    for schema_path in (SCHEMA_PATH, DETERMINISM_SCHEMA_PATH):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    specification = _repo_path(decision["normative_specification"]).read_text(encoding="utf-8")
    for token in (
        decision["decision_id"],
        "authorized_formal_only",
        "unauthorized_formal_only",
        "same_identity_inconsistent",
        "Formal Network Acceptance",
    ):
        if token not in specification:
            raise ProfileDifferenceContractError(f"normative token is absent: {token}")
    return {
        "decision": "passed",
        "amendment": "passed",
        "approved_rule_allowlist": "passed",
        "schema": "passed",
        "normative_specification": "passed",
        "result": "passed",
    }


def main() -> int:
    try:
        result = validate_profile_difference_contract()
    except Exception as error:
        print(json.dumps({"result": "failed", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
