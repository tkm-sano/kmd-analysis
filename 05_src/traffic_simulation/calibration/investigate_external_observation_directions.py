"""Finalize direction evidence and fixed-corridor traffic usability for nine mappings.

Targets are selected exclusively from the canonical external-observation
inventory.  This program does not search for edges, alter a mapping, create a
reverse edge, or use GeoJSON coordinate order, bearing, or traffic magnitude.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any
import xml.etree.ElementTree as ET

from traffic_simulation.paths import REPOSITORY_ROOT


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_direction_investigation_20260827_v1"
DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
INVENTORY = DATA_DIR / "external_observation_final_inventory.csv"
FORMAL_MAPPING = DATA_DIR / "external_observation_final_mapping.csv"
FORMAL_EDGE_EVIDENCE = DATA_DIR / "external_observation_mapping_final_edge_evidence.csv"
BASE_MAPPING = DATA_DIR / "census_section_final_mapping.csv"
ROAD_CENSUS = (
    REPOSITORY_ROOT
    / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823/kasyo13.csv"
)
ROUTE_RELATIONS = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
)
BASE_OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_baseline_explicit_v17_oneway.osm.xml"
)
CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
NORMALIZER = REPOSITORY_ROOT / "05_src/traffic_simulation/calibration/normalize_road_census_section_attributes.py"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_direction_final_review.md"

CLASSIFICATION_CSV = DATA_DIR / "external_observation_direction_final_classification.csv"
CLUSTER_CSV = DATA_DIR / "external_observation_direction_cluster_evidence.csv"
RULES_CSV = DATA_DIR / "external_observation_direction_rules.csv"
ASSUMPTIONS_CSV = DATA_DIR / "external_observation_direction_assumption_candidates.csv"
QA_JSON = DATA_DIR / "external_observation_direction_qa.json"
MANIFEST_JSON = DATA_DIR / "external_observation_direction_manifest.json"
VALIDATION_JSON = DATA_DIR / "external_observation_direction_validation.json"

MLIT_DEFINITION_URL = "https://www.mlit.go.jp/road/census/r3/data/pdf/kasyorep.pdf"
MLIT_DEFINITION_SHA256 = "88c18b15bac402384ca1ce1d78ed2481bc639491f74b57c2917f6771e6076fb1"
EXPECTED_INPUT_HASHES = {
    INVENTORY: "bcc5ce7e12914500ea853c1d477dad7e917c9647655ab1d7b5f0c64c0d94e2e0",
    FORMAL_MAPPING: "0e81382a5cef5a566643742de0db407d53431c78533ec57ba662614e5c3a20c6",
    FORMAL_EDGE_EVIDENCE: "d45df421a8b318f133c1cdd34e9411ab550ecb9197a276f7aa125d61e1fa2a0f",
    BASE_MAPPING: "c321c161c965d65dc3f77ecfa01efe81ec0e48461bf36f1ad89aa787d350820c",
    ROAD_CENSUS: "37c41661cf92ee0f9964138694f43c5764f237dc061262f6457bbb6dd3e30c85",
    ROUTE_RELATIONS: "4197b97b2d3c9706d973f7b2e4d08c83618778d6411528f71b47e1df3e70dc56",
    BASE_OSM: "46b8f712f58b399c8e8caecbdbe82f74899d333342e10cbc750c67ccc685daa5",
    CONFIG: "74c9afe746deafe97c865c825ac30f010c7086fd0f73f43c034c1a1e4ff4afea",
    NORMALIZER: "900e2b514e59e5795586dbe510f41745e20000787eb57d2f74ce425c4539dff7",
}

UP = "UP_TERMINUS_TO_ORIGIN"
DOWN = "DOWN_ORIGIN_TO_TERMINUS"
UNASSIGNED = "UNASSIGNED_DIRECTION"


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


def verify_locked_inputs() -> dict[str, str]:
    actual = {relative(path): sha256_file(path) for path in EXPECTED_INPUT_HASHES}
    for path, expected in EXPECTED_INPUT_HASHES.items():
        if actual[relative(path)] != expected:
            raise ValueError(f"locked input changed: {relative(path)}")
    return actual


def extract_targets() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_csv(INVENTORY)
        if row["mapping_status"] == "RESOLVED"
        and row["direction_status"] == "MODEL_ASSUMPTION_REQUIRED"
    ]
    if len(rows) != 9:
        raise ValueError(f"canonical inventory target count is {len(rows)}, expected 9")
    if len({row["official_observation_section_id"] for row in rows}) != 5:
        raise ValueError("canonical inventory does not yield five observation clusters")
    return sorted(rows, key=lambda row: row["target_section_id"])


def unique_formal_mappings() -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(FORMAL_MAPPING):
        grouped[row["official_observation_section_id"]].append(row)
    result: dict[str, dict[str, str]] = {}
    invariant_fields = [
        "final_sumo_edge_sequence",
        "route_relation_id",
        "adopted_route_system",
        "adopted_route_number",
        "adopted_route_name",
        "input_files_json",
    ]
    for observation, rows in grouped.items():
        for field in invariant_fields:
            if len({row[field] for row in rows}) != 1:
                raise ValueError(f"cluster mapping differs for {observation}: {field}")
        result[observation] = rows[0]
    return result


def census_rows(section_ids: set[str]) -> dict[str, dict[str, str]]:
    rows = {
        row["交通調査基本区間番号"]: row
        for row in read_csv(ROAD_CENSUS, encoding="cp932")
        if row["交通調査基本区間番号"] in section_ids
    }
    missing = section_ids - set(rows)
    if missing:
        raise ValueError(f"Road Census rows missing: {sorted(missing)}")
    return rows


def way_id(edge_id: str) -> str:
    return edge_id.lstrip("-").split("#", 1)[0]


def selected_edge_metadata(
    target_observations: set[str], formal: dict[str, dict[str, str]]
) -> tuple[dict[str, dict[str, tuple[str, str]]], dict[str, str]]:
    evidence = read_csv(FORMAL_EDGE_EVIDENCE)
    by_observation: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    network_by_observation: dict[str, str] = {}
    for row in evidence:
        observation = row["official_observation_section_id"]
        if observation not in target_observations:
            continue
        edge_id = row["edge_id"]
        pair = (row["sumo_from"], row["sumo_to"])
        old = by_observation[observation].get(edge_id)
        if old is not None and old != pair:
            raise ValueError(f"edge evidence differs within cluster: {observation}/{edge_id}")
        by_observation[observation][edge_id] = pair
        network_by_observation.setdefault(observation, row["network_file"])
        if network_by_observation[observation] != row["network_file"]:
            raise ValueError(f"multiple networks in cluster: {observation}")
    for observation in target_observations:
        selected = formal[observation]["final_sumo_edge_sequence"].split(";")
        if set(selected) - set(by_observation[observation]):
            raise ValueError(f"selected edge evidence missing: {observation}")
    return dict(by_observation), network_by_observation


def parse_network_evidence(
    targets: list[dict[str, str]],
    formal: dict[str, dict[str, str]],
    selected_meta: dict[str, dict[str, tuple[str, str]]],
    network_by_observation: dict[str, str],
    base_mapping: dict[str, dict[str, str]],
) -> dict[str, dict[str, Any]]:
    jobs: dict[str, list[str]] = defaultdict(list)
    for observation, network in network_by_observation.items():
        jobs[network].append(observation)
    target_ids_by_observation: dict[str, list[str]] = defaultdict(list)
    for row in targets:
        target_ids_by_observation[row["official_observation_section_id"]].append(
            row["target_section_id"]
        )

    result: dict[str, dict[str, Any]] = {}
    for network_rel, observations in jobs.items():
        network_path = REPOSITORY_ROOT / network_rel
        reverse_pairs: set[tuple[str, str]] = set()
        endpoint_nodes: set[str] = set()
        required_edges: set[str] = set()
        required_connections: set[tuple[str, str]] = set()
        for observation in observations:
            selected = formal[observation]["final_sumo_edge_sequence"].split(";")
            pairs = [selected_meta[observation][edge] for edge in selected]
            reverse_pairs.update((to_node, from_node) for from_node, to_node in pairs)
            endpoint_nodes.update((pairs[0][0], pairs[-1][1]))
            required_edges.update(selected)
            required_connections.update(zip(selected, selected[1:]))
            for target_id in target_ids_by_observation[observation]:
                required_edges.update(base_mapping[target_id]["final_edge_ids"].split(";"))

        actual_meta: dict[str, tuple[str, str]] = {}
        reverse_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
        reverse_candidate_ids: set[str] = set()
        incident_by_node: dict[str, list[str]] = defaultdict(list)
        connections: set[tuple[str, str]] = set()
        for _, element in ET.iterparse(network_path, events=("end",)):
            if element.tag == "edge":
                edge_id = element.attrib.get("id", "")
                if edge_id and not edge_id.startswith(":") and "from" in element.attrib:
                    pair = (element.attrib["from"], element.attrib["to"])
                    if edge_id in required_edges:
                        actual_meta[edge_id] = pair
                    if pair in reverse_pairs:
                        reverse_by_pair[pair].append(edge_id)
                        reverse_candidate_ids.add(edge_id)
                    for node in pair:
                        if node in endpoint_nodes:
                            incident_by_node[node].append(edge_id)
                element.clear()
            elif element.tag == "connection":
                pair = (element.attrib.get("from", ""), element.attrib.get("to", ""))
                if pair in required_connections or (
                    pair[0] in reverse_candidate_ids and pair[1] in reverse_candidate_ids
                ):
                    connections.add(pair)
                element.clear()

        for observation in observations:
            selected = formal[observation]["final_sumo_edge_sequence"].split(";")
            if any(actual_meta.get(edge) != selected_meta[observation][edge] for edge in selected):
                raise ValueError(f"SUMO edge metadata changed: {observation}")
            connection_violations = sum(
                (left, right) not in connections for left, right in zip(selected, selected[1:])
            )
            pairs = [actual_meta[edge] for edge in selected]
            reverse_slots: list[str] = []
            missing_edges: list[str] = []
            ambiguous_edges: list[str] = []
            for edge in reversed(selected):
                from_node, to_node = actual_meta[edge]
                candidates = sorted(reverse_by_pair.get((to_node, from_node), []))
                if len(candidates) == 1:
                    reverse_slots.append(candidates[0])
                else:
                    reverse_slots.append("")
                    if candidates:
                        ambiguous_edges.append(edge)
                    else:
                        missing_edges.append(edge)
            reverse_complete = all(reverse_slots)
            reverse_connection_violations = 0
            if reverse_complete:
                reverse_connection_violations = sum(
                    (left, right) not in connections
                    for left, right in zip(reverse_slots, reverse_slots[1:])
                )
            target_nodes: dict[str, set[str]] = {}
            for target_id in target_ids_by_observation[observation]:
                nodes: set[str] = set()
                for edge in base_mapping[target_id]["final_edge_ids"].split(";"):
                    if edge not in actual_meta:
                        raise ValueError(f"target edge absent from selected network: {target_id}/{edge}")
                    nodes.update(actual_meta[edge])
                target_nodes[target_id] = nodes
            start_node, end_node = pairs[0][0], pairs[-1][1]
            result[observation] = {
                "network_path": network_path,
                "selected": selected,
                "pairs": pairs,
                "start_node": start_node,
                "end_node": end_node,
                "incident_start": sorted(set(incident_by_node[start_node]) - set(selected)),
                "incident_end": sorted(set(incident_by_node[end_node]) - set(selected)),
                "target_nodes": target_nodes,
                "reverse_slots": reverse_slots,
                "missing_edges": missing_edges,
                "ambiguous_edges": ambiguous_edges,
                "connection_violations": connection_violations,
                "reverse_connection_violations": reverse_connection_violations,
            }
    return result


def parse_osm_way_tags(edge_ids: set[str]) -> dict[str, dict[str, str]]:
    wanted = {way_id(edge) for edge in edge_ids}
    found: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(BASE_OSM, events=("end",)):
        if element.tag != "way":
            continue
        osm_id = element.attrib.get("id", "")
        if osm_id in wanted:
            found[osm_id] = {
                child.attrib["k"]: child.attrib.get("v", "")
                for child in element
                if child.tag == "tag" and "k" in child.attrib
            }
        element.clear()
    return found


def parse_route_relations(relation_ids: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for _, element in ET.iterparse(ROUTE_RELATIONS, events=("end",)):
        if element.tag != "relation":
            continue
        relation_id = element.attrib.get("id", "")
        if relation_id in relation_ids:
            members = [
                {"index": index, "ref": child.attrib.get("ref", ""), "role": child.attrib.get("role", "")}
                for index, child in enumerate(child for child in element if child.tag == "member")
                if child.attrib.get("type") == "way"
            ]
            tags = {
                child.attrib["k"]: child.attrib.get("v", "")
                for child in element
                if child.tag == "tag" and "k" in child.attrib
            }
            result[relation_id] = {"members": members, "tags": tags}
        element.clear()
    return result


def relation_explicit_origin_to_terminus(
    relation: dict[str, Any] | None, selected: list[str]
) -> tuple[bool, list[dict[str, Any]]]:
    if not relation:
        return False, []
    note = " ".join(
        value for key, value in relation["tags"].items() if key == "note" or key.startswith("note:")
    )
    if "起点から終点" not in note:
        return False, []
    selected_ways: list[str] = []
    for edge in selected:
        osm_way = way_id(edge)
        if not selected_ways or selected_ways[-1] != osm_way:
            selected_ways.append(osm_way)
    positions: list[dict[str, Any]] = []
    for selected_way in selected_ways:
        matches = [member for member in relation["members"] if member["ref"] == selected_way]
        if len(matches) != 1:
            return False, []
        positions.append(matches[0])
    indices = [item["index"] for item in positions]
    roles = [item["role"] for item in positions]
    return indices == list(range(indices[0], indices[0] + len(indices))) and all(
        role == "forward" for role in roles
    ), positions


def cluster_id(mapping: dict[str, str]) -> str:
    system = mapping["adopted_route_system"].replace(":", "_")
    return f"ROUTE_{system}_{mapping['adopted_route_number']}"


def direction_from_endpoint(endpoint: str, position: str) -> str:
    if endpoint == "ORIGIN" and position == "START":
        return DOWN
    if endpoint == "ORIGIN" and position == "END":
        return UP
    if endpoint == "TERMINUS" and position == "START":
        return UP
    if endpoint == "TERMINUS" and position == "END":
        return DOWN
    raise ValueError((endpoint, position))


def decide_direction(
    observation: str,
    target_rows: list[dict[str, str]],
    mapping: dict[str, str],
    census: dict[str, dict[str, str]],
    net: dict[str, Any],
    way_tags: dict[str, dict[str, str]],
    relation: dict[str, Any] | None,
) -> dict[str, Any]:
    raw = census[observation]
    origin_label = raw["起点側／路線名等"]
    terminus_label = raw["終点側／路線名等"]

    boundary_matches: list[tuple[str, str, str]] = []
    for target in target_rows:
        target_id = target["target_section_id"]
        target_raw = census[target_id]
        shared_start = net["start_node"] in net["target_nodes"][target_id]
        shared_end = net["end_node"] in net["target_nodes"][target_id]
        if "区境" in origin_label and target_raw["終点側／路線名等"] == origin_label:
            if shared_start:
                boundary_matches.append(("ORIGIN", "START", target_id))
            if shared_end:
                boundary_matches.append(("ORIGIN", "END", target_id))
        if "区境" in terminus_label and target_raw["起点側／路線名等"] == terminus_label:
            if shared_start:
                boundary_matches.append(("TERMINUS", "START", target_id))
            if shared_end:
                boundary_matches.append(("TERMINUS", "END", target_id))
    if len(boundary_matches) == 1:
        endpoint, position, target_id = boundary_matches[0]
        role = direction_from_endpoint(endpoint, position)
        return {
            "status": "RESOLVED",
            "selected_role": role,
            "rule_id": "OFFICIAL_ADJACENT_BOUNDARY_SUMO_TOPOLOGY_V1",
            "reason_code": "OFFICIAL_BOUNDARY_ENDPOINT_ANCHORED_IN_SUMO_TOPOLOGY",
            "reason": (
                f"原票で{observation}の{endpoint}側と隣接区間{target_id}が同一の区境を共有し、"
                f"固定列の{position} nodeが隣接区間mappingのnode集合と一致した。"
            ),
            "anchor_json": {"endpoint": endpoint, "position": position, "target_section_id": target_id},
        }

    selected_way_ids = {way_id(edge) for edge in net["selected"]}
    for endpoint, label in (("ORIGIN", origin_label), ("TERMINUS", terminus_label)):
        for position, incident_edges in (("START", net["incident_start"]), ("END", net["incident_end"])):
            matches = []
            for edge in incident_edges:
                osm_way = way_id(edge)
                if osm_way in selected_way_ids:
                    continue
                tags = way_tags.get(osm_way, {})
                if label and label in {tags.get("name", ""), tags.get("name:ja", "")}:
                    matches.append({"edge_id": edge, "osm_way_id": osm_way, "name": label})
            if len(matches) == 1:
                role = direction_from_endpoint(endpoint, position)
                return {
                    "status": "RESOLVED",
                    "selected_role": role,
                    "rule_id": "OFFICIAL_ENDPOINT_OSM_SUMO_INTERSECTION_V1",
                    "reason_code": "OFFICIAL_ENDPOINT_ROAD_MATCHED_AT_SUMO_ENDPOINT",
                    "reason": (
                        f"原票の{endpoint}側接続路線「{label}」が固定列の{position} nodeに接続する"
                        f"OSM/SUMO edgeで一意に確認された。"
                    ),
                    "anchor_json": {"endpoint": endpoint, "position": position, "matches": matches},
                }

    explicit, positions = relation_explicit_origin_to_terminus(relation, net["selected"])
    if explicit:
        return {
            "status": "RESOLVED",
            "selected_role": DOWN,
            "rule_id": "OSM_RELATION_EXPLICIT_ORIGIN_TERMINUS_SEQUENCE_V1",
            "reason_code": "EXPLICIT_RELATION_SEQUENCE_AND_FORWARD_ROLES",
            "reason": (
                "route relationの注記が起点から終点までの順序を明示し、固定列のOSM wayが"
                "連続memberかつ全てrole=forwardであるため、固定列をDOWNと判定した。"
            ),
            "anchor_json": {"relation_member_evidence": positions},
        }

    return {
        "status": "UNRESOLVED",
        "selected_role": UNASSIGNED,
        "rule_id": "INSUFFICIENT_OFFICIAL_ENDPOINT_ANCHOR_V1",
        "reason_code": "OFFICIAL_ENDPOINT_NOT_ANCHORED_TO_FIXED_EDGE_ENDPOINT",
        "reason": (
            "原票の起点・終点は確認できるが、部分被覆の固定列端点をどちらへ対応させるかを"
            "公式隣接区間、接続路線、または明示的relation方向から一意に確定できない。"
        ),
        "anchor_json": {},
    }


def traffic_status(net: dict[str, Any]) -> str:
    found = sum(bool(edge) for edge in net["reverse_slots"])
    total = len(net["selected"])
    if found == total and net["reverse_connection_violations"] == 0:
        return "BIDIRECTIONAL_ASSIGNABLE"
    if found == 0:
        return "REVERSE_CORRIDOR_MISSING"
    if found < total:
        return "REVERSE_CORRIDOR_PARTIAL"
    return "UNRESOLVED"


def build_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    targets = extract_targets()
    target_observations = {row["official_observation_section_id"] for row in targets}
    formal = unique_formal_mappings()
    base_mapping = {row["section_id"]: row for row in read_csv(BASE_MAPPING)}
    section_ids = {row["target_section_id"] for row in targets} | target_observations
    census = census_rows(section_ids)
    selected_meta, network_by_observation = selected_edge_metadata(target_observations, formal)
    network = parse_network_evidence(
        targets, formal, selected_meta, network_by_observation, base_mapping
    )
    incident_edges = {
        edge
        for evidence in network.values()
        for edge in evidence["incident_start"] + evidence["incident_end"]
    }
    way_tags = parse_osm_way_tags(incident_edges)
    relation_ids = {
        formal[observation]["route_relation_id"]
        for observation in target_observations
        if formal[observation]["route_relation_id"]
    }
    relations = parse_route_relations(relation_ids)

    targets_by_observation: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in targets:
        targets_by_observation[row["official_observation_section_id"]].append(row)

    cluster_rows: list[dict[str, Any]] = []
    decisions: dict[str, dict[str, Any]] = {}
    for observation in sorted(target_observations):
        mapping = formal[observation]
        raw = census[observation]
        net = network[observation]
        relation_id = mapping["route_relation_id"]
        decision = decide_direction(
            observation,
            targets_by_observation[observation],
            mapping,
            census,
            net,
            way_tags,
            relations.get(relation_id),
        )
        decisions[observation] = decision
        found = sum(bool(edge) for edge in net["reverse_slots"])
        total = len(net["selected"])
        status = traffic_status(net)
        reverse_complete = status == "BIDIRECTIONAL_ASSIGNABLE"
        selected_text = ";".join(net["selected"])
        reverse_text = ";".join(net["reverse_slots"]) if reverse_complete else ""
        up_edges = ""
        down_edges = ""
        if decision["status"] == "RESOLVED":
            if decision["selected_role"] == UP:
                up_edges = selected_text
                down_edges = reverse_text
            else:
                down_edges = selected_text
                up_edges = reverse_text
        relation = relations.get(relation_id, {})
        relation_tags = relation.get("tags", {})
        cluster_rows.append(
            {
                "cluster": cluster_id(mapping),
                "official_observation_section_id": observation,
                "target_section_ids_json": json_text(
                    sorted(row["target_section_id"] for row in targets_by_observation[observation])
                ),
                "route_system": mapping["adopted_route_system"],
                "route_number": mapping["adopted_route_number"],
                "route_name": mapping["adopted_route_name"],
                "route_relation_id": relation_id,
                "official_direction_definition": "UP=TERMINUS_TO_ORIGIN;DOWN=ORIGIN_TO_TERMINUS",
                "official_direction_definition_url": MLIT_DEFINITION_URL,
                "official_origin_connection_type": raw["起点側／接続区分"],
                "official_origin_adjacent_section_id": raw["起点側／交通調査基本区間番号"],
                "official_origin_label": raw["起点側／路線名等"],
                "official_terminus_connection_type": raw["終点側／接続区分"],
                "official_terminus_adjacent_section_id": raw["終点側／交通調査基本区間番号"],
                "official_terminus_label": raw["終点側／路線名等"],
                "official_oneway_flag": raw["一方通行フラグ"],
                "adopted_edge_sequence": selected_text,
                "adopted_sequence_role": decision["selected_role"],
                "up_edge_sequence": up_edges,
                "down_edge_sequence": down_edges,
                "selected_start_node": net["start_node"],
                "selected_end_node": net["end_node"],
                "direction_evidence_status": decision["status"],
                "direction_rule_id": decision["rule_id"],
                "direction_reason_code": decision["reason_code"],
                "direction_reason": decision["reason"],
                "endpoint_anchor_json": json_text(decision["anchor_json"]),
                "relation_note": relation_tags.get("note", ""),
                "reverse_edge_match_count": found,
                "adopted_edge_count": total,
                "reverse_edge_completeness_ratio": f"{found / total:.6f}",
                "reverse_edge_sequence": reverse_text,
                "reverse_edge_slots_json": json_text(net["reverse_slots"]),
                "reverse_missing_selected_edges_json": json_text(net["missing_edges"]),
                "reverse_ambiguous_selected_edges_json": json_text(net["ambiguous_edges"]),
                "connection_violation_count": net["connection_violations"],
                "reverse_connection_violation_count": net["reverse_connection_violations"],
                "traffic_assignment_status": status,
                "network_file": relative(net["network_path"]),
                "network_sha256": sha256_file(net["network_path"]),
                "evidence_provenance_json": json_text(
                    {
                        "official_definition": {"url": MLIT_DEFINITION_URL, "sha256": MLIT_DEFINITION_SHA256},
                        "official_road_census": relative(ROAD_CENSUS),
                        "route_relations": relative(ROUTE_RELATIONS),
                        "sumo_network": relative(net["network_path"]),
                        "fixed_mapping": relative(FORMAL_MAPPING),
                        "fixed_edge_evidence": relative(FORMAL_EDGE_EVIDENCE),
                    }
                ),
            }
        )

    by_observation = {row["official_observation_section_id"]: row for row in cluster_rows}
    classification_rows: list[dict[str, Any]] = []
    for target in targets:
        cluster = by_observation[target["official_observation_section_id"]]
        classification_rows.append(
            {
                "target_section_id": target["target_section_id"],
                "official_observation_section_id": target["official_observation_section_id"],
                "cluster": cluster["cluster"],
                "official_direction_evidence": cluster["direction_reason"],
                "adopted_edge_sequence": cluster["adopted_edge_sequence"],
                "adopted_sequence_role": cluster["adopted_sequence_role"],
                "up_edge_sequence": cluster["up_edge_sequence"],
                "down_edge_sequence": cluster["down_edge_sequence"],
                "reverse_edge_match_count": cluster["reverse_edge_match_count"],
                "adopted_edge_count": cluster["adopted_edge_count"],
                "reverse_edge_completeness_ratio": cluster["reverse_edge_completeness_ratio"],
                "reverse_edge_sequence": cluster["reverse_edge_sequence"],
                "direction_evidence_status": cluster["direction_evidence_status"],
                "traffic_assignment_status": cluster["traffic_assignment_status"],
                "connection_violation_count": cluster["connection_violation_count"],
                "decision_reason_code": cluster["direction_reason_code"],
                "decision_reason": cluster["direction_reason"],
                "cluster_evidence_reference": f"{relative(CLUSTER_CSV)}#{cluster['cluster']}",
                "direction_rule_id": cluster["direction_rule_id"],
                "generator_version": SCRIPT_VERSION,
            }
        )

    assumptions = []
    for row in cluster_rows:
        if row["direction_evidence_status"] == "UNRESOLVED":
            assumptions.append(
                {
                    "cluster": row["cluster"],
                    "official_observation_section_id": row["official_observation_section_id"],
                    "target_section_ids_json": row["target_section_ids_json"],
                    "candidate_direction_role": "",
                    "candidate_status": "NOT_FORMULATED",
                    "adoption_status": "NOT_ADOPTED",
                    "eligible_for_traffic_assignment": "false",
                    "reason_code": "RESEARCHER_ESTIMATE_PROHIBITED_INSUFFICIENT_EVIDENCE",
                    "reason": "根拠不足のため研究者推定を作成せず、UNRESOLVEDを維持する。",
                }
            )
    return cluster_rows, classification_rows, assumptions


def rule_rows() -> list[dict[str, str]]:
    return [
        {
            "rule_id": "MLIT_R3_UP_DOWN_SEMANTICS_V1",
            "priority": "1",
            "scope": "ALL_CLUSTERS",
            "condition": "Road Census R3 official definition",
            "outcome": "UP=TERMINUS_TO_ORIGIN;DOWN=ORIGIN_TO_TERMINUS",
            "prohibited_inputs": "GeoJSON coordinate order;bearing;traffic magnitude",
        },
        {
            "rule_id": "OFFICIAL_ADJACENT_BOUNDARY_SUMO_TOPOLOGY_V1",
            "priority": "2",
            "scope": "SAME_ROUTE_CLUSTER",
            "condition": "official reciprocal ward-boundary endpoints and one unambiguous shared SUMO endpoint",
            "outcome": "assign fixed sequence role from the anchored official endpoint",
            "prohibited_inputs": "bearing;visual map direction",
        },
        {
            "rule_id": "OFFICIAL_ENDPOINT_OSM_SUMO_INTERSECTION_V1",
            "priority": "3",
            "scope": "SAME_ROUTE_CLUSTER",
            "condition": "official endpoint road name uniquely matches a non-corridor incident OSM/SUMO edge",
            "outcome": "assign fixed sequence role from START/END endpoint position",
            "prohibited_inputs": "bearing;traffic magnitude",
        },
        {
            "rule_id": "OSM_RELATION_EXPLICIT_ORIGIN_TERMINUS_SEQUENCE_V1",
            "priority": "4",
            "scope": "SAME_ROUTE_CLUSTER",
            "condition": "relation explicitly documents origin-to-terminus order and selected ways are contiguous forward members",
            "outcome": "fixed sequence is DOWN_ORIGIN_TO_TERMINUS",
            "prohibited_inputs": "undocumented member order;blank roles alone",
        },
        {
            "rule_id": "INSUFFICIENT_OFFICIAL_ENDPOINT_ANCHOR_V1",
            "priority": "5",
            "scope": "SAME_ROUTE_CLUSTER",
            "condition": "no unique official endpoint anchor after higher-priority checks",
            "outcome": "direction_evidence_status=UNRESOLVED;no researcher assumption",
            "prohibited_inputs": "route name inference;GeoJSON order;bearing",
        },
        {
            "rule_id": "EXACT_REVERSE_SUMO_TOPOLOGY_V1",
            "priority": "6",
            "scope": "ALL_CLUSTERS",
            "condition": "for every selected edge, one edge has swapped SUMO from/to and the reversed list is connected",
            "outcome": "complete=BIDIRECTIONAL_ASSIGNABLE;zero=MISSING;intermediate=PARTIAL",
            "prohibited_inputs": "reverse-edge generation;edge reselection;parallel-corridor remapping",
        },
    ]


def build_qa(cluster_rows: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_direction = Counter(row["direction_evidence_status"] for row in rows)
    row_traffic = Counter(row["traffic_assignment_status"] for row in rows)
    cluster_direction = Counter(row["direction_evidence_status"] for row in cluster_rows)
    cluster_traffic = Counter(row["traffic_assignment_status"] for row in cluster_rows)
    qa = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "target_selection": {
            "source": relative(INVENTORY),
            "predicate": "mapping_status=RESOLVED AND direction_status=MODEL_ASSUMPTION_REQUIRED",
            "row_count": len(rows),
            "cluster_count": len(cluster_rows),
            "manual_target_ids_used": False,
        },
        "row_summary": {
            "direction_evidence_status": dict(sorted(row_direction.items())),
            "traffic_assignment_status": dict(sorted(row_traffic.items())),
        },
        "cluster_summary": {
            "direction_evidence_status": dict(sorted(cluster_direction.items())),
            "traffic_assignment_status": dict(sorted(cluster_traffic.items())),
        },
        "invariants": {
            "unclassified_count": sum(
                not row["direction_evidence_status"] or not row["traffic_assignment_status"] for row in rows
            ),
            "selected_connection_violation_count": sum(
                int(row["connection_violation_count"]) for row in cluster_rows
            ),
            "mapping_hash_unchanged": sha256_file(FORMAL_MAPPING) == EXPECTED_INPUT_HASHES[FORMAL_MAPPING],
            "base_mapping_hash_unchanged": sha256_file(BASE_MAPPING) == EXPECTED_INPUT_HASHES[BASE_MAPPING],
            "matching_config_hash_unchanged": sha256_file(CONFIG) == EXPECTED_INPUT_HASHES[CONFIG],
            "edge_reselection_performed": False,
            "reverse_edges_generated": False,
        },
    }
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    if len(rows) != 9 or len(cluster_rows) != 5:
        raise ValueError("target completeness invariant failed")
    if qa["invariants"]["unclassified_count"] != 0:
        raise ValueError("unclassified result exists")
    if qa["invariants"]["selected_connection_violation_count"] != 0:
        raise ValueError("selected connection violation exists")
    if not all(
        qa["invariants"][key]
        for key in ("mapping_hash_unchanged", "base_mapping_hash_unchanged", "matching_config_hash_unchanged")
    ):
        raise ValueError("locked mapping/config invariant failed")
    return qa


def render_report(cluster_rows: list[dict[str, Any]], qa: dict[str, Any]) -> str:
    lines = [
        "# 外部観測参照9件の方向証拠・交通量割当可否 最終確認",
        "",
        "## 結論",
        "",
        (
            f"正本inventoryの条件抽出により9件・5 clusterを再現した。方向証拠は"
            f"{qa['row_summary']['direction_evidence_status'].get('RESOLVED', 0)}/9件で確定し、"
            f"{qa['row_summary']['direction_evidence_status'].get('UNRESOLVED', 0)}/9件は未解決を維持した。"
        ),
        "",
        "方向証拠とreverse corridor可用性は別判定である。固定mapping、採択edge列、matching閾値、元データは変更していない。",
        "",
        "## Cluster判定",
        "",
        "| cluster | 観測区間 | 対象数 | 固定列の方向 | 方向証拠 | reverse | 交通量割当 |",
        "|---|---:|---:|---|---|---:|---|",
    ]
    for row in cluster_rows:
        target_count = len(json.loads(row["target_section_ids_json"]))
        reverse = f"{row['reverse_edge_match_count']}/{row['adopted_edge_count']}"
        lines.append(
            f"| `{row['cluster']}` | `{row['official_observation_section_id']}` | {target_count} | "
            f"`{row['adopted_sequence_role']}` | `{row['direction_evidence_status']}` | {reverse} | "
            f"`{row['traffic_assignment_status']}` |"
        )
    lines.extend(
        [
            "",
            "## 判定規律",
            "",
            "Road Census公式定義の `UP=TERMINUS_TO_ORIGIN`、`DOWN=ORIGIN_TO_TERMINUS` を全clusterへ適用した。原票の相互隣接区間・区境、原票に記載された接続路線、明示的なroute relation、SUMO from/to・接続・reverseの順で照合した。GeoJSON座標順、bearing、交通量の大小は方向判定に使用していない。",
            "",
            "完全reverseは、採択列を逆順にした各edgeについて `from/to` を交換したedgeが一意に存在し、その列のSUMO connection violationが0である場合だけ認定した。部分reverseをUP/DOWN列として採用せず、欠損edgeを生成していない。",
            "",
            "## QA",
            "",
            f"- 未分類: {qa['invariants']['unclassified_count']}",
            f"- 採択列connection violation: {qa['invariants']['selected_connection_violation_count']}",
            f"- 既存正式mapping SHA不変: {qa['invariants']['mapping_hash_unchanged']}",
            f"- 既存66区間mapping SHA不変: {qa['invariants']['base_mapping_hash_unchanged']}",
            f"- matching設定 SHA不変: {qa['invariants']['matching_config_hash_unchanged']}",
            f"- validation: {qa.get('validation', {}).get('passed_test_count', 'NOT_RECORDED')} passed / "
            f"{qa.get('validation', {}).get('failed_test_count', 'NOT_RECORDED')} failed",
            "",
            "詳細な原票端点、anchor、reverse欠損edge、規則・provenanceはCSVとmanifestを正本とする。",
            "",
        ]
    )
    return "\n".join(lines)


def command_version(command: str) -> str:
    completed = subprocess.run([command, "--version"], check=True, capture_output=True, text=True)
    return completed.stdout.splitlines()[0]


def write_all() -> None:
    input_hashes = verify_locked_inputs()
    cluster_rows, classification_rows, assumptions = build_outputs()
    rules = rule_rows()
    qa = build_qa(cluster_rows, classification_rows)
    write_csv(CLUSTER_CSV, cluster_rows)
    write_csv(CLASSIFICATION_CSV, classification_rows)
    write_csv(RULES_CSV, rules)
    write_csv(ASSUMPTIONS_CSV, assumptions)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(cluster_rows, qa), encoding="utf-8")
    output_paths = [CLASSIFICATION_CSV, CLUSTER_CSV, RULES_CSV, ASSUMPTIONS_CSV, QA_JSON, REPORT]
    if VALIDATION_JSON.is_file():
        output_paths.append(VALIDATION_JSON)
    manifest = {
        "run_id": RUN_ID,
        "generator": relative(Path(__file__)),
        "generator_sha256": sha256_file(Path(__file__)),
        "generator_version": SCRIPT_VERSION,
        "git_base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "official_direction_definition": {
            "url": MLIT_DEFINITION_URL,
            "retrieved_sha256": MLIT_DEFINITION_SHA256,
            "up": "TERMINUS_TO_ORIGIN",
            "down": "ORIGIN_TO_TERMINUS",
        },
        "target_selection": qa["target_selection"],
        "input_hashes": input_hashes,
        "network_versions": {
            "sumo": command_version("sumo"),
            "netconvert": command_version("netconvert"),
        },
        "output_hashes": {relative(path): sha256_file(path) for path in output_paths},
        "qa": qa,
        "non_mutation_contract": {
            "existing_mapping_changed": False,
            "selected_edges_changed": False,
            "matching_thresholds_changed": False,
            "source_data_changed": False,
            "reverse_edges_generated": False,
        },
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    write_all()


if __name__ == "__main__":
    main()
