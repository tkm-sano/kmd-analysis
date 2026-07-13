from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "03_data/raw/vehicle_specs/official_sources"
PROCESSED = ROOT / "data/processed"
SOURCE_CSV = ROOT / "03_data/raw/vehicle_specs/330_20260705_v02_ev_vehicle_specs_sources.csv"
SCENARIO_CSV = PROCESSED / "416_20260705_ev_truck_specs_scenario.csv"
SUMMARY_CSV = PROCESSED / "417_20260705_ev_truck_specs_summary.csv"
INVENTORY = ROOT / "literature/use_case_scenario/213_20260705_open_data_source_inventory.csv"
SOCIO = ROOT / "03_data/processed/449_20260705_socio_technical_variables.csv"


SOURCES = [
    {
        "source_id": "mitsubishi_fuso_ecanter_launch_2023",
        "manufacturer": "Mitsubishi Fuso",
        "title": "New eCanter launch press release",
        "url": "https://www.mitsubishi-fuso.com/ja/news-main/press-release/2023/03/09/%E9%9B%BB%E6%B0%97%E5%B0%8F%E5%9E%8B%E3%83%88%E3%83%A9%E3%83%83%E3%82%AF%E3%80%8Cecanter%E3%80%8D%E6%96%B0%E5%9E%8B%E3%83%A2%E3%83%87%E3%83%AB%E3%82%92%E7%99%BA%E5%A3%B2/",
        "local_file": "335_20260705_v02_mitsubishi_fuso_ecanter_launch_2023.html",
        "file_type": "html",
    },
    {
        "source_id": "mitsubishi_fuso_ecanter_yamato_2023",
        "manufacturer": "Mitsubishi Fuso",
        "title": "eCanter Yamato deployment press release",
        "url": "https://www.mitsubishi-fuso.com/ja/news-main/press-release/2023/09/12/%E9%9B%BB%E6%B0%97%E5%B0%8F%E5%9E%8B%E3%83%88%E3%83%A9%E3%83%83%E3%82%AF%E3%80%8Cecanter%E3%80%8D%E6%96%B0%E5%9E%8B%E3%83%A2%E3%83%87%E3%83%AB%E7%B4%84900%E5%8F%B0%E3%82%92%E3%83%A4%E3%83%9E%E3%83%88/",
        "local_file": "336_20260705_v02_mitsubishi_fuso_ecanter_yamato_2023.html",
        "file_type": "html",
    },
    {
        "source_id": "isuzu_elf_ev_product",
        "manufacturer": "Isuzu",
        "title": "ELF EV product specifications",
        "url": "https://www.isuzu.co.jp/product/elf/ev/",
        "local_file": "334_20260705_v02_isuzu_elf_ev_product.html",
        "file_type": "html",
    },
    {
        "source_id": "hino_dutro_z_ev_2024",
        "manufacturer": "Hino",
        "title": "Dutro Z EV 2024 specification press release",
        "url": "https://www.hino.co.jp/corp/news/2024/20240918-003755.html",
        "local_file": "333_20260705_v02_hino_dutro_z_ev_2024.html",
        "file_type": "html",
    },
    {
        "source_id": "toyota_pixis_van_bev_spec_2026",
        "manufacturer": "Toyota",
        "title": "Pixis Van BEV specifications PDF",
        "url": "https://toyota.jp/pages/contents/pixisvan/002_b_001/pdf/pixisvan_spec_202606.pdf",
        "local_file": "337_20260705_v02_toyota_pixisvan_bev_spec_202606.pdf",
        "file_type": "pdf",
    },
]


