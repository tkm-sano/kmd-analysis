"""Fixed geographic rules, bounded assignment moves, routes and FCFS loading.

No B/C/D solver imports; coordinates shape territories only, OD supplies all costs.
"""
from collections import Counter
import heapq
import math
from kmd_toc.common.config import load_conditions
from kmd_toc.common.models import Plan, Trip, Visit
from .config import load_settings, SHA256


def _angular_order(p, offset):
    lat = math.radians(p.depot.latitude)
    def key(j):
        s = p.stops[j-1]
        x = (s.longitude-p.depot.longitude)*math.cos(lat)
        y = s.latitude-p.depot.latitude
        return ((math.degrees(math.atan2(y,x))-offset) % 360, x*x+y*y, s.stop_id)
    return sorted(range(1,len(p.stops)+1), key=key)


def _cost(route, d):
    nodes = [0, *route, 0]
    return math.fsum(float(d[a,b]) for a,b in zip(nodes,nodes[1:]))


def _chunks(route, capacity):
    return [list(route[k:k+capacity]) for k in range(0,len(route),capacity)]


def _nearest(group, p):
    remaining = set(group); result = []; current = 0
    while remaining:
        j = min(remaining, key=lambda j:(float(p.od.distance_m[current,j]),p.stops[j-1].stop_id))
        result.append(j); remaining.remove(j); current = j
    return result


def _group_cost(group, p, capacity):
    return math.fsum(_cost(r,p.od.distance_m) for r in _chunks(_nearest(group,p),capacity))


def _balance(groups, p, ranks, capacity, budget):
    weights = {j:120 + (math.ceil(float(p.od.duration_s[0,j])) +
                        math.ceil(float(p.od.duration_s[j,0])))/2
               for g in groups for j in g}
    trace = []
    if len(groups) < 2: return trace
    for _ in range(budget):
        work = [math.fsum(weights[j] for j in g) for g in groups]
        candidates = []
        for src, group in enumerate(groups):
            if not group: continue
            for dst in sorted({(src-1)%len(groups),(src+1)%len(groups)} - {src}):
                if len(groups[dst]) >= 2*capacity: continue
                for j in sorted(set([group[0],group[-1]])):
                    w = weights[j]
                    delta = (work[src]-w)**2+(work[dst]+w)**2-work[src]**2-work[dst]**2
                    if delta < -1e-6: candidates.append((delta,p.stops[j-1].stop_id,src,dst,j))
        if not candidates: break
        delta,_,src,dst,j = min(candidates)
        groups[src].remove(j); groups[dst].append(j); groups[dst].sort(key=ranks.__getitem__)
        trace.append({'stop_id':p.stops[j-1].stop_id,'from':src,'to':dst,'proxy_squared_delta':delta})
    return trace


def _relocate(groups, p, ranks, capacity, settings):
    trace = []; cfg = settings['relocation']
    for step in range(settings['methods']['A3']['relocation_passes']):
        for src in range(len(groups)):
            if not groups[src]: continue
            centers = [(sum(p.stops[j-1].longitude for j in g)/len(g),
                        sum(p.stops[j-1].latitude for j in g)/len(g)) if g else
                       (p.depot.longitude,p.depot.latitude) for g in groups]
            x,y = centers[src]
            dests = sorted((i for i in range(len(groups)) if i!=src),
                           key=lambda i:((centers[i][0]-x)**2+(centers[i][1]-y)**2,i))[:cfg['nearest_other_centroids']]
            candidates = []
            for dst in dests:
                if len(groups[dst]) >= 2*capacity: continue
                before = _group_cost(groups[src],p,capacity)+_group_cost(groups[dst],p,capacity)
                for j in sorted(set([groups[src][0],groups[src][-1]])):
                    a = [k for k in groups[src] if k!=j]; b = [*groups[dst],j]
                    after = _group_cost(a,p,capacity)+_group_cost(b,p,capacity)
                    if after < before-cfg['distance_tolerance_m']:
                        candidates.append((after-before,p.stops[j-1].stop_id,dst,j))
            if candidates:
                delta,_,dst,j = min(candidates)
                groups[src].remove(j); groups[dst].append(j); groups[dst].sort(key=ranks.__getitem__)
                trace.append({'pass':step,'stop_id':p.stops[j-1].stop_id,'from':src,'to':dst,'distance_delta_m':delta})
    return trace


