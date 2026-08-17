"""Normalize and select maximal static access rules for v17 production."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    build_lane_production_artifact,
)
from traffic_simulation.network.directed_segments_v17 import normalize_oneway
from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
RULE_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/access_rule_v17.schema.json"
)
VEHICLE_PROFILE_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/scenario_profiles/"
    "managed_urban_ev_delivery_v1.yml"
)
ACCESS_BASE_KEYS = {
    "access",
    "vehicle",
    "motor_vehicle",
    "motorcar",
    "goods",
    "hgv",
    "delivery",
    "truck",
    "bus",
    "coach",
    "taxi",
    "motorcycle",
    "psv",
    "emergency",
    "agricultural",
    "forestry",
    "bicycle",
    "foot",
    "horse",
    "moped",
    "mofa",
}
VALUE_PATTERN = re.compile(r"^[a-z_]+$")
PURPOSE_UNIVERSE = (
    "general",
    "trip_purpose_destination",
    "trip_purpose_delivery",
    "trip_purpose_customer",
    "private_authorization",
    "permit_assignment",
    "agricultural_context",
    "forestry_context",
)


class StaticAccessError(ValueError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StaticAccessError(
            f"YAML root must be an object: {path}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StaticAccessError(
            f"JSON root must be an object: {path}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return value


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    return _load_yaml(REGISTRY_PATH)


@lru_cache(maxsize=1)
def _rule_validator() -> jsonschema.Draft202012Validator:
    schema = _load_json(RULE_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def default_scenario_context() -> dict[str, Any]:
    profile = _load_yaml(VEHICLE_PROFILE_PATH)
    purpose = profile["trip_purpose"]
    return {
        "vehicle_class": profile["sumo_vclass"],
        "trip_purpose_destination": purpose == "destination",
        "trip_purpose_delivery": purpose == "delivery",
        "trip_purpose_customer": purpose == "customers",
        "permit_assignment": bool(profile["permit_ids"]),
    }


def _access_value(value: str) -> dict[str, Any]:
    normalized = value.strip().lower()
    if VALUE_PATTERN.fullmatch(normalized) is None:
        raise StaticAccessError(
            f"invalid access value: {value!r}",
            stop_code="ACCESS_VALUE_INVALID",
            status="invalid",
        )
    registered = {
        item["source_value"]: item for item in _registry()["access_values"]
    }
    item = registered.get(normalized)
    if item is None:
        raise StaticAccessError(
            f"unregistered access value: {value!r}",
            stop_code="ACCESS_VALUE_UNSUPPORTED",
            status="valid_but_unsupported",
        )
    if item["effect"] == "unsupported":
        raise StaticAccessError(
            f"unsupported access value: {value!r}",
            stop_code=item["stop_code"],
            status="valid_but_unsupported",
        )
    requirement = next(iter(item["required_context"]), None)
    return {
        "source_value": normalized,
        "effect": item["effect"] if item["effect"] != "contextual" else "allowed",
        "authorization_requirement": requirement,
        "purpose_domain": (
            [requirement] if requirement is not None else list(PURPOSE_UNIVERSE)
        ),
    }


def _vehicle_domain(base_key: str) -> list[str]:
    ontology = _registry()["vehicle_ontology"]
    domains = ontology["domains"]
    if base_key in domains:
        return sorted(domains[base_key])
    governed = set(ontology["governed_vclasses"])
    if base_key in governed:
        return [base_key]
    raise StaticAccessError(
        f"no registered vehicle domain for access key: {base_key}",
        stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
        status="unresolved",
    )


def _non_governed_domain_decision(base_key: str) -> dict[str, Any] | None:
    decisions = _registry()["vehicle_ontology"].get(
        "non_governed_domain_decisions", {}
    )
    decision = decisions.get(base_key)
    return decision if isinstance(decision, dict) else None


def _validate_non_governed_domain_decision(key: str, value: str) -> None:
    """Enforce the exact syntax/value boundary approved by an ontology decision."""

    base_key = key.split(":", 1)[0]
    decision = _non_governed_domain_decision(base_key)
    if decision is None:
        return
    if decision["approved_syntax"] == "scalar" and key != base_key:
        raise StaticAccessError(
            f"unregistered scoped syntax for non-governed access key: {key}",
            stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
            status="unresolved",
        )
    normalized = value.strip().lower()
    if normalized not in decision["approved_source_values"]:
        raise StaticAccessError(
            f"unapproved value for non-governed access key {base_key}: {value!r}",
            stop_code="ACCESS_VALUE_UNSUPPORTED",
            status="valid_but_unsupported",
        )


def _rule_id(
    source_way_id: int, source_key: str, lane_position: int | None, source_value: str
) -> str:
    payload = json.dumps(
        {
            "source_way_id": source_way_id,
            "source_key": source_key,
            "lane_position": lane_position,
            "source_value": source_value,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sar:{hashlib.sha256(payload).hexdigest()}"


def _build_rule(
    *,
    source_way_id: int,
    source_key: str,
    source_value: str,
    base_key: str,
    direction_scope: str,
    lane_position: int | None,
) -> dict[str, Any]:
    semantics = _access_value(source_value)
    decision = _non_governed_domain_decision(base_key)
    rule = {
        "rule_id": _rule_id(
            source_way_id, source_key, lane_position, semantics["source_value"]
        ),
        "source_key": source_key,
        "source_value": semantics["source_value"],
        "source_element": {"type": "way", "id": source_way_id},
        "target_scope": {
            "direction_scope": direction_scope,
            "lane_scope": {
                "type": "all" if lane_position is None else "explicit_positions",
                "positions": [] if lane_position is None else [lane_position],
            },
        },
        "spatial_domain": [f"way:{source_way_id}"],
        "vehicle_domain": _vehicle_domain(base_key),
        "temporal_domain": ["unconditional"],
        "purpose_domain": semantics["purpose_domain"],
        "effect": semantics["effect"],
        "authorization_requirement": semantics["authorization_requirement"],
        "source_order": None,
        "provenance": {
            "policy_id": "ota_ward_attribute_resolution_policy_v17",
            "registry_bundle_id": _registry()["registry_bundle_id"],
            "normalization": "static_access_v17",
            **(
                {
                    "vehicle_ontology_decision_id": decision["decision_id"],
                    "vehicle_ontology_rule_id": decision["rule_id"],
                }
                if decision is not None
                else {}
            ),
        },
    }
    try:
        _rule_validator().validate(rule)
    except jsonschema.ValidationError as error:
        raise StaticAccessError(
            f"AccessRule Schema violation: {error.message}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        ) from error
    return rule


def _parse_access_key(key: str) -> tuple[str, str, bool] | None:
    parts = key.split(":")
    base = parts[0]
    if base not in ACCESS_BASE_KEYS:
        return None
    if "conditional" in parts:
        if base == "psv":
            raise StaticAccessError(
                f"unsupported psv conditional syntax: {key}",
                stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
                status="unresolved",
            )
        return None
    direction = "both"
    if parts[-1] in {"forward", "backward"}:
        direction = parts[-1]
        parts = parts[:-1]
    lane_scoped = len(parts) == 2 and parts[1] == "lanes"
    scalar = len(parts) == 1
    if not scalar and not lane_scoped:
        if base == "psv":
            raise StaticAccessError(
                f"unsupported psv syntax: {key}",
                stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
                status="unresolved",
            )
        return None
    if base == "psv" and direction != "both" and not lane_scoped:
        raise StaticAccessError(
            f"unsupported psv directional syntax: {key}",
            stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
            status="unresolved",
        )
    return base, direction, lane_scoped


def normalize_static_access_rules(
    *,
    source_way_id: int,
    tags: Mapping[str, str],
    lane_counts: Mapping[str, int],
    candidate_keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Normalize static OSM tags while deferring all conditional tags."""

    selected_keys = set(candidate_keys) if candidate_keys is not None else set(tags)
    for key in sorted(selected_keys):
        if key in tags:
            if key.split(":", 1)[0] == "psv" and "conditional" in key.split(":"):
                raise StaticAccessError(
                    f"unsupported psv conditional syntax: {key}",
                    stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
                    status="unresolved",
                )
            _validate_non_governed_domain_decision(key, tags[key])
    conditional = {
        key: tags[key]
        for key in sorted(selected_keys)
        if key in tags and "conditional" in key.split(":")
    }
    rules: list[dict[str, Any]] = []
    oneway = normalize_oneway(tags)["canonical_oneway"]
    active_direction = "backward" if oneway == "-1" else "forward"
    for key in sorted(selected_keys):
        if key not in tags or key in conditional:
            continue
        parsed = _parse_access_key(key)
        if parsed is None:
            if candidate_keys is not None:
                base = key.split(":", 1)[0]
                _vehicle_domain(base)
            continue
        base, direction, lane_scoped = parsed
        if lane_scoped:
            target_direction = active_direction if direction == "both" and oneway != "no" else direction
            if target_direction == "both":
                raise StaticAccessError(
                    f"unsuffixed lane access is ambiguous on bidirectional Way: {key}",
                    stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
                    status="unresolved",
                )
            count = lane_counts.get(target_direction, 0)
            values = tags[key].split("|")
            if len(values) != count:
                raise StaticAccessError(
                    f"access lane vector length differs for {key}",
                    stop_code="LANE_VECTOR_LENGTH_MISMATCH",
                    status="conflict",
                )
            for position, value in enumerate(values):
                if value == "":
                    continue
                rules.append(
                    _build_rule(
                        source_way_id=source_way_id,
                        source_key=key,
                        source_value=value,
                        base_key=base,
                        direction_scope=target_direction,
                        lane_position=position,
                    )
                )
        else:
            rules.append(
                _build_rule(
                    source_way_id=source_way_id,
                    source_key=key,
                    source_value=tags[key],
                    base_key=base,
                    direction_scope=direction,
                    lane_position=None,
                )
            )
    rules.sort(key=lambda item: item["rule_id"])
    return {"rules": rules, "deferred_conditional_tags": conditional}


