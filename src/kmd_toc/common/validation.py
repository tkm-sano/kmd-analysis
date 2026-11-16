"""Independent reconstruction from common input. Never imports a solver/builder."""
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import math
from .config import load_conditions
from .models import integer, number


@dataclass(frozen=True)
class Validation:
    feasible: bool
    violations: tuple[dict, ...]
    D_km: float | None
    W_min: float | None
    W1_min: float | None
    W2_min: float | None
    ready_to_loading_end_min: float | None
    trip_metrics: tuple[dict, ...]

    def as_dict(self):
        return asdict(self)


def validate_plan(problem, plan):
    violations = []
    def fail(code, context='', detail=''):
        violations.append({'code': code, 'context': context, 'detail': detail})
    def result(metrics=()):
        feasible = not violations
        if not feasible:
            return Validation(False, tuple(violations), None, None, None, None, None, tuple(metrics))
        return Validation(True, (), math.fsum(m['distance_m'] for m in metrics)/1000,
                          sum(m['waiting_s'] for m in metrics)/60,
                          sum(m['waiting_s'] for m in metrics if m['trip_no']==1)/60,
                          sum(m['waiting_s'] for m in metrics if m['trip_no']==2)/60,
                          sum(m['ready_to_loading_end_s'] for m in metrics)/60, tuple(metrics))
    try:
        problem.validate()
    except ValueError as error:
        fail('INPUT_HOLD', detail=str(error))
        return result()
    # Invalid JSON scalar/container types must produce a rejection, not a crash.
    if (not isinstance(plan.plan_id,str) or not isinstance(plan.method_id,str) or
            not isinstance(plan.method_settings,dict) or not isinstance(plan.trips,(list,tuple))):
        fail('PLAN_FIELD_TYPES')
        return result()
    for t in plan.trips:
        if (any(not isinstance(x,str) for x in
                (t.vehicle_id,t.berth_id,t.origin_id,t.destination_id)) or
                not isinstance(t.visits,(list,tuple)) or
                any(not isinstance(v.stop_id,str) for v in t.visits)):
            fail('PLAN_FIELD_TYPES')
            return result()
    if (plan.schema_version != '1.0' or not plan.plan_id or plan.method_id not in ('A','B','C','D') or
            plan.execution_kind not in ('classical', 'quantum_circuit_simulator')):
        fail('PLAN_METADATA')
    if plan.method_id == 'D' and plan.execution_kind != 'quantum_circuit_simulator':
        fail('AOA_EXECUTION_KIND')
    if plan.problem_hash != problem.fingerprint or plan.od_hash != problem.od.fingerprint:
        fail('COMMON_INPUT_OR_OD_HASH')
    c = load_conditions()
    o = c['operations']
    stops = {s.stop_id:s for s in problem.stops}
    vehicles = {v.vehicle_id:v for v in problem.vehicles}
    berths = {b.berth_id:b for b in problem.berths}
    visits = Counter(v.stop_id for t in plan.trips for v in t.visits)
    for identifier in sorted(stops.keys() | visits.keys()):
        if identifier not in stops:
            fail('UNKNOWN_STOP', identifier)
        elif visits[identifier] != 1:
            fail('VISIT_EXACTLY_ONCE', identifier, str(visits[identifier]))
    groups = defaultdict(list)
    intervals = []
    metrics = []
    for t in plan.trips:
        if t.vehicle_id not in vehicles:
            fail('UNKNOWN_VEHICLE', str(t.vehicle_id))
        if not integer(t.trip_no, minimum=1):
            fail('TRIP_NUMBER', str(t.vehicle_id))
            continue
        groups[t.vehicle_id].append(t)
    for vid, trips in groups.items():
        if vid not in vehicles:
            continue
        vehicle = vehicles[vid]
        trips = sorted(trips, key=lambda t:t.trip_no)
        if len(trips) > vehicle.max_trips or [t.trip_no for t in trips] != list(range(1, len(trips)+1)):
            fail('MAX_TWO_CONTIGUOUS_TRIPS', vid)
        previous_return = None
        for t in trips:
            context = f'{vid}/{t.trip_no}'
            fields = (t.ready_s,t.load_start_s,t.load_end_s,t.departure_s,t.return_s,t.waiting_s)
            if any(not integer(s) for s in fields) or any(
                    not integer(s) for visit in t.visits for s in
                    (visit.arrival_s,visit.service_start_s,visit.service_end_s)):
                fail('INTEGER_SECOND_TIMES', context)
                continue
            # Common v1.1: preparation_s=0, so trip 2 may load at trip 1 return.
            ready = vehicle.first_ready_s if t.trip_no == 1 else (
                previous_return + o['preparation_s'] if previous_return is not None else None)
            if ready is None or t.ready_s != ready:
                fail('READY_DEFINITION', context)
            if ready is not None and t.load_start_s < ready:
                fail('READY_OR_SECOND_TRIP_PREPARATION', context)
            if not t.visits:
                fail('EMPTY_USED_TRIP', context)
            if t.origin_id != problem.depot.depot_id or t.destination_id != problem.depot.depot_id:
                fail('DEPOT_ROUND_TRIP', context)
            if sum(stops[v.stop_id].demand for v in t.visits if v.stop_id in stops) > vehicle.capacity:
                fail('CAPACITY', context)
            if t.load_end_s - t.load_start_s != o['loading_s']:
                fail('LOADING_DURATION', context)
            if t.departure_s != t.load_end_s:
                fail('DEPARTURE_AT_LOADING_END', context)
            if t.berth_id not in berths:
                fail('UNKNOWN_BERTH', context)
            else:
                b = berths[t.berth_id]
                if t.load_start_s < b.opening_s or t.load_end_s > b.closing_s:
                    fail('BERTH_AVAILABILITY', context)
            if t.load_end_s > t.load_start_s:
                intervals.append((t.load_start_s,t.load_end_s,t.berth_id,context))
            distances = []
            clock = t.departure_s
            current = problem.depot.depot_id
            valid_route = True
            for visit in t.visits:
                if visit.stop_id not in stops:
                    valid_route = False
                    continue
                try:
                    distance, seconds = problem.od.leg(current, visit.stop_id)
                except ValueError as error:
                    fail('OD_ROUTE', context, str(error))
                    valid_route = False
                    continue
                clock += seconds
                distances.append(distance)
                if visit.arrival_s != clock:
                    fail('TRAVEL_TIME', context, visit.stop_id)
                if visit.service_start_s != clock or visit.service_end_s != clock + o['service_s']:
                    fail('CUSTOMER_SERVICE_TIME', context, visit.stop_id)
                clock += o['service_s']
                current = visit.stop_id
            if valid_route:
                distance, seconds = problem.od.leg(current,problem.depot.depot_id)
                distances.append(distance)
                clock += seconds
                previous_return = clock
                if t.return_s != clock:
                    fail('RETURN_TIME', context)
                distance = math.fsum(distances)
                if not number(t.distance_m) or not math.isclose(t.distance_m, distance, rel_tol=0, abs_tol=1e-6):
                    fail('DISTANCE_FROM_COMMON_OD', context)
            else:
                distance = None
                previous_return = None
            if t.return_s > vehicle.return_deadline_s or (valid_route and clock > vehicle.return_deadline_s):
                fail('RETURN_DEADLINE_2000', context)
            if t.departure_s < o['opening_s']:
                fail('OPERATING_WINDOW', context)
            waiting = t.load_start_s - ready if ready is not None else None
            if waiting is None or t.waiting_s != waiting:
                fail('WAITING_DEFINITION', context)
            metrics.append({'vehicle_id':vid,'trip_no':t.trip_no,'distance_m':distance,
                            'waiting_s':waiting, 'return_s':clock if valid_route else None,
                            'ready_to_loading_end_s':t.load_end_s-ready if ready is not None else None})
    # Half-open intervals: an end event sorts before a start at the same second.
    for berth_id in berths:
        ordered = sorted((s,e,k) for s,e,b,k in intervals if b == berth_id)
        largest_end = -1
        for s,e,k in ordered:
            if s < largest_end:
                fail('BERTH_OVERLAP', k, berth_id)
            largest_end = max(largest_end,e)
    active = 0
    events = sorted([(s,1,k) for s,e,b,k in intervals] + [(e,-1,k) for s,e,b,k in intervals])
    for second, change, context in events:
        active += change
        if active > len(berths):
            fail('BERTH_COUNT_EXCEEDED', context, str(second))
    return result(metrics)
