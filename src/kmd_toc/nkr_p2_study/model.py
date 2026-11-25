"""Fixed selector/completer/oracle contract for the entire new pilot."""
from dataclasses import asdict
from itertools import combinations
import math
import time

import numpy as np

from kmd_toc.d_local_design.coverage import catalogue
from kmd_toc.d_local_design.completion import extract, pinned_routes, complete, preserves, physical
from kmd_toc.cargo_wait_v2.evaluation import evaluate


def dw(p, plan):
    m = evaluate(p, plan)
    if m['missing_operation_count']:
        raise ValueError('MISSING_WAIT_DATA')
    return {k: m[k] for k in ('D_km', 'W_total_min', 'W_mean_min_per_operation', 'operation_count',
        'loading_W_min', 'unloading_W_min', 'other_W_min', 'wait_incidence_pct', 'evaluation_version', 'model_hash')}


def relation(a, b):
    d = b['D_km'] - a['D_km']; w = b['W_mean_min_per_operation'] - a['W_mean_min_per_operation']
    return 'ACCEPT' if d <= 0 and w <= 0 and (d < 0 or w < 0) else 'TRADEOFF' if (d < 0 < w or w < 0 < d) else 'EQUAL' if d == w == 0 else 'DOMINATED'


def classification(a, b):
    d = round((b['D_km'] - a['D_km']) * 10000)
    w = round((b['W_total_min'] - a['W_total_min']) * 60)
    if d < 0 and w < 0: return 'BOTH_STRICT'
    if d < 0 and w == 0: return 'D_ONLY'
    if w < 0 and d == 0: return 'W_ONLY'
    if d == w == 0: return 'EQUAL'
    if d * w < 0: return 'TRADEOFF'
    return 'WORSE'


def seed_for(outer, branch, r, k):
    return int(np.random.SeedSequence([outer, branch, r, k]).generate_state(1)[0])


