"""Deterministic Experiment B initialization generation."""

from __future__ import annotations

import hashlib
import math
from typing import Sequence

import numpy as np


RANDOM_INITIALIZATION_SEEDS = (11, 23, 37, 53, 71)


def generate_initial_parameters(p: int, initialization_id: str = "fixed_0.1", seed: int | None = None) -> tuple[float, ...]:
    """Return the frozen R23 Experiment B vector in repository order.

    The domains apply only to initial-vector generation.  Optimization remains
    unconstrained, as required by the frozen design.
    """
    if p not in (1, 2, 3):
        raise ValueError("R23 initialization generation supports p in {1,2,3}")
    if initialization_id == "fixed_0.1":
        return tuple([0.1] * (2 * p))
    if not initialization_id.startswith("random_seed_"):
        raise ValueError(f"unsupported initialization: {initialization_id}")
    declared_seed = int(initialization_id.removeprefix("random_seed_"))
    if seed is not None and int(seed) != declared_seed:
        raise ValueError("initialization id and seed disagree")
    rng = np.random.Generator(np.random.PCG64(declared_seed))
    gamma = rng.uniform(-math.pi, math.pi, size=p)
    beta = rng.uniform(-math.pi / 2.0, math.pi / 2.0, size=p)
    return tuple(float(x) for x in (*gamma, *beta))


def initialization_vector_sha256(parameters: Sequence[float]) -> str:
    payload = ",".join(format(float(value), ".17g") for value in parameters).encode()
    return hashlib.sha256(payload).hexdigest()
