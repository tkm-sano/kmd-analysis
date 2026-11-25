"""Independent decimal arc ledger and integer event checks, never a scheduler.

Tolerances apply only to floating point report reconciliation, never to physical
feasibility, local acceptance, or the exact final candidate ordering.
"""
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math

D_ATOL_KM = 1e-7
W_ATOL_MIN = 1e-9
DISTANCE_TRIP_ATOL_M = 1e-6


def digest_payload(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def physical_payload(plan):
    # IDs, generator labels and solver settings are not physical plan content.
    return {k: getattr(plan, k) if k not in ('trips', 'breaks') else
            [asdict(x) for x in getattr(plan, k)]
            for k in ('problem_hash', 'od_hash', 'trips', 'breaks') if hasattr(plan, k)}


def profile(p):
    duty = hasattr(p, 'rest_options')
    return {'problem_hash': p.fingerprint, 'od_hash': p.od.fingerprint,
            'operating_version': 'duty-break-20261121-v1' if duty else 'FCFS_v1',
            'duty_policy_sha256': getattr(p, 'activated_policy_sha256', None),
            'rest_options': p.rest_options.payload() if duty else None,
            'D_unit': 'km', 'W_unit': 'min_total_loading_wait'}


def independent(p, plan):
    """Reconstruct ledgers directly from directed OD and saved event times.

    No production metric/route-distance/FCFS/scheduler function is used here.
    The full versioned physical validator is separately called by cross_evaluate.
    """
    errors = []
    arcs, waits = [], []
    idx = {s: i for i, s in enumerate(p.od.ids)}
    vehicles = {v.vehicle_id: v for v in p.vehicles}
    berths = {b.berth_id: b for b in p.berths}
    depot = p.depot.depot_id
    if plan.problem_hash != p.fingerprint or plan.od_hash != p.od.fingerprint:
        errors.append('PHYSICAL_PROFILE_MISMATCH')
    counted = Counter(v.stop_id for t in plan.trips for v in t.visits)
    if counted != Counter({s.stop_id: 1 for s in p.stops}):
        errors.append('CUSTOMER_COVERAGE')
    keys = [(t.vehicle_id, t.trip_no) for t in plan.trips]
    if len(set(keys)) != len(keys): errors.append('DUPLICATE_TRIP')
    bykey = {(t.vehicle_id, t.trip_no): t for t in plan.trips}
    drive_intervals = defaultdict(list)
    for t in plan.trips:
        key = f'{t.vehicle_id}/{t.trip_no}'
        if not t.visits:
            errors.append('EMPTY_ACTIVE_TRIP:' + key)
            continue
        if t.vehicle_id not in vehicles or t.berth_id not in berths:
            errors.append('UNKNOWN_RESOURCE:' + key)
            continue
        if t.origin_id != depot or t.destination_id != depot:
            errors.append('DEPOT_ROUNDTRIP:' + key)
        expected_ready = (vehicles[t.vehicle_id].first_ready_s if t.trip_no == 1 else
                          getattr(bykey.get((t.vehicle_id, 1)), 'return_s', None))
        if expected_ready != t.ready_s: errors.append('READY_CONNECTION:' + key)
        wait_s = t.load_start_s - t.ready_s
        if wait_s < 0: errors.append('NEGATIVE_WAIT:' + key)
        if wait_s != t.waiting_s: errors.append('WAIT_FIELD:' + key)
        if t.departure_s != t.load_end_s: errors.append('IMMEDIATE_DEPARTURE:' + key)
        nodes = [depot, *(v.stop_id for v in t.visits), depot]
        distances = []
        for j, (a, b) in enumerate(zip(nodes, nodes[1:])):
            if a not in idx or b not in idx:
                errors.append('UNKNOWN_OD_NODE:' + key)
                continue
            d = Decimal(str(float(p.od.distance_m[idx[a], idx[b]])))
            if not d.is_finite() or d < 0 or not p.od.reachable[idx[a], idx[b]]:
                errors.append('INVALID_DIRECTED_OD:' + key)
                continue
            distances.append(d)
            secs = math.ceil(float(p.od.duration_s[idx[a], idx[b]]))
            # End of a drive is an arrival (or the final return), not service start.
            end = t.visits[j].arrival_s if j < len(t.visits) else t.return_s
            start = t.departure_s if j == 0 else t.visits[j-1].service_end_s
            # A rest after service delays the next drive by 3600 s.
            for br in getattr(plan, 'breaks', ()):
                if (br.vehicle_id == t.vehicle_id and br.trip_no == t.trip_no and
                        br.placement == 'after_delivery_service' and br.start_s == start):
                    start = br.end_s
            if end - start != secs: errors.append('DRIVE_INTERVAL:' + key)
            drive_intervals[t.vehicle_id].append((start, end, 'driving'))
            arcs.append({'vehicle_id': t.vehicle_id, 'trip_no': t.trip_no,
                         'arc_index': j, 'from_id': a, 'to_id': b,
                         'kind': 'outward' if j == 0 else 'return' if j == len(nodes)-2 else 'between',
                         'distance_m': str(d), 'D_km': float(d/1000),
                         'driving_s': secs, 'start_s': start, 'end_s': end})
        total_m = sum(distances, Decimal(0))
        if abs(total_m - Decimal(str(t.distance_m))) > Decimal(str(DISTANCE_TRIP_ATOL_M)):
            errors.append('SAVED_TRIP_DISTANCE:' + key)
        waits.append({'vehicle_id': t.vehicle_id, 'trip_no': t.trip_no,
                      'ready_s': t.ready_s, 'load_start_s': t.load_start_s,
                      'load_end_s': t.load_end_s, 'departure_s': t.departure_s,
                      'return_s': t.return_s, 'W_s': wait_s, 'W_min': wait_s/60,
                      'D_m': str(total_m), 'berth_id': t.berth_id})
    # Independent discrete FCFS replay from saved ready/return times, no repairs.
    pending = dict(bykey)
    free = {b.berth_id: b.opening_s for b in p.berths}
    done = set()
    while pending:
        released = [t for (v, k), t in pending.items() if k == 1 or (v, 1) in done]
        if not released:
            errors.append('FCFS_RELEASE_DEADLOCK')
            break
        t = min(released, key=lambda t: (t.ready_s, t.vehicle_id, t.trip_no))
        start = max(t.ready_s, min(free.values()))
        berth = min(b for b, available in free.items() if available <= start)
        if (t.load_start_s, t.berth_id) != (start, berth): errors.append('FCFS_ORDER')
        b = berths[berth]
        if t.load_end_s != start + b.loading_s or t.load_end_s > b.closing_s:
            errors.append('BERTH_WINDOW_OR_LOADING')
        free[berth] = start + b.loading_s
        done.add((t.vehicle_id, t.trip_no))
        pending.pop((t.vehicle_id, t.trip_no))
    for br in getattr(plan, 'breaks', ()):
        if br.end_s-br.start_s != 3600 or not 43200 <= br.start_s <= 46800 or br.end_s > 50400:
            errors.append('BREAK_WINDOW')
        activities = list(drive_intervals[br.vehicle_id])
        for t in plan.trips:
            if t.vehicle_id != br.vehicle_id: continue
            activities += [(t.ready_s, t.load_start_s, 'wait'),
                           (t.load_start_s, t.load_end_s, 'loading')]
            activities += [(v.service_start_s, v.service_end_s, 'service') for v in t.visits]
        if any(a < br.end_s and br.start_s < b for a, b, _ in activities if a < b):
            errors.append('BREAK_LABOUR_OVERLAP')
    D = sum((Decimal(a['distance_m']) for a in arcs), Decimal(0))/1000
    W_s = sum(r['W_s'] for r in waits)
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'D_km': float(D), 'W_total_min': W_s/60,
            'D_exact': str(Fraction(D)), 'W_exact': str(Fraction(W_s, 60)),
            'arcs': arcs, 'waits': waits,
            'physical_plan_hash': digest_payload(physical_payload(plan)),
            'profile': profile(p)}


