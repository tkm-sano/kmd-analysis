"""Heuristic pricing domains; explicit independent extensions, not paper features.

Inputs: immutable artificial Instance/dual. Outputs: contracted pricing and exact
expansion back to original routes. No demand or OD files are written. No RNG.
"""
from dataclasses import dataclass
import numpy as np
from .models import Instance, Route, enumerate_routes, route_cost, validate_route


@dataclass(frozen=True)
class Domain:
    name: str
    pricing: Instance
    groups: tuple[tuple[int, ...], ...]
    dual: tuple[float, ...]
    slots: int

    def expand(self, route):
        return Route(tuple(i for node in route.customers for i in self.groups[node - 1]))


def contract(instance, dual, groups, name, slots=4):
    groups = tuple(tuple(g) for g in groups)
    flat = [i for g in groups for i in g]
    if not groups or any(not g for g in groups) or len(set(flat)) != len(flat):
        raise ValueError('Fragments must be nonempty, disjoint, and oriented')
    if not set(flat) <= set(instance.customers):
        raise ValueError('Unknown fragment customer')
    demands = (0,) + tuple(sum(instance.demand[i] for i in g) for g in groups)
    if max(demands) > instance.capacity:
        raise ValueError('A mandatory fragment exceeds capacity')
    n = len(groups) + 1
    d = np.zeros((n, n))
    internal = [sum(instance.distance[a, b] for a, b in zip(g, g[1:])) for g in groups]
    for b, gb in enumerate(groups, 1):
        d[0, b] = instance.distance[0, gb[0]] + internal[b - 1]
        d[b, 0] = instance.distance[gb[-1], 0]
        for a, ga in enumerate(groups, 1):
            if a != b:
                d[a, b] = instance.distance[ga[-1], gb[0]] + internal[b - 1]
    reduced = Instance(name, d, demands, instance.capacity)
    return Domain(name, reduced, groups,
                  tuple(sum(float(dual[i - 1]) for i in g) for g in groups), slots)


def build_domains(instance, dual, k=3):
    """Fixed top-dual, near anchor, fragments, and updating overlapping domains."""
    ids = instance.customers
    top = sorted(ids, key=lambda i: (-float(dual[i - 1]), i))[:k]
    anchor = max(ids, key=lambda i: (float(dual[i - 1]), -i))
    near = sorted(ids, key=lambda i: (instance.distance[anchor, i], i))[:k]
    # Deterministic scaffold; no vehicle ownership is fixed by these fragments.
    unvisited, order, current = set(ids), [], 0
    while unvisited:
        nxt = min(unvisited, key=lambda i: (instance.distance[current, i], i))
        order.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    fragments = tuple(tuple(order[i:i + 2]) for i in range(0, len(order), 2))
    result = [contract(instance, dual, [(i,) for i in top], 'top_dual'),
              contract(instance, dual, [(i,) for i in near], 'geographic_anchor'),
              contract(instance, dual, fragments, 'oriented_fragments')]
    for anchor in sorted(top[:2]):
        group = sorted(ids, key=lambda i: (instance.distance[anchor, i], i))[:k]
        result.append(contract(instance, dual, [(i,) for i in group], f'adaptive_anchor_{anchor}'))
    return result


def exact_domain_routes(original, domain):
    routes = enumerate_routes(domain.pricing, max_customers=domain.slots - 1)
    expanded = [domain.expand(r) for r in routes]
    for small, full in zip(routes, expanded):
        validate_route(original, full)
        if abs(route_cost(original, full) - route_cost(domain.pricing, small)) > 1e-8:
            raise RuntimeError('Fragment contraction does not preserve route cost')
    return expanded
