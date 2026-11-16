"""Joint finite observed-front analysis and reference/weight sensitivity."""
import csv
from collections import Counter
import json
from pathlib import Path
from .evaluation import eligible, pareto, score, KEYS
from .worker import dump


def csv_write(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                          for k, v in r.items()} for r in rows])


def analyze(root, config):
    root = Path(root)
    rows = [json.loads(p.read_text()) for p in sorted((root / 'trials').glob('*/metrics.json'))]
    simple = [{k: v for k, v in r.items() if k not in ['validation', 'second_validation', 'timing_events']} for r in rows]
    csv_write(root / 'ALL_TRIALS.csv', simple)
    dump(root / 'ALL_TRIALS.json', rows)
    limited = [r for r in rows if r['phase'] == 'limited']
    front, relations = pareto(limited)
    csv_write(root / 'NONDOMINATED.csv', [{k: r.get(k) for k in ['trial_id', 'scenario_id', 'method', 'epsilon_W_min', 'tau_s', *KEYS, 'input_hash']} for r in front],
              ['trial_id', 'scenario_id', 'method', 'epsilon_W_min', 'tau_s', *KEYS, 'input_hash'])
    csv_write(root / 'DOMINANCE.csv', relations, ['dominator', 'dominated', 'dominator_method', 'dominated_method'])
    matrix = Counter((r['dominator_method'], r['dominated_method']) for r in relations)
    csv_write(root / 'METHOD_DOMINANCE.csv', [{'dominator_method': a, 'dominated_method': b, 'observed_relations': matrix[a, b]}
              for a in ['B', 'C', 'D'] for b in ['B', 'C', 'D']])
    sensitivities = []
    for r in limited:
        ref = config['reference'].get(r['scenario_id'])
        if ref is None or r['method'] not in ('B', 'C', 'D'):
            continue
        for mul in config['T_reference_multipliers']:
            refs = {k: ref[k] for k in KEYS}
            refs['T_program_s'] *= mul
            for name, weights in config['weights'].items():
                sensitivities.append({'trial_id': r['trial_id'], 'method': r['method'], 'weight_profile': name,
                                      'T_ref_multiplier': mul, 'weights': weights, 'reference': refs,
                                      'J': score(r, refs, weights), 'eligible': eligible(r)})
    csv_write(root / 'WEIGHT_REFERENCE_SENSITIVITY.csv', sensitivities)
    summary = []
    for group in sorted({(r['scenario_id'], r['method'], r['epsilon_W_min'], r['tau_s']) for r in limited}):
        selected = [r for r in limited if (r['scenario_id'], r['method'], r['epsilon_W_min'], r['tau_s']) == group]
        valid = [r for r in selected if eligible(r)]
        summary.append({'scenario_id': group[0], 'method': group[1], 'epsilon_W_min': group[2], 'tau_s': group[3],
                        'attempts': len(selected), 'verified_plan_count': sum(bool(r.get('feasible')) for r in selected),
                        'operational_feasible_rate': sum(bool(r.get('feasible')) for r in selected) / len(selected),
                        'accepted_count': len(valid), 'accepted_rate': len(valid) / len(selected),
                        **{k + '_values': [r[k] for r in valid] for k in KEYS},
                        'failures': [r['status'] for r in selected if not eligible(r)]})
    csv_write(root / 'BUDGET_EPSILON_RESULTS.csv', summary)
    output = {'meaning': 'observed nondominated points in executed finite candidate/budget trials; no global optimality proof',
              'front_trial_ids': [r['trial_id'] for r in front], 'front_count_by_method': {m: sum(r['method'] == m for r in front) for m in ['B', 'C', 'D']},
              'total_trials': len(rows), 'limited_trials': len(limited), 'limited_eligible': sum(eligible(r) for r in limited),
              'quantization': dict(zip(KEYS, ['1e-7 km', '1e-7 min', '1e-6 s'])),
              'failed_trials_retained': True, 'A_program_human_scores_combined': False,
              'rows': [{k: r.get(k) for k in ['trial_id', 'scenario_id', 'phase', 'method', 'epsilon_W_min', 'tau_s', *KEYS, 'status', 'feasible']} for r in rows],
              'budget_epsilon_summary': summary, 'dominance': relations, 'weight_reference_sensitivity': sensitivities}
    dump(root / 'THREE_OBJECTIVE_EVALUATION.json', output)
    return output
