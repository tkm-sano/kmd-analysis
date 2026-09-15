"""Immutable R24 input model and explicit HiGHS MILP builder."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import highspy
import numpy as np

DEPOT_ID = "DEP_006"
CAPACITY = 14
FLEET_SEMANTICS = "AT_MOST_M"
SUBTOUR_FORMULATION = "LOAD_MTZ"
OBJECTIVE_TOLERANCE = 1e-7
FEASIBILITY_TOLERANCE = 1e-7
INTEGER_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Arc:
    travel_time: float
    distance: float
    zero_proxy: bool = False


@dataclass(frozen=True)
class CVRPInstance:
    instance_id: str
    condition_id: str
    suite: str
    customers: tuple[str, ...]
    demands: Mapping[str, int]
    arcs: Mapping[tuple[str, str], Arc]
    max_vehicles: int
    target_rho: float
    actual_rho: float
    capacity: int = CAPACITY
    depot: str = DEPOT_ID

    @property
    def nodes(self) -> tuple[str, ...]:
        return (self.depot, *self.customers)


@dataclass
class HighsModelArtifacts:
    highs: highspy.Highs
    x: dict[tuple[str, str, int], int]
    y: dict[tuple[str, int], int]
    z: dict[int, int]
    u: dict[tuple[str, int], int]


def _bool(value: str) -> bool:
    return value.strip().lower() == "true"


def validate_instance(instance: CVRPInstance) -> None:
    if instance.depot != DEPOT_ID:
        raise ValueError(f"unexpected depot: {instance.depot}")
    if instance.capacity != CAPACITY:
        raise ValueError(f"unexpected capacity: {instance.capacity}")
    if len(instance.customers) != len(set(instance.customers)):
        raise ValueError("duplicate customer ID")
    if instance.max_vehicles < 1:
        raise ValueError("max_vehicles must be positive")
    for customer in instance.customers:
        q = instance.demands.get(customer)
        if not isinstance(q, int) or isinstance(q, bool) or not 1 <= q <= CAPACITY:
            raise ValueError(f"invalid demand for {customer}: {q!r}")
    for i in instance.nodes:
        for j in instance.nodes:
            if i == j:
                continue
            arc = instance.arcs.get((i, j))
            if arc is None:
                raise ValueError(f"missing arc {i!r}->{j!r}")
            if not np.isfinite(arc.travel_time) or arc.travel_time < 0:
                raise ValueError(f"invalid travel time {i!r}->{j!r}")
            if not np.isfinite(arc.distance) or arc.distance < 0:
                raise ValueError(f"invalid distance {i!r}->{j!r}")
            if (arc.travel_time == 0 or arc.distance == 0) and not arc.zero_proxy:
                raise ValueError(f"unflagged zero arc {i!r}->{j!r}")


def load_instance(suite_dir: Path, base_instance_id: str, condition_id: str) -> CVRPInstance:
    base_dir = suite_dir / "instances" / base_instance_id
    with (base_dir / "base_instance.json").open(encoding="utf-8") as handle:
        base = json.load(handle)
    with (base_dir / "capacity_conditions.json").open(encoding="utf-8") as handle:
        conditions = json.load(handle)
    if isinstance(conditions, dict):
        condition_rows = conditions.get("conditions", conditions.get("capacity_conditions", []))
    else:
        condition_rows = conditions
    condition = next((row for row in condition_rows if row["condition_id"] == condition_id), None)
    if condition is None:
        raise ValueError(f"condition not found: {condition_id}")
    if base.get("base_status") != "VALID" or base.get("routing_validation_status") != "PASS":
        raise ValueError(f"base instance is not validated: {base_instance_id}")
    demands = {row["customer_id"]: int(row["q_i"]) for row in base["q_i_by_customer"]}
    arcs: dict[tuple[str, str], Arc] = {}
    with (base_dir / "od_manifest.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not _bool(row["reachable"]) or row["validation_status"] != "PASS":
                raise ValueError(f"invalid OD row in {base_instance_id}")
            key = (row["origin_id"], row["destination_id"])
            arcs[key] = Arc(
                travel_time=float(row["travel_time_s"]),
                distance=float(row["distance_m"]),
                zero_proxy=_bool(row["zero_proxy_arc_flag"]),
            )
    instance = CVRPInstance(
        instance_id=base_instance_id,
        condition_id=condition_id,
        suite=base["suite"],
        customers=tuple(base["customer_ids"]),
        demands=demands,
        arcs=arcs,
        max_vehicles=int(condition["m"]),
        target_rho=float(condition["target_rho"]),
        actual_rho=float(condition["actual_rho"]),
    )
    validate_instance(instance)
    return instance


def _add_col(highs: highspy.Highs, lower: float, upper: float, cost: float, integer: bool) -> int:
    index = highs.getNumCol()
    status = highs.addVar(lower, upper)
    if status != highspy.HighsStatus.kOk:
        raise RuntimeError(f"HiGHS addVar failed: {status}")
    highs.changeColCost(index, cost)
    if integer:
        highs.changeColIntegrality(index, highspy.HighsVarType.kInteger)
    return index


def _add_row(highs: highspy.Highs, coefficients: Mapping[int, float], lower: float, upper: float) -> None:
    items = [(idx, value) for idx, value in coefficients.items() if value]
    indices = np.asarray([idx for idx, _ in items], dtype=np.int32)
    values = np.asarray([value for _, value in items], dtype=np.float64)
    status = highs.addRow(lower, upper, len(items), indices, values)
    if status != highspy.HighsStatus.kOk:
        raise RuntimeError(f"HiGHS addRow failed: {status}")


def build_highs_model(instance: CVRPInstance) -> HighsModelArtifacts:
    """Build a three-index arc MILP with load-MTZ subtour elimination."""
    validate_instance(instance)
    highs = highspy.Highs()
    inf = highspy.kHighsInf
    x: dict[tuple[str, str, int], int] = {}
    y: dict[tuple[str, int], int] = {}
    z: dict[int, int] = {}
    u: dict[tuple[str, int], int] = {}
    vehicles = range(instance.max_vehicles)
    for k in vehicles:
        z[k] = _add_col(highs, 0, 1, 0, True)
        for customer in instance.customers:
            y[customer, k] = _add_col(highs, 0, 1, 0, True)
            u[customer, k] = _add_col(highs, 0, instance.capacity, 0, False)
        for i in instance.nodes:
            for j in instance.nodes:
                if i != j:
                    x[i, j, k] = _add_col(highs, 0, 1, instance.arcs[i, j].travel_time, True)

    # Every building-based customer identity is assigned exactly once.
    for customer in instance.customers:
        _add_row(highs, {y[customer, k]: 1 for k in vehicles}, 1, 1)
    for k in vehicles:
        # Per-vehicle assignment/flow consistency.
        for customer in instance.customers:
            outbound = {x[customer, j, k]: 1 for j in instance.nodes if j != customer}
            outbound[y[customer, k]] = -1
            _add_row(highs, outbound, 0, 0)
            inbound = {x[i, customer, k]: 1 for i in instance.nodes if i != customer}
            inbound[y[customer, k]] = -1
            _add_row(highs, inbound, 0, 0)
        departure = {x[instance.depot, j, k]: 1 for j in instance.customers}
        departure[z[k]] = -1
        _add_row(highs, departure, 0, 0)
        returning = {x[i, instance.depot, k]: 1 for i in instance.customers}
        returning[z[k]] = -1
        _add_row(highs, returning, 0, 0)
        capacity = {y[c, k]: instance.demands[c] for c in instance.customers}
        capacity[z[k]] = -instance.capacity
        _add_row(highs, capacity, -inf, 0)
        for customer in instance.customers:
            # q_i y_ik <= u_ik <= Q y_ik.
            _add_row(highs, {u[customer, k]: 1, y[customer, k]: -instance.demands[customer]}, 0, inf)
            _add_row(highs, {u[customer, k]: 1, y[customer, k]: -instance.capacity}, -inf, 0)
        for i in instance.customers:
            for j in instance.customers:
                if i == j:
                    continue
                # x_ijk=1 => u_jk >= u_ik + q_j; 2Q fully relaxes the
                # constraint when either per-vehicle load variable is inactive.
                _add_row(
                    highs,
                    {u[j, k]: 1, u[i, k]: -1, x[i, j, k]: -2 * instance.capacity},
                    instance.demands[j] - 2 * instance.capacity,
                    inf,
                )
    # Safe identical-vehicle symmetry breaking.
    for k in range(instance.max_vehicles - 1):
        _add_row(highs, {z[k]: 1, z[k + 1]: -1}, 0, inf)
    return HighsModelArtifacts(highs=highs, x=x, y=y, z=z, u=u)
