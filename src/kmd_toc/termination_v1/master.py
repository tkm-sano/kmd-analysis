"""Finite candidate catalogue and native non-time work limits."""
import math
import numpy as np
from kmd_toc.pipeline.hybrid import EventDayMaster, column_generation

class FiniteMaster(EventDayMaster):
    def __init__(self,day,columns,config,ledger):
        super().__init__(day,columns,native_threads=1)
        self.config=config;self.ledger=ledger
    def lp(self,indices,primary='D',limit=None):
        from scipy.optimize import linprog
        a,b,rhs,cost=self.arrays(indices,primary,limit)
        cap=max(self.config['catalogue']['LP_min_iterations'],self.config['catalogue']['LP_iterations_per_row_column']*(a.shape[0]+b.shape[0]+len(indices)))
        # Dual simplex, finite iterations; no IPM crossover or presolve hidden solve.
        r=linprog(cost,A_eq=a,b_eq=np.ones(self.n),A_ub=b,b_ub=rhs,bounds=(0,None),method='highs-ds',
                  options={'maxiter':cap,'presolve':False,'threads':1})
        self.ledger.count('LP_calls');self.ledger.count('LP_iterations',int(r.nit))
        self.ledger.emit('LP_end',iteration_limit=cap,iterations=int(r.nit),status=int(r.status),reason=r.message)
        if not r.success:return {'success':False,'reason':r.message,'status':int(r.status)}
        y=np.r_[r.eqlin.marginals,r.ineqlin.marginals[:len(self.rhs)]]
        other=self.w if primary=='D' else self.d
        dual=r.ineqlin.marginals[-1] if limit is not None else 0.
        rc=(self.d if primary=='D' else self.w)-np.asarray(self.a.T@y).ravel()-dual*other
        if not np.allclose(rc[indices],r.lower.marginals,atol=1e-6):raise ValueError('EVENT_MASTER_DUAL_CHECK')
        return {'success':True,'objective':float(r.fun),'weights':r.x.tolist(),'dual_customer':r.eqlin.marginals.tolist(),'rc':rc.tolist(),'epsilon_dual':float(dual)}
    def ip(self,indices,primary='D',limit=None,seconds=None):
        # seconds exists only to satisfy inherited column_generation's API; passing it is forbidden.
        if seconds is not None:raise ValueError('TIME_BUDGET_FORBIDDEN')
        from scipy.optimize import milp,Bounds,LinearConstraint
        a,b,rhs,cost=self.arrays(indices,primary,limit)
        cap=self.config['catalogue']['IP_nodes_per_vehicle']*self.f
        constraints=[LinearConstraint(a,1,1),LinearConstraint(b,-np.inf,rhs)]
        options={'node_limit':cap,'presolve':False,'mip_rel_gap':0.,'mip_abs_gap':0.,'threads':1,
                 'simplex_iteration_limit':max(1000,4*(self.a.shape[0]+len(indices))),
                 'mip_max_stall_nodes':cap}
        first=milp(cost,integrality=np.ones(len(indices)),bounds=Bounds(0,1),constraints=constraints,options=options)
        self.ledger.count('IP_calls')
        self.ledger.emit('IP_end',objective_stage='primary',node_limit=cap,status=int(first.status),nodes=getattr(first,'mip_node_count',None),reason=first.message)
        selected=first;second=None;other=(self.w if primary=='D' else self.d)[indices]
        if first.x is not None:
            second=milp(other,integrality=np.ones(len(indices)),bounds=Bounds(0,1),
                constraints=constraints+[LinearConstraint(cost,-np.inf,float(first.fun)+1e-8)],options=options)
            self.ledger.count('IP_calls')
            self.ledger.emit('IP_end',objective_stage='secondary',node_limit=cap,status=int(second.status),nodes=getattr(second,'mip_node_count',None),reason=second.message)
            if second.x is not None and (float(cost@second.x)<float(first.fun)-1e-7 or
                (float(cost@second.x)<=float(first.fun)+1e-7 and float(other@second.x)<=float(other@first.x)+1e-7)):
                selected=second
        return {'success':selected.x is not None,'certified_in_finite_pool':bool(first.success),'status':int(first.status),
            'reason':first.message,'objective':float(cost@selected.x) if selected.x is not None else None,
            'mip_gap':float(first.mip_gap) if getattr(first,'mip_gap',None) is not None else None,
            'lexicographic_tie_break':True,'secondary_certified_in_finite_pool':bool(second is not None and second.success),
            'selected':[int(i) for i,x in zip(indices,selected.x) if x>.5] if selected.x is not None else []}


def catalogue(p,day,pool,seed_plan,initial,config,ledger):
    from kmd_toc.column_generation.models import Route
    from kmd_toc.vehicle_day.generation import make_day
    from kmd_toc.pipeline.completion import route_duration
    by={v.vehicle_id:[] for v in day.vehicles}
    for t in seed_plan.trips:by[t.vehicle_id].append(t.load_start_s)
    routes=sorted(set(tuple(r) for r in pool));groups={}
    for r in routes:groups.setdefault(tuple(sorted(r)),[]).append(r)
    coverage=sorted(groups);where={g:i for i,g in enumerate(coverage)}
    patterns=[(r,) for r in routes]
    for r in routes:
        g=tuple(sorted(r));k=where[g];variant=groups[g].index(r)
        for offset in config['catalogue']['partner_coverage_offsets']:
            neighbour=coverage[(k+offset)%len(coverage)]
            b=groups[neighbour][variant%len(groups[neighbour])]
            patterns.append((r,b))
    columns={c.column_id:c for c in initial}
    for v in day.vehicles:
        starts=sorted(by[v.vehicle_id]) or [v.ready_s]
        if len(starts)==1:starts.append(min(70200,starts[0]+1800+min((route_duration(p,r) for r in routes),default=0)))
        for pattern in patterns:
            ledger.count('day_pattern_attempts')
            if len(pattern)==2 and set(pattern[0]).intersection(pattern[1]):
                ledger.count('day_pattern_overlap_rejections');continue
            try:c=make_day(day,v.vehicle_id,tuple(Route(r) for r in pattern),tuple(starts[:len(pattern)]))
            except ValueError:
                ledger.count('day_pattern_infeasible');continue
            if c.column_id in columns:ledger.count('day_pattern_duplicates')
            columns[c.column_id]=c
    ledger.emit('catalogue_complete',routes=len(routes),coverage_groups=len(coverage),vehicles=len(day.vehicles),
        patterns_per_vehicle=len(patterns),columns=len(columns),termination='CONSTRUCTION_COMPLETE',
        scope='all single trips plus two cyclic coverage-neighbour partners per variant, all vehicles; seed columns preserved')
    return list(columns.values())


def solve_master(p,day,pool,seed_plan,initial,config,ledger,label):
    columns=catalogue(p,day,pool,seed_plan,initial,config,ledger)
    master=FiniteMaster(day,columns,config,ledger);index={c.column_id:i for i,c in enumerate(columns)}
    outcome=column_generation(master,[index[c.column_id] for c in initial],'D',None,
                              max_rounds=config['catalogue']['column_generation_rounds'])
    ledger.capture(label,{'outcome':outcome,'columns':len(columns)})
    return columns,outcome
