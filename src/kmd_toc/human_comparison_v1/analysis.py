"""Evidence verification, failure-inclusive tables and case-level paired analysis."""
from collections import defaultdict
from itertools import combinations
import math
from pathlib import Path
from statistics import mean,median,stdev

from .contract import (CONTRACT,TIME_KIND,REGISTRY,read,digest,require,load_registration,
                       fingerprint,load_case,dump)
from .session import events
from .evaluation import partition,evaluate,union_seconds

METRICS=('D_km','W_min','T_total_sec','T_compute_sec','T_human_sec','T_machine_sec','T_other_sec')


def verify_session(path,reg):
 out=Path(path);row=read(out/'RESULT.json');meta=read(out/'PREPARED.json')
 run=next((r for r in reg['runs'] if r['run_id']==row['run_id']),None);require(run is not None,'UNREGISTERED_RESULT')
 case=next(c for c in reg['cases'] if c['case_id']==run['case_id'])
 require(meta['registration_hash']==row['registration_hash']==reg['registration_hash'],'RESULT_REGISTRATION_MISMATCH')
 require(meta['run']==run,'RESULT_RUN_MISMATCH')
 require(row['measurement_contract']==CONTRACT and row['T_kind']==TIME_KIND,'LEGACY_TIMING_REJECTED')
 require(row['method']==run['method'] and row['method_version']==REGISTRY[run['method']]['method_version'] and
         row['implementation_id']==REGISTRY[run['method']]['implementation_id'],'METHOD_IDENTITY_MISMATCH')
 require(row['case_id']==run['case_id'] and row['scenario_id']==case['scenario_id'] and row['scale']==case['scale'],'CASE_IDENTITY_MISMATCH')
 require(row['input_hash']==fingerprint(case['files']) and row['physical_hash']==reg['physical_hash'],'INPUT_CONDITIONS_MISMATCH')
 require(row['source_hashes']==reg['source_hashes'],'RESULT_SOURCE_MISMATCH')
 if row['status']!='abnormal_interruption':
  require(row['resource_contract']['cpu_ids']==reg['cpu_ids'] and
          row['resource_contract']['tree_RSS_limit_MiB']==reg['memory_limit_MiB'],'RESOURCE_CONTRACT_MISMATCH')
 require(row['observed']==(reg['phase']!='contract_check' and case['kind']!='synthetic_validation'),'FALSE_EMPIRICAL_CLASSIFICATION')
 for key,expected in [('repetition',run['repetition']),('participant_id',run.get('participant_id')),
                      ('seed',run.get('solver_seed')),('analysis_role',run['analysis_role'])]:
  require(row.get(key)==expected,'RESULT_FACTOR_MISMATCH:'+key)
 if row['status']=='abnormal_interruption':
  require(not row['feasibility'] and all(row.get(k) is None for k in METRICS),'INTERRUPTED_VALUES_MUST_BE_NULL')
  return row
 log=events(out);require(log and log[-1]['stage']=='END','MISSING_FINAL_EVENT')
 parts=partition(log)
 require(log[-1]['detail']['status']==row['status'],'RESULT_STATUS_MISMATCH')
 for k,value in parts.items():
  if k.startswith('T_'):
   require(abs(row['diagnostic_elapsed'][k]-value)<=1e-8,'DIAGNOSTIC_TIME_CHANGED')
   if row['observed'] and row['status']=='success':require(row[k] is not None and abs(row[k]-value)<=1e-8,'TIME_PARTITION_CHANGED')
   else:require(row[k] is None,'UNOBSERVED_OR_FAILED_TIME_NOT_NULL')
 require(abs(row['T_attempt_sec']-parts['T_total_sec'])<=1e-8,'ATTEMPT_TIME_MISMATCH')
 reports=row['attempts'];spans=[]
 for report in reports:
  dest=Path(report['path'])
  require(dest.is_relative_to(out.resolve()),'FOREIGN_ATTEMPT')
  require(report==read(dest/'PROCESS.json'),'ATTEMPT_RECORD_CHANGED')
  require(report['start_ns']>=log[0]['ns'] and report['end_ns']<=log[-1]['ns'],'ATTEMPT_OUTSIDE_SESSION')
  for a,b in report['result'].get('compute_spans_ns',[]):
   require(report['start_ns']<=a<=b<=report['end_ns'],'COMPUTE_SPAN_OUTSIDE_MACHINE')
   spans.append((a,b))
 complete=run['method']!='A' and all(r['result'].get('T_compute_sec') is not None for r in reports if r['action']=='evaluate')
 expected_compute=union_seconds(spans) if complete else None
 require(row['diagnostic_elapsed']['T_compute_sec']==expected_compute,'COMPUTE_UNION_MISMATCH')
 require(row['T_compute_sec']==(expected_compute if row['observed'] and row['status']=='success' else None),'COMPUTE_ADOPTION_MISMATCH')
 if run['method']=='A':require(row['T_compute_sec'] is None,'HUMAN_COMPUTE_MUST_BE_NULL')
 require(row.get('J') is None,'UNREGISTERED_J')
 if row['status']=='success':
  require(parts['T_total_sec']<=case['total_limit_s'] and row['completed_within_limit'],'LATE_SUCCESS')
  require(row['feasibility'],'INVALID_SUCCESS')
  require(digest(out/'accepted_plan.json')==row['plan_sha256'],'ACCEPTED_PLAN_CHANGED')
  reports=row['attempts'];require(all(Path(r['path']).is_relative_to(out.resolve()) for r in reports),'FOREIGN_ATTEMPT')
  final=reports[-1]
  require(final['action']=='final' and final['cleanup_proved'] and final['end_ns']<=log[-1]['ns'],'POSTHOC_VALIDATION_NOT_DEADLINE_SUCCESS')
  require(final==read(Path(final['path'])/'PROCESS.json'),'ATTEMPT_RECORD_CHANGED')
  from kmd_toc.common.models import load_plan
  problem=load_case(reg,case);plan=load_plan(out/'accepted_plan.json')
  manual=None
  if run['method']=='A':
   require(row['human_authorship_attested'] and log[-1]['detail']['human_authorship_attested'],'HUMAN_AUTHORSHIP_REQUIRED')
   require(any(e['stage']=='HUMAN' and e['detail'].get('task')=='assignment_order' for e in log),'NO_HUMAN_ASSIGNMENT_EVIDENCE')
   require(any(e['stage']=='HUMAN' and e['detail'].get('task')=='review' for e in log),'NO_HUMAN_REVIEW_EVIDENCE')
   submission=sorted(out.glob('manual_submission_*.csv'))[-1]
   manual=submission.read_text()
   require(digest(submission)==final['result']['manual_csv_sha256'],'MANUAL_SUBMISSION_CHANGED')
  checked=evaluate(problem,plan,human_csv=manual);require(checked['validated'],'POSTRUN_PHYSICAL_REJECTION')
  for k,v in checked['official_metrics'].items():require(abs(row[k]-v)<=1e-7,'OFFICIAL_METRIC_CHANGED:'+k)
 else:
  require(not row['feasibility'] and all(row.get(k) is None for k in METRICS),'FAILURE_VALUES_MUST_BE_NULL')
 return row


