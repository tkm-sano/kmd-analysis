from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.validate_attribute_classification import (
    calculate_record_sha256,
    file_sha256,
    validate_classification_artifact,
    validate_fixture_artifact,
    validate_predicate_artifact,
)


SHA256 = "a" * 64


def write_file(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def file_ref(root: Path, relative_path: str) -> dict[str, str]:
    return {"path": relative_path, "sha256": file_sha256(root / relative_path)}


def prepare_sources(root: Path) -> dict[str, Path]:
    paths = {
        "relation": write_file(root, "inputs/relation-closed.osm.xml", "<osm/>"),
        "predicates": write_file(root, "inputs/predicates.json", "{}\n"),
        "external": write_file(root, "inputs/external-evidence.json", "{}\n"),
        "specification": write_file(root, "specification.md", "# Specification\n"),
        "oracle": write_file(root, "fixtures/oracle.json", '{"expected":true}\n'),
    }
    policy = {
        "road_criticality": {
            "classification_rule_priority": {
                "lanes": [
                    "LANE-CRIT-001",
                    "LANE-CRIT-002",
                    "LANE-CRIT-003",
                    "LANE-CRIT-004",
                    "LANE-CRIT-005",
                    "LANE-CRIT-006",
                    "LANE-CRIT-007",
                ],
                "maxspeed": [
                    "SPEED-CRIT-001",
                    "SPEED-CRIT-002",
                    "SPEED-CRIT-003",
                    "SPEED-CRIT-004",
                    "SPEED-CRIT-005",
                    "SPEED-CRIT-006",
                ],
            }
        }
    }
    paths["policy"] = write_file(
        root, "policy.yml", yaml.safe_dump(policy, sort_keys=False)
    )
    return paths


def predicate_evidence(source_hash: str, value: bool = False) -> dict[str, Any]:
    return {
        "value": value,
        "source_artifact_type": "relation_closed_osm",
        "source_artifact_sha256": source_hash,
        "source_record_locator": "ways/123",
        "derivation_rule_id": "PRED-OSM-TAG-001",
    }


def predicate_artifact(root: Path, *, role: str = "final") -> dict[str, Any]:
    relation_ref = file_ref(root, "inputs/relation-closed.osm.xml")
    policy_ref = file_ref(root, "policy.yml")
    schema = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "reproducibility/config/traffic_simulation/schemas/"
            "classification_predicates.schema.json"
        ).read_text(encoding="utf-8")
    )
    predicate_names = schema["$defs"]["predicate_set"]["required"]
    role_evidence = predicate_evidence(relation_ref["sha256"])
    del role_evidence["value"]
    role_evidence["asserted_role"] = role
    return {
        "artifact_type": "attribute_classification_predicates",
        "schema_version": 1,
        "config_id": "ota_ward_sumo_network_v15",
        "config_version": 15,
        "run_id": "semantic-test",
        "complete": True,
        "relation_closed_osm": relation_ref,
        "predicate_policy": policy_ref,
        "population_way_count": 1,
        "records": [
            {
                "osm_way_id": "123",
                "subgraph_role": role,
                "subgraph_role_evidence": role_evidence,
                "topology_support_reason": (
                    "Retained to preserve relation topology."
                    if role == "topology_support"
                    else None
                ),
                "predicates": {
                    name: predicate_evidence(relation_ref["sha256"])
                    for name in predicate_names
                },
            }
        ],
    }


def evidence_candidate(source_hash: str, *, applicable: bool = True) -> dict[str, Any]:
    return {
        "evidence_id": "external-lanes-001",
        "source": "public-road-ledger",
        "value": 2,
        "unit": "lanes",
        "direction": "both",
        "segment": "osm-way-123",
        "vehicle_scope": ["delivery"],
        "reference_period": "2026-07",
        "license": "public-data-license",
        "source_sha256": source_hash,
        "matching_confidence": 1.0,
        "applicable": applicable,
        "rejection_reason_code": None if applicable else "DIRECTION_MISMATCH",
    }


