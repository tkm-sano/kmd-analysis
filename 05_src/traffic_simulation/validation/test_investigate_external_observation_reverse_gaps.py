from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from traffic_simulation.calibration import investigate_external_observation_reverse_gaps as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_targets_are_conditionally_extracted_from_canonical_outputs() -> None:
    targets, clusters = subject.extract_targets()
    assert len(targets) == 6
    assert len(clusters) == 4
    assert all(row["traffic_assignment_status"] in subject.TARGET_TRAFFIC_STATUSES for row in targets)


def test_all_72_missing_edges_have_a_final_cause() -> None:
    rows = read_csv(subject.EDGE_CSV)
    assert len(rows) == 72
    assert {row["cause_taxonomy"] for row in rows} == {
        "ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO"
    }
    assert all(row["same_node_pair_reverse_exists"] == "false" for row in rows)


def test_alternate_corridors_exist_in_input_and_sumo_and_are_connected() -> None:
    rows = read_csv(subject.CLUSTER_CSV)
    assert len(rows) == 4
    assert {row["official_observation_section_id"]: int(row["alternate_reverse_corridor_edge_count"])
            for row in rows} == {
        "13300010260": 14,
        "13400020040": 43,
        "13403160320": 4,
        "13604210030": 14,
    }
    assert all(row["alternate_osm_all_present_in_netconvert_input"] == "true" for row in rows)
    assert all(row["alternate_all_present_in_sumo"] == "true" for row in rows)
    assert all(int(row["alternate_node_violation_count"]) == 0 for row in rows)
    assert all(int(row["alternate_connection_violation_count"]) == 0 for row in rows)
    assert all(row["netconvert_dropout_status"] == "NO_DROPOUT" for row in rows)
    assert all(row["network_scope_status"] == "IN_SCOPE" for row in rows)


def test_route_identity_evidence_is_not_invented_for_route_421() -> None:
    rows = {row["route_number"]: row for row in read_csv(subject.CLUSTER_CSV)}
    for route_number in ("1", "2", "316"):
        assert rows[route_number]["route_relation_status"] == "SUPPORTED_SAME_ROUTE_NETWORK_REF_MEMBER"
    assert rows["421"]["route_relation_id"] == ""
    assert rows["421"]["route_relation_status"] == "NO_ROUTE_RELATION_OSM_REF_NAME_SUPPORT"


def test_route_421_preserves_67_exact_reverse_edges_and_only_traces_ten_gaps() -> None:
    row = next(row for row in read_csv(subject.CLUSTER_CSV) if row["route_number"] == "421")
    assert int(row["fixed_edge_count"]) == 77
    assert int(row["preserved_exact_reverse_count"]) == 67
    assert int(row["investigated_missing_edge_count"]) == 10
    assert int(row["alternate_connection_violation_count"]) == 0


def test_route_316_remains_direction_unresolved_and_unadopted() -> None:
    row = next(row for row in read_csv(subject.CLUSTER_CSV) if row["route_number"] == "316")
    assert row["direction_evidence_status"] == "UNRESOLVED"
    assert row["resolution_category"] == "HOLD_DIRECTION_UNRESOLVED"
    assert row["up_down_adoption_status"] == "PROHIBITED_DIRECTION_UNRESOLVED"


def test_requested_six_target_aggregation_is_complete() -> None:
    qa = json.loads(subject.QA_JSON.read_text(encoding="utf-8"))
    assert qa["requested_target_aggregation"] == {
        "mapping_only": 3,
        "network_regeneration_or_limited_extension": 0,
        "osm_or_source_missing": 0,
        "legitimate_oneway": 0,
        "direction_unresolved_hold": 3,
        "cause_unresolved": 0,
    }
    assert qa["invariants"]["unclassified_edge_count"] == 0
    assert qa["invariants"]["alternate_connection_violation_count"] == 0
    assert qa["validation"]["status"] == "PASSED"
    assert qa["validation"]["passed_test_count"] == 84
    assert qa["validation"]["existing_validation_test_count"] == 76
    assert qa["validation"]["new_reverse_gap_test_count"] == 8


def test_regeneration_is_deterministic_and_locked_inputs_do_not_change() -> None:
    outputs = [subject.EDGE_CSV, subject.CLUSTER_CSV, subject.TARGET_CSV,
               subject.QA_JSON, subject.MANIFEST_JSON, subject.REPORT]
    if subject.VALIDATION_JSON.is_file():
        outputs.append(subject.VALIDATION_JSON)
    before_outputs = {path: sha256(path) for path in outputs}
    snapshot = json.loads(subject.PREWORK.read_text(encoding="utf-8"))
    locked = [subject.REPOSITORY_ROOT / path for path in snapshot["sha256"]]
    before_locked = {path: sha256(path) for path in locked}
    subprocess.run([sys.executable, str(Path(subject.__file__))], cwd=subject.REPOSITORY_ROOT, check=True)
    assert {path: sha256(path) for path in outputs} == before_outputs
    assert {path: sha256(path) for path in locked} == before_locked
