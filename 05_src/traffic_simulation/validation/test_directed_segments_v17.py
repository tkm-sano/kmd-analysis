from __future__ import annotations

import json
from copy import deepcopy

import pytest

from traffic_simulation.network.directed_segments_v17 import (
    DirectedSegmentError,
    build_directed_segment,
    build_production_artifact,
    generate_way_segments,
    map_turn_restriction,
    normalize_oneway,
    sha256_file,
    validate_directed_segment,
    write_artifact_atomic,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "directed_segments_phase4.osm.xml"
)


def _way(oneway: str = "no") -> dict[str, object]:
    return {
        "source_way_id": 1001,
        "source_node_ids": [10, 20, 30],
        "tags": {"highway": "residential", "oneway": oneway},
    }


@pytest.mark.parametrize(
    ("source", "canonical", "origin"),
    [("yes", "yes", "source_explicit"), ("1", "yes", "source_normalized"),
     ("no", "no", "source_explicit"), ("false", "no", "source_normalized"),
     ("-1", "-1", "source_explicit"), ("reverse", "-1", "source_normalized")],
)
def test_registered_explicit_oneway_normalization(
    source: str, canonical: str, origin: str
) -> None:
    result = normalize_oneway({"highway": "residential", "oneway": source})
    assert result["canonical_oneway"] == canonical
    assert result["value_origin"] == origin


def test_registered_absent_oneway_rules_are_deterministic() -> None:
    assert normalize_oneway({"highway": "residential"})["canonical_oneway"] == "no"
    assert normalize_oneway({"highway": "motorway"})["canonical_oneway"] == "yes"
    assert normalize_oneway(
        {"highway": "residential", "junction": "roundabout"}
    )["rule_id"] == "OSM_IMPLICIT_ROUNDABOUT_ONEWAY_YES"


@pytest.mark.parametrize(
    ("value", "stop_code"),
    [("yes;no", "ONEWAY_VALUE_INVALID"), ("reversible", "ONEWAY_VALUE_UNSUPPORTED")],
)
def test_invalid_or_unsupported_oneway_stops(value: str, stop_code: str) -> None:
    with pytest.raises(DirectedSegmentError) as caught:
        normalize_oneway({"highway": "residential", "oneway": value})
    assert caught.value.stop_code == stop_code


def test_unregistered_absent_oneway_rule_stops() -> None:
    with pytest.raises(DirectedSegmentError) as caught:
        normalize_oneway({"highway": "motorway_link"})
    assert caught.value.stop_code == "ONEWAY_RULE_NOT_REGISTERED"


def test_reverse_oneway_is_backward_only_and_source_is_immutable() -> None:
    way = _way("-1")
    before = deepcopy(way)
    segments = generate_way_segments(way)
    assert way == before
    assert [item["source_direction"] for item in segments] == ["backward"]
    assert segments[0]["directed_segment_id"] == "ds:1001:0:2:backward"
    assert segments[0]["source_node_ids"] == [10, 20, 30]
    assert segments[0]["travel_node_ids"] == [30, 20, 10]


def test_split_intervals_have_stable_direction_symmetric_ids() -> None:
    first = generate_way_segments(_way(), split_indices={1})
    second = generate_way_segments(_way(), split_indices={1})
    assert first == second
    assert [item["directed_segment_id"] for item in first] == [
        "ds:1001:0:1:forward",
        "ds:1001:0:1:backward",
        "ds:1001:1:2:forward",
        "ds:1001:1:2:backward",
    ]
    assert first[0]["source_node_ids"] == first[1]["source_node_ids"]
    assert first[0]["travel_node_ids"] == list(reversed(first[1]["travel_node_ids"]))


def test_lineage_validator_rejects_id_interval_disagreement() -> None:
    segment = build_directed_segment(
        source_way_id=1001,
        source_start_index=0,
        source_end_index=2,
        source_way_node_ids=[10, 20, 30],
        source_direction="forward",
        derivation_rule_id="TEST",
    )
    segment["directed_segment_id"] = "ds:1001:0:1:forward"
    with pytest.raises(DirectedSegmentError) as caught:
        validate_directed_segment(segment, source_way_node_ids=[10, 20, 30])
    assert caught.value.stop_code == "DIRECTED_SEGMENT_LINEAGE_INVALID"


def test_node_via_mapping_requires_one_exact_candidate() -> None:
    artifact = build_production_artifact(FIXTURE)
    mapping = next(item for item in artifact["relation_mappings"] if item["relation_id"] == 2001)
    assert mapping["from_directed_segment_id"] == "ds:1002:0:1:forward"
    assert mapping["to_directed_segment_id"] == "ds:1003:0:1:forward"
    assert mapping["mapping_method"] == "exact_source_node_lineage"


def test_way_via_mapping_uses_ordered_exact_lineage() -> None:
    artifact = build_production_artifact(FIXTURE)
    mapping = next(item for item in artifact["relation_mappings"] if item["relation_id"] == 2002)
    assert mapping["via"][0]["directed_segment_ids"] == ["ds:1001:1:2:forward"]


def test_relation_missing_and_ambiguous_candidates_stop() -> None:
    ways = {
        1: {"source_node_ids": [1, 2]},
        2: {"source_node_ids": [2, 3]},
    }
    relation = {
        "relation_id": 9,
        "members": [
            {"type": "way", "ref": 1, "role": "from"},
            {"type": "node", "ref": 2, "role": "via"},
            {"type": "way", "ref": 2, "role": "to"},
        ],
        "tags": {"type": "restriction", "restriction": "no_left_turn"},
    }
    with pytest.raises(DirectedSegmentError) as missing:
        map_turn_restriction(relation, ways=ways, segments=[])
    assert missing.value.stop_code == "RELATION_DIRECTED_MAPPING_MISSING"

    forward = build_directed_segment(
        source_way_id=1, source_start_index=0, source_end_index=1,
        source_way_node_ids=[1, 2], source_direction="forward", derivation_rule_id="TEST"
    )
    duplicate = dict(forward, directed_segment_id="ds:1:0:1:forward")
    with pytest.raises(DirectedSegmentError) as ambiguous:
        map_turn_restriction(relation, ways=ways, segments=[forward, duplicate])
    assert ambiguous.value.stop_code == "RELATION_DIRECTED_MAPPING_AMBIGUOUS"


def test_production_fixture_is_deterministic_and_source_bytes_are_immutable() -> None:
    before = sha256_file(FIXTURE)
    first = build_production_artifact(FIXTURE)
    second = build_production_artifact(FIXTURE)
    assert sha256_file(FIXTURE) == before
    assert first == second
    assert first["source_way_mutated"] is False
    assert first["blockers"] == []
    assert first["counts"] == {
        "source_ways": 5,
        "directed_segments": 8,
        "restriction_relations": 2,
        "mapped_relations": 2,
        "blockers": 0,
    }


def test_production_writer_is_atomic_and_refuses_overwrite(tmp_path) -> None:
    artifact = build_production_artifact(FIXTURE)
    output = tmp_path / "directed-segments.json"
    write_artifact_atomic(artifact, output)
    assert json.loads(output.read_text(encoding="utf-8"))["semantic_sha256"] == artifact[
        "semantic_sha256"
    ]
    with pytest.raises(FileExistsError):
        write_artifact_atomic(artifact, output)
