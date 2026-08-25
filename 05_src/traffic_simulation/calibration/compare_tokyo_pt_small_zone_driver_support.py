#!/usr/bin/env python3
"""Compare coarse-prior and small-zone driver-OD spatial support."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from diagnose_ota_initial_demand_spatial_support import read_route_edge_support


def amount(edges: list[str], support: dict[str, dict[str, float]]) -> float:
    return sum(support.get(edge, {}).get("assigned_amount", 0.0) for edge in edges)


def compare(
    groups_path: Path,
    prior_comparison_path: Path,
    prior_baseline_route: Path,
    prior_best_route: Path,
    incremental_route: Path,
    stochastic_route: Path,
) -> list[dict[str, object]]:
    with groups_path.open(encoding="utf-8-sig", newline="") as stream:
        groups = list(csv.DictReader(stream))
    with prior_comparison_path.open(encoding="utf-8", newline="") as stream:
        prior_rows = list(csv.DictReader(stream))
    target = {
        row["measurement_group_id"] for row in prior_rows
        if row["cause_classification"] == "coarse_od_or_route_cost_corridor_choice_unresolved"
    }
    if len(target) != 5:
        raise ValueError(f"fixed unresolved population changed: {len(target)}")
    supports = {
        "prior_baseline": read_route_edge_support(prior_baseline_route),
        "prior_best": read_route_edge_support(prior_best_route),
        "small_zone_incremental": read_route_edge_support(incremental_route),
        "small_zone_stochastic": read_route_edge_support(stochastic_route),
    }
    rows: list[dict[str, object]] = []
    for group in groups:
        edges = group["selected_edge_ids"].split(";")
        values = {name: amount(edges, support) for name, support in supports.items()}
        prior_supported = values["prior_baseline"] > 0 or values["prior_best"] > 0
        incremental_supported = values["small_zone_incremental"] > 0
        stochastic_supported = values["small_zone_stochastic"] > 0
        rows.append({
            "measurement_group_id": group["measurement_group_id"],
            "official_name": group["official_name"],
            "selected_edge_ids": group["selected_edge_ids"],
            "fixed_unresolved_target": group["measurement_group_id"] in target,
            **{f"{name}_assigned_amount": value for name, value in values.items()},
            "prior_supported": prior_supported,
            "incremental_supported": incremental_supported,
            "stochastic_supported": stochastic_supported,
            "supported_in_both_small_zone_scenarios": incremental_supported and stochastic_supported,
            "scenario_disagreement": incremental_supported != stochastic_supported,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--prior-comparison", type=Path, required=True)
    parser.add_argument("--prior-baseline-route", type=Path, required=True)
    parser.add_argument("--prior-best-route", type=Path, required=True)
    parser.add_argument("--incremental-route", type=Path, required=True)
    parser.add_argument("--stochastic-route", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = compare(
        args.groups, args.prior_comparison, args.prior_baseline_route, args.prior_best_route,
        args.incremental_route, args.stochastic_route,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "small_zone_support_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    target_rows = [row for row in rows if row["fixed_unresolved_target"]]
    summary = {
        "research_stage": "2-3-B",
        "measurement_group_count": len(rows),
        "fixed_unresolved_target_count": len(target_rows),
        "observed_traffic_values_used": False,
        "target_support": {
            "incremental": sum(bool(row["incremental_supported"]) for row in target_rows),
            "stochastic": sum(bool(row["stochastic_supported"]) for row in target_rows),
            "both": sum(bool(row["supported_in_both_small_zone_scenarios"]) for row in target_rows),
        },
        "all_group_support": {
            "incremental": sum(bool(row["incremental_supported"]) for row in rows),
            "stochastic": sum(bool(row["stochastic_supported"]) for row in rows),
            "both": sum(bool(row["supported_in_both_small_zone_scenarios"]) for row in rows),
        },
        "scenario_disagreement_ids": [
            row["measurement_group_id"] for row in rows if row["scenario_disagreement"]
        ],
        "target_unresolved_under_stochastic": [
            row["measurement_group_id"] for row in target_rows if not row["stochastic_supported"]
        ],
        "numeric_calibration_run": False,
    }
    (args.output / "small_zone_support_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
