"""Resolve v17 access candidates into governed final permission expectations."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
)
from traffic_simulation.network.static_access_v17 import (
    StaticAccessError,
    _evaluate_context,
    _load_json,
    _scope_sets,
    build_static_access_production_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


PERMISSION_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/"
    "final_permission_expectation_v17.schema.json"
)
GOVERNED_VCLASSES = frozenset(
    {"passenger", "taxi", "bus", "coach", "delivery", "truck", "motorcycle"}
)


class FinalPermissionError(StaticAccessError):
    """Raised when final access dominance cannot produce one permission."""


@lru_cache(maxsize=1)
def _permission_validator() -> jsonschema.Draft202012Validator:
    schema = _load_json(PERMISSION_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _set_relation(
    left: Sequence[Any], right: Sequence[Any], *, temporal: bool = False
) -> tuple[bool, bool]:
    """Return (left is subset of right, the subset is strict)."""

    left_set, right_set = set(left), set(right)
    if temporal:
        if left_set == right_set:
            return True, False
        if right_set == {"unconditional"} and left_set != {"unconditional"}:
            return True, True
        # Different registered condition hashes do not prove containment.
        return False, False
    return left_set <= right_set, left_set < right_set


def rule_dominates(
    left: Mapping[str, Any], right: Mapping[str, Any], *, lane_count: int
) -> bool:
    """Apply target-scope plus four-axis Pareto dominance."""

    left_directions, left_lanes = _scope_sets(left, lane_count)
    right_directions, right_lanes = _scope_sets(right, lane_count)
    relations = [
        (left_directions <= right_directions, left_directions < right_directions),
        (left_lanes <= right_lanes, left_lanes < right_lanes),
        _set_relation(left["spatial_domain"], right["spatial_domain"]),
        _set_relation(left["vehicle_domain"], right["vehicle_domain"]),
        _set_relation(
            left["temporal_domain"], right["temporal_domain"], temporal=True
        ),
        _set_relation(left["purpose_domain"], right["purpose_domain"]),
    ]
    return all(subset for subset, _strict in relations) and any(
        strict for _subset, strict in relations
    )


def applicable_rules_for_tuple(
    rules: Sequence[Mapping[str, Any]],
    *,
    direction: str,
    lane_position: int,
    lane_count: int,
    vehicle_class: str,
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    if vehicle_class not in GOVERNED_VCLASSES:
        raise FinalPermissionError(
            f"vehicle class is outside the governed universe: {vehicle_class}",
            stop_code="ACCESS_VEHICLE_HIERARCHY_MISSING",
            status="unresolved",
        )
    candidates: list[dict[str, Any]] = []
    for rule in rules:
        directions, lanes = _scope_sets(rule, lane_count)
        if (
            direction in directions
            and lane_position in lanes
            and vehicle_class in rule["vehicle_domain"]
        ):
            candidates.append(_evaluate_context(rule, context))
    return tuple(candidates)


def maximal_rules(
    rules: Sequence[Mapping[str, Any]], *, lane_count: int
) -> tuple[dict[str, Any], ...]:
    """Select order-invariant maximal rules from already-applicable rules."""

    return tuple(
        copy.deepcopy(dict(rule))
        for rule in sorted(rules, key=lambda item: item["rule_id"])
        if not any(
            other["rule_id"] != rule["rule_id"]
            and rule_dominates(other, rule, lane_count=lane_count)
            for other in rules
        )
    )


def resolve_permission(
    rules: Sequence[Mapping[str, Any]], *, lane_count: int
) -> dict[str, Any]:
    selected = maximal_rules(rules, lane_count=lane_count)
    rule_ids = [item["rule_id"] for item in selected]
    if not selected:
        return {
            "resolution_status": "unresolved",
            "value_origin": None,
            "effective_permission": None,
            "maximal_rule_ids": [],
            "stop_code": "ACCESS_PERMISSION_UNRESOLVED",
            "review_required": True,
            "maximal_rules": [],
        }
    effects = {item["effect"] for item in selected}
    provenance = [_rule_provenance(item) for item in selected]
    if len(effects) > 1:
        return {
            "resolution_status": "conflict",
            "value_origin": None,
            "effective_permission": None,
            "maximal_rule_ids": rule_ids,
            "stop_code": "ACCESS_SPECIFICITY_CONFLICT",
            "review_required": True,
            "conflicting_candidates": [
                {"rule_id": item["rule_id"], "effect": item["effect"]}
                for item in selected
            ],
            "maximal_rules": provenance,
        }
    return {
        "resolution_status": "resolved",
        "value_origin": "rule_derived",
        "effective_permission": next(iter(effects)),
        "maximal_rule_ids": rule_ids,
        "stop_code": None,
        "review_required": False,
        "maximal_rules": provenance,
    }


def _rule_provenance(rule: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "source_key": rule["source_key"],
        "source_value": rule["source_value"],
        "source_element": copy.deepcopy(rule["source_element"]),
        "target_scope": copy.deepcopy(rule["target_scope"]),
        "spatial_domain": copy.deepcopy(rule["spatial_domain"]),
        "vehicle_domain": copy.deepcopy(rule["vehicle_domain"]),
        "temporal_domain": copy.deepcopy(rule["temporal_domain"]),
        "purpose_domain": copy.deepcopy(rule["purpose_domain"]),
        "effect": rule["effect"],
        "provenance": copy.deepcopy(rule["provenance"]),
    }


def _permission_id(identity: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(identity), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_permission_record(
    candidate: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    population_version: str,
    profile: str,
    scenario_context_id: str,
) -> dict[str, Any]:
    identity = {
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": population_version,
        "profile": profile,
        "source_way_id": candidate["source_way_id"],
        "directed_segment_id": candidate["directed_segment_id"],
        "source_direction": candidate["source_direction"],
        "lane_position": candidate["lane_position"],
        "vehicle_class": candidate["vehicle_class"],
        "scenario_context_id": scenario_context_id,
    }
    result = {
        "permission_record_id": _permission_id(identity),
        **identity,
        "resolution_status": decision["resolution_status"],
        "value_origin": decision["value_origin"],
        "effective_permission": decision["effective_permission"],
        "maximal_rule_ids": list(decision["maximal_rule_ids"]),
        "stop_code": decision["stop_code"],
        "review_required": decision["review_required"],
        "provenance": {
            "resolution": "scope_and_axis_dominance_v17",
            "maximal_rules": copy.deepcopy(decision["maximal_rules"]),
            "typemap_permission_used": False,
        },
    }
    if "conflicting_candidates" in decision:
        result["conflicting_candidates"] = copy.deepcopy(
            decision["conflicting_candidates"]
        )
    _permission_validator().validate(result)
    return result


def _rules_by_way(collection: Sequence[Mapping[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    return {
        int(item["source_way_id"]): [copy.deepcopy(rule) for rule in item["rules"]]
        for item in collection
    }


def build_final_permission_production_artifact(
    input_path: Path,
    *,
    profile: str,
    scenario_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    conditional = build_conditional_access_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )
    static = build_static_access_production_artifact(
        input_path,
        profile=profile,
        scenario_context=conditional["scenario_context"],
    )
    static_by_way = _rules_by_way(static["normalized_rules"])
    conditional_by_way = _rules_by_way(conditional["conditional_rules"])
    context = conditional["scenario_context"]
    scenario_context_id = str(context.get("scenario_context_id", "fixture_context"))

    lane_counts: dict[tuple[int, str], int] = {}
    for candidate in conditional["access_candidates"]:
        key = (int(candidate["source_way_id"]), candidate["source_direction"])
        lane_counts[key] = max(
            lane_counts.get(key, 0), int(candidate["lane_position"]) + 1
        )

    permission_records: list[dict[str, Any]] = []
    for candidate in conditional["access_candidates"]:
        way_id = int(candidate["source_way_id"])
        lane_count = lane_counts[(way_id, candidate["source_direction"])]
        rules = static_by_way.get(way_id, []) + conditional_by_way.get(way_id, [])
        applicable = applicable_rules_for_tuple(
            rules,
            direction=candidate["source_direction"],
            lane_position=int(candidate["lane_position"]),
            lane_count=lane_count,
            vehicle_class=candidate["vehicle_class"],
            context=context,
        )
        decision = resolve_permission(applicable, lane_count=lane_count)
        permission_records.append(
            _build_permission_record(
                candidate,
                decision,
                population_version=conditional["population_version"],
                profile=profile,
                scenario_context_id=scenario_context_id,
            )
        )
    permission_records.sort(key=lambda item: item["permission_record_id"])

    blockers = [
        {
            "scope": "permission_tuple",
            "permission_record_id": item["permission_record_id"],
            "source_way_id": item["source_way_id"],
            "resolution_status": item["resolution_status"],
            "stop_code": item["stop_code"],
        }
        for item in permission_records
        if item["resolution_status"] != "resolved"
    ]
    upstream_groups = (
        conditional["blockers"],
        conditional["upstream_static_access_blockers"],
        conditional["upstream_lane_blockers"],
        conditional["upstream_relation_blockers"],
    )
    upstream_count = sum(len(group) for group in upstream_groups)
    payload = json.dumps(
        {
            "permission_records": permission_records,
            "blockers": blockers,
            "upstream_blockers": upstream_groups,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    status_counts = Counter(item["resolution_status"] for item in permission_records)
    return {
        "schema_version": 17,
        "artifact_type": "final_permission_expectation_collection",
        "configuration_id": conditional["configuration_id"],
        "population_version": conditional["population_version"],
        "profile": profile,
        "source": conditional["source"],
        "scenario_context": copy.deepcopy(context),
        "permission_authority": "resolver_expected_permissions",
        "typemap_role": "provisional_topology_candidate_only",
        "governed_vclasses": sorted(GOVERNED_VCLASSES),
        "conditional_access_semantic_sha256": conditional["semantic_sha256"],
        "permission_records": permission_records,
        "blockers": blockers,
        "upstream_conditional_access_blockers": conditional["blockers"],
        "upstream_static_access_blockers": conditional[
            "upstream_static_access_blockers"
        ],
        "upstream_lane_blockers": conditional["upstream_lane_blockers"],
        "upstream_relation_blockers": conditional["upstream_relation_blockers"],
        "counts": {
            "governed_lane_tuples": len(conditional["access_candidates"]),
            "permission_records": len(permission_records),
            "resolved_permissions": status_counts["resolved"],
            "unresolved_permissions": status_counts["unresolved"],
            "conflicting_permissions": status_counts["conflict"],
            "permission_blockers": len(blockers),
            "upstream_blockers": upstream_count,
        },
        "record_coverage_complete": len(permission_records)
        == len(conditional["access_candidates"]),
        "formal_permission_complete": not blockers and upstream_count == 0,
        "blocker_stop_codes": dict(
            sorted(Counter(item["stop_code"] for item in blockers).items())
        ),
        "semantic_sha256": hashlib.sha256(payload).hexdigest(),
    }


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(
            f"refusing to overwrite final-permission artifact: {output_path}"
        )
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
        description="Resolve v17 final permission expectations."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    parser.add_argument("--scenario-context", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = None
    if args.scenario_context is not None:
        context = json.loads(args.scenario_context.read_text(encoding="utf-8"))
    artifact = build_final_permission_production_artifact(
        args.input, profile=args.profile, scenario_context=context
    )
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 0 if artifact["formal_permission_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
