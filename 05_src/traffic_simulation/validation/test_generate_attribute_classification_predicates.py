from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterator

import pytest
import yaml

from traffic_simulation.network.generate_attribute_classification_predicates import (
    EXTERNAL_PREDICATES,
    OSM_DERIVED_PREDICATES,
    PredicateGenerationError,
    file_ref,
    generate_predicate_artifact,
    write_artifact_atomic,
)
from traffic_simulation.network.validate_attribute_classification import (
    validate_predicate_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
FIXTURE_OSM = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "predicate_generator/relation-closed.osm.xml"
)


@pytest.fixture
def governed_workspace() -> Iterator[Path]:
    temporary = Path(
        tempfile.mkdtemp(prefix=".predicate-generator-test-", dir=REPOSITORY_ROOT)
    )
    try:
        yield temporary
    finally:
        shutil.rmtree(temporary)


def write_json(path: Path, value: Any) -> Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def make_registry(
    root: Path,
    *,
    accepted: bool = True,
    scope: str = "synthetic_fixture",
    include_way_104: bool = True,
    unknown_external_way: bool = False,
    override: bool = False,
) -> Path:
    osm_path = root / "relation-closed.osm.xml"
    shutil.copyfile(FIXTURE_OSM, osm_path)
    role_source = write_json(root / "role-source.json", {"reviewed": True})
    external_source = write_json(
        root / "external-predicates.json", {"reviewed": True}
    )
    override_source = write_json(root / "predicate-overrides.json", {"reviewed": True})
    acceptance_source = write_json(
        root / "population-acceptance.json", {"accepted": accepted}
    )
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    role_decisions = [
        {
            "osm_way_id": "101",
            "subgraph_role": "final",
            "topology_support_reason": None,
            "source_record_locator": "roles/101",
            "derivation_rule_id": "PRED-ROLE-REVIEW-001",
        },
        {
            "osm_way_id": "102",
            "subgraph_role": "final",
            "topology_support_reason": None,
            "source_record_locator": "roles/102",
            "derivation_rule_id": "PRED-ROLE-REVIEW-001",
        },
        {
            "osm_way_id": "103",
            "subgraph_role": "topology_support",
            "topology_support_reason": "Preserves relation-closed topology.",
            "source_record_locator": "roles/103",
            "derivation_rule_id": "PRED-ROLE-REVIEW-001",
        },
    ]
    if include_way_104:
        role_decisions.append(
            {
                "osm_way_id": "104",
                "subgraph_role": "excluded",
                "topology_support_reason": None,
                "source_record_locator": "roles/104",
                "derivation_rule_id": "PRED-ROLE-REVIEW-001",
            }
        )
    true_ids = {
        "is_calibration_segment": ["101"],
        "is_validation_segment": ["102"],
        "is_major_junction_approach": ["101"],
        "is_accepted_delivery_route": ["101", "102", "103"],
        "is_sensitivity_elevated": ["102"],
    }
    if unknown_external_way:
        true_ids["is_calibration_segment"].append("999")
    external_sources = {
        predicate: {
            "source_artifact_type": "reviewed_external_predicate_source",
            "source": file_ref(external_source),
            "derivation_rule_id": f"PRED-EXTERNAL-{index:03d}",
            "true_way_ids": true_ids[predicate],
            "false_scope": "all_other_population_ways",
        }
        for index, predicate in enumerate(EXTERNAL_PREDICATES, start=1)
    }
    overrides = []
    if override:
        overrides.append(
            {
                "osm_way_id": "102",
                "predicate": "is_bridge",
                "value": True,
                "source_artifact_type": "reviewed_predicate_override",
                "source": file_ref(override_source),
                "source_record_locator": "overrides/102/is_bridge",
                "derivation_rule_id": "PRED-OVERRIDE-REVIEW-001",
            }
        )
    registry = {
        "artifact_type": "attribute_classification_predicate_source_registry",
        "schema_version": 1,
        "config_id": config["config_id"],
        "config_version": config["config_version"],
        "run_id": "predicate-generator-fixture",
        "population_acceptance": {
            "scope": scope,
            "accepted": accepted,
            "acceptance_artifact": (
                file_ref(acceptance_source) if scope == "registered_real_data" else None
            ),
        },
        "relation_closed_osm": file_ref(osm_path),
        "role_source_artifact_type": "reviewed_subgraph_role_source",
        "role_source": file_ref(role_source),
        "role_decisions": role_decisions,
        "external_predicate_sources": external_sources,
        "predicate_overrides": overrides,
    }
    return write_json(root / "predicate-source-registry.json", registry)


