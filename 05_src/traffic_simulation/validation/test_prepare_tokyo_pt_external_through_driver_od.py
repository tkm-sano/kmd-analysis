import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "prepare_tokyo_pt_external_through_driver_od.py"
SPEC = importlib.util.spec_from_file_location("prepare_external_through_driver_od", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_basic_zone_parser_accepts_official_codes_and_rejects_nonspatial_categories():
    assert MODULE.parse_basic_zone_token("001_0010:") == "0010"
    assert MODULE.parse_basic_zone_token("634_8700:圏域外合計") is None
    assert MODULE.parse_basic_zone_token("635_9999:不明") is None
    assert MODULE.parse_basic_zone_token("116_00--:東京区部（その他）") is None
    assert MODULE.parse_basic_zone_token("636_合計") is None


def test_exact_pair_filter_keeps_only_explicit_positive_driver_rows(tmp_path):
    raw = tmp_path / "official.csv"
    raw.write_text(
        "調査年,発ゾーン,着ゾーン,運転有無,トリップ数\n"
        "平成３０年,001_0010:,002_0020:,1_運転した,12\n"
        "平成３０年,001_0010:,002_0020:,2_運転しなかった,7\n"
        "平成３０年,001_0010:,003_0030:,4_合計,9\n"
        "平成３０年,001_0010:,004_0040:,1_運転した,99\n"
        "平成３０年,001_0010:,634_8700:圏域外合計,1_運転した,999\n",
        encoding="cp932",
    )
    candidates = {("0010", "0020"), ("0010", "0030"), ("0020", "0010")}
    totals, reconciliation, accounting = MODULE.read_exact_candidate_driver_od(
        raw, candidates, {"0010", "0020", "0030", "0040"}, set()
    )
    assert totals == {("0010", "0020"): 12.0}
    status = {(row["origin_zone"], row["destination_zone"]): row["match_status"] for row in reconciliation}
    assert status == {
        ("0010", "0020"): "explicit_positive_driver",
        ("0010", "0030"): "driver_row_absent_other_status_present",
        ("0020", "0010"): "pair_absent_from_sparse_export",
    }
    assert accounting["accepted_driver_trips"] == 12
    assert accounting["accepted_exact_pairs"] == 1
    assert accounting["candidate_pairs"] == 3


def test_external_external_candidates_reject_ota_endpoints():
    try:
        MODULE.validate_candidate_population({("0130", "0020")}, {"0130"})
    except ValueError as error:
        assert "Ota endpoint" in str(error)
    else:
        raise AssertionError("Ota endpoint candidate must fail closed")


def test_merge_relations_preserves_existing_and_uses_distinct_basic_zone_ids():
    existing = {("PT_SZ_01300", "PT_SZ_00103"): 10.0}
    through = {("0010", "0020"): 20.0}
    combined = MODULE.merge_daily_relations(existing, through)
    assert combined == {
        ("EXT_KZ_0010", "EXT_KZ_0020"): 20.0,
        ("PT_SZ_01300", "PT_SZ_00103"): 10.0,
    }
    assert sum(combined.values()) == 30.0


def test_candidate_file_counts_are_never_used_as_vehicle_demand(tmp_path):
    candidates = tmp_path / "candidates.csv"
    candidates.write_text(
        "origin_zone,destination_zone,automobile_person_trips\n0010,0020,999999\n",
        encoding="utf-8",
    )
    assert MODULE.read_candidate_pairs(candidates) == {("0010", "0020")}


def test_basic_zone_hourly_expansion_preserves_daily_total():
    daily = {("0010", "0020"): 120.0}
    profiles = {"0010": {hour: 1 / 12 for hour in range(7, 19)}}
    hourly, fallback = MODULE.expand_basic_hourly_od(daily, profiles)
    assert fallback == set()
    assert sum(hourly.values()) == 120.0
