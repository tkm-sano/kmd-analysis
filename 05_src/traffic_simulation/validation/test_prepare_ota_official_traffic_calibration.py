import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "prepare_ota_official_traffic_calibration.py"
SPEC = importlib.util.spec_from_file_location("prepare_ota_official_traffic_calibration", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_normalize_handles_width_and_official_road_notation():
    assert MODULE.normalize("一般国道１５号") == MODULE.normalize("15")
    assert MODULE.normalize("東矢口２") == MODULE.normalize("東矢口2")


def test_road_identity_uses_approved_aliases_not_substring_guessing():
    assert MODULE.road_identity({"ref": "15", "name": "第一京浜"}, "第一京浜")
    assert not MODULE.road_identity({"ref": "15", "name": "第一京浜"}, "第二京浜")


def test_unknown_road_name_does_not_become_a_match():
    assert not MODULE.road_identity({"ref": "311", "name": "環八通り"}, "未定義道路")
