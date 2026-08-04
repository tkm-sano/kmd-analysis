from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import jsonschema
import pytest
import yaml

from traffic_simulation.network.resolver_integration_v17 import (
    ResolverIntegrationError,
    build_resolver_integration_artifact,
    validate_resolver_integration_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution"
)
FIXTURE = FIXTURE_ROOT / "resolver_integration_phase11.osm.xml"
ORACLE = FIXTURE_ROOT / "resolver_integration_phase11_oracle.yml"
CONTEXT = {"weekday": "Mo", "time": "08:00"}


@pytest.fixture(scope="module")
def artifact() -> dict:
    return build_resolver_integration_artifact(
        FIXTURE, profile="formal", scenario_context=CONTEXT
    )


def _oracle() -> dict:
    return yaml.safe_load(ORACLE.read_text(encoding="utf-8"))


def _transformed_fixture(
    destination: Path, *, reverse_ways: bool = False, reverse_tags: bool = False
) -> Path:
    tree = ET.parse(FIXTURE)
    root = tree.getroot()
    if reverse_ways:
        children = list(root)
        way_positions = [index for index, item in enumerate(children) if item.tag == "way"]
        reversed_ways = list(reversed([children[index] for index in way_positions]))
        for index, way in zip(way_positions, reversed_ways, strict=True):
            children[index] = way
        root[:] = children
    if reverse_tags:
        for element in root.findall("way") + root.findall("relation"):
            children = list(element)
            tag_positions = [index for index, item in enumerate(children) if item.tag == "tag"]
            reversed_tags = list(reversed([children[index] for index in tag_positions]))
            for index, tag in zip(tag_positions, reversed_tags, strict=True):
                children[index] = tag
            element[:] = children
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return destination


def test_schema_gate_passes(artifact: dict) -> None:
    validate_resolver_integration_artifact(artifact)


def test_schema_or_semantic_tampering_fails(artifact: dict) -> None:
    broken = copy.deepcopy(artifact)
    broken["counts"]["speed_records"] = 7
    with pytest.raises(ResolverIntegrationError):
        validate_resolver_integration_artifact(broken)


def test_independent_count_oracle_matches(artifact: dict) -> None:
    assert artifact["counts"] == _oracle()["expected_counts"]


def test_independent_speed_oracle_matches(artifact: dict) -> None:
    observed = {
        item["directed_segment_id"]: item["speed_kmh"]
        for item in artifact["speed_projection"]
    }
    assert observed == _oracle()["expected_directional_speed_kmh"]


def test_independent_permission_oracle_matches(artifact: dict) -> None:
    by_way: dict[int, set[str]] = {}
    for item in artifact["permission_projection"]:
        way_id = int(item["directed_segment_id"].split(":")[1])
        by_way.setdefault(way_id, set()).add(item["effective_permission"])
    observed = {
        way_id: next(iter(values)) if len(values) == 1 else "mixed_by_lane"
        for way_id, values in by_way.items()
    }
    assert observed == _oracle()["expected_permission_by_way"]


def test_semantic_cross_stage_invariants_pass(artifact: dict) -> None:
    assert all(artifact["lineage_invariants"].values())
    assert set(artifact["formal_invariants"].values()) == {0}
    assert artifact["evidence_origin_audit"]["unapproved_evidence_emission_count"] == 0


def test_repeated_run_is_deterministic(artifact: dict) -> None:
    repeated = build_resolver_integration_artifact(
        FIXTURE, profile="formal", scenario_context=CONTEXT
    )
    assert repeated["semantic_sha256"] == artifact["semantic_sha256"]


@pytest.mark.parametrize(
    ("reverse_ways", "reverse_tags"), [(True, False), (False, True), (True, True)]
)
def test_source_order_metamorphic_relations(
    artifact: dict,
    tmp_path: Path,
    reverse_ways: bool,
    reverse_tags: bool,
) -> None:
    transformed = _transformed_fixture(
        tmp_path / "metamorphic.osm.xml",
        reverse_ways=reverse_ways,
        reverse_tags=reverse_tags,
    )
    observed = build_resolver_integration_artifact(
        transformed, profile="formal", scenario_context=CONTEXT
    )
    assert observed["semantic_sha256"] == artifact["semantic_sha256"]


def test_non_access_conditional_does_not_enter_access_blockers(artifact: dict) -> None:
    assert artifact["counts"]["conditional_rule_groups"] == 1
    assert artifact["counts"]["blockers"] == 0
