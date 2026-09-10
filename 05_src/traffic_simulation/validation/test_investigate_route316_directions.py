from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import investigate_route316_directions as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_prior_direct_cause_is_preserved_as_evidence_gap_not_conflict() -> None:
    rows = read_csv(subject.CLASSIFICATION_CSV)
    assert len(rows) == 3
    assert {row["target_section_id"] for row in rows} == set(subject.TARGET_IDS)
    assert all(row["prior_direction_evidence_status"] == "UNRESOLVED" for row in rows)
    assert all(row["prior_reason_code"] == "OFFICIAL_ENDPOINT_NOT_ANCHORED_TO_FIXED_EDGE_ENDPOINT"
               for row in rows)
    assert all(row["evidence_gap_or_conflict"] == "PRIOR_EVIDENCE_GAP_NO_CONFLICT"
               for row in rows)


def test_official_direction_definition_and_route_endpoints_are_recorded() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    official = qa["official_route_inventory"]
    assert official["route_number"] == "316"
    assert official["route_name"] == "日本橋芝浦大森線"
    assert official["origin"] == "中央区日本橋本町三丁目"
    assert official["terminus"] == "大田区大森南一丁目"
    assert official["sha256"] == subject.TOKYO_ROUTE_INVENTORY_SHA256
    assert all(row["official_definition"] == "UP=TERMINUS_TO_ORIGIN;DOWN=ORIGIN_TO_TERMINUS"
               for row in read_csv(subject.CLASSIFICATION_CSV))


def test_fixed_and_alternate_corridors_are_connected_and_complete() -> None:
    rows = read_csv(subject.EDGE_CSV)
    fixed = [row for row in rows if row["corridor_role"] == "FIXED_7_EDGE"]
    alternate = [row for row in rows if row["corridor_role"] == "ALTERNATE_4_EDGE"]
    assert [row["edge_id"] for row in fixed] == [
        "45662502", "45662510#0", "45662510#1", "45662510#2",
        "45662510#3", "45662510#4", "45662510#5",
    ]
    assert [row["edge_id"] for row in alternate] == [
        "652322551#0", "652322551#1", "652322551#2", "45662512",
    ]
    assert all(row["connection_to_next_status"] in {"PASS", "LAST_EDGE"}
               for row in fixed + alternate)
    assert all(row["route_identity_status"] == "PASS" for row in fixed + alternate)
    assert all(row["edge_type_status"] == "PASS" for row in fixed + alternate)


def test_route_relation_supports_identity_but_not_direction_alone() -> None:
    rows = read_csv(subject.RELATION_CSV)
    relevant = [row for row in rows if row["corridor_role"] in {
        "FIXED_7_EDGE", "ALTERNATE_4_EDGE"
    }]
    assert {row["relation_id"] for row in relevant} == {"11699637"}
    assert {row["network"] for row in relevant} == {"JP:prefectural:tokyo"}
    assert {row["ref"] for row in relevant} == {"316"}
    assert {row["canonical_name"] for row in relevant} == {"日本橋芝浦大森線"}
    assert {row["operator"] for row in relevant} == {""}
    assert {row["member_role"] for row in relevant} == {""}
    assert {row["corridor_member_sequence_status"] for row in relevant} == {
        "CONTIGUOUS_DECREASING"
    }
    assert all(row["direction_evidence_status"] ==
               "INSUFFICIENT_ALONE_EMPTY_ROLES_NO_DIRECTION_NOTE" for row in relevant)
    assert all(row["bare_numeric_ref_used_alone"] == "false" for row in relevant)


def test_official_adjacent_chain_has_exact_sumo_edge_overlaps() -> None:
    rows = read_csv(subject.ADJACENT_CSV)
    target_anchor = next(row for row in rows if row["evidence_status"] == "PASS_TARGET_BRANCH")
    assert target_anchor["left_section_id"] == subject.OBSERVATION_ID
    assert target_anchor["right_section_id"] == "13403160330"
    assert target_anchor["official_label_correspondence"] == "PASS"
    assert json.loads(target_anchor["shared_sumo_edges_json"]) == ["45662512"]
    chain = [row for row in rows if row["evidence_status"] == "PASS_TARGET_CHAIN"]
    assert len(chain) == 2
    assert [json.loads(row["shared_sumo_edges_json"]) for row in chain] == [
        ["1457802380"], ["1068239670", "45662504"],
    ]


def test_missing_origin_adjacent_and_competing_branch_are_not_hidden() -> None:
    rows = read_csv(subject.ADJACENT_CSV)
    missing = next(row for row in rows if row["right_section_id"] == "13403160400")
    assert missing["evidence_status"] == "MISSING_REFERENCED_CENSUS_ROW"
    assert missing["official_label_correspondence"] == "UNAVAILABLE"
    competing = next(row for row in rows if row["right_section_id"] == "13403160380")
    assert competing["official_label_correspondence"] == "PASS"
    assert competing["evidence_status"] == "COMPETING_BRANCH_NO_OVERLAP"
    assert json.loads(competing["shared_sumo_edges_json"]) == []


def test_all_three_targets_resolve_only_by_combined_evidence() -> None:
    rows = read_csv(subject.CLASSIFICATION_CSV)
    assert {row["final_classification"] for row in rows} == {
        "RESOLVED_BY_COMBINED_EVIDENCE"
    }
    assert {row["fixed_7_edge_direction_role"] for row in rows} == {
        "UP_TERMINUS_TO_ORIGIN"
    }
    assert {row["alternate_4_edge_direction_role"] for row in rows} == {
        "DOWN_ORIGIN_TO_TERMINUS"
    }
    assert all(row["route_relation_alone_sufficient"] == "false" for row in rows)
    assert all(row["adjacent_section_anchor_status"] == "PASS" for row in rows)
    assert all(row["evidence_conflict_status"] == "NONE" for row in rows)
    assert all(row["adoption_status"] == "DIAGNOSIS_ONLY_NOT_APPLIED_TO_FORMAL_MAPPING"
               for row in rows)


