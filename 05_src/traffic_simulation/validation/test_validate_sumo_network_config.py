"""Test fail-closed validation of the governed SUMO network configuration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from traffic_simulation.network import validate_sumo_network_config as validator


def governed_config() -> dict[str, object]:
    return validator.load_config()


def governed_traceability(
    config: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    registry = validator.load_unique_yaml(
        validator.REPOSITORY_ROOT
        / config["policy_documents"]["requirements_traceability"]
    )
    texts = [
        (validator.REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for path in config["normative_specifications"].values()
    ]
    return registry, texts


def test_current_governed_config_passes_cross_field_validation() -> None:
    validator.validate_config(governed_config())


def test_governed_configuration_schema_is_enforced() -> None:
    config = deepcopy(governed_config())
    del config["normative_specifications"]

    with pytest.raises(validator.ConfigurationError, match="does not satisfy"):
        validator.validate_config(config)


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

    with pytest.raises(validator.ConfigurationError, match="type 'boolean'"):
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
            {"config_id": "ota_ward_sumo_network_v13", "config_version": 14},
        )


def test_all_normative_requirements_have_registered_tests() -> None:
    config = governed_config()
    registry, texts = governed_traceability(config)

    validator.validate_traceability(config, registry, texts)
    assert len(registry["requirements"]) == 81


def test_missing_traceability_requirement_is_rejected() -> None:
    config = governed_config()
    registry, texts = governed_traceability(config)
    registry["requirements"].pop()

    with pytest.raises(validator.ConfigurationError, match="registry differ"):
        validator.validate_traceability(config, registry, texts)


def test_requirement_without_test_id_is_rejected() -> None:
    config = governed_config()
    registry, texts = governed_traceability(config)
    registry["requirements"][0]["test_ids"] = []

    with pytest.raises(validator.ConfigurationError, match="has no test ID"):
        validator.validate_traceability(config, registry, texts)


def test_failure_taxonomy_is_complete_and_fixture_identified() -> None:
    config = governed_config()
    texts = {
        name: (validator.REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for name, path in config["normative_specifications"].items()
    }

    validator.validate_failure_taxonomy(
        texts["failure_taxonomy"], texts["fixtures"], list(texts.values())
    )
    assert len(validator.EXPECTED_FAILURE_CODES) == 91


def test_missing_failure_code_is_rejected() -> None:
    config = governed_config()
    texts = {
        name: (validator.REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for name, path in config["normative_specifications"].items()
    }
    taxonomy = texts["failure_taxonomy"].replace("| PA015 |", "| PA999 |")

    with pytest.raises(validator.ConfigurationError, match="taxonomy is incomplete"):
        validator.validate_failure_taxonomy(
            taxonomy, texts["fixtures"], list(texts.values())
        )
