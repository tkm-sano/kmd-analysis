#!/usr/bin/env python3
"""Registered grouped experimental entry; operational commands require a verified Freeze."""
import argparse
from collections import Counter
import csv
import fcntl
import json
from pathlib import Path
import sys

import run_grouped_loading_v2 as pilot
from kmd_toc.iterative_d3_ops import resources
from kmd_toc.iterative_v3.io import dump,read,sha,verify_pins
from kmd_toc.iterative_v3_study.analysis import summarize

ENTRY=Path(__file__).resolve()
SOLVERS=pilot.METHODS[1:]


def load_registration(out):
    path=out/"MANIFEST.json"
    if not path.is_file() or not (out/"FREEZE_RECORD.json").is_file():
        raise ValueError("NO_APPROVED_GROUPED_FORMAL_REGISTRATION")
    m,freeze=read(path),read(out/"FREEZE_RECORD.json")
    if (m["stage"]!="formal" or not m["formal_activation"] or
            freeze["status"]!="GO" or freeze["manifest_sha256"]!=sha(path)):
        raise ValueError("GROUPED_FORMAL_FREEZE_BINDING")
    if Counter(c["scale"] for c in m["cases"]) != {"S1":30,"S2":30,"S3":30}:
        raise ValueError("GROUPED_FORMAL_J_MISMATCH")
    if len({c["trial_id"] for c in m["cases"]})!=90 or not all(c["context"]["stage"]=="formal" for c in m["cases"]):
        raise ValueError("GROUPED_TRIAL_ID_OR_CONTEXT")
    verify_pins(m["code_hashes"])
    if any(sha(p)!=h for p,h in m["input_hashes"].items()):
        raise ValueError("GROUPED_INPUT_HASH_FAILURE")
    for scale,fixed in m["fixed_initials"].items():
        at=out/scale/"B/plan.json"
        if sha(at)!=fixed["plan_sha256"]:raise ValueError("GROUPED_FIXED_B_MISMATCH")
    return m


def execution_preflight(out):
    from prepare_grouped_formal_v2 import environment
    m=load_registration(out)
    if sha(out/"SEEDS.csv")!=m["seed_table"]["sha256"]:
        raise ValueError("GROUPED_FORMAL_SEED_CHECKSUM")
    for role in ("classical","branch"):
        if environment(m["configuration"][role+"_python"])!=m["environment"][role]:
            raise ValueError("GROUPED_FORMAL_RUNTIME_CHANGED:"+role)
    return m,resources.budget(pilot.POLICY)


def location(out,case,method):
    return out/"trials"/case["trial_id"]/method


def completion(path, method, base, branch=None):
    """Read a completed publication, or detect a receipt without its payload."""
    result_path, plan_path = path/"RESULT.json", path/"plan.json"
    if not result_path.exists():
        return None
    try:
        receipt, plan = read(result_path), read(plan_path)
        if receipt["status"] != "COMPLETE":
            raise ValueError("RECEIPT_STATUS")
        if branch is not None:
            if (receipt["branch"], receipt["condition"], receipt["metrics"]["physical_hash"]) != (
                    branch, method, plan["physical_hash"]):
                raise ValueError("BRANCH_RECEIPT_PLAN_MISMATCH")
        elif method == "C_Idual":
            if (receipt["initial_hash"] != base["physical_hash"] or
                    plan not in (base, read(path/"CP_CANDIDATE.json"))):
                raise ValueError("C_RECEIPT_PLAN_MISMATCH")
        else:
            branches = [completion(path/f"branch_{i}", method, base, i) for i in range(4)]
            if any(b is None for b in branches):
                raise ValueError("D_BRANCH_PUBLICATION_MISSING")
            if receipt["branches"] != [b[0] for b in branches]:
                raise ValueError("D_BRANCH_RECEIPTS_MISMATCH")
            expected, chosen = pilot.selected(path, method, base)
            if receipt["chosen_branch"] != chosen or plan != expected:
                raise ValueError("D_WINNING_BRANCH_MISMATCH")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"INVALID_GROUPED_PUBLICATION:{path}:{error}") from error
    return receipt, plan


def display_statistics(report, denominators):
    """Convert display values from the same native eligible trial sets."""
    rows=[]
    rename={"D_km":"D_km_per_parcel","W_total_min":"W_min_per_configured_vehicle_day",
            "delta_D_km":"delta_D_km_per_parcel","delta_W_min":"delta_W_min_per_configured_vehicle_day"}
    for key in ("method_statistics","paired_statistics"):
        for r in report[key]:
            v=dict(r)
            if r["metric"] in rename:
                v["metric"]=rename[r["metric"]]
                parcels,fleet=denominators[r["scale"]]
                divisor=parcels if "D" in r["metric"] else fleet
                for field in ("mean","median","SD","MCSE","Q1","Q3","IQR","min","max","whisker_low","whisker_high"):
                    if v.get(field) is not None:v[field]/=divisor
                v["outliers"]=[x/divisor for x in v["outliers"]]
            rows.append(dict(series_kind=key) | v)
    return rows


