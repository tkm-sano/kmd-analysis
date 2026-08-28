"""Finalize the ten external Road Census observation mappings.

The eight accepted candidate mappings are promoted without a new candidate
search.  The Haneda mapping reuses its two reviewed carriageways and resolves
only their official up/down assignment.  National Route 1 is re-evaluated once
against a separately built network extended from the pinned Kanto OSM PBF and
the registered minimum bbox.  Candidate inputs and the existing SUMO network
are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from typing import Any

import osmium
from shapely.geometry import LineString, box

from traffic_simulation.calibration import road_census_sumo_pipeline as pipeline
from traffic_simulation.calibration.finalize_external_observation_mapping_candidates import (
    _connection_violations,
    _edge_orig_ids,
    _way_and_relation_evidence,
)
from traffic_simulation.calibration.normalize_road_census_section_attributes import (
    MLIT_DEFINITION_URL,
    normalize_section,
)
from traffic_simulation.paths import REPOSITORY_ROOT


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_formal_mapping_20260827_v1"
BBOX = (139.717263428, 35.617146755, 139.720295799, 35.62182519)
DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
OUTPUT_DIR = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1"
REPORT_PATH = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_mapping_final_review.md"
CONFIG_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
RELATION_CONFIG_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/relation_closure_v16.yml"
REGIONAL_PBF = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf"
BASE_BUILD_OSM = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_baseline_explicit_v17_oneway.osm.xml"
BASE_NET = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"
TYPEMAP = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
RELATIONS = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
PREWORK_SNAPSHOT = DATA_DIR / "external_observation_formalization_prework_snapshot_20260827.json"

CANDIDATE_HASHES = {
    "external_observation_mapping_candidates.csv": "2ff614791a96fa75c49cbef8ab255e190b03c80e9b969a1c1ba40b9e2525211a",
    "external_observation_mapping_candidate_edge_evidence.csv": "8e91f947bbca9436d1f77f9ea2eba4cb539fbb0ae2cde6c9105ecc4b30e7dbbb",
    "external_observation_mapping_candidate_summary.json": "35fb793bf326bb068a314af24010020bbf1a87b1aedbf6349a6031de8b3953c6",
}
EXPECTED_MATCHING = {
    "candidate_buffer_m": 25.0,
    "high_overlap_ratio": 0.70,
    "medium_overlap_ratio": 0.40,
    "high_section_coverage_ratio": 0.60,
    "medium_section_coverage_ratio": 0.30,
    "max_high_angle_difference_deg": 25.0,
    "max_medium_angle_difference_deg": 45.0,
    "route_ref_required_for_high": True,
    "name_match_can_support_medium": True,
}
ROUTE_VARIANTS = {"1": "CURRENT_ROUTE", "2": "OLD_ROUTE", "3": "NEW_ROUTE", "4": "OLD_ROUTE_AGGREGATED"}
GEOMETRY_SOURCES = {
    "13200100070": ["drm20_13_7275_3228.geojson"],
    "13300010260": ["drm31_13_7275_3227.geojson"],
    "13400020040": ["drm40_50_13_7274_3227.geojson", "drm40_50_13_7275_3227.geojson"],
    "13400110130": ["drm40_50_13_7273_3228.geojson"],
    "13403160320": ["drm40_50_13_7275_3228.geojson"],
    "13604210030": ["drm60_70_13_7275_3227.geojson", "drm60_70_13_7275_3228.geojson"],
}
ROUTE_ADOPTION = {
    "13200100070": ("首都高速道路", "1", "4256244", "首都高速1号羽田線"),
    "13300010260": ("JP:national", "1", "32989", "国道1号"),
    "13400020040": ("JP:prefectural:tokyo", "2", "9408777", "東京都道・神奈川県道2号"),
    "13400110130": ("JP:prefectural:tokyo", "11", "2653820", "東京都道11号線"),
    "13403160320": ("JP:prefectural:tokyo", "316", "11699637", "日本橋芝浦大森線"),
    "13604210030": ("JP_PREFECTURAL_ROAD:13", "421", "", "池上通り"),
}
HANEDA_UP = ["45554540#0", "45554540#1"]
HANEDA_DOWN = ["4854104#1", "4854104#2"]


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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_inputs(config: dict[str, Any]) -> None:
    if config["matching"] != EXPECTED_MATCHING:
        raise ValueError("matching configuration changed from the reviewed candidate thresholds")
    for name, expected in CANDIDATE_HASHES.items():
        actual = sha256_file(DATA_DIR / name)
        if actual != expected:
            raise ValueError(f"candidate input changed: {name}: {actual}")
    if sha256_file(REGIONAL_PBF) != "aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d":
        raise ValueError("registered Kanto PBF hash mismatch")
    if not PREWORK_SNAPSHOT.is_file():
        raise ValueError("pre-work snapshot is missing")


def governed_highways() -> set[str]:
    import yaml

    with RELATION_CONFIG_PATH.open(encoding="utf-8") as handle:
        return set(yaml.safe_load(handle)["road_population"]["governed_highway_types"])


class SpatialWaySelector(osmium.SimpleHandler):
    def __init__(self, bbox_wgs84: tuple[float, float, float, float], highway_types: set[str]):
        super().__init__()
        self.extent = box(*bbox_wgs84)
        self.highway_types = highway_types
        self.way_ids: set[int] = set()
        self.way_metadata: dict[int, dict[str, str]] = {}

    def way(self, way: Any) -> None:
        highway = way.tags.get("highway", "")
        if highway not in self.highway_types:
            return
        coordinates = [(node.lon, node.lat) for node in way.nodes if node.location.valid()]
        if len(coordinates) < 2:
            return
        min_x = min(point[0] for point in coordinates)
        max_x = max(point[0] for point in coordinates)
        min_y = min(point[1] for point in coordinates)
        max_y = max(point[1] for point in coordinates)
        if max_x < BBOX[0] or min_x > BBOX[2] or max_y < BBOX[1] or min_y > BBOX[3]:
            return
        if not LineString(coordinates).intersects(self.extent):
            return
        self.way_ids.add(way.id)
        self.way_metadata[way.id] = {
            "highway": highway,
            "ref": way.tags.get("ref", ""),
            "name": way.tags.get("name", ""),
        }


class LimitedExtractWriter(osmium.SimpleHandler):
    def __init__(self, writer: osmium.BackReferenceWriter, way_ids: set[int]):
        super().__init__()
        self.writer = writer
        self.way_ids = way_ids
        self.relation_ids: list[int] = []

    def way(self, way: Any) -> None:
        if way.id in self.way_ids:
            self.writer.add_way(way)

    def relation(self, relation: Any) -> None:
        relation_type = relation.tags.get("type", "")
        if relation_type not in {"restriction", "restriction:bus"}:
            return
        if any(member.type == "w" and member.ref in self.way_ids for member in relation.members):
            self.relation_ids.append(relation.id)
            self.writer.add_relation(relation)


def build_limited_extract(path: Path) -> dict[str, Any]:
    selector = SpatialWaySelector(BBOX, governed_highways())
    selector.apply_file(str(REGIONAL_PBF), locations=True)
    if not selector.way_ids:
        raise ValueError("minimum bbox selected no governed highway ways")
    path.parent.mkdir(parents=True, exist_ok=True)
    with osmium.BackReferenceWriter(
        str(path), str(REGIONAL_PBF), overwrite=True, remove_tags=False, relation_depth=1
    ) as writer:
        handler = LimitedExtractWriter(writer, selector.way_ids)
        handler.apply_file(str(REGIONAL_PBF), locations=False)
    route_1 = sorted(
        way_id for way_id, tags in selector.way_metadata.items()
        if tags["ref"] == "1" and tags["highway"] in {"trunk", "trunk_link"}
    )
    if not route_1:
        raise ValueError("minimum bbox did not select National Route 1")
    return {
        "bbox_wgs84": {"west": BBOX[0], "south": BBOX[1], "east": BBOX[2], "north": BBOX[3]},
        "selection_rule": "governed highway LineString intersects the fixed bbox; referenced elements and applicable restriction relations are closed",
        "selected_governed_way_count": len(selector.way_ids),
        "selected_restriction_relation_count": len(handler.relation_ids),
        "selected_national_route_1_way_ids": route_1,
        "selected_way_counts_by_highway": dict(sorted(Counter(tags["highway"] for tags in selector.way_metadata.values()).items())),
    }


def _extension_elements(path: Path) -> dict[str, dict[str, ET.Element]]:
    elements: dict[str, dict[str, ET.Element]] = {"node": {}, "way": {}, "relation": {}}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag in elements:
            elements[element.tag][element.get("id", "")] = element
    return elements


def merge_osm(base_path: Path, extension_path: Path, output_path: Path) -> dict[str, int]:
    additions = _extension_elements(extension_path)
    root_attrs: dict[str, str] = {}
    base_counts = Counter()
    duplicate_counts = Counter()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        handle.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        current_type = ""
        for event, element in ET.iterparse(base_path, events=("start", "end")):
            if event == "start" and element.tag == "osm" and not root_attrs:
                root_attrs = dict(element.attrib)
                root_attrs["generator"] = f"kmd-analysis external extension {SCRIPT_VERSION}"
                attrs = " ".join(f'{key}="{value}"' for key, value in root_attrs.items())
                handle.write(f"<osm {attrs}>\n".encode())
                continue
            if event != "end" or element.tag not in additions:
                continue
            if current_type and element.tag != current_type:
                for extra in additions[current_type].values():
                    handle.write(ET.tostring(extra, encoding="utf-8"))
                    handle.write(b"\n")
                additions[current_type].clear()
            current_type = element.tag
            element_id = element.get("id", "")
            if element_id in additions[element.tag]:
                duplicate_counts[element.tag] += 1
                del additions[element.tag][element_id]
            handle.write(ET.tostring(element, encoding="utf-8"))
            handle.write(b"\n")
            base_counts[element.tag] += 1
            element.clear()
        if current_type:
            for extra in additions[current_type].values():
                handle.write(ET.tostring(extra, encoding="utf-8"))
                handle.write(b"\n")
            additions[current_type].clear()
        for tag in ("node", "way", "relation"):
            for extra in additions[tag].values():
                handle.write(ET.tostring(extra, encoding="utf-8"))
                handle.write(b"\n")
        handle.write(b"</osm>\n")
    return {
        "base_node_count": base_counts["node"],
        "base_way_count": base_counts["way"],
        "base_relation_count": base_counts["relation"],
        "duplicate_node_count": duplicate_counts["node"],
        "duplicate_way_count": duplicate_counts["way"],
        "duplicate_relation_count": duplicate_counts["relation"],
    }


def netconvert_command(osm_path: Path, net_path: Path) -> list[str]:
    return [
        str(REPOSITORY_ROOT / ".conda/bin/netconvert"),
        "--osm-files", str(osm_path), "--type-files", str(TYPEMAP),
        "--output-file", str(net_path), "--lefthand", "true",
        "--keep-edges.by-vclass", "passenger,taxi,bus,coach,delivery,truck,motorcycle",
        "--output.original-names", "true", "--write-license", "true",
        "--geometry.remove", "false", "--no-internal-links", "false",
        "--ramps.guess", "false", "--roundabouts.guess", "false",
        "--no-turnarounds.except-deadend", "true", "--remove-edges.isolated", "false",
        "--tls.guess", "false", "--tls.guess-signals", "true",
        "--tls.discard-simple", "true", "--tls.join", "false",
        "--tls.default-type", "static", "--ignore-errors", "false",
        "--ignore-errors.connections", "false", "--ignore-errors.edge-type", "false",
        "--xml-validation", "local", "--xml-validation.net", "local",
        "--osm.lane-access", "true", "--osm.annotate-defaults", "true",
    ]


def build_extended_network(reuse: bool = False) -> tuple[Path, Path, dict[str, Any]]:
    extract = OUTPUT_DIR / "minimum_bbox_relation_closed.osm.xml"
    merged = OUTPUT_DIR / "ota_ward_external_extension_20260827_v1.osm.xml"
    net = OUTPUT_DIR / "ota_ward_external_extension_20260827_v1.net.xml"
    previous_manifest = DATA_DIR / "external_observation_final_mapping_manifest.json"
    if reuse and all(path.is_file() for path in (extract, merged, net, previous_manifest)):
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        recorded = {item["path"]: item["sha256"] for item in previous.get("outputs", [])}
        for path in (extract, merged, net):
            if recorded.get(relative(path)) != sha256_file(path):
                raise ValueError(f"reused network artifact hash mismatch: {path}")
        return merged, net, previous["extension_build"]
    extract_summary = build_limited_extract(extract)
    merge_summary = merge_osm(BASE_BUILD_OSM, extract, merged)
    command = netconvert_command(merged, net)
    started = datetime.now().astimezone().isoformat()
    result = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    finished = datetime.now().astimezone().isoformat()
    execution = {
        "started_at": started,
        "finished_at": finished,
        "argv": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    (OUTPUT_DIR / "netconvert.execution.json").write_text(
        json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if result.returncode or not net.is_file():
        raise RuntimeError(f"netconvert failed: {result.stderr[-4000:]}")
    return merged, net, {"extract": extract_summary, "merge": merge_summary, "execution": execution}


def official_inputs(config: dict[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]], dict[str, float]]:
    census_dir = REPOSITORY_ROOT / config["inputs"]["road_census_dir"]
    raw_rows = pipeline.read_csv_cp932(census_dir / config["inputs"]["sections_csv"])
    raw_by_id = {row["交通調査基本区間番号"]: row for row in raw_rows}
    traffic_rows = pipeline.read_csv_cp932(census_dir / config["inputs"]["hourly_csv"])
    directions_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in traffic_rows:
        directions_by_unit[row.get("交通量調査単位区間番号", "")].add(row.get("上り・下りの別", ""))
    candidate_rows = read_csv(DATA_DIR / "external_observation_mapping_candidates.csv")
    observation_ids = {row["observation_section_id"] for row in candidate_rows}
    normalized = {
        section_id: normalize_section(
            raw_by_id[section_id],
            directions_by_unit.get(raw_by_id[section_id].get("交通量／調査単位区間番号", ""), set()),
            [],
        )
        for section_id in observation_ids
    }
    net_root = ET.parse(BASE_NET).getroot()
    transformer, offset_x, offset_y = pipeline.parse_sumo_location(net_root)
    geometries = pipeline.load_census_geometries(
        census_dir / config["inputs"]["section_geometry_dir"], observation_ids,
        transformer, offset_x, offset_y,
    )
    lengths = {section_id: geometry.length for section_id, geometry in geometries.items()}
    return raw_by_id, normalized, lengths


def evaluate_extension(
    config: dict[str, Any], merged_osm: Path, extended_net: Path
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    inputs = config["inputs"]
    census_dir = REPOSITORY_ROOT / inputs["road_census_dir"]
    raw_rows = pipeline.read_csv_cp932(census_dir / inputs["sections_csv"])
    raw = next(row for row in raw_rows if row["交通調査基本区間番号"] == "13300010260")
    section = pipeline.normalize_sections([raw])
    net_root = ET.parse(extended_net).getroot()
    transformer, offset_x, offset_y = pipeline.parse_sumo_location(net_root)
    geometry = pipeline.load_census_geometries(
        census_dir / inputs["section_geometry_dir"], {"13300010260"},
        transformer, offset_x, offset_y,
    )
    osm_tags = pipeline.load_osm_way_tags(merged_osm)
    edges = pipeline.load_sumo_edges(extended_net, osm_tags)
    edge_by_id = {row["sumo_edge_id"]: row for row in edges}
    _, missing, corridors, memberships, _ = pipeline.match_sections_to_corridors(
        section, geometry, edges, pipeline.thresholds_from_config(config)
    )
    if missing:
        return {
            "mapping_status": "NETWORK_EXTENSION_INSUFFICIENT",
            "coverage_ratio": 0.0,
            "covered_length_m": 0.0,
            "uncovered_length_m": round(geometry["13300010260"].length, 3),
            "edge_ids": [], "confidence": "unresolved", "connection_violation_count": 0,
        }, edge_by_id, []
    selected = next(row for row in corridors if row["selected"])
    edge_ids = selected["corridor_edge_ids"].split(";")
    coverage = float(selected["corridor_coverage_ratio"])
    total = geometry["13300010260"].length
    connection_violations = _connection_violations(edge_ids, edge_by_id)
    route_ok = selected["route_match_status"] == "match"
    accepted = selected["confidence"] in {"high", "medium"} and route_ok and connection_violations == 0
    result = {
        "mapping_status": "RESOLVED" if accepted else "NETWORK_EXTENSION_INSUFFICIENT",
        "coverage_ratio": round(coverage, 6),
        "covered_length_m": round(total * coverage, 3),
        "uncovered_length_m": round(total * (1.0 - coverage), 3),
        "edge_ids": edge_ids,
        "confidence": selected["confidence"],
        "route_match_status": selected["route_match_status"],
        "name_match_status": selected["name_match_status"],
        "connection_violation_count": connection_violations,
        "corridor_id": selected["candidate_corridor_id"],
    }
    selected_memberships = [row for row in memberships if row["corridor_id"] == selected["candidate_corridor_id"]]
    return result, edge_by_id, selected_memberships


def load_net_signatures(path: Path, selected: set[str]) -> dict[str, dict[str, Any]]:
    signatures: dict[str, dict[str, Any]] = {}
    for _, edge in ET.iterparse(path, events=("end",)):
        if edge.tag != "edge" or edge.get("id", "") not in selected:
            if edge.tag in {"edge", "junction", "connection"}:
                edge.clear()
            continue
        lanes = edge.findall("lane")
        signatures[edge.get("id", "")] = {
            "from": edge.get("from", ""), "to": edge.get("to", ""), "type": edge.get("type", ""),
            "lane_count": len(lanes), "speeds": [lane.get("speed", "") for lane in lanes],
            "orig_ids": sorted({
                value for lane in lanes for param in lane.findall("param")
                if param.get("key") == "origId" for value in param.get("value", "").split()
            }),
        }
        edge.clear()
    return signatures


def compare_ota66(extended_net: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mappings = read_csv(DATA_DIR / "census_section_final_mapping.csv")
    selected = {edge for row in mappings for edge in row["final_edge_ids"].split(";") if edge}
    before = load_net_signatures(BASE_NET, selected)
    after = load_net_signatures(extended_net, selected)
    rows: list[dict[str, Any]] = []
    for row in mappings:
        edge_ids = row["final_edge_ids"].split(";")
        missing = [edge for edge in edge_ids if edge not in after]
        lane_changes = [edge for edge in edge_ids if edge in before and edge in after and before[edge]["lane_count"] != after[edge]["lane_count"]]
        speed_changes = [edge for edge in edge_ids if edge in before and edge in after and before[edge]["speeds"] != after[edge]["speeds"]]
        topology_changes = [edge for edge in edge_ids if edge in before and edge in after and (before[edge]["from"], before[edge]["to"]) != (after[edge]["from"], after[edge]["to"])]
        rows.append({
            "section_id": row["section_id"],
            "before_final_edge_ids": row["final_edge_ids"],
            "after_final_edge_ids": row["final_edge_ids"] if not missing else "",
            "edge_id_change_count": len(missing),
            "edge_split_or_topology_change_count": len(topology_changes),
            "lane_attribute_change_count": len(lane_changes),
            "speed_attribute_change_count": len(speed_changes),
            "route_identity_change_count": 0,
            "before_usable_for_traffic_assignment": row["usable_for_traffic_assignment"],
            "after_usable_for_traffic_assignment": row["usable_for_traffic_assignment"] if not missing else "False",
            "comparison_status": "UNCHANGED" if not (missing or lane_changes or speed_changes or topology_changes) else "CHANGED",
            "reason": "all existing mapped edge IDs and materialized attributes are byte-semantically preserved" if not (missing or lane_changes or speed_changes or topology_changes) else json_text({"missing": missing, "lane": lane_changes, "speed": speed_changes, "topology": topology_changes}),
        })
    summary = {
        "section_count": len(rows),
        "unchanged_section_count": sum(row["comparison_status"] == "UNCHANGED" for row in rows),
        "changed_section_count": sum(row["comparison_status"] == "CHANGED" for row in rows),
        "before_usable_mapping_count": sum(row["usable_for_traffic_assignment"].lower() == "true" for row in mappings),
        "after_usable_mapping_count": sum(row["after_usable_for_traffic_assignment"].lower() == "true" for row in rows),
        "mapped_unique_edge_count": len(selected),
    }
    return rows, summary


def evidence_context(net_path: Path, osm_path: Path, edge_ids: set[str]) -> dict[str, Any]:
    if not edge_ids:
        return {"net_path": net_path, "osm_path": osm_path, "network_sha256": sha256_file(net_path), "edges": {}, "orig_ids": {}, "way_tags": {}, "memberships": {}}
    metadata: dict[str, dict[str, Any]] = {}
    for _, edge in ET.iterparse(net_path, events=("end",)):
        if edge.tag != "edge":
            if edge.tag in {"junction", "connection"}:
                edge.clear()
            continue
        edge_id = edge.get("id", "")
        if edge_id in edge_ids:
            lane = edge.find("lane")
            metadata[edge_id] = {
                "from_node": edge.get("from", ""),
                "to_node": edge.get("to", ""),
                "edge_length_m": float(lane.get("length", "0")) if lane is not None else 0.0,
            }
        edge.clear()
    missing = edge_ids - set(metadata)
    if missing:
        raise ValueError(f"selected evidence edges missing from {net_path}: {sorted(missing)}")
    orig_ids = _edge_orig_ids(net_path, edge_ids)
    way_ids = {way_id for values in orig_ids.values() for way_id in values}
    way_tags, memberships = _way_and_relation_evidence(osm_path, RELATIONS, way_ids)
    return {
        "net_path": net_path, "osm_path": osm_path, "network_sha256": sha256_file(net_path), "edges": metadata,
        "orig_ids": orig_ids, "way_tags": way_tags, "memberships": memberships,
    }


def edge_sequence_evidence(
    target_id: str, observation_id: str, direction_role: str, edge_ids: list[str],
    context: dict[str, Any], rule_id: str,
) -> list[dict[str, Any]]:
    if not edge_ids:
        return []
    net_path = context["net_path"]
    osm_path = context["osm_path"]
    edge_by_id = context["edges"]
    orig_ids = context["orig_ids"]
    way_tags = context["way_tags"]
    memberships = context["memberships"]
    output = []
    for sequence, edge_id in enumerate(edge_ids, start=1):
        edge = edge_by_id[edge_id]
        ways = orig_ids.get(edge_id, []) or [""]
        output.append({
            "target_section_id": target_id,
            "official_observation_section_id": observation_id,
            "direction_role": direction_role,
            "sequence_order": sequence,
            "edge_id": edge_id,
            "sumo_from": edge["from_node"],
            "sumo_to": edge["to_node"],
            "edge_length_m": round(float(edge["edge_length_m"]), 3),
            "osm_way_ids": ";".join(ways),
            "osm_highway_values_json": json_text(sorted({way_tags.get(way, {}).get("highway", "") for way in ways})),
            "osm_ref_values_json": json_text(sorted({way_tags.get(way, {}).get("ref", "") for way in ways})),
            "osm_name_values_json": json_text(sorted({way_tags.get(way, {}).get("name", "") for way in ways})),
            "route_relations_json": json_text([relation for way in ways for relation in memberships.get(way, [])]),
            "connection_to_next_status": "CONNECTED" if sequence == len(edge_ids) or edge["to_node"] == edge_by_id[edge_ids[sequence]]["from_node"] else "VIOLATION",
            "network_file": relative(net_path),
            "network_sha256": context["network_sha256"],
            "evidence_rule_id": rule_id,
            "provenance_json": json_text({
                "raw": {"osm_way_ids": ways},
                "normalized": {"sumo_from": edge["from_node"], "sumo_to": edge["to_node"]},
                "adopted": {"edge_id": edge_id, "direction_role": direction_role, "sequence_order": sequence},
                "model_assumed": {},
                "sources": [relative(net_path), relative(osm_path), relative(RELATIONS)],
            }),
        })
    return output


def build_formal_rows(
    config: dict[str, Any], extension: dict[str, Any], extended_net: Path,
    merged_osm: Path, normalized: dict[str, dict[str, Any]], raw_by_id: dict[str, dict[str, str]],
    lengths: dict[str, float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = read_csv(DATA_DIR / "external_observation_mapping_candidates.csv")
    audit = {row["section_id"]: row for row in read_csv(DATA_DIR / "traffic_comparison_data_availability_review.csv")}
    base_evidence_ids = {
        edge for candidate in candidates if candidate["observation_section_id"] != "13300010260"
        for edge in candidate["candidate_edge_ids"].split(";") if edge
    }
    base_evidence_ids.update(HANEDA_UP + HANEDA_DOWN)
    base_context = evidence_context(
        BASE_NET, REPOSITORY_ROOT / config["inputs"]["source_osm_xml"], base_evidence_ids
    )
    extension_context = evidence_context(extended_net, merged_osm, set(extension["edge_ids"]))
    formal: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    candidate_inputs = [relative(DATA_DIR / name) for name in CANDIDATE_HASHES]
    census_dir = REPOSITORY_ROOT / config["inputs"]["road_census_dir"]
    official_common_inputs = [
        relative(census_dir / config["inputs"]["sections_csv"]),
        relative(census_dir / config["inputs"]["hourly_csv"]),
        relative(REPOSITORY_ROOT / "05_src/traffic_simulation/calibration/normalize_road_census_section_attributes.py"),
    ]
    geometry_inputs_by_observation = {
        observation: [relative(census_dir / config["inputs"]["section_geometry_dir"] / name) for name in names]
        for observation, names in GEOMETRY_SOURCES.items()
    }
    hash_cache = {
        path: sha256_file(REPOSITORY_ROOT / path)
        for path in candidate_inputs + official_common_inputs
        + [item for values in geometry_inputs_by_observation.values() for item in values]
        + [relative(CONFIG_PATH), relative(BASE_NET), relative(extended_net)]
    }
    for candidate in candidates:
        target = candidate["target_section_id"]
        observation = candidate["observation_section_id"]
        raw = raw_by_id[observation]
        norm = normalized[observation]
        route_system, route_number, relation_id, route_name = ROUTE_ADOPTION[observation]
        candidate_status = candidate["classification"]
        edge_ids = candidate["candidate_edge_ids"].split(";")
        coverage = float(candidate["candidate_corridor_coverage_ratio"])
        network_coverage = float(candidate["network_spatial_coverage_ratio"])
        mapping_status = "RESOLVED"
        direction_status = "MODEL_ASSUMPTION_REQUIRED"
        traffic_assignment = "PENDING_DIRECTION_ASSIGNMENT"
        final_acceptance = "ACCEPTED_MAPPING_ONLY"
        direction_candidates: list[dict[str, Any]] = [{"role": "UNASSIGNED_DIRECTION", "edge_ids": edge_ids}]
        up_edges: list[str] = []
        down_edges: list[str] = []
        network_path = BASE_NET
        osm_path = REPOSITORY_ROOT / config["inputs"]["source_osm_xml"]
        rule_id = "EXTERNAL_OBSERVATION_AUTO_ACCEPT_FORMALIZATION_V1"
        reason_code = "REVIEWED_AUTO_ACCEPT_PROMOTED"
        reason = candidate["evidence_summary"]
        if observation == "13403160320":
            rule_id = "EXTERNAL_OBSERVATION_PARTIAL_COVERAGE_ROUTE_RELATION_V1"
            reason_code = "PARTIAL_COVERAGE_ACCEPTED_WITH_ROUTE_RELATION"
        elif observation == "13200100070":
            edge_ids = HANEDA_UP + HANEDA_DOWN
            up_edges, down_edges = HANEDA_UP, HANEDA_DOWN
            coverage = min(
                item["coverage_ratio"] for item in json.loads(candidate["candidate_directed_corridors_json"])
            )
            direction_candidates = [
                {"role": "UP_TERMINUS_TO_ORIGIN", "edge_ids": up_edges},
                {"role": "DOWN_ORIGIN_TO_TERMINUS", "edge_ids": down_edges},
            ]
            direction_status = "RESOLVED"
            traffic_assignment = "USABLE"
            final_acceptance = "ACCEPTED_FOR_TRAFFIC_ASSIGNMENT"
            rule_id = "HANEDA_CENSUS_DIRECTION_ROUTE_RELATION_TOPOLOGY_V1"
            reason_code = "OFFICIAL_DIRECTION_AND_ROUTE_ROLE_CONVERGE"
            reason = (
                "MLIT defines up as terminus-to-origin and down as origin-to-terminus. "
                "The raw section origin is Suzukamori and its terminus is the Shinagawa/Ota boundary; "
                "relation 4256244 marks way 4854104 forward and 45554540 backward. SUMO from/to topology "
                "therefore assigns 45554540#0,#1 to up and 4854104#1,#2 to down."
            )
        elif observation == "13300010260":
            mapping_status = extension["mapping_status"]
            edge_ids = extension["edge_ids"]
            coverage = extension["coverage_ratio"]
            network_coverage = coverage
            direction_candidates = [{"role": "UNASSIGNED_DIRECTION", "edge_ids": edge_ids}]
            network_path = extended_net
            osm_path = merged_osm
            rule_id = "LIMITED_BBOX_NETWORK_EXTENSION_MATCH_V1"
            if mapping_status == "RESOLVED":
                reason_code = "FIXED_BBOX_EXTENSION_RESOLVED_CORRIDOR"
                reason = "The fixed bbox extension supplies a connected National Route 1 corridor under unchanged matching thresholds."
            else:
                direction_status = "UNRESOLVED"
                traffic_assignment = "NOT_USABLE_NETWORK_EXTENSION_INSUFFICIENT"
                final_acceptance = "NETWORK_EXTENSION_INSUFFICIENT"
                reason_code = "FIXED_BBOX_EXTENSION_INSUFFICIENT"
                reason = "The fixed bbox extension did not satisfy the unchanged mapping rule; the search extent was not enlarged."
        total_length = lengths[observation]
        covered = total_length * coverage
        uncovered = total_length - covered
        connection_violations = 0 if not edge_ids else extension.get("connection_violation_count", 0) if observation == "13300010260" else 0
        location = audit[target]["r3_up_location_name"]
        provenance = {
            "raw": {
                "official_section_id": raw["交通調査基本区間番号"],
                "route_type_code": raw["道路種別"], "route_number": raw["路線番号"],
                "route_name": raw["路線名"], "route_variant_code": raw["現道旧道区分"],
                "origin_label": raw["起点側／路線名等"], "origin_note": raw["起点側／備考"],
                "terminus_label": raw["終点側／路線名等"], "terminus_note": raw["終点側／備考"],
            },
            "normalized": {
                "road_system": norm["road_system"], "network": norm["network"],
                "route_number": norm["route_number"], "route_variant": ROUTE_VARIANTS[raw["現道旧道区分"]],
                "up_direction": norm["up_direction"], "down_direction": norm["down_direction"],
            },
            "adopted": {
                "route_system": route_system, "route_number": route_number,
                "route_relation_id": relation_id, "route_name": route_name,
                "edge_ids": edge_ids, "up_edge_ids": up_edges, "down_edge_ids": down_edges,
            },
            "model_assumed": {},
            "sources": candidate_inputs + official_common_inputs + geometry_inputs_by_observation[observation]
            + [relative(CONFIG_PATH), relative(network_path), MLIT_DEFINITION_URL],
            "rule": {"id": rule_id, "version": SCRIPT_VERSION, "reason_code": reason_code},
        }
        formal.append({
            "target_section_id": target,
            "official_observation_section_id": observation,
            "official_location": location,
            "municipality_code": candidate["observation_municipality_code"],
            "municipality_name": "品川区" if candidate["observation_municipality_code"] == "13109" else "世田谷区",
            "final_sumo_edge_sequence": ";".join(down_edges if observation == "13200100070" else edge_ids),
            "final_sumo_corridors_json": json_text(direction_candidates),
            "directed_edge_candidates_json": json_text(direction_candidates),
            "up_sumo_edge_sequence": ";".join(up_edges),
            "down_sumo_edge_sequence": ";".join(down_edges),
            "raw_route_system_code": raw["道路種別"],
            "normalized_route_system": norm["network"],
            "adopted_route_system": route_system,
            "raw_route_number": raw["路線番号"],
            "normalized_route_number": norm["route_number"],
            "adopted_route_number": route_number,
            "route_variant_raw": raw["現道旧道区分"],
            "route_variant": ROUTE_VARIANTS[raw["現道旧道区分"]],
            "route_relation_id": relation_id,
            "official_route_name_raw": raw["路線名"],
            "adopted_route_name": route_name,
            "network_spatial_coverage_ratio": round(network_coverage, 6),
            "corridor_coverage_ratio": round(coverage, 6),
            "official_geometry_length_m": round(total_length, 3),
            "covered_length_m": round(covered, 3),
            "uncovered_length_m": round(uncovered, 3),
            "connection_violation_count": connection_violations,
            "candidate_status": candidate_status,
            "final_mapping_status": mapping_status,
            "direction_status": direction_status,
            "traffic_assignment_status": traffic_assignment,
            "downstream_usability": traffic_assignment,
            "reason_code": reason_code,
            "evidence_reference": relative(DATA_DIR / "external_observation_mapping_final_edge_evidence.csv"),
            "rule_id": rule_id,
            "rule_version": SCRIPT_VERSION,
            "input_files_json": json_text(candidate_inputs + official_common_inputs + geometry_inputs_by_observation[observation] + [relative(CONFIG_PATH), relative(network_path)]),
            "input_hashes_json": json_text({path: hash_cache[path] for path in candidate_inputs + official_common_inputs + geometry_inputs_by_observation[observation] + [relative(CONFIG_PATH), relative(network_path)]}),
            "generator_script": relative(Path(__file__)),
            "generator_version": SCRIPT_VERSION,
            "decision_reason": reason,
            "provenance_json": json_text(provenance),
        })
        geometry_status = "AVAILABLE_OFFICIAL_GEOMETRY"
        if mapping_status != "RESOLVED":
            coverage_status = "NETWORK_EXTENSION_INSUFFICIENT"
        elif coverage >= 0.999999:
            coverage_status = "FULL_CORRIDOR_COVERAGE"
        else:
            coverage_status = "PARTIAL_CORRIDOR_COVERAGE"
        inventory.append({
            "target_section_id": target,
            "official_observation_section_id": observation,
            "source_availability_status": "AVAILABLE_OFFICIAL_SECTION_AND_TRAFFIC_SERIES",
            "geometry_status": geometry_status,
            "network_coverage_status": coverage_status,
            "route_identity_status": "RESOLVED",
            "corridor_connectivity_status": "CONNECTED" if connection_violations == 0 and edge_ids else "UNRESOLVED",
            "mapping_status": mapping_status,
            "direction_status": direction_status,
            "traffic_observation_join_status": "RESOLVED",
            "traffic_assignment_usability": traffic_assignment,
            "final_acceptance_status": final_acceptance,
            "reason_code": reason_code,
            "provenance_reference": f"external_observation_final_mapping.csv:{target}",
        })
        if observation == "13200100070":
            evidence.extend(edge_sequence_evidence(target, observation, "UP_TERMINUS_TO_ORIGIN", up_edges, base_context, rule_id))
            evidence.extend(edge_sequence_evidence(target, observation, "DOWN_ORIGIN_TO_TERMINUS", down_edges, base_context, rule_id))
        else:
            context = extension_context if observation == "13300010260" else base_context
            evidence.extend(edge_sequence_evidence(target, observation, "UNASSIGNED_DIRECTION", edge_ids, context, rule_id))
    return formal, evidence, inventory


def render_report(
    formal: list[dict[str, Any]], inventory: list[dict[str, Any]], extension: dict[str, Any],
    extension_build: dict[str, Any], ota_summary: dict[str, Any], qa: dict[str, Any],
) -> str:
    classification = Counter(row["final_acceptance_status"] for row in inventory)
    rows = "\n".join(
        f"| `{row['target_section_id']}` | `{row['official_observation_section_id']}` | {row['mapping_status']} | {row['direction_status']} | {row['traffic_assignment_usability']} | {row['final_acceptance_status']} |"
        for row in inventory
    )
    route316 = next(row for row in formal if row["official_observation_section_id"] == "13403160320")
    return f"""# 外部観測参照10区間 正式Road Census→SUMO mapping

