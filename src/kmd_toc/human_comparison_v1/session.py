"""Append-only human/system sessions; case data stay unopened until start."""
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import ctypes
import subprocess
import sys
import time

from .contract import (ROOT,CONTRACT,TIME_KIND,REGISTRY,read,dump,digest,fingerprint,
                       require,load_registration,verify_sources,now)
from .evaluation import partition,union_seconds


def clock_id():
 return {'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         'host':os.uname().nodename,'clock':'CLOCK_MONOTONIC_ns'}


def prepare(registration,run_id,out,*,authorize_observation=False):
 reg=load_registration(registration)
 require(reg['phase']=='contract_check' or authorize_observation,'OBSERVATION_AUTHORIZATION_REQUIRED')
 run=next((r for r in reg['runs'] if r['run_id']==run_id),None);require(run is not None,'RUN_NOT_REGISTERED')
 base=Path(registration).resolve().parent
 claims=base/'claims';claims.mkdir(exist_ok=True)
 # Registration ownership prevents duplicate sessions for a planned trial.
 with (claims/(run_id+'.json')).open('x') as f:
  import json
  json.dump({'run_id':run_id,'session':str(Path(out).resolve())},f)
 out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'events').mkdir();(out/'attempts').mkdir()
 meta={'session_id':run_id,'registration_path':str(Path(registration).resolve()),
       'registration_hash':reg['registration_hash'],'run':run,'case_id':run['case_id'],
       'clock_id':clock_id(),'prepared_utc':now(),'input_payload_opened':False}
 dump(out/'PREPARED.json',meta)
 return out


def events(out):
 meta=read(out/'PREPARED.json');last=None;result=[]
 for i,p in enumerate(sorted((out/'events').glob('*.json'))):
  require(p.name==f'{i:06}.json','EVENT_SEQUENCE')
  row=read(p);require(row['previous_sha256']==last,'EVENT_CHAIN_CHANGED')
  require(row['clock_id']==meta['clock_id'],'EVENT_CLOCK_ID_CHANGED')
  require(type(row['ns']) is int and row['ns']>=0,'EVENT_CLOCK_TYPE')
  if result:require(row['ns']>=result[-1]['ns'],'CLOCK_REVERSED')
  result.append(row);last=digest(p)
 return result


def append(out,stage,*,at_ns=None,**detail):
 old=events(out);meta=read(out/'PREPARED.json')
 require(meta['clock_id']==clock_id(),'BOOT_OR_HOST_CHANGED')
 stamp=time.monotonic_ns() if at_ns is None else at_ns
 require(not old or stamp>=old[-1]['ns'],'CLOCK_REVERSED')
 dump(out/'events'/f'{len(old):06}.json',{'stage':stage,'ns':stamp,
   'utc':now(),'clock_id':meta['clock_id'],'detail':detail,
   'previous_sha256':digest(out/'events'/f'{len(old)-1:06}.json') if old else None})


def command_enter(out,entry_ns):
 """Stop a declared human interval at CLI entry, before source checks/imports."""
 out=Path(out);old=events(out)
 if old and old[-1]['stage']!='END':
  require(old[-1]['stage']!='MACHINE','UNFINISHED_MACHINE_STAGE_USE_RECOVER')
  append(out,'MACHINE',at_ns=entry_ns,operation='CLI_dispatch_and_integrity_checks')


def context(out,*,allow_closed=False):
 out=Path(out);meta=read(out/'PREPARED.json')
 require(meta['clock_id']==clock_id(),'BOOT_OR_HOST_CHANGED')
 # Direct system/API orchestration also performs real machine work here.
 # Interactive CLI calls already mark entry before parsing/source checks.
 log=events(out)
 if log and log[-1]['stage'] not in ('MACHINE','END'):
  append(out,'MACHINE',operation='controller_integrity_checks')
 reg=load_registration(meta['registration_path'])
 require(reg['registration_hash']==meta['registration_hash'],'SESSION_REGISTRATION_CHANGED')
 require(allow_closed or not (out/'RESULT.json').exists(),'SESSION_CLOSED')
 run=meta['run'];require(run in reg['runs'],'RUN_IDENTITY_CHANGED')
 case=next(c for c in reg['cases'] if c['case_id']==run['case_id'])
 return meta,reg,run,case


def expired(out,case):
 e=events(out)
 return bool(e and (time.monotonic_ns()-e[0]['ns'])/1e9>case['total_limit_s'])


