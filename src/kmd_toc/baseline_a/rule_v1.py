"""A_rule_v1: deterministic, bounded joint assignment/order/trip decisions.

All rules are research assumptions. No operator algorithm is reproduced.
Candidate states are immutable; only route geometry (never berth times) is cached.
"""
from dataclasses import dataclass, replace
from collections import Counter
import heapq
import math
import time
import unicodedata

from kmd_toc.common.models import Plan, Trip, Visit

VERSION = 'A_rule_v1-20261115'


def normalized_ids(problem):
    ids = tuple(unicodedata.normalize('NFC', s) for s in problem.od.ids)
    if len(set(ids)) != len(ids):
        raise ValueError('NORMALIZED_ID_COLLISION')
    return ids


def angular_groups(p):
    ids = normalized_ids(p)
    cosine = math.cos(math.radians(p.depot.latitude))
    def key(j):
        stop = p.stops[j-1]
        x = (stop.longitude-p.depot.longitude)*cosine
        y = stop.latitude-p.depot.latitude
        return (math.degrees(math.atan2(y, x)) % 360, x*x+y*y, ids[j])
    order = sorted(range(1, len(p.stops)+1), key=key)
    n, v = len(order), len(p.vehicles)
    return tuple(tuple(order[n*i//v:n*(i+1)//v]) for i in range(v))


def nearest_order(nodes, problem, *, context=None):
    """Exchange interface: assigned nodes -> one permutation; no trip splitting.

    context reserves explicit zone/history/budget inputs for future adapters.
    Cook is deliberately not implemented or silently substituted here.
    """
    ids = normalized_ids(problem)
    remaining, current, result = set(nodes), 0, []
    if len(remaining) != len(nodes):
        raise ValueError('DUPLICATE_ORDER_INPUT')
    while remaining:
        chosen = min(remaining, key=lambda j: (float(problem.od.distance_m[current,j]), ids[j]))
        result.append(chosen)
        remaining.remove(chosen)
        current = chosen
    return tuple(result)


@dataclass(frozen=True)
class Route:
    nodes: tuple
    distance_m: float
    duration_s: int
    # Arrival offsets relative to departure, before service at each stop.
    arrivals: tuple


def compile_group(p, group, orderer=nearest_order, context=None):
    order = tuple(orderer(group, p, context=context)) if group else ()
    if Counter(order) != Counter(group):
        raise ValueError('ORDERER_PERMUTATION')
    routes = []
    for begin in range(0, len(order), 60):
        nodes = order[begin:begin+60]
        clock, current, arrivals, distances = 0, 0, [], []
        for j in (*nodes, 0):
            if not p.od.reachable[current,j]:
                raise ValueError('UNREACHABLE')
            d, t = float(p.od.distance_m[current,j]), float(p.od.duration_s[current,j])
            if not math.isfinite(d) or not math.isfinite(t) or min(d,t) < 0:
                raise ValueError('INVALID_OD')
            distances.append(d)
            clock += math.ceil(t)
            if j:
                arrivals.append(clock)
                clock += 120
            current = j
        routes.append(Route(nodes, math.fsum(distances), clock, tuple(arrivals)))
    if len(routes) > 2:
        raise ValueError('MAX_TRIPS')
    return tuple(routes)


def schedule(p, routes):
    """Rebuild the entire ready-order FCFS schedule, with no stored start reuse."""
    events = [(v.first_ready_s,i,0) for i,v in enumerate(p.vehicles) if routes[i]]
    heapq.heapify(events)
    berths = sorted(p.berths, key=lambda b:b.berth_id)
    free = [b.opening_s for b in berths]
    bookings = []
    final = [None]*len(p.vehicles)
    while events:
        ready, v, k = heapq.heappop(events)
        b = min(range(len(berths)), key=lambda i:(free[i],berths[i].berth_id))
        start = max(ready, free[b], berths[b].opening_s)
        end = start+berths[b].loading_s
        free[b] = end
        returned = end+routes[v][k].duration_s
        bookings.append((v,k,berths[b].berth_id,ready,start,end,returned))
        final[v] = returned
        if k+1 < len(routes[v]):
            heapq.heappush(events,(returned+berths[b].preparation_s,v,k+1))
    loads = [r-v.first_ready_s if r is not None else 0 for r,v in zip(final,p.vehicles)]
    overtime = sum(max(0,r-v.return_deadline_s) for r,v in zip(final,p.vehicles) if r is not None)
    return {'bookings':tuple(bookings), 'final_return_s':tuple(final), 'L_s':tuple(loads),
            'objective':(overtime,sum(x*x for x in loads))}


def boundary_candidates(groups):
    """Fixed circular boundaries i -> (i+1)%V, then clockwise/reverse.

    Empty sectors keep their vehicle index and neighbours; never skip them.
    Circular sequence order is retained when a point crosses the zero-angle cut.
    """
    if len(groups) < 2:
        return
    for left in range(len(groups)):
        right = (left+1) % len(groups)
        if groups[left]:
            yield left,right,groups[left][-1],'clockwise'
        if groups[right]:
            yield right,left,groups[right][0],'counterclockwise'


def move(groups, src, dst, node, direction):
    changed = list(groups)
    if direction == 'clockwise':
        assert groups[src][-1] == node
        changed[src] = groups[src][:-1]
        changed[dst] = (node,*groups[dst])
    else:
        assert groups[src][0] == node
        changed[src] = groups[src][1:]
        changed[dst] = (*groups[dst],node)
    return tuple(changed)


def materialize(p, routes, state, metadata):
    trips = []
    for v,k,berth,ready,start,end,returned in state['bookings']:
        route = routes[v][k]
        visits = tuple(Visit(p.od.ids[j],end+a,end+a,end+a+120)
                       for j,a in zip(route.nodes,route.arrivals))
        trips.append(Trip(p.vehicles[v].vehicle_id,k+1,p.depot.depot_id,p.depot.depot_id,
                          visits,ready,berth,start,end,end,returned,route.distance_m,start-ready))
    return Plan('1.0',p.experiment.scenario_id+'-'+VERSION,'A',p.fingerprint,p.od.fingerprint,
                tuple(trips),metadata,'classical')


def generate(p, *, deadline=math.inf, max_evaluations=10000, clock=time.perf_counter,
             orderer=nearest_order, use_cache=True, context=None):
    groups = initial = angular_groups(p)
    if any(len(g)>120 for g in groups):
        raise ValueError('RULE_INITIAL_CAPACITY_EXCEEDED')
    calls, order_time = 0, 0.
    def compile_one(group):
        nonlocal calls, order_time
        begin = clock()
        result = compile_group(p, group, orderer, context)
        calls += bool(group)
        order_time += clock()-begin
        return result
    routes = tuple(compile_one(g) for g in groups)
    state = schedule(p,routes)
    initial_state = state
    trace, accepted, scans = [], [], 0
    stop = 'MOVE_LIMIT'
    for _ in range(len(p.vehicles)):
        if clock() >= deadline:
            stop = 'PLANNING_TIME_LIMIT'
            break
        scans += 1
        improved = False
        for src,dst,node,direction in boundary_candidates(groups):
            if clock() >= deadline or len(trace)>=max_evaluations:
                stop = 'PLANNING_TIME_LIMIT' if clock()>=deadline else 'EVALUATION_LIMIT'
                break
            record = {'scan':scans,'source':src,'destination':dst,'node':node,
                      'stop_id':p.od.ids[node],'direction':direction,'before':state['objective']}
            if len(groups[dst])>=120:
                trace.append({**record,'status':'CAPACITY_REJECTED','after':None})
                continue
            candidate = move(groups,src,dst,node,direction)
            if use_cache:
                candidate_routes = list(routes)
                for v in (src,dst):
                    candidate_routes[v] = compile_one(candidate[v])
                candidate_routes = tuple(candidate_routes)
            else:
                candidate_routes = tuple(compile_one(g) for g in candidate)
            candidate_state = schedule(p,candidate_routes)
            # Integer seconds and integer squared loads: exact lexicographic comparison.
            better = candidate_state['objective'] < state['objective']
            trace.append({**record,'after':candidate_state['objective'],
                          'status':'ACCEPTED' if better else 'NO_STRICT_IMPROVEMENT'})
            if better:
                groups,routes,state = candidate,candidate_routes,candidate_state
                accepted.append(trace[-1])
                improved = True
                break
        if stop in ('PLANNING_TIME_LIMIT','EVALUATION_LIMIT'):
            break
        if not improved:
            stop = 'NO_IMPROVEMENT'
            break
    meta = {'method_version':VERSION,'operator_actual_algorithm':False,'orderer':orderer.__name__,
            'initial_groups':initial,'final_groups':groups,'initial_objective':initial_state['objective'],
            'final_objective':state['objective'],'candidate_evaluations':len(trace),'scans':scans,
            'accepted_moves':len(accepted),'stop_reason':stop,'candidate_trace':trace,
            'orderer_calls':calls,'orderer_wall_s':order_time,'loading_rule':'ready_FCFS',
            'inactive_vehicle_L_s':0,'initial_angle_deg':0,'route_cache':use_cache}
    # Timing diagnostics must not alter the reproducible plan bytes.
    diagnostic = {k:meta.pop(k) for k in ('orderer_calls','orderer_wall_s')}
    return materialize(p,routes,state,meta), {**meta,**diagnostic,'state':state}
