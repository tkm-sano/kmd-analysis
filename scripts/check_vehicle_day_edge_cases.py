"""Supplemental order-sensitive/second-seed checks; preserves the first batch."""
import argparse
from dataclasses import replace
from pathlib import Path
import json
import hashlib
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.generation import enumerate_days
from kmd_toc.vehicle_day.master import reduced_cost
from kmd_toc.vehicle_day.runner import run_day_cg
from kmd_toc.vehicle_day.validation import independent_plan_oracle
from run_vehicle_day_validation import save


def main(output):
    out = Path(output)
    cfg = AOAConfig(slots=3, max_evaluations=80, restarts=1, solver_seed=2102)
    records = []
    for b in [1, 2]:
        p = small_problem(4, b)
        p = replace(p, travel_s=((0,120,240,120,240), (240,0,120,240,120),
                    (120,240,0,120,240), (240,120,240,0,120), (120,240,120,240,0)))
        columns = enumerate_days(p)
        save(out / f'INPUT_ORDER_SENSITIVE_B{b}.json', p)
        for primary in ['D', 'W']:
            profile = ObjectiveProfile(primary)
            r = run_day_cg(p, columns, profile)
            reference = independent_plan_oracle(p, columns, profile)
            assert reference['objective'] == r['full_grid_integer']['objective']
            r['independent_plan_reference'] = reference
            save(out / f'ORDER_SENSITIVE_B{b}_{primary}.json', r)
            records.append({'case': f'ORDER_SENSITIVE_B{b}_{primary}', 'passed': True})
    p = small_problem(6, 1)
    columns = enumerate_days(p)
    for primary in ['D', 'W']:
        r = run_day_cg(p, columns, ObjectiveProfile(primary), 'aoa', cfg)
        save(out / f'AOA_SECOND_SEED_N6_B1_{primary}.json', r)
        records.append({'case': f'AOA_SECOND_SEED_N6_B1_{primary}', 'valid': r['metrics']['valid'],
                        'integer_gap': r['integer_gap'], 'final_full_min_rc': r['final_full_oracle_min_rc']})
    # Explain the recorded first-seed miss without inserting its oracle column.
    original = json.loads((out / 'AOA_N6_B1_D.json').read_text())
    dual = original['final_lp']['dual']
    best = min(columns, key=lambda c: reduced_cost(p, c, dual, ObjectiveProfile('D')))
    last = original['trace'][-1]['aoa']
    sampled = {tuple(ids) for q in last['quantum'] for ids in q['expanded_sampled_trips']}
    subsets = [set(q['subset_original_ids']) for q in last['quantum']]
    explanation = {'full_best_day': best, 'true_day_rc': reduced_cost(p,best,dual,ObjectiveProfile('D')),
        'last_sampled_trips': sorted(sampled), 'last_candidate_subsets': [sorted(s) for s in subsets],
        'oracle_trips_sampled': [t.customers in sampled for t in best.trips],
        'oracle_trips_inside_any_subset': [any(set(t.customers) <= s for s in subsets) for t in best.trips],
        'not_a_global_certificate': True}
    save(out / 'AOA_MISS_EXPLANATION.json', explanation)
    save(out / 'SUPPLEMENT_ACCEPTANCE.json', {'cases': records,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
