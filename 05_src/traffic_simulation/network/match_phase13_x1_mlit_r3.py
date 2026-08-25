#!/usr/bin/env python3
"""Assess the fixed Phase 13 X1 population against official MLIT R3 data.

This is an investigation tool.  It does not materialize lane counts and it does
not register an evidence method in the v17 runtime.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform, unary_union


BUFFER_M = 12.0
NEARBY_M = 30.0
HIGH_OVERLAP = 0.90
EVIDENCE_DATE = "2021-10-01"
OSM_SNAPSHOT_DATE = "2026-07-16"

# OSM expressway refs and the Road Census route-number namespace are different.
# These aliases are used only to test identity; they never supply a lane count.
EXPRESSWAY_ALIASES = {
    "B": ("52", "高速湾岸線"),
    "C2": ("120", "高速中央環状線"),
    "K6": ("160", "高速神奈川6号川崎線"),
}


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalize_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    for token in ("首都", " ", "　", "(", ")", "（", "）", "・"):
        text = text.replace(token, "")
    return text


def name_agrees(osm_name: str | None, official_name: str | None) -> bool:
    left = normalize_name(osm_name)
    right = normalize_name(official_name)
    if not left or not right:
        return False
    return left == right or left in right or right in left


def load_rows(paths: list[Path]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in paths:
        with path.open(encoding="cp932") as stream:
            for row in csv.DictReader(stream):
                rows[row["交通調査基本区間番号"]] = row
    return rows


def load_features(tile_dir: Path, rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    fragments: dict[str, list[Any]] = defaultdict(list)
    source_files: dict[str, set[str]] = defaultdict(set)
    for name in sorted(glob.glob(str(tile_dir / "*.geojson"))):
        path = Path(name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload["features"]:
            census_id = str(feature["properties"]["census"])
            fragments[census_id].append(shape(feature["geometry"]))
            source_files[census_id].add(path.name)

    project = Transformer.from_crs(4326, 6677, always_xy=True).transform
    features = []
    for census_id in sorted(fragments):
        if census_id not in rows:
            continue
        row = rows[census_id]
        features.append(
            {
                "census_id": census_id,
                "geometry": transform(project, unary_union(fragments[census_id])),
                "route_number": row["路線番号"],
                "route_name": row["路線名"],
                "management_code": row["管理区分"],
                "separated_segment_code": row["分離区間／分離区分"],
                "oneway_flag": row["一方通行フラグ"],
                "lane_count": row["車線数"],
                "source_tile_files": sorted(source_files[census_id]),
            }
        )
    return features


def identity_components(record: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    osm_ref = record["identifiers"].get("ref")
    osm_name = record["names"].get("name") or record["names"].get("name:ja")
    alias = EXPRESSWAY_ALIASES.get(osm_ref)
    alias_agreement = bool(
        alias
        and candidate["route_number"] == alias[0]
        and name_agrees(alias[1], candidate["route_name"])
    )
    return {
        "route_ref_exact": bool(osm_ref and osm_ref == candidate["route_number"]),
        "route_name_agreement": name_agrees(osm_name, candidate["route_name"]),
        "expressway_namespace_alias_agreement": alias_agreement,
        "operator_agreement": None,
        "operator_agreement_reason": "OSM operator is absent for all 135 Ways",
    }


def assess(population: dict[str, Any], features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    project = Transformer.from_crs(4326, 6677, always_xy=True).transform
    results = []
    for record in population["records"]:
        osm_line = transform(project, LineString(record["geometry"]["coordinates_lon_lat"]))
        candidates = []
        for feature in features:
            distance = osm_line.distance(feature["geometry"])
            if distance > NEARBY_M:
                continue
            overlap = osm_line.intersection(feature["geometry"].buffer(BUFFER_M)).length / osm_line.length
            start_distance = feature["geometry"].distance(LineString(osm_line.coords[:2]).boundary.geoms[0])
            end_distance = feature["geometry"].distance(LineString(osm_line.coords[-2:]).boundary.geoms[-1])
            identity = identity_components(record, feature)
            candidates.append(
                {
                    "census_id": feature["census_id"],
                    "route_number": feature["route_number"],
                    "route_name": feature["route_name"],
                    "management_code": feature["management_code"],
                    "separated_segment_code": feature["separated_segment_code"],
                    "oneway_flag": feature["oneway_flag"],
                    "lane_count": int(feature["lane_count"]) if feature["lane_count"].isdigit() else None,
                    "minimum_distance_m": round(distance, 3),
                    "geometry_overlap_ratio_12m": round(overlap, 6),
                    "both_osm_endpoints_within_12m": start_distance <= BUFFER_M and end_distance <= BUFFER_M,
                    "source_tile_files": feature["source_tile_files"],
                    **identity,
                }
            )
        candidates.sort(key=lambda item: (-item["geometry_overlap_ratio_12m"], item["census_id"]))

        osm_ref = record["identifiers"].get("ref")
        osm_name = record["names"].get("name") or record["names"].get("name:ja")
        alias = EXPRESSWAY_ALIASES.get(osm_ref)
        source_identity_conflict = bool(alias and osm_name and not name_agrees(osm_name, alias[1]))
        high = [item for item in candidates if item["geometry_overlap_ratio_12m"] >= HIGH_OVERLAP]
        exact = [item for item in high if item["route_ref_exact"]]
        strong = [
            item for item in high
            if item["route_name_agreement"]
            or (item["expressway_namespace_alias_agreement"] and not source_identity_conflict)
        ]

        selected = None
        if len(exact) == 1:
            category = "A_EXACT_IDENTIFIER_GEOMETRY"
            selected = exact[0]
        elif strong:
            category = "B_STRONG_NAME_GEOMETRY"
            selected = strong[0]
        elif (source_identity_conflict and high) or not candidates or (not osm_ref and not osm_name):
            category = "E_SOURCE_IDENTITY_NOT_USABLE"
        else:
            category = "C_AMBIGUOUS_OR_INCOMPLETE_MATCH"

        lane_semantics = None
        temporal = None
        formal_eligible = False
        reasons = ["official_evidence_method_not_approved_in_v17"]
        if selected:
            if selected["oneway_flag"] in {"1", "2"}:
                lane_semantics = "active_direction_moving_lane_count"
            elif selected["oneway_flag"] == "0":
                lane_semantics = "both_directions_total_not_assignable_to_split_osm_way"
                reasons.append("directional_lane_semantics_incompatible")
            else:
                lane_semantics = "official_oneway_flag_unknown"
                reasons.append("official_direction_semantics_unknown")
            temporal = {
                "evidence_reference_date": EVIDENCE_DATE,
                "osm_snapshot_date": OSM_SNAPSHOT_DATE,
                "aligned": False,
                "reason": "R3 road-condition evidence predates the 2026-07-16 OSM snapshot",
            }
            reasons.append("temporal_alignment_not_established")
        else:
            reasons.append("external_match_not_selected")

        results.append(
            {
                "source_way_id": record["source_way_id"],
                "stable_blocker_id": record["stable_blocker_id"],
                "highway": record["highway"],
                "source_way_timestamp": record["source_way_timestamp"],
                "source_identifiers": record["identifiers"],
                "source_names": record["names"],
                "match_category": category,
                "selected_candidate": selected,
                "candidate_count_within_30m": len(candidates),
                "high_overlap_candidate_count": len(high),
                "confidence_components": {
                    "geometry_threshold_m": BUFFER_M,
                    "minimum_overlap_ratio": HIGH_OVERLAP,
                    "identifier_uniqueness": len(exact) == 1,
                    "name_agreement": bool(selected and selected["route_name_agreement"]),
                    "operator_agreement": None,
                    "temporal_alignment": False if selected else None,
                    "source_identity_conflict": source_identity_conflict,
                },
                "official_lane_semantics": lane_semantics,
                "temporal_assessment": temporal,
                "formal_eligible": formal_eligible,
                "formal_ineligibility_reasons": reasons,
                "candidates": candidates,
            }
        )

    category_counts = Counter(item["match_category"] for item in results)
    selected = [item for item in results if item["selected_candidate"]]
    compatible = [
        item for item in selected
        if item["official_lane_semantics"] == "active_direction_moving_lane_count"
    ]
    aggregates = {
        "population_count": len(results),
        "match_category_counts": dict(sorted(category_counts.items())),
        "match_category_highway_counts": {
            category: dict(sorted(Counter(
                item["highway"] for item in results if item["match_category"] == category
            ).items()))
            for category in sorted(category_counts)
        },
        "high_confidence_identity_geometry_count": len(selected),
        "direction_semantics_compatible_count": len(compatible),
        "direction_semantics_compatible_way_ids": [item["source_way_id"] for item in compatible],
        "both_directions_total_incompatible_count": sum(
            item["official_lane_semantics"] == "both_directions_total_not_assignable_to_split_osm_way"
            for item in selected
        ),
        "formal_eligible_count": sum(item["formal_eligible"] for item in results),
        "expected_immediate_blocker_reduction": 0,
        "records_semantic_sha256": canonical_sha(results),
    }
    return results, aggregates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", required=True, type=Path)
    parser.add_argument("--tokyo-csv", required=True, type=Path)
    parser.add_argument("--kanagawa-csv", required=True, type=Path)
    parser.add_argument("--tile-dir", required=True, type=Path)
    parser.add_argument("--assessment-output", required=True, type=Path)
    parser.add_argument("--aggregates-output", required=True, type=Path)
    args = parser.parse_args()
    for output in (args.assessment_output, args.aggregates_output):
        if output.exists():
            raise FileExistsError(f"immutable output already exists: {output}")

    population = json.loads(args.population.read_text(encoding="utf-8"))
    rows = load_rows([args.tokyo_csv, args.kanagawa_csv])
    features = load_features(args.tile_dir, rows)
    results, aggregates = assess(population, features)
    assessment = {
        "schema_version": 1,
        "investigation_id": population["investigation_id"],
        "status": "investigation_only_no_formal_lane_materialization",
        "method": {
            "source": "MLIT R3 Road Traffic Census location-specific survey CSV and official web-map geometry",
            "projection": "EPSG:6677",
            "nearby_candidate_distance_m": NEARBY_M,
            "geometry_buffer_m": BUFFER_M,
            "high_overlap_ratio": HIGH_OVERLAP,
            "threshold_status": "candidate_for_decision_not_approved_runtime_policy",
        },
        "source_files": {
            str(path): file_sha(path)
            for path in (args.population, args.tokyo_csv, args.kanagawa_csv)
        },
        "official_feature_count_in_tile_extent": len(features),
        "aggregates": aggregates,
        "records": results,
    }
    args.assessment_output.write_text(
        json.dumps(assessment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.aggregates_output.write_text(
        json.dumps(aggregates, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(aggregates, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
