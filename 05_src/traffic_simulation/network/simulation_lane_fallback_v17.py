"""Simulation-only lane fallback for formally unresolved missing source evidence.

This module never changes the formal directional-lane resolver. It consumes the
formal result first, then emits a provenance-complete model assumption only for
the approved L1/L4 missing-evidence boundary.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network.directional_lanes_v17 import (
    COUNT_KEYS,
    SHARED_SINGLE_LANE_KIND,
    SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
    resolve_directional_lanes,
)
from traffic_simulation.network.directed_segments_v17 import (
    _governed_highways,
    normalize_oneway,
)
from traffic_simulation.paths import REPOSITORY_ROOT


DECISION_ID = "DEC-P13-LANE-MISSING-SOURCE-SIMULATION-FALLBACK-001"
DECISION_VERSION = "1.0.0"
ASSUMPTION_ID = "MISSING_SOURCE_LANE_SIMULATION_FALLBACK_V1"
ASSUMPTION_VERSION = "1.0.0"
POLICY_VERSION = "1.0.0"
MISSING_STOP_CODE = "LANE_DIRECTIONAL_ALLOCATION_MISSING"
SCENARIOS = frozenset({"conservative", "baseline", "high_capacity"})

DECISION_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_missing_lane_simulation_fallback_decision.yml"
)
POLICY_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_missing_lane_simulation_fallback_policy.yml"
)
ASSUMPTION_SCHEMA_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "missing_lane_simulation_assumption_v17.schema.json"
)
MANIFEST_SCHEMA_PATH = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/schemas/"
    "missing_lane_simulation_manifest_v17.schema.json"
)


class SimulationLaneFallbackError(ValueError):
    """Raised for invalid policy bindings or simulation requests."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _semantic_sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_policy() -> dict[str, Any]:
    decision = yaml.safe_load(DECISION_PATH.read_text(encoding="utf-8"))
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if decision.get("status") != "approved":
        raise SimulationLaneFallbackError("fallback decision is not approved")
    if decision.get("decision_id") != DECISION_ID:
        raise SimulationLaneFallbackError("unexpected fallback decision ID")
    if decision.get("decision_version") != DECISION_VERSION:
        raise SimulationLaneFallbackError("unexpected fallback decision version")
    if _file_sha(POLICY_PATH) != decision["approved_policy"]["byte_sha256"]:
        raise SimulationLaneFallbackError("approved fallback policy hash mismatch")
    if policy.get("policy_id") != ASSUMPTION_ID:
        raise SimulationLaneFallbackError("unexpected fallback policy ID")
    if policy.get("policy_version") != POLICY_VERSION:
        raise SimulationLaneFallbackError("unexpected fallback policy version")
    return policy


