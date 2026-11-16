"""HiGHS day-column LP/IP, with customer, physical vehicle and berth duals.

Independent extension of local D master; external RMP separation is a reference,
not copied implementation. Phase I is explicit min unmet coverage, no big M.
"""
import numpy as np
from scipy.optimize import linprog, milp, Bounds, LinearConstraint
from .model import occupied_slots
from .validation import validate_day


def matrices(problem, columns, profile):
    n, f, u, j = len(problem.base.customers), len(problem.vehicles), problem.slots, len(columns)
    cover = np.zeros((n, j))
    resources = np.zeros((f + u + (profile.other_limit is not None), j))
    vindex = {v.vehicle_id: i for i, v in enumerate(problem.vehicles)}
    for k, c in enumerate(columns):
        errors = validate_day(problem, c)
        if errors:
            raise ValueError('INVALID_DAY_COLUMN:' + ','.join(errors))
        for i in c.customers:
            cover[i - 1, k] += 1
        resources[vindex[c.vehicle_id], k] = 1
        for slot in occupied_slots(problem, c):
            resources[f + slot, k] = 1
        if profile.other_limit is not None:
            resources[-1, k] = profile.other(c)
    rhs = np.r_[np.ones(f), np.full(u, problem.berths),
                [] if profile.other_limit is None else [profile.other_limit]]
    return cover, resources, rhs


def reduced_cost(problem, column, dual, profile):
    cost = 0.0 if dual['phase'] == 'I' else profile.cost(column)
    return float(cost - sum(dual['customer'][i - 1] for i in column.customers)
                 - dual['vehicle'][column.vehicle_id]
                 - sum(dual['berth'][u] for u in occupied_slots(problem, column))
                 - dual['other'] * profile.other(column))


def solve_lp(problem, columns, profile, phase='II'):
    if phase not in ('I', 'II'):
        raise ValueError('Unknown phase')
    a, b, rhs = matrices(problem, columns, profile)
    n, j, f = len(a), len(columns), len(problem.vehicles)
    cost = np.asarray([profile.cost(c) for c in columns])
    if phase == 'I':
        a = np.c_[a, np.eye(n)]
        b = np.c_[b, np.zeros((len(rhs), n))]
        cost = np.r_[np.zeros(j), np.ones(n)]
    if not len(cost):
        return {'success': False, 'reason': 'EMPTY_RESTRICTED_MASTER'}
    result = linprog(cost, A_eq=a, b_eq=np.ones(n), A_ub=b, b_ub=rhs,
                     bounds=(0, None), method='highs')
    if not result.success:
        return {'success': False, 'reason': 'RMP_INFEASIBLE' if result.status == 2 else 'LP_ERROR',
                'message': result.message}
    eq, ub = result.eqlin.marginals, result.ineqlin.marginals
    dual = {'phase': phase, 'customer': eq.tolist(),
            'vehicle': {v.vehicle_id: float(ub[i]) for i, v in enumerate(problem.vehicles)},
            'berth': ub[f:f + problem.slots].tolist(),
            'other': float(ub[-1]) if profile.other_limit is not None else 0.0}
    dual_objective = float(sum(eq) + ub @ rhs)
    rc = [reduced_cost(problem, c, dual, profile) for c in columns]
    if ((rc and min(rc) < -1e-7) or abs(result.fun - dual_objective) > 1e-7
            or not np.allclose(rc, result.lower.marginals[:j], atol=1e-7)):
        raise RuntimeError('DAY_LP_DUAL_INCONSISTENCY')
    return {'success': True, 'phase': phase, 'objective': float(result.fun),
            'dual': dual, 'dual_objective': dual_objective,
            'weights': result.x[:j].tolist(), 'artificial_sum': float(sum(result.x[j:])),
            'pool_reduced_costs': rc,
            'solver_lower_marginals': result.lower.marginals[:j].tolist()}


def solve_integer(problem, columns, profile):
    if not columns:
        return {'success': False, 'reason': 'NO_FEASIBLE_RESTRICTED_INTEGER'}
    a, b, rhs = matrices(problem, columns, profile)
    result = milp(np.asarray([profile.cost(c) for c in columns]),
                  integrality=np.ones(len(columns)), bounds=Bounds(0, 1),
                  constraints=[LinearConstraint(a, 1, 1), LinearConstraint(b, -np.inf, rhs)],
                  options={'mip_rel_gap': 0.0})
    if not result.success or result.x is None:
        return {'success': False, 'reason': 'NO_FEASIBLE_RESTRICTED_INTEGER' if result.status == 2 else 'MIP_ERROR',
                'message': result.message}
    selected = [c for c, x in zip(columns, result.x) if x > .5]
    return {'success': True, 'objective': float(result.fun), 'selected': selected,
            'scope': 'RESTRICTED_POOL_INTEGER_OPTIMAL', 'mip_gap': float(result.mip_gap)}