def describe(values):
 require(all(type(x) in (int,float) and math.isfinite(x) for x in values),'NONFINITE_ANALYSIS_VALUE')
 if not values:return {'n':0,'mean':None,'median':None,'sd':None,'IQR':None,'min':None,'max':None}
 s=sorted(values)
 def quantile(p):
  pos=(len(s)-1)*p;i=int(pos);return s[i]+(s[min(i+1,len(s)-1)]-s[i])*(pos-i)
 return {'n':len(s),'mean':mean(s),'median':median(s),'sd':stdev(s) if len(s)>1 else None,
         'IQR':quantile(.75)-quantile(.25),'min':s[0],'max':s[-1],
         'quantile_rule':'linear_interpolation_(n-1)*p'}


def paired_interval(values,confidence):
 if len(values)<2:return {'interval':None,'reason':'FEWER_THAN_TWO_INDEPENDENT_CASES'}
 sd=stdev(values)
 if sd==0:return {'interval':None,'reason':'ZERO_OBSERVED_VARIANCE_NO_PRECISION_GUARANTEE'}
 from scipy.stats import t
 half=float(t.ppf((1+confidence)/2,len(values)-1))*sd/math.sqrt(len(values))
 return {'interval':[mean(values)-half,mean(values)+half],'reason':'PAIRED_CASE_T_UNDER_REGISTERED_NORMALITY_ASSUMPTION',
         'confidence':confidence,'df':len(values)-1,'independent_units':len(values)}


