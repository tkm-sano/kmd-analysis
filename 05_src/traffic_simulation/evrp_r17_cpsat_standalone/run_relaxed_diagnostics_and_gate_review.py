#!/usr/bin/env python3
"""R17-only causal diagnostics for T04-T07 and formulation gate review."""
from __future__ import annotations
import argparse, hashlib, json, platform, time
from pathlib import Path
from ortools.sat.python import cp_model
import ortools

BATTERY=147600000; MIN_E=29520000; POWER=70; MAX_D=1800000; C=11; HORIZON=10000000
CONFIG={"ortools_version":"9.12.4544","random_seed":20260909,"num_search_workers":1,"max_time_in_seconds":2.0,"log_search_progress":False}

def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def build(route, energies, *, initial=BATTERY, duration_fix=None, duration_domain_max=MAX_D,
          duration_cap=True, energy_domain_max=BATTERY, capacity_cap=True, minimum_cap=True,
          consecutive_cap=True):
    P=len(route); m=cp_model.CpModel(); duration_fix=duration_fix
    charger=[m.NewBoolVar(f"charger_{p}") for p in range(P)]
    for p,n in enumerate(route): m.Add(charger[p]==(n=="H"))
    used=[m.NewBoolVar(f"slot_used_{c}") for c in range(C)]
    pos=[m.NewIntVar(0,P-1,f"slot_position_{c}") for c in range(C)]
    dur=[m.NewIntVar(0,duration_domain_max,f"slot_duration_{c}") for c in range(C)]
    add=[m.NewIntVar(0,POWER*duration_domain_max,f"slot_energy_{c}") for c in range(C)]
    at={(c,p):m.NewBoolVar(f"slot_at_{c}_{p}") for c in range(C) for p in range(P)}
    for c in range(C):
        m.Add(sum(at[c,p] for p in range(P))==used[c]); m.Add(pos[c]==0).OnlyEnforceIf(used[c].Not())
        m.Add(dur[c]>=1).OnlyEnforceIf(used[c]); m.Add(dur[c]==0).OnlyEnforceIf(used[c].Not()); m.Add(add[c]==POWER*dur[c])
        if duration_fix is not None and c==0: m.Add(dur[c]==duration_fix)
        for p in range(P): m.Add(pos[c]==p).OnlyEnforceIf(at[c,p])
    for c in range(C-1):
        m.AddImplication(used[c+1],used[c]); m.Add(pos[c+1]>pos[c]).OnlyEnforceIf(used[c+1])
    for p in range(P):
        m.Add(sum(at[c,p] for c in range(C))==charger[p])
        if p+1<P and consecutive_cap: m.Add(charger[p]+charger[p+1]<=1)
    e_upper=energy_domain_max
    arr=[m.NewIntVar(0,HORIZON,f"arrival_{p}") for p in range(P)]; dep=[m.NewIntVar(0,HORIZON,f"departure_{p}") for p in range(P)]
    ea=[m.NewIntVar(0,e_upper,f"energy_arrival_{p}") for p in range(P)]; ed=[m.NewIntVar(0,e_upper,f"energy_departure_{p}") for p in range(P)]
    cp=[m.NewIntVar(0,duration_domain_max,f"charge_at_{p}") for p in range(P)]; ce=[m.NewIntVar(0,POWER*duration_domain_max,f"charge_energy_at_{p}") for p in range(P)]
    m.Add(arr[0]==0); m.Add(ea[0]==initial)
    for p,n in enumerate(route):
        service=0 if n in ("D","H") else 100; m.Add(dep[p]==arr[p]+service+cp[p]); m.Add(ed[p]==ea[p]+ce[p])
        if minimum_cap: m.Add(ea[p]>=MIN_E); m.Add(ed[p]>=MIN_E)
        if capacity_cap: m.Add(ed[p]<=BATTERY)
        if n!="H": m.Add(cp[p]==0); m.Add(ce[p]==0)
        else:
            for c in range(C): m.Add(cp[p]==dur[c]).OnlyEnforceIf(at[c,p]); m.Add(ce[p]==add[c]).OnlyEnforceIf(at[c,p])
    for p,e in enumerate(energies): m.Add(arr[p+1]==dep[p]+1000); m.Add(ea[p+1]==ed[p]-e)
    m.Minimize(sum(dur))
    return m