SPEC_ROWS = [
    {
        "scenario_vehicle_id": "mitsubishi_fuso_ecanter_s_yamato",
        "manufacturer": "Mitsubishi Fuso",
        "vehicle_model": "eCanter S battery, Yamato deployment specification",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 41,
        "range_km": 116,
        "payload_kg": 2000,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed value; 60 km/h, half loaded, flat body as described by source",
        "payload_note": "Yamato deployment vehicle specification; payload varies by body and configuration.",
        "scenario_use": "baseline small EV truck",
        "source_id": "mitsubishi_fuso_ecanter_yamato_2023",
        "source_url": SOURCES[1]["url"],
        "source_quote_or_location": "vehicle dimensions/spec section: rated capacity 41 kWh, range 116 km, max payload 2,000 kg",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "mitsubishi_fuso_ecanter_m_reference",
        "manufacturer": "Mitsubishi Fuso",
        "vehicle_model": "eCanter M battery reference",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 82,
        "range_km": 236,
        "payload_kg": "",
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed value reported in launch press release",
        "payload_note": "Payload not extracted from source page for this battery size; use only for battery/range sensitivity.",
        "scenario_use": "medium battery sensitivity",
        "source_id": "mitsubishi_fuso_ecanter_launch_2023",
        "source_url": SOURCES[0]["url"],
        "source_quote_or_location": "battery module section: 2 batteries, 236 km",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "mitsubishi_fuso_ecanter_l_reference",
        "manufacturer": "Mitsubishi Fuso",
        "vehicle_model": "eCanter L battery reference",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 123,
        "range_km": 324,
        "payload_kg": "",
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed value reported in launch press release",
        "payload_note": "Payload not extracted from source page for this battery size; use only for battery/range sensitivity.",
        "scenario_use": "large battery sensitivity",
        "source_id": "mitsubishi_fuso_ecanter_launch_2023",
        "source_url": SOURCES[0]["url"],
        "source_quote_or_location": "battery module section: 3 batteries, 324 km",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "isuzu_elfmio_ev_nhr",
        "manufacturer": "Isuzu",
        "vehicle_model": "ELFmio EV standard cab NHR",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 44,
        "range_km": 115,
        "payload_kg": 1050,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed WLTC-related source value",
        "payload_note": "Payload varies by body specification.",
        "scenario_use": "ordinary-license small truck scenario",
        "source_id": "isuzu_elf_ev_product",
        "source_url": SOURCES[2]["url"],
        "source_quote_or_location": "ELFmio EV NHR section",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "isuzu_elf_ev_njr",
        "manufacturer": "Isuzu",
        "vehicle_model": "ELF EV standard cab NJR",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 44,
        "range_km": 120,
        "payload_kg": 2000,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed source value",
        "payload_note": "Payload varies by body specification.",
        "scenario_use": "baseline small EV truck",
        "source_id": "isuzu_elf_ev_product",
        "source_url": SOURCES[2]["url"],
        "source_quote_or_location": "ELF EV NJR section",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "isuzu_elf_ev_high_cab",
        "manufacturer": "Isuzu",
        "vehicle_model": "ELF EV high cab NLR/NMR",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 66,
        "range_km": "180-190",
        "payload_kg": 2000,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed source value",
        "payload_note": "Payload varies by body specification.",
        "scenario_use": "medium battery truck scenario",
        "source_id": "isuzu_elf_ev_product",
        "source_url": SOURCES[2]["url"],
        "source_quote_or_location": "ELF EV high cab section",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "isuzu_elf_ev_wide_cab",
        "manufacturer": "Isuzu",
        "vehicle_model": "ELF EV wide cab NPR",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 110,
        "range_km": 250,
        "payload_kg": "2950-3000",
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed source value",
        "payload_note": "Payload varies by body specification.",
        "scenario_use": "large battery truck scenario",
        "source_id": "isuzu_elf_ev_product",
        "source_url": SOURCES[2]["url"],
        "source_quote_or_location": "ELF EV wide cab NPR section",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "hino_dutro_z_ev_walkthrough",
        "manufacturer": "Hino",
        "vehicle_model": "Dutro Z EV walkthrough van",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 40,
        "range_km": 150,
        "payload_kg": 1000,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed WLTC-mode source value",
        "payload_note": "Walkthrough van specification.",
        "scenario_use": "urban last-mile EV truck scenario",
        "source_id": "hino_dutro_z_ev_2024",
        "source_url": SOURCES[3]["url"],
        "source_quote_or_location": "Dutro Z EV specification table",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "hino_dutro_z_ev_aluminum_van",
        "manufacturer": "Hino",
        "vehicle_model": "Dutro Z EV aluminum van with side door",
        "vehicle_class_for_scenario": "light_duty_ev_truck",
        "battery_kwh": 40,
        "range_km": 150,
        "payload_kg": 1050,
        "energy_consumption_kwh_per_km": "",
        "range_test_basis": "MLIT reviewed WLTC-mode source value",
        "payload_note": "Aluminum van specification.",
        "scenario_use": "urban last-mile EV truck scenario",
        "source_id": "hino_dutro_z_ev_2024",
        "source_url": SOURCES[3]["url"],
        "source_quote_or_location": "Dutro Z EV specification table",
        "source_confidence": "official",
    },
    {
        "scenario_vehicle_id": "toyota_pixis_van_bev_2wd_deluxe",
        "manufacturer": "Toyota",
        "vehicle_model": "Pixis Van BEV 2WD Deluxe",
        "vehicle_class_for_scenario": "kei_commercial_ev_van",
        "battery_kwh": 36.6,
        "range_km": 257,
        "payload_kg": "350 (200 with 4 passengers)",
        "energy_consumption_kwh_per_km": 0.161,
        "range_test_basis": "MLIT reviewed WLTC-mode source value",
        "payload_note": "Payload is 350 kg with 2 occupants; bracketed value is 4 occupants.",
        "scenario_use": "small commercial van scenario",
        "source_id": "toyota_pixis_van_bev_spec_2026",
        "source_url": SOURCES[4]["url"],
        "source_quote_or_location": "Pixis Van BEV 2WD Deluxe specification table",
        "source_confidence": "official",
    },
]


