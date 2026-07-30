"""Validate cross-field invariants in the governed SUMO network configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from traffic_simulation.network.approved_attribute_resolution_policy import (
    ApprovedPolicyError,
    validate_approved_policy,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/sumo_network.yml"
ALLOWED_STATES = {"eligible", "ineligible", "pending", "conditional", "not_applicable"}
GATE_ORDER = (
    "formal_build_input_ready",
    "formal_network_acceptance",
    "downstream_experiment_ready",
)
REQUIREMENT_FIELDS = {
    "gate",
    "policy",
    "implementation",
    "unit_validation",
    "xsd_validation",
    "runtime_validation",
    "real_data_validation",
    "eligibility",
}
TRACE_FIELDS = {
    "requirement_id",
    "component",
    "test_ids",
    "fixture_class",
    "implementation_state",
}
REQUIREMENT_PATTERN = re.compile(
    r"\b(?:SIM|ARC|RS|AC|PM|TLS|BLD|PA)-REQ-[0-9]{3}\b"
)
TEST_PATTERN = re.compile(
    r"\b(?:SIM|ARC|RS|AC|PM|TLS|BLD|PA)-TST-[0-9]{3}\b"
)
FAILURE_PATTERN = re.compile(r"\b(?:RS|AC|PM|TLS|BLD|PA)[0-9]{3}\b")
UNRESOLVED_MARKER_PATTERN = re.compile(r"\b(?:TBD|TODO|FIXME)\b", re.IGNORECASE)
EXPECTED_FAILURE_CODES = {
    *(f"RS{number:03d}" for number in range(1, 15)),
    *(f"AC{number:03d}" for number in range(1, 11)),
    *(f"PM{number:03d}" for number in range(1, 29)),
    *(f"TLS{number:03d}" for number in range(1, 11)),
    *(f"BLD{number:03d}" for number in range(1, 15)),
    *(f"PA{number:03d}" for number in range(1, 16)),
}


class ConfigurationError(ValueError):
    """Raised when the governed configuration is internally inconsistent."""


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConfigurationError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.load(handle, Loader=UniqueKeyLoader)
    if not isinstance(config, dict):
        raise ConfigurationError("configuration root must be a mapping")
    return config


def load_unique_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.load(handle, Loader=UniqueKeyLoader)
    if not isinstance(value, dict):
        raise ConfigurationError(f"YAML root must be a mapping: {path}")
    return value


def validate_traceability(
    config: dict[str, Any], registry: dict[str, Any], normative_texts: list[str]
) -> None:
    if registry.get("schema_version") != 1:
        raise ConfigurationError("traceability schema_version must be 1")
    if registry.get("config_id") != config["config_id"]:
        raise ConfigurationError("traceability config_id is out of sync")
    rows = registry.get("requirements")
    if not isinstance(rows, list) or not rows:
        raise ConfigurationError("traceability requirements must be a nonempty list")

    requirement_ids: list[str] = []
    registered_test_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != TRACE_FIELDS:
            raise ConfigurationError("invalid traceability row schema")
        requirement_id = row["requirement_id"]
        if REQUIREMENT_PATTERN.fullmatch(requirement_id) is None:
            raise ConfigurationError(f"invalid requirement ID: {requirement_id}")
        test_ids = row["test_ids"]
        if not isinstance(test_ids, list) or not test_ids:
            raise ConfigurationError(f"{requirement_id} has no test ID")
        if any(TEST_PATTERN.fullmatch(test_id) is None for test_id in test_ids):
            raise ConfigurationError(f"{requirement_id} has an invalid test ID")
        requirement_ids.append(requirement_id)
        registered_test_ids.update(test_ids)
    if len(requirement_ids) != len(set(requirement_ids)):
        raise ConfigurationError("traceability contains duplicate requirement IDs")

    text = "\n".join(normative_texts)
    documented_requirements = set(REQUIREMENT_PATTERN.findall(text))
    documented_tests = set(TEST_PATTERN.findall(text))
    if set(requirement_ids) != documented_requirements:
        raise ConfigurationError("normative requirements and traceability registry differ")
    if not registered_test_ids <= documented_tests:
        raise ConfigurationError("traceability references undocumented test IDs")


def validate_failure_taxonomy(
    taxonomy_text: str, fixture_text: str, normative_texts: list[str]
) -> None:
    taxonomy_codes = set(FAILURE_PATTERN.findall(taxonomy_text))
    if taxonomy_codes != EXPECTED_FAILURE_CODES:
        raise ConfigurationError("failure taxonomy is incomplete or has unknown codes")
    referenced_codes = set(FAILURE_PATTERN.findall("\n".join(normative_texts)))
    if not referenced_codes <= taxonomy_codes:
        raise ConfigurationError("normative specification references an unknown failure code")
    if "<failure-code>-NEG-001" not in fixture_text:
        raise ConfigurationError("negative fixture identity convention is missing")


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != 2:
        raise ConfigurationError("schema_version must be 2")
    version = config.get("config_version")
    if config.get("config_id") != f"ota_ward_sumo_network_v{version}":
        raise ConfigurationError("config_id and config_version do not match")

    schema_path = REPOSITORY_ROOT / str(config.get("config_schema"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ConfigurationError("unsupported or missing JSON Schema declaration")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise ConfigurationError("invalid governed configuration schema") from error
    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=str)
    if errors:
        raise ConfigurationError(
            f"configuration does not satisfy its JSON Schema: {errors[0].message}"
        )

    schema_ids: set[str] = set()
    for name, relative_path in config["artifact_schema_registry"].items():
        artifact_schema = json.loads(
            (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        )
        if artifact_schema.get("$schema") != (
            "https://json-schema.org/draft/2020-12/schema"
        ):
            raise ConfigurationError(f"{name} has an invalid JSON Schema declaration")
        try:
            Draft202012Validator.check_schema(artifact_schema)
        except SchemaError as error:
            raise ConfigurationError(f"{name} is not a valid JSON Schema") from error
        schema_id = artifact_schema.get("$id")
        if not schema_id or schema_id in schema_ids:
            raise ConfigurationError(f"{name} has a missing or duplicate schema ID")
        schema_ids.add(schema_id)

    normative_texts: list[str] = []
    specification_texts: dict[str, str] = {}
    for name, relative_path in config["normative_specifications"].items():
        text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        if UNRESOLVED_MARKER_PATTERN.search(text):
            raise ConfigurationError(f"{name} contains an unresolved marker")
        specification_texts[name] = text
        normative_texts.append(text)
    trace_path = REPOSITORY_ROOT / config["policy_documents"][
        "requirements_traceability"
    ]
    validate_traceability(config, load_unique_yaml(trace_path), normative_texts)
    validate_failure_taxonomy(
        specification_texts["failure_taxonomy"],
        specification_texts["fixtures"],
        normative_texts,
    )

    status = config["status"]
    if set(status["eligibility_allowed_states"]) != ALLOWED_STATES:
        raise ConfigurationError("eligibility_allowed_states is not the governed enum")
    matrix = status["requirement_matrix"]
    gates = status["readiness_gates"]
    if tuple(gates) != GATE_ORDER:
        raise ConfigurationError("readiness gates must be declared in dependency order")
    if "requires_gate" in gates["formal_build_input_ready"]:
        raise ConfigurationError("formal_build_input_ready cannot depend on another gate")
    if gates["formal_network_acceptance"].get("requires_gate") != GATE_ORDER[0]:
        raise ConfigurationError("formal_network_acceptance has an invalid dependency")
    if gates["downstream_experiment_ready"].get("requires_gate") != GATE_ORDER[1]:
        raise ConfigurationError("downstream_experiment_ready has an invalid dependency")

    assigned: list[str] = []
    prior_gate_satisfied = True
    for gate_name, gate in gates.items():
        for requirement_name in gate["requires"]:
            if requirement_name not in matrix:
                raise ConfigurationError(
                    f"{gate_name} references unknown requirement {requirement_name}"
                )
            if matrix[requirement_name]["gate"] != gate_name:
                raise ConfigurationError(
                    f"{requirement_name} has inconsistent gate assignment"
                )
            assigned.append(requirement_name)
        expected_satisfied = prior_gate_satisfied and all(
            matrix[name]["eligibility"]["eligible"] for name in gate["requires"]
        )
        if gate.get("satisfied") is not expected_satisfied:
            raise ConfigurationError(f"{gate_name}.satisfied does not match its requirements")
        prior_gate_satisfied = gate["satisfied"]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(matrix):
        raise ConfigurationError("readiness gates must partition the requirement matrix")

    for name, requirement in matrix.items():
        if set(requirement) != REQUIREMENT_FIELDS:
            raise ConfigurationError(f"{name} has an invalid requirement-state schema")
        eligibility = requirement["eligibility"]
        if not isinstance(eligibility.get("eligible"), bool):
            raise ConfigurationError(f"{name}.eligibility.eligible must be boolean")
        state = eligibility.get("state")
        if state not in ALLOWED_STATES:
            raise ConfigurationError(f"{name} has unknown eligibility state {state}")
        if eligibility["eligible"] != (state == "eligible"):
            raise ConfigurationError(f"{name} eligibility boolean and state disagree")
        if not eligibility.get("reason"):
            raise ConfigurationError(f"{name} eligibility reason is required")

    top_level_gate_states = {
        "formal_build_input_ready": gates["formal_build_input_ready"]["satisfied"],
        "formal_network_accepted": gates["formal_network_acceptance"]["satisfied"],
        "downstream_experiment_ready": gates["downstream_experiment_ready"][
            "satisfied"
        ],
    }
    for status_name, expected in top_level_gate_states.items():
        if status.get(status_name) is not expected:
            raise ConfigurationError(f"status.{status_name} disagrees with readiness gate")

    if config["access_resolution"]["allow_permission_placeholder"] is not False:
        raise ConfigurationError("permission placeholders are prohibited")
    if config["netconvert"]["common_options"]["geometry.remove"] is not False:
        raise ConfigurationError("geometry.remove must be false for governed provenance")
    if set(config["provenance"]["distinguish_value_classes"]) != set(
        config["attribute_resolution"]["value_states"]
    ):
        raise ConfigurationError("resolver and final provenance states must match")
    materialization = config["permission_materialization"]
    if materialization["edge_provenance_artifact"][
        "coordinate_matching_in_formal_profile"
    ] != "prohibited":
        raise ConfigurationError("formal edge mapping must use exact lineage")
    if materialization["signal_structure_handoff"][
        "tls_connection_assignment_location"
    ] != "tllogic_file_connection_elements":
        raise ConfigurationError("TLS assignment must be governed in the tllogic file")
    if materialization["expectation_artifact"]["schema_version"] != 2:
        raise ConfigurationError("permission expectation schema version must be 2")

    config_id = config["config_id"]
    current_spec = REPOSITORY_ROOT / config["policy_documents"]["current_specification"]
    if f"Configuration: `{config_id}`" not in current_spec.read_text(encoding="utf-8"):
        raise ConfigurationError("current specification config_id is out of sync")
    change_log = REPOSITORY_ROOT / config["policy_documents"]["change_log"]
    latest_change = change_log.read_text(encoding="utf-8").rsplit("\n### ", 1)[-1]
    if config_id not in latest_change:
        next_policy = config.get("approved_next_configuration_policy")
        if not isinstance(next_policy, dict):
            raise ConfigurationError("latest change-log section config_id is out of sync")
        required_next_policy_fields = {
            "policy_id",
            "policy",
            "effective_from_config_version",
            "policy_status",
            "formal_build_ready",
            "v16_artifact_treatment",
        }
        if not required_next_policy_fields.issubset(next_policy):
            raise ConfigurationError(
                "approved next configuration policy metadata is incomplete"
            )
        if (
            next_policy["effective_from_config_version"]
            != config["config_version"] + 1
        ):
            raise ConfigurationError(
                "approved next configuration policy must target the next version"
            )
        if next_policy["policy_status"] != "fixed":
            raise ConfigurationError(
                "approved next configuration policy must have fixed status"
            )
        if next_policy["formal_build_ready"] is not False:
            raise ConfigurationError(
                "approved next configuration policy cannot claim formal build readiness"
            )
        if (
            next_policy["v16_artifact_treatment"]
            != "immutable_historical_evidence_not_relabelled_as_v17"
        ):
            raise ConfigurationError(
                "approved next configuration policy must preserve v16 artifacts"
            )
        policy_path = REPOSITORY_ROOT / next_policy["policy"]
        if not policy_path.is_file():
            raise ConfigurationError(
                "approved next configuration policy file does not exist"
            )
        try:
            policy = validate_approved_policy(policy_path)
        except (ApprovedPolicyError, yaml.YAMLError, ValidationError) as error:
            raise ConfigurationError(
                "approved next configuration policy validation failed"
            ) from error
        if policy.get("policy_id") != next_policy["policy_id"]:
            raise ConfigurationError(
                "approved next configuration policy_id is out of sync"
            )
        if (
            policy["effective_configuration"]["from"]
            != next_policy["effective_from_config_version"]
        ):
            raise ConfigurationError(
                "approved next configuration policy effective version is out of sync"
            )
        for field in (
            "policy_status",
            "implementation_status",
            "runtime_validation_status",
            "formal_build_ready",
        ):
            if policy[field] != next_policy[field]:
                raise ConfigurationError(
                    f"approved next configuration policy {field} is out of sync"
                )
        if next_policy["policy_id"] not in latest_change:
            raise ConfigurationError(
                "latest change-log section is not registered as current or next policy"
            )


def validate_manifest_identity(config: dict[str, Any], manifest: dict[str, Any]) -> None:
    for field in ("config_id", "config_version"):
        if manifest.get(field) != config[field]:
            raise ConfigurationError(f"manifest {field} is out of sync")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    validate_config(config)
    if args.manifest:
        validate_manifest_identity(
            config, json.loads(args.manifest.read_text(encoding="utf-8"))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
