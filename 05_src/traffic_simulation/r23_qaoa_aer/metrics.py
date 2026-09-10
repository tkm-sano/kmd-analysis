"""Probability and route metrics for exact statevector output."""

from __future__ import annotations

import math
from typing import Any, Mapping

from traffic_simulation.r20_route_ordering.core import ValidationStatus, route_travel_time, validate_bitstring

from .schema import R23Input


def qiskit_label_to_bits(label: str) -> tuple[int, ...]:
    if not isinstance(label, str) or any(c not in "01" for c in label):
        raise ValueError("statevector label must be a binary string")
    return tuple(int(c) for c in reversed(label))


def ising_energy(spins: tuple[int, ...], input_data: R23Input) -> float:
    energy = input_data.ising_constant
    energy += sum(input_data.ising_linear[i] * spins[i] for i in input_data.ising_linear)
    energy += sum(value * spins[a] * spins[b] for (a, b), value in input_data.ising_quadratic.items())
    return float(energy)


def energy_statistics(probabilities: Mapping[str, float], input_data: R23Input) -> dict[str, float]:
    values = []
    for label, probability in probabilities.items():
        bits = qiskit_label_to_bits(label)
        spins = tuple(1 if bit == 0 else -1 for bit in bits)
        values.append((float(probability), ising_energy(spins, input_data)))
    expectation = sum(probability * energy for probability, energy in values)
    variance = sum(probability * (energy - expectation) ** 2 for probability, energy in values)
    return {"expectation": float(expectation), "variance": float(variance)}


def probability_metrics(probabilities: Mapping[str, float], input_data: R23Input, *, threshold: float = 1e-12) -> dict[str, Any]:
    records = []
    for label, probability in sorted(probabilities.items()):
        p = float(probability)
        bits = qiskit_label_to_bits(label)
        validation = validate_bitstring(bits, input_data.n, input_data.customer_ids)
        records.append({"qiskit_label": label, "bitstring": list(bits), "probability": p, "valid": validation.status == ValidationStatus.VALID, "status": validation.status.value, "route": list(validation.route) if validation.route else None})
    total = sum(r["probability"] for r in records)
    feasible = [r for r in records if r["valid"] and r["probability"] >= threshold]
    p_feasible = sum(r["probability"] for r in records if r["valid"])
    p_opt = sum(r["probability"] for r in records if tuple(r["bitstring"]) in input_data.exact_optimal_bitstrings)
    most_probable = max(records, key=lambda r: (r["probability"], r["qiskit_label"]), default=None)
    most_probable_feasible = max(feasible, key=lambda r: (r["probability"], r["qiskit_label"]), default=None)
    best_feasible = None
    for record in feasible:
        route = record["route"]
        cost = route_travel_time(input_data.depot_id, route, input_data.normalized_matrix) if route else math.nan
        candidate = {"record": record, "normalized_route_objective": cost}
        if best_feasible is None or cost < best_feasible["normalized_route_objective"]:
            best_feasible = candidate
    return {"probability_total": total, "P_feasible_exact": p_feasible, "P_opt": p_opt, "invalid_probability_mass": total - p_feasible, "most_probable_state": most_probable, "most_probable_feasible_state": most_probable_feasible, "best_feasible_state": best_feasible, "records": records, "probability_threshold": threshold}
