"""Validate cross-field invariants in the governed SUMO network configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


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

    config_id = config["config_id"]
    current_spec = REPOSITORY_ROOT / config["policy_documents"]["current_specification"]
    if f"Configuration: `{config_id}`" not in current_spec.read_text(encoding="utf-8"):
        raise ConfigurationError("current specification config_id is out of sync")
    change_log = REPOSITORY_ROOT / config["policy_documents"]["change_log"]
    latest_change = change_log.read_text(encoding="utf-8").rsplit("\n### ", 1)[-1]
    if config_id not in latest_change:
        raise ConfigurationError("latest change-log section config_id is out of sync")


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
