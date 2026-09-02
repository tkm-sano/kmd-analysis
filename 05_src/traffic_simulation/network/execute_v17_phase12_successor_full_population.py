"""Execute one clean Phase 12-equivalent successor run with the current adopted v17 bundle."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network import execute_v17_phase12_full_population as phase12
from traffic_simulation.network.scenario_context_v17 import load_governed_runtime_context
from traffic_simulation.network.validate_v17_phase12_successor_run import (
    build_profile_population_difference,
    validate_successor_major_artifacts,
)
from traffic_simulation.paths import REPOSITORY_ROOT


SUCCESSOR_ID = "phase12_20260902_profile_difference_v1_2"
BASE_HEAD = "2bb66d0b431d75485847b7c443cd5e08164b64f0"
OUTPUT_ROOT = (
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    + SUCCESSOR_ID
)
CONTRACT_PATH = Path(
    "reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml"
)
CONTRACT_AMENDMENT_PATH = Path("reproducibility/config/traffic_simulation/v17_phase12_output_contract_profile_difference_v1_2.yml")
PROFILE_DIFFERENCE_DECISION_PATH = Path(
    "reproducibility/config/traffic_simulation/decisions/"
    "phase12_decision_a_formal_only_profile_difference_v1_1.yml"
)
MANIFEST_SCHEMA = Path(
    "reproducibility/config/traffic_simulation/schemas/"
    "phase12_successor_run_manifest_v1.schema.json"
)
DETERMINISM_SCHEMA = Path(
    "reproducibility/config/traffic_simulation/schemas/"
    "phase12_successor_determinism_report_v1.schema.json"
)
RUNTIME_REQUIREMENTS = Path("reproducibility/environment/requirements-analysis.txt")

ADOPTED_AUTHORITIES = (
    Path("05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md"),
    Path("05_src/traffic_simulation/specifications/formal_lane_evidence_policy_v17.md"),
    Path("05_src/traffic_simulation/specifications/11_formal_blocker_resolution_exclusion_policy_v17.md"),
    Path("05_src/traffic_simulation/specifications/12_phase12_full_population_output_contract_v17.md"),
    Path("05_src/traffic_simulation/specifications/13_phase12_profile_difference_contract_v17_2.md"),
    CONTRACT_AMENDMENT_PATH,
    PROFILE_DIFFERENCE_DECISION_PATH,
    Path("reproducibility/config/traffic_simulation/sumo_network_v17.yml"),
    Path("reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"),
    Path("reproducibility/config/traffic_simulation/v17_semantic_invariants.yml"),
    Path("reproducibility/config/traffic_simulation/v17_governed_runtime_interval_context.yml"),
    Path("reproducibility/config/traffic_simulation/japan_speed_rules_v17.yml"),
    Path("reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml"),
    Path("reproducibility/config/traffic_simulation/formal_evidence_methods_v17.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_vehicle_ontology_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_horse_vehicle_ontology_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_psv_vehicle_ontology_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_motorcar_vehicle_ontology_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_use_sidepath_semantics_decision_v1_1.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_private_authorization_context_resolution.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_lane_bidirectional_lanes2_formal_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_lane_count_from_road_lane_vector_decision.yml"),
    Path("reproducibility/config/traffic_simulation/v17_phase13_lane_bidirectional_shared_single_lane_decision.yml"),
)

IMPLEMENTATIONS = (
    Path("05_src/traffic_simulation/network/directed_segments_v17.py"),
    Path("05_src/traffic_simulation/network/directional_lanes_v17.py"),
    Path("05_src/traffic_simulation/network/static_access_v17.py"),
    Path("05_src/traffic_simulation/network/conditional_access_v17.py"),
    Path("05_src/traffic_simulation/network/final_permission_v17.py"),
    Path("05_src/traffic_simulation/network/speed_resolution_v17.py"),
    Path("05_src/traffic_simulation/network/scenario_context_v17.py"),
    Path("05_src/traffic_simulation/network/formal_blocker_governance_v17.py"),
    Path("05_src/traffic_simulation/network/execute_v17_phase12_full_population.py"),
    Path("05_src/traffic_simulation/network/validate_v17_phase12_run_completion.py"),
    Path("05_src/traffic_simulation/network/validate_v17_phase12_successor_run.py"),
    Path("05_src/traffic_simulation/network/validate_v17_phase12_profile_difference_contract.py"),
    Path("05_src/traffic_simulation/network/execute_v17_phase12_successor_full_population.py"),
)

RELEVANT_SCHEMAS = (
    Path("reproducibility/config/traffic_simulation/schemas/phase12_profile_artifact_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/formal_blocker_inventory_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/exclusion_manifest_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/phase12_population_accounting_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/phase12_population_accounting_v17_2.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/directed_segment_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/access_rule_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/final_permission_expectation_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/speed_resolution_record_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/semantic_invariants_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/governed_runtime_interval_context_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/japan_speed_rules_v17.schema.json"),
    Path("reproducibility/config/traffic_simulation/schemas/formal_blocker_policy_v17.schema.json"),
    MANIFEST_SCHEMA,
    DETERMINISM_SCHEMA,
)


class SuccessorRunError(ValueError):
    pass


def _repo_path(relative: Path | str) -> Path:
    item = PurePosixPath(str(relative))
    if item.is_absolute() or ".." in item.parts:
        raise SuccessorRunError(f"unsafe repository path: {relative}")
    result = (REPOSITORY_ROOT / Path(*item.parts)).resolve()
    if not result.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise SuccessorRunError(f"repository path escapes root: {relative}")
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_map(paths: Sequence[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = _repo_path(relative)
        if not path.is_file():
            raise SuccessorRunError(f"required bundle file is absent: {relative}")
        result[str(relative)] = _sha256(path)
    return dict(sorted(result.items()))


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SuccessorRunError(f"YAML root is not an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SuccessorRunError(f"JSON root is not an object: {path}")
    return value


def _require_clean_worktree() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    if status:
        raise SuccessorRunError("successor Formal run requires a clean Git worktree")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def _validate_json(value: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema,
        resolver=jsonschema.RefResolver(base_uri=schema_path.resolve().as_uri(), referrer=schema),
        format_checker=jsonschema.FormatChecker(),
    ).validate(value)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    phase12._atomic_json(path, value)


def _runtime_environment() -> dict[str, Any]:
    packages = {
        name: importlib.metadata.version(name)
        for name in ("PyYAML", "jsonschema", "pytest")
    }
    history = Path(sys.prefix) / "conda-meta/history"
    return {
        "authority": "hayate_native_conda",
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "requirements_path": str(RUNTIME_REQUIREMENTS),
        "requirements_sha256": _sha256(_repo_path(RUNTIME_REQUIREMENTS)),
        "conda_history_sha256": _sha256(history) if history.is_file() else None,
        "packages": packages,
        "random_seeds": {"resolver": 0},
        "sumo_version": "not_invoked_phase12_successor",
    }


def execute(run_id: str) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    source_commit = _require_clean_worktree()
    contract = _load_yaml(_repo_path(CONTRACT_PATH))
    amendment = _load_yaml(_repo_path(CONTRACT_AMENDMENT_PATH))
    decision = _load_yaml(_repo_path(PROFILE_DIFFERENCE_DECISION_PATH))
    input_path = _repo_path(contract["fixed_inputs"]["source_osm"])
    context = load_governed_runtime_context()
    stages = {
        profile: phase12._build_stages(input_path, profile, context)
        for profile in ("structural", "formal")
    }
    source_hash = _sha256(input_path)
    profiles = {
        profile: phase12._profile_artifact(
            profile, value, source_hash, context["scenario_context_id"]
        )
        for profile, value in stages.items()
    }
    blockers, root_causes = phase12._blocker_inventory(stages["formal"])
    exclusion = phase12._exclusion_manifest(
        stages["formal"]["final_permission"]["permission_records"]
    )
    accounting = phase12._population_accounting(
        stages["formal"], stages["structural"], blockers, root_causes
    )
    accounting["schema_version"] = "17.2.0"
    accounting["profile_population_difference"] = build_profile_population_difference(
        stages["structural"], stages["formal"], registry=_load_yaml(
            _repo_path(contract["fixed_inputs"]["registry_bundle"])
        ), decision=decision
    )
    # Every accounting unit carries the profile partition.  Upstream units are
    # source-governed populations; the lane/permission identity comparison is
    # recorded in the dedicated profile-difference object below.
    lane_diff = accounting["profile_population_difference"]["lane_identities"]
    permission_diff = accounting["profile_population_difference"]["permission_identities"]
    for unit in accounting["population_units"]:
        unit.update({
            "structural_count": unit["governed"],
            "formal_count": unit["governed"],
            "common_count": unit["governed"],
            "structural_only_count": 0,
            "formal_only_count": 0,
            "authorized_formal_only_count": 0,
            "unauthorized_formal_only_count": 0,
            "same_identity_inconsistent_count": 0,
        })
    for unit_id, diff in (("formal_lane_canonical_representation", lane_diff), ("formal_permission_lane_tuple", permission_diff)):
        unit = next(item for item in accounting["population_units"] if item["population_unit_id"] == unit_id)
        unit.update({
            "structural_count": diff["structural_count"], "formal_count": diff["formal_count"],
            "common_count": diff["common_count"], "structural_only_count": diff["structural_only_count"],
            "formal_only_count": diff["formal_only_count"],
            "authorized_formal_only_count": diff["authorized_formal_only_count"],
            "unauthorized_formal_only_count": diff["unauthorized_formal_only_count"],
            "same_identity_inconsistent_count": diff["same_identity_inconsistent_count"],
        })
    accounting = phase12._with_semantic_hash(accounting)
    payloads = {
        "structural_full_population": profiles["structural"],
        "formal_full_population": profiles["formal"],
        "complete_blocker_inventory": blockers,
        "exclusion_manifest": exclusion,
        "population_accounting": accounting,
    }
    catalog = {item["artifact_id"]: item for item in contract["artifact_catalog"]}
    catalog["population_accounting"] = {
        **catalog["population_accounting"],
        "schema": amendment["overrides"]["population_accounting_schema"],
    }
    root = _repo_path(OUTPUT_ROOT)
    run_root = root / "runs" / run_id
    if run_root.exists():
        raise SuccessorRunError(f"run output already exists: {run_root}")
    references = []
    for artifact_id, value in payloads.items():
        item = catalog[artifact_id]
        schema_path = _repo_path(item["schema"])
        _validate_json(value, schema_path)
        relative = Path(item["path_template"].format(run_id=run_id)).relative_to(
            Path("runs") / run_id
        )
        path = run_root / relative
        _write_json(path, value)
        references.append({
            "artifact_id": artifact_id,
            "path": str(path.relative_to(REPOSITORY_ROOT)),
            "schema": item["schema"],
            "byte_sha256": _sha256(path),
            "semantic_sha256": value["semantic_sha256"],
        })
    registry = _load_yaml(
        _repo_path(contract["fixed_inputs"]["registry_bundle"])
    )
    policy = _load_yaml(_repo_path(contract["fixed_inputs"]["blocker_policy"]))
    validation_results = validate_successor_major_artifacts(
        payloads, registry=registry, policy=policy, decision=decision
    )
    if set(validation_results.values()) != {"passed"}:
        raise SuccessorRunError(f"major artifact validation failed: {validation_results}")
    config = _load_yaml(_repo_path(contract["fixed_inputs"]["configuration"]))
    input_paths = tuple(
        Path(value)
        for key, value in contract["fixed_inputs"].items()
        if key != "hash_binding_required"
    )
    manifest = {
        "schema_version": 1,
        "artifact_type": "phase12_successor_run_manifest",
        "successor_run_id": SUCCESSOR_ID,
        "run_id": run_id,
        "configuration_id": contract["configuration_id"],
        "configuration_version": config.get("configuration_version", config["schema_version"]),
        "population_version": contract["population_version"],
        "profile_set": ["structural", "formal"],
        "governed_vclasses": list(config["permissions"]["governed_vclasses"]),
        "scenario_context_id": context["scenario_context_id"],
        "source_commit": source_commit,
        "base_repository_head": BASE_HEAD,
        "dirty_tree": False,
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "runtime_environment": _runtime_environment(),
        "input_hashes": _hash_map(input_paths),
        "adopted_authority_hashes": _hash_map(ADOPTED_AUTHORITIES),
        "implementation_hashes": _hash_map(IMPLEMENTATIONS),
        "schema_hashes": _hash_map(RELEVANT_SCHEMAS),
        "artifacts": sorted(references, key=lambda item: item["artifact_id"]),
        "validation": {
            **validation_results,
            "registered_values": "passed",
            "blocker_exclusion": "passed",
            "result": "passed",
        },
        "formal_state_mutated": False,
    }
    _validate_json(manifest, _repo_path(MANIFEST_SCHEMA))
    manifest_path = run_root / "successor_run_manifest.json"
    _write_json(manifest_path, manifest)
    return {
        "successor_run_id": SUCCESSOR_ID,
        "run_id": run_id,
        "manifest": str(manifest_path.relative_to(REPOSITORY_ROOT)),
        "manifest_sha256": _sha256(manifest_path),
        "formal_blocker_count": blockers["counts"]["total"],
        "result": "passed",
    }


def finalize() -> dict[str, Any]:
    source_commit = _require_clean_worktree()
    amendment = _load_yaml(_repo_path(CONTRACT_AMENDMENT_PATH))
    root = _repo_path(amendment["overrides"]["execution_output_root"])
    report_path = root / "determinism_report.json"
    published = root / "published"
    temporary = root / ".published.tmp"
    for path in (report_path, published, temporary):
        if path.exists():
            raise SuccessorRunError(f"refusing to overwrite finalization artifact: {path}")

    manifests: dict[str, dict[str, Any]] = {}
    artifact_maps: dict[str, dict[str, Mapping[str, Any]]] = {}
    for run_id in ("run_1", "run_2"):
        manifest_path = root / "runs" / run_id / "successor_run_manifest.json"
        manifest = _load_json(manifest_path)
        _validate_json(manifest, _repo_path(MANIFEST_SCHEMA))
        if manifest["source_commit"] != source_commit or manifest["dirty_tree"] is not False:
            raise SuccessorRunError(f"run source revision differs: {run_id}")
        references = {item["artifact_id"]: item for item in manifest["artifacts"]}
        if len(references) != len(manifest["artifacts"]):
            raise SuccessorRunError(f"duplicate artifact reference: {run_id}")
        for reference in references.values():
            path = _repo_path(reference["path"])
            if not path.is_relative_to((root / "runs" / run_id).resolve()):
                raise SuccessorRunError(f"artifact path escapes run: {run_id}")
            if _sha256(path) != reference["byte_sha256"]:
                raise SuccessorRunError(f"artifact byte hash differs: {run_id}")
            value = _load_json(path)
            if value.get("semantic_sha256") != reference["semantic_sha256"]:
                raise SuccessorRunError(f"artifact semantic hash differs: {run_id}")
            if phase12._semantic_hash(value) != reference["semantic_sha256"]:
                raise SuccessorRunError(f"artifact semantic content differs: {run_id}")
        manifests[run_id] = manifest
        artifact_maps[run_id] = references

    stable_fields = (
        "successor_run_id", "configuration_id", "configuration_version",
        "population_version", "profile_set", "governed_vclasses",
        "scenario_context_id", "source_commit", "base_repository_head",
        "runtime_environment", "input_hashes", "adopted_authority_hashes",
        "implementation_hashes", "schema_hashes", "validation",
        "formal_state_mutated",
    )
    if any(manifests["run_1"][field] != manifests["run_2"][field] for field in stable_fields):
        raise SuccessorRunError("run environment or authority binding differs")
    if set(artifact_maps["run_1"]) != set(artifact_maps["run_2"]):
        raise SuccessorRunError("run artifact sets differ")
    comparisons = []
    for artifact_id in sorted(artifact_maps["run_1"]):
        left = artifact_maps["run_1"][artifact_id]["semantic_sha256"]
        right = artifact_maps["run_2"][artifact_id]["semantic_sha256"]
        comparisons.append({
            "artifact_id": artifact_id,
            "run_1_semantic_sha256": left,
            "run_2_semantic_sha256": right,
            "match": left == right,
        })
    if not all(item["match"] for item in comparisons):
        raise SuccessorRunError("two-run semantic determinism differs")

    report = phase12._with_semantic_hash({
        "schema_version": 1,
        "artifact_type": "phase12_successor_determinism_report",
        "successor_run_id": SUCCESSOR_ID,
        "source_commit": source_commit,
        "comparisons": comparisons,
        "environment_match": True,
        "result": "passed",
    })
    _validate_json(report, _repo_path(DETERMINISM_SCHEMA))
    shutil.copytree(root / "runs" / "run_1", temporary)
    _write_json(report_path, report)
    temporary.rename(published)
    return {
        "successor_run_id": SUCCESSOR_ID,
        "determinism_report": str(report_path.relative_to(REPOSITORY_ROOT)),
        "determinism_report_sha256": _sha256(report_path),
        "published": str(published.relative_to(REPOSITORY_ROOT)),
        "result": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-id", choices=("run_1", "run_2"))
    mode.add_argument("--finalize", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = finalize() if args.finalize else execute(args.run_id)
    except Exception as error:
        print(json.dumps({"successor_execution": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
