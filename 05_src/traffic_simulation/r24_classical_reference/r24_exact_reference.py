"""Independent unlabeled-partition/permutation exact CVRP reference."""

from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass

from .r24_cvrp_model import CVRPInstance, OBJECTIVE_TOLERANCE, validate_instance


@dataclass(frozen=True)
class ExactResult:
    status: str
    objective: float | None
    total_distance: float | None
    routes: tuple[tuple[str, ...], ...]
    candidates_evaluated: int
    feasible_candidates: int
    optimum_multiplicity: int
    runtime_s: float


def _partitions(items: tuple[str, ...], max_blocks: int):
    blocks: list[list[str]] = []

    def visit(index: int):
        if index == len(items):
            yield tuple(tuple(block) for block in blocks)
            return
        item = items[index]
        for block in blocks:
            block.append(item)
            yield from visit(index + 1)
            block.pop()
        if len(blocks) < max_blocks:
            blocks.append([item])
            yield from visit(index + 1)
            blocks.pop()

    yield from visit(0)


def solve_exact(instance: CVRPInstance) -> ExactResult:
    """Enumerate unlabeled feasible partitions and every directed route order."""
    validate_instance(instance)
    started = time.perf_counter()
    best = math.inf
    best_distance = math.inf
    best_routes: tuple[tuple[str, ...], ...] = ()
    evaluated = feasible = multiplicity = 0
    for partition in _partitions(instance.customers, instance.max_vehicles):
        if any(sum(instance.demands[c] for c in block) > instance.capacity for block in partition):
            continue
        permutations = [tuple(itertools.permutations(block)) for block in partition]
        for ordered_blocks in itertools.product(*permutations):
            evaluated += 1
            routes = tuple((instance.depot, *order, instance.depot) for order in ordered_blocks)
            objective = sum(
                instance.arcs[a, b].travel_time
                for route in routes for a, b in zip(route, route[1:])
            )
            distance = sum(
                instance.arcs[a, b].distance
                for route in routes for a, b in zip(route, route[1:])
            )
            feasible += 1
            if objective < best - OBJECTIVE_TOLERANCE:
                best, best_distance, best_routes, multiplicity = objective, distance, routes, 1
            elif abs(objective - best) <= OBJECTIVE_TOLERANCE:
                multiplicity += 1
    runtime = time.perf_counter() - started
    if math.isinf(best):
        return ExactResult("INFEASIBLE", None, None, (), evaluated, feasible, 0, runtime)
    return ExactResult("OPTIMAL", best, best_distance, best_routes, evaluated, feasible, multiplicity, runtime)

