#!/usr/bin/env python3
"""Grouped D3 pilot runner; formal launches are outside this entry."""
import argparse
import csv
from collections import Counter
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
for env in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS"):
    os.environ[env]="1"

from kmd_toc.duty_break_v1.policy import load_policy
from kmd_toc.grouped_loading_v2 import cp, methods, model, recheck, search
from kmd_toc.iterative_d3 import rng_v2
from kmd_toc.iterative_d3_ops import resources
from kmd_toc.iterative_d3_ops.operation import POLICY
from kmd_toc.iterative_v3.io import decode_routes,dump,load_problem,read,sha,sources,verify_pins
from kmd_toc.iterative_v3_study.analysis import delta

ENTRY=Path(__file__).resolve()
OLD=ROOT/"output/iterative_d3/formal_J30_v4"
PILOT=Path("/tmp/kmd-d3-revised.JtsgfT/pilot")
CONFIG=ROOT/"configs/grouped_loading_20261124_v2/conditions.json"
METHODS=("B","C_Idual","D_classical","D_quantum")


def pins():
    m=read(OLD/"MANIFEST.json")
    return m["code_hashes"]|{str(p.relative_to(ROOT)):sha(p) for p in [ENTRY,CONFIG,
        *(ROOT/"src/kmd_toc/grouped_loading_v2").glob("*.py")]}


def register(out):
    old,prior=read(OLD/"MANIFEST.json"),read(PILOT/"MANIFEST.json")
    if sha(OLD/"MANIFEST.json")!=read(OLD/"FREEZE_RECORD.json")["manifest_sha256"]:
        raise ValueError("FORMAL_PARENT_HASH")
    cfg=read(CONFIG)
    if cfg["loading_s"]!=900 or cfg["reception"]["min_gap_s"]!=1:
        raise ValueError("GROUPED_CONTRACT")
    cases=prior["cases"]
    if len(cases)!=3 or any(x["context"]["stage"]!="pilot" for x in cases):
        raise ValueError("PILOT_CASE_COUNT")
    assets={}
    for case in cases:
        for path in Path(case["input"]).iterdir():
            if path.is_file():
                key=str(path)
                origin=old["asset_hashes"].get(key)
                if origin:
                    actual=sha(path)
                    if actual!=origin:raise ValueError("OLD_ASSET_CHANGED:"+key)
                    assets[key]=actual
    m=dict(version=cfg["version"],stage="pilot",execution_scope="authorized 3 matched pilot cases only",
           formal_worker_jobs=0,registered_comparisons=3,cases=cases,configuration=old["configuration"],
           classical_configuration=old["classical_configuration"],code_hashes=pins(),input_hashes=assets,
           grouped_conditions=cfg,old_formal_sha256=sha(OLD/"MANIFEST.json"),
           old_pilot_source_sha256=sha(PILOT/"MANIFEST.json"))
    out.mkdir(parents=True,exist_ok=True)
    dump(out/"MANIFEST.json",m)
    dump(out/"REGISTRATION.json",dict(manifest_sha256=sha(out/"MANIFEST.json"),formal_workers=0))
    return m


def load_manifest(out):
    p=out/"MANIFEST.json"
    m=read(p)
    if sha(p)!=read(out/"REGISTRATION.json")["manifest_sha256"] or m["stage"]!="pilot":
        raise ValueError("PILOT_MANIFEST_BINDING")
    verify_pins(m["code_hashes"])
    return m


def selected(out,condition,base):
    branch=[read(out/f"branch_{b}"/"plan.json") for b in range(4)]
    i=min(range(4),key=lambda b:model.candidate_key(branch[b],base,branch_id=b))
    return branch[i],i


def publish(where, plan, receipt):
    if (where/"plan.json").exists():
        if read(where/"plan.json")!=plan:raise ValueError("CONTROLLER_PLAN_EXISTS_DIFFERENT")
    else:dump(where/"plan.json",plan)
    dump(where/"RESULT.json",receipt)


