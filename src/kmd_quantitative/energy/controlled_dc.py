"""Public aliases to unchanged Controlled-DC functions. No physical reimplementation.

Importing the frozen module loads definitions only: its main/preflight are not
called. Inputs, outputs, assertion behavior, and tolerances are exactly those of
that kernel. Use Simulation's reader for CSV validation. Do not use python -O.
"""
from pathlib import Path
import hashlib
import importlib.util
SOURCE_RELATIVE = '05_src/literature_analysis/run_full_controlled_dc.py'
EXPECTED_SHA256 = '4ece8782fc6c4a5fd2731ea310d2042973d2f0f996f016c148ca29c6b935e39b'
_source = Path(__file__).resolve().parents[3] / SOURCE_RELATIVE
if hashlib.sha256(_source.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise ValueError('Controlled-DC scientific source hash mismatch')
_spec = importlib.util.spec_from_file_location('_kmd_frozen_controlled_dc', _source)
_kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_kernel)
evaluate = _kernel.evaluate
scalar_check = _kernel.scalar_check
near = _kernel.near
BOUNDARY = _kernel.BOUNDARY
__all__ = ['evaluate', 'scalar_check', 'near', 'BOUNDARY']
