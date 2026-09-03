from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
MAP = ROOT / "reproducibility/config/research_portal/research_map_v1.yml"
ALLOWED_STATUSES = {"DONE", "CURRENT", "NEXT", "PLANNED", "FUTURE", "UNRESOLVED", "SUPERSEDED", "HISTORICAL"}
REQUIRED_RELATIONS = {"produces", "depends on", "parameterizes", "validates", "feeds into", "compares with", "interprets"}


def main() -> None:
    research_map = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    nodes = research_map["implementation_nodes"]
    ids = {node["id"] for node in nodes}
    by_id = {node["id"]: node for node in nodes}

    assert research_map["current_position"] == {
        "current_milestone": "M1 Network Ready",
        "milestone_status": "DONE",
        "current_stage": "Routing Baseline",
        "current_stage_id": "routing_baseline",
        "immediate_next_task": "Define routing scope for delivery instances",
        "next_research_stage": "Routing Baseline",
    }
    assert len(ids) == len(nodes)
    assert all(node["status"] in ALLOWED_STATUSES for node in nodes)
    assert all(edge["from"] in ids and edge["to"] in ids for edge in research_map["implementation_edges"])
    relations = {edge["relation"] for edge in research_map["implementation_edges"] + research_map["conceptual_edges"]}
    assert REQUIRED_RELATIONS <= relations

    for node_id in ("demand_scenario", "requests_stops", "structural_network", "formal_network", "sumo_network", "stop_mapping", "network_acceptance"):
        assert by_id[node_id]["status"] == "DONE"
    assert by_id["routing_baseline"]["status"] == "NEXT"
    assert by_id["common_instance"]["status"] == "PLANNED"
    for node_id in ("classical_optimization", "qubo", "qaoa", "delivery_simulation", "fulfillment_evaluation", "planning_interpretation", "business_interpretation", "future_society"):
        assert by_id[node_id]["status"] == "FUTURE"

    public_view = research_map["public_view"]
    assert public_view["role"] == "Research communication layer"
    assert [item["status"] for item in public_view["pipeline"]] == [
        "DONE", "DONE", "DONE", "NEXT", "PLANNED", "FUTURE", "FUTURE", "FUTURE",
    ]
    assert all(stage_ref in ids for item in public_view["pipeline"] for stage_ref in item["stage_refs"])

    spec = importlib.util.spec_from_file_location("portal", ROOT / "research_portal/serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = module.summary()
    assert state["public_view"]["role"] == "Research communication layer"
    assert state["public_view"]["interpretation_assessment"] == "SUPPORTED_WITH_CONDITIONS"
    assert state["public_view"]["mapped_delivery_stops"] == 39956
    network = state["accepted_network"]
    assert network["accepted"] is True
    assert network["sha_matches"] is True
    assert network["declared_sha256"] == network["actual_sha256"]
    assert network["mapping"]["mapped"] == network["mapping"]["total_stops"] == 39956
    assert network["mapping"]["mapping_rate"] == 1.0
    assert network["validation"]["routeability_gate"]["routeable"] == 100
    assert network["validation"]["delivery_routeability"] == "PASS"
    acceptance_path = ROOT / state["source_of_truth"]["acceptance"]
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    network_scale = state["network_scale"]
    canonical_counts = acceptance["validation"]["counts"]
    assert network_scale["network_node_count"] == canonical_counts["nodes"] > 0
    assert network_scale["network_edge_count"] == canonical_counts["edges"] > 0
    assert network_scale["network_lane_count"] == canonical_counts["lanes"] > 0
    assert network_scale["edge_semantics"] == "directed"
    assert network_scale["source_artifact"] == state["source_of_truth"]["acceptance"]
    assert network_scale["source_json_pointer"] == "/validation/counts"
    assert network_scale["accepted_run"] == network["accepted_run"]
    assert network_scale["network_artifact"] == network["network_path"]
    assert network_scale["network_sha256"] == network["actual_sha256"]
    assert state["routing_workload"] == {
        "routing_origin_count": None,
        "routing_destination_count": None,
        "required_od_pair_count": None,
        "status": "NOT YET AVAILABLE",
        "reason": "Routing Baseline scope is unresolved and no production routing artifact exists.",
    }
    assert state["instance_scale"]["status"] == "NOT YET AVAILABLE"
    assert all(
        state["instance_scale"][key] is None
        for key in ("request_count", "stop_count", "parcel_equivalent", "vehicle_count", "instance_route_pair_count")
    )
    portal_js = (ROOT / "research_portal/app.js").read_text(encoding="utf-8")
    for ui_term in ("Network Scale", "Nodes |V|", "Directed Edges |E|", "Routing Workload", "Instance Scale"):
        assert ui_term in portal_js
    assert not [item for item in state["artifacts"] if not item["exists"]]
    assert not [item for item in state["traceability"] if not item["available"]]

    evidence = state["interpretation_evidence"]
    assert evidence["overall_assessment"] == "SUPPORTED_WITH_CONDITIONS"
    assert evidence["direct_research_boundary"] == "Delivery Fulfillment"
    evidence_nodes = {item["id"]: item for item in evidence["pathway_nodes"]}
    evidence_links = {item["id"]: item for item in evidence["pathway_links"]}
    assert evidence_nodes["fleet_expansion_replacement"]["label"] == "Potential Need for Fleet Expansion / Replacement"
    assert evidence_links["link_fulfillment_to_unserved"]["evidence_status"] == "DEFINITION_DERIVED"
    assert evidence_links["link_unserved_to_capacity"]["evidence_status"] == "EVIDENCE_SUPPORTED"
    assert evidence_links["link_capacity_to_fleet"]["evidence_status"] == "SUPPORTED_WITH_CONDITIONS"
    assert evidence_links["link_fulfillment_to_actual_investment"]["claim_status"] == "OUT_OF_SCOPE"
    assert [item["label"] for item in evidence["traceability"]] == [
        "Research Question", "Direct Metric", "Interpretation Claim",
        "Evidence Artifact", "External Source", "Portal Node",
    ]
    assert any(item["category"] == "Evidence" and item["exists"] for item in state["artifacts"])

    current_view = json.dumps({
        "position": state["current_position"],
        "nodes": state["maps"]["implementation"]["nodes"],
        "conceptual": state["maps"]["conceptual"],
        "interpretation_evidence": state["interpretation_evidence"],
        "network": state["accepted_network"],
        "validation": state["validation_gates"],
    }, ensure_ascii=False)
    for stale in ("FORMAL_NETWORK_ACCEPTED=false", "83/100", "17 failed OD", "Network Acceptance = pending"):
        assert stale not in current_view
    assert "Hierarchical Hybrid" not in current_view
    assert "strict v17" not in current_view

    portal_html = (ROOT / "research_portal/index.html").read_text(encoding="utf-8")
    public_markup = portal_html[:portal_html.index('<details id="technical-details"')]
    assert "./research " not in public_markup
    assert "SHA256" not in public_markup
    assert "Current Research Stage" in public_markup
    assert "Explore Network / Instances" in public_markup
    assert '<details id="technical-details" class="technical-details">' in portal_html

    print(json.dumps({
        "research_map": "passed", "nodes": len(ids),
        "current_stage": state["current_position"]["current_stage"],
        "formal_network_accepted": network["accepted"],
        "artifact_links": sum(bool(item["url"]) for item in state["artifacts"]),
        "network_scale": {
            "nodes": network_scale["network_node_count"],
            "directed_edges": network_scale["network_edge_count"],
            "lanes": network_scale["network_lane_count"],
        },
        "interpretation_assessment": evidence["overall_assessment"],
        "evidence_sources": evidence["source_counts"]["total"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
