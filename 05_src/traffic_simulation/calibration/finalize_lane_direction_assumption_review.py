#!/usr/bin/env python3
"""Finalize the evidence-only review of the remaining lane-direction cases.

This audit does not select new lane values.  It distinguishes explicit source
conflicts from lane values that exist in SUMO only because a simulation policy
or a netconvert importer default materialized them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
DEFAULT_POLICY = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/v17_phase13_missing_lane_simulation_fallback_policy.yml"
DEFAULT_DECISION = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/v17_phase13_missing_lane_simulation_fallback_decision.yml"
DEFAULT_TYPEMAP = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
DEFAULT_NET_EXECUTION = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/netconvert.execution.json"
DEFAULT_FORMAL_POLICY = REPOSITORY_ROOT / "05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md"

FINAL_CLASSES = (
    "NO_ASSUMPTION_NEEDED", "MODEL_ASSUMPTION_REQUIRED", "DATA_CONFLICT", "UNRESOLVED",
)
RANK = {name: index for index, name in enumerate(FINAL_CLASSES)}
MODEL_SOURCES = {"MODEL_ASSUMPTION_MATERIALIZED", "SUMO_TYPE_DEFAULT"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def positive_int(value: Any) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def json_value(value: str, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_decisive_edge(
    previous_section_class: str,
    official_total: int,
    evidence: dict[str, Any],
    edge: dict[str, str],
) -> tuple[str, str, str]:
    """Return final class, cause code and reason without creating a lane split."""

    source = edge["sumo_lane_count_source_type"]
    actual = positive_int(edge["sumo_lane_count_normalized"])
    reverse = positive_int(evidence.get("reverse_sumo_lane_count"))
    osm_total = positive_int(edge["osm_lanes_normalized"])
    pair_total = actual + reverse if actual is not None and reverse is not None else None

    if previous_section_class == "UNRESOLVED" and pair_total is not None:
        if osm_total is not None and osm_total != official_total:
            return (
                "DATA_CONFLICT", "CENSUS_OSM_EXPLICIT_CONFLICT",
                f"official Census total={official_total}, explicit OSM total={osm_total}, realized SUMO pair={actual}+{reverse}={pair_total}",
            )
        if pair_total != official_total:
            return (
                "DATA_CONFLICT", "CENSUS_SUMO_MATERIALIZED_CONFLICT",
                f"official Census total={official_total}, OSM lane counts missing, but realized SUMO pair={actual}+{reverse}={pair_total}; SUMO value originates from {source}",
            )
        if source in MODEL_SOURCES:
            return (
                "MODEL_ASSUMPTION_REQUIRED", "NUMERIC_MATCH_WITH_MODEL_PROVENANCE",
                f"SUMO pair={actual}+{reverse}={pair_total} matches Census numerically, but OSM lane counts are missing and provenance is {source}",
            )

    if source == "MODEL_ASSUMPTION_MATERIALIZED":
        return (
            "MODEL_ASSUMPTION_REQUIRED", "SIMULATION_FALLBACK_NOT_FORMAL_EVIDENCE",
            "lane count is a simulation-only baseline fallback with value_origin=model_assumed and the formal missing-evidence blocker preserved",
        )
    if source == "SUMO_TYPE_DEFAULT":
        return (
            "MODEL_ASSUMPTION_REQUIRED", "NETCONVERT_IMPORTER_DEFAULT_NOT_FORMAL_EVIDENCE",
            "OSM lane tags and typemap numLanes are absent; netconvert annotated numLanes in osmDefaults and materialized one lane",
        )
    if source == "OSM_EXPLICIT_TRANSFORMED" and pair_total == osm_total == official_total:
        return "NO_ASSUMPTION_NEEDED", "EXPLICIT_TOTALS_AGREE", "explicit OSM, SUMO directed pair and Census totals agree"
    return "UNRESOLVED", "INSUFFICIENT_REGISTERED_EVIDENCE", "available registered evidence does not determine one final lane allocation"


def make_edge_record(
    section: dict[str, str], evidence: dict[str, Any], edge: dict[str, str],
    official_total: int, policy_path: Path, decision_path: Path,
    typemap_path: Path, net_execution_path: Path, formal_policy_path: Path,
) -> dict[str, Any]:
    final_class, cause, reason = classify_decisive_edge(
        section["refined_classification"], official_total, evidence, edge
    )
    assumptions = json_value(edge["lane_assumption_records_raw_json"], [])
    assumption = assumptions[0] if assumptions else {}
    actual = positive_int(edge["sumo_lane_count_normalized"])
    reverse = positive_int(evidence.get("reverse_sumo_lane_count"))
    pair_total = actual + reverse if actual is not None and reverse is not None else ""
    source = edge["sumo_lane_count_source_type"]
    approved_rule_justifies_formal_value = False
    return {
        "section_id": section["section_id"],
        "edge_id": edge["edge_id"],
        "previous_edge_classification": evidence["classification"],
        "final_classification": final_class,
        "cause_code": cause,
        "official_census_lane_count": official_total,
        "official_lane_direction_scope": section["official_lane_direction_scope"],
        "osm_way_id": edge["osm_way_id"],
        "osm_highway": edge["osm_highway_normalized"],
        "osm_oneway": edge["osm_oneway_normalized"],
        "osm_lanes": edge["osm_lanes_normalized"],
        "osm_lanes_forward": edge["osm_lanes_forward_normalized"],
        "osm_lanes_backward": edge["osm_lanes_backward_normalized"],
        "sumo_lane_count": edge["sumo_lane_count_normalized"],
        "reverse_edge_id": evidence.get("reverse_edge_id") or "",
        "reverse_sumo_lane_count": evidence.get("reverse_sumo_lane_count") if evidence.get("reverse_sumo_lane_count") is not None else "",
        "sumo_pair_total": pair_total,
        "sumo_type": edge["sumo_type_raw"],
        "sumo_osm_defaults": edge["sumo_osm_defaults_raw"],
        "sumo_lane_source_type": source,
        "sumo_lane_source_id": edge["sumo_lane_count_source_id"],
        "sumo_lane_source_file": edge["sumo_lane_count_source_file"],
        "sumo_lane_extraction_rule_id": edge["sumo_lane_count_extraction_rule_id"],
        "assumption_id": assumption.get("assumption_id", ""),
        "decision_id": assumption.get("decision_id", ""),
        "scenario": assumption.get("scenario", ""),
        "fallback_level": assumption.get("fallback_level", ""),
        "calibration_group": assumption.get("calibration_group", ""),
        "chosen_lane_count_json": json.dumps(assumption.get("chosen_lane_count", {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "value_origin": assumption.get("value_origin", "SUMO_IMPORTER_DEFAULT" if source == "SUMO_TYPE_DEFAULT" else ""),
        "formal_stop_code": assumption.get("formal_stop_code", "LANE_DIRECTIONAL_ALLOCATION_MISSING" if source == "SUMO_TYPE_DEFAULT" else ""),
        "formal_blocker_preserved": assumption.get("formal_blocker_preserved", source in MODEL_SOURCES),
        "source_rewrite": assumption.get("source_rewrite", False),
        "approved_rule_justifies_formal_value": approved_rule_justifies_formal_value,
        "fallback_policy_file": relative(policy_path) if source == "MODEL_ASSUMPTION_MATERIALIZED" else "",
        "fallback_decision_file": relative(decision_path) if source == "MODEL_ASSUMPTION_MATERIALIZED" else "",
        "typemap_file": relative(typemap_path) if source == "SUMO_TYPE_DEFAULT" else "",
        "netconvert_execution_file": relative(net_execution_path) if source == "SUMO_TYPE_DEFAULT" else "",
        "formal_policy_file": relative(formal_policy_path),
        "reason": reason,
        "data_changed": False,
    }


def summarize(section_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, dict[str, Any]] = {}
    for classification in FINAL_CLASSES:
        sections = [row for row in section_rows if row["final_classification"] == classification]
        decisive = [row for row in edge_rows if row["final_classification"] == classification]
        by_class[classification] = {
            "section_count": len(sections),
            "target_corridor_unique_edge_count": len({edge for row in sections for edge in row["all_edge_ids"].split(";") if edge}),
            "target_corridor_section_edge_pair_count": sum(row["all_edge_count"] for row in sections),
            "decisive_unique_edge_count": len({row["edge_id"] for row in decisive}),
            "decisive_section_edge_pair_count": len(decisive),
        }
    primary_cause_summary = []
    for cause in sorted({row["primary_cause_code"] for row in section_rows}):
        sections = [row for row in section_rows if row["primary_cause_code"] == cause]
        decisive = [row for row in edge_rows if row["cause_code"] == cause]
        primary_cause_summary.append({
            "cause_code": cause,
            "final_classification": sections[0]["final_classification"],
            "section_count": len(sections),
            "decisive_unique_edge_count": len({row["edge_id"] for row in decisive}),
            "decisive_section_edge_pair_count": len(decisive),
        })
    evidence_cause_summary = []
    for cause in sorted({row["cause_code"] for row in edge_rows}):
        decisive = [row for row in edge_rows if row["cause_code"] == cause]
        evidence_cause_summary.append({
            "cause_code": cause,
            "final_classification": decisive[0]["final_classification"],
            "section_count": len({row["section_id"] for row in decisive}),
            "decisive_unique_edge_count": len({row["edge_id"] for row in decisive}),
            "decisive_section_edge_pair_count": len(decisive),
        })
    source_summary = []
    for source in sorted({row["sumo_lane_source_type"] for row in edge_rows}):
        decisive = [row for row in edge_rows if row["sumo_lane_source_type"] == source]
        source_summary.append({
            "sumo_lane_source_type": source,
            "section_count": len({row["section_id"] for row in decisive}),
            "decisive_unique_edge_count": len({row["edge_id"] for row in decisive}),
            "decisive_section_edge_pair_count": len(decisive),
        })
    return {
        "classification_summary": by_class,
        "primary_cause_summary": primary_cause_summary,
        "evidence_cause_summary": evidence_cause_summary,
        "source_provenance_summary": source_summary,
    }


def run(
    data_dir: Path = DEFAULT_DATA_DIR,
    policy_path: Path = DEFAULT_POLICY,
    decision_path: Path = DEFAULT_DECISION,
    typemap_path: Path = DEFAULT_TYPEMAP,
    net_execution_path: Path = DEFAULT_NET_EXECUTION,
    formal_policy_path: Path = DEFAULT_FORMAL_POLICY,
) -> dict[str, Any]:
    refinements = [
        row for row in read_csv(data_dir / "lane_direction_assumption_refinement.csv")
        if row["refined_classification"] != "NO_ASSUMPTION_NEEDED"
    ]
    if Counter(row["refined_classification"] for row in refinements) != Counter({"ASSUMPTION_MAY_BE_NEEDED": 17, "UNRESOLVED": 4}):
        raise ValueError("expected the reviewed scope to contain 17 assumption candidates and 4 unresolved sections")
    attrs = {row["edge_id"]: row for row in read_csv(data_dir / "osm_sumo_edge_attributes_normalized.csv")}
    census = {row["section_id"]: row for row in read_csv(data_dir / "road_census_section_attributes_normalized.csv")}

    edge_output: list[dict[str, Any]] = []
    section_output: list[dict[str, Any]] = []
    for section in refinements:
        sid = section["section_id"]
        official_total = positive_int(section["official_census_lane_count"])
        if official_total is None:
            raise ValueError(f"missing official Census lane total for {sid}")
        all_evidence = json.loads(section["edge_evidence_json"])
        decisive_evidence = [item for item in all_evidence.values() if item["classification"] != "NO_ASSUMPTION_NEEDED"]
        records = [
            make_edge_record(section, evidence, attrs[evidence["edge_id"]], official_total,
                             policy_path, decision_path, typemap_path, net_execution_path, formal_policy_path)
            for evidence in decisive_evidence
        ]
        edge_output.extend(records)
        final_class = max((row["final_classification"] for row in records), key=RANK.get)
        relevant = [row for row in records if row["final_classification"] == final_class]
        causes = Counter(row["cause_code"] for row in relevant)
        primary_cause = causes.most_common(1)[0][0]
        assumption_ids = sorted({row["assumption_id"] for row in records if row["assumption_id"]})
        decision_ids = sorted({row["decision_id"] for row in records if row["decision_id"]})
        levels = sorted({row["fallback_level"] for row in records if row["fallback_level"]})
        source_types = Counter(row["sumo_lane_source_type"] for row in records)
        conflict_details = "; ".join(row["reason"] for row in relevant[:3])
        section_output.append({
            "section_id": sid,
            "previous_classification": section["refined_classification"],
            "final_classification": final_class,
            "primary_cause_code": primary_cause,
            "official_census_lane_count": official_total,
            "official_lane_direction_scope": section["official_lane_direction_scope"],
            "official_lane_source": census[sid]["lane_count_source"],
            "official_lane_normalization_rule_id": census[sid]["lane_count_normalization_rule_id"],
            "all_edge_count": int(section["edge_count"]),
            "all_edge_ids": ";".join(all_evidence),
            "decisive_edge_count": len(records),
            "decisive_edge_ids": ";".join(row["edge_id"] for row in records),
            "decisive_source_type_counts_json": json.dumps(source_types, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "assumption_ids": ";".join(assumption_ids),
            "decision_ids": ";".join(decision_ids),
            "fallback_levels": ";".join(levels),
            "approved_rule_justifies_formal_value": False,
            "evidence_summary": conflict_details,
            "classification_rule_id": "LANE_REMAINING_ASSUMPTION_FINAL_REVIEW_V1",
            "data_changed": False,
        })

    summary_parts = summarize(section_output, edge_output)
    execution = json.loads(net_execution_path.read_text(encoding="utf-8"))
    summary = {
        "schema_version": 1,
        "scope": {
            "section_count": len(section_output),
            "previous_assumption_may_be_needed": 17,
            "previous_unresolved": 4,
            "decisive_section_edge_pair_count": len(edge_output),
            "decisive_unique_edge_count": len({row["edge_id"] for row in edge_output}),
        },
        **summary_parts,
        "provenance": {
            "fallback_policy": {"path": relative(policy_path), "sha256": sha256(policy_path), "policy_id": "MISSING_SOURCE_LANE_SIMULATION_FALLBACK_V1", "policy_version": "1.0.0"},
            "fallback_decision": {"path": relative(decision_path), "sha256": sha256(decision_path), "decision_id": "DEC-P13-LANE-MISSING-SOURCE-SIMULATION-FALLBACK-001", "status": "approved_for_simulation_model_assumption"},
            "typemap": {"path": relative(typemap_path), "sha256": sha256(typemap_path), "primary_link_numLanes_explicit": False},
            "netconvert": {"execution_path": relative(net_execution_path), "sha256": sha256(net_execution_path), "argv": execution["argv"], "exit_code": execution["exit_code"], "osm_annotate_defaults": True},
            "formal_policy": {"path": relative(formal_policy_path), "rule": "value_origin=model_assumed is not formal eligible"},
        },
        "decision_rules": {
            "model_assumption_materialized": "An approved simulation fallback remains MODEL_ASSUMPTION_REQUIRED when value_origin=model_assumed and formal_blocker_preserved=true.",
            "sumo_type_default": "A lane count annotated by netconvert osmDefaults=numLanes is not official, explicit OSM, or formal approved lane evidence.",
            "data_conflict": "DATA_CONFLICT is used when the official Census both-directions total disagrees with explicit OSM total or the realized forward/reverse SUMO pair.",
            "no_equal_split_or_imputation": True,
            "values_and_thresholds_changed": False,
        },
    }
    write_csv(data_dir / "lane_direction_assumption_final_review.csv", section_output)
    write_csv(data_dir / "lane_direction_assumption_final_review_edge_evidence.csv", edge_output)
    write_csv(data_dir / "lane_direction_assumption_final_review_summary.csv", [
        {"final_classification": key, **value} for key, value in summary_parts["classification_summary"].items()
    ])
    write_csv(data_dir / "lane_direction_assumption_final_review_cause_summary.csv", summary_parts["evidence_cause_summary"])
    (data_dir / "lane_direction_assumption_final_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
