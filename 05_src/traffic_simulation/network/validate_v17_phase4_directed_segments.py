from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.directed_segments_v17 import (
    DirectedSegmentError,
    adopt_unique_relation_candidate,
    build_production_artifact,
    generate_way_segments,
    normalize_oneway,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase1_authority import (
    validate_phase1_authority,
)
from traffic_simulation.network.validate_v17_phase3_state_migration import (
    validate_phase3_state_migration,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase4_completion.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"


class Phase4DirectedSegmentError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase4DirectedSegmentError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase4DirectedSegmentError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase4DirectedSegmentError(f"invalid repository artifact: {relative}")
    return path


def _case_index() -> tuple[dict[str, Any], dict[str, Any]]:
    fixtures = {
        item["fixture_id"]: item
        for item in _load_json(FIXTURE_ROOT / "inputs.json")["cases"]
    }
    oracles = {
        item["oracle_id"]: item
        for item in _load_json(FIXTURE_ROOT / "oracle.json")["oracles"]
    }
    return fixtures, oracles


def _compare_direction_case(fixture: dict[str, Any], oracle: dict[str, Any]) -> None:
    value = fixture["input"]
    way = {
        "source_way_id": value["source_way_id"],
        "source_node_ids": value.get("source_node_ids", [10, 20, 30]),
        "tags": value["tags"],
    }
    resolution = normalize_oneway(way["tags"])
    segments = generate_way_segments(way)
    actual_directions = [item["source_direction"] for item in segments]
    if resolution["value_origin"] != oracle["value_origin"]:
        raise Phase4DirectedSegmentError(
            f"fixed oracle origin mismatch: {fixture['fixture_id']}"
        )
    if actual_directions != oracle["effective_value"]["directions"]:
        raise Phase4DirectedSegmentError(
            f"fixed oracle direction mismatch: {fixture['fixture_id']}"
        )


def validate_phase4_directed_segments() -> dict[str, Any]:
    validate_phase1_authority()
    validate_fixture_oracle()
    validate_phase3_state_migration()
    fixtures, oracles = _case_index()

    for fixture_id in ("V17-POS-001", "V17-POS-002", "V17-POS-003", "V17-POS-004"):
        fixture = fixtures[fixture_id]
        _compare_direction_case(fixture, oracles[fixture["oracle_id"]])

    implicit = fixtures["V17-POS-005"]
    implicit_result = normalize_oneway(implicit["input"]["tags"])
    implicit_oracle = oracles[implicit["oracle_id"]]
    if implicit_result["canonical_oneway"] != implicit_oracle["effective_value"]["oneway"]:
        raise Phase4DirectedSegmentError("fixed implicit-oneway oracle mismatch")

    for fixture_id in ("V17-NEG-024", "V17-NEG-025", "V17-NEG-026"):
        fixture = fixtures[fixture_id]
        try:
            normalize_oneway(fixture["input"]["tags"])
        except DirectedSegmentError as error:
            if error.stop_code != oracles[fixture["oracle_id"]]["stop_code"]:
                raise Phase4DirectedSegmentError(
                    f"fixed stop-code oracle mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase4DirectedSegmentError(f"negative fixture did not stop: {fixture_id}")

    unique_fixture = fixtures["V17-POS-017"]
    unique = adopt_unique_relation_candidate(
        unique_fixture["input"]["candidate_directed_segment_ids"]
    )
    if unique != oracles[unique_fixture["oracle_id"]]["effective_value"]:
        raise Phase4DirectedSegmentError("fixed unique relation oracle mismatch")
    for fixture_id in ("V17-NEG-028", "V17-NEG-029"):
        fixture = fixtures[fixture_id]
        try:
            adopt_unique_relation_candidate(
                fixture["input"]["candidate_directed_segment_ids"]
            )
        except DirectedSegmentError as error:
            if error.stop_code != oracles[fixture["oracle_id"]]["stop_code"]:
                raise Phase4DirectedSegmentError(
                    f"fixed relation stop-code mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase4DirectedSegmentError(f"negative fixture did not stop: {fixture_id}")

    production = build_production_artifact(PRODUCTION_FIXTURE)
    if production["blockers"]:
        raise Phase4DirectedSegmentError("production integration fixture has blockers")
    if production["source_way_mutated"]:
        raise Phase4DirectedSegmentError("source Way was mutated")
    repeated = build_production_artifact(PRODUCTION_FIXTURE)
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase4DirectedSegmentError("two-run Directed Segment hash differs")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase4DirectedSegmentError("Phase 4 completion record is not passed")
    for section in ("artifacts", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase4DirectedSegmentError(
                    f"Phase 4 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase4_directed_segments": "passed",
        "fixed_oracle_comparison_count": 11,
        "production_fixture_segment_count": production["counts"]["directed_segments"],
        "production_fixture_relation_mapping_count": production["counts"]["mapped_relations"],
        "production_fixture_blockers": 0,
        "source_way_immutable": True,
        "two_run_determinism": "passed",
        "formal_direction_evidence": production["direction_evidence"],
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 4 Directed Segment production integration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase4_directed_segments()
    except (Phase4DirectedSegmentError, DirectedSegmentError, KeyError) as error:
        print(json.dumps({"phase4_directed_segments": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
