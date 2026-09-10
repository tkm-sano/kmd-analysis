"""Tests for the Research Portal Registry v1 validator."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from traffic_simulation import validate_research_portal_registry as registry_validator
from traffic_simulation.validate_research_portal_registry import (
    REGISTRY_PATH,
    SCHEMA_PATH,
    _load_schema,
    _load_yaml,
    _schema_errors,
    validate_registry,
)


@pytest.fixture(scope="module")
def registry() -> dict:
    return _load_yaml(REGISTRY_PATH)


@pytest.fixture(scope="module")
def schema() -> dict:
    return _load_schema(SCHEMA_PATH)


def write_registry(tmp_path: Path, registry: dict) -> Path:
    path = tmp_path / "registry.yml"
    path.write_text(
        yaml.safe_dump(registry, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_repository_registry_is_valid_and_reports_governed_gaps() -> None:
    report = validate_registry()

    assert report.valid
    assert report.errors == ()
    assert {key: value for key, value in report.counts.items() if key != "warnings"} == {
        "nodes": 29,
        "relations": 28,
        "evidence": 36,
        "issues": 5,
        "stages": 2,
        "metrics": 3,
        "remaining_unknowns": 17,
        "remaining_conflicts": 4,
    }
    assert report.counts["warnings"] == len(report.warnings)
    assert sum("unresolved known conflict" in warning for warning in report.warnings) == 4
    assert not any("isolated node" in warning for warning in report.warnings)


def test_unknown_review_uses_null_and_reason_not_unknown_string(
    registry: dict, schema: dict
) -> None:
    changed = copy.deepcopy(registry)
    changed["review"]["reviewed_by"] = "unknown"

    errors = _schema_errors(changed, schema)

    assert any("reviewed_by" in error and "should not be valid" in error for error in errors)


def test_duplicate_yaml_mapping_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yml"
    path.write_text("schema_version: 1\nschema_version: 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate YAML mapping key: schema_version"):
        _load_yaml(path)


def test_evidence_support_target_is_limited_to_node_or_relation(
    registry: dict, schema: dict
) -> None:
    changed = copy.deepcopy(registry)
    changed["evidence"][0]["supports"][0]["target_type"] = "variable"

    errors = _schema_errors(changed, schema)

    assert any("target_type" in error for error in errors)


def test_implemented_method_requires_implementation_and_test_evidence(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    classical = next(node for node in changed["nodes"] if node["id"] == "method.classical")
    classical["status"] = "implemented"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert not report.valid
    assert any(
        "implemented method requires implementation and test evidence: method.classical"
        in error
        for error in report.errors
    )


def test_dataset_implemented_does_not_require_implementation_or_test(
    registry: dict,
) -> None:
    open_data = next(node for node in registry["nodes"] if node["id"] == "data.open_data")
    assert open_data["status"] == "implemented"
    assert open_data["readiness"] == "provisional"
    assert validate_registry().valid


def test_blocked_by_must_be_issue_to_blocked_target(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    relation = next(
        relation
        for relation in changed["relations"]
        if relation["id"] == "rel.route_issue_blocks_fulfillment"
    )
    relation["source"] = "model.baseline"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert not report.valid
    assert any("blocked_by source must be issue node" in error for error in report.errors)


def test_compares_with_is_stored_once_and_references_common_instance(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    relation = copy.deepcopy(
        next(
            relation
            for relation in changed["relations"]
            if relation["id"] == "rel.baseline_compares_classical"
        )
    )
    relation["id"] = "rel.classical_compares_baseline_duplicate"
    relation["source"], relation["target"] = relation["target"], relation["source"]
    changed["relations"].append(relation)

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert not report.valid
    assert any("compares_with must be stored once" in error for error in report.errors)


def test_missing_evidence_path_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    changed["evidence"][0]["path"] = "does/not/exist.md"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert not report.valid
    assert any("missing evidence path: ev.research_overview" in error for error in report.errors)


def test_untracked_evidence_is_warning_not_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry_validator, "_is_git_tracked", lambda *_: False)

    report = validate_registry()

    assert report.valid
    assert sum("untracked evidence" in warning for warning in report.warnings) == 36


def test_status_and_readiness_are_independent(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    open_data = next(node for node in changed["nodes"] if node["id"] == "data.open_data")
    open_data["readiness"] = "not_accepted"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert report.valid


def test_current_stage_ref_must_reference_stage(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    changed["current_stage_ref"] = "model.baseline"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("current_stage_ref must reference exactly one stage node" in error for error in report.errors)


def test_evidence_refs_and_supports_are_bidirectional(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    evidence = next(item for item in changed["evidence"] if item["id"] == "ev.data_registry")
    evidence["supports"].remove({"target_type": "node", "target_id": "data.open_data"})

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("node evidence ref is not reciprocated by evidence supports" in error for error in report.errors)


@pytest.mark.parametrize(
    ("collection", "item_id", "field", "missing", "message"),
    [
        ("nodes", "model.road_network", "parent_node_ref", "model.missing", "missing parent node ref"),
        ("views", "view.evidence_gaps", "conflict_refs", ["conflict.missing"], "missing conflict ref"),
        ("groups", "group.baseline", "node_refs", ["model.missing"], "missing node ref"),
    ],
)
def test_missing_cross_references_are_errors(
    tmp_path: Path,
    registry: dict,
    collection: str,
    item_id: str,
    field: str,
    missing: object,
    message: str,
) -> None:
    changed = copy.deepcopy(registry)
    item = next(value for value in changed[collection] if value["id"] == item_id)
    item[field] = missing

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any(message in error for error in report.errors)


def test_missing_relation_and_view_references_are_errors(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    view = next(item for item in changed["views"] if item["id"] == "view.current_stage")
    view["relation_refs"].append("rel.missing")
    changed["default_view_id"] = "view.missing"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert "missing default view: view.missing" in report.errors
    assert any("has missing relation ref: rel.missing" in error for error in report.errors)


def test_path_traversal_is_rejected_by_schema(registry: dict, schema: dict) -> None:
    changed = copy.deepcopy(registry)
    changed["evidence"][0]["path"] = "../outside.md"

    errors = _schema_errors(changed, schema)

    assert errors


def test_symlink_escape_is_rejected(tmp_path: Path, registry: dict) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    (repository / "escape.md").symlink_to(outside)
    changed = copy.deepcopy(registry)
    changed["evidence"][0]["path"] = "escape.md"

    report = validate_registry(
        write_registry(tmp_path, changed), SCHEMA_PATH, repository_root=repository
    )

    assert any("symlink evidence path escapes repository" in error for error in report.errors)


def test_accepted_readiness_requires_acceptance_and_review(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    open_data = next(node for node in changed["nodes"] if node["id"] == "data.open_data")
    open_data["readiness"] = "accepted"

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("accepted node requires acceptance_decision evidence" in error for error in report.errors)
    assert any("accepted node requires a completed review" in error for error in report.errors)


def test_planned_relation_requires_design_intent(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    relation = next(item for item in changed["relations"] if item["id"] == "rel.baseline_to_common_instance")
    relation["evidence_refs"] = ["ev.current_issues"]

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("planned relation requires design_intent evidence" in error for error in report.errors)


def test_dependency_cycle_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    relation = copy.deepcopy(next(item for item in changed["relations"] if item["id"] == "rel.baseline_to_common_instance"))
    relation["id"] = "rel.common_instance_to_baseline_cycle"
    relation["source"], relation["target"] = relation["target"], relation["source"]
    changed["relations"].append(relation)

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("depends_on/blocked_by graph contains a cycle" in error for error in report.errors)


def test_relation_supersedes_cycle_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    first, second = changed["relations"][0], changed["relations"][1]
    first.update({"type": "supersedes", "source": "data.open_data", "target": "model.baseline"})
    second.update({"type": "supersedes", "source": "model.baseline", "target": "data.open_data"})

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("supersedes graph contains a cycle" in error for error in report.errors)


def test_evidence_superseded_cycle_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    changed["evidence"][0]["superseded_by"] = changed["evidence"][1]["id"]
    changed["evidence"][1]["superseded_by"] = changed["evidence"][0]["id"]

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("evidence superseded graph contains a cycle" in error for error in report.errors)


def test_view_coverage_warning(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    node_id = "data.open_data"
    for view in changed["views"]:
        view["node_refs"] = [ref for ref in view["node_refs"] if ref != node_id]
        for rank in view["fixed_ranks"]:
            rank["node_refs"] = [ref for ref in rank["node_refs"] if ref != node_id]
        view["fixed_ranks"] = [rank for rank in view["fixed_ranks"] if rank["node_refs"]]

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert f"node is not included in any view: {node_id}" in report.warnings


def test_aer_modality_is_structurally_guarded(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    qaoa = next(node for node in changed["nodes"] if node["id"] == "method.qaoa_aer")
    qaoa["hardware_execution"] = True
    qaoa["quantum_advantage_claimed"] = True

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("hardware_execution false" in error for error in report.errors)
    assert any("quantum_advantage_claimed false" in error for error in report.errors)


def test_numeric_metric_requires_unit_and_scope(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    metric = next(node for node in changed["nodes"] if node["id"] == "metric.delivery_fulfillment_rate")
    metric["metric_definition"]["unit"] = None
    metric["metric_definition"]["scope"] = None

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("numeric metric requires unit" in error for error in report.errors)
    assert any("numeric metric requires scope" in error for error in report.errors)


def test_problem_scale_value_requires_evidence_and_derivation(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    road = next(node for node in changed["nodes"] if node["id"] == "model.road_network")
    scale = road["problem_scale"][0]
    scale["evidence_ref"] = None
    scale["derivation_method"] = None

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("valued problem scale requires evidence" in error for error in report.errors)
    assert any("valued problem scale requires unit and derivation_method" in error for error in report.errors)


def test_problem_scale_derivation_cycle_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    synthetic = next(node for node in changed["nodes"] if node["id"] == "data.synthetic_delivery_demand")
    first, second = synthetic["problem_scale"]
    first["derived_from_scale_refs"] = [second["id"]]
    second["derived_from_scale_refs"] = [first["id"]]

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("problem scale derivation graph contains a cycle" in error for error in report.errors)


def test_generated_evidence_requires_non_circular_provenance(
    tmp_path: Path, registry: dict
) -> None:
    changed = copy.deepcopy(registry)
    artifact = next(item for item in changed["evidence"] if item["id"] == "ev.baseline_demand_artifact")
    artifact.pop("generated_from_evidence_refs")

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("generated evidence requires provenance refs" in error for error in report.errors)


def test_generated_evidence_provenance_cycle_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    artifact = next(item for item in changed["evidence"] if item["id"] == "ev.baseline_demand_artifact")
    quality = next(item for item in changed["evidence"] if item["id"] == "ev.baseline_demand_quality")
    artifact["generated_from_evidence_refs"] = [quality["id"]]
    quality["generated_from_evidence_refs"] = [artifact["id"]]

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("generated evidence provenance graph contains a cycle" in error for error in report.errors)


def test_evidence_sha256_mismatch_is_error(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    evidence = next(item for item in changed["evidence"] if item["id"] == "ev.baseline_demand_quality")
    evidence["sha256"] = "0" * 64

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert "evidence sha256 mismatch: ev.baseline_demand_quality" in report.errors


def test_issue_requires_resolution_status(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    issue = next(node for node in changed["nodes"] if node["id"] == "issue.delivery_metric_definition")
    issue.pop("resolution_status")

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert "issue requires resolution_status: issue.delivery_metric_definition" in report.errors


def test_unknown_problem_scale_requires_reason(tmp_path: Path, registry: dict) -> None:
    changed = copy.deepcopy(registry)
    classical = next(node for node in changed["nodes"] if node["id"] == "method.classical")
    classical["problem_scale"][0].pop("unknown_reason")

    report = validate_registry(write_registry(tmp_path, changed), SCHEMA_PATH)

    assert any("unknown problem scale requires unknown_reason" in error for error in report.errors)


def test_intentional_isolated_issue_does_not_warn(registry: dict) -> None:
    issue = next(node for node in registry["nodes"] if node["id"] == "issue.future_external_models_missing")
    assert issue["intentionally_isolated"] is True
    assert issue["scope_refs"]
    assert "isolated node: issue.future_external_models_missing" not in validate_registry().warnings
