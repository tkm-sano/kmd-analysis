"""One fixed physical trip, fixed boundary, permutation-only local variables."""
from dataclasses import dataclass,asdict
from itertools import permutations
import math,random,time
from .io import encode_routes,decode_routes,assignment_hash
from kmd_toc.measurement_audit_v1.measurement import digest_payload

ENCODING='fixed-trip-permutation-register-v3-no-separator'
@dataclass(frozen=True)
class OrderProblem:
    vehicle:str
    trip:int
    ids:tuple
    prefix:tuple
    suffix:tuple
    entry:str
    exit:str
    lookup:dict
    assignment_hash:str
    routes:list
    seed:int
    problem_hash:str
    od_hash:str
    encoding:str=ENCODING
    @property
    def n(self):return len(self.ids)
    @property
    def fingerprint(self):return digest_payload(asdict(self))

def build(p,rs,size,seed,affected_slots=()):
    preferred={tuple(k) for k in affected_slots}
    eligible=sorted((k,r) for k,r in rs.items() if len(r)>=size)
    if not eligible:return None
    key,r=min(eligible,key=lambda x:(x[0] not in preferred,-len(x[1]),x[0]))
    # Boundary window rotates deterministically with the registered local seed.
    at=seed%(len(r)-size+1);ids=r[at:at+size];pre=r[:at];suf=r[at+size:]
    entry=pre[-1] if pre else p.depot.depot_id;exit=suf[0] if suf else p.depot.depot_id
    index={s:i for i,s in enumerate(p.od.ids)};dist=lambda a,b:float(p.od.distance_m[index[a],index[b]])
    edge=[[dist(a,b) for b in ids] for a in ids];first=[dist(entry,b) for b in ids];last=[dist(a,exit) for a in ids]
    bound=max(1.,(size+1)*max([*first,*last,*(x for row in edge for x in row)]))
    lookup=dict(first=first,last=last,edge=edge,bound_m=bound,version='directed_fixed_boundary_order_v3',W_in_oracle=False)
    return OrderProblem(key[0],key[1],ids,pre,suf,entry,exit,lookup,assignment_hash(rs),encode_routes(rs),seed,p.fingerprint,p.od.fingerprint)

def cost(problem,order):
    if len(order)!=problem.n or set(order)!=set(range(problem.n)):raise ValueError('NOT_A_FIXED_TRIP_PERMUTATION')
    c=problem.lookup
    return math.fsum([c['first'][order[0]],c['last'][order[-1]],*(c['edge'][a][b] for a,b in zip(order,order[1:]))])

def expand(problem,order):
    cost(problem,order);rs=decode_routes(problem.routes);key=(problem.vehicle,problem.trip)
    rs[key]=problem.prefix+tuple(problem.ids[i] for i in order)+problem.suffix
    if assignment_hash(rs)!=problem.assignment_hash:raise ValueError('LOCAL_SOLVER_CHANGED_PHYSICAL_SLOT_MEMBERSHIP')
    return rs

def classical(problem,settings,return_limit):
    begin=time.perf_counter();rng=random.Random(settings.get('rng_seed',problem.seed));evaluations=0;pool={};budget=settings['classical_evaluations'];starts=0;passes=0
    def evaluate(order):
        nonlocal evaluations
        if evaluations>=budget:return None
        evaluations+=1;order=tuple(order);v=cost(problem,order);pool[order]=v;return v
    if problem.n<=settings['classical_exact_up_to']:
        algorithm='exact_directed_permutation_enumeration'
        for order in permutations(range(problem.n)):
            if evaluate(order) is None:break
    else:
        algorithm='multistart_directed_swap_and_reversal_local_search'
        for restart in range(settings['classical_starts']):
            order=list(range(problem.n))
            if restart:rng.shuffle(order)
            value=evaluate(order)
            if value is None:break
            starts+=1
            for sweep in range(settings['classical_sweeps_per_start']):
                passes+=1
                best=(value,tuple(order));improved=False
                pairs=[(i,j) for i in range(problem.n) for j in range(i+1,problem.n)];rng.shuffle(pairs)
                for i,j in pairs:
                    for operator in ('swap','reverse'):
                        other=order.copy()
                        if operator=='swap':other[i],other[j]=other[j],other[i]
                        else:other[i:j+1]=reversed(other[i:j+1])
                        c=evaluate(other)
                        if c is None:break
                        if (c,tuple(other))<best:best=(c,tuple(other));improved=True
                    if evaluations>=budget:break
                value,seq=best;order=list(seq)
                if not improved or evaluations>=budget:break
    # Solver selection is declared before execution; every returned candidate
    # is subsequently evaluated globally, without distance top-k at that stage.
    returned=sorted(pool,key=lambda o:(pool[o],o))[:return_limit]
    return [dict(order=list(o),source='classical_order_only',local_distance_m=pool[o]) for o in returned],dict(
        algorithm=algorithm,objective_evaluations=evaluations,raw_candidate_evaluations=evaluations,
        unique_generated=len(pool),returned=len(returned),return_limit=return_limit,quantum_shots=0,
        wall_s=time.perf_counter()-begin,encoding=ENCODING,
        selection='distinct lowest local directed costs within fixed finite classical budget; no refill',
        starts_executed=starts,local_search_passes=passes,stop_reason='finite evaluation/start/sweep limits or local no-improvement',
        exact_enumeration_completed=problem.n<=settings['classical_exact_up_to'] and len(pool)==math.factorial(problem.n))
