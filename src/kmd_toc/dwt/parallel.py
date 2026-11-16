"""Bounded CPU-parallel multi-start, one external trial and one wall deadline.

Each branch runs the existing complete method with one native solver thread.
The coordinator joins every child, checks all usable candidates, and validates
the selected plan again before stopping T. Branches are not statistical repeats.
"""
from dataclasses import replace
import math
import multiprocessing as mp
import os
from pathlib import Path
import resource
import time


METHODS = ('B', 'C', 'D', 'D_CLASSICAL_CONTROL', 'D_CLASSICAL_REPLACEMENT')


def enabled(spec):
    return spec['method'] in METHODS and spec['config'].get('cpu_parallel', {}).get('enabled') is True


def cpu_profile(config, available=None):
    policy = config['cpu_parallel']
    workers = policy['workers']
    if type(workers) is not int or workers < 2 or policy.get('native_threads_per_branch') != 1:
        raise ValueError('PARALLEL_WORKERS_REQUIRE_AT_LEAST_TWO_AND_ONE_NATIVE_THREAD')
    if config.get('threads') != workers:
        raise ValueError('CONFIGURED_CPU_BUDGET_MUST_EQUAL_PARALLEL_WORKERS')
    allowed = sorted(os.sched_getaffinity(0) if available is None else available)
    requested = policy.get('cpu_ids')
    if requested is None:
        selected, physical = [], set()
        for cpu in allowed:
            topology = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
            try:
                key = ((topology / 'physical_package_id').read_text().strip(),
                       (topology / 'core_id').read_text().strip())
            except OSError:
                key = ('logical', str(cpu))
            if key not in physical:
                selected.append(cpu)
                physical.add(key)
            if len(selected) == workers:
                break
    else:
        if (not isinstance(requested, list) or len(requested) != workers
                or any(type(c) is not int or c not in allowed for c in requested)
                or len(set(requested)) != workers):
            raise ValueError('PARALLEL_CPU_IDS_OUTSIDE_ALLOWED_AFFINITY_OR_DUPLICATED')
        selected = requested
    if len(selected) != workers:
        raise ValueError('INSUFFICIENT_CPU_CORES_FOR_PARALLEL_POLICY; no silent serial fallback')
    fraction = policy['coordinator_reserve_fraction']
    if type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 < fraction < 1:
        raise ValueError('PARALLEL_COORDINATOR_RESERVE_RANGE')
    return {'mode': 'parallel_multistart', 'workers': workers, 'cpu_ids': selected,
            'native_threads_per_branch': 1, 'coordinator_reserve_fraction': fraction,
            'method_concurrency': 1, 'statistical_trial_count': 1}


def branch_seeds(seeds, count):
    import numpy as np
    # A domain tag keeps branch streams distinct from old direct root-seed use.
    roots = np.random.SeedSequence([int(seeds['solver_seed']), int(seeds['quantum_seed'] or 0),
                                   0x43505534]).spawn(count)
    records = []
    for root in roots:
        solver, quantum = root.spawn(2)
        records.append({'solver_seed': int(solver.generate_state(1)[0]) % (2**31 - 1),
                        'quantum_seed': int(quantum.generate_state(1)[0]), 'validation_seed': None})
    if len({(x['solver_seed'], x['quantum_seed']) for x in records}) != count:
        raise ValueError('PARALLEL_SEED_COLLISION')
    return records


def quantum_use_state(method, summaries):
    if any(s.get('quantum_seed_used') is True for s in summaries):
        return True
    if method == 'D' and any(not s['quantum_accounting_complete'] for s in summaries):
        return None  # a killed/incomplete circuit cannot honestly be called unused
    return False


def _branch_entry(spec, out, cpu, go, deadline, ready):
    from .worker import dump, execute
    from .setup import preload_dependencies
    import traceback
    out = Path(out)
    with (out / 'execution.log').open('a') as log:
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        try:
            os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                              NUMEXPR_NUM_THREADS='1')
            os.sched_setaffinity(0, {cpu})
            from kmd_toc.column_generation.backends import backend_environment
            setup_s = preload_dependencies(spec['config'])  # imports only
            ready.send({'ok': True, 'pid': os.getpid(), 'cpu_affinity': sorted(os.sched_getaffinity(0)),
                        'dependency_setup_s': setup_s,
                        'quantum_backend_environment': backend_environment(spec['config'])})
            ready.close()
            go.wait()
            remaining = deadline.value - time.perf_counter()
            if remaining <= 0:
                dump(out / 'branch_failure.json', {'status': 'NO_TIME_BEFORE_INPUT', 'pid': os.getpid()})
                return
            local = {**spec, 'tau_s': remaining}
            dump(out / 'spec.json', local)
            execute(local, out)
        except BaseException as error:
            traceback.print_exc()
            dump(out / 'branch_failure.json', {'status': 'BRANCH_ERROR', 'type': type(error).__name__,
                                             'message': str(error), 'pid': os.getpid()})
            try:
                ready.send({'ok': False, 'error': str(error), 'pid': os.getpid()})
            except (OSError, ValueError):
                pass


