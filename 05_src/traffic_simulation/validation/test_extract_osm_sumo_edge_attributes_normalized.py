import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "extract_osm_sumo_edge_attributes_normalized.py"
SPEC = importlib.util.spec_from_file_location("edge_attributes", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_load_osm_preserves_way_tags_and_route_members(tmp_path):
    osm = tmp_path / "source.osm.xml"
    osm.write_text(
        """<osm>
        <way id="10"><nd ref="1"/><nd ref="2"/><tag k="highway" v="primary"/><tag k="lanes" v="2"/></way>
        <relation id="20"><member type="way" ref="10" role=""/><tag k="type" v="route"/><tag k="route" v="road"/><tag k="network" v="JP:national"/><tag k="ref" v="15"/></relation>
        </osm>""",
        encoding="utf-8",
    )

    ways, memberships = MODULE.load_osm(osm, {"10"})

    assert ways["10"] == {"highway": "primary", "lanes": "2"}
    assert memberships["10"] == [{"relation_id": "20", "network": "JP:national", "ref": "15", "operator": ""}]


def test_load_net_uses_orig_id_for_reverse_candidate(tmp_path):
    net = tmp_path / "network.net.xml"
    net.write_text(
        """<net>
        <edge id="synthetic-forward" from="a" to="b"><lane id="f_0" speed="10"><param key="origId" value="10 11"/></lane></edge>
        <edge id="synthetic-reverse" from="b" to="a"><lane id="r_0" speed="10"><param key="origId" value="10"/></lane></edge>
        </net>""",
        encoding="utf-8",
    )

    records, endpoint_index, all_orig_ids = MODULE.load_net(net, {"synthetic-forward"})

    assert records["synthetic-forward"]["orig_ids"] == ["10", "11"]
    assert endpoint_index[("b", "a")] == ["synthetic-reverse"]
    assert all_orig_ids["synthetic-reverse"] == ["10"]


def test_oneway_does_not_claim_allow_disallow_provenance():
    record = {"orig_ids": ["10"], "type": "highway.primary"}

    source_type, _, rule = MODULE.permission_source(record, {"10": {"oneway": "yes"}})

    assert source_type == "SUMO_TYPE_DEFAULT"
    assert rule == "CUSTOM_TYPEMAP_PERMISSION_DEFAULT_V1"
