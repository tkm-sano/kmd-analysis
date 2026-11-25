"""Verify and summarize the registered initial-angle pilot."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
import math
from pathlib import Path
from statistics import median
import sys

from experiment import (
    ANGLE_NAMES, ARMS, HERE, ROOT, SCALES, cost, formal_guard, load_policy, load_problem,
    output_csv, problem_of, quantum, read, registered, sha,
)
from analyze import by_evaluation, distribution, output_json, trace

SHORT_METRICS = ("final_norm", "train_best_norm", "min_measured_m", "min_returned_m", "gap_pp",
                 "returned_gap_pp", "Q_minus_classical_m", "D_km", "W_min", "I_dual_pp", "feasible_fraction",
                 "has_feasible", "evals", "shots", "wall_s", "cpu_s")
LARGER_BETTER = {"I_dual_pp", "feasible_fraction", "has_feasible"}


def full_metrics(selected, base):
    d, w = Fraction(selected["D_exact"]), Fraction(selected["W_exact"])
    bd, bw = Fraction(base["D_exact"]), Fraction(base["W_exact"])
    return d, w, 100*min(1-d/bd,1-w/bw)


def load_one(item):
    case, rep, arm, protocol, seed = item
    folder = HERE/"runs"/case["id"]/f"seed_{rep}"/arm
    raw = read(folder/"RESULT.json")
    solver = folder/"solver"
    call = read(solver/"CALL.json")
    solver_result = read(solver/"RESULT.json")
    identity = dict(case=case["id"],scale=case["scale"],origin=case["origin"],replicate=rep,arm=arm)
    expected = protocol["configuration"]["search"]["quantum"] | dict(
        initial_angles=protocol["conditions"]["angles"][arm],
        measurement_seeds=dict(optimization=seed["optimization"],final=seed["final"]))
    if (call["settings"]!=expected or call["problem_hash"]!=case["case_hash"] or
            raw["case_hash"]!=case["case_hash"] or raw["training_evaluations"]>24 or
            (call["p"],call["optimization_shots"],call["final_shots"],call["return_limit"])!=(2,1000,10000,4)
            or raw["total_shots_actual"]!=1000*raw["training_evaluations"]+10000 or
            len(raw["candidates"])>4 or raw["valid_shots"]!=10000):
        raise ValueError("ARM_EXECUTION_CONTRACT")
    records, final = trace(solver,identity,solver_result,raw["bound_m"])
    if ([records[0][k] for k in ANGLE_NAMES]!=expected["initial_angles"] or
            not math.isclose(records[-1]["best_so_far_normalized"],raw["optimizer_fun"],abs_tol=1e-14) or
            raw["selected_plan_sha256"]!=sha(folder/"selected_plan.json")):
        raise ValueError("ARM_RESULT_BINDING")
    problem = problem_of(read(Path(case["local"])))
    costs = [(cost(problem,quantum.decode(bits,problem)),n) for bits,n in final["counts"].items()]
    mean = math.fsum(d*n for d,n in costs)/10000
    se = math.sqrt(math.fsum(n*(d-mean)**2 for d,n in costs)/(9999*10000))
    min_cost = min(d for d,_ in costs)
    if (not math.isclose(mean/raw["bound_m"],raw["final_norm"],abs_tol=1e-14)
            or min_cost!=raw["min_measured_m"] or raw["min_returned_distance_m"]!=min_cost):
        raise ValueError("SAMPLE_AND_SELECTOR_RECHECK")
    return raw, records, identity, mean, se


def verify_plans(protocol, loaded):
    sys.path.insert(0,str(ROOT/"scripts"))
    from audit_grouped_loading_v2 import independently_build, recheck

    cfg = protocol["configuration"]
    duty = load_policy()|{"loading_s":protocol["grouped_conditions"]["loading_s"]}
    checks = []
    for scale in SCALES:
        cases = [c for c in protocol["cases"] if c["scale"]==scale]
        p = load_problem(cases[0]["input"],cfg["rest_options"])
        berths = {b.berth_id:(b.opening_s,b.closing_s) for b in p.berths}
        for case in cases:
            parent = read(Path(case["parent"]))
            for rep in (0,1):
                for arm in ARMS:
                    path = HERE/"runs"/case["id"]/f"seed_{rep}"/arm/"selected_plan.json"
                    plan = read(path)
                    result = loaded[case["id"],rep,arm][0]
                    if (plan["physical_hash"]!=result["selected"]["physical_hash"] or plan["calls_s"]!=parent["calls_s"]):
                        raise ValueError("SELECTED_PLAN_OR_CALLS")
                    audit = recheck.recheck(plan,independently_build(p,plan),berths,duty,p.rest_options,p.depot.depot_id)
                    if (Fraction(audit["D_exact"])!=Fraction(result["selected"]["D_exact"]) or
                            Fraction(audit["W_total_s"],60)!=Fraction(result["selected"]["W_exact"])):
                        raise ValueError("INDEPENDENT_PLAN_METRICS")
                    checks.append(dict(case=case["id"],replicate=rep,arm=arm,**audit))
    return checks


def classify(delta, key, tolerance):
    if abs(delta)<=tolerance:
        return "equal"
    gain = delta if key in LARGER_BETTER else -delta
    return "improved" if gain>0 else "worsened"


def summarize_pairs(rows):
    out = dict(pairs=len(rows), distinct_problems=len({r["case"] for r in rows}),
               same_plan=sum(r["same_plan"] for r in rows), pareto=dict(Counter(r["global_Pareto"] for r in rows)))
    for name in SHORT_METRICS:
        out[name] = distribution([r[f"delta_{name}"] for r in rows]) | dict(Counter(r[f"class_{name}"] for r in rows))
    return out


def decide(pairs, thresholds, runs):
    def replicate(rows, prefix):
        return dict(pairs=len(rows),problems=len({r["case"] for r in rows}),scales=len({r["scale"] for r in rows}),
                    passed=len(rows)>=thresholds[f"{prefix}_pair_count"] and
                    len({r["case"] for r in rows})>=thresholds[f"{prefix}_problem_count"] and
                    len({r["scale"] for r in rows})>=thresholds[f"{prefix}_scales"])

    local = {}
    for key, limit in (("final_norm",thresholds["final_norm_gain"]),("gap_pp",thresholds["shortest_exact_gap_gain_pp"]),
                       ("returned_gap_pp",thresholds["shortest_exact_gap_gain_pp"])):
        gains = [-r[f"delta_{key}"] for r in pairs]
        outcome = replicate([r for r,gain in zip(pairs,gains) if gain>=limit],"local")
        local[key] = outcome | dict(median_gain=median(gains),passed=outcome["passed"] and median(gains)>=limit)
    global_result = replicate([r for r in pairs if r["global_material"]],"global")
    med = median(r["delta_I_dual_pp"] for r in pairs)
    losses = sum(r["A_has_feasible"] and not r["B_has_feasible"] for r in pairs)
    rates = {}
    passed_rates = True
    for scale in ("all",*SCALES):
        group = {}
        for arm in ARMS:
            selected = [r for r in runs if r["arm"]==arm and (scale=="all" or r["scale"]==scale)]
            group[arm] = Fraction(sum(r["feasible_candidates"] for r in selected),sum(r["returned"] for r in selected))
        passed_rates &= group["B"]>=group["A"]
        rates[scale] = {k:float(v) for k,v in group.items()}
    admit = global_result["passed"] and med>=0 and losses==0 and passed_rates
    return dict(recommendation="B" if admit else "A", local=local,
                global_gate=global_result|dict(median_I_dual_gain_pp=med,feasible_call_losses=losses,
                    feasible_candidate_rate=rates,feasible_rate_nondecreasing=passed_rates,passed=admit))


def analyze():
    protocol = registered()
    finish = read(HERE/"RUN_COMPLETE.json")
    if (finish["protocol_sha256"]!=sha(HERE/"PROTOCOL.json") or finish["runs"]!=48 or
            finish["formal"]!=protocol["formal"] or formal_guard()!=protocol["formal"]):
        raise ValueError("COMPLETION_OR_FORMAL_BINDING")
    seeds = {(s["case_id"],s["replicate"]):s for s in protocol["seed_pairs"]}
    jobs = [(c,rep,arm,protocol,seeds[c["id"],rep]) for c in protocol["cases"] for rep in (0,1) for arm in ARMS]
    with ThreadPoolExecutor(max_workers=12) as pool:
        loaded = {(r[2]["case"],r[2]["replicate"],r[2]["arm"]):r for r in pool.map(load_one,jobs)}
    checks = verify_plans(protocol,loaded)
    runs, evaluations, candidates, pairs = [],[],[],[]
    thresholds = protocol["thresholds"]
    for case in protocol["cases"]:
        base = read(Path(case["base"]))
        for rep in (0,1):
            pair = {}
            xa, xb = (loaded[case["id"],rep,arm][0] for arm in ARMS)
            reference = xa["classical_reference"]
            if xa["exact"]!=xb["exact"] or xa["incumbent"]!=xb["incumbent"] or reference["objective_evaluations"]>2048:
                raise ValueError("PAIR_PHYSICAL_REFERENCE_DRIFT")
            for arm in ARMS:
                raw, rec, identity, mean, se = loaded[case["id"],rep,arm]
                d, w, i = full_metrics(raw["selected"], base)
                pd, pw, pi = full_metrics(raw["incumbent"],base)
                cd, cw, ci = full_metrics(reference["selected"],base)
                exact = raw["exact"]["distance_m"]
                returned, shortest = raw["min_returned_distance_m"],raw["min_measured_m"]
                if min(returned,shortest,reference["min_returned_distance_m"])<exact-1e-8:
                    raise ValueError("ORDER_BELOW_HELD_KARP")
                row = identity | dict(
                    final_norm=raw["final_norm"], final_mean_m=mean, final_mean_se_m=se, train_best_norm=raw["optimizer_fun"],
                    min_measured_m=shortest, min_returned_m=returned, exact_m=exact, exact_m_fraction=raw["exact"]["exact_m"],
                    gap_pp=100*(shortest/exact-1), returned_gap_pp=100*(returned/exact-1),
                    classical_m=reference["min_returned_distance_m"],classical_evals=reference["objective_evaluations"],
                    Q_minus_classical_m=returned-reference["min_returned_distance_m"], D_km=float(d),W_min=float(w),
                    I_dual_pp=float(i),D_exact=str(d),W_exact=str(w),I_exact=str(i),
                    parent_D_km=float(pd),parent_W_min=float(pw),parent_I_dual_pp=float(pi),
                    delta_parent_D_km=float(d-pd),delta_parent_W_min=float(w-pw),delta_parent_I_dual_pp=float(i-pi),
                    classical_D_km=float(cd),classical_W_min=float(cw),classical_I_dual_pp=float(ci),
                    returned=len(raw["candidates"]),feasible_candidates=raw["feasible_candidates"],
                    feasible_fraction=raw["feasible_candidates"]/len(raw["candidates"]),
                    has_feasible=raw["feasible_candidates"]>0,selected_candidate=raw["selected_candidate"],
                    selected_plan_hash=raw["selected"]["physical_hash"],evals=raw["training_evaluations"],
                    at_cap=raw["training_evaluations"]==24,success=raw["optimizer_success"],reason=raw["optimizer_message"],
                    shots=raw["total_shots_actual"],wall_s=raw["wall_s"],cpu_s=raw["CPU_s"],cached_evals=raw["cached_evals"],
                    unique_orders=raw["unique_orders"],valid_final_shots=raw["valid_shots"])
                for k, initial, final in zip(ANGLE_NAMES,protocol["conditions"]["angles"][arm],raw["angles"]):
                    row[f"initial_{k}"],row[f"final_{k}"] = initial,final
                runs.append(row)
                pair[arm] = row
                evaluations.extend(rec)
                for label, source in ((arm,raw),("classical",reference)) if arm=="A" else ((arm,raw),):
                    for n,item in enumerate(source["candidates"]):
                        candidates.append(identity|item|dict(arm=label,rank=n+1,
                            order=" ".join(map(str,item["order"])),selected=n==source["selected_candidate"]))
            a,b = pair["A"],pair["B"]
            rec = {k:a[k] for k in ("case","scale","origin","replicate")}
            exact = {key:Fraction(b[x])-Fraction(a[x]) for key,x in
                     (("D_km","D_exact"),("W_min","W_exact"),("I_dual_pp","I_exact"))}
            for key in SHORT_METRICS:
                delta = exact[key] if key in exact else b[key]-a[key]
                tol = thresholds["float_equivalence"].get(
                    "normalized" if key.endswith("_norm") else "local_m" if key.endswith("_m") else
                    "exact_gap_pp" if key in ("gap_pp","returned_gap_pp") else "",0)
                rec |= {f"A_{key}":a[key],f"B_{key}":b[key],f"delta_{key}":float(delta),f"class_{key}":classify(delta,key,tol)}
            dd,dw,di = exact.values()
            pareto = ("equal" if dd==dw==0 else "improved" if dd<=0 and dw<=0 else
                      "worsened" if dd>=0 and dw>=0 else "tradeoff")
            global_material = pareto=="improved" and (
                -dd>=Fraction(str(thresholds["global_D_km_gain"])) or
                -dw>=Fraction(str(thresholds["global_W_min_gain"])) or
                di>=Fraction(str(thresholds["global_I_dual_gain_pp"])))
            pairs.append(rec|dict(global_Pareto=pareto,global_material=global_material,
                same_plan=a["selected_plan_hash"]==b["selected_plan_hash"]))
    decision = decide(pairs,thresholds,runs)
    strata = {"all":pairs} | {s:[r for r in pairs if r["scale"]==s] for s in SCALES}
    strata |= {g:[r for r in pairs if r["origin"]==g] for g in ("current","reallocation")}
    summary = dict(decision=decision, comparisons={k:summarize_pairs(v) for k,v in strata.items()}, arms={})
    for arm in ARMS:
        rows = [r for r in runs if r["arm"]==arm]
        summary["arms"][arm] = {m:distribution([r[m] for r in rows]) for m in SHORT_METRICS} | dict(
            success=sum(r["success"] for r in rows),at_cap=sum(r["at_cap"] for r in rows), reasons=dict(Counter(r["reason"] for r in rows)),
            evaluations=sum(r["evals"] for r in rows),shots=sum(r["shots"] for r in rows),cached_evals=sum(r["cached_evals"] for r in rows),
            total_candidates=sum(r["returned"] for r in rows),feasible_candidates=sum(r["feasible_candidates"] for r in rows))
    output_csv(HERE/"runs.csv",runs)
    output_csv(HERE/"evaluations.csv",evaluations)
    output_csv(HERE/"evaluation_summary.csv",by_evaluation(evaluations,("arm","scale"))+by_evaluation(evaluations,("arm",)))
    output_csv(HERE/"paired_comparison.csv",pairs)
    output_csv(HERE/"candidates.csv",candidates)
    output_json(HERE/"summary.json",summary)
    output_json(HERE/"verification.json",dict(formal=formal_guard(),checks=checks,protocol_sha256=sha(HERE/"PROTOCOL.json")))
    figures(evaluations,pairs)
    print("ANALYZED",len(runs),"runs",len(pairs),"pairs","recommendation",decision["recommendation"],flush=True)


def figures(evaluations,pairs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not (HERE/"figures").is_dir():
        (HERE/"figures").mkdir()
    folder = HERE/"figures"
    grouped = defaultdict(list)
    for row in by_evaluation(evaluations,("arm",)):
        grouped[row["arm"]].append(row)
    colors = {"A":"#285b97","B":"#bf4a29"}

    def history(axes, names, titles):
        for axis,name,title in zip(axes,names,titles):
            for arm in ARMS:
                rows = grouped[arm]
                x = [r["eval"] for r in rows]
                y = [r[f"{name}_median"] for r in rows]
                axis.plot(x,y,label=arm,color=colors[arm])
            axis.set(xlabel="Objective evaluation",title=title,ylabel="Radians" if name in ANGLE_NAMES else "Normalized distance")
            axis.grid(alpha=.22)
            axis.legend()

    def save(fig,name):
        fig.savefig(folder/name,dpi=165)
        plt.close(fig)

    fig,axes = plt.subplots(2,2,figsize=(10,7),layout="constrained")
    history(axes.flat,ANGLE_NAMES,("Gamma 1","Beta 1","Gamma 2","Beta 2"))
    fig.suptitle("Angle trajectories | pointwise medians among calls reaching each evaluation")
    save(fig,"01_parameter_trajectories.png")
    fig,axes = plt.subplots(1,3,figsize=(13,4),layout="constrained")
    history(axes[:2],("mean_normalized","best_so_far_normalized"),("Training sample mean","Best training sample mean"))
    for r in pairs:
        axes[2].plot([0,1],[r["A_final_norm"],r["B_final_norm"]],".-",alpha=.5,color="#43574d")
    axes[2].set(xticks=[0,1],xticklabels=ARMS,title="Independent final measurement",ylabel="Normalized distance")
    fig.suptitle("QAOA costs | training traces and independent final sample means")
    save(fig,"02_expectation_trajectories.png")

    def differences(axes,specs):
        for axis,(key,title,unit) in zip(axes,specs):
            for y,scale in enumerate(SCALES):
                rows = [r for r in pairs if r["scale"]==scale]
                for j,r in enumerate(rows):
                    axis.scatter(r[f"delta_{key}"],y+(j-3.5)*.055,
                                 color="#356b93" if r["origin"]=="current" else "#c35533",s=21)
            axis.axvline(0,color="#586471",lw=1)
            axis.set(yticks=range(3),yticklabels=SCALES,title=title,xlabel=f"B − A [{unit}]")
            axis.grid(axis="x",alpha=.2)

    fig,axes = plt.subplots(1,3,figsize=(13,4),layout="constrained")
    differences(axes,(("gap_pp","Best measured vs exact","pp"),("returned_gap_pp","Best returned vs exact","pp"),
                      ("Q_minus_classical_m","Best returned vs classical","m")))
    fig.suptitle("Local candidate quality | blue current, orange reallocation")
    save(fig,"03_candidate_quality.png")
    fig,axes = plt.subplots(1,3,figsize=(13,4),layout="constrained")
    differences(axes,(("D_km","Total distance","km"),("W_min","Total loading wait","min"),("I_dual_pp","Dual improvement vs B reference","pp")))
    fig.suptitle("Completed delivery plans | blue current, orange reallocation")
    save(fig,"04_delivery_plans.png")


if __name__=="__main__":
    analyze()
