#!/usr/bin/env python3
"""Compare observation-independent route-support experiments for stage 2-3-A."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from diagnose_ota_initial_demand_spatial_support import read_route_edge_support


EXPERIMENTS = (
    "baseline",
    "e1_original_8sector_paths5_maxalt5",
    "e2_original_8sector_paths20_maxalt5",
    "e3_stratified_8sector_paths20_maxalt5",
    "e4_original_8sector_paths20_maxalt20",
    "e5_stratified_8sector_paths20_maxalt20",
    "e6_original_16sector_paths20_maxalt20",
    "e7_stratified_16sector_paths20_maxalt20",
)


def compare(groups_path: Path, route_paths: dict[str, Path]) -> list[dict[str, object]]:
    with groups_path.open(encoding="utf-8", newline="") as stream:
        groups = list(csv.DictReader(stream))
    support = {name: read_route_edge_support(path) for name, path in route_paths.items()}
    rows: list[dict[str, object]] = []
    for group in groups:
        edges = group["selected_edge_ids"].split(";")
        row: dict[str, object] = {
            "measurement_group_id": group["measurement_group_id"],
            "official_name": group["official_name"],
            "selected_edge_ids": group["selected_edge_ids"],
        }
        for name in EXPERIMENTS:
            row[name] = sum(support[name].get(edge, {}).get("route_count", 0) for edge in edges)
            row[f"{name}_assigned_amount"] = sum(
                support[name].get(edge, {}).get("assigned_amount", 0) for edge in edges
            )
        if row["e4_original_8sector_paths20_maxalt20_assigned_amount"]:
            cause = "route_alternative_pruning"
        elif row["e5_stratified_8sector_paths20_maxalt20_assigned_amount"]:
            cause = "coarse_taz_connector_sampling"
        elif (row["e6_original_16sector_paths20_maxalt20_assigned_amount"]
              or row["e7_stratified_16sector_paths20_maxalt20_assigned_amount"]):
            cause = "external_sector_aggregation"
        else:
            cause = "coarse_od_or_route_cost_corridor_choice_unresolved"
        row["cause_classification"] = cause
        row["recovered_after_general_improvement"] = bool(
            row["e7_stratified_16sector_paths20_maxalt20_assigned_amount"]
        )
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--experiments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    route_paths = {
        "baseline": args.baseline,
        "e1_original_8sector_paths5_maxalt5": args.experiments / "e1_original_taz_paths5.rou.xml",
        "e2_original_8sector_paths20_maxalt5": args.experiments / "e2_original_taz_paths20.rou.xml",
        "e3_stratified_8sector_paths20_maxalt5": args.experiments / "e3_stratified_taz_paths20.rou.xml",
        "e4_original_8sector_paths20_maxalt20": args.experiments / "e4_original_taz_paths20_maxalt20.rou.xml",
        "e5_stratified_8sector_paths20_maxalt20": args.experiments / "e5_stratified_taz_paths20_maxalt20.rou.xml",
        "e6_original_16sector_paths20_maxalt20": args.experiments / "e6_16sector_original_paths20_maxalt20.rou.xml",
        "e7_stratified_16sector_paths20_maxalt20": args.experiments / "e7_16sector_stratified_paths20_maxalt20.rou.xml",
    }
    missing = [str(path) for path in route_paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)
    rows = compare(args.groups, route_paths)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "experiment_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "research_stage": "2-3-A",
        "fixed_population": len(rows),
        "observed_traffic_values_used": False,
        "recovered_by_experiment": {
            name: sum(bool(row[f"{name}_assigned_amount"]) for row in rows) for name in EXPERIMENTS
        },
        "cause_counts": {
            cause: sum(row["cause_classification"] == cause for row in rows)
            for cause in sorted({str(row["cause_classification"]) for row in rows})
        },
        "final_recovered": sum(bool(row["recovered_after_general_improvement"]) for row in rows),
    }
    summary["final_unresolved"] = len(rows) - summary["final_recovered"]
    (args.output / "experiment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
