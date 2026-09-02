from __future__ import annotations

import copy

import pytest

from traffic_simulation.network.project_v17_phase12_blockers import (
    BlockerProjectionError,
    build_projection,
)


def _baseline() -> dict:
    return {
        "baseline_id": "fixture",
        "canonical_run": {"run_id": "fixture", "source_commit": "a" * 40, "population_version": "fixture"},
        "formal_blocker_baseline": {"semantic_sha256": "b" * 64},
    }


def _entry(record_id: str, attribute: str, *, way: int | None = 1, relation: bool = False, root_ids: list[str] | None = None) -> dict:
    if relation:
        record_id = f"directed_segments:directed_segments:relation:{record_id}:RELATION_DIRECTED_MAPPING_MISSING"
    return {
        "blocker_id": f"blocker:{record_id}",
        "record_id": record_id,
        "source_way_id": way,
        "directed_segment_id": "ds:1:0:1:forward" if attribute == "final_permission" else None,
        "lane_position": 0 if attribute == "final_permission" else None,
        "vehicle_class": "delivery" if attribute == "final_permission" else None,
        "attribute_name": attribute,
        "stop_code": "ACCESS_PERMISSION_UNRESOLVED" if attribute == "final_permission" else "SPEED_RULE_NOT_REGISTERED",
        "root_cause_category": "missing_registered_rule" if attribute == "final_permission" else "missing_evidence",
        "secondary_causes": [],
        "root_cause_record_ids": root_ids or [],
        "research_scope_status": {"value": "governed", "reason": "fixture", "evidence_ids": ["fixture:evidence"]},
        "selected_strategy": {"value": "remain_blocked", "reason": "fixture"},
        "remediation": {"decision_id": None, "rule_id": None, "fixture_ids": [], "owner": "fixture", "target_phase": 13, "status": "planned"},
    }


def _accounting(entries: list[dict], root: dict | None = None, *, duplicate_edge: bool = False, fake_suppressed: bool = False) -> dict:
    permissions = [e for e in entries if e["attribute_name"] == "final_permission"]
    upstream = [e for e in entries if e["attribute_name"] != "final_permission"]
    roots = [root] if root else []
    edges = [{"root_cause_record_id": root["root_cause_record_id"], "downstream_record_id": e["record_id"], "relationship": "causes_permission_blocker"} for e in permissions] if root else []
    if duplicate_edge and edges:
        edges.append(copy.deepcopy(edges[0]))
    suppressed = [{"root_cause_record_id": e["record_id"], "source_way_id": e["source_way_id"], "suppressed_directed_segment_count": 1, "suppressed_lane_tuple_count": 1, "relationship": "candidate_suppressed"} for e in upstream]
    if fake_suppressed:
        suppressed[0]["root_cause_record_id"] = "fabricated"
    return {"root_cause_records": roots, "blocker_relationships": {"causal_edges": edges, "suppressed_candidates": suppressed}}


def _root() -> dict:
    return {"root_cause_record_id": "root:permission", "source_way_id": 1, "vehicle_class": "delivery", "scenario_context_id": "context", "root_cause_category": "missing_registered_rule", "cause_kind": "no_applicable_access_rule", "access_tag_keys": ["vehicle"], "candidate_rule_ids": [], "affected_permission_record_count": 2, "resolution_status": "unresolved", "stop_code": "ACCESS_PERMISSION_UNRESOLVED"}


def test_one_root_to_multiple_downstream_blockers_and_permission_upstream() -> None:
    root = _root()
    entries = [_entry("p1", "final_permission", root_ids=[root["root_cause_record_id"]]), _entry("p2", "final_permission", way=2, root_ids=[root["root_cause_record_id"]])]
    result = build_projection({"counts": {"total": 2}, "entries": entries, "semantic_sha256": "c" * 64}, _accounting(entries, root), _baseline(), require_canonical_baseline=False)
    assert result["deduplicated_summary"]["causal_edge_count"] == 2
    assert result["deduplicated_summary"]["one_root_to_n_downstream_root_count"] == 1


def test_suppressed_upstream_candidate_is_retained() -> None:
    entry = _entry("speed1", "speed")
    result = build_projection({"counts": {"total": 1}, "entries": [entry], "semantic_sha256": "c" * 64}, _accounting([entry]), _baseline(), require_canonical_baseline=False)
    assert result["deduplicated_summary"]["suppressed_candidate_count"] == 1


def test_permission_and_upstream_lane_blocker_remain_distinct_without_fabricated_edge() -> None:
    root = _root()
    lane = _entry("lane1", "directional_lanes")
    permission = _entry("permission1", "final_permission", root_ids=[root["root_cause_record_id"]])
    entries = [lane, permission]
    result = build_projection({"counts": {"total": 2}, "entries": entries, "semantic_sha256": "c" * 64}, _accounting(entries, root), _baseline(), require_canonical_baseline=False)
    assert result["deduplicated_summary"]["causal_edge_count"] == 1
    assert result["deduplicated_summary"]["suppressed_candidate_count"] == 1


def test_unique_source_way_and_relation_identity_are_separate() -> None:
    entries = [_entry("speed1", "speed", way=7), _entry("42", "directed_segments", way=None, relation=True)]
    result = build_projection({"counts": {"total": 2}, "entries": entries, "semantic_sha256": "c" * 64}, _accounting(entries), _baseline(), require_canonical_baseline=False)
    summary = result["deduplicated_summary"]
    assert summary["unique_source_way_count"] == 1
    assert summary["unique_relation_count"] == 1


def test_duplicate_edge_is_rejected() -> None:
    root = _root()
    entry = _entry("p1", "final_permission", root_ids=[root["root_cause_record_id"]])
    with pytest.raises(BlockerProjectionError, match="duplicate causal edge"):
        build_projection({"counts": {"total": 1}, "entries": [entry], "semantic_sha256": "c" * 64}, _accounting([entry], root, duplicate_edge=True), _baseline(), require_canonical_baseline=False)


def test_missing_root_reference_is_rejected() -> None:
    entry = _entry("p1", "final_permission", root_ids=["missing"])
    with pytest.raises(BlockerProjectionError, match="missing permission root reference"):
        build_projection({"counts": {"total": 1}, "entries": [entry], "semantic_sha256": "c" * 64}, _accounting([entry]), _baseline(), require_canonical_baseline=False)


def test_fabricated_suppressed_blocker_is_rejected() -> None:
    entry = _entry("speed1", "speed")
    with pytest.raises(BlockerProjectionError, match="suppressed candidate references absent blocker"):
        build_projection({"counts": {"total": 1}, "entries": [entry], "semantic_sha256": "c" * 64}, _accounting([entry], fake_suppressed=True), _baseline(), require_canonical_baseline=False)


def test_canonical_baseline_sha_mismatch_is_rejected() -> None:
    entry = _entry("speed1", "speed")
    bad = copy.deepcopy(_baseline())
    bad["canonical_run"]["run_id"] = "run_4"
    bad["formal_blocker_baseline"]["semantic_sha256"] = "d" * 64
    with pytest.raises(BlockerProjectionError, match="SHA mismatch"):
        build_projection({"counts": {"total": 115935}, "entries": [entry], "semantic_sha256": "c" * 64}, _accounting([entry]), bad)
