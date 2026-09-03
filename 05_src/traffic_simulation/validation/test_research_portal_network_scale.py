"""Ensure Portal network scale stays bound to the current accepted network."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml"


def file_sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def portal_state() -> dict:
    spec = importlib.util.spec_from_file_location("research_portal_serve", ROOT / "research_portal/serve.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.summary()


def test_network_scale_matches_current_acceptance_and_network_sha() -> None:
    authority = yaml.safe_load(AUTHORITY.read_text(encoding="utf-8"))
    accepted = authority["accepted_run"]
    acceptance = json.loads((ROOT / accepted["acceptance_artifact"]).read_text(encoding="utf-8"))
    state = portal_state()
    scale = state["network_scale"]
    counts = acceptance["validation"]["counts"]

    assert scale["network_node_count"] == counts["nodes"] > 0
    assert scale["network_edge_count"] == counts["edges"] > 0
    assert scale["network_lane_count"] == counts["lanes"] > 0
    assert scale["edge_semantics"] == "directed"
    assert scale["source_artifact"] == accepted["acceptance_artifact"]
    assert scale["accepted_run"] == accepted["run_id"]
    assert scale["network_sha256"] == accepted["network_sha256"]
    assert file_sha256(ROOT / accepted["network_file"]) == scale["network_sha256"]
    assert acceptance["FORMAL_NETWORK_ACCEPTED"] is True


def test_unimplemented_workload_and_instance_counts_remain_unavailable() -> None:
    state = portal_state()

    assert state["routing_workload"]["status"] == "NOT YET AVAILABLE"
    assert state["routing_workload"]["required_od_pair_count"] is None
    assert state["instance_scale"]["status"] == "NOT YET AVAILABLE"
    assert state["instance_scale"]["instance_route_pair_count"] is None
