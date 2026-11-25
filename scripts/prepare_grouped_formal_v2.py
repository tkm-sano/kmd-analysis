#!/usr/bin/env python3
"""Bind the 90 grouped comparison cases and assess launch evidence without launching."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from kmd_toc.iterative_v3.io import dump,read,sha

OLD=ROOT/"output/iterative_d3/formal_J30_v4"
VERSION="grouped-loading-20261124-v2"


def environment(executable):
    probe="""import importlib.metadata as m, json, platform, sys
names = ('numpy','scipy','ortools','qiskit','qiskit-aer')
installed = {d.metadata['Name'].lower():d.version for d in m.distributions()}
print(json.dumps(dict(executable=sys.executable, version=sys.version, platform=platform.platform(),
    packages={n:installed.get(n) for n in names})))"""
    return json.loads(subprocess.check_output([executable,"-B","-c",probe],text=True))


def source_path(pilot,scale):
    managed=pilot/scale/"B/plan.json"
    if (pilot/scale/"B/RESULT.json").is_file() and managed.is_file():return managed,"managed"
    return pilot/f"{scale}_B.json","development_reproducible_candidate"


def prepare(pilot,out,verification=None,certify=False):
    frozen=read(OLD/"FREEZE_RECORD.json")
    if sha(OLD/"MANIFEST.json")!=frozen["manifest_sha256"]:raise ValueError("OLD_REGISTRATION_CHANGED")
    old,p=read(OLD/"MANIFEST.json"),read(pilot/"MANIFEST.json")
    if p["version"]!=VERSION or p["stage"]!="pilot":raise ValueError("NOT_GROUPED_PILOT")
    fixed={}
    for scale in ("S1","S2","S3"):
        src,status=source_path(pilot,scale)
        if src.exists():
            plan=read(src)
            fixed[scale]=dict(source=str(src),source_role=status,plan_sha256=sha(src),physical_hash=plan["physical_hash"],
                              problem_hash=plan["base_problem_hash"],od_hash=plan["od_hash"],group_calls=plan["calls_s"])
    if len(old["cases"])!=90 or Counter(c["scale"] for c in old["cases"])!={"S1":30,"S2":30,"S3":30}:
        raise ValueError("FORMAL_J_CHANGED")
    cases=[dict(trial_id=c["trial_id"],scale=c["scale"],outer_index=c["outer_index"],input=c["input"],
                problem_hash=c["problem_hash"],od_hash=c["od_hash"],context=c["context"],seed=c["seed"],
                C_seed=c["C_seed"],branch_seeds=c["branch_seeds"],
                initial_plan_sha256=fixed.get(c["scale"],{}).get("plan_sha256")) for c in old["cases"]]
    code={str(x.relative_to(ROOT)):sha(x) for x in (Path(__file__).resolve(),
        ROOT/"scripts/audit_grouped_loading_v2.py",ROOT/"scripts/plot_grouped_pilot_v2.py",
        ROOT/"scripts/run_grouped_formal_v2.py")}
    audit=read(verification/"RECHECK.json") if verification and (verification/"RECHECK.json").exists() else {}
    complete=(pilot/"COMPLETE.json").is_file()
    gaps=[]
    if not complete or audit.get("validated_plans")!=12:gaps.append("FULL_PILOT_AND_INDEPENDENT_12_PLAN_EVIDENCE")
    if len(fixed)!=3 or any(x["source_role"]!="managed" for x in fixed.values()):gaps.append("THREE_MANAGED_PILOT_B_PLANS")
    if not (pilot/"MIRROR_CANDIDATE.json").is_file():gaps.append("VERIFIED_REPRODUCTION_MIRROR")
    tests=(pilot/"TESTS.txt").read_text() if (pilot/"TESTS.txt").is_file() else ""
    if "16 passed" not in tests:gaps.append("RECEPTION_AND_RESUME_TESTS")
    if not (pilot/"FORMAL_REPORT_FIXTURE.json").is_file() or read(pilot/"FORMAL_REPORT_FIXTURE.json").get("status")!="PASS":
        gaps.append("FORMAL_REPORT_REGRESSION")
    if not certify:gaps.append("APPROVED_FORMAL_MIRROR_AND_REGISTERED_PREFLIGHT")
    m=dict(version=VERSION,state="DRAFT_ONLY",formal_activation=False,formal_workers=0,formal_observations=0,
           comparison_cases=90,formal_J=30,paired=True,C_runs=90,D_branch_jobs=720,solver_jobs=810,
           seed_version=old["rng_version"],seed_table=dict(source=str(OLD/"SEEDS.csv"),sha256=sha(OLD/"SEEDS.csv")),
           inherited_formal_sha256=frozen["manifest_sha256"],pilot_manifest_sha256=sha(pilot/"MANIFEST.json"),
           comparison_keys=old["configuration"]["statistics"],cases=cases,fixed_initials=fixed,
           grouped_conditions=p["grouped_conditions"],configuration=p["configuration"],
           classical_configuration=p["classical_configuration"],
           input_hashes={k:v for k,v in old["asset_hashes"].items()
                         if any(k.startswith(c["input"]+"/") for c in p["cases"])},
           code_hashes=p["code_hashes"]|code,environment={role:environment(p["configuration"][f"{role}_python"])
                                                        for role in ("classical","branch")},
           host=platform.node(),readiness_blockers=gaps)
    out.mkdir(parents=True,exist_ok=False)
    if certify and not gaps:
        checked=audit["source_sha256"]
        for f,h in checked.items():
            if sha(f)!=h:raise ValueError("PILOT_EVIDENCE_CHANGED")
        for scale,reference in fixed.items():
            target=out/scale/"B"/"plan.json"
            target.parent.mkdir(parents=True)
            shutil.copyfile(reference["source"],target)
            target.chmod(0o444)
        m.update(stage="formal",state="NOT_STARTED",formal_activation=True)
        shutil.copyfile(OLD/"SEEDS.csv",out/"SEEDS.csv")
        dump(out/"MANIFEST.json",m)
        dump(out/"FREEZE_RECORD.json",dict(status="GO",manifest_sha256=sha(out/"MANIFEST.json"),
            independent_audit_sha256=sha(verification/"RECHECK.json"),formal_workers=0))
        for name in ("MANIFEST.json","FREEZE_RECORD.json","SEEDS.csv"):(out/name).chmod(0o444)
        print(json.dumps({"status":"REGISTERED_NOT_STARTED","cases":90,"formal_workers":0}))
        return 0
    dump(out/"MANIFEST_DRAFT.json",m)
    receipt=dict(status="HOLD",worker_permission=False,draft_sha256=sha(out/"MANIFEST_DRAFT.json"),
                 blockers=gaps,verified_pilot_plans=audit.get("validated_plans",0),formal_workers_submitted=0,
                 formal_valid_observations=0,formal_case_count=90)
    dump(out/"PREFLIGHT.json",receipt)
    print(json.dumps(receipt))
    return 2


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pilot",type=Path);cli.add_argument("output",type=Path)
    cli.add_argument("--audit",type=Path)
    cli.add_argument("--certify",action="store_true")
    a=cli.parse_args()
    raise SystemExit(prepare(a.pilot,a.output,a.audit,a.certify))
