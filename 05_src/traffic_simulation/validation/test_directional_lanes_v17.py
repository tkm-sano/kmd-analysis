from __future__ import annotations

import json
from pathlib import Path

import pytest

from traffic_simulation.network.directional_lanes_v17 import (
    ASSUMPTION_ID,
    DirectionalLaneError,
    LANES2_FORMAL_RULE_ID,
    ONEWAY_ROAD_LANE_VECTOR_RULE_ID,
    build_lane_production_artifact,
    materialize_segment_lanes,
    resolve_directional_lanes,
    validate_lane_vector,
    write_artifact_atomic,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)


def test_formal_explicit_bidirectional_lanes_resolve() -> None:
    result = resolve_directional_lanes(
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "4",
            "lanes:forward": "2",
            "lanes:backward": "2",
        },
        profile="formal",
    )
    assert result["value_origin"] == "source_explicit"
    assert result["effective_value"] == {
        "total": 4,
        "forward": 2,
        "backward": 2,
        "both_ways": 0,
    }
    assert result["formal_eligible"] is True


def test_both_ways_participates_in_total_equation() -> None:
    result = resolve_directional_lanes(
        {
            "highway": "residential",
            "oneway": "no",
            "lanes": "5",
            "lanes:forward": "2",
            "lanes:backward": "2",
            "lanes:both_ways": "1",
        },
        profile="formal",
    )
    assert result["effective_value"] == {
        "total": 5,
        "forward": 2,
        "backward": 2,
        "both_ways": 1,
    }


def test_structural_even_split_is_explicitly_nonformal() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "4"},
        profile="structural",
    )
    assert result["value_origin"] == "model_assumed"
    assert result["assumption_ids"] == [ASSUMPTION_ID]
    assert result["formal_eligible"] is False
    assert result["effective_value"]["forward"] == 2
    assert result["effective_value"]["backward"] == 2


@pytest.mark.parametrize("lanes", ["4", "3"])
def test_formal_total_only_bidirectional_stops(lanes: str) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "residential", "oneway": "no", "lanes": lanes},
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_bidirectional_lanes2_total_only_is_rule_derived() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "2"},
        profile="formal",
    )

    assert result["value_origin"] == "rule_derived"
    assert result["rule_ids"] == [LANES2_FORMAL_RULE_ID]
    assert result["assumption_ids"] == []
    assert result["formal_eligible"] is True
    assert result["effective_value"] == {
        "total": 2,
        "forward": 1,
        "backward": 1,
        "both_ways": 0,
    }


def test_lanes2_formal_rule_preserves_source_lanes_value() -> None:
    result = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "2"},
        profile="formal",
    )
    assert result["source_lane_tags"] == {"lanes": "2"}


@pytest.mark.parametrize("lanes", ["3", "1"])
def test_structural_odd_or_single_lane_is_not_split(lanes: str) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "residential", "oneway": "no", "lanes": lanes},
            profile="structural",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_structural_lane_conditional_prohibits_even_split() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "4",
                "lanes:conditional": "3 @ (Mo-Fr)",
            },
            profile="structural",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_lanes2_conditional_is_not_split() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "2",
                "lanes:conditional": "3 @ (Mo-Fr)",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_lanes2_both_ways_is_not_split() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "2",
                "lanes:both_ways": "1",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_lanes2_partial_directional_evidence_is_not_split() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "2",
                "lanes:forward": "2",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_lanes2_vector_conflict_remains_fail_closed() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "2",
                "turn:lanes:forward": "through|right",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_VECTOR_LENGTH_MISMATCH"


def test_formal_lanes2_rule_is_record_order_invariant() -> None:
    first = resolve_directional_lanes(
        {"highway": "residential", "oneway": "no", "lanes": "2"},
        profile="formal",
    )
    second = resolve_directional_lanes(
        {"lanes": "2", "oneway": "no", "highway": "residential"},
        profile="formal",
    )
    assert first == second