def cross_evaluate(p, plan):
    """Relabel the SAME physical plan, not regenerate B/C/D solutions."""
    own = independent(p, plan)
    methods = {}
    for method in ('B', 'C', 'D'):
        relabeled = replace(plan, method_id=method,
                            execution_kind='quantum_circuit_simulator' if method == 'D' else 'classical')
        try:
            if hasattr(p, 'rest_options'):
                from kmd_toc.duty_break_v1.evaluation import evaluate
                result = evaluate(p, relabeled)
                d, w = result['D_km'], result['W_total_loading_min']
            else:
                from kmd_toc.fcfs_v1.evaluation import evaluate
                result = evaluate(p, relabeled)
                d, w = result['D_km'], result['W_min']
            ok = abs(d-own['D_km']) <= D_ATOL_KM and abs(w-own['W_total_min']) <= W_ATOL_MIN
            methods[method] = {'status': 'PASS' if ok else 'FAIL', 'D_km': d, 'W_total_min': w,
                               'profile': profile(p),
                               'stopping_site_feasibility': result.get('stopping_site_feasibility')}
        except (ValueError, KeyError) as error:
            methods[method] = {'status': 'FAIL', 'reason': str(error)}
    return {**own, 'status': 'PASS' if own['status'] == 'PASS' and
            all(r['status'] == 'PASS' for r in methods.values()) else 'FAIL',
            'cross_methods': methods,
            'interpretation': 'same physical plan; method metadata relabeled only; no optimizer invoked',
            'tolerance': {'D_km_absolute': D_ATOL_KM, 'W_min_absolute': W_ATOL_MIN,
                          'event_seconds': 0, 'local_acceptance': 'unchanged_exact_nonworsening'}}


def selection_key(candidate, c):
    """Independent exact implementation of frozen final selection ordering."""
    d, w = (Fraction(candidate[k]) for k in ('D_exact', 'W_exact'))
    dc, wc = (Fraction(c[k]) for k in ('D_exact', 'W_exact'))
    tail = (candidate['branch_id'] is not None, candidate['branch_id'] or 0)
    if dc > 0 and wc > 0:
        rd, rw = (dc-d)/dc, (wc-w)/wc
        return (-min(rd, rw), -(rd+rw), d, w, *tail)
    return ((w, d, *tail) if wc == 0 and dc > 0 else (d, w, *tail))


def dual_exact(c, x):
    dc, wc = (Fraction(c[k]) for k in ('D_exact', 'W_exact'))
    if dc <= 0 or wc <= 0: return None
    d, w = (Fraction(x[k]) for k in ('D_exact', 'W_exact'))
    return 100*min((dc-d)/dc, (wc-w)/wc)


def reference_group_metrics(group):
    """C supervisor stores metrics in the selected branch, not a selected field."""
    if group.get('status') != 'COMPLETE' or group.get('kind') != 'reference':
        raise ValueError('C_REFERENCE_GROUP_NOT_COMPLETE')
    selected = [b for b in group['branches'] if b['branch'] == group['selected_branch_id']]
    if len(selected) != 1 or selected[0]['status'] != 'COMPLETE':
        raise ValueError('C_REFERENCE_SELECTED_BRANCH_NOT_COMPLETE')
    return selected[0]['after']
