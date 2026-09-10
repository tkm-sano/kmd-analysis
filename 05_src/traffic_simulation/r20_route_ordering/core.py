"""Exact, non-QAOA validation for the adopted R20 route-ordering QUBO."""

from __future__ import annotations

import itertools
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

ENERGY_ABS_TOLERANCE = 1e-12


class ExactEnumerationGuardError(RuntimeError):
    """Raised before an unsafe exponential enumeration is started."""


class QuboInputError(ValueError):
    """Raised for invalid formulation inputs, not sampled bitstrings."""


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID_CUSTOMER_ONCE = "INVALID_CUSTOMER_ONCE"
    INVALID_POSITION_ONCE = "INVALID_POSITION_ONCE"
    INVALID_BOTH = "INVALID_BOTH"
    INVALID_BITSTRING = "INVALID_BITSTRING"
    DECODE_FAILURE = "DECODE_FAILURE"


@dataclass(frozen=True)
class BitstringValidation:
    status: ValidationStatus
    customer_penalty: int | None
    position_penalty: int | None
    customer_once: bool
    position_once: bool
    decode_success: bool
    route: tuple[Any, ...] | None
    reason: str | None = None


@dataclass(frozen=True)
class QuboCoefficients:
    """Canonical coefficients for E=c+sum(h*x)+sum(Q*x*x)."""

    constant: float
    linear: dict[int, float]
    quadratic: dict[tuple[int, int], float]
    n_logical: int


def energy_equal(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=ENERGY_ABS_TOLERANCE)


def _validated_customers(depot: Any, customer_ids: Sequence[Any]) -> tuple[Any, ...]:
    if not isinstance(customer_ids, Sequence) or isinstance(customer_ids, (str, bytes)):
        raise QuboInputError("customer_ids must be a sequence")
    customers = tuple(customer_ids)
    try:
        customer_set = set(customers)
    except TypeError as exc:
        raise QuboInputError("customer IDs must be hashable") from exc
    if len(customer_set) != len(customers):
        raise QuboInputError("customer IDs must be unique")
    if depot in customer_set:
        raise QuboInputError("depot must not appear in customer IDs")
    if not customers:
        raise QuboInputError("at least one customer is required")
    return customers


def _validate_lambda(lam: float) -> float:
    try:
        value = float(lam)
    except (TypeError, ValueError) as exc:
        raise QuboInputError("lambda must be a finite non-negative number") from exc
    if not math.isfinite(value) or value < 0:
        raise QuboInputError("lambda must be a finite non-negative number")
    return value


def _matrix_value(matrix: Mapping[Any, Any] | Sequence[Sequence[float]], i: Any, j: Any, ids: Sequence[Any]) -> float:
    try:
        if isinstance(matrix, Mapping):
            row = matrix[i]
            value = row[j] if isinstance(row, Mapping) else row[ids.index(j)]
        else:
            value = matrix[ids.index(i)][ids.index(j)]
        value = float(value)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise QuboInputError(f"missing or invalid travel time for directed edge {i!r}->{j!r}") from exc
    if not math.isfinite(value) or value < 0:
        raise QuboInputError("travel-time matrix must contain finite non-negative off-diagonal values")
    return value


def canonical_travel_time_matrix(depot: Any, customer_ids: Sequence[Any], travel_time_matrix: Mapping[Any, Any] | Sequence[Sequence[float]]) -> dict[Any, dict[Any, float]]:
    """Validate all directed non-self edges; self-loop entries are never read."""
    customers = _validated_customers(depot, customer_ids)
    ids = (depot, *customers)
    return {i: {j: 0.0 if i == j else _matrix_value(travel_time_matrix, i, j, ids) for j in ids} for i in ids}


