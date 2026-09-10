"""Mathematical QUBO-to-Ising conversion for the scoped reduced R22 path."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from traffic_simulation.r20_route_ordering.core import QuboCoefficients, QuboInputError

BINARY_SPIN_CONVENTION = "x=(1-s)/2; s=1-2*x"


class IsingInputError(ValueError):
    """Malformed binary/spin vector or coefficient input."""


@dataclass(frozen=True)
class IsingCoefficients:
    """Canonical full Ising energy: C+sum(h*s)+sum(J*s*s)."""

    constant: float
    linear: dict[int, float]
    quadratic: dict[tuple[int, int], float]
    n_logical: int
    binary_spin_convention: str = BINARY_SPIN_CONVENTION


def _validate_vector(values: Sequence[int], n: int, allowed: set[int], name: str) -> tuple[int, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != n:
        raise IsingInputError(f"{name} must have length {n}")
    if any(type(value) is not int or value not in allowed for value in values):
        raise IsingInputError(f"{name} contains a value outside {sorted(allowed)}")
    return tuple(values)


def binary_to_spin(bits: Sequence[int]) -> tuple[int, ...]:
    bits = _validate_vector(bits, len(bits) if isinstance(bits, Sequence) else 0, {0, 1}, "binary vector")
    return tuple(1 - 2 * value for value in bits)


def spin_to_binary(spins: Sequence[int]) -> tuple[int, ...]:
    spins = _validate_vector(spins, len(spins) if isinstance(spins, Sequence) else 0, {-1, 1}, "spin vector")
    return tuple((1 - value) // 2 for value in spins)


def convert_qubo_to_ising(qubo: QuboCoefficients) -> IsingCoefficients:
    """Apply the documented substitution without external solver libraries."""
    if not isinstance(qubo, QuboCoefficients) or qubo.n_logical < 0:
        raise IsingInputError("qubo must be QuboCoefficients")
    incident = {index: 0.0 for index in range(qubo.n_logical)}
    for (left, right), value in qubo.quadratic.items():
        if left >= right or left < 0 or right >= qubo.n_logical:
            raise IsingInputError("QUBO quadratic keys must be canonical and in range")
        incident[left] += value
        incident[right] += value
    constant = qubo.constant + 0.5 * sum(qubo.linear.values()) + 0.25 * sum(qubo.quadratic.values())
    linear = {index: -0.5 * qubo.linear[index] - 0.25 * incident[index] for index in range(qubo.n_logical)}
    quadratic = {(left, right): value / 4.0 for (left, right), value in sorted(qubo.quadratic.items())}
    return IsingCoefficients(constant, linear, quadratic, qubo.n_logical)


def evaluate_ising(spins: Sequence[int], coefficients: IsingCoefficients, *, include_offset: bool = True) -> float:
    spins = _validate_vector(spins, coefficients.n_logical, {-1, 1}, "spin vector")
    energy = coefficients.constant if include_offset else 0.0
    energy += sum(coefficients.linear[index] * spins[index] for index in coefficients.linear)
    energy += sum(value * spins[left] * spins[right] for (left, right), value in coefficients.quadratic.items())
    if not math.isfinite(energy):
        raise IsingInputError("Ising energy is not finite")
    return energy
