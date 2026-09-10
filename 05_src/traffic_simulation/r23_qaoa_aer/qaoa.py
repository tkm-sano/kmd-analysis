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
from .schema import R23Config, R23Input, R23SchemaError


class R23ResourceGuard(RuntimeError):
    reason_code = "RESOURCE_GUARD_STOP"


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
    return expectation, probabilities, {"untranspiled_depth": circuit.depth(), "transpiled_depth": transpiled.depth(), "gate_count": sum(transpiled.count_ops().values()), "two_qubit_gate_count": sum(v for k, v in transpiled.count_ops().items() if k in {"cx", "ecr", "cz"}), "parameter_count": 2 * len(gamma), "logical_qubits": input_data.n_logical}, {"circuit_construction_seconds": circuit_seconds, "transpilation_seconds": transpile_seconds, "aer_execution_seconds": execution_seconds, "expectation_seconds": expectation_seconds, "evaluation_total_seconds": time.perf_counter() - started}


def run_single(input_data: R23Input, config: R23Config) -> dict[str, Any]:
    config.validate(input_data.n_logical)
    started = time.perf_counter(); trace = []; call_time = 0.0
    initial = tuple([config.initial_parameter] * (2 * config.p))
    best = {"value": math.inf, "parameters": None}

    def objective(values):
        nonlocal call_time
        elapsed = time.perf_counter() - started
        if len(trace) >= config.max_evaluations or elapsed > config.wall_time_seconds:
            raise R23ResourceGuard("objective evaluation resource guard reached")
        t = time.perf_counter()
        gamma, beta = repository_parameters(values, config.p)
        value, _, _, _ = _statevector_and_expectation(input_data, gamma, beta, seed=config.seed, optimization_level=config.optimization_level)
        duration = time.perf_counter() - t; call_time += duration
        record = {"evaluation": len(trace) + 1, "parameters": [float(v) for v in values], "expectation": value, "elapsed_seconds": duration}
        trace.append(record)
        if value < best["value"]:
            best.update(value=value, parameters=record["parameters"])
        return value

    status, failure_reasons = "PASS", []
    try:
        optimizer = COBYLA(maxiter=config.maxiter, options={"maxiter": config.maxiter})
        result = optimizer.minimize(fun=objective, x0=list(initial))
        final_parameters = [float(v) for v in result.x]
        termination = {"nfev": int(getattr(result, "nfev", len(trace))), "nit": getattr(result, "nit", None), "message": str(getattr(result, "message", ""))}
    except R23ResourceGuard as exc:
        status, failure_reasons, final_parameters = "RESOURCE_GUARD_STOP", [exc.reason_code], list(best["parameters"] or initial)
        termination = {"nfev": len(trace), "nit": None, "message": str(exc)}
    except Exception as exc:  # backend/optimizer errors are serialized, not hidden
        status, failure_reasons, final_parameters = "OPTIMIZER_FAILURE", ["OPTIMIZER_FAILURE"], list(best["parameters"] or initial)
        termination = {"nfev": len(trace), "nit": None, "message": repr(exc)}
    gamma, beta = repository_parameters(final_parameters, config.p)
    try:
        final_expectation, probabilities, circuit_metrics, final_timing = _statevector_and_expectation(input_data, gamma, beta, seed=config.seed, optimization_level=config.optimization_level)
        metrics = probability_metrics(probabilities, input_data, threshold=config.probability_threshold)
        energy_stats = energy_statistics(probabilities, input_data)
        p_opt = metrics["P_opt"]
        if status == "PASS":
            status = "OPTIMAL_FOUND" if p_opt >= config.probability_threshold else ("FEASIBLE_SUBOPTIMAL" if metrics["P_feasible_exact"] >= config.probability_threshold else "NO_FEASIBLE_SOLUTION")
    except Exception as exc:
        status, failure_reasons = "BACKEND_FAILURE", ["BACKEND_FAILURE"]
        final_expectation, probabilities, metrics, circuit_metrics, final_timing, energy_stats = None, {}, {}, {}, {}, {}
        termination["message"] = f"{termination.get('message','')}; final evaluation: {exc!r}"
    exact_energy = float(input_data.payload.get("ising_global_minimum_energy", 0.0))
    return {"schema_version": "r23-reduced-qaoa-aer-result-v1", "run_classification": status, "instance_id": input_data.instance_id, "n": input_data.n, "logical_qubits": input_data.n_logical, "p": config.p, "optimizer": config.optimizer, "maxiter": config.maxiter, "max_evaluations": config.max_evaluations, "initial_parameters": list(initial), "final_parameters": final_parameters, "objective_trace": trace, "initial_expectation": trace[0]["expectation"] if trace else None, "optimized_expectation": final_expectation, "exact_ground_state_full_energy": exact_energy, "expectation_energy_gap": None if final_expectation is None else final_expectation - exact_energy, "probability_metrics": metrics, "energy_variance": energy_stats.get("variance"), "termination": termination, "optimizer_evaluations": len(trace), "optimizer_evaluator_seconds_inclusive": call_time, "circuit_metrics": circuit_metrics, "timing": {"total_wall_seconds": time.perf_counter() - started, "expectation_evaluator_seconds_accumulated": call_time, "final_evaluation": final_timing}, "backend": {"class": "AerSimulator", "method": config.backend_method, "device": config.device, "seed_simulator": config.seed, "seed_transpiler": config.seed, "optimization_level": config.optimization_level}, "r22_ising_coefficient_hash": input_data.ising_coefficient_hash, "r22_qubo_coefficient_hash": input_data.qubo_coefficient_hash, "lambda": input_data.lambda_value, "B": input_data.bound, "probabilities": probabilities, "failure_reasons": failure_reasons, "software_simulation_resource_guard": True, "formal_baseline": False}
