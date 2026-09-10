import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "calibrate_ota_general_traffic.py"
SPEC = importlib.util.spec_from_file_location("calibrate_ota_general_traffic", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_only_three_prespecified_time_blocks_exist():
    assert MODULE.time_block(7) == "morning_07_10"
    assert MODULE.time_block(15) == "daytime_10_16"
    assert MODULE.time_block(18) == "evening_16_19"
    with pytest.raises(ValueError):
        MODULE.time_block(19)


def test_calibration_source_allowlist_excludes_2024():
    assert MODULE.ALLOWED_CALIBRATION_YEARS == {"2021", "2023"}
    assert "keishicho_2024" not in MODULE.ALLOWED_CALIBRATION_SOURCES


def test_regularized_fit_uses_one_scale_per_block_and_bounds():
    targets = {(f"g{index}", hour): 100.0 for index in range(2) for hour in range(7, 19)}
    modeled = {key: 200.0 for key in targets}
    scales, trace = MODULE.fit_scales(modeled, targets)
    assert set(scales) == set(MODULE.BLOCKS)
    assert len(trace) == 3
    assert all(MODULE.SCALE_BOUNDS[0] <= value <= MODULE.SCALE_BOUNDS[1] for value in scales.values())
    assert all(0.4 < value < 0.7 for value in scales.values())


def test_route_crossing_is_counted_once_per_measurement_group(tmp_path):
    route = tmp_path / "routes.xml"
    route.write_text(
        '<routes><flow id="f" begin="25200" end="28800" number="12">'
        '<route edges="a b a c"/></flow></routes>', encoding="utf-8"
    )
    counts = MODULE.read_route_counts(route, {"g1": {"a", "b"}, "g2": {"z"}})
    assert counts == {("g1", 7): 12.0}


def test_netload_selected_edges_are_summed_once_per_group(tmp_path):
    netload = tmp_path / "netload.xml"
    netload.write_text(
        '<meandata><interval begin="25200" end="28800">'
        '<edge id="a" entered="10"/><edge id="b" entered="12"/>'
        '</interval></meandata>', encoding="utf-8"
    )
    counts = MODULE.read_netload_counts(netload, {"g1": {"a", "b"}, "g2": {"b"}})
    assert counts == {("g1", 7): 22.0, ("g2", 7): 12.0}


def test_relation_scaling_preserves_od_and_changes_only_counts(tmp_path):
    source = tmp_path / "source.xml"
    destination = tmp_path / "destination.xml"
    source.write_text(
        '<data><interval begin="25200" end="28800"><tazRelation from="a" to="b" count="10"/>'
        '</interval></data>', encoding="utf-8"
    )
    total = MODULE.write_calibrated_relations(
        source, destination,
        {"morning_07_10": 0.5, "daytime_10_16": 1.0, "evening_16_19": 1.0},
    )
    text = destination.read_text(encoding="utf-8")
    assert 'from="a"' in text and 'to="b"' in text
    assert 'count="5.000000"' in text
    assert total == 5


def test_independent_observation_is_rejected(tmp_path):
    groups = tmp_path / "groups.csv"
    groups.write_text("source,official_id,official_name,measurement_group_id\nKeishicho,,x,g\n", encoding="utf-8")
    observations = tmp_path / "observations.csv"
    observations.write_text(
        "source,survey_date,eligible,use_split,hour,site_name,four_wheel_count,motorcycle_count,census_id,count\n"
        "keishicho_2024,2024-09-01,true,validation,7,x,1,1,,\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="independent"):
        MODULE.read_targets(observations, groups)
