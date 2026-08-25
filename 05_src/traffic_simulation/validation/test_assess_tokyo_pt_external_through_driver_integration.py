import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "assess_tokyo_pt_external_through_driver_integration.py"
SPEC = importlib.util.spec_from_file_location("assess_external_through_driver", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_route_population_recognizes_direct_and_distributed_routes(tmp_path):
    route = tmp_path / "routes.xml"
    route.write_text(
        "<routes>"
        '<flow fromTaz="PT_SZ_1" toTaz="PT_SZ_2"><route edges="a b"/></flow>'
        '<flow fromTaz="EXT_KZ_1" toTaz="EXT_KZ_2"><routeDistribution>'
        '<route probability="2" edges="b c"/></routeDistribution></flow>'
        '<flow fromTaz="X" toTaz="Y"><route edges=""/></flow>'
        "</routes>",
        encoding="utf-8",
    )
    assert MODULE.route_population(route) == {
        ("PT_SZ_1", "PT_SZ_2"), ("EXT_KZ_1", "EXT_KZ_2")
    }


def test_measurement_group_support_uses_edges_not_observation_values(tmp_path):
    groups = tmp_path / "groups.csv"
    groups.write_text(
        "measurement_group_id,official_name,selected_edge_ids\n"
        "G1,one,a;b\nG2,two,c\n",
        encoding="utf-8",
    )
    support = {"a": {"assigned_amount": 0.0}, "b": {"assigned_amount": 2.0}}
    rows = MODULE.measurement_group_support(groups, support)
    assert [(row["measurement_group_id"], row["supported"]) for row in rows] == [
        ("G1", True), ("G2", False)
    ]
