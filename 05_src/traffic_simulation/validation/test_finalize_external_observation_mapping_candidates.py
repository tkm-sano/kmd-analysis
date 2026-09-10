import json

import pytest

from traffic_simulation.calibration.finalize_external_observation_mapping_candidates import (
    DEFAULT_DATA_DIR,
    build_review,
)


@pytest.fixture(scope="module")
def review():
    return build_review(DEFAULT_DATA_DIR)


def test_external_mapping_candidate_review_counts(review) -> None:
    rows, _, summary = review

    assert len(rows) == 10
    assert len({row["observation_section_id"] for row in rows}) == 6
    assert summary["classification_counts"] == {
        "AUTO_ACCEPT": 8,
        "REVIEW_REQUIRED": 1,
        "NETWORK_EXTENSION_REQUIRED": 1,
        "UNRESOLVED": 0,
    }
    assert all(row["connection_violation_count"] == 0 for row in rows)
    assert all(row["mapping_threshold_changed"] is False for row in rows)
    assert all(row["existing_mapping_changed"] is False for row in rows)


def test_medium_route_relation_and_haneda_mainline_evidence(review) -> None:
    rows, evidence, summary = review
    by_observation = {row["observation_section_id"]: row for row in rows}

    haneda = by_observation["13200100070"]
    assert haneda["classification"] == "REVIEW_REQUIRED"
    alternatives = json.loads(haneda["candidate_directed_corridors_json"])
    assert len(alternatives) == 2
    assert {row["osm_name"] for row in evidence if row["edge_id"] in {
        edge for alternative in alternatives for edge in alternative["edge_ids"]
    }} == {"首都高速1号羽田線"}

    route_316 = by_observation["13403160320"]
    assert route_316["classification"] == "AUTO_ACCEPT"
    assert route_316["candidate_corridor_coverage_ratio"] == 0.580542
    assert route_316["connection_violation_count"] == 0
    selected_evidence = [
        row for row in evidence if row["edge_id"] in route_316["candidate_edge_ids"].split(";")
    ]
    relations = [
        relation
        for row in selected_evidence
        for relation in json.loads(row["route_relations_json"])
    ]
    assert any(
        relation["network"] == "JP:prefectural:tokyo"
        and relation["ref"] == "316"
        and relation["name"] == "日本橋芝浦大森線"
        for relation in relations
    )


def test_network_extension_is_spatial_not_threshold_relaxation(review) -> None:
    rows, _, summary = review
    row = next(item for item in rows if item["observation_section_id"] == "13300010260")
    extension = summary["network_extension"]

    assert row["classification"] == "NETWORK_EXTENSION_REQUIRED"
    assert row["network_spatial_coverage_ratio"] == 0.245414
    assert extension["uncovered_length_m"] == 776.834
    assert extension["minimum_25m_search_bbox_wgs84"] == {
        "west": 139.717263428,
        "south": 35.617146755,
        "east": 139.720295799,
        "north": 35.62182519,
    }
    assert summary["guardrails"]["matching_threshold_changed"] is False
