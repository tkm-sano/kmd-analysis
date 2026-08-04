from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


POLICY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "approved_attribute_resolution_policy_v17.yml"
)

AXIS_VALUES = {
    "spatial_scope": ("way", "direction", "lane"),
    "vehicle_scope": ("access", "vehicle", "motor_vehicle", "vehicle_class"),
    "temporal_scope": ("unconditional", "conditional"),
    "purpose_scope": ("general", "destination", "delivery", "customers"),
}


class ApprovedPolicyError(ValueError):
    pass


def _load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ApprovedPolicyError(f"YAML root must be an object: {path}")
    return value


def _load_schema(relative_path: str) -> dict[str, Any]:
    path = REPOSITORY_ROOT / relative_path
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ApprovedPolicyError(f"JSON Schema root must be an object: {path}")
    return value


def validate_approved_policy(
    policy_path: Path = POLICY_PATH,
) -> dict[str, Any]:
    policy = _load_mapping(policy_path)
    policy_schema = _load_schema(policy["schema"])
    jsonschema.Draft202012Validator.check_schema(policy_schema)
    jsonschema.Draft202012Validator(policy_schema).validate(policy)

    # The v17 policy file is now an authority index. Phase 1 synchronization
    # is validated centrally so enum, Schema, Registry, invariant, hash, and
    # traceability checks cannot drift across independent validators.
    from traffic_simulation.network.validate_v17_phase1_authority import (
        validate_phase1_authority,
    )

    validate_phase1_authority(policy_path=policy_path)
    return policy

    axes = policy["access_specificity"]["axes"]
    if axes != {name: list(values) for name, values in AXIS_VALUES.items()}:
        raise ApprovedPolicyError("access specificity axes or order differ")

    profile_ref = policy["managed_vehicle_profile"]
    profile_path = REPOSITORY_ROOT / profile_ref["path"]
    profile = _load_mapping(profile_path)
    profile_schema = _load_schema(profile["schema"])
    jsonschema.Draft202012Validator.check_schema(profile_schema)
    jsonschema.Draft202012Validator(profile_schema).validate(profile)
    if profile["vehicle_profile_id"] != profile_ref["profile_id"]:
        raise ApprovedPolicyError("managed vehicle profile identity mismatch")
    if (
        profile["unladen_mass_kg"] + profile["maximum_payload_kg"]
        != profile["maximum_permissible_mass_kg"]
    ):
        raise ApprovedPolicyError("managed vehicle mass values are inconsistent")

    traceability_path = REPOSITORY_ROOT / policy["requirements_traceability"]
    traceability = _load_mapping(traceability_path)
    traceability_schema = _load_schema(
        "reproducibility/config/traffic_simulation/schemas/"
        "requirements_traceability.schema.json"
    )
    jsonschema.Draft202012Validator.check_schema(traceability_schema)
    jsonschema.Draft202012Validator(traceability_schema).validate(traceability)
    if traceability["config_id"] != "ota_ward_sumo_network_v17":
        raise ApprovedPolicyError("v17 traceability identity mismatch")
    specification_text = "\n".join(
        (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "05_src/traffic_simulation/specifications/"
            "01_network_build_architecture.md",
            "05_src/traffic_simulation/specifications/"
            "02_resolver_specification.md",
            "05_src/traffic_simulation/specifications/"
            "10_approved_attribute_resolution_policy.md",
        )
    )
    test_text = (
        REPOSITORY_ROOT
        / "05_src/traffic_simulation/validation/"
        "test_approved_attribute_resolution_policy.py"
    ).read_text(encoding="utf-8")
    for requirement in traceability["requirements"]:
        if requirement["requirement_id"] not in specification_text:
            raise ApprovedPolicyError(
                f"unregistered v17 requirement: {requirement['requirement_id']}"
            )
        for test_id in requirement["test_ids"]:
            if test_id not in test_text:
                raise ApprovedPolicyError(f"unregistered v17 test: {test_id}")

    if set(policy["permissions_authority"]["managed_vclass_universe"]) != {
        "passenger",
        "taxi",
        "bus",
        "coach",
        "delivery",
        "truck",
        "motorcycle",
    }:
        raise ApprovedPolicyError("managed vClass universe differs")
    contract = policy["resolution_contract"]
    if set(contract["formal_approved_origins"]) & set(
        contract["formal_prohibited_origins"]
    ):
        raise ApprovedPolicyError("formal origin sets overlap")
    if set(contract["formal_approved_origins"]) | set(
        contract["formal_prohibited_origins"]
    ) != set(contract["value_origin_values"]):
        raise ApprovedPolicyError("formal origin sets do not cover every value origin")
    return policy