def normalize_travel_time_matrix(depot: Any, customer_ids: Sequence[Any], travel_time_matrix: Mapping[Any, Any] | Sequence[Sequence[float]]) -> tuple[dict[Any, dict[Any, float]], float]:
    """Return a new normalized matrix and positive off-diagonal tau_max."""
    dense = canonical_travel_time_matrix(depot, customer_ids, travel_time_matrix)
    ids = tuple(dense)
    tau_max = max(dense[i][j] for i in ids for j in ids if i != j)
    if tau_max <= 0:
        raise QuboInputError("tau_max must be positive for normalization")
    return ({i: {j: 0.0 if i == j else dense[i][j] / tau_max for j in ids} for i in ids}, tau_max)


def encode_route(route: Sequence[Any], customer_ids: Sequence[Any]) -> tuple[int, ...]:
    """Encode a customer permutation in row-major x[i,t] order."""
    customers = _validated_customers(object(), customer_ids)
    if not isinstance(route, Sequence) or isinstance(route, (str, bytes)):
        raise QuboInputError("route must be a sequence")
    if len(route) != len(customers) or set(route) != set(customers):
        raise QuboInputError("route must be a permutation of customer_ids")
    n = len(customers)
    bits = [0] * (n * n)
    for position, customer in enumerate(route):
        bits[customers.index(customer) * n + position] = 1
    return tuple(bits)


def decode_bitstring(bitstring: Any, n: int, customer_ids: Sequence[Any]) -> tuple[tuple[Any, ...] | None, ValidationStatus]:
    result = validate_bitstring(bitstring, n, customer_ids)
    return result.route, result.status


def validate_bitstring(bitstring: Any, n: int, customer_ids: Sequence[Any]) -> BitstringValidation:
    """Classify sampled data; duplicate IDs are a formulation input error."""
    customers = _validated_customers(object(), customer_ids)
    invalid = lambda reason: BitstringValidation(ValidationStatus.INVALID_BITSTRING, None, None, False, False, False, None, reason)
    if type(n) is not int or n <= 0 or n != len(customers):
        return invalid("n/customer mismatch")
    if not isinstance(bitstring, Sequence) or isinstance(bitstring, (str, bytes)):
        return invalid("not a bit sequence")
    if len(bitstring) != n * n:
        return invalid("length mismatch")
    if any(type(value) is not int or value not in (0, 1) for value in bitstring):
        return invalid("non-binary value")
    rows = [list(bitstring[i * n:(i + 1) * n]) for i in range(n)]
    columns = [[rows[i][t] for i in range(n)] for t in range(n)]
    customer_penalty = sum((1 - sum(row)) ** 2 for row in rows)
    position_penalty = sum((1 - sum(column)) ** 2 for column in columns)
    customer_once = all(sum(row) == 1 for row in rows)
    position_once = all(sum(column) == 1 for column in columns)
    if not customer_once and not position_once:
        status = ValidationStatus.INVALID_BOTH
    elif not customer_once:
        status = ValidationStatus.INVALID_CUSTOMER_ONCE
    elif not position_once:
        status = ValidationStatus.INVALID_POSITION_ONCE
    else:
        route = tuple(customers[next(i for i in range(n) if rows[i][t])] for t in range(n))
        if len(route) != n or len(set(route)) != n or set(route) != set(customers):
            return BitstringValidation(ValidationStatus.DECODE_FAILURE, customer_penalty, position_penalty, True, True, False, None, "decoded customer set mismatch")
        return BitstringValidation(ValidationStatus.VALID, customer_penalty, position_penalty, True, True, True, route)
    return BitstringValidation(status, customer_penalty, position_penalty, customer_once, position_once, False, None, "one-hot constraint violation")


def route_travel_time(depot: Any, route: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]]) -> float:
    nodes = (depot, *route, depot)
    return sum(matrix[a][b] for a, b in zip(nodes, nodes[1:]))