def download_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        target = RAW_DIR / source["local_file"]
        request = Request(source["url"], headers={"User-Agent": "research-data-collection/1.0"})
        with urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())


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


def write_tables() -> None:
    SOURCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    source_rows = []
    for source in SOURCES:
        source_rows.append(
            {
                **source,
                "local_raw_path": str((RAW_DIR / source["local_file"]).relative_to(ROOT)),
                "use_in_analysis": "Vehicle battery, range, and payload assumptions for synthetic EV delivery simulation scenarios.",
                "limitation": "Manufacturer specifications are test-condition values and vary by body, loading, environment, and driving pattern.",
            }
        )
    pd.DataFrame(source_rows).to_csv(SOURCE_CSV, index=False)
    specs = pd.DataFrame(SPEC_ROWS)
    specs.to_csv(SCENARIO_CSV, index=False)
    summary = (
        specs.groupby(["manufacturer", "vehicle_class_for_scenario"], dropna=False)
        .agg(
            scenario_rows=("scenario_vehicle_id", "size"),
            min_battery_kwh=("battery_kwh", "min"),
            max_battery_kwh=("battery_kwh", "max"),
        )
        .reset_index()
    )
    summary.to_csv(SUMMARY_CSV, index=False)


def update_research_tables() -> None:
    upsert_rows(
        INVENTORY,
        "source_id",
        [
            {
                "source_id": "ev_vehicle_specs_official_sources",
                "source_name": "Official EV truck and commercial van specification sources",
                "provider": "Mitsubishi Fuso; Isuzu; Hino; Toyota",
                "url": "see 03_data/raw/vehicle_specs/330_20260705_v02_ev_vehicle_specs_sources.csv",
                "local_raw_path": "03_data/raw/vehicle_specs/official_sources/",
                "data_type": "official html/pdf specifications",
                "collection_method": "official webpage/PDF download",
                "downloaded_at": "2026-07-05",
                "license_or_terms": "manufacturer website terms",
                "spatial_level": "vehicle model",
                "temporal_level": "2023-2026 specifications",
                "use_in_analysis": "Battery, range, and payload scenario assumptions for updated Future Wheels EV delivery simulation.",
                "limitation": "Manufacturer test-condition specifications are not observed fleet operating data.",
                "collection_status": "local_existing",
            }
        ],
    )
    specs = pd.read_csv(SCENARIO_CSV)
    socio_rows = [
        {
            "variable_id": "ev_vehicle_spec_scenario_rows",
            "source_id": "ev_vehicle_specs_official_sources",
            "country": "Japan",
            "city": "",
            "year": 2026,
            "variable_name": "EV vehicle specification scenario rows",
            "value": len(specs),
            "unit": "vehicle scenario rows",
            "spatial_level": "vehicle model",
            "temporal_level": "2023-2026 specifications",
            "analysis_axis": "Vehicle and battery scenario",
            "use_case_relevance": "Provides battery, range, and payload assumptions for synthetic Tokyo EV delivery simulation.",
            "processing_rule": "Manually structured official manufacturer specification values into scenario rows.",
            "limitation": "Scenario rows are specification-based and do not represent observed route energy use or actual fleet composition.",
            "source_url": "see 03_data/raw/vehicle_specs/330_20260705_v02_ev_vehicle_specs_sources.csv",
            "local_raw_path": "03_data/processed/416_20260705_ev_truck_specs_scenario.csv",
            "status": "extracted",
        },
        {
            "variable_id": "ev_vehicle_spec_battery_kwh_range",
            "source_id": "ev_vehicle_specs_official_sources",
            "country": "Japan",
            "city": "",
            "year": 2026,
            "variable_name": "EV vehicle scenario battery capacity range",
            "value": f"{specs['battery_kwh'].min()}-{specs['battery_kwh'].max()}",
            "unit": "kWh",
            "spatial_level": "vehicle model",
            "temporal_level": "2023-2026 specifications",
            "analysis_axis": "Vehicle and battery scenario",
            "use_case_relevance": "Defines sensitivity range for SOC feasibility and charging need in synthetic simulation.",
            "processing_rule": "Minimum and maximum battery_kwh across official specification scenario rows.",
            "limitation": "Battery capacity is total installed energy where specified; usable energy may be lower.",
            "source_url": "see 03_data/raw/vehicle_specs/330_20260705_v02_ev_vehicle_specs_sources.csv",
            "local_raw_path": "03_data/processed/416_20260705_ev_truck_specs_scenario.csv",
            "status": "extracted",
        },
    ]
    upsert_rows(SOCIO, "variable_id", socio_rows)


def main() -> None:
    download_sources()
    write_tables()
    update_research_tables()
    print(SOURCE_CSV.relative_to(ROOT))
    print(SCENARIO_CSV.relative_to(ROOT))
    print(SUMMARY_CSV.relative_to(ROOT))


if __name__ == "__main__":
    main()
