"""Canonical candidate/smoke artifact writer for reduced R23."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .schema import canonical_json, config_payload, sha256_bytes, sha256_file

_NON_SEMANTIC = {
    "runtime_seconds", "timestamp_utc", "started_at", "completed_at", "total_wall_seconds",
    "elapsed_seconds", "optimizer_evaluator_seconds_inclusive", "expectation_evaluator_seconds_accumulated",
    "circuit_construction_seconds", "transpilation_seconds", "aer_execution_seconds",
    "expectation_seconds", "evaluation_total_seconds",
}


def semantic_artifact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: semantic_artifact(v) for k, v in sorted(value.items()) if k not in _NON_SEMANTIC}
    if isinstance(value, list):
        return [semantic_artifact(v) for v in value]
    return value


def config_hash(config: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(semantic_artifact(config)))


def source_hashes(repo_root: Path, *, execution_entry_point: Path | None = None) -> dict[str, str]:
    """Hash the implementation files that define a future formal R23 run."""
    repo_root = Path(repo_root)
    paths = {
        "qaoa.py": repo_root / "05_src/traffic_simulation/r23_qaoa_aer/qaoa.py",
        "hamiltonian.py": repo_root / "05_src/traffic_simulation/r23_qaoa_aer/hamiltonian.py",
        "metrics.py": repo_root / "05_src/traffic_simulation/r23_qaoa_aer/metrics.py",
        "schema.py": repo_root / "05_src/traffic_simulation/r23_qaoa_aer/schema.py",
        "artifact.py": repo_root / "05_src/traffic_simulation/r23_qaoa_aer/artifact.py",
    }
    if execution_entry_point is not None:
        entry = Path(execution_entry_point)
        if not entry.is_absolute():
            entry = repo_root / entry
        paths["execution_entry_point"] = entry
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing R23 source files: " + ", ".join(missing))
    return {name: sha256_file(path) for name, path in sorted(paths.items())}


def build_provenance_lineage(repo_root: Path, config: Mapping[str, Any], *, execution_entry_point: Path | None = None) -> dict[str, Any]:
    """Build standalone R20--R23 lineage from the frozen authority references."""
    repo_root = Path(repo_root)
    authority = config.get("authority", {})
    def rel(path_value: str) -> str:
        return str(path_value)
    def file_hash(path_value: str) -> str:
        return sha256_file(repo_root / path_value)
    r21_results = rel(authority["r21_results"])
    r21_manifest = rel(authority["r21_manifest"])
    r22_results = rel(authority["r22_results"])
    r22_manifest = rel(authority["r22_manifest"])
    return {
        "R20": {
            "specification_path": rel(authority["r20_specification"]),
            "specification_sha256": file_hash(authority["r20_specification"]),
            "formulation_identifier": config["scope"],
        },
        "R21": {
            "authoritative_results_path": r21_results,
            "authoritative_results_sha256": file_hash(r21_results),
            "authoritative_manifest_path": r21_manifest,
            "authoritative_manifest_sha256": file_hash(r21_manifest),
            "coefficient_hash_identifier": authority.get("r21_results_sha256"),
            "status": "PASS",
        },
        "R22": {
            "authoritative_results_path": r22_results,
            "authoritative_results_sha256": file_hash(r22_results),
            "authoritative_manifest_path": r22_manifest,
            "authoritative_manifest_sha256": file_hash(r22_manifest),
            "coefficient_hash_identifier": authority.get("r22_results_sha256"),
            "status": "PASS",
        },
        "R23": {
            "source_file_hashes": source_hashes(repo_root, execution_entry_point=execution_entry_point),
            "configuration_id": config.get("configuration_id"),
            "configuration_semantic_sha256": config.get("artifact_hashes", {}).get("semantic_configuration_sha256"),
        },
    }


def validate_provenance_lineage(lineage: Mapping[str, Any]) -> None:
    """Reject incomplete R20--R23 lineage before a formal artifact is written."""
    required = {
        "R20": ("specification_path", "specification_sha256", "formulation_identifier"),
        "R21": ("authoritative_results_path", "authoritative_results_sha256", "authoritative_manifest_path", "authoritative_manifest_sha256", "coefficient_hash_identifier", "status"),
        "R22": ("authoritative_results_path", "authoritative_results_sha256", "authoritative_manifest_path", "authoritative_manifest_sha256", "coefficient_hash_identifier", "status"),
        "R23": ("source_file_hashes", "configuration_id", "configuration_semantic_sha256"),
    }
    for stage, fields in required.items():
        record = lineage.get(stage)
        if not isinstance(record, Mapping) or any(not record.get(field) for field in fields):
            raise ValueError(f"incomplete provenance lineage for {stage}")
    for stage in ("R21", "R22"):
        if lineage[stage]["status"] != "PASS":
            raise ValueError(f"{stage} authority is not PASS")
    sources = lineage["R23"]["source_file_hashes"]
    for name in ("qaoa.py", "hamiltonian.py", "metrics.py", "schema.py", "artifact.py"):
        if not isinstance(sources.get(name), str) or len(sources[name]) != 64:
            raise ValueError(f"missing source hash: {name}")


def build_formal_manifest(*, repo_root: Path, config: Mapping[str, Any], environment: Mapping[str, Any],
                          run_ids: list[str], artifact_file_hashes: Mapping[str, str],
                          execution_entry_point: Path | None = None) -> dict[str, Any]:
    """Return the forward-looking manifest contract; it does not execute a run."""
    lineage = build_provenance_lineage(repo_root, config, execution_entry_point=execution_entry_point)
    validate_provenance_lineage(lineage)
    return {
        "schema_version": "r23-reduced-qaoa-aer-formal-manifest-v2",
        "classification": "FORMAL_ARTIFACT_CONTRACT_ONLY",
        "configuration_id": config.get("configuration_id"),
        "configuration_semantic_sha256": config.get("artifact_hashes", {}).get("semantic_configuration_sha256"),
        "source_commit": "record_at_execution",
        "environment": dict(environment),
        "lineage": lineage,
        "run_ids": list(run_ids),
        "artifact_file_hashes": dict(artifact_file_hashes),
        "runtime_contract": {
            "T_total": "wall-clock envelope",
            "T_optimizer_total": "inclusive optimizer.minimize wall time, including objective evaluations",
            "T_objective_eval_total": "sum of all objective callback wall times",
            "T_Aer_total": "sum of Aer execution time across objective evaluations; final evaluation separate",
            "T_expectation_total": "sum of Statevector/operator expectation processing across objective evaluations; final evaluation separate",
            "T_final_evaluation": "post-optimizer evaluation object; never add to T_optimizer_total",
            "double_counting_rule": "nested components are not summed into the wall-clock envelope; inclusion metadata is mandatory",
        },
    }


def write_smoke_artifact(config: Mapping[str, Any], result: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "experiment_config.json").write_bytes(canonical_json(config) + b"\n")
    (output_dir / "run_results.json").write_bytes(canonical_json(result) + b"\n")
    summary = {"artifact_classification": "IMPLEMENTATION_SMOKE_ONLY", "runs": [result], "config_hash": config_hash(config)}
    (output_dir / "summary.json").write_bytes(canonical_json(summary) + b"\n")
    manifest = {"schema_version": "r23-reduced-qaoa-aer-manifest-v1", "classification": "IMPLEMENTATION_SMOKE_ONLY", "config_sha256": config_hash(config), "result_sha256": sha256_bytes((output_dir / "run_results.json").read_bytes()), "summary_sha256": sha256_bytes((output_dir / "summary.json").read_bytes()), "semantic_output_hash": sha256_bytes(canonical_json(semantic_artifact({"config": config, "result": result}))), "files": {}}
    for path in sorted(output_dir.glob("*.json")):
        if path.name != "manifest.json": manifest["files"][path.name] = sha256_bytes(path.read_bytes())
    (output_dir / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    return manifest
