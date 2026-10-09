"""Mass API over the original documented stage arithmetic, without report writes.

The frozen research scenario is not a measured battery or a quantum-material
calculation. Custom specific energy is a sensitivity input, not a new authority.
"""
from pathlib import Path
import ast
import hashlib
import math
SOURCE_RELATIVE = 'src/kmd_quantitative/battery/frozen_sources/review_pack_specific_energy.py'
EXPECTED_SHA256 = 'b8fb03a45ebc738c4b9a1e1cc283449bbb63e48f4bac416d30d111ec56f9bca8'
_source = Path(__file__).resolve().parents[3] / SOURCE_RELATIVE
_data = _source.read_bytes()
if hashlib.sha256(_data).hexdigest() != EXPECTED_SHA256:
    raise ValueError('Mass scientific source hash mismatch')
_tree = ast.parse(_data)
_calc = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == 'calc')
_main = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
_loop = next(n for n in _main.body if isinstance(n, ast.For) and any(
    isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)
    and x.value.id == 'masses' and x.attr == 'append' for x in ast.walk(n)))
_custom = [n for n in _loop.body if
    (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'m', 'm0'} for t in n.targets)) or
    (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
     and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'masses')]
if len(_custom) != 3:
    raise ValueError('Mass source statement contract changed')

def official_mass_stages():
    """Original B0/B1/B2 mass records (kg, Wh/kg, fixed 20 kWh)."""
    ns = {'math': math, 'stages': [], 'masses': []}
    exec(compile(ast.Module(body=[_calc, _loop], type_ignores=[]), str(_source), 'exec'), ns)
    return ns['masses']

def mass_at_specific_energy(selected):
    """Original fixed-capacity arithmetic at a custom Wh/kg; not a frozen stage."""
    if not isinstance(selected, (int, float)) or not math.isfinite(selected) or selected <= 0:
        raise ValueError('specific energy must be finite and positive')
    ns = {'selected': selected, 'k': 'CUSTOM', 'masses': []}
    exec(compile(ast.Module(body=_custom, type_ignores=[]), str(_source), 'exec'), ns)
    return ns['masses'][0]
