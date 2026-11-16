"""Counters drive termination. Clocks only annotate observations."""
import json
import math
from pathlib import Path
import time


class WorkLimit(Exception):
    pass


class Ledger:
    def __init__(self, directory=None, clock=time.perf_counter):
        self.directory=Path(directory) if directory else None
        if self.directory:self.directory.mkdir(parents=True,exist_ok=True)
        self.clock=clock;self.start=clock();self.counts={};self.events=[]

    def emit(self,event,**values):
        record={'event':event,'elapsed_s':self.clock()-self.start,**values}
        self.events.append(record)
        if self.directory:
            with (self.directory/'work.jsonl').open('a') as stream:
                stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')

    def count(self,key,n=1):
        self.counts[key]=self.counts.get(key,0)+n
        return self.counts[key]

    def capture(self,name,value):
        if self.directory:
            from kmd_toc.dwt.worker import dump
            from dataclasses import is_dataclass,asdict
            dump(self.directory/(name+'.json'),asdict(value) if is_dataclass(value) else value)


class CheckBudget:
    """Shared callable used by all native CustomLimit clones, never reset.

    Count active predicates up to the request boundary; subsequent native
    acknowledgement calls are recorded separately and continue returning True.
    No clock, solution count, improvement or feasibility is consulted.
    """
    def __init__(self,limit):
        if type(limit) is not int or limit<1:raise ValueError('POSITIVE_WORK_LIMIT')
        self.limit=limit;self.checks=0;self.acknowledgements=0;self.reached=False
    def __call__(self):
        if self.reached:self.acknowledgements+=1;return True
        self.checks+=1
        self.reached=self.checks>=self.limit
        return self.reached


def key(plan):
    return (int(round(math.fsum(t.distance_m for t in plan.trips)*10)),sum(t.waiting_s for t in plan.trips))


def verified(p,plan,ledger):
    if plan is None:return False
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.independent import recompute
    a,b=validate_plan(p,plan),recompute(p,plan)
    ledger.count('double_candidate_checks')
    good=bool(a.feasible and b['feasible'] and abs(a.D_km-float(b['D_km']))<=1e-7 and abs(a.W_min-float(b['W_min']))<=1e-7)
    ledger.emit('candidate_checked',valid=good,D=a.D_km if good else None,W=a.W_min if good else None)
    return good
