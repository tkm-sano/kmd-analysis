#!/usr/bin/env python3
"""Diagnose outside-to-outside PT automobile person-trip corridors through Ota.

The input table has no driver-status field. Counts are therefore retained only
as person-trip evidence and are never materialized as vehicle demand. SUMO is
fed one diagnostic unit per OD solely to test general route availability.
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
import openpyxl
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from prepare_tokyo_pt_small_zone_driving_od import gateway_candidates, nearest_gateways
from prepare_tokyo_pt_sumo_od import load_passenger_edges, read_location, to_sumo_geometry


SURVEY_YEAR = "平成３０年"
AUTOMOBILE_LABEL = "3_自動車"
TOTAL_PURPOSE_LABEL = "9_合計"
OTA_BASIC_ZONES = {f"{value:04d}" for value in range(130, 139)}


def parse_basic_zone(value: str) -> str | None:
    match = re.fullmatch(r"\s*\d+_(\d{4}):\s*", value or "")
    if not match:
        return None
    code = match.group(1)
    return None if code in {"8700", "9999"} else code


def read_external_automobile_person_od(
    path: Path, valid_zones: set[str], ota_zones: set[str]
) -> tuple[dict[tuple[str, str], float], dict[str, Any]]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    accounting = Counter()
    with path.open(encoding="cp932", newline="") as stream:
        for row in csv.DictReader(stream):
            accounting["input_rows"] += 1
            if row["調査年"] != SURVEY_YEAR:
                accounting["wrong_year_rows_excluded"] += 1
                continue
            if row["目的種類"] != TOTAL_PURPOSE_LABEL:
                accounting["non_total_purpose_rows_excluded"] += 1
                continue
            if row["代表交通手段"] != AUTOMOBILE_LABEL:
                accounting["non_automobile_rows_excluded"] += 1
                continue
            origin = parse_basic_zone(row["発ゾーン"])
            destination = parse_basic_zone(row["着ゾーン"])
            if origin not in valid_zones or destination not in valid_zones:
                accounting["non_official_zone_rows_excluded"] += 1
                continue
            if origin in ota_zones or destination in ota_zones:
                accounting["ota_endpoint_rows_excluded"] += 1
                continue
            count = float(row["トリップ数"].replace(",", ""))
            if count <= 0:
                accounting["nonpositive_rows_excluded"] += 1
                continue
            totals[(origin, destination)] += count
            accounting["accepted_rows"] += 1
            accounting["accepted_person_trips"] += round(count)
    return dict(sorted(totals.items())), dict(accounting)


def geographic_candidates(
    totals: dict[tuple[str, str], float], centroids: dict[str, Point], ota_geometry: Any
) -> dict[tuple[str, str], dict[str, float]]:
    result = {}
    for (origin, destination), count in totals.items():
        chord = LineString([centroids[origin], centroids[destination]])
        overlap = chord.intersection(ota_geometry).length
        if overlap > 0:
            result[(origin, destination)] = {
                "person_trips": count, "ota_chord_length_m": overlap,
                "centroid_distance_m": chord.length,
            }
    return dict(sorted(result.items()))


def load_basic_zones(geometry_zip: Path) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    frame = gpd.read_file(f"zip://{geometry_zip}!H30_gis/H30_kzone.shp")
    zones = {}
    repaired = []
    for _, row in frame.iterrows():
        code = f"{int(row['kzone']):04d}"
        geometry = row.geometry
        if not geometry.is_valid:
            geometry = geometry.buffer(0)
            repaired.append(code)
        zones[code] = geometry
    if len(zones) != 615:
        raise ValueError(f"unexpected official planning-basic zone population: {len(zones)}")
    frame.attrs["repaired_zone_codes"] = repaired
    return frame, zones


def load_zone_names(path: Path) -> dict[str, dict[str, str]]:
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book["市区町村別ゾーン一覧"]
    collected: dict[str, dict[str, set[str]]] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        prefecture, municipality, _, medium, basic, _ = row
        if basic is None:
            continue
        code = str(basic).zfill(4)
        record = collected.setdefault(code, {
            "prefecture": set(), "municipality": set(), "medium_zone": set(),
        })
        record["prefecture"].add(str(prefecture))
        record["municipality"].add(str(municipality))
        record["medium_zone"].add(str(medium).zfill(3))
    return {
        code: {key: ";".join(sorted(values)) for key, values in record.items()}
        for code, record in collected.items()
    }


def write_candidate_csv(
    path: Path, candidates: dict[tuple[str, str], dict[str, float]],
    names: dict[str, dict[str, str]],
) -> None:
    fields = [
        "origin_zone", "origin_prefecture", "origin_municipality", "origin_medium_zone",
        "destination_zone", "destination_prefecture", "destination_municipality",
        "destination_medium_zone", "automobile_person_trips", "ota_chord_length_m",
        "centroid_distance_m",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for (origin, destination), values in candidates.items():
            writer.writerow({
                "origin_zone": origin, "origin_prefecture": names[origin]["prefecture"],
                "origin_municipality": names[origin]["municipality"],
                "origin_medium_zone": names[origin]["medium_zone"],
                "destination_zone": destination,
                "destination_prefecture": names[destination]["prefecture"],
                "destination_municipality": names[destination]["municipality"],
                "destination_medium_zone": names[destination]["medium_zone"],
                "automobile_person_trips": f"{values['person_trips']:.6f}",
                "ota_chord_length_m": f"{values['ota_chord_length_m']:.3f}",
                "centroid_distance_m": f"{values['centroid_distance_m']:.3f}",
            })


def write_external_taz(
    path: Path, used: set[str], sumo_zones: dict[str, Any], candidates: dict[str, Any],
    gateway_count: int,
) -> None:
    root = ET.Element("additional")
    for code in sorted(used):
        taz = ET.SubElement(root, "taz", {"id": f"EXT_KZ_{code}"})
        sources = nearest_gateways(sumo_zones[code].centroid, candidates["sources"], gateway_count)
        sinks = nearest_gateways(sumo_zones[code].centroid, candidates["sinks"], gateway_count)
        for edge, weight in sources.items():
            ET.SubElement(taz, "tazSource", {"id": edge, "weight": f"{weight:.9f}"})
        for edge, weight in sinks.items():
            ET.SubElement(taz, "tazSink", {"id": edge, "weight": f"{weight:.9f}"})
    ET.indent(root); ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_unit_relations(path: Path, candidates: dict[tuple[str, str], Any]) -> None:
    root = ET.Element("data")
    interval = ET.SubElement(root, "interval", {"id": "diagnostic_unit", "begin": "0", "end": "43200"})
    for origin, destination in candidates:
        ET.SubElement(interval, "tazRelation", {
            "from": f"EXT_KZ_{origin}", "to": f"EXT_KZ_{destination}", "count": "1",
        })
    ET.indent(root); ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def route_od_population(path: Path) -> set[tuple[str, str]]:
    result = set()
    for _, flow in ET.iterparse(path, events=("end",)):
        if flow.tag != "flow":
            continue
        if flow.get("fromTaz") and flow.get("toTaz"):
            origin = flow.get("fromTaz", "").removeprefix("EXT_KZ_")
            destination = flow.get("toTaz", "").removeprefix("EXT_KZ_")
            routes = flow.findall("route")
            distribution = flow.find("routeDistribution")
            if distribution is not None:
                routes = distribution.findall("route")
            if any((route.get("edges") or "").strip() for route in routes):
                result.add((origin, destination))
        flow.clear()
    return result


def write_assessment(
    output: Path, candidates: dict[tuple[str, str], dict[str, float]],
    names: dict[str, dict[str, str]], routes1: Path, routes3: Path,
) -> dict[str, Any]:
    one = route_od_population(routes1); three = route_od_population(routes3)
    stable = one & three
    rows = []
    for od in sorted(stable):
        values = candidates[od]; origin, destination = od
        rows.append({
            "origin_zone": origin, "origin_prefecture": names[origin]["prefecture"],
            "origin_municipality": names[origin]["municipality"],
            "destination_zone": destination,
            "destination_prefecture": names[destination]["prefecture"],
            "destination_municipality": names[destination]["municipality"],
            "automobile_person_trips": values["person_trips"],
            "route_support_gateway1": True, "route_support_gateway3": True,
            "semantic_type": "exploratory_automobile_person_trips_not_driver_vehicle_demand",
        })
    with (output / "stable_through_od_candidates.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    corridor = defaultdict(float); prefecture_corridor = defaultdict(float)
    origins = defaultdict(float); destinations = defaultdict(float)
    for row in rows:
        count = float(row["automobile_person_trips"])
        corridor[(row["origin_prefecture"], row["origin_municipality"], row["destination_prefecture"], row["destination_municipality"])] += count
        prefecture_corridor[(row["origin_prefecture"], row["destination_prefecture"])] += count
        origins[(row["origin_zone"], row["origin_prefecture"], row["origin_municipality"])] += count
        destinations[(row["destination_zone"], row["destination_prefecture"], row["destination_municipality"])] += count
    def ranked(values: dict[Any, float], limit: int = 30) -> list[dict[str, Any]]:
        return [{"key": list(key), "person_trips": count} for key, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]]
    ranked_pairs = sorted(rows, key=lambda row: (-float(row["automobile_person_trips"]), row["origin_zone"], row["destination_zone"]))
    total_person_trips = sum(float(row["automobile_person_trips"]) for row in rows)
    concentration = {}
    for threshold in (0.5, 0.8, 0.9):
        accumulated = 0.0
        for index, row in enumerate(ranked_pairs, 1):
            accumulated += float(row["automobile_person_trips"])
            if accumulated / total_person_trips >= threshold:
                concentration[f"od_pairs_for_{round(threshold * 100)}_percent"] = index
                break
    origin_scope = sorted({row["origin_zone"] for row in rows})
    destination_scope = sorted({row["destination_zone"] for row in rows})
    query_scope = {
        "survey_year": "平成30年", "zone_level": "計画基本ゾーン",
        "origin_zone_count": len(origin_scope), "destination_zone_count": len(destination_scope),
        "zone_union_count": len(set(origin_scope) | set(destination_scope)),
        "origin_zones": origin_scope, "destination_zones": destination_scope,
        "retain_exact_directed_pairs_from": "stable_through_od_candidates.csv",
        "driver_status": "1_運転した", "purpose": "合計",
        "exclude": ["合計行", "その他地域", "圏域外合計", "不明", "大田区を発着するOD"],
        "exploratory_person_trip_counts_must_not_be_joined_as_vehicle_counts": True,
    }
    (output / "official_driver_od_query_scope.json").write_text(
        json.dumps(query_scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    overlap_sensitivity = {}
    for threshold_m in (0, 100, 250, 500, 1000, 2000, 5000):
        selected = [od for od in stable if candidates[od]["ota_chord_length_m"] >= threshold_m]
        overlap_sensitivity[str(threshold_m)] = {
            "od_count": len(selected),
            "automobile_person_trips": round(sum(candidates[od]["person_trips"] for od in selected)),
        }
    assessment = {
        "geographic_candidate_od_count": len(candidates),
        "geographic_candidate_person_trips": round(sum(v["person_trips"] for v in candidates.values())),
        "gateway1_routed_od_count": len(one), "gateway3_routed_od_count": len(three),
        "stable_routed_od_count": len(stable),
        "stable_routed_person_trips": round(sum(candidates[od]["person_trips"] for od in stable)),
        "gateway_disagreement_od_count": len(one ^ three),
        "unique_origin_zone_count": len(origin_scope),
        "unique_destination_zone_count": len(destination_scope),
        "unique_zone_union_count": len(set(origin_scope) | set(destination_scope)),
        "od_concentration": concentration,
        "top_directed_od_pairs": [{
            "origin_zone": row["origin_zone"], "origin_municipality": row["origin_municipality"],
            "destination_zone": row["destination_zone"],
            "destination_municipality": row["destination_municipality"],
            "person_trips": float(row["automobile_person_trips"]),
        } for row in ranked_pairs[:30]],
        "top_origin_zones": ranked(origins), "top_destination_zones": ranked(destinations),
        "top_prefecture_corridors": ranked(prefecture_corridor),
        "top_municipality_corridors": ranked(corridor),
        "geometry_overlap_sensitivity_m": overlap_sensitivity,
        "method_limitations": [
            "planning-basic-zone centroid chords are a geographic screening approximation, not observed routes",
            "the clipped Ota SUMO network cannot test whether an external regional route would avoid Ota",
            "gateway-count agreement establishes internal connectivity robustness only",
            "therefore all 727 candidates remain acquisition scope; no overlap threshold is promoted to formal truth",
        ],
        "formal_demand_status": "not_eligible_missing_driver_status",
        "recommended_official_query": {
            "zone_level": "planning-basic zone",
            "origin_destination_scope": (
                f"{len(origin_scope)} origin zones x {len(destination_scope)} destination zones, "
                f"then retain the exact {len(stable)} directed pairs listed in stable_through_od_candidates.csv"
            ),
            "driver_status": "1_運転した",
            "purpose": "合計",
            "survey_year": "平成30年",
            "directions": "retain directed OD",
        },
        "2024_police_data": "not_read_not_used",
    }
    (output / "through_prior_assessment.json").write_text(
        json.dumps(assessment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return assessment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-csv", type=Path, required=True)
    parser.add_argument("--geometry-zip", type=Path, required=True)
    parser.add_argument("--zone-code-xlsx", type=Path, required=True)
    parser.add_argument("--net", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--routes-gateway1", type=Path)
    parser.add_argument("--routes-gateway3", type=Path)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)

    frame, zones = load_basic_zones(args.geometry_zip)
    totals, accounting = read_external_automobile_person_od(args.raw_csv, set(zones), OTA_BASIC_ZONES)
    ota = unary_union([zones[code] for code in OTA_BASIC_ZONES])
    centroids = {code: geometry.centroid for code, geometry in zones.items()}
    geographic = geographic_candidates(totals, centroids, ota)
    names = load_zone_names(args.zone_code_xlsx)
    write_candidate_csv(args.output / "geographic_through_candidates.csv", geographic, names)

    if args.routes_gateway1 and args.routes_gateway3:
        print(json.dumps(write_assessment(
            args.output, geographic, names, args.routes_gateway1, args.routes_gateway3
        ), ensure_ascii=False, indent=2)); return

    location = read_location(args.net)
    sumo_zones = {code: to_sumo_geometry(geometry, frame.crs, location) for code, geometry in zones.items()}
    edges, _ = load_passenger_edges(args.net)
    ota_sumo = unary_union([sumo_zones[code] for code in OTA_BASIC_ZONES])
    gateways = gateway_candidates(edges, ota_sumo)
    used = {code for od in geographic for code in od}
    write_external_taz(args.output / "external_basic_zones_gateway1.taz.xml", used, sumo_zones, gateways, 1)
    write_external_taz(args.output / "external_basic_zones_gateway3.taz.xml", used, sumo_zones, gateways, 3)
    write_unit_relations(args.output / "geographic_candidates_unit.taz_relations.xml", geographic)
    summary = {
        "input_accounting": accounting,
        "external_external_od_count": len(totals),
        "external_external_automobile_person_trips": round(sum(totals.values())),
        "geographic_candidate_od_count": len(geographic),
        "geographic_candidate_automobile_person_trips": round(sum(v["person_trips"] for v in geographic.values())),
        "diagnostic_route_count_per_od": 1,
        "diagnostic_count_semantics": "unit route-support probe; not person count and not vehicle demand",
        "geometry_repairs": {
            "rule": "invalid official polygon topology repaired with zero-width buffer without changing zone identity",
            "zone_codes": frame.attrs.get("repaired_zone_codes", []),
        },
        "observation_values_used": False, "2024_police_data": "not_read_not_used",
    }
    (args.output / "extraction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
