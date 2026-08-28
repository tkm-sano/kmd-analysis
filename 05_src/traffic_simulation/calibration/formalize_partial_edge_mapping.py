"""Formalize and validate the non-destructive Road Census-SUMO segment layer."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator
from shapely.geometry import LineString
from shapely.ops import substring
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.calibration import investigate_route1_opposite_carriageway_boundary as route1


SCRIPT_VERSION = "1.0.0"
RUN_ID = "partial_edge_mapping_formalization_20260827_v1"
POSITION_TOLERANCE_M = 0.001
OBSERVATION_ID = "13300010260"
DATA_DIR = route1.DATA_DIR
SPECIFICATION = REPOSITORY_ROOT / "05_src/traffic_simulation/partial_edge_mapping_specification.md"
SCHEMA = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/partial_edge_mapping.schema.json"
CONFIG = route1.CONFIG
BASE_66 = DATA_DIR / "census_section_final_mapping.csv"
BASE_BEFORE_AFTER = DATA_DIR / "census_mapping_before_after.csv"
DIRECTION_FINAL = DATA_DIR / "external_observation_direction_final_classification.csv"
ADOPTION_REVIEW = route1.ADOPTION_REVIEW
PRIOR_BOUNDARY_REVIEW = route1.REVIEW_CSV
PRIOR_BOUNDARY_EDGE_EVIDENCE = route1.EDGE_CSV

SEGMENTS_CSV = DATA_DIR / "external_observation_partial_edge_mapping_v1.csv"
FORMAL_REVIEW_CSV = DATA_DIR / "external_observation_partial_edge_formal_review.csv"
CANDIDATE_INVENTORY_CSV = DATA_DIR / "partial_edge_candidate_inventory.csv"
POST_REVIEW_INVENTORY_CSV = DATA_DIR / "external_observation_post_partial_edge_inventory.csv"
QA_JSON = DATA_DIR / "external_observation_partial_edge_mapping_qa.json"
MANIFEST_JSON = DATA_DIR / "external_observation_partial_edge_mapping_manifest.json"
VALIDATION_JSON = DATA_DIR / "external_observation_partial_edge_mapping_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_partial_edge_formal_review.md"

REQUIRED_FIELDS = (
    "official_observation_section_id", "direction", "sequence_order", "edge_id",
    "coverage_role", "start_position_m", "end_position_m", "edge_length_m",
    "used_length_m", "boundary_position_source", "boundary_anchor",
    "derivation_rule_id", "projection_error_m", "route_identity_status",
    "topology_status", "contamination_status", "adoption_status",
)
ROLES = {"FULL_EDGE", "PARTIAL_START_EDGE", "PARTIAL_END_EDGE", "PARTIAL_SINGLE_EDGE"}
SCREENING_CLASSES = {
    "NOT_TRIGGERED", "PARTIAL_EDGE_REVIEW_CANDIDATE", "PARTIAL_EDGE_RESOLVED",
    "ROUTE_IDENTITY_CONFLICT", "TOPOLOGY_CONFLICT",
    "CARRIAGEWAY_IDENTIFICATION_FAILURE", "OFFICIAL_DIRECTION_UNRESOLVED",
    "GENUINE_GEOMETRY_MISMATCH", "INSUFFICIENT_EVIDENCE",
}


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPOSITORY_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def segment_line(
    sequence: list[str], metadata: dict[str, dict[str, Any]], terminal_position_m: float
) -> LineString:
    lines = [LineString(metadata[edge_id]["shape"]) for edge_id in sequence[:-1]]
    lines.append(substring(LineString(metadata[sequence[-1]]["shape"]), 0, terminal_position_m))
    coordinates: list[tuple[float, float]] = []
    for line in lines:
        points = list(line.coords)
        coordinates.extend(points[1:] if coordinates and coordinates[-1] == points[0] else points)
    return LineString(coordinates)


def derive_route1() -> dict[str, Any]:
    target, direction = route1.extract_target()
    candidate = target["alternate_carriageway_edge_sequence"].split(";")
    fixed = target["fixed_edge_sequence"].split(";")
    metadata, connections, location = route1.parse_network(set(candidate + fixed))
    terminal = LineString(metadata[candidate[-1]]["shape"])
    fixed_line = route1.combined_line(fixed, metadata)
    anchor = fixed_line.interpolate(0)
    boundary_position = terminal.project(anchor)
    projected_point = terminal.interpolate(boundary_position)
    projection_error = anchor.distance(projected_point)
    partial_line = segment_line(candidate, metadata, boundary_position)
    official = route1.official_geometry(location)
    with CONFIG.open(encoding="utf-8") as handle:
        matching = yaml.safe_load(handle)["matching"]
    buffer_m = float(matching["candidate_buffer_m"])
    coverage_threshold = float(matching["high_section_coverage_ratio"])
    metrics = {
        "official_geometry_coverage_ratio": official.intersection(partial_line.buffer(buffer_m)).length / official.length,
        "candidate_axis_coverage_ratio": partial_line.intersection(fixed_line.buffer(buffer_m)).length / partial_line.length,
        "fixed_axis_coverage_ratio": fixed_line.intersection(partial_line.buffer(buffer_m)).length / fixed_line.length,
        "endpoint_difference_m": math.dist(fixed_line.coords[0], partial_line.coords[-1]),
        "projection_error_m": projection_error,
        "connection_violation_count": len(route1.connection_violations(candidate, connections)),
        "candidate_buffer_m": buffer_m,
        "coverage_threshold": coverage_threshold,
        "boundary_position_m": boundary_position,
    }

    prior = next(row for row in read_csv(PRIOR_BOUNDARY_REVIEW)
                 if row["official_observation_section_id"] == OBSERVATION_ID)
    edge_evidence = [row for row in read_csv(PRIOR_BOUNDARY_EDGE_EVIDENCE)
                     if row["official_observation_section_id"] == OBSERVATION_ID
                     and row["edge_role"] == "CURRENT_CANDIDATE"]
    route_pass = target["route_identity_status"] == "CONFIRMED"
    contamination_pass = (
        len(edge_evidence) == len(candidate)
        and all(row["contamination_status"] == "PASS" for row in edge_evidence)
        and prior["contamination_check"].startswith("PASS_")
    )
    topology_pass = metrics["connection_violation_count"] == 0
    spatial_pass = (
        metrics["official_geometry_coverage_ratio"] >= coverage_threshold
        and metrics["candidate_axis_coverage_ratio"] >= coverage_threshold
        and metrics["fixed_axis_coverage_ratio"] >= coverage_threshold
        and metrics["endpoint_difference_m"] <= buffer_m
        and metrics["projection_error_m"] <= buffer_m
    )
    derivation_reproduced = bool(
        abs(boundary_position - 14.072655216512528) <= POSITION_TOLERANCE_M
    )
    accepted = all((route_pass, contamination_pass, topology_pass, spatial_pass, derivation_reproduced))
    if not accepted:
        raise ValueError("Route 1 does not satisfy the locked partial-edge adoption rule")
    return {
        "target": target, "direction": direction, "candidate": candidate, "fixed": fixed,
        "metadata": metadata, "metrics": metrics, "prior": prior,
        "route_pass": route_pass, "contamination_pass": contamination_pass,
        "topology_pass": topology_pass, "spatial_pass": spatial_pass,
        "derivation_reproduced": derivation_reproduced,
    }


def build_segment_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    candidate = result["candidate"]
    metadata = result["metadata"]
    position = result["metrics"]["boundary_position_m"]
    rows: list[dict[str, Any]] = []
    for order, edge_id in enumerate(candidate, start=1):
        edge_length = LineString(metadata[edge_id]["shape"]).length
        partial = order == len(candidate)
        end = position if partial else edge_length
        rows.append({
            "official_observation_section_id": OBSERVATION_ID,
            "direction": "UP",
            "sequence_order": order,
            "edge_id": edge_id,
            "coverage_role": "PARTIAL_END_EDGE" if partial else "FULL_EDGE",
            "start_position_m": "0.000",
            "end_position_m": f"{end:.3f}",
            "edge_length_m": f"{edge_length:.3f}",
            "used_length_m": f"{end:.3f}",
            "boundary_position_source": "DERIVED_BY_GEOMETRIC_PROJECTION" if partial else "",
            "boundary_anchor": "DOWN_CORRIDOR_START" if partial else "",
            "derivation_rule_id": "PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1" if partial else "",
            "projection_error_m": f"{result['metrics']['projection_error_m']:.3f}" if partial else "",
            "route_identity_status": "PASS",
            "topology_status": "PASS",
            "contamination_status": "PASS",
            "adoption_status": "ACCEPTED_AS_PARTIAL_EDGE_MAPPING",
        })
    return rows


def validate_segment_rows(rows: list[dict[str, Any]]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema)
    errors: list[str] = []
    if tuple(schema["required"]) != REQUIRED_FIELDS:
        errors.append("schema required fields differ from implementation contract")
    if not rows:
        return errors + ["segment mapping is empty"]
    orders = [int(row["sequence_order"]) for row in rows]
    if orders != list(range(1, len(rows) + 1)):
        errors.append("sequence_order is not contiguous from one")
    keys = [(row["official_observation_section_id"], row["direction"], row["sequence_order"])
            for row in rows]
    if len(keys) != len(set(keys)):
        errors.append("duplicate segment row key")
    for index, row in enumerate(rows):
        missing = set(REQUIRED_FIELDS) - set(row)
        if missing:
            errors.append(f"row {index + 1} missing fields: {sorted(missing)}")
            continue
        start, end = float(row["start_position_m"]), float(row["end_position_m"])
        length, used = float(row["edge_length_m"]), float(row["used_length_m"])
        role = row["coverage_role"]
        normalized = dict(row)
        normalized["sequence_order"] = int(row["sequence_order"])
        for field in ("start_position_m", "end_position_m", "edge_length_m", "used_length_m"):
            normalized[field] = float(row[field])
        for field in ("boundary_position_source", "boundary_anchor", "derivation_rule_id"):
            normalized[field] = row[field] or None
        normalized["projection_error_m"] = (
            float(row["projection_error_m"]) if row["projection_error_m"] != "" else None
        )
        for issue in schema_validator.iter_errors(normalized):
            errors.append(f"row {index + 1} schema: {issue.message}")
        if role not in ROLES:
            errors.append(f"row {index + 1} invalid role")
        if not (-POSITION_TOLERANCE_M <= start <= end + POSITION_TOLERANCE_M
                and end <= length + POSITION_TOLERANCE_M):
            errors.append(f"row {index + 1} invalid position range")
        if used <= 0 or abs(used - (end - start)) > POSITION_TOLERANCE_M:
            errors.append(f"row {index + 1} inconsistent used length")
        if role == "FULL_EDGE" and (
            abs(start) > POSITION_TOLERANCE_M or abs(end - length) > POSITION_TOLERANCE_M
            or any(row[field] != "" for field in (
                "boundary_position_source", "boundary_anchor", "derivation_rule_id", "projection_error_m"
            ))
        ):
            errors.append(f"row {index + 1} inconsistent FULL_EDGE")
        if role == "PARTIAL_END_EDGE" and (
            index != len(rows) - 1 or abs(start) > POSITION_TOLERANCE_M
            or not 0 < end < length or any(row[field] == "" for field in (
                "boundary_position_source", "boundary_anchor", "derivation_rule_id", "projection_error_m"
            ))
        ):
            errors.append(f"row {index + 1} inconsistent PARTIAL_END_EDGE")
        if role == "PARTIAL_START_EDGE" and (
            index != 0 or not 0 < start < length or abs(end - length) > POSITION_TOLERANCE_M
        ):
            errors.append(f"row {index + 1} inconsistent PARTIAL_START_EDGE")
        if role == "PARTIAL_SINGLE_EDGE" and (len(rows) != 1 or not 0 <= start < end <= length):
            errors.append(f"row {index + 1} inconsistent PARTIAL_SINGLE_EDGE")
    return errors


def build_formal_review(result: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = result["metrics"]
    prior = result["prior"]
    return [{
        "official_observation_section_id": OBSERVATION_ID,
        "target_section_id": result["target"]["target_section_id"],
        "direction": "UP",
        "edge_sequence": ";".join(result["candidate"]),
        "edge_count": len(result["candidate"]),
        "terminal_edge_id": result["candidate"][-1],
        "coverage_role": "PARTIAL_END_EDGE",
        "boundary_position_m": f"{metrics['boundary_position_m']:.3f}",
        "boundary_position_fact_class": "RULE_DERIVED_NOT_OFFICIAL",
        "boundary_position_source": "DERIVED_BY_GEOMETRIC_PROJECTION",
        "boundary_anchor": "DOWN_CORRIDOR_START",
        "derivation_rule_id": "PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1",
        "derivation_tolerance_m": f"{POSITION_TOLERANCE_M:.3f}",
        "derivation_reproducibility_status": "PASS" if result["derivation_reproduced"] else "FAIL",
        "projection_error_m": f"{metrics['projection_error_m']:.3f}",
        "configured_endpoint_threshold_m": f"{metrics['candidate_buffer_m']:.3f}",
        "endpoint_difference_m": f"{metrics['endpoint_difference_m']:.3f}",
        "configured_coverage_threshold": f"{metrics['coverage_threshold']:.6f}",
        "partial_edge_coverage_ratio": f"{metrics['official_geometry_coverage_ratio']:.6f}",
        "candidate_axis_coverage_ratio": f"{metrics['candidate_axis_coverage_ratio']:.6f}",
        "fixed_axis_coverage_ratio": f"{metrics['fixed_axis_coverage_ratio']:.6f}",
        "connection_violation_count": metrics["connection_violation_count"],
        "route_identity_status": "PASS" if result["route_pass"] else "FAIL",
        "topology_status": "PASS" if result["topology_pass"] else "FAIL",
        "contamination_status": "PASS" if result["contamination_pass"] else "FAIL",
        "prior_final_review_status": prior["final_review_status"],
        "prior_adoption_status": prior["adoption_status"],
        "prior_review_preserved": "true",
        "new_adoption_status": "ACCEPTED_AS_PARTIAL_EDGE_MAPPING",
        "bidirectional_traffic_assignment_status": "BIDIRECTIONAL_ASSIGNABLE",
        "decision_reason": (
            "The unchanged 14-edge UP sequence passes route identity, topology and contamination checks; "
            "the derived 0-14.073 m terminal interval reproduces from the resolved DOWN corridor start "
            "and passes the unchanged 0.60 coverage and 25 m endpoint/projection criteria."
        ),
        "prior_review_reference": relative(PRIOR_BOUNDARY_REVIEW),
        "segment_mapping_reference": relative(SEGMENTS_CSV),
    }]


def build_candidate_inventory() -> list[dict[str, Any]]:
    before = {row["section_id"]: row for row in read_csv(BASE_BEFORE_AFTER)}
    rows: list[dict[str, Any]] = []
    for final in read_csv(BASE_66):
        metrics = before[final["section_id"]]
        coverage = float(metrics["new_corridor_coverage"])
        triggers: list[str] = []
        if coverage < 0.60:
            triggers.append("LOW_COVERAGE")
        if metrics["new_manual_review_required"] == "True":
            triggers.append("REVIEW_REQUIRED_BASELINE")
        if final["final_confidence"] == "low":
            triggers.append("LOW_CONFIDENCE")
        classification = "INSUFFICIENT_EVIDENCE" if triggers else "NOT_TRIGGERED"
        rows.append({
            "population": "BASE_ROAD_CENSUS_66",
            "target_section_id": final["section_id"],
            "official_observation_section_id": final["section_id"],
            "screening_trigger": ";".join(triggers) if triggers else "NONE",
            "existing_coverage_ratio": f"{coverage:.6f}",
            "existing_endpoint_difference_m": "",
            "route_identity_evidence_status": (
                "RESOLVED_BY_MANUAL_REVIEW" if final["manual_reviewed"] == "True" else "AS_RECORDED"
            ),
            "topology_evidence_status": "SELECTED_CORRIDOR",
            "official_direction_status": "NOT_EVALUATED_BY_SCREEN",
            "boundary_anchor_status": "NOT_AVAILABLE_IN_CURRENT_ARTIFACT",
            "partial_edge_screening_class": classification,
            "automatic_adoption": "false",
            "existing_mapping_usable": final["usable_for_traffic_assignment"].lower(),
            "screening_effect_on_existing_mapping": "PRESERVE_EXISTING_DECISION",
            "next_required_evidence": (
                "direction-resolved official or formally derived boundary anchor and edge projection evidence"
                if triggers else "none"
            ),
            "evidence_reference": f"{relative(BASE_66)}:{final['section_id']};{relative(BASE_BEFORE_AFTER)}:{final['section_id']}",
        })

    adoption = {row["official_observation_section_id"]: row for row in read_csv(ADOPTION_REVIEW)}
    for direction in read_csv(DIRECTION_FINAL):
        observation = direction["official_observation_section_id"]
        review = adoption.get(observation)
        if observation == OBSERVATION_ID:
            trigger, classification, anchor, next_evidence = (
                "BOUNDARY_MISMATCH;ENDPOINT_MISMATCH;LOW_COVERAGE",
                "PARTIAL_EDGE_RESOLVED", "FORMALLY_DERIVED_AND_REPRODUCED", "none",
            )
            coverage = "0.840896"
            endpoint = "17.968"
        elif direction["direction_evidence_status"] != "RESOLVED":
            trigger, classification, anchor, next_evidence = (
                "OFFICIAL_DIRECTION_UNRESOLVED", "OFFICIAL_DIRECTION_UNRESOLVED",
                "UNAVAILABLE_UNTIL_DIRECTION_RESOLUTION",
                "resolve official direction and carriageway identity before boundary projection",
            )
            coverage = endpoint = ""
        else:
            trigger, classification, anchor, next_evidence = (
                "NONE", "NOT_TRIGGERED", "NOT_REQUIRED_BY_EXISTING_ACCEPTED_MAPPING", "none",
            )
            coverage = review["opposite_axis_coverage_by_fixed_ratio"] if review else ""
            endpoint = (
                str(max(float(review["fixed_start_to_opposite_end_distance_m"]),
                        float(review["fixed_end_to_opposite_start_distance_m"])))
                if review else ""
            )
        rows.append({
            "population": "EXTERNAL_OBSERVATION_9",
            "target_section_id": direction["target_section_id"],
            "official_observation_section_id": observation,
            "screening_trigger": trigger,
            "existing_coverage_ratio": coverage,
            "existing_endpoint_difference_m": endpoint,
            "route_identity_evidence_status": "RESOLVED",
            "topology_evidence_status": "CONNECTED",
            "official_direction_status": direction["direction_evidence_status"],
            "boundary_anchor_status": anchor,
            "partial_edge_screening_class": classification,
            "automatic_adoption": "false",
            "existing_mapping_usable": (
                "false" if direction["traffic_assignment_status"] == "REVERSE_CORRIDOR_MISSING" else "true"
            ),
            "screening_effect_on_existing_mapping": "PRESERVE_EXISTING_DECISION",
            "next_required_evidence": next_evidence,
            "evidence_reference": f"{relative(DIRECTION_FINAL)}:{direction['target_section_id']}",
        })
    if len(rows) != 75 or any(row["partial_edge_screening_class"] not in SCREENING_CLASSES for row in rows):
        raise ValueError("candidate inventory population or classification invalid")
    return rows


def build_post_review_inventory(result: dict[str, Any]) -> list[dict[str, Any]]:
    adoption = {row["official_observation_section_id"]: row for row in read_csv(ADOPTION_REVIEW)}
    rows: list[dict[str, Any]] = []
    for direction in read_csv(DIRECTION_FINAL):
        observation = direction["official_observation_section_id"]
        if observation == OBSERVATION_ID:
            assignment, status, rule = (
                "BIDIRECTIONAL_ASSIGNABLE", "ACCEPTED_AS_PARTIAL_EDGE_MAPPING",
                "PARTIAL_EDGE_FORMAL_ADOPTION_V1",
            )
            up = ";".join(result["candidate"])
            down = ";".join(result["fixed"])
            segment_reference = relative(SEGMENTS_CSV)
        elif direction["traffic_assignment_status"] == "BIDIRECTIONAL_ASSIGNABLE":
            assignment, status, rule = (
                "BIDIRECTIONAL_ASSIGNABLE", "PRESERVED_EXISTING_BIDIRECTIONAL_MAPPING",
                direction["direction_rule_id"],
            )
            up, down = direction["up_edge_sequence"], direction["down_edge_sequence"]
            segment_reference = ""
        elif observation in adoption and adoption[observation]["adoption_status"] == "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY":
            assignment, status, rule = (
                "BIDIRECTIONAL_ASSIGNABLE", "PRESERVED_ACCEPTED_OPPOSITE_CARRIAGEWAY",
                "OPPOSITE_CARRIAGEWAY_ADOPTION_REVIEW_V1",
            )
            up, down = adoption[observation]["up_sumo_edge_sequence"], adoption[observation]["down_sumo_edge_sequence"]
            segment_reference = ""
        else:
            assignment, status, rule = (
                "DIRECTION_UNRESOLVED", "UNRESOLVED_NO_FORCED_ADOPTION", direction["direction_rule_id"],
            )
            up, down, segment_reference = "", direction["down_edge_sequence"], ""
        rows.append({
            "target_section_id": direction["target_section_id"],
            "official_observation_section_id": observation,
            "cluster": direction["cluster"],
            "direction_evidence_status": direction["direction_evidence_status"],
            "up_sumo_edge_sequence": up,
            "down_sumo_edge_sequence": down,
            "edge_segment_specification_reference": segment_reference,
            "traffic_assignment_status_after_partial_edge_review": assignment,
            "adoption_status_after_partial_edge_review": status,
            "decision_rule_id": rule,
        })
    if len(rows) != 9:
        raise ValueError("external observation inventory is no longer nine targets")
    return rows


def build_qa(
    result: dict[str, Any], segment_rows: list[dict[str, Any]], errors: list[str],
    candidate_rows: list[dict[str, Any]], post_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = result["metrics"]
    qa: dict[str, Any] = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "status": "PASSED" if not errors else "FAILED",
        "validation_rules": {
            "position_range_validity": not any("position range" in error for error in errors),
            "used_length_consistency": not any("used length" in error for error in errors),
            "boundary_derivation_reproducibility": result["derivation_reproduced"],
            "topology_continuity": result["topology_pass"],
            "route_identity": result["route_pass"],
            "contamination": result["contamination_pass"],
            "coverage_recomputation": bool(abs(metrics["official_geometry_coverage_ratio"] - 0.8408960570172147) < 1e-9),
            "endpoint_difference": bool(abs(metrics["endpoint_difference_m"] - 17.96841882740716) < 1e-9),
            "schema_validation": not any("schema" in error or "missing fields" in error for error in errors),
            "coverage_role_consistency": not any("inconsistent" in error for error in errors),
        },
        "route1_review": {
            "edge_count": len(segment_rows),
            "terminal_edge_id": segment_rows[-1]["edge_id"],
            "boundary_position_m": round(metrics["boundary_position_m"], 6),
            "projection_error_m": round(metrics["projection_error_m"], 6),
            "partial_edge_coverage_ratio": round(metrics["official_geometry_coverage_ratio"], 6),
            "endpoint_difference_m": round(metrics["endpoint_difference_m"], 6),
            "connection_violation_count": metrics["connection_violation_count"],
            "prior_status_preserved": True,
            "new_adoption_status": "ACCEPTED_AS_PARTIAL_EDGE_MAPPING",
        },
        "inventory": {
            "base_road_census_count": sum(row["population"] == "BASE_ROAD_CENSUS_66" for row in candidate_rows),
            "external_observation_count": sum(row["population"] == "EXTERNAL_OBSERVATION_9" for row in candidate_rows),
            "screening_class_counts": dict(sorted(Counter(row["partial_edge_screening_class"] for row in candidate_rows).items())),
            "post_review_assignment_counts": dict(sorted(Counter(row["traffic_assignment_status_after_partial_edge_review"] for row in post_rows).items())),
        },
        "non_mutation_contract": {
            "sumo_network_changed": False,
            "sumo_edge_split": False,
            "existing_formal_mapping_changed": False,
            "prior_review_changed": False,
            "matching_threshold_changed": False,
            "traffic_count_apportioned_by_edge_count_or_length": False,
        },
        "errors": errors,
    }
    if errors or not all(qa["validation_rules"].values()):
        raise ValueError(f"partial-edge QA failed: {qa}")
    return qa


def render_report(review: dict[str, Any], qa: dict[str, Any]) -> str:
    counts = qa["inventory"]["post_review_assignment_counts"]
    return f"""# 国道1号 partial-edge mapping 正式再レビュー

