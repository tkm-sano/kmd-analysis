"""Validated R23 post-processing candidate: indexed amplitudes, no probability dict."""
from __future__ import annotations
import itertools
import math
from typing import Any
import numpy as np
from traffic_simulation.r20_route_ordering.core import encode_route, route_travel_time

def feasible_basis_indices(customer_ids, n):
    return tuple(sum(bit << i for i, bit in enumerate(encode_route(route, customer_ids)))
                 for route in itertools.permutations(customer_ids))

def indexed_probability_metrics(statevector, customer_ids, exact_optimal_bitstrings, n, normalized_matrix=None, depot_id=None):
    """Return raw-denominator metrics using only feasible basis indices."""
    amplitudes = np.asarray(statevector.data if hasattr(statevector, "data") else statevector)
    indices = np.asarray(feasible_basis_indices(customer_ids, n), dtype=np.int64)
    probabilities = np.abs(amplitudes[indices]) ** 2
    optimal = np.asarray([i for i in indices if tuple((int(i) >> q) & 1 for q in range(n*n)) in exact_optimal_bitstrings], dtype=np.int64)
    total = float(np.vdot(amplitudes, amplitudes).real)
    feasible = float(probabilities.sum(dtype=np.float64))
    optimal_mass = float(np.abs(amplitudes[optimal]) @ np.abs(amplitudes[optimal]))
    return {"probability_total": total, "P_feasible_exact": feasible, "P_opt": optimal_mass,
            "invalid_probability_mass": total-feasible, "feasible_indices": indices.tolist(),
            "optimal_indices": optimal.tolist(), "renormalized": False,
            "denominator": "raw_full_state_probability_mass"}
