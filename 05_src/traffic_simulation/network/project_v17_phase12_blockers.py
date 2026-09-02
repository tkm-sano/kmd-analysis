"""Project the validated Phase 12 blocker inventory into deduplicated lineage views."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from traffic_simulation.network import execute_v17_phase12_full_population as phase12


BASELINE_DEFAULT = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase12_validated_successor_baseline_20260902.yml"
)
PROJECTION_DEFAULT = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase12_20260902_profile_difference_v1_2/runs/run_4/projection"
)
REQUIRED_ATTRIBUTES = frozenset(
    {"directed_segments", "directional_lanes", "speed", "conditional_access", "final_permission"}
)
EVIDENCE_CLASSES = frozenset(
    {"genuine_rule_conflict", "missing_evidence", "missing_registered_rule", "unsupported_source_syntax"}
)
ACTION_CLASS = {
    "genuine_rule_conflict": "RESEARCH_DECISION_REQUIRED",
    "missing_evidence": "DATA_GAP",
    "missing_registered_rule": "PIPELINE_GAP",
    "unsupported_source_syntax": "PIPELINE_GAP",
}
_RELATION_RE = re.compile(r"(?:^|:)relation:(\d+):")


class BlockerProjectionError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BlockerProjectionError(f"JSON object required: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BlockerProjectionError(f"YAML object required: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_sha(value: Mapping[str, Any]) -> str:
    return phase12._semantic_hash(value)


def _relation_id(record: Mapping[str, Any]) -> int | None:
    for value in (record.get("record_id"), record.get("blocker_id")):
        match = _RELATION_RE.search(str(value))
        if match:
            return int(match.group(1))
    return None


def _source_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    source_way_id = record.get("source_way_id")
    relation_id = _relation_id(record)
    if source_way_id is not None:
        if not isinstance(source_way_id, int) or isinstance(source_way_id, bool) or source_way_id < 1:
            raise BlockerProjectionError(f"invalid source_way_id: {record.get('record_id')}")
        return {"source_way_id": source_way_id, "relation_id": relation_id}
    if relation_id is not None:
        return {"source_way_id": None, "relation_id": relation_id}
    raise BlockerProjectionError(f"blocker lacks source Way or relation identity: {record.get('record_id')}")


def _stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()}"


def _root_node_from_blocker(record: Mapping[str, Any]) -> dict[str, Any]:
    identity = _source_identity(record)
    key = {
        "root_cause_class": record["root_cause_category"],
        "source_identity": identity,
        "primary_attribute": record["attribute_name"],
        "stop_code": record["stop_code"],
        "directed_segment_id": record.get("directed_segment_id"),
        "lane_position": record.get("lane_position"),
        "vehicle_class": record.get("vehicle_class"),
    }
    return {
        "root_cause_id": _stable_id("root-cause:inventory", key),
        "root_cause_class": record["root_cause_category"],
        "action_class": ACTION_CLASS.get(record["root_cause_category"], "RECORD_GOVERNANCE"),
        "source_identity": identity,
        "source_evidence": list(record["research_scope_status"].get("evidence_ids", [])),
        "primary_attribute": record["attribute_name"],
        "stop_code": record["stop_code"],
        "source_record_ids": [record["record_id"]],
        "explicit_upstream_reference": False,
    }


def _root_node_from_accounting(root: Mapping[str, Any]) -> dict[str, Any]:
    identity = {"source_way_id": int(root["source_way_id"]), "relation_id": None}
    return {
        "root_cause_id": root["root_cause_record_id"],
        "root_cause_class": root["root_cause_category"],
        "action_class": ACTION_CLASS[root["root_cause_category"]],
        "source_identity": identity,
        "source_evidence": sorted(
            {f"source_way:{root['source_way_id']}", *[f"access_key:{x}" for x in root.get("access_tag_keys", [])]}
        ),
        "primary_attribute": "final_permission",
        "stop_code": root["stop_code"],
        "source_record_ids": [],
        "explicit_upstream_reference": True,
        "cause_kind": root["cause_kind"],
        "candidate_rule_ids": list(root.get("candidate_rule_ids", [])),
        "decision_id": None,
    }


def _downstream_node(record: Mapping[str, Any]) -> dict[str, Any]:
    identity = _source_identity(record)
    if record["attribute_name"] == "final_permission":
        required = ("directed_segment_id", "lane_position", "vehicle_class")
        if any(record.get(field) in (None, "") for field in required):
            raise BlockerProjectionError(f"permission blocker has incomplete identity: {record['record_id']}")
    rule_id = record.get("remediation", {}).get("rule_id")
    return {
        "blocker_id": record["blocker_id"],
        "record_id": record["record_id"],
        "attribute": record["attribute_name"],
        "source_identity": identity,
        "directed_segment_id": record.get("directed_segment_id"),
        "lane_position": record.get("lane_position"),
        "vehicle_class": record.get("vehicle_class"),
        "stop_code": record["stop_code"],
        "evidence_class": record["root_cause_category"],
        "action_class": ACTION_CLASS.get(record["root_cause_category"], "RECORD_GOVERNANCE"),
        "rule_ids": [str(rule_id)] if rule_id else [],
        "provenance": list(record["research_scope_status"].get("evidence_ids", [])),
    }


def _baseline_context(
    baseline: Mapping[str, Any],
    inventory: Mapping[str, Any],
    *,
    require_canonical_baseline: bool,
) -> dict[str, Any]:
    canonical = baseline.get("canonical_run", {})
    blocker = baseline.get("formal_blocker_baseline", {})
    if require_canonical_baseline and canonical.get("run_id") != "run_4":
        raise BlockerProjectionError("canonical baseline is not run_4")
    expected = blocker.get("semantic_sha256")
    actual = inventory.get("semantic_sha256")
    if require_canonical_baseline and (
        expected != actual
        or actual != _semantic_sha(inventory)
        or expected != "21cc19bc837af2a97b98b881166bd340aff913822860a9db42b904fdb3c298a8"
    ):
        raise BlockerProjectionError("canonical run_4 blocker inventory SHA mismatch")
    if require_canonical_baseline and (inventory.get("counts", {}).get("total") != 115935 or len(inventory.get("entries", [])) != 115935):
        raise BlockerProjectionError("canonical blocker total differs from 115935")
    return {
        "baseline_id": baseline["baseline_id"],
        "canonical_run_id": canonical["run_id"],
        "source_commit": canonical["source_commit"],
        "blocker_inventory_semantic_sha256": actual,
        "population_version": canonical["population_version"],
    }


def build_projection(
    inventory: Mapping[str, Any],
    accounting: Mapping[str, Any],
    baseline: Mapping[str, Any],
    *,
    require_canonical_baseline: bool = True,
) -> dict[str, Any]:
    context = _baseline_context(
        baseline, inventory, require_canonical_baseline=require_canonical_baseline
    )
    entries = list(inventory.get("entries", []))
    if not entries:
        raise BlockerProjectionError("empty blocker inventory")
    if set(item["attribute_name"] for item in entries) - REQUIRED_ATTRIBUTES:
        raise BlockerProjectionError("inventory contains an attribute outside the P0 projection")
    if set(item["root_cause_category"] for item in entries) - EVIDENCE_CLASSES:
        raise BlockerProjectionError("inventory contains an unrecognized evidence class")
    if inventory["counts"]["total"] != len(entries):
        raise BlockerProjectionError("raw blocker count does not equal inventory entries")

    blockers = {item["record_id"]: _downstream_node(item) for item in entries}
    if len(blockers) != len(entries) or len({item["blocker_id"] for item in entries}) != len(entries):
        raise BlockerProjectionError("duplicate blocker identity")

    roots: dict[str, dict[str, Any]] = {}
    for root in accounting.get("root_cause_records", []):
        node = _root_node_from_accounting(root)
        if node["root_cause_id"] in roots:
            raise BlockerProjectionError("duplicate explicit root-cause identity")
        roots[node["root_cause_id"]] = node
    root_for_record: dict[str, str] = {}
    for item in entries:
        if item["attribute_name"] == "final_permission":
            refs = item.get("root_cause_record_ids", [])
            if len(refs) != 1 or refs[0] not in roots:
                raise BlockerProjectionError(f"missing permission root reference: {item['record_id']}")
            root_for_record[item["record_id"]] = refs[0]
        else:
            node = _root_node_from_blocker(item)
            roots.setdefault(node["root_cause_id"], node)
            root_for_record[item["record_id"]] = node["root_cause_id"]

    edges = []
    seen_edges: set[tuple[str, str]] = set()
    for edge in accounting.get("blocker_relationships", {}).get("causal_edges", []):
        root_id = edge["root_cause_record_id"]
        downstream_id = edge["downstream_record_id"]
        if root_id not in roots or downstream_id not in blockers:
            raise BlockerProjectionError("causal edge references absent root or blocker")
        pair = (root_id, downstream_id)
        if pair in seen_edges:
            raise BlockerProjectionError("duplicate causal edge")
        seen_edges.add(pair)
        edges.append({
            "root_cause_id": root_id,
            "downstream_blocker_id": downstream_id,
            "edge_reason": edge["relationship"],
            "provenance": "population_accounting.blocker_relationships.causal_edges",
            "rule_ids": [],
            "decision_id": None,
        })
    expected_permission_edges = {
        (root_for_record[item["record_id"]], item["record_id"])
        for item in entries if item["attribute_name"] == "final_permission"
    }
    if {(item["root_cause_id"], item["downstream_blocker_id"]) for item in edges} != expected_permission_edges:
        raise BlockerProjectionError("permission causal edge coverage differs")

    suppressed = []
    for item in accounting.get("blocker_relationships", {}).get("suppressed_candidates", []):
        source_record_id = item["root_cause_record_id"]
        if source_record_id not in blockers:
            raise BlockerProjectionError("suppressed candidate references absent blocker")
        root_id = root_for_record[source_record_id]
        suppressed.append({
            "root_cause_id": root_id,
            "upstream_blocker_id": source_record_id,
            "relationship": "candidate_suppressed",
            "suppressed_directed_segment_count": item["suppressed_directed_segment_count"],
            "suppressed_lane_tuple_count": item["suppressed_lane_tuple_count"],
            "provenance": "population_accounting.blocker_relationships.suppressed_candidates",
        })
    if len(suppressed) != len(entries) - len(expected_permission_edges):
        raise BlockerProjectionError("suppressed candidate coverage differs")

    by_attribute = Counter(item["attribute"] for item in blockers.values())
    by_evidence = Counter(item["evidence_class"] for item in blockers.values())
    source_ways = {item["source_identity"]["source_way_id"] for item in blockers.values() if item["source_identity"]["source_way_id"] is not None}
    relations = {item["source_identity"]["relation_id"] for item in blockers.values() if item["source_identity"]["relation_id"] is not None}
    directed = {item["directed_segment_id"] for item in blockers.values() if item["directed_segment_id"]}
    lanes = {(item["directed_segment_id"], item["lane_position"]) for item in blockers.values() if item["directed_segment_id"] and item["lane_position"] is not None}
    permissions = {(item["directed_segment_id"], item["lane_position"], item["vehicle_class"]) for item in blockers.values() if item["attribute"] == "final_permission"}
    root_fanout = Counter(item["root_cause_id"] for item in edges)
    projection = {
        **context,
        "raw_blocker_record_count": len(entries),
        "root_cause_count": len(roots),
        "blockers": list(blockers.values()),
        "roots": list(sorted(roots.values(), key=lambda x: x["root_cause_id"])),
        "edges": sorted(edges, key=lambda x: (x["root_cause_id"], x["downstream_blocker_id"])),
        "suppressed_candidates": sorted(suppressed, key=lambda x: x["upstream_blocker_id"]),
        "fanout": {key: value for key, value in sorted(root_fanout.items())},
        "unlinked_upstream_cause_count": sum(1 for item in roots.values() if not item["explicit_upstream_reference"]),
    }
    summary = {
        **context,
        "raw_blocker_record_count": len(entries),
        "unique_root_cause_count": len(roots),
        "unique_source_way_count": len(source_ways),
        "unique_relation_count": len(relations),
        "unique_directed_segment_count": len(directed),
        "unique_lane_identity_count": len(lanes),
        "unique_permission_identity_count": len(permissions),
        "causal_edge_count": len(edges),
        "suppressed_candidate_count": len(suppressed),
        "one_root_to_n_downstream_root_count": sum(value > 1 for value in root_fanout.values()),
        "max_downstream_fanout": max(root_fanout.values(), default=0),
        "simple_sum_allowed": False,
        "by_attribute": dict(sorted(by_attribute.items())),
        "by_evidence_class": dict(sorted(by_evidence.items())),
        "by_action_class": dict(sorted(Counter(ACTION_CLASS[item["evidence_class"]] for item in blockers.values()).items())),
        "identity_availability": {"source_way": True, "relation": bool(relations), "directed_segment": bool(directed), "lane": bool(lanes), "permission": bool(permissions)},
    }
    attribute_summary = []
    for attribute in sorted(REQUIRED_ATTRIBUTES):
        selected = [item for item in blockers.values() if item["attribute"] == attribute]
        attribute_summary.append({
            "attribute": attribute,
            "raw_blocker_count": len(selected),
            "unique_source_way_count": len({item["source_identity"]["source_way_id"] for item in selected if item["source_identity"]["source_way_id"] is not None}),
            "unique_relation_count": len({item["source_identity"]["relation_id"] for item in selected if item["source_identity"]["relation_id"] is not None}),
            "by_evidence_class": dict(sorted(Counter(item["evidence_class"] for item in selected).items())),
            "by_action_class": dict(sorted(Counter(item["action_class"] for item in selected).items())),
            "root_cause_count": len({root_for_record[item["record_id"]] for item in entries if item["attribute_name"] == attribute}),
        })
    root_inventory = {**context, "root_causes": projection["roots"]}
    return {"root_cause_inventory": root_inventory, "root_cause_blocker_projection": projection, "deduplicated_summary": summary, "attribute_summary": {**context, "attributes": attribute_summary}}


def validate_projection(
    outputs: Mapping[str, Mapping[str, Any]],
    inventory: Mapping[str, Any],
    accounting: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> dict[str, str]:
    expected = build_projection(inventory, accounting, baseline)
    if outputs != expected:
        raise BlockerProjectionError("projection output differs from recomputed canonical projection")
    if outputs["deduplicated_summary"]["raw_blocker_record_count"] != 115935:
        raise BlockerProjectionError("projection raw count differs")
    return {"baseline_binding": "passed", "identity": "passed", "causal_edges": "passed", "deduplication": "passed", "projection": "passed"}


def _markdown(outputs: Mapping[str, Mapping[str, Any]]) -> str:
    summary = outputs["deduplicated_summary"]
    lines = [
        "# Phase 12 Formal Blocker Root-Cause Projection",
        "",
        f"- Canonical baseline: `{summary['canonical_run_id']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Blocker inventory semantic SHA: `{summary['blocker_inventory_semantic_sha256']}`",
        f"- Raw blocker records: **{summary['raw_blocker_record_count']:,}**",
        "- Simple cross-population sum: **forbidden**",
        "",
        "## Deduplicated identity summary",
        "",
        "| Identity | Count |",
        "|---|---:|",
    ]
    labels = (("unique_root_cause_count", "root causes"), ("unique_source_way_count", "source Ways"), ("unique_relation_count", "relations"), ("unique_directed_segment_count", "directed segments"), ("unique_lane_identity_count", "lane identities"), ("unique_permission_identity_count", "permission identities"))
    lines.extend(f"| {label} | {summary[key]:,} |" for key, label in labels)
    lines.extend(["", "## Attribute decomposition", "", "| Attribute | Raw blockers | Unique root causes |", "|---|---:|---:|"])
    lines.extend(f"| {item['attribute']} | {item['raw_blocker_count']:,} | {item['root_cause_count']:,} |" for item in outputs["attribute_summary"]["attributes"])
    lines.extend(["", "## Causal interpretation", "", f"- Explicit root-cause → permission edges: **{summary['causal_edge_count']:,}**.", f"- Suppressed upstream candidates: **{summary['suppressed_candidate_count']:,}**.", f"- Roots with multiple downstream blockers: **{summary['one_root_to_n_downstream_root_count']:,}**.", "- Lane/speed/access causality is not inferred where the baseline accounting has no explicit edge.", "- Evidence class and action class remain separate axes.", ""])
    return "\n".join(lines)


def generate(baseline_path: Path = BASELINE_DEFAULT, output_dir: Path = PROJECTION_DEFAULT) -> dict[str, Any]:
    baseline = _load_yaml(baseline_path)
    root = Path(baseline["canonical_run"]["artifact_root"])
    inventory = _load_json(root / "formal/blocker_inventory.json")
    accounting = _load_json(root / "population_accounting.json")
    outputs = build_projection(inventory, accounting, baseline)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "root_cause_inventory": "root_cause_inventory.json",
        "root_cause_blocker_projection": "root_cause_blocker_projection.json",
        "deduplicated_summary": "deduplicated_summary.json",
        "attribute_summary": "attribute_summary.json",
    }
    for key, filename in files.items():
        (output_dir / filename).write_text(json.dumps(outputs[key], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (output_dir / "report.md").write_text(_markdown(outputs), encoding="utf-8")
    return {"result": "passed", "output_dir": str(output_dir), "files": sorted(files.values()) + ["report.md"], "raw_blocker_record_count": outputs["deduplicated_summary"]["raw_blocker_record_count"]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=PROJECTION_DEFAULT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(generate(args.baseline, args.output_dir), ensure_ascii=False, sort_keys=True))
    except Exception as error:
        print(json.dumps({"result": "failed", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
