#!/usr/bin/env python3
"""Prepare and execute the isolated grouped-v2 local-size pilot on hayate."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import random
import resource
import signal
import subprocess
import sys
import threading
import time

from audit_grouped_loading_v2 import independently_build
from prepare_grouped_formal_v2 import environment
from run_grouped_formal_v2 import load_registration
from run_grouped_loading_v2 import POLICY, load_policy, load_problem
from kmd_toc.grouped_loading_v2 import model, recheck, search
from kmd_toc.iterative_d3 import operators, rng_v2
from kmd_toc.iterative_d3_ops import resources
from kmd_toc.iterative_v3 import order, quantum
from kmd_toc.iterative_v3.io import atomic, decode_routes, dump, read, sha
from kmd_toc.iterative_v3_study.analysis import delta
from report_grouped_qaoa_size_pilot import exact_checked, report, trace, write_csv

ROOT = Path(__file__).resolve().parents[1]
ENTRY = Path(__file__).resolve()
OUT = ROOT / "output/iterative_d3"
FORMAL = OUT / "formal_J30_grouped_v2"
PILOT = OUT / "grouped_loading_20261124_v2_pilot"
BUDGET = OUT / "qaoa_budget_grouped_v2_20261124"
ANGLES = OUT / "qaoa_initial_transfer_grouped_v2_20261124"
VERSION = "grouped-v2-qaoa-size-20261124-v1"
SIZES = (10, 12, 14)
SCALES = ("S1", "S2", "S3")
METHODS = ("D_classical", "D_quantum")
TECH_CASES = ("S1-current-1", "S2-reallocation-1", "S3-current-2", "S3-reallocation-2")


class ApprovalHold(RuntimeError):
    pass


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_once(path, data):
    data = json.loads(json.dumps(data))
    if path.is_file():
        if read(path) != data:
            raise ValueError(f"REGISTERED_RECORD_DRIFT:{path}")
    else:
        dump(path, data)


def formal_guard():
    p = FORMAL / "MANIFEST.json"
    manifest = read(p)
    checksum = sha(p)
    if (manifest["state"], manifest["comparison_cases"], manifest["formal_workers"]) != ("NOT_STARTED", 90, 0):
        raise ValueError("FORMAL_STATE")
    if any((FORMAL / name).exists() for name in ("EXECUTION_STARTED.json", "trials", "COMPLETE.json")):
        raise ValueError("FORMAL_EXECUTION_PRESENT")
    if read(FORMAL / "FREEZE_RECORD.json")["manifest_sha256"] != checksum:
        raise ValueError("FORMAL_FREEZE")
    return dict(state="NOT_STARTED", comparison_cases=90, workers_launched_by_pilot=0,
                manifest_sha256=checksum, freeze_sha256=sha(FORMAL / "FREEZE_RECORD.json"),
                seed_sha256=sha(FORMAL / "SEEDS.csv"))


def telemetry(out, state, **values):
    atomic(out / "PROGRESS.json", dict(state=state, updated=now(), formal_workers=0, **values))


def locals_for(p, plan, slot, center, seed):
    """Use the production window/lookup builder, fixing the selected trip and start."""
    routes = decode_routes(plan["routes"])
    r = routes[slot]
    windows = {}
    for n in SIZES:
        start = center - n // 2
        modulus = len(r) - n + 1
        if not 0 <= start < modulus:
            raise ValueError("INVALID_NESTED_WINDOW_CENTER")
        offset_seed = seed - seed % modulus + start
        win = order.build(p, routes, n, offset_seed, [slot])
        if (win.vehicle, win.trip) != slot or win.ids != r[start:start+n]:
            raise ValueError("WINDOW_DID_NOT_USE_REGISTERED_TRIP")
        windows[n] = replace(win, seed=seed)
    if windows[14].ids[1:-1] != windows[12].ids or windows[12].ids[1:-1] != windows[10].ids:
        raise ValueError("NESTING")
    return windows


def source_candidates(scale, origin):
    for branch in range(4):
        folder = PILOT / scale / "D_quantum" / f"branch_{branch}"
        for marker in sorted(folder.glob("iteration_*/COMMIT.json")):
            c = read(marker)
            if origin == "current":
                yield marker.parent / c["state_file"], None
            else:
                for r in c["candidate_receipts"]:
                    if r["kind"] == "classical_reallocation_only" and r["status"] == "FEASIBLE":
                        path = marker.parent / f'{r["id"]}.json'
                        yield path, r["move_id"]


def extract(out, config, scale, spec):
    p = load_problem(spec["input"], config["rest_options"])
    base = FORMAL / scale / "B/plan.json"
    seed = rng_v2.event(dict(stage="diagnostic", scale=scale, trial=549000), VERSION, "extract-windows")
    rng = random.Random(seed)
    used = set()
    groups = []
    for origin in ("current", "reallocation"):
        pool = list(source_candidates(scale, origin))
        rng.shuffle(pool)
        for path, move in pool:
            raw = read(path)
            plan = raw["plan"] if move else raw
            routes = decode_routes(plan["routes"])
            slots = sorted(k for k, r in routes.items() if len(r) >= max(SIZES))
            if move:
                marker = read(path.parent / "COMMIT.json")
                prev = (path.parent.parent / f'iteration_{marker["iteration"]-1:04d}' / "state.json"
                        if marker["iteration"] else base)
                before = decode_routes(read(prev)["routes"])
                slots = [k for k in slots if set(before.get(k, ())) != set(routes[k])]
            if not slots:
                continue
            slot = rng.choice(slots)
            route = routes[slot]
            center = rng.randint(7, len(route)-7)
            group = locals_for(p, plan, slot, center, seed)
            signature = tuple(sorted(group[14].ids))
            if signature in used:
                continue
            used.add(signature)
            ordinal = 1 + sum(g["origin"] == origin for g in groups)
            ident = f"{scale}-{origin}-{ordinal}"
            folder = out / "cases" / ident
            folder.mkdir(parents=True, exist_ok=True)
            parent = folder / "parent.json"
            write_once(parent, plan)
            for n, problem in group.items():
                write_once(folder / f"n{n}.json", dict(problem=asdict(problem), case_hash=problem.fingerprint))
            groups.append(dict(id=ident, scale=scale, origin=origin, move=move, input=spec["input"],
                source=str(path), source_sha256=sha(path), parent=str(parent), parent_sha256=sha(parent),
                parent_physical_hash=plan["physical_hash"], base=str(base), base_sha256=sha(base),
                calls_s=plan["calls_s"], vehicle=slot[0], trip=slot[1], center=center,
                extraction_seed=seed, windows={str(n): dict(path=str(folder/f"n{n}.json"),
                    sha256=sha(folder/f"n{n}.json"), ids=w.ids, entry=w.entry, exit=w.exit)
                    for n, w in group.items()}))
            if ordinal == 2:
                break
        else:
            raise ValueError(f"EXTRACTION_SHORTFALL:{scale}:{origin}")
    return groups


def seed_context(scale, ordinal):
    return rng_v2.context("diagnostic", scale, ordinal)


def prepare(out):
    if (out / "MANIFEST.json").exists():
        raise ValueError("PILOT_ALREADY_PREPARED")
    m = load_registration(FORMAL)
    if m["version"] != "grouped-loading-20261124-v2":
        raise ValueError("WRONG_FORMAL_PARENT")
    cfg = m["configuration"]
    s, q = cfg["search"], cfg["search"]["quantum"]
    assert (s["local_order_size"], s["outer_iterations"], s["physical_completion_budget"],
            s["returned_order_candidates"], s["classical"]["classical_evaluations"]) == (12,10,70,4,2048)
    assert (q["optimizer_max_evaluations"], q["optimizer_restarts"], q["optimizer_rhobeg"], q["optimizer_tol"]) == (24,1,.1,.01)
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    cases=[]; jobs=[]
    for scale in SCALES:
        spec=next(c for c in m["cases"] if c["scale"]==scale)
        block=extract(out,cfg,scale,spec)
        cases.extend(block)
        for index,c in enumerate(block):
            for n in SIZES:
                for rep in range(2):
                    jobs.append(dict(id=f'local-{c["id"]}-n{n}-r{rep}', phase="local",
                        case=c["id"],n=n,rep=rep,scale=scale,method="D_quantum",
                        context=seed_context(scale,549100+2*index+rep)))
                if c["id"] in TECH_CASES:
                    jobs.append(dict(id=f'tech-{c["id"]}-n{n}',phase="technical",case=c["id"],n=n,
                        scale=scale,method="D_quantum",context=seed_context(scale,549200+index)))
        ctx=seed_context(scale,549300)
        for n in SIZES:
            for method in METHODS:
                for branch in range(4):
                    jobs.append(dict(id=f"outer-{scale}-n{n}-{method}-b{branch}",phase="outer",
                        n=n,scale=scale,method=method,branch=branch,context=ctx|dict(branch=branch)))
    local=[j for j in jobs if j["phase"]=="local"]
    for j in local:
        jobs.append(j|dict(id=j["id"].replace("local-","classical-",1),phase="classical",method="D_classical"))
        if j["rep"]==0:
            jobs.append(j|dict(id=f'exact-{j["case"]}-n{j["n"]}',phase="exact",method="reference"))
    contexts={tuple(sorted(j["context"].items())) for j in jobs}
    seeds={}
    for items in sorted(contexts):
        ctx=dict(items)
        # n and the other D arm share this logical context by design.
        arms=("D_classical","D_quantum") if "branch" in ctx else (
            ("D_quantum",) if ctx["trial"]>=549200 else ("D_classical","D_quantum"))
        def register(seed, group, iteration, use, sample=None):
            if seed in seeds:
                raise ValueError("UNINTENDED_SEED_COLLISION")
            seeds[seed]=ctx|dict(group=group,iteration=iteration,purpose=use,sample=sample,seed=seed)
        if "branch" in ctx:
            register(rng_v2.event(ctx,"D_shared","branch-identity"),"D_shared",-1,"branch-identity")
        for iteration in range(10 if "branch" in ctx else 1):
            if "branch" in ctx:
                for purpose in ("outer-neighbours","whole-transfer","local-window"):
                    register(rng_v2.event(ctx,"D_shared",purpose,iteration),"D_shared",iteration,purpose)
            for arm in arms:
                generated=rng_v2.call_seeds(ctx,arm,iteration,24)
                if arm=="D_classical":
                    register(generated["rng_seed"],arm,iteration,"order-search")
                else:
                    for index, seed in enumerate(generated["measurement_seeds"]["optimization"]):
                        register(seed,arm,iteration,"learn-sample",index)
                    register(generated["measurement_seeds"]["final"],arm,iteration,"final-sample")
    import csv
    with (FORMAL/"SEEDS.csv").open() as file:
        if any(int(row["effective_seed"]) in seeds for row in csv.DictReader(file)):
            raise ValueError("FORMAL_SEED_OVERLAP")
    write_csv(out/"SEEDS.csv",list(seeds.values()))
    protocol=dict(version=VERSION,registered_at=now(),sizes=list(SIZES),reference_size=12,
        settings=dict(qaoa_layers=2, learning_shots=1000, final_shots=10000, angles_domain="unbounded R^4",
            initial_angles="requires explicit researcher adoption of the separate initialization study",
            optimization=q, returned_orders=4, classical=s["classical"], outer_iterations=10,
            physical_limit=70, branches=4), resource_policy=POLICY,
        budgets=read(BUDGET/"PROTOCOL.json")["stopping_thresholds"],
        design=dict(local_cases=12,seeds_per_case=2,planned_local_QAOA=72,planned_outer_methods=18,
            planned_outer_branches=72,technical_cases=list(TECH_CASES),technical_calls=12,
            extraction="seeded shuffle of archived grouped-v2 states and evaluated reallocation candidates, "
                       "eligible-trip uniform choice, integer center uniform over 14-feasible offsets, "
                       "no identical customer set across windows within scale; frozen before computation",
            paired_rng="phase, scale, archived case and replicate fixed across n; training, final, classical "
                       "separate streams; outer paired across n by scale and branch, no shared measurements",
            metrics="within-n relative gap and improvement opportunity; normalized expectation differences descriptive "
                    "across n because boundary and normalization change",
            decision="Use absolute global D/W and B-based I_dual. Reuse material global thresholds from budget study; "
                     "n14 needs material nonworsening gains in at least two scales and no remaining-scale D/W loss. "
                     "n10 needs local median gap loss <=0.5pp, no material global loss in all scales and lower "
                     "median paired outer wall and peak branch RSS. Else retain n12 if technically qualified. "
                     "Incomplete or technically unqualified n12 precludes a recommendation to change formal settings."),
        formal_workers_allowed=False, formal_contribution=0)
    dump(out/"PROTOCOL.json",protocol)
    dump(out/"MANIFEST.json",dict(version=VERSION,formal=formal_guard(),head=subprocess.check_output(
        ["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),programs={str(path):sha(path) for path in
        (ENTRY,ENTRY.with_name("report_grouped_qaoa_size_pilot.py"),BUDGET/"pilot.py",BUDGET/"PROTOCOL.json")},
        source_registration=str(FORMAL/"MANIFEST.json"),protocol_sha256=sha(out/"PROTOCOL.json"),
        seed_sha256=sha(out/"SEEDS.csv"),formal_code_hashes=m["code_hashes"],
        frozen_inputs=m["input_hashes"], environment=m["environment"],config=cfg,demand=m["grouped_conditions"],
        scale_inputs={c["scale"]:c["input"] for c in cases},cases=cases,jobs=jobs,
        saved_references={scale:{method:dict(path=str(PILOT/scale/method/"plan.json"),
              sha256=sha(PILOT/scale/method/"plan.json")) for method in ("B","C_Idual")} for scale in SCALES}))
    write_csv(out/"LOCAL_PROBLEMS.csv",[dict(id=c["id"],scale=c["scale"],origin=c["origin"],n=n,
        center=c["center"],vehicle=c["vehicle"],trip=c["trip"],parent=c["parent"],
        reception=c["calls_s"],**c["windows"][str(n)]) for c in cases for n in SIZES])
    telemetry(out,"HOLD",stage="REGISTERED",reason="INITIAL_PARAMETERS_NOT_APPROVED",completed=0,
              running=0,unrun=len(jobs),failed=0)
    dump(out/"TECHNICAL_VALIDATION.json",{str(n):dict(status="UNVERIFIED",reason="pending explicit initial-angle approval")
         for n in SIZES})


def registered(out, *, thorough=False):
    m=read(out/"MANIFEST.json")
    if (m["version"]!=VERSION or m["formal"]!=formal_guard() or sha(out/"PROTOCOL.json")!=m["protocol_sha256"]
            or sha(out/"SEEDS.csv")!=m["seed_sha256"]):
        raise ValueError("SIZE_PILOT_BINDING")
    if thorough:
        load_registration(FORMAL)
        paths=dict(m["programs"])
        for c in m["cases"]:
            paths.update({c["parent"]:c["parent_sha256"],c["base"]:c["base_sha256"],c["source"]:c["source_sha256"]})
            paths.update({w["path"]:w["sha256"] for w in c["windows"].values()})
        for ref in m["saved_references"].values():
            for item in ref.values():
                paths[item["path"]]=item["sha256"]
        if any(sha(f)!=h for f,h in paths.items()):
            raise ValueError("REGISTERED_SOURCE_DRIFT")
        if environment(m["config"]["branch_python"])!=m["environment"]["branch"]:
            raise ValueError("REGISTERED_RUNTIME_DRIFT")
    return m


def adopt(out, arm, reference):
    if not reference.strip() or not (ANGLES/"RUN_COMPLETE.json").is_file() or not (ANGLES/"summary.json").is_file():
        raise ApprovalHold("INITIALIZATION_STUDY_INCOMPLETE_OR_APPROVAL_REFERENCE_MISSING")
    a=read(ANGLES/"INITIAL_VALUES.json")["angles"][arm]
    if len(a)!=4 or not all(math.isfinite(value) for value in a):
        raise ValueError("APPROVED_ANGLE_VECTOR")
    dump(out/"INITIAL_APPROVAL.json",dict(arm=arm,angles=a,approval_reference=reference,
        recorded=now(),source_sha256=sha(ANGLES/"INITIAL_VALUES.json"),
        comparison_summary_sha256=sha(ANGLES/"summary.json")))


def approval(out):
    p=out/"INITIAL_APPROVAL.json"
    if not p.is_file():
        raise ApprovalHold("INITIAL_PARAMETERS_NOT_APPROVED")
    a=read(p)
    if (sha(ANGLES/"INITIAL_VALUES.json")!=a["source_sha256"]
        or sha(ANGLES/"summary.json")!=a["comparison_summary_sha256"]
        or read(ANGLES/"INITIAL_VALUES.json")["angles"][a["arm"]]!=a["angles"]
        or not a["approval_reference"].strip()):
        raise ApprovalHold("APPROVAL_SOURCE_DRIFT")
    return a


def load_window(case,n):
    spec=case["windows"][str(n)]
    if sha(spec["path"])!=spec["sha256"]:
        raise ValueError("WINDOW_CHECKSUM")
    h=read(spec["path"]); r=h["problem"]
    problem=order.OrderProblem(**(r|{k:tuple(r[k]) for k in ("ids","prefix","suffix")}))
    if problem.fingerprint!=h["case_hash"] or problem.n!=n:
        raise ValueError("WINDOW_IDENTITY")
    return problem,h


def independent(p,plan,duty):
    recheck.recheck(plan,independently_build(p,plan),{b.berth_id:(b.opening_s,b.closing_s) for b in p.berths},
                    duty,p.rest_options,p.depot.depot_id)


def plan_values(plan,base,parent):
    return {k:plan[k] for k in ("physical_hash","L_km","D_exact","W_exact","D_km_per_parcel","W_total_min",
        "W_min_per_configured_vehicle_day","W1_s","W2_s","before_reception_total_s","final_return_s")} | dict(
        I_dual_B_pp=delta(plan,base)["I_dual_percent"], delta_D_parent_km=plan["L_km"]-parent["L_km"],
        delta_W_parent_min=plan["W_total_min"]-parent["W_total_min"])


def complete_orders(p,problem,orders,duty,parent,base,folder):
    rank=lambda x:model.candidate_key(x,base,initial=x["physical_hash"]==base["physical_hash"])
    best=parent; winning=None; report_rows=[]
    for i,item in enumerate(orders):
        row=dict(index=i,**item)
        try:
            plan=model.evaluate(p,order.expand(problem,item["order"]),parent["calls_s"],duty)
        except model.ScheduleError as error:
            row.update(feasible=False,reason=str(error))
        else:
            independent(p,plan,duty)
            row.update(feasible=True,**plan_values(plan,base,parent))
            name=f"candidate_{i}.json"
            write_once(folder/name,plan)
            row["plan"]=name
            if rank(plan)<rank(best):
                best=plan; winning=i
        report_rows.append(row)
    for row in report_rows:
        row["adopted"]=row["index"]==winning
    write_once(folder/"selected_plan.json",best)
    return dict(candidates=report_rows,selected_index=winning,selected=plan_values(best,base,parent),
                feasible_candidates=sum(row["feasible"] for row in report_rows))


def trial_seeds(job):
    if job["phase"]=="outer":
        return dict(branch=rng_v2.event(job["context"],"D_shared","branch-identity"))
    return rng_v2.call_seeds(job["context"],job["method"],0,24) | rng_v2.call_seeds(job["context"],"D_classical",0)


def profile():
    return dict(cpu_s=time.process_time(),peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)


def local_solver(out, m, job, folder, angles):
    case=next(c for c in m["cases"] if c["id"]==job["case"])
    n=job["n"]
    problem,h=load_window(case,n)
    cfg=m["config"]["search"]
    if job["phase"]=="exact":
        return exact_checked(problem)
    p=load_problem(case["input"],m["config"]["rest_options"])
    duty=load_policy()|{"loading_s":m["demand"]["loading_s"]}
    parent,base=read(Path(case["parent"])),read(Path(case["base"]))
    seeds=trial_seeds(job)
    if job["phase"]=="classical":
        items,r=order.classical(problem,cfg["classical"]|{"rng_seed":seeds["rng_seed"]},4)
        return r|complete_orders(p,problem,items,duty,parent,base,folder)
    settings=cfg["quantum"]|dict(initial_angles=angles,measurement_seeds=seeds["measurement_seeds"])
    solver=folder/"solver"
    if job["phase"]=="technical" and n==14 and not (solver/"EVAL_000.json").exists():
        try:
            quantum.run(problem,settings,solver,4,pause_after_evaluations=1)
        except quantum.DiagnosticPause:
            pass
        else:
            raise ValueError("CHECKPOINT_PROBE_DID_NOT_PAUSE")
    first=solver/"EVAL_000.json"
    first_hash=sha(first) if first.is_file() else None
    items,r=operators.selected_quantum(quantum.run,problem,settings,solver,4,local_header=h)
    if first_hash and sha(first)!=first_hash:
        raise ValueError("CHECKPOINT_REWRITTEN")
    samples=r["selector"]; bound=settings["TV_bound_max"]
    if samples["invalid_shots"] or r["max_TV_bound"]>bound:
        raise ValueError("INVALID_PERMUTATION_OR_TV")
    output={k:v for k,v in r.items() if k not in ("selector","measurement_provenance")}
    output.update(selection={k:v for k,v in samples.items() if k!="candidates"},
                  checkpoint_unchanged=bool(first_hash))
    if job["phase"]=="technical" and n==14 and not (first_hash and r["cached_evaluations_reused"]):
        raise ValueError("N14_CHECKPOINT_NOT_REPLAYED")
    if job["phase"]=="technical":
        trace(folder, job, [])
    output.update(complete_orders(p,problem,items,duty,parent,base,folder))
    return output


def run_job(job_path):
    lease,binding,_=resources.authorized(Path(os.environ["KMD_D3_LEASE_INTENT"]),worker=True)
    out=Path(lease["output"]); m=registered(out); a=approval(out)
    if binding["job"]!=str(job_path) or lease["manifest_sha256"]!=sha(out/"MANIFEST.json"):
        raise ValueError("JOB_LEASE_BINDING")
    job=read(job_path); folder=job_path.parent; started=time.monotonic()
    try:
        if job["phase"]=="outer":
            p=load_problem(m["scale_inputs"][job["scale"]],m["config"]["rest_options"])
            base=read(FORMAL/job["scale"]/"B/plan.json")
            cfg=deepcopy(m["config"]["search"])
            cfg.update(local_order_size=job["n"],rng_v2=job["context"])
            cfg["quantum"]["initial_angles"]=a["angles"]
            duty=load_policy()|{"loading_s":m["demand"]["loading_s"]}
            value=search.run(p,base,folder/"branch",job["method"],cfg,trial_seeds(job)["branch"],job["branch"],duty)
            independent(p,read(folder/"branch/plan.json"),duty)
        else:
            value=local_solver(out,m,job,folder,a["angles"])
    except (ValueError, AssertionError) as error:
        # Deterministic contract failures in the technical test disqualify the size.
        if job["phase"]!="technical":
            raise
        value=dict(status="FAIL",reason=str(error))
    details={str(path.relative_to(folder)):sha(path) for path in folder.rglob("*.json")
        if path.name!="COMMITTED.json"}
    write_once(folder/"COMMITTED.json",dict(job=job,approval_sha256=sha(out/"INITIAL_APPROVAL.json"),
            status=value.get("status","COMPLETE"),result=value,hashes=details,
            wall_s=time.monotonic()-started,**profile()))


def committed(folder, out, job):
    path=folder/"COMMITTED.json"
    if not path.exists():
        return None
    row=read(path)
    if row["job"]!=job or row["approval_sha256"]!=sha(out/"INITIAL_APPROVAL.json") or any(
            sha(folder/f)!=h for f,h in row["hashes"].items()):
        raise ValueError(f"COMPLETION_CHECKSUM:{folder}")
    return row


def stop_signal(*_):
    raise KeyboardInterrupt


def date_progress(out, state, started, m, stage, finished, failures, skipped, jobs=(), **extra):
    telemetry(out,state,pid=os.getpid(),controller=resources.proc(os.getpid()),started_at=started,
        elapsed_s=time.monotonic()-m,stage=stage,running=len(jobs),completed=finished,failed=failures,skipped=skipped,
        active_jobs=list(jobs),**extra)


@contextmanager
def live_resources(out, directory, activity):
    ending=threading.Event()
    last_sample=None
    def monitor():
        nonlocal last_sample
        while not ending.wait(3):
            traces=sorted(directory.glob("executions/*/RESOURCES.jsonl"))
            try:
                if not traces: continue
                with traces[-1].open("rb") as file:
                    file.seek(max(0,file.seek(0,os.SEEK_END)-262144))
                    lines=file.read().splitlines()
                if not lines: continue
                last_sample=json.loads(lines[-1])
                workers=[p for tree in last_sample["worker_trees"] for p in tree]
                cpu_s=0
                for p in workers:
                    try:
                        vals=Path(f"/proc/{p['pid']}/stat").read_text().rpartition(")")[2].split()
                        if int(vals[19])==p["start_ticks"]:
                            cpu_s+=(int(vals[11])+int(vals[12]))/os.sysconf("SC_CLK_TCK")
                    except (FileNotFoundError,ProcessLookupError):
                        continue
                activity.update(resource_sample=last_sample, active_tree_CPU_s=cpu_s,
                                resource_log=str(traces[-1]),resource_sample_at=now())
                atomic(out/"PROGRESS.json",activity|dict(updated=now()))
            except (OSError,ValueError,IndexError):
                continue
    thread=threading.Thread(target=monitor,daemon=True)
    thread.start()
    try:
        yield
    finally:
        ending.set()
        thread.join()


def control(out):
    started=now(); begin=time.monotonic()
    with (out/"CONTROLLER.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        m=registered(out,thorough=True)
        approval(out)
        schedule=m["jobs"]
        stages={stage:[j for j in schedule if j["phase"]==stage] for stage in
                ("technical","exact","classical","local","outer")}
        planned=sum(map(len,stages.values()))
        finished=failed=skipped=0; stage="PREFLIGHT"; allowed=set(SIZES); rows=[]
        def progress(state, jobs=(), reason=None):
            date_progress(out,state,started,begin,stage,finished,failed,skipped,jobs,
                reason=reason,unrun=max(0,planned-finished-failed-skipped-len(jobs)))
        try:
            with resources.acquire(out,sha(out/"MANIFEST.json"),POLICY,VERSION,"local-size-pilot") as lease:
                for stage, jobs in stages.items():
                    if stage=="outer":
                        groups=[[j for j in jobs if (j["scale"],j["n"],j["method"])==key] for key in
                                dict.fromkeys((j["scale"],j["n"],j["method"]) for j in jobs)]
                    else:
                        groups=[]
                        for n in SIZES:
                            batch=[j for j in jobs if j["n"]==n]
                            groups.extend(batch[i:i+4] for i in range(0,len(batch),4))
                    for group in groups:
                        if (out/"STOP_REQUESTED.json").is_file():
                            raise KeyboardInterrupt
                        if group[0]["n"] not in allowed:
                            skipped+=len(group)
                            rows.extend(dict(job=j,status="NOT_RUN_TECHNICAL_GATE") for j in group)
                            continue
                        entries=[]
                        groupdir=out/"logs"/group[0]["id"]
                        groupdir.mkdir(exist_ok=True)
                        disqualified=(groupdir/"RESOURCE_FAILURE.json").is_file()
                        for cpu,job in enumerate(group):
                            f=out/"jobs"/job["id"]; f.mkdir(parents=True,exist_ok=True)
                            spec=job|dict(cpu=cpu)
                            write_once(f/"JOB.json",spec)
                            if not committed(f,out,spec) and not disqualified:
                                entries.append(dict(path=f/"JOB.json",action="_branch"))
                        if entries:
                            progress("RUNNING",[read(j["path"]) for j in entries])
                            with live_resources(out,groupdir,read(out/"PROGRESS.json")):
                                codes,alarm=resources.supervise(lease,ENTRY,entries,groupdir,m["config"])
                            if alarm and stage=="technical":
                                resources.durable(groupdir/"RESOURCE_FAILURE.json",dict(alarm=alarm,codes=codes))
                            elif any(codes) or alarm:
                                raise RuntimeError(f"WORKER_INTERRUPTED:{codes}:{alarm}")
                        for job in group:
                            f=out/"jobs"/job["id"]
                            log=committed(f,out,read(f/"JOB.json"))
                            if log is None and stage=="technical" and (groupdir/"RESOURCE_FAILURE.json").is_file():
                                log=dict(job=job,status="FAIL",result=read(groupdir/"RESOURCE_FAILURE.json"))
                            if log is None:
                                raise ValueError("MISSING_JOB_COMMIT")
                            rows.append(log)
                            if log["status"]=="FAIL": failed+=1
                            else: finished+=1
                        progress("RUNNING")
                    if stage=="technical":
                        tech={str(n): [r for r in rows if r["job"]["n"]==n] for n in SIZES}
                        gate={n:dict(status="PASS" if len(items)==4 and all(r["status"]=="COMPLETE" for r in items)
                                     else "FAIL",workers=items) for n,items in tech.items()}
                        atomic(out/"TECHNICAL_VALIDATION.json",gate)
                        allowed={int(n) for n,r in gate.items() if r["status"]=="PASS"}
                stage="INDEPENDENT_RECHECK_REPORT"; progress("RUNNING")
                report(out,m,rows,allowed,formal_guard())
                atomic(out/"RUN_COMPLETE.json",dict(status="COMPLETE",formal_workers=0,allowed=sorted(allowed),
                    completed=finished,failed_technical=failed,skipped=skipped,completed_at=now(),
                    final_validation_sha256=sha(out/"FINAL_VALIDATION.json")))
                progress("COMPLETE")
        except KeyboardInterrupt:
            progress("INTERRUPTED",reason="operator interruption at batch boundary or signal")
        except resources.Unavailable as e:
            progress("HOLD",reason=str(e)); raise
        except Exception as e:
            progress("FAILED",reason=repr(e)); raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","preflight","approve","launch","run","status","stop","_guard","_branch"))
    parser.add_argument("--output",type=lambda p:Path(p).resolve())
    parser.add_argument("--intent",type=Path)
    parser.add_argument("--job",type=Path)
    parser.add_argument("--arm",choices=("A","B"))
    parser.add_argument("--approval-ref")
    a=parser.parse_args()
    if a.action=="_guard": return resources.guard(a.intent)
    if a.action=="_branch": run_job(a.job); return 0
    out=a.output
    if out is None or not out.is_relative_to(OUT) or not out.name.startswith("qaoa_size_grouped_v2_"):
        parser.error("specific isolated output under output/iterative_d3/qaoa_size_grouped_v2_* required")
    if a.action=="prepare": prepare(out)
    elif a.action=="approve":
        if not a.arm or not a.approval_ref: parser.error("--arm and --approval-ref required")
        registered(out,thorough=True); adopt(out,a.arm,a.approval_ref)
    elif a.action in ("launch","preflight"):
        m=registered(out,thorough=True)
        try:
            approval(out); capacity=resources.budget(POLICY)
        except (ApprovalHold,resources.Unavailable) as error:
            print(json.dumps(dict(state="HOLD",reason=str(error),workers_started=0),ensure_ascii=False))
            return 2
        if a.action=="preflight":
            print(json.dumps(dict(state="READY",planned=len(m["jobs"]),capacity=capacity)))
            return 0
        with (out/"LAUNCH.lock").open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (out/"RUN_COMPLETE.json").exists(): raise ValueError("PILOT_ALREADY_COMPLETE")
            last=out/"LAUNCH.json"
            if last.exists() and resources.same_process(read(last)["identity"]):
                raise ValueError("CONTROLLER_ALREADY_RUNNING")
            flag=out/"STOP_REQUESTED.json"
            if flag.is_file(): flag.rename(out/"logs"/f"stop_{time.time_ns()}.json")
            logfile=out/"logs"/f"controller_{time.time_ns()}.log"
            command=[m["config"]["branch_python"],"-B",str(ENTRY),"run","--output",str(out)]
            with logfile.open("x") as file:
                proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=file,stderr=subprocess.STDOUT,
                                      cwd=ROOT,start_new_session=True)
            identity=resources.proc(proc.pid)
            if identity is None: raise RuntimeError("CONTROLLER_EXITED_AT_LAUNCH")
            result=dict(identity=identity,started_at=now(),command=command,log=str(logfile),formal_workers=0)
            atomic(last,result); print(json.dumps(result))
    elif a.action=="run":
        signal.signal(signal.SIGTERM,stop_signal)
        control(out)
    elif a.action=="status":
        state=read(out/"PROGRESS.json")
        launch=out/"LAUNCH.json"
        if launch.is_file():
            state["controller_live"]=resources.same_process(read(launch)["identity"])
            if not state["controller_live"] and state["state"]=="RUNNING":
                state["observed_state"]="INTERRUPTED"
        print(json.dumps(state,indent=2,ensure_ascii=False))
    elif a.action=="stop":
        if not (out/"LAUNCH.json").is_file() or not resources.same_process(read(out/"LAUNCH.json")["identity"]):
            raise ValueError("NO_LIVE_REGISTERED_CONTROLLER")
        atomic(out/"STOP_REQUESTED.json",dict(requested_at=now(),mode="drain current batch; do not launch next"))
        print("STOP_REQUESTED_AFTER_CURRENT_BATCH")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
