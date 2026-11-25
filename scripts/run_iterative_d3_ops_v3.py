#!/usr/bin/env python3
"""Public entry point for the hash-bound D3 operations revision."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS"):
    os.environ[name]="1"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("register","preflight","aggregate","freeze","run","resume",
                                        "_environment","_guard","_branch","_classical","_dummy"))
    parser.add_argument("--output",type=lambda p:Path(p).resolve())
    parser.add_argument("--evidence",type=lambda p:Path(p).resolve())
    parser.add_argument("--job",type=lambda p:Path(p).resolve())
    parser.add_argument("--intent",type=lambda p:Path(p).resolve())
    parser.add_argument("--role",choices=("classical","branch"))
    parser.add_argument("--execute",action="store_true")
    a=parser.parse_args()
    from kmd_toc.iterative_d3_ops import resources
    if a.action=="_guard":
        return resources.guard(a.intent)
    from kmd_toc.iterative_d3_ops import operation as op
    if a.action in ("_branch","_classical","_dummy"):
        return op.worker(a.job,a.action)
    if a.action=="_environment":
        result=op.rev.fingerprint(a.role)
    else:
        if a.output is None:
            parser.error("--output is required")
        try:
            if a.action in ("run","resume"):
                if not a.execute:
                    parser.error("run/resume require --execute")
                result=op.execute(a.output,resume=a.action=="resume")
            elif a.action=="freeze":
                if a.evidence is None:
                    parser.error("--evidence is required")
                result=op.freeze(a.output,a.evidence)
            else:
                result=getattr(op,a.action)(a.output)
        except (resources.Unavailable, BlockingIOError) as error:
            result=dict(state="HOLD_RESOURCE",reason=str(error),workers_submitted=0)
    print(json.dumps(result,ensure_ascii=False))
    return 2 if result.get("state","").startswith(("FAILED","HOLD","INTERRUPTED")) or result.get("report_state")=="INVALID_DENOMINATOR" else 0


if __name__=="__main__":
    raise SystemExit(main())
