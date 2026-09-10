#!/usr/bin/env python3
"""Generate an EVRP customer set with successive PPS without replacement."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "reproducibility/config/traffic_simulation/evrp_r05_pps_sampling_v1.yml"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sample(rows: list[dict[str, str]], n: int, seed: int) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    if not 0 < n <= len(rows):
        raise ValueError(f"n must satisfy 0 < n <= population size ({len(rows)}): {n}")
    weights = [float(row["w_i"]) for row in rows]
    if any(not math.isfinite(w) or w < 0 for w in weights):
        raise ValueError("weights must be finite and non-negative")
    if sum(w > 0 for w in weights) < n:
        raise ValueError("positive-weight population is smaller than n")
    rng = random.Random(seed)
    remaining = list(range(len(rows)))
    selected: list[dict[str, str]] = []
    draws: list[dict[str, object]] = []
    for k in range(1, n + 1):
        total = math.fsum(weights[i] for i in remaining)
        if not math.isfinite(total) or total <= 0:
            raise ValueError(f"remaining weight total invalid at draw {k}: {total}")
        u = rng.random()
        threshold = u * total
        cumulative = 0.0
        chosen_position = None
        for pos, index in enumerate(remaining):
            cumulative += weights[index]
            if threshold < cumulative:
                chosen_position = pos
                break
        if chosen_position is None:  # protect the finite-sum roundoff endpoint
            chosen_position = len(remaining) - 1
        chosen_index = remaining.pop(chosen_position)
        selected.append(rows[chosen_index])
        chosen_weight = weights[chosen_index]
        draws.append({
            "draw": k,
            "candidate_order_index": chosen_index,
            "stop_id": rows[chosen_index]["stop_id"],
            "building_id": rows[chosen_index]["building_id"],
            "weight": chosen_weight,
            "remaining_population_before_draw": len(remaining) + 1,
            "remaining_weight_total_before_draw": total,
            "draw_probability": chosen_weight / total,
            "uniform_random": u,
        })
    return selected, draws


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--n", type=int, required=True, help="fixed sample size; not a fixed research scenario")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    population_path = (ROOT / config["inputs"]["candidate_population"]).resolve()
    candidate_path = (ROOT / config["inputs"]["weight_artifact"]).resolve()
    output = (ROOT / config["output_root"] / args.run_id).resolve()
    output.mkdir(parents=True, exist_ok=False)
    with candidate_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"stop_id", "building_id", "w_i"}
    if not rows or not required <= rows[0].keys():
        raise ValueError(f"weight artifact lacks required columns: {required}")
    ids = [row["stop_id"] for row in rows]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("candidate order contains missing or duplicate stop_id")
    with population_path.open(newline="", encoding="utf-8") as f:
        population_rows = list(csv.DictReader(f))
    if [r["stop_id"] for r in population_rows] != ids or [r["building_id"] for r in population_rows] != [r["building_id"] for r in rows]:
        raise ValueError("weight artifact order/IDs do not match candidate population")
    selected, draws = sample(rows, args.n, args.seed)

    with (output / "candidate_population_order.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_order_index", "stop_id", "building_id", "w_i"])
        for i, row in enumerate(rows):
            writer.writerow([i, row["stop_id"], row["building_id"], row["w_i"]])
    with (output / "sampling_draws.csv").open("w", newline="", encoding="utf-8") as f:
        fields = list(draws[0])
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(draws)
    with (output / "customer_ids.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f); writer.writerow(["sample_order", "stop_id", "building_id"])
        for k, row in enumerate(selected, 1):
            writer.writerow([k, row["stop_id"], row["building_id"]])
    metadata = {
        "schema_version": "evrp-r05-pps-sampling-v1",
        "run_id": args.run_id, "n": args.n, "seed": args.seed,
        "algorithm": "successive PPS without replacement",
        "probability_definition": "p_i^(k) = w_i / sum_{j in U_k} w_j",
        "probability_record": "draw_probability (conditional at draw k); first-order inclusion probability not calculated",
        "sampling_strata": False, "mesh_quota": False,
        "candidate_population_order": "weight artifact CSV row order; zero-based order index",
        "rng": {"implementation": "random.Random", "version": "Python " + __import__("sys").version.split()[0], "method": "MT19937-compatible Python random.Random"},
        "inputs": {
            "candidate_population": {"path": str(population_path.relative_to(ROOT)), "sha256": sha256(population_path)},
            "weight_artifact": {"path": str(candidate_path.relative_to(ROOT)), "sha256": sha256(candidate_path)},
        },
        "outputs": {}, "created_at": datetime.now(timezone.utc).isoformat(),
        "code": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha256(Path(__file__))},
        "config": {"path": str(config_path.relative_to(ROOT)), "sha256": sha256(config_path)},
    }
    for path in sorted(output.iterdir()):
        metadata["outputs"][path.name] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    (output / "sampling_manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": args.run_id, "n": args.n, "seed": args.seed, "output": str(output.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