def _stop_join(processes):
    for process in processes:
        if process.is_alive():
            process.terminate()
    for process in processes:
        process.join(timeout=.3)
        if process.is_alive():
            process.kill()
            process.join(timeout=.3)
        if process.is_alive():
            raise RuntimeError('PARALLEL_CHILD_NOT_REAPED')


def _plan(raw):
    from kmd_toc.common.models import Plan, Trip, Visit
    return Plan(**{k: v for k, v in raw.items() if k != 'trips'},
                trips=tuple(Trip(**{k: v for k, v in t.items() if k != 'visits'},
                                 visits=tuple(Visit(**v) for v in t['visits'])) for t in raw['trips']))


def select_candidate(problem, rows, epsilon):
    """Recheck every complete branch; never select an invalid low metric."""
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.independent import recompute
    candidates, audits = [], []
    for index, row in enumerate(rows):
        result = {'branch_id': index, 'accepted': False, 'status': row.get('status')}
        if (row.get('status') == 'VALIDATED' and row.get('feasible') is True
                and row.get('budget_met') is True and row.get('epsilon_met') is True and row.get('plan')):
            try:
                plan = _plan(row['plan'])
                common, raw = validate_plan(problem, plan), recompute(problem, plan)
                valid = (common.feasible and raw['feasible']
                         and row['input_hash'] == plan.problem_hash == problem.fingerprint
                         and row['OD_hash'] == plan.od_hash == problem.od.fingerprint
                         and abs(common.D_km - float(raw['D_km'])) < 1e-7
                         and abs(common.W_min - float(raw['W_min'])) < 1e-7
                         and abs(common.D_km - row['D_km']) < 1e-7
                         and abs(common.W_min - row['W_min']) < 1e-7
                         and (epsilon is None or common.W_min <= epsilon + 1e-9))
                result.update(accepted=bool(valid), D_km=common.D_km, W_min=common.W_min)
                if valid:
                    key = (int(round(math.fsum(t.distance_m for t in plan.trips) * 10)),
                           sum(t.waiting_s for t in plan.trips), index)
                    candidates.append((key, index, plan))
            except Exception as error:
                result['error'] = str(error)
        audits.append(result)
    return (min(candidates, key=lambda x: x[0]) if candidates else None), audits


