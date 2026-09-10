"""Schema and deterministic hashing for the scoped R21 input contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from traffic_simulation.r20_route_ordering.core import QuboCoefficients, QuboInputError, _validated_customers

R21_SCHEMA_VERSION = "r21-reduced-qubo-validation-v1"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class R21SchemaError(ValueError):
    """Malformed reduced-R21 input."""

    reason_code = "INPUT_CONTRACT_FAILURE"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _float(value: Any, name: str, *, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise R21SchemaError(f"{name} must be numeric") from exc
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise R21SchemaError(f"{name} must be finite and non-negative")
    return result


def _commit(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _COMMIT_RE.fullmatch(value):
        raise R21SchemaError(f"{name} must be a 40-character lowercase commit hash")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise R21SchemaError(f"{name} must be a 64-character lowercase SHA-256 hash")
    return value


def _coefficients_payload(coefficients: QuboCoefficients) -> dict[str, Any]:
    return {
        "constant": float(coefficients.constant),
        "linear": {str(k): float(v) for k, v in sorted(coefficients.linear.items())},
        "quadratic": {f"{a},{b}": float(v) for (a, b), v in sorted(coefficients.quadratic.items())},
        "n_logical": coefficients.n_logical,
    }


def coefficient_hash(coefficients: QuboCoefficients) -> str:
    return hashlib.sha256(canonical_json(_coefficients_payload(coefficients))).hexdigest()


def coefficients_to_payload(coefficients: QuboCoefficients) -> dict[str, Any]:
    return _coefficients_payload(coefficients)


def coefficients_from_payload(value: Any) -> QuboCoefficients:
    if not isinstance(value, Mapping):
        raise R21SchemaError("qubo_coefficients must be an object")
    try:
        constant = _float(value["constant"], "qubo_coefficients.constant")
        n_logical = int(value["n_logical"])
        linear_raw = value["linear"]
        quadratic_raw = value["quadratic"]
    except (KeyError, TypeError, ValueError) as exc:
        raise R21SchemaError("qubo_coefficients is incomplete") from exc
    if not isinstance(linear_raw, Mapping) or not isinstance(quadratic_raw, Mapping):
        raise R21SchemaError("linear and quadratic coefficients must be objects")
    try:
        linear = {int(k): _float(v, f"linear[{k}]") for k, v in linear_raw.items()}
        quadratic: dict[tuple[int, int], float] = {}
        for key, val in quadratic_raw.items():
            if isinstance(key, str):
                a, b = (int(x) for x in key.split(","))
            elif isinstance(key, (list, tuple)) and len(key) == 2:
                a, b = int(key[0]), int(key[1])
            else:
                raise ValueError(key)
            if a >= b:
                raise ValueError("quadratic keys must be canonical")
            quadratic[(a, b)] = _float(val, f"quadratic[{key}]")
    except (TypeError, ValueError) as exc:
        raise R21SchemaError("invalid QUBO coefficient key/value") from exc
    return QuboCoefficients(constant, linear, quadratic, n_logical)


@dataclass(frozen=True)
class ReducedR21Input:
    """Validated, JSON-compatible reduced R21 input."""

    payload: Mapping[str, Any]
    coefficients: QuboCoefficients

    @property
    def instance_id(self) -> str:
        return str(self.payload["instance_id"])


def load_input(value: Mapping[str, Any]) -> ReducedR21Input:
    if not isinstance(value, Mapping):
        raise R21SchemaError("input must be an object")
    required = (
        "schema_version", "instance_id", "depot_id", "customer_ids", "n_customers",
        "variable_ordering", "raw_travel_time_matrix", "normalized_travel_time_matrix",
        "tau_max", "complete_reachability", "routing_source", "r20_formulation_source_commit",
        "r20_gate_commit", "qubo_coefficients", "coefficient_hash", "lambda", "bound_type",
        "B", "applied_margin", "numerical_tolerance", "classical_reference_config",
    )
    missing = [name for name in required if name not in value]
    if missing:
        raise R21SchemaError(f"missing mandatory fields: {', '.join(missing)}")
    if value["schema_version"] != R21_SCHEMA_VERSION:
        raise R21SchemaError("schema/version mismatch")
    depot = value["depot_id"]
    customers = value["customer_ids"]
    try:
        customers = tuple(_validated_customers(depot, customers))
    except QuboInputError as exc:
        raise R21SchemaError(str(exc)) from exc
    if value["n_customers"] != len(customers):
        raise R21SchemaError("n_customers does not match customer_ids")
    if value["variable_ordering"] != "row-major:index=(i-1)*n+(t-1)":
        raise R21SchemaError("unsupported variable_ordering")
    if value["complete_reachability"] is not True:
        raise R21SchemaError("complete_reachability must be true for reduced R21")
    _commit(value["r20_formulation_source_commit"], "r20_formulation_source_commit")
    _commit(value["r20_gate_commit"], "r20_gate_commit")
    routing_source = value["routing_source"]
    if not isinstance(routing_source, Mapping) or not routing_source.get("artifact_id"):
        raise R21SchemaError("routing_source.artifact_id is required")
    _sha256(routing_source.get("artifact_sha256"), "routing_source.artifact_sha256")
    lam = _float(value["lambda"], "lambda")
    bound = _float(value["B"], "B")
    _float(value["tau_max"], "tau_max")
    _float(value["applied_margin"], "applied_margin")
    if not isinstance(value["numerical_tolerance"], Mapping):
        raise R21SchemaError("numerical_tolerance must be an object")
    coefficients = coefficients_from_payload(value["qubo_coefficients"])
    n_logical = len(customers) ** 2
    if coefficients.n_logical != n_logical:
        raise R21SchemaError("QUBO logical-variable count mismatch")
    if set(coefficients.linear) != set(range(n_logical)):
        raise R21SchemaError("QUBO linear coefficient indices are incomplete")
    if value["coefficient_hash"] != coefficient_hash(coefficients):
        raise R21SchemaError("QUBO coefficient hash mismatch")
    # Keep the caller's mapping immutable from the validation layer's perspective.
    return ReducedR21Input(dict(value), coefficients)
