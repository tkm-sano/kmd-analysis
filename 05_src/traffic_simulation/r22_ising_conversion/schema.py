"""R21 provenance loader and reduced R22 input schema."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from traffic_simulation.r20_route_ordering.core import QuboCoefficients
from traffic_simulation.r21_qubo_validation.schema import coefficients_from_payload

from .converter import BINARY_SPIN_CONVENTION

R22_SCHEMA_VERSION = "r22-reduced-ising-conversion-v1"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class R22SchemaError(ValueError):
    """Invalid reduced R22 input or upstream R21 evidence."""

    reason_code = "R21_INPUT_NOT_PASS"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def coefficient_hash(coefficients: QuboCoefficients) -> str:
    payload = {
        "constant": float(coefficients.constant),
        "linear": {str(k): float(v) for k, v in sorted(coefficients.linear.items())},
        "quadratic": {f"{a},{b}": float(v) for (a, b), v in sorted(coefficients.quadratic.items())},
        "n_logical": coefficients.n_logical,
    }
    return sha256_bytes(canonical_json(payload))


def ising_coefficient_hash(coefficients) -> str:
    payload = {
        "constant": float(coefficients.constant),
        "linear": {str(k): float(v) for k, v in sorted(coefficients.linear.items())},
        "quadratic": {f"{a},{b}": float(v) for (a, b), v in sorted(coefficients.quadratic.items())},
        "n_logical": coefficients.n_logical,
        "binary_spin_convention": coefficients.binary_spin_convention,
    }
    return sha256_bytes(canonical_json(payload))


@dataclass(frozen=True)
class R22Input:
    payload: Mapping[str, Any]
    qubo: QuboCoefficients

    @property
    def instance_id(self) -> str:
        return str(self.payload["instance_id"])

    @property
    def customer_ids(self) -> tuple[Any, ...]:
        return tuple(self.payload.get("customer_ids", ()))


def _hash(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise R22SchemaError(f"{name} must be a 64-character SHA-256 hash")
    return value


def load_input(value: Mapping[str, Any]) -> R22Input:
    if not isinstance(value, Mapping):
        raise R22SchemaError("R22 input must be an object")
    required = ("schema_version", "r21", "instance_id", "n", "n_logical", "variable_ordering", "qubo_coefficients", "qubo_coefficient_hash", "lambda", "B", "bound_type", "normalization_metadata", "numerical_tolerance")
    missing = [key for key in required if key not in value]
    if missing:
        raise R22SchemaError(f"missing R22 fields: {', '.join(missing)}")
    if value["schema_version"] != R22_SCHEMA_VERSION:
        raise R22SchemaError("R22 schema/version mismatch")
    r21 = value["r21"]
    if not isinstance(r21, Mapping) or r21.get("status") != "PASS" or r21.get("scope") != "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY":
        raise R22SchemaError("R21 reduced evidence is not PASS for the required scope")
    _hash(r21.get("validation_results_sha256"), "r21.validation_results_sha256")
    _hash(r21.get("manifest_sha256"), "r21.manifest_sha256")
    try:
        n = int(value["n"]); n_logical = int(value["n_logical"])
    except (TypeError, ValueError) as exc:
        raise R22SchemaError("n and n_logical must be integers") from exc
    if n <= 0 or n_logical != n * n:
        raise R22SchemaError("n_logical must equal n squared")
    if value["variable_ordering"] != "row-major:index=(i-1)*n+(t-1)":
        raise R22SchemaError("unsupported variable ordering")
    qubo = coefficients_from_payload(value["qubo_coefficients"])
    if qubo.n_logical != n_logical or value["qubo_coefficient_hash"] != coefficient_hash(qubo):
        raise R22SchemaError("QUBO coefficient hash mismatch")
    for name in ("lambda", "B"):
        try: number = float(value[name])
        except (TypeError, ValueError) as exc: raise R22SchemaError(f"{name} must be numeric") from exc
        if not math.isfinite(number):
            raise R22SchemaError(f"{name} must be finite")
    if not math.isfinite(float(value["lambda"])) or float(value["lambda"]) <= float(value["B"]):
        raise R22SchemaError("lambda must be finite and strictly greater than B")
    if not isinstance(value["normalization_metadata"], Mapping) or not isinstance(value["numerical_tolerance"], Mapping):
        raise R22SchemaError("normalization_metadata and numerical_tolerance must be objects")
    return R22Input(dict(value), qubo)


def load_r21_instance(artifact_dir: Path, instance_id: str | None = None) -> R22Input:
    """Load one PASSed R21 instance and verify its report/manifest hashes."""
    artifact_dir = Path(artifact_dir)
    report_path = artifact_dir / "validation_results.json"
    manifest_path = artifact_dir / "manifest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_report_hash = sha256_file(report_path)
    actual_manifest_hash = sha256_file(manifest_path)
    expected_report_hash = manifest.get("files", {}).get("validation_results.json")
    if expected_report_hash != actual_report_hash:
        raise R22SchemaError("R21 validation-results hash mismatch")
    if report.get("status") != "PASS" or report.get("scope") != "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY":
        raise R22SchemaError("R21 artifact is not PASS for the reduced scope")
    candidates = [item for item in report.get("instances", []) if instance_id is None or item.get("instance_id") == instance_id]
    if len(candidates) != 1:
        raise R22SchemaError("R21 instance selection is not unique")
    item = candidates[0]
    snapshot = item.get("input_snapshot")
    if not isinstance(snapshot, Mapping):
        raise R22SchemaError("R21 input snapshot is missing")
    payload = {
        "schema_version": R22_SCHEMA_VERSION,
        "r21": {"artifact_id": str(artifact_dir), "validation_results_sha256": actual_report_hash, "manifest_sha256": actual_manifest_hash, "status": report["status"], "scope": report["scope"]},
        "instance_id": item["instance_id"], "depot_id": snapshot.get("depot_id"), "customer_ids": snapshot.get("customer_ids", []),
        "n": item["n"], "n_logical": item["n_logical"], "variable_ordering": snapshot["variable_ordering"],
        "qubo_coefficients": snapshot["qubo_coefficients"], "qubo_coefficient_hash": item["coefficient_hash"],
        "lambda": snapshot["lambda"], "B": snapshot["B"], "bound_type": snapshot["bound_type"],
        "normalization_metadata": {"tau_max": snapshot.get("tau_max"), "input_scale": "normalized", "rule": "tau/tau_max"},
        "numerical_tolerance": snapshot.get("numerical_tolerance", {}),
        "r21_global_minimum_bitstrings": item.get("qubo_global_minimum_bitstrings", []),
        "r21_optimal_routes": item.get("qubo_optimal_routes", []),
        "source_provenance": {"routing_source": snapshot.get("routing_source"), "r20_formulation_source_commit": snapshot.get("r20_formulation_source_commit"), "r20_gate_commit": snapshot.get("r20_gate_commit")},
    }
    return load_input(payload)
