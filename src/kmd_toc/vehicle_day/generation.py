"""Independent 0/1/2-trip schedules, referencing PyVRP's activity segmentation.

No external code copied. Explicit grid domain; exact only within that domain.
Inputs orders/starts; outputs validated-by-construction columns. No RNG.
"""
from itertools import product
from kmd_toc.column_generation.models import Route, enumerate_routes, route_cost
from .model import DayColumn, TripSchedule


def grid_ceil(t, delta):
    return ((t + delta - 1) // delta) * delta


def make_day(problem, vehicle_id, routes, starts):
    v = problem.vehicle(vehicle_id)
    if len(routes) != len(starts) or len(routes) > 2:
        raise ValueError('MAX_TWO_TRIPS_OR_START_MISMATCH')
    seen, result, ready = set(), [], v.ready_s
    for b, (route, start) in enumerate(zip(routes, starts), 1):
        ids = route.customers
        if not ids or len(set(ids)) != len(ids) or set(ids) & seen:
            raise ValueError('EMPTY_OR_REPEATED_CUSTOMER')
        if not set(ids) <= set(problem.base.customers):
            raise ValueError('UNKNOWN_CUSTOMER')
        load = sum(problem.base.demand[i] for i in ids)
        if load > v.capacity:
            raise ValueError('CAPACITY_EXCEEDED')
        if type(start) is not int or start % problem.delta_s or start < ready:
            raise ValueError('START_BEFORE_READY_OR_OFF_GRID')
        nodes = route.nodes()
        travel = sum(problem.travel_s[i][j] for i, j in zip(nodes, nodes[1:]))
        service = sum(problem.service_s[i] for i in ids)
        end = start + v.loading_s
        arrival = end + travel + service
        if arrival > v.shift_end_s:
            raise ValueError('SHIFT_END_EXCEEDED')
        result.append(TripSchedule(b, ids, load, ready, start, end, end, arrival,
                       travel, service, 0 if b == 1 else v.preparation_s,
                       route_cost(problem.base, route)))
        ready = arrival + v.preparation_s
        seen.update(ids)
    return DayColumn(problem.fingerprint, v.vehicle_id, v.shift_start_s, v.shift_end_s, tuple(result))


def enumerate_days(problem, route_pool=None, required_routes=None, max_columns=100000):
    if len(problem.base.customers) > 6 or len(problem.vehicles) > 2 or problem.slots > 40:
        raise ValueError('SMALL_REFERENCE_DOMAIN_LIMIT')
    pool = tuple(enumerate_routes(problem.base) if route_pool is None else sorted(set(route_pool)))
    required = set(required_routes or [])
    columns = []
    for v in problem.vehicles:
        if not required:
            columns.append(make_day(problem, v.vehicle_id, (), ()))
        valid = [r for r in pool if sum(problem.base.demand[i] for i in r.customers) <= v.capacity]
        sequences = [(r,) for r in valid]
        sequences += [(a, b) for a, b in product(valid, repeat=2)
                      if not set(a.customers) & set(b.customers)]
        for routes in sequences:
            if required and not any(r in required for r in routes):
                continue
            for first in range(grid_ceil(v.ready_s, problem.delta_s), v.shift_end_s, problem.delta_s):
                try:
                    one = make_day(problem, v.vehicle_id, routes[:1], (first,))
                except ValueError:
                    continue
                if len(routes) == 1:
                    columns.append(one)
                else:
                    ready2 = one.trips[0].return_s + v.preparation_s
                    for second in range(grid_ceil(ready2, problem.delta_s), v.shift_end_s, problem.delta_s):
                        try:
                            columns.append(make_day(problem, v.vehicle_id, routes, (first, second)))
                        except ValueError:
                            continue
                if len(columns) > max_columns:
                    raise ValueError('DAY_COLUMN_LIMIT')
    return columns


def seed_plan(problem):
    """ID-order initial assignment only; no optimization or oracle injection."""
    routes, current, load = [], [], 0
    capacity = min(v.capacity for v in problem.vehicles)
    for i in problem.base.customers:
        q = problem.base.demand[i]
        if q > capacity:
            return []
        if load + q > capacity:
            routes.append(Route(tuple(current)))
            current, load = [], 0
        current.append(i)
        load += q
    if current:
        routes.append(Route(tuple(current)))
    if len(routes) > 2 * len(problem.vehicles):
        return []
    assigned = {v.vehicle_id: [] for v in problem.vehicles}
    for b, r in enumerate(routes):
        assigned[problem.vehicles[b % len(problem.vehicles)].vehicle_id].append(r)
    starts, occupied = {v.vehicle_id: [] for v in problem.vehicles}, [0] * problem.slots
    pending = [(v.ready_s, v.vehicle_id, 0) for v in problem.vehicles if assigned[v.vehicle_id]]
    while pending:
        ready, vid, b = min(pending)
        pending.remove((ready, vid, b))
        v = problem.vehicle(vid)
        chosen = None
        for start in range(grid_ceil(ready, problem.delta_s), v.shift_end_s, problem.delta_s):
            slots = range(start // problem.delta_s, (start + v.loading_s + problem.delta_s - 1) // problem.delta_s)
            if any(u >= len(occupied) or occupied[u] >= problem.berths for u in slots):
                continue
            try:
                chosen = make_day(problem, vid, assigned[vid][:b + 1], starts[vid] + [start])
                break
            except ValueError:
                continue
        if chosen is None:
            return []
        starts[vid].append(start)
        for u in slots:
            occupied[u] += 1
        if b + 1 < len(assigned[vid]):
            pending.append((chosen.trips[-1].return_s + v.preparation_s, vid, b + 1))
    return [make_day(problem, v.vehicle_id, assigned[v.vehicle_id], starts[v.vehicle_id])
            for v in problem.vehicles if assigned[v.vehicle_id]]
