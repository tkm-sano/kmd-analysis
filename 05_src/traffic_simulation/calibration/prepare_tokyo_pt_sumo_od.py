#!/usr/bin/env python3
"""Map the public 2018 Tokyo PT automobile OD table to coarse SUMO TAZ demand.

The PT table is used only as a fixed spatial prior.  Its automobile values are
person trips, not observed vehicle counts.  Vehicle conversion and calibration
are deliberately left to the later low-dimensional calibration stage.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform, unary_union


OTA_CODES = {f"{value:04d}" for value in range(130, 139)}
HOURS = tuple(range(7, 19))
SECTORS = ("E", "NE", "N", "NW", "W", "SW", "S", "SE")
SECTORS_16 = (
    "E", "ENE", "NE", "NNE", "N", "NNW", "NW", "WNW",
    "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE",
)
BOUNDARY_TOLERANCE_M = 150.0
MIN_TAZ_EDGE_LENGTH_M = 5.1
MIN_GATEWAY_PRIORITY = 10
MIN_INWARD_PROGRESS_M = 5.0


def normalize_zone(value: Any) -> str:
    match = re.match(r"^\s*:?(\d{1,4})(?:\s|$)", str(value))
    if not match:
        raise ValueError(f"invalid PT zone token: {value!r}")
    return match.group(1).zfill(4)


def parse_number(value: str) -> float:
    return float((value or "0").replace(",", ""))


def hour_from_label(label: str) -> int | None:
    match = re.match(r"^(\d+)時台$", label.strip())
    return int(match.group(1)) if match else None


def sector_for_point(point: Point, center: Point, sectors: tuple[str, ...] = SECTORS) -> str:
    angle = math.degrees(math.atan2(point.y - center.y, point.x - center.x))
    width = 360.0 / len(sectors)
    index = int(math.floor(((angle + width / 2) % 360.0) / width))
    return sectors[index]


def safe_profile(hourly: dict[int, float], hours: tuple[int, ...] = HOURS) -> dict[int, float]:
    total = sum(max(0.0, hourly.get(hour, 0.0)) for hour in hours)
    if total <= 0:
        return {hour: 1.0 / len(hours) for hour in hours}
    return {hour: max(0.0, hourly.get(hour, 0.0)) / total for hour in hours}


def map_relation(
    origin: str,
    destination: str,
    centroids: dict[str, Point],
    ota_geometry: Any,
    sectors: tuple[str, ...] = SECTORS,
) -> tuple[str, str] | None:
    origin_inside = origin in OTA_CODES
    destination_inside = destination in OTA_CODES
    if not origin_inside and not destination_inside:
        chord = LineString([centroids[origin], centroids[destination]])
        if not chord.intersects(ota_geometry):
            return None
    center = ota_geometry.centroid
    mapped_origin = (
        f"PT_{origin}" if origin_inside else f"EXT_{sector_for_point(centroids[origin], center, sectors)}"
    )
    mapped_destination = (
        f"PT_{destination}" if destination_inside
        else f"EXT_{sector_for_point(centroids[destination], center, sectors)}"
    )
    if mapped_origin == mapped_destination and not (origin_inside and destination_inside):
        return None
    return mapped_origin, mapped_destination


def read_location(net_path: Path) -> dict[str, str]:
    for _, element in ET.iterparse(net_path, events=("end",)):
        if element.tag == "location":
            return dict(element.attrib)
        element.clear()
    raise ValueError("SUMO network location metadata is missing")


def to_sumo_geometry(geometry: Any, source_crs: Any, location: dict[str, str]) -> Any:
    projection = CRS.from_proj4(location["projParameter"])
    transformer = Transformer.from_crs(source_crs, projection, always_xy=True)
    offset_x, offset_y = map(float, location["netOffset"].split(","))

    def project(x: Any, y: Any, z: Any = None) -> tuple[Any, Any]:
        projected_x, projected_y = transformer.transform(x, y)
        return projected_x + offset_x, projected_y + offset_y

    return transform(project, geometry)


def load_zones(raw_dir: Path, location: dict[str, str]) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    archive = raw_dir / "tokyo_pt_2018_zone_geometry.zip"
    uri = f"zip://{archive}!H30_gis/H30_kzone.shp"
    frame = gpd.read_file(uri)
    zones: dict[str, Any] = {}
    for _, row in frame.iterrows():
        code = f"{int(row['kzone']):04d}"
        zones[code] = to_sumo_geometry(row.geometry, frame.crs, location)
    return frame, zones


def write_internal_polygons(path: Path, zones: dict[str, Any]) -> None:
    root = ET.Element("additional")
    for code in sorted(OTA_CODES):
        geometry = zones[code]
        parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        for index, polygon in enumerate(parts):
            simplified = polygon.simplify(0.5, preserve_topology=True)
            shape_value = " ".join(f"{x:.3f},{y:.3f}" for x, y in simplified.exterior.coords)
            ET.SubElement(root, "poly", {
                "id": f"PT_{code}__part{index}", "type": "tokyo_pt_2018_planning_basic_zone",
                "color": "0.2,0.6,1.0,0.35", "fill": "true", "layer": "-10", "shape": shape_value,
            })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def load_passenger_edges(net_path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    edges: dict[str, dict[str, Any]] = {}
    connections: dict[str, set[str]] = defaultdict(set)
    for _, element in ET.iterparse(net_path, events=("end",)):
        if element.tag == "edge" and not element.get("function"):
            lanes = []
            for lane in element.findall("lane"):
                allow = set((lane.get("allow") or "").split())
                disallow = set((lane.get("disallow") or "").split())
                permitted = "passenger" in allow if allow else "passenger" not in disallow
                if permitted and lane.get("shape"):
                    lanes.append({
                        "id": lane.get("id"), "length": float(lane.get("length")),
                        "speed": float(lane.get("speed")),
                        "shape": LineString([tuple(map(float, item.split(","))) for item in lane.get("shape").split()]),
                    })
            if lanes:
                edges[element.get("id")] = {
                    "id": element.get("id"), "from": element.get("from"), "to": element.get("to"),
                    "length": max(lane["length"] for lane in lanes), "lanes": lanes, "shape": lanes[0]["shape"],
                    "priority": int(element.get("priority", "-1")), "type": element.get("type", ""),
                }
        elif element.tag == "connection" and element.get("from") and element.get("to"):
            connections[element.get("from")].add(element.get("to"))
        if element.tag in {"edge", "connection"}:
            element.clear()
    return edges, connections


def boundary_gateways(
    edges: dict[str, dict[str, Any]], connections: dict[str, set[str]], ota_geometry: Any,
    sectors: tuple[str, ...] = SECTORS,
) -> dict[str, dict[str, list[str]]]:
    del connections  # Direction is determined geometrically within the fixed boundary band.
    result = {sector: {"sources": [], "sinks": []} for sector in sectors}
    center = ota_geometry.centroid
    for edge_id, edge in edges.items():
        if edge["length"] < MIN_TAZ_EDGE_LENGTH_M or edge["priority"] < MIN_GATEWAY_PRIORITY:
            continue
        start = Point(edge["shape"].coords[0])
        end = Point(edge["shape"].coords[-1])
        start_distance = start.distance(ota_geometry.boundary)
        end_distance = end.distance(ota_geometry.boundary)
        if (
            start_distance <= BOUNDARY_TOLERANCE_M
            and end_distance >= start_distance + MIN_INWARD_PROGRESS_M
        ):
            result[sector_for_point(start, center, sectors)]["sources"].append(edge_id)
        if (
            end_distance <= BOUNDARY_TOLERANCE_M
            and start_distance >= end_distance + MIN_INWARD_PROGRESS_M
        ):
            result[sector_for_point(end, center, sectors)]["sinks"].append(edge_id)
    for sector in sectors:
        result[sector]["sources"].sort()
        result[sector]["sinks"].sort()
    return result


def read_internal_taz(path: Path) -> dict[str, dict[str, float]]:
    collected: dict[str, dict[str, float]] = defaultdict(dict)
    root = ET.parse(path).getroot()
    for taz in root.iter("taz"):
        taz_id = (taz.get("id") or "").split("__", 1)[0]
        edges = (taz.get("edges") or "").split()
        if edges:
            for edge_id in edges:
                collected[taz_id][edge_id] = max(collected[taz_id].get(edge_id, 0.0), 1.0)
        else:
            for item in taz.findall("tazSource"):
                edge_id = item.get("id")
                if edge_id:
                    weight = float(item.get("weight", "1"))
                    collected[taz_id][edge_id] = max(collected[taz_id].get(edge_id, 0.0), weight)
    return {taz_id: dict(sorted(edges.items())) for taz_id, edges in collected.items()}


def write_final_taz(
    path: Path, internal: dict[str, dict[str, float]], gateways: dict[str, dict[str, list[str]]],
    sectors: tuple[str, ...] = SECTORS,
) -> None:
    root = ET.Element("additional")
    for taz_id, edges in sorted(internal.items()):
        taz = ET.SubElement(root, "taz", {"id": taz_id})
        for edge_id, weight in edges.items():
            value = f"{weight:.6f}"
            ET.SubElement(taz, "tazSource", {"id": edge_id, "weight": value})
            ET.SubElement(taz, "tazSink", {"id": edge_id, "weight": value})
    for sector in sectors:
        taz = ET.SubElement(root, "taz", {"id": f"EXT_{sector}"})
        for edge_id in gateways[sector]["sources"]:
            ET.SubElement(taz, "tazSource", {"id": edge_id, "weight": "1"})
        for edge_id in gateways[sector]["sinks"]:
            ET.SubElement(taz, "tazSink", {"id": edge_id, "weight": "1"})
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def read_departure_profiles(raw_dir: Path, valid_zones: set[str]) -> dict[str, dict[int, float]]:
    path = raw_dir / "tokyo_pt_2018_zone_mode_hour_trip_ends.csv"
    values: dict[str, dict[int, float]] = defaultdict(dict)
    with path.open(encoding="cp932", newline="") as stream:
        rows = csv.reader(stream)
        for _ in range(5):
            next(rows)
        for row in rows:
            if len(row) < 29:
                continue
            try:
                zone = normalize_zone(row[0])
            except ValueError:
                continue
            hour = hour_from_label(row[1])
            if zone in valid_zones and hour in HOURS:
                values[zone][hour] = parse_number(row[4])
    return {zone: safe_profile(values.get(zone, {})) for zone in valid_zones}


def aggregate_hourly_od(
    raw_dir: Path, zones: dict[str, Any], ota_geometry: Any,
    sectors: tuple[str, ...] = SECTORS,
) -> tuple[dict[tuple[int, str, str], float], dict[str, Any]]:
    valid = set(zones)
    centroids = {code: geometry.centroid for code, geometry in zones.items()}
    profiles = read_departure_profiles(raw_dir, valid)
    totals: dict[tuple[int, str, str], float] = defaultdict(float)
    accounting = Counter()
    path = raw_dir / "tokyo_pt_2018_od_by_purpose_and_main_mode.csv"
    with path.open(encoding="cp932", newline="") as stream:
        rows = csv.reader(stream)
        for _ in range(5):
            next(rows)
        for row in rows:
            if len(row) < 12 or row[2] != "計":
                continue
            try:
                origin, destination = normalize_zone(row[0]), normalize_zone(row[1])
            except ValueError:
                continue
            if origin not in valid or destination not in valid:
                accounting["aggregate_or_unknown_zone_rows_excluded"] += 1
                continue
            automobile_person_trips = parse_number(row[5])
            if automobile_person_trips <= 0:
                continue
            mapped = map_relation(origin, destination, centroids, ota_geometry, sectors)
            if mapped is None:
                accounting["outside_non_traversing_person_trips_excluded"] += round(automobile_person_trips)
                continue
            for hour, fraction in profiles[origin].items():
                totals[(hour, mapped[0], mapped[1])] += automobile_person_trips * fraction
            accounting["included_daily_automobile_person_trips"] += round(automobile_person_trips)
    return totals, dict(accounting)


def write_relations(path: Path, totals: dict[tuple[int, str, str], float]) -> None:
    root = ET.Element("data")
    for hour in HOURS:
        interval = ET.SubElement(root, "interval", {
            "id": "passenger", "begin": str(hour * 3600), "end": str((hour + 1) * 3600),
        })
        for (_, origin, destination), count in sorted(
            ((key, value) for key, value in totals.items() if key[0] == hour),
            key=lambda item: (item[0][1], item[0][2]),
        ):
            if count >= 0.5:
                ET.SubElement(interval, "tazRelation", {
                    "from": origin, "to": destination, "count": f"{count:.6f}",
                })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--net", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--internal-taz", type=Path)
    parser.add_argument("--external-sector-count", type=int, choices=(8, 16), default=8)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sectors = SECTORS if args.external_sector_count == 8 else SECTORS_16
    location = read_location(args.net)
    _, zones = load_zones(args.raw_dir, location)
    ota_geometry = unary_union([zones[code] for code in OTA_CODES])
    if args.internal_taz is None:
        write_internal_polygons(output / "pt_internal_zones.poly.xml", zones)
        print(json.dumps({"stage": "polygons", "ota_zones": len(OTA_CODES)}, ensure_ascii=False))
        return
    internal = read_internal_taz(args.internal_taz)
    expected_internal = {f"PT_{code}" for code in OTA_CODES}
    if set(internal) != expected_internal:
        raise ValueError(f"unexpected internal TAZ ids: {sorted(internal)}")
    edges, connections = load_passenger_edges(args.net)
    gateways = boundary_gateways(edges, connections, ota_geometry, sectors)
    empty = [sector for sector, value in gateways.items() if not value["sources"] or not value["sinks"]]
    if empty:
        raise ValueError(f"external sectors without both source and sink edges: {empty}")
    write_final_taz(output / "tokyo_pt_ota.taz.xml", internal, gateways, sectors)
    totals, accounting = aggregate_hourly_od(args.raw_dir, zones, ota_geometry, sectors)
    write_relations(output / "tokyo_pt_automobile_person_trips_07_19.taz_relations.xml", totals)
    summary = {
        "artifact_id": "TOKYO_PT_2018_TO_OTA_SUMO_TAZ_OD_V1",
        "internal_taz_count": len(internal), "external_taz_count": len(gateways),
        "external_sector_count": len(sectors),
        "gateway_counts": {sector: {key: len(value) for key, value in record.items()} for sector, record in gateways.items()},
        "gateway_model_assumption": {
            "boundary_tolerance_m": BOUNDARY_TOLERANCE_M,
            "minimum_directed_progress_m": MIN_INWARD_PROGRESS_M,
            "minimum_sumo_edge_priority": MIN_GATEWAY_PRIORITY,
            "meaning": "区境帯内で区内方向へ進む幹線道路を入口、逆向きを出口とする",
        },
        "hourly_relation_count": len(totals),
        "hours": list(HOURS), "accounting": accounting,
        "semantic_warning": "PT automobile values are person trips, not vehicle counts",
        "calibration_status": "spatial_prior_only_not_yet_calibrated",
    }
    (output / "taz_od_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