def pick(p, plan, seen, n, seed):
    routes, gain = catalogue(p, plan)
    sizes = (n // 2, n - n // 2)
    candidates = []
    for pair in combinations(sorted(routes), 2):
        if any(len(routes[key]) < count for key, count in zip(pair, sizes)): continue
        ids = tuple(s for key, count in zip(pair, sizes)
                    for s in routes[key][(len(routes[key]) - count)//2:(len(routes[key]) - count)//2 + count])
        priority = (-sum(s not in seen for s in ids), -sum(gain[s] for key in pair for s in routes[key]), pair)
        candidates.append((priority, pair, ids))
    if not candidates: return None
    _, pair, ids = min(candidates)
    return extract(p, plan, pair, ids, seed)


def full_distance_m(p, routes):
    index = {s: i for i, s in enumerate(p.od.ids)}
    return math.fsum(float(p.od.distance_m[index[a], index[b]])
        for route in routes.values() for a, b in zip((p.depot.depot_id, *route), (*route, p.depot.depot_id)))


def validate_oracle(p, plan, local, q, lookup, random_checks=12):
    original = q.decode_register(q.encode_labels(q.initial_order(local)), local.customer_ids)
    old_routes = {(t.vehicle_id, t.trip_no): tuple(v.stop_id for v in t.visits) for t in plan.trips}
    assert pinned_routes(plan, local, original) == old_routes
    constant = full_distance_m(p, old_routes) - q.lookup_cost(q.initial_order(local), lookup)
    rng = np.random.default_rng(20261120)
    residual = 0.
    for _ in range(random_checks):
        labels = tuple(map(int, rng.permutation(local.n + 1)))
        decision = q.decode_register(q.encode_labels(labels), local.customer_ids)
        residual = max(residual, abs(full_distance_m(p, pinned_routes(plan, local, decision)) - q.lookup_cost(labels, lookup) - constant))
    if residual > 1e-7: raise ValueError('BOUNDARY_ORACLE_MISMATCH')
    return {'incumbent_representable': True, 'random_permutation_checks': random_checks,
            'boundary_residual_m': residual, 'constant_outside_m': constant}


def unconstrained_bound(local, lookup):
    """Independent subset DP, diagnostic only; no solution is supplied to QAOA."""
    n = local.n; full = (1 << n) - 1; edge = np.asarray(lookup['edge']); costs = []
    for which in (0, 1):
        start = np.asarray(lookup['first'][1:] if which == 0 else edge[0, 1:])
        end = np.asarray(edge[1:, 0] if which == 0 else lookup['last'][1:])
        dp = {(1 << j, j): float(start[j]) for j in range(n)}
        best = {0: float(lookup['first'][0] if which == 0 else lookup['last'][0])}
        for mask in range(1, 1 << n):
            for j in range(n):
                if not mask & (1 << j): continue
                rest = mask ^ (1 << j)
                if rest: dp[mask, j] = min(dp[rest, k] + edge[k + 1, j + 1] for k in range(n) if rest & (1 << k))
            best[mask] = min(dp[mask, j] + end[j] for j in range(n) if mask & (1 << j))
        costs.append(best)
    return min(costs[0][mask] + costs[1][full ^ mask] for mask in range(1 << n))


def assess(p, incumbent, local, decoded, save_candidate, limit=3):
    base = dw(p, incumbent); chosen = incumbent; current = base; ledger = []
    timing = dict(screen_s=0., completion_s=0., validation_s=0., reevaluation_s=0., acceptance_s=0., save_s=0.)
    demand = {s.stop_id: s.demand for s in p.stops}; capacity = {v.vehicle_id: v.capacity for v in p.vehicles}
    routes = {(t.vehicle_id, t.trip_no): [v.stop_id for v in t.visits] for t in incumbent.trips}
    ids = set(local.customer_ids); checked = 0; screened = 0
    for energy, bits, decision, count in decoded:
        start = time.perf_counter()
        bad = any(sum(demand[s] for s in routes[key] if s not in ids) + sum(demand[s] for s in route) > capacity[key[0]]
                  for key, route in zip(local.trip_ids, (decision.trip_1, decision.trip_2)))
        timing['screen_s'] += time.perf_counter() - start
        if bad: screened += 1; continue
        if checked >= limit: break
        checked += 1
        row = {'bits': bits, 'count': count, 'decision': asdict(decision), 'proxy': energy}
        start = time.perf_counter()
        try: proposal = complete(p, incumbent, local, decision)
        except ValueError as error:
            timing['completion_s'] += time.perf_counter() - start
            ledger.append({**row, 'status': 'COMPLETION_REJECT', 'reason': str(error)}); continue
        timing['completion_s'] += time.perf_counter() - start
        start = time.perf_counter(); ok, checks = physical(p, proposal)
        ok = ok and preserves(proposal, local, decision, incumbent)
        timing['validation_s'] += time.perf_counter() - start
        if not ok:
            ledger.append({**row, 'status': 'PHYSICAL_REJECT', 'checks': checks}); continue
        start = time.perf_counter(); metrics = dw(p, proposal)
        timing['reevaluation_s'] += time.perf_counter() - start
        start = time.perf_counter(); status = relation(base, metrics)
        if status == 'ACCEPT' and relation(current, metrics) == 'ACCEPT': chosen, current = proposal, metrics
        timing['acceptance_s'] += time.perf_counter() - start
        start = time.perf_counter(); path = save_candidate(checked, proposal)
        timing['save_s'] += time.perf_counter() - start
        ledger.append({**row, 'status': status, 'metrics': metrics, 'classification': classification(base, metrics), 'plan': path})
    return chosen, {'checked': checked, 'capacity_screened': screened, 'feasible_checked': sum('metrics' in row for row in ledger),
                    'plan_yield': any('metrics' in row for row in ledger), 'ledger': ledger, 'timing': timing}


def coverage(sets, N):
    E = sum(map(len, sets)); U = len(set().union(*sets)) if sets else 0
    return {'E': E, 'U': U, 'coverage': U / N, 'repeat_rate': 1 - U / E if E else None}
