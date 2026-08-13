from __future__ import annotations

import copy

import pytest

from traffic_simulation.network.evidence_resolution_v17 import (
    EvidenceResolutionError,
    audit_production_origins,
    canonical_manual_evidence_hash,
    load_evidence_method_registry,
    resolve_evidence_request,
    validate_evidence_method_registry,
    validate_manual_evidence_record,
)


HASH = "a" * 64


def approved_registry() -> dict:
    registry = copy.deepcopy(load_evidence_method_registry())
    registry["approved_method_count"] = 1
    registry["methods"] = [
        {
            "method_id": "TEST_IDENTITY_SINGLE_DONOR_V1",
            "status": "approved",
            "target_attribute": "speed",
            "output_origin": "evidence_derived",
            "eligible_population": {"highway": ["residential"]},
            "required_inputs": ["target_record_id"],
            "donor_eligibility": list(registry["minimum_donor_eligibility"]),
            "estimator_or_model": {"type": "identity_single_donor"},
            "validation_dataset": {"dataset_id": "TEST-DATASET", "sha256": HASH},
            "validation_metrics": {"exact_match_rate": 1.0},
            "acceptance_thresholds": {"minimum_exact_match_rate": 1.0},
            "uncertainty_output": {"type": "none", "value": None},
            "provenance_fields": ["method_id", "donor_record_ids"],
            "approver": "independent_test_authority",
            "approval_date": "2026-08-04",
            "implementation_hash": HASH,
            "fixture_hash": HASH,
            "oracle_hash": HASH,
        }
    ]
    return registry


def eligible_donor() -> dict:
    return {
        "record_id": "donor:1",
        "effective_value": 40,
        "resolution_status": "resolved",
        "value_origin": "source_normalized",
        "eligible_population_match": True,
        "formal_direction_resolved": True,
        "formal_directional_lanes_resolved_when_relevant": True,
        "formal_speed_resolved_when_relevant": True,
        "no_relevant_unsupported_conditional": True,
        "formal_permissions_resolved_when_relevant": True,
        "assumption_ids": [],
        "source_sha256": HASH,
        "configuration_sha256": HASH,
    }


def evidence_request(donor: dict | None = None) -> dict:
    return {
        "method_id": "TEST_IDENTITY_SINGLE_DONOR_V1",
        "target_attribute": "speed",
        "requested_origin": "evidence_derived",
        "eligible_population_match": True,
        "inputs": {"target_record_id": "target:1"},
        "donors": [eligible_donor() if donor is None else donor],
        "production_output_edit": False,
    }


def manual_evidence() -> dict:
    record = {
        "schema_version": 17,
        "evidence_record_id": "MANUAL-EVIDENCE-TEST-001",
        "evidence_version": "1.0.0",
        "source": {
            "description": "independent test evidence",
            "path_or_url": "fixtures/manual-evidence-test.json",
            "sha256": HASH,
        },
        "reviewer": "independent_test_reviewer",
        "decision": {"speed_kmh": 40},
        "reason": "exercise the separate evidence artifact contract",
        "affected_record_ids": ["target:1"],
        "review_date": "2026-08-04",
        "evidence_sha256": "0" * 64,
        "production_output_edit": False,
        "requires_regeneration": True,
    }
    record["evidence_sha256"] = canonical_manual_evidence_hash(record)
    return record


def test_production_registry_has_no_approved_method_and_disables_fallback() -> None:
    registry = load_evidence_method_registry()
    validate_evidence_method_registry(registry)
    assert registry["approved_method_count"] == 0
    assert registry["methods"] == []
    assert set(registry["output_policy"].values()) == {False}


def test_fixed_unapproved_method_oracle_stops() -> None:
    with pytest.raises(EvidenceResolutionError) as caught:
        resolve_evidence_request(
            {"requested_origin": "evidence_derived", "method_id": "UNAPPROVED"}
        )
    assert caught.value.stop_code == "EVIDENCE_METHOD_NOT_APPROVED"
    assert caught.value.status == "unresolved"


