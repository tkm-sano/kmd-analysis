#!/usr/bin/env python3
"""Refine lane-direction assumption candidates using explicit directed evidence."""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
DEFAULT_NET = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"
DEFAULT_OSM = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
CAUSE_CODES = (
    "OSM_DIRECTIONAL_TAG_MISSING", "SUMO_SYMMETRIC", "SUMO_ASYMMETRIC",
    "CENSUS_OSM_SUMO_CONFLICT", "SPECIAL_LANE_STRUCTURE", "OTHER",
)
RANK = {"NO_ASSUMPTION_NEEDED": 0, "ASSUMPTION_MAY_BE_NEEDED": 1, "UNRESOLVED": 2}
SPECIAL_EXACT = {"lanes:both_ways", "reversible", "shoulder"}
SPECIAL_PREFIXES = ("turn:lanes", "change:lanes", "bus:lanes", "lanes:bus", "lanes:psv", "lanes:hgv")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def positive_int(value: str | None) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def load_sumo_lane_counts(path: Path, wanted: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "edge":
            edge_id = element.get("id", "")
            if edge_id in wanted:
                counts[edge_id] = len(element.findall("lane"))
            element.clear()
    missing = wanted - set(counts)
    if missing:
        raise ValueError(f"SUMO lane counts missing for {len(missing)} edges: {sorted(missing)[:5]}")
    return counts


def load_special_lane_tags(path: Path, wanted_way_ids: set[str]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "way":
            way_id = element.get("id", "")
            if way_id in wanted_way_ids:
                tags = {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")}
                special = {
                    key: value for key, value in tags.items()
                    if key in SPECIAL_EXACT or key.startswith(SPECIAL_PREFIXES)
                }
                if special:
                    output[way_id] = special
            element.clear()
    return output


def classify_edge(
    edge: dict[str, str], official_total: int, reverse_lane_counts: dict[str, int],
    special_tags: dict[str, dict[str, str]],
) -> dict[str, Any]:
    edge_id = edge["edge_id"]
    actual = positive_int(edge.get("sumo_lane_count_normalized"))
    osm_total = positive_int(edge.get("osm_lanes_normalized"))
    forward = positive_int(edge.get("osm_lanes_forward_normalized"))
    backward = positive_int(edge.get("osm_lanes_backward_normalized"))
    source = edge.get("sumo_lane_count_source_type", "")
    oneway = edge.get("osm_oneway_normalized", "")
    reverse_id = edge.get("reverse_edge_id_normalized", "")
    way_ids = split(edge.get("osm_way_ids_raw", ""))
    edge_special = {way_id: special_tags[way_id] for way_id in way_ids if way_id in special_tags}
    causes: set[str] = set()
    if forward is None or backward is None:
        causes.add("OSM_DIRECTIONAL_TAG_MISSING")
    if edge_special:
        causes.add("SPECIAL_LANE_STRUCTURE")
    reverse_count = reverse_lane_counts.get(reverse_id) if reverse_id else None

    if actual is None:
        status, primary, reason = "UNRESOLVED", "CENSUS_OSM_SUMO_CONFLICT", "SUMO actual lane count is missing"
        causes.add(primary)
    elif oneway in {"yes", "-1"}:
        # For an explicitly one-way OSM way, lanes is already directional.  No
        # equal split or opposite-carriageway inference is performed here.
        if osm_total == actual and source == "OSM_EXPLICIT_TRANSFORMED":
            status, primary = "NO_ASSUMPTION_NEEDED", "OTHER"
            reason = "explicit OSM oneway lanes equals the realized directed SUMO lane count"
            causes.add("OTHER")
        elif source in {"MODEL_ASSUMPTION_MATERIALIZED", "SUMO_TYPE_DEFAULT"} or osm_total is None:
            status, primary = "ASSUMPTION_MAY_BE_NEEDED", "OSM_DIRECTIONAL_TAG_MISSING"
            reason = f"directed SUMO lanes rely on {source or 'unresolved provenance'}"
        else:
            status, primary = "UNRESOLVED", "CENSUS_OSM_SUMO_CONFLICT"
            reason = f"oneway OSM lanes={osm_total} differs from SUMO lanes={actual}"
            causes.add(primary)
    elif reverse_count is not None:
        pair_total = actual + reverse_count
        causes.add("SUMO_SYMMETRIC" if actual == reverse_count else "SUMO_ASYMMETRIC")
        pair_cause = "SUMO_SYMMETRIC" if actual == reverse_count else "SUMO_ASYMMETRIC"
        if source == "OSM_EXPLICIT_TRANSFORMED" and osm_total == pair_total == official_total:
            status, primary = "NO_ASSUMPTION_NEEDED", pair_cause
            reason = "realized forward/reverse SUMO lane counts sum to both explicit OSM and official Census totals"
        elif source in {"MODEL_ASSUMPTION_MATERIALIZED", "SUMO_TYPE_DEFAULT"} and osm_total == pair_total == official_total:
            status, primary = "ASSUMPTION_MAY_BE_NEEDED", pair_cause
            reason = f"SUMO pair is numerically consistent but lane provenance is {source}"
        else:
            status, primary = "UNRESOLVED", "CENSUS_OSM_SUMO_CONFLICT"
            reason = f"Census={official_total}, OSM={osm_total}, SUMO directed pair={actual}+{reverse_count}"
            causes.add(primary)
    else:
        status, primary = "ASSUMPTION_MAY_BE_NEEDED", "OSM_DIRECTIONAL_TAG_MISSING"
        reason = "neither explicit oneway directional lanes nor an exact reverse SUMO edge is available"

    return {
        "edge_id": edge_id,
        "classification": status,
        "primary_cause_code": primary,
        "cause_codes": sorted(causes or {primary}),
        "osm_way_ids": way_ids,
        "osm_lanes": osm_total,
        "osm_lanes_forward": forward,
        "osm_lanes_backward": backward,
        "osm_oneway": oneway or None,
        "sumo_lane_count": actual,
        "reverse_edge_id": reverse_id or None,
        "reverse_sumo_lane_count": reverse_count,
        "sumo_lane_count_source_type": source,
        "sumo_lane_count_extraction_rule_id": edge.get("sumo_lane_count_extraction_rule_id", ""),
        "special_lane_tags": edge_special,
        "reason": reason,
    }


def primary_section_cause(edge_evidence: list[dict[str, Any]], classification: str) -> str:
    relevant = [item for item in edge_evidence if item["classification"] == classification]
    priorities = (
        "CENSUS_OSM_SUMO_CONFLICT", "SPECIAL_LANE_STRUCTURE", "SUMO_ASYMMETRIC",
        "SUMO_SYMMETRIC", "OSM_DIRECTIONAL_TAG_MISSING", "OTHER",
    )
    present = {item["primary_cause_code"] for item in relevant}
    special = any("SPECIAL_LANE_STRUCTURE" in item["cause_codes"] for item in relevant)
    if special and classification != "NO_ASSUMPTION_NEEDED":
        return "SPECIAL_LANE_STRUCTURE"
    return next((code for code in priorities if code in present), "OTHER")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    section_counts = Counter(row["refined_classification"] for row in rows)
    edge_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
    cause_sections: dict[tuple[str, str], set[str]] = defaultdict(set)
    cause_edges: dict[tuple[str, str], set[str]] = defaultdict(set)
    primary_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        primary_rows[(row["primary_cause_code"], row["refined_classification"])].append(row)
        for edge_id, evidence in json.loads(row["edge_evidence_json"]).items():
            edge_pairs[evidence["classification"]].add((row["section_id"], edge_id))
            for cause in evidence["cause_codes"]:
                cause_sections[(cause, row["refined_classification"])].add(row["section_id"])
                cause_edges[(cause, row["refined_classification"])].add(edge_id)
    evidence_cause_summary = []
    primary_cause_summary = []
    for cause in CAUSE_CODES:
        for classification in ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED"):
            selected = primary_rows[(cause, classification)]
            matching_pairs = {
                (row["section_id"], edge_id)
                for row in selected
                for edge_id, evidence in json.loads(row["edge_evidence_json"]).items()
                if evidence["classification"] == classification
            }
            primary_cause_summary.append({
                "primary_cause_code": cause,
                "classification": classification,
                "section_count": len(selected),
                "unique_edge_count": len({edge for row in selected for edge in json.loads(row["edge_evidence_json"])}),
                "section_edge_pair_count": sum(int(row["edge_count"]) for row in selected),
                "matching_classification_unique_edge_count": len({edge_id for _, edge_id in matching_pairs}),
                "matching_classification_section_edge_pair_count": len(matching_pairs),
            })
            evidence_cause_summary.append({
                "cause_code": cause,
                "classification": classification,
                "section_count": len(cause_sections[(cause, classification)]),
                "unique_edge_count": len(cause_edges[(cause, classification)]),
            })
    return {
        "schema_version": 1,
        "scope": {"original_assumption_candidate_sections": len(rows)},
        "classification_summary": {
            classification: {
                "section_count": section_counts[classification],
                "unique_edge_count": len({edge for _, edge in edge_pairs[classification]}),
                "section_edge_pair_count": len(edge_pairs[classification]),
            }
            for classification in ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED")
        },
        "remaining_assumption_candidate_sections": section_counts["ASSUMPTION_MAY_BE_NEEDED"],
        "rules": {
            "explicit_oneway": "OSM oneway=yes/-1, explicit OSM lanes, OSM_EXPLICIT_TRANSFORMED provenance, and equal realized SUMO lanes resolve only the mapped directed edge; no opposite carriageway is inferred.",
            "bidirectional_pair": "An exact reverse SUMO edge resolves allocation only when realized pair sum equals explicit OSM lanes and official Census total.",
            "provenance_guard": "SUMO_TYPE_DEFAULT and MODEL_ASSUMPTION_MATERIALIZED remain assumption candidates even when numerical totals match.",
            "no_equal_split": True,
            "no_value_or_threshold_change": True,
        },
        "primary_cause_summary": primary_cause_summary,
        "evidence_cause_summary": evidence_cause_summary,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(data_dir: Path = DEFAULT_DATA_DIR, net_path: Path = DEFAULT_NET, osm_path: Path = DEFAULT_OSM) -> dict[str, Any]:
    inventory = [
        row for row in read_csv(data_dir / "assumption_inventory.csv")
        if row["target"] == "LANE_DIRECTION_ALLOCATION" and row["classification"] == "ASSUMPTION_MAY_BE_NEEDED"
    ]
    if len(inventory) != 59:
        raise ValueError(f"expected 59 original lane assumption candidates, got {len(inventory)}")
    census = {row["section_id"]: row for row in read_csv(data_dir / "road_census_section_attributes_normalized.csv")}
    edge_rows = {row["edge_id"]: row for row in read_csv(data_dir / "osm_sumo_edge_attributes_normalized.csv")}
    selected_ids = {edge_id for row in inventory for edge_id in split(row["edge_ids"])}
    reverse_ids = {edge_rows[edge_id]["reverse_edge_id_normalized"] for edge_id in selected_ids if edge_rows[edge_id]["reverse_edge_id_normalized"]}
    lane_counts = load_sumo_lane_counts(net_path, selected_ids | reverse_ids)
    way_ids = {way_id for edge_id in selected_ids for way_id in split(edge_rows[edge_id]["osm_way_ids_raw"])}
    special_tags = load_special_lane_tags(osm_path, way_ids)
    output: list[dict[str, Any]] = []
    for original in inventory:
        sid = original["section_id"]
        official_total = positive_int(census[sid].get("lane_count"))
        if official_total is None:
            raise ValueError(f"official lane count missing for {sid}")
        evidence = [
            classify_edge(edge_rows[edge_id], official_total, lane_counts, special_tags)
            for edge_id in split(original["edge_ids"])
        ]
        classification = max((item["classification"] for item in evidence), key=RANK.get)
        causes = sorted({cause for item in evidence for cause in item["cause_codes"]})
        provenance = Counter(item["sumo_lane_count_source_type"] for item in evidence)
        output.append({
            "section_id": sid,
            "original_classification": original["classification"],
            "refined_classification": classification,
            "primary_cause_code": primary_section_cause(evidence, classification),
            "cause_codes": ";".join(causes),
            "official_census_lane_count": official_total,
            "official_lane_direction_scope": census[sid]["lane_direction_scope"],
            "edge_count": len(evidence),
            "no_assumption_needed_edge_count": sum(item["classification"] == "NO_ASSUMPTION_NEEDED" for item in evidence),
            "assumption_may_be_needed_edge_count": sum(item["classification"] == "ASSUMPTION_MAY_BE_NEEDED" for item in evidence),
            "unresolved_edge_count": sum(item["classification"] == "UNRESOLVED" for item in evidence),
            "sumo_lane_provenance_counts_json": json.dumps(provenance, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "edge_evidence_json": json.dumps({item["edge_id"]: item for item in evidence}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "evidence_summary": f"explicitly resolved={sum(item['classification'] == 'NO_ASSUMPTION_NEEDED' for item in evidence)}; assumption provenance/incomplete={sum(item['classification'] == 'ASSUMPTION_MAY_BE_NEEDED' for item in evidence)}; conflicts={sum(item['classification'] == 'UNRESOLVED' for item in evidence)}",
            "classification_rule_id": "LANE_DIRECTION_EVIDENCE_REFINEMENT_V1",
            "data_changed": False,
        })
    summary = summarize(output)
    write_csv(data_dir / "lane_direction_assumption_refinement.csv", output)
    summary_rows = [
        {"classification": key, **value}
        for key, value in summary["classification_summary"].items()
    ]
    write_csv(data_dir / "lane_direction_assumption_refinement_summary.csv", summary_rows)
    write_csv(data_dir / "lane_direction_assumption_refinement_cause_summary.csv", summary["primary_cause_summary"])
    write_csv(data_dir / "lane_direction_assumption_refinement_evidence_cause_summary.csv", summary["evidence_cause_summary"])
    (data_dir / "lane_direction_assumption_refinement_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--net", type=Path, default=DEFAULT_NET)
    parser.add_argument("--osm", type=Path, default=DEFAULT_OSM)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.net, args.osm), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
