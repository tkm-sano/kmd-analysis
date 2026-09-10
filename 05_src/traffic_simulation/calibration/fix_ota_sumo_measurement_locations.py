#!/usr/bin/env python3
"""Fix reproducible SUMO measurement locations for uniquely matched official counts.

This tool creates detector definitions and observation links only.  It does not
change demand, traffic parameters, the SUMO network, or source observations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge, transform, unary_union


MOTORIZED = {"passenger", "taxi", "bus", "coach", "delivery", "truck", "motorcycle"}
MLIT_SAMPLE_FRACTIONS = (0.25, 0.35, 0.50, 0.65, 0.75)
MLIT_MAX_EDGE_DISTANCE_M = 50.0
MLIT_MIN_DIRECTION_COSINE = 0.50
POLICE_CLUSTER_MARGIN_M = 20.0
POLICE_CLUSTER_LINK_MAX_M = 45.0
DETECTOR_END_MARGIN_M = 5.0
MIN_BOUNDARY_EDGE_LENGTH_M = DETECTOR_END_MARGIN_M + 0.1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def use_split(year: int) -> str:
    if year == 2023:
        return "calibration"
    if year == 2024:
        return "independent_validation"
    raise ValueError(f"unsupported police observation year: {year}")


def safe_lane_position(length: float, desired: float) -> float:
    if length <= 0.2:
        raise ValueError(f"lane too short for a detector: {length}")
    return round(min(max(desired, 0.1), length - 0.1), 3)


def external_incoming_edges(edges: dict[str, dict[str, Any]], cluster_nodes: set[str]) -> list[str]:
    return sorted(
        edge_id for edge_id, edge in edges.items()
        if edge["to"] in cluster_nodes and edge["from"] not in cluster_nodes and edge["motorized"]
    )


def absorb_short_incoming_links(
    edges: dict[str, dict[str, Any]], cluster_nodes: set[str], minimum_detector_length: float
) -> set[str]:
    """Move the measurement boundary upstream across artificial short edge splits."""
    expanded = set(cluster_nodes)
    while True:
        short_sources = {
            edge["from"] for edge in edges.values()
            if edge["to"] in expanded and edge["from"] not in expanded
            and edge["motorized"] and edge["length"] < minimum_detector_length
        }
        if not short_sources:
            return expanded
        expanded.update(short_sources)


class DetectorRegistry:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._by_key: dict[tuple[str, int], str] = {}

    def register(self, observation_group: str, edge_id: str, lane_id: str, position: float) -> str:
        key = (lane_id, round(position * 1000))
        if key in self._by_key:
            detector_id = self._by_key[key]
            record = next(item for item in self.records if item["detector_id"] == detector_id)
            if observation_group not in record["observation_groups"]:
                record["observation_groups"].append(observation_group)
                record["observation_groups"].sort()
            return detector_id
        detector_id = f"DET_{len(self.records) + 1:04d}"
        self._by_key[key] = detector_id
        self.records.append({
            "detector_id": detector_id,
            "edge_id": edge_id,
            "lane_id": lane_id,
            "position_m": round(position, 3),
            "observation_groups": [observation_group],
        })
        return detector_id


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_shape(value: str) -> LineString:
    return LineString([tuple(map(float, item.split(","))) for item in value.split()])


def lane_motorized(attrib: dict[str, str]) -> bool:
    allow = attrib.get("allow")
    if allow:
        return bool(set(allow.split()) & MOTORIZED)
    disallow = set(attrib.get("disallow", "").split())
    return not MOTORIZED.issubset(disallow)


def load_net(net_path: Path) -> dict[str, Any]:
    location = None
    junctions: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    connections: dict[str, set[str]] = defaultdict(set)
    for _, element in ET.iterparse(net_path, events=("end",)):
        if element.tag == "location":
            location = dict(element.attrib)
        elif element.tag == "junction" and not element.get("id", "").startswith(":"):
            junctions[element.get("id")] = {
                "x": float(element.get("x")), "y": float(element.get("y")), "type": element.get("type")
            }
        elif element.tag == "edge" and not element.get("function"):
            lanes = []
            orig_ids = set()
            for lane in element.findall("lane"):
                if not lane.get("shape"):
                    continue
                lane_record = {
                    "id": lane.get("id"), "length": float(lane.get("length")), "shape": parse_shape(lane.get("shape")),
                    "motorized": lane_motorized(lane.attrib), "allow": lane.get("allow", ""),
                }
                lanes.append(lane_record)
                for param in lane.findall("param"):
                    if param.get("key") == "origId": orig_ids.update((param.get("value") or "").split())
            if lanes:
                edge_id = element.get("id")
                edges[edge_id] = {
                    "id": edge_id, "from": element.get("from"), "to": element.get("to"), "lanes": lanes,
                    "shape": lanes[0]["shape"], "length": max(lane["length"] for lane in lanes),
                    "motorized": any(lane["motorized"] for lane in lanes), "orig_ids": sorted(orig_ids),
                }
        elif element.tag == "connection" and element.get("from") and element.get("to"):
            connections[element.get("from")].add(element.get("to"))
        if element.tag in {"edge", "junction", "connection", "location"}:
            element.clear()
    if location is None:
        raise ValueError("SUMO network location metadata is missing")
    return {"location": location, "junctions": junctions, "edges": edges, "connections": connections}


def wgs84_to_sumo_transformer(location: dict[str, str]) -> tuple[Transformer, float, float]:
    projection = CRS.from_proj4(location["projParameter"])
    transformer = Transformer.from_crs(4326, projection, always_xy=True)
    offset_x, offset_y = map(float, location["netOffset"].split(","))
    return transformer, offset_x, offset_y


def to_sumo_geometry(geometry: Any, location: dict[str, str]) -> Any:
    transformer, offset_x, offset_y = wgs84_to_sumo_transformer(location)
    def project(x: Any, y: Any, z: Any = None) -> tuple[Any, Any]:
        projected_x, projected_y = transformer.transform(x, y)
        return projected_x + offset_x, projected_y + offset_y
    return transform(project, geometry)


def longest_line(geometry: Any) -> LineString:
    if geometry.geom_type == "LineString":
        return geometry
    merged = linemerge(geometry)
    if merged.geom_type == "LineString":
        return merged
    lines = [item for item in merged.geoms if item.geom_type == "LineString"]
    if not lines:
        raise ValueError(f"official geometry has no line: {geometry.geom_type}")
    return max(lines, key=lambda item: item.length)


def local_unit_vector(line: LineString, position: float, delta: float = 3.0) -> tuple[float, float]:
    start = line.interpolate(max(0.0, position - delta))
    end = line.interpolate(min(line.length, position + delta))
    dx, dy = end.x - start.x, end.y - start.y
    norm = math.hypot(dx, dy)
    if norm == 0:
        raise ValueError("zero-length local tangent")
    return dx / norm, dy / norm


def dot(left: tuple[float, float], right: tuple[float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1]


def select_mlit_cross_section(official: LineString, candidate_edges: list[dict[str, Any]]) -> dict[str, Any]:
    attempts = []
    for fraction in MLIT_SAMPLE_FRACTIONS:
        official_pos = official.length * fraction
        point = official.interpolate(official_pos)
        official_vector = local_unit_vector(official, official_pos, min(10.0, max(1.0, official.length / 100)))
        directional: dict[str, list[dict[str, Any]]] = {"along": [], "against": []}
        for edge in candidate_edges:
            if not edge["motorized"]:
                continue
            edge_pos = edge["shape"].project(point)
            nearest = edge["shape"].interpolate(edge_pos)
            distance = point.distance(nearest)
            if distance > MLIT_MAX_EDGE_DISTANCE_M:
                continue
            edge_vector = local_unit_vector(edge["shape"], edge_pos, min(3.0, max(0.2, edge["shape"].length / 10)))
            cosine = dot(official_vector, edge_vector)
            if abs(cosine) < MLIT_MIN_DIRECTION_COSINE:
                continue
            direction = "along" if cosine >= 0 else "against"
            directional[direction].append({
                "edge": edge, "distance": distance, "edge_position": edge_pos,
                "endpoint_clearance": min(edge_pos, edge["shape"].length - edge_pos), "cosine": cosine,
            })
        if not directional["along"] or not directional["against"]:
            attempts.append({"fraction": fraction, "status": "direction_pair_missing"})
            continue
        along = min(directional["along"], key=lambda item: (item["distance"], -item["endpoint_clearance"], item["edge"]["id"]))
        against = min(directional["against"], key=lambda item: (item["distance"], -item["endpoint_clearance"], item["edge"]["id"]))
        pair = [along, against]
        score = (
            -min(item["endpoint_clearance"] for item in pair),
            max(item["distance"] for item in pair),
            sum(item["distance"] for item in pair),
            abs(fraction - 0.5),
            along["edge"]["id"], against["edge"]["id"],
        )
        attempts.append({
            "fraction": fraction, "status": "candidate", "score": score,
            "point": [point.x, point.y], "along": along, "against": against,
        })
    candidates = [item for item in attempts if item["status"] == "candidate"]
    if not candidates:
        raise ValueError("no opposite-direction SUMO edge pair near official section")
    selected = min(candidates, key=lambda item: item["score"])
    return {"selected": selected, "attempts": attempts}


def expand_junction_cluster(seed_nodes: set[str], net: dict[str, Any]) -> set[str]:
    points = [Point(net["junctions"][node]["x"], net["junctions"][node]["y"]) for node in seed_nodes]
    center = unary_union(points).centroid
    radius = max(center.distance(point) for point in points) + POLICE_CLUSTER_MARGIN_M
    eligible = {
        node for node, record in net["junctions"].items()
        if center.distance(Point(record["x"], record["y"])) <= radius
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in net["edges"].values():
        if edge["from"] in eligible and edge["to"] in eligible and edge["length"] <= POLICE_CLUSTER_LINK_MAX_M:
            adjacency[edge["from"]].add(edge["to"])
            adjacency[edge["to"]].add(edge["from"])
    cluster = set(seed_nodes)
    queue = list(seed_nodes)
    while queue:
        node = queue.pop()
        for neighbor in adjacency[node]:
            if neighbor not in cluster:
                cluster.add(neighbor)
                queue.append(neighbor)
    return cluster


def lane_detectors_at_point(registry: DetectorRegistry, group_id: str, edge: dict[str, Any], point: Point) -> list[str]:
    detector_ids = []
    for lane in edge["lanes"]:
        if not lane["motorized"]:
            continue
        position = safe_lane_position(lane["length"], lane["shape"].project(point))
        detector_ids.append(registry.register(group_id, edge["id"], lane["id"], position))
    return detector_ids


def lane_detectors_near_end(registry: DetectorRegistry, group_id: str, edge: dict[str, Any]) -> list[str]:
    detector_ids = []
    for lane in edge["lanes"]:
        if lane["motorized"]:
            position = safe_lane_position(lane["length"], lane["length"] - DETECTOR_END_MARGIN_M)
            detector_ids.append(registry.register(group_id, edge["id"], lane["id"], position))
    return detector_ids


def load_official_features(tile_dir: Path, census_ids: set[str], location: dict[str, str]) -> dict[str, LineString]:
    fragments: dict[str, list[Any]] = defaultdict(list)
    for path in sorted(tile_dir.glob("*.geojson")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            census_id = str(feature.get("properties", {}).get("census", ""))
            if census_id in census_ids:
                fragments[census_id].append(shape(feature["geometry"]))
    return {
        census_id: longest_line(to_sumo_geometry(unary_union(geometries), location))
        for census_id, geometries in fragments.items()
    }


def group_hash(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:10]}"


def build(repo: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"immutable output already exists: {output}")
    output.mkdir(parents=True)
    mapping_dir = repo / "reproducibility/outputs/traffic_simulation/calibration/20260823_ota_official_traffic_observation_mapping_v5"
    census_dir = repo / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
    net_path = repo / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"
    mlit_mapping_path = mapping_dir / "mlit_r3_ota_observation_mapping.csv"
    police_mapping_path = mapping_dir / "keishicho_ota_observation_mapping.csv"

    mlit_rows = [row for row in read_csv(mlit_mapping_path) if row["match_status"] == "unique"]
    police_rows = [row for row in read_csv(police_mapping_path) if row["match_status"] == "unique"]
    if len(mlit_rows) != 21:
        raise ValueError(f"expected 21 unique MLIT sections, found {len(mlit_rows)}")
    net = load_net(net_path)
    features = load_official_features(census_dir / "webmap_tiles", {row["census_id"] for row in mlit_rows}, net["location"])
    registry = DetectorRegistry()
    groups: list[dict[str, Any]] = []
    observation_links: list[dict[str, Any]] = []
    selection_details: dict[str, Any] = {}

    for row in sorted(mlit_rows, key=lambda item: item["census_id"]):
        census_id = row["census_id"]
        group_id = f"MLIT_R3_{census_id}"
        edge_ids = [edge for edge in row["sumo_edge_ids"].split(";") if edge in net["edges"]]
        candidates = [net["edges"][edge_id] for edge_id in edge_ids]
        result = select_mlit_cross_section(features[census_id], candidates)
        selected = result["selected"]
        selected_items = [("along_official_geometry", selected["along"]), ("against_official_geometry", selected["against"])]
        detector_ids, selected_edge_ids = [], []
        selected_records = []
        for direction, item in selected_items:
            edge = item["edge"]
            point = edge["shape"].interpolate(item["edge_position"])
            ids = lane_detectors_at_point(registry, group_id, edge, point)
            detector_ids.extend(ids); selected_edge_ids.append(edge["id"])
            selected_records.append({
                "direction_role": direction, "edge_id": edge["id"], "distance_from_official_line_m": round(item["distance"], 3),
                "direction_cosine": round(item["cosine"], 6), "endpoint_clearance_m": round(item["endpoint_clearance"], 3),
                "detector_ids": ids,
            })
        groups.append({
            "measurement_group_id": group_id, "source": "MLIT_R3", "official_id": census_id,
            "official_name": row["route_name"], "measurement_type": "representative_both_direction_cross_section",
            "aggregation_semantics": "sum_all_selected_lanes_and_both_directions",
            "official_direction_assignment": "unresolved_not_required_for_both_direction_total",
            "selected_edge_ids": ";".join(selected_edge_ids), "detector_ids": ";".join(detector_ids),
            "selection_fraction": selected["fraction"], "status": "fixed",
        })
        observation_links.append({
            "source": "MLIT_R3", "observation_id": census_id, "observation_year": "2021",
            "use_split": "calibration", "measurement_group_id": group_id,
            "observation_aggregation": "sum_up_and_down_before_comparison", "status": "linked",
        })
        selection_details[group_id] = {"selected": selected_records, "sampled_fractions": list(MLIT_SAMPLE_FRACTIONS)}

    police_by_name: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in police_rows:
        police_by_name[(row["site_name"], row["observation_kind"])].append(row)
    for (site_name, kind), rows in sorted(police_by_name.items()):
        seed_nodes = set(rows[0]["sumo_junction_ids"].split(";"))
        if not seed_nodes or not seed_nodes.issubset(net["junctions"]):
            raise ValueError(f"police seed junction missing for {site_name}")
        cluster = expand_junction_cluster(seed_nodes, net)
        cluster = absorb_short_incoming_links(net["edges"], cluster, MIN_BOUNDARY_EDGE_LENGTH_M)
        group_id = group_hash("KEISHICHO_JUNCTION" if kind == "junction" else "KEISHICHO_SECTION", site_name)
        detector_ids: list[str] = []
        selected_edge_ids: list[str] = []
        if kind == "junction":
            selected_edge_ids = external_incoming_edges(net["edges"], cluster)
            if not selected_edge_ids:
                raise ValueError(f"no external incoming edge for {site_name}")
            for edge_id in selected_edge_ids:
                detector_ids.extend(lane_detectors_near_end(registry, group_id, net["edges"][edge_id]))
            measurement_type = "all_external_motorized_incoming_edges"
            aggregation = "sum_all_selected_incoming_lanes_once"
        else:
            mapped_way_ids = set(rows[0]["osm_way_ids"].split(";"))
            incoming = external_incoming_edges(net["edges"], cluster)
            selected_edge_ids = [
                edge_id for edge_id in incoming
                if mapped_way_ids.intersection(net["edges"][edge_id]["orig_ids"])
                or re.sub(r"^-?(\d+).*$", r"\1", edge_id) in mapped_way_ids
            ]
            if len(selected_edge_ids) != 2:
                raise ValueError(f"expected two Spring Bridge direction edges, found {selected_edge_ids}")
            for edge_id in selected_edge_ids:
                detector_ids.extend(lane_detectors_near_end(registry, group_id, net["edges"][edge_id]))
            measurement_type = "named_road_both_direction_cross_section"
            aggregation = "sum_all_selected_lanes_and_both_directions"
        missing_connections = [edge_id for edge_id in selected_edge_ids if not net["connections"].get(edge_id)]
        groups.append({
            "measurement_group_id": group_id, "source": "Keishicho", "official_id": site_name,
            "official_name": site_name, "measurement_type": measurement_type, "aggregation_semantics": aggregation,
            "official_direction_assignment": "not_used_aggregate_only", "selected_edge_ids": ";".join(selected_edge_ids),
            "detector_ids": ";".join(detector_ids), "selection_fraction": "near_downstream_end_5m",
            "status": "fixed" if not missing_connections else "connection_review_required",
        })
        selection_details[group_id] = {
            "seed_junction_ids": sorted(seed_nodes), "expanded_cluster_junction_ids": sorted(cluster),
            "selected_incoming_edge_ids": selected_edge_ids, "missing_outgoing_connection_edge_ids": missing_connections,
        }
        for row in sorted(rows, key=lambda item: item["year"]):
            year = int(row["year"])
            observation_links.append({
                "source": f"Keishicho_{year}", "observation_id": row["site_number"], "observation_year": year,
                "use_split": use_split(year), "measurement_group_id": group_id,
                "observation_aggregation": (
                    "junction_entering_total" if kind == "junction" else "section_both_directions_total"
                ), "status": "linked",
            })

    detector_groups = defaultdict(list)
    for record in registry.records:
        detector_groups[(record["lane_id"], record["position_m"])].append(record["detector_id"])
    physical_duplicates = {str(key): value for key, value in detector_groups.items() if len(value) > 1}
    group_edge_owners: dict[str, list[str]] = defaultdict(list)
    for group in groups:
        for edge_id in group["selected_edge_ids"].split(";"):
            group_edge_owners[edge_id].append(group["measurement_group_id"])
    cross_group_edge_reuse = {edge: owners for edge, owners in group_edge_owners.items() if len(set(owners)) > 1}
    split_errors = [
        row for row in observation_links
        if (str(row["observation_year"]) == "2024" and row["use_split"] != "independent_validation")
        or (str(row["observation_year"]) in {"2021", "2023"} and row["use_split"] != "calibration")
    ]
    incomplete_groups = [group["measurement_group_id"] for group in groups if group["status"] != "fixed"]

    write_csv(output / "measurement_groups.csv", groups)
    write_csv(output / "detector_lanes.csv", registry.records)
    write_csv(output / "observation_to_measurement_group.csv", observation_links)
    (output / "selection_details.json").write_text(json.dumps(selection_details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    additional = ET.Element("additional")
    for record in registry.records:
        ET.SubElement(additional, "inductionLoop", {
            "id": record["detector_id"], "lane": record["lane_id"], "pos": f"{record['position_m']:.3f}",
            "period": "3600", "file": "official_traffic_measurements_e1.xml", "friendlyPos": "false",
        })
    ET.indent(additional)
    ET.ElementTree(additional).write(output / "official_traffic_measurement_detectors.add.xml", encoding="utf-8", xml_declaration=True)

    deterministic_outputs = [
        "measurement_groups.csv", "detector_lanes.csv", "observation_to_measurement_group.csv",
        "selection_details.json", "official_traffic_measurement_detectors.add.xml",
    ]

    counts = {
        "mlit_representative_sections": sum(group["source"] == "MLIT_R3" for group in groups),
        "keishicho_junction_groups": sum(group["source"] == "Keishicho" and group["measurement_type"] == "all_external_motorized_incoming_edges" for group in groups),
        "keishicho_section_groups": sum(group["source"] == "Keishicho" and group["measurement_type"] == "named_road_both_direction_cross_section" for group in groups),
        "measurement_groups": len(groups), "unique_detector_lanes": len(registry.records),
        "calibration_observation_links": sum(row["use_split"] == "calibration" for row in observation_links),
        "independent_validation_observation_links": sum(row["use_split"] == "independent_validation" for row in observation_links),
    }
    accepted = (
        counts["mlit_representative_sections"] == 21 and counts["keishicho_junction_groups"] == 5
        and counts["keishicho_section_groups"] == 1 and not physical_duplicates and not split_errors and not incomplete_groups
    )
    validation = {
        "artifact_id": "OTA_SUMO_OFFICIAL_TRAFFIC_MEASUREMENT_LOCATIONS_V1",
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "research_stage": "2-2",
        "accepted": accepted,
        "counts": counts,
        "physical_detector_duplicates": physical_duplicates,
        "cross_group_edge_reuse": cross_group_edge_reuse,
        "split_errors": split_errors,
        "incomplete_groups": incomplete_groups,
        "source_hashes": {
            "sumo_net": sha256(net_path), "mlit_mapping": sha256(mlit_mapping_path),
            "keishicho_mapping": sha256(police_mapping_path),
        },
        "deterministic_output_hashes": {
            name: sha256(output / name) for name in deterministic_outputs
        },
        "non_actions": ["no_traffic_parameter_calibration", "no_demand_change", "no_sumo_network_change", "no_osm_change"],
    }
    (output / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "COMPLETE" if accepted else "PARTIAL"
    report = f"""# 2-2 SUMO公式交通量測定位置固定

