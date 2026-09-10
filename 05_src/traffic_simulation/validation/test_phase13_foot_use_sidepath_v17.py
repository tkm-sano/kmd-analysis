from __future__ import annotations

from collections import Counter, OrderedDict
import hashlib
import xml.etree.ElementTree as ET

import pytest
import yaml

from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
    resolve_maximal_static_effect,
)
from traffic_simulation.paths import REPOSITORY_ROOT


BASE_TAGS = {"highway": "primary", "oneway": "yes", "lanes": "2"}
DECISION_V1_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_use_sidepath_semantics_decision.yml"
)
AMENDMENT_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_use_sidepath_semantics_decision_v1_1.yml"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
C2_WAY_IDS = {150870020, 150870021, 150870022, 150870023}


def _normalize(tags):
    return normalize_static_access_rules(
        source_way_id=150870020,
        tags={**BASE_TAGS, **tags},
        lane_counts={"forward": 2},
    )


def _delivery_maxima(rules):
    return maximal_static_rules_for_tuple(
        rules,
        direction="forward",
        lane_position=0,
        lane_count=2,
        vehicle_class="delivery",
        context=default_scenario_context(),
    )


def test_foot_use_sidepath_preserves_empty_domain_and_parallel_way_semantics() -> None:
    result = _normalize(
        {
            "vehicle": "no",
            "motor_vehicle": "yes",
            "bicycle": "no",
            "foot": "use_sidepath",
            "foot:conditional": "no @ (roadway); yes @ (sidewalk)",
            "mofa": "no",
        }
    )
    foot_rule = next(rule for rule in result["rules"] if rule["source_key"] == "foot")

    assert foot_rule["source_value"] == "use_sidepath"
    assert foot_rule["source_value"] != "no"
    assert foot_rule["vehicle_domain"] == []
    assert foot_rule["provenance"]["access_value_semantics"] == "parallel_way_required"
    assert foot_rule["provenance"]["permission_effect_on_governed_vclasses"] == "none"
    assert foot_rule["provenance"]["source_value_rewritten"] is False
    assert result["deferred_conditional_tags"] == {
        "foot:conditional": "no @ (roadway); yes @ (sidewalk)"
    }

    maxima = _delivery_maxima(result["rules"])
    assert [rule["source_key"] for rule in maxima] == ["motor_vehicle"]
    assert resolve_maximal_static_effect(maxima)["effect"] == "allowed"


def test_foot_use_sidepath_is_record_order_invariant() -> None:
    tags = OrderedDict(
        [
            ("vehicle", "no"),
            ("motor_vehicle", "yes"),
            ("foot", "use_sidepath"),
            ("foot:conditional", "no @ (roadway); yes @ (sidewalk)"),
        ]
    )
    assert _normalize(tags) == _normalize(OrderedDict(reversed(list(tags.items()))))


@pytest.mark.parametrize("source_key", ["access", "vehicle", "motor_vehicle"])
def test_use_sidepath_remains_unsupported_for_unapproved_parent_keys(
    source_key: str,
) -> None:
    with pytest.raises(StaticAccessError) as caught:
        _normalize({source_key: "use_sidepath"})
    assert caught.value.stop_code == "ACCESS_VALUE_UNSUPPORTED"


def test_versioned_amendment_preserves_v1_and_adds_only_foot() -> None:
    original = yaml.safe_load(DECISION_V1_PATH.read_text(encoding="utf-8"))
    amendment = yaml.safe_load(AMENDMENT_PATH.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    use_sidepath = next(
        value for value in registry["access_values"]
        if value["source_value"] == "use_sidepath"
    )

    assert original["decision_version"] == "1.0.0"
    assert original["decision"]["approved_base_keys"] == ["bicycle"]
    assert amendment["decision_id"] == original["decision_id"]
    assert amendment["decision_version"] == "1.1.0"
    assert amendment["amends"]["decision_version"] == "1.0.0"
    assert amendment["decision"]["approved_base_keys"] == ["bicycle", "foot"]
    assert use_sidepath["applicable_base_keys"] == ["bicycle", "foot"]
    assert use_sidepath["normalized_semantics"] == "parallel_way_required"


def test_fixed_c2_population_matches_immutable_source() -> None:
    amendment = yaml.safe_load(AMENDMENT_PATH.read_text(encoding="utf-8"))
    fixed = amendment["fixed_population"]
    source = REPOSITORY_ROOT / fixed["source_osm"]
    tags_by_way = {}
    for _, element in ET.iterparse(source, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in C2_WAY_IDS:
                tags_by_way[way_id] = {
                    tag.attrib["k"]: tag.attrib["v"]
                    for tag in element.findall("tag")
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()

    assert hashlib.sha256(source.read_bytes()).hexdigest() == fixed[
        "source_osm_byte_sha256"
    ]
    assert set(tags_by_way) == C2_WAY_IDS == set(fixed["source_way_ids"])
    assert Counter(tags["highway"] for tags in tags_by_way.values()) == fixed[
        "highway_counts"
    ]
    for tags in tags_by_way.values():
        assert tags["vehicle"] == "no"
        assert tags["motor_vehicle"] == "yes"
        assert tags["bicycle"] == "no"
        assert tags["foot"] == "use_sidepath"
        assert tags["foot:conditional"] == "no @ (roadway); yes @ (sidewalk)"
        assert tags["mofa"] == "no"
