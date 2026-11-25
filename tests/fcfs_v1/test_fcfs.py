"""FCFS contracts only: no real quantum evaluations or S1-S3 optimization."""
from dataclasses import replace
import itertools
import json
from pathlib import Path

import pytest

from kmd_toc.fcfs_v1.scheduler import schedule_jobs,schedule,reschedule
from kmd_toc.fcfs_v1.validation import validate_fcfs,require_fcfs
from kmd_toc.fcfs_v1.evaluation import evaluate
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.pipeline.completion import assemble
from kmd_toc.common.config import ROOT,read_json
from kmd_toc.termination_v1.work import Ledger,key


def jobs(ready,durations,berths=1):
    return schedule_jobs(ready,durations,{f'b{i}':(0,20000) for i in range(berths)})


def test_one_berth_ready_order_and_busy_queue():
    rows=jobs({'v0':0,'v1':100,'v2':50},{('v0',1):0,('v1',1):0,('v2',1):0})
    assert [(r['vehicle_id'],r['load_start_s']) for r in rows]==[('v0',0),('v2',1800),('v1',3600)]


def test_simultaneous_berths_ready_ties_and_string_ids():
    rows=jobs({'v2':0,'v10':0,'v1':0},{('v2',1):0,('v10',1):0,('v1',1):0},2)
    assert [(r['vehicle_id'],r['load_start_s'],r['berth_id']) for r in rows]==[
        ('v1',0,'b0'),('v10',0,'b1'),('v2',1800,'b0')]


def test_lowest_id_among_all_idle_berths_not_longest_idle():
    rows=jobs({'v0':0,'v1':0,'v2':100,'v3':5000},
              {(f'v{i}',1):0 for i in range(4)},2)
    assert rows[-1]['load_start_s']==5000
    assert rows[-1]['berth_id']=='b0' # b1 has been idle since 1800, b0 since 3600.


def test_second_trip_arrives_at_return_and_joins_common_queue():
    rows=jobs({'v0':0,'v1':300},{('v0',1):600,('v0',2):100,('v1',1):600})
    first,other,second=rows
    assert (first['return_s'],other['load_start_s'])==(2400,1800)
    assert second['ready_s']==2400 and second['load_start_s']==3600
    assert sum(r['load_start_s']-r['ready_s'] for r in rows)==2700


def test_second_trip_ready_tie_uses_vehicle_id():
    rows=jobs({'v0':0,'v1':1800},{('v0',1):0,('v0',2):0,('v1',1):0})
    assert [(r['vehicle_id'],r['trip_no']) for r in rows]==[('v0',1),('v0',2),('v1',1)]


def test_idle_berth_starts_immediately_and_loading_is_not_preempted():
    rows=jobs({'v0':500,'v1':501},{('v0',1):1,('v1',1):1})
    assert rows[0]['load_start_s']==500
    assert rows[1]['load_start_s']==2300
    assert all(r['load_end_s']-r['load_start_s']==1800 for r in rows)


def test_second_trip_requires_first_and_empty_active_routes_rejected():
    with pytest.raises(ValueError,match='WITHOUT_FIRST'):jobs({'v0':0},{('v0',2):0})
    p=artificial_problem(1,1,1)
    with pytest.raises(ValueError,match='EMPTY_ACTIVE_TRIP'):schedule(p,{('v0',1):()},'B')


def test_non_fcfs_input_is_rejected_and_conversion_is_explicit():
    p=artificial_problem(2,1,1);ready=p.vehicles[0].first_ready_s
    old=assemble(p,[{'v':0,'trip_no':1,'route':(1,2),'start_s':ready+600}],'C',{})
    assert not validate_fcfs(p,old)['feasible']
    with pytest.raises(ValueError,match='FCFS_V1_REJECTION'):evaluate(p,old)
    fixed=reschedule(p,old)
    assert fixed.trips[0].load_start_s==ready and old.trips[0].load_start_s==ready+600
    assert evaluate(p,fixed)['W_min']==0
    assert fixed.trips[0].distance_m==old.trips[0].distance_m


def test_same_routes_return_same_schedule_and_W_for_B_C_Q_D():
    p=artificial_problem(4,2,1)
    routes={('v0',1):('c0001','c0002'),('v0',2):('c0003',),('v1',1):('c0004',)}
    plans=[schedule(p,routes,m) for m in ('B','C','Q','D')]
    assert all(x.trips==plans[0].trips for x in plans)
    assert len({evaluate(p,x)['W_min'] for x in plans})==1
    assert all(evaluate(p,x)['D_km']==evaluate(p,plans[0])['D_km'] for x in plans)


