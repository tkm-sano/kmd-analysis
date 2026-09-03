"""Validate the adopted Formal network-completion Decision and method registry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/network_completion_method_registry_v17.yml"
SCHEMA_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/schemas/network_completion_policy_v17.schema.json"
FORMAL_METHODS_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/formal_evidence_methods_v17.yml"
EXPECTED_STATUSES = {
    "FORMAL_ALLOWED_NOW",
    "FORMAL_ALLOWED_AFTER_VALIDATION",
    "SIMULATION_ONLY",
    "PROHIBITED",
    "UNRESOLVED_RESEARCH_DECISION_REQUIRED",
}
FORMAL_EPISTEMIC = {
    "OBSERVED", "NORMALIZED", "DETERMINISTIC_DERIVED",
    "EXTERNAL_DATA_DERIVED", "VALIDATED_LOCAL_INFERRED", "VALIDATED_MODEL_DERIVED",
}
SIMULATION_EPISTEMIC = {"TYPE_DEFAULTED", "SIMULATION_DEFAULTED", "CONSERVATIVE_FALLBACK"}
PROMOTION_GATES = {
    "train_test_way_separation", "spatial_corridor_holdout", "explicit_domain_validation",
    "missing_domain_validation", "external_validation", "accuracy", "mae", "bias",
    "calibration_confidence", "abstention_support", "provenance_completeness",
    "deterministic_regeneration", "sensitivity_analysis",
}
EXPECTED_METHOD_STATUS = {
    "EXPLICIT_SOURCE_EVIDENCE": "FORMAL_ALLOWED_NOW",
    "SOURCE_VALUE_NORMALIZATION": "FORMAL_ALLOWED_NOW",
    "ADOPTED_DETERMINISTIC_DERIVED_RULE": "FORMAL_ALLOWED_NOW",
    "VALIDATED_EXTERNAL_OFFICIAL_DATA": "FORMAL_ALLOWED_AFTER_VALIDATION",
    "VALIDATED_LOCAL_CORRIDOR_PROPAGATION": "FORMAL_ALLOWED_AFTER_VALIDATION",
    "VALIDATED_EMPIRICAL_GROUP_MODEL": "FORMAL_ALLOWED_AFTER_VALIDATION",
    "VALIDATED_STATISTICAL_ML_PREDICTION": "FORMAL_ALLOWED_AFTER_VALIDATION",
    "VEHICLE_SPECIFIC_ACCESS_EVIDENCE": "FORMAL_ALLOWED_NOW",
    "DETERMINISTIC_OSM_ACCESS_SEMANTICS": "FORMAL_ALLOWED_NOW",
    "VALIDATED_POLICY_DERIVED_ACCESS": "FORMAL_ALLOWED_AFTER_VALIDATION",
    "ROAD_TYPE_DEFAULT": "SIMULATION_ONLY",
    "SUMO_TYPEMAP_DEFAULT": "SIMULATION_ONLY",
    "MATSIM_DEFAULT": "SIMULATION_ONLY",
    "CONSERVATIVE_SIMULATION_FALLBACK": "SIMULATION_ONLY",
    "GOVERNANCE_FALLBACK": "UNRESOLVED_RESEARCH_DECISION_REQUIRED",
    "FAIL_CLOSED_CONFLICT_RESOLUTION": "FORMAL_ALLOWED_NOW",
    "ML_LEGAL_ACCESS_GRANT": "PROHIBITED",
    "SILENT_OR_UNREGISTERED_INFERENCE": "PROHIBITED",
}


class NetworkCompletionPolicyError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NetworkCompletionPolicyError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NetworkCompletionPolicyError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _method_sets(methods: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {
        status: {item["method_id"] for item in methods if item["status"] == status}
        for status in EXPECTED_STATUSES
    }


def validate_network_completion_policy(registry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    selected = dict(registry) if registry is not None else _load_yaml(REGISTRY_PATH)
    schema = _load_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(selected)
    except jsonschema.ValidationError as error:
        raise NetworkCompletionPolicyError(f"network completion schema violation: {error.message}") from error

    methods = list(selected["methods"])
    method_ids = [item["method_id"] for item in methods]
    if len(method_ids) != len(set(method_ids)):
        raise NetworkCompletionPolicyError("duplicate method ID")
    if set(selected["method_statuses"]) != EXPECTED_STATUSES:
        raise NetworkCompletionPolicyError("method status registry is incomplete")
    by_id = {item["method_id"]: item for item in methods}
    actual_method_status = {item["method_id"]: item["status"] for item in methods}
    if actual_method_status != EXPECTED_METHOD_STATUS:
        raise NetworkCompletionPolicyError("normative method status allowlist differs")
    sets = _method_sets(methods)

    formal_classes = set(selected["epistemic_classes"]["formal"])
    simulation_classes = set(selected["epistemic_classes"]["simulation_only"])
    if formal_classes != FORMAL_EPISTEMIC or simulation_classes != SIMULATION_EPISTEMIC:
        raise NetworkCompletionPolicyError("epistemic class allowlist differs")
    if formal_classes & simulation_classes:
        raise NetworkCompletionPolicyError("Formal and simulation epistemic classes overlap")

    for method in methods:
        status = method["status"]
        epistemic = method["epistemic_class"]
        if status == "SIMULATION_ONLY" and epistemic not in SIMULATION_EPISTEMIC:
            raise NetworkCompletionPolicyError(f"simulation method has non-simulation epistemic class: {method['method_id']}")
        if status in {"SIMULATION_ONLY", "PROHIBITED", "UNRESOLVED_RESEARCH_DECISION_REQUIRED", "FORMAL_ALLOWED_AFTER_VALIDATION"} and method["formal_value_producer"]:
            raise NetworkCompletionPolicyError(f"non-activated method claims Formal output: {method['method_id']}")
        if status == "FORMAL_ALLOWED_NOW" and method["formal_value_producer"] and epistemic not in FORMAL_EPISTEMIC:
            raise NetworkCompletionPolicyError(f"Formal method has disallowed epistemic class: {method['method_id']}")
        if status == "FORMAL_ALLOWED_AFTER_VALIDATION" and not PROMOTION_GATES.issubset(method["required_validation"]):
            if method["method_id"] not in {"VALIDATED_EXTERNAL_OFFICIAL_DATA", "VALIDATED_POLICY_DERIVED_ACCESS"}:
                raise NetworkCompletionPolicyError(f"gated model omits promotion gate: {method['method_id']}")

    decision_path = REPOSITORY_ROOT / selected["decision_record"]
    spec_path = REPOSITORY_ROOT / selected["normative_specification"]
    if not decision_path.is_file() or not spec_path.is_file():
        raise NetworkCompletionPolicyError("Decision or normative specification reference is missing")
    decision = _load_yaml(decision_path)
    required_decision_sections = {
        "context", "evidence", "alternatives", "benchmark_results", "decision",
        "formal_allowed_methods", "validation_gated_methods", "simulation_only_methods",
        "prohibited_methods", "attribute_hierarchies", "provenance_requirements",
        "validation_requirements", "abstention_conditions", "blocker_semantics",
        "completion_semantics", "layer_separation", "rollback_criteria",
    }
    if not required_decision_sections.issubset(decision):
        raise NetworkCompletionPolicyError("Decision Record omits a required normative section")
    if decision["decision_id"] != selected["decision_id"] or decision["status"] != "adopted":
        raise NetworkCompletionPolicyError("Decision ID/status differs from registry")
    if decision["method_registry"] != str(REGISTRY_PATH.relative_to(REPOSITORY_ROOT)) or decision["normative_specification"] != selected["normative_specification"]:
        raise NetworkCompletionPolicyError("Decision cross-reference differs from registry")
    specification = spec_path.read_text(encoding="utf-8")
    if selected["decision_id"] not in specification or str(REGISTRY_PATH.relative_to(REPOSITORY_ROOT)) not in specification:
        raise NetworkCompletionPolicyError("normative specification omits Decision or registry reference")
    expected_decision_sets = {
        "FORMAL_ALLOWED_NOW": set(decision["formal_allowed_methods"]),
        "FORMAL_ALLOWED_AFTER_VALIDATION": set(decision["validation_gated_methods"]),
        "SIMULATION_ONLY": set(decision["simulation_only_methods"]),
        "PROHIBITED": set(decision["prohibited_methods"]),
        "UNRESOLVED_RESEARCH_DECISION_REQUIRED": set(decision["unresolved_research_decision_required"]),
    }
    if sets != expected_decision_sets:
        raise NetworkCompletionPolicyError("Decision allowlists differ from method registry")

    for attribute, hierarchy in selected["resolution_hierarchies"].items():
        formal_ids = set(hierarchy["formal_priority"])
        simulation_ids = set(hierarchy["simulation_only_priority"])
        if not formal_ids.issubset(sets["FORMAL_ALLOWED_NOW"] | sets["FORMAL_ALLOWED_AFTER_VALIDATION"]):
            raise NetworkCompletionPolicyError(f"{attribute} Formal hierarchy contains a non-Formal method")
        if not simulation_ids.issubset(sets["SIMULATION_ONLY"]):
            raise NetworkCompletionPolicyError(f"{attribute} simulation hierarchy contains a non-simulation method")
        if formal_ids & simulation_ids:
            raise NetworkCompletionPolicyError(f"{attribute} hierarchies overlap")
        if any(method_id not in by_id for method_id in formal_ids | simulation_ids):
            raise NetworkCompletionPolicyError(f"{attribute} hierarchy references unknown method")

    required = set(selected["validation_gates"]["required_for_promotion"])
    if required != PROMOTION_GATES:
        raise NetworkCompletionPolicyError("promotion gate set differs")
    if selected["validation_gates"]["missing_domain_policy"] != "explicit_domain_and_missing_domain_validation_both_required":
        raise NetworkCompletionPolicyError("both validation domains are not mandatory")

    for authority in selected["authority_artifacts"]:
        path = REPOSITORY_ROOT / authority["path"]
        if not path.is_file() or _sha256(path) != authority["sha256"]:
            raise NetworkCompletionPolicyError(f"authority artifact hash mismatch: {authority['path']}")

    benchmark = _load_json(REPOSITORY_ROOT / selected["authority_artifacts"][0]["path"])
    low = benchmark["models"]["hierarchical_hybrid"]["stage_metrics"]["LOW_TYPE_FALLBACK"]
    if low["exact_accuracy"] != decision["evidence"]["rejected_candidate_hybrid"]["type_fallback_stage_accuracy"] or low["bias_pred_minus_actual"] != decision["evidence"]["rejected_candidate_hybrid"]["type_fallback_stage_bias_pred_minus_actual"]:
        raise NetworkCompletionPolicyError("Decision benchmark values differ from authority")

    existing_formal = _load_yaml(FORMAL_METHODS_PATH)
    if existing_formal["approved_method_count"] != 0 or existing_formal["methods"]:
        raise NetworkCompletionPolicyError("gated method activation occurred without this policy validator being revised")

    return {
        "network_completion_policy": "passed",
        "decision_id": selected["decision_id"],
        "method_count": len(methods),
        "formal_allowed_now_count": len(sets["FORMAL_ALLOWED_NOW"]),
        "validation_gated_count": len(sets["FORMAL_ALLOWED_AFTER_VALIDATION"]),
        "simulation_only_count": len(sets["SIMULATION_ONLY"]),
        "prohibited_count": len(sets["PROHIBITED"]),
        "authority_hash_count": len(selected["authority_artifacts"]),
        "gated_methods_activated": 0,
        "production_actions_performed": False,
    }


def main() -> int:
    try:
        result = validate_network_completion_policy()
    except (NetworkCompletionPolicyError, KeyError, TypeError) as error:
        print(json.dumps({"network_completion_policy": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