## 結論

国道1号 `13300010260` のUP側14-edge列を
`ACCEPTED_AS_PARTIAL_EDGE_MAPPING` と判定する。edge列は変更せず、末尾
`542890137#0` の使用範囲だけを `PARTIAL_END_EDGE` の `0–14.073 m` とする。

14.073 mは公式Road Census境界値ではない。方向解決済みDOWN corridorの始点
`DOWN_CORRIDOR_START` をSUMO edgeへ
`PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1` で投影した導出値である。

## 固定基準による判定

- partial-edge coverage: {review['partial_edge_coverage_ratio']}（既存閾値 {review['configured_coverage_threshold']}）
- candidate/fixed axis coverage: {review['candidate_axis_coverage_ratio']} / {review['fixed_axis_coverage_ratio']}
- endpoint difference / projection error: {review['endpoint_difference_m']} m / {review['projection_error_m']} m（既存閾値 {review['configured_endpoint_threshold_m']} m）
- connection violation: {review['connection_violation_count']}
- route identity / topology / contamination: PASS / PASS / PASS

旧判定 `{review['prior_final_review_status']}` / `{review['prior_adoption_status']}` は
`{review['prior_review_reference']}` に変更せず保持した。新判定は別reviewとして追加した。
Google Maps等の目視情報は正式判定に使用していない。

