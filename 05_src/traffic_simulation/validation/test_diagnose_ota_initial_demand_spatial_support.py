import importlib.util
from pathlib import Path

import networkx as nx


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "diagnose_ota_initial_demand_spatial_support.py"
SPEC = importlib.util.spec_from_file_location("diagnose_spatial_support", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_group_is_route_choice_limited_when_connected_od_exists_but_route_omits_edge():
    graph = nx.DiGraph([("a", "b"), ("b", "a")])
    rows = MODULE.assess_groups(
        [{"measurement_group_id": "g", "official_name": "x", "selected_edge_ids": "a"}],
        {"a": {}, "b": {}}, graph,
        {"PT_0130": {"sources": {"a": 1}, "sinks": {"a": 1}}},
        {("PT_0130", "PT_0131")}, {},
    )
    assert rows[0]["direct_cause"] == "connected_with_od_but_not_selected_by_route_assignment"


def test_daily_relation_aggregation_preserves_od_totals(tmp_path):
    source = tmp_path / "hourly.xml"
    output = tmp_path / "daily.xml"
    source.write_text(
        '<data><interval><tazRelation from="a" to="b" count="2"/></interval>'
        '<interval><tazRelation from="a" to="b" count="3"/></interval></data>', encoding="utf-8"
    )
    MODULE.write_daily_relations(source, output)
    _, totals = MODULE.read_positive_relations(output)
    assert totals == {("a", "b"): 5.0}
