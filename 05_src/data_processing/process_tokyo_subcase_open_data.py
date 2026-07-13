from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pyogrio
from shapely import box
from shapely.geometry import LineString, MultiLineString


ROOT = Path(__file__).resolve().parents[1]
ESTAT_CSV = ROOT / "data" / "raw" / "estat" / "tokyo" / "326_20260704_v02_estat_2020_population_census_table_1_1_3_tokyo_2026_07_04.csv"
OSM_ZIP = ROOT / "data" / "raw" / "osm" / "tokyo" / "329_20260704_v02_kanto_260703_free_shp.zip"

VARIABLES_CSV = ROOT / "data" / "processed" / "449_20260705_socio_technical_variables.csv"
ESTAT_SUMMARY_CSV = ROOT / "data" / "processed" / "415_20260704_estat_tokyo_population_summary.csv"
OSM_SUMMARY_CSV = ROOT / "data" / "processed" / "433_20260704_osm_tokyo_road_network_summary.csv"

TOKYO_BBOX = {
    "min_lon": 139.45,
    "min_lat": 35.50,
    "max_lon": 139.95,
    "max_lat": 35.90,
}

DRIVABLE_FCLASSES = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "unclassified",
    "residential",
    "living_street",
    "service",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        all_rows = list(csv.reader(f))
    header_index = next(i for i, row in enumerate(all_rows) if row and row[0] == "Time Code")
    headers = all_rows[header_index]
    return [dict(zip(headers, row)) for row in all_rows[header_index + 1 :] if row]


def clean_number(value: str) -> float:
    return float(value.replace(",", "").strip())


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def process_estat() -> list[dict[str, Any]]:
    rows = read_rows(ESTAT_CSV)
    tokyo = next(row for row in rows if row["All Municipalities (including those as of 2000)"] == "Tokyo-to")
    summary = [
        {
            "variable_id": "population_tokyo_2020",
            "value": int(clean_number(tokyo["Population in 2015 (readjusted)[people]"]) + clean_number(tokyo["Population change number for 5 years[people]"])),
            "unit": "people",
            "source_file": str(ESTAT_CSV.relative_to(ROOT)),
            "processing_rule": "Tokyo-to row from 2020 Population Census Table 1-1-3; 2020 population reconstructed from 2015 readjusted population plus 5-year population change.",
            "limitation": "Prefecture-level value; not mesh-level customer demand.",
        },
        {
            "variable_id": "population_density_tokyo_mesh",
            "value": clean_number(tokyo["Population density[per km2]"]),
            "unit": "persons per km2",
            "source_file": str(ESTAT_CSV.relative_to(ROOT)),
            "processing_rule": "Tokyo-to population density from 2020 Population Census Table 1-1-3.",
            "limitation": "This is Tokyo-to aggregate density, not grid-square density. Use as first-pass demand concentration proxy.",
        },
        {
            "variable_id": "area_tokyo_2020_reference",
            "value": clean_number(tokyo["Area (reference)[km2]"]),
            "unit": "km2",
            "source_file": str(ESTAT_CSV.relative_to(ROOT)),
            "processing_rule": "Tokyo-to reference area from 2020 Population Census Table 1-1-3.",
            "limitation": "Reference area used by the census table.",
        },
    ]
    write_csv(
        ESTAT_SUMMARY_CSV,
        summary,
        ["variable_id", "value", "unit", "source_file", "processing_rule", "limitation"],
    )
    return summary


def endpoints(geom: Any) -> list[tuple[float, float]]:
    if geom is None or geom.is_empty:
        return []
    lines: list[LineString]
    if isinstance(geom, LineString):
        lines = [geom]
    elif isinstance(geom, MultiLineString):
        lines = list(geom.geoms)
    else:
        return []
    out: list[tuple[float, float]] = []
    for line in lines:
        coords = list(line.coords)
        if len(coords) >= 2:
            out.append((round(coords[0][0], 5), round(coords[0][1], 5)))
            out.append((round(coords[-1][0], 5), round(coords[-1][1], 5)))
    return out


