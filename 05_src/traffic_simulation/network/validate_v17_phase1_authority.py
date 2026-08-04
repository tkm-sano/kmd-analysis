from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network_v17.yml"
)
POLICY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "approved_attribute_resolution_policy_v17.yml"
)
REGISTRY_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "attribute_resolution_registries_v17.schema.json"
)
INVARIANT_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "semantic_invariants_v17.schema.json"
)
COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase1_completion.yml"
)


class Phase1AuthorityError(ValueError):
    """Raised when the v17 Phase 1 authority is incomplete or inconsistent."""


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise Phase1AuthorityError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(value, dict):
        raise Phase1AuthorityError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise Phase1AuthorityError(f"duplicate JSON key: {key} in {path}")
            value[key] = item
        return value

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate)
    if not isinstance(value, dict):
        raise Phase1AuthorityError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate(schema_path: Path, instance: dict[str, Any]) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(item) for item in error.absolute_path) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise Phase1AuthorityError(f"{schema_path.name}: {details}")


def _repo_path(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    root = REPOSITORY_ROOT.resolve()
    if path != root and root not in path.parents:
        raise Phase1AuthorityError(f"path escapes repository: {relative_path}")
    if not path.is_file():
        raise Phase1AuthorityError(f"referenced file does not exist: {relative_path}")
    return path


def validate_phase1_authority(
    config_path: Path = CONFIG_PATH,
    policy_path: Path = POLICY_PATH,
) -> dict[str, Any]:
    config = _load_yaml(config_path)
    policy = _load_yaml(policy_path)

    _validate(_repo_path(config["schema"]), config)
    _validate(_repo_path(policy["schema"]), policy)

    for policy_reference in (
        "normative_specification",
        "phase1_configuration",
        "requirements_traceability",
        "semantic_invariants",
        "registry_bundle",
    ):
        _repo_path(policy[policy_reference])

    if config_path.resolve() == CONFIG_PATH.resolve() and policy[
        "phase1_configuration"
    ] != str(CONFIG_PATH.resolve().relative_to(REPOSITORY_ROOT.resolve())):
        raise Phase1AuthorityError("policy/configuration reference mismatch")
    if policy["policy_id"] != config["policy_id"]:
        raise Phase1AuthorityError("policy identity mismatch")
    if policy["normative_specification"] != config["normative_specification"]:
        raise Phase1AuthorityError("normative specification reference mismatch")

    registries = _load_yaml(_repo_path(config["registries"]["path"]))
    invariants = _load_yaml(_repo_path(config["semantic_invariants"]["path"]))
    _validate(REGISTRY_SCHEMA_PATH, registries)
    _validate(INVARIANT_SCHEMA_PATH, invariants)

    for reference, artifact in (
        (config["registries"], registries),
        (config["semantic_invariants"], invariants),
    ):
        artifact_path = _repo_path(reference["path"])
        if reference["sha256"] != _sha256(artifact_path):
            raise Phase1AuthorityError(f"SHA-256 mismatch: {reference['path']}")
        version = artifact.get("registry_version", artifact.get("version"))
        if reference["version"] != version:
            raise Phase1AuthorityError(f"version mismatch: {reference['path']}")

    schema_files: dict[str, Path] = {
        name: _repo_path(path) for name, path in config["schemas"].items()
    }
    for schema_path in schema_files.values():
        jsonschema.Draft202012Validator.check_schema(_load_json(schema_path))

    configured_status = config["resolution_contract"]["resolution_status"]
    registered_status = [
        item["value"] for item in registries["state_origin"]["resolution_status"]
    ]
    if configured_status != registered_status:
        raise Phase1AuthorityError("resolution_status enum mismatch")

    configured_origin = config["resolution_contract"]["value_origin"]
    registered_origin = [
        item["value"] for item in registries["state_origin"]["value_origin"]
    ]
    if configured_origin != registered_origin:
        raise Phase1AuthorityError("value_origin enum mismatch")

    resolution_schema = _load_json(schema_files["resolution_record"])
    schema_status = resolution_schema["properties"]["resolution_status"]["enum"]
    schema_origin = [
        value
        for value in resolution_schema["properties"]["value_origin"]["enum"]
        if value is not None
    ]
    if schema_status != configured_status or schema_origin != configured_origin:
        raise Phase1AuthorityError("record Schema enum mismatch")

    stop_codes = [item["stop_code"] for item in registries["stop_codes"]]
    if len(stop_codes) != len(set(stop_codes)):
        raise Phase1AuthorityError("duplicate stop code")
    required_stop_codes = {
        "LEGACY_STATE_MAPPING_UNSUPPORTED",
        "ONEWAY_VALUE_INVALID",
        "ONEWAY_VALUE_UNSUPPORTED",
        "ONEWAY_RULE_NOT_REGISTERED",
        "DIRECTED_SEGMENT_LINEAGE_INVALID",
        "RELATION_DIRECTED_MAPPING_MISSING",
        "RELATION_DIRECTED_MAPPING_AMBIGUOUS",
        "LANE_COUNT_INVALID",
        "LANE_COUNT_CONFLICT",
        "LANE_DIRECTIONAL_ALLOCATION_MISSING",
        "LANE_VECTOR_LENGTH_MISMATCH",
        "SPEED_VALUE_INVALID",
        "SPEED_VALUE_UNSUPPORTED",
        "SPEED_RULE_NOT_REGISTERED",
        "SPEED_CONDITIONAL_CONTEXT_MISSING",
        "SPEED_WITHIN_INTERVAL_CHANGE",
        "ACCESS_VALUE_INVALID",
        "ACCESS_VALUE_UNSUPPORTED",
        "ACCESS_VEHICLE_HIERARCHY_MISSING",
        "ACCESS_CONDITIONAL_SYNTAX_UNSUPPORTED",
        "ACCESS_CONTEXT_MISSING",
        "ACCESS_WITHIN_INTERVAL_CHANGE",
        "ACCESS_SPECIFICITY_CONFLICT",
        "ACCESS_PERMISSION_UNRESOLVED",
        "EVIDENCE_METHOD_NOT_APPROVED",
        "EVIDENCE_DONOR_INELIGIBLE",
        "EXCLUSION_RULE_UNREGISTERED",
        "UNREGISTERED_RULE",
        "UNREGISTERED_STATE",
        "UNREGISTERED_STOP_CODE",
    }
    if set(stop_codes) != required_stop_codes:
        missing = sorted(required_stop_codes - set(stop_codes))
        extra = sorted(set(stop_codes) - required_stop_codes)
        raise Phase1AuthorityError(
            f"stop-code registry mismatch; missing={missing}, extra={extra}"
        )

    invariant_items = invariants["invariants"]
    invariant_ids = [item["invariant_id"] for item in invariant_items]
    if len(invariant_ids) != len(set(invariant_ids)):
        raise Phase1AuthorityError("duplicate invariant ID")
    for item in invariant_items:
        stop_code = item.get("stop_code")
        if stop_code is not None and stop_code not in required_stop_codes:
            raise Phase1AuthorityError(
                f"unregistered invariant stop code: {item['invariant_id']}={stop_code}"
            )

    traceability_text = _repo_path(policy["requirements_traceability"]).read_text(
        encoding="utf-8"
    )
    missing_invariants = sorted(
        invariant_id
        for invariant_id in invariant_ids
        if invariant_id not in traceability_text
    )
    if missing_invariants:
        raise Phase1AuthorityError(
            f"invariants absent from traceability: {missing_invariants}"
        )

    specification = _repo_path(config["normative_specification"]).read_text(
        encoding="utf-8"
    )
    required_spec_tokens = (
        "resolution_status",
        "value_origin",
        "ds:{source_way_id}:{source_start_index}:{source_end_index}:{source_direction}",
        "ACCESS_SPECIFICITY_CONFLICT",
        "Attribute Resolution Acceptance",
        "Phase 14",
    )
    for token in required_spec_tokens:
        if token not in specification:
            raise Phase1AuthorityError(f"normative specification token missing: {token}")

    if config["status"] != "phase1_complete":
        raise Phase1AuthorityError("configuration is not marked phase1_complete")
    if config["formal_build_ready"] is not False:
        raise Phase1AuthorityError("Phase 1 must not claim formal build readiness")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase1AuthorityError("Phase 1 completion record is not passed")
    for name, reference in completion["artifacts"].items():
        artifact_path = _repo_path(reference["path"])
        if _sha256(artifact_path) != reference["sha256"]:
            raise Phase1AuthorityError(f"completion artifact hash mismatch: {name}")
    v16_reference = completion["v16_boundary"]
    if _sha256(_repo_path(v16_reference["configuration_path"])) != v16_reference[
        "sha256"
    ]:
        raise Phase1AuthorityError("v16 configuration hash mismatch")

    completion_schema_paths = {
        "access_rule_v17": schema_files["access_rule"],
        "attribute_resolution_acceptance_v17": schema_files["acceptance"],
        "attribute_resolution_record_v17": schema_files["resolution_record"],
        "attribute_resolution_registries_v17": REGISTRY_SCHEMA_PATH,
        "directed_segment_v17": schema_files["directed_segment"],
        "environment_build_manifest_v17": schema_files["environment_build_manifest"],
        "exclusion_manifest_v17": schema_files["exclusion_manifest"],
        "materialization_omission_v17": schema_files["materialization_omission"],
        "semantic_invariants_v17": INVARIANT_SCHEMA_PATH,
        "sumo_network_v17": _repo_path(config["schema"]),
        "governed_runtime_interval_context_v17": schema_files[
            "governed_runtime_interval_context"
        ],
        "holiday_calendar_v17": schema_files["holiday_calendar"],
        "warning_audit_v17": schema_files["warning_audit"],
        "approved_policy_index": _repo_path(policy["schema"]),
    }
    for name, schema_path in completion_schema_paths.items():
        if _sha256(schema_path) != completion["schemas"][name]:
            raise Phase1AuthorityError(f"completion Schema hash mismatch: {name}")

    return {
        "policy_id": policy["policy_id"],
        "configuration_id": config["configuration_id"],
        "configuration_status": config["status"],
        "schema_count": len(schema_files) + 4,
        "registry_stop_code_count": len(stop_codes),
        "semantic_invariant_count": len(invariant_ids),
        "phase1_authority": "passed",
        "runtime_validation": "not_run",
        "formal_build_ready": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the synchronized v17 Phase 1 authority package."
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = validate_phase1_authority(args.config, args.policy)
    except (Phase1AuthorityError, jsonschema.ValidationError, KeyError) as error:
        print(json.dumps({"phase1_authority": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
