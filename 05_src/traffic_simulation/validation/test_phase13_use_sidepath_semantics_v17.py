from __future__ import annotations

from collections import OrderedDict
from collections import Counter
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


BASE_TAGS = {"highway": "trunk", "oneway": "yes", "lanes": "2"}
LANE_COUNTS = {"forward": 2}
DECISION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_use_sidepath_semantics_decision.yml"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
INVARIANTS_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_semantic_invariants.yml"
)


def _normalize(tags):
    return normalize_static_access_rules(
        source_way_id=28017223,
        tags=tags,
        lane_counts=LANE_COUNTS,
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


def test_bicycle_use_sidepath_preserves_semantics_with_empty_domain() -> None:
    collection = _normalize({**BASE_TAGS, "bicycle": "use_sidepath"})
    bicycle_rule = next(
        rule for rule in collection["rules"] if rule["source_key"] == "bicycle"
    )

    assert bicycle_rule["source_key"] == "bicycle"
    assert bicycle_rule["source_value"] == "use_sidepath"
    assert bicycle_rule["source_value"] != "no"
    assert bicycle_rule["vehicle_domain"] == []
    assert bicycle_rule["provenance"]["access_value_semantics"] == (
        "parallel_way_required"
    )
    assert bicycle_rule["provenance"][
        "permission_effect_on_governed_vclasses"
    ] == "none"
    assert bicycle_rule["provenance"]["source_value_rewritten"] is False


def test_bicycle_use_sidepath_does_not_change_motorized_permission() -> None:
    without_bicycle = _normalize({**BASE_TAGS, "access": "no"})["rules"]
    with_bicycle = _normalize(
        {**BASE_TAGS, "access": "no", "bicycle": "use_sidepath"}
    )["rules"]

    maxima_without = _delivery_maxima(without_bicycle)
    maxima_with = _delivery_maxima(with_bicycle)

    assert maxima_with == maxima_without
    assert resolve_maximal_static_effect(maxima_with)["effect"] == "denied"


@pytest.mark.parametrize("source_key", ["access", "vehicle", "motor_vehicle"])
def test_use_sidepath_remains_fail_closed_outside_approved_mode_keys(
    source_key: str,
) -> None:
    with pytest.raises(StaticAccessError) as caught:
        _normalize({**BASE_TAGS, source_key: "use_sidepath"})

    assert caught.value.stop_code == "ACCESS_VALUE_UNSUPPORTED"


@pytest.mark.parametrize("source_value", ["use_sidepth", "unknown_sidepath"])
def test_unknown_bicycle_values_remain_fail_closed(source_value: str) -> None:
    with pytest.raises(StaticAccessError) as caught:
        _normalize({**BASE_TAGS, "bicycle": source_value})

    assert caught.value.stop_code == "ACCESS_VALUE_UNSUPPORTED"


def test_bicycle_use_sidepath_is_record_order_invariant() -> None:
    forward = OrderedDict(
        [
            ("highway", "trunk"),
            ("oneway", "yes"),
            ("lanes", "2"),
            ("access", "no"),
            ("bicycle", "use_sidepath"),
        ]
    )
    reversed_tags = OrderedDict(reversed(list(forward.items())))

    assert _normalize(forward) == _normalize(reversed_tags)


def test_use_sidepath_is_an_independent_access_value_decision() -> None:
    decision = yaml.safe_load(DECISION_PATH.read_text(encoding="utf-8"))

    assert decision["decision_id"] == "DEC-P13-USE-SIDEPATH-SEMANTICS-001"
    assert decision["decision_version"] == "1.0.0"
    assert decision["status"] == "approved"
    assert decision["decision_method"]["selected_method"] == (
        "new_independent_decision"
    )
    assert decision["decision_method"]["differs_from_general_principle"] is False
    assert decision["responsibility_boundary"]["existing_decision"][
        "decision_id"
    ] == "DEC-P13-VEHICLE-ONTOLOGY-001"
    assert decision["decision"]["normalized_semantics"] == (
        "parallel_way_required"
    )
    assert decision["decision"]["approved_base_keys"] == ["bicycle"]
    assert decision["future_extension"]["foot_can_reuse_this_decision"] is True


def test_use_sidepath_decision_is_synchronized_to_registry_and_invariant() -> None:
    decision = yaml.safe_load(DECISION_PATH.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    invariants = yaml.safe_load(INVARIANTS_PATH.read_text(encoding="utf-8"))
    registered = next(
        item
        for item in registry["access_values"]
        if item["source_value"] == "use_sidepath"
    )

    assert registry["registry_version"] == "1.10.0"
    assert registered["decision_id"] == decision["decision_id"]
    assert registered["normalized_semantics"] == (
        decision["decision"]["normalized_semantics"]
    )
    assert registered["applicable_base_keys"] == ["bicycle", "foot"]
    assert registered["required_vehicle_domain"] == []
    assert registered["permission_effect_on_governed_vclasses"] == "none"
    invariant = next(
        item
        for item in invariants["invariants"]
        if item["invariant_id"] == "AR-ACCESS-011"
    )
    assert invariants["version"] == "1.8.0"
    assert "parallel_way_required" in invariant["assertion"]
    assert "never rewritten to no" in invariant["assertion"]


def test_fixed_c1_population_matches_immutable_source() -> None:
    decision = yaml.safe_load(DECISION_PATH.read_text(encoding="utf-8"))
    fixed = decision["fixed_population"]
    source_path = REPOSITORY_ROOT / fixed["source_osm"]
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    target_ids = set(fixed["source_way_ids"])
    tags_by_way = {}

    for _, element in ET.iterparse(source_path, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in target_ids:
                tags_by_way[way_id] = {
                    tag.attrib["k"]: tag.attrib["v"]
                    for tag in element.findall("tag")
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()

    assert digest == fixed["source_osm_byte_sha256"]
    assert len(target_ids) == fixed["source_way_count"] == 27
    assert set(tags_by_way) == target_ids
    assert all(tags["bicycle"] == "use_sidepath" for tags in tags_by_way.values())
    assert Counter(tags["highway"] for tags in tags_by_way.values()) == (
        fixed["highway_counts"]
    )
