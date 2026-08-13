"""Govern formal v17 evidence methods and reject unapproved imputation."""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/formal_evidence_methods_v17.yml"
)
REGISTRY_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/formal_evidence_methods_v17.schema.json"
)
MANUAL_EVIDENCE_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/manual_evidence_record_v17.schema.json"
)
EVIDENCE_ORIGINS = frozenset({"evidence_derived", "derived_validated_model"})
HASH_PATTERN = "0123456789abcdef"
REQUIRED_DONOR_ELIGIBILITY = frozenset(
    {
        "eligible_population_match",
        "formal_direction_resolved",
        "formal_directional_lanes_resolved_when_relevant",
        "formal_speed_resolved_when_relevant",
        "no_relevant_unsupported_conditional",
        "formal_permissions_resolved_when_relevant",
        "no_structural_assumption",
        "not_model_assumed",
        "traceable_source_hash",
        "traceable_configuration_hash",
    }
)


class EvidenceResolutionError(ValueError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceResolutionError(
            f"YAML root must be an object: {path}",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceResolutionError(
            f"JSON root must be an object: {path}",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    return value


def _validate_schema(instance: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(instance)
    except jsonschema.ValidationError as error:
        raise EvidenceResolutionError(
            f"evidence Schema violation: {error.message}",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        ) from error


@lru_cache(maxsize=1)
def load_evidence_method_registry() -> dict[str, Any]:
    registry = _load_yaml(REGISTRY_PATH)
    validate_evidence_method_registry(registry)
    return registry


def validate_evidence_method_registry(registry: Mapping[str, Any]) -> None:
    _validate_schema(registry, REGISTRY_SCHEMA_PATH)
    methods = list(registry["methods"])
    ids = [item["method_id"] for item in methods]
    if len(ids) != len(set(ids)):
        raise EvidenceResolutionError(
            "duplicate evidence method ID",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if registry["approved_method_count"] != len(methods):
        raise EvidenceResolutionError(
            "approved evidence method count differs",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if not methods and not registry.get("no_method_approval_reason"):
        raise EvidenceResolutionError(
            "empty evidence registry has no recorded reason",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if set(registry["minimum_donor_eligibility"]) != REQUIRED_DONOR_ELIGIBILITY:
        raise EvidenceResolutionError(
            "minimum donor eligibility differs from the formal contract",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if any(
        not REQUIRED_DONOR_ELIGIBILITY.issubset(item["donor_eligibility"])
        for item in methods
    ):
        raise EvidenceResolutionError(
            "approved method omits a mandatory donor eligibility check",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )


def canonical_manual_evidence_hash(record: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(value) for key, value in record.items() if key != "evidence_sha256"}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_manual_evidence_record(record: Mapping[str, Any]) -> None:
    _validate_schema(record, MANUAL_EVIDENCE_SCHEMA_PATH)
    if record["evidence_sha256"] != canonical_manual_evidence_hash(record):
        raise EvidenceResolutionError(
            "manual evidence hash differs",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if record["production_output_edit"] is not False or record["requires_regeneration"] is not True:
        raise EvidenceResolutionError(
            "manual evidence attempted a direct production edit",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )


def _is_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HASH_PATTERN for character in value)
    )


def validate_formal_donor(
    donor: Mapping[str, Any], *, method: Mapping[str, Any]
) -> None:
    checks = {
        "eligible_population_match": donor.get("eligible_population_match") is True,
        "formal_direction_resolved": donor.get("formal_direction_resolved") is True,
        "formal_directional_lanes_resolved_when_relevant": donor.get(
            "formal_directional_lanes_resolved_when_relevant"
        )
        is True,
        "formal_speed_resolved_when_relevant": donor.get(
            "formal_speed_resolved_when_relevant"
        )
        is True,
        "no_relevant_unsupported_conditional": donor.get(
            "no_relevant_unsupported_conditional"
        )
        is True,
        "formal_permissions_resolved_when_relevant": donor.get(
            "formal_permissions_resolved_when_relevant"
        )
        is True,
        "no_structural_assumption": not donor.get("assumption_ids"),
        "not_model_assumed": donor.get("value_origin") != "model_assumed",
        "traceable_source_hash": _is_hash(donor.get("source_sha256")),
        "traceable_configuration_hash": _is_hash(
            donor.get("configuration_sha256")
        ),
    }
    required = set(method["donor_eligibility"])
    if donor.get("resolution_status") != "resolved" or any(
        not checks.get(requirement, False) for requirement in required
    ):
        raise EvidenceResolutionError(
            "formal evidence donor is ineligible",
            stop_code="EVIDENCE_DONOR_INELIGIBLE",
            status="invalid",
        )


def resolve_evidence_request(
    request: Mapping[str, Any], *, registry: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    selected_registry = copy.deepcopy(dict(registry or load_evidence_method_registry()))
    validate_evidence_method_registry(selected_registry)
    if request.get("production_output_edit") is True:
        raise EvidenceResolutionError(
            "evidence requests may not edit production output directly",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    method_id = request.get("method_id")
    method = next(
        (item for item in selected_registry["methods"] if item["method_id"] == method_id),
        None,
    )
    if method is None or method.get("status") != "approved":
        raise EvidenceResolutionError(
            f"evidence method is not approved: {method_id}",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if request.get("target_attribute") != method["target_attribute"]:
        raise EvidenceResolutionError(
            "evidence method target attribute differs",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if request.get("requested_origin") != method["output_origin"]:
        raise EvidenceResolutionError(
            "evidence method output origin differs",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    if request.get("eligible_population_match") is not True:
        raise EvidenceResolutionError(
            "target is outside or unverified against the eligible population",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    inputs = request.get("inputs")
    if not isinstance(inputs, Mapping) or any(
        name not in inputs for name in method["required_inputs"]
    ):
        raise EvidenceResolutionError(
            "evidence method required input is missing",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    manual = request.get("manual_evidence")
    if manual is not None:
        if not isinstance(manual, Mapping):
            raise EvidenceResolutionError(
                "manual evidence is not a separate record",
                stop_code="EVIDENCE_METHOD_NOT_APPROVED",
                status="unresolved",
            )
        validate_manual_evidence_record(manual)
    donors = request.get("donors")
    if not isinstance(donors, Sequence) or isinstance(donors, (str, bytes)) or not donors:
        raise EvidenceResolutionError(
            "evidence method has no donor",
            stop_code="EVIDENCE_DONOR_INELIGIBLE",
            status="invalid",
        )
    for donor in donors:
        if not isinstance(donor, Mapping):
            raise EvidenceResolutionError(
                "evidence donor is not an object",
                stop_code="EVIDENCE_DONOR_INELIGIBLE",
                status="invalid",
            )
        validate_formal_donor(donor, method=method)
    estimator = method["estimator_or_model"].get("type")
    if estimator != "identity_single_donor" or len(donors) != 1:
        raise EvidenceResolutionError(
            "evidence estimator implementation is not registered",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    value = copy.deepcopy(donors[0].get("effective_value"))
    if value is None:
        raise EvidenceResolutionError(
            "evidence donor has no effective value",
            stop_code="EVIDENCE_DONOR_INELIGIBLE",
            status="invalid",
        )
    return {
        "resolution_status": "resolved",
        "value_origin": method["output_origin"],
        "effective_value": value,
        "method_id": method["method_id"],
        "donor_record_ids": sorted(str(item["record_id"]) for item in donors),
        "assumption_ids": [],
        "stop_code": None,
        "review_required": False,
        "provenance": {
            "method_id": method["method_id"],
            "registry_id": selected_registry["registry_id"],
            "registry_version": selected_registry["registry_version"],
            "implementation_hash": method["implementation_hash"],
            "fixture_hash": method["fixture_hash"],
            "oracle_hash": method["oracle_hash"],
            "validation_dataset": copy.deepcopy(method["validation_dataset"]),
            "validation_metrics": copy.deepcopy(method["validation_metrics"]),
            "acceptance_thresholds": copy.deepcopy(method["acceptance_thresholds"]),
            "uncertainty_output": copy.deepcopy(method["uncertainty_output"]),
            "manual_evidence_record_id": None
            if manual is None
            else manual["evidence_record_id"],
            "regenerated_complete_artifact_required": True,
        },
    }


def audit_production_origins(
    collections: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_registry = dict(registry or load_evidence_method_registry())
    approved = {item["method_id"] for item in selected_registry["methods"]}
    origins: dict[str, int] = {}
    stage_counts: dict[str, int] = {}
    unapproved: list[dict[str, Any]] = []
    for stage, records in sorted(collections.items()):
        stage_counts[stage] = len(records)
        for record in records:
            origin = record.get("value_origin")
            if origin is not None:
                origins[str(origin)] = origins.get(str(origin), 0) + 1
            if origin in EVIDENCE_ORIGINS:
                provenance = record.get("provenance", {})
                method_id = provenance.get("method_id") if isinstance(provenance, Mapping) else None
                if method_id not in approved:
                    unapproved.append(
                        {"stage": stage, "record_id": record.get("record_id"), "method_id": method_id}
                    )
    if unapproved:
        raise EvidenceResolutionError(
            "production emitted an unapproved evidence-derived value",
            stop_code="EVIDENCE_METHOD_NOT_APPROVED",
            status="unresolved",
        )
    payload = {
        "approved_method_count": len(approved),
        "stage_record_counts": stage_counts,
        "value_origin_counts": dict(sorted(origins.items())),
        "evidence_derived_count": origins.get("evidence_derived", 0),
        "derived_validated_model_count": origins.get("derived_validated_model", 0),
        "unapproved_evidence_emission_count": 0,
    }
    payload["semantic_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload
