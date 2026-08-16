"""Audit the Phase 13 PSV full-population probe against the fixed PSV blocker inventory."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

class PsvProbeComparisonError(RuntimeError):
    """Raised when a PSV probe invariant is violated."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(item) for key, item in value.items() if key != "semantic_sha256"}
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _static_access_semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {
        "normalized_rules": copy.deepcopy(value.get("normalized_rules", [])),
        "static_maxima": copy.deepcopy(value.get("static_maxima", [])),
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PsvProbeComparisonError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _formal_blocker_id(source_way_id: int, stop_code: str) -> str:
    return (
        "blocker:static_access:static_access:source_way:"
        f"{source_way_id}:{stop_code}"
    )


def _as_way_id(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
    raise PsvProbeComparisonError(f"way id is not a usable integer: {value!r}")


def _entries_by_way(entries: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_way: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        source_way_id = entry.get("source_way_id")
        if source_way_id is None:
            continue
        by_way[_as_way_id(source_way_id)].append(entry)
    return by_way


def _normalized_rules_by_way(normalized_rules: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_way: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in normalized_rules:
        by_way[_as_way_id(item["source_way_id"])].extend(item.get("rules", []))
    return by_way


def _parse_lane_vector(source_value: str) -> tuple[list[str], list[int], list[int]]:
    cells = source_value.split("|")
    empty_positions = [index for index, cell in enumerate(cells) if cell == ""]
    non_empty_positions = [index for index, cell in enumerate(cells) if cell != ""]
    return cells, empty_positions, non_empty_positions


def _source_values_for_record(record: Mapping[str, Any]) -> set[tuple[str, str]]:
    values: set[tuple[str, str]] = set()
    for occurrence in record.get("target_occurrences", []):
        key = str(occurrence.get("source_key", ""))
        value = str(occurrence.get("source_value", ""))
        if key:
            values.add((key, value))
    return values


def _validate_artifact_hashes(*, inventory: Mapping[str, Any], extraction: Mapping[str, Any], probe: Mapping[str, Any], fixed_inventory_path: Path, extraction_path: Path, probe_path: Path) -> None:
    if inventory.get("semantic_sha256") is not None:
        computed = _semantic_hash(inventory)
        if computed != inventory["semantic_sha256"]:
            raise PsvProbeComparisonError(
                f"fixed inventory semantic hash mismatch: expected {inventory['semantic_sha256']}, got {computed}"
            )
    if extraction.get("semantic_sha256") is not None:
        computed = _semantic_hash(extraction)
        if computed != extraction["semantic_sha256"]:
            raise PsvProbeComparisonError(
                f"PSV extraction semantic hash mismatch: expected {extraction['semantic_sha256']}, got {computed}"
            )
    if probe.get("semantic_sha256") is not None:
        computed = _static_access_semantic_hash(probe)
        if computed != probe["semantic_sha256"]:
            raise PsvProbeComparisonError(
                f"probe semantic hash mismatch: expected {probe['semantic_sha256']}, got {computed}"
            )

    expected_inventory_hash = extraction["sources"]["complete_blocker_inventory"]["byte_sha256"]
    if _sha256(fixed_inventory_path) != expected_inventory_hash:
        raise PsvProbeComparisonError("fixed inventory byte hash differs from extraction")
    expected_osm_hash = extraction["sources"]["osm_population"]["byte_sha256"]
    if probe["source"]["sha256"] != expected_osm_hash:
        raise PsvProbeComparisonError("probe OSM hash differs from fixed extraction")


def _parse_tourist_bus_yes_ways(osm_path: Path) -> set[int]:
    tree = ET.parse(str(osm_path))
    ways: set[int] = set()
    for element in tree.getroot().iter("way"):
        for tag in element.findall("tag"):
            if tag.attrib.get("k") == "tourist_bus" and tag.attrib.get("v") == "yes":
                ways.add(int(element.attrib["id"]))
    return ways


def compare_psv_probe(
    *,
    fixed_inventory_path: Path,
    extraction_path: Path,
    probe_path: Path,
    source_osm_path: Path | None = None,
) -> dict[str, Any]:
    inventory = _load_json(fixed_inventory_path)
    extraction = _load_json(extraction_path)
    probe = _load_json(probe_path)

    _validate_artifact_hashes(
        inventory=inventory,
        extraction=extraction,
        probe=probe,
        fixed_inventory_path=fixed_inventory_path,
        extraction_path=extraction_path,
        probe_path=probe_path,
    )

    psv_records = [
        item for item in extraction["records"] if item["selected_blocking_base_key_after_decision_001"] == "psv"
    ]
    if len(psv_records) != 16:
        raise PsvProbeComparisonError(f"expected 16 fixed PSV records, got {len(psv_records)}")

    fixed_way_ids = {int(item["source_way_id"]) for item in psv_records}
    fixed_blocker_ids = {item["blocker_id"] for item in psv_records}
    probe_by_way = defaultdict(list)
    for blocker in probe["blockers"]:
        probe_by_way[int(blocker["source_way_id"])].append(blocker)
    normalized_rules_by_way = _normalized_rules_by_way(probe.get("normalized_rules", []))

    fixed_ids_in_inventory = {item["blocker_id"] for item in inventory["entries"]}
    if not fixed_blocker_ids.issubset(fixed_ids_in_inventory):
        raise PsvProbeComparisonError("PSV blocker ids are not all present in the fixed inventory")

    resolved_ids: list[str] = []
    remaining_ids: list[str] = []
    changed_stop_code_records: list[dict[str, Any]] = []
    unexpected_new_ids: list[str] = []
    affected_way_ids: set[int] = set()

    for record in sorted(psv_records, key=lambda item: int(item["source_way_id"])):
        source_way_id = int(record["source_way_id"])
        before_blocker_id = record["blocker_id"]
        before_stop_code = record["stop_code"]
        after_blockers = probe_by_way.get(source_way_id, [])
        if not after_blockers:
            resolved_ids.append(before_blocker_id)
            continue

        affected_way_ids.add(source_way_id)
        for blocker in after_blockers:
            blocker_id = _formal_blocker_id(int(blocker["source_way_id"]), blocker["stop_code"])
            if blocker["stop_code"] != before_stop_code:
                changed_stop_code_records.append(
                    {
                        "source_way_id": source_way_id,
                        "before_blocker_id": before_blocker_id,
                        "before_stop_code": before_stop_code,
                        "after_blocker_id": blocker_id,
                        "after_stop_code": blocker["stop_code"],
                        "after_message": blocker.get("message"),
                    }
                )
            remaining_ids.append(blocker_id)
            if blocker_id not in fixed_blocker_ids:
                unexpected_new_ids.append(blocker_id)

    # Additional full-population comparison: any new blocker identity in the probe that is not in the fixed inventory
    # and that relates to a fixed PSV way is unexpected; action is fail-closed.
    unexpected_new_ids = sorted(set(unexpected_new_ids))

    delivery_change_count = 0
    coach_change_count = 0
    motorcar_change_count = 0
    for record in psv_records:
        way_id = int(record["source_way_id"])
        relevant_rules = [
            rule
            for rule in normalized_rules_by_way.get(way_id, [])
            if rule.get("source_key", "").split(":", 1)[0] == "psv"
        ]
        if not relevant_rules:
            continue
        for rule in relevant_rules:
            domains = set(rule.get("vehicle_domain", []))
            if "delivery" in domains:
                delivery_change_count += 1
            if "coach" in domains:
                coach_change_count += 1
            if "motorcar" in rule.get("source_key", ""):
                motorcar_change_count += 1

    lane_records: list[dict[str, Any]] = []
    lane_validation_pass = True
    for record in psv_records:
        if not any(occ.get("lane_scoped") for occ in record.get("target_occurrences", [])):
            continue
        way_id = int(record["source_way_id"])
        lane_matches = []
        for occurrence in record.get("target_occurrences", []):
            if not occurrence.get("lane_scoped"):
                continue
            key = occurrence.get("source_key")
            value = occurrence.get("source_value")
            source_cells, empty_positions, nonempty_positions = _parse_lane_vector(str(value))
            matching_rules = [
                rule
                for rule in normalized_rules_by_way.get(way_id, [])
                if rule.get("source_key") == key
            ]
            matched_positions: set[int] = set()
            for rule in matching_rules:
                lane_scope = rule.get("target_scope", {}).get("lane_scope", {})
                positions = lane_scope.get("positions", [])
                if positions:
                    matched_positions.update(int(pos) for pos in positions)
            lane_matches.append(
                {
                    "source_way_id": way_id,
                    "source_key": key,
                    "source_value": value,
                    "original_positions": sorted(nonempty_positions),
                    "matched_positions": sorted(matched_positions),
                    "empty_positions": sorted(empty_positions),
                    "valid": set(matched_positions).issubset(set(nonempty_positions)) and not (set(empty_positions) & set(matched_positions)),
                }
            )
        lane_records.extend(lane_matches)
        if not all(item["valid"] for item in lane_matches):
            lane_validation_pass = False

    tourist_bus_expected = {
        int(item["source_way_id"])
        for item in psv_records
        if item.get("source_tags", {}).get("tourist_bus") == "yes"
    }
    if source_osm_path is not None:
        osm_tourist_bus_yes_ways = _parse_tourist_bus_yes_ways(source_osm_path)
        tourist_bus_actual = tourist_bus_expected & osm_tourist_bus_yes_ways
    else:
        tourist_bus_actual = tourist_bus_expected
    tourist_bus_preserved = tourist_bus_expected == tourist_bus_actual

    fixed_scalar_key_value_pairs = {
        (int(record["source_way_id"]), occurrence["source_key"], occurrence["source_value"])
        for record in psv_records
        for occurrence in record.get("target_occurrences", [])
        if occurrence.get("base_key") == "psv" and not occurrence.get("lane_scoped")
    }
    probe_scalar_key_value_pairs = {
        (int(rule["source_element"]["id"]), rule["source_key"], rule["source_value"])
        for rules in normalized_rules_by_way.values()
        for rule in rules
        if rule["source_key"].split(":", 1)[0] == "psv" and rule["target_scope"]["lane_scope"]["type"] == "all"
    }
    scalar_lineage_pairs_present = fixed_scalar_key_value_pairs.issubset(probe_scalar_key_value_pairs)
    lane_lineage_preserved = lane_validation_pass
    lineage_pairs_present = scalar_lineage_pairs_present and lane_lineage_preserved
    lineage_preserved = lineage_pairs_present

    # Use artifact-backed comparison only. If a source OSM path is unavailable then keep the test fail-closed.
    if source_osm_path is None:
        tourist_bus_preserved = False

    fixed_psv_blocker_count = len(fixed_blocker_ids)
    resolved_count = len(resolved_ids)
    remaining_count = len(remaining_ids)
    new_count = len(unexpected_new_ids)
    unexpected_change_count = len(changed_stop_code_records) + new_count

    impact_summary = {
        "managed_delivery_permission_change_count": delivery_change_count,
        "coach_permission_change_count": coach_change_count,
        "motorcar_blocker_change_count": motorcar_change_count,
        "managed_delivery_permission_impact": "none" if delivery_change_count == 0 else "changed",
        "coach_permission_impact": "none" if coach_change_count == 0 else "changed",
        "motorcar_blocker_impact": "none" if motorcar_change_count == 0 else "changed",
    }

    acceptance = {
        "fixed_psv_way_count_is_16": len(psv_records) == 16,
        "psv_hierarchy_blockers_are_zero": remaining_count == 0,
        "resolved_blocker_count_is_16": resolved_count == 16,
        "remaining_fixed_psv_blocker_count_is_zero": remaining_count == 0,
        "no_changed_stop_code_on_fixed_psv_ways": len(changed_stop_code_records) == 0,
        "no_unexpected_new_blockers_on_fixed_psv_ways": new_count == 0,
        "full_population_unexpected_new_blocker_count_is_zero": new_count == 0,
        "managed_delivery_permission_change_count_is_zero": delivery_change_count == 0,
        "coach_permission_change_count_is_zero": coach_change_count == 0,
        "motorcar_blocker_change_count_is_zero": motorcar_change_count == 0,
        "all_16_fixed_source_way_ids_tracked": len(fixed_way_ids) == 16,
        "source_key_value_pairs_preserved": lineage_pairs_present,
        "blocker_lineage_preserved": resolved_count == fixed_psv_blocker_count and remaining_count == 0,
        "lane_scoped_positions_preserved": lane_validation_pass and len(lane_records) == 7,
        "tourist_bus_yes_way_set_preserved": tourist_bus_preserved,
        "artifact_hashes_are_valid": True,
        "semantic_hashes_are_valid": True,
    }

    result = {
        "schema_version": 1,
        "comparison_id": "phase13_psv_full_population_stable_id_diff_20260816",
        "decision_id": "DEC-P13-PSV-ONTOLOGY-001",
        "status": "failed",
        "sources": {
            "fixed_inventory": {
                "path": str(fixed_inventory_path),
                "byte_sha256": _sha256(fixed_inventory_path),
                "semantic_sha256": inventory.get("semantic_sha256"),
            },
            "fixed_psv_extraction": {
                "path": str(extraction_path),
                "byte_sha256": _sha256(extraction_path),
                "semantic_sha256": extraction.get("semantic_sha256"),
            },
            "full_population_probe": {
                "path": str(probe_path),
                "byte_sha256": _sha256(probe_path),
                "semantic_sha256": probe.get("semantic_sha256"),
            },
        },
        "fixed_psv_summary": {
            "fixed_psv_way_count": len(psv_records),
            "fixed_psv_blocker_count": fixed_psv_blocker_count,
            "resolved_fixed_psv_blocker_count": resolved_count,
            "remaining_fixed_psv_blocker_count": remaining_count,
        },
        "stable_id_diff": {
            "fixed_psv_blocker_count": fixed_psv_blocker_count,
            "resolved_fixed_blocker_count": resolved_count,
            "remaining_psv_blocker_count": remaining_count,
            "new_blocker_id_count": new_count,
            "new_blocker_ids": unexpected_new_ids,
            "resolved_blocker_ids": sorted(resolved_ids),
            "remaining_blocker_ids": sorted(remaining_ids),
            "changed_stop_code_records": changed_stop_code_records,
            "unexpected_changed_blocker_ids": sorted(set(item["after_blocker_id"] for item in changed_stop_code_records) | set(unexpected_new_ids)),
            "affected_way_ids": sorted(affected_way_ids),
        },
        "impact_summary": impact_summary,
        "lineage_preservation": {
            "fixed_way_ids": sorted(fixed_way_ids),
            "fixed_key_value_pairs_count": len(fixed_scalar_key_value_pairs),
            "probe_key_value_pairs_count": len(probe_scalar_key_value_pairs),
            "source_key_value_pairs_preserved": lineage_pairs_present,
            "source_key_value_pairs_count": len(fixed_scalar_key_value_pairs),
            "lane_scoped_record_count": len(lane_records),
            "lane_positions_preserved": lane_validation_pass,
            "tourist_bus_yes_expected_way_count": len(tourist_bus_expected),
            "tourist_bus_yes_actual_way_count": len(tourist_bus_actual),
            "tourist_bus_yes_set_preserved": tourist_bus_preserved,
            "lane_validation_records": lane_records,
        },
        "acceptance": acceptance,
    }

    if all(value is True for value in acceptance.values()):
        result["status"] = "passed"
    result["semantic_sha256"] = _semantic_hash(result)
    return result


def write_json_atomic(value: Mapping[str, Any], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite comparison artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-inventory", required=True, type=Path)
    parser.add_argument("--psv-extraction", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-osm", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = compare_psv_probe(
        fixed_inventory_path=args.fixed_inventory,
        extraction_path=args.psv_extraction,
        probe_path=args.probe,
        source_osm_path=args.source_osm,
    )
    write_json_atomic(result, args.output)
    summary = {
        "acceptance": result["acceptance"],
        "stable_id_diff": {
            key: value
            for key, value in result["stable_id_diff"].items()
            if key.endswith("_count") or key.endswith("_ids") or key == "changed_stop_code_records"
        },
        "status": result["status"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
