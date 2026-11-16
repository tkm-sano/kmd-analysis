"""Sparse mirror of validated day LP/IP; new code, existing master untouched.

Rows: customer equality; vehicle <=1; time-slot berth <=B; optional epsilon.
Dual sign follows SciPy/HiGHS marginals. LP rc uses lower bound 0, no upper
bound; binary IP upper bound 1. Node-limit exit never claims optimality.
"""
from time import perf_counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog, milp, Bounds, LinearConstraint
from kmd_toc.vehicle_day.model import occupied_slots
from kmd_toc.vehicle_day.validation import validate_day, validate_plan


class CatalogueMaster:
    def __init__(self, problem, columns):
        self.problem, self.columns = problem, tuple(columns)
        self.ids = [c.column_id for c in columns]
        self.index = {x:i for i,x in enumerate(self.ids)}
        if len(self.index) != len(columns):
            raise ValueError('DUPLICATE_CATALOGUE_COLUMN')
        n, f, u = len(problem.base.customers), len(problem.vehicles), problem.slots
        rows, cols, values = [], [], []
        vr = {v.vehicle_id:n+i for i,v in enumerate(problem.vehicles)}
        self.routes = []
        self.route_index = {}
        for j,c in enumerate(columns):
            errors = validate_day(problem,c)
            if errors: raise ValueError('INVALID_CATALOGUE:' + ','.join(errors))
            r = tuple(t.customers for t in c.trips)
            self.routes.append(r)
            for route in r: self.route_index.setdefault(route, set()).add(j)
            for row in list(i-1 for i in c.customers) + [vr[c.vehicle_id]] + [n+f+s for s in occupied_slots(problem,c)]:
                rows.append(row); cols.append(j); values.append(1.)
        self.a = sparse.csc_matrix((values,(rows,cols)), shape=(n+f+u,len(columns)))
        self.n, self.f = n, f
        self.rhs = np.r_[np.ones(f),np.full(u,problem.berths)]
        self.d = np.array([c.distance_km for c in columns])
        self.w = np.array([c.waiting_min for c in columns])

    def arrays(self, indices, profile):
        ids = np.asarray(indices,dtype=int)
        a = self.a[:self.n,ids].tocsc()
        b = self.a[self.n:,ids].tocsc()
        cost = (self.d if profile.primary=='D' else self.w)[ids]
        other = (self.w if profile.primary=='D' else self.d)[ids]
        rhs = self.rhs.copy()
        if profile.other_limit is not None:
            b = sparse.vstack([b,sparse.csc_matrix(other.reshape(1,-1))],format='csc')
            rhs = np.r_[rhs,profile.other_limit]
        return a,b,rhs,cost,other

    def lp(self, indices, profile, phase='II'):
        started=perf_counter()
        a,b,rhs,cost,_ = self.arrays(indices,profile)
        j=len(indices)
        if phase=='I':
            a=sparse.hstack([a,sparse.eye(self.n)],format='csc')
            b=sparse.hstack([b,sparse.csc_matrix((len(rhs),self.n))],format='csc')
            cost=np.r_[np.zeros(j),np.ones(self.n)]
        if not len(cost): return {'success':False,'reason':'EMPTY_RMP'}
        result=linprog(cost,A_eq=a,b_eq=np.ones(self.n),A_ub=b,b_ub=rhs,bounds=(0,None),method='highs')
        if not result.success:
            return {'success':False,'reason':'RMP_INFEASIBLE' if result.status==2 else 'LP_ERROR','message':result.message,'seconds':perf_counter()-started}
        eq,ub=result.eqlin.marginals,result.ineqlin.marginals
        dual={'phase':phase,'customer':eq.tolist(),
              'vehicle':{v.vehicle_id:float(ub[i]) for i,v in enumerate(self.problem.vehicles)},
              'berth':ub[self.f:self.f+self.problem.slots].tolist(),
              'other':float(ub[-1]) if profile.other_limit is not None else 0.}
        rc=self.rc(dual,profile)
        if not np.allclose(rc[list(indices)],result.lower.marginals[:j],atol=1e-7) or abs(result.fun-(sum(eq)+ub@rhs))>1e-7:
            raise RuntimeError('SPARSE_MASTER_DUAL_INCONSISTENCY')
        return {'success':True,'phase':phase,'objective':float(result.fun),'dual':dual,
                'weights':result.x[:j].tolist(),'artificial_sum':float(sum(result.x[j:])),
                'dual_objective':float(sum(eq)+ub@rhs),'seconds':perf_counter()-started}

    def rc(self,dual,profile):
        cost=np.zeros(len(self.columns)) if dual['phase']=='I' else (self.d if profile.primary=='D' else self.w)
        y=np.r_[dual['customer'],[dual['vehicle'][v.vehicle_id] for v in self.problem.vehicles],dual['berth']]
        other=self.w if profile.primary=='D' else self.d
        return cost - np.asarray(self.a.T@y).ravel() - dual['other']*other

    def ip(self,indices,profile,node_limit=50000):
        started=perf_counter()
        if not indices: return {'success':False,'reason':'EMPTY_INTEGER_POOL','seconds':0.}
        a,b,rhs,cost,_=self.arrays(indices,profile)
        result=milp(cost,integrality=np.ones(len(indices)),bounds=Bounds(0,1),
                    constraints=[LinearConstraint(a,1,1),LinearConstraint(b,-np.inf,rhs)],
                    options={'mip_rel_gap':0.,'node_limit':node_limit})
        output={'success':bool(result.success),'reason':result.message,'status':int(result.status),
                'seconds':perf_counter()-started,'certified_optimal':bool(result.success),
                'selected_indices':[], 'objective':None,
                'mip_gap':float(result.mip_gap) if getattr(result,'mip_gap',None) is not None else None,
                'mip_node_count':int(result.mip_node_count) if getattr(result,'mip_node_count',None) is not None else None}
        if result.x is not None:
            selected=[int(i) for i,x in zip(indices,result.x) if x>.5]
            metrics=validate_plan(self.problem,[self.columns[i] for i in selected])
            if not metrics['valid']: raise RuntimeError('INTEGER_PLAN_INVALID')
            output.update(selected_indices=selected,objective=float(result.fun),metrics=metrics)
        return output

    def complete(self,generated,known):
        """Same catalogue-based completion for AOA and exact reduced-domain control.

        Empty generated set yields no candidates. No oracle route injection.
        """
        generated=set(generated); allowed=set(known)|generated
        possible=set()
        for r in generated: possible.update(self.route_index.get(r,()))
        return {i for i in possible if all(r in allowed for r in self.routes[i])}

    def known(self,pool):
        return {(i,) for i in self.problem.base.customers} | {r for j in pool for r in self.routes[j]}
