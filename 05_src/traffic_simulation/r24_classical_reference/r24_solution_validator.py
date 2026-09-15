"""Solver-independent decoded-route validator and objective recomputation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .r24_cvrp_model import CVRPInstance, OBJECTIVE_TOLERANCE


@dataclass(frozen=True)
class ValidationResult:
    status: str
    errors: tuple[str, ...]
    objective: float
    total_distance: float
    used_vehicles: int
    route_loads: tuple[int, ...]
    route_travel_times: tuple[float, ...]
    route_distances: tuple[float, ...]
    objective_difference: float | None


def validate_routes(
    instance: CVRPInstance,
    routes: Iterable[Iterable[str]],
    reported_objective: float | None = None,
    decoder_errors: Iterable[str] = (),
) -> ValidationResult:
    normalized = tuple(tuple(route) for route in routes)
    errors = list(decoder_errors)
    served: list[str] = []
    loads: list[int] = []
    times: list[float] = []
    distances: list[float] = []
    valid_nodes = set(instance.nodes)
    for idx, route in enumerate(normalized):
        if len(route) < 3 or route[0] != instance.depot or route[-1] != instance.depot:
            errors.append(f"route {idx}: invalid depot endpoints")
        inner = route[1:-1]
        if instance.depot in inner:
            errors.append(f"route {idx}: interior depot/disconnected tour")
        served.extend(inner)
        if any(node not in valid_nodes for node in route):
            errors.append(f"route {idx}: unknown node")
        load = sum(instance.demands.get(customer, 0) for customer in inner)
        if load > instance.capacity:
            errors.append(f"route {idx}: capacity {load}>{instance.capacity}")
        loads.append(load)
        route_time = route_distance = 0.0
        for a, b in zip(route, route[1:]):
            arc = instance.arcs.get((a, b))
            if arc is None:
                errors.append(f"route {idx}: missing arc {a}->{b}")
                continue
            route_time += arc.travel_time
            route_distance += arc.distance
        times.append(route_time)
        distances.append(route_distance)
    counts = Counter(served)
    missing = sorted(set(instance.customers) - set(served))
    duplicate = sorted(customer for customer, count in counts.items() if count != 1)
    unexpected = sorted(set(served) - set(instance.customers))
    if missing:
        errors.append(f"missing customers: {missing}")
    if duplicate:
        errors.append(f"duplicate service: {duplicate}")
    if unexpected:
        errors.append(f"unexpected customers: {unexpected}")
    if sum(loads) != sum(instance.demands.values()):
        errors.append("total demand not conserved")
    if len(normalized) > instance.max_vehicles:
        errors.append("AT_MOST_M fleet limit exceeded")
    objective = sum(times)
    difference = None if reported_objective is None else abs(reported_objective - objective)
    if difference is not None and difference > OBJECTIVE_TOLERANCE:
        errors.append(f"objective mismatch: {difference}")
    return ValidationResult(
        status="VALID_SOLUTION" if not errors else "INVALID_SOLUTION",
        errors=tuple(errors),
        objective=objective,
        total_distance=sum(distances),
        used_vehicles=len(normalized),
        route_loads=tuple(loads),
        route_travel_times=tuple(times),
        route_distances=tuple(distances),
        objective_difference=difference,
    )

