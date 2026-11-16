"""Uniform code/dependency initialization, never loads a delivery instance."""
import time


def preload_dependencies():
    started = time.perf_counter()
    # The same union is initialized for A/B/C/D and quantum-off controls.
    # No circuit, objective evaluation, route, optimizer or input is created.
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    from ortools.sat.python import cp_model
    from scipy.optimize import linprog, milp
    from scipy import sparse
    from verypy.classic_heuristics.parallel_savings import clarke_wright_savings_function
    from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
    from kmd_toc.pipeline.hybrid import EventDayMaster
    from kmd_toc.baseline_a.construction import create_plan
    from kmd_toc.vehicle_day.generation import make_day
    from kmd_toc.vehicle_day.validation import validate_day
    from kmd_toc.column_generation.reduction import contract
    from kmd_toc.common.adapters import to_vehicle_day
    from .methods import generate
    return time.perf_counter() - started
