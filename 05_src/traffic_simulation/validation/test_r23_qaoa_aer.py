from __future__ import annotations

from pathlib import Path

import pytest
from qiskit.quantum_info import Statevector

from traffic_simulation.r23_qaoa_aer.artifact import config_hash, semantic_artifact, write_smoke_artifact
from traffic_simulation.r23_qaoa_aer.hamiltonian import build_cost_operator, build_qaoa_circuit, repository_parameters
from traffic_simulation.r23_qaoa_aer.metrics import energy_statistics, probability_metrics, qiskit_label_to_bits
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, R23Input, R23SchemaError, R23_SCOPE, load_r22_instance


R22 = Path("reproducibility/outputs/traffic_simulation/r22_ising_conversion/20260910_formal_reduced_v1")


def tiny_input() -> R23Input:
    return R23Input("tiny", 1, (1,), 0, 3.0, {0: 2.0}, {}, "i" * 64, "q" * 64, 2.0, 1.0, frozenset({(1,)}), frozenset({(-1,)}), frozenset({(1,)}), {0: {0: 0.0, 1: 1.0}, 1: {0: 1.0, 1: 0.0}}, {"ising_global_minimum_energy": 1.0})


def test_r22_loader_and_provenance():
    data = load_r22_instance(R22, "synthetic_n2_unique")
    assert data.n == 2 and data.n_logical == 4
    assert data.payload["status"] == "PASS"
    assert data.ising_coefficient_hash
    assert data.normalized_matrix[0][1] > 0


def test_reject_missing_or_bad_r22_artifact():
    with pytest.raises(R23SchemaError):
        load_r22_instance(Path("/does/not/exist"), "x")


def test_operator_basis_state_and_constant_offset():
    data = tiny_input()
    operator = build_cost_operator(data)
    full_operator = build_cost_operator(data, include_constant=True)
    state = Statevector.from_label("1")
    assert float(state.expectation_value(operator).real) == pytest.approx(-2.0)
    assert float(state.expectation_value(full_operator).real) == pytest.approx(1.0)


def test_qaoa_circuit_mixer_and_parameter_convention():
    data = tiny_input()
    qc = build_qaoa_circuit(data, 2, (0.1, 0.2), (0.3, 0.4))
    assert qc.num_qubits == 1
    assert qc.depth() > 0
    assert repository_parameters((1, 2, 3, 4), 2) == ((1.0, 2.0), (3.0, 4.0))
    with pytest.raises(ValueError):
        build_qaoa_circuit(data, 2, (0.1,), (0.2, 0.3))


def test_qiskit_little_endian_label_conversion():
    assert qiskit_label_to_bits("010") == (0, 1, 0)


def test_probability_metrics_preserve_ties_and_invalid_mass():
    data = tiny_input()
    metrics = probability_metrics({"0": 0.25, "1": 0.75}, data, threshold=1e-12)
    assert metrics["P_feasible_exact"] == pytest.approx(0.75)
    assert metrics["P_opt"] == pytest.approx(0.75)
    assert metrics["invalid_probability_mass"] == pytest.approx(0.25)


def test_energy_statistics_uses_repository_qubit_order():
    data = tiny_input()
    # Qiskit label "1" maps to repository q0=1, hence spin=-1 and E=1.
    stats = energy_statistics({"1": 1.0}, data)
    assert stats["expectation"] == pytest.approx(1.0)
    assert stats["variance"] == pytest.approx(0.0)


def test_config_and_guard_validation():
    data = load_r22_instance(R22, "synthetic_n2_unique")
    R23Config(p=3).validate(data.n_logical)
    with pytest.raises(R23SchemaError):
        R23Config(p=4).validate(data.n_logical)
    with pytest.raises(R23SchemaError):
        R23Config(expectation_mode="shots").validate(data.n_logical)
    with pytest.raises(R23SchemaError):
        R23Config().validate(17)


def test_implementation_smoke_single_n2_p1(tmp_path):
    data = load_r22_instance(R22, "synthetic_n2_unique")
    config = R23Config(p=1, maxiter=5, max_evaluations=20, wall_time_seconds=60.0)
    result = run_single(data, config)
    assert result["formal_baseline"] is False
    assert result["backend"]["method"] == "statevector"
    assert result["logical_qubits"] == 4
    assert result["run_classification"] in {"OPTIMAL_FOUND", "FEASIBLE_SUBOPTIMAL", "NO_FEASIBLE_SOLUTION"}
    cfg = {"schema_version": "candidate-not-formally-frozen", "scope": R23_SCOPE, "p": 1, "instance_id": data.instance_id}
    manifest = write_smoke_artifact(cfg, result, tmp_path / "smoke")
    assert manifest["config_sha256"] == config_hash(cfg)
    assert semantic_artifact(result) == semantic_artifact(dict(result, timing=dict(result["timing"], total_wall_seconds=999.0)))


def test_smoke_semantic_result_is_deterministic():
    data = load_r22_instance(R22, "synthetic_n2_unique")
    config = R23Config(p=1, maxiter=5, max_evaluations=12, wall_time_seconds=60.0)
    first = run_single(data, config)
    second = run_single(data, config)
    assert semantic_artifact(first) == semantic_artifact(second)
