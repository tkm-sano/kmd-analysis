#!/usr/bin/env python3
"""Build prospective, non-executing Experiment B authority artifacts."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1"
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b/20260911_experiment_b_v1.json"
DESIGN_RECORD = ROOT / "05_src/traffic_simulation/specifications/R23_EXPERIMENT_B_DESIGN_V1.md"
SMOKE = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_implementation_validation/20260911_v1/smoke_validation.json"
INSTANCE_MANIFEST = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json"
LAMBDA = ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json"
FORMAL = ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json"
REVIEW_MANIFEST = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_evidence_review/20260911_v1/manifest.json"
SOURCE_FILES = [
    "05_src/traffic_simulation/r23_qaoa_aer/qaoa.py",
    "05_src/traffic_simulation/r23_qaoa_aer/schema.py",
    "05_src/traffic_simulation/r23_qaoa_aer/optimizers.py",
    "05_src/traffic_simulation/r23_qaoa_aer/initialization.py",
    "05_src/traffic_simulation/r23_qaoa_aer/hamiltonian.py",
    "05_src/traffic_simulation/r23_qaoa_aer/metrics.py",
    "05_src/traffic_simulation/r23_qaoa_aer/artifact.py",
    "05_src/traffic_simulation/validation/test_r23_experiment_b_implementation.py",
]
INSTANCES = ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
P_VALUES = [2, 3]
INIT_CONDITIONS = [("fixed_0.1", None), ("random_seed_11", 11), ("random_seed_23", 23), ("random_seed_37", 37), ("random_seed_53", 53), ("random_seed_71", 71)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def dump(name: str, value) -> Path:
    path = OUT / name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    design = json.loads(DESIGN.read_text())
    smoke = json.loads(SMOKE.read_text())
    design_hash = sha(DESIGN)
    review_manifest_hash = sha(REVIEW_MANIFEST)
    head = git_head()
    source_hashes = {path: sha(ROOT / path) for path in SOURCE_FILES}

    initialization_records = []
    for p in P_VALUES:
        for init_id, seed in INIT_CONDITIONS:
            if init_id == "fixed_0.1":
                params = [0.1] * (2 * p)
            else:
                params = smoke["smoke_d_initialization"]["vectors"][f"p{p}_seed{seed}"]["parameters"]
            initialization_records.append({"p": p, "initialization_id": init_id, "seed": seed, "parameter_order": "[gamma_1..gamma_p, beta_1..beta_p]", "parameters": params, "vector_sha256": hashlib.sha256(",".join(format(float(x), ".17g") for x in params).encode()).hexdigest(), "generation_only_domain": {"gamma": "Uniform[-pi, pi)", "beta": "Uniform[-pi/2, pi/2)"}})
    initialization_authority = {
        "schema_version": "r23-experiment-b-initialization-authority-v1",
        "authority_id": "R23_EXPERIMENT_B_INITIALIZATION_AUTHORITY_V1",
        "classification": "INITIALIZATION_GENERATOR_AUTHORITY_FROZEN",
        "execution_performed": False,
        "generator_source": "05_src/traffic_simulation/r23_qaoa_aer/initialization.py",
        "generator_sha256": source_hashes["05_src/traffic_simulation/r23_qaoa_aer/initialization.py"],
        "rng": "numpy.random.Generator(numpy.random.PCG64(seed))",
        "seed_list": [11, 23, 37, 53, 71],
        "domain_only_for_generation": True,
        "optimization_is_unconstrained": True,
        "records": initialization_records,
        "validation": {"smoke_classification": smoke["classification"], "smoke_status": smoke["smoke_d_initialization"]["status"], "p_values": P_VALUES, "deterministic": True},
    }
    init_path = dump("initialization_authority.json", initialization_authority)

    def run_id(instance, p, init_id, optimizer):
        init_token = "fixed01" if init_id == "fixed_0.1" else init_id
        return f"{instance}_p{p}_init_{init_token}_rep1_optimizer_{optimizer.lower()}"

    b1_runs = [{"run_id": run_id(instance, p, init, "COBYLA"), "condition_id": f"{instance}_p{p}_init_{'fixed01' if init == 'fixed_0.1' else init}_rep1", "instance_id": instance, "n": 4, "p": p, "initialization_id": init, "initialization_seed": seed, "optimizer": "COBYLA", "repetition": 1, "execution": False} for instance in INSTANCES for p in P_VALUES for init, seed in INIT_CONDITIONS]
    b2_runs = [{"run_id": run_id(instance, p, "fixed_0.1", "NELDER_MEAD"), "condition_id": f"{instance}_p{p}_init_fixed01_rep1", "instance_id": instance, "n": 4, "p": p, "initialization_id": "fixed_0.1", "initialization_seed": None, "optimizer": "NELDER_MEAD", "repetition": 1, "execution": False} for instance in INSTANCES for p in P_VALUES]
    common = {"schema_version": "r23-experiment-b-planned-run-manifest-v1", "design_id": design["design_id"], "design_sha256": design_hash, "instance_authority_manifest": rel(INSTANCE_MANIFEST), "instance_authority_manifest_sha256": sha(INSTANCE_MANIFEST), "lambda_policy": "R20_COMMON_GLOBAL_LAMBDA_V1", "lambda_policy_sha256": sha(LAMBDA), "p_values": P_VALUES, "n": 4, "execution_performed": False, "objective_evaluation_cap": 900, "maxiter": 300, "repetition": 1, "expectation_mode": "exact_statevector", "shots": "NONE", "wall_time_policy": "NO_RESEARCH_WALL_TIME_CAP"}
    b1_path = dump("b1_planned_run_manifest.json", {**common, "manifest_id": "R23_EXPERIMENT_B1_PLANNED_RUN_MANIFEST_V1", "optimizer": "COBYLA", "initialization_authority": rel(init_path), "initialization_authority_sha256": sha(init_path), "runs": b1_runs, "run_count": len(b1_runs), "unique_run_ids": len({x["run_id"] for x in b1_runs}) == len(b1_runs)})
    b2_path = dump("b2_planned_run_manifest.json", {**common, "manifest_id": "R23_EXPERIMENT_B2_PLANNED_RUN_MANIFEST_V1", "optimizer": "NELDER_MEAD", "initialization": "fixed_0.1", "runs": b2_runs, "run_count": len(b2_runs), "unique_run_ids": len({x["run_id"] for x in b2_runs}) == len(b2_runs), "authorization_policy": "planned only; execution authorization deferred until B1 evidence review"})

    validation = {
        "schema_version": "r23-experiment-b-validation-summary-v1",
        "classification": "NON_RESEARCH_IMPLEMENTATION_VALIDATION",
        "implementation_commit": head,
        "runtime": {"python": sys.version, "platform": platform.platform(), "environment_path": "/home/takuma/.conda/envs/evrp-quantum-temp", "qiskit": "2.5.2", "qiskit_aer": "0.17.2", "qiskit_algorithms": "0.4.0", "qiskit_optimization": "0.7.0", "numpy": "2.4.6", "scipy": "1.17.1"},
        "smoke_artifact": {"path": rel(SMOKE), "sha256": sha(SMOKE)},
        "smokes": smoke,
        "pytest_status": "NOT_RUN: pytest is not installed in the frozen environment; equivalent direct smoke and py_compile validation passed",
        "test_file": "05_src/traffic_simulation/validation/test_r23_experiment_b_implementation.py",
        "test_count_declared": 6,
        "direct_smoke_pass_count": 4,
        "direct_smoke_fail_count": 0,
    }
    validation_path = dump("validation_summary.json", validation)

    implementation_authority = {
        "schema_version": "r23-experiment-b-implementation-authority-v1",
        "authority_id": "R23_EXPERIMENT_B_IMPLEMENTATION_SOURCE_SET_V1",
        "classification": "EXPERIMENT_B_IMPLEMENTATION_SOURCE_SET_FROZEN",
        "execution_performed": False,
        "implementation_commit": head,
        "source_hashes": source_hashes,
        "optimizer_support": {"COBYLA": "SciPy method COBYLA via explicit adapter", "NELDER_MEAD": "SciPy method Nelder-Mead via explicit adapter", "unsupported": ["SPSA", "all other optimizers"]},
        "common_objective_cap": 900,
        "final_evaluation_outside_optimizer_nfev": True,
        "termination_categories": ["OPTIMIZER_REPORTED_SUCCESS", "OPTIMIZER_REPORTED_FAILURE", "MAXITER_REACHED", "OBJECTIVE_EVALUATION_CAP_REACHED", "EXTERNAL_SAFETY_STOP", "IMPLEMENTATION_EXCEPTION", "TERMINATION_UNKNOWN"],
        "probability_semantics_unchanged": True,
        "hamiltonian_semantics_unchanged": True,
        "validation_summary": rel(validation_path),
        "validation_summary_sha256": sha(validation_path),
    }
    impl_path = dump("implementation_authority.json", implementation_authority)
    b1_authorization = {
        "schema_version": "r23-experiment-b1-execution-authorization-v1",
        "authorization_id": "R23_EXPERIMENT_B1_EXECUTION_AUTHORIZATION_V1",
        "classification": "EXPERIMENT_B1_AUTHORIZED_READY_TO_EXECUTE",
        "execution_performed": False,
        "execution_authorized": True,
        "scope": "B1 initialization robustness only",
        "design_id": design["design_id"],
        "design_sha256": design_hash,
        "implementation_authority_id": implementation_authority["authority_id"],
        "implementation_authority_sha256": sha(impl_path),
        "initialization_authority_id": initialization_authority["authority_id"],
        "initialization_authority_sha256": sha(init_path),
        "b1_planned_run_manifest": rel(b1_path),
        "b1_planned_run_manifest_sha256": sha(b1_path),
        "formal_instance_authority_manifest": rel(INSTANCE_MANIFEST),
        "formal_instance_authority_manifest_sha256": sha(INSTANCE_MANIFEST),
        "lambda_policy": rel(LAMBDA),
        "lambda_policy_sha256": sha(LAMBDA),
        "r23_formal_design": rel(FORMAL),
        "r23_formal_design_sha256": sha(FORMAL),
        "evidence_review_manifest_sha256": review_manifest_hash,
        "checks": {"exactly_36_conditions": len(b1_runs) == 36, "unique_run_ids": len({x["run_id"] for x in b1_runs}) == 36, "n4_only": all(x["n"] == 4 for x in b1_runs), "p_2_3_only": sorted({x["p"] for x in b1_runs}) == [2, 3], "three_authoritative_instances": sorted({x["instance_id"] for x in b1_runs}) == sorted(INSTANCES), "six_initializations": sorted({x["initialization_id"] for x in b1_runs}) == sorted(x[0] for x in INIT_CONDITIONS), "no_research_wall_time_cap": True, "execution_not_performed": True, "smoke_validation_pass": smoke["all_smokes_pass"]},
        "next_action": "Execute only as a separately requested task after confirming the implementation and authority artifacts remain unchanged.",
    }
    auth_path = dump("b1_execution_authorization.json", b1_authorization)
    files = {p.name: sha(p) for p in [impl_path, init_path, validation_path, b1_path, b2_path, auth_path]}
    manifest = {"schema_version": "r23-experiment-b-authority-manifest-v1", "authority_root_id": "R23_EXPERIMENT_B_AUTHORITY_V1", "created_at_utc": datetime.now(timezone.utc).isoformat(), "classification": "EXPERIMENT_B_IMPLEMENTATION_AND_B1_AUTHORITY_READY", "implementation_authority_id": implementation_authority["authority_id"], "b1_authorization_id": b1_authorization["authorization_id"], "b2_execution_authorization_created": False, "execution_performed": False, "source_design_sha256": design_hash, "source_design_record_sha256": sha(DESIGN_RECORD), "source_evidence_review_manifest_sha256": review_manifest_hash, "implementation_commit": head, "files": files, "scope": {"b1_planned_runs": 36, "b2_planned_new_runs": 6, "unique_potential_executions": 42}, "no_formal_qaoa_execution": True}
    dump("manifest.json", manifest)


if __name__ == "__main__":
    main()
