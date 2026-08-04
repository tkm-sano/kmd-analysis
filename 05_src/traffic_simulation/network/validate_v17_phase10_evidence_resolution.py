from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    build_lane_production_artifact,
)
from traffic_simulation.network.evidence_resolution_v17 import (
    REGISTRY_PATH,
    EvidenceResolutionError,
    audit_production_origins,
    load_evidence_method_registry,
    resolve_evidence_request,
)
from traffic_simulation.network.final_permission_v17 import (
    build_final_permission_production_artifact,
)
from traffic_simulation.network.speed_resolution_v17 import (
    build_speed_production_artifact,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase9_speed_resolution import (
    validate_phase9_speed_resolution,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase10_completion.yml"
)
AUDIT_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase10_evidence_origin_audit.yml"
)
REGISTRY_BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"
SPEED_FIXTURE = FIXTURE_ROOT / "speed_phase9_production.osm.xml"
POINT_CONTEXT = {"weekday": "Mo", "time": "08:00"}
HASH = "a" * 64


class Phase10EvidenceResolutionError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase10EvidenceResolutionError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase10EvidenceResolutionError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase10EvidenceResolutionError(f"invalid repository artifact: {relative}")
    return path


def _indexes() -> tuple[dict[str, Any], dict[str, Any]]:
    fixtures = {
        item["fixture_id"]: item
        for item in _load_json(FIXTURE_ROOT / "inputs.json")["cases"]
    }
    oracles = {
        item["oracle_id"]: item
        for item in _load_json(FIXTURE_ROOT / "oracle.json")["oracles"]
    }
    return fixtures, oracles


def _approved_test_registry() -> dict[str, Any]:
    registry = copy.deepcopy(load_evidence_method_registry())
    registry["approved_method_count"] = 1
    registry["methods"] = [
        {
            "method_id": "FIXTURE_IDENTITY_SINGLE_DONOR_V1",
            "status": "approved",
            "target_attribute": "directional_lanes",
            "output_origin": "evidence_derived",
            "eligible_population": {"fixture_only": True},
            "required_inputs": ["target_record_id"],
            "donor_eligibility": list(registry["minimum_donor_eligibility"]),
            "estimator_or_model": {"type": "identity_single_donor"},
            "validation_dataset": {"dataset_id": "FIXTURE-DATASET", "sha256": HASH},
            "validation_metrics": {"exact_match_rate": 1.0},
            "acceptance_thresholds": {"minimum_exact_match_rate": 1.0},
            "uncertainty_output": {"type": "none"},
            "provenance_fields": ["method_id", "donor_record_ids"],
            "approver": "independent_fixture_authority",
            "approval_date": "2026-08-04",
            "implementation_hash": HASH,
            "fixture_hash": HASH,
            "oracle_hash": HASH,
        }
    ]
    return registry


def _assert_stop(request: dict[str, Any], oracle: dict[str, Any], *, registry=None) -> None:
    try:
        resolve_evidence_request(request, registry=registry)
    except EvidenceResolutionError as error:
        if error.stop_code != oracle["stop_code"] or error.status != oracle["resolution_status"]:
            raise Phase10EvidenceResolutionError(
                f"fixed evidence oracle mismatch: {oracle['oracle_id']}"
            ) from error
    else:
        raise Phase10EvidenceResolutionError(
            f"negative evidence fixture passed: {oracle['oracle_id']}"
        )


