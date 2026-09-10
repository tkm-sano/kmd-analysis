"""Exact-small R22 equivalence validator."""

from __future__ import annotations

import copy
import math
from typing import Any

from traffic_simulation.r20_route_ordering.core import ENERGY_ABS_TOLERANCE, ValidationStatus, encode_route, validate_bitstring

from .converter import IsingCoefficients, binary_to_spin, convert_qubo_to_ising, evaluate_ising
from .schema import R22Input, coefficient_hash, ising_coefficient_hash

FAILURE_REASONS = (
    "R21_INPUT_NOT_PASS", "QUBO_HASH_MISMATCH", "SPIN_MAPPING_FAILURE", "ISING_COEFFICIENT_MISMATCH",
    "CONSTANT_OFFSET_MISMATCH", "ENERGY_EQUIVALENCE_FAILURE", "GLOBAL_OPTIMUM_MISMATCH",
    "TIE_SET_MISMATCH", "ROUTE_SET_MISMATCH", "INDEX_MAPPING_FAILURE", "NUMERICAL_TOLERANCE_FAILURE",
    "NONDETERMINISTIC_RESULT",
)


class R22ValidationError(ValueError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def _qubo_energy(bits, qubo) -> float:
    return qubo.constant + sum(qubo.linear[i] * bits[i] for i in qubo.linear) + sum(value * bits[a] * bits[b] for (a, b), value in qubo.quadratic.items())


def _energy_equal(left: float, right: float, tolerance: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)


def _coefficient_equal(actual: IsingCoefficients, expected: IsingCoefficients, tolerance: float) -> bool:
    return actual.n_logical == expected.n_logical and actual.binary_spin_convention == expected.binary_spin_convention and _energy_equal(actual.constant, expected.constant, tolerance) and set(actual.linear) == set(expected.linear) and set(actual.quadratic) == set(expected.quadratic) and all(_energy_equal(actual.linear[k], expected.linear[k], tolerance) for k in actual.linear) and all(_energy_equal(actual.quadratic[k], expected.quadratic[k], tolerance) for k in actual.quadratic)


def validate_conversion(input_data: R22Input, *, ising: IsingCoefficients | None = None, max_logical_variables: int = 16, max_states: int = 1_000_000, energy_tolerance: float = ENERGY_ABS_TOLERANCE) -> dict[str, Any]:
    """Validate one R22 input in memory; does not update repository status."""
    if not isinstance(input_data, R22Input):
        raise R22ValidationError("R21_INPUT_NOT_PASS", "expected validated R22Input")
    if energy_tolerance < 0 or not math.isfinite(energy_tolerance):
        raise R22ValidationError("NUMERICAL_TOLERANCE_FAILURE", "energy tolerance must be finite and non-negative")
    expected = convert_qubo_to_ising(input_data.qubo)
    actual = ising if ising is not None else expected
    logical = input_data.qubo.n_logical
    state_count = 2 ** logical
    if logical > max_logical_variables or state_count > max_states:
        raise R22ValidationError("EXACT_ENUMERATION_GUARD", f"R22 exact enumeration guarded: n_logical={logical}, states={state_count}")
    # I1 is evaluated against a second independently constructed coefficient object.
    algebra = convert_qubo_to_ising(input_data.qubo)
    i1 = _coefficient_equal(actual, algebra, energy_tolerance)
    i2 = True
    mismatches = []
    qubo_energies = []
    ising_energies = []
    for integer in range(state_count):
        bits = tuple((integer >> (logical - 1 - k)) & 1 for k in range(logical))
        spins = binary_to_spin(bits)
        if tuple((1 - spin) // 2 for spin in spins) != bits:
            i2 = False
        q_energy = _qubo_energy(bits, input_data.qubo)
        i_energy = evaluate_ising(spins, actual)
        qubo_energies.append((bits, q_energy)); ising_energies.append((spins, i_energy))
        difference = abs(q_energy - i_energy)
        if difference > energy_tolerance:
            mismatches.append({"bitstring": list(bits), "spins": list(spins), "absolute_difference": difference})
    i3 = not mismatches
    q_min = min(value for _, value in qubo_energies); i_min = min(value for _, value in ising_energies)
    q_global = {bits for bits, value in qubo_energies if _energy_equal(value, q_min, energy_tolerance)}
    i_global_bits = {tuple((1 - spin) // 2 for spin in spins) for spins, value in ising_energies if _energy_equal(value, i_min, energy_tolerance)}
    i4 = q_global == i_global_bits
    expected_routes = {tuple(route) for route in input_data.payload.get("r21_optimal_routes", [])}
    decoded_routes = set()
    decode_ok = True
    for bits in i_global_bits:
        validation = validate_bitstring(bits, input_data.payload["n"], input_data.customer_ids)
        if validation.status != ValidationStatus.VALID or not validation.decode_success:
            decode_ok = False
        else:
            decoded_routes.add(tuple(validation.route))
    i5 = decode_ok and (not expected_routes or decoded_routes == expected_routes)
    i6 = len(q_global) == len(i_global_bits) and i4 and i5
    i7 = coefficient_hash(input_data.qubo) == input_data.payload["qubo_coefficient_hash"] and bool(input_data.payload.get("r21", {}).get("validation_results_sha256"))
    i8 = _coefficient_equal(expected, convert_qubo_to_ising(input_data.qubo), energy_tolerance)
    checks = {"I1_conversion_algebra": i1, "I2_variable_mapping": i2, "I3_energy_equivalence": i3, "I4_global_optimum_equivalence": i4, "I5_route_equivalence": i5, "I6_tie_preservation": i6, "I7_coefficient_provenance_integrity": i7, "I8_deterministic_conversion": i8}
    failures = []
    for key, reason in (("I1_conversion_algebra", "ISING_COEFFICIENT_MISMATCH"), ("I2_variable_mapping", "SPIN_MAPPING_FAILURE"), ("I3_energy_equivalence", "ENERGY_EQUIVALENCE_FAILURE"), ("I4_global_optimum_equivalence", "GLOBAL_OPTIMUM_MISMATCH"), ("I5_route_equivalence", "ROUTE_SET_MISMATCH"), ("I6_tie_preservation", "TIE_SET_MISMATCH"), ("I7_coefficient_provenance_integrity", "QUBO_HASH_MISMATCH"), ("I8_deterministic_conversion", "NONDETERMINISTIC_RESULT")):
        if not checks[key]: failures.append(reason)
    max_difference = max((item["absolute_difference"] for item in mismatches), default=max(abs(q - i) for (_, q), (_, i) in zip(qubo_energies, ising_energies)))
    return {
        "schema_version": "r22-reduced-ising-conversion-result-v1", "r22_stage": "R22_REDUCED_ISING_CONVERSION", "status": "PASS" if all(checks.values()) else "FAIL", "instance_id": input_data.instance_id, "n": input_data.payload["n"], "n_logical": logical, "state_count": state_count, "binary_spin_convention": actual.binary_spin_convention, "qubo_constant": input_data.qubo.constant, "ising_constant": actual.constant, "transformation_offset": actual.constant, "ising_linear": actual.linear, "ising_quadratic": {f"{a},{b}": value for (a, b), value in actual.quadratic.items()}, "ising_coefficient_hash": ising_coefficient_hash(actual), "max_abs_energy_mismatch": max_difference, "energy_mismatch_count": len(mismatches), "qubo_global_minimum_energy": q_min, "ising_global_minimum_energy": i_min, "qubo_global_minimum_count": len(q_global), "ising_global_minimum_count": len(i_global_bits), "decoded_ising_routes": [list(route) for route in sorted(decoded_routes, key=repr)], "checks": checks, "failure_reasons": failures, "metadata": {"energy_tolerance": energy_tolerance, "formal_r22_execution": False, "implementation_smoke_only": True},
    }
