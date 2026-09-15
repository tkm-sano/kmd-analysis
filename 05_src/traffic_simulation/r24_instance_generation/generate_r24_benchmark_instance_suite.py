#!/usr/bin/env python3
"""Generate the frozen R24 benchmark instance suite.

This implements R24-INSTANCE-GEN-20260915-v1.  It does not optimize a CVRP
and does not mutate demand, the routing graph, or the frozen specification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pyproj import Transformer
from sumolib.net import readNet


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_ID = "R24-INSTANCE-GEN-20260915-v1"
PROTOCOL_VERSION = "20260915_v1"
START_SHA = "44f7960abefe4df9648dd00b738885a14813ba54"
SOURCE = ROOT / "reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/C_ELIGIBLE_MANIFEST.csv"
SOURCE_HASH = "245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c"
NETWORK = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml"
NETWORK_ACCEPTANCE = NETWORK.parent / "network_acceptance.json"
NETWORK_HASH = "460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
GRAPH_ID = "P13-THREE-TIER-RUN-3-GEOMETRY-REACCEPTANCE"
DEPOT_SOURCE = ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r09_depot/20260909_r09_depot_fixture_n10_v18_geometry_reaccepted_repeat/depot_definition.csv"
DEPOT_ID = "DEP_006"
DEPOT_EDGE = "617631294"
CAPACITY_UNIT = "METHODOLOGICAL_PARCEL_EQUIVALENT"
Q = 14
RANDOM_NS = (2, 3, 4, 5, 8, 10, 15, 20)
STRUCTURAL_NS = (4, 10, 20)
STRUCTURES = ("CLUSTERED", "DISPERSED", "MIXED")
RHOS = (("LOOSE", "0.50", "RHO050"), ("MODERATE", "0.70", "RHO070"), ("TIGHT", "0.90", "RHO090"))
VCLASS = "delivery"
PACKING_ALGORITHM = "SYMMETRY_REDUCED_MEMOIZED_EXACT_BIN_PACKING_V1"
OUT_DEFAULT = ROOT / "reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def content_hash(value: dict[str, Any]) -> str:
    return sha_bytes(canonical_bytes({k: v for k, v in value.items() if k != "output_sha256"}))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def seed_record(suite: str, n: int, rep: int, structure: str | None = None) -> dict[str, Any]:
    if suite == "RND":
        material = f"{PROTOCOL_ID}|suite=RND|n={n}|rep={rep:02d}"
    else:
        material = f"{PROTOCOL_ID}|suite=STR|structure={structure}|n={n}|rep={rep:02d}"
    digest = sha_bytes(material.encode())
    return {
        "seed_material": material,
        "seed_digest_sha256": digest,
        "seed_uint64": int.from_bytes(bytes.fromhex(digest)[:8], "big"),
    }


def selection_score(seed_digest: str, customer_id: str) -> str:
    return sha_bytes(f"{seed_digest}|customer={customer_id}".encode())


def select_random(rows: list[dict[str, Any]], seed: dict[str, Any], n: int) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: (selection_score(seed["seed_digest_sha256"], row["benchmark_customer_id"]), row["benchmark_customer_id"].encode()))
    return sorted(ranked[:n], key=lambda row: row["benchmark_customer_id"].encode())


def select_structural(rows: list[dict[str, Any]], seed: dict[str, Any], n: int, structure: str) -> list[dict[str, Any]]:
    score = {row["benchmark_customer_id"]: selection_score(seed["seed_digest_sha256"], row["benchmark_customer_id"]) for row in rows}
    by_score = sorted(rows, key=lambda row: (score[row["benchmark_customer_id"]], row["benchmark_customer_id"].encode()))
    anchor = by_score[0]

    def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
        return math.hypot(a["x_6677"] - b["x_6677"], a["y_6677"] - b["y_6677"])

    def near_key(a: dict[str, Any], row: dict[str, Any]) -> tuple[Any, ...]:
        return (distance(a, row), score[row["benchmark_customer_id"]], row["benchmark_customer_id"].encode())

    if structure == "CLUSTERED":
        selected = sorted(rows, key=lambda row: near_key(anchor, row))[:n]
    elif structure == "DISPERSED":
        selected = [anchor]
        selected_ids = {anchor["benchmark_customer_id"]}
        while len(selected) < n:
            best = min(
                (row for row in rows if row["benchmark_customer_id"] not in selected_ids),
                key=lambda row: (-min(distance(row, item) for item in selected), score[row["benchmark_customer_id"]], row["benchmark_customer_id"].encode()),
            )
            selected.append(best)
            selected_ids.add(best["benchmark_customer_id"])
    elif structure == "MIXED":
        second = min((row for row in rows if row is not anchor), key=lambda row: (-distance(anchor, row), score[row["benchmark_customer_id"]], row["benchmark_customer_id"].encode()))
        groups = [[anchor], [second]]
        quotas = ((n + 1) // 2, n // 2)
        selected_ids = {anchor["benchmark_customer_id"], second["benchmark_customer_id"]}
        group_index = 0
        while len(selected_ids) < n:
            if len(groups[group_index]) < quotas[group_index]:
                group_anchor = anchor if group_index == 0 else second
                chosen = min((row for row in rows if row["benchmark_customer_id"] not in selected_ids), key=lambda row: near_key(group_anchor, row))
                groups[group_index].append(chosen)
                selected_ids.add(chosen["benchmark_customer_id"])
            group_index = 1 - group_index
        selected = groups[0] + groups[1]
    else:
        raise ValueError(structure)
    return sorted(selected, key=lambda row: row["benchmark_customer_id"].encode())


class EdgeRouter:
    def __init__(self, net: Any) -> None:
        self.net = net
        self.edges = {edge.getID(): edge for edge in net.getEdges() if edge.allows(VCLASS)}
        self.edge_time: dict[str, float] = {}
        self.edge_length: dict[str, float] = {}
        self.adjacency: dict[str, list[str]] = {}
        self.transition_count = 0
        for edge_id, edge in self.edges.items():
            length = float(edge.getLength())
            speed = float(edge.getSpeed())
            if not math.isfinite(length) or not math.isfinite(speed) or length < 0 or speed <= 0:
                raise RuntimeError(f"invalid run_3 edge cost: {edge_id}")
            self.edge_length[edge_id] = length
            self.edge_time[edge_id] = length / speed
        for edge_id, edge in self.edges.items():
            targets = []
            for target, connections in edge.getOutgoing().items():
                target_id = target.getID()
                if target_id not in self.edges:
                    continue
                if any(conn.getFromLane().allows(VCLASS) and conn.getToLane().allows(VCLASS) for conn in connections):
                    targets.append(target_id)
            self.adjacency[edge_id] = sorted(set(targets))
            self.transition_count += len(self.adjacency[edge_id])

    def shortest_paths(self, source: str, targets: set[str]) -> dict[str, list[str]]:
        remaining = set(targets) - {source}
        if not remaining:
            return {}
        distances = {source: 0.0}
        previous: dict[str, str] = {}
        heap = [(0.0, source)]
        found: set[str] = set()
        while heap and found != remaining:
            cost, edge_id = heapq.heappop(heap)
            if cost > distances.get(edge_id, math.inf) + 1e-12:
                continue
            if edge_id in remaining:
                found.add(edge_id)
            for nxt in self.adjacency[edge_id]:
                candidate = cost + self.edge_time[nxt]
                old = distances.get(nxt, math.inf)
                if candidate < old - 1e-12 or (abs(candidate - old) <= 1e-12 and edge_id < previous.get(nxt, "~")):
                    distances[nxt] = candidate
                    previous[nxt] = edge_id
                    heapq.heappush(heap, (candidate, nxt))
        paths: dict[str, list[str]] = {}
        for target in sorted(found):
            path = [target]
            while path[-1] != source:
                path.append(previous[path[-1]])
            paths[target] = list(reversed(path))
        return paths

    def shortest_cycle(self, source: str) -> list[str] | None:
        distances: dict[str, float] = {}
        previous: dict[str, str] = {}
        heap: list[tuple[float, str]] = []
        for nxt in self.adjacency[source]:
            if nxt == source:
                return [source, source]
            cost = self.edge_time[nxt]
            if cost < distances.get(nxt, math.inf):
                distances[nxt] = cost
                previous[nxt] = source
                heapq.heappush(heap, (cost, nxt))
        while heap:
            cost, edge_id = heapq.heappop(heap)
            if cost > distances.get(edge_id, math.inf) + 1e-12:
                continue
            for nxt in self.adjacency[edge_id]:
                if nxt == source:
                    middle = [edge_id]
                    while previous[middle[-1]] != source:
                        middle.append(previous[middle[-1]])
                    return [source, *reversed(middle), source]
                candidate = cost + self.edge_time[nxt]
                old = distances.get(nxt, math.inf)
                if candidate < old - 1e-12 or (abs(candidate - old) <= 1e-12 and edge_id < previous.get(nxt, "~")):
                    distances[nxt] = candidate
                    previous[nxt] = edge_id
                    heapq.heappush(heap, (candidate, nxt))
        return None

    def route(self, origin: dict[str, Any], destination: dict[str, Any], path: list[str] | None) -> dict[str, Any]:
        origin_edge = origin["edge_id"]
        destination_edge = destination["edge_id"]
        origin_offset = origin["offset_m"]
        destination_offset = destination["offset_m"]
        if origin_edge not in self.edges or destination_edge not in self.edges:
            return {"reachable": False, "validation_status": "INVALID_ENDPOINT", "path": None}
        if origin_edge == destination_edge and destination_offset >= origin_offset:
            sequence = [origin_edge]
            distance = destination_offset - origin_offset
            travel = self.edge_time[origin_edge] * (distance / self.edge_length[origin_edge] if self.edge_length[origin_edge] else 0.0)
        else:
            sequence = path if path is not None else (self.shortest_cycle(origin_edge) if origin_edge == destination_edge else None)
            if not sequence:
                return {"reachable": False, "validation_status": "UNREACHABLE", "path": None}
            origin_remaining = self.edge_length[origin_edge] - origin_offset
            middle = sequence[1:-1]
            distance = origin_remaining + sum(self.edge_length[e] for e in middle) + destination_offset
            travel = (
                self.edge_time[origin_edge] * (origin_remaining / self.edge_length[origin_edge] if self.edge_length[origin_edge] else 0.0)
                + sum(self.edge_time[e] for e in middle)
                + self.edge_time[destination_edge] * (destination_offset / self.edge_length[destination_edge] if self.edge_length[destination_edge] else 0.0)
            )
        connections_valid = all(b in self.adjacency.get(a, []) for a, b in zip(sequence, sequence[1:]))
        return {
            "reachable": True,
            "distance_m": round(distance, 9),
            "travel_time_s": round(travel, 9),
            "path": sequence,
            "connections_valid": connections_valid,
            "validation_status": "PASS" if connections_valid and distance >= 0 and travel >= 0 else "FAIL",
        }


def exact_packing(customers: list[dict[str, Any]], m: int) -> tuple[str, list[list[str]], int]:
    ordered = sorted(((int(row["q_i"]), row["benchmark_customer_id"]) for row in customers), key=lambda item: (-item[0], item[1].encode()))
    if any(q <= 0 or q > Q for q, _ in ordered):
        return "INVALID_INPUT", [], 0
    bins: list[tuple[int, tuple[str, ...]]] = [(Q, ()) for _ in range(m)]
    failed: set[tuple[int, tuple[int, ...]]] = set()
    states = 0

    def search(index: int, current: list[tuple[int, tuple[str, ...]]]) -> list[tuple[int, tuple[str, ...]]] | None:
        nonlocal states
        states += 1
        if index == len(ordered):
            return current
        state = (index, tuple(remaining for remaining, _ in current))
        if state in failed:
            return None
        q, customer_id = ordered[index]
        seen_remaining: set[int] = set()
        for position, (remaining, members) in enumerate(current):
            if remaining < q or remaining in seen_remaining:
                continue
            seen_remaining.add(remaining)
            nxt = list(current)
            nxt[position] = (remaining - q, members + (customer_id,))
            nxt.sort(key=lambda item: (-item[0], item[1]))
            result = search(index + 1, nxt)
            if result is not None:
                return result
        failed.add(state)
        return None

    result = search(0, bins)
    if result is None:
        return "PACKING_INFEASIBLE", [], states
    certificate = [list(members) for _, members in sorted((item for item in result if item[1]), key=lambda item: item[1])]
    return "PACKING_FEASIBLE", certificate, states


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - position) + ordered[hi] * (position - lo)


def stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "p90": None, "max": None, "mean": None}
    return {
        "count": len(values), "min": min(values), "p25": percentile(values, 0.25), "median": percentile(values, 0.5),
        "p75": percentile(values, 0.75), "p90": percentile(values, 0.9), "max": max(values), "mean": sum(values) / len(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--execution-commit", default=None)
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    execution_commit = args.execution_commit or git("rev-parse", "HEAD")
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    code_hash = sha_file(Path(__file__))

    if sha_file(SOURCE) != SOURCE_HASH:
        raise RuntimeError("frozen source manifest hash mismatch")
    if sha_file(NETWORK) != NETWORK_HASH:
        raise RuntimeError("run_3 graph hash mismatch")
    acceptance = json.loads(NETWORK_ACCEPTANCE.read_text(encoding="utf-8"))
    if not acceptance.get("FORMAL_NETWORK_ACCEPTED") or acceptance.get("network_semantic_sha256") != NETWORK_HASH:
        raise RuntimeError("run_3 acceptance mismatch")

    source_rows = read_csv(SOURCE)
    eligible_raw = [row for row in source_rows if row["eligibility_status"] == "ELIGIBLE"]
    if len(eligible_raw) != 39930 or sum(int(row["q_i"]) for row in eligible_raw) != 81793:
        raise RuntimeError("frozen eligible population count/demand mismatch")
    ids = [row["benchmark_customer_id"] for row in eligible_raw]
    if len(set(ids)) != len(ids):
        raise RuntimeError("source customer IDs are not unique")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6677", always_xy=True)
    eligible: list[dict[str, Any]] = []
    for raw in eligible_raw:
        q_i = int(raw["q_i"])
        lon, lat = float(raw["source_longitude"]), float(raw["source_latitude"])
        x, y = transformer.transform(lon, lat)
        if raw["capacity_unit"] != CAPACITY_UNIT or not (1 <= q_i <= Q):
            raise RuntimeError(f"invalid frozen q_i: {raw['benchmark_customer_id']}")
        if not raw["routing_proxy_id"] or not raw["routing_edge_id"] or not raw["edge_offset_m"]:
            raise RuntimeError(f"missing frozen proxy: {raw['benchmark_customer_id']}")
        if raw["network_hash"] != NETWORK_HASH or raw["reachability_status"] != "ROUNDTRIP_REACHABLE":
            raise RuntimeError(f"invalid frozen routing status: {raw['benchmark_customer_id']}")
        eligible.append({**raw, "q_i": q_i, "source_longitude": lon, "source_latitude": lat, "edge_offset_m": float(raw["edge_offset_m"]), "x_6677": x, "y_6677": y})
    eligible.sort(key=lambda row: row["benchmark_customer_id"].encode())

    depot_rows = read_csv(DEPOT_SOURCE)
    if len(depot_rows) != 1 or depot_rows[0]["depot_id"] != DEPOT_ID or depot_rows[0]["mapped_sumo_edge_id"] != DEPOT_EDGE or depot_rows[0]["network_hash"] != NETWORK_HASH:
        raise RuntimeError("DEP_006 authority mismatch")
    depot = {"id": DEPOT_ID, "edge_id": DEPOT_EDGE, "offset_m": float(depot_rows[0]["edge_offset_m"]), "proxy_id": f"RUN3_EDGE_OFFSET:{DEPOT_EDGE}:{float(depot_rows[0]['edge_offset_m']):.6f}", "q_i": 0}

    seeds: list[dict[str, Any]] = []
    bases: list[dict[str, Any]] = []
    for n in RANDOM_NS:
        for rep in range(1, 11):
            seed = seed_record("RND", n, rep)
            seeds.append({"instance_id": f"R24-RND-N{n:03d}-R{rep:02d}", "suite": "RND", "structure": "", "n": n, "repetition": rep, **seed})
            bases.append({"instance_id": f"R24-RND-N{n:03d}-R{rep:02d}", "suite": "RND", "structure": None, "n": n, "repetition": rep, "sampling_method": "HASH_RANKED_SRSWOR", "customers": select_random(eligible, seed, n), **seed, "anchor_source_base_instance_id": None})
    for structure in STRUCTURES:
        for n in STRUCTURAL_NS:
            for rep in range(1, 4):
                seed = seed_record("STR", n, rep, structure)
                instance_id = f"R24-STR-{structure}-N{n:03d}-R{rep:02d}"
                seeds.append({"instance_id": instance_id, "suite": "STR", "structure": structure, "n": n, "repetition": rep, **seed})
                bases.append({"instance_id": instance_id, "suite": "STR", "structure": structure, "n": n, "repetition": rep, "sampling_method": structure, "customers": select_structural(eligible, seed, n, structure), **seed, "anchor_source_base_instance_id": None})

    net = readNet(str(NETWORK), withInternal=False, withPrograms=False)
    router = EdgeRouter(net)
    if DEPOT_EDGE not in router.edges:
        raise RuntimeError("DEP_006 edge absent from delivery graph")

    required: dict[str, set[str]] = defaultdict(set)
    for base in bases:
        endpoints = [depot] + [{"id": row["benchmark_customer_id"], "edge_id": row["routing_edge_id"], "offset_m": row["edge_offset_m"], "proxy_id": row["routing_proxy_id"], "q_i": row["q_i"]} for row in base["customers"]]
        for origin in endpoints:
            required[origin["edge_id"]].update(destination["edge_id"] for destination in endpoints if destination["id"] != origin["id"] and destination["edge_id"] != origin["edge_id"])
    path_cache: dict[tuple[str, str], list[str]] = {}
    for index, source_edge in enumerate(sorted(required), 1):
        for target_edge, path in router.shortest_paths(source_edge, required[source_edge]).items():
            path_cache[(source_edge, target_edge)] = path
        if index % 100 == 0:
            print(f"routed source edges: {index}/{len(required)}", flush=True)

    od_by_base: dict[str, list[dict[str, Any]]] = {}
    base_records: list[dict[str, Any]] = []
    condition_by_base: dict[str, list[dict[str, Any]]] = {}
    rejection_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []

    for base_index, base in enumerate(bases, 1):
        customers = base["customers"]
        hard_reasons: set[str] = set()
        customer_ids = [row["benchmark_customer_id"] for row in customers]
        if len(customers) != base["n"] or len(set(customer_ids)) != base["n"]:
            hard_reasons.add("N_OR_SELECTION_RULE_MISMATCH" if len(customers) != base["n"] else "CUSTOMER_ID_NOT_UNIQUE")
        endpoints = [depot] + [{"id": row["benchmark_customer_id"], "edge_id": row["routing_edge_id"], "offset_m": row["edge_offset_m"], "proxy_id": row["routing_proxy_id"], "q_i": row["q_i"]} for row in customers]
        for row in customers:
            edge = router.edges.get(row["routing_edge_id"])
            if edge is None or not (0 <= row["edge_offset_m"] <= float(edge.getLength()) + 1e-8):
                hard_reasons.add("ROUTING_PROXY_MISSING_OR_INVALID")
            elif edge.getFromNode().getID() != row["edge_from_node"] or edge.getToNode().getID() != row["edge_to_node"]:
                hard_reasons.add("EDGE_SEQUENCE_OR_ENDPOINT_SEMANTICS_INVALID")
        od_rows: list[dict[str, Any]] = []
        for origin in sorted(endpoints, key=lambda item: item["id"].encode()):
            for destination in sorted(endpoints, key=lambda item: item["id"].encode()):
                if origin["id"] == destination["id"]:
                    continue
                path = path_cache.get((origin["edge_id"], destination["edge_id"]))
                result = router.route(origin, destination, path)
                same_proxy = origin["proxy_id"] == destination["proxy_id"]
                zero_distance = result.get("distance_m") == 0
                zero_time = result.get("travel_time_s") == 0
                if not result["reachable"]:
                    hard_reasons.add("ORDERED_PAIR_UNREACHABLE" if result["validation_status"] == "UNREACHABLE" else "RUN3_OD_COMPUTATION_FAILURE")
                elif result["validation_status"] != "PASS":
                    hard_reasons.add("SUMO_CONNECTION_OR_TURN_INVALID")
                elif (zero_distance or zero_time) and not same_proxy:
                    hard_reasons.add("OD_VALUE_MISSING_NONFINITE_OR_NEGATIVE")
                sequence = result.get("path")
                od_rows.append({
                    "instance_id": base["instance_id"], "origin_id": origin["id"], "destination_id": destination["id"],
                    "reachable": result["reachable"], "distance_m": result.get("distance_m"), "travel_time_s": result.get("travel_time_s"),
                    "origin_edge_id": origin["edge_id"], "origin_offset_m": round(origin["offset_m"], 9),
                    "destination_edge_id": destination["edge_id"], "destination_offset_m": round(destination["offset_m"], 9),
                    "edge_sequence": sequence, "edge_sequence_sha256": sha_bytes(canonical_bytes(sequence)) if sequence else "",
                    "connection_validation_status": "PASS" if result.get("connections_valid", len(sequence or []) <= 1) else "FAIL",
                    "duplicate_proxy_arc_flag": same_proxy, "zero_distance_flag": zero_distance, "zero_travel_time_flag": zero_time,
                    "zero_proxy_arc_flag": bool(same_proxy and zero_distance and zero_time), "validation_status": result["validation_status"],
                })
        if len(od_rows) != (base["n"] + 1) * base["n"] or len({(row["origin_id"], row["destination_id"]) for row in od_rows}) != len(od_rows):
            hard_reasons.add("ORDERED_PAIR_MISSING_OR_DUPLICATED")
        od_core = [{k: v for k, v in row.items() if k != "instance_id"} for row in od_rows]
        od_hash = sha_bytes(canonical_bytes(od_core))
        od_validation_hash = sha_bytes(canonical_bytes([{"origin_id": row["origin_id"], "destination_id": row["destination_id"], "validation_status": row["validation_status"]} for row in od_rows]))
        od_by_base[base["instance_id"]] = od_rows

        proxy_groups: dict[str, list[str]] = defaultdict(list)
        for row in customers:
            proxy_groups[row["routing_proxy_id"]].append(row["benchmark_customer_id"])
        shared = {key: sorted(value) for key, value in proxy_groups.items() if len(value) > 1}
        duplicate_count = sum(len(value) for value in shared.values())
        population_shared_count = sum(str(row["duplicate_proxy_flag"]).lower() == "true" for row in customers)
        zero_coordinate_pairs = sum(1 for a in customers for b in customers if a["benchmark_customer_id"] != b["benchmark_customer_id"] and a["source_longitude"] == b["source_longitude"] and a["source_latitude"] == b["source_latitude"])
        zero_distance_count = sum(bool(row["zero_distance_flag"]) for row in od_rows)
        zero_time_count = sum(bool(row["zero_travel_time_flag"]) for row in od_rows)
        duplicate_rows.append({"instance_id": base["instance_id"], "suite": base["suite"], "structure": base["structure"] or "", "n": base["n"], "population_shared_proxy_selected_customer_count": population_shared_count, "instance_duplicate_proxy_customer_count": duplicate_count, "instance_duplicate_proxy_group_count": len(shared), "duplicate_proxy_groups": json.dumps(shared, ensure_ascii=False, sort_keys=True, separators=(",", ":")), "zero_coordinate_ordered_pair_count": zero_coordinate_pairs, "zero_distance_ordered_arc_count": zero_distance_count, "zero_travel_time_ordered_arc_count": zero_time_count})

        D = sum(row["q_i"] for row in customers)
        q_vector = [{"customer_id": row["benchmark_customer_id"], "q_i": row["q_i"]} for row in customers]
        q_hash = sha_bytes(canonical_bytes(q_vector))
        customer_hash = sha_bytes(canonical_bytes(customer_ids))
        base_status = "HARD_REJECTED" if hard_reasons else "VALID"
        base_record = {
            "protocol_id": PROTOCOL_ID, "protocol_version": PROTOCOL_VERSION, "instance_id": base["instance_id"], "suite": base["suite"], "structure": base["structure"],
            "n": base["n"], "repetition": base["repetition"], "seed_material": base["seed_material"], "seed_digest_sha256": base["seed_digest_sha256"], "seed_uint64": base["seed_uint64"],
            "sampling_method": base["sampling_method"], "customer_ids": customer_ids, "customer_ids_sha256": customer_hash, "anchor_source_base_instance_id": None,
            "depot_id": DEPOT_ID, "graph_id": GRAPH_ID, "graph_sha256": NETWORK_HASH, "source_c_eligible_path": str(SOURCE.relative_to(ROOT)), "source_c_eligible_sha256": SOURCE_HASH,
            "source_customer_count": 39930, "source_total_demand": 81793, "capacity_unit": CAPACITY_UNIT, "total_demand_D": D,
            "q_i_by_customer": q_vector, "q_i_vector_sha256": q_hash, "duplicate_proxy_customer_count": duplicate_count, "duplicate_proxy_group_count": len(shared), "duplicate_proxy_groups": shared,
            "zero_distance_ordered_arc_count": zero_distance_count, "zero_travel_time_ordered_arc_count": zero_time_count, "od_record_count": len(od_rows), "od_matrix_sha256": od_hash, "od_validation_sha256": od_validation_hash,
            "selection_validation_status": "PASS" if not ({"CUSTOMER_ID_NOT_UNIQUE", "N_OR_SELECTION_RULE_MISMATCH"} & hard_reasons) else "FAIL",
            "routing_validation_status": "PASS" if not hard_reasons else "FAIL", "base_status": base_status, "hard_rejection_reasons": sorted(hard_reasons),
            "created_at_utc": created_at, "generator_code_sha": code_hash, "git_commit_sha": execution_commit,
        }
        base_record["output_sha256"] = content_hash(base_record)
        base_records.append(base_record)
        if hard_reasons:
            for reason in sorted(hard_reasons):
                rejection_rows.append({"instance_id": base["instance_id"], "level": "BASE", "reason": reason, "no_redraw": True})

        conditions: list[dict[str, Any]] = []
        m_by_target: dict[str, int] = {}
        for label, target, suffix in RHOS:
            target_float = float(target)
            m = math.ceil(D / (target_float * Q))
            m_by_target[target] = m
            if base_status == "VALID":
                packing, certificate, states = exact_packing(customers, m)
            else:
                packing, certificate, states = "NOT_RUN_BASE_HARD_REJECTED", [], 0
            certificate_hash = sha_bytes(canonical_bytes(certificate)) if certificate else ""
            condition = {
                "condition_id": f"{base['instance_id']}-{suffix}", "base_instance_id": base["instance_id"], "regime_label": label, "target_rho": target,
                "Q": Q, "capacity_unit": CAPACITY_UNIT, "m": m, "actual_rho": format(D / (m * Q), ".17g"), "total_demand_D": D,
                "necessary_capacity_check": m * Q >= D, "packing_preflight_algorithm": PACKING_ALGORITHM, "packing_feasibility": packing,
                "packing_certificate": certificate, "packing_certificate_sha256": certificate_hash, "packing_states_examined": states,
                "degenerate_regime_flag": False, "degenerate_regime_group_id": None, "condition_status": "READY" if packing == "PACKING_FEASIBLE" else packing,
                "hard_condition_reasons": [] if packing == "PACKING_FEASIBLE" else (["CAPACITY_PACKING_INFEASIBLE"] if packing == "PACKING_INFEASIBLE" else ["BASE_HARD_REJECTED"]),
                "base_output_sha256": base_record["output_sha256"], "generator_code_sha": code_hash,
            }
            conditions.append(condition)
        groups: dict[int, list[str]] = defaultdict(list)
        for target, m in m_by_target.items():
            groups[m].append(target)
        for condition in conditions:
            targets = sorted(groups[condition["m"]])
            if len(targets) > 1:
                condition["degenerate_regime_flag"] = True
                condition["degenerate_regime_group_id"] = f"M{condition['m']:03d}-" + "-".join(target.replace(".", "") for target in targets)
                if condition["condition_status"] == "READY":
                    condition["condition_status"] = "DEGENERATE_REGIME_SAME_M"
            condition["output_sha256"] = content_hash(condition)
        condition_by_base[base["instance_id"]] = conditions
        if base_index % 20 == 0:
            print(f"validated bases: {base_index}/{len(bases)}", flush=True)

    # Fixed anchors are aliases, never new selections or routing computations.
    for n in STRUCTURAL_NS:
        source_id = f"R24-RND-N{n:03d}-R01"
        source_record = next(record for record in base_records if record["instance_id"] == source_id)
        anchor_id = f"R24-ANCHOR-N{n:03d}"
        anchor_record = {**source_record, "instance_id": anchor_id, "suite": "ANCHOR", "structure": None, "repetition": None, "sampling_method": "ANCHOR_ALIAS", "anchor_source_base_instance_id": source_id}
        anchor_record["output_sha256"] = content_hash(anchor_record)
        base_records.append(anchor_record)
        anchor_od = [{**row, "instance_id": anchor_id} for row in od_by_base[source_id]]
        od_by_base[anchor_id] = anchor_od
        anchor_conditions = []
        for source_condition in condition_by_base[source_id]:
            suffix = source_condition["condition_id"].rsplit("-", 1)[1]
            condition = {**source_condition, "condition_id": f"{anchor_id}-{suffix}", "base_instance_id": anchor_id, "base_output_sha256": anchor_record["output_sha256"], "anchor_source_condition_id": source_condition["condition_id"]}
            condition["output_sha256"] = content_hash(condition)
            anchor_conditions.append(condition)
        condition_by_base[anchor_id] = anchor_conditions
        source_duplicate = next(row for row in duplicate_rows if row["instance_id"] == source_id)
        duplicate_rows.append({**source_duplicate, "instance_id": anchor_id, "suite": "ANCHOR"})
        for reason in anchor_record["hard_rejection_reasons"]:
            rejection_rows.append({"instance_id": anchor_id, "level": "BASE", "reason": reason, "no_redraw": True})

    base_records.sort(key=lambda record: record["instance_id"])
    all_conditions = sorted((condition for instance_id in sorted(condition_by_base) for condition in condition_by_base[instance_id]), key=lambda row: row["condition_id"])
    all_od = sorted((row for instance_id in sorted(od_by_base) for row in od_by_base[instance_id]), key=lambda row: (row["instance_id"], row["origin_id"], row["destination_id"]))

    # Individual instance artifacts.
    for base_record in base_records:
        instance_dir = output / "instances" / base_record["instance_id"]
        write_json(instance_dir / "base_instance.json", base_record)
        instance_od = od_by_base[base_record["instance_id"]]
        od_serial = [{**row, "edge_sequence": json.dumps(row["edge_sequence"], separators=(",", ":")) if row["edge_sequence"] is not None else ""} for row in instance_od]
        write_csv(instance_dir / "od_manifest.csv", list(od_serial[0]), od_serial)
        write_json(instance_dir / "capacity_conditions.json", condition_by_base[base_record["instance_id"]])

    base_fields = [
        "instance_id", "suite", "structure", "n", "repetition", "seed_material", "seed_digest_sha256", "seed_uint64", "sampling_method", "customer_ids", "customer_ids_sha256",
        "anchor_source_base_instance_id", "depot_id", "graph_id", "graph_sha256", "source_c_eligible_sha256", "total_demand_D", "q_i_vector_sha256", "duplicate_proxy_customer_count",
        "duplicate_proxy_group_count", "zero_distance_ordered_arc_count", "zero_travel_time_ordered_arc_count", "od_record_count", "od_matrix_sha256", "od_validation_sha256",
        "selection_validation_status", "routing_validation_status", "base_status", "hard_rejection_reasons", "generator_code_sha", "git_commit_sha", "output_sha256",
    ]
    base_csv = []
    for record in base_records:
        row = {**record, "customer_ids": json.dumps(record["customer_ids"], ensure_ascii=False, separators=(",", ":")), "hard_rejection_reasons": json.dumps(record["hard_rejection_reasons"], separators=(",", ":"))}
        base_csv.append(row)
    write_csv(output / "BASE_INSTANCE_MANIFEST.csv", base_fields, base_csv)

    condition_fields = [
        "condition_id", "base_instance_id", "regime_label", "target_rho", "Q", "capacity_unit", "m", "actual_rho", "total_demand_D", "necessary_capacity_check",
        "packing_preflight_algorithm", "packing_feasibility", "packing_certificate_sha256", "packing_states_examined", "degenerate_regime_flag", "degenerate_regime_group_id",
        "condition_status", "hard_condition_reasons", "base_output_sha256", "generator_code_sha", "output_sha256", "anchor_source_condition_id",
    ]
    condition_csv = [{**row, "hard_condition_reasons": json.dumps(row["hard_condition_reasons"], separators=(",", ":"))} for row in all_conditions]
    write_csv(output / "CAPACITY_CONDITION_MANIFEST.csv", condition_fields, condition_csv)
    od_fields = ["instance_id", "origin_id", "destination_id", "reachable", "distance_m", "travel_time_s", "origin_edge_id", "origin_offset_m", "destination_edge_id", "destination_offset_m", "edge_sequence", "edge_sequence_sha256", "connection_validation_status", "duplicate_proxy_arc_flag", "zero_distance_flag", "zero_travel_time_flag", "zero_proxy_arc_flag", "validation_status", "path_reference"]
    od_csv = []
    for row in all_od:
        path_ref = f"instances/{row['instance_id']}/od_manifest.csv"
        od_csv.append({**row, "edge_sequence": json.dumps(row["edge_sequence"], separators=(",", ":")) if row["edge_sequence"] is not None else "", "path_reference": path_ref})
    write_csv(output / "OD_MANIFEST.csv", od_fields, od_csv)
    write_csv(output / "SEED_MANIFEST.csv", ["instance_id", "suite", "structure", "n", "repetition", "seed_material", "seed_digest_sha256", "seed_uint64"], sorted(seeds, key=lambda row: row["instance_id"]))
    duplicate_fields = list(duplicate_rows[0])
    write_csv(output / "DUPLICATE_PROXY_SUMMARY.csv", duplicate_fields, sorted(duplicate_rows, key=lambda row: row["instance_id"]))
    write_csv(output / "INSTANCE_REJECTION_LOG.csv", ["instance_id", "level", "reason", "no_redraw"], sorted(rejection_rows, key=lambda row: (row["instance_id"], row["reason"])))

    def suite_summary(suite: str) -> list[dict[str, Any]]:
        selected = [row for row in base_records if row["suite"] == suite]
        keys = sorted({(row["structure"] or "ALL", row["n"]) for row in selected})
        return [{"suite": suite, "structure": structure, "n": n, "expected": sum(1 for row in selected if (row["structure"] or "ALL", row["n"]) == (structure, n)), "generated": sum(1 for row in selected if (row["structure"] or "ALL", row["n"]) == (structure, n)), "valid": sum(row["base_status"] == "VALID" for row in selected if (row["structure"] or "ALL", row["n"]) == (structure, n)), "rejected": sum(row["base_status"] != "VALID" for row in selected if (row["structure"] or "ALL", row["n"]) == (structure, n))} for structure, n in keys]

    random_summary = suite_summary("RND")
    structural_summary = suite_summary("STR")
    write_csv(output / "RANDOM_SUITE_SUMMARY.csv", list(random_summary[0]), random_summary)
    write_csv(output / "STRUCTURAL_SUITE_SUMMARY.csv", list(structural_summary[0]), structural_summary)
    anchor_rows = [{"instance_id": row["instance_id"], "source_base_instance_id": row["anchor_source_base_instance_id"], "n": row["n"], "source_status": next(item["base_status"] for item in base_records if item["instance_id"] == row["anchor_source_base_instance_id"]), "anchor_status": row["base_status"], "customer_ids_sha256": row["customer_ids_sha256"], "od_matrix_sha256": row["od_matrix_sha256"]} for row in base_records if row["suite"] == "ANCHOR"]
    write_csv(output / "ANCHOR_SUITE_SUMMARY.csv", list(anchor_rows[0]), anchor_rows)

    packing_groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for condition in all_conditions:
        base = next(row for row in base_records if row["instance_id"] == condition["base_instance_id"])
        packing_groups[(condition["target_rho"], base["n"])].append(condition)
    packing_summary = []
    for (rho, n), group in sorted(packing_groups.items()):
        packing_summary.append({"target_rho": rho, "n": n, "conditions": len(group), "packing_feasible": sum(row["packing_feasibility"] == "PACKING_FEASIBLE" for row in group), "packing_infeasible": sum(row["packing_feasibility"] == "PACKING_INFEASIBLE" for row in group), "degenerate": sum(bool(row["degenerate_regime_flag"]) for row in group), "ready_nondegenerate": sum(row["condition_status"] == "READY" for row in group)})
    write_csv(output / "PACKING_PREFLIGHT_SUMMARY.csv", list(packing_summary[0]), packing_summary)

    unique_base_ids = {row["instance_id"] for row in base_records if row["suite"] != "ANCHOR"}
    unique_od = [row for row in all_od if row["instance_id"] in unique_base_ids]
    distribution = {
        "q_i_selected_occurrences": stats([float(item["q_i"]) for row in base_records if row["suite"] != "ANCHOR" for item in row["q_i_by_customer"]]),
        "D_by_n": {str(n): stats([float(row["total_demand_D"]) for row in base_records if row["suite"] != "ANCHOR" and row["n"] == n]) for n in sorted({row["n"] for row in base_records})},
        "m_by_rho_and_n": {f"rho={rho}|n={n}": stats([float(row["m"]) for row in group]) for (rho, n), group in sorted(packing_groups.items())},
        "actual_rho": stats([float(row["actual_rho"]) for row in all_conditions]),
        "travel_distance_m": stats([float(row["distance_m"]) for row in unique_od if row["reachable"]]),
        "travel_time_s": stats([float(row["travel_time_s"]) for row in unique_od if row["reachable"]]),
        "duplicate_proxy_instance_frequency": sum(row["instance_duplicate_proxy_group_count"] > 0 for row in duplicate_rows if row["suite"] != "ANCHOR") / len(unique_base_ids),
        "zero_distance_ordered_arcs_unique_bases": sum(bool(row["zero_distance_flag"]) for row in unique_od),
        "zero_travel_time_ordered_arcs_unique_bases": sum(bool(row["zero_travel_time_flag"]) for row in unique_od),
        "packing_feasibility_rate": sum(row["packing_feasibility"] == "PACKING_FEASIBLE" for row in all_conditions) / len(all_conditions),
    }
    write_json(output / "DISTRIBUTION_SUMMARY.json", distribution)

    def readiness(n_values: set[int]) -> dict[str, Any]:
        selected_bases = [row for row in base_records if row["suite"] == "RND" and row["n"] in n_values]
        selected_ids = {row["instance_id"] for row in selected_bases}
        selected_conditions = [row for row in all_conditions if row["base_instance_id"] in selected_ids]
        return {
            "base_instances": len(selected_bases), "valid": sum(row["base_status"] == "VALID" for row in selected_bases),
            "all_od_ready": sum(row["routing_validation_status"] == "PASS" for row in selected_bases), "capacity_conditions": len(selected_conditions),
            "packing_feasible": sum(row["packing_feasibility"] == "PACKING_FEASIBLE" for row in selected_conditions),
            "packing_infeasible": sum(row["packing_feasibility"] == "PACKING_INFEASIBLE" for row in selected_conditions),
            "nondegenerate_ready": sum(row["condition_status"] == "READY" for row in selected_conditions),
            "degenerate": sum(bool(row["degenerate_regime_flag"]) for row in selected_conditions),
        }

    quantum = readiness({2, 3, 4})
    classical = readiness({5, 8, 10, 15, 20})
    (output / "QUANTUM_COMPARABLE_READINESS.md").write_text(f"# Quantum-comparable readiness\n\nScope: primary n={{2,3,4}}. This is input readiness, not QUBO/QAOA authorization.\n\n```json\n{json.dumps(quantum, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")
    (output / "CLASSICAL_EXTENSION_READINESS.md").write_text(f"# Classical-extension readiness\n\nScope: primary n={{5,8,10,15,20}}. No MILP or optimization was run.\n\n```json\n{json.dumps(classical, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")

    suite_counts = {
        "random": {"expected": 80, "generated": sum(row["suite"] == "RND" for row in base_records), "valid": sum(row["suite"] == "RND" and row["base_status"] == "VALID" for row in base_records), "rejected": sum(row["suite"] == "RND" and row["base_status"] != "VALID" for row in base_records)},
        "structural": {"expected": 27, "generated": sum(row["suite"] == "STR" for row in base_records), "valid": sum(row["suite"] == "STR" and row["base_status"] == "VALID" for row in base_records), "rejected": sum(row["suite"] == "STR" and row["base_status"] != "VALID" for row in base_records)},
        "anchor": {"expected": 3, "generated": sum(row["suite"] == "ANCHOR" for row in base_records), "valid": sum(row["suite"] == "ANCHOR" and row["base_status"] == "VALID" for row in base_records), "rejected": sum(row["suite"] == "ANCHOR" and row["base_status"] != "VALID" for row in base_records)},
    }
    condition_counts = Counter(row["condition_status"] for row in all_conditions)
    routing_failures = sum(row["validation_status"] != "PASS" for row in all_od)
    verdict = "R24_INSTANCE_SUITE_GENERATED_WITH_LIMITATIONS" if not rejection_rows and routing_failures == 0 else "R24_INSTANCE_SUITE_PARTIALLY_GENERATED"
    next_task = "implement and validate classical R24 CVRP reference solver"
    suite_manifest = {
        "protocol_id": PROTOCOL_ID, "execution_verdict": verdict, "next_executable_task": next_task, "created_at_utc": created_at,
        "branch": git("branch", "--show-current"), "repository_start_sha": START_SHA, "execution_commit_sha": execution_commit, "generator_code_sha": code_hash,
        "source_c_eligible_sha256": SOURCE_HASH, "source_customer_count": 39930, "source_total_demand": 81793, "graph_sha256": NETWORK_HASH,
        "suite_counts": suite_counts, "total_base_records_including_anchor_aliases": len(base_records), "independently_generated_base_instances": len(unique_base_ids),
        "total_capacity_conditions": len(all_conditions), "condition_status_counts": dict(sorted(condition_counts.items())), "routing_validation_failures": routing_failures,
        "rejection_reason_counts": dict(sorted(Counter(row["reason"] for row in rejection_rows).items())), "quantum_comparable_readiness": quantum, "classical_extension_readiness": classical,
        "demand_generation": "NONE", "routing_graph_regeneration": "NONE", "optimization": "NONE", "specification_deviations": "NONE",
        "python": sys.version, "platform": platform.platform(), "pyproj": __import__("pyproj").__version__, "sumo": "1.24.0 bundled sumolib",
    }
    write_json(output / "SUITE_MANIFEST.json", suite_manifest)

    report = f"""# R24 Benchmark Instance Suite Report

