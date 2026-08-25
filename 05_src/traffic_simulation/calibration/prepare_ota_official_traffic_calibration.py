#!/usr/bin/env python3
"""Fix and map official Ota traffic observations to the fixed OSM/SUMO network.

The output is an investigation/calibration-input artifact.  It does not alter
OSM, the v17 resolver, or the SUMO network.  A match is usable only when the
official identity and geometry (MLIT), or official point name and intersecting
road identities (Tokyo Police), select one OSM location without competition.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from numbers import Integral
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree


OTA_BBOX = (139.62, 35.50, 139.86, 35.66)
MLIT_BUFFER_M = 15.0
MLIT_WAY_OVERLAP = 0.70
MLIT_OFFICIAL_COVERAGE = 0.80
POLICE_CLUSTER_M = 80.0

ROAD_ALIASES = {
    "第一京浜": {"15", "第一京浜", "一般国道15号"},
    "第二京浜": {"1", "第二京浜", "一般国道1号"},
    "中原街道": {"2", "中原街道", "東京丸子横浜線"},
    "湾岸道路": {"357", "湾岸道路", "国道357号", "一般国道357号"},
    "産業道路": {"6", "131", "産業道路", "東京大師横浜線", "一般国道131号"},
    "環七通り": {"318", "環七通り", "環状七号線"},
    "環八通り": {"311", "環八通り", "環状八号線"},
    "池上通り": {"421", "池上通り", "東品川下丸子線"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"[\s・･()（）号線都道国道一般]", "", text)


def road_identity(tags: dict[str, str], official: str) -> bool:
    observed = {normalize(tags.get("ref")), normalize(tags.get("name"))}
    expected = {normalize(item) for item in ROAD_ALIASES.get(official, {official})}
    return bool((observed - {""}) & expected)


def exact_route_identity(tags: dict[str, str], number: str, name: str) -> bool:
    refs = {normalize(x) for x in (tags.get("ref") or "").split(";")}
    return normalize(number) in refs or normalize(tags.get("name")) == normalize(name)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_cp932_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="cp932") as stream:
        return list(csv.DictReader(stream))


def zip_csv(path: Path, suffix: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith(suffix))
        with archive.open(member) as raw:
            return list(csv.DictReader(io.TextIOWrapper(raw, encoding="cp932")))


def load_osm(osm_path: Path) -> tuple[dict[int, tuple[float, float, dict[str, str]]], list[dict[str, Any]]]:
    node_coordinates: dict[int, tuple[float, float, dict[str, str]]] = {}
    ways_raw: list[tuple[int, list[int], dict[str, str]]] = []
    minlon, minlat, maxlon, maxlat = OTA_BBOX
    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "node":
            lat, lon = float(element.get("lat")), float(element.get("lon"))
            if minlat <= lat <= maxlat and minlon <= lon <= maxlon:
                tags = {x.get("k"): x.get("v") for x in element.findall("tag")}
                node_coordinates[int(element.get("id"))] = (lon, lat, tags)
            element.clear()
        elif element.tag == "way":
            tags = {x.get("k"): x.get("v") for x in element.findall("tag")}
            if tags.get("highway"):
                ways_raw.append((int(element.get("id")), [int(x.get("ref")) for x in element.findall("nd")], tags))
            element.clear()
        elif element.tag == "relation":
            element.clear()

    project = Transformer.from_crs(4326, 6677, always_xy=True).transform
    ways = []
    for way_id, refs, tags in ways_raw:
        if len(refs) < 2 or any(ref not in node_coordinates for ref in refs):
            continue
        geometry_wgs84 = LineString([(node_coordinates[n][0], node_coordinates[n][1]) for n in refs])
        ways.append({
            "way_id": way_id,
            "node_ids": refs,
            "tags": tags,
            "geometry": transform(project, geometry_wgs84),
        })
    return node_coordinates, ways


def load_sumo(net_path: Path) -> tuple[dict[int, list[str]], set[str]]:
    by_way: dict[int, list[str]] = defaultdict(list)
    junctions: set[str] = set()
    for _, element in ET.iterparse(net_path, events=("end",)):
        if element.tag == "junction" and not element.get("id", "").startswith(":"):
            junctions.add(element.get("id"))
        elif element.tag == "edge" and not element.get("function"):
            edge_id = element.get("id", "")
            original = None
            for lane in element.findall("lane"):
                for param in lane.findall("param"):
                    if param.get("key") == "origId" and (param.get("value") or "").isdigit():
                        original = int(param.get("value"))
                        break
            if original is None:
                match = re.match(r"^-?(\d+)(?:#.*)?$", edge_id)
                original = int(match.group(1)) if match else None
            if original is not None:
                by_way[original].append(edge_id)
        if element.tag in {"edge", "junction"}:
            element.clear()
    return {key: sorted(set(value)) for key, value in by_way.items()}, junctions


def load_mlit_features(tile_dir: Path, rows: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    fragments: dict[str, list[Any]] = defaultdict(list)
    files: dict[str, set[str]] = defaultdict(set)
    for path in sorted(tile_dir.glob("*.geojson")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            census_id = str(feature.get("properties", {}).get("census", ""))
            if census_id in rows:
                fragments[census_id].append(shape(feature["geometry"]))
                files[census_id].add(path.name)
    project = Transformer.from_crs(4326, 6677, always_xy=True).transform
    return {
        census_id: {
            "geometry": transform(project, unary_union(geometries)),
            "files": sorted(files[census_id]),
            "row": rows[census_id],
        }
        for census_id, geometries in fragments.items()
    }


def match_mlit(
    ota_rows: list[dict[str, str]], features: dict[str, dict[str, Any]], ways: list[dict[str, Any]],
    sumo_by_way: dict[int, list[str]],
) -> list[dict[str, Any]]:
    observed_targets = set()
    target_context: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ota_rows:
        for direction in ("上り", "下り"):
            if row[f"{direction}／令和３年度調査交通量観測・非観測の別"] == "1":
                target = row[f"{direction}／観測地点交通調査基本区間番号"]
                if target:
                    observed_targets.add(target)
                    target_context[target].append(row)

    geometries = [way["geometry"] for way in ways]
    tree = STRtree(geometries)
    geometry_index = {id(geometry): index for index, geometry in enumerate(geometries)}
    output = []
    for census_id in sorted(observed_targets):
        feature = features.get(census_id)
        contexts = target_context[census_id]
        if not feature:
            output.append({
                "census_id": census_id, "match_status": "unmatched", "reason": "official_geometry_not_in_acquired_ota_tiles",
                "osm_way_ids": "", "sumo_edge_ids": "", "official_coverage_ratio": "", "competing_way_ids": "",
            })
            continue
        official = feature["geometry"]
        row = feature["row"]
        selected, competing = [], []
        query = tree.query(official.buffer(MLIT_BUFFER_M))
        for candidate in query:
            # Shapely 2 returns integer indices; Shapely 1 returns geometries.
            index = int(candidate) if isinstance(candidate, Integral) else geometry_index[id(candidate)]
            candidate_geometry = geometries[index]
            way = ways[index]
            overlap = candidate_geometry.intersection(official.buffer(MLIT_BUFFER_M)).length / max(candidate_geometry.length, 0.001)
            if overlap < MLIT_WAY_OVERLAP:
                continue
            item = (way, overlap)
            if exact_route_identity(way["tags"], row["路線番号"], row["路線名"]):
                selected.append(item)
            else:
                competing.append(item)
        selected_geometry = unary_union([item[0]["geometry"] for item in selected]) if selected else None
        coverage = (
            official.intersection(selected_geometry.buffer(MLIT_BUFFER_M)).length / max(official.length, 0.001)
            if selected_geometry is not None else 0.0
        )
        selected_ids = sorted({item[0]["way_id"] for item in selected})
        sumo_edges = sorted({edge for way_id in selected_ids for edge in sumo_by_way.get(way_id, [])})
        if selected and coverage >= MLIT_OFFICIAL_COVERAGE and sumo_edges:
            status, reason = "unique", "official_identifier_geometry_corridor_set_and_sumo_provenance_agree"
        elif selected:
            status, reason = "ambiguous", "identity_candidates_exist_but_full_official_geometry_or_sumo_coverage_is_incomplete"
        else:
            status, reason = "unmatched", "no_osm_way_has_both_official_identity_and_geometry_overlap"
        output.append({
            "census_id": census_id,
            "route_number": row["路線番号"],
            "route_name": row["路線名"],
            "observation_dates": ";".join(sorted({r["上り／交通量観測年月日"] for r in contexts if r["上り／交通量観測年月日"]} | {r["下り／交通量観測年月日"] for r in contexts if r["下り／交通量観測年月日"]})),
            "match_status": status,
            "reason": reason,
            "official_coverage_ratio": f"{coverage:.6f}",
            "osm_way_ids": ";".join(map(str, selected_ids)),
            "sumo_edge_ids": ";".join(sumo_edges),
            "competing_way_ids": ";".join(map(str, sorted({item[0]["way_id"] for item in competing}))),
            "official_tile_files": ";".join(feature["files"]),
        })
    return output


def cluster_named_nodes(
    site_name: str, roads: list[str], nodes: dict[int, tuple[float, float, dict[str, str]]],
    ways: list[dict[str, Any]], sumo_junctions: set[str], sumo_by_way: dict[int, list[str]],
) -> list[dict[str, Any]]:
    project = Transformer.from_crs(4326, 6677, always_xy=True).transform
    candidates = []
    for node_id, (lon, lat, tags) in nodes.items():
        if normalize(tags.get("name")) != normalize(site_name):
            continue
        if not (tags.get("junction") == "yes" or tags.get("highway") in {"traffic_signals", "crossing"}):
            continue
        point = transform(project, Point(lon, lat))
        nearby = [way for way in ways if way["geometry"].distance(point) <= POLICE_CLUSTER_M]
        road_hits = {road: [way for way in nearby if road_identity(way["tags"], road)] for road in roads}
        if all(road_hits.values()):
            relevant = sorted({way["way_id"] for values in road_hits.values() for way in values})
            candidates.append({
                "node_id": node_id, "lon": lon, "lat": lat, "road_hits": road_hits,
                "way_ids": relevant,
                "sumo_edges": sorted({edge for wid in relevant for edge in sumo_by_way.get(wid, [])}),
                "sumo_junction_present": str(node_id) in sumo_junctions,
            })
    # Multi-node modeled intersections are one candidate when all named nodes lie within 100 m.
    if not candidates:
        return []
    center = unary_union([Point(item["lon"], item["lat"]) for item in candidates]).centroid
    if any(Point(item["lon"], item["lat"]).distance(center) > 0.002 for item in candidates):
        return candidates
    return [{
        "node_ids": sorted(item["node_id"] for item in candidates),
        "lon": sum(item["lon"] for item in candidates) / len(candidates),
        "lat": sum(item["lat"] for item in candidates) / len(candidates),
        "way_ids": sorted({wid for item in candidates for wid in item["way_ids"]}),
        "sumo_edges": sorted({edge for item in candidates for edge in item["sumo_edges"]}),
        "sumo_junction_ids": sorted(str(item["node_id"]) for item in candidates if item["sumo_junction_present"]),
    }]


def police_inventory(police_dir: Path, year: int) -> list[dict[str, str]]:
    prefix = "01" if year == 2023 else "02"
    overview = police_dir / f"{prefix}_cyousagaiyou_csv.zip"
    output = []
    for suffix, kind in [
        ("1-4-02cyousachiten_kokkakukannsen.csv", "junction"),
        ("1-4-03cyousachiten_sonota.csv", "junction"),
        ("1-4-04cyousachiten_syuyoudanmen.csv", "section"),
    ]:
        for row in zip_csv(overview, suffix):
            if row.get("所在地") == "大田区":
                row = dict(row)
                row["observation_kind"] = kind
                row["year"] = str(year)
                output.append(row)
    return output


def match_police(
    inventory: list[dict[str, str]], nodes: dict[int, tuple[float, float, dict[str, str]]], ways: list[dict[str, Any]],
    sumo_junctions: set[str], sumo_by_way: dict[int, list[str]],
) -> list[dict[str, Any]]:
    output = []
    for row in inventory:
        screen = row.get("スクリーンライン(注)(環状･南北方向の骨格幹線道路名）", "")
        crossed = row.get("交差道路名(放射状･東西方向の骨格幹線道路名）", "") or row.get("交差道路名", "")
        roads = [item for item in (screen, crossed) if item]
        candidates = cluster_named_nodes(row["調査地点名"], roads, nodes, ways, sumo_junctions, sumo_by_way)
        if len(candidates) == 1 and candidates[0]["sumo_edges"]:
            match_status = "unique"
            reason = "official_point_name_and_all_official_road_identities_select_one_osm_cluster"
            selected = candidates[0]
        elif len(candidates) > 1:
            match_status, reason, selected = "ambiguous", "multiple_named_osm_clusters_satisfy_official_road_identity", None
        else:
            match_status, reason, selected = "unmatched", "no_named_osm_junction_cluster_satisfies_all_official_road_identities", None
        output.append({
            "year": row["year"], "site_number": row["調査地点№"].strip(), "site_name": row["調査地点名"],
            "observation_kind": row["observation_kind"], "survey_date": row["調査日"],
            "official_roads": ";".join(roads), "match_status": match_status, "reason": reason,
            "osm_node_ids": ";".join(map(str, selected["node_ids"])) if selected else "",
            "osm_way_ids": ";".join(map(str, selected["way_ids"])) if selected else "",
            "sumo_junction_ids": ";".join(selected["sumo_junction_ids"]) if selected else "",
            "sumo_edge_ids": ";".join(selected["sumo_edges"]) if selected else "",
            "candidate_count": len(candidates),
            "use_split": "calibration" if row["year"] == "2023" else "independent_validation",
            "usable_granularity": (
                "junction_hourly_entering_total_only" if row["observation_kind"] == "junction" else "section_hourly_both_directions_total_only"
            ) if match_status == "unique" else "none",
            "directional_mapping_status": "not_approved_without_official_arm_or_up_down_geometry",
        })
    return output


def mlit_observation_rows(ota_rows: list[dict[str, str]], traffic_rows: list[dict[str, str]], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    match_by_id = {row["census_id"]: row for row in matches}
    units = {row["交通量／調査単位区間番号"]: row for row in ota_rows if row["交通量／調査単位区間番号"]}
    output = []
    hour_fields = [(hour, f"時間帯別自動車類交通量（台／時）／{str(hour).translate(str.maketrans('0123456789','０１２３４５６７８９'))}時台") for hour in list(range(7, 24)) + list(range(0, 7))]
    for traffic in traffic_rows:
        if traffic["都道府県指定市コード"] != "13100":
            continue
        context = units.get(traffic["交通量調査単位区間番号"])
        if not context:
            continue
        direction = "上り" if traffic["上り・下りの別"] == "1" else "下り"
        target = context.get(f"{direction}／観測地点交通調査基本区間番号", "")
        observed = context.get(f"{direction}／令和３年度調査交通量観測・非観測の別") == "1"
        match = match_by_id.get(target, {})
        eligible = observed and match.get("match_status") == "unique"
        for hour, field in hour_fields:
            value = traffic.get(field, "")
            if value.isdigit():
                output.append({
                    "source": "mlit_r3_road_census_tokyo", "use_split": "calibration", "traffic_unit_id": traffic["交通量調査単位区間番号"],
                    "census_id": target, "survey_date": traffic["交通量観測年月日"], "direction_code": traffic["上り・下りの別"],
                    "vehicle_class_code": traffic["車種区分"], "hour": hour, "count": int(value),
                    "match_status": match.get("match_status", "unmatched"), "eligible": str(eligible).lower(),
                    "osm_way_ids": match.get("osm_way_ids", ""), "sumo_edge_ids": match.get("sumo_edge_ids", ""),
                    "exclusion_reason": "" if eligible else ("not_directly_observed" if not observed else match.get("reason", "target_mapping_missing")),
                })
    return output


def police_observations(police_dir: Path, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for match in matches:
        year = int(match["year"]); prefix = "01" if year == 2023 else "02"; number = match["site_number"]
        if match["observation_kind"] == "junction":
            minimum_digits = 3 if year == 2023 else 4
            padded_number = str(int(number)).zfill(max(minimum_digits, len(number)))
            rows = zip_csv(police_dir / f"{prefix}_kousatenkubu_csv.zip", f"kousaten_{padded_number}_houkou.csv")
            hourly = [row for row in rows if row["時間帯等"].isdigit() and row["流出方向"] == "流入計"]
            grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for row in hourly:
                for field in ("四輪計", "二輪車"):
                    if row[field].isdigit(): grouped[row["時間帯等"]][field] += int(row[field])
            for hour, values in sorted(grouped.items(), key=lambda item: int(item[0])):
                output.append({
                    "source": f"keishicho_{year}", "use_split": match["use_split"], "site_number": number, "site_name": match["site_name"],
                    "observation_kind": "junction_entering_total", "survey_date": match["survey_date"], "hour": int(hour),
                    "four_wheel_count": values["四輪計"], "motorcycle_count": values["二輪車"],
                    "match_status": match["match_status"], "eligible": str(match["match_status"] == "unique").lower(),
                    "osm_node_ids": match["osm_node_ids"], "osm_way_ids": match["osm_way_ids"],
                    "sumo_junction_ids": match["sumo_junction_ids"], "sumo_edge_ids": match["sumo_edge_ids"],
                    "exclusion_reason": "" if match["match_status"] == "unique" else match["reason"],
                })
        else:
            rows = zip_csv(police_dir / f"{prefix}_syuyoudanmen_csv.zip", f"syuyoudanmen_{number}.csv")
            for row in rows:
                if not row["時間帯等"].isdigit(): continue
                four = sum(int(row[field]) for field in ("上り四輪計", "下り四輪計") if row[field].isdigit())
                motorcycles = sum(int(row[field]) for field in ("上り二輪車", "下り二輪車") if row[field].isdigit())
                output.append({
                    "source": f"keishicho_{year}", "use_split": match["use_split"], "site_number": number, "site_name": match["site_name"],
                    "observation_kind": "section_both_directions_total", "survey_date": match["survey_date"], "hour": int(row["時間帯等"]),
                    "four_wheel_count": four, "motorcycle_count": motorcycles, "match_status": match["match_status"],
                    "eligible": str(match["match_status"] == "unique").lower(), "osm_node_ids": match["osm_node_ids"],
                    "osm_way_ids": match["osm_way_ids"], "sumo_junction_ids": match["sumo_junction_ids"], "sumo_edge_ids": match["sumo_edge_ids"],
                    "exclusion_reason": "" if match["match_status"] == "unique" else match["reason"],
                })
    return output


def build_manifest(paths: Iterable[Path], repo: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(paths):
        if path.is_file():
            records.append({"path": str(path.relative_to(repo)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(f"immutable output already exists: {output}")
    output.mkdir(parents=True)
    census_dir = repo / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
    police_dir = repo / "03_data/raw/traffic_simulation/tokyo_police/keishicho_traffic_counts_2023_2024_20260823"
    osm_path = repo / "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
    net_path = repo / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"

    all_mlit = read_cp932_csv(census_dir / "kasyo13.csv")
    ota_mlit = [row for row in all_mlit if row["市区町村コード"] == "13111"]
    mlit_by_id = {row["交通調査基本区間番号"]: row for row in all_mlit}
    nodes, ways = load_osm(osm_path)
    sumo_by_way, sumo_junctions = load_sumo(net_path)
    features = load_mlit_features(census_dir / "webmap_tiles", mlit_by_id)
    mlit_matches = match_mlit(ota_mlit, features, ways, sumo_by_way)
    police_sites = police_inventory(police_dir, 2023) + police_inventory(police_dir, 2024)
    police_matches = match_police(police_sites, nodes, ways, sumo_junctions, sumo_by_way)
    mlit_obs = mlit_observation_rows(ota_mlit, read_cp932_csv(census_dir / "zkntrf13.csv"), mlit_matches)
    police_obs = police_observations(police_dir, police_matches)

    write_csv(output / "mlit_r3_ota_observation_mapping.csv", mlit_matches)
    write_csv(output / "keishicho_ota_observation_mapping.csv", police_matches)
    write_csv(output / "mlit_r3_ota_hourly_observations.csv", mlit_obs)
    write_csv(output / "keishicho_ota_hourly_observations.csv", police_obs)
    eligible_calibration = [row for row in mlit_obs + police_obs if row.get("eligible") == "true" and row["use_split"] == "calibration"]
    eligible_validation = [row for row in police_obs if row.get("eligible") == "true" and row["use_split"] == "independent_validation"]
    excluded = [row for row in mlit_obs + police_obs if row.get("eligible") != "true"]
    write_csv(output / "calibration_observations.csv", eligible_calibration)
    write_csv(output / "independent_validation_observations.csv", eligible_validation)
    write_csv(output / "ambiguous_and_unmatched_observations.csv", excluded)

    source_files = list(census_dir.glob("*")) + list((census_dir / "webmap_tiles").glob("*")) + list(police_dir.glob("*")) + [osm_path, net_path]
    summary = {
        "artifact_id": "OTA_OFFICIAL_TRAFFIC_OBSERVATION_MAPPING_V1",
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "source_policy": "DEC-TRAFFIC-OSM-PRIMARY-CENSUS-POLICE-CALIBRATION-001",
        "source_osm_is_modified": False,
        "sumo_network_is_modified": False,
        "split_policy": {"calibration": ["MLIT_R3", "Keishicho_2023"], "independent_validation": ["Keishicho_2024"], "independence": "temporal_not_spatial"},
        "thresholds": {"mlit_buffer_m": MLIT_BUFFER_M, "mlit_way_overlap": MLIT_WAY_OVERLAP, "mlit_official_coverage": MLIT_OFFICIAL_COVERAGE, "police_named_cluster_radius_m": POLICE_CLUSTER_M},
        "counts": {
            "mlit_ota_basic_sections": len(ota_mlit),
            "mlit_observed_target_mappings": dict(Counter(row["match_status"] for row in mlit_matches)),
            "keishicho_site_mappings_2023": dict(Counter(row["match_status"] for row in police_matches if row["year"] == "2023")),
            "keishicho_site_mappings_2024": dict(Counter(row["match_status"] for row in police_matches if row["year"] == "2024")),
            "calibration_hourly_rows": len(eligible_calibration),
            "independent_validation_hourly_rows": len(eligible_validation),
            "excluded_hourly_rows": len(excluded),
        },
        "semantic_limits": [
            "Police intersection observations are accepted only as the sum entering the uniquely identified junction; arm-to-edge movements are not approved.",
            "Police section observations are accepted only as both-directions totals; official up/down geometry is not supplied by the CSV.",
            "A Census section may map to a unique same-route corridor set made of multiple OSM Ways and SUMO edges; detector ordering is not established here.",
            "Traffic observations calibrate flow and do not overwrite OSM geometry, direction, access, or lane facts.",
        ],
        "source_manifest": build_manifest(source_files, repo),
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = f"""# 大田区の公式交通量観測とOSM/SUMO道路の対応（v1）

