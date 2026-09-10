#!/usr/bin/env python3
"""Reproduce marouter candidate-generation probes and audit route support.

The fixed-endpoint probe separates route legality from marouter's candidate
enumeration.  The support audit evaluates the six canonical Road Census
directions without using the observed traffic counts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from traffic_simulation.paths import REPOSITORY_ROOT


GENERATOR_VERSION = "1.0.0"


def local_name(tag: str) -> str:
    """Return an XML tag without its optional namespace."""

    return tag.rsplit("}", 1)[-1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_xml_sha256(path: Path) -> str:
    """Hash XML elements/attributes while excluding comments and formatting."""

    digest = hashlib.sha256()
    for event, element in ET.iterparse(path, events=("start", "end")):
        tag = local_name(element.tag)
        if event == "start":
            digest.update(b"S\0")
            digest.update(tag.encode("utf-8"))
            for key, value in sorted(element.attrib.items()):
                digest.update(b"\0A\0")
                digest.update(key.encode("utf-8"))
                digest.update(b"\0")
                digest.update(value.encode("utf-8"))
        else:
            text = (element.text or "").strip()
            if text:
                digest.update(b"\0T\0")
                digest.update(text.encode("utf-8"))
            digest.update(b"\0E\0")
            digest.update(tag.encode("utf-8"))
            element.clear()
    return digest.hexdigest()


def repository_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return resolved.name


def stable_command(command: list[str]) -> list[str]:
    """Remove host-specific repository prefixes from a recorded command."""

    stable: list[str] = []
    for value in command:
        candidate = Path(value)
        if candidate.is_absolute():
            stable.append(repository_relative(candidate))
        else:
            stable.append(value)
    return stable


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"configuration must be a JSON object: {path}")
    return value


def write_xml(path: Path, root: ET.Element) -> None:
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def first_route(path: Path) -> list[str]:
    for _, element in ET.iterparse(path, events=("end",)):
        if local_name(element.tag) == "route":
            return (element.get("edges") or "").split()
        element.clear()
    raise ValueError(f"no route in {path}")


def free_flow_seconds(network: Path, route_edges: Iterable[str]) -> float:
    """Compute sum(length / speed) for a route without loading the full net."""

    sequence = list(route_edges)
    wanted = set(sequence)
    edge_costs: dict[str, float] = {}
    for _, element in ET.iterparse(network, events=("end",)):
        if local_name(element.tag) != "edge":
            continue
        edge_id = element.get("id", "")
        if edge_id in wanted:
            lane = next(
                (child for child in element if local_name(child.tag) == "lane"),
                None,
            )
            if lane is None:
                raise ValueError(f"edge has no lane: {edge_id}")
            edge_costs[edge_id] = float(lane.get("length", "0")) / float(
                lane.get("speed", "0")
            )
        element.clear()
    missing = wanted - edge_costs.keys()
    if missing:
        raise ValueError(f"route edges missing from network: {sorted(missing)[:5]}")
    return sum(edge_costs[edge] for edge in sequence)


def summarize_fixed_routes(path: Path, target_edge: str) -> dict[str, Any]:
    routes: list[dict[str, Any]] = []
    for _, element in ET.iterparse(path, events=("end",)):
        if local_name(element.tag) == "route":
            edges = (element.get("edges") or "").split()
            routes.append(
                {
                    "cost": float(element.get("cost", "nan")),
                    "probability": float(element.get("probability", "1")),
                    "edge_count": len(edges),
                    "target_supported": target_edge in edges,
                }
            )
        element.clear()
    supported = [route for route in routes if route["target_supported"]]
    return {
        "route_count": len(routes),
        "target_route_count": len(supported),
        "target_supported": bool(supported),
        "minimum_cost_seconds": min(
            (route["cost"] for route in routes), default=None
        ),
        "best_target_cost_seconds": min(
            (route["cost"] for route in supported), default=None
        ),
        "target_probability": sum(route["probability"] for route in supported),
    }


def run_checked(command: list[str], stdout_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    with stdout_path.open("w", encoding="utf-8") as stdout:
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {' '.join(command)}"
        )
    return {
        "command": stable_command(command),
        "elapsed_seconds": elapsed,
        "exit_code": 0,
    }


def sumo_version(binary: Path) -> str:
    result = subprocess.run(
        [str(binary), "--version"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()[0]


def fixed_endpoint_probe(config_path: Path, output: Path) -> dict[str, Any]:
    config = read_json(config_path)
    output.mkdir(parents=True, exist_ok=True)

    network = REPOSITORY_ROOT / config["network"]
    marouter = REPOSITORY_ROOT / config["sumo"]["marouter"]
    duarouter = REPOSITORY_ROOT / config["sumo"]["duarouter"]
    probe = config["probe"]
    seed = int(config["sumo"]["seed"])

    for required in (network, marouter, duarouter):
        if not required.exists():
            raise FileNotFoundError(required)
    required_version = str(config["sumo"]["required_version"])
    for binary in (marouter, duarouter):
        if f"Version {required_version}" not in sumo_version(binary):
            raise RuntimeError(
                f"required SUMO {required_version}, found {sumo_version(binary)}"
            )

    ordinary_trip = output / "fixed_endpoint.trips.xml"
    forced_trip = output / "fixed_endpoint_forced_via.trips.xml"
    for path, use_via in ((ordinary_trip, False), (forced_trip, True)):
        root = ET.Element("routes")
        attributes = {
            "id": probe["id"] + ("_forced_via" if use_via else ""),
            "depart": "0",
            "from": probe["origin_edge"],
            "to": probe["destination_edge"],
        }
        if use_via:
            attributes["via"] = probe["target_edge"]
        ET.SubElement(root, "trip", attributes)
        write_xml(path, root)

    forced_routes = output / "forced_via.rou.xml"
    forced_log = output / "forced_via.execution.log"
    forced_execution = run_checked(
        [
            str(duarouter),
            "--net-file",
            str(network),
            "--route-files",
            str(forced_trip),
            "--output-file",
            str(forced_routes),
            "--seed",
            str(seed),
            "--ignore-errors",
            "false",
            "--no-step-log",
            "true",
        ],
        forced_log,
    )
    forced_edges = first_route(forced_routes)
    if probe["target_edge"] not in forced_edges:
        raise RuntimeError("duarouter forced-via route did not contain target edge")
    forced_cost = free_flow_seconds(network, forced_edges)

    rows: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    for index, case in enumerate(config["grid"], start=1):
        paths = int(case["paths"])
        penalty = float(case["paths_penalty"])
        max_alternatives = int(case.get("max_alternatives", paths))
        stem = f"case_{index:02d}_paths{paths}_penalty{penalty:g}_maxalt{max_alternatives}"
        route_output = output / f"{stem}.rou.xml"
        execution_log = output / f"{stem}.execution.log"
        command = [
            str(marouter),
            "--net-file",
            str(network),
            "--route-files",
            str(ordinary_trip),
            "--output-file",
            str(route_output),
            "--assignment-method",
            config["marouter"]["assignment_method"],
            "--paths",
            str(paths),
            "--paths.penalty",
            str(penalty),
            "--max-alternatives",
            str(max_alternatives),
            "--max-iterations",
            str(config["marouter"]["max_iterations"]),
            "--max-inner-iterations",
            str(config["marouter"]["max_inner_iterations"]),
            "--routing-threads",
            str(config["marouter"]["routing_threads"]),
            "--seed",
            str(seed),
            "--ignore-errors",
            "false",
            "--no-step-log",
            "true",
        ]
        execution = run_checked(command, execution_log)
        execution["case"] = stem
        executions.append(execution)
        summary = summarize_fixed_routes(route_output, probe["target_edge"])
        best_target = summary["best_target_cost_seconds"]
        rows.append(
            {
                "case": stem,
                "paths": paths,
                "paths_penalty_seconds": penalty,
                "max_alternatives": max_alternatives,
                **summary,
                "forced_via_free_flow_seconds": forced_cost,
                "best_target_vs_forced_ratio": (
                    best_target / forced_cost if best_target is not None else None
                ),
                "elapsed_seconds": execution["elapsed_seconds"],
                "route_output_sha256": sha256_file(route_output),
                "route_output_semantic_sha256": semantic_xml_sha256(route_output),
            }
        )

    summary_path = output / "fixed_endpoint_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "artifact_id": "MAROUTER_ROUTE2_DOWN_FIXED_ENDPOINT_DIAGNOSIS_V1",
        "generator_version": GENERATOR_VERSION,
        "config": repository_relative(config_path),
        "config_sha256": sha256_file(config_path),
        "network": repository_relative(network),
        "network_sha256": sha256_file(network),
        "sumo": {
            "marouter_version": sumo_version(marouter),
            "duarouter_version": sumo_version(duarouter),
            "seed": seed,
        },
        "probe": probe,
        "forced_via": {
            "legal": True,
            "free_flow_seconds": forced_cost,
            "edge_count": len(forced_edges),
            "route_sha256": sha256_file(forced_routes),
            "route_semantic_sha256": semantic_xml_sha256(forced_routes),
            "execution": forced_execution,
        },
        "cases": rows,
        "executions": executions,
        "interpretation": (
            "A missing or high-detour target route is a candidate-generation "
            "result; forced-via legality is established independently by duarouter."
        ),
    }
    manifest_path = output / "fixed_endpoint_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_canonical_locations(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {
        "official_observation_section_id",
        "direction",
        "representative_edge_id",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"invalid canonical count-location file: {path}")
    if len(rows) != 6:
        raise ValueError(f"expected six canonical directions, found {len(rows)}")
    return rows


def audit_route_support(
    route_path: Path, count_locations_path: Path
) -> list[dict[str, Any]]:
    locations = read_canonical_locations(count_locations_path)
    target_by_edge = {
        row["representative_edge_id"]: (
            row["official_observation_section_id"],
            row["direction"],
        )
        for row in locations
    }
    opposite: dict[str, str] = {}
    by_section: dict[str, dict[str, str]] = defaultdict(dict)
    for edge, (section, direction) in target_by_edge.items():
        by_section[section][direction] = edge
    for directions in by_section.values():
        if set(directions) == {"UP", "DOWN"}:
            opposite[directions["UP"]] = directions["DOWN"]
            opposite[directions["DOWN"]] = directions["UP"]

    stats: dict[str, dict[str, Any]] = {
        edge: {
            "route_count": 0,
            "od_pairs": set(),
            "assigned_route_weight": 0.0,
            "best_target_route_cost_seconds": math.inf,
            "best_target_detour_factor": math.inf,
            "routes_with_opposite_edge": 0,
            "opposite_edge_assigned_route_weight": 0.0,
            "routes_with_immediate_reversal": 0,
            "immediate_reversal_assigned_route_weight": 0.0,
            "clean_route_count": 0,
            "clean_assigned_route_weight": 0.0,
        }
        for edge in target_by_edge
    }
    current: dict[str, Any] | None = None
    for event, element in ET.iterparse(route_path, events=("start", "end")):
        tag = local_name(element.tag)
        if event == "start" and tag in {"flow", "vehicle"}:
            current = {
                "id": element.get("id", ""),
                "origin": element.get("fromTaz", element.get("from", "")),
                "destination": element.get("toTaz", element.get("to", "")),
                "routes": [],
            }
        elif event == "end" and tag == "route" and current is not None:
            edge_sequence = (element.get("edges") or "").split()
            current["routes"].append(
                {
                    "edges": set(edge_sequence),
                    "has_immediate_reversal": any(
                        first == (second[1:] if second.startswith("-") else "-" + second)
                        for first, second in zip(edge_sequence, edge_sequence[1:])
                    ),
                    "cost": float(element.get("cost", "nan")),
                    "weight": float(element.get("probability", "1")),
                }
            )
            element.clear()
        elif event == "end" and tag in {"flow", "vehicle"} and current is not None:
            finite_costs = [
                route["cost"]
                for route in current["routes"]
                if math.isfinite(route["cost"])
            ]
            shortest = min(finite_costs, default=math.nan)
            od_pair = (current["origin"], current["destination"])
            for route in current["routes"]:
                touched = route["edges"] & target_by_edge.keys()
                for edge in touched:
                    item = stats[edge]
                    item["route_count"] += 1
                    item["od_pairs"].add(od_pair)
                    item["assigned_route_weight"] += route["weight"]
                    if math.isfinite(route["cost"]):
                        item["best_target_route_cost_seconds"] = min(
                            item["best_target_route_cost_seconds"], route["cost"]
                        )
                        if shortest > 0:
                            item["best_target_detour_factor"] = min(
                                item["best_target_detour_factor"],
                                route["cost"] / shortest,
                            )
                    if opposite.get(edge) in route["edges"]:
                        item["routes_with_opposite_edge"] += 1
                        item["opposite_edge_assigned_route_weight"] += route["weight"]
                    if route["has_immediate_reversal"]:
                        item["routes_with_immediate_reversal"] += 1
                        item["immediate_reversal_assigned_route_weight"] += route[
                            "weight"
                        ]
                    if (
                        opposite.get(edge) not in route["edges"]
                        and not route["has_immediate_reversal"]
                    ):
                        item["clean_route_count"] += 1
                        item["clean_assigned_route_weight"] += route["weight"]
            current = None
            element.clear()

    output_rows: list[dict[str, Any]] = []
    for location in locations:
        edge = location["representative_edge_id"]
        item = stats[edge]
        route_count = item["route_count"]
        supported = route_count > 0
        clean_supported = item["clean_route_count"] > 0
        support_status = (
            "PRESENT_CLEAN"
            if clean_supported
            else "PATHOLOGICAL_ONLY"
            if supported
            else "ABSENT"
        )
        output_rows.append(
            {
                "official_observation_section_id": location[
                    "official_observation_section_id"
                ],
                "direction": location["direction"],
                "representative_edge_id": edge,
                "route_count": route_count,
                "od_pair_count": len(item["od_pairs"]),
                "assigned_route_weight": item["assigned_route_weight"],
                "best_target_route_cost_seconds": (
                    item["best_target_route_cost_seconds"] if supported else None
                ),
                "best_target_detour_factor": (
                    item["best_target_detour_factor"] if supported else None
                ),
                "routes_with_opposite_edge": item["routes_with_opposite_edge"],
                "opposite_edge_cooccurrence_fraction": (
                    item["routes_with_opposite_edge"] / route_count
                    if route_count
                    else None
                ),
                "opposite_edge_assigned_weight_fraction": (
                    item["opposite_edge_assigned_route_weight"]
                    / item["assigned_route_weight"]
                    if item["assigned_route_weight"]
                    else None
                ),
                "routes_with_immediate_reversal": item[
                    "routes_with_immediate_reversal"
                ],
                "immediate_reversal_fraction": (
                    item["routes_with_immediate_reversal"] / route_count
                    if route_count
                    else None
                ),
                "immediate_reversal_assigned_weight_fraction": (
                    item["immediate_reversal_assigned_route_weight"]
                    / item["assigned_route_weight"]
                    if item["assigned_route_weight"]
                    else None
                ),
                "clean_route_count": item["clean_route_count"],
                "clean_assigned_route_weight": item["clean_assigned_route_weight"],
                "route_support_status": support_status,
            }
        )
    return output_rows


def audit_demand_coverage(
    relations_path: Path, routes_path: Path
) -> dict[str, Any]:
    """Verify that every aggregate OD relation and its demand reach output."""

    input_by_pair: dict[tuple[str, str], float] = defaultdict(float)
    for _, element in ET.iterparse(relations_path, events=("end",)):
        if local_name(element.tag) == "tazRelation":
            pair = (element.get("from", ""), element.get("to", ""))
            input_by_pair[pair] += float(element.get("count", "0"))
        element.clear()

    output_by_pair: dict[tuple[str, str], float] = defaultdict(float)
    route_weight_by_pair: dict[tuple[str, str], float] = defaultdict(float)
    current_pair: tuple[str, str] | None = None
    for event, element in ET.iterparse(routes_path, events=("start", "end")):
        tag = local_name(element.tag)
        if event == "start" and tag == "flow":
            current_pair = (
                element.get("fromTaz", ""),
                element.get("toTaz", ""),
            )
            output_by_pair[current_pair] += float(element.get("number", "0"))
        elif event == "end" and tag == "route" and current_pair is not None:
            route_weight_by_pair[current_pair] += float(
                element.get("probability", "1")
            )
            element.clear()
        elif event == "end" and tag == "flow":
            current_pair = None
            element.clear()

    input_pairs = set(input_by_pair)
    output_pairs = set(output_by_pair)
    missing_pairs = sorted(input_pairs - output_pairs)
    unexpected_pairs = sorted(output_pairs - input_pairs)
    total_input = sum(input_by_pair.values())
    total_output = sum(output_by_pair.values())
    total_route_weight = sum(route_weight_by_pair.values())
    demand_tolerance = max(1e-6, total_input * 1e-9)
    route_weight_tolerance = max(1e-6, total_output * 1e-6)
    return {
        "input_od_relation_count": len(input_pairs),
        "output_od_flow_count": len(output_pairs),
        "missing_od_pairs": [list(pair) for pair in missing_pairs],
        "unexpected_od_pairs": [list(pair) for pair in unexpected_pairs],
        "input_demand": total_input,
        "output_flow_demand": total_output,
        "output_route_weight": total_route_weight,
        "all_od_relations_routed": not missing_pairs and not unexpected_pairs,
        "flow_demand_matches_input": abs(total_output - total_input)
        <= demand_tolerance,
        "route_weight_matches_output_flow": abs(total_route_weight - total_output)
        <= route_weight_tolerance,
    }


def write_support_audit(
    route_path: Path, count_locations_path: Path, output: Path
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    rows = audit_route_support(route_path, count_locations_path)
    csv_path = output / "canonical_direction_route_support.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "artifact_id": "CANONICAL_SIX_DIRECTION_ROUTE_SUPPORT_AUDIT_V1",
        "generator_version": GENERATOR_VERSION,
        "routes": repository_relative(route_path),
        "routes_sha256": sha256_file(route_path),
        "routes_semantic_sha256": semantic_xml_sha256(route_path),
        "canonical_count_locations": repository_relative(count_locations_path),
        "canonical_count_locations_sha256": sha256_file(count_locations_path),
        "all_six_directions_supported": all(
            row["route_support_status"] == "PRESENT_CLEAN" for row in rows
        ),
        "directions": rows,
        "guardrail": "No observed traffic count value is read by this audit.",
    }
    (output / "canonical_direction_route_support_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def experiment_case_command(
    config: dict[str, Any], case: dict[str, Any]
) -> tuple[list[str], dict[str, Path], Path]:
    """Build the executable marouter command from one experiment case."""

    inputs = {
        key: REPOSITORY_ROOT / value for key, value in config["inputs"].items()
    }
    output = REPOSITORY_ROOT / case["output"]
    common = config["common"]
    marouter = (
        REPOSITORY_ROOT
        / ".local"
        / f"sumo-{config['sumo_version']}"
        / "bin"
        / "marouter"
    )
    command = [
        str(marouter),
        "--net-file",
        str(inputs["network"]),
        "--additional-files",
        str(inputs["taz"]),
        "--tazrelation-files",
        str(inputs["assignment_relations"]),
        "--output-file",
        str(output / "routes.rou.xml"),
        "--netload-output",
        str(output / "netload.xml"),
        "--with-taz",
        str(common["with_taz"]).lower(),
        "--assignment-method",
        common["assignment_method"],
        "--route-choice-method",
        common["route_choice_method"],
        "--paths",
        str(case["paths"]),
        "--paths.penalty",
        str(case.get("paths_penalty", common["paths_penalty"])),
        "--max-alternatives",
        str(case["max_alternatives"]),
        "--max-iterations",
        str(case.get("max_iterations", common["max_iterations"])),
        "--max-inner-iterations",
        str(common["max_inner_iterations"]),
        "--routing-algorithm",
        common["routing_algorithm"],
        "--routing-threads",
        str(common["routing_threads"]),
    ]
    turnaround_penalty = case.get(
        "weights_turnaround_penalty",
        common.get("weights_turnaround_penalty"),
    )
    if turnaround_penalty is not None:
        command.extend(
            ["--weights.turnaround-penalty", str(turnaround_penalty)]
        )
    command.extend(
        [
            "--seed",
            str(config["seed"]),
            "--ignore-errors",
            "true",
            "--message-log",
            str(output / "marouter_messages.log"),
            "--error-log",
            str(output / "marouter_errors.log"),
        ]
    )
    return command, inputs, marouter


def run_experiment_case(
    experiment_config_path: Path, case_id: str
) -> dict[str, Any]:
    """Execute and audit one full-OD candidate-generation case."""

    config = read_json(experiment_config_path)
    cases = {case["case_id"]: case for case in config["cases"]}
    if case_id not in cases:
        raise ValueError(f"unknown case id {case_id}; expected one of {sorted(cases)}")
    case = cases[case_id]
    command, inputs, marouter = experiment_case_command(config, case)
    for required in (*inputs.values(), marouter):
        if not required.exists():
            raise FileNotFoundError(required)
    required_version = str(config["sumo_version"])
    if f"Version {required_version}" not in sumo_version(marouter):
        raise RuntimeError(
            f"required SUMO {required_version}, found {sumo_version(marouter)}"
        )

    output = REPOSITORY_ROOT / case["output"]
    output.mkdir(parents=True, exist_ok=True)
    execution = run_checked(command, output / "marouter_console.log")
    manifest = audit_experiment_case(experiment_config_path, case_id)
    manifest["execution"] = execution
    (output / "route_generation_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def audit_experiment_case(
    experiment_config_path: Path, case_id: str
) -> dict[str, Any]:
    config = read_json(experiment_config_path)
    cases = {case["case_id"]: case for case in config["cases"]}
    if case_id not in cases:
        raise ValueError(f"unknown case id {case_id}; expected one of {sorted(cases)}")
    case = cases[case_id]
    output = REPOSITORY_ROOT / case["output"]
    routes = output / "routes.rou.xml"
    netload = output / "netload.xml"
    message_log = output / "marouter_messages.log"
    error_log = output / "marouter_errors.log"
    for required in (routes, netload, message_log, error_log):
        if not required.exists():
            raise FileNotFoundError(required)

    command, inputs, marouter = experiment_case_command(config, case)
    support = write_support_audit(
        routes, inputs["canonical_count_locations"], output
    )
    demand_coverage = audit_demand_coverage(
        inputs["assignment_relations"], routes
    )
    rows = support["directions"]
    limits = config["acceptance"]
    immediate_max = max(
        (
            row["immediate_reversal_assigned_weight_fraction"] or 0.0
            for row in rows
        ),
        default=0.0,
    )
    opposite_max = max(
        (row["opposite_edge_assigned_weight_fraction"] or 0.0 for row in rows),
        default=0.0,
    )
    detour_values = [
        row["best_target_detour_factor"]
        for row in rows
        if row["best_target_detour_factor"] is not None
    ]
    detour_max = max(detour_values, default=None)
    checks = {
        "all_six_directions_have_clean_support": support[
            "all_six_directions_supported"
        ],
        "immediate_reversal_weight_within_limit": immediate_max
        <= limits["maximum_immediate_reversal_assigned_weight_fraction"],
        "opposite_edge_weight_within_limit": opposite_max
        <= limits["maximum_opposite_edge_assigned_weight_fraction"],
        "best_target_detour_within_limit": (
            len(detour_values) == len(rows)
            and detour_max is not None
            and detour_max <= limits["maximum_best_target_detour_factor"]
        ),
        "error_log_empty": error_log.stat().st_size == 0,
        "all_od_relations_routed": demand_coverage[
            "all_od_relations_routed"
        ],
        "flow_demand_matches_input": demand_coverage[
            "flow_demand_matches_input"
        ],
        "route_weight_matches_output_flow": demand_coverage[
            "route_weight_matches_output_flow"
        ],
    }
    manifest = {
        "artifact_id": "MAROUTER_ROUTE_GENERATION_CASE_AUDIT_V1",
        "generator_version": GENERATOR_VERSION,
        "case_id": case_id,
        "accepted": all(checks.values()),
        "experiment_config": repository_relative(experiment_config_path),
        "experiment_config_sha256": sha256_file(experiment_config_path),
        "sumo": {
            "version": sumo_version(marouter),
            "seed": config["seed"],
            "command": stable_command(command),
        },
        "input_sha256": {
            repository_relative(path): sha256_file(path)
            for path in inputs.values()
        },
        "output": {
            "routes": repository_relative(routes),
            "routes_sha256": sha256_file(routes),
            "routes_semantic_sha256": semantic_xml_sha256(routes),
            "netload": repository_relative(netload),
            "netload_sha256": sha256_file(netload),
            "netload_semantic_sha256": semantic_xml_sha256(netload),
            "message_log_sha256": sha256_file(message_log),
            "error_log_sha256": sha256_file(error_log),
        },
        "quality": {
            "checks": checks,
            "maximum_immediate_reversal_assigned_weight_fraction": immediate_max,
            "maximum_opposite_edge_assigned_weight_fraction": opposite_max,
            "maximum_best_target_detour_factor": detour_max,
            "demand_coverage": demand_coverage,
            "canonical_directions": rows,
        },
        "guardrail": "No observed traffic count value was read or optimized.",
    }
    (output / "route_generation_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    fixed = subparsers.add_parser("fixed-endpoint")
    fixed.add_argument("--config", type=Path, required=True)
    fixed.add_argument("--output", type=Path, required=True)

    support = subparsers.add_parser("support-audit")
    support.add_argument("--routes", type=Path, required=True)
    support.add_argument("--count-locations", type=Path, required=True)
    support.add_argument("--output", type=Path, required=True)

    case_audit = subparsers.add_parser("case-audit")
    case_audit.add_argument("--experiment-config", type=Path, required=True)
    case_audit.add_argument("--case-id", required=True)

    run_case = subparsers.add_parser("run-case")
    run_case.add_argument("--experiment-config", type=Path, required=True)
    run_case.add_argument("--case-id", required=True)

    args = parser.parse_args()
    if args.command == "fixed-endpoint":
        result = fixed_endpoint_probe(args.config, args.output)
    elif args.command == "support-audit":
        result = write_support_audit(args.routes, args.count_locations, args.output)
    elif args.command == "case-audit":
        result = audit_experiment_case(args.experiment_config, args.case_id)
    else:
        result = run_experiment_case(args.experiment_config, args.case_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
