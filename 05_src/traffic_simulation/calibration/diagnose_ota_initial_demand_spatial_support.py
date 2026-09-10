#!/usr/bin/env python3
"""Diagnose zero spatial support without using observed traffic values."""

from __future__ import annotations

import argparse
import csv
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx


GRID_SIZE_M = 500.0
CONNECTORS_PER_GRID_CELL = 2


def passenger_lane(lane: ET.Element) -> bool:
    allow = set((lane.get("allow") or "").split())
    disallow = set((lane.get("disallow") or "").split())
    return "passenger" in allow if allow else "passenger" not in disallow


def read_passenger_graph(net_path: Path) -> tuple[dict[str, dict[str, Any]], nx.DiGraph]:
    edges: dict[str, dict[str, Any]] = {}
    graph = nx.DiGraph()
    for event, element in ET.iterparse(net_path, events=("end",)):
        if element.tag == "edge" and not element.get("function"):
            lanes = [lane for lane in element.findall("lane") if passenger_lane(lane) and lane.get("shape")]
            if lanes:
                coordinates = [tuple(map(float, value.split(","))) for value in lanes[0].get("shape", "").split()]
                midpoint = coordinates[len(coordinates) // 2]
                edges[element.get("id", "")] = {
                    "priority": int(element.get("priority", "-1")),
                    "type": element.get("type", ""),
                    "midpoint": midpoint,
                    "passenger_lane_count": len(lanes),
                    "length": max(float(lane.get("length", "0")) for lane in lanes),
                }
                graph.add_node(element.get("id", ""))
        elif element.tag == "connection":
            source, destination = element.get("from"), element.get("to")
            if source and destination:
                graph.add_edge(source, destination)
        if element.tag in {"edge", "connection"}:
            element.clear()
    graph = graph.subgraph(edges).copy()
    return edges, graph


def largest_scc(graph: nx.DiGraph) -> set[str]:
    return set(max(nx.strongly_connected_components(graph), key=len))


def read_taz(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    result: dict[str, dict[str, dict[str, float]]] = {}
    for taz in ET.parse(path).getroot().iter("taz"):
        record = {"sources": {}, "sinks": {}}
        for role, tag in (("sources", "tazSource"), ("sinks", "tazSink")):
            for item in taz.findall(tag):
                if item.get("id"):
                    record[role][item.get("id", "")] = float(item.get("weight", "1"))
        result[taz.get("id", "")] = record
    return result


def edge_taz_membership(taz: dict[str, dict[str, dict[str, float]]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for taz_id, record in taz.items():
        for edge_id in set(record["sources"]) | set(record["sinks"]):
            result[edge_id].add(taz_id)
    return result


def read_positive_relations(path: Path) -> tuple[set[tuple[str, str]], dict[tuple[str, str], float]]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "tazRelation":
            key = (element.get("from", ""), element.get("to", ""))
            totals[key] += float(element.get("count", "0"))
        element.clear()
    return {key for key, value in totals.items() if value > 0}, dict(totals)


def read_route_edge_support(path: Path) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = defaultdict(lambda: {"route_count": 0.0, "assigned_amount": 0.0})
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "route" and element.get("edges"):
            amount = float(element.get("probability", "0"))
            for edge_id in set(element.get("edges", "").split()):
                result[edge_id]["route_count"] += 1
                result[edge_id]["assigned_amount"] += amount
        element.clear()
    return dict(result)


def read_groups(path: Path, group_ids: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [row for row in csv.DictReader(stream) if row["measurement_group_id"] in group_ids]


def assess_groups(
    groups: list[dict[str, str]], edges: dict[str, dict[str, Any]], graph: nx.DiGraph,
    taz: dict[str, dict[str, dict[str, float]]], positive_relations: set[tuple[str, str]],
    route_support: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    giant = largest_scc(graph)
    membership = edge_taz_membership(taz)
    result = []
    for group in groups:
        selected = group["selected_edge_ids"].split(";")
        available = [edge_id for edge_id in selected if edge_id in edges]
        connected = [edge_id for edge_id in available if edge_id in giant]
        zones = sorted({zone for edge_id in selected for zone in membership.get(edge_id, set())})
        zones_with_od = sorted({
            zone for zone in zones
            if any(origin == zone or destination == zone for origin, destination in positive_relations)
        })
        route_edges = [
            edge_id for edge_id in selected
            if route_support.get(edge_id, {}).get("assigned_amount", 0) > 0
        ]
        if len(available) < len(selected):
            direct_cause = "passenger_edge_unavailable"
        elif not connected:
            direct_cause = "outside_largest_passenger_scc"
        elif zones and not zones_with_od:
            direct_cause = "local_taz_has_no_positive_od"
        elif not route_edges:
            direct_cause = "connected_with_od_but_not_selected_by_route_assignment"
        else:
            direct_cause = "route_support_present"
        result.append({
            "measurement_group_id": group["measurement_group_id"],
            "official_name": group["official_name"],
            "selected_edge_ids": ";".join(selected),
            "passenger_edges_available": len(available),
            "edges_in_largest_scc": len(connected),
            "taz_membership": ";".join(zones),
            "taz_with_positive_od": ";".join(zones_with_od),
            "route_supported_edges": ";".join(route_edges),
            "route_alternative_count": sum(route_support.get(edge_id, {}).get("route_count", 0) for edge_id in selected),
            "assigned_amount": sum(route_support.get(edge_id, {}).get("assigned_amount", 0) for edge_id in selected),
            "direct_cause": direct_cause,
        })
    return result


def write_daily_relations(source: Path, destination: Path) -> None:
    _, totals = read_positive_relations(source)
    root = ET.Element("data")
    interval = ET.SubElement(root, "interval", {"id": "passenger", "begin": "25200", "end": "68400"})
    for (origin, target), count in sorted(totals.items()):
        if count > 0:
            ET.SubElement(interval, "tazRelation", {"from": origin, "to": target, "count": f"{count:.6f}"})
    ET.indent(root)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)


def write_stratified_taz(
    source: Path, destination: Path, edges: dict[str, dict[str, Any]], giant_scc: set[str]
) -> dict[str, int]:
    original = read_taz(source)
    root = ET.Element("additional")
    counts: dict[str, int] = {}
    for taz_id, record in sorted(original.items()):
        taz_element = ET.SubElement(root, "taz", {"id": taz_id})
        if taz_id.startswith("EXT_"):
            chosen_sources = record["sources"]
            chosen_sinks = record["sinks"]
        else:
            candidates: dict[tuple[int, int], list[tuple[float, str]]] = defaultdict(list)
            for edge_id, weight in record["sources"].items():
                if edge_id not in edges or edge_id not in giant_scc:
                    continue
                x, y = edges[edge_id]["midpoint"]
                cell = (math.floor(x / GRID_SIZE_M), math.floor(y / GRID_SIZE_M))
                candidates[cell].append((weight, edge_id))
            selected = {
                edge_id
                for values in candidates.values()
                for _, edge_id in sorted(values, reverse=True)[:CONNECTORS_PER_GRID_CELL]
            }
            chosen_sources = {edge_id: record["sources"][edge_id] for edge_id in sorted(selected)}
            chosen_sinks = {edge_id: record["sinks"].get(edge_id, record["sources"][edge_id]) for edge_id in sorted(selected)}
        for edge_id, weight in chosen_sources.items():
            ET.SubElement(taz_element, "tazSource", {"id": edge_id, "weight": f"{weight:.6f}"})
        for edge_id, weight in chosen_sinks.items():
            ET.SubElement(taz_element, "tazSink", {"id": edge_id, "weight": f"{weight:.6f}"})
        counts[taz_id] = len(chosen_sources)
    ET.indent(root)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--net", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--taz", type=Path, required=True)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with args.support.open(encoding="utf-8", newline="") as stream:
        zero_groups = {row["measurement_group_id"] for row in csv.DictReader(stream) if row["spatial_support"] == "absent"}
    if len(zero_groups) != 10:
        raise ValueError(f"fixed zero-support population changed: {len(zero_groups)}")
    edges, graph = read_passenger_graph(args.net)
    giant = largest_scc(graph)
    taz = read_taz(args.taz)
    positive_relations, _ = read_positive_relations(args.relations)
    route_support = read_route_edge_support(args.routes)
    rows = assess_groups(read_groups(args.groups, zero_groups), edges, graph, taz, positive_relations, route_support)
    with (args.output / "baseline_zero_group_diagnosis.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_daily_relations(args.relations, args.output / "diagnostic_daily_relations.xml")
    connector_counts = write_stratified_taz(
        args.taz, args.output / "diagnostic_stratified_500m.taz.xml", edges, giant
    )
    summary = {
        "research_stage": "2-3-A",
        "zero_group_count": len(zero_groups),
        "passenger_edge_count": len(edges),
        "largest_passenger_scc_edge_count": len(giant),
        "direct_cause_counts": dict(sorted(defaultdict(int, {
            cause: sum(row["direct_cause"] == cause for row in rows)
            for cause in {row["direct_cause"] for row in rows}
        }).items())),
        "stratified_connector_counts": connector_counts,
        "improvement_is_observation_independent": True,
        "improvement_rule": {
            "grid_size_m": GRID_SIZE_M,
            "connectors_per_grid_cell": CONNECTORS_PER_GRID_CELL,
            "selection": "two highest official TAZ weights among passenger edges in largest SCC",
        },
    }
    (args.output / "diagnostic_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
