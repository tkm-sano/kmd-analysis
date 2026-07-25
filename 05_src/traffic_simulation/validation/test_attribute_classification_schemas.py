from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "reproducibility/config/traffic_simulation/schemas"
CONFIG_PATH = REPO_ROOT / "reproducibility/config/traffic_simulation/sumo_network.yml"
SHA256 = "a" * 64


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def schema_registry() -> Registry:
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(
        load_schema(name),
        registry=schema_registry(),
        format_checker=FormatChecker(),
    )


def assert_valid(name: str, instance: dict[str, Any]) -> None:
    errors = sorted(validator(name).iter_errors(instance), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def assert_invalid(name: str, instance: dict[str, Any]) -> None:
    assert list(validator(name).iter_errors(instance))


def file_ref(path: str) -> dict[str, str]:
    return {"path": path, "sha256": SHA256}


def predicate_evidence(value: bool = False) -> dict[str, Any]:
    return {
        "value": value,
        "source_artifact_type": "relation_closed_osm_audit",
        "source_artifact_sha256": SHA256,
        "source_record_locator": "ways/123",
        "derivation_rule_id": "PRED-OSM-TAG-001",
    }


def subgraph_role_evidence(role: str = "final") -> dict[str, Any]:
    evidence = predicate_evidence()
    evidence["asserted_role"] = role
    del evidence["value"]
    return evidence


def predicate_artifact() -> dict[str, Any]:
    schema = load_schema("classification_predicates.schema.json")
    predicate_names = schema["$defs"]["predicate_set"]["required"]
    return {
        "artifact_type": "attribute_classification_predicates",
        "schema_version": 1,
        "config_id": "ota_ward_sumo_network_v15",
        "config_version": 15,
        "run_id": "fixture-run-001",
        "complete": True,
        "relation_closed_osm": file_ref("artifacts/relation-closed.osm.xml"),
        "source_registry": file_ref("artifacts/predicate-source-registry.json"),
        "predicate_policy": file_ref("reproducibility/predicate-policy.yml"),
        "population_way_count": 1,
        "records": [
            {
                "osm_way_id": "123",
                "subgraph_role": "final",
                "subgraph_role_evidence": subgraph_role_evidence(),
                "topology_support_reason": None,
                "predicates": {
                    name: predicate_evidence(name == "is_accepted_delivery_route")
                    for name in predicate_names
                },
            }
        ],
    }


def resolution(
    *,
    action: str = "adopt_explicit",
    value_state: str = "explicit_osm",
    resolved_value: int | str | None = 2,
    review_status: str = "machine_classified",
) -> dict[str, Any]:
    reviewed = review_status == "reviewed"
    stopped = action in {"require_human_review", "stop_unresolved"}
    return {
        "resolution_action": action,
        "resolution_rule_id": "LANE-RES-001",
        "value_state": value_state,
        "resolved_value": resolved_value,
        "unit": "lanes" if resolved_value is not None else None,
        "evidence_requirement": {
            "required": False,
            "requirement_rule_id": None,
            "minimum_authority": None,
            "description": None,
        },
        "evidence_candidates": [],
        "selected_evidence_id": None,
        "rejected_evidence_ids": [],
        "conflict_resolution_rule_id": None,
        "review_status": review_status,
        "reviewer": "reviewer-1" if reviewed else None,
        "reviewed_at": "2026-07-24T09:00:00+09:00" if reviewed else None,
        "stop_failure_codes": ["AC001"] if stopped else [],
    }


def classification_artifact() -> dict[str, Any]:
    return {
        "artifact_type": "attribute_classification",
        "schema_version": 1,
        "config_id": "ota_ward_sumo_network_v15",
        "config_version": 15,
        "run_id": "fixture-run-001",
        "profile": "structural",
        "complete": True,
        "relation_closed_osm": file_ref("artifacts/relation-closed.osm.xml"),
        "predicate_artifact": file_ref("artifacts/attribute-classification-predicates.json"),
        "classification_policy": file_ref("reproducibility/classification-policy.yml"),
        "population_way_count": 1,
        "records": [
            {
                "classification_record_id": "acr:123:lanes:structural",
                "osm_way_id": "123",
                "attribute": "lanes",
                "profile": "structural",
                "subgraph_role": "final",
                "record_revision": 1,
                "record_sha256": SHA256,
                "supersedes_record_sha256": None,
                "revision_reason_code": "ACR-INITIAL",
                "source_artifact_sha256": SHA256,
                "classification_config_sha256": SHA256,
                "classification": {
                    "criticality_level": "L1",
                    "selected_rule_id": "LANE-CRIT-001",
                    "matched_rule_ids": ["LANE-CRIT-001"],
                },
                "resolution": resolution(),
            }
        ],
        "blockers": [],
    }


def fixture_artifact() -> dict[str, Any]:
    return {
        "artifact_type": "attribute_classification_fixture",
        "schema_version": 2,
        "fixture_id": "AC-POS-001",
        "case_type": "positive",
        "requirement_ids": ["AC-REQ-001"],
        "description": "An explicit lanes value is adopted.",
        "input_artifacts": [
            {
                "role": "classification_input",
                "path": "fixtures/AC-POS-001/input.json",
                "sha256": SHA256,
            }
        ],
        "expected": {
            "outcome": "success",
            "records": [
                {
                    "classification_record_id": "acr:123:lanes:structural",
                    "classification": {
                        "criticality_level": "L1",
                        "selected_rule_id": "LANE-CRIT-001",
                        "matched_rule_ids": ["LANE-CRIT-001"],
                    },
                    "resolution": {
                        **resolution(),
                    },
                }
            ],
            "failure_codes": [],
            "assertions": [
                {
                    "assertion_id": "ASSERT-AC-POS-001-001",
                    "type": "classification",
                    "subject_pointer": "/expected/records/0",
                    "expected": {"criticality_level": "L1"},
                }
            ],
            "record_emission_policy": {
                "failure_stage": "none",
                "records_emitted": True,
                "partial_records_allowed": False,
                "resolution_emitted": True,
                "artifact_publication_allowed": True,
            },
        },
        "repeat_assertion": None,
        "oracle": {
            "path": "fixtures/AC-POS-001/oracle.json",
            "sha256": SHA256,
            "source_specification_sha256": SHA256,
            "independently_authored": True,
        },
    }


@pytest.mark.parametrize(
    "schema_name",
    [
        "classification_predicates.schema.json",
        "attribute_classification.schema.json",
        "attribute_classification_fixture.schema.json",
    ],
)
def test_schema_is_valid_draft_2020_12(schema_name: str) -> None:
    Draft202012Validator.check_schema(load_schema(schema_name))


def test_predicate_artifact_accepts_complete_evidence() -> None:
    assert_valid("classification_predicates.schema.json", predicate_artifact())


def test_predicate_artifact_requires_evidence_for_false_predicate() -> None:
    artifact = predicate_artifact()
    del artifact["records"][0]["predicates"]["is_bridge"]["source_artifact_sha256"]
    assert_invalid("classification_predicates.schema.json", artifact)


def test_topology_support_requires_a_reason() -> None:
    artifact = predicate_artifact()
    artifact["records"][0]["subgraph_role"] = "topology_support"
    assert_invalid("classification_predicates.schema.json", artifact)


def test_final_role_requires_null_topology_support_reason() -> None:
    artifact = predicate_artifact()
    artifact["records"][0]["topology_support_reason"] = "Not topology support."
    assert_invalid("classification_predicates.schema.json", artifact)


def test_excluded_role_rejects_accepted_delivery_route() -> None:
    artifact = predicate_artifact()
    artifact["records"][0]["subgraph_role"] = "excluded"
    artifact["records"][0]["subgraph_role_evidence"]["asserted_role"] = "excluded"
    assert_invalid("classification_predicates.schema.json", artifact)


def test_calibration_and_validation_predicates_are_exclusive() -> None:
    artifact = predicate_artifact()
    predicates = artifact["records"][0]["predicates"]
    predicates["is_calibration_segment"]["value"] = True
    predicates["is_validation_segment"]["value"] = True
    assert_invalid("classification_predicates.schema.json", artifact)


def test_attribute_classification_accepts_explicit_lane_value() -> None:
    assert_valid("attribute_classification.schema.json", classification_artifact())


def test_incomplete_artifact_may_stop_before_records_are_generated() -> None:
    artifact = classification_artifact()
    artifact["complete"] = False
    artifact["records"] = []
    artifact["blockers"] = [
        {
            "code": "AC001",
            "message": "Population input was unavailable.",
            "component": "attribute_criticality",
            "formal_blocker": True,
        }
    ]
    assert_valid("attribute_classification.schema.json", artifact)


def test_complete_artifact_requires_at_least_one_record() -> None:
    artifact = classification_artifact()
    artifact["records"] = []
    assert_invalid("attribute_classification.schema.json", artifact)


def test_complete_artifact_rejects_unresolved_record() -> None:
    artifact = classification_artifact()
    artifact["records"][0]["resolution"] = resolution(
        action="stop_unresolved",
        value_state="missing",
        resolved_value=None,
        review_status="stopped",
    )
    assert_invalid("attribute_classification.schema.json", artifact)


def test_l2_rejects_structural_placeholder() -> None:
    artifact = classification_artifact()
    record = artifact["records"][0]
    record["classification"]["criticality_level"] = "L2"
    record["classification"]["selected_rule_id"] = "LANE-CRIT-002"
    record["classification"]["matched_rule_ids"] = ["LANE-CRIT-002"]
    record["resolution"] = resolution(
        action="apply_structural_placeholder",
        value_state="structural_placeholder",
    )
    assert_invalid("attribute_classification.schema.json", artifact)


def test_formal_record_rejects_structural_placeholder() -> None:
    artifact = classification_artifact()
    artifact["profile"] = "formal"
    record = artifact["records"][0]
    record["profile"] = "formal"
    record["classification"]["criticality_level"] = "L1"
    record["resolution"] = resolution(
        action="apply_structural_placeholder",
        value_state="structural_placeholder",
    )
    assert_invalid("attribute_classification.schema.json", artifact)


def test_external_evidence_requires_candidate_and_selection() -> None:
    artifact = classification_artifact()
    artifact["records"][0]["resolution"] = resolution(
        action="adopt_external_evidence",
        value_state="authoritative_external",
        review_status="reviewed",
    )
    assert_invalid("attribute_classification.schema.json", artifact)


def test_inapplicable_evidence_requires_rejection_reason() -> None:
    artifact = classification_artifact()
    candidate = {
        "evidence_id": "candidate-1",
        "source": "public ledger",
        "value": 2,
        "unit": "lanes",
        "direction": "both",
        "segment": "way-123",
        "vehicle_scope": ["delivery"],
        "reference_period": "2026-07",
        "license": "public",
        "source_sha256": SHA256,
        "matching_confidence": 0.5,
        "applicable": False,
        "rejection_reason_code": None,
    }
    artifact["records"][0]["resolution"]["evidence_candidates"] = [candidate]
    assert_invalid("attribute_classification.schema.json", artifact)


def test_l3_adopted_value_requires_completed_review() -> None:
    artifact = classification_artifact()
    artifact["records"][0]["classification"]["criticality_level"] = "L3"
    assert_invalid("attribute_classification.schema.json", artifact)


def test_excluded_record_cannot_contain_a_resolved_value() -> None:
    artifact = classification_artifact()
    record = artifact["records"][0]
    record["subgraph_role"] = "excluded"
    record["classification"]["criticality_level"] = "L0"
    record["classification"]["selected_rule_id"] = "LANE-CRIT-000"
    record["classification"]["matched_rule_ids"] = ["LANE-CRIT-000"]
    record["resolution"]["resolution_action"] = "exclude"
    record["resolution"]["value_state"] = "excluded"
    assert_invalid("attribute_classification.schema.json", artifact)


def test_fixture_accepts_positive_oracle() -> None:
    assert_valid("attribute_classification_fixture.schema.json", fixture_artifact())


def test_fixture_keeps_classification_and_resolution_objects_separate() -> None:
    artifact = fixture_artifact()
    record = artifact["expected"]["records"][0]
    record["criticality_level"] = record.pop("classification")["criticality_level"]
    assert_invalid("attribute_classification_fixture.schema.json", artifact)


def test_fixture_case_type_and_identifier_must_match() -> None:
    artifact = fixture_artifact()
    artifact["case_type"] = "boundary"
    assert_invalid("attribute_classification_fixture.schema.json", artifact)


def test_fixture_governed_stop_requires_failure_code() -> None:
    artifact = fixture_artifact()
    artifact["fixture_id"] = "AC001-NEG-001"
    artifact["case_type"] = "negative"
    artifact["expected"]["outcome"] = "governed_stop"
    assert_invalid("attribute_classification_fixture.schema.json", artifact)


def test_fixture_may_stop_before_expected_records_are_generated() -> None:
    artifact = fixture_artifact()
    artifact["fixture_id"] = "AC001-NEG-001"
    artifact["case_type"] = "negative"
    artifact["expected"] = {
        "outcome": "governed_stop",
        "records": [],
        "failure_codes": ["AC001"],
        "assertions": [
            {
                "assertion_id": "ASSERT-AC001-NEG-001",
                "type": "governed_stop",
                "subject_pointer": "/expected",
                "expected": {"failure_codes": ["AC001"]},
            }
        ],
        "record_emission_policy": {
            "failure_stage": "schema",
            "records_emitted": False,
            "partial_records_allowed": False,
            "resolution_emitted": False,
            "artifact_publication_allowed": False,
        },
    }
    assert_valid("attribute_classification_fixture.schema.json", artifact)


def test_fixture_reuses_production_resolution_state_machine() -> None:
    artifact = fixture_artifact()
    fixture_resolution = artifact["expected"]["records"][0]["resolution"]
    fixture_resolution["value_state"] = "missing"
    fixture_resolution["resolved_value"] = None
    assert_invalid("attribute_classification_fixture.schema.json", artifact)


def test_repeat_fixture_requires_repeat_assertion() -> None:
    artifact = fixture_artifact()
    artifact["fixture_id"] = "AC-REP-001"
    artifact["case_type"] = "repeat"
    assert_invalid("attribute_classification_fixture.schema.json", artifact)


def test_three_schemas_are_registered_in_network_config() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    registry = config["artifact_schema_registry"]
    assert {
        registry["classification_predicates"],
        registry["attribute_classification"],
        registry["attribute_classification_fixture"],
    } == {
        "reproducibility/config/traffic_simulation/schemas/classification_predicates.schema.json",
        "reproducibility/config/traffic_simulation/schemas/attribute_classification.schema.json",
        "reproducibility/config/traffic_simulation/schemas/attribute_classification_fixture.schema.json",
    }
