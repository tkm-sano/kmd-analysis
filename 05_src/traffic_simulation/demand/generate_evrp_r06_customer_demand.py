#!/usr/bin/env python3
"""Attach Baseline delivery requests to the R05 customer sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "reproducibility/config/traffic_simulation/evrp_r06_customer_demand_v1.yml"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    r05_ids_path = (ROOT / config["inputs"]["r05_customer_ids"]).resolve()
    r05_manifest_path = (ROOT / config["inputs"]["r05_manifest"]).resolve()
    weight_path = (ROOT / config["inputs"]["r04_weight_artifact"]).resolve()
    output = (ROOT / config["output_root"] / args.run_id).resolve()
    output.mkdir(parents=True, exist_ok=False)

    selected = read_csv(r05_ids_path)
    weights = read_csv(weight_path)
    if not selected or not weights:
        raise ValueError("R05 customer IDs and R04 weights must be non-empty")
    required_selected = {"sample_order", "stop_id", "building_id"}
    required_weight = {"stop_id", "building_id", "w_i"}
    if not required_selected <= selected[0].keys() or not required_weight <= weights[0].keys():
        raise ValueError("required input columns are missing")
    weight_by_id = {r["stop_id"]: r for r in weights}
    if len(weight_by_id) != len(weights):
        raise ValueError("R04 weight artifact contains duplicate stop_id")
    ids = [r["stop_id"] for r in selected]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("R05 customer IDs contain missing or duplicate stop_id")
    rows: list[dict[str, object]] = []
    for order, customer in enumerate(selected, 1):
        if customer["stop_id"] not in weight_by_id:
            raise ValueError(f"customer missing from R04 weight artifact: {customer['stop_id']}")
        weight = weight_by_id[customer["stop_id"]]
        if customer["building_id"] != weight["building_id"]:
            raise ValueError(f"building_id mismatch: {customer['stop_id']}")
        w = float(weight["w_i"])
        if not math.isfinite(w) or w < 0:
            raise ValueError(f"invalid w_i: {customer['stop_id']}")
        rows.append({
            "customer_order": order,
            "sample_order": customer["sample_order"],
            "stop_id": customer["stop_id"],
            "building_id": customer["building_id"],
            "customer_selected": True,
            "w_i": weight["w_i"],
            "w_i_unit": weight.get("weight_unit", "household_equivalents_per_candidate"),
            "w_i_source": weight.get("source", "R04 weight artifact"),
            "w_i_classification": weight.get("classification_w_i", "COMPUTED"),
            "q_i": 1,
            "q_i_unit": "delivery_requests_per_customer",
            "q_i_classification": "ASSUMED",
            "q_i_source": "EVRP Baseline model convention",
            "q_i_transformation": "q_i = 1 for every R05-selected customer",
            "q_i_assumption_reason": "Model convention to make customer count equal delivery-request count; not an empirical parcel observation",
            "parcel_count": "",
            "parcel_count_status": "not_defined",
            "delivery_count": "",
            "delivery_count_status": "not_defined",
            "payload_quantity": "",
            "payload_quantity_status": "not_defined",
        })
    fields = list(rows[0])
    with (output / "customer_demand.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    validation = {
        "customer_count": len(rows), "total_delivery_requests": sum(int(r["q_i"]) for r in rows),
        "q_i_all_equal_one": all(r["q_i"] == 1 for r in rows),
        "customer_selected_all_true": all(r["customer_selected"] is True for r in rows),
        "w_i_preserved_separately": True, "parcel_count_defined": False,
        "delivery_count_defined": False, "payload_quantity_defined": False,
        "model_convention": "q_i = 1; one customer equals one delivery request",
    }
    (output / "r06_demand_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "evrp-r06-customer-demand-v1", "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(), "q_i": 1,
        "q_i_interpretation": "Baseline model convention, not an observed delivery count",
        "inputs": {
            "r05_customer_ids": {"path": str(r05_ids_path.relative_to(ROOT)), "sha256": sha256(r05_ids_path)},
            "r05_manifest": {"path": str(r05_manifest_path.relative_to(ROOT)), "sha256": sha256(r05_manifest_path)},
            "r04_weight_artifact": {"path": str(weight_path.relative_to(ROOT)), "sha256": sha256(weight_path)},
        },
        "source": "R05 customer selection plus R04 sampling weight artifact",
        "classification": "ASSUMED for q_i; COMPUTED/derived w_i retained from R04",
        "unit": "q_i: delivery_requests_per_customer; parcel_count/delivery_count/payload_quantity: not_defined",
        "transformation": "left-preserving join by stop_id in R05 sample order; q_i=1 for each selected customer",
        "assumption_reason": "Baseline model convention to align customer and delivery-request counts",
        "code": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha256(Path(__file__))},
        "config": {"path": str(config_path.relative_to(ROOT)), "sha256": sha256(config_path)},
        "validation": validation, "outputs": {},
    }
    for path in sorted(output.iterdir()):
        if path.name != "r06_demand_manifest.json":
            manifest["outputs"][path.name] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    (output / "r06_demand_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": args.run_id, "customer_count": len(rows), "output": str(output.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
