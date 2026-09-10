#!/usr/bin/env python3
"""Independent validator for an R05 successive-PPS run plus small fixtures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_run(output: Path) -> dict[str, object]:
    manifest = json.loads((output / "sampling_manifest.json").read_text(encoding="utf-8"))
    population = read_csv(output / "candidate_population_order.csv")
    draws = read_csv(output / "sampling_draws.csv")
    customers = read_csv(output / "customer_ids.csv")
    n = int(manifest["n"])
    ids = [r["stop_id"] for r in population]
    selected = [r["stop_id"] for r in customers]
    assert len(ids) == len(set(ids)) and all(ids)
    assert len(customers) == n == len(draws)
    assert len(selected) == len(set(selected))
    assert set(selected) <= set(ids)
    assert manifest["sampling_strata"] is False and manifest["mesh_quota"] is False
    assert "inclusion_probability" not in manifest["probability_record"]
    row_by_id = {r["stop_id"]: r for r in population}
    remaining = set(ids)
    for k, draw in enumerate(draws, 1):
        assert int(draw["draw"]) == k
        sid = draw["stop_id"]
        assert sid in remaining and sid == selected[k - 1]
        weights = [float(row_by_id[x]["w_i"]) for x in remaining]
        assert all(math.isfinite(w) and w >= 0 for w in weights)
        total = math.fsum(weights)
        assert total > 0
        expected = float(row_by_id[sid]["w_i"]) / total
        assert math.isclose(float(draw["draw_probability"]), expected, rel_tol=1e-12, abs_tol=1e-15)
        assert math.isclose(math.fsum(w / total for w in weights), 1.0, rel_tol=0, abs_tol=1e-12)
        assert float(row_by_id[sid]["w_i"]) > 0
        remaining.remove(sid)
    return {"population_count": len(population), "n": n, "duplicate_count": len(selected) - len(set(selected)), "draw_probability_checks": len(draws), "sampling_strata": False, "mesh_quota": False}


def fixture_check() -> dict[str, object]:
    rows = [{"stop_id": f"f{i}", "building_id": f"b{i}", "w_i": str(i + 1)} for i in range(6)]
    def run(seed):
        rng = random.Random(seed); remaining = list(rows); out = []
        for _ in range(3):
            total = math.fsum(float(x["w_i"]) for x in remaining); u = rng.random() * total; c = 0.0
            for pos, row in enumerate(remaining):
                c += float(row["w_i"])
                if u < c: out.append(row["stop_id"]); remaining.pop(pos); break
        return out
    a, b, c = run(17), run(17), run(18)
    assert a == b and a != c
    return {"same_seed_identical": True, "different_seed_changed": True, "fixture_n": 3}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("output", type=Path); args = parser.parse_args()
    result = validate_run(args.output.resolve()); result["fixture"] = fixture_check()
    (args.output / "r05_sampling_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
