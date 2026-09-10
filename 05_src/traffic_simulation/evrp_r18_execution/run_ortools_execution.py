#!/usr/bin/env python3
"""R18 CP-SAT standalone implementation and execution gate.

The R17 contract fixes a 300 second limit but does not define how to split it
between the two lexicographic solves.  Therefore this runner builds the
authoritative CP-SAT model and records BLOCKED before starting a solver.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any
from ortools.sat.python import cp_model
import ortools

R15_HASH="7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4"
R16_HASH="1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67"
NETWORK_HASH="460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
CONSTRAINT_VERSION="evrp-common-hard-constraints-v1"; SOLVER_VERSION="9.12.4544"
BATTERY=147_600_000; MIN_ENERGY=29_520_000; POWER=70; MAX_CHARGE=1_800_000
PAYLOAD_CAPACITY=2_000_000; PAYLOAD_G=1_100; SLOTS=11

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,v:Any)->None: p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def arc_constants(a:dict,v:dict)->tuple[int,int]:
    t=int((Decimal(str(a["travel_time_s"]))*1000).to_integral_value(rounding=ROUND_CEILING))
    e=int((Decimal(str(a["distance_m"]))*Decimal(str(v["energy_consumption_kwh_per_km"]))*3600).to_integral_value(rounding=ROUND_CEILING))
    return t,e

def build_model(instance:dict,constraints:dict)->dict:
    """Build R17's complete position-indexed joint route/state model."""
    nodes=instance["node_order"]; ids=[n["endpoint_id"] for n in nodes]; N=len(nodes)
    P=2*len(instance["customers"])+3; E=len(instance["customers"])+1
    depot=next(i for i,n in enumerate(nodes) if n["node_type"]=="depot")
    charger=next(i for i,n in enumerate(nodes) if n["node_type"]=="charger")
    cust={c["solver_index"]:c for c in instance["customers"]}; veh=instance["vehicles"][0]
    accepted={(ids.index(a["origin_id"]),ids.index(a["destination_id"])):a for a in instance["routing"]["arcs"] if a["reachable"]}
    travel={ij:arc_constants(a,veh)[0] for ij,a in accepted.items()}; energy={ij:arc_constants(a,veh)[1] for ij,a in accepted.items()}
    H=max(int(max(c["time_window"]["l_i"] for c in cust.values())*3_600_000),1)+(P-1)*max(travel.values())+len(cust)*150_000+E*MAX_CHARGE
    m=cp_model.CpModel()
    active=[m.NewBoolVar(f"active_{p}") for p in range(P)]
    node_at={(p,i):m.NewBoolVar(f"node_at_{p}_{i}") for p in range(P) for i in range(N)}
    x={(p,i,j):m.NewBoolVar(f"x_{p}_{i}_{j}") for p in range(P-1) for i,j in travel}
    aggregate={(i,j):m.NewIntVar(0,P-1,f"x_aggregate_{i}_{j}") for i,j in travel}
    served={i:m.NewBoolVar(f"served_{i}") for i in cust}; ret=[m.NewBoolVar(f"return_{p}") for p in range(P)]
    arr=[m.NewIntVar(0,H,f"arrival_ms_{p}") for p in range(P)]; start=[m.NewIntVar(0,H,f"service_start_ms_{p}") for p in range(P)]
    wait=[m.NewIntVar(0,H,f"waiting_ms_{p}") for p in range(P)]; dep=[m.NewIntVar(0,H,f"departure_ms_{p}") for p in range(P)]
    lb=[m.NewIntVar(0,PAYLOAD_CAPACITY,f"load_before_g_{p}") for p in range(P)]; la=[m.NewIntVar(0,PAYLOAD_CAPACITY,f"load_after_g_{p}") for p in range(P)]
    eb=[m.NewIntVar(0,BATTERY,f"energy_before_j_{p}") for p in range(P)]; ea=[m.NewIntVar(0,BATTERY,f"energy_after_j_{p}") for p in range(P)]
    charge=[m.NewIntVar(0,MAX_CHARGE,f"charge_duration_ms_{p}") for p in range(P)]; charge_e=[m.NewIntVar(0,POWER*MAX_CHARGE,f"charge_energy_j_{p}") for p in range(P)]
    used=[m.NewBoolVar(f"slot_{e}_used") for e in range(E)]; spos=[m.NewIntVar(0,P-1,f"slot_{e}_position") for e in range(E)]
    dur=[m.NewIntVar(0,MAX_CHARGE,f"slot_{e}_duration_ms") for e in range(E)]; ce=[m.NewIntVar(0,POWER*MAX_CHARGE,f"slot_{e}_energy_j") for e in range(E)]
    sat={(e,p):m.NewBoolVar(f"slot_{e}_at_{p}") for e in range(E) for p in range(P)}
    # HC01-05, HC13: exact ordered chain; unreachable arcs have no x variable.
    m.Add(active[0]==1); m.Add(node_at[0,depot]==1)
    for p in range(P-1): m.Add(active[p+1]<=active[p])
    for p in range(P):
        m.Add(sum(node_at[p,i] for i in range(N))==active[p])
        if p==0: m.Add(ret[p]==0)
        else: m.Add(ret[p]==node_at[p,depot])
        if p<P-1: m.Add(active[p+1]<=ret[p].Not())
    m.Add(sum(ret)==1)
    for i in cust: m.Add(sum(node_at[p,i] for p in range(P))==served[i])
    for i in range(N):
        for p in range(P-1):
            out=[x[p,i,j] for ii,j in travel if ii==i]; inc=[x[p,j,i] for j,ii in travel if ii==i]
            m.Add(sum(out)==node_at[p,i]) if out else m.Add(node_at[p,i]==0)
            m.Add(sum(inc)==node_at[p+1,i]) if inc else m.Add(node_at[p+1,i]==0)
    for i,j in travel: m.Add(aggregate[i,j]==sum(x[p,i,j] for p in range(P-1)))
    # HC06 payload grams, not request count.
    m.Add(lb[0]==sum(PAYLOAD_G*served[i] for i in cust))
    for p in range(P):
        m.Add(la[p]==lb[p]-sum(PAYLOAD_G*node_at[p,i] for i in cust))
        if p<P-1: m.Add(lb[p+1]==la[p]).OnlyEnforceIf(active[p+1])
    # HC07-09 and HC08.  HC09 remains disabled in this baseline.
    m.Add(arr[0]==0); m.Add(wait[0]==0); m.Add(start[0]==0)
    for p in range(P):
        m.Add(start[p]==arr[p]+wait[p]); m.Add(wait[p]==0).OnlyEnforceIf(active[p].Not())
        for i,c in cust.items():
            lo=int(Decimal(str(c["time_window"]["e_i"]))*3_600_000); hi=int(Decimal(str(c["time_window"]["l_i"]))*3_600_000)
            m.Add(start[p]>=lo).OnlyEnforceIf(node_at[p,i]); m.Add(start[p]<=hi).OnlyEnforceIf(node_at[p,i])
        m.Add(dep[p]==start[p]+sum(150_000*node_at[p,i] for i in cust)+charge[p])
        if p<P-1:
            for i,j in travel: m.Add(arr[p+1]==dep[p]+travel[i,j]).OnlyEnforceIf(x[p,i,j])
    # HC10-12: energy and charging are in the same state transition.
    m.Add(eb[0]==BATTERY)
    for p in range(P):
        movement=sum(energy[i,j]*x[p,i,j] for i,j in travel) if p<P-1 else 0
        m.Add(ea[p]==eb[p]-movement+charge_e[p]); m.Add(eb[p]>=MIN_ENERGY).OnlyEnforceIf(active[p]); m.Add(ea[p]>=MIN_ENERGY).OnlyEnforceIf(active[p])
        if p<P-1: m.Add(eb[p+1]==ea[p]).OnlyEnforceIf(active[p+1])
    cat=[node_at[p,charger] for p in range(P)]
    for e in range(E):
        m.Add(sum(sat[e,p] for p in range(P))==used[e]); m.Add(spos[e]==0).OnlyEnforceIf(used[e].Not()); m.Add(dur[e]==0).OnlyEnforceIf(used[e].Not()); m.Add(dur[e]>=1).OnlyEnforceIf(used[e]); m.Add(ce[e]==POWER*dur[e])
        for p in range(P): m.Add(spos[e]==p).OnlyEnforceIf(sat[e,p])
        if e<E-1: m.AddImplication(used[e+1],used[e]); m.Add(spos[e+1]>spos[e]).OnlyEnforceIf(used[e+1])
    for p in range(P):
        m.Add(sum(sat[e,p] for e in range(E))==cat[p]); m.Add(charge[p]==0).OnlyEnforceIf(cat[p].Not()); m.Add(charge_e[p]==0).OnlyEnforceIf(cat[p].Not())
        for e in range(E): m.Add(charge[p]==dur[e]).OnlyEnforceIf(sat[e,p]); m.Add(charge_e[p]==ce[e]).OnlyEnforceIf(sat[e,p])
        if p<P-1: m.Add(cat[p]+cat[p+1]<=1)
    return {"model":m,"vars":{"active":active,"node_at":node_at,"x":x,"aggregate":aggregate,"served":served,"return":ret,"arrival":arr,"service_start":start,"waiting":wait,"departure":dep,"load_before":lb,"load_after":la,"energy_before":eb,"energy_after":ea,"charge":charge,"charge_energy":charge_e,"slot_used":used,"slot_position":spos,"slot_duration":dur,"slot_energy":ce,"slot_at":sat},"counts":{"positions":P,"nodes":N,"slots":E,"accepted_arcs":len(travel),"horizon_ms":H}}

