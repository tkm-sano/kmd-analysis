from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import investigate_external_observation_directions as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_target_population_is_derived_from_canonical_inventory() -> None:
    targets = subject.extract_targets()
    assert len(targets) == 9
    assert len({row["official_observation_section_id"] for row in targets}) == 5
    assert all(row["mapping_status"] == "RESOLVED" for row in targets)
    assert all(row["direction_status"] == "MODEL_ASSUMPTION_REQUIRED" for row in targets)


def test_all_targets_have_both_final_status_axes() -> None:
    rows = read_csv(subject.CLASSIFICATION_CSV)
    assert len(rows) == 9
    assert {row["direction_evidence_status"] for row in rows} == {"RESOLVED", "UNRESOLVED"}
    assert {row["traffic_assignment_status"] for row in rows} == {
        "BIDIRECTIONAL_ASSIGNABLE",
        "REVERSE_CORRIDOR_MISSING",
        "REVERSE_CORRIDOR_PARTIAL",
    }
    assert all(row["decision_reason"] for row in rows)


def test_cluster_direction_results_follow_reusable_rules() -> None:
    clusters = {
        row["official_observation_section_id"]: row for row in read_csv(subject.CLUSTER_CSV)
    }
    assert clusters["13300010260"]["adopted_sequence_role"] == subject.DOWN
    assert clusters["13400020040"]["adopted_sequence_role"] == subject.DOWN
    assert clusters["13400110130"]["adopted_sequence_role"] == subject.UP
    assert clusters["13604210030"]["adopted_sequence_role"] == subject.DOWN
    assert clusters["13403160320"]["adopted_sequence_role"] == subject.UNASSIGNED
    assert clusters["13403160320"]["direction_evidence_status"] == "UNRESOLVED"


def test_reverse_completeness_and_traffic_status_are_separate_from_direction() -> None:
    clusters = {
        row["official_observation_section_id"]: row for row in read_csv(subject.CLUSTER_CSV)
    }
    expected = {
        "13300010260": (0, 15, "REVERSE_CORRIDOR_MISSING"),
        "13400020040": (0, 40, "REVERSE_CORRIDOR_MISSING"),
        "13400110130": (5, 5, "BIDIRECTIONAL_ASSIGNABLE"),
        "13403160320": (0, 7, "REVERSE_CORRIDOR_MISSING"),
        "13604210030": (67, 77, "REVERSE_CORRIDOR_PARTIAL"),
    }
    for observation, (found, total, status) in expected.items():
        row = clusters[observation]
        assert int(row["reverse_edge_match_count"]) == found
        assert int(row["adopted_edge_count"]) == total
        assert row["traffic_assignment_status"] == status


def test_only_complete_reverse_is_published_as_up_down_sequence() -> None:
    clusters = {
        row["official_observation_section_id"]: row for row in read_csv(subject.CLUSTER_CSV)
    }
    route_11 = clusters["13400110130"]
    assert route_11["up_edge_sequence"] == route_11["adopted_edge_sequence"]
    assert route_11["down_edge_sequence"] == (
        "261270870#11;261270870#12;261270870#13;261270870#14;261270870#15"
    )
    for observation, row in clusters.items():
        if observation != "13400110130":
            assert not (row["up_edge_sequence"] and row["down_edge_sequence"])


def test_unresolved_cluster_has_no_researcher_assumption() -> None:
    rows = read_csv(subject.ASSUMPTIONS_CSV)
    assert len(rows) == 1
    assert rows[0]["official_observation_section_id"] == "13403160320"
    assert rows[0]["candidate_direction_role"] == ""
    assert rows[0]["candidate_status"] == "NOT_FORMULATED"
    assert rows[0]["adoption_status"] == "NOT_ADOPTED"


def test_qa_locks_mapping_config_and_connectivity() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["target_selection"]["manual_target_ids_used"] is False
    assert qa["invariants"]["unclassified_count"] == 0
    assert qa["invariants"]["selected_connection_violation_count"] == 0
    assert qa["invariants"]["mapping_hash_unchanged"] is True
    assert qa["invariants"]["base_mapping_hash_unchanged"] is True
    assert qa["invariants"]["matching_config_hash_unchanged"] is True
    assert qa["invariants"]["edge_reselection_performed"] is False
    assert qa["invariants"]["reverse_edges_generated"] is False
    assert qa["validation"]["status"] == "PASSED"
    assert qa["validation"]["passed_test_count"] == 76
    assert qa["validation"]["existing_regression_test_count"] == 68
    assert qa["validation"]["new_direction_test_count"] == 8


def test_regeneration_is_deterministic_and_non_mutating() -> None:
    generated = [
        subject.CLASSIFICATION_CSV,
        subject.CLUSTER_CSV,
        subject.RULES_CSV,
        subject.ASSUMPTIONS_CSV,
        subject.QA_JSON,
        subject.MANIFEST_JSON,
        subject.VALIDATION_JSON,
        subject.REPORT,
    ]
    before_outputs = {path: sha256(path) for path in generated}
    before_locked = {path: sha256(path) for path in subject.EXPECTED_INPUT_HASHES}
    subprocess.run(
        [sys.executable, str(Path(subject.__file__))],
        cwd=subject.REPOSITORY_ROOT,
        check=True,
    )
    assert {path: sha256(path) for path in generated} == before_outputs
    assert {path: sha256(path) for path in subject.EXPECTED_INPUT_HASHES} == before_locked
