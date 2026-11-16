"""Scoped scalable extension of existing day columns, LP/IP and Huang AOA.

Whole-trip macro fragments retain original directed OD cost and demands. Exact
berth rows use interval endpoints, without discretizing seconds. Neither finite
macro coverage nor restricted IP optimality proves global VRP optimality.
"""
import itertools
import math
import time
import numpy as np
from .classical import directed_cw
from .completion import complete_routes, assemble


class EventDayMaster:
    def __init__(self,problem,columns,native_threads=None):
        from scipy import sparse
        from kmd_toc.vehicle_day.validation import validate_day
        self.problem=problem;self.columns=tuple(columns);self.n=len(problem.base.customers);self.f=len(problem.vehicles)
        if native_threads is not None and (type(native_threads) is not int or native_threads < 1):
            raise ValueError('INVALID_MASTER_NATIVE_THREADS')
        self.native_threads=native_threads
        self.events=sorted({t for c in columns for trip in c.trips for t in [trip.load_start_s,trip.load_end_s]})
        self.intervals=list(zip(self.events,self.events[1:]));rows=[];cols=[];vals=[]
        vi={v.vehicle_id:i for i,v in enumerate(problem.vehicles)}
        for j,c in enumerate(columns):
            errors=validate_day(problem,c)
            if errors:raise ValueError('INVALID_REAL_DAY_COLUMN:'+str(errors))
            occupied=[k for k,(a,b) in enumerate(self.intervals) if any(t.load_start_s<=a and b<=t.load_end_s for t in c.trips)]
            for i in [*(i-1 for i in c.customers),self.n+vi[c.vehicle_id],*(self.n+self.f+k for k in occupied)]:rows.append(i);cols.append(j);vals.append(1.)
        self.a=sparse.csc_matrix((vals,(rows,cols)),shape=(self.n+self.f+len(self.intervals),len(columns)))
        self.rhs=np.r_[np.ones(self.f),np.full(len(self.intervals),problem.berths)]
        self.d=np.array([c.distance_km for c in columns]);self.w=np.array([c.waiting_min for c in columns])

    def arrays(self,indices,primary,limit):
        from scipy import sparse
        a=self.a[:self.n,indices].tocsc();b=self.a[self.n:,indices].tocsc();rhs=self.rhs.copy()
        cost=(self.d if primary=='D' else self.w)[indices];other=(self.w if primary=='D' else self.d)[indices]
        if limit is not None:b=sparse.vstack([b,sparse.csc_matrix(other.reshape(1,-1))],format='csc');rhs=np.r_[rhs,limit]
        return a,b,rhs,cost

    def lp(self,indices,primary='D',limit=None):
        from scipy.optimize import linprog
        a,b,rhs,cost=self.arrays(indices,primary,limit);r=linprog(cost,A_eq=a,b_eq=np.ones(self.n),A_ub=b,b_ub=rhs,bounds=(0,None),method='highs',options={} if self.native_threads is None else {'threads':self.native_threads})
        if not r.success:return {'success':False,'reason':r.message}
        y=np.r_[r.eqlin.marginals,r.ineqlin.marginals[:len(self.rhs)]]
        other=self.w if primary=='D' else self.d;epsilon_dual=r.ineqlin.marginals[-1] if limit is not None else 0.
        rc=(self.d if primary=='D' else self.w)-np.asarray(self.a.T@y).ravel()-epsilon_dual*other
        if not np.allclose(rc[indices],r.lower.marginals,atol=1e-6):raise ValueError('EVENT_MASTER_DUAL_CHECK')
        return {'success':True,'objective':float(r.fun),'weights':r.x.tolist(),'dual_customer':r.eqlin.marginals.tolist(),'rc':rc.tolist(),'epsilon_dual':float(epsilon_dual)}

    def ip(self,indices,primary='D',limit=None,seconds=30):
        from scipy.optimize import milp,Bounds,LinearConstraint
        begin=time.perf_counter()
        a,b,rhs,cost=self.arrays(indices,primary,limit)
        native={} if self.native_threads is None else {'threads':self.native_threads}
        r=milp(cost,integrality=np.ones(len(indices)),bounds=Bounds(0,1),constraints=[LinearConstraint(a,1,1),LinearConstraint(b,-np.inf,rhs)],options={'time_limit':seconds,'mip_rel_gap':0.0,**native})
        primary_result=r;secondary=None;other=(self.w if primary=='D' else self.d)[indices]
        remaining=max(0.,seconds-(time.perf_counter()-begin))
        if r.x is not None and remaining>0.001:
            # Keep the same primary incumbent/epsilon domain. This is a second
            # classical objective, not a change to the D/W epsilon policy.
            secondary=milp(other,integrality=np.ones(len(indices)),bounds=Bounds(0,1),
                constraints=[LinearConstraint(a,1,1),LinearConstraint(b,-np.inf,rhs),LinearConstraint(cost,-np.inf,float(r.fun)+1e-8)],
                options={'time_limit':remaining,'mip_rel_gap':0.0,**native})
            if secondary.x is not None:
                first=float(cost@secondary.x);second=float(other@secondary.x)
                if first<float(r.fun)-1e-7 or (first<=float(r.fun)+1e-7 and second<=float(other@r.x)+1e-7):r=secondary
        return {'success':r.x is not None,'certified_in_finite_pool':bool(primary_result.success),'status':int(primary_result.status),'reason':primary_result.message,
                'objective':float(cost@r.x) if r.x is not None else None,'mip_gap':float(primary_result.mip_gap) if getattr(primary_result,'mip_gap',None) is not None else None,
                'lexicographic_tie_break':True,'secondary_certified_in_finite_pool':bool(secondary is not None and secondary.success),
                'secondary_objective':float(other@r.x) if r.x is not None else None,
                'primary_secondary_total_budget_s':seconds,'integer_wall_s':time.perf_counter()-begin,
                'selected':[int(i) for i,x in zip(indices,r.x) if x>.5] if r.x is not None else []}


