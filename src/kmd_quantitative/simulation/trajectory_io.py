"""Read the original two-column Controlled-DC input without executing a worker.

The CSV projection is taken verbatim from frozen apply_r0_method_battery.py,
which is also reused by final R1/R0-common energy workers. No resampling,
sorting, endpoint interpolation, or synthetic distance is performed.
"""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

SOURCE_RELATIVE = 'src/kmd_quantitative/simulation/frozen_sources/apply_r0_method_battery.py'
EXPECTED_SHA256 = 'cf048dc63ba8715c499fcdf1e165c846c99c114de976113b4d200cfeeefc0eb6'
_source = Path(__file__).resolve().parents[3] / SOURCE_RELATIVE
_data = _source.read_bytes()
if hashlib.sha256(_data).hexdigest() != EXPECTED_SHA256:
    raise ValueError('Frozen trajectory reader source hash mismatch')
_tree = ast.parse(_data)
_loop = next(n for n in _tree.body if isinstance(n, ast.For)
             and isinstance(n.target, ast.Tuple)
             and [t.id for t in n.target.elts] == ['ix', 'row'])
_nodes = _loop.body[:3]
if [[t.id for t in n.targets] if isinstance(n, ast.Assign) else [] for n in _nodes] != [['df'], ['t'], ['speed']]:
    raise ValueError('Frozen trajectory reader statement contract changed')
_reader = compile(ast.Module(body=_nodes, type_ignores=[]), str(_source), 'exec')


def validate_dc_input(t, speed):
    """API input guard, not an added scientific feasibility/delivery test.

Rejects malformed arrays explicitly before the original DC kernel is called.
Valid inputs are returned unchanged; no values are repaired or substituted.
"""
    if t.ndim != 1 or speed.ndim != 1 or len(t) != len(speed) or len(t) < 2:
        raise ValueError('Need equal one-dimensional arrays with at least two samples')
    try:
        valid = np.isfinite(t).all() and np.isfinite(speed).all() and (speed >= 0).all() and (np.diff(t) == 1).all()
    except (TypeError, ValueError) as exc:
        raise ValueError('Numeric time seconds and speed m/s required') from exc
    if not valid:
        raise ValueError('Require finite samples, nonnegative speed and exact 1 s intervals')
    return t, speed


def read_dc_input(path, *, expected_sha256=None, metadata=None):
    """Return (timestamp_s array, speed_m_s array), in saved row order.

CSV/CSV.gz inferred by pandas exactly as in the frozen reader. Optional hash
binds compressed file bytes, not a newly canonicalized CSV. Optional manifest
checks sample count, interval count and first/last sample when supplied.
This does not certify SUMO completion, time-window fulfillment or full-trip Wh.
"""
    path = Path(path).resolve()
    if expected_sha256 is not None and hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('Trajectory hash mismatch')
    ns = {'pd': pd, 'R': path.parent, 'row': SimpleNamespace(trajectory_path=path.name)}
    exec(_reader, ns)
    t, speed = validate_dc_input(ns['t'], ns['speed'])
    if metadata is not None:
        actual = {'sample_count': len(t), 'integration_interval_count': len(t)-1,
                  'first_sample_s': t[0], 'last_sample_s': t[-1]}
        for key, value in actual.items():
            if key in metadata and float(metadata[key]) != value:
                raise ValueError('Trajectory metadata mismatch: ' + key)
    return t, speed
