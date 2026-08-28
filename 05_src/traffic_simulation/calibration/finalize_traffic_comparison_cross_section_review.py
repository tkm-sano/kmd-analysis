#!/usr/bin/env python3
"""Finalize the evidence-only review of Road Census comparison cross-sections.

No representative SUMO edge, point coordinate, traffic value, or threshold is
created here.  The audit separates missing official/mapping evidence from a
genuine choice among multiple directed SUMO edge candidates.
"""

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
    "OFFICIAL_LOCATION_AVAILABLE", "LOCATION_MAPPING_MISSING", "OBSERVATION_MISSING",
    "NON_CURRENT_SERIES", "MULTIPLE_CANDIDATE_CROSS_SECTION", "DATA_CONFLICT", "OTHER",
)
FINAL_CLASSES = ("NO_ASSUMPTION_NEEDED", "MODEL_ASSUMPTION_REQUIRED", "UNRESOLVED")
DIRECTION_FIELDS = {
    "up": "上り／交通量観測地点地名",
    "down": "下り／交通量観測地点地名",
}


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def split(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def classify_direction(
    prior: dict[str, Any], location_name: str, comparison_mapping: dict[str, str] | None,
    normalized_observation: dict[str, str] | None, edges: dict[str, dict[str, str]],
) -> dict[str, Any]:
    observation_id = prior["official_observation_section_id"]
    geometry = prior["official_location"]
    series = prior["series"]
    mapping_usable = bool(comparison_mapping and parse_bool(comparison_mapping.get("usable_for_traffic_assignment", "")))
    candidate_edges = split(comparison_mapping.get("final_edge_ids", "")) if mapping_usable and comparison_mapping else []
    causes: set[str] = set()
    location_available = bool(observation_id and location_name and geometry)
    if location_available:
        causes.add("OFFICIAL_LOCATION_AVAILABLE")
    else:
        # The requested taxonomy has no OFFICIAL_LOCATION_MISSING code.  An
        # absent official observation-section identifier is recorded as an
        # observation-data deficit; partial/inconsistent location fields use
        # OTHER rather than inventing an unregistered category.
        causes.add("OTHER" if observation_id else "OBSERVATION_MISSING")
    series_available = (
        series.get("raw_row_count", 0) > 0
        and {"1", "2"}.issubset(series.get("vehicle_class_codes", []))
        and series.get("hours_with_any_value", 0) > 0
    )
    if not series_available:
        causes.add("OBSERVATION_MISSING")
    non_current = (
        prior.get("official_observation_flag") == "2"
        or "2" in series.get("observation_flags", [])
        or any(date and not date.startswith("2021") for date in series.get("survey_dates", []))
    )
    if non_current and series_available:
        causes.add("NON_CURRENT_SERIES")
    if observation_id and not mapping_usable:
        causes.add("LOCATION_MAPPING_MISSING")

    bidirectional = bool(normalized_observation and normalized_observation.get("oneway") == "BIDIRECTIONAL")
    opposing_direction_mapping_missing = False
    if location_available and series_available and mapping_usable:
        if len(candidate_edges) > 1:
            causes.add("MULTIPLE_CANDIDATE_CROSS_SECTION")
        # A Census basic section may represent both directions while the OSM
        # network uses separate one-way carriageway Ways.  Absence of the
        # opposite carriageway from the final mapping is a mapping deficit, not
        # proof that the two source datasets contradict one another.
        opposing_direction_mapping_missing = bidirectional and all(
            edges[edge_id].get("reverse_edge_status") != "RESOLVED_EXACT_SAME_WAY"
            and not edges[edge_id].get("reverse_edge_id_normalized")
            for edge_id in candidate_edges
        )
        if opposing_direction_mapping_missing:
            causes.add("LOCATION_MAPPING_MISSING")

    if causes & {"LOCATION_MAPPING_MISSING", "OBSERVATION_MISSING", "DATA_CONFLICT", "OTHER"}:
        classification = "UNRESOLVED"
        resolution_type = "EVIDENCE_OR_MAPPING_DEFICIT"
    elif "MULTIPLE_CANDIDATE_CROSS_SECTION" in causes or "NON_CURRENT_SERIES" in causes:
        classification = "MODEL_ASSUMPTION_REQUIRED"
        resolution_type = "RESEARCHER_SELECTION_REQUIRED"
    else:
        classification = "NO_ASSUMPTION_NEEDED"
        resolution_type = "OFFICIAL_EVIDENCE_UNIQUE"

    return {
        "direction": prior["direction"],
        "final_classification": classification,
        "resolution_type": resolution_type,
        "cause_codes": sorted(causes),
        "official_observation_section_id": observation_id,
        "official_location_name": location_name,
        "official_location_geometry": geometry,
        "official_location_representation": "PLACE_NAME_PLUS_SECTION_GEOMETRY_NOT_POINT" if location_available else "MISSING",
        "official_observation_flag": prior.get("official_observation_flag", ""),
        "official_direction_semantics": prior.get("official_direction_semantics", ""),
        "series": series,
        "series_available": series_available,
        "series_current": series_available and not non_current,
        "comparison_mapping_usable": mapping_usable,
        "comparison_final_corridor_id": comparison_mapping.get("final_corridor_id", "") if comparison_mapping else "",
        "candidate_directed_edge_ids": candidate_edges,
        "candidate_directed_edge_count": len(candidate_edges),
        "official_observation_section_oneway": normalized_observation.get("oneway", "") if normalized_observation else "",
        "opposing_direction_mapping_missing": opposing_direction_mapping_missing,
        "selected_edge_id": None,
        "position_inferred": False,
        "note": "Official location is a place name plus basic-section geometry, not an edge-level point; no representative edge is selected.",
    }


def primary_cause(items: list[dict[str, Any]], final_class: str) -> str:
    causes = {cause for item in items if item["final_classification"] == final_class for cause in item["cause_codes"]}
    if final_class == "UNRESOLVED":
        order = ("DATA_CONFLICT", "OBSERVATION_MISSING", "LOCATION_MAPPING_MISSING", "OTHER")
    elif final_class == "MODEL_ASSUMPTION_REQUIRED":
        order = ("NON_CURRENT_SERIES", "MULTIPLE_CANDIDATE_CROSS_SECTION")
    else:
        order = ("OFFICIAL_LOCATION_AVAILABLE", "OTHER")
    return next((cause for cause in order if cause in causes), "OTHER")


def summarize(section_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]]) -> dict[str, Any]:
    classification_summary = {}
    for classification in FINAL_CLASSES:
        selected = [row for row in section_rows if row["final_classification"] == classification]
        candidates = [row for row in edge_rows if row["section_final_classification"] == classification]
        classification_summary[classification] = {
            "section_count": len(selected),
            "target_final_unique_edge_count": len({edge for row in selected for edge in split(row["target_final_edge_ids"])}),
            "target_final_section_edge_pair_count": sum(row["target_final_edge_count"] for row in selected),
            "comparison_candidate_unique_edge_count": len({row["candidate_edge_id"] for row in candidates}),
            "comparison_candidate_section_direction_edge_count": len(candidates),
        }
    cause_summary = []
    for cause in CAUSE_CODES:
        section_ids = {
            row["section_id"] for row in section_rows
            if cause in json.loads(row["direction_evidence_json"])["up"]["cause_codes"]
            or cause in json.loads(row["direction_evidence_json"])["down"]["cause_codes"]
        }
        related_edges = [row for row in edge_rows if cause in row["direction_cause_codes"].split(";")]
        cause_summary.append({
            "cause_code": cause,
            "section_count": len(section_ids),
            "comparison_candidate_unique_edge_count": len({row["candidate_edge_id"] for row in related_edges}),
            "comparison_candidate_section_direction_edge_count": len(related_edges),
        })
    return {"classification_summary": classification_summary, "cause_summary": cause_summary}


