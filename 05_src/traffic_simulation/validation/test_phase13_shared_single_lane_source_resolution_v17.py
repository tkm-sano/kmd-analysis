from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    SHARED_SINGLE_LANE_DECISION_ID,
    SHARED_SINGLE_LANE_DECISION_VERSION,
    SHARED_SINGLE_LANE_KIND,
    SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
    SHARED_SINGLE_LANE_RULE_ID,
    DirectionalLaneError,
    build_lane_production_artifact,
    resolve_directional_lanes,
)
from traffic_simulation.paths import REPOSITORY_ROOT


DECISION = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_lane_bidirectional_shared_single_lane_decision.yml"
)
SOURCE_SCHEMA = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "shared_lane_source_semantic_v17.schema.json"
)
ATTEMPT_SCHEMA = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "shared_lane_materialization_attempt_v17.schema.json"
)
REGISTRY = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)


def _write_way(path: Path, tags: dict[str, str]) -> None:
    tag_xml = "".join(
        f'<tag k="{key}" v="{value}"/>' for key, value in sorted(tags.items())
    )
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<osm version="0.6" generator="phase13-test">'
        '<node id="1" lat="35.0" lon="139.0"/>'
        '<node id="2" lat="35.0001" lon="139.0001"/>'
        f'<way id="101"><nd ref="1"/><nd ref="2"/>{tag_xml}</way>'
        '</osm>\n',
        encoding="utf-8",
    )


def test_approved_decision_matches_runtime_contract() -> None:
    decision = yaml.safe_load(DECISION.read_text(encoding="utf-8"))

    assert decision["status"] == "approved"
    assert decision["approved_by"] == "repository_owner_directive"
    assert decision["decision_id"] == SHARED_SINGLE_LANE_DECISION_ID
    assert decision["decision_version"] == SHARED_SINGLE_LANE_DECISION_VERSION
    assert decision["source_semantics"]["kind"] == SHARED_SINGLE_LANE_KIND
    assert decision["source_semantics"]["rule_id"] == SHARED_SINGLE_LANE_RULE_ID
    assert decision["materialization_boundary"]["stop_code"] == (
        SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE
    )
    candidate = REPOSITORY_ROOT / decision["approved_candidate"]["path"]
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == decision[
        "approved_candidate"
    ]["byte_sha256"]


def test_rule_and_successor_stop_are_registered() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    rules = {item["rule_id"]: item for item in registry["lane_rules"]}
    stops = {item["stop_code"]: item for item in registry["stop_codes"]}
    assert rules[SHARED_SINGLE_LANE_RULE_ID]["decision_id"] == (
        SHARED_SINGLE_LANE_DECISION_ID
    )
    assert rules[SHARED_SINGLE_LANE_RULE_ID]["priority"] == (
        "before_generic_odd_or_single_stop"
    )
    assert stops[SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE] == {
        "stop_code": SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
        "resolution_status": "valid_but_unsupported",
        "review_required": True,
    }


def test_shared_single_lane_source_semantics_are_rule_derived_and_lossless() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "1"},
        profile="formal",
    )

    assert result["resolution_status"] == "resolved"
    assert result["value_origin"] == "rule_derived"
    assert result["rule_ids"] == [SHARED_SINGLE_LANE_RULE_ID]
    assert result["decision_id"] == SHARED_SINGLE_LANE_DECISION_ID
    assert result["decision_version"] == SHARED_SINGLE_LANE_DECISION_VERSION
    assert result["effective_value"] == {
        "kind": SHARED_SINGLE_LANE_KIND,
        "physical_moving_lane_count": 1,
        "usable_source_directions": ["forward", "backward"],
        "dedicated_moving_lane_count": {"forward": 0, "backward": 0},
    }
    assert result["source_lane_tags"] == {"lanes": "1"}
    assert result["oneway_provenance"] == {
        "canonical_oneway": "no",
        "rule_id": None,
        "source_value": "no",
        "value_origin": "source_explicit",
    }
    assert "total" not in result["effective_value"]
    assert "forward" not in result["effective_value"]
    assert "backward" not in result["effective_value"]


def test_absent_oneway_provenance_is_preserved_for_shared_semantics() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "lanes": "1"}, profile="formal"
    )
    assert result["oneway_provenance"]["canonical_oneway"] == "no"
    assert result["oneway_provenance"]["source_value"] is None
    assert result["oneway_provenance"]["rule_id"] is not None


def test_build_separates_resolved_source_from_unsupported_materialization(
    tmp_path: Path,
) -> None:
    source = tmp_path / "shared.osm.xml"
    _write_way(
        source, {"highway": "residential", "oneway": "no", "lanes": "1"}
    )
    artifact = build_lane_production_artifact(source, profile="formal")

    assert artifact["counts"]["source_semantic_blockers"] == 0
    assert artifact["counts"]["canonical_representation_blockers"] == 0
    assert artifact["counts"]["simulation_materialization_blockers"] == 1
    assert artifact["counts"]["overall_acceptance_blockers"] == 1
    assert len(artifact["source_semantic_records"]) == 1
    assert len(artifact["materialization_attempts"]) == 1
    assert artifact["segment_lanes"] == []
    record = artifact["source_semantic_records"][0]
    attempt = artifact["materialization_attempts"][0]
    blocker = artifact["blockers"][0]
    assert attempt["source_semantic_record_id"] == record["record_id"]
    assert attempt["child_directed_segment_ids"]
    assert attempt["materialization_status"] == "valid_but_unsupported"
    assert attempt["stop_code"] == SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE
    assert blocker["stop_code"] == SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE
    assert blocker["source_semantic_record_id"] == record["record_id"]
    assert blocker["child_directed_segment_ids"] == attempt[
        "child_directed_segment_ids"
    ]
    assert record["source"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    jsonschema.Draft202012Validator(
        json.loads(SOURCE_SCHEMA.read_text(encoding="utf-8"))
    ).validate(record)
    jsonschema.Draft202012Validator(
        json.loads(ATTEMPT_SCHEMA.read_text(encoding="utf-8"))
    ).validate(attempt)


@pytest.mark.parametrize(
    "tags",
    [
        {"highway": "residential", "oneway": "no", "lanes": "3"},
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "lanes:forward": "1",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "lanes:backward": "1",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "lanes:both_ways": "1",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "oneway:conditional": "yes @ (Mo-Fr)",
            "lanes": "1",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "lanes:conditional": "2 @ (Mo-Fr)",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "lanes:reversible": "1",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "oneway:alternating": "yes",
        },
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "1",
            "turn:lanes": "through",
        },
        {"highway": "path", "oneway": "no", "lanes": "1"},
    ],
)
def test_shared_rule_boundary_cases_remain_fail_closed(tags: dict[str, str]) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(tags, profile="formal")
    assert caught.value.stop_code != SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE


def test_existing_lanes2_rule_remains_unchanged() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "2"},
        profile="formal",
    )
    assert result["effective_value"] == {
        "total": 2,
        "forward": 1,
        "backward": 1,
        "both_ways": 0,
    }
    assert result["rule_ids"] != [SHARED_SINGLE_LANE_RULE_ID]


@pytest.mark.parametrize("lanes", ["01", "1.0", "one", "-1", ""])
def test_noncanonical_single_lane_values_remain_invalid(lanes: str) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "residential", "oneway": "no", "lanes": lanes},
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_COUNT_INVALID"


def test_shared_rule_is_record_order_invariant() -> None:
    first = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "1"},
        profile="formal",
    )
    second = resolve_directional_lanes(
        {"lanes": "1", "oneway": "no", "highway": "residential"},
        profile="formal",
    )
    assert first == second
