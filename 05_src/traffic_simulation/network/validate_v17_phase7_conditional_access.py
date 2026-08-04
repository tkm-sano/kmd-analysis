from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
    evaluate_conditional_access_rules,
    evaluate_conditional_value,
)
from traffic_simulation.network.static_access_v17 import StaticAccessError
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase6_static_access import (
    validate_phase6_static_access,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase7_completion.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"


class Phase7ConditionalAccessError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase7ConditionalAccessError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase7ConditionalAccessError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase7ConditionalAccessError(f"invalid repository artifact: {relative}")
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


def validate_phase7_conditional_access() -> dict[str, Any]:
    validate_phase6_static_access()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()

    positive = fixtures["V17-POS-015"]
    selected = evaluate_conditional_value(
        positive["input"]["tags"]["access:conditional"],
        positive["input"]["scenario"],
    )
    positive_oracle = oracles[positive["oracle_id"]]
    if selected is None:
        raise Phase7ConditionalAccessError("fixed conditional rule did not match")
    normalized = evaluate_conditional_access_rules(
        source_way_id=1001,
        conditional_tags=positive["input"]["tags"],
        tags={"highway": "residential", "oneway": "yes", "lanes": "1"},
        lane_counts={"forward": 1},
        context={"vehicle_class": "delivery", **positive["input"]["scenario"]},
    )
    if (
        len(normalized["rules"]) != 1
        or normalized["rules"][0]["effect"] != positive_oracle["effective_value"]
    ):
        raise Phase7ConditionalAccessError("fixed conditional access oracle mismatch")

    negative_operations = {
        "V17-NEG-042": lambda value: evaluate_conditional_value(
            value["tags"]["access:conditional"], {}
        ),
        "V17-NEG-044": lambda value: evaluate_conditional_value(
            value["tags"]["access:conditional"], value["scenario"]
        ),
    }
    for fixture_id, operation in negative_operations.items():
        fixture = fixtures[fixture_id]
        oracle = oracles[fixture["oracle_id"]]
        try:
            operation(fixture["input"])
        except StaticAccessError as error:
            if error.stop_code != oracle["stop_code"]:
                raise Phase7ConditionalAccessError(
                    f"fixed conditional stop-code mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase7ConditionalAccessError(
                f"negative conditional fixture passed: {fixture_id}"
            )

    scenario = {"weekday": "Mo", "time": "08:00"}
    production = build_conditional_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=scenario
    )
    if (
        production["blockers"]
        or production["upstream_static_access_blockers"]
        or production["upstream_lane_blockers"]
        or production["upstream_relation_blockers"]
    ):
        raise Phase7ConditionalAccessError("Phase 7 production fixture has blockers")
    repeated = build_conditional_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal", scenario_context=scenario
    )
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase7ConditionalAccessError("two-run conditional-access hash differs")
    if production["counts"]["normalized_conditional_rules"] != 1:
        raise Phase7ConditionalAccessError("production fixture rule count differs")
    if production["counts"]["lane_tuples_with_applicable_conditional_rules"] != 1:
        raise Phase7ConditionalAccessError("production fixture applicability differs")
    if not all(
        item["pending_final_permission_resolution"]
        for item in production["access_candidates"]
    ):
        raise Phase7ConditionalAccessError("Phase 7 finalized a permission prematurely")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase7ConditionalAccessError("Phase 7 completion record is not passed")
    for section in ("artifacts", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase7ConditionalAccessError(
                    f"Phase 7 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase7_conditional_access": "passed",
        "fixed_oracle_comparison_count": 3,
        "production_fixture_conditional_rules": 1,
        "production_fixture_applicable_lane_tuples": 1,
        "production_fixture_blockers": 0,
        "final_permission_resolution": "pending_phase8",
        "two_run_determinism": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 7 conditional-access integration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase7_conditional_access()
    except (Phase7ConditionalAccessError, StaticAccessError, KeyError) as error:
        print(json.dumps({"phase7_conditional_access": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
