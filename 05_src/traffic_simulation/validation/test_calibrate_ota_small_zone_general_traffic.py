import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "calibrate_ota_small_zone_general_traffic.py"
SPEC = importlib.util.spec_from_file_location("calibrate_small_zone", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_relative_simulation_clock_maps_zero_to_source_hour_seven():
    assert MODULE.source_hour(0) == 7
    assert MODULE.source_hour(3599) == 7
    assert MODULE.source_hour(39600) == 18


def test_relative_netload_is_mapped_to_source_hours(tmp_path):
    path = tmp_path / "netload.xml"
    path.write_text(
        '<meandata><interval begin="0" end="3600"><edge id="e" entered="3"/>'
        '</interval><interval begin="39600" end="43200"><edge id="e" entered="5"/>'
        '</interval></meandata>', encoding="utf-8"
    )
    assert MODULE.read_relative_netload(path, {"g": {"e"}}) == {
        ("g", 7): 3.0, ("g", 18): 5.0
    }


def test_global_fit_is_single_bounded_parameter():
    targets = {("g", hour): 100.0 for hour in range(7, 19)}
    modeled = {key: 200.0 for key in targets}
    scale, trace = MODULE.fit_global(modeled, targets)
    assert MODULE.SCALE_BOUNDS[0] <= scale <= MODULE.SCALE_BOUNDS[1]
    assert scale < 0.7
    assert trace["success"] is True


def test_static_route_shares_are_applied_to_each_hour(tmp_path):
    relations = tmp_path / "relations.xml"
    relations.write_text(
        '<data><interval begin="0" end="3600"><tazRelation from="a" to="b" count="10"/>'
        '</interval><interval begin="3600" end="7200"><tazRelation from="a" to="b" count="20"/>'
        '</interval></data>', encoding="utf-8"
    )
    routes = tmp_path / "routes.xml"
    routes.write_text(
        '<routes><flow fromTaz="a" toTaz="b"><routeDistribution>'
        '<route probability="3" edges="x e"/><route probability="1" edges="y"/>'
        '</routeDistribution></flow></routes>', encoding="utf-8"
    )
    counts, accounting = MODULE.read_assigned_route_counts(routes, relations, {"g": {"e"}})
    assert counts == {("g", 7): 7.5, ("g", 8): 15.0}
    assert accounting["hourly_relations_without_assigned_route"] == 0


def test_2024_is_still_excluded_by_imported_target_reader():
    assert MODULE.base.ALLOWED_CALIBRATION_YEARS == {"2021", "2023"}