def day_candidates(day,routes,seed_plan,common):
    from kmd_toc.column_generation.models import Route
    from kmd_toc.vehicle_day.generation import make_day
    # Seed calendars define a finite time-pattern domain. Single-trip patterns
    # include all first-ready times, ensuring alternatives for smaller problems.
    by={v.vehicle_id:[] for v in day.vehicles}
    for t in seed_plan.trips:by[t.vehicle_id].append(t.load_start_s)
    pool={};routes=sorted(set(tuple(r) for r in routes))
    for v in day.vehicles:
        starts=sorted(by[v.vehicle_id])
        if not starts:starts=[v.ready_s]
        if len(starts)==1:starts=[starts[0],min(70200,starts[0]+1800+min((sum(day.travel_s[a][b] for a,b in zip((0,*r,0),(0,*r,0)[1:]))+120*len(r) for r in routes),default=0))]
        for r in routes:
            try:
                c=make_day(day,v.vehicle_id,(Route(r),),(starts[0],));pool[c.column_id]=c
            except ValueError:continue
        for a in routes:
            sa=set(a)
            for b in routes:
                if sa.intersection(b):continue
                try:
                    c=make_day(day,v.vehicle_id,(Route(a),Route(b)),tuple(starts[:2]));pool[c.column_id]=c
                except ValueError:continue
    return list(pool.values())


def column_generation(master,initial,primary,limit,max_rounds=40):
    pool=list(initial);trace=[]
    for k in range(max_rounds):
        lp=master.lp(pool,primary,limit)
        if not lp['success']:break
        new=sorted((i for i,rc in enumerate(lp['rc']) if rc< -1e-7 and i not in pool),key=lambda i:(lp['rc'][i],i))[:20]
        trace.append({'round':k,'LP':lp['objective'],'global_min_rc_in_declared_pool':min(lp['rc']),'new_negative':len(new)})
        if not new:break
        pool.extend(new)
    lp=master.lp(pool,primary,limit);ip=master.ip(pool,primary,limit)
    before=ip.copy();zero=[]
    if lp['success']:
        zero=[i for i,rc in enumerate(lp['rc']) if abs(rc)<=1e-7 and i not in pool]
        if zero:pool=sorted(set(pool+zero));ip=master.ip(pool,primary,limit)
    after_zero=ip.copy();all_pool_ip=None
    # LP closure does not ensure that the best integer combination lies on its
    # zero-RC face. If a gap remains, solve ALL declared columns separately.
    if lp['success'] and ip['success'] and ip['objective']>lp['objective']+1e-7:
        all_pool_ip=master.ip(list(range(len(master.columns))),primary,limit)
        if all_pool_ip['success'] and all_pool_ip['objective']<ip['objective']-1e-7:ip=all_pool_ip
    return {'pool':pool,'trace':trace,'LP':lp,'IP_before_zero_face':before,'IP':ip,'zero_face_added':len(zero),
            'IP_after_zero_face':after_zero,'IP_all_declared_columns':all_pool_ip,
            'integer_enrichment_attribution':'classical full finite-pool IP when positive-RC integer columns may matter',
            'zero_face_attribution':'classical finite-catalogue enrichment, not AOA',
            'finite_pool_lp_closed':bool(lp['success'] and min(lp['rc'])>=-1e-7)}


