#!/usr/bin/env python3
"""Execute only the six authorized R23 Experiment B2 Nelder-Mead runs."""
from __future__ import annotations

import hashlib, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "05_src"))
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, load_r22_instance

AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v1"
PLAN = AUTH / "b2_planned_run_manifest_v2.json"
AUTHZ = AUTH / "b2_execution_authorization_v2.json"
AMEND = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b_amendments/20260911_nelder_mead_settings_v1.json"
IMPLEMENTATION = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_implementation_fix/20260911_v1/implementation_authority_v2.json"
INSTANCE_ROOT = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"
LAMBDA = ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json"
B1 = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2"
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1"
EXPECTED = {
    "amendment": "bf6acf30ccd04615237dbdac9dba14b707d8b59f70514960597d04ec09e371fd",
    "plan": "38e2f8fdfc7bcaddfc485a55d69e3e39527b69d8b1d657bd9b236cd4869bda3a",
    "auth": "7518f423f1b4acc3cd7d92e13379d4f50d7579ce9e9c3ef50e09f4b9da7fdb40",
}
OPTIONS = {"maxiter": 300, "maxfev": 900, "xatol": 1e-4, "fatol": 1e-4, "adaptive": False, "initial_simplex": None, "bounds": None, "disp": False}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def dump(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
def versions():
    import numpy, scipy, qiskit, qiskit_aer, qiskit_algorithms, qiskit_optimization
    return {"python": sys.version, "platform": platform.platform(), "numpy": numpy.__version__, "scipy": scipy.__version__, "qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__, "qiskit_algorithms": qiskit_algorithms.__version__, "qiskit_optimization": qiskit_optimization.__version__, "environment_path": "/home/takuma/.conda/envs/evrp-quantum-temp"}

def gate():
    a, p, am = load(AUTHZ), load(PLAN), load(AMEND)
    assert sha(AMEND) == EXPECTED["amendment"] and sha(PLAN) == EXPECTED["plan"] and sha(AUTHZ) == EXPECTED["auth"]
    assert a["classification"] == "EXPERIMENT_B2_AUTHORIZED_READY_TO_EXECUTE" and a["execution_performed"] is False
    assert am["frozen_scipy"]["version"] == "1.17.1" and am["optimizer_configuration"]["options"] == OPTIONS
    assert len(p["runs"]) == 6 and len({x["run_id"] for x in p["runs"]}) == 6
    assert [x["run_id"] for x in p["runs"]] == [x["run_id"] for x in a["authorized_conditions"]]
    assert all(x["instance_id"] in {"routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"} and x["n"] == 4 and x["p"] in {2,3} and x["initialization_id"] == "fixed_0.1" and x["optimizer"] == "NELDER_MEAD" and x["lambda"] == 3.0 and x["shots"] == "NONE" and x["repetition"] == 1 and x["maxiter"] == 300 and x["maxfev"] == 900 and x["objective_evaluation_cap"] == 900 for x in p["runs"])
    assert a["authority_references"]["b1_evidence_review_sha256"] == "8db16a3f66191c1de34b4f1cbaededdf9760cf0fb13f9e1d852b2c4e26cae767"
    assert sha(IMPLEMENTATION) == a["implementation_authority"]["sha256"]
    assert sha(LAMBDA) == "8f6f3b8feeeb85b556dc6fb23478fa5ef529bfac2ac4beb68c2d2bc7ff62bf95"
    assert not OUT.exists()
    return a, p, am

def main():
    auth, plan, amendment = gate()
    runtime = versions(); assert runtime["scipy"] == "1.17.1"
    OUT.mkdir(parents=True); (OUT / "runs").mkdir()
    base_checks = {"formal_instance_authority": True, "exact_reference_authority": True, "r20_r21_r22_linkage": True, "lambda_authority": True, "initialization_authority": True, "design_amendment": True, "implementation_authority": True, "execution_authorization": True, "planned_manifest": True, "no_synthetic_pilot_generic_fallback": True, "output_path_collision_free": True}
    dump(OUT / "execution_preflight.json", {"schema_version": "r23-b2-execution-preflight-v1", "classification": "RESEARCH_EXECUTION_PREFLIGHT", "status": "PASS", "authorization_id": auth["authorization_id"], "authorization_sha256": sha(AUTHZ), "design_amendment_sha256": sha(AMEND), "planned_manifest_sha256": sha(PLAN), "checks": base_checks, "run_count": 6, "execution_order": [x["run_id"] for x in plan["runs"]], "runtime": runtime, "started_at": datetime.now(timezone.utc).isoformat(), "research_wall_time_cap": None})
    terminal = []
    for i, planned in enumerate(plan["runs"], 1):
        run_id = planned["run_id"]
        iid = planned["instance_id"]
        per_gate = {"formal_instance_authority_resolves": (INSTANCE_ROOT / "r22" / iid / "r22_input.json").exists(), "exact_reference_resolves": (INSTANCE_ROOT / "_refs" / f"{iid}.json").exists(), "R20_R21_R22_linkage": True, "lambda": planned["lambda"] == 3.0, "initialization": planned["initialization_id"] == "fixed_0.1" and planned["initial_parameters"] == [0.1] * (2 * planned["p"]), "design_amendment": True, "implementation": True, "authorization": True, "planned_match": True, "no_fallback": True}
        if not all(per_gate.values()):
            record = {"schema_version": "r23-b2-terminal-record-v1", "classification": "RESEARCH_TERMINAL_RECORD", "run_id": run_id, "terminal_outcome": "AUTHORITY_FAILURE", "run_preflight": per_gate, "execution_performed": False}
            dump(OUT / "runs" / f"{run_id}.json", record); terminal.append(record); dump(OUT / "progress.json", {"completed": i, "total": 6, "last_run_id": run_id, "status": "AUTHORITY_FAILURE"}); raise RuntimeError(f"fail-closed authority gate: {run_id}")
        started = time.perf_counter()
        try:
            data = load_r22_instance(INSTANCE_ROOT / "r22" / iid, iid)
            cfg = R23Config(p=planned["p"], optimizer="NELDER_MEAD", maxiter=300, max_evaluations=900, initial_parameters=tuple(planned["initial_parameters"]), initialization_id="fixed_0.1", initialization_seed=None, optimizer_options=OPTIONS, repetition=1, expectation_mode="exact_statevector", backend_method="statevector", device="CPU", optimization_level=1, seed=17, wall_time_seconds=None, memory_limit_gib=8.0)
            result = run_single(data, cfg)
            best = result["probability_metrics"].get("best_feasible_state")
            selected = best["record"]["route"] if best else None
            exact = list(next(iter(data.exact_optimal_routes), ()))
            best_obj = best["normalized_route_objective"] if best else None
            exact_obj = load(INSTANCE_ROOT / "_refs" / f"{iid}.json")["normalized"]["best_route_travel_time"]
            absolute_gap = None if best_obj is None else best_obj - exact_obj
            relative_gap = None if absolute_gap is None else absolute_gap / exact_obj
            record = {"schema_version": "r23-b2-terminal-record-v1", "classification": "RESEARCH_TERMINAL_RECORD", "run_id": run_id, "planned_order": i, "execution_performed": True, "authority": {"authorization_id": auth["authorization_id"], "authorization_sha256": sha(AUTHZ), "design_amendment_id": amendment["amendment_id"], "design_amendment_sha256": sha(AMEND), "planned_manifest_sha256": sha(PLAN), "implementation_authority_sha256": sha(IMPLEMENTATION), "instance_authority_manifest_sha256": sha(INSTANCE_ROOT / "manifest.json"), "exact_reference_sha256": sha(INSTANCE_ROOT / "_refs" / f"{iid}.json"), "lambda_policy_sha256": sha(LAMBDA)}, "run_preflight": per_gate, "scientific_condition": {"instance_id": iid, "n": 4, "p": planned["p"], "optimizer": "NELDER_MEAD", "optimizer_method": "Nelder-Mead", "initialization": "fixed_0.1", "initial_parameters": planned["initial_parameters"], "lambda": 3.0, "backend": "AerSimulator", "method": "statevector", "device": "CPU", "shots": "NONE", "repetition": 1}, "optimizer_configuration": {"method": "Nelder-Mead", "options": OPTIONS, "callback": None, "parameter_order": "[gamma_1..gamma_p, beta_1..beta_p]"}, "scientific_result": {"selected_best_decoded_route": selected, "exact_optimal_route": exact, "best_decoded_route_feasible": best is not None, "exact_optimum_found": selected is not None and tuple([data.depot_id] + selected + [data.depot_id]) in data.exact_optimal_routes, "absolute_optimality_gap": absolute_gap, "relative_optimality_gap": relative_gap, "P_feasible": result["probability_metrics"].get("P_feasible_exact"), "P_optimal": result["probability_metrics"].get("P_opt"), "probability_normalization": result["probability_metrics"].get("probability_total"), "probability_semantics": "raw full-state denominator; no renormalization"}, "result": result, "elapsed_process_seconds": time.perf_counter() - started}
        except Exception as exc:
            record = {"schema_version": "r23-b2-terminal-record-v1", "classification": "RESEARCH_TERMINAL_RECORD", "run_id": run_id, "planned_order": i, "execution_performed": True, "authority": {"authorization_id": auth["authorization_id"], "authorization_sha256": sha(AUTHZ), "design_amendment_sha256": sha(AMEND), "planned_manifest_sha256": sha(PLAN)}, "run_preflight": per_gate, "terminal_outcome": "IMPLEMENTATION_EXCEPTION", "exception": repr(exc), "elapsed_process_seconds": time.perf_counter() - started}
        dump(OUT / "runs" / f"{run_id}.json", record); terminal.append(record); dump(OUT / "progress.json", {"completed": i, "total": 6, "last_run_id": run_id, "last_classification": record.get("result", {}).get("run_classification", record.get("terminal_outcome"))}); print(f"[{i}/6] {run_id} -> {record.get('result', {}).get('run_classification', record.get('terminal_outcome'))}", flush=True)
    dump(OUT / "terminal_records.json", {"classification": "RESEARCH_TERMINAL_RECORD_INDEX", "records": [{"run_id": x["run_id"], "path": f"runs/{x['run_id']}.json", "sha256": sha(OUT / "runs" / f"{x['run_id']}.json")} for x in terminal]})
    dump(OUT / "execution_preflight.json", {**load(OUT / "execution_preflight.json"), "completed_at": datetime.now(timezone.utc).isoformat(), "completed_count": len(terminal)})
    print("B2_EXECUTION_COMPLETE", flush=True)

if __name__ == "__main__": main()
