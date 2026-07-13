from __future__ import annotations

import csv
import json
import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_BOUNDARY_ZIP = ROOT / "03_data/raw/boundary/mlit_n03_tokyo/328_20240101_v02_n03_20240101_13_gml.zip"
RAW_MESH_ZIP = ROOT / "03_data/raw/estat/tokyo_mesh/327_20260705_v02_tblt001101h13.zip"
RAW_POLICE_ZIP = ROOT / "03_data/raw/smart_city/traffic/tokyo_metropolitan_police/02_cyousakekka_csv.zip"
RAW_ROAD_CENSUS = ROOT / "03_data/raw/smart_city/traffic/mlit_road_census_tokyo/zkntrf13.csv"

PROCESSED = ROOT / "data/processed"
INVENTORY = ROOT / "literature/use_case_scenario/213_20260705_open_data_source_inventory.csv"
SOCIO = ROOT / "03_data/processed/449_20260705_socio_technical_variables.csv"
FW_STATUS = ROOT / "outputs/use_case_scenario/future_wheels_pre_analysis_action_status.csv"


def clean_number(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().replace(",", "")
    if text in {"", "*", "-", "nan"}:
        return pd.NA
    return pd.to_numeric(text, errors="coerce")


def upsert_rows(path: Path, key: str, rows: list[dict]) -> None:
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame()
    incoming = pd.DataFrame(rows)
    if existing.empty:
        incoming.to_csv(path, index=False)
        return
    for column in incoming.columns:
        if column not in existing.columns:
            existing[column] = pd.NA
    for column in existing.columns:
        if column not in incoming.columns:
            incoming[column] = pd.NA
    existing = existing[~existing[key].isin(incoming[key])]
    pd.concat([existing, incoming[existing.columns]], ignore_index=True).to_csv(path, index=False)


def process_boundary() -> dict:
    out_summary = PROCESSED / "451_20260705_tokyo_boundary_n03_summary.csv"
    out_municipalities = PROCESSED / "450_20260705_tokyo_boundary_n03_municipalities.csv"
    with zipfile.ZipFile(RAW_BOUNDARY_ZIP) as zf:
        zf.extractall(PROCESSED / "_tmp_n03_tokyo")
    geojson_path = PROCESSED / "_tmp_n03_tokyo/N03-20240101_13.geojson"
    gdf = gpd.read_file(geojson_path)
    gdf_6677 = gdf.to_crs(6677)
    valid_municipalities = gdf["N03_004"].dropna()
    municipalities = (
        gdf[["N03_001", "N03_004", "N03_007"]]
        .drop_duplicates()
        .rename(columns={"N03_001": "prefecture", "N03_004": "municipality", "N03_007": "admin_code"})
        .sort_values(["admin_code", "municipality"])
    )
    municipalities.to_csv(out_municipalities, index=False)
    minx, miny, maxx, maxy = gdf.total_bounds
    summary = {
        "source_id": "mlit_n03_tokyo_boundary",
        "feature_count": int(len(gdf)),
        "municipality_count_including_unassigned": int(valid_municipalities.nunique()),
        "area_km2_epsg6677": round(float(gdf_6677.geometry.area.sum() / 1_000_000), 3),
        "bbox_min_lon": round(float(minx), 6),
        "bbox_min_lat": round(float(miny), 6),
        "bbox_max_lon": round(float(maxx), 6),
        "bbox_max_lat": round(float(maxy), 6),
        "processed_file": str(out_municipalities.relative_to(ROOT)),
    }
    pd.DataFrame([summary]).to_csv(out_summary, index=False)
    shutil.rmtree(PROCESSED / "_tmp_n03_tokyo", ignore_errors=True)
    return summary


def process_mesh() -> dict:
    out_cells = PROCESSED / "413_20260705_estat_tokyo_mesh_population_cells.csv"
    out_summary = PROCESSED / "414_20260705_estat_tokyo_mesh_population_summary.csv"
    with zipfile.ZipFile(RAW_MESH_ZIP) as zf:
        with zf.open("tblT001101H13.txt") as f:
            rows = list(csv.reader((line.decode("cp932") for line in f)))
    code_row, label_row, *data_rows = rows
    df = pd.DataFrame(data_rows, columns=code_row)
    labels = dict(zip(code_row, label_row))
    population_col = "T001101001"
    households_col = "T001101034"
    cells = pd.DataFrame(
        {
            "mesh_code": df["KEY_CODE"],
            "total_population": df[population_col].map(clean_number),
            "total_households": df[households_col].map(clean_number),
            "htksyori": df["HTKSYORI"],
            "htksaki": df["HTKSAKI"],
        }
    )
    cells["total_population"] = pd.to_numeric(cells["total_population"], errors="coerce")
    cells["total_households"] = pd.to_numeric(cells["total_households"], errors="coerce")
    cells.to_csv(out_cells, index=False)
    populated = cells[cells["total_population"].fillna(0) > 0]
    summary = {
        "source_id": "estat_tokyo_mesh_population",
        "mesh_cell_count": int(len(cells)),
        "populated_mesh_cell_count": int(len(populated)),
        "total_population": int(cells["total_population"].sum(skipna=True)),
        "total_households": int(cells["total_households"].sum(skipna=True)),
        "max_population_in_mesh": int(cells["total_population"].max(skipna=True)),
        "population_column": population_col,
        "population_column_label": labels.get(population_col, "").strip(),
        "households_column": households_col,
        "households_column_label": labels.get(households_col, "").strip(),
        "processed_file": str(out_cells.relative_to(ROOT)),
    }
    pd.DataFrame([summary]).to_csv(out_summary, index=False)
    return summary


def process_police_traffic() -> dict:
    out_inventory = PROCESSED / "461_20260705_tokyo_police_traffic_stats_inventory.csv"
    out_border = PROCESSED / "460_20260705_tokyo_police_traffic_border_hourly_all_vehicles.csv"
    out_summary = PROCESSED / "462_20260705_tokyo_police_traffic_stats_summary.csv"
    with zipfile.ZipFile(RAW_POLICE_ZIP) as zf:
        inventory = pd.DataFrame(
            [{"file_name": info.filename, "file_size_bytes": info.file_size} for info in zf.infolist()]
        )
        inventory.to_csv(out_inventory, index=False)
        with zf.open("2-2-15jikanbetu_ryuusyutunyuu_zensya.csv") as f:
            border = pd.read_csv(f, encoding="cp932")
    for col in ["昼12時間計", "夜12時間計", "24時間計"]:
        border[col] = border[col].map(clean_number)
    border.to_csv(out_border, index=False)
    summary = {
        "source_id": "tokyo_police_traffic_statistics",
        "file_count": int(len(inventory)),
        "representative_file": "2-2-15jikanbetu_ryuusyutunyuu_zensya.csv",
        "border_observation_rows": int(len(border)),
        "border_24h_total_vehicles": int(border["24時間計"].sum(skipna=True)),
        "border_daytime_12h_total_vehicles": int(border["昼12時間計"].sum(skipna=True)),
        "border_nighttime_12h_total_vehicles": int(border["夜12時間計"].sum(skipna=True)),
        "processed_file": str(out_border.relative_to(ROOT)),
    }
    pd.DataFrame([summary]).to_csv(out_summary, index=False)
    return summary


def process_road_census() -> dict:
    out_summary = PROCESSED / "427_20260705_mlit_road_census_tokyo_traffic_summary.csv"
    out_by_class = PROCESSED / "426_20260705_mlit_road_census_tokyo_traffic_by_vehicle_class.csv"
    df = pd.read_csv(RAW_ROAD_CENSUS, encoding="cp932")
    for col in ["昼間１２時間自動車類交通量（台）", "２４時間自動車類交通量（台）"]:
        df[col] = df[col].map(clean_number)
    by_class = (
        df.groupby("車種区分", dropna=False)
        .agg(
            rows=("車種区分", "size"),
            daytime_12h_vehicles=("昼間１２時間自動車類交通量（台）", "sum"),
            vehicles_24h=("２４時間自動車類交通量（台）", "sum"),
        )
        .reset_index()
    )
    by_class.to_csv(out_by_class, index=False)
    unique_segments = df[["都道府県指定市コード", "交通量調査単位区間番号"]].drop_duplicates()
    summary = {
        "source_id": "mlit_road_census_tokyo",
        "row_count": int(len(df)),
        "survey_segment_count": int(len(unique_segments)),
        "daytime_12h_observation_rows": int(df["昼間１２時間自動車類交通量（台）"].notna().sum()),
        "twenty_four_hour_observation_rows": int(df["２４時間自動車類交通量（台）"].notna().sum()),
        "total_daytime_12h_vehicles": int(df["昼間１２時間自動車類交通量（台）"].sum(skipna=True)),
        "total_24h_vehicles": int(df["２４時間自動車類交通量（台）"].sum(skipna=True)),
        "vehicle_class_count": int(df["車種区分"].nunique(dropna=True)),
        "processed_file": str(out_by_class.relative_to(ROOT)),
    }
    pd.DataFrame([summary]).to_csv(out_summary, index=False)
    return summary


def update_research_tables(boundary: dict, mesh: dict, police: dict, road: dict) -> None:
    upsert_rows(
        INVENTORY,
        "source_id",
        [
            {
                "source_id": "mlit_n03_tokyo_boundary",
                "source_name": "National Land Numerical Information administrative boundary data for Tokyo",
                "provider": "MLIT National Land Numerical Information",
                "url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2024.html",
                "local_raw_path": "03_data/raw/boundary/mlit_n03_tokyo/328_20240101_v02_n03_20240101_13_gml.zip",
                "data_type": "GIS boundary zip",
                "collection_method": "manual download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "MLIT National Land Numerical Information terms",
                "spatial_level": "Tokyo prefecture / municipality polygons",
                "temporal_level": "2024 boundary",
                "use_in_analysis": "Official Tokyo boundary for clipping, area normalization, and Tokyo-scope definition.",
                "limitation": "Boundary data defines administrative geography; it does not provide demand, traffic, depot, or charging behavior.",
                "collection_status": "local_existing",
            },
            {
                "source_id": "estat_tokyo_mesh_population",
                "source_name": "2020 Population Census grid-square statistics for Tokyo",
                "provider": "e-Stat / Statistics Bureau of Japan",
                "url": "https://www.e-stat.go.jp/gis/statmap-search?page=1&toukeiCode=00200521&type=1",
                "local_raw_path": "03_data/raw/estat/tokyo_mesh/327_20260705_v02_tblt001101h13.zip",
                "data_type": "mesh csv zip",
                "collection_method": "manual download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "e-Stat terms",
                "spatial_level": "Tokyo grid-square mesh",
                "temporal_level": "2020 census",
                "use_in_analysis": "Customer-node density proxy for the Tokyo EV routing use case.",
                "limitation": "Population mesh is a proxy for spatial demand concentration; it is not observed parcel, depot, or EV route demand.",
                "collection_status": "local_existing",
            },
            {
                "source_id": "tokyo_police_traffic_statistics",
                "source_name": "Tokyo Metropolitan Police traffic volume statistics",
                "provider": "Tokyo Metropolitan Police / Tokyo Open Data Catalog",
                "url": "https://catalog.data.metro.tokyo.lg.jp/dataset/t000022d0000000035",
                "local_raw_path": "03_data/raw/smart_city/traffic/tokyo_metropolitan_police/02_cyousakekka_csv.zip",
                "data_type": "traffic statistics csv zip",
                "collection_method": "manual download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "Tokyo Open Data Catalog terms",
                "spatial_level": "Tokyo road observation points / borders",
                "temporal_level": "periodic traffic survey",
                "use_in_analysis": "Static traffic-volume context for congestion and travel-cost uncertainty branches.",
                "limitation": "Traffic-volume statistics are not EV delivery routes, customer demand, depot data, or realtime dispatch decisions.",
                "collection_status": "local_existing",
            },
            {
                "source_id": "mlit_road_census_tokyo",
                "source_name": "Road Traffic Census Tokyo traffic-volume table",
                "provider": "MLIT Road Traffic Census",
                "url": "https://www.mlit.go.jp/road/census/r3/",
                "local_raw_path": "03_data/raw/smart_city/traffic/mlit_road_census_tokyo/zkntrf13.csv",
                "data_type": "road census csv",
                "collection_method": "manual download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "MLIT terms",
                "spatial_level": "Tokyo road survey segments",
                "temporal_level": "FY2021 survey",
                "use_in_analysis": "Static road traffic-volume proxy for Tokyo routing environment complexity.",
                "limitation": "Road census volumes are road-segment traffic observations; they do not identify commercial EV routes or charging behavior.",
                "collection_status": "local_existing",
            },
        ],
    )

    socio_rows = [
        {
            "variable_id": "tokyo_n03_boundary_area_km2",
            "source_id": "mlit_n03_tokyo_boundary",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2024,
            "variable_name": "Tokyo official boundary area",
            "value": boundary["area_km2_epsg6677"],
            "unit": "square kilometers",
            "spatial_level": "Tokyo prefecture boundary polygons",
            "temporal_level": "2024 boundary",
            "analysis_axis": "Tokyo scope definition",
            "use_case_relevance": "Defines the spatial scope for Tokyo public-data proxies.",
            "processing_rule": "Sum polygon area after projecting N03 Tokyo GeoJSON to EPSG:6677.",
            "limitation": "Administrative area does not measure routing demand or EV operation.",
            "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2024.html",
            "local_raw_path": "03_data/raw/boundary/mlit_n03_tokyo/328_20240101_v02_n03_20240101_13_gml.zip",
            "status": "extracted",
        },
        {
            "variable_id": "estat_tokyo_mesh_total_population",
            "source_id": "estat_tokyo_mesh_population",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2020,
            "variable_name": "Tokyo mesh total population",
            "value": mesh["total_population"],
            "unit": "persons",
            "spatial_level": "Tokyo grid-square mesh",
            "temporal_level": "2020 census",
            "analysis_axis": "Demand concentration proxy",
            "use_case_relevance": "Proxy for potential customer-node density in Tokyo EV last-mile routing.",
            "processing_rule": "Sum T001101001 total population across Tokyo mesh rows.",
            "limitation": "Population is not parcel demand, delivery stops, depot locations, or vehicle routes.",
            "source_url": "https://www.e-stat.go.jp/gis/statmap-search?page=1&toukeiCode=00200521&type=1",
            "local_raw_path": "03_data/raw/estat/tokyo_mesh/327_20260705_v02_tblt001101h13.zip",
            "status": "extracted",
        },
        {
            "variable_id": "estat_tokyo_populated_mesh_cells",
            "source_id": "estat_tokyo_mesh_population",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2020,
            "variable_name": "Tokyo populated mesh cells",
            "value": mesh["populated_mesh_cell_count"],
            "unit": "mesh cells",
            "spatial_level": "Tokyo grid-square mesh",
            "temporal_level": "2020 census",
            "analysis_axis": "Demand concentration proxy",
            "use_case_relevance": "Indicates spatial granularity available for synthetic customer-node placement.",
            "processing_rule": "Count mesh rows with T001101001 total population greater than zero.",
            "limitation": "Mesh count is spatial granularity, not actual delivery-node count.",
            "source_url": "https://www.e-stat.go.jp/gis/statmap-search?page=1&toukeiCode=00200521&type=1",
            "local_raw_path": "03_data/raw/estat/tokyo_mesh/327_20260705_v02_tblt001101h13.zip",
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_police_border_24h_traffic",
            "source_id": "tokyo_police_traffic_statistics",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2024,
            "variable_name": "Tokyo border 24-hour traffic in selected police statistics file",
            "value": police["border_24h_total_vehicles"],
            "unit": "vehicles per 24 hours across representative border observations",
            "spatial_level": "Tokyo border observation points",
            "temporal_level": "periodic traffic survey",
            "analysis_axis": "Traffic intensity proxy",
            "use_case_relevance": "Static context for congestion and travel-cost uncertainty in the Tokyo use case.",
            "processing_rule": "Sum 24時間計 from 2-2-15jikanbetu_ryuusyutunyuu_zensya.csv.",
            "limitation": "Representative traffic statistic, not delivery routes, customer demand, or realtime dispatch.",
            "source_url": "https://catalog.data.metro.tokyo.lg.jp/dataset/t000022d0000000035",
            "local_raw_path": "03_data/raw/smart_city/traffic/tokyo_metropolitan_police/02_cyousakekka_csv.zip",
            "status": "extracted",
        },
        {
            "variable_id": "mlit_road_census_tokyo_segments",
            "source_id": "mlit_road_census_tokyo",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2021,
            "variable_name": "Tokyo road census survey segments",
            "value": road["survey_segment_count"],
            "unit": "survey segments",
            "spatial_level": "Tokyo road survey segments",
            "temporal_level": "FY2021 road traffic census",
            "analysis_axis": "Traffic intensity proxy",
            "use_case_relevance": "Road-network observation granularity for Tokyo routing environment complexity.",
            "processing_rule": "Count unique prefecture-code and traffic-survey-unit-section combinations.",
            "limitation": "Survey segment count is not a vehicle fleet size or delivery-customer count.",
            "source_url": "https://www.mlit.go.jp/road/census/r3/",
            "local_raw_path": "03_data/raw/smart_city/traffic/mlit_road_census_tokyo/zkntrf13.csv",
            "status": "extracted",
        },
        {
            "variable_id": "mlit_road_census_tokyo_total_24h_traffic",
            "source_id": "mlit_road_census_tokyo",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2021,
            "variable_name": "Tokyo road census total 24-hour traffic",
            "value": road["total_24h_vehicles"],
            "unit": "vehicles per 24 hours across survey rows",
            "spatial_level": "Tokyo road survey segments",
            "temporal_level": "FY2021 road traffic census",
            "analysis_axis": "Traffic intensity proxy",
            "use_case_relevance": "Static traffic-volume context for Tokyo routing environment complexity.",
            "processing_rule": "Sum non-null ２４時間自動車類交通量（台） values across rows in zkntrf13.csv.",
            "limitation": "Only rows with 24-hour observations are included in this sum; it is a traffic-intensity proxy, not EV delivery demand.",
            "source_url": "https://www.mlit.go.jp/road/census/r3/",
            "local_raw_path": "03_data/raw/smart_city/traffic/mlit_road_census_tokyo/zkntrf13.csv",
            "status": "extracted",
        },
    ]
    upsert_rows(SOCIO, "variable_id", socio_rows)

    status = pd.read_csv(FW_STATUS)
    replacements = {
        "Tokyo official boundary polygon": (
            "collected",
            "Tokyo public-data proxy",
            "N03 Tokyo administrative boundary has been collected and processed; used for Tokyo-scope definition and possible area normalization.",
        ),
        "e-Stat grid-square mesh population": (
            "collected",
            "Tokyo public-data proxy",
            "2020 Population Census Tokyo grid-square population has been collected and processed; use as customer-node density proxy, not observed delivery demand.",
        ),
        "Tokyo traffic / realtime API": (
            "collected_optional",
            "Dynamic dispatch extension",
            "JARTIC hourly API, Tokyo Metropolitan Police traffic statistics, and MLIT Road Traffic Census Tokyo data are available as traffic-intensity proxies; none directly provides EV delivery routes.",
        ),
    }
    for item, (status_value, use_value, notes) in replacements.items():
        mask = status["item"].eq(item)
        status.loc[mask, "status"] = status_value
        status.loc[mask, "use_in_future_wheels"] = use_value
        status.loc[mask, "notes"] = notes
    status.to_csv(FW_STATUS, index=False)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    boundary = process_boundary()
    mesh = process_mesh()
    police = process_police_traffic()
    road = process_road_census()
    update_research_tables(boundary, mesh, police, road)
    print(json.dumps({"boundary": boundary, "mesh": mesh, "police": police, "road": road}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
