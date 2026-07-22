"""Resolve governed OSM road attributes before SUMO ``netconvert``.

The resolver is deliberately independent from the future network-build CLI. It
normalizes an OSM XML document, records every adopted value and expected lane
permission, and refuses to emit conversion input while governed attributes are
unresolved. PBF conversion, build manifests, and ``netconvert`` execution remain
the responsibility of ``build_sumo_network.py``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, MutableMapping, Sequence
from xml.etree import ElementTree

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
LANES_PATTERN: Final = re.compile(r"[1-9][0-9]*\Z")
MAXSPEED_PATTERN: Final = re.compile(r"[1-9][0-9]*(?:\.[0-9]+)?\Z")
ACCESS_ALLOW_VALUES: Final = frozenset({"yes", "permissive"})
ACCESS_DENY_VALUES: Final = frozenset({"no"})
ACCESS_BASE_KEYS: Final = (
    "access",
    "vehicle",
    "motor_vehicle",
    "motorcar",
    "goods",
    "hgv",
    "bus",
    "coach",
    "taxi",
    "psv",
    "motorcycle",
    "moped",
    "delivery",
)
ACCESS_CLASS_MAP: Final = {
    "motorcar": frozenset({"passenger", "taxi"}),
    "goods": frozenset({"delivery"}),
    "hgv": frozenset({"truck"}),
    "bus": frozenset({"bus"}),
    "coach": frozenset({"coach"}),
    "taxi": frozenset({"taxi"}),
    "psv": frozenset({"bus", "taxi"}),
    "motorcycle": frozenset({"motorcycle"}),
    "moped": frozenset({"moped"}),
    "delivery": frozenset({"delivery"}),
}
CLASS_ACCESS_PRECEDENCE: Final = (
    "motorcar",
    "goods",
    "hgv",
    "delivery",
    "motorcycle",
    "moped",
    "psv",
    "coach",
    "bus",
    "taxi",
)
AUDIT_FIELDS: Final = (
    "osm_way_id",
    "highway",
    "name",
    "attribute",
    "source_value",
    "adopted_value",
    "value_state",
    "source_registry_id",
    "derivation_method",
    "reference_date",
    "match_status",
    "match_confidence",
    "criticality",
    "decision",
    "reviewer",
    "reviewed_at",
)


class ResolutionError(ValueError):
    """Raised when governed values cannot be safely materialized."""


@dataclass(frozen=True, slots=True)
class AuditRow:
    """One adopted, rejected, or unresolved road-attribute decision."""

    osm_way_id: str
    highway: str
    name: str
    attribute: str
    source_value: str
    adopted_value: str
    value_state: str
    source_registry_id: str
    derivation_method: str
    reference_date: str
    match_status: str
    match_confidence: str
    criticality: str
    decision: str
    reviewer: str = ""
    reviewed_at: str = ""


@dataclass(frozen=True, slots=True)
class ModeDecision:
    """A preregistered unique-mode structural imputation decision."""

    value: str | None
    sample_size: int
    mode_share: float
    distribution: Mapping[str, int]
    decision: str


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """Resolved XML tree, complete audit, and blocking issue descriptions."""

    tree: ElementTree.ElementTree
    audit_rows: tuple[AuditRow, ...]
    blockers: tuple[str, ...]
    retained_way_count: int
    excluded_way_count: int
    permission_expectations: Mapping[str, Mapping[str, tuple[tuple[str, ...], ...]]]
    imputation_summary: Mapping[str, Mapping[str, ModeDecision]]


@dataclass(frozen=True, slots=True)
class ResolverPolicy:
    """Validated subset of ``sumo_network.yml`` used by this resolver."""

    config_id: str
    config_version: int
    source_registry_id: str
    reference_date: str
    retained_highway_types: frozenset[str]
    governed_vclasses: frozenset[str]
    class_access_map: Mapping[str, frozenset[str]]
    typemap_permissions: Mapping[str, frozenset[str]]
    profile: str
    lane_imputation_minimum_sample_size: int
    lane_imputation_minimum_mode_share: float
    speed_imputation_minimum_sample_size: int
    speed_imputation_minimum_mode_share: float


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tags(way: ElementTree.Element) -> dict[str, str]:
    return {
        tag.attrib["k"]: tag.attrib["v"]
        for tag in way.findall("tag")
        if "k" in tag.attrib and "v" in tag.attrib
    }


def _set_tag(way: ElementTree.Element, key: str, value: str) -> None:
    matches = [tag for tag in way.findall("tag") if tag.attrib.get("k") == key]
    if len(matches) > 1:
        raise ResolutionError(f"way {way.attrib.get('id')} has duplicate tag {key}")
    if matches:
        matches[0].set("v", value)
    else:
        ElementTree.SubElement(way, "tag", {"k": key, "v": value})


def _is_access_tag(key: str) -> bool:
    return any(key == base or key.startswith(base + ":") for base in ACCESS_BASE_KEYS)


def _relative_repository_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside the repository: {path}") from exc


def _load_typemap_permissions(
    typemap_path: Path, governed_vclasses: frozenset[str]
) -> dict[str, frozenset[str]]:
    root = ElementTree.parse(typemap_path).getroot()
    if root.tag != "types":
        raise ValueError("typemap root must be <types>")
    result: dict[str, frozenset[str]] = {}
    for element in root.findall("type"):
        type_id = element.attrib.get("id")
        if not type_id or element.attrib.get("discard") == "true":
            continue
        permissions = frozenset(element.attrib.get("allow", "").split())
        if not permissions or not permissions <= governed_vclasses:
            raise ValueError(f"invalid governed permissions for typemap type {type_id}")
        if type_id in result:
            raise ValueError(f"duplicate typemap type {type_id}")
        result[type_id] = permissions
    return result


def load_policy(
    profile: str,
    config_path: Path = CONFIG_PATH,
) -> ResolverPolicy:
    """Load and strictly validate the v14 resolver policy."""

    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("SUMO network config must be a mapping")
    if profile not in {"structural", "formal"}:
        raise ValueError(f"unsupported network profile: {profile}")
    if config.get("config_version") != 14:
        raise ValueError("resolve_osm_attributes requires sumo_network config v14")

    vehicle_scope = config.get("vehicle_scope", {})
    typemap_policy = config.get("typemap_policy", {})
    source = config.get("source", {})
    imputation = config.get("structural_imputation", {})
    oneway = config.get("attribute_rules", {}).get("oneway", {})
    access = config.get("access_resolution", {})
    if oneway.get("motorway_link_without_explicit_value") != "unresolved":
        raise ValueError("unsupported motorway_link oneway policy")
    if oneway.get("explicit_reverse") != (
        "valid_but_unsupported_stop_until_directional_tag_safe_transform"
    ):
        raise ValueError("reverse oneway must fail closed in config v11")
    if oneway.get("statistical_placeholder_allowed") is not False:
        raise ValueError("oneway statistical placeholders must be prohibited")
    if access.get("osm_override_application_order") != [
        "access",
        "vehicle",
        "motor_vehicle",
        "class_specific",
        "direction_specific",
        "lane_specific",
    ]:
        raise ValueError("unsupported OSM access precedence")
    if access.get("final_permission_composition") != (
        "intersection_of_research_scope_and_resolved_osm_permissions"
    ):
        raise ValueError("unsupported final permission composition")

    governed_vclasses = frozenset(vehicle_scope.get("keep_vclasses", ()))
    if not governed_vclasses:
        raise ValueError("vehicle_scope.keep_vclasses must not be empty")
    configured_class_tags = tuple(access.get("class_specific_tags_to_validate", ()))
    unknown_class_tags = sorted(set(configured_class_tags) - set(ACCESS_CLASS_MAP))
    if unknown_class_tags:
        raise ValueError(f"unsupported configured class access tags: {unknown_class_tags}")
    class_access_map = {
        key: ACCESS_CLASS_MAP[key]
        for key in CLASS_ACCESS_PRECEDENCE
        if key in configured_class_tags
    }
    shared = typemap_policy.get("retained_shared_highway_types", ())
    dedicated_ids = typemap_policy.get("retained_dedicated_motorized_type_ids", ())
    retained = {str(value) for value in shared}
    retained.update(
        str(type_id).removeprefix("highway.") for type_id in dedicated_ids
    )

    typemap_path = REPOSITORY_ROOT / str(typemap_policy.get("path", ""))
    if not typemap_path.is_file():
        raise ValueError(f"typemap does not exist: {typemap_path}")
    expected_typemap_hash = typemap_policy.get("sha256")
    if sha256_file(typemap_path) != expected_typemap_hash:
        raise ValueError("typemap SHA-256 does not match sumo_network.yml")
    permissions = _load_typemap_permissions(typemap_path, governed_vclasses)

    lane_rule = imputation.get("lanes", {})
    speed_rule = imputation.get("maxspeed_kmh", {})
    for name, rule in (("lanes", lane_rule), ("maxspeed", speed_rule)):
        if rule.get("statistic") != "unique_mode":
            raise ValueError(f"unsupported {name} structural statistic")
        if rule.get("tie_policy") != "unresolved":
            raise ValueError(f"unsupported {name} tie policy")
        if rule.get("prohibit_automatic_fallback_to_adjacent_highway_class") is not True:
            raise ValueError(f"{name} adjacent-class fallback must be prohibited")
    return ResolverPolicy(
        config_id=str(config["config_id"]),
        config_version=int(config["config_version"]),
        source_registry_id=str(source["source_registry_id"]),
        reference_date=str(source["snapshot_date"]),
        retained_highway_types=frozenset(retained),
        governed_vclasses=governed_vclasses,
        class_access_map=class_access_map,
        typemap_permissions=permissions,
        profile=profile,
        lane_imputation_minimum_sample_size=int(lane_rule["minimum_sample_size"]),
        lane_imputation_minimum_mode_share=float(lane_rule["minimum_mode_share"]),
        speed_imputation_minimum_sample_size=int(speed_rule["minimum_sample_size"]),
        speed_imputation_minimum_mode_share=float(speed_rule["minimum_mode_share"]),
    )


def unique_mode(
    values: Iterable[str], minimum_sample_size: int, minimum_mode_share: float
) -> ModeDecision:
    """Apply the preregistered structural unique-mode decision rule."""

    counts = Counter(values)
    sample_size = sum(counts.values())
    distribution = dict(sorted(counts.items()))
    if sample_size < minimum_sample_size:
        return ModeDecision(None, sample_size, 0.0, distribution, "insufficient_sample")
    highest = max(counts.values(), default=0)
    modes = sorted(value for value, count in counts.items() if count == highest)
    share = highest / sample_size if sample_size else 0.0
    if len(modes) != 1:
        return ModeDecision(None, sample_size, share, distribution, "tied_mode")
    if share < minimum_mode_share:
        return ModeDecision(None, sample_size, share, distribution, "insufficient_mode_share")
    return ModeDecision(modes[0], sample_size, share, distribution, "selected")


def _simple_positive_integer(value: str | None) -> str | None:
    if value is None or LANES_PATTERN.fullmatch(value) is None:
        return None
    return value


def _simple_maxspeed(value: str | None) -> str | None:
    if value is None or MAXSPEED_PATTERN.fullmatch(value) is None:
        return None
    return value


def _direction_status(tags: Mapping[str, str]) -> str | None:
    value = tags.get("oneway")
    if value in {"yes", "-1"}:
        return "oneway"
    if value == "no":
        return "bidirectional"
    if value is not None:
        return None
    if tags.get("junction") == "roundabout" or tags.get("highway") == "motorway":
        return "oneway"
    if tags.get("highway") == "motorway_link":
        return None
    return "bidirectional"


def _explicit_lane_total(tags: Mapping[str, str]) -> str | None:
    directional_keys = ("lanes:forward", "lanes:backward", "lanes:both_ways")
    directional_present = [key for key in directional_keys if key in tags]
    if directional_present:
        values = [_simple_positive_integer(tags.get(key)) for key in directional_present]
        if any(value is None for value in values):
            return None
        direction = _direction_status(tags)
        if direction == "bidirectional" and not {
            "lanes:forward",
            "lanes:backward",
        } <= set(directional_present):
            return None
        if direction == "oneway" and set(directional_present) != {"lanes:forward"}:
            return None
        total = sum(int(value) for value in values if value is not None)
        return str(total)
    return _simple_positive_integer(tags.get("lanes"))


def _explicit_maxspeed(tags: Mapping[str, str]) -> str | None:
    direct = _simple_maxspeed(tags.get("maxspeed"))
    forward = _simple_maxspeed(tags.get("maxspeed:forward"))
    backward = _simple_maxspeed(tags.get("maxspeed:backward"))
    direction = _direction_status(tags)
    if forward is not None or backward is not None:
        if direction == "oneway":
            if forward is None or backward is not None:
                return None
            directional = forward
        elif direction == "bidirectional":
            if forward is None or backward is None or forward != backward:
                return None
            directional = forward
        else:
            return None
        if direct is not None and direct != directional:
                return None
        return directional
    return direct


def _imputation_tables(
    ways: Sequence[ElementTree.Element], policy: ResolverPolicy
) -> tuple[dict[tuple[str, str], ModeDecision], dict[str, ModeDecision]]:
    lane_values: MutableMapping[tuple[str, str], list[str]] = {}
    speed_values: MutableMapping[str, list[str]] = {}
    for way in ways:
        tags = _tags(way)
        highway = tags.get("highway")
        direction = _direction_status(tags)
        lanes = _explicit_lane_total(tags)
        speed = _simple_maxspeed(tags.get("maxspeed"))
        if highway is None:
            continue
        total = _simple_positive_integer(tags.get("lanes"))
        lane_values_conflict = total is not None and lanes is not None and total != lanes
        if direction is not None and lanes is not None and not lane_values_conflict:
            lane_values.setdefault((highway, direction), []).append(lanes)
        if speed is not None and "maxspeed:conditional" not in tags:
            speed_values.setdefault(highway, []).append(speed)
    lane_modes = {
        group: unique_mode(
            values,
            policy.lane_imputation_minimum_sample_size,
            policy.lane_imputation_minimum_mode_share,
        )
        for group, values in lane_values.items()
    }
    speed_modes = {
        highway: unique_mode(
            values,
            policy.speed_imputation_minimum_sample_size,
            policy.speed_imputation_minimum_mode_share,
        )
        for highway, values in speed_values.items()
    }
    return lane_modes, speed_modes


def _audit(
    *,
    way_id: str,
    tags: Mapping[str, str],
    attribute: str,
    source_value: str,
    adopted_value: str,
    value_state: str,
    policy: ResolverPolicy,
    derivation_method: str,
    criticality: str,
    decision: str,
    match_confidence: str = "not_applicable",
) -> AuditRow:
    return AuditRow(
        osm_way_id=way_id,
        highway=tags.get("highway", ""),
        name=tags.get("name", ""),
        attribute=attribute,
        source_value=source_value,
        adopted_value=adopted_value,
        value_state=value_state,
        source_registry_id=policy.source_registry_id,
        derivation_method=derivation_method,
        reference_date=policy.reference_date,
        match_status="not_matched",
        match_confidence=match_confidence,
        criticality=criticality,
        decision=decision,
    )


def _resolve_oneway(
    way: ElementTree.Element,
    tags: Mapping[str, str],
    policy: ResolverPolicy,
    criticality: str,
) -> tuple[AuditRow, str | None]:
    way_id = way.attrib.get("id", "")
    source = tags.get("oneway", "")
    if source == "-1":
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="oneway",
                source_value="-1",
                adopted_value="",
                value_state="valid_but_unsupported",
                policy=policy,
                derivation_method="reverse_oneway_requires_directional_tag_safe_transform",
                criticality=criticality,
                decision="stop",
            ),
            None,
        )
    if source in {"yes", "no"}:
        _set_tag(way, "oneway", source)
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="oneway",
                source_value=source,
                adopted_value=source,
                value_state="explicit_osm",
                policy=policy,
                derivation_method="explicit_osm_oneway",
                criticality=criticality,
                decision="adopted",
            ),
            source,
        )
    if source:
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="oneway",
                source_value=source,
                adopted_value="",
                value_state="invalid",
                policy=policy,
                derivation_method="unsupported_explicit_oneway",
                criticality=criticality,
                decision="stop",
            ),
            None,
        )
    if tags.get("junction") == "roundabout":
        adopted, method = "yes", "implied_roundabout_oneway"
    elif tags.get("highway") == "motorway":
        adopted, method = "yes", "implied_motorway_oneway"
    elif tags.get("highway") == "motorway_link":
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="oneway",
                source_value="",
                adopted_value="",
                value_state="unresolved",
                policy=policy,
                derivation_method="motorway_link_requires_explicit_value",
                criticality=criticality,
                decision="stop",
            ),
            None,
        )
    else:
        adopted, method = "no", "ordinary_road_derived_bidirectional_osm_rule"
    _set_tag(way, "oneway", adopted)
    return (
        _audit(
            way_id=way_id,
            tags=tags,
            attribute="oneway",
            source_value="",
            adopted_value=adopted,
            value_state="derived_osm_rule",
            policy=policy,
            derivation_method=method,
            criticality=criticality,
            decision="adopted",
        ),
        adopted,
    )


def _resolve_lanes(
    way: ElementTree.Element,
    tags: Mapping[str, str],
    oneway: str | None,
    policy: ResolverPolicy,
    criticality: str,
    modes: Mapping[tuple[str, str], ModeDecision],
) -> tuple[AuditRow, int | None]:
    way_id = way.attrib.get("id", "")
    directional_keys = ("lanes:forward", "lanes:backward", "lanes:both_ways")
    directional_source = {key: tags[key] for key in directional_keys if key in tags}
    total_source = tags.get("lanes", "")
    explicit = _explicit_lane_total(tags)
    if directional_source:
        method = "explicit_osm_directional_lanes"
        source_value = json.dumps(directional_source, sort_keys=True)
    else:
        method = "explicit_osm_lanes"
        source_value = total_source
    if explicit is not None:
        if total_source and _simple_positive_integer(total_source) != explicit:
            return (
                _audit(
                    way_id=way_id,
                    tags=tags,
                    attribute="lanes",
                    source_value=source_value,
                    adopted_value="",
                    value_state="conflict",
                    policy=policy,
                    derivation_method="directional_and_total_lanes_disagree",
                    criticality=criticality,
                    decision="stop",
                ),
                None,
            )
        _set_tag(way, "lanes", explicit)
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="lanes",
                source_value=source_value,
                adopted_value=explicit,
                value_state="explicit_osm",
                policy=policy,
                derivation_method=method,
                criticality=criticality,
                decision="adopted",
            ),
            int(explicit),
        )

    explicit_present = bool(total_source or directional_source)
    if (
        not explicit_present
        and policy.profile == "structural"
        and criticality == "noncritical"
        and oneway
    ):
        group = (tags.get("highway", ""), "oneway" if oneway == "yes" else "bidirectional")
        decision = modes.get(group)
        if decision is not None and decision.value is not None:
            _set_tag(way, "lanes", decision.value)
            return (
                _audit(
                    way_id=way_id,
                    tags=tags,
                    attribute="lanes",
                    source_value=source_value,
                    adopted_value=decision.value,
                    value_state="structural_placeholder",
                    policy=policy,
                    derivation_method=(
                        f"input_extent_way_count_unique_mode:{group[0]}:{group[1]}:"
                        f"n={decision.sample_size}:share={decision.mode_share:.6f}"
                    ),
                    criticality=criticality,
                    decision="adopted_structural_only",
                ),
                int(decision.value),
            )
    if directional_source:
        state = "valid_but_unsupported"
        method = "incomplete_or_unsupported_directional_lane_encoding"
    elif total_source:
        state = "invalid"
        method = "invalid_explicit_lane_value"
    else:
        state = "missing"
        method = "no_admissible_lane_value"
    return (
        _audit(
            way_id=way_id,
            tags=tags,
            attribute="lanes",
            source_value=source_value,
            adopted_value="",
            value_state=state,
            policy=policy,
            derivation_method=method,
            criticality=criticality,
            decision="stop",
        ),
        None,
    )


def _resolve_maxspeed(
    way: ElementTree.Element,
    tags: Mapping[str, str],
    policy: ResolverPolicy,
    criticality: str,
    modes: Mapping[str, ModeDecision],
) -> tuple[AuditRow, str | None]:
    way_id = way.attrib.get("id", "")
    related = {
        key: value
        for key, value in tags.items()
        if key == "maxspeed" or key.startswith("maxspeed:")
    }
    source_value = json.dumps(related, sort_keys=True) if related else ""
    if "maxspeed:conditional" in tags:
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="maxspeed",
                source_value=source_value,
                adopted_value="",
                value_state="conditional",
                policy=policy,
                derivation_method="conditional_maxspeed_requires_supported_parser",
                criticality=criticality,
                decision="stop",
            ),
            None,
        )
    explicit = _explicit_maxspeed(tags)
    if explicit is not None:
        _set_tag(way, "maxspeed", explicit)
        method = (
            "explicit_osm_directional_maxspeed"
            if "maxspeed:forward" in tags or "maxspeed:backward" in tags
            else "explicit_osm_maxspeed"
        )
        return (
            _audit(
                way_id=way_id,
                tags=tags,
                attribute="maxspeed",
                source_value=source_value,
                adopted_value=explicit,
                value_state="explicit_osm",
                policy=policy,
                derivation_method=method,
                criticality=criticality,
                decision="adopted",
            ),
            explicit,
        )
    direction = _direction_status(tags)
    forward = _simple_maxspeed(tags.get("maxspeed:forward"))
    backward = _simple_maxspeed(tags.get("maxspeed:backward"))
    directionally_asymmetric = (
        direction == "bidirectional"
        and forward is not None
        and backward is not None
        and forward != backward
    )
    highway = tags.get("highway", "")
    if not related and policy.profile == "structural" and criticality == "noncritical":
        decision = modes.get(highway)
        if decision is not None and decision.value is not None:
            _set_tag(way, "maxspeed", decision.value)
            return (
                _audit(
                    way_id=way_id,
                    tags=tags,
                    attribute="maxspeed",
                    source_value=source_value,
                    adopted_value=decision.value,
                    value_state="structural_placeholder",
                    policy=policy,
                    derivation_method=(
                        f"input_extent_way_count_unique_mode:{highway}:"
                        f"n={decision.sample_size}:"
                        f"share={decision.mode_share:.6f}"
                    ),
                    criticality=criticality,
                    decision="adopted_structural_only",
                ),
                decision.value,
            )
    if directionally_asymmetric:
        state = "directionally_asymmetric"
        method = "directional_maxspeed_cannot_be_materialized_as_single_value"
    elif related:
        state = "valid_but_unsupported"
        method = "unsupported_explicit_maxspeed_encoding"
    else:
        state = "missing"
        method = "no_admissible_maxspeed_value"
    return (
        _audit(
            way_id=way_id,
            tags=tags,
            attribute="maxspeed",
            source_value=source_value,
            adopted_value="",
            value_state=state,
            policy=policy,
            derivation_method=method,
            criticality=criticality,
            decision="stop",
        ),
        None,
    )


def _type_id(tags: Mapping[str, str]) -> str:
    highway = tags.get("highway", "")
    if highway == "service" and tags.get("service") in {"psv", "bus"}:
        return f"highway.service|{tags['service']}"
    return f"highway.{highway}"


def _access_value(key: str, value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized == "designated":
        return True if key.split(":", 1)[0] in ACCESS_CLASS_MAP else None
    if normalized in ACCESS_ALLOW_VALUES:
        return True
    if normalized in ACCESS_DENY_VALUES:
        return False
    return None


def _apply_access_override(
    permissions: set[str],
    baseline: frozenset[str],
    affected: frozenset[str],
    key: str,
    value: str,
) -> bool:
    decision = _access_value(key, value)
    if decision is None:
        return False
    if decision:
        permissions.update(baseline & affected)
    else:
        permissions.difference_update(affected)
    return True


def _lane_counts(
    tags: Mapping[str, str], total_lanes: int, oneway: str
) -> Mapping[str, int] | None:
    if oneway == "yes":
        return {"forward": total_lanes}
    forward = _simple_positive_integer(tags.get("lanes:forward"))
    backward = _simple_positive_integer(tags.get("lanes:backward"))
    both = _simple_positive_integer(tags.get("lanes:both_ways"))
    if forward and backward:
        counts = {"forward": int(forward), "backward": int(backward)}
        if both:
            counts["both_ways"] = int(both)
        if sum(counts.values()) != total_lanes:
            return None
        return counts
    if total_lanes == 1:
        return None
    if total_lanes % 2 == 0:
        return {"forward": total_lanes // 2, "backward": total_lanes // 2}
    return None


def _resolve_permissions(
    tags: Mapping[str, str],
    total_lanes: int,
    oneway: str,
    policy: ResolverPolicy,
) -> tuple[Mapping[str, tuple[tuple[str, ...], ...]] | None, str | None]:
    baseline = policy.typemap_permissions.get(_type_id(tags))
    if baseline is None:
        return None, f"no governed typemap permission set for {_type_id(tags)}"
    counts = _lane_counts(tags, total_lanes, oneway)
    if counts is None:
        return None, "bidirectional lane allocation is unresolved"
    result: dict[str, list[set[str]]] = {
        direction: [set(baseline) for _ in range(count)]
        for direction, count in counts.items()
    }
    consumed_access_tags: set[str] = set()

    general_keys = ("access", "vehicle", "motor_vehicle")
    for key in general_keys:
        if key not in tags:
            continue
        consumed_access_tags.add(key)
        for lanes in result.values():
            for lane in lanes:
                if not _apply_access_override(
                    lane, baseline, policy.governed_vclasses, key, tags[key]
                ):
                    return None, f"unsupported access value {key}={tags[key]}"
    for key, affected in policy.class_access_map.items():
        if key not in tags:
            continue
        consumed_access_tags.add(key)
        for lanes in result.values():
            for lane in lanes:
                if not _apply_access_override(lane, baseline, affected, key, tags[key]):
                    return None, f"unsupported access value {key}={tags[key]}"

    for direction, lanes in result.items():
        for key in general_keys:
            directional_key = f"{key}:{direction}"
            if directional_key not in tags:
                continue
            consumed_access_tags.add(directional_key)
            for lane in lanes:
                if not _apply_access_override(
                    lane,
                    baseline,
                    policy.governed_vclasses,
                    directional_key,
                    tags[directional_key],
                ):
                    return None, (
                        f"unsupported access value {directional_key}="
                        f"{tags[directional_key]}"
                    )
        for key, affected in policy.class_access_map.items():
            directional_key = f"{key}:{direction}"
            if directional_key not in tags:
                continue
            consumed_access_tags.add(directional_key)
            for lane in lanes:
                if not _apply_access_override(
                    lane, baseline, affected, directional_key, tags[directional_key]
                ):
                    return None, (
                        f"unsupported access value {directional_key}="
                        f"{tags[directional_key]}"
                    )

        lane_keys = (*general_keys, *policy.class_access_map)
        for key in lane_keys:
            candidates = (f"{key}:lanes:{direction}", f"{key}:lanes")
            present = [candidate for candidate in candidates if candidate in tags]
            if len(present) > 1:
                return None, f"ambiguous lane access tags: {present}"
            if not present:
                continue
            lane_key = present[0]
            consumed_access_tags.add(lane_key)
            if oneway == "no" and lane_key.endswith(":lanes"):
                return None, f"unsuffixed lane access is ambiguous on bidirectional way: {lane_key}"
            values = tags[lane_key].split("|")
            if len(values) != len(lanes):
                return None, (
                    f"lane access count mismatch for {lane_key}: "
                    f"{len(values)} != {len(lanes)}"
                )
            affected = policy.class_access_map.get(key, policy.governed_vclasses)
            for lane, value in zip(lanes, values):
                if value == "":
                    continue
                if not _apply_access_override(lane, baseline, affected, lane_key, value):
                    return None, f"unsupported lane access value {lane_key}={value}"

    if oneway == "yes":
        for key in (*general_keys, *policy.class_access_map):
            backward_key = f"{key}:backward"
            if backward_key in tags:
                if _access_value(backward_key, tags[backward_key]) is not False:
                    return None, (
                        "opposite-direction access on a one-way road requires "
                        f"separate modeling: {backward_key}={tags[backward_key]}"
                    )
                consumed_access_tags.add(backward_key)
            backward_lane_key = f"{key}:lanes:backward"
            if backward_lane_key in tags:
                values = tags[backward_lane_key].split("|")
                if any(
                    value and _access_value(backward_lane_key, value) is not False
                    for value in values
                ):
                    return None, (
                        "opposite-direction lane access on a one-way road requires "
                        f"separate modeling: {backward_lane_key}"
                    )
                consumed_access_tags.add(backward_lane_key)

    unknown_access_tags = sorted(
        key for key in tags if _is_access_tag(key) and key not in consumed_access_tags
    )
    if unknown_access_tags:
        return None, f"unsupported access tags: {unknown_access_tags}"

    normalized = {
        direction: tuple(tuple(sorted(lane & set(baseline))) for lane in lanes)
        for direction, lanes in result.items()
    }
    return normalized, None


def resolve_tree(
    tree: ElementTree.ElementTree,
    policy: ResolverPolicy,
    *,
    criticality_by_way: Mapping[str, str] | None = None,
) -> ResolutionResult:
    """Resolve retained ways without writing files or hiding blockers."""

    root = tree.getroot()
    if root.tag != "osm":
        raise ValueError("OSM input root must be <osm>")
    criticality_map = criticality_by_way or {}
    retained: list[ElementTree.Element] = []
    excluded = 0
    seen_way_ids: set[str] = set()
    for way in root.findall("way"):
        way_id = way.attrib.get("id", "")
        if not way_id:
            raise ResolutionError("OSM input contains a way without an id")
        if way_id in seen_way_ids:
            raise ResolutionError(f"OSM input contains duplicate way id {way_id}")
        seen_way_ids.add(way_id)
        tag_keys = [tag.attrib.get("k", "") for tag in way.findall("tag")]
        duplicate_keys = sorted(
            key for key, count in Counter(tag_keys).items() if key and count > 1
        )
        if duplicate_keys:
            raise ResolutionError(f"way {way_id} has duplicate tags: {duplicate_keys}")
        highway = _tags(way).get("highway")
        if highway in policy.retained_highway_types:
            retained.append(way)
        elif highway is not None:
            excluded += 1
            root.remove(way)
    if not retained:
        raise ResolutionError("OSM input contains no governed motorized ways")
    lane_modes, speed_modes = _imputation_tables(retained, policy)

    audit_rows: list[AuditRow] = []
    blockers: list[str] = []
    expectations: dict[str, Mapping[str, tuple[tuple[str, ...], ...]]] = {}
    for way in retained:
        original_tags = _tags(way)
        way_id = way.attrib.get("id", "")
        criticality = criticality_map.get(way_id, "unclassified")
        if criticality not in {"critical", "noncritical", "unclassified"}:
            raise ValueError(f"unsupported criticality for way {way_id}: {criticality}")

        oneway_row, oneway = _resolve_oneway(
            way, original_tags, policy, criticality
        )
        audit_rows.append(oneway_row)
        tags_after_direction = _tags(way)
        lanes_row, lanes = _resolve_lanes(
            way,
            tags_after_direction,
            oneway,
            policy,
            criticality,
            lane_modes,
        )
        audit_rows.append(lanes_row)
        speed_row, speed = _resolve_maxspeed(
            way,
            tags_after_direction,
            policy,
            criticality,
            speed_modes,
        )
        audit_rows.append(speed_row)

        if oneway is None or lanes is None or speed is None:
            blockers.extend(
                f"way {way_id} {row.attribute}: {row.value_state}"
                for row in (oneway_row, lanes_row, speed_row)
                if row.decision == "stop"
            )
            continue

        permission_tags = _tags(way)
        permissions, permission_error = _resolve_permissions(
            permission_tags, lanes, oneway, policy
        )
        source_access = {
            key: value for key, value in permission_tags.items() if _is_access_tag(key)
        }
        if permission_error is not None or permissions is None:
            audit_rows.append(
                _audit(
                    way_id=way_id,
                    tags=permission_tags,
                    attribute="permissions",
                    source_value=json.dumps(source_access, sort_keys=True),
                    adopted_value="",
                    value_state="unresolved",
                    policy=policy,
                    derivation_method=permission_error or "permission_resolution_failed",
                    criticality=criticality,
                    decision="stop",
                )
            )
            blockers.append(f"way {way_id} permissions: {permission_error}")
            continue

        if oneway == "no" and not {
            "lanes:forward",
            "lanes:backward",
        } <= set(permission_tags):
            lane_counts = _lane_counts(permission_tags, lanes, oneway)
            audit_rows.append(
                _audit(
                    way_id=way_id,
                    tags=permission_tags,
                    attribute="lane_direction_allocation",
                    source_value=permission_tags.get("lanes", ""),
                    adopted_value=json.dumps(lane_counts, sort_keys=True),
                    value_state="approved_assumption",
                    policy=policy,
                    derivation_method="even_total_lanes_split_equally_by_direction",
                    criticality=criticality,
                    decision="adopted_with_sensitivity_required",
                )
            )

        expectations[way_id] = permissions
        for direction, lane_permissions in permissions.items():
            for lane_index, allowed in enumerate(lane_permissions):
                audit_rows.append(
                    _audit(
                        way_id=way_id,
                        tags=permission_tags,
                        attribute=f"permissions.{direction}.lane_{lane_index}",
                        source_value=json.dumps(source_access, sort_keys=True),
                        adopted_value=" ".join(allowed),
                        value_state="explicit_osm" if source_access else "derived_osm_rule",
                        policy=policy,
                        derivation_method=(
                            "osm_precedence_then_research_scope_intersection:"
                            + (
                                "permissive_access_semantics_recorded"
                                if "permissive" in source_access.values()
                                else "standard_access_semantics"
                            )
                        ),
                        criticality=criticality,
                        decision="adopted",
                    )
                )
        # Preserve source semantics until the post-netconvert permission patch and
        # exhaustive comparison are implemented. The JSON expectation is binding.

    summary = {
        "lanes": {
            f"{highway}|{direction}": decision
            for (highway, direction), decision in lane_modes.items()
        },
        "maxspeed": speed_modes,
    }
    return ResolutionResult(
        tree=tree,
        audit_rows=tuple(audit_rows),
        blockers=tuple(blockers),
        retained_way_count=len(retained),
        excluded_way_count=excluded,
        permission_expectations=expectations,
        imputation_summary=summary,
    )


def write_audit_csv(rows: Sequence[AuditRow], path: Path) -> None:
    """Atomically write the complete attribute audit."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".part",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    temporary.replace(path)


