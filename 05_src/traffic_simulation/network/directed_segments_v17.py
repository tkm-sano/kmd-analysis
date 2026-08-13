"""Production Directed Segment generation and restriction mapping for v17."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network_v17.yml"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/directed_segment_v17.schema.json"
)
RELATION_CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/relation_closure_v16.yml"
)


class DirectedSegmentError(ValueError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DirectedSegmentError(
            f"YAML root must be an object: {path}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DirectedSegmentError(
            f"JSON root must be an object: {path}",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _segment_validator() -> jsonschema.Draft202012Validator:
    schema = _load_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


@lru_cache(maxsize=1)
def _governed_highways() -> frozenset[str]:
    return frozenset(
        _load_yaml(RELATION_CONFIG_PATH)["road_population"]["governed_highway_types"]
    )


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    return _load_yaml(REGISTRY_PATH)


def canonical_segment_id(
    source_way_id: int,
    source_start_index: int,
    source_end_index: int,
    source_direction: str,
) -> str:
    if source_way_id <= 0 or source_start_index < 0:
        raise DirectedSegmentError(
            "source Way ID and start index must be non-negative canonical values",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    if source_start_index >= source_end_index:
        raise DirectedSegmentError(
            "source_start_index must be less than source_end_index",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    if source_direction not in {"forward", "backward"}:
        raise DirectedSegmentError(
            f"unsupported source direction: {source_direction}",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    return (
        f"ds:{source_way_id}:{source_start_index}:"
        f"{source_end_index}:{source_direction}"
    )


def normalize_oneway(
    tags: Mapping[str, str], *, registry: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Resolve base direction from registered explicit or absent rules."""

    rules = dict(registry or _registry())["oneway_rules"]
    if "oneway" in tags:
        raw = tags["oneway"]
        if not isinstance(raw, str) or not raw.strip() or any(
            token in raw for token in (";", "|", "@")
        ):
            raise DirectedSegmentError(
                f"invalid explicit oneway value: {raw!r}",
                stop_code="ONEWAY_VALUE_INVALID",
                status="invalid",
            )
        normalized = raw.strip().lower()
        explicit_normalization = {
            ("yes" if key is True else "no" if key is False else str(key)): value
            for key, value in rules["explicit_normalization"].items()
        }
        canonical = explicit_normalization.get(normalized)
        if canonical is None:
            raise DirectedSegmentError(
                f"unsupported explicit oneway value: {raw!r}",
                stop_code="ONEWAY_VALUE_UNSUPPORTED",
                status="valid_but_unsupported",
            )
        return {
            "canonical_oneway": canonical,
            "value_origin": (
                "source_explicit" if normalized == canonical else "source_normalized"
            ),
            "rule_id": None,
            "source_value": raw,
        }

    for rule in sorted(
        rules["absent_rules"], key=lambda item: (-item["priority"], item["rule_id"])
    ):
        predicate = rule["predicate"]
        if predicate == "junction_roundabout" and tags.get("junction") == "roundabout":
            matched = True
        elif predicate == "highway_motorway" and tags.get("highway") == "motorway":
            matched = True
        elif predicate == "ordinary_road_without_oneway":
            matched = tags.get("highway") in _governed_highways() - {
                "motorway",
                "motorway_link",
            }
            matched = matched and tags.get("junction") != "roundabout"
        else:
            matched = False
        if matched:
            return {
                "canonical_oneway": rule["canonical_value"],
                "value_origin": rule["value_origin"],
                "rule_id": rule["rule_id"],
                "source_value": None,
            }
    raise DirectedSegmentError(
        "no registered absent-oneway rule matches the source Way",
        stop_code="ONEWAY_RULE_NOT_REGISTERED",
        status="unresolved",
    )


