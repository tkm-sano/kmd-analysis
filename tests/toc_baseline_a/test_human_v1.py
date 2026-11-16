"""Human-choice preservation and honest operational timing; no empirical humans."""
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.human_v1 import complete_manual,manual_groups,timing,VERSION
from kmd_toc.common.models import save_problem

ROOT=Path(__file__).resolve().parents[2]
CLI=ROOT/'scripts/run_a_human_v1.py'


def csv_for(p,groups=None):
    groups=groups if groups is not None else [list(range(1,len(p.stops)+1))]+[[]]*(len(p.vehicles)-1)
    return 'vehicle_id,sequence,stop_id\n'+''.join(
        f'{p.vehicles[v].vehicle_id},{k},{p.od.ids[j]}\n'
        for v,g in enumerate(groups) for k,j in enumerate(g,1))


def test_human_order_is_not_nearest_neighbor_or_boundary_search(monkeypatch):
    import kmd_toc.baseline_a.rule_v1 as rule
    def forbidden(*a,**kw):raise AssertionError('AUTOMATED_HUMAN_CHOICE')
    monkeypatch.setattr(rule,'nearest_order',forbidden)
    monkeypatch.setattr(rule,'generate',forbidden)
    monkeypatch.setattr(rule,'boundary_candidates',forbidden)
    p=artificial_problem(2,1,1)
    d=np.array([[0.,1000.,9000.],[3000.,0.,2000.],[4000.,8000.,0.]])
    t=np.array([[0.,1.2,8.1],[4.1,0.,2.2],[3.2,9.1,0.]])
    od=replace(p.od,distance_m=d,duration_s=t)
    p=replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))
    q,v=complete_manual(p,csv_for(p,[[2,1]]))
    assert v['validated'] and v['common']['D_km']==20
    assert q.trips[0].return_s==32664
    assert [s.stop_id for s in q.trips[0].visits]==['c0002','c0001']
    assert q.method_settings['method_version']==VERSION
    assert q.method_settings['automated_NN'] is False
    assert v['independent']['D_km']=='20.0'


@pytest.mark.parametrize('n,count',[(60,1),(61,2),(120,2)])
def test_capacity_and_reload_preserve_whole_manual_order(n,count):
    p=artificial_problem(n,1,1)
    order=list(range(n,0,-1));q,v=complete_manual(p,csv_for(p,[order]))
    assert v['validated'] and len(q.trips)==count
    assert [s.stop_id for t in q.trips for s in t.visits]==[p.od.ids[j] for j in order]
    if count==2:assert q.trips[1].ready_s==q.trips[0].return_s


def test_121_rejected_without_automatic_reassignment():
    p=artificial_problem(121,2,1)
    with pytest.raises(ValueError,match='CAPACITY_MAX_TRIPS'):manual_groups(p,csv_for(p))


def test_assignment_not_rebalanced_empty_vehicle_no_empty_trip():
    p=artificial_problem(4,3,1);q,v=complete_manual(p,csv_for(p,[[],[4,2,1,3],[]]))
    assert v['validated'] and len(q.trips)==1 and q.trips[0].vehicle_id=='v1'


@pytest.mark.parametrize('kind',['missing','duplicate','unknown_vehicle','unknown_stop','sequence','header'])
def test_invalid_manual_input(kind):
    p=artificial_problem(2,1,1);text=csv_for(p)
    if kind=='missing':text=text.rsplit('\n',2)[0]+'\n'
    if kind=='duplicate':text=text.replace('c0002','c0001')
    if kind=='unknown_vehicle':text=text.replace('v0','v9')
    if kind=='unknown_stop':text=text.replace('c0002','missing')
    if kind=='sequence':text=text.replace('v0,2,','v0,1,')
    if kind=='header':text=text.replace('sequence','order')
    with pytest.raises(ValueError):manual_groups(p,text)


def timeline():
    return [{'phase':p,'at_s':t} for p,t in [('PROGRAM',0),('HUMAN_PLANNING',2),
        ('PROGRAM',62),('HUMAN_PLANNING',65),('PROGRAM',85),('HUMAN_REVIEW',90),
        ('PROGRAM',100),('FINISHED',102)]]


def test_failed_attempt_and_review_included_not_just_last_program_time():
    r=timing(timeline(),validated=True,human_attested=True)
    assert r['T']==r['T_operational']==102
    assert r['T_human']==90 and r['T_program']==12
    assert r['T']==r['T_human']+r['T_program']+r['T_other']
    assert r['J'] is None


@pytest.mark.parametrize('change,reason',[
    ('invalid','INVALID_PLAN'),('unattested','HUMAN_AUTHORSHIP_NOT_ATTESTED'),
    ('no_planning','MISSING_HUMAN_PLANNING_STAGE'),('no_review','MISSING_HUMAN_REVIEW_STAGE'),
    ('synthetic','SYNTHETIC_AUTOMATION_NOT_HUMAN_MEASUREMENT'),('abandoned','ABANDONED')])
