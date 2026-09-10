from __future__ import annotations

import pytest

from traffic_simulation.r20_route_ordering.core import (
    ExactEnumerationGuardError,
    ValidationStatus,
    decode_bitstring,
    encode_route,
    enumerate_qubo_states,
    enumerate_routes,
    normalize_travel_time_matrix,
    penalty_consistency,
    validate_bitstring,
)
from traffic_simulation.r20_route_ordering.run_validation import synthetic_instances


def instance_n2():
    nodes = [0, 1, 2]
    values = [[0, 1, 8], [7, 0, 1], [1, 7, 0]]
    return {a: {b: float(values[i][j]) for j, b in enumerate(nodes)} for i, a in enumerate(nodes)}


def test_valid_encoding_and_decoder_roundtrip():
    bits = encode_route((2, 1), [1, 2])
    assert bits == (0, 1, 1, 0)
    assert decode_bitstring(bits, 2, [1, 2]) == ((2, 1), ValidationStatus.VALID)
    assert validate_bitstring(bits, 2, [1, 2]).status == ValidationStatus.VALID


@pytest.mark.parametrize("bits,status", [
    ((1, 1, 0, 0), ValidationStatus.INVALID_CUSTOMER_ONCE),  # duplicate customer / empty position
    ((1, 0, 0, 1), ValidationStatus.VALID),
    ((1, 0, 0, 0), ValidationStatus.INVALID_BOTH),
    ((1, 1, 1, 0), ValidationStatus.INVALID_BOTH),
    ((1, 0, 0), ValidationStatus.INVALID_BITSTRING),
])
def test_invalid_assignment_classification(bits, status):
    assert validate_bitstring(bits, 2, [1, 2]).status == status


def test_position_violation_is_distinguished():
    result = validate_bitstring((1, 0, 1, 0), 2, [1, 2])
    assert result.status == ValidationStatus.INVALID_POSITION_ONCE


def test_penalty_calculation_matches_expansion_for_all_n2_states():
    assert all(penalty_consistency(tuple((state >> (3 - k)) & 1 for k in range(4)), 2) == (True, True) for state in range(16))


def test_original_permutation_optimum_and_tie_retention():
    reference = enumerate_routes(0, [1, 2], instance_n2())
    assert reference["evaluated_permutations"] == 2
    assert reference["best_route"] == [0, 1, 2, 0]
    tie = synthetic_instances()[-1]
    tie_result = enumerate_routes(tie[1], tie[2], tie[3])
    assert len(tie_result["optimal_routes"]) > 1


def test_qubo_feasible_optimum_and_lambda_insufficient_vs_sufficient():
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    insufficient = enumerate_qubo_states(0, [1, 2], normalized, 0.0)
    sufficient = enumerate_qubo_states(0, [1, 2], normalized, 1.0)
    assert not insufficient["global_minimum_all_feasible"]
    assert sufficient["global_minimum_all_feasible"]
    assert sufficient["best_infeasible_energy"] > sufficient["best_feasible_energy"]


def test_normalization_preserves_route_ranking():
    raw = enumerate_routes(0, [1, 2], instance_n2())
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    scaled = enumerate_routes(0, [1, 2], normalized)
    assert {tuple(x[1:-1]) for x in raw["optimal_routes"]} == {tuple(x[1:-1]) for x in scaled["optimal_routes"]}


def test_exact_enumeration_guard():
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    with pytest.raises(ExactEnumerationGuardError):
        enumerate_qubo_states(0, [1, 2], normalized, 1.0, max_logical_variables=3)
