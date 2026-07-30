"""Generate governed per-way predicates for attribute classification."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Final, Iterable, Mapping, Sequence
from xml.etree import ElementTree

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from traffic_simulation.network.validate_attribute_classification import (
    file_sha256,
    validate_predicate_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
SCHEMA_DIR: Final = (
    REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/schemas"
)
SOURCE_REGISTRY_SCHEMA: Final = SCHEMA_DIR / "predicate_source_registry.schema.json"
EXTERNAL_PREDICATES: Final = (
    "is_calibration_segment",
    "is_validation_segment",
    "is_major_junction_approach",
    "is_accepted_delivery_route",
    "is_sensitivity_elevated",
)
OSM_DERIVED_PREDICATES: Final = (
    "is_bridge",
    "is_tunnel",
    "is_grade_separated",
    "has_directional_lane_semantics",
    "has_reversible_lane_semantics",
    "has_tidal_flow_semantics",
    "has_turn_lane_semantics",
    "has_bus_or_psv_lane_semantics",
    "has_conflicting_lane_semantics",
    "has_directional_speed_semantics",
    "has_conditional_speed_semantics",
    "has_variable_speed_semantics",
    "has_vehicle_specific_speed_semantics",
    "has_advisory_or_multiple_speed_semantics",
)
DERIVATION_RULES: Final = {
    "is_bridge": "PRED-OSM-BRIDGE-001",
    "is_tunnel": "PRED-OSM-TUNNEL-001",
    "is_grade_separated": "PRED-OSM-GRADE-SEPARATION-001",
    "has_directional_lane_semantics": "PRED-OSM-DIRECTIONAL-LANES-001",
    "has_reversible_lane_semantics": "PRED-OSM-REVERSIBLE-LANES-001",
    "has_tidal_flow_semantics": "PRED-OSM-TIDAL-FLOW-001",
    "has_turn_lane_semantics": "PRED-OSM-TURN-LANES-001",
    "has_bus_or_psv_lane_semantics": "PRED-OSM-BUS-PSV-LANES-001",
    "has_conflicting_lane_semantics": "PRED-OSM-LANE-CONFLICT-001",
    "has_directional_speed_semantics": "PRED-OSM-DIRECTIONAL-SPEED-001",
    "has_conditional_speed_semantics": "PRED-OSM-CONDITIONAL-SPEED-001",
    "has_variable_speed_semantics": "PRED-OSM-VARIABLE-SPEED-001",
    "has_vehicle_specific_speed_semantics": "PRED-OSM-VEHICLE-SPEED-001",
    "has_advisory_or_multiple_speed_semantics": "PRED-OSM-ADVISORY-MULTIPLE-SPEED-001",
}
NEGATIVE_TAG_VALUES: Final = frozenset({"", "no", "false", "0"})
VARIABLE_SPEED_VALUES: Final = frozenset({"variable", "signals"})


class PredicateGenerationError(ValueError):
    """A governed predicate artifact cannot be generated."""

    def __init__(
        self,
        code: str,
        json_pointer: str,
        message: str,
        *,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        super().__init__(message)
        self.error = {
            "code": code,
            "json_pointer": json_pointer,
            "message": message,
            "expected": expected,
            "actual": actual,
        }


def _schema_registry() -> Registry:
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PredicateGenerationError(
            "PGEN001", "", "JSON artifact root must be an object", actual=str(path)
        )
    return value


def load_config(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PredicateGenerationError(
            "PGEN001", "", "policy root must be an object", actual=str(path)
        )
    return value


def validate_source_registry(registry: Mapping[str, Any]) -> None:
    schema = json.loads(SOURCE_REGISTRY_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(registry), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise PredicateGenerationError(
            "PGEN001",
            pointer,
            f"predicate source registry failed JSON Schema: {error.message}",
            actual=error.instance,
        )


def repository_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise PredicateGenerationError(
            "PGEN002",
            "",
            "artifact path is outside the repository",
            actual=str(path),
        ) from error


def validate_file_ref(
    ref: Mapping[str, Any],
    pointer: str,
    *,
    expected_path: Path | None = None,
) -> Path:
    relative_path = ref.get("path")
    expected_hash = ref.get("sha256")
    if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
        raise PredicateGenerationError(
            "PGEN002", pointer, "invalid file reference", actual=ref
        )
    path = (REPOSITORY_ROOT / relative_path).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents:
        raise PredicateGenerationError(
            "PGEN002", f"{pointer}/path", "file reference escapes repository"
        )
    if expected_path is not None and path != expected_path.resolve():
        raise PredicateGenerationError(
            "PGEN002",
            f"{pointer}/path",
            "file reference does not match supplied input",
            expected=repository_relative(expected_path),
            actual=relative_path,
        )
    if not path.is_file():
        raise PredicateGenerationError(
            "PGEN002",
            f"{pointer}/path",
            "referenced source file does not exist",
            actual=relative_path,
        )
    actual_hash = file_sha256(path)
    if actual_hash != expected_hash:
        raise PredicateGenerationError(
            "PGEN002",
            f"{pointer}/sha256",
            "referenced source SHA-256 does not match",
            expected=expected_hash,
            actual=actual_hash,
        )
    return path


def file_ref(path: Path) -> dict[str, str]:
    return {"path": repository_relative(path), "sha256": file_sha256(path)}


def load_osm_ways(path: Path) -> dict[str, dict[str, str]]:
    ways: dict[str, dict[str, str]] = {}
    try:
        for _, element in ElementTree.iterparse(path, events=("end",)):
            if element.tag in {"node", "relation"}:
                element.clear()
                continue
            if element.tag != "way":
                continue
            way_id = element.get("id")
            if way_id is None or not way_id.isdigit() or way_id == "0":
                raise PredicateGenerationError(
                    "PGEN003",
                    "",
                    "OSM way has an invalid positive decimal ID",
                    actual=way_id,
                )
            if way_id in ways:
                raise PredicateGenerationError(
                    "PGEN003",
                    "",
                    "OSM contains a duplicate way ID",
                    actual=way_id,
                )
            tags: dict[str, str] = {}
            for tag in element.findall("tag"):
                key = tag.get("k")
                value = tag.get("v")
                if key is None or value is None:
                    raise PredicateGenerationError(
                        "PGEN003",
                        f"/ways/{way_id}",
                        "OSM tag is missing k or v",
                    )
                if key in tags:
                    raise PredicateGenerationError(
                        "PGEN003",
                        f"/ways/{way_id}",
                        "OSM way contains a duplicate tag key",
                        actual=key,
                    )
                tags[key] = value
            ways[way_id] = tags
            element.clear()
    except ElementTree.ParseError as error:
        raise PredicateGenerationError(
            "PGEN003", "", f"OSM XML is not well formed: {error}"
        ) from error
    if not ways:
        raise PredicateGenerationError(
            "PGEN003", "", "OSM XML contains no ways"
        )
    return ways


def _asserted(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in NEGATIVE_TAG_VALUES


def _parse_positive_int(value: str | None) -> int | None:
    if value is None or not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def _layer_is_nonzero(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return int(value.strip()) != 0
    except ValueError:
        return False


def derive_osm_predicates(
    tags: Mapping[str, str],
    *,
    vehicle_qualifiers: set[str],
) -> dict[str, bool]:
    lowered = {key.lower(): value.strip().lower() for key, value in tags.items()}
    keys = set(lowered)
    bridge = _asserted(lowered.get("bridge"))
    tunnel = _asserted(lowered.get("tunnel"))
    lane_total = _parse_positive_int(lowered.get("lanes"))
    lane_forward = _parse_positive_int(lowered.get("lanes:forward"))
    lane_backward = _parse_positive_int(lowered.get("lanes:backward"))
    conflicting_lanes = (
        lane_total is not None
        and lane_forward is not None
        and lane_backward is not None
        and lane_total != lane_forward + lane_backward
    )

    maxspeed_keys = {key for key in keys if key.startswith("maxspeed")}
    main_maxspeed = lowered.get("maxspeed", "")
    return {
        "is_bridge": bridge,
        "is_tunnel": tunnel,
        "is_grade_separated": bridge
        or tunnel
        or _layer_is_nonzero(lowered.get("layer")),
        "has_directional_lane_semantics": (
            "lanes:forward" in keys or "lanes:backward" in keys
        ),
        "has_reversible_lane_semantics": (
            lowered.get("oneway") == "reversible"
            or any(
                "reversible" in key and _asserted(value)
                for key, value in lowered.items()
            )
        ),
        "has_tidal_flow_semantics": any(
            "tidal" in key and _asserted(value) for key, value in lowered.items()
        ),
        "has_turn_lane_semantics": any(
            key == "turn:lanes" or key.startswith("turn:lanes:")
            for key in keys
        ),
        "has_bus_or_psv_lane_semantics": any(
            key == prefix or key.startswith(f"{prefix}:")
            for key in keys
            for prefix in (
                "bus:lanes",
                "psv:lanes",
                "lanes:bus",
                "lanes:psv",
                "busway",
            )
        ),
        "has_conflicting_lane_semantics": conflicting_lanes,
        "has_directional_speed_semantics": any(
            key == "maxspeed:forward"
            or key.startswith("maxspeed:forward:")
            or key == "maxspeed:backward"
            or key.startswith("maxspeed:backward:")
            for key in maxspeed_keys
        ),
        "has_conditional_speed_semantics": any(
            "conditional" in key.split(":") for key in maxspeed_keys
        ),
        "has_variable_speed_semantics": (
            main_maxspeed in VARIABLE_SPEED_VALUES
            or any("variable" in key.split(":") for key in maxspeed_keys)
        ),
        "has_vehicle_specific_speed_semantics": any(
            any(part in vehicle_qualifiers for part in key.split(":")[1:])
            for key in maxspeed_keys
        ),
        "has_advisory_or_multiple_speed_semantics": (
            any("advisory" in key.split(":") for key in maxspeed_keys)
            or ";" in main_maxspeed
            or "|" in main_maxspeed
        ),
    }


def _predicate_evidence(
    value: bool,
    source_artifact_type: str,
    source_sha256: str,
    source_record_locator: str,
    derivation_rule_id: str,
) -> dict[str, Any]:
    return {
        "value": value,
        "source_artifact_type": source_artifact_type,
        "source_artifact_sha256": source_sha256,
        "source_record_locator": source_record_locator,
        "derivation_rule_id": derivation_rule_id,
    }


def _role_map(
    registry: Mapping[str, Any],
    ways: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
    decisions = registry["role_decisions"]
    role_by_way: dict[str, Mapping[str, Any]] = {}
    for index, decision in enumerate(decisions):
        way_id = decision["osm_way_id"]
        if way_id in role_by_way:
            raise PredicateGenerationError(
                "PGEN004",
                f"/role_decisions/{index}/osm_way_id",
                "role decision way ID is duplicated",
                actual=way_id,
            )
        if way_id not in ways:
            raise PredicateGenerationError(
                "PGEN004",
                f"/role_decisions/{index}/osm_way_id",
                "role decision references a way absent from OSM",
                actual=way_id,
            )
        role_by_way[way_id] = decision

    highway_ids = {way_id for way_id, tags in ways.items() if "highway" in tags}
    support_without_highway = {
        way_id
        for way_id, decision in role_by_way.items()
        if decision["subgraph_role"] == "topology_support"
        and way_id not in highway_ids
    }
    invalid_nonhighway = {
        way_id
        for way_id, decision in role_by_way.items()
        if way_id not in highway_ids
        and decision["subgraph_role"] != "topology_support"
    }
    if invalid_nonhighway:
        raise PredicateGenerationError(
            "PGEN004",
            "/role_decisions",
            "non-highway role decisions must be topology_support",
            actual=sorted(invalid_nonhighway, key=int),
        )
    role_ids = set(role_by_way)
    if registry["population_acceptance"]["scope"] == "registered_real_data":
        population = role_ids
    else:
        population = highway_ids | support_without_highway
    if role_ids != population:
        raise PredicateGenerationError(
            "PGEN004",
            "/role_decisions",
            "role decisions do not exactly cover the governed population",
            expected=sorted(population, key=int),
            actual=sorted(role_ids, key=int),
        )
    return role_by_way, population


def _validate_external_sources(
    registry: Mapping[str, Any],
    population: set[str],
    source_index: dict[str, Path],
) -> None:
    for predicate in EXTERNAL_PREDICATES:
        source = registry["external_predicate_sources"][predicate]
        path = validate_file_ref(
            source["source"], f"/external_predicate_sources/{predicate}/source"
        )
        source_index[source["source"]["sha256"]] = path
        unknown_ids = set(source["true_way_ids"]) - population
        if unknown_ids:
            raise PredicateGenerationError(
                "PGEN005",
                f"/external_predicate_sources/{predicate}/true_way_ids",
                "external predicate source references ways outside the population",
                actual=sorted(unknown_ids, key=int),
            )


def _override_map(
    registry: Mapping[str, Any],
    population: set[str],
    source_index: dict[str, Path],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    overrides: dict[tuple[str, str], Mapping[str, Any]] = {}
    for index, override in enumerate(registry["predicate_overrides"]):
        way_id = override["osm_way_id"]
        predicate = override["predicate"]
        key = (way_id, predicate)
        if way_id not in population:
            raise PredicateGenerationError(
                "PGEN006",
                f"/predicate_overrides/{index}/osm_way_id",
                "predicate override references a way outside the population",
                actual=way_id,
            )
        if key in overrides:
            raise PredicateGenerationError(
                "PGEN006",
                f"/predicate_overrides/{index}",
                "predicate override tuple is duplicated",
                actual=list(key),
            )
        path = validate_file_ref(
            override["source"], f"/predicate_overrides/{index}/source"
        )
        source_index[override["source"]["sha256"]] = path
        overrides[key] = override
    return overrides


def generate_predicate_artifact(
    *,
    osm_path: Path,
    source_registry_path: Path,
    policy_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    registry = load_json(source_registry_path)
    validate_source_registry(registry)
    policy = load_config(policy_path)
    if registry["config_id"] != policy.get("config_id") or registry[
        "config_version"
    ] != policy.get("config_version"):
        raise PredicateGenerationError(
            "PGEN007",
            "",
            "source registry and policy config identity differ",
            expected={
                "config_id": policy.get("config_id"),
                "config_version": policy.get("config_version"),
            },
            actual={
                "config_id": registry["config_id"],
                "config_version": registry["config_version"],
            },
        )
    acceptance = registry["population_acceptance"]
    if acceptance["accepted"] is not True:
        raise PredicateGenerationError(
            "PGEN008",
            "/population_acceptance/accepted",
            "classification population has not passed its acceptance gate",
            expected=True,
            actual=acceptance["accepted"],
        )

    source_index: dict[str, Path] = {}
    relation_path = validate_file_ref(
        registry["relation_closed_osm"],
        "/relation_closed_osm",
        expected_path=osm_path,
    )
    source_index[registry["relation_closed_osm"]["sha256"]] = relation_path
    role_source_path = validate_file_ref(registry["role_source"], "/role_source")
    source_index[registry["role_source"]["sha256"]] = role_source_path
    if acceptance["acceptance_artifact"] is not None:
        acceptance_path = validate_file_ref(
            acceptance["acceptance_artifact"],
            "/population_acceptance/acceptance_artifact",
        )
        source_index[acceptance["acceptance_artifact"]["sha256"]] = acceptance_path

    ways = load_osm_ways(relation_path)
    role_by_way, population = _role_map(registry, ways)
    _validate_external_sources(registry, population, source_index)
    overrides = _override_map(registry, population, source_index)

    generator_policy = policy["road_criticality"]["predicate_generator"]
    if (
        acceptance["scope"] == "registered_real_data"
        and registry["config_version"]
        < generator_policy["minimum_real_data_config_version"]
    ):
        raise PredicateGenerationError(
            "PGEN008",
            "/config_version",
            "registered real data predates the minimum accepted population contract",
            expected=f">={generator_policy['minimum_real_data_config_version']}",
            actual=registry["config_version"],
        )
    if tuple(generator_policy["externally_governed_predicates"]) != EXTERNAL_PREDICATES:
        raise PredicateGenerationError(
            "PGEN007",
            "/road_criticality/predicate_generator/externally_governed_predicates",
            "policy external predicate order differs from implementation",
        )
    if tuple(generator_policy["osm_derived_predicates"]) != OSM_DERIVED_PREDICATES:
        raise PredicateGenerationError(
            "PGEN007",
            "/road_criticality/predicate_generator/osm_derived_predicates",
            "policy OSM-derived predicate order differs from implementation",
        )
    vehicle_qualifiers = set(
        generator_policy["vehicle_specific_maxspeed_qualifiers"]
    )

    relation_hash = registry["relation_closed_osm"]["sha256"]
    role_hash = registry["role_source"]["sha256"]
    external_sources = registry["external_predicate_sources"]
    external_true_ids = {
        predicate: set(external_sources[predicate]["true_way_ids"])
        for predicate in EXTERNAL_PREDICATES
    }
    records: list[dict[str, Any]] = []
    for way_id in sorted(population, key=int):
        decision = role_by_way[way_id]
        predicates: dict[str, dict[str, Any]] = {}
        for predicate in EXTERNAL_PREDICATES:
            source = external_sources[predicate]
            value = way_id in external_true_ids[predicate]
            locator = (
                f"true_way_ids/{way_id}"
                if value
                else f"false_scope/all_other_population_ways/{way_id}"
            )
            predicates[predicate] = _predicate_evidence(
                value,
                source["source_artifact_type"],
                source["source"]["sha256"],
                locator,
                source["derivation_rule_id"],
            )

        derived = derive_osm_predicates(
            ways[way_id], vehicle_qualifiers=vehicle_qualifiers
        )
        for predicate in OSM_DERIVED_PREDICATES:
            predicates[predicate] = _predicate_evidence(
                derived[predicate],
                "relation_closed_osm",
                relation_hash,
                f"way/{way_id}/tags",
                DERIVATION_RULES[predicate],
            )

        for predicate in (*EXTERNAL_PREDICATES, *OSM_DERIVED_PREDICATES):
            override = overrides.get((way_id, predicate))
            if override is None:
                continue
            predicates[predicate] = _predicate_evidence(
                override["value"],
                override["source_artifact_type"],
                override["source"]["sha256"],
                override["source_record_locator"],
                override["derivation_rule_id"],
            )

        records.append(
            {
                "osm_way_id": way_id,
                "subgraph_role": decision["subgraph_role"],
                "subgraph_role_evidence": {
                    "asserted_role": decision["subgraph_role"],
                    "source_artifact_type": registry[
                        "role_source_artifact_type"
                    ],
                    "source_artifact_sha256": role_hash,
                    "source_record_locator": decision["source_record_locator"],
                    "derivation_rule_id": decision["derivation_rule_id"],
                },
                "topology_support_reason": decision["topology_support_reason"],
                "predicates": predicates,
            }
        )

    artifact = {
        "artifact_type": "attribute_classification_predicates",
        "schema_version": 1,
        "config_id": registry["config_id"],
        "config_version": registry["config_version"],
        "run_id": registry["run_id"],
        "complete": True,
        "relation_closed_osm": file_ref(relation_path),
        "source_registry": file_ref(source_registry_path),
        "predicate_policy": file_ref(policy_path),
        "population_way_count": len(population),
        "records": records,
    }
    result = validate_predicate_artifact(
        artifact,
        artifact_root=REPOSITORY_ROOT,
        source_index=source_index,
    )
    if not result.valid:
        first = result.errors[0]
        raise PredicateGenerationError(
            "PGEN009",
            first.json_pointer,
            f"generated predicate artifact failed validation: {first.message}",
            expected=first.expected,
            actual=first.actual,
        )
    return artifact


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise PredicateGenerationError(
            "PGEN010",
            "",
            "refusing to overwrite an existing predicate artifact",
            actual=str(output_path),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        artifact, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a governed attribute-classification predicate artifact."
    )
    parser.add_argument("--osm", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        artifact = generate_predicate_artifact(
            osm_path=args.osm,
            source_registry_path=args.source_registry,
            policy_path=args.policy,
        )
        write_artifact_atomic(artifact, args.output)
    except (OSError, json.JSONDecodeError, PredicateGenerationError) as error:
        if isinstance(error, PredicateGenerationError):
            item = error.error
        else:
            item = {
                "code": "PGEN000",
                "json_pointer": "",
                "message": str(error),
                "expected": None,
                "actual": None,
            }
        print(
            json.dumps(
                {"valid": False, "errors": [item]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "valid": True,
                "output": repository_relative(args.output),
                "population_way_count": artifact["population_way_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