def _scope_sets(rule: Mapping[str, Any], lane_count: int) -> tuple[set[str], set[int]]:
    direction = rule["target_scope"]["direction_scope"]
    directions = {"forward", "backward"} if direction == "both" else {direction}
    lane_scope = rule["target_scope"]["lane_scope"]
    lanes = (
        set(range(lane_count))
        if lane_scope["type"] == "all"
        else set(lane_scope["positions"])
    )
    return directions, lanes


def static_rule_dominates(
    left: Mapping[str, Any], right: Mapping[str, Any], *, lane_count: int
) -> bool:
    left_direction, left_lanes = _scope_sets(left, lane_count)
    right_direction, right_lanes = _scope_sets(right, lane_count)
    left_domains = (
        left_direction,
        left_lanes,
        set(left["spatial_domain"]),
        set(left["vehicle_domain"]),
        set(left["temporal_domain"]),
        set(left["purpose_domain"]),
    )
    right_domains = (
        right_direction,
        right_lanes,
        set(right["spatial_domain"]),
        set(right["vehicle_domain"]),
        set(right["temporal_domain"]),
        set(right["purpose_domain"]),
    )
    return all(left_set <= right_set for left_set, right_set in zip(left_domains, right_domains)) and any(
        left_set < right_set for left_set, right_set in zip(left_domains, right_domains)
    )