def worker(job_path,action):
    lease,binding,_=resources.authorized(Path(os.environ["KMD_D3_LEASE_INTENT"]),worker=True)
    out=Path(lease["output"])
    m=load_manifest(out)
    if binding["job"]!=str(job_path) or sha(out/"MANIFEST.json")!=lease["manifest_sha256"]:
        raise ValueError("GROUPED_JOB_BINDING")
    job=read(job_path)
    case=next(c for c in m["cases"] if c["trial_id"]==job["trial"])
    method=job["method"]
    cfg=m["configuration"]
    p=load_problem(case["input"],cfg["rest_options"])
    duty=load_policy()|{"loading_s":m["grouped_conditions"]["loading_s"]}
    path=Path(job["output"])
    if method=="B":
        if (path/"RESULT.json").exists(): return 0
        start=time.monotonic()
        plan,receipt=methods.generate_b(p,duty)
        publish(path,plan,receipt|dict(status="COMPLETE",wall_s=time.monotonic()-start))
        return 0
    base=read(out/case["scale"]/"B/plan.json")
    if method=="C_Idual":
        if (path/"RESULT.json").exists(): return 0
        start,cpu=time.monotonic(),time.process_time()
        pool,receipt=methods.routing_pool(p,base,m["classical_configuration"],case["C_seed"])
        plan,solver=cp.solve(p,pool,base,m["classical_configuration"],case["C_seed"],duty)
        chosen=min((base,plan),key=lambda q:model.candidate_key(q,base,initial=q is base))
        if not (path/"CP_CANDIDATE.json").exists():dump(path/"CP_CANDIDATE.json",plan)
        publish(path,chosen,dict(status="COMPLETE",initial_hash=base["physical_hash"],routing=receipt,
                cp=solver,started_s=time.time(),wall_s=time.monotonic()-start,cpu_s=time.process_time()-cpu,
                rss_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
        return 0
    b=job["branch"]
    settings=cfg["search"]|{"rng_v2":case["context"]|{"branch":b}}
    search.run(p,base,path,method,settings,case["branch_seeds"][b],b,duty)
    return 0


def controller(out,resume):
    m=load_manifest(out) if (out/"MANIFEST.json").exists() else register(out)
    if (out/"COMPLETE.json").exists():
        return read(out/"COMPLETE.json")
    with resources.acquire(out,sha(out/"MANIFEST.json"),POLICY,m["version"],"pilot_resume" if resume else "pilot") as lease:
        for case in m["cases"]:
            scale=case["scale"]
            for method in METHODS:
                path=out/scale/method
                path.mkdir(parents=True,exist_ok=True)
                if (path/"RESULT.json").exists() and (path/"plan.json").is_file():continue
                branches=range(4) if method.startswith("D_") else (None,)
                jobs=[]
                for b in branches:
                    target=path if b is None else path/f"branch_{b}"
                    target.mkdir(exist_ok=True)
                    if (target/"RESULT.json").exists() and (target/"plan.json").is_file():continue
                    job=target/"JOB.json"
                    spec=dict(trial=case["trial_id"],method=method,branch=b,output=str(target),cpu=b or 0)
                    if job.exists() and read(job)!=spec:raise ValueError("JOB_CHANGED")
                    if not job.exists():dump(job,spec)
                    jobs.append(dict(path=job,action="_branch" if b is not None else "_classical"))
                if jobs:
                    codes,alarm=resources.supervise(lease,ENTRY,jobs,path,m["configuration"])
                    if any(codes) or alarm:
                        raise RuntimeError(f"PILOT_WORKER_FAILED:{scale}:{method}:{codes}:{alarm}")
                if method.startswith("D_"):
                    plan,b=selected(path,method,read(out/scale/"B/plan.json"))
                    publish(path,plan,dict(status="COMPLETE",chosen_branch=b,
                         branches=[read(path/f"branch_{i}"/"RESULT.json") for i in range(4)]))
                print(scale,method,"COMPLETE",flush=True)
        result=dict(status="COMPLETE_PILOT",cases=3,plans=12,formal_workers=0)
        dump(out/"COMPLETE.json",result)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("pilot","resume-pilot","_guard","_branch","_classical"))
    parser.add_argument("--output",type=lambda x:Path(x).resolve())
    parser.add_argument("--job",type=lambda x:Path(x).resolve())
    parser.add_argument("--intent",type=Path)
    a=parser.parse_args()
    if a.action=="_guard":return resources.guard(a.intent)
    if a.action in ("_classical","_branch"):return worker(a.job,a.action)
    if a.output is None or "formal" in a.output.name.lower():parser.error("isolated non-formal output required")
    print(json.dumps(controller(a.output,a.action=="resume-pilot")))
    return 0


if __name__=="__main__":
    sys.exit(main())
