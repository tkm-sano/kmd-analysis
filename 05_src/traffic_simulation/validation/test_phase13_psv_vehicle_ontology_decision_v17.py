from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DECISION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_psv_vehicle_ontology_decision.yml"
)


def _yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_psv_decision_uses_fixed_primary_authorities_and_exact_intersection() -> None:
    decision = _yaml(DECISION_PATH)
    result = decision["decision"]

    assert decision["status"] == "approved"
    assert decision["decision_id"] == "DEC-P13-PSV-ONTOLOGY-001"
    assert result["rule_id"] == "OSM_PSV_TO_GOVERNED_BUS_TAXI_V1"
    assert result["registered_vehicle_domain"] == ["bus", "taxi"]
    assert result["class_intersections"] == {
        "bus": True,
        "coach": False,
        "taxi": True,
    }
    assert result["permission_effect_on_managed_delivery"] == "none"
    assert result["formal_exclusion"] is False

    evidence_ids = {
        item["evidence_id"] for item in decision["primary_authority_evidence"]
    }
    assert evidence_ids == {
        "OSM-PSV-KEY-REV-2960634",
        "OSM-ACCESS-HIERARCHY-REV-3054035",
        "SUMO-VCLASS-V1-24-0",
    }
    for evidence in decision["primary_authority_evidence"]:
        snapshot = REPOSITORY_ROOT / evidence["snapshot_path"]
        assert evidence["snapshot_byte_sha256"] == _sha256(snapshot)
        if evidence["authority"] == "OpenStreetMap Wiki":
            assert f"oldid={evidence['revision_id']}" in evidence["url"]
        else:
            assert evidence["source_commit"] in evidence["url"]


def test_psv_decision_matches_all_sixteen_fixed_records() -> None:
    decision = _yaml(DECISION_PATH)
    fixed = decision["fixed_record_evidence"]
    extraction_path = REPOSITORY_ROOT / fixed["extraction_output"]
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    records = [
        item
        for item in extraction["records"]
        if item["selected_blocking_base_key_after_decision_001"] == "psv"
    ]

    assert fixed["extraction_output_byte_sha256"] == _sha256(extraction_path)
    assert fixed["extraction_output_semantic_sha256"] == extraction["semantic_sha256"]
    assert len(records) == fixed["selected_source_way_count"] == 16
    assert Counter(
        occurrence["source_key"]
        for item in records
        for occurrence in item["target_occurrences"]
        if occurrence["base_key"] == "psv"
    ) == fixed["source_key_counts"]
    assert sum(item["source_tags"].get("tourist_bus") == "yes" for item in records) == 9


def test_psv_primary_text_supports_bus_taxi_and_separate_coach_boundary() -> None:
    decision = _yaml(DECISION_PATH)
    evidence = {
        item["evidence_id"]: item for item in decision["primary_authority_evidence"]
    }
    psv_text = (
        REPOSITORY_ROOT / evidence["OSM-PSV-KEY-REV-2960634"]["snapshot_path"]
    ).read_text(encoding="utf-8")
    access_text = (
        REPOSITORY_ROOT
        / evidence["OSM-ACCESS-HIERARCHY-REV-3054035"]["snapshot_path"]
    ).read_text(encoding="utf-8")
    sumo_text = (
        REPOSITORY_ROOT / evidence["SUMO-VCLASS-V1-24-0"]["snapshot_path"]
    ).read_text(encoding="utf-8")

    child_section = psv_text.split("== Child tags ==", 1)[1].split("== How to map ==", 1)[0]
    assert "{{Tag|bus}}" in child_section
    assert "{{Tag|taxi}}" in child_section
    assert "{{Key|coach}}" not in child_section
    assert "{{Key|coach}} - restrictions on long-distance buses" in psv_text
    assert "{{Key|psv}} – public service vehicle" in access_text
    assert "{{Key|coach}} – a bus for long-distance travel" in access_text
    assert "| bus            | 9" in sumo_text and "urban line traffic" in sumo_text
    assert "| coach          | 10" in sumo_text and "overland transport" in sumo_text
    assert "| taxi           | 8" in sumo_text

    boundaries = "\n".join(decision["mandatory_boundaries"])
    assert "psv does not grant or deny the SUMO coach" in boundaries
    assert "tourist_bus=yes co-occurrences remain separate" in boundaries
    assert "not treated as a claim that UK statutory PSV law applies in Japan" in boundaries
