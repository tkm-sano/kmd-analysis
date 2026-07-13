from __future__ import annotations

import csv
import json
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from datetime import date
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "charging_infrastructure" / "open_charge_map" / "tokyo"
PROCESSED_DIR = ROOT / "data" / "processed"
VARIABLES_CSV = PROCESSED_DIR / "449_20260705_socio_technical_variables.csv"
TOKYO_BOUNDARY_ZIP = ROOT / "03_data/raw/boundary/mlit_n03_tokyo/328_20240101_v02_n03_20240101_13_gml.zip"

TODAY = date.today().isoformat()
RAW_JSON = RAW_DIR / f"open_charge_map_tokyo_{TODAY}.json"
RAW_DETAILED_JSON = RAW_DIR / f"open_charge_map_tokyo_detailed_{TODAY}.json"
STATIONS_CSV = PROCESSED_DIR / "431_20260704_open_charge_map_tokyo_stations.csv"
SUMMARY_CSV = PROCESSED_DIR / "432_20260704_open_charge_map_tokyo_summary.csv"
DETAILED_STATIONS_CSV = PROCESSED_DIR / "429_20260705_open_charge_map_tokyo_boundary_clipped_stations.csv"
DETAILED_CONNECTIONS_CSV = PROCESSED_DIR / "428_20260705_open_charge_map_tokyo_boundary_clipped_connections.csv"
DETAILED_SUMMARY_CSV = PROCESSED_DIR / "430_20260705_open_charge_map_tokyo_boundary_clipped_summary.csv"

API_URL = "https://api.openchargemap.io/v3/poi"

# Tokyo Metropolitan Government approximate bounding box.
TOKYO_BBOX = {
    "min_lat": 35.50,
    "max_lat": 35.90,
    "min_lon": 139.45,
    "max_lon": 139.95,
}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def fetch_open_charge_map() -> list[dict[str, Any]]:
    params = {
        "output": "json",
        "countrycode": "JP",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "distance": 50,
        "distanceunit": "KM",
        "maxresults": 5000,
        "compact": "true",
        "verbose": "false",
    }
    api_key = os.environ.get("OPENCHARGEMAP_API_KEY")
    if api_key:
        params["key"] = api_key

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "research-openchargemap-fetch/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 403 and not api_key:
            raise RuntimeError(
                "Open Charge Map returned HTTP 403. Set an API key first, for example: "
                "export OPENCHARGEMAP_API_KEY='your_api_key'"
            ) from exc
        raise
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Open Charge Map response: {type(data)}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RAW_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def fetch_open_charge_map_detailed() -> list[dict[str, Any]]:
    params = {
        "output": "json",
        "countrycode": "JP",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "distance": 80,
        "distanceunit": "KM",
        "maxresults": 5000,
        "compact": "false",
        "verbose": "true",
    }
    api_key = os.environ.get("OPENCHARGEMAP_API_KEY")
    if api_key:
        params["key"] = api_key

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "tokyo-ev-routing-research/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 403 and not api_key:
            raise RuntimeError(
                "Open Charge Map returned HTTP 403. Set an API key first, for example: "
                "export OPENCHARGEMAP_API_KEY='your_api_key'"
            ) from exc
        raise
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Open Charge Map response: {type(data)}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DETAILED_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def load_tokyo_boundary() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(f"zip://{TOKYO_BOUNDARY_ZIP}!N03-20240101_13.geojson")
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=4326)[["geometry"]].dissolve()