def execute_parallel(spec, out, *, allow_import_only_fork=False):
    import json
    from dataclasses import asdict
    from .worker import dump
    from .setup import preload_dependencies
    from kmd_toc.common.models import load_problem
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.independent import recompute
    from kmd_toc.column_generation.backends import backend_environment, observed_quantum_timings

    out = Path(out)
    setup_begin = time.perf_counter()
    profile = cpu_profile(spec['config'])
    if 'execution_cpu_profile' in spec:
        registered = spec['execution_cpu_profile']
        if (registered['workers'] != profile['workers']
                or not set(registered['cpu_ids']).issubset(os.sched_getaffinity(0))):
            raise ValueError('REGISTERED_PARALLEL_CPU_PROFILE_UNAVAILABLE')
        profile = registered
    os.sched_setaffinity(0, set(profile['cpu_ids']))
    preload_dependencies(spec['config'])
    quantum_environment = backend_environment(spec['config'])
    native_threads = len(list(Path('/proc/self/task').iterdir()))
    mode = 'fork' if allow_import_only_fork and native_threads == 1 and 'fork' in mp.get_all_start_methods() else 'spawn'
    context = mp.get_context(mode)
    go, deadline = context.Event(), context.Value('d', 0.)
    seeds = branch_seeds(spec['seeds'], profile['workers'])
    processes, branches, connections = [], [], []
    stages = out / 'stages'
    stages.mkdir(exist_ok=True)
    ready_records = []
    try:
        for index, cpu in enumerate(profile['cpu_ids']):
            branch_out = out / 'branches' / str(index)
            branch_out.mkdir(parents=True, exist_ok=False)
            branch_spec = {**spec, 'trial_id': spec['trial_id'] + f'_internal{index}',
                           'phase': 'parallel_internal_branch', 'seeds': seeds[index],
                           'parallel_branch_id': index}
            recv, send = context.Pipe(duplex=False)
            process = context.Process(target=_branch_entry, args=(branch_spec, str(branch_out), cpu, go, deadline, send))
            process.start()
            send.close()
            processes.append(process)
            connections.append(recv)
            branches.append(branch_out)
        setup_deadline = setup_begin + spec['config'].get('dependency_setup_limit_s', 240)
        for recv in connections:
            if not recv.poll(max(0., setup_deadline - time.perf_counter())):
                raise RuntimeError('PARALLEL_WORKER_SETUP_TIMEOUT')
            record = recv.recv()
            if not record['ok']:
                raise RuntimeError('PARALLEL_WORKER_SETUP_ERROR:' + record['error'])
            ready_records.append(record)
        setup_s = time.perf_counter() - setup_begin
        dump(out / 'parallel_setup.json', {'profile': profile, 'start_method': mode,
             'native_threads_before_fork': native_threads, 'seconds': setup_s,
             'workers': ready_records, 'no_input_solver_or_circuit_before_T': True})

        start, cpu_start = time.perf_counter(), time.process_time()
        events = [{'name': 'input_load_start', 'elapsed_s': 0.}]
        def mark(name):
            events.append({'name': name, 'elapsed_s': time.perf_counter() - start})
        dump(out / 'progress.json', {'start_perf_counter': start, 'deadline': start + spec['tau_s'],
                                     'timing_finished': False, 'worker_pid': os.getpid()})
        p = load_problem(spec['input_dir'])
        if (p.fingerprint != spec.get('registered_input_hash', p.fingerprint)
                or p.od.fingerprint != spec.get('registered_OD_hash', p.od.fingerprint)):
            raise ValueError('REGISTERED_INPUT_OR_OD_CHANGED')
        mark('input_load_end')
        deadline.value = start + spec['tau_s'] * (1 - profile['coordinator_reserve_fraction'])
        go.set()
        mark('parallel_branches_released')
        timed_out = set()
        while any(process.is_alive() for process in processes):
            if time.perf_counter() >= deadline.value:
                timed_out = {i for i, process in enumerate(processes) if process.is_alive()}
                break
            time.sleep(.01)
        _stop_join(processes)
        mark('parallel_branches_joined')
        rows, summaries = [], []
        for index, (directory, process) in enumerate(zip(branches, processes)):
            path = directory / 'worker_result.json'
            row = json.loads(path.read_text()) if path.exists() else {'status': 'NO_BRANCH_RESULT'}
            if index in timed_out:
                row = {**row, 'status': 'BRANCH_WALL_TIMEOUT'}
            rows.append(row)
            summary = {k: row.get(k) for k in ['status', 'D_km', 'W_min', 'T_program_s', 'T_attempt_wall_s',
                      'process_cpu_s', 'max_rss_KiB', 'quantum_seed_used', 'error', 'input_hash', 'OD_hash']}
            quantum = [json.loads(p.read_text()) for p in sorted((directory / 'stages').glob('D_AOA_*.json'))]
            quantum_complete = spec['method'] != 'D' or (row.get('status') == 'VALIDATED' and not row.get('error') and index not in timed_out)
            summary.update(branch_id=index, pid=process.pid, cpu_affinity=ready_records[index]['cpu_affinity'],
                           seeds=seeds[index], exitcode=process.exitcode, timed_out=index in timed_out,
                           children_joined=not process.is_alive(), quantum_calls=len(quantum),
                           quantum_accounting_complete=quantum_complete,
                           quantum_backend_environment=ready_records[index]['quantum_backend_environment'],
                           statevector_backends_observed=sorted({q.get('statevector_backend', 'unknown') for q in quantum}),
                           observed_quantum_timing_s=observed_quantum_timings(quantum),
                           training_shots=sum(q['training_total_shots'] for q in quantum),
                           final_shots=sum(q['final_total_shots'] for q in quantum))
            summaries.append(summary)
        selected, candidate_audits = select_candidate(p, rows, spec['epsilon_W_min'])
        mark('parallel_candidate_selection_end')
        dump(stages / 'parallel_candidates.json', {'branches': summaries, 'candidate_validation': candidate_audits})
        plan = common = second = None
        if selected is not None:
            _, selected_index, plan = selected
            plan = replace(plan, method_settings={**plan.method_settings,
                'cpu_parallel': {**profile, 'selected_branch': selected_index,
                    'root_seeds': spec['seeds'], 'selected_seeds': seeds[selected_index],
                    'all_branches': summaries, 'selection': 'validated minimum D, then W, then branch index',
                    'quantum_totals_include_unselected_branches': True}})
            mark('final_validation_start')
            common, second = validate_plan(p, plan), recompute(p, plan)
        mark('final_validation_end' if plan is not None else 'failed')
        elapsed = events[-1]['elapsed_s']
        parent_cpu_s = time.process_time() - cpu_start
        feasible = bool(common and common.feasible and second and second['feasible']
                        and abs(common.D_km - float(second['D_km'])) < 1e-7
                        and abs(common.W_min - float(second['W_min'])) < 1e-7)
        within = elapsed <= spec['tau_s']
        epsilon_met = bool(feasible and (spec['epsilon_W_min'] is None or common.W_min <= spec['epsilon_W_min'] + 1e-9))
        status = ('VALIDATED' if feasible and within and epsilon_met else
                  'TIME_BUDGET_EXCEEDED' if not within else 'NO_VERIFIED_PLAN')
        row = {k: spec[k] for k in ['trial_id', 'scenario_id', 'instance_id', 'method', 'repetition_id',
                                   'phase', 'epsilon_W_min', 'tau_s']}
        row.update(status=status, feasible=feasible, budget_met=within, epsilon_met=epsilon_met,
            standard_output_complete=False, T_kind='program_wall',
            D_km=common.D_km if feasible else None, W_min=common.W_min if feasible else None,
            T_program_s=elapsed if feasible else None, T_attempt_wall_s=elapsed,
            failure_elapsed_s=elapsed if status != 'VALIDATED' else None,
            input_hash=p.fingerprint, OD_hash=p.od.fingerprint,
            demand_seed=None, demand_random_generator=None, input_experiment_seed=p.experiment.random_seed,
            demand_generation='retained common input; no demand generation', **spec['seeds'],
            random_generator='SeedSequence domain-separated branch streams; each branch uses existing solver/quantum generators',
            solver_seed_scope='root branches to explicitly logged per-branch seeds; CP-SAT/OR ReSeed; HiGHS native threads=1',
            quantum_seed_used=quantum_use_state(spec['method'], summaries),
            environment_version=spec.get('environment_version'),
            quantum_backend_environment=quantum_environment,
            max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            process_cpu_s=parent_cpu_s,
            total_process_cpu_s=(parent_cpu_s + sum(s['process_cpu_s'] for s in summaries)
                                 if all(s.get('process_cpu_s') is not None for s in summaries) else None),
            observed_partial_process_cpu_s=parent_cpu_s + sum(s.get('process_cpu_s') or 0 for s in summaries),
            resource_accounting='CPU total is measured parent plus returned branch CPU; killed branch CPU unknown, never imputed as complete',
            all_branch_CPU_accounted=all(s.get('process_cpu_s') is not None for s in summaries),
            worker_pid=os.getpid(), cpu_affinity=sorted(os.sched_getaffinity(0)),
            dependency_setup_s=setup_s, dependency_setup_scope='uniform library and waiting-process setup only; all input/solver work inside parent T',
            error=None if status == 'VALIDATED' else {'message': status, 'branch_statuses': [s['status'] for s in summaries]},
            timing_events=events, T_boundary='before coordinator common input load through all children joined, selection and final two validations; exports excluded',
            T_human_s=None, T_human_status='not applicable', T_program_role='primary measured planning time',
            validation=common.as_dict() if common else None, second_validation=second,
            plan=asdict(plan) if plan else None, execution_config_sha256=spec['config_sha256'],
            cpu_parallel_profile=profile, parallel_start_method=mode, parallel_branches=summaries,
            selected_branch=selected[1] if selected else None,
            quantum_accounting_complete=all(s['quantum_accounting_complete'] for s in summaries),
            total_quantum_calls=sum(s['quantum_calls'] for s in summaries) if all(s['quantum_accounting_complete'] for s in summaries) else None,
            total_training_shots=sum(s['training_shots'] for s in summaries) if all(s['quantum_accounting_complete'] for s in summaries) else None,
            total_final_shots=sum(s['final_shots'] for s in summaries) if all(s['quantum_accounting_complete'] for s in summaries) else None,
            completed_quantum_call_observations=sum(s['quantum_calls'] for s in summaries),
            stage_evidence_files=['stages/parallel_candidates.json'])
        timing_keys = summaries[0]['observed_quantum_timing_s']
        row['observed_quantum_timing_s'] = {
            key: (sum(s['observed_quantum_timing_s'][key] for s in summaries)
                  if all(s['observed_quantum_timing_s'][key] is not None for s in summaries) else None)
            for key in timing_keys}
        row['total_quantum_timing_s'] = (row['observed_quantum_timing_s']
                                         if row['quantum_accounting_complete'] else None)
        row['aggregate_RSS_upper_bound_KiB'] = (row['max_rss_KiB'] + sum(s['max_rss_KiB'] for s in summaries)
                                                if all(s.get('max_rss_KiB') is not None for s in summaries) else None)
        row['aggregate_RSS_scope'] = 'sum of process high-water marks including shared pages; not measured simultaneous physical RSS; incomplete if a branch was killed'
        dump(out / 'progress.json', {'start_perf_counter': start, 'deadline': start + spec['tau_s'],
                                    'timing_finished': True, 'T_program_s': elapsed})
        dump(out / 'worker_result.json', row)
        return row
    finally:
        _stop_join(processes)
        for connection in connections:
            connection.close()
