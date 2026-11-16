"""New finite-work adapters; legacy timed implementations remain unchanged."""
import math
from dataclasses import replace
from .work import CheckBudget, key, verified
from kmd_toc.pipeline.completion import route_distance, route_duration, assemble, greedy_assignment

def solve_completion(p,routes,method,config,ledger,seed,settings=None):
    primary='D';other_limit=None
    from ortools.sat.python import cp_model
    from ortools.sat import sat_parameters_pb2
    routes=sorted(set(tuple(r) for r in routes if r));V=len(p.vehicles);S=2*V
    if any(len(r)>60 or len(set(r))!=len(r) for r in routes):raise ValueError('INVALID_COMPLETION_ROUTE')
    model=cp_model.CpModel();x={};used=[];starts=[];returns=[];intervals=[];wait=[]
    costs=[int(round(route_distance(p,r)*10)) for r in routes];dur=[route_duration(p,r) for r in routes]
    for s in range(S):
        active=model.NewBoolVar(f'used{s}');used.append(active)
        for r in range(len(routes)):x[s,r]=model.NewBoolVar(f'x{s}_{r}')
        model.Add(sum(x[s,r] for r in range(len(routes)))==active)
        start=model.NewIntVar(28800,70200,f'start{s}');ret=model.NewIntVar(28800,72000,f'return{s}');starts.append(start);returns.append(ret)
        model.Add(ret==start+1800*active+sum(dur[r]*x[s,r] for r in range(len(routes))))
        interval=model.NewOptionalFixedSizeIntervalVar(start,1800,active,f'load{s}');intervals.append(interval)
        w=model.NewIntVar(0,43200,f'wait{s}');wait.append(w)
        if s%2==0:
            ready=p.vehicles[s//2].first_ready_s;model.Add(start>=ready);model.Add(w==start-ready).OnlyEnforceIf(active)
        else:
            model.Add(active<=used[s-1]);model.Add(start>=returns[s-1]).OnlyEnforceIf(active);model.Add(w==start-returns[s-1]).OnlyEnforceIf(active)
        model.Add(w==0).OnlyEnforceIf(active.Not())
    patterns=set()
    for j in range(1,len(p.stops)+1):
        cover=tuple(r for r,route in enumerate(routes) if j in route)
        if not cover:raise ValueError('COMPLETION_MISSING_CUSTOMER')
        if cover not in patterns:model.Add(sum(x[s,r] for s in range(S) for r in cover)==1);patterns.add(cover)
    model.AddCumulative(intervals,[1]*S,len(p.berths))
    D=sum(costs[r]*x[s,r] for s in range(S) for r in range(len(routes)));W=sum(wait)
    if other_limit is not None:
        model.Add(W<=math.floor(other_limit*60+1e-7)) if primary=='D' else model.Add(D<=math.floor(other_limit*10000+1e-7))
    # Exact lexicographic tie breaking in integer objective units, not a D/W weighted tradeoff.
    model.Minimize(D*(43200*S+1)+W if primary=='D' else W*(max(costs,default=0)*S+1)+D)
    # A hint is just a hint; it is never returned as success without final validation.
    try:
        hint=greedy_assignment(p,routes) if len(routes)<=S else []
        rid={r:i for i,r in enumerate(routes)}
        for item in hint:
            s=2*item['v']+item['trip_no']-1;model.AddHint(x[s,rid[item['route']]],1);model.AddHint(starts[s],item['start_s'])
    except ValueError:pass
    solver=cp_model.CpSolver();q=solver.parameters
    q.num_search_workers=1;q.random_seed=seed
    q.search_branching=cp_model.FIXED_SEARCH;q.cp_model_presolve=False
    q.cp_model_probing_level=0;q.linearization_level=0;q.use_lns=False
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
    monitor=Solutions()
    ledger.emit('CP_start',variables=len(model.Proto().variables),routes=len(routes),parameters=str(q))
    status=solver.Solve(model,monitor)
    ledger.count('CP_calls');ledger.count('CP_conflicts',solver.NumConflicts())
    ledger.count('CP_branches',solver.NumBranches());ledger.count('CP_solutions',monitor.count)
    stopped='WORK_BUDGET_REACHED' if monitor.reached or status in (cp_model.UNKNOWN,cp_model.FEASIBLE) else 'SEARCH_EXHAUSTED'
    ledger.emit('CP_end',status=solver.StatusName(status),algorithm_termination=stopped,
                improving_solutions=monitor.count,conflicts=solver.NumConflicts(),branches=solver.NumBranches(),
                objective=solver.ObjectiveValue() if status in (cp_model.FEASIBLE,cp_model.OPTIMAL) else None,
                bound=solver.BestObjectiveBound(),proof_scope='supplied route pool and integer D resolution only; zero gap parameters')
    if status not in [cp_model.FEASIBLE,cp_model.OPTIMAL]:raise ValueError('CP_COMPLETION_'+solver.StatusName(status))
    items=[]
    for s in range(S):
        if solver.Value(used[s]):
            r=next(r for r in range(len(routes)) if solver.Value(x[s,r]));items.append({'v':s//2,'trip_no':s%2+1,'route':routes[r],'start_s':solver.Value(starts[s])})
    info={**(settings or {}),'completion':'shared_CP_SAT_route_pool_physical_vehicles_and_optional_cumulative_loading',
          'primary':primary,'other_limit':other_limit,'pool_routes':len(routes),'CP_status':solver.StatusName(status),
          'scope':'finite_supplied_route_pool_only','seed':seed,'threads':1,'CP_objective_bound':solver.BestObjectiveBound(),
          'termination_rule':'finite integer model; no restart; per-internal-SAT conflict budget and improving-solution callback',
          'distance_objective_resolution_m':0.1,'lexicographic_tie_break':True}
    return assemble(p,items,method,info)


def complete(p,routes,method,config,ledger,seed,settings=None,incumbent=None):
    settings=settings or {};best=None;source=None
    if incumbent is None:
        try:incumbent=assemble(p,greedy_assignment(p,routes),method,{'candidate_source':'shared_greedy'})
        except (ValueError,IndexError) as e:ledger.emit('greedy_rejected',error=str(e))
    if verified(p,incumbent,ledger):best=incumbent;source='verified_incumbent'
    try:
        candidate=solve_completion(p,routes,method,config,ledger,seed,settings)
        if verified(p,candidate,ledger) and (best is None or key(candidate)<=key(best)):
            best=candidate;source='CP_candidate'
    except ValueError as e:ledger.emit('CP_no_candidate',error=str(e))
    if best is None:raise ValueError('NO_VERIFIED_COMMON_COMPLETION')
    return replace(best,method_settings={**best.method_settings,**settings,'completion_selected_source':source,
        'completion_input_routes':[list(r) for r in routes],'termination_mode':'finite_work'})


def routing_pool(p,initial,config,ledger,seed):
    from ortools.constraint_solver import pywrapcp,routing_enums_pb2
    n=len(p.stops)+1;V=2*len(p.vehicles)
    manager=pywrapcp.RoutingIndexManager(n,V,0);routing=pywrapcp.RoutingModel(manager)
    distance=routing.RegisterTransitCallback(lambda a,b:int(round(float(p.od.distance_m[manager.IndexToNode(a),manager.IndexToNode(b)])*10)))
    routing.SetArcCostEvaluatorOfAllVehicles(distance)
    demand=routing.RegisterUnaryTransitCallback(lambda a:0 if manager.IndexToNode(a)==0 else 1)
    routing.AddDimensionWithVehicleCapacity(demand,0,[60]*V,True,'Capacity')
    params=pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.ClearField('time_limit');params.ClearField('lns_time_limit')
    params.use_cp_sat=2;params.use_generalized_cp_sat=False;params.fallback_to_cp_sat_size_threshold=0
    params.sat_parameters.num_search_workers=1;params.sat_parameters.random_seed=seed
    routing.solver().ReSeed(seed)
    counter=CheckBudget(max(config['C']['minimum_search_limit_checks'],config['C']['search_limit_checks_per_stop']*len(p.stops)))
    monitor=routing.solver().CustomLimit(counter)
    routing.AddSearchMonitor(monitor)
    # Close with the same parameters BEFORE ReadAssignment, avoiding default LNS timers.
    routing.CloseModelWithParameters(params)
    seedroutes=[list(r) for r in initial]+[[] for _ in range(V-len(initial))]
    assignment=routing.ReadAssignmentFromRoutes(seedroutes,True)
    ledger.emit('Routing_start',limit_checks=counter.limit,parameters=str(params))
    solution=routing.SolveFromAssignmentWithParameters(assignment,params) if assignment else routing.SolveWithParameters(params)
    generated=[]
    if solution is not None:
        for v in range(V):
            idx=routing.Start(v);route=[]
            while not routing.IsEnd(idx):
                j=manager.IndexToNode(idx)
                if j:route.append(j)
                idx=solution.Value(routing.NextVar(idx))
            if route:generated.append(tuple(route))
    ledger.count('Routing_limit_checks',counter.checks)
    ledger.count('Routing_limit_acknowledgements',counter.acknowledgements)
    ledger.emit('Routing_end',algorithm_termination='WORK_BUDGET_REACHED' if counter.reached else 'SEARCH_EXHAUSTED',
        limit=counter.limit,checks=counter.checks,acknowledgements=counter.acknowledgements,
        native_status=routing.status(),generated_routes=len(generated),failures=routing.solver().Failures(),
        branches=routing.solver().Branches(),solutions=routing.solver().Solutions(),
        proof='none; incumbent preserved; no-plan is not an infeasibility proof')
    return sorted(set([*initial,*generated])),{'OR_Routing_generated_routes':len(generated),'OR_Routing_seed':'directed_CW',
        'routing_work_checks':counter.checks,'routing_check_limit':counter.limit,
        'full_time_berth_constraints_applied_in':'CP_SAT_completion_not_Routing_stage'}
