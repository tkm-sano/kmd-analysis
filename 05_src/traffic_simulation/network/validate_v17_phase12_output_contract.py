"""Validate the fixed v17 Phase 12 full-population output contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml"
)
ADOPTION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase12_output_contract_adoption.yml"
)
REQUIRED_ARTIFACT_IDS = {
    "structural_full_population",
    "formal_full_population",
    "complete_blocker_inventory",
    "exclusion_manifest",
    "population_accounting",
    "environment_build_manifest",
    "run_manifest",
    "determinism_report",
}
DETERMINISTIC_ARTIFACT_IDS = {
    "structural_full_population",
    "formal_full_population",
    "complete_blocker_inventory",
    "exclusion_manifest",
    "population_accounting",
}


class Phase12OutputContractError(ValueError):
    pass


def _repo_file(relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        raise Phase12OutputContractError(f"non-repository-relative path: {relative}")
    resolved = (REPOSITORY_ROOT / Path(*path.parts)).resolve()
    if not resolved.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise Phase12OutputContractError(f"path escapes repository: {relative}")
    return resolved


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase12OutputContractError(f"YAML root is not an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase12OutputContractError(f"JSON root is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_output_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    schema_path = _repo_file(str(contract.get("schema", "")))
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(contract)
    except jsonschema.ValidationError as error:
        raise Phase12OutputContractError(
            f"output contract Schema validation failed: {error.message}"
        ) from error

    for field in (
        "normative_specification",
        *contract["fixed_inputs"].keys(),
    ):
        if field == "hash_binding_required":
            continue
        relative = (
            contract[field]
            if field == "normative_specification"
            else contract["fixed_inputs"][field]
        )
        if not _repo_file(str(relative)).is_file():
            raise Phase12OutputContractError(f"referenced input does not exist: {relative}")

    artifacts = contract["artifact_catalog"]
    ids = [item["artifact_id"] for item in artifacts]
    paths = [item["path_template"] for item in artifacts]
    if set(ids) != REQUIRED_ARTIFACT_IDS or len(ids) != len(set(ids)):
        raise Phase12OutputContractError("required artifact IDs differ or are duplicated")
    if len(paths) != len(set(paths)):
        raise Phase12OutputContractError("artifact paths are duplicated")
    for item in artifacts:
        if not _repo_file(item["schema"]).is_file():
            raise Phase12OutputContractError(
                f"artifact Schema does not exist: {item['schema']}"
            )
        artifact_schema = _load_json(_repo_file(item["schema"]))
        jsonschema.Draft202012Validator.check_schema(artifact_schema)
        if PurePosixPath(item["path_template"]).is_absolute() or ".." in PurePosixPath(
            item["path_template"]
        ).parts:
            raise Phase12OutputContractError("artifact path is not safely relative")

    deterministic = {
        item["artifact_id"] for item in artifacts if item["determinism_required"]
    }
    if deterministic != DETERMINISTIC_ARTIFACT_IDS:
        raise Phase12OutputContractError("determinism-required artifact set differs")
    if set(contract["determinism"]["compare_artifact_ids"]) != deterministic:
        raise Phase12OutputContractError("determinism comparison set differs")
    expected_normalization = {
        "arguments": {
            "method": "replace_cli_option_value",
            "option": "--run-id",
            "replacement": "<run_id>",
            "require_value_equals_run_id": True,
        }
    }
    if contract["determinism"].get("environment_field_normalization") != expected_normalization:
        raise Phase12OutputContractError("environment normalization rule differs")
    if contract["profiles"]["formal"]["allow_model_assumed"]:
        raise Phase12OutputContractError("formal profile permits model assumptions")
    if contract["profiles"]["structural"]["acceptance_eligible"]:
        raise Phase12OutputContractError("structural profile became acceptance eligible")
    if contract["population_accounting"]["cross_unit_simple_sum_allowed"]:
        raise Phase12OutputContractError("heterogeneous population units may be summed")
    if contract["population_accounting"][
        "upstream_and_permission_blockers_simple_sum_allowed"
    ]:
        raise Phase12OutputContractError("upstream and permission blockers may be summed")

    return {
        "phase12_output_contract": "passed",
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "required_artifact_count": len(artifacts),
        "determinism_artifact_count": len(deterministic),
        "required_run_count": len(contract["execution"]["required_run_ids"]),
        "next_action": "follow_execution_roadmap",
    }


def validate_adoption_record() -> dict[str, Any]:
    adoption = _load_yaml(ADOPTION_PATH)
    if adoption.get("result") != "passed":
        raise Phase12OutputContractError("output-contract adoption state differs")
    for section in ("artifacts", "schemas"):
        for reference in adoption[section].values():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase12OutputContractError(
                    f"adoption hash differs: {reference['path']}"
                )
    return validate_output_contract(_load_yaml(CONTRACT_PATH))


def main() -> int:
    argparse.ArgumentParser(
        description="Validate the v17 Phase 12 output contract."
    ).parse_args()
    try:
        result = validate_adoption_record()
    except (Phase12OutputContractError, jsonschema.ValidationError, KeyError) as error:
        print(json.dumps({"phase12_output_contract": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