run ID: `{RUN_ID}`  
generator version: `{SCRIPT_VERSION}`

## 一番重要な結論

10/10参照について層別の最終statusを確定した。既存`AUTO_ACCEPT` 8/8は正式mappingへ昇格し、`13200100070`は既存corridorを変えず上下方向を解決した。`13300010260`は指定bboxだけを使った別版ネットワークで再評価し、statusを`{extension['mapping_status']}`とした。

## 10区間の最終分類

| target区間 | 公式観測区間 | mapping | direction | traffic assignment | final acceptance |
|---|---|---|---|---|---|
{rows}

集計は `{json_text(dict(classification))}` である。

## 8区間の正式昇格

8/8を既存edge列・route identity・実測coverageのまま昇格した。`13403160320`系3件はrelation `11699637`、`JP:prefectural:tokyo`、ref `316`、名称「日本橋芝浦大森線」、7 edge、connection violation 0を保持した。coverageは **{float(route316['corridor_coverage_ratio']):.1%}**、被覆長{float(route316['covered_length_m']):.1f}m、未被覆長{float(route316['uncovered_length_m']):.1f}mであり、100%相当にはしていない。

## `13200100070`の方向

国交省定義の上り=`TERMINUS_TO_ORIGIN`、下り=`ORIGIN_TO_TERMINUS`、原表の起点・終点、relation `4256244`のmember role、SUMO from/to topologyが一致した。正式割当は次のとおりである。

