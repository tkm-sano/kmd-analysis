from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DECISION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_motorcar_vehicle_ontology_decision.yml"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
OSM_PATH = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)


def _yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target_way_tags() -> dict[int, dict[str, str]]:
    targets = {783347228, 1051964008}
    result: dict[int, dict[str, str]] = {}

    for _, elem in ET.iterparse(OSM_PATH, events=("end",)):
        if elem.tag == "way":
            way_id = int(elem.attrib["id"])
            if way_id in targets:
                result[way_id] = {
                    tag.attrib["k"]: tag.attrib["v"]
                    for tag in elem.findall("tag")
                }
            elem.clear()

    return result


def test_motorcar_decision_is_fixed_with_exact_governed_intersection() -> None:
    decision = _yaml(DECISION_PATH)
    result = decision["decision"]

    expected = [
        "passenger",
        "taxi",
        "bus",
        "coach",
        "delivery",
        "truck",
    ]

    assert decision["status"] == "approved"
    assert decision["decision_id"] == "DEC-P13-MOTORCAR-ONTOLOGY-001"
    assert result["rule_id"] == "OSM_MOTORCAR_TO_GOVERNED_DOUBLE_TRACKED_V1"
    assert result["registered_vehicle_domain"] == expected
    assert decision["formal_reasoning"]["governed_intersection"] == expected
    assert decision["formal_reasoning"]["excluded_governed_classes"] == ["motorcycle"]
    assert result["permission_effect_on_managed_delivery"] == "applies"
    assert result["formal_exclusion"] is False

    evidence = decision["primary_authority_evidence"]
    for item in evidence.values():
        snapshot = REPOSITORY_ROOT / item["snapshot_path"]
        assert item["snapshot_byte_sha256"] == _sha256(snapshot)


def test_motorcar_decision_matches_fixed_154_record_population() -> None:
    decision = _yaml(DECISION_PATH)
    fixed = decision["fixed_record_evidence"]
    extraction_path = REPOSITORY_ROOT / fixed["extraction_output"]
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))

    records = [
        item
        for item in extraction["records"]
        if item["selected_blocking_base_key_after_decision_001"] == "motorcar"
    ]

    assert len(records) == fixed["selected_motorcar_record_count"] == 154

    assert Counter(
        occurrence["source_value"]
        for item in records
        for occurrence in item["target_occurrences"]
        if occurrence["base_key"] == "motorcar"
    ) == {"designated": 154}

    assert Counter(
        item["source_tags"].get("highway")
        for item in records
    ) == {
        "motorway_link": 104,
        "motorway": 50,
    }

    assert Counter(
        item["source_tags"].get("motorcycle")
        for item in records
    ) == {
        "designated": 148,
        "no": 6,
    }


def test_motorcar_successor_way_source_divergence_is_preserved() -> None:
    decision = _yaml(DECISION_PATH)
    tags = _target_way_tags()

    assert set(tags) == {783347228, 1051964008}

    for way_id in sorted(tags):
        assert tags[way_id]["highway"] == "motorway"
        assert tags[way_id]["horse"] == "no"
        assert tags[way_id]["motor_vehicle"] == "no"
        assert tags[way_id]["motorcar"] == "designated"
        assert tags[way_id]["motorcycle"] == "designated"

    divergence = decision["japan_tagging_divergence"]
    assert divergence["reference_motorway_tags"]["motor_vehicle"] == "yes"
    assert divergence["observed_successor_way_tags"]["motor_vehicle"] == "no"
    assert divergence["treatment"] == "preserve_source_divergence_without_rewriting"

    boundaries = "\n".join(decision["mandatory_boundaries"])
    assert "source motor_vehicle=no value is preserved" in boundaries


def test_motorcar_decision_is_synchronized_to_registry() -> None:
    decision = _yaml(DECISION_PATH)
    registry = _yaml(REGISTRY_PATH)

    assert registry["vehicle_ontology"]["domains"]["motorcar"] == (
        decision["decision"]["registered_vehicle_domain"]
    )


def test_motorcar_full_population_validation_is_fixed_and_passed() -> None:
    decision = _yaml(DECISION_PATH)
    validation = decision["full_population_validation"]

    probe = validation["probe"]
    probe_path = REPOSITORY_ROOT / probe["path"]

    assert probe["byte_sha256"] == _sha256(probe_path)
    assert probe["remaining_total_blocker_count"] == 31
    assert probe["remaining_motorcar_hierarchy_blocker_count"] == 0
    assert probe["remaining_blocker_stop_codes"] == {
        "ACCESS_VALUE_UNSUPPORTED": 31
    }

    comparator_v1 = validation["comparator_v1"]
    comparator_v1_path = REPOSITORY_ROOT / comparator_v1["path"]

    assert comparator_v1["byte_sha256"] == _sha256(comparator_v1_path)
    assert comparator_v1["status"] == "failed"
    assert "ordering" in comparator_v1["failure_reason"]

    comparator_v2 = validation["comparator_v2"]
    comparator_v2_path = REPOSITORY_ROOT / comparator_v2["path"]

    assert comparator_v2["byte_sha256"] == _sha256(comparator_v2_path)
    assert comparator_v2["status"] == "passed"
    assert comparator_v2["fixed_motorcar_record_count"] == 154
    assert comparator_v2["successor_way_count"] == 2
    assert comparator_v2["affected_way_count"] == 156
    assert comparator_v2["resolved_motorcar_hierarchy_blocker_count"] == 156
    assert comparator_v2["remaining_motorcar_hierarchy_blocker_count"] == 0
    assert comparator_v2["remaining_affected_blocked_way_count"] == 0
    assert comparator_v2["new_blocker_id_count"] == 0
    assert comparator_v2["unaffected_normalized_rules_unchanged"] is True
    assert comparator_v2["unaffected_static_maxima_unchanged"] is True

    state = decision["implementation_state"]
    assert state["registry_update"] == "implemented"
    assert state["full_population_probe"] == "passed"
    assert state["phase13_complete"] is True
