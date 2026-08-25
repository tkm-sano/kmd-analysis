#!/usr/bin/env python3
"""Build the immutable Phase 13 X1 external-evidence investigation population."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


X1_CLUSTER = "X1_EXTERNAL_MATCH_IDENTIFIER_ONLY"


def _canonical_sha(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tags(element: ET.Element) -> dict[str, str]:
    return {
        child.attrib["k"]: child.attrib["v"]
        for child in element.findall("tag")
    }


def _way_refs(element: ET.Element) -> list[int]:
    return [int(child.attrib["ref"]) for child in element.findall("nd")]


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    radius_m = 6_371_008.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius_m * math.asin(math.sqrt(h))


def _representative_coordinate(
    coordinates: list[tuple[float, float]],
) -> tuple[float, float]:
    if len(coordinates) == 1:
        return coordinates[0]
    lengths = [
        _haversine_m(coordinates[index - 1], coordinates[index])
        for index in range(1, len(coordinates))
    ]
    half = sum(lengths) / 2
    traversed = 0.0
    for index, length in enumerate(lengths, start=1):
        if traversed + length >= half:
            ratio = 0.0 if length == 0 else (half - traversed) / length
            lat1, lon1 = coordinates[index - 1]
            lat2, lon2 = coordinates[index]
            return lat1 + ratio * (lat2 - lat1), lon1 + ratio * (lon2 - lon1)
        traversed += length
    return coordinates[-1]


def _relation_summary(element: ET.Element, role: str) -> dict[str, Any]:
    tags = _tags(element)
    return {
        "relation_id": int(element.attrib["id"]),
        "version": int(element.attrib.get("version", "0")),
        "timestamp": element.attrib.get("timestamp"),
        "member_role": role,
        "type": tags.get("type"),
        "route": tags.get("route"),
        "ref": tags.get("ref"),
        "name": tags.get("name"),
        "name:ja": tags.get("name:ja"),
        "network": tags.get("network"),
        "operator": tags.get("operator"),
    }


def _neighbor_summary(
    way_id: int, tags: dict[str, str], shared_node_ids: Iterable[int]
) -> dict[str, Any]:
    return {
        "source_way_id": way_id,
        "shared_node_ids": sorted(shared_node_ids),
        "highway": tags.get("highway"),
        "service": tags.get("service"),
        "ref": tags.get("ref"),
        "name": tags.get("name"),
        "name:ja": tags.get("name:ja"),
        "operator": tags.get("operator"),
        "oneway": tags.get("oneway"),
        "bridge": tags.get("bridge"),
        "tunnel": tags.get("tunnel"),
    }


def _count_map(values: Iterable[str | None]) -> dict[str, int]:
    return dict(sorted(Counter(value if value is not None else "<null>" for value in values).items()))


def build_population(l4_path: Path, osm_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    l4 = json.loads(l4_path.read_text(encoding="utf-8"))
    base_records = {
        int(record["source_way_id"]): record
        for record in l4["records"]
        if record["evidence_cluster"] == X1_CLUSTER
    }
    if len(base_records) != 135:
        raise ValueError(f"expected 135 X1 Ways, found {len(base_records)}")

    target_ids = set(base_records)
    target_ways: dict[int, dict[str, Any]] = {}
    relations: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in target_ids:
                target_ways[way_id] = {
                    "version": int(element.attrib.get("version", "0")),
                    "timestamp": element.attrib.get("timestamp"),
                    "node_ids": _way_refs(element),
                    "tags": _tags(element),
                }
        elif element.tag == "relation":
            relation_members = [
                member
                for member in element.findall("member")
                if member.attrib.get("type") == "way"
                and int(member.attrib["ref"]) in target_ids
            ]
            for member in relation_members:
                relations[int(member.attrib["ref"])].append(
                    _relation_summary(element, member.attrib.get("role", ""))
                )
        if element.tag in {"node", "way", "relation"}:
            element.clear()

    missing = target_ids - set(target_ways)
    if missing:
        raise ValueError(f"target Ways missing from source OSM: {sorted(missing)}")

    target_node_ids = {
        node_id for way in target_ways.values() for node_id in way["node_ids"]
    }
    endpoint_ids = {
        node_id
        for way in target_ways.values()
        for node_id in (way["node_ids"][0], way["node_ids"][-1])
    }
    node_data: dict[int, dict[str, Any]] = {}
    neighbors: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "node":
            node_id = int(element.attrib["id"])
            if node_id in target_node_ids:
                node_data[node_id] = {
                    "lat": float(element.attrib["lat"]),
                    "lon": float(element.attrib["lon"]),
                    "version": int(element.attrib.get("version", "0")),
                    "timestamp": element.attrib.get("timestamp"),
                    "tags": _tags(element),
                }
        elif element.tag == "way":
            way_id = int(element.attrib["id"])
            refs = _way_refs(element)
            shared = endpoint_ids.intersection(refs)
            if shared:
                summary = _neighbor_summary(way_id, _tags(element), shared)
                for node_id in shared:
                    neighbors[node_id].append(summary)
        if element.tag in {"node", "way", "relation"}:
            element.clear()

    if target_node_ids - set(node_data):
        raise ValueError("one or more target geometry nodes are missing")

    records: list[dict[str, Any]] = []
    for way_id in sorted(target_ids):
        base = base_records[way_id]
        way = target_ways[way_id]
        coords = [
            (node_data[node_id]["lat"], node_data[node_id]["lon"])
            for node_id in way["node_ids"]
        ]
        representative = _representative_coordinate(coords)
        length_m = sum(
            _haversine_m(coords[index - 1], coords[index])
            for index in range(1, len(coords))
        )
        start_id = way["node_ids"][0]
        end_id = way["node_ids"][-1]
        record = {
            "source_way_id": way_id,
            "stable_blocker_id": base["stable_blocker_id"],
            "stop_code": base["stop_code"],
            "blocker_message": base["blocker_message"],
            "evidence_cluster": X1_CLUSTER,
            "source_way_version": way["version"],
            "source_way_timestamp": way["timestamp"],
            "highway": way["tags"].get("highway"),
            "service": way["tags"].get("service"),
            "names": {
                key: way["tags"][key]
                for key in ("name", "name:ja", "name:en")
                if key in way["tags"]
            },
            "identifiers": {
                key: way["tags"][key]
                for key in ("ref", "nat_ref", "official_name", "wikidata", "wikipedia")
                if key in way["tags"]
            },
            "operator": way["tags"].get("operator"),
            "bridge": way["tags"].get("bridge"),
            "tunnel": way["tags"].get("tunnel"),
            "junction": way["tags"].get("junction"),
            "oneway": way["tags"].get("oneway"),
            "geometry": {
                "type": "LineString",
                "coordinates_lon_lat": [[lon, lat] for lat, lon in coords],
                "representative_coordinate_lon_lat": [representative[1], representative[0]],
                "geodesic_length_m": round(length_m, 3),
                "node_ids": way["node_ids"],
            },
            "start_context": {
                "node_id": start_id,
                **node_data[start_id],
                "neighboring_ways": sorted(
                    (item for item in neighbors[start_id] if item["source_way_id"] != way_id),
                    key=lambda item: item["source_way_id"],
                ),
            },
            "end_context": {
                "node_id": end_id,
                **node_data[end_id],
                "neighboring_ways": sorted(
                    (item for item in neighbors[end_id] if item["source_way_id"] != way_id),
                    key=lambda item: item["source_way_id"],
                ),
            },
            "relation_memberships": sorted(
                relations.get(way_id, []), key=lambda item: item["relation_id"]
            ),
            "existing_lane_related_tags": base["all_lane_related_tags"],
            "source_tags": way["tags"],
            "external_match_status": "not_evaluated",
        }
        records.append(record)

    way_ids = [record["source_way_id"] for record in records]
    source_osm = {
        "path": str(osm_path),
        "byte_sha256": _file_sha(osm_path),
        "snapshot_date": "2026-07-16",
    }
    population = {
        "schema_version": 1,
        "investigation_id": "phase13_x1_official_evidence_20260821",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "status": "fixed_population_external_match_not_evaluated",
        "population_definition": {
            "source_cluster": X1_CLUSTER,
            "expected_count": 135,
            "predicate": "exact records classified X1 in the fixed L4 v2 investigation",
        },
        "source_l4_investigation": {
            "path": str(l4_path),
            "byte_sha256": _file_sha(l4_path),
            "semantic_sha256": l4.get("semantic_sha256"),
        },
        "source_osm": source_osm,
        "summary": {
            "population_count": len(records),
            "unique_source_way_count": len(set(way_ids)),
            "unique_stable_blocker_id_count": len(
                {record["stable_blocker_id"] for record in records}
            ),
            "stable_source_way_id_set_sha256": _canonical_sha(way_ids),
            "records_semantic_sha256": _canonical_sha(records),
        },
        "records": records,
    }

    aggregates = {
        "schema_version": 1,
        "investigation_id": population["investigation_id"],
        "population_count": len(records),
        "highway_counts": _count_map(record["highway"] for record in records),
        "ref_counts": _count_map(record["identifiers"].get("ref") for record in records),
        "name_counts": _count_map(record["names"].get("name") for record in records),
        "operator_counts": _count_map(record["operator"] for record in records),
        "service_counts": _count_map(record["service"] for record in records),
        "bridge_counts": _count_map(record["bridge"] for record in records),
        "tunnel_counts": _count_map(record["tunnel"] for record in records),
        "junction_counts": _count_map(record["junction"] for record in records),
        "oneway_counts": _count_map(record["oneway"] for record in records),
        "route_relation_membership_count": sum(
            any(item.get("type") == "route" for item in record["relation_memberships"])
            for record in records
        ),
        "source_way_timestamp_range": {
            "minimum": min(record["source_way_timestamp"] for record in records),
            "maximum": max(record["source_way_timestamp"] for record in records),
        },
        "population_summary_sha256": population["summary"]["records_semantic_sha256"],
    }
    return population, aggregates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l4", required=True, type=Path)
    parser.add_argument("--osm", required=True, type=Path)
    parser.add_argument("--population-output", required=True, type=Path)
    parser.add_argument("--aggregates-output", required=True, type=Path)
    args = parser.parse_args()

    for output in (args.population_output, args.aggregates_output):
        if output.exists():
            raise FileExistsError(f"immutable output already exists: {output}")

    population, aggregates = build_population(args.l4, args.osm)
    args.population_output.write_text(
        json.dumps(population, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.aggregates_output.write_text(
        json.dumps(aggregates, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"population": population["summary"], "aggregates": aggregates}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