def resolution(
    *,
    action: str,
    state: str,
    value: int | str | None,
    unit: str | None,
    review_status: str,
    rule_id: str | None = None,
    candidates: list[dict[str, Any]] | None = None,
    selected: str | None = None,
    rejected: list[str] | None = None,
) -> dict[str, Any]:
    reviewed = review_status == "reviewed"
    stopped = action in {"require_human_review", "stop_unresolved"}
    return {
        "resolution_action": action,
        "resolution_rule_id": rule_id,
        "value_state": state,
        "resolved_value": value,
        "unit": unit,
        "evidence_required": "Governed attribute evidence.",
        "evidence_candidates": candidates or [],
        "selected_evidence_id": selected,
        "rejected_evidence_ids": rejected or [],
        "conflict_resolution_rule_id": None,
        "review_status": review_status,
        "reviewer": "reviewer-1" if reviewed else None,
        "reviewed_at": "2026-07-25T09:00:00+09:00" if reviewed else None,
        "stop_failure_codes": ["AC006"] if stopped else [],
    }


def make_record(
    *,
    way_id: str,
    attribute: str,
    profile: str,
    criticality: str,
    rule_id: str,
    role: str,
    resolution_value: dict[str, Any],
    source_hash: str,
    config_hash: str,
    revision: int = 1,
    supersedes: str | None = None,
) -> dict[str, Any]:
    record = {
        "classification_record_id": f"acr:{way_id}:{attribute}:{profile}",
        "osm_way_id": way_id,
        "attribute": attribute,
        "profile": profile,
        "subgraph_role": role,
        "record_revision": revision,
        "record_sha256": SHA256,
        "supersedes_record_sha256": supersedes,
        "revision_reason_code": "ACR-INITIAL" if revision == 1 else "ACR-EVIDENCE-UPDATE",
        "source_artifact_sha256": source_hash,
        "classification_config_sha256": config_hash,
        "classification": {
            "criticality_level": criticality,
            "selected_rule_id": rule_id,
            "matched_rule_ids": [rule_id],
        },
        "resolution": resolution_value,
    }
    record["record_sha256"] = calculate_record_sha256(record)
    return record


def classification_artifact(
    root: Path,
    *,
    profile: str = "structural",
    external: bool = False,
    excluded: bool = False,
) -> tuple[dict[str, Any], dict[str, Path]]:
    paths = prepare_sources(root)
    predicate_hash = file_sha256(paths["predicates"])
    policy_hash = file_sha256(paths["policy"])
    external_hash = file_sha256(paths["external"])
    if excluded:
        role = "excluded"
        lane_level, lane_rule = "L0", "LANE-CRIT-001"
        speed_level, speed_rule = "S0", "SPEED-CRIT-001"
        lane_resolution = resolution(
            action="exclude",
            state="excluded",
            value=None,
            unit=None,
            review_status="machine_classified",
        )
        speed_resolution = copy.deepcopy(lane_resolution)
    elif profile == "formal":
        role = "final"
        lane_level, lane_rule = "L2", "LANE-CRIT-006"
        speed_level, speed_rule = "S2", "SPEED-CRIT-005"
        lane_resolution = resolution(
            action="adopt_explicit",
            state="explicit_osm",
            value=2,
            unit="lanes",
            review_status="machine_classified",
        )
        speed_resolution = resolution(
            action="adopt_explicit",
            state="explicit_osm",
            value="40",
            unit="km/h",
            review_status="machine_classified",
        )
    else:
        role = "final"
        lane_level, lane_rule = "L1", "LANE-CRIT-007"
        speed_level, speed_rule = "S1", "SPEED-CRIT-006"
        lane_resolution = resolution(
            action="apply_structural_placeholder",
            state="structural_placeholder",
            value=2,
            unit="lanes",
            review_status="machine_classified",
            rule_id="LANE-PLACEHOLDER-001",
        )
        speed_resolution = resolution(
            action="adopt_explicit",
            state="explicit_osm",
            value="40",
            unit="km/h",
            review_status="machine_classified",
        )
    if external:
        candidate = evidence_candidate(external_hash)
        lane_resolution = resolution(
            action="adopt_external_evidence",
            state="authoritative_external",
            value=2,
            unit="lanes",
            review_status="reviewed",
            candidates=[candidate],
            selected=candidate["evidence_id"],
        )
    records = [
        make_record(
            way_id="123",
            attribute="lanes",
            profile=profile,
            criticality=lane_level,
            rule_id=lane_rule,
            role=role,
            resolution_value=lane_resolution,
            source_hash=predicate_hash,
            config_hash=policy_hash,
        ),
        make_record(
            way_id="123",
            attribute="maxspeed",
            profile=profile,
            criticality=speed_level,
            rule_id=speed_rule,
            role=role,
            resolution_value=speed_resolution,
            source_hash=predicate_hash,
            config_hash=policy_hash,
        ),
    ]
    return (
        {
            "artifact_type": "attribute_classification",
            "schema_version": 1,
            "config_id": "ota_ward_sumo_network_v15",
            "config_version": 15,
            "run_id": "semantic-test",
            "profile": profile,
            "complete": True,
            "relation_closed_osm": file_ref(root, "inputs/relation-closed.osm.xml"),
            "predicate_artifact": file_ref(root, "inputs/predicates.json"),
            "classification_policy": file_ref(root, "policy.yml"),
            "population_way_count": 1,
            "records": records,
            "blockers": [],
        },
        paths,
    )


