"""Deterministic artificial input only; no study demand/OD file access."""
import numpy as np
from kmd_toc.column_generation.models import Instance
from .model import DayProblem, Vehicle


def small_problem(n=4, berths=2):
    if n not in (4, 5, 6):
        raise ValueError('Only artificial 4/5/6 customer problems')
    position = (0,) + tuple(range(1, n + 1, 2)) + tuple(range(2, n + 1, 2))
    d = np.array([[((b - a) if b >= a else 2 * (a - b)) / 10
                   for b in position] for a in position])
    travel = tuple(tuple(0 if i == j else 120 for j in range(n + 1)) for i in range(n + 1))
    base = Instance(f'day_artificial_{n}_B{berths}', d, (0,) + (1,) * n, 2)
    vehicles = tuple(Vehicle(f'V{i}', 2, 0, 0, 1680, 120, 120) for i in range(2))
    return DayProblem(base, travel, (0,) + (120,) * n, vehicles, berths, 120)
