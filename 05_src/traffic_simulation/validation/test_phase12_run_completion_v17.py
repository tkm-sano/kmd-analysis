from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from traffic_simulation.network import execute_v17_phase12_full_population as phase12_runner
from traffic_simulation.network.validate_v17_phase12_run_completion import (
    Phase12RunCompletionError,
    _semantic_hash,
    validate_major_artifacts,
    validate_run_gate,
)
from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
POLICY_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml"


def _rehash(value: dict) -> dict:
    value["semantic_sha256"] = _semantic_hash(value)
    return value


def _stage_set(profile: str, *, permission_blocked: bool) -> dict:
    permission = {
        "permission_record_id": f"permission-{profile}",
        "directed_segment_id": "segment-1",
        "lane_position": 0,
        "vehicle_class": "delivery",
        "resolution_status": "unresolved" if permission_blocked else "resolved",
        "stop_code": "ACCESS_PERMISSION_UNRESOLVED" if permission_blocked else None,
    }
    blocker = {
        "permission_record_id": permission["permission_record_id"],
        "source_way_id": 1,
        "scope": "lane_tuple",
        "stop_code": "ACCESS_PERMISSION_UNRESOLVED",
        "resolution_status": "unresolved",
    }
    directed = {"counts": {}, "blockers": [], "directed_segments": [], "semantic_sha256": "directed"}
    lanes = {
        "counts": {}, "blockers": [], "resolutions": [], "segment_lanes": [],
        "directed_segment_semantic_sha256": "directed", "semantic_sha256": "lanes",
    }
    static = {
        "counts": {}, "blockers": [], "normalized_rules": [],
        "directional_lane_semantic_sha256": "lanes", "semantic_sha256": "static",
    }
    conditional = {
        "counts": {}, "blockers": [], "conditional_rules": [],
        "static_access_semantic_sha256": "static", "semantic_sha256": "conditional",
    }
    final = {
        "counts": {}, "blockers": [blocker] if permission_blocked else [],
        "permission_records": [permission],
        "conditional_access_semantic_sha256": "conditional", "semantic_sha256": "permission",
    }
    speed = {"counts": {}, "blockers": [], "speed_records": [], "semantic_sha256": "speed"}
    return {
        "directed_segments": directed,
        "directional_lanes": lanes,
        "static_access": static,
        "conditional_access": conditional,
        "final_permission": final,
        "speed": speed,
    }


def _profile(profile: str, *, permission_blocked: bool) -> dict:
    stages = _stage_set(profile, permission_blocked=permission_blocked)
    return _rehash({
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "profile": profile,
        "scenario_context_id": "context-1",
        "source_sha256": "a" * 64,
        "stage_outputs": stages,
        "counts": {},
        "blockers": list(stages["final_permission"]["blockers"]),
    })


def _unit(unit_id: str, *, unresolved: int = 0, resolved: int = 0) -> dict:
    governed = unresolved + resolved
    return {
        "population_unit_id": unit_id,
        "input": governed,
        "governed": governed,
        "excluded": 0,
        "resolved": resolved,
        "unresolved": unresolved,
        "conflict": 0,
        "invalid": 0,
        "valid_but_unsupported": 0,
    }


def artifacts() -> dict:
    structural = _profile("structural", permission_blocked=False)
    formal = _profile("formal", permission_blocked=True)
    inventory = _rehash({
        "entries": [{
            "blocker_id": "blocker-1",
            "record_id": "final_permission:permission-formal",
            "attribute_name": "final_permission",
            "root_cause_category": "missing_registered_rule",
            "root_cause_record_ids": ["root-1"],
            "selected_strategy": {"value": "preserve_and_resolve"},
        }],
        "counts": {
            "total": 1,
            "by_strategy": {"preserve_and_resolve": 1},
            "by_root_cause": {"missing_registered_rule": 1},
        },
    })
    exclusion = _rehash({
        "schema_version": 17,
        "manifest_id": "test-empty-exclusions",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "policy_id": "FORMAL_BLOCKER_POLICY_V17",
        "entries": [],
        "population_counts": {"input": 1, "governed": 1, "excluded": 0},
    })
    accounting = _rehash({
        "population_units": [
            _unit("formal_directional_lane_source_way"),
            _unit("formal_static_access_source_way"),
            _unit("formal_conditional_access_source_way"),
            _unit("formal_permission_lane_tuple", unresolved=1),
            _unit("formal_speed_directed_segment"),
        ],
        "root_cause_records": [{
            "root_cause_record_id": "root-1",
            "affected_permission_record_count": 1,
        }],
        "blocker_relationships": {
            "upstream_record_count": 0,
            "permission_blocker_count": 1,
            "deduplicated_blocker_count": 1,
            "causal_edges": [{
                "root_cause_record_id": "root-1",
                "downstream_record_id": "final_permission:permission-formal",
            }],
            "suppressed_candidates": [],
        },
        "profile_population_difference": {
            "formal_record_count": 1,
            "structural_record_count": 1,
            "difference": 0,
            "by_assumption_id": {},
            "missing_formal_record_detected": False,
            "duplicate_structural_record_detected": False,
            "unregistered_assumption_detected": False,
        },
        "exclusion_audit": {
            "excluded_way_count": 0,
            "excluded_way_ratio": 0,
            "excluded_length_m": 0,
            "excluded_length_ratio": 0,
            "by_highway_class": {},
            "by_original_stop_code": {},
        },
        "exclusion_network_impact": {
            "removed_edge_count": 0,
            "removed_total_length_m": 0,
            "critical_connector_removed": False,
            "result": "passed",
        },
    })
    return {
        "structural_full_population": structural,
        "formal_full_population": formal,
        "complete_blocker_inventory": inventory,
        "exclusion_manifest": exclusion,
        "population_accounting": accounting,
    }


