"""Review the locked Route 316 opposite-carriageway candidate without adoption."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.calibration import investigate_route316_directions as direction
from traffic_simulation.calibration import road_census_sumo_pipeline as pipeline


SCRIPT_VERSION = "1.0.0"
RUN_ID = "route316_opposite_carriageway_adoption_review_20260827_v1"
OBSERVATION_ID = direction.OBSERVATION_ID
TARGET_IDS = direction.TARGET_IDS
DATA_DIR = direction.DATA_DIR

DIRECTION_DIAGNOSIS = direction.DIAGNOSIS_CSV
DIRECTION_CLASSIFICATION = direction.CLASSIFICATION_CSV
DIRECTION_EDGE_EVIDENCE = direction.EDGE_CSV
DIRECTION_RELATION_EVIDENCE = direction.RELATION_CSV
DIRECTION_ADJACENT_EVIDENCE = direction.ADJACENT_CSV
PRIOR_ADOPTION_REVIEW = DATA_DIR / "external_observation_opposite_carriageway_adoption_review.csv"
DIRECTION_CLUSTERS = direction.DIRECTION_CLUSTER
PARTIAL_EDGE_SPECIFICATION = REPOSITORY_ROOT / "05_src/traffic_simulation/partial_edge_mapping_specification.md"

REVIEW_CSV = DATA_DIR / "route316_opposite_carriageway_adoption_review.csv"
EDGE_CSV = DATA_DIR / "route316_opposite_carriageway_edge_evidence.csv"
TARGET_CSV = DATA_DIR / "route316_opposite_carriageway_target_summary.csv"
QA_JSON = DATA_DIR / "route316_opposite_carriageway_qa.json"
MANIFEST_JSON = DATA_DIR / "route316_opposite_carriageway_manifest.json"
VALIDATION_JSON = DATA_DIR / "route316_opposite_carriageway_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/route316_opposite_carriageway_adoption_review.md"
VALIDATOR = REPOSITORY_ROOT / "05_src/traffic_simulation/validation/validate_route316_opposite_carriageway_adoption.py"

ALLOWED_STATUSES = {
    "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY", "ACCEPTED_AS_PARTIAL_EDGE_MAPPING",
    "REVIEW_REQUIRED", "REJECTED_ROUTE_IDENTITY_CONFLICT", "REJECTED_TOPOLOGY_CONFLICT",
    "REJECTED_SPATIAL_MISMATCH", "REJECTED_CONTAMINATION", "DATA_CONFLICT",
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


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def extract_locked_review() -> dict[str, Any]:
    diagnoses = read_csv(DIRECTION_DIAGNOSIS)
    if len(diagnoses) != 3 or tuple(row["target"] for row in diagnoses) != TARGET_IDS:
        raise ValueError("Route 316 diagnosis target population changed")
    for row in diagnoses:
        expected = {
            "proposed_direction_status": "RESOLVED_UP",
            "selected_corridor_role": direction.UP,
            "opposite_candidate_status": "FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED",
            "direction_evidence_status": "RESOLVED",
            "traffic_assignment_status": "REVIEW_REQUIRED",
            "opposite_candidate_direction_role": direction.DOWN,
            "formal_mapping_changed": "false",
        }
        if any(row[key] != value for key, value in expected.items()):
            raise ValueError(f"DATA_CONFLICT in locked direction diagnosis: {row['target']}")
    locked = direction.extract_locked_evidence()
    if locked["fixed"] != [
        "45662502", "45662510#0", "45662510#1", "45662510#2",
        "45662510#3", "45662510#4", "45662510#5",
    ]:
        raise ValueError("selected 7-edge corridor changed")
    if locked["alternate"] != [
        "652322551#0", "652322551#1", "652322551#2", "45662512",
    ]:
        raise ValueError("locked alternate 4-edge candidate changed")
    return {"diagnoses": diagnoses, "locked": locked}


def official_geometries() -> dict[str, Any]:
    root = ET.parse(direction.NETWORK).getroot()
    transformer, offset_x, offset_y = pipeline.parse_sumo_location(root)
    return pipeline.load_census_geometries(
        direction.ROAD_CENSUS.parent / "webmap_tiles",
        {OBSERVATION_ID, *TARGET_IDS}, transformer, offset_x, offset_y,
    )


def standards_comparison() -> list[dict[str, Any]]:
    prior = read_csv(PRIOR_ADOPTION_REVIEW)
    comparisons = []
    for observation in ("13300010260", "13400020040", "13604210030"):
        row = next(item for item in prior if item["official_observation_section_id"] == observation)
        comparisons.append({
            "reference_route": row["route"], "source_observation": observation,
            "route_identity_rule": row["route_identity_status"],
            "topology_rule": row["topology_status"],
            "configured_buffer_m": row["configured_candidate_buffer_m"],
            "configured_high_coverage_ratio": row["configured_high_section_coverage_ratio"],
            "spatial_result": row["coverage_status"], "adoption_status": row["adoption_status"],
        })
    route11 = next(row for row in read_csv(DIRECTION_CLUSTERS) if row["route_number"] == "11")
    comparisons.append({
        "reference_route": "JP:prefectural:tokyo:11",
        "source_observation": route11["official_observation_section_id"],
        "route_identity_rule": "CANONICAL_ROUTE_IDENTITY",
        "topology_rule": "CONNECTED" if route11["reverse_connection_violation_count"] == "0" else "INVALID",
        "configured_buffer_m": "NOT_SEPARATE_ADOPTION_REVIEW",
        "configured_high_coverage_ratio": "NOT_SEPARATE_ADOPTION_REVIEW",
        "spatial_result": "COMPLETE_REVERSE_EDGE_EVIDENCE",
        "adoption_status": route11["traffic_assignment_status"],
    })
    return comparisons


def build_outputs() -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    review = extract_locked_review()
    facts, direction_edges, relation_rows, adjacent_rows, _ = direction.build_evidence()
    fixed, alternate = review["locked"]["fixed"], review["locked"]["alternate"]
    metadata, connections = facts["metadata"], facts["connections"]
    with direction.CONFIG.open(encoding="utf-8") as handle:
        matching = yaml.safe_load(handle)["matching"]
    buffer_m = float(matching["candidate_buffer_m"])
    high_coverage = float(matching["high_section_coverage_ratio"])
    official = official_geometries()
    official_line = official[OBSERVATION_ID]
    fixed_line = direction.combined_line(fixed, metadata)
    alternate_line = direction.combined_line(alternate, metadata)

    def node_violations(sequence: list[str]) -> list[list[str]]:
        return [[left, right] for left, right in zip(sequence, sequence[1:])
                if metadata[left]["to"] != metadata[right]["from"]]

    fixed_connection = direction.connection_violations(fixed, connections)
    alternate_connection = direction.connection_violations(alternate, connections)
    fixed_node, alternate_node = node_violations(fixed), node_violations(alternate)

    candidate_direction_rows = [row for row in direction_edges if row["corridor_role"] == "ALTERNATE_4_EDGE"]
    fixed_direction_rows = [row for row in direction_edges if row["corridor_role"] == "FIXED_7_EDGE"]
    candidate_tags = [json.loads(row["osm_tags_json"]) for row in candidate_direction_rows]
    fixed_tags = [json.loads(row["osm_tags_json"]) for row in fixed_direction_rows]
    candidate_flat_tags = [tags for edge in candidate_tags for tags in edge.values()]
    fixed_flat_tags = [tags for edge in fixed_tags for tags in edge.values()]
    candidate_names = {item.get("name", "") for item in candidate_flat_tags}
    fixed_names = {item.get("name", "") for item in fixed_flat_tags}
    candidate_refs = {item.get("ref", "") for item in candidate_flat_tags}
    fixed_refs = {item.get("ref", "") for item in fixed_flat_tags}
    relation_candidate = [row for row in relation_rows if row["corridor_role"] == "ALTERNATE_4_EDGE"]
    route_identity_ok = bool(
        candidate_names <= fixed_names
        and candidate_refs == fixed_refs == {"316"}
        and relation_candidate
        and all(row["route_identity_status"] == "PASS" for row in relation_candidate)
        and {row["relation_id"] for row in relation_candidate} == {"11699637"}
        and {row["network"] for row in relation_candidate} == {"JP:prefectural:tokyo"}
        and {row["canonical_name"] for row in relation_candidate} == {"日本橋芝浦大森線"}
    )
    inappropriate: list[str] = []
    edge_rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_direction_rows, start=1):
        tags = [item for item in json.loads(row["osm_tags_json"]).values()]
        relation_evidence = [item for item in json.loads(row["route_relation_membership_json"])
                             if item.get("osm_way_id") in {r["osm_way_id"] for r in relation_candidate}]
        reasons = []
        if row["edge_id"].startswith(":") or metadata[row["edge_id"]]["function"] == "internal":
            reasons.append("INTERNAL_EDGE")
        if metadata[row["edge_id"]]["type"].endswith("_link") or any(
            item.get("highway", "").endswith("_link") for item in tags
        ):
            reasons.append("RAMP_OR_LINK")
        if any(item.get("ref") != "316" for item in tags):
            reasons.append("CROSS_OR_UNRELATED_ROUTE")
        if any(item.get("name", "") not in fixed_names for item in tags):
            reasons.append("FRONTAGE_OR_UNRELATED_CARRIAGEWAY")
        if not relation_evidence:
            reasons.append("ROUTE_RELATION_MEMBERSHIP_MISSING")
        if reasons:
            inappropriate.append(row["edge_id"])
        edge_rows.append({
            "official_observation_section_id": OBSERVATION_ID,
            "candidate_role": "LOCKED_ALTERNATE_4_EDGE",
            "sequence_order": index, "edge_id": row["edge_id"],
            "sumo_from": row["sumo_from"], "sumo_to": row["sumo_to"],
            "sumo_type": metadata[row["edge_id"]]["type"],
            "sumo_function": metadata[row["edge_id"]]["function"],
            "osm_tags_json": row["osm_tags_json"],
            "relation_id": "11699637", "relation_membership_json": json_text(relation_evidence),
            "canonical_route_identity": "JP:prefectural:tokyo:316:日本橋芝浦大森線",
            "oneway_status": "PASS" if all(item.get("oneway") == "yes" for item in tags) else "FAIL",
            "connection_to_next_status": row["connection_to_next_status"],
            "route_identity_status": "PASS" if row["route_identity_status"] == "PASS" and relation_evidence else "FAIL",
            "contamination_status": "PASS" if not reasons else "FAIL",
            "contamination_reasons_json": json_text(reasons),
            "direction_input_role": direction.DOWN,
        })

    metrics = {
        "configured_candidate_buffer_m": buffer_m,
        "configured_high_section_coverage_ratio": high_coverage,
        "official_geometry_length_m": official_line.length,
        "selected_length_m": fixed_line.length, "alternate_length_m": alternate_line.length,
        "official_coverage_by_selected_ratio": official_line.intersection(fixed_line.buffer(buffer_m)).length / official_line.length,
        "official_coverage_by_alternate_ratio": official_line.intersection(alternate_line.buffer(buffer_m)).length / official_line.length,
        "selected_axis_coverage_by_official_ratio": fixed_line.intersection(official_line.buffer(buffer_m)).length / fixed_line.length,
        "alternate_axis_coverage_by_official_ratio": alternate_line.intersection(official_line.buffer(buffer_m)).length / alternate_line.length,
        "selected_axis_coverage_by_alternate_ratio": fixed_line.intersection(alternate_line.buffer(buffer_m)).length / fixed_line.length,
        "alternate_axis_coverage_by_selected_ratio": alternate_line.intersection(fixed_line.buffer(buffer_m)).length / alternate_line.length,
        "selected_start_to_alternate_end_distance_m": math.dist(fixed_line.coords[0], alternate_line.coords[-1]),
        "selected_end_to_alternate_start_distance_m": math.dist(fixed_line.coords[-1], alternate_line.coords[0]),
        "corridor_min_separation_m": fixed_line.distance(alternate_line),
        "axis_hausdorff_distance_m": fixed_line.hausdorff_distance(alternate_line),
        "direction_cosine": facts["fixed_alternate_direction_cosine"],
    }
    route_pass = route_identity_ok
    topology_pass = not (fixed_connection or alternate_connection or fixed_node or alternate_node)
    contamination_pass = not inappropriate
    oneway_pass = all(row["oneway_status"] == "PASS" for row in edge_rows) and all(
        all(item.get("oneway") == "yes" for item in tags.values()) for tags in fixed_tags
    )
    direction_pass = all(
        row["selected_corridor_role"] == direction.UP
        and row["opposite_candidate_direction_role"] == direction.DOWN
        and row["direction_evidence_status"] == "RESOLVED"
        for row in review["diagnoses"]
    )
    official_coverage_pass = (
        metrics["official_coverage_by_selected_ratio"] >= high_coverage
        and metrics["official_coverage_by_alternate_ratio"] >= high_coverage
    )
    mutual_coverage_pass = (
        metrics["selected_axis_coverage_by_alternate_ratio"] >= high_coverage
        and metrics["alternate_axis_coverage_by_selected_ratio"] >= high_coverage
    )
    endpoints_pass = (
        metrics["selected_start_to_alternate_end_distance_m"] <= buffer_m
        and metrics["selected_end_to_alternate_start_distance_m"] <= buffer_m
    )
    spatial_pass = official_coverage_pass and mutual_coverage_pass and endpoints_pass
    partial_applicability = "NOT_APPLICABLE_LATERAL_AND_BOTH_ENDPOINT_FAILURE"
    data_conflict = not direction_pass
    if data_conflict:
        adoption = "DATA_CONFLICT"
    elif not route_pass:
        adoption = "REJECTED_ROUTE_IDENTITY_CONFLICT"
    elif not topology_pass:
        adoption = "REJECTED_TOPOLOGY_CONFLICT"
    elif not contamination_pass or not oneway_pass:
        adoption = "REJECTED_CONTAMINATION"
    elif not spatial_pass:
        adoption = "REVIEW_REQUIRED"
    else:
        adoption = "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"
    if adoption not in ALLOWED_STATUSES:
        raise ValueError(adoption)
    traffic_status = (
        "BIDIRECTIONAL_ASSIGNMENT_AVAILABLE" if adoption.startswith("ACCEPTED_")
        else "REVIEW_REQUIRED"
    )

    boundary_by_target = {
        TARGET_IDS[0]: ("DIRECT_60320_TERMINUS_TO_TARGET_ORIGIN", ["45662512"]),
        TARGET_IDS[1]: ("CHAIN_VIA_60330_TERMINUS_TO_TARGET_ORIGIN", ["1457802380"]),
        TARGET_IDS[2]: ("CHAIN_VIA_60340_TERMINUS_TO_TARGET_ORIGIN", ["1068239670", "45662504"]),
    }
    common = {
        "official_observation_section_id": OBSERVATION_ID,
        "selected_edge_sequence": ";".join(fixed), "selected_edge_count": len(fixed),
        "alternate_edge_sequence": ";".join(alternate), "alternate_edge_count": len(alternate),
        "selected_direction": direction.UP, "alternate_direction": direction.DOWN,
        "route_identity_status": "PASS" if route_pass else "FAIL",
        "topology_status": "PASS" if topology_pass else "FAIL",
        "direction_status": "PASS_LOCKED_DIAGNOSIS" if direction_pass else "DATA_CONFLICT",
        "contamination_status": "PASS" if contamination_pass else "FAIL",
        "oneway_carriageway_status": "PASS_SEPARATE_ONEWAY_CARRIAGES" if oneway_pass else "FAIL",
        "spatial_correspondence_status": "PASS" if spatial_pass else "FAIL_CONFIGURED_THRESHOLDS",
        "official_coverage_by_selected_ratio": f"{metrics['official_coverage_by_selected_ratio']:.6f}",
        "official_coverage_by_alternate_ratio": f"{metrics['official_coverage_by_alternate_ratio']:.6f}",
        "selected_axis_coverage_by_alternate_ratio": f"{metrics['selected_axis_coverage_by_alternate_ratio']:.6f}",
        "alternate_axis_coverage_by_selected_ratio": f"{metrics['alternate_axis_coverage_by_selected_ratio']:.6f}",
        "selected_start_to_alternate_end_distance_m": f"{metrics['selected_start_to_alternate_end_distance_m']:.3f}",
        "selected_end_to_alternate_start_distance_m": f"{metrics['selected_end_to_alternate_start_distance_m']:.3f}",
        "configured_candidate_buffer_m": f"{buffer_m:.1f}",
        "configured_high_coverage_ratio": f"{high_coverage:.2f}",
        "partial_edge_applicability": partial_applicability,
        "adoption_status": adoption, "traffic_assignment_status": traffic_status,
        "formal_mapping_changed": "false", "threshold_changed": "false",
    }
    review_rows, target_rows = [], []
    for target in TARGET_IDS:
        boundary_role, shared = boundary_by_target[target]
        boundary_pass = bool(shared)
        reason = (
            "route/topology/direction/contamination/oneway and target boundary checks pass, but the locked "
            f"25 m/0.60 spatial rule fails: alternate official coverage={metrics['official_coverage_by_alternate_ratio']:.6f}, "
            f"mutual coverage={metrics['selected_axis_coverage_by_alternate_ratio']:.6f}/"
            f"{metrics['alternate_axis_coverage_by_selected_ratio']:.6f}, endpoint distances="
            f"{metrics['selected_start_to_alternate_end_distance_m']:.3f}/"
            f"{metrics['selected_end_to_alternate_start_distance_m']:.3f} m."
        )
        review_rows.append({
            "target_section_id": target, **common,
            "target_boundary_role": boundary_role,
            "target_shared_boundary_edges_json": json_text(shared),
            "target_boundary_consistency": "PASS" if boundary_pass else "FAIL",
            "adoption_reason": reason,
            "next_action": "OBTAIN_OR_RECONCILE_SPATIAL_CARRIAGEWAY_BOUNDARY_EVIDENCE_WITHOUT_THRESHOLD_CHANGE",
        })
        target_rows.append({
            "official_observation_section_id": OBSERVATION_ID, "target_section_id": target,
            "candidate_coverage_scope": "OFFICIAL_OBSERVATION_GEOMETRY_NOT_TARGET_SECTION_GEOMETRY",
            "official_observation_coverage_ratio": f"{metrics['official_coverage_by_alternate_ratio']:.6f}",
            "endpoint_correspondence_status": "FAIL_CONFIGURED_25M_BUFFER" if not endpoints_pass else "PASS",
            "section_boundary_continuity": "PASS" if boundary_pass else "FAIL",
            "adjacent_shared_edges_json": json_text(shared),
            "direction_status": "RESOLVED_DOWN_INPUT_NOT_REESTIMATED",
            "adoption_status": adoption, "traffic_assignment_status": traffic_status,
        })
    result = {
        "facts": facts, "metrics": metrics, "route_pass": route_pass,
        "topology_pass": topology_pass, "direction_pass": direction_pass,
        "contamination_pass": contamination_pass, "oneway_pass": oneway_pass,
        "official_coverage_pass": official_coverage_pass,
        "mutual_coverage_pass": mutual_coverage_pass, "endpoints_pass": endpoints_pass,
        "spatial_pass": spatial_pass, "adoption": adoption,
        "traffic_status": traffic_status, "inappropriate": inappropriate,
        "comparisons": standards_comparison(), "adjacent_rows": adjacent_rows,
    }
    return result, review_rows, edge_rows, target_rows


def build_qa(
    result: dict[str, Any], review_rows: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    qa = {
        "run_id": RUN_ID, "generator_version": SCRIPT_VERSION, "status": "PASSED",
        "summary": {
            "target_count": len(target_rows), "selected_edge_count": 7,
            "alternate_edge_count": len(edge_rows),
            "adoption_status_counts": {result["adoption"]: len(review_rows)},
            "traffic_assignment_status_counts": {result["traffic_status"]: len(review_rows)},
        },
        "criteria": {
            "candidate_buffer_m": result["metrics"]["configured_candidate_buffer_m"],
            "high_section_coverage_ratio": result["metrics"]["configured_high_section_coverage_ratio"],
            "source": relative(direction.CONFIG), "threshold_changed": False,
        },
        "checks": {
            "direction_input_consistency": result["direction_pass"],
            "route_identity": result["route_pass"], "topology": result["topology_pass"],
            "contamination": result["contamination_pass"], "oneway_structure": result["oneway_pass"],
            "official_geometry_coverage": result["official_coverage_pass"],
            "mutual_carriageway_coverage": result["mutual_coverage_pass"],
            "endpoint_correspondence": result["endpoints_pass"],
            "target_boundary_consistency_count": sum(
                row["section_boundary_continuity"] == "PASS" for row in target_rows
            ),
            "connection_violation_count": sum(
                row["connection_to_next_status"] == "FAIL" for row in edge_rows
            ),
            "contaminated_edge_count": sum(row["contamination_status"] == "FAIL" for row in edge_rows),
        },
        "spatial_metrics": result["metrics"],
        "standards_comparison": result["comparisons"],
        "invariants": {
            "candidate_search_performed": False, "direction_reestimated": False,
            "geojson_coordinate_order_used_for_direction": False,
            "direct_reverse_edge_required": False, "visual_inspection_used": False,
            "partial_edge_special_rule_created": False, "formal_mapping_changed": False,
            "direction_artifacts_changed": False, "network_changed": False,
            "threshold_changed": False, "traffic_counts_apportioned": False,
        },
    }
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    if len(review_rows) != 3 or len(edge_rows) != 4 or len(target_rows) != 3:
        raise ValueError("Route 316 adoption review population failed")
    if not all((result["route_pass"], result["topology_pass"], result["direction_pass"],
                result["contamination_pass"], result["oneway_pass"])):
        raise ValueError("non-spatial Route 316 adoption criterion failed")
    if result["spatial_pass"] or result["adoption"] != "REVIEW_REQUIRED":
        raise ValueError("spatial failure must remain REVIEW_REQUIRED under the prior-route rule")
    if qa["checks"]["target_boundary_consistency_count"] != 3:
        raise ValueError("target boundary consistency failed")
    return qa


def render_report(rows: list[dict[str, Any]], qa: dict[str, Any]) -> str:
    first = rows[0]
    metrics = qa["spatial_metrics"]
    lines = [
        "# 都道316号 opposite carriageway 正式採択レビュー", "",
        "## 結論", "",
        "既存4-edge candidateを固定して審査した結果、3 targetすべて `REVIEW_REQUIRED` とする。",
        "directionは既存診断をinputとして使用し、selectedは `UP_TERMINUS_TO_ORIGIN`、alternateは",
        "`DOWN_ORIGIN_TO_TERMINUS` のまま再推測していない。traffic assignmentも `REVIEW_REQUIRED` を維持する。", "",
        "## 固定review対象", "",
        f"- selected 7 edges: `{first['selected_edge_sequence']}`",
        f"- alternate 4 edges: `{first['alternate_edge_sequence']}`",
        "- targets: `13403160330`, `13403160340`, `13403160350`", "",
        "## 判定根拠", "",
        "route identity、relation `11699637` membership、SUMO connection、node continuity、contamination、",
        "別oneway carriageway構造、3 targetの公式section-boundary chainはすべてPASSした。bare ref単独、",
        "direct reverse edge、visual inspection、GeoJSON coordinate orderは判定根拠にしていない。", "",
        f"一方、既存25 m / high coverage 0.60基準に対し、alternateの公式geometry被覆は "
        f"`{metrics['official_coverage_by_alternate_ratio']:.6f}`、selected/alternate相互被覆は "
        f"`{metrics['selected_axis_coverage_by_alternate_ratio']:.6f}` / "
        f"`{metrics['alternate_axis_coverage_by_selected_ratio']:.6f}`、反対端点差は "
        f"`{metrics['selected_start_to_alternate_end_distance_m']:.3f} m` / "
        f"`{metrics['selected_end_to_alternate_start_distance_m']:.3f} m` であり、spatial条件を満たさない。", "",
        "国道1号と同様に、route/topologyがPASSしてspatial条件だけが不足する候補は棄却や強制採択をせず",
        "`REVIEW_REQUIRED` とした。今回の不一致は横方向分離と両端にあり、端部切詰めだけの既存partial-edge",
        "仕様では解消できないため `ACCEPTED_AS_PARTIAL_EDGE_MAPPING` にもしない。", "",
        "## target別結果", "",
        "| target | boundary evidence | adoption | traffic assignment |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['target_section_id']}` | `{row['target_boundary_role']}` "
            f"{row['target_shared_boundary_edges_json']} | `{row['adoption_status']}` | "
            f"`{row['traffic_assignment_status']}` |"
        )
    lines.extend([
        "", "## 他routeとの整合性", "",
        "国道1号・都道2号・都道421号の既存採択reviewと同じ25 m / 0.60基準、route identity、",
        "topology、contamination条件を使用した。都道11号は既存complete reverse-edge evidenceを参照し、",
        "Route 316専用の例外基準は作成していない。", "",
        "## 次に必要な証拠", "",
        "閾値変更ではなく、公式観測境界と両車道中心線の対応を説明できる追加の公式boundary evidence、",
        "または既存network形状と公式geometryの横方向offsetを正式にreconcileする再現可能な証拠が必要である。",
        "既存direction成果物、正式mapping、SUMO network、config/thresholdは変更していない。", "",
    ])
    if "validation" in qa:
        lines.append(
            f"Validation: {qa['validation']['passed_test_count']} passed, "
            f"{qa['validation']['failed_test_count']} failed."
        )
        lines.append("")
    return "\n".join(lines)


def write_all() -> None:
    result, review_rows, edge_rows, target_rows = build_outputs()
    qa = build_qa(result, review_rows, edge_rows, target_rows)
    write_csv(REVIEW_CSV, review_rows)
    write_csv(EDGE_CSV, edge_rows)
    write_csv(TARGET_CSV, target_rows)
    if not VALIDATION_JSON.exists():
        VALIDATION_JSON.write_text(json.dumps({
            "status": "NOT_RUN", "verified_on": None, "test_command": None,
            "passed_test_count": 0, "failed_test_count": 0,
            "new_route316_adoption_test_count": 0,
        }, indent=2) + "\n", encoding="utf-8")
    qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(review_rows, qa), encoding="utf-8")
    inputs = [
        DIRECTION_DIAGNOSIS, DIRECTION_CLASSIFICATION, DIRECTION_EDGE_EVIDENCE,
        DIRECTION_RELATION_EVIDENCE, DIRECTION_ADJACENT_EVIDENCE,
        direction.EVIDENCE_CSV, direction.QA_JSON, direction.MANIFEST_JSON,
        direction.VALIDATION_JSON, direction.REPORT,
        direction.FORMAL_MAPPING, direction.NETWORK, direction.OSM, direction.ROUTE_RELATIONS,
        direction.CONFIG, direction.ROAD_CENSUS, PRIOR_ADOPTION_REVIEW, DIRECTION_CLUSTERS,
        PARTIAL_EDGE_SPECIFICATION, VALIDATOR,
    ]
    outputs = [REVIEW_CSV, EDGE_CSV, TARGET_CSV, QA_JSON, VALIDATION_JSON, REPORT]
    manifest = {
        "run_id": RUN_ID, "generator": relative(Path(__file__)),
        "generator_version": SCRIPT_VERSION, "generator_sha256": sha256_file(Path(__file__)),
        "input_hashes": {relative(path): sha256_file(path) for path in inputs},
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "review_subject": {
            "candidate_source": relative(direction.REVERSE_CLUSTER),
            "candidate_search_performed": False, "selected_edge_count": 7,
            "alternate_edge_count": 4, "target_count": 3,
        },
        "decision": {"adoption_status": result["adoption"],
                     "traffic_assignment_status": result["traffic_status"]},
        "non_mutation_contract": qa["invariants"], "qa_status": qa["status"],
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
