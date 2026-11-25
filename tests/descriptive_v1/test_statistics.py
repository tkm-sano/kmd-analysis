import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from kmd_toc.descriptive_v1 import statistics as s
from kmd_toc.descriptive_v1.analysis import analyze,_pairs,_A_gate
from kmd_toc.descriptive_v1.inputs import Reader,load_rows
from kmd_toc.descriptive_v1.pipeline import dump,write_analysis
from kmd_toc.descriptive_v1.policy import ROOT,VERSION,PINS,require_frozen,digest


@pytest.fixture
def fixture_module():
    spec=importlib.util.spec_from_file_location('stats_fixture',ROOT/'scripts/statistical_scope_20261121_v1/audit_and_demo.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_summary_known_sample_and_mcse():
    z=s.summary([1,2,3],independent=True)
    assert {k:z[k] for k in ('J','mean','SD','median','Q1','Q3','IQR','min','max')}=={
        'J':3,'mean':2,'SD':1,'median':2,'Q1':1.5,'Q3':2.5,'IQR':1,'min':1,'max':3}
    assert z['MCSE']==pytest.approx(1/math.sqrt(3))
    assert s.summary([1,2,3])['MCSE'] is None


@pytest.mark.parametrize('values', [[],[3]])
def test_insufficient_sd_not_zero(values):
    z=s.summary(values,independent=True)
    assert z['SD'] is None and z['MCSE'] is None


def test_observed_zero_sd_no_determinism_inference_or_j_adoption():
    z=s.summary([7]*4,independent=True)
    assert z['SD']==z['MCSE']==0 and z['observed_zero_SD']
    assert z['zero_SD_is_determinism_proof'] is False and z['formal_J']=='HOLD'


@pytest.mark.parametrize('bad',[None,True,float('nan'),float('inf'),'2'])
def test_no_missing_or_non_numeric_zero_imputation(bad):
    with pytest.raises(ValueError):s.summary([bad])


def test_quantiles_fences_outliers_and_interpolation():
    assert s.quantile([0,10],.25)==2.5
    assert s.quantile([1,2,3,4],.75)==3.25
    z=s.summary([0,0,0,2,5]);assert z['Q3']==2 and z['whisker_high']==5 and not z['outliers']
    z=s.summary([1,2,3,4,100]);assert z['whisker_high']==4 and z['outliers']==[100]
    assert z['mean']==22 # outliers remain in descriptive statistics


def test_direct_differences_sd_not_group_sd():
    z=s.paired([10,20,30],[9,19,29],independent_pairs=True)
    assert z['delta_values']==[-1]*3
    assert z['delta']['SD']==z['delta']['MCSE']==0
    assert z['relative_rate_values']==pytest.approx([10,5,100/30])
    assert s.paired([0,1],[0,0])['undefined_rate_count']==1
    with pytest.raises(ValueError):s.paired([1,2],[1])


def test_independent_group_means_do_not_create_trial_differences():
    z=s.independent_contrast([1,2,3],[3,4,5],independent_groups=True)
    assert z['mean_delta']==2 and z['SD_delta'] is None
    assert z['MCSE_delta']==pytest.approx(math.sqrt(2/3))
    assert z['trial_difference_distribution'] is None
    assert s.independent_contrast([1,2,3],[3,4,5])['MCSE_delta'] is None


@pytest.mark.parametrize('cd,cw,xd,xw,expected',[(100,50,90,45,10),(100,50,90,50,0),
    (100,50,90,55,-10),(0,50,0,45,None),(100,0,90,0,None),(0,0,0,0,None)])
def test_dual_definitions(cd,cw,xd,xw,expected):
    if expected is None:assert s.dual(cd,cw,xd,xw) is None
    else:assert s.dual(cd,cw,xd,xw)==pytest.approx(expected)


def test_trial_index_mean_is_not_index_of_means():
    c=[{'D':100,'W':10},{'D':10,'W':100},{'D':0,'W':50}]
    x=[{'D':90,'W':5},{'D':5,'W':90},{'D':0,'W':40}]
    z=s.paired_dual(c,x,independent_pairs=True)
    assert z['summary']['mean']==10 and z['summary']['J']==2 and z['undefined_count']==1
    assert z['strict_dual_fraction']==pytest.approx(2/3)
    assert s.dual(55,55,47.5,47.5)!=10


def test_pairing_requires_more_than_seed_or_fixed_problem():
    rows={k:{'trial_id':k,'scale':'S1','method':m,'eligible':True,'D':1,'W':1} for k,m in [('c','C'),('d','D')]}
    d={'scale':'S1','baseline':'C','comparison':'D','kind':'paired_common_random_factors','pairs':[['c','d']]}
    proof={'kind':d['kind'],'registered_before_results':True,'pairs':d['pairs'],'independent_pairs':True}
    for factors in [[],['same_seed'],['same_index','fixed_demand']]:
        with pytest.raises(ValueError,match='IS_NOT_PAIRING'):_pairs(d,rows,lambda _:dict(proof,stochastic_shared_factors=factors))
    a,b,ind=_pairs(d,rows,lambda _:dict(proof,stochastic_shared_factors=['shared_initial_randomization']))
    assert a[0]['method']=='C' and b[0]['method']=='D' and ind
    with pytest.raises(ValueError,match='PRIOR_DESIGN'):_pairs(d,rows,lambda _:dict(proof,registered_before_results=False))


def test_no_reuse_or_fixed_reference_certificate_from_sd_zero():
    rows={k:{'trial_id':k,'scale':'S1','method':m,'eligible':True,'D':1,'W':1} for k,m in [('c','C'),('d','D'),('d2','D')]}
    d={'scale':'S1','baseline':'C','comparison':'D','kind':'paired_common_random_factors','pairs':[['c','d'],['c','d2']]}
    proof={'kind':d['kind'],'registered_before_results':True,'pairs':d['pairs'],'stochastic_shared_factors':['initial_randomness']}
    with pytest.raises(ValueError,match='REUSED'):_pairs(d,rows,lambda _:proof)
    d['kind']='certified_fixed_reference';proof['kind']=d['kind']
    with pytest.raises(ValueError,match='CERTIFICATE'):_pairs(d,rows,lambda _:proof)
    proof.update(deterministic_certified=True,certificate='algorithm/config proof, not observed SD=0',independent_pairs=True)
    assert len(_pairs(d,rows,lambda _:proof)[0])==2


def test_fixture_five_comparisons_scale_separation_and_precision(tmp_path,fixture_module):
    path=fixture_module.fixture(tmp_path/'fixture');reg=json.loads(path.read_text());reader=Reader(path)
    rows=load_rows(reg,reader);z=analyze(reg,rows,reader.evidence)
    assert len(rows)==54 and len(z['summaries'])==18 and len(z['comparisons'])==30
    by={(r['scale'],r['method'],r['metric']):r for r in z['summaries']}
    assert by['S1','C','D']['J']==6 and by['S3','C','D']['mean']==4*by['S1','C','D']['mean']
    assert all(r['strict_dual_fraction']==pytest.approx(5/6) for r in z['dual_trials'] if r['method']=='D')
    assert all(r['A_SD'] is None and r['A_J'] is None and r['status']=='HOLD_A_COMPARABILITY' for r in z['comparisons'] if r['baseline']=='A')
    reg['comparison_designs']=[];reg['dual_designs']=[]
    z=analyze(reg,rows,reader.evidence)
    assert not z['dual_trials']
    assert all(r['SD_delta'] is None and r['MCSE_delta'] is None for r in z['comparisons'] if r['baseline']!='A')


def test_A_comparability_and_constant_reference_difference_sd(tmp_path,fixture_module):
    path=fixture_module.fixture(tmp_path/'fixture');reg=json.loads(path.read_text());reader=Reader(path)
    ref={'value':100,'comparability_audit':{k:{'status':'PASS','evidence':'synthetic comparability fixture only'} for k in
         ('unit','measurement_scope','time_context','spatial_context','aggregation_target')}}
    assert _A_gate(ref);reg['A_references']={'S1':{'D':ref}}
    z=analyze(reg,load_rows(reg,reader),reader.evidence)
    a=next(r for r in z['comparisons'] if (r['scale'],r['baseline'],r['comparison'],r['metric'])==('S1','A','D','D'))
    assert a['A_J'] is None and a['A_SD'] is None
    assert a['SD_delta']==s.summary([90,91,93,89,92,95])['SD']
    del ref['comparability_audit']['time_context'];assert not _A_gate(ref)


def test_branch_retry_failures_not_valid_j_or_zero(tmp_path):
    def row(i,**kw):return {'trial_id':str(i),'outer_unit_id':str(i),'scale':'S1','method':'D',
        'order':i,'unit_type':'outer_trial','status':'SUCCESS','D':10,'W':5,**kw}
    reg={'version':VERSION,'data_role':'synthetic_statistics_fixture','trials':[
        row(0),row(1,branch_id=0),row(2,retry_of='0'),row(3,status='MISSING'),row(4,status='INFEASIBLE'),row(5,status='FAILED')]}
    reader=Reader(tmp_path/'registration.json');rows=load_rows(reg,reader);z=analyze(reg,rows,lambda _: {})
    group=next(r for r in z['summaries'] if (r['scale'],r['method'],r['metric'])==('S1','D','D'))
    failure=next(r for r in z['failures'] if (r['scale'],r['method'])==('S1','D'))
    assert group['J']==1 and group['mean']==10
    assert failure['registered_outer_attempts']==4 and failure['nonouter_or_retry_records']==2
    assert failure['missing_fraction']==failure['infeasible_fraction']==.25
    assert max(r['registered_prefix'] for r in z['prefixes'])==4
    assert all(r['D'] is None for r in rows[1:])


def test_real_role_requires_saved_plan_and_execution_evidence(tmp_path):
    reg={'version':VERSION,'data_role':'verified_outer_trials','cases':{},'trials':[
        {'trial_id':'d','outer_unit_id':'d','scale':'S1','method':'D','order':0,'unit_type':'outer_trial','status':'SUCCESS','D':10,'W':5}]}
    row=load_rows(reg,Reader(tmp_path/'r.json'))[0]
    assert not row['eligible'] and row['D'] is None


def test_saved_plan_recalculated_not_trusted_scalars(tmp_path):
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.fcfs_v1.scheduler import schedule
    from kmd_toc.common.models import save_problem,save_plan
    p=artificial_problem(2,1,1);plan=schedule(p,{('v0',1):('c0001','c0002')},'C')
    save_problem(p,tmp_path/'input');save_plan(plan,tmp_path/'plan.json')
    evidence={'trial_id':'c','outer_unit_id':'c','scale':'S1','method':'C','unit_type':'outer_trial',
        'problem_hash':p.fingerprint,'od_hash':p.od.fingerprint,'plan_sha256':digest(tmp_path/'plan.json'),'comparison_profile':'synthetic_saved_plan_gateway_test'}
    dump(tmp_path/'proof.json',evidence)
    reg={'version':VERSION,'data_role':'verified_outer_trials','cases':{'S1':{'input_path':'input',
        'base_problem_hash':p.fingerprint,'od_hash':p.od.fingerprint,'operating_version':'FCFS_v1','comparison_profile':evidence['comparison_profile']}},'trials':[
        {'trial_id':'c','outer_unit_id':'c','scale':'S1','method':'C','order':0,'unit_type':'outer_trial','status':'SUCCESS','D':9999,'W':9999,
         'plan':{'path':'plan.json','sha256':digest(tmp_path/'plan.json')},'outer_evidence':{'path':'proof.json','sha256':digest(tmp_path/'proof.json')}}]}
    reader=Reader(tmp_path/'reg.json');r=load_rows(reg,reader)[0]
    assert r['eligible'] and r['D']!=9999 and r['W']==0 and not reader.unchanged()
    (tmp_path/'plan.json').write_text('{}')
    assert str(tmp_path/'plan.json') in reader.unchanged()
    r=load_rows(reg,Reader(tmp_path/'reg.json'))[0];assert not r['eligible'] and 'HASH_MISMATCH' in r['exclusion_reason']


def test_duty_saved_plan_and_no_version_mixing(tmp_path):
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.common.models import save_problem
    from kmd_toc.duty_break_v1.models import activate,RestOptions,save_plan
    from kmd_toc.duty_break_v1.scheduler import schedule
    base=artificial_problem(2,1,1);p=activate(base,version='duty-break-20261121-v1',rest_options=RestOptions(True))
    plan=schedule(p,{('v0',1):('c0001','c0002')},'D')
    save_problem(base,tmp_path/'input');save_plan(plan,tmp_path/'plan.json')
    proof={'trial_id':'d','outer_unit_id':'d','scale':'S1','method':'D','unit_type':'outer_trial','problem_hash':p.fingerprint,
        'od_hash':p.od.fingerprint,'plan_sha256':digest(tmp_path/'plan.json'),'comparison_profile':'duty_test_only'}
    dump(tmp_path/'proof.json',proof)
    case={'input_path':'input','base_problem_hash':base.fingerprint,'od_hash':base.od.fingerprint,
          'operating_version':'duty-break-20261121-v1','rest_options':{'allow_assumed_locations':True},'comparison_profile':'duty_test_only'}
    reg={'version':VERSION,'data_role':'verified_outer_trials','cases':{'S1':case},'trials':[
        {'trial_id':'d','outer_unit_id':'d','scale':'S1','method':'D','order':0,'unit_type':'outer_trial','status':'SUCCESS',
         'plan':{'path':'plan.json','sha256':digest(tmp_path/'plan.json')},'outer_evidence':{'path':'proof.json','sha256':digest(tmp_path/'proof.json')}}]}
    row=load_rows(reg,Reader(tmp_path/'reg.json'))[0];assert row['eligible'] and row['W']==0
    case['operating_version']='FCFS_v1'
    row=load_rows(reg,Reader(tmp_path/'reg.json'))[0];assert not row['eligible']


def test_repeated_rng_id_disables_mcse_even_with_design_claim(tmp_path,fixture_module):
    path=fixture_module.fixture(tmp_path/'fixture');reg=json.loads(path.read_text());reader=Reader(path)
    for r in reg['trials']:
        if r['scale']=='S1' and r['method']=='D':r['seed_identity']='same_complete_RNG_identity'
    z=analyze(reg,load_rows(reg,reader),reader.evidence)
    assert next(r for r in z['summaries'] if (r['scale'],r['method'],r['metric'])==('S1','D','D'))['MCSE'] is None
    assert all(r['MCSE_delta'] is None for r in z['comparisons'] if r['scale']=='S1')
    assert next(r for r in z['dual_trials'] if (r['scale'],r['method'])==('S1','D'))['summary']['MCSE'] is None


def test_no_A_distribution_duplicate_order_or_wrong_role(tmp_path):
    t={'trial_id':'a','outer_unit_id':'a','scale':'S1','method':'A','order':0,'unit_type':'outer_trial','status':'SUCCESS','D':1,'W':1}
    reg={'version':VERSION,'data_role':'synthetic_statistics_fixture','trials':[t]};reader=Reader(tmp_path/'r.json')
    with pytest.raises(ValueError,match='NO_A'):load_rows(reg,reader)
    t['method']='B';reg['trials'].append(dict(t,trial_id='b',outer_unit_id='b'))
    with pytest.raises(ValueError,match='ORDER_MUST_BE_UNIQUE'):analyze(reg,load_rows(reg,reader),lambda _: {})
    reg['data_role']='unversioned_results'
    with pytest.raises(ValueError,match='DATA_ROLE'):load_rows(reg,reader)


def test_prior_work_protected_and_guides_original_body_preserved():
    folder=ROOT/'docs/research/statistical_scope_20261121_v1'
    before=json.loads((folder/'PRESERVATION_BEFORE.json').read_text())
    assert not [name for name,sha in before['files'].items() if name not in before['editable'] and digest(ROOT/name)!=sha]
    for name in before['editable']:
        if name!='scripts/analyze_dw.py':assert (ROOT/name).read_bytes().endswith((folder/'before'/name).read_bytes())


def test_version_policy_and_spec_pinned(tmp_path):
    z=require_frozen();assert z['version']==VERSION
    assert '統計的仮説検定および有意性の判定は実施しない。' in z['formal_statement']
    for path in PINS:
        target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
    require_frozen(tmp_path)
    (tmp_path/next(iter(PINS))).write_text('{}')
    with pytest.raises(ValueError,match='FREEZE_CHANGED'):require_frozen(tmp_path)


def test_pipeline_no_overwrite_and_internal_diagnostics(tmp_path,fixture_module):
    path=fixture_module.fixture(tmp_path/'fixture')
    z=write_analysis(path,tmp_path/'out',figures=False)
    assert z['formal_J'] is None and z['MDE']=='SUPERSEDED' and z['hypothesis_testing']=='NOT_PERFORMED'
    assert (tmp_path/'out/internal/I_DUAL_PREFIXES.csv').exists()
    assert (tmp_path/'out/internal/CONTRAST_PREFIXES.csv').exists()
    assert json.loads((tmp_path/'out/J_DECISION.json').read_text())['MCSE_tolerance'] is None
    with pytest.raises(FileExistsError):write_analysis(path,tmp_path/'out',figures=False)


def test_single_pair_mcse_undefined_for_sample_size_not_independence(tmp_path,fixture_module):
    import csv
    path=fixture_module.fixture(tmp_path/'fixture');reg=json.loads(path.read_text())
    for t in reg['trials']:
        if t['order']>0:t['status']='MISSING'
    path.write_text(json.dumps(reg));write_analysis(path,tmp_path/'out',figures=False)
    for name in ('CONTRAST_PREFIXES.csv','I_DUAL_PREFIXES.csv'):
        with (tmp_path/'out/internal'/name).open() as f:rows=list(csv.DictReader(f))
        assert rows and all(r['MCSE_status']=='UNDEFINED_J_LT_2' for r in rows)


def test_dispatcher_and_removed_test_arguments(tmp_path,fixture_module):
    path=fixture_module.fixture(tmp_path/'fixture')
    result=subprocess.run([sys.executable,str(ROOT/'scripts/analyze_dw.py'),'--statistics-registration',str(path),
        '--output',str(tmp_path/'out'),'--no-figures'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'HOLD' in result.stdout
    result=subprocess.run([sys.executable,str(ROOT/'scripts/analyze_descriptive_v1.py'),'--alpha','0.05'],capture_output=True)
    assert result.returncode!=0