def test_fcfs_reconstruction_can_violate_shift_and_must_reject():
    p=artificial_problem(1,1,1)
    from kmd_toc.common.od import OD
    d=p.od.duration_s.copy();d[0,1]=d[1,0]=25000
    od=OD(p.od.ids,p.od.distance_m,d,p.od.reachable,p.od.metadata)
    changed=replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))
    with pytest.raises(ValueError,match='RETURN_DEADLINE'):schedule(changed,{('v0',1):('c0001',)},'B')


def test_wrong_berth_id_and_overtaking_are_detected():
    p=artificial_problem(3,3,2)
    plan=schedule(p,{('v0',1):('c0001',),('v1',1):('c0002',),('v2',1):('c0003',)},'B')
    t=plan.trips[-1]
    bad=replace(plan,trips=(*plan.trips[:-1],replace(t,berth_id='b1' if t.berth_id=='b0' else 'b0')))
    assert not validate_fcfs(p,bad)['feasible']


def test_cp_candidates_have_fcfs_W_inside_objective():
    from kmd_toc.fcfs_v1.cp import solve_completion
    p=artificial_problem(3,2,1)
    cfg=read_json(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    plan=solve_completion(p,[(1,2),(3,)],'C',cfg,Ledger(),13)
    check=require_fcfs(p,plan)
    assert plan.method_settings['CP_wait_s']==round(check['W_loading_min']*60)
    # Independently enumerate the small route-to-slot assignment space.
    candidates=[];routes=[('c0001','c0002'),('c0003',)]
    for keys in itertools.permutations([('v0',1),('v0',2),('v1',1),('v1',2)],2):
        try:candidates.append(schedule(p,dict(zip(keys,routes)),'C'))
        except ValueError:pass
    assert key(plan)==min(map(key,candidates))


@pytest.mark.parametrize('method',['B','C'])
def test_current_generation_uses_fcfs_before_selection(method):
    from kmd_toc.cargo_wait_v2.methods import generate
    p=artificial_problem(4,2,1)
    cfg=read_json(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    before=json.dumps(cfg,sort_keys=True)
    ledger=Ledger();plan,report=generate(p,method,cfg,ledger,{'solver_seed':13,'quantum_seed':17})
    assert plan.method_settings['operating_policy']=='FCFS_v1'
    assert require_fcfs(p,plan)['feasible']
    assert report['loading_W_min']==sum(t.waiting_s for t in plan.trips)/60
    assert json.dumps(cfg,sort_keys=True)==before
    assert any(e['event']=='CP_FCFS_start' for e in ledger.events)


def test_new_local_Q_uses_shared_completion_and_preserves_decision():
    from kmd_toc.d_local_design.completion import extract,preserves
    from kmd_toc.d_local_design.model import Decision
    from kmd_toc.fcfs_v1.local import complete
    p=artificial_problem(4,2,1)
    plan=schedule(p,{('v0',1):('c0001','c0002'),('v1',1):('c0003','c0004')},'D')
    local=extract(p,plan,(('v0',1),('v1',1)),('c0001','c0003'))
    decision=Decision(('c0003',),('c0001',))
    proposed=complete(p,plan,local,decision)
    assert preserves(proposed,local,decision,plan)
    assert require_fcfs(p,proposed)['feasible']


@pytest.mark.parametrize('alias',['D','Q'])
def test_no_legacy_W_integer_master_is_called_in_current_D(monkeypatch,alias):
    """An engine double tests wiring only; no real quantum circuit is executed."""
    import kmd_toc.termination_v1.quantum as quantum
    import kmd_toc.termination_v1.master as master
    from kmd_toc.cargo_wait_v2.methods import generate
    from kmd_toc.cargo_wait_v2.validation_fixture import quantum_connection_witness
    class Engine:
        def __init__(self,*args):self.q=12;self.assignments=(0,)*64
        def run(self):return {'routes':[(1,3,2)],'history':[{'nfev':1}],'measured_shots':10000}
    def forbidden(*args,**kwargs):raise AssertionError('legacy calendar W IP must never run')
    monkeypatch.setattr(quantum,'FinitePricingAOA',Engine)
    monkeypatch.setattr(master.FiniteMaster,'ip',forbidden)
    p=quantum_connection_witness();cfg=read_json(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    ledger=Ledger();plan,report=generate(p,alias,cfg,ledger,{'solver_seed':13,'quantum_seed':17})
    assert require_fcfs(p,plan)['feasible']
    assert not ledger.counts.get('quantum_calls_failed',0)
    assert report['loading_W_min']==sum(t.waiting_s for t in plan.trips)/60
    assert plan.method_settings['new_pricing_routes_in_final']>0
    assert plan.method_settings['reported_method']==alias


def test_saved_S1_C_overtaking_regression_without_optimization():
    from kmd_toc.common.models import load_problem,load_plan
    import hashlib
    source=ROOT/'output/toc_delivery/non_time_variance_pilot_20261117_v1/runs/S1_C_pilot_r01/plan.json'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    p=load_problem(ROOT/'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1')
    plan=load_plan(source);old={(t.vehicle_id,t.trip_no):t for t in plan.trips}
    assert (old['v3',2].ready_s,old['v3',2].load_start_s)==(44036,44978)
    assert (old['v2',2].ready_s,old['v2',2].load_start_s)==(44543,44875)
    assert not validate_fcfs(p,plan)['feasible']
    new=reschedule(p,plan);fixed={(t.vehicle_id,t.trip_no):t for t in new.trips}
    assert require_fcfs(p,new)['feasible']
    assert fixed['v3',2].load_start_s==44875
    assert fixed['v2',2].load_start_s==44978
    assert fixed['v3',2].return_s==57479 and fixed['v2',2].return_s==57584
    assert sum(t.distance_m for t in new.trips)==sum(t.distance_m for t in plan.trips)
    assert {k:tuple(v.stop_id for v in t.visits) for k,t in old.items()}=={
        (t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in new.trips}
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before


def test_synthetic_release_order_and_no_idle_against_independent_event_oracle():
    import heapq
    import random
    rng=random.Random(20261120)
    for _ in range(30):
        vehicles=['v0','v1','v10','v2'];ready={v:rng.randrange(6000) for v in vehicles}
        duration={(v,k):rng.randrange(2000) for v in vehicles for k in (1,2)}
        count=rng.choice((1,2,3));actual=jobs(ready,duration,count)
        # Different event-based reference from the release-order production loop.
        events=[(r,1,v,1) for v,r in ready.items()]+[(0,0,f'b{i}',0) for i in range(count)]
        heapq.heapify(events);idle=set();queue=[];expected=[]
        while events:
            now=events[0][0]
            while events and events[0][0]==now:
                t,kind,identifier,k=heapq.heappop(events)
                if kind==0:idle.add(identifier)
                else:heapq.heappush(queue,(t,identifier,k))
            while idle and queue:
                r,v,k=heapq.heappop(queue);b=min(idle);idle.remove(b)
                ret=now+1800+duration[v,k]
                expected.append((v,k,r,b,now,ret))
                heapq.heappush(events,(now+1800,0,b,0))
                if k==1:heapq.heappush(events,(ret,1,v,2))
        assert [(x['vehicle_id'],x['trip_no'],x['ready_s'],x['berth_id'],x['load_start_s'],x['return_s'])
                for x in actual]==expected


def test_evaluation_refuses_mixing_old_and_FCFS_v1_results(monkeypatch,tmp_path):
    import importlib.util
    import kmd_toc.common.models as models
    p=artificial_problem(1,1,1)
    current=schedule(p,{('v0',1):('c0001',)},'B')
    old=replace(current,method_id='C',method_settings={})
    a=tmp_path/'current.json';b=tmp_path/'old.json'
    a.write_text('current');b.write_text('old')
    monkeypatch.setattr(models,'load_problem',lambda _:p)
    monkeypatch.setattr(models,'load_plan',lambda path:{a:current,b:old}[Path(path)])
    s=importlib.util.spec_from_file_location('fcfs_evaluation_cli',ROOT/'scripts/evaluate_fcfs_v1.py')
    module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
    out=tmp_path/'out'
    with pytest.raises(ValueError,match='MIXED_HISTORICAL_AND_FCFS'):
        module.main(['--input',str(tmp_path/'input'),'--plan',str(a),'--plan',str(b),'--output',str(out)])
    assert not out.exists()


def test_CP_model_inconsistency_cannot_be_hidden_by_valid_incumbent(monkeypatch):
    import kmd_toc.fcfs_v1.cp as cp
    p=artificial_problem(1,1,1)
    incumbent=schedule(p,{('v0',1):('c0001',)},'B')
    def inconsistent(*args,**kwargs):
        raise cp.FCFSModelConsistencyError('FCFS_CP_MODEL_SCHEDULER_DISAGREE')
    monkeypatch.setattr(cp,'solve_completion',inconsistent)
    cfg=read_json(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    with pytest.raises(cp.FCFSModelConsistencyError):
        cp.complete(p,[(1,)],'B',cfg,Ledger(),13,incumbent=incumbent)