def create_hybrid(p,primary='D',other_limit=None,mark=None):
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.column_generation.models import Route
    from kmd_toc.column_generation.reduction import contract
    from kmd_toc.column_generation.aoa import AOAConfig,PricingAOA
    from kmd_toc.vehicle_day.generation import make_day
    routes,cw=directed_cw(p);seed=complete_routes(p,routes,'D',primary,other_limit,settings={'seed_classical':True,**cw})
    if mark:mark('D_classical_seed_completion_end')
    day=to_vehicle_day(p,delta_s=1);initial=[]
    for v in day.vehicles:
        trips=sorted((t for t in seed.trips if t.vehicle_id==v.vehicle_id),key=lambda t:t.trip_no)
        if trips:initial.append(make_day(day,v.vehicle_id,tuple(Route(tuple(p.od.ids.index(s.stop_id) for s in t.visits)) for t in trips),tuple(t.load_start_s for t in trips)))
    columns=day_candidates(day,routes,seed,p);index={c.column_id:i for i,c in enumerate(columns)}
    master=EventDayMaster(day,columns);seedidx=[index[c.column_id] for c in initial]
    base_lp=master.lp(seedidx,primary,other_limit)
    base=column_generation(master,seedidx,primary,other_limit)
    if not base['LP']['success']:raise ValueError('D_INITIAL_RMP_INFEASIBLE')
    if mark:mark('D_classical_base_column_generation_end')
    quantum=[];q_routes=set();exact_scope=set()
    # W duals have minute units and cannot be subtracted from kilometre route
    # costs. W runs use distance-only AOA proposals; true W/resource reduced
    # costs are evaluated in the day master, never asserted by this proxy.
    duals=base['LP']['dual_customer'] if primary=='D' else [0.]*len(p.stops)
    # Fixed three contiguous fragments per original trip. Full-trip permutations
    # alone enter the new pool; partial/depot-split samples remain in raw logs.
    for iteration in range(2):
        for ri,route in enumerate(routes):
            groups=tuple(tuple(a) for a in np.array_split(np.array(route,dtype=int),min(3,len(route))) if len(a))
            groups=tuple(tuple(int(i) for i in g) for g in groups)
            dom=contract(day.base,duals,groups,f'macro_{iteration}_{ri}',slots=len(groups)+1)
            cfg=AOAConfig(slots=len(groups)+1,p=2,max_evaluations=80,restarts=1,train_shots=1000,final_shots=4096,solver_seed=20261112+100*iteration+ri)
            result=PricingAOA(dom.pricing,dom.dual,cfg).run();accepted=[]
            for small in result['routes']:
                if len(small)==len(groups) and set(small)==set(range(1,len(groups)+1)):
                    full=dom.expand(Route(tuple(small))).customers;q_routes.add(full);accepted.append(full)
            exact={tuple(i for k in order for i in groups[k]) for order in itertools.permutations(range(len(groups)))}
            exact_scope.update(exact)
            quantum.append({'iteration':iteration,'route_index':ri,'fragment_groups':groups,'full_route_obtained':accepted,
                            'full_route_domain_size':len(exact),'sampled_full_route_count':len(set(accepted)),
                            'result':result,'exact_scope_used_to_generate_AOA':False})
        if mark:mark(f'D_AOA_round_{iteration}_end')
    # No exact-domain route is fed to this candidate pool unless actually sampled.
    allroutes=set(routes)|q_routes
    columns=day_candidates(day,allroutes,seed,p);master=EventDayMaster(day,columns);index={c.column_id:i for i,c in enumerate(columns)}
    initialidx=[index[c.column_id] for c in initial]
    solved=column_generation(master,initialidx,primary,other_limit)
    if not solved['IP']['success']:raise ValueError('D_RESTRICTED_INTEGER_NO_PLAN')
    selected=[columns[i] for i in solved['IP']['selected']]
    items=[{'v':next(i for i,v in enumerate(p.vehicles) if v.vehicle_id==c.vehicle_id),'trip_no':t.trip_id,'route':t.customers,'start_s':t.load_start_s} for c in selected for t in c.trips]
    baseobj=base['IP']['objective'];after=solved['IP']['objective']
    meta={'algorithm':'existing_Huang_AOA_plus_exact_event_day_column_extension','scope':'finite_CW_macro_route_and_seed_calendar_domain_NOT_global_VRP',
          'classical_seed':cw,'seed_routes':routes,'seed_plan':__import__('dataclasses').asdict(seed),'base_initial_RMP_LP':base_lp['objective'],'base':base,'hybrid':solved,'quantum':quantum,
          'quantum_new_full_routes':len(q_routes-set(routes)),'macro_full_route_coverage':len(q_routes&exact_scope)/len(exact_scope) if exact_scope else None,
          'macro_full_routes_total':len(exact_scope),'macro_full_routes_obtained':len(q_routes&exact_scope),
          'quantum_candidate_pool_integer_delta':baseobj-after if baseobj is not None else None,
          'quantum_advantage_claim':False,'global_negative_columns_unexplored':'unknown beyond fixed macro/time domain',
          'day_columns':len(columns),'event_intervals':len(master.intervals),'seed':20261112,'primary':primary,'other_limit':other_limit,
          'completion_used_exact_domain_oracle_routes':False,'global_integer_gap':None,
          'integer_tie_policy':'primary_then_other_lexicographic_D-lex-v1',
          'AOA_pricing_scope':'route-distance/customer-dual proposal only; vehicle, berth and epsilon duals evaluated after day construction',
          'AOA_W_proxy':'distance-only proposal; no mixed kilometre/minute dual arithmetic' if primary=='W' else None,
          'qubits_max':max((r['result']['qubits'] for r in quantum),default=0)}
    if mark:mark('D_restricted_LP_IP_zero_face_end')
    return assemble(p,items,'D',meta)
