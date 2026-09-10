"""Check geographic conversion and refusal of unaccepted snapshots."""
import json

import pytest
import yaml

from traffic_simulation.visualization import render_current_map as renderer


def test_raw_script_preserves_css_and_literal_template_characters():
    import folium
    m = folium.Map()
    script = renderer.RawScript()
    script.script = 'const css = "@media(max-width:650px){#road-detail{color:red}}"; const value = "{{literal}}";'
    m.add_child(script)
    output = m.get_root().render()
    assert script.script in output
    assert output.index('L.map(') < output.index('const css')


def test_network_geometry_permissions_and_internal_exclusion(tmp_path):
    network = tmp_path / "network.xml"
    network.write_text('''<net>
      <location netOffset="-377000,-3927000" projParameter="+proj=utm +zone=54 +datum=WGS84 +units=m +no_defs"/>
      <edge id="a" from="n1" to="n2"><lane shape="0,0 100,100" speed="10" allow="delivery passenger"/></edge>
      <edge id="b" from="n2" to="n1"><lane shape="100,100 0,0" speed="5" disallow="delivery"/></edge>
      <edge id=":internal" function="internal"><lane shape="0,0 10,10" speed="5"/></edge>
    </net>''')
    roads, lanes, nodes = renderer.read_network(network)
    assert (len(roads), lanes, nodes) == (2, 2, 2)
    assert [r[2] for r in roads] == [True, False]
    assert roads[0][4] == 36
    lat, lon = roads[0][1][0]
    assert 35.4 < lat < 35.6 and 139.5 < lon < 139.8
    assert roads[0][1] == roads[1][1][::-1]


def test_details_preserve_lanes_connections_signals_and_missing_values(tmp_path):
    path = tmp_path / "network.xml"
    path.write_text('''<net>
      <location netOffset="-377000,-3927000" projParameter="+proj=utm +zone=54 +datum=WGS84 +units=m +no_defs"/>
      <edge id="a" name="A &amp; B" type="highway.primary" from="n1" to="n2">
        <lane id="a_0" index="0" shape="0,0 100,100" length="141" width="3.2" speed="10" allow="passenger"/>
        <lane id="a_1" index="1" shape="1,0 101,100" length="142" speed="5" allow="delivery"><param key="origId" value="123"/></lane>
      </edge>
      <edge id="b" from="n2" to="n3"><lane id="b_0" index="0" shape="100,100 200,100" length="100" speed="5"/></edge>
      <tlLogic id="signal" programID="0" type="static"><phase duration="30" state="G"/></tlLogic>
      <junction id="n1" type="priority"/><junction id="n2" type="traffic_light"/>
      <connection from="a" to="b" fromLane="1" toLane="0" via=":n2_0_0" dir="r" tl="signal" linkIndex="0" state="O"/>
      <connection from=":n2_0" to="b" fromLane="0" toLane="0"/>
    </net>''')
    details = {}
    roads, lanes, nodes = renderer.read_network(path, details)
    assert (lanes, nodes) == (3, 3)
    assert roads[0][2] is True
    a = details['a']
    assert a['attributes']['name'] == 'A & B'
    assert a['lanes'][0]['width'] == '3.2'
    assert 'width' not in a['lanes'][1]
    assert a['lanes'][1]['params']['origId'] == '123'
    assert a['lanes'][0]['coordinates'] != a['lanes'][1]['coordinates']
    assert a['outgoing'] == details['b']['incoming']
    assert len(a['outgoing']) == 1
    assert a['outgoing'][0]['fromLane'] == '1'
    assert a['junctions']['to']['type'] == 'traffic_light'
    assert a['signals']['signal'][0]['phases'] == [{'duration': '30', 'state': 'G'}]


@pytest.mark.parametrize("accepted,sha", [(False, "correct"), (True, "wrong")])
def test_rejects_unaccepted_or_changed_network(tmp_path, monkeypatch, accepted, sha):
    network = tmp_path / "network.xml"
    network.write_text("not parsed unless accepted")
    digest = renderer.digest(network)
    acceptance = tmp_path / "acceptance.json"
    acceptance.write_text(json.dumps({"FORMAL_NETWORK_ACCEPTED": accepted, "network_semantic_sha256": digest}))
    authority = tmp_path / "authority.yml"
    authority.write_text(yaml.safe_dump({"accepted_run": {"acceptance_artifact": str(acceptance), "network_file": str(network), "network_sha256": digest if sha == "correct" else sha}}))
    config = tmp_path / "research.yml"
    config.write_text("{}")
    monkeypatch.setattr(renderer, "AUTHORITY_PATH", authority)
    monkeypatch.setattr(renderer, "RESEARCH_MAP_PATH", config)
    with pytest.raises(ValueError, match="acceptance/hash mismatch"):
        renderer.generate()
