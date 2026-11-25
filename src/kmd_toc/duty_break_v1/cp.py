"""Common finite-route completion: FCFS and break-induced returns inside CP.

Break opportunity domains are unions of start intervals, one for each eligible
service end. A single Boolean per slot adds exactly 3600 seconds to that trip.
This avoids a break-position variable for every route x slot x delivery point.
The common deterministic scheduler determines the first eligible stop, and all
CP times / W are checked against its independently validated final plan.
"""
from dataclasses import replace
from kmd_toc.pipeline.completion import route_distance,greedy_assignment
from .scheduler import schedule,route_data,NoDutySchedule
from .validation import require_valid


class CompletionNotFound(ValueError):
    pass


class CompletionMismatch(RuntimeError):
    pass


def solve_completion(p,routes,method,config,ledger,seed,settings=None,*,pinned_assignments=None):
    if method in ('D','Q') and pinned_assignments is None:
        raise ValueError('QUANTUM_ASSIGNMENT_MUST_BE_EXPLICITLY_PINNED')
    from ortools.sat.python import cp_model
    from ortools.sat import sat_parameters_pb2
    p.validate_duty()
    routes=sorted(set(tuple(r) for r in routes if r));V=len(p.vehicles);S=2*V;B=len(p.berths)
    if not routes or any(not r or len(set(r))!=len(r) or len(r)>60 or
                         any(type(i) is not int or not 1<=i<=len(p.stops) for i in r) for r in routes):
        raise ValueError('DUTY_INVALID_ROUTE_POOL')
    model=cp_model.CpModel();x={};used=[];starts=[];returns=[];ready=[];ordered_ready=[];wait=[];rest=[]
    costs=[int(round(route_distance(p,r)*10)) for r in routes];dur=[];domains=[]
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
    model.Minimize(D*(43200*S+1)+W)
    model.AddDecisionStrategy([x[s,r] for r in sorted(range(len(routes)),key=lambda r:(costs[r],routes[r])) for s in range(S)],
                              cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE)
    # Only valid DUTY schedules may be hints; no old unbroken schedule is a fallback.
    try:
        raw=pinned_assignments
        if raw is None:
            raw={(p.vehicles[i['v']].vehicle_id,i['trip_no']):tuple(i['route']) for i in greedy_assignment(p,routes)}
        hint=schedule(p,{k:tuple(p.od.ids[i] for i in r) for k,r in raw.items()},method)
        rid={r:i for i,r in enumerate(routes)};ids={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
        for t in hint.trips:
            s=2*ids[t.vehicle_id]+t.trip_no-1;r=tuple(p.od.ids.index(v.stop_id) for v in t.visits)
            model.AddHint(x[s,rid[r]],1);model.AddHint(starts[s],t.load_start_s)
    except (NoDutySchedule,ValueError,IndexError):pass
    solver=cp_model.CpSolver();q=solver.parameters
    q.num_search_workers=1;q.random_seed=seed;q.search_branching=cp_model.FIXED_SEARCH
    q.cp_model_presolve=False;q.cp_model_probing_level=0;q.linearization_level=0;q.use_lns=False
    q.use_sat_inprocessing=False;q.symmetry_level=0;q.use_rins_lns=False;q.use_feasibility_pump=False
    q.restart_algorithms.append(sat_parameters_pb2.SatParameters.NO_RESTART)
    q.max_number_of_conflicts=config['completion']['max_conflicts_per_internal_solve']
    q.absolute_gap_limit=0;q.relative_gap_limit=0
    class Solutions(cp_model.CpSolverSolutionCallback):
        def __init__(self):super().__init__();self.count=0;self.reached=False
        def on_solution_callback(self):
            self.count+=1
            if self.count>=config['completion']['max_improving_solutions']:self.reached=True;self.StopSearch()
    cb=Solutions();ledger.emit('DUTY_CP_start',routes=len(routes),variables=len(model.Proto().variables),parameters=str(q))
    status=solver.Solve(model,cb)
    ledger.count('CP_calls');ledger.count('CP_conflicts',solver.NumConflicts());ledger.count('CP_solutions',cb.count)
    ledger.emit('DUTY_CP_end',status=solver.StatusName(status),conflicts=solver.NumConflicts(),
                branches=solver.NumBranches(),solutions=cb.count,
                proof_scope='supplied route pool and common deterministic rest rule only, not global VRP')
    if status==cp_model.MODEL_INVALID:raise CompletionMismatch('DUTY_CP_MODEL_INVALID:'+model.Validate())
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        raise CompletionNotFound('DUTY_CP_'+solver.StatusName(status)+'_NOT_GLOBAL_INFEASIBILITY_PROOF')
    selected={};times={}
    for s in range(S):
        if solver.Value(used[s]):
            r=next(r for r in range(len(routes)) if solver.Value(x[s,r]));key=(p.vehicles[s//2].vehicle_id,s%2+1)
            selected[key]=tuple(p.od.ids[i] for i in routes[r]);times[key]=(solver.Value(ready[s]),solver.Value(starts[s]),solver.Value(returns[s]))
    plan=schedule(p,selected,method,{**(settings or {}),'completion':'DUTY_CP_FCFS_AND_BREAK_INSIDE_MODEL',
                                  'CP_status':solver.StatusName(status),'CP_wait_s':solver.Value(W),
                                  'CP_seed':seed,'scope':'finite_supplied_route_pool',
                                  'pinned_assignments':pinned_assignments is not None})
    if any(times[t.vehicle_id,t.trip_no]!=(t.ready_s,t.load_start_s,t.return_s) for t in plan.trips):
        raise CompletionMismatch('DUTY_CP_SCHEDULER_TIMES_DISAGREE')
    if sum(t.waiting_s for t in plan.trips)!=solver.Value(W):raise CompletionMismatch('DUTY_CP_W_DISAGREES')
    require_valid(p,plan)
    return plan


def complete(p,routes,method,config,ledger,seed,settings=None,*,pinned_assignments=None,incumbent=None):
    if method in ('D','Q') and pinned_assignments is None:
        raise ValueError('QUANTUM_ASSIGNMENT_MUST_BE_EXPLICITLY_PINNED')
    from kmd_toc.termination_v1.work import key
    best=None
    try:
        if incumbent is not None:
            require_valid(p,incumbent)
            if pinned_assignments is not None:
                actual={(t.vehicle_id,t.trip_no):tuple(p.od.ids.index(v.stop_id) for v in t.visits) for t in incumbent.trips}
                if actual!=pinned_assignments:raise ValueError('INCUMBENT_WOULD_CHANGE_PINNED_QUANTUM_ASSIGNMENT')
            best=incumbent
        else:
            assigned=pinned_assignments
            if assigned is None:
                assigned={(p.vehicles[i['v']].vehicle_id,i['trip_no']):tuple(i['route']) for i in greedy_assignment(p,routes)}
            best=schedule(p,{k:tuple(p.od.ids[i] for i in r) for k,r in assigned.items()},method,
                          {**(settings or {}),'completion':'verified_common_DUTY_incumbent'})
    except (ValueError,IndexError) as error:ledger.emit('DUTY_incumbent_rejected',reason=str(error))
    try:
        proposal=solve_completion(p,routes,method,config,ledger,seed,settings,pinned_assignments=pinned_assignments)
        if best is None or key(proposal)<=key(best):best=proposal
    except CompletionNotFound as error:ledger.emit('DUTY_CP_no_candidate',reason=str(error))
    if best is None:raise CompletionNotFound('NO_VERIFIED_DUTY_COMPLETION_FOUND_NOT_GLOBAL_PROOF')
    require_valid(p,best)
    return replace(best,method_settings={**(settings or {}),**best.method_settings,
        'completion_input_routes':[list(r) for r in routes],'termination_mode':'finite_work',
        'completion_work_limits':dict(config['completion'])})
