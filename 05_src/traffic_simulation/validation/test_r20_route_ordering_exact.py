from __future__ import annotations

import itertools
import math

import pytest

from traffic_simulation.r20_route_ordering.core import (
    ENERGY_ABS_TOLERANCE,
    ExactEnumerationGuardError,
    QuboInputError,
    ValidationStatus,
    build_expanded_qubo,
    decode_bitstring,
    encode_route,
    enumerate_qubo_states,
    enumerate_routes,
    evaluate_direct_qubo,
    evaluate_expanded_qubo,
    normalize_travel_time_matrix,
    penalty_consistency,
    validate_bitstring,
)
from traffic_simulation.r20_route_ordering.run_validation import LAMBDA_CANDIDATES, synthetic_instances


def instance_n2():
    nodes = [0, 1, 2]
    values = [[0, 1, 8], [7, 0, 1], [1, 7, 0]]
    return {a: {b: float(values[i][j]) for j, b in enumerate(nodes)} for i, a in enumerate(nodes)}


def mutation_instance():
    return synthetic_instances()[-1]


def test_valid_encoding_and_decoder_roundtrip():
    bits = encode_route((2, 1), [1, 2])
    assert bits == (0, 1, 1, 0)
    assert decode_bitstring(bits, 2, [1, 2]) == ((2, 1), ValidationStatus.VALID)
    assert validate_bitstring(bits, 2, [1, 2]).status == ValidationStatus.VALID


@pytest.mark.parametrize("bits,status", [
    ((1, 1, 0, 0), ValidationStatus.INVALID_CUSTOMER_ONCE),
    ((1, 0, 0, 1), ValidationStatus.VALID),
    ((1, 0, 0, 0), ValidationStatus.INVALID_BOTH),
    ((1, 1, 1, 0), ValidationStatus.INVALID_BOTH),
    ((1, 0, 1, 0), ValidationStatus.INVALID_POSITION_ONCE),
    ((1, 0, 0), ValidationStatus.INVALID_BITSTRING),
    ((1, 0, 0, 2), ValidationStatus.INVALID_BITSTRING),
])
def test_assignment_classification(bits, status):
    assert validate_bitstring(bits, 2, [1, 2]).status == status


@pytest.mark.parametrize("malformed", [None, 7, object(), "1001"])
def test_malformed_bitstrings_are_classified(malformed):
    assert validate_bitstring(malformed, 2, [1, 2]).status == ValidationStatus.INVALID_BITSTRING
    assert decode_bitstring(malformed, 2, [1, 2]) == (None, ValidationStatus.INVALID_BITSTRING)


@pytest.mark.parametrize("call", [
    lambda: validate_bitstring((1, 0, 0, 1), 2, [1, 1]),
    lambda: encode_route((1, 1), [1, 1]),
    lambda: enumerate_routes(0, [1, 1], instance_n2()),
])
def test_duplicate_customer_ids_are_rejected(call):
    with pytest.raises(QuboInputError, match="unique"):
        call()


def test_penalty_calculation_matches_expansion_for_all_n2_states():
    for state in range(16):
        bits = tuple((state >> (3 - k)) & 1 for k in range(4))
        assert penalty_consistency(bits, 2) == (True, True)


def test_original_permutation_optimum_and_tie_retention():
    reference = enumerate_routes(0, [1, 2], instance_n2())
    assert reference["evaluated_permutations"] == math.factorial(2)
    assert reference["best_route"] == [0, 1, 2, 0]
    assert reference["best_route_travel_time"] == 3.0
    tie = synthetic_instances()[2]
    tie_result = enumerate_routes(tie[1], tie[2], tie[3])
    assert len(tie_result["optimal_routes"]) == math.factorial(3)


def test_correct_expanded_coefficient_sources():
    _, depot, customers, travel = mutation_instance()
    lam = 2.0
    coefficients = build_expanded_qubo(depot, customers, travel, lam)
    assert coefficients.constant == 2 * len(customers) * lam
    assert coefficients.linear[0] == -2 * lam + travel[0][1]  # depot departure
    assert coefficients.linear[1] == -2 * lam
    assert coefficients.linear[2] == -2 * lam + travel[1][0]  # depot return
    assert coefficients.quadratic[(0, 1)] == 2 * lam  # row pair; no i==j travel
    assert coefficients.quadratic[(0, 3)] == 2 * lam  # column pair
    assert coefficients.quadratic[(0, 4)] == travel[1][2]  # consecutive i!=j
    assert (0, 5) not in coefficients.quadratic  # different customer, non-consecutive


