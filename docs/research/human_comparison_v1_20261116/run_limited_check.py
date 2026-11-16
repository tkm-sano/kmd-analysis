#!/usr/bin/env python3
"""Scripted fixture only. Never use this script to manufacture human observations."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.human_comparison_v1.contract import CONTRACT,FILES,digest,dump,read
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.common.models import save_problem


def main():
 out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
 source=out/'input';save_problem(artificial_problem(12,4,1),source)
 plan={'experiment_id':out.name,'mode':'human_inclusive','measurement_contract':CONTRACT,
  'phase':'contract_check','preparation_policy':'no_case_view_or_case_specific_tuning_before_start',
  'tuning_policy':'frozen_existing_BCD_no_case_tuning','stopping':'fixed_registered_runs',
  'memory_limit_MiB':8192,'python':sys.executable,
  'dependency_prefix':'/opt/miniconda/envs/qgpu/lib/python3.12/site-packages',
  'participants':{'SCRIPTED_NOT_HUMAN':{'experience':'No human experiment: scripted fixture',
   'tools':[{'name':'scripted fixture','version':'1'}],'pc':{'os':'Linux','description':'test host'},
   'procedure':'fixed artificial CSV; not observed human decisions','planned_date':'2026-11-16',
   'activity_recording':'participant_markers'}},
  'cases':[{'case_id':'fixture12','scenario_id':'ART12_ONLY','scale':'ART_N12','kind':'synthetic_validation',
   'input_dir':str(source),'files':{f:digest(source/f) for f in FILES},'family_id':'fixture12',
   'independent_draw':False,'demand_seed':None,'total_limit_s':240,'machine_limit_s':200,'native_limit_s':45}],
  'runs':[{'run_id':m+'_path_check','case_id':'fixture12','method':m,'repetition':1,'order_index':i,
   'max_attempts':2 if m=='A' else 1,'workflow':'human' if m=='A' else 'system_only',
   'participant_id':'SCRIPTED_NOT_HUMAN' if m=='A' else None,'prior_exposure_expected':False,
   'solver_seed':None if m=='A' else 20261116,'quantum_seed':20261117 if m=='D' else None,
   'analysis_role':'primary'} for i,m in enumerate('ABCD')],
  'statistics':{'scope':'fixed_cases','ci_method':'descriptive','confidence':.95,
   'pairs':[['A','D'],['C','D']],'rationale':'actual small code paths; synthetic observations excluded from empirical inference'}}
 assert plan['phase']=='contract_check'
 dump(out/'LIMITED_VALIDATION_PLAN.json',{'max_total_s':960,'formal_experiment':False,
  'methods_run_sequentially':True,'plan':plan,'automatic_human_input':'fixture only; observed=false'})
 dump(out/'plan.json',plan)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 calls=[]
 def cli(*args):
  command=[sys.executable,'-B',str(ROOT/'scripts/run_human_comparison_v1.py'),'--mode','human_inclusive',*map(str,args)]
  result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=260)
  calls.append({'argv':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
  dump(out/f'CLI_{len(calls):03}.json',calls[-1])
  print(args[0],result.returncode,result.stdout.strip(),flush=True)
  return result.returncode
 cli('register','--plan',out/'plan.json','--output',out/'registration')
 reg=out/'registration/REGISTERED.json';a=out/'A'
 if reg.exists():
  cli('prepare','--registration',reg,'--run-id','A_path_check','--output',a)
  cli('start','--session',a,'--confirm-unseen')
  if not (a/'RESULT.json').exists():
   cli('activity','--session',a,'--state','begin','--task','assignment_order','--actor','SCRIPTED_NOT_HUMAN')
   # This is deliberately artificial test data, not an observation of a participant.
   with (a/'assignment.csv').open('w') as f:
    f.write('vehicle_id,sequence,stop_id\n')
    for v in range(4):
     for j in range(3):f.write(f'v{v},{j+1},c{v*3+j+1:04}\n')
   cli('evaluate','--session',a)
   cli('activity','--session',a,'--state','begin','--task','review','--actor','SCRIPTED_NOT_HUMAN')
   if cli('accept','--session',a,'--attest-human-authored','--attest-reviewed'):
    if not (a/'RESULT.json').exists():cli('abort','--session',a,'--reason','FIXTURE_FAILED')
  for method in 'BCD':
   cli('run-system','--registration',reg,'--run-id',method+'_path_check','--output',out/method)
  for method in 'ABCD':
   if (out/method/'RESULT.json').exists():cli('verify','--registration',reg,'--session',out/method)
  cli('aggregate','--registration',reg,'--output',out/'aggregate')
  cli('adopt','--registration',reg,'--output',out/'ADOPTION.json')
 dump(out/'CLI_CALLS.json',calls)


if __name__=='__main__':main()
