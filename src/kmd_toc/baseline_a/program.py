"""Pure provisional A2/FCFS, measured through two validations; no B/C/D plans."""
from dataclasses import asdict, replace
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time

from .construction import create_plan
from .program_validation import audit_plan
from kmd_toc.common.models import load_problem
from kmd_toc.common.validation import validate_plan

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/toc_delivery/a_provisional_program_v2.json'
CONFIG_SHA256 = '358e99dfbe78e5790b137b0fa32d70395b322e17a10c0cf4060a794f4cb7bb9e'
T_SCOPE = ['input_files_and_hashes', 'common_input_and_OD_load', 'preprocessing',
           'territories_and_boundary_balance', 'nearest_neighbor_and_trip_split',
           'FCFS_berths_and_timestamps', 'common_validation', 'independent_recalculation',
           'validation_agreement']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def settings():
    if digest(CONFIG) != CONFIG_SHA256:
        raise ValueError('A_PROGRAM_CONFIG_HASH')
    return json.loads(CONFIG.read_text())


def load_registered(directory, registration, scenario):
    directory = Path(directory)
    for name, expected in registration['files'].items():
        if digest(directory / name) != expected:
            raise ValueError('REGISTERED_INPUT_FILE_HASH: ' + name)
    p = load_problem(directory)
    if p.experiment.kind != 'frozen_research' or p.experiment.scenario_id != scenario:
        raise ValueError('REGISTERED_SCENARIO_KIND')
    if [len(p.stops), len(p.vehicles), len(p.berths)] != registration['counts']:
        raise ValueError('REGISTERED_COUNTS')
    if (p.od.metadata.get('table_distances_used') is not False or
            p.od.metadata.get('matrix_service') !=
            'Route per ordered pair with annotated node path; distance and duration from same Route object'):
        raise ValueError('A_REQUIRES_ROUTE_PAIR_OD_NOT_TABLE')
    return p


def measure(loader, *, limit_s=180, clock=time.perf_counter):
    """A failure retains diagnostics and attempt time, never accepted D/W/T."""
    started, cpu_started = clock(), time.process_time()
    events = [{'name': 'input_load_start', 'elapsed_s': 0.0}]
    def mark(name):
        elapsed = clock() - started
        events.append({'name': name, 'elapsed_s': elapsed})
        if elapsed > limit_s:
            raise TimeoutError('A_PROGRAM_TIME_LIMIT')
    row = {'method': 'A', 'rule': 'A2', 'offset_deg': 0, 'completion': 'FCFS_only',
           'status': 'ERROR', 'physical_feasible': False, 'D_km': None, 'W_min': None,
           'T_A_program': None, 'T_program_s': None, 'T_A_human_reference': None,
           'T_kind': 'program_wall', 'T_scope': T_SCOPE, 'human_reference_status': '未取得',
           'quantitative_representativeness': 'FAIL', 'calibrated': False,
           'random_seed': None, 'error': None, 'validation': None, 'second_validation': None}
    p = plan = None
    stage = 'INPUT'
    try:
        p = loader()
        mark('input_load_end')
        stage = 'GENERATION'
        plan = create_plan(p, 'A2', 0, mark)
        plan = replace(plan, method_settings={**plan.method_settings,
                       'program_spec_version': 'A-provisional-rule-program-v2-20261113',
                       'representative_operator_algorithm': False})
        mark('generation_end')
        stage = 'VALIDATION'
        common = validate_plan(p, plan)
        row['validation'] = common.as_dict()
        mark('common_validation_end')
        other = audit_plan(p, plan)
        row['second_validation'] = other
        mark('independent_recalculation_end')
        valid = common.feasible and other['feasible']
        agrees = valid and abs(common.D_km - float(other['D_km'])) < 1e-7 and abs(common.W_min - float(other['W_min'])) < 1e-7
        row['physical_feasible'] = bool(agrees)
        row['status'] = 'VALIDATED' if agrees else 'REJECTED_PLAN'
        if agrees:
            row.update(D_km=common.D_km, W_min=common.W_min)
        mark('validation_agreement_end')
    except Exception as error:
        row.update(status='TIME_LIMIT' if isinstance(error, TimeoutError) else
                   ('INPUT_HOLD' if stage == 'INPUT' else 'ERROR'),
                   error={'stage': stage, 'type': type(error).__name__, 'message': str(error)})
        events.append({'name': 'failed', 'elapsed_s': clock() - started})
    elapsed = events[-1]['elapsed_s']
    row.update(T_attempt_wall_s=elapsed, cpu_time_s=time.process_time() - cpu_started,
               timing_events=events, budget_met=elapsed <= limit_s,
               max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if row['status'] == 'VALIDATED':
        row.update(T_A_program=elapsed, T_program_s=elapsed)
    else:
        row.update(D_km=None, W_min=None, physical_feasible=False)
    if p is not None:
        row.update(scenario_id=p.experiment.scenario_id, input_hash=p.fingerprint,
                   OD_hash=p.od.fingerprint, visited_count=sum(len(t.visits) for t in plan.trips) if plan else 0)
    return row, plan


def score(metrics, reference):
    """No reference is inferred from a functional run or another scale."""
    identity = ('scenario_id', 'input_hash', 'OD_hash', 'T_kind', 'T_scope', 'comparison_contract_id')
    if (not reference or reference.get('status') != 'FROZEN' or
            any(not metrics.get(k) or reference.get(k) != metrics.get(k) for k in identity)):
        return {'status': 'REFERENCE_UNDEFINED', 'J': None}
    keys = ('D_km', 'W_min', 'T_program_s')
    values = [reference.get(k) for k in keys]
    if not all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in values):
        return {'status': 'REFERENCE_UNDEFINED', 'J': None}
    if metrics.get('status') != 'VALIDATED' or not all(
            type(metrics.get(k)) in (int, float) and math.isfinite(metrics[k]) and metrics[k] >= 0 for k in keys):
        return {'status': 'INELIGIBLE_PLAN', 'J': None}
    return {'status': 'COMPUTED_PROGRAM_ONLY', 'J': math.fsum(metrics[k] / reference[k] for k in keys) / 3}


