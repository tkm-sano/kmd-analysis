from __future__ import annotations

from pathlib import Path

from traffic_simulation.network.conditional_access_v17 import (
    evaluate_conditional_access_rules,
)
from traffic_simulation.network.final_permission_v17 import (
    build_final_permission_production_artifact,
    maximal_rules,
    resolve_permission,
    rule_dominates,
    write_artifact_atomic,
)
from traffic_simulation.network.static_access_v17 import normalize_static_access_rules
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)
BASE = {"highway": "residential", "oneway": "yes", "lanes": "2"}
CONTEXT = {
    "vehicle_class": "delivery",
    "weekday": "Mo",
    "time": "08:00",
    "trip_purpose": "delivery",
    "permit_ids": [],
    "authorization_ids": [],
}


def _rules(tags):
    return normalize_static_access_rules(
        source_way_id=1001,
        tags={**BASE, **tags},
        lane_counts={"forward": 2},
    )["rules"]


def _conditional(expression: str):
    return evaluate_conditional_access_rules(
        source_way_id=1001,
        conditional_tags={"access:conditional": expression},
        tags=BASE,
        lane_counts={"forward": 2},
        context=CONTEXT,
    )["rules"]


def test_vehicle_axis_dominates_general_rule() -> None:
    by_key = {
        item["source_key"]: item
        for item in _rules({"access": "no", "goods": "yes"})
    }
    general, vehicle = by_key["access"], by_key["goods"]
    assert rule_dominates(vehicle, general, lane_count=2)
    assert resolve_permission([general, vehicle], lane_count=2)[
        "effective_permission"
    ] == "allowed"


def test_conditional_temporal_domain_dominates_unconditional() -> None:
    static = _rules({"access": "yes"})[0]
    conditional = _conditional("no @ (Mo-Fr 07:00-09:00)")[0]
    assert rule_dominates(conditional, static, lane_count=2)
    decision = resolve_permission([static, conditional], lane_count=2)
    assert decision["effective_permission"] == "denied"
    assert decision["maximal_rule_ids"] == [conditional["rule_id"]]


def test_incomparable_same_effect_rules_preserve_all_provenance() -> None:
    selected = maximal_rules(
        _rules({"goods": "yes", "access:lanes": "yes|"}), lane_count=2
    )
    decision = resolve_permission(selected, lane_count=2)
    assert decision["effective_permission"] == "allowed"
    assert len(decision["maximal_rule_ids"]) == 2
    assert len(decision["maximal_rules"]) == 2


def test_incomparable_different_effect_rules_stop() -> None:
    decision = resolve_permission(
        _rules({"goods": "no", "access:lanes": "yes|"}), lane_count=2
    )
    assert decision["resolution_status"] == "conflict"
    assert decision["stop_code"] == "ACCESS_SPECIFICITY_CONFLICT"
    assert len(decision["conflicting_candidates"]) == 2


def test_empty_maximal_set_emits_unresolved_permission() -> None:
    decision = resolve_permission([], lane_count=1)
    assert decision["resolution_status"] == "unresolved"
    assert decision["stop_code"] == "ACCESS_PERMISSION_UNRESOLVED"


def test_rule_order_is_not_a_tiebreak() -> None:
    rules = _rules({"goods": "yes", "access:lanes": "yes|"})
    assert resolve_permission(rules, lane_count=2) == resolve_permission(
        list(reversed(rules)), lane_count=2
    )


def test_production_fixture_emits_complete_final_permissions() -> None:
    artifact = build_final_permission_production_artifact(
        FIXTURE,
        profile="formal",
        scenario_context={"weekday": "Mo", "time": "08:00"},
    )
    assert artifact["formal_permission_complete"] is True
    assert artifact["record_coverage_complete"] is True
    assert artifact["permission_authority"] == "resolver_expected_permissions"
    assert artifact["typemap_role"] == "provisional_topology_candidate_only"
    assert artifact["counts"] == {
        "governed_lane_tuples": 14,
        "permission_records": 14,
        "resolved_permissions": 14,
        "unresolved_permissions": 0,
        "conflicting_permissions": 0,
        "permission_blockers": 0,
        "upstream_blockers": 0,
    }
    way_1002 = [
        item for item in artifact["permission_records"] if item["source_way_id"] == 1002
    ]
    assert len(way_1002) == 1
    assert way_1002[0]["effective_permission"] == "denied"
    assert way_1002[0]["provenance"]["typemap_permission_used"] is False


def test_governed_context_uses_static_permission_after_conditional_window() -> None:
    artifact = build_final_permission_production_artifact(FIXTURE, profile="formal")
    way_1002 = [
        item for item in artifact["permission_records"] if item["source_way_id"] == 1002
    ]
    assert way_1002[0]["effective_permission"] == "allowed"


def test_lane_local_provenance_is_not_copied() -> None:
    artifact = build_final_permission_production_artifact(
        FIXTURE,
        profile="formal",
        scenario_context={"weekday": "Mo", "time": "08:00"},
    )
    records = sorted(
        (item for item in artifact["permission_records"] if item["source_way_id"] == 1003),
        key=lambda item: item["lane_position"],
    )
    assert records[0]["provenance"]["maximal_rules"][0]["target_scope"][
        "lane_scope"
    ]["positions"] == [0]
    assert records[1]["provenance"]["maximal_rules"][0]["target_scope"][
        "lane_scope"
    ]["positions"] == [1]


def test_production_artifact_is_deterministic() -> None:
    context = {"weekday": "Mo", "time": "08:00"}
    first = build_final_permission_production_artifact(
        FIXTURE, profile="formal", scenario_context=context
    )
    second = build_final_permission_production_artifact(
        FIXTURE, profile="formal", scenario_context=context
    )
    assert first == second


def test_writer_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    artifact = build_final_permission_production_artifact(FIXTURE, profile="formal")
    output = tmp_path / "final-permission.json"
    write_artifact_atomic(artifact, output)
    assert output.is_file()
    try:
        write_artifact_atomic(artifact, output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("final permission writer overwrote an artifact")
