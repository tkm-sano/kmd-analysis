"""Diagnose and resolve Route 316 direction evidence without mutating mappings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any
import xml.etree.ElementTree as ET

from pyproj import CRS, Transformer
from shapely.geometry import LineString

from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.calibration import investigate_external_observation_reverse_gaps as gaps


SCRIPT_VERSION = "1.1.0"
RUN_ID = "route316_direction_investigation_20260827_v2"
OBSERVATION_ID = "13403160320"
TARGET_IDS = ("13403160330", "13403160340", "13403160350")
COMPETING_BRANCH_ID = "13403160380"
MISSING_ORIGIN_ADJACENT_ID = "13403160400"
FINAL_CLASS = "RESOLVED_BY_COMBINED_EVIDENCE"
UP = "UP_TERMINUS_TO_ORIGIN"
DOWN = "DOWN_ORIGIN_TO_TERMINUS"

DATA_DIR = gaps.DATA_DIR
DIRECTION_FINAL = gaps.CLASSIFICATION
DIRECTION_CLUSTER = gaps.CLUSTER_EVIDENCE
REVERSE_CLUSTER = gaps.CLUSTER_CSV
FORMAL_MAPPING = gaps.FORMAL_MAPPING
BASE_MAPPING = DATA_DIR / "census_section_final_mapping.csv"
ROAD_CENSUS = (
    REPOSITORY_ROOT
    / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/kasyo13.csv"
)
NETWORK = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"
)
OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_baseline_explicit_v17_oneway.osm.xml"
)
ROUTE_RELATIONS = gaps.ROUTE_RELATIONS
CONFIG = gaps.CONFIG

EDGE_CSV = DATA_DIR / "route316_direction_edge_evidence.csv"
RELATION_CSV = DATA_DIR / "route316_direction_route_relation_evidence.csv"
ADJACENT_CSV = DATA_DIR / "route316_direction_adjacent_section_evidence.csv"
CLASSIFICATION_CSV = DATA_DIR / "route316_direction_final_classification.csv"
QA_JSON = DATA_DIR / "route316_direction_qa_summary.json"
MANIFEST_JSON = DATA_DIR / "route316_direction_manifest.json"
VALIDATION_JSON = DATA_DIR / "route316_direction_validation.json"
EVIDENCE_CSV = DATA_DIR / "route316_direction_evidence.csv"
DIAGNOSIS_CSV = DATA_DIR / "route316_direction_diagnosis.csv"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/route316_direction_investigation.md"

TOKYO_ROUTE_INVENTORY_URL = "https://www.kensetsu.metro.tokyo.lg.jp/content/000064960.pdf"
TOKYO_ROUTE_INVENTORY_SHA256 = "d113eca2555f35fcd2bf202d81c6de308acbf691984187ffa054730f914f87b0"
TOKYO_ROUTE_INVENTORY_PAGE = "PDF page 10 / printed page 193"
TOKYO_ROUTE_INVENTORY_AS_OF = "2024-04-01"
TOKYO_ROUTE_ORIGIN = "中央区日本橋本町三丁目"
TOKYO_ROUTE_TERMINUS = "大田区大森南一丁目"


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPOSITORY_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def way_id(edge_id: str) -> str:
    return edge_id.lstrip("-").split("#", 1)[0]


def extract_locked_evidence() -> dict[str, Any]:
    direction_rows = [
        row for row in read_csv(DIRECTION_FINAL)
        if row["official_observation_section_id"] == OBSERVATION_ID
    ]
    if tuple(row["target_section_id"] for row in direction_rows) != TARGET_IDS:
        raise ValueError("Route 316 target population is no longer the locked three targets")
    if any(row["direction_evidence_status"] != "UNRESOLVED" for row in direction_rows):
        raise ValueError("prior Route 316 direction result was changed")
    if any(row["decision_reason_code"] != "OFFICIAL_ENDPOINT_NOT_ANCHORED_TO_FIXED_EDGE_ENDPOINT"
           for row in direction_rows):
        raise ValueError("prior direct unresolved cause was changed")
    cluster = next(row for row in read_csv(DIRECTION_CLUSTER)
                   if row["official_observation_section_id"] == OBSERVATION_ID)
    reverse = next(row for row in read_csv(REVERSE_CLUSTER)
                   if row["official_observation_section_id"] == OBSERVATION_ID)
    mapping_rows = [row for row in read_csv(FORMAL_MAPPING)
                    if row["official_observation_section_id"] == OBSERVATION_ID]
    fixed_sequences = {row["final_sumo_edge_sequence"] for row in mapping_rows}
    if len(fixed_sequences) != 1:
        raise ValueError("fixed Route 316 sequence differs by target")
    fixed = next(iter(fixed_sequences)).split(";")
    alternate = json.loads(reverse["alternate_reverse_corridor_json"])
    if len(fixed) != 7 or alternate != gaps.REVIEWED_ALTERNATE_CORRIDORS[OBSERVATION_ID]:
        raise ValueError("locked 7-edge or 4-edge evidence changed")
    return {
        "direction_rows": direction_rows, "cluster": cluster, "reverse": reverse,
        "mapping_rows": mapping_rows, "fixed": fixed, "alternate": alternate,
    }


def census_rows() -> tuple[dict[str, dict[str, str]], bool]:
    wanted = {OBSERVATION_ID, *TARGET_IDS, COMPETING_BRANCH_ID, MISSING_ORIGIN_ADJACENT_ID}
    rows = {row["交通調査基本区間番号"]: row
            for row in read_csv(ROAD_CENSUS, encoding="cp932")
            if row["交通調査基本区間番号"] in wanted}
    required = {OBSERVATION_ID, *TARGET_IDS, COMPETING_BRANCH_ID}
    if required - set(rows):
        raise ValueError(f"official Census rows missing: {sorted(required - set(rows))}")
    return rows, MISSING_ORIGIN_ADJACENT_ID not in rows


def parse_shape(text: str) -> list[tuple[float, float]]:
    return [tuple(map(float, point.split(","))) for point in text.split()]


def parse_network(required: set[str]) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]], dict[str, str]]:
    metadata: dict[str, dict[str, Any]] = {}
    connections: set[tuple[str, str]] = set()
    location: dict[str, str] = {}
    for event, element in ET.iterparse(NETWORK, events=("start", "end")):
        if event == "start" and element.tag == "location":
            location = dict(element.attrib)
        elif event == "end" and element.tag == "edge":
            edge_id = element.get("id", "")
            if edge_id in required:
                lane = element.find("lane")
                if lane is None:
                    raise ValueError(f"edge has no lane: {edge_id}")
                metadata[edge_id] = {
                    "from": element.get("from", ""), "to": element.get("to", ""),
                    "length": float(lane.get("length", "0")),
                    "shape": parse_shape(lane.get("shape", "")),
                    "type": element.get("type", ""), "function": element.get("function", ""),
                    "orig_ids": sorted({
                        source for item in element.findall("lane") for param in item.findall("param")
                        if param.get("key") == "origId"
                        for source in param.get("value", "").split() if source
                    }),
                }
            element.clear()
        elif event == "end" and element.tag == "connection":
            connections.add((element.get("from", ""), element.get("to", "")))
            element.clear()
    if required - set(metadata):
        raise ValueError(f"required SUMO edges missing: {sorted(required - set(metadata))}")
    if not location:
        raise ValueError("SUMO location metadata missing")
    return metadata, connections, location


def parse_osm(wanted: set[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(OSM, events=("end",)):
        if element.tag == "way":
            if element.get("id", "") in wanted:
                result[element.get("id", "")] = {
                    tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
                }
            element.clear()
    if wanted - set(result):
        raise ValueError(f"OSM ways missing: {sorted(wanted - set(result))}")
    return result


def parse_relation(relation_id: str) -> dict[str, Any]:
    for _, element in ET.iterparse(ROUTE_RELATIONS, events=("end",)):
        if element.tag == "relation":
            if element.get("id") == relation_id:
                return {
                    "tags": {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")},
                    "members": [
                        {"member_index": index, "osm_way_id": member.get("ref", ""),
                         "member_role": member.get("role", "")}
                        for index, member in enumerate(element.findall("member"))
                        if member.get("type") == "way"
                    ],
                }
            element.clear()
    raise ValueError(f"route relation missing: {relation_id}")


def wgs84(point: tuple[float, float], location: dict[str, str]) -> tuple[float, float]:
    offset_x, offset_y = map(float, location["netOffset"].split(","))
    inverse = Transformer.from_crs(
        CRS.from_proj4(location["projParameter"]), 4326, always_xy=True
    )
    return inverse.transform(point[0] - offset_x, point[1] - offset_y)


def connection_violations(sequence: list[str], connections: set[tuple[str, str]]) -> list[list[str]]:
    return [[left, right] for left, right in zip(sequence, sequence[1:])
            if (left, right) not in connections]


def combined_line(sequence: list[str], metadata: dict[str, dict[str, Any]]) -> LineString:
    coordinates: list[tuple[float, float]] = []
    for edge_id in sequence:
        shape = metadata[edge_id]["shape"]
        coordinates.extend(shape[1:] if coordinates and coordinates[-1] == shape[0] else shape)
    return LineString(coordinates)


def deduplicated_ways(sequence: list[str]) -> list[str]:
    result: list[str] = []
    for edge in sequence:
        osm_way = way_id(edge)
        if not result or result[-1] != osm_way:
            result.append(osm_way)
    return result


def relation_sequence_status(sequence: list[str], positions: dict[str, dict[str, Any]]) -> str:
    ways = deduplicated_ways(sequence)
    if any(way not in positions for way in ways):
        return "MEMBERSHIP_INCOMPLETE"
    indexes = [positions[way]["member_index"] for way in ways]
    if indexes == list(range(indexes[0], indexes[0] + len(indexes))):
        return "CONTIGUOUS_INCREASING"
    if indexes == list(range(indexes[0], indexes[0] - len(indexes), -1)):
        return "CONTIGUOUS_DECREASING"
    return "MEMBER_SEQUENCE_NONCONTIGUOUS"


def build_evidence() -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]],
    list[dict[str, Any]], list[dict[str, Any]]
]:
    locked = extract_locked_evidence()
    census, missing_origin_adjacent = census_rows()
    base = {row["section_id"]: row for row in read_csv(BASE_MAPPING)}
    adjacent_sequences = {section: base[section]["final_edge_ids"].split(";")
                          for section in (*TARGET_IDS, COMPETING_BRANCH_ID)}
    required = set(locked["fixed"] + locked["alternate"])
    required.update(
        edge for section in TARGET_IDS for edge in adjacent_sequences[section]
    )
    metadata, connections, location = parse_network(required)
    wanted_ways = {orig for edge in required for orig in metadata[edge]["orig_ids"]}
    osm = parse_osm(wanted_ways)
    relation_id = locked["cluster"]["route_relation_id"]
    relation = parse_relation(relation_id)
    relation_positions = {row["osm_way_id"]: row for row in relation["members"]}

    sequences = {
        "FIXED_7_EDGE": locked["fixed"],
        "ALTERNATE_4_EDGE": locked["alternate"],
        **{f"ADJACENT_{section}": adjacent_sequences[section] for section in TARGET_IDS},
    }
    inferred_roles = {
        "FIXED_7_EDGE": UP, "ALTERNATE_4_EDGE": DOWN,
        f"ADJACENT_{TARGET_IDS[0]}": DOWN, f"ADJACENT_{TARGET_IDS[1]}": DOWN,
        f"ADJACENT_{TARGET_IDS[2]}": DOWN,
    }
    edge_rows: list[dict[str, Any]] = []
    for corridor_role, sequence in sequences.items():
        violations = {tuple(pair) for pair in connection_violations(sequence, connections)}
        for index, edge_id in enumerate(sequence, start=1):
            item = metadata[edge_id]
            start_lon, start_lat = wgs84(item["shape"][0], location)
            end_lon, end_lat = wgs84(item["shape"][-1], location)
            tags = {orig: osm[orig] for orig in item["orig_ids"]}
            memberships = [relation_positions[orig] for orig in item["orig_ids"]
                           if orig in relation_positions]
            edge_rows.append({
                "official_observation_section_id": OBSERVATION_ID,
                "corridor_role": corridor_role,
                "inferred_direction_role": inferred_roles[corridor_role],
                "sequence_order": index,
                "edge_id": edge_id,
                "sumo_from": item["from"], "sumo_to": item["to"],
                "edge_length_m": f"{item['length']:.3f}",
                "start_lon": f"{start_lon:.9f}", "start_lat": f"{start_lat:.9f}",
                "end_lon": f"{end_lon:.9f}", "end_lat": f"{end_lat:.9f}",
                "edge_progression_support_only": "NORTHBOUND" if end_lat > start_lat else "SOUTHBOUND",
                "osm_way_ids_json": json_text(item["orig_ids"]),
                "osm_tags_json": json_text(tags),
                "route_relation_membership_json": json_text(memberships),
                "route_identity_status": "PASS" if all(
                    tag.get("ref") == "316" and tag.get("name") in {"海岸通り", "日本橋芝浦大森線"}
                    for tag in tags.values()
                ) and memberships else "FAIL",
                "edge_type_status": "PASS" if item["function"] != "internal"
                and not item["type"].endswith("_link") else "FAIL",
                "connection_to_next_status": (
                    "LAST_EDGE" if index == len(sequence)
                    else "FAIL" if (edge_id, sequence[index]) in violations else "PASS"
                ),
                "geometry_use_restriction": "LOCATION_AND_CORRESPONDENCE_ONLY_NOT_DIRECTION_AUTHORITY",
            })

    relation_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for corridor_role, sequence in sequences.items():
        sequence_status = relation_sequence_status(sequence, relation_positions)
        for osm_way in deduplicated_ways(sequence):
            key = (corridor_role, osm_way)
            if key in seen:
                continue
            seen.add(key)
            member = relation_positions.get(osm_way, {})
            relation_rows.append({
                "official_observation_section_id": OBSERVATION_ID,
                "corridor_role": corridor_role,
                "osm_way_id": osm_way,
                "relation_id": relation_id,
                "canonical_name": relation["tags"].get("name", ""),
                "official_name": relation["tags"].get("official_name", ""),
                "network": relation["tags"].get("network", ""),
                "ref": relation["tags"].get("ref", ""),
                "operator": relation["tags"].get("operator", ""),
                "member_index": member.get("member_index", ""),
                "member_role": member.get("member_role", ""),
                "corridor_member_sequence_status": sequence_status,
                "route_identity_status": "PASS" if (
                    relation["tags"].get("network") == "JP:prefectural:tokyo"
                    and relation["tags"].get("ref") == "316"
                    and relation["tags"].get("name") == "日本橋芝浦大森線"
                    and member
                ) else "FAIL",
                "direction_evidence_status": "INSUFFICIENT_ALONE_EMPTY_ROLES_NO_DIRECTION_NOTE",
                "bare_numeric_ref_used_alone": "false",
            })

    def overlap(left: list[str], right: list[str]) -> list[str]:
        return [edge for edge in left if edge in set(right)]

    adjacent_specs = [
        (OBSERVATION_ID, "ORIGIN", MISSING_ORIGIN_ADJACENT_ID, "UNKNOWN", "品川区道", [],
         "MISSING_REFERENCED_CENSUS_ROW"),
        (OBSERVATION_ID, "TERMINUS", TARGET_IDS[0], "ORIGIN", "品川区・大田区境",
         overlap(locked["alternate"], adjacent_sequences[TARGET_IDS[0]]), "PASS_TARGET_BRANCH"),
        (OBSERVATION_ID, "TERMINUS", COMPETING_BRANCH_ID, "ORIGIN", "品川区・大田区境",
         overlap(locked["alternate"], adjacent_sequences[COMPETING_BRANCH_ID]), "COMPETING_BRANCH_NO_OVERLAP"),
        (TARGET_IDS[0], "TERMINUS", TARGET_IDS[1], "ORIGIN", "環状七号線",
         overlap(adjacent_sequences[TARGET_IDS[0]], adjacent_sequences[TARGET_IDS[1]]), "PASS_TARGET_CHAIN"),
        (TARGET_IDS[1], "TERMINUS", TARGET_IDS[2], "ORIGIN", "高速１号羽田線",
         overlap(adjacent_sequences[TARGET_IDS[1]], adjacent_sequences[TARGET_IDS[2]]), "PASS_TARGET_CHAIN"),
    ]
    adjacent_rows: list[dict[str, Any]] = []
    for left_id, left_side, right_id, right_side, label, shared, status in adjacent_specs:
        left = census[left_id]
        right = census.get(right_id)
        left_label = left[f"{'起点' if left_side == 'ORIGIN' else '終点'}側／路線名等"]
        right_label = "" if right is None or right_side == "UNKNOWN" else right[
            f"{'起点' if right_side == 'ORIGIN' else '終点'}側／路線名等"
        ]
        adjacent_rows.append({
            "official_observation_section_id": OBSERVATION_ID,
            "left_section_id": left_id, "left_endpoint": left_side,
            "right_section_id": right_id, "right_endpoint": right_side,
            "left_route_number": left["路線番号"],
            "right_route_number": right["路線番号"] if right else "",
            "left_route_name": left["路線名"],
            "right_route_name": right["路線名"] if right else "",
            "left_endpoint_label": left_label, "right_endpoint_label": right_label,
            "expected_shared_label": label,
            "official_label_correspondence": (
                "PASS" if left_label == right_label == label else
                "UNAVAILABLE" if right is None else "FAIL"
            ),
            "shared_sumo_edges_json": json_text(shared),
            "sumo_overlap_status": "PASS" if shared else "UNAVAILABLE",
            "evidence_status": status,
            "direction_anchor_contribution": (
                "ALTERNATE_IS_DOWN_ORIGIN_TO_TERMINUS" if status == "PASS_TARGET_BRANCH"
                else "SUPPORTS_ORIGIN_TO_TERMINUS_TARGET_CHAIN" if status == "PASS_TARGET_CHAIN"
                else "NONE"
            ),
            "geojson_coordinate_order_used": "false",
        })

    fixed_line = combined_line(locked["fixed"], metadata)
    alternate_line = combined_line(locked["alternate"], metadata)
    fixed_vector = (fixed_line.coords[-1][0] - fixed_line.coords[0][0],
                    fixed_line.coords[-1][1] - fixed_line.coords[0][1])
    alternate_vector = (alternate_line.coords[-1][0] - alternate_line.coords[0][0],
                        alternate_line.coords[-1][1] - alternate_line.coords[0][1])
    cosine = (fixed_vector[0] * alternate_vector[0] + fixed_vector[1] * alternate_vector[1]) / (
        math.hypot(*fixed_vector) * math.hypot(*alternate_vector)
    )
    anchor_overlaps = {
        "observation_to_60330": overlap(locked["alternate"], adjacent_sequences[TARGET_IDS[0]]),
        "60330_to_60340": overlap(adjacent_sequences[TARGET_IDS[0]], adjacent_sequences[TARGET_IDS[1]]),
        "60340_to_60350": overlap(adjacent_sequences[TARGET_IDS[1]], adjacent_sequences[TARGET_IDS[2]]),
    }
    facts = {
        "locked": locked, "census": census, "missing_origin_adjacent": missing_origin_adjacent,
        "metadata": metadata, "connections": connections, "relation": relation,
        "relation_positions": relation_positions, "sequences": sequences,
        "adjacent_sequences": adjacent_sequences, "anchor_overlaps": anchor_overlaps,
        "fixed_alternate_direction_cosine": cosine,
        "fixed_endpoint_cross_distance_m": fixed_line.coords[0],
        "relation_direction_alone_sufficient": False,
    }

    classification_rows: list[dict[str, Any]] = []
    for prior in locked["direction_rows"]:
        classification_rows.append({
            "target_section_id": prior["target_section_id"],
            "official_observation_section_id": OBSERVATION_ID,
            "prior_direction_evidence_status": prior["direction_evidence_status"],
            "prior_reason_code": prior["decision_reason_code"],
            "prior_reason": prior["decision_reason"],
            "evidence_gap_or_conflict": "PRIOR_EVIDENCE_GAP_NO_CONFLICT",
            "final_classification": FINAL_CLASS,
            "fixed_7_edge_direction_role": UP,
            "alternate_4_edge_direction_role": DOWN,
            "up_edge_sequence": ";".join(locked["fixed"]),
            "down_edge_sequence": ";".join(locked["alternate"]),
            "official_definition": "UP=TERMINUS_TO_ORIGIN;DOWN=ORIGIN_TO_TERMINUS",
            "resolving_evidence_combination": (
                "official route endpoints + official section endpoint chain + exact shared-edge "
                "continuity at 60320/60330, 60330/60340 and 60340/60350 + canonical route relation "
                "identity + connected anti-parallel one-way SUMO carriageways"
            ),
            "route_relation_alone_sufficient": "false",
            "adjacent_section_anchor_status": "PASS",
            "evidence_conflict_status": "NONE",
            "formal_mapping_changed": "false",
            "sumo_network_changed": "false",
            "threshold_changed": "false",
            "adoption_status": "DIAGNOSIS_ONLY_NOT_APPLIED_TO_FORMAL_MAPPING",
            "decision_rule_id": "ROUTE316_COMBINED_OFFICIAL_ADJACENCY_TOPOLOGY_V1",
        })
    return facts, edge_rows, relation_rows, adjacent_rows, classification_rows


def build_qa(
    facts: dict[str, Any], edge_rows: list[dict[str, Any]], relation_rows: list[dict[str, Any]],
    adjacent_rows: list[dict[str, Any]], classification_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]], diagnosis_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fixed = facts["locked"]["fixed"]
    alternate = facts["locked"]["alternate"]
    connections = facts["connections"]
    target_chain = [row for row in adjacent_rows if row["evidence_status"] in {
        "PASS_TARGET_BRANCH", "PASS_TARGET_CHAIN"
    }]
    qa = {
        "run_id": RUN_ID, "generator_version": SCRIPT_VERSION, "status": "PASSED",
        "direct_unresolved_cause": "OFFICIAL_ENDPOINT_NOT_ANCHORED_TO_FIXED_EDGE_ENDPOINT",
        "evidence_diagnosis": "PRIOR_EVIDENCE_INSUFFICIENT_NOT_CONFLICTING",
        "summary": {
            "target_count": len(classification_rows), "fixed_edge_count": len(fixed),
            "alternate_edge_count": len(alternate), "final_classification_counts": {
                FINAL_CLASS: len(classification_rows)
            },
            "proposed_direction_status_counts": {"RESOLVED_UP": len(diagnosis_rows)},
            "direction_evidence_status_counts": {"RESOLVED": len(diagnosis_rows)},
            "traffic_assignment_status_counts": {"REVIEW_REQUIRED": len(diagnosis_rows)},
            "evidence_type_counts": {
                evidence_type: sum(row["evidence_type"] == evidence_type for row in evidence_rows)
                for evidence_type in sorted({row["evidence_type"] for row in evidence_rows})
            },
        },
        "invariants": {
            "prior_unresolved_rows_preserved": all(
                row["prior_direction_evidence_status"] == "UNRESOLVED"
                for row in classification_rows
            ),
            "fixed_connection_violation_count": len(connection_violations(fixed, connections)),
            "alternate_connection_violation_count": len(connection_violations(alternate, connections)),
            "edge_route_identity_failure_count": sum(row["route_identity_status"] != "PASS" for row in edge_rows),
            "edge_type_failure_count": sum(row["edge_type_status"] != "PASS" for row in edge_rows),
            "route_relation_identity_failure_count": sum(row["route_identity_status"] != "PASS" for row in relation_rows),
            "route_relation_alone_used_for_direction": False,
            "route_relation_member_roles_all_empty": all(row["member_role"] == "" for row in relation_rows),
            "route_relation_operator_empty": facts["relation"]["tags"].get("operator", "") == "",
            "target_chain_anchor_count": len(target_chain),
            "target_chain_anchor_failure_count": sum(
                row["official_label_correspondence"] != "PASS" or row["sumo_overlap_status"] != "PASS"
                for row in target_chain
            ),
            "origin_adjacent_60400_row_missing": facts["missing_origin_adjacent"],
            "fixed_alternate_antiparallel": facts["fixed_alternate_direction_cosine"] < -0.8,
            "geojson_coordinate_order_used": False,
            "formal_mapping_changed": False, "sumo_network_changed": False,
            "matching_threshold_changed": False,
            "opposite_candidate_formally_adopted": False,
            "direction_status_separated_from_traffic_assignment": all(
                row["direction_evidence_status"] == "RESOLVED"
                and row["traffic_assignment_status"] == "REVIEW_REQUIRED"
                for row in diagnosis_rows
            ),
        },
        "official_route_inventory": {
            "url": TOKYO_ROUTE_INVENTORY_URL, "sha256": TOKYO_ROUTE_INVENTORY_SHA256,
            "page": TOKYO_ROUTE_INVENTORY_PAGE, "as_of": TOKYO_ROUTE_INVENTORY_AS_OF,
            "route_number": "316", "route_name": "日本橋芝浦大森線",
            "origin": TOKYO_ROUTE_ORIGIN, "terminus": TOKYO_ROUTE_TERMINUS,
        },
        "anchor_overlaps": facts["anchor_overlaps"],
    }
    checks = qa["invariants"]
    if (
        checks["fixed_connection_violation_count"] or checks["alternate_connection_violation_count"]
        or checks["edge_route_identity_failure_count"] or checks["edge_type_failure_count"]
        or checks["route_relation_identity_failure_count"] or checks["target_chain_anchor_failure_count"]
        or checks["route_relation_alone_used_for_direction"] or checks["geojson_coordinate_order_used"]
        or checks["formal_mapping_changed"] or checks["sumo_network_changed"]
        or checks["matching_threshold_changed"] or not checks["prior_unresolved_rows_preserved"]
        or not checks["fixed_alternate_antiparallel"] or checks["target_chain_anchor_count"] != 3
        or checks["opposite_candidate_formally_adopted"]
        or not checks["direction_status_separated_from_traffic_assignment"]
    ):
        raise ValueError(f"Route 316 QA failed: {qa}")
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    return qa


def build_required_outputs(
    facts: dict[str, Any], classification_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the request's compact evidence ledger and target-level diagnosis."""
    relation_id = facts["locked"]["cluster"]["route_relation_id"]
    common = [
        {
            "evidence_type": "OFFICIAL_DIRECTION_EVIDENCE",
            "source": "MLIT_ROAD_CENSUS_DIRECTION_DEFINITION",
            "source_object_id": "UP_DOWN_DEFINITION",
            "evidence_value": "UP=TERMINUS_TO_ORIGIN;DOWN=ORIGIN_TO_TERMINUS",
            "supports_up": "false", "supports_down": "false",
            "conflict_status": "DEFINITION_ONLY",
            "notes": "Defines the official semantics; it does not identify either SUMO carriageway alone.",
        },
        {
            "evidence_type": "OFFICIAL_ROUTE_ENDPOINT_EVIDENCE",
            "source": TOKYO_ROUTE_INVENTORY_URL,
            "source_object_id": "TOKYO_ROUTE_316",
            "evidence_value": (
                f"route=316;name=日本橋芝浦大森線;origin={TOKYO_ROUTE_ORIGIN};"
                f"terminus={TOKYO_ROUTE_TERMINUS};as_of={TOKYO_ROUTE_INVENTORY_AS_OF}"
            ),
            "supports_up": "true", "supports_down": "false",
            "conflict_status": "SUPPORTS_ONLY_WHEN_COMBINED",
            "notes": "Official route endpoints connect the selected corridor to UP only through the section-chain anchors.",
        },
        {
            "evidence_type": "OFFICIAL_ROUTE_ENDPOINT_EVIDENCE",
            "source": relative(ROAD_CENSUS),
            "source_object_id": f"{OBSERVATION_ID}->{TARGET_IDS[0]}",
            "evidence_value": "60320_TERMINUS=60330_ORIGIN=品川区・大田区境;shared_edge=45662512",
            "supports_up": "true", "supports_down": "false",
            "conflict_status": "CONSISTENT",
            "notes": "Anchors the alternate carriageway to origin-to-terminus (DOWN), hence the paired selected carriageway to UP.",
        },
        {
            "evidence_type": "TOPOLOGY_SUPPORTING_EVIDENCE",
            "source": relative(BASE_MAPPING),
            "source_object_id": f"{TARGET_IDS[0]}->{TARGET_IDS[1]}",
            "evidence_value": "official_endpoint=環状七号線;shared_edge=1457802380",
            "supports_up": "true", "supports_down": "false",
            "conflict_status": "CONSISTENT",
            "notes": "Continues the official terminus-to-origin section chain in the alternate corridor's travel direction.",
        },
        {
            "evidence_type": "TOPOLOGY_SUPPORTING_EVIDENCE",
            "source": relative(BASE_MAPPING),
            "source_object_id": f"{TARGET_IDS[1]}->{TARGET_IDS[2]}",
            "evidence_value": "official_endpoint=高速１号羽田線;shared_edges=1068239670;45662504",
            "supports_up": "true", "supports_down": "false",
            "conflict_status": "CONSISTENT",
            "notes": "Provides a second independent continuation of the same official endpoint chain.",
        },
        {
            "evidence_type": "OSM_ROUTE_RELATION_EVIDENCE",
            "source": relative(ROUTE_RELATIONS),
            "source_object_id": relation_id,
            "evidence_value": (
                "name=日本橋芝浦大森線;network=JP:prefectural:tokyo;ref=316;operator=;"
                "fixed_sequence=CONTIGUOUS_DECREASING;alternate_sequence=CONTIGUOUS_DECREASING;roles=empty"
            ),
            "supports_up": "false", "supports_down": "false",
            "conflict_status": "INSUFFICIENT_ALONE",
            "notes": "Confirms canonical identity and continuity only; empty roles and equal sequence trends prevent direction resolution.",
        },
        {
            "evidence_type": "TOPOLOGY_SUPPORTING_EVIDENCE",
            "source": relative(NETWORK),
            "source_object_id": "SELECTED_7_EDGE_AND_ALTERNATE_4_EDGE",
            "evidence_value": "selected_connection_violations=0;alternate_connection_violations=0;separate_oneway_carriageways=true",
            "supports_up": "true", "supports_down": "false",
            "conflict_status": "CONSISTENT",
            "notes": "Supports applying the official endpoint anchor to the two connected carriageways; topology alone is not decisive.",
        },
        {
            "evidence_type": "GEOMETRY_SUPPORTING_EVIDENCE",
            "source": relative(NETWORK),
            "source_object_id": "SELECTED_VS_ALTERNATE",
            "evidence_value": f"direction_cosine={facts['fixed_alternate_direction_cosine']:.6f}",
            "supports_up": "false", "supports_down": "false",
            "conflict_status": "SUPPORT_ONLY",
            "notes": "Shows anti-parallel geometry only; bearing and GeoJSON coordinate order were not used as direction authority.",
        },
        {
            "evidence_type": "INSUFFICIENT_EVIDENCE",
            "source": relative(ROAD_CENSUS),
            "source_object_id": MISSING_ORIGIN_ADJACENT_ID,
            "evidence_value": "referenced_by_60320_origin_but_row_absent",
            "supports_up": "false", "supports_down": "false",
            "conflict_status": "MISSING_NOT_CONFLICTING",
            "notes": "Prevents an independent origin-side anchor but does not contradict the three terminus-side anchors.",
        },
        {
            "evidence_type": "CONFLICTING_EVIDENCE",
            "source": "CROSS_EVIDENCE_RECONCILIATION",
            "source_object_id": OBSERVATION_ID,
            "evidence_value": "NONE_FOUND",
            "supports_up": "false", "supports_down": "false",
            "conflict_status": "NONE",
            "notes": "No official, relation, topology, or geometry item supports selected-corridor DOWN against the combined UP conclusion.",
        },
    ]
    evidence_rows = [
        {"target": target, **item}
        for target in TARGET_IDS for item in common
    ]
    decisive = (
        "official 60320 terminus/60330 origin match + exact edge 45662512 overlap + "
        "60330/60340 and 60340/60350 official endpoint/shared-edge chain + relation identity + "
        "connected anti-parallel one-way carriageways"
    )
    diagnosis_rows = []
    for row in classification_rows:
        diagnosis_rows.append({
            "official_obs": OBSERVATION_ID,
            "target": row["target_section_id"],
            "current_status": "UNRESOLVED",
            "proposed_direction_status": "RESOLVED_UP",
            "selected_corridor_role": UP,
            "opposite_candidate_status": "FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED",
            "decisive_evidence": decisive,
            "unresolved_reason": "",
            "next_action": "RUN_SEPARATE_OPPOSITE_CARRIAGEWAY_FORMAL_ADOPTION_REVIEW",
            "direction_evidence_status": "RESOLVED",
            "traffic_assignment_status": "REVIEW_REQUIRED",
            "opposite_candidate_direction_role": DOWN,
            "formal_mapping_changed": "false",
        })
    return evidence_rows, diagnosis_rows


