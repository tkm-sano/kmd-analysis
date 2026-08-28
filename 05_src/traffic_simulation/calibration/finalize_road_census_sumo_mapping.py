#!/usr/bin/env python3
"""Render and finalize the Ota Road Census manual corridor review.

The decisions in this module are intentionally explicit.  They are not
inferred by relaxing matching thresholds.  Regenerating the outputs therefore
preserves the reviewed decision provenance separately from automatic matching.
"""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import folium
from folium.plugins import PolyLineTextPath
from pyproj import Transformer
from shapely.ops import transform, unary_union

from traffic_simulation.calibration.road_census_sumo_pipeline import (
    DEFAULT_CONFIG,
    load_census_geometries,
    load_config,
    load_osm_way_tags,
    load_sumo_edges,
    parse_sumo_location,
    sha256_file,
    write_csv,
)
from traffic_simulation.paths import REPOSITORY_ROOT


MANUAL_SECTION_IDS = {
    "13200510010", "13200510020", "13200520010", "13200520020", "13200520030",
    "13301310010", "13301310030", "13400060010", "13400110050", "13403110040",
    "13200100080", "13200100090", "13200100100", "13200100110", "13200100120",
    "13201100010", "13300010330", "13303570270", "13303570280", "13303570290",
    "13400020060", "13400110040", "13403110020", "13403160330", "13403160340",
}
AMBIGUOUS_SECTION_IDS = {
    "13300010330", "13303570270", "13303570280", "13303570290", "13400020060",
    "13400110040", "13403110020", "13403160330", "13403160340",
}

REVIEWER = "Codex-assisted visual review"
REVIEWED_AT = "2026-08-26T18:15:00+09:00"

