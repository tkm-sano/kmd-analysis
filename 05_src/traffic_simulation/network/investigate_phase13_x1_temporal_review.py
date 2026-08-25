#!/usr/bin/env python3
"""Build the immutable Phase 13 X1 eight-Way temporal-review evidence set.

This is an investigation-only builder.  It does not resolve lanes, register an
evidence method, or alter the source OSM extract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_WAY_IDS = (
    23647119,
    378374542,
    474632305,
    474632841,
    604017306,
    1003546986,
    1107344513,
    1228062431,
)
SNAPSHOT_DATE = "2026-07-16"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tags(element: ET.Element) -> dict[str, str]:
    return {item.attrib["k"]: item.attrib["v"] for item in element.findall("tag")}


def _parse_way_history(path: Path) -> dict[str, Any]:
    versions = ET.parse(path).getroot().findall("way")
    if not versions:
        raise ValueError(f"OSM history has no Way versions: {path}")
    events: list[dict[str, Any]] = []
    previous_tags: dict[str, str] | None = None
    previous_nodes: list[int] | None = None
    for element in versions:
        tags = _tags(element)
        nodes = [int(item.attrib["ref"]) for item in element.findall("nd")]
        created = previous_tags is None
        changed_tags = []
        if previous_tags is not None:
            for key in sorted(set(previous_tags) | set(tags)):
                if previous_tags.get(key) != tags.get(key):
                    changed_tags.append(
                        {
                            "key": key,
                            "before": previous_tags.get(key),
                            "after": tags.get(key),
                        }
                    )
        events.append(
            {
                "version": int(element.attrib["version"]),
                "timestamp": element.attrib["timestamp"],
                "changeset": int(element.attrib["changeset"]),
                "created": created,
                "initial_relevant_tags": (
                    {
                        key: value
                        for key, value in tags.items()
                        if key in {"highway", "name", "oneway", "ref"}
                        or "lane" in key
                    }
                    if created
                    else {}
                ),
                "node_sequence_changed": (
                    previous_nodes is not None and previous_nodes != nodes
                ),
                "node_count": len(nodes),
                "changed_tags": changed_tags,
                "moving_lane_tag_change": any(
                    item["key"] == "lanes"
                    or item["key"].startswith("lanes:")
                    or item["key"].endswith(":lanes")
                    for item in changed_tags
                ),
                "oneway_tag_change": any(
                    item["key"] == "oneway" for item in changed_tags
                ),
            }
        )
        previous_tags = tags
        previous_nodes = nodes
    post_r3 = [event for event in events if event["timestamp"] >= "2021-09-01"]
    return {
        "source": str(path),
        "sha256": _sha256(path),
        "version_count": len(events),
        "latest_version": events[-1]["version"],
        "latest_timestamp": events[-1]["timestamp"],
        "post_r3_events": post_r3,
        "post_r3_event_count": len(post_r3),
        "post_r3_way_created": any(event["created"] for event in post_r3),
        "post_r3_node_sequence_change_count": sum(
            event["node_sequence_changed"] for event in post_r3
        ),
        "post_r3_moving_lane_tag_change_count": sum(
            event["moving_lane_tag_change"] for event in post_r3
        ),
        "post_r3_oneway_tag_change_count": sum(
            event["oneway_tag_change"] for event in post_r3
        ),
        "interpretation_limit": (
            "OSM history distinguishes Way tag/node-sequence edits only; it is not "
            "authoritative proof of road construction or of no construction."
        ),
    }


def _write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"immutable output already exists: {path}")
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-dir", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    population_path = args.prior_dir / "x1_fixed_population.json"
    match_path = args.prior_dir / "x1_mlit_r3_match_assessment_v3.json"
    population = json.loads(population_path.read_text(encoding="utf-8"))
    matches = json.loads(match_path.read_text(encoding="utf-8"))
    by_way = {item["source_way_id"]: item for item in population["records"]}
    match_by_way = {item["source_way_id"]: item for item in matches["records"]}
    if set(TARGET_WAY_IDS) - set(by_way) or set(TARGET_WAY_IDS) - set(match_by_way):
        raise ValueError("one or more fixed target Ways are missing from prior evidence")

    common_evidence = {
        "r3_road_condition_temporal_basis": {
            "authority": "国土交通省 道路局",
            "source": str(
                args.prior_dir / "raw/mlit_r3_kasyo_methodology.pdf"
            ),
            "sha256": _sha256(
                args.prior_dir / "raw/mlit_r3_kasyo_methodology.pdf"
            ),
            "basis": (
                "2021-04-01 condition is the default; sections scheduled for "
                "reconstruction by autumn are surveyed again in autumn and reflected."
            ),
            "per_record_exact_observation_date_available": False,
            "published_table_reference": "2021 autumn",
        },
        "tokyo_road_ledger": {
            "authority": "東京都建設局",
            "data_currency": "2025-06",
            "snapshot_coverage_end": "2025-06-30",
            "contains_osm_snapshot": False,
            "modification_history_capability_established": False,
            "lane_inventory_capability_established": False,
            "update_source": str(
                args.raw_dir / "tokyo_road_ledger_update_date_20260821.html"
            ),
            "update_source_sha256": _sha256(
                args.raw_dir / "tokyo_road_ledger_update_date_20260821.html"
            ),
            "limitation": (
                "The published plan currency ends before 2026-07-16 and the portal "
                "warns that ledger drawings can differ from current conditions."
            ),
        },
        "gsi_imagery": {
            "authority": "国土地理院",
            "seamless_photo_capture_period": "2019-06 through 2019-11",
            "photo_id": None,
            "photo_id_reason": "coverage is an orthophoto mosaic, not a selected single photograph",
            "post_r3_annual_coverage_2021_through_2026": False,
            "visible_lane_configuration": "not reviewed because no post-R3 target coverage exists",
            "interpretation_confidence": "not_applicable",
            "formal_effect": "none",
        },
    }

    shinagawa_evidence = {
        "authority": "東京都建設局",
        "project": "東京都市計画道路補助線街路第26号線（豊町）",
        "opening": "2021-10-22T11:00:00+09:00",
        "opening_extent": "品川区二葉一丁目～豊町二丁目、約670m",
        "project_period": "FY1991 through FY2023",
        "post_opening_work": "remaining side-road works explicitly continued",
        "effect_survey_date": "2022-04-26",
        "effect": (
            "the opened corridor carried about 5,000 vehicles/12h; parallel local-road "
            "traffic decreased, confirming a material network change"
        ),
        "sources": [
            {
                "path": str(args.raw_dir / "tokyo_hojo26_opening_20211007.html"),
                "sha256": _sha256(args.raw_dir / "tokyo_hojo26_opening_20211007.html"),
            },
            {
                "path": str(args.raw_dir / "tokyo_hojo26_opening_map_20211007.pdf"),
                "sha256": _sha256(args.raw_dir / "tokyo_hojo26_opening_map_20211007.pdf"),
            },
            {
                "path": str(args.raw_dir / "tokyo_hojo26_effects_20220831.html"),
                "sha256": _sha256(args.raw_dir / "tokyo_hojo26_effects_20220831.html"),
            },
            {
                "path": str(args.raw_dir / "tokyo_hojo26_effects_20220831.pdf"),
                "sha256": _sha256(args.raw_dir / "tokyo_hojo26_effects_20220831.pdf"),
            },
        ],
        "temporal_effect": (
            "The opening falls inside the R3 autumn reference season, so it is not "
            "by itself proof of a post-R3 change.  Continued side-road work and the "
            "absence of a complete official change ledger through 2026-07-16 prevent "
            "a no-change finding for the matched old-road/side-road Ways."
        ),
    }

    records = []
    for way_id in TARGET_WAY_IDS:
        source = by_way[way_id]
        match = match_by_way[way_id]
        candidate = match["selected_candidate"]
        if match["match_category"] != "A_EXACT_IDENTIFIER_GEOMETRY":
            raise ValueError(f"target Way {way_id} is not prior category A")
        history = _parse_way_history(args.raw_dir / f"osm_way_{way_id}_history.xml")
        shinagawa = way_id not in {23647119, 1107344513}
        identity_warning = not candidate["both_osm_endpoints_within_12m"]
        reasons = [
            "No official observation interval contains the 2026-07-16 OSM snapshot.",
            "No authoritative modification history proves no lane-configuration change through the snapshot.",
            "The available Tokyo road-ledger currency ends in 2025-06.",
            "GSI has no post-R3 annual imagery coverage at the target location.",
        ]
        if shinagawa:
            reasons.append(
                "The Way is in/adjacent to the Hojo Route 26 Toyomachi network-change area, where official records show a 2021-10-22 opening and continued side-road work."
            )
        else:
            reasons.append(
                "No directly applicable official construction/no-change record was located for the Okusawa segment."
            )
        if identity_warning:
            reasons.append(
                "Prior category A output has an endpoint-predicate inconsistency: one endpoint is not within 12m of the selected official geometry."
            )
        records.append(
            {
                "source_way_id": way_id,
                "stable_blocker_id": source["stable_blocker_id"],
                "stop_code": source["stop_code"],
                "source_way_version": source["source_way_version"],
                "source_way_timestamp": source["source_way_timestamp"],
                "source_tags": source["source_tags"],
                "highway": source["highway"],
                "road_name": source["names"].get("name"),
                "road_ref": source["identifiers"].get("ref"),
                "oneway": source["oneway"],
                "bridge": source["bridge"],
                "tunnel": source["tunnel"],
                "junction": source["junction"],
                "geometry": source["geometry"],
                "census_id": candidate["census_id"],
                "official_route_number": candidate["route_number"],
                "official_route_name": candidate["route_name"],
                "r3_oneway_flag": candidate["oneway_flag"],
                "r3_lane_count": candidate["lane_count"],
                "r3_observation_period": "2021 autumn; exact per-record date unavailable",
                "identity": {
                    "preserved_match_category": match["match_category"],
                    "route_ref_exact": candidate["route_ref_exact"],
                    "geometry_overlap_ratio_12m": candidate["geometry_overlap_ratio_12m"],
                    "both_osm_endpoints_within_12m": candidate[
                        "both_osm_endpoints_within_12m"
                    ],
                    "candidate_count_within_30m": match["candidate_count_within_30m"],
                    "status": "review_required" if identity_warning else "preserved",
                },
                "official_temporal_evidence": (
                    shinagawa_evidence if shinagawa else {
                        "authority": "東京都建設局 / 世田谷区",
                        "directly_applicable_modification_record_found": False,
                        "road_ledger_currency": "2025-06",
                        "temporal_effect": (
                            "No official record spanning the R3 condition through "
                            "2026-07-16 was located."
                        ),
                    }
                ),
                "osm_history": history,
                "temporal_predicate": {
                    "external_observation_interval_contains_snapshot": False,
                    "official_evidence_predates_snapshot": True,
                    "authoritative_no_change_history_to_snapshot": False,
                    "accepted": False,
                },
                "classification": "C_AMBIGUOUS",
                "formal_eligible": False,
                "classification_reasons": reasons,
            }
        )

    fixed_population = {
        "schema_version": 1,
        "investigation_id": "phase13_x1_temporal_review_8way_20260821",
        "status": "immutable_investigation_population",
        "population_definition": "user-specified X1 temporal review candidate Way IDs",
        "population_count": len(records),
        "source_population": str(population_path),
        "source_population_sha256": _sha256(population_path),
        "source_match_assessment": str(match_path),
        "source_match_assessment_sha256": _sha256(match_path),
        "source_osm_sha256": population["source_osm"]["byte_sha256"],
        "records": records,
    }
    aggregate = {
        "schema_version": 1,
        "investigation_id": fixed_population["investigation_id"],
        "population_count": len(records),
        "classification_counts": dict(
            sorted(Counter(record["classification"] for record in records).items())
        ),
        "formal_eligible_way_ids": [
            record["source_way_id"] for record in records if record["formal_eligible"]
        ],
        "formal_eligible_count": sum(record["formal_eligible"] for record in records),
        "expected_blocker_reduction": 0,
        "decision_readiness": False,
        "decision_candidate": "DEC-P13-LANE-COUNT-OFFICIAL-EVIDENCE-METHOD-001",
        "decision_gate": "at least one A_TEMPORALLY_CONFIRMED Way",
        "decision_gate_result": "not_met",
        "production_action": "do_not_proceed_to_decision_or_tdd",
        "common_evidence": common_evidence,
        "records_semantic_sha256": _canonical_sha(records),
    }
    manifest = {
        "schema_version": 1,
        "investigation_id": fixed_population["investigation_id"],
        "retrieved_at": "2026-08-21",
        "raw_artifacts": [
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in sorted(args.raw_dir.iterdir())
            if path.is_file()
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_new(args.output_dir / "x1_temporal_review_fixed_population.json", fixed_population)
    _write_new(args.output_dir / "x1_temporal_review_aggregates.json", aggregate)
    _write_new(args.output_dir / "raw_artifact_manifest.json", manifest)
    print(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