def _write_json(payload: Mapping[str, Any], path: Path) -> None:
    """Atomically write a deterministic JSON audit artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".part",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def _mode_payload(decision: ModeDecision) -> dict[str, Any]:
    return {
        "decision": decision.decision,
        "distribution": dict(decision.distribution),
        "mode_share": decision.mode_share,
        "sample_size": decision.sample_size,
        "selected_value": decision.value,
    }


def _write_tree(tree: ElementTree.ElementTree, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".part",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        tree.write(handle, encoding="utf-8", xml_declaration=True)
    temporary.replace(path)


def resolve_file(
    input_path: Path,
    output_path: Path,
    audit_path: Path,
    permission_expectations_path: Path,
    imputation_summary_path: Path,
    policy: ResolverPolicy,
    *,
    criticality_by_way: Mapping[str, str] | None = None,
    criticality_source_path: Path | None = None,
    overwrite: bool = False,
) -> ResolutionResult:
    """Resolve one OSM XML file, retaining the audit when the gate fails."""

    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and normalized output paths must differ")
    artifact_paths = (
        output_path,
        audit_path,
        permission_expectations_path,
        imputation_summary_path,
    )
    for path in (input_path, *artifact_paths):
        _relative_repository_path(path)
    if len({path.resolve() for path in (input_path, *artifact_paths)}) != 5:
        raise ValueError("resolver input and artifact paths must be distinct")
    if criticality_source_path is not None:
        _relative_repository_path(criticality_source_path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not overwrite and any(path.exists() for path in artifact_paths):
        raise FileExistsError("resolver output already exists; use --overwrite")

    tree = ElementTree.parse(input_path)
    result = resolve_tree(tree, policy, criticality_by_way=criticality_by_way)
    write_audit_csv(result.audit_rows, audit_path)
    source_hash = sha256_file(input_path)
    _write_json(
        {
            "blockers": list(result.blockers),
            "complete": not result.blockers
            and len(result.permission_expectations) == result.retained_way_count,
            "config_id": policy.config_id,
            "input_osm_sha256": source_hash,
            "permission_expectations": result.permission_expectations,
            "profile": policy.profile,
            "retained_way_count": result.retained_way_count,
        },
        permission_expectations_path,
    )
    _write_json(
        {
            "config_id": policy.config_id,
            "criticality_source_sha256": (
                sha256_file(criticality_source_path)
                if criticality_source_path is not None
                else None
            ),
            "group_definitions": {
                "lanes": ["highway", "oneway_status"],
                "maxspeed": ["highway"],
            },
            "input_extent": "fixed_input_osm_xml",
            "input_osm_sha256": source_hash,
            "sample_unit": "osm_way_count",
            "thresholds": {
                "lanes": {
                    "minimum_mode_share": policy.lane_imputation_minimum_mode_share,
                    "minimum_sample_size": policy.lane_imputation_minimum_sample_size,
                },
                "maxspeed": {
                    "minimum_mode_share": policy.speed_imputation_minimum_mode_share,
                    "minimum_sample_size": policy.speed_imputation_minimum_sample_size,
                },
            },
            "groups": {
                attribute: {
                    group: _mode_payload(decision)
                    for group, decision in decisions.items()
                }
                for attribute, decisions in result.imputation_summary.items()
            },
        },
        imputation_summary_path,
    )
    if result.blockers:
        output_path.unlink(missing_ok=True)
        preview = "; ".join(result.blockers[:5])
        suffix = (
            ""
            if len(result.blockers) <= 5
            else f"; +{len(result.blockers) - 5} more"
        )
        raise ResolutionError(f"pre-netconvert materialization gate failed: {preview}{suffix}")
    _write_tree(result.tree, output_path)
    return result


def _load_criticality(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    _relative_repository_path(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["osm_way_id", "criticality"]:
            raise ValueError("criticality CSV columns must be osm_way_id,criticality")
        rows = list(reader)
    result = {row["osm_way_id"]: row["criticality"] for row in rows}
    if len(result) != len(rows):
        raise ValueError("criticality CSV contains duplicate osm_way_id")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve governed OSM XML attributes before netconvert"
    )
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    parser.add_argument("--input-osm", required=True, type=Path)
    parser.add_argument("--output-osm", required=True, type=Path)
    parser.add_argument("--audit-csv", required=True, type=Path)
    parser.add_argument("--permission-expectations-json", required=True, type=Path)
    parser.add_argument("--imputation-summary-json", required=True, type=Path)
    parser.add_argument("--criticality-csv", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policy = load_policy(args.profile)
    result = resolve_file(
        args.input_osm,
        args.output_osm,
        args.audit_csv,
        args.permission_expectations_json,
        args.imputation_summary_json,
        policy,
        criticality_by_way=_load_criticality(args.criticality_csv),
        criticality_source_path=args.criticality_csv,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "config_id": policy.config_id,
                "profile": policy.profile,
                "retained_way_count": result.retained_way_count,
                "excluded_way_count": result.excluded_way_count,
                "audit_rows": len(result.audit_rows),
                "input_osm": _relative_repository_path(args.input_osm),
                "output_osm": _relative_repository_path(args.output_osm),
                "output_sha256": sha256_file(args.output_osm),
                "audit_csv": _relative_repository_path(args.audit_csv),
                "audit_sha256": sha256_file(args.audit_csv),
                "permission_expectations_json": _relative_repository_path(
                    args.permission_expectations_json
                ),
                "permission_expectations_sha256": sha256_file(
                    args.permission_expectations_json
                ),
                "imputation_summary_json": _relative_repository_path(
                    args.imputation_summary_json
                ),
                "imputation_summary_sha256": sha256_file(
                    args.imputation_summary_json
                ),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
