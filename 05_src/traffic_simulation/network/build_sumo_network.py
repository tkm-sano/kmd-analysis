"""Prepare governed, relation-closed OSM inputs for the SUMO network build."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Iterable, Iterator, Sequence
from urllib.parse import unquote
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator
from shapely.geometry import LineString
import yaml

from traffic_simulation.network.study_areas import load_study_area
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/relation_closure_v16.yml"
)
MANIFEST_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "relation_closure_manifest.schema.json"
)
JST = ZoneInfo("Asia/Tokyo")
ELEMENT_NAMES = {"n": "nodes", "w": "ways", "r": "relations"}


class PrepareError(RuntimeError):
    """Raised when a governed prepare input or quality gate fails."""


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in value:
            raise PrepareError(f"duplicate YAML key: {key}")
        value[key] = loader.construct_object(value_node, deep=deep)
    return value


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise PrepareError(f"path must be repository-relative: {value}")
    return REPOSITORY_ROOT / path


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.load(handle, Loader=UniqueKeyLoader)
    if not isinstance(config, dict):
        raise PrepareError("relation closure configuration must be a mapping")
    if config.get("schema_version") != 1:
        raise PrepareError("unsupported relation closure schema_version")
    version = config.get("config_version")
    if config.get("config_id") != f"ota_ward_relation_closure_v{version}":
        raise PrepareError("relation closure config_id and version do not match")
    retained = config.get("relation_policy", {}).get("retained", {})
    if set(retained) != {"restriction", "restriction:bus"}:
        raise PrepareError("v16 must retain ordinary and bus turn restrictions")
    required = config["relation_policy"]["known_required_relation_ids"]
    if len(required) != len(set(required)):
        raise PrepareError("known required relation IDs must be unique")
    return config


def verify_registered_file(record: dict[str, Any], label: str) -> Path:
    path = repository_path(record["path"])
    if not path.is_file():
        raise PrepareError(f"{label} does not exist: {record['path']}")
    actual = sha256_file(path)
    if actual != record["sha256"]:
        raise PrepareError(
            f"{label} SHA-256 mismatch: expected {record['sha256']}, got {actual}"
        )
    return path


def _field(line: str, prefix: str) -> str:
    for part in line.rstrip("\n").split(" "):
        if part.startswith(prefix):
            return part[len(prefix) :]
    return ""


def opl_tags(line: str) -> dict[str, str]:
    encoded = _field(line, "T")
    if not encoded:
        return {}
    result: dict[str, str] = {}
    for pair in encoded.split(","):
        key, separator, value = pair.partition("=")
        if not separator:
            raise PrepareError(f"invalid OPL tag pair: {pair}")
        decoded_key = unquote(key)
        if decoded_key in result:
            raise PrepareError(f"duplicate OSM tag key: {decoded_key}")
        result[decoded_key] = unquote(value)
    return result


def opl_way_nodes(line: str) -> tuple[int, ...]:
    encoded = _field(line, "N")
    if not encoded:
        return ()
    try:
        return tuple(int(item[1:]) for item in encoded.split(",") if item)
    except ValueError as exc:
        raise PrepareError("invalid OPL way node reference") from exc


def opl_relation_members(line: str) -> tuple[tuple[str, int, str], ...]:
    encoded = _field(line, "M")
    if not encoded:
        return ()
    members: list[tuple[str, int, str]] = []
    for item in encoded.split(","):
        typed_id, separator, role = item.partition("@")
        if not separator or typed_id[:1] not in ELEMENT_NAMES:
            raise PrepareError(f"invalid OPL relation member: {item}")
        try:
            members.append((typed_id[0], int(typed_id[1:]), unquote(role)))
        except ValueError as exc:
            raise PrepareError(f"invalid OPL relation member: {item}") from exc
    return tuple(members)


def iter_osmium_opl(path: Path) -> Iterator[str]:
    command = ["osmium", "cat", str(path), "-f", "opl"]
    process = subprocess.Popen(
        command,
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    try:
        for line in process.stdout:
            if line.strip():
                yield line
    finally:
        process.stdout.close()
    stderr = process.stderr.read() if process.stderr is not None else ""
    return_code = process.wait()
    if return_code:
        raise PrepareError(f"osmium cat failed ({return_code}): {stderr.strip()}")


def run_command(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise PrepareError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stderr.strip()}"
        )


def scan_bbox(
    bbox_path: Path,
    id_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    retained_rules = config["relation_policy"]["retained"]
    stop_prefixes = tuple(config["relation_policy"]["stop_type_prefixes"])
    ids: dict[str, set[int]] = {"n": set(), "w": set(), "r": set()}
    counts = Counter()
    retained_by_type = Counter()
    retained_by_category = Counter()
    discarded_by_type = Counter()
    retained_relations: dict[int, str] = {}
    duplicate_count = 0

    with id_path.open("w", encoding="ascii", newline="\n") as handle:
        for line in iter_osmium_opl(bbox_path):
            kind = line[0]
            if kind not in ELEMENT_NAMES:
                continue
            osm_id = int(line.split(" ", 1)[0][1:])
            if osm_id in ids[kind]:
                duplicate_count += 1
                continue
            ids[kind].add(osm_id)
            counts[ELEMENT_NAMES[kind]] += 1
            if kind in {"n", "w"}:
                handle.write(f"{kind}{osm_id}\n")
                continue

            relation_type = opl_tags(line).get("type", "")
            if relation_type in retained_rules:
                rule = retained_rules[relation_type]
                retained_relations[osm_id] = relation_type
                retained_by_type[relation_type] += 1
                retained_by_category[rule["category"]] += 1
                handle.write(f"r{osm_id}\n")
            elif relation_type.startswith(stop_prefixes):
                raise PrepareError(
                    "unclassified vehicle-specific restriction type: "
                    f"{relation_type or '<missing>'} on relation {osm_id}"
                )
            else:
                discarded_by_type[relation_type or "<missing>"] += 1

    if duplicate_count:
        raise PrepareError(f"BBOX input has {duplicate_count} duplicate identifiers")
    missing_required = sorted(
        set(config["relation_policy"]["known_required_relation_ids"])
        - set(retained_relations)
    )
    if missing_required:
        raise PrepareError(f"required bus restrictions are absent: {missing_required}")
    return {
        "ids": ids,
        "counts": dict(counts),
        "retained_relations": retained_relations,
        "retained_by_type": dict(sorted(retained_by_type.items())),
        "retained_by_category": dict(sorted(retained_by_category.items())),
        "discarded_by_type": dict(sorted(discarded_by_type.items())),
    }


def relation_cycles(graph: dict[int, set[int]]) -> list[list[int]]:
    state: dict[int, int] = {}
    stack: list[int] = []
    cycles: list[list[int]] = []

    def visit(relation_id: int) -> None:
        status = state.get(relation_id, 0)
        if status == 1:
            start = stack.index(relation_id)
            cycles.append(stack[start:] + [relation_id])
            return
        if status == 2:
            return
        state[relation_id] = 1
        stack.append(relation_id)
        for child in sorted(graph.get(relation_id, ())):
            visit(child)
        stack.pop()
        state[relation_id] = 2

    for relation_id in sorted(graph):
        visit(relation_id)
    return cycles


def transitive_relation_members(
    relation_members: dict[int, tuple[tuple[str, int, str], ...]]
) -> tuple[set[int], set[int]]:
    support_nodes: set[int] = set()
    support_ways: set[int] = set()
    visited: set[int] = set()

    def visit(relation_id: int) -> None:
        if relation_id in visited:
            return
        visited.add(relation_id)
        for kind, member_id, _role in relation_members.get(relation_id, ()):
            if kind == "n":
                support_nodes.add(member_id)
            elif kind == "w":
                support_ways.add(member_id)
            else:
                visit(member_id)

    for relation_id in relation_members:
        visit(relation_id)
    return support_nodes, support_ways


def scan_closed(
    closed_path: Path,
    bbox_scan: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    base_ids: dict[str, set[int]] = bbox_scan["ids"]
    ids: dict[str, set[int]] = {"n": set(), "w": set(), "r": set()}
    counts = Counter()
    duplicates = 0
    missing_node_refs = 0
    way_nodes: dict[int, tuple[int, ...]] = {}
    way_highways: dict[int, str] = {}
    node_coordinates: dict[int, tuple[float, float]] = {}
    relation_members: dict[int, tuple[tuple[str, int, str], ...]] = {}
    relation_types: dict[int, str] = {}
    governed = set(config["road_population"]["governed_highway_types"])

    for line in iter_osmium_opl(closed_path):
        kind = line[0]
        if kind not in ELEMENT_NAMES:
            continue
        osm_id = int(line.split(" ", 1)[0][1:])
        if osm_id in ids[kind]:
            duplicates += 1
            continue
        ids[kind].add(osm_id)
        counts[ELEMENT_NAMES[kind]] += 1
        if kind == "n":
            try:
                node_coordinates[osm_id] = (
                    float(_field(line, "x")),
                    float(_field(line, "y")),
                )
            except ValueError as exc:
                raise PrepareError(f"node {osm_id} has invalid coordinates") from exc
        elif kind == "w":
            refs = opl_way_nodes(line)
            missing_node_refs += sum(ref not in ids["n"] for ref in refs)
            highway = opl_tags(line).get("highway", "")
            if highway in governed:
                way_nodes[osm_id] = refs
                way_highways[osm_id] = highway
        else:
            relation_members[osm_id] = opl_relation_members(line)
            relation_types[osm_id] = opl_tags(line).get("type", "")

    missing_way_members = 0
    missing_relation_members = 0
    missing_node_members = 0
    graph: dict[int, set[int]] = {}
    for relation_id, members in relation_members.items():
        graph[relation_id] = set()
        for kind, member_id, _role in members:
            if member_id not in ids[kind]:
                if kind == "n":
                    missing_node_members += 1
                elif kind == "w":
                    missing_way_members += 1
                else:
                    missing_relation_members += 1
            if kind == "r":
                graph[relation_id].add(member_id)
    cycles = relation_cycles(graph)
    missing_node_total = missing_node_refs + missing_node_members
    if duplicates or missing_node_total or missing_way_members or missing_relation_members:
        raise PrepareError(
            "closed input failed reference validation: "
            f"duplicates={duplicates}, missing_nodes={missing_node_total}, "
            f"missing_ways={missing_way_members}, "
            f"missing_relations={missing_relation_members}"
        )
    if cycles:
        raise PrepareError(f"relation reference cycles detected: {cycles[:3]}")
    expected_relations = bbox_scan["retained_relations"]
    if relation_types != expected_relations:
        raise PrepareError("closed relation set or source types differ from selected scope")

    boundary = load_study_area(config["study_area"]["region_id"]).api_boundary
    final_ids: set[int] = set()
    for way_id, refs in way_nodes.items():
        if len(refs) < 2:
            continue
        coordinates = [node_coordinates[ref] for ref in refs]
        if boundary.intersects(LineString(coordinates)):
            final_ids.add(way_id)

    relation_nodes, relation_ways = transitive_relation_members(relation_members)
    topology_support_ids = relation_ways - final_ids
    final_node_ids = {
        node_id for way_id in final_ids for node_id in way_nodes.get(way_id, ())
    }
    topology_support_node_ids = (
        relation_nodes
        | {
            node_id
            for way_id in topology_support_ids
            for node_id in way_nodes.get(way_id, ())
        }
    ) - final_node_ids
    candidate_ids = set(way_highways)
    excluded_ids = ids["w"] - final_ids - topology_support_ids
    supplemented = {
        kind: sorted(ids[kind] - base_ids[kind]) for kind in ("n", "w", "r")
    }
    candidate_by_highway = Counter(way_highways.values())
    final_by_highway = Counter(way_highways[way_id] for way_id in final_ids)
    candidate_by_origin = Counter(
        "bbox" if way_id in base_ids["w"] else "regional_supplement"
        for way_id in candidate_ids
    )

    return {
        "ids": ids,
        "counts": dict(counts),
        "supplemented": supplemented,
        "reference_validation": {
            "missing_node_references": 0,
            "missing_way_members": 0,
            "missing_relation_members": 0,
            "relation_cycles": 0,
            "duplicate_identifiers": 0,
        },
        "relation_member_node_ids": sorted(relation_nodes),
        "candidate_ids": candidate_ids,
        "final_ids": final_ids,
        "final_node_ids": final_node_ids,
        "topology_support_ids": topology_support_ids,
        "topology_support_node_ids": topology_support_node_ids,
        "excluded_ids": excluded_ids,
        "candidate_by_highway": dict(sorted(candidate_by_highway.items())),
        "final_by_highway": dict(sorted(final_by_highway.items())),
        "candidate_by_origin": dict(sorted(candidate_by_origin.items())),
    }


def candidate_ids(path: Path, governed_highways: Iterable[str]) -> set[int]:
    governed = set(governed_highways)
    result: set[int] = set()
    for line in iter_osmium_opl(path):
        if line[0] == "w" and opl_tags(line).get("highway") in governed:
            result.add(int(line.split(" ", 1)[0][1:]))
    return result


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_acceptance(
    config: dict[str, Any],
    bbox_scan: dict[str, Any],
    closed_scan: dict[str, Any],
    output_hashes: dict[str, str],
) -> None:
    expected = config["acceptance"]
    actual_counts = {
        "bbox": bbox_scan["counts"],
        "closed": closed_scan["counts"],
        "supplemented": {
            "nodes": len(closed_scan["supplemented"]["n"]),
            "ways": len(closed_scan["supplemented"]["w"]),
            "relations": len(closed_scan["supplemented"]["r"]),
        },
    }
    actual_population = {
        "governed_candidate_ways": len(closed_scan["candidate_ids"]),
        "final_analysis_target_ways": len(closed_scan["final_ids"]),
        "topology_support_ways": len(closed_scan["topology_support_ids"]),
        "excluded_ways": len(closed_scan["excluded_ids"]),
    }
    checks = {
        "retained relation counts": (
            expected["retained_relation_counts"],
            bbox_scan["retained_by_type"],
        ),
        "element counts": (expected["element_counts"], actual_counts),
        "road population": (expected["road_population"], actual_population),
        "output SHA-256": (expected["output_sha256"], output_hashes),
    }
    for label, (expected_value, actual_value) in checks.items():
        if expected_value != actual_value:
            raise PrepareError(
                f"{label} differs from the fixed acceptance value: "
                f"expected {expected_value}, got {actual_value}"
            )


def relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def prepare(config_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    bbox_path = verify_registered_file(config["inputs"]["bbox_extract"], "BBOX extract")
    regional_path = verify_registered_file(
        config["inputs"]["regional_authority"], "regional authority"
    )
    baseline_path = verify_registered_file(
        config["inputs"]["v15_baseline"]["relation_closed_pbf"],
        "v15 baseline",
    )
    output_paths = {
        name: repository_path(value) for name, value in config["outputs"].items()
    }
    for path in output_paths.values():
        if path.exists() and not overwrite:
            raise PrepareError(f"output exists; use --overwrite: {relative(path)}")
        path.parent.mkdir(parents=True, exist_ok=True)

    output_parent = output_paths["manifest"].parent
    with tempfile.TemporaryDirectory(prefix=".relation-closure-v16-", dir=output_parent) as raw:
        stage = Path(raw)
        staged = {name: stage / path.name for name, path in output_paths.items()}
        bbox_scan = scan_bbox(bbox_path, staged["id_set"], config)
        getid_command = [
            "osmium",
            "getid",
            str(regional_path),
            "--id-file",
            str(staged["id_set"]),
            "--add-referenced",
            "--output",
            str(staged["relation_closed_pbf"]),
        ]
        xml_command = [
            "osmium",
            "cat",
            str(staged["relation_closed_pbf"]),
            "-f",
            "osm",
            "--output",
            str(staged["relation_closed_xml"]),
        ]
        run_command(getid_command)
        run_command(xml_command)
        closed_scan = scan_closed(staged["relation_closed_pbf"], bbox_scan, config)
        governed = config["road_population"]["governed_highway_types"]
        baseline_candidates = candidate_ids(baseline_path, governed)
        current_candidates = closed_scan["candidate_ids"]

        roles = {
            "artifact_type": "relation_closure_element_roles",
            "schema_version": 1,
            "config_id": config["config_id"],
            "config_version": config["config_version"],
            "run_id": config["run_id"],
            "definitions": config["road_population"]["roles"],
            "ways": {
                "final_analysis_target": sorted(closed_scan["final_ids"]),
                "topology_support": sorted(closed_scan["topology_support_ids"]),
                "excluded": sorted(closed_scan["excluded_ids"]),
            },
            "supplemented_elements": {
                "nodes": {
                    "final_analysis_target": sorted(
                        set(closed_scan["supplemented"]["n"])
                        & closed_scan["final_node_ids"]
                    ),
                    "topology_support": sorted(
                        set(closed_scan["supplemented"]["n"])
                        & closed_scan["topology_support_node_ids"]
                    ),
                    "excluded": sorted(
                        set(closed_scan["supplemented"]["n"])
                        - closed_scan["final_node_ids"]
                        - closed_scan["topology_support_node_ids"]
                    ),
                },
                "ways": {
                    "final_analysis_target": sorted(
                        set(closed_scan["supplemented"]["w"])
                        & closed_scan["final_ids"]
                    ),
                    "topology_support": sorted(
                        set(closed_scan["supplemented"]["w"])
                        & closed_scan["topology_support_ids"]
                    ),
                    "excluded": sorted(
                        set(closed_scan["supplemented"]["w"])
                        - closed_scan["final_ids"]
                        - closed_scan["topology_support_ids"]
                    ),
                },
                "relation_ids": closed_scan["supplemented"]["r"],
            },
        }
        write_json(staged["element_roles"], roles)

        config_sha = sha256_file(config_path)
        output_hashes = {
            name: sha256_file(staged[name])
            for name in (
                "id_set",
                "relation_closed_pbf",
                "relation_closed_xml",
                "element_roles",
            )
        }
        verify_acceptance(config, bbox_scan, closed_scan, output_hashes)
        inputs = {
            "configuration": {"path": relative(config_path), "sha256": config_sha},
            "bbox_extract": config["inputs"]["bbox_extract"],
            "regional_authority": config["inputs"]["regional_authority"],
            "v15_baseline": config["inputs"]["v15_baseline"]["relation_closed_pbf"],
        }
        generated_outputs = {
            name: {"path": relative(output_paths[name]), "sha256": output_hashes[name]}
            for name in ("id_set", "relation_closed_pbf", "relation_closed_xml", "element_roles")
        }
        manifest = {
            "artifact_type": "relation_closure_manifest",
            "schema_version": 1,
            "config_id": config["config_id"],
            "config_version": config["config_version"],
            "run_id": config["run_id"],
            "status": "accepted",
            "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
            "tool_versions": {"osmium": config["tools"]["osmium_version"]},
            "inputs": inputs,
            "outputs": generated_outputs,
            "commands": [
                " ".join(getid_command).replace(str(stage), "<staging>"),
                " ".join(xml_command).replace(str(stage), "<staging>"),
            ],
            "relation_scope": {
                "retained_by_type": bbox_scan["retained_by_type"],
                "retained_by_category": bbox_scan["retained_by_category"],
                "retained_relation_ids_by_type": {
                    relation_type: sorted(
                        relation_id
                        for relation_id, selected_type in bbox_scan[
                            "retained_relations"
                        ].items()
                        if selected_type == relation_type
                    )
                    for relation_type in sorted(
                        config["relation_policy"]["retained"]
                    )
                },
                "rule_ids_by_type": {
                    relation_type: rule["rule_id"]
                    for relation_type, rule in sorted(
                        config["relation_policy"]["retained"].items()
                    )
                },
                "discarded_by_type": bbox_scan["discarded_by_type"],
                "required_relation_ids": sorted(
                    config["relation_policy"]["known_required_relation_ids"]
                ),
            },
            "element_counts": {
                "bbox": bbox_scan["counts"],
                "closed": closed_scan["counts"],
                "supplemented": {
                    "nodes": len(closed_scan["supplemented"]["n"]),
                    "ways": len(closed_scan["supplemented"]["w"]),
                    "relations": len(closed_scan["supplemented"]["r"]),
                },
            },
            "reference_validation": closed_scan["reference_validation"],
            "road_population": {
                "governed_candidate_ways": len(current_candidates),
                "final_analysis_target_ways": len(closed_scan["final_ids"]),
                "topology_support_ways": len(closed_scan["topology_support_ids"]),
                "excluded_ways": len(closed_scan["excluded_ids"]),
                "candidate_by_highway": closed_scan["candidate_by_highway"],
                "final_by_highway": closed_scan["final_by_highway"],
                "candidate_by_origin": closed_scan["candidate_by_origin"],
            },
            "v15_comparison": {
                "baseline_candidate_way_count": config["inputs"]["v15_baseline"][
                    "candidate_way_count"
                ],
                "added_candidate_way_ids": sorted(current_candidates - baseline_candidates),
                "removed_candidate_way_ids": sorted(baseline_candidates - current_candidates),
                "unchanged_candidate_way_count": len(
                    current_candidates & baseline_candidates
                ),
            },
        }
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=str)
        if errors:
            raise PrepareError(f"manifest schema validation failed: {errors[0].message}")
        write_json(staged["manifest"], manifest)

        for name, destination in output_paths.items():
            os.replace(staged[name], destination)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser(
        "prepare", help="build and validate the registered relation closure"
    )
    prepare_parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    prepare_parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = prepare(args.config.resolve(), overwrite=args.overwrite)
    except (OSError, PrepareError, ValueError) as exc:
        print(f"prepare failed: {exc}")
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