def boundary_clip_items(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for item in data:
        address = item.get("AddressInfo") or {}
        lat = address.get("Latitude")
        lon = address.get("Longitude")
        if lat is None or lon is None:
            continue
        candidates.append({"ocm_id": item.get("ID"), "latitude": lat, "longitude": lon, "item": item})
    if not candidates:
        return []
    boundary = load_tokyo_boundary()
    points = gpd.GeoDataFrame(
        candidates,
        geometry=gpd.points_from_xy(
            [float(row["longitude"]) for row in candidates],
            [float(row["latitude"]) for row in candidates],
        ),
        crs="EPSG:4326",
    )
    clipped = gpd.sjoin(points, boundary, predicate="within", how="inner")
    clipped_ids = set(clipped["ocm_id"].tolist())
    return [row["item"] for row in candidates if row["ocm_id"] in clipped_ids]


def title(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("Title", "") or "")
    return ""


def connection_type(conn: dict[str, Any], key: str) -> str:
    obj = conn.get(key) or {}
    if isinstance(obj, dict):
        return str(obj.get("Title", "") or obj.get("FormalName", "") or "")
    return ""


def detailed_station_and_connection_rows(
    data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    station_rows_out: list[dict[str, Any]] = []
    connection_rows_out: list[dict[str, Any]] = []
    for item in boundary_clip_items(data):
        address = item.get("AddressInfo") or {}
        connections = item.get("Connections") or []
        operator = item.get("OperatorInfo") or {}
        usage = item.get("UsageType") or {}
        status = item.get("StatusType") or {}
        data_provider = item.get("DataProvider") or {}
        power_values = [
            float(conn["PowerKW"])
            for conn in connections
            if conn.get("PowerKW") not in (None, "")
        ]
        connection_types = sorted(
            {
                connection_type(conn, "ConnectionType")
                for conn in connections
                if connection_type(conn, "ConnectionType")
            }
        )
        station_rows_out.append(
            {
                "ocm_id": item.get("ID", ""),
                "uuid": item.get("UUID", ""),
                "title": address.get("Title", ""),
                "address_line_1": address.get("AddressLine1", ""),
                "town": address.get("Town", ""),
                "state_or_province": address.get("StateOrProvince", ""),
                "postcode": address.get("Postcode", ""),
                "latitude": address.get("Latitude", ""),
                "longitude": address.get("Longitude", ""),
                "operator": operator.get("Title", ""),
                "usage_type": usage.get("Title", ""),
                "status_type": status.get("Title", ""),
                "data_provider": data_provider.get("Title", ""),
                "connection_count": len(connections),
                "connection_types": "; ".join(connection_types),
                "max_power_kw": max(power_values) if power_values else "",
                "has_power_kw": "yes" if power_values else "no",
                "is_fast_charger_proxy": "yes" if power_values and max(power_values) >= 50 else "no",
                "date_last_verified": item.get("DateLastVerified", ""),
                "date_last_status_update": item.get("DateLastStatusUpdate", ""),
                "date_created": item.get("DateCreated", ""),
                "source": "Open Charge Map",
                "downloaded_at": TODAY,
                "boundary_filter": "N03 Tokyo boundary polygon",
            }
        )
        for conn in connections:
            power_kw = conn.get("PowerKW", "")
            connection_rows_out.append(
                {
                    "ocm_id": item.get("ID", ""),
                    "connection_id": conn.get("ID", ""),
                    "station_title": address.get("Title", ""),
                    "latitude": address.get("Latitude", ""),
                    "longitude": address.get("Longitude", ""),
                    "connection_type": connection_type(conn, "ConnectionType"),
                    "level": connection_type(conn, "Level"),
                    "current_type": connection_type(conn, "CurrentType"),
                    "quantity": conn.get("Quantity", ""),
                    "power_kw": power_kw,
                    "voltage": conn.get("Voltage", ""),
                    "amps": conn.get("Amps", ""),
                    "is_fast_charger_proxy": "yes"
                    if power_kw not in (None, "") and float(power_kw) >= 50
                    else "no",
                    "operator": operator.get("Title", ""),
                    "usage_type": usage.get("Title", ""),
                    "status_type": status.get("Title", ""),
                    "source": "Open Charge Map",
                    "downloaded_at": TODAY,
                }
            )
    station_rows_out.sort(key=lambda r: (str(r["town"]), str(r["title"]), str(r["ocm_id"])))
    connection_rows_out.sort(
        key=lambda r: (str(r["station_title"]), str(r["connection_id"]), str(r["ocm_id"]))
    )
    return station_rows_out, connection_rows_out


def in_tokyo_bbox(row: dict[str, Any]) -> bool:
    address = row.get("AddressInfo") or {}
    lat = address.get("Latitude")
    lon = address.get("Longitude")
    if lat is None or lon is None:
        return False
    return (
        TOKYO_BBOX["min_lat"] <= float(lat) <= TOKYO_BBOX["max_lat"]
        and TOKYO_BBOX["min_lon"] <= float(lon) <= TOKYO_BBOX["max_lon"]
    )


def station_rows(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in data:
        if not in_tokyo_bbox(item):
            continue
        address = item.get("AddressInfo") or {}
        connections = item.get("Connections") or []
        power_values = [
            float(conn["PowerKW"])
            for conn in connections
            if conn.get("PowerKW") not in (None, "")
        ]
        max_power_kw = max(power_values) if power_values else ""
        connection_types = sorted(
            {
                str((conn.get("ConnectionType") or {}).get("Title", "")).strip()
                for conn in connections
                if (conn.get("ConnectionType") or {}).get("Title")
            }
        )
        status = item.get("StatusType") or {}
        usage = item.get("UsageType") or {}
        operator = item.get("OperatorInfo") or {}
        rows.append(
            {
                "ocm_id": item.get("ID", ""),
                "title": address.get("Title", ""),
                "latitude": address.get("Latitude", ""),
                "longitude": address.get("Longitude", ""),
                "town": address.get("Town", ""),
                "postcode": address.get("Postcode", ""),
                "operator": operator.get("Title", ""),
                "usage_type": usage.get("Title", ""),
                "status_type": status.get("Title", ""),
                "connection_count": len(connections),
                "connection_types": "; ".join(connection_types),
                "max_power_kw": max_power_kw,
                "is_fast_charger_proxy": "yes" if power_values and max(power_values) >= 50 else "no",
                "source": "Open Charge Map",
                "downloaded_at": TODAY,
            }
        )
    rows.sort(key=lambda r: (str(r["town"]), str(r["title"]), str(r["ocm_id"])))
    return rows


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    station_count = len(rows)
    with_power = [r for r in rows if r["max_power_kw"] != ""]
    fast = [r for r in rows if r["is_fast_charger_proxy"] == "yes"]
    return [
        {
            "variable_id": "charging_stations_tokyo_geocoded_snapshot",
            "value": station_count,
            "unit": "stations",
            "definition": "Open Charge Map stations within approximate Tokyo bounding box.",
            "source_file": str(RAW_JSON.relative_to(ROOT)),
            "processed_file": str(STATIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "Bounding-box filter is approximate; OCM coverage/status may be incomplete.",
        },
        {
            "variable_id": "fast_charger_share_tokyo_snapshot",
            "value": round(len(fast) / len(with_power), 4) if with_power else "",
            "unit": "share of stations with known power",
            "definition": "Share of Tokyo OCM stations with max reported connection power >= 50 kW among stations with known power.",
            "source_file": str(RAW_JSON.relative_to(ROOT)),
            "processed_file": str(STATIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "PowerKW is missing for some stations; threshold is a proxy, not an official charger class.",
        },
    ]


def detailed_summary_rows(
    station_rows_in: list[dict[str, Any]],
    connection_rows_in: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stations = pd.DataFrame(station_rows_in)
    connections = pd.DataFrame(connection_rows_in)
    known_power = connections[
        connections["power_kw"].astype(str).str.len().gt(0)
    ] if not connections.empty else connections
    fast_connections = known_power[
        pd.to_numeric(known_power["power_kw"], errors="coerce").ge(50)
    ] if not known_power.empty else known_power
    fast_stations = stations[stations["is_fast_charger_proxy"].eq("yes")] if not stations.empty else stations
    return [
        {
            "variable_id": "charging_stations_tokyo_n03_boundary_clipped",
            "value": len(station_rows_in),
            "unit": "stations",
            "definition": "Open Charge Map stations clipped by official MLIT N03 Tokyo boundary polygon.",
            "source_file": str(RAW_DETAILED_JSON.relative_to(ROOT)),
            "processed_file": str(DETAILED_STATIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "OCM coverage/status may be incomplete; public availability and connector compatibility require case-specific screening.",
        },
        {
            "variable_id": "charging_connections_tokyo_n03_boundary_clipped",
            "value": len(connection_rows_in),
            "unit": "connections",
            "definition": "Open Charge Map connector records for stations clipped by official MLIT N03 Tokyo boundary polygon.",
            "source_file": str(RAW_DETAILED_JSON.relative_to(ROOT)),
            "processed_file": str(DETAILED_CONNECTIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "Each OCM connection is a reported connector record; quantity and actual availability may be incomplete.",
        },
        {
            "variable_id": "fast_charging_connections_tokyo_n03_boundary_clipped",
            "value": len(fast_connections),
            "unit": "connections",
            "definition": "Connector records with reported PowerKW >= 50 after N03 Tokyo boundary clipping.",
            "source_file": str(RAW_DETAILED_JSON.relative_to(ROOT)),
            "processed_file": str(DETAILED_CONNECTIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "50 kW threshold is a research proxy and depends on reported PowerKW availability.",
        },
        {
            "variable_id": "fast_charger_station_share_tokyo_n03_boundary_clipped",
            "value": round(len(fast_stations) / len(stations), 4) if len(stations) else "",
            "unit": "share of stations",
            "definition": "Share of N03-clipped Tokyo stations with at least one reported connector PowerKW >= 50.",
            "source_file": str(RAW_DETAILED_JSON.relative_to(ROOT)),
            "processed_file": str(DETAILED_STATIONS_CSV.relative_to(ROOT)),
            "downloaded_at": TODAY,
            "limitation": "PowerKW is missing for some stations; threshold is a proxy, not an official charger class.",
        },
    ]


def update_variables(summary: list[dict[str, Any]]) -> None:
    if not VARIABLES_CSV.exists():
        return
    with VARIABLES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    by_id = {row["variable_id"]: row for row in rows}
    for item in summary:
        variable_id = str(item["variable_id"])
        if variable_id not in by_id:
            rows.append(
                {
                    key: ""
                    for key in fieldnames
                }
            )
            rows[-1]["variable_id"] = variable_id
            by_id[variable_id] = rows[-1]
        row = by_id[variable_id]
        row.update(
            {
                "source_id": "open_charge_map",
                "country": "Japan",
                "city": "Tokyo",
                "year": TODAY,
                "value": item["value"],
                "unit": item["unit"],
                "spatial_level": "city",
                "temporal_level": "snapshot",
                "source_url": "https://www.openchargemap.org/develop/api",
                "local_raw_path": item["source_file"],
                "status": "extracted",
            }
        )
        if variable_id == "charging_stations_tokyo_geocoded_snapshot":
            row.update(
                {
                    "variable_name": "Geocoded charging station count",
                    "analysis_axis": "Charging geospatial readiness",
                    "use_case_relevance": "EVRP station-choice and charging-feasibility context",
                    "processing_rule": item["definition"],
                    "limitation": item["limitation"],
                }
            )
        elif variable_id == "fast_charger_share_tokyo_snapshot":
            row.update(
                {
                    "variable_name": "Fast charger share proxy",
                    "analysis_axis": "Charging geospatial readiness",
                    "use_case_relevance": "Charging-time constraint context for EVRP",
                    "processing_rule": item["definition"],
                    "limitation": item["limitation"],
                }
            )
        elif variable_id in {
            "charging_stations_tokyo_n03_boundary_clipped",
            "charging_connections_tokyo_n03_boundary_clipped",
            "fast_charging_connections_tokyo_n03_boundary_clipped",
            "fast_charger_station_share_tokyo_n03_boundary_clipped",
        }:
            row.update(
                {
                    "variable_name": item["definition"],
                    "analysis_axis": "Charging geospatial readiness",
                    "use_case_relevance": "EVRP station-choice, SOC feasibility, and charging-time constraint context",
                    "processing_rule": item["definition"],
                    "limitation": item["limitation"],
                }
            )
    write_csv(VARIABLES_CSV, rows, fieldnames)


def main() -> None:
    data = fetch_open_charge_map()
    rows = station_rows(data)
    write_csv(
        STATIONS_CSV,
        rows,
        [
            "ocm_id",
            "title",
            "latitude",
            "longitude",
            "town",
            "postcode",
            "operator",
            "usage_type",
            "status_type",
            "connection_count",
            "connection_types",
            "max_power_kw",
            "is_fast_charger_proxy",
            "source",
            "downloaded_at",
        ],
    )
    summary = summary_rows(rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        [
            "variable_id",
            "value",
            "unit",
            "definition",
            "source_file",
            "processed_file",
            "downloaded_at",
            "limitation",
        ],
    )
    update_variables(summary)
    print(RAW_JSON)
    print(STATIONS_CSV)
    print(SUMMARY_CSV)
    print(f"stations={len(rows)}")


def main_detailed() -> None:
    data = fetch_open_charge_map_detailed()
    station_rows_out, connection_rows_out = detailed_station_and_connection_rows(data)
    write_csv(
        DETAILED_STATIONS_CSV,
        station_rows_out,
        [
            "ocm_id",
            "uuid",
            "title",
            "address_line_1",
            "town",
            "state_or_province",
            "postcode",
            "latitude",
            "longitude",
            "operator",
            "usage_type",
            "status_type",
            "data_provider",
            "connection_count",
            "connection_types",
            "max_power_kw",
            "has_power_kw",
            "is_fast_charger_proxy",
            "date_last_verified",
            "date_last_status_update",
            "date_created",
            "source",
            "downloaded_at",
            "boundary_filter",
        ],
    )
    write_csv(
        DETAILED_CONNECTIONS_CSV,
        connection_rows_out,
        [
            "ocm_id",
            "connection_id",
            "station_title",
            "latitude",
            "longitude",
            "connection_type",
            "level",
            "current_type",
            "quantity",
            "power_kw",
            "voltage",
            "amps",
            "is_fast_charger_proxy",
            "operator",
            "usage_type",
            "status_type",
            "source",
            "downloaded_at",
        ],
    )
    summary = detailed_summary_rows(station_rows_out, connection_rows_out)
    write_csv(
        DETAILED_SUMMARY_CSV,
        summary,
        [
            "variable_id",
            "value",
            "unit",
            "definition",
            "source_file",
            "processed_file",
            "downloaded_at",
            "limitation",
        ],
    )
    update_variables(summary)
    print(RAW_DETAILED_JSON)
    print(DETAILED_STATIONS_CSV)
    print(DETAILED_CONNECTIONS_CSV)
    print(DETAILED_SUMMARY_CSV)
    print(f"stations={len(station_rows_out)}")
    print(f"connections={len(connection_rows_out)}")


if __name__ == "__main__":
    if os.environ.get("OCM_DETAILED", "").lower() in {"1", "true", "yes"}:
        main_detailed()
    else:
        main()
