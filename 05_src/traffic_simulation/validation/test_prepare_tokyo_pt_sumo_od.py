import importlib.util
from pathlib import Path

from shapely.geometry import Point, box


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "prepare_tokyo_pt_sumo_od.py"
SPEC = importlib.util.spec_from_file_location("prepare_tokyo_pt_sumo_od", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_zone_tokens_are_normalized_without_accepting_aggregate_labels():
    assert MODULE.normalize_zone(130) == "0130"
    assert MODULE.normalize_zone(":0138 ") == "0138"
    assert MODULE.normalize_zone(":8888 全計") == "8888"


def test_departure_profile_is_normalized_and_has_fixed_hours():
    profile = MODULE.safe_profile({7: 2, 8: 3})
    assert set(profile) == set(MODULE.HOURS)
    assert abs(sum(profile.values()) - 1.0) < 1e-12
    assert profile[7] == 0.4


def test_external_od_is_aggregated_by_fixed_sector_and_nontraversing_is_excluded():
    ota = box(-1, -1, 1, 1)
    centers = {"0130": Point(0, 0), "1000": Point(-3, 0), "2000": Point(3, 0), "3000": Point(3, 3)}
    assert MODULE.map_relation("0130", "2000", centers, ota) == ("PT_0130", "EXT_E")
    assert MODULE.map_relation("1000", "2000", centers, ota) == ("EXT_W", "EXT_E")
    assert MODULE.map_relation("2000", "3000", centers, ota) is None


def test_sixteen_sector_mapping_preserves_finer_external_bearing():
    center = Point(0, 0)
    assert MODULE.sector_for_point(Point(10, 1), center, MODULE.SECTORS_16) == "E"
    assert MODULE.sector_for_point(Point(10, 5), center, MODULE.SECTORS_16) == "ENE"
    assert MODULE.sector_for_point(Point(5, 10), center, MODULE.SECTORS_16) == "NNE"


def test_boundary_gateway_has_no_duplicate_edge_within_a_role(monkeypatch):
    monkeypatch.setattr(MODULE, "MIN_INWARD_PROGRESS_M", 0.05)
    edges = {
        "enter": {
            "id": "enter", "length": 20.0, "priority": 10,
            "shape": MODULE.LineString([(-0.1, 0), (0.5, 0)]),
        },
        "leave": {
            "id": "leave", "length": 20.0, "priority": 10,
            "shape": MODULE.LineString([(0.5, 0), (-0.1, 0)]),
        },
    }
    gateways = MODULE.boundary_gateways(edges, {}, box(-0.1, -1, 1, 1))
    all_sources = [edge for record in gateways.values() for edge in record["sources"]]
    all_sinks = [edge for record in gateways.values() for edge in record["sinks"]]
    assert all_sources == ["enter"]
    assert all_sinks == ["leave"]


def test_official_polygon_parts_are_merged_back_to_one_research_taz(tmp_path):
    path = tmp_path / "parts.xml"
    path.write_text(
        '<tazs><taz id="PT_0130__part0" edges="a b"/>'
        '<taz id="PT_0130__part1" edges="b c"/></tazs>', encoding="utf-8"
    )
    assert MODULE.read_internal_taz(path) == {"PT_0130": {"a": 1.0, "b": 1.0, "c": 1.0}}


def test_official_taz_weights_are_preserved_when_polygon_parts_are_merged(tmp_path):
    path = tmp_path / "weighted.xml"
    path.write_text(
        '<tazs><taz id="PT_0130__part0"><tazSource id="a" weight="2.5"/></taz>'
        '<taz id="PT_0130__part1"><tazSource id="a" weight="3.5"/>'
        '<tazSource id="b" weight="4"/></taz></tazs>', encoding="utf-8"
    )
    assert MODULE.read_internal_taz(path) == {"PT_0130": {"a": 3.5, "b": 4.0}}
