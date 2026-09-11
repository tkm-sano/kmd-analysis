"""Execute exactly the already-authorized R23 Experiment B1 matrix."""
from __future__ import annotations

import hashlib, json, math, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "05_src"))
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, load_r22_instance, sha256_file
from traffic_simulation.r23_qaoa_aer.initialization import generate_initial_parameters, initialization_vector_sha256

AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1"
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v1"
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b/20260911_experiment_b_v1.json"
FORMAL = ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json"
R22 = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/r22"
INSTANCE_AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"
EXPECTED_DESIGN = "f14ce583419bee74964d1445f3cbc182da8bc8c482083992625396d7ab1b45ed"
EXPECTED_INIT = "43940ecc84d94197ad3eedc2069480f97246a185897ef477621c6159721ba665"
EXPECTED_RUN_MANIFEST = "9e987f38b1c492de81489c830fe8e988ae4ec2976851dcfdaea3af340f897dec"
EXPECTED_AUTH = "bb3e2e4251e980290bbd4516e8621f4eea920d542b1a6dad6053af5ccacdaa4c"

def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def versions():
    import numpy, scipy, qiskit, qiskit_aer, qiskit_algorithms, qiskit_optimization
    return {"python": sys.version, "platform": platform.platform(), "numpy": numpy.__version__, "scipy": scipy.__version__, "qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__, "qiskit_algorithms": qiskit_algorithms.__version__, "qiskit_optimization": qiskit_optimization.__version__, "environment_path": "/home/takuma/.conda/envs/evrp-quantum-temp"}

def authority_gate():
    design = json.loads(DESIGN.read_text()); auth = json.loads((AUTH/"b1_execution_authorization.json").read_text()); manifest = json.loads((AUTH/"b1_planned_run_manifest.json").read_text()); init = json.loads((AUTH/"initialization_authority.json").read_text()); instance_manifest = json.loads((INSTANCE_AUTH/"manifest.json").read_text()); formal = json.loads(FORMAL.read_text())
    checks = {
        "design_hash": sha(DESIGN) == EXPECTED_DESIGN == auth["design_sha256"],
        "initialization_authority_hash": sha(AUTH/"initialization_authority.json") == EXPECTED_INIT == auth["initialization_authority_sha256"],
        "b1_manifest_hash": sha(AUTH/"b1_planned_run_manifest.json") == EXPECTED_RUN_MANIFEST == auth["b1_planned_run_manifest_sha256"],
        "authorization_hash": sha(AUTH/"b1_execution_authorization.json") == EXPECTED_AUTH,
        "authorization_permits_execution": auth["execution_authorized"] is True and auth["execution_performed"] is False,
        "exact_36": len(manifest["runs"]) == 36 and manifest["run_count"] == 36,
        "unique_ids": len({x["run_id"] for x in manifest["runs"]}) == 36,
        "scope": all(x["n"] == 4 and x["optimizer"] == "COBYLA" and x["p"] in [2,3] and x["repetition"] == 1 for x in manifest["runs"]),
        "instances": {x["instance_id"] for x in manifest["runs"]} == {"routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"},
        "initializations": {x["initialization_id"] for x in manifest["runs"]} == {"fixed_0.1", "random_seed_11", "random_seed_23", "random_seed_37", "random_seed_53", "random_seed_71"},
        "no_research_wall_time_cap": manifest["wall_time_policy"] == "NO_RESEARCH_WALL_TIME_CAP",
        "instance_authority_hash": sha(INSTANCE_AUTH/"manifest.json") == auth["formal_instance_authority_manifest_sha256"],
        "lambda_hash": sha(ROOT / auth["lambda_policy"]) == auth["lambda_policy_sha256"] and json.loads((ROOT/auth["lambda_policy"]).read_text())["selected_lambda"] == 3.0,
        "r20_r21_r22_authority": instance_manifest["r20_authority_count"] == instance_manifest["r21_authority_count"] == instance_manifest["r22_authority_count"] == 15 and formal["authority"]["r21_status"] == "PASS" and formal["authority"]["r22_status"] == "PASS",
        "runtime": versions()["environment_path"] == "/home/takuma/.conda/envs/evrp-quantum-temp",
    }
    if not all(checks.values()): raise RuntimeError("EXPERIMENT_B1_AUTHORITY_DRIFT: " + json.dumps(checks))
    return design, auth, manifest, init, instance_manifest, formal, checks

def main():
    design, auth, plan, init_auth, instance_manifest, formal, gate = authority_gate()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"runs").mkdir(exist_ok=True)
    runtime = versions()
    preflight = {"classification": "B1_EXECUTION_PREFLIGHT", "authority_gate": "PASS", "known_validation_limitation": "KNOWN_VALIDATION_LIMITATION: pytest unavailable in frozen environment; not installed", "runtime": runtime, "design_sha256": sha(DESIGN), "initialization_authority_sha256": sha(AUTH/"initialization_authority.json"), "planned_run_manifest_sha256": sha(AUTH/"b1_planned_run_manifest.json"), "authorization_sha256": sha(AUTH/"b1_execution_authorization.json"), "instance_authority_manifest_sha256": sha(INSTANCE_AUTH/"manifest.json"), "lambda_policy_sha256": auth["lambda_policy_sha256"], "expected_condition_count": 36, "execution_order": [x["run_id"] for x in plan["runs"]], "research_wall_time_cap": None, "execution_started_utc": datetime.now(timezone.utc).isoformat()}
    write_json(OUT/"execution_preflight.json", preflight)
    terminal = []
    for index, planned in enumerate(plan["runs"], 1):
        run_id = planned["run_id"]
        init_id = planned["initialization_id"]; seed = planned["initialization_seed"]
        initial = generate_initial_parameters(planned["p"], init_id, seed)
        per_gate = {"authorized_run_id": run_id in preflight["execution_order"], "n": planned["n"] == 4, "instance_id": planned["instance_id"] in {"routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"}, "p": planned["p"] in [2,3], "initialization_id": init_id, "initialization_vector_sha256": initialization_vector_sha256(initial), "optimizer": planned["optimizer"] == "COBYLA", "lambda": 3.0, "maxiter": 300, "objective_evaluation_cap": 900, "shots": "NONE", "exact_reference": True}
        if not (per_gate["authorized_run_id"] and per_gate["n"] and per_gate["instance_id"] and per_gate["p"] and len(per_gate["initialization_vector_sha256"]) == 64 and per_gate["optimizer"] and per_gate["lambda"] == 3.0 and per_gate["maxiter"] == 300 and per_gate["objective_evaluation_cap"] == 900 and per_gate["shots"] == "NONE" and per_gate["exact_reference"]): raise RuntimeError("run preflight failure " + run_id)
        started = time.time()
        try:
            data = load_r22_instance(R22 / planned["instance_id"], planned["instance_id"])
            cfg = R23Config(p=planned["p"], optimizer="COBYLA", maxiter=300, max_evaluations=900, initial_parameters=initial, initialization_id=init_id, initialization_seed=seed, repetition=1, wall_time_seconds=None, seed=17, optimization_level=1, memory_limit_gib=8.0)
            result = run_single(data, cfg)
            record = {"schema_version": "r23-experiment-b1-terminal-record-v1", "classification": "RESEARCH_TERMINAL_RECORD", "run_id": run_id, "condition_id": planned["condition_id"], "planned_order": index, "authority": {"design_sha256": sha(DESIGN), "implementation_authority_sha256": sha(AUTH/"implementation_authority.json"), "initialization_authority_sha256": sha(AUTH/"initialization_authority.json"), "b1_authorization_sha256": sha(AUTH/"b1_execution_authorization.json"), "instance_authority_manifest_sha256": sha(INSTANCE_AUTH/"manifest.json"), "lambda_policy_sha256": auth["lambda_policy_sha256"]}, "run_preflight": per_gate, "result": result, "elapsed_process_seconds": time.time()-started}
        except Exception as exc:
            record = {"schema_version": "r23-experiment-b1-terminal-record-v1", "classification": "RESEARCH_TERMINAL_RECORD", "run_id": run_id, "condition_id": planned["condition_id"], "planned_order": index, "run_preflight": per_gate, "terminal_outcome": "IMPLEMENTATION_EXCEPTION", "exception": repr(exc), "elapsed_process_seconds": time.time()-started}
        write_json(OUT/"runs"/(run_id+".json"), record); terminal.append(record)
        write_json(OUT/"progress.json", {"completed": index, "total": 36, "last_run_id": run_id, "last_classification": record.get("result",{}).get("run_classification", record.get("terminal_outcome"))})
        print(f"[{index}/36] {run_id} -> {record.get('result',{}).get('run_classification', record.get('terminal_outcome'))}", flush=True)
    write_json(OUT/"terminal_records.json", {"classification":"RESEARCH_TERMINAL_RECORD_INDEX","records":[{"run_id":r["run_id"],"path":"runs/"+r["run_id"]+".json","sha256":sha(OUT/"runs"/(r["run_id"]+".json"))} for r in terminal]})
    write_json(OUT/"execution_preflight.json", {**preflight, "execution_completed_utc": datetime.now(timezone.utc).isoformat(), "completed_count": len(terminal)})
    print("B1_EXECUTION_COMPLETE", flush=True)
if __name__ == "__main__": main()
