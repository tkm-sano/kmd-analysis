from dataclasses import asdict, replace
from itertools import permutations
from pathlib import Path
import random

import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.common_initial_v1.plans import create_initial
from kmd_toc.duty_break_v1.models import RestOptions, activate
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.iterative_v3 import search
from kmd_toc.iterative_v3.io import assignment_hash, dump, identity, read, routes, sha
from kmd_toc.iterative_v3.order import OrderProblem, build, cost, expand
from kmd_toc.iterative_v3.physical import evaluate, metrics
from kmd_toc.iterative_v3.quantum import run as kernel
from kmd_toc.iterative_d3.operators import local_target, proposals, select, selected_quantum, transfer_routes, whole_transfer
from kmd_toc.iterative_d3.overlay import variant_worker

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = read(ROOT/'configs/iterative_d3/study.json')['search']
C_CONFIG = read(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')


def fixture(base=None):
    return activate(base or artificial_problem(4,3,1),version='duty-break-20261121-v1',rest_options=RestOptions(True))


def encoded(order, width=2):
    return format(sum(v << (width*i) for i,v in enumerate(order)), 'b')


def test_selector_frequency_aggregation_ties_short_and_invalid():
    problem = OrderProblem('v0',1,('a','b','c'),(),(),'depot','depot',
        dict(first=[0,0,0],last=[0,0,0],edge=[[0,7,3],[4,0,6],[2,1,0]]),
        '',[],1,'','')
    # Two byte encodings of 0,1,2 decode to one permutation. The same-frequency
    # remaining orders sort by distance, and equal distances sort canonically.
    a,b,c,d,e,f = list(permutations(range(3)))
    assert [cost(problem,order) for order in (a,b,c,d,e,f)] == [13,4,7,8,9,5]
    counts = {encoded(a):3, '0'+encoded(a):3, encoded(b):4, encoded(c):4,
              encoded(d):1, encoded(e):1, encoded(f):1, '1111111':2}
    chosen,tally = select(problem,counts,4)
    assert [tuple(x['order']) for x in chosen] == [a,b,f,c]
    assert [x['count'] for x in chosen] == [6,4,1,4]
    assert [x['selection_reason'] for x in chosen] == ['frequency','frequency','distance','distance']
    assert tally['invalid_shots']==2 and tally['distance_evaluations']==6
    assert len(select(problem,{encoded(a):1},4)[0])==1
    assert len(select(problem,counts,1)[0])==1
    same = replace(problem,lookup=dict(first=[0]*3,last=[0]*3,edge=[[0]*3]*3))
    assert [tuple(x['order']) for x in select(same,{encoded(c):4,encoded(b):4},4)[0]] == [b,c]


def test_d2_and_d3_local_policy_uses_actual_parent_and_has_5_plus_5():
    p=fixture()
    rs={('v0',1):('c0001','c0002','c0003'),('v1',1):('c0004',)}
    base=evaluate(p,rs,'D_classical')
    moved,_=whole_transfer(p,base,41,1)
    for variant in ('D2','D3'):
        result=[]
        for i in range(10):
            origin, targets=local_target(build,p,base,[moved],{**SETTINGS,'variant':variant,'local_order_size':2},41,0,i)
            link, assigned, problem=targets[0]
            assert (link is None and assigned==rs) if i%2==0 else link==moved
            expanded=expand(problem,tuple(reversed(range(problem.n))))
            assert assignment_hash(expanded)==assignment_hash(assigned)
            result.append(origin)
        assert result==['current','reallocation']*5
        assert local_target(build,p,base,[],{**SETTINGS,'variant':variant,'local_order_size':2},41,0,1)==('reallocation',[])


def test_transfer_preserves_order_coverage_and_rng_and_three_slots():
    p=fixture()
    rs={('v0',1):('c0001',),('v0',2):('c0002','c0003'),('v1',1):('c0004',)}
    base=evaluate(p,rs,'D_classical')
    changed=transfer_routes(p,rs,'v0','v2')
    assert changed['v2',1]==rs['v0',1] and changed['v2',2]==rs['v0',2]
    assert set(changed)=={('v2',1),('v2',2),('v1',1)}
    finished=evaluate(p,changed,'D_classical')
    assert metrics(p,finished)['D_exact']==metrics(p,base)['D_exact']
    assert {t.vehicle_id:t.ready_s for t in finished.trips if t.trip_no==1}['v2']==p.vehicles[2].first_ready_s
    visited=[]
    rng=random.Random(17);before=rng.getstate()
    def only_record(p,plan,rng,*,families,max_candidates,**unused):
        visited.append((list(families),max_candidates))
        return []
    for i in range(3):
        moves,audit=proposals(only_record,p,base,rng,SETTINGS,41,i,70)
        assert len(moves)==1 and audit['attempts']==1
    assert [f for f,_ in visited]==[['inter_relocate','inter_swap'],['inter_swap','intra_transfer'],['intra_transfer','inter_relocate']]
    assert all(cap==2 for _,cap in visited) and rng.getstate()==before
    all_active=evaluate(p,{('v0',1):('c0001','c0002'),('v1',1):('c0003',),('v2',1):('c0004',)},'D_classical')
    visited.clear()
    moved,audit=proposals(only_record,p,all_active,rng,SETTINGS,41,0,70)
    assert not moved and audit['attempts']==0 and visited==[(['inter_relocate','inter_swap'],2),(['intra_transfer'],1)]


def test_equal_ready_vehicle_names_keep_total_wait(monkeypatch):
    import kmd_toc.common.models as model
    base=artificial_problem(4,3,1)
    monkeypatch.setattr(model,'ready_s',lambda *args:28800)
    p=fixture(replace(base,vehicles=tuple(replace(v,first_ready_s=28800) for v in base.vehicles)))
    rs={('v0',1):('c0001','c0002','c0003'),('v1',1):('c0004',)}
    before=metrics(p,evaluate(p,rs,'D_classical'))
    after=metrics(p,evaluate(p,transfer_routes(p,rs,'v0','v2'),'D_classical'))
    assert before['W_total_min']==after['W_total_min']==30
    assert before['D_exact']==after['D_exact']


@pytest.mark.parametrize('type_', ['distance','waiting'])
def test_single_improvement_is_adopted_and_resumed(type_,tmp_path,monkeypatch):
    from kmd_toc.iterative_d3 import overlay
    p=fixture()
    rs={('v0',1):('c0003','c0002','c0001'),('v1',1):('c0004',)}
    problem=build(p,rs,3,0)
    worst=max(permutations(range(3)),key=lambda o:cost(problem,o))
    rs=expand(problem,worst)
    c=create_initial(p,tmp_path/'initial',experiment_id='TEST_D3',scale='ART',trial_id='J0',
        seed=0,config=C_CONFIG,generator=lambda p,s:schedule(p,rs,'B'))
    initial=c.checked_plan(p)
    seed=next(s for s in range(30) if whole_transfer(p,initial,s,1)[1]['selected']==['v1','v2'])
    settings={**SETTINGS,'variant':'D2' if type_=='distance' else 'D3','local_order_size':3 if type_=='distance' else 4}
    # Isolate the operator whose acceptance we want to prove. Physics, exact
    # comparator, archive, candidate budget and resume are the production code.
    genuine=overlay.proposals
    def restrict(generate,*args):
        return genuine(lambda *a,**k:[],*args)
    monkeypatch.setattr(overlay,'proposals',restrict)
    with variant_worker():
        r=search.run(p,c,tmp_path/'work','D_classical',settings,seed,0,pause_after_iterations=1)
        assert r['status']=='INTERRUPTED_DIAGNOSTIC'
        committed=tmp_path/'work/iteration_0000/COMMIT.json'
        original=sha(committed);first=read(committed)
        measured=first['state_metrics'];initial_metrics=metrics(p,initial)
        assert first['adopted'] and measured['I_dual_percent']==0
        if type_=='distance':
            assert measured['D_km']<initial_metrics['D_km'] and measured['W_total_min']==10
        else:
            assert measured['D_exact']==initial_metrics['D_exact'] and measured['W_total_min']==0
        resumed=search.run(p,c,tmp_path/'work','D_classical',settings,seed,0)
        direct=search.run(p,c,tmp_path/'direct','D_classical',settings,seed,0)
    assert resumed['status']=='COMPLETE' and resumed['counters']['completion_requests']<=70
    assert resumed['metrics']==direct['metrics'] and resumed['counters']==direct['counters']
    second=read(tmp_path/'work/iteration_0001/COMMIT.json')
    assert second['input_hash']==first['adopted_hash']!=identity(initial)
    assert sha(committed)==original


def test_real_qaoa_selector_uses_saved_final_measurements_and_cache(tmp_path):
    p=fixture()
    rs={('v0',1):('c0001','c0002','c0003'),('v1',1):('c0004',)}
    problem=build(p,rs,3,12)
    original=tmp_path/'original'/'local_000'
    folder=original/'solver'
    q=SETTINGS['quantum']
    classical_header=dict(problem=asdict(problem),case_hash=problem.fingerprint,
                          assignment_before=problem.assignment_hash,return_limit=4)
    header=classical_header | {'state_hash':'artificial'}
    raw,_=kernel(problem,q,folder,4)
    dump(original/'CASE.json',classical_header)
    dump(original.parent/'COMMIT.json',{'input_hash':'artificial'})
    old=sha(folder/'FINAL_SAMPLE.json')
    for state in ('artificial','changed'):
        (tmp_path/state).mkdir()
        selected, receipt=selected_quantum(kernel,problem,q,tmp_path/state/'solver',4,
            local_header=header|{'state_hash':state},replay_dir=original)
        if state=='artificial':
            assert receipt['measurement_provenance']['kind']=='replayed_D0_measurements'
            assert receipt['total_shots_actual']==0 and not (tmp_path/state/'solver').exists()
            assert receipt['original_sample_bank_shots']==receipt['training_evaluations']*1000+10000
        else:
            assert receipt['measurement_provenance']['kind']=='variant_QAOA_measurements'
            assert receipt['total_shots_actual']==receipt['training_evaluations']*1000+10000
        assert len(selected)==4 and {x['selection_reason'] for x in selected}=={'frequency','distance'}
        assert all(assignment_hash(expand(problem,item['order']))==problem.assignment_hash for item in selected)
        selected_again, _=selected_quantum(kernel,problem,q,tmp_path/state/'solver',4,
            local_header=header|{'state_hash':state},replay_dir=original)
        assert selected_again==selected and old==sha(folder/'FINAL_SAMPLE.json')
