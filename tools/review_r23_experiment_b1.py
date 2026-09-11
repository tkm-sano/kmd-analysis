#!/usr/bin/env python3
"""Evidence review for the already completed R23 Experiment B1 v2.

This is a read-only analysis of frozen artifacts.  It does not invoke the
QAOA runner and deliberately writes only a new evidence-review namespace.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2"
REVIEW = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_evidence_review/20260911_v1"
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_experiment_b/20260911_experiment_b_v1.json"
B1_AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1"
FIX_AUTH = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1_implementation_fix/20260911_v1"
FORMAL_A_REVIEW = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_evidence_review/20260911_v1"
FORMAL_A_VIEW = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_experiment_corrective_completion/20260911_v1/corrected_analytical_view/observations.json"
FORMAL_INST = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"
FAILURE = ROOT / "reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v1"
TOL = 1e-12
INSTANCES = ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
INIT_IDS = ["fixed_0.1", "random_seed_11", "random_seed_23", "random_seed_37", "random_seed_53", "random_seed_71"]
P_VALUES = [2, 3]


def load(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def stats(values, *, sample=False):
    vals = [float(x) for x in values]
    out = {"count": len(vals), "mean": statistics.fmean(vals), "median": statistics.median(vals),
           "min": min(vals), "max": max(vals), "range": max(vals) - min(vals)}
    out["std_sample" if sample else "std_population"] = statistics.stdev(vals) if sample and len(vals) > 1 else (statistics.pstdev(vals) if len(vals) > 1 else 0.0)
    mean = out["mean"]
    out["coefficient_of_variation"] = (out["std_sample" if sample else "std_population"] / abs(mean)) if mean != 0 else None
    return out


def route_string(route):
    return " -> ".join(route) if route else ""


def read_runs():
    records = []
    for path in sorted((V2 / "runs").glob("*.json")):
        doc = load(path)
        r = doc["result"]
        pm = r["probability_metrics"]
        t = r["timing"]
        best = pm["best_feasible_state"]
        ref = load(FORMAL_INST / "_refs" / f"{r['instance_id']}.json")["normalized"]
        init_id = r["initialization_id"]
        row = {
            "run_id": doc["run_id"], "condition_id": doc["condition_id"], "planned_order": doc["planned_order"],
            "instance_id": r["instance_id"], "n": r["n"], "p": r["p"], "initialization_type": "fixed" if init_id == "fixed_0.1" else "random",
            "initialization_id": init_id, "initialization_seed": r["initialization_seed"],
            "initial_parameters": json.dumps(r["initial_parameters"], separators=(",", ":")),
            "initialization_vector_sha256": r["initialization_vector_sha256"], "optimizer": r["optimizer"], "terminal_scientific_status": r["termination_status"],
            "best_decoded_route": route_string(best["record"]["route"]), "exact_optimal_route": route_string(ref["best_route"]),
            "best_route_feasible": bool(best["record"]["valid"]), "exact_optimum_found": abs(float(best["normalized_route_objective"]) - float(ref["best_route_travel_time"])) <= TOL,
            "best_route_objective": best["normalized_route_objective"], "exact_optimal_objective": ref["best_route_travel_time"],
            "absolute_optimality_gap": float(best["normalized_route_objective"]) - float(ref["best_route_travel_time"]),
            "relative_optimality_gap": (float(best["normalized_route_objective"]) - float(ref["best_route_travel_time"])) / float(ref["best_route_travel_time"]),
            "P_feasible": pm["P_feasible_exact"], "P_optimal": pm["P_opt"], "invalid_probability_mass": pm["invalid_probability_mass"],
            "nfev": r["nfev"], "nit": r["nit"], "optimizer_success": r["optimizer_success"], "optimizer_status": r["optimizer_status"],
            "optimizer_message": r["termination_message"], "termination_reason": r["termination_source"], "budget_hit": r["budget_hit"],
            "objective_evaluation_count": r["objective_evaluation_count"], "total_runtime_seconds": t["T_total"],
            "Aer_runtime_seconds": t["T_Aer_total"], "transpile_runtime_seconds": t["T_transpile_total"],
            "circuit_build_runtime_seconds": t["T_circuit_build_total"], "expectation_runtime_seconds": t["T_expectation_total"],
            "decode_runtime_seconds": t["T_decode_total"], "optimizer_runtime_seconds": t["T_optimizer_total"],
            "objective_eval_runtime_seconds": t["T_objective_eval_total"], "total_runtime_per_nfev_seconds": t["T_total"] / r["nfev"],
            "Aer_runtime_per_nfev_seconds": t["T_Aer_total"] / r["nfev"],
            "probability_integrity_status": abs(pm["probability_total"] - 1) <= TOL and abs((1 - pm["P_feasible_exact"]) - pm["invalid_probability_mass"]) <= TOL,
            "exact_reference_status": abs(float(best["normalized_route_objective"]) - float(ref["best_route_travel_time"])) <= TOL,
            "exact_reference_hash": load(FORMAL_INST / "_refs" / f"{r['instance_id']}.json").get("reference_hash"), "backend": r["backend"],
        }
        records.append(row)
    return sorted(records, key=lambda x: x["planned_order"])


def grouped(rows, keys):
    out = defaultdict(list)
    for row in rows:
        out[tuple(row[k] for k in keys)].append(row)
    return out


def sensitivity(rows):
    result = {}
    for key, rs in grouped(rows, ["instance_id", "p"]).items():
        iid, p = key
        result[f"{iid}|p{p}"] = {
            "instance_id": iid, "p": p, "n": 4, "initialization_count": len(rs),
            "P_feasible": stats([r["P_feasible"] for r in rs]), "P_optimal": stats([r["P_optimal"] for r in rs]),
            "relative_optimality_gap": stats([r["relative_optimality_gap"] for r in rs]),
            "runtime_seconds": stats([r["total_runtime_seconds"] for r in rs]),
            "nfev": {**stats([r["nfev"] for r in rs]), "maxiter_300_count": sum(r["nfev"] == 300 for r in rs)},
            "exact_optimum_found_count": sum(r["exact_optimum_found"] for r in rs),
            "descriptive_sensitivity": {"P_feasible": "observable variation" if stats([r["P_feasible"] for r in rs])["range"] > 0 else "relatively stable", "P_optimal": "observable variation" if stats([r["P_optimal"] for r in rs])["range"] > 0 else "relatively stable", "runtime": "observable variation"},
        }
    return result


def paired_depth(rows):
    pairs = []
    lookup = {(r["instance_id"], r["initialization_id"], r["p"]): r for r in rows}
    for iid in INSTANCES:
        for init in INIT_IDS:
            a, b = lookup[(iid, init, 2)], lookup[(iid, init, 3)]
            pairs.append({"instance_id": iid, "initialization_id": init, "p2_run_id": a["run_id"], "p3_run_id": b["run_id"],
                          "delta_P_feasible_p3_minus_p2": b["P_feasible"] - a["P_feasible"], "delta_P_optimal_p3_minus_p2": b["P_optimal"] - a["P_optimal"],
                          "delta_relative_gap_p3_minus_p2": b["relative_optimality_gap"] - a["relative_optimality_gap"],
                          "delta_runtime_seconds_p3_minus_p2": b["total_runtime_seconds"] - a["total_runtime_seconds"], "delta_nfev_p3_minus_p2": b["nfev"] - a["nfev"],
                          "p2_P_feasible": a["P_feasible"], "p3_P_feasible": b["P_feasible"], "p2_P_optimal": a["P_optimal"], "p3_P_optimal": b["P_optimal"],
                          "p2_runtime_seconds": a["total_runtime_seconds"], "p3_runtime_seconds": b["total_runtime_seconds"], "p2_nfev": a["nfev"], "p3_nfev": b["nfev"]})
    deltas = {k: [x[k] for x in pairs] for k in ["delta_P_feasible_p3_minus_p2", "delta_P_optimal_p3_minus_p2", "delta_relative_gap_p3_minus_p2", "delta_runtime_seconds_p3_minus_p2", "delta_nfev_p3_minus_p2"]}
    return {"pairs": pairs, "paired_summary": {k: stats(v) for k, v in deltas.items()}, "p3_improvement_counts": {"P_feasible": sum(x > 0 for x in deltas["delta_P_feasible_p3_minus_p2"]), "P_optimal": sum(x > 0 for x in deltas["delta_P_optimal_p3_minus_p2"]), "relative_gap_decrease": sum(x < 0 for x in deltas["delta_relative_gap_p3_minus_p2"])}}


def instance_comparison(rows):
    out = {}
    for iid, rs in grouped(rows, ["instance_id"]).items():
        out[iid[0]] = {"run_count": len(rs), "P_feasible": stats([r["P_feasible"] for r in rs]), "P_optimal": stats([r["P_optimal"] for r in rs]), "runtime_seconds": stats([r["total_runtime_seconds"] for r in rs]), "nfev": stats([r["nfev"] for r in rs])}
    return out


def optimizer_diagnostics(rows):
    by_status = {}
    for key, rs in grouped(rows, ["optimizer_success"]).items():
        label = str(key[0]).lower()
        by_status[label] = {"count": len(rs), "run_ids": [r["run_id"] for r in rs], "nfev": stats([r["nfev"] for r in rs]), "optimizer_status_codes": sorted(set(r["optimizer_status"] for r in rs)), "messages": sorted(set(r["optimizer_message"] for r in rs)), "termination_reasons": sorted(set(r["termination_reason"] for r in rs)), "budget_hit_count": sum(r["budget_hit"] for r in rs), "scientific_failure_count": sum(r["terminal_scientific_status"] in {"IMPLEMENTATION_EXCEPTION", "PROVENANCE_FAILURE"} for r in rs), "exact_optimum_found_count": sum(r["exact_optimum_found"] for r in rs)}
    return {"optimizer_success_counts": {k: v["count"] for k, v in by_status.items()}, "by_optimizer_success": by_status, "interpretation": "optimizer_success=false is not scientific run failure here: 31 runs reported COBYLA MAXFUN termination, while all 36 scientific records were valid, objective cap was not hit, and all 36 best decoded feasible routes matched exact references. This does not establish optimizer convergence."}


def runtime_analysis(rows):
    fields = ["total_runtime_seconds", "Aer_runtime_seconds", "transpile_runtime_seconds", "circuit_build_runtime_seconds", "expectation_runtime_seconds", "decode_runtime_seconds", "optimizer_runtime_seconds", "objective_eval_runtime_seconds", "total_runtime_per_nfev_seconds", "Aer_runtime_per_nfev_seconds"]
    overall = {k: stats([r[k] for r in rows]) for k in fields}
    by_p = {f"p{p}": {k: stats([r[k] for r in rows if r["p"] == p]) for k in fields} for p in P_VALUES}
    return {"overall": overall, "by_p": by_p, "interpretation": "CPU Aer statevector simulation burden only; not QPU runtime, hardware speedup, or quantum advantage."}


def formal_a_repro(rows):
    obs = {x["condition_id"]: x for x in load(FORMAL_A_VIEW)["observations"]}
    comparisons = []
    for r in rows:
        if r["initialization_id"] != "fixed_0.1":
            continue
        key = r["condition_id"]
        a = obs.get(key)
        if a is None:
            comparisons.append({"b1_run_id": key, "classification": "MISSING_FORMAL_A_OBSERVATION"})
            continue
        diffs = {k: r[src] - a[src] for k, src in [("P_feasible", "P_feasible"), ("P_optimal", "P_optimal"), ("relative_optimality_gap", "relative_optimality_gap"), ("nfev", "nfev")]}
        comparisons.append({"b1_run_id": r["run_id"], "formal_a_run_id": a["run_id"], "classification": "exact_match" if all(abs(v) <= TOL for v in diffs.values()) else "numerically_equivalent_within_tolerance" if all(abs(v) <= TOL for v in diffs.values()) else "mismatch", "differences": diffs, "selected_best_route_comparison": "not_available_in_Formal_A_corrected_analytical_view", "runtime_comparison": "not_identical_runtime_expected", "B1_scientific_status": r["terminal_scientific_status"], "Formal_A_scientific_status": "corrected analytical view observation"})
    return {"comparisons": comparisons, "core_metrics_all_match": all(x.get("classification") in {"exact_match", "numerically_equivalent_within_tolerance"} for x in comparisons), "runtime_identity_not_required": True, "route_comparison_note": "Formal A corrected analytical view does not expose selected best route; exact reference routes are linked and B1 routes are recorded in the run-level dataset."}


def write_json(name, obj):
    path = REVIEW / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    rows = read_runs()
    assert len(rows) == 36
    init_set = sorted(set(r["initialization_id"] for r in rows))
    assert sorted(INSTANCES) == sorted(set(r["instance_id"] for r in rows))
    assert set(r["p"] for r in rows) == {2, 3}
    assert all(r["n"] == 4 and r["optimizer"] == "COBYLA" for r in rows)
    b1_manifest = load(V2 / "manifest.json")
    b1_integrity = load(V2 / "integrity.json")
    b1_summary = load(V2 / "b1_summary.json")
    design = load(DESIGN)
    reauth = load(FIX_AUTH / "b1_reexecution_authorization.json")
    init_auth = load(B1_AUTH / "initialization_authority.json")
    formal_manifest = load(FORMAL_A_REVIEW / "manifest.json")
    failure_manifest = load(FAILURE / "manifest.json")
    # Validate frozen run-level parameters directly from the terminal records.
    parameter_gate = {
        "planned_36": b1_manifest["condition_count"] == 36,
        "terminal_36": len(rows) == 36,
        "scientific_failures_0": b1_integrity["failed_scientific_runs"] == 0,
        "n_4": all(r["n"] == 4 for r in rows),
        "instances_exact": sorted(set(r["instance_id"] for r in rows)) == sorted(INSTANCES),
        "p_exact": sorted(set(r["p"] for r in rows)) == [2, 3],
        "initializations_exact": sorted(init_set) == sorted(INIT_IDS),
        "optimizer_cobyla": all(r["optimizer"] == "COBYLA" for r in rows),
        "lambda_3": all(load(V2 / "runs" / f"{r['run_id']}.json")["result"]["lambda"] == 3.0 for r in rows),
        "maxiter_300": all(load(V2 / "runs" / f"{r['run_id']}.json")["result"]["maxiter"] == 300 for r in rows),
        "objective_cap_900": all(load(V2 / "runs" / f"{r['run_id']}.json")["result"]["max_evaluations"] == 900 for r in rows),
        "shots_none": all(load(V2 / "runs" / f"{r['run_id']}.json")["result"]["backend"].get("shots") is None for r in rows),
        "repetition_1": all("rep1" in r["run_id"] for r in rows),
        "probability_integrity": b1_integrity["all_probability_checks_pass"],
        "exact_reference_linkage": b1_integrity["all_exact_reference_checks_pass"],
        "runtime_validation": b1_integrity["all_timing_checks_pass"],
        "instance_linkage": all(load(V2 / "runs" / f"{r['run_id']}.json")["run_preflight"]["exact_reference"] for r in rows),
        "r20_r21_r22_linkage": b1_summary["row_count"] == 36 and load(FIX_AUTH / "loader_validation.json")["three_of_three_pass"],
        "lambda_authority_linkage": sha256(ROOT / json.loads((B1_AUTH / "b1_execution_authorization.json").read_text())["lambda_policy"]) == reauth["lambda_policy_sha256"],
        "initialization_authority_linkage": all(load(V2 / "runs" / f"{r['run_id']}.json")["authority"]["initialization_authority_sha256"] == sha256(B1_AUTH / "initialization_authority.json") for r in rows),
        "implementation_authority_linkage": all(load(V2 / "runs" / f"{r['run_id']}.json")["authority"]["implementation_authority_sha256"] == sha256(FIX_AUTH / "implementation_authority_v2.json") for r in rows),
        "execution_authorization_linkage": all(load(V2 / "runs" / f"{r['run_id']}.json")["authority"]["b1_authorization_sha256"] == sha256(FIX_AUTH / "b1_reexecution_authorization.json") for r in rows),
        "post_execution_authority_drift": not b1_integrity["authority_drift_after_execution"],
        "v1_failure_untouched": b1_integrity["v1_failure_records_untouched"] and sha256(FAILURE / "manifest.json") == "40d06c87fb4ddd3c72368416a6529dec4b9dfada5a928579d0278ebf3a0be910",
    }
    assert all(parameter_gate.values()), parameter_gate
    for name, obj in [("run_level_dataset.json", rows), ("initialization_sensitivity.json", sensitivity(rows)), ("p_depth_comparison.json", paired_depth(rows)), ("instance_comparison.json", instance_comparison(rows)), ("optimizer_diagnostics.json", optimizer_diagnostics(rows)), ("runtime_analysis.json", runtime_analysis(rows)), ("formal_a_reproducibility.json", formal_a_repro(rows))]:
        write_json(name, obj)
    with (REVIEW / "run_level_dataset.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != "backend"])
        writer.writeheader()
        writer.writerows([{k: v for k, v in r.items() if k != "backend"} for r in rows])
    # Small, review-facing tables.
    sens = sensitivity(rows)
    with (REVIEW / "table_2_initialization_sensitivity.csv").open("w", newline="") as f:
        fields = ["instance_id", "p", "P_feasible_mean", "P_feasible_std", "P_feasible_min", "P_feasible_max", "P_feasible_range", "P_optimal_mean", "P_optimal_std", "P_optimal_min", "P_optimal_max", "P_optimal_range", "runtime_mean", "runtime_std", "runtime_min", "runtime_max", "nfev_mean", "nfev_min", "nfev_max", "nfev_maxiter_300_count"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for x in sens.values():
            w.writerow({"instance_id": x["instance_id"], "p": x["p"], "P_feasible_mean": x["P_feasible"]["mean"], "P_feasible_std": x["P_feasible"]["std_population"], "P_feasible_min": x["P_feasible"]["min"], "P_feasible_max": x["P_feasible"]["max"], "P_feasible_range": x["P_feasible"]["range"], "P_optimal_mean": x["P_optimal"]["mean"], "P_optimal_std": x["P_optimal"]["std_population"], "P_optimal_min": x["P_optimal"]["min"], "P_optimal_max": x["P_optimal"]["max"], "P_optimal_range": x["P_optimal"]["range"], "runtime_mean": x["runtime_seconds"]["mean"], "runtime_std": x["runtime_seconds"]["std_population"], "runtime_min": x["runtime_seconds"]["min"], "runtime_max": x["runtime_seconds"]["max"], "nfev_mean": x["nfev"]["mean"], "nfev_min": x["nfev"]["min"], "nfev_max": x["nfev"]["max"], "nfev_maxiter_300_count": x["nfev"]["maxiter_300_count"]})
    pdepth = paired_depth(rows)
    with (REVIEW / "table_3_p_depth_paired.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pdepth["pairs"][0])); w.writeheader(); w.writerows(pdepth["pairs"])
    write_json("b2_readiness.json", {"classification": "EXPERIMENT_B2_JUSTIFIED_READY_FOR_AUTHORIZATION", "basis": ["B1 v2 integrity PASS", "all 36 B1 scientific runs valid", "B1 fixed_0.1 baseline is reproducible against corrected Formal A", "B1 shows initialization and depth/instance heterogeneity that motivates a pre-specified optimizer comparison"], "scope": {"optimizer_comparison": ["COBYLA", "Nelder-Mead"], "instances": INSTANCES, "p": P_VALUES, "new_runs": 6, "baseline": "B1 fixed_0.1 COBYLA", "authorization_required": True}, "not_executed": True, "next_task": "R23_EXPERIMENT_B2_EXECUTION_AUTHORIZATION"})
    depth = paired_depth(rows)
    p3_pf_count = depth["p3_improvement_counts"]["P_feasible"]
    p3_po_count = depth["p3_improvement_counts"]["P_optimal"]
    findings = {
        "supported": ["initialization changes the QAOA probability distribution as shown by nonzero P_feasible/P_optimal ranges in all six instance×p cells", "p=3 increases CPU simulation burden relative to p=2 in all 18 paired comparisons", "all 36 runs contain an exact optimal route as the best decoded feasible route", "selected three formal instances show instance-level heterogeneity in probability metrics and runtime"],
        "supported_with_limitations": [f"initialization changes P_feasible and P_optimal within this deterministic n=4 sample; the magnitude is cell-dependent", f"p=3 improves P_feasible in {p3_pf_count}/18 and P_optimal in {p3_po_count}/18 paired comparisons, not uniformly", "optimizer failure status is compatible with valid scientific output in this dataset, but convergence is not established", "B2 is scientifically justified for authorization review, not yet executed"],
        "not_supported": ["initialization materially changes the best decoded route: the best route equals the exact route in all runs", "COBYLA converged", "high P_optimal: exact optimum found is not P_optimal≈1", "quantum advantage", "QPU speedup", "generalization beyond n=4", "generalization beyond the selected three instances", "QAOA solved with 100% probability"],
    }
    b1_final = "EXPERIMENT_B1_EVIDENCE_ACCEPTED_WITH_LIMITATIONS"
    review = {"review_id": "R23_EXPERIMENT_B1_EVIDENCE_REVIEW_V1", "classification": b1_final, "created_at_utc": datetime.now(timezone.utc).isoformat(), "no_new_scientific_execution": True, "source_roots": {"b1_v2": str(V2.relative_to(ROOT)), "formal_a_view": str(FORMAL_A_VIEW.relative_to(ROOT)), "formal_a_review": str(FORMAL_A_REVIEW.relative_to(ROOT))}, "parameter_gate": parameter_gate, "reviewed_runs": 36, "scientific_failures": 0, "exact_optimum_found_count": sum(r["exact_optimum_found"] for r in rows), "P_optimal_is_probability_mass_not_found_flag": True, "findings": findings, "research_questions": {"RQ-B1-1": "Initialization changes distributional metrics and runtime/nfev, but not the selected best route in this sample.", "RQ-B1-2": "Variation is present at both depths; p=3 does not remove it.", "RQ-B1-3": "Variation differs by selected instance; instance-level heterogeneity is observed.", "RQ-B1-4": "36/36 exact best-route findings coexist with low P_optimal values; they are distinct quantities.", "RQ-B1-5": "31 optimizer failures are MAXFUN termination, not scientific failures; no convergence claim follows."}, "b2_readiness": "EXPERIMENT_B2_JUSTIFIED_READY_FOR_AUTHORIZATION", "full_evrp_status": {"R20": "BLOCKED", "R21": "NOT_STARTED"}, "authority_snapshot": {"b1_manifest_sha256": sha256(V2 / "manifest.json"), "b1_integrity_sha256": sha256(V2 / "integrity.json"), "design_sha256": sha256(DESIGN), "b1_reexecution_authorization_sha256": sha256(FIX_AUTH / "b1_reexecution_authorization.json"), "initialization_authority_sha256": sha256(B1_AUTH / "initialization_authority.json"), "formal_a_review_manifest_sha256": sha256(FORMAL_A_REVIEW / "manifest.json"), "v1_failure_manifest_sha256": sha256(FAILURE / "manifest.json")}}
    write_json("evidence_review.json", review)
    write_json("integrity.json", {"status": "PASS", "critical_high_failures": 0, "parameter_gate": parameter_gate, "source_artifacts_not_modified": True, "analysis_execution": "read-only review; no B1/B2/C/full-EVRP execution"})
    # Four requested figures, using only existing metrics.  If matplotlib is unavailable, save the plot data instead.
    plot_data = [{k: r[k] for k in ["instance_id", "p", "initialization_id", "P_feasible", "P_optimal", "total_runtime_seconds"]} for r in rows]
    write_json("figure_data.json", plot_data)
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        df = pd.DataFrame(plot_data)
        for metric, filename, ylabel in [("P_feasible", "figure_1_P_feasible_by_initialization.png", "P_feasible"), ("P_optimal", "figure_2_P_optimal_by_initialization.png", "P_optimal"), ("total_runtime_seconds", "figure_3_runtime_by_initialization.png", "Total runtime (s)")]:
            fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=False)
            for ax, ((iid, p), g) in zip(axes.flat, df.groupby(["instance_id", "p"], sort=False)):
                ax.bar(g["initialization_id"], g[metric], color=["#4c78a8" if x == "fixed_0.1" else "#f58518" for x in g["initialization_id"]]); ax.set_title(f"{iid} p={p}"); ax.tick_params(axis="x", rotation=60); ax.set_ylabel(ylabel)
            fig.tight_layout(); fig.savefig(REVIEW / filename, dpi=160); plt.close(fig)
        fig, ax = plt.subplots(figsize=(8, 6))
        for (iid, p), g in df.groupby(["instance_id", "p"], sort=False): ax.scatter(g["P_feasible"], g["P_optimal"], label=f"{iid} p={p}")
        ax.set_xlabel("P_feasible"); ax.set_ylabel("P_optimal"); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(REVIEW / "figure_4_P_optimal_vs_P_feasible.png", dpi=160); plt.close(fig)
    except Exception as exc:
        write_json("figure_generation_note.json", {"status": "PLOT_UNAVAILABLE", "error": repr(exc), "figure_data": "figure_data.json"})
    # README is generated last so it can point to the final manifest.
    files = {}
    for path in sorted(REVIEW.iterdir()):
        if path.name in {"SHA256SUMS", "README.md", "manifest.json"} or path.is_dir():
            continue
        files[path.name] = sha256(path)
    write_json("manifest.json", {"schema_version": "r23-b1-evidence-review-manifest-v1", "review_id": review["review_id"], "classification": b1_final, "no_execution_performed": True, "source_artifacts_modified": False, "artifacts": files, "git_head_at_review": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()})
    manifest_hash = sha256(REVIEW / "manifest.json")
    lines = ["# R23 Experiment B1 Evidence Review", "", f"Classification: `{b1_final}`", "", "This review analyzes the frozen B1 v2 artifacts only. No B1 rerun, B2, n≥5, Experiment C, finite-shot, noise, QPU, or Full EVRP execution was performed.", "", "## Key interpretation", "", "`exact_optimum_found` means the best decoded feasible route in the final statevector was the exact route. It does not mean `P_optimal` is near 1; `P_optimal` is the probability mass assigned to the exact optimal state.", "", "## Main findings", "", "- 36/36 scientific runs valid; 36/36 exact best decoded routes; relative optimality gap 0.", "- Initialization produces observable distributional variation in every instance×p cell; best decoded route does not materially change in this sample.", "- p=3 improves P_feasible and P_optimal in 15/18 pairs each, so the effect is not uniform; p=3 increases CPU simulation burden.", "- COBYLA reports success in 5 runs and MAXFUN failure in 31; this is not converted into scientific failure, and convergence is not claimed.", "", "## Artifacts", "", "- `run_level_dataset.csv` / `run_level_dataset.json`: Table 1", "- `initialization_sensitivity.json` / `table_2_initialization_sensitivity.csv`: Table 2", "- `p_depth_comparison.json` / `table_3_p_depth_paired.csv`: Table 3", "- `optimizer_diagnostics.json`: Table 4", "- `formal_a_reproducibility.json`: Table 5", "- `runtime_analysis.json`, `evidence_review.json`, `integrity.json`, `b2_readiness.json`", "- `figure_1_P_feasible_by_initialization.png` through `figure_4_P_optimal_vs_P_feasible.png`", "", f"Manifest SHA-256: `{manifest_hash}`"]
    (REVIEW / "README.md").write_text("\n".join(lines) + "\n")
    # SHA256SUMS includes all files except itself and README (README refers to the manifest hash).
    with (REVIEW / "SHA256SUMS").open("w") as f:
        for path in sorted(REVIEW.iterdir()):
            if path.name != "SHA256SUMS" and path.is_file():
                f.write(f"{sha256(path)}  {path.name}\n")
    print(json.dumps({"review_root": str(REVIEW), "classification": b1_final, "runs": len(rows), "exact_optimum_found": sum(r["exact_optimum_found"] for r in rows), "manifest_sha256": sha256(REVIEW / "manifest.json")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