def solve(model):
    s=cp_model.CpSolver(); s.parameters.random_seed=CONFIG["random_seed"]; s.parameters.num_search_workers=1; s.parameters.max_time_in_seconds=CONFIG["max_time_in_seconds"]; s.parameters.log_search_progress=False
    t=time.monotonic(); code=s.Solve(model); return {"status":s.StatusName(code),"runtime_seconds":time.monotonic()-t,"objective":s.ObjectiveValue() if s.StatusName(code) in ("OPTIMAL","FEASIBLE") else None}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",required=True); a=ap.parse_args(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=False)
    cases=[
      {"id":"T04_consecutive_charger","target":"consecutive charger prohibition","original":{"route":["D","H","H","D"],"energies":[1000000,1000000,0],"consecutive_cap":True},"control":{"route":["D","H","H","D"],"energies":[1000000,1000000,0],"consecutive_cap":False},"changed_domains":[]},
      {"id":"T05_duration_over_cap","target":"charging duration upper bound","original":{"route":["D","H","D"],"energies":[0,0],"duration_fix":1800001,"duration_domain_max":MAX_D,"duration_cap":True},"control":{"route":["D","H","D"],"energies":[0,0],"duration_fix":1800001,"duration_domain_max":MAX_D+1,"duration_cap":False},"changed_domains":["slot_duration domain upper: 1800000 -> 1800001","slot_energy domain derived from duration domain"]},
      {"id":"T06_capacity_overflow","target":"post-charge battery upper bound","original":{"route":["D","H","D"],"energies":[0,0],"initial":147000100,"duration_fix":10000,"energy_domain_max":BATTERY,"capacity_cap":True},"control":{"route":["D","H","D"],"energies":[0,0],"initial":147000100,"duration_fix":10000,"energy_domain_max":BATTERY+POWER*10000,"capacity_cap":False},"changed_domains":["energy arrival/departure upper: 147600000 -> 148300100"]},
      {"id":"T07_minimum_energy","target":"minimum energy lower bound","original":{"route":["D","C_A","D"],"energies":[480001,0],"initial":30000000,"minimum_cap":True},"control":{"route":["D","C_A","D"],"energies":[480001,0],"initial":30000000,"minimum_cap":False},"changed_domains":["energy lower domain remains 0 in both; only explicit minimum-energy inequalities are removed"]}
    ]
    results=[]
    for c in cases:
        original=solve(build(**c["original"])); control=solve(build(**c["control"])); ok=original["status"]=="INFEASIBLE" and control["status"] in ("FEASIBLE","OPTIMAL")
        r={"id":c["id"],"target_constraint":c["target"],"original":{"expected":"INFEASIBLE","actual":original},"control":{"expected":"FEASIBLE_OR_OPTIMAL","actual":control,"relaxed_target_only":True,"unchanged_constraints":"all common route/slot/time/energy/charging constraints except target","changed_variable_domains":c["changed_domains"]},"causal_confirmation":ok}
        results.append(r); write(out/(c["id"]+"_relaxed_diagnostic.json"),r)
    checks={r["id"]:r["causal_confirmation"] for r in results}; aggregate={"status":"PASS" if all(checks.values()) else "FAIL","tests":results,"checks":checks,"config":CONFIG,"solver_scope":"diagnostic controls only; R18 production not executed"}; write(out/"relaxed_diagnostics_aggregate.json",aggregate)
    write(out/"manifest.json",{"run_id":out.name,"status":aggregate["status"],"r18_executed":False,"r19_executed":False,"software":{"python":platform.python_version(),"ortools":ortools.__version__},"files":{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return 0 if aggregate["status"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