def test_objective_terms_are_individually_observable():
    _, depot, customers, travel = mutation_instance()
    routes = list(itertools.permutations(customers))

    def optimum(include_departure=True, include_return=True, include_middle=True):
        costs = {}
        for route in routes:
            cost = travel[depot][route[0]] if include_departure else 0
            cost += travel[route[-1]][depot] if include_return else 0
            if include_middle:
                cost += sum(travel[a][b] for a, b in zip(route, route[1:]))
            costs[route] = cost
        return min(costs, key=costs.get)

    full = optimum()
    assert full == (3, 2, 1)
    assert optimum(include_departure=False) != full
    assert optimum(include_return=False) != full
    assert optimum(include_middle=False) != full


def test_direct_vs_expanded_exhaustive_all_fixtures_and_lambdas():
    for _, depot, customers, raw in synthetic_instances():
        normalized, _ = normalize_travel_time_matrix(depot, customers, raw)
        for lam in LAMBDA_CANDIDATES:
            result = enumerate_qubo_states(depot, customers, normalized, lam)
            assert result["direct_expanded_mismatch_count"] == 0
            assert result["direct_expanded_max_abs_difference"] <= ENERGY_ABS_TOLERANCE
            assert len(result["records"]) == 2 ** (len(customers) ** 2)
            assert len({tuple(r["bitstring"]) for r in result["records"]}) == len(result["records"])


def test_manual_direct_and_expanded_energy_detect_penalty_signs():
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    bits = (1, 1, 0, 0)
    lam = 0.25
    direct = evaluate_direct_qubo(bits, 0, [1, 2], normalized, lam)
    expanded = evaluate_expanded_qubo(bits, build_expanded_qubo(0, [1, 2], normalized, lam))
    assert direct["customer_penalty"] == 2
    assert direct["position_penalty"] == 0
    assert math.isclose(float(direct["qubo_energy"]), expanded, abs_tol=ENERGY_ABS_TOLERANCE)


def test_self_loop_entries_are_not_required_or_used():
    no_diagonal = {0: {1: 1, 2: 8}, 1: {0: 7, 2: 1}, 2: {0: 1, 1: 7}}
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], no_diagonal)
    coefficients = build_expanded_qubo(0, [1, 2], normalized, 0.5)
    assert coefficients.quadratic[(0, 1)] == 1.0
    assert coefficients.quadratic[(2, 3)] == 1.0


def test_qubo_feasible_optimum_and_lambda_insufficient_vs_sufficient():
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    insufficient = enumerate_qubo_states(0, [1, 2], normalized, 0.0)
    sufficient = enumerate_qubo_states(0, [1, 2], normalized, 1.0)
    assert not insufficient["all_global_minima_feasible"]
    assert sufficient["all_global_minima_feasible"]
    assert sufficient["best_infeasible_energy"] > sufficient["best_feasible_energy"]


@pytest.mark.parametrize("lam", [float("nan"), float("inf"), -1.0])
def test_invalid_lambda_is_rejected(lam):
    with pytest.raises(QuboInputError, match="finite non-negative"):
        enumerate_qubo_states(0, [1, 2], instance_n2(), lam)
    with pytest.raises(QuboInputError, match="finite non-negative"):
        build_expanded_qubo(0, [1, 2], instance_n2(), lam)
    with pytest.raises(QuboInputError, match="finite non-negative"):
        evaluate_direct_qubo((1, 0, 0, 1), 0, [1, 2], instance_n2(), lam)


def test_tie_comparison_policy_includes_all_feasible_routes_and_rejects_infeasible_tie():
    _, depot, customers, raw = synthetic_instances()[2]
    normalized, _ = normalize_travel_time_matrix(depot, customers, raw)
    tied = enumerate_qubo_states(depot, customers, normalized, 1.0)
    separated = enumerate_qubo_states(depot, customers, normalized, 2.0)
    assert not tied["all_global_minima_feasible"]
    assert len(tied["best_feasible_states"]) == math.factorial(3)
    assert separated["all_global_minima_feasible"]
    assert len(separated["best_feasible_states"]) == math.factorial(3)


def test_normalization_preserves_ranking_and_is_non_destructive():
    raw = instance_n2()
    original = {i: dict(row) for i, row in raw.items()}
    raw_result = enumerate_routes(0, [1, 2], raw)
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], raw)
    normalized_result = enumerate_routes(0, [1, 2], normalized)
    assert raw == original
    assert {tuple(x[1:-1]) for x in raw_result["optimal_routes"]} == {tuple(x[1:-1]) for x in normalized_result["optimal_routes"]}


def test_exact_enumeration_guard():
    normalized, _ = normalize_travel_time_matrix(0, [1, 2], instance_n2())
    with pytest.raises(ExactEnumerationGuardError):
        enumerate_qubo_states(0, [1, 2], normalized, 1.0, max_logical_variables=3)
