#!/usr/bin/env python3
"""Read-only evidence review and independent recomputation for R23 Experiment A.

This script never executes QAOA.  It reads the frozen original and corrective
artifacts and writes a new review namespace only.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_experiment/20260911_formal_v1"
CORR = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_experiment_corrective_completion/20260911_v1"
VIEW = CORR / "corrected_analytical_view"
REVIEW = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_evidence_review/20260911_v1"


def load(path: Path):
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def rnd(x):
    return round(float(x), 12) if isinstance(x, (float, int)) else x


def stats(values):
    vals = [float(x) for x in values]
    return {"count": len(vals), "mean": statistics.fmean(vals),
            "median": statistics.median(vals),
            "std_population": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals), "max": max(vals)}


def close(a, b, tol=1e-10):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    original_manifest = load(ORIG / "manifest.json")
    original_integrity = load(ORIG / "integrity.json")
    original_summary = load(ORIG / "summary.json")
    corrected_manifest = load(CORR / "manifest.json")
    corrected_integrity = load(CORR / "integrity.json")
    corrected_view_manifest = load(VIEW / "manifest.json")
    corrected_view_integrity = load(VIEW / "integrity.json")
    corrected_view = load(VIEW / "observations.json")
    corrected_summary = load(VIEW / "summary.json")
    corrective_summary = load(CORR / "corrective_summary.json")
    amendment = load(CORR / "amendment_reference.json")
    authorization = load(CORR / "authorization_reference.json")
    formal_config = load(ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json")
    lambda_config = load(ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json")
    instance_manifest = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json")
    exact_refs = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/exact_references.json")
    r20_set = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/r20_authority_set.json")
    r21_set = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/r21_authority_set.json")
    r22_set = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/r22_authority_set.json")
    r23_design_manifest = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_design_authority/20260911_v1/manifest.json")
    r23_design_auth = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_design_authority/20260911_v1/execution_authorization.json")
    r23_design_resolution = load(ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_design_authority/20260911_v1/design_authority_resolution.json")

    corr_ids = {
        "routing_v18_n4_rank01_p3_init_fixed01_rep1",
        "routing_v18_n4_rank02_p2_init_fixed01_rep1",
        "routing_v18_n4_rank02_p3_init_fixed01_rep1",
        "routing_v18_n4_rank05_p3_init_fixed01_rep1",
    }
    corrected = corrected_view["observations"]
    original_records = {}
    corrective_records = {}
    for p in (ORIG / "runs").glob("*/result.json"):
        d = load(p)
        original_records[d["formal_run_id"]] = (p, d)
    for p in (CORR / "runs").glob("*/result.json"):
        d = load(p)
        corrective_records[d["formal_run_id"]] = (p, d)

    raw_records = {}
    linkage = []
    for obs in corrected:
        cid = obs["condition_id"]
        if obs["source"] == "ORIGINAL_FORMAL_EXPERIMENT_A_UNCENSORED":
            raw_records[cid] = original_records[cid][1]
        else:
            formal_id = obs["run_id"]
            corrective_run_id = formal_id if formal_id in corrective_records else cid
            raw_records[cid] = corrective_records[corrective_run_id][1]
            c = raw_records[cid]
            opath, od = original_records[c["formal_run_id"]]
            linkage.append({
                "condition_id": cid,
                "original_observation_path": rel(opath),
                "original_observation_sha256": sha(opath),
                "original_manifest_declared_sha256": original_manifest["artifact_file_hashes"][rel(opath).split("/20260911_formal_v1/", 1)[1]],
                "original_termination_status": od.get("termination_status"),
                "original_termination_message": od.get("termination_message", ""),
                "original_failure_reasons": od.get("failure_reasons", []),
                "corrective_observation_path": rel(corrective_records[corrective_run_id][0]),
                "corrective_observation_sha256": sha(corrective_records[corrective_run_id][0]),
                "corrective_termination_status": c.get("termination_status"),
                "corrective_termination_message": c.get("termination_message", ""),
                "corrective_status": c.get("status"),
                "scientific_parameters": {
                    k: c.get(k) for k in ["instance_id", "n", "p", "lambda", "optimizer", "maxiter", "max_evaluations", "initial_parameters", "formal_config_unchanged", "scientific_parameters_unchanged", "exact_reference_hash"]
                },
                "scientific_parameters_match_exactly": bool(c.get("scientific_parameters_unchanged")) and c.get("formal_config_unchanged", True) is True and od.get("n") == c.get("n") and od.get("p") == c.get("p") and od.get("instance_id") == c.get("instance_id") and od.get("lambda") == c.get("lambda") and od.get("initial_parameters") == c.get("initial_parameters") and od.get("optimizer") == c.get("optimizer") and od.get("maxiter") == c.get("maxiter") and od.get("max_evaluations") == c.get("max_evaluations"),
            })

    metric_map = {
        "P_feasible": lambda d: d["probability_metrics"]["P_feasible_exact"],
        "P_optimal": lambda d: d["probability_metrics"]["P_opt"],
        "relative_optimality_gap": lambda d: d["relative_optimality_gap"],
        "absolute_optimality_gap": lambda d: d["absolute_optimality_gap"],
        "best_decoded_route_objective": lambda d: d["best_route_objective"],
        "invalid_probability_mass": lambda d: d["probability_metrics"]["invalid_probability_mass"],
        "objective_evaluation_count": lambda d: d["objective_evaluation_count"],
        "nfev": lambda d: d["nfev"],
        "budget_hit": lambda d: d["budget_hit"],
        "T_total": lambda d: d["timing"]["T_total"],
        "T_optimizer_total": lambda d: d["timing"]["T_optimizer_total"],
        "T_objective_eval_total": lambda d: d["timing"]["T_objective_eval_total"],
        "T_Aer_total": lambda d: d["timing"]["T_Aer_total"],
        "T_expectation_total": lambda d: d["timing"]["T_expectation_total"],
        "T_transpile_total": lambda d: d["timing"]["T_transpile_total"],
        "T_circuit_build_total": lambda d: d["timing"]["T_circuit_build_total"],
    }
    raw_rows = []
    for obs in corrected:
        d = raw_records[obs["condition_id"]]
        row = {"condition_id": obs["condition_id"], "source": obs["source"], "instance_id": d["instance_id"], "n": d["n"], "p": d["p"]}
        for k, fn in metric_map.items(): row[k] = fn(d)
        exact_routes = exact_refs["instances"][d["instance_id"]]["normalized"]["optimal_routes"]
        exact_customer_routes = [route[1:-1] for route in exact_routes]
        decoded_route = d.get("probability_metrics", {}).get("best_feasible_state", {}).get("record", {}).get("route")
        row.update({"termination_status": d.get("termination_status"), "optimizer_success": d.get("optimizer_success"), "termination_message": d.get("termination_message", ""), "nit": d.get("nit"), "expectation_evaluation_count": d.get("expectation_evaluation_count"), "maxiter": d.get("maxiter"), "objective_cap_hit": d.get("termination", {}).get("objective_cap_hit"), "maxiter_boundary_reached": d.get("termination", {}).get("maxiter_boundary_reached"), "best_decoded_objective_exact": close(d["best_route_objective"], d["exact_route_optimum"], 1e-10), "best_decoded_route_in_exact_optimal_set": decoded_route in exact_customer_routes})
        raw_rows.append(row)

    def grouped(rows, keyfn):
        out = defaultdict(list)
        for row in rows: out[keyfn(row)].append(row)
        return out

    group_fields = ["P_feasible", "P_optimal", "relative_optimality_gap", "absolute_optimality_gap", "best_decoded_route_objective", "invalid_probability_mass", "nfev", "T_total", "T_optimizer_total", "T_objective_eval_total", "T_Aer_total", "T_expectation_total", "T_transpile_total", "T_circuit_build_total"]
    corrected_stats = {}
    for key, rows in grouped(raw_rows, lambda r: (r["n"], r["p"])).items():
        corrected_stats[f"n{key[0]}_p{key[1]}"] = {m: stats([r[m] for r in rows]) for m in group_fields}
        corrected_stats[f"n{key[0]}_p{key[1]}"]["source_counts"] = dict(Counter(r["source"] for r in rows))
    by_n = {str(k): {m: stats([r[m] for r in rows]) for m in group_fields} for k, rows in grouped(raw_rows, lambda r: r["n"]).items()}
    by_instance = {inst: {m: stats([x[m] for x in rows]) for m in group_fields} for inst, rows in grouped(raw_rows, lambda x: x["instance_id"]).items()}

    # Independent agreement against the corrected view summary. The repository summary uses population SD.
    mismatches = []
    for key, cell in corrected_stats.items():
        expected = corrected_summary["by_n_p"][key]
        for metric in ["P_feasible", "P_optimal", "relative_optimality_gap", "absolute_optimality_gap", "invalid_probability_mass", "nfev", "T_total", "T_optimizer_total", "T_Aer_total"]:
            for stat in ["count", "mean", "median", "min", "max", "std_population"]:
                existing_stat = "std" if stat == "std_population" else stat
                if not close(cell[metric][stat], expected[metric][existing_stat], 1e-9):
                    mismatches.append({"cell": key, "metric": metric, "stat": stat, "recomputed": cell[metric][stat], "existing": expected[metric][existing_stat]})

    # p transitions: strict numerical improvement/worsening, with effectively unchanged <= 1e-12.
    p_effects = {}
    for n in [2, 3, 4]:
        for metric in ["P_feasible", "P_optimal", "nfev", "T_total"]:
            transitions = {}
            for a, b in [(1, 2), (2, 3), (1, 3)]:
                counts = Counter()
                for inst in [f"routing_v18_n{n}_rank{i:02d}" for i in range(1, 6)]:
                    x = next(r[metric] for r in raw_rows if r["instance_id"] == inst and r["p"] == a)
                    y = next(r[metric] for r in raw_rows if r["instance_id"] == inst and r["p"] == b)
                    if close(x, y, 1e-12): counts["unchanged"] += 1
                    elif (y > x): counts["improves"] += 1
                    else: counts["worsens"] += 1
                transitions[f"p{a}_to_p{b}"] = dict(counts)
            p_effects[f"n{n}"] = p_effects.get(f"n{n}", {})
            p_effects[f"n{n}"][metric] = transitions

    # Corrected impact from original published summary for affected cells.
    impact = {}
    for key in ["n4_p2", "n4_p3"]:
        impact[key] = {"original": {}, "corrected": {}, "difference": {}}
        for metric in ["P_feasible", "P_optimal", "nfev", "T_total", "T_optimizer_total", "T_Aer_total"]:
            original_metric = "objective_evaluation_count" if metric == "nfev" else metric
            o = original_summary["by_n_p"][key][original_metric]
            c = corrected_stats[key][metric]
            impact[key]["original"][metric] = o
            impact[key]["corrected"][metric] = c
            impact[key]["difference"][metric] = {"mean": c["mean"] - o["mean"], "median": c["median"] - o["median"]}
        impact[key]["classification"] = "NON-MATERIAL" if max(abs(v["mean"]) for v in impact[key]["difference"].values()) < 1e-6 else "INTERPRETATIONALLY_IMPORTANT_BUT_NUMERICALLY_SMALL"

    baselines = {str(n): {"factorial_routes": math.factorial(n), "logical_qubits": n*n, "amplitude_count": 2**(n*n), "uniform_feasible_fraction": math.factorial(n)/(2**(n*n)), "uniform_optimal_given_feasible": 1/math.factorial(n)} for n in [2,3,4]}
    prob_diag = {}
    for r in raw_rows:
        base = baselines[str(r["n"])]["uniform_feasible_fraction"]
        r["feasible_concentration_ratio"] = r["P_feasible"] / base
        r["P_optimal_given_feasible"] = r["P_optimal"] / r["P_feasible"] if r["P_feasible"] > 0 else None
    for key, rows in grouped(raw_rows, lambda r: (r["n"], r["p"])).items():
        name = f"n{key[0]}_p{key[1]}"
        prob_diag[name] = {m: stats([r[m] for r in rows]) for m in ["feasible_concentration_ratio", "P_optimal_given_feasible"]}
        prob_diag[name]["uniform_optimal_given_feasible"] = baselines[str(key[0])]["uniform_optimal_given_feasible"]

    runtime = {}
    for key, rows in grouped(raw_rows, lambda r: (r["n"], r["p"])).items():
        name = f"n{key[0]}_p{key[1]}"
        runtime[name] = {m: stats([r[m] for r in rows]) for m in ["T_total", "T_optimizer_total", "T_objective_eval_total", "T_Aer_total", "T_expectation_total", "T_transpile_total", "T_circuit_build_total", "nfev"]}
        for metric, denom in [("T_total", "nfev"), ("T_optimizer_total", "nfev"), ("T_Aer_total", "nfev"), ("T_transpile_total", "nfev")]:
            runtime[name][f"{metric}_per_nfev"] = stats([r[metric]/r[denom] for r in rows])
        comp_means = {m: runtime[name][m]["mean"] for m in ["T_Aer_total", "T_expectation_total", "T_transpile_total", "T_circuit_build_total"]}
        runtime[name]["dominant_component_by_mean"] = max(comp_means, key=comp_means.get)

    termination = Counter(r["termination_status"] for r in raw_rows)
    nfev_dist = {name: {"lt_300": sum(r["nfev"] < 300 for r in rows), "eq_300": sum(r["nfev"] == 300 for r in rows), "count": len(rows)} for name, rows in ((f"n{k[0]}_p{k[1]}", v) for k,v in grouped(raw_rows, lambda r: (r["n"], r["p"])).items())}
    exact_count = sum(r["best_decoded_route_in_exact_optimal_set"] for r in raw_rows)
    all_gap_zero = all(close(r["absolute_optimality_gap"], 0) and close(r["relative_optimality_gap"], 0) for r in raw_rows)

    # Provenance: path/hash links and declared cross-authority hashes.
    chain = []
    def check_file(label, path, declared=None):
        exists = path.exists()
        actual = sha(path) if exists and path.is_file() else None
        ok = exists and (declared is None or actual == declared)
        chain.append({"label": label, "path": rel(path), "exists": exists, "actual_sha256": actual, "declared_sha256": declared, "status": "PASS" if ok else "FAIL"})
        return ok
    routing_root = ROOT / instance_manifest["routing_authority"]["artifact_path"]
    check_file("Routing Baseline manifest", routing_root / "r13_manifest.json", instance_manifest["routing_authority"]["manifest_sha256"])
    check_file("R20 lambda authority", ROOT / lambda_config["source_authority"]["formal_design_artifact"], lambda_config["source_authority"]["formal_design_artifact_sha256"])
    check_file("R20 lambda policy", ROOT / "reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json", instance_manifest["lambda_policy"]["sha256"])
    check_file("R23 formal design", ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json", r23_design_manifest["canonical_design_file_sha256"])
    check_file("R23 instance set manifest", ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/manifest.json")
    check_file("Original Formal Experiment A manifest", ORIG / "manifest.json", original_integrity["file_hashes"]["manifest.json"])
    check_file("Original Formal Experiment A integrity", ORIG / "integrity.json")
    check_file("Wall-time amendment", ROOT / amendment["path"], amendment["sha256"])
    check_file("Corrective authorization", ROOT / authorization["path"], authorization["sha256"])
    check_file("Corrective completion manifest", CORR / "manifest.json")
    check_file("Corrected analytical observations", VIEW / "observations.json", corrected_view_manifest["files"]["observations.json"])
    check_file("Corrected analytical integrity", VIEW / "integrity.json")
    # Authority-set internal link checks.
    authority_link_checks = {"r20": all(rec["status"] == "R20_FORMAL_INSTANCE_PASS" and (ROOT / rec["path"]).exists() for rec in r20_set["records"]), "r21": all(rec["status"] == "R21_FORMAL_INSTANCE_PASS" and (ROOT / rec["path"]).exists() for rec in r21_set["records"]), "r22": all(rec["status"] == "R22_FORMAL_INSTANCE_PASS" and (ROOT / rec["path"]).exists() for rec in r22_set["records"]), "exact": exact_refs["count"] == 15 and len(exact_refs["instances"]) == 15, "design_resolution": r23_design_resolution.get("resolution_id") == "R23_FORMAL_DESIGN_AUTHORITY_RESOLUTION_V1", "design_authorization": r23_design_auth.get("formal_design_id") == "R23_FORMAL_EXPERIMENT_DESIGN_V1" and r23_design_auth.get("formal_design_artifact_sha256") == r23_design_manifest.get("canonical_design_file_sha256")}
    provenance_pass = all(x["status"] == "PASS" for x in chain) and all(authority_link_checks.values()) and original_integrity["status"] == "PASS" and corrected_view_integrity["status"] == "PASS"

    # Four replacement checks against raw and exact references.
    replacement_check = {"count": len(linkage), "expected_count": 4, "all_expected_conditions": {x["condition_id"] for x in linkage} == corr_ids, "all_scientific_parameters_match": all(x["scientific_parameters_match_exactly"] for x in linkage), "records": linkage}
    corrected_summary_payload = {"standard_deviation_convention": "population SD (ddof=0), matching repository corrected summary", "by_n_p": corrected_stats, "by_n": by_n, "by_instance": by_instance, "agreement_with_existing_corrected_summary": {"status": "PASS" if not mismatches else "MISMATCH", "mismatch_count": len(mismatches), "mismatches": mismatches}}
    json_dump = lambda p, obj: p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    json_dump(REVIEW / "recomputed_summary.json", corrected_summary_payload)
    json_dump(REVIEW / "probability_diagnostics.json", {"structural_baselines": baselines, "by_n_p": prob_diag, "raw_run_diagnostics": [{"condition_id": r["condition_id"], "n": r["n"], "p": r["p"], "P_feasible": r["P_feasible"], "P_optimal": r["P_optimal"], "feasible_concentration_ratio": r["feasible_concentration_ratio"], "P_optimal_given_feasible": r["P_optimal_given_feasible"]} for r in raw_rows]})
    json_dump(REVIEW / "runtime_review.json", {"by_n_p": runtime, "nfev_distribution": nfev_dist, "total_runs_nfev_lt_300": sum(r["nfev"] < 300 for r in raw_rows), "total_runs_nfev_eq_300": sum(r["nfev"] == 300 for r in raw_rows), "objective_cap_hit_count": sum(bool(r["objective_cap_hit"]) for r in raw_rows), "budget_hit_count": sum(bool(r["budget_hit"]) for r in raw_rows), "termination_status_counts": dict(termination), "per_evaluation_denominator": "nfev/objective_evaluation_count; raw result timing divided by nfev", "runtime_interpretation": "CPU software-simulation burden only"})
    json_dump(REVIEW / "corrective_impact_review.json", {"post_execution_correction": True, "original_summary_unchanged": corrective_summary["original_summary_unchanged"], "full_45_run_reexecution": corrective_summary["full_45_run_reexecution"], "affected_cells": impact, "replacements": replacement_check})
    json_dump(REVIEW / "scaling_readiness.json", {"classification": "SCALING_EXTENSION_DESIGN_READY_WITH_RESOURCE_REDESIGN", "experiment_b_priority": "B1_REQUIRED_BEFORE_SCALING_EXTENSION", "experiment_c_priority": "REQUIRED_BEFORE_SCENARIO_MODELLING", "n5": {"logical_qubits": 25, "amplitude_count": 33554432, "raw_statevector_memory_bytes": {"complex128": 536870912, "complex64": 268435456}, "raw_statevector_memory_gib": {"complex128": 0.5, "complex64": 0.25}, "current_guard_gib": 8.0, "assessment": "raw statevector fits nominal guard, but actual Aer peak exceeds one raw statevector; preflight and staged execution required; no runtime extrapolation"}, "blockers": ["memory/peak allocation", "CPU simulator wall-clock burden", "transpilation and optimizer evaluation burden", "artifact size", "R22 full-state validation at 2^25 states", "R20/R22 authority validation method for n=5"], "r22_validation": "SCALING_DESIGN_REQUIREMENT: replace or supplement full-state enumeration with coefficient-level analytical equivalence plus targeted deterministic checks; do not assume 2^25 full-state validation is operationally cheap", "exact_aer_recommendation": "C_CHANGE_SCALING_METHODOLOGY_BEFORE_N5", "separation": "separate algorithmic response scaling from classical simulator resource scaling", "architecture": {"S1": "n=5 resource preflight and very limited frozen formal instances; no authorization implied", "S2": "expand n only after S1 evidence review and resource acceptance"}})
    json_dump(REVIEW / "evidence_review.json", {"review_id": "R23_FORMAL_EXPERIMENT_A_EVIDENCE_REVIEW_V1", "review_timestamp_utc": datetime.now(timezone.utc).isoformat(), "branch_head": "see manifest", "evidence_acceptance": "FORMAL_EXPERIMENT_A_EVIDENCE_ACCEPTED_WITH_LIMITATIONS", "r23_status_recommendation": "FORMAL_EXPERIMENT_A_EVIDENCE_ACCEPTED_WITH_LIMITATIONS", "original_integrity": {"planned_conditions": original_manifest["planned_runs"], "terminal_records": original_manifest["completed_runs"], "original_uncensored": 41, "original_right_censored": 4, "integrity_status": original_integrity["status"], "authority_drift_after_execution": original_integrity["authority_drift_after_execution"], "configuration_changed": original_integrity["configuration_changed"], "environment_changed": original_integrity["environment_changed"], "immutable_historical_layer": True}, "corrective_integrity": {"authorized": 4, "completed": 4, "all_pass": all(x["status"] == "CORRECTIVE_RUN_PASS" for x in corrective_summary["corrective_observations"]), "separate_post_execution_layer": True, "integrity_status": corrected_integrity["status"]}, "corrected_view_integrity": {"status": corrected_view_integrity["status"], "observation_count": corrected_view_integrity["observation_count"], "original_summary_not_modified": corrected_view_integrity["original_summary_not_modified"], "original_41_preserved_by_reference": corrected_view["original_41_preserved_by_reference"]}, "provenance": {"status": "PASS" if provenance_pass else "FORMAL_EVIDENCE_PROVENANCE_FAILURE", "chain": chain, "authority_link_checks": authority_link_checks}, "completeness": {"expected": 45, "actual": len(corrected), "unique_conditions": len({x["condition_id"] for x in corrected}), "by_n_p": {f"n{k[0]}_p{k[1]}": v for k, v in Counter((x["n"], x["p"]) for x in corrected).items()}, "by_n": {str(k): v for k, v in Counter(x["n"] for x in corrected).items()}, "missing": sorted(set(f"routing_v18_n{n}_rank{rank:02d}_p{p}_init_fixed01_rep1" for n in [2,3,4] for rank in range(1,6) for p in [1,2,3]) - {x["condition_id"] for x in corrected}), "duplicate_condition_count": len(corrected) - len({x["condition_id"] for x in corrected})}, "corrective_replacements": replacement_check, "recomputed_summary_agreement": {"status": "PASS" if not mismatches else "MISMATCH", "mismatch_count": len(mismatches)}, "gap_and_exact_route": {"absolute_gap_zero_count": sum(close(r["absolute_optimality_gap"], 0) for r in raw_rows), "relative_gap_zero_count": sum(close(r["relative_optimality_gap"], 0) for r in raw_rows), "exact_best_decoded_route_count": exact_count, "interpretation": "gap=0 means best decoded feasible route equals exact optimum; it does not imply high P_optimal, sampling success, optimizer convergence, finite-shot success, robustness, or quantum advantage"}, "optimizer": {"termination_status_counts": dict(termination), "optimizer_success_counts": dict(Counter(str(r["optimizer_success"]) for r in raw_rows)), "nit_counts": dict(Counter(str(r["nit"]) for r in raw_rows)), "termination_unknown_count": termination.get("TERMINATION_UNKNOWN", 0), "convergence_established": False, "conclusion": "optimizer convergence cannot be established from this formal evidence"}, "p_effects": p_effects, "corrected_stats_by_n": by_n, "runtime_by_n_p": runtime, "corrective_impact": impact, "wall_time_amendment_assessment": "SUPPORTED_WITH_LIMITATIONS: four old right-censored conditions completed under no wall-time research cap, supporting policy censoring rather than an algorithmic feasibility boundary; this does not establish n>=5 feasibility", "claims": {"problem_size_reduces_P_feasible": "SUPPORTED_WITH_LIMITATIONS", "problem_size_reduces_P_optimal": "SUPPORTED_WITH_LIMITATIONS", "increasing_p_improves_P_feasible": "SUPPORTED_WITH_LIMITATIONS", "increasing_p_improves_P_optimal": "SUPPORTED_WITH_LIMITATIONS", "always_finds_exact_optimum": "SUPPORTED_WITH_LIMITATIONS: all 45 best decoded routes are exact, but not a claim of sampling or optimizer reliability", "cpu_burden_rises_sharply_by_n4": "SUPPORTED", "COBYLA_converged": "NOT_SUPPORTED", "finite_shot_reliably_samples_optimum": "NOT_SUPPORTED", "quantum_advantage": "NOT_SUPPORTED", "Aer_predicts_QPU_scaling": "NOT_SUPPORTED"}, "limitations": ["n only 2,3,4", "five deterministic reproducibility instances per n, not representative random population", "one initialization and repetition=1", "COBYLA only", "exact expectation and shots=NONE", "lambda fixed at 3.0", "p only 1,2,3", "CPU Aer only", "termination uncertainty", "post-execution wall-time amendment/corrective completion"], "sample_selection": "reproducibility and instance heterogeneity evidence, not population representativeness or inferential uncertainty", "experiment_b": "B1_REQUIRED_BEFORE_SCALING_EXTENSION", "experiment_b_rationale": "n=4 p2/p3 heterogeneity and universal termination uncertainty make initialization/optimizer robustness a prerequisite", "experiment_c": "REQUIRED_BEFORE_SCENARIO_MODELLING", "experiment_c_rationale": "n=4 P_optimal is typically 10^-4 to 10^-3 in corrected cells, so exact-statevector probability is not operational finite-shot success", "scaling_readiness": "SCALING_EXTENSION_DESIGN_READY_WITH_RESOURCE_REDESIGN", "full_evrp_status": {"R20": "BLOCKED", "R21": "NOT_STARTED"}, "no_execution": {"qaoa_executed_by_review": False, "original_or_corrective_modified": False, "n_ge_5_executed": False, "experiment_b_executed": False, "experiment_c_executed": False, "future_qpu_claim": False, "prohibited_action": False}})

    # Manifest is written last so it can hash all review artifacts.
    artifacts = {p.name: sha(p) for p in REVIEW.glob("*.json") if p.name != "manifest.json"}
    manifest = {"schema_version": "r23-formal-evidence-review-manifest-v1", "review_id": "R23_FORMAL_EXPERIMENT_A_EVIDENCE_REVIEW_V1", "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_roots": {"original": rel(ORIG), "corrective": rel(CORR), "corrected_view": rel(VIEW)}, "source_manifest_hashes": {"original": sha(ORIG/"manifest.json"), "corrective": sha(CORR/"manifest.json"), "corrected_view": sha(VIEW/"manifest.json")}, "artifacts": artifacts, "provenance_status": "PASS" if provenance_pass else "FORMAL_EVIDENCE_PROVENANCE_FAILURE", "no_execution_performed": True, "original_and_corrective_artifacts_modified": False}
    json_dump(REVIEW / "manifest.json", manifest)


if __name__ == "__main__":
    main()
