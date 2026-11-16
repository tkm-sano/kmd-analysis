"""Snapshot Pricing and a full small-day CG with updated duals; no oracle injection."""
import sys,json,time,os
from pathlib import Path
from adapters import *
set_native_threads()
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.generation import seed_plan,enumerate_days
from kmd_toc.vehicle_day.master import solve_lp,reduced_cost as day_rc
from kmd_toc.vehicle_day.runner import run_day_cg
from kmd_toc.vehicle_day.validation import validate_plan
from kmd_toc.column_generation.reduction import contract

def snapshot(backend,seed):
    start=time.perf_counter();p=small_problem(6,1);pool=seed_plan(p);profile=ObjectiveProfile('D');lp=solve_lp(p,pool,profile,'II')
    assert lp['success']
    subset=sorted(p.base.customers,key=lambda i:(-lp['dual']['customer'][i-1],i))[:3]
    domain=contract(p.base,lp['dual']['customer'],[(i,) for i in subset],'pricing',slots=3)
    cfg=AOAConfig(slots=3,p=2,max_evaluations=80,restarts=1,train_shots=1000,final_shots=4096,solver_seed=seed)
    cls=OriginalAOA if backend=='original' else backend_class(backend)
    ts=time.perf_counter();engine=cls(domain.pricing,domain.dual,cfg);result=engine.run();quantum_s=time.perf_counter()-ts
    generated={domain.expand(Route(tuple(r))) for r in result['routes']}
    partners={Route((i,)) for i in p.base.customers}|{Route(t.customers) for c in pool for t in c.trips}|generated
    completed=enumerate_days(p,route_pool=partners,required_routes=generated)
    existing={c.column_id for c in pool};negative=[(day_rc(p,c,lp['dual'],profile),c) for c in completed if c.column_id not in existing and day_rc(p,c,lp['dual'],profile)<-1e-7]
    seedsets={frozenset(t.customers) for c in pool for t in c.trips}
    return {'backend':backend,'seed':seed,'Pricing_s':time.perf_counter()-start,'quantum_Pricing_s':quantum_s,'result':result,
            'generated_routes':[r.customers for r in sorted(generated)],'distinct_routes':len(generated),
            'changed_set_routes':sum(frozenset(r.customers) not in seedsets for r in generated),'negative_columns':len(negative),
            'best_proxy_rc':min((reduced_cost(p.base,r,lp['dual']['customer']) for r in generated),default=None),
            'best_true_RC':min((r for r,c in negative),default=None),'memory':memory(),'two_trip_initial':max(len(c.trips) for c in pool)}

if __name__=='__main__':
    backend,seed,dest=sys.argv[1:];Path(dest).write_text(json.dumps(snapshot(backend,int(seed)),indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v)))