def pair_state(left_success,right_success,complete=True):
 if not complete:return 'EXCLUDED_NOT_OBSERVED_OR_INCOMPLETE'
 return ('BOTH_SUCCESS' if left_success and right_success else 'LEFT_ONLY_SUCCESS' if left_success
         else 'RIGHT_ONLY_SUCCESS' if right_success else 'BOTH_FAILED')


def independence_reasons(cases,participants):
 reasons=[]
 if any(not c['independent_draw'] for c in cases):reasons.append('CASE_NOT_REGISTERED_AS_INDEPENDENT_DRAW')
 if len({c['family_id'] for c in cases})<len(cases):reasons.append('SHARED_DEMAND_FAMILY')
 if any(len(c)>1 for c in participants.values()):reasons.append('REUSED_HUMAN_PARTICIPANT_ACROSS_CASES')
 return reasons


def aggregate(registration,out):
 reg=load_registration(registration);base=Path(registration).resolve().parent
 claims=base/'claims';rows=[];seen=set();missing=[]
 for run in reg['runs']:
  claim=claims/(run['run_id']+'.json')
  if not claim.exists():missing.append(run['run_id']);continue
  path=Path(read(claim)['session'])
  if not (path/'RESULT.json').exists():missing.append(run['run_id']);continue
  r=verify_session(path,reg)
  require(r['run_id'] not in seen,'DUPLICATE_RESULT');seen.add(r['run_id']);rows.append(r)
 return aggregate_rows(reg,rows,missing=missing,out=out)


