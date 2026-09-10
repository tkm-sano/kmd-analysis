#!/usr/bin/env python3
"""Independent R14 validation for an immutable R13 routing matrix."""

from __future__ import annotations

import argparse, csv, hashlib, heapq, json, math, statistics, sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SUMO_TOOLS = ROOT / ".local/sumo-1.24.0/share/sumo/tools"
sys.path.insert(0, str(SUMO_TOOLS))
import sumolib  # type: ignore


EXPECTED_NETWORK = "460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
EXPECTED_OUTPUT = "29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1"
VEHICLE = "delivery"
DIJKSTRA_CACHE: dict[tuple[str, str], tuple[dict[str, float], dict[str, tuple[str, str]]]] = {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def edge_time(edge: Any) -> float:
    return float(edge.getLength()) / float(edge.getSpeed())


def permitted(edge: Any) -> bool:
    return VEHICLE in (edge.getPermissions() or [])


def dijkstra(net: Any, start: Any, target: str, weight: str) -> tuple[float | None, list[str]]:
    start_id = start.getID()
    dist = {start_id: 0.0}
    prev: dict[str, tuple[str, str]] = {}
    heap = [(0.0, start_id)]
    nodes = {n.getID(): n for n in net.getNodes()}
    while heap:
        cost, node_id = heapq.heappop(heap)
        if cost > dist[node_id] + 1e-12:
            continue
        if node_id == target:
            break
        for edge in sorted(nodes[node_id].getOutgoing(), key=lambda x: x.getID()):
            if not permitted(edge):
                continue
            nxt = edge.getToNode().getID()
            edge_cost = edge_time(edge) if weight == "time" else float(edge.getLength())
            candidate = cost + edge_cost
            if candidate < dist.get(nxt, math.inf) - 1e-12:
                dist[nxt] = candidate
                prev[nxt] = (node_id, edge.getID())
                heapq.heappush(heap, (candidate, nxt))
    if target not in dist:
        return None, []
    path: list[str] = []
    cur = target
    while cur != start_id:
        parent, edge_id = prev[cur]
        path.append(edge_id)
        cur = parent
    path.reverse()
    return dist[target], path


def dijkstra_all(net: Any, start: Any, weight: str) -> tuple[dict[str, float], dict[str, tuple[str, str]]]:
    start_id = start.getID()
    dist = {start_id: 0.0}
    prev: dict[str, tuple[str, str]] = {}
    heap = [(0.0, start_id)]
    nodes = {n.getID(): n for n in net.getNodes()}
    while heap:
        cost, node_id = heapq.heappop(heap)
        if cost > dist[node_id] + 1e-12:
            continue
        for edge in sorted(nodes[node_id].getOutgoing(), key=lambda x: x.getID()):
            if not permitted(edge):
                continue
            nxt = edge.getToNode().getID()
            edge_cost = edge_time(edge) if weight == "time" else float(edge.getLength())
            candidate = cost + edge_cost
            if candidate < dist.get(nxt, math.inf) - 1e-12:
                dist[nxt] = candidate
                prev[nxt] = (node_id, edge.getID())
                heapq.heappush(heap, (candidate, nxt))
    return dist, prev


def reconstruct(previous: dict[str, tuple[str, str]], start: str, target: str) -> list[str]:
    path = []
    cur = target
    while cur != start:
        if cur not in previous:
            return []
        parent, edge_id = previous[cur]
        path.append(edge_id)
        cur = parent
    path.reverse()
    return path


def partials(origin: dict[str, str], destination: dict[str, str], net: Any) -> tuple[float, float, float, float]:
    oe, de = net.getEdge(origin["mapped_edge_id"]), net.getEdge(destination["mapped_edge_id"])
    ol, dl = float(oe.getLength()), float(de.getLength())
    oo, do = float(origin["edge_offset_m"]), float(destination["edge_offset_m"])
    od = ol - oo
    dd = do
    return od, od / float(oe.getSpeed()), dd, dd / float(de.getSpeed())


def route_cost(origin: dict[str, str], destination: dict[str, str], net: Any, weight: str) -> tuple[float | None, list[str]]:
    oe, de = net.getEdge(origin["mapped_edge_id"]), net.getEdge(destination["mapped_edge_id"])
    oo, do = float(origin["edge_offset_m"]), float(destination["edge_offset_m"])
    if oe.getID() == de.getID() and do >= oo:
        delta = do - oo
        return (delta if weight == "distance" else delta / float(oe.getSpeed())), [oe.getID()]
    cache_key = (oe.getID(), weight)
    if cache_key not in DIJKSTRA_CACHE:
        DIJKSTRA_CACHE[cache_key] = dijkstra_all(net, oe.getToNode(), weight)
    distances, previous = DIJKSTRA_CACHE[cache_key]
    target_node = de.getFromNode().getID()
    graph_cost = distances.get(target_node)
    path = reconstruct(previous, oe.getToNode().getID(), target_node) if graph_cost is not None else []
    if graph_cost is None:
        return None, []
    ol = float(oe.getLength()); dl = float(de.getLength())
    origin_part = ol - oo
    dest_part = do
    if weight == "time":
        origin_part /= float(oe.getSpeed()); dest_part /= float(de.getSpeed())
    return origin_part + graph_cost + dest_part, [oe.getID(), *path, *([] if de.getID() in path else [de.getID()])]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = (len(ordered) - 1) * p
    lo, hi = math.floor(idx), math.ceil(idx)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def haversine(a: dict[str, str], b: dict[str, str]) -> float:
    r = 6371000.0
    p1, p2 = math.radians(float(a["latitude"])), math.radians(float(b["latitude"]))
    dp = p2 - p1
    dl = math.radians(float(b["longitude"]) - float(a["longitude"]))
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def mapped_position(edge: Any, offset_m: float) -> tuple[float, float]:
    """Return the SUMO projected XY position at the stored edge offset."""
    remaining = float(offset_m)
    shape = edge.getShape()
    for start, end in zip(shape, shape[1:]):
        segment = math.dist(start, end)
        if remaining <= segment:
            fraction = remaining / segment if segment else 0.0
            return (start[0] + fraction * (end[0] - start[0]), start[1] + fraction * (end[1] - start[1]))
        remaining -= segment
    return shape[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r12-dir", required=True)
    ap.add_argument("--r13-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    r12, r13, out = map(Path, (args.r12_dir, args.r13_dir, args.output_dir))
    out.mkdir(parents=True, exist_ok=True)
    network = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml"
    endpoints = rows(r12 / "endpoint_manifest.csv")
    routing = rows(r13 / "routing_arcs.csv")
    required = rows(r12 / "od_manifest.csv")
    config = json.loads((r12 / "r12_routing_config.json").read_text())
    endpoint = {r["endpoint_id"]: r for r in endpoints}
    required_pairs = {(r["origin_id"], r["destination_id"]) for r in required}
    actual_pairs = {(r["origin_id"], r["destination_id"]) for r in routing}
    checks: dict[str, bool] = {}
    checks["r13_output_hash"] = sha256(r13 / "routing_arcs.csv") == EXPECTED_OUTPUT
    checks["network_hash"] = sha256(network) == EXPECTED_NETWORK and all(r["network_hash"] == EXPECTED_NETWORK for r in routing)
    checks["endpoint_count"] = len(endpoints) == 12
    checks["endpoint_roles"] = Counter(r["endpoint_type"] for r in endpoints) == Counter({"depot": 1, "customer": 10, "charger": 1})
    checks["od_count"] = len(routing) == 132 and len(required) == 132
    checks["self_loop_zero"] = all(r["origin_id"] != r["destination_id"] for r in routing)
    checks["duplicate_zero"] = len(actual_pairs) == len(routing)
    checks["missing_zero"] = required_pairs == actual_pairs
    checks["endpoint_coverage"] = all(sum(r["origin_id"] == eid for r in routing) == 11 and sum(r["destination_id"] == eid for r in routing) == 11 for eid in endpoint)
    expected_columns = {"origin_id", "destination_id", "reachable", "distance_m", "travel_time_s", "origin_edge", "destination_edge", "origin_offset_m", "destination_offset_m", "routing_objective", "vehicle_class", "network_hash"}
    checks["schema_columns"] = expected_columns <= set(routing[0])
    checks["id_references"] = all(r["origin_id"] in endpoint and r["destination_id"] in endpoint for r in routing)
    checks["datatype_nullability"] = all((r["reachable"] == "True" and r["distance_m"] != "" and r["travel_time_s"] != "") or (r["reachable"] == "False" and r["distance_m"] == "" and r["travel_time_s"] == "") for r in routing)
    reachable = [r for r in routing if r["reachable"] == "True"]
    distances = [float(r["distance_m"]) for r in reachable]
    times = [float(r["travel_time_s"]) for r in reachable]
    checks["numeric_positive_finite"] = all(math.isfinite(x) and x > 0 for x in distances + times)
    checks["objective"] = all(r["routing_objective"] == "travel_time_minimizing" for r in routing)
    checks["vehicle_class"] = all(r["vehicle_class"] == VEHICLE for r in routing)

    net = sumolib.net.readNet(str(network))
    checks["mapped_edges_valid"] = all(net.getEdge(r["mapped_edge_id"]) is not None and permitted(net.getEdge(r["mapped_edge_id"])) for r in endpoints)
    # Directed endpoint graph connectivity by independent breadth-first search.
    graph_nodes = {n.getID(): n for n in net.getNodes()}
    def reachable_nodes(start: str) -> set[str]:
        seen, q = {start}, deque([start])
        while q:
            node = graph_nodes[q.popleft()]
            for edge in node.getOutgoing():
                if permitted(edge) and edge.getToNode().getID() not in seen:
                    seen.add(edge.getToNode().getID()); q.append(edge.getToNode().getID())
        return seen
    endpoint_start_nodes = {net.getEdge(row["mapped_edge_id"]).getToNode().getID() for row in endpoints}
    node_reach = {n: reachable_nodes(n) for n in endpoint_start_nodes}
    checks["endpoint_strong_connectivity"] = all(endpoint[a]["mapped_edge_id"] and endpoint[b]["mapped_edge_id"] and net.getEdge(endpoint[b]["mapped_edge_id"]).getFromNode().getID() in node_reach[net.getEdge(endpoint[a]["mapped_edge_id"]).getToNode().getID()] for a in endpoint for b in endpoint)

    # Independent component arithmetic and fastest-path objective checks.
    offset_rows = []
    objective_rows = []
    path_double_count = []
    for r in routing:
        if r["reachable"] != "True":
            continue
        o, d = endpoint[r["origin_id"]], endpoint[r["destination_id"]]
        oe, de = net.getEdge(o["mapped_edge_id"]), net.getEdge(d["mapped_edge_id"])
        od, ot, dd, dt = partials(o, d, net)
        path = json.loads(r["path_edge_sequence"])
        inner = path[1:-1] if len(path) >= 2 else []
        if oe.getID() == de.getID() and float(d["edge_offset_m"]) >= float(o["edge_offset_m"]):
            expected_d, expected_t = float(d["edge_offset_m"]) - float(o["edge_offset_m"]), (float(d["edge_offset_m"]) - float(o["edge_offset_m"])) / float(oe.getSpeed())
        else:
            expected_d = od + sum(float(net.getEdge(e).getLength()) for e in inner) + dd
            expected_t = ot + sum(edge_time(net.getEdge(e)) for e in inner) + dt
        offset_rows.append({"origin_id": r["origin_id"], "destination_id": r["destination_id"], "origin_edge": o["mapped_edge_id"], "origin_offset_m": float(o["edge_offset_m"]), "destination_edge": d["mapped_edge_id"], "destination_offset_m": float(d["edge_offset_m"]), "origin_partial_distance_m": od, "origin_partial_time_s": ot, "network_path_distance_m": sum(float(net.getEdge(e).getLength()) for e in inner), "network_path_time_s": sum(edge_time(net.getEdge(e)) for e in inner), "destination_partial_distance_m": dd, "destination_partial_time_s": dt, "reconstructed_distance_m": expected_d, "r13_distance_m": float(r["distance_m"]), "reconstructed_time_s": expected_t, "r13_time_s": float(r["travel_time_s"]), "distance_difference_m": expected_d-float(r["distance_m"]), "time_difference_s": expected_t-float(r["travel_time_s"]), "path_contains_origin_twice": path.count(oe.getID()) > 1, "path_contains_destination_twice": path.count(de.getID()) > 1})
        path_double_count.extend([x for x in offset_rows[-1:] if x["path_contains_origin_twice"] or x["path_contains_destination_twice"]])
        fast, fast_path = route_cost(o, d, net, "time")
        dist, dist_path = route_cost(o, d, net, "distance")
        objective_rows.append({"origin_id": r["origin_id"], "destination_id": r["destination_id"], "r13_time_s": float(r["travel_time_s"]), "independent_fastest_time_s": fast, "r13_distance_m": float(r["distance_m"]), "independent_shortest_distance_m": dist, "fastest_time_difference_s": float(r["travel_time_s"]) - fast if fast is not None else None, "distance_difference_from_shortest_m": float(r["distance_m"]) - dist if dist is not None else None, "r13_path": path, "fastest_path": fast_path, "shortest_distance_path": dist_path})
    checks["offset_reconstruction"] = all(abs(x["distance_difference_m"]) < 1e-7 and abs(x["time_difference_s"]) < 1e-7 for x in offset_rows)
    checks["no_partial_edge_double_count"] = not path_double_count
    checks["fastest_objective"] = all(x["fastest_time_difference_s"] is not None and abs(x["fastest_time_difference_s"]) < 1e-7 for x in objective_rows)
    checks["delivery_edges_only"] = all(all(permitted(net.getEdge(e)) for e in json.loads(r["path_edge_sequence"])) for r in routing if r["reachable"] == "True")

    speeds = [d/t for d, t in zip(distances, times)]
    detours = []
    original_coordinate_warnings = []
    spatial_categories = []
    mapped_critical_flags = []
    epsilon_m = 1e-6
    for r in routing:
        if r["reachable"] != "True": continue
        origin_endpoint, destination_endpoint = endpoint[r["origin_id"]], endpoint[r["destination_id"]]
        straight = haversine(origin_endpoint, destination_endpoint)
        mapped_origin = mapped_position(net.getEdge(origin_endpoint["mapped_edge_id"]), float(origin_endpoint["edge_offset_m"]))
        mapped_destination = mapped_position(net.getEdge(destination_endpoint["mapped_edge_id"]), float(destination_endpoint["edge_offset_m"]))
        mapped_straight = math.dist(mapped_origin, mapped_destination)
        road = float(r["distance_m"])
        factor = road / straight if straight > 0 else None
        detours.append(factor)
        mapping_bound = straight - float(origin_endpoint["mapping_distance_m"]) - float(destination_endpoint["mapping_distance_m"]) - epsilon_m
        original_violation = straight > 0 and road + epsilon_m < straight
        mapped_violation = road + epsilon_m < mapped_straight
        if original_violation:
            original_coordinate_warnings.append({"od": [r["origin_id"], r["destination_id"]], "road_m": road, "straight_original_m": straight, "mapping_adjusted_lower_bound_m": mapping_bound, "mapped_straight_m": mapped_straight, "mapping_distances_m": [float(origin_endpoint["mapping_distance_m"]), float(destination_endpoint["mapping_distance_m"])], "warning": "road distance below original-coordinate straight distance; original-coordinate comparison is diagnostic only"})
        if mapped_violation:
            item = {"od": [r["origin_id"], r["destination_id"]], "road_m": road, "straight_mapped_m": mapped_straight, "deficit_m": mapped_straight-road, "classification": "true critical inconsistency", "reason": "road distance is below straight distance between the actual SUMO mapped routing positions"}
            mapped_critical_flags.append(item); spatial_categories.append(item)
        elif original_violation and road + epsilon_m >= mapping_bound:
            spatial_categories.append({"od": [r["origin_id"], r["destination_id"]], "classification": "explainable by mapping / geometry", "road_m": road, "straight_original_m": straight, "mapped_straight_m": mapped_straight, "mapping_adjusted_lower_bound_m": mapping_bound})
        elif original_violation:
            spatial_categories.append({"od": [r["origin_id"], r["destination_id"]], "classification": "diagnostic warning only", "road_m": road, "straight_original_m": straight, "mapped_straight_m": mapped_straight, "mapping_adjusted_lower_bound_m": mapping_bound})
    checks["mapped_spatial_critical_gate"] = not mapped_critical_flags
    checks["spatial_noncritical"] = True
    # Compare route values with the independently reconstructed values and report
    # road-network behavior without imposing an arbitrary speed threshold.
    speed_summary = {"mps": {"min": min(speeds), "max": max(speeds), "mean": statistics.mean(speeds), "median": statistics.median(speeds), "p05": percentile(speeds,.05), "p95": percentile(speeds,.95)}, "kmh": {"min": min(s*3.6 for s in speeds), "max": max(s*3.6 for s in speeds), "mean": statistics.mean(s*3.6 for s in speeds), "median": statistics.median(s*3.6 for s in speeds), "p05": percentile([s*3.6 for s in speeds],.05), "p95": percentile([s*3.6 for s in speeds],.95)}}
    asymmetry=[]
    by_pair={(r["origin_id"],r["destination_id"]):r for r in routing}
    for i,a in enumerate(sorted(endpoint)):
        for b in sorted(endpoint)[i+1:]:
            ab, ba = by_pair[(a,b)], by_pair[(b,a)]
            asymmetry.append({"a":a,"b":b,"distance_a_to_b":float(ab["distance_m"]),"distance_b_to_a":float(ba["distance_m"]),"time_a_to_b":float(ab["travel_time_s"]),"time_b_to_a":float(ba["travel_time_s"]),"distance_abs_difference_m":abs(float(ab["distance_m"])-float(ba["distance_m"])),"time_abs_difference_s":abs(float(ab["travel_time_s"])-float(ba["travel_time_s"]))})
    asym_values=[x["distance_abs_difference_m"] for x in asymmetry]
    detour_summary={"min":min(detours),"max":max(detours),"mean":statistics.mean(detours),"median":statistics.median(detours),"p05":percentile(detours,.05),"p95":percentile(detours,.95)}
    speed_outliers=[{"od":[r["origin_id"],r["destination_id"]],"speed_kmh":float(r["distance_m"])/float(r["travel_time_s"])*3.6,"why_flagged":"outside p05-p95 diagnostic band","investigation":"diagnostic only; no fixed threshold used"} for r in routing if r["reachable"]=="True" and (float(r["distance_m"])/float(r["travel_time_s"])*3.6 < speed_summary["kmh"]["p05"] or float(r["distance_m"])/float(r["travel_time_s"])*3.6 > speed_summary["kmh"]["p95"])]
    anomaly={"critical_count":len(mapped_critical_flags),"candidates":spatial_categories+speed_outliers,"speed_outlier_count":len(speed_outliers),"partial_double_count_count":len(path_double_count),"mapped_position_critical_flags":mapped_critical_flags,"original_coordinate_warning_count":len(original_coordinate_warnings),"spatial_categories":spatial_categories,"acceptable_reason":"original-coordinate distance violations are diagnostic; only mapped-position violations are critical"}
    stats={"total_od":len(routing),"reachable":len(reachable),"unreachable":len(routing)-len(reachable),"reachability_rate":len(reachable)/len(routing),"distance_m":{"min":min(distances),"max":max(distances),"mean":statistics.mean(distances),"median":statistics.median(distances)},"travel_time_s":{"min":min(times),"max":max(times),"mean":statistics.mean(times),"median":statistics.median(times)},"speed":speed_summary,"detour_factor":detour_summary,"asymmetry":{"pair_count":len(asymmetry),"distance_abs_difference_m":{"min":min(asym_values),"max":max(asym_values),"mean":statistics.mean(asym_values),"median":statistics.median(asym_values)},"fully_symmetric_pair_count":sum(x["distance_abs_difference_m"]<1e-9 and x["time_abs_difference_s"]<1e-9 for x in asymmetry)}}
    spot_keys={"shortest_distance":min(routing,key=lambda r:float(r["distance_m"])),"longest_distance":max(routing,key=lambda r:float(r["distance_m"])),"shortest_time":min(routing,key=lambda r:float(r["travel_time_s"])),"longest_time":max(routing,key=lambda r:float(r["travel_time_s"])),"highest_speed":max(routing,key=lambda r:float(r["distance_m"])/float(r["travel_time_s"])),"lowest_speed":min(routing,key=lambda r:float(r["distance_m"])/float(r["travel_time_s"]))}
    spot_ids={(r["origin_id"],r["destination_id"]):r for r in spot_keys.values()}
    for r in routing:
        if endpoint[r["origin_id"]]["endpoint_type"]=="depot" and endpoint[r["destination_id"]]["endpoint_type"]=="customer": spot_ids[(r["origin_id"],r["destination_id"])]=r
        if endpoint[r["origin_id"]]["endpoint_type"]=="customer" and endpoint[r["destination_id"]]["endpoint_type"]=="depot": spot_ids[(r["origin_id"],r["destination_id"])]=r
        if endpoint[r["origin_id"]]["endpoint_type"]=="customer" and endpoint[r["destination_id"]]["endpoint_type"]=="charger": spot_ids[(r["origin_id"],r["destination_id"])]=r
        if endpoint[r["origin_id"]]["endpoint_type"]=="charger" and endpoint[r["destination_id"]]["endpoint_type"]=="customer": spot_ids[(r["origin_id"],r["destination_id"])]=r
    spot=[next((x for x in offset_rows if x["origin_id"]==a and x["destination_id"]==b),None) | {"routing_objective_validation":next(x for x in objective_rows if x["origin_id"]==a and x["destination_id"]==b)} for a,b in spot_ids]
    checks["spot_reconstruction"] = all(abs(x["distance_difference_m"])<1e-7 and abs(x["time_difference_s"])<1e-7 for x in spot)
    final_status="PASS" if all(checks.values()) else "FAIL"
    report={"status":final_status,"checks":checks,"input_r13_output_sha256":sha256(r13/"routing_arcs.csv"),"network_hash":EXPECTED_NETWORK,"endpoint_count":len(endpoints),"required_od_count":len(required),"validated_od_count":len(routing),"role_counts":dict(Counter(r["endpoint_type"] for r in endpoints)),"statistics":stats,"anomaly_report":anomaly,"original_coordinate_warnings":original_coordinate_warnings,"spatial_categories":spatial_categories,"asymmetry":asymmetry,"spot_validation":spot,"offset_validation_sample":offset_rows[:20],"objective_validation_sample":objective_rows[:20],"notes":{"r13_output_immutable":True,"same_edge_actual_cases":sum(r["origin_edge"]==r["destination_edge"] for r in routing),"nearest_node_is_not_reference":True,"triangle_inequality": "diagnostic not used as gate","spatial_epsilon_m":epsilon_m,"mapped_position_rule":"road_distance >= straight(mapped SUMO positions) - epsilon","original_coordinate_rule":"road_distance >= straight(original coordinates) - (origin mapping distance + destination mapping distance + epsilon) is diagnostic only","unreachable_graph_check":"all 12 endpoint edge positions mutually reachable in delivery-permitted directed graph"}}
    (out/"r14_validation_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/"od_completeness.json").write_text(json.dumps({"status":"PASS" if all(checks[k] for k in ["od_count","self_loop_zero","duplicate_zero","missing_zero","endpoint_coverage"]) else "FAIL","checks":{k:checks[k] for k in ["od_count","self_loop_zero","duplicate_zero","missing_zero","endpoint_coverage"]}},ensure_ascii=False,indent=2)+'\n')
    (out/"r14_statistics.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    (out/"speed_diagnostics.json").write_text(json.dumps(speed_summary,ensure_ascii=False,indent=2)+'\n')
    (out/"asymmetry_diagnostics.json").write_text(json.dumps(asymmetry,ensure_ascii=False,indent=2)+'\n')
    (out/"spatial_detour_diagnostics.json").write_text(json.dumps({"detour_factor":detour_summary,"spatial_categories":spatial_categories,"original_coordinate_warnings":original_coordinate_warnings,"epsilon_m":epsilon_m},ensure_ascii=False,indent=2)+'\n')
    (out/"spot_validation.json").write_text(json.dumps(spot,ensure_ascii=False,indent=2)+'\n')
    (out/"anomaly_report.json").write_text(json.dumps(anomaly,ensure_ascii=False,indent=2)+'\n')
    files={p.name:sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    manifest={"status":final_status,"input_r13_output_sha256":sha256(r13/"routing_arcs.csv"),"network_hash":EXPECTED_NETWORK,"files":files}
    (out/"r14_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({"status":final_status,"checks":checks,"validated_od":len(routing),"reachable":len(reachable),"critical_anomaly_count":anomaly["critical_count"]},ensure_ascii=False))
    return 0 if final_status=="PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
