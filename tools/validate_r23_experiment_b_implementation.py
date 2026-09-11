#!/usr/bin/env python3
"""Non-research smoke validation for the R23 Experiment B implementation."""

from __future__ import annotations

import json
import math
from pathlib import Path

from qiskit_algorithms.optimizers import COBYLA

from traffic_simulation.r23_qaoa_aer.initialization import generate_initial_parameters, initialization_vector_sha256
from traffic_simulation.r23_qaoa_aer.optimizers import ObjectiveEvaluationCapReached, minimize_objective
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, R23Input


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_implementation_validation/20260911_v1"


def synthetic_input() -> R23Input:
    return R23Input(
        "synthetic_b_n2", 2, (1, 2), 0, 3.0,
        {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0}, {}, "i" * 64, "q" * 64,
        2.0, 1.0, frozenset({(1, 0, 0, 1)}), frozenset({(-1, 1, 1, -1)}),
        frozenset({(1, 2)}),
        {0: {0: 0.0, 1: 1.0, 2: 1.0}, 1: {0: 1.0, 1: 0.0, 2: 1.0}, 2: {0: 1.0, 1: 1.0, 2: 0.0}},
        {"ising_global_minimum_energy": 0.0},
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = synthetic_input()
    smoke = {"classification": "NON_RESEARCH_IMPLEMENTATION_VALIDATION", "execution_scope": "synthetic_n2_only", "formal_experiment_b_conditions_used": False}

    def objective(values):
        return float((values[0] - 0.3) ** 2 + (values[1] + 0.2) ** 2)

    native = COBYLA(maxiter=20, options={"maxiter": 20}).minimize(objective, [0.1, 0.1])
    adapted = minimize_objective(optimizer_name="COBYLA", fun=objective, x0=[0.1, 0.1], maxiter=20, objective_cap=900)
    smoke["smoke_a_cobyla_regression"] = {
        "status": "PASS" if adapted.final_parameters == list(native.x) and adapted.final_objective == float(native.fun) and adapted.nfev == int(native.nfev) else "FAIL",
        "qiskit_wrapper": {"final_parameters": list(native.x), "final_objective": float(native.fun), "nfev": int(native.nfev)},
        "adapter": {"final_parameters": adapted.final_parameters, "final_objective": adapted.final_objective, "nfev": adapted.nfev},
        "comparison_tolerance": "exact float equality observed for this deterministic objective",
    }

    smoke_b = run_single(data, R23Config(p=1, optimizer="NELDER_MEAD", maxiter=5, max_evaluations=20))
    smoke["smoke_b_nelder_mead"] = {
        "status": "PASS" if smoke_b["optimizer_method"] == "Nelder-Mead" and smoke_b["nfev"] > 0 and math.isfinite(smoke_b["final_objective"]) else "FAIL",
        "optimizer_method": smoke_b["optimizer_method"], "nfev": smoke_b["nfev"], "nit": smoke_b["nit"],
        "optimizer_status": smoke_b["optimizer_status"], "optimizer_success": smoke_b["optimizer_success"],
        "termination_status": smoke_b["termination_status"], "termination_message": smoke_b["termination_message"],
        "final_objective": smoke_b["final_objective"], "P_feasible": smoke_b["probability_metrics"]["P_feasible_exact"],
        "P_optimal": smoke_b["probability_metrics"]["P_opt"], "absolute_optimality_gap": smoke_b.get("absolute_optimality_gap"),
        "relative_optimality_gap": smoke_b.get("relative_optimality_gap"),
    }

    smoke_c = run_single(data, R23Config(p=1, optimizer="COBYLA", maxiter=100, max_evaluations=2))
    smoke["smoke_c_objective_cap"] = {
        "status": "PASS" if smoke_c["budget_hit"] and smoke_c["termination_status"] == "OBJECTIVE_EVALUATION_CAP_REACHED" and smoke_c["objective_evaluation_count"] == 2 and smoke_c["expectation_evaluation_count"] == 3 else "FAIL",
        "objective_evaluation_count": smoke_c["objective_evaluation_count"], "expectation_evaluation_count": smoke_c["expectation_evaluation_count"],
        "budget_hit": smoke_c["budget_hit"], "termination_status": smoke_c["termination_status"], "termination_source": smoke_c["termination_source"],
    }

    vectors = {}
    for p in (2, 3):
        for seed in (11, 23, 37, 53, 71):
            first = generate_initial_parameters(p, f"random_seed_{seed}")
            second = generate_initial_parameters(p, f"random_seed_{seed}")
            vectors[f"p{p}_seed{seed}"] = {"parameters": list(first), "sha256": initialization_vector_sha256(first), "deterministic": first == second, "dimension": len(first), "gamma_in_domain": all(-math.pi <= x < math.pi for x in first[:p]), "beta_in_domain": all(-math.pi / 2 <= x < math.pi / 2 for x in first[p:])}
    smoke["smoke_d_initialization"] = {"status": "PASS" if all(v["deterministic"] and v["dimension"] in (4, 6) and v["gamma_in_domain"] and v["beta_in_domain"] for v in vectors.values()) else "FAIL", "fixed_0.1_p2": list(generate_initial_parameters(2, "fixed_0.1")), "vectors": vectors, "rng": "numpy.random.Generator(numpy.random.PCG64(seed))"}
    smoke["all_smokes_pass"] = all(smoke[key]["status"] == "PASS" for key in ("smoke_a_cobyla_regression", "smoke_b_nelder_mead", "smoke_c_objective_cap", "smoke_d_initialization"))
    (OUT / "smoke_validation.json").write_text(json.dumps(smoke, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