def source_index(paths: dict[str, Path]) -> dict[str, Path]:
    return {file_sha256(path): path for path in paths.values()}


def rehash(artifact: dict[str, Any]) -> None:
    for record in artifact["records"]:
        record["record_sha256"] = calculate_record_sha256(record)


def error_codes(result: Any) -> set[str]:
    return {error.code for error in result.errors}


def fixture_artifact(root: Path, resolution_value: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "attribute_classification_fixture",
        "schema_version": 1,
        "fixture_id": "AC-POS-001",
        "case_type": "positive",
        "requirement_ids": ["AC-REQ-001"],
        "description": "Valid classification fixture.",
        "input_artifacts": [
            {
                "role": "classification_input",
                **file_ref(root, "inputs/predicates.json"),
            }
        ],
        "expected": {
            "outcome": "success",
            "records": [
                {
                    "classification_record_id": "acr:123:lanes:structural",
                    "classification": {
                        "criticality_level": "L1",
                        "selected_rule_id": "LANE-CRIT-007",
                        "matched_rule_ids": ["LANE-CRIT-007"],
                    },
                    "resolution": resolution_value,
                }
            ],
            "failure_codes": [],
        },
        "repeat_assertion": None,
        "oracle": {
            **file_ref(root, "fixtures/oracle.json"),
            "source_specification_sha256": file_sha256(root / "specification.md"),
            "independently_authored": True,
        },
    }


