"""One deterministic, work-conserving queue shared by B/C/Q (internal D)."""
from dataclasses import replace
import math

from kmd_toc.common.models import Plan, Trip, Visit

POLICY_ID = 'FCFS_v1'


def schedule_jobs(first_ready, durations, berths, *, loading_s=1800):
    """Time dependent second-trip releases; IDs use ascending string order.

    durations[(vehicle_id, trip_no)] excludes loading, includes depot round trip
    and customer service. No previously recorded start/return is trusted.
    """
    if loading_s != 1800 or not berths:
        raise ValueError('FCFS_V1_REQUIRES_1800_SECONDS_AND_BERTHS')
    if any(type(t) is not int or t < 0 for t in durations.values()):
        raise ValueError('FCFS_INTEGER_NONNEGATIVE_ROUTE_DURATION')
    if any(type(v) is not str or not v or type(k) is not int or k not in (1, 2)
           or v not in first_ready for v, k in durations):
        raise ValueError('FCFS_TRIP_ID')
    if any(k == 2 and (v, 1) not in durations for v, k in durations):
        raise ValueError('FCFS_SECOND_TRIP_WITHOUT_FIRST')
    if any(type(t) is not int or t < 0 for t in first_ready.values()):
        raise ValueError('FCFS_INTEGER_READY')
    free = {bid: opening for bid, (opening, closing) in berths.items()}
    if any(not isinstance(bid, str) or type(o) is not int or type(c) is not int or o > c
           for bid, (o, c) in berths.items()):
        raise ValueError('FCFS_BERTH_INPUT')
    pending = set(durations)
    returns = {}
    rows = []
    while pending:
        released = [(first_ready[v] if k == 1 else returns[v, 1], v, k)
                    for v, k in pending if k == 1 or (v, 1) in returns]
        if not released:
            raise ValueError('FCFS_RELEASE_DEADLOCK')
        ready, vid, number = min(released)
        start = max(ready, min(free.values()))
        # At this start time every already idle berth is eligible, even if a
        # higher-ID berth has been idle longer. Earliest-free is NOT the tie rule.
        bid = min(b for b in free if free[b] <= start)
        end = start + loading_s
        if end > berths[bid][1]:
            raise ValueError('FCFS_BERTH_CLOSING')
        ret = end + durations[vid, number]
        returns[vid, number] = ret
        free[bid] = end
        pending.remove((vid, number))
        rows.append(dict(vehicle_id=vid, trip_no=number, ready_s=ready, berth_id=bid,
                         load_start_s=start, load_end_s=end, departure_s=end, return_s=ret))
    return rows


def schedule(problem, routes, method, settings=None):
    """Build a whole plan with pinned assignments/orders and recheck physical law."""
    from .policy import require_frozen
    require_frozen()
    if method not in ('B', 'C', 'D', 'Q'):
        raise ValueError('FCFS_APPLIES_TO_B_C_Q_ONLY_A_IS_EXTERNAL')
    problem.validate()
    routes = {key: tuple(route) for key, route in routes.items()}
    if not routes or any(not route for route in routes.values()):
        raise ValueError('EMPTY_ACTIVE_TRIP')
    index = {s: i for i, s in enumerate(problem.od.ids)}
    stops = {s.stop_id: s for s in problem.stops}
    vehicles = {v.vehicle_id: v for v in problem.vehicles}
    durations = {}
    for key, route in routes.items():
        vid, number = key
        if vid not in vehicles or any(s not in stops for s in route):
            raise ValueError('FCFS_UNKNOWN_VEHICLE_OR_CUSTOMER')
        if sum(stops[s].demand for s in route) > vehicles[vid].capacity:
            raise ValueError('CAPACITY')
        nodes = (problem.depot.depot_id, *route, problem.depot.depot_id)
        durations[key] = sum(math.ceil(float(problem.od.duration_s[index[a], index[b]]))
                             for a, b in zip(nodes, nodes[1:])) + 120 * len(route)
    rows = schedule_jobs({v: x.first_ready_s for v, x in vehicles.items()}, durations,
                         {b.berth_id: (b.opening_s, b.closing_s) for b in problem.berths})
    trips = []
    for row in rows:
        route = routes[row['vehicle_id'], row['trip_no']]
        clock = row['departure_s']; current = problem.depot.depot_id; visits = []; distances = []
        for stop in route:
            a, b = index[current], index[stop]
            clock += math.ceil(float(problem.od.duration_s[a, b]))
            visits.append(Visit(stop, clock, clock, clock + 120)); clock += 120
            distances.append(float(problem.od.distance_m[a, b])); current = stop
        distances.append(float(problem.od.distance_m[index[current], 0]))
        clock += math.ceil(float(problem.od.duration_s[index[current], 0]))
        assert clock == row['return_s']
        trips.append(Trip(row['vehicle_id'], row['trip_no'], problem.depot.depot_id,
            problem.depot.depot_id, tuple(visits), row['ready_s'], row['berth_id'],
            row['load_start_s'], row['load_end_s'], row['departure_s'], row['return_s'],
            math.fsum(distances), row['load_start_s'] - row['ready_s']))
    native = 'D' if method == 'Q' else method
    plan = Plan('1.0', problem.experiment.scenario_id + '-' + native + '-FCFS_v1', native,
                problem.fingerprint, problem.od.fingerprint,
                tuple(sorted(trips, key=lambda t: (t.vehicle_id, t.trip_no))),
                {**(settings or {}), 'operating_policy': POLICY_ID, 'reported_method': method},
                'quantum_circuit_simulator' if native == 'D' else 'classical')
    from .validation import require_fcfs
    require_fcfs(problem, plan)
    return plan


def reschedule(problem, plan, *, method=None):
    """Explicit conversion to a NEW plan; caller must use a new output directory."""
    keys=[(t.vehicle_id,t.trip_no) for t in plan.trips]
    if len(keys)!=len(set(keys)):
        raise ValueError('FCFS_DUPLICATE_TRIP_ID_NO_SILENT_REPAIR')
    result = schedule(problem, {(t.vehicle_id, t.trip_no): tuple(v.stop_id for v in t.visits)
                                for t in plan.trips}, method or plan.method_id,
                      {**plan.method_settings, 'source_plan_id': plan.plan_id,
                       'conversion': 'routes_pinned_times_recomputed_not_a_rerun'})
    return replace(result, plan_id=plan.plan_id + '-FCFS_v1')
