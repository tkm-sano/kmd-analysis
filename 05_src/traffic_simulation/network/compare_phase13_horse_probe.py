"""Audit the Phase 13 horse full-population probe against fixed blocker IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    default_scenario_context,
    maximal_static_rules_for_tuple,
    normalize_static_access_rules,
)


class HorseProbeComparisonError(RuntimeError):
    """Raised when a fixed-input or horse audit invariant is violated."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HorseProbeComparisonError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _semantic_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _blocker_id(item: Mapping[str, Any]) -> str:
    return (
        "blocker:static_access:static_access:source_way:"
        f"{item['source_way_id']}:{item['stop_code']}"
    )


def _blocked_way_outcome(
    *, source_way_id: int, tags: Mapping[str, str], context: Mapping[str, Any]
) -> dict[str, Any]:
    """Evaluate a currently blocked one-way Way for horse counterfactual parity."""

    if tags.get("oneway") not in {"yes", "-1"} or not tags.get("lanes", "").isdigit():
        raise HorseProbeComparisonError(
            f"blocked horse counterfactual lacks explicit one-way lane count: {source_way_id}"
        )
    direction = "backward" if tags["oneway"] == "-1" else "forward"
    lane_count = int(tags["lanes"])
    try:
        rules = normalize_static_access_rules(
            source_way_id=source_way_id,
            tags=tags,
            lane_counts={direction: lane_count},
        )["rules"]
        outcomes = []
        for lane_position in range(lane_count):
            selected = maximal_static_rules_for_tuple(
                rules,
                direction=direction,
                lane_position=lane_position,
                lane_count=lane_count,
                vehicle_class=context["vehicle_class"],
                context=context,
            )
            outcomes.append(
                {
                    "lane_position": lane_position,
                    "maximal_rule_ids": sorted(item["rule_id"] for item in selected),
                    "effects": sorted({item["effect"] for item in selected}),
                }
            )
        return {"type": "permission", "outcomes": outcomes}
    except StaticAccessError as error:
        return {
            "type": "blocker",
            "status": error.status,
            "stop_code": error.stop_code,
            "message": str(error),
        }