Execution verdict: **`{verdict}`**

Specification: `{PROTOCOL_ID}` at commit `44f7960abefe4df9648dd00b738885a14813ba54`<br>
Execution commit: `{execution_commit}`<br>
Generated at: `{created_at}`

## Results

| Suite | Expected | Generated | Valid | Rejected |
|---|---:|---:|---:|---:|
| Random | 80 | {suite_counts['random']['generated']} | {suite_counts['random']['valid']} | {suite_counts['random']['rejected']} |
| Structural | 27 | {suite_counts['structural']['generated']} | {suite_counts['structural']['valid']} | {suite_counts['structural']['rejected']} |
| Anchor aliases | 3 | {suite_counts['anchor']['generated']} | {suite_counts['anchor']['valid']} | {suite_counts['anchor']['rejected']} |

- Independently generated bases: {len(unique_base_ids)}; manifest base records including aliases: {len(base_records)}.
- Capacity conditions: {len(all_conditions)}; statuses: `{json.dumps(dict(sorted(condition_counts.items())), sort_keys=True)}`.
- Packing infeasible: {sum(row['packing_feasibility'] == 'PACKING_INFEASIBLE' for row in all_conditions)}.
- Degenerate conditions: {sum(bool(row['degenerate_regime_flag']) for row in all_conditions)}.
- Routing validation failures: {routing_failures}.
- Hard rejection reasons: `{json.dumps(dict(sorted(Counter(row['reason'] for row in rejection_rows).items())), sort_keys=True)}`.
- Instance-level duplicate-proxy occurrence among 107 independent bases: {sum(row['instance_duplicate_proxy_group_count'] > 0 for row in duplicate_rows if row['suite'] != 'ANCHOR')}.
- Zero-distance/time ordered arcs among independent bases: {distribution['zero_distance_ordered_arcs_unique_bases']} / {distribution['zero_travel_time_ordered_arcs_unique_bases']}.

