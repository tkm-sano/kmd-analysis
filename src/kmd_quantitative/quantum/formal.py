"""Read-only adapters to hash-pinned Protocol V2 statements, without running workers.

Input contracts are those of V2: a complete qualification metadata table,
independently valid input arrays, Qiskit count keys, and positive sampler counts.
This module does not execute a circuit, optimize parameters, or write results.
Qualification decoding is a separate API in decoder.py.
"""
import ast
import hashlib
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
from . import builder
from ..routing import independent

_SOURCE = Path(__file__).resolve().parents[3] / builder.SCIENTIFIC_SOURCE_RELATIVE
_data = _SOURCE.read_bytes()
if hashlib.sha256(_data).hexdigest() != builder.EXPECTED_SOURCE_SHA256:
    raise ValueError('Formal Protocol V2 source hash mismatch')
_tree = ast.parse(_data)
_child = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == 'execute_child')


def _assignment(nodes, name):
    matches = [i for i, n in enumerate(nodes) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise ValueError('Frozen statement boundary changed: ' + name)
    return matches[0]


# Original statements only: no mathematical expression or selection rule copied.
_i = _assignment(_child.body, 'feasible_routes')
_j = _assignment(_child.body, 'exact_optimum')
_FEASIBLE = _child.body[_i:_j + 1]
_i = _assignment(_child.body, 'routes')
_j = _assignment(_child.body, 'best')
_FINAL = _child.body[_i:_j + 1]
_sample = next(n for n in _child.body if isinstance(n, ast.FunctionDef) and n.name == 'sample')
_i = _assignment(_sample.body, 'counts')
_COUNTS = _sample.body[_i:_i + 2]  # original conversion and SHOT_COUNT_MISMATCH guard
assert isinstance(_COUNTS[1], ast.If)
_RETURN = next(n for n in _sample.body if isinstance(n, ast.Return)).value
# Reuse original sample's feasible_count expression, without energy array/sampler.
_FEASIBLE_COUNT = _RETURN.values[next(i for i, k in enumerate(_RETURN.keys) if k.value == 'feasible_count')]
_BEST = _FINAL[-1].value
_ERRORS = [n for n in _tree.body if isinstance(n, ast.ClassDef)
           and n.name in {'ValidationFailure', 'ProtocolFailure'}]
_error_namespace = {'__name__': __name__}
exec(compile(ast.Module(body=_ERRORS, type_ignores=[]), str(_SOURCE), 'exec'), _error_namespace)
ValidationFailure = _error_namespace['ValidationFailure']
ProtocolFailure = _error_namespace['ProtocolFailure']


def _run(nodes, values):
    namespace = {'D': D, 'route_code': builder.route_code, 'ind': independent,
                 'ValidationFailure': ValidationFailure, 'ProtocolFailure': ProtocolFailure, **values}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(_SOURCE), 'exec'), namespace)
    return namespace


def feasible_route_table(model, a):
    """Return original code->route table and retrospective optimum (seconds).

As in V2, raises AssertionError if no feasible route exists at all. This differs
from a feasible problem with zero acquired feasible samples, which returns None.
"""
    ns = _run(_FEASIBLE, {'model': model, 'a': a})
    return ns['feasible_routes'], ns['exact_optimum']


def parse_sample_counts(raw_counts, shots):
    """Original Qiskit binary-string conversion and total-shot guard.

Not a general hostile-input validator: width/nonnegative checks are not added.
Nonbinary keys raise ValueError; a total mismatch raises ProtocolFailure.
"""
    sampled = SimpleNamespace(data=SimpleNamespace(meas=SimpleNamespace(get_counts=lambda: raw_counts)))
    return _run(_COUNTS, {'sampled': sampled, 'shots': shots})['counts']


def select_final_route(routes):
    """Original best expression; expects already independently validated records."""
    return eval(compile(ast.Expression(_BEST), str(_SOURCE), 'eval'), {'D': D, 'routes': routes})


def evaluate_final_counts(model, a, counts):
    """Decode integer codes, revalidate routes and select by the frozen rule.

Counts must already satisfy the sampler contract (use parse_sample_counts).
Unlisted codes are ignored, exactly as in V2. No optimizer/probe samples may be
merged into this final sample set. Return keys mirror the scientific record.
"""
    table, optimum = feasible_route_table(model, a)
    feasible_count = eval(compile(ast.Expression(_FEASIBLE_COUNT), str(_SOURCE), 'eval'),
                          {'counts': counts, 'feasible_routes': table})
    ns = _run(_FINAL, {'a': a, 'q': int(model['n']) ** 2, 'feasible_routes': table,
                      'exact_optimum': optimum, 'final': {'counts': counts, 'feasible_count': feasible_count}})
    return {'final_feasible_count': feasible_count, 'sampled_feasible_routes': ns['routes'],
            'best_final_feasible_route': ns['best']}


__all__ = ['feasible_route_table', 'parse_sample_counts', 'select_final_route',
           'evaluate_final_counts', 'ValidationFailure', 'ProtocolFailure']
