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
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.directed_segments_v17 import (
    build_production_artifact as build_directed_segment_artifact,
    normalize_oneway,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIGURATION_ID = "ota_ward_sumo_network_v17"
ASSUMPTION_ID = "BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1"
COUNT_KEYS = {"lanes", "lanes:forward", "lanes:backward", "lanes:both_ways"}
INTEGER_PATTERN = re.compile(r"^[0-9]+$")


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
                raise DirectionalLaneError(
                    "one-way moving-lane count is missing",
                    stop_code="LANE_DIRECTIONAL_ALLOCATION_MISSING",
                    status="unresolved",
                )
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
    segment_lanes: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for way_id in sorted(segments_by_way):
        try:
            resolution = resolve_directional_lanes(tags_by_way[way_id], profile=profile)
            resolutions.append({"source_way_id": way_id, **resolution})
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
    canonical_payload = json.dumps(
        {"resolutions": resolutions, "segment_lanes": segment_lanes},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
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
