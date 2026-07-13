from __future__ import annotations

import shutil
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "03_data/raw/logistics/mlit_primary_highway_freight_network"
RAW_ZIP = RAW_DIR / "324_20260705_v02_n12_21_13_gml.zip"
PROCESSED = ROOT / "data/processed"
OUT_SEGMENTS = PROCESSED / "464_20260705_tokyo_primary_highway_freight_network_segments.csv"
OUT_BY_ROAD_CLASS = PROCESSED / "463_20260705_tokyo_primary_highway_freight_network_by_road_class.csv"
OUT_SUMMARY = PROCESSED / "465_20260705_tokyo_primary_highway_freight_network_summary.csv"
INVENTORY = ROOT / "outputs/use_case_scenario/939_20260711_v03_source_data_inventory.csv"
SOCIAL_SOURCES = ROOT / "outputs/use_case_scenario/938_20260705_v03_social_side_variable_sources.csv"


FREIGHT_CLASS = {
    "1": "Primary highway freight network road",
    "2": "Alternative or complementary route",
}

ROAD_CLASS = {
    "1": "National expressway",
    "2": "Urban expressway",
    "3": "General national highway",
    "4": "Major local road (prefectural road)",
    "5": "Major local road (designated-city road)",
    "6": "General prefectural road",
    "7": "Municipal or special-ward road",
    "8": "Other road",
    "9": "Unknown",
}


def append_or_replace_csv(path: Path, rows: list[dict], key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows)
    if path.exists() and path.stat().st_size:
        old = pd.read_csv(path)
        if key in old.columns:
            old = old[~old[key].isin(new[key])]
        out = pd.concat([old, new], ignore_index=True, sort=False)
    else:
        out = new
    out.to_csv(path, index=False)


