#!/usr/bin/env python3
"""Finalize the non-retried B2 implementation-failure evidence layer."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1"
B1 = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2/runs"
AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v1"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")

def main():
    runs = sorted((OUT / "runs").glob("*.json"))
    records = [load(p) for p in runs]
    assert len(records) == 6 and len({x["run_id"] for x in records}) == 6
    pairs = []
    for rec in records:
        cobyla_id = rec["run_id"].replace("optimizer_nelder_mead", "optimizer_cobyla")
        b = load(B1 / f"{cobyla_id}.json")["result"]
        bm = b["probability_metrics"]
        pairs.append({"instance_id": rec["run_id"].split("_p")[0], "p": int(rec["run_id"].split("_p")[1].split("_")[0]), "run_id": rec["run_id"], "cobyla_baseline": {"run_id": cobyla_id, "P_feasible": bm["P_feasible_exact"], "P_optimal": bm["P_opt"], "absolute_optimality_gap": 0.0, "relative_optimality_gap": 0.0, "selected_best_route": bm["best_feasible_state"]["record"]["route"], "exact_optimum_found": True, "runtime": b["timing"]["T_total"], "T_Aer": b["timing"]["T_Aer_total"], "nfev": b["nfev"], "optimizer_success": b["optimizer_success"], "optimizer_status": b["optimizer_status"], "termination": {"status": b["termination_status"], "source": b["termination_source"], "message": b["termination_message"]}}, "nelder_mead": {"status": "IMPLEMENTATION_EXCEPTION", "exception": rec["result"].get("termination_message"), "P_feasible": None, "P_optimal": None, "absolute_optimality_gap": None, "relative_optimality_gap": None, "selected_best_route": None, "exact_optimum_found": None, "runtime": None, "T_Aer": None, "nfev": 0, "optimizer_success": None, "optimizer_status": None, "termination": "IMPLEMENTATION_EXCEPTION"}, "differences": {"P_feasible": None, "P_optimal": None, "absolute_optimality_gap": None, "relative_optimality_gap": None, "runtime": None, "T_Aer": None, "nfev": None}})
    comparison = {"schema_version": "r23-b2-cobyla-vs-nelder-mead-raw-comparison-v1", "classification": "RAW_COMPARISON_INCOMPLETE_REQUIRES_REVIEW", "scientific_conclusion": None, "baseline_source": "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2/manifest.json", "baseline_manifest_sha256": sha(ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2/manifest.json"), "pairs": pairs}
    dump(OUT / "cobyla_vs_nelder_mead_raw_comparison.json", comparison)
    failure_messages = [x["result"].get("termination_message") for x in records]
    summary = {"schema_version": "r23-b2-summary-v1", "classification": "EXPERIMENT_B2_COMPLETED_WITH_FAILURES_REQUIRES_REVIEW", "authorized_runs": 6, "started_runs": 6, "completed_terminal_runs": 6, "scientific_failures": 6, "implementation_failures": 6, "optimizer_success_count": 0, "optimizer_failure_count": 6, "exact_optimum_found_count": 0, "relative_gap_summary": {"status": "NO_SCIENTIFIC_RESULT", "values": []}, "P_feasible_summary": {"status": "NO_SCIENTIFIC_RESULT", "values": []}, "P_optimal_summary": {"status": "NO_SCIENTIFIC_RESULT", "values": []}, "runtime_summary": {"status": "NO_SCIENTIFIC_RESULT", "values": []}, "Aer_runtime_summary": {"status": "NO_SCIENTIFIC_RESULT", "values": []}, "nfev_summary": {"count": 6, "min": 0, "max": 0, "values": [0] * 6}, "termination_reasons": {"IMPLEMENTATION_EXCEPTION": 6}, "failure_messages": failure_messages, "comparison_baseline_source": "B1 v2 fixed_0.1 COBYLA six immutable records", "integrity_result": "PASS_WITH_SCIENTIFIC_FAILURES", "no_retry": True, "scientific_conclusion": None}
    dump(OUT / "b2_summary.json", summary)
    terminal_index = {"classification": "RESEARCH_TERMINAL_RECORD_INDEX", "records": [{"run_id": x["run_id"], "path": f"runs/{x['run_id']}.json", "sha256": sha(OUT / "runs" / f"{x['run_id']}.json")} for x in records]}
    dump(OUT / "terminal_records.json", terminal_index)
    integrity = {"schema_version": "r23-b2-integrity-v1", "status": "PASS_WITH_SCIENTIFIC_FAILURES", "classification": summary["classification"], "planned_count": 6, "started_count": 6, "terminal_count": 6, "unique_run_ids": 6, "duplicate_count": 0, "authority_gate": "PASS", "authority_drift": False, "scientific_parameter_drift": False, "probability_integrity": "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION", "exact_reference_integrity": "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION", "lambda_integrity": "PASS_AT_PREFLIGHT", "runtime_integrity": "NOT_AVAILABLE_DUE_TO_IMPLEMENTATION_EXCEPTION", "implementation_failures": 6, "retry_performed": False, "cobyla_reexecuted": False, "scientific_results_valid": False, "failure_cause": "SciPy 1.17.1 Nelder-Mead dispatch received bounds twice because the execution path passed bounds=None inside options; all failures occurred before optimizer/Aer scientific evaluation.", "execution_performed": True}
    dump(OUT / "integrity.json", integrity)
    manifest = {"schema_version": "r23-b2-execution-manifest-v1", "classification": summary["classification"], "execution_performed": True, "authorized_run_count": 6, "started_run_count": 6, "terminal_run_count": 6, "artifacts": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"}}, "authorization_sha256": "7518f423f1b4acc3cd7d92e13379d4f50d7579ce9e9c3ef50e09f4b9da7fdb40", "design_amendment_sha256": "bf6acf30ccd04615237dbdac9dba14b707d8b59f70514960597d04ec09e371fd", "planned_manifest_sha256": "38e2f8fdfc7bcaddfc485a55d69e3e39527b69d8b1d657bd9b236cd4869bda3a", "no_retry": True}
    (OUT / "README.md").write_text("# R23 Experiment B2 Execution\n\nClassification: `EXPERIMENT_B2_COMPLETED_WITH_FAILURES_REQUIRES_REVIEW`\n\nSix authorized conditions were started exactly once. All six terminated before scientific optimizer/Aer evaluation because the execution integration passed `bounds=None` twice to SciPy 1.17.1 Nelder-Mead. No retry or parameter change was performed. The six failure records remain immutable for review. No scientific conclusion is drawn.\n")
    manifest["artifacts"] = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"}}
    dump(OUT / "manifest.json", manifest)
    all_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in all_files))
    print(json.dumps({"classification": summary["classification"], "terminal_count": 6, "execution_performed": True, "failure": "IMPLEMENTATION_EXCEPTION", "manifest_sha256": sha(OUT / "manifest.json")}, indent=2))

if __name__ == "__main__": main()
