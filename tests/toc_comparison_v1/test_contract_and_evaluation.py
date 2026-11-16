from copy import deepcopy
import json
from pathlib import Path

import pytest

from kmd_toc.comparison_v1.contract import (CONTRACT_ID,TIME_KIND,REGISTRY,ROOT,fingerprint,
    read,run_identity,validate_manifest,check_freeze,digest)
from kmd_toc.comparison_v1.evaluation import (aggregate,build_reference,not_run,paired,score,
    summarize,validate_result)


def manifest():
    a=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
    b=read(ROOT/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json')
    runs=[{'run_id':m,'method':m,'case_id':'tiny','attempt_id':1,'repeat_id':1,'pair_id':'p1',
        'retry_of':None,'solver_seed':None if m=='A' else 101,'quantum_seed':102 if m=='D' else None,
        'reference_group_id':'ref'} for m in 'ABCD']
    physical=digest(ROOT/'configs/toc_delivery/common_conditions_v1_1.json')
    return {'contract_id':CONTRACT_ID,'T_kind':TIME_KIND,'phase':'contract_check','physical_hash':physical,
        'cases':[{'case_id':'tiny','scenario_id':'synthetic','scale':'ART_N12','budget_wall_s':20,
            'physical_hash':physical,'case_parameters':{'BCD_epsilon_W_min':None},
            'input':{'kind':'synthetic_validation','input_hash':'input','OD_hash':'od'}}],
        'runs':runs,'reference_groups':[{'group_id':'ref','purpose':'contract_check','run_ids':['A'],'required_count':1}],
        'A_config':a,'A_config_hash':fingerprint(a),'BCD_config':b,'BCD_config_hash':fingerprint(b),
        'A_config_file_hash':digest(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json'),
        'A_frozen_hash':fingerprint(check_freeze()),'source_hashes':{},
        'resource_contract':{'available_physical_cores':4,'A_processes':1,'BCD_internal_branches':4,
            'native_threads_per_process':1,'method_concurrency':1},'registry':REGISTRY}


def rows():
    m=manifest();out=[]
    for run in m['runs']:
        row=not_run(m,run)
        row.update(input_state='VALID',termination_reason='A_MOVE_LIMIT' if run['method']=='A' else 'NORMAL',
            validation_state='VALIDATED',adoptable=True,D=100.,W=20.,W_first=15.,W_reload=5.,
            T_program=4.,T_attempt=4.,plan_sha256='bytes',plan_semantic_hash='plan')
        out.append(row)
    return m,out


def failed(row,reason='NORMAL'):
    row.update(adoptable=False,validation_state='NO_PLAN',termination_reason=reason,
               D=None,W=None,W_first=None,W_reload=None,T_program=None)


def test_complete_manifest_and_missing_future_values_are_rejected():
    m=manifest();validate_manifest(m)
    for field in ('budget_wall_s','scenario_id','input','case_parameters'):
        bad=deepcopy(m);del bad['cases'][0][field]
        with pytest.raises(ValueError):validate_manifest(bad)
    bad=deepcopy(m);bad['cases'][0]['budget_wall_s']=None
    with pytest.raises(ValueError,match='BUDGET'):validate_manifest(bad)
    bad=deepcopy(m);bad['reference_groups'][0]['required_count']=None
    with pytest.raises(ValueError,match='REFERENCE_MEMBERSHIP'):validate_manifest(bad)
    bad=deepcopy(m);bad['cases'][0]['case_parameters']['BCD_native_cap_s']=21
    with pytest.raises(ValueError,match='NATIVE_CAP'):validate_manifest(bad)


@pytest.mark.parametrize('key',['input_hash','physical_hash','budget_wall_s','T_kind','config'])
def test_no_method_specific_common_overrides(key):
    m=manifest();m['runs'][1][key]='different'
    with pytest.raises(ValueError,match='OVERRIDE'):validate_manifest(m)


def test_config_and_legacy_guards():
    for change in ('old_contract','old_A','old_ref','old_time','changed_BCD'):
        m=manifest()
        if change=='old_contract':m['contract_id']='legacy'
        if change=='old_A':m['runs'][0]['method']='A2'
        if change=='old_ref':m['reference']={'S1':{'T_program_s':60}}
        if change=='old_time':m['T_kind']='program_wall'
        if change=='changed_BCD':m['BCD_config']['D']['pricing_rounds']=0
        with pytest.raises(ValueError):validate_manifest(m)


def test_reference_median_and_individual_A_J_not_forced_to_one():
    m,r=rows();a=deepcopy(r[0]);a.update(run_id='A2',T_program=8.)
    group={'group_id':'g','purpose':'contract_check','required_count':2,'run_ids':['A','A2']}
    ref=build_reference(group,{'A':r[0],'A2':a})
    assert ref['T_A_ref']==6. and ref['established'] and not ref['formal_reference']
    assert score(r[0],ref)['J']==pytest.approx((1+1+4/6)/3)
    baseline={**r[0],'T_program':6.}
    assert score(baseline,ref)=={'J':1.,'J_reason':'DEFINED'}


@pytest.mark.parametrize('kind,reason',[
    ('missing','A_TIME_REFERENCE_INCOMPLETE'),('not_run','A_TIME_REFERENCE_INCOMPLETE'),
    ('failed','REFERENCE_TRIAL_FAILED'),('plan','A_REFERENCE_PLAN_MISMATCH'),
    ('D','A_REFERENCE_PLAN_MISMATCH'),('Wzero','ZERO_REFERENCE_DENOMINATOR'),
    ('inf','NONFINITE_VALUE'),('legacy','LEGACY_METHOD_OR_CONTRACT')])
def test_reference_unavailable(kind,reason):
    _,r=rows();a=deepcopy(r[0]);a['run_id']='A2'
    group={'group_id':'g','purpose':'contract_check','required_count':2,'run_ids':['A','A2']}
    data={'A':r[0],'A2':a}
    if kind=='missing':del data['A2']
    if kind=='not_run':a['termination_reason']='NOT_STARTED'
    if kind=='failed':failed(a)
    if kind=='plan':a['plan_semantic_hash']='other'
    if kind=='D':a['D']=101
    if kind=='Wzero':a['W']=r[0]['W']=0.
    if kind=='inf':a['T_program']=float('inf')
    if kind=='legacy':a['implementation_id']='A2_with_completion'
    ref=build_reference(group,data)
    assert not ref['established'] and ref['reason']==reason
    assert score(r[3],ref)=={'J':None,'J_reason':reason}


@pytest.mark.parametrize('key,reason',[('T_kind','TIME_SCOPE_MISMATCH'),
    ('resource_contract_hash','RESOURCE_CONTRACT_MISMATCH'),('input_hash','INPUT_CONDITIONS_MISMATCH'),
    ('OD_hash','INPUT_CONDITIONS_MISMATCH'),('budget_wall_s','INPUT_CONDITIONS_MISMATCH'),
    ('contract_id','LEGACY_METHOD_OR_CONTRACT')])
def test_J_mismatch(key,reason):
    m,r=rows();ref=build_reference(m['reference_groups'][0],{x['run_id']:x for x in r})
    r[3][key]='different'
    assert score(r[3],ref)=={'J':None,'J_reason':reason}


def test_zero_nonfinite_target_invalid_and_no_ref():
    m,r=rows();ref=build_reference(m['reference_groups'][0],{x['run_id']:x for x in r})
    assert score(r[3],None)['J_reason']=='A_REFERENCE_PLAN_MISSING'
    ref['T_A_ref']=0
    assert score(r[3],ref)['J_reason']=='ZERO_REFERENCE_DENOMINATOR'
    ref['T_A_ref']=1;r[3]['D']=float('nan')
    assert score(r[3],ref)['J_reason']=='NONFINITE_VALUE'
    failed(r[3]);assert score(r[3],ref)['J_reason']=='TARGET_PLAN_INVALID'


@pytest.mark.parametrize('fail_left,fail_right,expected',[(False,False,'BOTH_SUCCESS'),
    (True,False,'RIGHT_ONLY_SUCCESS'),(False,True,'LEFT_ONLY_SUCCESS'),(True,True,'BOTH_FAILED')])
def test_pair_outcomes(fail_left,fail_right,expected):
    _,r=rows()
    if fail_left:failed(r[0])
    if fail_right:failed(r[3])
    result=paired(r,'A','D')
    assert result['entries'][0]['status']==expected
    assert result['raw_adopted_cases']==int(expected=='BOTH_SUCCESS')


def test_A_failure_keeps_CD_raw_without_J():
    m,r=rows();failed(r[0])
    ref=build_reference(m['reference_groups'][0],{x['run_id']:x for x in r})
    for x in r:x.update(score(x,ref))
    result=paired(r,'C','D')
    assert result['raw_adopted_cases']==1 and result['J_adopted_cases']==0
    assert result['entries'][0]['raw']['D']['C']==100


def test_errors_timeouts_invalid_inputs_notrun_retry_denominators():
    m,r=rows();failed(r[1],'CHILD_PROCESS_ERROR');failed(r[2],'OUTER_WALL_LIMIT')
    invalid=deepcopy(r[0]);failed(invalid,'INPUT_INVALID');invalid.update(run_id='bad',input_state='INVALID')
    missing=not_run(m,m['runs'][0]);missing['run_id']='unrun'
    retry=deepcopy(r[0]);retry.update(run_id='retry',retry_of='A',attempt_id=2)
    result=summarize(r+[invalid,missing,retry])
    a=next(x for x in result if x['method']=='A')
    assert a['planned']==4 and a['executed']==3 and a['valid_input_executed']==2
    assert a['retry_count']==1 and a['input_invalid_count']==1 and a['not_executed_count']==1
    b=next(x for x in result if x['method']=='B')
    assert b['valid_input_executed']==1 and b['success_rate']==0 and b['runtime_error_count']==1
    c=next(x for x in result if x['method']=='C')
    assert c['valid_input_executed']==1 and c['limit_stop_count']==1 and c['success_rate']==0
    assert a['limit_stop_count']==0  # A_MOVE_LIMIT is normal algorithm termination.
    assert paired(r+[retry],'A','D')['retries_not_substituted_for_primary']==['retry']


def test_validated_limit_and_invalid_plan_adoption_guards():
    m,r=rows();r[0]['termination_reason']='OUTER_WALL_LIMIT';validate_result(r[0],run_identity(m,m['runs'][0]))
    r[0]['validation_state']='INVALID_PLAN'
    from jsonschema import ValidationError
    with pytest.raises((ValueError,ValidationError)):validate_result(r[0],run_identity(m,m['runs'][0]))
    failed(r[0]);r[0]['D']=1
    with pytest.raises((ValueError,ValidationError)):validate_result(r[0],run_identity(m,m['runs'][0]))


def test_full_aggregation_missing_trials_and_no_success_only_references(tmp_path):
    m,r=rows();path=tmp_path/'REGISTERED.json';path.write_text(json.dumps(m))
    # Leave prespecified A absent; C/D raw comparisons must survive.
    for row in r[1:]:
        out=tmp_path/'runs'/row['run_id'];out.mkdir(parents=True)
        (out/'result.json').write_text(json.dumps(row))
    out=tmp_path/'tables';result=aggregate(path,out)
    assert result['all_attempts']==4 and result['adoptable']==3
    assert result['references']['ref']['reason']=='A_TIME_REFERENCE_INCOMPLETE'
    stored=read(out/'ALL_ATTEMPTS.json')['rows']
    assert stored[0]['termination_reason']=='NOT_STARTED'
    pairs=read(out/'PAIRED_COMPARISONS.json')['pairs']
    assert next(x for x in pairs if x['pair']==['C','D'])['raw_adopted_cases']==1
    corrupt=tmp_path/'runs'/'C'/'result.json';row=read(corrupt);row['input_hash']='other';corrupt.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='IDENTITY'):aggregate(path,tmp_path/'reject')


def test_plan_transport_preserves_bytes_and_semantics(tmp_path):
    from dataclasses import asdict
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.baseline_a.rule_v1 import generate
    from kmd_toc.comparison_v1.contract import atomic,digest
    from kmd_toc.common.models import load_plan
    p=artificial_problem(12,4,1);plan,_=generate(p)
    raw=json.dumps(asdict(plan),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    original=tmp_path/'original.json';original.write_text(raw)
    transport=tmp_path/'transport.json';atomic(transport,asdict(plan))
    assert digest(original)==digest(transport)
    loaded=load_plan(transport)
    assert loaded.trips==plan.trips
    assert fingerprint(asdict(loaded))==fingerprint(asdict(plan))


def test_any_real_road_registration_rejects_table_before_method_execution(tmp_path):
    from kmd_toc.comparison_v1.contract import input_inventory
    (tmp_path/'od').mkdir()
    (tmp_path/'input.json').write_text(json.dumps({'experiment':{'kind':'road_validation'}}))
    (tmp_path/'od/manifest.json').write_text(json.dumps({'metadata':{'table_distances_used':True,
        'matrix_service':'Table'}}))
    with pytest.raises(ValueError,match='REQUIRES_ROUTE_PAIR_OD_NOT_TABLE'):input_inventory(tmp_path)
