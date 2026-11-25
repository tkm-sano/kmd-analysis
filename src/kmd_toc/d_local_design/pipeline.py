"""Resumable, hash-pinned evidence stages; no production runner dependency."""
import csv
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
from time import perf_counter, sleep
import resource
import numpy as np
from .model import LocalProblem, Encoding, Decision, candidate_count, enumerate_decisions, direct_cost
from .completion import extract, physical, evaluate, trip_key
from .coverage import catalogue, choose, replay, csv_row
from .quantum import preflight, run_kernel, table, encoding_gate_resources

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/d_local_design/validation_v1.json'
INPUTS = ROOT / 'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs'
SAVED = ROOT / 'output/toc_delivery/non_time_variance_pilot_20261117_v1/runs'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 ** 2), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    tmp.replace(path)


def read(path):
    return json.loads(Path(path).read_text())


def source_hashes():
    files = list((ROOT / 'src/kmd_toc/d_local_design').glob('*.py'))
    files += list((ROOT / 'tests/d_local_design').glob('*.py'))
    files += [CONFIG, ROOT / 'AGENTS.md', ROOT / 'docs/research/DW_RESEARCH_POLICY.md',
              ROOT / 'configs/toc_delivery/common_conditions_v1_1.json',
              ROOT / 'configs/toc_delivery/termination_rules_20261116_v1.json',
              ROOT / 'configs/toc_delivery/dw_policy_20261117_v1.json',
              ROOT / 'docs/p1_pricing/APPROVALS.md', ROOT / 'docs/p1_pricing/REPORT.md',
              ROOT / 'src/kmd_toc/pipeline/completion.py', ROOT / 'src/kmd_toc/common/models.py',
              ROOT / 'src/kmd_toc/common/validation.py', ROOT / 'src/kmd_toc/baseline_a/program_validation.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)}


def environment():
    import psutil
    versions = {}
    for name in ('numpy', 'scipy', 'qiskit', 'qiskit-aer', 'qulacs', 'pytest', 'psutil', 'ortools'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    cg = Path('/sys/fs/cgroup')
    relative = Path('/proc/self/cgroup').read_text().strip().split('::')[-1].lstrip('/')
    current = cg / relative
    limits = {}
    effective = psutil.virtual_memory().available
    while True:
        for name in ('memory.max', 'memory.current', 'cpu.max', 'pids.max', 'cpuset.cpus.effective'):
            path = current / name
            if path.exists():
                value = path.read_text().strip()
                limits[str(path)] = value
                if name == 'memory.max' and value.isdigit():
                    used = int((current / 'memory.current').read_text())
                    effective = min(effective, max(0, int(value) - used))
        if current == cg:
            break
        current = current.parent
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'cpu_count': os.cpu_count(), 'affinity': sorted(os.sched_getaffinity(0)),
            'memory_total_bytes': psutil.virtual_memory().total, 'effective_available_bytes': effective,
            'cgroup_limits': limits, 'rlimit_AS': resource.getrlimit(resource.RLIMIT_AS),
            'versions': versions, 'pid': os.getpid(), 'benchmark_processes_at_once': 1,
            'native_threads': 1, 'production_P': 4, 'production_K_nested_parallelism': False,
            'cpu_model': next((line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown')}


def init(out):
    out = Path(out).resolve()
    allowed = (ROOT / 'output/d_local_design').resolve()
    if out == allowed or allowed not in out.parents:
        raise ValueError('DEDICATED_OUTPUT_SUBDIRECTORY_REQUIRED')
    if out.exists() and any(out.iterdir()) and not (out / 'MANIFEST.json').exists():
        raise ValueError('REFUSE_NONEMPTY_UNREGISTERED_OUTPUT')
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / 'MANIFEST.json'
    pins = source_hashes()
    if manifest.exists():
        old = read(manifest)
        if old['source_hashes'] != pins:
            raise ValueError('SOURCE_OR_CONFIG_CHANGED: choose a fresh output directory')
        for name, expected in old.get('inputs', {}).items():
            if digest(ROOT / name) != expected:
                raise ValueError('PINNED_INPUT_CHANGED:' + name)
    else:
        dump(manifest, {'purpose': 'design_validation_only', 'main_experiment_authorized': False,
                        'source_hashes': pins, 'inputs': {}, 'HEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                        'environment': environment(), 'settings': read(CONFIG)})
    return out, read(CONFIG)


def pin_inputs(out, scale):
    path = out / 'MANIFEST.json'
    manifest = read(path)
    selected = list((INPUTS / scale).glob('input.json')) + list((INPUTS / scale / 'od').glob('*'))
    selected.append(SAVED / f'{scale}_B_pilot_r01/plan.json')
    for p in selected:
        if p.is_file():
            key = str(p.relative_to(ROOT))
            value = digest(p)
            if key in manifest['inputs'] and manifest['inputs'][key] != value:
                raise ValueError('INPUT_CHANGED:' + key)
            manifest['inputs'][key] = value
    dump(path, manifest)


def load_saved(out, scale):
    from kmd_toc.common.models import load_problem, load_plan
    pin_inputs(out, scale)
    p = load_problem(INPUTS / scale)
    plan = load_plan(SAVED / f'{scale}_B_pilot_r01/plan.json')
    ok, checks = physical(p, plan)
    if not ok:
        raise ValueError('SAVED_PLAN_NOT_FEASIBLE:' + json.dumps(checks))
    return p, plan


def local_from_payload(data):
    data = dict(data)
    data.pop('n', None)
    data.pop('same_vehicle', None)
    data['trip_ids'] = tuple(tuple(k) for k in data['trip_ids'])
    for name in ('customer_ids', 'demand', 'outside_routes'):
        data[name] = tuple(data[name])
    for name in ('distance_m', 'duration_s'):
        data[name] = tuple(map(tuple, data[name]))
    return LocalProblem(**data).validate()


def validate(out, config):
    if (out / 'VALIDATION.json').exists():
        return read(out / 'VALIDATION.json')
    with (out / 'TEST_LOG.txt').open('w') as log:
        checked = subprocess.run([sys.executable, '-B', '-m', 'pytest', 'tests/d_local_design', '-q',
                                  '--junitxml=' + str(out / 'TEST_RESULTS.xml')], cwd=ROOT,
                                 stdout=log, stderr=subprocess.STDOUT, timeout=240)
    if checked.returncode:
        raise ValueError('UNIT_TESTS_FAILED: inspect TEST_LOG.txt')
    p, plan = load_saved(out, 'S1')
    routes, gain = catalogue(p, plan)
    reports = []
    for n in config['n_candidates']:
        pair, ids = choose(routes, gain, set(), n)
        local = extract(p, plan, pair, tuple(sorted(ids)), config['seed'])
        dump(out / f'local_n{n}.json', local.payload())
        # n=8 exhaustive independent enumeration; n7/9 also exact tables.
        energy, bound = table(local, Encoding('compact_rank_split', ids))
        np.save(out / f'energy_n{n}.npy', energy, allow_pickle=False)
        report = {'n': n, 'expected_candidates': candidate_count(n), 'table_valid_states': candidate_count(n),
                  'allow_empty_local_part': candidate_count(n), 'nonempty_local_parts': candidate_count(n, False),
                  'energy_table_sha256': digest(out / f'energy_n{n}.npy'),
                  'enumeration_kind': 'classical_exact_not_quantum', 'all_encodings_checked': n == 8}
        if n == 8:
            start = perf_counter()
            encodings = [Encoding(name, local.customer_ids) for name in Encoding.names]
            h = hashlib.sha256()
            count = 0
            max_error = 0.
            seen_compact = bytearray(candidate_count(n))
            for decision in enumerate_decisions(local.customer_ids):
                values = [e.encode(decision) for e in encodings]
                for e, bits in zip(encodings, values):
                    if e.decode(bits) != decision:
                        raise AssertionError('ENCODING_ROUNDTRIP')
                rank = values[-1]
                if seen_compact[rank]:
                    raise AssertionError('DUPLICATE_COMPACT_RANK')
                seen_compact[rank] = 1
                cost = direct_cost(local, decision)
                max_error = max(max_error, abs(energy[rank] * bound - cost))
                if max_error > 1e-7:
                    raise AssertionError('DIRECTED_COST_MISMATCH')
                h.update(f'{rank}:{cost:.9f}\n'.encode())
                count += 1
            assert count == 362880 and all(seen_compact)
            report.update(enumerated=count, encoding_roundtrips=3 * count, max_cost_residual_m=max_error,
                          exhaustive_cost_digest=h.hexdigest(), exhaustive_wall_s=perf_counter() - start)
        reports.append(report)
    result = {'status': 'PASS', 'scope': 'n8_full_enumeration_n7_n9_exact_tables', 'reports': reports,
              'constraint_feasibility_is_separate': True}
    dump(out / 'VALIDATION.json', result)
    return result


def worker(job_path):
    job = read(job_path)
    cpu = job['cpu']
    os.sched_setaffinity(0, {cpu})
    local = local_from_payload(job['local'])
    start = perf_counter()
    def progress(row):
        with Path(job_path).with_suffix('.progress.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
            stream.flush()
    result = run_kernel(local, job['encoding'], job['quantum'], job['method'], progress=progress)
    result['worker_kernel_wall_s'] = perf_counter() - start
    result['cpu_process_s'] = __import__('time').process_time()
    dump(Path(job_path).with_suffix('.result.json'), result)


def supervised_kernel(out, local, encoding, method, config, tag):
    import psutil
    path = out / 'kernels' / (tag + '.json')
    result_path = path.with_suffix('.result.json')
    if result_path.exists():
        return read(result_path)
    safety = config['safety_only']
    gate = preflight(Encoding(encoding, local.customer_ids), safety, method,
                     read(out / 'MANIFEST.json')['environment']['effective_available_bytes'])
    if not gate['safe']:
        return {'status': 'NOT_RUN_SAFETY', **Encoding(encoding, local.customer_ids).resources(), 'method': method, 'preflight': gate}
    dump(path, {'local': local.payload(), 'encoding': encoding, 'method': method,
                'quantum': config['measurement_only_quantum'], 'safety': safety,
                'cpu': min(os.sched_getaffinity(0))})
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'), 'PYTHONDONTWRITEBYTECODE': '1',
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1'}
    start = perf_counter()
    peak = 0
    reason = None
    with path.with_suffix('.log').open('w') as log:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'kmd_toc.d_local_design', '_worker', str(path)],
                                 env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        while child.poll() is None:
            try:
                proc = psutil.Process(child.pid)
                peak = max(peak, sum(q.memory_info().rss for q in [proc, *proc.children(recursive=True)] if q.is_running()))
            except psutil.Error:
                pass
            if peak > safety['worker_RSS_MiB'] * 1024 ** 2:
                reason = 'SAFETY_RSS_STOP'
            if perf_counter() - start > safety['worker_wall_s']:
                reason = 'SAFETY_WALL_STOP'
            if reason:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                break
            sleep(.05)
    if reason or child.returncode or not result_path.exists():
        result = {'status': reason or 'FAILED', 'returncode': child.returncode,
                  **Encoding(encoding, local.customer_ids).resources(), 'method': method}
        progress_path = path.with_suffix('.progress.jsonl')
        progress_rows = [json.loads(line) for line in progress_path.read_text().splitlines()] if progress_path.exists() else []
        training = [r for r in progress_rows if r['phase'] == 'training_complete']
        result.update(completed_training_evaluations=len(training),
                      completed_training_shots=sum(r['training_shots'] for r in training),
                      in_flight_shots='UNKNOWN; incomplete evaluation may have executed',
                      peak_RSS_MiB=peak / 1024 ** 2, peak_RSS_scope='sampled process tree; lower bound on instantaneous peak')
    else:
        result = read(result_path)
    result.update(parent_worker_wall_s=perf_counter() - start, sampled_tree_peak_RSS_MiB=peak / 1024 ** 2,
                  quantum_optimization_calls_attempted=1, quantum_optimization_calls_completed=int(result['status'] == 'MEASURED'),
                  preflight=gate, log=str(path.with_suffix('.log').relative_to(out)))
    dump(result_path, result)
    return result


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list, tuple)) else v for k, v in row.items()})


def benchmark(out, config):
    validate(out, config)
    results = []
    # All three encodings actually run on a small n2 restriction of same OD.
    full = local_from_payload(read(out / 'local_n8.json'))
    small_data = full.payload()
    small_data.update(customer_ids=full.customer_ids[:2], demand=full.demand[:2],
                      distance_m=[r[:3] for r in full.distance_m[:3]], duration_s=[r[:3] for r in full.duration_s[:3]])
    small = local_from_payload(small_data)
    for name in Encoding.names:
        for method in ('statevector', 'matrix_product_state'):
            # n2 one-hot q9 uses a direct quadratic circuit; its separate fixed
            # MPS QUBO cap is 12, unlike the wide diagonal oracle cap of 8.
            result = supervised_kernel(out, small, name, method, config, f'{name}_n2_{method}')
            results.append(result)
    for n in config['n_candidates']:
        local = local_from_payload(read(out / f'local_n{n}.json'))
        for name in Encoding.names:
            for method in ('statevector', 'matrix_product_state'):
                results.append(supervised_kernel(out, local, name, method, config, f'{name}_n{n}_{method}'))
    # Same seed, same actual circuit, same complete optimization trace.
    local = local_from_payload(read(out / 'local_n8.json'))
    repeat = supervised_kernel(out, local, 'compact_rank_split', 'statevector', config, 'compact_n8_reproduce')
    original = next(r for r in results if r['n'] == 8 and r['encoding'] == 'compact_rank_split' and r['method'] == 'statevector')
    reproducible = original.get('history') == repeat.get('history') and original.get('counts') == repeat.get('counts') and original['status'] == repeat['status'] == 'MEASURED'
    dump(out / 'REPRODUCIBILITY.json', {'status': 'PASS' if reproducible else 'FAIL', 'n': 8,
                                      'all_training_counts_and_final_counts_identical': reproducible})
    rows = []
    for r in results:
        row = {k: v for k, v in r.items() if k not in ('history', 'counts', 'decoded')}
        local = (local_from_payload(read(out / f"local_n{r['n']}.json")) if r['n'] >= 7 else small)
        row.update(encoding_gate_resources(local, r['encoding'], config['measurement_only_quantum']['p']))
        row['feasibility_preservation'] = 'not preserved by X; exact decode and full completion reject violations'
        row['implementation_limits'] = r.get('preflight',{}).get('reason')
        row['decode_complexity'] = r['encode_decode_complexity']
        row['software_versions'] = read(out / 'MANIFEST.json')['environment']['versions']
        row['measurement_kind'] = ('measured' if r['status'] == 'MEASURED' else
                                   'preflight_estimate_not_run' if r['status'] == 'NOT_RUN_SAFETY' else 'measured_incomplete_or_failed')
        row['physical_feasible_rate'] = None
        rows.append(row)
    write_csv(out / 'RESOURCE_BENCHMARK.csv', rows)
    dump(out / 'BENCHMARK.json', {'results': results, 'reproducibility': reproducible})
    return results


def coverage(out, config):
    rows = []
    for scale in ('S1', 'S2', 'S3'):
        p, plan = load_saved(out, scale)
        for n in config['n_candidates']:
            for series, multiple in config['K_series'].items():
                K = int(len(p.vehicles) * multiple)
                for rule in ('hybrid', 'unseen', 'gain'):
                    result = replay(p, plan, n, K, config['P'], max(config['R_candidates']), rule, scale)
                    for row in result:
                        row['K_series'] = series
                        rows.append(csv_row(row))
    write_csv(out / 'COVERAGE_ANALYSIS.csv', rows)
    dump(out / 'COVERAGE_SUMMARY.json', {'rows': [{k: v for k, v in row.items() if k not in ('selected_customer_ids', 'selected_trip_pairs')}
                                                for row in rows if row['R'] in config['R_candidates']],
                                         'branch_ID_rule': '0..P-1 use identical saved snapshot; per-branch coverage identical; ID lists apply to each branch',
                                         'plan_updates': False, 'optimization_calls_actually_executed_by_coverage': 0})
    return rows


def connection(out, config, benchmarks):
    tests = []
    for scale in ('S1', 'S2', 'S3'):
        p, plan = load_saved(out, scale)
        routes, gain = catalogue(p, plan)
        for n in config['n_candidates']:
            pair, ids = choose(routes, gain, set(), n)
            local = extract(p, plan, pair, tuple(sorted(ids)), config['seed'])
            incumbent = Decision(*(tuple(v.stop_id for v in next(t for t in plan.trips if trip_key(t) == key).visits if v.stop_id in ids) for key in pair))
            candidates = [('incumbent_order_fixture_not_quantum', incumbent)]
            if scale == 'S1':
                measured = next((r for r in benchmarks if r['n'] == n and r['encoding'] == 'compact_rank_split' and r['method'] == 'statevector' and r['status'] == 'MEASURED'), None)
                if measured:
                    candidates += [('quantum_measurement', Decision(tuple(row['trip_1']), tuple(row['trip_2']))) for row in measured['decoded'][:4]]
            for source, decision in candidates:
                start = perf_counter()
                selected, ledger = evaluate(p, plan, local, decision)
                tests.append({'scale': scale, 'n': n, 'source': source, 'local_ids': ids, 'trip_ids': pair,
                              'full_gateway_wall_s': perf_counter() - start, 'ledger': ledger})
    dump(out / 'COMPLETION.json', {'scope': 'limited_validation_no_full_search', 'tests': tests})
    return tests


def select(out, config):
    if not (out / 'BENCHMARK.json').exists() or not (out / 'COVERAGE_SUMMARY.json').exists():
        raise ValueError('RUN_BENCHMARK_AND_COVERAGE_FIRST')
    benchmarks = read(out / 'BENCHMARK.json')['results']
    tests = connection(out, config, benchmarks)
    summary = read(out / 'COVERAGE_SUMMARY.json')['rows']
    candidates = []
    for n in config['n_candidates']:
        measured = next((r for r in benchmarks if r['n'] == n and r['encoding'] == 'compact_rank_split' and r['method'] == 'statevector' and r['status'] == 'MEASURED'), None)
        if not measured:
            continue
        for series in config['K_series']:
            for R in config['R_candidates']:
                rows = [r for r in summary if r['n'] == n and r['K_series'] == series and r['R'] == R and r['rule'] == 'hybrid']
                assert len(rows) == 3
                quantum_s = measured['parent_worker_wall_s']
                estimates = []
                for row in rows:
                    gateway = max(t['full_gateway_wall_s'] for t in tests if t['n'] == n and t['scale'] == row['scale'])
                    quantum = quantum_s * row['K'] * R
                    completion = gateway * row['K'] * R
                    historical = read(SAVED / f"{row['scale']}_B_pilot_r01/RESULT.json")
                    estimates.append({'scale': row['scale'], 'K': row['K'], 'R': R, 'P': config['P'],
                        'Q_calls': config['P'] * row['K'] * R, 'coverage_replay': row['coverage'],
                        'unique_replay': row['unique_customers'], 'unexplored_replay': row['unexplored_customers'],
                        'quantum_plus_worker_wall_prediction_s': quantum, 'completion_gateway_prediction_s': completion,
                        'selection_prediction_s': row['selection_wall_s_per_branch'],
                        'initial_plan_wall_s': None, 'full_parent_wall_s': None,
                        'historical_B_parent_wall_reference_s': historical.get('T_program'),
                        'historical_reference_is_new_D_initial_plan_measurement': False,
                        'P_times_local_peak_RSS_prediction_MiB': config['P'] * measured['peak_RSS_MiB'],
                        'partial_branch_wall_prediction_s': quantum + completion + row['selection_wall_s_per_branch'],
                        'parallel_rule': 'P independent single-thread branches; parent wall=max(branch walls)+parent stages; no nested K parallelism',
                        'estimation_kind': 'extrapolated_single_local_fixture_and_static_plan; not measured full search',
                        'training_evaluations_prediction': config['P'] * row['K'] * R * measured['nfev'],
                        'training_shots_prediction': config['P'] * row['K'] * R * measured['training_shots'],
                        'final_shots_prediction': config['P'] * row['K'] * R * measured['final_shots']})
                candidates.append({'n': n, 'series': series, 'R': R, 'minimum_coverage': min(r['coverage'] for r in rows),
                                   'mean_coverage': sum(r['coverage'] for r in rows) / 3,
                                   'sum_Q_calls': sum(r['Q_calls'] for r in estimates), 'scales': estimates})
    # Diagnostic winner uses ONLY comparable first two keys, then minimum calls.
    # Deliberately does not skip missing common-time-budget n comparison.
    diagnostic = min(candidates, key=lambda c: (-c['minimum_coverage'], -c['mean_coverage'], c['sum_Q_calls'], c['n'], c['series'], c['R'])) if candidates else None
    result = {'status': 'UNRESOLVED', 'n': None, 'K_S1': None, 'K_S2': None, 'K_S3': None, 'R': None,
              'main_experiment_authorized': False, 'main_experiment_state': 'HOLD',
              'A_mathematical_validity': 'PASS' if read(out / 'VALIDATION.json')['status'] == 'PASS' else 'FAIL',
              'B_simulator_local_resource_validity': 'PASS_LOCAL_ONLY' if read(out / 'REPRODUCIBILITY.json')['status'] == 'PASS' else 'FAIL',
              'C_production_adoptability': 'HOLD_NOT_APPROVED',
              'gaps': ['Common approved/proposed full planning wall budget is absent; priority key n under same budget cannot be evaluated.',
                       'New local-D QAOA p/shots/optimizer evaluations are measurement-only; they do not define a production call cost.',
                       'Initial plan creation for new architecture and max-of-four-branches complete parent wall time have not been measured.',
                       'Static selection replay does not measure actual plan-updating coverage, completion rates or D/W stagnation.',
                       'Only four quantum candidates per n on one saved S1 plan received full completion; not a distribution-wide feasibility estimate.',
                       'Surrogate depot-route cost omits outside-route boundaries and W; formal cost policy requires adoption decision.'],
              'resource_only_diagnostic': diagnostic, 'resource_only_diagnostic_is_recommendation': False,
              'candidates': candidates, 'settings': config,
              'required_approvals': ['local-D QAOA execution contract and cost surrogate', 'K/R selection and full resource budget',
                                     'Pareto acceptance and 0.1m/1s comparison policy', 'production protocol and outer statistical replication'],
              'environment': read(out / 'MANIFEST.json')['environment']}
    dump(out / 'SELECTED_CONFIG.json', result)
    write_csv(out / 'TIME_ESTIMATES.csv', [dict(n=c['n'], K_series=c['series'], **row) for c in candidates for row in c['scales']])
    return result
