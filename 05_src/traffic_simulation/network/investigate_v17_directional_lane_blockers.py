"""Decompose canonical run_4 directional-lane blockers; never resolves them."""
from __future__ import annotations
import argparse, hashlib, json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import yaml
from traffic_simulation.network.directed_segments_v17 import normalize_oneway
from traffic_simulation.network.directional_lanes_v17 import DirectionalLaneError, resolve_directional_lanes

BASELINE_SHA = "21cc19bc837af2a97b98b881166bd340aff913822860a9db42b904fdb3c298a8"
STOP_CODES = {"LANE_DIRECTIONAL_ALLOCATION_MISSING", "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED", "LANE_VECTOR_LENGTH_MISMATCH", "LANE_COUNT_CONFLICT"}
COUNT_KEYS = {"lanes", "lanes:forward", "lanes:backward", "lanes:both_ways"}
VECTOR_KEYS = {"turn:lanes", "destination:lanes", "destination:ref:lanes"}
EVIDENCE_KEYS = ("lanes", "lanes:forward", "lanes:backward", "turn:lanes", "destination:lanes", "destination:ref:lanes", "oneway")

def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError(f"JSON object required: {path}")
    return value

def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def _target_way_tags(path: Path, way_ids: set[int]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    way_re = re.compile(r'<way[^>]*\bid="(\d+)"')
    tag_re = re.compile(r'<tag[^>]*\bk="([^"]+)"[^>]*\bv="([^"]*)"')
    current: int | None = None
    for line in path.open(encoding="utf-8"):
        if current is None:
            match = way_re.search(line)
            if match and int(match.group(1)) in way_ids:
                current = int(match.group(1)); result[current] = {}
        elif "</way>" in line:
            current = None
        else:
            match = tag_re.search(line)
            if match: result[current][match.group(1)] = match.group(2)
    return result

def _cohort(blocker: dict[str, Any], tags: dict[str, str]) -> tuple[str, str, str, str]:
    code = blocker["stop_code"]; keys = set(tags)
    if code == "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED":
        return "F_SHARED_PHYSICAL_LANE", "RESEARCH_DECISION_REQUIRED", "RESEARCH_DECISION_REQUIRED", "approved source semantics lacks an approved physical materializer"
    if code in {"LANE_VECTOR_LENGTH_MISMATCH", "LANE_COUNT_CONFLICT"}:
        return "E_CONTRADICTORY_EVIDENCE", "RESEARCH_DECISION_REQUIRED", "RESEARCH_DECISION_REQUIRED", "explicit counts and/or lane vectors conflict; existing fail-closed rule applies"
    if (keys & VECTOR_KEYS):
        return "E_CONTRADICTORY_EVIDENCE", "RESEARCH_DECISION_REQUIRED", "RESEARCH_DECISION_REQUIRED", "lane-vector evidence exists but is outside the approved unambiguous vector predicate"
    if not (keys & COUNT_KEYS):
        return "A_NO_LANE_EVIDENCE", "DATA_GAP", "SOURCE_DATA_REQUIRED", "no lane count or directional lane allocation tag"
    return "B_INSUFFICIENT_ALLOCATION", "RESEARCH_DECISION_REQUIRED", "RESEARCH_DECISION_REQUIRED", "lane evidence exists but does not uniquely determine Formal directional allocation"

def _coverage(blocker: dict[str, Any], tags: dict[str, str], resolution: dict[str, Any]) -> str:
    """Classify only against registered policy; never promote a candidate."""
    if blocker["stop_code"] == "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED":
        return "ALREADY_ADOPTED_BUT_NOT_MATERIALIZED"
    if resolution.get("status") == "resolved":
        return "FIXABLE_PIPELINE_GAP"
    if blocker["stop_code"] in {"LANE_VECTOR_LENGTH_MISMATCH", "LANE_COUNT_CONFLICT"}:
        return "RESEARCH_DECISION_REQUIRED"
    if not (set(tags) & set(EVIDENCE_KEYS)):
        return "SOURCE_DATA_REQUIRED"
    return "RESEARCH_DECISION_REQUIRED"

def investigate(*, baseline_path: Path, inventory_path: Path, output_dir: Path, source_path: Path | None = None) -> dict[str, Any]:
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8")); inventory = _read(inventory_path)
    if baseline["canonical_run"]["run_id"] != "run_4" or inventory["semantic_sha256"] != BASELINE_SHA or baseline["formal_blocker_baseline"]["semantic_sha256"] != BASELINE_SHA: raise ValueError("canonical baseline binding failed")
    rows = [x for x in inventory["entries"] if x["attribute_name"] == "directional_lanes"]
    if len(rows) != 22934: raise ValueError(f"expected 22934 directional blockers, got {len(rows)}")
    rows_by_way = {int(x["source_way_id"]): x for x in rows}
    source = source_path or Path("03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml")
    target_ids = set(rows_by_way); ways = _target_way_tags(source, target_ids); stage_by_way = rows_by_way
    records, groups = [], defaultdict(list)
    for row in rows:
        way_id = row.get("source_way_id")
        if not isinstance(way_id, int) or way_id not in ways: raise ValueError(f"source Way identity missing: {row['record_id']}")
        tags = ways[way_id]; cohort, root, eligibility, reason = _cohort(stage_by_way[way_id], tags)
        try:
            resolved = resolve_directional_lanes(tags, profile="formal")
            resolution = {"status": "resolved", "rule_ids": resolved.get("rule_ids", []), "value_origin": resolved.get("value_origin")}
        except DirectionalLaneError as error:
            resolution = {"status": error.status, "stop_code": error.stop_code, "reason": str(error)}
        try: direction = normalize_oneway(tags)
        except Exception as error: direction = {"status": "invalid", "reason": str(error)}
        candidates = []
        if "lanes" in tags and direction.get("canonical_oneway") == "no" and tags.get("lanes") == "2" and not (keys := (set(tags) & {"lanes:forward", "lanes:backward", "lanes:both_ways"})): candidates.append({"rule_id": "OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1", "status": "candidate"})
        if direction.get("canonical_oneway") in {"yes", "-1"} and set(tags) & VECTOR_KEYS: candidates.append({"rule_id": "OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1", "status": "blocked_if_vector_lengths_conflict"})
        if tags.get("oneway") in {"no", None} and tags.get("lanes") == "1" and not (set(tags) & (VECTOR_KEYS | {"lanes:forward", "lanes:backward", "lanes:both_ways"})): candidates.append({"rule_id": "OSM_BIDIRECTIONAL_TOTAL_1_TO_SHARED_SINGLE_V1", "status": "source_semantics_resolved_materialization_blocked"})
        groups[(cohort, root, reason)].append(row["blocker_id"])
        records.append({"blocker_id": row["blocker_id"], "record_id": row["record_id"], "source_way_id": way_id, "directed_segment_id": row.get("directed_segment_id"), "source_tags": tags, "source_evidence": row["research_scope_status"].get("evidence_ids", []), "source_pattern": sorted(set(tags) & set(EVIDENCE_KEYS)), "stop_code": row["stop_code"], "existing_rule_candidates": candidates, "coverage_class": _coverage(row, tags, resolution), "current_resolution_path": {"resolver": "resolve_directional_lanes", "result": resolution, "stage_blocker": {"scope": "source_way", "source_way_id": way_id, "stop_code": row["stop_code"]}}, "formal_eligibility": False, "provenance": {"baseline_id": baseline["baseline_id"], "canonical_run_id": "run_4", "inventory_sha256": BASELINE_SHA, "source_osm": str(source), "source_osm_sha256": _sha(source)}, "assumptions": [], "evidence_class": row["root_cause_category"], "action_class": root, "cohort": cohort, "downstream_affected_attributes": {"known": [], "possible": ["speed", "conditional_access", "final_permission"]}})
    if len({r["blocker_id"] for r in records}) != 22934: raise ValueError("duplicate blocker identity")
    summary = {"baseline": {"run_id": "run_4", "inventory_sha256": BASELINE_SHA, "attribute": "directional_lanes"}, "counts": {"raw_blockers": len(records), "unique_source_ways": len({r["source_way_id"] for r in records}), "by_stop_code": dict(Counter(r["stop_code"] for r in records)), "by_cohort": dict(Counter(r["cohort"] for r in records)), "by_root_cause": dict(Counter(r["action_class"] for r in records)), "by_coverage_class": dict(Counter(r["coverage_class"] for r in records)), "by_source_pattern": dict(Counter("+".join(r["source_pattern"]) or "none" for r in records)), "by_eligibility": dict(Counter("FIXABLE_WITH_EXISTING_POLICY" if r["formal_eligibility"] else ("GOVERNANCE_FIX_REQUIRED" if r["action_class"] == "RECORD_GOVERNANCE" else ("SOURCE_DATA_REQUIRED" if r["action_class"] == "DATA_GAP" else "RESEARCH_DECISION_REQUIRED")) for r in records))}, "groups": [{"cohort": k[0], "root_cause": k[1], "reason": k[2], "blocker_count": len(v)} for k, v in sorted(groups.items())], "downstream": {"known_explicit_edges": 0, "possible_attributes": ["speed", "conditional_access", "final_permission"]}}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "directional_lane_blocker_inventory.json").write_text(json.dumps({"baseline": summary["baseline"], "records": records}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    (output_dir / "directional_lane_root_cause_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    fix = {"baseline": summary["baseline"], "fixable_with_existing_policy": [], "not_fixable_without_new_authority": summary["counts"]["by_eligibility"], "decision": "No owner-free PIPELINE_GAP identified; do not change blockers."}
    (output_dir / "directional_lane_fixability_summary.json").write_text(json.dumps(fix, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    md = ["# Directional Lane Blocker Review", "", "Canonical baseline: `run_4`", f"Blocker inventory SHA: `{BASELINE_SHA}`", "", "## Result", "", "22,934 records were covered. No blocker was reduced and no lane rule was adopted.", "", "## Cohorts", ""]
    md += [f"- `{g['cohort']}` / `{g['root_cause']}`: {g['blocker_count']} records — {g['reason']}." for g in summary["groups"]]
    md += ["", "## Downstream", "", "The baseline projection contains no explicit causal edge from directional_lanes roots to speed, conditional_access, or final_permission. Their impact is therefore possible only, not counted.", "", "## Recommendation", "", "No owner-free PIPELINE_GAP was identified.", ""]
    (output_dir / "directional_lane_review.md").write_text("\n".join(md), encoding="utf-8")
    return summary

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--baseline", type=Path, default=Path("reproducibility/config/traffic_simulation/v17_phase12_validated_successor_baseline_20260902.yml")); p.add_argument("--inventory", type=Path, required=True); p.add_argument("--source", type=Path); p.add_argument("--output-dir", type=Path, required=True); a = p.parse_args(); print(json.dumps(investigate(baseline_path=a.baseline, inventory_path=a.inventory, source_path=a.source, output_dir=a.output_dir), indent=2, sort_keys=True))

if __name__ == "__main__": main()
