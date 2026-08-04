from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from traffic_simulation.network.speed_resolution_v17 import (
    REGISTRY_PATH,
    SpeedResolutionError,
    build_speed_production_artifact,
    load_japan_speed_registry,
    resolve_segment_speed,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase8_final_permission import (
    validate_phase8_final_permission,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase9_completion.yml"
)
REGISTRY_BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "speed_phase9_production.osm.xml"
POINT_CONTEXT = {"weekday": "Mo", "time": "08:00"}


class Phase9SpeedResolutionError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase9SpeedResolutionError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase9SpeedResolutionError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase9SpeedResolutionError(f"invalid repository artifact: {relative}")
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


def validate_phase9_speed_resolution() -> dict[str, Any]:
    validate_phase8_final_permission()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()
    registry = load_japan_speed_registry()
    bundle_ref = _load_yaml(REGISTRY_BUNDLE_PATH)["japan_speed_rules"]
    if bundle_ref["registry_id"] != registry["registry_id"]:
        raise Phase9SpeedResolutionError("Japan speed registry ID mismatch")
    if bundle_ref["registry_version"] != registry["registry_version"]:
        raise Phase9SpeedResolutionError("Japan speed registry version mismatch")
    if bundle_ref["sha256"] != _sha256(REGISTRY_PATH):
        raise Phase9SpeedResolutionError("Japan speed registry hash mismatch")

    direction_fixture = fixtures["V17-POS-009"]
    direction_oracle = oracles[direction_fixture["oracle_id"]]
    tags = direction_fixture["input"]["tags"]
    observed = {
        direction: resolve_segment_speed(
            tags,
            direction=direction,
            profile="formal",
            scenario_context=POINT_CONTEXT,
        )["speed_kmh"]
        for direction in ("forward", "backward")
    }
    if observed != {
        "forward": float(direction_oracle["effective_value"]["forward_kmh"]),
        "backward": float(direction_oracle["effective_value"]["backward_kmh"]),
    }:
        raise Phase9SpeedResolutionError("directional speed oracle mismatch")

    symbolic_fixture = fixtures["V17-POS-010"]
    symbolic_oracle = oracles[symbolic_fixture["oracle_id"]]
    symbolic = resolve_segment_speed(
        symbolic_fixture["input"]["tags"],
        direction="forward",
        profile="formal",
        scenario_context=POINT_CONTEXT,
        japan_registry=symbolic_fixture["input"]["fixture_registry"],
    )
    if symbolic["speed_kmh"] != float(symbolic_oracle["effective_value"]["speed_kmh"]):
        raise Phase9SpeedResolutionError("symbolic speed oracle mismatch")

    for fixture_id in (
        "V17-NEG-034",
        "V17-NEG-035",
        "V17-NEG-036",
        "V17-NEG-037",
        "V17-NEG-038",
    ):
        fixture = fixtures[fixture_id]
        oracle = oracles[fixture["oracle_id"]]
        try:
            resolve_segment_speed(
                fixture["input"]["tags"],
                direction="forward",
                profile="formal",
                scenario_context=fixture["input"].get("scenario", POINT_CONTEXT),
            )
        except SpeedResolutionError as error:
            if error.stop_code != oracle["stop_code"]:
                raise Phase9SpeedResolutionError(
                    f"fixed speed stop-code mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase9SpeedResolutionError(
                f"negative speed fixture passed: {fixture_id}"
            )

    production = build_speed_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    if not production["formal_speed_complete"] or production["blockers"]:
        raise Phase9SpeedResolutionError("Phase 9 production fixture has blockers")
    if production["counts"]["speed_records"] != 4:
        raise Phase9SpeedResolutionError("Phase 9 production fixture count differs")
    repeated = build_speed_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=POINT_CONTEXT
    )
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase9SpeedResolutionError("two-run speed hash differs")
    by_way = {
        (item["source_way_id"], item["source_direction"]): item
        for item in production["speed_records"]
    }
    if (
        by_way[(3001, "forward")]["speed_kmh"] != 50
        or by_way[(3001, "backward")]["speed_kmh"] != 40
    ):
        raise Phase9SpeedResolutionError("directional production speeds collapsed")
    if by_way[(3002, "forward")]["advisory_speed"]["legal_maxspeed"] is not False:
        raise Phase9SpeedResolutionError("advisory speed became legal maxspeed")
    if any(
        item["value_origin"] == "model_assumed"
        or item["provenance"]["typemap_used_as_formal_evidence"]
        for item in production["speed_records"]
    ):
        raise Phase9SpeedResolutionError("formal speed used a structural assumption")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase9SpeedResolutionError("Phase 9 completion record is not passed")
    for section in ("artifacts", "schemas", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase9SpeedResolutionError(
                    f"Phase 9 completion hash mismatch: {section}.{name}"
                )
    record_schema = _load_json(
        _repo_file(completion["schemas"]["speed_resolution_record"]["path"])
    )
    jsonschema.Draft202012Validator.check_schema(record_schema)
    for record in production["speed_records"]:
        jsonschema.Draft202012Validator(record_schema).validate(record)

    return {
        "phase9_speed_resolution": "passed",
        "fixed_oracle_comparison_count": 7,
        "japan_speed_registry": registry["registry_id"],
        "japan_speed_registry_version": registry["registry_version"],
        "production_fixture_speed_records": 4,
        "production_fixture_blockers": 0,
        "directional_asymmetry": "passed",
        "formal_model_assumed_speeds": 0,
        "two_run_determinism": "passed",
        "next_phase": 10,
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 9 speed resolution."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase9_speed_resolution()
    except (
        Phase9SpeedResolutionError,
        SpeedResolutionError,
        jsonschema.ValidationError,
        KeyError,
    ) as error:
        print(json.dumps({"phase9_speed_resolution": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
