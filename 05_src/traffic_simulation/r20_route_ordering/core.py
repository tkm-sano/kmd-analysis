"""Exact reference and validation for the adopted R20 route-ordering QUBO.

This module deliberately contains no QAOA, Ising conversion, optimizer, or repair
logic.  The QUBO convention is the expanded scalar form in the R20 specification.
"""

from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class ExactEnumerationGuardError(RuntimeError):
    """Raised before an unsafe exponential enumeration is started."""


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


def _matrix_value(matrix: Mapping[Any, Any] | Sequence[Sequence[float]], i: Any, j: Any, ids: Sequence[Any]) -> float:
    if isinstance(matrix, Mapping):
        row = matrix[i]
        value = row[j] if isinstance(row, Mapping) else row[ids.index(j)]
    else:
        value = matrix[ids.index(i)][ids.index(j)]
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("travel-time matrix must contain finite non-negative values")
    return value


def normalize_travel_time_matrix(
    depot: Any,
    customer_ids: Sequence[Any],
    travel_time_matrix: Mapping[Any, Any] | Sequence[Sequence[float]],
) -> tuple[dict[Any, dict[Any, float]], float]:
    """Return a dense normalized matrix and τ_max for the supplied node order."""
    ids = [depot, *customer_ids]
    if len(set(ids)) != len(ids):
        raise ValueError("depot and customer IDs must be unique")
    values = {(i, j): _matrix_value(travel_time_matrix, i, j, ids) for i in ids for j in ids}
    tau_max = max((v for (i, j), v in values.items() if i != j), default=0.0)
    if tau_max <= 0:
        raise ValueError("τ_max must be positive for normalization")
    return ({i: {j: values[i, j] / tau_max for j in ids} for i in ids}, tau_max)


def encode_route(route: Sequence[Any], customer_ids: Sequence[Any]) -> tuple[int, ...]:
    """Encode a customer permutation in row-major x[i,t] order."""
    customers = tuple(customer_ids)
    if tuple(sorted(route, key=repr)) != tuple(sorted(customers, key=repr)) or len(route) != len(customers):
        raise ValueError("route must be a permutation of customer_ids")
    n = len(customers)
    bits = [0] * (n * n)
    for position, customer in enumerate(route):
        bits[customers.index(customer) * n + position] = 1
    return tuple(bits)


def decode_bitstring(bitstring: Sequence[Any], n: int, customer_ids: Sequence[Any]) -> tuple[tuple[Any, ...] | None, ValidationStatus]:
    result = validate_bitstring(bitstring, n, customer_ids)
    return result.route, result.status


def validate_bitstring(bitstring: Sequence[Any], n: int, customer_ids: Sequence[Any]) -> BitstringValidation:
    customers = tuple(customer_ids)
    if n != len(customers) or len(bitstring) != n * n:
        return BitstringValidation(ValidationStatus.INVALID_BITSTRING, None, None, False, False, False, None, "length mismatch")
    if any(type(value) is not int or value not in (0, 1) for value in bitstring):
        return BitstringValidation(ValidationStatus.INVALID_BITSTRING, None, None, False, False, False, None, "non-binary value")
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
        route = tuple(customers[next(i for i in range(n) if rows[i][t] == 1)] for t in range(n))
        if len(route) != n or set(route) != set(customers):
            return BitstringValidation(ValidationStatus.DECODE_FAILURE, customer_penalty, position_penalty, customer_once, position_once, False, None, "decoded customer set mismatch")
        return BitstringValidation(ValidationStatus.VALID, customer_penalty, position_penalty, customer_once, position_once, True, route)
    return BitstringValidation(status, customer_penalty, position_penalty, customer_once, position_once, False, None, "one-hot constraint violation")


def route_travel_time(depot: Any, route: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]]) -> float:
    nodes = (depot, *route, depot)
    return sum(matrix[a][b] for a, b in zip(nodes, nodes[1:]))


def enumerate_routes(depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]]) -> dict[str, Any]:
    start = time.perf_counter()
    records = []
    for permutation in itertools.permutations(customer_ids):
        route = (depot, *permutation, depot)
        records.append({"customer_permutation": list(permutation), "route": list(route), "travel_time": route_travel_time(depot, permutation, matrix), "valid": True})
    best = min(record["travel_time"] for record in records)
    optimal = [record for record in records if math.isclose(record["travel_time"], best, rel_tol=0.0, abs_tol=1e-12)]
    return {"best_route": optimal[0]["route"], "best_route_travel_time": best, "optimal_routes": [r["route"] for r in optimal], "evaluated_permutations": len(records), "records": records, "metadata": {"method": "all_customer_permutations", "expected_permutations": math.factorial(len(customer_ids)), "elapsed_seconds": time.perf_counter() - start}}


