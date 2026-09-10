"""Reduced R21 validation orchestration, without QAOA or Ising execution."""

from __future__ import annotations

import math
import time
from typing import Any, Mapping

from traffic_simulation.r20_route_ordering.core import (
    ENERGY_ABS_TOLERANCE,
    ExactEnumerationGuardError,
    QuboInputError,
    build_expanded_qubo,
    encode_route,
    energy_equal,
    enumerate_qubo_states,
    enumerate_routes,
    normalize_travel_time_matrix,
)

from .schema import R21_SCHEMA_VERSION, ReducedR21Input, R21SchemaError, coefficient_hash, load_input

FAILURE_REASONS = (
    "INPUT_CONTRACT_FAILURE", "PROVENANCE_FAILURE", "LAMBDA_BOUND_FAILURE",
    "INFEASIBLE_GLOBAL_MINIMUM", "QUBO_ROUTE_OBJECTIVE_MISMATCH", "OPTIMAL_ROUTE_SET_MISMATCH",
    "DIRECT_EXPANDED_MISMATCH", "DECODE_FAILURE", "NORMALIZATION_MISMATCH",
    "EXACT_ENUMERATION_GUARD", "NUMERICAL_TOLERANCE_FAILURE", "NONDETERMINISTIC_RESULT",
)


