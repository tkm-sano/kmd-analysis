#!/usr/bin/env python3
"""Map MLIT R3 Road Traffic Census sections to SUMO edges.

This pipeline keeps three things separate:

* Road Traffic Census observations and road attributes.
* OSM/SUMO network identity and geometry.
* Model-facing calibration inputs derived from explicit, reviewable matches.

It never rewrites raw Census data, OSM, or SUMO networks.  Ambiguous or
under-supported cases are emitted as ``manual_review_required`` or
``unresolved`` rather than forced into a nearest-neighbor match.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from numbers import Integral
from pathlib import Path
from typing import Any, Iterable

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DEFAULT_CONFIG = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
)
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
HOUR_ORDER = list(range(7, 24)) + list(range(0, 7))
VEHICLE_CLASS = {"1": "small", "2": "large"}
DIRECTION = {"1": "up", "2": "down"}


@dataclass(frozen=True)
class MatchThresholds:
    candidate_buffer_m: float
    high_overlap_ratio: float
    medium_overlap_ratio: float
    high_section_coverage_ratio: float
    medium_section_coverage_ratio: float
    max_high_angle_difference_deg: float
    max_medium_angle_difference_deg: float
    route_ref_required_for_high: bool
    name_match_can_support_medium: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_cp932(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="cp932", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value: str | None) -> int | None:
    text = (value or "").strip().translate(FULLWIDTH_DIGITS)
    if not text or not re.fullmatch(r"-?\d+", text):
        return None
    return int(text)


def as_float(value: str | None) -> float | None:
    text = (value or "").strip().translate(FULLWIDTH_DIGITS)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_road_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").lower()
    text = re.sub(r"[\s　・･()（）\[\]【】]", "", text)
    for token in ("一般国道", "国道", "都道", "主要地方道", "号線", "線", "通り", "道路"):
        text = text.replace(token, "")
    return text


def normalize_route_ref(value: str | None) -> set[str]:
    text = unicodedata.normalize("NFKC", value or "")
    parts = re.split(r"[;,/、\s]+", text)
    refs: set[str] = set()
    for part in parts:
        stripped = re.sub(r"[^0-9A-Za-z]", "", part)
        if stripped:
            refs.add(stripped.upper())
    return refs


def route_matches(census_route_number: str | None, osm_ref: str | None) -> str:
    expected = normalize_route_ref(census_route_number)
    observed = normalize_route_ref(osm_ref)
    if not expected or not observed:
        return "unknown"
    return "match" if expected & observed else "mismatch"


def name_matches(census_route_name: str | None, osm_name: str | None) -> str:
    left = normalize_road_name(census_route_name)
    right = normalize_road_name(osm_name)
    if not left or not right:
        return "unknown"
    return "match" if left == right or left in right or right in left else "mismatch"


def angle_difference_deg(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    diff = abs((a - b + 180.0) % 360.0 - 180.0)
    return min(diff, 180.0 - diff)


def bearing_from_coords(coords: list[tuple[float, float]]) -> float | None:
    if len(coords) < 2:
        return None
    x1, y1 = coords[0]
    x2, y2 = coords[-1]
    if x1 == x2 and y1 == y2:
        return None
    return (math.degrees(math.atan2(x2 - x1, y2 - y1)) + 360.0) % 360.0


def representative_coords(geometry: Any) -> list[tuple[float, float]]:
    """Return start/end coordinates for LineString or MultiLineString geometry."""
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return list(geometry.coords)
    if geometry.geom_type == "MultiLineString":
        lines = [part for part in geometry.geoms if not part.is_empty and part.length > 0]
        if not lines:
            return []
        lines.sort(key=lambda part: part.length, reverse=True)
        return list(lines[0].coords)
    if hasattr(geometry, "geoms"):
        coords: list[tuple[float, float]] = []
        for part in geometry.geoms:
            coords = representative_coords(part)
            if coords:
                return coords
    return []


def geometry_bearing_deg(geometry: Any) -> float | None:
    return bearing_from_coords(representative_coords(geometry))


def confidence_for_candidate(
    overlap_ratio: float,
    coverage_ratio: float,
    angle_diff: float | None,
    route_match: str,
    name_match: str,
    thresholds: MatchThresholds,
) -> tuple[str, bool, str]:
    angle_high = angle_diff is not None and angle_diff <= thresholds.max_high_angle_difference_deg
    angle_medium = angle_diff is not None and angle_diff <= thresholds.max_medium_angle_difference_deg
    route_high_ok = route_match == "match" or not thresholds.route_ref_required_for_high
    if (
        overlap_ratio >= thresholds.high_overlap_ratio
        and coverage_ratio >= thresholds.high_section_coverage_ratio
        and angle_high
        and route_high_ok
    ):
        return "high", False, "spatial_direction_route_rule"
    if (
        overlap_ratio >= thresholds.medium_overlap_ratio
        and coverage_ratio >= thresholds.medium_section_coverage_ratio
        and angle_medium
        and route_match != "mismatch"
        and (route_match == "match" or name_match == "match" or thresholds.name_match_can_support_medium)
    ):
        return "medium", route_match != "match", "spatial_direction_partial_identity_rule"
    reason = "route_mismatch" if route_match == "mismatch" else "insufficient_spatial_or_directional_support"
    return "low", True, reason


def aggregate_match_status(statuses: Iterable[str]) -> str:
    """Aggregate identity evidence without hiding an explicit mismatch."""
    values = {value for value in statuses if value and value != "unknown"}
    if not values:
        return "unknown"
    if values == {"match"}:
        return "match"
    if values == {"mismatch"}:
        return "mismatch"
    return "mixed_mismatch"


def _directed_turn_difference_deg(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 0.0
    return abs((a - b + 180.0) % 360.0 - 180.0)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise ValueError("unsupported road census mapping config")
    return config


def thresholds_from_config(config: dict[str, Any]) -> MatchThresholds:
    data = config["matching"]
    return MatchThresholds(
        candidate_buffer_m=float(data["candidate_buffer_m"]),
        high_overlap_ratio=float(data["high_overlap_ratio"]),
        medium_overlap_ratio=float(data["medium_overlap_ratio"]),
        high_section_coverage_ratio=float(data["high_section_coverage_ratio"]),
        medium_section_coverage_ratio=float(data["medium_section_coverage_ratio"]),
        max_high_angle_difference_deg=float(data["max_high_angle_difference_deg"]),
        max_medium_angle_difference_deg=float(data["max_medium_angle_difference_deg"]),
        route_ref_required_for_high=bool(data["route_ref_required_for_high"]),
        name_match_can_support_medium=bool(data["name_match_can_support_medium"]),
    )


def normalize_sections(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        section_id = row["交通調査基本区間番号"]
        total_lanes = as_int(row.get("車線数"))
        output.append(
            {
                "census_section_id": section_id,
                "generation_tens": row.get("世代管理番号（十の位）", ""),
                "generation_ones": row.get("世代管理番号（一の位）", ""),
                "road_type_code": row.get("道路種別", ""),
                "route_number": row.get("路線番号", ""),
                "route_name": row.get("路線名", ""),
                "municipality_code": row.get("市区町村コード", ""),
                "section_length_km": as_float(row.get("区間延長（ｋｍ）")),
                "total_lanes": total_lanes,
                "roadway_width_m": as_float(row.get("幅員構成／道路部幅員（ｍ）")),
                "carriageway_width_m": as_float(row.get("幅員構成／車道部幅員（ｍ）")),
                "lane_width_m": as_float(row.get("幅員構成／車道幅員（ｍ）")),
                "median_width_m": as_float(row.get("幅員構成／中央帯幅員（ｍ）")),
                "oneway_flag": row.get("一方通行フラグ", ""),
                "traffic_unit_prefecture_code": row.get("交通量／都道府県指定市コード", ""),
                "traffic_unit_id": row.get("交通量／調査単位区間番号", ""),
                "up_observation_section_id": row.get("上り／観測地点交通調査基本区間番号", ""),
                "down_observation_section_id": row.get("下り／観測地点交通調査基本区間番号", ""),
                "up_observation_flag": row.get("上り／令和３年度調査交通量観測・非観測の別", ""),
                "down_observation_flag": row.get("下り／令和３年度調査交通量観測・非観測の別", ""),
                "source_file": "kasyo13.csv",
                "source_row_id": section_id,
            }
        )
    return output


def normalize_hourly_traffic(
    hourly_rows: list[dict[str, str]],
    section_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    unit_to_targets: dict[tuple[str, str], dict[str, str]] = {}
    for row in section_rows:
        unit = row.get("交通量／調査単位区間番号", "")
        if not unit:
            continue
        unit_to_targets[(unit, "up")] = {
            "census_section_id": row.get("上り／観測地点交通調査基本区間番号", ""),
            "observation_flag": row.get("上り／令和３年度調査交通量観測・非観測の別", ""),
        }
        unit_to_targets[(unit, "down")] = {
            "census_section_id": row.get("下り／観測地点交通調査基本区間番号", ""),
            "observation_flag": row.get("下り／令和３年度調査交通量観測・非観測の別", ""),
        }

    grouped: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in hourly_rows:
        direction = DIRECTION.get(row.get("上り・下りの別", ""), "unknown")
        unit = row.get("交通量調査単位区間番号", "")
        target = unit_to_targets.get((unit, direction), {})
        census_section_id = target.get("census_section_id") or ""
        vehicle_class = VEHICLE_CLASS.get(row.get("車種区分", ""), f"code_{row.get('車種区分', '')}")
        for hour in HOUR_ORDER:
            label = str(hour).translate(str.maketrans("0123456789", "０１２３４５６７８９"))
            count = as_int(row.get(f"時間帯別自動車類交通量（台／時）／{label}時台"))
            key = (unit, direction, hour)
            item = grouped.setdefault(
                key,
                {
                    "census_section_id": census_section_id,
                    "traffic_unit_id": unit,
                    "direction": direction,
                    "hour": hour,
                    "begin": f"{hour:02d}:00:00",
                    "end": f"{(hour + 1) % 24:02d}:00:00",
                    "small_vehicle_count": None,
                    "large_vehicle_count": None,
                    "total_vehicle_count": 0,
                    "observation_flag": target.get("observation_flag") or row.get("令和３年度調査交通量観測・非観測の別", ""),
                    "survey_date": row.get("交通量観測年月日", ""),
                    "weather_code": row.get("天候", ""),
                    "source_file": "zkntrf13.csv",
                },
            )
            if count is None:
                continue
            if vehicle_class == "small":
                item["small_vehicle_count"] = count
            elif vehicle_class == "large":
                item["large_vehicle_count"] = count
            item["total_vehicle_count"] = (item["small_vehicle_count"] or 0) + (item["large_vehicle_count"] or 0)
    return list(grouped.values())


def qa_sections_and_traffic(
    sections: list[dict[str, Any]],
    hourly: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    section_ids = [row["census_section_id"] for row in sections]
    known = set(section_ids)
    for section_id, count in Counter(section_ids).items():
        if count > 1:
            issues.append({"check": "duplicate_census_section_id", "severity": "error", "id": section_id, "count": count})
    for row in sections:
        for field in ("census_section_id", "route_number", "route_name"):
            if not row.get(field):
                issues.append({"check": "missing_required_section_field", "severity": "warning", "id": row["census_section_id"], "field": field})
        if row.get("total_lanes") is not None and row["total_lanes"] <= 0:
            issues.append({"check": "non_positive_lane_count", "severity": "error", "id": row["census_section_id"], "value": row["total_lanes"]})
    for row in hourly:
        if row["census_section_id"] and row["census_section_id"] not in known:
            issues.append({"check": "hourly_section_id_not_in_basic_table", "severity": "error", "id": row["census_section_id"], "traffic_unit_id": row["traffic_unit_id"]})
        if row["direction"] == "unknown":
            issues.append({"check": "unknown_direction", "severity": "warning", "id": row["census_section_id"], "traffic_unit_id": row["traffic_unit_id"]})
        if row["hour"] not in range(24):
            issues.append({"check": "invalid_hour", "severity": "error", "id": row["census_section_id"], "hour": row["hour"]})
        for field in ("small_vehicle_count", "large_vehicle_count", "total_vehicle_count"):
            value = row.get(field)
            if value is not None and value < 0:
                issues.append({"check": "negative_traffic_count", "severity": "error", "id": row["census_section_id"], "field": field, "value": value})
    return issues


def _require_geometry_deps() -> None:
    try:
        import pyproj  # noqa: F401
        import shapely  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "geometry matching requires the repository Conda environment "
            "(.conda; see reproducibility/environment/README.md)"
        ) from exc


def parse_sumo_location(root: ET.Element):
    from pyproj import CRS, Transformer

    location = root.find("location")
    if location is None:
        raise ValueError("SUMO net.xml has no location element")
    offset_x, offset_y = (float(x) for x in location.get("netOffset", "0,0").split(","))
    crs = CRS.from_proj4(location.get("projParameter"))
    transformer = Transformer.from_crs(4326, crs, always_xy=True)
    return transformer, offset_x, offset_y


def project_geometry_to_sumo(geometry, transformer, offset_x: float, offset_y: float):
    from shapely.ops import transform

    projected = transform(transformer.transform, geometry)
    return transform(lambda x, y, z=None: (x + offset_x, y + offset_y), projected)


def load_osm_way_tags(osm_path: Path) -> dict[str, dict[str, str]]:
    tags_by_way: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way":
            tags_by_way[element.get("id", "")] = {
                tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
            }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return tags_by_way


def load_sumo_edges(net_path: Path, osm_tags: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    _require_geometry_deps()
    from shapely.geometry import LineString

    tree = ET.parse(net_path)
    root = tree.getroot()
    successors: dict[str, set[str]] = defaultdict(set)
    for connection in root.findall("connection"):
        from_edge = connection.get("from", "")
        to_edge = connection.get("to", "")
        if from_edge and to_edge and not from_edge.startswith(":") and not to_edge.startswith(":"):
            successors[from_edge].add(to_edge)
    edges: list[dict[str, Any]] = []
    for edge in root.findall("edge"):
        if edge.get("function") or edge.get("id", "").startswith(":"):
            continue
        lanes = edge.findall("lane")
        if not lanes:
            continue
        lane = lanes[0]
        shape = lane.get("shape", "")
        coords = [tuple(float(v) for v in pair.split(",")) for pair in shape.split() if "," in pair]
        if len(coords) < 2:
            continue
        orig_ids = []
        for param in lane.findall("param"):
            if param.get("key") == "origId":
                orig_ids = [item for item in re.split(r"[ ;,]+", param.get("value", "")) if item]
        if not orig_ids:
            m = re.match(r"^-?(\d+)", edge.get("id", ""))
            if m:
                orig_ids = [m.group(1)]
        tags: dict[str, str] = {}
        for orig in orig_ids:
            tags.update(osm_tags.get(orig, {}))
        edge_lanes = len(lanes)
        lanes_tag = tags.get("lanes", "")
        explicit_lanes = as_int(lanes_tag)
        edges.append(
            {
                "sumo_edge_id": edge.get("id", ""),
                "from_node": edge.get("from", ""),
                "to_node": edge.get("to", ""),
                "geometry": LineString(coords),
                "edge_length_m": as_float(lane.get("length")) or LineString(coords).length,
                "osm_way_ids": ";".join(orig_ids),
                "ref": tags.get("ref", ""),
                "name": tags.get("name", "") or tags.get("name:ja", ""),
                "highway": tags.get("highway", edge.get("type", "")),
                "lanes": explicit_lanes,
                "sumo_lane_count": edge_lanes,
                "oneway": tags.get("oneway", ""),
                "bearing_deg": bearing_from_coords(coords),
                "internal": False,
                "_successor_edge_ids": successors.get(edge.get("id", ""), set()),
            }
        )
    return edges


def load_census_geometries(tile_dir: Path, section_ids: set[str], transformer, offset_x: float, offset_y: float) -> dict[str, Any]:
    _require_geometry_deps()
    from shapely.geometry import shape
    from shapely.ops import unary_union

    fragments: dict[str, list[Any]] = defaultdict(list)
    for path in sorted(tile_dir.glob("*.geojson")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            census_id = str(feature.get("properties", {}).get("census", ""))
            if census_id in section_ids:
                fragments[census_id].append(shape(feature["geometry"]))
    return {
        census_id: project_geometry_to_sumo(unary_union(parts), transformer, offset_x, offset_y)
        for census_id, parts in fragments.items()
    }


def extract_sumo_edge_attributes(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for edge in edges:
        rows.append({k: v for k, v in edge.items() if k != "geometry" and not k.startswith("_")})
    return rows


def _candidate_edge_features(
    section: dict[str, Any], section_geom: Any, edges: list[dict[str, Any]], tree: Any,
    geom_id_to_index: dict[int, int], thresholds: MatchThresholds,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for candidate in tree.query(section_geom.buffer(thresholds.candidate_buffer_m)):
        idx = int(candidate) if isinstance(candidate, Integral) else geom_id_to_index[id(candidate)]
        edge = edges[idx]
        edge_geom = edge["geometry"]
        distance = section_geom.distance(edge_geom)
        if distance > thresholds.candidate_buffer_m:
            continue
        overlap = edge_geom.intersection(section_geom.buffer(thresholds.candidate_buffer_m)).length / max(edge_geom.length, 0.001)
        coverage = section_geom.intersection(edge_geom.buffer(thresholds.candidate_buffer_m)).length / max(section_geom.length, 0.001)
        angle = angle_difference_deg(geometry_bearing_deg(section_geom), edge.get("bearing_deg"))
        route_match = route_matches(section["route_number"], edge.get("ref"))
        name_match = name_matches(section["route_name"], edge.get("name"))
        old_confidence, old_manual, old_method = confidence_for_candidate(
            overlap, coverage, angle, route_match, name_match, thresholds
        )
        candidates.append({
            "edge": edge, "distance_m": distance, "overlap_ratio": overlap,
            "single_edge_coverage_ratio": coverage, "direction_difference": angle,
            "route_match_status": route_match, "name_match_status": name_match,
            "old_confidence": old_confidence, "old_manual_review_required": old_manual,
            "old_match_method": old_method,
        })
    return candidates


def _candidate_corridor_paths(candidates: list[dict[str, Any]], max_turn_deg: float) -> list[list[int]]:
    """Return singleton and maximal paths from directed SUMO topology."""
    by_from: dict[str, list[int]] = defaultdict(list)
    for idx, item in enumerate(candidates):
        node = item["edge"].get("from_node", "")
        if node:
            by_from[node].append(idx)
    outgoing: dict[int, list[int]] = defaultdict(list)
    incoming_count = Counter()
    for idx, item in enumerate(candidates):
        to_node = item["edge"].get("to_node", "")
        for next_idx in by_from.get(to_node, []) if to_node else []:
            if next_idx == idx:
                continue
            explicit_successors = item["edge"].get("_successor_edge_ids")
            if explicit_successors is not None and candidates[next_idx]["edge"]["sumo_edge_id"] not in explicit_successors:
                continue
            turn = _directed_turn_difference_deg(
                item["edge"].get("bearing_deg"), candidates[next_idx]["edge"].get("bearing_deg")
            )
            if turn <= max_turn_deg:
                outgoing[idx].append(next_idx)
                incoming_count[next_idx] += 1
    paths: set[tuple[int, ...]] = {(idx,) for idx in range(len(candidates))}
    starts = [idx for idx in range(len(candidates)) if incoming_count[idx] == 0] or list(range(len(candidates)))

    def visit(path: tuple[int, ...]) -> None:
        extensions = [idx for idx in outgoing.get(path[-1], []) if idx not in path]
        if not extensions:
            paths.add(path)
            return
        for idx in extensions:
            visit(path + (idx,))

    for start in starts:
        visit((start,))
    covered = {idx for path in paths if len(path) > 1 for idx in path}
    for start in set(range(len(candidates))) - covered:
        visit((start,))
    return [list(path) for path in sorted(paths, key=lambda value: (value[0], len(value), value))]


def _corridor_row(
    section_id: str, corridor_id: str, path: list[int], candidates: list[dict[str, Any]],
    section_geom: Any, thresholds: MatchThresholds,
) -> dict[str, Any]:
    from shapely.ops import unary_union

    members = [candidates[idx] for idx in path]
    geometries = [item["edge"]["geometry"] for item in members]
    lengths = [max(float(item["edge"].get("edge_length_m") or geometry.length), 0.001) for item, geometry in zip(members, geometries)]
    total_length = sum(lengths)
    overlap_support = sum(item["overlap_ratio"] * length for item, length in zip(members, lengths)) / total_length
    angle_members = [(item["direction_difference"], length) for item, length in zip(members, lengths) if item["direction_difference"] is not None]
    direction_difference = (
        sum(angle * length for angle, length in angle_members) / sum(length for _, length in angle_members)
        if angle_members else None
    )
    coverage = section_geom.intersection(unary_union(geometries).buffer(thresholds.candidate_buffer_m)).length / max(section_geom.length, 0.001)
    route_status = aggregate_match_status(item["route_match_status"] for item in members)
    name_status = aggregate_match_status(item["name_match_status"] for item in members)
    confidence_route = "mismatch" if route_status == "mixed_mismatch" else route_status
    confidence, manual, method = confidence_for_candidate(
        overlap_support, coverage, direction_difference, confidence_route, name_status, thresholds
    )
    return {
        "section_id": section_id, "candidate_corridor_id": corridor_id,
        "edge_count": len(members),
        "corridor_edge_ids": ";".join(item["edge"]["sumo_edge_id"] for item in members),
        "corridor_coverage_ratio": coverage, "overlap_support": overlap_support,
        "direction_difference": direction_difference, "route_match_status": route_status,
        "name_match_status": name_status, "continuity_status": "continuous",
        "confidence": confidence, "manual_review_required": manual,
        "selected": False, "match_method": method, "_path": path,
    }


def _confidence_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2, "unresolved": 3}.get(value, 4)


def match_sections_to_corridors(
    sections: list[dict[str, Any]], census_geometries: dict[str, Any],
    edges: list[dict[str, Any]], thresholds: MatchThresholds,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    _require_geometry_deps()
    from shapely.strtree import STRtree

    edge_geometries = [edge["geometry"] for edge in edges]
    tree = STRtree(edge_geometries)
    geom_id_to_index = {id(geom): i for i, geom in enumerate(edge_geometries)}
    mapping: list[dict[str, Any]] = []
    missing_spatial: list[dict[str, Any]] = []
    corridor_rows: list[dict[str, Any]] = []
    membership_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    for section_id, section in {row["census_section_id"]: row for row in sections}.items():
        section_geom = census_geometries.get(section_id)
        if section_geom is None:
            missing_spatial.append({
                "census_section_id": section_id, "status": "unresolved", "missing": "section_geometry",
                "additional_public_data_needed": "MLIT R3 road census visualization GeoJSON tiles for this section",
                "current_matching_possible": "attribute_only_not_accepted",
            })
            continue
        candidates = _candidate_edge_features(section, section_geom, edges, tree, geom_id_to_index, thresholds)
        if not candidates:
            mapping.append({
                "census_section_id": section_id, "sumo_edge_id": "", "direction": "unknown",
                "match_method": "no_candidate_in_configured_buffer", "distance_m": "", "overlap_ratio": "",
                "single_edge_coverage_ratio": "", "section_coverage_ratio": "", "angle_difference_deg": "",
                "route_match": "unknown", "name_match": "unknown", "confidence": "unresolved",
                "manual_review_required": True, "review_status": "unreviewed",
                "provenance": "mlit_r3_section_geometry;sumo_net_xml",
            })
            continue
        old_candidates = sorted(candidates, key=lambda item: (
            _confidence_rank(item["old_confidence"]), item["distance_m"],
            -item["overlap_ratio"], item["edge"]["sumo_edge_id"],
        ))
        old_best = old_candidates[0]
        old_selected = [item for item in old_candidates if item["old_confidence"] in {"high", "medium"}]
        if not old_selected:
            old_selected = old_candidates[: min(3, len(old_candidates))]
        old_best_manual = bool(
            old_best["old_manual_review_required"]
            or old_best["old_confidence"] == "low"
            or (
                old_best["old_confidence"] != "high"
                and sum(item["old_confidence"] == old_best["old_confidence"] for item in candidates) > 1
            )
        )
        paths = _candidate_corridor_paths(candidates, thresholds.max_medium_angle_difference_deg)
        section_corridors = [
            _corridor_row(section_id, f"{section_id}_C{number:04d}", path, candidates, section_geom, thresholds)
            for number, path in enumerate(paths, start=1)
        ]
        section_corridors.sort(key=lambda row: (
            _confidence_rank(row["confidence"]), -row["corridor_coverage_ratio"], -row["overlap_support"],
            float("inf") if row["direction_difference"] is None else row["direction_difference"],
            -row["edge_count"], row["candidate_corridor_id"],
        ))
        selected = section_corridors[0]
        selected["selected"] = True
        if len(section_corridors) > 1:
            runner_up = section_corridors[1]
            ambiguous_medium = (
                selected["confidence"] == runner_up["confidence"] == "medium"
                and abs(selected["corridor_coverage_ratio"] - runner_up["corridor_coverage_ratio"]) < 0.05
                and selected["corridor_edge_ids"] != runner_up["corridor_edge_ids"]
            )
            selected["manual_review_required"] = bool(selected["manual_review_required"] or ambiguous_medium)
        for corridor in section_corridors:
            output_corridor = {key: value for key, value in corridor.items() if not key.startswith("_")}
            for field in ("corridor_coverage_ratio", "overlap_support"):
                output_corridor[field] = round(output_corridor[field], 6)
            if output_corridor["direction_difference"] is not None:
                output_corridor["direction_difference"] = round(output_corridor["direction_difference"], 3)
            corridor_rows.append(output_corridor)
            for sequence_order, candidate_idx in enumerate(corridor["_path"], start=1):
                item = candidates[candidate_idx]
                membership_rows.append({
                    "section_id": section_id, "corridor_id": corridor["candidate_corridor_id"],
                    "edge_id": item["edge"]["sumo_edge_id"], "sequence_order": sequence_order,
                    "single_edge_coverage_ratio": round(item["single_edge_coverage_ratio"], 6),
                    "overlap_ratio": round(item["overlap_ratio"], 6),
                    "direction_difference": "" if item["direction_difference"] is None else round(item["direction_difference"], 3),
                    "route_match_status": item["route_match_status"],
                })
        selected_members = [candidates[idx] for idx in selected["_path"]]
        for item in selected_members:
            edge = item["edge"]
            mapping.append({
                "census_section_id": section_id, "sumo_edge_id": edge["sumo_edge_id"], "direction": "unknown",
                "corridor_id": selected["candidate_corridor_id"], "match_method": selected["match_method"],
                "distance_m": round(item["distance_m"], 3), "overlap_ratio": round(item["overlap_ratio"], 6),
                "single_edge_coverage_ratio": round(item["single_edge_coverage_ratio"], 6),
                "section_coverage_ratio": round(selected["corridor_coverage_ratio"], 6),
                "corridor_overlap_support": round(selected["overlap_support"], 6),
                "angle_difference_deg": "" if item["direction_difference"] is None else round(item["direction_difference"], 3),
                "corridor_direction_difference": "" if selected["direction_difference"] is None else round(selected["direction_difference"], 3),
                "route_match": selected["route_match_status"], "edge_route_match": item["route_match_status"],
                "name_match": selected["name_match_status"], "continuity_status": selected["continuity_status"],
                "confidence": selected["confidence"], "manual_review_required": bool(selected["manual_review_required"]),
                "review_status": "unreviewed" if selected["manual_review_required"] else "automatic",
                "provenance": "mlit_r3_section_geometry;sumo_net_xml;osm_way_tags",
            })
        if selected["confidence"] != old_best["old_confidence"] and selected["corridor_coverage_ratio"] >= thresholds.medium_section_coverage_ratio:
            change_reason = "corridor_coverage_recovered_split_section"
        elif selected["route_match_status"] in {"mismatch", "mixed_mismatch"}:
            change_reason = "route_mismatch_preserved"
        elif selected["confidence"] == "low" and (selected["direction_difference"] is None or selected["direction_difference"] > thresholds.max_medium_angle_difference_deg):
            change_reason = "corridor_direction_support_insufficient"
        else:
            change_reason = "confidence_unchanged"
        comparison_rows.append({
            "section_id": section_id, "old_best_confidence": old_best["old_confidence"],
            "new_best_confidence": selected["confidence"],
            "old_manual_review_required": old_best_manual,
            "new_manual_review_required": selected["manual_review_required"],
            "old_single_edge_coverage": round(old_best["single_edge_coverage_ratio"], 6),
            "new_corridor_coverage": round(selected["corridor_coverage_ratio"], 6),
            "selected_edge_count": selected["edge_count"],
            "old_best_route_match_status": old_best["route_match_status"],
            "new_route_match_status": selected["route_match_status"],
            "old_selected_route_mismatch_edge_count": sum(
                item["route_match_status"] == "mismatch" for item in old_selected
            ),
            "new_selected_route_mismatch_edge_count": sum(
                item["route_match_status"] == "mismatch" for item in selected_members
            ),
            "change_reason": change_reason,
        })
    return mapping, missing_spatial, corridor_rows, membership_rows, comparison_rows


def match_sections_to_edges(
    sections: list[dict[str, Any]], census_geometries: dict[str, Any],
    edges: list[dict[str, Any]], thresholds: MatchThresholds,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compatibility wrapper returning the selected corridor expanded to edges."""
    mapping, missing, _, _, _ = match_sections_to_corridors(sections, census_geometries, edges, thresholds)
    return mapping, missing


