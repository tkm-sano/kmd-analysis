"""Independent opt-in diagnostic adapters; no classical result enters D."""
from dataclasses import asdict,replace
from fractions import Fraction
from pathlib import Path
import json
import time

from .plans import start, dump, sha, exact_metrics
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.duty_break_v1.cp import complete
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.duty_break_v1.local import metrics
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
from kmd_toc.termination_v1.work import Ledger,CheckBudget,key
from kmd_toc.d_final_selection_v1.ranking import Candidate,Metrics,select,metric_record


def slot_routes(p,plan):
    index={s:i for i,s in enumerate(p.od.ids)}
    trips={(t.vehicle_id,t.trip_no):tuple(index[v.stop_id] for v in t.visits) for t in plan.trips}
    return [trips.get((v.vehicle_id,k),()) for v in p.vehicles for k in (1,2)]


def routing_from_initial(p,plan,config,seed):
    """Same Routing formulation/budget; verify slot-aware initial assignment."""
    from ortools.constraint_solver import pywrapcp,routing_enums_pb2
    initial=slot_routes(p,plan);size=len(initial)
    manager=pywrapcp.RoutingIndexManager(len(p.stops)+1,size,0);routing=pywrapcp.RoutingModel(manager)
    callback=routing.RegisterTransitCallback(lambda a,b:int(round(float(p.od.distance_m[manager.IndexToNode(a),manager.IndexToNode(b)])*10)))
    routing.SetArcCostEvaluatorOfAllVehicles(callback)
    demand=routing.RegisterUnaryTransitCallback(lambda a:0 if manager.IndexToNode(a)==0 else 1)
    routing.AddDimensionWithVehicleCapacity(demand,0,[60]*size,True,'Capacity')
    q=pywrapcp.DefaultRoutingSearchParameters()
    q.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    q.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    q.ClearField('time_limit');q.ClearField('lns_time_limit');q.use_cp_sat=2
    q.use_generalized_cp_sat=False;q.fallback_to_cp_sat_size_threshold=0
    q.sat_parameters.num_search_workers=1;q.sat_parameters.random_seed=seed;routing.solver().ReSeed(seed)
    budget=CheckBudget(max(config['C']['minimum_search_limit_checks'],config['C']['search_limit_checks_per_stop']*len(p.stops)))
    routing.AddSearchMonitor(routing.solver().CustomLimit(budget));routing.CloseModelWithParameters(q)
    assignment=routing.ReadAssignmentFromRoutes([list(r) for r in initial],True)
    if assignment is None:raise ValueError('HOLD_ROUTING_CANNOT_READ_SHARED_INITIAL')
    def unpack(solution):
        routes=[]
        for v in range(size):
            at=routing.Start(v);r=[]
            while not routing.IsEnd(at):
                node=manager.IndexToNode(at)
                if node:r.append(node)
                at=solution.Value(routing.NextVar(at))
            routes.append(tuple(r))
        return routes
    projected=unpack(assignment)
    if projected!=initial:raise ValueError('ROUTING_INITIAL_SLOT_OR_VISIT_ORDER_CHANGED')
    routes={(p.vehicles[s//2].vehicle_id,s%2+1):tuple(p.od.ids[i] for i in r)
            for s,r in enumerate(projected) if r}
    reconstructed=schedule(p,routes,'C')
    same=digest_payload(physical_payload(reconstructed))==digest_payload(physical_payload(plan))
    if not same:raise ValueError('ROUTING_PROJECTION_RECONSTRUCTION_CHANGED_PHYSICAL_INITIAL')
    receipt={'initial_slot_routes':[list(r) for r in initial],
        'loaded_slot_routes':[list(r) for r in projected],
        'reconstructed_physical_hash':digest_payload(physical_payload(reconstructed)),
        'full_reconstructed_plan_equal':same,'preserved_outer_incumbent_hash':digest_payload(physical_payload(plan)),
        'Routing_internal_state_scope':'ordered routes and virtual-to-physical slot mapping only',
        'Routing_internal_schedule_variables':'ABSENT: FCFS/break/berth times live in common physical completion',
        'full_native_internal_schedule_identity':'HOLD_NOT_REPRESENTED',
        'new_CW_generation':False}
    solution=routing.SolveFromAssignmentWithParameters(assignment,q)
    generated=unpack(solution) if solution else []
    pool=sorted(set(r for r in [*initial,*generated] if r))
    receipt.update(native_status=routing.status(),checks=budget.checks,check_limit=budget.limit,
                   candidate_route_count=len(pool),native_solution_found=solution is not None)
    return pool,receipt


def classical(p,initial,output,*,config,seed):
    from .policy import require_policy
    require_policy()
    out=Path(output);out.mkdir(parents=True,exist_ok=False);t=time.perf_counter()
    plan=start(p,initial,'C',out)
    if plan is None:return {'status':'COMMON_INITIAL_UNAVAILABLE','method':'C'}
    pool,bridge=routing_from_initial(p,plan,config,seed);dump(out/'ROUTING_BRIDGE.json',bridge)
    ledger=Ledger(out)
    result=complete(p,pool,'C',config,ledger,seed,{'purpose':'shared_initial_diagnostic_C'},incumbent=plan)
    initial.checked_plan(p);require_valid(p,result)
    record={'status':'COMPLETE_COMPONENT_VALIDATION','method':'C','metrics':exact_metrics(p,result),
            'initial_plan_sha256':initial.manifest['plan_sha256'],'wall_s':time.perf_counter()-t,
            'main_experiment':False,'search_scope':'Routing then finite route pool duty/FCFS completion',
            'full_Routing_native_schedule_equivalence':'HOLD'}
    dump(out/'plan.json',asdict(result));dump(out/'RESULT.json',record)
    return record


def relaxed_master(p,pool):
    """Necessary-condition route partition relaxation, not full physical RMP."""
    import numpy as np
    from scipy.optimize import linprog
    from kmd_toc.pipeline.completion import route_distance
    routes=sorted(set(pool));a=np.array([[float(i in r) for r in routes] for i in range(1,len(p.stops)+1)])
    costs=np.array([route_distance(p,r)/1000 for r in routes])
    lp=linprog(costs,A_eq=a,b_eq=np.ones(len(p.stops)),A_ub=np.ones((1,len(routes))),
               b_ub=[2*len(p.vehicles)],bounds=(0,None),method='highs',options={'threads':1})
    if not lp.success:raise ValueError('ROUTE_RELAXATION_FAILED:'+lp.message)
    dual=lp.eqlin.marginals;fleet=float(lp.ineqlin.marginals[0])
    return {'objective_km':float(lp.fun),'customer_duals_km':dual.tolist(),'fleet_dual_km':fleet,
            'scope':'route-cover equality and <=2V trips only; FCFS/W/duty absent from relaxation',
            'not_full_physical_pricing':True}


def hybrid(p,initial,output,*,config,seed,proposal_source,rounds=1):
    """Measured route candidates -> true RC of relaxation -> common completion.

    proposal_source receives ONLY this method's incumbent and own LP duals.
    A test source must declare fixture provenance; it never proves quantum use.
    """
    from .policy import require_policy
    require_policy()
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    incumbent=start(p,initial,'D',out)
    if incumbent is None:return {'status':'COMMON_INITIAL_UNAVAILABLE','method':'D'}
    pool={r for r in slot_routes(p,incumbent) if r};origin=set(pool);trace=[];measured=set()
    if proposal_source is None:raise ValueError('HOLD_QUANTUM_COLUMN_PROVIDER_REQUIRED_NO_CLASSICAL_REPLACEMENT')
    for round_id in range(rounds):
        master=relaxed_master(p,pool)
        proposals=proposal_source(p,incumbent,dict(master),out/f'pricing_{round_id:03d}')
        added=[];considered=[]
        from kmd_toc.pipeline.completion import route_distance
        for item in proposals:
            if item.get('provenance_role') not in ('measured_quantum','explicit_test_double'):
                raise ValueError('UNDECLARED_QUANTUM_CANDIDATE_PROVENANCE')
            route=tuple(item['route'])
            if not route or len(route)>60 or len(set(route))!=len(route):raise ValueError('INVALID_COLUMN')
            if any(type(i) is not int or not 1<=i<=len(p.stops) for i in route):raise ValueError('COLUMN_CUSTOMER_SCOPE')
            rc=route_distance(p,route)/1000-sum(master['customer_duals_km'][i-1] for i in route)-master['fleet_dual_km']
            considered.append({**item,'reduced_cost_km':rc})
            if item['provenance_role']=='measured_quantum':measured.add(route)
            if rc < -1e-7 and route not in pool:pool.add(route);added.append(route)
        # Keep quantum assignment/order. Do not bypass the existing D pin guard
        # by calling a C optimizer and relabeling its result as quantum.
        from kmd_toc.duty_break_v1.models import load_plan
        for item in proposals:
            if not item.get('candidate_plan_path'):continue
            path=Path(item['candidate_plan_path'])
            if sha(path)!=item['candidate_plan_sha256']:raise ValueError('QUANTUM_PLAN_PROVENANCE_HASH')
            completed=load_plan(path);require_valid(p,completed)
            if completed.method_id!='D':raise ValueError('QUANTUM_CANDIDATE_METHOD')
            old=exact_metrics(p,incumbent);new=exact_metrics(p,completed)
            nd,nw,od,ow=(Fraction(new['D_exact']),Fraction(new['W_exact']),Fraction(old['D_exact']),Fraction(old['W_exact']))
            if nd<=od and nw<=ow and (nd<od or nw<ow):
                incumbent=completed
        trace.append({'round':round_id,'master':master,'considered':considered,'negative_new_columns':[list(r) for r in added],
                      'stop_reason':None if added else 'NO_NEGATIVE_SAMPLED_COLUMN_NOT_CERTIFICATE'})
        if not added:break
    initial.checked_plan(p)
    final_routes=set(slot_routes(p,incumbent))
    record={'method':'D','status':'COMPLETE_COMPONENT_VALIDATION','metrics':exact_metrics(p,incumbent),
        'initial_plan_sha256':initial.manifest['plan_sha256'],'trace':trace,
        'quantum_new_routes_retained':len(final_routes & (measured-origin)),
        'pricing_scope':'relaxed route master only; full physical dual pricing HOLD',
        'final_relaxed_master':relaxed_master(p,pool),
        'full_Huang_or_full_physical_CG':'HOLD_PHYSICAL_INTEGER_MASTER_NOT_CONNECTED','main_experiment':False,
        'C_final_or_A_reference_input':False}
    dump(out/'plan.json',asdict(incumbent));dump(out/'RESULT.json',record)
    return record


def select_four(p,initial,branches,output):
    """New approval: reference pi0 only. No classical final result argument."""
    from .policy import require_policy
    require_policy()
    if set(branches)!=set(range(4)):raise ValueError('FOUR_EXPLICIT_BRANCH_RECORDS_REQUIRED')
    baseline=initial.checked_plan(p);d0,w0=metrics(p,baseline)
    candidates=[Candidate(None,Metrics(d0,w0))];plans={None:baseline};excluded=[];branch_records=[]
    for b,plan in sorted(branches.items()):
        if plan is None:excluded.append({'branch_id':b,'status':'MISSING_OR_FAILED'});continue
        try:
            require_valid(p,plan);d,w=metrics(p,plan)
            if plan.method_id!='D':raise ValueError('NOT_HYBRID_BRANCH')
            candidates.append(Candidate(b,Metrics(d,w)));plans[b]=plan
            branch_records.append({'branch_id':b,'feasible':True,**metric_record(Metrics(d,w),Metrics(d0,w0)),
                                   'runtime_s':None,'runtime_status':'NOT_SUPPLIED_TO_SELECTION_ONLY_API'})
        except ValueError as e:excluded.append({'branch_id':b,'status':'INVALID','reason':str(e)})
    winner,why=select(candidates,Metrics(d0,w0))
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    selected=plans[winner.branch_id]
    if winner.branch_id is None:
        selected=replace(selected,method_id='D',execution_kind='quantum_circuit_simulator')
    dump(out/'plan.json',asdict(selected))
    record={'version':'common-initial-20261122-v1','reference_role':'common_initial_pi0',
        'reference_plan_sha256':initial.manifest['plan_sha256'],'selected_branch_id':winner.branch_id,
        'selection':why,'metrics':metric_record(winner.metrics,Metrics(d0,w0)),
        'branches':branch_records,'excluded':excluded,'old_C_reference_rule_modified':False,'statistical_ratio_zero_baseline':'undefined_not_zero'}
    dump(out/'SELECTION.json',record);return record
