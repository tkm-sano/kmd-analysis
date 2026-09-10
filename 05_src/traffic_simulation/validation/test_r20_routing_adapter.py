from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from traffic_simulation.r20_route_ordering.core import (
    enumerate_qubo_states,
    enumerate_routes,
)
from traffic_simulation.r20_route_ordering.routing_adapter import (
    ACCEPTED,
    REJECTED_INCOMPLETE,
    REJECTED_INVALID,
    ZERO_TIME_UNRESOLVED,
    adapt_routing_artifact,
)
from traffic_simulation.r20_route_ordering.run_validation import run_instance


NODES = ("D", "A", "B", "C")
TIMES = {
    ("D", "A"): 11.0, ("A", "D"): 17.0,
    ("D", "B"): 23.0, ("B", "D"): 13.0,
    ("D", "C"): 19.0, ("C", "D"): 29.0,
    ("A", "B"): 7.0, ("B", "A"): 31.0,
    ("A", "C"): 37.0, ("C", "A"): 5.0,
    ("B", "C"): 41.0, ("C", "B"): 43.0,
}


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_artifact(tmp_path: Path, mutate=None, *, schema="evrp_routing_arc_v1") -> Path:
    artifact = tmp_path / "routing"
    artifact.mkdir(parents=True)
    endpoints = [
        {"endpoint_id": node, "endpoint_type": "depot" if node == "D" else "customer"}
        for node in NODES
    ]
    arcs = [
        {
            "origin_id": origin,
            "destination_id": destination,
            "reachable": "True",
            "distance_m": str(TIMES[origin, destination] * 10),
            "travel_time_s": str(TIMES[origin, destination]),
            "path_edge_sequence": json.dumps([f"{origin}-{destination}"]),
            "routing_objective": "travel_time_minimizing",
            "vehicle_class": "delivery",
            "network_hash": "network-test-hash",
            "run_config_version": "routing-test-v1",
            "status": "OK",
        }
        for origin in NODES
        for destination in NODES
        if origin != destination
    ]
    if mutate:
        mutate(arcs)
    _write_csv(artifact / "endpoint_manifest_input.csv", endpoints)
    _write_csv(artifact / "routing_arcs.csv", arcs)
    (artifact / "r12_config_snapshot.json").write_text(json.dumps({
        "run_id": "routing-test-v1",
        "output_schema": schema,
        "routing_objective": "travel_time_minimizing",
        "network_hash": "network-test-hash",
        "network_version": "test",
    }), encoding="utf-8")
    source_hash = hashlib.sha256((artifact / "routing_arcs.csv").read_bytes()).hexdigest()
    (artifact / "r13_manifest.json").write_text(json.dumps({
        "run_id": "routing-test-v1",
        "status": "PASS",
        "routing_objective": "travel_time_minimizing",
        "network_hash": "network-test-hash",
        "files": {"routing_arcs.csv": source_hash},
    }), encoding="utf-8")
    return artifact


def reason_codes(result):
    return {reason["code"] for reason in result["validation"]["reasons"]}


def test_complete_reachability_missing_diagonal_and_asymmetry_accepted(tmp_path):
    artifact = fixture_artifact(tmp_path)
    result = adapt_routing_artifact(artifact, "D", ["A", "B", "C"])
    assert result["accepted"]
    assert result["validation"]["status"] == ACCEPTED
    adapted = result["input"]
    assert adapted["expected_directed_pair_count"] == 12
    assert adapted["reachable_pair_count"] == 12
    assert adapted["complete_reachability"]
    assert adapted["raw_travel_time_matrix_s"]["A"]["B"] == 7.0
    assert adapted["raw_travel_time_matrix_s"]["B"]["A"] == 31.0
    assert adapted["normalization"]["diagonal_is_formal_edge"] is False
    assert adapted["asymmetric_pair_evidence"]


def test_normalization_is_correct_and_raw_is_not_modified(tmp_path):
    result = adapt_routing_artifact(fixture_artifact(tmp_path), "D", ["A", "B"])
    adapted = result["input"]
    raw = adapted["raw_travel_time_matrix_s"]
    normalized = adapted["normalized_travel_time_matrix"]
    assert adapted["normalization"]["tau_max_s"] == 31.0
    assert raw["B"]["A"] == 31.0
    assert normalized["B"]["A"] == 1.0
    assert normalized["A"]["B"] == 7.0 / 31.0


def test_silent_missing_is_distinct_rejection(tmp_path):
    def mutate(arcs):
        arcs[:] = [row for row in arcs if not (row["origin_id"] == "A" and row["destination_id"] == "B")]
    result = adapt_routing_artifact(fixture_artifact(tmp_path, mutate), "D", ["A", "B"])
    assert not result["accepted"] and result["input"] is None
    assert result["validation"]["status"] == REJECTED_INCOMPLETE
    assert "SILENT_MISSING_DIRECTED_PAIR" in reason_codes(result)


