"""Inputs/outputs and deterministic route enumeration, Huang (2025) eqs. 5/13/14.

Costs are artificial distance units, demands integer parcels. No RNG is used here.
Invalid data raise ValueError. Tests: tests/toc_cg/test_reference.py.
"""
from dataclasses import dataclass
from itertools import permutations
import numpy as np


@dataclass(frozen=True)
class Instance:
    name: str
    distance: np.ndarray
    demand: tuple[int, ...]
    capacity: int
    coordinates: tuple[tuple[float, float], ...] = ()

    def __post_init__(self):
        d = np.array(self.distance, dtype=float, copy=True)
        n = len(self.demand)
        if n < 2 or d.shape != (n, n) or not np.isfinite(d).all() or (d < 0).any():
            raise ValueError('Invalid directed distance matrix')
        if not np.allclose(np.diag(d), 0) or self.demand[0] != 0:
            raise ValueError('Depot demand and diagonal must be zero')
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError('Capacity must be a positive integer')
        if any(type(q) is not int or q < 1 or q > self.capacity for q in self.demand[1:]):
            raise ValueError('Positive integer customer demand within capacity required')
        d.setflags(write=False)
        object.__setattr__(self, 'distance', d)

    @property
    def customers(self):
        return tuple(range(1, len(self.demand)))


@dataclass(frozen=True, order=True)
class Route:
    customers: tuple[int, ...]

    def nodes(self):
        return (0,) + self.customers + (0,)


def validate_route(instance, route):
    ids = route.customers
    if not ids or len(ids) != len(set(ids)) or any(i not in instance.customers for i in ids):
        raise ValueError('Empty, repeated, or unknown customer')
    if sum(instance.demand[i] for i in ids) > instance.capacity:
        raise ValueError('Route exceeds capacity')


def route_cost(instance, route):
    validate_route(instance, route)
    nodes = route.nodes()
    return float(sum(instance.distance[i, j] for i, j in zip(nodes, nodes[1:])))


def reduced_cost(instance, route, dual):
    return route_cost(instance, route) - sum(float(dual[i - 1]) for i in route.customers)


def enumerate_routes(instance, candidates=None, max_customers=None):
    """Exact elementary-route oracle on the explicitly declared finite domain."""
    ids = tuple(sorted(instance.customers if candidates is None else candidates))
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(instance.customers):
        raise ValueError('Invalid pricing domain')
    if len(ids) > 8:
        raise ValueError('Reference enumerator is deliberately limited to 8 customers')
    limit = len(ids) if max_customers is None else min(max_customers, len(ids))
    return [Route(p) for k in range(1, limit + 1) for p in permutations(ids, k)
            if sum(instance.demand[i] for i in p) <= instance.capacity]


def artificial_instance(m):
    """Deterministic independent fixtures, not the authors' unpublished instances."""
    coords = ((.5, .5), (.10, .10), (.15, .15), (.85, .85),
              (.90, .90), (.10, .85), (.15, .90))[:m + 1]
    demands = {4: (0, 12, 13, 12, 13), 5: (0, 8, 9, 10, 11, 12),
               6: (0, 7, 8, 9, 10, 11, 12)}
    if m not in demands:
        raise ValueError('Reference fixture supports 4/5/6 customers')
    xy = np.asarray(coords)
    d = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
    return Instance(f'independent_{m}', d, demands[m], 25, coords)
