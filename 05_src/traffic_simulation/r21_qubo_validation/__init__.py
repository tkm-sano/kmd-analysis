"""Preparation-only validation infrastructure for scoped R21.

This package validates the initial reduced route-ordering QUBO.  It contains
no QAOA or Ising execution code.
"""

from .artifact import semantic_artifact, write_validation_artifact
from .runner import R21ValidationError, validate_reduced_r21
from .schema import (
    R21_SCHEMA_VERSION,
    ReducedR21Input,
    coefficient_hash,
    load_input,
)

__all__ = [
    "R21_SCHEMA_VERSION",
    "ReducedR21Input",
    "R21ValidationError",
    "coefficient_hash",
    "load_input",
    "semantic_artifact",
    "validate_reduced_r21",
    "write_validation_artifact",
]