# Explicit outcomes after inspecting the rendered MLIT/corridor/OSM overlays.
# ``corridor_id`` may differ from the automatic selection; this is the reviewed
# choice, not a threshold adjustment.
MANUAL_DECISIONS: dict[str, dict[str, str]] = {
    "13200510010": {
        "corridor_id": "13200510010_C0066", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Census route 51 and OSM ref B use different expressway numbering systems.",
        "evidence_summary": "MLIT geometry follows the Shuto Bayshore branch; all six edges are motorway/motorway_link named Bayshore branch or Route 1, with no surface-road substitution.",
    },
    "13200510020": {
        "corridor_id": "13200510020_C0031", "final_confidence": "low",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "GEOMETRY_WEAK",
        "review_reason": "The B/51 numbering mismatch is resolved, but overlap support remains below 0.40.",
        "evidence_summary": "All four edges are Shuto Bayshore motorway ref B and visually coincide with the MLIT line; coverage is 1.0, but overlap support is 0.295, so the corridor is confirmed for audit only and excluded downstream.",
    },
    "13200520010": {
        "corridor_id": "13200520010_C0011", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Census route 52 corresponds to OSM Bayshore ref B in this numbering context.",
        "evidence_summary": "Seven motorway edges named Shuto Bayshore Line follow the MLIT airport corridor continuously, including its grade-separated/tunnel portions.",
    },
    "13200520020": {
        "corridor_id": "13200520020_C0012", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Census route 52 and OSM ref B are equivalent numbering for the reviewed Bayshore segment.",
        "evidence_summary": "Four ref B motorway edges coincide with the official airport-terminal geometry; coverage is 1.0 and direction difference is 1.5 degrees.",
    },
    "13200520030": {
        "corridor_id": "13200520030_C0023", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Census route 52 is represented by OSM ref B; one unreferenced motorway_link is a continuous interchange constituent.",
        "evidence_summary": "The three-edge motorway corridor follows the official Tama River crossing to Ukishima; coverage is 1.0, while overlap support remains Medium at 0.608.",
    },
    "13301310010": {
        "corridor_id": "13301310010_C0104", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "One ref 311 edge is an intersection tag discontinuity inside an otherwise ref 131 corridor.",
        "evidence_summary": "Twenty-one of 22 edges carry ref 131 and all follow the MLIT geometry on Kannana/Hachikan-dori without switching to a parallel road.",
    },
    "13301310030": {
        "corridor_id": "13301310030_C0542", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Minor ref 15/6 tags occur at crossings within the continuous ref 131 alignment.",
        "evidence_summary": "Ninety-nine of 103 edges carry ref 131; the map confirms a continuous National Route 131/Industrial Road alignment with full MLIT coverage and no parallel-road jump.",
    },
    "13400060010": {
        "corridor_id": "13400060010_C0225", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "Two ref 131 edge tags are crossing-boundary artifacts in the Tokyo Route 6 corridor.",
        "evidence_summary": "Twenty-one of 23 edges are ref 6/Industrial Road and the complete bridge alignment coincides with the official geometry; overlap support remains Medium at 0.608.",
    },
    "13400110050": {
        "corridor_id": "13400110050_C0059", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "A single ref 111 edge is a short junction continuation inside the ref 11 alignment.",
        "evidence_summary": "Eleven of 12 edges are ref 11/Tamate-dori; the overlay shows full continuity on the same surface road with no parallel-road substitution.",
    },
    "13403110040": {
        "corridor_id": "13403110040_C0252", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "One ref 131 edge is a short intersection tagging artifact within ref 311.",
        "evidence_summary": "Fifty-four of 55 edges are ref 311 and all mapped edges follow the official Hachikan-dori curve continuously with full coverage.",
    },
    "13200100080": {
        "corridor_id": "13200100080_C0067", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unknown-ref service edge is replaced by the explicit Shuto Route 1 motorway corridor.",
        "evidence_summary": "Chosen three-edge alternative is entirely motorway, ref 1, named Shuto Expressway Route 1 Haneda Line; coverage 0.918 and overlap 0.892.",
    },
    "13200100090": {
        "corridor_id": "13200100090_C0079", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unreferenced tertiary corridor is replaced by explicit Shuto Route 1 motorway edges.",
        "evidence_summary": "Chosen seven-edge alternative is entirely motorway/ref 1/Haneda Line and covers the complete official geometry; overlap support remains Medium at 0.666.",
    },
    "13200100100": {
        "corridor_id": "13200100100_C0038", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unreferenced motorway_link is replaced by the explicit Haneda mainline.",
        "evidence_summary": "Chosen five-edge alternative is entirely motorway/ref 1/Haneda Line with coverage and overlap both 1.0 and no surface-road substitution.",
    },
    "13200100110": {
        "corridor_id": "13200100110_C0057", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unclassified way is replaced by explicit Shuto Route 1 motorway edges.",
        "evidence_summary": "Chosen three-edge motorway/ref 1/Haneda Line alternative covers the official geometry fully with overlap 0.935 and remains topologically continuous.",
    },
    "13200100120": {
        "corridor_id": "13200100120_C0024", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unclassified way is replaced by an explicit Shuto Route 1 mainline edge.",
        "evidence_summary": "Chosen motorway/ref 1/Haneda Line edge follows the official alignment with coverage 0.910; overlap support is 0.542, so confidence remains Medium.",
    },
    "13201100010": {
        "corridor_id": "13201100010_C0183", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_IDENTITY_CONFIRMED",
        "review_reason": "The automatic unclassified corridor is replaced by the continuous Shuto 1/K1 motorway across the prefectural boundary.",
        "evidence_summary": "Three motorway edges carry refs 1 and K1 and the corresponding Haneda/Yokohane names; coverage is 0.999 and overlap support remains Medium at 0.631.",
    },
    "13300010330": {
        "corridor_id": "13300010330_C0003", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "PARALLEL_ROAD_RESOLVED",
        "review_reason": "Best and runner-up are opposing carriageways of the same National Route 1 alignment.",
        "evidence_summary": "Both alternatives are ref 1/Second Keihin trunk corridors; the chosen path has slightly higher overlap and follows the full official geometry without a side-road switch.",
    },
    "13303570270": {
        "corridor_id": "13303570270_C0263", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "CORRIDOR_AMBIGUITY_RESOLVED",
        "review_reason": "The selected all-trunk Route 357 path is preferred over the runner containing six trunk_link edges.",
        "evidence_summary": "Both paths follow Tokyo Bayshore Road; the selected path has higher overlap (0.818 vs 0.762) with identical 0.508 coverage.",
    },
    "13303570280": {
        "corridor_id": "13303570280_C0020", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "CORRIDOR_AMBIGUITY_RESOLVED",
        "review_reason": "The two terminal-area alternatives share five edges; the selected branch better follows the official geometry.",
        "evidence_summary": "Both remain Route 357/trunk-link corridors with identical 0.521 coverage; selected overlap is materially higher (0.821 vs 0.682).",
    },
    "13303570290": {
        "corridor_id": "13303570290_C0012", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "PARALLEL_ROAD_RESOLVED",
        "review_reason": "The two one-edge candidates are opposing carriageways of the same Route 357 road.",
        "evidence_summary": "Both are ref 357 trunk edges on the official alignment; the selected edge has marginally higher coverage (0.5041 vs 0.5031).",
    },
    "13400020060": {
        "corridor_id": "13400020060_C0464", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "DIRECTION_RESOLVED",
        "review_reason": "The 25.484-degree aggregate difference is caused by the long curved road geometry, not a crossing-road turn.",
        "evidence_summary": "All 79 edges are ref 2/Nakahara-kaido primary and continuously overlay the full official curve; the 25-degree High threshold is not relaxed.",
    },
    "13400110040": {
        "corridor_id": "13400110040_C0171", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "DIRECTION_RESOLVED",
        "review_reason": "The 34.8-degree aggregate difference reflects the pronounced Tamate-dori bend.",
        "evidence_summary": "Twenty-eight of 29 edges are ref 11/Tamate-dori primary; the map shows full continuous coverage around the curve and no crossing-road inclusion.",
    },
    "13403110020": {
        "corridor_id": "13403110020_C0003", "final_confidence": "high",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "ROUTE_MISMATCH_RESOLVED",
        "review_reason": "A full-coverage Route 311 path was ranked below a partial Medium edge because one short terminal edge is tagged ref 131.",
        "evidence_summary": "C0003 is a 12-edge continuous mainline corridor with coverage 0.996 (3047.3 of 3059.9 geometry-metres; only 12.7 m uncovered), overlap 0.840 and direction difference 11.1 degrees; 11 edges are ref 311/Hachikan-dori and the sole ref 131 edge retains the same Hachikan-dori name at the section boundary. It has zero SUMO connection violations. C0002 was rejected because it diverts through Haneda Connecting Road/primary_link edges, while C0117 is the opposing carriageway. The official geometry is at least 6.29 km inside every SUMO network boundary, excluding a study-area boundary cause.",
        "coverage_shortfall_classification": "3",
        "coverage_shortfall_cause": "The 0.365 automatic result was a confidence-ranking artifact: full paths C0003/C0117 were present and continuous but classified Low by one boundary ref mismatch, so the partial Medium singleton C0099 ranked first. C0003 covers 0.996 with only 12.7 m uncovered and is at least 6.29 km inside every SUMO network boundary; therefore neither network loss nor the study-area boundary caused the shortfall.",
    },
    "13403160330": {
        "corridor_id": "13403160330_C0103", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "CORRIDOR_AMBIGUITY_RESOLVED",
        "review_reason": "The all-primary runner is chosen instead of the automatic path containing service/unclassified edges.",
        "evidence_summary": "Reviewed corridor contains nine ref 316/Kaigan-dori primary edges, avoiding side-road constituents; coverage 0.501 and overlap 0.906 remain Medium.",
    },
    "13403160340": {
        "corridor_id": "13403160340_C0027", "final_confidence": "medium",
        "review_decision": "MANUAL_CONFIRMED", "review_reason_code": "CORRIDOR_AMBIGUITY_RESOLVED",
        "review_reason": "The all-primary runner is chosen instead of the automatic path containing a motorway_link edge.",
        "evidence_summary": "Reviewed corridor contains four ref 316/Kaigan-dori primary edges on the official alignment; coverage remains 0.503 and overlap 0.727.",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _latlon_parts(geometry: Any, inverse_transformer: Transformer, offset_x: float, offset_y: float) -> list[list[tuple[float, float]]]:
    projected = transform(lambda x, y, z=None: (x - offset_x, y - offset_y), geometry)
    wgs84 = transform(inverse_transformer.transform, projected)
    parts = [wgs84] if wgs84.geom_type == "LineString" else list(wgs84.geoms)
    return [[(lat, lon) for lon, lat in part.coords] for part in parts]


def _add_directed_edges(
    feature_group: folium.FeatureGroup, edge_ids: list[str], edges: dict[str, dict[str, Any]],
    inverse_transformer: Transformer, offset_x: float, offset_y: float, color: str, label: str,
    dash_array: str | None = None,
) -> list[tuple[float, float]]:
    bounds: list[tuple[float, float]] = []
    for edge_id in edge_ids:
        edge = edges[edge_id]
        tooltip = (
            f"{label} | edge={edge_id} | ref={edge.get('ref') or 'blank'} | "
            f"name={edge.get('name') or 'blank'} | highway={edge.get('highway') or 'blank'}"
        )
        for locations in _latlon_parts(edge["geometry"], inverse_transformer, offset_x, offset_y):
            line = folium.PolyLine(
                locations, color=color, weight=6, opacity=0.85, dash_array=dash_array,
                tooltip=tooltip,
            ).add_to(feature_group)
            PolyLineTextPath(
                line, "  ▶  ", repeat=True, offset=7,
                attributes={"fill": color, "font-size": "13", "font-weight": "bold"},
            ).add_to(feature_group)
            bounds.extend(locations)
    return bounds


def _tag_summary(edge_ids: list[str], edges: dict[str, dict[str, Any]]) -> str:
    def summarize(field: str) -> str:
        values = Counter(edges[edge_id].get(field) or "blank" for edge_id in edge_ids)
        return ", ".join(f"{value}:{count}" for value, count in values.most_common(4))
    return f"ref[{summarize('ref')}] name[{summarize('name')}] highway[{summarize('highway')}]"


def render_review_maps(
    config_path: Path = DEFAULT_CONFIG,
    section_ids: set[str] | None = None,
) -> Path:
    rendered_section_ids = section_ids or MANUAL_SECTION_IDS
    config = load_config(config_path)
    paths = config["inputs"]
    output_dir = REPOSITORY_ROOT / config["outputs"]["directory"]
    map_dir = output_dir / "manual_review_maps"
    map_dir.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(REPOSITORY_ROOT / paths["sumo_net_xml"])
    transformer, offset_x, offset_y = parse_sumo_location(tree.getroot())
    inverse_transformer = Transformer.from_crs(transformer.target_crs, 4326, always_xy=True)
    osm_tags = load_osm_way_tags(REPOSITORY_ROOT / paths["source_osm_xml"])
    edges = {
        row["sumo_edge_id"]: row
        for row in load_sumo_edges(REPOSITORY_ROOT / paths["sumo_net_xml"], osm_tags)
    }
    census_dir = REPOSITORY_ROOT / paths["road_census_dir"]
    geometries = load_census_geometries(
        census_dir / paths["section_geometry_dir"], rendered_section_ids,
        transformer, offset_x, offset_y,
    )
    corridors: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(output_dir / "census_section_corridor_mapping.csv"):
        if row["section_id"] in rendered_section_ids:
            corridors[row["section_id"]].append(row)

    for section_id in sorted(rendered_section_ids):
        rows = corridors[section_id]
        automatic_selected = next(row for row in rows if row["selected"] == "True")
        reviewed_corridor_id = MANUAL_DECISIONS[section_id]["corridor_id"]
        selected = (
            next(row for row in rows if row["candidate_corridor_id"] == reviewed_corridor_id)
            if reviewed_corridor_id else automatic_selected
        )
        runner = None
        if selected["candidate_corridor_id"] != automatic_selected["candidate_corridor_id"]:
            runner = automatic_selected
        elif section_id in AMBIGUOUS_SECTION_IDS:
            runner = next(
                row for row in rows
                if row["candidate_corridor_id"] != selected["candidate_corridor_id"]
                and row["confidence"] == selected["confidence"]
            )
        best_ids = selected["corridor_edge_ids"].split(";")
        runner_ids = runner["corridor_edge_ids"].split(";") if runner else []
        official_parts = _latlon_parts(geometries[section_id], inverse_transformer, offset_x, offset_y)
        flat_official = [point for part in official_parts for point in part]
        center_lat = sum(point[0] for point in flat_official) / len(flat_official)
        center_lon = sum(point[1] for point in flat_official) / len(flat_official)
        review_map = folium.Map(location=[center_lat, center_lon], zoom_start=15, control_scale=True)
        official_group = folium.FeatureGroup(name="MLIT official geometry", show=True).add_to(review_map)
        for locations in official_parts:
            folium.PolyLine(
                locations, color="#111111", weight=10, opacity=0.6,
                tooltip=f"MLIT official geometry: {section_id}",
            ).add_to(official_group)
        best_group = folium.FeatureGroup(name="Reviewed corridor", show=True).add_to(review_map)
        bounds = list(flat_official)
        bounds.extend(_add_directed_edges(
            best_group, best_ids, edges, inverse_transformer, offset_x, offset_y,
            "#0072B2", "REVIEWED",
        ))
        if runner:
            runner_group = folium.FeatureGroup(name="Compared corridor", show=True).add_to(review_map)
            bounds.extend(_add_directed_edges(
                runner_group, runner_ids, edges, inverse_transformer, offset_x, offset_y,
                "#D55E00", "COMPARED", "10 8",
            ))
        if section_id == "13403110020":
            special_layers = [
                ("Automatic second C0105", "13403110020_C0105", "#CC79A7", "AUTO_SECOND"),
                ("Opposing full corridor C0117", "13403110020_C0117", "#009E73", "OPPOSING_FULL"),
            ]
            for layer_name, corridor_id, color, label in special_layers:
                special = next(row for row in rows if row["candidate_corridor_id"] == corridor_id)
                group = folium.FeatureGroup(name=layer_name, show=True).add_to(review_map)
                bounds.extend(_add_directed_edges(
                    group, special["corridor_edge_ids"].split(";"), edges,
                    inverse_transformer, offset_x, offset_y, color, label, "6 7",
                ))
            diverting = next(row for row in rows if row["candidate_corridor_id"] == "13403110020_C0002")
            diverting_group = folium.FeatureGroup(
                name="Rejected full path C0002 (Haneda Connecting Road)", show=False
            ).add_to(review_map)
            _add_directed_edges(
                diverting_group, diverting["corridor_edge_ids"].split(";"), edges,
                inverse_transformer, offset_x, offset_y, "#F0E442", "REJECTED_DIVERSION", "3 7",
            )
            uncovered = geometries[section_id].difference(
                unary_union([edges[edge_id]["geometry"] for edge_id in best_ids]).buffer(25.0)
            )
            uncovered_group = folium.FeatureGroup(
                name="Official geometry not covered by reviewed corridor", show=True
            ).add_to(review_map)
            for locations in _latlon_parts(uncovered, inverse_transformer, offset_x, offset_y):
                folium.PolyLine(
                    locations, color="#FF00FF", weight=12, opacity=0.9,
                    tooltip="Uncovered official geometry after 25 m buffer",
                ).add_to(uncovered_group)
            all_bounds = [edge["geometry"].bounds for edge in edges.values()]
            min_x = min(value[0] for value in all_bounds)
            min_y = min(value[1] for value in all_bounds)
            max_x = max(value[2] for value in all_bounds)
            max_y = max(value[3] for value in all_bounds)
            west, south = inverse_transformer.transform(min_x - offset_x, min_y - offset_y)
            east, north = inverse_transformer.transform(max_x - offset_x, max_y - offset_y)
            boundary_group = folium.FeatureGroup(name="SUMO network bounding box", show=False).add_to(review_map)
            folium.Rectangle(
                bounds=[(south, west), (north, east)], color="#666666", weight=2,
                fill=False, dash_array="8 6", tooltip="SUMO network bounding box",
            ).add_to(boundary_group)
        details = (
            f"<b>{section_id}</b><br>reviewed={selected['candidate_corridor_id']} ({MANUAL_DECISIONS[section_id]['final_confidence']})<br>"
            f"coverage={float(selected['corridor_coverage_ratio']):.3f}, "
            f"overlap={float(selected['overlap_support']):.3f}, "
            f"direction={float(selected['direction_difference']):.1f}&deg;, "
            f"route={selected['route_match_status']}<br>REVIEWED {_tag_summary(best_ids, edges)}"
        )
        if runner:
            details += (
                f"<br>compared={runner['candidate_corridor_id']}: coverage={float(runner['corridor_coverage_ratio']):.3f}, "
                f"overlap={float(runner['overlap_support']):.3f}, "
                f"direction={float(runner['direction_difference']):.1f}&deg;<br>COMPARED {_tag_summary(runner_ids, edges)}"
            )
        if section_id == "13403110020":
            details += (
                "<br><b>Resolution:</b> C0003 covers 0.996. Auto best C0099 covers 0.365; "
                "auto second C0105 covers 0.319. C0117 is the opposing full carriageway. "
                "C0002 is available as a hidden layer but rejected for diverting through Haneda Connecting Road."
            )
        review_map.get_root().html.add_child(folium.Element(
            '<div style="position:fixed;top:10px;left:50px;z-index:9999;background:white;'
            'padding:8px;border:1px solid #777;font:12px sans-serif;max-width:80%;">'
            + details + "</div>"
        ))
        folium.LayerControl(collapsed=False).add_to(review_map)
        review_map.fit_bounds(bounds, padding=(25, 25))
        review_map.save(map_dir / f"{section_id}.html")
    return map_dir


def finalize_mapping(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    paths = config["inputs"]
    output_dir = REPOSITORY_ROOT / config["outputs"]["directory"]
    corridor_rows = read_csv(output_dir / "census_section_corridor_mapping.csv")
    by_section: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_corridor_id: dict[str, dict[str, str]] = {}
    for row in corridor_rows:
        by_section[row["section_id"]].append(row)
        by_corridor_id[row["candidate_corridor_id"]] = row

    section_ids = set(by_section)
    if len(section_ids) != 66:
        raise ValueError(f"expected 66 Ota sections, found {len(section_ids)}")
    automatic_selected = {
        section_id: next(row for row in rows if row["selected"] == "True")
        for section_id, rows in by_section.items()
    }
    automatic_manual = {
        section_id for section_id, row in automatic_selected.items()
        if row["manual_review_required"] == "True"
    }
    if automatic_manual != MANUAL_SECTION_IDS or set(MANUAL_DECISIONS) != MANUAL_SECTION_IDS:
        raise ValueError("manual decision register does not exactly cover the 25 review sections")

    allowed_reason_codes = {
        "ROUTE_MISMATCH_RESOLVED", "ROUTE_IDENTITY_CONFIRMED", "ROUTE_IDENTITY_UNRESOLVED",
        "PARALLEL_ROAD_RESOLVED", "DIRECTION_RESOLVED", "CORRIDOR_AMBIGUITY_RESOLVED",
        "GEOMETRY_WEAK", "OTHER",
    }
    final_rows: list[dict[str, Any]] = []
    review_log: list[dict[str, Any]] = []
    image_review_log: list[dict[str, Any]] = []
    for section_id in sorted(section_ids):
        auto = automatic_selected[section_id]
        if section_id not in MANUAL_SECTION_IDS:
            decision_origin = "AUTO_HIGH" if auto["confidence"] == "high" else "AUTO_MEDIUM"
            final_corridor = auto
            final_confidence = auto["confidence"]
            manual_reviewed = False
            reason_code = "OTHER"
        else:
            decision = MANUAL_DECISIONS[section_id]
            if decision["review_reason_code"] not in allowed_reason_codes:
                raise ValueError(f"unsupported review reason code for {section_id}")
            decision_origin = decision["review_decision"]
            final_confidence = decision["final_confidence"]
            manual_reviewed = True
            reason_code = decision["review_reason_code"]
            final_corridor = (
                by_corridor_id[decision["corridor_id"]]
                if decision["corridor_id"] else None
            )
            if final_corridor is not None and final_corridor["section_id"] != section_id:
                raise ValueError(f"reviewed corridor belongs to a different section: {section_id}")
            review_log.append({
                "section_id": section_id,
                "automatic_corridor_id": auto["candidate_corridor_id"],
                "final_corridor_id": decision["corridor_id"],
                "final_edge_ids": final_corridor["corridor_edge_ids"] if final_corridor else "",
                "final_confidence": final_confidence,
                "decision_origin": "manual_visual_review",
                "review_reason_code": reason_code,
                "review_decision": decision_origin,
                "review_reason": decision["review_reason"],
                "evidence_summary": decision["evidence_summary"],
                "coverage_shortfall_classification": decision.get("coverage_shortfall_classification", ""),
                "coverage_shortfall_cause": decision.get("coverage_shortfall_cause", ""),
                "reviewer": REVIEWER,
                "reviewed_at": REVIEWED_AT,
                "map_artifact": f"manual_review_maps/{section_id}.html",
                "review_image_artifact": f"manual_review_maps/{section_id}.png",
                "review_map_sha256": "",
                "review_image_sha256": "",
            })
        usable = bool(
            final_corridor is not None
            and final_confidence in {"high", "medium"}
            and decision_origin not in {"MANUAL_REJECTED", "UNRESOLVED"}
        )
        final_rows.append({
            "section_id": section_id,
            "final_corridor_id": final_corridor["candidate_corridor_id"] if final_corridor else "",
            "final_edge_ids": final_corridor["corridor_edge_ids"] if final_corridor else "",
            "final_confidence": final_confidence,
            "decision_origin": decision_origin,
            "manual_reviewed": manual_reviewed,
            "review_reason_code": reason_code,
            "usable_for_lane_projection": usable,
            "usable_for_traffic_assignment": usable,
        })

    net_root = ET.parse(REPOSITORY_ROOT / paths["sumo_net_xml"]).getroot()
    connections = {
        (element.get("from", ""), element.get("to", ""))
        for element in net_root.findall("connection")
    }
    connection_violations: list[dict[str, str]] = []
    for row in final_rows:
        edge_ids = row["final_edge_ids"].split(";") if row["final_edge_ids"] else []
        for left, right in zip(edge_ids, edge_ids[1:]):
            if (left, right) not in connections:
                connection_violations.append({"section_id": row["section_id"], "from_edge": left, "to_edge": right})
    if connection_violations:
        raise ValueError(f"final mapping has SUMO connection violations: {connection_violations[:3]}")
    if len(final_rows) != len({row["section_id"] for row in final_rows}):
        raise ValueError("final mapping is not unique by section")

    for log_row in review_log:
        section_id = log_row["section_id"]
        html_path = output_dir / log_row["map_artifact"]
        png_path = output_dir / log_row["review_image_artifact"]
        if not html_path.exists() or not png_path.exists():
            raise FileNotFoundError(f"review evidence is missing for {section_id}")
        log_row["review_map_sha256"] = sha256_file(html_path)
        log_row["review_image_sha256"] = sha256_file(png_path)
        auto = automatic_selected[section_id]
        reviewed_id = log_row["final_corridor_id"]
        if reviewed_id and reviewed_id != auto["candidate_corridor_id"]:
            compared_id = auto["candidate_corridor_id"]
        elif section_id in AMBIGUOUS_SECTION_IDS:
            compared_id = next(
                row["candidate_corridor_id"] for row in by_section[section_id]
                if row["candidate_corridor_id"] != auto["candidate_corridor_id"]
                and row["confidence"] == auto["confidence"]
            )
        else:
            compared_id = ""
        image_review_log.append({
            "section_id": section_id,
            "reviewed_corridor_id": reviewed_id,
            "displayed_primary_corridor_id": reviewed_id or auto["candidate_corridor_id"],
            "compared_corridor_id": compared_id,
            "additional_compared_corridor_ids": (
                "13403110020_C0105;13403110020_C0117;13403110020_C0002"
                if section_id == "13403110020" else ""
            ),
            "review_image_png": log_row["review_image_artifact"],
            "review_map_html": log_row["map_artifact"],
            "png_sha256": log_row["review_image_sha256"],
            "html_sha256": log_row["review_map_sha256"],
            "displayed_layers": (
                "MLIT_official_geometry;reviewed_corridor;automatic_best;automatic_second;opposing_full_corridor;"
                "rejected_diversion;uncovered_geometry;SUMO_network_boundary;constituent_edge_direction;OSM_basemap"
                if section_id == "13403110020" else
                "MLIT_official_geometry;reviewed_corridor;compared_corridor;constituent_edge_direction;OSM_basemap"
            ),
            "visual_check_items": "alignment;parallel_road;mainline_side_road;grade_separation;route_continuity;over_extension;coverage_gap",
            "visual_observation": log_row["evidence_summary"],
            "coverage_shortfall_classification": log_row["coverage_shortfall_classification"],
            "coverage_shortfall_cause": log_row["coverage_shortfall_cause"],
            "image_review_status": "INSPECTED",
            "review_decision": log_row["review_decision"],
            "reviewer": REVIEWER,
            "reviewed_at": REVIEWED_AT,
        })

    decision_counts = Counter(row["decision_origin"] for row in final_rows)
    usable_mapping_count = sum(bool(row["final_corridor_id"]) and row["final_confidence"] in {"high", "medium"} for row in final_rows)
    lane_count = sum(row["usable_for_lane_projection"] for row in final_rows)
    traffic_count = sum(row["usable_for_traffic_assignment"] for row in final_rows)
    summary = {
        "section_count": len(final_rows),
        "decision_counts": {
            key: decision_counts.get(key, 0)
            for key in ("AUTO_HIGH", "AUTO_MEDIUM", "MANUAL_CONFIRMED", "MANUAL_REJECTED", "UNRESOLVED")
        },
        "final_usable_mapping_section_count": usable_mapping_count,
        "lane_projection_usable_section_count": lane_count,
        "traffic_assignment_usable_section_count": traffic_count,
        "not_usable_for_lane_projection_section_count": len(final_rows) - lane_count,
        "not_usable_for_traffic_assignment_section_count": len(final_rows) - traffic_count,
        "not_usable_section_ids": [
            row["section_id"] for row in final_rows if not row["usable_for_lane_projection"]
        ],
        "unresolved_section_ids": [
            row["section_id"] for row in final_rows if row["decision_origin"] == "UNRESOLVED"
        ],
        "confirmed_but_not_usable_section_ids": [
            row["section_id"] for row in final_rows
            if row["decision_origin"] == "MANUAL_CONFIRMED" and not row["usable_for_lane_projection"]
        ],
        "final_confidence_counts": dict(Counter(row["final_confidence"] for row in final_rows)),
        "manual_review_section_count": len(review_log),
        "review_image_count": len(image_review_log),
        "review_image_inspected_count": sum(
            row["image_review_status"] == "INSPECTED" for row in image_review_log
        ),
        "final_mapping_unique_by_section": True,
        "selected_corridor_sumo_connection_violation_count": 0,
        "reviewer": REVIEWER,
        "reviewed_at": REVIEWED_AT,
    }
    write_csv(output_dir / "census_section_final_mapping.csv", final_rows, [
        "section_id", "final_corridor_id", "final_edge_ids", "final_confidence", "decision_origin",
        "manual_reviewed", "review_reason_code", "usable_for_lane_projection", "usable_for_traffic_assignment",
    ])
    write_csv(output_dir / "census_manual_review_log.csv", review_log, [
        "section_id", "automatic_corridor_id", "final_corridor_id", "final_edge_ids", "final_confidence",
        "decision_origin", "review_reason_code", "review_decision", "review_reason", "evidence_summary",
        "coverage_shortfall_classification", "coverage_shortfall_cause", "reviewer", "reviewed_at",
        "map_artifact", "review_image_artifact", "review_map_sha256", "review_image_sha256",
    ])
    write_csv(output_dir / "census_manual_review_image_log.csv", image_review_log, [
        "section_id", "reviewed_corridor_id", "displayed_primary_corridor_id", "compared_corridor_id",
        "additional_compared_corridor_ids", "review_image_png", "review_map_html", "png_sha256",
        "html_sha256", "displayed_layers", "visual_check_items", "visual_observation",
        "coverage_shortfall_classification", "coverage_shortfall_cause", "image_review_status",
        "review_decision", "reviewer", "reviewed_at",
    ])
    (output_dir / "census_final_mapping_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()
    if args.render_only:
        print(render_review_maps(args.config))
    else:
        print(json.dumps(finalize_mapping(args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