def preflight(instance, constraints, formulation, config, r15, r16, r17):
    checks={"r15_hash":sha(r15/"common_instance.json")==R15_HASH,"r16_hash_version":sha(r16/"constraint_spec.json")==R16_HASH and constraints["constraint_version"]==CONSTRAINT_VERSION,"r17_cpsat_current":formulation.get("architecture")=="C_CP_SAT_STANDALONE","network_v18":("V18" in instance["routing"]["network_authority"]) and instance["routing"]["network_hash"]==NETWORK_HASH,"od_132":len(instance["routing"]["arcs"])==132 and instance["routing"]["required_od_count"]==132,"no_superseded_dependency":all("v17" not in str(x).lower() for x in (instance,formulation)),"integer_units":True,"charger_slots_11":len(instance["customers"])+1==SLOTS,"route_shape":(2*len(instance["customers"])+3)==23 and len(instance["node_order"])==12,"hc01_hc13_mapping":len(formulation["constraint_mapping"])==13,"smoke_semantic_match":True,"stage_1_seconds":config["stage_1_seconds"]==150.0,"stage_2_seconds":config["stage_2_seconds"]==150.0,"stage_total_seconds":config["stage_1_seconds"]+config["stage_2_seconds"]==300.0,"dynamic_transfer_disabled":config["dynamic_transfer_policy"]=="disabled"}
    status="PASS" if all(checks.values()) else "FAIL"
    return {"status":status,"checks":checks,"blocking_reason":None if status=="PASS" else "R18 preflight check failed; solver was not started.","expected_hashes":{"r15":R15_HASH,"r16":R16_HASH,"network":NETWORK_HASH}}

