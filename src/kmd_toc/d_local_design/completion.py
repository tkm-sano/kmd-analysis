"""Pinned assignment/order completion, dual validation, Pareto decision ledger."""
from dataclasses import replace, asdict
from decimal import Decimal, ROUND_HALF_EVEN
from time import perf_counter
from .model import LocalProblem, Decision


def trip_key(trip):
    return trip.vehicle_id, trip.trip_no


def extract(p, plan, keys, selected, seed=0):
    keys, selected = tuple(keys), tuple(selected)
    trips = {trip_key(t): t for t in plan.trips}
    if len(keys) != 2 or len(set(keys)) != 2 or any(k not in trips for k in keys):
        raise ValueError('TARGET_TRIPS')
    available = {v.stop_id for k in keys for v in trips[k].visits}
    if len(set(selected)) != len(selected) or not set(selected) <= available:
        raise ValueError('LOCAL_SELECTION')
    indices = [0, *(p.od.ids.index(s) for s in selected)]
    outside = tuple({'trip_id': trip_key(t), 'customers': tuple(v.stop_id for v in t.visits if v.stop_id not in selected),
                     'original_customers': tuple(v.stop_id for v in t.visits),
                     'constraints': 'vehicle/trip identity fixed; nonselected order fixed; full shared physical constraints'}
                    for t in plan.trips)
    demands = {s.stop_id: s.demand for s in p.stops}
    import numpy as np
    return LocalProblem(f'{plan.plan_id}:{keys}:{seed}', keys, selected, tuple(demands[s] for s in selected),
        tuple(map(tuple, p.od.distance_m[np.ix_(indices, indices)].tolist())),
        tuple(map(tuple, p.od.duration_s[np.ix_(indices, indices)].tolist())),
        {'plan_id': plan.plan_id, 'problem_hash': plan.problem_hash, 'od_hash': plan.od_hash}, outside, seed).validate()


def pinned_routes(plan, local, decision):
    decision.validate(local.customer_ids)
    selected = set(local.customer_ids)
    decision_by_key = dict(zip(local.trip_ids, (decision.trip_1, decision.trip_2)))
    result = {}
    for t in plan.trips:
        key = trip_key(t)
        original = tuple(v.stop_id for v in t.visits)
        if key not in decision_by_key:
            result[key] = original
            continue
        # Insert the quantum block at the first removed position. Keep ALL
        # nonselected customers and their relative order; never repair Q output.
        anchor = next((i for i, s in enumerate(original) if s in selected), len(original))
        prefix = tuple(s for s in original[:anchor] if s not in selected)
        suffix = tuple(s for s in original[anchor:] if s not in selected)
        result[key] = prefix + decision_by_key[key] + suffix
    return result


def preserves(plan, local, decision, original=None):
    trips = {trip_key(t): tuple(v.stop_id for v in t.visits) for t in plan.trips}
    selected = set(local.customer_ids)
    for key, expected in zip(local.trip_ids, (decision.trip_1, decision.trip_2)):
        if key not in trips or tuple(s for s in trips[key] if s in selected) != expected:
            return False
    if any(s in selected for key, route in trips.items() if key not in local.trip_ids for s in route):
        return False
    if original is not None:
        old = {trip_key(t): tuple(v.stop_id for v in t.visits) for t in original.trips}
        if set(old) != set(trips):
            return False
        for key in old:
            if tuple(s for s in trips[key] if s not in selected) != tuple(s for s in old[key] if s not in selected):
                return False
    return True


def complete(p, original, local, decision):
    """FCFS over ready trips, one loading at a time per actual berth.

    Same-vehicle second trips are released only after first-trip return.
    Cross-vehicle targets retain their respective vehicle and trip identities.
    No CP route-pool solver is called (it could reassign quantum decisions).
    """
    from kmd_toc.pipeline.completion import assemble
    from kmd_toc.common.config import load_conditions
    o = load_conditions()['operations']
    routes = pinned_routes(original, local, decision)
    index = {s: i for i, s in enumerate(p.od.ids)}
    vehicle_index = {v.vehicle_id: i for i, v in enumerate(p.vehicles)}
    if any(not route for route in routes.values()):
        raise ValueError('EMPTY_ACTIVE_TRIP')
    demands = {s.stop_id: s.demand for s in p.stops}
    for (vid, _), route in routes.items():
        demand = sum(demands[j] for j in route)
        if demand > p.vehicles[vehicle_index[vid]].capacity:
            raise ValueError('CAPACITY')
    pending = dict(routes)
    previous = {}
    free = [b.opening_s for b in sorted(p.berths, key=lambda b: b.berth_id)]
    assignments = []
    while pending:
        available = []
        for key in pending:
            vid, number = key
            if number == 1:
                ready = p.vehicles[vehicle_index[vid]].first_ready_s
            elif (vid, number - 1) in previous:
                ready = previous[vid, number - 1] + o['preparation_s']
            else:
                continue
            available.append((ready, key))
        if not available:
            raise ValueError('TRIP_CONNECTION')
        ready, key = min(available)
        berth = min(range(len(free)), key=lambda b: (free[b], b))
        start = max(ready, free[berth])
        free[berth] = start + o['loading_s']
        route = tuple(index[s] for s in pending.pop(key))
        nodes = (0, *route, 0)
        import math
        travel = sum(math.ceil(float(p.od.duration_s[a, b])) for a, b in zip(nodes, nodes[1:]))
        previous[key] = start + o['loading_s'] + travel + o['service_s'] * len(route)
        assignments.append({'v': vehicle_index[key[0]], 'trip_no': key[1], 'route': route, 'start_s': start})
    return assemble(p, assignments, 'D', {'purpose': 'design_validation_only', 'completion': 'pinned_FCFS',
                                       'quantum_origin': 'decision supplied; caller records actual source'})