def distribution_figures(dest, report, observed, denominators):
    if not any(x["primary_trial_ids"] or x["control_trial_ids"] for x in report["cohorts"]):return []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from statistics import mean,stdev
    source={r["trial_id"]:r for r in observed}
    files=[]
    for cohort in report["cohorts"]:
        scale=cohort["scale"]
        for key,methods in (("primary",("B","C_Idual","D_quantum")),("control",("D_classical","D_quantum"))):
            members=cohort[key+"_trial_ids"]
            if not members:continue
            plans={m:[source[t]["baseline_metrics"] if m=="B" else source[t]["methods"][m]["metrics"]
                      for t in members] for m in methods}
            for mode in ("boxplot","mean_sample_sd","paired_differences"):
                fig,axes=plt.subplots(1,2,figsize=(10,4),layout="constrained")
                for ax,metric,divisor,label in zip(axes,("L_km","W_total_min"),denominators[scale],("km/parcel","min/vehicle-day")):
                    values={m:[r[metric]/divisor for r in plans[m]] for m in methods}
                    if mode=="paired_differences":
                        ax.axhline(0,color="#8996a0")
                        for m in methods[1:]:
                            ax.scatter(range(1,len(members)+1),[b-a for a,b in zip(values[methods[0]],values[m])],label=f"{methods[0]} → {m}")
                        if key=="primary":
                            ax.scatter(range(1,len(members)+1),[b-a for a,b in zip(values["C_Idual"],values["D_quantum"])],
                                       marker="+",label="C_Idual → D_quantum")
                        ax.legend();ax.set_xlabel("Paired trial index")
                    else:
                        for i,m in enumerate(methods,1):
                            v=values[m]
                            if m=="B":ax.axhline(v[0],color="#255467",linestyle=":")
                            elif mode=="boxplot" and len(v)>1:ax.boxplot(v,positions=[i],manage_ticks=False)
                            else:ax.errorbar(i,mean(v),yerr=stdev(v) if len(v)>1 else None,fmt="o")
                        ax.set_xticks(range(1,len(methods)+1),methods,rotation=15)
                    ax.set_ylabel(label)
                fig.suptitle(f"{scale}  {key}  n={len(members)}  {mode}")
                name=f"{scale}_{key}_{mode}.svg"
                fig.savefig(dest/name);plt.close(fig)
                files.append(dict(file=name,scale=scale,comparison=key,trial_ids=members,sha256=sha(dest/name)))
    return files


def execute(out,resume):
    m,_=execution_preflight(out)
    with resources.acquire(out,sha(out/"MANIFEST.json"),pilot.POLICY,m["version"],
                           "formal-resume" if resume else "formal-run") as lease:
        with (out/"EXECUTION.lock").open("a") as file:
            fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
            started=out/"EXECUTION_STARTED.json"
            if resume!=started.is_file():
                raise ValueError("MATCH_RUN_OR_RESUME_TO_FORMAL_STATE")
            if not resume:dump(started,{"run_id":lease.info["run_id"]})
            for case in m["cases"]:
                base=read(out/case["scale"]/"B/plan.json")
                for method in SOLVERS:
                    path=location(out,case,method)
                    if completion(path,method,base):continue
                    path.mkdir(parents=True,exist_ok=True)
                    branches=range(4) if method.startswith("D_") else (None,)
                    jobs=[]
                    for b in branches:
                        target=path if b is None else path/f"branch_{b}"
                        target.mkdir(exist_ok=True)
                        if completion(target,method,base,b):continue
                        job=target/"JOB.json"
                        spec=dict(trial=case["trial_id"],method=method,branch=b,output=str(target),cpu=b or 0)
                        if job.exists() and read(job)!=spec:raise ValueError("FORMAL_JOB_MISMATCH")
                        if not job.exists():dump(job,spec)
                        jobs.append(dict(path=job,action="_branch" if b is not None else "_classical"))
                    if jobs:
                        codes,alarm=resources.supervise(lease,ENTRY,jobs,path,m["configuration"])
                        if any(codes) or alarm:
                            raise RuntimeError(f"GROUPED_FORMAL_WORKER:{case['trial_id']}:{method}:{codes}:{alarm}")
                    if method.startswith("D_"):
                        for i in range(4):
                            if not completion(path/f"branch_{i}",method,base,i):
                                raise ValueError("D_BRANCH_PUBLICATION_MISSING")
                        plan,b=pilot.selected(path,method,base)
                        pilot.publish(path,plan,dict(status="COMPLETE",chosen_branch=b,
                            branches=[read(path/f"branch_{i}"/"RESULT.json") for i in range(4)]))
                    if not completion(path,method,base):
                        raise ValueError("METHOD_PUBLICATION_MISSING")
            if not (out/"COMPLETE.json").exists():dump(out/"COMPLETE.json",{"cases":90,"status":"COMPLETE"})
            return {"state":"COMPLETE"}


