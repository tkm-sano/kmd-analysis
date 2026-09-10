"""Review previously extracted opposite carriageways without changing mappings."""

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
import xml.etree.ElementTree as ET

from shapely.geometry import LineString
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


SCRIPT_VERSION = "1.0.0"
RUN_ID = "external_observation_opposite_carriageway_adoption_review_20260827_v1"
DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
TARGET_SOURCE = DATA_DIR / "external_observation_reverse_gap_target_summary.csv"
GAP_CLUSTERS = DATA_DIR / "external_observation_reverse_gap_cluster_classification.csv"
DIRECTION_CLUSTERS = DATA_DIR / "external_observation_direction_cluster_evidence.csv"
FORMAL_MAPPING = DATA_DIR / "external_observation_final_mapping.csv"
BASE_MAPPING = DATA_DIR / "census_section_final_mapping.csv"
CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
BASE_OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_baseline_explicit_v17_oneway.osm.xml"
)
EXTENSION_OSM = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1/ota_ward_external_extension_20260827_v1.osm.xml"
)
PREWORK = DATA_DIR / "external_observation_opposite_carriageway_adoption_prework_20260827.json"

REVIEW_CSV = DATA_DIR / "external_observation_opposite_carriageway_adoption_review.csv"
EDGE_CSV = DATA_DIR / "external_observation_opposite_carriageway_adoption_edge_evidence.csv"
QA_JSON = DATA_DIR / "external_observation_opposite_carriageway_adoption_qa.json"
MANIFEST_JSON = DATA_DIR / "external_observation_opposite_carriageway_adoption_manifest.json"
VALIDATION_JSON = DATA_DIR / "external_observation_opposite_carriageway_adoption_validation.json"
REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_opposite_carriageway_adoption_review.md"

ALLOWED_STATUSES = {
    "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY",
    "REVIEW_REQUIRED",
    "REJECTED_ROUTE_MISMATCH",
    "REJECTED_TOPOLOGY",
    "REJECTED_COVERAGE",
    "UNRESOLVED",
}
UP = "UP_TERMINUS_TO_ORIGIN"
DOWN = "DOWN_ORIGIN_TO_TERMINUS"


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPOSITORY_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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


def verify_prework() -> dict[str, Any]:
    snapshot = json.loads(PREWORK.read_text(encoding="utf-8"))
    for path_text, expected in snapshot["sha256"].items():
        if sha256_file(REPOSITORY_ROOT / path_text) != expected:
            raise ValueError(f"locked pre-work input changed: {path_text}")
    if snapshot["validation_baseline"]["passed_test_count"] != 84:
        raise ValueError("pre-work validation baseline is not 84")
    return snapshot


def extract_targets() -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    targets = [
        row for row in read_csv(TARGET_SOURCE)
        if row["resolution_category"] == "MAPPING_ONLY_REVIEW_REQUIRED"
    ]
    gap_clusters = {
        row["official_observation_section_id"]: row for row in read_csv(GAP_CLUSTERS)
    }
    direction_clusters = {
        row["official_observation_section_id"]: row for row in read_csv(DIRECTION_CLUSTERS)
    }
    observations = {row["official_observation_section_id"] for row in targets}
    if len(targets) != 3 or len(observations) != 3:
        raise ValueError("canonical adoption-review population is not three targets")
    if "13403160320" in observations:
        raise ValueError("direction-unresolved Route 316 must remain outside adoption review")
    excluded = gap_clusters["13403160320"]
    if excluded["resolution_category"] != "HOLD_DIRECTION_UNRESOLVED":
        raise ValueError("Route 316 exclusion reason changed")
    return sorted(targets, key=lambda row: row["official_observation_section_id"]), gap_clusters, direction_clusters


def parse_shape(text: str) -> list[tuple[float, float]]:
    return [tuple(map(float, point.split(","))) for point in text.split()]


