import importlib.util
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "diagnose_ota_external_through_prior.py"
SPEC = importlib.util.spec_from_file_location("diagnose_external_through", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_planning_basic_zone_parser_rejects_aggregate_unknown_and_other():
    assert MODULE.parse_basic_zone("001_0010:") == "0010"
    assert MODULE.parse_basic_zone("634_8700:圏域外合計") is None
    assert MODULE.parse_basic_zone("635_9999:不明") is None
    assert MODULE.parse_basic_zone("116_00--:東京区部（その他）") is None
    assert MODULE.parse_basic_zone("636_合計") is None


def test_candidate_reader_keeps_only_external_external_automobile_total(tmp_path):
    path = tmp_path / "od.csv"
    path.write_text(
        "調査年,発ゾーン,着ゾーン,目的種類,代表交通手段,トリップ数\n"
        "平成３０年,001_0010:,002_0011:,9_合計,3_自動車,10\n"
        "平成３０年,001_0010:,002_0011:,1_自宅－勤務,3_自動車,4\n"
        "平成３０年,001_0010:,002_0011:,9_合計,1_鉄道,5\n"
        "平成３０年,001_0010:,055_0130:,9_合計,3_自動車,6\n"
        "平成３０年,636_合計,002_0011:,9_合計,3_自動車,7\n",
        encoding="cp932",
    )
    totals, accounting = MODULE.read_external_automobile_person_od(
        path, {"0010", "0011", "0130"}, {"0130"}
    )
    assert totals == {("0010", "0011"): 10.0}
    assert accounting["accepted_person_trips"] == 10
    assert accounting["non_total_purpose_rows_excluded"] == 1
    assert accounting["non_automobile_rows_excluded"] == 1
    assert accounting["ota_endpoint_rows_excluded"] == 1
    assert accounting["non_official_zone_rows_excluded"] == 1


def test_geographic_candidate_requires_positive_ota_interior_overlap():
    ota = Polygon([(0, -1), (2, -1), (2, 1), (0, 1)])
    centroids = {
        "west": Point(-2, 0), "east": Point(4, 0),
        "northwest": Point(-2, 2), "northeast": Point(4, 2),
    }
    selected = MODULE.geographic_candidates(
        {("west", "east"): 10.0, ("northwest", "northeast"): 20.0}, centroids, ota
    )
    assert list(selected) == [("west", "east")]
    assert selected[("west", "east")]["person_trips"] == 10.0
    assert selected[("west", "east")]["ota_chord_length_m"] == 2.0


def test_route_population_reads_nested_route_distribution(tmp_path):
    path = tmp_path / "routes.xml"
    path.write_text(
        '<routes><flow fromTaz="EXT_KZ_0010" toTaz="EXT_KZ_1010">'
        '<routeDistribution><route edges="a b" probability="1"/>'
        '</routeDistribution></flow></routes>', encoding="utf-8"
    )
    assert MODULE.route_od_population(path) == {("0010", "1010")}