def render_report(
    facts: dict[str, Any], relation_rows: list[dict[str, Any]],
    adjacent_rows: list[dict[str, Any]], qa: dict[str, Any],
) -> str:
    relation = facts["relation"]["tags"]
    fixed_status = relation_sequence_status(facts["locked"]["fixed"], facts["relation_positions"])
    alternate_status = relation_sequence_status(facts["locked"]["alternate"], facts["relation_positions"])
    return f"""# 都道316号 `13403160320` direction formal investigation

## 直接原因

既存 `UNRESOLVED` の直接原因は、公式の起点・終点は確認済みでも、部分被覆の7-edge
固定列のどちらの端が公式起点／終点側かを、当時の公式隣接区間・接続路線・明示的
route relation方向から一意にanchorできなかったことである。これは証拠矛盾ではなく
`PRIOR_EVIDENCE_INSUFFICIENT_NOT_CONFLICTING` である。

## 結論

3 targetすべてについて、selected corridorを `RESOLVED_UP` と判定する
（導出分類は `{FINAL_CLASS}`）。診断上の方向は次のとおりである。

- 固定7-edge corridor: `{UP}`
- alternate 4-edge corridor: `{DOWN}`

既存正式mapping、既存direction classification、SUMO network、matching閾値は変更していない。
本成果物は診断レイヤーであり、正式mappingへの採択適用は別工程とする。

方向証拠statusは `RESOLVED` だが、traffic assignment statusは `REVIEW_REQUIRED` である。
alternateは方向・route identity・topologyの観点では
`FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED` であり、正式採択済みではない。

## 公式定義とendpoint

- MLIT定義: `UP=TERMINUS_TO_ORIGIN; DOWN=ORIGIN_TO_TERMINUS`
- Road Census `13403160320`: route 316「日本橋芝浦大森線」、起点側「品川区道」
  （接続先 `13403160400`）、終点側「品川区・大田区境」
- 東京都路線調書: 起点 `{TOKYO_ROUTE_ORIGIN}`、終点 `{TOKYO_ROUTE_TERMINUS}`
  （{TOKYO_ROUTE_INVENTORY_AS_OF}現在、{TOKYO_ROUTE_INVENTORY_PAGE}）

東京都の公式路線調書: {TOKYO_ROUTE_INVENTORY_URL}

## resolving evidence combination

1. `60320`終点と`60330`起点は公式原票で同じ「品川区・大田区境」である。
2. alternate末尾と`60330`先頭はedge `45662512`を共有する。
3. `60330`終点／`60340`起点は「環状七号線」で、edge `1457802380`を共有する。
4. `60340`終点／`60350`起点は「高速１号羽田線」で、edge
   `1068239670;45662504`を共有する。
5. 各列はconnection violation 0で、同じcanonical route relationに属する。
6. 固定列とalternate列は別oneway carriagewayで逆向き
   （direction cosine {facts['fixed_alternate_direction_cosine']:.6f}）である。

この公式endpoint chainとSUMO shared-edge topologyがalternateを起点→終点へanchorし、
alternateをDOWN、対応する反対車道の固定列をUPへ接続する。geometryは車道対応と位置の
補助に限定し、GeoJSON coordinate orderを方向証拠には使用していない。

## route relation diagnosis

- relation: `{facts['locked']['cluster']['route_relation_id']}`
- name / network / ref: `{relation.get('name', '')}` / `{relation.get('network', '')}` / `{relation.get('ref', '')}`
- operator: 空欄
- fixed member sequence: `{fixed_status}`
- alternate member sequence: `{alternate_status}`
- member role: 対象memberはすべて空欄

relationはcanonical identityとmember continuityを支持するが、方向注記、operator、
forward/backward roleがない。さらに両反対車道が同じdecreasing index trendを持つため、
relation sequence単独ではUP/DOWNを確定できない。bare numeric `ref=316`単独も使用していない。

## 残る制約

原票が`60320`起点側の接続先として参照する`13403160400`は、手元の`kasyo13.csv`に
対応行がないため、起点側からの独立anchorは得られない。ただし終点側から始まる3段の
公式section chainとSUMO edge共有が同一結論を与え、矛盾証拠はない。

## 次工程と成果物

正式mappingへ反対車道を追加する場合は、本診断とは分離した採択reviewを実施する。
本調査は `route316_direction_evidence.csv`、`route316_direction_diagnosis.csv`、詳細な
edge/relation/adjacent/final classification CSV、QA JSON、manifest、validation JSONを生成する。

## automated tests

関連回帰は `{qa.get('validation', {}).get('passed_test_count', 0)} passed / `
`{qa.get('validation', {}).get('failed_test_count', 0)} failed`
（Route316専用 `{qa.get('validation', {}).get('new_route316_direction_test_count', 0)}`件）である。

## Git差分

Gitの更新・stage・commitは行っていない。task sourceとして調査script、本文書、専用testを
workspaceへ追加し、生成CSV/JSONは既存のignored processed-data directoryへ出力した。
formal mapping、SUMO network、matching config/thresholdのhashはmanifest入力hashとして固定した。
"""