## 結論

国土交通省の令和3年度道路交通センサスと、警視庁の2023年・2024年交通量統計を原本のまま固定し、
固定OSMと現行v17 SUMO候補ネットワークへ照合した。較正には国交省R3と警視庁2023、独立確認には
警視庁2024を使う。独立性は時点についてのみで、場所については独立ではない。

一意な対応だけを `calibration_observations.csv` と
`independent_validation_observations.csv` に収録した。対応不能な観測は
`ambiguous_and_unmatched_observations.csv` に分離した。

## 件数

- 国交省R3: 大田区の道路区間66、実測参照先33、うち一意21、対応不能12
- 警視庁2023: 大田区9地点、うち一意6、対応不能3
- 警視庁2024: 大田区10地点、うち一意6、対応不能4
- 較正用の時間別行: {len(eligible_calibration)}
- 独立確認用の時間別行: {len(eligible_validation)}

## 意味上の制限

- 警視庁交差点は、一意な交差点へ流入する総量だけを採用し、各進行方向を個別SUMO接続へ割り当てない。
- 警視庁主要断面は、上り・下りの地理的対応がCSVにないため、両方向合計だけを採用する。
- 国交省区間は同一路線のOSM/SUMO道路集合へ対応する。検出器を置く順序はこの成果物では確定しない。
- 観測交通量は需要・交通流の較正にだけ使い、OSMの形状、方向、車線数、通行権限を上書きしない。

