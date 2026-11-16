"""Contract, evidence, physical and statistical checks; never real human data."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from kmd_toc.human_comparison_v1.contract import (CONTRACT,TIME_KIND,ROOT,FILES,REGISTRY,
    validate_plan,register,load_registration,digest,read,dump,fingerprint)
from kmd_toc.human_comparison_v1.evaluation import partition,union_seconds,evaluate
from kmd_toc.human_comparison_v1.analysis import (describe,paired_interval,aggregate,
    aggregate_rows,adoption,verify_session,pair_state,independence_reasons)
from kmd_toc.human_comparison_v1 import session
from kmd_toc.human_comparison_v1.inputs import sampling_plan
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.human_v1 import complete_manual
from kmd_toc.common.models import save_problem


def plan_for(tmp_path):
 source=tmp_path/'input';save_problem(artificial_problem(4,2,1),source)
 person={'experience':'scripted fixture, not a participant','tools':[{'name':'pytest','version':'fixture'}],
         'pc':{'os':'Linux','description':'synthetic validation host'},'procedure':'scripted test only',
         'planned_date':'2026-11-16','activity_recording':'participant_markers'}
 return {'experiment_id':'TEST_ONLY','mode':'human_inclusive','measurement_contract':CONTRACT,
  'phase':'contract_check','preparation_policy':'no_case_view_or_case_specific_tuning_before_start',
  'tuning_policy':'frozen_existing_BCD_no_case_tuning','stopping':'fixed_registered_runs','memory_limit_MiB':4096,
  'python':sys.executable,'participants':{'TEST_PERSON':person},
  'cases':[{'case_id':'case1','scenario_id':'synthetic-case1','scale':'ART_N4','kind':'synthetic_validation',
    'input_dir':str(source),'files':{n:digest(source/n) for n in FILES},'family_id':'synthetic-family',
    'independent_draw':False,'demand_seed':None,'total_limit_s':120,'machine_limit_s':30,'native_limit_s':10}],
  'runs':[{'run_id':m,'case_id':'case1','method':m,'repetition':1,'order_index':i,'max_attempts':3,
    'workflow':'human' if m=='A' else 'system_only','participant_id':'TEST_PERSON' if m=='A' else None,
    'prior_exposure_expected':False,'solver_seed':None if m=='A' else 101,
    'quantum_seed':102 if m=='D' else None,'analysis_role':'primary'} for i,m in enumerate('ABCD')],
  'statistics':{'scope':'fixed_cases','ci_method':'descriptive','confidence':.95,
    'pairs':[['A','D'],['C','D']],'rationale':'synthetic validation; no empirical inference'}}


def registered(tmp_path):
 p=plan_for(tmp_path);path=tmp_path/'plan.json';dump(path,p)
 reg_path=register(path,tmp_path/'registration')
 return p,reg_path,load_registration(reg_path)


@pytest.mark.parametrize('key',['mode','measurement_contract','cases','runs','statistics','stopping','memory_limit_MiB'])
def test_missing_preregistration_is_rejected(tmp_path,key):
 p=plan_for(tmp_path);del p[key]
 with pytest.raises((ValueError,KeyError)):validate_plan(p)


@pytest.mark.parametrize('key',['total_limit_s','machine_limit_s','native_limit_s'])
def test_missing_or_invalid_case_budgets(tmp_path,key):
 p=plan_for(tmp_path);p['cases'][0][key]=None
 with pytest.raises(ValueError):validate_plan(p)


@pytest.mark.parametrize('key',['experience','tools','pc','procedure','planned_date','activity_recording'])
def test_person_metadata_required(tmp_path,key):
 p=plan_for(tmp_path);p['participants']['TEST_PERSON'][key]=None
 with pytest.raises(ValueError):validate_plan(p)


def test_no_hidden_case_overrides_and_duplicate_trial_units(tmp_path):
 p=plan_for(tmp_path)
 for key in ('input_dir','physical_hash','config','budget_wall_s'):
  bad=deepcopy(p);bad['runs'][1][key]='override'
  with pytest.raises(ValueError,match='OVERRIDE'):validate_plan(bad)
 bad=deepcopy(p);bad['runs'].append(deepcopy(bad['runs'][0]));bad['runs'][-1]['run_id']='A_alias'
 with pytest.raises(ValueError,match='DUPLICATE_TRIAL_UNIT'):validate_plan(bad)
 bad=deepcopy(p);bad['cases'].append({**bad['cases'][0],'case_id':'alias'})
 with pytest.raises(ValueError,match='DUPLICATE_INPUT_BUNDLE'):validate_plan(bad)


def test_formal_does_not_accept_synthetic_or_missing_approval(tmp_path):
 p=plan_for(tmp_path);p['phase']='formal'
 with pytest.raises(ValueError,match='SYNTHETIC'):validate_plan(p)


def test_register_and_prepare_do_not_read_problem_payload(tmp_path,monkeypatch):
 p=plan_for(tmp_path);path=tmp_path/'plan.json';dump(path,p)
 import kmd_toc.common.models as models
 def forbidden(*a,**kw):raise AssertionError('PREMATURE_CASE_READ')
 monkeypatch.setattr(models,'load_problem',forbidden)
 reg_path=register(path,tmp_path/'registration')
 out=session.prepare(reg_path,'A',tmp_path/'session')
 assert read(out/'PREPARED.json')['input_payload_opened'] is False
 assert not (out/'stops.csv').exists()
 with pytest.raises(FileExistsError):session.prepare(reg_path,'A',tmp_path/'duplicate')


def test_time_partition_corrections_pauses_and_compute_union():
 e=[{'stage':s,'ns':t*10**9} for s,t in [('MACHINE',0),('HUMAN',2),('MACHINE',62),
    ('HUMAN',65),('OTHER',85),('HUMAN',95),('MACHINE',105),('END',107)]]
 r=partition(e)
 assert r['T_total_sec']==107 and r['T_human_sec']==90 and r['T_machine_sec']==7 and r['T_other_sec']==10
 assert union_seconds([(0,4*10**9),(2*10**9,6*10**9)])==6
 with pytest.raises(ValueError):partition([{'stage':'HUMAN','ns':2},{'stage':'END','ns':1}])


def test_direct_controller_checks_are_machine_time(tmp_path):
 p,path,reg=registered(tmp_path);out=session.prepare(path,'A',tmp_path/'session')
 session.append(out,'OTHER',operation='test_unassigned_gap')
 session.context(out)
 assert session.events(out)[-1]['stage']=='MACHINE'
 assert session.events(out)[-1]['detail']['operation']=='controller_integrity_checks'


def test_common_evaluator_same_metric_and_preserves_manual_decisions():
 p=artificial_problem(2,1,1)
 d=np.array([[0.,1000.,9000.],[3000.,0.,2000.],[4000.,8000.,0.]])
 t=np.array([[0.,1.2,8.1],[4.1,0.,2.2],[3.2,9.1,0.]])
 od=replace(p.od,distance_m=d,duration_s=t);p=replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))
 csv='vehicle_id,sequence,stop_id\nv0,1,c0002\nv0,2,c0001\n'
 q,_=complete_manual(p,csv)
 assert evaluate(p,q,human_csv=csv)['official_metrics']['D_km']==20
 assert evaluate(p,q)['official_metrics']==evaluate(p,q,human_csv=csv)['official_metrics']
 bad=replace(q,trips=(replace(q.trips[0],load_start_s=q.trips[0].ready_s-1),))
 assert evaluate(p,bad)['validated'] is False


def test_actual_human_mode_fixture_retry_and_aggregation(tmp_path):
 p,path,reg=registered(tmp_path);out=session.prepare(path,'A',tmp_path/'session')
 with pytest.raises(ValueError,match='EXPOSURE'):session.start(out)
 session.start(out,confirm_unseen=True)
 session.activity(out,True,'assignment_order','TEST_PERSON')
 session.activity(out,True,'pause','TEST_PERSON')
 assert session.events(out)[-1]['stage']=='OTHER'
 session.activity(out,True,'assignment_order','TEST_PERSON')
 first=session.attempt(out);assert not first['result'].get('validated')
 session.activity(out,True,'correction','TEST_PERSON')
 (out/'assignment.csv').write_text('vehicle_id,sequence,stop_id\nv0,1,c0003\nv0,2,c0001\nv1,1,c0004\nv1,2,c0002\n')
 second=session.attempt(out);assert second['result']['validated'],second
 session.activity(out,True,'review','TEST_PERSON')
 row=session.accept(out,attest_human=True,attest_reviewed=True)
 assert row['status']=='success' and row['T_total_sec'] is None and row['observed'] is False
 assert row['T_human_sec'] is None and row['T_compute_sec'] is None and row['revision_count']==1
 assert row['diagnostic_elapsed']['T_human_sec']>0 and row['T_attempt_sec']>row['diagnostic_elapsed']['T_machine_sec']
 verify_session(out,reg)
 result=aggregate(path,tmp_path/'aggregate')
 assert result['empirical_human_records']==0 and result['planned_runs']==4 and len(result['missing_or_incomplete'])==3
 assert not adoption(reg,result)['MEASURED'] and not adoption(reg,result)['formal_adoption']
 row['measurement_contract']='old_program_contract'
 with pytest.raises(ValueError,match='LEGACY'):aggregate_rows(reg,[row])
 row=read(out/'RESULT.json')
 with pytest.raises(ValueError,match='DUPLICATE'):aggregate_rows(reg,[row,row])


def test_hash_mismatch_is_rejected(tmp_path):
 p,path,reg=registered(tmp_path);out=session.prepare(path,'A',tmp_path/'session')
 meta=read(out/'PREPARED.json');meta['registration_hash']='0'*64
 (out/'PREPARED.json').write_text(json.dumps(meta))
 with pytest.raises(ValueError,match='REGISTRATION_CHANGED'):session.start(out,confirm_unseen=True)


def test_descriptive_and_ci_arithmetic_without_fake_research_observations():
 r=describe([1,2,3,4]);assert r['mean']==r['median']==2.5 and r['IQR']==1.5
 assert describe([1])['sd'] is None and describe([])['mean'] is None
 assert paired_interval([1],.95)['interval'] is None
 assert paired_interval([1,1],.95)['interval'] is None
 ci=paired_interval([1,2,3],.95);assert ci['interval'][0]<2<ci['interval'][1]
 with pytest.raises(ValueError):describe([float('nan')])


def test_additional_demand_generation_is_a_plan_not_runtime_regeneration():
 p=sampling_plan(dataset_id='future',candidate_manifest_hash='a'*64,scenario_ids=['i1','i2'],seeds=[1,2])
 assert len(p['requests'])==6 and p['runtime_generation'] is False
 assert all('NEEDS' in r['status'] for r in p['requests'])


@pytest.mark.parametrize('a,b,complete,expected',[
 (True,True,True,'BOTH_SUCCESS'),(True,False,True,'LEFT_ONLY_SUCCESS'),
 (False,True,True,'RIGHT_ONLY_SUCCESS'),(False,False,True,'BOTH_FAILED'),
 (True,True,False,'EXCLUDED_NOT_OBSERVED_OR_INCOMPLETE')])
def test_pair_failures_keep_correspondence(a,b,complete,expected):
 assert pair_state(a,b,complete)==expected
 # C/D's own status does not depend on whether A succeeded.
 assert pair_state(True,True,True)=='BOTH_SUCCESS'


def test_no_independence_from_seeds_or_reused_people():
 cases=[{'family_id':'nested','independent_draw':False},{'family_id':'nested','independent_draw':False}]
 r=independence_reasons(cases,{'person':{'c1','c2'}})
 assert set(r)=={'CASE_NOT_REGISTERED_AS_INDEPENDENT_DRAW','SHARED_DEMAND_FAMILY','REUSED_HUMAN_PARTICIPANT_ACROSS_CASES'}
 assert not independence_reasons([{'family_id':'a','independent_draw':True},{'family_id':'b','independent_draw':True}],{'p1':{'c1'},'p2':{'c2'}})


def test_real_timeout_control_and_no_late_success(tmp_path):
 p=plan_for(tmp_path);p['cases'][0].update(total_limit_s=30,machine_limit_s=.05,native_limit_s=.02)
 path=tmp_path/'plan.json';dump(path,p);reg_path=register(path,tmp_path/'registration')
 out=session.prepare(reg_path,'A',tmp_path/'session')
 r=session.start(out,confirm_unseen=True)
 assert 'TIMEOUT' in r['status'] and r['T_total_sec'] is None
 assert r['T_attempt_sec']>0 and r['observed'] is False
 proc=read(next((out/'attempts').glob('*/PROCESS.json')))
 assert proc['cleanup_proved']
 import os
 with pytest.raises(ProcessLookupError):os.killpg(proc['pid'],0)


def test_abnormal_restart_does_not_invent_monotonic_elapsed(tmp_path):
 p,path,reg=registered(tmp_path);out=session.prepare(path,'A',tmp_path/'session')
 r=session.recover(out,'test restart before input')
 assert r['T_total_sec'] is None and r['T_attempt_sec'] is None
 assert r['status']=='abnormal_interruption' and r['observed'] is False
 verify_session(out,reg)


def test_formal_template_is_not_silently_executable():
 p=read(ROOT/'configs/toc_delivery/human_comparison_v1_formal_template.json')
 with pytest.raises((ValueError,TypeError)):validate_plan(p)


def test_source_and_config_hash_mismatch(tmp_path):
 p,path,reg=registered(tmp_path)
 from kmd_toc.human_comparison_v1.contract import verify_sources
 bad=deepcopy(reg);key=next(iter(bad['source_hashes']));bad['source_hashes'][key]='0'*64
 with pytest.raises(ValueError,match='SOURCE_HASH'):verify_sources(bad)
 bad=deepcopy(reg);bad['physical_hash']='0'*64
 with pytest.raises(ValueError,match='PHYSICAL_HASH'):verify_sources(bad)


def test_observer_markers_require_registered_observer(tmp_path):
 p=plan_for(tmp_path);p['participants']['TEST_PERSON']['activity_recording']='observer_markers'
 with pytest.raises(ValueError,match='OBSERVER'):validate_plan(p)


def test_timed_input_hash_rejection(tmp_path):
 p=plan_for(tmp_path);p['cases'][0]['files']['input.json']='0'*64
 path=tmp_path/'plan.json';dump(path,p);reg_path=register(path,tmp_path/'registration')
 out=session.prepare(reg_path,'A',tmp_path/'session')
 r=session.start(out,confirm_unseen=True)
 assert r['status']=='INPUT_INVALID' and r['T_total_sec'] is None


def test_synthetic_result_cannot_be_promoted_to_measured(tmp_path):
 p,path,reg=registered(tmp_path)
 row={'run_id':'A','case_id':'case1','method':'A','measurement_contract':CONTRACT,
      'T_kind':TIME_KIND,'registration_hash':reg['registration_hash'],'observed':True}
 with pytest.raises(ValueError,match='FALSE_EMPIRICAL'):aggregate_rows(reg,[row])