def _components(bits: Sequence[int], depot: Any, customers: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]], lam: float) -> dict[str, float | int]:
    n = len(customers)
    rows = [bits[i * n:(i + 1) * n] for i in range(n)]
    columns = [[rows[i][t] for i in range(n)] for t in range(n)]
    customer_penalty = sum((1 - sum(row)) ** 2 for row in rows)
    position_penalty = sum((1 - sum(column)) ** 2 for column in columns)
    travel = 0.0
    travel += sum(matrix[depot][customers[i]] * rows[i][0] for i in range(n))
    travel += sum(matrix[customers[i]][customers[j]] * rows[i][t] * rows[j][t + 1] for t in range(n - 1) for i in range(n) for j in range(n))
    travel += sum(matrix[customers[i]][depot] * rows[i][n - 1] for i in range(n))
    return {"travel_objective": travel, "customer_penalty": customer_penalty, "position_penalty": position_penalty, "total_penalty": customer_penalty + position_penalty, "qubo_energy": travel + lam * (customer_penalty + position_penalty)}


def enumerate_qubo_states(depot: Any, customer_ids: Sequence[Any], matrix: Mapping[Any, Mapping[Any, float]], lam: float, *, max_logical_variables: int = 16, max_states: int = 1_000_000, allow_unsafe: bool = False) -> dict[str, Any]:
    n = len(customer_ids)
    logical = n * n
    states = 2 ** logical
    if not allow_unsafe and (logical > max_logical_variables or states > max_states):
        raise ExactEnumerationGuardError(f"exact enumeration guarded: n_logical={logical}, states={states}; explicit allow_unsafe required")
    start = time.perf_counter()
    records = []
    for integer in range(states):
        bits = tuple((integer >> (logical - 1 - k)) & 1 for k in range(logical))
        components = _components(bits, depot, customer_ids, matrix, lam)
        validation = validate_bitstring(bits, n, customer_ids)
        records.append({"bitstring": list(bits), **components, "feasibility": validation.status == ValidationStatus.VALID, "validation_status": validation.status.value, "decode_success": validation.decode_success, "decoded_customer_sequence": list(validation.route) if validation.route else None, "decoded_route": [depot, *validation.route, depot] if validation.route else None})
    global_energy = min(r["qubo_energy"] for r in records)
    global_minima = [r for r in records if math.isclose(r["qubo_energy"], global_energy, rel_tol=0.0, abs_tol=1e-12)]
    feasible = [r for r in records if r["feasibility"]]
    infeasible = [r for r in records if not r["feasibility"]]
    feasible_energy = min(r["qubo_energy"] for r in feasible) if feasible else None
    infeasible_energy = min(r["qubo_energy"] for r in infeasible) if infeasible else None
    return {"lambda": lam, "n": n, "n_logical": logical, "state_count": states, "records": records, "global_minimum_energy": global_energy, "global_minimum_bitstrings": [r["bitstring"] for r in global_minima], "global_minimum_all_feasible": all(r["feasibility"] for r in global_minima), "best_feasible_energy": feasible_energy, "best_feasible_states": [r for r in feasible if math.isclose(r["qubo_energy"], feasible_energy, abs_tol=1e-12, rel_tol=0.0)] if feasible else [], "best_infeasible_energy": infeasible_energy, "best_infeasible_states": [r for r in infeasible if math.isclose(r["qubo_energy"], infeasible_energy, abs_tol=1e-12, rel_tol=0.0)] if infeasible else [], "metadata": {"method": "exhaustive_binary_assignment_enumeration", "elapsed_seconds": time.perf_counter() - start, "repair": "not_used"}}


def penalty_consistency(bits: Sequence[int], n: int) -> tuple[bool, bool]:
    rows = [bits[i * n:(i + 1) * n] for i in range(n)]
    columns = [[rows[i][t] for i in range(n)] for t in range(n)]
    customer_direct = sum((1 - sum(row)) ** 2 for row in rows)
    position_direct = sum((1 - sum(column)) ** 2 for column in columns)
    customer_expanded = n - sum(bits) + 2 * sum(sum(row) * (sum(row) - 1) // 2 for row in rows)
    position_expanded = n - sum(bits) + 2 * sum(sum(column) * (sum(column) - 1) // 2 for column in columns)
    return customer_direct == customer_expanded, position_direct == position_expanded
