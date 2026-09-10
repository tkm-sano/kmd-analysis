#!/usr/bin/env python3
"""Prepare H30 Tokyo PT small-zone driver OD for spatial-support diagnosis.

Only rows labelled ``1_運転した`` are treated as vehicle demand. Aggregate,
unknown and other-area rows are excluded by requiring both endpoint codes to
exist in the official H30 small-zone geometry.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union

from prepare_tokyo_pt_sumo_od import (
    BOUNDARY_TOLERANCE_M,
    MIN_GATEWAY_PRIORITY,
    MIN_INWARD_PROGRESS_M,
    MIN_TAZ_EDGE_LENGTH_M,
    load_passenger_edges,
    HOURS,
    read_departure_profiles,
    read_internal_taz,
    read_location,
    to_sumo_geometry,
)


DRIVER_LABEL = "1_運転した"
SURVEY_YEAR = "平成３０年"
OTA_JIS_CODE = 13111
EXTERNAL_GATEWAYS_PER_ZONE = 3
FILE_ROLES = {
    "ota_to_ota_small_zone_od.csv": "internal",
    "ota_to_all_small_zone_od.csv": "outbound",
    "all_to_ota_small_zone_od.csv": "inbound",
}


def parse_small_zone_token(value: str) -> str | None:
    """Return the trailing official five-digit zone code, not totals/other."""
    match = re.search(r"(?:^|_)(\d{5}):$", (value or "").strip())
    return match.group(1) if match else None


def parent_basic_zone(small_zone: str) -> str:
    """Map an official five-digit small zone to its four-digit parent zone."""
    if not re.fullmatch(r"\d{5}", small_zone):
        raise ValueError(f"invalid small-zone code: {small_zone!r}")
    return small_zone[:4]


def expand_hourly_od(
    daily: dict[tuple[str, str], float], profiles: dict[str, dict[int, float]]
) -> tuple[dict[tuple[int, str, str], float], set[str]]:
    """Apply the origin parent-zone profile without changing daily OD shares."""
    hourly: dict[tuple[int, str, str], float] = {}
    fallback_parents: set[str] = set()
    uniform = {hour: 1.0 / len(HOURS) for hour in HOURS}
    for (origin, destination), count in daily.items():
        parent = parent_basic_zone(origin)
        profile = profiles.get(parent)
        if profile is None:
            profile = uniform
            fallback_parents.add(parent)
        for hour in HOURS:
            hourly[(hour, origin, destination)] = count * profile[hour]
    return dict(sorted(hourly.items())), fallback_parents


def load_small_zones(raw_public_dir: Path, location: dict[str, str]) -> tuple[dict[str, Any], set[str]]:
    archive = raw_public_dir / "tokyo_pt_2018_zone_geometry.zip"
    frame = gpd.read_file(f"zip://{archive}!H30_gis/H30_szone.shp")
    zones: dict[str, Any] = {}
    ota: set[str] = set()
    for _, row in frame.iterrows():
        code = f"{int(row['szone']):05d}"
        zones[code] = to_sumo_geometry(row.geometry, frame.crs, location)
        if int(row["JisCode"]) == OTA_JIS_CODE:
            ota.add(code)
    if len(zones) != 1660 or len(ota) != 15:
        raise ValueError(f"unexpected official small-zone population: all={len(zones)}, ota={len(ota)}")
    return zones, ota


def read_driver_od(
    raw_dir: Path, valid_zones: set[str], ota_zones: set[str]
) -> tuple[dict[tuple[str, str], float], dict[str, Any]]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    accounting = Counter()
    accepted_by_file = Counter()
    for filename, role in FILE_ROLES.items():
        path = raw_dir / filename
        with path.open(encoding="cp932", newline="") as stream:
            for row in csv.DictReader(stream):
                accounting["input_rows"] += 1
                if row["調査年"] != SURVEY_YEAR:
                    accounting["wrong_year_rows_excluded"] += 1
                    continue
                if row["運転有無"] != DRIVER_LABEL:
                    accounting["non_driver_rows_excluded"] += 1
                    continue
                origin = parse_small_zone_token(row["発ゾーン"])
                destination = parse_small_zone_token(row["着ゾーン"])
                if origin not in valid_zones or destination not in valid_zones:
                    accounting["aggregate_unknown_or_other_rows_excluded"] += 1
                    continue
                correct_direction = (
                    role == "internal" and origin in ota_zones and destination in ota_zones
                    or role == "outbound" and origin in ota_zones and destination not in ota_zones
                    or role == "inbound" and origin not in ota_zones and destination in ota_zones
                )
                if not correct_direction:
                    accounting["overlap_or_direction_rows_excluded"] += 1
                    continue
                count = float(row["トリップ数"].replace(",", ""))
                if count <= 0:
                    accounting["nonpositive_rows_excluded"] += 1
                    continue
                totals[(origin, destination)] += count
                accepted_by_file[filename] += 1
                accounting["accepted_rows"] += 1
                accounting["accepted_driver_trips"] += round(count)
    return dict(sorted(totals.items())), {
        **dict(accounting),
        "accepted_rows_by_file": dict(sorted(accepted_by_file.items())),
    }


def write_small_zone_polygons(path: Path, zones: dict[str, Any], ota_zones: set[str]) -> None:
    root = ET.Element("additional")
    for code in sorted(ota_zones):
        geometry = zones[code]
        parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        for index, polygon in enumerate(parts):
            simplified = polygon.simplify(0.5, preserve_topology=True)
            shape = " ".join(f"{x:.3f},{y:.3f}" for x, y in simplified.exterior.coords)
            ET.SubElement(root, "poly", {
                "id": f"PT_SZ_{code}__part{index}",
                "type": "tokyo_pt_2018_small_zone",
                "color": "0.2,0.6,1.0,0.35",
                "fill": "true",
                "layer": "-10",
                "shape": shape,
            })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def gateway_candidates(edges: dict[str, dict[str, Any]], ota_geometry: Any) -> dict[str, list[tuple[str, Point]]]:
    result: dict[str, list[tuple[str, Point]]] = {"sources": [], "sinks": []}
    for edge_id, edge in edges.items():
        if edge["length"] < MIN_TAZ_EDGE_LENGTH_M or edge["priority"] < MIN_GATEWAY_PRIORITY:
            continue
        start = Point(edge["shape"].coords[0])
        end = Point(edge["shape"].coords[-1])
        start_distance = start.distance(ota_geometry.boundary)
        end_distance = end.distance(ota_geometry.boundary)
        if start_distance <= BOUNDARY_TOLERANCE_M and end_distance >= start_distance + MIN_INWARD_PROGRESS_M:
            result["sources"].append((edge_id, start))
        if end_distance <= BOUNDARY_TOLERANCE_M and start_distance >= end_distance + MIN_INWARD_PROGRESS_M:
            result["sinks"].append((edge_id, end))
    for role in result:
        result[role].sort(key=lambda item: item[0])
    if not result["sources"] or not result["sinks"]:
        raise ValueError("no directed boundary gateway candidates")
    return result


def nearest_gateways(
    point: Point, candidates: list[tuple[str, Point]], count: int = EXTERNAL_GATEWAYS_PER_ZONE
) -> dict[str, float]:
    selected = sorted(candidates, key=lambda item: (point.distance(item[1]), item[0]))[:count]
    inverse = [(edge_id, 1.0 / max(point.distance(location), 1.0)) for edge_id, location in selected]
    total = sum(weight for _, weight in inverse)
    return {edge_id: weight / total for edge_id, weight in inverse}


def write_final_taz(
    path: Path,
    internal: dict[str, dict[str, float]],
    zones: dict[str, Any],
    external_used: set[str],
    candidates: dict[str, list[tuple[str, Point]]],
) -> dict[str, dict[str, int]]:
    root = ET.Element("additional")
    counts: dict[str, dict[str, int]] = {}
    for taz_id, edges in sorted(internal.items()):
        taz = ET.SubElement(root, "taz", {"id": taz_id})
        for edge_id, weight in edges.items():
            ET.SubElement(taz, "tazSource", {"id": edge_id, "weight": f"{weight:.6f}"})
            ET.SubElement(taz, "tazSink", {"id": edge_id, "weight": f"{weight:.6f}"})
        counts[taz_id] = {"sources": len(edges), "sinks": len(edges)}
    for code in sorted(external_used):
        taz_id = f"PT_SZ_{code}"
        taz = ET.SubElement(root, "taz", {"id": taz_id})
        source_weights = nearest_gateways(zones[code].centroid, candidates["sources"])
        sink_weights = nearest_gateways(zones[code].centroid, candidates["sinks"])
        for edge_id, weight in source_weights.items():
            ET.SubElement(taz, "tazSource", {"id": edge_id, "weight": f"{weight:.9f}"})
        for edge_id, weight in sink_weights.items():
            ET.SubElement(taz, "tazSink", {"id": edge_id, "weight": f"{weight:.9f}"})
        counts[taz_id] = {"sources": len(source_weights), "sinks": len(sink_weights)}
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return counts


def write_relations(path: Path, totals: dict[tuple[str, str], float]) -> None:
    root = ET.Element("data")
    interval = ET.SubElement(root, "interval", {"id": "passenger", "begin": "25200", "end": "68400"})
    for (origin, destination), count in sorted(totals.items()):
        ET.SubElement(interval, "tazRelation", {
            "from": f"PT_SZ_{origin}", "to": f"PT_SZ_{destination}", "count": f"{count:.6f}",
        })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_assignment_relations(path: Path, totals: dict[tuple[str, str], float]) -> None:
    """Write daily OD for one static route-choice pass on the relative clock."""
    root = ET.Element("data")
    interval = ET.SubElement(root, "interval", {"id": "passenger", "begin": "0", "end": "43200"})
    for (origin, destination), count in sorted(totals.items()):
        ET.SubElement(interval, "tazRelation", {
            "from": f"PT_SZ_{origin}", "to": f"PT_SZ_{destination}", "count": f"{count:.6f}",
        })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_hourly_relations(path: Path, totals: dict[tuple[int, str, str], float]) -> None:
    """Write 07:00--19:00 source hours on a simulation-relative 0--43200 clock."""
    root = ET.Element("data")
    for hour in HOURS:
        begin = (hour - HOURS[0]) * 3600
        interval = ET.SubElement(root, "interval", {
            "id": f"passenger_{hour:02d}", "begin": str(begin), "end": str(begin + 3600),
        })
        for (_, origin, destination), count in (
            (key, value) for key, value in totals.items() if key[0] == hour
        ):
            ET.SubElement(interval, "tazRelation", {
                "from": f"PT_SZ_{origin}", "to": f"PT_SZ_{destination}",
                "count": f"{count:.9f}",
            })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-small-zone-od", type=Path, required=True)
    parser.add_argument("--raw-public-pt", type=Path, required=True)
    parser.add_argument("--net", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--internal-taz", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    location = read_location(args.net)
    zones, ota_zones = load_small_zones(args.raw_public_pt, location)
    totals, accounting = read_driver_od(args.raw_small_zone_od, set(zones), ota_zones)
    parent_zones = {parent_basic_zone(origin) for origin, _ in totals}
    profiles = read_departure_profiles(args.raw_public_pt, parent_zones)
    hourly, fallback_parents = expand_hourly_od(totals, profiles)
    if args.internal_taz is None:
        write_small_zone_polygons(args.output / "ota_small_zones.poly.xml", zones, ota_zones)
        write_relations(args.output / "small_zone_driver_daily.taz_relations.xml", totals)
        write_assignment_relations(args.output / "small_zone_driver_assignment_relative.taz_relations.xml", totals)
        write_hourly_relations(args.output / "small_zone_driver_hourly_07_19.taz_relations.xml", hourly)
        print(json.dumps({"stage": "polygons", "ota_small_zones": len(ota_zones)}, ensure_ascii=False))
        return
    internal = read_internal_taz(args.internal_taz)
    expected = {f"PT_SZ_{code}" for code in ota_zones}
    if set(internal) != expected:
        raise ValueError(f"unexpected internal small-zone TAZ ids: {sorted(internal)}")
    edges, _ = load_passenger_edges(args.net)
    ota_geometry = unary_union([zones[code] for code in ota_zones])
    candidates = gateway_candidates(edges, ota_geometry)
    used = {code for pair in totals for code in pair}
    external_used = used - ota_zones
    connector_counts = write_final_taz(
        args.output / "small_zone_driver.taz.xml", internal, zones, external_used, candidates
    )
    write_relations(args.output / "small_zone_driver_daily.taz_relations.xml", totals)
    write_assignment_relations(args.output / "small_zone_driver_assignment_relative.taz_relations.xml", totals)
    write_hourly_relations(args.output / "small_zone_driver_hourly_07_19.taz_relations.xml", hourly)
    summary = {
        "artifact_id": "TOKYO_PT_2018_SMALL_ZONE_DRIVER_OD_V1",
        "semantic_type": "external_observed_expanded_driver_vehicle_trips",
        "survey_year": 2018,
        "driver_filter": DRIVER_LABEL,
        "ota_small_zone_count": len(ota_zones),
        "external_small_zone_count_used": len(external_used),
        "od_relation_count": len(totals),
        "driver_trip_total": round(sum(totals.values())),
        "hourly_driver_trip_total": round(sum(hourly.values())),
        "time_origin": {
            "simulation_second_0": "07:00 survey time",
            "simulation_end_second": 43200,
            "source_hours": list(HOURS),
            "rule": "origin small-zone inherits its official four-digit parent-zone automobile departure profile",
            "semantic_type": "model_assumed_temporal_prior",
            "fallback_parent_zones": sorted(fallback_parents),
        },
        "accounting": accounting,
        "external_gateway_rule": {
            "gateways_per_external_zone": EXTERNAL_GATEWAYS_PER_ZONE,
            "selection": "nearest directed Ota-boundary passenger edges to official external small-zone centroid",
            "weight": "normalized inverse centroid-to-boundary-endpoint distance",
            "observation_values_used": False,
        },
        "connector_counts": connector_counts,
        "calibration_status": "spatial_support_diagnosis_only_not_calibrated",
    }
    (args.output / "small_zone_driver_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
