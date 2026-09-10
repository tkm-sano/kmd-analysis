#!/usr/bin/env python3
"""Compute R13 directed EVRP routing arcs from the fixed R12 contract.

The runner uses the accepted SUMO network through the repository's bundled
``sumolib``.  Routing cost is free-flow edge travel time, while distance is
reported for the same selected path.  Endpoint offsets are represented as
partial directed-edge segments; endpoints are never rounded to nodes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SUMO_TOOLS = ROOT / ".local" / "sumo-1.24.0" / "share" / "sumo" / "tools"
if str(SUMO_TOOLS) not in sys.path:
    sys.path.insert(0, str(SUMO_TOOLS))
import sumolib  # type: ignore  # noqa: E402


RUNNER_VERSION = "1.0.0"
ALLOWED_STATUS = {
    "OK",
    "LEGITIMATE_UNREACHABLE",
    "ROUTING_ENGINE_FAILURE",
    "INVALID_ENDPOINT",
    "MISSING_OD",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object expected: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def edge_time(edge: Any) -> float:
    length = float(edge.getLength())
    speed = float(edge.getSpeed())
    if not math.isfinite(length) or not math.isfinite(speed) or length < 0 or speed <= 0:
        raise ValueError(f"invalid edge length/speed: {edge.getID()}")
    return length / speed


def partial_cost(edge: Any, distance: float) -> tuple[float, float]:
    length = float(edge.getLength())
    if distance < -1e-8 or distance > length + 1e-8:
        raise ValueError(f"offset outside edge: {edge.getID()} {distance} / {length}")
    distance = min(max(distance, 0.0), length)
    return distance, edge_time(edge) * (distance / length if length else 0.0)


def has_vehicle_access(edge: Any, vehicle_class: str) -> bool:
    permissions = edge.getPermissions() or []
    return vehicle_class in permissions


def dijkstra_from_node(net: Any, start_node: Any, vehicle_class: str) -> tuple[dict[str, float], dict[str, tuple[str, str]]]:
    """Fastest directed path from a SUMO node over permitted edges."""

    start = start_node.getID()
    distance: dict[str, float] = {start: 0.0}
    previous: dict[str, tuple[str, str]] = {}
    heap: list[tuple[float, str]] = [(0.0, start)]
    nodes = {node.getID(): node for node in net.getNodes()}
    while heap:
        cost, node_id = heapq.heappop(heap)
        if cost > distance[node_id] + 1e-12:
            continue
        node = nodes[node_id]
        outgoing = sorted(node.getOutgoing(), key=lambda edge: edge.getID())
        for edge in outgoing:
            if not has_vehicle_access(edge, vehicle_class):
                continue
            nxt = edge.getToNode().getID()
            candidate = cost + edge_time(edge)
            old = distance.get(nxt, math.inf)
            if candidate < old - 1e-12:
                distance[nxt] = candidate
                previous[nxt] = (node_id, edge.getID())
                heapq.heappush(heap, (candidate, nxt))
            elif abs(candidate - old) <= 1e-12:
                old_edge = previous.get(nxt, ("", "~"))[1]
                if edge.getID() < old_edge:
                    previous[nxt] = (node_id, edge.getID())
                    heapq.heappush(heap, (candidate, nxt))
    return distance, previous


def reconstruct_edges(previous: dict[str, tuple[str, str]], start: str, target: str) -> list[str]:
    if start == target:
        return []
    result: list[str] = []
    current = target
    while current != start:
        if current not in previous:
            raise KeyError(target)
        prior, edge_id = previous[current]
        result.append(edge_id)
        current = prior
    result.reverse()
    return result


def route_between(origin: dict[str, str], destination: dict[str, str], net: Any, vehicle_class: str) -> dict[str, Any]:
    """Route between two offset points on directed SUMO edges."""

    origin_edge = net.getEdge(origin["mapped_edge_id"])
    destination_edge = net.getEdge(destination["mapped_edge_id"])
    if origin_edge is None or destination_edge is None:
        return {"reachable": False, "distance_m": None, "travel_time_s": None, "path_edge_sequence": None, "status": "INVALID_ENDPOINT"}
    if not has_vehicle_access(origin_edge, vehicle_class) or not has_vehicle_access(destination_edge, vehicle_class):
        return {"reachable": False, "distance_m": None, "travel_time_s": None, "path_edge_sequence": None, "status": "INVALID_ENDPOINT"}

    origin_offset = float(origin["edge_offset_m"])
    destination_offset = float(destination["edge_offset_m"])
    origin_length = float(origin_edge.getLength())
    destination_length = float(destination_edge.getLength())
    if not (0 <= origin_offset <= origin_length and 0 <= destination_offset <= destination_length):
        return {"reachable": False, "distance_m": None, "travel_time_s": None, "path_edge_sequence": None, "status": "INVALID_ENDPOINT"}

    # The R12 contract requires a direct directed same-edge segment when moving
    # forward.  Reverse offsets must use the network, never abs(offset delta).
    if origin_edge.getID() == destination_edge.getID() and destination_offset >= origin_offset:
        distance, travel = partial_cost(origin_edge, destination_offset - origin_offset)
        return {"reachable": True, "distance_m": distance, "travel_time_s": travel, "path_edge_sequence": [origin_edge.getID()], "status": "OK", "origin_partial_distance_m": 0.0, "origin_partial_time_s": 0.0, "network_path_distance_m": distance, "network_path_time_s": travel, "destination_partial_distance_m": 0.0, "destination_partial_time_s": 0.0}

    origin_remaining = origin_length - origin_offset
    origin_distance, origin_time = partial_cost(origin_edge, origin_remaining)
    destination_distance, destination_time = partial_cost(destination_edge, destination_offset)

    distances, previous = dijkstra_from_node(net, origin_edge.getToNode(), vehicle_class)
    target_node = destination_edge.getFromNode().getID()
    if target_node not in distances:
        return {"reachable": False, "distance_m": None, "travel_time_s": None, "path_edge_sequence": None, "status": "LEGITIMATE_UNREACHABLE"}

    graph_edges = reconstruct_edges(previous, origin_edge.getToNode().getID(), target_node)
    graph_distance = sum(float(net.getEdge(edge_id).getLength()) for edge_id in graph_edges)
    graph_time = sum(edge_time(net.getEdge(edge_id)) for edge_id in graph_edges)
    total_distance = origin_distance + graph_distance + destination_distance
    total_time = origin_time + graph_time + destination_time
    path = [origin_edge.getID(), *graph_edges]
    if destination_edge.getID() not in graph_edges:
        path.append(destination_edge.getID())
    return {
        "reachable": True,
        "distance_m": total_distance,
        "travel_time_s": total_time,
        "path_edge_sequence": path,
        "status": "OK",
        "origin_partial_distance_m": origin_distance,
        "origin_partial_time_s": origin_time,
        "network_path_distance_m": graph_distance,
        "network_path_time_s": graph_time,
        "destination_partial_distance_m": destination_distance,
        "destination_partial_time_s": destination_time,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    config = load_json(config_path)
    network_path = ROOT / config["network_path"]
    expected_hash = config["network_hash"]
    if sha256(network_path) != expected_hash:
        raise RuntimeError("network hash mismatch")
    if config["vehicle_class"] != "delivery":
        raise RuntimeError("R12 vehicle class mismatch")
    if config["routing_objective"] != "travel_time_minimizing":
        raise RuntimeError("R12 routing objective mismatch")
    input_dir = config_path.parent
    endpoint_rows = read_csv(input_dir / "endpoint_manifest.csv")
    od_rows = read_csv(input_dir / "od_manifest.csv")
    if len(endpoint_rows) != 12 or len(od_rows) != 132:
        raise RuntimeError("R12 endpoint/OD count mismatch")
    endpoint_by_id = {row["endpoint_id"]: row for row in endpoint_rows}
    if len(endpoint_by_id) != len(endpoint_rows):
        raise RuntimeError("duplicate endpoint")
    if len({(row["origin_id"], row["destination_id"]) for row in od_rows}) != 132:
        raise RuntimeError("duplicate OD")
    net = sumolib.net.readNet(str(network_path))
    started = time.time()
    output_dir = Path(args.output_dir) if args.output_dir else ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing" / config["run_id"]
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for od in od_rows:
        origin = endpoint_by_id[od["origin_id"]]
        destination = endpoint_by_id[od["destination_id"]]
        result = route_between(origin, destination, net, config["vehicle_class"])
        rows.append({
            "origin_id": od["origin_id"], "destination_id": od["destination_id"],
            "origin_type": od["origin_type"], "destination_type": od["destination_type"],
            "origin_edge": origin["mapped_edge_id"], "destination_edge": destination["mapped_edge_id"],
            "origin_offset_m": float(origin["edge_offset_m"]), "destination_offset_m": float(destination["edge_offset_m"]),
            "reachable": bool(result["reachable"]), "distance_m": result["distance_m"], "travel_time_s": result["travel_time_s"],
            "path_edge_sequence": json.dumps(result["path_edge_sequence"], separators=(",", ":")) if result["path_edge_sequence"] is not None else None,
            "path_reference": None, "routing_objective": config["routing_objective"], "vehicle_class": config["vehicle_class"],
            "network_hash": expected_hash, "run_config_version": config["run_id"], "status": result["status"],
            "origin_partial_distance_m": result.get("origin_partial_distance_m"), "origin_partial_time_s": result.get("origin_partial_time_s"),
            "network_path_distance_m": result.get("network_path_distance_m"), "network_path_time_s": result.get("network_path_time_s"),
            "destination_partial_distance_m": result.get("destination_partial_distance_m"), "destination_partial_time_s": result.get("destination_partial_time_s"),
        })
    result_path = output_dir / "routing_arcs.csv"
    fields = list(rows[0].keys())
    with result_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    log = {"runner_version": RUNNER_VERSION, "config_path": str(config_path.relative_to(ROOT)), "output_path": str(result_path.relative_to(ROOT)), "network_hash": expected_hash, "vehicle_class": config["vehicle_class"], "routing_objective": config["routing_objective"], "od_count": len(rows), "elapsed_seconds": time.time() - started}
    (output_dir / "execution_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"routing_arcs": len(rows), "output": str(result_path), "network_hash": expected_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
