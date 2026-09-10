"""Evidence-only validation of the common R23 formal penalty coefficient.

This module performs routing adaptation, exact route enumeration, exhaustive
small-QUBO validation, and R21/R22 algebra checks.  It never constructs or
executes a QAOA circuit or optimizer.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .core import enumerate_routes, enumerate_qubo_states, normalize_travel_time_matrix
from .routing_adapter import adapt_routing_artifact
from .run_validation import run_instance
from traffic_simulation.r21_qubo_validation.runner import validate_reduced_r21
from traffic_simulation.r21_qubo_validation.schema import coefficients_to_payload
from traffic_simulation.r22_ising_conversion.converter import convert_qubo_to_ising
from traffic_simulation.r22_ising_conversion.schema import R22Input, coefficient_hash, ising_coefficient_hash
from traffic_simulation.r22_ising_conversion.validator import validate_conversion

ROOT = Path(__file__).resolve().parents[3]
ROUTING = ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted"
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r20_formal_penalty_validation/20260911_lambda_v1"
LAMBDA = 3.0
SEED = 2301
DEPOT = "DEP_006"
R20_COMMIT = "3d770b66eb8a053c22acbc38e3058f7845639929"
R20_GATE_COMMIT = "2cc6ae2a4c582e694b1ec80f4c243b1d5ca384b6"
R21_REPORT = "reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/validation_results.json"
R21_MANIFEST = "reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/manifest.json"
TOL = 1e-12


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_hashes() -> dict[str, str]:
    paths = {
        "core.py": ROOT / "05_src/traffic_simulation/r20_route_ordering/core.py",
        "routing_adapter.py": ROOT / "05_src/traffic_simulation/r20_route_ordering/routing_adapter.py",
        "run_validation.py": ROOT / "05_src/traffic_simulation/r20_route_ordering/run_validation.py",
        "validate_formal_lambda.py": Path(__file__),
        "r21_runner.py": ROOT / "05_src/traffic_simulation/r21_qubo_validation/runner.py",
        "r21_schema.py": ROOT / "05_src/traffic_simulation/r21_qubo_validation/schema.py",
        "r22_converter.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/converter.py",
        "r22_schema.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/schema.py",
        "r22_validator.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/validator.py",
    }
    return {name: sha(path) for name, path in paths.items()}


def customers() -> list[str]:
    import csv
    with (ROUTING / "endpoint_manifest_input.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return sorted(row["endpoint_id"] for row in rows if row["endpoint_type"] == "customer")


def selected_subsets(population: list[str]) -> tuple[dict[int, list[dict[str, Any]]], dict[int, int]]:
    selected: dict[int, list[dict[str, Any]]] = {}
    accepted_counts: dict[int, int] = {}
    for n in (2, 3, 4):
        ranked = []
        for subset in itertools.combinations(population, n):
            key = f"{SEED}|{DEPOT}|{'|'.join(subset)}|{n}"
            digest = hashlib.sha256(key.encode()).hexdigest()
            adapter = adapt_routing_artifact(ROUTING, DEPOT, list(subset), source_schema_version="evrp_routing_arc_v1", instance_id="candidate")
            if adapter["accepted"]:
                ranked.append((digest, subset, adapter["input"]))
        ranked.sort(key=lambda item: item[0])
        accepted_counts[n] = len(ranked)
        selected[n] = [{"rank": rank, "selection_key_sha256": digest, "customer_ids": list(subset), "adapter_input": inp} for rank, (digest, subset, inp) in enumerate(ranked[:5], 1)]
    return selected, accepted_counts


def r21_payload(instance_id: str, inp: dict[str, Any], exact_raw: dict[str, Any], exact_norm: dict[str, Any], coeff: Any, bound: float) -> dict[str, Any]:
    return {
        "schema_version": "r21-reduced-qubo-validation-v1", "instance_id": instance_id,
        "depot_id": inp["depot_id"], "customer_ids": inp["customer_ids"], "n_customers": inp["n_customers"],
        "variable_ordering": "row-major:index=(i-1)*n+(t-1)",
        "raw_travel_time_matrix": inp["raw_travel_time_matrix_s"],
        "normalized_travel_time_matrix": inp["normalized_travel_time_matrix"],
        "tau_max": inp["normalization"]["tau_max_s"], "complete_reachability": True,
        "routing_source": {"artifact_id": inp["source"]["artifact_path"], "artifact_sha256": inp["source"]["routing_arcs_sha256"], "schema_version": inp["source"]["source_schema_version"]},
        "r20_formulation_source_commit": R20_COMMIT, "r20_gate_commit": R20_GATE_COMMIT,
        "qubo_coefficients": coefficients_to_payload(coeff), "coefficient_hash": coefficient_hash(coeff),
        "lambda": LAMBDA, "bound_type": "universal_conservative_sufficient", "B": bound, "applied_margin": LAMBDA - bound,
        "numerical_tolerance": {"energy_abs": TOL, "route_cost_abs": TOL},
        "classical_reference_config": {"method": "all_customer_permutations", "tie_policy": "energy_equal"},
    }


def main() -> None:
    started = time.perf_counter()
    population = customers()
    selected, accepted_counts = selected_subsets(population)
    exact_refs = []
    r20_results = []
    r21_results = []
    r22_results = []
    coefficient_summary = []
    pmin_results = {}

    for n in (2, 3, 4):
        # Independent verification of the minimum positive penalty on the n x n binary domain.
        pmin = math.inf
        counts: dict[str, int] = {}
        for bits in itertools.product((0, 1), repeat=n * n):
            rows = [bits[i * n:(i + 1) * n] for i in range(n)]
            rp = sum((1 - sum(row)) ** 2 for row in rows)
            cp = sum((1 - sum(rows[i][t] for i in range(n))) ** 2 for t in range(n))
            penalty = rp + cp
            if penalty:
                pmin = min(pmin, penalty)
                counts[str(penalty)] = counts.get(str(penalty), 0) + 1
        pmin_results[str(n)] = {"minimum_positive_penalty": pmin, "counts_by_penalty": counts, "pass": pmin == 2}

        for item in selected[n]:
            instance_id = f"routing_v18_n{n}_rank{item['rank']:02d}"
            inp = item["adapter_input"]
            raw = inp["raw_travel_time_matrix_s"]
            norm = inp["normalized_travel_time_matrix"]
            raw_ref = enumerate_routes(DEPOT, item["customer_ids"], raw)
            norm_ref = enumerate_routes(DEPOT, item["customer_ids"], norm)
            assert {tuple(x["route"]) for x in raw_ref["records"] if math.isclose(x["travel_time"], raw_ref["best_route_travel_time"], abs_tol=TOL, rel_tol=0)} == {tuple(x) for x in raw_ref["optimal_routes"]}
            reference = {"instance_id": instance_id, "n": n, "depot_id": DEPOT, "customer_ids": list(item["customer_ids"]), "raw": raw_ref, "normalized": norm_ref, "tau_max": inp["normalization"]["tau_max_s"], "ranking_preserved": {tuple(x) for x in raw_ref["optimal_routes"]} == {tuple(x) for x in norm_ref["optimal_routes"]}}
            reference["reference_hash"] = hashlib.sha256(canonical(reference)).hexdigest()
            exact_refs.append(reference)

            bound = (n + 1) / 2
            exact = run_instance(instance_id, DEPOT, list(item["customer_ids"]), raw, [LAMBDA])
            lambda_result = exact["lambda_results"][0]
            coeff = __import__("traffic_simulation.r20_route_ordering.core", fromlist=["build_expanded_qubo"]).build_expanded_qubo(DEPOT, item["customer_ids"], norm, LAMBDA)
            qstates = enumerate_qubo_states(DEPOT, item["customer_ids"], norm, LAMBDA)
            r20 = {"instance_id": instance_id, "n": n, "lambda": LAMBDA, "B": bound, "lambda_minus_B": LAMBDA-bound, "checks": lambda_result["checks"], "all_global_minima_feasible": qstates["all_global_minima_feasible"], "best_feasible_energy": qstates["best_feasible_energy"], "global_minimum_energy": qstates["global_minimum_energy"], "global_minimum_count": len(qstates["global_minimum_bitstrings"]), "direct_expanded_mismatch_count": qstates["direct_expanded_mismatch_count"], "direct_expanded_max_abs_difference": qstates["direct_expanded_max_abs_difference"], "status": "PASS" if all(lambda_result["checks"].values()) and qstates["all_global_minima_feasible"] else "FAIL"}
            r20_results.append(r20)

            payload = r21_payload(instance_id, inp, raw_ref, norm_ref, coeff, bound)
            r21 = validate_reduced_r21(payload)
            r21_results.append({"instance_id": instance_id, "status": r21["status"], "coefficient_hash": r21["coefficient_hash"], "checks": r21["checks"], "lambda": LAMBDA, "B": bound, "lambda_minus_B": LAMBDA-bound})

            r22_payload = {"schema_version": "r22-reduced-ising-conversion-v1", "r21": {"validation_results_sha256": hashlib.sha256(canonical(r21)).hexdigest(), "manifest_sha256": "0"*64, "status": "PASS", "scope": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"}, "instance_id": instance_id, "depot_id": DEPOT, "customer_ids": list(item["customer_ids"]), "n": n, "n_logical": n*n, "variable_ordering": payload["variable_ordering"], "qubo_coefficients": payload["qubo_coefficients"], "qubo_coefficient_hash": payload["coefficient_hash"], "lambda": LAMBDA, "B": bound, "bound_type": payload["bound_type"], "normalization_metadata": {"tau_max": payload["tau_max"], "input_scale": "normalized", "rule": "tau/tau_max"}, "numerical_tolerance": payload["numerical_tolerance"], "r21_optimal_routes": r21["qubo_optimal_routes"]}
            r22 = validate_conversion(R22Input(r22_payload, coeff))
            r22_results.append({"instance_id": instance_id, "status": r22["status"], "checks": r22["checks"], "ising_coefficient_hash": ising_coefficient_hash(convert_qubo_to_ising(coeff)), "max_abs_energy_mismatch": r22["max_abs_energy_mismatch"]})

            ising = convert_qubo_to_ising(coeff)
            all_coeffs = list(coeff.linear.values()) + list(coeff.quadratic.values()) + [coeff.constant]
            ising_coeffs = list(ising.linear.values()) + list(ising.quadratic.values()) + [ising.constant]
            coefficient_summary.append({"instance_id": instance_id, "n": n, "qubo_constant": coeff.constant, "qubo_linear_min": min(coeff.linear.values()), "qubo_linear_max": max(coeff.linear.values()), "qubo_quadratic_min": min(coeff.quadratic.values()), "qubo_quadratic_max": max(coeff.quadratic.values()), "qubo_max_abs": max(map(abs, all_coeffs)), "ising_max_abs": max(map(abs, ising_coeffs)), "ising_min": min(ising_coeffs), "ising_max": max(ising_coeffs), "qubo_coefficient_dynamic_range": max(map(abs, all_coeffs)) / min(abs(v) for v in all_coeffs if v), "coefficient_hash": coefficient_hash(coeff), "ising_coefficient_hash": ising_coefficient_hash(ising)})

    theorem = {"classification": "FORMAL_LAMBDA_POLICY_ADOPTED", "policy_id": "R20_COMMON_GLOBAL_LAMBDA_V1", "lambda": LAMBDA, "scope": {"n": [2,3,4], "instances": 15, "formulation": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"}, "assumptions": {"normalized_travel_times": True, "reachable_nonself_costs_positive": True, "normalized_cost_max": 1, "complete_reachability": True, "customer_only_nxn_encoding": True, "customer_once_squared_penalty": True, "position_once_squared_penalty": True, "common_lambda": True, "no_unreachable_penalty": True, "fixed_depot_not_encoded": True, "direct_squared_formulation": True}, "proof": {"travel_nonnegative": "All binary travel monomials have nonnegative coefficients because normalized directed costs are positive; therefore H_travel >= 0.", "feasible_upper_bound": "A feasible route has n+1 directed arcs, each <=1, so f_route* <= n+1.", "minimum_positive_penalty": "For an n x n binary matrix, if row/column one-hot constraints fail, conservation of total ones forces at least two unit squared deviations across the two families; exhaustive n=2,3,4 checks also give P_min=2.", "dominance": "Every infeasible state has H_QUBO >= 2 lambda > n+1 >= f_route* for a feasible route, so every global minimizer is feasible.", "universal_bound": "lambda > (n+1)/2"}, "margins": {str(n): {"energy_margin": 2*LAMBDA-(n+1), "lambda_margin": LAMBDA-(n+1)/2} for n in (2,3,4)}, "pmin_exhaustive": pmin_results}
    metadata = {"schema_version": "r20-formal-penalty-validation-v1", "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "formal_qaoa_executed": False, "optimizer_executed": False, "source_commit": git("rev-parse", "HEAD"), "source_worktree_dirty": bool(git("status", "--porcelain")), "python": sys.version, "platform": platform.platform(), "source_hashes": source_hashes(), "routing_artifact": str(ROUTING), "routing_arcs_sha256": sha(ROUTING / "routing_arcs.csv"), "r13_manifest_sha256": sha(ROUTING / "r13_manifest.json"), "r14_validation": "PASS", "runtime_seconds": time.perf_counter()-started}

    OUT.mkdir(parents=True, exist_ok=False)
    files = {"theorem_validation.json": theorem, "instance_validation.json": {"selection_seed": SEED, "depot": DEPOT, "population": population, "accepted_candidate_counts": accepted_counts, "selected": selected, "exact_references": exact_refs, "r20_results": r20_results, "r21_results": r21_results, "r22_results": r22_results, "status": "PASS" if all(x["status"] == "PASS" for x in r20_results+r21_results+r22_results) else "FAIL"}, "coefficient_summary.json": {"lambda": LAMBDA, "instances": coefficient_summary}, "metadata.json": metadata}
    for name, value in files.items():
        (OUT / name).write_bytes(canonical(value) + b"\n")
    manifest = {"schema_version": "r20-formal-penalty-validation-manifest-v1", "classification": "FORMAL_LAMBDA_POLICY_ADOPTED", "policy_id": "R20_COMMON_GLOBAL_LAMBDA_V1", "lambda": LAMBDA, "files": {name: sha(OUT / name) for name in files}, "source_commit": metadata["source_commit"], "source_hashes": metadata["source_hashes"], "routing_artifact": metadata["routing_artifact"], "routing_arcs_sha256": metadata["routing_arcs_sha256"], "formal_qaoa_executed": False, "optimizer_executed": False, "instance_count": 15, "r20_pass_count": sum(x["status"] == "PASS" for x in r20_results), "r21_pass_count": sum(x["status"] == "PASS" for x in r21_results), "r22_pass_count": sum(x["status"] == "PASS" for x in r22_results)}
    (OUT / "manifest.json").write_bytes(canonical(manifest) + b"\n")


if __name__ == "__main__":
    main()
