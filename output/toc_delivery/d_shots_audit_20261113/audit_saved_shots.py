"""Read-only saved-result audit plus small fixed 12-qubit state replays.

Never invokes optimization, day column generation, or a full delivery experiment.
New files are written only beneath this audit directory.
"""
import csv
import hashlib
import inspect
import itertools
import json
import math
import platform
import resource
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
import qiskit
from scipy.stats import binomtest, beta
from qiskit.quantum_info import Statevector
from kmd_toc.common.models import load_problem
from kmd_toc.common.adapters import to_vehicle_day
from kmd_toc.column_generation.models import Route
from kmd_toc.column_generation.reduction import contract
from kmd_toc.column_generation.aoa import AOAConfig, PricingAOA

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
OLD = REPO / 'output/toc_delivery/ad_pipeline_20261112_route_v2'
NS = [1024, 4096, 8192, 10000, 16384, 32768]
CHECKS = []


def check(label, value):
    CHECKS.append({'check': label, 'passed': bool(value)})


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                                      default=lambda x: x.item() if isinstance(x, np.generic) else list(x)) + '\n')


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list, tuple)) else v for k, v in row.items()})


def ci(k, n):
    interval = binomtest(k, n).proportion_ci(confidence_level=.95, method='exact')
    return [float(interval.low), float(interval.high)]


def hit(probability, shots):
    if probability <= 0: return 0.
    if probability >= 1: return 1.
    return -math.expm1(shots * math.log1p(-probability))


def independent_decode(mask, groups, cfg, demands):
    """Decode bit positions directly without using production decode or maps."""
    n = len(groups) + 1
    sequence = [0]
    for slot in range(cfg.slots - 1):
        active = [node for node in range(n) if (mask >> (slot * n + node)) & 1]
        if len(active) != 1: return None, 'ONE_HOT_VIOLATION', None
        sequence.append(active[0])
    nonzero = [x for x in sequence if x != 0]
    if not nonzero: return sequence, 'EMPTY_WALK', None
    if len(nonzero) != len(set(nonzero)): return sequence, 'REPEATED_CUSTOMER', None
    if sum(demands[x] for x in nonzero) > 60: return sequence, 'CAPACITY_EXCEEDED', None
    if len(nonzero) == len(groups):
        return sequence, 'VALID', tuple(v for x in nonzero for v in groups[x - 1])
    return sequence, 'VALID', None


