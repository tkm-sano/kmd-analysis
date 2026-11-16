"""Classical RMP/dual/IP reference, Huang eqs. 7--15.

SciPy HiGHS LP (cover or partition); HiGHS MIP final partition. No RNG.
Unsuccessful solves raise RuntimeError; never label a restricted IP globally optimal.
"""
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from .models import route_cost


def incidence(instance, routes):
    return np.asarray([[float(i in r.customers) for r in routes]
                       for i in instance.customers])


def solve_lp(instance, routes, variant='cover'):
    if variant not in ('cover', 'partition') or not routes:
        raise ValueError('Unknown master variant or empty pool')
    a = incidence(instance, routes)
    c = np.asarray([route_cost(instance, r) for r in routes])
    kwargs = {'A_ub': -a, 'b_ub': -np.ones(len(a))} if variant == 'cover' else {
        'A_eq': a, 'b_eq': np.ones(len(a))}
    result = linprog(c, bounds=(0, None), method='highs', **kwargs)
    if not result.success:
        raise RuntimeError(f'LP failed: {result.message}')
    dual = -result.ineqlin.marginals if variant == 'cover' else result.eqlin.marginals
    rc = c - a.T @ dual
    if np.min(rc) < -1e-7 or abs(result.fun - sum(dual)) > 1e-7:
        raise RuntimeError('LP dual/reduced-cost consistency failed')
    return {'objective': float(result.fun), 'dual': dual.tolist(),
            'weights': result.x.tolist(), 'pool_reduced_costs': rc.tolist(),
            'dual_gap': float(result.fun - sum(dual)), 'variant': variant}


def solve_integer(instance, routes):
    a = incidence(instance, routes)
    c = np.asarray([route_cost(instance, r) for r in routes])
    result = milp(c, integrality=np.ones(len(routes)), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(a, 1, 1),
                  options={'mip_rel_gap': 0.0})
    if not result.success or result.x is None:
        raise RuntimeError(f'Restricted integer master failed: {result.message}')
    selected = [r for r, value in zip(routes, result.x) if value > .5]
    visits = [i for r in selected for i in r.customers]
    if sorted(visits) != list(instance.customers):
        raise RuntimeError('Integer output violates exactly-once delivery')
    return {'objective': float(result.fun), 'routes': [list(r.nodes()) for r in selected],
            'scope': 'RESTRICTED_POOL_INTEGER_OPTIMAL', 'mip_gap': float(result.mip_gap),
            'route_count': len(selected), 'exactly_once_verified': True}
