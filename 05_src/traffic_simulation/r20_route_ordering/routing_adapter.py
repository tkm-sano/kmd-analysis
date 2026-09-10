"""Versioned Routing Baseline to R20 complete-reachability adapter.

This adapter is for exact formulation validation only.  It never executes
QAOA, invents costs for unreachable arcs, or implements an unreachable-edge
penalty.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any


ADAPTER_VERSION = "1.0.0"
INPUT_SCHEMA_VERSION = "r20-route-ordering-input-v1"
SOURCE_SCHEMA_VERSION = "evrp_routing_arc_v1"
ACCEPTED = "R20_INPUT_ACCEPTED_COMPLETE_REACHABILITY"
REJECTED_INCOMPLETE = "R20_INPUT_REJECTED_INCOMPLETE_REACHABILITY"
REJECTED_INVALID = "R20_INPUT_REJECTED_INVALID"
ZERO_TIME_UNRESOLVED = "ROUTING_BASELINE_ZERO_TIME_POLICY_UNRESOLVED"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return value


def select_customer_ids(artifact_dir: Path | str, count: int) -> list[str]:
    """Select the first customers in source endpoint-manifest order."""
    if type(count) is not int or count <= 0:
        raise ValueError("count must be a positive integer")
    rows = _read_csv(Path(artifact_dir) / "endpoint_manifest_input.csv")
    selected = [row["endpoint_id"] for row in rows if row.get("endpoint_type") == "customer"][:count]
    if len(selected) != count:
        raise ValueError(f"only {len(selected)} customer endpoints available")
    return selected


def _base_result(artifact_dir: Path, depot_id: Any, customer_ids: Any) -> dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "schema_version": INPUT_SCHEMA_VERSION,
        "source_artifact": str(artifact_dir),
        "requested_depot_id": depot_id,
        "requested_customer_ids": list(customer_ids) if isinstance(customer_ids, Sequence) and not isinstance(customer_ids, (str, bytes)) else customer_ids,
        "accepted": False,
        "input": None,
        "validation": {"status": REJECTED_INVALID, "reasons": [], "runtime_seconds": None},
    }


def adapt_routing_artifact(
    artifact_dir: Path | str,
    depot_id: Any,
    customer_ids: Sequence[Any],
    *,
    source_schema_version: str = SOURCE_SCHEMA_VERSION,
    expected_source_sha256: str | None = None,
    instance_id: str | None = None,
) -> dict[str, Any]:
    """Validate and adapt one complete-reachability node subset.

    Rejections are returned as data.  A rejected result never contains an R20
    matrix under ``input`` and therefore cannot be passed accidentally to the
    exact/QUBO layer.
    """
    started = time.perf_counter()
    directory = Path(artifact_dir)
    result = _base_result(directory, depot_id, customer_ids)
    reasons: list[dict[str, Any]] = result["validation"]["reasons"]
    rejection_status = REJECTED_INVALID

    def reject(code: str, **details: Any) -> None:
        reasons.append({"code": code, **details})

    if not isinstance(customer_ids, Sequence) or isinstance(customer_ids, (str, bytes)):
        reject("INVALID_CUSTOMER_ID_LIST")
        result["validation"]["runtime_seconds"] = time.perf_counter() - started
        return result
    customers = tuple(customer_ids)
    try:
        customer_set = set(customers)
    except TypeError:
        reject("UNHASHABLE_CUSTOMER_ID")
        result["validation"]["runtime_seconds"] = time.perf_counter() - started
        return result
    if not customers:
        reject("EMPTY_CUSTOMER_ID_LIST")
    if len(customer_set) != len(customers):
        reject("DUPLICATE_CUSTOMER_ID")
    if depot_id in customer_set:
        reject("DEPOT_CUSTOMER_OVERLAP", depot_id=depot_id)

    required_names = (
        "routing_arcs.csv",
        "endpoint_manifest_input.csv",
        "r12_config_snapshot.json",
        "r13_manifest.json",
    )
    missing_files = [name for name in required_names if not (directory / name).is_file()]
    if missing_files:
        reject("MISSING_ARTIFACT_FILE", files=missing_files)
    if reasons:
        result["validation"]["runtime_seconds"] = time.perf_counter() - started
        return result

    try:
        endpoints = _read_csv(directory / "endpoint_manifest_input.csv")
        arcs = _read_csv(directory / "routing_arcs.csv")
        config = _read_json(directory / "r12_config_snapshot.json")
        manifest = _read_json(directory / "r13_manifest.json")
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        reject("ARTIFACT_PARSE_ERROR", error=str(exc))
        result["validation"]["runtime_seconds"] = time.perf_counter() - started
        return result

    source_hash = sha256_file(directory / "routing_arcs.csv")
    declared_hash = manifest.get("files", {}).get("routing_arcs.csv")
    if declared_hash != source_hash:
        reject("ARTIFACT_HASH_MISMATCH", declared=declared_hash, actual=source_hash)
    if expected_source_sha256 is not None and expected_source_sha256 != source_hash:
        reject("EXPECTED_SOURCE_HASH_MISMATCH", expected=expected_source_sha256, actual=source_hash)
    if config.get("output_schema") != source_schema_version or source_schema_version != SOURCE_SCHEMA_VERSION:
        reject("SOURCE_SCHEMA_VERSION_MISMATCH", expected=source_schema_version, actual=config.get("output_schema"))
    if manifest.get("status") != "PASS":
        reject("SOURCE_MANIFEST_NOT_PASS", actual=manifest.get("status"))
    if config.get("routing_objective") != "travel_time_minimizing" or manifest.get("routing_objective") != "travel_time_minimizing":
        reject("SOURCE_OBJECTIVE_MISMATCH")
    if config.get("network_hash") != manifest.get("network_hash"):
        reject("SOURCE_NETWORK_HASH_MISMATCH")

    endpoint_by_id: dict[str, dict[str, str]] = {}
    duplicate_endpoint_ids: list[str] = []
    for row in endpoints:
        endpoint = row.get("endpoint_id")
        if endpoint in endpoint_by_id:
            duplicate_endpoint_ids.append(str(endpoint))
        else:
            endpoint_by_id[str(endpoint)] = row
    if duplicate_endpoint_ids:
        reject("DUPLICATE_ENDPOINT_ID", endpoint_ids=sorted(set(duplicate_endpoint_ids)))
    if depot_id not in endpoint_by_id:
        reject("REQUESTED_DEPOT_MISSING", depot_id=depot_id)
    elif endpoint_by_id[depot_id].get("endpoint_type") != "depot":
        reject("REQUESTED_DEPOT_ROLE_INVALID", depot_id=depot_id)
    for customer in customers:
        if customer not in endpoint_by_id:
            reject("REQUESTED_CUSTOMER_MISSING", customer_id=customer)
        elif endpoint_by_id[customer].get("endpoint_type") != "customer":
            reject("REQUESTED_CUSTOMER_ROLE_INVALID", customer_id=customer)

    if reasons:
        result["validation"]["runtime_seconds"] = time.perf_counter() - started
        return result

    all_pairs: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row_number, row in enumerate(arcs, start=2):
        origin, destination = row.get("origin_id"), row.get("destination_id")
        if origin not in endpoint_by_id or destination not in endpoint_by_id:
            reject("UNKNOWN_EDGE_ENDPOINT", row_number=row_number, origin_id=origin, destination_id=destination)
            continue
        if origin == destination:
            continue
        all_pairs.setdefault((str(origin), str(destination)), []).append(row)

    nodes = (depot_id, *customers)
    required_pairs = [(origin, destination) for origin in nodes for destination in nodes if origin != destination]
    expected_pair_count = len(nodes) * (len(nodes) - 1)
    raw_edges: list[dict[str, Any]] = []
    raw_matrix: dict[Any, dict[Any, float]] = {node: {node: 0.0} for node in nodes}
    distance_matrix: dict[Any, dict[Any, float | None]] = {node: {node: None} for node in nodes}
    explicit_unreachable = 0
    reachable_count = 0

    for origin, destination in required_pairs:
        records = all_pairs.get((origin, destination), [])
        if not records:
            rejection_status = REJECTED_INCOMPLETE
            reject("SILENT_MISSING_DIRECTED_PAIR", origin_id=origin, destination_id=destination)
            continue
        if len(records) > 1:
            canonical = {json.dumps(record, sort_keys=True) for record in records}
            reject("DUPLICATE_INCONSISTENT_EDGE" if len(canonical) > 1 else "DUPLICATE_EDGE", origin_id=origin, destination_id=destination, count=len(records))
            continue
        row = records[0]
        reachable_text = row.get("reachable")
        status = row.get("status")
        travel_text = row.get("travel_time_s")
        distance_text = row.get("distance_m")
        if reachable_text == "False" and status == "LEGITIMATE_UNREACHABLE" and travel_text in (None, "") and distance_text in (None, ""):
            explicit_unreachable += 1
            rejection_status = REJECTED_INCOMPLETE
            reject("EXPLICIT_UNREACHABLE_DIRECTED_PAIR", origin_id=origin, destination_id=destination)
            continue
        if reachable_text != "True" or status != "OK":
            reject("MALFORMED_EDGE_SEMANTICS", origin_id=origin, destination_id=destination, reachable=reachable_text, status=status)
            continue
        try:
            travel_time = float(travel_text)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            reject("MALFORMED_REACHABLE_TRAVEL_TIME", origin_id=origin, destination_id=destination, value=travel_text)
            continue
        if not math.isfinite(travel_time) or travel_time < 0:
            reject("MALFORMED_REACHABLE_TRAVEL_TIME", origin_id=origin, destination_id=destination, value=travel_text)
            continue
        if travel_time == 0:
            rejection_status = ZERO_TIME_UNRESOLVED
            reject("NONSELF_ZERO_TRAVEL_TIME", origin_id=origin, destination_id=destination)
            continue
        distance: float | None = None
        if distance_text not in (None, ""):
            try:
                distance = float(distance_text)
            except (TypeError, ValueError):
                reject("MALFORMED_REACHABLE_DISTANCE", origin_id=origin, destination_id=destination, value=distance_text)
                continue
            if not math.isfinite(distance) or distance < 0:
                reject("MALFORMED_REACHABLE_DISTANCE", origin_id=origin, destination_id=destination, value=distance_text)
                continue
        else:
            reject("MALFORMED_REACHABLE_DISTANCE", origin_id=origin, destination_id=destination, value=distance_text)
            continue
        raw_matrix[origin][destination] = travel_time
        distance_matrix[origin][destination] = distance
        reachable_count += 1
        raw_edges.append({
            "origin_id": origin,
            "destination_id": destination,
            "reachable": True,
            "status": "OK",
            "travel_time_s": travel_time,
            "distance_m": distance,
            "path_edge_sequence": row.get("path_edge_sequence"),
            "source_run_config_version": row.get("run_config_version"),
        })

    complete = not reasons and reachable_count == expected_pair_count
    reason_codes = {reason["code"] for reason in reasons}
    incomplete_codes = {"SILENT_MISSING_DIRECTED_PAIR", "EXPLICIT_UNREACHABLE_DIRECTED_PAIR"}
    if "NONSELF_ZERO_TRAVEL_TIME" in reason_codes:
        rejection_status = ZERO_TIME_UNRESOLVED
    elif reason_codes - incomplete_codes:
        rejection_status = REJECTED_INVALID
    elif reason_codes:
        rejection_status = REJECTED_INCOMPLETE
    result["validation"].update({
        "status": ACCEPTED if complete else rejection_status,
        "expected_directed_pair_count": expected_pair_count,
        "observed_selected_pair_count": sum(bool(all_pairs.get(pair)) for pair in required_pairs),
        "reachable_pair_count": reachable_count,
        "explicit_unreachable_pair_count": explicit_unreachable,
        "complete_reachability": complete,
        "runtime_seconds": time.perf_counter() - started,
    })
    if not complete:
        return result

    tau_max = max(raw_matrix[origin][destination] for origin, destination in required_pairs)
    if not math.isfinite(tau_max) or tau_max <= 0:
        reject("NORMALIZATION_IMPOSSIBLE", tau_max=tau_max)
        result["validation"].update({"status": REJECTED_INVALID, "complete_reachability": False})
        return result
    normalized = {
        origin: {
            destination: 0.0 if origin == destination else raw_matrix[origin][destination] / tau_max
            for destination in nodes
        }
        for origin in nodes
    }
    asymmetry = [
        {
            "node_a": left,
            "node_b": right,
            "a_to_b_s": raw_matrix[left][right],
            "b_to_a_s": raw_matrix[right][left],
            "absolute_difference_s": abs(raw_matrix[left][right] - raw_matrix[right][left]),
        }
        for index, left in enumerate(nodes)
        for right in nodes[index + 1 :]
        if raw_matrix[left][right] != raw_matrix[right][left]
    ]
    input_identity = {
        "source_sha256": source_hash,
        "depot_id": depot_id,
        "customer_ids": list(customers),
        "raw_edges": raw_edges,
        "adapter_version": ADAPTER_VERSION,
    }
    result["accepted"] = True
    result["input"] = {
        "instance_id": instance_id or f"{directory.name}__depot_{depot_id}__n{len(customers)}",
        "schema_version": INPUT_SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "depot_id": depot_id,
        "customer_ids": list(customers),
        "n_customers": len(customers),
        "node_set": list(nodes),
        "expected_directed_pair_count": expected_pair_count,
        "reachable_pair_count": reachable_count,
        "complete_reachability": True,
        "raw_directed_edges": raw_edges,
        "raw_travel_time_matrix_s": raw_matrix,
        "distance_matrix_m_auxiliary": distance_matrix,
        "normalized_travel_time_matrix": normalized,
        "normalization": {
            "rule": "reachable_valid_selected_nonself_tau_divided_by_tau_max",
            "tau_max_s": tau_max,
            "diagonal_placeholder": 0.0,
            "diagonal_is_formal_edge": False,
            "raw_matrix_immutable": True,
        },
        "asymmetric_pair_evidence": asymmetry,
        "source": {
            "artifact_path": str(directory),
            "artifact_run_id": manifest.get("run_id"),
            "routing_arcs_sha256": source_hash,
            "source_schema_version": config.get("output_schema"),
            "source_run_id": config.get("run_id"),
            "network_hash": config.get("network_hash"),
            "network_version": config.get("network_version"),
            "routing_objective": config.get("routing_objective"),
            "travel_time_unit": "s",
            "distance_unit": "m",
        },
        "input_sha256": sha256_json(input_identity),
    }
    result["validation"]["runtime_seconds"] = time.perf_counter() - started
    return result