def machine(out,reg,run,case,action,**extra):
 """Machine ownership includes imports, IPC, validation, and process cleanup."""
 log=events(out)
 require(log and log[-1]['stage'] not in ('END',),'SESSION_NOT_ACTIVE')
 append(out,'MACHINE',action=action)
 os.sched_setaffinity(0,set(reg['cpu_ids']))
 index=len(list((out/'attempts').iterdir()));dest=out/'attempts'/f'{index:04}_{action}'
 dest.mkdir(exist_ok=False)
 require(action in ('input','evaluate','final'),'MACHINE_ACTION')
 job={'registration':reg,'run':run,'case':case,'action':action,'out':str(dest.resolve()),
      'attempt':sum(p.name.endswith('_evaluate') for p in (out/'attempts').iterdir()),**extra}
 dump(dest/'JOB.json',job)
 remaining=case['total_limit_s']-(time.monotonic_ns()-events(out)[0]['ns'])/1e9
 cap=min(case['machine_limit_s'],max(0,remaining))
 env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',
    OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 prefix=reg.get('dependency_prefix')
 if prefix:env['PYTHONPATH']=str(ROOT/'src')+os.pathsep+prefix
 begin=events(out)[-1]['ns'];proc=None;reason='NORMAL';clean=False;samples=[]
 try:
  require(cap>0,'TOTAL_DEADLINE')
  require(ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0,'SUBREAPER_REQUIRED')
  # Parent stopwatch and source checks are separate from algorithm instrumentation.
  with (dest/'stdout.log').open('x') as stdout,(dest/'stderr.log').open('x') as stderr:
   proc=subprocess.Popen([reg.get('python',sys.executable),'-B','-m',
        'kmd_toc.human_comparison_v1.machine',str((dest/'JOB.json').resolve())],
        cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
   from kmd_toc.comparison_v1.telemetry import tree_sample
   until=begin/1e9+cap;next_sample=0.
   while proc.poll() is None:
    if time.monotonic()>=until:raise subprocess.TimeoutExpired(proc.args,cap)
    if time.monotonic()>=next_sample:
     sample=tree_sample(proc.pid);samples.append(sample);next_sample=time.monotonic()+.1
     if sample['tree_rss_sum_KiB']>reg['memory_limit_MiB']*1024:
      raise MemoryError('REGISTERED_PROCESS_TREE_RSS_LIMIT')
    time.sleep(.01)
   if proc.returncode!=0:reason='PROCESS_ERROR'
 except subprocess.TimeoutExpired:reason='MACHINE_OR_TOTAL_TIMEOUT'
 except Exception as e:reason=type(e).__name__+':'+str(e)
 finally:
  if proc:
   # Terminate the owned group, including native branches, on success and failure.
   from kmd_toc.comparison_v1.execution import cleanup
   detail=cleanup(proc);clean=detail['session_empty']
   dump(dest/'CLEANUP.json',detail)
  else:clean=True
  result=read(dest/'RESULT.json') if (dest/'RESULT.json').exists() else {'validated':False}
  report={'termination':reason,'returncode':proc.returncode if proc else None,
          'pid':proc.pid if proc else None,'start_ns':begin,'end_ns':time.monotonic_ns(),
          'result':result,'path':str(dest.resolve()),'action':action,
          'error':read(dest/'ERROR.json') if (dest/'ERROR.json').exists() else None,
          'cleanup_proved':bool(clean),'resource_samples':samples,
          'tree_RSS_peak_sum_KiB':max((s['tree_rss_sum_KiB'] for s in samples),default=None),
          'RSS_scope':'sampled process RSS sum may double count shared pages; not exact unique memory'}
  dump(dest/'PROCESS.json',report)
  append(out,'OTHER',machine_result=str(dest.resolve()),termination=reason)
 return report


def failure_status(report):
 text=report['termination']+' '+str(report.get('error'))+' '+str(report['result'].get('native_status'))
 if 'TIMEOUT' in text or 'TIME_BUDGET' in text:return 'MACHINE_OR_NATIVE_TIMEOUT'
 if 'MemoryError' in text:return 'MEMORY_LIMIT'
 if 'INPUT_HASH' in text or 'INPUT_SCHEMA' in text or 'FROZEN_DEMAND' in text:return 'INPUT_INVALID'
 if report.get('error') and 'MANUAL_' in str(report['error']):return 'INVALID_MANUAL_PLAN'
 if report['result'].get('native_status')=='NO_VERIFIED_PLAN':return 'NO_VERIFIED_PLAN'
 if report['result'].get('common',{}).get('feasible') is False:return 'INVALID_PLAN'
 return 'PROCESS_ERROR_OR_NO_VERIFIED_PLAN'


def start(out,*,confirm_unseen=False,confirm_registered_repeat=False):
 out=Path(out);meta,reg,run,case=context(out)
 require(not events(out),'SESSION_ALREADY_STARTED')
 if run['workflow']=='human':
  require(confirm_registered_repeat if run['prior_exposure_expected'] else confirm_unseen,'CASE_EXPOSURE_CONFIRMATION_REQUIRED')
 append(out,'MACHINE',operation='start_before_case_input_read',
        unseen_confirmed=confirm_unseen,registered_repeat_confirmed=confirm_registered_repeat)
 report=machine(out,reg,run,case,'input')
 if report['termination']!='NORMAL' or not report['cleanup_proved']:
  return abort(out,failure_status(report))
 origin=Path(report['path'])
 append(out,'MACHINE',operation='catalog_transfer')
 with (out/'stops.csv').open('xb') as f:f.write((origin/'stops.csv').read_bytes())
 with (out/'vehicles.json').open('xb') as f:f.write((origin/'vehicles.json').read_bytes())
 if run['method']=='A':
  with (out/'assignment.csv').open('x') as f:f.write('vehicle_id,sequence,stop_id\n')
 dump(out/'INPUT_IDENTITY.json',report['result'])
 append(out,'OTHER',operation='input_available')
 return report


def activity(out,active,task,actor):
 out=Path(out);meta,reg,run,case=context(out)
 require(run['workflow']=='human','SYSTEM_WORKFLOW_HAS_NO_HUMAN_ACTIVITY')
 person=reg['participants'][run['participant_id']]
 expected_actor=person['observer_id'] if person['activity_recording']=='observer_markers' else run['participant_id']
 require(actor==expected_actor,'ACTIVITY_ACTOR')
 require(task in ('assignment_order','input_operation','review','correction','pause'),'ACTIVITY_TASK')
 require(events(out),'SESSION_NOT_STARTED')
 if expired(out,case):return abort(out,'TOTAL_TIMEOUT')
 require(not (active and task=='assignment_order' and run['method']!='A'),'BCD_ASSIGNMENT_IS_ALGORITHM_DECISION')
 if active and task=='review':
  prior=accepted_attempt(out)
  require(prior and prior['result'].get('validated'),'VALIDATED_PLAN_REQUIRED_FOR_REVIEW')
 append(out,'HUMAN' if active and task!='pause' else 'OTHER',task=task,actor=actor,
        observation=reg['participants'][run['participant_id']]['activity_recording'])


def attempt(out):
 out=Path(out);meta,reg,run,case=context(out)
 require(events(out),'SESSION_NOT_STARTED')
 if expired(out,case):return abort(out,'TOTAL_TIMEOUT')
 prior=[p for p in (out/'attempts').iterdir() if p.name.endswith('_evaluate')]
 require(len(prior)<run['max_attempts'],'REGISTERED_ATTEMPT_LIMIT')
 extras={}
 if run['method']=='A':
  require(any(e['stage']=='HUMAN' and e['detail'].get('task')=='assignment_order' for e in events(out)),'HUMAN_ASSIGNMENT_ACTIVITY_REQUIRED')
  append(out,'MACHINE',operation='manual_submission_snapshot')
  # Snapshot exact submitted decisions; rejected CSVs remain too.
  path=out/f'manual_submission_{len(prior)+1:04}.csv'
  with path.open('xb') as f:f.write((out/'assignment.csv').read_bytes())
  extras['csv_path']=str(path.resolve())
 report=machine(out,reg,run,case,'evaluate',**extras)
 if expired(out,case):return abort(out,'TOTAL_TIMEOUT')
 return report


def accepted_attempt(out):
 reports=[read(p/'PROCESS.json') for p in sorted((out/'attempts').glob('*_evaluate')) if (p/'PROCESS.json').exists()]
 return reports[-1] if reports else None


def finish(out,reg,run,case,status,*,candidate=None,human_attested=False):
 if status=='success' and expired(out,case):status='TOTAL_TIMEOUT'
 append(out,'END',status=status,human_authorship_attested=human_attested)
 log=events(out);parts=partition(log);valid=status=='success'
 synthetic=reg['phase']=='contract_check' or case['kind']=='synthetic_validation'
 observed=not synthetic
 results=[read(p) for p in sorted((out/'attempts').glob('*/PROCESS.json'))]
 computes=[(int(a),int(b)) for r in results for a,b in r['result'].get('compute_spans_ns',[])]
 compute=None if run['method']=='A' else union_seconds(computes)
 compute_complete=(run['method']!='A' and all(r['result'].get('T_compute_sec') is not None for r in results if r['action']=='evaluate'))
 if not compute_complete:compute=None
 metrics=candidate['result'].get('official_metrics',{}) if candidate and valid else {}
 identity=read(out/'INPUT_IDENTITY.json') if (out/'INPUT_IDENTITY.json').exists() else {}
 row={'experiment_id':reg['experiment_id'],'session_id':run['run_id'],'run_id':run['run_id'],
  'scenario_id':case['scenario_id'],'case_id':case['case_id'],'scale':case['scale'],
  'family_id':case['family_id'],'independent_draw':case['independent_draw'],
  'method':run['method'],**REGISTRY[run['method']],'mode':'human_inclusive',
  'measurement_contract':CONTRACT,'T_kind':TIME_KIND,'phase':reg['phase'],
  'seed':run.get('solver_seed'),'quantum_seed':run.get('quantum_seed'),'demand_seed':case.get('demand_seed'),
  'repetition':run['repetition'],'participant_id':run.get('participant_id'),
  'order_index':run['order_index'],'analysis_role':run['analysis_role'],
  'start_utc':log[0]['utc'],'end_utc':log[-1]['utc'],
  'monotonic_start_ns':log[0]['ns'],'monotonic_end_ns':log[-1]['ns'],'clock_id':log[0]['clock_id'],
  'prior_exposure_expected':run['prior_exposure_expected'] if run['workflow']=='human' else False,
  'D_km':metrics.get('D_km'),'W_min':metrics.get('W_min'),
  'W_first_min':metrics.get('W_first_min'),'W_reload_min':metrics.get('W_reload_min'),
  **{k:v if valid and observed else None for k,v in parts.items() if k.startswith('T_')},
  'T_compute_sec':compute if observed and valid else None,
  'T_compute_reason':'HUMAN_DECISION_NOT_COMPARABLE_ALGORITHM_TIME' if run['method']=='A' else
      'COMPLETE_ALGORITHM_UNION' if compute_complete else 'INCOMPLETE_ALGORITHM_OBSERVATION',
  'diagnostic_elapsed':{**parts,'T_compute_sec':compute},'T_attempt_sec':parts['T_total_sec'],
  'time_partition_complete':True,'feasibility':bool(valid),'status':status,
  'human_time_scope':'participant/observer marked active-work intervals; not independent proof of continuous attention',
  'completed_within_limit':valid and parts['T_total_sec']<=case['total_limit_s'],
  'time_limit_sec':case['total_limit_s'],'observed':observed,'origin':'synthetic_validation' if synthetic else 'registered_observation',
  'candidate_feasibility':any(r['result'].get('validated') for r in results if r['action'] in ('evaluate','final')),
  'human_authorship_attested':human_attested,'activity_measurement':'system_only_no_human_tasks' if run['workflow']=='system_only' else reg['participants'][run['participant_id']]['activity_recording'],
  'input_hash':fingerprint(case['files']),'problem_hash':identity.get('problem_hash'),
  'input_state':'INVALID' if 'INPUT_INVALID' in status else 'VALID' if identity.get('problem_hash') else 'NOT_CHECKED',
  'OD_hash':identity.get('OD_hash'),'physical_hash':reg['physical_hash'],
  'registration_hash':reg['registration_hash'],'resource_contract':{'available_physical_cores':4,
     'cpu_ids':reg['cpu_ids'],'A_native_threads':1,'BCD_branches':4,'native_threads_per_branch':1,
     'tree_RSS_limit_MiB':reg['memory_limit_MiB'],'A_address_space_limit_MiB':4096},
  'source_hashes':reg['source_hashes'],'plan_sha256':candidate['result'].get('plan_sha256') if candidate and valid else None,
  'participant_metadata':reg['participants'].get(run.get('participant_id')),
  'attempts':results,'revision_count':max(0,len([r for r in results if r['action']=='evaluate'])-1),
  'evidence_path':str(out.resolve()),'J':None,'J_reason':'HUMAN_TOTAL_REFERENCE_NOT_PREREGISTERED',
  'registry_version':CONTRACT,'target_operator_representativeness':'NOT_VERIFIED'}
 dump(out/'RESULT.json',row)
 return row


def accept(out,*,attest_human=False,attest_reviewed=False):
 out=Path(out);meta,reg,run,case=context(out)
 if expired(out,case):return abort(out,'TOTAL_TIMEOUT')
 candidate=accepted_attempt(out)
 require(candidate and candidate['termination']=='NORMAL' and candidate['cleanup_proved'] and candidate['result'].get('validated'),'VALIDATED_CANDIDATE_REQUIRED')
 require(run['workflow']=='system_only' or attest_reviewed,'FINAL_REVIEW_ATTESTATION_REQUIRED')
 if run['workflow']=='human':
  require(any(e['stage']=='HUMAN' and e['detail'].get('task')=='review' and e['ns']>=candidate['end_ns'] for e in events(out)),'LATEST_CANDIDATE_HUMAN_REVIEW_REQUIRED')
 if run['method']=='A':
  require(attest_human,'HUMAN_AUTHORSHIP_ATTESTATION_REQUIRED')
  require(any(e['stage']=='HUMAN' and e['detail'].get('task')=='review' for e in events(out)),'HUMAN_REVIEW_ACTIVITY_REQUIRED')
  require(digest(out/'assignment.csv')==candidate['result']['manual_csv_sha256'],'MANUAL_PLAN_CHANGED_SINCE_VALIDATION')
 source=Path(candidate['path'])/'plan.json'
 require(digest(source)==candidate['result']['plan_sha256'],'CANDIDATE_PLAN_CHANGED')
 extras={'plan_path':str(source.resolve())}
 if run['method']=='A':extras['csv_path']=str((out/'assignment.csv').resolve())
 final=machine(out,reg,run,case,'final',**extras)
 append(out,'MACHINE',operation='final_adoption_and_evidence_transfer')
 if expired(out,case):return abort(out,'TOTAL_TIMEOUT')
 if not (final['termination']=='NORMAL' and final['cleanup_proved'] and final['result'].get('validated')):return abort(out,failure_status(final))
 with (out/'accepted_plan.json').open('xb') as f:f.write((Path(final['path'])/'plan.json').read_bytes())
 return finish(out,reg,run,case,'success',candidate=final,human_attested=attest_human)


def abort(out,reason):
 out=Path(out);meta,reg,run,case=context(out)
 require(events(out),'SESSION_NOT_STARTED')
 return finish(out,reg,run,case,reason)


def recover(out,reason):
 """Record abnormal/rebooted sessions without fabricating a new monotonic span."""
 out=Path(out);meta=read(out/'PREPARED.json');require(not (out/'RESULT.json').exists(),'SESSION_CLOSED')
 reg=read(meta['registration_path']);run=meta['run'];case=next(c for c in reg['cases'] if c['case_id']==run['case_id'])
 row={'experiment_id':reg['experiment_id'],'run_id':run['run_id'],'session_id':run['run_id'],
  'case_id':case['case_id'],'scenario_id':case['scenario_id'],'scale':case['scale'],'method':run['method'],
  **REGISTRY[run['method']],'measurement_contract':CONTRACT,'T_kind':TIME_KIND,'mode':'human_inclusive',
  'phase':reg['phase'],'status':'abnormal_interruption','reason':reason,'observed':reg['phase']!='contract_check',
  'feasibility':False,'completed_within_limit':False,'D_km':None,'W_min':None,
  'T_total_sec':None,'T_human_sec':None,'T_machine_sec':None,'T_other_sec':None,'T_compute_sec':None,
  'T_attempt_sec':None,'time_partition_complete':False,'registration_hash':reg['registration_hash'],
  'input_hash':fingerprint(case['files']),'physical_hash':reg['physical_hash'],
  'source_hashes':reg['source_hashes'],'evidence_path':str(out.resolve()),'repetition':run['repetition'],
  'analysis_role':run['analysis_role'],'participant_id':run.get('participant_id'),
  'seed':run.get('solver_seed'),'J':None,'J_reason':'INTERRUPTED_NO_VALIDATED_MEASUREMENT'}
 dump(out/'RESULT.json',row);return row
