"""R23 reduced input/configuration validation."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

R23_SCHEMA_VERSION = "r23-reduced-qaoa-aer-v1"
R23_SCOPE = "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"
R22_REPORT_SHA256 = "1b6015bcaf38d58fb98a743f47346be9e68601c0b0f7c09567ca77186ea26cea"
R22_MANIFEST_SHA256 = "2bd1bed556b265cc4b6f555497f78e1e432c8d22dabfcccb722fe0faf0da46d9"
PROBABILITY_RANGE_TOLERANCE = 1e-12
PROBABILITY_SUM_TOLERANCE = 1e-12
PROBABILITY_ISCLOSE_TOLERANCE = 1e-12


class R23SchemaError(ValueError):
    reason_code = "PROVENANCE_FAILURE"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def memory_preflight(n_logical: int, memory_limit_gib: float) -> dict[str, Any]:
    """Return a conservative software-memory preflight without allocating a statevector."""
    if n_logical < 0 or not math.isfinite(memory_limit_gib) or memory_limit_gib <= 0:
        raise R23SchemaError("invalid memory preflight inputs")
    amplitude_count = 2 ** n_logical
    statevector_bytes = 16 * amplitude_count  # complex128 bytes
    estimated_peak_bytes = 4 * statevector_bytes
    guard_bytes = memory_limit_gib * (1024 ** 3)
    return {
        "logical_qubits": n_logical,
        "statevector_amplitude_count": amplitude_count,
        "estimated_statevector_bytes": statevector_bytes,
        "estimated_peak_bytes": estimated_peak_bytes,
        "configured_memory_guard_gib": memory_limit_gib,
        "configured_memory_guard_bytes": guard_bytes,
        "status": "PASS" if estimated_peak_bytes <= guard_bytes else "FAIL",
        "guard_semantics": "software_execution_safety_only",
    }


@dataclass(frozen=True)
class R23Input:
    instance_id: str
    n: int
    customer_ids: tuple[Any, ...]
    depot_id: Any
    ising_constant: float
    ising_linear: dict[int, float]
    ising_quadratic: dict[tuple[int, int], float]
    ising_coefficient_hash: str
    qubo_coefficient_hash: str
    lambda_value: float
    bound: float
    exact_optimal_bitstrings: frozenset[tuple[int, ...]]
    exact_optimal_spin_states: frozenset[tuple[int, ...]]
    exact_optimal_routes: frozenset[tuple[Any, ...]]
    normalized_matrix: Mapping[Any, Any]
    payload: Mapping[str, Any]

    @property
    def n_logical(self) -> int:
        return self.n * self.n


@dataclass(frozen=True)
class R23Config:
    p: int = 1
    optimizer: str = "COBYLA"
    maxiter: int = 100
    max_evaluations: int = 300
    initial_parameter: float = 0.1
    seed: int = 17
    repetition: int = 1
    expectation_mode: str = "exact_statevector"
    backend_method: str = "statevector"
    device: str = "CPU"
    optimization_level: int = 1
    max_logical_qubits: int = 16
    max_p: int = 3
    wall_time_seconds: float | None = None
    memory_limit_gib: float = 8.0
    probability_threshold: float = 1e-12

    def validate(self, n_logical: int) -> None:
        if self.p not in (1, 2, 3) or self.p > self.max_p:
            raise R23SchemaError("p exceeds the governed reduced R23 range")
        if n_logical > self.max_logical_qubits:
            raise R23SchemaError("logical-qubit software guard exceeded")
        if self.optimizer != "COBYLA" or self.maxiter <= 0 or self.max_evaluations <= 0:
            raise R23SchemaError("unsupported optimizer or invalid iteration/evaluation guard")
        if not math.isfinite(self.initial_parameter) or (self.wall_time_seconds is not None and not math.isfinite(self.wall_time_seconds)):
            raise R23SchemaError("configuration contains non-finite values")
        if self.wall_time_seconds is not None and self.wall_time_seconds <= 0:
            raise R23SchemaError("wall-time safety guard must be positive when configured")
        if self.repetition != 1 or self.expectation_mode != "exact_statevector":
            raise R23SchemaError("only the deterministic exact-expectation baseline is supported")
        if self.backend_method != "statevector" or self.device != "CPU":
            raise R23SchemaError("only the governed CPU statevector backend is supported")
        if self.probability_threshold < 0 or not math.isfinite(self.probability_threshold):
            raise R23SchemaError("probability threshold must be finite and non-negative")
        if memory_preflight(n_logical, self.memory_limit_gib)["status"] != "PASS":
            raise R23SchemaError("software memory guard exceeded")


def load_r22_instance(artifact_dir: Path, instance_id: str) -> R23Input:
    """Load R22's exact Ising coefficients without reconstructing them from QUBO."""
    artifact_dir = Path(artifact_dir)
    report_path, manifest_path = artifact_dir / "conversion_results.json", artifact_dir / "manifest.json"
    if not report_path.exists() or not manifest_path.exists():
        raise R23SchemaError("R22 authoritative artifact files are missing")
    if sha256_file(report_path) != R22_REPORT_SHA256 or sha256_file(manifest_path) != R22_MANIFEST_SHA256:
        raise R23SchemaError("R22 authoritative artifact hash mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("status") != "PASS" or report.get("scope") != R23_SCOPE:
        raise R23SchemaError("R22 artifact is not PASS for the required reduced scope")
    if manifest.get("status") != "PASS" or manifest.get("r22_stage") != "R22_REDUCED_ISING_CONVERSION":
        raise R23SchemaError("R22 manifest status/stage is invalid")
    items = [x for x in report.get("instances", []) if x.get("instance_id") == instance_id]
    if len(items) != 1:
        raise R23SchemaError("R22 instance selection is not unique")
    item = items[0]
    if item.get("status") != "PASS" or not all(item.get("checks", {}).values()):
        raise R23SchemaError("selected R22 instance is not PASS")
    n = int(item["n"])
    linear = {int(k): float(v) for k, v in item["ising_linear"].items()}
    quadratic = {}
    for key, value in item["ising_quadratic"].items():
        a, b = (int(x) for x in key.split(","))
        if a >= b:
            raise R23SchemaError("R22 Ising coupler is not canonical")
        quadratic[(a, b)] = float(value)
    if len(linear) != n * n or any(i not in linear for i in range(n * n)):
        raise R23SchemaError("R22 Ising linear coefficient coverage is invalid")
    spins = frozenset(tuple(int(v) for v in item["ising_global_minimum_spin_states"][k]) for k in range(len(item["ising_global_minimum_spin_states"])))
    bits = frozenset(tuple(int(v) for v in b) for b in item["qubo_global_minimum_bitstrings"])
    # R22 stores the compact conversion result; the frozen R21 snapshot supplies
    # route-metric metadata without changing the authoritative Ising coefficients.
    meta = item.get("input_instance_metadata", {})
    customer_ids = tuple(meta.get("customer_ids", []))
    depot_id = meta.get("depot_id")
    r21_report = json.loads((Path(item["r21_artifact_id"]) / "validation_results.json").read_text(encoding="utf-8")) if item.get("r21_artifact_id") else {}
    r21_items = [x for x in r21_report.get("instances", []) if x.get("instance_id") == instance_id]
    snap = r21_items[0].get("input_snapshot", {}) if len(r21_items) == 1 else {}
    if not customer_ids or depot_id is None:
        raise R23SchemaError("R22 input instance metadata is incomplete")
    # The formal R22 result carries decoded routes; retain the exact R21 routes in payload lineage.
    routes = frozenset(tuple(r) for r in item.get("decoded_ising_routes", []))
    if not routes:
        routes = frozenset(tuple(r) for r in item.get("decoded_ising_routes", []))
    node_ids = (depot_id, *customer_ids)
    raw_matrix = snap.get("normalized_travel_time_matrix", {})
    normalized_matrix = {
        origin: {destination: float(raw_matrix[str(origin)][str(destination)]) if str(origin) in raw_matrix and str(destination) in raw_matrix[str(origin)] else float(raw_matrix[origin][destination]) for destination in node_ids}
        for origin in node_ids
    }
    return R23Input(
        instance_id=instance_id, n=n, customer_ids=customer_ids, depot_id=depot_id,
        ising_constant=float(item["ising_constant"]), ising_linear=linear, ising_quadratic=quadratic,
        ising_coefficient_hash=str(item["ising_coefficient_hash"]), qubo_coefficient_hash=str(item["qubo_coefficient_hash"]),
        lambda_value=float(item["lambda"]), bound=float(item["B"]), exact_optimal_bitstrings=bits,
        exact_optimal_spin_states=spins, exact_optimal_routes=routes,
        normalized_matrix=normalized_matrix, payload=item,
    )


def config_payload(config: R23Config, input_data: R23Input, *, instance_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": R23_SCHEMA_VERSION, "scope": R23_SCOPE, "instance_id": instance_id or input_data.instance_id,
        "n": input_data.n, "n_logical": input_data.n_logical, "p": config.p, "optimizer": config.optimizer,
        "maxiter": config.maxiter, "max_evaluations": config.max_evaluations, "initial_parameter": config.initial_parameter,
        "seed": config.seed, "repetition": config.repetition, "expectation_mode": config.expectation_mode,
        "backend_method": config.backend_method, "device": config.device, "optimization_level": config.optimization_level,
        "max_logical_qubits": config.max_logical_qubits, "max_p": config.max_p, "wall_time_seconds": config.wall_time_seconds,
        "memory_limit_gib": config.memory_limit_gib, "probability_threshold": config.probability_threshold,
        "r22_ising_coefficient_hash": input_data.ising_coefficient_hash, "r22_qubo_coefficient_hash": input_data.qubo_coefficient_hash,
        "r22_scope": R23_SCOPE,
    }
