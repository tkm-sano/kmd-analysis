from __future__ import annotations

from collections import Counter

import pytest
from shapely.geometry import LineString, MultiLineString

from traffic_simulation.calibration.finalize_road_census_sumo_mapping import (
    MANUAL_DECISIONS,
    MANUAL_SECTION_IDS,
)
from traffic_simulation.calibration.road_census_sumo_pipeline import (
    MatchThresholds,
    angle_difference_deg,
    confidence_for_candidate,
    geometry_bearing_deg,
    lane_completion,
    map_hourly_counts_to_edges,
    match_sections_to_corridors,
    match_sections_to_edges,
    normalize_hourly_traffic,
    normalize_road_name,
    normalize_route_ref,
    normalize_sections,
)


def thresholds() -> MatchThresholds:
    return MatchThresholds(
        candidate_buffer_m=5.0,
        high_overlap_ratio=0.7,
        medium_overlap_ratio=0.4,
        high_section_coverage_ratio=0.6,
        medium_section_coverage_ratio=0.3,
        max_high_angle_difference_deg=25.0,
        max_medium_angle_difference_deg=45.0,
        route_ref_required_for_high=True,
        name_match_can_support_medium=True,
    )


def config() -> dict:
    return {
        "lane_completion": {
            "minimum_confidence_for_census_fallback": "medium",
            "allow_symmetric_even_total_split": True,
        },
        "traffic_assignment": {"minimum_confidence": "medium"},
    }


def section_row(**overrides: str) -> dict[str, str]:
    row = {
        "交通調査基本区間番号": "S1",
        "世代管理番号（十の位）": "0",
        "世代管理番号（一の位）": "1",
        "道路種別": "3",
        "路線番号": "15",
        "路線名": "一般国道15号",
        "市区町村コード": "13111",
        "区間延長（ｋｍ）": "0.2",
        "一方通行フラグ": "0",
        "交通量／都道府県指定市コード": "13",
        "交通量／調査単位区間番号": "T1",
        "上り／観測地点交通調査基本区間番号": "S1",
        "下り／観測地点交通調査基本区間番号": "S1D",
        "上り／令和３年度調査交通量観測・非観測の別": "1",
        "下り／令和３年度調査交通量観測・非観測の別": "2",
        "幅員構成／道路部幅員（ｍ）": "10.0",
        "幅員構成／車道部幅員（ｍ）": "8.0",
        "幅員構成／車道幅員（ｍ）": "3.5",
        "幅員構成／中央帯幅員（ｍ）": "0.0",
        "車線数": "4",
    }
    row.update(overrides)
    return row


def test_normalizes_sections_and_hourly_traffic_by_direction_target() -> None:
    sections = normalize_sections([section_row()])
    hourly = normalize_hourly_traffic(
        [
            {
                "交通量調査単位区間番号": "T1",
                "上り・下りの別": "1",
                "車種区分": "1",
                "時間帯別自動車類交通量（台／時）／７時台": "10",
                "交通量観測年月日": "20211001",
                "天候": "1",
            },
            {
                "交通量調査単位区間番号": "T1",
                "上り・下りの別": "1",
                "車種区分": "2",
                "時間帯別自動車類交通量（台／時）／７時台": "3",
                "交通量観測年月日": "20211001",
                "天候": "1",
            },
        ],
        [section_row()],
    )

    assert sections[0]["total_lanes"] == 4
    seven = next(row for row in hourly if row["hour"] == 7)
    assert seven["census_section_id"] == "S1"
    assert seven["direction"] == "up"
    assert seven["small_vehicle_count"] == 10
    assert seven["large_vehicle_count"] == 3
    assert seven["total_vehicle_count"] == 13
    assert seven["observation_flag"] == "1"


def test_identity_and_direction_helpers_normalize_japanese_road_labels() -> None:
    assert normalize_route_ref(" 国道15号 / R1 ") == {"15", "R1"}
    assert normalize_road_name("一般国道 １５号線") == "15"
    assert angle_difference_deg(90, 270) == 0
    assert geometry_bearing_deg(MultiLineString([[(0, 0), (5, 0)], [(5, 0), (20, 0)]])) == pytest.approx(90)


