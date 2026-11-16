#!/usr/bin/env python3
"""Whole-method A_rule_v1/B/C/D comparison, including method loading decisions.

Does not isolate a quantum causal effect or represent observed operator results.
Requires an explicit common wall cap per case; historical DWT is unchanged.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['register','run','aggregate'])
    parser.add_argument('--plan')
    parser.add_argument('--registration')
    parser.add_argument('--output')
    parser.add_argument('--authorize-formal-experiment',action='store_true',
        help='Separate explicit authorization; not used by contract checks')
    args=parser.parse_args()
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    if args.action=='register':
        if not args.plan or not args.output:parser.error('--plan and --output required')
        from kmd_toc.comparison_v1.contract import register
        print(register(args.plan,args.output))
    elif args.action=='run':
        if not args.registration:parser.error('--registration required')
        from kmd_toc.comparison_v1.execution import run_registered
        rows=run_registered(args.registration,allow_formal=args.authorize_formal_experiment)
        return 0 if all(r['adoptable'] for r in rows) else 1
    else:
        if not args.registration or not args.output:parser.error('--registration and --output required')
        from kmd_toc.comparison_v1.evaluation import aggregate
        print(json.dumps(aggregate(args.registration,args.output),ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    sys.exit(main())
