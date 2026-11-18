#!/usr/bin/env python3
"""Explicit legacy_program_only / human_inclusive comparison modes."""

# 2026-11-17: this entry point retains the historical timing-based contract.
# Check before imports so rejection cannot initialize solvers or write files.
if __name__ == "__main__":
    import sys as _history_sys
    if "--historical-reproduction" in _history_sys.argv:
        _history_sys.argv.remove("--historical-reproduction")
    elif any(arg in _history_sys.argv for arg in ("--help", "-h")):
        print("Historical entry point. Current analysis: scripts/analyze_dw.py. "
              "Use --historical-reproduction --help for the previous command options.")
        raise SystemExit(0)
    else:
        raise SystemExit("HISTORICAL_ENTRYPOINT: use scripts/analyze_dw.py for current D/W analysis; "
                         "pass --historical-reproduction only to reproduce the previous study")

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ENTRY_NS=time.monotonic_ns()
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
 for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
 first=argparse.ArgumentParser(add_help=False)
 first.add_argument('--mode',required=True,choices=['legacy_program_only','human_inclusive'])
 opts,rest=first.parse_known_args()
 if opts.mode=='legacy_program_only':
  return subprocess.call([sys.executable,'-B',str(ROOT/'scripts/run_comparison_v1.py'),*rest],cwd=ROOT)
 from kmd_toc.human_comparison_v1 import session as s
 from kmd_toc.human_comparison_v1.contract import register,read,dump,load_registration
 from kmd_toc.human_comparison_v1.analysis import aggregate,adoption,verify_session
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
 q=sub.add_parser('register');q.add_argument('--plan',required=True);q.add_argument('--output',required=True)
 q=sub.add_parser('prepare');q.add_argument('--registration',required=True);q.add_argument('--run-id',required=True);q.add_argument('--output',required=True);q.add_argument('--authorize-observation',action='store_true')
 q=sub.add_parser('start');q.add_argument('--session',required=True);q.add_argument('--confirm-unseen',action='store_true');q.add_argument('--confirm-registered-repeat',action='store_true')
 q=sub.add_parser('activity');q.add_argument('--session',required=True);q.add_argument('--state',choices=['begin','end'],required=True);q.add_argument('--task',choices=['assignment_order','input_operation','review','correction','pause'],required=True);q.add_argument('--actor',required=True)
 q=sub.add_parser('evaluate');q.add_argument('--session',required=True)
 q=sub.add_parser('accept');q.add_argument('--session',required=True);q.add_argument('--attest-human-authored',action='store_true');q.add_argument('--attest-reviewed',action='store_true')
 for action in ('abort','recover'):
  q=sub.add_parser(action);q.add_argument('--session',required=True);q.add_argument('--reason',required=True)
 q=sub.add_parser('verify');q.add_argument('--registration',required=True);q.add_argument('--session',required=True)
 q=sub.add_parser('aggregate');q.add_argument('--registration',required=True);q.add_argument('--output',required=True)
 q=sub.add_parser('adopt');q.add_argument('--registration',required=True);q.add_argument('--output',required=True)
 q=sub.add_parser('run-system');q.add_argument('--registration',required=True);q.add_argument('--run-id',required=True);q.add_argument('--output',required=True);q.add_argument('--authorize-observation',action='store_true')
 a=p.parse_args(rest)
 try:
  if a.action=='register':result=str(register(a.plan,a.output))
  elif a.action=='prepare':result=str(s.prepare(a.registration,a.run_id,a.output,authorize_observation=a.authorize_observation))
  elif a.action=='run-system':
   reg=load_registration(a.registration);r=next(r for r in reg['runs'] if r['run_id']==a.run_id)
   if r['workflow']!='system_only':raise ValueError('AUTOMATION_MUST_NOT_CREATE_HUMAN_PLANS')
   out=s.prepare(a.registration,a.run_id,a.output,authorize_observation=a.authorize_observation)
   first_result=s.start(out)
   if (out/'RESULT.json').exists():result=first_result
   else:
    attempt=s.attempt(out)
    if (out/'RESULT.json').exists():result=attempt
    else:result=s.accept(out) if attempt.get('result',{}).get('validated') and attempt.get('cleanup_proved') else s.abort(out,s.failure_status(attempt))
  elif a.action=='start':result=s.start(a.session,confirm_unseen=a.confirm_unseen,confirm_registered_repeat=a.confirm_registered_repeat)
  elif a.action in ('activity','evaluate','accept','abort'):
   s.command_enter(a.session,ENTRY_NS)
   if a.action=='activity':result=s.activity(a.session,a.state=='begin',a.task,a.actor)
   elif a.action=='evaluate':result=s.attempt(a.session)
   elif a.action=='accept':result=s.accept(a.session,attest_human=a.attest_human_authored,attest_reviewed=a.attest_reviewed)
   else:result=s.abort(a.session,a.reason)
  elif a.action=='recover':result=s.recover(a.session,a.reason)
  elif a.action=='verify':result=verify_session(a.session,load_registration(a.registration))
  elif a.action=='aggregate':result=aggregate(a.registration,a.output)
  else:
   reg=load_registration(a.registration);summary=aggregate(a.registration,None);result=adoption(reg,summary);dump(a.output,result)
  # Keep CLI output compact; detailed traces stay in evidence files.
  if isinstance(result,dict):
   print(json.dumps({k:result.get(k) for k in ('status','run_id','T_total_sec','MEASURED','COMPARABLE','formal_adoption') if k in result},ensure_ascii=False))
  else:print(result)
  if isinstance(result,dict) and result.get('status') not in (None,'success'):return 1
  if a.action=='evaluate' and isinstance(result,dict) and not result.get('result',{}).get('validated'):return 1
  return 0
 except Exception as e:
  print(type(e).__name__+': '+str(e),file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
