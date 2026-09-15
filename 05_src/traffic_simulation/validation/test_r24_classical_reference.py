from __future__ import annotations

import pytest

from traffic_simulation.r24_classical_reference.r24_cvrp_model import Arc, CVRPInstance, validate_instance
from traffic_simulation.r24_classical_reference.r24_exact_reference import solve_exact
from traffic_simulation.r24_classical_reference.r24_highs_solver import solve_highs
from traffic_simulation.r24_classical_reference.r24_solution_validator import validate_routes


def fixture(
    demands: dict[str, int] | None = None,
    max_vehicles: int = 1,
    zero_ab: bool = False,
) -> CVRPInstance:
    demands = demands or {"A": 1, "B": 1}
    customers = tuple(demands)
    nodes = ("DEP_006", *customers)
    arcs: dict[tuple[str, str], Arc] = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            time = 10.0
            if (i, j) == ("DEP_006", "A"):
                time = 2.0
            elif (i, j) == ("A", "DEP_006"):
                time = 2.0
            elif (i, j) == ("DEP_006", "B"):
                time = 3.0
            elif (i, j) == ("B", "DEP_006"):
                time = 3.0
            elif (i, j) == ("A", "B"):
                time = 0.0 if zero_ab else 1.0
            elif (i, j) == ("B", "A"):
                time = 4.0
            arcs[i, j] = Arc(time, time, zero_proxy=zero_ab and (i, j) == ("A", "B"))
    return CVRPInstance("FIXTURE", "FIXTURE-RHO", "UNIT_TEST", customers, demands, arcs, max_vehicles, 0.5, 0.5)


def test_exact_known_optimum_and_asymmetric_directed_costs() -> None:
    result = solve_exact(fixture())
    assert result.status == "OPTIMAL"
    assert result.objective == pytest.approx(6.0)
    assert result.routes == (("DEP_006", "A", "B", "DEP_006"),)


def test_exact_and_highs_fixture_agree_and_validate() -> None:
    instance = fixture()
    exact = solve_exact(instance)
    highs = solve_highs(instance)
    assert highs.status == "OPTIMAL"
    assert highs.objective == pytest.approx(exact.objective)
    validation = validate_routes(instance, highs.decoded.routes, highs.objective, highs.decoded.errors)
    assert validation.status == "VALID_SOLUTION"
    assert validation.objective_difference <= 1e-7


def test_zero_cost_duplicate_proxy_like_customers_remain_distinct() -> None:
    instance = fixture(zero_ab=True)
    exact = solve_exact(instance)
    highs = solve_highs(instance)
    assert exact.objective == pytest.approx(5.0)
    assert highs.objective == pytest.approx(exact.objective)
    validation = validate_routes(instance, highs.decoded.routes, highs.objective, highs.decoded.errors)
    assert validation.status == "VALID_SOLUTION"
    assert set(highs.decoded.routes[0][1:-1]) == {"A", "B"}


def test_capacity_binding_requires_multiple_vehicles_but_at_most_m_allows_unused() -> None:
    instance = fixture({"A": 8, "B": 8}, max_vehicles=3)
    exact = solve_exact(instance)
    highs = solve_highs(instance)
    validation = validate_routes(instance, highs.decoded.routes, highs.objective, highs.decoded.errors)
    assert exact.status == highs.status == "OPTIMAL"
    assert validation.status == "VALID_SOLUTION"
    assert validation.used_vehicles == 2
    assert validation.used_vehicles < instance.max_vehicles
    assert all(load <= 14 for load in validation.route_loads)


def test_infeasible_capacity_fixture() -> None:
    instance = fixture({"A": 8, "B": 8}, max_vehicles=1)
    assert solve_exact(instance).status == "INFEASIBLE"
    assert solve_highs(instance).status == "PROVEN_INFEASIBLE"


@pytest.mark.parametrize(
    "routes, expected_fragment",
    [
        (("DEP_006", "A", "DEP_006"), "missing customers"),
        (("DEP_006", "A", "B", "A", "DEP_006"), "duplicate service"),
        (("A", "B", "DEP_006"), "invalid depot endpoints"),
    ],
)
def test_validator_rejects_corrupted_customer_once_and_depot(routes, expected_fragment) -> None:
    result = validate_routes(fixture(), (routes,))
    assert result.status == "INVALID_SOLUTION"
    assert any(expected_fragment in error for error in result.errors)


def test_validator_rejects_capacity_and_fleet_violations() -> None:
    capacity = validate_routes(fixture({"A": 8, "B": 8}), (("DEP_006", "A", "B", "DEP_006"),))
    assert capacity.status == "INVALID_SOLUTION"
    assert any("capacity" in error for error in capacity.errors)
    fleet = validate_routes(
        fixture(max_vehicles=1),
        (("DEP_006", "A", "DEP_006"), ("DEP_006", "B", "DEP_006")),
    )
    assert fleet.status == "INVALID_SOLUTION"
    assert any("AT_MOST_M" in error for error in fleet.errors)


def test_validator_recomputes_and_rejects_false_objective() -> None:
    instance = fixture()
    result = validate_routes(instance, (("DEP_006", "A", "B", "DEP_006"),), reported_objective=99)
    assert result.objective == pytest.approx(6)
    assert result.status == "INVALID_SOLUTION"
    assert result.objective_difference == pytest.approx(93)


def test_input_validator_rejects_missing_arc() -> None:
    instance = fixture()
    arcs = dict(instance.arcs)
    del arcs["A", "B"]
    broken = CVRPInstance(**{**instance.__dict__, "arcs": arcs})
    with pytest.raises(ValueError, match="missing arc"):
        validate_instance(broken)
