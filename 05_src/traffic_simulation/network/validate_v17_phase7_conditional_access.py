from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
import jsonschema

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
    evaluate_conditional_access_rules,
    evaluate_conditional_value,
)
from traffic_simulation.network.static_access_v17 import StaticAccessError
from traffic_simulation.network.scenario_context_v17 import (
    ScenarioContextError,
    load_governed_runtime_context,
    validate_governed_runtime_context,
)
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
WARNING_AUDIT_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase7_warning_audit.yml"
)
CONTEXT_FIXTURE_PATH = (
    FIXTURE_ROOT / "governed_runtime_context_phase7.json"
)


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


def _validate_warning_audit() -> dict[str, Any]:
    audit = _load_yaml(WARNING_AUDIT_PATH)
    schema = _load_json(_repo_file(audit["schema"]))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(audit)
    warnings = audit["warning_classification"]
    warning_ids = [item["warning_id"] for item in warnings]
    if len(warning_ids) != len(set(warning_ids)):
        raise Phase7ConditionalAccessError("duplicate warning audit ID")
    diagnostic_count = sum(item["occurrence_count"] for item in warnings)
    if diagnostic_count != audit["prior_host_diagnostic_run"]["warning_event_count"]:
        raise Phase7ConditionalAccessError("warning audit event total differs")
    for item in warnings:
        by_test = item.get("occurrences_by_test")
        if by_test is not None and sum(by_test.values()) != item["occurrence_count"]:
            raise Phase7ConditionalAccessError(
                f"warning occurrence breakdown differs: {item['warning_id']}"
            )
    governed = audit["governed_run"]
    if governed["warning_event_count"] != 0 or governed["blocking_warning_count"] != 0:
        raise Phase7ConditionalAccessError("governed warning gate is not clean")
    environment = governed["environment"]
    for prefix in ("compose", "dockerfile", "requirements"):
        path = _repo_file(environment[f"{prefix}_path"])
        if _sha256(path) != environment[f"{prefix}_sha256"]:
            raise Phase7ConditionalAccessError(
                f"warning audit environment hash differs: {prefix}"
            )
    return audit


def validate_phase7_conditional_access() -> dict[str, Any]:
    validate_phase6_static_access()
    validate_fixture_oracle()
    governed_context = load_governed_runtime_context()
    warning_audit = _validate_warning_audit()
    fixtures, oracles = _indexes()

    context_cases = _load_json(CONTEXT_FIXTURE_PATH)["cases"]
    positive_context = context_cases[0]["oracle"]
    for field, expected in positive_context.items():
        if governed_context[field] != expected:
            raise Phase7ConditionalAccessError(
                f"governed context oracle mismatch: {field}"
            )
    negative_context = context_cases[1]
    context_artifact = _load_yaml(
        _repo_file(context_cases[0]["input"]["path"])
    )
    broken_context = copy.deepcopy(context_artifact)
    del broken_context["vehicle_context"]["authorization_ids"]
    try:
        validate_governed_runtime_context(broken_context)
    except ScenarioContextError as error:
        if error.stop_code != negative_context["oracle"]["stop_code"]:
            raise Phase7ConditionalAccessError(
                "governed negative context oracle mismatch"
            ) from error
    else:
        raise Phase7ConditionalAccessError("missing authorization context passed")

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

    governed_production = build_conditional_access_production_artifact(
        PRODUCTION_FIXTURE, profile="formal"
    )
    if governed_production["scenario_context"]["scenario_context_id"] != governed_context[
        "scenario_context_id"
    ]:
        raise Phase7ConditionalAccessError("governed context was not used by production")
    if any(
        item["stop_code"] == "ACCESS_CONTEXT_MISSING"
        for item in governed_production["blockers"]
    ):
        raise Phase7ConditionalAccessError("governed fixture has missing context")

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
        "fixed_oracle_comparison_count": 5,
        "production_fixture_conditional_rules": 1,
        "production_fixture_applicable_lane_tuples": 1,
        "production_fixture_blockers": 0,
        "governed_runtime_interval_context": governed_context[
            "scenario_context_id"
        ],
        "governed_blocking_warning_count": warning_audit["governed_run"][
            "blocking_warning_count"
        ],
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
    except (
        Phase7ConditionalAccessError,
        ScenarioContextError,
        StaticAccessError,
        jsonschema.ValidationError,
        KeyError,
    ) as error:
        print(json.dumps({"phase7_conditional_access": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