def validate_phase10_evidence_resolution() -> dict[str, Any]:
    validate_phase9_speed_resolution()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()
    registry = load_evidence_method_registry()
    bundle_ref = _load_yaml(REGISTRY_BUNDLE_PATH)["evidence_methods"]
    if bundle_ref["registry_id"] != registry["registry_id"]:
        raise Phase10EvidenceResolutionError("formal evidence registry ID mismatch")
    if bundle_ref["registry_version"] != registry["registry_version"]:
        raise Phase10EvidenceResolutionError("formal evidence registry version mismatch")
    if bundle_ref["sha256"] != _sha256(REGISTRY_PATH):
        raise Phase10EvidenceResolutionError("formal evidence registry hash mismatch")
    if bundle_ref["approved_method_count"] != registry["approved_method_count"]:
        raise Phase10EvidenceResolutionError("approved evidence method count mismatch")
    if registry["approved_method_count"] != 0 or registry["methods"]:
        raise Phase10EvidenceResolutionError("unvalidated production evidence method approved")
    if any(registry["output_policy"].values()):
        raise Phase10EvidenceResolutionError("unapproved evidence fallback enabled")

    unapproved_fixture = fixtures["V17-NEG-047"]
    _assert_stop(
        unapproved_fixture["input"], oracles[unapproved_fixture["oracle_id"]]
    )
    donor_fixture = fixtures["V17-NEG-048"]
    donor = {
        **donor_fixture["input"]["donor"],
        "record_id": "fixture-donor:1",
        "effective_value": 2,
        "resolution_status": "resolved",
        "eligible_population_match": True,
        "formal_direction_resolved": True,
        "formal_directional_lanes_resolved_when_relevant": True,
        "formal_speed_resolved_when_relevant": True,
        "no_relevant_unsupported_conditional": True,
        "formal_permissions_resolved_when_relevant": True,
        "source_sha256": HASH,
        "configuration_sha256": HASH,
    }
    _assert_stop(
        {
            "method_id": "FIXTURE_IDENTITY_SINGLE_DONOR_V1",
            "target_attribute": "directional_lanes",
            "requested_origin": "evidence_derived",
            "eligible_population_match": True,
            "inputs": {"target_record_id": "fixture-target:1"},
            "donors": [donor],
        },
        oracles[donor_fixture["oracle_id"]],
        registry=_approved_test_registry(),
    )

    lanes = build_lane_production_artifact(PRODUCTION_FIXTURE, profile="formal")
    permissions = build_final_permission_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    speeds = build_speed_production_artifact(
        SPEED_FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    collections = {
        "directional_lanes": lanes["resolutions"],
        "final_permissions": permissions["permission_records"],
        "speed": speeds["speed_records"],
    }
    audit = audit_production_origins(collections)
    repeated = audit_production_origins(collections)
    if audit != repeated:
        raise Phase10EvidenceResolutionError("two-run evidence-origin audit differs")
    if audit["stage_record_counts"] != {
        "directional_lanes": 5,
        "final_permissions": 14,
        "speed": 4,
    }:
        raise Phase10EvidenceResolutionError("production fixture audit count differs")
    if audit["evidence_derived_count"] or audit["derived_validated_model_count"]:
        raise Phase10EvidenceResolutionError("production fixture emitted evidence origin")

    full_audit = _load_yaml(AUDIT_PATH)
    if full_audit.get("result") != "passed":
        raise Phase10EvidenceResolutionError("full-population evidence audit not passed")
    full_counts = full_audit["audit"]
    if (
        full_counts["evidence_derived_count"] != 0
        or full_counts["derived_validated_model_count"] != 0
        or full_counts["unapproved_evidence_emission_count"] != 0
    ):
        raise Phase10EvidenceResolutionError("full population contains evidence emission")
    audit_payload = {
        key: copy.deepcopy(value)
        for key, value in full_counts.items()
        if key != "semantic_sha256"
    }
    audit_hash = hashlib.sha256(
        json.dumps(audit_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if audit_hash != full_counts["semantic_sha256"]:
        raise Phase10EvidenceResolutionError("full-population audit hash mismatch")
    if full_counts["stage_record_counts"] != {
        "directional_lanes": 2082,
        "final_permissions": 6984,
        "speed": 94745,
    }:
        raise Phase10EvidenceResolutionError("full-population audit count differs")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase10EvidenceResolutionError("Phase 10 completion record is not passed")
    for section in ("artifacts", "schemas", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase10EvidenceResolutionError(
                    f"Phase 10 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase10_evidence_resolution": "passed",
        "approved_production_evidence_methods": 0,
        "fixed_oracle_comparison_count": 2,
        "production_fixture_record_count": 23,
        "production_evidence_derived_count": 0,
        "production_derived_validated_model_count": 0,
        "two_run_determinism": "passed",
        "next_phase": 11,
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 10 formal evidence-method governance."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase10_evidence_resolution()
    except (Phase10EvidenceResolutionError, EvidenceResolutionError, KeyError) as error:
        print(json.dumps({"phase10_evidence_resolution": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
