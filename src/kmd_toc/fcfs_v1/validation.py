"""Independent event replay: never call the production FCFS scheduler."""
import heapq
import math


def validate_fcfs(problem, plan):
    from .policy import require_frozen
    require_frozen()
    from kmd_toc.cargo_wait_v2.physical import validate_plan
    physical = validate_plan(problem, plan)
    violations = list(physical.violations)
    if not physical.feasible:
        return {'feasible': False, 'operating_policy': 'FCFS_v1', 'violations': violations,
                'physical': physical.as_dict(), 'W_loading_min': None}
    # Reconstruct future events from OD and input readiness, not recorded ready,
    # start, return or waiting. Keep a global waiting heap and all free berth IDs.
    trips = {(t.vehicle_id, t.trip_no): t for t in plan.trips}
    vehicles = {v.vehicle_id: v for v in problem.vehicles}
    index = {s: i for i, s in enumerate(problem.od.ids)}
    events = []
    for v in vehicles:
        if (v, 1) in trips:heapq.heappush(events, (vehicles[v].first_ready_s, 1, v, 1))
    for b in problem.berths:heapq.heappush(events, (b.opening_s, 0, b.berth_id, 0))
    idle = set(); waiting = []; expected = {}; wait_s = 0
    while events:
        now = events[0][0]
        while events and events[0][0] == now:
            time, kind, identifier, number = heapq.heappop(events)
            if kind == 0:idle.add(identifier)
            else:heapq.heappush(waiting, (time, identifier, number))
        while idle and waiting:
            ready, vid, number = heapq.heappop(waiting)
            bid = min(idle);idle.remove(bid)
            t = trips[vid, number]; start = now; end = start + 1800
            nodes = (problem.depot.depot_id, *(v.stop_id for v in t.visits), problem.depot.depot_id)
            ret = end + 120 * len(t.visits) + sum(math.ceil(float(problem.od.duration_s[index[a], index[b]]))
                                                 for a, b in zip(nodes, nodes[1:]))
            expected[vid, number] = {'ready_s': ready, 'berth_id': bid, 'load_start_s': start,
                'load_end_s': end, 'departure_s': end, 'return_s': ret, 'waiting_s': start-ready}
            wait_s += start-ready
            heapq.heappush(events, (end, 0, bid, 0))
            if number == 1 and (vid, 2) in trips:heapq.heappush(events, (ret, 1, vid, 2))
        if len(expected) == len(trips):break
    if len(expected) != len(trips):
        violations.append({'code': 'FCFS_UNSCHEDULED', 'context': '', 'detail': ''})
    for key, row in expected.items():
        for field, value in row.items():
            actual = getattr(trips[key], field)
            if actual != value:
                violations.append({'code': 'FCFS_' + field.upper(), 'context': f'{key[0]}/{key[1]}',
                                   'detail': {'expected': value, 'actual': actual}})
    return {'feasible': not violations, 'operating_policy': 'FCFS_v1', 'violations': violations,
            'physical': physical.as_dict(), 'W_loading_min': wait_s/60 if not violations else None,
            'expected_schedule': [{'vehicle_id': v, 'trip_no': k, **row} for (v, k), row in sorted(expected.items())]}


def require_fcfs(problem, plan):
    report = validate_fcfs(problem, plan)
    if not report['feasible']:
        raise ValueError('FCFS_V1_REJECTION:' + str(report['violations']))
    return report
