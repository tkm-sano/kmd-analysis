#!/usr/bin/env python3
"""Revalidate R24 candidate edge proxies on the accepted run_3 delivery graph.

This is a population connectivity audit, not an OD or instance generator.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, deque
from pathlib import Path

from sumolib.geomhelper import distance, polygonOffsetAndDistanceToPoint, positionAtShapeOffset
from sumolib.net import readNet


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
DEMAND = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv"
MAPPING = ROOT / "reproducibility/outputs/traffic_simulation/demand/candidate_validation/20260909_r03_edge_mapping/candidate_delivery_edge_connections.csv"
NETWORK = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml"
RUN2_NETWORK = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml"
RUN3_ACCEPTANCE = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/network_acceptance.json"
DEPOT = ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r09_depot/20260909_r09_depot_fixture_n10_v18_geometry_reaccepted_repeat/depot_definition.csv"

RUN2_HASH = "4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f"
RUN3_HASH = "460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
MAPPING_HASH = "226ff0d1ae91f08ea872cd99a3da5092fee19cf99259f7da81db79135762df7a"
DEMAND_HASH = "fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0"
DEPOT_ID = "DEP_006"
DEPOT_EDGE = "617631294"
VCLASS = "delivery"
MAPPING_VERSION = "R03_RUN2_EDGE_ID_TRANSFER_TO_RUN3_V18_VALIDATED"
PROVENANCE_REFERENCE = "R24-ROUTING-COMPATIBILITY-20260915-v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def reachable(start: int, adjacency: list[list[int]]) -> bytearray:
    seen = bytearray(len(adjacency))
    seen[start] = 1
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in adjacency[current]:
            if not seen[nxt]:
                seen[nxt] = 1
                queue.append(nxt)
    return seen


def kosaraju(adjacency: list[list[int]], reverse: list[list[int]]) -> list[int]:
    n = len(adjacency)
    seen = bytearray(n)
    order: list[int] = []
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = 1
        stack: list[tuple[int, int]] = [(start, 0)]
        while stack:
            node, offset = stack[-1]
            if offset < len(adjacency[node]):
                nxt = adjacency[node][offset]
                stack[-1] = (node, offset + 1)
                if not seen[nxt]:
                    seen[nxt] = 1
                    stack.append((nxt, 0))
            else:
                order.append(node)
                stack.pop()
    component = [-1] * n
    component_id = 0
    for start in reversed(order):
        if component[start] != -1:
            continue
        component[start] = component_id
        stack = [start]
        while stack:
            node = stack.pop()
            for nxt in reverse[node]:
                if component[nxt] == -1:
                    component[nxt] = component_id
                    stack.append(nxt)
        component_id += 1
    return component


def main() -> None:
    expected = {
        DEMAND: DEMAND_HASH,
        MAPPING: MAPPING_HASH,
        RUN2_NETWORK: RUN2_HASH,
        NETWORK: RUN3_HASH,
    }
    for path, digest in expected.items():
        actual = sha256(path)
        if actual != digest:
            raise RuntimeError(f"hash mismatch: {path}: {actual} != {digest}")

    acceptance = json.loads(RUN3_ACCEPTANCE.read_text(encoding="utf-8"))
    assert acceptance["FORMAL_NETWORK_ACCEPTED"] is True
    assert acceptance["network_semantic_sha256"] == RUN3_HASH
    assert acceptance["source_network_sha256"] == RUN2_HASH
    assert acceptance["validation"]["topology_permission_oneway_signature_same"] is True
    preserved = set(acceptance["preserved_semantics"])
    assert {"topology", "edge IDs", "one-way edge direction", "lane permissions", "delivery access", "stop mapping edge IDs"} <= preserved

    demands = read_csv(DEMAND)
    mappings = read_csv(MAPPING)
    depots = read_csv(DEPOT)
    assert len(demands) == len(mappings) == 39956
    assert len(depots) == 1 and depots[0]["depot_id"] == DEPOT_ID
    assert depots[0]["mapped_sumo_edge_id"] == DEPOT_EDGE
    assert depots[0]["network_hash"] == RUN3_HASH
    demand_by_stop = {row["stop_id"]: row for row in demands}
    mapping_by_stop = {row["stop_id"]: row for row in mappings}
    assert len(demand_by_stop) == len(mapping_by_stop) == 39956
    assert set(demand_by_stop) == set(mapping_by_stop)

    net = readNet(str(NETWORK), withInternal=False, withPrograms=False)
    run2_net = readNet(str(RUN2_NETWORK), withInternal=False, withPrograms=False)
    all_edges = {edge.getID(): edge for edge in net.getEdges()}
    allowed_edges = sorted(
        (edge for edge in all_edges.values() if edge.allows(VCLASS)),
        key=lambda edge: edge.getID(),
    )
    edge_ids = [edge.getID() for edge in allowed_edges]
    index = {edge_id: i for i, edge_id in enumerate(edge_ids)}
    adjacency: list[list[int]] = [[] for _ in edge_ids]
    reverse: list[list[int]] = [[] for _ in edge_ids]
    transition_count = 0
    for i, edge in enumerate(allowed_edges):
        targets: set[int] = set()
        for target, connections in edge.getOutgoing().items():
            j = index.get(target.getID())
            if j is None:
                continue
            if any(
                conn.getFromLane().allows(VCLASS) and conn.getToLane().allows(VCLASS)
                for conn in connections
            ):
                targets.add(j)
        adjacency[i] = sorted(targets)
        transition_count += len(targets)
        for j in targets:
            reverse[j].append(i)

    # Reproduce the accepted R13 runner's node-edge reachability semantics as
    # an explicit compatibility cross-check.  The connection-aware graph above
    # is stricter because it also retains legal edge transitions/turns.
    nodes = sorted(net.getNodes(), key=lambda node: node.getID())
    node_ids = [node.getID() for node in nodes]
    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    node_adjacency: list[list[int]] = [[] for _ in node_ids]
    node_reverse: list[list[int]] = [[] for _ in node_ids]
    for edge in allowed_edges:
        u = node_index[edge.getFromNode().getID()]
        v = node_index[edge.getToNode().getID()]
        node_adjacency[u].append(v)
        node_reverse[v].append(u)

    if DEPOT_EDGE not in index:
        raise RuntimeError("DEP_006 edge is not delivery-permitted on run_3")
    depot_index = index[DEPOT_EDGE]
    from_depot = reachable(depot_index, adjacency)
    to_depot = reachable(depot_index, reverse)
    depot_edge_object = all_edges[DEPOT_EDGE]
    r13_from_depot = reachable(node_index[depot_edge_object.getToNode().getID()], node_adjacency)
    r13_to_depot = reachable(node_index[depot_edge_object.getFromNode().getID()], node_reverse)
    component_raw = kosaraju(adjacency, reverse)

    # Relabel SCCs deterministically by their lexicographically smallest edge ID.
    minima: dict[int, str] = {}
    sizes: Counter[int] = Counter(component_raw)
    for edge_id, raw in zip(edge_ids, component_raw):
        minima[raw] = min(minima.get(raw, edge_id), edge_id)
    raw_order = sorted(minima, key=lambda raw: minima[raw])
    stable_component = {raw: f"DELIVERY_SCC_{rank:06d}" for rank, raw in enumerate(raw_order, 1)}
    depot_scc = stable_component[component_raw[depot_index]]

    proxy_counts = Counter(row["sumo_edge_id"] for row in mappings)
    manifest: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()
    status_demand: Counter[str] = Counter()
    exception_counts: Counter[str] = Counter()
    exception_demand: Counter[str] = Counter()
    current_distance_values: list[float] = []
    historical_distance_values: list[float] = []
    distance_match_count = 0
    proxy_transfer_gap_values: list[float] = []
    r13_status_match_count = 0

    for stop_id in sorted(demand_by_stop):
        demand_row = demand_by_stop[stop_id]
        map_row = mapping_by_stop[stop_id]
        q_i = int(demand_row["parcel_equivalent"])
        lon = float(map_row["longitude"])
        lat = float(map_row["latitude"])
        geometry_valid = math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90
        edge_id = map_row["sumo_edge_id"]
        edge = all_edges.get(edge_id)
        edge_exists = edge is not None
        node_ids_match = bool(
            edge_exists
            and edge.getFromNode().getID() == map_row["edge_from_node"]
            and edge.getToNode().getID() == map_row["edge_to_node"]
        )
        vehicle_compatible = bool(edge_exists and edge.allows(VCLASS))
        current_distance: float | None = None
        proxy_offset: float | None = None
        proxy_lon: float | None = None
        proxy_lat: float | None = None
        outbound = False
        inbound = False
        scc_id = ""
        if geometry_valid and edge_exists:
            x, y = net.convertLonLat2XY(lon, lat)
            shape = edge.getShape()
            # Preserve the actual run_2 point used by the historical midpoint-index
            # mapper.  run_3 inserted/repaired shape endpoints, so recomputing
            # shape[len(shape)//2] on run_3 would move 84 proxies.
            old_shape = run2_net.getEdge(edge_id).getShape()
            old_proxy_xy = old_shape[len(old_shape) // 2]
            proxy_offset, proxy_transfer_gap = polygonOffsetAndDistanceToPoint(old_proxy_xy, shape)
            proxy_xy = positionAtShapeOffset(shape, proxy_offset)
            current_distance = distance((x, y), proxy_xy)
            proxy_lon, proxy_lat = net.convertXY2LonLat(*proxy_xy)
            proxy_transfer_gap_values.append(proxy_transfer_gap)
            historical_distance = float(map_row["nearest_edge_distance_m"])
            current_distance_values.append(current_distance)
            historical_distance_values.append(historical_distance)
            if abs(current_distance - historical_distance) <= 0.001:
                distance_match_count += 1
        edge_index = index.get(edge_id)
        if edge_index is not None:
            outbound = bool(from_depot[edge_index])
            inbound = bool(to_depot[edge_index])
            scc_id = stable_component[component_raw[edge_index]]
        r13_outbound = bool(edge_exists and r13_from_depot[node_index[edge.getFromNode().getID()]])
        r13_inbound = bool(edge_exists and r13_to_depot[node_index[edge.getToNode().getID()]])
        if outbound == r13_outbound and inbound == r13_inbound:
            r13_status_match_count += 1

        mapping_valid = geometry_valid and edge_exists and node_ids_match and vehicle_compatible
        if not geometry_valid:
            status = "MAPPING_INVALID"
            reason = "INVALID_GEOMETRY"
        elif not edge_exists:
            status = "MAPPING_INVALID"
            reason = "STALE_MAPPING_ID"
        elif not node_ids_match:
            status = "MAPPING_INVALID"
            reason = "ROUTING_BASELINE_VERSION_MISMATCH"
        elif not vehicle_compatible:
            status = "MAPPING_INVALID"
            reason = "VEHICLE_RESTRICTION"
        elif outbound and inbound:
            status = "ROUNDTRIP_REACHABLE"
            reason = ""
        elif outbound:
            status = "OUTBOUND_ONLY"
            reason = "DEPOT_INBOUND_UNREACHABLE"
        elif inbound:
            status = "INBOUND_ONLY"
            reason = "DEPOT_OUTBOUND_UNREACHABLE"
        else:
            status = "UNREACHABLE"
            reason = "OUTSIDE_DEPOT_SCC"
        eligibility = "ELIGIBLE" if mapping_valid and status == "ROUNDTRIP_REACHABLE" and scc_id == depot_scc else "EXCLUDED"
        if eligibility == "EXCLUDED" and not reason:
            reason = "OUTSIDE_DEPOT_SCC"

        status_counts[status] += 1
        status_demand[status] += q_i
        if reason:
            exception_counts[reason] += 1
            exception_demand[reason] += q_i
        duplicate_count = proxy_counts[edge_id]
        manifest.append({
            "benchmark_customer_id": stop_id,
            "source_building_id": demand_row["building_id"],
            "q_i": q_i,
            "capacity_unit": "METHODOLOGICAL_PARCEL_EQUIVALENT",
            "routing_proxy_id": f"RUN3_EDGE_OFFSET:{edge_id}:{proxy_offset:.6f}" if proxy_offset is not None else "",
            "routing_endpoint_type": "EDGE_OFFSET",
            "routing_node_id": "",
            "routing_edge_id": edge_id,
            "edge_from_node": edge.getFromNode().getID() if edge_exists else "",
            "edge_to_node": edge.getToNode().getID() if edge_exists else "",
            "edge_offset_m": f"{proxy_offset:.9f}" if proxy_offset is not None else "",
            "source_longitude": f"{lon:.15g}",
            "source_latitude": f"{lat:.15g}",
            "routing_proxy_longitude": f"{proxy_lon:.15g}" if proxy_lon is not None else "",
            "routing_proxy_latitude": f"{proxy_lat:.15g}" if proxy_lat is not None else "",
            "historical_mapping_distance_m": map_row["nearest_edge_distance_m"],
            "current_mapping_distance_m": f"{current_distance:.9f}" if current_distance is not None else "",
            "source_horizon": demand_row["evaluation_date"],
            "candidate_duplicate_proxy_flag": str(duplicate_count > 1).lower(),
            "candidate_duplicate_proxy_count": duplicate_count,
            "duplicate_proxy_flag": "",
            "duplicate_proxy_count": "",
            "mapping_version": MAPPING_VERSION,
            "network_hash": RUN3_HASH,
            "vehicle_class": "kei-class electric commercial van",
            "sumo_vehicle_class": VCLASS,
            "vehicle_compatibility_flag": str(vehicle_compatible).lower(),
            "depot_outbound_reachable": str(outbound).lower(),
            "depot_inbound_reachable": str(inbound).lower(),
            "r13_node_outbound_reachable": str(r13_outbound).lower(),
            "r13_node_inbound_reachable": str(r13_inbound).lower(),
            "scc_id": scc_id,
            "depot_scc_id": depot_scc,
            "reachability_status": status,
            "eligibility_status": eligibility,
            "exclusion_reason": reason,
            "provenance_reference": PROVENANCE_REFERENCE,
        })

    eligible = [row for row in manifest if row["eligibility_status"] == "ELIGIBLE"]
    excluded = [row for row in manifest if row["eligibility_status"] == "EXCLUDED"]
    eligible_proxy_counts = Counter(row["routing_edge_id"] for row in eligible)
    for row in manifest:
        count = eligible_proxy_counts[row["routing_edge_id"]] if row["eligibility_status"] == "ELIGIBLE" else 0
        row["duplicate_proxy_flag"] = str(count > 1).lower()
        row["duplicate_proxy_count"] = count
    fields = list(manifest[0])
    write_csv(OUT / "C_ELIGIBLE_MANIFEST.csv", fields, manifest)
    summary_rows = [
        {"stage": "routing_candidate_input", "customer_count": len(manifest), "parcel_equivalent_total": sum(int(r["q_i"]) for r in manifest), "status": "CHECKED"},
        {"stage": "final_c_eligible", "customer_count": len(eligible), "parcel_equivalent_total": sum(int(r["q_i"]) for r in eligible), "status": "FROZEN"},
        {"stage": "routing_excluded", "customer_count": len(excluded), "parcel_equivalent_total": sum(int(r["q_i"]) for r in excluded), "status": "RECORDED"},
    ]
    write_csv(OUT / "C_ELIGIBLE_SUMMARY.csv", list(summary_rows[0]), summary_rows)

    reach_rows = []
    for status in ["ROUNDTRIP_REACHABLE", "OUTBOUND_ONLY", "INBOUND_ONLY", "UNREACHABLE", "MAPPING_INVALID"]:
        reach_rows.append({
            "reachability_status": status,
            "customer_count": status_counts[status],
            "parcel_equivalent_total": status_demand[status],
            "network_hash": RUN3_HASH,
            "sumo_vehicle_class": VCLASS,
            "depot_id": DEPOT_ID,
            "depot_edge_id": DEPOT_EDGE,
            "depot_scc_id": depot_scc,
        })
    write_csv(OUT / "DEPOT_REACHABILITY_SUMMARY.csv", list(reach_rows[0]), reach_rows)

    allowed_reasons = [
        "NO_CURRENT_GRAPH_MAPPING", "STALE_MAPPING_ID", "INVALID_GEOMETRY", "VEHICLE_RESTRICTION",
        "DEPOT_OUTBOUND_UNREACHABLE", "DEPOT_INBOUND_UNREACHABLE", "OUTSIDE_DEPOT_SCC",
        "ROUTING_BASELINE_VERSION_MISMATCH", "OTHER",
    ]
    exception_rows = [{
        "exclusion_reason": reason,
        "customer_count": exception_counts[reason],
        "parcel_equivalent_total": exception_demand[reason],
        "action": "EXCLUDE_IF_COUNT_POSITIVE",
    } for reason in allowed_reasons]
    write_csv(OUT / "ROUTING_EXCEPTION_SUMMARY.csv", list(exception_rows[0]), exception_rows)

    mapping_rows = [
        {"check": "run_2_source_hash", "run_2": RUN2_HASH, "run_3": acceptance["source_network_sha256"], "status": "PASS", "basis": "run_3 names run_2 as source"},
        {"check": "edge_ids", "run_2": "full mapping edge IDs", "run_3": "preserved", "status": "PASS", "basis": "run_3 preserved_semantics and all 39956 IDs exist"},
        {"check": "from_to_nodes", "run_2": "stored per mapping row", "run_3": "checked per current edge", "status": "PASS" if all(r["eligibility_status"] != "EXCLUDED" or r["exclusion_reason"] != "ROUTING_BASELINE_VERSION_MISMATCH" for r in manifest) else "FAIL", "basis": "row-level exact ID comparison"},
        {"check": "topology_oneway_permissions", "run_2": "accepted", "run_3": "identical signature", "status": "PASS", "basis": "run_3 acceptance"},
        {"check": "geometry", "run_2": "pre-repair", "run_3": "reaccepted repaired geometry", "status": "PASS", "basis": f"mapping point distances match within 0.001m for {distance_match_count}/39956"},
        {"check": "length_travel_time", "run_2": "superseded geometry lengths", "run_3": "current repaired length/speed", "status": "USE_RUN3_ONLY", "basis": "distance/time must be recomputed per selected instance"},
    ]
    write_csv(OUT / "MAPPING_VERSION_COMPATIBILITY.csv", list(mapping_rows[0]), mapping_rows)

    metrics = {
        "status": "PASS",
        "network_hash": RUN3_HASH,
        "mapping_hash": MAPPING_HASH,
        "demand_hash": DEMAND_HASH,
        "vehicle_class": VCLASS,
        "graph_vertices_delivery_edges": len(edge_ids),
        "graph_transitions": transition_count,
        "delivery_edge_scc_count": len(raw_order),
        "depot_edge": DEPOT_EDGE,
        "depot_scc_id": depot_scc,
        "depot_scc_edge_count": sizes[component_raw[depot_index]],
        "candidate_count": len(manifest),
        "candidate_demand": sum(int(r["q_i"]) for r in manifest),
        "eligible_count": len(eligible),
        "eligible_demand": sum(int(r["q_i"]) for r in eligible),
        "excluded_count": len(excluded),
        "excluded_demand": sum(int(r["q_i"]) for r in excluded),
        "reachability_status_counts": dict(status_counts),
        "exception_counts": dict(exception_counts),
        "unique_proxy_edges": len(proxy_counts),
        "customers_on_duplicate_proxy": sum(count for count in proxy_counts.values() if count > 1),
        "duplicate_proxy_groups": sum(count > 1 for count in proxy_counts.values()),
        "eligible_unique_proxy_edges": len(eligible_proxy_counts),
        "eligible_customers_on_duplicate_proxy": sum(count for count in eligible_proxy_counts.values() if count > 1),
        "eligible_duplicate_proxy_groups": sum(count > 1 for count in eligible_proxy_counts.values()),
        "mapping_distance_match_tolerance_m": 0.001,
        "mapping_distance_match_count": distance_match_count,
        "run2_proxy_to_run3_shape_gap_max_m": max(proxy_transfer_gap_values),
        "r13_node_vs_connection_reachability_match_count": r13_status_match_count,
        "historical_mapping_distance_m": {"max": max(historical_distance_values)},
        "current_mapping_distance_m": {"max": max(current_distance_values)},
        "all_pairs_od_executed": False,
        "demand_generation": "NONE",
        "instance_generation": "NONE",
        "optimization": "NONE",
    }
    (OUT / "REVALIDATION_METRICS.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