def test_unavailable_operational_time_stays_null(change,reason):
    es=timeline()
    if change=='no_planning':
        for e in es:
            if e['phase']=='HUMAN_PLANNING':e['phase']='PAUSED'
    if change=='no_review':es[-3]['phase']='PAUSED'
    if change=='abandoned':es[-1]['phase']='ABANDONED'
    r=timing(es,validated=change!='invalid',human_attested=change!='unattested',synthetic=change=='synthetic')
    assert r['T'] is None and r['T_human'] is None and r['T_reason']==reason
    assert r['T_attempt']==102


def test_pauses_remain_in_elapsed_time():
    es=timeline();es.insert(2,{'phase':'PAUSED','at_s':12})
    r=timing(es,validated=True,human_attested=True)
    assert r['T']==102 and r['T_other']==50 and r['T_human']==40


@pytest.mark.parametrize('bad',['reverse','nonfinite','missing_end','after_end'])
def test_bad_clocks_and_incomplete_timelines(bad):
    es=timeline()
    if bad=='reverse':es[2]['at_s']=1
    if bad=='nonfinite':es[2]['at_s']=float('nan')
    if bad=='missing_end':es.pop()
    if bad=='after_end':es[2]['phase']='FINISHED'
    with pytest.raises(ValueError):timing(es,validated=True,human_attested=True)


def command(*args):
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',
             OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],cwd=ROOT,env=env,
                          capture_output=True,text=True,timeout=45)


def test_actual_cli_fixture_failed_then_corrected_and_final_accept(tmp_path):
    source=tmp_path/'input';p=artificial_problem(4,2,1);save_problem(p,source)
    out=tmp_path/'session'
    r=command('start','--fixture-input',source,'--operator','SCRIPTED_FIXTURE_NOT_A_PERSON',
              '--session-wall-limit-s',120,'--output',out)
    assert r.returncode==0,r.stderr
    r=command('evaluate','--session',out)
    assert r.returncode==1 and json.loads((out/'attempts/0001/result.json').read_text())['validated'] is False
    (out/'assignment.csv').write_text(csv_for(p,[[3,1],[4,2]]))
    r=command('evaluate','--session',out)
    assert r.returncode==0,r.stderr
    r=command('accept','--session',out)
    assert r.returncode==2 and 'ATTESTATION' in r.stderr
    r=command('accept','--session',out,'--attest-human-assignment-and-order')
    assert r.returncode==0,r.stderr
    result=json.loads((out/'RESULT.json').read_text())
    assert result['T'] is None and result['T_reason']=='SYNTHETIC_AUTOMATION_NOT_HUMAN_MEASUREMENT'
    assert result['plan_validated'] and result['T_program']>0
    assert result['T_attempt']>result['T_program']
    assert len(list((out/'attempts').iterdir()))==2
    assert command('evaluate','--session',out).returncode==2
    assert command('start','--fixture-input',source,'--operator','fixture',
                   '--session-wall-limit-s',120,'--output',out).returncode==2


def test_cli_requires_session_limit_and_rejects_changed_plan(tmp_path):
    source=tmp_path/'input';p=artificial_problem(2,1,1);save_problem(p,source)
    out=tmp_path/'session'
    assert command('start','--fixture-input',source,'--operator','fixture','--output',out).returncode==2
    r=command('start','--fixture-input',source,'--operator','fixture',
              '--session-wall-limit-s',120,'--output',out);assert r.returncode==0,r.stderr
    (out/'assignment.csv').write_text(csv_for(p));r=command('evaluate','--session',out);assert r.returncode==0,r.stderr
    (out/'assignment.csv').write_text(csv_for(p,[[2,1]]))
    r=command('accept','--session',out,'--attest-human-assignment-and-order')
    assert r.returncode==1
    result=json.loads((out/'RESULT.json').read_text())
    assert result['T'] is None and result['D'] is None and 'CHANGED' in result['error']


def test_session_limit_does_not_retroactively_accept_plan(tmp_path):
    source=tmp_path/'input';save_problem(artificial_problem(2,1,1),source)
    out=tmp_path/'session'
    r=command('start','--fixture-input',source,'--operator','fixture',
              '--session-wall-limit-s',0.001,'--output',out);assert r.returncode==0,r.stderr
    r=command('evaluate','--session',out);assert r.returncode==1,r.stderr
    value=json.loads((out/'RESULT.json').read_text())
    assert value['T'] is None and value['error']=='SESSION_WALL_LIMIT'
    assert value['T_attempt']>0.001


def test_real_short_program_alarm_in_separate_process():
    code="""
import importlib.util,time
s=importlib.util.spec_from_file_location('human_cli','scripts/run_a_human_v1.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
try:
    m.bounded_setup({'address_space_MiB':4096,'program_wall_limit_s':0.02},m.cpus())
    while True: pass
except TimeoutError as e:
    print(str(e))
"""
    r=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=5)
    assert r.returncode==0 and 'PROGRAM_WALL_LIMIT' in r.stdout
