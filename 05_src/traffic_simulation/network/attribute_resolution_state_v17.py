from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


MIGRATION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/legacy_state_migration_v17.yml"
)
MIGRATION_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "legacy_state_migration_v17.schema.json"
)
RECORD_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "attribute_resolution_record_v17.schema.json"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
CONFIGURATION_ID = "ota_ward_sumo_network_v17"


class V17StateContractError(ValueError):
    pass


class LegacyExclusionRequired(V17StateContractError):
    """The legacy row belongs in an exclusion manifest, not a v17 record."""


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise V17StateContractError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise V17StateContractError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate)
    if not isinstance(value, dict):
        raise V17StateContractError(f"JSON root must be an object: {path}")
    return value


def _load_schema(path: Path) -> dict[str, Any]:
    return _load_json(path)


def validate_migration_registry() -> dict[str, Any]:
    migration = _load_yaml(MIGRATION_PATH)
    schema = _load_schema(MIGRATION_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(migration)
    return migration


def migrate_legacy_resolution(
    legacy: Mapping[str, Any], *, profile: str
) -> dict[str, Any]:
    """Read one v16 resolution without allowing v17 to emit legacy fields."""

    if profile not in {"structural", "formal"}:
        raise V17StateContractError(f"unknown profile: {profile}")
    migration = validate_migration_registry()
    legacy_state = legacy.get("value_state")
    legacy_action = legacy.get("resolution_action")
    if not isinstance(legacy_state, str):
        legacy_state = "<missing>"

    if legacy_state == migration["excluded_mapping"]["source_state"]:
        raise LegacyExclusionRequired(
            "legacy excluded rows must be routed to the exclusion manifest"
        )

    successful = migration["successful_mappings"].get(legacy_state)
    audit = {
        "legacy_state": legacy_state,
        "legacy_action": legacy_action,
        "legacy_stop_failure_codes": copy.deepcopy(
            legacy.get("stop_failure_codes", [])
        ),
    }
    if successful is not None:
        if legacy_action != successful["required_action"]:
            raise V17StateContractError(
                f"legacy action/state mismatch: {legacy_action}/{legacy_state}"
            )
        value = copy.deepcopy(legacy.get("resolved_value"))
        if value is None:
            raise V17StateContractError(
                f"resolved legacy state has no value: {legacy_state}"
            )
        origin = successful["value_origin"]
        if origin == "model_assumed" and profile == "formal":
            raise V17StateContractError(
                "formal migration rejects structural model assumptions"
            )
        rule_id = legacy.get("resolution_rule_id")
        selected_evidence_id = legacy.get("selected_evidence_id")
        rule_ids = [rule_id] if isinstance(rule_id, str) else []
        evidence_ids = (
            [selected_evidence_id]
            if isinstance(selected_evidence_id, str)
            else []
        )
        assumption_ids: list[str] = []
        if origin == "model_assumed":
            if not isinstance(rule_id, str):
                raise V17StateContractError(
                    "structural placeholder requires an assumption ID"
                )
            assumption_ids = [rule_id]
            rule_ids = []
        return {
            "resolution_status": "resolved",
            "value_origin": origin,
            "effective_value": value,
            "rule_ids": rule_ids,
            "evidence_ids": evidence_ids,
            "assumption_ids": assumption_ids,
            "stop_code": None,
            "review_required": False,
            "migration_audit": audit,
        }

    return {
        "resolution_status": migration["unknown_mapping"]["resolution_status"],
        "value_origin": None,
        "effective_value": None,
        "rule_ids": [],
        "evidence_ids": [],
        "assumption_ids": [],
        "stop_code": migration["unknown_mapping"]["stop_code"],
        "review_required": legacy.get("review_status") == "review_required",
        "migration_audit": audit,
    }


def _record_key(identity: Mapping[str, Any], *, profile: str) -> dict[str, Any]:
    required = {
        "population_version",
        "source_way_id",
        "directed_segment_id",
        "source_direction",
        "lane_position",
        "vehicle_class",
        "attribute_name",
        "scenario_context_id",
    }
    missing = sorted(required - set(identity))
    if missing:
        raise V17StateContractError(f"record identity fields missing: {missing}")
    return {
        "configuration_id": CONFIGURATION_ID,
        "population_version": identity["population_version"],
        "profile": profile,
        "source_way_id": identity["source_way_id"],
        "directed_segment_id": identity["directed_segment_id"],
        "source_direction": identity["source_direction"],
        "lane_position": identity["lane_position"],
        "vehicle_class": identity["vehicle_class"],
        "attribute_name": identity["attribute_name"],
        "scenario_context_id": identity["scenario_context_id"],
    }


def canonical_record_id(record_key: Mapping[str, Any]) -> str:
    """Hash the fixed v17 identity domain in RFC 8785-compatible form.

    The identity contract contains fixed ASCII keys and JSON strings, integers,
    booleans, and nulls only. Floats are rejected, avoiding number-format
    differences between the standard encoder and JCS.
    """

    def reject_float(value: Any) -> None:
        if isinstance(value, float):
            raise V17StateContractError("floating-point identity values are prohibited")
        if isinstance(value, Mapping):
            for item in value.values():
                reject_float(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                reject_float(item)

    reject_float(record_key)
    payload = json.dumps(
        dict(record_key),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _registered_contract() -> tuple[set[str], set[str], set[str], set[str]]:
    registries = _load_yaml(REGISTRY_PATH)
    statuses = {
        item["value"] for item in registries["state_origin"]["resolution_status"]
    }
    origins = {
        item["value"] for item in registries["state_origin"]["value_origin"]
    }
    formal_origins = {
        item["value"]
        for item in registries["state_origin"]["value_origin"]
        if item["formal_eligible"]
    }
    stop_codes = {item["stop_code"] for item in registries["stop_codes"]}
    return statuses, origins, formal_origins, stop_codes


def validate_v17_record(
    record: Mapping[str, Any], *, expected_classification_record_id: str | None = None
) -> None:
    schema = _load_schema(RECORD_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        pointer = "/".join(str(item) for item in first.absolute_path)
        raise V17StateContractError(
            f"record Schema violation at {pointer or '<root>'}: {first.message}"
        )
    if "value_state" in record:
        raise V17StateContractError("v17 writer emitted value_state")

    statuses, origins, formal_origins, stop_codes = _registered_contract()
    if record["resolution_status"] not in statuses:
        raise V17StateContractError("unregistered resolution status")
    origin = record["value_origin"]
    if origin is not None and origin not in origins:
        raise V17StateContractError("unregistered value origin")
    stop_code = record["stop_code"]
    if stop_code is not None and stop_code not in stop_codes:
        raise V17StateContractError("unregistered stop code")
    if record["profile"] == "formal":
        if origin is not None and origin not in formal_origins:
            raise V17StateContractError("formal record uses an ineligible origin")
        if record["assumption_ids"]:
            raise V17StateContractError("formal record contains an assumption ID")

    if record["resolution_status"] == "resolved" and not any(
        (
            record["source_observations"],
            record["rule_ids"],
            record["evidence_ids"],
            record["assumption_ids"],
        )
    ):
        raise V17StateContractError("resolved record has no explanatory reference")

    key = _record_key(record, profile=record["profile"])
    if canonical_record_id(key) != record["record_id"]:
        raise V17StateContractError("record_id does not match the record key")
    if (
        expected_classification_record_id is not None
        and record["classification_record_id"]
        != expected_classification_record_id
    ):
        raise V17StateContractError("classification_record_id changed during resolution")


def build_v17_record(
    *,
    identity: Mapping[str, Any],
    profile: str,
    classification_record_id: str,
    source_observations: Sequence[Mapping[str, Any]],
    resolution: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    key = _record_key(identity, profile=profile)
    migration_audit = copy.deepcopy(resolution.get("migration_audit"))
    combined_provenance = copy.deepcopy(dict(provenance))
    if migration_audit is not None:
        combined_provenance["legacy_migration"] = migration_audit
    record = {
        "schema_version": 17,
        **key,
        "record_id": canonical_record_id(key),
        "classification_record_id": classification_record_id,
        "source_observations": copy.deepcopy(list(source_observations)),
        "resolution_status": resolution["resolution_status"],
        "value_origin": resolution["value_origin"],
        "effective_value": copy.deepcopy(resolution["effective_value"]),
        "rule_ids": copy.deepcopy(list(resolution.get("rule_ids", []))),
        "evidence_ids": copy.deepcopy(list(resolution.get("evidence_ids", []))),
        "assumption_ids": copy.deepcopy(list(resolution.get("assumption_ids", []))),
        "stop_code": resolution["stop_code"],
        "review_required": bool(resolution.get("review_required", False)),
        "provenance": combined_provenance,
    }
    if "conflicting_candidates" in resolution:
        record["conflicting_candidates"] = copy.deepcopy(
            resolution["conflicting_candidates"]
        )
    validate_v17_record(
        record, expected_classification_record_id=classification_record_id
    )
    return record


def migrate_legacy_record(envelope: Mapping[str, Any]) -> dict[str, Any]:
    profile = envelope.get("profile")
    if not isinstance(profile, str):
        raise V17StateContractError("profile is required")
    classification_record_id = envelope.get("classification_record_id")
    if not isinstance(classification_record_id, str):
        raise V17StateContractError("classification_record_id is required")
    legacy = envelope.get("legacy_resolution")
    if not isinstance(legacy, Mapping):
        raise V17StateContractError("legacy_resolution must be an object")
    resolution = migrate_legacy_resolution(legacy, profile=profile)
    return build_v17_record(
        identity=envelope.get("identity", {}),
        profile=profile,
        classification_record_id=classification_record_id,
        source_observations=envelope.get("source_observations", []),
        resolution=resolution,
        provenance=envelope.get("provenance", {}),
    )


def write_v17_record_atomic(record: Mapping[str, Any], output_path: Path) -> None:
    validate_v17_record(record)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite v17 record: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, output_path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate one legacy resolution envelope to a v17 record."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    envelope = _load_json(args.input)
    record = migrate_legacy_record(envelope)
    write_v17_record_atomic(record, args.output)
    print(
        json.dumps(
            {
                "record_id": record["record_id"],
                "classification_record_id": record["classification_record_id"],
                "resolution_status": record["resolution_status"],
                "value_origin": record["value_origin"],
                "valid": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