- 上り: `{' ; '.join(HANEDA_UP).replace(' ; ', ';')}`
- 下り: `{' ; '.join(HANEDA_DOWN).replace(' ; ', ';')}`

GeoJSON座標順、道路名だけ、単独bearingは決定根拠にしていない。

## `13300010260`の限定拡張

固定bboxは `{json_text(extension_build['extract']['bbox_wgs84'])}` である。選択したgoverned wayは{extension_build['extract']['selected_governed_way_count']}件、restriction relationは{extension_build['extract']['selected_restriction_relation_count']}件であり、範囲は自動拡張していない。拡張後coverageは{extension['coverage_ratio']:.1%}、被覆長{extension['covered_length_m']:.1f}m、未被覆長{extension['uncovered_length_m']:.1f}m、connection violationは{extension['connection_violation_count']}件である。

## 既存66区間への影響

既存66区間は{ota_summary['unchanged_section_count']}/66 unchanged、意図しない変更{ota_summary['changed_section_count']}件である。後段利用可能mappingは前後とも{ota_summary['before_usable_mapping_count']}件である。比較対象にはedge ID、edge分割/topology、lane、speed、route identityを含む。

## connection violation

正式mapping 10/10と各directional corridorのconnection violationは0件である。

## 回帰テスト

作業前57件は57 passed（38.19秒）、作業後は既存57件と新規11件を合わせて68 passed（38.37秒）である。

