"""Finite CG control, Huang fig.1. Small reference only; no study-data access.

Inputs: artificial Instance and explicit pricing/config. Outputs: all LP/dual/
pricing traces and restricted integer solution. Exact oracle is diagnostics only
in AOA runs; it never injects columns. Failure is an exception, not a fake plan.
"""
from dataclasses import replace
from time import perf_counter
from .models import Route, enumerate_routes, reduced_cost
from .master import solve_lp, solve_integer
from .aoa import PricingAOA, AOAConfig
from .reduction import build_domains


def run_column_generation(instance, pricing='classical', config=None, variant='cover',
                          max_rounds=20, batch_size=5, reduced=False):
    if pricing not in ('classical', 'aoa') or max_rounds < 1 or batch_size < 1:
        raise ValueError('Invalid finite CG settings')
    start = perf_counter()
    config = config or AOAConfig()
    universe = enumerate_routes(instance)
    pool = [Route((i,)) for i in instance.customers]
    trace, aoa_runs, added_from_aoa = [], [], 0
    stop = 'CG_ITERATION_LIMIT'
    for iteration in range(max_rounds):
        lp = solve_lp(instance, pool, variant)
        dual = lp['dual']
        exact = sorted(((reduced_cost(instance, r, dual), r) for r in universe),
                       key=lambda item: (item[0], item[1].customers))
        candidates = universe
        local_runs = []
        if pricing == 'aoa':
            candidates = []
            domains = build_domains(instance, dual) if reduced else None
            if domains is None:
                result = PricingAOA(instance, dual,
                                    replace(config, solver_seed=config.solver_seed + iteration * 100)).run()
                candidates = [Route(tuple(ids)) for ids in result['routes']]
                result['pricing_domain'] = 'all_customers_with_slot_limit'
                local_runs.append(result)
            else:
                for d_index, domain in enumerate(domains):
                    cfg = replace(config, slots=domain.slots,
                                  solver_seed=config.solver_seed + iteration * 100 + d_index)
                    result = PricingAOA(domain.pricing, domain.dual, cfg).run()
                    candidates.extend(domain.expand(Route(tuple(ids))) for ids in result['routes'])
                    result['pricing_domain'] = domain.name
                    result['fragment_groups'] = domain.groups
                    local_runs.append(result)
            aoa_runs.append({'iteration': iteration, 'runs': local_runs})
        valid = sorted(((reduced_cost(instance, r, dual), r) for r in set(candidates)
                        if r not in set(pool)), key=lambda item: (item[0], item[1].customers))
        new = [(cost, route) for cost, route in valid if cost < -1e-7][:batch_size]
        trace.append({'iteration': iteration, 'lp': lp, 'pool_size': len(pool),
                      'full_oracle_min_reduced_cost': exact[0][0],
                      'full_oracle_best_route': list(exact[0][1].nodes()),
                      'oracle_improvement_exists': bool(exact[0][0] < -1e-7),
                      'found_candidate_min_reduced_cost': min((c for c, _ in valid), default=None),
                      'added': [{'customers': list(r.customers), 'reduced_cost': c} for c, r in new],
                      'elapsed_seconds': perf_counter() - start})
        if not new:
            stop = 'PRICING_CERTIFIED_NONNEGATIVE' if pricing == 'classical' else 'AOA_NO_IMPROVING_COLUMN'
            break
        pool.extend(r for _, r in new)
        if pricing == 'aoa':
            added_from_aoa += len(new)
    # Always re-solve after last addition, including when the iteration cap is hit.
    final_lp = solve_lp(instance, pool, variant)
    final_min = min(reduced_cost(instance, r, final_lp['dual']) for r in universe)
    integer = solve_integer(instance, pool)
    full_integer = solve_integer(instance, universe)  # independent diagnostic only
    return {'instance': instance.name, 'pricing': pricing, 'master_variant': variant,
            'reduced_pricing': reduced, 'trace': trace, 'aoa_runs': aoa_runs,
            'stop_reason': stop, 'full_oracle_nonnegative_at_final_dual': bool(final_min >= -1e-7),
            'final_full_oracle_min_reduced_cost': final_min, 'final_lp': final_lp,
            'integer': integer, 'full_enumeration_integer': full_integer,
            'integer_gap_to_full_enumeration': integer['objective'] - full_integer['objective'],
            'columns_added_by_aoa': added_from_aoa, 'initial_pool_size': len(instance.customers),
            'final_pool_size': len(pool), 'full_route_universe_size': len(universe),
            'total_seconds': perf_counter() - start,
            'quantum_advantage_claimed': False, 'oracle_columns_injected': False}
