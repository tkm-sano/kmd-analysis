from __future__ import annotations

import math

import pytest

from traffic_simulation.r20_route_ordering.analyze_lambda_tolerance_rule import tolerance_aware_lambda


def test_tolerance_rule_is_strict_and_uses_relative_floor():
    assert tolerance_aware_lambda(2.0, 1e-12, 10, 1e-6) > 2.0
    assert tolerance_aware_lambda(2.0, 1e-12, 10, 1e-6) == pytest.approx(2.000002)


def test_tolerance_rule_uses_absolute_floor_for_small_bound():
    value = tolerance_aware_lambda(1e-15, 1e-6, 10, 1e-12)
    assert value == pytest.approx(1e-5)
    assert value > 1e-15


def test_zero_bound_and_zero_noise_cannot_claim_strict_safety():
    with pytest.raises(ValueError):
        tolerance_aware_lambda(0.0, 0.0, 10, 1e-6)


@pytest.mark.parametrize("args", [(math.nan, 1, 1, 1e-6), (1, math.inf, 1, 1e-6), (1, 1, 0, 1e-6), (1, 1, 1, 0)])
def test_tolerance_rule_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        tolerance_aware_lambda(*args)
