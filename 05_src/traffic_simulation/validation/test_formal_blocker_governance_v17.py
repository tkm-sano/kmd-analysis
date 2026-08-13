from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from traffic_simulation.network.formal_blocker_governance_v17 import (
    FormalBlockerGovernanceError,
    build_blocker_inventory,
    classify_blocker,
    load_formal_blocker_policy,
    validate_exclusion_manifest,
    validate_formal_blocker_policy,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution"
)
FIXTURES = FIXTURE_ROOT / "formal_blocker_phase13_fixture.yml"
ORACLES = FIXTURE_ROOT / "formal_blocker_phase13_oracle.yml"
HASH = "a" * 64


def load_cases() -> tuple[dict, dict]:
    fixtures = {
        item["fixture_id"]: item["input"]
        for item in yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))["cases"]
    }
    oracles = {
        item["fixture_id"]: item
        for item in yaml.safe_load(ORACLES.read_text(encoding="utf-8"))["oracles"]
    }
    return fixtures, oracles


def policy_with_fixture_exclusion() -> dict:
    policy = copy.deepcopy(load_formal_blocker_policy())
    policy["registered_exclusion_rules"] = [
        {
            "exclusion_rule_id": "FIXTURE-OUTSIDE-AREA-V1",
            "rule_version": "1.0.0",
            "decision_id": "FIXTURE-DECISION-002",
            "scope_predicate": {"fixture_outside_area": True},
            "evidence_sha256": HASH,
            "approver": "independent_fixture_authority",
            "approval_date": "2026-08-04",
        }
    ]
    return policy


def semantic_hash(value: dict) -> str:
    payload = {key: item for key, item in value.items() if key != "semantic_sha256"}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def exclusion_manifest(entries: list[dict], *, governed: int, input_count: int) -> dict:
    manifest = {
        "schema_version": 17,
        "manifest_id": "FIXTURE-EXCLUSION-MANIFEST-V1",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "policy_id": "FORMAL_BLOCKER_POLICY_V17",
        "entries": entries,
        "population_counts": {
            "input": input_count,
            "governed": governed,
            "excluded": len(entries),
        },
    }
    manifest["semantic_sha256"] = semantic_hash(manifest)
    return manifest


def exclusion_entry() -> dict:
    return {
        "record_id": "outside:104",
        "source_way_id": 104,
        "directed_segment_id": None,
        "lane_position": None,
        "vehicle_class": None,
        "attribute_name": "governed_population",
        "reason": "Fixture rule proves the record lies outside the configured area.",
        "exclusion_rule_id": "FIXTURE-OUTSIDE-AREA-V1",
        "decision_id": "FIXTURE-DECISION-002",
        "approver": "independent_fixture_authority",
        "approval_date": "2026-08-04",
        "evidence_sha256": HASH,
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
    }


def test_production_policy_is_valid_and_has_no_exclusion_rules() -> None:
    policy = load_formal_blocker_policy()
    validate_formal_blocker_policy(policy)
    assert policy["default_strategy"] == "preserve_and_resolve"
    assert policy["registered_exclusion_rules"] == []


@pytest.mark.parametrize("fixture_id", ["FB-POS-001", "FB-POS-002", "FB-POS-003"])
def test_independent_strategy_oracles_match(fixture_id: str) -> None:
    fixtures, oracles = load_cases()
    result = classify_blocker(fixtures[fixture_id])
    assert result["selected_strategy"]["value"] == oracles[fixture_id]["selected_strategy"]


def test_unregistered_exclusion_matches_fixed_oracle() -> None:
    fixtures, oracles = load_cases()
    with pytest.raises(FormalBlockerGovernanceError) as caught:
        classify_blocker(fixtures["FB-NEG-001"])
    assert caught.value.stop_code == oracles["FB-NEG-001"]["stop_code"]


def test_registered_fixture_rule_is_the_only_formal_exclusion_route() -> None:
    fixtures, oracles = load_cases()
    result = classify_blocker(
        fixtures["FB-POS-004"], policy=policy_with_fixture_exclusion()
    )
    assert result["selected_strategy"]["value"] == oracles["FB-POS-004"]["selected_strategy"]
    assert "resolution_status" not in result


def test_omitted_identity_field_is_rejected_instead_of_defaulted() -> None:
    fixtures, _ = load_cases()
    broken = copy.deepcopy(fixtures["FB-POS-001"])
    del broken["lane_position"]
    with pytest.raises(FormalBlockerGovernanceError):
        classify_blocker(broken)


def test_permission_blocker_requires_causal_root_record_ids() -> None:
    fixtures, _ = load_cases()
    broken = copy.deepcopy(fixtures["FB-POS-003"])
    broken["root_cause_record_ids"] = []
    with pytest.raises(FormalBlockerGovernanceError):
        classify_blocker(broken)


def test_inventory_is_order_invariant_and_strategies_are_exclusive() -> None:
    fixtures, _ = load_cases()
    blockers = [fixtures[name] for name in ("FB-POS-001", "FB-POS-002", "FB-POS-003")]
    first = build_blocker_inventory(blockers, inventory_id="FIXTURE-INVENTORY-V1")
    second = build_blocker_inventory(list(reversed(blockers)), inventory_id="FIXTURE-INVENTORY-V1")
    assert first == second
    assert first["counts"]["total"] == 3
    assert sum(first["counts"]["by_strategy"].values()) == 3


def test_duplicate_record_cannot_receive_multiple_strategies() -> None:
    fixtures, _ = load_cases()
    duplicate = copy.deepcopy(fixtures["FB-POS-001"])
    duplicate["blocker_id"] = "different-blocker-id"
    with pytest.raises(FormalBlockerGovernanceError):
        build_blocker_inventory(
            [fixtures["FB-POS-001"], duplicate], inventory_id="DUPLICATE"
        )


def test_valid_exclusion_manifest_satisfies_population_equation() -> None:
    validate_exclusion_manifest(
        exclusion_manifest([exclusion_entry()], governed=2, input_count=3),
        governed_record_ids=["governed:1", "governed:2"],
        policy=policy_with_fixture_exclusion(),
    )


def test_population_equation_mismatch_is_rejected() -> None:
    manifest = exclusion_manifest([exclusion_entry()], governed=2, input_count=4)
    with pytest.raises(FormalBlockerGovernanceError):
        validate_exclusion_manifest(
            manifest,
            governed_record_ids=["governed:1", "governed:2"],
            policy=policy_with_fixture_exclusion(),
        )


def test_governed_and_excluded_overlap_is_rejected() -> None:
    with pytest.raises(FormalBlockerGovernanceError):
        validate_exclusion_manifest(
            exclusion_manifest([exclusion_entry()], governed=2, input_count=3),
            governed_record_ids=["outside:104", "governed:2"],
            policy=policy_with_fixture_exclusion(),
        )


def test_production_policy_rejects_fixture_exclusion_manifest() -> None:
    with pytest.raises(FormalBlockerGovernanceError) as caught:
        validate_exclusion_manifest(
            exclusion_manifest([exclusion_entry()], governed=2, input_count=3),
            governed_record_ids=["governed:1", "governed:2"],
        )
    assert caught.value.stop_code == "EXCLUSION_RULE_UNREGISTERED"
