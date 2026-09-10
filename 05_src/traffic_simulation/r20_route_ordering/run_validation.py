#!/usr/bin/env python3
"""Generate exact formulation evidence on deterministic synthetic instances."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from .core import (
    ENERGY_ABS_TOLERANCE,
    encode_route,
    energy_equal,
    enumerate_qubo_states,
    enumerate_routes,
    normalize_travel_time_matrix,
)

LAMBDA_CANDIDATES = [0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
SCHEMA_VERSION = "r20-reduced-route-ordering-exact-validation-v2"


def matrix(nodes: list[int], values: list[list[int]]) -> dict[int, dict[int, float]]:
    return {a: {b: float(values[i][j]) for j, b in enumerate(nodes)} for i, a in enumerate(nodes)}


def synthetic_instances() -> list[tuple[str, int, list[int], dict[int, dict[int, float]]]]:
    n2 = [[0, 1, 8], [7, 0, 1], [1, 7, 0]]
    n3_unique = [[0, 1, 9, 9], [9, 0, 1, 9], [9, 9, 0, 1], [1, 9, 9, 0]]
    n3_tie = [[0, 1, 1, 1], [1, 0, 2, 2], [1, 2, 0, 2], [1, 2, 2, 0]]
    n3_mutation = [[0, 4, 9, 3], [3, 0, 8, 1], [15, 3, 0, 5], [1, 5, 2, 0]]
    return [
        ("synthetic_n2_unique", 0, [1, 2], matrix([0, 1, 2], n2)),
        ("synthetic_n3_unique", 0, [1, 2, 3], matrix([0, 1, 2, 3], n3_unique)),
        ("synthetic_n3_tie", 0, [1, 2, 3], matrix([0, 1, 2, 3], n3_tie)),
        ("synthetic_n3_asymmetric_mutation", 0, [1, 2, 3], matrix([0, 1, 2, 3], n3_mutation)),
    ]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_worktree_dirty() -> bool | None:
    try:
        result = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], check=True, capture_output=True, text=True)
        return bool(result.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def independent_penalties(bits: list[int], n: int) -> tuple[int, int]:
    customer = sum((1 - sum(bits[i * n:(i + 1) * n])) ** 2 for i in range(n))
    position = sum((1 - sum(bits[i * n + t] for i in range(n))) ** 2 for t in range(n))
    return customer, position


def run_instance(instance_id: str, depot: int, customers: list[int], raw_matrix: dict[int, dict[int, float]], lambdas: list[float] = LAMBDA_CANDIDATES) -> dict[str, Any]:
    normalized, tau_max = normalize_travel_time_matrix(depot, customers, raw_matrix)
    raw_reference = enumerate_routes(depot, customers, raw_matrix)
    normalized_reference = enumerate_routes(depot, customers, normalized)
    raw_optimal = {tuple(route[1:-1]) for route in raw_reference["optimal_routes"]}
    normalized_optimal = {tuple(route[1:-1]) for route in normalized_reference["optimal_routes"]}
    results = []
    for lam in lambdas:
        qubo = enumerate_qubo_states(depot, customers, normalized, lam)
        best_feasible = qubo["best_feasible_states"]
        customer_ok = all(r["customer_penalty"] == independent_penalties(r["bitstring"], len(customers))[0] for r in qubo["records"])
        position_ok = all(r["position_penalty"] == independent_penalties(r["bitstring"], len(customers))[1] for r in qubo["records"])
        roundtrip_ok = all(tuple(r["bitstring"]) == encode_route(r["decoded_customer_sequence"], customers) for r in qubo["records"] if r["feasibility"])
        results.append({
            "lambda": lam,
            "input_scale": "normalized",
            "qubo_cost_scale": "tau_tilde=tau/tau_max",
            "state_count": qubo["state_count"],
            "n_logical": qubo["n_logical"],
            "runtime_seconds": qubo["metadata"]["elapsed_seconds"],
            "energy_abs_tolerance": ENERGY_ABS_TOLERANCE,
            "global_minimum_energy": qubo["global_minimum_energy"],
            "all_global_minima_feasible": qubo["all_global_minima_feasible"],
            "global_minimum_bitstrings": qubo["global_minimum_bitstrings"],
            "best_feasible_energy": qubo["best_feasible_energy"],
            "best_infeasible_energy": qubo["best_infeasible_energy"],
            "best_feasible_route_objective": min(float(r["travel_objective"]) for r in best_feasible),
            "best_feasible_decoded_routes": [r["decoded_route"] for r in best_feasible],
            "direct_expanded_max_abs_difference": qubo["direct_expanded_max_abs_difference"],
            "direct_expanded_mismatch_count": qubo["direct_expanded_mismatch_count"],
            "checks": {
                "all_global_minima_feasible": qubo["all_global_minima_feasible"],
                "qubo_route_optimum_matches_original": all(energy_equal(float(r["travel_objective"]), normalized_reference["best_route_travel_time"]) for r in best_feasible),
                "no_infeasible_state_below_best_feasible": qubo["best_infeasible_energy"] >= qubo["best_feasible_energy"] - ENERGY_ABS_TOLERANCE,
                "customer_penalty_correct": customer_ok,
                "position_penalty_correct": position_ok,
                "decode_roundtrip_valid": roundtrip_ok,
                "normalization_preserves_route_ranking": raw_optimal == normalized_optimal,
                "direct_expanded_energy_match": qubo["direct_expanded_mismatch_count"] == 0,
            },
            "records": qubo["records"],
        })
    return {
        "instance_id": instance_id,
        "depot": depot,
        "customer_ids": customers,
        "n": len(customers),
        "n_logical": len(customers) ** 2,
        "raw_travel_time_matrix": raw_matrix,
        "raw_matrix_sha256": sha256_bytes(canonical_json(raw_matrix)),
        "tau_max": tau_max,
        "raw_optimum": raw_reference["best_route_travel_time"],
        "raw_optimal_routes": raw_reference["optimal_routes"],
        "normalized_optimum": normalized_reference["best_route_travel_time"],
        "normalized_optimal_routes": normalized_reference["optimal_routes"],
        "original_enumeration_count": raw_reference["evaluated_permutations"],
        "original_enumeration_runtime_seconds": raw_reference["metadata"]["elapsed_seconds"],
        "lambda_candidate_reason": "fixed monotone validation grid; no formal lambda adopted",
        "lambda_results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("reproducibility/outputs/traffic_simulation/r20_exact_validation/20260910_corrected_expanded_qubo_v5"))
    args = parser.parse_args()
    started = time.perf_counter()
    root = Path(__file__).resolve().parents[3]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "VALIDATION_EVIDENCE_ONLY",
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "travel_self_loop_policy": "excluded_i_not_equal_j_only",
        "source_commit": source_commit(),
        "source_worktree_dirty": source_worktree_dirty(),
        "source_hashes": {
            "core.py": sha256_bytes((Path(__file__).parent / "core.py").read_bytes()),
            "run_validation.py": sha256_bytes(Path(__file__).read_bytes()),
            "R20_QAOA_SUBPROBLEM_SPEC.md": sha256_bytes((root / "05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md").read_bytes()),
            "test_r20_route_ordering_exact.py": sha256_bytes((root / "05_src/traffic_simulation/validation/test_r20_route_ordering_exact.py").read_bytes()),
        },
        "instances": [run_instance(*instance) for instance in synthetic_instances()],
        "software": {"python": platform.python_version(), "implementation": SCHEMA_VERSION},
        "elapsed_seconds": None,
        "unresolved": ["ROUTING_BASELINE_SPEC_CONFLICT: non-self zero-time policy", "future unreachable-transition hard constraint not implemented"],
    }
    payload["elapsed_seconds"] = time.perf_counter() - started
    args.out.mkdir(parents=True, exist_ok=False)
    results_path = args.out / "validation_results.json"
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    manifest = {
        "run_id": args.out.name,
        "status": payload["status"],
        "source_commit": payload["source_commit"],
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "files": {"validation_results.json": sha256_bytes(results_path.read_bytes())},
        "repository_root": ".",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(args.out), "instances": len(payload["instances"]), "state_counts": {x["instance_id"]: 2 ** x["n_logical"] for x in payload["instances"]}}, indent=2))


if __name__ == "__main__":
    main()