def test_confidence_requires_spatial_direction_and_identity_support() -> None:
    high = confidence_for_candidate(0.9, 0.8, 5, "match", "unknown", thresholds())
    low = confidence_for_candidate(0.9, 0.8, 5, "mismatch", "match", thresholds())
    assert high == ("high", False, "spatial_direction_route_rule")
    assert low == ("low", True, "route_mismatch")


def test_matching_allows_one_census_section_to_multiple_sumo_edges() -> None:
    sections = normalize_sections([section_row()])
    edges = [
        {
            "sumo_edge_id": "e1",
            "from_node": "n0",
            "to_node": "n1",
            "geometry": LineString([(0, 0), (10, 0)]),
            "ref": "15",
            "name": "国道15号",
            "bearing_deg": 90.0,
        },
        {
            "sumo_edge_id": "e2",
            "from_node": "n1",
            "to_node": "n2",
            "geometry": LineString([(10, 0), (20, 0)]),
            "ref": "15",
            "name": "国道15号",
            "bearing_deg": 90.0,
        },
    ]

    mapping, missing = match_sections_to_edges(
        sections,
        {"S1": LineString([(0, 0), (20, 0)])},
        edges,
        thresholds(),
    )

    assert missing == []
    assert {row["sumo_edge_id"] for row in mapping} == {"e1", "e2"}
    assert {row["confidence"] for row in mapping} == {"high"}
    assert not any(row["manual_review_required"] for row in mapping)


def test_single_edge_coverage_is_diagnostic_and_corridor_coverage_drives_confidence() -> None:
    sections = normalize_sections([section_row()])
    edges = []
    for index in range(5):
        edges.append(
            {
                "sumo_edge_id": f"e{index + 1}",
                "from_node": f"n{index}",
                "to_node": f"n{index + 1}",
                "geometry": LineString([(index * 20, 0), ((index + 1) * 20, 0)]),
                "edge_length_m": 20.0,
                "ref": "15",
                "name": "国道15号",
                "bearing_deg": 90.0,
            }
        )

    mapping, _, corridors, membership, comparison = match_sections_to_corridors(
        sections, {"S1": LineString([(0, 0), (120, 0)])}, edges, thresholds()
    )

    assert all(row["single_edge_coverage_ratio"] < 0.3 for row in membership)
    selected = next(row for row in corridors if row["selected"])
    assert selected["edge_count"] == 5
    assert selected["corridor_coverage_ratio"] >= 0.6
    assert selected["confidence"] == "high"
    assert {row["sumo_edge_id"] for row in mapping} == {"e1", "e2", "e3", "e4", "e5"}
    assert comparison[0]["old_best_confidence"] == "low"
    assert comparison[0]["new_best_confidence"] == "high"


def test_geometrically_adjacent_edges_are_not_joined_without_sumo_topology() -> None:
    sections = normalize_sections([section_row()])
    edges = [
        {
            "sumo_edge_id": "e1", "from_node": "a", "to_node": "b",
            "geometry": LineString([(0, 0), (20, 0)]), "edge_length_m": 20.0,
            "ref": "15", "name": "国道15号", "bearing_deg": 90.0,
        },
        {
            "sumo_edge_id": "e2", "from_node": "x", "to_node": "y",
            "geometry": LineString([(20, 0), (40, 0)]), "edge_length_m": 20.0,
            "ref": "15", "name": "国道15号", "bearing_deg": 90.0,
        },
    ]

    _, _, corridors, _, _ = match_sections_to_corridors(
        sections, {"S1": LineString([(0, 0), (120, 0)])}, edges, thresholds()
    )

    assert all(row["edge_count"] == 1 for row in corridors)
    assert next(row for row in corridors if row["selected"])["confidence"] == "low"


