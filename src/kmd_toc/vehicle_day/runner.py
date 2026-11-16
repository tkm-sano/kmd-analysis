"""Finite day-column CG; full oracle is diagnostics only in AOA mode.

Explicit Phase I/II, complete-day reduced costs, no wall-time primary stop.
All stored timings distinguish diagnostic full solves from the method runtime.
"""
from time import perf_counter
from .generation import seed_plan
from .master import solve_lp, solve_integer, reduced_cost
from .pricing import exact_price, aoa_day_candidates
from .validation import validate_plan, assign_berths


def run_day_cg(problem, all_columns, profile, mode='classical', aoa_config=None,
               max_rounds=80, batch_size=20, use_seed=True):
    if mode not in ('classical', 'aoa') or (mode == 'aoa' and aoa_config is None):
        raise ValueError('Invalid day-CG pricing settings')
    started, diagnostics_seconds = perf_counter(), 0.0
    pool = seed_plan(problem) if use_seed else []
    initial = validate_plan(problem, pool)
    if pool and not initial['valid']:
        raise RuntimeError('Invalid rule-constructed initial plan')
    if pool and profile.other_limit is not None and sum(profile.other(c) for c in pool) > profile.other_limit + 1e-9:
        pool = []
    phase, trace, stop, negative_added = 'I', [], 'CG_ITERATION_LIMIT', 0
    for iteration in range(max_rounds):
        lp = solve_lp(problem, pool, profile, phase)
        if not lp['success']:
            stop = lp['reason']
            break
        if phase == 'I' and lp['objective'] <= 1e-7:
            phase = 'II'
            lp = solve_lp(problem, pool, profile, phase)
            if not lp['success']:
                raise RuntimeError('Phase I closure did not lead to feasible Phase II')
        diagnostic_start = perf_counter()
        oracle = exact_price(problem, all_columns, lp, profile)
        oracle_seconds = perf_counter() - diagnostic_start
        if mode == 'aoa':
            diagnostics_seconds += oracle_seconds
        pricing_log = None
        if mode == 'classical':
            # The oracle above is the actual pricing operation here, not excluded diagnostics.
            ranked = oracle
        else:
            ranked, pricing_log = aoa_day_candidates(problem, pool, lp, profile, aoa_config, iteration)
        existing = {c.identity for c in pool}
        new = [(rc, c) for rc, c in ranked if rc < -1e-7 and c.identity not in existing][:batch_size]
        trace.append({'iteration': iteration, 'phase': phase, 'pool_size': len(pool), 'lp': lp,
                      'full_grid_oracle_min_rc': oracle[0][0],
                      'candidate_min_rc': ranked[0][0] if ranked else None,
                      'added': [{'column_id': c.column_id, 'rc': rc,
                                 'vehicle_id': c.vehicle_id,
                                 'trips': [list(t.customers) for t in c.trips]} for rc, c in new],
                      'aoa': pricing_log})
        if not new:
            stop = 'GRID_PRICING_CERTIFIED' if mode == 'classical' else 'AOA_NO_IMPROVING_DAY'
            break
        pool.extend(c for _, c in new)
        negative_added += len(new)
    final = solve_lp(problem, pool, profile, phase)
    if final['success'] and phase == 'I' and final['objective'] <= 1e-7:
        phase = 'II'
        final = solve_lp(problem, pool, profile, phase)
    integer = solve_integer(problem, pool, profile) if phase == 'II' else {
        'success': False, 'reason': 'PHASE_I_UNSERVED_CUSTOMERS'}
    metrics = validate_plan(problem, integer['selected']) if integer['success'] else None
    if metrics is not None and not metrics['valid']:
        raise RuntimeError('Integer result failed independent validator')
    assignments = assign_berths(problem, integer['selected']) if integer['success'] else []
    method_done = perf_counter()
    method_seconds = method_done - started - diagnostics_seconds
    diagnostic_start = perf_counter()
    full_integer = solve_integer(problem, all_columns, profile)
    full_lp = solve_lp(problem, all_columns, profile, 'II')
    if final['success']:
        full_rc = min(reduced_cost(problem, c, final['dual'], profile) for c in all_columns)
    else:
        full_rc = None
    diagnostics_seconds += perf_counter() - diagnostic_start
    causes = []
    if sum(problem.base.demand) > 2 * sum(v.capacity for v in problem.vehicles):
        causes.append('TOTAL_CAPACITY_NECESSARY_CONDITION')
    if not full_integer['success']:
        causes.append('FULL_GRID_DOMAIN_INFEASIBLE')
    if phase == 'I' and final['success'] and final['objective'] > 1e-7:
        causes.append('PHASE_I_UNSERVED_CUSTOMERS')
    return {'mode': mode, 'profile': {'primary': profile.primary, 'other_limit': profile.other_limit},
            'initial_plan': initial, 'negative_columns_added': negative_added,
            'trace': trace, 'stop_reason': stop, 'final_phase': phase, 'final_lp': final,
            'integer': integer, 'metrics': metrics, 'berth_assignments': assignments,
            'full_grid_lp': full_lp, 'full_grid_integer': full_integer,
            'integer_gap': integer['objective'] - full_integer['objective']
                if integer['success'] and full_integer['success'] else None,
            'final_full_oracle_min_rc': full_rc, 'pool_size': len(pool),
            'all_column_count': len(all_columns), 'oracle_fallback_used': False,
            'method_wall_s_including_validation': method_seconds,
            'infeasibility_causes': causes,
            'diagnostic_wall_s': diagnostics_seconds,
            'total_reference_wall_s': perf_counter() - started}
