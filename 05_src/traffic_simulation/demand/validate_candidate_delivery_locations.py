#!/usr/bin/env python3
"""Create an auditable, per-candidate road connection table for R03.

This command does not regenerate or modify the candidate population.  It joins
the fixed candidate CSV to the fixed accepted SUMO network using the existing
deterministic edge-midpoint rule and writes a new, run-scoped evidence packet.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import sumolib


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CANDIDATES = ROOT / (
    "03_data/processed/traffic_simulation/demand/household_parcel_v1/"
    "pipelines_v1/building_delivery_stops_scoped.csv"
)
DEFAULT_NETWORK = ROOT / (
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260903_three_tier_completion/run_2/three_tier.net.xml"
)
DEFAULT_OUTPUT = ROOT / (
    "reproducibility/outputs/traffic_simulation/demand/"
    "candidate_validation/20260909_r03_edge_mapping"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def point(value: str) -> tuple[float, float]:
    match = re.fullmatch(r"POINT \(([-+0-9.eE]+) ([-+0-9.eE]+)\)", value.strip())
    if not match:
        raise ValueError(f"invalid WKT point: {value!r}")
    lon, lat = map(float, match.groups())
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError(f"out-of-range coordinate: {lon}, {lat}")
    return lon, lat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--network", type=Path, default=DEFAULT_NETWORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    for path in (args.candidates, args.network):
        if not path.is_file():
            raise FileNotFoundError(path)

    args.output.mkdir(parents=True, exist_ok=False)
    network = sumolib.net.readNet(str(args.network))
    edges = [edge for edge in network.getEdges() if edge.allows("delivery")]
    if not edges:
        raise RuntimeError("accepted network has no delivery-permitted edges")
    midpoints = np.asarray(
        [edge.getShape()[len(edge.getShape()) // 2] for edge in edges], dtype=float
    )
    tree = cKDTree(midpoints)

    with args.candidates.open(newline="", encoding="utf-8") as stream:
        candidates = list(csv.DictReader(stream))
    required = {"stop_id", "building_id", "building_representative_point"}
    missing = required - set(candidates[0] if candidates else ())
    if missing:
        raise ValueError(f"candidate columns missing: {sorted(missing)}")
    if len(candidates) != 39956:
        raise ValueError(f"candidate count is {len(candidates)}, expected 39956")
    ids = [row["stop_id"] for row in candidates]
    if len(set(ids)) != len(ids) or any(not value for value in ids):
        raise ValueError("candidate stop IDs are not unique and non-empty")

    output_csv = args.output / "candidate_delivery_edge_connections.csv"
    fields = [
        "stop_id", "building_id", "longitude", "latitude", "sumo_edge_id",
        "edge_from_node", "edge_to_node", "edge_length_m", "nearest_edge_distance_m",
        "delivery_permitted", "mapping_rule",
    ]
    max_distance = 0.0
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in candidates:
            lon, lat = point(row["building_representative_point"])
            x, y = network.convertLonLat2XY(lon, lat)
            distance, index = tree.query((x, y))
            edge = edges[int(index)]
            max_distance = max(max_distance, float(distance))
            writer.writerow({
                "stop_id": row["stop_id"],
                "building_id": row["building_id"],
                "longitude": f"{lon:.15g}",
                "latitude": f"{lat:.15g}",
                "sumo_edge_id": edge.getID(),
                "edge_from_node": edge.getFromNode().getID(),
                "edge_to_node": edge.getToNode().getID(),
                "edge_length_m": f"{edge.getLength():.9g}",
                "nearest_edge_distance_m": f"{float(distance):.9g}",
                "delivery_permitted": "true",
                "mapping_rule": "nearest_delivery_permitted_edge_midpoint",
            })

    manifest = {
        "schema_version": "evrp-r03-candidate-edge-connection-v1",
        "run_id": "20260909_r03_edge_mapping",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "mapped_count": len(candidates),
        "unmapped_count": 0,
        "delivery_permitted_count": len(candidates),
        "max_nearest_edge_distance_m": max_distance,
        "mapping_rule": "nearest_delivery_permitted_edge_midpoint",
        "candidate_population": {
            "path": str(args.candidates.relative_to(ROOT)),
            "sha256": sha256(args.candidates),
        },
        "accepted_network": {
            "path": str(args.network.relative_to(ROOT)),
            "sha256": sha256(args.network),
            "sumo_version": "1.24.0",
        },
        "output": {
            "path": str(output_csv.relative_to(ROOT)),
            "sha256": sha256(output_csv),
        },
        "candidate_generation": {
            "status": "not_regenerated",
            "reason": "This command validates the fixed candidate population and does not claim to be its production generator.",
        },
    }
    (args.output / "candidate_validation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
