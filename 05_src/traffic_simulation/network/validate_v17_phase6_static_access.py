from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    build_static_access_production_artifact,
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
    resolve_maximal_static_effect,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase5_directional_lanes import (
    validate_phase5_directional_lanes,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase6_completion.yml"
)
PRODUCTION_FIXTURE = FIXTURE_ROOT / "directed_segments_phase4.osm.xml"
BASE_TAGS = {"highway": "residential", "oneway": "yes", "lanes": "2"}


class Phase6StaticAccessError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase6StaticAccessError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase6StaticAccessError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase6StaticAccessError(f"invalid repository artifact: {relative}")
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


def _rules(tags: Mapping[str, Any], *, candidate_keys=None) -> list[dict[str, Any]]:
    return normalize_static_access_rules(
        source_way_id=1001,
        tags={**BASE_TAGS, **{key: str(value) for key, value in tags.items()}},
        lane_counts={"forward": 2},
        candidate_keys=candidate_keys,
    )["rules"]


def _effect(
    rules: list[dict[str, Any]],
    *,
    direction: str = "forward",
    lane_position: int = 0,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected = maximal_static_rules_for_tuple(
        rules,
        direction=direction,
        lane_position=lane_position,
        lane_count=2,
        vehicle_class="delivery",
        context=default_scenario_context() if context is None else context,
    )
    return resolve_maximal_static_effect(selected)


def _assert_effect(
    fixture_id: str,
    fixtures: Mapping[str, Any],
    oracles: Mapping[str, Any],
    *,
    lane_position: int = 0,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    fixture = fixtures[fixture_id]
    oracle = oracles[fixture["oracle_id"]]
    result = _effect(
        _rules(fixture["input"]["tags"]),
        direction=fixture["input"].get("direction", "forward"),
        lane_position=lane_position,
        context=context,
    )
    if result["effect"] != oracle["effective_value"]:
        raise Phase6StaticAccessError(f"fixed access oracle mismatch: {fixture_id}")
    return result


def validate_phase6_static_access() -> dict[str, Any]:
    validate_phase5_directional_lanes()
    validate_fixture_oracle()
    fixtures, oracles = _indexes()

    _assert_effect("V17-POS-011", fixtures, oracles)
    _assert_effect("V17-POS-012", fixtures, oracles)
    _assert_effect("V17-POS-013", fixtures, oracles)
    _assert_effect("V17-POS-014", fixtures, oracles, lane_position=1)
    same_result = _effect(_rules({"goods": "yes", "access:lanes": "yes|"}))
    if (
        same_result["effect"]
        != oracles[fixtures["V17-POS-016"]["oracle_id"]]["effective_value"]
        or len(same_result["maximal_rule_ids"]) != 2
    ):
        raise Phase6StaticAccessError("fixed same-result maxima oracle mismatch")
    _assert_effect(
        "V17-POS-021",
        fixtures,
        oracles,
        context={"vehicle_class": "delivery", "permit_assignment": False},
    )

    negative_cases = {
        "V17-NEG-039": lambda value: _rules(value["tags"]),
        "V17-NEG-040": lambda value: _rules(value["tags"]),
        "V17-NEG-041": lambda value: _rules(
            value["tags"], candidate_keys=set(value["tags"])
        ),
        "V17-NEG-043": lambda value: _effect(
            _rules(value["tags"]), context=value["scenario"]
        ),
        "V17-NEG-045": lambda _value: _effect(
            _rules({"goods": "no", "access:lanes": "yes|"})
        ),
    }
    for fixture_id, operation in negative_cases.items():
        fixture = fixtures[fixture_id]
        oracle = oracles[fixture["oracle_id"]]
        try:
            operation(fixture["input"])
        except StaticAccessError as error:
            if error.stop_code != oracle["stop_code"]:
                raise Phase6StaticAccessError(
                    f"fixed access stop-code mismatch: {fixture_id}"
                ) from error
        else:
            raise Phase6StaticAccessError(
                f"negative static-access fixture passed: {fixture_id}"
            )

    independent = _rules({"goods": "yes", "access:lanes": "yes|"})
    first = _effect(independent)
    second = _effect(list(reversed(independent)))
    if first != second:
        raise Phase6StaticAccessError("fixed rule-order metamorphic oracle mismatch")

    production = build_static_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal"
    )
    if (
        production["blockers"]
        or production["upstream_lane_blockers"]
        or production["upstream_relation_blockers"]
    ):
        raise Phase6StaticAccessError("Phase 6 production fixture has blockers")
    repeated = build_static_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal"
    )
    if production["semantic_sha256"] != repeated["semantic_sha256"]:
        raise Phase6StaticAccessError("two-run static-access hash differs")
    if production["counts"]["normalized_rules"] != 8:
        raise Phase6StaticAccessError("production fixture rule count differs")
    if not all(
        item["pending_final_permission_resolution"]
        for item in production["static_maxima"]
    ):
        raise Phase6StaticAccessError("Phase 6 finalized a permission prematurely")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase6StaticAccessError("Phase 6 completion record is not passed")
    for section in ("artifacts", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase6StaticAccessError(
                    f"Phase 6 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase6_static_access": "passed",
        "fixed_oracle_comparison_count": 12,
        "production_fixture_normalized_rules": production["counts"][
            "normalized_rules"
        ],
        "production_fixture_static_lane_tuples": production["counts"][
            "static_lane_tuples"
        ],
        "production_fixture_blockers": 0,
        "conditional_evaluation": "deferred_to_phase7",
        "final_permission_resolution": "pending",
        "two_run_determinism": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate v17 Phase 6 static-access production integration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase6_static_access()
    except (Phase6StaticAccessError, StaticAccessError, KeyError) as error:
        print(json.dumps({"phase6_static_access": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