def _evaluate_context(
    rule: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    result = copy.deepcopy(dict(rule))
    requirement = rule["authorization_requirement"]
    if requirement is None:
        return result
    if requirement not in context:
        raise StaticAccessError(
            f"required static access context is missing: {requirement}",
            stop_code="ACCESS_CONTEXT_MISSING",
            status="unresolved",
        )
    matched = context[requirement]
    if not isinstance(matched, bool):
        raise StaticAccessError(
            f"static access context must be Boolean: {requirement}",
            stop_code="ACCESS_CONTEXT_MISSING",
            status="unresolved",
        )
    result["effect"] = "allowed" if matched else "denied"
    result["provenance"]["context_evaluation"] = {
        "requirement": requirement,
        "matched": matched,
    }
    return result


def maximal_static_rules_for_tuple(
    rules: Sequence[Mapping[str, Any]],
    *,
    direction: str,
    lane_position: int,
    lane_count: int,
    vehicle_class: str,
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    candidates: list[dict[str, Any]] = []
    for rule in rules:
        directions, lanes = _scope_sets(rule, lane_count)
        if (
            direction in directions
            and lane_position in lanes
            and vehicle_class in rule["vehicle_domain"]
        ):
            candidates.append(_evaluate_context(rule, context))
    return tuple(
        rule
        for rule in candidates
        if not any(
            other["rule_id"] != rule["rule_id"]
            and static_rule_dominates(other, rule, lane_count=lane_count)
            for other in candidates
        )
    )


def resolve_maximal_static_effect(rules: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rules:
        return {"effect": None, "maximal_rule_ids": [], "pending_final_resolution": True}
    effects = {rule["effect"] for rule in rules}
    if len(effects) > 1:
        raise StaticAccessError(
            "maximal static access rules have different effects",
            stop_code="ACCESS_SPECIFICITY_CONFLICT",
            status="conflict",
        )
    return {
        "effect": next(iter(effects)),
        "maximal_rule_ids": sorted(rule["rule_id"] for rule in rules),
        "pending_final_resolution": True,
    }


def _source_way_tags(input_path: Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for _event, element in ET.iterparse(input_path, events=("end",)):
        if element.tag == "way":
            tags = {item.attrib["k"]: item.attrib["v"] for item in element.findall("tag")}
            if "highway" in tags:
                result[int(element.attrib["id"])] = tags
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return result


def build_static_access_production_artifact(
    input_path: Path,
    *,
    profile: str,
    scenario_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    lanes = build_lane_production_artifact(input_path, profile=profile)
    tags_by_way = _source_way_tags(input_path)
    context = {**default_scenario_context(), **dict(scenario_context or {})}
    lane_segments_by_way: dict[int, list[Mapping[str, Any]]] = {}
    for item in lanes["segment_lanes"]:
        lane_segments_by_way.setdefault(int(item["source_way_id"]), []).append(item)

    normalized: list[dict[str, Any]] = []
    maxima: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    deferred_count = 0
    empty_maxima_count = 0
    conflict_candidate_count = 0
    for way_id in sorted(lane_segments_by_way):
        segments = lane_segments_by_way[way_id]
        counts = {
            item["source_direction"]: int(item["moving_lane_count"])
            for item in segments
        }
        try:
            collection = normalize_static_access_rules(
                source_way_id=way_id,
                tags=tags_by_way[way_id],
                lane_counts=counts,
            )
            normalized.append(
                {
                    "source_way_id": way_id,
                    "rules": collection["rules"],
                    "deferred_conditional_tags": collection[
                        "deferred_conditional_tags"
                    ],
                }
            )
            deferred_count += len(collection["deferred_conditional_tags"])
            for segment in segments:
                for lane in segment["lanes"]:
                    selected = maximal_static_rules_for_tuple(
                        collection["rules"],
                        direction=segment["source_direction"],
                        lane_position=lane["lane_position"],
                        lane_count=segment["moving_lane_count"],
                        vehicle_class=context["vehicle_class"],
                        context=context,
                    )
                    effects = sorted({item["effect"] for item in selected})
                    if not selected:
                        empty_maxima_count += 1
                    if len(effects) > 1:
                        conflict_candidate_count += 1
                    maxima.append(
                        {
                            "directed_segment_id": segment["directed_segment_id"],
                            "source_way_id": way_id,
                            "source_direction": segment["source_direction"],
                            "lane_position": lane["lane_position"],
                            "vehicle_class": context["vehicle_class"],
                            "maximal_rule_ids": sorted(
                                item["rule_id"] for item in selected
                            ),
                            "effects": effects,
                            "pending_conditional_integration": bool(
                                collection["deferred_conditional_tags"]
                            ),
                            "pending_final_permission_resolution": True,
                        }
                    )
        except (StaticAccessError, KeyError) as error:
            if isinstance(error, StaticAccessError):
                status, stop_code = error.status, error.stop_code
            else:
                status, stop_code = "unresolved", "ACCESS_CONTEXT_MISSING"
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": status,
                    "stop_code": stop_code,
                    "message": str(error),
                }
            )
    canonical_payload = json.dumps(
        {"normalized_rules": normalized, "static_maxima": maxima},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 17,
        "artifact_type": "static_access_production_collection",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": lanes["population_version"],
        "profile": profile,
        "source": lanes["source"],
        "directional_lane_semantic_sha256": lanes["semantic_sha256"],
        "managed_scenario_context": context,
        "normalized_rules": normalized,
        "static_maxima": maxima,
        "blockers": blockers,
        "upstream_lane_blockers": lanes["blockers"],
        "upstream_relation_blockers": lanes["upstream_blockers"],
        "counts": {
            "source_ways_with_lane_tuples": len(lane_segments_by_way),
            "normalized_source_ways": len(normalized),
            "normalized_rules": sum(len(item["rules"]) for item in normalized),
            "static_lane_tuples": len(maxima),
            "empty_static_maxima": empty_maxima_count,
            "static_conflict_candidates": conflict_candidate_count,
            "deferred_conditional_tags": deferred_count,
            "static_access_blockers": len(blockers),
            "upstream_lane_blockers": len(lanes["blockers"]),
            "upstream_relation_blockers": len(lanes["upstream_blockers"]),
        },
        "blocker_stop_codes": dict(
            sorted(Counter(item["stop_code"] for item in blockers).items())
        ),
        "semantic_sha256": hashlib.sha256(canonical_payload).hexdigest(),
    }


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite static-access artifact: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(artifact, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, output_path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize v17 static access rules and select tuple maxima."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = build_static_access_production_artifact(
        args.input, profile=args.profile
    )
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 1 if (
        artifact["blockers"]
        or artifact["upstream_lane_blockers"]
        or artifact["upstream_relation_blockers"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
