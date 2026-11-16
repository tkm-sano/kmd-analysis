"""Meaningful adapter/regression witnesses, including capacity/2-trip/berth binding."""
import json
from pathlib import Path
import pytest
from adapters import *
from backend_bench import instance
set_native_threads()

@pytest.mark.parametrize('backend',['qiskit','qulacs','quri'])
def test_original_run_parity(backend):
    cfg=AOAConfig(slots=3,p=2,max_evaluations=40,restarts=1,solver_seed=1101)
    e=OriginalAOA(instance(4),[.6,.9,1.2],cfg);b=backend_class(backend)(e.instance,e.dual[1:],cfg)
    x=e.run();y=b.run()
    assert x['routes']==y['routes']
    assert x['history']==y['history']
    assert x['feasible_rate']==y['feasible_rate']


def test_global_phase_and_distribution():
    e=OriginalAOA(instance(4),[.6,.9,1.2],AOAConfig(slots=3,p=2))
    reference=Statevector.from_instruction(e.circuit([.17,.41,.23,.31])).data
    for b in ['qulacs','quri']:
        v,*_=simulate(build(e,[.17,.41,.23,.31],b),e.q,b)
        x=compare_states(reference,v*np.exp(.79j))
        assert x['phase_aligned_max_abs']<1e-10 and x['probability_L1']<1e-10


def independent_day_check(p,columns):
    # Recompute solely from requested routes/starts, ignoring reported end/cost.
    cover=[];events=[];distance=waiting=0.;seenvehicles=set()
    for c in columns:
        assert c.vehicle_id not in seenvehicles;seenvehicles.add(c.vehicle_id)
        v=p.vehicle(c.vehicle_id);assert len(c.trips)<=2;ready=v.ready_s;seen=set()
        for number,t in enumerate(c.trips,1):
            r=t.customers;assert r and len(r)==len(set(r)) and not set(r)&seen
            assert set(r)<=set(p.base.customers) and sum(p.base.demand[i] for i in r)<=v.capacity
            assert t.trip_id==number and t.load_start_s>=ready and t.load_start_s%p.delta_s==0
            nodes=(0,*r,0);end=t.load_start_s+v.loading_s+sum(p.travel_s[i][j] for i,j in zip(nodes,nodes[1:]))+sum(p.service_s[i] for i in r)
            assert end<=v.shift_end_s and end==t.return_s
            waiting+=t.load_start_s-ready;distance+=sum(p.base.distance[i,j] for i,j in zip(nodes,nodes[1:]))
            events.extend([(t.load_start_s,1),(t.load_start_s+v.loading_s,-1)])
            ready=end+v.preparation_s;cover.extend(r);seen.update(r)
    assert sorted(cover)==list(p.base.customers)
    active=0
    for _,delta in sorted(events):active+=delta;assert 0<=active<=p.berths
    return {'D_km':float(distance),'W_min':float(waiting/60)}

@pytest.mark.parametrize('backend',['qiskit','qulacs','quri','qamomile_quri'])
def test_binding_day_CG(backend):
    from kmd_toc.vehicle_day.fixtures import small_problem
    from kmd_toc.vehicle_day.generation import seed_plan
    from kmd_toc.vehicle_day.model import ObjectiveProfile
    from kmd_toc.vehicle_day.master import solve_lp,solve_integer
    from kmd_toc.vehicle_day.validation import validate_plan
    import kmd_toc.vehicle_day.pricing as pricing
    p=small_problem(6,1);pool=seed_plan(p);profile=ObjectiveProfile('D')
    assert max(len(c.trips) for c in pool)==2
    assert validate_plan(p,pool)['peak_berths']==1
    old=pricing.PricingAOA;pricing.PricingAOA=backend_class(backend);trace=[]
    try:
        for k in range(4):
            before=solve_lp(p,pool,profile,'II');assert before['success']
            ranked,log=pricing.aoa_day_candidates(p,pool,before,profile,AOAConfig(slots=3,p=2,max_evaluations=40,restarts=1,solver_seed=1101),k)
            existing={c.column_id for c in pool};new=[(rc,c) for rc,c in ranked if rc<-1e-7 and c.column_id not in existing][:20]
            pool.extend(c for rc,c in new);after=solve_lp(p,pool,profile,'II');assert after['success']
            assert after['objective']<=before['objective']+1e-7
            trace.append({'round':k,'before':before['dual'],'after':after['dual'],'added':len(new)})
            if not new:break
        ip=solve_integer(p,pool,profile);assert ip['success'];a=validate_plan(p,ip['selected']);b=independent_day_check(p,ip['selected'])
        assert a['valid'] and np.isclose(a['D_km'],b['D_km']) and np.isclose(a['W_min'],b['W_min'])
        assert not validate_plan(p,ip['selected'][:1])['valid'] # missing global coverage
        assert len(trace)>1 and any(t['added'] for t in trace)
        (ROOT/'evidence'/f'binding_contract_{backend}.json').write_text(json.dumps({'trace':trace,'final':a,'independent':b},indent=2))
    finally:pricing.PricingAOA=old