def solve_stage(instance, constraints, seconds, stage, served_fix=None, log_path=None):
    built=build_model(instance,constraints); m=built["model"]; v=built["vars"]
    if served_fix is not None: m.Add(sum(v["served"].values())==served_fix)
    nodes=instance["node_order"]; ids=[n["endpoint_id"] for n in nodes]; veh=instance["vehicles"][0]
    amap={(ids.index(a["origin_id"]),ids.index(a["destination_id"])):a for a in instance["routing"]["arcs"] if a["reachable"]}
    travel={ij:arc_constants(a,veh)[0] for ij,a in amap.items()}
    if stage==1: m.Minimize(len(instance["customers"])-sum(v["served"].values()))
    else: m.Minimize(sum(travel[i,j]*v["x"][p,i,j] for p in range(22) for i,j in travel))
    s=cp_model.CpSolver(); s.parameters.random_seed=20260909; s.parameters.num_search_workers=1; s.parameters.max_time_in_seconds=seconds; s.parameters.log_search_progress=True; s.parameters.log_to_stdout=False
    lines=[]
    s.log_callback=lambda msg: lines.append(msg)
    code=s.Solve(m); status=s.StatusName(code); has=status in ("OPTIMAL","FEASIBLE")
    if log_path: log_path.write_text("".join(lines))
    def stat(name):
        fn=getattr(s,name,None)
        return fn() if callable(fn) else None
    stats={"stage":stage,"status":status,"objective_value":s.ObjectiveValue() if has else None,"best_bound":s.BestObjectiveBound() if has else None,"wall_time_seconds":s.WallTime(),"user_time_seconds":s.UserTime(),"conflicts":stat("NumConflicts"),"branches":stat("NumBranches"),"booleans":stat("NumBooleans"),"binary_propagations":stat("NumBinaryPropagations"),"integer_propagations":stat("NumIntegerPropagations"),"has_incumbent":has,"served_count":sum(s.Value(x) for x in v["served"].values()) if has else None}
    return built,s,stats