def process() -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    source_zip = ROOT / "324_20260705_v02_n12_21_13_gml.zip"
    if not RAW_ZIP.exists() and source_zip.exists():
        shutil.copy2(source_zip, RAW_ZIP)
    if not RAW_ZIP.exists():
        raise FileNotFoundError(
            f"Missing raw file: {RAW_ZIP}. Place 324_20260705_v02_n12_21_13_gml.zip in {RAW_DIR}."
        )

    gdf = gpd.read_file(f"zip://{RAW_ZIP}!N12-21_13.geojson")
    gdf = gdf.rename(
        columns={
            "N12_001": "prefecture_code",
            "N12_002": "freight_network_class_code",
            "N12_003": "road_class_code",
            "N12_004": "route_name_ja",
            "N12_005": "route_id",
            "N12_006": "branch_id",
        }
    )
    for col in ["prefecture_code", "freight_network_class_code", "road_class_code"]:
        gdf[col] = gdf[col].astype(str)

    projected = gdf.to_crs(epsg=6677)
    gdf["length_km"] = projected.geometry.length / 1000
    gdf["freight_network_class"] = gdf["freight_network_class_code"].map(FREIGHT_CLASS)
    gdf["road_class"] = gdf["road_class_code"].map(ROAD_CLASS)
    gdf["use_in_analysis"] = (
        "Tokyo logistics-corridor proxy for EV last-mile routing context; "
        "use as infrastructure-context evidence, not as observed delivery routes."
    )
    gdf["limitation"] = (
        "National Land Numerical Information N12 identifies designated freight-road corridors. "
        "It does not provide parcel demand, depot schedules, travel time, or EV charging behavior."
    )

    segment_cols = [
        "prefecture_code",
        "freight_network_class_code",
        "freight_network_class",
        "road_class_code",
        "road_class",
        "route_name_ja",
        "route_id",
        "branch_id",
        "length_km",
        "use_in_analysis",
        "limitation",
    ]
    segments = gdf[segment_cols].copy()
    segments["length_km"] = segments["length_km"].round(6)
    segments.to_csv(OUT_SEGMENTS, index=False)

    by_class = (
        segments.groupby(
            [
                "freight_network_class_code",
                "freight_network_class",
                "road_class_code",
                "road_class",
            ],
            dropna=False,
        )
        .agg(
            segment_count=("route_id", "size"),
            unique_route_count=("route_id", "nunique"),
            total_length_km=("length_km", "sum"),
        )
        .reset_index()
    )
    by_class["total_length_km"] = by_class["total_length_km"].round(3)
    by_class.to_csv(OUT_BY_ROAD_CLASS, index=False)

    total_length = float(segments["length_km"].sum())
    primary_length = float(
        segments.loc[segments["freight_network_class_code"].eq("1"), "length_km"].sum()
    )
    alternative_length = float(
        segments.loc[segments["freight_network_class_code"].eq("2"), "length_km"].sum()
    )
    summary_rows = [
        {
            "source_id": "mlit_primary_highway_freight_network_tokyo_2021",
            "source_name": "National Land Numerical Information N12 Primary Highway Freight Network Roads, Tokyo",
            "local_raw_path": str(RAW_ZIP.relative_to(ROOT)),
            "processed_segments_csv": str(OUT_SEGMENTS.relative_to(ROOT)),
            "processed_by_road_class_csv": str(OUT_BY_ROAD_CLASS.relative_to(ROOT)),
            "segment_count": int(len(segments)),
            "unique_route_count": int(segments["route_id"].nunique()),
            "total_length_km": round(total_length, 3),
            "primary_freight_network_length_km": round(primary_length, 3),
            "alternative_or_complementary_route_length_km": round(alternative_length, 3),
            "road_class_count": int(segments["road_class_code"].nunique()),
            "use_in_analysis": "Infrastructure-context proxy for freight corridors in Tokyo EV routing scenario design.",
            "limitation": "Designated freight-road geometry, not observed commercial EV delivery routes or travel-time data.",
        }
    ]
    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)

    append_or_replace_csv(
        INVENTORY,
        [
            {
                "source_id": "mlit_primary_highway_freight_network_tokyo_2021",
                "source_name": "National Land Numerical Information N12 Primary Highway Freight Network Roads, Tokyo",
                "provider": "Ministry of Land, Infrastructure, Transport and Tourism, Japan",
                "year_or_version": "2021",
                "url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N12-v1_1.html",
                "local_raw_path": str(RAW_ZIP.relative_to(ROOT)),
                "data_type": "geospatial line data",
                "geographic_scope": "Tokyo",
                "spatial_level": "designated freight-road segments",
                "use_in_analysis": "Freight-corridor infrastructure proxy for Tokyo EV routing requirement map and Future Wheels inputs.",
                "limitation": "Does not measure delivery demand, depot operation, charger use, or real-time traffic.",
            }
        ],
        key="source_id",
    )

    append_or_replace_csv(
        SOCIAL_SOURCES,
        [
            {
                "variable_id": "tokyo_primary_highway_freight_network_total_length_km",
                "source_id": "mlit_primary_highway_freight_network_tokyo_2021",
                "stage_layer": "social_infrastructure_context",
                "variable_name": "Tokyo designated freight-road network length",
                "value": round(total_length, 3),
                "unit": "km",
                "geographic_scope": "Tokyo",
                "spatial_level": "designated freight-road segments",
                "temporal_level": "2021 release",
                "processing_rule": "Read N12-21_13 GeoJSON, mapped MLIT codes to English labels, projected to EPSG:6677, and summed segment geometry lengths.",
                "use_in_analysis": "Proxy for freight-corridor infrastructure available in the Tokyo EV routing setting.",
                "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N12-v1_1.html",
                "local_raw_path": str(RAW_ZIP.relative_to(ROOT)),
                "limitation": "Corridor length is an infrastructure proxy and is not an EV route demand or travel-time measure.",
            },
            {
                "variable_id": "tokyo_primary_highway_freight_network_segment_count",
                "source_id": "mlit_primary_highway_freight_network_tokyo_2021",
                "stage_layer": "social_infrastructure_context",
                "variable_name": "Tokyo designated freight-road segment count",
                "value": int(len(segments)),
                "unit": "segments",
                "geographic_scope": "Tokyo",
                "spatial_level": "designated freight-road segments",
                "temporal_level": "2021 release",
                "processing_rule": "Counted N12-21_13 line features after reading the GeoJSON inside the MLIT zip file.",
                "use_in_analysis": "Proxy for freight-road network granularity in the Tokyo EV routing setting.",
                "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N12-v1_1.html",
                "local_raw_path": str(RAW_ZIP.relative_to(ROOT)),
                "limitation": "Segment count depends on source geometry splitting and should not be interpreted as route count.",
            },
        ],
        key="variable_id",
    )

    return summary_rows[0]


if __name__ == "__main__":
    print(pd.Series(process()).to_string())