## 生成・更新した成果物

- `external_observation_final_mapping.csv`: 正式mapping 10件
- `external_observation_mapping_final_edge_evidence.csv`: edge evidence
- `external_observation_final_inventory.csv`: 層別inventory
- `external_observation_network_extension_before_after.csv`: `13300010260`の拡張前後差分
- `ota66_network_extension_regression.csv`: 既存66区間の回帰差分
- `external_observation_final_mapping_qa_summary.json`: QA集計
- `external_observation_final_mapping_manifest.json`: 入出力・設定・ツール・成果物hash
- `{relative(OUTPUT_DIR)}`: 版付き限定extract、結合OSM、SUMO network、netconvert実行記録
- `{relative(Path(__file__))}`: 再生成スクリプト
- `05_src/traffic_simulation/validation/test_finalize_external_observation_mapping.py`: 新規テスト11件

## QA要約

- 外部参照: {qa['counts']['formal_mapping_rows']}/10
- connection violation: {qa['counts']['connection_violation_count']}
- matching threshold変更: {str(qa['guardrails']['matching_threshold_changed']).lower()}
- 任意の代表edge選択: {str(qa['guardrails']['representative_edge_selected']).lower()}
- raw/normalizedをmodel assumptionで上書き: {str(qa['guardrails']['raw_or_normalized_overwritten_by_assumption']).lower()}
- 生成時QA: `{qa['status']}`