class R21ValidationError(ValueError):
    """A validation input cannot be evaluated under the reduced R21 contract."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def _route_set(routes: list[list[Any]]) -> set[tuple[Any, ...]]:
    return {tuple(route[1:-1]) for route in routes}


def _coefficients_match(actual, expected) -> bool:
    if actual.n_logical != expected.n_logical or not energy_equal(actual.constant, expected.constant):
        return False
    if set(actual.linear) != set(expected.linear) or set(actual.quadratic) != set(expected.quadratic):
        return False
    return all(energy_equal(actual.linear[k], expected.linear[k]) for k in actual.linear) and all(
        energy_equal(actual.quadratic[k], expected.quadratic[k]) for k in actual.quadratic
    )


def _input_failure(exc: Exception) -> R21ValidationError:
    reason = getattr(exc, "reason_code", "INPUT_CONTRACT_FAILURE")
    return R21ValidationError(reason, str(exc))


def validate_reduced_r21(payload: Mapping[str, Any], *, max_logical_variables: int = 16, max_states: int = 1_000_000) -> dict[str, Any]:
    """Validate one reduced-R21 input in memory.

    This function is an implementation runner. Calling it does not change the
    repository R21 status or create an authoritative stage artifact.
    """
    started = time.perf_counter()
    try:
        input_data: ReducedR21Input = load_input(payload)
    except (R21SchemaError, TypeError, ValueError) as exc:
        raise _input_failure(exc) from exc
    p = input_data.payload
    customers = tuple(p["customer_ids"])
    depot = p["depot_id"]
    lam = float(p["lambda"])
    bound = float(p["B"])
    if not math.isfinite(lam) or not math.isfinite(bound) or lam <= bound:
        raise R21ValidationError("LAMBDA_BOUND_FAILURE", "lambda must be finite and strictly greater than B")
    try:
        raw_reference = enumerate_routes(depot, customers, p["raw_travel_time_matrix"])
        normalized, tau_max = normalize_travel_time_matrix(depot, customers, p["raw_travel_time_matrix"])
        normalized_reference = enumerate_routes(depot, customers, normalized)
        if not energy_equal(tau_max, float(p["tau_max"])):
            raise R21ValidationError("INPUT_CONTRACT_FAILURE", "tau_max does not match raw matrix")
        supplied_normalized = p["normalized_travel_time_matrix"]
        supplied_reference = enumerate_routes(depot, customers, supplied_normalized)
        if _route_set(supplied_reference["optimal_routes"]) != _route_set(normalized_reference["optimal_routes"]):
            raise R21ValidationError("NORMALIZATION_MISMATCH", "supplied normalized matrix changes route optimum")
        expected_coefficients = build_expanded_qubo(depot, customers, supplied_normalized, lam)
        if not _coefficients_match(input_data.coefficients, expected_coefficients):
            raise R21ValidationError("INPUT_CONTRACT_FAILURE", "supplied QUBO coefficients differ from R20 builder")
        qubo = enumerate_qubo_states(depot, customers, supplied_normalized, lam, max_logical_variables=max_logical_variables, max_states=max_states)
    except ExactEnumerationGuardError as exc:
        raise R21ValidationError("EXACT_ENUMERATION_GUARD", str(exc)) from exc
    except QuboInputError as exc:
        raise R21ValidationError("INPUT_CONTRACT_FAILURE", str(exc)) from exc
    except R21ValidationError:
        raise

    classical_routes = _route_set(normalized_reference["optimal_routes"])
    qubo_routes = {tuple(r["decoded_customer_sequence"]) for r in qubo["best_feasible_states"]}
    v1 = qubo["all_global_minima_feasible"]
    v2 = all(energy_equal(float(r["travel_objective"]), normalized_reference["best_route_travel_time"]) for r in qubo["best_feasible_states"])
    v3 = qubo_routes == classical_routes
    v4 = qubo["direct_expanded_mismatch_count"] == 0 and qubo["direct_expanded_max_abs_difference"] <= ENERGY_ABS_TOLERANCE
    v5 = all(tuple(r["bitstring"]) == encode_route(r["decoded_customer_sequence"], customers) for r in qubo["best_feasible_states"])
    v6 = True
    v7 = math.isfinite(lam) and lam > bound
    v8 = _route_set(raw_reference["optimal_routes"]) == _route_set(normalized_reference["optimal_routes"])
    checks = {"V1_feasibility": v1, "V2_objective_equivalence": v2, "V3_route_set_equivalence": v3, "V4_direct_expanded_consistency": v4, "V5_decode_reencode": v5, "V6_input_provenance_integrity": v6, "V7_lambda_validity": v7, "V8_normalization_consistency": v8}
    reasons = []
    if not v1: reasons.append("INFEASIBLE_GLOBAL_MINIMUM")
    if not v2: reasons.append("QUBO_ROUTE_OBJECTIVE_MISMATCH")
    if not v3: reasons.append("OPTIMAL_ROUTE_SET_MISMATCH")
    if not v4: reasons.append("DIRECT_EXPANDED_MISMATCH")
    if not v5: reasons.append("DECODE_FAILURE")
    if not v8: reasons.append("NORMALIZATION_MISMATCH")
    return {
        "schema_version": R21_SCHEMA_VERSION,
        "r21_stage": "R21_REDUCED_QUBO_VALIDATION",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "instance_id": input_data.instance_id,
        "depot_id": depot,
        "customer_ids": list(customers),
        "n": len(customers),
        "n_logical": qubo["n_logical"],
        "state_count": qubo["state_count"],
        "permutation_count": raw_reference["evaluated_permutations"],
        "lambda": lam,
        "B": bound,
        "bound_type": p["bound_type"],
        "lambda_minus_B": lam - bound,
        "classical_raw_optimum": raw_reference["best_route_travel_time"],
        "classical_normalized_optimum": normalized_reference["best_route_travel_time"],
        "classical_raw_optimal_routes": raw_reference["optimal_routes"],
        "classical_optimal_routes": normalized_reference["optimal_routes"],
        "qubo_global_minimum_energy": qubo["global_minimum_energy"],
        "qubo_global_minimum_count": len(qubo["global_minimum_bitstrings"]),
        "qubo_global_minimum_bitstrings": qubo["global_minimum_bitstrings"],
        "qubo_feasible_global_minimum_count": sum(1 for r in qubo["global_minimum_bitstrings"] if next(record for record in qubo["records"] if record["bitstring"] == r)["feasibility"]),
        "all_global_minima_feasible": qubo["all_global_minima_feasible"],
        "best_feasible_energy": qubo["best_feasible_energy"],
        "best_infeasible_energy": qubo["best_infeasible_energy"],
        "energy_gap_infeasible_minus_feasible": qubo["best_infeasible_energy"] - qubo["best_feasible_energy"],
        "direct_expanded_max_abs_difference": qubo["direct_expanded_max_abs_difference"],
        "direct_expanded_mismatch_count": qubo["direct_expanded_mismatch_count"],
        "qubo_optimal_routes": [list(route) for route in sorted(qubo_routes, key=repr)],
        "coefficient_hash": coefficient_hash(input_data.coefficients),
        "checks": checks,
        "failure_reasons": reasons,
        "metadata": {"runtime_seconds": time.perf_counter() - started, "implementation_smoke_only": True, "formal_r21_execution": False},
    }