## 9 target inventory

実成果物を再集計した結果、双方向割当可能は {counts.get('BIDIRECTIONAL_ASSIGNABLE', 0)} 件
（国道1号1、都道2号1、都道11号3、都道421号1）、方向未解決は
{counts.get('DIRECTION_UNRESOLVED', 0)} 件（都道316号3）である。したがって次の主要な
未解決対象は都道316号である。

## 下流接続

edge-level consumerは既存edge列を読み続ける。空間対応、coverage、boundary、endpoint、
空間集計、mapping QAだけが `{relative(SEGMENTS_CSV)}` をjoinする。partial edgeを新しい
SUMO edgeとして扱わず、観測交通量をedge数または使用長で按分しない。
"""


def write_all() -> None:
    result = derive_route1()
    segment_rows = build_segment_rows(result)
    errors = validate_segment_rows(segment_rows)
    review_rows = build_formal_review(result)
    candidate_rows = build_candidate_inventory()
    post_rows = build_post_review_inventory(result)
    qa = build_qa(result, segment_rows, errors, candidate_rows, post_rows)
    write_csv(SEGMENTS_CSV, segment_rows)
    write_csv(FORMAL_REVIEW_CSV, review_rows)
    write_csv(CANDIDATE_INVENTORY_CSV, candidate_rows)
    write_csv(POST_REVIEW_INVENTORY_CSV, post_rows)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(review_rows[0], qa), encoding="utf-8")
    if not VALIDATION_JSON.exists():
        VALIDATION_JSON.write_text(json.dumps({
            "status": "NOT_RUN", "verified_on": None, "test_command": None,
            "passed_test_count": 0, "failed_test_count": 0,
        }, indent=2) + "\n", encoding="utf-8")
    inputs = [SPECIFICATION, SCHEMA, CONFIG, route1.NETWORK, route1.OFFICIAL_GEOMETRY,
              ADOPTION_REVIEW, PRIOR_BOUNDARY_REVIEW, PRIOR_BOUNDARY_EDGE_EVIDENCE,
              BASE_66, BASE_BEFORE_AFTER, DIRECTION_FINAL]
    outputs = [SEGMENTS_CSV, FORMAL_REVIEW_CSV, CANDIDATE_INVENTORY_CSV,
               POST_REVIEW_INVENTORY_CSV, QA_JSON, VALIDATION_JSON, REPORT]
    manifest = {
        "run_id": RUN_ID,
        "generator": relative(Path(__file__)),
        "generator_version": SCRIPT_VERSION,
        "generator_sha256": sha256_file(Path(__file__)),
        "git_base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "input_hashes": {relative(path): sha256_file(path) for path in inputs},
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "derivation": {
            "provenance_class": "DERIVED_BY_GEOMETRIC_PROJECTION",
            "boundary_anchor": "DOWN_CORRIDOR_START",
            "rule_id": "PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1",
            "position_tolerance_m": POSITION_TOLERANCE_M,
        },
        "unchanged_thresholds": {
            "candidate_buffer_m": result["metrics"]["candidate_buffer_m"],
            "high_section_coverage_ratio": result["metrics"]["coverage_threshold"],
        },
        "non_mutation_contract": qa["non_mutation_contract"],
        "qa_status": qa["status"],
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
