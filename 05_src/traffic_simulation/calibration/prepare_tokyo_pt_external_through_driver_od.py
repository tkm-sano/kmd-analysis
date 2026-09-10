#!/usr/bin/env python3
"""Integrate official H30 external-through driver OD with the accepted Ota prior.

The exploratory automobile-person counts are used only to identify the exact
directed candidate pairs. Vehicle demand comes exclusively from official rows
labelled ``1_運転した`` in the planning-basic-zone export.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely.ops import unary_union

from diagnose_ota_external_through_prior import load_basic_zones
from prepare_tokyo_pt_small_zone_driving_od import (
    DRIVER_LABEL,
    SURVEY_YEAR,
    gateway_candidates,
    nearest_gateways,
)
from prepare_tokyo_pt_sumo_od import (
    HOURS,
    load_passenger_edges,
    read_departure_profiles,
    read_location,
    to_sumo_geometry,
)


OTA_BASIC_ZONES = {f"{value:04d}" for value in range(130, 139)}
EXTERNAL_GATEWAYS_PER_ZONE = 3


def parse_basic_zone_token(value: str) -> str | None:
    """Parse an official four-digit planning-basic zone, rejecting totals."""
    match = re.fullmatch(r"\s*\d+_(\d{4}):\s*", value or "")
    if not match:
        return None
    code = match.group(1)
    return None if code in {"8700", "9999"} else code


def read_candidate_pairs(path: Path) -> set[tuple[str, str]]:
    """Read candidate identities only; deliberately ignore exploratory counts."""
    pairs: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            pairs.add((row["origin_zone"], row["destination_zone"]))
    return pairs


def validate_candidate_population(
    candidates: set[tuple[str, str]], ota_zones: set[str] = OTA_BASIC_ZONES
) -> None:
    if not candidates:
        raise ValueError("candidate population is empty")
    ota_pairs = sorted(pair for pair in candidates if pair[0] in ota_zones or pair[1] in ota_zones)
    if ota_pairs:
        raise ValueError(f"candidate population contains Ota endpoint pairs: {ota_pairs[:5]}")


def read_exact_candidate_driver_od(
    path: Path,
    candidates: set[tuple[str, str]],
    valid_zones: set[str],
    ota_zones: set[str] = OTA_BASIC_ZONES,
) -> tuple[dict[tuple[str, str], float], list[dict[str, Any]], dict[str, Any]]:
    """Keep explicit positive driver rows on the exact directed population."""
    validate_candidate_population(candidates, ota_zones)
    driver_totals: dict[tuple[str, str], float] = defaultdict(float)
    present_pairs: set[tuple[str, str]] = set()
    driver_rows: set[tuple[str, str]] = set()
    accounting = Counter()
    labels = Counter()
    with path.open(encoding="cp932", newline="") as stream:
        for row in csv.DictReader(stream):
            accounting["input_rows"] += 1
            labels[row["運転有無"]] += 1
            if row["調査年"] != SURVEY_YEAR:
                accounting["wrong_year_rows_excluded"] += 1
                continue
            origin = parse_basic_zone_token(row["発ゾーン"])
            destination = parse_basic_zone_token(row["着ゾーン"])
            if origin not in valid_zones or destination not in valid_zones:
                accounting["aggregate_other_outside_or_unknown_rows_excluded"] += 1
                continue
            pair = (origin, destination)
            if pair not in candidates:
                accounting["non_candidate_spatial_rows_excluded"] += 1
                continue
            present_pairs.add(pair)
            if row["運転有無"] != DRIVER_LABEL:
                accounting["candidate_non_driver_rows_excluded"] += 1
                continue
            driver_rows.add(pair)
            count = float(row["トリップ数"].replace(",", ""))
            if count <= 0:
                accounting["candidate_nonpositive_driver_rows_excluded"] += 1
                continue
            driver_totals[pair] += count
            accounting["accepted_rows"] += 1

    reconciliation = []
    for origin, destination in sorted(candidates):
        pair = (origin, destination)
        if driver_totals.get(pair, 0) > 0:
            status = "explicit_positive_driver"
        elif pair in driver_rows:
            status = "explicit_nonpositive_driver"
        elif pair in present_pairs:
            status = "driver_row_absent_other_status_present"
        else:
            status = "pair_absent_from_sparse_export"
        reconciliation.append({
            "origin_zone": origin,
            "destination_zone": destination,
            "match_status": status,
            "official_driver_trips": f"{driver_totals.get(pair, 0):.6f}" if pair in driver_totals else "",
            "formally_integrated": status == "explicit_positive_driver",
        })

    accounting.update({
        "candidate_pairs": len(candidates),
        "candidate_pairs_present_any_status": len(present_pairs),
        "candidate_pairs_absent_from_sparse_export": len(candidates - present_pairs),
        "candidate_pairs_without_driver_row": len(candidates - driver_rows),
        "accepted_exact_pairs": len(driver_totals),
        "accepted_driver_trips": round(sum(driver_totals.values())),
    })
    return dict(sorted(driver_totals.items())), reconciliation, {
        **dict(accounting), "driver_status_row_counts": dict(sorted(labels.items()))
    }


def read_relation_file(path: Path) -> dict[tuple[str, str], float]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    for relation in ET.parse(path).getroot().iter("tazRelation"):
        totals[(relation.get("from", ""), relation.get("to", ""))] += float(
            relation.get("count", "0")
        )
    return dict(sorted(totals.items()))


def merge_daily_relations(
    existing: dict[tuple[str, str], float], through: dict[tuple[str, str], float]
) -> dict[tuple[str, str], float]:
    combined = dict(existing)
    for (origin, destination), count in through.items():
        key = (f"EXT_KZ_{origin}", f"EXT_KZ_{destination}")
        if key in combined:
            raise ValueError(f"duplicate OD relation during integration: {key}")
        combined[key] = count
    return dict(sorted(combined.items()))


def expand_basic_hourly_od(
    daily: dict[tuple[str, str], float], profiles: dict[str, dict[int, float]]
) -> tuple[dict[tuple[int, str, str], float], set[str]]:
    """Apply official origin basic-zone profiles without altering OD shares."""
    hourly: dict[tuple[int, str, str], float] = {}
    fallback_zones: set[str] = set()
    uniform = {hour: 1.0 / len(HOURS) for hour in HOURS}
    for (origin, destination), count in daily.items():
        profile = profiles.get(origin)
        if profile is None:
            profile = uniform
            fallback_zones.add(origin)
        for hour in HOURS:
            hourly[(hour, origin, destination)] = count * profile[hour]
    return dict(sorted(hourly.items())), fallback_zones


def write_daily_relations(path: Path, totals: dict[tuple[str, str], float], begin: int, end: int) -> None:
    root = ET.Element("data")
    interval = ET.SubElement(root, "interval", {"id": "passenger", "begin": str(begin), "end": str(end)})
    for (origin, destination), count in sorted(totals.items()):
        ET.SubElement(interval, "tazRelation", {
            "from": origin, "to": destination, "count": f"{count:.6f}",
        })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def read_hourly_relations(path: Path) -> dict[tuple[int, str, str], float]:
    totals: dict[tuple[int, str, str], float] = defaultdict(float)
    for interval in ET.parse(path).getroot().iter("interval"):
        hour = HOURS[0] + int(float(interval.get("begin", "0")) // 3600)
        for relation in interval.findall("tazRelation"):
            totals[(hour, relation.get("from", ""), relation.get("to", ""))] += float(
                relation.get("count", "0")
            )
    return dict(sorted(totals.items()))


def write_hourly_relations(path: Path, totals: dict[tuple[int, str, str], float]) -> None:
    root = ET.Element("data")
    for hour in HOURS:
        begin = (hour - HOURS[0]) * 3600
        interval = ET.SubElement(root, "interval", {
            "id": f"passenger_{hour:02d}", "begin": str(begin), "end": str(begin + 3600),
        })
        for (row_hour, origin, destination), count in sorted(totals.items()):
            if row_hour == hour:
                ET.SubElement(interval, "tazRelation", {
                    "from": origin, "to": destination, "count": f"{count:.9f}",
                })
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def merge_taz(
    path: Path,
    base_taz_path: Path,
    used_basic_zones: set[str],
    sumo_zones: dict[str, Any],
    gateways: dict[str, list[tuple[str, Any]]],
) -> dict[str, Any]:
    base_root = ET.parse(base_taz_path).getroot()
    root = ET.Element("additional")
    existing_ids = set()
    for taz in base_root.iter("taz"):
        taz_id = taz.get("id", "")
        if taz_id in existing_ids:
            raise ValueError(f"duplicate base TAZ id: {taz_id}")
        existing_ids.add(taz_id)
        root.append(ET.fromstring(ET.tostring(taz, encoding="unicode")))
    connector_counts = {}
    for code in sorted(used_basic_zones):
        taz_id = f"EXT_KZ_{code}"
        if taz_id in existing_ids:
            raise ValueError(f"TAZ id collision: {taz_id}")
        taz = ET.SubElement(root, "taz", {"id": taz_id})
        source_weights = nearest_gateways(
            sumo_zones[code].centroid, gateways["sources"], EXTERNAL_GATEWAYS_PER_ZONE
        )
        sink_weights = nearest_gateways(
            sumo_zones[code].centroid, gateways["sinks"], EXTERNAL_GATEWAYS_PER_ZONE
        )
        for edge, weight in source_weights.items():
            ET.SubElement(taz, "tazSource", {"id": edge, "weight": f"{weight:.9f}"})
        for edge, weight in sink_weights.items():
            ET.SubElement(taz, "tazSink", {"id": edge, "weight": f"{weight:.9f}"})
        connector_counts[taz_id] = {"sources": len(source_weights), "sinks": len(sink_weights)}
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return {
        "base_taz_count": len(existing_ids),
        "added_basic_zone_taz_count": len(used_basic_zones),
        "combined_taz_count": len(existing_ids) + len(used_basic_zones),
        "connector_counts": connector_counts,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-driver-csv", type=Path, required=True)
    parser.add_argument("--candidate-pairs", type=Path, required=True)
    parser.add_argument("--raw-public-pt", type=Path, required=True)
    parser.add_argument("--net", type=Path, required=True)
    parser.add_argument("--base-taz", type=Path, required=True)
    parser.add_argument("--base-daily-relations", type=Path, required=True)
    parser.add_argument("--base-hourly-relations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    frame, basic_zones = load_basic_zones(args.raw_public_pt / "tokyo_pt_2018_zone_geometry.zip")
    candidates = read_candidate_pairs(args.candidate_pairs)
    if len(candidates) != 727:
        raise ValueError(f"fixed candidate population changed: {len(candidates)}")
    through, reconciliation, accounting = read_exact_candidate_driver_od(
        args.official_driver_csv, candidates, set(basic_zones), OTA_BASIC_ZONES
    )
    if any(origin in OTA_BASIC_ZONES or destination in OTA_BASIC_ZONES for origin, destination in through):
        raise ValueError("accepted through OD contains an Ota endpoint")

    existing_daily = read_relation_file(args.base_daily_relations)
    combined_daily = merge_daily_relations(existing_daily, through)
    existing_hourly = read_hourly_relations(args.base_hourly_relations)
    profiles = read_departure_profiles(args.raw_public_pt, {origin for origin, _ in through})
    through_hourly_raw, fallback = expand_basic_hourly_od(through, profiles)
    through_hourly = {
        (hour, f"EXT_KZ_{origin}", f"EXT_KZ_{destination}"): count
        for (hour, origin, destination), count in through_hourly_raw.items()
    }
    combined_hourly = dict(existing_hourly)
    for key, count in through_hourly.items():
        if key in combined_hourly:
            raise ValueError(f"duplicate hourly relation: {key}")
        combined_hourly[key] = count

    location = read_location(args.net)
    sumo_zones = {
        code: to_sumo_geometry(geometry, frame.crs, location)
        for code, geometry in basic_zones.items()
    }
    edges, _ = load_passenger_edges(args.net)
    ota_geometry = unary_union([sumo_zones[code] for code in OTA_BASIC_ZONES])
    gateways = gateway_candidates(edges, ota_geometry)
    used_basic = {code for pair in through for code in pair}
    taz_summary = merge_taz(
        args.output / "combined_driver.taz.xml", args.base_taz, used_basic, sumo_zones, gateways
    )

    write_daily_relations(args.output / "combined_driver_daily.taz_relations.xml", combined_daily, 25200, 68400)
    write_daily_relations(args.output / "combined_driver_assignment_relative.taz_relations.xml", combined_daily, 0, 43200)
    write_hourly_relations(args.output / "combined_driver_hourly_07_19.taz_relations.xml", combined_hourly)
    write_csv(args.output / "exact_pair_reconciliation.csv", reconciliation)
    accepted_rows = [{
        "origin_zone": origin,
        "destination_zone": destination,
        "official_driver_trips": f"{count:.6f}",
        "semantic_type": "external_observed_expanded_driver_vehicle_trips",
        "source_driver_status": DRIVER_LABEL,
    } for (origin, destination), count in sorted(through.items())]
    write_csv(args.output / "external_through_driver_od.csv", accepted_rows)

    summary = {
        "artifact_id": "TOKYO_PT_2018_EXTERNAL_THROUGH_DRIVER_OD_INTEGRATION_V1",
        "research_stage": "2-3-D",
        "survey_year": 2018,
        "source_zone_level": "planning-basic zone",
        "driver_filter": DRIVER_LABEL,
        "candidate_identity_source": str(args.candidate_pairs),
        "exploratory_person_trip_counts_used_as_vehicle_demand": False,
        "candidate_pair_count": len(candidates),
        "added_od_count": len(through),
        "added_driver_trip_total": round(sum(through.values())),
        "existing_od_count": len(existing_daily),
        "existing_driver_trip_total": round(sum(existing_daily.values())),
        "combined_od_count": len(combined_daily),
        "combined_driver_trip_total": round(sum(combined_daily.values())),
        "overlap_with_existing_relation_ids": 0,
        "ota_endpoint_added_od_count": 0,
        "daily_hourly_total_difference": sum(combined_daily.values()) - sum(combined_hourly.values()),
        "accounting": accounting,
        "time_distribution": {
            "rule": "official origin planning-basic-zone automobile departure profile",
            "semantic_type": "model_assumed_temporal_prior",
            "fallback_origin_zones": sorted(fallback),
        },
        "taz": taz_summary,
        "external_gateway_rule": {
            "gateways_per_zone": EXTERNAL_GATEWAYS_PER_ZONE,
            "selection": "nearest directed Ota-boundary passenger edges to official zone centroid",
            "weight": "normalized inverse centroid-to-boundary-endpoint distance",
            "observation_values_used": False,
        },
        "numeric_calibration_run": False,
        "measurement_observation_values_used": False,
        "police_2024_data": "not_read_not_used",
    }
    (args.output / "integration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
