from __future__ import annotations

import json
from pathlib import Path

import pytest

from traffic_simulation.r20_route_ordering.core import QuboCoefficients, build_expanded_qubo, normalize_travel_time_matrix
from traffic_simulation.r21_qubo_validation.schema import coefficients_to_payload
from traffic_simulation.r22_ising_conversion.artifact import semantic_artifact, write_conversion_artifact
from traffic_simulation.r22_ising_conversion.converter import (
    BINARY_SPIN_CONVENTION,
    IsingInputError,
    binary_to_spin,
    convert_qubo_to_ising,
    evaluate_ising,
    spin_to_binary,
)
from traffic_simulation.r22_ising_conversion.schema import R22_SCHEMA_VERSION, R22SchemaError, coefficient_hash, load_input, load_r21_instance
from traffic_simulation.r22_ising_conversion.validator import R22ValidationError, validate_conversion


def tiny_qubo():
    return QuboCoefficients(3.0, {0: 2.0, 1: -4.0}, {(0, 1): 8.0}, 2)


def route_qubo():
    return QuboCoefficients(3.0, {0: 2.0, 1: -4.0, 2: 0.0, 3: 0.0}, {(0, 1): 8.0}, 4)


def make_input(qubo=None):
    if qubo is None:
        raw = {0: {0: 0.0, 1: 1.0, 2: 8.0}, 1: {0: 7.0, 1: 0.0, 2: 1.0}, 2: {0: 1.0, 1: 7.0, 2: 0.0}}
        normalized, _ = normalize_travel_time_matrix(0, [1, 2], raw)
        qubo = build_expanded_qubo(0, [1, 2], normalized, 2.0)
    return {
        "schema_version": R22_SCHEMA_VERSION,
        "r21": {"artifact_id": "r21-fixture", "validation_results_sha256": "a" * 64, "manifest_sha256": "b" * 64, "status": "PASS", "scope": "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"},
        "instance_id": "fixture", "depot_id": 0, "customer_ids": [1, 2], "n": 2, "n_logical": 4,
        "variable_ordering": "row-major:index=(i-1)*n+(t-1)", "qubo_coefficients": coefficients_to_payload(qubo), "qubo_coefficient_hash": coefficient_hash(qubo),
        "lambda": 2.0, "B": 1.0, "bound_type": "test", "normalization_metadata": {"rule": "tau/tau_max"}, "numerical_tolerance": {"energy_abs": 1e-12},
        "r21_global_minimum_bitstrings": [], "r21_optimal_routes": [],
    }


def test_hand_computable_conversion():
    ising = convert_qubo_to_ising(tiny_qubo())
    assert ising.binary_spin_convention == BINARY_SPIN_CONVENTION
    assert ising.constant == 4.0  # 3 + 2/2 - 4/2 + 8/4
    assert ising.linear == {0: -3.0, 1: 0.0}
    assert ising.quadratic == {(0, 1): 2.0}


def test_mapping_roundtrips_and_malformed_values():
    for bits in ((0, 0), (0, 1), (1, 0), (1, 1)):
        assert spin_to_binary(binary_to_spin(bits)) == bits
    for spins in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        assert binary_to_spin(spin_to_binary(spins)) == spins
    with pytest.raises(IsingInputError): binary_to_spin((0, 2))
    with pytest.raises(IsingInputError): spin_to_binary((1, 0))


def test_all_tiny_states_energy_equivalence():
    inp = load_input(make_input())
    result = validate_conversion(inp)
    assert result["status"] == "PASS"
    assert result["checks"]["I1_conversion_algebra"]
    assert result["checks"]["I3_energy_equivalence"]
    assert result["max_abs_energy_mismatch"] <= 1e-12


def test_wrong_j_factor_and_wrong_sign_are_detectable():
    inp = load_input(make_input())
    expected = convert_qubo_to_ising(tiny_qubo())
    assert evaluate_ising(binary_to_spin((1, 1)), expected) == pytest.approx(3.0 + 2.0 - 4.0 + 8.0)
    wrong = type(expected)(expected.constant, expected.linear, {(0, 1): 4.0}, expected.n_logical)
    assert evaluate_ising(binary_to_spin((1, 1)), wrong) != pytest.approx(3.0 + 2.0 - 4.0 + 8.0)
    correct = binary_to_spin((1, 0))
    wrong_sign = tuple(2 * value - 1 for value in (1, 0))
    assert wrong_sign != correct
    assert evaluate_ising(wrong_sign, expected) != evaluate_ising(correct, expected)


def test_mutated_coefficients_fail_i1_and_energy_equivalence():
    inp = load_input(make_input())
    expected = convert_qubo_to_ising(inp.qubo)
    mutated_h = type(expected)(expected.constant, {0: expected.linear[0] + 1.0, **{k: v for k, v in expected.linear.items() if k != 0}}, expected.quadratic, expected.n_logical)
    mutated_offset = type(expected)(expected.constant + 1.0, expected.linear, expected.quadratic, expected.n_logical)
    assert validate_conversion(inp, ising=mutated_h)["checks"]["I1_conversion_algebra"] is False
    assert validate_conversion(inp, ising=mutated_offset)["checks"]["I3_energy_equivalence"] is False


def test_r21_schema_and_hash_failures():
    value = make_input(); value["r21"]["status"] = "FAIL"
    with pytest.raises(R22SchemaError, match="not PASS"): load_input(value)
    value = make_input(); value["qubo_coefficient_hash"] = "0" * 64
    with pytest.raises(R22SchemaError, match="hash mismatch"): load_input(value)
    value = make_input(); value["lambda"] = value["B"]
    with pytest.raises(R22SchemaError, match="strictly greater"): load_input(value)


def test_guard_and_artifact_determinism(tmp_path):
    inp = load_input(make_input())
    with pytest.raises(R22ValidationError, match="guarded"): validate_conversion(inp, max_logical_variables=1)
    result = validate_conversion(inp)
    result["runtime_seconds"] = 1.0
    clone = dict(result); clone["runtime_seconds"] = 999.0
    assert semantic_artifact(result) == semantic_artifact(clone)
    manifest = write_conversion_artifact(result, tmp_path / "smoke")
    assert json.loads((tmp_path / "smoke" / "manifest.json").read_text())["status"] == "PASS"
    assert manifest["files"]["conversion_results.json"]


def test_authoritative_r21_artifact_loader_verifies_v4():
    artifact = Path("reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4")
    if not artifact.exists():
        pytest.skip("authoritative R21 output is unavailable")
    inp = load_r21_instance(artifact, "routing_baseline_v18_first_2_customers")
    assert inp.payload["r21"]["status"] == "PASS"
    assert inp.payload["r21"]["scope"] == "INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY"
