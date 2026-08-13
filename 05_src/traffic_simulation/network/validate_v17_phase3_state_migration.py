from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.attribute_resolution_state_v17 import (
    V17StateContractError,
    build_v17_record,
    migrate_legacy_resolution,
    validate_migration_registry,
    validate_v17_record,
)
from traffic_simulation.network.validate_v17_fixture_oracle import (
    FIXTURE_ROOT,
    validate_fixture_oracle,
)
from traffic_simulation.network.validate_v17_phase1_authority import (
    validate_phase1_authority,
)
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase3_completion.yml"
)


class Phase3MigrationError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase3MigrationError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase3MigrationError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase3MigrationError(f"invalid repository artifact: {relative}")
    return path


def _identity() -> dict[str, Any]:
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


def _legacy(
    state: str,
    action: str,
    value: Any,
    *,
    rule_id: str | None = None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    return {
        "value_state": state,
        "resolution_action": action,
        "resolved_value": value,
        "resolution_rule_id": rule_id,
        "selected_evidence_id": evidence_id,
        "stop_failure_codes": [],
        "review_status": "machine_classified",
    }


def _contains_legacy_key(value: Any) -> bool:
    if isinstance(value, dict):
        return "value_state" in value or any(
            _contains_legacy_key(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_legacy_key(item) for item in value)
    return False


def validate_phase3_state_migration() -> dict[str, Any]:
    validate_phase1_authority()
    validate_fixture_oracle()
    migration = validate_migration_registry()

    samples = [
        (_legacy("explicit_osm", "adopt_explicit", 2), "source_explicit", [{}]),
        (
            _legacy(
                "derived_osm_rule", "derive_osm_rule", 2, rule_id="RULE-001"
            ),
            "rule_derived",
            [],
        ),
        (
            _legacy(
                "authoritative_external",
                "adopt_external_evidence",
                2,
                evidence_id="EVID-001",
            ),
            "evidence_derived",
            [],
        ),
        (
            _legacy(
                "derived_validated_model",
                "apply_governed_rule",
                2,
                rule_id="MODEL-001",
            ),
            "derived_validated_model",
            [],
        ),
        (
            _legacy(
                "structural_placeholder",
                "apply_structural_placeholder",
                2,
                rule_id="BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1",
            ),
            "model_assumed",
            [],
        ),
    ]
    record_ids: set[str] = set()
    for legacy, expected_origin, observations in samples:
        resolution = migrate_legacy_resolution(legacy, profile="structural")
        if resolution["value_origin"] != expected_origin:
            raise Phase3MigrationError(f"origin mapping mismatch: {expected_origin}")
        record = build_v17_record(
            identity=_identity(),
            profile="structural",
            classification_record_id="acr:1001:lanes:structural",
            source_observations=observations,
            resolution=resolution,
            provenance={"activity": "phase3_authority_validation"},
        )
        validate_v17_record(
            record,
            expected_classification_record_id="acr:1001:lanes:structural",
        )
        if _contains_legacy_key(record):
            raise Phase3MigrationError("v17 record contains value_state")
        record_ids.add(record["record_id"])
    if len(record_ids) != 1:
        raise Phase3MigrationError("mutable resolution result changed record identity")

    try:
        migrate_legacy_resolution(samples[-1][0], profile="formal")
    except V17StateContractError:
        pass
    else:
        raise Phase3MigrationError("formal migration accepted model_assumed")

    fixtures = _load_json(FIXTURE_ROOT / "inputs.json")["cases"]
    oracles = {
        item["oracle_id"]: item
        for item in _load_json(FIXTURE_ROOT / "oracle.json")["oracles"]
    }
    legacy_mapping_case = next(
        item for item in fixtures if item["fixture_id"] == "V17-POS-020"
    )
    mapping = migration["successful_mappings"][
        legacy_mapping_case["input"]["legacy_value_state"]
    ]
    if mapping["value_origin"] != oracles["OR-V17-020"]["effective_value"][
        "canonical_origin"
    ]:
        raise Phase3MigrationError("fixed positive legacy oracle mismatch")

    unsupported_case = next(
        item for item in fixtures if item["fixture_id"] == "V17-NEG-023"
    )
    unsupported = migrate_legacy_resolution(
        _legacy(
            unsupported_case["input"]["legacy_value_state"],
            "stop_unresolved",
            None,
        ),
        profile="formal",
    )
    unsupported_oracle = oracles[unsupported_case["oracle_id"]]
    for field in (
        "resolution_status",
        "value_origin",
        "effective_value",
        "stop_code",
    ):
        if unsupported[field] != unsupported_oracle[field]:
            raise Phase3MigrationError(f"fixed negative legacy oracle mismatch: {field}")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase3MigrationError("Phase 3 completion record is not passed")
    for section in ("artifacts", "schemas"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase3MigrationError(
                    f"Phase 3 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase3_state_migration": "passed",
        "legacy_success_mapping_count": len(migration["successful_mappings"]),
        "fixed_oracle_comparison_count": 2,
        "canonical_writer_emits_value_state": False,
        "formal_model_assumed_rejected": True,
        "record_identity_invariant": "passed",
        "classification_identity_invariant": "passed",
        "runtime_full_population": "not_run",
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Validate the v17 Phase 3 production state-contract migration."
    )


def main() -> int:
    build_parser().parse_args()
    try:
        result = validate_phase3_state_migration()
    except (Phase3MigrationError, V17StateContractError, KeyError) as error:
        print(json.dumps({"phase3_state_migration": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
