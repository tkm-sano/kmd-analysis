from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import pytest
import yaml

from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
    resolve_maximal_static_effect,
    static_rule_dominates,
)
from traffic_simulation.paths import REPOSITORY_ROOT


BASE_TAGS = {"highway": "trunk", "oneway": "yes", "lanes": "2"}


def _rules(tags):
    return normalize_static_access_rules(
        source_way_id=150870020,
        tags={**BASE_TAGS, **tags},
        lane_counts={"forward": 2},
    )["rules"]


def _maxima(rules):
    return maximal_static_rules_for_tuple(
        rules,
        direction="forward",
        lane_position=0,
        lane_count=2,
        vehicle_class="delivery",
        context=default_scenario_context(),
    )


def test_motor_vehicle_yes_overrides_vehicle_no_after_equal_domain_projection() -> None:
    rules = _rules({"vehicle": "no", "motor_vehicle": "yes"})

    assert {rule["source_key"] for rule in rules} == {"vehicle", "motor_vehicle"}
    assert len({tuple(rule["vehicle_domain"]) for rule in rules}) == 1
    maxima = _maxima(rules)

    assert [rule["source_key"] for rule in maxima] == ["motor_vehicle"]
    assert resolve_maximal_static_effect(maxima)["effect"] == "allowed"


def test_motor_vehicle_no_overrides_vehicle_yes_after_equal_domain_projection() -> None:
    maxima = _maxima(_rules({"vehicle": "yes", "motor_vehicle": "no"}))

    assert [rule["source_key"] for rule in maxima] == ["motor_vehicle"]
    assert resolve_maximal_static_effect(maxima)["effect"] == "denied"


def test_motorcar_child_remains_more_specific_than_motor_vehicle_and_vehicle() -> None:
    maxima = _maxima(
        _rules({"vehicle": "no", "motor_vehicle": "yes", "motorcar": "no"})
    )

    assert [rule["source_key"] for rule in maxima] == ["motorcar"]
    assert resolve_maximal_static_effect(maxima)["effect"] == "denied"


def test_equal_projected_domains_do_not_create_precedence_for_unrelated_keys() -> None:
    vehicle, motor_vehicle = _rules({"vehicle": "yes", "motor_vehicle": "no"})
    left = deepcopy(vehicle)
    right = deepcopy(motor_vehicle)
    left["source_key"] = "goods"
    left["rule_id"] = "unrelated:goods"
    right["source_key"] = "hgv"
    right["rule_id"] = "unrelated:hgv"

    assert left["vehicle_domain"] == right["vehicle_domain"]
    assert not static_rule_dominates(left, right, lane_count=2)
    assert not static_rule_dominates(right, left, lane_count=2)


def test_child_over_parent_specificity_is_record_order_invariant() -> None:
    forward = OrderedDict(
        [
            ("vehicle", "no"),
            ("motor_vehicle", "yes"),
        ]
    )
    reverse = OrderedDict(reversed(list(forward.items())))

    forward_maxima = _maxima(_rules(forward))
    reverse_maxima = _maxima(_rules(reverse))

    assert forward_maxima == reverse_maxima
    assert [rule["source_key"] for rule in forward_maxima] == ["motor_vehicle"]


def test_current_runtime_exposes_the_equal_projection_as_a_real_conflict() -> None:
    """The pre-fix runtime reaches conflicting maxima, rather than value failure."""

    rules = _rules({"vehicle": "no", "motor_vehicle": "yes"})
    maxima = _maxima(rules)
    if len(maxima) == 2:
        with pytest.raises(StaticAccessError) as caught:
            resolve_maximal_static_effect(maxima)
        assert caught.value.stop_code == "ACCESS_SPECIFICITY_CONFLICT"
    else:
        assert [rule["source_key"] for rule in maxima] == ["motor_vehicle"]


def test_source_hierarchy_is_registered_and_policy_owned() -> None:
    registry = yaml.safe_load(
        (REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/"
         "attribute_resolution_registries_v17.yml").read_text(encoding="utf-8")
    )
    hierarchy = registry["vehicle_ontology"]["source_hierarchy"]
    policy = (
        REPOSITORY_ROOT
        / "05_src/traffic_simulation/specifications/"
        "10_approved_attribute_resolution_policy.md"
    ).read_text(encoding="utf-8")

    assert hierarchy["direct_parents"]["motor_vehicle"] == "vehicle"
    assert hierarchy["direct_parents"]["motorcar"] == "motor_vehicle"
    assert hierarchy["direct_parents"]["psv"] == "motor_vehicle"
    assert "access < vehicle < motor_vehicle < vehicle_class" in policy
