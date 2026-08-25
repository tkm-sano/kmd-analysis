from __future__ import annotations

import json
from copy import deepcopy

import jsonschema
import pytest
import yaml

from traffic_simulation.network.validate_v17_fixture_oracle import (
    DECISION_SPECIFIC_STOP_CODES,
    FIXTURE_ROOT,
    MANIFEST_PATH,
    FixtureOracleError,
    validate_fixture_oracle,
)
from traffic_simulation.paths import REPOSITORY_ROOT


def _json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_fixed_fixture_oracle_collection_validates() -> None:
    result = validate_fixture_oracle()
    assert result == {
        "manifest_id": "ota_ward_attribute_resolution_v17_phase2_manifest_v1",
        "fixture_count": 57,
        "oracle_count": 57,
        "required_family_count": 38,
        "stop_code_coverage": 30,
        "metamorphic_case_count": 5,
        "production_code_used_for_oracle": False,
        "phase2_fixture_oracle": "passed",
    }


def test_fixture_and_oracle_ids_are_one_to_one() -> None:
    fixtures = _json("inputs.json")["cases"]
    oracles = _json("oracle.json")["oracles"]
    assert {case["oracle_id"] for case in fixtures} == {
        oracle["oracle_id"] for oracle in oracles
    }
    assert len(fixtures) == len(oracles) == 57


def test_every_registered_stop_code_has_one_negative_oracle() -> None:
    fixtures = _json("inputs.json")["cases"]
    oracles = {
        item["oracle_id"]: item for item in _json("oracle.json")["oracles"]
    }
    registry = yaml.safe_load(
        (
            REPOSITORY_ROOT
            / "reproducibility/config/traffic_simulation/"
            "attribute_resolution_registries_v17.yml"
        ).read_text(encoding="utf-8")
    )
    registered = {item["stop_code"] for item in registry["stop_codes"]}
    negative = [case for case in fixtures if case["case_type"] == "negative"]
    covered = [case["covered_stop_codes"][0] for case in negative]
    assert len(covered) == len(set(covered)) == 30
    assert set(covered) == registered - DECISION_SPECIFIC_STOP_CODES
    assert DECISION_SPECIFIC_STOP_CODES <= registered
    for case in negative:
        oracle = oracles[case["oracle_id"]]
        assert oracle["outcome"] == "stopped"
        assert oracle["value_origin"] is None
        assert oracle["effective_value"] is None
        assert oracle["stop_code"] == case["covered_stop_codes"][0]


def test_oracle_records_production_independence() -> None:
    independence = _json("oracle.json")["independence"]
    assert independence["authored_from_normative_specification"] is True
    assert independence["production_code_used_to_derive_expected_values"] is False
    assert independence["production_output_compared_during_authoring"] is False
    validator_source = (
        REPOSITORY_ROOT
        / "05_src/traffic_simulation/network/validate_v17_fixture_oracle.py"
    ).read_text(encoding="utf-8")
    assert "resolve_attribute_values" not in validator_source
    assert "run_v16_attribute_resolution" not in validator_source


def test_required_case_families_and_metamorphic_cases_are_present() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    fixtures = _json("inputs.json")["cases"]
    actual = {case["family"] for case in fixtures}
    assert set(manifest["coverage"]["required_case_families"]) <= actual
    assert sum(case["case_type"] == "metamorphic" for case in fixtures) == 5


def test_manifest_schema_requires_independence_review() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    changed = deepcopy(manifest)
    del changed["independence_review"]
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "reproducibility/config/traffic_simulation/schemas/"
            "v17_fixture_oracle_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(changed)


def test_validator_rejects_tampered_oracle_hash(tmp_path) -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["oracles"]["sha256"] = "0" * 64
    changed_path = tmp_path / "manifest.yml"
    changed_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    with pytest.raises(FixtureOracleError, match="manifest hash mismatch: oracles"):
        validate_fixture_oracle(changed_path)
