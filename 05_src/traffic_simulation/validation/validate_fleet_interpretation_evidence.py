"""Validate the fleet-capacity interpretation Evidence artifact without running research."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "reproducibility/evidence/fleet_capacity_interpretation_v1.yml"
SCHEMA = ROOT / "reproducibility/evidence/fleet_capacity_interpretation_v1.schema.json"
INDEX = ROOT / "reproducibility/indexes/research_repository_index_v17.yml"

REQUIRED_STATUSES = {
    "DIRECT_ANALYSIS",
    "DEFINITION_DERIVED",
    "EVIDENCE_SUPPORTED",
    "SUPPORTED_WITH_CONDITIONS",
    "NOT_ESTABLISHED",
    "OUT_OF_SCOPE",
    "NEEDS_SOURCE_VERIFICATION",
}


def validate() -> dict:
    artifact = yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))
    repository_index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(artifact)

    nodes = {item["id"]: item for item in artifact["pathway_nodes"]}
    links = {item["id"]: item for item in artifact["pathway_links"]}
    sources = {item["id"]: item for item in artifact["external_sources"]}
    categories = {item["id"] for item in artifact["evidence_categories"]}
    assert len(nodes) == len(artifact["pathway_nodes"])
    assert len(links) == len(artifact["pathway_links"])
    assert len(sources) == len(artifact["external_sources"])
    assert set(artifact["status_vocabulary"]) == REQUIRED_STATUSES

    allowed_external_target = "actual_corporate_investment_decision"
    for link in links.values():
        assert link["from"] in nodes
        assert link["to"] in nodes or link["to"] == allowed_external_target
        assert set(link["source_refs"]) <= sources.keys()
    for node in nodes.values():
        assert set(node["source_refs"]) <= sources.keys()
    for source in sources.values():
        assert source["category"] in categories

    assert nodes["delivery_fulfillment"]["layer"] == "DIRECT_ANALYSIS"
    assert nodes["unserved_delivery_demand"]["layer"] == "EVIDENCE_SUPPORTED_INTERPRETATION"
    assert nodes["effective_delivery_capacity_requirement"]["layer"] == "EVIDENCE_SUPPORTED_INTERPRETATION"
    assert nodes["fleet_expansion_replacement"]["label"] == "Potential Need for Fleet Expansion / Replacement"
    assert links["link_fulfillment_to_unserved"]["evidence_status"] == "DEFINITION_DERIVED"
    assert links["link_unserved_to_capacity"]["evidence_status"] == "EVIDENCE_SUPPORTED"
    assert links["link_capacity_to_fleet"]["evidence_status"] == "SUPPORTED_WITH_CONDITIONS"
    assert links["link_fulfillment_to_actual_investment"]["evidence_status"] == "NOT_ESTABLISHED"
    assert links["link_fulfillment_to_actual_investment"]["claim_status"] == "OUT_OF_SCOPE"
    assert artifact["traceability"]["evidence_artifact"] == str(EVIDENCE.relative_to(ROOT))
    index_entry = repository_index["interpretation_evidence"]
    assert index_entry["artifact"] == str(EVIDENCE.relative_to(ROOT))
    assert index_entry["schema"] == str(SCHEMA.relative_to(ROOT))
    assert index_entry["role"] == "NON_AUTHORITATIVE_EVIDENCE_SUPPORTED_INTERPRETATION"

    return {
        "evidence_artifact": "passed",
        "overall_assessment": artifact["overall_assessment"],
        "pathway_nodes": len(nodes),
        "pathway_links": len(links),
        "external_sources": len(sources),
        "needs_source_verification": sum(
            item["citation_status"] == "NEEDS_SOURCE_VERIFICATION"
            for item in sources.values()
        ),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
