from __future__ import annotations

import numpy as np
import pytest

from traffic_simulation.r20_route_ordering.core import encode_route
from traffic_simulation.r23_qaoa_aer.optimized_metrics_v4 import (
    V4InputError,
    indexed_probability_metrics,
)


def valid_case(n: int):
    customers = tuple(range(1, n + 1))
    route_bits = encode_route(customers, customers)
    state = np.zeros(2 ** (n * n), dtype=np.complex128)
    state[sum(bit << i for i, bit in enumerate(route_bits))] = 1.0
    return state, customers, (route_bits,)


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_valid_inputs_preserve_raw_probability_semantics(n: int) -> None:
    state, customers, optimal = valid_case(n)
    result = indexed_probability_metrics(state, customers, optimal, n)
    assert result["probability_total"] == 1.0
    assert result["P_feasible_exact"] == 1.0
    assert result["P_opt"] == 1.0
    assert result["invalid_probability_mass"] == 0.0
    assert result["renormalized"] is False


@pytest.mark.parametrize(
    "mutator",
    [
        lambda s, c, o, n: (s[:-1], c, o, n),
        lambda s, c, o, n: (s, c, ((0,) * (n * n)), n),
        lambda s, c, o, n: (s, c, (o[0], o[0]), n),
        lambda s, c, o, n: (np.full_like(s, np.nan), c, o, n),
        lambda s, c, o, n: (np.full_like(s, np.inf), c, o, n),
        lambda s, c, o, n: (s, c, (), n),
        lambda s, c, o, n: (s, c, o, n + 1),
        lambda s, c, o, n: (s.astype(np.int64), c, o, n),
    ],
)
def test_invalid_inputs_fail_closed(mutator) -> None:
    state, customers, optimal = valid_case(2)
    args = mutator(state, customers, optimal, 2)
    with pytest.raises(V4InputError):
        indexed_probability_metrics(*args)
