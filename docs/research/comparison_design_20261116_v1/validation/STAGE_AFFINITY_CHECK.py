import sys,json,tempfile,os
from pathlib import Path
sys.path.insert(0,'scripts');sys.path.insert(0,'src')
from unittest.mock import patch
from run_comparison_design import stage
from kmd_toc.comparison_v1.contract import dump
original=set(os.sched_getaffinity(0));cpus=sorted(original)[:4]
root=Path(tempfile.mkdtemp(prefix='kmd-stage-affinity-'))
plan={'design_extension':{}}
def registration(plan_path,out):
 out.mkdir();dump(out/'REGISTERED.json',{'cpu_profile':{'cpu_ids':cpus}});return out/'REGISTERED.json'
def runner(path):os.sched_setaffinity(0,{cpus[0]})
def aggregation(path,out):
 out.mkdir();dump(out/'ALL_ATTEMPTS.json',{'rows':[]})
try:
 with patch('kmd_toc.comparison_v1.contract.register',registration),patch('kmd_toc.comparison_v1.execution.run_registered',runner),patch('kmd_toc.comparison_v1.evaluation.aggregate',aggregation):
  stage(root,'first',plan)
 assert set(os.sched_getaffinity(0))==set(cpus)
 print('post-stage CPU allocation restored; no timed method executed')
finally:os.sched_setaffinity(0,original)
