"""Non-production numerical margin analysis for the R20 lambda bound.

This module performs only exact classical enumeration.  It contains no QAOA,
Ising, optimizer, or hardware execution logic.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

from .analyze_lambda_bound import adversarial_matrix
from .core import (
    ENERGY_ABS_TOLERANCE,
    build_expanded_qubo,
    energy_equal,
    evaluate_direct_qubo,
    evaluate_expanded_qubo,
    normalize_travel_time_matrix,
    route_travel_time,
)

DELTA_CANDIDATES = [
    0.0,
    1e-12,
    1e-10,
    1e-8,
    1e-6,
    1e-4,
    1e-3,
    1e-2,
    0.05,
    0.1,
    0.2,
    0.5,
]
EPSILON_CANDIDATES = [1e-12, 1e-10, 1e-8, 1e-6, 1e-4, 1e-3, 1e-2]
SCHEMA_VERSION = "r20-lambda-margin-analysis-v1"


def validate_delta(delta: float) -> float:
    value = float(delta)
    if not math.isfinite(value) or value < 0:
        raise ValueError("delta must be finite and non-negative")
    return value


def validate_epsilon(epsilon: float) -> float:
    value = float(epsilon)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("epsilon must be finite and positive")
    return value


def lambda_from_relative_bound(bound: float, delta: float) -> float:
    if not math.isfinite(bound) or bound < 0:
        raise ValueError("bound must be finite and non-negative")
    return bound * (1.0 + validate_delta(delta))


def lambda_from_absolute_bound(bound: float, epsilon: float) -> float:
    if not math.isfinite(bound) or bound < 0:
        raise ValueError("bound must be finite and non-negative")
    return bound + validate_epsilon(epsilon)


def _iter_bits(n: int) -> Iterable[tuple[int, ...]]:
    logical = n * n
    for state in range(2**logical):
        yield tuple((state >> (logical - 1 - index)) & 1 for index in range(logical))


def _matrix_hash(matrix: dict[Any, dict[Any, float]]) -> str:
    payload = json.dumps(matrix, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_dirty() -> bool | None:
    try:
        result = subprocess.run(["git", "status", "--porcelain"], check=True, capture_output=True, text=True)
        return bool(result.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def _travel_coefficients(depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]]) -> list[float]:
    n = len(customers)
    values = [matrix[depot][customer] for customer in customers]
    values.extend(matrix[customer][depot] for customer in customers)
    values.extend(
        matrix[source][target]
        for _position in range(n - 1)
        for source in customers
        for target in customers
        if source != target
    )
    return values


def _route_optimum(depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]]) -> tuple[float, list[list[Any]]]:
    records = []
    for route in itertools.permutations(customers):
        records.append((route_travel_time(depot, route, matrix), route))
    optimum = min(cost for cost, _route in records)
    routes = [list(route) for cost, route in records if energy_equal(cost, optimum)]
    return optimum, routes


def _classify(delta: float, gap: float, noise_floor: float) -> str:
    if delta == 0.0:
        return "INVALID_EQUALITY"
    if gap <= noise_floor:
        return "THEORETICALLY_VALID_BUT_NUMERICALLY_FRAGILE"
    return "NUMERICALLY_ROBUST"


def evaluate_margin_case(
    instance_id: str,
    depot: Any,
    customers: list[Any],
    raw_matrix: dict[Any, dict[Any, float]],
    policy: str,
    bound: float,
    delta: float,
    *,
    lambda_mode: str = "relative",
    epsilon: float | None = None,
) -> dict[str, Any]:
    normalized, tau_max = normalize_travel_time_matrix(depot, customers, raw_matrix)
    n = len(customers)
    lam = lambda_from_relative_bound(bound, delta) if lambda_mode == "relative" else lambda_from_absolute_bound(bound, epsilon if epsilon is not None else 0.0)
    coefficients = build_expanded_qubo(depot, customers, normalized, lam)
    feasible_energy = math.inf
    infeasible_energy = math.inf
    feasible_routes: list[list[Any]] = []
    min_penalty = math.inf
    max_abs_difference = 0.0
    mismatch_count = 0
    max_energy_scale = 0.0
    for bits in _iter_bits(n):
        direct = evaluate_direct_qubo(bits, depot, customers, normalized, lam)
        expanded = evaluate_expanded_qubo(bits, coefficients)
        difference = abs(float(direct["qubo_energy"]) - expanded)
        max_abs_difference = max(max_abs_difference, difference)
        mismatch_count += int(not energy_equal(float(direct["qubo_energy"]), expanded))
        energy = float(direct["qubo_energy"])
        max_energy_scale = max(max_energy_scale, abs(energy))
        penalty = int(direct["total_penalty"])
        if penalty == 0:
            if energy < feasible_energy - ENERGY_ABS_TOLERANCE:
                feasible_energy = energy
                feasible_routes = []
            if energy_equal(energy, feasible_energy):
                feasible_routes.append(list(direct_route(depot, customers, bits)))
        else:
            min_penalty = min(min_penalty, penalty)
            infeasible_energy = min(infeasible_energy, energy)
    gap = infeasible_energy - feasible_energy
    relative_gap = gap / max(1.0, abs(feasible_energy), abs(infeasible_energy))
    ulp_scale = math.ulp(max(1.0, max_energy_scale))
    noise_floor = max(ENERGY_ABS_TOLERANCE, 64.0 * ulp_scale, 10.0 * max_abs_difference)
    travel_values = _travel_coefficients(depot, customers, normalized)
    penalty_abs = 2.0 * lam
    return {
        "instance_id": instance_id,
        "n": n,
        "n_logical": n * n,
        "state_count": 2 ** (n * n),
        "matrix_sha256": _matrix_hash(raw_matrix),
        "input_scale": "normalized",
        "tau_max_raw": tau_max,
        "policy": policy,
        "bound": bound,
        "delta": delta,
        "epsilon": epsilon,
        "lambda_mode": lambda_mode,
        "lambda": lam,
        "minimum_feasible_energy": feasible_energy,
        "minimum_infeasible_energy": infeasible_energy,
        "energy_separation": gap,
        "relative_gap": relative_gap,
        "minimum_infeasible_penalty": min_penalty,
        "feasible_routes_at_minimum": feasible_routes,
        "infeasible_feasible_tie": energy_equal(infeasible_energy, feasible_energy),
        "all_global_minima_feasible": infeasible_energy > feasible_energy + ENERGY_ABS_TOLERANCE,
        "direct_expanded_max_abs_difference": max_abs_difference,
        "direct_expanded_mismatch_count": mismatch_count,
        "numeric_noise_floor": noise_floor,
        "classification": _classify(delta, gap, noise_floor),
        "coefficient_scales": {
            "max_abs_linear": max(abs(value) for value in coefficients.linear.values()),
            "max_abs_quadratic": max(abs(value) for value in coefficients.quadratic.values()),
            "travel_coefficient_min_positive": min(value for value in travel_values if value > 0),
            "travel_coefficient_max": max(travel_values),
            "penalty_coefficient_abs": penalty_abs,
            "penalty_to_max_travel_ratio": penalty_abs / max(travel_values),
            "penalty_to_min_positive_travel_ratio": penalty_abs / min(value for value in travel_values if value > 0),
        },
    }


def direct_route(depot: Any, customers: list[Any], bits: tuple[int, ...]) -> tuple[Any, ...]:
    n = len(customers)
    rows = [bits[i * n : (i + 1) * n] for i in range(n)]
    return tuple(customers[next(i for i in range(n) if rows[i][position])] for position in range(n))


def synthetic_margin_fixtures() -> list[tuple[str, int, list[int], dict[int, dict[int, float]]]]:
    return [
        (f"adversarial_n{n}_{kind}", 0, list(range(1, n + 1)), {i: {j: value for j, value in enumerate(row)} for i, row in enumerate(adversarial_matrix(n, kind))})
        for n in (2, 3, 4)
        for kind in ("all_one", "cheap_cycle", "asymmetric", "near_one")
    ]


def load_real_margin_fixtures(path: Path) -> list[tuple[str, Any, list[Any], dict[Any, dict[Any, float]]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = []
    for subset in data["subsets"]:
        input_data = subset["adapter"]["input"]
        nodes = input_data["node_set"]
        matrix = {node: {} for node in nodes}
        for edge in input_data["raw_directed_edges"]:
            matrix[edge["origin_id"]][edge["destination_id"]] = float(edge["travel_time_s"])
        for node in nodes:
            matrix[node][node] = 0.0
        fixtures.append((subset["subset_id"], input_data["depot_id"], input_data["customer_ids"], matrix))
    return fixtures


def _prepare_state_features(depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]]) -> list[dict[str, Any]]:
    """Compute the state-dependent terms once; lambda sweeps reuse these values."""
    normalized, _tau_max = normalize_travel_time_matrix(depot, customers, matrix)
    n = len(customers)
    features = []
    for bits in _iter_bits(n):
        rows = [bits[i * n : (i + 1) * n] for i in range(n)]
        customer_penalty = sum((1 - sum(row)) ** 2 for row in rows)
        position_penalty = sum((1 - sum(rows[i][t] for i in range(n))) ** 2 for t in range(n))
        travel = sum(normalized[depot][customers[i]] * rows[i][0] for i in range(n))
        travel += sum(
            normalized[customers[i]][customers[j]] * rows[i][t] * rows[j][t + 1]
            for t in range(n - 1)
            for i in range(n)
            for j in range(n)
            if i != j
        )
        travel += sum(normalized[customers[i]][depot] * rows[i][n - 1] for i in range(n))
        feature = {"bits": bits, "travel": travel, "penalty": customer_penalty + position_penalty}
        if feature["penalty"] == 0:
            feature["route"] = list(direct_route(depot, customers, bits))
        features.append(feature)
    return features


def _direct_expanded_check(
    depot: Any,
    customers: list[Any],
    matrix: dict[Any, dict[Any, float]],
    lam: float,
    *,
    stride: int = 1,
) -> tuple[float, int, int]:
    normalized, _tau_max = normalize_travel_time_matrix(depot, customers, matrix)
    coefficients = build_expanded_qubo(depot, customers, normalized, lam)
    states = 2 ** (len(customers) ** 2)
    max_difference = 0.0
    mismatch_count = 0
    checked = 0
    for state_index, bits in enumerate(_iter_bits(len(customers))):
        if state_index % stride:
            continue
        direct = evaluate_direct_qubo(bits, depot, customers, normalized, lam)["qubo_energy"]
        expanded = evaluate_expanded_qubo(bits, coefficients)
        difference = abs(float(direct) - expanded)
        max_difference = max(max_difference, difference)
        mismatch_count += int(not energy_equal(float(direct), expanded))
        checked += 1
    return max_difference, mismatch_count, checked


def _batch_cases(
    instance_id: str,
    depot: Any,
    customers: list[Any],
    raw_matrix: dict[Any, dict[Any, float]],
    features: list[dict[str, Any]],
    policy: str,
    bound: float,
    *,
    lambda_mode: str,
    values: list[float],
    expanded_check: tuple[float, int, int],
    tau_max: float,
) -> list[dict[str, Any]]:
    feasible_base = min(item["travel"] for item in features if item["penalty"] == 0)
    travel_values = _travel_coefficients(depot, customers, normalize_travel_time_matrix(depot, customers, raw_matrix)[0])
    output = []
    for value in values:
        lam = lambda_from_relative_bound(bound, value) if lambda_mode == "relative" else lambda_from_absolute_bound(bound, value)
        energies = [(item["travel"] + lam * item["penalty"], item) for item in features]
        feasible_energy = min(energy for energy, item in energies if item["penalty"] == 0)
        infeasible_energy = min(energy for energy, item in energies if item["penalty"] > 0)
        feasible_routes = [item["route"] for energy, item in energies if item["penalty"] == 0 and energy_equal(energy, feasible_energy)]
        max_energy_scale = max(abs(energy) for energy, _item in energies)
        gap = infeasible_energy - feasible_energy
        relative_gap = gap / max(1.0, abs(feasible_energy), abs(infeasible_energy))
        ulp_scale = math.ulp(max(1.0, max_energy_scale))
        max_difference, mismatch_count, checked_states = expanded_check
        noise_floor = max(ENERGY_ABS_TOLERANCE, 64.0 * ulp_scale, 10.0 * max_difference)
        output.append({
            "instance_id": instance_id,
            "n": len(customers),
            "n_logical": len(customers) ** 2,
            "state_count": 2 ** (len(customers) ** 2),
            "matrix_sha256": _matrix_hash(raw_matrix),
            "input_scale": "normalized",
            "tau_max_raw": tau_max,
            "policy": policy,
            "bound": bound,
            "delta": value if lambda_mode == "relative" else 0.0,
            "epsilon": value if lambda_mode == "absolute" else None,
            "lambda_mode": lambda_mode,
            "lambda": lam,
            "minimum_feasible_energy": feasible_energy,
            "minimum_infeasible_energy": infeasible_energy,
            "energy_separation": gap,
            "relative_gap": relative_gap,
            "minimum_infeasible_penalty": min(item["penalty"] for item in features if item["penalty"] > 0),
            "feasible_routes_at_minimum": feasible_routes,
            "infeasible_feasible_tie": energy_equal(infeasible_energy, feasible_energy),
            "all_global_minima_feasible": infeasible_energy > feasible_energy + ENERGY_ABS_TOLERANCE,
            "direct_expanded_max_abs_difference": max_difference,
            "direct_expanded_mismatch_count": mismatch_count,
            "direct_expanded_checked_states": checked_states,
            "numeric_noise_floor": noise_floor,
            "classification": _classify(value if lambda_mode == "relative" else 1.0, gap, noise_floor),
            "coefficient_scales": {
                "max_abs_linear": max(2.0 * lam, max(travel_values)),
                "max_abs_quadratic": max(2.0 * lam, max(travel_values)),
                "travel_coefficient_min_positive": min(value for value in travel_values if value > 0),
                "travel_coefficient_max": max(travel_values),
                "penalty_coefficient_abs": 2.0 * lam,
                "penalty_to_max_travel_ratio": 2.0 * lam / max(travel_values),
                "penalty_to_min_positive_travel_ratio": 2.0 * lam / min(value for value in travel_values if value > 0),
            },
            "feasible_base_travel_objective": feasible_base,
        })
    return output


def analyze(out: Path, real_artifact: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    fixtures = synthetic_margin_fixtures()
    if real_artifact is not None:
        fixtures.extend(load_real_margin_fixtures(real_artifact))
    cases = []
    for instance_id, depot, customers, raw_matrix in fixtures:
        normalized, _tau_max = normalize_travel_time_matrix(depot, customers, raw_matrix)
        route_costs = [route_travel_time(depot, route, normalized) for route in itertools.permutations(customers)]
        instance_bound = route_costs[0] / 2.0
        bounds = [("universal", (len(customers) + 1) / 2.0), ("instance_aware", instance_bound)]
        features = _prepare_state_features(depot, customers, raw_matrix)
        # Existing R20 evidence is exhaustive for n=2/n=3.  For n=4 this
        # analysis checks a deterministic 4096-state subset to keep the
        # margin sweep bounded; the direct objective sweep still covers all states.
        stride = 1 if len(customers) <= 3 else max(1, (2 ** (len(customers) ** 2)) // 4096)
        expanded_check = _direct_expanded_check(depot, customers, raw_matrix, 1.0, stride=stride)
        for policy, bound in bounds:
            cases.extend(_batch_cases(instance_id, depot, customers, raw_matrix, features, policy, bound, lambda_mode="relative", values=DELTA_CANDIDATES, expanded_check=expanded_check, tau_max=_tau_max))
            cases.extend(_batch_cases(instance_id, depot, customers, raw_matrix, features, policy, bound, lambda_mode="absolute", values=EPSILON_CANDIDATES, expanded_check=expanded_check, tau_max=_tau_max))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "MARGIN_ANALYSIS_EVIDENCE_ONLY",
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "formal_lambda_adopted": False,
        "source_commit": _source_commit(),
        "source_worktree_dirty": _git_dirty(),
        "source_hashes": {
            "analyze_lambda_margin.py": _file_hash(Path(__file__)),
            "core.py": _file_hash(Path(__file__).parent / "core.py"),
            "R20_QAOA_SUBPROBLEM_SPEC.md": _file_hash(Path(__file__).resolve().parents[3] / "05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md"),
        },
        "software": {"python": platform.python_version(), "implementation": SCHEMA_VERSION},
        "bound_policies": {
            "universal": "B=(n+1)/2",
            "instance_aware": "B=U_feasible/2 using the first deterministic customer permutation as U_feasible",
        },
        "relative_delta_candidates": DELTA_CANDIDATES,
        "absolute_epsilon_candidates": EPSILON_CANDIDATES,
        "classification_criteria": {
            "INVALID_EQUALITY": "delta=0 equality baseline; no general guarantee",
            "THEORETICALLY_VALID_BUT_NUMERICALLY_FRAGILE": "positive delta but measured gap <= max(1e-12, 64 ulp energy scale, 10 direct-expanded error)",
            "NUMERICALLY_ROBUST": "positive delta and measured gap exceeds the declared noise floor",
            "ROBUST_BUT_UNNECESSARILY_CONSERVATIVE": "not assigned automatically; requires separate scaling decision",
            "direct_expanded_scope": "exhaustive for n<=3; deterministic 4096-state check for n=4 in this margin artifact; existing v12 artifact remains the exhaustive n=2/n=3 authority",
        },
        "authoritative_evidence_checked": {
            "synthetic": "reproducibility/outputs/traffic_simulation/r20_exact_validation/20260910_corrected_expanded_qubo_v12/validation_results.json",
            "real_data": "reproducibility/outputs/traffic_simulation/r20_real_data_validation/20260910_complete_reachability_v10/validation_results.json",
            "bound_analysis": "reproducibility/outputs/traffic_simulation/r20_lambda_bound_analysis/20260910_adversarial_v8/lambda_bound_analysis.json",
        },
        "fixtures": cases,
        "elapsed_seconds": time.perf_counter() - started,
        "recommendation_status": "MARGIN_POLICY_RECOMMENDED",
        "recommendation": {
            "policy": "B",
            "text": "Use a tolerance-aware relative margin only after recording the bound, numerical noise floor, and selected margin; no numeric delta is formally adopted by this artifact.",
            "smallest_observed_robust_delta": min((case["delta"] for case in cases if case["lambda_mode"] == "relative" and case["classification"] == "NUMERICALLY_ROBUST"), default=None),
            "empirical_only": True,
        },
    }
    out.mkdir(parents=True, exist_ok=False)
    results_path = out / "lambda_margin_analysis.json"
    results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "source_commit": payload["source_commit"],
        "source_worktree_dirty": payload["source_worktree_dirty"],
        "files": {"lambda_margin_analysis.json": _file_hash(results_path)},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--real-artifact", type=Path)
    args = parser.parse_args()
    payload = analyze(args.out, args.real_artifact)
    print(json.dumps({"output": str(args.out), "cases": len(payload["fixtures"]), "status": payload["recommendation_status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
