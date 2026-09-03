"""Validate the current pipeline reference without executing research pipelines."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "RESEARCH_PIPELINE_REFERENCE.md"
INDEX = ROOT / "reproducibility/indexes/research_repository_index_v17.yml"
MAP = ROOT / "reproducibility/config/research_portal/research_map_v1.yml"
AUTHORITY = ROOT / "reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml"
CATALOG = ROOT / "05_src/research_cli/catalog.py"

PIPELINES = (
    "A. External / Open Data",
    "B. Demand",
    "C. Requests / Stops",
    "D. Network Construction",
    "E. Stop Mapping",
    "F. Network Acceptance",
    "G. Routing Baseline",
    "H. Common Delivery Instance",
    "I. Classical Optimization",
    "J. QUBO",
    "K. QAOA",
    "L. Scenario Construction",
    "M. Delivery Simulation",
    "N. Evaluation",
    "O. Evidence-Supported Interpretation",
    "P. Sensitivity / Robustness",
    "Q. Publication / Reproducibility Freeze",
)
TEMPLATE_HEADINGS = (
    "Purpose",
    "Current status",
    "Entry conditions",
    "Canonical inputs",
    "Commands",
    "Implementation",
    "Outputs",
    "Authority / Source of truth",
    "Validation",
    "Acceptance / DONE criteria",
    "Provenance",
    "Known limitations",
    "Unresolved decisions",
    "Next handoff",
)
LINK_PATTERN = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def validate() -> dict:
    text = REFERENCE.read_text(encoding="utf-8")
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    research_map = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    authority = yaml.safe_load(AUTHORITY.read_text(encoding="utf-8"))
    accepted = authority["accepted_run"]
    acceptance = json.loads((ROOT / accepted["acceptance_artifact"]).read_text(encoding="utf-8"))

    required_top = (
        "## Update policy",
        "## Current Research Position — 今何をすべきか",
        "## Pipeline Map",
        "## Research Command Index",
        "## Artifact / Authority Matrix",
        "## Validation Matrix",
        "## Dependency Matrix",
        "## Current lifecycle boundary",
        "## Role separation",
    )
    for heading in required_top:
        assert heading in text, f"missing required heading: {heading}"

    section_offsets = []
    for pipeline in PIPELINES:
        marker = f"## {pipeline}"
        offset = text.find(marker)
        assert offset >= 0, f"missing pipeline section: {pipeline}"
        section_offsets.append((pipeline, offset))
    assert section_offsets == sorted(section_offsets, key=lambda item: item[1])
    for index_position, (pipeline, start) in enumerate(section_offsets):
        end = section_offsets[index_position + 1][1] if index_position + 1 < len(section_offsets) else text.find("## Research Command Index", start)
        section = text[start:end]
        for heading in TEMPLATE_HEADINGS:
            assert f"### {heading}" in section, f"{pipeline}: missing template heading: {heading}"

    broken_links = []
    checked_links = 0
    for raw_target in LINK_PATTERN.findall(text):
        target = raw_target.strip().strip("<>").split(maxsplit=1)[0].strip("'\"")
        if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        checked_links += 1
        if not (REFERENCE.parent / target).resolve().exists():
            broken_links.append(raw_target)
    assert not broken_links, f"broken local links: {broken_links}"

    catalog_text = CATALOG.read_text(encoding="utf-8")
    commands = re.findall(r'CommandInfo\("[^"]+", "([^"]+)"', catalog_text)
    assert len(commands) == 41 and len(commands) == len(set(commands))
    missing_commands = [command for command in commands if f"./research {command}" not in text]
    assert not missing_commands, f"catalog commands absent from reference: {missing_commands}"

    assert index["pipeline_reference"] == str(REFERENCE.relative_to(ROOT))
    important = next(item for item in index["important_markdown"] if item["path"] == index["pipeline_reference"])
    assert important["document_id"] == "DOC-RESEARCH-PIPELINE-REFERENCE"
    assert important["role"] == "CURRENT_REFERENCE"
    assert important["lifecycle"] == "CURRENT"
    assert research_map["current_position"]["current_stage"] == "Routing Baseline"
    assert research_map["current_position"]["immediate_next_task"] == "Define routing scope for delivery instances"
    assert "Current research stage | `Routing Baseline — NEXT`" in text
    assert "Immediate next task | Define routing scope for delivery instances." in text
    assert accepted["network_file"] in text
    assert accepted["network_sha256"] in text
    assert "Network graph size（`|V|` nodes / `|E|` directed edges / lanes）" in text
    assert "`required_od_pair_count`は`NOT YET AVAILABLE`" in text
    assert sha256(ROOT / accepted["network_file"]) == accepted["network_sha256"]
    assert acceptance["FORMAL_NETWORK_ACCEPTED"] is True
    assert "`HISTORICAL`: strict v17" in text
    assert "`SUPERSEDED`: Hierarchical Hybrid" in text

    return {
        "pipeline_reference": "passed",
        "pipeline_sections": len(PIPELINES),
        "commands": len(commands),
        "checked_local_links": checked_links,
        "broken_local_links": len(broken_links),
        "current_stage": research_map["current_position"]["current_stage"],
        "accepted_network_sha256": accepted["network_sha256"],
        "formal_network_accepted": acceptance["FORMAL_NETWORK_ACCEPTED"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