@dataclass(frozen=True)
class AccessRule:
    rule_id: str
    spatial_scope: str
    vehicle_scope: str
    temporal_scope: str
    purpose_scope: str
    result: str
    applicable: bool = True

    def coordinates(self) -> tuple[int, int, int, int]:
        values = (
            self.spatial_scope,
            self.vehicle_scope,
            self.temporal_scope,
            self.purpose_scope,
        )
        coordinates: list[int] = []
        for axis, value in zip(AXIS_VALUES, values, strict=True):
            try:
                coordinates.append(AXIS_VALUES[axis].index(value))
            except ValueError as error:
                raise ApprovedPolicyError(
                    f"{self.rule_id}: unknown {axis}={value}"
                ) from error
        return tuple(coordinates)  # type: ignore[return-value]


def dominates(left: AccessRule, right: AccessRule) -> bool:
    left_coordinates = left.coordinates()
    right_coordinates = right.coordinates()
    return all(
        left_value >= right_value
        for left_value, right_value in zip(
            left_coordinates, right_coordinates, strict=True
        )
    ) and any(
        left_value > right_value
        for left_value, right_value in zip(
            left_coordinates, right_coordinates, strict=True
        )
    )


def maximal_access_rules(rules: Iterable[AccessRule]) -> tuple[AccessRule, ...]:
    applicable = tuple(rule for rule in rules if rule.applicable)
    for rule in applicable:
        rule.coordinates()
    return tuple(
        rule
        for rule in applicable
        if not any(
            other != rule and dominates(other, rule)
            for other in applicable
        )
    )


def resolve_access_rules(rules: Iterable[AccessRule]) -> dict[str, Any]:
    maximal = maximal_access_rules(rules)
    if not maximal:
        raise ApprovedPolicyError("no applicable access rule")
    results = {rule.result for rule in maximal}
    if len(results) != 1:
        return {
            "resolution_status": "conflict",
            "resolved_value": None,
            "selected_rule_ids": [],
            "maximal_rule_ids": sorted(rule.rule_id for rule in maximal),
            "stop_code": "ACCESS_SPECIFICITY_CONFLICT",
        }
    return {
        "resolution_status": "resolved",
        "resolved_value": next(iter(results)),
        "selected_rule_ids": sorted(rule.rule_id for rule in maximal),
        "maximal_rule_ids": sorted(rule.rule_id for rule in maximal),
        "stop_code": None,
    }


def directed_segment_id(
    source_way_id: int,
    source_start_index: int,
    source_end_index: int,
    direction: str,
) -> str:
    try:
        from traffic_simulation.network.directed_segments_v17 import (
            canonical_segment_id,
        )

        return canonical_segment_id(
            source_way_id, source_start_index, source_end_index, direction
        )
    except ValueError as error:
        raise ApprovedPolicyError(str(error)) from error


def build_directed_segment(
    *,
    source_way_id: int,
    source_start_index: int,
    source_end_index: int,
    source_way_node_ids: Sequence[int],
    direction: str,
    derivation_rule_id: str,
) -> dict[str, Any]:
    try:
        from traffic_simulation.network.directed_segments_v17 import (
            build_directed_segment as build_v17_directed_segment,
        )

        return build_v17_directed_segment(
            source_way_id=source_way_id,
            source_start_index=source_start_index,
            source_end_index=source_end_index,
            source_way_node_ids=source_way_node_ids,
            source_direction=direction,
            derivation_rule_id=derivation_rule_id,
        )
    except ValueError as error:
        raise ApprovedPolicyError(str(error)) from error


def build_way_directions(
    *,
    source_way_id: int,
    source_node_ids: Sequence[int],
    oneway: str,
    source_start_index: int = 0,
    source_end_index: int | None = None,
) -> tuple[dict[str, Any], ...]:
    directions = {
        "yes": ("forward",),
        "no": ("forward", "backward"),
        "-1": ("backward",),
    }
    try:
        selected = directions[oneway]
    except KeyError as error:
        raise ApprovedPolicyError(f"unsupported oneway value: {oneway}") from error
    end_index = len(source_node_ids) - 1 if source_end_index is None else source_end_index
    return tuple(
        build_directed_segment(
            source_way_id=source_way_id,
            source_start_index=source_start_index,
            source_end_index=end_index,
            source_way_node_ids=source_node_ids,
            direction=direction,
            derivation_rule_id=f"OSM_ONEWAY_EXPLICIT_{oneway}",
        )
        for direction in selected
    )
