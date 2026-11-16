"""A restricted-pricing miss at an optimal RMP dual, on an artificial problem."""
import argparse
from pathlib import Path
from kmd_toc.column_generation.models import artificial_instance, Instance, Route, enumerate_routes, reduced_cost
from kmd_toc.column_generation.reduction import contract, exact_domain_routes
from kmd_toc.column_generation.master import solve_lp
from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
from kmd_toc.column_generation.experiment import write_json


def main(output):
    base = artificial_instance(6)
    instance = Instance('artificial_bad_fragments', base.distance, (0, 1, 1, 1, 1, 1, 1), 2)
    groups = ((1, 3), (2, 5), (4, 6))
    initial_domain = contract(instance, [0] * 6, groups, 'bad_fragments')
    restricted = exact_domain_routes(instance, initial_domain)
    pool = [Route((i,)) for i in instance.customers] + restricted
    lp = solve_lp(instance, pool)
    domain = contract(instance, lp['dual'], groups, 'bad_fragments')
    full = enumerate_routes(instance)
    full_best = min(full, key=lambda r: reduced_cost(instance, r, lp['dual']))
    full_min = reduced_cost(instance, full_best, lp['dual'])
    restricted_min = min(reduced_cost(instance, r, lp['dual']) for r in restricted)
    assert full_min < -1e-7 and restricted_min >= -1e-7
    aoa = PricingAOA(domain.pricing, domain.dual, AOAConfig(solver_seed=1501)).run()
    expanded = [domain.expand(Route(tuple(ids))) for ids in aoa['routes']]
    found = min((reduced_cost(instance, r, lp['dual']) for r in expanded), default=None)
    assert found is None or found >= -1e-7
    write_json(Path(output) / 'REDUCTION_MISS_COUNTEREXAMPLE.json', {
        'scope': 'independent_artificial_Q2_not_study_vehicle', 'groups': groups,
        'optimal_RMP': lp, 'full_min_rc': full_min,
        'full_best_route': full_best.nodes(), 'restricted_min_rc': restricted_min,
        'aoa_min_rc': found, 'global_improvement_exists': True,
        'restricted_domain_has_improvement': False, 'aoa': aoa,
        'conclusion': 'No negative restricted column is not a global pricing certificate'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    main(parser.parse_args().output)
