from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "03_data/raw/logistics/mlit_logistics_hubs/323_20260705_v02_p31_13_13.zip"
TMP = ROOT / "03_data/processed/_tmp_p31"
OUT_CANDIDATES = ROOT / "03_data/processed/458_20260705_tokyo_logistics_hub_candidates.csv"
OUT_SUMMARY = ROOT / "03_data/processed/459_20260705_tokyo_logistics_hub_summary.csv"
OUT_BY_TYPE = ROOT / "03_data/processed/457_20260705_tokyo_logistics_hub_by_type.csv"
INVENTORY = ROOT / "literature/use_case_scenario/213_20260705_open_data_source_inventory.csv"
SOCIO = ROOT / "03_data/processed/449_20260705_socio_technical_variables.csv"
FW_STATUS = ROOT / "outputs/use_case_scenario/future_wheels_pre_analysis_action_status.csv"


MAJOR_TYPE = {
    1: "port_or_ferry_terminal",
    2: "airport_or_air_cargo_related_facility",
    3: "rail_freight_station_or_related_facility",
    4: "bonded_area_or_warehouse",
    5: "truck_terminal_or_parcel_operator_terminal",
    7: "wholesale_market",
}

DEPOT_RELEVANCE = {
    1: "medium",
    2: "medium",
    3: "high",
    4: "high",
    5: "high",
    7: "medium",
}


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


def mainland_tokyo_proxy(lon: float, lat: float) -> bool:
    return 35.45 <= lat <= 35.95 and 138.9 <= lon <= 140.2


def process_hubs() -> dict:
    TMP.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW) as zf:
        zf.extractall(TMP)
    shp = TMP / "P31-13_13/P31-13_13_e.shp"
    gdf = gpd.read_file(shp, encoding="cp932")
    # The source metadata states JGD2000 / (B, L); coordinates are longitude/latitude points.
    gdf = gdf.set_crs(epsg=4612, allow_override=True).to_crs(epsg=4326)
    df = pd.DataFrame(
        {
            "hub_id": [f"P31_13_{i+1:04d}" for i in range(len(gdf))],
            "facility_name": gdf["P31_001"],
            "facility_major_type_code": gdf["P31_002"].astype("Int64"),
            "facility_major_type": gdf["P31_002"].map(MAJOR_TYPE),
            "facility_subtype_code": gdf["P31_003"].astype("Int64"),
            "prefecture_code": gdf["P31_004"].astype("Int64"),
            "address_or_municipality": gdf["P31_005"],
            "source_attribute_p31_006": gdf["P31_006"],
            "source_attribute_p31_007": gdf["P31_007"],
            "area_m2_or_source_area_field": pd.to_numeric(gdf["P31_008"], errors="coerce"),
            "remarks_or_related_name": gdf["P31_009"],
            "longitude": gdf.geometry.x.round(6),
            "latitude": gdf.geometry.y.round(6),
        }
    )
    df["depot_candidate_relevance"] = df["facility_major_type_code"].map(DEPOT_RELEVANCE)
    df["mainland_tokyo_proxy"] = [
        mainland_tokyo_proxy(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])
    ]
    df["use_note"] = (
        "Candidate logistics/depot proxy from MLIT P31; not observed operator depot or delivery-route data."
    )
    df.to_csv(OUT_CANDIDATES, index=False)

    by_type = (
        df.groupby(["facility_major_type_code", "facility_major_type", "depot_candidate_relevance"], dropna=False)
        .agg(
            hub_count=("hub_id", "size"),
            mainland_tokyo_proxy_count=("mainland_tokyo_proxy", "sum"),
            area_m2_sum=("area_m2_or_source_area_field", "sum"),
        )
        .reset_index()
    )
    by_type.to_csv(OUT_BY_TYPE, index=False)

    summary = {
        "source_id": "mlit_logistics_hubs_tokyo_p31",
        "hub_count": int(len(df)),
        "mainland_tokyo_proxy_count": int(df["mainland_tokyo_proxy"].sum()),
        "high_depot_relevance_count": int(df["depot_candidate_relevance"].eq("high").sum()),
        "truck_terminal_or_parcel_operator_terminal_count": int(df["facility_major_type_code"].eq(5).sum()),
        "bonded_area_or_warehouse_count": int(df["facility_major_type_code"].eq(4).sum()),
        "rail_freight_station_or_related_facility_count": int(df["facility_major_type_code"].eq(3).sum()),
        "wholesale_market_count": int(df["facility_major_type_code"].eq(7).sum()),
        "processed_file": str(OUT_CANDIDATES.relative_to(ROOT)),
    }
    pd.DataFrame([summary]).to_csv(OUT_SUMMARY, index=False)
    shutil.rmtree(TMP, ignore_errors=True)
    return summary