def compare_horse_probe(
    *,
    fixed_inventory_path: Path,
    extraction_path: Path,
    probe_path: Path,
) -> dict[str, Any]:
    inventory = _load_json(fixed_inventory_path)
    extraction = _load_json(extraction_path)
    probe = _load_json(probe_path)

    expected_inventory_hash = extraction["sources"]["complete_blocker_inventory"][
        "byte_sha256"
    ]
    if _sha256(fixed_inventory_path) != expected_inventory_hash:
        raise HorseProbeComparisonError("fixed inventory hash differs from extraction")
    expected_osm_hash = extraction["sources"]["osm_population"]["byte_sha256"]
    if probe["source"]["sha256"] != expected_osm_hash:
        raise HorseProbeComparisonError("probe OSM hash differs from fixed extraction")

    horse_records = [
        item
        for item in extraction["records"]
        if item["selected_blocking_base_key_after_decision_001"] == "horse"
    ]
    if len(horse_records) != 130:
        raise HorseProbeComparisonError(
            f"expected 130 fixed horse records, got {len(horse_records)}"
        )
    if len({item["blocker_id"] for item in horse_records}) != 130:
        raise HorseProbeComparisonError("fixed horse blocker IDs are not unique")

    inventory_ids = {item["blocker_id"] for item in inventory["entries"]}
    fixed_ids = {item["blocker_id"] for item in horse_records}
    if not fixed_ids <= inventory_ids:
        raise HorseProbeComparisonError("horse blocker IDs are not all in fixed inventory")

    blockers_by_way = {
        int(item["source_way_id"]): item for item in probe["blockers"]
    }
    normalized_by_way = {
        int(item["source_way_id"]): item for item in probe["normalized_rules"]
    }
    maxima_by_way: dict[int, list[Mapping[str, Any]]] = {}
    for item in probe["static_maxima"]:
        maxima_by_way.setdefault(int(item["source_way_id"]), []).append(item)

    current_target_ids: set[str] = set()
    transitions: list[dict[str, Any]] = []
    permission_records: list[dict[str, Any]] = []
    unexpected_transitions: list[dict[str, Any]] = []
    changed_tuples: list[dict[str, Any]] = []
    blocked_outcome_changes: list[dict[str, Any]] = []
    preserved_horse_rule_count = 0
    compared_tuple_count = 0

    context = probe.get("managed_scenario_context") or default_scenario_context()
    for fixed in sorted(horse_records, key=lambda item: int(item["source_way_id"])):
        way_id = int(fixed["source_way_id"])
        blocker = blockers_by_way.get(way_id)
        occurrences = fixed["target_occurrences"]
        has_motorcar = any(item["base_key"] == "motorcar" for item in occurrences)
        if blocker is not None:
            current_id = _blocker_id(blocker)
            current_target_ids.add(current_id)
            expected_transition = (
                has_motorcar
                and blocker["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING"
                and "motorcar" in blocker["message"]
            )
            source_tags = fixed["source_tags"]
            expected_context_transition = (
                source_tags.get("motor_vehicle") == "private"
                and blocker["stop_code"] == "ACCESS_CONTEXT_MISSING"
                and "private_authorization" in blocker["message"]
            )
            transition = {
                "source_way_id": way_id,
                "fixed_blocker_id": fixed["blocker_id"],
                "current_blocker_id": current_id,
                "status": (
                    "known_transition_to_motorcar"
                    if expected_transition
                    else (
                        "revealed_missing_private_authorization_context"
                        if expected_context_transition
                        else "unexpected_blocker_transition"
                    )
                ),
                "current_stop_code": blocker["stop_code"],
                "current_message": blocker["message"],
                "source_key": fixed["selected_blocking_source_key_after_decision_001"],
                "source_value": next(
                    item["source_value"]
                    for item in occurrences
                    if item["base_key"] == "horse"
                ),
            }
            transitions.append(transition)
            if not expected_transition and not expected_context_transition:
                unexpected_transitions.append(transition)
            with_horse_outcome = _blocked_way_outcome(
                source_way_id=way_id,
                tags=source_tags,
                context=context,
            )
            without_horse_outcome = _blocked_way_outcome(
                source_way_id=way_id,
                tags={
                    key: value
                    for key, value in source_tags.items()
                    if key.split(":", 1)[0] != "horse"
                },
                context=context,
            )
            same_blocked_outcome = with_horse_outcome == without_horse_outcome
            if not same_blocked_outcome:
                blocked_outcome_changes.append(
                    {
                        "source_way_id": way_id,
                        "with_horse": with_horse_outcome,
                        "without_horse": without_horse_outcome,
                    }
                )
            permission_records.append(
                {
                    "source_way_id": way_id,
                    "status": "not_evaluable_known_motorcar_blocker"
                    if expected_transition
                    else (
                        "not_evaluable_revealed_private_context_blocker"
                        if expected_context_transition
                        else "not_evaluable_unexpected_blocker"
                    ),
                    "with_horse_outcome": with_horse_outcome,
                    "without_horse_outcome": without_horse_outcome,
                    "counterfactual_outcome_unchanged": same_blocked_outcome,
                    "changed_tuple_count": 0,
                }
            )
            continue

        normalized = normalized_by_way.get(way_id)
        if normalized is None:
            raise HorseProbeComparisonError(
                f"horse Way is neither normalized nor blocked: {way_id}"
            )
        rules = normalized["rules"]
        horse_rules = [
            item for item in rules if item["source_key"].split(":", 1)[0] == "horse"
        ]
        if len(horse_rules) != 1 or horse_rules[0]["vehicle_domain"] != []:
            raise HorseProbeComparisonError(
                f"horse source rule was not preserved with empty domain: {way_id}"
            )
        preserved_horse_rule_count += 1
        counterfactual_rules = [item for item in rules if item not in horse_rules]
        way_changed = 0
        maxima_records = maxima_by_way.get(way_id, [])
        lane_counts = Counter(
            item["directed_segment_id"] for item in maxima_records
        )
        for actual in maxima_records:
            selected = maximal_static_rules_for_tuple(
                counterfactual_rules,
                direction=actual["source_direction"],
                lane_position=int(actual["lane_position"]),
                lane_count=lane_counts[actual["directed_segment_id"]],
                vehicle_class=actual["vehicle_class"],
                context=context,
            )
            expected_rule_ids = sorted(item["rule_id"] for item in selected)
            expected_effects = sorted({item["effect"] for item in selected})
            compared_tuple_count += 1
            if (
                expected_rule_ids != actual["maximal_rule_ids"]
                or expected_effects != actual["effects"]
            ):
                way_changed += 1
                changed_tuples.append(
                    {
                        "source_way_id": way_id,
                        "directed_segment_id": actual["directed_segment_id"],
                        "lane_position": actual["lane_position"],
                        "with_horse_rule_ids": actual["maximal_rule_ids"],
                        "without_horse_rule_ids": expected_rule_ids,
                        "with_horse_effects": actual["effects"],
                        "without_horse_effects": expected_effects,
                    }
                )
        permission_records.append(
            {
                "source_way_id": way_id,
                "status": "unchanged" if way_changed == 0 else "changed",
                "compared_tuple_count": len(maxima_records),
                "changed_tuple_count": way_changed,
            }
        )

    horse_message_blockers = [
        item
        for item in probe["blockers"]
        if item["stop_code"] == "ACCESS_VEHICLE_HIERARCHY_MISSING"
        and "horse" in item["message"]
    ]
    new_target_ids = sorted(current_target_ids - fixed_ids)
    resolved_ids = sorted(fixed_ids - current_target_ids)
    result = {
        "schema_version": 1,
        "comparison_id": "phase13_horse_full_population_stable_id_diff_20260815",
        "decision_id": "DEC-P13-HORSE-ONTOLOGY-001",
        "status": "passed",
        "sources": {
            "fixed_inventory": {
                "path": str(fixed_inventory_path),
                "byte_sha256": _sha256(fixed_inventory_path),
                "semantic_sha256": inventory["semantic_sha256"],
            },
            "fixed_horse_extraction": {
                "path": str(extraction_path),
                "byte_sha256": _sha256(extraction_path),
                "semantic_sha256": extraction["semantic_sha256"],
            },
            "full_population_probe": {
                "path": str(probe_path),
                "byte_sha256": _sha256(probe_path),
                "semantic_sha256": probe["semantic_sha256"],
            },
        },
        "probe_counts": probe["counts"],
        "probe_blocker_stop_codes": probe["blocker_stop_codes"],
        "stable_id_diff": {
            "fixed_horse_blocker_count": len(fixed_ids),
            "resolved_fixed_blocker_count": len(resolved_ids),
            "remaining_same_stable_id_count": len(current_target_ids & fixed_ids),
            "known_motorcar_transition_count": sum(
                item["status"] == "known_transition_to_motorcar"
                for item in transitions
            ),
            "revealed_private_context_successor_count": sum(
                item["status"] == "revealed_missing_private_authorization_context"
                for item in transitions
            ),
            "new_blocked_source_way_count": len(
                {item["source_way_id"] for item in transitions}
                - {item["source_way_id"] for item in horse_records}
            ),
            "new_blocker_id_count": len(new_target_ids),
            "unexpected_transition_count": len(unexpected_transitions),
            "remaining_horse_hierarchy_blocker_count": len(horse_message_blockers),
            "resolved_fixed_blocker_ids": resolved_ids,
            "remaining_fixed_blocker_ids": sorted(current_target_ids & fixed_ids),
            "new_blocker_ids": new_target_ids,
            "transitions": transitions,
        },
        "permission_diff": {
            "managed_vehicle_class": context["vehicle_class"],
            "evaluable_way_count": sum(
                item["status"] in {"unchanged", "changed"}
                for item in permission_records
            ),
            "known_unevaluable_motorcar_way_count": sum(
                item["status"] == "not_evaluable_known_motorcar_blocker"
                for item in permission_records
            ),
            "known_unevaluable_private_context_way_count": sum(
                item["status"] == "not_evaluable_revealed_private_context_blocker"
                for item in permission_records
            ),
            "compared_tuple_count": compared_tuple_count,
            "changed_way_count": sum(
                item["status"] == "changed" for item in permission_records
            ),
            "changed_tuple_count": len(changed_tuples),
            "blocked_counterfactual_same_count": sum(
                item.get("counterfactual_outcome_unchanged") is True
                for item in permission_records
            ),
            "blocked_counterfactual_changed_count": len(blocked_outcome_changes),
            "unexpected_permission_change_count": len(changed_tuples)
            + len(blocked_outcome_changes),
            "preserved_empty_domain_horse_rule_count": preserved_horse_rule_count,
            "records": permission_records,
            "changed_tuples": changed_tuples,
            "blocked_outcome_changes": blocked_outcome_changes,
        },
        "acceptance": {
            "fixed_horse_record_count_is_130": len(fixed_ids) == 130,
            "horse_hierarchy_blockers_are_zero": not horse_message_blockers,
            "new_stable_blocker_ids_are_zero": not new_target_ids,
            "new_blocked_source_ways_are_zero": not (
                {item["source_way_id"] for item in transitions}
                - {item["source_way_id"] for item in horse_records}
            ),
            "unexpected_blocker_transitions_are_zero": not unexpected_transitions,
            "unexpected_permission_changes_are_zero": not changed_tuples
            and not blocked_outcome_changes,
            "known_motorcar_cooccurrences_are_preserved": sum(
                item["status"] == "known_transition_to_motorcar"
                for item in transitions
            )
            == 2,
        },
    }
    if not all(result["acceptance"].values()):
        result["status"] = "failed"
    result["semantic_sha256"] = _semantic_sha256(result)
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
    parser.add_argument("--horse-extraction", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = compare_horse_probe(
        fixed_inventory_path=args.fixed_inventory,
        extraction_path=args.horse_extraction,
        probe_path=args.probe,
    )
    write_json_atomic(result, args.output)
    print(
        json.dumps(
            {
                "acceptance": result["acceptance"],
                "permission_diff": {
                    key: value
                    for key, value in result["permission_diff"].items()
                    if key.endswith("_count")
                },
                "stable_id_diff": {
                    key: value
                    for key, value in result["stable_id_diff"].items()
                    if key.endswith("_count")
                },
                "status": result["status"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
