from __future__ import annotations

from traffic_simulation.calibration.normalize_road_census_section_attributes import (
    canonical_route_key,
    normalize_section,
    parse_section_id,
)


def _raw(**overrides: str) -> dict[str, str]:
    row = {
        "交通調査基本区間番号": "13300010010",
        "道路種別": "3",
        "路線番号": "1",
        "路線名": "一般国道１号",
        "管理区分": "1",
        "市区町村コード": "13111",
        "起点側／接続区分": "1",
        "起点側／交通調査基本区間番号": "13300010000",
        "終点側／接続区分": "2",
        "終点側／交通調査基本区間番号": "13300010020",
        "区間種別": "0",
        "分離区間／分離区分": "0",
        "一方通行フラグ": "0",
        "車線数": "4",
        "交通量／調査単位区間番号": "10010",
    }
    row.update(overrides)
    return row


def test_section_id_official_components_are_validated() -> None:
    assert parse_section_id("13300010010") == {
        "prefecture_code": "13",
        "road_type_code": "3",
        "route_number_code4": "0001",
        "sequence_number_code4": "0010",
    }


def test_canonical_route_key_keeps_road_system_namespace() -> None:
    national = canonical_route_key("NATIONAL_HIGHWAY", "JP_NATIONAL_HIGHWAY", "MLIT", "1")
    urban = canonical_route_key("URBAN_EXPRESSWAY", "JP_URBAN_EXPRESSWAY", "SHUTO_EXPRESSWAY", "1")
    assert national != urban


def test_oneway_code_two_is_terminus_to_origin_without_geometry_inference() -> None:
    issues: list[dict[str, str]] = []
    row = normalize_section(
        _raw(**{"一方通行フラグ": "2"}), {"1", "2"}, issues
    )
    assert row["oneway"] == "ONEWAY_TERMINUS_TO_ORIGIN"
    assert row["permitted_census_direction"] == "UP"
    assert row["lane_direction_scope"] == "PERMITTED_ONEWAY_DIRECTION_TOTAL"
    assert row["geojson_digitization_direction_used"] is False
    assert row["geojson_digitization_direction_status"] == "UNVERIFIED"


def test_missing_lane_value_stays_blank_and_is_unresolved() -> None:
    issues: list[dict[str, str]] = []
    row = normalize_section(_raw(**{"車線数": ""}), {"1", "2"}, issues)
    assert row["lane_count_raw"] == ""
    assert row["lane_count"] == ""
    assert row["normalization_status"] == "UNRESOLVED"
    assert any(issue["category"] == "MISSING" and issue["field"] == "lane_count" for issue in issues)


def test_conflicting_official_route_components_do_not_emit_canonical_key() -> None:
    issues: list[dict[str, str]] = []
    row = normalize_section(
        _raw(**{"交通調査基本区間番号": "13301100010", "路線番号": "10"}),
        {"1", "2"},
        issues,
    )
    assert row["route_number_raw"] == "10"
    assert row["canonical_route_key"] == ""
    assert row["canonical_route_key_status"] == "UNRESOLVED"
    assert row["normalization_status"] == "UNRESOLVED"
