"""Integrate the nine external-observation targets into final calibration artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.calibration import road_census_sumo_pipeline as pipeline


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_final_inventory_20260827_v1"
DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
RAW_DIR = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
RAW_SECTIONS = RAW_DIR / "kasyo13.csv"
RAW_HOURLY = RAW_DIR / "zkntrf13.csv"

DIRECTION_FINAL = DATA_DIR / "external_observation_direction_final_classification.csv"
DIRECTION_CLUSTERS = DATA_DIR / "external_observation_direction_cluster_evidence.csv"
ROUTE316_DIRECTION = DATA_DIR / "route316_direction_diagnosis.csv"
ROUTE316_DIRECTION_EVIDENCE = DATA_DIR / "route316_direction_evidence.csv"
ADOPTION_REVIEW = DATA_DIR / "external_observation_opposite_carriageway_adoption_review.csv"
ROUTE316_ADOPTION = DATA_DIR / "route316_opposite_carriageway_adoption_review.csv"
ROUTE316_TARGETS = DATA_DIR / "route316_opposite_carriageway_target_summary.csv"
PARTIAL_SEGMENTS = DATA_DIR / "external_observation_partial_edge_mapping_v1.csv"
PARTIAL_REVIEW = DATA_DIR / "external_observation_partial_edge_formal_review.csv"
POST_PARTIAL_INVENTORY = DATA_DIR / "external_observation_post_partial_edge_inventory.csv"
PARTIAL_SCHEMA = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/partial_edge_mapping.schema.json"
PARTIAL_SPEC = REPOSITORY_ROOT / "05_src/traffic_simulation/partial_edge_mapping_specification.md"
CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
NETWORK = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"

FINAL_DIR = DATA_DIR / "external_observation_finalization_20260827"
INVENTORY_CSV = FINAL_DIR / "external_observation_final_inventory.csv"
SUMMARY_JSON = FINAL_DIR / "final_traffic_observation_status_summary.json"
SCHEMA_JSON = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/final_traffic_observations.schema.json"
OBSERVATIONS_CSV = FINAL_DIR / "final_traffic_observations.csv"
MANIFEST_JSON = FINAL_DIR / "external_observation_final_inventory_manifest.json"
VALIDATION_JSON = FINAL_DIR / "external_observation_final_inventory_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_final_inventory_specification.md"
VALIDATOR = REPOSITORY_ROOT / "05_src/traffic_simulation/validation/validate_external_observation_final_inventory.py"

UP = "UP_TERMINUS_TO_ORIGIN"
DOWN = "DOWN_ORIGIN_TO_TERMINUS"
SPATIAL_REASON = "SPATIAL_CORRESPONDENCE_BELOW_EXISTING_ADOPTION_CRITERIA"
HISTORICAL_REASON = "HISTORICAL_EXTERNAL_VALIDATION_WEIGHT_ZERO"


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


def split_edges(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def machine_sources() -> dict[str, Any]:
    post = read_csv(POST_PARTIAL_INVENTORY)
    if len(post) != 9 or len({row["target_section_id"] for row in post}) != 9:
        raise ValueError("post-partial inventory is not the unique nine-target population")
    return {
        "post": post,
        "direction_final": read_csv(DIRECTION_FINAL),
        "direction_clusters": read_csv(DIRECTION_CLUSTERS),
        "route316_direction": read_csv(ROUTE316_DIRECTION),
        "adoption": read_csv(ADOPTION_REVIEW),
        "route316_adoption": read_csv(ROUTE316_ADOPTION),
        "partial": read_csv(PARTIAL_REVIEW),
        "partial_segments": read_csv(PARTIAL_SEGMENTS),
    }


def inventory_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    post_by_target = {row["target_section_id"]: row for row in sources["post"]}
    clusters = {row["official_observation_section_id"]: row for row in sources["direction_clusters"]}
    adoption = {row["target_section_id"]: row for row in sources["adoption"]}
    route316 = {row["target_section_id"]: row for row in sources["route316_adoption"]}
    route316_direction = {row["target"]: row for row in sources["route316_direction"]}
    partial = {row["target_section_id"]: row for row in sources["partial"]}
    raw_sections = {row["交通調査基本区間番号"]: row
                    for row in pipeline.read_csv_cp932(RAW_SECTIONS)}
    rows: list[dict[str, Any]] = []
    for target in sorted(post_by_target):
        post = post_by_target[target]
        observation = post["official_observation_section_id"]
        raw = raw_sections[observation]
        route_identity = f"{post['cluster'].replace('ROUTE_', '')}:{raw['路線名']}"
        coverage = endpoint = projection = ""
        partial_used = "false"
        segment_reference = ""
        connection_violations = "0"
        route_status = topology_status = contamination_status = "PASS"
        exclusion = review_reason = ""
        observation_date = raw["上り／交通量観測年月日"].strip()
        observation_year = int(observation_date[:4])

        if target in partial:
            item = partial[target]
            cluster = clusters[observation]
            selected_role, selected_edges = DOWN, split_edges(post["down_sumo_edge_sequence"])
            opposite_role, opposite_edges = UP, split_edges(post["up_sumo_edge_sequence"])
            direction_status = "RESOLVED_DOWN"
            opposite_status = "ACCEPTED_AS_PARTIAL_EDGE_MAPPING"
            partial_used = "true"
            segment_reference = post["edge_segment_specification_reference"]
            traffic_status = "BIDIRECTIONAL_ASSIGNMENT_AVAILABLE"
            coverage = item["partial_edge_coverage_ratio"]
            endpoint = item["endpoint_difference_m"]
            projection = item["projection_error_m"]
            source_artifact = relative(PARTIAL_REVIEW)
            decisive = "formal partial-edge review + reproducible terminal segment + route/topology/contamination PASS"
            provenance = "COMPLETE_MACHINE_READABLE_HISTORICAL_OBSERVATION"
            if cluster["direction_evidence_status"] != "RESOLVED" or item["new_adoption_status"] != opposite_status:
                raise ValueError("Route 1 machine evidence conflict")
        elif target in route316:
            item = route316[target]
            diagnosis = route316_direction[target]
            selected_role, selected_edges = UP, split_edges(item["selected_edge_sequence"])
            opposite_role, opposite_edges = DOWN, split_edges(item["alternate_edge_sequence"])
            direction_status = "RESOLVED_UP"
            opposite_status = item["adoption_status"]
            traffic_status = item["traffic_assignment_status"]
            coverage = item["official_coverage_by_alternate_ratio"]
            endpoint = str(max(float(item["selected_start_to_alternate_end_distance_m"]),
                               float(item["selected_end_to_alternate_start_distance_m"])))
            source_artifact = relative(ROUTE316_ADOPTION)
            decisive = "resolved official direction + route/topology/contamination PASS + configured spatial criteria FAIL"
            review_reason = SPATIAL_REASON
            provenance = "COMPLETE_MACHINE_READABLE_REVIEW_BLOCKER"
            if diagnosis["proposed_direction_status"] != "RESOLVED_UP" or opposite_status != "REVIEW_REQUIRED":
                raise ValueError("Route 316 machine evidence conflict")
        elif target in adoption:
            item = adoption[target]
            selected_role = item["fixed_direction"]
            opposite_role = item["alternate_direction"]
            selected_edges = split_edges(item["fixed_edge_sequence"])
            if selected_role == DOWN:
                opposite_edges = split_edges(item["up_sumo_edge_sequence"])
                direction_status = "RESOLVED_DOWN"
            else:
                opposite_edges = split_edges(item["down_sumo_edge_sequence"])
                direction_status = "RESOLVED_UP"
            opposite_status = item["adoption_status"]
            traffic_status = "BIDIRECTIONAL_ASSIGNMENT_AVAILABLE"
            coverage = item["opposite_axis_coverage_by_fixed_ratio"]
            endpoint = str(max(float(item["fixed_start_to_opposite_end_distance_m"]),
                               float(item["fixed_end_to_opposite_start_distance_m"])))
            connection_violations = item["connection_violation_count"]
            route_status = "PASS" if item["route_identity_status"] == "CONFIRMED" else "FAIL"
            topology_status = "PASS" if item["topology_status"] == "CONNECTED" else "FAIL"
            contamination_status = "PASS" if not json.loads(item["inappropriate_edge_ids_json"]) else "FAIL"
            source_artifact = relative(ADOPTION_REVIEW)
            decisive = "formal opposite-carriageway adoption + route/topology/coverage/endpoint criteria PASS"
            provenance = "COMPLETE_MACHINE_READABLE_CURRENT_OBSERVATION"
            if opposite_status != "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY":
                raise ValueError(f"unexpected non-accepted prior adoption target: {target}")
        else:
            cluster = clusters[observation]
            if cluster["direction_evidence_status"] != "RESOLVED" or cluster["traffic_assignment_status"] != "BIDIRECTIONAL_ASSIGNABLE":
                raise ValueError(f"direct reverse evidence conflict: {target}")
            selected_role = cluster["adopted_sequence_role"]
            direction_status = "RESOLVED_UP" if selected_role == UP else "RESOLVED_DOWN"
            selected_edges = split_edges(post["up_sumo_edge_sequence"] if selected_role == UP
                                         else post["down_sumo_edge_sequence"])
            opposite_role = DOWN if selected_role == UP else UP
            opposite_edges = split_edges(post["down_sumo_edge_sequence"] if selected_role == UP
                                         else post["up_sumo_edge_sequence"])
            opposite_status = "DIRECT_REVERSE_AVAILABLE"
            traffic_status = "BIDIRECTIONAL_ASSIGNMENT_AVAILABLE"
            connection_violations = str(int(cluster["connection_violation_count"])
                                        + int(cluster["reverse_connection_violation_count"]))
            source_artifact = relative(DIRECTION_CLUSTERS)
            decisive = "complete direct reverse edge sequence + official direction anchor + zero connection violations"
            provenance = "COMPLETE_MACHINE_READABLE_CURRENT_OBSERVATION"

        if traffic_status == "REVIEW_REQUIRED":
            calibration_status, calibration_weight = "REVIEW_REQUIRED", "0.0"
            exclusion = SPATIAL_REASON
        elif observation_year < 2021:
            calibration_status, calibration_weight = "VALIDATION_ONLY", "0.0"
            exclusion = HISTORICAL_REASON
        else:
            calibration_status, calibration_weight = "CALIBRATION_USABLE", "1.0"

        rows.append({
            "official_observation_section_id": observation,
            "target_id": target, "route_identity": route_identity,
            "direction_evidence_status": direction_status,
            "selected_corridor_role": selected_role,
            "selected_edge_sequence": ";".join(selected_edges),
            "selected_edge_count": len(selected_edges),
            "opposite_mapping_status": opposite_status,
            "opposite_corridor_role": opposite_role,
            "opposite_edge_sequence": ";".join(opposite_edges),
            "opposite_edge_count": len(opposite_edges),
            "partial_edge_used": partial_used,
            "edge_segment_specification_reference": segment_reference,
            "traffic_assignment_status": traffic_status,
            "calibration_usability_status": calibration_status,
            "calibration_weight": calibration_weight,
            "calibration_exclusion_reason": exclusion,
            "review_required_reason": review_reason,
            "observation_year": observation_year,
            "observation_type": "HISTORICAL_EXTERNAL_VALIDATION" if observation_year < 2021 else "CURRENT_OFFICIAL_OBSERVATION",
            "coverage_ratio": coverage, "endpoint_difference_m": endpoint,
            "projection_error_m": projection,
            "connection_violation_count": connection_violations,
            "route_identity_status": route_status,
            "topology_status": topology_status,
            "contamination_status": contamination_status,
            "decisive_evidence": decisive,
            "source_review_artifact": source_artifact,
            "provenance_status": provenance,
        })
    return rows


HOURS = list(range(7, 24)) + list(range(0, 7))
FULLWIDTH = str.maketrans("0123456789", "０１２３４５６７８９")


def observation_series() -> dict[str, dict[str, Any]]:
    raw_sections = {row["交通調査基本区間番号"]: row
                    for row in pipeline.read_csv_cp932(RAW_SECTIONS)}
    hourly = pipeline.read_csv_cp932(RAW_HOURLY)
    observations = {row["official_observation_section_id"] for row in read_csv(POST_PARTIAL_INVENTORY)}
    result: dict[str, dict[str, Any]] = {}
    for observation in observations:
        section = raw_sections[observation]
        prefecture_city = section["交通量／都道府県指定市コード"].strip()
        unit = section["交通量／調査単位区間番号"].strip()
        source_rows = [row for row in hourly
                       if row["都道府県指定市コード"].strip() == prefecture_city
                       and row["交通量調査単位区間番号"].strip() == unit]
        if len(source_rows) != 4:
            raise ValueError(f"expected exactly four vehicle-class/direction rows: {observation}")
        directions: dict[str, dict[int, int]] = {}
        for code, name in (("1", "UP"), ("2", "DOWN")):
            selected = [row for row in source_rows if row["上り・下りの別"].strip() == code]
            classes = {row["車種区分"].strip(): row for row in selected}
            if set(classes) != {"1", "2"}:
                raise ValueError(f"missing official vehicle class: {observation}/{name}")
            directions[name] = {}
            for hour in HOURS:
                label = str(hour).translate(FULLWIDTH)
                field = f"時間帯別自動車類交通量（台／時）／{label}時台"
                texts = [classes[vehicle_class][field].strip() for vehicle_class in ("1", "2")]
                if texts == ["", ""]:
                    continue
                if any(text == "" for text in texts):
                    raise ValueError(f"partial vehicle-class value: {observation}/{name}/{hour}")
                values = [int(text) for text in texts]
                directions[name][hour] = sum(values)
        if set(directions["UP"]) != set(directions["DOWN"]) or len(directions["UP"]) not in {12, 24}:
            raise ValueError(f"unexpected official observation window: {observation}")
        dates = {row["交通量観測年月日"].strip() for row in source_rows}
        flags = {row["令和３年度調査交通量観測・非観測の別"].strip() for row in source_rows}
        if len(dates) != 1 or not next(iter(dates)) or len(flags) != 1:
            raise ValueError(f"ambiguous official observation provenance: {observation}")
        date = next(iter(dates))
        result[observation] = {
            "prefecture_city": prefecture_city, "traffic_unit": unit,
            "date": date, "year": int(date[:4]), "flag": next(iter(flags)),
            "directions": directions,
        }
    return result


def observation_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    series = observation_series()
    rows: list[dict[str, Any]] = []
    for item in inventory:
        observation = item["official_observation_section_id"]
        source = series[observation]
        historical = item["observation_type"] == "HISTORICAL_EXTERNAL_VALIDATION"
        for direction_name in ("UP", "DOWN"):
            for hour in sorted(source["directions"][direction_name]):
                value = source["directions"][direction_name][hour]
                label = str(hour).translate(FULLWIDTH)
                rows.append({
                    "official_observation_section_id": observation,
                    "target_id": item["target_id"], "direction": direction_name,
                    "observation_year": item["observation_year"],
                    "observation_type": item["observation_type"],
                    "hour": hour, "begin_time": f"{hour:02d}:00:00",
                    "end_time": f"{(hour + 1) % 24:02d}:00:00",
                    "raw_observed_value": value, "normalized_observed_value": value,
                    "unit": "vehicles_per_hour", "source_year": source["year"],
                    "source_system": "MLIT_ROAD_CENSUS_R3",
                    "source_field": f"時間帯別自動車類交通量（台／時）／{label}時台",
                    "selected_edge_sequence": item["selected_edge_sequence"],
                    "opposite_edge_sequence": item["opposite_edge_sequence"],
                    "edge_segment_specification_reference": item["edge_segment_specification_reference"],
                    "mapping_status": item["opposite_mapping_status"],
                    "direction_status": item["direction_evidence_status"],
                    "calibration_usability_status": item["calibration_usability_status"],
                    "calibration_weight": item["calibration_weight"],
                    "exclusion_or_review_reason": item["calibration_exclusion_reason"] or item["review_required_reason"],
                    "source_object": f"zkntrf13.csv#{source['prefecture_city']}|{source['traffic_unit']}|{direction_name}|{hour:02d}",
                    "derivation_rule": "SUM_SMALL_AND_LARGE_AT_OFFICIAL_CROSS_SECTION_NO_EDGE_DIVISION_V1",
                    "provenance_class": "OFFICIAL_HISTORICAL_VALIDATION" if historical else "OFFICIAL_CURRENT",
                    "mapping_evidence_artifact": item["source_review_artifact"],
                })
    return rows


def validate_schema(rows: list[dict[str, Any]]) -> list[str]:
    schema = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        converted = dict(row)
        for field in ("observation_year", "hour", "raw_observed_value", "source_year"):
            converted[field] = int(converted[field])
        converted["normalized_observed_value"] = float(converted["normalized_observed_value"])
        converted["calibration_weight"] = float(converted["calibration_weight"])
        for issue in validator.iter_errors(converted):
            errors.append(f"row {index}: {issue.message}")
    return errors


def build_summary(inventory: list[dict[str, Any]], observations: list[dict[str, Any]]) -> dict[str, Any]:
    direction = Counter(row["direction_evidence_status"] for row in inventory)
    traffic = Counter(row["traffic_assignment_status"] for row in inventory)
    usability = Counter(row["calibration_usability_status"] for row in inventory)
    opposite = Counter(row["opposite_mapping_status"] for row in inventory)
    schema_errors = validate_schema(observations)
    summary = {
        "run_id": RUN_ID, "generator_version": SCRIPT_VERSION, "status": "PASSED",
        "status_taxonomy": {
            "direction_evidence_status": ["RESOLVED_UP", "RESOLVED_DOWN", "UNRESOLVED_INSUFFICIENT_EVIDENCE", "UNRESOLVED_CONFLICT"],
            "opposite_mapping_status": ["NOT_REQUIRED", "DIRECT_REVERSE_AVAILABLE", "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY", "ACCEPTED_AS_PARTIAL_EDGE_MAPPING", "REVIEW_REQUIRED", "REJECTED", "NOT_AVAILABLE"],
            "traffic_assignment_status": ["BIDIRECTIONAL_ASSIGNMENT_AVAILABLE", "SINGLE_DIRECTION_ASSIGNMENT_AVAILABLE", "REVIEW_REQUIRED", "DATA_NOT_AVAILABLE", "UNRESOLVED"],
            "calibration_usability_status": ["CALIBRATION_USABLE", "CALIBRATION_USABLE_SINGLE_DIRECTION", "REVIEW_REQUIRED", "VALIDATION_ONLY", "DATA_NOT_AVAILABLE", "EXCLUDED"],
        },
        "counts": {
            "target_total": len(inventory),
            "direction_resolved": sum(status.startswith("RESOLVED_") for status in direction.elements()),
            "direction_unresolved": sum(status.startswith("UNRESOLVED_") for status in direction.elements()),
            "bidirectional_assignment_available": traffic["BIDIRECTIONAL_ASSIGNMENT_AVAILABLE"],
            "review_required": traffic["REVIEW_REQUIRED"],
            "calibration_usable": usability["CALIBRATION_USABLE"],
            "calibration_validation_only": usability["VALIDATION_ONLY"],
            "calibration_unusable_or_review": len(inventory) - usability["CALIBRATION_USABLE"],
            "partial_edge_mapping": opposite["ACCEPTED_AS_PARTIAL_EDGE_MAPPING"],
            "opposite_carriageway_adopted": opposite["ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"],
            "direct_reverse_available": opposite["DIRECT_REVERSE_AVAILABLE"],
            "data_conflict": sum(row["direction_evidence_status"] == "UNRESOLVED_CONFLICT" for row in inventory),
            "topology_failure": sum(row["topology_status"] != "PASS" for row in inventory),
            "route_identity_failure": sum(row["route_identity_status"] != "PASS" for row in inventory),
            "contamination_failure": sum(row["contamination_status"] != "PASS" for row in inventory),
            "final_traffic_observation_rows": len(observations),
            "schema_validation_errors": len(schema_errors),
        },
        "observation_value_policy": {
            "cross_section_value_preserved": True,
            "divided_by_mapped_edge_count": False,
            "one_to_many_target_policy": "REPEAT_OBSERVATION_SERIES_WITHOUT_DIVISION",
            "historical_silent_substitution": False,
            "historical_calibration_weight": 0.0,
        },
        "expected_state_reconciliation": {
            "assignment_ready_targets": 6,
            "current_calibration_usable_targets": 5,
            "difference_reason": HISTORICAL_REASON,
        },
    }
    expected = {
        "target_total": 9, "direction_resolved": 9, "direction_unresolved": 0,
        "bidirectional_assignment_available": 6, "review_required": 3,
        "calibration_usable": 5, "calibration_validation_only": 1,
        "calibration_unusable_or_review": 4, "partial_edge_mapping": 1,
        "opposite_carriageway_adopted": 2, "direct_reverse_available": 3,
        "data_conflict": 0, "topology_failure": 0, "route_identity_failure": 0,
        "contamination_failure": 0, "final_traffic_observation_rows": 240,
        "schema_validation_errors": 0,
    }
    if summary["counts"] != expected:
        raise ValueError(f"final inventory QA count mismatch: {summary['counts']}")
    if any(float(row["normalized_observed_value"]) != float(row["raw_observed_value"])
           for row in observations):
        raise ValueError("observed values were normalized by an unauthorized rule")
    return summary


def render_report(inventory: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# External traffic observation final inventory specification", "",
        "## Status axes", "",
        "`direction_evidence_status`、`opposite_mapping_status`、`traffic_assignment_status`、",
        "`calibration_usability_status`を独立して管理する。direction解決は反対車道採択や",
        "calibration利用可能性を自動的には意味しない。", "",
        "## Nine-target final inventory", "",
        "| target | direction | opposite mapping | assignment | calibration |",
        "|---|---|---|---|---|",
    ]
    for row in inventory:
        lines.append(
            f"| `{row['target_id']}` | `{row['direction_evidence_status']}` | "
            f"`{row['opposite_mapping_status']}` | `{row['traffic_assignment_status']}` | "
            f"`{row['calibration_usability_status']}` |"
        )
    counts = summary["counts"]
    lines.extend([
        "", "## Recomputed counts", "",
        f"- direction resolved: {counts['direction_resolved']}",
        f"- bidirectional assignment available: {counts['bidirectional_assignment_available']}",
        f"- current calibration usable: {counts['calibration_usable']}",
        f"- validation only: {counts['calibration_validation_only']}",
        f"- review required: {counts['review_required']}", "",
        "国道1号はmappingと双方向assignmentは正式利用可能だが、公式raw seriesの観測日は",
        "2019-11-20である。`HISTORICAL_EXTERNAL_VALIDATION`、calibration weight 0、",
        "`VALIDATION_ONLY`として保持し、2021 current observationへsilent substitutionしない。", "",
        "都道316号3件はすべて `RESOLVED_UP` であり、direction unresolvedではない。残課題は",
        f"`{SPATIAL_REASON}` で、opposite mapping、traffic assignment、calibration usabilityを",
        "`REVIEW_REQUIRED`とする。", "",
        "## final_traffic_observations.csv", "",
        "公式raw `zkntrf13.csv`から5観測地点の公開時間値を読み、9 targetへ240行を生成する。",
        "国道1号は24時間、他4観測地点は公式12時間（7–18時）であり、未公開夜間値は補完しない。",
        "small/large vehicle classを公式cross-section単位で合計し、raw値とnormalized値は同値である。",
        "観測値をmapped edge数で割らず、one-to-many targetには同じcross-section seriesを反復する。", "",
        "国道1号のUP列は14 edge sequenceのまま保持し、`542890137#0`の部分使用は",
        "`external_observation_partial_edge_mapping_v1.csv`へのreferenceで表す。新SUMO edgeは作らない。", "",
        "schemaはcurrent、historical validation、data not availableを共通に表現でき、",
        "historicalはweight 0、DATA_NOT_AVAILABLEはnull値・weight 0を要求する。", "",
        "既存mapping、direction、adoption review、SUMO network、config/thresholdは変更していない。", "",
    ])
    if "validation" in summary:
        lines.append(
            f"Validation: {summary['validation']['passed_test_count']} passed, "
            f"{summary['validation']['failed_test_count']} failed."
        )
        lines.append("")
    return "\n".join(lines)


def write_all() -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    sources = machine_sources()
    inventory = inventory_rows(sources)
    observations = observation_rows(inventory)
    summary = build_summary(inventory, observations)
    if not VALIDATION_JSON.exists():
        VALIDATION_JSON.write_text(json.dumps({
            "status": "NOT_RUN", "verified_on": None, "test_command": None,
            "passed_test_count": 0, "failed_test_count": 0,
            "new_final_inventory_test_count": 0,
        }, indent=2) + "\n", encoding="utf-8")
    summary["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    write_csv(INVENTORY_CSV, inventory)
    write_csv(OBSERVATIONS_CSV, observations)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(inventory, summary), encoding="utf-8")
    inputs = [
        DIRECTION_FINAL, DIRECTION_CLUSTERS, ROUTE316_DIRECTION,
        ROUTE316_DIRECTION_EVIDENCE, ADOPTION_REVIEW, ROUTE316_ADOPTION,
        ROUTE316_TARGETS, PARTIAL_SEGMENTS, PARTIAL_REVIEW, POST_PARTIAL_INVENTORY,
        PARTIAL_SCHEMA, PARTIAL_SPEC, CONFIG, NETWORK, RAW_SECTIONS, RAW_HOURLY,
        SCHEMA_JSON, VALIDATOR,
    ]
    outputs = [INVENTORY_CSV, SUMMARY_JSON, SCHEMA_JSON, OBSERVATIONS_CSV,
               VALIDATION_JSON, REPORT]
    manifest = {
        "run_id": RUN_ID, "generator": relative(Path(__file__)),
        "generator_version": SCRIPT_VERSION, "generator_sha256": sha256_file(Path(__file__)),
        "input_hashes": {relative(path): sha256_file(path) for path in inputs},
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "qa_status": summary["status"], "counts": summary["counts"],
        "non_mutation_contract": {
            "sumo_network_changed": False, "mapping_overwritten": False,
            "direction_artifacts_changed": False, "adoption_artifacts_changed": False,
            "threshold_changed": False, "route316_forced_adoption": False,
            "traffic_count_divided_by_edge_count": False,
            "historical_substituted_as_current": False,
        },
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
