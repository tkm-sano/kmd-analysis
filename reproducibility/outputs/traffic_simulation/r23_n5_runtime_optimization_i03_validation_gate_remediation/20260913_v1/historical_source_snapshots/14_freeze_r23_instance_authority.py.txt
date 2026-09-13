"""Build the formal R20/R21/R22 authority bundle for R23 instances.

This is a pre-QAOA authority-generation command.  It performs no QAOA,
optimizer, Aer, or sampling execution.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .core import build_expanded_qubo, enumerate_qubo_states, enumerate_routes, normalize_travel_time_matrix
from .validate_formal_lambda import DEPOT, LAMBDA, ROOT, SEED, ROUTING, selected_subsets, sha
from traffic_simulation.r21_qubo_validation.runner import validate_reduced_r21
from traffic_simulation.r21_qubo_validation.schema import coefficient_hash, coefficients_to_payload
from traffic_simulation.r22_ising_conversion.converter import convert_qubo_to_ising
from traffic_simulation.r22_ising_conversion.schema import R22Input, ising_coefficient_hash
from traffic_simulation.r22_ising_conversion.validator import validate_conversion

OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"
SET_CONFIG = ROOT / "reproducibility/config/traffic_simulation/r23_formal_instances/20260911_r23_formal_instances_v1.json"
EXACT_OUT = OUT / "exact_references.json"
R20_OUT = OUT / "r20"
R21_OUT = OUT / "r21"
R22_OUT = OUT / "r22"
LAMBDA_CONFIG = ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json"
FORMAL_CONFIG = ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json"
FORMAL_DESIGN = ROOT / "05_src/traffic_simulation/specifications/R23_FORMAL_EXPERIMENT_DESIGN_V1.md"
LAMBDA_POLICY_ID = "R20_COMMON_GLOBAL_LAMBDA_V1"
LAMBDA_POLICY_SHA = "8f6f3b8feeeb85b556dc6fb23478fa5ef529bfac2ac4beb68c2d2bc7ff62bf95"
FORMAL_DESIGN_ID = "R23_FORMAL_EXPERIMENT_DESIGN_V1"
R20_COMMIT = "3d770b66eb8a053c22acbc38e3058f7845639929"
R20_GATE_COMMIT = "2cc6ae2a4c582e694b1ec80f4c243b1d5ca384b6"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b"\n")
    return sha(path)


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
        "validate_formal_lambda.py": ROOT / "05_src/traffic_simulation/r20_route_ordering/validate_formal_lambda.py",
        "freeze_r23_instance_authority.py": Path(__file__),
        "r21_runner.py": ROOT / "05_src/traffic_simulation/r21_qubo_validation/runner.py",
        "r21_schema.py": ROOT / "05_src/traffic_simulation/r21_qubo_validation/schema.py",
        "r22_converter.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/converter.py",
        "r22_schema.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/schema.py",
        "r22_validator.py": ROOT / "05_src/traffic_simulation/r22_ising_conversion/validator.py",
    }
    return {name: sha(path) for name, path in paths.items()}


def make_r21_payload(instance_id: str, inp: dict[str, Any], coeff: Any, bound: float, r20_input_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "r21-reduced-qubo-validation-v1", "instance_id": instance_id,
        "depot_id": inp["depot_id"], "customer_ids": inp["customer_ids"], "n_customers": inp["n_customers"],
        "variable_ordering": "row-major:index=(i-1)*n+(t-1)", "raw_travel_time_matrix": inp["raw_travel_time_matrix_s"],
        "normalized_travel_time_matrix": inp["normalized_travel_time_matrix"], "tau_max": inp["normalization"]["tau_max_s"],
        "complete_reachability": True, "routing_source": {"artifact_id": inp["source"]["artifact_path"], "artifact_sha256": inp["source"]["routing_arcs_sha256"], "schema_version": inp["source"]["source_schema_version"]},
        "r20_formulation_source_commit": R20_COMMIT, "r20_gate_commit": R20_GATE_COMMIT,
        "r20_authority_input_sha256": r20_input_hash, "r20_formulation": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY",
        "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA,
        "qubo_coefficients": coefficients_to_payload(coeff), "coefficient_hash": coefficient_hash(coeff),
        "lambda": LAMBDA, "bound_type": "universal_conservative_sufficient", "B": bound, "applied_margin": LAMBDA-bound,
        "numerical_tolerance": {"energy_abs": 1e-12, "route_cost_abs": 1e-12},
        "classical_reference_config": {"method": "all_customer_permutations", "tie_policy": "energy_equal"},
    }


def main() -> None:
    if OUT.exists():
        raise RuntimeError(f"refusing to overwrite existing authority output: {OUT}")
    start = time.perf_counter()
    population = __import__("traffic_simulation.r20_route_ordering.validate_formal_lambda", fromlist=["customers"]).customers()
    selected, accepted_counts = selected_subsets(population)
    if accepted_counts != {2: 45, 3: 120, 4: 210} or sum(len(selected[n]) for n in (2,3,4)) != 15:
        raise RuntimeError("selection authority mismatch")

    records = []
    exact_refs = {}
    r20_manifest_records = []
    r21_manifest_records = []
    r22_manifest_records = []
    for n in (2, 3, 4):
        for item in selected[n]:
            instance_id = f"routing_v18_n{n}_rank{item['rank']:02d}"
            inp = item["adapter_input"]
            customers = list(item["customer_ids"])
            raw = inp["raw_travel_time_matrix_s"]
            normalized = inp["normalized_travel_time_matrix"]
            raw_ref = enumerate_routes(DEPOT, customers, raw)
            norm_ref = enumerate_routes(DEPOT, customers, normalized)
            reference = {"instance_id": instance_id, "n": n, "depot_id": DEPOT, "customer_ids": customers, "raw": raw_ref, "normalized": norm_ref, "tau_max": inp["normalization"]["tau_max_s"], "ranking_preserved": {tuple(x) for x in raw_ref["optimal_routes"]} == {tuple(x) for x in norm_ref["optimal_routes"]}, "reference_algorithm": "all_customer_permutations", "reference_tolerance": 1e-12}
            reference["reference_hash"] = write_json(OUT / "_refs" / f"{instance_id}.json", reference)
            exact_refs[instance_id] = reference
            coeff = build_expanded_qubo(DEPOT, customers, normalized, LAMBDA)
            qstates = enumerate_qubo_states(DEPOT, customers, normalized, LAMBDA, max_logical_variables=16, max_states=1_000_000)
            r20_validation = {"status": "R20_FORMAL_INSTANCE_PASS" if qstates["all_global_minima_feasible"] and qstates["direct_expanded_mismatch_count"] == 0 else "R20_FORMAL_INSTANCE_VALIDATION_FAILED", "instance_id": instance_id, "n": n, "n_logical": n*n, "state_count": qstates["state_count"], "lambda": LAMBDA, "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA, "checks": {"all_global_minima_feasible": qstates["all_global_minima_feasible"], "direct_expanded_consistency": qstates["direct_expanded_mismatch_count"] == 0, "best_feasible_matches_exact": all(abs(float(x["travel_objective"]) - norm_ref["best_route_travel_time"]) <= 1e-12 for x in qstates["best_feasible_states"]), "route_set_preserved": {tuple(x["decoded_customer_sequence"]) for x in qstates["best_feasible_states"]} == {tuple(x[1:-1]) for x in norm_ref["optimal_routes"]}}, "global_minimum_energy": qstates["global_minimum_energy"], "global_minimum_bitstrings": qstates["global_minimum_bitstrings"], "global_minimum_count": len(qstates["global_minimum_bitstrings"]), "direct_expanded_mismatch_count": qstates["direct_expanded_mismatch_count"], "direct_expanded_max_abs_difference": qstates["direct_expanded_max_abs_difference"], "exact_reference_hash": reference["reference_hash"]}
            r20_input = {"schema_version": "r20-formal-instance-input-v1", "instance_id": instance_id, "n": n, "n_logical": n*n, "depot_id": DEPOT, "customer_ids": customers, "candidate_rank": item["rank"], "selection_key_sha256": item["selection_key_sha256"], "node_set": inp["node_set"], "expected_directed_pair_count": inp["expected_directed_pair_count"], "observed_directed_pair_count": inp["reachable_pair_count"], "complete_reachability": inp["complete_reachability"], "raw_directed_edges": inp["raw_directed_edges"], "raw_travel_time_matrix_s": raw, "normalized_travel_time_matrix": normalized, "tau_max_s": inp["normalization"]["tau_max_s"], "normalization_rule": "tau/tau_max", "routing_source": inp["source"], "routing_artifact_sha256": inp["source"]["routing_arcs_sha256"], "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA, "lambda": LAMBDA, "qubo_coefficients": coefficients_to_payload(coeff), "qubo_coefficient_hash": coefficient_hash(coeff), "exact_reference_hash": reference["reference_hash"], "formulation_id": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY", "validation": r20_validation}
            r20_input_hash = write_json(R20_OUT / instance_id / "r20_input.json", r20_input)
            r20_val_hash = write_json(R20_OUT / instance_id / "validation.json", r20_validation)
            r20_manifest = {"stage": "R20_FORMAL_REDUCED_INSTANCE", "status": r20_validation["status"], "instance_id": instance_id, "files": {"r20_input.json": r20_input_hash, "validation.json": r20_val_hash}, "input_hash": r20_input_hash, "qubo_coefficient_hash": coefficient_hash(coeff), "exact_reference_hash": reference["reference_hash"], "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA}
            r20_manifest_hash = write_json(R20_OUT / instance_id / "manifest.json", r20_manifest); r20_manifest_records.append({"instance_id": instance_id, "path": str(R20_OUT.relative_to(ROOT) / instance_id), "manifest_sha256": r20_manifest_hash, "input_sha256": r20_input_hash, "validation_sha256": r20_val_hash, "qubo_coefficient_hash": coefficient_hash(coeff), "status": r20_validation["status"]})

            bound = (n + 1) / 2
            r21_payload = make_r21_payload(instance_id, inp, coeff, bound, r20_input_hash)
            r21_result = validate_reduced_r21(r21_payload)
            r21_result["status"] = "R21_FORMAL_INSTANCE_PASS" if r21_result["status"] == "PASS" else "R21_FORMAL_INSTANCE_VALIDATION_FAILED"
            r21_result["r20_authority_input_sha256"] = r20_input_hash; r21_result["lambda_policy_id"] = LAMBDA_POLICY_ID; r21_result["lambda_policy_sha256"] = LAMBDA_POLICY_SHA
            r21_input_hash = write_json(R21_OUT / instance_id / "r21_input.json", r21_payload)
            r21_val_hash = write_json(R21_OUT / instance_id / "validation.json", r21_result)
            r21_manifest = {"stage": "R21_FORMAL_REDUCED_QUBO", "status": r21_result["status"], "instance_id": instance_id, "files": {"r21_input.json": r21_input_hash, "validation.json": r21_val_hash}, "r20_input_sha256": r20_input_hash, "validation_results_sha256": r21_val_hash, "qubo_coefficient_hash": r21_result["coefficient_hash"], "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA}
            r21_manifest_hash = write_json(R21_OUT / instance_id / "manifest.json", r21_manifest); r21_manifest_records.append({"instance_id": instance_id, "path": str(R21_OUT.relative_to(ROOT) / instance_id), "manifest_sha256": r21_manifest_hash, "input_sha256": r21_input_hash, "validation_sha256": r21_val_hash, "qubo_coefficient_hash": r21_result["coefficient_hash"], "status": r21_result["status"]})

            r22_payload = {"schema_version": "r22-reduced-ising-conversion-v1", "r21": {"validation_results_sha256": r21_val_hash, "manifest_sha256": r21_manifest_hash, "status": "PASS", "scope": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"}, "instance_id": instance_id, "depot_id": DEPOT, "customer_ids": customers, "n": n, "n_logical": n*n, "variable_ordering": r21_payload["variable_ordering"], "qubo_coefficients": r21_payload["qubo_coefficients"], "qubo_coefficient_hash": r21_payload["coefficient_hash"], "lambda": LAMBDA, "B": bound, "bound_type": r21_payload["bound_type"], "normalization_metadata": {"tau_max": r21_payload["tau_max"], "input_scale": "normalized", "rule": "tau/tau_max"}, "numerical_tolerance": r21_payload["numerical_tolerance"], "r21_optimal_routes": r21_result["qubo_optimal_routes"]}
            r22_input_data = R22Input(r22_payload, coeff)
            r22_result = validate_conversion(r22_input_data)
            r22_result["status"] = "R22_FORMAL_INSTANCE_PASS" if r22_result["status"] == "PASS" else "R22_FORMAL_INSTANCE_EQUIVALENCE_FAILED"
            r22_result["r20_authority_input_sha256"] = r20_input_hash; r22_result["r21_validation_sha256"] = r21_val_hash; r22_result["lambda_policy_id"] = LAMBDA_POLICY_ID; r22_result["lambda_policy_sha256"] = LAMBDA_POLICY_SHA
            ising = convert_qubo_to_ising(coeff)
            r22_payload["ising_coefficients"] = {"constant": ising.constant, "linear": {str(k): v for k,v in ising.linear.items()}, "quadratic": {f"{a},{b}": v for (a,b),v in ising.quadratic.items()}, "n_logical": ising.n_logical, "binary_spin_convention": ising.binary_spin_convention}
            r22_payload["ising_coefficient_hash"] = ising_coefficient_hash(ising)
            r22_input_hash = write_json(R22_OUT / instance_id / "r22_input.json", r22_payload)
            r22_val_hash = write_json(R22_OUT / instance_id / "validation.json", r22_result)
            r22_manifest = {"stage": "R22_FORMAL_REDUCED_ISING_EQUIVALENCE", "status": r22_result["status"], "instance_id": instance_id, "files": {"r22_input.json": r22_input_hash, "validation.json": r22_val_hash}, "r20_input_sha256": r20_input_hash, "r21_manifest_sha256": r21_manifest_hash, "r21_validation_sha256": r21_val_hash, "qubo_coefficient_hash": r22_payload["qubo_coefficient_hash"], "ising_coefficient_hash": r22_result["ising_coefficient_hash"], "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA}
            r22_manifest_hash = write_json(R22_OUT / instance_id / "manifest.json", r22_manifest); r22_manifest_records.append({"instance_id": instance_id, "path": str(R22_OUT.relative_to(ROOT) / instance_id), "manifest_sha256": r22_manifest_hash, "input_sha256": r22_input_hash, "validation_sha256": r22_val_hash, "qubo_coefficient_hash": r22_payload["qubo_coefficient_hash"], "ising_coefficient_hash": r22_result["ising_coefficient_hash"], "max_abs_energy_mismatch": r22_result["max_abs_energy_mismatch"], "status": r22_result["status"]})

            records.append({"instance_id": instance_id, "n": n, "depot_id": DEPOT, "customer_ids": customers, "candidate_rank": item["rank"], "selection_key_sha256": item["selection_key_sha256"], "routing_artifact_sha256": inp["source"]["routing_arcs_sha256"], "r20": r20_manifest_records[-1], "r21": r21_manifest_records[-1], "r22": r22_manifest_records[-1], "exact_reference_hash": reference["reference_hash"], "matrix_sha256": {"raw": sha_bytes(raw), "normalized": sha_bytes(normalized)}, "status": "FORMAL_INSTANCE_AUTHORITY_PASS" if r20_validation["status"].endswith("PASS") and r21_result["status"].endswith("PASS") and r22_result["status"].endswith("PASS") else "FORMAL_SELECTED_INSTANCE_AUTHORITY_FAILED"})

    exact_hash = write_json(EXACT_OUT, {"schema_version": "r23-formal-exact-reference-set-v1", "method": "all_customer_permutations", "instances": exact_refs, "count": len(exact_refs)})
    instance_set = {"instance_set_id": "R23_FORMAL_INSTANCE_SET_V1", "formal_design_id": FORMAL_DESIGN_ID, "formal_design_sha256": sha(FORMAL_CONFIG), "selection_algorithm": "canonical combinations; SHA256(seed|depot|sorted_customer_ids|n) ascending; complete-reachability candidates only", "selection_seed": SEED, "routing_authority": {"artifact_path": str(ROUTING.relative_to(ROOT)), "routing_arcs_sha256": sha(ROUTING / "routing_arcs.csv"), "manifest_sha256": sha(ROUTING / "r13_manifest.json")}, "lambda_policy_id": LAMBDA_POLICY_ID, "lambda_policy_sha256": LAMBDA_POLICY_SHA, "lambda": LAMBDA, "instances": records, "counts": {"n2": 5, "n3": 5, "n4": 5, "total": 15}, "qaoa_executed": False, "selection_performance_blind": True}
    instance_set_hash = write_json(SET_CONFIG, instance_set)
    summary = {"schema_version": "r23-formal-instance-authority-summary-v1", "instance_set_id": "R23_FORMAL_INSTANCE_SET_V1", "instances": records, "counts": {"total": len(records), "pass": sum(x["status"] == "FORMAL_INSTANCE_AUTHORITY_PASS" for x in records), "by_n": {str(n): sum(x["n"] == n for x in records) for n in (2,3,4)}}, "qaoa_executed": False}
    summary_hash = write_json(OUT / "authority_summary.json", summary)
    run_manifest = {"schema_version": "r23-formal-planned-run-manifest-v1", "formal_design_id": FORMAL_DESIGN_ID, "instance_set_id": "R23_FORMAL_INSTANCE_SET_V1", "lambda": LAMBDA, "optimizer": "COBYLA", "maxiter": 300, "objective_cap": 900, "initialization": "all parameters = 0.1", "repetition": 1, "shots": "NONE", "runs": [{"run_id": f"{x['instance_id']}_p{p}_init_fixed01_rep1", "instance_id": x["instance_id"], "n": x["n"], "p": p, "parameter_count": 2*p, "lambda": LAMBDA} for x in records for p in (1,2,3)], "run_count": 45, "execution": False}
    run_manifest_hash = write_json(OUT / "planned_run_manifest.json", run_manifest)
    authority_manifest = {"schema_version": "r23-formal-instance-authority-manifest-v1", "classification": "FORMAL_INSTANCE_AUTHORITY_FROZEN_READY_TO_EXECUTE", "instance_set_id": "R23_FORMAL_INSTANCE_SET_V1", "source_commit": git("rev-parse", "HEAD"), "implementation_commit": "417bfe97520f42ae749d876fc26cfd205d6e8607", "formal_design_commit": "2a57d9cce3e69d3cc3fbcc077a2e0f65d402064e", "lambda_policy_commit": "dbca4b5a3ad748f46902c27da8e7c77bf02cbadf", "source_hashes": source_hashes(), "python": sys.version, "platform": platform.platform(), "routing_authority": instance_set["routing_authority"], "lambda_policy": {"id": LAMBDA_POLICY_ID, "sha256": LAMBDA_POLICY_SHA, "lambda": LAMBDA}, "files": {"selected_instances.json": instance_set_hash, "exact_references.json": exact_hash, "authority_summary.json": summary_hash, "planned_run_manifest.json": run_manifest_hash}, "r20_authority_count": 15, "r21_authority_count": 15, "r22_authority_count": 15, "final_authority_count": 15, "formal_qaoa_executed": False, "runtime_seconds": time.perf_counter()-start}
    write_json(OUT / "selected_instances.json", instance_set)
    # The manifest is intentionally excluded from its own files map to avoid
    # a circular self-hash.  Its external SHA-256 is recorded by the handoff.
    write_json(OUT / "manifest.json", authority_manifest)


def sha_bytes(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


if __name__ == "__main__":
    main()