def enumerate_routes(depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Any] | Sequence[Sequence[float]]) -> dict[str, Any]:
    customers = _validated_customers(depot, customer_ids)
    dense = canonical_travel_time_matrix(depot, customers, matrix)
    start = time.perf_counter()
    records = []
    for permutation in itertools.permutations(customers):
        route = (depot, *permutation, depot)
        records.append({"customer_permutation": list(permutation), "route": list(route), "travel_time": route_travel_time(depot, permutation, dense), "valid": True})
    best = min(record["travel_time"] for record in records)
    optimal = [record for record in records if energy_equal(record["travel_time"], best)]
    return {"best_route": optimal[0]["route"], "best_route_travel_time": best, "optimal_routes": [r["route"] for r in optimal], "evaluated_permutations": len(records), "records": records, "metadata": {"method": "all_customer_permutations", "expected_permutations": math.factorial(len(customers)), "elapsed_seconds": time.perf_counter() - start}}


def evaluate_direct_qubo(bits: Sequence[int], depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]], lam: float) -> dict[str, float | int]:
    """Evaluate the authoritative direct squared formulation."""
    customers = _validated_customers(depot, customer_ids)
    lam = _validate_lambda(lam)
    dense = canonical_travel_time_matrix(depot, customers, matrix)
    if len(bits) != len(customers) ** 2 or any(type(value) is not int or value not in (0, 1) for value in bits):
        raise QuboInputError("direct QUBO evaluation requires the expected binary bitstring")
    return _evaluate_direct_prevalidated(bits, depot, customers, dense, lam)


def _evaluate_direct_prevalidated(bits: Sequence[int], depot: Any, customers: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]], lam: float) -> dict[str, float | int]:
    n = len(customers)
    rows = [bits[i * n:(i + 1) * n] for i in range(n)]
    columns = [[rows[i][t] for i in range(n)] for t in range(n)]
    customer_penalty = sum((1 - sum(row)) ** 2 for row in rows)
    position_penalty = sum((1 - sum(column)) ** 2 for column in columns)
    travel = sum(matrix[depot][customers[i]] * rows[i][0] for i in range(n))
    travel += sum(matrix[customers[i]][customers[j]] * rows[i][t] * rows[j][t + 1] for t in range(n - 1) for i in range(n) for j in range(n) if i != j)
    travel += sum(matrix[customers[i]][depot] * rows[i][n - 1] for i in range(n))
    return {"travel_objective": travel, "customer_penalty": customer_penalty, "position_penalty": position_penalty, "total_penalty": customer_penalty + position_penalty, "qubo_energy": travel + lam * (customer_penalty + position_penalty)}


def build_expanded_qubo(depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Any] | Sequence[Sequence[float]], lam: float) -> QuboCoefficients:
    """Build coefficients mathematically derived from the squared formulation."""
    customers = _validated_customers(depot, customer_ids)
    lam = _validate_lambda(lam)
    dense = canonical_travel_time_matrix(depot, customers, matrix)
    n = len(customers)
    linear = {index: -2.0 * lam for index in range(n * n)}
    quadratic: dict[tuple[int, int], float] = {}

    def add_pair(left: int, right: int, value: float) -> None:
        key = (left, right) if left < right else (right, left)
        quadratic[key] = quadratic.get(key, 0.0) + value

    for i in range(n):
        for t in range(n):
            for u in range(t + 1, n):
                add_pair(i * n + t, i * n + u, 2.0 * lam)
    for t in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                add_pair(i * n + t, j * n + t, 2.0 * lam)
    for i, customer in enumerate(customers):
        linear[i * n] += dense[depot][customer]
        linear[i * n + n - 1] += dense[customer][depot]
    for t in range(n - 1):
        for i, source in enumerate(customers):
            for j, target in enumerate(customers):
                if i != j:
                    add_pair(i * n + t, j * n + t + 1, dense[source][target])
    return QuboCoefficients(2.0 * n * lam, linear, quadratic, n * n)


def evaluate_expanded_qubo(bits: Sequence[int], coefficients: QuboCoefficients) -> float:
    if len(bits) != coefficients.n_logical or any(type(value) is not int or value not in (0, 1) for value in bits):
        raise QuboInputError("expanded QUBO evaluation requires the expected binary bitstring")
    energy = coefficients.constant
    energy += sum(value * bits[index] for index, value in coefficients.linear.items())
    energy += sum(value * bits[left] * bits[right] for (left, right), value in coefficients.quadratic.items())
    return energy


