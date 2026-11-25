"""Independent copy of existing duty CP constraints; exact pi0 objective.

Physical template copied from duty_break_v1/cp.py. Old file is unchanged.
"""
from fractions import Fraction as F
from kmd_toc.duty_break_v1.scheduler import schedule,route_data,NoDutySchedule
from kmd_toc.duty_break_v1.validation import require_valid
from .objective import exact_units,ObjectiveHold,measure,record,metric_key,Metrics

TEMPLATE_SHA256='790bae5a6a0c17d05004a4f7532cbbb737dcae651dee95e3e5e98504b9163930'


def solve(p,routes,initial,config,seed,*,pinned_assignments=None):
    from ortools.sat.python import cp_model
    from ortools.sat import sat_parameters_pb2
    require_valid(p,initial)
    p.validate_duty()
    routes=sorted(set(tuple(r) for r in routes if r));V=len(p.vehicles);S=2*V;B=len(p.berths)
    if not routes or any(not r or len(set(r))!=len(r) or len(r)>60 or
                         any(type(i) is not int or not 1<=i<=len(p.stops) for i in r) for r in routes):
        raise ValueError('DUTY_INVALID_ROUTE_POOL')
    model=cp_model.CpModel();x={};used=[];starts=[];returns=[];ready=[];ordered_ready=[];wait=[];rest=[]
    units=exact_units(p,routes,initial);costs=units.costs;dur=[];domains=[]
    for r in routes:
        travel,_,offsets=route_data(p,tuple(p.od.ids[i] for i in r))
        dur.append(sum(travel)+120*len(r))
        domains.append(cp_model.Domain.FromIntervals([[43200-1800-offset,46800-1800-offset] for _,offset in offsets]) if offsets else None)
    sentinel=72001;horizon=sentinel+S*1800
    for s in range(S):
        active=model.NewBoolVar(f'used{s}');used.append(active)
        start=model.NewIntVar(28800,horizon,f'start{s}');starts.append(start)
        ret=model.NewIntVar(0,68400,f'return{s}');returns.append(ret)
        rd=model.NewIntVar(0,68400,f'ready{s}');ready.append(rd)
        y=model.NewBoolVar(f'break_in_slot{s}');rest.append(y)
        chosen_eligible=[]
        for r,domain in enumerate(domains):
            a=model.NewBoolVar(f'x{s}_{r}');x[s,r]=a
            if domain is not None:
                e=model.NewBoolVar(f'eligible{s}_{r}')
                model.AddLinearExpressionInDomain(start,domain).OnlyEnforceIf(e)
                model.AddLinearExpressionInDomain(start,domain.complement()).OnlyEnforceIf(e.Not())
                conjunction=model.NewBoolVar(f'chosen_eligible{s}_{r}')
                model.Add(conjunction<=a);model.Add(conjunction<=e);model.Add(conjunction>=a+e-1)
                chosen_eligible.append(conjunction)
        model.Add(sum(x[s,r] for r in range(len(routes)))==active)
        eligible=sum(chosen_eligible)
        if s%2==0:
            model.Add(y==eligible)
            model.Add(rd==p.vehicles[s//2].first_ready_s).OnlyEnforceIf(active)
        else:
            model.Add(active<=used[s-1]);model.Add(rd==returns[s-1]).OnlyEnforceIf(active)
            model.Add(y<=eligible);model.Add(y+rest[s-1]<=1);model.Add(y>=eligible-rest[s-1])
        model.Add(rd==0).OnlyEnforceIf(active.Not())
        model.Add(ret==start+1800+sum(dur[r]*x[s,r] for r in range(len(routes)))+3600*y).OnlyEnforceIf(active)
        model.Add(ret==0).OnlyEnforceIf(active.Not())
        sr=model.NewIntVar(0,sentinel,f'sort_ready{s}');ordered_ready.append(sr)
        model.Add(sr==rd).OnlyEnforceIf(active);model.Add(sr==sentinel).OnlyEnforceIf(active.Not())
        w=model.NewIntVar(0,43200,f'wait{s}');wait.append(w)
        model.Add(w==start-rd).OnlyEnforceIf(active);model.Add(w==0).OnlyEnforceIf(active.Not())
    for v in range(V):
        first,second=2*v,2*v+1
        if p.rest_options.allow_post_final_depot_break and p.rest_options.eligible(p.depot.depot_id):
            # User clarification: only active vehicles returned by noon may
            # use 12:00-13:00 at the depot. Unused vehicles have no plan break.
            none=[rest[first].Not(),rest[second].Not()]
            model.Add(returns[second]<=43200).OnlyEnforceIf([*none,used[second]])
            model.Add(returns[first]<=43200).OnlyEnforceIf([*none,used[second].Not(),used[first]])
        else:model.Add(rest[first]+rest[second]==used[first])
    for customer in range(1,len(p.stops)+1):
        cover=[x[s,r] for s in range(S) for r,route in enumerate(routes) if customer in route]
        if not cover:raise ValueError('DUTY_ROUTE_POOL_MISSING_CUSTOMER')
        model.Add(sum(cover)==1)
    if pinned_assignments is not None:
        rid={r:i for i,r in enumerate(routes)};slot={}
        ids={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
        for (vid,k),r in pinned_assignments.items():
            if vid not in ids or k not in (1,2) or tuple(r) not in rid:raise ValueError('PINNED_ASSIGNMENT_SCHEMA')
            slot[2*ids[vid]+k-1]=rid[tuple(r)]
        for s in range(S):
            for r in range(len(routes)):model.Add(x[s,r]==int(slot.get(s)==r))
    # Unchanged common queue priority (ready, vehicle string, trip integer).
    tie={s:i for i,(_,_,s) in enumerate(sorted((p.vehicles[s//2].vehicle_id,s%2+1,s) for s in range(S)))}
    priority=[ordered_ready[s]*(S+1)+tie[s] for s in range(S)];pred=[[] for _ in range(S)]
    for s in range(S):
        for t in range(s+1,S):
            before=model.NewBoolVar(f'before{s}_{t}')
            model.Add(priority[s]<priority[t]).OnlyEnforceIf(before)
            model.Add(priority[s]>priority[t]).OnlyEnforceIf(before.Not())
            pred[t].append(before);pred[s].append(before.Not())
    rank=[model.NewIntVar(0,S-1,f'rank{s}') for s in range(S)]
    order=[model.NewIntVar(0,S-1,f'order{j}') for j in range(S)]
    for s in range(S):model.Add(rank[s]==sum(pred[s]))
    model.AddInverse(rank,order);ordered_start=[]
    for j in range(S):
        rd=model.NewIntVar(0,sentinel,f'ordered_ready{j}');model.AddElement(order[j],ordered_ready,rd)
        st=model.NewIntVar(28800,horizon,f'ordered_start{j}');ordered_start.append(st)
        model.AddMaxEquality(st,[rd,28800 if j<B else ordered_start[j-B]+1800])
    for s in range(S):model.AddElement(rank[s],ordered_start,starts[s])
    D=sum(costs[r]*x[s,r] for s in range(S) for r in range(len(routes)));W=sum(wait)
    model.AddDecisionStrategy([x[s,r] for r in sorted(range(len(routes)),key=lambda r:(costs[r],routes[r])) for s in range(S)],
                              cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE)
    # Only valid DUTY schedules may be hints; no old unbroken schedule is a fallback.
    try:
        raw=pinned_assignments
        if raw is None:
            raw={(t.vehicle_id,t.trip_no):tuple(p.od.ids.index(v.stop_id) for v in t.visits) for t in initial.trips}
        hint=schedule(p,{k:tuple(p.od.ids[i] for i in r) for k,r in raw.items()},'C')
        rid={r:i for i,r in enumerate(routes)};ids={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
        if any(tuple(p.od.ids.index(v.stop_id) for v in t.visits) not in rid for t in hint.trips):
            raise ValueError('INITIAL_HINT_OUTSIDE_SUPPLIED_POOL; INCUMBENT_STILL_RETAINED_EXTERNALLY')
        for t in hint.trips:
            s=2*ids[t.vehicle_id]+t.trip_no-1;r=tuple(p.od.ids.index(v.stop_id) for v in t.visits)
            model.AddHint(x[s,rid[r]],1);model.AddHint(starts[s],t.load_start_s)
    except (NoDutySchedule,ValueError,IndexError):pass
    if units.mode=='POSITIVE':
        T=model.NewIntVar(0,units.objective_bound,'exact_dual_max_ratio_numerator')
        model.AddMaxEquality(T,[units.alpha*D,units.beta*W])
        stages=[T,units.alpha*D+units.beta*W,D,W]
    else:stages=[W,D] if units.mode=='ZERO_W' else [D,W]
    reports=[];last=None;last_key=None;all_optimal=True;reference=measure(p,initial)
    for stage_id,objective in enumerate(stages):
        model.Minimize(objective)
        if model.Validate():raise ObjectiveHold('CP_MODEL_VALIDATION:'+model.Validate())
        solver=cp_model.CpSolver();q=solver.parameters
        q.num_search_workers=1;q.random_seed=seed;q.search_branching=cp_model.FIXED_SEARCH
        q.cp_model_presolve=False;q.cp_model_probing_level=0;q.linearization_level=0;q.use_lns=False
        q.use_sat_inprocessing=False;q.symmetry_level=0;q.use_rins_lns=False;q.use_feasibility_pump=False
        q.restart_algorithms.append(sat_parameters_pb2.SatParameters.NO_RESTART)
        q.max_number_of_conflicts=config['completion']['max_conflicts_per_internal_solve']
        q.absolute_gap_limit=0;q.relative_gap_limit=0
        class Solutions(cp_model.CpSolverSolutionCallback):
            def __init__(self):super().__init__();self.count=0
            def on_solution_callback(self):
                self.count+=1
                if self.count>=config['completion']['max_improving_solutions']:self.StopSearch()
        cb=Solutions();status=solver.Solve(model,cb)
        info={'stage':stage_id,'status':solver.StatusName(status),'solutions':cb.count,
              'conflicts':solver.NumConflicts(),'branches':solver.NumBranches(),
              'solver_wall_s':solver.WallTime(),
              'best_bound_float_auxiliary':solver.BestObjectiveBound(),
              'work_budget_scope':'per stage diagnostic only; no formal main budget'}
        reports.append(info)
        if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            all_optimal=False
            if status==cp_model.MODEL_INVALID:raise ObjectiveHold('CP_MODEL_INVALID')
            break
        candidate=Metrics(F(solver.Value(D),units.scale_per_m*1000),F(solver.Value(W),60))
        info['candidate_metrics']=record(candidate,reference)
        candidate_key=metric_key(candidate,reference)
        better=last is None or candidate_key<last_key
        if better:last=solver;last_key=candidate_key
        info['retained_by_common_Idual_rule']=better
        value=solver.Value(objective);info['objective_exact_integer']=value
        if status!=cp_model.OPTIMAL:all_optimal=False;break
        model.Add(objective==value)
    if last is None:raise ObjectiveHold('NO_CP_PLAN; '+str(reports))
    selected={};times={}
    for s in range(S):
        if last.Value(used[s]):
            r=next(r for r in range(len(routes)) if last.Value(x[s,r]))
            k=(p.vehicles[s//2].vehicle_id,s%2+1)
            selected[k]=tuple(p.od.ids[i] for i in routes[r])
            times[k]=(last.Value(ready[s]),last.Value(starts[s]),last.Value(returns[s]))
    plan=schedule(p,selected,'C',{'condition_id':'C_Idual','objective_version':'objective-alignment-20261122-v1'})
    require_valid(p,plan);m=measure(p,plan)
    qv=last.Value(D);lv=last.Value(W)
    if m.D!=F(qv,units.scale_per_m*1000) or m.W!=F(lv,60):
        raise ObjectiveHold('CP_EXACT_DW_NOT_EQUAL_COMMON_EVALUATOR')
    if any(times[t.vehicle_id,t.trip_no]!=(t.ready_s,t.load_start_s,t.return_s) for t in plan.trips):
        raise ObjectiveHold('CP_TIMES_NOT_EQUAL_COMMON_SCHEDULER')
    report={'status':'PASS_EXACT_REPRESENTATION','stages':reports,'all_tie_stages_optimal':all_optimal,
        'CP_q':qv,'CP_wait_seconds':lv,'q0':units.q0,'l0':units.l0,
        'scale_per_m':units.scale_per_m,'alpha':units.alpha,'beta':units.beta,
        'mode':units.mode,'objective_numerator':units.target(qv,lv),
        'integer_activity_bound':units.objective_bound,'int64_guard':'conservative 2**62-1',
        'CP_D_exact':str(F(qv,units.scale_per_m*1000)),'CP_W_exact':str(F(lv,60)),
        'evaluated':record(m,measure(p,initial)),
        'proof_scope':'finite supplied route pool and common deterministic rest rule only',
        'full_VRP_optimality':'NOT_CLAIMED','physical_template_sha256':TEMPLATE_SHA256}
    return plan,report