作成日: 2026-08-23
状態: `{status}`

```text
0-1 社会科学としての問い                     [PARTIAL]
0-2 研究設計                                 [CURRENT]
0-3 方法論                                   [CURRENT]
1. 道路・交通条件                           [PARTIAL]
2. 交通状態                                 [CURRENT]
 ├─ 2-1 公式観測の取得・道路対応             [COMPLETE]
 ├─ 2-2 SUMO上の観測断面・検出位置固定       [{status}]  ← この文書
 ├─ 2-3 交通量較正                           [NOT STARTED]
 └─ 2-4 未使用観測による独立確認             [NOT STARTED]
3. 配送条件                                 [PARTIAL]
4. 配送simulation                           [PARTIAL]
5. 配送最適化問題                           [NOT STARTED]
6. 計算手法比較                             [NOT STARTED]
```

## 結論

- 国交省21区間は、公式区間内部の同一断面を通る両方向SUMO edgeと全motorized laneを固定した。
- 国交省の上り・下りは公開資料だけで地理方向へ割り当てず、両方向合計で比較する。
- 警視庁5交差点は、交差点cluster外から入る全motorized edgeを1回ずつ固定した。
- 春日橋は池上通りの両方向edgeを固定し、両方向合計で比較する。
- 2021年国交省・2023年警視庁は較正用、2024年警視庁は独立確認用のまま分離した。
- 交通量パラメータ、需要、道路網、OSMは変更していない。