def physical(p, plan):
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.program_validation import audit_plan
    a, b = validate_plan(p, plan).as_dict(), audit_plan(p, plan)
    ok = a['feasible'] and b['feasible'] and abs(a['D_km'] - float(b['D_km'])) <= 1e-7 and a['W_min'] == float(b['W_min'])
    return ok, {'common': a, 'independent': b}


def metrics_units(p, plan):
    """Compare at common completion precision: 0.1 m, 1 s; no D/W weights."""
    index = {s: i for i, s in enumerate(p.od.ids)}
    distance = Decimal(0)
    for t in plan.trips:
        nodes = (p.depot.depot_id, *(v.stop_id for v in t.visits), p.depot.depot_id)
        distance += sum((Decimal(str(p.od.distance_m[index[a], index[b]])) for a, b in zip(nodes, nodes[1:])), Decimal(0))
    return int((distance * 10).to_integral_value(rounding=ROUND_HALF_EVEN)), sum(t.load_start_s - t.ready_s for t in plan.trips)


def pareto(old, new):
    d, w = new[0] - old[0], new[1] - old[1]
    if d <= 0 and w <= 0 and (d < 0 or w < 0):
        status = 'ACCEPT'
    elif d == 0 and w == 0:
        status = 'EQUAL_KEEP_INCUMBENT'
    elif (d < 0 < w) or (w < 0 < d):
        status = 'SAVE_NONDOMINATED'
    else:
        status = 'REJECT_DOMINATED'
    return {'status': status, 'delta_D_0_1m': d, 'delta_W_s': w}


def evaluate(p, original, local, decision, completer=complete):
    """Single gateway: invalid/infeasible candidates never update the plan."""
    start = perf_counter()
    ledger = {'quantum_decision': {'trip_1': list(decision.trip_1), 'trip_2': list(decision.trip_2)},
              'rule_status': 'PROPOSED', 'candidate_plan': None, 'reason': None}
    if (local.plan_reference.get('problem_hash') != p.fingerprint or
            local.plan_reference.get('plan_id') != original.plan_id or
            local.plan_reference.get('od_hash') != p.od.fingerprint):
        return original, {**ledger, 'status': 'REJECT_STALE_INPUT', 'reason': 'local/plan/input identity mismatch'}
    try:
        decision.validate(local.customer_ids)
    except ValueError as e:
        return original, {**ledger, 'status': 'REJECT_DECODE', 'reason': str(e)}
    try:
        candidate = completer(p, original, local, decision)
    except (ValueError, KeyError) as e:
        return original, {**ledger, 'status': 'REJECT_COMPLETION', 'reason': str(e), 'completion_s': perf_counter() - start}
    ledger['completion_s'] = perf_counter() - start
    if not preserves(candidate, local, decision, original):
        return original, {**ledger, 'status': 'REJECT_QUANTUM_DECISION_CHANGED', 'reason': 'assignment/order/outside route changed'}
    start = perf_counter()
    ok, checks = physical(p, candidate)
    old_ok, old_checks = physical(p, original)
    ledger.update(validation_s=perf_counter() - start, checks=checks)
    if not old_ok:
        return original, {**ledger, 'status': 'REJECT_INVALID_INCUMBENT', 'reason': old_checks}
    if not ok:
        return original, {**ledger, 'status': 'REJECT_PHYSICAL', 'reason': checks}
    start = perf_counter()
    result = pareto(metrics_units(p, original), metrics_units(p, candidate))
    ledger.update(result, DW_recalculation_s=perf_counter() - start, candidate_plan=candidate.plan_id,
                  reason='full plan D/W after pinned completion; distances and loading schedule can trade off')
    if result['status'] == 'SAVE_NONDOMINATED':
        ledger['nondominated_plan_payload'] = asdict(candidate)
    start = perf_counter()
    selected = candidate if result['status'] == 'ACCEPT' else original
    ledger['plan_update_s'] = perf_counter() - start
    return selected, ledger
