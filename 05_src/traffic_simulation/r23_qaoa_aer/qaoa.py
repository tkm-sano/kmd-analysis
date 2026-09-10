"""Single-configuration exact-expectation QAOA runner for reduced R23."""

from __future__ import annotations

import math
import time
from typing import Any

from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_algorithms.optimizers import COBYLA
from qiskit.quantum_info import Statevector

from .hamiltonian import build_cost_operator, build_qaoa_circuit, repository_parameters
from .metrics import energy_statistics, probability_metrics
from .schema import R23Config, R23Input, R23SchemaError, memory_preflight


class R23ResourceGuard(RuntimeError):
    reason_code = "RESOURCE_GUARD_STOP"


def transpiler_metadata(*, optimization_level: int, seed_transpiler: int) -> dict[str, Any]:
    """Serialize explicit and backend-default transpiler settings."""
    return {
        "optimization_level": optimization_level,
        "optimization_level_source": "R23Config",
        "seed_transpiler": seed_transpiler,
        "basis_gates": "backend default",
        "backend_dependent_settings": "backend defaults",
        "implementation_default_used": True,
    }


def classify_optimizer_termination(*, optimizer_success: bool | None, nfev: int | None, nit: int | None,
                                   configured_maxiter: int, configured_objective_cap: int,
                                   exception: bool = False) -> dict[str, Any]:
    """Classify API facts; maxiter uses nit and objective cap uses nfev."""
    nfev_value = None if nfev is None else int(nfev)
    nit_value = None if nit is None else int(nit)
    maxiter_boundary = nit_value is not None and nit_value >= configured_maxiter
    objective_cap_hit = nfev_value is not None and nfev_value >= configured_objective_cap
    budget_hit = maxiter_boundary or objective_cap_hit
    if exception:
        status = "OPTIMIZER_FAILURE"
    elif optimizer_success is True:
        status = "CONVERGED"
    elif optimizer_success is False:
        status = "OPTIMIZER_FAILURE"
    elif budget_hit:
        status = "BUDGET_BOUNDARY_REACHED_TERMINATION_UNKNOWN"
    else:
        status = "TERMINATION_UNKNOWN"
    return {"termination_status": status, "budget_hit": budget_hit,
            "maxiter_boundary_reached": maxiter_boundary,
            "objective_cap_hit": objective_cap_hit}


def _statevector_and_expectation(input_data: R23Input, gamma, beta, *, seed: int, optimization_level: int) -> tuple[float, dict[str, float], dict[str, float], dict[str, float]]:
    started = time.perf_counter()
    circuit_started = time.perf_counter()
    circuit = build_qaoa_circuit(input_data, len(gamma), gamma, beta)
    circuit_seconds = time.perf_counter() - circuit_started
    simulator = AerSimulator(method="statevector", device="CPU")
    transpile_started = time.perf_counter()
    transpiled = transpile(circuit, simulator, optimization_level=optimization_level, seed_transpiler=seed)
    transpile_seconds = time.perf_counter() - transpile_started
    transpiled.save_statevector()
    execution_started = time.perf_counter()
    result = simulator.run(transpiled, seed_simulator=seed).result()
    execution_seconds = time.perf_counter() - execution_started
    expectation_started = time.perf_counter()
    state = Statevector(result.data(0)["statevector"])
    operator = build_cost_operator(input_data, include_constant=False)
    expectation = float(state.expectation_value(operator).real + input_data.ising_constant)
    expectation_seconds = time.perf_counter() - expectation_started
    probabilities = {str(label): float(value) for label, value in state.probabilities_dict().items()}
    return expectation, probabilities, {"untranspiled_depth": circuit.depth(), "transpiled_depth": transpiled.depth(), "gate_count": sum(transpiled.count_ops().values()), "two_qubit_gate_count": sum(v for k, v in transpiled.count_ops().items() if k in {"cx", "ecr", "cz"}), "parameter_count": 2 * len(gamma), "logical_qubits": input_data.n_logical, "transpiler": transpiler_metadata(optimization_level=optimization_level, seed_transpiler=seed)}, {"circuit_construction_seconds": circuit_seconds, "transpilation_seconds": transpile_seconds, "aer_execution_seconds": execution_seconds, "expectation_seconds": expectation_seconds, "evaluation_total_seconds": time.perf_counter() - started}