## 選定規則と根拠

- 国交省の交通量観測は、交通調査基本区間内の代表地点を通過する車両を方向別に数える公式定義に従った。
- 公開データだけでは上り・下りをSUMOの地理方向へ確実に対応できないため、両方向合計だけを使用する。
- 代表断面候補は公式区間の25、35、50、65、75%位置から作り、50m以内に互いに逆向きのSUMO edgeが存在し、交差点端から最も離れる組を決定的に選ぶ。
- 警視庁交差点は交差点群の外から中へ入る全motorized edgeを選ぶ。5.1m未満の人工的な分割edgeは境界内部へ吸収し、上流側の実測可能なedgeを使う。
- 春日橋は一意対応済みの池上通りだけに限定し、両方向を合計する。
- SUMO公式の車線別検出器（E1）として各motorized laneへ配置し、集計間隔は1時間とした。

参照:

- 国土交通省「令和3年度 全国道路・街路交通情勢調査 一般交通量調査結果WEBマップの閲覧方法」および調査方法資料。
- `20260823_ota_official_traffic_observation_mapping_v5/official_source_urls.json` に固定した国土交通省・警視庁の公式配布元。
- SUMO公式文書 `Induction Loops Detectors (E1)` と `Lane- or Edge-based Traffic Measures`。