def enumerate_qubo_states(depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Any] | Sequence[Sequence[float]], lam: float, *, max_logical_variables: int = 16, max_states: int = 1_000_000, allow_unsafe: bool = False) -> dict[str, Any]:
    customers = _validated_customers(depot, customer_ids)
    lam = _validate_lambda(lam)
    dense = canonical_travel_time_matrix(depot, customers, matrix)
    logical = len(customers) ** 2
    states = 2 ** logical
    if not allow_unsafe and (logical > max_logical_variables or states > max_states):
        raise ExactEnumerationGuardError(f"exact enumeration guarded: n_logical={logical}, states={states}; explicit allow_unsafe required")
    coefficients = build_expanded_qubo(depot, customers, dense, lam)
    start = time.perf_counter()
    records = []
    for integer in range(states):
        bits = tuple((integer >> (logical - 1 - k)) & 1 for k in range(logical))
        direct = _evaluate_direct_prevalidated(bits, depot, customers, dense, lam)
        expanded = evaluate_expanded_qubo(bits, coefficients)
        validation = validate_bitstring(bits, len(customers), customers)
        records.append({"bitstring": list(bits), **direct, "expanded_qubo_energy": expanded, "direct_expanded_abs_difference": abs(float(direct["qubo_energy"]) - expanded), "feasibility": validation.status == ValidationStatus.VALID, "validation_status": validation.status.value, "decode_success": validation.decode_success, "decoded_customer_sequence": list(validation.route) if validation.route else None, "decoded_route": [depot, *validation.route, depot] if validation.route else None})
    global_energy = min(float(r["qubo_energy"]) for r in records)
    global_minima = [r for r in records if energy_equal(float(r["qubo_energy"]), global_energy)]
    feasible = [r for r in records if r["feasibility"]]
    infeasible = [r for r in records if not r["feasibility"]]
    feasible_energy = min(float(r["qubo_energy"]) for r in feasible)
    infeasible_energy = min(float(r["qubo_energy"]) for r in infeasible)
    return {"lambda": lam, "n": len(customers), "n_logical": logical, "state_count": states, "records": records, "global_minimum_energy": global_energy, "global_minimum_bitstrings": [r["bitstring"] for r in global_minima], "all_global_minima_feasible": bool(global_minima) and all(r["feasibility"] for r in global_minima), "best_feasible_energy": feasible_energy, "best_feasible_states": [r for r in feasible if energy_equal(float(r["qubo_energy"]), feasible_energy)], "best_infeasible_energy": infeasible_energy, "best_infeasible_states": [r for r in infeasible if energy_equal(float(r["qubo_energy"]), infeasible_energy)], "direct_expanded_max_abs_difference": max(float(r["direct_expanded_abs_difference"]) for r in records), "direct_expanded_mismatch_count": sum(not energy_equal(float(r["qubo_energy"]), float(r["expanded_qubo_energy"])) for r in records), "metadata": {"method": "exhaustive_binary_assignment_enumeration", "elapsed_seconds": time.perf_counter() - start, "energy_abs_tolerance": ENERGY_ABS_TOLERANCE, "repair": "not_used", "travel_self_loop_policy": "excluded"}}


def penalty_consistency(bits: Sequence[int], n: int) -> tuple[bool, bool]:
    rows = [bits[i * n:(i + 1) * n] for i in range(n)]
    columns = [[rows[i][t] for i in range(n)] for t in range(n)]
    customer_direct = sum((1 - sum(row)) ** 2 for row in rows)
    position_direct = sum((1 - sum(column)) ** 2 for column in columns)
    customer_expanded = n - sum(bits) + 2 * sum(sum(row) * (sum(row) - 1) // 2 for row in rows)
    position_expanded = n - sum(bits) + 2 * sum(sum(column) * (sum(column) - 1) // 2 for column in columns)
    return customer_direct == customer_expanded, position_direct == position_expanded