def main():
    begin = time.perf_counter()
    settings = json.loads((REPO / 'configs/toc_delivery/ad_pipeline_v2_route.json').read_text())
    snapshot_checks = []
    for rel in ['src/kmd_toc/column_generation/aoa.py', 'src/kmd_toc/pipeline/hybrid.py',
                'src/kmd_toc/pipeline/execution.py', 'configs/toc_delivery/ad_pipeline_v2_route.json']:
        same = (REPO / rel).read_bytes() == (OLD / 'SOURCE_SNAPSHOT' / rel).read_bytes()
        check('live/source-snapshot match:' + rel, same)
        snapshot_checks.append({'path': rel, 'matches_saved_snapshot': same})
    write_json('SOURCE_SNAPSHOT_COMPARISON.json', snapshot_checks)

    summaries = []
    for path in sorted((OLD / 'experiments/S1').glob('D*/result.json')):
        r = json.loads(path.read_text()); m = r['plan']['method_settings']; qs = m['quantum']
        histories = [h for q in qs for h in q['result']['history']]
        for q in qs:
            x = q['result']; cfg = x['config']
            check(path.parent.name + f":logged_final_sum:{q['iteration']}:{q['route_index']}",
                  sum(sum(h['qiskit_counts'].values()) for h in x['history']) == x['measured_shots'] == cfg['final_shots'] * cfg['restarts'])
            for key in ['p', 'restarts', 'train_shots', 'final_shots', 'max_evaluations']:
                check(path.parent.name + f":config:{key}:{q['iteration']}:{q['route_index']}", cfg[key] == settings['D'][key])
            check(path.parent.name + f":nfev:{q['iteration']}:{q['route_index']}", all(h['nfev'] == len(h['evaluations']) for h in x['history']))
        training = sum(q['result']['config']['train_shots'] * sum(h['nfev'] for h in q['result']['history']) for q in qs)
        final = sum(q['result']['measured_shots'] for q in qs)
        seed = {tuple(x) for x in m['seed_routes']}
        obtained = {tuple(x) for q in qs for x in q['full_route_obtained']}
        summaries.append({
            'condition': path.parent.name, 'primary': r['primary'], 'other_limit': r['other_limit'],
            'input_hash': r['input_hash'], 'OD_hash': r['OD_hash'],
            'AOA_calls': len(qs), 'actual_Qiskit_state_preparations': len(histories),
            'tensor_objective_evaluations': sum(h['nfev'] for h in histories),
            'training_simulated_shots': training, 'final_sampled_shots': final,
            'total_measurement_equivalent_draws': training + final,
            'hardware_measurements': 0, 'raw_decode_valid_shots': sum(q['result']['feasible_shots'] for q in qs),
            'proxy_negative_reduced_cost_shots': sum(q['result']['improving_shots'] for q in qs),
            'quantum_complete_macro_routes': len(obtained), 'finite_macro_route_domain': m['macro_full_routes_total'],
            'new_quantum_routes': len(obtained - seed), 'classical_seed_routes': len(seed),
            'seed_routes_not_sampled_by_quantum': len(seed - obtained), 'union_route_pool': len(seed | obtained),
            'base_day_catalogue': len(m['base']['LP']['rc']), 'hybrid_day_catalogue': m['day_columns'],
            'base_zero_RC_added': m['base']['zero_face_added'], 'hybrid_zero_RC_added': m['hybrid']['zero_face_added'],
            'D_km': r['D_km'], 'W_min': r['W_min'], 'T_program_s': r['T_program_s'],
            'training_wall_s': sum(q['result']['training_seconds'] for q in qs),
            'qiskit_final_decode_wall_s': sum(q['result']['qiskit_seconds'] for q in qs),
            'AOA_total_wall_s': sum(q['result']['total_seconds'] for q in qs),
            'selected_new_AOA_routes': None,
        })
    attribution = json.loads((OLD / 'D_ATTRIBUTION_AUDIT/SUMMARY.json').read_text())
    for s in summaries:
        a = next(x for x in attribution if x['condition'] == s['condition'])
        s['selected_new_AOA_routes'] = a['new_AOA_routes_selected']
        s['final_D_improvement_from_AOA_candidate_pool_km'] = a['D_improvement_from_candidate_pool_km']
        s['final_W_improvement_from_AOA_candidate_pool_min'] = a['W_improvement_from_candidate_pool_min']
    write_csv('S1_ALL_CONDITIONS.csv', summaries)
    write_json('S1_ALL_CONDITIONS.json', summaries)

    saved = json.loads((OLD / 'experiments/S1/D_primaryD_epsW_1/result.json').read_text())
    meta = saved['plan']['method_settings']
    p = load_problem(OLD / 'roads/inputs/S1'); day = to_vehicle_day(p, delta_s=1)
    check('same input instance as saved S1', p.fingerprint == saved['input_hash'] and p.od.fingerprint == saved['OD_hash'])
    source_routes = {tuple(x) for x in meta['seed_routes']}
    positions = {sid: i for i, sid in enumerate(p.od.ids)}
    final_routes = {tuple(positions[v['stop_id']] for v in t['visits']) for t in saved['plan']['trips']}
    b = json.loads((OLD / 'experiments/S1/B_primaryD_epsW_1/result.json').read_text())
    check('B and D seed physical trip plans match', b['plan']['trips'] == meta['seed_plan']['trips'])
    route_signature = lambda t: tuple(v['stop_id'] for v in t['visits'])
    b_by_route = {route_signature(t): t for t in b['plan']['trips']}
    d_by_route = {route_signature(t): t for t in saved['plan']['trips']}
    check('D final unordered route set matches B', b_by_route.keys() == d_by_route.keys())
    write_json('B_D_PLAN_LINEAGE.json', {
        'B_plan_equals_D_classical_seed_physical_trips': b['plan']['trips'] == meta['seed_plan']['trips'],
        'B_plan_equals_D_final_physical_trips': b['plan']['trips'] == saved['plan']['trips'],
        'B_D_unordered_route_set_equal': b_by_route.keys() == d_by_route.keys(),
        'unchanged_vehicle_trip_assignments': sum((b_by_route[k]['vehicle_id'], b_by_route[k]['trip_no']) ==
            (d_by_route[k]['vehicle_id'], d_by_route[k]['trip_no']) for k in b_by_route),
        'unchanged_loading_starts': sum(b_by_route[k]['load_start_s'] == d_by_route[k]['load_start_s'] for k in b_by_route),
        'routes': len(b_by_route),
        'interpretation': 'B routes and classical seed reused; day-master changes assignments/calendar. Equal D/W does not imply identical physical plans.'
    })
    calls, bits_rows, targets, macro_by_route, frozen = [], [], [], {}, []
    for q in meta['quantum']:
        cid = f"round{q['iteration']}_route{q['route_index']}"
        result = q['result']; cfg = AOAConfig(**result['config']); history = result['history'][0]
        groups = tuple(tuple(g) for g in q['fragment_groups'])
        dom = contract(day.base, meta['base']['LP']['dual_customer'], groups, cid, slots=len(groups) + 1)
        model = PricingAOA(dom.pricing, dom.dual, cfg)
        angles = history['optimized_angles']
        t0 = time.perf_counter(); qc = model.circuit(angles); state = Statevector.from_instruction(qc)
        vector_wall = time.perf_counter() - t0
        tensor = model.tensor_state(angles)
        check(cid + ':tensor/statevector fidelity', abs(abs(np.vdot(tensor, state.data[model.indices])) ** 2 - 1) < 1e-9)
        check(cid + ':saved logical depth', qc.depth() == result['logical_depth'])
        check(cid + ':free angle count', len(angles) == 2 * cfg.p == 4 and qc.num_parameters == 0)

        # Reproduce the training RNG draws at SAVED angles, not optimize angles.
        rng = np.random.default_rng(np.random.SeedSequence(cfg.solver_seed).spawn(cfg.restarts)[0])
        max_mean_error = 0.
        for ev in history['evaluations']:
            pr = np.abs(model.tensor_state(ev['angles'])) ** 2; pr /= pr.sum()
            count = rng.multinomial(cfg.train_shots, pr)
            max_mean_error = max(max_mean_error, abs(float(count @ model.energy / cfg.train_shots) - ev['sample_mean']))
        derived_final_seed = int(rng.integers(0, 2 ** 31))
        state.seed(derived_final_seed)
        t0 = time.perf_counter(); replay = dict(state.sample_counts(cfg.final_shots)); sample_wall = time.perf_counter() - t0
        check(cid + ':training means replay', max_mean_error < 1e-9)
        check(cid + ':final counts replay exactly', replay == history['qiskit_counts'])

        # Audit every supported one-hot basis element, including zero observations.
        full_expected, reasons, accepted_set = {}, Counter(), set()
        empirical = history['qiskit_counts']
        minimum_cost = math.inf
        for order in itertools.permutations(range(len(groups))):
            full = tuple(v for k in order for v in groups[k])
            route_nodes = (0, *full, 0)
            cost = sum(day.base.distance[a, b] for a, b in zip(route_nodes, route_nodes[1:]))
            minimum_cost = min(minimum_cost, float(cost))
        parent = tuple(meta['seed_routes'][q['route_index']]); parent_nodes = (0, *parent, 0)
        parent_cost = float(sum(day.base.distance[a, b] for a, b in zip(parent_nodes, parent_nodes[1:])))
        event_probability = Counter(); event_count = Counter()
        for index in model.indices:
            mask = int(index); bits = format(mask, f'0{model.q}b')
            probability = float(abs(state.data[mask]) ** 2)
            count = int(empirical.get(bits, 0))
            seq, reason, full = independent_decode(mask, groups, cfg, dom.pricing.demand)
            reasons[reason] += count
            production, production_reason = model.decode(tuple(seq))
            check(cid + ':independent decoder:' + bits, production_reason == reason)
            flags = {'one_hot_bitstring': True, 'decoded_route_valid': reason == 'VALID',
                     'complete_macro_trip': full is not None, 'new_complete_macro_trip': full is not None and full not in source_routes,
                     'shorter_than_parent_trip': False, 'minimum_distance_macro_trip': False,
                     'proxy_negative_reduced_cost': False}
            if reason == 'VALID':
                # Independently compute macro path costs minus customer duals.
                segment, reduced = [], []
                for node in list(seq[1:]) + [0]:
                    if node: segment.append(node)
                    elif segment:
                        nodes = [0] + segment + [0]
                        reduced.append(sum(dom.pricing.distance[a, b] for a, b in zip(nodes, nodes[1:])) - sum(dom.dual[a - 1] for a in segment))
                        segment = []
                flags['proxy_negative_reduced_cost'] = any(rc < -1e-7 for rc in reduced)
            if full is not None:
                full_expected[full] = probability
                if count: accepted_set.add(full)
                nodes = (0, *full, 0)
                cost = float(sum(day.base.distance[a, b] for a, b in zip(nodes, nodes[1:])))
                flags['shorter_than_parent_trip'] = cost < parent_cost - 1e-7
                flags['minimum_distance_macro_trip'] = abs(cost - minimum_cost) < 1e-7
                macro = macro_by_route.setdefault(full, {'route_index': q['route_index'], 'route': list(full),
                    'distance_km': cost, 'parent_distance_km': parent_cost, 'already_classical_seed': full in source_routes,
                    'duration_s': int(sum(day.travel_s[a][b] for a, b in zip(nodes, nodes[1:]))) + 120 * len(full),
                    'selected_in_final': full in final_routes, 'observed_count_round0': 0, 'observed_count_round1': 0,
                    'probability_round0': 0., 'probability_round1': 0.})
                macro['observed_count_round' + str(q['iteration'])] += count
                macro['probability_round' + str(q['iteration'])] += probability
            for key, flag in flags.items():
                if flag:
                    event_probability[key] += probability
                    event_count[key] += count
            bits_rows.append({'call': cid, 'bitstring': bits, 'sequence': seq, 'observed_count': count,
                              'observed_frequency': count / cfg.final_shots, 'exact_ideal_probability': probability,
                              'reason': reason, **flags})
        check(cid + ':valid shot recount', reasons['VALID'] == result['feasible_shots'])
        check(cid + ':negative proxy shot recount', event_count['proxy_negative_reduced_cost'] == result['improving_shots'])
        check(cid + ':accepted full-route recount', accepted_set == {tuple(x) for x in q['full_route_obtained']})
        for key in ['one_hot_bitstring', 'decoded_route_valid', 'complete_macro_trip', 'new_complete_macro_trip',
                    'shorter_than_parent_trip', 'minimum_distance_macro_trip', 'proxy_negative_reduced_cost']:
            probability = float(event_probability[key]); k = int(event_count[key]); interval = ci(k, cfg.final_shots)
            targets.append({'call': cid, 'event': key, 'k': k, 'n': cfg.final_shots,
                            'observed_rate': k / cfg.final_shots, 'CP95_lower': interval[0], 'CP95_upper': interval[1],
                            'exact_ideal_probability': probability,
                            **{f'P_at_least_one_N{n}': hit(probability, n) for n in NS}})
        calls.append({'call': cid, 'qubits': model.q, 'logical_depth': qc.depth(), 'variational_angles': len(angles),
                      'train_shots': cfg.train_shots, 'nfev': history['nfev'], 'final_shots': cfg.final_shots,
                      'solver_seed': cfg.solver_seed, 'derived_final_seed': derived_final_seed,
                      'training_rng_replay_max_error': max_mean_error, 'counts_reproduced_exactly': replay == history['qiskit_counts'],
                      'observed_bitstring_kinds': len(empirical), 'complete_macro_kinds': len(accepted_set),
                      'complete_macro_shots': int(event_count['complete_macro_trip']),
                      'new_complete_macro_shots': int(event_count['new_complete_macro_trip']),
                      'shorter_parent_shots': int(event_count['shorter_than_parent_trip']),
                      'best_observed_macro_distance_km': min((macro_by_route[x]['distance_km'] for x in accepted_set), default=None),
                      'exact_best_macro_distance_km': minimum_cost,
                      'audit_only_rebuild_state_wall_s': vector_wall, 'audit_only_sample_wall_s': sample_wall})
        frozen.append({'call': cid, 'fragment_groups': groups, 'config': result['config'],
                       'optimized_angles': angles, 'derived_final_seed': derived_final_seed,
                       'pricing_distance': dom.pricing.distance.tolist(), 'pricing_demand': dom.pricing.demand,
                       'capacity': dom.pricing.capacity, 'dual': list(dom.dual),
                       'saved_final_counts_sha256': hashlib.sha256(json.dumps(history['qiskit_counts'], sort_keys=True).encode()).hexdigest()})

    write_csv('S1_KERNEL_CALLS.csv', calls)
    write_csv('S1_BITSTRING_FREQUENCIES.csv', bits_rows)
    write_csv('S1_EVENT_PROBABILITIES.csv', targets)
    write_csv('S1_MACRO_CANDIDATES.csv', list(macro_by_route.values()))
    write_json('S1_FROZEN_PARAMETER_BANK.json', frozen)
    projections = []
    for n in NS:
        candidate_probs = [1 - (1 - x['probability_round0']) ** n * (1 - x['probability_round1']) ** n for x in macro_by_route.values()]
        projections.append({'shots_per_kernel': n, 'kernels': len(calls), 'final_draws_one_bank': len(calls) * n,
                            'expected_unique_complete_macro_routes': sum(candidate_probs),
                            'expected_missing_macro_routes': len(macro_by_route) - sum(candidate_probs),
                            'data_kind': 'exact_ideal_fixed_parameter_prediction_NOT_shots_experiment'})
    write_csv('ANALYTIC_COVERAGE_PROJECTIONS.csv', projections)
    theory = []
    for n in NS:
        theory.append({'shots': n, 'p_required_for_95pct_hit': -math.expm1(math.log(.05) / n),
                       'P_hit_if_p_1e_4': hit(1e-4, n),
                       'zero_success_CP95_two_sided_upper': float(beta.ppf(.975, 1, n)),
                       'zero_success_CP95_one_sided_upper': -math.expm1(math.log(.05) / n),
                       'worst_case_Wilson95_halfwidth_shot_probability': 1.959963984540054 / (2 * math.sqrt(n + 1.959963984540054 ** 2))})
    write_csv('BINOMIAL_DESIGN.csv', theory)

    rep = []
    for n in [20, 30, 60, 100, 385]:
        rep.append({'independent_repetitions': n, 'all_successes_one_sided_CP95_lower': .05 ** (1 / n),
                    'zero_successes_one_sided_CP95_upper': 1 - .05 ** (1 / n),
                    'worst_case_Wilson95_halfwidth': 1.959963984540054 / (2 * math.sqrt(n + 1.959963984540054 ** 2))})
    write_csv('REPETITION_PRECISION.csv', rep)

    # Tiny distinct sampling streams; same seeds test debugging only.
    seed_children = np.random.SeedSequence(2026111309).spawn(3)
    trial_seeds = [int(s.generate_state(1, dtype=np.uint64)[0]) for s in seed_children]
    small = Statevector(np.sqrt(np.array([.1, .2, .3, .4])))
    small.seed(trial_seeds[0]); a = dict(small.sample_counts(1024))
    small.seed(trial_seeds[0]); again = dict(small.sample_counts(1024))
    small.seed(trial_seeds[1]); other = dict(small.sample_counts(1024))
    check('tiny fixed-seed exact debug reproduction', a == again)
    check('tiny spawned seeds distinct', len(set(trial_seeds)) == 3)
    check('tiny independent-stream counts sum', sum(a.values()) == sum(other.values()) == 1024)
    check('tiny probability state unmodified by sampling', np.allclose(small.probabilities(), [.1, .2, .3, .4]))
    write_json('TINY_SAMPLING_CHECK.json', {'shots': 1024, 'seeds': trial_seeds, 'first': a, 'same_seed': again,
                                          'different_seed': other, 'purpose': 'debug functionality only, not performance replicates'})
    (OUT / 'INSTALLED_STATEVECTOR_SAMPLE_COUNTS.py.txt').write_text(inspect.getsource(Statevector.sample_counts))

    current = next(x for x in summaries if x['condition'] == 'D_primaryD_epsW_1')
    summary = {'S1_main': current, 'kernel_count': len(calls), 'logical_depth_range': [min(x['logical_depth'] for x in calls), max(x['logical_depth'] for x in calls)],
               'qubit_range': [min(x['qubits'] for x in calls), max(x['qubits'] for x in calls)],
               'nfev_range': [min(x['nfev'] for x in calls), max(x['nfev'] for x in calls)],
               'complete_macro_shots': sum(x['complete_macro_shots'] for x in calls),
               'new_complete_macro_shots': sum(x['new_complete_macro_shots'] for x in calls),
               'shorter_parent_shots': sum(x['shorter_parent_shots'] for x in calls),
               'shorter_parent_macro_routes_in_exact_domain': sum(x['distance_km'] < x['parent_distance_km'] - 1e-7 for x in macro_by_route.values()),
               'equal_parent_macro_routes_in_exact_domain': sum(abs(x['distance_km'] - x['parent_distance_km']) <= 1e-7 for x in macro_by_route.values()),
               'minimum_positive_parent_distance_delta_km': min(x['distance_km'] - x['parent_distance_km'] for x in macro_by_route.values() if x['distance_km'] - x['parent_distance_km'] > 1e-7),
               'minimum_original_route_duration_s': min(x['duration_s'] for x in macro_by_route.values() if x['already_classical_seed']),
               'minimum_all_macro_route_duration_s': min(x['duration_s'] for x in macro_by_route.values()),
               'exact_domain_count': len(macro_by_route),
               'observed_complete_macro_routes': sum(x['observed_count_round0'] + x['observed_count_round1'] > 0 for x in macro_by_route.values()),
               'minimum_macro_candidate_probability': min(min(x['probability_round0'], x['probability_round1']) for x in macro_by_route.values()),
               'max_macro_candidate_probability': max(max(x['probability_round0'], x['probability_round1']) for x in macro_by_route.values()),
               'all_saved_counts_reproduced': all(x['counts_reproduced_exactly'] for x in calls),
               'analytic_projections': projections, 'new_D_W_T_sensitivity_experiment_executed': False,
               'environment': {'python': sys.version, 'executable': sys.executable, 'numpy': np.__version__, 'scipy': scipy.__version__,
                               'qiskit': qiskit.__version__, 'platform': platform.platform(), 'generator': 'NumPy PCG64 / SeedSequence; Qiskit Statevector local RNG'},
               'audit_wall_s': time.perf_counter() - begin, 'audit_max_rss_KiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write_json('AUDIT_SUMMARY.json', summary)
    baseline = json.loads((OUT / 'PRESERVATION_BEFORE.json').read_text())
    changes = []
    for rel, expected in baseline['files'].items():
        path = REPO / rel
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected: changes.append(rel)
    check('235 protected existing files unchanged', not changes and len(baseline['files']) == 235)
    write_json('VALIDATION.json', {'checks': len(CHECKS), 'passed': sum(c['passed'] for c in CHECKS),
                                  'failed': [c for c in CHECKS if not c['passed']], 'changed_existing_files': changes,
                                  'details': CHECKS})
    print(json.dumps({k: v for k, v in summary.items() if k not in ['environment', 'analytic_projections']}, indent=2))
    print('checks', len(CHECKS), 'failures', sum(not x['passed'] for x in CHECKS))
    if any(not c['passed'] for c in CHECKS): raise SystemExit(1)


if __name__ == '__main__': main()