def run_single(input_data: R23Input, config: R23Config) -> dict[str, Any]:
    config.validate(input_data.n_logical)
    resource_preflight = memory_preflight(input_data.n_logical, config.memory_limit_gib)
    started = time.perf_counter(); trace = []; objective_eval_total = 0.0
    component_totals = {"circuit_build": 0.0, "transpile": 0.0, "aer": 0.0, "expectation": 0.0, "objective_eval": 0.0}
    initial = tuple([config.initial_parameter] * (2 * config.p))
    best = {"value": math.inf, "parameters": None}

    def objective(values):
        nonlocal objective_eval_total
        elapsed = time.perf_counter() - started
        if len(trace) >= config.max_evaluations or elapsed > config.wall_time_seconds:
            raise R23ResourceGuard("objective evaluation resource guard reached")
        t = time.perf_counter()
        gamma, beta = repository_parameters(values, config.p)
        value, _, _, evaluation_timing = _statevector_and_expectation(input_data, gamma, beta, seed=config.seed, optimization_level=config.optimization_level)
        duration = time.perf_counter() - t; objective_eval_total += duration
        component_totals["objective_eval"] += duration
        component_totals["circuit_build"] += evaluation_timing["circuit_construction_seconds"]
        component_totals["transpile"] += evaluation_timing["transpilation_seconds"]
        component_totals["aer"] += evaluation_timing["aer_execution_seconds"]
        component_totals["expectation"] += evaluation_timing["expectation_seconds"]
        record = {"evaluation": len(trace) + 1, "parameters": [float(v) for v in values], "expectation": value, "elapsed_seconds": duration, "timing": evaluation_timing, "cumulative_elapsed_seconds": time.perf_counter() - started, "cumulative_runtime_seconds": dict(component_totals)}
        trace.append(record)
        if value < best["value"]:
            best.update(value=value, parameters=record["parameters"])
        return value

    status, failure_reasons = "PASS", []
    optimizer_started = time.perf_counter()
    optimizer_wall_seconds = 0.0
    optimizer_success = None
    optimizer_nit = None
    optimizer_nfev = None
    termination_status = "TERMINATION_UNKNOWN"
    budget_flags = {"budget_hit": False, "maxiter_boundary_reached": False, "objective_cap_hit": False}
    try:
        optimizer = COBYLA(maxiter=config.maxiter, options={"maxiter": config.maxiter})
        result = optimizer.minimize(fun=objective, x0=list(initial))
        final_parameters = [float(v) for v in result.x]
        optimizer_wall_seconds = time.perf_counter() - optimizer_started
        optimizer_success = getattr(result, "success", None)
        optimizer_nit = getattr(result, "nit", None)
        optimizer_nfev = int(getattr(result, "nfev", len(trace)))
        budget_flags = classify_optimizer_termination(optimizer_success=optimizer_success, nfev=optimizer_nfev, nit=optimizer_nit, configured_maxiter=config.maxiter, configured_objective_cap=config.max_evaluations)
        termination_status = budget_flags["termination_status"]
        termination = {"nfev": optimizer_nfev, "nit": optimizer_nit, "success": optimizer_success, "message": str(getattr(result, "message", "")), **budget_flags}
    except R23ResourceGuard as exc:
        optimizer_wall_seconds = time.perf_counter() - optimizer_started
        status, failure_reasons, final_parameters = "RESOURCE_GUARD_STOP", [exc.reason_code], list(best["parameters"] or initial)
        budget_flags = classify_optimizer_termination(optimizer_success=None, nfev=len(trace), nit=None, configured_maxiter=config.maxiter, configured_objective_cap=config.max_evaluations)
        termination_status = budget_flags["termination_status"]
        termination = {"nfev": len(trace), "nit": None, "success": None, "message": str(exc), **budget_flags}
    except Exception as exc:  # backend/optimizer errors are serialized, not hidden
        optimizer_wall_seconds = time.perf_counter() - optimizer_started
        status, failure_reasons, final_parameters = "OPTIMIZER_FAILURE", ["OPTIMIZER_FAILURE"], list(best["parameters"] or initial)
        budget_flags = classify_optimizer_termination(optimizer_success=None, nfev=len(trace), nit=None, configured_maxiter=config.maxiter, configured_objective_cap=config.max_evaluations, exception=True)
        termination_status = budget_flags["termination_status"]
        termination = {"nfev": len(trace), "nit": None, "success": None, "message": repr(exc), **budget_flags}
    else:
        optimizer_wall_seconds = time.perf_counter() - optimizer_started
    gamma, beta = repository_parameters(final_parameters, config.p)
    try:
        final_expectation, probabilities, circuit_metrics, final_timing = _statevector_and_expectation(input_data, gamma, beta, seed=config.seed, optimization_level=config.optimization_level)
        decode_started = time.perf_counter()
        metrics = probability_metrics(probabilities, input_data, threshold=config.probability_threshold)
        energy_stats = energy_statistics(probabilities, input_data)
        decode_seconds = time.perf_counter() - decode_started
        p_opt = metrics["P_opt"]
        if status == "PASS":
            status = "OPTIMAL_FOUND" if p_opt >= config.probability_threshold else ("FEASIBLE_SUBOPTIMAL" if metrics["P_feasible_exact"] >= config.probability_threshold else "NO_FEASIBLE_SOLUTION")
    except Exception as exc:
        status, failure_reasons = "BACKEND_FAILURE", ["BACKEND_FAILURE"]
        final_expectation, probabilities, metrics, circuit_metrics, final_timing, energy_stats = None, {}, {}, {}, {}, {}
        decode_seconds = 0.0
        termination["message"] = f"{termination.get('message','')}; final evaluation: {exc!r}"
    exact_energy = float(input_data.payload.get("ising_global_minimum_energy", 0.0))
    total_wall_seconds = time.perf_counter() - started
    termination_message = str(termination.get("message", ""))
    objective_evaluation_count = len(trace)
    expectation_evaluation_count = objective_evaluation_count + (1 if final_expectation is not None else 0)
    return {"schema_version": "r23-reduced-qaoa-aer-result-v2", "run_classification": status, "instance_id": input_data.instance_id, "n": input_data.n, "logical_qubits": input_data.n_logical, "p": config.p, "optimizer": config.optimizer, "maxiter": config.maxiter, "max_evaluations": config.max_evaluations, "configured_maxiter": config.maxiter, "configured_objective_cap": config.max_evaluations, "initial_parameters": list(initial), "final_parameters": final_parameters, "objective_trace": trace, "initial_expectation": trace[0]["expectation"] if trace else None, "optimized_expectation": final_expectation, "exact_ground_state_full_energy": exact_energy, "expectation_energy_gap": None if final_expectation is None else final_expectation - exact_energy, "probability_metrics": metrics, "energy_variance": energy_stats.get("variance"), "termination": termination, "termination_status": termination_status, "termination_message": termination_message, "optimizer_success": optimizer_success, "nit": optimizer_nit, "nfev": optimizer_nfev if optimizer_nfev is not None else len(trace), "budget_hit": budget_flags["budget_hit"], "objective_evaluation_count": objective_evaluation_count, "expectation_evaluation_count": expectation_evaluation_count, "optimizer_evaluations": objective_evaluation_count, "optimizer_evaluator_seconds_inclusive": objective_eval_total, "circuit_metrics": circuit_metrics, "resource_preflight": resource_preflight, "timing": {"T_total": total_wall_seconds, "T_optimizer_total": optimizer_wall_seconds, "T_objective_eval_total": component_totals["objective_eval"], "T_circuit_build_total": component_totals["circuit_build"], "T_transpile_total": component_totals["transpile"], "T_Aer_total": component_totals["aer"], "T_expectation_total": component_totals["expectation"], "T_decode_total": decode_seconds, "T_final_evaluation": final_timing, "total_wall_seconds": total_wall_seconds, "expectation_evaluator_seconds_accumulated": component_totals["objective_eval"], "final_evaluation": final_timing, "inclusion_relationships": {"T_optimizer_total": "inclusive of optimizer overhead and all objective evaluations", "T_objective_eval_total": "inclusive of circuit build, transpilation, Aer, and expectation processing for objective evaluations", "T_circuit_build_total": "exclusive component within objective evaluations", "T_transpile_total": "exclusive component within objective evaluations", "T_Aer_total": "exclusive component within objective evaluations", "T_expectation_total": "exclusive component within objective evaluations", "T_decode_total": "post-final-evaluation decode/metric processing", "T_final_evaluation": "separate post-optimizer evaluation; do not add to T_optimizer_total", "T_total": "wall-clock envelope; do not sum component metrics as an alternative"}}, "backend": {"class": "AerSimulator", "method": config.backend_method, "device": config.device, "seed_simulator": config.seed, "seed_transpiler": config.seed, "optimization_level": config.optimization_level, "optimization_level_source": "R23Config", "basis_gates": "backend default", "backend_dependent_settings": "backend defaults", "implementation_default_used": True}, "r22_ising_coefficient_hash": input_data.ising_coefficient_hash, "r22_qubo_coefficient_hash": input_data.qubo_coefficient_hash, "lambda": input_data.lambda_value, "B": input_data.bound, "probabilities": probabilities, "failure_reasons": failure_reasons, "software_simulation_resource_guard": True, "formal_baseline": False}
