"""Fresh-process trial. All method work and both plan checks are inside T."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import time
from kmd_toc.common.models import load_problem
from kmd_toc.common.validation import validate_plan
from kmd_toc.baseline_a.independent import recompute
from .budget import Budget, BudgetExceeded


def dump(path, value):
    def default(x):
        import numpy as np
        if isinstance(x, np.generic):
            return x.item()
        if isinstance(x, np.ndarray):
            return x.tolist()
        raise TypeError(type(x).__name__)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, default=default) + '\n')


def execute(spec, out):
    out = Path(out)
    from .setup import preload_dependencies
    from kmd_toc.column_generation.backends import backend_environment
    dependency_setup_s = preload_dependencies(spec['config'])
    quantum_environment = backend_environment(spec['config'])
    stages = out / 'stages'
    stages.mkdir(exist_ok=True)
    budget = Budget(spec['tau_s'], spec['config']['allocation']['validation_reserve_fraction'],
                    capture_sink=lambda name, value: dump(stages / (name + '.json'), value),
                    adaptive_validation=spec['config']['allocation'].get('adaptive_validation_reserve', False),
                    verification_passes=spec['config']['allocation'].get('remaining_verification_passes', 2),
                    jitter_fraction=spec['config']['allocation'].get('validation_jitter_fraction', .02))
    if spec.get('design_telemetry'):
        from kmd_toc.comparison_v1.telemetry import install
        install(out, budget.start)
    process_cpu_start = time.process_time()
    dump(out / 'progress.json', {'start_perf_counter': budget.start, 'deadline': budget.deadline, 'timing_finished': False,
                                 'worker_pid': os.getpid(), 'cpu_affinity': sorted(os.sched_getaffinity(0))})
    plan = problem = common = second = None
    error = None
    try:
        problem = load_problem(spec['input_dir'])
        # load_problem already performs complete pinned input validation.
        if (problem.fingerprint != spec.get('registered_input_hash', problem.fingerprint)
                or problem.od.fingerprint != spec.get('registered_OD_hash', problem.od.fingerprint)):
            raise ValueError('REGISTERED_INPUT_OR_OD_CHANGED')
        budget.mark('input_load_end')
        budget.left()
        from .methods import generate
        plan = generate(problem, spec['method'], spec['epsilon_W_min'], budget, spec['seeds'], spec['config'])
        budget.mark('algorithm_and_completion_end')
        budget.left(validation=True)
        budget.mark('final_validation_start')
        common = validate_plan(problem, plan)
        second = recompute(problem, plan)
        budget.mark('final_validation_end')
    except BudgetExceeded as e:
        error = {'type': type(e).__name__, 'message': str(e), 'scheduled_budget_stop': True}
        if budget.incumbent is not None:
            from dataclasses import replace
            previous = budget.incumbent
            q = [v for k, v in budget.evidence.items() if k.startswith('D_AOA_')]
            cw_routes = {tuple(r) for r in budget.evidence.get('directed_CW', {}).get('routes', [])}
            sampled = {tuple(r) for item in q for r in item['full_routes']}
            selected = {tuple(problem.od.ids.index(v.stop_id) for v in t.visits) for t in previous.trips}
            settings = {**previous.method_settings, 'cooperative_stop_reason': error,
                        'quantum_improvement_claim': False,
                        'classical_only_control': spec['method'] in ('D_CLASSICAL_CONTROL','D_CLASSICAL_REPLACEMENT'),
                        'classical_replacement':spec['method']=='D_CLASSICAL_REPLACEMENT',
                        'algorithm_path_incomplete': True, 'quantum_enabled': spec['method'] == 'D',
                        'quantum': q, 'quantum_calls': len(q), 'quantum_new_routes': len(sampled - cw_routes),
                        'new_quantum_routes_in_final': len(selected & (sampled - cw_routes)),
                        'base_columns': budget.evidence.get('D_base_master', {}).get('columns'),
                        'hybrid_columns': budget.evidence.get('D_hybrid_master', {}).get('columns'),
                        'hybrid': budget.evidence.get('D_hybrid_master', {}).get('outcome', {'catalogue_construction': {'truncated_at_time_limit': None, 'not_executed': True}}),
                        'completion_selected_source': 'verified_incumbent_after_cooperative_stop'}
            plan = replace(previous, method_settings=settings,
                           method_id='B' if spec['method'] in ('D_CLASSICAL_CONTROL','D_CLASSICAL_REPLACEMENT') else previous.method_id,
                           execution_kind='classical' if spec['method'] in ('D_CLASSICAL_CONTROL','D_CLASSICAL_REPLACEMENT') else previous.execution_kind)
            try:
                budget.left(validation=True)
                budget.mark('final_validation_start')
                common = validate_plan(problem, plan)
                second = recompute(problem, plan)
                budget.mark('final_validation_end')
            except Exception as final_error:
                error['final_validation_error'] = str(final_error)
                budget.mark('failed')
        else:
            budget.mark('failed')
    except Exception as e:
        error = {'type': type(e).__name__, 'message': str(e)}
        budget.mark('failed')
    elapsed = budget.events[-1]['elapsed_s']
    process_cpu_s = time.process_time() - process_cpu_start
    dump(out / 'progress.json', {'start_perf_counter': budget.start, 'deadline': budget.deadline,
                                 'timing_finished': True, 'T_program_s': elapsed})
    feasible = bool(common is not None and common.feasible and second and second['feasible'])
    if feasible:
        feasible = (abs(common.D_km - float(second['D_km'])) <= 1e-7
                    and abs(common.W_min - float(second['W_min'])) <= 1e-7)
    within = elapsed <= spec['tau_s']
    epsilon_met = bool(feasible and (spec['epsilon_W_min'] is None or common.W_min <= spec['epsilon_W_min'] + 1e-9))
    status = ('VALIDATED' if feasible and within and epsilon_met else
              'TIME_BUDGET_EXCEEDED' if not within else
              'VALIDATION_FAILURE' if plan is not None else 'NO_VERIFIED_PLAN')
    row = {k: spec[k] for k in ['trial_id', 'scenario_id', 'instance_id', 'method', 'repetition_id', 'phase', 'epsilon_W_min', 'tau_s']}
    row.update(status=status, feasible=feasible, budget_met=within, epsilon_met=epsilon_met,
               standard_output_complete=False, T_kind='program_wall',
               D_km=common.D_km if feasible else None, W_min=common.W_min if feasible else None,
               T_program_s=elapsed if feasible else None, T_attempt_wall_s=elapsed,
               failure_elapsed_s=elapsed if status != 'VALIDATED' else None,
               input_hash=problem.fingerprint if problem else None,
               OD_hash=problem.od.fingerprint if problem else None,
               demand_seed=None, demand_random_generator=None,
               input_experiment_seed=problem.experiment.random_seed if problem else None,
               demand_generation='frozen deterministic SHA256 rank / deterministic validation subsets; no demand PRNG',
               demand_seed_semantics_corrected=True, **spec['seeds'],
               demand_randomness='frozen input; no runtime demand generation',
               quantum_seed_used=any(k.startswith('D_AOA_') for k in budget.evidence),
               solver_randomness='B generator deterministic; completion CP-SAT uses solver_seed',
               solver_seed_scope='OR Routing ReSeed for C; shared CP-SAT for all; HiGHS seed not explicitly set',
               D_HiGHS_seed=None,
               random_generator='NumPy SeedSequence PCG64 / Qiskit Statevector; versions in environment',
               environment_version=spec.get('environment_version'),
               quantum_backend_environment=quantum_environment,
               max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               process_cpu_s=process_cpu_s,
               worker_pid=os.getpid(), cpu_affinity=sorted(os.sched_getaffinity(0)),
               dependency_setup_s=dependency_setup_s,
               dependency_setup_scope='uniform library imports before any delivery input read; same union for all methods; no problem-specific computation',
               error=error, timing_events=budget.events,
               validation_reserve_s=budget.reserve, max_observed_validation_s=budget.max_validation_s,
               stage_evidence_files=[str(p.relative_to(out)) for p in sorted(stages.glob('*.json'))],
               T_boundary='before common input load through common validator AND second raw recomputation; exports excluded',
               T_human_s=None, T_human_status='unmapped external episode reference' if spec['method'] == 'A' else 'not applicable',
               T_program_role='auxiliary program time, not human T' if spec['method'] == 'A' else 'primary measured planning time',
               validation=common.as_dict() if common else None, second_validation=second,
               plan=asdict(plan) if plan else None,
               execution_config_sha256=spec['config_sha256'])
    if spec['method'] == 'A':
        import hashlib
        reference_path = Path('configs/toc_delivery/a_human_route_time_reference_v1.json')
        row['T_human_route_episode_reference'] = json.loads(reference_path.read_text())
        row['T_human_reference_sha256'] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    dump(out / 'worker_result.json', row)
    return row


def execute_trial(spec, out, *, allow_import_only_fork=False):
    from .parallel import enabled, execute_parallel
    if enabled(spec):
        return execute_parallel(spec, out, allow_import_only_fork=allow_import_only_fork)
    return execute(spec, out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', required=True)
    args = parser.parse_args()
    path = Path(args.spec)
    execute_trial(json.loads(path.read_text()), path.parent, allow_import_only_fork=True)


if __name__ == '__main__':
    main()
