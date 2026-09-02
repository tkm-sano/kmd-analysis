"""Validate successor artifacts, including adopted shared-lane source/materialization accounting."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Mapping, Sequence

from traffic_simulation.network import validate_v17_phase12_run_completion as base


SHARED_MATERIALIZATION_STOP = "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
PROFILE_DIFFERENCE_DECISION_ID = "DEC-P12-FORMAL-ONLY-PROFILE-DIFFERENCE-002"


def _lane_map(stage: Mapping[str, Any]) -> tuple[dict[tuple[str, int], dict[str, Any]], bool]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    duplicate = False
    for segment in stage["directional_lanes"]["segment_lanes"]:
        for lane in segment["lanes"]:
            key = (str(segment["directed_segment_id"]), int(lane["lane_position"]))
            duplicate = duplicate or key in result
            result[key] = {
                "source_way_id": int(segment["source_way_id"]),
                "directed_segment_id": str(segment["directed_segment_id"]),
                "lane_position": int(lane["lane_position"]),
                "source_direction": segment.get("source_direction"),
                "source_vector_values": dict(lane.get("source_vector_values", {})),
                "value_origin": segment.get("value_origin"),
                "rule_ids": sorted(str(item) for item in segment.get("rule_ids", [])),
                "assumption_ids": sorted(
                    str(item) for item in segment.get("assumption_ids", [])
                ),
                "formal_eligible": segment.get("formal_eligible"),
            }
    return result, duplicate


def _permission_map(
    stage: Mapping[str, Any],
) -> tuple[dict[tuple[str, int, str], Mapping[str, Any]], bool]:
    result: dict[tuple[str, int, str], Mapping[str, Any]] = {}
    duplicate = False
    for record in stage["final_permission"]["permission_records"]:
        key = (
            str(record["directed_segment_id"]),
            int(record["lane_position"]),
            str(record["vehicle_class"]),
        )
        duplicate = duplicate or key in result
        result[key] = record
    return result, duplicate


def _profile_difference_identity(
    key: tuple[Any, ...], source_way_id: Any
) -> dict[str, Any]:
    """Build the v1.2 identity from the upstream source-Way provenance."""
    if not isinstance(source_way_id, int) or isinstance(source_way_id, bool) or source_way_id < 1:
        raise base.Phase12RunCompletionError(
            "population_accounting", "profile-difference identity lacks valid source_way_id provenance"
        )
    identity = {
        "source_way_id": source_way_id,
        "directed_segment_id": key[0],
        "lane_position": key[1],
    }
    if len(key) == 3:
        identity["vehicle_class"] = key[2]
    return identity


def _difference_record(
    key: tuple[Any, ...],
    *,
    classification: str,
    explanation_code: str,
    lane: Mapping[str, Any] | None,
    permission: Mapping[str, Any] | None,
) -> dict[str, Any]:
    identity = {
        "source_way_id": lane.get("source_way_id") if lane else None,
        "directed_segment_id": key[0],
        "lane_position": key[1],
    }
    if len(key) == 3:
        identity["vehicle_class"] = key[2]
    return {
        "identity": identity,
        "classification": classification,
        "explanation_code": explanation_code,
        "lane_value_origin": lane.get("value_origin") if lane else None,
        "lane_rule_ids": list(lane.get("rule_ids", [])) if lane else [],
        "lane_assumption_ids": list(lane.get("assumption_ids", [])) if lane else [],
        "lane_formal_eligible": lane.get("formal_eligible") if lane else None,
        "permission_record_id": permission.get("permission_record_id") if permission else None,
        "permission_resolution_status": permission.get("resolution_status") if permission else None,
        "permission_rule_ids": sorted(
            str(item) for item in permission.get("maximal_rule_ids", [])
        ) if permission else [],
    }


def _build_profile_population_difference_v1_1_legacy(
    structural: Mapping[str, Any],
    formal: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify both profile directions without treating net difference as evidence."""
    if decision.get("decision_id") != PROFILE_DIFFERENCE_DECISION_ID:
        raise base.Phase12RunCompletionError(
            "population_accounting", "profile-difference decision identity differs"
        )
    approved_rules = set(
        decision["decision"]["formal_only_differences"]["approved_lane_rule_ids"]
    )
    registered_assumptions = {
        str(item["assumption_id"]) for item in registry["assumptions"]
    }
    structural_lanes, duplicate_structural_lanes = _lane_map(structural)
    formal_lanes, duplicate_formal_lanes = _lane_map(formal)
    structural_permissions, duplicate_structural_permissions = _permission_map(structural)
    formal_permissions, duplicate_formal_permissions = _permission_map(formal)

    def classify(
        structural_map: Mapping[tuple[Any, ...], Any],
        formal_map: Mapping[tuple[Any, ...], Any],
        *,
        permission_level: bool,
    ) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        assumptions: Counter[str] = Counter()
        rules: Counter[str] = Counter()
        for key in sorted(structural_map.keys() - formal_map.keys()):
            lane = structural_lanes.get((key[0], key[1]))
            for assumption_id in lane.get("assumption_ids", []) if lane else []:
                assumptions[assumption_id] += 1
            records.append(_difference_record(
                key,
                classification="structural_only",
                explanation_code="REGISTERED_STRUCTURAL_ASSUMPTION",
                lane=lane,
                permission=structural_permissions.get(key) if permission_level else None,
            ))
        for key in sorted(formal_map.keys() - structural_map.keys()):
            lane = formal_lanes.get((key[0], key[1]))
            permission = formal_permissions.get(key) if permission_level else None
            lane_rules = set(lane.get("rule_ids", [])) if lane else set()
            allowed = bool(
                lane
                and lane.get("value_origin") == "rule_derived"
                and isinstance(lane.get("source_way_id"), int)
                and lane["source_way_id"] > 0
                and lane.get("formal_eligible") is True
                and not lane.get("assumption_ids")
                and lane_rules
                and lane_rules.issubset(approved_rules)
                and (
                    not permission_level
                    or (
                        permission is not None
                        and permission.get("source_way_id") == lane["source_way_id"]
                    )
                )
            )
            classification = "allowed_formal_only" if allowed else "unexplained_formal_only"
            explanation = (
                "ADOPTED_FORMAL_LANE_RULE_AND_AR_ACCESS_006"
                if allowed and permission_level
                else "ADOPTED_FORMAL_LANE_RULE"
                if allowed
                else "FORMAL_ONLY_PROVENANCE_REQUIREMENT_NOT_MET"
            )
            if allowed:
                for rule_id in lane_rules:
                    rules[rule_id] += 1
            records.append(_difference_record(
                key,
                classification=classification,
                explanation_code=explanation,
                lane=lane,
                permission=permission,
            ))
        formal_only = [item for item in records if item["classification"] != "structural_only"]
        return {
            "identity_axes": ["directed_segment_id", "lane_position"]
            + (["vehicle_class"] if permission_level else []),
            "structural_record_count": len(structural_map),
            "formal_record_count": len(formal_map),
            "structural_only_count": len(structural_map.keys() - formal_map.keys()),
            "formal_only_count": len(formal_only),
            "allowed_formal_only_count": sum(
                item["classification"] == "allowed_formal_only" for item in formal_only
            ),
            "unexplained_formal_only_count": sum(
                item["classification"] == "unexplained_formal_only" for item in formal_only
            ),
            "by_assumption_id": dict(sorted(assumptions.items())),
            "allowed_formal_only_by_rule_id": dict(sorted(rules.items())),
            "records": records,
        }

    lanes = classify(structural_lanes, formal_lanes, permission_level=False)
    permissions = classify(
        structural_permissions, formal_permissions, permission_level=True
    )
    unexplained = (
        lanes["unexplained_formal_only_count"]
        + permissions["unexplained_formal_only_count"]
    )
    structural_provenance_invalid = any(
        not item["lane_assumption_ids"]
        or not set(item["lane_assumption_ids"]).issubset(registered_assumptions)
        for section in (lanes, permissions)
        for item in section["records"]
        if item["classification"] == "structural_only"
    )
    unregistered = structural_provenance_invalid or any(
        item not in registered_assumptions
        for section in (lanes, permissions)
        for item in section["by_assumption_id"]
    )
    duplicate_structural = duplicate_structural_lanes or duplicate_structural_permissions
    duplicate_formal = duplicate_formal_lanes or duplicate_formal_permissions
    passed = not (unexplained or unregistered or duplicate_structural or duplicate_formal)
    return {
        "policy_decision_id": PROFILE_DIFFERENCE_DECISION_ID,
        "lane_identities": lanes,
        "permission_identities": permissions,
        "unexplained_formal_only_count": unexplained,
        "unexplained_formal_only_detected": bool(unexplained),
        "duplicate_structural_record_detected": duplicate_structural,
        "duplicate_formal_record_detected": duplicate_formal,
        "unregistered_assumption_detected": unregistered,
        "gate_result": "passed" if passed else "failed",
    }


