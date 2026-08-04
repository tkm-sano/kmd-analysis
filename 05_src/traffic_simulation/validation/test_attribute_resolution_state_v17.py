from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from traffic_simulation.network.attribute_resolution_state_v17 import (
    LegacyExclusionRequired,
    V17StateContractError,
    build_v17_record,
    migrate_legacy_resolution,
    validate_migration_registry,
    validate_v17_record,
    write_v17_record_atomic,
)
from traffic_simulation.paths import REPOSITORY_ROOT


def identity() -> dict:
    return {
        "population_version": "ota_ward_relation_closure_v16",
        "source_way_id": 1001,
        "directed_segment_id": None,
        "source_direction": None,
        "lane_position": None,
        "vehicle_class": None,
        "attribute_name": "lanes",
        "scenario_context_id": None,
    }


def legacy(
    state: str,
    action: str,
    value: int | str | None,
    *,
    rule_id: str | None = None,
    evidence_id: str | None = None,
) -> dict:
    return {
        "resolution_action": action,
        "resolution_rule_id": rule_id,
        "value_state": state,
        "resolved_value": value,
        "selected_evidence_id": evidence_id,
        "stop_failure_codes": [],
        "review_status": "machine_classified",
    }


def record_from_legacy(
    legacy_resolution: dict,
    *,
    profile: str = "structural",
    source_observations: list[dict] | None = None,
) -> dict:
    migrated = migrate_legacy_resolution(legacy_resolution, profile=profile)
    return build_v17_record(
        identity=identity(),
        profile=profile,
        classification_record_id=f"acr:1001:lanes:{profile}",
        source_observations=source_observations or [],
        resolution=migrated,
        provenance={"activity": "phase3_fixture"},
    )


def test_migration_registry_is_machine_valid() -> None:
    registry = validate_migration_registry()
    assert registry["read_compatibility_only"] is True
    assert registry["v17_writer_emits_value_state"] is False


@pytest.mark.parametrize(
    ("legacy_resolution", "origin"),
    [
        (legacy("explicit_osm", "adopt_explicit", 2), "source_explicit"),
        (
            legacy(
                "derived_osm_rule", "derive_osm_rule", 2, rule_id="RULE-001"
            ),
            "rule_derived",
        ),
        (
            legacy(
                "authoritative_external",
                "adopt_external_evidence",
                2,
                evidence_id="EVID-001",
            ),
            "evidence_derived",
        ),
        (
            legacy(
                "derived_validated_model",
                "apply_governed_rule",
                2,
                rule_id="MODEL-001",
            ),
            "derived_validated_model",
        ),
        (
            legacy(
                "structural_placeholder",
                "apply_structural_placeholder",
                2,
                rule_id="BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1",
            ),
            "model_assumed",
        ),
    ],
)
def test_registered_successful_legacy_states_map_explicitly(
    legacy_resolution: dict, origin: str
) -> None:
    migrated = migrate_legacy_resolution(legacy_resolution, profile="structural")
    assert migrated["resolution_status"] == "resolved"
    assert migrated["value_origin"] == origin
    assert migrated["stop_code"] is None


def test_unknown_legacy_state_fails_closed_and_matches_fixed_oracle() -> None:
    migrated = migrate_legacy_resolution(
        legacy("unknown_legacy_state", "stop_unresolved", None),
        profile="formal",
    )
    oracle_catalog = json.loads(
        (
            REPOSITORY_ROOT
            / "05_src/traffic_simulation/validation/fixtures/"
            "v17_attribute_resolution/oracle.json"
        ).read_text(encoding="utf-8")
    )
    oracle = next(
        item for item in oracle_catalog["oracles"] if item["oracle_id"] == "OR-V17-023"
    )
    assert migrated["resolution_status"] == oracle["resolution_status"]
    assert migrated["value_origin"] == oracle["value_origin"]
    assert migrated["effective_value"] == oracle["effective_value"]
    assert migrated["stop_code"] == oracle["stop_code"]


