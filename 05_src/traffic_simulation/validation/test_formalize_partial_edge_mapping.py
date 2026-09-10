from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import formalize_partial_edge_mapping as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_schema_declares_all_required_fields_and_roles() -> None:
    schema = json.loads(subject.SCHEMA.read_text(encoding="utf-8"))
    assert tuple(schema["required"]) == subject.REQUIRED_FIELDS
    assert set(schema["properties"]["coverage_role"]["enum"]) == subject.ROLES


def test_position_range_used_length_and_role_consistency() -> None:
    rows = read_csv(subject.SEGMENTS_CSV)
    assert subject.validate_segment_rows(rows) == []
    assert len(rows) == 14
    for row in rows:
        start = float(row["start_position_m"])
        end = float(row["end_position_m"])
        length = float(row["edge_length_m"])
        assert 0 <= start <= end <= length
        assert abs(float(row["used_length_m"]) - (end - start)) <= subject.POSITION_TOLERANCE_M


def test_edge_sequence_is_unchanged_and_segment_layer_is_separate() -> None:
    source, _ = subject.route1.extract_target()
    rows = read_csv(subject.SEGMENTS_CSV)
    assert [row["edge_id"] for row in rows] == source["alternate_carriageway_edge_sequence"].split(";")
    assert [int(row["sequence_order"]) for row in rows] == list(range(1, 15))


def test_full_and_partial_end_roles_are_exact() -> None:
    rows = read_csv(subject.SEGMENTS_CSV)
    assert all(row["coverage_role"] == "FULL_EDGE" for row in rows[:-1])
    terminal = rows[-1]
    assert terminal["edge_id"] == "542890137#0"
    assert terminal["coverage_role"] == "PARTIAL_END_EDGE"
    assert float(terminal["start_position_m"]) == 0.0
    assert float(terminal["end_position_m"]) == 14.073
    assert float(terminal["edge_length_m"]) == 233.782


def test_boundary_derivation_is_reproducible_and_not_labelled_official() -> None:
    result = subject.derive_route1()
    terminal = read_csv(subject.SEGMENTS_CSV)[-1]
    assert abs(result["metrics"]["boundary_position_m"] - 14.072655216512528) <= 1e-12
    assert terminal["boundary_position_source"] == "DERIVED_BY_GEOMETRIC_PROJECTION"
    assert terminal["boundary_anchor"] == "DOWN_CORRIDOR_START"
    assert terminal["derivation_rule_id"] == "PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1"
    review = read_csv(subject.FORMAL_REVIEW_CSV)[0]
    assert review["boundary_position_fact_class"] == "RULE_DERIVED_NOT_OFFICIAL"


def test_route_topology_and_contamination_all_pass() -> None:
    rows = read_csv(subject.SEGMENTS_CSV)
    assert all(row["route_identity_status"] == "PASS" for row in rows)
    assert all(row["topology_status"] == "PASS" for row in rows)
    assert all(row["contamination_status"] == "PASS" for row in rows)
    review = read_csv(subject.FORMAL_REVIEW_CSV)[0]
    assert review["connection_violation_count"] == "0"


def test_coverage_and_endpoint_recompute_against_unchanged_thresholds() -> None:
    review = read_csv(subject.FORMAL_REVIEW_CSV)[0]
    assert float(review["partial_edge_coverage_ratio"]) == 0.840896
    assert float(review["candidate_axis_coverage_ratio"]) == 0.728822
    assert float(review["fixed_axis_coverage_ratio"]) == 0.736383
    assert float(review["endpoint_difference_m"]) == 17.968
    assert float(review["projection_error_m"]) == 17.968
    assert float(review["configured_coverage_threshold"]) == 0.60
    assert float(review["configured_endpoint_threshold_m"]) == 25.0


def test_old_review_is_preserved_and_new_review_is_additive() -> None:
    prior = read_csv(subject.PRIOR_BOUNDARY_REVIEW)[0]
    review = read_csv(subject.FORMAL_REVIEW_CSV)[0]
    assert prior["final_review_status"] == "BOUNDARY_GEOMETRY_MISMATCH"
    assert prior["adoption_status"] == "REVIEW_REQUIRED"
    assert review["prior_final_review_status"] == prior["final_review_status"]
    assert review["prior_adoption_status"] == prior["adoption_status"]
    assert review["prior_review_preserved"] == "true"
    assert review["new_adoption_status"] == "ACCEPTED_AS_PARTIAL_EDGE_MAPPING"


def test_candidate_screen_covers_66_and_nine_without_auto_adoption() -> None:
    rows = read_csv(subject.CANDIDATE_INVENTORY_CSV)
    assert len(rows) == 75
    assert sum(row["population"] == "BASE_ROAD_CENSUS_66" for row in rows) == 66
    assert sum(row["population"] == "EXTERNAL_OBSERVATION_9" for row in rows) == 9
    assert all(row["automatic_adoption"] == "false" for row in rows)
    assert all(row["screening_effect_on_existing_mapping"] == "PRESERVE_EXISTING_DECISION" for row in rows)
    assert all(row["partial_edge_screening_class"] in subject.SCREENING_CLASSES for row in rows)


def test_post_review_inventory_has_six_assignable_and_route316_is_next() -> None:
    rows = read_csv(subject.POST_REVIEW_INVENTORY_CSV)
    assignable = [row for row in rows if row["traffic_assignment_status_after_partial_edge_review"] == "BIDIRECTIONAL_ASSIGNABLE"]
    unresolved = [row for row in rows if row["traffic_assignment_status_after_partial_edge_review"] == "DIRECTION_UNRESOLVED"]
    assert len(assignable) == 6
    assert len(unresolved) == 3
    assert {row["cluster"] for row in unresolved} == {"ROUTE_JP_prefectural_tokyo_316"}
    route1 = next(row for row in rows if row["official_observation_section_id"] == subject.OBSERVATION_ID)
    assert len(route1["up_sumo_edge_sequence"].split(";")) == 14
    assert route1["edge_segment_specification_reference"].endswith("external_observation_partial_edge_mapping_v1.csv")


def test_qa_manifest_and_regeneration_preserve_locked_inputs() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["status"] == "PASSED"
    assert all(qa["validation_rules"].values())
    assert not any(qa["non_mutation_contract"].values())
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["qa_status"] == "PASSED"
    assert manifest["unchanged_thresholds"] == {
        "candidate_buffer_m": 25.0, "high_section_coverage_ratio": 0.6,
    }
    locked = [subject.REPOSITORY_ROOT / path for path in manifest["input_hashes"]]
    outputs = [subject.SEGMENTS_CSV, subject.FORMAL_REVIEW_CSV,
               subject.CANDIDATE_INVENTORY_CSV, subject.POST_REVIEW_INVENTORY_CSV,
               subject.QA_JSON, subject.VALIDATION_JSON, subject.REPORT]
    before_locked = {path: sha256(path) for path in locked}
    before_outputs = {path: sha256(path) for path in outputs}
    subprocess.run(
        [sys.executable, str(Path(subject.__file__))],
        cwd=subject.REPOSITORY_ROOT, check=True,
    )
    assert {path: sha256(path) for path in locked} == before_locked
    assert {path: sha256(path) for path in outputs} == before_outputs
