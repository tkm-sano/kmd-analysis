from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "03_data/raw/logistics/freight_flow_census_tokyo"
PROCESSED = ROOT / "data/processed"
INVENTORY = ROOT / "outputs/use_case_scenario/939_20260711_v03_source_data_inventory.csv"
SOCIAL_SOURCES = ROOT / "outputs/use_case_scenario/938_20260705_v03_social_side_variable_sources.csv"
SOCIO_TECH_VARIABLES = ROOT / "03_data/processed/449_20260705_socio_technical_variables.csv"

RAW_ESTABLISHMENTS = RAW_DIR / "320_20260705_v02_56_01_1011_establishment_locations_by_prefecture.csv"
RAW_GENERATED_ATTRACTED = RAW_DIR / "321_20260705_v02_56_01_2011_generated_attracted_freight_by_prefecture.csv"
RAW_INTERREGIONAL = RAW_DIR / "322_20260705_v02_56_01_3011_interregional_freight_flow_by_prefecture.csv"

OUT_ESTABLISHMENTS = PROCESSED / "452_20260705_tokyo_freight_establishment_locations.csv"
OUT_GENERATED_ATTRACTED = PROCESSED / "454_20260705_tokyo_generated_attracted_freight_by_facility.csv"
OUT_INTERREGIONAL = PROCESSED / "456_20260705_tokyo_interregional_freight_flow_by_commodity.csv"
OUT_SUMMARY = PROCESSED / "453_20260705_tokyo_freight_flow_census_summary.csv"


FACILITY_EN = {
    "事務所施設": "Office facilities",
    "工場": "Factories",
    "店舗・飲食店": "Retail and restaurant facilities",
    "物流施設": "Logistics facilities",
    "その他": "Other facilities",
    "全施設": "All facilities",
}

