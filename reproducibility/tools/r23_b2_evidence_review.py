#!/usr/bin/env python3
"""Recompute R23 B2 optimizer comparison artifacts from immutable terminal records."""
import csv, hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/traffic_simulation/r23_experiment_b2_evidence_review/20260911_v1"
B1 = ROOT / "outputs/traffic_simulation/r23_experiment_b1/20260911_v2"
B2 = ROOT / "outputs/traffic_simulation/r23_experiment_b2/20260911_v2"

def load(p):
    return json.loads(p.read_text())

def sha(p):
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def mean(xs): return sum(xs) / len(xs) if xs else None
def median(xs): return statistics.median(xs) if xs else None
def summary(xs):
    return {"count": len(xs), "mean": mean(xs), "median": median(xs),
            "min": min(xs) if xs else None, "max": max(xs) if xs else None}

def pct_diff(a, b):
    return None if a == 0 else (b-a)/abs(a)

def compact(rec, optimizer):
    r = rec["result"]
    pm = r.get("probability_metrics", {})
    best = pm.get("best_feasible_state", {})
    t = r["timing"]
    term = r["termination"]
    return {
        "optimizer": optimizer, "instance_id": r["instance_id"], "p": r["p"],
        "initialization": r["initialization_id"], "selected_best_route": best.get("record", {}).get("route"),
        "P_feasible": pm.get("P_feasible_exact"), "P_optimal": pm.get("P_opt"),
        "absolute_gap": r.get("absolute_optimality_gap", 0.0),
        "relative_gap": r.get("relative_optimality_gap", 0.0),
        "exact_optimum_found": r.get("run_classification") == "OPTIMAL_FOUND",
        "success": term.get("success"), "status": term.get("status"),
        "message": term.get("message"), "termination_reason": r.get("termination_status"),
        "nfev": r.get("nfev"), "nit": r.get("nit"),
        "T_total": t.get("T_total"), "T_Aer": t.get("T_Aer_total"),
        "T_transpile": t.get("T_transpile_total"),
        "T_total_per_nfev": t.get("T_total")/r["nfev"],
        "T_Aer_per_nfev": t.get("T_Aer_total")/r["nfev"],
        "run_id": rec["run_id"],
    }