def test_oneway_total_is_rule_derived_to_active_direction() -> None:
    forward = resolve_directional_lanes(
        {"highway": "residential", "oneway": "yes", "lanes": "2"},
        profile="formal",
    )
    backward = resolve_directional_lanes(
        {"highway": "residential", "oneway": "-1", "lanes": "2"},
        profile="formal",
    )
    assert forward["effective_value"]["forward"] == 2
    assert forward["effective_value"]["backward"] == 0
    assert backward["effective_value"]["forward"] == 0
    assert backward["effective_value"]["backward"] == 2
    assert forward["rule_ids"] == ["OSM_ONEWAY_TOTAL_TO_ACTIVE_DIRECTION"]


@pytest.mark.parametrize(
    ("vector_key", "vector_value", "expected_count"),
    [
        ("turn:lanes", "through", 1),
        ("turn:lanes", "left|through", 2),
        ("destination:lanes", "A|B|C", 3),
        ("destination:ref:lanes", "R1|R2", 2),
    ],
)
def test_formal_oneway_missing_count_is_derived_from_approved_road_lane_vector(
    vector_key: str, vector_value: str, expected_count: int
) -> None:
    result = resolve_directional_lanes(
        {"highway": "tertiary", "oneway": "yes", vector_key: vector_value},
        profile="formal",
    )

    assert result["effective_value"] == {
        "total": expected_count,
        "forward": expected_count,
        "backward": 0,
        "both_ways": 0,
    }
    assert result["value_origin"] == "rule_derived"
    assert result["rule_ids"] == [ONEWAY_ROAD_LANE_VECTOR_RULE_ID]
    assert result["assumption_ids"] == []
    assert result["formal_eligible"] is True
    assert result["source_lane_tags"] == {vector_key: vector_value}


def test_formal_oneway_missing_count_accepts_equal_approved_vector_lengths() -> None:
    result = resolve_directional_lanes(
        {
            "highway": "tertiary",
            "oneway": "yes",
            "turn:lanes": "left|through",
            "destination:lanes": "A|B",
        },
        profile="formal",
    )
    assert result["effective_value"]["forward"] == 2
    assert result["lane_vectors"]["forward"] == {
        "destination:lanes": ["A", "B"],
        "turn:lanes": ["left", "through"],
    }


def test_formal_oneway_missing_count_conflicting_approved_vectors_remain_closed() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "primary",
                "oneway": "yes",
                "turn:lanes": "left|through",
                "destination:lanes": "A|B|C",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


@pytest.mark.parametrize(
    ("vector_key", "vector_value"),
    [
        ("cycleway:lanes", "pictogram"),
        ("bicycle:lanes", "yes|designated"),
        ("bus:lanes", "yes|designated"),
        ("access:lanes", "yes|no"),
        ("foo:lanes", "a|b"),
    ],
)
def test_formal_oneway_missing_count_rejects_unapproved_lane_vector_authority(
    vector_key: str, vector_value: str
) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "unclassified", "oneway": "yes", vector_key: vector_value},
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_reverse_oneway_vector_count_targets_active_backward_direction() -> None:
    result = resolve_directional_lanes(
        {
            "highway": "tertiary",
            "oneway": "-1",
            "turn:lanes": "left|through",
        },
        profile="formal",
    )
    assert result["effective_value"] == {
        "total": 2,
        "forward": 0,
        "backward": 2,
        "both_ways": 0,
    }
    assert result["lane_vectors"]["backward"]["turn:lanes"] == [
        "left",
        "through",
    ]


def test_explicit_oneway_lane_count_still_validates_approved_vector_length() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "tertiary",
                "oneway": "yes",
                "lanes": "1",
                "turn:lanes": "left|through",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_VECTOR_LENGTH_MISMATCH"


def test_formal_oneway_road_lane_vector_rule_is_record_order_invariant() -> None:
    first = resolve_directional_lanes(
        {
            "highway": "tertiary",
            "oneway": "yes",
            "turn:lanes": "left|through",
            "destination:lanes": "A|B",
        },
        profile="formal",
    )
    second = resolve_directional_lanes(
        {
            "destination:lanes": "A|B",
            "turn:lanes": "left|through",
            "oneway": "yes",
            "highway": "tertiary",
        },
        profile="formal",
    )
    assert first == second


