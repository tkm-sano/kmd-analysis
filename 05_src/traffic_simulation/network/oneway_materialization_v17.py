"""Materialize approved v17 road direction into an explicit SUMO OSM input.

This module is a conformance bridge.  It does not resolve direction itself and
does not infer direction from width.  The only semantic authority is the
existing v17 ``normalize_oneway`` resolver and its registered rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from typing import Any, Sequence

from traffic_simulation.network.directed_segments_v17 import (
    DirectedSegmentError,
    _governed_highways,
    normalize_oneway,
)


MATERIALIZER_ID = "V17_CANONICAL_ONEWAY_TO_EXPLICIT_OSM_V1"


class OnewayMaterializationError(RuntimeError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _materialize_way(block: str) -> tuple[str, dict[str, Any] | None]:
    try:
        way = ET.fromstring(block)
    except ET.ParseError as error:
        raise OnewayMaterializationError(
            f"invalid OSM Way XML: {error}",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        ) from error
    if way.tag != "way":
        raise OnewayMaterializationError(
            "materialization block is not an OSM Way",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    try:
        way_id = int(way.attrib["id"])
    except (KeyError, ValueError) as error:
        raise OnewayMaterializationError(
            "OSM Way has no canonical positive identifier",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        ) from error
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
    if tags.get("highway") not in _governed_highways():
        return block, None

    try:
        resolution = normalize_oneway(tags)
    except DirectedSegmentError as error:
        raise OnewayMaterializationError(
            f"Way {way_id}: {error}",
            stop_code=error.stop_code,
            status=error.status,
        ) from error

    canonical = resolution["canonical_oneway"]
    oneway_tags = [tag for tag in way.findall("tag") if tag.attrib.get("k") == "oneway"]
    if len(oneway_tags) > 1:
        raise OnewayMaterializationError(
            f"Way {way_id}: duplicate oneway tags",
            stop_code="ONEWAY_VALUE_INVALID",
            status="invalid",
        )
    source_value = resolution["source_value"]
    if not oneway_tags:
        ET.SubElement(way, "tag", {"k": "oneway", "v": canonical})
        action = "inserted"
    elif oneway_tags[0].attrib["v"] != canonical:
        oneway_tags[0].set("v", canonical)
        action = "normalized"
    else:
        action = "already_canonical"

    indentation = block[: len(block) - len(block.lstrip())]
    materialized = indentation + ET.tostring(way, encoding="unicode") + "\n"
    record = {
        "source_way_id": way_id,
        "highway": tags["highway"],
        "source_value": source_value,
        "canonical_oneway": canonical,
        "value_origin": resolution["value_origin"],
        "rule_id": resolution["rule_id"],
        "materialization_action": action,
        "assumption_ids": [],
        "used_width": False,
        "materializer_id": MATERIALIZER_ID,
    }
    return materialized, record


def materialize_osm_oneway(
    source_path: Path | str,
    target_path: Path | str,
    manifest_path: Path | str,
) -> dict[str, Any]:
    """Write a new OSM XML with explicit canonical direction for governed Ways."""

    source = Path(source_path)
    target = Path(target_path)
    manifest = Path(manifest_path)
    if not source.is_file():
        raise OnewayMaterializationError(
            f"source OSM does not exist: {source}",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    if source.resolve() in {target.resolve(), manifest.resolve()}:
        raise OnewayMaterializationError(
            "source OSM is immutable and cannot be an output target",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )
    if target.exists() or manifest.exists():
        raise OnewayMaterializationError(
            "refusing to overwrite an existing materialization artifact",
            stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
            status="invalid",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    records: list[dict[str, Any]] = []
    non_governed = 0
    source_hash_before = _sha256(source)
    in_way = False
    block: list[str] = []
    try:
        with source.open(encoding="utf-8") as input_handle, os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as output_handle:
            for line in input_handle:
                if not in_way:
                    if "<way " not in line:
                        output_handle.write(line)
                        continue
                    in_way = True
                    block = [line]
                else:
                    block.append(line)
                if "</way>" not in line:
                    continue
                materialized, record = _materialize_way("".join(block))
                output_handle.write(materialized)
                if record is None:
                    non_governed += 1
                else:
                    records.append(record)
                in_way = False
                block = []
            if in_way:
                raise OnewayMaterializationError(
                    "unterminated OSM Way",
                    stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
                    status="invalid",
                )
            output_handle.flush()
            os.fsync(output_handle.fileno())

        source_hash_after = _sha256(source)
        if source_hash_after != source_hash_before:
            raise OnewayMaterializationError(
                "source OSM changed during materialization",
                stop_code="DIRECTED_SEGMENT_LINEAGE_INVALID",
                status="invalid",
            )
        records.sort(key=lambda item: item["source_way_id"])
        action_counts = {
            action: sum(record["materialization_action"] == action for record in records)
            for action in ("inserted", "normalized", "already_canonical")
        }
        result: dict[str, Any] = {
            "schema_version": 1,
            "materializer_id": MATERIALIZER_ID,
            "semantic_authority": "attribute_resolution_registries_v17.oneway_rules",
            "source_path": str(source),
            "target_path": str(target),
            "source_sha256": source_hash_before,
            "target_sha256": _sha256(temporary),
            "source_mutated": False,
            "width_direction_inference": False,
            "way_specific_exceptions": False,
            "counts": {
                "governed_ways": len(records),
                **action_counts,
                "non_governed_ways": non_governed,
            },
            "records": records,
        }
        _atomic_json(manifest, result)
        os.replace(temporary, target)
        return result
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    result = materialize_osm_oneway(args.source, args.target, args.manifest)
    print(json.dumps({"counts": result["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
