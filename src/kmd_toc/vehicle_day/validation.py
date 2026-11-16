"""Independent recomputation and finite exhaustive two-vehicle plan reference.

Does not call make_day or trust stored cost/time/load. Half-open interval sweep
is separate from master's slot constraints. No RNG or solver dependency here.
"""
from collections import Counter, defaultdict
from itertools import product
import math
from .model import occupied_slots


def validate_day(problem, column):
    reasons = set()
    try:
        v = problem.vehicle(column.vehicle_id)
    except StopIteration:
        return ['UNKNOWN_VEHICLE']
    if column.problem_hash != problem.fingerprint:
        reasons.add('INPUT_HASH_MISMATCH')
    if (column.shift_start_s, column.shift_end_s) != (v.shift_start_s, v.shift_end_s):
        reasons.add('SHIFT_METADATA_MISMATCH')
    if len(column.trips) > 2:
        reasons.add('MAX_TWO_TRIPS')
    seen, previous = set(), None
    for b, trip in enumerate(column.trips, 1):
        if trip.trip_id != b:
            reasons.add('TRIP_ID_OR_SECOND_ONLY')
        ids = trip.customers
        if not ids or not set(ids) <= set(problem.base.customers):
            reasons.add('EMPTY_OR_UNKNOWN_STOP')
            continue
        if len(set(ids)) != len(ids) or set(ids) & seen:
            reasons.add('DUPLICATE_CUSTOMER')
        seen.update(ids)
        nodes = (0,) + ids + (0,)
        load = sum(problem.base.demand[i] for i in ids)
        travel = sum(problem.travel_s[i][k] for i, k in zip(nodes, nodes[1:]))
        service = sum(problem.service_s[i] for i in ids)
        distance = sum(problem.base.distance[i, k] for i, k in zip(nodes, nodes[1:]))
        ready = v.ready_s if previous is None else previous.return_s + v.preparation_s
        if trip.parcel_count != load:
            reasons.add('LOAD_METADATA_MISMATCH')
        if load > v.capacity:
            reasons.add('CAPACITY_EXCEEDED')
        if trip.ready_s != ready:
            reasons.add('READY_TIME_MISMATCH')
        if trip.load_start_s < ready:
            reasons.add('LOAD_BEFORE_READY_OR_PREPARATION')
        if trip.load_start_s % problem.delta_s:
            reasons.add('LOAD_START_OFF_GRID')
        if trip.load_end_s != trip.load_start_s + v.loading_s:
            reasons.add('LOADING_DURATION_MISMATCH')
        if trip.departure_s != trip.load_end_s:
            reasons.add('DEPARTURE_NOT_AT_LOADING_END')
        if trip.return_s != trip.departure_s + travel + service:
            reasons.add('RETURN_TIME_MISMATCH')
        if trip.return_s > v.shift_end_s or trip.load_start_s < v.shift_start_s:
            reasons.add('SHIFT_END_EXCEEDED')
        if trip.preparation_s != (0 if b == 1 else v.preparation_s):
            reasons.add('PREPARATION_METADATA_MISMATCH')
        if trip.travel_s != travel or trip.service_s != service:
            reasons.add('TRAVEL_SERVICE_MISMATCH')
        if not math.isclose(trip.distance_km, distance, abs_tol=1e-9):
            reasons.add('DISTANCE_MISMATCH')
        previous = trip
    return sorted(reasons)


def validate_plan(problem, columns):
    reasons = set()
    for c in columns:
        reasons.update(validate_day(problem, c))
    vehicles = [c.vehicle_id for c in columns]
    if len(vehicles) != len(set(vehicles)):
        reasons.add('MULTIPLE_DAYS_SAME_VEHICLE')
    visits = Counter(i for c in columns for i in c.customers)
    if any(visits[i] != 1 for i in problem.base.customers) or set(visits) != set(problem.base.customers):
        reasons.add('CUSTOMER_COVERAGE')
    events = [(t.load_start_s, 1) for c in columns for t in c.trips]
    events += [(t.load_end_s, -1) for c in columns for t in c.trips]
    active = peak = 0
    for _, delta in sorted(events):  # end (-1) before start (+1)
        active += delta
        peak = max(peak, active)
    if peak > problem.berths:
        reasons.add('BERTH_OVERLAP')
    w = [sum(t.load_start_s - t.ready_s for c in columns for t in c.trips if t.trip_id == b) / 60
         for b in [1, 2]]
    return {'valid': not reasons, 'reasons': sorted(reasons),
            'D_km': float(sum(c.distance_km for c in columns)),
            'W1_min': w[0], 'W2_min': w[1], 'W_min': sum(w),
            'loading_work_min': sum(c.loading_s for c in columns) / 60,
            'peak_berths': peak, 'used_vehicles': sum(bool(c.trips) for c in columns),
            'trip_count': sum(len(c.trips) for c in columns)}


def assign_berths(problem, columns):
    if not validate_plan(problem, columns)['valid']:
        raise ValueError('Cannot assign berths to invalid plan')
    free_at = [0] * problem.berths
    assignments = []
    trips = sorted((t.load_start_s, c.vehicle_id, t.trip_id, t.load_end_s)
                   for c in columns for t in c.trips)
    for start, vehicle, trip, end in trips:
        available = [b for b, free in enumerate(free_at) if free <= start]
        if not available:
            raise RuntimeError('Interval coloring contradicts capacity constraints')
        berth = min(available)
        free_at[berth] = end
        assignments.append({'vehicle_id': vehicle, 'trip_id': trip,
                            'berth_id': berth, 'start_s': start, 'end_s': end})
    return assignments


def independent_plan_oracle(problem, all_columns, profile):
    """All compatible mask combinations, independent of LP/MIP and pricing.

    For one primary with no epsilon bound, identical cover/occupancy signatures
    can retain the cheapest representative exactly. Epsilon profiles retain all
    signatures including the other metric to preserve tradeoffs.
    """
    if len(problem.vehicles) != 2:
        raise ValueError('Independent oracle is limited to two vehicles')
    buckets = [{}, {}]
    vidx = {v.vehicle_id: k for k, v in enumerate(problem.vehicles)}
    for column in all_columns:
        coverage = sum(1 << (i - 1) for i in column.customers)
        occupancy = sum(1 << u for u in occupied_slots(problem, column)) if problem.berths == 1 else 0
        key = (coverage, occupancy, profile.other(column) if profile.other_limit is not None else 0)
        bucket = buckets[vidx[column.vehicle_id]]
        old = bucket.get(key)
        if old is None or (profile.cost(column), column.column_id) < (profile.cost(old), old.column_id):
            bucket[key] = column
    by_mask = defaultdict(list)
    for (mask, occupancy, _), c in buckets[1].items():
        by_mask[mask].append((occupancy, c))
    all_mask = (1 << len(problem.base.customers)) - 1
    best, best_value, comparisons = None, math.inf, 0
    for (mask, occupancy, _), a in buckets[0].items():
        for other_occ, b in by_mask[all_mask ^ mask]:
            comparisons += 1
            if occupancy & other_occ:
                continue
            if profile.other_limit is not None and profile.other(a) + profile.other(b) > profile.other_limit + 1e-9:
                continue
            value = profile.cost(a) + profile.cost(b)
            if value < best_value - 1e-9:
                best, best_value = [a, b], value
    return {'feasible': best is not None, 'objective': None if best is None else best_value,
            'columns': best, 'comparisons': comparisons,
            'scope': 'FULL_FINITE_GRID_DAY_DOMAIN'}