## Fixed inputs and controls

- `C_eligible`: 39,930; demand 81,793; SHA-256 `{SOURCE_HASH}`.
- run_3 graph SHA-256: `{NETWORK_HASH}`; depot `DEP_006`.
- `Q=14`; target rho `{{0.50,0.70,0.90}}`; `m=ceil(D/(rho*Q))`.
- No redraw, seed change, resampling, graph rebuild, demand generation, or optimization occurred.
- Specification deviations: `NONE`.

## Claim boundary

The suite consists of Ota-grounded repeated-random and controlled structural subsets of the frozen synthetic eligible benchmark population. It is not an observed or statistically representative sample of real Ota carrier routes, deliveries, fleets, or dispatches.

`NEXT_EXECUTABLE_TASK = {next_task}`
"""
    (output / "R24_BENCHMARK_INSTANCE_SUITE_REPORT.md").write_text(report, encoding="utf-8")
    provenance = f"""# Provenance

- Protocol: `{PROTOCOL_ID}`
- Branch: `{git('branch', '--show-current')}`
- Repository start SHA: `{START_SHA}`
- Execution/code commit SHA: `{execution_commit}`
- Generator code SHA-256: `{code_hash}`
- Source eligible SHA-256: `{SOURCE_HASH}`
- run_3 graph SHA-256: `{NETWORK_HASH}`
- DEP_006 source SHA-256: `{sha_file(DEPOT_SOURCE)}`
- Generated at: `{created_at}`
- Demand generation: `NONE`
- Routing graph regeneration: `NONE`
- Optimization: `NONE`
- Specification deviations: `NONE`

Customer selection used only the frozen seed/hash or structural rules. Routing used the accepted run_3 external-edge connection graph for SUMO class `delivery`, minimizing model/free-flow travel time with endpoint partial-edge costs. Capacity packing used `{PACKING_ALGORITHM}` and is not route optimization. Output hashes below cover every generated artifact except `SHA256SUMS.txt` itself.
"""
    (output / "PROVENANCE.md").write_text(provenance, encoding="utf-8")

    # Final hashes cover all generated files other than the checksum file itself.
    checksum_path = output / "SHA256SUMS.txt"
    if checksum_path.exists():
        checksum_path.unlink()
    checksum_lines = []
    for path in sorted((path for path in output.rglob("*") if path.is_file() and path != checksum_path), key=lambda path: str(path.relative_to(output))):
        checksum_lines.append(f"{sha_file(path)}  {path.relative_to(output)}")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(suite_manifest, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