def edge_orig_ids(element: ET.Element) -> list[str]:
    return sorted({
        source
        for lane in element.findall("lane")
        for param in lane.findall("param")
        if param.get("key") == "origId"
        for source in param.get("value", "").split()
        if source
    })


def parse_network(path: Path, required: set[str], sequences: list[list[str]]) -> dict[str, Any]:
    metadata: dict[str, dict[str, Any]] = {}
    expected_connections = {
        pair for sequence in sequences for pair in zip(sequence, sequence[1:])
    }
    connections: set[tuple[str, str]] = set()
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "edge":
            edge_id = element.get("id", "")
            if edge_id in required:
                lane = element.find("lane")
                if lane is None:
                    raise ValueError(f"edge has no lane: {edge_id}")
                metadata[edge_id] = {
                    "from": element.get("from", ""),
                    "to": element.get("to", ""),
                    "function": element.get("function", ""),
                    "type": element.get("type", ""),
                    "length": float(lane.get("length", "0")),
                    "shape": parse_shape(lane.get("shape", "")),
                    "allow": lane.get("allow", ""),
                    "orig_ids": edge_orig_ids(element),
                }
            element.clear()
        elif element.tag == "connection":
            pair = (element.get("from", ""), element.get("to", ""))
            if pair in expected_connections:
                connections.add(pair)
            element.clear()
    missing = required - set(metadata)
    if missing:
        raise ValueError(f"review edge absent from SUMO: {sorted(missing)}")
    return {"metadata": metadata, "connections": connections}


