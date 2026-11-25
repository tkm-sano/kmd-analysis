"""Shared local selection/completion, including a genuinely unused trip slot.

The oracle view may contain an empty route descriptor; it is never a physical
plan or an accepted initial plan. This permits tiny CW single-route inputs to
exercise QAOA without replacing B by an artificial multi-route initial plan.
"""
from dataclasses import asdict
from types import SimpleNamespace
from pathlib import Path
from copy import deepcopy
import time,json,resource
import numpy as np
from kmd_toc.objective_alignment_v1.generators import Case,case_digest,digest,proposal,Classical
from kmd_toc.nkr_p2_study.model import pick
from kmd_toc.d_local_design.model import LocalProblem
from kmd_toc.main_experiment_d.quantum import backend_modules
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.common_initial_v1.plans import dump

def oracle_view(case):
    """Only route endpoints/orders are consumed by the unchanged cost kernel."""
    return SimpleNamespace(trips=tuple(SimpleNamespace(vehicle_id=r['trip_id'][0],trip_no=r['trip_id'][1],
        visits=tuple(SimpleNamespace(stop_id=s) for s in r['original_customers'])) for r in case.local.outside_routes))

def prepare(p,plan,n,seed,seen=()):
    if type(n) is not int or n<2 or type(seed) is not int or seed<0:raise ValueError('EXPLICIT_LOCAL_SIZE_AND_SEED')
    local=pick(p,plan,set(seen),n,seed)
    if local is None:
        routes={(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
        # No reassignment of the initial plan: choose an available unused slot
        # in the local decision space, not a fabricated active initial trip.
        active=sorted((k,r) for k,r in routes.items() if len(r)>=n)
        empty=sorted((v.vehicle_id,k) for v in p.vehicles for k in (1,2) if (v.vehicle_id,k) not in routes)
        eligible=[(sum(s not in seen for s in r),key,r,target) for key,r in active for target in empty
                  if target[1]==1 or (target[0],1) in routes]
        if not eligible:return None
        _,key,route,target=min(eligible,key=lambda x:(-x[0],x[1],x[3]))
        at=(len(route)-n)//2;ids=route[at:at+n];routes[target]=()
        outside=tuple(dict(trip_id=k,customers=tuple(s for s in r if s not in ids),original_customers=r,
            constraints='fixed physical slot; nonselected order fixed; empty descriptor is not an active trip') for k,r in sorted(routes.items()))
        idx=[0,*(p.od.ids.index(s) for s in ids)];demand={s.stop_id:s.demand for s in p.stops}
        local=LocalProblem(f'{plan.plan_id}:active_empty:{seed}',(key,target),ids,tuple(demand[s] for s in ids),
            tuple(map(tuple,p.od.distance_m[np.ix_(idx,idx)].tolist())),
            tuple(map(tuple,p.od.duration_s[np.ix_(idx,idx)].tolist())),
            dict(plan_id=plan.plan_id,problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
                 selector='v2 active-active, or active-unused-slot if no eligible active pair'),outside,seed).validate()
    q,_=backend_modules();physical=digest_payload(physical_payload(plan))
    temporary=Case(local,{},physical,p.fingerprint,p.od.fingerprint,'')
    lookup=q.boundary_lookups(p,oracle_view(temporary),local)
    case=Case(local,lookup,physical,p.fingerprint,p.od.fingerprint,'')
    return Case(local,lookup,physical,p.fingerprint,p.od.fingerprint,case_digest(case))

def complete(p,original,case,item,condition):
    if case.case_hash!=case_digest(case) or case.problem_hash!=p.fingerprint or case.od_hash!=p.od.fingerprint:
        raise ValueError('LOCAL_CASE_INPUT_OR_CONTENT_CHANGED')
    if case.physical_initial_hash!=digest_payload(physical_payload(original)):raise ValueError('STALE_LOCAL_ANCHOR')
    decision=item['decision'];decision.validate(case.local.customer_ids)
    chosen=dict(zip(case.local.trip_ids,(decision.trip_1,decision.trip_2)));selected=set(case.local.customer_ids)
    original_routes={(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in original.trips}
    routes=dict(original_routes)
    for key,block in chosen.items():
        r=original_routes.get(key,());at=next((i for i,s in enumerate(r) if s in selected),len(r))
        routes[key]=tuple(s for s in r[:at] if s not in selected)+block+tuple(s for s in r[at:] if s not in selected)
    routes={k:r for k,r in routes.items() if r}
    method='D' if condition=='D_quantum' else 'C'
    plan=schedule(p,routes,method,dict(condition_id=condition,case_hash=case.case_hash,
        generator_source=item['source'],completion='v2 exact supplied order/slot + common duty FCFS'))
    actual={(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
    if actual!=routes:raise ValueError('PHYSICAL_COMPLETION_CHANGED_GENERATED_ASSIGNMENT_OR_ORDER')
    require_valid(p,plan);return plan

class Quantum:
    condition_id='D_quantum'
    def __init__(self,protocol,*,diagnostic=False):self.protocol=deepcopy(protocol);self.diagnostic=diagnostic
    def generate(self,p,plan,case,output):
        from kmd_toc.nkr_unlimited.kernel import run
        from kmd_toc.objective_alignment_v1.generators import proxy
        if case.local.n not in (10,12):
            if not self.diagnostic or case.local.n!=2:raise ValueError('EXPLICIT_N2_DIAGNOSTIC_REQUIRED')
            self.protocol['numerical']['bond_by_n']['2']=32
        path=Path(output);path.mkdir(parents=True,exist_ok=False);begin=time.perf_counter();cpu=time.process_time()
        decoded,meta=run(p,oracle_view(case),case.local,self.protocol,path/'kernel')
        items=[]
        for energy,bits,decision,count in decoded:
            row=proposal(decision,case,'measured_quantum',count=count,bits=bits)
            if abs(row['proxy']-energy)>1e-12:raise ValueError('KERNEL_BOUNDARY_OBJECTIVE_MISMATCH')
            items.append(row)
        progress=[json.loads(x) for x in (path/'kernel/evaluations.jsonl').read_text().splitlines()]
        receipt=dict(condition_id=self.condition_id,algorithm='unchanged p2 finite-shot sector-MPS kernel',
            case_hash=case.case_hash,quantum_executed=True,replay_only=False,kernel=meta,
            generation_wall_s=time.perf_counter()-begin,generation_CPU_s=time.process_time()-cpu,
            objective_evaluations=sum(len(r['counts']) for r in progress if r.get('event')=='sampling_completed'),
            quantum_shots=meta['training_shots_actual']+meta['final_shots_actual'],
            optimizer_function_evaluations=meta['nfev'],optimization_iterations=None,
            RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            cost_function='boundary distance only; physical W and RMP duals are not in quantum Hamiltonian')
        dump(path/'GENERATION.json',dict(receipt=receipt,proposals=[{**r,'decision':asdict(r['decision'])} for r in items]))
        return items,receipt
