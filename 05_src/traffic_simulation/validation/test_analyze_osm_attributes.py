from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from traffic_simulation.network import analyze_osm_attributes as audit


@pytest.mark.parametrize("value", ["1", "12", "999"])
def test_lanes_accepts_positive_integer(value: str) -> None:
    assert audit.is_valid_lanes(value)


@pytest.mark.parametrize("value", [None, "", "0", "2;3", "2.0", "-1"])
def test_lanes_rejects_non_simple_values(value: object) -> None:
    assert not audit.is_valid_lanes(value)


@pytest.mark.parametrize("value", ["30", "40.5", "120"])
def test_maxspeed_accepts_plain_numeric_kmh(value: str) -> None:
    assert audit.is_valid_maxspeed(value)


@pytest.mark.parametrize("value", [None, "", "0", "50;40", "30 mph", "signals"])
def test_maxspeed_rejects_non_simple_values(value: object) -> None:
    assert not audit.is_valid_maxspeed(value)


@pytest.mark.parametrize("value", ["yes", "no", "-1"])
def test_oneway_accepts_governed_values(value: str) -> None:
    assert audit.is_valid_oneway(value)


@pytest.mark.parametrize("value", [None, "", "true", "1", "reversible"])
def test_oneway_rejects_other_values(value: object) -> None:
    assert not audit.is_valid_oneway(value)


def test_haversine_length_for_one_degree_at_equator() -> None:
    distance = audit.haversine_m((0.0, 0.0), (1.0, 0.0), 6_371_008.8)
    assert distance == pytest.approx(111_195.08, rel=1e-5)


def feature(highway: str, coordinates: list[list[float]], **tags: str) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coordinates},
        "properties": {"highway": highway, **tags},
    }


def test_summary_separates_missing_invalid_and_valid() -> None:
    features = [
        feature(
            "primary",
            [[139.0, 35.0], [139.001, 35.0]],
            lanes="2",
            maxspeed="50",
            oneway="no",
        ),
        feature(
            "residential",
            [[139.0, 35.0], [139.0, 35.001]],
            width="5",
            lane_markings="no",
            **{"lanes:forward": "1", "maxspeed:type": "JP:urban"},
        ),
        feature(
            "primary",
            [[139.0, 35.0], [139.001, 35.001]],
            lanes="2;3",
            maxspeed="50;40",
            oneway="true",
        ),
        feature("footway", [[139.0, 35.0], [139.002, 35.0]]),
    ]

    result = audit.summarize_features(
        features, ["primary", "residential"], 6_371_008.8
    )

    assert result["candidate_ways"] == 3
    assert result["ways_with_any_unresolved"] == 2
    assert result["ways_with_all_simple_values_valid"] == 1
    assert result["attributes"]["lanes"]["missing_ways"] == 1
    assert result["attributes"]["lanes"]["invalid_ways"] == 1
    assert result["attributes"]["lanes"]["invalid_value_counts"] == {"2;3": 1}
    assert result["attributes"]["maxspeed"]["unresolved_ways"] == 2
    assert result["attributes"]["maxspeed"]["invalid_value_counts"] == {"50;40": 1}
    assert result["attributes"]["oneway"]["unresolved_ways"] == 2
    assert result["unresolved_patterns"] == {
        "none": 1,
        "lanes,maxspeed,oneway": 2,
    }
    diagnostics = result["related_tag_diagnostics"]
    assert diagnostics["lanes_missing_with_directional_tag"] == 1
    assert diagnostics["lanes_missing_with_width"] == 1
    assert diagnostics["lanes_missing_with_lane_markings"] == 1
    assert diagnostics["maxspeed_missing_with_related_tag"] == 1


def test_geojson_sequence_reader_accepts_record_separator(tmp_path: Path) -> None:
    path = tmp_path / "roads.geojsonseq"
    records = [
        feature("primary", [[0, 0], [1, 0]], lanes="2"),
        feature("service", [[0, 0], [0, 1]]),
    ]
    path.write_text(
        "".join("\x1e" + json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    assert list(audit.read_geojson_sequence(path)) == records


def test_summary_rejects_empty_candidate_scope() -> None:
    with pytest.raises(ValueError, match="no candidate"):
        audit.summarize_features([], ["primary"], math.tau)