def generate(root: Path, registry_path: Path) -> dict[str, Any]:
    return generate_predicate_artifact(
        osm_path=root / "relation-closed.osm.xml",
        source_registry_path=registry_path,
        policy_path=CONFIG_PATH,
    )


def records_by_id(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["osm_way_id"]: record for record in artifact["records"]}


def test_generates_complete_traceable_predicates(
    governed_workspace: Path,
) -> None:
    registry_path = make_registry(governed_workspace)
    artifact = generate(governed_workspace, registry_path)
    records = records_by_id(artifact)

    assert artifact["population_way_count"] == 4
    assert [record["osm_way_id"] for record in artifact["records"]] == [
        "101",
        "102",
        "103",
        "104",
    ]
    assert set(records["101"]["predicates"]) == {
        *EXTERNAL_PREDICATES,
        *OSM_DERIVED_PREDICATES,
    }
    assert records["103"]["subgraph_role"] == "topology_support"
    assert records["104"]["subgraph_role"] == "excluded"
    assert records["101"]["predicates"]["is_bridge"]["value"] is True
    assert records["101"]["predicates"]["has_conflicting_lane_semantics"]["value"] is False
    assert records["102"]["predicates"]["is_tunnel"]["value"] is True
    assert records["102"]["predicates"]["has_reversible_lane_semantics"]["value"] is True
    assert records["102"]["predicates"]["has_tidal_flow_semantics"]["value"] is True
    assert records["102"]["predicates"]["has_conflicting_lane_semantics"]["value"] is True
    assert records["104"]["predicates"]["has_reversible_lane_semantics"]["value"] is False
    assert records["104"]["predicates"]["has_tidal_flow_semantics"]["value"] is False
    false_evidence = records["104"]["predicates"]["is_calibration_segment"]
    assert false_evidence["value"] is False
    assert false_evidence["source_record_locator"].startswith(
        "false_scope/all_other_population_ways/"
    )
    assert artifact["source_registry"] == file_ref(registry_path)
    assert validate_predicate_artifact(artifact).valid


def test_reviewed_override_replaces_osm_derivation(
    governed_workspace: Path,
) -> None:
    registry_path = make_registry(governed_workspace, override=True)
    artifact = generate(governed_workspace, registry_path)
    bridge = records_by_id(artifact)["102"]["predicates"]["is_bridge"]

    assert bridge["value"] is True
    assert bridge["source_artifact_type"] == "reviewed_predicate_override"
    assert bridge["derivation_rule_id"] == "PRED-OVERRIDE-REVIEW-001"


@pytest.mark.parametrize(
    ("registry_change", "expected_code"),
    [
        ({"accepted": False}, "PGEN001"),
        ({"include_way_104": False}, "PGEN004"),
        ({"unknown_external_way": True}, "PGEN005"),
    ],
)
def test_invalid_governance_inputs_stop_generation(
    governed_workspace: Path,
    registry_change: dict[str, Any],
    expected_code: str,
) -> None:
    registry_path = make_registry(governed_workspace, **registry_change)

    with pytest.raises(PredicateGenerationError) as error:
        generate(governed_workspace, registry_path)

    assert error.value.error["code"] == expected_code


def test_registered_v15_real_data_is_rejected(
    governed_workspace: Path,
) -> None:
    registry_path = make_registry(
        governed_workspace, scope="registered_real_data"
    )

    with pytest.raises(PredicateGenerationError) as error:
        generate(governed_workspace, registry_path)

    assert error.value.error["code"] == "PGEN008"
    assert "minimum accepted population contract" in error.value.error["message"]


def test_source_hash_mismatch_stops_generation(
    governed_workspace: Path,
) -> None:
    registry_path = make_registry(governed_workspace)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["role_source"]["sha256"] = "0" * 64
    write_json(registry_path, registry)

    with pytest.raises(PredicateGenerationError) as error:
        generate(governed_workspace, registry_path)

    assert error.value.error["code"] == "PGEN002"


def test_generation_is_deterministic(governed_workspace: Path) -> None:
    registry_path = make_registry(governed_workspace)

    first = generate(governed_workspace, registry_path)
    second = generate(governed_workspace, registry_path)

    assert first == second


def test_atomic_writer_refuses_overwrite(governed_workspace: Path) -> None:
    registry_path = make_registry(governed_workspace)
    artifact = generate(governed_workspace, registry_path)
    output = governed_workspace / "attribute-classification-predicates.json"
    write_artifact_atomic(artifact, output)
    original = output.read_bytes()

    with pytest.raises(PredicateGenerationError) as error:
        write_artifact_atomic(copy.deepcopy(artifact), output)

    assert error.value.error["code"] == "PGEN010"
    assert output.read_bytes() == original
