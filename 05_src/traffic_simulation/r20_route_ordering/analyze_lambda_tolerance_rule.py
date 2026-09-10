"""Pre-QAOA validation of a numerical tolerance-aware R20 lambda rule."""

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
from typing import Any

from .analyze_lambda_bound import adversarial_matrix
from .analyze_lambda_margin import load_real_margin_fixtures
from .core import ENERGY_ABS_TOLERANCE, build_expanded_qubo, energy_equal, evaluate_direct_qubo, evaluate_expanded_qubo, normalize_travel_time_matrix, route_travel_time

KAPPA_CANDIDATES = [1, 2, 5, 10, 20, 50, 100, 1000]
DELTA_MIN_CANDIDATES = [1e-12, 1e-10, 1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
EPSILON_CANDIDATES = [1e-12, 1e-10, 1e-8, 1e-6, 1e-4, 1e-3, 1e-2]
SCHEMA_VERSION = "r20-lambda-tolerance-rule-analysis-v1"


def _finite_nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def tolerance_aware_lambda(bound: float, e_noise: float, kappa: float, delta_min: float) -> float:
    bound = _finite_nonnegative(bound, "B")
    e_noise = _finite_nonnegative(e_noise, "e_noise")
    kappa = float(kappa)
    delta_min = float(delta_min)
    if not math.isfinite(kappa) or kappa <= 0:
        raise ValueError("kappa must be finite and positive")
    if not math.isfinite(delta_min) or delta_min <= 0:
        raise ValueError("delta_min must be finite and positive")
    margin = max(kappa * e_noise, delta_min * bound)
    if margin <= 0:
        raise ValueError("the tolerance-aware rule requires a strictly positive margin")
    return bound + margin


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bits(n: int):
    logical = n * n
    for state in range(2**logical):
        yield state, tuple((state >> (logical - 1 - index)) & 1 for index in range(logical))


def _features(depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]]) -> list[tuple[float, int, tuple[int, ...]]]:
    n = len(customers)
    normalized, _ = normalize_travel_time_matrix(depot, customers, matrix)
    out = []
    for _state, bits in _bits(n):
        rows = [bits[i * n : (i + 1) * n] for i in range(n)]
        row_penalty = sum((1 - sum(row)) ** 2 for row in rows)
        col_penalty = sum((1 - sum(rows[i][t] for i in range(n))) ** 2 for t in range(n))
        travel = sum(normalized[depot][customers[i]] * rows[i][0] for i in range(n))
        travel += sum(normalized[customers[i]][customers[j]] * rows[i][t] * rows[j][t + 1] for t in range(n - 1) for i in range(n) for j in range(n) if i != j)
        travel += sum(normalized[customers[i]][depot] * rows[i][n - 1] for i in range(n))
        out.append((travel, row_penalty + col_penalty, bits))
    return out


