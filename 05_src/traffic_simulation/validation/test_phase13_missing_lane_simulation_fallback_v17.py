from __future__ import annotations

import hashlib
import gzip
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from traffic_simulation.network.simulation_lane_fallback_v17 import (
    ASSUMPTION_ID,
    ASSUMPTION_VERSION,
    DECISION_ID,
    POLICY_VERSION,
    allocate_assumed_lanes,
    build_simulation_collection,
    lower_tie_mode,
    resolve_simulation_lanes,
    select_calibration_group,
)
from traffic_simulation.paths import REPOSITORY_ROOT


DECISION = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_missing_lane_simulation_fallback_decision.yml"
)
POLICY = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_missing_lane_simulation_fallback_policy.yml"
)
ASSUMPTION_SCHEMA = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "missing_lane_simulation_assumption_v17.schema.json"
)
MANIFEST_SCHEMA = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "missing_lane_simulation_manifest_v17.schema.json"
)
SOURCE_HASH = "8b5157e48c3c87c2b4430f56d6abe292ce1ea5449b374ae4cb395fc19475b67d"
CALIBRATION_HASH = "9b7f3016e9f3e2d747bfb2e49ccfddc15dd4b1e90e88f1d8db5d5a0814e336ca"
OUTPUT = REPOSITORY_ROOT / (
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260822_missing_lane_simulation_fallback_tdd"
)


def _assumed(tags: dict[str, str], *, scenario: str = "baseline", way_id: int = 101) -> dict:
    return resolve_simulation_lanes(
        tags,
        source_way_id=way_id,
        source_osm_hash=SOURCE_HASH,
        scenario=scenario,
    )


def test_approved_decision_and_policy_are_hash_bound() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))

    assert decision["status"] == "approved"
    assert decision["approved_by"] == "repository_owner_directive"
    assert decision["decision_type"] == "SIMULATION_MODEL_ASSUMPTION_POLICY"
    assert decision["decision_id"] == DECISION_ID
    assert policy["policy_version"] == POLICY_VERSION
    assert policy["provenance"]["assumption_id"] == ASSUMPTION_ID
    assert policy["provenance"]["assumption_version"] == ASSUMPTION_VERSION
    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == decision[
        "approved_policy"
    ]["byte_sha256"]


def test_L1_and_L4_missing_evidence_are_simulation_eligible() -> None:
    l1 = _assumed({"highway": "service", "oneway": "no"}, way_id=101)
    l4 = _assumed({"highway": "primary", "oneway": "yes"}, way_id=102)

    assert l1["resolution_status"] == "resolved_for_simulation"
    assert l1["cluster_id"] == "L1_BIDIRECTIONAL_NO_LANE_COUNT"
    assert l4["resolution_status"] == "resolved_for_simulation"
    assert l4["cluster_id"] == "L4_ONEWAY_COUNT_MISSING"
    assert l1["value_origin"] == l4["value_origin"] == "model_assumed"


@pytest.mark.parametrize(
    ("tags", "expected_level"),
    [
        ({"highway": "primary", "oneway": "yes", "lanes": "2"}, "formal_source_resolved"),
        ({"highway": "primary", "oneway": "no", "lanes": "4"}, "not_applicable_out_of_scope_fail_closed"),
        ({"highway": "primary", "oneway": "no", "lanes:forward": "1"}, "not_applicable_out_of_scope_fail_closed"),
        ({"highway": "primary", "oneway": "no", "lanes": "3"}, "not_applicable_out_of_scope_fail_closed"),
        ({"highway": "residential", "oneway": "no", "lanes": "1"}, "not_applicable_shared_physical_unsupported"),
        ({"highway": "primary", "oneway": "yes", "lanes": "2", "turn:lanes": "left"}, "not_applicable_conflict_fail_closed"),
        ({"highway": "primary", "oneway": "yes", "lanes": "2", "lanes:forward": "3"}, "not_applicable_conflict_fail_closed"),
    ],
)
def test_fallback_does_not_cross_formal_or_excluded_boundaries(
    tags: dict[str, str], expected_level: str
) -> None:
    result = _assumed(tags)
    assert result["fallback_level"] == expected_level
    assert result["value_origin"] != "model_assumed"
    assert result["assumption_record"] is None


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [("conservative", 1), ("baseline", 1), ("high_capacity", 3)],
)
def test_approved_service_oneway_scenarios(scenario: str, expected: int) -> None:
    result = _assumed(
        {"highway": "service", "oneway": "yes"}, scenario=scenario
    )
    assert result["effective_value"] == {
        "total": expected,
        "forward": expected,
        "backward": 0,
        "both_ways": 0,
    }


def test_minimum_sample_boundary_uses_global_at_29_and_class_at_30() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    at_29 = select_calibration_group(
        policy, "service", "oneway", sample_count_override=29
    )
    at_30 = select_calibration_group(
        policy, "service", "oneway", sample_count_override=30
    )
    assert at_29 == ("global_directionality_fallback", "GLOBAL|oneway")
    assert at_30 == (
        "class_directionality_calibrated_default",
        "service|oneway",
    )


