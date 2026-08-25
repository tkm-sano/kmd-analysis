"""Production directional-lane resolution for v17 Directed Segments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema

from traffic_simulation.network.directed_segments_v17 import (
    _governed_highways,
    build_production_artifact as build_directed_segment_artifact,
    normalize_oneway,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIGURATION_ID = "ota_ward_sumo_network_v17"
ASSUMPTION_ID = "BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"
LANES2_FORMAL_RULE_ID = "OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1"
ONEWAY_ROAD_LANE_VECTOR_RULE_ID = "OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1"
SHARED_SINGLE_LANE_RULE_ID = "OSM_BIDIRECTIONAL_TOTAL_1_TO_SHARED_SINGLE_V1"
SHARED_SINGLE_LANE_DECISION_ID = (
    "DEC-P13-LANE-BIDIRECTIONAL-SHARED-SINGLE-LANE-001"
)
SHARED_SINGLE_LANE_DECISION_VERSION = "1.0.0"
SHARED_SINGLE_LANE_KIND = "shared_bidirectional_single_moving_lane"
SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE = (
    "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
)
SHARED_SINGLE_LANE_PREDICATE_VERSION = "1.0.0"
SHARED_SINGLE_LANE_SOURCE_SCHEMA = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "shared_lane_source_semantic_v17.schema.json"
)
SHARED_SINGLE_LANE_ATTEMPT_SCHEMA = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "shared_lane_materialization_attempt_v17.schema.json"
)
MOTORIZED_ONEWAY_CONDITIONAL_BASE_KEYS = frozenset(
    {
        "oneway",
        "oneway:vehicle",
        "oneway:motor_vehicle",
        "oneway:motorcar",
        "oneway:goods",
        "oneway:hgv",
        "oneway:psv",
        "oneway:bus",
        "oneway:taxi",
        "oneway:motorcycle",
    }
)
APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS = frozenset(
    {"turn:lanes", "destination:lanes", "destination:ref:lanes"}
)
COUNT_KEYS = {"lanes", "lanes:forward", "lanes:backward", "lanes:both_ways"}
INTEGER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)$")


class DirectionalLaneError(ValueError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _count(tags: Mapping[str, str], key: str, *, allow_zero: bool) -> int | None:
    if key not in tags:
        return None
    raw = tags[key].strip()
    if INTEGER_PATTERN.fullmatch(raw) is None:
        raise DirectionalLaneError(
            f"{key} is not a canonical integer: {tags[key]!r}",
            stop_code="LANE_COUNT_INVALID",
            status="invalid",
        )
    value = int(raw)
    if value < 0 or (value == 0 and not allow_zero):
        raise DirectionalLaneError(
            f"{key} must be a positive moving-lane count",
            stop_code="LANE_COUNT_INVALID",
            status="invalid",
        )
    return value


def validate_lane_vector(
    directional_lane_count: int, lane_vector: Sequence[str]
) -> list[str]:
    if directional_lane_count <= 0:
        raise DirectionalLaneError(
            "directional lane count must be positive",
            stop_code="LANE_COUNT_INVALID",
            status="invalid",
        )
    values = list(lane_vector)
    if len(values) != directional_lane_count:
        raise DirectionalLaneError(
            f"lane vector length {len(values)} differs from {directional_lane_count}",
            stop_code="LANE_VECTOR_LENGTH_MISMATCH",
            status="conflict",
        )
    if not all(isinstance(item, str) for item in values):
        raise DirectionalLaneError(
            "lane vector entries must be strings",
            stop_code="LANE_VECTOR_LENGTH_MISMATCH",
            status="conflict",
        )
    return values


def _has_lane_conditional(tags: Mapping[str, str]) -> bool:
    return any("lanes" in key.split(":") and "conditional" in key.split(":") for key in tags)


def _vector_tags(tags: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in tags.items()
        if key not in COUNT_KEYS and "lanes" in key.split(":")
    }


def _source_lane_tags(tags: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in sorted(tags.items())
        if key in COUNT_KEYS or "lanes" in key.split(":")
    }


def _asserted(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in {"", "0", "false", "no"}


def _has_directional_operation_conditional(tags: Mapping[str, str]) -> bool:
    return any(
        key.endswith(":conditional")
        and key[: -len(":conditional")] in MOTORIZED_ONEWAY_CONDITIONAL_BASE_KEYS
        for key in tags
    )


def _has_reversible_or_alternating_operation(tags: Mapping[str, str]) -> bool:
    if tags.get("oneway", "").strip().lower() in {"reversible", "alternating"}:
        return True
    return any(
        any(token in {"reversible", "alternating"} for token in key.split(":"))
        and _asserted(value)
        for key, value in tags.items()
    )


def _is_current_governed_highway(tags: Mapping[str, str]) -> bool:
    return (
        tags.get("highway") in _governed_highways()
        and tags.get("highway") not in {"construction", "proposed"}
        and not _asserted(tags.get("construction"))
        and not _asserted(tags.get("proposed"))
    )


def _is_formal_shared_single_lane_rule_applicable(
    tags: Mapping[str, str],
    *,
    profile: str,
    canonical_oneway: str,
    total: int | None,
    forward: int | None,
    backward: int | None,
    both: int | None,
) -> bool:
    return (
        profile == "formal"
        and _is_current_governed_highway(tags)
        and canonical_oneway == "no"
        and total == 1
        and forward is None
        and backward is None
        and both is None
        and not _has_directional_operation_conditional(tags)
        and not _has_reversible_or_alternating_operation(tags)
        and not _has_lane_conditional(tags)
        and not _vector_tags(tags)
    )


def is_formal_shared_single_lane_candidate(tags: Mapping[str, str]) -> bool:
    """Return the approved strict source predicate without using Way IDs."""

    try:
        direction = normalize_oneway(tags)
        total = _count(tags, "lanes", allow_zero=False)
        forward = _count(tags, "lanes:forward", allow_zero=True)
        backward = _count(tags, "lanes:backward", allow_zero=True)
        both = _count(tags, "lanes:both_ways", allow_zero=True)
    except (DirectionalLaneError, KeyError, ValueError):
        return False
    return _is_formal_shared_single_lane_rule_applicable(
        tags,
        profile="formal",
        canonical_oneway=direction["canonical_oneway"],
        total=total,
        forward=forward,
        backward=backward,
        both=both,
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _stable_id(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


@lru_cache(maxsize=2)
def _schema(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(value)
    return value


def _validate_schema(value: Mapping[str, Any], path: Path) -> None:
    jsonschema.Draft202012Validator(_schema(path)).validate(value)


def _is_formal_bidirectional_lanes2_rule_applicable(
    tags: Mapping[str, str],
    *,
    profile: str,
    total: int | None,
    forward: int | None,
    backward: int | None,
    both: int | None,
) -> bool:
    return (
        profile == "formal"
        and total == 2
        and forward is None
        and backward is None
        and both is None
        and not _has_lane_conditional(tags)
    )


def _approved_oneway_road_lane_vector_count(
    tags: Mapping[str, str], *, profile: str
) -> int | None:
    if profile != "formal" or _has_lane_conditional(tags):
        return None
    field_counts = {
        len(tags[key].split("|"))
        for key in APPROVED_ONEWAY_ROAD_LANE_VECTOR_KEYS
        if key in tags
    }
    if len(field_counts) != 1:
        return None
    return field_counts.pop()


def _resolve_vectors(
    tags: Mapping[str, str],
    *,
    canonical_oneway: str,
    counts: Mapping[str, int],
) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {
        direction: {} for direction in ("forward", "backward") if direction in counts
    }
    active = "backward" if canonical_oneway == "-1" else "forward"
    for key, raw in sorted(_vector_tags(tags).items()):
        if key.endswith(":forward"):
            direction = "forward"
        elif key.endswith(":backward"):
            direction = "backward"
        elif canonical_oneway in {"yes", "-1"}:
            direction = active
        else:
            raise DirectionalLaneError(
                f"unsuffixed lane vector is ambiguous on a bidirectional Way: {key}",
                stop_code="LANE_DIRECTIONAL_ALLOCATION_MISSING",
                status="unresolved",
            )
        if direction not in counts:
            if any(raw.split("|")):
                raise DirectionalLaneError(
                    f"lane vector targets inactive direction: {key}",
                    stop_code="LANE_COUNT_CONFLICT",
                    status="conflict",
                )
            continue
        result[direction][key] = validate_lane_vector(
            counts[direction], raw.split("|")
        )
    return result


def resolve_directional_lanes(
    tags: Mapping[str, str], *, profile: str
) -> dict[str, Any]:
    if profile not in {"structural", "formal"}:
        raise DirectionalLaneError(
            f"unknown profile: {profile}",
            stop_code="LANE_COUNT_INVALID",
            status="invalid",
        )
    direction = normalize_oneway(tags)
    oneway = direction["canonical_oneway"]
    total = _count(tags, "lanes", allow_zero=False)
    forward = _count(tags, "lanes:forward", allow_zero=True)
    backward = _count(tags, "lanes:backward", allow_zero=True)
    both = _count(tags, "lanes:both_ways", allow_zero=True)
    assumptions: list[str] = []
    rule_ids: list[str] = []

    if oneway in {"yes", "-1"}:
        active = "forward" if oneway == "yes" else "backward"
        inactive = "backward" if active == "forward" else "forward"
        directional = {"forward": forward, "backward": backward}
        inactive_value = directional[inactive]
        if inactive_value not in {None, 0}:
            raise DirectionalLaneError(
                f"inactive {inactive} direction has {inactive_value} moving lanes",
                stop_code="LANE_COUNT_CONFLICT",
                status="conflict",
            )
        if both not in {None, 0}:
            raise DirectionalLaneError(
                "one-way Way cannot contain lanes:both_ways",
                stop_code="LANE_COUNT_CONFLICT",
                status="conflict",
            )
        active_count = directional[active]
        if active_count == 0:
            raise DirectionalLaneError(
                f"active {active} direction has zero moving lanes",
                stop_code="LANE_COUNT_INVALID",
                status="invalid",
            )
        if active_count is not None and total is not None and active_count != total:
            raise DirectionalLaneError(
                "one-way total and active directional lane counts disagree",
                stop_code="LANE_COUNT_CONFLICT",
                status="conflict",
            )
        if active_count is None:
            if total is None:
                active_count = _approved_oneway_road_lane_vector_count(
                    tags, profile=profile
                )
                if active_count is None:
                    raise DirectionalLaneError(
                        "one-way moving-lane count is missing",
                        stop_code="LANE_DIRECTIONAL_ALLOCATION_MISSING",
                        status="unresolved",
                    )
                origin = "rule_derived"
                rule_ids = [ONEWAY_ROAD_LANE_VECTOR_RULE_ID]
            else:
                active_count = total
                origin = "rule_derived"
                rule_ids = ["OSM_ONEWAY_TOTAL_TO_ACTIVE_DIRECTION"]
        else:
            origin = "source_explicit"
        counts = {active: active_count}
        effective_total = total if total is not None else active_count
        both_value = 0
    else:
        if forward == 0 or backward == 0:
            raise DirectionalLaneError(
                "bidirectional directions require positive moving-lane counts",
                stop_code="LANE_COUNT_INVALID",
                status="invalid",
            )
        if forward is not None and backward is not None:
            both_value = both or 0
            resolved_total = forward + backward + both_value
            if total is not None and total != resolved_total:
                raise DirectionalLaneError(
                    "total does not equal forward + backward + both_ways",
                    stop_code="LANE_COUNT_CONFLICT",
                    status="conflict",
                )
            counts = {"forward": forward, "backward": backward}
            effective_total = total if total is not None else resolved_total
            origin = "source_explicit"
        elif forward is not None or backward is not None or both is not None:
            raise DirectionalLaneError(
                "formal directional allocation is incomplete; arithmetic complement is prohibited",
                stop_code="LANE_DIRECTIONAL_ALLOCATION_MISSING",
                status="unresolved",
            )
        elif (
            profile == "structural"
            and total is not None
            and total > 1
            and total % 2 == 0
            and not _has_lane_conditional(tags)
        ):
            counts = {"forward": total // 2, "backward": total // 2}
            effective_total = total
            both_value = 0
            origin = "model_assumed"
            assumptions = [ASSUMPTION_ID]
        elif _is_formal_shared_single_lane_rule_applicable(
            tags,
            profile=profile,
            canonical_oneway=oneway,
            total=total,
            forward=forward,
            backward=backward,
            both=both,
        ):
            return {
                "resolution_status": "resolved",
                "value_origin": "rule_derived",
                "effective_value": {
                    "kind": SHARED_SINGLE_LANE_KIND,
                    "physical_moving_lane_count": 1,
                    "usable_source_directions": ["forward", "backward"],
                    "dedicated_moving_lane_count": {
                        "forward": 0,
                        "backward": 0,
                    },
                },
                "rule_ids": [SHARED_SINGLE_LANE_RULE_ID],
                "decision_id": SHARED_SINGLE_LANE_DECISION_ID,
                "decision_version": SHARED_SINGLE_LANE_DECISION_VERSION,
                "assumption_ids": [],
                "formal_eligible": True,
                "lane_vectors": {},
                "source_lane_tags": _source_lane_tags(tags),
                "source_observations": [
                    {"source_key": "lanes", "source_value": tags["lanes"]},
                    {
                        "source_key": "oneway",
                        "source_value": direction["source_value"],
                    },
                ],
                "oneway_provenance": direction,
                "stop_code": None,
            }
        elif _is_formal_bidirectional_lanes2_rule_applicable(
            tags,
            profile=profile,
            total=total,
            forward=forward,
            backward=backward,
            both=both,
        ):
            counts = {"forward": 1, "backward": 1}
            effective_total = 2
            both_value = 0
            origin = "rule_derived"
            rule_ids = [LANES2_FORMAL_RULE_ID]
        else:
            raise DirectionalLaneError(
                "directional moving-lane allocation is missing",
                stop_code="LANE_DIRECTIONAL_ALLOCATION_MISSING",
                status="unresolved",
            )

    vectors = _resolve_vectors(tags, canonical_oneway=oneway, counts=counts)
    return {
        "resolution_status": "resolved",
        "value_origin": origin,
        "effective_value": {
            "total": effective_total,
            "forward": counts.get("forward", 0),
            "backward": counts.get("backward", 0),
            "both_ways": both_value,
        },
        "rule_ids": rule_ids,
        "assumption_ids": assumptions,
        "formal_eligible": origin != "model_assumed",
        "lane_vectors": vectors,
        "source_lane_tags": _source_lane_tags(tags),
        "stop_code": None,
    }


def materialize_segment_lanes(
    segment: Mapping[str, Any], resolution: Mapping[str, Any]
) -> dict[str, Any]:
    direction = str(segment["source_direction"])
    count = int(resolution["effective_value"][direction])
    if count <= 0:
        raise DirectionalLaneError(
            f"Directed Segment has no resolved lanes: {segment['directed_segment_id']}",
            stop_code="LANE_COUNT_INVALID",
            status="invalid",
        )
    vectors = resolution["lane_vectors"].get(direction, {})
    lanes = []
    for position in range(count):
        lanes.append(
            {
                "lane_position": position,
                "sumo_lane_index": count - 1 - position,
                "source_vector_values": {
                    key: values[position] for key, values in sorted(vectors.items())
                },
            }
        )
    return {
        "directed_segment_id": segment["directed_segment_id"],
        "source_way_id": segment["source_way_id"],
        "source_direction": direction,
        "moving_lane_count": count,
        "value_origin": resolution["value_origin"],
        "rule_ids": list(resolution["rule_ids"]),
        "assumption_ids": list(resolution["assumption_ids"]),
        "formal_eligible": resolution["formal_eligible"],
        "lanes": lanes,
    }


def _is_shared_single_lane_resolution(resolution: Mapping[str, Any]) -> bool:
    effective = resolution.get("effective_value")
    return isinstance(effective, Mapping) and effective.get("kind") == SHARED_SINGLE_LANE_KIND


def _shared_source_semantic_record(
    *,
    source_way_id: int,
    resolution: Mapping[str, Any],
    profile: str,
    population_version: str,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    record_key = {
        "configuration_id": CONFIGURATION_ID,
        "population_version": population_version,
        "profile": profile,
        "source_way_id": source_way_id,
        "attribute_name": "lane_semantics",
        "semantic_kind": SHARED_SINGLE_LANE_KIND,
    }
    record = {
        "schema_version": 17,
        "configuration_id": CONFIGURATION_ID,
        "population_version": population_version,
        "profile": profile,
        "record_id": _stable_id(record_key),
        "source_way_id": source_way_id,
        "attribute_name": "lane_semantics",
        "resolution_status": "resolved",
        "value_origin": "rule_derived",
        "effective_value": dict(resolution["effective_value"]),
        "rule_ids": [SHARED_SINGLE_LANE_RULE_ID],
        "decision_id": SHARED_SINGLE_LANE_DECISION_ID,
        "decision_version": SHARED_SINGLE_LANE_DECISION_VERSION,
        "source_observations": list(resolution["source_observations"]),
        "oneway_provenance": dict(resolution["oneway_provenance"]),
        "source": dict(source),
        "source_lane_tags": dict(resolution["source_lane_tags"]),
        "provenance": {
            "strict_predicate_version": SHARED_SINGLE_LANE_PREDICATE_VERSION,
            "source_rewrite": False,
            "access_permission_effect": "none",
            "sumo_behavior_approved": False,
        },
        "stop_code": None,
        "review_required": False,
    }
    _validate_schema(record, SHARED_SINGLE_LANE_SOURCE_SCHEMA)
    return record


def _shared_materialization_attempt(
    *,
    source_semantic_record: Mapping[str, Any],
    segments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    child_ids = sorted(str(item["directed_segment_id"]) for item in segments)
    attempt_key = {
        "source_semantic_record_id": source_semantic_record["record_id"],
        "target_system": "SUMO",
        "target_version": "1.24.0",
        "stage": "phase_5B_target_lane_materialization",
    }
    attempt = {
        "schema_version": 17,
        "record_id": _stable_id(attempt_key),
        "configuration_id": CONFIGURATION_ID,
        "population_version": source_semantic_record["population_version"],
        "profile": source_semantic_record["profile"],
        "source_semantic_record_id": source_semantic_record["record_id"],
        "source_way_id": source_semantic_record["source_way_id"],
        "child_directed_segment_ids": child_ids,
        "target": {
            "system": "SUMO",
            "version": "1.24.0",
            "stage": "phase_5B_target_lane_materialization",
        },
        "materialization_status": "valid_but_unsupported",
        "stop_code": SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
        "reason": "no approved behaviorally valid shared-physical-lane materializer",
        "decision_id": SHARED_SINGLE_LANE_DECISION_ID,
        "decision_version": SHARED_SINGLE_LANE_DECISION_VERSION,
        "rule_ids": [SHARED_SINGLE_LANE_RULE_ID],
        "missing_contracts": [
            "entry_arbitration",
            "deadlock_prevention",
            "passing_place",
            "junction_connection",
        ],
        "review_required": True,
        "acceptance_blocking": True,
        "formal_exclusion": False,
    }
    _validate_schema(attempt, SHARED_SINGLE_LANE_ATTEMPT_SCHEMA)
    return attempt


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


def build_lane_production_artifact(
    input_path: Path, *, profile: str
) -> dict[str, Any]:
    directed = build_directed_segment_artifact(input_path)
    tags_by_way = _source_way_tags(input_path)
    segments_by_way: dict[int, list[Mapping[str, Any]]] = {}
    for segment in directed["directed_segments"]:
        segments_by_way.setdefault(int(segment["source_way_id"]), []).append(segment)

    resolutions: list[dict[str, Any]] = []
    source_semantic_records: list[dict[str, Any]] = []
    materialization_attempts: list[dict[str, Any]] = []
    segment_lanes: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for way_id in sorted(segments_by_way):
        try:
            resolution = resolve_directional_lanes(tags_by_way[way_id], profile=profile)
        except (DirectionalLaneError, KeyError) as error:
            if isinstance(error, DirectionalLaneError):
                status, stop_code = error.status, error.stop_code
            else:
                status, stop_code = "invalid", "LANE_COUNT_INVALID"
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": status,
                    "stop_code": stop_code,
                    "message": str(error),
                }
            )
            continue

        resolutions.append({"source_way_id": way_id, **resolution})
        if _is_shared_single_lane_resolution(resolution):
            source_record = _shared_source_semantic_record(
                source_way_id=way_id,
                resolution=resolution,
                profile=profile,
                population_version=directed["population_version"],
                source=directed["source"],
            )
            source_semantic_records.append(source_record)
            attempt = _shared_materialization_attempt(
                source_semantic_record=source_record,
                segments=segments_by_way[way_id],
            )
            materialization_attempts.append(attempt)
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": "valid_but_unsupported",
                    "stop_code": SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
                    "message": attempt["reason"],
                    "materialization_attempt_id": attempt["record_id"],
                    "source_semantic_record_id": source_record["record_id"],
                    "child_directed_segment_ids": attempt[
                        "child_directed_segment_ids"
                    ],
                    "decision_id": SHARED_SINGLE_LANE_DECISION_ID,
                    "decision_version": SHARED_SINGLE_LANE_DECISION_VERSION,
                    "rule_ids": [SHARED_SINGLE_LANE_RULE_ID],
                    "acceptance_blocking": True,
                    "formal_exclusion": False,
                }
            )
            continue

        try:
            segment_lanes.extend(
                materialize_segment_lanes(segment, resolution)
                for segment in segments_by_way[way_id]
            )
        except (DirectionalLaneError, KeyError) as error:
            if isinstance(error, DirectionalLaneError):
                status, stop_code = error.status, error.stop_code
            else:
                status, stop_code = "invalid", "LANE_COUNT_INVALID"
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": status,
                    "stop_code": stop_code,
                    "message": str(error),
                }
            )
    segment_lanes.sort(key=lambda item: item["directed_segment_id"])
    source_semantic_records.sort(key=lambda item: item["record_id"])
    materialization_attempts.sort(key=lambda item: item["record_id"])
    canonical_payload = json.dumps(
        {
            "resolutions": resolutions,
            "source_semantic_records": source_semantic_records,
            "materialization_attempts": materialization_attempts,
            "segment_lanes": segment_lanes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    simulation_blockers = sum(
        item["stop_code"] == SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE
        for item in blockers
    )
    source_blockers = len(blockers) - simulation_blockers
    return {
        "schema_version": 17,
        "artifact_type": "directional_lane_production_collection",
        "configuration_id": CONFIGURATION_ID,
        "population_version": directed["population_version"],
        "profile": profile,
        "source": directed["source"],
        "directed_segment_semantic_sha256": directed["semantic_sha256"],
        "lane_order": "left_to_right_in_travel_direction",
        "sumo_lane_index_formula": "n - 1 - p",
        "resolutions": resolutions,
        "source_semantic_records": source_semantic_records,
        "materialization_attempts": materialization_attempts,
        "segment_lanes": segment_lanes,
        "blockers": blockers,
        "upstream_blockers": directed["blockers"],
        "counts": {
            "source_ways": len(segments_by_way),
            "resolved_source_ways": len(resolutions),
            "directed_segments_with_lanes": len(segment_lanes),
            "directional_lanes": sum(
                len(item["lanes"]) for item in segment_lanes
            ),
            "lane_blockers": len(blockers),
            "source_semantic_resolved": len(resolutions),
            "source_semantic_blockers": source_blockers,
            "canonical_representation_resolved": len(resolutions),
            "canonical_representation_blockers": source_blockers,
            "simulation_materialization_blockers": simulation_blockers,
            "overall_acceptance_blockers": len(blockers),
            "shared_source_semantic_records": len(source_semantic_records),
            "materialization_attempts": len(materialization_attempts),
            "upstream_blockers": len(directed["blockers"]),
        },
        "blocker_stop_codes": dict(
            sorted(Counter(item["stop_code"] for item in blockers).items())
        ),
        "semantic_sha256": hashlib.sha256(canonical_payload).hexdigest(),
    }


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite directional-lane artifact: {output_path}")
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
        description="Resolve v17 directional lanes onto production Directed Segments."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = build_lane_production_artifact(args.input, profile=args.profile)
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 1 if artifact["blockers"] or artifact["upstream_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
