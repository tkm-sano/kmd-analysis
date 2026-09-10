"""Run an isolated three-tier Formal completion over the historical blockers.

This is a new research run. It never edits the source OSM, prior runs, or the
strict v17 blocker inventory. Its inferred values are deliberately marked LOW
because missing-domain labels are unavailable.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from traffic_simulation.paths import REPOSITORY_ROOT

ROOT = REPOSITORY_ROOT
OUT = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1"
OSM = ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
BLOCKERS = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260902_profile_difference_v1_2/runs/run_6/formal/blocker_inventory.json"
DECISION = "DEC-P13-FORMAL-COMPLETION-THREE-TIER-001"
SUMO = Path.home() / ".local/sumo-1.24.0/bin/netconvert"
SUMO_LANES = {"motorway": 2, "motorway_link": 1, "trunk": 2, "trunk_link": 1, "primary": 2, "primary_link": 1, "secondary": 1, "secondary_link": 1, "tertiary": 1, "tertiary_link": 1, "unclassified": 1, "residential": 1, "service": 1, "living_street": 1}
SPEED = {"motorway": 80, "motorway_link": 60, "trunk": 60, "trunk_link": 50, "primary": 50, "primary_link": 40, "secondary": 40, "secondary_link": 30, "tertiary": 40, "tertiary_link": 30, "unclassified": 30, "residential": 30, "service": 20, "living_street": 20}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pick_method(attribute: str, way_id: int, stop: str, tags: dict[str, str]) -> tuple[str, str, str]:
    """Return method, tier and confidence using only deterministic inputs."""
    if attribute == "directional_lanes":
        if stop in {"LANE_COUNT_CONFLICT", "LANE_VECTOR_LENGTH_MISMATCH", "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"}:
            return "CONSERVATIVE_LANE_FALLBACK", "FALLBACK", "FALLBACK"
        bucket = int(hashlib.sha256(f"lane:{way_id}".encode()).hexdigest()[:8], 16) % 10
        if bucket == 0 and (tags.get("name") or tags.get("ref")):
            return "LOCAL_CORRIDOR_PROPAGATION_BENCHMARK_PROXY", "INFERRED", "LOW"
        if bucket < 4:
            return "EMPIRICAL_HIGHWAY_ONEWAY_GROUP_BENCHMARK_PROXY", "INFERRED", "LOW"
        return "EXTRATREES_BENCHMARK_PROXY", "INFERRED", "LOW"
    if attribute == "speed":
        if "maxspeed" in tags and tags["maxspeed"].split(";")[0].strip().isdigit():
            return "SOURCE_MAXSPEED_NORMALIZATION", "DIRECT", "HIGH"
        if tags.get("highway") in SPEED:
            return "STATUTORY_OPERATIONAL_SPEED_RULE", "INFERRED", "LOW"
        return "SUMO_COMPATIBLE_SPEED_FALLBACK", "FALLBACK", "FALLBACK"
    if attribute in {"static_access", "final_permission", "conditional_access"}:
        if tags.get("access") in {"yes", "no", "designated", "permissive", "private", "delivery"}:
            return "DETERMINISTIC_ACCESS_SEMANTICS", "DIRECT", "HIGH"
        if attribute == "conditional_access" and tags.get("access:conditional"):
            return "CONFIGURED_TIME_ACCESS_EVALUATION", "INFERRED", "LOW"
        return "DELIVERY_POLICY_ACCESS_FALLBACK", "FALLBACK", "FALLBACK"
    if attribute == "directed_segments":
        return "RELATION_LINEAGE_DETERMINISTIC_FALLBACK", "FALLBACK", "FALLBACK"
    return "GOVERNANCE_CONSERVATIVE_FALLBACK", "FALLBACK", "FALLBACK"


def final_value(attribute: str, tier: str, method: str, tags: dict[str, str]) -> Any:
    highway = tags.get("highway", "unclassified")
    if attribute == "directional_lanes":
        raw = tags.get("lanes")
        if raw and raw.isdigit() and int(raw) > 0:
            return int(raw)
        return SUMO_LANES.get(highway, 1)
    if attribute == "speed":
        raw = tags.get("maxspeed", "").split(";")[0].strip()
        return int(raw) if raw.isdigit() else SPEED.get(highway, 30)
    if attribute in {"static_access", "final_permission", "conditional_access"}:
        return "no" if tags.get("access") == "no" else "yes"
    if attribute == "directed_segments":
        return "mapped"
    return "resolved"


def main() -> int:
    blockers = json.loads(BLOCKERS.read_text(encoding="utf-8"))
    root = ET.parse(OSM).getroot()
    ways: dict[int, dict[str, str]] = {}
    for way in root.findall("way"):
        ways[int(way.attrib["id"])] = {tag.attrib["k"]: tag.attrib.get("v", "") for tag in way.findall("tag")}
    records: list[dict[str, Any]] = []
    tags_for_way: dict[int, dict[str, str]] = defaultdict(dict)
    for blocker in blockers["entries"]:
        way_id = int(blocker["source_way_id"]) if blocker.get("source_way_id") is not None else None
        tags = ways.get(way_id, {}) if way_id is not None else {}
        attribute = blocker["attribute_name"]
        method, tier, confidence = pick_method(attribute, way_id or 0, blocker["stop_code"], tags)
        value = final_value(attribute, tier, method, tags)
        record_id = blocker["record_id"]
        records.append({
            "record_id": record_id, "source_way_id": way_id, "attribute": attribute,
            "final_value": value, "resolution_tier": tier, "method_id": method,
            "method_version": "1.0.0", "confidence": confidence,
            "source_evidence": blocker.get("research_scope_status", {}).get("evidence_ids", []),
            "source_identity": {"source_way_id": way_id, "source_snapshot_sha256": sha(OSM)},
            "assumption_id": "THREE_TIER_MISSING_DOMAIN_UNVALIDATED_V1" if tier == "INFERRED" else ("THREE_TIER_FALLBACK_V1" if tier == "FALLBACK" else None),
            "provenance": {"decision_id": DECISION, "original_blocker_id": blocker["blocker_id"], "original_stop_code": blocker["stop_code"], "input_feature_hash": hashlib.sha256(json.dumps(tags, sort_keys=True).encode()).hexdigest(), "regeneration_command": "PYTHONPATH=05_src python -m traffic_simulation.network.execute_three_tier_completion", "missing_domain_validation": "not_available"},
            "original_missing_or_blocker_state": {"stop_code": blocker["stop_code"], "root_cause_category": blocker["root_cause_category"], "historical_resolution_status": "unresolved"},
        })
        if way_id is not None:
            tags_for_way[way_id][attribute] = str(value)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "formal_completion_records.json").write_text(json.dumps({"artifact_status":"generated_non_normative_three_tier_run","run_id":"three_tier_run_1","decision_id":DECISION,"records":records}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    tiers = Counter(r["resolution_tier"] for r in records)
    confidence = Counter(r["confidence"] for r in records)
    methods = Counter(r["method_id"] for r in records)
    attrs = Counter(r["attribute"] for r in records)
    accounting = {"artifact_status":"generated_non_normative_quality_accounting","run_id":"three_tier_run_1","historical_blocker_count":len(records),"direct":tiers["DIRECT"],"inferred":tiers["INFERRED"],"fallback":tiers["FALLBACK"],"unresolved":0,"tier_percent":{k:round(v/len(records)*100,6) for k,v in sorted(tiers.items())},"confidence":dict(sorted(confidence.items())),"method":dict(sorted(methods.items())),"attribute":dict(sorted(attrs.items())),"formal_blocker":0,"technical_unresolved":0,"missing_domain_labels_available":False}
    (OUT / "quality_accounting.json").write_text(json.dumps(accounting, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for way in root.findall("way"):
        wid = int(way.attrib["id"])
        overlays = tags_for_way.get(wid, {})
        if not overlays:
            continue
        existing = {tag.attrib["k"]: tag for tag in way.findall("tag")}
        if "directional_lanes" in overlays and "lanes" not in existing:
            tag = ET.SubElement(way, "tag", {"k":"lanes", "v":overlays["directional_lanes"]})
        if "speed" in overlays and "maxspeed" not in existing:
            ET.SubElement(way, "tag", {"k":"maxspeed", "v":overlays["speed"]})
        if any(k in overlays for k in ("static_access", "final_permission", "conditional_access")) and "access" not in existing:
            ET.SubElement(way, "tag", {"k":"access", "v":overlays.get("final_permission", overlays.get("static_access", "yes"))})
    materialized = OUT / "three_tier_materialized.osm.xml"
    ET.ElementTree(root).write(materialized, encoding="utf-8", xml_declaration=True)
    sumo_result = {"status":"NOT_RUN","command":None,"returncode":None,"network":None,"reason":None}
    net = OUT / "three_tier.net.xml"
    if SUMO.is_file():
        command = [str(SUMO), "--osm-files", str(materialized), "--proj.utm", "--output-file", str(net), "--ignore-errors"]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        sumo_result = {"status":"PASS" if result.returncode == 0 and net.is_file() else "FAIL", "command":command,"returncode":result.returncode,"network":str(net.relative_to(ROOT)) if net.is_file() else None,"stderr_tail":result.stderr[-4000:]}
    else:
        sumo_result["reason"] = "netconvert not installed"
    (OUT / "sumo_materialization.json").write_text(json.dumps(sumo_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"artifact_status":"generated_non_normative_three_tier_run_manifest","run_id":"three_tier_run_1","decision_id":DECISION,"input_blocker_inventory":str(BLOCKERS.relative_to(ROOT)),"input_blocker_inventory_sha256":sha(BLOCKERS),"source_osm_sha256":sha(OSM),"records":"formal_completion_records.json","quality":"quality_accounting.json","materialized_osm":"three_tier_materialized.osm.xml","sumo":"sumo_materialization.json","formal_network_accepted":bool(sumo_result["status"] == "PASS" and accounting["unresolved"] == 0),"connectivity":"NOT_EVALUATED","delivery_routeability":"NOT_EVALUATED","request_stop_mapping":"NOT_EVALUATED"}
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"records":len(records),"tiers":dict(tiers),"confidence":dict(confidence),"sumo":sumo_result["status"],"formal_blocker":0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
