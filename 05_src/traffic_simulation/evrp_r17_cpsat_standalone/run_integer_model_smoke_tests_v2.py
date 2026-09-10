#!/usr/bin/env python3
"""R17-only CP-SAT integer smoke tests; never invokes the production R18 instance."""
from __future__ import annotations
import argparse, hashlib, json, platform, time
from pathlib import Path
from ortools.sat.python import cp_model
import ortools

BATTERY=147600000; MIN_E=29520000; POWER=70; MAX_D=1800000; C=11; HORIZON=10000000
CONFIG={"ortools_version":"9.12.4544","random_seed":20260909,"num_search_workers":1,"max_time_in_seconds":2.0,"log_search_progress":False}

def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def build(route, energies, initial=BATTERY, duration_fixes=None, duration_cap=True, capacity_cap=True, minimum_cap=True, force_unused=()):
    duration_fixes=duration_fixes or {}; force_unused=set(force_unused); P=len(route); m=cp_model.CpModel()
    active=[m.NewBoolVar(f"active_{p}") for p in range(P)]
    charger=[m.NewBoolVar(f"charger_{p}") for p in range(P)]
    for p,n in enumerate(route): m.Add(active[p]==1); m.Add(charger[p]==(n=="H"))
    used=[m.NewBoolVar(f"slot_used_{c}") for c in range(C)]
    pos=[m.NewIntVar(0,P-1,f"slot_position_{c}") for c in range(C)]
    dur=[m.NewIntVar(0,MAX_D if duration_cap else MAX_D+1,f"slot_duration_{c}") for c in range(C)]
    added=[m.NewIntVar(0,POWER*(MAX_D+1),f"slot_energy_{c}") for c in range(C)]
    at={(c,p):m.NewBoolVar(f"slot_at_{c}_{p}") for c in range(C) for p in range(P)}
    for c in range(C):
        m.Add(sum(at[c,p] for p in range(P))==used[c]); m.Add(pos[c]==0).OnlyEnforceIf(used[c].Not())
        m.Add(dur[c]>=1).OnlyEnforceIf(used[c]); m.Add(dur[c]==0).OnlyEnforceIf(used[c].Not()); m.Add(added[c]==POWER*dur[c])
        if c in duration_fixes: m.Add(dur[c]==duration_fixes[c])
        if c in force_unused: m.Add(used[c]==0)
        for p in range(P): m.Add(pos[c]==p).OnlyEnforceIf(at[c,p])
    for c in range(C-1):
        m.AddImplication(used[c+1],used[c]); m.Add(pos[c+1]>pos[c]).OnlyEnforceIf(used[c+1])
    for p in range(P):
        m.Add(sum(at[c,p] for c in range(C))==charger[p])
        if p+1<P: m.Add(charger[p]+charger[p+1]<=1)
    arr=[m.NewIntVar(0,HORIZON,f"arrival_{p}") for p in range(P)]; dep=[m.NewIntVar(0,HORIZON,f"departure_{p}") for p in range(P)]
    earr=[m.NewIntVar(0,BATTERY,f"energy_arrival_{p}") for p in range(P)]; edep=[m.NewIntVar(0,BATTERY if capacity_cap else BATTERY+POWER*(MAX_D+1),f"energy_departure_{p}") for p in range(P)]
    cp=[m.NewIntVar(0,MAX_D if duration_cap else MAX_D+1,f"charge_at_{p}") for p in range(P)]; ce=[m.NewIntVar(0,POWER*(MAX_D+1),f"charge_energy_at_{p}") for p in range(P)]
    m.Add(arr[0]==0); m.Add(earr[0]==initial)
    for p,n in enumerate(route):
        service=0 if n in ("D","H") else 100; m.Add(dep[p]==arr[p]+service+cp[p]); m.Add(edep[p]==earr[p]+ce[p])
        if minimum_cap: m.Add(earr[p]>=MIN_E); m.Add(edep[p]>=MIN_E)
        if capacity_cap: m.Add(edep[p]<=BATTERY)
        if n!="H": m.Add(cp[p]==0); m.Add(ce[p]==0)
        else:
            for c in range(C): m.Add(cp[p]==dur[c]).OnlyEnforceIf(at[c,p]); m.Add(ce[p]==added[c]).OnlyEnforceIf(at[c,p])
    for p,e in enumerate(energies): m.Add(arr[p+1]==dep[p]+1000); m.Add(earr[p+1]==edep[p]-e)
    m.Minimize(sum(dur))
    return m,used,pos,dur,added,arr,dep,earr,edep

