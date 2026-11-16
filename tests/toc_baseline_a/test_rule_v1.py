"""Hand witnesses, adversarial mutations, and bounded rule state transitions."""
from dataclasses import asdict, replace
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.rule_v1 import (angular_groups,boundary_candidates,compile_group,
    generate,materialize,move,nearest_order,schedule)
from kmd_toc.baseline_a.rule_validation import audit_rule
from kmd_toc.common.validation import validate_plan


def matrices(p,d,t):
    od = replace(p.od,distance_m=d,duration_s=t)
    return replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))


def test_directed_hand_witness_rounding_and_distance():
    p = artificial_problem(2,1,1)
    d = np.array([[0.,1000.,9000.],[3000.,0.,2000.],[4000.,8000.,0.]])
    t = np.array([[0.,1.2,8.1],[4.1,0.,2.2],[3.2,9.1,0.]])
    p = matrices(p,d,t)
    q,diag = generate(p)
    trip = q.trips[0]
    assert [x.stop_id for x in trip.visits]==['c0001','c0002']
    assert trip.distance_m==7000
    assert trip.return_s==30600+1800+2+3+4+240
    assert [v.arrival_s for v in trip.visits]==[32402,32525]
    common,other = validate_plan(p,q),audit_rule(p,q)
    assert common.feasible and other['feasible']
    assert common.D_km==float(other['D_km'])==7
    assert common.W_min==other['W_first']==other['W_reload']==0


