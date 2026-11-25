"""Restricted full-PHYSICAL-PLAN columns: schedules are indivisible columns.

The LP is a finite-column convex relaxation, never an executable mixture.
Exact integer selection solves sum(z)=1, z binary by enumerating those columns.
Sampled distance pricing is not an exhaustive dual-compatible pricing oracle.
"""
from pathlib import Path
from fractions import Fraction as F
import time
from kmd_toc.objective_alignment_v1.archive import Archive
from kmd_toc.objective_alignment_v1.objective import measure,record
from kmd_toc.common_initial_v1.plans import dump,sha
from kmd_toc.duty_break_v1.models import load_plan
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.measurement_audit_v1.measurement import cross_evaluate,physical_payload,digest_payload

def solve_lp(values,reference):
    import numpy as np
    from scipy.optimize import linprog
    positive=reference.D>0 and reference.W>0;N=len(values)
    if positive:
        d=[float(v.D/reference.D) for v in values];w=[float(v.W/reference.W) for v in values]
        c=[0.]*N+[1.];a=[d+[-1.],w+[-1.]];b=[0.,0.];eq=[[1.]*N+[0.]]
        fit=linprog(c,A_ub=a,b_ub=b,A_eq=eq,b_eq=[1.],bounds=[(0,None)]*(N+1),method='highs',options={'threads':1})
    else:
        d=w=None
        c=[float(v.W if reference.W==0 and reference.D>0 else v.D) for v in values]
        fit=linprog(c,A_eq=[[1.]*N],b_eq=[1.],bounds=(0,None),method='highs',options={'threads':1})
    if not fit.success:raise ValueError('FULL_PLAN_RMP_LP_FAILED:'+fit.message)
    y=float(fit.eqlin.marginals[0]);duals=list(map(float,fit.ineqlin.marginals)) if positive else []
    def rc(v):
        if positive:return -duals[0]*float(v.D/reference.D)-duals[1]*float(v.W/reference.W)-y
        return float(v.W if reference.W==0 and reference.D>0 else v.D)-y
    rcs=[rc(v) for v in values]
    if any(x < -1e-7 for x in rcs):raise ValueError('RMP_DUAL_SIGN_OR_KKT_MISMATCH')
    return dict(status='OPTIMAL_FINITE_COLUMN_LP',objective=float(fit.fun),weights=list(map(float,fit.x[:N])),
        distance_normalized_dual=duals[0] if positive else None,wait_normalized_dual=duals[1] if positive else None,
        convexity_dual=y,existing_column_reduced_costs=rcs,
        mode='POSITIVE_MIN_MAX_NORMALIZED' if positive else 'ZERO_REFERENCE_EXCEPTION_PRIMARY_ONLY',
        I_dual_relaxation_percent=100*(1-float(fit.fun)) if positive else None,
        domain='convex combinations of supplied complete feasible pi0-nonworsening physical plans',
        executable=False,global_VRP_bound=False)

def reduced_cost(value,reference,lp):
    if lp['mode']=='POSITIVE_MIN_MAX_NORMALIZED':
        return (-lp['distance_normalized_dual']*float(value.D/reference.D)
                -lp['wait_normalized_dual']*float(value.W/reference.W)-lp['convexity_dual'])
    return float(value.W if reference.W==0 and reference.D>0 else value.D)-lp['convexity_dual']

class PhysicalMaster:
    def __init__(self,p,initial,output):
        self.p=p;self.out=Path(output);self.out.mkdir(parents=True,exist_ok=False)
        self.archive=Archive(p,initial,self.out/'columns');self.reference=self.archive.reference
        self.trace=[];self.lp_s=0.;self.integer_s=0.;self.last=None
        self.optimize()
    def values(self):return [x['metrics'] for _,x in sorted(self.archive.candidates.items())]
    def optimize(self):
        tick=time.perf_counter();self.last=solve_lp(self.values(),self.reference);self.lp_s+=time.perf_counter()-tick
        self.trace.append(dict(event='RMP_REOPTIMIZE',columns=len(self.archive.candidates),LP=self.last));return self.last
    def add(self,plan,*,origin,branch_id=0):
        before=set(self.archive.candidates)
        kept=self.archive.add(plan,origin=origin,branch_id=branch_id)
        row=self.archive.rows[-1]
        if row['status']=='INFEASIBLE_OR_MEASUREMENT_FAIL':return kept,None
        m=measure(self.p,plan);rc=reduced_cost(m,self.reference,self.last)
        new=set(self.archive.candidates)-before
        self.trace.append(dict(event='PHYSICAL_COLUMN',origin=origin,retained=kept,new=bool(new),
            full_schedule_reduced_cost=rc,negative_reduced_cost=rc < -1e-7,
            admitted_as='negative_RC_sample' if rc < -1e-7 else 'finite_pool_enrichment_not_classical_CG_certificate',
            **record(m,self.reference)))
        # Archive and integer problem keep all generated admissible plans,
        # including zero/positive RC columns. Never lose an integer winner.
        if new:self.optimize()
        return kept,m
    def finish(self):
        tick=time.perf_counter();plan,why=self.archive.best();self.integer_s+=time.perf_counter()-tick
        sid=digest_payload(physical_payload(plan));path=self.out/'columns'/f'{sid}.json'
        loaded=load_plan(path);require_valid(self.p,loaded)
        if digest_payload(physical_payload(loaded))!=sid or measure(self.p,loaded)!=measure(self.p,plan):
            raise ValueError('INTEGER_COLUMN_RECONSTRUCTION_MISMATCH')
        if cross_evaluate(self.p,loaded)['status']!='PASS':raise ValueError('FINAL_INDEPENDENT_MEASUREMENT_FAIL')
        self.archive.save(self.out/'ARCHIVE.json')
        result=dict(selected=why,column_path=str(path),column_sha256=sha(path),
            physical_reconstruction='one complete scheduled column; no fractional route mixing or reassignment',
            integer_solver='exact enumeration of one-hot binary full-plan columns under frozen ranking',
            integer_optimality='supplied feasible retained columns ONLY',
            LP=self.last,LP_s=self.lp_s,integer_s=self.integer_s,trace=self.trace,
            full_dual_compatible_pricing='HOLD_DISTANCE_QUANTUM_ORACLE_DOES_NOT_REPRESENT_COUPLED_W',
            route_combination_master='NOT_IMPLEMENTED_THIS_IS_COMPLETE_PLAN_COLUMN_RESTRICTION',
            full_VRP_optimality=False)
        dump(self.out/'MASTER.json',result);return loaded,result
