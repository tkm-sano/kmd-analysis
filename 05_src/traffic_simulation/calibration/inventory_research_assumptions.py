#!/usr/bin/env python3
"""Inventory where downstream work may require a research assumption.

This audit uses only normalized official Road Census fields, explicit OSM
tags, realized SUMO values/provenance, and observation metadata.  It does not
impute, reconcile, overwrite, or alter a matching threshold.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
TARGETS = ("LANE_DIRECTION_ALLOCATION", "SPEED_VALUE_SELECTION", "TRAFFIC_COMPARISON_CROSS_SECTION")
CLASSIFICATIONS = ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED")
CLASS_RANK = {value: rank for rank, value in enumerate(CLASSIFICATIONS)}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def split_edges(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def as_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def result(
    target: str,
    final: dict[str, str],
    classification: str,
    issue_types: Iterable[str],
    evidence: Iterable[str],
    source_fields: Iterable[str],
    rule_id: str,
    edge_statuses: dict[str, str] | None = None,
) -> dict[str, Any]:
    edges = split_edges(final["final_edge_ids"])
    edge_statuses = edge_statuses or {edge_id: classification for edge_id in edges}
    return {
        "section_id": final["section_id"],
        "target": target,
        "classification": classification,
        "issue_types": ";".join(sorted(set(issue_types))),
        "edge_count": len(edges),
        "edge_ids": ";".join(edges),
        "no_assumption_needed_edge_count": sum(value == "NO_ASSUMPTION_NEEDED" for value in edge_statuses.values()),
        "assumption_may_be_needed_edge_count": sum(value == "ASSUMPTION_MAY_BE_NEEDED" for value in edge_statuses.values()),
        "unresolved_edge_count": sum(value == "UNRESOLVED" for value in edge_statuses.values()),
        "edge_classifications_json": json.dumps(edge_statuses, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "evidence_summary": " | ".join(evidence),
        "source_fields": ";".join(sorted(set(source_fields))),
        "classification_rule_id": rule_id,
        "data_changed": False,
    }


def worst(statuses: Iterable[str]) -> str:
    return max(statuses, key=CLASS_RANK.get)


def classify_lane_direction(
    final: dict[str, str], census: dict[str, str], edge_rows: list[dict[str, str]]
) -> dict[str, Any]:
    issues: list[str] = []
    evidence: list[str] = []
    fields = ["lane_count", "lane_direction_scope", "oneway", "osm_lanes", "osm_lanes_forward",
              "osm_lanes_backward", "osm_lanes_both_ways", "sumo_lane_count"]
    if not parse_bool(final["usable_for_lane_projection"]):
        return result(TARGETS[0], final, "UNRESOLVED", ["MAPPING_NOT_USABLE"],
                      ["final mapping disables lane projection"], ["usable_for_lane_projection"],
                      "ASSUMP_LANE_MAPPING_USABILITY_V1")
    official_lanes = as_positive_int(census.get("lane_count", ""))
    scope = census.get("lane_direction_scope", "")
    if official_lanes is None or scope not in {"BOTH_DIRECTIONS_TOTAL", "PERMITTED_ONEWAY_DIRECTION_TOTAL"}:
        return result(TARGETS[0], final, "UNRESOLVED", ["OFFICIAL_LANE_SEMANTICS_MISSING"],
                      [f"lane_count={census.get('lane_count', '')!r}; lane_direction_scope={scope!r}"], fields,
                      "ASSUMP_LANE_OFFICIAL_SEMANTICS_V1")
    if not edge_rows:
        return result(TARGETS[0], final, "UNRESOLVED", ["SUMO_EDGE_ATTRIBUTES_MISSING"],
                      ["no normalized edge rows"], fields, "ASSUMP_LANE_EDGE_PRESENCE_V1")

    if scope == "PERMITTED_ONEWAY_DIRECTION_TOTAL":
        statuses = []
        edge_statuses: dict[str, str] = {}
        for edge in edge_rows:
            actual = as_positive_int(edge.get("sumo_lane_count_normalized", ""))
            osm_oneway = edge.get("osm_oneway_normalized", "")
            if actual is None:
                statuses.append("UNRESOLVED")
                edge_statuses[edge["edge_id"]] = "UNRESOLVED"
                issues.append("SUMO_LANE_COUNT_MISSING")
            elif osm_oneway in {"no"}:
                statuses.append("UNRESOLVED")
                edge_statuses[edge["edge_id"]] = "UNRESOLVED"
                issues.append("OFFICIAL_OSM_ONEWAY_CONFLICT")
            else:
                statuses.append("NO_ASSUMPTION_NEEDED")
                edge_statuses[edge["edge_id"]] = "NO_ASSUMPTION_NEEDED"
        classification = worst(statuses)
        evidence.append(
            f"official one-way scope assigns all {official_lanes} representative lanes to the permitted Census direction; "
            f"SUMO edge lane counts are present for {sum(actual is not None for actual in (as_positive_int(e.get('sumo_lane_count_normalized', '')) for e in edge_rows))}/{len(edge_rows)} edges"
        )
        if classification == "NO_ASSUMPTION_NEEDED":
            issues.append("OFFICIAL_ONEWAY_NO_DIRECTION_SPLIT")
        return result(TARGETS[0], final, classification, issues, evidence, fields,
                      "ASSUMP_LANE_OFFICIAL_ONEWAY_V1", edge_statuses)

    statuses: list[str] = []
    explicit_count = 0
    implicit_count = 0
    conflict_count = 0
    edge_statuses: dict[str, str] = {}
    for edge in edge_rows:
        total = as_positive_int(edge.get("osm_lanes_normalized", ""))
        forward = as_positive_int(edge.get("osm_lanes_forward_normalized", ""))
        backward = as_positive_int(edge.get("osm_lanes_backward_normalized", ""))
        both = as_positive_int(edge.get("osm_lanes_both_ways_normalized", ""))
        actual = as_positive_int(edge.get("sumo_lane_count_normalized", ""))
        if actual is None:
            statuses.append("UNRESOLVED")
            edge_statuses[edge["edge_id"]] = "UNRESOLVED"
            conflict_count += 1
            continue
        if total is not None and forward is not None and backward is not None:
            tagged_sum = forward + backward + (both or 0)
            if tagged_sum != total or total != official_lanes or actual not in {forward, backward, both or -1}:
                statuses.append("UNRESOLVED")
                edge_statuses[edge["edge_id"]] = "UNRESOLVED"
                conflict_count += 1
            else:
                statuses.append("NO_ASSUMPTION_NEEDED")
                edge_statuses[edge["edge_id"]] = "NO_ASSUMPTION_NEEDED"
                explicit_count += 1
        else:
            statuses.append("ASSUMPTION_MAY_BE_NEEDED")
            edge_statuses[edge["edge_id"]] = "ASSUMPTION_MAY_BE_NEEDED"
            implicit_count += 1
    classification = worst(statuses)
    if conflict_count:
        issues.append("DIRECTIONAL_LANE_EVIDENCE_CONFLICT")
    if implicit_count:
        issues.append("DIRECTIONAL_LANE_TAGS_INCOMPLETE")
    if explicit_count:
        issues.append("EXPLICIT_DIRECTIONAL_LANES_AVAILABLE")
    evidence.append(
        f"official total lanes={official_lanes}; explicit complete/consistent edges={explicit_count}; "
        f"incomplete directional tags={implicit_count}; conflicting/missing actual={conflict_count}"
    )
    return result(TARGETS[0], final, classification, issues, evidence, fields,
                  "ASSUMP_LANE_BIDIRECTIONAL_EXPLICIT_SPLIT_V1", edge_statuses)


def expected_sumo_speed(kmh: str) -> str | None:
    try:
        value = float(kmh)
    except (TypeError, ValueError):
        return None
    return f"{value / 3.6:.2f}"


def classify_speed(final: dict[str, str], edge_rows: list[dict[str, str]]) -> dict[str, Any]:
    fields = ["osm_maxspeed", "sumo_speed_mps", "sumo_speed_source_type", "sumo_speed_extraction_rule_id"]
    if not final["final_edge_ids"] or not (
        parse_bool(final["usable_for_lane_projection"]) or parse_bool(final["usable_for_traffic_assignment"])
    ):
        return result(TARGETS[1], final, "UNRESOLVED", ["MAPPING_NOT_USABLE"],
                      ["final mapping is excluded from downstream use"], fields,
                      "ASSUMP_SPEED_MAPPING_USABILITY_V1")
    statuses: list[str] = []
    explicit = defaults = conflicts = 0
    edge_statuses: dict[str, str] = {}
    for edge in edge_rows:
        source_type = edge.get("sumo_speed_source_type", "")
        osm_status = edge.get("osm_maxspeed_missing_status", "")
        actual_values = [item for item in edge.get("sumo_speed_mps_normalized", "").split(";") if item]
        if not actual_values:
            statuses.append("UNRESOLVED"); edge_statuses[edge["edge_id"]] = "UNRESOLVED"; conflicts += 1
        elif source_type == "SUMO_TYPE_DEFAULT" and osm_status != "PRESENT":
            statuses.append("ASSUMPTION_MAY_BE_NEEDED"); edge_statuses[edge["edge_id"]] = "ASSUMPTION_MAY_BE_NEEDED"; defaults += 1
        elif source_type == "OSM_EXPLICIT_TRANSFORMED" and osm_status == "PRESENT":
            expected = expected_sumo_speed(edge.get("osm_maxspeed_normalized", ""))
            if expected is not None and set(actual_values) == {expected}:
                statuses.append("NO_ASSUMPTION_NEEDED"); edge_statuses[edge["edge_id"]] = "NO_ASSUMPTION_NEEDED"; explicit += 1
            else:
                statuses.append("UNRESOLVED"); edge_statuses[edge["edge_id"]] = "UNRESOLVED"; conflicts += 1
        else:
            statuses.append("UNRESOLVED"); edge_statuses[edge["edge_id"]] = "UNRESOLVED"; conflicts += 1
    classification = worst(statuses)
    issues = []
    if explicit: issues.append("OSM_EXPLICIT_SPEED_TRANSFORMED")
    if defaults: issues.append("SUMO_TYPE_DEFAULT_SPEED")
    if conflicts: issues.append("SPEED_PROVENANCE_OR_VALUE_CONFLICT")
    evidence = [f"OSM-explicit matching edges={explicit}; SUMO-default edges={defaults}; unresolved/conflicting edges={conflicts}"]
    return result(TARGETS[1], final, classification, issues, evidence, fields,
                  "ASSUMP_SPEED_EXPLICIT_VS_DEFAULT_V1", edge_statuses)


def observed_counts_available(rows: list[dict[str, str]]) -> bool:
    """Whether the direction has any recorded comparison-period count.

    The audit is about spatial comparison cross-sections, not 24-hour temporal
    completion.  Blank vehicle classes in hours outside a 12-hour survey must
    therefore not invalidate an otherwise explicit observation cross-section.
    """
    return any(
        any(row.get(field, "").strip() for field in (
            "small_vehicle_count", "large_vehicle_count", "total_vehicle_count"
        ))
        and as_positive_int(row.get("total_vehicle_count", "")) is not None
        for row in rows
    )


def classify_traffic_cross_section(
    final: dict[str, str], census: dict[str, str],
    hourly: dict[str, list[dict[str, str]]], final_by_section: dict[str, dict[str, str]],
) -> dict[str, Any]:
    fields = ["up_observation_section_id_raw", "down_observation_section_id_raw",
              "up_observation_flag_raw", "down_observation_flag_raw", "direction", "observed counts"]
    if not parse_bool(final["usable_for_traffic_assignment"]):
        return result(TARGETS[2], final, "UNRESOLVED", ["MAPPING_NOT_USABLE"],
                      ["final mapping disables traffic assignment"], fields,
                      "ASSUMP_TRAFFIC_MAPPING_USABILITY_V1")
    statuses: list[str] = []
    issues: list[str] = []
    evidence: list[str] = []
    for direction, id_field, flag_field in (
        ("up", "up_observation_section_id_raw", "up_observation_flag_raw"),
        ("down", "down_observation_section_id_raw", "down_observation_flag_raw"),
    ):
        observation_id = census.get(id_field, "").strip()
        official_flag = census.get(flag_field, "").strip()
        direction_rows = [row for row in hourly.get(observation_id, []) if row.get("direction") == direction]
        mapped = final_by_section.get(observation_id)
        if not observation_id:
            statuses.append("UNRESOLVED"); issues.append("OFFICIAL_COMPARISON_SECTION_MISSING")
        elif mapped is None or not parse_bool(mapped.get("usable_for_traffic_assignment", "")):
            statuses.append("UNRESOLVED"); issues.append("COMPARISON_SECTION_MAPPING_UNAVAILABLE")
        elif not observed_counts_available(direction_rows):
            statuses.append("UNRESOLVED"); issues.append("COMPARISON_SECTION_COUNTS_UNAVAILABLE")
        elif official_flag == "1" and all(row.get("observation_flag") == "1" for row in direction_rows):
            statuses.append("NO_ASSUMPTION_NEEDED")
        elif official_flag == "2" or any(row.get("observation_flag") == "2" for row in direction_rows):
            statuses.append("ASSUMPTION_MAY_BE_NEEDED"); issues.append("NONCURRENT_OR_NONOBSERVED_SERIES")
        else:
            statuses.append("UNRESOLVED"); issues.append("OBSERVATION_FLAG_UNREGISTERED_OR_CONFLICTING")
        evidence.append(
            f"{direction}: official_section={observation_id or 'MISSING'}, flag={official_flag or 'MISSING'}, "
            f"hourly_rows={len(direction_rows)}, mapped={'yes' if mapped else 'no'}"
        )
    return result(TARGETS[2], final, worst(statuses), issues or ["OFFICIAL_COMPARISON_SECTION_AVAILABLE"],
                  evidence, fields, "ASSUMP_TRAFFIC_OFFICIAL_COMPARISON_SECTION_V1")


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    process_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    for target in TARGETS:
        selected = [row for row in rows if row["target"] == target]
        all_edges = {edge for row in selected for edge in split_edges(row["edge_ids"])}
        summary: dict[str, Any] = {"target": target, "total_sections": len(selected), "total_unique_edges": len(all_edges)}
        for classification in CLASSIFICATIONS:
            classified = [row for row in selected if row["classification"] == classification]
            prefix = classification.lower()
            summary[f"{prefix}_sections"] = len(classified)
            edge_pairs = {
                (row["section_id"], edge_id)
                for row in selected
                for edge_id, edge_class in json.loads(row["edge_classifications_json"]).items()
                if edge_class == classification
            }
            summary[f"{prefix}_unique_edges"] = len({edge_id for _, edge_id in edge_pairs})
            summary[f"{prefix}_section_edge_pairs"] = len(edge_pairs)
        process_rows.append(summary)

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for issue in filter(None, row["issue_types"].split(";")):
            grouped[(row["target"], issue, row["classification"])].append(row)
    for (target, issue, classification), selected in sorted(grouped.items()):
        issue_rows.append({
            "target": target,
            "issue_type": issue,
            "classification": classification,
            "section_count": len({row["section_id"] for row in selected}),
            "unique_edge_count": len({edge for row in selected for edge in split_edges(row["edge_ids"])}),
            "section_ids": ";".join(sorted({row["section_id"] for row in selected})),
        })
    payload = {
        "schema_version": 1,
        "scope": {"road_census_sections": 66, "targets_per_section": 3, "inventory_rows": len(rows)},
        "classifications": list(CLASSIFICATIONS),
        "counting_note": "Sections use their worst constituent status. Edges are independently classified in edge_classifications_json and deduplicated within each target/classification; a reused edge can occur in more than one classification when its Census-section context differs.",
        "evidence_policy": "Official normalized Road Census fields, explicit OSM values, realized SUMO values/provenance, and observation metadata only. No imputation or value/threshold changes.",
        "calibration_validation_split": {
            "status": "UNDEFINED_RESEARCH_DESIGN_ITEM",
            "counted_in_inventory": False,
            "note": "Calibration/Validation candidate assignment and holdout policy require a separate research design decision and are intentionally not quantified here.",
        },
        "target_summary": process_rows,
        "issue_summary": issue_rows,
    }
    return process_rows, issue_rows, payload


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("no rows to write")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(input_dir: Path = DEFAULT_INPUT_DIR, output_dir: Path | None = None) -> dict[str, Any]:
    output_dir = output_dir or input_dir
    finals = read_csv(input_dir / "census_section_final_mapping.csv")
    census = {row["section_id"]: row for row in read_csv(input_dir / "road_census_section_attributes_normalized.csv")}
    edges = {row["edge_id"]: row for row in read_csv(input_dir / "osm_sumo_edge_attributes_normalized.csv")}
    hourly: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(input_dir / "road_census_hourly_traffic.csv"):
        hourly[row["census_section_id"]].append(row)
    final_by_section = {row["section_id"]: row for row in finals}
    if len(finals) != 66 or len(final_by_section) != 66:
        raise ValueError(f"expected 66 unique final sections, got {len(finals)} rows/{len(final_by_section)} IDs")
    missing_census = set(final_by_section) - set(census)
    if missing_census:
        raise ValueError(f"normalized Census attributes missing: {sorted(missing_census)}")
    rows: list[dict[str, Any]] = []
    for final in finals:
        edge_ids = split_edges(final["final_edge_ids"])
        missing_edges = set(edge_ids) - set(edges)
        if missing_edges:
            raise ValueError(f"normalized edge attributes missing for {final['section_id']}: {sorted(missing_edges)}")
        selected_edges = [edges[edge_id] for edge_id in edge_ids]
        rows.append(classify_lane_direction(final, census[final["section_id"]], selected_edges))
        rows.append(classify_speed(final, selected_edges))
        rows.append(classify_traffic_cross_section(final, census[final["section_id"]], hourly, final_by_section))
    process_rows, issue_rows, payload = summarize(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "assumption_inventory.csv", rows)
    write_csv(output_dir / "assumption_inventory_summary.csv", process_rows)
    write_csv(output_dir / "assumption_inventory_issue_summary.csv", issue_rows)
    (output_dir / "assumption_inventory_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.input_dir, args.output_dir)["target_summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
