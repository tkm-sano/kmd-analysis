"""Decode selected HiGHS arc variables without validating feasibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .r24_cvrp_model import CVRPInstance, HighsModelArtifacts, INTEGER_TOLERANCE


@dataclass(frozen=True)
class DecodedSolution:
    routes: tuple[tuple[str, ...], ...]
    selected_arcs: tuple[tuple[str, str, int], ...]
    errors: tuple[str, ...]


def decode_solution(instance: CVRPInstance, model: HighsModelArtifacts, values: Mapping[int, float]) -> DecodedSolution:
    selected = tuple(key for key, index in model.x.items() if values[index] >= 1 - INTEGER_TOLERANCE)
    routes: list[tuple[str, ...]] = []
    errors: list[str] = []
    for k in range(instance.max_vehicles):
        arcs = [(i, j) for i, j, vehicle in selected if vehicle == k]
        if not arcs:
            continue
        successors: dict[str, str] = {}
        for i, j in arcs:
            if i in successors:
                errors.append(f"vehicle {k}: multiple successors for {i}")
            successors[i] = j
        route = [instance.depot]
        used: set[tuple[str, str]] = set()
        current = instance.depot
        for _ in range(len(instance.customers) + 2):
            if current not in successors:
                errors.append(f"vehicle {k}: path stops at {current}")
                break
            nxt = successors[current]
            used.add((current, nxt))
            route.append(nxt)
            current = nxt
            if current == instance.depot:
                break
        else:
            errors.append(f"vehicle {k}: route traversal did not return")
        if current != instance.depot:
            errors.append(f"vehicle {k}: route does not return to depot")
        if used != set(arcs):
            errors.append(f"vehicle {k}: disconnected selected arcs")
        routes.append(tuple(route))
    return DecodedSolution(tuple(routes), selected, tuple(errors))