def test_explicit_unreachable_is_distinct_rejection(tmp_path):
    def mutate(arcs):
        row = next(row for row in arcs if row["origin_id"] == "A" and row["destination_id"] == "B")
        row.update(reachable="False", status="LEGITIMATE_UNREACHABLE", travel_time_s="", distance_m="")
    result = adapt_routing_artifact(fixture_artifact(tmp_path, mutate), "D", ["A", "B"])
    assert not result["accepted"] and result["input"] is None
    assert result["validation"]["status"] == REJECTED_INCOMPLETE
    assert "EXPLICIT_UNREACHABLE_DIRECTED_PAIR" in reason_codes(result)


@pytest.mark.parametrize("bad", ["", "nan", "inf", "-1"])
def test_malformed_reachable_travel_time_rejected(tmp_path, bad):
    def mutate(arcs):
        next(row for row in arcs if row["origin_id"] == "A" and row["destination_id"] == "B")["travel_time_s"] = bad
    result = adapt_routing_artifact(fixture_artifact(tmp_path, mutate), "D", ["A", "B"])
    assert result["validation"]["status"] == REJECTED_INVALID
    assert "MALFORMED_REACHABLE_TRAVEL_TIME" in reason_codes(result)


def test_nonself_zero_time_stops_with_specific_status(tmp_path):
    def mutate(arcs):
        next(row for row in arcs if row["origin_id"] == "A" and row["destination_id"] == "B")["travel_time_s"] = "0"
    result = adapt_routing_artifact(fixture_artifact(tmp_path, mutate), "D", ["A", "B"])
    assert result["validation"]["status"] == ZERO_TIME_UNRESOLVED
    assert "NONSELF_ZERO_TRAVEL_TIME" in reason_codes(result)


def test_duplicate_inconsistent_pair_rejected(tmp_path):
    def mutate(arcs):
        duplicate = dict(next(row for row in arcs if row["origin_id"] == "A" and row["destination_id"] == "B"))
        duplicate["travel_time_s"] = "99"
        arcs.append(duplicate)
    result = adapt_routing_artifact(fixture_artifact(tmp_path, mutate), "D", ["A", "B"])
    assert result["validation"]["status"] == REJECTED_INVALID
    assert "DUPLICATE_INCONSISTENT_EDGE" in reason_codes(result)


@pytest.mark.parametrize(
    "depot,customers,code",
    [
        ("D", ["A", "A"], "DUPLICATE_CUSTOMER_ID"),
        ("D", ["D", "A"], "DEPOT_CUSTOMER_OVERLAP"),
        ("UNKNOWN", ["A", "B"], "REQUESTED_DEPOT_MISSING"),
        ("D", ["A", "UNKNOWN"], "REQUESTED_CUSTOMER_MISSING"),
    ],
)
def test_requested_id_errors_are_rejected(tmp_path, depot, customers, code):
    result = adapt_routing_artifact(fixture_artifact(tmp_path), depot, customers)
    assert result["validation"]["status"] == REJECTED_INVALID
    assert code in reason_codes(result)


def test_schema_and_artifact_hash_mismatch_rejected(tmp_path):
    schema_result = adapt_routing_artifact(fixture_artifact(tmp_path / "schema", schema="wrong"), "D", ["A", "B"])
    assert "SOURCE_SCHEMA_VERSION_MISMATCH" in reason_codes(schema_result)
    artifact = fixture_artifact(tmp_path / "hash")
    with (artifact / "routing_arcs.csv").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    hash_result = adapt_routing_artifact(artifact, "D", ["A", "B"])
    assert "ARTIFACT_HASH_MISMATCH" in reason_codes(hash_result)


def test_real_semantics_route_and_qubo_consistency(tmp_path):
    result = adapt_routing_artifact(fixture_artifact(tmp_path), "D", ["A", "B", "C"])
    adapted = result["input"]
    raw = adapted["raw_travel_time_matrix_s"]
    normalized = adapted["normalized_travel_time_matrix"]
    raw_reference = enumerate_routes("D", ["A", "B", "C"], raw)
    normalized_reference = enumerate_routes("D", ["A", "B", "C"], normalized)
    assert raw_reference["best_route"] == ["D", "C", "A", "B", "D"]
    assert raw_reference["best_route_travel_time"] == 44.0
    assert raw_reference["optimal_routes"] == [["D", "C", "A", "B", "D"]]
    assert normalized_reference["optimal_routes"] == raw_reference["optimal_routes"]
    evidence = run_instance("fixture", "D", ["A", "B", "C"], raw, lambdas=[0.0, 2.0])
    assert all(item["direct_expanded_mismatch_count"] == 0 for item in evidence["lambda_results"])
    assert all(item["checks"]["qubo_route_optimum_matches_original"] for item in evidence["lambda_results"])
    assert any(item["all_global_minima_feasible"] for item in evidence["lambda_results"])
    qubo = enumerate_qubo_states("D", ["A", "B", "C"], normalized, 2.0)
    assert qubo["direct_expanded_mismatch_count"] == 0