@lru_cache(maxsize=2)
def _schema(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(value)
    return value


def lower_tie_mode(values: Sequence[int]) -> int:
    """Return the modal lane count, choosing the smaller value on a tie."""

    if not values:
        raise SimulationLaneFallbackError("mode requires at least one value")
    counts = Counter(int(value) for value in values)
    maximum = max(counts.values())
    return min(value for value, count in counts.items() if count == maximum)


def select_calibration_group(
    policy: Mapping[str, Any],
    highway: str,
    directionality: str,
    *,
    sample_count_override: int | None = None,
) -> tuple[str, str]:
    if directionality not in {"oneway", "bidirectional"}:
        raise SimulationLaneFallbackError(
            f"unsupported directionality: {directionality}"
        )
    threshold = int(policy["fixed_binding"]["calibration"]["minimum_class_sample_count"])
    configured = policy.get("class_defaults", {}).get(highway, {}).get(directionality)
    sample_count = (
        int(sample_count_override)
        if sample_count_override is not None
        else int(configured.get("sample_count", 0)) if configured else 0
    )
    if configured and not configured.get("use_global", False) and sample_count >= threshold:
        return (
            "class_directionality_calibrated_default",
            f"{highway}|{directionality}",
        )
    return "global_directionality_fallback", f"GLOBAL|{directionality}"


def allocate_assumed_lanes(total: int, canonical_oneway: str) -> dict[str, int]:
    if total <= 0:
        raise SimulationLaneFallbackError("assumed lane total must be positive")
    if canonical_oneway == "yes":
        forward, backward = total, 0
    elif canonical_oneway == "-1":
        forward, backward = 0, total
    elif canonical_oneway == "no":
        forward, backward = (total + 1) // 2, total // 2
    else:
        raise SimulationLaneFallbackError(
            f"unsupported canonical oneway: {canonical_oneway}"
        )
    return {
        "total": total,
        "forward": forward,
        "backward": backward,
        "both_ways": 0,
    }


def _formal_stop(error: Exception) -> tuple[str, str]:
    return (
        str(getattr(error, "status", "invalid")),
        str(getattr(error, "stop_code", "LANE_COUNT_INVALID")),
    )


def _not_applicable(
    *,
    fallback_level: str,
    stop_code: str,
    status: str,
    formal_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "resolution_status": status,
        "value_origin": "unresolved",
        "fallback_level": fallback_level,
        "formal_stop_code": stop_code,
        "formal_blocker_preserved": stop_code != "FORMAL_SOURCE_RESOLVED",
        "effective_value": None,
        "formal_result": dict(formal_result) if formal_result is not None else None,
        "assumption_record": None,
        "cluster_id": None,
    }


def _selected_total(
    policy: Mapping[str, Any],
    *,
    scenario: str,
    highway: str,
    directionality: str,
    fallback_level: str,
) -> int:
    if fallback_level == "class_directionality_calibrated_default":
        configured = policy["class_defaults"][highway][directionality]
        return int(configured[scenario])
    return int(policy["global_defaults"][directionality][scenario])


def resolve_simulation_lanes(
    tags: Mapping[str, str],
    *,
    source_way_id: int,
    source_osm_hash: str,
    scenario: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve formal semantics first, then the approved missing-only fallback."""

    registered = dict(policy or load_policy())
    if scenario not in SCENARIOS:
        raise SimulationLaneFallbackError(f"unsupported scenario: {scenario}")
    expected_source_hash = registered["fixed_binding"]["source_osm"]["sha256"]
    if source_osm_hash != expected_source_hash:
        raise SimulationLaneFallbackError("source OSM hash differs from approved binding")

    try:
        formal = resolve_directional_lanes(tags, profile="formal")
    except Exception as error:
        status, stop_code = _formal_stop(error)
        formal = None
    else:
        effective = formal.get("effective_value")
        if isinstance(effective, Mapping) and effective.get("kind") == SHARED_SINGLE_LANE_KIND:
            return _not_applicable(
                fallback_level="not_applicable_shared_physical_unsupported",
                stop_code=SHARED_SINGLE_LANE_MATERIALIZATION_STOP_CODE,
                status="valid_but_unsupported",
                formal_result=formal,
            )
        return {
            "resolution_status": "resolved",
            "value_origin": formal["value_origin"],
            "fallback_level": "formal_source_resolved",
            "formal_stop_code": None,
            "formal_blocker_preserved": False,
            "effective_value": dict(formal["effective_value"]),
            "formal_result": formal,
            "assumption_record": None,
            "cluster_id": None,
        }

    if stop_code != MISSING_STOP_CODE:
        return _not_applicable(
            fallback_level="not_applicable_conflict_fail_closed",
            stop_code=stop_code,
            status=status,
        )
    if any(key in tags for key in COUNT_KEYS):
        return _not_applicable(
            fallback_level="not_applicable_out_of_scope_fail_closed",
            stop_code=stop_code,
            status="unresolved",
        )
    if tags.get("highway") not in _governed_highways():
        return _not_applicable(
            fallback_level="not_applicable_out_of_scope_fail_closed",
            stop_code=stop_code,
            status="unresolved",
        )

    try:
        direction = normalize_oneway(tags)
    except Exception as error:
        error_status, error_stop = _formal_stop(error)
        return _not_applicable(
            fallback_level="not_applicable_conflict_fail_closed",
            stop_code=error_stop,
            status=error_status,
        )
    canonical_oneway = str(direction["canonical_oneway"])
    directionality = "bidirectional" if canonical_oneway == "no" else "oneway"
    cluster_id = (
        "L1_BIDIRECTIONAL_NO_LANE_COUNT"
        if directionality == "bidirectional"
        else "L4_ONEWAY_COUNT_MISSING"
    )
    fallback_level, calibration_group = select_calibration_group(
        registered, str(tags["highway"]), directionality
    )
    total = _selected_total(
        registered,
        scenario=scenario,
        highway=str(tags["highway"]),
        directionality=directionality,
        fallback_level=fallback_level,
    )
    counts = allocate_assumed_lanes(total, canonical_oneway)
    record_key = {
        "decision_id": DECISION_ID,
        "decision_version": DECISION_VERSION,
        "scenario": scenario,
        "source_way_id": int(source_way_id),
        "source_osm_hash": source_osm_hash,
        "chosen_lane_count": counts,
    }
    assumption = {
        "schema_version": 17,
        "record_id": _semantic_sha(record_key),
        "decision_id": DECISION_ID,
        "decision_version": DECISION_VERSION,
        "value_origin": "model_assumed",
        "assumption_id": ASSUMPTION_ID,
        "assumption_version": ASSUMPTION_VERSION,
        "scenario": scenario,
        "source_way_id": int(source_way_id),
        "source_osm_hash": source_osm_hash,
        "source_lane_status": "unresolved",
        "formal_stop_code": MISSING_STOP_CODE,
        "formal_blocker_preserved": True,
        "cluster_id": cluster_id,
        "canonical_directionality": directionality,
        "canonical_oneway": canonical_oneway,
        "highway": str(tags["highway"]),
        "chosen_lane_count": counts,
        "fallback_level": fallback_level,
        "calibration_group": calibration_group,
        "calibration_population_hash": registered["fixed_binding"]["calibration"]["semantic_sha256"],
        "source_rewrite": False,
    }
    jsonschema.Draft202012Validator(_schema(ASSUMPTION_SCHEMA_PATH)).validate(
        assumption
    )
    return {
        "resolution_status": "resolved_for_simulation",
        "value_origin": "model_assumed",
        "fallback_level": fallback_level,
        "formal_stop_code": MISSING_STOP_CODE,
        "formal_blocker_preserved": True,
        "effective_value": counts,
        "formal_result": None,
        "assumption_record": assumption,
        "cluster_id": cluster_id,
    }


def _empty_account() -> dict[str, Any]:
    return {
        "way_count": 0,
        "lane_totals": {"total": 0, "forward": 0, "backward": 0, "both_ways": 0},
    }


def _add_account(account: dict[str, Any], counts: Mapping[str, int]) -> None:
    account["way_count"] += 1
    for key in ("total", "forward", "backward", "both_ways"):
        account["lane_totals"][key] += int(counts[key])


def build_simulation_collection(
    ways: Sequence[Mapping[str, Any]],
    *,
    source_osm_hash: str,
    scenario: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an order-invariant simulation assumption collection and manifest."""

    registered = dict(policy or load_policy())
    results = []
    for item in sorted(ways, key=lambda value: int(value["source_way_id"])):
        result = resolve_simulation_lanes(
            item["tags"],
            source_way_id=int(item["source_way_id"]),
            source_osm_hash=source_osm_hash,
            scenario=scenario,
            policy=registered,
        )
        results.append({"source_way_id": int(item["source_way_id"]), **result})

    assumptions = sorted(
        (item["assumption_record"] for item in results if item["assumption_record"]),
        key=lambda item: item["source_way_id"],
    )
    formal_source_usage = sorted(
        item["source_way_id"]
        for item in results
        if item["fallback_level"] == "formal_source_resolved"
    )
    excluded = sorted(
        (
            {
                "source_way_id": item["source_way_id"],
                "fallback_level": item["fallback_level"],
                "formal_stop_code": item["formal_stop_code"],
            }
            for item in results
            if item["fallback_level"].startswith("not_applicable_")
        ),
        key=lambda item: item["source_way_id"],
    )

    by_cluster: dict[str, dict[str, Any]] = defaultdict(_empty_account)
    by_highway: dict[str, dict[str, Any]] = defaultdict(_empty_account)
    by_fallback = Counter()
    totals = {"total": 0, "forward": 0, "backward": 0, "both_ways": 0}
    for record in assumptions:
        counts = record["chosen_lane_count"]
        _add_account(by_cluster[record["cluster_id"]], counts)
        _add_account(by_highway[record["highway"]], counts)
        by_fallback[record["fallback_level"]] += 1
        for key in totals:
            totals[key] += int(counts[key])

    manifest = {
        "schema_version": 17,
        "artifact_type": "missing_source_lane_simulation_assumption_manifest",
        "decision_id": DECISION_ID,
        "decision_version": DECISION_VERSION,
        "policy_id": ASSUMPTION_ID,
        "policy_version": POLICY_VERSION,
        "scenario": scenario,
        "source_osm_hash": source_osm_hash,
        "calibration_population_hash": registered["fixed_binding"]["calibration"]["semantic_sha256"],
        "assumed_way_count": len(assumptions),
        "assumed_lane_totals": totals,
        "by_cluster": dict(sorted(by_cluster.items())),
        "by_highway": dict(sorted(by_highway.items())),
        "by_fallback_level": dict(sorted(by_fallback.items())),
        "formal_source_usage_count": len(formal_source_usage),
        "conflicts_excluded": sum(
            item["fallback_level"] == "not_applicable_conflict_fail_closed"
            for item in excluded
        ),
        "shared_unsupported_excluded": sum(
            item["fallback_level"] == "not_applicable_shared_physical_unsupported"
            for item in excluded
        ),
        "out_of_scope_excluded": sum(
            item["fallback_level"] == "not_applicable_out_of_scope_fail_closed"
            for item in excluded
        ),
        "formal_blockers_preserved": len(assumptions),
        "source_rewrite": False,
    }
    jsonschema.Draft202012Validator(_schema(MANIFEST_SCHEMA_PATH)).validate(manifest)
    semantic_payload = {
        "assumption_records": assumptions,
        "formal_source_usage_way_ids": formal_source_usage,
        "excluded": excluded,
        "manifest": manifest,
    }
    return {
        "schema_version": 17,
        "artifact_type": "missing_source_lane_simulation_collection",
        "scenario": scenario,
        **semantic_payload,
        "semantic_sha256": _semantic_sha(semantic_payload),
    }
