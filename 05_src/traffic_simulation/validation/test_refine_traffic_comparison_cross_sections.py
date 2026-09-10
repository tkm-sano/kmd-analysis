import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "refine_traffic_comparison_cross_sections.py"
SPEC = importlib.util.spec_from_file_location("refine_traffic", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_series_index_keeps_prefecture_city_code_in_key():
    rows = [
        {"都道府県指定市コード": "13000", "交通量調査単位区間番号": "10", "上り・下りの別": "1"},
        {"都道府県指定市コード": "13100", "交通量調査単位区間番号": "10", "上り・下りの別": "1"},
    ]
    index = MODULE.index_raw_series(rows)
    assert len(index[("13000", "10", "1")]) == 1
    assert len(index[("13100", "10", "1")]) == 1


def test_series_evidence_preserves_noncurrent_flag_and_date():
    rows = [{
        "車種区分": "1", "令和３年度調査交通量観測・非観測の別": "2",
        "交通量観測年月日": "20191203", "時間帯別自動車類交通量（台／時）／７時台": "10",
    }]
    evidence = MODULE.series_evidence(rows)
    assert evidence["observation_flags"] == ["2"]
    assert evidence["survey_dates"] == ["20191203"]
    assert evidence["hours_with_any_value"] == 1


def test_geometry_index_records_section_geometry_not_point(tmp_path):
    tile = tmp_path / "tile.geojson"
    tile.write_text(
        '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"census":"s"},"geometry":{"type":"LineString","coordinates":[[139.0,35.0],[140.0,36.0]]}}]}',
        encoding="utf-8",
    )
    result = MODULE.load_geometry_index(tmp_path)["s"]
    assert result["bbox_wgs84"] == [139.0, 35.0, 140.0, 36.0]
    assert result["location_representation"] == "OFFICIAL_SECTION_GEOMETRY_NOT_POINT"
