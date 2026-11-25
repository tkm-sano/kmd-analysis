#!/usr/bin/env python3
"""Recompute grouped pilot schedules, accounting and comparisons from saved files."""
import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction as F
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from kmd_toc.duty_break_v1.policy import load_policy
from kmd_toc.grouped_loading_v2 import model, recheck
from kmd_toc.iterative_v3.io import decode_routes,digest_payload,read,sha,load_problem,dump,verify_pins
from kmd_toc.iterative_v3_study.analysis import delta

METHODS=("B","C_Idual","D_classical","D_quantum")
FIELDS=("L_km","D_km_per_parcel","W_total_min","W_total_s","W_min_per_configured_vehicle_day","W1_s","W2_s",
        "before_reception_total_s","opening_wait_s","berth_wait_s","active_vehicles","unused_vehicles",
        "configured_vehicles","final_return_s","calls_s","group_gaps_s","parcels","active_trips")


def independently_build(p, plan):
    trips=plan["trips"]
    actual=Counter(v["stop_id"] for t in trips for v in t["visits"])
    require=set(actual)=={s.stop_id for s in p.stops} and all(n==1 for n in actual.values())
    if not require:raise ValueError("INDEPENDENT_DELIVERY_COVERAGE")
    od={v:i for i,v in enumerate(p.od.ids)}
    jobs={}
    for t in trips:
        customers=tuple(v["stop_id"] for v in t["visits"])
        path=(p.depot.depot_id,*customers,p.depot.depot_id)
        if not 1<=len(customers)<=60:raise ValueError("INDEPENDENT_CAPACITY")
        seconds=[]; metres=F(0)
        for a,b in zip(path,path[1:]):
            metres+=F(str(float(p.od.distance_m[od[a],od[b]])))
            seconds.append(math.ceil(float(p.od.duration_s[od[a],od[b]])))
        jobs[t["vehicle_id"],t["trip_no"]]=model.Job(customers,len(customers),metres/1000,tuple(seconds))
    return jobs


def verify_d(path,method,base,cfg):
    history=[]
    chosen=read(path/"RESULT.json")["chosen_branch"]
    branches=[]
    for i in range(4):
        branch=path/f"branch_{i}"
        b=read(branch/"RESULT.json")
        plan=read(branch/"plan.json")
        if b["status"]!="COMPLETE" or not 1<=b["completed"]<=10 or b["used"]>70 or b["calls"]>10:
            raise ValueError("BRANCH_BUDGET_OR_STATUS")
        branches.append(b)
        old_used=0; expected=base["physical_hash"]
        for iteration in sorted(branch.glob("iteration_*/COMMIT.json")):
            c=read(iteration)
            if c["input_hash"]!=expected:raise ValueError("CANDIDATE_CHAIN")
            expected=c["state_hash"]
            n_complete=0
            for row in c["candidate_receipts"]:
                event=dict(method=method,branch=i,selected_branch=(i==chosen),iteration=c["iteration"],kind=row["kind"])
                if row["kind"]=="local_search":
                    if method=="D_quantum" and row["receipt"]["total_shots_actual"]<=0:
                        raise ValueError("MISSING_QAOA_SHOTS")
                    continue
                n_complete+=1
                parent,m=row["parent"],row["metrics"]
                record=event | dict(candidate=row["id"],status=row["status"],move_id=row["move_id"],
                           adopted=row["id"]==c["adopted"], parent_calls=parent["calls_s"],calls=row["calls_s"],
                           chosen_as_final=bool(m) and m["physical_hash"]==plan["physical_hash"],
                           matching_parent_available=row.get("matching_parent_available",True))
                if m and record["matching_parent_available"]:
                    record.update(delta_D_km=float(F(m["D_exact"])-F(parent["D_exact"])),
                                  delta_W_min=float(F(m["W_exact"])-F(parent["W_exact"])),
                                  delta_before_reception_s=m["before_reception_total_s"]-parent["before_reception_total_s"],
                                  delta_final_return_s=m["final_return_s"]-parent["final_return_s"],
                                  delta_W1_s=m["W1_s"]-parent["W1_s"],delta_W2_s=m["W2_s"]-parent["W2_s"])
                history.append(record)
            if c["used"]-old_used!=n_complete or n_complete>7:raise ValueError("COMPLETION_COUNTER")
            old_used=c["used"]
        if old_used!=b["used"]:raise ValueError("FINAL_COMPLETION_COUNTER")
    if not any(h["kind"]=="reception_time" and h["parent_calls"]!=h["calls"] for h in history):
        raise ValueError("TIMING_CANDIDATES_NOT_REACHED")
    return history,dict(wall_s=sum(b["wall_s"] for b in branches), max_branch_wall_s=max(b["wall_s"] for b in branches),
        cpu_s=sum(b["cpu_s"] for b in branches),rss_MiB=max(b["rss_MiB"] for b in branches),
        used=sum(b["used"] for b in branches),shots=sum(b["shots"] for b in branches),calls=sum(b["calls"] for b in branches),
        stop_reason=";".join(b["stop_reason"] for b in branches),operation_counts={kind:dict(
            generated=sum(r["kind"]==kind for r in history),feasible=sum(r["kind"]==kind and r["status"]=="FEASIBLE" for r in history),
            adopted=sum(r["kind"]==kind and r["adopted"] for r in history)) for kind in sorted({r["kind"] for r in history})})


