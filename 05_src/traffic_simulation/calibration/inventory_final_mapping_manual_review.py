#!/usr/bin/env python3
"""Inventory downstream review needs from the authoritative final mapping.

This audit is deliberately read-only with respect to Census, OSM, and SUMO
values.  It records conflicts and missing evidence; it does not complete lane
counts, assign traffic, or change matching thresholds.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from traffic_simulation.calibration.road_census_sumo_pipeline import (
    DEFAULT_CONFIG,
    load_config,
    load_osm_way_tags,
    normalize_route_ref,
    write_csv,
)
from traffic_simulation.paths import REPOSITORY_ROOT


PROCESSES = (
    "LANE_PROJECTION",
    "ATTRIBUTE_CHECK",
    "FINAL_MAPPING_NOTES",
    "TRAFFIC_ASSIGNMENT",
    "CALIBRATION_VALIDATION_SELECTION",
)
CLASS_RANK = {"AUTO_RESOLVED": 0, "REVIEW_REQUIRED": 1, "UNRESOLVED": 2}
OUTPUT_STEM = "manual_review_inventory"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def split_edge_ids(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def as_int(value: str | None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def simple_maxspeed_kmh(value: str) -> float | None:
    """Return a simple numeric OSM maxspeed, leaving compound values for review."""
    text = value.strip().lower()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:km/?h)?", text)
    return float(match.group(1)) if match else None


def survey_date_is_specific(value: str) -> bool:
    text = value.strip()
    return bool(re.fullmatch(r"\d{8}", text)) and not text.endswith("00")


def passenger_allowed(lane: dict[str, str]) -> bool:
    allow = set(lane.get("allow", "").split())
    disallow = set(lane.get("disallow", "").split())
    return (not allow or "passenger" in allow) and "passenger" not in disallow


def load_final_net_lanes(net_path: Path, wanted_edge_ids: set[str]) -> dict[str, list[dict[str, str]]]:
    found: dict[str, list[dict[str, str]]] = {}
    for _, element in ET.iterparse(net_path, events=("end",)):
        if element.tag != "edge":
            continue
        edge_id = element.get("id", "")
        if edge_id in wanted_edge_ids:
            found[edge_id] = [dict(lane.attrib) for lane in element.findall("lane")]
        element.clear()
    return found


@dataclass
class Issue:
    process: str
    section_id: str
    issue_type: str
    classification: str
    edge_ids: set[str] = field(default_factory=set)
    evidence: list[str] = field(default_factory=list)
    source_fields: set[str] = field(default_factory=set)


class Inventory:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str, str], Issue] = {}

    def add(
        self,
        process: str,
        section_id: str,
        issue_type: str,
        classification: str,
        edge_ids: Iterable[str],
        evidence: str,
        source_fields: Iterable[str],
    ) -> None:
        key = (process, section_id, issue_type, classification)
        issue = self._items.setdefault(
            key, Issue(process, section_id, issue_type, classification)
        )
        issue.edge_ids.update(edge_ids)
        if evidence and evidence not in issue.evidence:
            issue.evidence.append(evidence)
        issue.source_fields.update(source_fields)

    def has_process(self, process: str, section_id: str) -> bool:
        return any(key[0] == process and key[1] == section_id for key in self._items)

    def rows(self) -> list[dict[str, Any]]:
        output = []
        for issue in sorted(
            self._items.values(),
            key=lambda x: (PROCESSES.index(x.process), x.section_id, x.issue_type, x.classification),
        ):
            edges = sorted(issue.edge_ids)
            output.append({
                "process": issue.process,
                "section_id": issue.section_id,
                "issue_type": issue.issue_type,
                "classification": issue.classification,
                "affected_edge_count": len(edges),
                "affected_edge_ids": ";".join(edges),
                "evidence": " | ".join(issue.evidence),
                "source_fields": ";".join(sorted(issue.source_fields)),
                "data_changed": False,
            })
        return output


def merged_way_tags(edge: dict[str, str], osm_tags: dict[str, dict[str, str]]) -> dict[str, str]:
    tags: dict[str, str] = {}
    for way_id in re.split(r"[ ;,]+", edge.get("osm_way_ids", "")):
        if way_id:
            tags.update(osm_tags.get(way_id, {}))
    return tags


def inventory_lane_projection(
    inv: Inventory,
    final: dict[str, str],
    section: dict[str, str],
    edges: dict[str, dict[str, str]],
) -> None:
    sid = final["section_id"]
    edge_ids = split_edge_ids(final["final_edge_ids"])
    if not parse_bool(final["usable_for_lane_projection"]):
        inv.add("LANE_PROJECTION", sid, "MAPPING_NOT_USABLE", "UNRESOLVED", edge_ids,
                f"final_confidence={final['final_confidence']}; lane projection is explicitly disabled",
                ["final_confidence", "usable_for_lane_projection"])
        return
    total = as_int(section.get("total_lanes"))
    if total is None or total <= 0:
        inv.add("LANE_PROJECTION", sid, "CENSUS_LANE_COUNT_MISSING", "UNRESOLVED", edge_ids,
                f"total_lanes={section.get('total_lanes', '')!r}", ["total_lanes"])
        return
    census_oneway = section.get("oneway_flag") == "1"
    if not census_oneway and total % 2:
        inv.add("LANE_PROJECTION", sid, "DIRECTIONAL_LANE_SPLIT_REQUIRED", "REVIEW_REQUIRED", edge_ids,
                f"two-way Census section has odd total_lanes={total}", ["total_lanes", "oneway_flag"])
        directional_expected = None
    else:
        directional_expected = total if census_oneway else total // 2

    for edge_id in edge_ids:
        edge = edges[edge_id]
        explicit = as_int(edge.get("lanes"))
        sumo_count = as_int(edge.get("sumo_lane_count"))
        osm_oneway = edge.get("oneway", "").lower() in {"yes", "1", "true", "-1"}
        if explicit is None:
            inv.add("LANE_PROJECTION", sid, "CENSUS_LANE_FALLBACK_AVAILABLE", "AUTO_RESOLVED", [edge_id],
                    f"edge {edge_id}: OSM lanes missing; final mapping and Census lanes are available",
                    ["lanes", "total_lanes", "final_confidence"])
        else:
            comparable_census = directional_expected if osm_oneway else total
            if comparable_census is not None and explicit != comparable_census:
                inv.add("LANE_PROJECTION", sid, "LANE_CENSUS_OSM_CONFLICT", "REVIEW_REQUIRED", [edge_id],
                        f"edge {edge_id}: Census comparable lanes={comparable_census}, OSM lanes={explicit}, OSM oneway={osm_oneway}",
                        ["total_lanes", "oneway_flag", "lanes", "oneway"])
            else:
                inv.add("LANE_PROJECTION", sid, "LANE_CENSUS_OSM_CONSISTENT", "AUTO_RESOLVED", [edge_id],
                        f"edge {edge_id}: comparable Census/OSM lanes={explicit}",
                        ["total_lanes", "oneway_flag", "lanes", "oneway"])
        if directional_expected is not None and sumo_count != directional_expected:
            inv.add("LANE_PROJECTION", sid, "LANE_CENSUS_SUMO_CONFLICT", "REVIEW_REQUIRED", [edge_id],
                    f"edge {edge_id}: expected directional Census lanes={directional_expected}, SUMO lanes={sumo_count}",
                    ["total_lanes", "oneway_flag", "sumo_lane_count"])


def inventory_attributes(
    inv: Inventory,
    final: dict[str, str],
    section: dict[str, str],
    edges: dict[str, dict[str, str]],
    tags_by_edge: dict[str, dict[str, str]],
    net_lanes: dict[str, list[dict[str, str]]],
) -> None:
    sid = final["section_id"]
    edge_ids = split_edge_ids(final["final_edge_ids"])
    if not edge_ids:
        inv.add("ATTRIBUTE_CHECK", sid, "MAPPING_UNSETTLED", "UNRESOLVED", [],
                "final_edge_ids is empty", ["final_edge_ids"])
        return
    base_classes = {edges[e]["highway"].removesuffix("_link") for e in edge_ids if edges[e]["highway"]}
    if len(base_classes) > 1:
        inv.add("ATTRIBUTE_CHECK", sid, "HIGHWAY_CLASS_MIXED", "REVIEW_REQUIRED", edge_ids,
                f"normalized highway classes={','.join(sorted(base_classes))}", ["highway"])
    weak_edges = [e for e in edge_ids if edges[e]["highway"].removesuffix("_link") in {"service", "residential", "unclassified"}]
    if weak_edges:
        inv.add("ATTRIBUTE_CHECK", sid, "HIGHWAY_CLASS_NON_ARTERIAL", "REVIEW_REQUIRED", weak_edges,
                "service/residential/unclassified constituent remains in the final corridor", ["highway"])
    is_expressway = section.get("road_type_code") == "2"
    class_conflicts = [e for e in edge_ids if (edges[e]["highway"].removesuffix("_link") == "motorway") != is_expressway]
    if class_conflicts:
        inv.add("ATTRIBUTE_CHECK", sid, "ROAD_TYPE_HIGHWAY_CONFLICT", "REVIEW_REQUIRED", class_conflicts,
                f"Census road_type_code={section.get('road_type_code')} conflicts with motorway/non-motorway class",
                ["road_type_code", "highway"])

    census_refs = normalize_route_ref(section.get("route_number", ""))
    missing_ref: list[str] = []
    conflicting_ref: list[str] = []
    for edge_id in edge_ids:
        edge_refs = normalize_route_ref(edges[edge_id].get("ref", ""))
        if not edge_refs:
            missing_ref.append(edge_id)
        elif census_refs and not census_refs.intersection(edge_refs):
            conflicting_ref.append(edge_id)
    if missing_ref:
        inv.add("ATTRIBUTE_CHECK", sid, "ROUTE_REF_MISSING", "REVIEW_REQUIRED", missing_ref,
                f"{len(missing_ref)} final edges have no OSM ref", ["route_number", "ref"])
    if conflicting_ref:
        inv.add("ATTRIBUTE_CHECK", sid, "ROUTE_REF_CONFLICT", "REVIEW_REQUIRED", conflicting_ref,
                f"Census route_number={section.get('route_number')}; {len(conflicting_ref)} edges carry a different ref",
                ["route_number", "ref", "review_reason_code"])

    for edge_id in edge_ids:
        tags = tags_by_edge[edge_id]
        lanes = net_lanes.get(edge_id, [])
        maxspeed = tags.get("maxspeed", "").strip()
        if not maxspeed:
            inv.add("ATTRIBUTE_CHECK", sid, "SPEED_OSM_MISSING_SUMO_DEFAULT", "AUTO_RESOLVED", [edge_id],
                    f"edge {edge_id}: no OSM maxspeed; SUMO network speed retained", ["maxspeed", "SUMO lane speed"])
        else:
            parsed = simple_maxspeed_kmh(maxspeed)
            if parsed is None:
                inv.add("ATTRIBUTE_CHECK", sid, "SPEED_VALUE_AMBIGUOUS", "REVIEW_REQUIRED", [edge_id],
                        f"edge {edge_id}: OSM maxspeed={maxspeed!r} is compound/non-numeric", ["maxspeed"])
            else:
                speeds = {round(float(lane["speed"]) * 3.6, 3) for lane in lanes if lane.get("speed")}
                if any(abs(speed - parsed) > 1.0 for speed in speeds):
                    inv.add("ATTRIBUTE_CHECK", sid, "SPEED_OSM_SUMO_CONFLICT", "REVIEW_REQUIRED", [edge_id],
                            f"edge {edge_id}: OSM={parsed:g} km/h, SUMO={sorted(speeds)} km/h", ["maxspeed", "SUMO lane speed"])
        restricted = any(tags.get(key, "").lower() in {"no", "private"}
                         for key in ("access", "vehicle", "motor_vehicle", "motorcar"))
        allowed = [passenger_allowed(lane) for lane in lanes]
        if allowed and any(allowed) != all(allowed):
            inv.add("ATTRIBUTE_CHECK", sid, "ACCESS_LANE_LEVEL_MIXED", "REVIEW_REQUIRED", [edge_id],
                    f"edge {edge_id}: passenger permission differs by SUMO lane", ["SUMO allow", "SUMO disallow"])
        elif allowed and restricted == all(allowed):
            inv.add("ATTRIBUTE_CHECK", sid, "ACCESS_OSM_SUMO_CONFLICT", "REVIEW_REQUIRED", [edge_id],
                    f"edge {edge_id}: OSM restricted={restricted}, SUMO passenger_allowed={all(allowed)}",
                    ["access", "vehicle", "motor_vehicle", "motorcar", "SUMO allow", "SUMO disallow"])


def traffic_quality(rows: list[dict[str, str]]) -> dict[str, bool]:
    return {
        "counts_missing": any(
            not row.get("small_vehicle_count", "").strip()
            or not row.get("large_vehicle_count", "").strip()
            for row in rows
        ) or (bool(rows) and all(as_int(row.get("total_vehicle_count")) == 0 for row in rows)),
        "nonobserved": bool(rows) and any(row.get("observation_flag") != "1" for row in rows),
        "date_nonspecific": bool(rows) and any(not survey_date_is_specific(row.get("survey_date", "")) for row in rows),
        "weather_missing": bool(rows) and any(not row.get("weather_code", "").strip() for row in rows),
        "direction_metadata_missing": bool(rows) and set(row.get("direction") for row in rows).issubset({"up", "down"}),
    }


def inventory_mapping_notes(inv: Inventory, final: dict[str, str]) -> None:
    sid = final["section_id"]
    edge_ids = split_edge_ids(final["final_edge_ids"])
    if not edge_ids:
        inv.add("FINAL_MAPPING_NOTES", sid, "MAPPING_UNSETTLED", "UNRESOLVED", [],
                "final corridor/edge sequence is absent", ["final_corridor_id", "final_edge_ids"])
    elif not (parse_bool(final["usable_for_lane_projection"]) and parse_bool(final["usable_for_traffic_assignment"])):
        inv.add("FINAL_MAPPING_NOTES", sid, "FINAL_MAPPING_DOWNSTREAM_EXCLUDED", "UNRESOLVED", edge_ids,
                f"confidence={final['final_confidence']}; downstream usability flags are false",
                ["final_confidence", "usable_for_lane_projection", "usable_for_traffic_assignment"])
    elif final["decision_origin"] == "MANUAL_CONFIRMED":
        inv.add("FINAL_MAPPING_NOTES", sid, "MANUAL_DECISION_RECORDED", "AUTO_RESOLVED", edge_ids,
                f"review_reason_code={final['review_reason_code']}; final decision is already recorded",
                ["decision_origin", "review_reason_code", "manual_reviewed"])
    elif final["final_confidence"] == "medium":
        inv.add("FINAL_MAPPING_NOTES", sid, "FINAL_MEDIUM_ACCEPTED_BY_POLICY", "AUTO_RESOLVED", edge_ids,
                "authoritative final mapping explicitly marks this Medium corridor usable", ["final_confidence", "decision_origin"])
    else:
        inv.add("FINAL_MAPPING_NOTES", sid, "NO_FINAL_MAPPING_CAUTION", "AUTO_RESOLVED", edge_ids,
                "authoritative AUTO_HIGH mapping has downstream usability enabled", ["final_confidence", "decision_origin"])


def inventory_traffic(
    inv: Inventory, final: dict[str, str], hourly_rows: list[dict[str, str]]
) -> None:
    sid = final["section_id"]
    edge_ids = split_edge_ids(final["final_edge_ids"])
    if not parse_bool(final["usable_for_traffic_assignment"]):
        inv.add("TRAFFIC_ASSIGNMENT", sid, "MAPPING_NOT_USABLE", "UNRESOLVED", edge_ids,
                "final mapping explicitly disables traffic assignment", ["usable_for_traffic_assignment"])
    if not hourly_rows:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "TRAFFIC_SERIES_MISSING", "UNRESOLVED", edge_ids,
                "no normalized hourly traffic rows exist for this section", ["road_census_hourly_traffic.csv"])
        return
    quality = traffic_quality(hourly_rows)
    if quality["counts_missing"]:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "TRAFFIC_COUNTS_MISSING", "UNRESOLVED", edge_ids,
                "small/large counts are missing and the normalized total is zero", ["small_vehicle_count", "large_vehicle_count", "total_vehicle_count"])
    if quality["nonobserved"]:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "OBSERVATION_NONOBSERVED", "REVIEW_REQUIRED", edge_ids,
                "observation_flag includes a value other than 1", ["observation_flag"])
    if quality["date_nonspecific"]:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "OBSERVATION_DATE_NONSPECIFIC", "REVIEW_REQUIRED", edge_ids,
                "survey_date is blank or uses day 00", ["survey_date"])
    if quality["weather_missing"]:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "OBSERVATION_WEATHER_MISSING", "REVIEW_REQUIRED", edge_ids,
                "weather_code is blank", ["weather_code"])
    if quality["direction_metadata_missing"]:
        inv.add("TRAFFIC_ASSIGNMENT", sid, "TRAFFIC_DIRECTION_UNKNOWN", "REVIEW_REQUIRED", edge_ids,
                "up/down series exist, but final mapping has no Census-to-SUMO direction field", ["direction", "final_edge_ids"])


def inventory_calibration_validation(
    inv: Inventory, final: dict[str, str], hourly_rows: list[dict[str, str]]
) -> None:
    sid = final["section_id"]
    edge_ids = split_edge_ids(final["final_edge_ids"])
    if not parse_bool(final["usable_for_traffic_assignment"]):
        inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_MAPPING_NOT_USABLE", "UNRESOLVED", edge_ids,
                "traffic assignment is disabled by final mapping", ["usable_for_traffic_assignment"])
        return
    if not hourly_rows:
        inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_OBSERVATION_MISSING", "UNRESOLVED", edge_ids,
                "no hourly observation series is available", ["road_census_hourly_traffic.csv"])
        return
    quality = traffic_quality(hourly_rows)
    if quality["counts_missing"]:
        inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_COUNTS_MISSING", "UNRESOLVED", edge_ids,
                "normalized observed counts are incomplete/zero", ["small_vehicle_count", "large_vehicle_count", "total_vehicle_count"])
        return
    if quality["nonobserved"]:
        inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_NOT_DIRECTLY_OBSERVED", "UNRESOLVED", edge_ids,
                "observation_flag is not direct observation (1)", ["observation_flag"])
        return
    if quality["date_nonspecific"]:
        inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_DATE_REVIEW", "REVIEW_REQUIRED", edge_ids,
                "survey date has day 00 and needs provenance review", ["survey_date"])
    inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CANDIDATE_DIRECTION_REVIEW", "REVIEW_REQUIRED", edge_ids,
            "candidate has no explicit Census up/down to SUMO edge-direction mapping", ["direction", "final_edge_ids"])
    inv.add("CALIBRATION_VALIDATION_SELECTION", sid, "CALIBRATION_VALIDATION_SPLIT_REQUIRED", "REVIEW_REQUIRED", edge_ids,
            "eligible observation has not been assigned to calibration or validation holdout", ["observation_flag"])


def summarize(
    inventory_rows: list[dict[str, Any]],
    final_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    final_edges = {r["section_id"]: set(split_edge_ids(r["final_edge_ids"])) for r in final_rows}
    by_process_section: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_issue: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in inventory_rows:
        by_process_section[(row["process"], row["section_id"])].append(row)
        by_issue[(row["process"], row["issue_type"], row["classification"])].append(row)

    process_rows: list[dict[str, Any]] = []
    for process in PROCESSES:
        status_by_section: dict[str, str] = {}
        for final in final_rows:
            sid = final["section_id"]
            statuses = [r["classification"] for r in by_process_section[(process, sid)]]
            status_by_section[sid] = max(statuses, key=CLASS_RANK.get)
        counts = {status: sum(value == status for value in status_by_section.values()) for status in CLASS_RANK}
        edge_counts = {
            status: len(set().union(*(final_edges[sid] for sid, value in status_by_section.items() if value == status)))
            for status in CLASS_RANK
        }
        edge_pair_counts = {
            status: sum(len(final_edges[sid]) for sid, value in status_by_section.items() if value == status)
            for status in CLASS_RANK
        }
        total = len(final_rows)
        process_rows.append({
            "process": process,
            "total_sections": total,
            "auto_resolved_sections": counts["AUTO_RESOLVED"],
            "review_required_sections": counts["REVIEW_REQUIRED"],
            "unresolved_sections": counts["UNRESOLVED"],
            "manual_review_rate": round(counts["REVIEW_REQUIRED"] / total, 6),
            "total_unique_edges": len(set().union(*final_edges.values())),
            "auto_resolved_unique_edges": edge_counts["AUTO_RESOLVED"],
            "review_required_unique_edges": edge_counts["REVIEW_REQUIRED"],
            "unresolved_unique_edges": edge_counts["UNRESOLVED"],
            "total_section_edge_pairs": sum(len(edges) for edges in final_edges.values()),
            "auto_resolved_section_edge_pairs": edge_pair_counts["AUTO_RESOLVED"],
            "review_required_section_edge_pairs": edge_pair_counts["REVIEW_REQUIRED"],
            "unresolved_section_edge_pairs": edge_pair_counts["UNRESOLVED"],
        })

    issue_rows: list[dict[str, Any]] = []
    for (process, issue_type, classification), rows in sorted(by_issue.items()):
        section_ids = sorted({r["section_id"] for r in rows})
        edges = {edge for r in rows for edge in split_edge_ids(r["affected_edge_ids"])}
        edge_pairs = {(r["section_id"], edge) for r in rows for edge in split_edge_ids(r["affected_edge_ids"])}
        issue_rows.append({
            "process": process,
            "issue_type": issue_type,
            "classification": classification,
            "section_count": len(section_ids),
            "unique_edge_count": len(edges),
            "section_edge_pair_count": len(edge_pairs),
            "section_ids": ";".join(section_ids),
        })

    check_types = {
        "lane_conflict": {"LANE_CENSUS_OSM_CONFLICT", "LANE_CENSUS_SUMO_CONFLICT"},
        "directional_lane_split": {"DIRECTIONAL_LANE_SPLIT_REQUIRED"},
        "attribute_contradiction": {"HIGHWAY_CLASS_MIXED", "HIGHWAY_CLASS_NON_ARTERIAL", "ROAD_TYPE_HIGHWAY_CONFLICT", "SPEED_OSM_SUMO_CONFLICT", "ACCESS_OSM_SUMO_CONFLICT", "ACCESS_LANE_LEVEL_MIXED"},
        "route_ref": {"ROUTE_REF_MISSING", "ROUTE_REF_CONFLICT"},
        "traffic_direction_unknown": {"TRAFFIC_DIRECTION_UNKNOWN"},
        "observation_quality": {"OBSERVATION_NONOBSERVED", "OBSERVATION_DATE_NONSPECIFIC", "OBSERVATION_WEATHER_MISSING", "TRAFFIC_COUNTS_MISSING"},
        "mapping_unsettled": {"MAPPING_UNSETTLED"},
    }
    required_checks: dict[str, dict[str, int]] = {}
    for check, types in check_types.items():
        matching = [row for row in inventory_rows if row["issue_type"] in types]
        required_checks[check] = {
            "section_count": len({row["section_id"] for row in matching}),
            "unique_edge_count": len({
                edge for row in matching for edge in split_edge_ids(row["affected_edge_ids"])
            }),
        }
    payload = {
        "schema_version": 1,
        "authoritative_input": "census_section_final_mapping.csv",
        "scope_sections": len(final_rows),
        "classification_order": ["AUTO_RESOLVED", "REVIEW_REQUIRED", "UNRESOLVED"],
        "manual_review_rate_definition": "REVIEW_REQUIRED sections / total sections; UNRESOLVED is reported separately",
        "counting_note": "unique_edge_count deduplicates SUMO edge IDs; section_edge_pair_count preserves reuse across Census sections",
        "no_data_modification": True,
        "process_summary": process_rows,
        "required_issue_checks": required_checks,
        "issue_summary": issue_rows,
        "recommendations": [
            {
                "issue_group": "lane_conflict",
                "recommendation": "RULE_BASED_TRIAGE_THEN_REVIEW_TRUE_CONFLICTS",
                "reason": "High volume. Normalize total-versus-directional lane semantics using Census oneway, OSM oneway and directional lane tags before sending only residual conflicts to review.",
            },
            {
                "issue_group": "route_ref",
                "recommendation": "RULE_BASED_NORMALIZATION_WITH_AUDITED_ALIAS_TABLE",
                "reason": "High volume and repeated numbering/tag-boundary patterns. Reuse reviewed route aliases, but retain mixed-route corridors for manual review.",
            },
            {
                "issue_group": "traffic_direction_unknown",
                "recommendation": "ADD_DETERMINISTIC_DIRECTION_MAPPING",
                "reason": "Recurring structural gap. Derive up/down to directed SUMO edges from official direction evidence, reverse-edge pairing and topology; manually review ambiguous interchanges only.",
            },
            {
                "issue_group": "observation_quality",
                "recommendation": "TIED_THIRD_KEEP_FLAGS_AUTOMATIC_REPAIR_SOURCE_MANUALLY",
                "reason": "Tied with traffic direction by section count. Detection is already rule-based, but missing counts, non-observed status and incomplete dates must not be imputed in this audit.",
            },
        ],
    }
    return process_rows, issue_rows, payload


def run(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    input_paths = config["inputs"]
    output_dir = REPOSITORY_ROOT / config["outputs"]["directory"]
    final_rows = read_csv(output_dir / "census_section_final_mapping.csv")
    sections = {r["census_section_id"]: r for r in read_csv(output_dir / "road_census_sections.csv")}
    hourly_by_section: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(output_dir / "road_census_hourly_traffic.csv"):
        hourly_by_section[row["census_section_id"]].append(row)
    wanted_edges = {edge for row in final_rows for edge in split_edge_ids(row["final_edge_ids"])}
    edge_rows = {
        row["sumo_edge_id"]: row
        for row in read_csv(output_dir / "sumo_edge_matching_attributes.csv")
        if row["sumo_edge_id"] in wanted_edges
    }
    missing_attributes = wanted_edges - set(edge_rows)
    if missing_attributes:
        raise ValueError(f"final edges missing from SUMO attributes: {sorted(missing_attributes)[:10]}")
    osm_tags = load_osm_way_tags(REPOSITORY_ROOT / input_paths["source_osm_xml"])
    tags_by_edge = {edge_id: merged_way_tags(row, osm_tags) for edge_id, row in edge_rows.items()}
    net_lanes = load_final_net_lanes(REPOSITORY_ROOT / input_paths["sumo_net_xml"], wanted_edges)
    missing_net = wanted_edges - set(net_lanes)
    if missing_net:
        raise ValueError(f"final edges missing from SUMO net: {sorted(missing_net)[:10]}")

    inv = Inventory()
    for final in final_rows:
        sid = final["section_id"]
        section = sections[sid]
        inventory_lane_projection(inv, final, section, edge_rows)
        inventory_attributes(inv, final, section, edge_rows, tags_by_edge, net_lanes)
        inventory_mapping_notes(inv, final)
        inventory_traffic(inv, final, hourly_by_section.get(sid, []))
        inventory_calibration_validation(inv, final, hourly_by_section.get(sid, []))
    for process in PROCESSES:
        for final in final_rows:
            if not inv.has_process(process, final["section_id"]):
                inv.add(process, final["section_id"], "NO_REVIEW_ISSUE", "AUTO_RESOLVED",
                        split_edge_ids(final["final_edge_ids"]), "no issue was detected by the stated audit rules", [])

    inventory_rows = inv.rows()
    process_rows, issue_rows, payload = summarize(inventory_rows, final_rows)
    write_csv(output_dir / f"{OUTPUT_STEM}.csv", inventory_rows, [
        "process", "section_id", "issue_type", "classification", "affected_edge_count",
        "affected_edge_ids", "evidence", "source_fields", "data_changed",
    ])
    write_csv(output_dir / f"{OUTPUT_STEM}_process_summary.csv", process_rows, list(process_rows[0]))
    write_csv(output_dir / f"{OUTPUT_STEM}_issue_summary.csv", issue_rows, list(issue_rows[0]))
    (output_dir / f"{OUTPUT_STEM}_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    payload = run(args.config)
    print(json.dumps(payload["process_summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
