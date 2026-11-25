"""Pinned routes, original FCFS priority, breaks propagated before trip-2 ready."""
from dataclasses import replace
import math

from kmd_toc.common.models import Trip, Visit
from .models import Break, DutyPlan, DutyProblem
from .policy import VERSION, load_policy, policy_hash


class NoDutySchedule(ValueError):
    """No completion for this assignment/rule; not a global VRP certificate."""


def route_data(p, route):
    index={s:i for i,s in enumerate(p.od.ids)}
    nodes=(p.depot.depot_id,*route,p.depot.depot_id)
    travel=[math.ceil(float(p.od.duration_s[index[a],index[b]])) for a,b in zip(nodes,nodes[1:])]
    distances=[float(p.od.distance_m[index[a],index[b]]) for a,b in zip(nodes,nodes[1:])]
    clock=0;offsets=[]
    for j,stop in enumerate(route):
        clock+=travel[j]
        if p.rest_options.eligible(stop):offsets.append((j,clock))
        clock+=120
        if p.rest_options.eligible(stop):offsets.append((j,clock))
    return travel,math.fsum(distances),offsets


def project_trip(p, key, route, start, ready, berth, break_already_taken):
    c=load_policy();travel,distance,_=route_data(p,route)
    clock=start+1800;visits=[];rest=None
    for j,stop in enumerate(route):
        clock+=travel[j];arrival=clock
        if (not break_already_taken and rest is None and p.rest_options.eligible(stop) and
                c['break_start_earliest_s']<=clock<=c['break_start_latest_s']):
            status,evidence=p.rest_options.evidence(stop)
            rest=Break(key[0],key[1],stop,clock,clock+3600,'before_delivery_service',status,evidence)
            clock+=3600
        visits.append(Visit(stop,arrival,clock,clock+120));clock+=120
        if (not break_already_taken and rest is None and p.rest_options.eligible(stop) and
                c['break_start_earliest_s']<=clock<=c['break_start_latest_s']):
            status,evidence=p.rest_options.evidence(stop)
            rest=Break(key[0],key[1],stop,clock,clock+3600,'after_delivery_service',status,evidence)
            clock+=3600
    clock+=travel[-1]
    trip=Trip(key[0],key[1],p.depot.depot_id,p.depot.depot_id,tuple(visits),ready,berth,
              start,start+1800,start+1800,clock,distance,start-ready)
    return trip,rest


def schedule(p,routes,method,settings=None,*,validate=True):
    if not isinstance(p,DutyProblem):
        raise ValueError('EXPLICIT_DUTY_INPUT_REQUIRED')
    p.validate_duty();c=load_policy()
    if method not in ('B','C','D','Q'):
        raise ValueError('A_IS_EXTERNAL_NO_DUTY_SCHEDULE')
    vehicles={v.vehicle_id:v for v in p.vehicles};stops={s.stop_id:s for s in p.stops}
    pending={key:tuple(route) for key,route in routes.items()}
    if not pending:raise NoDutySchedule('NO_ACTIVE_ROUTES')
    for (vid,k),route in pending.items():
        if vid not in vehicles or type(k) is not int or k not in (1,2) or not route:
            raise NoDutySchedule('VEHICLE_TRIP_OR_EMPTY_ROUTE')
        if k==2 and (vid,1) not in pending:raise NoDutySchedule('SECOND_WITHOUT_FIRST')
        if any(s not in stops for s in route) or sum(stops[s].demand for s in route)>vehicles[vid].capacity:
            raise NoDutySchedule('UNKNOWN_STOP_OR_CAPACITY')
    free={b.berth_id:b.opening_s for b in p.berths};berths={b.berth_id:b for b in p.berths}
    returns={};breaks={};trips=[]
    while pending:
        released=[(vehicles[v].first_ready_s if k==1 else returns[v,1],v,k)
                  for v,k in pending if k==1 or (v,1) in returns]
        if not released:raise NoDutySchedule('TRIP_RELEASE_DEADLOCK')
        ready,vid,k=min(released)
        start=max(ready,min(free.values()),c['shift_start_s'])
        bid=min(b for b in free if free[b]<=start)
        free[bid]=start+1800
        trip,rest=project_trip(p,(vid,k),pending.pop((vid,k)),start,ready,bid,vid in breaks)
        trips.append(trip);returns[vid,k]=trip.return_s
        if rest:breaks[vid]=rest
    # Optional, explicitly approved post-final / unused-driver depot placement.
    # Never inserted between trips or immediately after loading.
    for vid in vehicles:
        if vid in breaks:continue
        actual=[t.return_s for t in trips if t.vehicle_id==vid]
        if not actual:continue  # User clarification: unused vehicles are excluded.
        final=max(actual)
        if (not p.rest_options.allow_post_final_depot_break or
                not p.rest_options.eligible(p.depot.depot_id) or final>43200):
            continue  # Rejected by the independent validator; retain all diagnostics.
        start=43200;status,evidence=p.rest_options.evidence(p.depot.depot_id)
        breaks[vid]=Break(vid,None,p.depot.depot_id,start,start+3600,'after_final_return_by_noon',status,evidence)
    native='D' if method=='Q' else method
    plan=DutyPlan('duty-break-plan-v1',p.experiment.scenario_id+'-'+native+'-'+VERSION,native,
                  p.fingerprint,p.od.fingerprint,tuple(sorted(trips,key=lambda t:(t.vehicle_id,t.trip_no))),
                  {**(settings or {}),'duty_version':VERSION,'duty_policy_sha256':policy_hash(),
                   'base_problem_hash':p.base.fingerprint,'rest_options':p.rest_options.payload(),
                   'operating_policy':'FCFS_v1_with_explicit_inroute_break_duration',
                   'reported_method':method,'rest_selection':'earliest_eligible_arrival_or_service_end_trip1_then_trip2'},
                  'quantum_circuit_simulator' if native=='D' else 'classical',tuple(breaks[v] for v in sorted(breaks)))
    if validate:
        from .validation import require_valid
        require_valid(p,plan)
    return plan


def replay(p,old_plan,*,validate=True):
    if old_plan.problem_hash!=p.base.fingerprint or old_plan.od_hash!=p.od.fingerprint:
        raise ValueError('BASE_PLAN_INPUT_HASH_MISMATCH')
    keys=[(t.vehicle_id,t.trip_no) for t in old_plan.trips]
    if len(keys)!=len(set(keys)):raise ValueError('DUPLICATE_TRIP_ID')
    return schedule(p,{(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in old_plan.trips},
                    old_plan.method_id,{'conversion':'explicit_routes_pinned_duty_replay_not_optimizer_rerun',
                                        'source_plan_id':old_plan.plan_id},validate=validate)
