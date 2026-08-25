#!/usr/bin/env python3
"""Calibrate a fixed Tokyo-PT spatial prior with three temporal scale factors.

The program deliberately does not alter OD proportions, routes, the 27 fixed
measurement groups, or their 160 detector locations.  It never reads the 2024
independent-validation observation file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

from scipy.optimize import minimize_scalar


ALLOWED_CALIBRATION_SOURCES = {"mlit_r3_road_census_tokyo", "keishicho_2023"}
ALLOWED_CALIBRATION_YEARS = {"2021", "2023"}
BLOCKS = {
    "morning_07_10": range(7, 10),
    "daytime_10_16": range(10, 16),
    "evening_16_19": range(16, 19),
}
SCALE_BOUNDS = (0.20, 1.20)
LOG_OFFSET = 50.0
REGULARIZATION = 0.05


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def time_block(hour: int) -> str:
    for name, hours in BLOCKS.items():
        if hour in hours:
            return name
    raise ValueError(f"hour outside calibrated interval: {hour}")


def read_measurement_groups(groups_path: Path, lanes_path: Path) -> dict[str, set[str]]:
    with groups_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with lanes_path.open(encoding="utf-8-sig", newline="") as stream:
        lane_rows = list(csv.DictReader(stream))
    if len(rows) != 27 or len(lane_rows) != 160:
        raise ValueError(f"fixed measurement population changed: groups={len(rows)}, lanes={len(lane_rows)}")
    if any(row["status"] != "fixed" for row in rows):
        raise ValueError("every measurement group must remain fixed")
    groups = {
        row["measurement_group_id"]: set(filter(None, row["selected_edge_ids"].split(";")))
        for row in rows
    }
    if len(groups) != 27 or any(not edges for edges in groups.values()):
        raise ValueError("measurement group ids or selected edges are invalid")
    return groups


def read_targets(path: Path, groups_path: Path) -> dict[tuple[str, int], float]:
    with groups_path.open(encoding="utf-8-sig", newline="") as stream:
        group_rows = list(csv.DictReader(stream))
    mlit = {row["official_id"]: row["measurement_group_id"] for row in group_rows if row["source"] == "MLIT_R3"}
    police = {row["official_name"]: row["measurement_group_id"] for row in group_rows if row["source"] == "Keishicho"}
    targets: dict[tuple[str, int], float] = defaultdict(float)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        source = row["source"]
        year = row["survey_date"][:4]
        if source not in ALLOWED_CALIBRATION_SOURCES or year not in ALLOWED_CALIBRATION_YEARS:
            raise ValueError(f"independent or unknown observation entered calibration: {source}/{year}")
        if row["eligible"] != "true" or row["use_split"] != "calibration":
            raise ValueError("calibration file contains an ineligible or non-calibration row")
        hour = int(row["hour"])
        if hour not in range(7, 19):
            continue
        if source == "mlit_r3_road_census_tokyo":
            group_id = mlit[row["census_id"]]
            value = float(row["count"])
        else:
            group_id = police[row["site_name"]]
            value = float(row["four_wheel_count"]) + float(row["motorcycle_count"])
        targets[(group_id, hour)] += value
    expected = {(group_id, hour) for group_id in (set(mlit.values()) | set(police.values())) for hour in range(7, 19)}
    if set(targets) != expected:
        missing = sorted(expected - set(targets))
        raise ValueError(f"calibration target coverage is incomplete: {missing[:5]}")
    return dict(targets)


def read_route_counts(route_path: Path, groups: dict[str, set[str]]) -> dict[tuple[str, int], float]:
    edge_to_groups: dict[str, set[str]] = defaultdict(set)
    for group_id, edges in groups.items():
        for edge_id in edges:
            edge_to_groups[edge_id].add(group_id)
    counts: dict[tuple[str, int], float] = defaultdict(float)
    for _, element in ET.iterparse(route_path, events=("end",)):
        if element.tag not in {"flow", "vehicle"}:
            continue
        begin = float(element.get("begin", element.get("depart", "0")))
        hour = int(begin // 3600)
        if hour not in range(7, 19):
            element.clear()
            continue
        number = float(element.get("number", "1"))
        route = element.find("route")
        route_edges = (route.get("edges") if route is not None else element.get("route-edges", "")) or ""
        touched: set[str] = set()
        for edge_id in route_edges.split():
            touched.update(edge_to_groups.get(edge_id, set()))
        for group_id in touched:
            counts[(group_id, hour)] += number
        element.clear()
    return dict(counts)


def read_netload_counts(netload_path: Path, groups: dict[str, set[str]]) -> dict[tuple[str, int], float]:
    edge_to_groups: dict[str, set[str]] = defaultdict(set)
    for group_id, edges in groups.items():
        for edge_id in edges:
            edge_to_groups[edge_id].add(group_id)
    counts: dict[tuple[str, int], float] = defaultdict(float)
    hour: int | None = None
    for event, element in ET.iterparse(netload_path, events=("start", "end")):
        if event == "start" and element.tag == "interval":
            hour = int(float(element.get("begin", "0")) // 3600)
        elif event == "end" and element.tag == "edge" and hour in range(7, 19):
            for group_id in edge_to_groups.get(element.get("id", ""), set()):
                counts[(group_id, hour)] += float(element.get("entered", "0"))
            element.clear()
        elif event == "end" and element.tag == "interval":
            hour = None
            element.clear()
    return dict(counts)


def objective(scale: float, pairs: list[tuple[float, float]]) -> float:
    residual = sum(
        math.log((scale * modeled + LOG_OFFSET) / (observed + LOG_OFFSET)) ** 2
        for modeled, observed in pairs
    ) / len(pairs)
    return residual + REGULARIZATION * math.log(scale) ** 2


def fit_scales(
    modeled: dict[tuple[str, int], float], targets: dict[tuple[str, int], float]
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    scales: dict[str, float] = {}
    trace: list[dict[str, Any]] = []
    for block in BLOCKS:
        pairs = [
            (modeled.get(key, 0.0), observed)
            for key, observed in targets.items()
            if time_block(key[1]) == block
        ]
        result = minimize_scalar(
            lambda value: objective(value, pairs), bounds=SCALE_BOUNDS, method="bounded",
            options={"xatol": 0.001, "maxiter": 64},
        )
        scales[block] = float(result.x)
        trace.append({
            "block": block, "scale": float(result.x), "objective": float(result.fun),
            "evaluations": int(result.nfev), "success": bool(result.success),
        })
    return scales, trace


def metrics(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    observed = [row["observed"] for row in rows]
    modeled = [row[key] for row in rows]
    errors = [model - obs for model, obs in zip(modeled, observed)]
    geh = [math.sqrt(2 * error * error / (model + obs)) if model + obs > 0 else 0.0 for model, obs, error in zip(modeled, observed, errors)]
    return {
        "rmse": math.sqrt(sum(value * value for value in errors) / len(errors)),
        "wmape": sum(abs(value) for value in errors) / sum(observed),
        "mean_geh": sum(geh) / len(geh),
        "geh_below_5_fraction": sum(value < 5 for value in geh) / len(geh),
        "zero_modeled_target_rows": float(sum(model == 0 and obs > 0 for model, obs in zip(modeled, observed))),
    }


def write_calibrated_relations(source: Path, destination: Path, scales: dict[str, float]) -> int:
    tree = ET.parse(source)
    total = 0.0
    for interval in tree.getroot().iter("interval"):
        hour = int(float(interval.get("begin", "0")) // 3600)
        for relation in interval.findall("tazRelation"):
            count = float(relation.get("count", "0")) * scales[time_block(hour)]
            relation.set("count", f"{count:.6f}")
            total += count
    ET.indent(tree.getroot())
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return round(total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--lanes", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--assignment-netload", type=Path, required=True)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    groups = read_measurement_groups(args.groups, args.lanes)
    targets = read_targets(args.observations, args.groups)
    modeled = read_netload_counts(args.assignment_netload, groups)
    scales, trace = fit_scales(modeled, targets)
    rows = []
    for (group_id, hour), observed in sorted(targets.items()):
        initial = modeled.get((group_id, hour), 0.0)
        rows.append({
            "measurement_group_id": group_id, "hour": hour, "block": time_block(hour),
            "observed": observed, "initial_assigned": initial,
            "calibrated_assigned": initial * scales[time_block(hour)],
        })
    calibrated_total = write_calibrated_relations(
        args.relations, args.output / "calibrated_general_traffic.taz_relations.xml", scales
    )
    fieldnames = list(rows[0])
    with (args.output / "calibration_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with args.groups.open(encoding="utf-8-sig", newline="") as stream:
        group_metadata = {row["measurement_group_id"]: row for row in csv.DictReader(stream)}
    support_rows = []
    for group_id in sorted(group_metadata):
        group_values = [row for row in rows if row["measurement_group_id"] == group_id]
        metadata = group_metadata[group_id]
        support_rows.append({
            "measurement_group_id": group_id,
            "source": metadata["source"],
            "official_id": metadata["official_id"],
            "official_name": metadata["official_name"],
            "selected_edge_ids": metadata["selected_edge_ids"],
            "observed_07_19_total": sum(row["observed"] for row in group_values),
            "initial_assigned_07_19_total": sum(row["initial_assigned"] for row in group_values),
            "hours_with_positive_assignment": sum(row["initial_assigned"] > 0 for row in group_values),
            "spatial_support": "present" if any(row["initial_assigned"] > 0 for row in group_values) else "absent",
        })
    with (args.output / "measurement_group_spatial_support.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(support_rows[0]))
        writer.writeheader()
        writer.writerows(support_rows)
    initial_metrics = metrics(rows, "initial_assigned")
    calibrated_metrics = metrics(rows, "calibrated_assigned")
    unsupported_groups = sorted({
        row["measurement_group_id"] for row in rows if row["observed"] > 0 and row["initial_assigned"] == 0
    })
    scale_at_bound = any(
        value <= SCALE_BOUNDS[0] + 0.001 or value >= SCALE_BOUNDS[1] - 0.001
        for value in scales.values()
    )
    assignment_ready = (
        not unsupported_groups
        and not scale_at_bound
        and all(item["success"] for item in trace)
        and calibrated_metrics["wmape"] < initial_metrics["wmape"]
    )
    manifest = {
        "artifact_id": "OTA_GENERAL_TRAFFIC_CALIBRATION_V1",
        "research_stage": "2-3",
        "status": (
            "assigned_count_calibrated_pending_microsimulation_check" if assignment_ready
            else "not_accepted_spatial_support_or_parameter_bound_failure"
        ),
        "fixed": {
            "network": "v17 accepted SUMO network", "measurement_groups": 27,
            "detector_locations": 160, "od_spatial_proportions": "Tokyo PT 2018",
            "hourly_profiles": "Tokyo PT 2018",
            "assignment": "SUMO marouter incremental, five iterations", "seed": 230823,
        },
        "adjusted": {"parameters": list(BLOCKS), "count": 3, "bounds": list(SCALE_BOUNDS)},
        "objective": {
            "formula": "mean(log((scale*assigned+50)/(observed+50))^2)+0.05*log(scale)^2",
            "weighting": "each measurement-group hour receives equal weight",
        },
        "stopping": {
            "maximum_objective_evaluations_per_parameter": 64,
            "absolute_parameter_tolerance": 0.001,
            "bounded_optimizer_success_required": True,
        },
        "scales": scales, "optimization_trace": trace,
        "metrics": {"initial": initial_metrics, "calibrated": calibrated_metrics},
        "assignment_acceptance": {
            "accepted": assignment_ready,
            "requirements": {
                "all_measurement_groups_have_modeled_support": not unsupported_groups,
                "no_scale_at_bound": not scale_at_bound,
                "optimizer_success": all(item["success"] for item in trace),
                "wmape_improves": calibrated_metrics["wmape"] < initial_metrics["wmape"],
            },
            "unsupported_measurement_groups": unsupported_groups,
            "stopping_reason": (
                "structural_zero_counts_and_upper_bound_reached; do not add detector-specific OD freedoms"
                if not assignment_ready else "ready_for_dynamic_microsimulation_check"
            ),
        },
        "calibrated_vehicle_departures": calibrated_total,
        "input_sha256": {
            "groups": sha256(args.groups), "lanes": sha256(args.lanes),
            "calibration_observations_2021_2023_only": sha256(args.observations),
            "initial_assignment_netload": sha256(args.assignment_netload),
            "unscaled_relations": sha256(args.relations),
        },
        "independent_2024_policy": "not_read_not_used_reserved_for_stage_2_4",
        "interpretation": "scale factors convert automobile person-trip prior into model-assumed vehicle demand",
    }
    (args.output / "calibration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
