"""Preregistration without opening case payloads or exposing demand to planners."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[3]
CONTRACT='human-inclusive-AD-v1-20261116'
TIME_KIND='input_before_to_common_adoption_total_v1'
FILES=('input.json','od/manifest.json','od/distance_m.npy','od/duration_s.npy','od/reachable.npy')
REGISTRY={
 'A':{'implementation_id':'human_assignment_order_capacity_split_FCFS_v1','method_version':'A_human_v1-20261116'},
 'B':{'implementation_id':'existing_dwt_directed_CW_parallel4','method_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
 'C':{'implementation_id':'existing_dwt_OR_Routing_parallel4','method_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
 'D':{'implementation_id':'existing_dwt_Huang_AOA_parallel4','method_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
}


def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()


def canonical(value):
 return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('DUPLICATE_JSON_KEY:'+k)
   d[k]=v
  return d
 return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
   parse_constant=lambda x:(_ for _ in ()).throw(ValueError('NONFINITE_JSON:'+x)))


def dump(path,value):
 with Path(path).open('x') as f:
  json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def require(value,code):
 if not value:raise ValueError(code)


def positive(x):return type(x) in (int,float) and math.isfinite(x) and x>0
def integer(x):return type(x) is int and x>=0
def now():return datetime.now(timezone.utc).isoformat()


def cpu_ids():
 result=[];seen=set()
 for c in sorted(os.sched_getaffinity(0)):
  p=Path(f'/sys/devices/system/cpu/cpu{c}/topology')
  key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
  if key not in seen:seen.add(key);result.append(c)
  if len(result)==4:return result
 raise ValueError('FOUR_PHYSICAL_CORES_REQUIRED')


def verify_sources(reg):
 for name,h in reg['source_hashes'].items():require(digest(ROOT/name)==h,'SOURCE_HASH_MISMATCH:'+name)
 require(digest(ROOT/'configs/toc_delivery/common_conditions_v1_1.json')==reg['physical_hash'],'PHYSICAL_HASH_MISMATCH')


def validate_plan(p):
 require(p.get('mode')=='human_inclusive','EXPLICIT_HUMAN_INCLUSIVE_MODE_REQUIRED')
 require(p.get('measurement_contract')==CONTRACT,'MEASUREMENT_CONTRACT_MISMATCH')
 require(p.get('phase') in ('contract_check','human_pilot','formal'),'EXPERIMENT_PHASE_REQUIRED')
 require(isinstance(p.get('experiment_id'),str) and p['experiment_id'],'EXPERIMENT_ID_REQUIRED')
 require(p.get('preparation_policy')=='no_case_view_or_case_specific_tuning_before_start','PREPARATION_POLICY_REQUIRED')
 require(p.get('stopping')=='fixed_registered_runs','FIXED_STOPPING_REQUIRED')
 require(isinstance(p.get('cases'),list) and p['cases'],'CASES_REQUIRED')
 require(isinstance(p.get('runs'),list) and p['runs'],'PLANNED_RUNS_REQUIRED')
 require(p.get('tuning_policy')=='frozen_existing_BCD_no_case_tuning','TUNING_POLICY_REQUIRED')
 require(integer(p.get('memory_limit_MiB')) and p['memory_limit_MiB']>0,'MEMORY_LIMIT_REQUIRED')
 cases={c['case_id']:c for c in p['cases']};require(len(cases)==len(p['cases']),'DUPLICATE_CASE')
 require(len({fingerprint(c['files']) for c in cases.values()})==len(cases),'DUPLICATE_INPUT_BUNDLE')
 frozen=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
 for c in cases.values():
  require(all(c.get(k) is not None for k in ('scenario_id','scale','input_dir','files','family_id','kind','independent_draw')),'CASE_IDENTITY_REQUIRED')
  require(set(c['files'])==set(FILES) and all(isinstance(h,str) and len(h)==64 for h in c['files'].values()),'INPUT_FILE_PINS_REQUIRED')
  for k in ('total_limit_s','machine_limit_s','native_limit_s'):
   require(positive(c.get(k)),k.upper()+'_REQUIRED')
  require(c['native_limit_s']<=c['machine_limit_s']<=c['total_limit_s'],'BUDGET_ORDER')
  if c['kind']=='frozen':
   require(c['scale'] in frozen['inputs']['scenarios'],'FROZEN_SCALE')
   require(c['files']==frozen['inputs']['scenarios'][c['scale']]['files'],'FROZEN_INPUT_MISMATCH')
   require(c.get('demand_seed') is None and c['independent_draw'] is False,'FROZEN_DEMAND_NOT_RANDOM_SAMPLE')
  elif c['kind']=='synthetic_validation':require(p['phase']=='contract_check','SYNTHETIC_NOT_EMPIRICAL')
  else:
   require(c['kind']=='registered_scenario' and c.get('generation_manifest') and 'demand_seed' in c,'SCENARIO_PROVENANCE_REQUIRED')
   require(isinstance(c['generation_manifest'],dict) and c['generation_manifest'].get('path') and c['generation_manifest'].get('sha256'),'GENERATION_MANIFEST_REQUIRED')
   require(c['scale'] in ('S1','S2','S3'),'REGISTERED_SCALE')
 participants=p.get('participants',{})
 identifiers=set();units=set();orders=set()
 for r in p['runs']:
  require(r.get('method') in REGISTRY and r.get('case_id') in cases,'RUN_METHOD_OR_CASE')
  require(isinstance(r.get('run_id'),str) and r['run_id'] and '/' not in r['run_id'],'RUN_ID_REQUIRED')
  require(r['run_id'] not in identifiers,'DUPLICATE_RUN_ID');identifiers.add(r['run_id'])
  require(integer(r.get('repetition')) and r['repetition']>0 and integer(r.get('order_index')),'REPETITION_AND_ORDER_REQUIRED')
  require(integer(r.get('max_attempts')) and r['max_attempts']>0,'ATTEMPT_LIMIT_REQUIRED')
  require(r.get('workflow') in ('human','system_only'),'WORKFLOW_REQUIRED')
  require(r.get('analysis_role') in ('primary','learning','retry'),'ANALYSIS_ROLE_REQUIRED')
  require('demand_seed' not in r and 'input_dir' not in r and 'total_limit_s' not in r,'NO_METHOD_SPECIFIC_CASE_OVERRIDE')
  require(not any(k in r for k in ('input_hash','OD_hash','physical_hash','files','config','resource_contract','T_kind','measurement_contract','budget_wall_s')),'NO_METHOD_SPECIFIC_CASE_OVERRIDE')
  unit=(r['case_id'],r['method'],r.get('participant_id'),r['repetition'],r['analysis_role'])
  require(unit not in units,'DUPLICATE_TRIAL_UNIT');units.add(unit)
  if r['method']=='A':require(r['workflow']=='human' and r.get('solver_seed') is None,'A_MUST_BE_HUMAN')
  else:require(integer(r.get('solver_seed')),'SOLVER_SEED_REQUIRED')
  if r['method']=='D':require(integer(r.get('quantum_seed')),'QUANTUM_SEED_REQUIRED')
  if r['workflow']=='human':
   person=participants.get(r.get('participant_id'));require(isinstance(person,dict),'PARTICIPANT_REQUIRED')
   require(all(person.get(k) is not None for k in ('experience','tools','pc','procedure','planned_date','activity_recording')),'PARTICIPANT_METADATA_REQUIRED')
   require(person['activity_recording'] in ('participant_markers','observer_markers'),'ACTIVITY_OBSERVATION_REQUIRED')
   if person['activity_recording']=='observer_markers':require(person.get('observer_id'),'OBSERVER_ID_REQUIRED')
   require(isinstance(person['tools'],list) and person['tools'] and all(t.get('name') and t.get('version') for t in person['tools']),'TOOLS_AND_VERSIONS_REQUIRED')
   require(person['pc'].get('os') and person['pc'].get('description'),'PC_OS_REQUIRED')
   order=(r['participant_id'],r['order_index']);require(order not in orders,'DUPLICATE_PARTICIPANT_ORDER');orders.add(order)
   require(type(r.get('prior_exposure_expected')) is bool,'EXPOSURE_DECLARATION_REQUIRED')
  else:require(r.get('participant_id') is None and r['method']!='A','SYSTEM_WORKFLOW_IDENTITY')
  if r['analysis_role']=='retry':
   original=next((x for x in p['runs'] if x['run_id']==r.get('retry_of')),None)
   require(original and original['method']==r['method'] and original['case_id']==r['case_id'] and original['run_id']!=r['run_id'],'RETRY_RELATION_REQUIRED')
 stats=p.get('statistics',{})
 require(stats.get('ci_method') in ('descriptive','paired_case_t'),'STATISTICAL_METHOD_REQUIRED')
 require(stats.get('scope') in ('fixed_cases','case_population') and isinstance(stats.get('rationale'),str) and stats['rationale'],'STATISTICAL_SCOPE_AND_RATIONALE_REQUIRED')
 require(positive(stats.get('confidence')) and stats['confidence']<1,'CONFIDENCE_REQUIRED')
 require(isinstance(stats.get('pairs'),list) and all(len(pair)==2 and all(m in REGISTRY for m in pair) for pair in stats['pairs']),'COMPARISON_PAIRS_REQUIRED')
 require(stats['pairs'] and all(a!=b for a,b in stats['pairs']) and len({tuple(sorted(x)) for x in stats['pairs']})==len(stats['pairs']),'DISTINCT_COMPARISON_PAIRS_REQUIRED')
 metrics=stats.get('inferential_metrics',['D_km','W_min','T_total_sec'])
 require(metrics and len(metrics)==len(set(metrics)) and all(k in ('D_km','W_min','T_total_sec') for k in metrics),'INFERENTIAL_METRICS_REQUIRED')
 if stats['ci_method']=='paired_case_t':
  require(stats['scope']=='case_population' and stats.get('assumptions')=='independent_normal_case_mean_differences','CI_ASSUMPTIONS_REQUIRED')
  require(stats.get('multiplicity') in ('pointwise_exploratory','bonferroni'),'MULTIPLICITY_POLICY_REQUIRED')
 if p['phase']!='contract_check':
  require(all(c['kind']!='synthetic_validation' for c in cases.values()),'SYNTHETIC_NOT_EMPIRICAL')
  require(p.get('rq_approval',{}).get('decision')=='approved_total_time_v1','RQ_APPROVAL_REQUIRED')
  require(p['rq_approval']==read(ROOT/'docs/research/human_comparison_v1_20261116/RQ_APPROVAL.json'),'RQ_APPROVAL_EVIDENCE_MISMATCH')
  require(p.get('execution_authorization',{}).get('approved') is True and p['execution_authorization'].get('evidence'),'HUMAN_OR_FORMAL_EXECUTION_AUTHORIZATION_REQUIRED')
  require(p.get('precision_goal') is not None,'PRECISION_OR_DESCRIPTIVE_GOAL_REQUIRED')
  require(p.get('study_budget_s') is not None and positive(p['study_budget_s']),'STUDY_BUDGET_REQUIRED')
  require(sum(cases[r['case_id']]['total_limit_s'] for r in p['runs'])<=p['study_budget_s'],'STUDY_BUDGET_EXCEEDED')
  require(all({r['method'] for r in p['runs'] if r['case_id']==case_id}==set(REGISTRY) for case_id in cases),'SHARED_A_TO_D_CASES_REQUIRED')
  seen={}
  for r in sorted(p['runs'],key=lambda r:r['order_index']):
   if r['workflow']!='human':continue
   family=cases[r['case_id']]['family_id'];key=(r['participant_id'],family)
   if key in seen:
    require(r['analysis_role'] in ('learning','retry') and r['prior_exposure_expected'] is True and seen[key]==r['case_id'],'PRIOR_EXPOSURE_OR_NESTED_CASE_LEAKAGE')
   else:require(r['prior_exposure_expected'] is False,'FIRST_EXPOSURE_MUST_BE_UNSEEN');seen[key]=r['case_id']
 return p


def register(plan_path,out):
 p=validate_plan(read(plan_path));out=Path(out);out.mkdir(parents=True,exist_ok=False)
 # Source/environment preparation only. No input.json, OD, or case catalog is read.
 files=sorted((ROOT/'src/kmd_toc').rglob('*.py'))+[
   ROOT/'scripts/run_human_comparison_v1.py',ROOT/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json',
   ROOT/'configs/toc_delivery/a_human_v1_20261116.json',ROOT/'configs/toc_delivery/common_conditions_v1_1.json',
   ROOT/'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json',
   ROOT/'configs/toc_delivery/human_comparison_v1_result_schema.json',
   ROOT/'docs/research/human_comparison_v1_20261116/RQ_APPROVAL.json']
 for name,h in read(ROOT/'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json')['files'].items():
  require(digest(ROOT/name)==h,'FROZEN_A_CHANGED:'+name)
 reg={**deepcopy(p),'T_kind':TIME_KIND,'registry':REGISTRY,'registered_utc':now(),
      'source_hashes':{str(f.relative_to(ROOT)):digest(f) for f in files},
      'physical_hash':digest(ROOT/'configs/toc_delivery/common_conditions_v1_1.json'),
      'BCD_config':read(ROOT/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json'),
      'cpu_ids':cpu_ids(),'registration_payload_read':False,
      'code_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'environment':{'python':p.get('python',os.sys.executable),'dependency_prefix':p.get('dependency_prefix'),
                     'OS_page_cache':'uncontrolled','shared_host_load':'uncontrolled'}}
 reg['registration_hash']=fingerprint(reg)
 dump(out/'REGISTERED.json',reg)
 with tarfile.open(out/'SOURCE_SNAPSHOT.tar.gz','x:gz') as tar:
  for f in files:tar.add(f,arcname=str(f.relative_to(ROOT)))
 return out/'REGISTERED.json'


def load_registration(path):
 reg=read(path);expected=reg.pop('registration_hash')
 require(fingerprint(reg)==expected,'REGISTRATION_HASH_MISMATCH');reg['registration_hash']=expected
 validate_plan(reg);verify_sources(reg)
 return reg


def load_case(reg,case):
 # Must be called inside a timed machine stage, never in register/prepare.
 from kmd_toc.common.models import load_problem
 base=Path(case['input_dir'])
 for name,h in case['files'].items():require(digest(base/name)==h,'INPUT_HASH_MISMATCH:'+name)
 if case['kind']=='registered_scenario':
  from .inputs import load_registered_scenario
  p=load_registered_scenario(base,case)
 else:p=load_problem(base)
 require(p.experiment.kind=='synthetic_validation' if case['kind']=='synthetic_validation' else p.experiment.kind!='synthetic_validation','CASE_ORIGIN_MISMATCH')
 if case['kind']!='synthetic_validation':
  expected={'S1':(1000,10,2),'S2':(2000,20,4),'S3':(4000,40,8)}[case['scale']]
  require((len(p.stops),len(p.vehicles),len(p.berths))==expected,'SCALE_COUNTS_MISMATCH')
  od=read(base/'od/manifest.json')['metadata']
  require(od.get('table_distances_used') is False and od.get('directed') is True,'ROUTE_OD_REQUIRED')
 return p
