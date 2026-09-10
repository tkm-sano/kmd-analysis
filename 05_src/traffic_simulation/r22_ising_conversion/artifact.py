"""Deterministic R22 conversion artifact writer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .schema import canonical_json

_NON_SEMANTIC = {"runtime_seconds", "timestamp_utc", "started_at", "completed_at"}


def semantic_artifact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: semantic_artifact(item) for key, item in sorted(value.items()) if key not in _NON_SEMANTIC}
    if isinstance(value, list):
        return [semantic_artifact(item) for item in value]
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_conversion_artifact(result: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    conversion_path = output_dir / "conversion_results.json"
    conversion_path.write_bytes(canonical_json(result) + b"\n")
    manifest = {
        "schema_version": result.get("schema_version"), "r22_stage": "R22_REDUCED_ISING_CONVERSION", "status": result.get("status"),
        "files": {"conversion_results.json": sha256_bytes(conversion_path.read_bytes())},
        "semantic_output_hash": sha256_bytes(canonical_json(semantic_artifact(result))),
    }
    for key in ("source_commit", "r22_governance_commit", "r21_artifact_id", "r21_validation_results_sha256", "r21_manifest_sha256", "qubo_coefficient_hash", "ising_coefficient_hash", "execution_plan_sha256", "spec_hashes", "code_hashes"):
        if key in result:
            manifest[key] = result[key]
    (output_dir / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    return manifest
