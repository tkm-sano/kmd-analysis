#!/usr/bin/env python3
"""R13 execution-completeness checks; independent R14 geometry checks are excluded."""
from __future__ import annotations

import argparse, csv, hashlib, json, math, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUMO_TOOLS = ROOT / ".local" / "sumo-1.24.0" / "share" / "sumo" / "tools"
sys.path.insert(0, str(SUMO_TOOLS))
import sumolib  # type: ignore

REQUIRED = [
    "origin_id", "destination_id", "origin_type", "destination_type",
    "origin_edge", "destination_edge", "origin_offset_m", "destination_offset_m",
    "reachable", "distance_m", "travel_time_s", "path_edge_sequence",
    "path_reference", "routing_objective", "vehicle_class", "network_hash",
    "run_config_version", "status", "origin_partial_distance_m",
    "origin_partial_time_s", "network_path_distance_m", "network_path_time_s",
    "destination_partial_distance_m", "destination_partial_time_s",
]

def sha256(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def read(p: Path):
    with p.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--r12-dir", required=True); ap.add_argument("--r13-dir", required=True)
    a = ap.parse_args(); r12, r13 = Path(a.r12_dir), Path(a.r13_dir)
    cfg = json.loads((r12 / "r12_routing_config.json").read_text())
    endpoints, ods, rows = read(r12/"endpoint_manifest.csv"), read(r12/"od_manifest.csv"), read(r13/"routing_arcs.csv")
    ep = {x["endpoint_id"]: x for x in endpoints}; required_pairs = {(x["origin_id"], x["destination_id"]) for x in ods}; result_pairs = {(x["origin_id"], x["destination_id"]) for x in rows}
    net = sumolib.net.readNet(str(ROOT / cfg["network_path"])); edge_ids = {e.getID(): e for e in net.getEdges()}
    checks = {
        "endpoint_count_12": len(endpoints) == 12 and len(ep) == 12,
        "role_counts": {k: sum(x["endpoint_type"] == k for x in endpoints) for k in ("depot", "customer", "charger")} == {"depot": 1, "customer": 10, "charger": 1},
        "od_count_132": len(rows) == 132,
        "self_loop_zero": all(x["origin_id"] != x["destination_id"] for x in rows),
        "duplicate_od_zero": len(result_pairs) == len(rows),
        "required_od_exact": result_pairs == required_pairs,
        "schema_exact": rows and list(rows[0]) == REQUIRED,
        "network_hash_exact": all(x["network_hash"] == cfg["network_hash"] for x in rows),
        "objective_exact": all(x["routing_objective"] == cfg["routing_objective"] for x in rows),
        "vehicle_class_exact": all(x["vehicle_class"] == cfg["vehicle_class"] for x in rows),
    }
    status_counts = {}
    reachable = []
    path_edge_failures = []
    value_failures = []
    for x in rows:
        status_counts[x["status"]] = status_counts.get(x["status"], 0) + 1
        if x["reachable"] == "True":
            try:
                d, t = float(x["distance_m"]), float(x["travel_time_s"])
                if not (math.isfinite(d) and math.isfinite(t) and d >= 0 and t >= 0): raise ValueError
                reachable.append((d, t))
                path = json.loads(x["path_edge_sequence"])
                if not path or any(e not in edge_ids for e in path): path_edge_failures.append([x["origin_id"], x["destination_id"]])
                if any("delivery" not in (edge_ids[e].getPermissions() or []) for e in path): path_edge_failures.append([x["origin_id"], x["destination_id"], "permission"])
            except (TypeError, ValueError, json.JSONDecodeError): value_failures.append([x["origin_id"], x["destination_id"]])
        else:
            if x["distance_m"] != "" or x["travel_time_s"] != "": value_failures.append([x["origin_id"], x["destination_id"], "unreachable_nonnull"])
    checks["reachable_basic_values"] = not value_failures
    checks["path_edges_exist_and_permitted"] = not path_edge_failures
    checks["execution_statuses_valid"] = all(s in {"OK", "LEGITIMATE_UNREACHABLE"} for s in status_counts)
    ds, ts = [x[0] for x in reachable], [x[1] for x in reachable]
    summary = {"total_od_count": len(rows), "reachable_od_count": len(reachable), "unreachable_od_count": len(rows)-len(reachable), "reachability_rate": len(reachable)/len(rows) if rows else 0, "distance_m": {"min": min(ds) if ds else None, "max": max(ds) if ds else None, "mean": statistics.mean(ds) if ds else None, "median": statistics.median(ds) if ds else None}, "travel_time_s": {"min": min(ts) if ts else None, "max": max(ts) if ts else None, "mean": statistics.mean(ts) if ts else None, "median": statistics.median(ts) if ts else None}, "status_counts": status_counts, "routing_exceptions": sum(v for k,v in status_counts.items() if k not in {"OK", "LEGITIMATE_UNREACHABLE"})}
    result = {"status": "PASS" if all(v is True for v in checks.values()) else "FAIL", "checks": checks, "value_failures": value_failures, "path_edge_failures": path_edge_failures, "summary": summary, "input_hashes": {"endpoint_manifest": sha256(r12/"endpoint_manifest.csv"), "od_manifest": sha256(r12/"od_manifest.csv"), "config": sha256(r12/"r12_routing_config.json"), "network": cfg["network_hash"]}, "routing_arcs_sha256": sha256(r13/"routing_arcs.csv")}
    (r13/"r13_basic_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    (r13/"r13_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__": raise SystemExit(main())
