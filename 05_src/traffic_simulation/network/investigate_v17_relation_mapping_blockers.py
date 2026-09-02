"""Investigate run_4 relation mapping blockers without changing resolution."""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping
import yaml
from traffic_simulation.network.directed_segments_v17 import DirectedSegmentError, _governed_highways, _xml_source, map_turn_restriction

STOP_CODE = "RELATION_DIRECTED_MAPPING_MISSING"
BASELINE_SHA = "21cc19bc837af2a97b98b881166bd340aff913822860a9db42b904fdb3c298a8"
RELATION_RE = re.compile(r"relation:(\d+):")

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError(f"JSON object required: {path}")
    return value

def _relation_id(record: Mapping[str, Any]) -> int:
    match = RELATION_RE.search(str(record["record_id"]))
    if not match: raise ValueError(f"relation identity missing: {record['record_id']}")
    return int(match.group(1))

def _classify(relation: Mapping[str, Any], ways: Mapping[int, Mapping[str, Any]]) -> tuple[str, str, str]:
    members = relation["members"]
    fc = sum(m["type"] == "way" and m["role"] == "from" for m in members)
    tc = sum(m["type"] == "way" and m["role"] == "to" for m in members)
    vc = sum(m["role"] == "via" for m in members)
    missing_roles = [role for role, count in (("from", fc), ("to", tc), ("via", vc)) if count != 1]
    missing_ways = sorted({int(m["ref"]) for m in members if m["type"] == "way"} - set(ways))
    if missing_roles:
        return "DATA_GAP", "SOURCE_DATA_REQUIRED", "required member role/count missing: " + ",".join(missing_roles)
    if missing_ways:
        return "RECORD_GOVERNANCE", "GOVERNANCE_FIX_REQUIRED", "relation closure lacks referenced Way: " + ",".join(map(str, missing_ways))
    if not relation["tags"].get("restriction") and not relation["tags"].get("restriction:bus"):
        return "RECORD_GOVERNANCE", "GOVERNANCE_FIX_REQUIRED", "restriction relation lacks registered restriction value"
    return "RECORD_GOVERNANCE", "GOVERNANCE_FIX_REQUIRED", "complete relation members do not connect to an exact source-node candidate"