def execute(directory, scenario, output, *, registration=None, setup=None):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    cfg = settings()
    registration = registration or cfg['scenarios'][scenario]
    dump(out / 'config.json', cfg)
    row, plan = measure(lambda: load_registered(directory, registration, scenario),
                        limit_s=cfg['timing_check']['program_limit_s'])
    row.setdefault('scenario_id', scenario)
    row.update(spec_version=cfg['version'], setup=setup, pid=os.getpid(),
               cpu_affinity=sorted(os.sched_getaffinity(0)), native_threads=1,
               experiment_kind='bounded_functional_check',
               comparison_contract_id='common-v1.1_Route_CPU4_program_double_validation_v2',
               J=score(row, None))
    exporting = time.perf_counter()
    for name in ('common_conditions_v1_1.json', 'a_rule_baseline_v1.json'):
        source = ROOT / 'configs/toc_delivery' / name
        (out / name).write_bytes(source.read_bytes())
    if plan is not None:
        dump(out / ('plan.json' if row['status'] == 'VALIDATED' else 'rejected_plan.json'), asdict(plan))
    dump(out / 'validation.json', {'status': row['status'], 'common': row['validation'],
                                  'independent': row['second_validation'], 'error': row['error']})
    if plan is not None:
        import csv
        with (out / 'trips.csv').open('w', newline='') as stream:
            fields = ['vehicle_id', 'trip_no', 'berth_id', 'ready_s', 'load_start_s', 'load_end_s',
                      'departure_s', 'return_s', 'distance_m', 'waiting_s', 'stop_count']
            writer = csv.DictWriter(stream, fields)
            writer.writeheader()
            for trip in plan.trips:
                writer.writerow({**{k: getattr(trip, k) for k in fields if k != 'stop_count'}, 'stop_count': len(trip.visits)})
    row['export_work_before_metrics_s'] = time.perf_counter() - exporting
    dump(out / 'metrics.json', row)
    code = sorted((ROOT / 'src/kmd_toc/baseline_a').glob('*.py'))
    code += sorted((ROOT / 'src/kmd_toc/common').glob('*.py'))
    code += [ROOT / 'src/kmd_toc/frozen_demand.py', ROOT / 'scripts/run_baseline_a.py']
    dump(out / 'manifest.json', {'version': cfg['version'], 'status': row['status'],
         'input_directory': str(Path(directory).resolve()), 'input_files_sha256': registration['files'],
         'config_sha256': CONFIG_SHA256, 'source_files_sha256': {str(p.relative_to(ROOT)): digest(p) for p in code},
         'products_sha256': {p.name: digest(p) for p in out.iterdir() if p.is_file()},
         'T_scope': T_SCOPE, 'T_excludes': ['dependency_import', 'process_start', 'output', 'OD_generation'],
         'export_scope': 'full output wall time also recorded by CLI parent',
         'operator_D_W_T_calibration': None, 'main_experiment_eligible': False})
    return row
