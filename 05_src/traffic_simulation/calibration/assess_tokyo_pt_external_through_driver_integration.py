#!/usr/bin/env python3
"""Assess route completeness and location support without observation values."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from diagnose_ota_initial_demand_spatial_support import read_route_edge_support
from prepare_tokyo_pt_external_through_driver_od import read_relation_file


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def route_population(path: Path) -> set[tuple[str, str]]:
    result = set()
    for _, flow in ET.iterparse(path, events=("end",)):
        if flow.tag != "flow":
            continue
        routes = flow.findall("route")
        distribution = flow.find("routeDistribution")
        if distribution is not None:
            routes = distribution.findall("route")
        if any((route.get("edges") or "").strip() for route in routes):
            result.add((flow.get("fromTaz", ""), flow.get("toTaz", "")))
        flow.clear()
    return result


def measurement_group_support(
    groups_path: Path, edge_support: dict[str, dict[str, float]]
) -> list[dict[str, Any]]:
    rows = []
    with groups_path.open(encoding="utf-8-sig", newline="") as stream:
        for group in csv.DictReader(stream):
            edges = group["selected_edge_ids"].split(";")
            amount = sum(edge_support.get(edge, {}).get("assigned_amount", 0.0) for edge in edges)
            rows.append({
                "measurement_group_id": group["measurement_group_id"],
                "official_name": group["official_name"],
                "selected_edge_ids": group["selected_edge_ids"],
                "assigned_amount": amount,
                "supported": amount > 0,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--detector-lanes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    expected = set(read_relation_file(args.relations))
    routed = route_population(args.routes)
    support = measurement_group_support(args.groups, read_route_edge_support(args.routes))
    with (args.output / "measurement_group_spatial_support.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(support[0]))
        writer.writeheader()
        writer.writerows(support)

    expected_base = {pair for pair in expected if pair[0].startswith("PT_SZ_")}
    expected_through = {pair for pair in expected if pair[0].startswith("EXT_KZ_")}
    summary = {
        "artifact_id": "TOKYO_PT_2018_EXTERNAL_THROUGH_DRIVER_ROUTE_SUPPORT_V1",
        "research_stage": "2-3-D",
        "expected_od_count": len(expected),
        "routed_od_count": len(routed),
        "missing_route_od_count": len(expected - routed),
        "unexpected_route_od_count": len(routed - expected),
        "existing_expected_od_count": len(expected_base),
        "existing_routed_od_count": len(expected_base & routed),
        "added_expected_od_count": len(expected_through),
        "added_routed_od_count": len(expected_through & routed),
        "measurement_group_count": len(support),
        "supported_measurement_group_count": sum(bool(row["supported"]) for row in support),
        "unsupported_measurement_group_ids": [
            row["measurement_group_id"] for row in support if not row["supported"]
        ],
        "fixed_input_hashes": {
            "measurement_groups.csv": sha256(args.groups),
            "detector_lanes.csv": sha256(args.detector_lanes),
        },
        "observation_values_used": False,
        "location_ids_used_for_support_only": True,
        "numeric_calibration_run": False,
        "police_2024_data": "not_read_not_used",
    }
    (args.output / "route_support_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
