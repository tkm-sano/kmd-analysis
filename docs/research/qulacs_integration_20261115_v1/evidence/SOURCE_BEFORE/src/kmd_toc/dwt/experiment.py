"""Registered finite pilots, fresh workers, watchdog and complete trial records."""
import hashlib
import importlib.metadata
import multiprocessing
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import numpy as np
from .worker import dump
from .standard import export_standard, Geometry


class LazyGeometry:
    def __init__(self):
        self.delegate = None

    def leg(self, *args):
        if self.delegate is None:
            self.delegate = Geometry(Path.cwd())
        return self.delegate.leg(*args)


def _import_only_fork_worker(spec, out):
    """Only fork a verified single-thread, solver-never-run parent."""
    os.setsid()
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (Path(out) / 'execution.log').open('a') as log:
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        from .worker import execute_trial
        execute_trial(spec, out, allow_import_only_fork=True)


class ForkHandle:
    def __init__(self, spec, out):
        self.process = multiprocessing.get_context('fork').Process(target=_import_only_fork_worker, args=(spec, out))
        self.process.start()
        self.pid = self.process.pid

    @property
    def returncode(self):
        return self.process.exitcode

    def poll(self):
        return None if self.process.is_alive() else self.process.exitcode

    def wait(self, timeout=None):
        self.process.join(timeout)
        if self.process.is_alive():
            raise subprocess.TimeoutExpired('preloaded worker', timeout)
        return self.process.exitcode


