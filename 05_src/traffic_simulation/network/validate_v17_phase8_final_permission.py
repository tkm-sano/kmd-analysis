from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema
import yaml

from traffic_simulation.network.final_permission_v17 import (
    build_final_permission_production_artifact,
    resolve_permission,
)
from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    normalize_static_access_rules,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase7_conditional_access import (
    validate_phase7_conditional_access,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase8_completion.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"
BASE_TAGS = {"highway": "residential", "oneway": "yes", "lanes": "2"}


class Phase8FinalPermissionError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase8FinalPermissionError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase8FinalPermissionError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase8FinalPermissionError(f"invalid repository artifact: {relative}")
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


def _rules(tags: Mapping[str, str]) -> list[dict[str, Any]]:
    return normalize_static_access_rules(
        source_way_id=1001,
        tags={**BASE_TAGS, **tags},
        lane_counts={"forward": 2},
    )["rules"]


def validate_phase8_final_permission() -> dict[str, Any]:
    validate_phase7_conditional_access()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()

    same_rules = _rules({"goods": "yes", "access:lanes": "yes|"})
    same = resolve_permission(same_rules, lane_count=2)
    same_oracle = oracles[fixtures["V17-POS-016"]["oracle_id"]]
    if (
        same["resolution_status"] != same_oracle["resolution_status"]
        or same["effective_permission"] != same_oracle["effective_value"]
        or len(same["maximal_rule_ids"]) != 2
    ):
        raise Phase8FinalPermissionError("same-effect maximal oracle mismatch")

    conflict = resolve_permission(
        _rules({"goods": "no", "access:lanes": "yes|"}), lane_count=2
    )
    conflict_oracle = oracles[fixtures["V17-NEG-045"]["oracle_id"]]
    if (
        conflict["resolution_status"] != conflict_oracle["resolution_status"]
        or conflict["stop_code"] != conflict_oracle["stop_code"]
    ):
        raise Phase8FinalPermissionError("conflicting maximal oracle mismatch")

    unresolved = resolve_permission([], lane_count=1)
    unresolved_oracle = oracles[fixtures["V17-NEG-046"]["oracle_id"]]
    if (
        unresolved["resolution_status"] != unresolved_oracle["resolution_status"]
        or unresolved["stop_code"] != unresolved_oracle["stop_code"]
    ):
        raise Phase8FinalPermissionError("unresolved permission oracle mismatch")

    if same != resolve_permission(list(reversed(same_rules)), lane_count=2):
        raise Phase8FinalPermissionError("rule-order metamorphic oracle mismatch")

    scenario = {"weekday": "Mo", "time": "08:00"}
    production = build_final_permission_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=scenario
    )
    if not production["formal_permission_complete"]:
        raise Phase8FinalPermissionError("production fixture permissions are incomplete")
    if production["counts"]["permission_records"] != 14:
        raise Phase8FinalPermissionError("production fixture permission count differs")
    if any(
        item["provenance"]["typemap_permission_used"]
        for item in production["permission_records"]
    ):
        raise Phase8FinalPermissionError("typemap became final permission authority")
    repeated = build_final_permission_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=scenario
    )
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase8FinalPermissionError("two-run final-permission hash differs")

    conditional_record = next(
        item
        for item in production["permission_records"]
        if item["source_way_id"] == 1002
    )
    if conditional_record["effective_permission"] != "denied":
        raise Phase8FinalPermissionError("conditional temporal dominance was not applied")
    lane_records = sorted(
        (
            item
            for item in production["permission_records"]
            if item["source_way_id"] == 1003
        ),
        key=lambda item: item["lane_position"],
    )
    if [
        item["provenance"]["maximal_rules"][0]["target_scope"]["lane_scope"][
            "positions"
        ]
        for item in lane_records
    ] != [[0], [1]]:
        raise Phase8FinalPermissionError("lane-local provenance was copied")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase8FinalPermissionError("Phase 8 completion record is not passed")
    for section in ("artifacts", "schemas", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase8FinalPermissionError(
                    f"Phase 8 completion hash mismatch: {section}.{name}"
                )

    schema = _load_json(
        _repo_file(completion["schemas"]["final_permission_expectation"]["path"])
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    for record in production["permission_records"]:
        jsonschema.Draft202012Validator(schema).validate(record)

    return {
        "phase8_final_permission": "passed",
        "fixed_oracle_comparison_count": 4,
        "production_fixture_permission_records": 14,
        "production_fixture_blockers": 0,
        "permission_authority": "resolver_expected_permissions",
        "typemap_permission_authority": False,
        "next_phase": 9,
        "two_run_determinism": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 8 final-permission integration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase8_final_permission()
    except (
        Phase8FinalPermissionError,
        StaticAccessError,
        jsonschema.ValidationError,
        KeyError,
    ) as error:
        print(json.dumps({"phase8_final_permission": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