def test_structural_oneway_missing_count_does_not_promote_road_lane_vector() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "tertiary", "oneway": "yes", "turn:lanes": "through"},
            profile="structural",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_formal_oneway_conditional_lane_vector_is_not_count_authority() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "tertiary",
                "oneway": "yes",
                "turn:lanes": "through",
                "turn:lanes:conditional": "left @ (Mo-Fr)",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_oneway_inactive_direction_is_a_conflict() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "yes",
                "lanes": "2",
                "lanes:backward": "1",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_COUNT_CONFLICT"


@pytest.mark.parametrize("value", ["0", "-1", "2.5", "two"])
def test_invalid_total_lane_count_stops(value: str) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "residential", "oneway": "yes", "lanes": value},
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_COUNT_INVALID"


def test_total_directional_conflict_stops() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "4",
                "lanes:forward": "3",
                "lanes:backward": "2",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_COUNT_CONFLICT"


def test_arithmetic_complement_is_not_adopted() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "4",
                "lanes:forward": "3",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_lane_vector_preserves_empty_entry_and_validates_length() -> None:
    assert validate_lane_vector(3, ["50", "", "40"]) == ["50", "", "40"]
    with pytest.raises(DirectionalLaneError) as caught:
        validate_lane_vector(3, ["50", "40"])
    assert caught.value.stop_code == "LANE_VECTOR_LENGTH_MISMATCH"


def test_backward_vector_is_not_reversed_again() -> None:
    resolution = resolve_directional_lanes(
        {
            "highway": "residential",
            "oneway": "-1",
            "lanes": "2",
            "access:lanes:backward": "yes|no",
        },
        profile="formal",
    )
    segment = {
        "directed_segment_id": "ds:1:0:2:backward",
        "source_way_id": 1,
        "source_direction": "backward",
    }
    materialized = materialize_segment_lanes(segment, resolution)
    assert materialized["lanes"] == [
        {
            "lane_position": 0,
            "sumo_lane_index": 1,
            "source_vector_values": {"access:lanes:backward": "yes"},
        },
        {
            "lane_position": 1,
            "sumo_lane_index": 0,
            "source_vector_values": {"access:lanes:backward": "no"},
        },
    ]


def test_unsuffixed_bidirectional_vector_stops() -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {
                "highway": "residential",
                "oneway": "no",
                "lanes": "4",
                "lanes:forward": "2",
                "lanes:backward": "2",
                "access:lanes": "yes|no",
            },
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


def test_production_fixture_materializes_every_directed_segment() -> None:
    artifact = build_lane_production_artifact(FIXTURE, profile="formal")
    assert artifact["blockers"] == []
    assert artifact["upstream_blockers"] == []
    assert artifact["counts"] == {
        "source_ways": 5,
        "resolved_source_ways": 5,
        "directed_segments_with_lanes": 8,
        "directional_lanes": 14,
        "lane_blockers": 0,
        "source_semantic_resolved": 5,
        "source_semantic_blockers": 0,
        "canonical_representation_resolved": 5,
        "canonical_representation_blockers": 0,
        "simulation_materialization_blockers": 0,
        "overall_acceptance_blockers": 0,
        "shared_source_semantic_records": 0,
        "materialization_attempts": 0,
        "upstream_blockers": 0,
    }
    reverse = next(
        item
        for item in artifact["segment_lanes"]
        if item["directed_segment_id"] == "ds:1004:0:2:backward"
    )
    assert reverse["lanes"][0]["source_vector_values"] == {
        "access:lanes:backward": "yes"
    }


def test_production_fixture_is_deterministic() -> None:
    first = build_lane_production_artifact(FIXTURE, profile="formal")
    second = build_lane_production_artifact(FIXTURE, profile="formal")
    assert first == second


def test_writer_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    artifact = build_lane_production_artifact(FIXTURE, profile="formal")
    output = tmp_path / "directional-lanes.json"
    write_artifact_atomic(artifact, output)
    assert json.loads(output.read_text(encoding="utf-8"))["semantic_sha256"] == artifact[
        "semantic_sha256"
    ]
    with pytest.raises(FileExistsError):
        write_artifact_atomic(artifact, output)