def aggregate_rows(reg,rows,*,missing=None,out=None):
 """Pure aggregation; production callers must first verify all session evidence."""
 ids=[r['run_id'] for r in rows];require(len(ids)==len(set(ids)),'DUPLICATE_RESULT')
 registered={r['run_id']:r for r in reg['runs']}
 for r in rows:
  require(r['run_id'] in registered,'UNREGISTERED_RESULT')
  require(r['measurement_contract']==CONTRACT and r['T_kind']==TIME_KIND,'LEGACY_TIMING_REJECTED')
  require(r['registration_hash']==reg['registration_hash'],'RESULT_REGISTRATION_MISMATCH')
  case=next(c for c in reg['cases'] if c['case_id']==r['case_id'])
  require(r['observed']==(reg['phase']!='contract_check' and case['kind']!='synthetic_validation'),'FALSE_EMPIRICAL_CLASSIFICATION')
  require(r['input_hash']==fingerprint(case['files']) and r['physical_hash']==reg['physical_hash'],'INPUT_CONDITIONS_MISMATCH')
 missing=missing if missing is not None else list(set(registered)-set(ids))
 table=[];raw=defaultdict(list)
 for scale in sorted({c['scale'] for c in reg['cases']}):
  case_ids={c['case_id'] for c in reg['cases'] if c['scale']==scale}
  for method in REGISTRY:
   planned=[r for r in reg['runs'] if r['case_id'] in case_ids and r['method']==method]
   selected=[r for r in rows if r['case_id'] in case_ids and r['method']==method]
   successful=[r for r in selected if r['status']=='success' and r['observed']]
   table.append({'scale':scale,'method':method,'planned':len(planned),'executed':len(selected),
      'not_executed_or_incomplete':len(planned)-len(selected),'observed':sum(r['observed'] for r in selected),
      'retry_trials':sum(r['analysis_role']=='retry' for r in selected),
      'learning_trials':sum(r['analysis_role']=='learning' for r in selected),
      'participant_ids':sorted({r['participant_id'] for r in selected if r.get('participant_id')}),
      'internal_branches_counted_as_trials':False,
      'validated_plans':sum(r['feasibility'] for r in selected),'observed_successes':len(successful),
      'observed_feasible_candidate_rate':sum(r.get('candidate_feasibility',r['feasibility']) for r in selected if r['observed'])/sum(r['observed'] for r in selected) if any(r['observed'] for r in selected) else None,
      'timeouts':sum('TIMEOUT' in r['status'].upper() for r in selected),
      'input_invalid':sum('INPUT_INVALID' in r['status'].upper() for r in selected),
      'runtime_errors':sum('ERROR' in r['status'].upper() or 'FAILURE' in r['status'].upper() for r in selected),
      'interrupted':sum(r['status']=='abnormal_interruption' for r in selected),
      'completion_rate_observed':len(successful)/sum(r['observed'] for r in selected) if any(r['observed'] for r in selected) else None,
      'completion_rate_denominator':'all observed started trials; timeouts/errors retained',
      'conditional_success_metrics':{k:describe([r[k] for r in successful if r.get(k) is not None]) for k in METRICS},
      'all_observed_attempt_times':describe([r['T_attempt_sec'] for r in selected if r['observed'] and r.get('T_attempt_sec') is not None]),
      'run_ids':[r['run_id'] for r in selected],'missing_run_ids':[r['run_id'] for r in planned if r['run_id'] in missing]})
   for r in successful:
    if r['analysis_role']=='primary':raw[(r['case_id'],method)].append(r)
 pairs=[]
 for left,right in reg['statistics']['pairs']:
  for scale in sorted({c['scale'] for c in reg['cases']}):
   entries=[];differences={k:[] for k in METRICS};participants=defaultdict(set);ci_allowed=True;reasons=[]
   for case in (c for c in reg['cases'] if c['scale']==scale):
    a,b=raw[(case['case_id'],left)],raw[(case['case_id'],right)]
    planned={m:[r for r in reg['runs'] if r['case_id']==case['case_id'] and r['method']==m and r['analysis_role']=='primary'] for m in (left,right)}
    matching={m:[r for r in rows if r['case_id']==case['case_id'] and r['method']==m and r['analysis_role']=='primary' and r['observed']] for m in (left,right)}
    complete=all(planned[m] and len(matching[m])==len(planned[m]) for m in (left,right))
    invalid_input=any(r.get('input_state')=='INVALID' for m in (left,right) for r in matching[m])
    if invalid_input:complete=False
    state=pair_state(bool(a),bool(b),complete)
    e={'case_id':case['case_id'],'scenario_id':case['scenario_id'],'status':state,
       'exclusion_reason':'INPUT_INVALID' if invalid_input else None if complete else 'NOT_OBSERVED_OR_INCOMPLETE',
       'left_success_runs':[r['run_id'] for r in a],'right_success_runs':[r['run_id'] for r in b]}
    if state=='BOTH_SUCCESS':
     require(all(r['input_hash']==fingerprint(case['files']) and r['physical_hash']==reg['physical_hash'] for r in a+b),'PAIRED_INPUT_MISMATCH')
     e['case_success_conditional_means']={}
     for k in METRICS:
      av=[r[k] for r in a if r.get(k) is not None];bv=[r[k] for r in b if r.get(k) is not None]
      if av and bv:
       delta=mean(bv)-mean(av);differences[k].append(delta)
       e['case_success_conditional_means'][k]={'left':mean(av),'right':mean(bv),'right_minus_left':delta,
          'relative_improvement_percent':100*(mean(av)-mean(bv))/mean(av) if mean(av)>0 else None,
          'relative_reason':'DEFINED' if mean(av)>0 else 'ZERO_REFERENCE'}
     for r in a+b:
      if r.get('participant_id'):participants[r['participant_id']].add(case['case_id'])
     if not case['independent_draw']:ci_allowed=False;reasons.append('CASE_NOT_REGISTERED_AS_INDEPENDENT_DRAW')
    entries.append(e)
   successful_ids={e['case_id'] for e in entries if e['status']=='BOTH_SUCCESS'}
   reasons.extend(independence_reasons([c for c in reg['cases'] if c['case_id'] in successful_ids],participants))
   if reasons:ci_allowed=False
   intervals={}
   inferential_metrics=reg['statistics'].get('inferential_metrics',['D_km','W_min','T_total_sec'])
   family_size=len(reg['statistics']['pairs'])*len({c['scale'] for c in reg['cases']})*len(inferential_metrics)
   confidence=reg['statistics']['confidence']
   if reg['statistics'].get('multiplicity')=='bonferroni':confidence=1-(1-confidence)/family_size
   for k,vals in differences.items():
    intervals[k]=(paired_interval(vals,confidence) if reg['statistics']['ci_method']=='paired_case_t' and ci_allowed and k in inferential_metrics
       else {'interval':None,'reason':';'.join(sorted(set(reasons))) or 'DESCRIPTIVE_OR_NOT_REGISTERED_INFERENTIAL_METRIC'})
   pairs.append({'left':left,'right':right,'scale':scale,'entries':entries,
      'case_mean_differences':{k:describe(v) for k,v in differences.items()},'confidence_intervals':intervals,
      'comparison_unit':'one mean per shared demand case; seeds/branches are not independent demand samples',
      'interpretation':'conditional on successful plans on both sides; completion rates must accompany quality/time',
      'cases_total':len(entries),'both_success':sum(e['status']=='BOTH_SUCCESS' for e in entries)})
 result={'experiment_id':reg['experiment_id'],'phase':reg['phase'],'measurement_contract':CONTRACT,
     'units':{'D_km':'km','W_min':'min','T_total_sec':'s'},'all_trial_table':table,'paired_case_table':pairs,
     'planned_runs':len(reg['runs']),'completed_records':len(rows),'missing_or_incomplete':missing,
     'empirical_human_records':sum(r['method']=='A' and r['observed'] and r['status']=='success' for r in rows),
     'joint_observed_case_ids':[c['case_id'] for c in reg['cases'] if all(any(r['case_id']==c['case_id'] and r['method']==m and r['observed'] and r.get('input_state')!='INVALID' for r in rows) for m in REGISTRY)],
     'J':None,'J_reason':'HUMAN_TOTAL_REFERENCE_NOT_PREREGISTERED','p_values':None}
 if out:
  out=Path(out);out.mkdir(parents=True,exist_ok=False);dump(out/'SUMMARY.json',result)
  import csv
  columns=['experiment_id','run_id','session_id','case_id','scenario_id','scale','method','method_version','measurement_contract','seed','demand_seed','quantum_seed',
    'repetition','participant_id','order_index','D_km','W_min','T_total_sec','T_compute_sec','T_human_sec','T_machine_sec','T_other_sec',
    'feasibility','status','observed','evidence_path']
  with (out/'ALL_TRIALS.csv').open('x') as f:
   w=csv.DictWriter(f,columns,extrasaction='ignore');w.writeheader()
   for run in reg['runs']:
    row=next((r for r in rows if r['run_id']==run['run_id']),None)
    if row:w.writerow(row)
    else:
     c=next(c for c in reg['cases'] if c['case_id']==run['case_id'])
     w.writerow({'experiment_id':reg['experiment_id'],'run_id':run['run_id'],'case_id':run['case_id'],'scenario_id':c['scenario_id'],'scale':c['scale'],
       'method':run['method'],'method_version':REGISTRY[run['method']]['method_version'],
       'measurement_contract':CONTRACT,'repetition':run['repetition'],'status':'not_executed_or_incomplete','observed':False})
 return result


