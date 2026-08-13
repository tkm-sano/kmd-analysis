from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    DirectionalLaneError,
    build_lane_production_artifact,
    resolve_directional_lanes,
    validate_lane_vector,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase4_directed_segments import (
    validate_phase4_directed_segments,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase5_completion.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"


class Phase5DirectionalLaneError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase5DirectionalLaneError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase5DirectionalLaneError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase5DirectionalLaneError(f"invalid repository artifact: {relative}")
    return path


def _indexes() -> tuple[dict[str, Any], dict[str, Any]]:
    fixtures = {
        item["fixture_id"]: item
        for item in _load_json(FIXTURE_ROOT / "inputs.json")["cases"]
    }
    oracles = {
        item["oracle_id"]: item
        for item in _load_json(FIXTURE_ROOT / "oracle.json")["oracles"]
    }
    return fixtures, oracles


def _lane_tags(value: dict[str, Any], *, default_oneway: str = "no") -> dict[str, str]:
    return {
        "highway": "residential",
        "oneway": default_oneway,
        **{key: str(item) for key, item in value.items()},
    }


def validate_phase5_directional_lanes() -> dict[str, Any]:
    validate_phase4_directed_segments()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()

    for fixture_id in ("V17-POS-006", "V17-POS-007", "V17-POS-008"):
        fixture = fixtures[fixture_id]
        profile = fixture["input"].get("profile", "formal")
        actual = resolve_directional_lanes(
            _lane_tags(fixture["input"]["tags"]), profile=profile
        )
        oracle = oracles[fixture["oracle_id"]]
        if actual["value_origin"] != oracle["value_origin"]:
            raise Phase5DirectionalLaneError(
                f"fixed lane origin oracle mismatch: {fixture_id}"
            )
        for key, expected in oracle["effective_value"].items():
            if actual["effective_value"][key] != expected:
                raise Phase5DirectionalLaneError(
                    f"fixed lane value oracle mismatch: {fixture_id}.{key}"
                )

    vector_fixture = fixtures["V17-POS-022"]
    vector = validate_lane_vector(
        vector_fixture["input"]["directional_lane_count"],
        vector_fixture["input"]["lane_vector"],
    )
    if vector != oracles[vector_fixture["oracle_id"]]["effective_value"]:
        raise Phase5DirectionalLaneError("fixed lane-vector oracle mismatch")

    negative_inputs = {
        "V17-NEG-030": (
            _lane_tags(fixtures["V17-NEG-030"]["input"]["tags"], default_oneway="yes"),
            "formal",
        ),
        "V17-NEG-031": (
            _lane_tags(fixtures["V17-NEG-031"]["input"]["tags"]),
            "formal",
        ),
    }
    for fixture_id, (tags, profile) in negative_inputs.items():
        try:
            resolve_directional_lanes(tags, profile=profile)
        except DirectionalLaneError as error:
            if error.stop_code != oracles[fixtures[fixture_id]["oracle_id"]]["stop_code"]:
                raise Phase5DirectionalLaneError(
                    f"fixed lane stop-code mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase5DirectionalLaneError(f"negative lane fixture passed: {fixture_id}")

    missing_fixture = fixtures["V17-NEG-032"]
    for variant in missing_fixture["input"]["variants"]:
        try:
            resolve_directional_lanes(
                _lane_tags(variant, default_oneway=missing_fixture["input"]["oneway"]),
                profile=missing_fixture["input"]["profile"],
            )
        except DirectionalLaneError as error:
            if error.stop_code != oracles[missing_fixture["oracle_id"]]["stop_code"]:
                raise Phase5DirectionalLaneError(
                    "fixed missing-allocation oracle mismatch"
                ) from error
        else:
            raise Phase5DirectionalLaneError("formal total-only variant passed")

    mismatch_fixture = fixtures["V17-NEG-033"]
    try:
        validate_lane_vector(
            mismatch_fixture["input"]["directional_lane_count"],
            mismatch_fixture["input"]["lane_vector"],
        )
    except DirectionalLaneError as error:
        if error.stop_code != oracles[mismatch_fixture["oracle_id"]]["stop_code"]:
            raise Phase5DirectionalLaneError(
                "fixed vector-mismatch oracle mismatch"
            ) from error
    else:
        raise Phase5DirectionalLaneError("negative lane-vector fixture passed")

    production = build_lane_production_artifact(PRODUCTION_FIXTURE, profile="formal")
    if production["blockers"] or production["upstream_blockers"]:
        raise Phase5DirectionalLaneError("Phase 5 production fixture has blockers")
    repeated = build_lane_production_artifact(PRODUCTION_FIXTURE, profile="formal")
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase5DirectionalLaneError("two-run directional-lane hash differs")
    if any(
        item["value_origin"] == "model_assumed"
        or item["assumption_ids"]
        or not item["formal_eligible"]
        for item in production["segment_lanes"]
    ):
        raise Phase5DirectionalLaneError("formal fixture contains structural assumptions")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase5DirectionalLaneError("Phase 5 completion record is not passed")
    for section in ("artifacts", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase5DirectionalLaneError(
                    f"Phase 5 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase5_directional_lanes": "passed",
        "fixed_oracle_comparison_count": 8,
        "production_fixture_resolved_way_count": production["counts"][
            "resolved_source_ways"
        ],
        "production_fixture_directional_lane_count": production["counts"][
            "directional_lanes"
        ],
        "production_fixture_blockers": 0,
        "formal_model_assumed_count": 0,
        "two_run_determinism": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 5 directional-lane production integration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase5_directional_lanes()
    except (Phase5DirectionalLaneError, DirectionalLaneError, KeyError) as error:
        print(json.dumps({"phase5_directional_lanes": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
