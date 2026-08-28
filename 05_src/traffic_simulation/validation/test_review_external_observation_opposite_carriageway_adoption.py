from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import review_external_observation_opposite_carriageway_adoption as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_population_is_derived_and_route_316_is_excluded() -> None:
    targets, gap_clusters, _ = subject.extract_targets()
    observations = {row["official_observation_section_id"] for row in targets}
    assert len(targets) == 3
    assert "13403160320" not in observations
    assert gap_clusters["13403160320"]["resolution_category"] == "HOLD_DIRECTION_UNRESOLVED"


def test_final_adoption_status_counts() -> None:
    rows = read_csv(subject.REVIEW_CSV)
    assert len(rows) == 3
    statuses = {row["official_observation_section_id"]: row["adoption_status"] for row in rows}
    assert statuses == {
        "13300010260": "REVIEW_REQUIRED",
        "13400020040": "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY",
        "13604210030": "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY",
    }


def test_route_1_candidate_is_not_trimmed_or_adopted() -> None:
    row = next(row for row in read_csv(subject.REVIEW_CSV)
               if row["official_observation_section_id"] == "13300010260")
    assert len(row["alternate_carriageway_edge_sequence"].split(";")) == 14
    assert float(row["opposite_axis_coverage_by_fixed_ratio"]) < 0.60
    assert float(row["fixed_start_to_opposite_end_distance_m"]) > 200
    assert row["up_sumo_edge_sequence"] == ""
    assert row["bidirectional_traffic_assignment_status"] == "NOT_YET_ASSIGNABLE"


def test_route_2_is_adopted_as_up_and_keeps_fixed_down() -> None:
    row = next(row for row in read_csv(subject.REVIEW_CSV)
               if row["official_observation_section_id"] == "13400020040")
    assert row["fixed_direction"] == subject.DOWN
    assert row["alternate_direction"] == subject.UP
    assert len(row["up_sumo_edge_sequence"].split(";")) == 43
    assert len(row["down_sumo_edge_sequence"].split(";")) == 40
    assert int(row["connection_violation_count"]) == 0


def test_route_421_preserves_67_and_splices_only_reviewed_14_edge_gap() -> None:
    row = next(row for row in read_csv(subject.REVIEW_CSV)
               if row["official_observation_section_id"] == "13604210030")
    assert int(row["preserved_existing_reverse_edge_count"]) == 67
    assert len(row["alternate_carriageway_edge_sequence"].split(";")) == 14
    assert len(row["up_sumo_edge_sequence"].split(";")) == 81
    assert len(row["down_sumo_edge_sequence"].split(";")) == 77
    assert int(row["opposite_composite_connection_violation_count"]) == 0


def test_all_reviewed_candidate_edges_are_mainline_route_edges() -> None:
    rows = read_csv(subject.EDGE_CSV)
    assert len(rows) == 71
    assert all(row["mainline_edge_status"] == "PASS" for row in rows)
    assert all(row["sumo_function"] != "internal" for row in rows)
    assert all(not row["sumo_type"].endswith("_link") for row in rows)


def test_qa_reports_two_adoptions_and_no_mutation() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["summary"] == {
        "accepted": 2,
        "review_required": 1,
        "rejected": 0,
        "unresolved": 0,
        "bidirectional_assignable_after_adoption": 2,
    }
    assert qa["invariants"]["connection_violation_count"] == 0
    assert qa["invariants"]["inappropriate_edge_count"] == 0
    assert qa["invariants"]["mapping_changed"] is False
    assert qa["invariants"]["base_mapping_changed"] is False
    assert qa["invariants"]["network_changed"] is False
    assert qa["invariants"]["config_or_thresholds_changed"] is False
    assert qa["validation"]["status"] == "PASSED"
    assert qa["validation"]["passed_test_count"] == 92
    assert qa["validation"]["existing_validation_test_count"] == 84
    assert qa["validation"]["new_adoption_review_test_count"] == 8


def test_regeneration_is_deterministic_and_all_locked_hashes_remain_equal() -> None:
    outputs = [subject.REVIEW_CSV, subject.EDGE_CSV, subject.QA_JSON,
               subject.MANIFEST_JSON, subject.REPORT]
    if subject.VALIDATION_JSON.is_file():
        outputs.append(subject.VALIDATION_JSON)
    before_outputs = {path: sha256(path) for path in outputs}
    snapshot = json.loads(subject.PREWORK.read_text(encoding="utf-8"))
    locked = [subject.REPOSITORY_ROOT / path for path in snapshot["sha256"]]
    before_locked = {path: sha256(path) for path in locked}
    subprocess.run([sys.executable, str(Path(subject.__file__))], cwd=subject.REPOSITORY_ROOT, check=True)
    assert {path: sha256(path) for path in outputs} == before_outputs
    assert {path: sha256(path) for path in locked} == before_locked