def test_required_evidence_ledger_has_explicit_support_and_limit_categories() -> None:
    rows = read_csv(subject.EVIDENCE_CSV)
    assert len(rows) == 30
    assert list(rows[0]) == [
        "target", "evidence_type", "source", "source_object_id", "evidence_value",
        "supports_up", "supports_down", "conflict_status", "notes",
    ]
    assert {row["target"] for row in rows} == set(subject.TARGET_IDS)
    assert {row["evidence_type"] for row in rows} == {
        "OFFICIAL_DIRECTION_EVIDENCE", "OFFICIAL_ROUTE_ENDPOINT_EVIDENCE",
        "OSM_ROUTE_RELATION_EVIDENCE", "TOPOLOGY_SUPPORTING_EVIDENCE",
        "GEOMETRY_SUPPORTING_EVIDENCE", "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE",
    }
    relation = [row for row in rows if row["evidence_type"] == "OSM_ROUTE_RELATION_EVIDENCE"]
    assert all(row["supports_up"] == row["supports_down"] == "false" for row in relation)
    assert all(row["conflict_status"] == "INSUFFICIENT_ALONE" for row in relation)
    conflicts = [row for row in rows if row["evidence_type"] == "CONFLICTING_EVIDENCE"]
    assert all(row["evidence_value"] == "NONE_FOUND" for row in conflicts)


def test_required_diagnosis_resolves_direction_but_not_traffic_assignment() -> None:
    rows = read_csv(subject.DIAGNOSIS_CSV)
    assert len(rows) == 3
    assert {row["target"] for row in rows} == set(subject.TARGET_IDS)
    assert all(row["current_status"] == "UNRESOLVED" for row in rows)
    assert all(row["proposed_direction_status"] == "RESOLVED_UP" for row in rows)
    assert all(row["selected_corridor_role"] == "UP_TERMINUS_TO_ORIGIN" for row in rows)
    assert all(row["direction_evidence_status"] == "RESOLVED" for row in rows)
    assert all(row["traffic_assignment_status"] == "REVIEW_REQUIRED" for row in rows)
    assert all(row["opposite_candidate_status"] ==
               "FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED" for row in rows)
    assert all(row["formal_mapping_changed"] == "false" for row in rows)


def test_geojson_order_and_mutations_are_prohibited() -> None:
    assert all(row["geojson_coordinate_order_used"] == "false"
               for row in read_csv(subject.ADJACENT_CSV))
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    invariants = qa["invariants"]
    assert invariants["geojson_coordinate_order_used"] is False
    assert invariants["formal_mapping_changed"] is False
    assert invariants["sumo_network_changed"] is False
    assert invariants["matching_threshold_changed"] is False
    assert invariants["route_relation_alone_used_for_direction"] is False


def test_qa_has_no_topology_identity_or_anchor_failures() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["status"] == "PASSED"
    assert qa["summary"]["target_count"] == 3
    assert qa["summary"]["fixed_edge_count"] == 7
    assert qa["summary"]["alternate_edge_count"] == 4
    assert qa["summary"]["final_classification_counts"] == {
        "RESOLVED_BY_COMBINED_EVIDENCE": 3
    }
    assert qa["summary"]["proposed_direction_status_counts"] == {"RESOLVED_UP": 3}
    assert qa["summary"]["direction_evidence_status_counts"] == {"RESOLVED": 3}
    assert qa["summary"]["traffic_assignment_status_counts"] == {"REVIEW_REQUIRED": 3}
    invariants = qa["invariants"]
    for key in (
        "fixed_connection_violation_count", "alternate_connection_violation_count",
        "edge_route_identity_failure_count", "edge_type_failure_count",
        "route_relation_identity_failure_count", "target_chain_anchor_failure_count",
    ):
        assert invariants[key] == 0
    assert invariants["target_chain_anchor_count"] == 3
    assert invariants["fixed_alternate_antiparallel"] is True
    assert invariants["opposite_candidate_formally_adopted"] is False
    assert invariants["direction_status_separated_from_traffic_assignment"] is True
    assert qa["validation"]["status"] == "PASSED"
    assert qa["validation"]["passed_test_count"] == 82
    assert qa["validation"]["new_route316_direction_test_count"] == 12


def test_manifest_hashes_and_regeneration_are_deterministic() -> None:
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["qa_status"] == "PASSED"
    assert not any(manifest["non_mutation_contract"].values())
    locked = [subject.REPOSITORY_ROOT / path for path in manifest["input_hashes"]]
    outputs = [subject.EDGE_CSV, subject.RELATION_CSV, subject.ADJACENT_CSV,
               subject.CLASSIFICATION_CSV, subject.EVIDENCE_CSV, subject.DIAGNOSIS_CSV,
               subject.QA_JSON, subject.VALIDATION_JSON, subject.REPORT]
    before_locked = {path: sha256(path) for path in locked}
    before_outputs = {path: sha256(path) for path in outputs}
    subprocess.run(
        [sys.executable, str(Path(subject.__file__))], cwd=subject.REPOSITORY_ROOT, check=True
    )
    assert {path: sha256(path) for path in locked} == before_locked
    assert {path: sha256(path) for path in outputs} == before_outputs