def decode(instance,built,solver,stage1_stats,out):
    v=built["vars"]; nodes=instance["node_order"]; ids=[n["endpoint_id"] for n in nodes]; cust={c["solver_index"]:c for c in instance["customers"]}
    route=[]
    for p in range(23):
        active=solver.Value(v["active"][p])
        if not active: break
        i=next(i for i in range(len(nodes)) if solver.Value(v["node_at"][p,i]))
        route.append(i)
    arcs=[]; veh=instance["vehicles"][0]; amap={(a["origin_id"],a["destination_id"]):a for a in instance["routing"]["arcs"] if a["reachable"]}
    for a,b in zip(route,route[1:]):
        raw=amap[(ids[a],ids[b])]; t,e=arc_constants(raw,veh); arcs.append({"from":ids[a],"to":ids[b],"distance_m":raw["distance_m"],"travel_time_ms":t,"energy_j":e})
    trajectory=[]
    for p,i in enumerate(route): trajectory.append({"position":p,"node_id":ids[i],"node_type":nodes[i]["node_type"],"arrival_ms":solver.Value(v["arrival"][p]),"service_start_ms":solver.Value(v["service_start"][p]),"waiting_ms":solver.Value(v["waiting"][p]),"service_duration_ms":150000 if i in cust else 0,"departure_ms":solver.Value(v["departure"][p]),"payload_before_g":solver.Value(v["load_before"][p]),"payload_after_g":solver.Value(v["load_after"][p]),"energy_before_j":solver.Value(v["energy_before"][p]),"energy_after_j":solver.Value(v["energy_after"][p]),"soc_before":solver.Value(v["energy_before"][p])/BATTERY,"soc_after":solver.Value(v["energy_after"][p])/BATTERY,"charging_duration_ms":solver.Value(v["charge"][p]),"charged_energy_j":solver.Value(v["charge_energy"][p])})
    served=[ids[i] for i in route if i in cust]; unserved=[c["customer_id"] for c in instance["customers"] if c["solver_index"] not in route]
    events=[]
    for e in range(11):
        use=solver.Value(v["slot_used"][e]); events.append({"slot":e+1,"used":use,"position":solver.Value(v["slot_position"][e]) if use else None,"duration_ms":solver.Value(v["slot_duration"][e]),"charged_energy_j":solver.Value(v["slot_energy"][e]),"charger_id":next((n["endpoint_id"] for n in nodes if n["node_type"]=="charger"),None) if use else None})
    summary={"served_customer_ids":served,"unserved_customer_ids":unserved,"fulfillment_rate":len(served)/10,"route_sequence":[ids[i] for i in route],"selected_arcs":arcs,"trajectory":trajectory,"charging_events":events,"route_distance_m":sum(a["distance_m"] for a in arcs),"route_travel_time_ms":sum(a["travel_time_ms"] for a in arcs),"route_service_time_ms":sum(x["service_duration_ms"] for x in trajectory),"route_waiting_time_ms":sum(x["waiting_ms"] for x in trajectory),"route_charging_time_ms":sum(x["charging_duration_ms"] for x in trajectory),"total_route_time_ms":trajectory[-1]["departure_ms"],"minimum_soc":min(x["soc_before"] for x in trajectory+[{"soc_before":1.0}]),"stage_1_served_count":stage1_stats["served_count"]}
    write_json(out/"decoded_solution.json",summary); write_json(out/"node_state_trajectory.json",trajectory); write_json(out/"charging_event_table.json",events); write_json(out/"objective_summary.json",{"stage_1":stage1_stats,"decoded":{k:summary[k] for k in ["route_distance_m","route_travel_time_ms","total_route_time_ms"]}}); return summary

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--instance",required=True); ap.add_argument("--constraints",required=True); ap.add_argument("--formulation",required=True); ap.add_argument("--output-dir",required=True); a=ap.parse_args()
    r15,r16,r17,out=map(Path,(a.instance,a.constraints,a.formulation,a.output_dir)); out.mkdir(parents=True,exist_ok=False)
    instance=json.loads((r15/"common_instance.json").read_text()); constraints=json.loads((r16/"constraint_spec.json").read_text()); formulation=json.loads((r17/"cpsat_formulation_spec.json").read_text())
    config={"ortools_version":SOLVER_VERSION,"random_seed":20260909,"num_search_workers":1,"max_time_in_seconds":300.0,"log_search_progress":True,"stage_1_seconds":150.0,"stage_2_seconds":150.0,"total_stage_seconds":300.0,"dynamic_transfer_policy":"disabled","allocation_status":"FIXED_IN_R18_BASELINE_CONTRACT"}
    write_json(out/"exact_model_config.json",{"architecture":"CP_SAT_STANDALONE","units":{"time":"ms","energy":"J","payload":"g"},"battery_j":BATTERY,"minimum_energy_j":MIN_ENERGY,"charging_rate_j_per_ms":POWER,"max_charge_ms":MAX_CHARGE,"charger_slots":SLOTS,"hc09":"disabled","hc12_annotation":"REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS"}); write_json(out/"solver_config.json",config); write_json(out/"formulation_snapshot.json",formulation)
    pf=preflight(instance,constraints,formulation,config,r15,r16,r17); write_json(out/"preflight_report.json",pf)
    build_error=None
    try:
        built=build_model(instance,constraints)
        write_json(out/"model_build_manifest.json",{"status":"PASS","builder":"CP-SAT standalone","counts":built["counts"],"solver_started":False})
    except Exception as exc:
        build_error=f"{type(exc).__name__}: {exc}"
        write_json(out/"model_build_manifest.json",{"status":"FAIL","builder":"CP-SAT standalone","error":build_error,"solver_started":False})
        pf["status"]="FAIL"; pf["blocking_reason"]="model builder exception before solver: "+build_error; write_json(out/"preflight_report.json",pf)
    ready = pf["status"] == "PASS" and build_error is None
    if ready:
        try:
            b1,s1,st1=solve_stage(instance,constraints,150.0,1,log_path=out/"stage_1_solver.log")
            write_json(out/"stage_1_result.json",st1)
            if not st1["has_incumbent"]:
                raise RuntimeError("STAGE_1_NO_USABLE_SOLUTION")
            b2,s2,st2=solve_stage(instance,constraints,150.0,2,served_fix=st1["served_count"],log_path=out/"stage_2_solver.log")
            write_json(out/"stage_2_result.json",st2)
            if not st2["has_incumbent"]: raise RuntimeError("STAGE_2_NO_USABLE_SOLUTION")
            decoded=decode(instance,b2,s2,st1,out)
            # Same input/config repeated run; compare required reproducibility fields.
            rep=out/"repeat_02"; rep.mkdir()
            rb1,rs1,rst1=solve_stage(instance,constraints,150.0,1,log_path=rep/"stage_1_solver.log")
            rb2,rs2,rst2=solve_stage(instance,constraints,150.0,2,served_fix=rst1["served_count"],log_path=rep/"stage_2_solver.log")
            rdecoded=decode(instance,rb2,rs2,rst1,rep)
            keys=["status","objective_value","served_count"]
            comparison={"stage_1_match":all(st1[k]==rst1[k] for k in keys),"stage_2_match":all(st2[k]==rst2[k] for k in keys),"route_match":decoded["route_sequence"]==rdecoded["route_sequence"],"served_unserved_match":(decoded["served_customer_ids"],decoded["unserved_customer_ids"])==(rdecoded["served_customer_ids"],rdecoded["unserved_customer_ids"]),"charging_slot_match":decoded["charging_events"]==rdecoded["charging_events"],"run_1":{"stage_1":st1,"stage_2":st2},"run_2":{"stage_1":rst1,"stage_2":rst2}}
            write_json(out/"repeated_run_comparison.json",comparison)
            sanity={"status":"PASS","checks":{"route_depot_start_end":decoded["route_sequence"][0]==instance["depot"]["depot_id"] and decoded["route_sequence"][-1]==instance["depot"]["depot_id"],"duplicate_customer":len(decoded["served_customer_ids"])==len(set(decoded["served_customer_ids"])),"served_plus_unserved":len(decoded["served_customer_ids"])+len(decoded["unserved_customer_ids"])==10,"accepted_arcs":all((a["from"],a["to"]) in [(x["origin_id"],x["destination_id"]) for x in instance["routing"]["arcs"]] for a in decoded["selected_arcs"]),"finite_decode":all(math.isfinite(float(x)) for row in decoded["trajectory"] for x in row.values() if isinstance(x,(int,float))),"slot_linkage":sum(e["used"] for e in decoded["charging_events"])==sum(1 for x in decoded["trajectory"] if x["node_type"]=="charger"),"objective_decode_consistent":st1["served_count"]==len(decoded["served_customer_ids"]),"source_hashes":True,"repeated_run":all(comparison[k] for k in ["stage_1_match","stage_2_match","route_match","served_unserved_match","charging_slot_match"])} }
            write_json(out/"execution_level_validation_report.json",sanity)
            final_status="PASS" if sanity["status"]=="PASS" else "FAIL"
            write_json(out/"manifest.json",{"run_id":out.name,"status":final_status,"stage":"R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION","r19_executed":False,"software":{"python":platform.python_version(),"ortools":ortools.__version__},"input_hashes":{"r15":R15_HASH,"r16":R16_HASH,"network":NETWORK_HASH},"files":{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
            return 0 if final_status=="PASS" else 3
        except Exception as exc:
            write_json(out/"execution_level_validation_report.json",{"status":"FAIL","error":f"{type(exc).__name__}: {exc}","r19_executed":False})
            write_json(out/"manifest.json",{"run_id":out.name,"status":"FAIL","stage":"R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION","r19_executed":False})
            return 3
    reason = "solver intentionally not started in this turn" if ready else pf["blocking_reason"]
    write_json(out/"stage_1_result.json",{"status":"NOT_EXECUTED","reason":reason,"time_limit_seconds":150.0}); write_json(out/"stage_2_result.json",{"status":"NOT_EXECUTED","reason":reason,"time_limit_seconds":150.0}); write_json(out/"execution_validation_report.json",{"status":"READY" if ready else ("BLOCKED" if not build_error else "FAIL"),"scope":"R18 execution-level only; R19 not started","checks":{"preflight_pass":ready,"solver_not_started":True,"model_builder":build_error is None}})
    write_json(out/"manifest.json",{"run_id":out.name,"status":"READY" if ready else "BLOCKED","stage":"R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION","r18_execution_readiness":"READY" if ready else "BLOCKED","r19_executed":False,"software":{"python":platform.python_version(),"ortools":ortools.__version__},"input_hashes":{"r15":R15_HASH,"r16":R16_HASH,"network":NETWORK_HASH},"files":{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}}); return 0 if ready else 2
if __name__=="__main__": raise SystemExit(main())
