from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from traffic_simulation.network.static_access_v17 import (
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
)
from traffic_simulation.paths import REPOSITORY_ROOT


RESOLUTION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_private_authorization_context_resolution.yml"
)


def _yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_private_authorization_resolution_uses_existing_governed_authority() -> None:
    record = _yaml(RESOLUTION_PATH)

    assert record["resolution_id"] == "RES-P13-PRIVATE-AUTH-CONTEXT-001"
    assert record["status"] == "passed"
    assert record["problem"]["source_way_ids"] == [992482251, 992488487]
    assert record["problem"]["prior_stop_code"] == "ACCESS_CONTEXT_MISSING"
    assert record["problem"]["required_context"] == "private_authorization"
    assert record["problem"]["horse_root_cause"] is False

    assert record["root_cause"]["governed_context_already_fixed"] is True
    assert record["root_cause"]["authorization_ids"] == []
    assert record["root_cause"]["derived_private_authorization"] is False
    assert (
        record["root_cause"]["static_access_default_context_omitted_private_authorization"]
        is True
    )

    authority = record["authority"]["governed_runtime_context"]
    authority_path = REPOSITORY_ROOT / authority["path"]
    assert authority["byte_sha256"] == _sha256(authority_path)
    assert authority["authorization_ids"] == []
    assert authority["private_authorization"] is False

    implementation = record["implementation"]
    assert implementation["way_specific_exception_added"] is False
    assert implementation["private_authorization_hardcoded"] is False
    assert implementation["registry_semantics_changed"] is False
    assert implementation["governed_context_authority_changed"] is False

    runtime_path = REPOSITORY_ROOT / implementation["runtime"]["path"]
    test_path = REPOSITORY_ROOT / implementation["regression_test"]["path"]
    assert implementation["runtime"]["byte_sha256"] == _sha256(runtime_path)
    assert implementation["regression_test"]["byte_sha256"] == _sha256(test_path)


def test_private_access_resolves_denied_from_governed_negative_context() -> None:
    context = default_scenario_context()

    assert context["private_authorization"] is False

    for way_id in (992482251, 992488487):
        rules = normalize_static_access_rules(
            source_way_id=way_id,
            tags={
                "highway": "service",
                "oneway": "yes",
                "lanes": "1",
                "motor_vehicle": "private",
            },
            lane_counts={"forward": 1},
        )["rules"]

        maxima = maximal_static_rules_for_tuple(
            rules,
            direction="forward",
            lane_position=0,
            lane_count=1,
            vehicle_class=context["vehicle_class"],
            context=context,
        )

        assert len(maxima) == 1
        assert maxima[0]["effect"] == "denied"
        assert maxima[0]["authorization_requirement"] == "private_authorization"
        assert maxima[0]["provenance"]["context_evaluation"]["matched"] is False


def test_private_authorization_resolution_records_successor_acceptance() -> None:
    record = _yaml(RESOLUTION_PATH)

    probe = record["full_population_probe"]
    comparison = record["horse_stable_id_recheck"]
    acceptance = record["acceptance"]

    assert probe["static_access_output"]["static_access_blocker_count"] == 187
    assert probe["static_access_output"]["access_context_missing_count"] == 0
    assert probe["static_access_output"]["managed_private_authorization"] is False

    assert all(
        item["remaining_blocker_count"] == 0
        for item in probe["target_way_results"]
    )
    assert all(
        item["effects"] == ["denied"]
        for item in probe["target_way_results"]
    )

    assert comparison["status"] == "passed"
    assert comparison["stable_id_diff"]["new_blocker_id_count"] == 0
    assert (
        comparison["stable_id_diff"]["revealed_private_context_successor_count"]
        == 0
    )
    assert comparison["permission_diff"]["unexpected_permission_change_count"] == 0

    assert acceptance["target_private_context_blockers_are_zero"] is True
    assert acceptance["target_private_ways_resolve_denied"] is True
    assert acceptance["access_context_missing_full_population_is_zero"] is True
    assert acceptance["new_horse_stable_blocker_ids_are_zero"] is True
    assert acceptance["unexpected_permission_changes_are_zero"] is True
    assert acceptance["overall_pass"] is True

    assert record["remaining_scope"]["motorcar_ontology"] == (
        "pending_independent_decision"
    )
    assert record["remaining_scope"]["phase13_complete"] is False