def _two_opt(route, d, passes, tolerance):
    route = list(route); trace = []
    for _ in range(passes):
        before = _cost(route,d); chosen = None
        for i in range(len(route)-1):
            for j in range(i+1,len(route)):
                candidate = route[:i]+list(reversed(route[i:j+1]))+route[j+1:]
                delta = _cost(candidate,d)-before
                if delta < -tolerance:
                    chosen = (candidate,delta,i,j); break
            if chosen is not None: break
        if chosen is None: break
        route,delta,i,j = chosen; trace.append({'i':i,'j':j,'distance_delta_m':delta})
    return route,trace


def create_plan(problem, condition='A1', offset_deg=0, mark=None):
    settings = load_settings(); problem.validate()
    if condition not in settings['methods'] or offset_deg not in settings['angle_offsets_deg']:
        raise ValueError('A_UNREGISTERED_CONDITION')
    o = load_conditions()['operations']; V = len(problem.vehicles); capacity = o['capacity_per_trip']
    if sum(s.demand for s in problem.stops) > sum(v.capacity*v.max_trips for v in problem.vehicles):
        raise ValueError('A_TOTAL_CAPACITY_INSUFFICIENT')
    ordered = _angular_order(problem,offset_deg); ranks = {j:i for i,j in enumerate(ordered)}
    groups = [ordered[len(ordered)*v//V:len(ordered)*(v+1)//V] for v in range(V)]
    initial = {problem.stops[j-1].stop_id:v for v,g in enumerate(groups) for j in g}
    cfg = settings['methods'][condition]
    balance = _balance(groups,problem,ranks,capacity,cfg['balance_moves_per_vehicle']*V)
    relocations = _relocate(groups,problem,ranks,capacity,settings) if cfg['relocation_passes'] else []
    routes = []; reversals = []
    for v,g in enumerate(groups):
        order = g if condition=='A1' else _nearest(g,problem)
        r = _chunks(order,capacity)
        if len(r)>o['max_trips_per_vehicle']: raise ValueError('A_TRIP_COUNT_OVERFLOW')
        for k,route in enumerate(r):
            r[k],changes = _two_opt(route,problem.od.distance_m,cfg['two_opt_passes'],settings['relocation']['distance_tolerance_m'])
            reversals.extend({'vehicle_index':v,'trip_index':k,**change} for change in changes)
        routes.append(r)
    if mark: mark('A_assignment_and_order_end')
    # All first-ready events compete with returned vehicles' second-ready events.
    events = [(v.first_ready_s,i,0) for i,v in enumerate(problem.vehicles) if routes[i]]
    heapq.heapify(events); available = {b.berth_id:b.opening_s for b in problem.berths}; trips = []
    for_group = {j:problem.stops[j-1].stop_id for g in groups for j in g}
    while events:
        ready,v,k = heapq.heappop(events)
        berth = min(problem.berths,key=lambda b:(available[b.berth_id],b.berth_id))
        start = max(ready,available[berth.berth_id],berth.opening_s)
        end = start+o['loading_s']; available[berth.berth_id]=end
        clock = end; visits=[]; node=0
        for j in routes[v][k]:
            clock += math.ceil(float(problem.od.duration_s[node,j]))
            visits.append(Visit(for_group[j],clock,clock,clock+o['service_s']))
            clock += o['service_s']; node=j
        clock += math.ceil(float(problem.od.duration_s[node,0]))
        trips.append(Trip(problem.vehicles[v].vehicle_id,k+1,problem.depot.depot_id,problem.depot.depot_id,
                          tuple(visits),ready,berth.berth_id,start,end,end,clock,
                          _cost(routes[v][k],problem.od.distance_m),start-ready))
        if k+1<len(routes[v]):heapq.heappush(events,(clock+o['preparation_s'],v,k+1))
    if mark: mark('A_loading_and_timestamps_end')
    final = {problem.stops[j-1].stop_id:v for v,g in enumerate(groups) for j in g}
    meta = {'baseline_version':settings['baseline_version'],'settings_sha256':SHA256,
            'condition':condition,'angle_offset_deg':offset_deg,'seed':None,
            'value_kind':'research_rule_estimate','Sagawa_actual':False,
            'initial_assignment':initial,'final_assignment':final,'balance_moves':balance,
            'distance_relocations':relocations,'directed_two_opt_moves':reversals,
            'loading_rule':settings['loading']['rule'],'automatic_repair':False}
    return Plan('1.0',f'{problem.experiment.scenario_id}-{condition}-angle{offset_deg}','A',
                problem.fingerprint,problem.od.fingerprint,tuple(trips),meta,'classical')
