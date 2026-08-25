import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "prepare_tokyo_pt_small_zone_driving_od.py"
SPEC = importlib.util.spec_from_file_location("prepare_small_zone_driver_od", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_small_zone_parser_accepts_official_codes_and_rejects_aggregates():
    assert MODULE.parse_small_zone_token("00000_大田区_0055_01300:") == "01300"
    assert MODULE.parse_small_zone_token("0001_00100:") == "00100"
    assert MODULE.parse_small_zone_token("1680_合計") is None
    assert MODULE.parse_small_zone_token("1678_87000:圏域外合計") is None
    assert MODULE.parse_small_zone_token("00000_大田区(その他)") is None


def test_driver_od_keeps_only_three_nonoverlapping_directions(tmp_path):
    headers = "調査年,発ゾーン,着ゾーン,運転有無,トリップ数\n"
    files = {
        "ota_to_ota_small_zone_od.csv": [
            "平成３０年,a_01300:,b_01310:,1_運転した,10",
            "平成３０年,a_01300:,b_01310:,4_合計,20",
        ],
        "ota_to_all_small_zone_od.csv": [
            "平成３０年,a_01300:,b_00100:,1_運転した,30",
            "平成３０年,a_01300:,b_01310:,1_運転した,10",
            "平成３０年,a_01300:,1680_合計,1_運転した,999",
        ],
        "all_to_ota_small_zone_od.csv": [
            "平成３０年,a_00100:,b_01300:,1_運転した,40",
            "平成３０年,a_01310:,b_01300:,1_運転した,10",
        ],
    }
    for name, rows in files.items():
        (tmp_path / name).write_text(headers + "\n".join(rows) + "\n", encoding="cp932")
    totals, accounting = MODULE.read_driver_od(
        tmp_path, {"00100", "01300", "01310"}, {"01300", "01310"}
    )
    assert totals == {("00100", "01300"): 40.0, ("01300", "00100"): 30.0, ("01300", "01310"): 10.0}
    assert accounting["accepted_driver_trips"] == 80
    assert accounting["non_driver_rows_excluded"] == 1
    assert accounting["aggregate_unknown_or_other_rows_excluded"] == 1
    assert accounting["overlap_or_direction_rows_excluded"] == 2


def test_nearest_gateway_weights_are_normalized_and_observation_independent():
    candidates = [("far", MODULE.Point(10, 0)), ("near", MODULE.Point(1, 0)), ("mid", MODULE.Point(5, 0))]
    weights = MODULE.nearest_gateways(MODULE.Point(0, 0), candidates, count=2)
    assert set(weights) == {"near", "mid"}
    assert abs(sum(weights.values()) - 1.0) < 1e-12
    assert weights["near"] > weights["mid"]


def test_small_zone_uses_parent_basic_zone_for_hourly_profile():
    assert MODULE.parent_basic_zone("01300") == "0130"
    assert MODULE.parent_basic_zone("00103") == "0010"


def test_hourly_relations_use_simulation_relative_time_and_preserve_total(tmp_path):
    daily = {("01300", "00103"): 120.0}
    profiles = {"0130": {hour: 1 / 12 for hour in range(7, 19)}}
    hourly, fallback = MODULE.expand_hourly_od(daily, profiles)
    assert fallback == set()
    assert sum(hourly.values()) == 120.0

    output = tmp_path / "hourly.xml"
    MODULE.write_hourly_relations(output, hourly)
    root = MODULE.ET.parse(output).getroot()
    intervals = root.findall("interval")
    assert intervals[0].attrib == {
        "id": "passenger_07", "begin": "0", "end": "3600"
    }
    assert intervals[-1].attrib == {
        "id": "passenger_18", "begin": "39600", "end": "43200"
    }


def test_static_assignment_interval_contains_the_relative_clock(tmp_path):
    output = tmp_path / "assignment.xml"
    MODULE.write_assignment_relations(output, {("01300", "00103"): 10.0})
    interval = MODULE.ET.parse(output).getroot().find("interval")
    assert interval is not None
    assert interval.attrib == {"id": "passenger", "begin": "0", "end": "43200"}
