"""Deterministic HiGHS runner for the R24 MILP."""

from __future__ import annotations

import time
from dataclasses import dataclass

import highspy

from .r24_cvrp_model import CVRPInstance, FEASIBILITY_TOLERANCE, build_highs_model
from .r24_solution_decoder import DecodedSolution, decode_solution

HIGHS_OPTIONS = {
    "threads": 1,
    "random_seed": 0,
    "presolve": "on",
    "mip_rel_gap": 0.0,
    "mip_abs_gap": 0.0,
    "primal_feasibility_tolerance": FEASIBILITY_TOLERANCE,
    "dual_feasibility_tolerance": FEASIBILITY_TOLERANCE,
    "mip_feasibility_tolerance": FEASIBILITY_TOLERANCE,
    "time_limit": 60.0,
    "output_flag": False,
    "log_to_console": False,
}


@dataclass(frozen=True)
class HighsResult:
    status: str
    model_status: str
    objective: float | None
    mip_gap: float | None
    build_time_s: float
    solve_time_s: float
    decode_time_s: float
    total_time_s: float
    decoded: DecodedSolution | None


def solve_highs(instance: CVRPInstance) -> HighsResult:
    started = time.perf_counter()
    build_started = time.perf_counter()
    model = build_highs_model(instance)
    build_time = time.perf_counter() - build_started
    for name, value in HIGHS_OPTIONS.items():
        status = model.highs.setOptionValue(name, value)
        if status != highspy.HighsStatus.kOk:
            raise RuntimeError(f"failed to set HiGHS option {name}={value!r}: {status}")
    solve_started = time.perf_counter()
    run_status = model.highs.run()
    solve_time = time.perf_counter() - solve_started
    model_status = model.highs.getModelStatus()
    if run_status != highspy.HighsStatus.kOk:
        return HighsResult("SOLVER_FAILURE", str(model_status), None, None, build_time, solve_time, 0, time.perf_counter() - started, None)
    if model_status == highspy.HighsModelStatus.kInfeasible:
        return HighsResult("PROVEN_INFEASIBLE", model.highs.modelStatusToString(model_status), None, None, build_time, solve_time, 0, time.perf_counter() - started, None)
    if model_status != highspy.HighsModelStatus.kOptimal:
        return HighsResult("TIME_LIMIT_NO_PROOF", model.highs.modelStatusToString(model_status), None, None, build_time, solve_time, 0, time.perf_counter() - started, None)
    solution = model.highs.getSolution()
    info = model.highs.getInfo()
    decode_started = time.perf_counter()
    decoded = decode_solution(instance, model, solution.col_value)
    decode_time = time.perf_counter() - decode_started
    return HighsResult(
        status="OPTIMAL",
        model_status=model.highs.modelStatusToString(model_status),
        objective=float(info.objective_function_value),
        mip_gap=float(info.mip_gap),
        build_time_s=build_time,
        solve_time_s=solve_time,
        decode_time_s=decode_time,
        total_time_s=time.perf_counter() - started,
        decoded=decoded,
    )

