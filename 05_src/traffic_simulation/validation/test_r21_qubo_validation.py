from __future__ import annotations

import copy
import hashlib
import json

import pytest

from traffic_simulation.r20_route_ordering.core import build_expanded_qubo
from traffic_simulation.r20_route_ordering.run_validation import synthetic_instances
from traffic_simulation.r21_qubo_validation.artifact import semantic_artifact, write_validation_artifact
from traffic_simulation.r21_qubo_validation.runner import R21ValidationError, validate_reduced_r21
from traffic_simulation.r21_qubo_validation.schema import (
    R21_SCHEMA_VERSION,
    R21SchemaError,
    coefficient_hash,
    coefficients_to_payload,
    load_input,
)


def make_input(index=0, lam=2.0):
    _, depot, customers, raw = synthetic_instances()[index]
    from traffic_simulation.r20_route_ordering.core import normalize_travel_time_matrix

    normalized, tau_max = normalize_travel_time_matrix(depot, customers, raw)
    coefficients = build_expanded_qubo(depot, customers, normalized, lam)
    return {
        "schema_version": R21_SCHEMA_VERSION,
        "instance_id": f"test-{index}",
        "depot_id": depot,
        "customer_ids": customers,
        "n_customers": len(customers),
        "variable_ordering": "row-major:index=(i-1)*n+(t-1)",
        "raw_travel_time_matrix": raw,
        "normalized_travel_time_matrix": normalized,
        "tau_max": tau_max,
        "complete_reachability": True,
        "routing_source": {"artifact_id": "fixture", "artifact_sha256": "a" * 64},
        "r20_formulation_source_commit": "1" * 40,
        "r20_gate_commit": "2" * 40,
        "qubo_coefficients": coefficients_to_payload(coefficients),
        "coefficient_hash": coefficient_hash(coefficients),
        "lambda": lam,
        "bound_type": "test",
        "B": 0.5,
        "applied_margin": lam - 0.5,
        "numerical_tolerance": {"energy_abs": 1e-12},
        "classical_reference_config": {"method": "all_customer_permutations"},
    }


def test_valid_unique_and_tie_inputs_smoke_pass():
    assert validate_reduced_r21(make_input(0))["status"] == "PASS"
    assert validate_reduced_r21(make_input(2, lam=2.0))["checks"]["V3_route_set_equivalence"]


def test_schema_missing_and_mismatched_fields_rejected():
    value = make_input()
    value.pop("B")
    with pytest.raises(R21SchemaError, match="missing mandatory"):
        load_input(value)
    value = make_input()
    value["n_customers"] = 99
    with pytest.raises(R21SchemaError, match="n_customers"):
        load_input(value)
    value = make_input()
    value["qubo_coefficients"]["n_logical"] = 99
    value["coefficient_hash"] = "0" * 64
    with pytest.raises(R21SchemaError, match="logical-variable"):
        load_input(value)


def test_provenance_and_coefficient_hash_rejected():
    value = make_input()
    value["routing_source"].pop("artifact_sha256")
    with pytest.raises(R21SchemaError, match="SHA-256"):
        load_input(value)
    value = make_input()
    value["coefficient_hash"] = "0" * 64
    with pytest.raises(R21SchemaError, match="hash mismatch"):
        load_input(value)


@pytest.mark.parametrize("lam", [0.5, 0.4, float("nan"), float("inf")])
def test_lambda_bound_is_strict(lam):
    value = make_input()
    value["lambda"] = lam
    value["applied_margin"] = lam - value["B"]
    if not (lam == lam and lam not in (float("inf"), float("-inf"))):
        with pytest.raises((R21SchemaError, R21ValidationError)):
            validate_reduced_r21(value)
    else:
        with pytest.raises(R21ValidationError, match="lambda"):
            validate_reduced_r21(value)


def test_asymmetric_and_normalized_input_are_checked():
    result = validate_reduced_r21(make_input(3, lam=2.0))
    assert result["checks"]["V8_normalization_consistency"]
    assert result["checks"]["V4_direct_expanded_consistency"]


def test_guard_is_explicit():
    with pytest.raises(R21ValidationError, match="guarded"):
        validate_reduced_r21(make_input(), max_logical_variables=3)


def test_artifact_semantics_and_manifest(tmp_path):
    result = validate_reduced_r21(make_input())
    first = semantic_artifact(result)
    second = semantic_artifact({**result, "metadata": {**result["metadata"], "runtime_seconds": 999}})
    assert first == second
    manifest = write_validation_artifact(result, tmp_path / "smoke")
    report = json.loads((tmp_path / "smoke" / "validation_results.json").read_text())
    assert manifest["files"]["validation_results.json"] == hashlib.sha256((tmp_path / "smoke" / "validation_results.json").read_bytes()).hexdigest()
    assert report["metadata"]["implementation_smoke_only"] is True