def test_complete_approved_method_contract_can_resolve() -> None:
    result = resolve_evidence_request(evidence_request(), registry=approved_registry())
    assert result["effective_value"] == 40
    assert result["value_origin"] == "evidence_derived"
    assert result["assumption_ids"] == []
    assert result["provenance"]["method_id"] == "TEST_IDENTITY_SINGLE_DONOR_V1"
    assert result["provenance"]["regenerated_complete_artifact_required"] is True


def test_approved_method_cannot_omit_mandatory_donor_check() -> None:
    registry = approved_registry()
    registry["methods"][0]["donor_eligibility"].pop()
    with pytest.raises(EvidenceResolutionError) as caught:
        validate_evidence_method_registry(registry)
    assert caught.value.stop_code == "EVIDENCE_METHOD_NOT_APPROVED"


def test_fixed_model_assumed_donor_oracle_stops() -> None:
    donor = eligible_donor()
    donor["value_origin"] = "model_assumed"
    donor["assumption_ids"] = ["BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"]
    with pytest.raises(EvidenceResolutionError) as caught:
        resolve_evidence_request(evidence_request(donor), registry=approved_registry())
    assert caught.value.stop_code == "EVIDENCE_DONOR_INELIGIBLE"
    assert caught.value.status == "invalid"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda donor: donor.update(assumption_ids=["STRUCTURAL_ASSUMPTION"]),
        lambda donor: donor.update(source_sha256="missing"),
        lambda donor: donor.update(configuration_sha256="missing"),
        lambda donor: donor.update(formal_speed_resolved_when_relevant=False),
        lambda donor: donor.update(resolution_status="unresolved"),
    ],
)
def test_ineligible_donor_conditions_stop(mutation) -> None:
    donor = eligible_donor()
    mutation(donor)
    with pytest.raises(EvidenceResolutionError) as caught:
        resolve_evidence_request(evidence_request(donor), registry=approved_registry())
    assert caught.value.stop_code == "EVIDENCE_DONOR_INELIGIBLE"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_attribute", "lanes"),
        ("requested_origin", "derived_validated_model"),
        ("inputs", {}),
        ("production_output_edit", True),
    ],
)
def test_method_boundary_mismatch_stops(field: str, value) -> None:
    request = evidence_request()
    request[field] = value
    with pytest.raises(EvidenceResolutionError) as caught:
        resolve_evidence_request(request, registry=approved_registry())
    assert caught.value.stop_code == "EVIDENCE_METHOD_NOT_APPROVED"


def test_manual_evidence_is_hash_bound_and_consumed_as_separate_artifact() -> None:
    manual = manual_evidence()
    validate_manual_evidence_record(manual)
    request = evidence_request()
    request["manual_evidence"] = manual
    result = resolve_evidence_request(request, registry=approved_registry())
    assert result["provenance"]["manual_evidence_record_id"] == manual["evidence_record_id"]


def test_manual_evidence_hash_tampering_stops() -> None:
    manual = manual_evidence()
    manual["reason"] = "tampered after hashing"
    with pytest.raises(EvidenceResolutionError) as caught:
        validate_manual_evidence_record(manual)
    assert caught.value.stop_code == "EVIDENCE_METHOD_NOT_APPROVED"


def test_production_origin_audit_is_deterministic_and_clean() -> None:
    collections = {
        "permissions": [
            {"record_id": "p:1", "value_origin": "source_explicit"},
            {"record_id": "p:2", "value_origin": "rule_derived"},
        ],
        "speed": [{"record_id": "s:1", "value_origin": "source_normalized"}],
    }
    first = audit_production_origins(collections)
    second = audit_production_origins(collections)
    assert first == second
    assert first["evidence_derived_count"] == 0
    assert first["derived_validated_model_count"] == 0
    assert first["unapproved_evidence_emission_count"] == 0


@pytest.mark.parametrize("origin", ["evidence_derived", "derived_validated_model"])
def test_production_origin_audit_rejects_unapproved_emission(origin: str) -> None:
    records = {"speed": [{"record_id": "s:1", "value_origin": origin, "provenance": {}}]}
    with pytest.raises(EvidenceResolutionError) as caught:
        audit_production_origins(records)
    assert caught.value.stop_code == "EVIDENCE_METHOD_NOT_APPROVED"