def test_equal_frequency_mode_uses_smaller_lane_count() -> None:
    assert lower_tie_mode([2] * 25 + [5] * 25 + [4] * 10) == 2


def test_bidirectional_even_and_odd_allocations_are_deterministic() -> None:
    assert allocate_assumed_lanes(4, "no") == {
        "total": 4, "forward": 2, "backward": 2, "both_ways": 0
    }
    assert allocate_assumed_lanes(5, "no") == {
        "total": 5, "forward": 3, "backward": 2, "both_ways": 0
    }


def test_current_reverse_oneway_places_assumed_lane_backward() -> None:
    result = _assumed(
        {"highway": "unclassified", "oneway": "-1"},
        scenario="conservative",
        way_id=263457004,
    )
    assert result["effective_value"] == {
        "total": 1, "forward": 0, "backward": 1, "both_ways": 0
    }


def test_assumption_provenance_is_complete_and_schema_valid() -> None:
    result = _assumed(
        {"highway": "primary", "oneway": "yes"},
        scenario="high_capacity",
        way_id=202,
    )
    record = result["assumption_record"]
    assert record["value_origin"] == "model_assumed"
    assert record["formal_blocker_preserved"] is True
    assert record["source_osm_hash"] == SOURCE_HASH
    assert record["calibration_population_hash"] == CALIBRATION_HASH
    assert record["scenario"] == "high_capacity"
    assert record["fallback_level"] == "class_directionality_calibrated_default"
    jsonschema.Draft202012Validator(
        json.loads(ASSUMPTION_SCHEMA.read_text(encoding="utf-8"))
    ).validate(record)


def test_record_order_does_not_change_collection_or_hash() -> None:
    ways = [
        {"source_way_id": 2, "tags": {"highway": "service", "oneway": "no"}},
        {"source_way_id": 1, "tags": {"highway": "primary", "oneway": "yes"}},
        {"source_way_id": 3, "tags": {"highway": "residential", "oneway": "no", "lanes": "2"}},
    ]
    first = build_simulation_collection(
        ways, source_osm_hash=SOURCE_HASH, scenario="baseline"
    )
    second = build_simulation_collection(
        list(reversed(ways)), source_osm_hash=SOURCE_HASH, scenario="baseline"
    )
    assert first == second
    assert first["semantic_sha256"] == second["semantic_sha256"]
    jsonschema.Draft202012Validator(
        json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    ).validate(first["manifest"])


def test_formal_resolver_output_is_unchanged_by_simulation_call() -> None:
    tags = {"highway": "residential", "oneway": "no"}
    first = _assumed(tags)
    second = _assumed(tags)
    assert first == second
    assert first["formal_stop_code"] == "LANE_DIRECTIONAL_ALLOCATION_MISSING"
    assert first["formal_blocker_preserved"] is True


@pytest.mark.parametrize(
    ("scenario", "expected_total"),
    [("conservative", 41634), ("baseline", 42172), ("high_capacity", 43990)],
)
def test_full_population_manifest_matches_approved_accounting(
    scenario: str, expected_total: int
) -> None:
    manifest = json.loads(
        (OUTPUT / f"manifest_{scenario}.json").read_text(encoding="utf-8")
    )
    assert manifest["assumed_way_count"] == 22627
    assert manifest["assumed_lane_totals"]["total"] == expected_total
    assert manifest["by_cluster"]["L1_BIDIRECTIONAL_NO_LANE_COUNT"][
        "way_count"
    ] == 19007
    assert manifest["by_cluster"]["L4_ONEWAY_COUNT_MISSING"][
        "way_count"
    ] == 3620
    assert manifest["by_fallback_level"] == {
        "class_directionality_calibrated_default": 22410,
        "global_directionality_fallback": 217,
    }
    assert manifest["formal_source_usage_count"] == 3286
    assert manifest["conflicts_excluded"] == 25
    assert manifest["shared_unsupported_excluded"] == 180
    assert manifest["out_of_scope_excluded"] == 102
    assert manifest["formal_blockers_preserved"] == 22627


def test_full_population_contains_real_reverse_oneway_assumption() -> None:
    with gzip.open(
        OUTPUT / "simulation_conservative.json.gz", "rt", encoding="utf-8"
    ) as stream:
        collection = json.load(stream)
    record = next(
        item
        for item in collection["assumption_records"]
        if item["source_way_id"] == 263457004
    )
    assert record["canonical_oneway"] == "-1"
    assert record["chosen_lane_count"] == {
        "total": 1, "forward": 0, "backward": 1, "both_ways": 0
    }


def test_persisted_stable_id_and_formal_state_comparators_pass() -> None:
    stable = json.loads(
        (OUTPUT / "stable_id_comparator.json").read_text(encoding="utf-8")
    )
    formal = json.loads(
        (OUTPUT / "formal_state_comparator.json").read_text(encoding="utf-8")
    )
    assert stable["status"] == "passed"
    assert all(
        not value["added_way_ids"]
        and not value["removed_way_ids"]
        and value["value_mismatch_count"] == 0
        for value in stable["by_scenario"].values()
    )
    assert formal["status"] == "passed"
    assert all(formal["checks"].values())
    assert formal["static_access"]["status"] == "passed"
