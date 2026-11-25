"""Selection-only replay of actual saved trip/customer IDs; never solves VRP."""
from itertools import combinations
from time import perf_counter
import json


def catalogue(p, plan):
    index = {s: i for i, s in enumerate(p.od.ids)}
    routes = {}
    gain = {}
    for t in plan.trips:
        key = (t.vehicle_id, t.trip_no)
        route = tuple(v.stop_id for v in t.visits)
        routes[key] = route
        nodes = (p.depot.depot_id, *route, p.depot.depot_id)
        for a, s, b in zip(nodes, nodes[1:], nodes[2:]):
            i, j, k = index[a], index[s], index[b]
            gain[s] = float(p.od.distance_m[i, j] + p.od.distance_m[j, k] - p.od.distance_m[i, k])
    return routes, gain


def choose(routes, gain, seen, n, rule='hybrid'):
    if rule not in ('hybrid', 'unseen', 'gain'):
        raise ValueError('SELECTION_RULE')
    unseen = {k: sum(s not in seen for s in route) for k, route in routes.items()}
    potential = {k: sum(gain[s] for s in route) for k, route in routes.items()}
    pairs = [(a, b) for a, b in combinations(sorted(routes), 2) if len(routes[a]) + len(routes[b]) >= n]
    if not pairs:
        return None
    def key(pair):
        a, b = pair
        u, g = unseen[a] + unseen[b], potential[a] + potential[b]
        return (-g, pair) if rule == 'gain' else (-u, pair) if rule == 'unseen' else (-u, -g, pair)
    pair = min(pairs, key=key)
    ids = routes[pair[0]] + routes[pair[1]]
    def customer_key(s):
        return (-gain[s], s) if rule == 'gain' else (s in seen, s) if rule == 'unseen' else (s in seen, -gain[s], s)
    return pair, tuple(sorted(ids, key=customer_key)[:n])


def replay(p, plan, n, K, P, R, rule='hybrid', scale=None):
    """Identical saved branch snapshot => identical ID replay in all P branches.

    Actual production branch trajectories and plan updates remain unmeasured.
    Never multiply unique coverage by P, or call R a statistical replication.
    """
    routes, gain = catalogue(p, plan)
    seen = set()
    rows = []
    elapsed = 0.
    all_ids = {s.stop_id for s in p.stops}
    cumulative = 0
    for cycle in range(1, R + 1):
        start = perf_counter()
        cycle_seen = set()
        selected = []
        same = cross = failed = repeated_slots = 0
        repeated_ids = set()
        for _ in range(K):
            item = choose(routes, gain, seen, n, rule)
            if item is None:
                failed += 1
                continue
            pair, ids = item
            same += pair[0][0] == pair[1][0]
            cross += pair[0][0] != pair[1][0]
            repeated_ids.update(s for s in ids if s in seen)
            repeated_slots += sum(s in seen for s in ids)
            seen.update(ids)
            cycle_seen.update(ids)
            selected.append({'trips': pair, 'customer_ids': ids})
        elapsed += perf_counter() - start
        cumulative += len(selected)
        assert seen <= all_ids
        row = {'scale': scale or p.experiment.scenario_id, 'rule': rule, 'n': n, 'K': K, 'P': P,
               'R': cycle, 'cycle': cycle, 'local_problems_per_branch': len(selected),
               'cumulative_local_problems_per_branch': cumulative, 'Q_calls': P * cumulative,
               'selection_slots_per_branch': n * len(selected), 'cycle_unique_customers': len(cycle_seen),
               'unique_customers': len(seen), 'coverage': len(seen) / len(all_ids),
               'cycle_coverage': len(cycle_seen) / len(all_ids),
               'reexplored_customers_cycle': len(repeated_ids), 'reexplored_slots_cycle': repeated_slots,
               'duplicate_fraction': (n * cumulative - len(seen)) / (n * cumulative) if cumulative else 0,
               'unexplored_customers': len(all_ids - seen), 'same_vehicle_problems_cycle': same,
               'cross_vehicle_problems_cycle': cross, 'failed_local_constructions_cycle': failed,
               'selection_wall_s_per_branch': elapsed, 'selected': selected,
               'feasible_candidate_rate': None, 'completion_rejection_rate': None, 'DW_stagnation': None,
               'scope': 'saved_plan_selection_replay_without_updates_not_quantum_optimization',
               'outer_statistical_repetitions': 0, 'union_across_P_identical_replays': len(seen)}
        assert row['Q_calls'] == P * K * cycle if not failed else True
        rows.append(row)
    return rows


def csv_row(row):
    result = dict(row)
    result['selected_customer_ids'] = json.dumps([s for item in row['selected'] for s in item['customer_ids']])
    result['selected_trip_pairs'] = json.dumps([item['trips'] for item in row['selected']])
    del result['selected']
    return result
