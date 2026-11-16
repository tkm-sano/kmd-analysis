"""Reproducible small experiments; never read or generate study demand/OD.

Each experiment writes a separate JSON before advancing. Errors are logged with
tracebacks and stop the batch, preserving prior and failed runs. Files are not
overwritten. Classical oracle diagnostics never inject AOA CG columns.
"""
import csv
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import traceback
from time import perf_counter
import numpy as np
from .models import Instance, Route, artificial_instance, enumerate_routes, reduced_cost
from .master import solve_lp
from .aoa import AOAConfig, PricingAOA
from .runner import run_column_generation
from .reduction import build_domains, exact_domain_routes


def json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=json_default, allow_nan=False)
        stream.write('\n')


def execute(config_path, output):
    config_path, out = Path(config_path), Path(output)
    out.mkdir(parents=True, exist_ok=True)
    settings = json.loads(config_path.read_text())
    cfg = AOAConfig(**{k: settings[k] for k in ['slots', 'p', 'max_evaluations', 'restarts',
                                              'train_shots', 'final_shots', 'lambda_capacity',
                                              'lambda_visit', 'tolerance']})
    manifest = {'started_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
                'executable': sys.executable, 'platform': platform.platform(),
                'cpu_count': os.cpu_count(), 'thread_environment': {k: os.getenv(k) for k in
                    ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS']},
                'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
                'config': settings, 'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
                'git_head': subprocess.run(['git', 'rev-parse', 'HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
                'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    sorted(Path('src/kmd_toc/column_generation').glob('*.py'))},
                'study_data_read_or_modified': False, 'authors_numerical_reproduction': False}
    write_json(out / 'EXECUTION_MANIFEST.json', manifest)
    table, reductions = [], []
    started = perf_counter()
    try:
        for m in settings['customer_counts']:
            instance = artificial_instance(m)
            write_json(out / f'INSTANCE_{m}.json', {'name': instance.name,
                'coordinates': instance.coordinates, 'distance': instance.distance.tolist(),
                'demand': instance.demand, 'capacity': instance.capacity,
                'provenance': 'independent artificial fixture; not Ota or author instance'})
            classic = run_column_generation(instance, pricing='classical', max_rounds=settings['max_cg_rounds'])
            write_json(out / f'CG_CLASSICAL_{m}.json', classic)
            for solver_seed in settings['solver_seeds']:
                print(f'A: m={m}, seed={solver_seed}', flush=True)
                result = run_column_generation(instance, pricing='aoa', config=replace(cfg, solver_seed=solver_seed),
                                               max_rounds=settings['max_cg_rounds'], batch_size=settings['cg_batch_size'])
                write_json(out / f'CG_AOA_{m}_{solver_seed}.json', result)
                runs = [run for it in result['aoa_runs'] for run in it['runs']]
                shots = sum(r['measured_shots'] for r in runs)
                table.append({'customers': m, 'solver_seed': solver_seed, 'method': 'CG_AOA',
                    'columns_added': result['columns_added_by_aoa'], 'rounds': len(result['trace']),
                    'lp_objective': result['final_lp']['objective'],
                    'integer_objective': result['integer']['objective'],
                    'full_integer_objective': result['full_enumeration_integer']['objective'],
                    'integer_gap': result['integer_gap_to_full_enumeration'],
                    'feasible_rate': sum(r['feasible_shots'] for r in runs) / shots,
                    'improving_rate_all_rounds': sum(r['improving_shots'] for r in runs) / shots,
                    'qubits': max(r['qubits'] for r in runs),
                    'logical_depth_max': max(r['logical_depth'] for r in runs),
                    'shots': shots, 'angle_evaluations': sum(h['nfev'] for r in runs for h in r['history']),
                    'seconds': result['total_seconds'], 'stop': result['stop_reason'],
                    'classical_oracle_closure': result['full_oracle_nonnegative_at_final_dual']})
        # Factorial audit isolates the displayed uniqueness and t=0 mixing choices.
        instance = artificial_instance(4)
        dual = solve_lp(instance, [Route((i,)) for i in instance.customers])['dual']
        for fixed in [True, False]:
            for penalty in ['customer_unique', 'paper_literal']:
                print(f'Audit: fixed={fixed}, penalty={penalty}', flush=True)
                audit_cfg = replace(cfg, fixed_depot=fixed, penalty=penalty, solver_seed=1201,
                                    max_evaluations=80, restarts=1)
                result = PricingAOA(instance, dual, audit_cfg).run(native_depth=fixed and penalty == 'customer_unique')
                result['dual'] = dual
                result['energy_comparison_repeated_sequence'] = {
                    'sequence': [0, 1, 1, 0],
                    'energy': PricingAOA(instance, dual, audit_cfg).direct_energy((0, 1, 1, 0))}
                write_json(out / f'FORMULA_AUDIT_{int(fixed)}_{penalty}.json', result)
        # B benchmark uses six original customers, q=1, Q=4, separately from study inputs.
        base = artificial_instance(6)
        instance = Instance('reduction_six_control', base.distance, (0, 1, 1, 1, 1, 1, 1), 4, base.coordinates)
        full_routes = enumerate_routes(instance)
        classical = run_column_generation(instance, pricing='classical')
        write_json(out / 'REDUCTION_CLASSICAL_FULL_CG.json', classical)
        for checkpoint, record in enumerate(classical['trace'][:2]):
            dual = record['lp']['dual']
            full_min = min(reduced_cost(instance, r, dual) for r in full_routes)
            for domain in build_domains(instance, dual):
                print(f'B: checkpoint={checkpoint}, domain={domain.name}', flush=True)
                candidates = exact_domain_routes(instance, domain)
                restricted_min = min(reduced_cost(instance, r, dual) for r in candidates)
                for seed in settings['solver_seeds']:
                    result = PricingAOA(domain.pricing, domain.dual,
                                        replace(cfg, slots=domain.slots, solver_seed=seed)).run()
                    expanded = [domain.expand(Route(tuple(ids))) for ids in result['routes']]
                    aoa_min = min((reduced_cost(instance, r, dual) for r in expanded), default=None)
                    result.update({'groups': domain.groups, 'dual_original': dual, 'original_checkpoint': checkpoint,
                                   'full_min_reduced_cost': full_min, 'restricted_min_reduced_cost': restricted_min,
                                   'expanded_routes': [list(r.nodes()) for r in expanded], 'aoa_min_reduced_cost': aoa_min})
                    write_json(out / f'REDUCTION_{checkpoint}_{domain.name}_{seed}.json', result)
                    reductions.append({'checkpoint': checkpoint, 'domain': domain.name, 'solver_seed': seed,
                        'full_routes': len(full_routes), 'restricted_routes': len(candidates),
                        'full_min_rc': full_min, 'restricted_min_rc': restricted_min, 'aoa_min_rc': aoa_min,
                        'restriction_gap': restricted_min - full_min,
                        'aoa_gap_to_restricted': None if aoa_min is None else aoa_min - restricted_min,
                        'aoa_gap_to_full': None if aoa_min is None else aoa_min - full_min,
                        'negative_column_found': bool(aoa_min is not None and aoa_min < -1e-7),
                        'feasible_rate': result['feasible_rate'], 'improving_rate': result['improving_rate'],
                        'qubits': result['qubits'], 'logical_depth': result['logical_depth'],
                        'seconds': result['total_seconds']})
        print('B: reduced-domain CG trajectory', flush=True)
        reduced_cg = run_column_generation(instance, pricing='aoa', config=replace(cfg, solver_seed=1301), reduced=True)
        write_json(out / 'REDUCTION_AOA_CG.json', reduced_cg)
        for name, rows in [('REFERENCE_RESULTS.csv', table), ('REDUCTION_RESULTS.csv', reductions)]:
            with (out / name).open('x', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        write_json(out / 'RUN_COMPLETION.json', {'status': 'COMPLETED', 'seconds': perf_counter() - started,
            'max_rss_kib_linux': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'cases_A': len(table), 'cases_B': len(reductions), 'study_runs_executed': 0})
    except Exception:
        write_json(out / f'FAILURE_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.json',
                   {'traceback': traceback.format_exc(), 'elapsed_seconds': perf_counter() - started})
        raise
