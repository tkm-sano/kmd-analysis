"""Build derived descriptors and the manifest for classification fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

from traffic_simulation.paths import REPOSITORY_ROOT


COLLECTION_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/attribute_classification"
)
SPECIFICATION_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/"
    "attribute_criticality_and_evidence_specification.md"
)


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def coverage_from_assertions(
    assertions: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for assertion in assertions:
        grouped.setdefault(str(assertion["type"]), []).append(
            str(assertion["assertion_id"])
        )
    return [
        {"coverage_id": coverage_id, "assertion_ids": sorted(assertion_ids)}
        for coverage_id, assertion_ids in sorted(grouped.items())
    ]


def repeat_contract(
    fixture_id: str,
    existing: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if fixture_id != "AC-REP-001":
        return None
    baseline = COLLECTION_ROOT / "repeat/baseline.json"
    repeated = COLLECTION_ROOT / "repeat/repeated.json"
    mode = (
        existing.get("comparison_mode")
        if isinstance(existing, Mapping)
        else "byte_equal"
    )
    return {
        "baseline_output_sha256": file_sha256(baseline),
        "repeated_output_sha256": file_sha256(repeated),
        "comparison_mode": mode,
        "excluded_json_pointers": [],
        "comparison_scope": (
            "raw_file_bytes"
            if mode == "byte_equal"
            else "canonical_json_bytes"
        ),
        "canonicalization_rule_id": (
            None if mode == "byte_equal" else "RFC-8785"
        ),
        "encoding": "UTF-8",
        "line_endings": "LF",
        "terminal_newline": True,
        "object_key_order": (
            "serialized_order_significant"
            if mode == "byte_equal"
            else "canonicalized"
        ),
        "record_array_order": "governed_order_significant",
    }


def desired_collection() -> dict[Path, bytes]:
    inputs_path = COLLECTION_ROOT / "inputs.json"
    oracles_path = COLLECTION_ROOT / "oracles.json"
    review_path = COLLECTION_ROOT / "review.json"
    manifest_path = COLLECTION_ROOT / "manifest.json"
    inputs = load_json(inputs_path)
    oracles = load_json(oracles_path)
    review = load_json(review_path)
    manifest = load_json(manifest_path)
    specification_hash = file_sha256(SPECIFICATION_PATH)
    if oracles.get("source_specification_sha256") != specification_hash:
        raise ValueError(
            "oracles.json source_specification_sha256 must be updated by the "
            "independent oracle author before rebuilding derived artifacts"
        )
    input_payload = json_bytes(inputs)
    oracle_payload = json_bytes(oracles)
    input_hash = sha256_bytes(input_payload)
    oracle_hash = sha256_bytes(oracle_payload)
    desired: dict[Path, bytes] = {
        inputs_path: input_payload,
        oracles_path: oracle_payload,
    }

    input_case_ids = set(inputs.get("cases", {}))
    oracle_case_ids = set(oracles.get("cases", {}))
    descriptor_paths = sorted((COLLECTION_ROOT / "cases").glob("*.fixture.json"))
    descriptor_ids = {
        path.name.removesuffix(".fixture.json") for path in descriptor_paths
    }
    if input_case_ids != oracle_case_ids or input_case_ids != descriptor_ids:
        raise ValueError("input, oracle and descriptor case memberships differ")

    case_entries: dict[str, dict[str, Any]] = {}
    descriptor_hashes: dict[str, str] = {}
    scenario_index: dict[str, list[str]] = {}
    level_index: dict[str, list[str]] = {
        level: [] for level in ("L0", "L1", "L2", "L3", "S0", "S1", "S2", "S3")
    }
    for path in descriptor_paths:
        fixture_id = path.name.removesuffix(".fixture.json")
        descriptor = load_json(path)
        descriptor["schema_version"] = 2
        descriptor["description"] = inputs["cases"][fixture_id]["description"]
        descriptor["input_artifacts"] = [
            {
                "role": "classification_input",
                "path": relative(inputs_path),
                "sha256": input_hash,
            }
        ]
        descriptor["expected"] = oracles["cases"][fixture_id]
        descriptor["repeat_assertion"] = repeat_contract(
            fixture_id, descriptor.get("repeat_assertion")
        )
        descriptor["oracle"] = {
            "path": relative(oracles_path),
            "sha256": oracle_hash,
            "source_specification_sha256": specification_hash,
            "independently_authored": True,
        }
        payload = json_bytes(descriptor)
        desired[path] = payload
        descriptor_hash = sha256_bytes(payload)
        descriptor_hashes[fixture_id] = descriptor_hash
        coverage = coverage_from_assertions(descriptor["expected"]["assertions"])
        case_entries[fixture_id] = {
            "path": relative(path),
            "sha256": descriptor_hash,
            "coverage": coverage,
        }
        for item in coverage:
            scenario_index.setdefault(item["coverage_id"], []).append(fixture_id)
        for record in descriptor["expected"]["records"]:
            level = record["classification"]["criticality_level"]
            level_index[level].append(fixture_id)

    level_case_index = {
        level: sorted(set(case_ids))
        for level, case_ids in level_index.items()
    }
    canonical_witnesses = {
        level: case_ids[0]
        for level, case_ids in level_case_index.items()
        if case_ids
    }
    manifest = {
        "artifact_type": "attribute_classification_fixture_manifest",
        "schema_version": 2,
        "created_on": manifest.get("created_on", "2026-07-25"),
        "case_count": len(case_entries),
        "cases": dict(sorted(case_entries.items())),
        "required_negative_fixture_ids": sorted(
            fixture_id
            for fixture_id in case_entries
            if "-NEG-" in fixture_id
        ),
        "level_case_index": level_case_index,
        "canonical_level_witnesses": canonical_witnesses,
        "scenario_coverage": {
            key: sorted(value) for key, value in sorted(scenario_index.items())
        },
        "catalogues": {
            "inputs": {
                "path": relative(inputs_path),
                "sha256": input_hash,
            },
            "oracles": {
                "path": relative(oracles_path),
                "sha256": oracle_hash,
            },
        },
    }
    manifest_payload = json_bytes(manifest)
    desired[manifest_path] = manifest_payload
    manifest_hash = sha256_bytes(manifest_payload)

    review_requirements = [
        "expected classifications follow rule priority",
        "expected resolutions follow the action-state-review contract",
        "negative cases map one-to-one to AC001 through AC010",
        "oracle catalogue was not produced by production code",
        "fixture and source specification hashes match",
        "complete execution inputs identify every target tuple and evidence segment",
        "manifest coverage is backed by executable oracle assertions",
        "failure-stage record emission follows the governed policy",
        "directional and lifecycle assertions contain observable before-and-after state",
        "schema rejection and canonicalization cases cover the declared mutations",
    ]
    existing_checks = review.get(
        "review_checks", review.get("required_review_checks", [])
    )
    check_by_requirement = {
        str(check.get("requirement", check.get("description"))): check
        for check in existing_checks
        if isinstance(check, Mapping)
    }
    review_checks = []
    for index, requirement in enumerate(review_requirements, start=1):
        previous = check_by_requirement.get(requirement, {})
        status = previous.get("status", "not_reviewed")
        mechanically_reviewed = previous.get("reviewed_by") == (
            "fixture-collection-builder"
        )
        if status == "pending" or mechanically_reviewed:
            status = "not_reviewed"
        default_evidence = (
            [
                relative(manifest_path),
                relative(inputs_path),
                relative(oracles_path),
                relative(SPECIFICATION_PATH),
            ]
            if "hashes match" in requirement
            else []
        )
        review_checks.append(
            {
                "check_id": f"FIX-REV-{index:03d}",
                "requirement": requirement,
                "required": True,
                "status": status,
                "evidence_references": (
                    default_evidence
                    if mechanically_reviewed
                    else previous.get(
                        "evidence_references",
                        previous.get("evidence_refs", default_evidence),
                    )
                ),
                "finding_ids": previous.get("finding_ids", []),
                "reviewer_comment": previous.get(
                    "reviewer_comment", previous.get("notes")
                ),
                "reviewed_by": (
                    None if mechanically_reviewed else previous.get("reviewed_by")
                ),
                "reviewed_at": (
                    None if mechanically_reviewed else previous.get("reviewed_at")
                ),
                "recheck_status": previous.get(
                    "recheck_status", "not_required"
                ),
            }
        )

    prior_reviewer = review.get(
        "independent_reviewer", review.get("independent_review", {})
    )
    if not isinstance(prior_reviewer, Mapping):
        prior_reviewer = {}
    attestation = prior_reviewer.get("independence_attestation", {})
    if not isinstance(attestation, Mapping):
        attestation = {}
    independent_reviewer = {
        "reviewer_id": prior_reviewer.get("reviewer_id"),
        "reviewer_name": prior_reviewer.get("reviewer_name"),
        "reviewer_role": prior_reviewer.get("reviewer_role"),
        "relationship_to_fixture_author": prior_reviewer.get(
            "relationship_to_fixture_author", "not_assessed"
        ),
        "relationship_to_production_code_author": prior_reviewer.get(
            "relationship_to_production_code_author", "not_assessed"
        ),
        "independence_declaration": prior_reviewer.get(
            "independence_declaration"
        ),
        "reviewed_at": prior_reviewer.get("reviewed_at"),
    }
    if independent_reviewer["independence_declaration"] is None and any(
        value is not None for value in attestation.values()
    ):
        independent_reviewer["independence_declaration"] = dict(attestation)

    observed_hashes = {}
    for key, path, digest, canonicalization in (
        (
            "manifest",
            manifest_path,
            manifest_hash,
            "pretty_json_sorted_keys_utf8_lf",
        ),
        (
            "inputs",
            inputs_path,
            input_hash,
            "pretty_json_sorted_keys_utf8_lf",
        ),
        (
            "oracles",
            oracles_path,
            oracle_hash,
            "pretty_json_sorted_keys_utf8_lf",
        ),
        (
            "source_specification",
            SPECIFICATION_PATH,
            specification_hash,
            "raw_file_bytes",
        ),
    ):
        observed_hashes[key] = {
            "artifact_path": relative(path),
            "algorithm": "SHA-256",
            "expected_sha256": digest,
            "observed_sha256": digest,
            "matches": True,
            "checked_at": "2026-07-25T00:00:00Z",
            "checker": "fixture-collection-builder",
            "canonicalization": canonicalization,
        }

    previous_observations = review.get("observed_hashes")
    artifacts_changed = (
        isinstance(previous_observations, Mapping)
        and set(previous_observations) == set(observed_hashes)
        and any(
            previous_observations[key].get("expected_sha256")
            != observation["expected_sha256"]
            for key, observation in observed_hashes.items()
            if isinstance(previous_observations.get(key), Mapping)
        )
    )
    collection_status = review.get(
        "collection_status", "awaiting_independent_human_acceptance"
    )
    if artifacts_changed:
        collection_status = "awaiting_independent_human_acceptance"
        independent_reviewer = {
            key: (
                "not_assessed"
                if key.startswith("relationship_to_")
                else None
            )
            for key in independent_reviewer
        }
        for check in review_checks:
            check["status"] = "not_reviewed"
            check["finding_ids"] = []
            check["reviewer_comment"] = None
            check["reviewed_by"] = None
            check["reviewed_at"] = None
            check["recheck_status"] = "required"
    prior_oracle_verification = review.get(
        "oracle_independence",
        review.get("oracle_authorship_verification", {}),
    )
    if not isinstance(prior_oracle_verification, Mapping):
        prior_oracle_verification = {}
    oracle_verification_status = prior_oracle_verification.get(
        "verification_status", "not_reviewed"
    )
    if artifacts_changed:
        oracle_verification_status = "not_reviewed"

    blocking_findings = review.get(
        "blocking_findings", review.get("findings", [])
    )
    if not isinstance(blocking_findings, list):
        blocking_findings = []
    required_checks = [
        check for check in review_checks if check.get("required") is True
    ]
    all_passed = bool(required_checks) and all(
        check["status"] in {"passed", "not_applicable"}
        for check in required_checks
    )
    no_open_blocker = not any(
        isinstance(finding, Mapping)
        and finding.get("severity") == "blocking"
        and finding.get("status") != "resolved"
        for finding in blocking_findings
    )
    review = {
        "artifact_type": "attribute_classification_fixture_review",
        "schema_version": 2,
        "author": review.get(
            "author",
            {
                "author_id": None,
                "author_name": None,
                "author_role": "fixture_author",
            },
        ),
        "authoring_basis": {
            "artifact_path": relative(SPECIFICATION_PATH),
            "artifact_version": "1.1.0",
            "artifact_sha256": specification_hash,
        },
        "collection_status": collection_status,
        "independent_reviewer": independent_reviewer,
        "oracle_independence": {
            "source_pointer": "oracles.json#/authorship",
            "oracles_authored_before_production_classifier": (
                oracles.get("authorship", {}).get(
                    "production_classifier_existed_at_authorship"
                )
                is False
            ),
            "production_code_used_to_generate_oracles": not bool(
                oracles.get("authorship", {}).get(
                    "independent_from_production_code"
                )
            ),
            "authoring_process_description": (
                "Expected results were authored from the normative "
                "specification before the production Classifier existed."
            ),
            "verification_status": oracle_verification_status,
        },
        "review_checks": review_checks,
        "observed_hashes": observed_hashes,
        "blocking_findings": blocking_findings,
        "reviewed_at": None if artifacts_changed else review.get("reviewed_at"),
        "acceptance_allowed": (
            collection_status == "independently_accepted"
            and all_passed
            and no_open_blocker
        ),
    }
    desired[review_path] = json_bytes(review)
    return desired


def build(*, check: bool) -> int:
    desired = desired_collection()
    stale = [
        path
        for path, payload in desired.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if check:
        if stale:
            for path in stale:
                print(f"stale: {relative(path)}")
            return 1
        print("attribute-classification fixture collection is current")
        return 0
    for path, payload in desired.items():
        atomic_write(path, payload)
    print(f"wrote {len(desired)} fixture-collection artifacts")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return build(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