def register(config_path, phase, methods=None):
    path = Path(config_path)
    config = json.loads(path.read_text())
    root = Path(config['output_root'])
    target = root / (phase + '_REGISTERED.json')
    if target.exists():
        raise FileExistsError('REGISTER_EXISTS_NO_POSTHOC_REPLACEMENT')
    group = config[phase]
    source_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(Path('src/kmd_toc').rglob('*.py'))}
    source_hashes['scripts/run_dwt.py'] = hashlib.sha256(Path('scripts/run_dwt.py').read_bytes()).hexdigest()
    if Path('scripts/run_dwt_bundle.py').exists():
        source_hashes['scripts/run_dwt_bundle.py'] = hashlib.sha256(Path('scripts/run_dwt_bundle.py').read_bytes()).hexdigest()
    versions = {p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'ortools', 'qiskit']}
    specs = []
    methods = methods or ['B', 'C', 'D']
    serial = 0
    for scenario in group['scenarios']:
        registered_input = json.loads((Path(config['input_root']) / scenario / 'input.json').read_text())
        for epsilon in group['W_limits_min']:
            for tau in group['budgets_s']:
                for rep in range(group['repetitions']):
                    for method in methods:
                        stream = np.random.SeedSequence([config['root_seed'], 1 if phase == 'pilot' else 2, serial])
                        s, q = stream.spawn(2)
                        seeds = {'solver_seed': int(s.generate_state(1)[0]) % (2 ** 31 - 1),
                                 'quantum_seed': int(q.generate_state(1)[0]), 'validation_seed': None}
                        serial += 1
                        tid = f'{phase}_{scenario}_{method}_W{epsilon:.12g}_T{tau:.12g}_r{rep}'
                        specs.append({'trial_id': tid, 'scenario_id': scenario, 'instance_id': scenario + '_frozen_v1',
                                      'method': method, 'repetition_id': rep, 'phase': phase,
                                      'epsilon_W_min': epsilon, 'tau_s': tau, 'seeds': seeds,
                                      'input_dir': str(Path(config['input_root']) / scenario),
                                      'code_hashes': source_hashes, 'environment_version': versions,
                                      'registered_input_hash': registered_input['problem_hash'],
                                      'registered_OD_hash': registered_input['od_hash'],
                                      'config': config, 'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
                        if config.get('cpu_parallel', {}).get('enabled') and method in ('B', 'C', 'D', 'D_CLASSICAL_CONTROL'):
                            from .parallel import cpu_profile
                            specs[-1]['execution_cpu_profile'] = cpu_profile(config)
    dump(target, {'phase': phase, 'registered_unix_s': time.time(), 'config_path': str(path),
                  'code_hashes': source_hashes, 'environment_version': versions,
                  'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'specs': specs,
                  'kind': 'limited feasibility/budget experiment; not confirmatory main experiment'})
    return target


def run_spec(spec, root, geometry=None, import_only_fork=False):
    out = Path(root) / 'trials' / spec['trial_id']
    out.mkdir(parents=True, exist_ok=False)
    dump(out / 'spec.json', spec)
    env = {**os.environ, 'PYTHONPATH': 'src', 'PYTHONDONTWRITEBYTECODE': '1',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    started = time.perf_counter()
    killed = False
    with (out / 'execution.log').open('w') as log:
        safe_fork = import_only_fork and len(list(Path('/proc/self/task').iterdir())) == 1
        process = (ForkHandle(spec, out) if safe_fork else
                   subprocess.Popen([sys.executable, '-B', '-m', 'kmd_toc.dwt.worker', '--spec', str(out / 'spec.json')],
                                    env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        while process.poll() is None:
            progress = out / 'progress.json'
            try:
                current = json.loads(progress.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                current = {}
            now = time.perf_counter()
            # Native solvers may not return to Python at their requested limit.
            # An independent process enforces the actual shared wall deadline.
            expired = (current and not current.get('timing_finished') and now > current['deadline'])
            startup_timeout = not current and now - started > spec['config'].get('dependency_setup_limit_s', 240)
            output_timeout = current.get('timing_finished') and now - current['deadline'] > 30
            if expired or startup_timeout or output_timeout:
                killed = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(0.025)
    worker_file = out / 'worker_result.json'
    if worker_file.exists() and not killed:
        row = json.loads(worker_file.read_text())
    else:
        row = {k: spec[k] for k in ['trial_id', 'scenario_id', 'instance_id', 'method', 'repetition_id', 'phase', 'epsilon_W_min', 'tau_s']}
        row.update(status='HARD_TIMEOUT' if killed else 'WORKER_ERROR', feasible=False, budget_met=False,
                   epsilon_met=False, standard_output_complete=False, T_kind='program_wall',
                   D_km=None, W_min=None, T_program_s=None, input_hash=None, OD_hash=None,
                   failure_elapsed_s=time.perf_counter() - current.get('start_perf_counter', started),
                   error={'returncode': process.returncode, 'watchdog': killed}, **spec['seeds'])
    row['fresh_process_wall_s'] = time.perf_counter() - started
    row['worker_launch_mode'] = 'single-thread import-only fork' if safe_fork else 'fresh exec'
    row['trial_directory'] = str(out)
    row = export_standard(row, spec, out, geometry)
    dump(out / 'result.json', row)
    return row


def run_registered(register_path):
    batch_start = time.perf_counter()
    register_path = Path(register_path)
    registration = json.loads(register_path.read_text())
    root = register_path.parent
    from .setup import preload_dependencies
    dump(root / (registration['phase'] + '_SETUP_PROGRESS.json'), {'state': 'uniform dependency import; no input read', 'started_unix_s': time.time()})
    setup_seconds = preload_dependencies()
    # Native thread count matters: Python active_count alone cannot detect
    # BLAS/HiGHS threads. No parent solver is executed anywhere in this loop.
    native_threads = len(list(Path('/proc/self/task').iterdir())) if Path('/proc/self/task').exists() else None
    import_only_fork = native_threads == 1 and 'fork' in multiprocessing.get_all_start_methods()
    dump(root / (registration['phase'] + '_DEPENDENCY_SETUP.json'),
         {'seconds': setup_seconds, 'native_threads_after_import_only': native_threads,
          'mode': 'single-thread import-only parent; independent fresh fork children' if import_only_fork else 'fresh exec children',
          'instance_read_or_solver_before_T': False, 'quantum_computation_before_T': False,
          'input_read_boundary': 'each child independently loads complete common input after T start'})
    geometry = LazyGeometry()
    results = []
    for spec in registration['specs']:
        if (root / 'trials' / spec['trial_id']).exists():
            raise FileExistsError('EXISTING_TRIAL_REQUIRES_EXPLICIT_NEW_REGISTRATION; never overwrite or silently omit a failure')
        row = run_spec(spec, root, geometry, import_only_fork=import_only_fork)
        results.append({k: v for k, v in row.items() if k != 'plan'})
        dump(root / (registration['phase'] + '_PROGRESS.json'), results)
        print(json.dumps({k: row.get(k) for k in ['trial_id', 'status', 'D_km', 'W_min', 'T_program_s', 'max_rss_KiB']}, ensure_ascii=False), flush=True)
    dump(root / (registration['phase'] + '_BATCH_TIMING.json'),
         {'wall_s': time.perf_counter() - batch_start, 'dependency_setup_s': setup_seconds,
          'trials': len(results), 'scope': 'includes uniform software setup, workers, export and logging; not T_program'})
    return results