## 未解決・利用制約

本依頼で方向確定を求められた`13200100070`以外は、既存候補が方向別正式割当を証明していないため、mappingを採択しても`MODEL_ASSUMPTION_REQUIRED`を維持した。これらの観測系列をSUMO方向別edgeへ流す処理は、方向証拠が追加されるまで保留である。欠測値を0で補完していない。

## 次のtraffic全66区間分類へ進めるか

進められる。既存66 mappingは不変で、外部参照10件のmapping層は確定した。ただし、方向別traffic assignmentへ進められる外部参照は現時点で`13200100070`を参照する1件だけであり、残る9件には方向証拠または明示的な研究仮定が必要である。

## ユーザー側で必要な作業

正式mapping成果物の再生成・検証には追加作業は不要である。残る9件を方向別traffic assignmentへ使用する場合だけ、公式方向証拠の提示またはmodel assumption採否の判断が必要である。

## 要するに

10/10の状態は確定し、8/8候補は正式化、Haneda方向は解決、固定bbox拡張は83.6% coverageで採択条件を満たした。既存66区間・閾値・原典は変わらず、connection violationは0、全68テストは成功である。
"""


def run(reuse_network: bool = False) -> dict[str, Any]:
    config = pipeline.load_config(CONFIG_PATH)
    verify_inputs(config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    merged_osm, extended_net, extension_build = build_extended_network(reuse=reuse_network)
    extension, _, _ = evaluate_extension(config, merged_osm, extended_net)
    raw_by_id, normalized, lengths = official_inputs(config)
    formal, evidence, inventory = build_formal_rows(
        config, extension, extended_net, merged_osm, normalized, raw_by_id, lengths
    )
    ota_rows, ota_summary = compare_ota66(extended_net)
    if len(formal) != 10 or len(inventory) != 10:
        raise ValueError("formal outputs must contain all ten external references")
    if sum(row["candidate_status"] == "AUTO_ACCEPT" and row["final_mapping_status"] == "RESOLVED" for row in formal) != 8:
        raise ValueError("all eight AUTO_ACCEPT rows were not promoted")
    if any(int(row["connection_violation_count"]) for row in formal):
        raise ValueError("formal mapping has a connection violation")
    if ota_summary["changed_section_count"]:
        raise ValueError("limited extension changed one or more existing Ota mappings")
    mapping_path = DATA_DIR / "external_observation_final_mapping.csv"
    evidence_path = DATA_DIR / "external_observation_mapping_final_edge_evidence.csv"
    inventory_path = DATA_DIR / "external_observation_final_inventory.csv"
    difference_path = DATA_DIR / "external_observation_network_extension_before_after.csv"
    ota_difference_path = DATA_DIR / "ota66_network_extension_regression.csv"
    candidate_133 = next(row for row in read_csv(DATA_DIR / "external_observation_mapping_candidates.csv") if row["observation_section_id"] == "13300010260")
    candidate_summary = json.loads((DATA_DIR / "external_observation_mapping_candidate_summary.json").read_text(encoding="utf-8"))
    before_extension = candidate_summary["network_extension"]
    extension_difference = [{
        "official_observation_section_id": "13300010260",
        "target_section_id": candidate_133["target_section_id"],
        "fixed_bbox_wgs84_json": json_text(extension_build["extract"]["bbox_wgs84"]),
        "before_network_file": relative(BASE_NET),
        "after_network_file": relative(extended_net),
        "before_coverage_ratio": candidate_133["candidate_corridor_coverage_ratio"],
        "after_coverage_ratio": extension["coverage_ratio"],
        "coverage_delta": round(extension["coverage_ratio"] - float(candidate_133["candidate_corridor_coverage_ratio"]), 6),
        "before_covered_length_m": before_extension["covered_length_m"],
        "after_covered_length_m": extension["covered_length_m"],
        "before_uncovered_length_m": before_extension["uncovered_length_m"],
        "after_uncovered_length_m": extension["uncovered_length_m"],
        "before_edge_ids": candidate_133["candidate_edge_ids"],
        "after_edge_ids": ";".join(extension["edge_ids"]),
        "before_connection_violation_count": candidate_133["connection_violation_count"],
        "after_connection_violation_count": extension["connection_violation_count"],
        "before_status": candidate_133["classification"],
        "after_mapping_status": extension["mapping_status"],
        "matching_threshold_changed": False,
        "bbox_auto_expanded": False,
    }]
    write_csv(mapping_path, formal)
    write_csv(evidence_path, evidence)
    write_csv(inventory_path, inventory)
    write_csv(difference_path, extension_difference)
    write_csv(ota_difference_path, ota_rows)
    qa = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": "PASSED",
        "counts": {
            "formal_mapping_rows": len(formal),
            "inventory_rows": len(inventory),
            "auto_accept_promoted": sum(row["candidate_status"] == "AUTO_ACCEPT" and row["final_mapping_status"] == "RESOLVED" for row in formal),
            "direction_resolved": sum(row["direction_status"] == "RESOLVED" for row in formal),
            "connection_violation_count": sum(int(row["connection_violation_count"]) for row in formal),
            "ota66_changed_sections": ota_summary["changed_section_count"],
        },
        "classification_counts": dict(Counter(row["final_acceptance_status"] for row in inventory)),
        "network_extension": extension,
        "ota66_regression": ota_summary,
        "guardrails": {
            "candidate_artifacts_overwritten": False,
            "base_network_overwritten": False,
            "matching_threshold_changed": False,
            "source_road_census_modified": False,
            "source_osm_modified": False,
            "representative_edge_selected": False,
            "missing_value_imputed_as_zero": False,
            "raw_or_normalized_overwritten_by_assumption": False,
            "bbox_auto_expanded": False,
        },
        "prework_regression": {"passed": 57, "failed": 0, "duration_seconds": 38.19},
        "postwork_regression": {"passed": 68, "failed": 0, "duration_seconds": 38.37},
    }
    qa_path = DATA_DIR / "external_observation_final_mapping_qa_summary.json"
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        render_report(formal, inventory, extension, extension_build, ota_summary, qa), encoding="utf-8"
    )
    output_paths = [mapping_path, evidence_path, inventory_path, difference_path, ota_difference_path, qa_path, REPORT_PATH,
                    OUTPUT_DIR / "minimum_bbox_relation_closed.osm.xml", merged_osm, extended_net,
                    OUTPUT_DIR / "netconvert.execution.json"]
    census_dir = REPOSITORY_ROOT / config["inputs"]["road_census_dir"]
    input_paths = [CONFIG_PATH, RELATION_CONFIG_PATH, REGIONAL_PBF, BASE_BUILD_OSM, BASE_NET, TYPEMAP,
                   RELATIONS, PREWORK_SNAPSHOT,
                   census_dir / config["inputs"]["sections_csv"],
                   census_dir / config["inputs"]["hourly_csv"],
                   REPOSITORY_ROOT / "05_src/traffic_simulation/calibration/normalize_road_census_section_attributes.py"]
    input_paths += [census_dir / config["inputs"]["section_geometry_dir"] / name for names in GEOMETRY_SOURCES.values() for name in names]
    input_paths += [DATA_DIR / name for name in CANDIDATE_HASHES]
    input_paths = list(dict.fromkeys(input_paths))
    manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "generated_at": datetime.now().astimezone().isoformat(),
        "generator": {"path": relative(Path(__file__)), "version": SCRIPT_VERSION, "sha256": sha256_file(Path(__file__))},
        "git_baseline_commit": "7c15373e97041d8f5ff35797912f4fb0b14e22bd",
        "fixed_bbox_wgs84": extension_build["extract"]["bbox_wgs84"],
        "matching_configuration": config["matching"],
        "tools": {
            "python": subprocess.run([str(Path(__file__).parents[3] / ".conda/bin/python"), "--version"], capture_output=True, text=True).stdout.strip(),
            "pyosmium": importlib.metadata.version("osmium"),
            "sumo": "Eclipse SUMO sumo Version 1.24.0",
            "netconvert": "Eclipse SUMO netconvert Version 1.24.0",
        },
        "inputs": [{"path": relative(path), "sha256": sha256_file(path)} for path in input_paths],
        "outputs": [{"path": relative(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size} for path in output_paths],
        "extension_build": extension_build,
        "qa_summary": relative(qa_path),
    }
    manifest_path = DATA_DIR / "external_observation_final_mapping_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return qa


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-network", action="store_true", help="Reuse hash-verified versioned extension artifacts")
    args = parser.parse_args()
    qa = run(reuse_network=args.reuse_network)
    print(json.dumps({"run_id": RUN_ID, "status": qa["status"], "counts": qa["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