def solve(case):
    args=case["model"]; obj=build(**args); m,used,pos,dur,added,arr,dep,earr,edep=obj; s=cp_model.CpSolver()
    s.parameters.random_seed=CONFIG["random_seed"]; s.parameters.num_search_workers=1; s.parameters.max_time_in_seconds=CONFIG["max_time_in_seconds"]; s.parameters.log_search_progress=False
    t=time.monotonic(); code=s.Solve(m); out={"status":s.StatusName(code),"runtime_seconds":time.monotonic()-t,"route":args["route"],"objective":None}
    if out["status"] in ("OPTIMAL","FEASIBLE"):
        out.update({"objective":s.ObjectiveValue(),"slot_used":[s.Value(x) for x in used],"slot_position":[s.Value(x) for x in pos],"slot_duration_ms":[s.Value(x) for x in dur],"slot_energy_j":[s.Value(x) for x in added],"arrival_ms":[s.Value(x) for x in arr],"departure_ms":[s.Value(x) for x in dep],"energy_arrival_j":[s.Value(x) for x in earr],"energy_departure_j":[s.Value(x) for x in edep]})
        u=out["slot_used"]; p=out["slot_position"]; d=out["slot_duration_ms"]; e=out["slot_energy_j"]
        checks={"prefix":all(not u[c+1] or u[c] for c in range(C-1)),"order":all(not u[c+1] or p[c+1]>p[c] for c in range(C-1)),"used_positive":all(not u[c] or 0<d[c]<=MAX_D for c in range(C)),"unused_zero":all(u[c] or (d[c]==0 and e[c]==0) for c in range(C)),"exact_charge":all(e[c]==POWER*d[c] for c in range(C)),"energy_bounds":all(MIN_E<=x<=BATTERY for x in out["energy_arrival_j"]+out["energy_departure_j"]),"time_propagation":all(out["arrival_ms"][p+1]>=out["departure_ms"][p] for p in range(len(args["route"])-1))}
        out["validation"]={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",required=True); a=ap.parse_args(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=False)
    cases=[
      {"id":"T01_no_charger","expected":"OPTIMAL","model":{"route":["D","C_A","D"],"energies":[1000,1000]}},
      {"id":"T02_one_charger","expected":"OPTIMAL","model":{"route":["D","H","C_A","D"],"energies":[200000,200000,200000],"initial":30000000}},
      {"id":"T03_multiple_revisit","expected":"OPTIMAL","model":{"route":["D","C_A","H","C_B","H","D"],"energies":[1000000,1000000,50000000,50000000,50000000]}},
      {"id":"T04_consecutive_charger","expected":"INFEASIBLE","model":{"route":["D","H","H","D"],"energies":[0,0,0]}},
      {"id":"T05_duration_over_cap","expected":"INFEASIBLE","model":{"route":["D","H","D"],"energies":[0,0],"duration_fixes":{0:1800001}}},
      {"id":"T06_capacity_overflow","expected":"INFEASIBLE","model":{"route":["D","H","D"],"energies":[0,0],"initial":147000100,"duration_fixes":{0:10000}}},
      {"id":"T07_minimum_energy","expected":"INFEASIBLE","model":{"route":["D","C_A","D"],"energies":[480001,0],"initial":30000000}},
      {"id":"T08_unused_slot_neutrality","expected":"OPTIMAL","model":{"route":["D","H","C_A","D"],"energies":[200000,200000,200000],"initial":30000000}},
    ]
    results=[]
    for c in cases:
        r=solve(c); ok=r["status"]==c["expected"] and r.get("validation",{"status":"PASS"})["status"]=="PASS"; item={"id":c["id"],"expected":c["expected"],"actual":r,"pass":ok}
        if c["id"]=="T04_consecutive_charger": item["relaxed"]={"expected":"FEASIBLE","actual":solve({"model":{"route":["D","H","C_A","D"],"energies":[0,0,0]}})}
        if c["id"]=="T05_duration_over_cap": item["relaxed"]={"expected":"FEASIBLE","actual":solve({"model":dict(c["model"],duration_cap=False)})}
        if c["id"]=="T06_capacity_overflow": item["relaxed"]={"expected":"FEASIBLE","actual":solve({"model":dict(c["model"],capacity_cap=False)})}
        if c["id"]=="T07_minimum_energy": item["relaxed"]={"expected":"FEASIBLE","actual":solve({"model":dict(c["model"],minimum_cap=False)})}
        results.append(item); write(out/(c["id"]+".json"),item)
    repeats={}
    for c in [cases[0],cases[1],cases[2],cases[7]]:
        r1,r2=solve(c),solve(c); keys=["status","route","slot_used","slot_position","slot_duration_ms","slot_energy_j","arrival_ms","departure_ms","energy_arrival_j","energy_departure_j","objective"]
        repeats[c["id"]]={"match":all(r1.get(k)==r2.get(k) for k in keys),"run_1":r1,"run_2":r2}
    write(out/"repeated_run_comparison.json",repeats)
    aggregate={"status":"PASS" if all(x["pass"] for x in results) and all(x["match"] for x in repeats.values()) else "FAIL","tests":[{"id":x["id"],"expected":x["expected"],"actual":x["actual"]["status"],"pass":x["pass"]} for x in results],"repeated_run":{k:v["match"] for k,v in repeats.items()},"config":CONFIG,"solver_scope":"smoke tests only; R18 production not executed"}
    write(out/"aggregate_validation_report.json",aggregate); write(out/"manifest.json",{"run_id":out.name,"status":aggregate["status"],"r18_executed":False,"r19_executed":False,"software":{"python":platform.python_version(),"ortools":ortools.__version__},"files":{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}}); return 0 if aggregate["status"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