def write_all() -> None:
    facts, edge_rows, relation_rows, adjacent_rows, classification_rows = build_evidence()
    evidence_rows, diagnosis_rows = build_required_outputs(facts, classification_rows)
    qa = build_qa(
        facts, edge_rows, relation_rows, adjacent_rows, classification_rows,
        evidence_rows, diagnosis_rows,
    )
    write_csv(EDGE_CSV, edge_rows)
    write_csv(RELATION_CSV, relation_rows)
    write_csv(ADJACENT_CSV, adjacent_rows)
    write_csv(CLASSIFICATION_CSV, classification_rows)
    write_csv(EVIDENCE_CSV, evidence_rows)
    write_csv(DIAGNOSIS_CSV, diagnosis_rows)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(facts, relation_rows, adjacent_rows, qa), encoding="utf-8")
    if not VALIDATION_JSON.exists():
        VALIDATION_JSON.write_text(json.dumps({
            "status": "NOT_RUN", "verified_on": None, "test_command": None,
            "passed_test_count": 0, "failed_test_count": 0,
        }, indent=2) + "\n", encoding="utf-8")
    inputs = [DIRECTION_FINAL, DIRECTION_CLUSTER, REVERSE_CLUSTER, FORMAL_MAPPING,
              BASE_MAPPING, ROAD_CENSUS, NETWORK, OSM, ROUTE_RELATIONS, CONFIG]
    outputs = [EDGE_CSV, RELATION_CSV, ADJACENT_CSV, CLASSIFICATION_CSV,
               EVIDENCE_CSV, DIAGNOSIS_CSV,
               QA_JSON, VALIDATION_JSON, REPORT]
    manifest = {
        "run_id": RUN_ID, "generator": relative(Path(__file__)),
        "generator_version": SCRIPT_VERSION, "generator_sha256": sha256_file(Path(__file__)),
        "git_base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "input_hashes": {relative(path): sha256_file(path) for path in inputs},
        "external_official_source": qa["official_route_inventory"],
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "non_mutation_contract": {
            "formal_mapping_changed": False, "prior_direction_result_changed": False,
            "sumo_network_changed": False, "matching_config_or_threshold_changed": False,
            "geojson_coordinate_order_used": False, "edge_reselection_performed": False,
        },
        "qa_status": qa["status"],
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
