"""Exact I_dual ranking. No solver, RNG, epsilon, or local-acceptance mutation."""
from dataclasses import dataclass
from fractions import Fraction
import math


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError('FINITE_NONNEGATIVE_NUMBER_REQUIRED')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('FINITE_NONNEGATIVE_NUMBER_REQUIRED')
    result = value if isinstance(value, Fraction) else Fraction(str(value))
    if result < 0:
        raise ValueError('FINITE_NONNEGATIVE_NUMBER_REQUIRED')
    return result


@dataclass(frozen=True)
class Metrics:
    D: Fraction
    W: Fraction

    def __post_init__(self):
        object.__setattr__(self, 'D', number(self.D))
        object.__setattr__(self, 'W', number(self.W))


@dataclass(frozen=True)
class Candidate:
    branch_id: int | None  # None is the saved initial plan, never C implicitly.
    metrics: Metrics

    def __post_init__(self):
        if self.branch_id is not None and (type(self.branch_id) is not int or self.branch_id not in range(4)):
            raise ValueError('FIXED_BRANCH_ID_0_TO_3_REQUIRED')


def score(metrics, reference):
    if reference.D == 0 or reference.W == 0:
        return None, None
    d = (reference.D - metrics.D) / reference.D
    w = (reference.W - metrics.W) / reference.W
    return 100 * min(d, w), d + w


def mode(reference):
    if reference.D == reference.W == 0:
        return 'ZERO_BOTH_MIN_D_W'
    if reference.W == 0:
        return 'ZERO_W_C_MIN_W_D'
    if reference.D == 0:
        return 'ZERO_D_C_MIN_D_W'
    return 'MAX_I_DUAL'


def rank_key(candidate, reference):
    m = candidate.metrics
    tail = (candidate.branch_id is not None, candidate.branch_id if candidate.branch_id is not None else -1)
    if reference.D == 0:
        return (m.D, m.W, *tail)
    if reference.W == 0:
        return (m.W, m.D, *tail)
    dual, total = score(m, reference)
    return (-dual, -total, m.D, m.W, *tail)


def select(candidates, reference):
    candidates = tuple(candidates)
    ids = [c.branch_id for c in candidates]
    if ids.count(None) != 1 or len(ids) != len(set(ids)):
        raise ValueError('ONE_INITIAL_AND_UNIQUE_BRANCH_IDS_REQUIRED')
    ordered = sorted(candidates, key=lambda c: rank_key(c, reference))
    if len(ordered) == 1:
        reason = 'ONLY_FEASIBLE_INITIAL'
    else:
        a, b = (rank_key(c, reference) for c in ordered[:2])
        fields = (['I_DUAL_MAX', 'RELATIVE_SUM_MAX', 'D_MIN', 'W_MIN', 'INITIAL_PREFERENCE', 'BRANCH_ID_ASC']
                  if mode(reference) == 'MAX_I_DUAL' else
                  (['W_MIN', 'D_MIN', 'INITIAL_PREFERENCE', 'BRANCH_ID_ASC'] if reference.D > 0 else
                   ['D_MIN', 'W_MIN', 'INITIAL_PREFERENCE', 'BRANCH_ID_ASC']))
        reason = next(fields[i] for i, (x, y) in enumerate(zip(a, b)) if x != y)
    return ordered[0], {'mode': mode(reference), 'reason': reason,
                        'ranked_branch_ids': [c.branch_id for c in ordered]}


def metric_record(metrics, reference):
    dual, total = score(metrics, reference)
    return {'D_km': float(metrics.D), 'W_total_loading_min': float(metrics.W),
            'D_exact': str(metrics.D), 'W_exact': str(metrics.W),
            'I_dual': float(dual) if dual is not None else None,
            'I_dual_exact': str(dual) if dual is not None else None,
            'I_dual_status': 'defined' if dual is not None else 'undefined',
            'relative_sum': float(total) if total is not None else None,
            'relative_sum_exact': str(total) if total is not None else None}