def run(data_dir: Path = DEFAULT_DATA_DIR, raw_dir: Path = DEFAULT_RAW_DIR) -> dict[str, Any]:
    prior_rows = read_csv(data_dir / "traffic_comparison_cross_section_refinement.csv")
    if Counter(row["original_classification"] for row in prior_rows) != Counter({"UNRESOLVED": 30, "ASSUMPTION_MAY_BE_NEEDED": 2}):
        raise ValueError("expected original scope of 30 unresolved and 2 assumption candidates")
    finals = {row["section_id"]: row for row in read_csv(data_dir / "census_section_final_mapping.csv")}
    normalized = {row["section_id"]: row for row in read_csv(data_dir / "road_census_section_attributes_normalized.csv")}
    edges = {row["edge_id"]: row for row in read_csv(data_dir / "osm_sumo_edge_attributes_normalized.csv")}
    raw_sections = {row["交通調査基本区間番号"]: row for row in read_csv(raw_dir / "kasyo13.csv", "cp932")}

    section_output: list[dict[str, Any]] = []
    edge_output: list[dict[str, Any]] = []
    for prior_row in prior_rows:
        sid = prior_row["section_id"]
        raw_target = raw_sections[sid]
        old_evidence = json.loads(prior_row["direction_evidence_json"])
        direction_items = []
        for direction in ("up", "down"):
            old = old_evidence[direction]
            observation_id = old["official_observation_section_id"]
            comparison = finals.get(observation_id)
            item = classify_direction(
                old, raw_target.get(DIRECTION_FIELDS[direction], "").strip(), comparison,
                normalized.get(observation_id), edges,
            )
            direction_items.append(item)
        direction_classes = {item["final_classification"] for item in direction_items}
        if "UNRESOLVED" in direction_classes:
            final_class = "UNRESOLVED"
        elif "MODEL_ASSUMPTION_REQUIRED" in direction_classes:
            final_class = "MODEL_ASSUMPTION_REQUIRED"
        else:
            final_class = "NO_ASSUMPTION_NEEDED"
        primary = primary_cause(direction_items, final_class)
        target_edges = split(finals[sid]["final_edge_ids"])
        evidence_json = {item["direction"]: item for item in direction_items}
        for item in direction_items:
            for edge_id in item["candidate_directed_edge_ids"]:
                edge = edges[edge_id]
                edge_output.append({
                    "section_id": sid,
                    "direction": item["direction"],
                    "section_final_classification": final_class,
                    "direction_final_classification": item["final_classification"],
                    "direction_cause_codes": ";".join(item["cause_codes"]),
                    "official_observation_section_id": item["official_observation_section_id"],
                    "official_location_name": item["official_location_name"],
                    "comparison_corridor_id": item["comparison_final_corridor_id"],
                    "candidate_edge_id": edge_id,
                    "sumo_from": edge["sumo_from_normalized"],
                    "sumo_to": edge["sumo_to_normalized"],
                    "reverse_edge_id": edge["reverse_edge_id_normalized"],
                    "reverse_edge_status": edge["reverse_edge_status"],
                    "osm_way_id": edge["osm_way_id"],
                    "selected": False,
                    "source_file": edge["sumo_lane_count_source_file"],
                    "extraction_rule_id": "FINAL_CORRIDOR_DIRECTED_EDGE_CANDIDATE_ENUMERATION_V1",
                })
        all_causes = sorted({cause for item in direction_items for cause in item["cause_codes"]})
        candidate_ids = sorted({edge for item in direction_items for edge in item["candidate_directed_edge_ids"]})
        section_output.append({
            "section_id": sid,
            "original_classification": prior_row["original_classification"],
            "previous_refined_classification": prior_row["refined_classification"],
            "final_classification": final_class,
            "resolution_type": direction_items[0]["resolution_type"] if len({item["resolution_type"] for item in direction_items}) == 1 else "MIXED",
            "primary_cause_code": primary,
            "cause_codes": ";".join(all_causes),
            "target_final_corridor_id": finals[sid]["final_corridor_id"],
            "target_final_edge_ids": finals[sid]["final_edge_ids"],
            "target_final_edge_count": len(target_edges),
            "comparison_candidate_edge_ids": ";".join(candidate_ids),
            "comparison_candidate_unique_edge_count": len(candidate_ids),
            "direction_evidence_json": json.dumps(evidence_json, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "representative_edge_selected": False,
            "position_inferred": False,
            "traffic_value_imputed": False,
            "mapping_or_threshold_changed": False,
            "evidence_summary": (
                f"official observation section(s)={sorted({item['official_observation_section_id'] for item in direction_items if item['official_observation_section_id']})}; "
                f"location representation(s)={sorted({item['official_location_representation'] for item in direction_items})}; "
                f"candidate directed edges={len(candidate_ids)}; causes={all_causes}"
            ),
            "classification_rule_id": "TRAFFIC_COMPARISON_CROSS_SECTION_FINAL_REVIEW_V1",
        })

    parts = summarize(section_output, edge_output)
    summary = {
        "schema_version": 1,
        "scope": {
            "original_unresolved_sections": 30,
            "original_assumption_candidate_sections": 2,
            "total_sections": 32,
            "target_final_unique_edge_count": len({edge for row in section_output for edge in split(row["target_final_edge_ids"])}),
            "target_final_section_edge_pair_count": sum(row["target_final_edge_count"] for row in section_output),
            "comparison_candidate_unique_edge_count": len({row["candidate_edge_id"] for row in edge_output}),
            "comparison_candidate_section_direction_edge_count": len(edge_output),
        },
        **parts,
        "separation": {
            "researcher_selection_required_sections": parts["classification_summary"]["MODEL_ASSUMPTION_REQUIRED"]["section_count"],
            "evidence_or_mapping_deficit_sections": parts["classification_summary"]["UNRESOLVED"]["section_count"],
            "official_evidence_unique_sections": parts["classification_summary"]["NO_ASSUMPTION_NEEDED"]["section_count"],
        },
        "rules": {
            "official_location": "kasyo13 observation-place name plus official basic-section GeoJSON; no point coordinate is present in the supplied official files",
            "unique_cross_section": "requires one edge-level official location and sufficient official direction binding; corridor availability alone is insufficient",
            "multiple_candidates": "more than one directed edge in the usable observation-section corridor requires researcher selection",
            "opposing_direction_mapping": "a bidirectional official section needs both SUMO directions; a final corridor containing only one-way edges with no resolved reverse is LOCATION_MAPPING_MISSING, not an asserted source-data conflict",
            "representative_edge_selection": False,
            "position_inference": False,
            "traffic_imputation": False,
            "mapping_or_threshold_change": False,
        },
        "provenance": {
            "official_section_file": "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/kasyo13.csv",
            "official_series_file": "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/zkntrf13.csv",
            "official_geometry_directory": "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/webmap_tiles",
            "final_mapping_file": "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/census_section_final_mapping.csv",
            "sumo_edge_file": "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/osm_sumo_edge_attributes_normalized.csv",
        },
    }
    write_csv(data_dir / "traffic_comparison_cross_section_final_review.csv", section_output)
    write_csv(data_dir / "traffic_comparison_cross_section_final_review_edge_evidence.csv", edge_output)
    write_csv(data_dir / "traffic_comparison_cross_section_final_review_summary.csv", [
        {"final_classification": key, **value} for key, value in parts["classification_summary"].items()
    ])
    write_csv(data_dir / "traffic_comparison_cross_section_final_review_cause_summary.csv", parts["cause_summary"])
    (data_dir / "traffic_comparison_cross_section_final_review_summary.json").write_text(
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
