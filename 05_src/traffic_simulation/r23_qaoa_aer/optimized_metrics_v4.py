"""Validated R23 post-processing candidate: indexed amplitudes, no probability dict."""
from __future__ import annotations
import itertools
from collections.abc import Collection, Sequence
from typing import Any
import numpy as np
from traffic_simulation.r20_route_ordering.core import encode_route, route_travel_time

class V4InputError(ValueError):
    """Raised when the indexed V4 helper receives an invalid contract input."""


def _validate_contract_inputs(statevector: Any, customer_ids: Sequence[Any],
                              exact_optimal_bitstrings: Collection[Sequence[int]],
                              n: int) -> np.ndarray:
    if type(n) is not int or n <= 0:
        raise V4InputError("n must be a positive integer")
    if not isinstance(customer_ids, Sequence) or isinstance(customer_ids, (str, bytes)):
        raise V4InputError("customer_ids must be a sequence")
    customers = tuple(customer_ids)
    if len(customers) != n:
        raise V4InputError("n must equal the number of customer IDs")
    try:
        if len(set(customers)) != n:
            raise V4InputError("customer_ids must be unique")
    except TypeError as exc:
        raise V4InputError("customer IDs must be hashable") from exc
    raw = statevector.data if hasattr(statevector, "data") else statevector
    try:
        amplitudes = np.asarray(raw)
    except (TypeError, ValueError) as exc:
        raise V4InputError("statevector must be a one-dimensional numeric array") from exc
    if amplitudes.ndim != 1:
        raise V4InputError("statevector must be one-dimensional")
    if amplitudes.dtype.kind not in "fc":
        raise V4InputError("statevector dtype must be a supported real or complex floating type")
    expected_dimension = 2 ** (n * n)
    if amplitudes.size != expected_dimension:
        raise V4InputError(f"statevector length must be {expected_dimension} for n={n}")
    if not np.all(np.isfinite(amplitudes)):
        raise V4InputError("statevector must not contain NaN or inf")
    if not isinstance(exact_optimal_bitstrings, Collection) or isinstance(exact_optimal_bitstrings, (str, bytes)) or not exact_optimal_bitstrings:
        raise V4InputError("exact_optimal_bitstrings must be non-empty")
    normalized = []
    for bits in exact_optimal_bitstrings:
        if not isinstance(bits, Sequence) or isinstance(bits, (str, bytes)) or len(bits) != n * n:
            raise V4InputError("each optimal bitstring must have dimension n*n")
        if any(type(bit) is not int or bit not in (0, 1) for bit in bits):
            raise V4InputError("optimal bitstrings must contain only binary integers")
        normalized.append(tuple(bits))
    if len(set(normalized)) != len(normalized):
        raise V4InputError("exact_optimal_bitstrings must be unique")
    valid_indices = set(feasible_basis_indices(customers, n))
    for bits in normalized:
        index = sum(bit << i for i, bit in enumerate(bits))
        if index not in valid_indices:
            raise V4InputError("each optimal bitstring must encode a feasible route")
    return amplitudes


def feasible_basis_indices(customer_ids, n):
    if type(n) is not int or n <= 0 or len(tuple(customer_ids)) != n:
        raise V4InputError("n must equal the number of customer IDs")
    indices = tuple(sorted(
        (sum(bit << i for i, bit in enumerate(encode_route(route, customer_ids)))
         for route in itertools.permutations(customer_ids)),
        key=lambda index: format(index, f"0{n * n}b"),
    ))
    if len(set(indices)) != len(indices):
        raise V4InputError("feasible basis indices must be unique")
    return indices

def indexed_probability_metrics(statevector, customer_ids, exact_optimal_bitstrings, n, normalized_matrix=None, depot_id=None):
    """Return raw-denominator metrics using only feasible basis indices."""
    amplitudes = _validate_contract_inputs(statevector, customer_ids, exact_optimal_bitstrings, n)
    indices = np.asarray(feasible_basis_indices(customer_ids, n), dtype=np.int64)
    probabilities = np.abs(amplitudes[indices]) ** 2
    optimal_bits = {tuple(bits) for bits in exact_optimal_bitstrings}
    optimal = np.asarray([i for i in indices if tuple((int(i) >> q) & 1 for q in range(n*n)) in optimal_bits], dtype=np.int64)
    total = float(np.vdot(amplitudes, amplitudes).real)
    feasible = float(probabilities.sum(dtype=np.float64))
    optimal_mass = float(np.abs(amplitudes[optimal]) @ np.abs(amplitudes[optimal]))
    return {"probability_total": total, "P_feasible_exact": feasible, "P_opt": optimal_mass,
            "invalid_probability_mass": total-feasible, "feasible_indices": indices.tolist(),
            "optimal_indices": optimal.tolist(), "renormalized": False,
            "denominator": "raw_full_state_probability_mass"}
