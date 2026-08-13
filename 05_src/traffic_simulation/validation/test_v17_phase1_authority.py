from __future__ import annotations

import json
from copy import deepcopy

import jsonschema
import pytest
import yaml

from traffic_simulation.network.validate_v17_phase1_authority import (
    Phase1AuthorityError,
    validate_phase1_authority,
)
from traffic_simulation.paths import REPOSITORY_ROOT


def _schema(name: str) -> dict:
    path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/schemas"
        / name
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_v17_phase1_authority_is_synchronized() -> None:
    result = validate_phase1_authority()
    assert result["phase1_authority"] == "passed"
    assert result["registry_stop_code_count"] == 30
    assert result["semantic_invariant_count"] >= 35
    assert result["runtime_validation"] == "not_run"
    assert result["formal_build_ready"] is False


def test_resolution_record_schema_accepts_resolved_formal_record() -> None:
    schema = _schema("attribute_resolution_record_v17.schema.json")
    record = {
        "schema_version": 17,
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "profile": "formal",
        "record_id": "a" * 64,
        "classification_record_id": "b" * 64,
        "source_way_id": 1,
        "directed_segment_id": "ds:1:0:1:forward",
        "source_direction": "forward",
        "lane_position": 0,
        "vehicle_class": "delivery",
        "attribute_name": "access",
        "scenario_context_id": "baseline",
        "source_observations": [{"key": "access", "value": "yes"}],
        "resolution_status": "resolved",
        "value_origin": "source_explicit",
        "effective_value": "allowed",
        "rule_ids": [],
        "evidence_ids": [],
        "assumption_ids": [],
        "stop_code": None,
        "review_required": False,
        "provenance": {"source": "fixture"},
    }
    jsonschema.Draft202012Validator(schema).validate(record)


def test_resolution_record_schema_rejects_formal_assumption() -> None:
    schema = _schema("attribute_resolution_record_v17.schema.json")
    record = {
        "schema_version": 17,
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "profile": "formal",
        "record_id": "a" * 64,
        "classification_record_id": "b" * 64,
        "source_way_id": 1,
        "directed_segment_id": "ds:1:0:1:forward",
        "source_direction": "forward",
        "lane_position": 0,
        "vehicle_class": "delivery",
        "attribute_name": "lanes",
        "scenario_context_id": "baseline",
        "source_observations": [],
        "resolution_status": "resolved",
        "value_origin": "model_assumed",
        "effective_value": 1,
        "rule_ids": [],
        "evidence_ids": [],
        "assumption_ids": ["BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"],
        "stop_code": None,
        "review_required": False,
        "provenance": {"source": "fixture"},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(record)


def test_resolution_record_schema_rejects_legacy_and_noncanonical_states() -> None:
    schema = _schema("attribute_resolution_record_v17.schema.json")
    status_schema = schema["properties"]["resolution_status"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(status_schema).validate("unsupported")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(status_schema).validate("not_applicable")


def test_configuration_schema_separates_scope_from_specificity() -> None:
    config_path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/sumo_network_v17.yml"
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    schema = _schema("sumo_network_v17.schema.json")
    changed = deepcopy(config)
    changed["access_resolution"]["specificity_axes"] = [
        "direction",
        "lane",
        "vehicle",
        "temporal",
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(changed)


def test_authority_validator_rejects_registry_hash_mismatch(tmp_path) -> None:
    config_path = (
        REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/sumo_network_v17.yml"
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["registries"]["sha256"] = "0" * 64
    changed_path = tmp_path / "sumo_network_v17.yml"
    changed_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(Phase1AuthorityError, match="SHA-256 mismatch"):
        validate_phase1_authority(config_path=changed_path)
