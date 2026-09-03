from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "research_portal"
INDEX = ROOT / "reproducibility/indexes/research_repository_index_v17.yml"
MAP = ROOT / "reproducibility/config/research_portal/research_map_v1.yml"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(path: str, label: str, category: str, lifecycle: str = "CURRENT", role: str = "") -> dict:
    absolute = ROOT / path
    return {
        "path": path, "label": label, "category": category, "lifecycle": lifecycle,
        "role": role, "exists": absolute.exists(), "url": "/artifact/" + path if absolute.exists() else None,
    }


def trace_entry(label: str, path: str | None) -> dict:
    if not path:
        return {"label": label, "available": False, "status": "NOT AVAILABLE"}
    item = artifact(path, label, "Traceability")
    return {"label": label, "available": item["exists"], "status": "CURRENT" if item["exists"] else "MISSING", **item}


def stage_detail(node: dict, map_config: dict, authority: dict, acceptance: dict) -> dict:
    accepted = authority["accepted_run"]
    configured = map_config.get("stage_details", {}).get(node["id"], {})
    detail = {
        "purpose": node.get("purpose"), "status": node["status"],
        "primary_input": node.get("input"), "primary_output": node.get("output"),
        "decision": configured.get("decision"), "specification": configured.get("specification"),
        "registry_schema": configured.get("registry_schema", []),
        "implementation": configured.get("implementation"), "validator": configured.get("validator"),
        "canonical_artifact": configured.get("canonical_artifact"),
        "result": configured.get("result", "Not yet produced" if node["status"] in {"NEXT", "PLANNED", "FUTURE"} else "See canonical artifact"),
        "known_limitations": configured.get("known_limitations", []),
        "blocking_dependency": configured.get("blocking_dependency", []),
        "next_action": configured.get("next_action", "No action recorded"),
        "commands": configured.get("commands", []),
    }
    if node["id"] in map_config["network_stage_ids"]:
        detail.update({
            "decision": authority["decision"]["path"], "specification": authority["specification"]["path"],
            "registry_schema": [authority["registry"]["path"], authority["schema"]["policy_path"], authority["schema"]["record_path"]],
            "implementation": map_config["network_trace"]["implementation"],
            "validator": accepted["acceptance_artifact"], "canonical_artifact": accepted["network_file"],
            "result": "FORMAL_NETWORK_ACCEPTED = true" if acceptance["FORMAL_NETWORK_ACCEPTED"] else "FORMAL_NETWORK_ACCEPTED = false",
            "known_limitations": acceptance["known_limitations"],
        })
    return detail