@pytest.fixture(scope="module")
def governance() -> tuple[dict, dict]:
    return (
        yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")),
        yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")),
    )


def validate(value: dict, governance: tuple[dict, dict]) -> dict[str, str]:
    registry, policy = governance
    return validate_major_artifacts(value, registry=registry, policy=policy)


def test_valid_single_run_major_artifacts_pass(governance: tuple[dict, dict]) -> None:
    assert set(validate(artifacts(), governance).values()) == {"passed"}


def test_semantic_hash_modification_is_rejected(governance: tuple[dict, dict]) -> None:
    value = artifacts()
    value["formal_full_population"]["semantic_sha256"] = "0" * 64
    with pytest.raises(Phase12RunCompletionError, match="semantic_hash"):
        validate(value, governance)


def test_duplicate_record_identity_is_rejected(governance: tuple[dict, dict]) -> None:
    value = artifacts()
    formal = value["formal_full_population"]
    records = formal["stage_outputs"]["final_permission"]["permission_records"]
    records.append(copy.deepcopy(records[0]))
    _rehash(formal)
    with pytest.raises(Phase12RunCompletionError, match="identity_uniqueness"):
        validate(value, governance)


def test_population_equation_modification_is_rejected(governance: tuple[dict, dict]) -> None:
    value = artifacts()
    accounting = value["population_accounting"]
    accounting["population_units"][3]["input"] += 1
    _rehash(accounting)
    with pytest.raises(Phase12RunCompletionError, match="population_accounting"):
        validate(value, governance)


def test_unregistered_assumption_is_rejected(governance: tuple[dict, dict]) -> None:
    value = artifacts()
    structural = value["structural_full_population"]
    structural["stage_outputs"]["speed"]["assumption_ids"] = ["UNREGISTERED_ASSUMPTION"]
    _rehash(structural)
    with pytest.raises(Phase12RunCompletionError, match="registered_values"):
        validate(value, governance)


def test_permission_blocker_without_root_cause_is_rejected(governance: tuple[dict, dict]) -> None:
    value = artifacts()
    inventory = value["complete_blocker_inventory"]
    inventory["entries"][0]["root_cause_record_ids"] = []
    _rehash(inventory)
    with pytest.raises(Phase12RunCompletionError, match="blocker_exclusion"):
        validate(value, governance)


def test_missing_major_artifacts_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(Phase12RunCompletionError, match="missing major artifacts"):
        validate_run_gate("run_1", "required_artifacts", output_root=tmp_path)


def test_existing_artifact_is_not_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "artifact.json"
    original = {"value": "original"}
    phase12_runner._atomic_json(target, original)

    with pytest.raises(phase12_runner.Phase12ExecutionError, match="refusing to overwrite"):
        phase12_runner._atomic_json(target, {"value": "replacement"})

    assert phase12_runner._load_json(target) == original


def _finalize_contract() -> dict:
    return {
        "contract_id": "OTA_WARD_V17_PHASE12_OUTPUT_CONTRACT",
        "execution": {
            "output_root": "phase12-test-output",
            "required_run_ids": ["run_1", "run_2"],
            "published_path": "published",
            "publish_source_run": "run_1",
        },
        "artifact_catalog": [{
            "artifact_id": "determinism_report",
            "path_template": "determinism_report.json",
            "schema": "unused-determinism-schema.json",
        }],
    }


def test_failed_run_manifest_prohibits_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "phase12-test-output"
    root.mkdir()
    copied = False

    def reject_run(*args: object, **kwargs: object) -> dict:
        raise phase12_runner.Phase12ExecutionError("run manifest aggregate differs: run_1")

    def forbidden_copy(*args: object, **kwargs: object) -> None:
        nonlocal copied
        copied = True

    monkeypatch.setattr(phase12_runner, "_require_clean_worktree", lambda: "a" * 40)
    monkeypatch.setattr(phase12_runner, "_load_yaml", lambda path: _finalize_contract())
    monkeypatch.setattr(phase12_runner, "_repo_path", lambda relative: root)
    monkeypatch.setattr(phase12_runner, "_validate_completed_run_manifest", reject_run)
    monkeypatch.setattr(phase12_runner.shutil, "copytree", forbidden_copy)

    with pytest.raises(phase12_runner.Phase12ExecutionError, match="aggregate differs"):
        phase12_runner.finalize()

    assert copied is False
    assert not (root / "published").exists()
    assert not (root / "determinism_report.json").exists()


def test_existing_published_output_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "phase12-test-output"
    published = root / "published"
    published.mkdir(parents=True)
    marker = published / "marker.txt"
    marker.write_text("keep", encoding="utf-8")

    monkeypatch.setattr(phase12_runner, "_require_clean_worktree", lambda: "a" * 40)
    monkeypatch.setattr(phase12_runner, "_load_yaml", lambda path: _finalize_contract())
    monkeypatch.setattr(phase12_runner, "_repo_path", lambda relative: root)

    with pytest.raises(phase12_runner.Phase12ExecutionError, match="published output already exists"):
        phase12_runner.finalize()

    assert marker.read_text(encoding="utf-8") == "keep"