## 再現条件

- 入力道路網・国交省対応表・警視庁対応表のSHA-256は `validation.json` に記録した。
- 固定した5個の主要出力のSHA-256も `validation.json` に記録した。
- 同じ入力と規則から再生成した成果物とのbyte比較を行う。

## 検証結果

```json
{json.dumps(validation['counts'], ensure_ascii=False, indent=2)}
```

受入結果: `{accepted}`

## 終了記録

- What was learned: 道路対応だけでは測定位置は決まらず、国交省は断面、警視庁は交差点境界という異なる測定単位が必要だった。
- What was decided: 国交省は両方向代表断面、警視庁交差点は全流入edge、春日橋は両方向合計断面を使用する。
- What remains unresolved: 国交省の上り・下りの地理方向割当、実交通量を再現する較正パラメータ、2024年による実証的妥当性確認。
- Whether this branch is closed: この作業は本線であり、受入結果がtrueなら2-2を完了する。
- Where we return to in the main route: `2-3 交通量較正`。
"""
    (output / f"2-2_20260823_{status}_SUMO公式交通量測定位置固定.md").write_text(report, encoding="utf-8")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validation = build(args.repo.resolve(), args.output.resolve())
    print(json.dumps(validation["counts"], ensure_ascii=False, indent=2))
    if not validation["accepted"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