def parse_osm(path: Path, wanted: set[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag != "way":
            continue
        way_id = element.get("id", "")
        if way_id in wanted:
            result[way_id] = {
                tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
            }
        element.clear()
    return result


def combined_line(sequence: list[str], metadata: dict[str, dict[str, Any]]) -> LineString:
    coordinates: list[tuple[float, float]] = []
    for edge_id in sequence:
        shape = metadata[edge_id]["shape"]
        coordinates.extend(shape[1:] if coordinates and coordinates[-1] == shape[0] else shape)
    return LineString(coordinates)


def topology_violations(
    sequence: list[str], metadata: dict[str, dict[str, Any]], connections: set[tuple[str, str]]
) -> tuple[list[list[str]], list[list[str]]]:
    node = [
        [left, right] for left, right in zip(sequence, sequence[1:])
        if metadata[left]["to"] != metadata[right]["from"]
    ]
    connection = [
        [left, right] for left, right in zip(sequence, sequence[1:])
        if (left, right) not in connections
    ]
    return node, connection


def build_opposite_sequence(slots: list[str], alternate: list[str]) -> tuple[list[str], int]:
    result: list[str] = []
    inserted = False
    preserved = 0
    for edge_id in slots:
        if edge_id:
            result.append(edge_id)
            preserved += 1
        elif not inserted:
            result.extend(alternate)
            inserted = True
    if not inserted:
        raise ValueError("canonical reverse slots contain no gap")
    return result, preserved


def build_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    targets, gap_clusters, direction_clusters = extract_targets()
    formal = {}
    for row in read_csv(FORMAL_MAPPING):
        formal.setdefault(row["official_observation_section_id"], row)
    with CONFIG.open(encoding="utf-8") as handle:
        matching = yaml.safe_load(handle)["matching"]
    buffer_m = float(matching["candidate_buffer_m"])
    high_coverage = float(matching["high_section_coverage_ratio"])

    review_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    for target in targets:
        observation = target["official_observation_section_id"]
        gap = gap_clusters[observation]
        direction = direction_clusters[observation]
        fixed = direction["adopted_edge_sequence"].split(";")
        alternate = json.loads(gap["alternate_reverse_corridor_json"])
        slots = json.loads(direction["reverse_edge_slots_json"])
        opposite, preserved = build_opposite_sequence(slots, alternate)
        network = REPOSITORY_ROOT / gap["network_file"]
        parsed = parse_network(network, set(fixed + opposite), [fixed, alternate, opposite])
        metadata = parsed["metadata"]
        candidate_node_violations, candidate_connection_violations = topology_violations(
            alternate, metadata, parsed["connections"]
        )
        opposite_node_violations, opposite_connection_violations = topology_violations(
            opposite, metadata, parsed["connections"]
        )

        osm_path = EXTENSION_OSM if observation == "13300010260" else BASE_OSM
        candidate_orig = {
            orig for edge_id in alternate for orig in metadata[edge_id]["orig_ids"]
        }
        fixed_orig = {orig for edge_id in fixed for orig in metadata[edge_id]["orig_ids"]}
        osm = parse_osm(osm_path, candidate_orig | fixed_orig)
        fixed_names = {
            osm[orig].get("name", "") or osm[orig].get("name:ja", "") for orig in fixed_orig
        }
        candidate_names = {
            osm[orig].get("name", "") or osm[orig].get("name:ja", "") for orig in candidate_orig
        }
        candidate_refs = {osm[orig].get("ref", "") for orig in candidate_orig}
        fixed_refs = {osm[orig].get("ref", "") for orig in fixed_orig}
        route_identity_ok = (
            candidate_orig <= set(osm)
            and fixed_orig <= set(osm)
            and candidate_names == fixed_names
            and candidate_refs == fixed_refs == {direction["route_number"]}
        )
        relation_status = gap["route_relation_status"]
        relation_ok = relation_status in {
            "SUPPORTED_SAME_ROUTE_NETWORK_REF_MEMBER",
            "NO_ROUTE_RELATION_OSM_REF_NAME_SUPPORT",
        }

        inappropriate = []
        for edge_id in alternate:
            item = metadata[edge_id]
            tags = [osm[orig] for orig in item["orig_ids"]]
            highways = {tag.get("highway", "") for tag in tags}
            if (
                edge_id.startswith(":")
                or item["function"] == "internal"
                or item["type"].endswith("_link")
                or any(highway.endswith("_link") for highway in highways)
                or any(tag.get("ref", "") != direction["route_number"] for tag in tags)
                or any((tag.get("name", "") or tag.get("name:ja", "")) not in fixed_names for tag in tags)
            ):
                inappropriate.append(edge_id)

        fixed_line = combined_line(fixed, metadata)
        opposite_line = combined_line(opposite, metadata)
        fixed_axis_coverage = fixed_line.intersection(opposite_line.buffer(buffer_m)).length / fixed_line.length
        opposite_axis_coverage = opposite_line.intersection(fixed_line.buffer(buffer_m)).length / opposite_line.length
        length_ratio = opposite_line.length / fixed_line.length
        fixed_start = metadata[fixed[0]]["shape"][0]
        fixed_end = metadata[fixed[-1]]["shape"][-1]
        opposite_start = metadata[opposite[0]]["shape"][0]
        opposite_end = metadata[opposite[-1]]["shape"][-1]
        origin_end_distance = math.dist(fixed_start, opposite_end)
        terminus_end_distance = math.dist(fixed_end, opposite_start)
        coverage_ok = (
            fixed_axis_coverage >= high_coverage
            and opposite_axis_coverage >= high_coverage
        )
        endpoints_ok = (
            origin_end_distance <= buffer_m and terminus_end_distance <= buffer_m
        )
        topology_ok = not (
            candidate_node_violations or candidate_connection_violations
            or opposite_node_violations or opposite_connection_violations
        )
        fixed_direction = direction["adopted_sequence_role"]
        direction_ok = direction["direction_evidence_status"] == "RESOLVED" and fixed_direction == DOWN

        if not route_identity_ok or not relation_ok:
            adoption = "REJECTED_ROUTE_MISMATCH"
        elif not topology_ok or inappropriate:
            adoption = "REJECTED_TOPOLOGY"
        elif not direction_ok:
            adoption = "UNRESOLVED"
        elif not coverage_ok or not endpoints_ok:
            adoption = "REVIEW_REQUIRED"
        else:
            adoption = "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"
        if adoption not in ALLOWED_STATUSES:
            raise ValueError(adoption)

        accepted = adoption == "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"
        coverage_status = (
            "PASS_CONFIGURED_BUFFER_AND_HIGH_COVERAGE"
            if coverage_ok and endpoints_ok
            else "REVIEW_REQUIRED_ASYMMETRIC_COVERAGE_OR_ENDPOINT_MISMATCH"
        )
        endpoint_status = (
            "PASS_OPPOSITE_ENDPOINTS_WITHIN_CONFIGURED_BUFFER"
            if endpoints_ok else "MAJOR_ENDPOINT_MISMATCH"
        )
        reason = (
            "OSM name/refとroute evidenceが同一路線を支持し、mainlineのみで連続する。"
            if route_identity_ok and relation_ok and topology_ok and not inappropriate
            else "route identityまたはtopology条件を満たさない。"
        )
        if accepted:
            reason += " 既存25 m bufferとhigh coverage 60%を両方向で満たし、固定DOWN列の反対方向UPへ一意に採択した。"
        elif adoption == "REVIEW_REQUIRED":
            reason += (
                f" 候補側coverage={opposite_axis_coverage:.4f}、反対端点最大差="
                f"{max(origin_end_distance, terminus_end_distance):.2f} mのため、候補列を変更せずREVIEW_REQUIREDとした。"
            )

        route_identity_evidence = {
            "canonical_route_system": direction["route_system"],
            "canonical_route_number": direction["route_number"],
            "canonical_route_name": direction["route_name"],
            "fixed_osm_names": sorted(fixed_names),
            "alternate_osm_names": sorted(candidate_names),
            "fixed_osm_refs": sorted(fixed_refs),
            "alternate_osm_refs": sorted(candidate_refs),
            "route_relation_id": direction["route_relation_id"],
            "route_relation_status": relation_status,
            "fixed_relation_evidence": json.loads(gap["route_relation_fixed_evidence_json"]),
            "alternate_relation_evidence": json.loads(gap["route_relation_alternate_evidence_json"]),
        }
        review_rows.append({
            "official_observation_section_id": observation,
            "target_section_id": target["target_section_id"],
            "route": f"{direction['route_system']}:{direction['route_number']}",
            "cluster": direction["cluster"],
            "fixed_edge_sequence": ";".join(fixed),
            "fixed_direction": fixed_direction,
            "alternate_carriageway_edge_sequence": ";".join(alternate),
            "alternate_direction": UP,
            "preserved_existing_reverse_edge_count": preserved,
            "opposite_composite_edge_count": len(opposite),
            "route_identity_evidence": json_text(route_identity_evidence),
            "route_identity_status": "CONFIRMED" if route_identity_ok and relation_ok else "NOT_CONFIRMED",
            "topology_status": "CONNECTED" if topology_ok else "INVALID",
            "candidate_connection_violation_count": len(candidate_connection_violations),
            "opposite_composite_connection_violation_count": len(opposite_connection_violations),
            "inappropriate_edge_ids_json": json_text(inappropriate),
            "coverage_status": coverage_status,
            "configured_candidate_buffer_m": f"{buffer_m:.1f}",
            "configured_high_section_coverage_ratio": f"{high_coverage:.2f}",
            "fixed_axis_coverage_by_opposite_ratio": f"{fixed_axis_coverage:.6f}",
            "opposite_axis_coverage_by_fixed_ratio": f"{opposite_axis_coverage:.6f}",
            "opposite_to_fixed_length_ratio": f"{length_ratio:.6f}",
            "axis_hausdorff_distance_m": f"{fixed_line.hausdorff_distance(opposite_line):.3f}",
            "endpoint_correspondence": endpoint_status,
            "fixed_start_to_opposite_end_distance_m": f"{origin_end_distance:.3f}",
            "fixed_end_to_opposite_start_distance_m": f"{terminus_end_distance:.3f}",
            "connection_violation_count": len(opposite_connection_violations),
            "adoption_status": adoption,
            "adoption_reason": reason,
            "up_sumo_edge_sequence": ";".join(opposite) if accepted else "",
            "down_sumo_edge_sequence": ";".join(fixed),
            "bidirectional_traffic_assignment_status": "BIDIRECTIONAL_ASSIGNABLE" if accepted else "NOT_YET_ASSIGNABLE",
            "evidence_source": json_text([
                relative(TARGET_SOURCE), relative(GAP_CLUSTERS), relative(DIRECTION_CLUSTERS),
                relative(network), relative(osm_path), relative(CONFIG),
            ]),
            "provenance": json_text({
                "generator": relative(Path(__file__)),
                "generator_version": SCRIPT_VERSION,
                "network_sha256": sha256_file(network),
                "osm_sha256": sha256_file(osm_path),
                "config_sha256": sha256_file(CONFIG),
                "candidate_source_immutable": True,
                "formal_mapping_mutated": False,
            }),
        })

        for order, edge_id in enumerate(alternate, start=1):
            item = metadata[edge_id]
            tags = {orig: osm[orig] for orig in item["orig_ids"]}
            edge_rows.append({
                "official_observation_section_id": observation,
                "alternate_sequence_order": order,
                "edge_id": edge_id,
                "sumo_from": item["from"],
                "sumo_to": item["to"],
                "sumo_type": item["type"],
                "sumo_function": item["function"],
                "orig_ids_json": json_text(item["orig_ids"]),
                "osm_tags_json": json_text(tags),
                "mainline_edge_status": "PASS" if edge_id not in inappropriate else "FAIL",
                "route_number": direction["route_number"],
                "adoption_status": adoption,
            })
    return review_rows, edge_rows


def build_qa(review_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(row["adoption_status"] for row in review_rows)
    qa: dict[str, Any] = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "target_selection": {
            "source": relative(TARGET_SOURCE),
            "predicate": "resolution_category=MAPPING_ONLY_REVIEW_REQUIRED",
            "target_count": len(review_rows),
            "manual_target_ids_used": False,
            "route_316_excluded": True,
        },
        "summary": {
            "accepted": statuses.get("ACCEPTED_AS_OPPOSITE_CARRIAGEWAY", 0),
            "review_required": statuses.get("REVIEW_REQUIRED", 0),
            "rejected": sum(count for status, count in statuses.items() if status.startswith("REJECTED_")),
            "unresolved": statuses.get("UNRESOLVED", 0),
            "bidirectional_assignable_after_adoption": sum(
                row["bidirectional_traffic_assignment_status"] == "BIDIRECTIONAL_ASSIGNABLE"
                for row in review_rows
            ),
        },
        "invariants": {
            "review_row_count": len(review_rows),
            "alternate_edge_evidence_count": len(edge_rows),
            "connection_violation_count": sum(int(row["connection_violation_count"]) for row in review_rows),
            "inappropriate_edge_count": sum(len(json.loads(row["inappropriate_edge_ids_json"])) for row in review_rows),
            "route_421_preserved_exact_reverse_count": next(
                int(row["preserved_existing_reverse_edge_count"])
                for row in review_rows if row["official_observation_section_id"] == "13604210030"
            ),
            "mapping_changed": False,
            "base_mapping_changed": False,
            "network_changed": False,
            "config_or_thresholds_changed": False,
            "source_data_changed": False,
        },
    }
    if VALIDATION_JSON.is_file():
        qa["validation"] = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    if len(review_rows) != 3 or len(edge_rows) != 71:
        raise ValueError("adoption review completeness failed")
    if qa["invariants"]["connection_violation_count"] or qa["invariants"]["inappropriate_edge_count"]:
        raise ValueError("adoption topology/mainline QA failed")
    if qa["invariants"]["route_421_preserved_exact_reverse_count"] != 67:
        raise ValueError("Route 421 existing reverse evidence changed")
    return qa


def render_report(rows: list[dict[str, Any]], qa: dict[str, Any]) -> str:
    lines = [
        "# 外部観測参照 opposite carriageway 正式採択レビュー",
        "",
        "既存mappingを更新せず、前回抽出済みalternate候補だけを正式採択レビューした。",
        "",
        "| 観測区間 | fixed | alternate/composite | coverage | endpoint最大差 | 判定 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        endpoint_max = max(
            float(row["fixed_start_to_opposite_end_distance_m"]),
            float(row["fixed_end_to_opposite_start_distance_m"]),
        )
        lines.append(
            f"| `{row['official_observation_section_id']}` | `{row['fixed_direction']}` | "
            f"{len(row['alternate_carriageway_edge_sequence'].split(';'))}/{row['opposite_composite_edge_count']} edge | "
            f"{row['fixed_axis_coverage_by_opposite_ratio']}/{row['opposite_axis_coverage_by_fixed_ratio']} | "
            f"{endpoint_max:.3f} m | `{row['adoption_status']}` |"
        )
    summary = qa["summary"]
    lines.extend([
        "",
        "国道1号の既抽出14-edge候補はroute identityとtopologyを満たすが、一端が約220 mオーバーランし、候補側の25 m相互被覆が既存high coverage 60%を下回る。候補を切り詰めず `REVIEW_REQUIRED` とした。",
        "",
        "都道421号は既存67 reverse edgeを同じ順序で保持し、欠損部へalternate 14 edgeを挿入した81-edge UP列として検証した。connection violationは0である。",
        "",
        "## Summary",
        "",
        f"- 正式採択: {summary['accepted']}",
        f"- REVIEW_REQUIRED: {summary['review_required']}",
        f"- REJECTED: {summary['rejected']}",
        f"- UNRESOLVED: {summary['unresolved']}",
        f"- 採択後に双方向交通量割当可能: {summary['bidirectional_assignable_after_adoption']}",
        "",
    ])
    if "validation" in qa:
        lines.append(
            f"Validation: {qa['validation']['passed_test_count']} passed, "
            f"{qa['validation']['failed_test_count']} failed."
        )
        lines.append("")
    return "\n".join(lines)


def write_all() -> None:
    snapshot = verify_prework()
    review_rows, edge_rows = build_outputs()
    qa = build_qa(review_rows, edge_rows)
    write_csv(REVIEW_CSV, review_rows)
    write_csv(EDGE_CSV, edge_rows)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(render_report(review_rows, qa), encoding="utf-8")
    outputs = [REVIEW_CSV, EDGE_CSV, QA_JSON, REPORT]
    if VALIDATION_JSON.is_file():
        outputs.append(VALIDATION_JSON)
    manifest = {
        "run_id": RUN_ID,
        "generator": relative(Path(__file__)),
        "generator_sha256": sha256_file(Path(__file__)),
        "generator_version": SCRIPT_VERSION,
        "git_base_commit": snapshot["git_base_commit"],
        "prework_snapshot": relative(PREWORK),
        "prework_snapshot_sha256": sha256_file(PREWORK),
        "input_hashes": snapshot["sha256"],
        "output_hashes": {relative(path): sha256_file(path) for path in outputs},
        "qa": qa,
        "non_mutation_contract": {
            "formal_mapping_changed": False,
            "base_mapping_changed": False,
            "selected_edges_changed": False,
            "network_changed": False,
            "config_or_thresholds_changed": False,
            "source_data_changed": False,
        },
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()


if __name__ == "__main__":
    main()
