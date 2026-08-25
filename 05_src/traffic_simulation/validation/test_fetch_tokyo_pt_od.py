import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "fetch_tokyo_pt_od.py"
SPEC = importlib.util.spec_from_file_location("fetch_tokyo_pt_od", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_acquisition_uses_only_public_official_https_sources():
    assert MODULE.SOURCES
    for url in MODULE.SOURCES.values():
        assert url.startswith("https://")
        assert "e-stat.go.jp" in url or "tokyo-pt.jp" in url
        assert "login" not in url and "form" not in url


def test_od_and_zone_geometry_are_both_acquired():
    names = set(MODULE.SOURCES)
    assert "tokyo_pt_2018_od_by_purpose_and_main_mode.csv" in names
    assert "tokyo_pt_2018_zone_geometry.zip" in names
