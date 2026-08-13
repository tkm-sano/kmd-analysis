from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution"
)
MANIFEST_PATH = FIXTURE_ROOT / "manifest.yml"
FIXTURE_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "v17_attribute_resolution_fixture_catalog.schema.json"
)
ORACLE_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "v17_attribute_resolution_oracle_catalog.schema.json"
)
MANIFEST_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "v17_fixture_oracle_manifest.schema.json"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
TRACEABILITY_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/"
    "v17_attribute_resolution_traceability_matrix.md"
)
COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase2_completion.yml"
)


class FixtureOracleError(ValueError):
    pass


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise FixtureOracleError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(value, dict):
        raise FixtureOracleError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise FixtureOracleError(f"duplicate JSON key: {key} in {path}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise FixtureOracleError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    root = REPOSITORY_ROOT.resolve()
    if root not in path.parents:
        raise FixtureOracleError(f"path escapes repository: {relative_path}")
    if not path.is_file():
        raise FixtureOracleError(f"missing referenced file: {relative_path}")
    return path


def _validate(schema_path: Path, instance: dict[str, Any]) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(item) for item in error.absolute_path) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise FixtureOracleError(f"{schema_path.name}: {details}")


def validate_fixture_oracle(
    manifest_path: Path = MANIFEST_PATH,
) -> dict[str, Any]:
    manifest = _load_yaml(manifest_path)
    _validate(MANIFEST_SCHEMA_PATH, manifest)

    bound: dict[str, Path] = {}
    for name in ("specification", "fixtures", "oracles"):
        reference = manifest[name]
        path = _repo_file(reference["path"])
        if _sha256(path) != reference["sha256"]:
            raise FixtureOracleError(f"manifest hash mismatch: {name}")
        bound[name] = path

    fixtures = _load_json(bound["fixtures"])
    oracles = _load_json(bound["oracles"])
    _validate(FIXTURE_SCHEMA_PATH, fixtures)
    _validate(ORACLE_SCHEMA_PATH, oracles)

    fixture_items = fixtures["cases"]
    oracle_items = oracles["oracles"]
    fixture_ids = [item["fixture_id"] for item in fixture_items]
    oracle_ids = [item["oracle_id"] for item in oracle_items]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise FixtureOracleError("duplicate fixture ID")
    if len(oracle_ids) != len(set(oracle_ids)):
        raise FixtureOracleError("duplicate oracle ID")

    oracle_by_id = {item["oracle_id"]: item for item in oracle_items}
    bound_oracle_ids = {item["oracle_id"] for item in fixture_items}
    if bound_oracle_ids != set(oracle_ids):
        raise FixtureOracleError("fixture/oracle binding is not one-to-one")

    registry = _load_yaml(REGISTRY_PATH)
    registered_stop_status = {
        item["stop_code"]: item["resolution_status"]
        for item in registry["stop_codes"]
    }
    registered_status = {
        item["value"] for item in registry["state_origin"]["resolution_status"]
    }
    registered_origin = {
        item["value"] for item in registry["state_origin"]["value_origin"]
    }

    covered_stop_codes: list[str] = []
    actual_families: set[str] = set()
    metamorphic_count = 0
    traceability = TRACEABILITY_PATH.read_text(encoding="utf-8")

    for fixture in fixture_items:
        oracle = oracle_by_id[fixture["oracle_id"]]
        actual_families.add(fixture["family"])
        for requirement_id in fixture["requirement_ids"]:
            if requirement_id not in traceability:
                raise FixtureOracleError(
                    f"untraced fixture requirement: {fixture['fixture_id']}={requirement_id}"
                )

        covered = fixture["covered_stop_codes"]
        if fixture["case_type"] == "negative":
            if len(covered) != 1:
                raise FixtureOracleError(
                    f"negative fixture must cover one stop code: {fixture['fixture_id']}"
                )
            stop_code = covered[0]
            covered_stop_codes.append(stop_code)
            if stop_code not in registered_stop_status:
                raise FixtureOracleError(f"unregistered covered stop code: {stop_code}")
            if oracle["outcome"] != "stopped" or oracle["stop_code"] != stop_code:
                raise FixtureOracleError(
                    f"negative oracle mismatch: {fixture['fixture_id']}"
                )
            if oracle["resolution_status"] != registered_stop_status[stop_code]:
                raise FixtureOracleError(
                    f"stop/status mismatch: {fixture['fixture_id']}"
                )
            if oracle["value_origin"] is not None or oracle["effective_value"] is not None:
                raise FixtureOracleError(
                    f"stopped oracle materializes a value: {fixture['fixture_id']}"
                )
        elif fixture["case_type"] == "positive":
            if covered or oracle["stop_code"] is not None:
                raise FixtureOracleError(
                    f"positive fixture contains a stop: {fixture['fixture_id']}"
                )
            if oracle["resolution_status"] is not None and oracle[
                "resolution_status"
            ] not in registered_status:
                raise FixtureOracleError(
                    f"positive oracle has unknown status: {fixture['fixture_id']}"
                )
            if oracle["value_origin"] is not None and oracle[
                "value_origin"
            ] not in registered_origin:
                raise FixtureOracleError(
                    f"positive oracle has unknown origin: {fixture['fixture_id']}"
                )
        else:
            metamorphic_count += 1
            if oracle["outcome"] != "metamorphic_pass":
                raise FixtureOracleError(
                    f"metamorphic oracle mismatch: {fixture['fixture_id']}"
                )

    if set(covered_stop_codes) != set(registered_stop_status):
        missing = sorted(set(registered_stop_status) - set(covered_stop_codes))
        extra = sorted(set(covered_stop_codes) - set(registered_stop_status))
        raise FixtureOracleError(
            f"stop-code coverage mismatch; missing={missing}, extra={extra}"
        )
    if len(covered_stop_codes) != len(set(covered_stop_codes)):
        raise FixtureOracleError("a stop code is covered by more than one negative fixture")

    required_families = set(manifest["coverage"]["required_case_families"])
    if not required_families.issubset(actual_families):
        raise FixtureOracleError(
            f"missing required families: {sorted(required_families - actual_families)}"
        )
    if metamorphic_count != manifest["coverage"]["metamorphic_case_count"]:
        raise FixtureOracleError("metamorphic case count mismatch")

    independence = oracles["independence"]
    review = manifest["independence_review"]
    if any(
        (
            independence["production_code_used_to_derive_expected_values"],
            independence["production_output_compared_during_authoring"],
            review["production_code_used"],
            review["production_output_used"],
        )
    ):
        raise FixtureOracleError("oracle independence boundary is violated")

    if manifest["state"] != "fixed" or review["result"] != "passed":
        raise FixtureOracleError("Phase 2 collection is not fixed and reviewed")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise FixtureOracleError("Phase 2 completion record is not passed")
    for name, reference in completion["fixed_artifacts"].items():
        path = _repo_file(reference["path"])
        if _sha256(path) != reference["sha256"]:
            raise FixtureOracleError(f"completion artifact hash mismatch: {name}")
    for name, reference in completion["schemas"].items():
        path = _repo_file(reference["path"])
        if _sha256(path) != reference["sha256"]:
            raise FixtureOracleError(f"completion Schema hash mismatch: {name}")
    phase1 = _load_yaml(_repo_file(completion["phase1_prerequisite"]["path"]))
    if phase1.get("result") != "passed":
        raise FixtureOracleError("Phase 1 prerequisite is not passed")

    return {
        "manifest_id": manifest["manifest_id"],
        "fixture_count": len(fixture_items),
        "oracle_count": len(oracle_items),
        "required_family_count": len(required_families),
        "stop_code_coverage": len(set(covered_stop_codes)),
        "metamorphic_case_count": metamorphic_count,
        "production_code_used_for_oracle": False,
        "phase2_fixture_oracle": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate fixed v17 specification fixtures and independent oracles."
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = validate_fixture_oracle(args.manifest)
    except (FixtureOracleError, jsonschema.ValidationError, KeyError) as error:
        print(json.dumps({"phase2_fixture_oracle": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