def build_profile_population_difference(
    structural: Mapping[str, Any],
    formal: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply Decision A using rule semantics, evidence, and lineage (v1.2)."""
    if decision.get("decision_id") != PROFILE_DIFFERENCE_DECISION_ID:
        raise base.Phase12RunCompletionError("population_accounting", "Decision A identity differs")
    rule_specs = decision.get("authorized_rules", {})
    allowed_origins = set(decision["authorized_formal_only"]["authorized_value_origins"])
    registered_assumptions = {str(x["assumption_id"]) for x in registry.get("assumptions", [])}
    sl, sd = _lane_map(structural)
    fl, fd = _lane_map(formal)
    sp, spd = _permission_map(structural)
    fp, fpd = _permission_map(formal)

    def immutable(item: Mapping[str, Any] | None, key: tuple[Any, ...]) -> tuple[Any, ...] | None:
        if item is None:
            return None
        return (item.get("source_way_id"), str(item.get("directed_segment_id")), int(item.get("lane_position", -1))) + ((str(key[2]),) if len(key) == 3 else ())

    def evidence_complete(lane: Mapping[str, Any], spec: Mapping[str, Any]) -> bool:
        for field in spec.get("required_evidence_fields", []):
            value = lane.get(field)
            if value is None or value == {} or value == [] or value == "":
                return False
        return True

    def authorized_lane(lane: Mapping[str, Any] | None) -> bool:
        if not lane:
            return False
        rule_ids = set(lane.get("rule_ids", []))
        return bool(rule_ids) and rule_ids.issubset(rule_specs) and lane.get("formal_eligible") is True and lane.get("value_origin") in allowed_origins and not lane.get("assumption_ids") and all(evidence_complete(lane, rule_specs[r]) for r in rule_ids)

    def classify(sm: Mapping[tuple[Any, ...], Any], fm: Mapping[tuple[Any, ...], Any],
                 *, permission: bool) -> dict[str, Any]:
        records = []
        counts = Counter({name: 0 for name in ("common", "structural_only", "formal_only", "authorized_formal_only", "unauthorized_formal_only", "same_identity_inconsistent")})
        by_rule, by_decision, by_origin, by_assumption = Counter(), Counter(), Counter(), Counter()
        all_keys = sorted(set(sm) | set(fm))
        for key in all_keys:
            lane_key = (key[0], key[1])
            lane = fl.get(lane_key) if permission else fl.get(key)
            slane = sl.get(lane_key) if permission else sl.get(key)
            item = fp.get(key) if permission else lane
            sitem = sp.get(key) if permission else slane
            if key in sm and key in fm:
                classification = "common"
                if immutable(sitem, key) != immutable(item, key):
                    classification = "same_identity_inconsistent"
                counts[classification] += 1
            elif key in sm:
                classification = "structural_only"
                counts[classification] += 1
            else:
                counts["formal_only"] += 1
                spec_ok = False
                rule_ids = set(lane.get("rule_ids", [])) if lane else set()
                lineage_ok = bool(lane) and (not permission or bool(item) and item.get("source_way_id") == lane.get("source_way_id") and item.get("directed_segment_id") == lane.get("directed_segment_id") and item.get("lane_position") == lane.get("lane_position"))
                if lineage_ok and authorized_lane(lane):
                    spec_ok = all(str(a) in registered_assumptions for a in lane.get("assumption_ids", []))
                if permission:
                    # A permission-only difference must be explained by an authorized lane-only difference.
                    spec_ok = authorized_lane(lane) and lane_key not in sl and lineage_ok
                if spec_ok:
                    classification = "authorized_formal_only"
                    for rule in rule_ids:
                        by_rule[rule] += 1
                        by_decision[rule_specs[rule]["decision_id"]] += 1
                    if lane:
                        by_origin[str(lane.get("value_origin"))] += 1
                        for assumption in lane.get("assumption_ids", []): by_assumption[str(assumption)] += 1
                else:
                    classification = "unauthorized_formal_only"
                counts[classification] += 1
            source_way_id = item.get("source_way_id") if item else (sitem.get("source_way_id") if sitem else None)
            records.append({"identity": _profile_difference_identity(key, source_way_id), "classification": classification, "source_way_id": source_way_id, "rule_ids": sorted(str(x) for x in (lane or {}).get("rule_ids", [])), "decision_ids": sorted({rule_specs[x]["decision_id"] for x in (lane or {}).get("rule_ids", []) if x in rule_specs}), "value_origin": (lane or {}).get("value_origin"), "assumption_ids": sorted(str(x) for x in (lane or {}).get("assumption_ids", [])), "formal_eligible": (lane or {}).get("formal_eligible"), "permission_record_id": item.get("permission_record_id") if permission and item else None})
        counts["formal_only"] = counts["authorized_formal_only"] + counts["unauthorized_formal_only"]
        return {"identity_axes": ["directed_segment_id", "lane_position"] + (["vehicle_class"] if permission else []), "structural_count": len(sm), "formal_count": len(fm), **{f"{k}_count": v for k, v in counts.items()}, "by_rule_id": dict(sorted(by_rule.items())), "by_decision_id": dict(sorted(by_decision.items())), "by_value_origin": dict(sorted(by_origin.items())), "by_assumption_id": dict(sorted(by_assumption.items())), "records": records}

    lanes = classify(sl, fl, permission=False)
    permissions = classify(sp, fp, permission=True)
    inconsistent = lanes["same_identity_inconsistent_count"] + permissions["same_identity_inconsistent_count"]
    unauthorized = lanes["unauthorized_formal_only_count"] + permissions["unauthorized_formal_only_count"]
    structural_invalid = any(
        not lane.get("assumption_ids") or not set(lane.get("assumption_ids", [])).issubset(registered_assumptions)
        for lane in sl.values()
    )
    return {"policy_decision_id": PROFILE_DIFFERENCE_DECISION_ID, "lane_identities": lanes, "permission_identities": permissions, "unauthorized_formal_only_count": unauthorized, "same_identity_inconsistent_count": inconsistent, "gate_result": "passed" if not unauthorized and not inconsistent and not structural_invalid and not sd and not fd and not spd and not fpd else "failed", "duplicate_structural_record_detected": sd or spd, "duplicate_formal_record_detected": fd or fpd}


def _counter(records: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(item["resolution_status"]) for item in records)


def _expected_population_statuses(formal: Mapping[str, Any]) -> dict[str, Counter[str]]:
    stages = formal["stage_outputs"]
    lanes = stages["directional_lanes"]
    source_blockers = [
        item for item in lanes["blockers"]
        if item["stop_code"] != SHARED_MATERIALIZATION_STOP
    ]
    materialization_blockers = [
        item for item in lanes["blockers"]
        if item["stop_code"] == SHARED_MATERIALIZATION_STOP
    ]
    source_records = [*lanes["resolutions"], *source_blockers]
    materialized_way_count = len(
        {int(item["source_way_id"]) for item in lanes["segment_lanes"]}
    )
    return {
        "formal_directional_lane_source_way": _counter(source_records),
        "formal_lane_canonical_representation": _counter(source_records),
        "formal_lane_simulation_materialization": _counter(
            [
                *({"resolution_status": "resolved"} for _ in range(materialized_way_count)),
                *materialization_blockers,
            ]
        ),
        "formal_static_access_source_way": _counter(
            [
                *({"resolution_status": "resolved"} for _ in stages["static_access"]["normalized_rules"]),
                *stages["static_access"]["blockers"],
            ]
        ),
        "formal_conditional_access_source_way": _counter(
            [
                *({"resolution_status": "resolved"} for _ in stages["conditional_access"]["conditional_rules"]),
                *stages["conditional_access"]["blockers"],
            ]
        ),
        "formal_permission_lane_tuple": _counter(
            stages["final_permission"]["permission_records"]
        ),
        "formal_speed_directed_segment": _counter(stages["speed"]["speed_records"]),
    }


def _validate_population(
    artifacts: Mapping[str, Mapping[str, Any]], registry: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> None:
    accounting = artifacts["population_accounting"]
    units = {item["population_unit_id"]: item for item in accounting["population_units"]}
    expected = _expected_population_statuses(artifacts["formal_full_population"])
    if set(units) != set(expected):
        raise base.Phase12RunCompletionError(
            "population_accounting", "successor population unit set differs"
        )
    for unit_id, unit in units.items():
        if unit["input"] != unit["governed"] + unit["excluded"]:
            raise base.Phase12RunCompletionError(
                "population_accounting", f"input equation differs: {unit_id}"
            )
        if unit["governed"] != sum(unit[name] for name in base.ACCOUNTED_STATUSES):
            raise base.Phase12RunCompletionError(
                "population_accounting", f"governed equation differs: {unit_id}"
            )
        actual = expected[unit_id]
        if any(unit[name] != actual[name] for name in base.ACCOUNTED_STATUSES):
            raise base.Phase12RunCompletionError(
                "population_accounting", f"status counts differ: {unit_id}"
            )
        if unit["structural_count"] != unit["common_count"] + unit["structural_only_count"] or unit["formal_count"] != unit["common_count"] + unit["formal_only_count"] or unit["formal_only_count"] != unit["authorized_formal_only_count"] + unit["unauthorized_formal_only_count"]:
            raise base.Phase12RunCompletionError("population_accounting", f"profile partition equation differs: {unit_id}")

    structural = artifacts["structural_full_population"]["stage_outputs"]
    formal = artifacts["formal_full_population"]["stage_outputs"]
    expected_difference = build_profile_population_difference(
        structural, formal, registry=registry, decision=decision
    )
    if accounting["profile_population_difference"] != expected_difference:
        raise base.Phase12RunCompletionError(
            "population_accounting", "profile-difference accounting differs"
        )
    if expected_difference["gate_result"] != "passed":
        raise base.Phase12RunCompletionError(
            "population_accounting", "unexplained or invalid profile difference exists"
        )
    if accounting["profile_population_difference"]["unauthorized_formal_only_count"] != 0 or accounting["profile_population_difference"]["same_identity_inconsistent_count"] != 0:
        raise base.Phase12RunCompletionError("population_accounting", "Decision A zero gate differs")


def validate_successor_major_artifacts(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    registry: Mapping[str, Any],
    policy: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, str]:
    if set(artifacts) != set(base.MAJOR_ARTIFACT_IDS):
        raise base.Phase12RunCompletionError(
            "required_artifacts", "major artifact set differs"
        )
    base._validate_semantic_hashes(artifacts)
    base._validate_semantics(artifacts)
    base._validate_identities(artifacts)
    _validate_population(artifacts, registry, decision)
    legacy = copy.deepcopy(artifacts)
    permission_difference = artifacts["population_accounting"]["profile_population_difference"]["permission_identities"]
    legacy["population_accounting"]["profile_population_difference"] = {
        "by_assumption_id": permission_difference["by_assumption_id"]
    }
    base._validate_registered_values(legacy, registry, policy)
    base._validate_blockers_and_exclusions(artifacts, policy)
    return {
        "schema": "passed",
        "semantic": "passed",
        "identity_uniqueness": "passed",
        "population_accounting": "passed",
        "registered_values": "passed",
        "blocker_exclusion": "passed",
    }
