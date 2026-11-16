"""Day pricing: exhaustive grid oracle versus unchanged Huang AOA trip generator.

AOA decides trip customer selection/order; classical completion decides partner,
vehicle and loading times. Only true complete-day reduced cost admits a column.
"""
from dataclasses import replace
from time import perf_counter
import numpy as np
from kmd_toc.column_generation.models import Instance, Route
from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
from kmd_toc.column_generation.reduction import contract
from .generation import enumerate_days
from .master import reduced_cost
from .validation import validate_day


def exact_price(problem, all_columns, lp, profile):
    ranked = sorted(((reduced_cost(problem, c, lp['dual'], profile), c) for c in all_columns),
                    key=lambda item: (item[0], item[1].column_id))
    return ranked


def aoa_day_candidates(problem, pool, lp, profile, config, iteration):
    start = perf_counter()
    dual = lp['dual']
    ids = problem.base.customers
    top = sorted(ids, key=lambda i: (-dual['customer'][i - 1], i))[:3]
    anchor = ids[iteration % len(ids)]
    near = sorted(ids, key=lambda i: (problem.base.distance[anchor, i], i))[:3]
    sets = []
    for subset in [top, near]:
        if set(subset) not in [set(s) for s in sets]:
            sets.append(subset)
    weight = 0.0 if lp['phase'] == 'I' else (1.0 if profile.primary == 'D' else -dual['other'])
    proxy = Instance(problem.base.name + '_AOA_proxy', weight * problem.base.distance,
                     problem.base.demand, max(v.capacity for v in problem.vehicles))
    required, quantum_logs = set(), []
    for domain_index, subset in enumerate(sets):
        domain = contract(proxy, dual['customer'], [(i,) for i in subset], 'day_trip_proxy', slots=config.slots)
        cfg = replace(config, solver_seed=config.solver_seed + 100 * iteration + domain_index)
        result = PricingAOA(domain.pricing, domain.dual, cfg).run()
        sampled = {domain.expand(Route(tuple(r))) for r in result['routes']}
        required.update(sampled)
        quantum_logs.append({'subset_original_ids': subset, 'distance_proxy_weight': weight,
                             'result': result, 'expanded_sampled_trips': [r.customers for r in sorted(sampled)]})
    partners = {Route((i,)) for i in ids}
    partners.update(Route(t.customers) for c in pool for t in c.trips)
    partners.update(required)
    columns = enumerate_days(problem, route_pool=partners, required_routes=required) if required else []
    for column in columns:
        reasons = validate_day(problem, column)
        if reasons:
            raise RuntimeError(f'Invalid AOA-completed day: {reasons}')
    # No classical oracle route is inserted. Every completion contains a measured trip.
    ranked = sorted(((reduced_cost(problem, c, dual, profile), c) for c in columns),
                    key=lambda item: (item[0], item[1].column_id))
    return ranked, {'seconds': perf_counter() - start, 'quantum': quantum_logs,
                    'sampled_trip_count': len(required), 'classical_partner_count': len(partners),
                    'completed_days': len(columns), 'oracle_fallback_used': False,
                    'scope': 'AOA_TRIP_SUBSETS_PLUS_FINITE_GRID_COMPLETION'}
