"""Artificial arithmetic witnesses, not measured participants or research results."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import pytest

from kmd_toc.human_comparison_v1.contract import ROOT,CONTRACT,TIME_KIND,read,digest,dump,fingerprint
from kmd_toc.human_comparison_v1.analysis import aggregate_rows,adoption,METRICS
from kmd_toc.human_comparison_v1.inputs import load_registered_scenario


def arithmetic_fixture():
 # Private pure-function input only. Never write these rows to a registered session.
 case={'case_id':'ARITHMETIC_ONLY','scenario_id':'NONE','scale':'TEST','kind':'frozen',
       'files':{'artificial':'0'*64},'family_id':'TEST','independent_draw':False}
 runs=[{'run_id':m,'case_id':case['case_id'],'method':m,'analysis_role':'primary',
        'repetition':1} for m in 'ABCD']
 reg={'experiment_id':'UNIT_ARITHMETIC_ONLY','phase':'human_pilot','cases':[case],
      'runs':runs,'registration_hash':'TEST','physical_hash':'TEST',
      'statistics':{'scope':'fixed_cases','ci_method':'descriptive','confidence':.95,
                    'pairs':[['A','D'],['C','D']]}}
 rows=[]
 for i,m in enumerate('ABCD'):
  rows.append({'run_id':m,'case_id':case['case_id'],'method':m,'participant_id':None,
       'measurement_contract':CONTRACT,'T_kind':TIME_KIND,'registration_hash':'TEST',
       'input_hash':fingerprint(case['files']),'physical_hash':'TEST','input_state':'VALID',
       'status':'success','feasibility':True,'candidate_feasibility':True,'observed':True,
       'T_attempt_sec':10+i,'analysis_role':'primary',
       **{k:float(10+i) for k in METRICS}})
 rows[0]['T_compute_sec']=None
 return reg,rows


@pytest.mark.parametrize('failures', ['', 'A', 'D', 'AD', 'ABCD'])
def test_full_failure_inclusive_aggregation_arithmetic(failures):
 reg,rows=arithmetic_fixture()
 for r in rows:
  if r['method'] in failures:
   r.update(status='TOTAL_TIMEOUT',feasibility=False,candidate_feasibility=False)
   r.update({k:None for k in METRICS})
 result=aggregate_rows(reg,rows)
 for table in result['all_trial_table']:
  expected=0 if table['method'] in failures else 1
  assert table['observed_successes']==expected and table['completion_rate_observed']==expected
  assert table['all_observed_attempt_times']['n']==1
  assert table['conditional_success_metrics']['T_total_sec']['n']==expected
 cd=result['paired_case_table'][1]
 assert cd['both_success']==(0 if 'C' in failures or 'D' in failures else 1)
 assert result['J'] is None and result['p_values'] is None
 assert not adoption(reg,result)['formal_adoption']


def test_zero_relative_reference_missing_time_and_pending_trial():
 reg,rows=arithmetic_fixture();rows[0]['W_min']=0;rows[0]['T_compute_sec']=None
 result=aggregate_rows(reg,rows)
 pair=result['paired_case_table'][0]['entries'][0]['case_success_conditional_means']
 assert pair['W_min']['relative_improvement_percent'] is None
 assert 'T_compute_sec' not in pair
 result=aggregate_rows(reg,rows[:-1])
 assert result['missing_or_incomplete']==['D']
 assert all(p['entries'][0]['status']=='EXCLUDED_NOT_OBSERVED_OR_INCOMPLETE' for p in result['paired_case_table'])


def test_input_invalid_excluded_but_runtime_error_stays_in_started_denominator():
 reg,rows=arithmetic_fixture()
 for r in (rows[0],rows[3]):
  r.update(status='PROCESS_ERROR_OR_NO_VERIFIED_PLAN',feasibility=False,candidate_feasibility=False)
  r.update({k:None for k in METRICS})
 rows[0].update(status='INPUT_INVALID',input_state='INVALID')
 result=aggregate_rows(reg,rows)
 assert result['paired_case_table'][0]['entries'][0]['exclusion_reason']=='INPUT_INVALID'
 d=next(t for t in result['all_trial_table'] if t['method']=='D')
 assert d['observed']==1 and d['runtime_errors']==1 and d['completion_rate_observed']==0


def test_registered_adapter_readonly_roundtrip_keeps_common_physics(tmp_path):
 frozen=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
 source=ROOT/frozen['inputs']['input_root']/'S1'
 lineage=tmp_path/'LINEAGE_TEST_ONLY.json'
 dump(lineage,{'dataset_id':'existing frozen S1 alias for adapter roundtrip only',
    'demand_seed':None,'candidate_source_hash':'0'*64,'not_a_new_demand_sample':True})
 case={'scale':'S1','input_dir':str(source),'files':frozen['inputs']['scenarios']['S1']['files'],
       'demand_seed':None,'generation_manifest':{'path':str(lineage),'sha256':digest(lineage)}}
 p=load_registered_scenario(source,case)
 assert (len(p.stops),len(p.vehicles),len(p.berths))==(1000,10,2)
 with pytest.raises(ValueError,match='VEHICLE_CONDITIONS'):
  replace(p,vehicles=(replace(p.vehicles[0],capacity=61),*p.vehicles[1:])).validate()
 bad=deepcopy(case);bad['generation_manifest']['sha256']='0'*64
 with pytest.raises(ValueError,match='GENERATION_MANIFEST_HASH'):
  load_registered_scenario(source,bad)