def update_research_tables(summary: dict) -> None:
    upsert_rows(
        INVENTORY,
        "source_id",
        [
            {
                "source_id": "mlit_logistics_hubs_tokyo_p31",
                "source_name": "National Land Numerical Information logistics hub data for Tokyo",
                "provider": "MLIT National Land Numerical Information",
                "url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P31.html",
                "local_raw_path": "03_data/raw/logistics/mlit_logistics_hubs/323_20260705_v02_p31_13_13.zip",
                "data_type": "GIS point shapefile zip",
                "collection_method": "manual download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "MLIT National Land Numerical Information terms",
                "spatial_level": "Tokyo logistics hub points",
                "temporal_level": "P31-13 source; metadata date 2014-03-03",
                "use_in_analysis": "Depot-candidate and logistics-facility proxy for Tokyo EV delivery simulation design.",
                "limitation": "Logistics hubs are facility proxies; they are not observed operator depots, delivery routes, or fleet schedules.",
                "collection_status": "local_existing",
            }
        ],
    )
    socio_rows = [
        {
            "variable_id": "tokyo_logistics_hub_candidates_total",
            "source_id": "mlit_logistics_hubs_tokyo_p31",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2014,
            "variable_name": "Tokyo logistics hub candidate points",
            "value": summary["hub_count"],
            "unit": "points",
            "spatial_level": "Tokyo logistics hub points",
            "temporal_level": "P31-13 source",
            "analysis_axis": "Depot candidate proxy",
            "use_case_relevance": "Candidate facility set for synthetic depot placement in Tokyo EV last-mile routing scenarios.",
            "processing_rule": "Read MLIT P31 Tokyo shapefile with CP932 encoding and count all point features.",
            "limitation": "Facility count is a depot-candidate proxy and not observed operator depot usage.",
            "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P31.html",
            "local_raw_path": "03_data/raw/logistics/mlit_logistics_hubs/323_20260705_v02_p31_13_13.zip",
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_high_relevance_depot_candidate_points",
            "source_id": "mlit_logistics_hubs_tokyo_p31",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2014,
            "variable_name": "Tokyo high-relevance depot candidate points",
            "value": summary["high_depot_relevance_count"],
            "unit": "points",
            "spatial_level": "Tokyo logistics hub points",
            "temporal_level": "P31-13 source",
            "analysis_axis": "Depot candidate proxy",
            "use_case_relevance": "High-relevance depot proxy count based on rail freight, bonded/warehouse, and truck terminal categories.",
            "processing_rule": "Count P31 major categories 3, 4, and 5 as high-relevance depot candidate proxies.",
            "limitation": "Category relevance is a research classification and not evidence that the facility is available to a delivery operator.",
            "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P31.html",
            "local_raw_path": "03_data/raw/logistics/mlit_logistics_hubs/323_20260705_v02_p31_13_13.zip",
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_mainland_logistics_hub_candidates_proxy",
            "source_id": "mlit_logistics_hubs_tokyo_p31",
            "country": "Japan",
            "city": "Tokyo",
            "year": 2014,
            "variable_name": "Tokyo mainland logistics hub candidate proxy points",
            "value": summary["mainland_tokyo_proxy_count"],
            "unit": "points",
            "spatial_level": "Tokyo mainland proxy bounding box",
            "temporal_level": "P31-13 source",
            "analysis_axis": "Depot candidate proxy",
            "use_case_relevance": "Approximate mainland-Tokyo candidate set for EV last-mile routing scenarios.",
            "processing_rule": "Count points with 35.45 <= latitude <= 35.95 and 138.9 <= longitude <= 140.2.",
            "limitation": "This is a simple mainland proxy filter; final simulations should clip by official Tokyo boundary if spatial precision matters.",
            "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P31.html",
            "local_raw_path": "03_data/raw/logistics/mlit_logistics_hubs/323_20260705_v02_p31_13_13.zip",
            "status": "extracted",
        },
    ]
    upsert_rows(SOCIO, "variable_id", socio_rows)

    status = pd.read_csv(FW_STATUS)
    row = {
        "item": "MLIT logistics hub data",
        "purpose": "Provide depot-candidate and logistics-facility proxy points",
        "status": "collected",
        "use_in_future_wheels": "Updated Future Wheels simulation input",
        "notes": "MLIT P31 Tokyo logistics hub data has been processed as depot-candidate proxy points; these are not observed operator depots.",
    }
    status = status[~status["item"].eq(row["item"])]
    pd.concat([status, pd.DataFrame([row])], ignore_index=True).to_csv(FW_STATUS, index=False)


def main() -> None:
    summary = process_hubs()
    update_research_tables(summary)
    print(pd.Series(summary).to_string())


if __name__ == "__main__":
    main()