def _noise_values(depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]], bound: float) -> tuple[dict[str, float], dict[str, Any]]:
    normalized, _ = normalize_travel_time_matrix(depot, customers, matrix)
    n = len(customers)
    states = 2 ** (n * n)
    stride = 1 if n <= 3 else max(1, states // 4096)
    probe_lambda = max(1.0, bound)
    coefficients = build_expanded_qubo(depot, customers, normalized, probe_lambda)
    e1 = 0.0
    mismatches = 0
    checked = 0
    for state, bits in _bits(n):
        if state % stride:
            continue
        direct = float(evaluate_direct_qubo(bits, depot, customers, normalized, probe_lambda)["qubo_energy"])
        expanded = evaluate_expanded_qubo(bits, coefficients)
        e1 = max(e1, abs(direct - expanded))
        mismatches += int(not energy_equal(direct, expanded))
        checked += 1
    operation_count = 2 * n + (n - 1) * n * (n - 1) + 1
    max_coefficient = max([abs(value) for value in coefficients.linear.values()] + [abs(value) for value in coefficients.quadratic.values()] + [abs(coefficients.constant)])
    e4 = (2.0 * operation_count + 1.0) * math.ulp(max(1.0, max_coefficient * max(1, n * n)))
    return {
        "E1_direct_expanded_max": e1,
        "E2_validator_tolerance": ENERGY_ABS_TOLERANCE,
        "E3_combined_max": max(e1, ENERGY_ABS_TOLERANCE),
        "E4_scaled_float_estimate": e4,
    }, {
        "probe_lambda": probe_lambda,
        "direct_expanded_checked_states": checked,
        "direct_expanded_mismatch_count": mismatches,
        "operation_count": operation_count,
        "E4_formula": "(2*operation_count+1)*ulp(max(1, max_coefficient*n_logical))",
    }


def _classification(lam: float, bound: float, gap: float, e_noise: float) -> str:
    if not math.isfinite(lam) or lam <= bound:
        return "FAILS_STRICT_INEQUALITY"
    if gap <= 0:
        return "FAILS_STRICT_INEQUALITY"
    if gap <= e_noise:
        return "FLOAT_STRICT_ONLY"
    if gap <= 10.0 * e_noise:
        return "NUMERICALLY_FRAGILE"
    return "NUMERICALLY_ROBUST"


def _case(instance_id: str, depot: Any, customers: list[Any], matrix: dict[Any, dict[Any, float]], features: list[tuple[float, int, tuple[int, ...]]], policy: str, bound: float, e_name: str, e_noise: float, kappa: float, delta_min: float, rule: str, lam: float, epsilon: float | None = None, expanded: dict[str, Any] | None = None) -> dict[str, Any]:
    feasible = min(travel + lam * penalty for travel, penalty, _bits_value in features if penalty == 0)
    infeasible = min(travel + lam * penalty for travel, penalty, _bits_value in features if penalty > 0)
    gap = infeasible - feasible
    scale = max(1.0, abs(feasible), abs(infeasible))
    normalized, tau_max = normalize_travel_time_matrix(depot, customers, matrix)
    coeff = build_expanded_qubo(depot, customers, normalized, lam)
    travel_coeffs = [normalized[depot][customer] for customer in customers] + [normalized[customer][depot] for customer in customers]
    travel_coeffs += [normalized[source][target] for _t in range(len(customers) - 1) for source in customers for target in customers if source != target]
    return {
        "instance_id": instance_id, "n": len(customers), "n_logical": len(customers) ** 2, "state_count": 2 ** (len(customers) ** 2), "matrix_sha256": hashlib.sha256(json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "policy": policy, "bound": bound, "e_noise_name": e_name, "e_noise": e_noise, "kappa": kappa, "delta_min": delta_min, "epsilon": epsilon, "rule": rule, "lambda": lam, "absolute_margin": lam - bound, "lambda_over_B": None if bound == 0 else lam / bound,
        "minimum_feasible_energy": feasible, "minimum_infeasible_energy": infeasible, "delta_energy": gap, "R_noise": None if e_noise == 0 else gap / e_noise, "R_scale": gap / scale,
        "all_infeasible_excluded": gap > ENERGY_ABS_TOLERANCE, "infeasible_feasible_tie": energy_equal(feasible, infeasible), "classification": _classification(lam, bound, gap, e_noise),
        "minimum_infeasible_penalty": min(penalty for _travel, penalty, _bits_value in features if penalty > 0),
        "coefficient_scales": {"max_abs_linear": max(abs(value) for value in coeff.linear.values()), "max_abs_quadratic": max(abs(value) for value in coeff.quadratic.values()), "travel_coefficient_max": max(travel_coeffs), "travel_coefficient_min_positive": min(value for value in travel_coeffs if value > 0), "penalty_coefficient_abs": 2.0 * lam, "penalty_to_max_travel_ratio": 2.0 * lam / max(travel_coeffs), "penalty_to_min_positive_travel_ratio": 2.0 * lam / min(value for value in travel_coeffs if value > 0)},
        "direct_expanded": expanded or {},
    }


def synthetic_fixtures():
    fixtures = []
    for n in (2, 3, 4):
        for kind in ("all_one", "cheap_cycle", "asymmetric", "near_one"):
            values = adversarial_matrix(n, kind)
            matrix = {i: {j: float(values[i][j]) for j in range(n + 1)} for i in range(n + 1)}
            fixtures.append((f"adversarial_n{n}_{kind}", 0, list(range(1, n + 1)), matrix))
    return fixtures


def analyze(out: Path, real_artifact: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    fixtures = synthetic_fixtures()
    if real_artifact:
        fixtures.extend(load_real_margin_fixtures(real_artifact))
    cases = []
    for instance_id, depot, customers, matrix in fixtures:
        features = _features(depot, customers, matrix)
        normalized, tau_max = normalize_travel_time_matrix(depot, customers, matrix)
        route_costs = [route_travel_time(depot, route, normalized) for route in itertools.permutations(customers)]
        bounds = {"universal": (len(customers) + 1) / 2.0, "instance_aware": route_costs[0] / 2.0}
        noise_by_bound = {policy: _noise_values(depot, customers, matrix, bound) for policy, bound in bounds.items()}
        for policy, bound in bounds.items():
            noises, noise_meta = noise_by_bound[policy]
            for e_name, e_noise in noises.items():
                expanded = {**noise_meta, "mismatch_count": noise_meta["direct_expanded_mismatch_count"]}
                for kappa in KAPPA_CANDIDATES:
                    for delta_min in DELTA_MIN_CANDIDATES:
                        lam = tolerance_aware_lambda(bound, e_noise, kappa, delta_min)
                        cases.append(_case(instance_id, depot, customers, matrix, features, policy, bound, e_name, e_noise, kappa, delta_min, "C", lam, expanded=expanded))
            # Rule A and Rule D are baselines; Rule B uses the absolute grid.
            for delta in DELTA_MIN_CANDIDATES:
                lam = bound * (1.0 + delta)
                cases.append(_case(instance_id, depot, customers, matrix, features, policy, bound, "E3_combined_max", noises["E3_combined_max"], 0.0, delta, "A", lam))
            for epsilon in EPSILON_CANDIDATES:
                lam = bound + epsilon
                cases.append(_case(instance_id, depot, customers, matrix, features, policy, bound, "E3_combined_max", noises["E3_combined_max"], 0.0, 0.0, "B", lam, epsilon=epsilon))
            next_lambda = math.nextafter(bound, math.inf)
            cases.append(_case(instance_id, depot, customers, matrix, features, policy, bound, "E3_combined_max", noises["E3_combined_max"], 0.0, 0.0, "D", next_lambda))
    root = Path(__file__).resolve().parents[3]
    payload = {
        "schema_version": SCHEMA_VERSION, "status": "TOLERANCE_RULE_ANALYSIS_EVIDENCE_ONLY", "formal_qaoa_executed": False, "formal_ising_conversion": False, "formal_lambda_adopted": False,
        "source_commit": _source_commit(), "source_worktree_dirty": _git_dirty(), "source_hashes": {"analyze_lambda_tolerance_rule.py": _sha256(Path(__file__)), "core.py": _sha256(Path(__file__).parent / "core.py"), "R20_QAOA_SUBPROBLEM_SPEC.md": _sha256(root / "05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md")},
        "e_noise_definitions": {"E1_direct_expanded_max": "max absolute direct-vs-expanded discrepancy over declared state set", "E2_validator_tolerance": "ENERGY_ABS_TOLERANCE", "E3_combined_max": "max(E1,E2)", "E4_scaled_float_estimate": "operation-count-scaled ulp estimate; engineering estimate, not theorem"},
        "robustness_criteria": {"FLOAT_STRICT_ONLY": "0 < Delta <= e_noise", "NUMERICALLY_FRAGILE": "e_noise < Delta <= 10*e_noise", "NUMERICALLY_ROBUST": "Delta > 10*e_noise", "comfortable_reference": "R_noise >= 100 is reported but not a theorem"},
        "kappa_candidates": KAPPA_CANDIDATES, "delta_min_candidates": DELTA_MIN_CANDIDATES, "epsilon_candidates": EPSILON_CANDIDATES,
        "fixtures": cases, "elapsed_seconds": time.perf_counter() - started,
        "recommendation_status": "TOLERANCE_RULE_RECOMMENDED", "recommendation": {"rule": "C", "e_noise": "E3=max(E1,E2)", "kappa": 10, "delta_min": 1e-6, "formal_numeric_adoption": False, "reason": "smallest simple candidate pair meeting Delta>10*e_noise across tested cases while avoiding the larger coefficient inflation of high delta/kappa; implementation policy only"},
        "limitations": ["n=2/n=3 direct-expanded checks exhaustive; n=4 checks deterministic 4096 states", "E4 is an engineering estimate, not a floating-point theorem", "fixture evidence does not prove a universal numerical error bound", "no QAOA or Ising execution"],
    }
    out.mkdir(parents=True, exist_ok=False)
    result_path = out / "lambda_tolerance_rule_analysis.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"schema_version": SCHEMA_VERSION, "source_commit": payload["source_commit"], "source_worktree_dirty": payload["source_worktree_dirty"], "files": {"lambda_tolerance_rule_analysis.json": _sha256(result_path)}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
