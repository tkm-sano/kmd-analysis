#!/usr/bin/env python3
"""Evaluate saved plans under FCFS_v1. Never repair inputs silently or run solvers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True)
    parser.add_argument('--plan',action='append',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    from kmd_toc.common.models import load_problem,load_plan
    from kmd_toc.fcfs_v1.evaluation import evaluate
    paths=[Path(p).resolve() for p in args.plan];source=Path(args.input).resolve();out=Path(args.output).resolve()
    if out.exists() or source==out or source in out.parents or out in source.parents or any(out==p or out in p.parents for p in paths):
        raise ValueError('SEPARATE_NEW_OUTPUT_REQUIRED')
    p=load_problem(source);reports=[]
    for path in paths:
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        plan=load_plan(path)
        result=evaluate(p,plan)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=before:
            raise ValueError('PLAN_CHANGED_DURING_FCFS_EVALUATION')
        reports.append({**result,'plan_path':str(path),'plan_sha256':before})
    if len({r['source_plan_operating_policy'] for r in reports})>1:
        raise ValueError('MIXED_HISTORICAL_AND_FCFS_V1_PLANS_FORBIDDEN')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'EVALUATION.json').open('x') as f:
        json.dump({'operating_policy':'FCFS_v1','plans':reports,'main_experiment':'HOLD',
                   'statistical_hypothesis':'NOT_TESTED','A':'external_reference_not_subject_to_FCFS'},f,
                  ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({'operating_policy':'FCFS_v1','plans':len(reports),'main_experiment':'HOLD'}))


if __name__=='__main__':main()