def validate_directed_segment(
    segment: Mapping[str, Any], *, source_way_node_ids: Sequence[int]
) -> None:
    try:
        _segment_validator().validate(segment)
    except jsonschema.ValidationError as error:
        raise DirectedSegmentError(
            f"Directed Segment Schema violation: {error.message}",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        ) from error

    start = segment["source_start_index"]
    end = segment["source_end_index"]
    if not 0 <= start < end < len(source_way_node_ids):
        raise DirectedSegmentError(
            "Directed Segment interval is outside the immutable source Way",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    source_nodes = list(source_way_node_ids[start : end + 1])
    if segment["source_node_ids"] != source_nodes:
        raise DirectedSegmentError(
            "Directed Segment does not preserve exact source-node lineage",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    expected_travel = (
        source_nodes
        if segment["source_direction"] == "forward"
        else list(reversed(source_nodes))
    )
    if segment["travel_node_ids"] != expected_travel:
        raise DirectedSegmentError(
            "travel node order disagrees with source direction",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    expected_id = canonical_segment_id(
        segment["source_way_id"], start, end, segment["source_direction"]
    )
    if segment["directed_segment_id"] != expected_id:
        raise DirectedSegmentError(
            "Directed Segment ID disagrees with its canonical interval",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )


def build_directed_segment(
    *,
    source_way_id: int,
    source_start_index: int,
    source_end_index: int,
    source_way_node_ids: Sequence[int],
    source_direction: str,
    derivation_rule_id: str,
) -> dict[str, Any]:
    source_nodes = list(source_way_node_ids[source_start_index : source_end_index + 1])
    travel_nodes = (
        source_nodes
        if source_direction == "forward"
        else list(reversed(source_nodes))
    )
    segment = {
        "directed_segment_id": canonical_segment_id(
            source_way_id,
            source_start_index,
            source_end_index,
            source_direction,
        ),
        "source_way_id": source_way_id,
        "source_start_index": source_start_index,
        "source_end_index": source_end_index,
        "source_direction": source_direction,
        "source_node_ids": source_nodes,
        "travel_node_ids": travel_nodes,
        "derivation_rule_id": derivation_rule_id,
    }
    validate_directed_segment(segment, source_way_node_ids=source_way_node_ids)
    return segment


def generate_way_segments(
    way: Mapping[str, Any], *, split_indices: Iterable[int] | None = None
) -> tuple[dict[str, Any], ...]:
    """Generate canonical intervals without mutating the supplied source Way."""

    source = copy.deepcopy(dict(way))
    try:
        way_id = int(source["source_way_id"])
        nodes = tuple(int(item) for item in source["source_node_ids"])
        tags = dict(source["tags"])
    except (KeyError, TypeError, ValueError) as error:
        raise DirectedSegmentError(
            "source Way is missing a valid ID, node sequence, or tags",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        ) from error
    if len(nodes) < 2:
        raise DirectedSegmentError(
            "source Way requires at least two nodes",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    resolution = normalize_oneway(tags)
    directions = {
        "yes": ("forward",),
        "no": ("forward", "backward"),
        "-1": ("backward",),
    }[resolution["canonical_oneway"]]
    boundaries = sorted(set(split_indices or ()) | {0, len(nodes) - 1})
    if boundaries[0] != 0 or boundaries[-1] != len(nodes) - 1 or any(
        not 0 <= item < len(nodes) for item in boundaries
    ):
        raise DirectedSegmentError(
            "split index is outside the immutable source Way",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    rule_id = resolution["rule_id"] or (
        f"OSM_ONEWAY_EXPLICIT_{resolution['canonical_oneway']}"
    )
    result = tuple(
        build_directed_segment(
            source_way_id=way_id,
            source_start_index=start,
            source_end_index=end,
            source_way_node_ids=nodes,
            source_direction=direction,
            derivation_rule_id=rule_id,
        )
        for start, end in zip(boundaries, boundaries[1:])
        for direction in directions
    )
    if dict(way) != source:
        raise DirectedSegmentError(
            "production generation mutated the source Way",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    return result


def _unique_candidate(candidates: Sequence[Any], *, label: str) -> Any:
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise DirectedSegmentError(
            f"relation {label} has no exact Directed Segment candidate",
            stop_code="RELATION_DIRECTED_MAPPING_MISSING",
            status="unresolved",
        )
    raise DirectedSegmentError(
        f"relation {label} has multiple exact Directed Segment candidates",
        stop_code="RELATION_DIRECTED_MAPPING_AMBIGUOUS",
        status="conflict",
    )


def adopt_unique_relation_candidate(candidate_ids: Sequence[str]) -> str:
    """Apply the normative 0/1/many relation-candidate contract."""

    return str(_unique_candidate(list(candidate_ids), label="Directed Segment"))


def map_turn_restriction(
    relation: Mapping[str, Any],
    *,
    ways: Mapping[int, Mapping[str, Any]],
    segments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Map node- or way-via restriction members using exact lineage only."""

    relation_id = int(relation["relation_id"])
    members = list(relation["members"])
    tags = dict(relation["tags"])
    relation_type = tags.get("type")
    if relation_type not in {"restriction", "restriction:bus"}:
        raise DirectedSegmentError(
            f"relation {relation_id} has unregistered restriction semantics",
            stop_code="RELATION_DIRECTED_MAPPING_MISSING",
            status="unresolved",
        )
    from_members = [m for m in members if m["role"] == "from" and m["type"] == "way"]
    to_members = [m for m in members if m["role"] == "to" and m["type"] == "way"]
    via_members = [m for m in members if m["role"] == "via"]
    from_member = _unique_candidate(from_members, label="from member")
    to_member = _unique_candidate(to_members, label="to member")
    if not via_members:
        _unique_candidate([], label="via member")

    from_way_id = int(from_member["ref"])
    to_way_id = int(to_member["ref"])
    by_way: dict[int, list[Mapping[str, Any]]] = {}
    for segment in segments:
        by_way.setdefault(int(segment["source_way_id"]), []).append(segment)

    if len(via_members) == 1 and via_members[0]["type"] == "node":
        via_node = int(via_members[0]["ref"])
        from_candidates = [
            item
            for item in by_way.get(from_way_id, [])
            if item["travel_node_ids"][-1] == via_node
        ]
        to_candidates = [
            item
            for item in by_way.get(to_way_id, [])
            if item["travel_node_ids"][0] == via_node
        ]
        selected_from = _unique_candidate(from_candidates, label="from")
        selected_to = _unique_candidate(to_candidates, label="to")
        via_mapping: list[dict[str, Any]] = [
            {"member_type": "node", "source_node_id": via_node}
        ]
    elif all(item["type"] == "way" for item in via_members):
        via_way_ids = [int(item["ref"]) for item in via_members]
        member_way_ids = [from_way_id, *via_way_ids, to_way_id]
        connection_nodes: list[int] = []
        for left_id, right_id in zip(member_way_ids, member_way_ids[1:]):
            left_nodes = set(ways[left_id]["source_node_ids"])
            right_nodes = set(ways[right_id]["source_node_ids"])
            connection_nodes.append(
                _unique_candidate(
                    sorted(left_nodes & right_nodes),
                    label=f"connection {left_id}->{right_id}",
                )
            )
        selected_from = _unique_candidate(
            [
                item
                for item in by_way.get(from_way_id, [])
                if item["travel_node_ids"][-1] == connection_nodes[0]
            ],
            label="from",
        )
        selected_to = _unique_candidate(
            [
                item
                for item in by_way.get(to_way_id, [])
                if item["travel_node_ids"][0] == connection_nodes[-1]
            ],
            label="to",
        )
        via_mapping = []
        for position, via_way_id in enumerate(via_way_ids):
            entry = connection_nodes[position]
            exit_node = connection_nodes[position + 1]
            paths = _via_way_paths(by_way.get(via_way_id, []), entry, exit_node)
            selected_path = _unique_candidate(paths, label=f"via way {via_way_id}")
            via_mapping.append(
                {
                    "member_type": "way",
                    "source_way_id": via_way_id,
                    "directed_segment_ids": [
                        item["directed_segment_id"] for item in selected_path
                    ],
                }
            )
    else:
        raise DirectedSegmentError(
            f"relation {relation_id} mixes unsupported via member types",
            stop_code="RELATION_DIRECTED_MAPPING_MISSING",
            status="unresolved",
        )

    return {
        "relation_id": relation_id,
        "relation_type": relation_type,
        "restriction": tags.get("restriction") or tags.get(relation_type),
        "from_directed_segment_id": selected_from["directed_segment_id"],
        "via": via_mapping,
        "to_directed_segment_id": selected_to["directed_segment_id"],
        "mapping_method": "exact_source_node_lineage",
    }


def _via_way_paths(
    segments: Sequence[Mapping[str, Any]], entry: int, exit_node: int
) -> list[list[Mapping[str, Any]]]:
    paths: list[list[Mapping[str, Any]]] = []
    for direction in ("forward", "backward"):
        current = entry
        path: list[Mapping[str, Any]] = []
        used: set[str] = set()
        while current != exit_node:
            candidates = [
                item
                for item in segments
                if item["source_direction"] == direction
                and item["travel_node_ids"][0] == current
                and item["directed_segment_id"] not in used
            ]
            if len(candidates) != 1:
                path = []
                break
            selected = candidates[0]
            path.append(selected)
            used.add(str(selected["directed_segment_id"]))
            current = int(selected["travel_node_ids"][-1])
        if path and current == exit_node:
            paths.append(path)
    return paths


def _xml_source(path: Path, governed_highways: set[str]) -> tuple[
    dict[int, dict[str, Any]], list[dict[str, Any]], Counter[int]
]:
    ways: dict[int, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    node_way_count: Counter[int] = Counter()
    for _event, element in ET.iterparse(path, events=("end",)):
        if element.tag == "way":
            tags = {item.attrib["k"]: item.attrib["v"] for item in element.findall("tag")}
            if tags.get("highway") in governed_highways:
                way_id = int(element.attrib["id"])
                nodes = [int(item.attrib["ref"]) for item in element.findall("nd")]
                ways[way_id] = {
                    "source_way_id": way_id,
                    "source_node_ids": nodes,
                    "tags": tags,
                }
                node_way_count.update(set(nodes))
            element.clear()
        elif element.tag == "relation":
            tags = {item.attrib["k"]: item.attrib["v"] for item in element.findall("tag")}
            if tags.get("type") in {"restriction", "restriction:bus"}:
                relations.append(
                    {
                        "relation_id": int(element.attrib["id"]),
                        "members": [
                            {
                                "type": item.attrib["type"],
                                "ref": int(item.attrib["ref"]),
                                "role": item.attrib.get("role", ""),
                            }
                            for item in element.findall("member")
                        ],
                        "tags": tags,
                    }
                )
            element.clear()
        elif element.tag == "node":
            element.clear()
    return ways, relations, node_way_count


def build_production_artifact(input_path: Path) -> dict[str, Any]:
    """Run the v17 Directed Segment stage against a relation-closed OSM file."""

    before_hash = sha256_file(input_path)
    config = _load_yaml(CONFIG_PATH)
    relation_config = _load_yaml(RELATION_CONFIG_PATH)
    governed = set(relation_config["road_population"]["governed_highway_types"])
    ways, relations, node_way_count = _xml_source(input_path, governed)
    via_nodes = {
        int(member["ref"])
        for relation in relations
        for member in relation["members"]
        if member["role"] == "via" and member["type"] == "node"
    }

    segments: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for way_id in sorted(ways):
        way = ways[way_id]
        split_indices = {
            index
            for index, node_id in enumerate(way["source_node_ids"])
            if node_way_count[node_id] > 1 or node_id in via_nodes
        }
        try:
            segments.extend(generate_way_segments(way, split_indices=split_indices))
        except DirectedSegmentError as error:
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": error.status,
                    "stop_code": error.stop_code,
                    "message": str(error),
                }
            )

    segments.sort(key=lambda item: item["directed_segment_id"])
    mappings: list[dict[str, Any]] = []
    for relation in sorted(relations, key=lambda item: item["relation_id"]):
        try:
            mappings.append(map_turn_restriction(relation, ways=ways, segments=segments))
        except (DirectedSegmentError, KeyError) as error:
            if isinstance(error, DirectedSegmentError):
                status, stop_code = error.status, error.stop_code
            else:
                status, stop_code = "unresolved", "RELATION_DIRECTED_MAPPING_MISSING"
            blockers.append(
                {
                    "scope": "relation",
                    "relation_id": relation["relation_id"],
                    "resolution_status": status,
                    "stop_code": stop_code,
                    "message": str(error),
                }
            )
    after_hash = sha256_file(input_path)
    if before_hash != after_hash:
        raise DirectedSegmentError(
            "source OSM bytes changed during Directed Segment generation",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )

    canonical_payload = json.dumps(
        {"directed_segments": segments, "relation_mappings": mappings},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 17,
        "artifact_type": "directed_segment_production_collection",
        "configuration_id": config["configuration_id"],
        "population_version": config["population_version"],
        "source": {"path": str(input_path), "sha256": before_hash},
        "direction_evidence": "exact_source_node_lineage",
        "source_way_mutated": False,
        "directed_segments": segments,
        "relation_mappings": mappings,
        "blockers": blockers,
        "counts": {
            "source_ways": len(ways),
            "directed_segments": len(segments),
            "restriction_relations": len(relations),
            "mapped_relations": len(mappings),
            "blockers": len(blockers),
        },
        "semantic_sha256": hashlib.sha256(canonical_payload).hexdigest(),
    }


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite Directed Segment artifact: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(artifact, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, output_path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate v17 Directed Segments and exact relation mappings."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = build_production_artifact(args.input)
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 1 if artifact["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
