"""Canonical candidate/smoke artifact writer for reduced R23."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .schema import canonical_json, config_payload, sha256_bytes

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
