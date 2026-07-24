"""Tests for focused OSM restriction-relation visualization."""

from __future__ import annotations

from pathlib import Path

import pytest

from traffic_simulation.visualization.render_osm_relation_sample import (
    parse_relation_xml,
)


SAMPLE_XML = """\
<osm version="0.6">
  <node id="1" lat="35.0" lon="139.0"/>
  <node id="2" lat="35.1" lon="139.1"/>
  <node id="3" lat="35.2" lon="139.2"/>
  <way id="10">
    <nd ref="1"/><nd ref="2"/>
    <tag k="highway" v="primary"/>
  </way>
  <way id="20">
    <nd ref="2"/><nd ref="3"/>
    <tag k="highway" v="primary"/>
  </way>
  <relation id="100">
    <member type="way" ref="10" role="from"/>
    <member type="node" ref="2" role="via"/>
    <member type="way" ref="20" role="to"/>
    <tag k="restriction" v="only_straight_on"/>
    <tag k="type" v="restriction:bus"/>
  </relation>
</osm>
"""


def test_parse_relation_xml_preserves_roles_and_source_semantics(
    tmp_path: Path,
) -> None:
    path = tmp_path / "relation.osm.xml"
    path.write_text(SAMPLE_XML, encoding="utf-8")

    sample = parse_relation_xml(path, "100")

    assert sample.relation_id == "100"
    assert sample.tags == {
        "restriction": "only_straight_on",
        "type": "restriction:bus",
    }
    assert [(member.role, member.member_type, member.reference) for member in sample.members] == [
        ("from", "way", "10"),
        ("via", "node", "2"),
        ("to", "way", "20"),
    ]
    assert sample.geometry.is_empty is False


def test_parse_relation_xml_rejects_incomplete_member_geometry(
    tmp_path: Path,
) -> None:
    path = tmp_path / "relation.osm.xml"
    path.write_text(SAMPLE_XML.replace('<node id="3" lat="35.2" lon="139.2"/>', ""), encoding="utf-8")

    with pytest.raises(ValueError, match="missing node references"):
        parse_relation_xml(path, "100")
