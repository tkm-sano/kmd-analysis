#!/usr/bin/env python3
"""Independent validator for the R06 Baseline customer-demand artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("output", type=Path); args = ap.parse_args()
    output = args.output.resolve()
    manifest = json.loads((output / "r06_demand_manifest.json").read_text(encoding="utf-8"))
    data = rows(output / "customer_demand.csv")
    assert data
    ids = [r["stop_id"] for r in data]
    assert all(ids) and len(ids) == len(set(ids))
    assert all(r["customer_selected"] == "True" for r in data)
    assert all(math.isfinite(float(r["w_i"])) and float(r["w_i"]) >= 0 for r in data)
    assert all(math.isfinite(float(r["q_i"])) and float(r["q_i"]) >= 0 for r in data)
    assert all(r["q_i"] == "1" for r in data)
    assert sum(float(r["q_i"]) for r in data) == len(data)
    assert all(r["parcel_count"] == "" and r["delivery_count"] == "" and r["payload_quantity"] == "" for r in data)
    assert manifest["q_i"] == 1 and "not an observed" in manifest["q_i_interpretation"]
    assert "w_i" in data[0] and "q_i" in data[0] and data[0]["w_i"] != data[0]["q_i"]
    for name, record in manifest["inputs"].items():
        assert sha256(ROOT / record["path"]) == record["sha256"], name
    result = {
        "customer_count": len(data), "total_delivery_requests": sum(int(r["q_i"]) for r in data),
        "duplicate_customer_count": len(ids) - len(set(ids)), "all_customer_ids_present": True,
        "q_i_all_equal_one": True, "w_i_preserved_separately": True,
        "parcel_count_delivery_count_payload_quantity_separate_undefined": True,
        "input_hash_validation": "PASS",
    }
    (output / "r06_independent_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
