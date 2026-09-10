#!/usr/bin/env python3
"""Refine speed-assumption candidates without confusing travel and limit speed."""

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
DEFAULT_CENSUS = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/kasyo13.csv"
DEFAULT_TYPEMAP = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
CAUSE_CODES = (
    "OSM_EXPLICIT", "SUMO_DEFAULT", "SUMO_INFERRED", "CENSUS_COMPARABLE",
    "SOURCE_CONFLICT", "DEFINITION_NOT_COMPARABLE", "OTHER",
)
RANK = {"NO_ASSUMPTION_NEEDED": 0, "ASSUMPTION_MAY_BE_NEEDED": 1, "UNRESOLVED": 2}
CENSUS_ID = "交通調査基本区間番号"
CENSUS_LIMIT_SPEED = "指定最高速度（ｋｍ／ｈ）"


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def split(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def numeric(value: str | None) -> float | None:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def canonical_number(value: float | None) -> str:
    return "" if value is None else format(value, "g")


def expected_sumo_mps(kmh: float) -> str:
    return f"{kmh / 3.6:.2f}"


def load_typemap_speeds(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {element.get("id", ""): element.get("speed", "") for element in root.iter("type")}


def travel_speed_fields(row: dict[str, str]) -> dict[str, str]:
    return {
        key: value for key, value in row.items()
        if "旅行速度" in key and value.strip()
    }


def classify_edge(
    edge: dict[str, str], census_limit_kmh: float | None, travel_available: bool,
    typemap_speeds: dict[str, str],
) -> dict[str, Any]:
    edge_id = edge["edge_id"]
    source = edge.get("sumo_speed_source_type", "")
    actual = split(edge.get("sumo_speed_mps_normalized", ""))
    osm_status = edge.get("osm_maxspeed_missing_status", "")
    osm_kmh = numeric(edge.get("osm_maxspeed_normalized")) if osm_status == "PRESENT" else None
    sumo_type = edge.get("sumo_type_raw", "")
    typemap_speed = typemap_speeds.get(sumo_type, "")
    causes: set[str] = set()
    if census_limit_kmh is not None:
        causes.add("CENSUS_COMPARABLE")
    if travel_available:
        causes.add("DEFINITION_NOT_COMPARABLE")

    if source == "OSM_EXPLICIT_TRANSFORMED":
        causes.add("OSM_EXPLICIT")
        expected = expected_sumo_mps(osm_kmh) if osm_kmh is not None else None
        sumo_matches_osm = expected is not None and set(actual) == {expected}
        census_matches_osm = census_limit_kmh is None or osm_kmh == census_limit_kmh
        if sumo_matches_osm and census_matches_osm:
            status, primary = "NO_ASSUMPTION_NEEDED", "OSM_EXPLICIT"
            reason = "OSM explicit maxspeed is preserved by SUMO and does not conflict with Census designated maximum speed"
        else:
            status, primary = "UNRESOLVED", "SOURCE_CONFLICT"
            causes.add("SOURCE_CONFLICT")
            reason = (
                f"OSM={canonical_number(osm_kmh)} km/h, SUMO={actual} m/s, "
                f"Census designated maximum={canonical_number(census_limit_kmh)} km/h"
            )
    elif source == "SUMO_TYPE_DEFAULT":
        causes.add("SUMO_DEFAULT")
        if census_limit_kmh is not None:
            status, primary = "NO_ASSUMPTION_NEEDED", "CENSUS_COMPARABLE"
            matches = set(actual) == {expected_sumo_mps(census_limit_kmh)}
            reason = (
                "Road Census designated maximum speed supplies a directly comparable adoption basis; "
                + ("current SUMO default already matches" if matches else "current SUMO default differs and requires later remediation")
            )
        elif travel_available:
            status, primary = "ASSUMPTION_MAY_BE_NEEDED", "DEFINITION_NOT_COMPARABLE"
            reason = "only Road Census travel speeds exist; they cannot replace legal/designated maximum speed"
        else:
            status, primary = "ASSUMPTION_MAY_BE_NEEDED", "SUMO_DEFAULT"
            reason = "SUMO type default has no comparable explicit speed source"
    elif source in {"EVIDENCE_DERIVED", "RULE_DERIVED", "MODEL_ASSUMPTION_MATERIALIZED"}:
        causes.add("SUMO_INFERRED")
        if census_limit_kmh is not None:
            status, primary = "NO_ASSUMPTION_NEEDED", "CENSUS_COMPARABLE"
            reason = "comparable Census designated maximum speed makes the adoption basis explicit; inferred SUMO value remains separately recorded"
        else:
            status, primary = "ASSUMPTION_MAY_BE_NEEDED", "SUMO_INFERRED"
            reason = "SUMO inferred speed lacks a comparable explicit maximum-speed source"
    else:
        causes.add("OTHER")
        status, primary = "UNRESOLVED", "OTHER"
        reason = f"unsupported SUMO speed provenance {source!r}"

    return {
        "edge_id": edge_id,
        "classification": status,
        "primary_cause_code": primary,
        "cause_codes": sorted(causes),
        "osm_maxspeed_raw_json": edge.get("osm_maxspeed_raw_json", ""),
        "osm_maxspeed_normalized_kmh": canonical_number(osm_kmh),
        "osm_maxspeed_missing_status": osm_status,
        "sumo_speed_mps": actual,
        "sumo_type": sumo_type,
        "sumo_osm_defaults": split(edge.get("sumo_osm_defaults_raw", "")),
        "typemap_speed_raw": typemap_speed,
        "sumo_speed_source_type": source,
        "sumo_speed_source_id": edge.get("sumo_speed_source_id", ""),
        "sumo_speed_source_file": edge.get("sumo_speed_source_file", ""),
        "sumo_speed_extraction_rule_id": edge.get("sumo_speed_extraction_rule_id", ""),
        "census_designated_maxspeed_kmh": canonical_number(census_limit_kmh),
        "reason": reason,
    }


def section_primary(evidence: list[dict[str, Any]], classification: str) -> str:
    present = {item["primary_cause_code"] for item in evidence if item["classification"] == classification}
    for cause in ("SOURCE_CONFLICT", "OTHER", "DEFINITION_NOT_COMPARABLE", "SUMO_INFERRED", "SUMO_DEFAULT", "CENSUS_COMPARABLE", "OSM_EXPLICIT"):
        if cause in present:
            return cause
    return "OTHER"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    section_counts = Counter(row["refined_classification"] for row in rows)
    edge_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
    primary: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    evidence_causes: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    default_matches: set[tuple[str, str]] = set()
    default_differs: set[tuple[str, str]] = set()
    for row in rows:
        primary[(row["primary_cause_code"], row["refined_classification"])].append(row)
        for edge_id, item in json.loads(row["edge_evidence_json"]).items():
            edge_pairs[item["classification"]].add((row["section_id"], edge_id))
            for cause in item["cause_codes"]:
                evidence_causes[(cause, item["classification"])].add((row["section_id"], edge_id))
            if item["sumo_speed_source_type"] == "SUMO_TYPE_DEFAULT":
                target = default_matches if "already matches" in item["reason"] else default_differs
                target.add((row["section_id"], edge_id))
    primary_summary = []
    evidence_summary = []
    for cause in CAUSE_CODES:
        for classification in ("NO_ASSUMPTION_NEEDED", "ASSUMPTION_MAY_BE_NEEDED", "UNRESOLVED"):
            selected = primary[(cause, classification)]
            primary_summary.append({
                "primary_cause_code": cause, "classification": classification,
                "section_count": len(selected),
                "unique_edge_count": len({edge for row in selected for edge in json.loads(row["edge_evidence_json"])}),
                "section_edge_pair_count": sum(int(row["edge_count"]) for row in selected),
            })
            pairs = evidence_causes[(cause, classification)]
            evidence_summary.append({
                "cause_code": cause, "edge_classification": classification,
                "section_count": len({sid for sid, _ in pairs}),
                "unique_edge_count": len({edge for _, edge in pairs}),
                "section_edge_pair_count": len(pairs),
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
        "remaining_research_assumption_sections": section_counts["ASSUMPTION_MAY_BE_NEEDED"],
        "remaining_research_assumption_unique_edges": len({edge for _, edge in edge_pairs["ASSUMPTION_MAY_BE_NEEDED"]}),
        "definition_policy": {
            "census_designated_maximum_speed": "COMPARABLE_TO_OSM_MAXSPEED",
            "census_travel_speed": "NOT_COMPARABLE_TO_LIMIT_SPEED",
            "sumo_type_default": "MODEL_DEFAULT_NOT_AN_OBSERVED_OR_LEGAL_SPEED",
            "no_imputation_or_value_change": True,
        },
        "sumo_default_vs_census_designated_maximum": {
            "already_matches": {
                "unique_edge_count": len({edge for _, edge in default_matches}),
                "section_edge_pair_count": len(default_matches),
            },
            "differs_remediation_required": {
                "unique_edge_count": len({edge for _, edge in default_differs}),
                "section_edge_pair_count": len(default_differs),
            },
        },
        "primary_cause_summary": primary_summary,
        "evidence_cause_summary": evidence_summary,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(data_dir: Path = DEFAULT_DATA_DIR, census_path: Path = DEFAULT_CENSUS, typemap_path: Path = DEFAULT_TYPEMAP) -> dict[str, Any]:
    candidates = [
        row for row in read_csv(data_dir / "assumption_inventory.csv")
        if row["target"] == "SPEED_VALUE_SELECTION" and row["classification"] == "ASSUMPTION_MAY_BE_NEEDED"
    ]
    if len(candidates) != 41:
        raise ValueError(f"expected 41 speed candidates, got {len(candidates)}")
    raw_census = {row[CENSUS_ID]: row for row in read_csv(census_path, "cp932")}
    edges = {row["edge_id"]: row for row in read_csv(data_dir / "osm_sumo_edge_attributes_normalized.csv")}
    typemap_speeds = load_typemap_speeds(typemap_path)
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        sid = candidate["section_id"]
        raw = raw_census[sid]
        census_limit = numeric(raw.get(CENSUS_LIMIT_SPEED))
        travel = travel_speed_fields(raw)
        evidence = [
            classify_edge(edges[edge_id], census_limit, bool(travel), typemap_speeds)
            for edge_id in split(candidate["edge_ids"])
        ]
        classification = max((item["classification"] for item in evidence), key=RANK.get)
        output.append({
            "section_id": sid,
            "original_classification": candidate["classification"],
            "refined_classification": classification,
            "primary_cause_code": section_primary(evidence, classification),
            "cause_codes": ";".join(sorted({cause for item in evidence for cause in item["cause_codes"]})),
            "census_designated_maxspeed_raw": raw.get(CENSUS_LIMIT_SPEED, ""),
            "census_designated_maxspeed_normalized_kmh": canonical_number(census_limit),
            "census_designated_maxspeed_source": "MLIT_R3_kasyo13.csv",
            "census_designated_maxspeed_rule_id": "RC_R3_DESIGNATED_MAXIMUM_SPEED_PRESERVE_NUMERIC_V1",
            "census_travel_speed_raw_json": json.dumps(travel, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "census_travel_speed_comparability": "DEFINITION_NOT_COMPARABLE_TO_MAXSPEED" if travel else "MISSING",
            "edge_count": len(evidence),
            "no_assumption_needed_edge_count": sum(item["classification"] == "NO_ASSUMPTION_NEEDED" for item in evidence),
            "assumption_may_be_needed_edge_count": sum(item["classification"] == "ASSUMPTION_MAY_BE_NEEDED" for item in evidence),
            "unresolved_edge_count": sum(item["classification"] == "UNRESOLVED" for item in evidence),
            "edge_evidence_json": json.dumps({item["edge_id"]: item for item in evidence}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "classification_rule_id": "SPEED_ADOPTION_EVIDENCE_REFINEMENT_V1",
            "data_changed": False,
        })
    summary = summarize(output)
    write_csv(data_dir / "speed_assumption_refinement.csv", output)
    write_csv(data_dir / "speed_assumption_refinement_summary.csv", [
        {"classification": key, **value} for key, value in summary["classification_summary"].items()
    ])
    write_csv(data_dir / "speed_assumption_refinement_cause_summary.csv", summary["primary_cause_summary"])
    write_csv(data_dir / "speed_assumption_refinement_evidence_cause_summary.csv", summary["evidence_cause_summary"])
    (data_dir / "speed_assumption_refinement_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--census", type=Path, default=DEFAULT_CENSUS)
    parser.add_argument("--typemap", type=Path, default=DEFAULT_TYPEMAP)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.census, args.typemap), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
