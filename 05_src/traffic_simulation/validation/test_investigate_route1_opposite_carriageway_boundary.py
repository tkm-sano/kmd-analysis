from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import investigate_route1_opposite_carriageway_boundary as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route1_row() -> dict[str, str]:
    rows = read_csv(subject.REVIEW_CSV)
    assert len(rows) == 1
    return rows[0]


def test_target_and_candidate_are_derived_from_formal_review() -> None:
    source, direction = subject.extract_target()
    result = route1_row()
    assert source["official_observation_section_id"] == subject.OBSERVATION_ID
    assert result["current_candidate_edge_sequence"] == source["alternate_carriageway_edge_sequence"]
    assert len(result["current_candidate_edge_sequence"].split(";")) == 14
    assert direction["adopted_sequence_role"] == "DOWN_ORIGIN_TO_TERMINUS"


def test_current_metrics_reproduce_the_review_required_baseline() -> None:
    row = route1_row()
    assert float(row["current_coverage"]) == 0.586498
    assert float(row["current_fixed_axis_coverage"]) == 0.736383
    assert float(row["current_endpoint_difference"]) == 220.357
    assert row["endpoint_mismatch_side"] == "OFFICIAL_ORIGIN_SIDE_FIXED_DOWN_START_OPPOSITE_UP_END"


def test_local_extensions_are_topology_derived_and_route_supported() -> None:
    row = route1_row()
    topology = json.loads(row["topology_evidence"])
    assert topology["derived_predecessor_chain"] == ["997793354#4", "997793354#3"]
    assert topology["derived_successor_chain"] == ["542890137#1"]
    assert topology["all_scenarios_connection_violation_zero"] is True
    evidence = json.loads(row["route_identity_evidence"])
    assert evidence["route_relation_network"] == "JP:national"
    assert evidence["route_relation_ref"] == "1"
    assert all(all(checks.values()) for checks in evidence["per_edge_checks"].values())


def test_no_local_extension_reaches_both_existing_thresholds() -> None:
    rows = read_csv(subject.EXTENSION_CSV)
    assert len(rows) == 4
    assert all(row["connection_violation_count"] == "0" for row in rows)
    assert not any(row["coverage_threshold_pass"] == "true" for row in rows)
    assert not any(row["endpoint_threshold_pass"] == "true" for row in rows)
    best = next(row for row in rows if row["scenario_id"] == "EXTEND_UP_START_1")
    assert best["extension_candidate_edges"] == "997793354#4"
    assert float(best["candidate_axis_coverage_ratio"]) == 0.589805
    assert float(best["maximum_endpoint_difference_m"]) == 220.357


def test_boundary_geometry_mismatch_is_spatially_quantified() -> None:
    row = route1_row()
    assert row["terminal_boundary_edge_id"] == "542890137#0"
    assert float(row["terminal_boundary_edge_length_m"]) > 230
    assert float(row["terminal_edge_length_after_fixed_origin_projection_m"]) > 219
    assert float(row["terminal_edge_length_inside_fixed_25m_buffer_m"]) < 32
    assert float(row["official_geometry_coverage_ratio"]) > 0.84
    assert 163 < float(row["official_geometry_uncovered_length_m"]) < 164
    deficits = json.loads(row["candidate_coverage_deficit_segments_json"])
    assert [item["length_m"] for item in deficits] == [198.333, 13.749, 202.159]
    assert row["coverage_deficit_characterization"].endswith("TERMINAL_EDGE_OVERRUN")


def test_final_status_preserves_review_required_and_does_not_adopt_up() -> None:
    row = route1_row()
    assert row["final_review_status"] == "BOUNDARY_GEOMETRY_MISMATCH"
    assert row["coverage_60_percent_reachable_by_valid_local_extension"] == "false"
    assert row["adoption_status"] == "REVIEW_REQUIRED"
    assert row["up_sumo_edge_sequence"] == ""
    assert len(row["down_sumo_edge_sequence"].split(";")) == 15
    assert row["contamination_check"].startswith("PASS_")


def test_qa_and_manifest_record_non_mutation_and_full_validation() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["summary"]["formally_adopted_count"] == 0
    assert qa["summary"]["review_required_count"] == 1
    assert qa["summary"]["final_status_counts"] == {"BOUNDARY_GEOMETRY_MISMATCH": 1}
    assert qa["invariants"]["all_scenario_connection_violation_count"] == 0
    assert qa["invariants"]["current_candidate_changed"] is False
    assert qa["invariants"]["fixed_mapping_changed"] is False
    assert qa["invariants"]["base_66_mapping_changed"] is False
    assert qa["invariants"]["network_changed"] is False
    assert qa["invariants"]["config_or_threshold_changed"] is False
    assert qa["validation"]["status"] == "PASSED"
    assert qa["validation"]["passed_test_count"] == 100
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    assert not any(manifest["non_mutation_contract"].values())


def test_regeneration_is_deterministic_and_locked_inputs_remain_equal() -> None:
    outputs = [
        subject.REVIEW_CSV, subject.EXTENSION_CSV, subject.EDGE_CSV,
        subject.QA_JSON, subject.MANIFEST_JSON, subject.REPORT,
    ]
    if subject.VALIDATION_JSON.is_file():
        outputs.append(subject.VALIDATION_JSON)
    before_outputs = {path: sha256(path) for path in outputs}
    snapshot = json.loads(subject.PREWORK.read_text(encoding="utf-8"))
    locked = [subject.REPOSITORY_ROOT / path for path in snapshot["sha256"]]
    before_locked = {path: sha256(path) for path in locked}
    subprocess.run(
        [sys.executable, str(Path(subject.__file__))],
        cwd=subject.REPOSITORY_ROOT,
        check=True,
    )
    assert {path: sha256(path) for path in outputs} == before_outputs
    assert {path: sha256(path) for path in locked} == before_locked