def test_manual_review_register_is_complete_and_keeps_weak_mapping_excluded() -> None:
    assert set(MANUAL_DECISIONS) == MANUAL_SECTION_IDS
    assert len(MANUAL_DECISIONS) == 25
    assert Counter(row["review_decision"] for row in MANUAL_DECISIONS.values()) == {
        "MANUAL_CONFIRMED": 25,
    }
    recovered = MANUAL_DECISIONS["13403110020"]
    assert recovered["corridor_id"] == "13403110020_C0003"
    assert recovered["final_confidence"] == "high"
    assert recovered["review_reason_code"] == "ROUTE_MISMATCH_RESOLVED"
    weak_but_located = MANUAL_DECISIONS["13200510020"]
    assert weak_but_located["review_decision"] == "MANUAL_CONFIRMED"
    assert weak_but_located["final_confidence"] == "low"


def test_matching_marks_route_mismatch_as_manual_low_confidence() -> None:
    sections = normalize_sections([section_row()])
    edges = [
        {
            "sumo_edge_id": "e1",
            "geometry": LineString([(0, 0), (20, 0)]),
            "ref": "1",
            "name": "国道15号",
            "bearing_deg": 90.0,
        }
    ]

    mapping, _ = match_sections_to_edges(sections, {"S1": LineString([(0, 0), (20, 0)])}, edges, thresholds())

    assert mapping[0]["confidence"] == "low"
    assert mapping[0]["manual_review_required"] is True
    assert mapping[0]["match_method"] == "route_mismatch"


def test_lane_completion_preserves_osm_and_keeps_conflicts_or_odd_totals_unresolved() -> None:
    sections = normalize_sections(
        [
            section_row(交通調査基本区間番号="S1", 車線数="4"),
            section_row(交通調査基本区間番号="S2", 車線数="3"),
            section_row(交通調査基本区間番号="S3", 車線数="6"),
        ]
    )
    edge_attrs = [
        {"sumo_edge_id": "osm", "lanes": 2},
        {"sumo_edge_id": "odd", "lanes": None},
        {"sumo_edge_id": "even", "lanes": None},
    ]
    mapping = [
        {"census_section_id": "S1", "sumo_edge_id": "osm", "confidence": "high", "manual_review_required": False},
        {"census_section_id": "S2", "sumo_edge_id": "odd", "confidence": "high", "manual_review_required": False},
        {"census_section_id": "S3", "sumo_edge_id": "even", "confidence": "medium", "manual_review_required": False},
    ]

    rows = {row["sumo_edge_id"]: row for row in lane_completion(sections, edge_attrs, mapping, config())}

    assert rows["osm"]["completion_status"] == "conflict"
    assert rows["osm"]["completed_lane_count"] == 2
    assert rows["odd"]["completion_status"] == "unresolved"
    assert rows["even"]["completion_status"] == "derived_symmetric_split"
    assert rows["even"]["completed_lane_count"] == 3
    assert "road_census_observed_total_lanes" in rows["even"]["provenance"]


def test_hourly_counts_repeat_on_each_matched_edge_without_splitting() -> None:
    hourly = [
        {
            "census_section_id": "S1",
            "direction": "up",
            "begin": "07:00:00",
            "end": "08:00:00",
            "small_vehicle_count": 40,
            "large_vehicle_count": 10,
            "total_vehicle_count": 50,
            "observation_flag": "1",
        }
    ]
    mapping = [
        {"census_section_id": "S1", "sumo_edge_id": "e1", "confidence": "high", "manual_review_required": False},
        {"census_section_id": "S1", "sumo_edge_id": "e2", "confidence": "high", "manual_review_required": False},
        {"census_section_id": "S1", "sumo_edge_id": "low", "confidence": "low", "manual_review_required": True},
    ]

    rows = map_hourly_counts_to_edges(hourly, mapping, config())
    totals = [row for row in rows if row["vehicle_class"] == "total"]

    assert {row["sumo_edge_id"] for row in totals} == {"e1", "e2"}
    assert [row["observed_count"] for row in totals] == [50, 50]
    assert all("series_repeated_not_split" in row["mapping_source"] for row in totals)