def summary() -> dict:
    repository_index = load_yaml(INDEX)
    map_config = load_yaml(MAP)
    authority_path = ROOT / repository_index["current_authority"]
    authority = load_yaml(authority_path)
    accepted = authority["accepted_run"]
    acceptance = load_json(ROOT / accepted["acceptance_artifact"])
    provenance = load_json(ROOT / accepted["provenance_accounting"])
    network_path = ROOT / accepted["network_file"]

    nodes = []
    for configured in map_config["implementation_nodes"]:
        node = dict(configured)
        node["detail"] = stage_detail(node, map_config, authority, acceptance)
        nodes.append(node)
    conceptual = [dict(node, detail=stage_detail(node, map_config, authority, acceptance)) for node in map_config["conceptual_nodes"]]

    validation = acceptance["validation"]
    validation_rows = [
        {"stage": "Network", "gate": "SUMO build", "status": validation["sumo_build"]},
        {"stage": "Network", "gate": "Lane validity", "status": validation["lane_validity"]},
        {"stage": "Network", "gate": "Speed validity", "status": validation["speed_validity"]},
        {"stage": "Network", "gate": "Permission validity", "status": validation["permission_validity"]},
        {"stage": "Network", "gate": "Connectivity", "status": validation["connectivity"]},
        {"stage": "Network", "gate": "Stop mapping", "status": acceptance["mapping"]["status"]},
        {"stage": "Network", "gate": "Routeability (sample)", "status": validation["delivery_routeability"]},
        {"stage": "Network", "gate": "Acceptance", "status": "PASS" if acceptance["FORMAL_NETWORK_ACCEPTED"] else "FAIL"},
        *map_config["future_validation_gates"],
    ]

    artifacts = [
        artifact(repository_index["stable_research_overview"], "Research Overview", "Overview"),
        artifact(repository_index["research_overview"], "Canonical Research Roadmap", "Overview"),
        artifact(repository_index["human_repository_map"], "Repository Map", "Overview"),
        artifact(repository_index["current_authority"], "Current Authority Pointer", "Configs"),
        artifact(authority["decision"]["path"], authority["decision"]["id"], "Decisions"),
        artifact(authority["specification"]["path"], "Three-tier Formal Completion", "Specifications"),
        artifact(authority["pipeline_specification"]["path"], "Network Completion Pipeline", "Specifications"),
        artifact(authority["registry"]["path"], "Three-tier Registry", "Registries"),
        artifact(authority["schema"]["policy_path"], "Policy Schema", "Schemas"),
        artifact(authority["schema"]["record_path"], "Record Schema", "Schemas"),
        artifact(accepted["path"], accepted["run_id"], "Runs"),
        artifact(accepted["network_file"], "Accepted SUMO Network", "Acceptance"),
        artifact(accepted["acceptance_artifact"], "Network Acceptance", "Acceptance"),
        artifact(accepted["path"] + "/request_stop_mapping.json", "Accepted Stop Mapping", "Validation"),
        artifact(accepted["provenance_accounting"], "Three-tier Quality Accounting", "Validation", "GENERATED", "diagnostic"),
        artifact("reproducibility/config/research_portal/research_map_v1.yml", "Research Map Config", "Portal"),
        artifact("research_portal/README.md", "Portal Handoff", "Portal"),
        artifact(authority["superseded_decision"]["lifecycle_path"], "Decision Lifecycle", "Historical", "SUPERSEDED"),
    ]
    for item in map_config["historical_artifacts"]:
        artifacts.append(artifact(**item))

    network_sha = digest(network_path) if network_path.is_file() else None
    total_tiers = sum(acceptance["three_tier_population"][key] for key in ("DIRECT", "INFERRED", "FALLBACK"))
    tier_rows = []
    for key in ("DIRECT", "INFERRED", "FALLBACK"):
        count = acceptance["three_tier_population"][key]
        tier_rows.append({"tier": key, "count": count, "percent": (100 * count / total_tiers if total_tiers else 0)})

    trace_paths = {
        "Research Question": repository_index["research_overview"],
        "Decision": authority["decision"]["path"], "Specification": authority["specification"]["path"],
        "Registry / Schema": authority["registry"]["path"],
        "Implementation": map_config["network_trace"]["implementation"],
        "Validation": accepted["acceptance_artifact"], "Run": accepted["path"],
        "Artifact": accepted["network_file"], "Acceptance": accepted["acceptance_artifact"],
    }
    return {
        "portal_philosophy": map_config["portal_philosophy"],
        "research_question": map_config["research_question"], "interpretation_mode": map_config["interpretation_mode"],
        "current_position": map_config["current_position"],
        "maps": {
            "conceptual": {"nodes": conceptual, "edges": map_config["conceptual_edges"]},
            "implementation": {"nodes": nodes, "edges": map_config["implementation_edges"], "groups": map_config["stage_groups"]},
            "data_flow": map_config["data_flow"],
        },
        "accepted_network": {
            "decision_id": acceptance["decision_id"], "accepted_run": accepted["run_id"],
            "network_id": accepted["network_id"], "network_path": accepted["network_file"],
            "network_url": "/artifact/" + accepted["network_file"],
            "declared_sha256": accepted["network_sha256"], "actual_sha256": network_sha,
            "sha_matches": network_sha == accepted["network_sha256"], "sumo_version": acceptance["sumo_version"],
            "validation": validation, "mapping": acceptance["mapping"],
            "accepted": acceptance["FORMAL_NETWORK_ACCEPTED"], "known_limitations": acceptance["known_limitations"],
        },
        "provenance": {"tiers": tier_rows, "confidence": provenance.get("confidence", {})},
        "validation_gates": validation_rows, "unresolved_decisions": map_config["unresolved_decisions"],
        "traceability": [trace_entry(label, path) for label, path in trace_paths.items()],
        "artifacts": artifacts, "timeline": map_config["timeline"], "historical": map_config["historical"],
        "superseded": {**authority["superseded_decision"], "status": "SUPERSEDED"},
        "commands": map_config["research_commands"],
        "source_of_truth": {
            "repository_index": str(INDEX.relative_to(ROOT)), "authority": str(authority_path.relative_to(ROOT)),
            "acceptance": accepted["acceptance_artifact"], "map_config": str(MAP.relative_to(ROOT)),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self._serve(send_body=False)

    def do_GET(self) -> None:
        self._serve(send_body=True)

    def _serve(self, *, send_body: bool) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self.send_json(summary(), send_body=send_body)
            return
        if parsed.path.startswith("/artifact/"):
            relative = unquote(parsed.path.removeprefix("/artifact/"))
            self.send_file(ROOT / relative, root=ROOT, send_body=send_body)
            return
        relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        self.send_file(PORTAL / relative, root=PORTAL, send_body=send_body)

    def send_file(self, path: Path, *, root: Path, send_body: bool) -> None:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root.resolve())
        except (FileNotFoundError, ValueError):
            self.send_error(404)
            return
        if resolved.is_dir():
            entries = {"path": str(resolved.relative_to(ROOT)), "files": sorted(item.name for item in resolved.iterdir())}
            data = json.dumps(entries, ensure_ascii=False).encode("utf-8") if send_body else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data) if send_body else len(json.dumps(entries, ensure_ascii=False).encode("utf-8"))))
            self.end_headers()
            if send_body:
                self.wfile.write(data)
            return
        if not resolved.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        data = resolved.read_bytes() if send_body else b""
        self.send_response(200)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
        self.send_header("Content-Length", str(resolved.stat().st_size))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def send_json(self, value: dict, *, send_body: bool) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(os.getenv("PORT", "8876"))), Handler).serve_forever()
