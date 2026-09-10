from __future__ import annotations

import itertools

from traffic_simulation.r20_route_ordering.analyze_lambda_bound import (
    assignment_penalty,
    adversarial_matrix,
    exact_lambda_critical,
    travel_objective,
)


def all_bits(n: int):
    return itertools.product((0, 1), repeat=n * n)


def test_minimum_positive_assignment_penalty_is_two_n2_n3():
    for n in (2, 3):
        penalties = [assignment_penalty(tuple(bits), n) for bits in all_bits(n)]
        assert min(value for value in penalties if value > 0) == 2


def test_arbitrary_state_travel_bound_is_counted_independently():
    for n in (2, 3, 4):
        matrix = adversarial_matrix(n, "all_one")
        maximum = max(travel_objective(tuple(bits), n, matrix) for bits in all_bits(n))
        assert maximum == n * ((n - 1) ** 2 + 2)


def test_universal_bound_exceeds_exact_threshold_on_adversarial_n2_n3_n4():
    for n in (2, 3, 4):
        for fixture in ("all_one", "cheap_cycle", "asymmetric", "near_one"):
            result = exact_lambda_critical(n, adversarial_matrix(n, fixture))
            assert result["exact_critical_lambda"] < (n + 1) / 2


def test_exact_threshold_is_strict_at_tie_boundary():
    result = exact_lambda_critical(2, adversarial_matrix(2, "all_one"))
    assert result["exact_critical_lambda"] == 1.0
