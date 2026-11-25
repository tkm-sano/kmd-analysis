#!/usr/bin/env python3
"""Revised, manifest-bound D3 pilot, registration and execution entry."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[name]='1'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('register','run','resume','preflight','aggregate','freeze','_branch','_classical','_environment'))
    p.add_argument('--stage',choices=('pilot','formal','diagnostic'))
    p.add_argument('--output',type=Path)
    p.add_argument('--benchmark',type=Path)
    p.add_argument('--legacy',type=Path)
    p.add_argument('--job',type=Path)
    p.add_argument('--evidence',type=Path)
    p.add_argument('--role',choices=('classical','branch'))
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    from kmd_toc.iterative_d3 import revision as rev
    if a.action=='_environment':
        result=rev.fingerprint(a.role)
    elif a.action in ('_branch','_classical'):
        return rev.worker(a.job,a.action)
    else:
        if a.output is None:
            p.error('--output is required')
        if a.action=='register':
            if a.stage is None or a.legacy is None:
                p.error('register requires --stage and --legacy')
            result=rev.register(a.output,a.stage,a.legacy,benchmark=a.benchmark)
        elif a.action in ('run','resume'):
            if not a.execute:
                p.error('run and resume require --execute')
            result=rev.execute(a.output,resume=a.action=='resume')
        elif a.action=='freeze':
            if a.evidence is None:
                p.error('freeze requires --evidence')
            result=rev.freeze(a.output,a.evidence)
        else:
            result={'preflight':rev.preflight,'aggregate':rev.aggregate}[a.action](a.output)
    print(json.dumps(result,ensure_ascii=False))
    return 2 if result.get('state','').startswith(('HOLD','INTERRUPTED','FAILED')) else 0


if __name__=='__main__':
    raise SystemExit(main())
