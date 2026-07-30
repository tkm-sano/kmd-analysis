from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from traffic_simulation.network.validate_attribute_classification import (
    file_sha256,
    validate_fixture_artifact,
    validate_fixture_review_artifact,
)
from traffic_simulation.validation.build_attribute_classification_fixture_collection import (
    build,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/attribute_classification"
)
CASE_ROOT = FIXTURE_ROOT / "cases"
SPECIFICATION_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/"
    "attribute_criticality_and_evidence_specification.md"
)
REQUIRED_NEGATIVE_IDS = {
    f"AC{number:03d}-NEG-001" for number in range(1, 11)
}
REQUIRED_LEVELS = {"L0", "L1", "L2", "L3", "S0", "S1", "S2", "S3"}
REQUIRED_SCENARIOS = {
    "artifact_invalidation",
    "canonicalization",
    "directional_semantics",
    "evidence_selection",
    "hash_match",
    "null_omission_distinction",
    "record_emission",
    "repeated_output_equality",
    "review_transition",
    "rule_priority",
    "schema_rejection",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def fixture_paths() -> list[Path]:
    return sorted(CASE_ROOT.glob("*.fixture.json"))


def test_fixture_manifest_has_exact_case_population_and_required_negatives() -> None:
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    paths = fixture_paths()
    fixture_ids = {path.name.removesuffix(".fixture.json") for path in paths}

    assert manifest["case_count"] == 19
    assert len(paths) == manifest["case_count"]
    assert set(manifest["cases"]) == fixture_ids
    assert set(manifest["required_negative_fixture_ids"]) == REQUIRED_NEGATIVE_IDS
    assert REQUIRED_NEGATIVE_IDS <= fixture_ids


def test_catalogue_and_case_hashes_are_pinned_to_actual_files() -> None:
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    assert set(manifest["catalogues"]) == {"inputs", "oracles"}
    for entry in manifest["catalogues"].values():
        path = REPOSITORY_ROOT / entry["path"]
        assert path.is_file()
        assert file_sha256(path) == entry["sha256"]

    for fixture_id, entry in manifest["cases"].items():
        path = REPOSITORY_ROOT / entry["path"]
        assert path.name == f"{fixture_id}.fixture.json"
        assert file_sha256(path) == entry["sha256"]


def test_inputs_oracles_and_descriptors_have_one_to_one_case_membership() -> None:
    inputs = load_json(FIXTURE_ROOT / "inputs.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    fixture_ids = {
        path.name.removesuffix(".fixture.json") for path in fixture_paths()
    }

    assert set(inputs["cases"]) == fixture_ids
    assert set(oracles["cases"]) == fixture_ids
    assert inputs["authorship"]["production_code_used"] is False
    assert (
        oracles["authorship"]["production_classifier_existed_at_authorship"]
        is False
    )
    assert oracles["authorship"]["independent_from_production_code"] is True
    assert oracles["source_specification_sha256"] == file_sha256(
        SPECIFICATION_PATH
    )


def test_every_descriptor_validates_and_matches_its_oracle() -> None:
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    baseline = FIXTURE_ROOT / "repeat/baseline.json"
    repeated = FIXTURE_ROOT / "repeat/repeated.json"

    for path in fixture_paths():
        fixture = load_json(path)
        kwargs: dict[str, Path] = {}
        if fixture["case_type"] == "repeat":
            kwargs = {
                "baseline_output": baseline,
                "repeated_output": repeated,
            }
        result = validate_fixture_artifact(
            fixture,
            artifact_root=REPOSITORY_ROOT,
            specification_path=SPECIFICATION_PATH,
            **kwargs,
        )
        assert result.valid, {
            "fixture": fixture["fixture_id"],
            **result.to_dict(),
        }
        assert fixture["expected"] == oracles["cases"][fixture["fixture_id"]]


def test_descriptor_refs_bind_shared_input_oracle_and_specification() -> None:
    input_hash = file_sha256(FIXTURE_ROOT / "inputs.json")
    oracle_hash = file_sha256(FIXTURE_ROOT / "oracles.json")
    specification_hash = file_sha256(SPECIFICATION_PATH)

    for path in fixture_paths():
        fixture = load_json(path)
        assert len(fixture["input_artifacts"]) == 1
        assert fixture["input_artifacts"][0]["sha256"] == input_hash
        assert fixture["oracle"]["sha256"] == oracle_hash
        assert (
            fixture["oracle"]["source_specification_sha256"]
            == specification_hash
        )
        assert fixture["oracle"]["independently_authored"] is True


def test_level_and_scenario_coverage_is_nonempty_and_observable() -> None:
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")

    assert set(manifest["level_case_index"]) == REQUIRED_LEVELS
    for level, fixture_ids in manifest["level_case_index"].items():
        assert fixture_ids
        observed = {
            record["classification"]["criticality_level"]
            for fixture_id in fixture_ids
            for record in oracles["cases"][fixture_id]["records"]
        }
        assert level in observed

    assert REQUIRED_SCENARIOS <= set(manifest["scenario_coverage"])
    assert all(manifest["scenario_coverage"].values())
    assert set(manifest["canonical_level_witnesses"]) == REQUIRED_LEVELS


def test_repeat_outputs_are_pinned_and_byte_equal() -> None:
    fixture = load_json(CASE_ROOT / "AC-REP-001.fixture.json")
    baseline = FIXTURE_ROOT / "repeat/baseline.json"
    repeated = FIXTURE_ROOT / "repeat/repeated.json"

    assert fixture["repeat_assertion"]["comparison_mode"] == "byte_equal"
    assert baseline.read_bytes() == repeated.read_bytes()
    assert file_sha256(baseline) == fixture["repeat_assertion"][
        "baseline_output_sha256"
    ]
    assert file_sha256(repeated) == fixture["repeat_assertion"][
        "repeated_output_sha256"
    ]


def test_fixture_collection_records_human_review_waiver_without_acceptance() -> None:
    review = load_json(FIXTURE_ROOT / "review.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")

    assert oracles["authorship"]["production_classifier_existed_at_authorship"] is False
    assert oracles["authorship"]["independent_from_production_code"] is True
    assert review["collection_status"] == "independent_human_review_waived"
    assert review["review_policy"] == {
        "mode": "automated_validation_without_independent_human_review",
        "independent_human_review_required": False,
        "independent_human_review_waived": True,
        "waiver_date": "2026-07-30",
        "waiver_authority": "research_owner",
        "claim_limit": (
            "The fixture collection is not independently human accepted."
        ),
    }
    assert review["independent_reviewer"]["reviewer_id"] is None
    assert (
        review["oracle_independence"]["verification_status"]
        == "not_reviewed"
    )
    assert review["acceptance_allowed"] is False
    assert any(
        check["status"] == "not_reviewed"
        for check in review["review_checks"]
    )


def test_fixture_inputs_are_complete_and_traceable() -> None:
    inputs = load_json(FIXTURE_ROOT / "inputs.json")
    assert inputs["input_contract"]["completeness"] == "complete_execution_input"
    for fixture_id, case in inputs["cases"].items():
        tuples = case["scenario"]["tuples"]
        assert tuples, fixture_id
        for item in tuples:
            assert {
                "osm_way_id",
                "attribute",
                "profile",
                "subgraph_role",
                "osm_attributes",
                "predicates",
                "evidence_candidates",
                "record_revision",
                "supersedes_record_sha256",
            } <= set(item)


def test_external_evidence_segments_match_target_ways() -> None:
    inputs = load_json(FIXTURE_ROOT / "inputs.json")
    for fixture_id, case in inputs["cases"].items():
        for item in case["scenario"]["tuples"]:
            expected_segment = f"way-{item['osm_way_id']}"
            for evidence in item["evidence_candidates"]:
                assert evidence["segment"] == expected_segment, fixture_id


def test_manifest_coverage_resolves_to_oracle_assertions() -> None:
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    for fixture_id, entry in manifest["cases"].items():
        assertion_ids = {
            assertion["assertion_id"]
            for assertion in oracles["cases"][fixture_id]["assertions"]
        }
        covered_ids = {
            assertion_id
            for coverage in entry["coverage"]
            for assertion_id in coverage["assertion_ids"]
        }
        assert covered_ids == assertion_ids


def test_review_acceptance_is_derived_and_specification_is_pinned() -> None:
    review = load_json(FIXTURE_ROOT / "review.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    assert review["schema_version"] == 2
    assert review["authoring_basis"]["artifact_sha256"] == file_sha256(
        SPECIFICATION_PATH
    )
    assert (
        review["authoring_basis"]["artifact_sha256"]
        == oracles["source_specification_sha256"]
    )
    expected_acceptance = (
        review["collection_status"] == "independently_accepted"
        and all(
            check["status"] in {"passed", "not_applicable"}
            for check in review["review_checks"]
            if check["required"]
        )
        and not any(
            finding["severity"] == "blocking"
            and finding["status"] != "resolved"
            for finding in review["blocking_findings"]
        )
    )
    assert review["acceptance_allowed"] is expected_acceptance
    result = validate_fixture_review_artifact(
        review,
        oracles,
        artifact_root=REPOSITORY_ROOT,
        specification_path=SPECIFICATION_PATH,
    )
    assert result.valid, result.to_dict()

    contradictory = copy.deepcopy(review)
    contradictory["acceptance_allowed"] = True
    invalid = validate_fixture_review_artifact(
        contradictory,
        oracles,
        artifact_root=REPOSITORY_ROOT,
        specification_path=SPECIFICATION_PATH,
    )
    assert not invalid.valid
    assert any(error.code == "ACV021" for error in invalid.errors)


def test_review_observes_all_governed_artifacts_without_hash_cycle() -> None:
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    review = load_json(FIXTURE_ROOT / "review.json")

    assert "review" not in manifest["catalogues"]
    assert set(review["observed_hashes"]) == {
        "manifest",
        "inputs",
        "oracles",
        "source_specification",
    }
    for observation in review["observed_hashes"].values():
        path = REPOSITORY_ROOT / observation["artifact_path"]
        actual = file_sha256(path)
        assert observation["algorithm"] == "SHA-256"
        assert observation["expected_sha256"] == actual
        assert observation["observed_sha256"] == actual
        assert observation["matches"] is True


def test_independent_acceptance_requires_complete_review_evidence() -> None:
    review = load_json(FIXTURE_ROOT / "review.json")
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    accepted = copy.deepcopy(review)
    accepted["collection_status"] = "independently_accepted"
    accepted["reviewed_at"] = "2026-07-25T01:00:00Z"
    accepted["independent_reviewer"].update(
        {
            "reviewer_id": "reviewer-001",
            "reviewer_role": "independent_fixture_reviewer",
            "relationship_to_fixture_author": "different_person",
            "relationship_to_production_code_author": "different_person",
            "independence_declaration": (
                "I did not author the fixture oracle or production output."
            ),
            "reviewed_at": "2026-07-25T01:00:00Z",
        }
    )
    accepted["oracle_independence"]["verification_status"] = "passed"
    for check in accepted["review_checks"]:
        check.update(
            {
                "status": "passed",
                "reviewed_by": "reviewer-001",
                "reviewed_at": "2026-07-25T01:00:00Z",
            }
        )
    accepted["acceptance_allowed"] = True

    result = validate_fixture_review_artifact(
        accepted,
        oracles,
        artifact_root=REPOSITORY_ROOT,
        specification_path=SPECIFICATION_PATH,
    )
    assert result.valid, result.to_dict()

    incomplete = copy.deepcopy(accepted)
    incomplete["independent_reviewer"]["independence_declaration"] = None
    invalid = validate_fixture_review_artifact(
        incomplete,
        oracles,
        artifact_root=REPOSITORY_ROOT,
        specification_path=SPECIFICATION_PATH,
    )
    assert not invalid.valid
    assert any(
        error.json_pointer
        == "/independent_reviewer/independence_declaration"
        for error in invalid.errors
    )


def test_specialized_assertions_have_required_observable_content() -> None:
    oracles = load_json(FIXTURE_ROOT / "oracles.json")
    by_type = {
        assertion["type"]: assertion
        for case in oracles["cases"].values()
        for assertion in case["assertions"]
    }
    assert by_type["rule_priority"]["expected"]["multiple_matches_required"] is True
    assert by_type["evidence_selection"]["expected"]["reject_inapplicable"] is True
    assert by_type["artifact_invalidation"]["expected"]["regenerate_artifacts"]
    assert by_type["review_transition"]["expected"]["states"] == [
        "review_required",
        "reviewed",
        "resolved",
    ]
    assert by_type["directional_semantics"]["expected"]["forward"] != (
        by_type["directional_semantics"]["expected"]["backward"]
    )
    assert len(by_type["schema_rejection"]["expected"]["mutations"]) == 8


def test_fixture_collection_builder_is_current() -> None:
    assert build(check=True) == 0
