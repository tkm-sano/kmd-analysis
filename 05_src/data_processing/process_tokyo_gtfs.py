from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ZIP = ROOT / "ToeiBus-GTFS.zip"
RAW_DIR = ROOT / "data" / "raw" / "smart_city" / "gtfs" / "tokyo"
RAW_ZIP = RAW_DIR / "toei_bus_gtfs_2026-07-04.zip"
SUMMARY_CSV = ROOT / "data" / "processed" / "455_20260704_tokyo_gtfs_summary.csv"
VARIABLES_CSV = ROOT / "data" / "processed" / "449_20260705_socio_technical_variables.csv"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def read_gtfs_table(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as f:
        return list(csv.DictReader((line.decode("utf-8-sig") for line in f)))


def summarize_gtfs() -> list[dict[str, Any]]:
    if SOURCE_ZIP.exists() and not RAW_ZIP.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        RAW_ZIP.write_bytes(SOURCE_ZIP.read_bytes())
        SOURCE_ZIP.unlink()

    with zipfile.ZipFile(RAW_ZIP) as zf:
        names = set(zf.namelist())
        agency = read_gtfs_table(zf, "agency.txt") if "agency.txt" in names else []
        routes = read_gtfs_table(zf, "routes.txt") if "routes.txt" in names else []
        stops = read_gtfs_table(zf, "stops.txt") if "stops.txt" in names else []
        trips = read_gtfs_table(zf, "trips.txt") if "trips.txt" in names else []
        stop_times = read_gtfs_table(zf, "stop_times.txt") if "stop_times.txt" in names else []
        calendar = read_gtfs_table(zf, "calendar.txt") if "calendar.txt" in names else []
        feed_info = read_gtfs_table(zf, "feed_info.txt") if "feed_info.txt" in names else []

    feed_start = min((row.get("start_date", "") for row in calendar if row.get("start_date")), default="")
    feed_end = max((row.get("end_date", "") for row in calendar if row.get("end_date")), default="")
    agency_name = agency[0].get("agency_name", "") if agency else ""
    feed_publisher = feed_info[0].get("feed_publisher_name", "") if feed_info else ""

    return [
        {
            "variable_id": "gtfs_available_tokyo",
            "value": 1,
            "unit": "binary",
            "definition": "A static GTFS feed is available for Toei Bus in the Tokyo subcase.",
            "source_file": str(RAW_ZIP.relative_to(ROOT)),
            "limitation": "Bus GTFS indicates static mobility-data readiness; it is not road traffic telemetry and is not a direct EV delivery-route demand dataset.",
        },
        {
            "variable_id": "gtfs_routes_tokyo",
            "value": len(routes),
            "unit": "routes",
            "definition": f"Number of routes in the Toei Bus GTFS feed. Agency: {agency_name or feed_publisher}.",
            "source_file": str(RAW_ZIP.relative_to(ROOT)),
            "limitation": "Public transit route count is a mobility-data availability indicator, not a logistics route count.",
        },
        {
            "variable_id": "gtfs_stops_tokyo",
            "value": len(stops),
            "unit": "stops",
            "definition": "Number of stops in the Toei Bus GTFS feed.",
            "source_file": str(RAW_ZIP.relative_to(ROOT)),
            "limitation": "Stops are public transit stops, not delivery customers.",
        },
        {
            "variable_id": "gtfs_trips_tokyo",
            "value": len(trips),
            "unit": "trips",
            "definition": f"Number of scheduled trips in the Toei Bus GTFS feed. Calendar range: {feed_start}-{feed_end}.",
            "source_file": str(RAW_ZIP.relative_to(ROOT)),
            "limitation": "Scheduled transit trips indicate data richness, not EV delivery operations.",
        },
        {
            "variable_id": "gtfs_stop_times_tokyo",
            "value": len(stop_times),
            "unit": "stop_time records",
            "definition": "Number of stop_time records in the Toei Bus GTFS feed.",
            "source_file": str(RAW_ZIP.relative_to(ROOT)),
            "limitation": "Large stop_time count indicates detailed static schedule data, not real-time traffic.",
        },
    ]


def update_variables(summary: list[dict[str, Any]]) -> None:
    with VARIABLES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    by_id = {row["variable_id"]: row for row in rows}
    for item in summary:
        variable_id = str(item["variable_id"])
        if variable_id not in by_id:
            row = {key: "" for key in fieldnames}
            row["variable_id"] = variable_id
            rows.append(row)
            by_id[variable_id] = row
        row = by_id[variable_id]
        row.update(
            {
                "source_id": "gtfs_city",
                "country": "Japan",
                "city": "Tokyo",
                "year": "2026",
                "variable_name": variable_id.replace("_", " "),
                "value": item["value"],
                "unit": item["unit"],
                "spatial_level": "city",
                "temporal_level": "static feed",
                "analysis_axis": "Smart city data readiness",
                "use_case_relevance": "Static mobility-data availability for the Tokyo subcase.",
                "processing_rule": item["definition"],
                "limitation": item["limitation"],
                "source_url": "https://ckan.odpt.org/dataset",
                "local_raw_path": item["source_file"],
                "status": "extracted",
            }
        )
    write_csv(VARIABLES_CSV, rows, fieldnames)


def main() -> None:
    summary = summarize_gtfs()
    write_csv(
        SUMMARY_CSV,
        summary,
        ["variable_id", "value", "unit", "definition", "source_file", "limitation"],
    )
    update_variables(summary)
    print(RAW_ZIP)
    print(SUMMARY_CSV)
    for row in summary:
        print(f"{row['variable_id']}={row['value']} {row['unit']}")


if __name__ == "__main__":
    main()
