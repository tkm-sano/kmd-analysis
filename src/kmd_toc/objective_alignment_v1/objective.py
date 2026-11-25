"""Exact common objective and integer representation; no floating tolerances."""
from dataclasses import dataclass
from fractions import Fraction as F
from math import lcm,gcd
from kmd_toc.d_final_selection_v1.ranking import Metrics,Candidate,rank_key,score
from kmd_toc.duty_break_v1.local import metrics

SAFE=(1<<62)-1  # conservative guard on coefficients AND possible activities

class ObjectiveHold(ValueError):pass

def measure(p,plan):return Metrics(*metrics(p,plan))

def metric_key(m,reference):
    # Reuse frozen metric ordering, without the old four-branch ID domain.
    return rank_key(Candidate(0,m),reference)[:-2]

def retained(reference,candidate):
    if reference.D==0 or reference.W==0:return True
    return candidate.D<=reference.D and candidate.W<=reference.W

def selection_key(m,reference,*,initial=False,branch_id=0,stable_id=''):
    if type(branch_id) is not int or branch_id<0:raise ValueError('FIXED_NONNEGATIVE_BRANCH_ID_REQUIRED')
    return (*metric_key(m,reference),not initial,branch_id,stable_id)

def local_update(old,new):
    return new.D<=old.D and new.W<=old.W and new!=old

def record(m,reference):
    value,total=score(m,reference)
    return {'D_km':float(m.D),'W_total_min':float(m.W),'D_exact':str(m.D),'W_exact':str(m.W),
        'I_dual_percent':float(value) if value is not None else None,
        'I_dual_exact':str(value) if value is not None else None,
        'I_dual_status':'defined' if value is not None else 'undefined',
        'relative_sum_exact':str(total) if total is not None else None}

@dataclass(frozen=True)
class Units:
    scale_per_m:int
    costs:tuple[int,...]
    q0:int
    l0:int
    q_bound:int
    l_bound:int
    alpha:int
    beta:int
    objective_bound:int
    mode:str

    def target(self,q,l):
        if self.mode=='POSITIVE':return max(self.alpha*q,self.beta*l)
        return l if self.mode=='ZERO_W' else q

def exact_units(p,routes,initial):
    index={s:i for i,s in enumerate(p.od.ids)}
    def cost(route):
        nodes=(0,*route,0)
        return sum((F(str(float(p.od.distance_m[a,b]))) for a,b in zip(nodes,nodes[1:])),F(0))
    values=[cost(r) for r in routes];m=measure(p,initial);base=m.D*1000
    if any(v<0 for v in values):raise ObjectiveHold('NEGATIVE_EXACT_DISTANCE')
    unit=lcm(base.denominator,*(v.denominator for v in values))
    costs=tuple(int(v*unit) for v in values);q0=int(base*unit)
    seconds=m.W*60
    if seconds.denominator!=1:raise ObjectiveHold('WAIT_NOT_EXACT_INTEGER_SECONDS')
    l0=int(seconds);S=2*len(p.vehicles)
    # Sum of all Boolean coefficients, stronger than a feasible-solution bound.
    qb=S*sum(costs);lb=43200*S
    mode='POSITIVE' if q0>0 and l0>0 else 'ZERO_W' if q0>0 else 'ZERO_D_OR_BOTH'
    g=gcd(q0,l0) or 1;alpha=l0//g;beta=q0//g
    bound=alpha*qb+beta*lb if mode=='POSITIVE' else max(qb,lb)
    if max(unit,q0,l0,qb,lb,alpha,beta,bound,*costs)>SAFE:
        raise ObjectiveHold('EXACT_OBJECTIVE_EXCEEDS_CONSERVATIVE_INT64_ACTIVITY_BOUND')
    return Units(unit,costs,q0,l0,qb,lb,alpha,beta,bound,mode)