def aggregate(out,dest):
    """Feed only verified fixed-B/paired outcome records to the retained statistics."""
    from audit_grouped_loading_v2 import independently_build,recheck
    m=load_registration(out)
    p_by_scale={}
    exported=[]
    states=[]
    for case in m["cases"]:
        scale=case["scale"]
        if scale not in p_by_scale:
            p_by_scale[scale]=pilot.load_problem(case["input"],m["configuration"]["rest_options"])
        p=p_by_scale[scale]
        duty=pilot.load_policy()|{"loading_s":900}
        berths={b.berth_id:(b.opening_s,b.closing_s) for b in p.berths}
        base=read(out/scale/"B/plan.json")
        row=dict(scale=scale,trial_id=case["trial_id"],baseline_metrics=base,methods={})
        for method in SOLVERS:
            path=location(out,case,method)
            status="MISSING_OR_PENDING" if (out/"EXECUTION_STARTED.json").exists() else "NOT_STARTED"
            plan=None
            try:
                saved=completion(path,method,base)
                if saved:
                    _,candidate=saved
                    recheck.recheck(candidate,independently_build(p,candidate),berths,duty,p.rest_options,p.depot.depot_id)
                    plan=candidate
                    status="NORMAL_INITIAL_RETAINED" if plan["physical_hash"]==base["physical_hash"] else "NORMAL_CHANGED"
                elif (path/"plan.json").exists():
                    status="INCOMPLETE_PUBLICATION"
            except (OSError, ValueError, KeyError, TypeError) as error:
                status="INVALID_PLAN:"+str(error)
            row["methods"][method]=dict(status=status,eligible=plan is not None,metrics=plan,
                D_km=plan["L_km"] if plan else None,W_total_min=plan["W_total_min"] if plan else None,
                I_dual_pi0_percent=pilot.delta(plan,base)["I_dual_percent"] if plan else None,I_dual_C_posthoc_percent=None)
            states.append(dict(trial_id=case["trial_id"],scale=scale,method=method,status=status,eligible=plan is not None))
        classical=row["methods"]["C_Idual"]["metrics"]
        for method in ("D_classical","D_quantum"):
            a=row["methods"][method]
            if a["metrics"] and classical:a["I_dual_C_posthoc_percent"]=pilot.delta(a["metrics"],classical)["I_dual_percent"]
        exported.append(row)
    output=summarize(exported)
    denominators={scale:(sum(s.demand for s in p.stops),len(p.vehicles)) for scale,p in p_by_scale.items()}
    dest.mkdir(parents=True,exist_ok=False)
    dump(dest/"NATIVE_DESCRIPTIVE.json",output)
    dump(dest/"DISPLAY_STATISTICS.json",display_statistics(output,denominators))
    dump(dest/"OBSERVATIONS.json",exported)
    dump(dest/"FIGURE_INDEX.json",distribution_figures(dest,output,exported,denominators))
    with (dest/"STATUS.csv").open("x",newline="",encoding="utf-8-sig") as file:
        w=csv.DictWriter(file,fieldnames=list(states[0]))
        w.writeheader();w.writerows(states)
    return {"state":"AGGREGATED","normal":sum(r["eligible"] for r in states),"rows":len(states)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("preflight","run","resume","aggregate","_guard","_branch","_classical"))
    parser.add_argument("--output",type=lambda x:Path(x).resolve())
    parser.add_argument("--job",type=lambda x:Path(x).resolve())
    parser.add_argument("--intent",type=Path)
    parser.add_argument("--analysis",type=Path)
    parser.add_argument("--execute",action="store_true")
    a=parser.parse_args()
    if a.action=="_guard":return resources.guard(a.intent)
    if a.action in ("_branch","_classical"):
        pilot.load_manifest=load_registration
        return pilot.worker(a.job,a.action)
    if a.output is None:parser.error("--output is required")
    if a.action=="preflight":
        try:
            _,visible=execution_preflight(a.output)
            ans={"state":"EXPERIMENT_READY","visible_resources":visible,"workers_submitted":0}
        except (OSError,ValueError,resources.Unavailable) as error:
            print(json.dumps({"state":"HOLD","reason":str(error),"workers_submitted":0}))
            return 2
    elif a.action=="aggregate":
        if a.analysis is None:parser.error("--analysis is required")
        ans=aggregate(a.output,a.analysis)
    else:
        if not a.execute:parser.error("--execute is required")
        ans=execute(a.output,a.action=="resume")
    print(json.dumps(ans,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
