"""Small artificial vehicle-day CG validation after the external audit/plan gate.

Writes all cases including failures, comparisons, source/input/version/seed logs.
Exclusive outputs; never loads study demand or roads. Existing AOA is unchanged.
"""
import argparse
import csv
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import shutil
import sys
import traceback
from time import perf_counter
import numpy as np
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile, occupied_slots
from kmd_toc.vehicle_day.generation import enumerate_days
from kmd_toc.vehicle_day.runner import run_day_cg
from kmd_toc.vehicle_day.validation import validate_day, validate_plan, independent_plan_oracle


def default(value):
    if is_dataclass(value): return asdict(value)
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    raise TypeError(type(value).__name__)


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, default=default, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def save_columns(path, problem, columns):
    with path.open('x', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['column_id', 'vehicle_id', 'shift_start_s', 'shift_end_s',
                         'trips_json', 'D_km', 'W_min', 'loading_s', 'occupied_slots'])
        for c in columns:
            writer.writerow([c.column_id, c.vehicle_id, c.shift_start_s, c.shift_end_s,
                             json.dumps([asdict(t) for t in c.trips]), c.distance_km,
                             c.waiting_min, c.loading_s, json.dumps(occupied_slots(problem, c))])


def execute(output, config_path):
    out, cfgpath = Path(output), Path(config_path)
    gate = json.loads((out / 'AUDIT_PLAN_GATE.json').read_text())
    assert gate['implementation_started'] is False  # historical saved gate, before implementation
    cfg = json.loads(cfgpath.read_text())
    aoa = cfg['aoa']
    quantum = AOAConfig(slots=aoa['slots'], p=aoa['p'], max_evaluations=aoa['max_evaluations'],
                       restarts=aoa['restarts'], train_shots=aoa['train_shots'],
                       final_shots=aoa['final_shots'], solver_seed=cfg['solver_seed'])
    source = sorted(Path('src/kmd_toc/vehicle_day').glob('*.py')) + [
        Path('src/kmd_toc/column_generation/aoa.py'), Path('src/kmd_toc/column_generation/models.py'),
        Path('src/kmd_toc/column_generation/reduction.py'), Path(__file__)]
    manifest = {'started_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
                'executable': sys.executable, 'platform': platform.platform(),
                'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
                'config': cfg, 'config_sha256': hashlib.sha256(cfgpath.read_bytes()).hexdigest(),
                'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source},
                'external_implementations_executed': False, 'study_runs': 0}
    save(out / 'EXECUTION_MANIFEST.json', manifest)
    for p in source + [cfgpath]:
        target = out / 'SOURCE_SNAPSHOT' / p.relative_to(Path.cwd()) if p.is_absolute() else out / 'SOURCE_SNAPSHOT' / p
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): raise FileExistsError(target)
        shutil.copy2(p, target)
    summaries, assertions = [], []
    def case(problem, columns, profile, mode, name, independent=True, use_seed=True):
        print(name, flush=True)
        begin = perf_counter()
        result = run_day_cg(problem, columns, profile, mode=mode, aoa_config=quantum,
                            max_rounds=cfg['max_cg_rounds'], batch_size=cfg['batch_size'], use_seed=use_seed)
        if independent:
            reference = independent_plan_oracle(problem, columns, profile)
            if reference['feasible'] != result['full_grid_integer']['success']:
                raise RuntimeError('Independent full-domain feasibility disagrees')
            if reference['feasible'] and not np.isclose(reference['objective'], result['full_grid_integer']['objective']):
                raise RuntimeError('Independent reference and full MIP disagree')
            result['independent_plan_reference'] = reference
        if result['integer']['success']:
            assert result['metrics']['valid']
            assert result['integer_gap'] >= -1e-7
        if mode == 'classical' and result['final_phase'] == 'II':
            assert abs(result['final_lp']['objective'] - result['full_grid_lp']['objective']) < 1e-7
        save(out / f'{name}.json', result)
        metrics = result['metrics'] or {}
        qubits = [q['result']['qubits'] for t in result['trace'] if t['aoa'] for q in t['aoa']['quantum']]
        summaries.append({'case': name, 'N': len(problem.base.customers), 'B': problem.berths,
            'mode': mode, 'primary': profile.primary, 'other_limit': profile.other_limit,
            'full_columns': len(columns), 'pool_columns': result['pool_size'],
            'rounds': len(result['trace']), 'added_negative': result['negative_columns_added'],
            'LP': result['final_lp'].get('objective'), 'full_LP': result['full_grid_lp'].get('objective'),
            'IP': result['integer'].get('objective'), 'full_IP': result['full_grid_integer'].get('objective'),
            'integer_gap': result['integer_gap'], 'D_km': metrics.get('D_km'), 'W_min': metrics.get('W_min'),
            'W1_min': metrics.get('W1_min'), 'W2_min': metrics.get('W2_min'),
            'loading_work_min': metrics.get('loading_work_min'), 'trip_count': metrics.get('trip_count'),
            'used_vehicles': metrics.get('used_vehicles'), 'valid': metrics.get('valid', False),
            'final_full_min_rc': result['final_full_oracle_min_rc'], 'stop': result['stop_reason'],
            'qubits': max(qubits) if qubits else None,
            'method_seconds': result['method_wall_s_including_validation'],
            'diagnostic_seconds': result['diagnostic_wall_s'], 'case_seconds': perf_counter() - begin})
        assertions.append({'case': name, 'full_mip_vs_independent': independent,
                           'valid_or_infeasible_recorded': True})
    begin = perf_counter()
    try:
        for n in cfg['customer_counts']:
            for b in cfg['berths']:
                problem = small_problem(n, b)
                save(out / f'INPUT_N{n}_B{b}.json', problem)
                columns = enumerate_days(problem)
                assert len({c.column_id for c in columns}) == len(columns)
                assert all(not validate_day(problem, c) for c in columns)
                save_columns(out / f'DAY_COLUMNS_N{n}_B{b}.csv', problem, columns)
                for primary in cfg['objective_profiles']:
                    case(problem, columns, ObjectiveProfile(primary), 'classical', f'CG_N{n}_B{b}_{primary}')
                case(problem, columns, ObjectiveProfile('D'), 'aoa', f'AOA_N{n}_B{b}_D')
        problem = small_problem(4, 1)
        columns = enumerate_days(problem)
        case(problem, columns, ObjectiveProfile('D', 0), 'classical', 'AUX_W0_FEASIBLE', use_seed=False)
        problem = small_problem(6, 1)
        columns = enumerate_days(problem)
        case(problem, columns, ObjectiveProfile('D', 0), 'classical', 'AUX_W0_INFEASIBLE', use_seed=False)
        problem = replace(small_problem(4, 1), vehicles=(replace(small_problem(4, 1).vehicles[0], capacity=1),))
        case(problem, enumerate_days(problem), ObjectiveProfile('D'), 'classical', 'CAPACITY_INFEASIBLE', independent=False, use_seed=False)
        base = small_problem(6, 1)
        problem = replace(base, vehicles=tuple(replace(v, shift_end_s=480) for v in base.vehicles))
        case(problem, enumerate_days(problem), ObjectiveProfile('D'), 'classical', 'SHIFT_INFEASIBLE', use_seed=False)
        with (out / 'RESULTS.csv').open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
            writer.writeheader(); writer.writerows(summaries)
        save(out / 'ACCEPTANCE.json', {'cases': assertions, 'case_count': len(assertions), 'passed': True,
            'study_runs': 0, 'seconds': perf_counter() - begin,
            'max_rss_kib_linux': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    except Exception:
        save(out / ('FAILURE_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json'),
             {'traceback': traceback.format_exc(), 'seconds': perf_counter() - begin})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--config', default='configs/toc_delivery_d/vehicle_day_validation_v1.json')
    args = parser.parse_args()
    execute(args.output, args.config)
