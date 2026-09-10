#!/usr/bin/env python3
"""Calibrate the accepted small-zone driver OD with minimal global freedom."""

from __future__ import annotations

import argparse
import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from scipy.optimize import minimize_scalar

import calibrate_ota_general_traffic as base


SOURCE_START_HOUR = 7
SCALE_BOUNDS = (0.5, 1.5)
REGULARIZATION = 0.05
LOG_OFFSET = 50.0
LEVEL2_MIN_WAPE_POINT_IMPROVEMENT = 0.03
LEVEL2_MIN_OBJECTIVE_IMPROVEMENT = 0.10
ACCEPTANCE_WAPE = 0.40
ACCEPTANCE_BLOCK_BIAS = 0.20


def source_hour(simulation_seconds: float) -> int:
    return SOURCE_START_HOUR + int(simulation_seconds // 3600)


def read_relative_netload(
    path: Path, groups: dict[str, set[str]]
) -> dict[tuple[str, int], float]:
    edge_to_groups: dict[str, set[str]] = {}
    for group_id, edges in groups.items():
        for edge in edges:
            edge_to_groups.setdefault(edge, set()).add(group_id)
    counts: dict[tuple[str, int], float] = {}
    hour: int | None = None
    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start" and element.tag == "interval":
            hour = source_hour(float(element.get("begin", "0")))
        elif event == "end" and element.tag == "edge" and hour in range(7, 19):
            for group_id in edge_to_groups.get(element.get("id", ""), set()):
                key = (group_id, hour)
                counts[key] = counts.get(key, 0.0) + float(element.get("entered", "0"))
            element.clear()
        elif event == "end" and element.tag == "interval":
            hour = None
            element.clear()
    return counts


def read_assigned_route_counts(
    route_path: Path, relations_path: Path, groups: dict[str, set[str]]
) -> tuple[dict[tuple[str, int], float], dict[str, int]]:
    """Apply one static OD route distribution to the fixed hourly OD profile."""
    hourly_od: dict[tuple[int, str, str], float] = {}
    root = ET.parse(relations_path).getroot()
    for interval in root.iter("interval"):
        hour = source_hour(float(interval.get("begin", "0")))
        for relation in interval.findall("tazRelation"):
            hourly_od[(hour, relation.get("from", ""), relation.get("to", ""))] = float(
                relation.get("count", "0")
            )

    edge_to_groups: dict[str, set[str]] = {}
    for group_id, edges in groups.items():
        for edge in edges:
            edge_to_groups.setdefault(edge, set()).add(group_id)
    shares: dict[tuple[str, str], dict[str, float]] = {}
    for _, flow in ET.iterparse(route_path, events=("end",)):
        if flow.tag != "flow":
            continue
        od = (flow.get("fromTaz", ""), flow.get("toTaz", ""))
        distribution = flow.find("routeDistribution")
        routes = distribution.findall("route") if distribution is not None else flow.findall("route")
        weights = [float(route.get("probability", "1")) for route in routes]
        total_weight = sum(weights)
        group_weights: dict[str, float] = {}
        for route, weight in zip(routes, weights):
            touched: set[str] = set()
            for edge in (route.get("edges") or "").split():
                touched.update(edge_to_groups.get(edge, set()))
            for group_id in touched:
                group_weights[group_id] = group_weights.get(group_id, 0.0) + weight
        shares[od] = {
            group_id: weight / total_weight for group_id, weight in group_weights.items()
        } if total_weight > 0 else {}
        flow.clear()

    counts: dict[tuple[str, int], float] = {}
    missing = 0
    for (hour, origin, destination), count in hourly_od.items():
        od_shares = shares.get((origin, destination))
        if od_shares is None:
            missing += 1
            continue
        for group_id, share in od_shares.items():
            key = (group_id, hour)
            counts[key] = counts.get(key, 0.0) + count * share
    return counts, {
        "hourly_od_relations": len(hourly_od), "assigned_od_pairs": len(shares),
        "hourly_relations_without_assigned_route": missing,
    }


def scalar_objective(scale: float, pairs: list[tuple[float, float]]) -> float:
    data = sum(
        math.log((scale * modeled + LOG_OFFSET) / (observed + LOG_OFFSET)) ** 2
        for modeled, observed in pairs
    ) / len(pairs)
    return data + REGULARIZATION * math.log(scale) ** 2


def fit_global(
    modeled: dict[tuple[str, int], float], targets: dict[tuple[str, int], float]
) -> tuple[float, dict[str, Any]]:
    pairs = [(modeled.get(key, 0.0), observed) for key, observed in targets.items()]
    result = minimize_scalar(
        lambda value: scalar_objective(value, pairs), bounds=SCALE_BOUNDS,
        method="bounded", options={"xatol": 0.001, "maxiter": 64},
    )
    return float(result.x), {
        "scale": float(result.x), "objective": float(result.fun),
        "evaluations": int(result.nfev), "success": bool(result.success),
    }


def fit_blocks(
    modeled: dict[tuple[str, int], float], targets: dict[tuple[str, int], float]
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    scales: dict[str, float] = {}
    trace: list[dict[str, Any]] = []
    for block in base.BLOCKS:
        pairs = [
            (modeled.get(key, 0.0), observed) for key, observed in targets.items()
            if base.time_block(key[1]) == block
        ]
        result = minimize_scalar(
            lambda value: scalar_objective(value, pairs), bounds=SCALE_BOUNDS,
            method="bounded", options={"xatol": 0.001, "maxiter": 64},
        )
        scales[block] = float(result.x)
        trace.append({
            "block": block, "scale": float(result.x), "objective": float(result.fun),
            "evaluations": int(result.nfev), "success": bool(result.success),
        })
    return scales, trace


def rows_for(
    targets: dict[tuple[str, int], float], modeled: dict[tuple[str, int], float],
    global_scale: float, block_scales: dict[str, float],
) -> list[dict[str, Any]]:
    rows = []
    for (group, hour), observed in sorted(targets.items()):
        initial = modeled.get((group, hour), 0.0)
        level1 = initial * global_scale
        level2 = initial * block_scales[base.time_block(hour)]
        rows.append({
            "measurement_group_id": group, "hour": hour,
            "block": base.time_block(hour), "observed": observed,
            "initial_assigned": initial, "level1_global": level1, "level2_time_block": level2,
            "initial_absolute_error": abs(initial - observed),
            "initial_relative_error": (initial - observed) / observed,
            "level1_absolute_error": abs(level1 - observed),
            "level1_relative_error": (level1 - observed) / observed,
            "level2_absolute_error": abs(level2 - observed),
            "level2_relative_error": (level2 - observed) / observed,
        })
    return rows


def total_objective(rows: list[dict[str, Any]], key: str, scales: list[float]) -> float:
    data = sum(
        math.log((row[key] + LOG_OFFSET) / (row["observed"] + LOG_OFFSET)) ** 2
        for row in rows
    ) / len(rows)
    return data + REGULARIZATION * sum(math.log(value) ** 2 for value in scales) / len(scales)


def block_bias(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    result = {}
    for block in base.BLOCKS:
        selected = [row for row in rows if row["block"] == block]
        observed = sum(row["observed"] for row in selected)
        result[block] = sum(row[key] for row in selected) / observed - 1.0
    return result


def scale_relations(source: Path, destination: Path, scales: dict[str, float]) -> float:
    tree = ET.parse(source)
    total = 0.0
    for interval in tree.getroot().iter("interval"):
        hour = source_hour(float(interval.get("begin", "0")))
        scale = scales[base.time_block(hour)]
        for relation in interval.findall("tazRelation"):
            count = float(relation.get("count", "0")) * scale
            relation.set("count", f"{count:.9f}")
            total += count
    ET.indent(tree.getroot())
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--lanes", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    assignment = parser.add_mutually_exclusive_group(required=True)
    assignment.add_argument("--assignment-netload", type=Path)
    assignment.add_argument("--assignment-routes", type=Path)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--assignment-label", choices=("SUE", "incremental"), default="SUE")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    groups = base.read_measurement_groups(args.groups, args.lanes)
    targets = base.read_targets(args.observations, args.groups)
    if args.assignment_routes:
        modeled, assignment_accounting = read_assigned_route_counts(
            args.assignment_routes, args.relations, groups
        )
        assignment_input = args.assignment_routes
    else:
        modeled = read_relative_netload(args.assignment_netload, groups)
        assignment_accounting = {"mode": "hourly_netload"}
        assignment_input = args.assignment_netload
    global_scale, global_trace = fit_global(modeled, targets)
    block_scales, block_trace = fit_blocks(modeled, targets)
    rows = rows_for(targets, modeled, global_scale, block_scales)

    metrics = {key: base.metrics(rows, key) for key in (
        "initial_assigned", "level1_global", "level2_time_block"
    )}
    objectives = {
        "level1_global": total_objective(rows, "level1_global", [global_scale]),
        "level2_time_block": total_objective(
            rows, "level2_time_block", list(block_scales.values())
        ),
    }
    biases = {
        "level1_global": block_bias(rows, "level1_global"),
        "level2_time_block": block_bias(rows, "level2_time_block"),
    }
    level2_wape_gain = metrics["level1_global"]["wmape"] - metrics["level2_time_block"]["wmape"]
    level2_objective_gain = 1 - objectives["level2_time_block"] / objectives["level1_global"]
    level2_needed = (
        metrics["level1_global"]["wmape"] > ACCEPTANCE_WAPE
        or max(abs(value) for value in biases["level1_global"].values()) > ACCEPTANCE_BLOCK_BIAS
    )
    level2_justified = (
        level2_needed and level2_wape_gain >= LEVEL2_MIN_WAPE_POINT_IMPROVEMENT
        and level2_objective_gain >= LEVEL2_MIN_OBJECTIVE_IMPROVEMENT
    )
    selected_level = "level2_time_block" if level2_justified else "level1_global"
    selected_scales = block_scales if level2_justified else {block: global_scale for block in base.BLOCKS}
    selected_values = list(selected_scales.values())
    at_bound = any(value <= 0.501 or value >= 1.499 for value in selected_values)
    accepted = (
        metrics[selected_level]["wmape"] <= ACCEPTANCE_WAPE
        and metrics[selected_level]["zero_modeled_target_rows"] == 0
        and max(abs(value) for value in biases[selected_level].values()) <= ACCEPTANCE_BLOCK_BIAS
        and not at_bound
    )

    with (args.output / "observed_vs_assigned.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    group_rows = []
    for group_id in sorted(groups):
        selected = [row for row in rows if row["measurement_group_id"] == group_id]
        group_rows.append({
            "measurement_group_id": group_id,
            "observed_total": sum(row["observed"] for row in selected),
            "initial_total": sum(row["initial_assigned"] for row in selected),
            "level1_total": sum(row["level1_global"] for row in selected),
            "positive_initial_hours": sum(row["initial_assigned"] > 0 for row in selected),
            "spatial_support": "present" if any(row["initial_assigned"] > 0 for row in selected) else "absent",
        })
    with (args.output / "measurement_group_support.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(group_rows[0]))
        writer.writeheader(); writer.writerows(group_rows)
    calibrated_total = scale_relations(
        args.relations, args.output / "selected_calibrated_small_zone_driver.taz_relations.xml",
        selected_scales,
    )
    manifest = {
        "artifact_id": "OTA_SMALL_ZONE_DRIVER_TRAFFIC_CALIBRATION_V1",
        "research_stage": "2-3", "accepted": accepted,
        "fixed_population": {
            "measurement_groups": 27, "detector_locations": 160,
            "groups_sha256": base.sha256(args.groups), "lanes_sha256": base.sha256(args.lanes),
        },
        "assignment": {
            "role": "primary" if args.assignment_label == "SUE" else "sensitivity",
            "method_name": args.assignment_label, "seed": 230823, "simulation_second_0": "07:00",
            "method": "one static OD route distribution applied to the official hourly prior",
            "accounting": assignment_accounting,
        },
        "levels": {
            "level1_global": global_trace, "level2_time_block": block_trace,
            "level2_needed": level2_needed, "level2_justified": level2_justified,
            "selected": selected_level,
        },
        "bounds": list(SCALE_BOUNDS), "selected_scales": selected_scales,
        "objective": {
            "formula": "equal-weight mean squared log ratio with offset 50 + 0.05 log-scale regularization",
            "values": objectives, "level2_relative_improvement": level2_objective_gain,
        },
        "metrics": metrics, "time_block_signed_bias": biases,
        "level2_wape_point_improvement": level2_wape_gain,
        "acceptance": {
            "wape_at_most": ACCEPTANCE_WAPE, "absolute_block_bias_at_most": ACCEPTANCE_BLOCK_BIAS,
            "zero_rows_required": True, "parameter_not_at_bound_required": True,
        },
        "pt_prior_deviation": {
            "original_total": sum(float(item.get("count", "0")) for item in ET.parse(args.relations).getroot().iter("tazRelation")),
            "selected_total": calibrated_total,
            "spatial_od_shares_changed": False,
        },
        "input_sha256": {
            "observations_2021_2023_only": base.sha256(args.observations),
            "assignment_output": base.sha256(assignment_input),
            "relations": base.sha256(args.relations),
        },
        "independent_2024_policy": "not_read_not_used_reserved_for_stage_2_4",
        "interpretation": "calibrated analytical demand, not the true OD",
    }
    (args.output / "calibration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
