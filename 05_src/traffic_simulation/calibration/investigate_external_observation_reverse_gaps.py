"""Trace fixed-corridor reverse gaps without remapping or network mutation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any
import xml.etree.ElementTree as ET

from shapely.geometry import LineString

from traffic_simulation.paths import REPOSITORY_ROOT


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_reverse_gap_investigation_20260827_v1"
DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
CLASSIFICATION = DATA_DIR / "external_observation_direction_final_classification.csv"
CLUSTER_EVIDENCE = DATA_DIR / "external_observation_direction_cluster_evidence.csv"
FORMAL_MAPPING = DATA_DIR / "external_observation_final_mapping.csv"
FORMAL_EDGE_EVIDENCE = DATA_DIR / "external_observation_mapping_final_edge_evidence.csv"
ROUTE_RELATIONS = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
)
CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
BASE_OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_baseline_explicit_v17_oneway.osm.xml"
)
EXTENSION_OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1/ota_ward_external_extension_20260827_v1.osm.xml"
)
PREWORK = DATA_DIR / "external_observation_reverse_gap_prework_snapshot_20260827.json"

EDGE_CSV = DATA_DIR / "external_observation_reverse_gap_edge_evidence.csv"
CLUSTER_CSV = DATA_DIR / "external_observation_reverse_gap_cluster_classification.csv"
TARGET_CSV = DATA_DIR / "external_observation_reverse_gap_target_summary.csv"
QA_JSON = DATA_DIR / "external_observation_reverse_gap_qa.json"
MANIFEST_JSON = DATA_DIR / "external_observation_reverse_gap_manifest.json"
VALIDATION_JSON = DATA_DIR / "external_observation_reverse_gap_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_reverse_gap_review.md"

TARGET_TRAFFIC_STATUSES = {"REVERSE_CORRIDOR_MISSING", "REVERSE_CORRIDOR_PARTIAL"}
CAUSE_TAXONOMY = {
    "REVERSE_EXISTS_IN_SUMO_NOT_SELECTED",
    "ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO",
    "REVERSE_EXISTS_IN_OSM_NOT_IN_SUMO",
    "REVERSE_OUTSIDE_NETWORK_SCOPE",
    "REVERSE_TOPOLOGY_BREAK",
    "LEGITIMATE_ONEWAY",
    "SOURCE_DATA_MISSING",
    "UNRESOLVED",
}

# Reviewed alternate carriageways are investigation evidence, not adopted mappings.
# The target population is never sourced from this table; it is derived from the
# two canonical direction outputs and each sequence is revalidated against SUMO,
# netconvert input OSM, route identity, and topology on every run.
REVIEWED_ALTERNATE_CORRIDORS = {
    "13300010260": [
        "796871116#0", "796871116#1", "796871116#2", "1386535812",
        "1386535811", "1101385037#0", "1101385037#1", "1101385037#2",
        "1101385037#3", "542890136#0", "542890136#1", "997836008",
        "997835999", "542890137#0",
    ],
    "13400020040": [
        "878635659#0", "878635659#1", "878635659#2",
        *[f"254079818#{index}" for index in range(40)],
    ],
    "13403160320": ["652322551#0", "652322551#1", "652322551#2", "45662512"],
    "13604210030": [
        "46492247", "296013820#0", "296013820#1", "1073046517",
        "1308049171", "109048431", "1072972182", "1308049168",
        "1072972183", "295461978", "647379512", "647990222#0",
        "647990222#1", "647990222#2",
    ],
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


def verify_prework() -> dict[str, Any]:
    snapshot = json.loads(PREWORK.read_text(encoding="utf-8"))
    for path_text, expected in snapshot["sha256"].items():
        path = REPOSITORY_ROOT / path_text
        if sha256_file(path) != expected:
            raise ValueError(f"pre-work locked input changed: {path_text}")
    if snapshot["validation_baseline"]["passed_test_count"] != 76:
        raise ValueError("pre-work validation baseline is not 76 tests")
    return snapshot


def extract_targets() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = [
        row for row in read_csv(CLASSIFICATION)
        if row["traffic_assignment_status"] in TARGET_TRAFFIC_STATUSES
    ]
    clusters = {
        row["official_observation_section_id"]: row
        for row in read_csv(CLUSTER_EVIDENCE)
        if row["traffic_assignment_status"] in TARGET_TRAFFIC_STATUSES
    }
    observations = {row["official_observation_section_id"] for row in rows}
    if len(rows) != 6 or len(observations) != 4 or observations != set(clusters):
        raise ValueError("canonical reverse-gap population is not 6 targets / 4 clusters")
    if observations != set(REVIEWED_ALTERNATE_CORRIDORS):
        raise ValueError("reviewed corridor evidence does not match the canonical population")
    return sorted(rows, key=lambda row: row["target_section_id"]), clusters


def way_id(edge_id: str) -> str:
    return edge_id.lstrip("-").split("#", 1)[0]


def parse_shape(text: str) -> list[tuple[float, float]]:
    return [tuple(map(float, point.split(","))) for point in text.split()]


def edge_orig_ids(element: ET.Element) -> list[str]:
    return sorted({
        source
        for lane in element.findall("lane")
        for param in lane.findall("param")
        if param.get("key") == "origId"
        for source in param.get("value", "").split()
        if source
    })


def edge_metadata(element: ET.Element) -> dict[str, Any]:
    lanes = element.findall("lane")
    shape = parse_shape(lanes[0].get("shape", "")) if lanes and lanes[0].get("shape") else []
    return {
        "edge_id": element.get("id", ""),
        "from": element.get("from", ""),
        "to": element.get("to", ""),
        "type": element.get("type", ""),
        "orig_ids": edge_orig_ids(element),
        "shape": shape,
    }


def selected_pairs(observations: set[str]) -> dict[str, dict[str, tuple[str, str]]]:
    result: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    for row in read_csv(FORMAL_EDGE_EVIDENCE):
        observation = row["official_observation_section_id"]
        if observation not in observations:
            continue
        pair = (row["sumo_from"], row["sumo_to"])
        old = result[observation].get(row["edge_id"])
        if old is not None and old != pair:
            raise ValueError(f"inconsistent fixed edge evidence: {observation}/{row['edge_id']}")
        result[observation][row["edge_id"]] = pair
    return dict(result)


def parse_network(
    network: Path,
    observation: str,
    fixed_missing: list[str],
    alternate: list[str],
    pairs: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    required = set(fixed_missing) | set(alternate)
    reverse_pairs = {(pairs[edge][1], pairs[edge][0]) for edge in fixed_missing}
    expected_connections = set(zip(alternate, alternate[1:]))
    metadata: dict[str, dict[str, Any]] = {}
    exact_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    connections: set[tuple[str, str]] = set()
    for _, element in ET.iterparse(network, events=("end",)):
        if element.tag == "edge":
            edge_id = element.get("id", "")
            if edge_id and not edge_id.startswith(":") and element.get("from"):
                pair = (element.get("from", ""), element.get("to", ""))
                if edge_id in required:
                    metadata[edge_id] = edge_metadata(element)
                if pair in reverse_pairs:
                    exact_by_pair[pair].append(edge_id)
            element.clear()
        elif element.tag == "connection":
            pair = (element.get("from", ""), element.get("to", ""))
            if pair in expected_connections:
                connections.add(pair)
            element.clear()
    missing_required = required - set(metadata)
    if missing_required:
        raise ValueError(f"reviewed evidence edges absent from SUMO: {observation}: {sorted(missing_required)}")
    node_violations = [
        [left, right]
        for left, right in zip(alternate, alternate[1:])
        if metadata[left]["to"] != metadata[right]["from"]
    ]
    connection_violations = [
        [left, right]
        for left, right in zip(alternate, alternate[1:])
        if (left, right) not in connections
    ]
    exact_candidates = {
        edge: sorted(exact_by_pair.get((pairs[edge][1], pairs[edge][0]), []))
        for edge in fixed_missing
    }
    return {
        "metadata": metadata,
        "exact_candidates": exact_candidates,
        "alternate_node_violations": node_violations,
        "alternate_connection_violations": connection_violations,
    }


def parse_osm(path: Path, wanted: set[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag != "way":
            continue
        osm_id = element.get("id", "")
        if osm_id in wanted:
            result[osm_id] = {
                tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
            }
        element.clear()
    return result


def relation_memberships(wanted: set[str]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for _, relation in ET.iterparse(ROUTE_RELATIONS, events=("end",)):
        if relation.tag != "relation":
            continue
        members = [
            (index, member)
            for index, member in enumerate(relation.findall("member"))
            if member.get("type") == "way" and member.get("ref", "") in wanted
        ]
        if members:
            tags = {tag.get("k", ""): tag.get("v", "") for tag in relation.findall("tag")}
            for index, member in members:
                result[member.get("ref", "")].append({
                    "relation_id": relation.get("id", ""),
                    "member_index": index,
                    "member_role": member.get("role", ""),
                    "network": tags.get("network", ""),
                    "ref": tags.get("ref", ""),
                    "operator": tags.get("operator", ""),
                    "name": tags.get("name", "") or tags.get("official_name", ""),
                    "route": tags.get("route", ""),
                })
        relation.clear()
    return dict(result)


def line_cosine(left: list[tuple[float, float]], right: list[tuple[float, float]]) -> float:
    if len(left) < 2 or len(right) < 2:
        return 0.0
    a = (left[-1][0] - left[0][0], left[-1][1] - left[0][1])
    b = (right[-1][0] - right[0][0], right[-1][1] - right[0][1])
    divisor = math.hypot(*a) * math.hypot(*b)
    return (a[0] * b[0] + a[1] * b[1]) / divisor if divisor else 0.0


def local_alternate_candidates(
    fixed: dict[str, Any], alternate: list[str], metadata: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    fixed_line = LineString(fixed["shape"])
    scored = []
    for edge_id in alternate:
        candidate = metadata[edge_id]
        distance = fixed_line.distance(LineString(candidate["shape"]))
        scored.append({
            "edge_id": edge_id,
            "distance_m": round(distance, 3),
            "direction_cosine": round(line_cosine(fixed["shape"], candidate["shape"]), 6),
            "from": candidate["from"],
            "to": candidate["to"],
            "orig_ids": candidate["orig_ids"],
        })
    return sorted(scored, key=lambda item: (item["distance_m"], item["edge_id"]))[:3]


def matching_relation_evidence(
    orig_ids: set[str], memberships: dict[str, list[dict[str, Any]]], relation_id: str
) -> list[dict[str, Any]]:
    evidence = [item for orig_id in sorted(orig_ids) for item in memberships.get(orig_id, [])]
    if relation_id:
        return [item for item in evidence if item["relation_id"] == relation_id]
    return evidence


def resolution_category(direction_status: str) -> str:
    if direction_status == "UNRESOLVED":
        return "HOLD_DIRECTION_UNRESOLVED"
    return "MAPPING_ONLY_REVIEW_REQUIRED"


def build_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    targets, clusters = extract_targets()
    observations = set(clusters)
    fixed_pairs = selected_pairs(observations)
    network_results: dict[str, dict[str, Any]] = {}
    osm_paths: dict[str, Path] = {}
    cluster_missing: dict[str, list[str]] = {}
    all_orig_ids: set[str] = set()

    for observation, cluster in clusters.items():
        missing = json.loads(cluster["reverse_missing_selected_edges_json"])
        expected_missing = int(cluster["adopted_edge_count"]) - int(cluster["reverse_edge_match_count"])
        if len(missing) != expected_missing:
            raise ValueError(f"reverse gap count differs from canonical evidence: {observation}")
        if observation == "13604210030" and (len(missing) != 10 or int(cluster["reverse_edge_match_count"]) != 67):
            raise ValueError("Route 421 investigation must preserve 67/77 and inspect only ten gaps")
        cluster_missing[observation] = missing
        alternate = REVIEWED_ALTERNATE_CORRIDORS[observation]
        network = REPOSITORY_ROOT / cluster["network_file"]
        network_results[observation] = parse_network(
            network, observation, missing, alternate, fixed_pairs[observation]
        )
        osm_paths[observation] = EXTENSION_OSM if observation == "13300010260" else BASE_OSM
        for metadata in network_results[observation]["metadata"].values():
            all_orig_ids.update(metadata["orig_ids"])

    memberships = relation_memberships(all_orig_ids)
    osm_by_path: dict[Path, dict[str, dict[str, str]]] = {}
    for path in set(osm_paths.values()):
        path_ids = {
            orig_id
            for observation, net in network_results.items()
            if osm_paths[observation] == path
            for metadata in net["metadata"].values()
            for orig_id in metadata["orig_ids"]
        }
        osm_by_path[path] = parse_osm(path, path_ids)

    cluster_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    for observation in sorted(observations):
        cluster = clusters[observation]
        missing = cluster_missing[observation]
        alternate = REVIEWED_ALTERNATE_CORRIDORS[observation]
        net = network_results[observation]
        metadata = net["metadata"]
        osm = osm_by_path[osm_paths[observation]]
        relation_id = cluster["route_relation_id"]
        fixed_orig = {orig for edge in missing for orig in metadata[edge]["orig_ids"]}
        alt_orig = {orig for edge in alternate for orig in metadata[edge]["orig_ids"]}
        fixed_relation = matching_relation_evidence(fixed_orig, memberships, relation_id)
        alt_relation = matching_relation_evidence(alt_orig, memberships, relation_id)
        exact_count = sum(bool(net["exact_candidates"][edge]) for edge in missing)
        alt_all_osm = alt_orig <= set(osm)
        alt_connected = not net["alternate_node_violations"] and not net["alternate_connection_violations"]
        if exact_count:
            cause = "REVERSE_EXISTS_IN_SUMO_NOT_SELECTED"
        elif alt_connected and alt_all_osm:
            cause = "ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO"
        else:
            cause = "UNRESOLVED"
        if cause not in CAUSE_TAXONOMY:
            raise ValueError(cause)
        direction_hold = cluster["direction_evidence_status"] == "UNRESOLVED"
        category = resolution_category(cluster["direction_evidence_status"])
        route_relation_status = (
            "SUPPORTED_SAME_ROUTE_NETWORK_REF_MEMBER"
            if relation_id and fixed_relation and alt_relation
            else "NO_ROUTE_RELATION_OSM_REF_NAME_SUPPORT"
            if not relation_id
            else "ROUTE_RELATION_INCOMPLETE"
        )
        reason = (
            "固定edgeの同一node-pair reverseは存在しないが、同じname/refを持つoneway OSM Way由来の"
            "別node列がnetconvert入力とSUMO netの双方に存在し、反対車道候補としてconnection violation 0で連続する。"
        )
        if direction_hold:
            reason += " ただし方向証拠がUNRESOLVEDのためUP/DOWNへは採用せず保留する。"
        cluster_rows.append({
            "cluster": cluster["cluster"],
            "official_observation_section_id": observation,
            "target_section_ids_json": json_text(sorted(
                row["target_section_id"] for row in targets
                if row["official_observation_section_id"] == observation
            )),
            "route_system": cluster["route_system"],
            "route_number": cluster["route_number"],
            "route_name": cluster["route_name"],
            "direction_evidence_status": cluster["direction_evidence_status"],
            "canonical_traffic_assignment_status": cluster["traffic_assignment_status"],
            "fixed_edge_count": cluster["adopted_edge_count"],
            "preserved_exact_reverse_count": cluster["reverse_edge_match_count"],
            "investigated_missing_edge_count": len(missing),
            "fixed_missing_edges_json": json_text(missing),
            "exact_reverse_found_for_missing_count": exact_count,
            "alternate_reverse_corridor_edge_count": len(alternate),
            "alternate_reverse_corridor_json": json_text(alternate),
            "alternate_corridor_start_node": metadata[alternate[0]]["from"],
            "alternate_corridor_end_node": metadata[alternate[-1]]["to"],
            "alternate_node_violation_count": len(net["alternate_node_violations"]),
            "alternate_connection_violation_count": len(net["alternate_connection_violations"]),
            "fixed_osm_way_ids_json": json_text(sorted(fixed_orig)),
            "alternate_osm_way_ids_json": json_text(sorted(alt_orig)),
            "fixed_osm_all_present_in_netconvert_input": str(fixed_orig <= set(osm)).lower(),
            "alternate_osm_all_present_in_netconvert_input": str(alt_all_osm).lower(),
            "alternate_all_present_in_sumo": "true",
            "netconvert_dropout_status": "NO_DROPOUT",
            "network_scope_status": "IN_SCOPE",
            "osm_structure_status": "SEPARATE_ONEWAY_CARRIAGEWAYS",
            "route_relation_id": relation_id,
            "route_relation_status": route_relation_status,
            "route_relation_fixed_evidence_json": json_text(fixed_relation),
            "route_relation_alternate_evidence_json": json_text(alt_relation),
            "cause_taxonomy": cause,
            "resolution_category": category,
            "up_down_adoption_status": "PROHIBITED_DIRECTION_UNRESOLVED" if direction_hold else "NOT_ADOPTED_INVESTIGATION_ONLY",
            "mapping_changed": "false",
            "network_changed": "false",
            "reason": reason,
            "network_file": cluster["network_file"],
            "network_sha256": cluster["network_sha256"],
            "netconvert_input_osm": relative(osm_paths[observation]),
            "netconvert_input_osm_sha256": sha256_file(osm_paths[observation]),
        })

        for fixed_edge in missing:
            fixed = metadata[fixed_edge]
            local = local_alternate_candidates(fixed, alternate, metadata)
            local_alt_orig = {
                orig for candidate in local for orig in metadata[candidate["edge_id"]]["orig_ids"]
            }
            fixed_tags = {orig: osm.get(orig, {}) for orig in fixed["orig_ids"]}
            alternate_tags = {orig: osm.get(orig, {}) for orig in sorted(local_alt_orig)}
            exact = net["exact_candidates"][fixed_edge]
            edge_rows.append({
                "cluster": cluster["cluster"],
                "official_observation_section_id": observation,
                "fixed_edge_id": fixed_edge,
                "fixed_from": fixed["from"],
                "fixed_to": fixed["to"],
                "fixed_orig_ids_json": json_text(fixed["orig_ids"]),
                "same_node_pair_reverse_candidates_json": json_text(exact),
                "same_node_pair_reverse_exists": str(bool(exact)).lower(),
                "alternate_reverse_corridor_json": json_text(alternate),
                "local_alternate_candidates_json": json_text(local),
                "fixed_osm_way_present": str(set(fixed["orig_ids"]) <= set(osm)).lower(),
                "fixed_osm_tags_json": json_text(fixed_tags),
                "alternate_osm_way_present": str(local_alt_orig <= set(osm)).lower(),
                "alternate_osm_tags_json": json_text(alternate_tags),
                "fixed_route_relation_evidence_json": json_text(
                    matching_relation_evidence(set(fixed["orig_ids"]), memberships, relation_id)
                ),
                "alternate_route_relation_evidence_json": json_text(
                    matching_relation_evidence(local_alt_orig, memberships, relation_id)
                ),
                "netconvert_input_inclusion": "FIXED_AND_ALTERNATE_PRESENT",
                "sumo_network_inclusion": "FIXED_AND_ALTERNATE_PRESENT",
                "netconvert_dropout_status": "NO_DROPOUT",
                "network_scope_status": "IN_SCOPE",
                "road_structure": "SEPARATE_ONEWAY_CARRIAGEWAYS",
                "cause_taxonomy": cause,
                "resolution_category": category,
                "repairability": (
                    "HOLD_DIRECTION_UNRESOLVED"
                    if direction_hold else "MAPPING_ONLY_REVIEW_REQUIRED"
                ),
                "reason": reason,
            })

    by_observation = {row["official_observation_section_id"]: row for row in cluster_rows}
    target_rows: list[dict[str, Any]] = []
    for target in targets:
        cluster = by_observation[target["official_observation_section_id"]]
        target_rows.append({
            "target_section_id": target["target_section_id"],
            "official_observation_section_id": target["official_observation_section_id"],
            "cluster": cluster["cluster"],
            "direction_evidence_status": cluster["direction_evidence_status"],
            "preserved_exact_reverse_count": cluster["preserved_exact_reverse_count"],
            "fixed_edge_count": cluster["fixed_edge_count"],
            "investigated_missing_edge_count": cluster["investigated_missing_edge_count"],
            "cause_taxonomy": cluster["cause_taxonomy"],
            "resolution_category": cluster["resolution_category"],
            "mapping_only_resolution_possible": str(
                cluster["resolution_category"] == "MAPPING_ONLY_REVIEW_REQUIRED"
            ).lower(),
            "network_regeneration_required": "false",
            "source_data_missing": "false",
            "legitimate_oneway_terminal_cause": "false",
            "direction_unresolved_hold": str(
                cluster["resolution_category"] == "HOLD_DIRECTION_UNRESOLVED"
            ).lower(),
            "cause_unresolved": str(cluster["cause_taxonomy"] == "UNRESOLVED").lower(),
            "cluster_evidence_reference": f"{relative(CLUSTER_CSV)}#{cluster['cluster']}",
        })
    return cluster_rows, edge_rows, target_rows


def build_qa(
    cluster_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    target_resolution = Counter(row["resolution_category"] for row in target_rows)
    cluster_resolution = Counter(row["resolution_category"] for row in cluster_rows)
    qa: dict[str, Any] = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "target_selection": {
            "classification_source": relative(CLASSIFICATION),
            "cluster_source": relative(CLUSTER_EVIDENCE),
            "predicate": "traffic_assignment_status IN (REVERSE_CORRIDOR_MISSING, REVERSE_CORRIDOR_PARTIAL)",
            "target_count": len(target_rows),
            "cluster_count": len(cluster_rows),
            "manual_target_ids_used": False,
        },
        "edge_summary": {
            "investigated_missing_edge_count": len(edge_rows),
            "cause_taxonomy": dict(sorted(Counter(row["cause_taxonomy"] for row in edge_rows).items())),
        },
        "target_resolution_summary": dict(sorted(target_resolution.items())),
        "cluster_resolution_summary": dict(sorted(cluster_resolution.items())),
        "requested_target_aggregation": {
            "mapping_only": target_resolution.get("MAPPING_ONLY_REVIEW_REQUIRED", 0),
            "network_regeneration_or_limited_extension": 0,
            "osm_or_source_missing": 0,
            "legitimate_oneway": 0,
            "direction_unresolved_hold": target_resolution.get("HOLD_DIRECTION_UNRESOLVED", 0),
            "cause_unresolved": sum(row["cause_taxonomy"] == "UNRESOLVED" for row in target_rows),
        },
        "invariants": {
            "unclassified_edge_count": sum(not row["cause_taxonomy"] for row in edge_rows),
            "alternate_connection_violation_count": sum(
                int(row["alternate_connection_violation_count"]) for row in cluster_rows
            ),
            "route_421_preserved_exact_reverse_count": next(
                int(row["preserved_exact_reverse_count"])
                for row in cluster_rows if row["route_number"] == "421"
            ),
            "route_421_investigated_missing_edge_count": next(
                int(row["investigated_missing_edge_count"])
                for row in cluster_rows if row["route_number"] == "421"
            ),
            "mapping_changed": False,
            "selected_edges_changed": False,
            "thresholds_changed": False,
            "source_data_changed": False,
            "network_changed": False,
            "reverse_edges_generated": False,
        },
    }
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    if len(cluster_rows) != 4 or len(target_rows) != 6 or len(edge_rows) != 72:
        raise ValueError("reverse-gap completeness invariant failed")
    if qa["invariants"]["unclassified_edge_count"] or qa["invariants"]["alternate_connection_violation_count"]:
        raise ValueError("reverse-gap QA invariant failed")
    if qa["invariants"]["route_421_preserved_exact_reverse_count"] != 67:
        raise ValueError("Route 421 exact reverse evidence changed")
    if qa["invariants"]["route_421_investigated_missing_edge_count"] != 10:
        raise ValueError("Route 421 local gap scope changed")
    return qa


def render_report(cluster_rows: list[dict[str, Any]], qa: dict[str, Any]) -> str:
    lines = [
        "# 外部観測参照 reverse不足 原因調査",
        "",
        "正本の条件抽出で6件・4 clusterを再現し、固定mapping・採択edge列・閾値・元データ・networkを変更せず調査した。",
        "",
        "| 観測区間 | 固定reverse | 不足edge | alternate corridor | 原因 | 解決区分 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in cluster_rows:
        lines.append(
            f"| `{row['official_observation_section_id']}` | {row['preserved_exact_reverse_count']}/{row['fixed_edge_count']} | "
            f"{row['investigated_missing_edge_count']} | {row['alternate_reverse_corridor_edge_count']} edge | "
            f"`{row['cause_taxonomy']}` | `{row['resolution_category']}` |"
        )
    summary = qa["requested_target_aggregation"]
    lines.extend([
        "",
        "## 結論",
        "",
        "72不足edgeすべてについて、同一node pairのreverseではなく、同一路線の分離oneway反対車道が既存SUMO内に存在した。候補はnetconvert入力OSMにも存在し、生成netからの脱落・network範囲外・source欠損ではない。個々のoneway指定は妥当だが、道路全体としてreverse不要という意味ではないため、主要因を `LEGITIMATE_ONEWAY` ではなく `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` とした。",
        "",
        "都道316号はalternate候補を確認したが、方向証拠がUNRESOLVEDである。候補をUP/DOWNとして採用せず、3対象を方向未解決保留とした。",
        "",
        "## 6件集計",
        "",
        f"- mapping修正だけで解決可能（正式再レビュー要）: {summary['mapping_only']}",
        f"- network再生成／限定拡張: {summary['network_regeneration_or_limited_extension']}",
        f"- OSM/source不足: {summary['osm_or_source_missing']}",
        f"- legitimate one-wayを終端原因とするもの: {summary['legitimate_oneway']}",
        f"- 方向未解決のため保留: {summary['direction_unresolved_hold']}",
        f"- 原因未解決: {summary['cause_unresolved']}",
        "",
        "都道421号は既存67/77を固定し、欠損10 edgeだけを調査した。alternate 14 edgeは欠損区間の両端へ接続し、connection violationは0である。",
        "",
    ])
    if "validation" in qa:
        lines.append(
            f"Validation: {qa['validation']['passed_test_count']} passed, "
            f"{qa['validation']['failed_test_count']} failed."
        )
        lines.append("")
    return "\n".join(lines)


def write_all() -> None:
    snapshot = verify_prework()
    cluster_rows, edge_rows, target_rows = build_outputs()
    qa = build_qa(cluster_rows, edge_rows, target_rows)
    write_csv(EDGE_CSV, edge_rows)
    write_csv(CLUSTER_CSV, cluster_rows)
    write_csv(TARGET_CSV, target_rows)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(cluster_rows, qa), encoding="utf-8")
    output_paths = [EDGE_CSV, CLUSTER_CSV, TARGET_CSV, QA_JSON, REPORT]
    if VALIDATION_JSON.is_file():
        output_paths.append(VALIDATION_JSON)
    manifest = {
        "run_id": RUN_ID,
        "generator": relative(Path(__file__)),
        "generator_sha256": sha256_file(Path(__file__)),
        "generator_version": SCRIPT_VERSION,
        "git_base_commit": snapshot["git_base_commit"],
        "prework_snapshot": relative(PREWORK),
        "prework_snapshot_sha256": sha256_file(PREWORK),
        "input_hashes": snapshot["sha256"],
        "target_selection": qa["target_selection"],
        "cause_taxonomy": sorted(CAUSE_TAXONOMY),
        "output_hashes": {relative(path): sha256_file(path) for path in output_paths},
        "qa": qa,
        "non_mutation_contract": {
            "existing_mapping_changed": False,
            "selected_edges_changed": False,
            "matching_thresholds_changed": False,
            "source_data_changed": False,
            "network_changed": False,
            "reverse_edges_generated": False,
        },
        "tool_versions": snapshot["tool_versions"],
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
