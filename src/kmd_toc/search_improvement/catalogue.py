"""Finite artificial reference catalogue, NOT a scalable S1 pricing oracle.

Inputs: DayProblem, explicit column safety cap. Output: immutable old DayColumns.
Capacity-pruned DFS replaces factorial enumeration for medium Q=2 fixtures.
Old make_day/validator retain the verified time and physical constraints.
All exceptions propagate; limits never silently truncate the feasible domain.
"""
from itertools import product
from kmd_toc.column_generation.models import Route
from kmd_toc.vehicle_day.generation import make_day, grid_ceil


def routes_pruned(instance):
    result = []
    def visit(prefix, remaining, load):
        for i in remaining:
            new = load + instance.demand[i]
            if new <= instance.capacity:
                route = prefix + (i,)
                result.append(Route(route))
                visit(route, tuple(j for j in remaining if j != i), new)
    visit((), tuple(instance.customers), 0)
    return tuple(sorted(result))


def artificial_column_estimate(n, f):
    """Exact ONLY for Q=2,q=1,14-slot,120s uniform operations fixtures."""
    return f * (1 + 11*n + 30*n*(n-1) + 20*n*(n-1)*(n-2)
                + 3*n*(n-1)*(n-2)*(n-3))


def build_catalogue(problem, max_columns=120000):
    if len(problem.base.customers) > 12 or len(problem.vehicles) > 3 or problem.slots > 40:
        raise ValueError('ARTIFICIAL_CATALOGUE_DOMAIN_GUARD')
    if problem.base.capacity > 2 or any(v.capacity > 2 for v in problem.vehicles):
        raise ValueError('ARTIFICIAL_CAPACITY_TWO_ONLY')
    routes = routes_pruned(problem.base)
    result = []
    def append(column):
        if len(result) >= max_columns:
            raise ValueError('CATALOGUE_COLUMN_SAFETY_LIMIT')
        result.append(column)
    for v in problem.vehicles:
        append(make_day(problem, v.vehicle_id, (), ()))
        valid = [r for r in routes if sum(problem.base.demand[i] for i in r.customers) <= v.capacity]
        sequences = [(r,) for r in valid]
        sequences += [(a,b) for a,b in product(valid, repeat=2)
                      if not set(a.customers) & set(b.customers)]
        for sequence in sequences:
            for first in range(grid_ceil(v.ready_s, problem.delta_s), v.shift_end_s, problem.delta_s):
                try:
                    one = make_day(problem, v.vehicle_id, sequence[:1], (first,))
                except ValueError:
                    continue
                if len(sequence) == 1:
                    append(one)
                else:
                    ready = one.trips[0].return_s + v.preparation_s
                    for second in range(grid_ceil(ready, problem.delta_s), v.shift_end_s, problem.delta_s):
                        try:
                            column = make_day(problem, v.vehicle_id, sequence, (first, second))
                        except ValueError:
                            continue
                        append(column)
    return result
