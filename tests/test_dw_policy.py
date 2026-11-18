"""Artificial fixtures for the D/W migration; no routing or circuit execution."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from kmd_toc.dw import (analyze_rows, difference, digest, fingerprint, load_policy,
                        load_saved_pilot, write_analysis)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT/'configs/toc_delivery/dw_policy_20261117_v1.json'


def rows():
    result = []
    for method, d, w in [('A',20,10), ('B',15,12), ('C',14,11), ('D',14,10),
                          ('D_CLASSICAL_REPLACEMENT',14,10.5)]:
        for repeat in (1,2,3):
            result.append({'run_id': f'{method}_{repeat}', 'case_id': 'S1', 'method': method,
                'repeat_id': repeat, 'adoptable': True, 'input_state': 'VALID',
                'execution_state': 'NORMAL', 'validation_state': 'VALIDATED', 'plan_state': 'VALID',
                'input_hash': 'input', 'OD_hash': 'od', 'physical_hash': 'physical', 'config_hash': 'config',
                'D': d, 'W': w if method == 'A' else w+repeat/10,
                'T_program': 999, 'J': -123})
    return result


def test_time_and_old_score_cannot_change_any_result():
    data = rows()
    expected = analyze_rows(data)
    for i,row in enumerate(data):
        row.update(T_program=float('nan') if i % 2 else None, T_attempt=-1,
                   J=1e99, T_kind='different', target_arrival_s=0, cpu_s=0)
    assert analyze_rows(data) == expected
    assert all(set(row).isdisjoint({'T_program','T_attempt','J','T_kind'}) for row in expected['rows'])


def test_dominance_does_not_use_time_and_keeps_ties():
    data = rows()
    # Exact same quality among D/its replacement: both remain nondominated.
    for row in data:
        if row['method'] == 'D_CLASSICAL_REPLACEMENT':
            row['W'] = 10+row['repeat_id']/10
    front = analyze_rows(data)['observed_fronts'][0]
    assert 'D_1' in front['observed_nondominated_run_ids']
    assert 'D_CLASSICAL_REPLACEMENT_1' in front['observed_nondominated_run_ids']


def test_zero_variance_does_not_create_zero_width_interval():
    result = difference([1,1,1], [1,1,1])
    assert result['mean_difference'] == 0
    assert result['CI95'] is None
    assert 'ZERO_OBSERVED' in result['null_reason']


def test_fixed_a_is_one_quality_reference():
    result = analyze_rows(rows())
    a = next(r for r in result['summaries'] if r['scale']=='S1' and r['method']=='A')
    assert a['quality_units'] == 1 and a['D']['n_recorded'] == 3
    comparison = next(r for r in result['comparisons'] if r['scale']=='S1' and r['left']=='A' and r['right']=='D')
    assert comparison['W']['left_quality_units'] == 1
    assert comparison['W']['CI95'] is not None
    assert comparison['paired_seed_analysis'] is False


def test_a_quality_disagreement_fails_closed():
    data = rows()
    data[0]['W'] += 1
    with pytest.raises(ValueError, match='A_REFERENCE_QUALITY'):
        analyze_rows(data)


def test_failure_counts_remain_in_denominator():
    data = rows()
    row = next(r for r in data if r['method']=='D')
    row.update(adoptable=False, execution_state='ERROR', D=None, W=None)
    summary = next(r for r in analyze_rows(data)['summaries'] if r['method']=='D' and r['scale']=='S1')
    assert summary['D']['n_recorded'] == 2
    assert summary['validated_plan_rate']['estimate'] == 2/3
    assert summary['validated_plan_rate']['denominator'] == 3


def test_pending_trial_prevents_final_rate_interval():
    data = rows()
    data[0].update(adoptable=False, execution_state='INCOMPLETE', D=None, W=None)
    summary = analyze_rows(data)['summaries'][0]
    assert summary['validated_plan_rate']['Wilson95'] is None
    assert summary['validated_plan_rate']['reason'] == 'UNRESOLVED_STARTED_TRIALS'


@pytest.mark.parametrize('change,match', [
    (lambda d: d.append(deepcopy(d[0])), 'DUPLICATE'),
    (lambda d: d[0].update(input_hash='different'), 'CONDITION_MISMATCH'),
    (lambda d: d[0].update(D=None), 'UNVALIDATED'),
    (lambda d: d[0].update(adoptable=False), 'REJECTED'),
])
def test_invalid_records_are_rejected(change,match):
    data = rows(); change(data)
    with pytest.raises(ValueError, match=match):
        analyze_rows(data)


@pytest.mark.parametrize('change', [
    lambda p: p['objectives'].update(T='seconds'),
    lambda p: p['composite'].update(weights=[.5,.5]),
    lambda p: p['main'].update(executable=True),
    lambda p: p['analysis'].update(dominance_dimensions=3),
    lambda p: p.update(rq='old RQ'),
])
def test_policy_drift_is_rejected(tmp_path,change):
    policy = load_policy(POLICY); change(policy)
    path = tmp_path/'policy.json'; path.write_text(json.dumps(policy))
    with pytest.raises(ValueError):
        load_policy(path)


def saved_fixture(tmp_path):
    root = tmp_path/'source'; root.mkdir()
    snapshot = root/'SOURCE_SNAPSHOT.tar.gz'; snapshot.write_bytes(b'artificial snapshot')
    inputs = tmp_path/'input'; inputs.mkdir()
    source = inputs/'input.json'; source.write_text('{}')
    run = {'run_id':'A_1','case_id':'S1','method':'A','repeat_id':1,'attempt_id':1,'seeds':None}
    policy = load_policy(POLICY)
    manifest = {'experiment_id':policy['source']['experiment_id'], 'contract_id':'fixture',
        'runs':[run], 'run_list_hash':fingerprint([run]), 'snapshot_sha256':digest(snapshot),
        'cases':[{'case_id':'S1','input':{'directory':str(inputs),'input_hash':'input','OD_hash':'od',
                                       'files':{'input.json':digest(source)}}}],
        'physical_hash':'physical','config_hash':'config'}
    for name in ('REGISTERED.json','PILOT_MANIFEST.json'):
        (root/name).write_text(json.dumps(manifest))
    lock = {name:digest(root/name) for name in ('REGISTERED.json','PILOT_MANIFEST.json')}
    lock.update(manifest_fingerprint=fingerprint(manifest),run_list_hash=manifest['run_list_hash'])
    (root/'REGISTRATION_LOCK.json').write_text(json.dumps(lock))
    return root,inputs,policy


def test_saved_registration_not_started_and_unfinished_are_distinct(tmp_path):
    root,_,policy = saved_fixture(tmp_path)
    assert load_saved_pilot(root,policy)[0][0]['execution_state'] == 'NOT_STARTED'
    (root/'runs/A_1').mkdir(parents=True)
    assert load_saved_pilot(root,policy)[0][0]['execution_state'] == 'INCOMPLETE'
    assert analyze_rows(load_saved_pilot(root,policy)[0])['summaries'][0]['validated_plan_rate']['reason'] == 'UNRESOLVED_STARTED_TRIALS'


def save_accepted(root):
    manifest = json.loads((root/'REGISTERED.json').read_text())
    run = manifest['runs'][0]
    directory = root/'runs'/run['run_id']; directory.mkdir(parents=True)
    plan = directory/'plan.json'
    plan.write_text(json.dumps({'problem_hash':'input','od_hash':'od'}))
    row = {**run, 'experiment_id':manifest['experiment_id'], 'contract_id':'fixture',
           'input_hash':'input','OD_hash':'od','physical_hash':'physical','config_hash':'config',
           'adoptable':True,'execution_state':'NORMAL','input_state':'VALID',
           'validation_state':'VALIDATED','plan_state':'VALID','D':20,'W':10,
           'selected_branch_id':0,'plan_sha256':digest(plan)}
    (directory/'RESULT.json').write_text(json.dumps(row))
    checks = {'common_physical':{'feasible':True,'D_km':20,'W_min':10},
              'independent_physical':{'feasible':True,'D_km':'20','W_min':'10'}}
    (directory/'PHYSICAL_CHECKS.json').write_text(json.dumps([
        {'branch_id':0,'checks':checks}, {'selected_repeat_check':0,'checks':checks}]))
    return directory


def test_saved_parent_final_checks_and_complete_write(tmp_path):
    root,_,policy = saved_fixture(tmp_path); save_accepted(root)
    result = write_analysis(root,tmp_path/'analysis',POLICY)
    assert result['rows'][0]['D'] == 20
    assert json.loads((tmp_path/'analysis/DW_ANALYSIS.json').read_text()) == result


@pytest.mark.parametrize('target,match', [
    ('plan.json','SAVED_PLAN_CHANGED'), ('PHYSICAL_CHECKS.json','DOUBLE_CHECKS_MISMATCH'),
    ('RESULT.json','RESULT_IDENTITY_CHANGED')])
def test_accepted_plan_identity_and_double_checks_are_checked(tmp_path,target,match):
    root,_,policy = saved_fixture(tmp_path); directory = save_accepted(root)
    path = directory/target
    data = json.loads(path.read_text())
    if target == 'plan.json': data['problem_hash']='forged'
    elif target == 'RESULT.json': data['method']='D'
    else: data[-1]['checks']['independent_physical']['W_min']='999'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match=match):
        load_saved_pilot(root,policy)


@pytest.mark.parametrize('target,match', [
    ('REGISTERED.json','REGISTRATION_CHANGED'),
    ('SOURCE_SNAPSHOT.tar.gz','SNAPSHOT_CHANGED'),
    ('input','FROZEN_INPUT_CHANGED'),
])
def test_saved_provenance_tampering_is_rejected(tmp_path,target,match):
    root,inputs,policy = saved_fixture(tmp_path)
    path = inputs/'input.json' if target=='input' else root/target
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match=match):
        load_saved_pilot(root,policy)


def test_existing_and_source_outputs_are_preserved(tmp_path):
    root,_,_ = saved_fixture(tmp_path)
    with pytest.raises(ValueError, match='SEPARATE'):
        write_analysis(root,root/'analysis',POLICY)
    out = tmp_path/'out'; out.mkdir()
    with pytest.raises(FileExistsError, match='PRESERVED'):
        write_analysis(root,out,POLICY)
    assert list(out.iterdir()) == []


@pytest.mark.parametrize('name', ['run_dwt.py','run_dwt_bundle.py','run_comparison_v1.py',
    'run_comparison_design.py','run_comparison_design_supplement.py','run_termination_rules.py',
    'run_human_comparison_v1.py','render_dwt.py','finalize_dwt.py'])
def test_old_entrypoints_require_explicit_history_before_work(name):
    result = subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/name)],
                            capture_output=True,text=True,check=False)
    assert result.returncode != 0 and 'HISTORICAL_ENTRYPOINT' in result.stderr


def test_current_import_does_not_initialize_solvers():
    result = subprocess.run([sys.executable,'-B','-c',
        "import kmd_toc.dw,sys; assert not any(n.startswith(('ortools','qiskit')) for n in sys.modules)"],
        capture_output=True,text=True,check=False)
    assert result.returncode == 0, result.stderr
