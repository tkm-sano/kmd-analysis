from __future__ import annotations

import math

import pytest
from qiskit_algorithms.optimizers import COBYLA

from traffic_simulation.r23_qaoa_aer.initialization import generate_initial_parameters
from traffic_simulation.r23_qaoa_aer.optimizers import ObjectiveEvaluationCapReached, minimize_objective, optimizer_method
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, R23Input, R23SchemaError


def synthetic_b_input() -> R23Input:
    return R23Input(
        "synthetic_b_n2",
        2,
        (1, 2),
        0,
        3.0,
        {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
        {},
        "i" * 64,
        "q" * 64,
        2.0,
        1.0,
        frozenset({(1, 0, 0, 1)}),
        frozenset({(-1, 1, 1, -1)}),
        frozenset({(1, 2)}),
        {0: {0: 0.0, 1: 1.0, 2: 1.0}, 1: {0: 1.0, 1: 0.0, 2: 1.0}, 2: {0: 1.0, 1: 1.0, 2: 0.0}},
        {"ising_global_minimum_energy": 0.0},
    )


def test_optimizer_selection_and_rejection():
    assert optimizer_method("COBYLA") == "COBYLA"
    assert optimizer_method("NELDER_MEAD") == "Nelder-Mead"
    with pytest.raises(ValueError):
        optimizer_method("SPSA")
    data = synthetic_b_input()
    R23Config(optimizer="COBYLA").validate(data.n_logical)
    R23Config(optimizer="NELDER_MEAD").validate(data.n_logical)
    with pytest.raises(R23SchemaError):
        R23Config(optimizer="SPSA").validate(data.n_logical)


def test_cobyla_adapter_matches_qiskit_wrapper_on_deterministic_objective():
    def objective(values):
        return float((values[0] - 0.3) ** 2 + (values[1] + 0.2) ** 2)

    native = COBYLA(maxiter=20, options={"maxiter": 20}).minimize(objective, [0.1, 0.1])
    adapted = minimize_objective(optimizer_name="COBYLA", fun=objective, x0=[0.1, 0.1], maxiter=20, objective_cap=900)
    assert adapted.final_parameters == pytest.approx(list(native.x), abs=1e-14)
    assert adapted.final_objective == pytest.approx(float(native.fun), abs=1e-14)
    assert adapted.nfev == int(native.nfev)


def test_nelder_mead_smoke_has_normalized_native_metadata():
    result = minimize_objective(optimizer_name="NELDER_MEAD", fun=lambda x: float(sum(v * v for v in x)), x0=[0.1, -0.1], maxiter=5, objective_cap=50)
    assert result.optimizer_name == "NELDER_MEAD"
    assert result.optimizer_method == "Nelder-Mead"
    assert result.nfev is not None and result.nfev > 0
    assert result.optimizer_status is not None
    assert result.optimizer_message is not None
    assert math.isfinite(result.final_objective)


def test_objective_cap_is_enforced_before_an_extra_call():
    calls = []

    def objective(values):
        calls.append(tuple(values))
        return 1.0

    with pytest.raises(ObjectiveEvaluationCapReached):
        minimize_objective(optimizer_name="COBYLA", fun=objective, x0=[0.1], maxiter=100, objective_cap=2)
    assert len(calls) == 2


def test_initialization_is_deterministic_and_in_domain():
    for p in (2, 3):
        for seed in (11, 23, 37, 53, 71):
            first = generate_initial_parameters(p, f"random_seed_{seed}")
            second = generate_initial_parameters(p, f"random_seed_{seed}")
            assert first == second
            assert len(first) == 2 * p
            assert all(-math.pi <= value < math.pi for value in first[:p])
            assert all(-math.pi / 2 <= value < math.pi / 2 for value in first[p:])
    assert generate_initial_parameters(2, "fixed_0.1") == (0.1, 0.1, 0.1, 0.1)


def test_run_single_supports_both_optimizers_and_preserves_final_eval_boundary():
    data = synthetic_b_input()
    for optimizer in ("COBYLA", "NELDER_MEAD"):
        result = run_single(data, R23Config(p=1, optimizer=optimizer, maxiter=5, max_evaluations=20))
        assert result["optimizer"] == optimizer
        assert result["objective_evaluation_count"] == len(result["objective_trace"])
        assert result["expectation_evaluation_count"] == result["objective_evaluation_count"] + 1
        assert result["termination_status"] in {"OPTIMIZER_REPORTED_SUCCESS", "OPTIMIZER_REPORTED_FAILURE", "MAXITER_REACHED", "TERMINATION_UNKNOWN"}
        assert result["probability_metrics"]["probability_total"] == pytest.approx(1.0, abs=1e-12)