def write_csv(path,records):
    if not records:return
    with path.open("x",encoding="utf-8-sig",newline="") as f:
        fieldnames=list(dict.fromkeys(k for row in records for k in row))
        writer=csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def audit(pilot,out,scale_filter=None):
    m=read(pilot/"MANIFEST.json")
    verify_pins(m["code_hashes"])
    duty=load_policy()|{"loading_s":m["grouped_conditions"]["loading_s"]}
    results=[]; events=[]; pairs=[]; trip_rows=[]
    sources={}
    cases=[c for c in m["cases"] if scale_filter is None or c["scale"]==scale_filter]
    for case in cases:
        scale=case["scale"]
        p=load_problem(case["input"],m["configuration"]["rest_options"])
        berths={b.berth_id:(b.opening_s,b.closing_s) for b in p.berths}
        available={}
        for method in METHODS:
            path=pilot/scale/method
            plan_path=path/"plan.json"; result_path=path/"RESULT.json"
            if not (plan_path.exists() and result_path.exists()):
                results.append(dict(scale=scale,trial_id=case["trial_id"],method=method,status="PENDING_OR_FAILED"))
                continue
            receipt=read(result_path); plan=read(plan_path)
            jobs=independently_build(p,plan)
            recheck.recheck(plan,jobs,berths,duty,p.rest_options,p.depot.depot_id)
            if plan["routes"]!=[dict(vehicle=t["vehicle_id"],trip=t["trip_no"],customers=[v["stop_id"] for v in t["visits"]])
                                for t in plan["trips"]]:
                raise ValueError("ROUTE_LOG_AND_OPERATION_PLAN_MISMATCH")
            regeneration=pilot/f"{scale}_B.json"
            if method=="B" and regeneration.is_file() and read(regeneration)!=plan:
                raise ValueError("INDEPENDENT_CW_REGENERATION_MISMATCH")
            available[method]=plan
            resources={k:receipt[k] for k in ("wall_s","cpu_s","rss_MiB","stop") if k in receipt}
            if method.startswith("D_"):
                trace,resources=verify_d(path,method,available["B"],m["configuration"])
                events.extend(dict(scale=scale,trial_id=case["trial_id"]) | r for r in trace)
            if method=="C_Idual":
                cp=receipt["cp"]
                attempted=[r["group_calls_s"] for r in cp["stages"] if "group_calls_s" in r]
                if receipt["initial_hash"]!=available["B"]["physical_hash"] or not attempted:
                    raise ValueError("C_INTEGRATION_OR_BASE")
                resources.update(cp_call_vectors=attempted,routing_checks=receipt["routing"]["checks"],
                                 cp_conflicts=sum(r["conflicts"] for r in cp["stages"]))
            results.append(dict(scale=scale,trial_id=case["trial_id"],method=method,status="PASS",source_plan=str(plan_path),
                plan_sha256=sha(plan_path), **{k:plan[k] for k in FIELDS}) | resources)
            trip_rows.extend(dict(scale=scale,trial_id=case["trial_id"],method=method) |
                            {k:v for k,v in t.items() if k!="visits"} for t in plan["trips"])
            for f in (plan_path,result_path):sources[str(f)]=sha(f)
        for name,a,b in (("B_vs_C","B","C_Idual"),("B_vs_Dq","B","D_quantum"),
            ("C_vs_Dq","C_Idual","D_quantum"),("Dclassic_vs_Dq","D_classical","D_quantum")):
            if a not in available or b not in available:continue
            old,new=available[a],available[b]
            pairs.append(dict(scale=scale,trial_id=case["trial_id"],comparison=name,baseline=a,candidate=b,
                              delta_before_reception_s=new["before_reception_total_s"]-old["before_reception_total_s"],
                              delta_final_return_s=new["final_return_s"]-old["final_return_s"]) | delta(new,old))
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/"RESULTS.csv",results);write_csv(out/"PAIRED.csv",pairs)
    write_csv(out/"CANDIDATE_OPERATIONS.csv",events);write_csv(out/"TRIPS.csv",trip_rows)
    result=dict(validated_plans=sum(r["status"]=="PASS" for r in results),planned_plans=4*len(cases),validated_trips=len(trip_rows),
                paired_comparisons=len(pairs),source_sha256=sources,formal_workers=0)
    dump(out/"RECHECK.json",result)
    return result


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pilot",type=Path);cli.add_argument("output",type=Path)
    cli.add_argument("--scale",choices=("S1","S2","S3"))
    a=cli.parse_args()
    r=audit(a.pilot,a.output,a.scale)
    print(json.dumps({k:v for k,v in r.items() if k!="source_sha256"}))
