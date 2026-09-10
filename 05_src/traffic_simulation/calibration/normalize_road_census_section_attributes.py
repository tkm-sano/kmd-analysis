#!/usr/bin/env python3
"""Normalize official R3 Road Census section semantics without imputation.

Only code-table transformations documented by MLIT are applied. Raw values are
preserved, blanks remain blank, and GeoJSON coordinate order is never used as
evidence of official direction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW_DIR = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
MLIT_DEFINITION_URL = "https://www.mlit.go.jp/road/census/r3/data/pdf/kasyorep.pdf"

SOURCE_SECTION = "MLIT_R3_kasyo13.csv"
SOURCE_TRAFFIC = "MLIT_R3_zkntrf13.csv"
SOURCE_DEFINITION = "MLIT_R3_kasyorep.pdf"

ROAD_TYPES = {
    "1": ("EXPRESSWAY_NATIONAL", "高速自動車国道", "JP_EXPRESSWAY_NATIONAL"),
    "2": ("URBAN_EXPRESSWAY", "都市高速道路", "JP_URBAN_EXPRESSWAY"),
    "3": ("NATIONAL_HIGHWAY", "一般国道", "JP_NATIONAL_HIGHWAY"),
    "4": ("MAJOR_PREFECTURAL_ROAD", "主要地方道（都道府県道）", "JP_PREFECTURAL_ROAD"),
    "5": ("MAJOR_DESIGNATED_CITY_ROAD", "主要地方道（指定市市道）", "JP_DESIGNATED_CITY_ROAD"),
    "6": ("GENERAL_PREFECTURAL_ROAD", "一般都道府県道", "JP_PREFECTURAL_ROAD"),
    "7": ("DESIGNATED_CITY_GENERAL_ROAD", "指定市の一般市道", "JP_DESIGNATED_CITY_ROAD"),
}

OPERATORS = {
    "1": ("MLIT", "国土交通大臣"),
    "2": ("PREFECTURAL_GOVERNMENT", "都道府県知事又は都道府県"),
    "3": ("DESIGNATED_CITY", "指定市の長又は指定市"),
    "4": ("NEXCO", "東日本・中日本・西日本高速道路株式会社"),
    "5": ("SHUTO_EXPRESSWAY", "首都高速道路株式会社"),
    "6": ("HANSHIN_EXPRESSWAY", "阪神高速道路株式会社"),
    "7": ("HSBE", "本州四国連絡高速道路株式会社"),
    "8": ("LOCAL_ROAD_PUBLIC_CORPORATION", "地方道路公社等"),
    "9": ("OTHER_OFFICIAL_MANAGER", "その他"),
}

CONNECTION_TYPES = {
    "1": "CONNECTED_TO_OTHER_BRANCH_TERMINUS_SIDE",
    "2": "CONNECTED_TO_OTHER_BRANCH_ORIGIN_SIDE",
    "3": "PREFECTURE_BOUNDARY",
    "4": "TWO_DIFFERENT_BRANCH_ENDPOINTS_ONLY",
    "5": "MANAGER_BOUNDARY_OR_MOTORWAY_DESIGNATION_ENDPOINT",
    "6": "MUNICIPALITY_BOUNDARY",
    "7": "LARGE_FACILITY_ACCESS_POINT",
    "8": "BRANCH_ENDPOINT_WITHOUT_OTHER_SECTION",
    "9": "LEGACY_DIVISION_POINT",
}

SECTION_TYPES = {
    "0": "NORMAL",
    "1": "DIVIDED_CARRIAGEWAY",
    "2": "MULTI_CARRIAGEWAY",
    "3": "DIVIDED_AND_MULTI_CARRIAGEWAY",
    "6": "MOTOR_TRAFFIC_IMPASSABLE",
    "7": "CIRCULAR",
    "8": "PARTIALLY_OPEN",
}

SEPARATION_TYPES = {
    "0": "NOT_SEPARATED",
    "1": "UP_MAIN_CARRIAGEWAY",
    "2": "DOWN_MAIN_CARRIAGEWAY",
    "3": "UP_SECONDARY_CARRIAGEWAY",
    "4": "DOWN_SECONDARY_CARRIAGEWAY",
}

ONEWAY_TYPES = {
    "0": ("BIDIRECTIONAL", "BOTH"),
    "1": ("ONEWAY_ORIGIN_TO_TERMINUS", "DOWN"),
    "2": ("ONEWAY_TERMINUS_TO_ORIGIN", "UP"),
}

TRAFFIC_DIRECTIONS = {
    "1": ("UP", "TERMINUS_TO_ORIGIN"),
    "2": ("DOWN", "ORIGIN_TO_TERMINUS"),
}

RULES = {
    "section_id": "RC_R3_SECTION_ID_COMPONENTS_V1",
    "road_type": "RC_R3_ROAD_TYPE_CODE_TABLE_V1",
    "operator": "RC_R3_MANAGEMENT_CODE_TABLE_V1",
    "route_number": "RC_R3_ROUTE_NUMBER_PRESERVE_OFFICIAL_V1",
    "canonical_route": "RC_R3_CANONICAL_ROUTE_COMPOSITE_V1",
    "endpoint": "RC_R3_ENDPOINT_CONNECTION_CODE_TABLE_V1",
    "oneway": "RC_R3_ONEWAY_CODE_TABLE_V1",
    "lanes": "RC_R3_REPRESENTATIVE_TOTAL_LANES_V1",
    "section_type": "RC_R3_SECTION_TYPE_CODE_TABLE_V1",
    "separation": "RC_R3_SEPARATION_CODE_TABLE_V1",
    "traffic_direction": "RC_R3_TRAFFIC_DIRECTION_CODE_TABLE_V1",
    "no_geometry_direction": "RC_R3_GEOJSON_DIRECTION_NOT_AUTHORIZED_V1",
}


def read_cp932(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="cp932", newline="") as handle:
        return list(csv.DictReader(handle))


def clean(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_integer_text(value: str | None) -> str | None:
    text = clean(value)
    if not text or not text.isdigit() or int(text) <= 0:
        return None
    return str(int(text))


def canonical_route_key(
    road_system: str, network: str, operator: str, route_number: str
) -> str | None:
    if not all((road_system, network, operator, route_number)):
        return None
    return "|".join((road_system, network, operator, route_number))


def parse_section_id(section_id: str) -> dict[str, str] | None:
    if len(section_id) != 11 or not section_id.isdigit():
        return None
    return {
        "prefecture_code": section_id[:2],
        "road_type_code": section_id[2],
        "route_number_code4": section_id[3:7],
        "sequence_number_code4": section_id[7:11],
    }


def _issue(
    issues: list[dict[str, str]], section_id: str, category: str, field: str,
    raw_value: str, detail: str,
) -> None:
    issues.append({
        "section_id": section_id,
        "category": category,
        "field": field,
        "raw_value": raw_value,
        "detail": detail,
    })


def _code_value(
    mapping: dict[str, Any], raw: str, *, section_id: str, field: str,
    issues: list[dict[str, str]],
) -> Any | None:
    if not raw:
        _issue(issues, section_id, "MISSING", field, raw, "required official code is blank")
        return None
    if raw not in mapping:
        _issue(issues, section_id, "UNREGISTERED_CODE", field, raw, "code is absent from the MLIT R3 code table")
        return None
    return mapping[raw]


def normalize_section(
    raw: dict[str, str], traffic_direction_codes: set[str],
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    sid_raw = raw.get("交通調査基本区間番号", "")
    sid = clean(sid_raw)
    parsed = parse_section_id(sid)
    if parsed is None:
        _issue(issues, sid, "CONVERSION_ERROR", "section_id", sid_raw, "section ID must be exactly 11 digits")
        parsed = {key: "" for key in ("prefecture_code", "road_type_code", "route_number_code4", "sequence_number_code4")}

    road_type_raw = clean(raw.get("道路種別"))
    road_type = _code_value(ROAD_TYPES, road_type_raw, section_id=sid, field="road_type_code", issues=issues)
    road_system, road_type_label, network_base = road_type or ("", "", "")
    operator_raw = clean(raw.get("管理区分"))
    operator_value = _code_value(OPERATORS, operator_raw, section_id=sid, field="management_code", issues=issues)
    operator, operator_label = operator_value or ("", "")
    route_raw = raw.get("路線番号", "")
    route_number = positive_integer_text(route_raw)
    if route_number is None:
        category = "MISSING" if not clean(route_raw) else "CONVERSION_ERROR"
        _issue(issues, sid, category, "route_number", route_raw, "official route number must be a positive integer")

    section_components_consistent = parsed is not None
    if parsed and parsed["road_type_code"] and road_type_raw and parsed["road_type_code"] != road_type_raw:
        _issue(issues, sid, "CONVERSION_ERROR", "section_id.road_type", sid, "embedded road type differs from the road_type field")
        section_components_consistent = False
    if parsed and parsed["route_number_code4"] and route_number is not None:
        if str(int(parsed["route_number_code4"])) != route_number:
            _issue(issues, sid, "CONVERSION_ERROR", "section_id.route_number", sid, "embedded route number differs from the route_number field")
            section_components_consistent = False

    prefecture = parsed["prefecture_code"] if parsed else ""
    if network_base == "JP_PREFECTURAL_ROAD" and prefecture:
        network = f"{network_base}:{prefecture}"
    elif network_base == "JP_DESIGNATED_CITY_ROAD":
        municipality = clean(raw.get("市区町村コード"))
        network = f"{network_base}:{municipality}" if municipality else ""
    else:
        network = network_base
    route_key = canonical_route_key(road_system, network, operator, route_number or "")
    if not section_components_consistent:
        route_key = None
    if route_key is None:
        _issue(issues, sid, "UNRESOLVED", "canonical_route_key", "", "one or more canonical route components are unresolved")

    origin_code = clean(raw.get("起点側／接続区分"))
    terminus_code = clean(raw.get("終点側／接続区分"))
    origin_type = _code_value(CONNECTION_TYPES, origin_code, section_id=sid, field="origin_connection_code", issues=issues) or ""
    terminus_type = _code_value(CONNECTION_TYPES, terminus_code, section_id=sid, field="terminus_connection_code", issues=issues) or ""
    section_type_raw = clean(raw.get("区間種別"))
    section_type = _code_value(SECTION_TYPES, section_type_raw, section_id=sid, field="section_type_code", issues=issues) or ""
    separation_raw = clean(raw.get("分離区間／分離区分"))
    separation = _code_value(SEPARATION_TYPES, separation_raw, section_id=sid, field="separation_code", issues=issues) or ""
    oneway_raw = clean(raw.get("一方通行フラグ"))
    oneway_value = _code_value(ONEWAY_TYPES, oneway_raw, section_id=sid, field="oneway_code", issues=issues)
    oneway, permitted_direction = oneway_value or ("", "")

    lanes_raw = raw.get("車線数", "")
    lanes = positive_integer_text(lanes_raw)
    if lanes is None:
        category = "MISSING" if not clean(lanes_raw) else "CONVERSION_ERROR"
        _issue(issues, sid, category, "lane_count", lanes_raw, "official lane count must be a positive integer")
    if not oneway_value:
        lane_direction_scope = ""
    elif oneway_raw == "0":
        lane_direction_scope = "BOTH_DIRECTIONS_TOTAL"
    else:
        lane_direction_scope = "PERMITTED_ONEWAY_DIRECTION_TOTAL"

    traffic_codes_raw = ";".join(sorted(traffic_direction_codes))
    unknown_traffic_codes = sorted(traffic_direction_codes - set(TRAFFIC_DIRECTIONS))
    if not traffic_direction_codes:
        _issue(issues, sid, "MISSING", "traffic_direction_code", "", "no zkntrf direction code exists for the traffic unit")
    for code in unknown_traffic_codes:
        _issue(issues, sid, "UNREGISTERED_CODE", "traffic_direction_code", code, "code is absent from the MLIT R3 direction code table")
    traffic_normalized = ";".join(
        f"{TRAFFIC_DIRECTIONS[code][0]}={TRAFFIC_DIRECTIONS[code][1]}"
        for code in sorted(traffic_direction_codes) if code in TRAFFIC_DIRECTIONS
    )

    row_issue_categories = {
        issue["category"] for issue in issues if issue["section_id"] == sid
    }
    status = "UNRESOLVED" if row_issue_categories & {
        "MISSING", "UNREGISTERED_CODE", "CONVERSION_ERROR", "UNRESOLVED"
    } else "RESOLVED"

    return {
        "section_id_raw": sid_raw,
        "section_id": sid,
        "section_id_status": "RESOLVED" if section_components_consistent else "UNRESOLVED",
        "section_id_source": SOURCE_SECTION,
        "section_id_normalization_rule_id": RULES["section_id"],
        "prefecture_code": parsed["prefecture_code"],
        "section_sequence_number_code4": parsed["sequence_number_code4"],
        "sequence_direction_semantics": "GENERALLY_INCREASES_ORIGIN_TO_TERMINUS_NOT_AUTHORITATIVE",
        "road_type_code_raw": raw.get("道路種別", ""),
        "road_type_code": road_type_raw,
        "road_type_label_ja": road_type_label,
        "road_system": road_system,
        "road_type_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "road_type_normalization_rule_id": RULES["road_type"],
        "management_code_raw": raw.get("管理区分", ""),
        "management_code": operator_raw,
        "operator": operator,
        "operator_label_ja": operator_label,
        "operator_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "operator_normalization_rule_id": RULES["operator"],
        "network": network,
        "route_number_raw": route_raw,
        "route_number": route_number or "",
        "route_name_raw": raw.get("路線名", ""),
        "route_number_source": SOURCE_SECTION,
        "route_number_normalization_rule_id": RULES["route_number"],
        "canonical_route_key": route_key or "",
        "canonical_route_key_status": "RESOLVED" if route_key else "UNRESOLVED",
        "canonical_route_key_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "canonical_route_key_normalization_rule_id": RULES["canonical_route"],
        "origin_connection_code_raw": raw.get("起点側／接続区分", ""),
        "origin_connection_type": origin_type,
        "origin_adjacent_section_id_raw": raw.get("起点側／交通調査基本区間番号", ""),
        "origin_adjacent_generation_tens_raw": raw.get("起点側／世代管理番号（十の位）", ""),
        "origin_label_raw": raw.get("起点側／路線名等", ""),
        "origin_note_raw": raw.get("起点側／備考", ""),
        "origin_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "origin_normalization_rule_id": RULES["endpoint"],
        "terminus_connection_code_raw": raw.get("終点側／接続区分", ""),
        "terminus_connection_type": terminus_type,
        "terminus_adjacent_section_id_raw": raw.get("終点側／交通調査基本区間番号", ""),
        "terminus_adjacent_generation_tens_raw": raw.get("終点側／世代管理番号（十の位）", ""),
        "terminus_label_raw": raw.get("終点側／路線名等", ""),
        "terminus_note_raw": raw.get("終点側／備考", ""),
        "terminus_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "terminus_normalization_rule_id": RULES["endpoint"],
        "oneway_code_raw": raw.get("一方通行フラグ", ""),
        "oneway": oneway,
        "permitted_census_direction": permitted_direction,
        "oneway_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "oneway_normalization_rule_id": RULES["oneway"],
        "lane_count_raw": lanes_raw,
        "lane_count": lanes or "",
        "lane_count_scope": "REPRESENTATIVE_CROSS_SECTION" if lanes else "",
        "lane_direction_scope": lane_direction_scope,
        "lane_exclusions": "CLIMBING;ADDITIONAL_PASSING;TURN;ACCEL_DECEL;STOPPING;YIELDING",
        "lane_count_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "lane_count_normalization_rule_id": RULES["lanes"],
        "section_type_code_raw": raw.get("区間種別", ""),
        "section_type": section_type,
        "section_type_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "section_type_normalization_rule_id": RULES["section_type"],
        "separation_code_raw": raw.get("分離区間／分離区分", ""),
        "separation_type": separation,
        "separation_main_section_id_raw": raw.get("分離区間／交通調査基本区間番号", ""),
        "separation_source": f"{SOURCE_SECTION};{SOURCE_DEFINITION}",
        "separation_normalization_rule_id": RULES["separation"],
        "traffic_unit_id_raw": raw.get("交通量／調査単位区間番号", ""),
        "traffic_direction_codes_raw": traffic_codes_raw,
        "traffic_directions": traffic_normalized,
        "up_direction": "TERMINUS_TO_ORIGIN",
        "down_direction": "ORIGIN_TO_TERMINUS",
        "up_observation_section_id_raw": raw.get("上り／観測地点交通調査基本区間番号", ""),
        "down_observation_section_id_raw": raw.get("下り／観測地点交通調査基本区間番号", ""),
        "up_observation_flag_raw": raw.get("上り／令和３年度調査交通量観測・非観測の別", ""),
        "down_observation_flag_raw": raw.get("下り／令和３年度調査交通量観測・非観測の別", ""),
        "traffic_direction_source": f"{SOURCE_TRAFFIC};{SOURCE_DEFINITION}",
        "traffic_direction_normalization_rule_id": RULES["traffic_direction"],
        "geojson_digitization_direction_used": False,
        "geojson_digitization_direction_status": "UNVERIFIED",
        "geojson_direction_rule_id": RULES["no_geometry_direction"],
        "normalization_status": status,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(raw_dir: Path, output_dir: Path, municipality_code: str = "13111") -> dict[str, Any]:
    section_path = raw_dir / "kasyo13.csv"
    traffic_path = raw_dir / "zkntrf13.csv"
    section_rows_all = read_cp932(section_path)
    section_rows = [row for row in section_rows_all if clean(row.get("市区町村コード")) == municipality_code]
    traffic_rows = read_cp932(traffic_path)
    directions_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in traffic_rows:
        unit = clean(row.get("交通量調査単位区間番号"))
        direction = clean(row.get("上り・下りの別"))
        if unit and direction:
            directions_by_unit[unit].add(direction)

    raw_ids = [clean(row.get("交通調査基本区間番号")) for row in section_rows]
    duplicate_ids = sorted(sid for sid, count in Counter(raw_ids).items() if count > 1)
    issues: list[dict[str, str]] = []
    for sid in duplicate_ids:
        _issue(issues, sid, "DUPLICATE", "section_id", sid, "section ID occurs more than once")
    normalized = [
        normalize_section(
            row,
            directions_by_unit.get(clean(row.get("交通量／調査単位区間番号")), set()),
            issues,
        )
        for row in section_rows
    ]
    output_path = output_dir / "road_census_section_attributes_normalized.csv"
    write_csv(output_path, normalized, list(normalized[0]))
    issue_path = output_dir / "road_census_section_attributes_normalized_qa_issues.csv"
    write_csv(issue_path, issues, ["section_id", "category", "field", "raw_value", "detail"])

    category_counts = Counter(issue["category"] for issue in issues)
    unregistered = defaultdict(Counter)
    missing = defaultdict(int)
    for issue in issues:
        if issue["category"] == "UNREGISTERED_CODE":
            unregistered[issue["field"]][issue["raw_value"]] += 1
        if issue["category"] == "MISSING":
            missing[issue["field"]] += 1
    summary = {
        "schema_version": 1,
        "scope": {"municipality_code": municipality_code, "section_count": len(normalized)},
        "official_definition": {"source": SOURCE_DEFINITION, "url": MLIT_DEFINITION_URL},
        "raw_inputs": {
            "section_csv": {
                "path": str(section_path.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_file(section_path),
            },
            "hourly_traffic_csv": {
                "path": str(traffic_path.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_file(traffic_path),
            },
        },
        "output": str(output_path.relative_to(REPOSITORY_ROOT)),
        "no_imputation": True,
        "geojson_direction_used": False,
        "normalization_status_counts": dict(Counter(row["normalization_status"] for row in normalized)),
        "unresolved_section_count": sum(row["normalization_status"] == "UNRESOLVED" for row in normalized),
        "unregistered_code_count": category_counts["UNREGISTERED_CODE"],
        "unregistered_codes": {field: dict(values) for field, values in sorted(unregistered.items())},
        "missing_value_count": category_counts["MISSING"],
        "missing_values_by_required_field": dict(sorted(missing.items())),
        "duplicate_section_id_count": len(duplicate_ids),
        "duplicate_section_ids": duplicate_ids,
        "conversion_error_count": category_counts["CONVERSION_ERROR"],
        "other_unresolved_issue_count": category_counts["UNRESOLVED"],
        "qa_issue_count": len(issues),
        "canonical_route_key_count": len({row["canonical_route_key"] for row in normalized if row["canonical_route_key"]}),
        "canonical_route_key_duplicates_are_expected": "multiple Census sections normally belong to the same route",
        "normalization_rule_ids": RULES,
    }
    (output_dir / "road_census_section_attributes_normalized_qa_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--municipality-code", default="13111")
    args = parser.parse_args()
    print(json.dumps(run(args.raw_dir, args.output_dir, args.municipality_code), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
