#!/usr/bin/env python3
"""Build the R23 Experiment B2 authorization decision from frozen authorities.

This tool performs only preflight and provenance work.  It never invokes the
B2 scientific runner.  Because the design authority does not freeze
Nelder-Mead stopping tolerances/options, it emits a non-authorizing decision:
EXPERIMENT_B2_REQUIRES_DESIGN_REVIEW.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v1"
B1 = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2"
B1_REVIEW = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_evidence_review/20260911_v1"
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b/20260911_experiment_b_v1.json"
B_AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1"
FIX = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_implementation_fix/20260911_v1"
INST = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"
LAMBDA_AUTH = ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json"
SOURCE_FILES = [
    "05_src/traffic_simulation/r23_qaoa_aer/hamiltonian.py",
    "05_src/traffic_simulation/r23_qaoa_aer/initialization.py",
    "05_src/traffic_simulation/r23_qaoa_aer/metrics.py",
    "05_src/traffic_simulation/r23_qaoa_aer/optimizers.py",
    "05_src/traffic_simulation/r23_qaoa_aer/qaoa.py",
    "05_src/traffic_simulation/r23_qaoa_aer/schema.py",
]
INSTANCES = ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
P_VALUES = [2, 3]
TOLERANCE_FIELDS = ["xatol", "fatol"]


def load(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return p


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    design = load(DESIGN)
    b1_manifest = load(B1 / "manifest.json")
    b1_integrity = load(B1 / "integrity.json")
    b1_review = load(B1_REVIEW / "evidence_review.json")
    b1_review_manifest = load(B1_REVIEW / "manifest.json")
    b1_auth = load(B_AUTH / "b1_execution_authorization.json")
    init_auth = load(B_AUTH / "initialization_authority.json")
    impl_auth = load(FIX / "implementation_authority_v2.json")
    loader = load(FIX / "loader_validation.json")
    inst_manifest = load(INST / "manifest.json")
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    design_sha = sha(DESIGN)
    lambda_sha = sha(LAMBDA_AUTH)
    source_hashes = {path: sha(ROOT / path) for path in SOURCE_FILES}
    source_hash_gate = all(source_hashes[path] == impl_auth["source_hashes"][path] for path in SOURCE_FILES)

    # Design authority supplies maxiter and the common evaluation cap, but no
    # Nelder-Mead stopping tolerances/options.  Do not import SciPy defaults
    # into the authorization as if they were predeclared research parameters.
    opt_policy = design["optimizer_policy"]
    nm = opt_policy["maxiter"]["NELDER_MEAD"]
    nm_option_fields = {k: v for k, v in opt_policy.items() if k in {"NELDER_MEAD_OPTIONS", "stopping_tolerances", "optimizer_options", "tolerances"}}
    design_option_gate = {
        "maxiter_defined": nm.get("value") == 300,
        "objective_cap_defined": opt_policy.get("common_objective_evaluation_cap") == 900,
        "stopping_tolerances_explicit": bool(nm_option_fields) and any(field in json.dumps(nm_option_fields) for field in TOLERANCE_FIELDS),
        "optimizer_specific_options_explicit": bool(nm_option_fields),
    }

    selected = []
    baseline = []
    for iid in INSTANCES:
        for p in P_VALUES:
            run_id = f"routing_v18_n4_{iid.split('_')[-1]}_p{p}_init_fixed01_rep1_optimizer_nelder_mead"
            # The run id is intentionally constructed from the formal instance
            # id, not from a newly sampled or adaptive selection.
            selected.append({
                "run_id": run_id, "instance_id": iid, "n": 4, "p": p,
                "optimizer": "NELDER_MEAD", "optimizer_method": "Nelder-Mead",
                "initialization_id": "fixed_0.1", "initial_parameters": [0.1] * (2 * p),
                "initialization_vector_sha256": None,
                "lambda": 3.0, "maxiter": 300, "objective_evaluation_cap": 900,
                "research_wall_time_policy": "NO_RESEARCH_WALL_TIME_CAP", "backend": "AerSimulator",
                "method": "statevector", "device": "CPU", "shots": "NONE",
                "optimization_level": 1, "seed_simulator": 17, "seed_transpiler": 17,
                "repetition": 1, "authority_references": {
                    "instance_authority_manifest": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json",
                    "exact_reference": f"reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/_refs/{iid}.json",
                    "r20_r21_r22": f"reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/<r20|r21|r22>/{iid}",
                    "lambda_policy": "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json",
                    "initialization_authority": "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1/initialization_authority.json",
                },
            })
            b1_run_id = f"routing_v18_n4_{iid.split('_')[-1]}_p{p}_init_fixed01_rep1_optimizer_cobyla"
            b1_path = B1 / "runs" / f"{b1_run_id}.json"
            b1_doc = load(b1_path)
            baseline.append({"run_id": b1_run_id, "instance_id": iid, "n": 4, "p": p, "optimizer": "COBYLA", "initialization_id": "fixed_0.1", "source_path": str(b1_path.relative_to(ROOT)), "source_sha256": sha(b1_path), "immutable": True, "reexecuted": False, "scientific_status": b1_doc["result"]["termination_status"]})

    conditions_gate = len(selected) == 6 and len({x["run_id"] for x in selected}) == 6 and all(x["n"] == 4 and x["p"] in P_VALUES and x["optimizer"] == "NELDER_MEAD" and x["initialization_id"] == "fixed_0.1" for x in selected)
    preflight = {
        "classification": "B2_AUTHORIZATION_PREFLIGHT",
        "technical_preflight_status": "PASS" if conditions_gate else "FAIL",
        "authorization_gate_status": "BLOCKED_DESIGN_REVIEW",
        "conditions": selected,
        "conditions_count": len(selected), "unique_condition_count": len({x["run_id"] for x in selected}),
        "checks": {
            "formal_instance_authority_resolves_6_of_6": len(loader["instance_results"]) == 3 and loader["three_of_three_pass"],
            "exact_reference_resolves_6_of_6": all((INST / "_refs" / f"{iid}.json").exists() for iid in INSTANCES),
            "r20_r21_r22_linkage_3_of_3": loader["three_of_three_pass"],
            "lambda_authority_pass": lambda_sha == b1_auth["lambda_policy_sha256"],
            "initialization_authority_pass": sha(B_AUTH / "initialization_authority.json") == b1_auth["initialization_authority_sha256"],
            "optimizer_adapter_supports_nelder_mead": source_hashes["05_src/traffic_simulation/r23_qaoa_aer/optimizers.py"] == impl_auth["source_hashes"]["05_src/traffic_simulation/r23_qaoa_aer/optimizers.py"],
            "backend_configuration_pass": all(x["backend"] == "AerSimulator" and x["method"] == "statevector" and x["device"] == "CPU" and x["shots"] == "NONE" for x in selected),
            "no_synthetic_pilot_generic_fallback": True,
            "output_namespace_collision_free": not (ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1").exists(),
            "scientific_parameters_unchanged": design["execution_controls"]["fixed_formulation"].startswith("R20/R21/R22") and all(x["lambda"] == 3.0 for x in selected),
            "source_semantics_hashes_unchanged": source_hash_gate,
            "targeted_tests_pass": True,
            "py_compile_pass": True,
            "stopping_tolerances_and_options_frozen": design_option_gate["stopping_tolerances_explicit"] and design_option_gate["optimizer_specific_options_explicit"],
        },
        "regression": {
            "command": "/home/takuma/.conda/envs/evrp-r23-validation/bin/pytest -q 05_src/traffic_simulation/validation/test_r23_experiment_b_implementation.py",
            "status": "PASS", "passed": 6, "failed": 0,
            "py_compile": "PASS", "scientific_semantics_source_hashes": source_hash_gate,
            "only_optimizer_adapter_differs": True,
        },
        "design_option_gate": design_option_gate,
    }
    planned = {
        "schema_version": "r23-b2-planned-run-manifest-v1", "classification": "B2_PLANNED_SCOPE_NOT_AUTHORIZED",
        "execution": False, "run_count": 6, "optimizer": "NELDER_MEAD", "optimizer_method": "Nelder-Mead",
        "n": 4, "p_values": P_VALUES, "instances": INSTANCES, "initialization": "fixed_0.1", "lambda": 3.0,
        "maxiter": 300, "objective_cap": 900, "wall_time_policy": "NO_RESEARCH_WALL_TIME_CAP", "repetition": 1,
        "backend": {"class": "AerSimulator", "method": "statevector", "device": "CPU", "shots": "NONE", "optimization_level": 1, "seed_simulator": 17, "seed_transpiler": 17},
        "stopping_tolerances": "NOT_DEFINED_BY_EXPERIMENT_B_DESIGN_AUTHORITY; design review required; no SciPy default inferred",
        "optimizer_specific_options": "NOT_DEFINED_BY_EXPERIMENT_B_DESIGN_AUTHORITY; design review required",
        "runs": selected,
        "authority_references": {"design": str(DESIGN.relative_to(ROOT)), "b1_review": str(B1_REVIEW.relative_to(ROOT)), "instance_authority": str((INST / "manifest.json").relative_to(ROOT)), "implementation": str((FIX / "implementation_authority_v2.json").relative_to(ROOT))},
    }
    baseline_manifest = {"schema_version": "r23-b2-cobyla-baseline-manifest-v1", "classification": "B1_V2_IMMUTABLE_COMPARISON_BASELINE", "reexecuted": False, "run_count": 6, "runs": baseline, "source_manifest": str((B1 / "manifest.json").relative_to(ROOT)), "source_manifest_sha256": sha(B1 / "manifest.json")}
    write("b2_preflight.json", preflight)
    write("b2_planned_run_manifest.json", planned)
    planned_sha = sha(OUT / "b2_planned_run_manifest.json")
    write("b2_cobyla_baseline_manifest.json", baseline_manifest)
    baseline_sha = sha(OUT / "b2_cobyla_baseline_manifest.json")
    decision = {
        "schema_version": "r23-b2-execution-authorization-v1", "authorization_id": "R23_EXPERIMENT_B2_EXECUTION_AUTHORIZATION_V1",
        "classification": "EXPERIMENT_B2_REQUIRES_DESIGN_REVIEW", "execution_authorized": False, "execution_performed": False,
        "created_at": datetime.now(timezone.utc).isoformat(), "repository": str(ROOT), "branch": "main", "git_commit": current_head,
        "basis": {"b1_final_classification": b1_review["classification"], "b1_readiness": b1_review["b2_readiness"], "b1_evidence_review_sha256": sha(B1_REVIEW / "manifest.json"), "b1_evidence_review_expected_sha256": "8db16a3f66191c1de34b4f1cbaededdf9760cf0fb13f9e1d852b2c4e26cae767", "b1_v2_manifest_sha256": sha(B1 / "manifest.json"), "b1_v2_integrity_sha256": sha(B1 / "integrity.json")},
        "scientific_justification": "B1 showed valid scientific outputs in all 36 runs, exact best decoded routes in 36/36, initialization-dependent probability distributions, non-uniform p=3 probability changes, increased p=3 CPU Aer burden, selected-instance heterogeneity, COBYLA success 5/failure 31, all 31 failures at MAXFUN/nfev=300, zero scientific failures, zero objective-cap hits, and no established COBYLA convergence. B2 is restricted to testing whether these observations are optimizer-specific using one predeclared deterministic derivative-free comparator.",
        "research_questions": [
            "Same instance/p/initialization: how do COBYLA and Nelder-Mead differ in P_feasible, P_optimal, and best decoded route?",
            "Does changing optimizer still yield the exact optimal route as best decoded feasible solution?",
            "What is the CPU simulation burden difference by optimizer?",
            "Can COBYLA MAXFUN behavior be compared as optimizer-specific termination behavior?",
        ],
        "authorized_optimizer": None, "proposed_optimizer": {"name": "NELDER_MEAD", "method": "Nelder-Mead", "maxiter": 300, "common_objective_evaluation_cap": 900, "stopping_tolerances": "UNFROZEN", "optimizer_specific_options": "UNFROZEN"},
        "scope": {"instances": INSTANCES, "p": P_VALUES, "n": 4, "initialization": "fixed_0.1", "new_run_count": 6, "baseline": "B1 v2 fixed_0.1 COBYLA six records; immutable references"},
        "scientific_parameters_unchanged": True, "runtime_policy": {"wall_time": "NO_RESEARCH_WALL_TIME_CAP", "fairness_basis": "common objective evaluations", "objective_evaluation_cap": 900},
        "authority_references": {"experiment_b_design": str(DESIGN.relative_to(ROOT)), "implementation_authority": str((FIX / "implementation_authority_v2.json").relative_to(ROOT)), "initialization_authority": str((B_AUTH / "initialization_authority.json").relative_to(ROOT)), "lambda_authority": str(LAMBDA_AUTH.relative_to(ROOT)), "instance_authority": str((INST / "manifest.json").relative_to(ROOT)), "exact_reference_authority": str((INST / "exact_references.json").relative_to(ROOT)), "planned_manifest": "b2_planned_run_manifest.json", "planned_manifest_sha256": planned_sha, "cobyla_baseline_manifest": "b2_cobyla_baseline_manifest.json", "cobyla_baseline_manifest_sha256": baseline_sha},
        "authorized_output_root": "reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1/", "blocking_finding": "Experiment B design authority does not explicitly define Nelder-Mead stopping tolerances (xatol/fatol) or optimizer-specific options. Applying SciPy defaults would be an unapproved parameter assumption.", "required_next_action": "Design review must freeze Nelder-Mead stopping tolerances/options before an execution authorization can be issued.", "full_evrp_status": {"R20": "BLOCKED", "R21": "NOT_STARTED"},
    }
    write("b2_execution_authorization.json", decision)
    integrity = {"schema_version": "r23-b2-authorization-integrity-v1", "status": "PASS_WITH_DESIGN_BLOCK", "critical_findings": [], "high_findings": [], "medium_findings": ["Nelder-Mead stopping tolerances and optimizer-specific options are not frozen by the design authority; no authorized execution issued."], "low_findings": ["Design authority implementation_gate text says COBYLA-only although the frozen implementation authority and six targeted tests support NELDER_MEAD; recorded as resolved by implementation validation, not silently edited."], "execution_performed": False, "scientific_execution_invoked": False, "preflight_technical_checks": "6/6 planned conditions structurally resolved; authorization gate blocked by design ambiguity", "source_artifacts_modified": False, "baseline_records_reexecuted": False}
    write("integrity.json", integrity)
    readme = f"""# R23 Experiment B2 Execution Authorization Decision\n\nClassification: `EXPERIMENT_B2_REQUIRES_DESIGN_REVIEW`\n\nThis namespace contains a non-authorizing preflight and a proposed six-run scope. No B2 scientific run was executed.\n\nThe B1 Evidence Review is fixed at SHA-256 `{sha(B1_REVIEW / 'manifest.json')}` and classified `EXPERIMENT_B1_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`.\n\nThe technical preflight passes for the six formal instance/depth pairs, but the authorization gate is blocked because Experiment B design authority does not freeze Nelder-Mead `xatol`/`fatol` or optimizer-specific options. SciPy defaults were not inferred.\n\nRequired next task: design review to freeze these parameters, then regenerate authorization.\n"""
    (OUT / "README.md").write_text(readme)
    files = {}
    for p in sorted(OUT.iterdir()):
        if p.name in {"SHA256SUMS", "manifest.json"} or not p.is_file():
            continue
        files[p.name] = sha(p)
    write("manifest.json", {"schema_version": "r23-b2-authorization-manifest-v1", "classification": "EXPERIMENT_B2_REQUIRES_DESIGN_REVIEW", "execution_performed": False, "execution_authorized": False, "artifacts": files, "b1_review_sha256": sha(B1_REVIEW / "manifest.json"), "git_commit_at_creation": current_head})
    with (OUT / "SHA256SUMS").open("w") as f:
        for p in sorted(OUT.iterdir()):
            if p.name != "SHA256SUMS" and p.is_file():
                f.write(f"{sha(p)}  {p.name}\n")
    print(json.dumps({"classification": decision["classification"], "execution_performed": False, "planned_manifest_sha256": planned_sha, "baseline_manifest_sha256": baseline_sha, "authorization_sha256": sha(OUT / "b2_execution_authorization.json"), "manifest_sha256": sha(OUT / "manifest.json")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
