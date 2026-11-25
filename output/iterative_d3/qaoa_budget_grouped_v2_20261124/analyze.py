"""Export archived optimizer histories and aggregate the paired budget pilot."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import statistics as stats
import sys

from pilot import BUDGETS, HERE, ROOT, SOURCE, cost, load_policy, load_problem, problem_of, quantum, read, sha

ANGLES = ("gamma1", "beta1", "gamma2", "beta2")
CANDIDATE_KIND = "measured_order_only_QAOA"
SCALES = ("S1", "S2", "S3")


def output_csv(path, rows):
    if not rows:
        raise ValueError(f"EMPTY_TABLE {path.name}")
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def output_json(path, value):
    with path.open("x") as file:
        json.dump(value, file, indent=2, ensure_ascii=False, allow_nan=False)
        file.write("\n")


def distribution(values):
    return dict(n=len(values), mean=stats.mean(values), median=stats.median(values),
                sd=stats.stdev(values) if len(values) > 1 else None,
                min=min(values), max=max(values))


def eval_header(path):
    with path.open() as file:
        metadata = []
        for line in file:
            if line.startswith('  "updates":'):
                return json.loads("".join(metadata).rstrip().removesuffix(",") + "}")
            metadata.append(line)
    raise ValueError(f"MISSING_EVAL_METADATA {path}")


def trace(solver, identity, result, bound):
    records = []
    seeds = read(solver / "CALL.json")["settings"]["measurement_seeds"]
    best = math.inf
    for i, file in enumerate(sorted(solver.glob("EVAL_*.json"))):
        data = eval_header(file)
        event = data["identity"]
        if (file.name != f"EVAL_{i:03d}.json" or event["phase"] != "optimization"
                or event["shots"] != 1000 or event["problem_hash"] != result["problem_hash"]
                or event["seed"] != seeds["optimization"][i] or sum(data["counts"].values()) != 1000):
            raise ValueError(f"EVALUATION_IDENTITY {file}")
        mean = data["objective"]
        best = min(best, mean)
        records.append(identity | dict(eval=i+1, mean_normalized=mean, mean_m=mean*bound,
                                       best_so_far_normalized=best, best_so_far_m=best*bound,
                                       unique_orders=len(data["counts"]), seed=event["seed"])
                       | dict(zip(ANGLES, event["angles"])))
    final = eval_header(solver / "FINAL_SAMPLE.json")
    if (len(records) != result["training_evaluations"] or
            final["identity"]["seed"] != seeds["final"] or final["identity"]["shots"] != 10000 or
            sum(final["counts"].values()) != 10000 or final["identity"]["angles"] != result["angles"]):
        raise ValueError(f"FINAL_MEASUREMENT_IDENTITY {solver}")
    return records, final


def by_evaluation(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in (*keys, "eval"))].append(row)
    result = []
    for group, records in sorted(groups.items()):
        summary = dict(zip((*keys, "eval"), group)) | {"n": len(records)}
        for name in ("mean_normalized", "mean_m", "best_so_far_normalized", *ANGLES):
            values = [r[name] for r in records]
            summary |= {f"{name}_{key}": v for key, v in distribution(values).items() if key != "n"}
        result.append(summary)
    return result


def archived_branch(job):
    scale, branch = job
    traces, calls, candidates = [], [], []
    method = SOURCE / scale / "D_quantum"
    method_plan = read(method / "plan.json")
    selected_branch = read(method / "RESULT.json")["chosen_branch"]
    directory = method / f"branch_{branch}"
    branch_plan = read(directory / "plan.json")
    commits = sorted(directory.glob("iteration_*/COMMIT.json"))
    if len(commits) != read(directory / "RESULT.json")["completed"]:
        raise ValueError("INCOMPLETE_ARCHIVE_TRACE")
    for marker in commits:
        commit = read(marker)
        local = marker.parent / "local_000"
        if not local.is_dir():
            continue
        identity = dict(scale=scale, branch=branch, iteration=commit["iteration"]+1)
        solver = local / "solver"
        problem = read(local / "CASE.json")["problem"]
        bound = problem["lookup"]["bound_m"]
        result = read(solver / "RESULT.json")
        main = read(solver / "CALL.json")["settings"]
        selector = read(local / "SELECTOR.json")
        ordered = [r for r in commit["candidate_receipts"] if r["kind"] == CANDIDATE_KIND]
        count = result["training_evaluations"]
        if len(ordered) != len(selector["candidates"]):
            raise ValueError("ARCHIVE_CANDIDATE_COUNT")
        records, final = trace(solver, identity, result, bound)
        traces.extend(records)
        adopted = False
        distances = []
        for rank, (item, receipt) in enumerate(zip(selector["candidates"], ordered), 1):
            if receipt["id"] != f"order_{rank-1}":
                raise ValueError("ARCHIVE_CANDIDATE_ORDERING")
            metrics = receipt["metrics"] or {}
            fingerprint = metrics.get("physical_hash")
            row = identity | dict(
                rank=rank, reason=item["selection_reason"], local_distance_m=item["local_distance_m"],
                measured_count=item["count"], status=receipt["status"], adopted_at_iteration=commit["adopted"]==receipt["id"],
                equals_branch_final=fingerprint==branch_plan["physical_hash"],
                equals_method_final=branch==selected_branch and fingerprint==method_plan["physical_hash"],
                D_km=float(Fraction(metrics["D_exact"])) if metrics else None,
                W_min=float(Fraction(metrics["W_exact"])) if metrics else None,
                physical_hash=fingerprint, order=" ".join(map(str, item["order"])))
            candidates.append(row)
            adopted |= row["adopted_at_iteration"]
            distances.append(item["local_distance_m"])
        calls.append(identity | dict(
            evals=count, cap=main["optimizer_max_evaluations"], at_cap=count==main["optimizer_max_evaluations"],
            success=result["optimizer_success"], reason=result["optimizer_message"], bound_m=bound,
            train_initial=records[0]["mean_normalized"], train_best=result["optimizer_fun"],
            final_mean=final["objective"], final_mean_m=final["objective"]*bound,
            shortest_returned_m=min(distances), unique_final_orders=selector["unique_valid_orders"],
            returned=len(ordered), feasible=sum(row["status"]=="FEASIBLE" for row in ordered),
            any_adoption=adopted, shots=result["total_shots_actual"], wall_s=result["wall_s"], cpu_s=result["CPU_s"])
            | dict(zip(ANGLES, result["angles"])))
    print("archived", scale, "branch", branch, len(calls), "calls", len(traces), "evaluations", flush=True)
    return traces, calls, candidates


def archived():
    if read(SOURCE / "COMPLETE.json")["status"] != "COMPLETE_PILOT":
        raise ValueError("ARCHIVED_PILOT_INCOMPLETE")
    traces, calls, candidates = [], [], []
    jobs = [(scale, branch) for scale in SCALES for branch in range(4)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        for branch_trace, branch_calls, branch_candidates in pool.map(archived_branch, jobs):
            traces.extend(branch_trace)
            calls.extend(branch_calls)
            candidates.extend(branch_candidates)
    output_csv(HERE / "archive_calls.csv", calls)
    output_csv(HERE / "archive_evaluations.csv", traces)
    output_csv(HERE / "archive_evaluation_summary.csv", by_evaluation(traces, ("scale",)) + by_evaluation(traces, ()))
    output_csv(HERE / "archive_candidates.csv", candidates)
    report = {}
    for scale in (*SCALES, "all"):
        rows = [r for r in calls if r["scale"] == scale or scale == "all"]
        cand = [r for r in candidates if r["scale"] == scale or scale == "all"]
        report[scale] = dict(
            calls=len(rows), evals=dict(sorted(Counter(r["evals"] for r in rows).items())), at_cap=sum(r["at_cap"] for r in rows),
            success=sum(r["success"] for r in rows), termination=dict(Counter(r["reason"] for r in rows)),
            training_gain=distribution([r["train_initial"]-r["train_best"] for r in rows]),
            final_minus_training_best=distribution([r["final_mean"]-r["train_best"] for r in rows]),
            returned=sum(r["returned"] for r in rows), feasible=sum(r["feasible"] for r in rows),
            any_adoption=sum(r["any_adoption"] for r in rows), matches_branch_final=sum(r["equals_branch_final"] for r in cand),
            matches_method_final=sum(r["equals_method_final"] for r in cand), shortest_m=distribution([r["shortest_returned_m"] for r in rows]),
            total_learning_evals=sum(r["evals"] for r in rows), total_shots=sum(r["shots"] for r in rows),
            final_angles={angle: distribution([r[angle] for r in rows]) for angle in ANGLES})
    output_json(HERE / "archive_summary.json", report)
    figures(traces, "archive", ("scale",))


def paired():
    protocol = read(HERE / "PROTOCOL.json")
    completion = read(HERE / "RUN_COMPLETE.json")
    if completion["protocol_sha256"] != sha(HERE / "PROTOCOL.json"):
        raise ValueError("UNBOUND_PILOT_COMPLETION")
    def load_trace(job):
        scale, rep, cap = job
        folder = HERE / "runs" / scale / f"seed_{rep}" / f"cap_{cap}"
        result = read(folder / "RESULT.json")
        solver = folder / "solver"
        identity = dict(scale=scale, replicate=rep, budget=cap)
        records, final = trace(solver, identity, read(solver / "RESULT.json"), result["bound_m"])
        return job, (result, read(solver / "CALL.json"), records, final)

    jobs = [(scale, rep, cap) for scale in SCALES for rep in protocol["replicates"] for cap in BUDGETS]
    with ThreadPoolExecutor(max_workers=12) as pool:
        loaded = dict(pool.map(load_trace, jobs))
    verified = verify_selected_plans(protocol, loaded)
    blocks = {}
    traces, rows, candidates, comparisons = [], [], [], []
    common_evaluations = 0
    for scale in SCALES:
        for rep in protocol["replicates"]:
            pair = {}
            observed = {}
            blocks[scale, rep] = pair
            source = next(case for case in protocol["cases"] if case["scale"]==scale)
            problem = problem_of(read(Path(source["local"])))
            c = loaded[scale, rep, 24][0]["classical_reference"]
            ref_call = loaded[scale, rep, 192][1]
            ref_seed = ref_call["settings"]["measurement_seeds"]
            for cap in BUDGETS:
                identity = dict(scale=scale, replicate=rep, budget=cap)
                result, call, records, final = loaded[scale, rep, cap]
                if any(result[key] != value for key, value in identity.items()) or result["evals"] > cap or result["valid_shots"] > 10000:
                    raise ValueError("PILOT_RESULT_CONTRACT")
                seed = call["settings"]["measurement_seeds"]
                if (seed["final"] != ref_seed["final"] or seed["final"] in seed["optimization"] or
                        seed["optimization"] != ref_seed["optimization"][:cap] or
                        {k: v for k, v in call["settings"].items() if k not in ("optimizer_max_evaluations", "measurement_seeds")} !=
                        {k: v for k, v in ref_call["settings"].items() if k not in ("optimizer_max_evaluations", "measurement_seeds")} or
                        call["problem_hash"] != result["case_hash"] or ref_call["problem_hash"] != result["case_hash"] or
                        (call["p"], call["return_limit"], call["optimization_shots"], call["final_shots"]) != (2, 4, 1000, 10000)):
                    raise ValueError("UNPAIRED_BUDGET")
                for record in records:
                    key = (record["eval"], *(record[name] for name in ANGLES), record["seed"])
                    value = (record["mean_normalized"], record["unique_orders"])
                    previous = observed.setdefault(key, value)
                    if previous != value:
                        raise ValueError("SHARED_EVALUATION_CHANGED")
                common_evaluations += len(records)
                final_samples = [(cost(problem, quantum.decode(bits, problem)), count)
                                 for bits, count in final["counts"].items()]
                if len(final_samples) != result["unique_valid_orders"]:
                    raise ValueError("FINAL_ORDER_COUNT_MISMATCH")
                final_mean = math.fsum(x * n for x, n in final_samples) / 10000
                if not math.isclose(final_mean, result["final_mean_m"], rel_tol=1e-14):
                    raise ValueError("FINAL_MEAN_RECALCULATION")
                final_se = math.sqrt(math.fsum(n * (x-final_mean)**2 for x, n in final_samples) / (9999*10000))
                min_distance = result["min_returned_distance_m"]
                exact = result["exact"]["distance_m"]
                if min_distance is not None and not math.isclose(min_distance, result["minimum_measured_m"], abs_tol=1e-8):
                    raise ValueError("SELECTOR_DID_NOT_RETURN_SHORTEST")
                if min_distance is not None and min_distance < exact - 1e-8:
                    raise ValueError("SAMPLE_BELOW_EXACT_OPTIMUM")
                traces.extend(records)
                pair[cap] = result
                d0 = result["incumbent"]
                d1 = result["selected"]
                row = identity | dict(
                    evals=result["evals"], at_cap=result["evals"]==cap, optimizer_success=result["optimizer_success"],
                    reason=result["optimizer_message"], train_best_normalized=result["training_best_normalized"],
                    final_mean_normalized=final["objective"], final_mean_m=result["final_mean_m"],
                    final_sample_mean_se_m=final_se,
                    shortest_m=min_distance, original_window_m=result["initial_cost_m"], exact_m=exact,
                    shortest_gap_pp=100*(min_distance/exact-1) if min_distance is not None else None,
                    classical_shortest_m=c["min_returned_distance_m"], delta_shortest_vs_classical_m=min_distance-c["min_returned_distance_m"],
                    classical_shortest_gap_pp=100*(c["min_returned_distance_m"]/exact-1),
                    classical_evals=c["objective_evaluations"], sampled_feasible_frac=result["valid_shots"]/result["final_shots"],
                    unique_final_orders=result["unique_valid_orders"], entropy_effective_orders=result["entropy_effective_orders"],
                    returned=len(result["candidates"]), returned_feasible=result["feasible_candidates"],
                    has_feasible=result["feasible_candidates"]>0, shots=result["shots"], cpu_s=result["cpu_s"], wall_s=result["wall_s"],
                    D_km=d1["D_km"], W_min=d1["W_total_min"], I_dual_B_pp=d1["I_dual_B_pp"],
                    delta_D_km=d1["D_km"]-d0["D_km"], delta_W_min=d1["W_total_min"]-d0["W_total_min"],
                    delta_I_dual_B_pp=d1["I_dual_B_pp"]-d0["I_dual_B_pp"],
                    classical_D_km=c["selected"]["D_km"], classical_W_min=c["selected"]["W_total_min"],
                    classical_I_dual_B_pp=c["selected"]["I_dual_B_pp"], selected_candidate=result["selected_candidate"] is not None)
                result["shortest_gap_pp"] = row["shortest_gap_pp"]
                rows.append(row | dict(zip(ANGLES, result["angles"])))
                for i, item in enumerate(result["candidates"]):
                    candidates.append(identity | (item | {"order": " ".join(map(str, item["order"]))})
                                      | dict(index=i, selected=i==result["selected_candidate"]))
                if cap == BUDGETS[0]:
                    for i, item in enumerate(c["candidates"]):
                        candidates.append(identity | (item | {"order": " ".join(map(str, item["order"]))})
                                          | dict(budget="classical", index=i, selected=i==c["selected_candidate"]))
            common_evaluations -= len(observed)
    thresholds = protocol["stopping_thresholds"]
    pair_summary = []
    for i, lower in enumerate(BUDGETS[:-1]):
        for upper in BUDGETS[i+1:]:
            subset = []
            for (scale, rep), pair in blocks.items():
                a, b = pair[lower], pair[upper]
                x, y = a["selected"], b["selected"]
                dg = Fraction(x["D_exact"])-Fraction(y["D_exact"])
                wg = Fraction(x["W_exact"])-Fraction(y["W_exact"])
                ig = y["I_dual_B_pp"]-x["I_dual_B_pp"]
                row = dict(scale=scale, replicate=rep, lower=lower, upper=upper,
                           final_mean_gain=a["final_mean_normalized"]-b["final_mean_normalized"],
                           gap_gain_pp=a["shortest_gap_pp"]-b["shortest_gap_pp"],
                           D_gain_km=float(dg), W_gain_min=float(wg), I_dual_gain_pp=ig,
                           global_gain=dg >= 0 and wg >= 0 and (
                               dg >= Fraction(str(thresholds["global_D_km_gain_min"])) or
                               wg >= Fraction(str(thresholds["global_W_min_gain_min"])) or ig >= thresholds["global_I_dual_pp_gain_min"]),
                           candidate_block_loss=a["feasible_candidates"]>0 and b["feasible_candidates"]==0,
                           additional_shots=b["shots"]-a["shots"], additional_cpu_s=b["cpu_s"]-a["cpu_s"],
                           identical_angles=a["angles"]==b["angles"], identical_plan=x["physical_hash"]==y["physical_hash"])
                subset.append(row)
            comparisons.extend(subset)
            summary = dict(lower=lower, upper=upper)
            for key in ("final_mean_gain", "gap_gain_pp", "D_gain_km", "W_gain_min", "I_dual_gain_pp",
                        "additional_shots", "additional_cpu_s"):
                summary[key] = distribution([r[key] for r in subset])
            for key, threshold in (("final_mean_gain", thresholds["block_final_mean_gain_min"]),
                                   ("gap_gain_pp", thresholds["block_shortest_gap_gain_pp_min"])):
                passed = [r for r in subset if r[key] >= threshold]
                summary[key]["material_blocks"] = len(passed)
                summary[key]["material_scales"] = len({r["scale"] for r in passed})
                summary[key]["material"] = (summary[key]["median"] >= threshold and
                    len(passed) >= thresholds["local_consistent_blocks_min"] and
                    len({r["scale"] for r in passed}) >= thresholds["local_consistent_scales_min"])
            passed = [r for r in subset if r["global_gain"]]
            summary.update(global_material_blocks=len(passed), global_material_scales=len({r["scale"] for r in passed}),
                           global_material=(len(passed) >= thresholds["global_blocks_min"] and
                               len({r["scale"] for r in passed}) >= thresholds["global_scales_min"] and
                               summary["I_dual_gain_pp"]["median"] >= 0 and not any(r["candidate_block_loss"] for r in subset)),
                           identical_angles=sum(r["identical_angles"] for r in subset),
                           identical_plan=sum(r["identical_plan"] for r in subset))
            pair_summary.append(summary)
    retained = BUDGETS[0]
    for cap in BUDGETS[1:]:
        if next(row for row in pair_summary if row["lower"]==retained and row["upper"]==cap)["global_material"]:
            retained = cap
    caps = {}
    for cap in BUDGETS:
        subset = [r for r in rows if r["budget"] == cap]
        caps[cap] = {key: distribution([r[key] for r in subset])
                     for key in ("evals", "final_mean_normalized", "shortest_gap_pp", "delta_shortest_vs_classical_m",
                                 "unique_final_orders", "entropy_effective_orders", "shots", "cpu_s", "wall_s",
                                 "delta_D_km", "delta_W_min", "delta_I_dual_B_pp")}
        caps[cap] |= dict(success=sum(r["optimizer_success"] for r in subset), at_cap=sum(r["at_cap"] for r in subset),
                         feasible_shot_fraction=stats.mean(r["sampled_feasible_frac"] for r in subset),
                         feasible_candidates=sum(r["returned_feasible"] for r in subset), candidates=sum(r["returned"] for r in subset),
                         blocks_with_feasible=sum(r["has_feasible"] for r in subset), selections=sum(r["selected_candidate"] for r in subset))
    output_csv(HERE / "paired_runs.csv", rows)
    output_csv(HERE / "paired_candidates.csv", candidates)
    output_csv(HERE / "paired_evaluations.csv", traces)
    output_csv(HERE / "paired_evaluation_summary.csv", by_evaluation(traces, ("budget",)))
    output_csv(HERE / "paired_differences.csv", comparisons)
    output_json(HERE / "paired_summary.json", dict(recommendation=retained, budgets=caps,
                paired_comparisons=pair_summary, shared_evaluations_compared=common_evaluations))
    output_json(HERE / "paired_verification.json", verified)
    figures(traces, "paired", ("budget",))


def verify_selected_plans(protocol, loaded):
    sys.path.insert(0, str(ROOT / "scripts"))
    from audit_grouped_loading_v2 import independently_build, recheck

    duty = load_policy() | {"loading_s": protocol["grouped_conditions"]["loading_s"]}
    formal = HERE.parent / "formal_J30_grouped_v2"
    manifest = formal / "MANIFEST.json"
    freeze = formal / "FREEZE_RECORD.json"
    formal_binding = dict(manifest_sha256=sha(manifest), freeze_sha256=sha(freeze),
                          grouped_worker_start_record=(formal / "EXECUTION_STARTED.json").exists())
    results = []
    unique_seed_bank = set()
    for source in protocol["cases"]:
        scale = source["scale"]
        problem = load_problem(source["input"], protocol["configuration"]["rest_options"])
        berths = {b.berth_id: (b.opening_s, b.closing_s) for b in problem.berths}
        for rep in protocol["replicates"]:
            seed = loaded[scale, rep, BUDGETS[-1]][1]["settings"]["measurement_seeds"]
            unique_seed_bank.update((*seed["optimization"], seed["final"]))
            for cap in BUDGETS:
                folder = HERE / "runs" / scale / f"seed_{rep}" / f"cap_{cap}"
                plan = read(folder / "selected_plan.json")
                result = loaded[scale, rep, cap][0]
                audit = recheck.recheck(plan, independently_build(problem, plan), berths, duty, problem.rest_options, problem.depot.depot_id)
                if (plan["physical_hash"] != result["selected"]["physical_hash"] or
                        audit["D_exact"] != result["selected"]["D_exact"] or
                        Fraction(audit["W_total_s"], 60) != Fraction(result["selected"]["W_exact"])):
                    raise ValueError("INDEPENDENT_PLAN_METRICS")
                results.append(dict(scale=scale, replicate=rep, budget=cap, **audit))
    if len(unique_seed_bank) != len(protocol["cases"]) * len(protocol["replicates"]) * (BUDGETS[-1]+1):
        raise ValueError("DIAGNOSTIC_SEED_COLLISION")
    return dict(selected_plans=results, unique_longest_budget_seeds=len(unique_seed_bank), formal=formal_binding)


def figures(traces, kind, keys):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), layout="constrained")
    names = ("mean_normalized", "best_so_far_normalized", *ANGLES)
    titles = ("Sample mean cost", "Best training sample mean", "Gamma 1", "Beta 1", "Gamma 2", "Beta 2")
    groups = defaultdict(list)
    for row in by_evaluation(traces, keys):
        groups[row[keys[0]]].append(row)
    for axis, name, title in zip(axes.flat, names, titles):
        for group, series in groups.items():
            x = [r["eval"] for r in series]
            y = [r[f"{name}_median"] for r in series]
            axis.plot(x, y, label=str(group))
        axis.set(title=title, xlabel="Objective evaluation", ylabel="Normalized distance" if name.endswith("normalized") else "Radians")
        axis.grid(alpha=0.2)
        axis.legend(title=keys[0].capitalize())
    fig.suptitle("Pointwise medians among calls reaching each evaluation")
    fig.savefig(HERE / f"{kind}_trajectories.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("archive", "paired"))
    args = parser.parse_args()
    {"archive": archived, "paired": paired}[args.action]()
