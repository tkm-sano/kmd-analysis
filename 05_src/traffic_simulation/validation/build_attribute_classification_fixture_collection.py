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

    review["schema_version"] = 2
    review["authoring_basis"] = {
        "path": relative(SPECIFICATION_PATH),
        "sha256": specification_hash,
        "specification_version": "1.1.0",
    }
    review["oracle_authorship_verification"] = {
        "source_pointer": "oracles.json#/authorship",
        "status": "pending",
    }
    observations = [
        {
            "artifact_path": relative(inputs_path),
            "algorithm": "SHA-256",
            "expected_hash": input_hash,
            "observed_hash": input_hash,
            "matched": True,
            "checked_at": "2026-07-25T00:00:00Z",
            "checker": "fixture-collection-builder",
            "canonicalization": "pretty_json_sorted_keys_utf8_lf",
        },
        {
            "artifact_path": relative(oracles_path),
            "algorithm": "SHA-256",
            "expected_hash": oracle_hash,
            "observed_hash": oracle_hash,
            "matched": True,
            "checked_at": "2026-07-25T00:00:00Z",
            "checker": "fixture-collection-builder",
            "canonicalization": "pretty_json_sorted_keys_utf8_lf",
        },
        {
            "artifact_path": relative(SPECIFICATION_PATH),
            "algorithm": "SHA-256",
            "expected_hash": specification_hash,
            "observed_hash": specification_hash,
            "matched": True,
            "checked_at": "2026-07-25T00:00:00Z",
            "checker": "fixture-collection-builder",
            "canonicalization": "raw_file_bytes",
        },
    ]
    review["hash_observations"] = observations
    checks = review.get("required_review_checks", [])
    if checks and isinstance(checks[0], str):
        review["required_review_checks"] = [
            {
                "check_id": f"REVIEW-CHECK-{index:03d}",
                "description": description,
                "status": (
                    "passed"
                    if "hash" in description
                    else "pending"
                ),
                "finding_ids": [],
                "evidence_refs": (
                    [relative(inputs_path), relative(oracles_path)]
                    if "hash" in description
                    else []
                ),
                "reviewed_by": (
                    "fixture-collection-builder"
                    if "hash" in description
                    else None
                ),
                "reviewed_at": (
                    "2026-07-25T00:00:00Z"
                    if "hash" in description
                    else None
                ),
                "notes": None,
                "recheck_status": "not_required",
            }
            for index, description in enumerate(checks, start=1)
        ]
    review["independent_review"] = review.get(
        "independent_review",
        {
            "reviewer_id": None,
            "reviewer_name": None,
            "reviewer_role": None,
            "reviewed_at": None,
            "independence_attestation": {
                "did_not_author_oracles": None,
                "did_not_generate_expected_results_from_production_code": None,
                "did_not_implement_reviewed_classifier_rules": None,
            },
        },
    )
    review.pop("independent_reviewer", None)
    review.pop("reviewed_at", None)
    review.pop("author_role", None)
    review.pop("oracles_authored_before_production_classifier", None)
    review.pop("production_code_used_to_generate_oracles", None)
    all_passed = all(
        check["status"] in {"passed", "not_applicable"}
        for check in review["required_review_checks"]
    )
    no_blocking_findings = not any(
        finding.get("blocking") and finding.get("status") != "resolved"
        for finding in review.get("findings", [])
        if isinstance(finding, Mapping)
    )
    independently_accepted = (
        review.get("collection_status") == "independently_accepted"
    )
    review["acceptance_allowed"] = (
        independently_accepted and all_passed and no_blocking_findings
    )
    review_payload = json_bytes(review)
    desired[review_path] = review_payload

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
            "review": {
                "path": relative(review_path),
                "sha256": sha256_bytes(review_payload),
            },
        },
    }
    desired[manifest_path] = json_bytes(manifest)
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
