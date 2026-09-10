from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from traffic_simulation.network.oneway_materialization_v17 import (
    OnewayMaterializationError,
    materialize_osm_oneway,
)


def _write_fixture(path: Path, ways: str) -> None:
    path.write_text(
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<osm version='0.6'>\n"
        "  <node id='1' lat='35.0' lon='139.0'/>\n"
        "  <node id='2' lat='35.1' lon='139.1'/>\n"
        f"{ways}"
        "</osm>\n",
        encoding="utf-8",
    )


def _way_tags(path: Path) -> dict[int, dict[str, str]]:
    root = ET.parse(path).getroot()
    return {
        int(way.attrib["id"]): {
            tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")
        }
        for way in root.findall("way")
    }


def test_materializes_registered_v17_direction_without_source_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.osm.xml"
    target = tmp_path / "materialized.osm.xml"
    manifest = tmp_path / "manifest.json"
    _write_fixture(
        source,
        """  <way id='100'><nd ref='1'/><nd ref='2'/><tag k='highway' v='residential'/><tag k='width' v='2.5'/></way>
  <way id='101'><nd ref='1'/><nd ref='2'/><tag k='highway' v='motorway'/></way>
  <way id='102'><nd ref='1'/><nd ref='2'/><tag k='junction' v='roundabout'/><tag k='highway' v='tertiary'/></way>
  <way id='103'><nd ref='1'/><nd ref='2'/><tag k='oneway' v='yes'/><tag k='highway' v='service'/></way>
  <way id='104'><nd ref='1'/><nd ref='2'/><tag k='oneway' v='no'/><tag k='highway' v='service'/></way>
  <way id='105'><nd ref='1'/><nd ref='2'/><tag k='oneway' v='-1'/><tag k='highway' v='service'/></way>
  <way id='106'><nd ref='1'/><nd ref='2'/><tag k='oneway' v='true'/><tag k='highway' v='service'/></way>
  <way id='107'><nd ref='1'/><nd ref='2'/><tag k='highway' v='footway'/></way>
""",
    )
    before = source.read_bytes()

    result = materialize_osm_oneway(source, target, manifest)

    assert source.read_bytes() == before
    tags = _way_tags(target)
    assert tags[100]["oneway"] == "no"
    assert tags[101]["oneway"] == "yes"
    assert tags[102]["oneway"] == "yes"
    assert tags[103]["oneway"] == "yes"
    assert tags[104]["oneway"] == "no"
    assert tags[105]["oneway"] == "-1"
    assert tags[106]["oneway"] == "yes"
    assert "oneway" not in tags[107]

    assert result["counts"] == {
        "governed_ways": 7,
        "inserted": 3,
        "normalized": 1,
        "already_canonical": 3,
        "non_governed_ways": 1,
    }
    records = {record["source_way_id"]: record for record in result["records"]}
    assert records[100] | {
        "canonical_oneway": "no",
        "value_origin": "rule_derived",
        "rule_id": "OSM_ONEWAY_ABSENT_DEFAULT_NO",
        "source_value": None,
    } == records[100]
    assert records[100]["assumption_ids"] == []
    assert records[100]["used_width"] is False
    assert records[101]["rule_id"] == "OSM_IMPLICIT_MOTORWAY_ONEWAY_YES"
    assert records[102]["rule_id"] == "OSM_IMPLICIT_ROUNDABOUT_ONEWAY_YES"
    assert records[106]["value_origin"] == "source_normalized"

    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved == result
    assert saved["source_sha256"] == hashlib.sha256(before).hexdigest()
    assert saved["source_mutated"] is False
    assert saved["width_direction_inference"] is False


def test_unknown_direction_fails_closed_and_publishes_nothing(tmp_path: Path) -> None:
    source = tmp_path / "source.osm.xml"
    target = tmp_path / "materialized.osm.xml"
    manifest = tmp_path / "manifest.json"
    _write_fixture(
        source,
        "  <way id='200'><nd ref='1'/><nd ref='2'/><tag k='highway' v='service'/><tag k='oneway' v='maybe'/></way>\n",
    )

    with pytest.raises(OnewayMaterializationError, match="Way 200") as caught:
        materialize_osm_oneway(source, target, manifest)

    assert caught.value.stop_code == "ONEWAY_VALUE_UNSUPPORTED"
    assert not target.exists()
    assert not manifest.exists()


def test_record_order_does_not_change_semantic_result(tmp_path: Path) -> None:
    first = tmp_path / "first.osm.xml"
    second = tmp_path / "second.osm.xml"
    _write_fixture(
        first,
        "  <way id='300'><nd ref='1'/><nd ref='2'/><tag k='width' v='4'/><tag k='highway' v='residential'/></way>\n",
    )
    _write_fixture(
        second,
        "  <way id='300'><nd ref='1'/><nd ref='2'/><tag k='highway' v='residential'/><tag k='width' v='4'/></way>\n",
    )

    first_result = materialize_osm_oneway(
        first, tmp_path / "first.out.xml", tmp_path / "first.json"
    )
    second_result = materialize_osm_oneway(
        second, tmp_path / "second.out.xml", tmp_path / "second.json"
    )

    for result in (first_result, second_result):
        result.pop("source_path")
        result.pop("target_path")
        result.pop("source_sha256")
        result.pop("target_sha256")
    assert first_result == second_result