COMMODITY_EN = {
    "農水産品・食料工業品": "Agricultural, marine, and food products",
    "林産品・鉱産品": "Forest and mineral products",
    "金属機械工業品": "Metal and machinery products",
    "化学工業品": "Chemical products",
    "軽工業品": "Light industrial products",
    "雑工業品": "Miscellaneous industrial products",
    "排出物": "Waste and by-products",
    "特殊品": "Special cargo",
    "全品目": "All commodities",
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


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def process_establishments() -> tuple[pd.DataFrame, dict]:
    df = read_csv(RAW_ESTABLISHMENTS)
    df = df.rename(
        columns={
            "地域コード": "region_code",
            "地域名": "region_name_ja",
            "施設種類コード": "facility_type_code",
            "施設種類名称": "facility_type_ja",
            "事業所数": "establishment_count",
        }
    )
    df["facility_type_en"] = df["facility_type_ja"].map(FACILITY_EN)
    tokyo = df[df["region_code"].eq(13)].copy()
    tokyo.to_csv(OUT_ESTABLISHMENTS, index=False)

    all_facilities = tokyo.loc[tokyo["facility_type_code"].eq(9), "establishment_count"].iloc[0]
    logistics_facilities = tokyo.loc[
        tokyo["facility_type_code"].eq(4), "establishment_count"
    ].iloc[0]
    return tokyo, {
        "tokyo_total_establishments": int(all_facilities),
        "tokyo_logistics_facilities": int(logistics_facilities),
    }


def process_generated_attracted() -> tuple[pd.DataFrame, dict]:
    df = read_csv(RAW_GENERATED_ATTRACTED)
    df = df.rename(
        columns={
            "地域コード": "region_code",
            "地域名": "region_name_ja",
            "施設種類コード": "facility_type_code",
            "施設種類名称": "facility_type_ja",
            "搬出重量": "outbound_weight_tons_per_day",
            "搬出トラック台数": "outbound_trucks_per_day",
            "搬入重量": "inbound_weight_tons_per_day",
            "搬入トラック台数": "inbound_trucks_per_day",
        }
    )
    df["facility_type_en"] = df["facility_type_ja"].map(FACILITY_EN)
    tokyo = df[df["region_code"].eq(13)].copy()
    tokyo.to_csv(OUT_GENERATED_ATTRACTED, index=False)

    all_facilities = tokyo[tokyo["facility_type_code"].eq(9)].iloc[0]
    logistics_facilities = tokyo[tokyo["facility_type_code"].eq(4)].iloc[0]
    return tokyo, {
        "tokyo_outbound_weight_tons_per_day": int(all_facilities["outbound_weight_tons_per_day"]),
        "tokyo_inbound_weight_tons_per_day": int(all_facilities["inbound_weight_tons_per_day"]),
        "tokyo_outbound_trucks_per_day": int(all_facilities["outbound_trucks_per_day"]),
        "tokyo_inbound_trucks_per_day": int(all_facilities["inbound_trucks_per_day"]),
        "tokyo_logistics_facility_outbound_trucks_per_day": int(
            logistics_facilities["outbound_trucks_per_day"]
        ),
        "tokyo_logistics_facility_inbound_trucks_per_day": int(
            logistics_facilities["inbound_trucks_per_day"]
        ),
    }


def process_interregional() -> tuple[pd.DataFrame, dict]:
    df = read_csv(RAW_INTERREGIONAL)
    df = df.rename(
        columns={
            "発地コード": "origin_code",
            "発地名": "origin_name_ja",
            "着地コード": "destination_code",
            "着地名": "destination_name_ja",
            "品目コード": "commodity_code",
            "品目名称": "commodity_ja",
            "重量（発→着）": "weight_origin_to_destination_tons_per_day",
            "重量（着→発）": "weight_destination_to_origin_tons_per_day",
            "トラック台数（発→着）": "trucks_origin_to_destination_per_day",
            "トラック台数（着→発）": "trucks_destination_to_origin_per_day",
        }
    )
    df["commodity_en"] = df["commodity_ja"].map(COMMODITY_EN)
    includes_tokyo = df["origin_code"].eq(13) | df["destination_code"].eq(13)
    tokyo = df[includes_tokyo].copy()

    tokyo["tokyo_direction"] = tokyo.apply(
        lambda row: "Tokyo outbound"
        if row["origin_code"] == 13
        else "Tokyo inbound"
        if row["destination_code"] == 13
        else "not_tokyo",
        axis=1,
    )
    tokyo["tokyo_counterpart_region_code"] = tokyo.apply(
        lambda row: row["destination_code"] if row["origin_code"] == 13 else row["origin_code"],
        axis=1,
    )
    tokyo["tokyo_counterpart_region_name_ja"] = tokyo.apply(
        lambda row: row["destination_name_ja"] if row["origin_code"] == 13 else row["origin_name_ja"],
        axis=1,
    )
    tokyo["tokyo_outbound_weight_tons_per_day"] = tokyo.apply(
        lambda row: row["weight_origin_to_destination_tons_per_day"]
        if row["origin_code"] == 13
        else row["weight_destination_to_origin_tons_per_day"],
        axis=1,
    )
    tokyo["tokyo_inbound_weight_tons_per_day"] = tokyo.apply(
        lambda row: row["weight_destination_to_origin_tons_per_day"]
        if row["origin_code"] == 13
        else row["weight_origin_to_destination_tons_per_day"],
        axis=1,
    )
    tokyo["tokyo_outbound_trucks_per_day"] = tokyo.apply(
        lambda row: row["trucks_origin_to_destination_per_day"]
        if row["origin_code"] == 13
        else row["trucks_destination_to_origin_per_day"],
        axis=1,
    )
    tokyo["tokyo_inbound_trucks_per_day"] = tokyo.apply(
        lambda row: row["trucks_destination_to_origin_per_day"]
        if row["origin_code"] == 13
        else row["trucks_origin_to_destination_per_day"],
        axis=1,
    )
    tokyo.to_csv(OUT_INTERREGIONAL, index=False)

    all_commodities = tokyo[tokyo["commodity_code"].eq(9)]
    return tokyo, {
        "tokyo_interregional_rows": int(len(tokyo)),
        "tokyo_interregional_counterpart_regions": int(
            all_commodities["tokyo_counterpart_region_code"].nunique()
        ),
        "tokyo_interregional_outbound_weight_tons_per_day": round(
            float(all_commodities["tokyo_outbound_weight_tons_per_day"].sum()), 3
        ),
        "tokyo_interregional_inbound_weight_tons_per_day": round(
            float(all_commodities["tokyo_inbound_weight_tons_per_day"].sum()), 3
        ),
        "tokyo_interregional_outbound_trucks_per_day": round(
            float(all_commodities["tokyo_outbound_trucks_per_day"].sum()), 3
        ),
        "tokyo_interregional_inbound_trucks_per_day": round(
            float(all_commodities["tokyo_inbound_trucks_per_day"].sum()), 3
        ),
    }


def process() -> dict:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    _, establishment_summary = process_establishments()
    _, generated_summary = process_generated_attracted()
    _, interregional_summary = process_interregional()

    summary = {
        "source_id": "freight_flow_census_tokyo_visual_csvs",
        "source_name": "Freight establishment, generated/attracted freight, and interregional freight-flow CSVs",
        "local_raw_dir": str(RAW_DIR.relative_to(ROOT)),
        "processed_establishment_csv": str(OUT_ESTABLISHMENTS.relative_to(ROOT)),
        "processed_generated_attracted_csv": str(OUT_GENERATED_ATTRACTED.relative_to(ROOT)),
        "processed_interregional_csv": str(OUT_INTERREGIONAL.relative_to(ROOT)),
        **establishment_summary,
        **generated_summary,
        **interregional_summary,
        "use_in_analysis": "Tokyo freight-demand, truck-count, establishment-density, and interregional-flow context for EV last-mile routing scenario design.",
        "limitation": "Aggregated public CSVs; not customer-level stops, operator depots, EV fleet schedules, or charging events.",
    }
    pd.DataFrame([summary]).to_csv(OUT_SUMMARY, index=False)

    append_or_replace_csv(
        INVENTORY,
        [
            {
                "source_id": "freight_flow_census_tokyo_visual_csvs",
                "source_name": "Freight establishment, generated/attracted freight, and interregional freight-flow CSVs",
                "provider": "User-downloaded public logistics visualization CSVs",
                "year_or_version": "not specified in file",
                "url": "",
                "local_raw_path": str(RAW_DIR.relative_to(ROOT)),
                "data_type": "csv",
                "geographic_scope": "Tokyo and prefectural interregional flows",
                "spatial_level": "prefecture",
                "use_in_analysis": "Freight-demand and truck-count context for Tokyo EV routing requirement mapping and Future Wheels inputs.",
                "limitation": "Aggregated logistics indicators, not observed EV delivery routes or charging behavior.",
            }
        ],
        key="source_id",
    )

    social_rows = [
        {
            "variable_id": "tokyo_freight_establishments_all_facilities",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "stage_layer": "social_demand_context",
            "variable_name": "Tokyo establishments that generate or attract logistics activity",
            "value": summary["tokyo_total_establishments"],
            "unit": "establishments",
            "geographic_scope": "Tokyo",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "processing_rule": "Filtered 56_01_1011 to region_code=13 and facility_type_code=9.",
            "use_in_analysis": "Proxy for potential freight-demand node density in Tokyo.",
            "source_url": "",
            "local_raw_path": str(RAW_ESTABLISHMENTS.relative_to(ROOT)),
            "limitation": "Establishment count is not customer-stop count or delivery-route count.",
        },
        {
            "variable_id": "tokyo_freight_logistics_facilities",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "stage_layer": "social_depot_context",
            "variable_name": "Tokyo logistics facilities in freight-generating establishments",
            "value": summary["tokyo_logistics_facilities"],
            "unit": "facilities",
            "geographic_scope": "Tokyo",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "processing_rule": "Filtered 56_01_1011 to region_code=13 and facility_type_code=4.",
            "use_in_analysis": "Proxy for logistics facility concentration and possible depot/service-area context.",
            "source_url": "",
            "local_raw_path": str(RAW_ESTABLISHMENTS.relative_to(ROOT)),
            "limitation": "Facility category is not evidence that a site is an EV depot or available for simulation.",
        },
        {
            "variable_id": "tokyo_generated_outbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "stage_layer": "social_demand_context",
            "variable_name": "Tokyo generated outbound freight trucks",
            "value": summary["tokyo_outbound_trucks_per_day"],
            "unit": "trucks per day",
            "geographic_scope": "Tokyo",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "processing_rule": "Filtered 56_01_2011 to region_code=13 and facility_type_code=9.",
            "use_in_analysis": "Truck-activity proxy for freight pressure in the Tokyo EV routing use case.",
            "source_url": "",
            "local_raw_path": str(RAW_GENERATED_ATTRACTED.relative_to(ROOT)),
            "limitation": "Truck count is aggregate freight activity and not EV fleet size or route count.",
        },
        {
            "variable_id": "tokyo_generated_inbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "stage_layer": "social_demand_context",
            "variable_name": "Tokyo attracted inbound freight trucks",
            "value": summary["tokyo_inbound_trucks_per_day"],
            "unit": "trucks per day",
            "geographic_scope": "Tokyo",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "processing_rule": "Filtered 56_01_2011 to region_code=13 and facility_type_code=9.",
            "use_in_analysis": "Truck-activity proxy for inbound freight pressure in the Tokyo EV routing use case.",
            "source_url": "",
            "local_raw_path": str(RAW_GENERATED_ATTRACTED.relative_to(ROOT)),
            "limitation": "Truck count is aggregate freight activity and not EV fleet size or route count.",
        },
    ]
    append_or_replace_csv(SOCIAL_SOURCES, social_rows, key="variable_id")
    socio_rows = [
        {
            "variable_id": "tokyo_freight_establishments_all_facilities",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo establishments that generate or attract logistics activity",
            "value": summary["tokyo_total_establishments"],
            "unit": "establishments",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "analysis_axis": "Freight demand proxy",
            "use_case_relevance": "Supports synthetic customer-node and freight-demand context for Tokyo EV last-mile routing.",
            "processing_rule": "Filtered 56_01_1011 to region_code=13 and facility_type_code=9.",
            "limitation": "Establishment count is not customer-stop count or delivery-route count.",
            "source_url": "",
            "local_raw_path": str(RAW_ESTABLISHMENTS.relative_to(ROOT)),
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_freight_logistics_facilities",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo logistics facilities in freight-generating establishments",
            "value": summary["tokyo_logistics_facilities"],
            "unit": "facilities",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "analysis_axis": "Depot and logistics facility proxy",
            "use_case_relevance": "Supports depot/service-area context for Tokyo EV last-mile routing.",
            "processing_rule": "Filtered 56_01_1011 to region_code=13 and facility_type_code=4.",
            "limitation": "Facility category is not evidence that a site is an EV depot or available for simulation.",
            "source_url": "",
            "local_raw_path": str(RAW_ESTABLISHMENTS.relative_to(ROOT)),
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_generated_outbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo generated outbound freight trucks",
            "value": summary["tokyo_outbound_trucks_per_day"],
            "unit": "trucks per day",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "analysis_axis": "Freight activity proxy",
            "use_case_relevance": "Provides aggregate freight-truck activity pressure for Tokyo EV routing motivation.",
            "processing_rule": "Filtered 56_01_2011 to region_code=13 and facility_type_code=9.",
            "limitation": "Truck count is aggregate freight activity and not EV fleet size or route count.",
            "source_url": "",
            "local_raw_path": str(RAW_GENERATED_ATTRACTED.relative_to(ROOT)),
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_generated_inbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo attracted inbound freight trucks",
            "value": summary["tokyo_inbound_trucks_per_day"],
            "unit": "trucks per day",
            "spatial_level": "prefecture",
            "temporal_level": "not specified in file",
            "analysis_axis": "Freight activity proxy",
            "use_case_relevance": "Provides aggregate inbound freight-truck activity pressure for Tokyo EV routing motivation.",
            "processing_rule": "Filtered 56_01_2011 to region_code=13 and facility_type_code=9.",
            "limitation": "Truck count is aggregate freight activity and not EV fleet size or route count.",
            "source_url": "",
            "local_raw_path": str(RAW_GENERATED_ATTRACTED.relative_to(ROOT)),
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_interregional_outbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo interregional outbound freight trucks",
            "value": summary["tokyo_interregional_outbound_trucks_per_day"],
            "unit": "trucks per day",
            "spatial_level": "prefecture-pair OD",
            "temporal_level": "not specified in file",
            "analysis_axis": "Interregional freight context",
            "use_case_relevance": "Optional context for Tokyo boundary-crossing freight, not the main last-mile routing input.",
            "processing_rule": "Filtered 56_01_3011 to rows involving Tokyo and summed all-commodity Tokyo outbound truck counts.",
            "limitation": "Interregional OD is useful background but does not identify urban last-mile stops or EV charging events.",
            "source_url": "",
            "local_raw_path": str(RAW_INTERREGIONAL.relative_to(ROOT)),
            "status": "extracted",
        },
        {
            "variable_id": "tokyo_interregional_inbound_trucks_per_day",
            "source_id": "freight_flow_census_tokyo_visual_csvs",
            "country": "Japan",
            "city": "Tokyo",
            "year": "",
            "variable_name": "Tokyo interregional inbound freight trucks",
            "value": summary["tokyo_interregional_inbound_trucks_per_day"],
            "unit": "trucks per day",
            "spatial_level": "prefecture-pair OD",
            "temporal_level": "not specified in file",
            "analysis_axis": "Interregional freight context",
            "use_case_relevance": "Optional context for Tokyo boundary-crossing freight, not the main last-mile routing input.",
            "processing_rule": "Filtered 56_01_3011 to rows involving Tokyo and summed all-commodity Tokyo inbound truck counts.",
            "limitation": "Interregional OD is useful background but does not identify urban last-mile stops or EV charging events.",
            "source_url": "",
            "local_raw_path": str(RAW_INTERREGIONAL.relative_to(ROOT)),
            "status": "extracted",
        },
    ]
    append_or_replace_csv(SOCIO_TECH_VARIABLES, socio_rows, key="variable_id")
    return summary


if __name__ == "__main__":
    print(pd.Series(process()).to_string())
