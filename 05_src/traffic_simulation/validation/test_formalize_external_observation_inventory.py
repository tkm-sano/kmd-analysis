from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import formalize_external_observation_inventory as subject
from traffic_simulation.validation import validate_external_observation_final_inventory as validator


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_inventory_has_nine_unique_targets() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    assert len(rows) == 9
    assert len({row["target_id"] for row in rows}) == 9


def test_all_nine_directions_are_resolved() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    assert all(row["direction_evidence_status"] in {"RESOLVED_UP", "RESOLVED_DOWN"}
               for row in rows)
    summary = json.loads(subject.SUMMARY_JSON.read_text(encoding="utf-8"))
    assert summary["counts"]["direction_resolved"] == 9
    assert summary["counts"]["direction_unresolved"] == 0


def test_traffic_assignment_status_is_independent_and_consistent() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    assert sum(row["traffic_assignment_status"] == "BIDIRECTIONAL_ASSIGNMENT_AVAILABLE"
               for row in rows) == 6
    assert sum(row["traffic_assignment_status"] == "REVIEW_REQUIRED" for row in rows) == 3


def test_calibration_usability_separates_current_and_historical() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    assert sum(row["calibration_usability_status"] == "CALIBRATION_USABLE" for row in rows) == 5
    historical = [row for row in rows if row["calibration_usability_status"] == "VALIDATION_ONLY"]
    assert len(historical) == 1
    assert historical[0]["target_id"] == "13300010290"
    assert historical[0]["observation_year"] == "2019"
    assert historical[0]["calibration_weight"] == "0.0"


def test_route1_partial_edge_reference_is_formally_preserved() -> None:
    row = next(row for row in read_csv(subject.INVENTORY_CSV)
               if row["target_id"] == "13300010290")
    assert row["opposite_mapping_status"] == "ACCEPTED_AS_PARTIAL_EDGE_MAPPING"
    assert row["partial_edge_used"] == "true"
    assert row["opposite_edge_count"] == "14"
    assert row["edge_segment_specification_reference"] == subject.relative(subject.PARTIAL_SEGMENTS)
    segments = read_csv(subject.PARTIAL_SEGMENTS)
    terminal = segments[-1]
    assert terminal["edge_id"] == "542890137#0"
    assert terminal["coverage_role"] == "PARTIAL_END_EDGE"


def test_opposite_carriageway_adoption_references_are_consistent() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    adopted = [row for row in rows
               if row["opposite_mapping_status"] == "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"]
    assert {row["target_id"] for row in adopted} == {"13400020050", "13604210040"}
    assert all(row["source_review_artifact"] == subject.relative(subject.ADOPTION_REVIEW)
               for row in adopted)


def test_route316_is_resolved_up_but_not_bidirectional() -> None:
    rows = [row for row in read_csv(subject.INVENTORY_CSV)
            if row["official_observation_section_id"] == "13403160320"]
    assert len(rows) == 3
    assert all(row["direction_evidence_status"] == "RESOLVED_UP" for row in rows)
    assert all(row["opposite_mapping_status"] == "REVIEW_REQUIRED" for row in rows)
    assert all(row["traffic_assignment_status"] == "REVIEW_REQUIRED" for row in rows)
    assert all(row["calibration_usability_status"] == "REVIEW_REQUIRED" for row in rows)
    assert all(row["review_required_reason"] == subject.SPATIAL_REASON for row in rows)


def test_only_current_adopted_or_direct_reverse_targets_are_calibration_usable() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    usable = [row for row in rows if row["calibration_usability_status"] == "CALIBRATION_USABLE"]
    assert all(row["observation_type"] == "CURRENT_OFFICIAL_OBSERVATION" for row in usable)
    assert all(row["opposite_mapping_status"] in {
        "DIRECT_REVERSE_AVAILABLE", "ACCEPTED_AS_OPPOSITE_CARRIAGEWAY"
    } for row in usable)


def test_route_topology_and_contamination_evidence_has_no_failure() -> None:
    rows = read_csv(subject.INVENTORY_CSV)
    assert all(row["route_identity_status"] == "PASS" for row in rows)
    assert all(row["topology_status"] == "PASS" for row in rows)
    assert all(row["contamination_status"] == "PASS" for row in rows)
    assert all(int(row["connection_violation_count"]) == 0 for row in rows)


def test_observations_are_not_divided_by_edge_count() -> None:
    rows = read_csv(subject.OBSERVATIONS_CSV)
    assert len(rows) == 240
    assert all(float(row["raw_observed_value"]) == float(row["normalized_observed_value"])
               for row in rows)
    route11 = [row for row in rows if row["official_observation_section_id"] == "13400110130"
               and row["direction"] == "UP" and row["hour"] == "7"]
    assert len(route11) == 3
    assert len({row["raw_observed_value"] for row in route11}) == 1


def test_official_observation_windows_are_not_imputed() -> None:
    rows = read_csv(subject.OBSERVATIONS_CSV)
    route1 = [row for row in rows if row["official_observation_section_id"] == "13300010260"]
    current = [row for row in rows if row["official_observation_section_id"] != "13300010260"]
    assert len(route1) == 48
    assert {int(row["hour"]) for row in route1} == set(range(24))
    assert {int(row["hour"]) for row in current} == set(range(7, 19))


def test_observation_provenance_is_complete() -> None:
    rows = read_csv(subject.OBSERVATIONS_CSV)
    for row in rows:
        assert row["source_object"].startswith("zkntrf13.csv#13100|")
        assert row["source_field"]
        assert row["derivation_rule"] == "SUM_SMALL_AND_LARGE_AT_OFFICIAL_CROSS_SECTION_NO_EDGE_DIVISION_V1"
        assert row["mapping_evidence_artifact"]
    assert all(row["provenance_status"].startswith("COMPLETE_MACHINE_READABLE")
               for row in read_csv(subject.INVENTORY_CSV))


def test_every_observation_row_validates_against_schema() -> None:
    rows = read_csv(subject.OBSERVATIONS_CSV)
    assert subject.validate_schema(rows) == []
    schema = json.loads(subject.SCHEMA_JSON.read_text(encoding="utf-8"))
    assert "HISTORICAL_EXTERNAL_VALIDATION" in schema["properties"]["observation_type"]["enum"]
    assert "DATA_NOT_AVAILABLE" in schema["properties"]["observation_type"]["enum"]


def test_manifest_validator_and_regeneration_are_consistent() -> None:
    assert validator.validate()["status"] == "PASSED"
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    inputs = [subject.REPOSITORY_ROOT / path for path in manifest["input_hashes"]]
    outputs = [subject.REPOSITORY_ROOT / path for path in manifest["output_hashes"]]
    before_inputs = {path: sha256(path) for path in inputs}
    before_outputs = {path: sha256(path) for path in outputs}
    subprocess.run([sys.executable, str(Path(subject.__file__))],
                   cwd=subject.REPOSITORY_ROOT, check=True)
    assert {path: sha256(path) for path in inputs} == before_inputs
    assert {path: sha256(path) for path in outputs} == before_outputs
    assert validator.validate()["status"] == "PASSED"
