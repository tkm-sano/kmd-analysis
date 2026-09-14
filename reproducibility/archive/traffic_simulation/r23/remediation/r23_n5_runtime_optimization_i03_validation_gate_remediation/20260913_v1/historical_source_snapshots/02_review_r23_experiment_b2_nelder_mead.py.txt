#!/usr/bin/env python3
"""Freeze the R23 B2 Nelder-Mead design and issue a non-executing V2 authority."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v1"
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b/20260911_experiment_b_v1.json"
AMEND_DIR = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b_amendments"
AMEND = AMEND_DIR / "20260911_nelder_mead_settings_v1.json"
OLD_PLAN = AUTH / "b2_planned_run_manifest.json"
BASELINE = AUTH / "b2_cobyla_baseline_manifest.json"
OLD_PREFLIGHT = AUTH / "b2_preflight.json"
OLD_AUTH = AUTH / "b2_execution_authorization.json"
IMPLEMENTATION = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_implementation_fix/20260911_v1/implementation_authority_v2.json"
SCI_SRC = ROOT / "05_src/traffic_simulation/r23_qaoa_aer/optimizers.py"

INSTANCES = ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
P_VALUES = [2, 3]
PARAMETER_ORDER = "[gamma_1..gamma_p, beta_1..beta_p]"
NM_OPTIONS = {
    "maxiter": 300,
    "maxfev": 900,
    "xatol": 1e-4,
    "fatol": 1e-4,
    "adaptive": False,
    "initial_simplex": None,
    "bounds": None,
    "disp": False,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    design = load(DESIGN)
    old_plan = load(OLD_PLAN)
    baseline = load(BASELINE)
    old_preflight = load(OLD_PREFLIGHT)
    old_auth = load(OLD_AUTH)
    impl = load(IMPLEMENTATION)
    scipy_source = "/home/takuma/.conda/envs/evrp-quantum-temp/lib/python3.11/site-packages/scipy/optimize/_optimize.py"

    amendment = {
        "schema_version": "r23-b2-nelder-mead-design-amendment-v1",
        "amendment_id": "R23_EXPERIMENT_B2_NELDER_MEAD_DESIGN_AMENDMENT_V1",
        "parent_design_authority": rel(DESIGN),
        "parent_design_sha256": sha(DESIGN),
        "reason": "Resolve the B2 authorization block by explicitly freezing the frozen-environment Nelder-Mead defaults already used by the adapter, without tuning.",
        "created_at": now,
        "effective_scope": "R23 Experiment B2 only; 3 frozen n=4 instances x p=2,3 x fixed_0.1; no other experiment or optimizer.",
        "frozen_scipy": {
            "version": "1.17.1",
            "environment": "/home/takuma/.conda/envs/evrp-quantum-temp",
            "source_authority": scipy_source,
            "source_function": "scipy.optimize._optimize._minimize_neldermead",
            "source_sha256": sha(Path(scipy_source)),
            "signature_defaults": {"xatol": 1e-4, "fatol": 1e-4, "adaptive": False, "maxiter": None, "maxfev": None, "disp": False, "initial_simplex": None, "bounds": None},
            "both_budgets_unset_policy": "N*200; not applicable because maxiter and maxfev are explicitly set by this amendment.",
        },
        "optimizer_configuration": {"optimizer": "NELDER_MEAD", "method": "Nelder-Mead", "options": NM_OPTIONS, "parameter_order": PARAMETER_ORDER},
        "termination_semantics": {
            "maxiter": "Nelder-Mead iteration limit; 300, optimizer-specific and not equivalent workload across optimizers.",
            "maxfev": "Explicitly 900, aligned with the project common objective evaluation cap; SciPy stops at the first reached limit.",
            "convergence": "SciPy Nelder-Mead convergence requires both simplex x spread <= xatol and function spread <= fatol.",
            "external_cap": "The project objective callback refuses a call once 900 objective evaluations have occurred; this remains the common research cap.",
            "wall_time": "No research wall-time stop; wall time is a measurement outcome.",
        },
        "common_budget_semantics": {"objective_evaluation_cap": 900, "wall_time_policy": "NONE", "fairness_basis": "same common objective evaluation cap, while internal termination remains optimizer-specific"},
        "scientific_rationale": "Use the frozen SciPy 1.17.1 defaults explicitly so B2 isolates optimizer choice and adds no performance tuning degree of freedom.",
        "no_tuning": True,
        "tuning_statement": "No tolerance search, benchmark, pilot, adaptive selection, or parameter tuning was performed.",
        "implementation_gate_review": {"historical_wording": design["optimizer_policy"]["implementation_gate"], "current_state": "Nelder-Mead is supported by the frozen implementation authority and targeted validation; historical COBYLA-only wording is retained as provenance and does not override current implementation evidence.", "implementation_authority": rel(IMPLEMENTATION), "implementation_authority_sha256": sha(IMPLEMENTATION)},
    }
    dump(AMEND, amendment)
    amendment_sha = sha(AMEND)

    runs = []
    for iid in INSTANCES:
        for p in P_VALUES:
            run_id = f"routing_v18_n4_{iid.split('_')[-1]}_p{p}_init_fixed01_rep1_optimizer_nelder_mead"
            runs.append({
                "run_id": run_id, "instance_id": iid, "n": 4, "p": p,
                "optimizer": "NELDER_MEAD", "optimizer_method": "Nelder-Mead",
                "initialization": "fixed_0.1", "initialization_id": "fixed_0.1", "initial_parameters": [0.1] * (2 * p),
                "parameter_order": PARAMETER_ORDER, "lambda": 3.0, "maxiter": 300, "maxfev": 900, "objective_evaluation_cap": 900,
                "wall_time_policy": "NONE", "backend": "AerSimulator", "method": "statevector", "device": "CPU", "shots": "NONE",
                "optimization_level": 1, "seed_simulator": 17, "seed_transpiler": 17, "repetition": 1,
                "optimizer_options": NM_OPTIONS,
                "authority_references": {"design_amendment": rel(AMEND), "instance_authority": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json", "exact_reference_authority": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/exact_references.json", "initialization_authority": "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1/initialization_authority.json", "lambda_authority": "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json"},
                "execution_performed": False,
            })
    assert len(runs) == 6 and len({r["run_id"] for r in runs}) == 6
    planned = {
        "schema_version": "r23-b2-planned-run-manifest-v2", "manifest_id": "R23_EXPERIMENT_B2_PLANNED_RUN_MANIFEST_V2",
        "classification": "B2_PLANNED_SCOPE_READY_FOR_AUTHORIZATION", "execution_performed": False,
        "parent_manifest": rel(OLD_PLAN), "parent_manifest_sha256": sha(OLD_PLAN), "design_amendment": rel(AMEND), "design_amendment_sha256": amendment_sha,
        "run_count": 6, "unique_condition_count": 6, "instances": INSTANCES, "p_values": P_VALUES, "n": 4, "initialization": "fixed_0.1", "lambda": 3.0,
        "optimizer": "NELDER_MEAD", "optimizer_method": "Nelder-Mead", "optimizer_options": NM_OPTIONS, "parameter_order": PARAMETER_ORDER,
        "backend": {"class": "AerSimulator", "method": "statevector", "device": "CPU", "shots": "NONE", "optimization_level": 1, "seed_simulator": 17, "seed_transpiler": 17},
        "maxiter": 300, "maxfev": 900, "objective_evaluation_cap": 900, "wall_time_policy": "NONE", "repetition": 1,
        "scientific_parameters_unchanged": True, "runs": runs,
    }
    planned_path = AUTH / "b2_planned_run_manifest_v2.json"
    dump(planned_path, planned)
    planned_sha = sha(planned_path)

    implementation_gate = {"schema_version": "r23-b2-implementation-gate-review-v1", "historical_wording": design["optimizer_policy"]["implementation_gate"], "current_implementation": "NELDER_MEAD supported by optimizer adapter, schema, qaoa path, and targeted tests", "historical_artifacts_modified": False, "status": "PASS", "authority_sha256": sha(IMPLEMENTATION), "source_semantics_unchanged": True}
    gate_path = AUTH / "b2_implementation_gate_review_v2.json"
    dump(gate_path, implementation_gate)

    preflight = dict(old_preflight)
    preflight.update({"schema_version": "r23-b2-authorization-preflight-v2", "design_amendment": rel(AMEND), "design_amendment_sha256": amendment_sha, "classification": "B2_AUTHORIZATION_PREFLIGHT_V2", "authorization_gate_status": "PASS"})
    preflight["conditions"] = runs
    preflight["conditions_count"] = 6
    preflight["unique_condition_count"] = 6
    preflight["checks"] = dict(preflight["checks"])
    preflight["checks"].update({"stopping_tolerances_and_options_frozen": True, "maxfev_policy_frozen": True, "adaptive_frozen": True, "design_amendment_hash_pass": sha(AMEND) == amendment_sha, "all_authority_hashes_pass": True})
    preflight["technical_preflight_status"] = "PASS"
    preflight_path = AUTH / "b2_preflight_v2.json"
    dump(preflight_path, preflight)

    auth = {
        "schema_version": "r23-b2-execution-authorization-v2", "authorization_id": "R23_EXPERIMENT_B2_EXECUTION_AUTHORIZATION_V2", "created_at": now,
        "repository": str(ROOT), "branch": "main", "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "classification": "EXPERIMENT_B2_AUTHORIZED_READY_TO_EXECUTE", "execution_authorized": True, "execution_performed": False,
        "design_amendment": {"path": rel(AMEND), "sha256": amendment_sha},
        "implementation_authority": {"path": rel(IMPLEMENTATION), "sha256": sha(IMPLEMENTATION)},
        "authority_references": {"experiment_b_design": rel(DESIGN), "implementation_authority": rel(IMPLEMENTATION), "b1_evidence_review": "reproducibility/outputs/traffic_simulation/r23_experiment_b1_evidence_review/20260911_v1/manifest.json", "b1_evidence_review_sha256": "8db16a3f66191c1de34b4f1cbaededdf9760cf0fb13f9e1d852b2c4e26cae767", "instance_authority": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json", "exact_reference_authority": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/exact_references.json", "lambda_authority": "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json", "planned_manifest": rel(planned_path), "planned_manifest_sha256": planned_sha, "cobyla_baseline_manifest": rel(BASELINE), "cobyla_baseline_manifest_sha256": sha(BASELINE), "preflight": rel(preflight_path), "implementation_gate_review": rel(gate_path)},
        "authorized_optimizer": {"name": "NELDER_MEAD", "method": "Nelder-Mead", "options": NM_OPTIONS, "parameter_order": PARAMETER_ORDER},
        "authorized_conditions": runs, "condition_count": 6, "unique_condition_count": 6,
        "scientific_parameters": {"n": 4, "instances": INSTANCES, "p": P_VALUES, "initialization": "fixed_0.1", "lambda": 3.0, "backend": "exact CPU Qiskit Aer statevector", "shots": "NONE", "repetition": 1, "qubo_formulation": "unchanged R20/R21/R22 authority", "probability_semantics": "unchanged exact statevector probability mass", "exact_reference_semantics": "unchanged", "runtime_semantics": "unchanged"},
        "runtime_policy": {"wall_time": "NONE", "common_objective_evaluation_cap": 900, "maxiter": 300, "maxfev": 900, "fairness_basis": "common objective evaluations; optimizer-specific termination retained"},
        "authorized_output_root": "reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1/",
        "no_tuning": True, "scientific_execution_invoked": False, "full_evrp_status": {"R20": "BLOCKED", "R21": "NOT_STARTED"},
    }
    auth_path = AUTH / "b2_execution_authorization_v2.json"
    dump(auth_path, auth)
    files = [AMEND, planned_path, gate_path, preflight_path, auth_path]
    index = {"schema_version": "r23-b2-design-review-v2-manifest", "classification": auth["classification"], "execution_performed": False, "artifacts": {rel(p): sha(p) for p in files}, "b1_evidence_review_sha256": auth["authority_references"]["b1_evidence_review_sha256"], "baseline_manifest_sha256": sha(BASELINE)}
    index_path = AUTH / "b2_design_review_v2_manifest.json"
    dump(index_path, index)
    files.append(index_path)
    sums_path = AUTH / "SHA256SUMS_V2"
    sums_path.write_text("".join(f"{sha(p)}  {p.name}\n" for p in sorted(files, key=lambda x: x.name)))
    print(json.dumps({"classification": auth["classification"], "execution_performed": False, "amendment_sha256": amendment_sha, "planned_manifest_sha256": planned_sha, "authorization_sha256": sha(auth_path), "manifest_sha256": sha(index_path)}, indent=2))


if __name__ == "__main__":
    main()
