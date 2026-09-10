#!/usr/bin/env python3
"""Make SUMO lane geometry continuous at junctions and length-consistent.

The transformation is intentionally limited to lane ``shape`` and ``length``
attributes. Junctions, edges, connections, permissions, speeds and IDs are
copied unchanged. Each lane shape is changed to:

    from-junction XY -> existing shape interior -> to-junction XY

and its declared length is set to the resulting polyline length. This makes
declared routing length follow the connected geometry; it does not add edges,
connections, turns, or access permissions.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def points(shape: str) -> list[tuple[float, float]]:
    out = []
    for token in shape.split():
        xy = token.split(",")
        if len(xy) >= 2:
            out.append((float(xy[0]), float(xy[1])))
    return out


def shape_text(ps: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.6f},{y:.6f}" for x, y in ps)


def polyline_len(ps: list[tuple[float, float]]) -> float:
    return sum(dist(a, b) for a, b in zip(ps, ps[1:]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    junctions: dict[str, tuple[float, float]] = {}
    for event, elem in ET.iterparse(args.input, events=("end",)):
        if elem.tag == "junction" and "x" in elem.attrib and "y" in elem.attrib:
            junctions[elem.attrib["id"]] = (float(elem.attrib["x"]), float(elem.attrib["y"]))
        elem.clear()

    changed_lanes = 0
    changed_edges = 0
    max_length_delta = 0.0
    edge_count = lane_count = node_count = connection_count = 0
    with args.output.open("w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        depth = 0
        for event, elem in ET.iterparse(args.input, events=("start", "end")):
            if event == "start":
                depth += 1
                if depth == 1:
                    attrs_parts = []
                    for k, v in elem.attrib.items():
                        if k == "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation":
                            attrs_parts.append(f'xsi:noNamespaceSchemaLocation="{v}"')
                        else:
                            attrs_parts.append(f'{k}="{v}"')
                    attrs_parts.append('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
                    attrs = " ".join(attrs_parts)
                    out.write(f"<net {attrs}>\n")
                continue
            if depth == 2:
                if elem.tag == "edge":
                    edge_count += 1
                    if elem.attrib.get("function") != "internal":
                        start = junctions.get(elem.attrib.get("from", ""))
                        end = junctions.get(elem.attrib.get("to", ""))
                        if start and end:
                            edge_changed = False
                            edge_shape = points(elem.attrib.get("shape", ""))
                            if len(edge_shape) >= 2:
                                edge_ps = [start]
                                for point in edge_shape:
                                    if dist(edge_ps[-1], point) > 1e-9:
                                        edge_ps.append(point)
                                if dist(edge_ps[-1], end) > 1e-9:
                                    edge_ps.append(end)
                                elem.attrib["shape"] = shape_text(edge_ps)
                                edge_changed = True
                            for lane in elem.findall("lane"):
                                lane_count += 1
                                old_length = float(lane.attrib["length"])
                                old = points(lane.attrib.get("shape", ""))
                                if len(old) < 2:
                                    continue
                                ps = [start]
                                for p in old:
                                    if dist(ps[-1], p) > 1e-9:
                                        ps.append(p)
                                if dist(ps[-1], end) > 1e-9:
                                    ps.append(end)
                                new_length = polyline_len(ps)
                                lane.attrib["shape"] = shape_text(ps)
                                lane.attrib["length"] = f"{new_length:.6f}"
                                changed_lanes += 1
                                max_length_delta = max(max_length_delta, abs(new_length - old_length))
                                edge_changed = True
                            if edge_changed:
                                changed_edges += 1
                elif elem.tag == "junction":
                    node_count += 1
                elif elem.tag == "connection":
                    connection_count += 1
                out.write(ET.tostring(elem, encoding="unicode") + "\n")
                elem.clear()
            depth -= 1
        out.write("</net>\n")

    report = args.output.with_name("repair_transform_report.json")
    import json
    report.write_text(json.dumps({
        "input": str(args.input), "input_sha256": sha(args.input),
        "output": str(args.output), "output_sha256": sha(args.output),
        "rule": "from-junction XY -> existing lane shape -> to-junction XY; lane length equals resulting polyline length",
        "changed_edges": changed_edges, "changed_lanes": changed_lanes,
        "edge_count_seen": edge_count, "lane_count_seen": lane_count,
        "junction_count_seen": node_count, "connection_count_seen": connection_count,
        "max_abs_length_delta_m": max_length_delta,
        "topology_or_permission_edit": False,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
