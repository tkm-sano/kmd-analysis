#!/usr/bin/env python3
"""Refine unresolved traffic comparison cross-sections from official evidence."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
DEFAULT_RAW_DIR = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
CAUSE_CODES = (
    "OFFICIAL_LOCATION_MISSING", "LOCATION_MAPPING_MISSING", "OBSERVATION_MISSING",
    "NON_CURRENT_SERIES", "MULTIPLE_CANDIDATE_CROSS_SECTION", "OTHER",
)
DIRECTIONS = {
    "up": ("up_observation_section_id_raw", "up_observation_flag_raw", "1"),
    "down": ("down_observation_section_id_raw", "down_observation_flag_raw", "2"),
}


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def split(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def flatten_coordinates(value: Any):
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        yield float(value[0]), float(value[1])
    elif isinstance(value, list):
        for item in value:
            yield from flatten_coordinates(item)


def load_geometry_index(tile_dir: Path) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(tile_dir.glob("*.geojson")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for feature in document.get("features", []):
            section_id = str(feature.get("properties", {}).get("census", ""))
            if section_id:
                grouped[section_id].append({"path": path, "feature": feature})
    output: dict[str, dict[str, Any]] = {}
    for section_id, records in grouped.items():
        coordinates = [
            coordinate
            for record in records
            for coordinate in flatten_coordinates(record["feature"].get("geometry", {}).get("coordinates", []))
        ]
        output[section_id] = {
            "feature_count": len(records),
            "source_files": [record["path"].name for record in records],
            "geometry_types": sorted({record["feature"].get("geometry", {}).get("type", "") for record in records}),
            "bbox_wgs84": [
                min(x for x, _ in coordinates), min(y for _, y in coordinates),
                max(x for x, _ in coordinates), max(y for _, y in coordinates),
            ] if coordinates else [],
            "location_representation": "OFFICIAL_SECTION_GEOMETRY_NOT_POINT",
        }
    return output


def index_raw_series(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    output: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            row.get("都道府県指定市コード", ""),
            row.get("交通量調査単位区間番号", ""),
            row.get("上り・下りの別", ""),
        )
        output[key].append(row)
    return output


def series_evidence(rows: list[dict[str, str]]) -> dict[str, Any]:
    hour_fields = [key for key in (rows[0] if rows else {}) if "時間帯別自動車類交通量" in key and "時台" in key]
    return {
        "raw_row_count": len(rows),
        "vehicle_class_codes": sorted({row.get("車種区分", "") for row in rows}),
        "observation_flags": sorted({row.get("令和３年度調査交通量観測・非観測の別", "") for row in rows}),
        "survey_dates": sorted({row.get("交通量観測年月日", "") for row in rows if row.get("交通量観測年月日", "")}),
        "hours_with_any_value": sum(any(row.get(field, "").strip() for row in rows) for field in hour_fields),
        "source_file": "MLIT_R3_zkntrf13.csv",
        "join_rule_id": "RC_R3_TRAFFIC_PREFECTURE_CITY_PLUS_UNIT_PLUS_DIRECTION_V1",
    }


def classify_direction(
    direction: str, normalized: dict[str, str], raw_sections: dict[str, dict[str, str]],
    final_by_section: dict[str, dict[str, str]], geometries: dict[str, dict[str, Any]],
    raw_series: dict[tuple[str, str, str], list[dict[str, str]]],
) -> dict[str, Any]:
    id_field, flag_field, direction_code = DIRECTIONS[direction]
    observation_id = normalized.get(id_field, "").strip()
    official_flag = normalized.get(flag_field, "").strip()
    causes: set[str] = set()
    raw_observation = raw_sections.get(observation_id)
    geometry = geometries.get(observation_id)
    final = final_by_section.get(observation_id)
    if not observation_id or raw_observation is None or geometry is None:
        causes.add("OFFICIAL_LOCATION_MISSING")
    if observation_id and (final is None or not parse_bool(final.get("usable_for_traffic_assignment", ""))):
        causes.add("LOCATION_MAPPING_MISSING")

    prefecture_city = raw_observation.get("交通量／都道府県指定市コード", "") if raw_observation else ""
    traffic_unit = raw_observation.get("交通量／調査単位区間番号", "") if raw_observation else ""
    rows = raw_series.get((prefecture_city, traffic_unit, direction_code), []) if traffic_unit else []
    series = series_evidence(rows)
    if observation_id and raw_observation is not None and (
        not rows or not {"1", "2"}.issubset(series["vehicle_class_codes"]) or series["hours_with_any_value"] == 0
    ):
        causes.add("OBSERVATION_MISSING")
    non_current = bool(rows) and (
        official_flag == "2"
        or "2" in series["observation_flags"]
        or any(date and not date.startswith("2021") for date in series["survey_dates"])
    )
    if non_current:
        causes.add("NON_CURRENT_SERIES")

    data_causes = causes & {"OFFICIAL_LOCATION_MISSING", "LOCATION_MAPPING_MISSING", "OBSERVATION_MISSING", "MULTIPLE_CANDIDATE_CROSS_SECTION"}
    if data_causes:
        classification, resolution_type = "UNRESOLVED", "DATA_INSUFFICIENCY"
    elif "NON_CURRENT_SERIES" in causes:
        classification, resolution_type = "ASSUMPTION_MAY_BE_NEEDED", "RESEARCH_ASSUMPTION"
    else:
        classification, resolution_type = "NO_ASSUMPTION_NEEDED", "OFFICIAL_EVIDENCE_RESOLVED"
    return {
        "direction": direction,
        "classification": classification,
        "resolution_type": resolution_type,
        "cause_codes": sorted(causes or {"OTHER"}),
        "official_observation_section_id": observation_id,
        "official_observation_flag": official_flag,
        "official_direction_semantics": normalized.get(f"{direction}_direction", ""),
        "official_location": geometry or {},
        "traffic_prefecture_city_code": prefecture_city,
        "traffic_unit_id": traffic_unit,
        "series": series,
        "comparison_final_corridor_id": final.get("final_corridor_id", "") if final else "",
        "comparison_final_edge_ids": split(final.get("final_edge_ids", "")) if final else [],
        "comparison_mapping_usable": bool(final and parse_bool(final.get("usable_for_traffic_assignment", ""))),
        "representative_edge_selected": False,
        "note": "The complete authoritative final corridor is retained; no representative edge or point location is inferred.",
    }


def primary_cause(direction_evidence: list[dict[str, Any]], classification: str) -> str:
    causes = {cause for item in direction_evidence if item["classification"] == classification for cause in item["cause_codes"]}
    for cause in ("OFFICIAL_LOCATION_MISSING", "LOCATION_MAPPING_MISSING", "OBSERVATION_MISSING", "MULTIPLE_CANDIDATE_CROSS_SECTION", "NON_CURRENT_SERIES", "OTHER"):
        if cause in causes:
            return cause
    return "OTHER"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classification_counts = Counter(row["refined_classification"] for row in rows)
    resolution_counts = Counter(row["resolution_type"] for row in rows)
    class_edges: dict[str, set[str]] = defaultdict(set)
    cause_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    evidence_causes: dict[tuple[str, str], set[str]] = defaultdict(set)
    comparison_edges: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        class_edges[row["refined_classification"]].update(split(row["target_final_edge_ids"]))
        cause_rows[(row["primary_cause_code"], row["refined_classification"])].append(row)
        for item in json.loads(row["direction_evidence_json"]).values():
            comparison_edges[item["classification"]].update(item["comparison_final_edge_ids"])
            for cause in item["cause_codes"]:
                evidence_causes[(cause, item["classification"])].add(row["section_id"])
    cause_summary = []
    evidence_summary = []
    for cause in CAUSE_CODES:
        for classification in ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED"):
            selected = cause_rows[(cause, classification)]
            cause_summary.append({
                "primary_cause_code": cause, "classification": classification,
                "section_count": len(selected),
                "target_unique_edge_count": len({edge for row in selected for edge in split(row["target_final_edge_ids"])}),
            })
            evidence_summary.append({
                "cause_code": cause, "direction_classification": classification,
                "section_count": len(evidence_causes[(cause, classification)]),
            })
    return {
        "schema_version": 1,
        "scope": {"original_unresolved_sections": 30, "original_assumption_candidate_sections": 2, "total_sections": len(rows)},
        "classification_summary": {
            classification: {
                "section_count": classification_counts[classification],
                "target_unique_edge_count": len(class_edges[classification]),
                "comparison_corridor_unique_edge_count": len(comparison_edges[classification]),
            }
            for classification in ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED")
        },
        "data_insufficiency_sections": resolution_counts["DATA_INSUFFICIENCY"],
        "research_assumption_needed_sections": resolution_counts["RESEARCH_ASSUMPTION"],
        "official_evidence_resolved_sections": resolution_counts["OFFICIAL_EVIDENCE_RESOLVED"],
        "raw_series_recovered_from_prior_observation_missing": sum(
            row.get("raw_series_recovered") is True for row in rows
        ),
        "policy": {
            "official_comparison_unit": "Road Census observation basic-section ID, separately for up/down",
            "location_evidence": "official GeoJSON section geometry; it is not treated as a point sensor coordinate",
            "representative_edge_selection": False,
            "position_inference": False,
            "direction_series_join": "prefecture/designated-city code + traffic unit ID + official up/down code",
            "value_or_mapping_change": False,
        },
        "primary_cause_summary": cause_summary,
        "evidence_cause_summary": evidence_summary,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(data_dir: Path = DEFAULT_DATA_DIR, raw_dir: Path = DEFAULT_RAW_DIR) -> dict[str, Any]:
    candidates = [
        row for row in read_csv(data_dir / "assumption_inventory.csv")
        if row["target"] == "TRAFFIC_COMPARISON_CROSS_SECTION"
        and row["classification"] in {"UNRESOLVED", "ASSUMPTION_MAY_BE_NEEDED"}
    ]
    if len(candidates) != 32:
        raise ValueError(f"expected 32 traffic comparison candidates, got {len(candidates)}")
    normalized = {row["section_id"]: row for row in read_csv(data_dir / "road_census_section_attributes_normalized.csv")}
    finals = {row["section_id"]: row for row in read_csv(data_dir / "census_section_final_mapping.csv")}
    raw_sections = {row["交通調査基本区間番号"]: row for row in read_csv(raw_dir / "kasyo13.csv", "cp932")}
    raw_series = index_raw_series(read_csv(raw_dir / "zkntrf13.csv", "cp932"))
    geometries = load_geometry_index(raw_dir / "webmap_tiles")
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        sid = candidate["section_id"]
        direction_evidence = [
            classify_direction(direction, normalized[sid], raw_sections, finals, geometries, raw_series)
            for direction in DIRECTIONS
        ]
        classifications = [item["classification"] for item in direction_evidence]
        if "UNRESOLVED" in classifications:
            classification, resolution_type = "UNRESOLVED", "DATA_INSUFFICIENCY"
        elif "ASSUMPTION_MAY_BE_NEEDED" in classifications:
            classification, resolution_type = "ASSUMPTION_MAY_BE_NEEDED", "RESEARCH_ASSUMPTION"
        else:
            classification, resolution_type = "NO_ASSUMPTION_NEEDED", "OFFICIAL_EVIDENCE_RESOLVED"
        target_final = finals[sid]
        output.append({
            "section_id": sid,
            "original_classification": candidate["classification"],
            "refined_classification": classification,
            "resolution_type": resolution_type,
            "primary_cause_code": primary_cause(direction_evidence, classification),
            "cause_codes": ";".join(sorted({cause for item in direction_evidence for cause in item["cause_codes"]})),
            "target_final_corridor_id": target_final["final_corridor_id"],
            "target_final_edge_ids": target_final["final_edge_ids"],
            "target_final_edge_count": len(split(target_final["final_edge_ids"])),
            "raw_series_recovered": candidate.get("issue_types") == "COMPARISON_SECTION_COUNTS_UNAVAILABLE",
            "direction_evidence_json": json.dumps({item["direction"]: item for item in direction_evidence}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "representative_edge_selected": False,
            "classification_rule_id": "TRAFFIC_COMPARISON_OFFICIAL_SECTION_AND_SERIES_V1",
            "data_changed": False,
        })
    summary = summarize(output)
    write_csv(data_dir / "traffic_comparison_cross_section_refinement.csv", output)
    write_csv(data_dir / "traffic_comparison_cross_section_refinement_summary.csv", [
        {"classification": key, **value} for key, value in summary["classification_summary"].items()
    ])
    write_csv(data_dir / "traffic_comparison_cross_section_refinement_cause_summary.csv", summary["primary_cause_summary"])
    write_csv(data_dir / "traffic_comparison_cross_section_refinement_evidence_cause_summary.csv", summary["evidence_cause_summary"])
    (data_dir / "traffic_comparison_cross_section_refinement_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.raw_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
