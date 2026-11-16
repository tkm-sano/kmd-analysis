"""Audit saved small results and measure exhaustive pricing on identical duals.

No optimizer on study data. Exact diagnostics are not injected into saved AOA CG.
Run after run_huang_reference.py; creates new files exclusively.
"""
import argparse
import csv
import json
from pathlib import Path
from time import perf_counter
from dataclasses import replace
import numpy as np
from kmd_toc.column_generation.models import artificial_instance, Instance, Route, enumerate_routes, reduced_cost
from kmd_toc.column_generation.master import solve_lp, solve_integer
from kmd_toc.column_generation.reduction import build_domains, exact_domain_routes
from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
from kmd_toc.column_generation.experiment import write_json
from kmd_toc.column_generation.runner import run_column_generation


def csv_write(path, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(directory):
    out = Path(directory)
    completion = json.loads((out / 'RUN_COMPLETION.json').read_text())
    assert completion['status'] == 'COMPLETED'
    checks, comparisons, pricing = [], [], []
    for path in sorted(out.glob('CG_AOA_*.json')):
        result = json.loads(path.read_text())
        m = int(path.name.split('_')[2])
        instance = artificial_instance(m)
        assert result['columns_added_by_aoa'] > 0
        assert result['integer']['exactly_once_verified']
        assert result['oracle_columns_injected'] is False
        assert result['stop_reason'] == 'AOA_NO_IMPROVING_COLUMN'
        assert all(b['lp']['objective'] <= a['lp']['objective'] + 1e-7
                   for a, b in zip(result['trace'], result['trace'][1:]))
        for iteration, record in zip(result['aoa_runs'], result['trace']):
            dual = record['lp']['dual']
            begin = perf_counter()
            routes = enumerate_routes(instance)
            full_cost = min(reduced_cost(instance, r, dual) for r in routes)
            seconds = perf_counter() - begin
            for run in iteration['runs']:
                assert run['qiskit_tensor_max_infidelity'] < 1e-8
                sampled = [Route(tuple(ids)) for ids in run['routes']]
                found = min((reduced_cost(instance, r, dual) for r in sampled), default=None)
                if found is not None:
                    assert found >= full_cost - 1e-7
                pricing.append({'run': path.name, 'iteration': record['iteration'],
                    'full_min_rc': full_cost, 'aoa_min_rc': found,
                    'gap_to_full': None if found is None else found - full_cost,
                    'full_enumeration_seconds': seconds, 'aoa_seconds': run['total_seconds'],
                    'feasible_rate': run['feasible_rate'], 'improving_rate': run['improving_rate'],
                    'oracle_has_negative': full_cost < -1e-7,
                    'aoa_has_negative': found is not None and found < -1e-7,
                    'max_infidelity': run['qiskit_tensor_max_infidelity']})
            for new in record['added']:
                assert reduced_cost(instance, Route(tuple(new['customers'])), dual) == new['reduced_cost']
                assert new['reduced_cost'] < -1e-7
        checks.append({'run': path.name, 'passed': True})
    csv_write(out / 'PRICING_COMPARISON.csv', pricing)

    base = artificial_instance(6)
    instance = Instance('reduction_six_control', base.distance, (0, 1, 1, 1, 1, 1, 1), 4, base.coordinates)
    full_cg = json.loads((out / 'REDUCTION_CLASSICAL_FULL_CG.json').read_text())
    for checkpoint, record in enumerate(full_cg['trace'][:2]):
        dual = record['lp']['dual']
        start = perf_counter()
        full = enumerate_routes(instance)
        full_values = [reduced_cost(instance, r, dual) for r in full]
        full_seconds = perf_counter() - start
        for domain in build_domains(instance, dual):
            start = perf_counter()
            routes = exact_domain_routes(instance, domain)
            values = [reduced_cost(instance, r, dual) for r in routes]
            seconds = perf_counter() - start
            comparisons.append({'checkpoint': checkpoint, 'domain': domain.name,
                'full_routes': len(full), 'restricted_routes': len(routes),
                'excluded_routes': len(set(full) - set(routes)),
                'full_min_rc': min(full_values), 'restricted_min_rc': min(values),
                'full_enumeration_seconds': full_seconds, 'restricted_enumeration_seconds': seconds,
                'full_negative_route_fraction': sum(v < -1e-7 for v in full_values) / len(full_values),
                'restricted_negative_route_fraction': sum(v < -1e-7 for v in values) / len(values)})
    csv_write(out / 'REDUCTION_ENUMERATION.csv', comparisons)

    pool = [Route((i,)) for i in instance.customers]
    trace = []
    for iteration in range(20):
        lp = solve_lp(instance, pool)
        candidates = set(r for d in build_domains(instance, lp['dual']) for r in exact_domain_routes(instance, d))
        costs = sorted(((reduced_cost(instance, r, lp['dual']), r) for r in candidates if r not in pool), key=lambda x: (x[0], x[1]))
        negative = [(v, r) for v, r in costs if v < -1e-7][:5]
        full_min = min(reduced_cost(instance, r, lp['dual']) for r in enumerate_routes(instance))
        trace.append({'iteration': iteration, 'lp': lp, 'full_min_rc': full_min,
                      'added': [{'customers': r.customers, 'rc': v} for v, r in negative]})
        if not negative:
            break
        pool.extend(r for _, r in negative)
    write_json(out / 'REDUCTION_CLASSICAL_RESTRICTED_CG.json', {'trace': trace,
        'integer': solve_integer(instance, pool), 'scope': 'RESTRICTED_DOMAIN_EXHAUSTED',
        'global_optimality_claimed': False})

    # Original-figure factor checks on an independently specified 4-customer input.
    factor_rows = []
    instance = artificial_instance(4)
    dual = solve_lp(instance, [Route((i,)) for i in instance.customers])['dual']
    cfg = AOAConfig(solver_seed=1401, max_evaluations=80, restarts=1)
    for p, slots in [(1, 4), (2, 4), (3, 4), (2, 2), (2, 3), (2, 5)]:
        result = PricingAOA(instance, dual, replace(cfg, p=p, slots=slots)).run()
        write_json(out / f'FACTOR_p{p}_L{slots}.json', result)
        found = min((reduced_cost(instance, Route(tuple(r)), dual) for r in result['routes']), default=None)
        factor_rows.append({'p': p, 'slots': slots, 'qubits': result['qubits'],
                            'feasible_rate': result['feasible_rate'], 'improving_rate': result['improving_rate'],
                            'min_rc': found, 'logical_depth': result['logical_depth'], 'seconds': result['total_seconds']})
    csv_write(out / 'PAPER_FACTOR_CHECKS.csv', factor_rows)
    batch_rows = []
    for k in [1, 5, 10]:
        result = run_column_generation(instance, pricing='aoa', config=replace(cfg, solver_seed=1402), batch_size=k)
        write_json(out / f'FACTOR_K{k}_CG.json', result)
        batch_rows.append({'K': k, 'rounds': len(result['trace']),
                           'columns_added': result['columns_added_by_aoa'],
                           'integer_objective': result['integer']['objective'],
                           'gap_to_full': result['integer_gap_to_full_enumeration'],
                           'seconds': result['total_seconds']})
    csv_write(out / 'PAPER_K_CHECKS.csv', batch_rows)
    write_json(out / 'REFERENCE_ASSERTIONS.json', {'runs': checks, 'passed': True,
        'pricing_snapshots': len(pricing), 'reduction_domains': len(comparisons),
        'original_figure_numbers_not_reproduced': [2, 3, 4, 5]})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    main(parser.parse_args().output)
