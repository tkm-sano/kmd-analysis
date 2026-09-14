#!/usr/bin/env python3
"""Build the R24 demand/capacity authority review without scientific execution."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1"
STOP = DATA / "building_delivery_stops_scoped.csv"
EXPECTED = DATA / "household_daily_expected_demand.csv"
ASSIGN = DATA / "household_building_assignment_scoped.csv"
PROFILE = ROOT / "reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml"
BASELINE = ROOT / "reproducibility/config/traffic_simulation/baseline_demand.yml"
STOP_SUMMARY = DATA / "stop_generation_run_summary.json"
PIPELINE_SUMMARY = DATA / "pipeline_run_summary.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qtile(values: list[float], p: float) -> float:
    x = sorted(values)
    pos = (len(x) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return x[lo] if lo == hi else x[lo] + (x[hi] - x[lo]) * (pos - lo)


def main() -> None:
    expected = {}
    with EXPECTED.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            expected[row["household_id"]] = float(row["expected_parcel_equivalent_per_day"])

    by_building = defaultdict(float)
    with ASSIGN.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["mapping_status"] in {"matched", "matched_cross_boundary"} and row["building_id"]:
                by_building[row["building_id"]] += expected[row["household_id"]]

    stops = []
    with STOP.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            stops.append({
                "stop_id": row["stop_id"],
                "building_id": row["building_id"],
                "chocho_code": row["chocho_code"],
                "parcel_equivalent_observed_day": int(row["parcel_equivalent"]),
                "parcel_equivalent_per_day_expected": by_building[row["building_id"]],
                "evaluation_date": row["evaluation_date"],
            })

    vals = [r["parcel_equivalent_per_day_expected"] for r in stops]
    expected_total = sum(vals)
    observed_total = sum(r["parcel_equivalent_observed_day"] for r in stops)
    stats = {
        "n_customers": len(stops),
        "expected_parcel_equivalent_per_customer_day": {
            "min": min(vals), "p01": qtile(vals, .01), "p05": qtile(vals, .05),
            "p25": qtile(vals, .25), "median": qtile(vals, .50), "mean": statistics.mean(vals),
            "p75": qtile(vals, .75), "p90": qtile(vals, .90), "p95": qtile(vals, .95),
            "p99": qtile(vals, .99), "max": max(vals), "sd_population": statistics.pstdev(vals),
            "zero_count": sum(v == 0 for v in vals),
        },
        "expected_total_parcel_equivalent_per_day": expected_total,
        "realized_current_stop_proxy_total_parcel_equivalent_on_2026_01_01": observed_total,
        "q_kg_per_vehicle": 2000,
        "total_kg_per_day": None,
        "capacity_only_theoretical_lower_bound_fleet_size": None,
        "capacity_pressure": None,
        "capacity_calculation_status": "BLOCKED_BY_STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT",
    }

    with (OUT / "customer_demand_kg.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["stop_id", "building_id", "chocho_code", "parcel_equivalent_per_day_expected",
                  "q_kg_customer_day", "q_kg_status", "Q_kg", "evaluation_date"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in stops:
            w.writerow({"stop_id": r["stop_id"], "building_id": r["building_id"],
                        "chocho_code": r["chocho_code"],
                        "parcel_equivalent_per_day_expected": r["parcel_equivalent_per_day_expected"],
                        "q_kg_customer_day": "", "q_kg_status": "BLOCKED_NO_AUTHORIZED_PARCEL_WEIGHT",
                        "Q_kg": 2000, "evaluation_date": r["evaluation_date"]})

    with (OUT / "ota_capacity_summary.json").open("w", encoding="utf-8") as f:
        json.dump({"schema_version": "r24-demand-capacity-summary-v1", "status": "BLOCKED",
                   "population": "39,956 scoped unique building stops", "statistics": stats,
                   "capacity_authority": {"profile_id": "managed_urban_ev_delivery_v1",
                                          "Q_kg": 2000,
                                          "basis": "fixed research vehicle profile; not observed commercial payload"},
                   "not_computed": ["customer kg/day", "Ota total kg/day", "m_min_capacity", "rho"]}, f,
                  ensure_ascii=False, indent=2)

    with (OUT / "stratum_capacity_summary.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["stratum_id", "stratum_status", "customer_count", "expected_parcel_equivalent_per_day",
                  "kg_per_day", "capacity_only_lower_bound", "depot_travel_time_status",
                  "reason"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        w.writerow({"stratum_id": "ALL_OTA", "stratum_status": "population_only_no_frozen_r24_strata",
                    "customer_count": len(stops), "expected_parcel_equivalent_per_day": expected_total,
                    "kg_per_day": "", "capacity_only_lower_bound": "",
                    "depot_travel_time_status": "not_available_in_current_customer_artifact",
                    "reason": "weight authority and CVRP-specific OD/reachability are not frozen"})

    source_paths = [STOP, EXPECTED, ASSIGN, STOP_SUMMARY, PIPELINE_SUMMARY, BASELINE, PROFILE]
    provenance = {"build_script": str(Path(__file__).relative_to(ROOT)),
                  "command": "python3 reproducibility/outputs/traffic_simulation/r24_demand_capacity_authority/20260914_v1/build_authority_artifact.py",
                  "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in source_paths},
                  "population_count": len(stops), "expected_parcel_total": expected_total,
                  "realized_parcel_total": observed_total, "random_sampling_used": False,
                  "scientific_execution": False}
    (OUT / "PROVENANCE.md").write_text("# Provenance\n\n" + json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