def lane_completion(
    sections: list[dict[str, Any]],
    edge_attrs: list[dict[str, Any]],
    mapping: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    sections_by_id = {row["census_section_id"]: row for row in sections}
    edge_by_id = {row["sumo_edge_id"]: row for row in edge_attrs}
    min_conf = config["lane_completion"]["minimum_confidence_for_census_fallback"]
    allowed = {"high"} if min_conf == "high" else {"high", "medium"}
    rows = []
    for match in mapping:
        edge_id = match["sumo_edge_id"]
        if not edge_id:
            continue
        section = sections_by_id.get(match["census_section_id"], {})
        edge = edge_by_id.get(edge_id, {})
        osm_lanes = edge.get("lanes")
        census_total = section.get("total_lanes")
        value = None
        status = "unresolved"
        provenance = "unresolved"
        conflict = False
        if osm_lanes:
            value = osm_lanes
            status = "osm_explicit"
            provenance = "osm_explicit"
            if census_total and census_total != osm_lanes and match["confidence"] in allowed:
                conflict = True
                status = "conflict"
                provenance = "osm_explicit;census_conflict_not_overwritten"
        elif match["confidence"] not in allowed or match["manual_review_required"]:
            status = "unresolved"
            provenance = "low_or_unreviewed_match_not_used"
        elif census_total is None:
            status = "unresolved"
            provenance = "census_lane_missing"
        elif census_total % 2 == 0 and config["lane_completion"]["allow_symmetric_even_total_split"]:
            value = census_total // 2
            status = "derived_symmetric_split"
            provenance = "road_census_observed_total_lanes;derived_symmetric_split"
        else:
            status = "unresolved"
            provenance = "odd_total_lanes_require_manual_review"
        rows.append(
            {
                "sumo_edge_id": edge_id,
                "census_section_id": match["census_section_id"],
                "osm_lanes": osm_lanes if osm_lanes is not None else "",
                "census_total_lanes": census_total if census_total is not None else "",
                "completed_lane_count": value if value is not None else "",
                "completion_status": status,
                "conflict": conflict,
                "confidence": match["confidence"],
                "manual_review_required": match["manual_review_required"] or status in {"conflict", "unresolved"},
                "provenance": provenance,
            }
        )
    return rows


def map_hourly_counts_to_edges(
    hourly: list[dict[str, Any]],
    mapping: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    min_conf = config["traffic_assignment"]["minimum_confidence"]
    allowed = {"high"} if min_conf == "high" else {"high", "medium"}
    by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mapping:
        if row.get("sumo_edge_id") and row["confidence"] in allowed and not row["manual_review_required"]:
            by_section[row["census_section_id"]].append(row)
    output = []
    for obs in hourly:
        if obs.get("observation_flag") != "1":
            continue
        matches = by_section.get(obs["census_section_id"], [])
        for match in matches:
            for vehicle_class, field in [
                ("small", "small_vehicle_count"),
                ("large", "large_vehicle_count"),
                ("total", "total_vehicle_count"),
            ]:
                count = obs.get(field)
                if count is None:
                    continue
                output.append(
                    {
                        "census_section_id": obs["census_section_id"],
                        "sumo_edge_id": match["sumo_edge_id"],
                        "direction": obs["direction"],
                        "begin": obs["begin"],
                        "end": obs["end"],
                        "observed_count": count,
                        "vehicle_class": vehicle_class,
                        "confidence": match["confidence"],
                        "mapping_source": "road_census_sumo_edge_mapping;series_repeated_not_split",
                    }
                )
    return output


def validation_summary(
    sections: list[dict[str, Any]],
    mapping: list[dict[str, Any]],
    lane_rows: list[dict[str, Any]],
    hourly: list[dict[str, Any]],
    edge_counts: list[dict[str, Any]],
) -> dict[str, Any]:
    section_matches: dict[str, dict[str, Any]] = {}
    for row in mapping:
        section_matches.setdefault(row["census_section_id"], row)
    matched_sections = {
        section_id for section_id, row in section_matches.items()
        if row.get("sumo_edge_id") and row["confidence"] in {"high", "medium"}
    }
    per_section = Counter(row["census_section_id"] for row in mapping if row.get("sumo_edge_id"))
    return {
        "matching": {
            "census_section_count": len(sections),
            "matched_section_count": len(matched_sections),
            "matched_section_ratio": round(len(matched_sections) / max(len(sections), 1), 6),
            "confidence_counts": dict(Counter(row["confidence"] for row in section_matches.values())),
            "manual_review_count": sum(
                str(row["manual_review_required"]).lower() == "true" or row["manual_review_required"] is True
                for row in section_matches.values()
            ),
            "edge_count_per_section": {
                "min": min(per_section.values()) if per_section else 0,
                "max": max(per_section.values()) if per_section else 0,
                "mean": round(sum(per_section.values()) / len(per_section), 3) if per_section else 0,
            },
            "route_mismatch_count": sum(row.get("route_match") == "mismatch" for row in mapping),
        },
        "lane_completion": dict(Counter(row["completion_status"] for row in lane_rows)),
        "traffic": {
            "observed_census_section_count": len({row["census_section_id"] for row in hourly if row.get("observation_flag") == "1"}),
            "edge_assigned_section_count": len({row["census_section_id"] for row in edge_counts}),
            "edge_hourly_count_rows": len(edge_counts),
            "unknown_direction_count": sum(row["direction"] == "unknown" for row in hourly),
            "hourly_missing_count": sum(row.get("total_vehicle_count") in {None, ""} for row in hourly),
        },
    }


def write_readme(path: Path, config: dict[str, Any], summary: dict[str, Any]) -> None:
    text = f"""# 道路交通センサス-SUMO対応付けパイプライン

この成果物は、令和3年度道路交通センサス東京都データを、現在の
OSM由来SUMO道路網へ再現可能に対応付けるための中間成果物である。
道路交通センサスは観測・属性根拠として扱い、OSM/SUMO本体を自動的に
上書きする権威としては扱わない。

## 既存構成との関係

- MLIT R3 raw files are kept under `03_data/raw/traffic_simulation/road_census/`
  and are ignored by Git.
- Source registry records are kept in `03_data/metadata/traffic_simulation_sources.csv`.
- `prepare_ota_official_traffic_calibration.py` already creates an Ota-focused
  official-observation artifact for calibration.
- `match_phase13_x1_mlit_r3.py` already investigates MLIT R3 lane evidence for
  v17 blocker review, but deliberately does not materialize lane counts.
- 本パイプラインは、区間属性正規化、時間帯交通量正規化、SUMO edge属性抽出、
  1対多対応付け、車線数補完候補、edge別観測交通量入力を同じルールで
  再生成できるようにしたものである。

## データフロー

1. `kasyo13.csv` -> `road_census_sections.csv`
2. `zkntrf13.csv` + section direction targets -> `road_census_hourly_traffic.csv`
3. SUMO `.net.xml` + OSM way tags -> `sumo_edge_matching_attributes.csv`
4. MLIT section geometry tiles + SUMO edge geometry -> `census_sumo_edge_mapping.csv`
5. Topologically connected candidate paths -> `census_section_corridor_mapping.csv`
6. Corridor composition and single-edge diagnostics -> `census_corridor_edge_membership.csv`
7. Old/new section-level decisions -> `census_mapping_before_after.csv`
8. Selected corridor + Census lane attributes -> `sumo_edge_lane_completion_candidates.csv`
9. Selected corridor + hourly observations -> `road_census_sumo_edge_hourly_counts.csv`

## 対応付けルール

候補はまず `candidate_buffer_m` 内で生成し、各edgeの距離、edge重複率、
単一edge区間カバー率、方位差、路線番号/ref一致、正規化路線名一致を
診断値として保存する。単一edge区間カバー率ではrejectしない。SUMOの
`to_node -> from_node` 接続と進行方向を使って連続corridorを構成した後、
corridor区間カバー率でconfidenceを判定する。重複率と方位差はedge長加重
平均で集約し、短いedge数による単純平均の偏りとworst-caseの過敏さを避ける。
route mismatchは空間一致と別の低信頼理由として保持する。

閾値は以下で管理する。

`reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml`

現在の閾値:

```json
{json.dumps(config["matching"], ensure_ascii=False, indent=2)}
```

## 自動・要確認・未解決

- `high`: sufficient spatial overlap, section coverage, direction agreement,
  and route/ref agreement.
- `medium`: spatial and direction support exist, but identity evidence is
  partial or incomplete.
- `low` / `unresolved`: insufficient spatial/directional support, route
  mismatch, missing geometry, or ambiguity. These rows require review and are
  not used for lane fallback or traffic assignment.

## 車線数補完

OSMの明示的な `lanes` は保持する。道路交通センサスの総車線数は、
レビュー不要の `high` / `medium` 対応に限ってフォールバック候補として
使う。偶数総車線数は `derived_symmetric_split` として対称分割できるが、
奇数総車線数、OSM/Censusの競合、低信頼対応は未解決または要確認に残す。

## 交通量割当

1つのセンサス区間が複数SUMO edgeへ対応する場合、時間帯別観測交通量は
各edgeに同じ観測系列として付与する。連続edgeが同一の物理的交通流を表す
可能性があるため、edge間で比例配分しない。

## 研究上の意味

この成果物は、SUMO交通量キャリブレーションへ投入できる観測系列と、
まだ研究判断・手作業確認が必要な対応候補を分けるためのトレーサブルな
中間層である。pytest成功や自動対応件数は、交通モデルの実証的妥当性を
直接示すものではない。実験・分析・評価で実際に使った観測区間のみを、
後続のキャリブレーション設定へ明示的に接続する。

## 検証サマリ

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```
"""
    path.write_text(text, encoding="utf-8")


def run_pipeline(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    paths = config["inputs"]
    census_dir = REPOSITORY_ROOT / paths["road_census_dir"]
    output_dir = REPOSITORY_ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    section_rows = read_csv_cp932(census_dir / paths["sections_csv"])
    hourly_rows = read_csv_cp932(census_dir / paths["hourly_csv"])
    sections = normalize_sections(section_rows)
    municipality_codes = {str(code) for code in paths.get("municipality_codes", [])}
    if municipality_codes:
        sections = [row for row in sections if row["municipality_code"] in municipality_codes]
    section_ids = {row["census_section_id"] for row in sections}
    hourly = [
        row for row in normalize_hourly_traffic(hourly_rows, section_rows)
        if row["census_section_id"] in section_ids
    ]
    qa = qa_sections_and_traffic(sections, hourly)

    _require_geometry_deps()
    sumo_tree = ET.parse(REPOSITORY_ROOT / paths["sumo_net_xml"])
    transformer, offset_x, offset_y = parse_sumo_location(sumo_tree.getroot())
    osm_tags = load_osm_way_tags(REPOSITORY_ROOT / paths["source_osm_xml"])
    edges = load_sumo_edges(REPOSITORY_ROOT / paths["sumo_net_xml"], osm_tags)
    edge_attrs = extract_sumo_edge_attributes(edges)
    census_geometries = load_census_geometries(census_dir / paths["section_geometry_dir"], section_ids, transformer, offset_x, offset_y)
    mapping, missing_spatial, corridor_rows, membership_rows, comparison_rows = match_sections_to_corridors(
        sections, census_geometries, edges, thresholds_from_config(config)
    )
    lane_rows = lane_completion(sections, edge_attrs, mapping, config)
    edge_counts = map_hourly_counts_to_edges(hourly, mapping, config)
    summary = validation_summary(sections, mapping, lane_rows, hourly, edge_counts)
    summary["missing_spatial_section_count"] = len(missing_spatial)
    summary["corridors"] = {
        "candidate_corridor_count": len(corridor_rows),
        "selected_confidence_counts": dict(Counter(row["confidence"] for row in corridor_rows if row["selected"])),
        "selected_route_mismatch_count": sum(
            row["route_match_status"] in {"mismatch", "mixed_mismatch"}
            for row in corridor_rows if row["selected"]
        ),
    }
    summary["created_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    summary["input_manifest"] = [
        {"path": paths["road_census_dir"] + "/" + paths["sections_csv"], "sha256": sha256_file(census_dir / paths["sections_csv"])},
        {"path": paths["road_census_dir"] + "/" + paths["hourly_csv"], "sha256": sha256_file(census_dir / paths["hourly_csv"])},
        {"path": paths["source_osm_xml"], "sha256": sha256_file(REPOSITORY_ROOT / paths["source_osm_xml"])},
        {"path": paths["sumo_net_xml"], "sha256": sha256_file(REPOSITORY_ROOT / paths["sumo_net_xml"])},
    ]

    write_csv(output_dir / "road_census_sections.csv", sections, [
        "census_section_id", "generation_tens", "generation_ones", "road_type_code", "route_number", "route_name",
        "municipality_code", "section_length_km", "total_lanes", "roadway_width_m", "carriageway_width_m",
        "lane_width_m", "median_width_m", "oneway_flag", "traffic_unit_prefecture_code", "traffic_unit_id",
        "up_observation_section_id", "down_observation_section_id", "up_observation_flag", "down_observation_flag",
        "source_file", "source_row_id",
    ])
    write_csv(output_dir / "road_census_hourly_traffic.csv", hourly, [
        "census_section_id", "traffic_unit_id", "direction", "hour", "begin", "end", "small_vehicle_count",
        "large_vehicle_count", "total_vehicle_count", "observation_flag", "survey_date", "weather_code", "source_file",
    ])
    write_csv(output_dir / "road_census_qa_issues.csv", qa, ["check", "severity", "id", "field", "value", "count", "traffic_unit_id", "hour"])
    write_csv(output_dir / "sumo_edge_matching_attributes.csv", edge_attrs, [
        "sumo_edge_id", "from_node", "to_node", "edge_length_m", "osm_way_ids", "ref", "name", "highway",
        "lanes", "sumo_lane_count", "oneway", "bearing_deg", "internal",
    ])
    write_csv(output_dir / "census_sumo_edge_mapping.csv", mapping, [
        "census_section_id", "sumo_edge_id", "direction", "corridor_id", "match_method", "distance_m",
        "overlap_ratio", "single_edge_coverage_ratio", "section_coverage_ratio", "corridor_overlap_support",
        "angle_difference_deg", "corridor_direction_difference", "route_match", "edge_route_match", "name_match",
        "continuity_status", "confidence", "manual_review_required", "review_status", "provenance",
    ])
    write_csv(output_dir / "census_section_corridor_mapping.csv", corridor_rows, [
        "section_id", "candidate_corridor_id", "edge_count", "corridor_edge_ids", "corridor_coverage_ratio",
        "overlap_support", "direction_difference", "route_match_status", "name_match_status", "continuity_status",
        "confidence", "manual_review_required", "selected", "match_method",
    ])
    write_csv(output_dir / "census_corridor_edge_membership.csv", membership_rows, [
        "section_id", "corridor_id", "edge_id", "sequence_order", "single_edge_coverage_ratio",
        "overlap_ratio", "direction_difference", "route_match_status",
    ])
    write_csv(output_dir / "census_mapping_before_after.csv", comparison_rows, [
        "section_id", "old_best_confidence", "new_best_confidence", "old_manual_review_required",
        "new_manual_review_required", "old_single_edge_coverage", "new_corridor_coverage",
        "selected_edge_count", "old_best_route_match_status", "new_route_match_status",
        "old_selected_route_mismatch_edge_count", "new_selected_route_mismatch_edge_count", "change_reason",
    ])
    write_csv(output_dir / "census_section_spatial_unresolved.csv", missing_spatial, [
        "census_section_id", "status", "missing", "additional_public_data_needed", "current_matching_possible",
    ])
    write_csv(output_dir / "sumo_edge_lane_completion_candidates.csv", lane_rows, [
        "sumo_edge_id", "census_section_id", "osm_lanes", "census_total_lanes", "completed_lane_count",
        "completion_status", "conflict", "confidence", "manual_review_required", "provenance",
    ])
    write_csv(output_dir / "road_census_sumo_edge_hourly_counts.csv", edge_counts, [
        "census_section_id", "sumo_edge_id", "direction", "begin", "end", "observed_count", "vehicle_class",
        "confidence", "mapping_source",
    ])
    (output_dir / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(output_dir / "README.md", config, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    summary = run_pipeline(args.config)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