def process_osm() -> list[dict[str, Any]]:
    roads_path = f"/vsizip/{OSM_ZIP}/gis_osm_roads_free_1.shp"
    bbox = (TOKYO_BBOX["min_lon"], TOKYO_BBOX["min_lat"], TOKYO_BBOX["max_lon"], TOKYO_BBOX["max_lat"])
    roads = pyogrio.read_dataframe(roads_path, bbox=bbox)
    roads = roads[roads["fclass"].isin(DRIVABLE_FCLASSES)].copy()
    roads_gdf = gpd.GeoDataFrame(roads, geometry="geometry", crs="EPSG:4326")
    roads_projected = roads_gdf.to_crs("EPSG:6677")

    bbox_poly = gpd.GeoSeries(
        [box(*bbox)],
        crs="EPSG:4326",
    ).to_crs("EPSG:6677")
    area_km2 = float(bbox_poly.area.iloc[0] / 1_000_000)
    road_length_km = float(roads_projected.length.sum() / 1000)
    road_density = road_length_km / area_km2 if area_km2 else 0.0

    endpoint_counter: Counter[tuple[float, float]] = Counter()
    for geom in roads_projected.geometry:
        endpoint_counter.update(endpoints(geom))
    intersection_proxy = sum(1 for count in endpoint_counter.values() if count >= 2)

    summary = [
        {
            "variable_id": "road_network_density_tokyo_snapshot",
            "value": round(road_density, 3),
            "unit": "km per km2",
            "source_file": str(OSM_ZIP.relative_to(ROOT)),
            "processing_rule": "Read Geofabrik Kanto roads shapefile within Tokyo approximate bounding box; kept drivable road classes; road length projected to EPSG:6677 and divided by bbox area.",
            "limitation": "Bounding-box proxy, not official Tokyo boundary. Road length depends on OSM completeness and included road classes.",
        },
        {
            "variable_id": "road_intersections_tokyo_snapshot",
            "value": intersection_proxy,
            "unit": "intersection proxy count",
            "source_file": str(OSM_ZIP.relative_to(ROOT)),
            "processing_rule": "Counted rounded drivable-road endpoints shared by at least two road segments after projection.",
            "limitation": "Endpoint-based proxy; grade-separated crossings and unsplit geometries may be under/over-counted.",
        },
        {
            "variable_id": "road_length_tokyo_bbox_snapshot",
            "value": round(road_length_km, 3),
            "unit": "km",
            "source_file": str(OSM_ZIP.relative_to(ROOT)),
            "processing_rule": "Total drivable road length in approximate Tokyo bounding box.",
            "limitation": "Auxiliary metric for interpreting road density.",
        },
        {
            "variable_id": "tokyo_bbox_area_snapshot",
            "value": round(area_km2, 3),
            "unit": "km2",
            "source_file": str(OSM_ZIP.relative_to(ROOT)),
            "processing_rule": "Area of approximate Tokyo bounding box after projection to EPSG:6677.",
            "limitation": "Not the official Tokyo-to area.",
        },
    ]
    write_csv(
        OSM_SUMMARY_CSV,
        summary,
        ["variable_id", "value", "unit", "source_file", "processing_rule", "limitation"],
    )
    return summary


def update_variables(summary_rows: list[dict[str, Any]]) -> None:
    with VARIABLES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    by_id = {row["variable_id"]: row for row in rows}
    for item in summary_rows:
        variable_id = str(item["variable_id"])
        if variable_id not in by_id:
            row = {key: "" for key in fieldnames}
            row["variable_id"] = variable_id
            rows.append(row)
            by_id[variable_id] = row
        row = by_id[variable_id]
        row.update(
            {
                "country": "Japan",
                "city": "Tokyo",
                "year": "2020" if "population" in variable_id or "area_tokyo_2020" in variable_id else "2026-07-04",
                "value": item["value"],
                "unit": item["unit"],
                "local_raw_path": item["source_file"],
                "status": "extracted",
                "processing_rule": item["processing_rule"],
                "limitation": item["limitation"],
            }
        )
        if variable_id.startswith("population") or variable_id.startswith("area_tokyo"):
            row["source_id"] = "estat_mesh"
            row["source_url"] = "https://www.e-stat.go.jp/en/statistics/00200521"
            row["spatial_level"] = "prefecture"
            row["temporal_level"] = "census"
            row["analysis_axis"] = "Demand concentration proxy"
            row["use_case_relevance"] = "Tokyo population density proxy for customer-node concentration."
        elif variable_id.startswith("road"):
            row["source_id"] = "osm_road_network"
            row["source_url"] = "https://download.geofabrik.de/asia/japan/kanto.html"
            row["spatial_level"] = "city bounding box"
            row["temporal_level"] = "snapshot"
            row["analysis_axis"] = "Urban network complexity"
            row["use_case_relevance"] = "Tokyo road-network complexity proxy for charging-aware last-mile routing."
    write_csv(VARIABLES_CSV, rows, fieldnames)


def main() -> None:
    summaries = []
    summaries.extend(process_estat())
    summaries.extend(process_osm())
    update_variables(summaries)
    print(ESTAT_SUMMARY_CSV)
    print(OSM_SUMMARY_CSV)
    for item in summaries:
        print(f"{item['variable_id']}={item['value']} {item['unit']}")


if __name__ == "__main__":
    main()