def test_fixed_legacy_mapping_oracle_uses_rule_derived() -> None:
    fixture_catalog = json.loads(
        (
            REPOSITORY_ROOT
            / "05_src/traffic_simulation/validation/fixtures/"
            "v17_attribute_resolution/inputs.json"
        ).read_text(encoding="utf-8")
    )
    fixture = next(
        item for item in fixture_catalog["cases"] if item["fixture_id"] == "V17-POS-020"
    )
    mapping = validate_migration_registry()["successful_mappings"][
        fixture["input"]["legacy_value_state"]
    ]
    assert mapping["resolution_status"] == "resolved"
    assert mapping["value_origin"] == "rule_derived"


def test_excluded_legacy_row_is_routed_outside_resolution_records() -> None:
    with pytest.raises(LegacyExclusionRequired):
        migrate_legacy_resolution(
            legacy("excluded", "exclude", None), profile="formal"
        )


def test_formal_profile_rejects_structural_assumption() -> None:
    with pytest.raises(V17StateContractError, match="formal migration rejects"):
        migrate_legacy_resolution(
            legacy(
                "structural_placeholder",
                "apply_structural_placeholder",
                2,
                rule_id="BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1",
            ),
            profile="formal",
        )


def test_v17_writer_emits_canonical_fields_without_value_state() -> None:
    record = record_from_legacy(
        legacy("explicit_osm", "adopt_explicit", 2),
        source_observations=[{"key": "lanes", "value": "2"}],
    )
    assert record["resolution_status"] == "resolved"
    assert record["value_origin"] == "source_explicit"
    assert "value_state" not in json.dumps(record, sort_keys=True)
    validate_v17_record(
        record, expected_classification_record_id="acr:1001:lanes:structural"
    )


def test_record_id_is_stable_when_only_resolution_result_changes() -> None:
    first = record_from_legacy(
        legacy("explicit_osm", "adopt_explicit", 2),
        source_observations=[{"key": "lanes", "value": "2"}],
    )
    second = record_from_legacy(
        legacy(
            "derived_osm_rule", "derive_osm_rule", 3, rule_id="RULE-001"
        )
    )
    assert first["record_id"] == second["record_id"]
    assert first["classification_record_id"] == second["classification_record_id"]


def test_classification_identity_change_is_rejected() -> None:
    record = record_from_legacy(
        legacy("explicit_osm", "adopt_explicit", 2),
        source_observations=[{"key": "lanes", "value": "2"}],
    )
    with pytest.raises(V17StateContractError, match="classification_record_id changed"):
        validate_v17_record(
            record, expected_classification_record_id="acr:999:lanes:structural"
        )


def test_nonresolved_writer_nulls_value_and_origin() -> None:
    record = record_from_legacy(
        legacy("missing", "stop_unresolved", None), profile="formal"
    )
    assert record["resolution_status"] == "valid_but_unsupported"
    assert record["effective_value"] is None
    assert record["value_origin"] is None
    assert record["stop_code"] == "LEGACY_STATE_MAPPING_UNSUPPORTED"


def test_unregistered_canonical_state_is_rejected_like_fixed_fixture() -> None:
    record = record_from_legacy(
        legacy("missing", "stop_unresolved", None), profile="formal"
    )
    changed = copy.deepcopy(record)
    changed["resolution_status"] = "unexpected"
    with pytest.raises(V17StateContractError, match="Schema violation"):
        validate_v17_record(changed)


def test_atomic_writer_refuses_overwrite(tmp_path: Path) -> None:
    record = record_from_legacy(
        legacy("explicit_osm", "adopt_explicit", 2),
        source_observations=[{"key": "lanes", "value": "2"}],
    )
    output = tmp_path / "record.json"
    write_v17_record_atomic(record, output)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == record
    with pytest.raises(FileExistsError):
        write_v17_record_atomic(record, output)


def test_migration_registry_schema_rejects_v17_legacy_writer() -> None:
    registry = validate_migration_registry()
    changed = copy.deepcopy(registry)
    changed["v17_writer_emits_value_state"] = True
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "reproducibility/config/traffic_simulation/schemas/"
            "legacy_state_migration_v17.schema.json"
        ).read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(changed)
