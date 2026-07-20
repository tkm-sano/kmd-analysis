"""Test fail-closed validation of the governed SUMO network configuration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from traffic_simulation.network import validate_sumo_network_config as validator


def governed_config() -> dict[str, object]:
    return validator.load_config()


def test_current_governed_config_passes_cross_field_validation() -> None:
    validator.validate_config(governed_config())


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yml"
    path.write_text("schema_version: 2\nschema_version: 2\n", encoding="utf-8")

    with pytest.raises(validator.ConfigurationError, match="duplicate YAML key"):
        validator.load_config(path)


def test_truthy_string_cannot_replace_boolean_eligibility() -> None:
    config = deepcopy(governed_config())
    config["status"]["requirement_matrix"]["typemap_xml"]["eligibility"][
        "eligible"
    ] = "pending"

    with pytest.raises(validator.ConfigurationError, match="must be boolean"):
        validator.validate_config(config)


def test_gate_dependency_cycle_is_rejected() -> None:
    config = deepcopy(governed_config())
    config["status"]["readiness_gates"]["formal_build_input_ready"][
        "requires_gate"
    ] = "formal_network_acceptance"

    with pytest.raises(validator.ConfigurationError, match="cannot depend"):
        validator.validate_config(config)


def test_requirement_must_belong_to_exactly_one_declared_gate() -> None:
    config = deepcopy(governed_config())
    config["status"]["readiness_gates"]["formal_build_input_ready"]["requires"].append(
        "formal_network"
    )

    with pytest.raises(validator.ConfigurationError, match="inconsistent gate assignment"):
        validator.validate_config(config)


def test_manifest_identity_must_match_governed_configuration() -> None:
    config = governed_config()
    validator.validate_manifest_identity(
        config,
        {"config_id": config["config_id"], "config_version": config["config_version"]},
    )

    with pytest.raises(validator.ConfigurationError, match="config_id is out of sync"):
        validator.validate_manifest_identity(
            config,
            {"config_id": "ota_ward_sumo_network_v12", "config_version": 13},
        )
