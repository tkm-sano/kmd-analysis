"""Non-production mathematical/evidence analysis for the R20 lambda bound."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from pathlib import Path
from typing import Any


def assignment_penalty(bits: tuple[int, ...], n: int) -> int:
    rows = [bits[i * n : (i + 1) * n] for i in range(n)]
    return sum((1 - sum(row)) ** 2 for row in rows) + sum(
        (1 - sum(rows[i][t] for i in range(n))) ** 2 for t in range(n)
    )


def travel_objective(bits: tuple[int, ...], n: int, matrix: list[list[float]]) -> float:
    rows = [bits[i * n : (i + 1) * n] for i in range(n)]
    value = sum(matrix[0][i + 1] * rows[i][0] for i in range(n))
    value += sum(
        matrix[i + 1][j + 1] * rows[i][t] * rows[j][t + 1]
        for t in range(n - 1)
        for i in range(n)
        for j in range(n)
        if i != j
    )
    value += sum(matrix[i + 1][0] * rows[i][n - 1] for i in range(n))
    return value


def route_cost(route: tuple[int, ...], matrix: list[list[float]]) -> float:
    closed = (0, *route, 0)
    return sum(matrix[left][right] for left, right in zip(closed, closed[1:]))


def exact_reference(n: int, matrix: list[list[float]]) -> tuple[float, list[tuple[int, ...]]]:
    routes = list(itertools.permutations(range(1, n + 1)))
    costs = {route: route_cost(route, matrix) for route in routes}
    optimum = min(costs.values())
    return optimum, [route for route, cost in costs.items() if math.isclose(cost, optimum, abs_tol=1e-12, rel_tol=0.0)]


def exact_lambda_critical(n: int, matrix: list[list[float]]) -> dict[str, Any]:
    """Compute the exact finite-domain threshold for evidence, not scaling."""
    feasible_optimum, optimal_routes = exact_reference(n, matrix)
    states = 2 ** (n * n)
    maximum_ratio = -math.inf
    argmax: tuple[int, ...] | None = None
    infeasible_count = 0
    max_travel = 0.0
    min_travel = math.inf
    for state in range(states):
        bits = tuple((state >> (n * n - 1 - index)) & 1 for index in range(n * n))
        penalty = assignment_penalty(bits, n)
        travel = travel_objective(bits, n, matrix)
        max_travel = max(max_travel, travel)
        min_travel = min(min_travel, travel)
        if penalty == 0:
            continue
        infeasible_count += 1
        ratio = (feasible_optimum - travel) / penalty
        if ratio > maximum_ratio:
            maximum_ratio, argmax = ratio, bits
    return {
        "n": n,
        "state_count": states,
        "feasible_optimum": feasible_optimum,
        "optimal_routes": [list(route) for route in optimal_routes],
        "infeasible_state_count": infeasible_count,
        "exact_critical_lambda": maximum_ratio,
        "critical_state": list(argmax) if argmax is not None else None,
        "arbitrary_state_travel_min": min_travel,
        "arbitrary_state_travel_max": max_travel,
        "universal_bound": (n + 1) / 2,
        "universal_bound_margin": 1e-9,
    }


def adversarial_matrix(n: int, kind: str) -> list[list[float]]:
    matrix = [[0.0 if i == j else 1.0 for j in range(n + 1)] for i in range(n + 1)]
    if kind == "all_one":
        return matrix
    if kind == "cheap_cycle":
        route = tuple(range(1, n + 1))
        for left, right in zip((0, *route), (*route, 0)):
            matrix[left][right] = 1e-9
        return matrix
    if kind == "asymmetric":
        for i in range(n + 1):
            for j in range(n + 1):
                if i != j:
                    matrix[i][j] = ((17 * i + 7 * j + 3) % 23 + 1) / 23
        return matrix
    if kind == "near_one":
        for i in range(n + 1):
            for j in range(n + 1):
                if i != j:
                    matrix[i][j] = 1.0 - ((i + 2 * j) % 5) * 1e-6
        matrix[0][1] = 1.0
        return matrix
    raise ValueError(kind)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    results = []
    for n in (2, 3, 4):
        for kind in ("all_one", "cheap_cycle", "asymmetric", "near_one"):
            result = exact_lambda_critical(n, adversarial_matrix(n, kind))
            result["fixture"] = kind
            result["bound_plus_passes_analytical_check"] = result["exact_critical_lambda"] < result["universal_bound"] + result["universal_bound_margin"]
            result["matrix"] = adversarial_matrix(n, kind)
            results.append(result)
    payload = {
        "schema_version": "r20-lambda-bound-analysis-v1",
        "status": "ANALYSIS_EVIDENCE_ONLY",
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "formal_lambda_adopted": False,
        "theorem": {
            "minimum_positive_assignment_penalty": 2,
            "arbitrary_state_travel_lower_bound": 0,
            "arbitrary_state_travel_upper_bound": "n*((n-1)**2 + 2)",
            "feasible_route_upper_bound": "n+1",
            "universal_conservative_sufficient_condition": "lambda > (n+1)/2",
            "instance_aware_sufficient_condition": "lambda > U_feasible/2 for any proven feasible route upper bound U_feasible",
        },
        "fixtures": results,
        "elapsed_seconds": time.perf_counter() - started,
        "theoretical_bound_status": "THEORETICAL_BOUND_PROVED",
        "unresolved": ["future unreachable-transition penalty bound is outside this formulation"],
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "lambda_bound_analysis.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.out),
        "fixture_count": len(results),
        "all_bound_checks": all(item["bound_plus_passes_analytical_check"] for item in results),
        "elapsed_seconds": payload["elapsed_seconds"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
