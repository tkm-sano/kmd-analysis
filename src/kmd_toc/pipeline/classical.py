"""Directed CW extension and OR-Tools routing; external code stays unmodified."""
import math
from .completion import route_distance, complete_routes


def directed_cw(p):
    from verypy.classic_heuristics.parallel_savings import clarke_wright_savings_function
    d=p.od.distance_m;n=len(p.stops)
    savings=clarke_wright_savings_function(d)
    savings.extend((float(d[j,0]+d[0,i]-d[j,i]),-float(d[j,i]),j,i) for _,__,i,j in list(savings))
    savings.sort(reverse=True)
    routes={i:[i] for i in range(1,n+1)};owner={i:i for i in range(1,n+1)}
    for saving,_,i,j in savings:
        a,b=owner[i],owner[j]
        if a==b or routes[a][-1]!=i or routes[b][0]!=j or len(routes[a])+len(routes[b])>60:continue
        routes[a].extend(routes[b])
        for k in routes[b]:owner[k]=a
        del routes[b]
    result=[tuple(r) for r in routes.values()];initial_count=len(result);eliminated=0
    while len(result)>2*len(p.vehicles):
        k=min(range(len(result)),key=lambda k:(len(result[k]),result[k]));removed=result.pop(k)
        targets=[list(r) for r in result]
        for customer in removed:
            candidates=[]
            for r,route in enumerate(targets):
                if len(route)>=60:continue
                nodes=[0,*route,0]
                for at,(a,b) in enumerate(zip(nodes,nodes[1:])):
                    candidates.append((float(d[a,customer]+d[customer,b]-d[a,b]),r,at))
            if not candidates:raise ValueError('CW_ROUTE_COUNT_COMPLETION_FAILED')
            _,r,at=min(candidates);targets[r].insert(at,customer)
        result=[tuple(r) for r in targets];eliminated+=1
    return result,{'algorithm':'VeRyPy_savings_order_with_explicit_directed_tail_to_head_CW_extension',
                   'upstream_symmetric_core_used_unmodified':False,'symmetric_OD_substitution':False,
                   'initial_CW_routes':initial_count,'classical_route_eliminations':eliminated,
                   'post_completion_route_count':len(result),'route_generation_D_km':sum(route_distance(p,r) for r in result)/1000}


def routing_pool(p,initial,seconds=60,seed=20261112):
    from ortools.constraint_solver import pywrapcp,routing_enums_pb2
    n=len(p.stops)+1;V=2*len(p.vehicles);manager=pywrapcp.RoutingIndexManager(n,V,0);routing=pywrapcp.RoutingModel(manager)
    def cost(a,b):return int(round(float(p.od.distance_m[manager.IndexToNode(a),manager.IndexToNode(b)])*10))
    distance=routing.RegisterTransitCallback(cost);routing.SetArcCostEvaluatorOfAllVehicles(distance)
    demand=routing.RegisterUnaryTransitCallback(lambda a:0 if manager.IndexToNode(a)==0 else 1)
    routing.AddDimensionWithVehicleCapacity(demand,0,[60]*V,True,'Capacity')
    params=pywrapcp.DefaultRoutingSearchParameters();params.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds=seconds;params.sat_parameters.num_search_workers=1;params.sat_parameters.random_seed=seed;routing.solver().ReSeed(seed)
    seedroutes=[list(r) for r in initial]+[[] for _ in range(V-len(initial))]
    assignment=routing.ReadAssignmentFromRoutes(seedroutes,True)
    solution=routing.SolveFromAssignmentWithParameters(assignment,params) if assignment else routing.SolveWithParameters(params)
    if solution is None:raise ValueError('OR_ROUTING_NO_CAPACITY_PLAN')
    generated=[]
    for v in range(V):
        idx=routing.Start(v);route=[]
        while not routing.IsEnd(idx):
            j=manager.IndexToNode(idx)
            if j:route.append(j)
            idx=solution.Value(routing.NextVar(idx))
        if route:generated.append(tuple(route))
    return sorted(set([*initial,*generated])),{'OR_Routing_objective_decimeter':solution.ObjectiveValue(),
                    'OR_Routing_generated_routes':len(generated),'OR_Routing_seed':'directed_CW',
                    'full_time_berth_constraints_applied_in':'CP_SAT_completion_not_Routing_stage'}


def create_classical(p,method,primary='D',other_limit=None,mark=None):
    routes,info=directed_cw(p)
    if mark:mark('initial_CW_end')
    if method=='C':
        routes,extra=routing_pool(p,routes);info.update(extra)
        if mark:mark('OR_Routing_improvement_end')
    plan=complete_routes(p,routes,method,primary,other_limit,settings=info)
    if mark:mark('physical_vehicle_berth_completion_end')
    return plan
