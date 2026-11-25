"""Every candidate is rebuilt as a full vehicle-day schedule, never patched times."""
from pathlib import Path
from fractions import Fraction
from .io import dump,read,identity,save_plan,load_plan,assignment_hash,atomic
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.measurement_audit_v1.measurement import independent
from kmd_toc.objective_alignment_v1.objective import measure,record,selection_key

def metrics(p,plan,reference=None):
    validation=require_valid(p,plan);m=measure(p,plan);check=independent(p,plan)
    if check['status']!='PASS' or Fraction(check['D_exact'])!=m.D or Fraction(check['W_exact'])!=m.W:
        raise ValueError('INDEPENDENT_FULL_PLAN_DW_MISMATCH')
    first=sum(t.waiting_s for t in plan.trips if t.trip_no==1);second=sum(t.waiting_s for t in plan.trips if t.trip_no==2)
    if Fraction(first+second,60)!=m.W:raise ValueError('WAIT_BREAKDOWN_DISAGREEMENT')
    return dict(**record(m,reference or m),first_trip_W_min=first/60,second_trip_W_min=second/60,
        active_trips=len(plan.trips),model_feasible=True,site_feasibility=validation['stopping_site_feasibility'],
        physical_hash=identity(plan),assignment_hash=assignment_hash({(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}))

def evaluate(p,rs,condition):
    method='D' if condition=='D_quantum' else 'C'
    plan=schedule(p,rs,method,dict(condition_id=condition,algorithm='adaptive_reallocation_then_fixed_order_v3'))
    # schedule rebuilds first/second ready, every trip return, break and shared
    # FCFS queue from routes; no old ready/load/return times are supplied.
    metrics(p,plan);return plan

class Archive:
    def __init__(self,p,initial,directory):
        self.p=p;self.ref=measure(p,initial);self.initial_hash=identity(initial);self.out=Path(directory)
        self.out.mkdir(parents=True,exist_ok=True);self.entries={}
        self.origins=read(self.out/'ORIGINS.json') if (self.out/'ORIGINS.json').exists() else {}
        for path in self.out.glob('*.json'):
            if not path.name.endswith('.plan.json'):continue
            plan=load_plan(path);self.add(plan,'reloaded')
        self.add(initial,'initial')
    def add(self,plan,origin):
        m=metrics(self.p,plan,self.ref);sid=m['physical_hash'];path=self.out/(sid+'.plan.json')
        save_plan(path,plan)
        if origin!='reloaded' and origin not in self.origins.get(sid,[]):
            self.origins.setdefault(sid,[]).append(origin);atomic(self.out/'ORIGINS.json',self.origins)
        self.entries[sid]=dict(plan=plan,metrics=m,origin=origin,path=str(path))
        return sid
    def key(self,plan):
        return selection_key(measure(self.p,plan),self.ref,initial=identity(plan)==self.initial_hash,stable_id=identity(plan))
    def best(self):return min(self.entries.values(),key=lambda r:self.key(r['plan']))
