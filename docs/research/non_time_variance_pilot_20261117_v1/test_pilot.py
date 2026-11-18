"""Management/statistics fixtures only: no additional actual-scale planning."""
import copy
import json
from pathlib import Path
import pytest
import pilot
import analysis

@pytest.fixture
def manifest():
    runs=pilot.make_runs()
    return {'experiment_id':pilot.ID,'phase':'non_time_variance_pilot','executable':True,'r_pilot':5,
        'T_kind':pilot.TIME_KIND,'config':pilot.read(pilot.runner.CONFIG),'config_hash':pilot.digest(pilot.runner.CONFIG),
        'runs':runs,'run_list_hash':pilot.fingerprint(runs)}

def test_exact_75_block_randomization_seed_and_A(manifest):
    pilot.validate(manifest)
    assert len({r['run_id'] for r in manifest['runs']})==75
    assert manifest['runs']==pilot.make_runs()
    for i in range(5):
        b=manifest['runs'][15*i:15*i+15]
        assert {(r['case_id'],r['method']) for r in b}=={(s,m) for s in pilot.SCALES for m in pilot.METHODS}
        assert {r['repeat_id'] for r in b}=={i+1}
    for r in manifest['runs']:
        assert len(r['branches'])==(1 if r['method']=='A' else 4)
        if r['method']=='A':assert all(v is None for v in r['seeds'].values())

def test_registration_rejects_count_order_config_and_main(manifest):
    for change in ('drop','order','seed','config','main'):
        m=copy.deepcopy(manifest)
        if change=='drop':m['runs'].pop()
        if change=='order':m['runs'].reverse()
        if change=='seed':m['runs'][0]['seeds']['solver_seed']=17
        if change=='config':m['config']['D']['max_evaluations']=79
        if change=='main':m['executable']=False;m['phase']='formal'
        with pytest.raises(ValueError):pilot.validate(m)

def test_registration_lock_changes_rejected(manifest):
    lock={'manifest_fingerprint':pilot.fingerprint(manifest)}
    pilot.validate(manifest,lock)
    manifest['extra']='changed'
    with pytest.raises(ValueError,match='REGISTRATION_CHANGED'):pilot.validate(manifest,lock)

def test_three_attempt_states_distinct(tmp_path):
    d=tmp_path/'trial'
    assert pilot.attempt_state(d)=='NOT_STARTED'
    d.mkdir();(d/'STARTED.json').write_text('{}')
    assert pilot.attempt_state(d)=='UNFINISHED'
    (d/'RESULT.json').write_text('{"adoptable":false,"execution_state":"ERROR"}')
    assert pilot.attempt_state(d)=='FINISHED'

def test_no_rerun_of_finished_failure_and_no_main(tmp_path,monkeypatch):
    d=tmp_path/'runs'/'a';d.mkdir(parents=True);(d/'RESULT.json').write_text('{"adoptable":false}')
    m={'runs':[{'run_id':'a'}]}
    monkeypatch.setattr(pilot,'load_registration',lambda _:m)
    monkeypatch.setattr(pilot,'preflight',lambda _:None)
    monkeypatch.setattr(pilot.runner,'execute',lambda *a:pytest.fail('must not rerun completed failure'))
    pilot.run(tmp_path)
    assert pilot.read(tmp_path/'LAST_INVOCATION.json')['new_completed_ids']==[]

def test_unfinished_never_restarted(tmp_path,monkeypatch):
    (tmp_path/'runs'/'a').mkdir(parents=True)
    monkeypatch.setattr(pilot,'load_registration',lambda _:{'runs':[{'run_id':'a'}]})
    monkeypatch.setattr(pilot,'preflight',lambda _:None)
    monkeypatch.setattr(pilot.runner,'execute',lambda *a:pytest.fail('must not restart unfinished'))
    with pytest.raises(ValueError,match='UNFINISHED'):pilot.run(tmp_path)