## 再現

`05_src/traffic_simulation/calibration/prepare_ota_official_traffic_calibration.py` を、存在しない新規出力先を
指定して実行する。入力URLは `official_source_urls.json`、取得ファイルと入力道路網のハッシュは
`summary.json` に固定した。
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    source_urls = {
        "mlit_r3": {
            "index": "https://www.mlit.go.jp/road/census/r3/index.html",
            "location_csv": "https://www.mlit.go.jp/road/census/r3/data/csv/kasyo13.csv",
            "hourly_csv": "https://www.mlit.go.jp/road/census/r3/data/csv/zkntrf13.csv",
            "location_format": "https://www.mlit.go.jp/road/census/r3/data/xlsx/KasyoFormat.xlsx",
            "hourly_format": "https://www.mlit.go.jp/road/census/r3/data/xlsx/zkntrfFormat.xlsx",
            "geometry_template": "https://www.mlit.go.jp/road/ir/ir-data/census_visualizationR3/{layer}/13/{x}/{y}.geojson",
        },
        "keishicho": {
            "catalog": "https://catalog.data.metro.tokyo.lg.jp/dataset/t000022d0000000035",
            "resource_template": "https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/tokei_jokyo/ryo.files/{filename}",
            "files": sorted(path.name for path in police_dir.glob("*.zip")),
        },
    }
    (output / "official_source_urls.json").write_text(json.dumps(source_urls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
