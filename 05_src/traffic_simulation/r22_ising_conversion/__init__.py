"""Preparation infrastructure for scoped R22 QUBO-to-Ising conversion.

This package performs no QAOA execution and no formal R22 run by import.
"""

from .artifact import semantic_artifact, write_conversion_artifact
from .converter import (
    BINARY_SPIN_CONVENTION,
    IsingCoefficients,
    binary_to_spin,
    convert_qubo_to_ising,
    evaluate_ising,
    spin_to_binary,
)
from .schema import R22_SCHEMA_VERSION, R22Input, R22SchemaError, ising_coefficient_hash, load_input, load_r21_instance
from .validator import R22ValidationError, validate_conversion

__all__ = [
    "BINARY_SPIN_CONVENTION",
    "IsingCoefficients",
    "R22_SCHEMA_VERSION",
    "R22Input",
    "R22SchemaError",
    "R22ValidationError",
    "binary_to_spin",
    "convert_qubo_to_ising",
    "evaluate_ising",
    "load_input",
    "load_r21_instance",
    "ising_coefficient_hash",
    "semantic_artifact",
    "spin_to_binary",
    "validate_conversion",
    "write_conversion_artifact",
]
