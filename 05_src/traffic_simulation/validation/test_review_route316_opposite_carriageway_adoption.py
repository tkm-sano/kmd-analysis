from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import review_route316_opposite_carriageway_adoption as subject
from traffic_simulation.validation import validate_route316_opposite_carriageway_adoption as validator


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_target_count_is_three_and_review_is_target_specific() -> None:
    rows = read_csv(subject.REVIEW_CSV)
    assert len(rows) == 3
    assert {row["target_section_id"] for row in rows} == set(subject.TARGET_IDS)
    assert len({row["target_boundary_role"] for row in rows}) == 3


def test_locked_selected_corridor_has_seven_edges() -> None:
    rows = read_csv(subject.REVIEW_CSV)
    assert all(int(row["selected_edge_count"]) == 7 for row in rows)
    assert all(row["selected_edge_sequence"].split(";") == [
        "45662502", "45662510#0", "45662510#1", "45662510#2",
        "45662510#3", "45662510#4", "45662510#5",
    ] for row in rows)


def test_locked_alternate_candidate_has_four_edges_without_new_search() -> None:
    rows = read_csv(subject.REVIEW_CSV)
    assert all(int(row["alternate_edge_count"]) == 4 for row in rows)
    assert all(row["alternate_edge_sequence"].split(";") == [
        "652322551#0", "652322551#1", "652322551#2", "45662512",
    ] for row in rows)
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["invariants"]["candidate_search_performed"] is False


def test_direction_is_consistent_input_and_not_reestimated() -> None:
    rows = read_csv(subject.REVIEW_CSV)
    assert all(row["selected_direction"] == "UP_TERMINUS_TO_ORIGIN" for row in rows)
    assert all(row["alternate_direction"] == "DOWN_ORIGIN_TO_TERMINUS" for row in rows)
    assert all(row["direction_status"] == "PASS_LOCKED_DIAGNOSIS" for row in rows)
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["invariants"]["direction_reestimated"] is False


def test_candidate_topology_is_continuous_by_nodes_and_connections() -> None:
    rows = read_csv(subject.EDGE_CSV)
    assert all(row["connection_to_next_status"] in {"PASS", "LAST_EDGE"} for row in rows)
    assert all(row["topology_status"] == "PASS" for row in read_csv(subject.REVIEW_CSV))
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["checks"]["connection_violation_count"] == 0


def test_route_identity_uses_relation_name_network_and_ref() -> None:
    rows = read_csv(subject.EDGE_CSV)
    assert {row["relation_id"] for row in rows} == {"11699637"}
    assert {row["canonical_route_identity"] for row in rows} == {
        "JP:prefectural:tokyo:316:日本橋芝浦大森線"
    }
    assert all(json.loads(row["relation_membership_json"]) for row in rows)
    assert all(row["route_identity_status"] == "PASS" for row in rows)


def test_candidate_has_no_contamination_and_is_separate_oneway_carriageway() -> None:
    edges = read_csv(subject.EDGE_CSV)
    assert all(row["contamination_status"] == "PASS" for row in edges)
    assert all(json.loads(row["contamination_reasons_json"]) == [] for row in edges)
    assert all(row["oneway_status"] == "PASS" for row in edges)
    assert all(not row["sumo_type"].endswith("_link") and row["sumo_function"] != "internal"
               for row in edges)


def test_spatial_coverage_fails_unchanged_prior_route_thresholds() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    metrics = qa["spatial_metrics"]
    assert qa["criteria"]["candidate_buffer_m"] == 25.0
    assert qa["criteria"]["high_section_coverage_ratio"] == 0.60
    assert metrics["official_coverage_by_selected_ratio"] >= 0.60
    assert metrics["official_coverage_by_alternate_ratio"] < 0.60
    assert metrics["selected_axis_coverage_by_alternate_ratio"] < 0.60
    assert metrics["alternate_axis_coverage_by_selected_ratio"] < 0.60
    assert qa["invariants"]["threshold_changed"] is False


def test_endpoint_correspondence_fails_both_25m_checks() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    metrics = qa["spatial_metrics"]
    assert metrics["selected_start_to_alternate_end_distance_m"] > 25.0
    assert metrics["selected_end_to_alternate_start_distance_m"] > 25.0
    assert qa["checks"]["endpoint_correspondence"] is False
    assert all(row["partial_edge_applicability"] ==
               "NOT_APPLICABLE_LATERAL_AND_BOTH_ENDPOINT_FAILURE"
               for row in read_csv(subject.REVIEW_CSV))


def test_all_target_boundaries_are_consistent_but_not_collapsed() -> None:
    rows = read_csv(subject.TARGET_CSV)
    expected = {
        "13403160330": ["45662512"],
        "13403160340": ["1457802380"],
        "13403160350": ["1068239670", "45662504"],
    }
    assert {row["target_section_id"]: json.loads(row["adjacent_shared_edges_json"])
            for row in rows} == expected
    assert all(row["section_boundary_continuity"] == "PASS" for row in rows)
    assert all(row["candidate_coverage_scope"] ==
               "OFFICIAL_OBSERVATION_GEOMETRY_NOT_TARGET_SECTION_GEOMETRY" for row in rows)


def test_adoption_and_traffic_assignment_remain_review_required() -> None:
    review = read_csv(subject.REVIEW_CSV)
    targets = read_csv(subject.TARGET_CSV)
    assert all(row["adoption_status"] == "REVIEW_REQUIRED" for row in review + targets)
    assert all(row["traffic_assignment_status"] == "REVIEW_REQUIRED" for row in review + targets)
    assert all(row["formal_mapping_changed"] == "false" for row in review)
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["summary"]["adoption_status_counts"] == {"REVIEW_REQUIRED": 3}
    assert qa["summary"]["traffic_assignment_status_counts"] == {"REVIEW_REQUIRED": 3}


def test_manifest_hashes_validator_and_regeneration_are_consistent() -> None:
    assert validator.validate()["status"] == "PASSED"
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    locked = [subject.REPOSITORY_ROOT / path for path in manifest["input_hashes"]]
    outputs = [subject.REPOSITORY_ROOT / path for path in manifest["output_hashes"]]
    before_locked = {path: sha256(path) for path in locked}
    before_outputs = {path: sha256(path) for path in outputs}
    subprocess.run([sys.executable, str(Path(subject.__file__))],
                   cwd=subject.REPOSITORY_ROOT, check=True)
    assert {path: sha256(path) for path in locked} == before_locked
    assert {path: sha256(path) for path in outputs} == before_outputs
    assert validator.validate()["status"] == "PASSED"
