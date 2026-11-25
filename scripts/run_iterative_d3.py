#!/usr/bin/env python3
"""Register, validate and run the versioned D3 study."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
for variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register','register-pilot','pilot','preflight','readiness',
                                          'freeze','run','resume','aggregate','_branch','_classical'))
    parser.add_argument('--config',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--job',type=Path)
    parser.add_argument('--execute',action='store_true')
    args = parser.parse_args()
    from kmd_toc.iterative_d3 import campaign
    from kmd_toc.iterative_v3.io import read
    if args.action == '_branch':
        return campaign.branch(read(args.job))
    if args.action == '_classical':
        with campaign.entry_binding():
            return campaign.runtime.classical_worker(read(args.job))
    if args.output is None:
        parser.error('--output is required')
    if args.action in ('register','register-pilot'):
        if args.config is None:
            parser.error('--config is required')
        if args.action=='register':
            result=campaign.register(args.config,args.output)
            result=dict(status='REGISTERED',cases=len(result['cases']),workers_submitted=0)
        else:
            result=campaign.register_pilot(args.config,args.output)
    else:
        if args.manifest is None:
            parser.error('--manifest is required')
        if args.action == 'pilot':
            if not args.execute:
                parser.error('--execute is required for the registered pilot')
            result=campaign.execute_pilot(args.manifest,args.output)
        elif args.action in ('run','resume'):
            result=campaign.execute_formal(args.manifest,args.output,args.execute)
        elif args.action == 'aggregate':
            from kmd_toc.iterative_v3_study import analysis
            from kmd_toc.iterative_v3.io import dump
            # The aggregator retains the existing D/W cohort and MCSE contract.
            analysis.preflight=campaign.preflight
            result=analysis.aggregate(args.manifest,args.output)
            dump(Path(result['output'])/'EXTERNAL_REFERENCE_A.json',dict(status='HOLD',display='reference availability note only',
                reason='Administrative parcel and trip conversions and the wait measurement scope are unconfirmed.'))
        else:
            function=dict(preflight=campaign.preflight,readiness=campaign.formal_state,freeze=campaign.freeze)[args.action]
            result=function(args.manifest,args.output)
    print(json.dumps(result,ensure_ascii=False,default=str))
    return 2 if isinstance(result,dict) and result.get('status') in ('PARTIAL','INTERRUPTED_OR_FAILED') else 0


if __name__=='__main__':
    raise SystemExit(main())
