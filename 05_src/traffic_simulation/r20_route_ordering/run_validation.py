#!/usr/bin/env python3
"""Run only exact route/QUBO validation on deterministic synthetic instances."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from .core import encode_route, enumerate_qubo_states, enumerate_routes, normalize_travel_time_matrix, penalty_consistency


LAMBDA_CANDIDATES = [0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]


def matrix(nodes, values):
    return {a: {b: float(values[nodes.index(a)][nodes.index(b)]) for b in nodes} for a in nodes}


def synthetic_instances():
    n2 = [
        [0, 1, 8], [7, 0, 1], [1, 7, 0]
    ]
    n3_unique = [
        [0, 1, 9, 9], [9, 0, 1, 9], [9, 9, 0, 1], [1, 9, 9, 0]
    ]
    n3_tie = [
        [0, 1, 1, 1], [1, 0, 2, 2], [1, 2, 0, 2], [1, 2, 2, 0]
    ]
    return [("synthetic_n2_unique", 0, [1, 2], matrix([0, 1, 2], n2)), ("synthetic_n3_unique", 0, [1, 2, 3], matrix([0, 1, 2, 3], n3_unique)), ("synthetic_n3_tie", 0, [1, 2, 3], matrix([0, 1, 2, 3], n3_tie))]


def run_instance(instance_id, depot, customers, raw_matrix, lambdas=LAMBDA_CANDIDATES):
    normalized, tau_max = normalize_travel_time_matrix(depot, customers, raw_matrix)
    raw_reference = enumerate_routes(depot, customers, raw_matrix)
    normalized_reference = enumerate_routes(depot, customers, normalized)
    raw_optimal = {tuple(route[1:-1]) for route in raw_reference["optimal_routes"]}
    normalized_optimal = {tuple(route[1:-1]) for route in normalized_reference["optimal_routes"]}
    results = []
    for lam in lambdas:
        qubo = enumerate_qubo_states(depot, customers, normalized, lam)
        best_feasible_route_objectives = [r["travel_objective"] for r in qubo["best_feasible_states"]]
        global_routes = [tuple(r["decoded_customer_sequence"]) for r in qubo["records"] if r["qubo_energy"] == qubo["global_minimum_energy"] and r["feasibility"]]
        all_penalty_ok = all(penalty_consistency(r["bitstring"], len(customers)) == (True, True) for r in qubo["records"])
        all_valid_roundtrip = all(tuple(r["bitstring"]) == encode_route(r["decoded_customer_sequence"], customers) for r in qubo["records"] if r["feasibility"])
        best_feasible_route = min(best_feasible_route_objectives) if best_feasible_route_objectives else None
        results.append({"lambda": lam, "global_minimum_energy": qubo["global_minimum_energy"], "global_minimum_feasible": qubo["global_minimum_all_feasible"], "best_feasible_energy": qubo["best_feasible_energy"], "best_infeasible_energy": qubo["best_infeasible_energy"], "best_feasible_route_objective": best_feasible_route, "global_minimum_decoded_routes": [list(r) for r in global_routes], "checks": {"all_global_minima_feasible": qubo["global_minimum_all_feasible"], "qubo_route_optimum_matches_original": any(abs(x - normalized_reference["best_route_travel_time"]) <= 1e-12 for x in best_feasible_route_objectives), "no_infeasible_state_below_best_feasible": qubo["best_infeasible_energy"] is None or qubo["best_infeasible_energy"] >= qubo["best_feasible_energy"] - 1e-12, "customer_penalty_correct": all_penalty_ok, "position_penalty_correct": all_penalty_ok, "decode_roundtrip_valid": all_valid_roundtrip, "normalization_preserves_route_ranking": raw_optimal == normalized_optimal}, "state_count": qubo["state_count"], "n_logical": qubo["n_logical"], "records": qubo["records"]})
    return {"instance_id": instance_id, "depot": depot, "customer_ids": customers, "n": len(customers), "n_logical": len(customers) ** 2, "tau_max": tau_max, "raw_optimum": raw_reference["best_route_travel_time"], "raw_optimal_routes": raw_reference["optimal_routes"], "normalized_optimum": normalized_reference["best_route_travel_time"], "normalized_optimal_routes": normalized_reference["optimal_routes"], "evaluated_permutations": raw_reference["evaluated_permutations"], "lambda_candidate_reason": "fixed monotone grid spanning zero, small penalties, and larger exploratory penalties; no formal λ adopted", "lambda_results": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("reproducibility/outputs/traffic_simulation/r20_exact_validation/20260910_synthetic_route_ordering"))
    args = parser.parse_args()
    started = time.perf_counter()
    payload = {"status": "VALIDATION_EVIDENCE_ONLY", "formal_qaoa_executed": False, "formal_ising_conversion": False, "instances": [run_instance(*instance) for instance in synthetic_instances()], "software": {"python": platform.python_version()}, "elapsed_seconds": time.perf_counter() - started, "unresolved": ["UNRESOLVED_THEORETICAL_BOUND", "Routing Baseline zero/unreachable/asymmetric edge policy not adopted for these synthetic fixtures"]}
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "validation_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    (args.out / "manifest.json").write_text(json.dumps({"run_id": args.out.name, "status": payload["status"], "formal_qaoa_executed": False, "files": ["validation_results.json", "manifest.json"]}, indent=2) + "\n")
    print(json.dumps({"output": str(args.out), "instances": len(payload["instances"]), "state_counts": {x["instance_id"]: 2 ** x["n_logical"] for x in payload["instances"]}}, indent=2))


if __name__ == "__main__":
    main()