def adoption(reg,summary):
 humans=summary['empirical_human_records']
 observed=sum(t['observed'] for t in summary['all_trial_table'])
 successful_methods={t['method'] for t in summary['all_trial_table'] if t['observed_successes']}
 human_started=sum(t['observed'] for t in summary['all_trial_table'] if t['method']=='A')
 complete=not summary['missing_or_incomplete']
 descriptive_evaluable=(reg['statistics']['ci_method']=='descriptive' and any(p['both_success']>=1 for p in summary['paired_case_table']))
 inferential_evaluable=any(p['both_success']>=2 and any(v['interval'] is not None for v in p['confidence_intervals'].values()) for p in summary['paired_case_table'])
 conditions={
  '1_human_assignment_and_order':'PASS' if humans else 'NOT_TESTED',
  '2_common_physical_feasibility':'PASS' if humans else 'FAIL' if human_started else 'NOT_TESTED',
  '3_actual_human_measurement':'PASS' if humans else 'FAIL' if human_started else 'NOT_TESTED',
  '4_same_boundary_A_to_D':'PASS' if summary['joint_observed_case_ids'] else 'NOT_TESTED',
  '5_traceability':'PASS' if observed and complete else 'NOT_TESTED',
  '6_statistical_evaluability':'PASS' if humans and complete and (descriptive_evaluable or inferential_evaluable) else 'NOT_TESTED',
  '7_limited_research_position':'PASS',
 }
 measured=humans>0;comparable=measured and bool(summary['joint_observed_case_ids'])
 return {'IMPLEMENTED':True,'MEASURED':measured,'COMPARABLE':comparable,
    'formal_adoption':measured and comparable and complete and reg['phase']=='formal' and all(v=='PASS' for v in conditions.values()),
    'conditions':conditions,'target_operator_representativeness':'NOT_TESTED',
    'statistical_generalization':'CONDITIONAL_ON_REGISTERED_INDEPENDENT_CASE_AND_HUMAN_DESIGN' if inferential_evaluable and humans else 'NOT_ESTABLISHED',
    'reason':'No formal adoption without actual observed human plans and same-contract A-D evidence',
    'data_phase':reg['phase']}
