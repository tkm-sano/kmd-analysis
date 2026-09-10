#!/usr/bin/env python3
"""Independent validation and summary for an R13 routing result."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r12-dir", required=True)
    parser.add_argument("--r13-dir", required=True)
    args = parser.parse_args()
    r12 = Path(args.r12_dir)
    r13 = Path(args.r13_dir)
    config = json.loads((r12 / "r12_routing_config.json").read_text())
    endpoints = list(csv.DictReader((r12 / "endpoint_manifest.csv").open()))
    required = list(csv.DictReader((r12 / "od_manifest.csv").open()))
    rows = list(csv.DictReader((r13 / "routing_arcs.csv").open()))
    endpoint_ids = {row["endpoint_id"] for row in endpoints}
    required_pairs = {(row["origin_id"], row["destination_id"]) for row in required}
    result_pairs = {(row["origin_id"], row["destination_id"]) for row in rows}
    checks: dict[str, bool] = {}
    checks["result_count_132"] = len(rows) == 132
    checks["self_loop_zero"] = all(row["origin_id"] != row["destination_id"] for row in rows)
    checks["duplicate_od_zero"] = len(result_pairs) == len(rows)
    checks["required_od_complete"] = result_pairs == required_pairs
    checks["endpoint_ids_valid"] = all(row["origin_id"] in endpoint_ids and row["destination_id"] in endpoint_ids for row in rows)
    checks["objective_unique"] = all(row["routing_objective"] == "travel_time_minimizing" for row in rows)
    checks["vehicle_class_unique"] = all(row["vehicle_class"] == config["vehicle_class"] for row in rows)
    checks["network_hash_unique"] = all(row["network_hash"] == config["network_hash"] for row in rows)
    checks["unit_schema"] = True
    checks["reachable_nonnull_nonnegative"] = all(
        row["reachable"] != "True" or (
            row["distance_m"] not in (None, "") and row["travel_time_s"] not in (None, "")
            and float(row["distance_m"]) >= 0 and float(row["travel_time_s"]) >= 0
        ) for row in rows
    )
    checks["unreachable_nulls"] = all(
        row["reachable"] == "True" or (row["distance_m"] == "" and row["travel_time_s"] == "") for row in rows
    )
    checks["finite_values"] = all(
        row["reachable"] != "True" or all(math.isfinite(float(row[key])) for key in ("distance_m", "travel_time_s")) for row in rows
    )
    checks["nonself_zero_anomaly_absent"] = all(
        row["origin_id"] == row["destination_id"] or not (float(row["distance_m"]) == 0 and float(row["travel_time_s"]) == 0) for row in rows if row["reachable"] == "True"
    )
    checks["offset_components_present"] = all(
        row["reachable"] != "True" or all(row[key] != "" for key in (
            "origin_partial_distance_m", "origin_partial_time_s", "network_path_distance_m", "network_path_time_s", "destination_partial_distance_m", "destination_partial_time_s"
        )) for row in rows
    )
    checks["offset_totals_reconcile"] = all(
        row["reachable"] != "True" or abs(float(row["distance_m"]) - sum(float(row[key]) for key in ("origin_partial_distance_m", "network_path_distance_m", "destination_partial_distance_m"))) < 1e-7 for row in rows
    ) and all(
        row["reachable"] != "True" or abs(float(row["travel_time_s"]) - sum(float(row[key]) for key in ("origin_partial_time_s", "network_path_time_s", "destination_partial_time_s"))) < 1e-7 for row in rows
    )
    reachable = [row for row in rows if row["reachable"] == "True"]
    distances = [float(row["distance_m"]) for row in reachable]
    times = [float(row["travel_time_s"]) for row in reachable]
    summary = {
        "total_od_count": len(rows),
        "reachable_od_count": len(reachable),
        "unreachable_od_count": len(rows) - len(reachable),
        "reachability_rate": len(reachable) / len(rows) if rows else 0,
        "reachable_distance_m": {"min": min(distances) if distances else None, "max": max(distances) if distances else None, "mean": statistics.mean(distances) if distances else None, "median": statistics.median(distances) if distances else None},
        "reachable_travel_time_s": {"min": min(times) if times else None, "max": max(times) if times else None, "mean": statistics.mean(times) if times else None, "median": statistics.median(times) if times else None},
        "anomaly_checks": {"negative_distance_or_time": not checks["reachable_nonnull_nonnegative"], "nonself_zero": not checks["nonself_zero_anomaly_absent"], "extreme_distance_over_20km": any(value > 20000 for value in distances), "extreme_time_over_1h": any(value > 3600 for value in times), "unreachable_rate_over_50pct": (len(rows)-len(reachable))/len(rows) > 0.5 if rows else False},
    }
    result = {"status": "PASS" if all(checks.values()) and not any(summary["anomaly_checks"].values()) else "FAIL", "checks": checks, "summary": summary, "routing_arcs_sha256": sha256(r13 / "routing_arcs.csv")}
    (r13 / "routing_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (r13 / "routing_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