def test_predicate_artifact_accepts_topology_support_with_reason(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    artifact = predicate_artifact(tmp_path, role="topology_support")
    result = validate_predicate_artifact(artifact, artifact_root=tmp_path)
    assert result.valid, result.to_dict()


def test_predicate_role_evidence_must_assert_the_record_role(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    artifact = predicate_artifact(tmp_path)
    artifact["records"][0]["subgraph_role_evidence"][
        "asserted_role"
    ] = "topology_support"
    result = validate_predicate_artifact(artifact, artifact_root=tmp_path)
    assert "ACV015" in error_codes(result)


def test_structural_l1_placeholder_artifact_is_valid(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert result.valid, result.to_dict()


def test_formal_explicit_osm_artifact_is_valid(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, profile="formal")
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert result.valid, result.to_dict()


def test_reviewed_external_evidence_artifact_is_valid(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, external=True)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert result.valid, result.to_dict()


def test_excluded_way_has_lane_and_speed_records(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, excluded=True)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert result.valid, result.to_dict()


def test_incomplete_artifact_may_stop_before_record_generation(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
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
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert result.valid, result.to_dict()


def test_classification_record_id_is_derived_from_fields(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["classification_record_id"] = "acr:999:lanes:structural"
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV001" in error_codes(result)
    payload = result.to_dict()
    id_error = next(error for error in payload["errors"] if error["code"] == "ACV001")
    assert payload["valid"] is False
    assert id_error == {
        "code": "ACV001",
        "json_pointer": "/records/0/classification_record_id",
        "message": (
            "classification_record_id does not match osm_way_id, attribute, and profile"
        ),
        "expected": "acr:123:lanes:structural",
        "actual": "acr:999:lanes:structural",
    }


def test_record_attribute_and_profile_must_match_id_and_artifact(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["attribute"] = "maxspeed"
    artifact["records"][1]["profile"] = "formal"
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert {"ACV001", "ACV002"} <= error_codes(result)


def test_selected_rule_must_be_matched_and_highest_priority(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    classification = artifact["records"][0]["classification"]
    classification["selected_rule_id"] = "LANE-CRIT-007"
    classification["matched_rule_ids"] = ["LANE-CRIT-006"]
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert {"ACV005", "ACV006"} <= error_codes(result)


def test_formal_profile_rejects_structural_placeholder(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, profile="formal")
    artifact["records"][0]["resolution"] = resolution(
        action="apply_structural_placeholder",
        state="structural_placeholder",
        value=2,
        unit="lanes",
        review_status="machine_classified",
        rule_id="LANE-PLACEHOLDER-001",
    )
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV000" in error_codes(result)


def test_external_evidence_requires_existing_selected_candidate(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, external=True)
    resolution_value = artifact["records"][0]["resolution"]
    resolution_value["selected_evidence_id"] = "missing-candidate"
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert {"ACV007", "ACV008"} <= error_codes(result)


def test_selected_evidence_cannot_also_be_rejected(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, external=True)
    resolution_value = artifact["records"][0]["resolution"]
    resolution_value["rejected_evidence_ids"] = [
        resolution_value["selected_evidence_id"]
    ]
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV007" in error_codes(result)


def test_inapplicable_candidate_requires_rejection_reason(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path, external=True)
    candidate = artifact["records"][0]["resolution"]["evidence_candidates"][0]
    candidate["applicable"] = False
    candidate["rejection_reason_code"] = None
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV000" in error_codes(result)


def test_complete_artifact_rejects_stopped_record(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["resolution"] = resolution(
        action="stop_unresolved",
        state="missing",
        value=None,
        unit=None,
        review_status="stopped",
    )
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV009" in error_codes(result)


def test_complete_artifact_rejects_review_required_record(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["resolution"] = resolution(
        action="require_human_review",
        state="missing",
        value=None,
        unit=None,
        review_status="review_required",
    )
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV009" in error_codes(result)


def test_predicate_way_ids_are_unique(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    artifact = predicate_artifact(tmp_path)
    artifact["records"].append(copy.deepcopy(artifact["records"][0]))
    artifact["population_way_count"] = 2
    result = validate_predicate_artifact(artifact, artifact_root=tmp_path)
    assert "ACV016" in error_codes(result)


def test_classification_ids_and_tuples_are_unique(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"].append(copy.deepcopy(artifact["records"][0]))
    artifact["population_way_count"] = 2
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert {"ACV003", "ACV004", "ACV010"} <= error_codes(result)


def test_each_way_requires_lane_and_maxspeed_records(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"].pop(0)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV010" in error_codes(result)


def test_predicate_forbidden_combinations_are_collected(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    artifact = predicate_artifact(tmp_path, role="excluded")
    predicates = artifact["records"][0]["predicates"]
    predicates["is_accepted_delivery_route"]["value"] = True
    predicates["is_calibration_segment"]["value"] = True
    predicates["is_validation_segment"]["value"] = True
    result = validate_predicate_artifact(artifact, artifact_root=tmp_path)
    assert "ACV016" in error_codes(result)
    assert len([error for error in result.errors if error.code == "ACV016"]) >= 3


def test_revision_two_requires_supplied_revision_one(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    base = copy.deepcopy(artifact)
    lane = artifact["records"][0]
    lane["record_revision"] = 2
    lane["supersedes_record_sha256"] = base["records"][0]["record_sha256"]
    lane["revision_reason_code"] = "ACR-EVIDENCE-UPDATE"
    rehash(artifact)
    missing = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV011" in error_codes(missing)
    supplied = validate_classification_artifact(
        artifact,
        artifact_root=tmp_path,
        source_index=source_index(paths),
        history_artifacts=[base],
    )
    assert "ACV011" not in error_codes(supplied)


def test_record_sha256_is_recomputed_from_rfc8785_content(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["record_sha256"] = SHA256
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV012" in error_codes(result)


def test_record_source_and_config_hashes_bind_to_top_level_refs(
    tmp_path: Path,
) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"][0]["source_artifact_sha256"] = file_sha256(paths["relation"])
    artifact["records"][0]["classification_config_sha256"] = file_sha256(
        paths["external"]
    )
    rehash(artifact)
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV014" in error_codes(result)


def test_records_must_follow_canonical_order(tmp_path: Path) -> None:
    artifact, paths = classification_artifact(tmp_path)
    artifact["records"].reverse()
    result = validate_classification_artifact(
        artifact, artifact_root=tmp_path, source_index=source_index(paths)
    )
    assert "ACV013" in error_codes(result)


def test_fixture_uses_production_resolution_state_machine(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    invalid = resolution(
        action="adopt_explicit",
        state="missing",
        value=None,
        unit=None,
        review_status="machine_classified",
    )
    artifact = fixture_artifact(tmp_path, invalid)
    result = validate_fixture_artifact(
        artifact,
        artifact_root=tmp_path,
        specification_path=tmp_path / "specification.md",
    )
    assert {"ACV000", "ACV018"} <= error_codes(result)


def test_lane_fixture_rejects_speed_criticality_family(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    valid_resolution = resolution(
        action="adopt_explicit",
        state="explicit_osm",
        value=2,
        unit="lanes",
        review_status="machine_classified",
    )
    artifact = fixture_artifact(tmp_path, valid_resolution)
    artifact["expected"]["records"][0]["classification"] = {
        "criticality_level": "S1",
        "selected_rule_id": "SPEED-CRIT-006",
        "matched_rule_ids": ["SPEED-CRIT-006"],
    }
    result = validate_fixture_artifact(
        artifact,
        artifact_root=tmp_path,
        specification_path=tmp_path / "specification.md",
    )
    assert "ACV017" in error_codes(result)


def test_repeat_fixture_accepts_equal_canonical_content(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    baseline = write_file(tmp_path, "outputs/baseline.json", '{"a":1,"time":"one"}\n')
    repeated = write_file(
        tmp_path, "outputs/repeated.json", '{\n  "time": "two",\n  "a": 1\n}\n'
    )
    valid_resolution = resolution(
        action="adopt_explicit",
        state="explicit_osm",
        value=2,
        unit="lanes",
        review_status="machine_classified",
    )
    artifact = fixture_artifact(tmp_path, valid_resolution)
    artifact["fixture_id"] = "AC-REP-001"
    artifact["case_type"] = "repeat"
    artifact["repeat_assertion"] = {
        "baseline_output_sha256": file_sha256(baseline),
        "repeated_output_sha256": file_sha256(repeated),
        "comparison_mode": "canonical_content_equal",
        "excluded_json_pointers": ["/time"],
    }
    result = validate_fixture_artifact(
        artifact,
        artifact_root=tmp_path,
        specification_path=tmp_path / "specification.md",
        baseline_output=baseline,
        repeated_output=repeated,
    )
    assert result.valid, result.to_dict()


def test_repeat_fixture_detects_different_output(tmp_path: Path) -> None:
    prepare_sources(tmp_path)
    baseline = write_file(tmp_path, "outputs/baseline.json", '{"a":1}\n')
    repeated = write_file(tmp_path, "outputs/repeated.json", '{"a":2}\n')
    valid_resolution = resolution(
        action="adopt_explicit",
        state="explicit_osm",
        value=2,
        unit="lanes",
        review_status="machine_classified",
    )
    artifact = fixture_artifact(tmp_path, valid_resolution)
    artifact["fixture_id"] = "AC-REP-001"
    artifact["case_type"] = "repeat"
    artifact["repeat_assertion"] = {
        "baseline_output_sha256": file_sha256(baseline),
        "repeated_output_sha256": file_sha256(repeated),
        "comparison_mode": "canonical_content_equal",
        "excluded_json_pointers": [],
    }
    result = validate_fixture_artifact(
        artifact,
        artifact_root=tmp_path,
        specification_path=tmp_path / "specification.md",
        baseline_output=baseline,
        repeated_output=repeated,
    )
    assert "ACV019" in error_codes(result)
