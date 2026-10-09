"""Candidate C PUBO API over the unchanged, hash-pinned Protocol V2 source.

Only the four pure function definitions are loaded. No worker, optimizer, circuit,
or mathematical expression is copied here. The scientific body remains at
SCIENTIFIC_SOURCE_RELATIVE; physical migration of that body is deferred.
"""
from pathlib import Path
import ast
import hashlib
from decimal import Decimal as D, getcontext
from itertools import combinations

SCIENTIFIC_SOURCE_RELATIVE = "05_src/traffic_simulation/matched_quantum_protocol_v2_shared/science.py"
EXPECTED_SOURCE_SHA256 = "76fc2f979b30d7938df3ec4fcaff158c108652aee37f3d225a298df5c3bb679d"
__all__ = ["add", "square_onehot", "build_C", "route_code"]
_source = Path(__file__).resolve().parents[3] / SCIENTIFIC_SOURCE_RELATIVE
if hashlib.sha256(_source.read_bytes()).hexdigest() != EXPECTED_SOURCE_SHA256:
    raise ValueError("Candidate C scientific source hash mismatch")
_tree = ast.parse(_source.read_text())
_nodes = [n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name in __all__]
if sorted(n.name for n in _nodes) != sorted(__all__):
    raise ValueError("Candidate C source function contract changed")
getcontext().prec = 80
_namespace = {"D": D, "combinations": combinations, "__name__": __name__}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), str(_source), "exec"), _namespace)
for _name in __all__:
    globals()[_name] = _namespace[_name]
