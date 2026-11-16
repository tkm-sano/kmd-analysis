"""Independent A v2 oracle. Reconstructs costs/times without builder helpers."""
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_CEILING


def audit_plan(problem, plan):
    errors = []
    def fail(code):
        errors.append(code)
    index = {s: i for i, s in enumerate(problem.od.ids)}
    stops = {s.stop_id: s for s in problem.stops}
    vehicles = {v.vehicle_id: v for v in problem.vehicles}
    berths = {b.berth_id: b for b in problem.berths}
    groups, bookings = defaultdict(list), defaultdict(list)
    from kmd_toc.common.config import load_conditions
    service = load_conditions()['operations']['service_s']
    seen = Counter(v.stop_id for t in plan.trips for v in t.visits)
    if seen != Counter({s: 1 for s in stops}):
        fail('COVERAGE')
    if plan.problem_hash != problem.fingerprint or plan.od_hash != problem.od.fingerprint:
        fail('INPUT_HASH')
    distance = Decimal(0)
    waiting = 0
    for t in plan.trips:
        if t.vehicle_id not in vehicles or t.berth_id not in berths:
            fail('RESOURCE_ID')
            continue
        vehicle, berth = vehicles[t.vehicle_id], berths[t.berth_id]
        groups[t.vehicle_id].append(t)
        times = (t.ready_s, t.load_start_s, t.load_end_s, t.departure_s, t.return_s, t.waiting_s,
                 *[x for v in t.visits for x in (v.arrival_s, v.service_start_s, v.service_end_s)])
        if type(t.trip_no) is not int or t.trip_no < 1 or any(type(x) is not int for x in times):
            fail('INTEGER_FIELDS')
        if not t.visits or any(v.stop_id not in stops for v in t.visits):
            fail('VISITS')
            continue
        if sum(stops[v.stop_id].demand for v in t.visits) > vehicle.capacity:
            fail('CAPACITY')
        if (t.origin_id, t.destination_id) != (problem.depot.depot_id,) * 2:
            fail('DEPOT')
        if (t.load_end_s - t.load_start_s != berth.loading_s or
                t.departure_s != t.load_end_s):
            fail('LOADING_DEPARTURE')
        if not berth.opening_s <= t.load_start_s <= t.load_end_s <= berth.closing_s:
            fail('BERTH_HOURS')
        bookings[t.berth_id].append((t.load_start_s, t.load_end_s))
        nodes = [problem.depot.depot_id, *[v.stop_id for v in t.visits], problem.depot.depot_id]
        clock, trip_distance = t.departure_s, Decimal(0)
        # Service duration comes from the input contract, not generator code.
        for k, (a, b) in enumerate(zip(nodes, nodes[1:])):
            i, j = index[a], index[b]
            d = Decimal(str(problem.od.distance_m[i, j]))
            seconds = Decimal(str(problem.od.duration_s[i, j]))
            if not problem.od.reachable[i, j] or not d.is_finite() or not seconds.is_finite():
                fail('UNREACHABLE')
                continue
            if d < 0 or seconds < 0:
                fail('NEGATIVE_OD')
                continue
            trip_distance += d
            clock += int(seconds.to_integral_value(rounding=ROUND_CEILING))
            if k < len(t.visits):
                visit = t.visits[k]
                if (visit.arrival_s, visit.service_start_s, visit.service_end_s) != (clock, clock, clock + service):
                    fail('VISIT_TIME')
                clock += service
        if clock != t.return_s or clock > vehicle.return_deadline_s:
            fail('RETURN_DEADLINE')
        if abs(trip_distance - Decimal(str(t.distance_m))) > Decimal('0.000001'):
            fail('TRIP_DISTANCE')
        distance += trip_distance
    for vid, trips in groups.items():
        vehicle = vehicles[vid]
        trips.sort(key=lambda t: t.trip_no)
        if len(trips) > vehicle.max_trips or [t.trip_no for t in trips] != list(range(1, len(trips) + 1)):
            fail('TRIP_COUNT')
        ready = vehicle.first_ready_s
        for t in trips:
            if t.ready_s != ready or t.load_start_s < ready:
                fail('READY_CONNECTION')
            delta = t.load_start_s - ready
            if delta < 0 or t.waiting_s != delta:
                fail('WAITING')
            waiting += delta
            ready = t.return_s + berths[t.berth_id].preparation_s
    for intervals in bookings.values():
        end = -1
        for start, stop in sorted(intervals):
            if start < end:
                fail('BERTH_OVERLAP')
            end = max(end, stop)
    return {'feasible': not errors, 'errors': sorted(set(errors)),
            'D_km': str(distance / 1000), 'W_min': str(Decimal(waiting) / 60),
            'visited_count': sum(seen.values()), 'unique_count': len(seen)}