@pytest.mark.parametrize('n,trips',[ (60,1),(61,2),(120,2),(121,None)])
def test_capacity_boundary(n,trips):
    p = artificial_problem(n,1,1)
    if trips is None:
        with pytest.raises(ValueError,match='CAPACITY'):
            generate(p)
    else:
        q,_ = generate(p)
        assert len(q.trips)==trips
        assert [len(t.visits) for t in q.trips]==([60]*(n//60)+([n%60] if n%60 else []))
        assert audit_rule(p,q)['feasible']
        if trips==2:
            assert q.trips[1].ready_s==q.trips[0].return_s


def test_empty_vehicle_no_empty_trip():
    p = artificial_problem(2,4,2)
    q,d = generate(p)
    assert sum(len(t.visits) for t in q.trips)==2
    assert all(t.visits for t in q.trips)
    assert sum(x is None for x in d['state']['final_return_s'])==2
    assert sum(x==0 for x in d['state']['L_s'])==2
    assert audit_rule(p,q)['feasible']


@pytest.mark.parametrize('v,b,expected',[(10,2,360),(20,4,720),(40,8,1440)])
def test_first_only_analytic(v,b,expected):
    p = artificial_problem(v,v,b)
    routes = tuple(compile_group(p,(i+1,)) for i in range(v))
    state = schedule(p,routes)
    assert sum(start-ready for _,_,_,ready,start,_,_ in state['bookings'])/60==expected
    q = materialize(p,routes,state,{})
    assert audit_rule(p,q)['W_first']==expected
    assert audit_rule(p,q)['W_reload']==0


def test_ties_and_angle_initialization():
    p = artificial_problem(4,2,2)
    d = np.ones((5,5),dtype='float64');np.fill_diagonal(d,0)
    p = matrices(p,d,d.copy())
    assert nearest_order((4,3,2,1),p)==(1,2,3,4)
    assert angular_groups(p)==((1,2),(4,3))
    tied = replace(p,vehicles=tuple(replace(v,first_ready_s=30000) for v in p.vehicles))
    state = schedule(tied,tuple(compile_group(tied,(i+1,)) for i in range(2)))
    assert [(x[0],x[2]) for x in state['bookings']]==[(0,'b0'),(1,'b1')]


def test_zero_crossing_and_empty_adjacency():
    groups = ((1,2),(),(3,4))
    candidates = list(boundary_candidates(groups))
    assert candidates==[(0,1,2,'clockwise'),(2,1,3,'counterclockwise'),
                        (2,0,4,'clockwise'),(0,2,1,'counterclockwise')]
    moved = move(groups,2,0,4,'clockwise')
    assert moved==((4,1,2),(),(3,))
    assert groups==((1,2),(),(3,4))


def test_cache_matches_full_rebuild_and_candidate_isolation():
    p = artificial_problem(30,3,1)
    a,da = generate(p)
    b,db = generate(p,use_cache=False)
    assert a.trips==b.trips
    assert da['state']==db['state']
    assert da['candidate_trace']==db['candidate_trace']
    assert 0 < da['accepted_moves'] <= len(p.vehicles)
    for candidate in da['candidate_trace']:
        if candidate['status']=='ACCEPTED':
            assert tuple(candidate['after'])<tuple(candidate['before'])
        elif candidate['after'] is not None:
            assert tuple(candidate['after'])>=tuple(candidate['before'])
    # Every accepted move ends its scan; all previous evaluated candidates failed.
    for scan in range(1,da['scans']+1):
        own = [x for x in da['candidate_trace'] if x['scan']==scan]
        if any(x['status']=='ACCEPTED' for x in own):
            assert own[-1]['status']=='ACCEPTED'
    assert audit_rule(p,a)['feasible']


def test_move_updates_order_split_and_global_berths():
    p = artificial_problem(122,2,1)
    groups = (tuple(range(1,62)),tuple(range(62,123)))
    moved = move(groups,0,1,61,'clockwise')
    before_routes = tuple(compile_group(p,g) for g in groups)
    after_routes = tuple(compile_group(p,g) for g in moved)
    assert list(map(len,before_routes))==[2,2]
    assert list(map(len,after_routes))==[1,2]
    assert before_routes[1]!=after_routes[1]
    before,after = schedule(p,before_routes),schedule(p,after_routes)
    assert before['bookings']!=after['bookings']
    assert len(after['bookings'])==3


def test_limits_and_stop_reasons():
    p = artificial_problem(20,3,1)
    q,d = generate(p,max_evaluations=0)
    assert d['stop_reason']=='EVALUATION_LIMIT' and d['accepted_moves']==0
    assert audit_rule(p,q)['feasible']
    _,d = generate(p,deadline=0)
    assert d['stop_reason']=='PLANNING_TIME_LIMIT'
    _,d = generate(artificial_problem(2,1,1))
    assert d['stop_reason']=='NO_IMPROVEMENT'
    found = [generate(artificial_problem(n,3,1))[1] for n in [12,20,30]]
    assert any(x['stop_reason']=='MOVE_LIMIT' and x['accepted_moves']==3 for x in found)


@pytest.mark.parametrize('kind',['duplicate','missing','depot','capacity','trip_count','ready',
    'departure','overlap','negative_wait','arrival','return','hash','empty'])
def test_corruption_rejected(kind):
    p = artificial_problem(120,1,1)
    q,_ = generate(p)
    a,b = q.trips
    if kind=='duplicate':a=replace(a,visits=(*a.visits,a.visits[0]))
    if kind=='missing':a=replace(a,visits=a.visits[1:])
    if kind=='depot':a=replace(a,destination_id='wrong')
    if kind=='capacity':a=replace(a,visits=(*a.visits,b.visits[0]))
    if kind=='trip_count':b=replace(b,trip_no=3)
    if kind=='ready':b=replace(b,ready_s=a.return_s-1,load_start_s=a.return_s-1)
    if kind=='departure':a=replace(a,departure_s=a.load_end_s-1)
    if kind=='overlap':b=replace(b,load_start_s=a.load_start_s,load_end_s=a.load_end_s)
    if kind=='negative_wait':a=replace(a,load_start_s=a.ready_s-1,waiting_s=-1)
    if kind=='arrival':a=replace(a,visits=(replace(a.visits[0],arrival_s=0),*a.visits[1:]))
    if kind=='return':b=replace(b,return_s=72001)
    if kind=='empty':a=replace(a,visits=())
    q=replace(q,trips=(a,b),problem_hash='bad' if kind=='hash' else q.problem_hash)
    assert not validate_plan(p,q).feasible
    # Malformed trip number is rejected by physical oracle before FCFS indexing.
    assert not audit_rule(p,q)['feasible']


def test_unreachable_and_orderer_contract():
    p = artificial_problem(2,1,1)
    reach = p.od.reachable.copy();reach[0,1]=False
    with pytest.raises(ValueError,match='UNREACHABLE'):
        compile_group(replace(p,od=replace(p.od,reachable=reach)),(1,))
    def bad(nodes,p,context=None):return ()
    with pytest.raises(ValueError,match='PERMUTATION'):
        generate(p,orderer=bad)


def test_worker_failure_and_limit_states(tmp_path,monkeypatch):
    script = Path(__file__).resolve().parents[2]/'scripts/run_a_rule_v1.py'
    spec = importlib.util.spec_from_file_location('rule_cli',script)
    cli = importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    import kmd_toc.baseline_a.rule_inputs as inputs
    import kmd_toc.baseline_a.rule_v1 as engine
    cpus = sorted(cli.os.sched_getaffinity(0))[:4]
    monkeypatch.setattr(cli.os,'sched_setaffinity',lambda *_:None)
    monkeypatch.setattr(cli.resource,'setrlimit',lambda *_:None)
    config = tmp_path/'config.json'
    config.write_text(json.dumps({'algorithm':{'distance_tolerance_km':1e-7}}))
    original_generate = engine.generate
    for case in ('valid','hash','limit_feasible','limit_no_feasible','input_bad','timeout','no_feasible'):
        out=tmp_path/case;out.mkdir()
        manifest={'allocated_cpu_ids':cpus,'limits':{'address_space_MiB':4096,'program_wall_s':30,
            'planning_absolute_wall_s':20,'candidate_evaluations':100},'scale':'S1','berths':2,
            'source_hashes':{},'config_hash':'bad' if case=='hash' else cli.digest(config),'T_scope':{}}
        cli.dump(out/'manifest.json',manifest)
        p = artificial_problem(6,2,1)
        if case in ('limit_no_feasible','no_feasible'):
            t=p.od.duration_s.copy();t[t>0]=50000
            p=matrices(p,p.od.distance_m,t)
        def load(*_,p=p):
            if case=='input_bad':raise ValueError('OD_UNREACHABLE')
            if case=='timeout':raise TimeoutError('PROGRAM_WALL_LIMIT')
            return p
        monkeypatch.setattr(inputs,'load_input',load)
        def gen(p,**kwargs):
            if case.startswith('limit_'):kwargs['max_evaluations']=0
            return original_generate(p,**kwargs)
        monkeypatch.setattr(engine,'generate',gen)
        cli.worker(type('Args',(),{'worker':str(out),'config':str(config)})())
        row=json.loads((out/'metrics.json').read_text())
        if case=='valid':assert row['status']=='VALIDATED'
        elif case=='limit_feasible':assert row['status']=='VALIDATED_LIMIT'
        elif case=='limit_no_feasible':assert row['status']=='NO_FEASIBLE_PLAN_LIMIT'
        elif case=='no_feasible':assert row['status']=='NO_FEASIBLE_PLAN'
        elif case=='timeout':assert row['status']=='TIME_LIMIT_NO_VALIDATED_PLAN'
        else:assert row['status']=='INPUT_INVALID'
        assert row['T_attempt']>0
        assert (row['D'] is None)==(row['T_program'] is None)
        if row['T_program'] is not None:
            assert math.isclose(row['T_input']+row['T_planning']+row['T_validation'],row['T_program'],abs_tol=1e-9)
