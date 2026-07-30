from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterator

import pytest

from traffic_simulation.network.classify_attribute_criticality import (
    CriticalityClassificationError,
    classify_predicate_artifact,
)
from traffic_simulation.network.resolve_osm_attributes import (
    attach_resolution_without_overwriting_classification,
    load_classification_for_resolution,
)
from traffic_simulation.network.validate_attribute_classification import file_sha256
from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.validation.test_generate_attribute_classification_predicates import (
    generate,
    make_registry,
)


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/attribute_classification"
)
ORACLE_PATH = FIXTURE_ROOT / "oracles.json"
PINNED_ORACLE_SHA256 = (
    "98b6a007e4828e42570a17d9255bdd029295afddf6307d1a6f3f63f8bc96664a"
)


@pytest.fixture
def classifier_workspace() -> Iterator[Path]:
    path = Path(
        tempfile.mkdtemp(prefix=".criticality-classifier-test-", dir=REPOSITORY_ROOT)
    )
    try:
        yield path
    finally:
        shutil.rmtree(path)


def _write_json(path: Path, value: Any) -> Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def _predicate_artifact(
    workspace: Path,
    *,
    accepted_route: bool = False,
) -> Path:
    registry_path = make_registry(workspace)
    artifact = generate(workspace, registry_path)
    record = next(
        record for record in artifact["records"] if record["osm_way_id"] == "103"
    )
    record["predicates"]["is_accepted_delivery_route"]["value"] = accepted_route
    record["predicates"]["is_sensitivity_elevated"]["value"] = False
    artifact["records"] = [record]
    artifact["population_way_count"] = 1
    return _write_json(workspace / "predicates.json", artifact)


def _oracle_classifications(case_id: str) -> dict[str, dict[str, Any]]:
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    return {
        record["classification_record_id"]: record["classification"]
        for record in oracle["cases"][case_id]["records"]
    }


def _classifications(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        record["classification_record_id"]: record["classification"]
        for record in artifact["records"]
    }


def test_normal_and_boundary_profiles_match_independent_oracle(
    classifier_workspace: Path,
) -> None:
    assert file_sha256(ORACLE_PATH) == PINNED_ORACLE_SHA256
    predicate_path = _predicate_artifact(classifier_workspace)

    structural = classify_predicate_artifact(
        predicate_path, profile="structural"
    )
    formal = classify_predicate_artifact(predicate_path, profile="formal")
    observed = {
        **_classifications(structural),
        **_classifications(formal),
    }
    expected = _oracle_classifications("AC-BND-002")

    assert observed["acr:103:lanes:structural"] == expected[
        "acr:3002:lanes:structural"
    ]
    assert observed["acr:103:maxspeed:structural"] == expected[
        "acr:3002:maxspeed:structural"
    ]
    assert observed["acr:103:lanes:formal"] == expected[
        "acr:3002:lanes:formal"
    ]
    assert observed["acr:103:maxspeed:formal"] == expected[
        "acr:3002:maxspeed:formal"
    ]
    assert all(
        set(record)
        == {
            "classification_record_id",
            "osm_way_id",
            "attribute",
            "profile",
            "subgraph_role",
            "record_revision",
            "record_sha256",
            "supersedes_record_sha256",
            "revision_reason_code",
            "source_artifact_sha256",
            "classification_config_sha256",
            "classification",
        }
        for record in structural["records"]
    )
    serialized = json.dumps(structural)
    assert "resolved_value" not in serialized
    assert "resolution_action" not in serialized
    assert '"resolution"' not in serialized


def test_invalid_predicate_state_fails_closed(
    classifier_workspace: Path,
) -> None:
    predicate_path = _predicate_artifact(classifier_workspace)
    artifact = json.loads(predicate_path.read_text(encoding="utf-8"))
    predicates = artifact["records"][0]["predicates"]
    predicates["is_calibration_segment"]["value"] = True
    predicates["is_validation_segment"]["value"] = True
    _write_json(predicate_path, artifact)

    with pytest.raises(
        CriticalityClassificationError,
        match="predicate artifact failed",
    ):
        classify_predicate_artifact(predicate_path, profile="formal")


def test_repeat_run_is_byte_deterministic(
    classifier_workspace: Path,
) -> None:
    predicate_path = _predicate_artifact(classifier_workspace)

    first = classify_predicate_artifact(predicate_path, profile="formal")
    second = classify_predicate_artifact(predicate_path, profile="formal")

    assert json.dumps(first, sort_keys=True).encode() == json.dumps(
        second, sort_keys=True
    ).encode()


def test_rule_revision_supersedes_prior_records_and_matches_oracle(
    classifier_workspace: Path,
) -> None:
    predicate_path = _predicate_artifact(classifier_workspace)
    initial = classify_predicate_artifact(predicate_path, profile="formal")
    predecessor_path = _write_json(
        classifier_workspace / "classification-v1.json", initial
    )
    promoted_path = _predicate_artifact(
        classifier_workspace, accepted_route=True
    )

    promoted = classify_predicate_artifact(
        promoted_path,
        profile="formal",
        predecessor_path=predecessor_path,
        revision_reason_code="ACR-PROMOTION",
    )
    expected = _oracle_classifications("AC-BND-003")

    assert _classifications(promoted)["acr:103:lanes:formal"] == expected[
        "acr:3003:lanes:formal"
    ]
    assert _classifications(promoted)["acr:103:maxspeed:formal"] == expected[
        "acr:3003:maxspeed:formal"
    ]
    for old_record, new_record in zip(initial["records"], promoted["records"]):
        assert new_record["record_revision"] == 2
        assert new_record["supersedes_record_sha256"] == old_record["record_sha256"]
        assert new_record["revision_reason_code"] == "ACR-PROMOTION"
    assert json.loads(predecessor_path.read_text(encoding="utf-8")) == initial


def test_resolver_adapter_preserves_classification_objects(
    classifier_workspace: Path,
) -> None:
    predicate_path = _predicate_artifact(classifier_workspace)
    classification = classify_predicate_artifact(
        predicate_path, profile="structural"
    )
    classification_path = _write_json(
        classifier_workspace / "classification.json", classification
    )
    before = copy.deepcopy(classification)
    criticality, loaded = load_classification_for_resolution(
        classification_path,
        expected_profile="structural",
    )
    resolutions = {
        record["classification_record_id"]: {
            "resolution_action": "stop_unresolved",
            "resolved_value": None,
        }
        for record in classification["records"]
    }

    combined = attach_resolution_without_overwriting_classification(
        loaded, resolutions
    )

    assert criticality == {"103": "noncritical"}
    assert loaded == before
    assert [
        record["classification_record"]["classification"] for record in combined
    ] == [
        record["classification"] for record in before["records"]
    ]
    assert json.loads(classification_path.read_text(encoding="utf-8")) == before

    invalid_resolutions = copy.deepcopy(resolutions)
    first_id = next(iter(invalid_resolutions))
    invalid_resolutions[first_id]["classification"] = {
        "criticality_level": "L3"
    }
    with pytest.raises(ValueError, match="must not contain classification"):
        attach_resolution_without_overwriting_classification(
            classification, invalid_resolutions
        )