def investigate(*, baseline_path: Path, inventory_path: Path, formal_path: Path, output_dir: Path) -> dict[str, Any]:
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    inventory, formal = _read(inventory_path), _read(formal_path)
    if baseline["canonical_run"]["run_id"] != "run_4": raise ValueError("canonical run is not run_4")
    if inventory["semantic_sha256"] != BASELINE_SHA or baseline["formal_blocker_baseline"]["semantic_sha256"] != BASELINE_SHA: raise ValueError("run_4 blocker inventory SHA mismatch")
    entries = [x for x in inventory["entries"] if x["stop_code"] == STOP_CODE]
    if len(entries) != 48: raise ValueError(f"expected 48 blockers, got {len(entries)}")
    source = Path(formal["stage_outputs"]["directed_segments"]["source"]["path"])
    ways, relations, _ = _xml_source(source, set(_governed_highways()))
    relation_by_id = {r["relation_id"]: r for r in relations}
    segments = formal["stage_outputs"]["directed_segments"]["directed_segments"]
    by_way: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for segment in segments: by_way[int(segment["source_way_id"])].append(segment)
    stage_blockers = {x["relation_id"]: x for x in formal["stage_outputs"]["directed_segments"]["blockers"] if x["stop_code"] == STOP_CODE}
    records, groups = [], defaultdict(list)
    for entry in entries:
        rid = _relation_id(entry); relation = relation_by_id.get(rid)
        if relation is None: raise ValueError(f"source relation missing: {rid}")
        members = relation["members"]; relevant = sorted({int(m["ref"]) for m in members if m["type"] == "way"})
        available = {str(w): sorted(s["directed_segment_id"] for s in by_way.get(w, [])) for w in relevant}
        try:
            mapping = map_turn_restriction(relation, ways=ways, segments=[s for w in relevant for s in by_way.get(w, [])])
            resolution = {"status": "mapped", "mapping": mapping}
        except DirectedSegmentError as error:
            resolution = {"status": error.status, "stop_code": error.stop_code, "reason": str(error)}
        except (KeyError, ValueError) as error:
            resolution = {"status": "invalid_source_reference", "reason": str(error)}
        root_class, eligibility, reason = _classify(relation, ways); groups[(root_class, reason)].append(rid)
        records.append({"blocker_id": entry["blocker_id"], "record_id": entry["record_id"], "relation_id": rid, "relation_type": relation["tags"].get("type"), "relation_tags": relation["tags"], "source_members": members, "relevant_way_ids": relevant, "expected_directed_segment_identity": {"method": "exact_source_node_lineage", "status": "indeterminate_until_source_gap_is_resolved"}, "existing_directed_segment_candidates": available, "current_resolution": resolution, "artifact_resolution_status": stage_blockers[rid], "provenance": {"baseline_id": baseline["baseline_id"], "canonical_run_id": "run_4", "inventory_sha256": BASELINE_SHA, "source_osm": str(source), "source_osm_sha256": _sha(source)}, "root_cause": {"class": root_class, "eligibility": eligibility, "reason": reason}, "downstream_affected_attributes": {"known": [], "possible": ["directional_lanes", "speed", "conditional_access", "final_permission"]}})
    records.sort(key=lambda x: x["relation_id"])
    if len({r["blocker_id"] for r in records}) != 48 or len({r["relation_id"] for r in records}) != 48: raise ValueError("duplicate blocker or relation identity")
    summary = {"baseline": {"run_id": "run_4", "inventory_sha256": BASELINE_SHA, "stop_code": STOP_CODE}, "counts": {"raw_blockers": 48, "unique_relations": 48, "unique_root_cause_groups": len(groups), "by_root_cause_class": dict(Counter(r["root_cause"]["class"] for r in records)), "by_eligibility": dict(Counter(r["root_cause"]["eligibility"] for r in records)), "by_resolution_reason": dict(Counter(r["current_resolution"].get("reason", "mapped") for r in records))}, "groups": [{"root_cause_class": k[0], "reason": k[1], "relation_ids": sorted(v), "blocker_count": len(v), "eligibility": next(r["root_cause"]["eligibility"] for r in records if r["relation_id"] == v[0])} for k, v in sorted(groups.items())]}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "relation_directed_mapping_blocker_inventory.json").write_text(json.dumps({"baseline": summary["baseline"], "records": records}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    (output_dir / "relation_directed_mapping_root_cause_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    md = ["# Relation Directed Mapping Blocker Review", "", "Canonical baseline: `run_4`", f"Inventory semantic SHA: `{BASELINE_SHA}`", "", "## Groups", ""]
    md += [f"- `{g['root_cause_class']}` / `{g['eligibility']}`: {g['blocker_count']} relations ({', '.join(map(str, g['relation_ids']))}); {g['reason']}." for g in summary["groups"]]
    md += ["", "## Downstream impact", "", "No explicit causal edge from these relation blockers to downstream attributes exists in the baseline projection. Known downstream blocker count is therefore zero; directional_lanes, speed, conditional_access, and final_permission are possible consumers only and are not counted.", "", "## Decision", "", "No owner-free PIPELINE_GAP was identified. Source completeness and relation-record governance must precede implementation.", ""]
    (output_dir / "relation_directed_mapping_review.md").write_text("\n".join(md), encoding="utf-8")
    return summary

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path("reproducibility/config/traffic_simulation/v17_phase12_validated_successor_baseline_20260902.yml"))
    parser.add_argument("--inventory", type=Path, required=True); parser.add_argument("--formal", type=Path, required=True); parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(investigate(baseline_path=args.baseline, inventory_path=args.inventory, formal_path=args.formal, output_dir=args.output_dir), indent=2, sort_keys=True))

if __name__ == "__main__": main()
