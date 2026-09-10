from __future__ import annotations

import pytest

from traffic_simulation.r20_route_ordering.analyze_lambda_margin import (
    lambda_from_absolute_bound,
    lambda_from_relative_bound,
    validate_delta,
    validate_epsilon,
)


def test_relative_lambda_margin_calculation():
    assert lambda_from_relative_bound(2.0, 0.1) == pytest.approx(2.2)


def test_absolute_lambda_margin_calculation():
    assert lambda_from_absolute_bound(2.0, 1e-6) == pytest.approx(2.000001)


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_invalid_delta_rejected(value):
    with pytest.raises(ValueError):
        validate_delta(value)


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_epsilon_rejected(value):
    with pytest.raises(ValueError):
        validate_epsilon(value)
