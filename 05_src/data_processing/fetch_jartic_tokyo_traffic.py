from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "smart_city" / "traffic" / "jartic" / "tokyo"
PROCESSED_DIR = ROOT / "data" / "processed"
SOCIO_CSV = PROCESSED_DIR / "449_20260705_socio_technical_variables.csv"
SUMMARY_CSV = PROCESSED_DIR / "425_20260705_jartic_tokyo_traffic_summary.csv"
OBS_CSV = PROCESSED_DIR / "424_20260705_jartic_tokyo_traffic_observations.csv"
INVENTORY_CSV = ROOT / "literature" / "use_case_scenario" / "213_20260705_open_data_source_inventory.csv"

BASE_URL = "https://api.jartic-open-traffic.org/geoserver"
SOURCE_URL = "https://www.jartic-open-traffic.org/"
TOKYO_BBOX = (139.1, 35.45, 140.0, 35.95)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def upsert_rows(path: Path, key_field: str, new_rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    existing = read_csv(path) if path.exists() else []
    by_key = {row[key_field]: row for row in existing if row.get(key_field)}
    for row in new_rows:
        by_key[str(row[key_field])] = {key: str(row.get(key, "")) for key in fieldnames}
    write_csv(path, list(by_key.values()), fieldnames)


def time_code(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H00")


def candidate_time_codes() -> list[str]:
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).replace(minute=0, second=0, microsecond=0)
    codes: list[str] = []
    for hours_back in range(2, 96):
        codes.append(time_code(now - timedelta(hours=hours_back)))
    # Stable fallback verified during development; keeps the script useful if local clock differs.
    codes.extend(["202607040900", "202606300900"])
    return list(dict.fromkeys(codes))


def fetch_for_time(code: str) -> dict[str, Any]:
    bbox = ",".join(str(x) for x in TOKYO_BBOX)
    cql_filter = f"道路種別=3 AND 時間コード={code} AND BBOX(ジオメトリ,{bbox},'EPSG:4326')"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "t_travospublic_measure_1h",
        "srsName": "EPSG:4326",
        "outputFormat": "application/json",
        "exceptions": "application/json",
        "cql_filter": cql_filter,
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    data["_request_url"] = BASE_URL + "?" + urlencode(params)
    data["_time_code"] = code
    data["_tokyo_bbox"] = TOKYO_BBOX
    return data


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def summarize_feature(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates") or [[]]
    lon, lat = coords[0] if coords and coords[0] else ("", "")
    up_small = int_value(props.get("上り・小型交通量"))
    up_large = int_value(props.get("上り・大型交通量"))
    up_unknown = int_value(props.get("上り・車種判別不能交通量"))
    down_small = int_value(props.get("下り・小型交通量"))
    down_large = int_value(props.get("下り・大型交通量"))
    down_unknown = int_value(props.get("下り・車種判別不能交通量"))
    total = up_small + up_large + up_unknown + down_small + down_large + down_unknown
    heavy = up_large + down_large
    return {
        "observation_code": props.get("常時観測点コード", ""),
        "time_code": props.get("時間コード", ""),
        "observation_date": props.get("観測年月日", ""),
        "hour_band": props.get("時間帯", ""),
        "lon": lon,
        "lat": lat,
        "up_small": up_small,
        "up_large": up_large,
        "up_unknown": up_unknown,
        "down_small": down_small,
        "down_large": down_large,
        "down_unknown": down_unknown,
        "total_traffic": total,
        "heavy_traffic": heavy,
        "missing_flag_up": props.get("上り・欠測", ""),
        "missing_flag_down": props.get("下り・欠測", ""),
        "road_type": props.get("道路種別", ""),
    }


def build_socio_rows(summary: dict[str, Any], raw_path: Path) -> list[dict[str, Any]]:
    year = str(summary["time_code"])[:4]
    common = {
        "source_id": "jartic_traffic_api",
        "country": "Japan",
        "city": "Tokyo",
        "year": year,
        "spatial_level": "Tokyo bounding box / national-road observation points",
        "temporal_level": "hourly snapshot",
        "analysis_axis": "Traffic intensity proxy",
        "use_case_relevance": "Optional dynamic-dispatch and travel-cost-uncertainty context for the Tokyo subcase.",
        "source_url": SOURCE_URL,
        "local_raw_path": str(raw_path.relative_to(ROOT)),
        "status": "extracted",
    }
    limitation = (
        "JARTIC traffic-volume API covers national-road observation points in the Tokyo bounding box; "
        "it is a traffic-intensity proxy and does not provide delivery routes, customer demand, depot locations, or EV charging behavior."
    )
    return [
        {
            **common,
            "variable_id": "jartic_tokyo_traffic_observation_points_snapshot",
            "variable_name": "JARTIC Tokyo traffic observation points",
            "value": summary["observation_points"],
            "unit": "points",
            "processing_rule": "Counted features returned by JARTIC t_travospublic_measure_1h for road type 3 inside Tokyo bounding box.",
            "limitation": limitation,
        },
        {
            **common,
            "variable_id": "jartic_tokyo_total_hourly_traffic_snapshot",
            "variable_name": "JARTIC Tokyo total hourly traffic",
            "value": summary["total_traffic"],
            "unit": "vehicles per hour across returned observation points",
            "processing_rule": "Summed up/down small, large, and unknown vehicle counts across returned observation points.",
            "limitation": limitation,
        },
        {
            **common,
            "variable_id": "jartic_tokyo_mean_hourly_traffic_per_point_snapshot",
            "variable_name": "JARTIC Tokyo mean hourly traffic per observation point",
            "value": round(summary["mean_traffic_per_point"], 3),
            "unit": "vehicles per hour per point",
            "processing_rule": "Total hourly traffic divided by returned observation-point count.",
            "limitation": limitation,
        },
        {
            **common,
            "variable_id": "jartic_tokyo_heavy_vehicle_share_snapshot",
            "variable_name": "JARTIC Tokyo heavy-vehicle share",
            "value": round(summary["heavy_vehicle_share"], 4),
            "unit": "share",
            "processing_rule": "Summed up/down large-vehicle counts divided by total traffic across returned observation points.",
            "limitation": limitation,
        },
    ]


def upsert_inventory(raw_path: Path) -> None:
    rows = read_csv(INVENTORY_CSV)
    fieldnames = list(rows[0].keys())
    new_row = {
        "source_id": "jartic_traffic_api",
        "source_name": "JARTIC traffic-volume API",
        "provider": "Japan Road Traffic Information Center / MLIT xROAD",
        "url": SOURCE_URL,
        "local_raw_path": str(raw_path.parent.relative_to(ROOT)),
        "data_type": "GeoJSON via WFS API",
        "collection_method": "API query",
        "downloaded_at": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d"),
        "license_or_terms": "JARTIC API terms",
        "spatial_level": "national-road observation points / Tokyo bounding box",
        "temporal_level": "hourly snapshot",
        "use_in_analysis": "Optional traffic-intensity proxy for dynamic dispatch or travel-cost uncertainty branches.",
        "limitation": "Covers traffic-volume observation points on national roads; not parcel delivery routes, customer demand, depot data, or EV charging behavior.",
        "collection_status": "local_existing",
    }
    upsert_rows(INVENTORY_CSV, "source_id", [new_row], fieldnames)


def main() -> None:
    selected: dict[str, Any] | None = None
    for code in candidate_time_codes():
        data = fetch_for_time(code)
        if data.get("features"):
            selected = data
            break
    if selected is None:
        raise RuntimeError("No JARTIC hourly traffic features were returned for the configured Tokyo bbox.")

    code = selected["_time_code"]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"jartic_tokyo_traffic_1h_{code}.json"
    raw_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")

    observations = [summarize_feature(feature) for feature in selected["features"]]
    obs_fields = [
        "observation_code",
        "time_code",
        "observation_date",
        "hour_band",
        "lon",
        "lat",
        "up_small",
        "up_large",
        "up_unknown",
        "down_small",
        "down_large",
        "down_unknown",
        "total_traffic",
        "heavy_traffic",
        "missing_flag_up",
        "missing_flag_down",
        "road_type",
    ]
    write_csv(OBS_CSV, observations, obs_fields)

    total = sum(row["total_traffic"] for row in observations)
    heavy = sum(row["heavy_traffic"] for row in observations)
    summary = {
        "source_id": "jartic_traffic_api",
        "time_code": code,
        "tokyo_bbox": ";".join(str(x) for x in TOKYO_BBOX),
        "observation_points": len(observations),
        "total_traffic": total,
        "mean_traffic_per_point": total / len(observations) if observations else 0,
        "heavy_traffic": heavy,
        "heavy_vehicle_share": heavy / total if total else 0,
        "raw_path": str(raw_path.relative_to(ROOT)),
        "source_url": SOURCE_URL,
        "interpretation": "Hourly traffic-volume snapshot for national-road observation points in Tokyo bounding box; use as optional traffic-intensity proxy.",
    }
    write_csv(SUMMARY_CSV, [summary], list(summary.keys()))

    socio_rows = build_socio_rows(summary, raw_path)
    socio_fields = list(read_csv(SOCIO_CSV)[0].keys())
    upsert_rows(SOCIO_CSV, "variable_id", socio_rows, socio_fields)
    upsert_inventory(raw_path)

    for path in [raw_path, OBS_CSV, SUMMARY_CSV, SOCIO_CSV, INVENTORY_CSV]:
        print(path)


if __name__ == "__main__":
    main()
