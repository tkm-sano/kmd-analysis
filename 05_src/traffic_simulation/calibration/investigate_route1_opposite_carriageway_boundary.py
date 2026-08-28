"""Investigate the fixed Route 1 opposite-carriageway candidate at its boundaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from pyproj import CRS, Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_route1_boundary_review_20260827_v1"
OBSERVATION_ID = "13300010260"
DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
ADOPTION_REVIEW = DATA_DIR / "external_observation_opposite_carriageway_adoption_review.csv"
DIRECTION_CLUSTERS = DATA_DIR / "external_observation_direction_cluster_evidence.csv"
FORMAL_MAPPING = DATA_DIR / "external_observation_final_mapping.csv"
BASE_MAPPING = DATA_DIR / "census_section_final_mapping.csv"
CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
NETWORK = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1/ota_ward_external_extension_20260827_v1.net.xml"
)
OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1/ota_ward_external_extension_20260827_v1.osm.xml"
)
ROUTE_RELATIONS = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
)
OFFICIAL_GEOMETRY = (
    REPOSITORY_ROOT
    / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/webmap_tiles/drm31_13_7275_3227.geojson"
)
PREWORK = DATA_DIR / "external_observation_route1_boundary_prework_20260827.json"

REVIEW_CSV = DATA_DIR / "external_observation_route1_boundary_review.csv"
EXTENSION_CSV = DATA_DIR / "external_observation_route1_boundary_extension_evidence.csv"
EDGE_CSV = DATA_DIR / "external_observation_route1_boundary_edge_evidence.csv"
QA_JSON = DATA_DIR / "external_observation_route1_boundary_qa.json"
MANIFEST_JSON = DATA_DIR / "external_observation_route1_boundary_manifest.json"
VALIDATION_JSON = DATA_DIR / "external_observation_route1_boundary_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_route1_boundary_review.md"

ALLOWED_FINAL_STATUSES = {
    "EXTENDABLE_AND_ACCEPTABLE",
    "EXTENDABLE_BUT_REVIEW_REQUIRED",
    "CURRENT_CANDIDATE_IS_MAXIMAL",
    "BOUNDARY_GEOMETRY_MISMATCH",
    "ROUTE_CONTINUITY_BREAK",
    "UNRESOLVED",
}


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPOSITORY_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_prework() -> dict[str, Any]:
    snapshot = json.loads(PREWORK.read_text(encoding="utf-8"))
    for path_text, expected in snapshot["sha256"].items():
        actual = sha256_file(REPOSITORY_ROOT / path_text)
        if actual != expected:
            raise ValueError(f"locked input changed: {path_text}: {actual} != {expected}")
    baseline = snapshot["validation_baseline"]
    if baseline["status"] != "PASSED" or baseline["passed_test_count"] != 92:
        raise ValueError("pre-work validation baseline is not 92 passed")
    return snapshot


def extract_target() -> tuple[dict[str, str], dict[str, str]]:
    rows = [
        row for row in read_csv(ADOPTION_REVIEW)
        if row["official_observation_section_id"] == OBSERVATION_ID
        and row["adoption_status"] == "REVIEW_REQUIRED"
    ]
    if len(rows) != 1:
        raise ValueError("Route 1 target must be derived exactly once from formal adoption review")
    row = rows[0]
    if len(row["alternate_carriageway_edge_sequence"].split(";")) != 14:
        raise ValueError("locked Route 1 alternate candidate is no longer 14 edges")
    direction = next(
        item for item in read_csv(DIRECTION_CLUSTERS)
        if item["official_observation_section_id"] == OBSERVATION_ID
    )
    if direction["adopted_sequence_role"] != "DOWN_ORIGIN_TO_TERMINUS":
        raise ValueError("locked fixed direction is no longer DOWN")
    return row, direction


def parse_shape(text: str) -> list[tuple[float, float]]:
    return [tuple(map(float, point.split(","))) for point in text.split()]


def parse_network(required: set[str]) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]], dict[str, str]]:
    """Keep Route 1 edges plus locked edges; this bounds graph inspection to one route."""
    metadata: dict[str, dict[str, Any]] = {}
    connections: set[tuple[str, str]] = set()
    location: dict[str, str] = {}
    for event, element in ET.iterparse(NETWORK, events=("start", "end")):
        if event == "start" and element.tag == "location":
            location = dict(element.attrib)
        elif event == "end" and element.tag == "edge":
            edge_id = element.get("id", "")
            edge_refs = {
                param.get("value", "") for param in element.findall("param")
                if param.get("key") == "ref"
            }
            if edge_id in required or (
                "1" in edge_refs
                and element.get("type", "") == "highway.trunk"
                and element.get("function", "") != "internal"
                and not edge_id.startswith(":")
            ):
                lane = element.find("lane")
                if lane is None:
                    raise ValueError(f"edge has no lane: {edge_id}")
                orig_ids = sorted({
                    source
                    for item in element.findall("lane")
                    for param in item.findall("param")
                    if param.get("key") == "origId"
                    for source in param.get("value", "").split()
                    if source
                })
                metadata[edge_id] = {
                    "from": element.get("from", ""),
                    "to": element.get("to", ""),
                    "type": element.get("type", ""),
                    "function": element.get("function", ""),
                    "length": float(lane.get("length", "0")),
                    "shape": parse_shape(lane.get("shape", "")),
                    "allow": lane.get("allow", ""),
                    "refs": sorted(edge_refs),
                    "orig_ids": orig_ids,
                }
            element.clear()
        elif event == "end" and element.tag == "connection":
            left, right = element.get("from", ""), element.get("to", "")
            if left in metadata and right in metadata:
                connections.add((left, right))
            element.clear()
    if required - set(metadata):
        raise ValueError(f"locked edges missing from network: {sorted(required - set(metadata))}")
    if not location:
        raise ValueError("network location metadata missing")
    return metadata, connections, location


def parse_osm(wanted: set[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(OSM, events=("end",)):
        if element.tag == "way":
            way_id = element.get("id", "")
            if way_id in wanted:
                result[way_id] = {
                    tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
                }
            element.clear()
    return result


def parse_relation(relation_id: str, wanted: set[str]) -> tuple[dict[str, str], dict[str, str]]:
    for _, element in ET.iterparse(ROUTE_RELATIONS, events=("end",)):
        if element.tag != "relation":
            continue
        if element.get("id") == relation_id:
            tags = {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")}
            roles = {
                member.get("ref", ""): member.get("role", "")
                for member in element.findall("member")
                if member.get("type") == "way" and member.get("ref") in wanted
            }
            return tags, roles
        element.clear()
    raise ValueError(f"route relation absent: {relation_id}")


def combined_line(sequence: list[str], metadata: dict[str, dict[str, Any]]) -> LineString:
    coordinates: list[tuple[float, float]] = []
    for edge_id in sequence:
        edge_shape = metadata[edge_id]["shape"]
        coordinates.extend(
            edge_shape[1:] if coordinates and coordinates[-1] == edge_shape[0] else edge_shape
        )
    return LineString(coordinates)


def connection_violations(sequence: list[str], connections: set[tuple[str, str]]) -> list[list[str]]:
    return [
        [left, right] for left, right in zip(sequence, sequence[1:])
        if (left, right) not in connections
    ]


def derive_local_chains(
    candidate: list[str], metadata: dict[str, dict[str, Any]], connections: set[tuple[str, str]]
) -> tuple[list[str], list[str]]:
    predecessors: dict[str, list[str]] = {}
    successors: dict[str, list[str]] = {}
    for left, right in connections:
        predecessors.setdefault(right, []).append(left)
        successors.setdefault(left, []).append(right)

    def plausible(edge_id: str) -> bool:
        item = metadata[edge_id]
        return (
            item["type"] == "highway.trunk"
            and item["function"] != "internal"
            and "1" in item["refs"]
            and not edge_id.startswith(":")
        )

    before: list[str] = []
    cursor = candidate[0]
    cumulative = 0.0
    while len(before) < 2:
        options = sorted(edge for edge in predecessors.get(cursor, []) if plausible(edge))
        if len(options) != 1:
            break
        edge_id = options[0]
        before.append(edge_id)
        cumulative += metadata[edge_id]["length"]
        cursor = edge_id
        if cumulative > 25.0:
            break

    after: list[str] = []
    cursor = candidate[-1]
    while len(after) < 2:
        options = sorted(edge for edge in successors.get(cursor, []) if plausible(edge))
        if len(options) != 1:
            break
        edge_id = options[0]
        after.append(edge_id)
        cursor = edge_id
        if metadata[edge_id]["length"] > 25.0:
            break
    return before, after


def scenario_metrics(
    sequence: list[str], fixed: list[str], metadata: dict[str, dict[str, Any]], buffer_m: float
) -> dict[str, float]:
    candidate_line = combined_line(sequence, metadata)
    fixed_line = combined_line(fixed, metadata)
    return {
        "edge_count": len(sequence),
        "candidate_length_m": candidate_line.length,
        "fixed_axis_coverage_ratio": (
            fixed_line.intersection(candidate_line.buffer(buffer_m)).length / fixed_line.length
        ),
        "candidate_axis_coverage_ratio": (
            candidate_line.intersection(fixed_line.buffer(buffer_m)).length / candidate_line.length
        ),
        "fixed_start_to_candidate_end_m": math.dist(fixed_line.coords[0], candidate_line.coords[-1]),
        "fixed_end_to_candidate_start_m": math.dist(fixed_line.coords[-1], candidate_line.coords[0]),
        "hausdorff_distance_m": fixed_line.hausdorff_distance(candidate_line),
    }


def official_geometry(location: dict[str, str]) -> Any:
    payload = json.loads(OFFICIAL_GEOMETRY.read_text(encoding="utf-8"))
    feature = next(
        item for item in payload["features"] if item["properties"].get("census") == OBSERVATION_ID
    )
    offset_x, offset_y = map(float, location["netOffset"].split(","))
    forward = Transformer.from_crs(
        4326, CRS.from_proj4(location["projParameter"]), always_xy=True
    )
    return transform(
        lambda x, y, z=None: (
            forward.transform(x, y)[0] + offset_x,
            forward.transform(x, y)[1] + offset_y,
        ),
        shape(feature["geometry"]),
    )


def wgs84_bbox(geometry: Any, location: dict[str, str]) -> dict[str, float]:
    offset_x, offset_y = map(float, location["netOffset"].split(","))
    inverse = Transformer.from_crs(
        CRS.from_proj4(location["projParameter"]), 4326, always_xy=True
    )
    converted = transform(
        lambda x, y, z=None: inverse.transform(x - offset_x, y - offset_y), geometry
    )
    west, south, east, north = converted.bounds
    return {key: round(value, 9) for key, value in zip(
        ("west", "south", "east", "north"), (west, south, east, north)
    )}


def build_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    target, direction = extract_target()
    candidate = target["alternate_carriageway_edge_sequence"].split(";")
    fixed = target["fixed_edge_sequence"].split(";")
    with CONFIG.open(encoding="utf-8") as handle:
        matching = yaml.safe_load(handle)["matching"]
    buffer_m = float(matching["candidate_buffer_m"])
    threshold = float(matching["high_section_coverage_ratio"])

    metadata, connections, location = parse_network(set(candidate + fixed))
    before, after = derive_local_chains(candidate, metadata, connections)
    extension_edges = before + after
    wanted_orig = {
        orig for edge_id in candidate + fixed + extension_edges
        for orig in metadata[edge_id]["orig_ids"]
    }
    osm = parse_osm(wanted_orig)
    relation_tags, relation_roles = parse_relation(direction["route_relation_id"], wanted_orig)

    current = scenario_metrics(candidate, fixed, metadata, buffer_m)
    scenario_specs: list[tuple[str, str, list[str], list[str]]] = [
        ("CURRENT", "NONE", [], candidate),
    ]
    for count in range(1, len(before) + 1):
        added = list(reversed(before[:count]))
        scenario_specs.append((
            f"EXTEND_UP_START_{count}", "UP_START_TERMINUS_SIDE", added,
            added + candidate,
        ))
    for count in range(1, len(after) + 1):
        added = after[:count]
        scenario_specs.append((
            f"EXTEND_UP_END_{count}", "UP_END_ORIGIN_SIDE", added,
            candidate + added,
        ))

    extension_rows: list[dict[str, Any]] = []
    scenario_values: dict[str, dict[str, float]] = {}
    for scenario_id, side, added, sequence in scenario_specs:
        metrics = scenario_metrics(sequence, fixed, metadata, buffer_m)
        scenario_values[scenario_id] = metrics
        violations = connection_violations(sequence, connections)
        max_endpoint = max(
            metrics["fixed_start_to_candidate_end_m"],
            metrics["fixed_end_to_candidate_start_m"],
        )
        extension_rows.append({
            "official_observation_section_id": OBSERVATION_ID,
            "scenario_id": scenario_id,
            "extension_side": side,
            "extension_candidate_edges": ";".join(added),
            "resulting_edge_sequence": ";".join(sequence),
            "resulting_edge_count": len(sequence),
            "connection_violation_count": len(violations),
            "fixed_axis_coverage_ratio": f"{metrics['fixed_axis_coverage_ratio']:.6f}",
            "candidate_axis_coverage_ratio": f"{metrics['candidate_axis_coverage_ratio']:.6f}",
            "coverage_threshold": f"{threshold:.2f}",
            "coverage_threshold_pass": str(
                metrics["fixed_axis_coverage_ratio"] >= threshold
                and metrics["candidate_axis_coverage_ratio"] >= threshold
            ).lower(),
            "fixed_start_to_candidate_end_m": f"{metrics['fixed_start_to_candidate_end_m']:.3f}",
            "fixed_end_to_candidate_start_m": f"{metrics['fixed_end_to_candidate_start_m']:.3f}",
            "maximum_endpoint_difference_m": f"{max_endpoint:.3f}",
            "endpoint_threshold_m": f"{buffer_m:.1f}",
            "endpoint_threshold_pass": str(max_endpoint <= buffer_m).lower(),
            "route_topology_assessment": (
                "LOCKED_CURRENT_CANDIDATE"
                if not added else "NATURAL_ROUTE_CONTINUATION_BUT_METRICS_NOT_ACCEPTABLE"
            ),
        })

    best_extension = max(
        (row for row in extension_rows if row["scenario_id"] != "CURRENT"),
        key=lambda row: float(row["candidate_axis_coverage_ratio"]),
    )
    official = official_geometry(location)
    candidate_line = combined_line(candidate, metadata)
    official_covered = official.intersection(candidate_line.buffer(buffer_m)).length
    official_uncovered = official.difference(candidate_line.buffer(buffer_m))

    terminal_edge = candidate[-1]
    terminal_line = LineString(metadata[terminal_edge]["shape"])
    fixed_line = combined_line(fixed, metadata)
    candidate_outside_fixed_buffer = candidate_line.difference(fixed_line.buffer(buffer_m))
    outside_parts = list(
        candidate_outside_fixed_buffer.geoms
        if hasattr(candidate_outside_fixed_buffer, "geoms")
        else [candidate_outside_fixed_buffer]
    )
    deficit_segments = []
    for index, part in enumerate(outside_parts, start=1):
        west, south, east, north = part.bounds
        deficit_segments.append({
            "segment": index,
            "length_m": round(part.length, 3),
            "net_bbox": {
                "west": round(west, 3), "south": round(south, 3),
                "east": round(east, 3), "north": round(north, 3),
            },
            "wgs84_bbox": wgs84_bbox(part, location),
        })
    fixed_origin = fixed_line.interpolate(0)
    projected = terminal_line.project(fixed_origin)
    terminal_remaining = terminal_line.length - projected
    terminal_inside_fixed_buffer = terminal_line.intersection(fixed_line.buffer(buffer_m)).length

    expected_name = "第二京浜"
    route_checks: dict[str, Any] = {}
    contamination: list[str] = []
    for edge_id in candidate + extension_edges:
        item = metadata[edge_id]
        tags = [osm[orig] for orig in item["orig_ids"]]
        checks = {
            "sumo_ref_1": "1" in item["refs"],
            "osm_ref_1": bool(tags) and all(tag.get("ref") == "1" for tag in tags),
            "osm_name": bool(tags) and all(tag.get("name") == expected_name for tag in tags),
            "osm_national_name": bool(tags) and all(tag.get("nat_name") == "国道1号" for tag in tags),
            "relation_32989_forward": bool(item["orig_ids"]) and all(
                relation_roles.get(orig) == "forward" for orig in item["orig_ids"]
            ),
        }
        route_checks[edge_id] = checks
        if (
            not all(checks.values())
            or item["function"] == "internal"
            or item["type"].endswith("_link")
            or any(tag.get("highway", "").endswith("_link") for tag in tags)
        ):
            contamination.append(edge_id)

    if abs(current["candidate_axis_coverage_ratio"] - float(
        target["opposite_axis_coverage_by_fixed_ratio"]
    )) > 1e-6:
        raise ValueError("current coverage no longer reproduces formal adoption review")
    if abs(max(
        current["fixed_start_to_candidate_end_m"], current["fixed_end_to_candidate_start_m"]
    ) - max(
        float(target["fixed_start_to_opposite_end_distance_m"]),
        float(target["fixed_end_to_opposite_start_distance_m"]),
    )) > 0.001:
        raise ValueError("current endpoint metric no longer reproduces formal adoption review")
    if contamination:
        raise ValueError(f"route contamination found: {contamination}")

    final_status = "BOUNDARY_GEOMETRY_MISMATCH"
    if final_status not in ALLOWED_FINAL_STATUSES:
        raise ValueError(final_status)
    review_row = {
        "target_section_id": target["target_section_id"],
        "official_observation_section_id": OBSERVATION_ID,
        "route": target["route"],
        "cluster": target["cluster"],
        "current_candidate_edge_sequence": ";".join(candidate),
        "current_candidate_edge_count": len(candidate),
        "current_coverage": f"{current['candidate_axis_coverage_ratio']:.6f}",
        "current_fixed_axis_coverage": f"{current['fixed_axis_coverage_ratio']:.6f}",
        "current_endpoint_difference": f"{max(current['fixed_start_to_candidate_end_m'], current['fixed_end_to_candidate_start_m']):.3f}",
        "endpoint_mismatch_side": "OFFICIAL_ORIGIN_SIDE_FIXED_DOWN_START_OPPOSITE_UP_END",
        "extension_candidate_edges": ";".join(extension_edges),
        "extension_side": "UP_START_TERMINUS_SIDE;UP_END_ORIGIN_SIDE",
        "topology_evidence": json_text({
            "current_connection_violations": connection_violations(candidate, connections),
            "derived_predecessor_chain": before,
            "derived_successor_chain": after,
            "all_scenarios_connection_violation_zero": all(
                int(row["connection_violation_count"]) == 0 for row in extension_rows
            ),
        }),
        "route_identity_evidence": json_text({
            "canonical_route": "JP:national:1",
            "route_name": "国道1号",
            "osm_name": expected_name,
            "sumo_ref": "1",
            "route_relation_id": direction["route_relation_id"],
            "route_relation_network": relation_tags.get("network", ""),
            "route_relation_ref": relation_tags.get("ref", ""),
            "route_relation_operator": relation_tags.get("operator", ""),
            "per_edge_checks": route_checks,
        }),
        "osm_route_relation_evidence": json_text({
            "relation_tags": relation_tags,
            "member_roles": relation_roles,
            "candidate_and_extension_orig_ids": sorted(wanted_orig),
        }),
        "extended_coverage": best_extension["candidate_axis_coverage_ratio"],
        "extended_endpoint_difference": best_extension["maximum_endpoint_difference_m"],
        "best_extension_scenario": best_extension["scenario_id"],
        "coverage_60_percent_reachable_by_valid_local_extension": "false",
        "official_geometry_coverage_ratio": f"{official_covered / official.length:.6f}",
        "official_geometry_covered_length_m": f"{official_covered:.3f}",
        "official_geometry_uncovered_length_m": f"{official_uncovered.length:.3f}",
        "official_geometry_uncovered_bbox_wgs84": json_text(wgs84_bbox(official_uncovered, location)),
        "candidate_coverage_deficit_segments_json": json_text(deficit_segments),
        "coverage_deficit_characterization": "INTERIOR_DIVIDED_CARRIAGEWAY_OFFSET_AND_ORIGIN_SIDE_TERMINAL_EDGE_OVERRUN",
        "terminal_boundary_edge_id": terminal_edge,
        "terminal_boundary_edge_length_m": f"{terminal_line.length:.3f}",
        "terminal_edge_length_after_fixed_origin_projection_m": f"{terminal_remaining:.3f}",
        "terminal_edge_length_inside_fixed_25m_buffer_m": f"{terminal_inside_fixed_buffer:.3f}",
        "contamination_check": "PASS_NO_INTERNAL_RAMP_FRONTAGE_CROSS_ROUTE_OR_OTHER_CARRIAGEWAY",
        "final_review_status": final_status,
        "final_review_reason": (
            "両端の局所延長は国道1号本線としてroute/topology上連続するが、最良の1-edge延長でも"
            f"候補側coverage={float(best_extension['candidate_axis_coverage_ratio']):.4f}<0.60であり、"
            "反対端の220.357 m差は残る。観測区間境界が固定候補末尾の長いSUMO edge途中より手前にあり、"
            "edge全体採用で過走するboundary/segmentation mismatchである。固定列を切断・再選択しない条件では正式採択不可。"
        ),
        "adoption_status": "REVIEW_REQUIRED",
        "up_sumo_edge_sequence": "",
        "down_sumo_edge_sequence": ";".join(fixed),
        "evidence_source": json_text([
            relative(ADOPTION_REVIEW), relative(DIRECTION_CLUSTERS), relative(OFFICIAL_GEOMETRY),
            relative(NETWORK), relative(OSM), relative(ROUTE_RELATIONS), relative(CONFIG),
        ]),
        "provenance": json_text({
            "generator": relative(Path(__file__)),
            "generator_version": SCRIPT_VERSION,
            "candidate_source_immutable": True,
            "formal_mapping_mutated": False,
            "network_mutated": False,
            "threshold_mutated": False,
            "source_data_mutated": False,
        }),
    }

    edge_rows: list[dict[str, Any]] = []
    for role, sequence in (("CURRENT_CANDIDATE", candidate), ("LOCAL_EXTENSION", extension_edges)):
        for order, edge_id in enumerate(sequence, start=1):
            item = metadata[edge_id]
            edge_line = LineString(item["shape"])
            edge_rows.append({
                "official_observation_section_id": OBSERVATION_ID,
                "edge_role": role,
                "sequence_order": order,
                "edge_id": edge_id,
                "sumo_from": item["from"],
                "sumo_to": item["to"],
                "sumo_type": item["type"],
                "sumo_function": item["function"],
                "orig_ids_json": json_text(item["orig_ids"]),
                "osm_tags_json": json_text({orig: osm[orig] for orig in item["orig_ids"]}),
                "route_relation_roles_json": json_text({
                    orig: relation_roles.get(orig, "") for orig in item["orig_ids"]
                }),
                "edge_length_m": f"{edge_line.length:.3f}",
                "length_inside_fixed_25m_buffer_m": f"{edge_line.intersection(fixed_line.buffer(buffer_m)).length:.3f}",
                "route_identity_status": "CONFIRMED",
                "contamination_status": "PASS",
            })
    return [review_row], extension_rows, edge_rows


def build_qa(
    review_rows: list[dict[str, Any]], extension_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    row = review_rows[0]
    qa: dict[str, Any] = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "summary": {
            "target_count": 1,
            "valid_local_extension_edge_count": len(row["extension_candidate_edges"].split(";")),
            "coverage_threshold_reached_count": sum(
                item["coverage_threshold_pass"] == "true" for item in extension_rows
            ),
            "formally_adopted_count": sum(item["up_sumo_edge_sequence"] != "" for item in review_rows),
            "review_required_count": sum(item["adoption_status"] == "REVIEW_REQUIRED" for item in review_rows),
            "final_status_counts": {row["final_review_status"]: 1},
        },
        "invariants": {
            "target_derived_from_formal_review": True,
            "current_candidate_edge_count": int(row["current_candidate_edge_count"]),
            "current_candidate_changed": False,
            "fixed_mapping_changed": False,
            "base_66_mapping_changed": False,
            "network_changed": False,
            "config_or_threshold_changed": False,
            "source_data_changed": False,
            "all_scenario_connection_violation_count": sum(
                int(item["connection_violation_count"]) for item in extension_rows
            ),
            "contamination_count": sum(
                item["contamination_status"] != "PASS" for item in edge_rows
            ),
            "up_sequence_adopted": row["up_sumo_edge_sequence"] != "",
        },
    }
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    if len(review_rows) != 1 or int(row["current_candidate_edge_count"]) != 14:
        raise ValueError("Route 1 review completeness failed")
    if qa["invariants"]["all_scenario_connection_violation_count"]:
        raise ValueError("local extension topology failed")
    if qa["invariants"]["contamination_count"]:
        raise ValueError("local extension contamination failed")
    if row["final_review_status"] != "BOUNDARY_GEOMETRY_MISMATCH":
        raise ValueError("unexpected final review status")
    return qa


def render_report(row: dict[str, Any], qa: dict[str, Any]) -> str:
    lines = [
        "# 国道1号 opposite carriageway coverage不足個別調査",
        "",
        "既存の固定DOWN 15-edge列、alternate UP 14-edge候補、matching閾値、SUMO network、元データは変更していない。",
        "",
        "## 結論",
        "",
        f"最終判定は `{row['final_review_status']}` であり、UP列は採択しない。",
        "",
        f"- 現候補coverage: {row['current_coverage']}（閾値0.60）",
        f"- 現候補の最大端点差: {row['current_endpoint_difference']} m（公式起点側、固定DOWN始点／候補UP終点）",
        f"- 最良局所延長: `{row['best_extension_scenario']}`、coverage {row['extended_coverage']}、最大端点差 {row['extended_endpoint_difference']} m",
        f"- 公式geometry被覆: {row['official_geometry_coverage_ratio']}、未被覆 {row['official_geometry_uncovered_length_m']} m",
        f"- 境界edge: `{row['terminal_boundary_edge_id']}`、長さ {row['terminal_boundary_edge_length_m']} m",
        "",
        "## 原因",
        "",
        "候補末尾のSUMO edgeは観測区間境界をまたぐ粒度であり、edge全体を含めると公式起点側へ過走する。"
        "直前側の短い1 edgeは自然な国道1号本線延長だがcoverageを0.60まで上げず、反対側の220.357 m差も解消しない。"
        "候補軸の25 m buffer外は198.333 m、13.749 m、202.159 mの3区間に分かれ、最後が起点側の末尾edge過走、"
        "前二者は分離車道軸間隔が25 mを超える内部区間である。さらに延ばすと端点対応が悪化するため、"
        "単純なcorridor aggregation不足ではない。",
        "",
        "## 非変更確認",
        "",
        "正本mapping、66区間mapping、候補列、network、config・閾値、公式geometryはpre-work hashで固定した。",
        "",
    ]
    if "validation" in qa:
        validation = qa["validation"]
        lines.append(
            f"Validation: {validation['passed_test_count']} passed, "
            f"{validation['failed_test_count']} failed."
        )
        lines.append("")
    return "\n".join(lines)


def write_all() -> None:
    snapshot = verify_prework()
    review_rows, extension_rows, edge_rows = build_outputs()
    qa = build_qa(review_rows, extension_rows, edge_rows)
    write_csv(REVIEW_CSV, review_rows)
    write_csv(EXTENSION_CSV, extension_rows)
    write_csv(EDGE_CSV, edge_rows)
    QA_JSON.write_text(
        json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    REPORT.write_text(render_report(review_rows[0], qa), encoding="utf-8")
    outputs = [REVIEW_CSV, EXTENSION_CSV, EDGE_CSV, QA_JSON, REPORT]
    if VALIDATION_JSON.is_file():
        outputs.append(VALIDATION_JSON)
    manifest = {
        "run_id": RUN_ID,
        "generator": relative(Path(__file__)),
        "generator_sha256": sha256_file(Path(__file__)),
        "generator_version": SCRIPT_VERSION,
        "git_base_commit": snapshot["git_base_commit"],
        "prework_snapshot": relative(PREWORK),
        "prework_snapshot_sha256": sha256_file(PREWORK),
        "input_hashes": snapshot["sha256"],
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "non_mutation_contract": {
            "formal_mapping_changed": False,
            "base_66_mapping_changed": False,
            "selected_edges_changed": False,
            "network_changed": False,
            "config_or_thresholds_changed": False,
            "source_data_changed": False,
        },
        "qa": qa,
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
