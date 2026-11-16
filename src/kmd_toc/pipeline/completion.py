"""Common classical route-pool/physical-vehicle/berth completion.

The master optimizes exactly only within supplied routes. It is not a global VRP
certificate. All method-specific use and timing are reported separately.
"""
import math
from collections import defaultdict
from kmd_toc.common.models import Plan, Trip, Visit
from kmd_toc.common.config import load_conditions


def route_distance(p,route):
    nodes=[0,*route,0];return math.fsum(float(p.od.distance_m[a,b]) for a,b in zip(nodes,nodes[1:]))


def route_duration(p,route):
    nodes=[0,*route,0]
    return sum(math.ceil(float(p.od.duration_s[a,b])) for a,b in zip(nodes,nodes[1:]))+120*len(route)


def assemble(p, assignments, method, settings):
    """Assign actual berth IDs by interval coloring; never change supplied starts."""
    berths=sorted(b.berth_id for b in p.berths);free={b:28800 for b in berths};labels={}
    for item in sorted(assignments,key=lambda z:(z['start_s'],z['v'],z['trip_no'])):
        available=[b for b in berths if free[b]<=item['start_s']]
        if not available:raise ValueError('COMPLETION_BERTH_COLORING_FAILED')
        berth=available[0];free[berth]=item['start_s']+1800;labels[item['v'],item['trip_no']]=berth
    trips=[];previous={}
    for item in sorted(assignments,key=lambda z:(z['v'],z['trip_no'])):
        v,k,route,start=item['v'],item['trip_no'],item['route'],item['start_s']
        ready=p.vehicles[v].first_ready_s if k==1 else previous[v]
        clock=start+1800;visits=[];node=0
        for j in route:
            clock+=math.ceil(float(p.od.duration_s[node,j]));visits.append(Visit(p.od.ids[j],clock,clock,clock+120));clock+=120;node=j
        clock+=math.ceil(float(p.od.duration_s[node,0]));previous[v]=clock
        trips.append(Trip(p.vehicles[v].vehicle_id,k,p.depot.depot_id,p.depot.depot_id,tuple(visits),ready,labels[v,k],start,start+1800,start+1800,clock,route_distance(p,route),start-ready))
    return Plan('1.0',p.experiment.scenario_id+'-'+method,method,p.fingerprint,p.od.fingerprint,tuple(trips),settings,
                'quantum_circuit_simulator' if method=='D' else 'classical')


def greedy_assignment(p,routes):
    """Deterministic feasible candidate/hint if constraints permit; no claims of optimality."""
    routes=sorted((tuple(r) for r in routes),key=lambda r:(-route_duration(p,r),r))
    V=len(p.vehicles);free=[28800]*len(p.berths);items=[];returns={}
    for v,route in enumerate(routes[:V]):
        b=min(range(len(free)),key=lambda i:(free[i],i));start=max(p.vehicles[v].first_ready_s,free[b]);free[b]=start+1800
        returns[v]=start+1800+route_duration(p,route);items.append({'v':v,'trip_no':1,'route':route,'start_s':start})
    available=set(returns)
    for route in routes[V:]:
        if not available:raise ValueError('MORE_THAN_TWO_VEHICLE_TRIPS')
        v=min(available,key=lambda i:(returns[i],i));available.remove(v)
        b=min(range(len(free)),key=lambda i:(free[i],i));start=max(returns[v],free[b]);free[b]=start+1800
        items.append({'v':v,'trip_no':2,'route':route,'start_s':start})
    return items


def complete_routes(p,routes,method,primary='D',other_limit=None,seconds=30,seed=20261112,settings=None):
    from ortools.sat.python import cp_model
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
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=1;solver.parameters.random_seed=seed
    status=solver.Solve(model)
    if status not in [cp_model.FEASIBLE,cp_model.OPTIMAL]:raise ValueError('CP_COMPLETION_'+solver.StatusName(status))
    items=[]
    for s in range(S):
        if solver.Value(used[s]):
            r=next(r for r in range(len(routes)) if solver.Value(x[s,r]));items.append({'v':s//2,'trip_no':s%2+1,'route':routes[r],'start_s':solver.Value(starts[s])})
    info={**(settings or {}),'completion':'shared_CP_SAT_route_pool_physical_vehicles_and_optional_cumulative_loading',
          'primary':primary,'other_limit':other_limit,'pool_routes':len(routes),'CP_status':solver.StatusName(status),
          'scope':'finite_supplied_route_pool_only','seed':seed,'threads':1,'CP_objective_bound':solver.BestObjectiveBound(),
          'distance_objective_resolution_m':0.1,'lexicographic_tie_break':True}
    return assemble(p,items,method,info)
