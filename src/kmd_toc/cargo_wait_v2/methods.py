"""Retain route algorithms; current B/C/D operation uses common FCFS_v1.

This branch-level API is for the existing four-process orchestrator or small
unit validation. It is not authorization or an entry point for main runs.
"""
from dataclasses import replace
from .evaluation import evaluate, load_model, VERSION


def generate(problem, method, config, ledger, seeds, *, model=None, historical_reproduction=False):
    reported_method = method
    if method == 'Q' and not historical_reproduction:
        method = 'D'  # Explicit research alias; historical result IDs stay intact.
    model = load_model() if model is None else model
    if problem.experiment.kind != 'synthetic_validation' or len(problem.stops) > 12:
        raise ValueError('MAIN_EXPERIMENT_HOLD_SMALL_SYNTHETIC_GENERATION_ONLY')
    if method not in ('B', 'C', 'D'):
        raise ValueError('ONLY_BCD_GENERATE_PLANS_A_IS_EXTERNAL')
    required = ('ready_is_arrival_facility_queue_assumption', 'immediate_handover_assumption', 'none_assumption')
    if tuple(model[k] for k in ('loading_wait', 'destination_wait', 'other_wait')) != required:
        raise ValueError('EVENT_WAIT_OPTIMIZATION_REQUIRES_NEW_APPROVED_MODEL')
    # Current artificial generation uses the approved common operating policy.
    # Explicit history retains the former schedules and frozen result semantics.
    if not historical_reproduction:
        config = {**config, 'operating_policy': 'FCFS_v1'}
    from kmd_toc.termination_v1.methods import generate as preserved_generate
    plan = preserved_generate(problem, method, config, ledger, seeds)
    if not historical_reproduction:
        from kmd_toc.fcfs_v1.validation import require_fcfs
        require_fcfs(problem, plan)
    report = evaluate(problem, plan, model=model)
    # Under these explicit assumptions, every candidate's total W is exactly
    # the unchanged solver loading W. No weight, normalizer or stop is changed.
    legacy_s = sum(t.waiting_s for t in plan.trips)
    if report['W_total_min'] != legacy_s / 60:
        raise ValueError('SOLVER_W_AND_NEW_W_DISAGREE')
    index = {s: i for i, s in enumerate(problem.od.ids)}
    final_routes = {tuple(index[v.stop_id] for v in t.visits) for t in plan.trips}
    q_routes = {tuple(r) for call in plan.method_settings.get('quantum_calls', [])
                for r in call.get('accepted_full_routes', [])}
    quantum = {'quantum_routes_selected': sorted(final_routes & q_routes),
               'new_pricing_routes_in_final': plan.method_settings.get('new_pricing_routes_in_final', 0),
               'novel_route_contribution_confirmed': plan.method_settings.get('new_pricing_routes_in_final', 0) > 0,
               'sampled_seed_overlap_is_not_novel_contribution': True,
               'quantum_improvement_claim': False}
    ledger.emit('cargo_wait_v2_evaluated', W_total_min=report['W_total_min'],
                W_mean_min_per_operation=report['W_mean_min_per_operation'],
                objective_equivalent_under_assumptions=True, quantum_contribution=quantum)
    return replace(plan, method_settings={**plan.method_settings, 'evaluation_version': VERSION,
                   'reported_method': reported_method,
                   'wait_model_hash': report['model_hash'], 'solver_W_equivalence': True,
                   'quantum_contribution_audit': quantum}), report
