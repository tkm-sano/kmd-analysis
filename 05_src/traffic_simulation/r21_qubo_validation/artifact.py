"""Deterministic reduced-R21 artifact serialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .schema import canonical_json

_NON_SEMANTIC_KEYS = {"runtime_seconds", "timestamp_utc", "started_at", "completed_at"}


def semantic_artifact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: semantic_artifact(v) for k, v in sorted(value.items()) if k not in _NON_SEMANTIC_KEYS}
    if isinstance(value, list):
        return [semantic_artifact(v) for v in value]
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_validation_artifact(result: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    """Write a report and manifest; caller must explicitly label smoke output."""
    output_dir.mkdir(parents=True, exist_ok=False)
    report_path = output_dir / "validation_results.json"
    report_path.write_bytes(canonical_json(result) + b"\n")
    manifest = {
        "schema_version": result.get("schema_version"),
        "r21_stage": "R21_REDUCED_QUBO_VALIDATION",
        "status": result.get("status"),
        "files": {"validation_results.json": sha256_bytes(report_path.read_bytes())},
        "output_hash": sha256_bytes(canonical_json(semantic_artifact(result))),
    }
    (output_dir / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    return manifest
