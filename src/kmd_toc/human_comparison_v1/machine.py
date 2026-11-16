"""Fresh timed subprocess: unchanged method code plus observational spans."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time
import resource
import platform

from .contract import dump,read,load_case,require,verify_sources,digest,fingerprint

_ORIGINAL_BRANCH=None


def observed_branch(spec,out,cpu,go,deadline,ready):
 """Transparent top-level branch adapter; works with fork and spawn."""
 from kmd_toc.dwt import methods
 from kmd_toc.column_generation import aoa
 from kmd_toc.dwt.parallel import _branch_entry
 original=_ORIGINAL_BRANCH if _ORIGINAL_BRANCH is not None else _branch_entry
 if spec.get('registered_case'):
  from .inputs import load_registered_scenario
  import kmd_toc.common.models as models
  import kmd_toc.dwt.worker as worker
  models.load_problem=lambda path:load_registered_scenario(path,spec['registered_case'])
  worker.load_problem=models.load_problem
 out=Path(out);counter=[0]
 def observe(fn,label):
  def wrapped(*args,**kwargs):
   i=counter[0];counter[0]+=1;start=time.monotonic_ns()
   # Preserve starts even if the branch is forcibly killed.
   dump(out/f'observation_{i:04}_start.json',{'event':label,'start_ns':start,'pid':os.getpid()})
   try:return fn(*args,**kwargs)
   finally:dump(out/f'observation_{i:04}_end.json',{'event':label,'start_ns':start,
           'end_ns':time.monotonic_ns(),'pid':os.getpid()})
  return wrapped
 methods.generate=observe(methods.generate,'algorithm_generate_including_completion')
 aoa.minimize=observe(aoa.minimize,'parameter_optimization_including_objective_simulation')
 from kmd_toc.pipeline.hybrid import EventDayMaster
 EventDayMaster.lp=observe(EventDayMaster.lp,'classical_master_LP')
 EventDayMaster.ip=observe(EventDayMaster.ip,'classical_master_IP')
 methods.complete_routes=observe(methods.complete_routes,'classical_CP_SAT_completion')
 methods.routing_pool=observe(methods.routing_pool,'classical_OR_Routing')
 aoa.PricingAOA.execution_state=observe(aoa.PricingAOA.execution_state,'simulator_final_circuit_build_and_evolution')
 original(spec,str(out),cpu,go,deadline,ready)


def quantum_and_compute(native_dir,native):
 from .evaluation import union_seconds
 spans=[];missing=[];parameter=[];components=[];branches=[]
 for b in sorted((native_dir/'branches').glob('*')):
  starts=[read(p) for p in b.glob('observation_*_start.json') if read(p)['event']=='algorithm_generate_including_completion']
  ends=[read(p) for p in b.glob('observation_*_end.json') if read(p)['event']=='algorithm_generate_including_completion']
  if len(starts)!=1 or len(ends)!=1:missing.append(b.name)
  else:spans.append((ends[0]['start_ns'],ends[0]['end_ns']))
  parameter.extend(read(p) for p in b.glob('observation_*_end.json') if read(p)['event'].startswith('parameter_optimization'))
  components.extend(read(p) for p in b.glob('observation_*_end.json') if read(p)['event'].startswith(('classical_','simulator_')))
  result=b/'worker_result.json'
  if result.exists():
   r=read(result);branches.append({'branch':b.name,'pid':r['worker_pid'],'seed':r['solver_seed'],
    'quantum_seed':r.get('quantum_seed'),'status':r['status'],'timing_events':r['timing_events'],
    'quantum':r.get('plan',{}).get('method_settings',{}).get('quantum',[]) if r.get('plan') else [],
    'affinity':r.get('cpu_affinity'),'CPU_sec':r.get('process_cpu_s'),'max_RSS_KiB':r.get('max_rss_KiB')})
 return {'T_compute_sec':union_seconds(spans) if len(spans)==4 and not missing else None,
    'T_compute_reason':'OBSERVED_UNION_OF_FOUR_ALGORITHM_SPANS' if len(spans)==4 and not missing else 'INCOMPLETE_ALGORITHM_OBSERVATION',
    'compute_spans_ns':spans,'missing_branches':missing,'native_result_status':native['status'],
    'D_component_timings':{'backend':native.get('quantum_backend_environment'),
      'observed_quantum_timing_s':native.get('observed_quantum_timing_s'),
      'quantum_timing_scope':'native per-call/branch sums; overlapping components, never substitute for parent wall',
      'parameter_optimization_spans':parameter,'parameter_optimization_includes_objective_simulation':True,
      'classical_and_simulator_component_spans':components,
      'complete_quantum_accounting':native.get('quantum_accounting_complete'),
      'all_branch_evidence':branches,'real_quantum_hardware_used':False}}


def main():
 global _ORIGINAL_BRANCH
 job=read(sys.argv[1]);out=Path(job['out']);reg=job['registration'];run=job['run'];case=job['case']
 for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
 os.sched_setaffinity(0,{reg['cpu_ids'][0]} if run['method']=='A' else set(reg['cpu_ids']))
 if run['method']=='A':resource.setrlimit(resource.RLIMIT_AS,(4096*1048576,4096*1048576))
 verify_sources(reg)
 before=time.monotonic_ns();problem=load_case(reg,case);input_end=time.monotonic_ns()
 from .evaluation import evaluate
 from kmd_toc.common.models import load_plan
 plan=None;compute={'T_compute_sec':None,'T_compute_reason':'HUMAN_ASSIGNMENT_ORDER_NOT_ALGORITHM_TIME'}
 if job['action']=='input':
  import csv
  with (out/'stops.csv').open('x') as f:
   w=csv.writer(f);w.writerow(['stop_id','longitude','latitude','demand']);w.writerows(
    (s.stop_id,s.longitude,s.latitude,s.demand) for s in problem.stops)
  dump(out/'vehicles.json',[asdict(v) for v in problem.vehicles])
 elif job['action']=='final':
  plan=load_plan(job['plan_path'])
 elif run['method']=='A':
  from kmd_toc.baseline_a.human_v1 import complete_manual
  plan,_=complete_manual(problem,Path(job['csv_path']).read_text())
 else:
  from kmd_toc.dwt import parallel
  _ORIGINAL_BRANCH=parallel._branch_entry;parallel._branch_entry=observed_branch
  if case['kind']=='registered_scenario':
   from .inputs import load_registered_scenario
   import kmd_toc.common.models as models
   models.load_problem=lambda path:load_registered_scenario(path,case)
  native_dir=out/'native';native_dir.mkdir()
  spec={'trial_id':run['run_id']+f"_attempt{job['attempt']}",'scenario_id':case['scenario_id'],
   'instance_id':case['case_id'],'method':run['method'],'repetition_id':run['repetition'],
   'phase':reg['phase'],'epsilon_W_min':None,'tau_s':case['native_limit_s'],
   'input_dir':case['input_dir'],'registered_input_hash':problem.fingerprint,
   'registered_OD_hash':problem.od.fingerprint,'config':reg['BCD_config'],
   'config_sha256':fingerprint(reg['BCD_config']),'design_telemetry':True,
   'registered_case':case if case['kind']=='registered_scenario' else None,
   'execution_cpu_profile':{'mode':'parallel_multistart','workers':4,'cpu_ids':reg['cpu_ids'],
       'native_threads_per_branch':1,'coordinator_reserve_fraction':.2},
   'seeds':{'solver_seed':run['solver_seed'],'quantum_seed':run.get('quantum_seed'),'validation_seed':None}}
  native=parallel.execute_parallel(spec,native_dir,allow_import_only_fork=True)
  dump(out/'native_summary.json',{k:v for k,v in native.items() if k!='plan'})
  compute=quantum_and_compute(native_dir,native)
  if native.get('plan'):plan=parallel._plan(native['plan'])
  if native['status']!='VALIDATED':
   # Keep a native diagnostic plan, but do not retroactively promote a late plan.
   if plan:dump(out/'diagnostic_plan.json',asdict(plan))
   dump(out/'RESULT.json',{'validated':False,'native_status':native['status'],**compute,
       'input_sec':(input_end-before)/1e9,'problem_hash':problem.fingerprint,'OD_hash':problem.od.fingerprint})
   return 1
 report={'validated':False}
 if plan:
  algorithm_end=time.monotonic_ns()
  manual=Path(job['csv_path']).read_text() if run['method']=='A' else None
  report=evaluate(problem,plan,human_csv=manual)
  dump(out/'plan.json',asdict(plan));dump(out/'validation.json',report)
  if run['method']=='A':
   from kmd_toc.baseline_a.human_v1 import manual_groups
   report['manual_csv_sha256']=digest(job['csv_path'])
  compute['validation_sec']=(time.monotonic_ns()-algorithm_end)/1e9
 dump(out/'RESULT.json',{**report,**compute,'input_sec':(input_end-before)/1e9,
     'problem_hash':problem.fingerprint,'OD_hash':problem.od.fingerprint,
     'plan_sha256':digest(out/'plan.json') if plan else None,
     'pid':os.getpid(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
     'process_CPU_sec':time.process_time(),'max_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'environment':{'python':sys.version,'platform':platform.platform(),
       'native_thread_limits':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
       'loaded_libraries':{name:{'version':getattr(sys.modules[name],'__version__',None),
            'path':getattr(sys.modules[name],'__file__',None)} for name in ('numpy','scipy','ortools','qiskit','verypy') if name in sys.modules}}})
 return 0 if job['action']=='input' or report['validated'] else 1


if __name__=='__main__':
 try:sys.exit(main())
 except Exception as error:
  import traceback
  traceback.print_exc()
  job=read(sys.argv[1]);path=Path(job['out'])/'ERROR.json'
  if not path.exists():dump(path,{'type':type(error).__name__,'message':str(error)})
  sys.exit(2)