def test_zero_insufficient_nonzero_Welch():
    zero=analysis.stats([10]*5)
    assert zero['sample_SD']==0
    c=analysis.independent_difference(zero,zero)
    assert c['CI95'] is None and c['null_reason']=='BOTH_SAMPLE_VARIANCES_ZERO'
    assert analysis.independent_difference(analysis.stats([1]),zero)['null_reason']=='INSUFFICIENT_SUCCESS_COUNT'
    c=analysis.independent_difference(analysis.stats([1,2,3]),analysis.stats([2,3,4]))
    assert c['mean_difference']==1 and c['CI95'][0]<1<c['CI95'][1]

def test_rates_pending_null_denominator_and_all_success():
    assert analysis.rate_record(0,0)['all_started']['Wilson95'] is None
    r=analysis.rate_record(3,4,1)
    assert r['all_started']['estimate'] is None and r['provisional_settled_only']['denominator']==4
    r=analysis.rate_record(5,5)
    assert 0<r['all_started']['Clopper_Pearson95'][0]<1
    assert analysis.rate_count(.15)==39 and analysis.rate_count(.1)==93 and analysis.rate_count(.05)==381

def test_failed_quality_not_imputed_and_long_times_not_trimmed():
    assert analysis.stats([None,None])['mean'] is None
    assert analysis.stats([1,2,3,4,10000])['max']==10000
    assert analysis.stats([1,2,3,4,10000])['n']==5

def fake_groups():
    return {s:{m:{'metrics':{'D':analysis.stats([10]*5)},'T_attempt_all':analysis.stats([10,11,12,13,14]),
        'success_exact95':analysis.clopper(5,5)} for m in pilot.METHODS} for s in pilot.SCALES}

def test_unidentified_vs_assumed_SD_candidates_and_three_scale_costs():
    table,vs=analysis.candidate_table(fake_groups())
    for c in table:
        if c['variance_mode'] in ('observed','normal_variance_upper'):
            assert c['total_attempts_all_scales'] is None
            assert c['quality_R_null_reasons']
        else:
            assert c['total_attempts_all_scales']>=15*c['rate_required_attempts_each']
            assert c['estimated_T_attempt_wall_s']==12*c['total_attempts_all_scales']
            for s in pilot.SCALES:assert c['quality_predicted_halfwidth_km'][s]<=c['h_D_km']
        assert c['adopted'] is False and c['finite_wall_upper_bound_s'] is None
    assert all(v['planning_variance_C'] is None for v in vs if v['mode']=='normal_variance_upper')

def test_positive_upper_variance_and_Bonferroni():
    g=fake_groups()
    for s in pilot.SCALES:
        for m in ('C','D'):g[s][m]['metrics']['D']=analysis.stats([1,2,3,4,5])
    table,vs=analysis.candidate_table(g)
    assert all(v['planning_variance_C']>v['observed_variance_C'] for v in vs if v['mode']=='normal_variance_upper')
    lookup={c['candidate_id']:c for c in table}
    a=next(c for c in table if c['scope']=='inherited_S2_primary' and c['variance_mode']=='additional_SD' and c['sigma_add_each_group_km']==10 and c['h_D_km']==1 and c['rate_Wilson_worst_halfwidth']==.15 and c['allocation']=='uniform_all_15')
    b=lookup[a['candidate_id'].replace('inherited_S2_primary','three_scale_primary_Bonferroni')]
    assert b['total_attempts_all_scales']>a['total_attempts_all_scales']

def test_old_result_not_allowed_in_new_aggregation(tmp_path,monkeypatch,manifest):
    r=manifest['runs'][0];d=tmp_path/'runs'/r['run_id'];d.mkdir(parents=True)
    row={**r,'experiment_id':'old_experiment','config_hash':manifest['config_hash'],'T_kind':pilot.TIME_KIND,'physical_hash':'physical'}
    pilot.dump(d/'RESULT.json',row)
    manifest['physical_hash']='physical'
    monkeypatch.setattr(analysis,'load_registration',lambda _:manifest)
    with pytest.raises(ValueError,match='OLD_OR_DIFFERENT_RESULT'):analysis.aggregate(tmp_path)
