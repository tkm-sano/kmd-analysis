"""Route-pool CP completion with FCFS inside the model, not a final repair.

For identical 1800-second loading on B identically available berths, the j-th
ready-ordered start is max(ready[j], start[j-B]+1800). Active trips precede
inactive sentinels. Reified ready ranks also include vehicle-ID/trip-ID ties.
The independent event replay checks every returned solution.
"""
from dataclasses import replace

from kmd_toc.pipeline.completion import route_distance, route_duration, greedy_assignment
from kmd_toc.termination_v1.work import key
from .scheduler import POLICY_ID, schedule, reschedule
from .validation import require_fcfs


class FCFSModelConsistencyError(RuntimeError):
    """A model/scheduler mismatch is a defect, never an ordinary no-solution."""


class FCFSNoSolution(ValueError):
    """A valid model did not supply a solution under the unchanged work budget."""


def solve_completion(p, routes, method, config, ledger, seed, settings=None):
    from .policy import require_frozen
    require_frozen()
    p.validate()
    from ortools.sat.python import cp_model
    from ortools.sat import sat_parameters_pb2
    routes = sorted(set(tuple(r) for r in routes if r))
    V = len(p.vehicles); S = 2*V; B = len(p.berths)
    if not routes or not B:
        raise ValueError('FCFS_EMPTY_ROUTE_POOL_OR_BERTHS')
    if len({(b.opening_s, b.closing_s, b.loading_s, b.preparation_s) for b in p.berths}) != 1:
        raise ValueError('FCFS_CP_REQUIRES_COMMON_BERTH_AVAILABILITY')
    opening = p.berths[0].opening_s; closing = p.berths[0].closing_s
    if p.berths[0].loading_s != 1800 or p.berths[0].preparation_s != 0:
        raise ValueError('FCFS_V1_LOADING_AND_PREPARATION')
    demands = {i: s.demand for i, s in enumerate(p.stops, 1)}
    if any(len(set(r)) != len(r) or any(i not in demands for i in r) or
           sum(demands[i] for i in r) > 60 for r in routes):
        raise ValueError('INVALID_COMPLETION_ROUTE')
    model = cp_model.CpModel()
    costs = [int(round(route_distance(p, r)*10)) for r in routes]
    dur = [route_duration(p, r) for r in routes]
    sentinel = closing + 1; horizon = sentinel + S*1800
    used=[];starts=[];returns=[];ready=[];sort_ready=[];wait=[];x={}
    for s in range(S):
        active=model.NewBoolVar(f'used{s}');used.append(active)
        for r in range(len(routes)):x[s,r]=model.NewBoolVar(f'x{s}_{r}')
        model.Add(sum(x[s,r] for r in range(len(routes)))==active)
        start=model.NewIntVar(opening,horizon,f'start{s}');starts.append(start)
        ret=model.NewIntVar(0,closing,f'return{s}');returns.append(ret)
        rd=model.NewIntVar(0,closing,f'ready{s}');ready.append(rd)
        model.Add(ret==start+1800+sum(dur[r]*x[s,r] for r in range(len(routes)))).OnlyEnforceIf(active)
        model.Add(ret==0).OnlyEnforceIf(active.Not())
        if s%2==0:model.Add(rd==p.vehicles[s//2].first_ready_s).OnlyEnforceIf(active)
        else:
            model.Add(active<=used[s-1]);model.Add(rd==returns[s-1]).OnlyEnforceIf(active)
        model.Add(rd==0).OnlyEnforceIf(active.Not())
        sorting=model.NewIntVar(0,sentinel,f'sort_ready{s}');sort_ready.append(sorting)
        model.Add(sorting==rd).OnlyEnforceIf(active)
        model.Add(sorting==sentinel).OnlyEnforceIf(active.Not())
        w=model.NewIntVar(0,closing-opening,f'wait{s}');wait.append(w)
        model.Add(w==start-rd).OnlyEnforceIf(active);model.Add(w==0).OnlyEnforceIf(active.Not())
    for customer in range(1,len(p.stops)+1):
        cover=[x[s,r] for s in range(S) for r,route in enumerate(routes) if customer in route]
        if not cover:raise ValueError('COMPLETION_MISSING_CUSTOMER')
        model.Add(sum(cover)==1)
    keys=sorted((p.vehicles[s//2].vehicle_id,s%2+1,s) for s in range(S))
    tie={s:i for i,(_,_,s) in enumerate(keys)}
    priority=[sort_ready[s]*(S+1)+tie[s] for s in range(S)]
    predecessors=[[] for _ in range(S)]
    for s in range(S):
        for t in range(s+1,S):
            before=model.NewBoolVar(f'before_{s}_{t}')
            model.Add(priority[s]<priority[t]).OnlyEnforceIf(before)
            model.Add(priority[s]>priority[t]).OnlyEnforceIf(before.Not())
            predecessors[t].append(before);predecessors[s].append(before.Not())
    rank=[model.NewIntVar(0,S-1,f'rank{s}') for s in range(S)]
    order=[model.NewIntVar(0,S-1,f'order{j}') for j in range(S)]
    for s in range(S):model.Add(rank[s]==sum(predecessors[s]))
    model.AddInverse(rank,order)
    ordered_start=[]
    for j in range(S):
        rd=model.NewIntVar(0,sentinel,f'ordered_ready{j}')
        model.AddElement(order[j],sort_ready,rd)
        st=model.NewIntVar(opening,horizon,f'ordered_start{j}');ordered_start.append(st)
        model.AddMaxEquality(st,[rd,opening if j<B else ordered_start[j-B]+1800])
    for s in range(S):model.AddElement(rank[s],ordered_start,starts[s])
    D=sum(costs[r]*x[s,r] for s in range(S) for r in range(len(routes)))
    W=sum(wait)
    # Same pre-existing D-first, W-second integer lexicographic objective.
    model.Minimize(D*(43200*S+1)+W)
    # Decide finite route/slot choices before auxiliary clock/rank domains. This
    # avoids spending the unchanged conflict budget on inactive sentinel times.
    model.AddDecisionStrategy([x[s,r] for r in sorted(range(len(routes)),key=lambda r:(costs[r],routes[r]))
                               for s in range(S)],cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE)
    try:
        raw=greedy_assignment(p,routes) if len(routes)<=S else []
        if raw:
            hint=schedule(p,{(p.vehicles[i['v']].vehicle_id,i['trip_no']):tuple(p.od.ids[j] for j in i['route']) for i in raw},method)
            route_index={r:i for i,r in enumerate(routes)}
            vehicle_index={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
            for t in hint.trips:
                s=2*vehicle_index[t.vehicle_id]+t.trip_no-1
                route=tuple(p.od.ids.index(v.stop_id) for v in t.visits)
                model.AddHint(x[s,route_index[route]],1);model.AddHint(starts[s],t.load_start_s)
    except (ValueError,IndexError):pass
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
            if self.count>=config['completion']['max_improving_solutions']:
                self.reached=True;self.StopSearch()
    callback=Solutions()
    ledger.emit('CP_FCFS_start',operating_policy=POLICY_ID,variables=len(model.Proto().variables),
                routes=len(routes),parameters=str(q))
    status=solver.Solve(model,callback)
    ledger.count('CP_calls');ledger.count('CP_conflicts',solver.NumConflicts())
    ledger.count('CP_branches',solver.NumBranches());ledger.count('CP_solutions',callback.count)
    ledger.emit('CP_FCFS_end',status=solver.StatusName(status),improving_solutions=callback.count,
                conflicts=solver.NumConflicts(),branches=solver.NumBranches(),
                algorithm_termination='WORK_BUDGET_REACHED' if callback.reached or status in (cp_model.UNKNOWN,cp_model.FEASIBLE) else 'SEARCH_EXHAUSTED')
    if status == cp_model.MODEL_INVALID:
        raise FCFSModelConsistencyError('FCFS_CP_MODEL_INVALID:'+model.Validate())
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        raise FCFSNoSolution('CP_FCFS_COMPLETION_'+solver.StatusName(status))
    selected={}; cp_times={}
    for s in range(S):
        if solver.Value(used[s]):
            r=next(r for r in range(len(routes)) if solver.Value(x[s,r]))
            trip_key=(p.vehicles[s//2].vehicle_id,s%2+1)
            selected[trip_key]=tuple(p.od.ids[i] for i in routes[r])
            cp_times[trip_key]=(solver.Value(ready[s]),solver.Value(starts[s]),solver.Value(returns[s]))
    plan=schedule(p,selected,method,{**(settings or {}),'completion':'CP_SAT_FCFS_inside_model',
        'operating_policy':POLICY_ID,'fcfs_solver_seed':seed,'pool_routes':len(routes),
        'primary':'D','lexicographic_tie_break':True,'distance_objective_resolution_m':0.1,
        'CP_status':solver.StatusName(status),'CP_objective':solver.ObjectiveValue(),
        'CP_wait_s':solver.Value(W),'CP_objective_bound':solver.BestObjectiveBound(),
        'scope':'finite_supplied_route_pool_FCFS_constraints_not_global_VRP_certificate'})
    for t in plan.trips:
        if cp_times[t.vehicle_id,t.trip_no] != (t.ready_s,t.load_start_s,t.return_s):
            raise FCFSModelConsistencyError('FCFS_CP_MODEL_SCHEDULER_DISAGREE')
    if sum(t.waiting_s for t in plan.trips)!=solver.Value(W):
        raise FCFSModelConsistencyError('FCFS_CP_OBJECTIVE_W_DISAGREES')
    return plan


def complete(p,routes,method,config,ledger,seed,settings=None,incumbent=None):
    """Every incumbent and CP candidate is FCFS BEFORE any D/W comparison."""
    best=None;source=None
    try:
        if incumbent is None:
            raw=greedy_assignment(p,routes)
            assigned={(p.vehicles[i['v']].vehicle_id,i['trip_no']):tuple(p.od.ids[j] for j in i['route']) for i in raw}
            candidate=schedule(p,assigned,method,{'candidate_source':'shared_greedy_FCFS'})
        else:
            candidate=reschedule(p,incumbent,method=method)
        require_fcfs(p,candidate);best=candidate;source='verified_FCFS_incumbent'
    except (ValueError,IndexError) as e:ledger.emit('FCFS_incumbent_rejected',error=str(e))
    try:
        candidate=solve_completion(p,routes,method,config,ledger,seed,settings)
        require_fcfs(p,candidate)
        if best is None or key(candidate)<=key(best):best=candidate;source='CP_FCFS_candidate'
    except FCFSNoSolution as e:ledger.emit('CP_FCFS_no_candidate',error=str(e))
    if best is None:raise ValueError('NO_VERIFIED_FCFS_COMPLETION')
    require_fcfs(p,best)
    return replace(best,method_settings={**best.method_settings,**(settings or {}),
        'operating_policy':POLICY_ID,'fcfs_solver_seed':seed,'completion_selected_source':source,
        'completion_input_routes':[list(r) for r in routes],'termination_mode':'finite_work'})
