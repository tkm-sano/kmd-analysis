"""Finite observed-front evaluation; no synthetic replacement of missing values."""
import math
from decimal import Decimal, ROUND_HALF_EVEN

KEYS = ('D_km', 'W_min', 'T_program_s')
QUANTA = ('0.0000001', '0.0000001', '0.000001')


def coordinates(row):
    values = [row.get(k) for k in KEYS]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('MISSING_NONFINITE_OR_NEGATIVE_OBJECTIVE')
    return tuple(Decimal(str(v)).quantize(Decimal(q), rounding=ROUND_HALF_EVEN)
                 for v, q in zip(values, QUANTA))


def dominates(p, q):
    """Transitive strict dominance on a predeclared decimal grid, ties retained."""
    a, b = coordinates(p), coordinates(q)
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def eligible(row):
    try:
        coordinates(row)
    except ValueError:
        return False
    return (row.get('status') == 'COMPLETE' and row.get('feasible') is True
            and row.get('budget_met') is True and row.get('epsilon_met') is True
            and row.get('standard_output_complete') is True
            and row.get('T_kind') == 'program_wall')


def score(row, reference, weights):
    if (len(weights) != 3 or any(type(w) not in (int, float) or not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1, abs_tol=1e-12)):
        raise ValueError('WEIGHT_SUM_OR_RANGE')
    if any(type(reference.get(k)) not in (int, float) or not math.isfinite(reference[k]) or reference[k] <= 0 for k in KEYS):
        raise ValueError('POSITIVE_COMMON_REFERENCE_REQUIRED')
    if not eligible(row) or row.get('method') == 'A':
        return None
    return math.fsum(w * row[k] / reference[k] for w, k in zip(weights, KEYS))


def pareto(rows):
    candidates = [r for r in rows if eligible(r) and r['method'] in ('B', 'C', 'D')]
    front, relations = [], []
    for q in candidates:
        parents = [p for p in candidates if p['trial_id'] != q['trial_id']
                   and p['input_hash'] == q['input_hash'] and dominates(p, q)]
        if not parents:
            front.append(q)
        relations.extend({'dominator': p['trial_id'], 'dominated': q['trial_id'],
                          'dominator_method': p['method'], 'dominated_method': q['method']}
                         for p in parents)
    return front, relations