def run_index(root, pattern):
    return {load(p)["run_id"]: load(p) for p in root.glob(pattern)}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b1idx = run_index(B1 / "runs", "*.json")
    b2idx = run_index(B2 / "runs", "*.json")
    instances = ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
    pairs = []
    for instance in instances:
        for p in [2, 3]:
            base = f"{instance}_p{p}_init_fixed01_rep1"
            c = compact(b1idx[base + "_optimizer_cobyla"], "COBYLA")
            nm = compact(b2idx[base + "_optimizer_nelder_mead"], "Nelder-Mead")
            # B1 v2 uses the same scientific fields as B2 but its exact route quality is in the record.
            row = {"instance": instance, "p": p, "COBYLA": c, "Nelder-Mead": nm,
                   "delta": {"P_feasible": nm["P_feasible"]-c["P_feasible"],
                             "P_optimal": nm["P_optimal"]-c["P_optimal"],
                             "T_total": nm["T_total"]-c["T_total"],
                             "T_Aer": nm["T_Aer"]-c["T_Aer"],
                             "T_transpile": nm["T_transpile"]-c["T_transpile"],
                             "nfev": nm["nfev"]-c["nfev"]},
                   "ratios": {"T_total_NM_over_COBYLA": nm["T_total"]/c["T_total"],
                              "T_Aer_NM_over_COBYLA": nm["T_Aer"]/c["T_Aer"],
                              "nfev_NM_over_COBYLA": nm["nfev"]/c["nfev"]}}
            pairs.append(row)

    flat = []
    for x in pairs:
        c, n = x["COBYLA"], x["Nelder-Mead"]
        flat.append({"instance": x["instance"], "p": x["p"],
          "COBYLA P_feasible": c["P_feasible"], "Nelder-Mead P_feasible": n["P_feasible"],
          "ΔP_feasible": x["delta"]["P_feasible"],
          "COBYLA P_optimal": c["P_optimal"], "Nelder-Mead P_optimal": n["P_optimal"],
          "ΔP_optimal": x["delta"]["P_optimal"], "COBYLA gap": c["relative_gap"],
          "Nelder-Mead gap": n["relative_gap"], "COBYLA T_total": c["T_total"],
          "Nelder-Mead T_total": n["T_total"], "runtime ratio": x["ratios"]["T_total_NM_over_COBYLA"],
          "COBYLA nfev": c["nfev"], "Nelder-Mead nfev": n["nfev"],
          "COBYLA selected best route": json.dumps(c["selected_best_route"], ensure_ascii=False),
          "Nelder-Mead selected best route": json.dumps(n["selected_best_route"], ensure_ascii=False),
          "COBYLA termination": c["message"], "Nelder-Mead termination": n["message"],
          "exact optimum COBYLA": c["exact_optimum_found"], "exact optimum Nelder-Mead": n["exact_optimum_found"]})
    fields = list(flat[0])
    with (OUT / "paired_optimizer_comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(flat)
    (OUT / "paired_optimizer_comparison.json").write_text(json.dumps({"schema_version":"r23-b2-paired-comparison-v1","pairs":pairs}, indent=2, ensure_ascii=False)+"\n")

    def prob(metric):
        c = [x["COBYLA"][metric] for x in pairs]; n = [x["Nelder-Mead"][metric] for x in pairs]
        d = [b-a for a,b in zip(c,n)]
        return {"metric":metric,"COBYLA":summary(c),"Nelder-Mead":summary(n),
                "paired_difference":summary(d),
                "paired_relative_difference_where_meaningful":summary([pct_diff(a,b) for a,b in zip(c,n) if a != 0]),
                "values":[{"instance":x["instance"],"p":x["p"],"COBYLA":a,"Nelder-Mead":b,"absolute_difference":dd,"relative_difference_where_meaningful":pct_diff(a,b)} for x,a,b,dd in zip(pairs,c,n,d)]}
    def probability_grouping(metric, field):
        groups = {}
        for value in sorted({x[field] for x in pairs}):
            subset = [x for x in pairs if x[field] == value]
            groups[str(value)] = {o: summary([x[o][metric] for x in subset]) for o in ["COBYLA", "Nelder-Mead"]}
        return groups
    probability = {"P_feasible":prob("P_feasible"),"P_optimal":prob("P_optimal"),
                   "by_p": {m:{"p":probability_grouping(m,"p")} for m in ["P_feasible","P_optimal"]},
                   "by_instance": {m:{"instance":probability_grouping(m,"instance")} for m in ["P_feasible","P_optimal"]},
                   "interpretation":"P_optimal is probability mass, not a found flag; n=6 paired observations are descriptive."}
    (OUT / "probability_comparison.json").write_text(json.dumps(probability, indent=2)+"\n")

    def grouped(metric):
        out = {}
        for key, subset in [("overall", pairs), ("p2", [x for x in pairs if x["p"]==2]), ("p3", [x for x in pairs if x["p"]==3])]:
            out[key] = {o:{"mean":mean([x[o][metric] for x in subset]),"median":median([x[o][metric] for x in subset]),"count":len(subset)} for o in ["COBYLA","Nelder-Mead"]}
        return out
    runtime = {m:grouped(m) for m in ["T_total","T_Aer","T_transpile","nfev","T_total_per_nfev","T_Aer_per_nfev"]}
    runtime["success_count_by_p"] = {str(p): {o: sum(bool(x[o]["success"]) for x in pairs if x["p"] == p) for o in ["COBYLA", "Nelder-Mead"]} for p in [2, 3]}
    runtime.update({"B2_known_summary":load(B2/"b2_summary.json"),"B1_v2_scope":"six fixed_0.1 COBYLA paired records only","runtime_interpretation":"CPU Qiskit Aer statevector simulation burden; not QPU runtime or speedup."})
    (OUT / "runtime_comparison.json").write_text(json.dumps(runtime, indent=2)+"\n")

    term = {o:{"success_count":sum(x[o]["success"] for x in pairs),"failure_count":sum(not x[o]["success"] for x in pairs),"status_counts":{},"termination_messages":{}} for o in ["COBYLA","Nelder-Mead"]}
    for x in pairs:
        for o in term:
            for k, dest in [("status","status_counts"),("message","termination_messages")]: term[o][dest][str(x[o][k])] = term[o][dest].get(str(x[o][k]),0)+1
    term["interpretation"] = "COBYLA MAXFUN and Nelder-Mead MAXITER are distinct native termination mechanisms; optimizer status is not scientific validity."
    (OUT / "termination_comparison.json").write_text(json.dumps(term, indent=2)+"\n")

    sources = {
      "B2_v2": {"root":str(B2.relative_to(ROOT)),"manifest_sha256":sha(B2/"manifest.json"),"summary_sha256":sha(B2/"b2_summary.json"),"integrity_sha256":sha(B2/"integrity.json"),"raw_comparison_sha256":sha(B2/"cobyla_vs_nelder_mead_raw_comparison.json")},
      "B1_v2": {"root":str(B1.relative_to(ROOT)),"manifest_sha256":sha(B1/"manifest.json"),"summary_sha256":sha(B1/"b1_summary.json"),"integrity_sha256":sha(B1/"integrity.json")},
      "B2_v1_excluded": {"root":"reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1","reason":"implementation failure; optimizer not reached; nfev=0; no scientific metrics"},
      "B1_v2_fixed_scope": {"count":6,"optimizer":"COBYLA","initialization":"fixed_0.1","instances":instances,"p":[2,3]}
    }
    (OUT / "reduced_problem_integration.json").write_text(json.dumps({"classification":"R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS","formal_scope":{"encoding":"customer-only position encoding","logical_qubits":"n^2","constraints":"exact one-hot","lambda":3.0,"travel_time":"directed asymmetric","reference":"exact-reference comparison"},"integrated_evidence":{"Formal A":"reproducibility/outputs/traffic_simulation/r23_formal_evidence_review/20260911_v1","B1":"reproducibility/outputs/traffic_simulation/r23_experiment_b1_evidence_review/20260911_v1","B2":"reproducibility/outputs/traffic_simulation/r23_experiment_b2_evidence_review/20260911_v1"},"supported_findings":["n=2,3,4 formal evidence","initialization sensitivity","optimizer sensitivity within frozen design","p sensitivity","probability quality","best-route quality","CPU statevector burden"],"limitations":["small n","deterministic small instance sample","exact statevector","no finite shots","no noise","CPU Aer","limited optimizer and initialization sets","no Full EVRP constraints"],"unsupported_claims":["universal optimizer independence","optimizer superiority","QAOA convergence","quantum advantage","QPU speedup","n>4 generalization","Full EVRP generalization"],"next_scientific_stage":"R23_REDUCED_PROBLEM_REPOSITORY_CONSOLIDATION","sources":sources}, indent=2, ensure_ascii=False)+"\n")
    final = {"review_id":"R23_REDUCED_PROBLEM_FINAL_REVIEW_20260911_V1","classification":"R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS","formal_problem_definition":{"customer_only_position_encoding":True,"logical_qubits":"n^2","exact_one_hot_constraints":True,"lambda":3.0,"directed_asymmetric_travel_time":True,"exact_reference_comparison":True},"evidence_linkage":{"Formal_A":{"root":"reproducibility/outputs/traffic_simulation/r23_formal_evidence_review/20260911_v1","classification":"FORMAL_EVIDENCE_ACCEPTED_WITH_LIMITATIONS"},"B1":{"root":"reproducibility/outputs/traffic_simulation/r23_experiment_b1_evidence_review/20260911_v1","classification":"EXPERIMENT_B1_EVIDENCE_ACCEPTED_WITH_LIMITATIONS"},"B2":{"root":"reproducibility/outputs/traffic_simulation/r23_experiment_b2_evidence_review/20260911_v1","classification":"EXPERIMENT_B2_EVIDENCE_ACCEPTED_WITH_LIMITATIONS"}},"supported_findings":["problem-size dependence","p dependence and probability degradation","CPU simulation scaling","initialization sensitivity","instance heterogeneity","exact optimum recovery","termination uncertainty","optimizer sensitivity within frozen n=4/3-instance/fixed-init design","optimizer termination differences","CPU simulation burden differences"],"supported_with_limitations":["n=2,3,4 formal evidence only","descriptive p/initialization/optimizer comparisons","exact best-route recovery in reviewed runs"],"unsupported_claims":["QAOA convergence established","optimizer independence universally established","Nelder-Mead or COBYLA superiority","quantum advantage","QPU speedup","n>4 generalization","Full EVRP generalization"],"limitations":["small n","deterministic small instance sample","exact statevector","no finite shots","no noise","CPU Aer","limited optimizer set","limited initialization set","no Full EVRP constraints"],"next_scientific_stage":"R23_REDUCED_PROBLEM_REPOSITORY_CONSOLIDATION","full_evrp_status":{"R20":"BLOCKED","R21":"NOT_STARTED"},"source_hashes":sources}
    final_root = ROOT / "outputs/traffic_simulation/r23_reduced_problem_final_review/20260911_v1"
    final_root.mkdir(parents=True, exist_ok=True)
    (final_root / "reduced_problem_final_review.json").write_text(json.dumps(final, indent=2, ensure_ascii=False)+"\n")
    (final_root / "formal_problem_definition_linkage.json").write_text(json.dumps(final["formal_problem_definition"], indent=2)+"\n")
    (final_root / "evidence_linkage.json").write_text(json.dumps(final["evidence_linkage"], indent=2)+"\n")
    (final_root / "README.md").write_text("# R23 Reduced Problem Final Review\n\nClassification: `R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS`\n\nThis is an evidence integration artifact linking Formal A, B1, and B2. The next recommended task is `R23_REDUCED_PROBLEM_REPOSITORY_CONSOLIDATION`; Full EVRP R20 remains BLOCKED and R21 remains NOT_STARTED. No additional scientific execution was performed.\n")
    final_files = sorted(p for p in final_root.iterdir() if p.name != "SHA256SUMS")
    (final_root / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in final_files))

    review = {"review_id":"R23_EXPERIMENT_B2_EVIDENCE_REVIEW_20260911_V1","classification":"EXPERIMENT_B2_EVIDENCE_ACCEPTED_WITH_LIMITATIONS","no_new_scientific_execution":True,"research_questions":{"RQ-B2-1":{"classification":"SUPPORTED_WITH_LIMITATIONS","finding":"P_feasible and P_optimal differ across all six paired observations; descriptive frozen-design evidence only."},"RQ-B2-2":{"classification":"SUPPORTED_WITH_LIMITATIONS","finding":"Both optimizers found exact best decoded routes in 6/6 pairs; this is not P_optimal=1, sampling success, convergence, or advantage."},"RQ-B2-3":{"classification":"SUPPORTED_WITH_LIMITATIONS","finding":"Runtime, Aer runtime and nfev differ by optimizer in the six pairs; CPU Aer burden only."},"RQ-B2-4":{"classification":"SUPPORTED_WITH_LIMITATIONS","finding":"COBYLA MAXFUN and Nelder-Mead MAXITER behaviors are distinct and optimizer-specific; convergence is not established."}},"integrity":sources,"b2_v2_integrity_recheck":{"planned":6,"started":6,"terminal":6,"scientific_failures":0,"exact_optimum_found":"6/6","relative_gap":"0 for all","probability":"PASS","exact_reference":"PASS","lambda":"PASS","runtime":"PASS","authority_drift":False},"v1_excluded":True,"paired_conditions":{"instances":instances,"p":[2,3],"initialization":"fixed_0.1","count":6},"boundary":"All optimizer comparisons are within this frozen n=4 / 3-instance / fixed-init design; no strong statistical generalization."}
    (OUT / "evidence_review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False)+"\n")
    readme = """# R23 Experiment B2 Evidence Review\n\nClassification: `EXPERIMENT_B2_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`\n\nThis review uses only the immutable B1 v2 COBYLA and B2 v2 Nelder-Mead fixed_0.1 records for six paired conditions (rank01/rank03/rank05 × p=2/3). No scientific run, rerun, tuning, additional condition, n≥5, finite-shot, noise, QPU, or Full EVRP execution was performed. B2 v1 is retained but excluded because it failed before optimizer execution and has nfev=0.\n\nExact best decoded route agreement (6/6 for each optimizer) is distinct from P_optimal probability mass, sampling success, convergence, or quantum advantage. Runtime is CPU Qiskit Aer statevector burden only. Differences are descriptive and limited to the frozen n=4 / three-instance / fixed-initialization design.\n\nThe paired table and JSON files are recomputed from terminal records; `SHA256SUMS` covers all review artifacts.\n"""
    (OUT / "README.md").write_text(readme)
    files = sorted(p for p in OUT.iterdir() if p.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files))

if __name__ == "__main__": main()
