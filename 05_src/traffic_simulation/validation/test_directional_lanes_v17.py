from __future__ import annotations

import json
from pathlib import Path

import pytest

from traffic_simulation.network.directional_lanes_v17 import (
    ASSUMPTION_ID,
    DirectionalLaneError,
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


@pytest.mark.parametrize("lanes", ["4", "3", "1"])
def test_formal_total_only_bidirectional_stops(lanes: str) -> None:
    with pytest.raises(DirectionalLaneError) as caught:
        resolve_directional_lanes(
            {"highway": "residential", "oneway": "no", "lanes": lanes},
            profile="formal",
        )
    assert caught.value.stop_code == "LANE_DIRECTIONAL_ALLOCATION_MISSING"


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
