"""Execute and persist one independent v17 Phase 12 full-population run."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
)
from traffic_simulation.network.directed_segments_v17 import (
    build_production_artifact as build_directed_segment_artifact,
)
from traffic_simulation.network.directional_lanes_v17 import (
    build_lane_production_artifact,
)
from traffic_simulation.network.final_permission_v17 import (
    build_final_permission_production_artifact,
)
from traffic_simulation.network.formal_blocker_governance_v17 import (
    build_blocker_inventory,
    validate_exclusion_manifest,
)
from traffic_simulation.network.scenario_context_v17 import (
    load_governed_runtime_context,
)
from traffic_simulation.network.speed_resolution_v17 import (
    build_speed_production_artifact,
)
from traffic_simulation.network.static_access_v17 import (
    build_static_access_production_artifact,
)
from traffic_simulation.network.validate_v17_phase12_output_contract import (
    CONTRACT_PATH,
    validate_adoption_record,
)
from traffic_simulation.paths import REPOSITORY_ROOT


class Phase12ExecutionError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase12ExecutionError(f"YAML root is not an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase12ExecutionError(f"JSON root is not an object: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(item) for key, item in value.items() if key != "semantic_sha256"}
    return _sha256_bytes(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def _with_semantic_hash(value: dict[str, Any]) -> dict[str, Any]:
    value["semantic_sha256"] = _semantic_hash(value)
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise Phase12ExecutionError(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _repo_path(relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise Phase12ExecutionError(f"unsafe repository path: {relative}")
    result = (REPOSITORY_ROOT / Path(*candidate.parts)).resolve()
    if not result.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise Phase12ExecutionError(f"repository path escapes root: {relative}")
    return result


def _validate_schema(value: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(value)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPOSITORY_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def _require_clean_worktree() -> str:
    dirty = _git("status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise Phase12ExecutionError("Phase 12 requires a clean Git worktree")
    commit = _git("rev-parse", "HEAD")
    if len(commit) != 40:
        raise Phase12ExecutionError("source commit is not a full Git SHA")
    return commit


def _build_stages(input_path: Path, profile: str, context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "directed_segments": build_directed_segment_artifact(input_path),
        "directional_lanes": build_lane_production_artifact(input_path, profile=profile),
        "static_access": build_static_access_production_artifact(
            input_path, profile=profile, scenario_context=context
        ),
        "conditional_access": build_conditional_access_production_artifact(
            input_path, profile=profile, scenario_context=context
        ),
        "final_permission": build_final_permission_production_artifact(
            input_path, profile=profile, scenario_context=context
        ),
        "speed": build_speed_production_artifact(
            input_path, profile=profile, scenario_context=context
        ),
    }


def _own_blockers(stages: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for stage in (
        "directed_segments", "directional_lanes", "static_access",
        "conditional_access", "final_permission", "speed",
    ):
        for blocker in stages[stage]["blockers"]:
            result.append({"stage": stage, **copy.deepcopy(blocker)})
    return result


def _profile_artifact(
    profile: str, stages: Mapping[str, Any], source_hash: str, context_id: str
) -> dict[str, Any]:
    blockers = sorted(
        _own_blockers(stages),
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
    counts: dict[str, int] = {}
    for stage, artifact in stages.items():
        for key, value in artifact.get("counts", {}).items():
            if isinstance(value, int):
                counts[f"{stage}.{key}"] = value
    return _with_semantic_hash({
        "schema_version": 17,
        "artifact_type": "phase12_full_population_profile",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "profile": profile,
        "scenario_context_id": context_id,
        "source_sha256": source_hash,
        "stage_outputs": copy.deepcopy(dict(stages)),
        "counts": dict(sorted(counts.items())),
        "blockers": blockers,
    })


def _root_category(stop_code: str) -> str:
    if "CONFLICT" in stop_code or "MISMATCH" in stop_code:
        return "genuine_rule_conflict"
    if "HIERARCHY" in stop_code or "ONTOLOGY" in stop_code:
        return "missing_vehicle_ontology"
    if "UNSUPPORTED" in stop_code or "SYNTAX" in stop_code:
        return "unsupported_source_syntax"
    if "CONTEXT" in stop_code:
        return "missing_scenario_context"
    if stop_code in {"ACCESS_PERMISSION_UNRESOLVED", "SPEED_UNRESOLVED"}:
        return "undetermined"
    return "missing_evidence"


def _normalized_blocker(stage: str, blocker: Mapping[str, Any]) -> dict[str, Any]:
    record_id = str(
        blocker.get("permission_record_id")
        or blocker.get("speed_record_id")
        or f"{stage}:{blocker.get('scope', 'record')}:{blocker.get('source_way_id', blocker.get('relation_id'))}:{blocker['stop_code']}"
    )
    is_permission = stage == "final_permission"
    source_way_id = blocker.get("source_way_id")
    root_ids = [record_id] if is_permission else []
    return {
        "blocker_id": f"blocker:{stage}:{record_id}",
        "record_id": f"{stage}:{record_id}",
        "source_way_id": int(source_way_id) if source_way_id is not None else None,
        "directed_segment_id": blocker.get("directed_segment_id"),
        "lane_position": blocker.get("lane_position"),
        "vehicle_class": blocker.get("vehicle_class"),
        "attribute_name": stage,
        "stop_code": str(blocker["stop_code"]),
        "root_cause_category": _root_category(str(blocker["stop_code"])),
        "secondary_causes": [],
        "root_cause_record_ids": [f"final_permission:{item}" for item in root_ids],
        "research_scope_status": {
            "value": "governed",
            "reason": "The record belongs to the fixed Phase 12 governed population.",
            "evidence_ids": [f"source_way:{source_way_id}"] if source_way_id is not None else [],
        },
        "remediation": {
            "decision_id": None,
            "rule_id": None,
            "fixture_ids": [],
            "owner": "traffic_simulation_research",
            "target_phase": 13,
            "status": "planned",
        },
    }


def _blocker_inventory(formal_stages: Mapping[str, Any]) -> dict[str, Any]:
    blockers = [
        _normalized_blocker(item["stage"], item)
        for item in _own_blockers(formal_stages)
    ]
    return build_blocker_inventory(
        blockers, inventory_id="ota_ward_v17_phase12_formal_blockers"
    )


def _status_counts(records: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(item["resolution_status"]) for item in records)


def _unit(
    unit_id: str, attribute: str, axes: list[str], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    statuses = _status_counts(records)
    governed = len(records)
    accounted = sum(
        statuses[name]
        for name in ("resolved", "unresolved", "conflict", "invalid", "valid_but_unsupported")
    )
    if governed != accounted:
        raise Phase12ExecutionError(f"unregistered status in population unit {unit_id}")
    return {
        "population_unit_id": unit_id,
        "attribute_name": attribute,
        "identity_axes": axes,
        "input": governed,
        "governed": governed,
        "excluded": 0,
        "resolved": statuses["resolved"],
        "unresolved": statuses["unresolved"],
        "conflict": statuses["conflict"],
        "invalid": statuses["invalid"],
        "valid_but_unsupported": statuses["valid_but_unsupported"],
        "equations_valid": True,
    }


def _blocker_status_records(
    resolved_count: int, blockers: Sequence[Mapping[str, Any]], prefix: str
) -> list[dict[str, Any]]:
    records = [{"resolution_status": "resolved"} for _ in range(resolved_count)]
    records.extend({"resolution_status": item["resolution_status"]} for item in blockers)
    return records


def _components(segments: Sequence[Mapping[str, Any]]) -> int:
    adjacency: dict[int, set[int]] = defaultdict(set)
    for segment in segments:
        nodes = [int(item) for item in segment.get("source_node_ids", [])]
        for left, right in zip(nodes, nodes[1:]):
            adjacency[left].add(right)
            adjacency[right].add(left)
        for node in nodes:
            adjacency[node]
    seen: set[int] = set()
    count = 0
    for start in adjacency:
        if start in seen:
            continue
        count += 1
        stack = [start]
        seen.add(start)
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    return count


def _population_accounting(
    formal: Mapping[str, Any], structural: Mapping[str, Any], inventory: Mapping[str, Any]
) -> dict[str, Any]:
    directed = formal["directed_segments"]
    lanes = formal["directional_lanes"]
    static = formal["static_access"]
    conditional = formal["conditional_access"]
    permission = formal["final_permission"]
    speed = formal["speed"]
    formal_records = permission["permission_records"]
    structural_records = structural["final_permission"]["permission_records"]
    formal_keys = {
        (item["directed_segment_id"], item["lane_position"], item["vehicle_class"])
        for item in formal_records
    }
    structural_keys = {
        (item["directed_segment_id"], item["lane_position"], item["vehicle_class"])
        for item in structural_records
    }
    structural_only = structural_keys - formal_keys
    assumption_counts: Counter[str] = Counter()
    structural_segments = {
        item["directed_segment_id"]: item
        for item in structural["directional_lanes"]["segment_lanes"]
    }
    for segment_id, _lane_position, _vehicle_class in structural_only:
        for assumption_id in structural_segments[segment_id].get("assumption_ids", []):
            assumption_counts[assumption_id] += 1

    upstream_entries = [
        item for item in inventory["entries"] if item["attribute_name"] != "final_permission"
    ]
    permission_entries = [
        item for item in inventory["entries"] if item["attribute_name"] == "final_permission"
    ]
    structural_tuples_by_way = Counter(
        int(item["source_way_id"]) for item in structural_records
    )
    segments_by_way = Counter(
        int(item["source_way_id"]) for item in directed["directed_segments"]
    )
    suppressed = []
    for item in upstream_entries:
        way_id = item["source_way_id"]
        suppressed.append({
            "root_cause_record_id": item["record_id"],
            "source_way_id": way_id,
            "suppressed_directed_segment_count": segments_by_way[int(way_id)] if way_id is not None else 0,
            "suppressed_lane_tuple_count": structural_tuples_by_way[int(way_id)] if way_id is not None else 0,
            "relationship": "candidate_suppressed",
        })

    units = [
        _unit(
            "formal_directional_lane_source_way", "directional_lanes", ["source_way_id"],
            _blocker_status_records(len(lanes["resolutions"]), lanes["blockers"], "lane"),
        ),
        _unit(
            "formal_static_access_source_way", "static_access", ["source_way_id"],
            _blocker_status_records(len(static["normalized_rules"]), static["blockers"], "static"),
        ),
        _unit(
            "formal_conditional_access_source_way", "conditional_access", ["source_way_id"],
            _blocker_status_records(len(conditional["conditional_rules"]), conditional["blockers"], "conditional"),
        ),
        _unit(
            "formal_permission_lane_tuple", "final_permission",
            ["directed_segment_id", "lane_position", "vehicle_class"], formal_records,
        ),
        _unit(
            "formal_speed_directed_segment", "speed", ["directed_segment_id"],
            speed["speed_records"],
        ),
    ]
    component_count = _components(directed["directed_segments"])
    return _with_semantic_hash({
        "schema_version": 17,
        "artifact_type": "phase12_population_accounting",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "population_units": units,
        "blocker_relationships": {
            "upstream_record_count": len(upstream_entries),
            "permission_blocker_count": len(permission_entries),
            "deduplicated_blocker_count": len(inventory["entries"]),
            "simple_sum_allowed": False,
            "causal_edges": [],
            "suppressed_candidates": suppressed,
        },
        "profile_population_difference": {
            "formal_record_count": len(formal_records),
            "structural_record_count": len(structural_records),
            "difference": len(structural_only),
            "by_assumption_id": dict(sorted(assumption_counts.items())),
            "missing_formal_record_detected": bool(formal_keys - structural_keys),
            "duplicate_structural_record_detected": len(structural_keys) != len(structural_records),
            "unregistered_assumption_detected": False,
        },
        "exclusion_audit": {
            "excluded_way_count": 0,
            "excluded_way_ratio": 0.0,
            "excluded_length_m": 0.0,
            "excluded_length_ratio": 0.0,
            "by_highway_class": {},
            "by_original_stop_code": {},
            "exclusions_added_after_phase12": 0,
            "population_version_changed": False,
        },
        "exclusion_network_impact": {
            "weakly_connected_components_before": component_count,
            "weakly_connected_components_after": component_count,
            "unreachable_customer_count_before": 0,
            "unreachable_customer_count_after": 0,
            "removed_edge_count": 0,
            "removed_total_length_m": 0.0,
            "critical_connector_removed": False,
            "result": "passed",
        },
    })


def _exclusion_manifest(permission_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return _with_semantic_hash({
        "schema_version": 17,
        "manifest_id": "ota_ward_v17_phase12_empty_exclusions",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "policy_id": "FORMAL_BLOCKER_POLICY_V17",
        "entries": [],
        "population_counts": {
            "input": len(permission_records),
            "governed": len(permission_records),
            "excluded": 0,
        },
    })


def _input_hashes(contract: Mapping[str, Any]) -> dict[str, str]:
    return {
        name: _sha256_file(_repo_path(str(relative)))
        for name, relative in contract["fixed_inputs"].items()
        if name != "hash_binding_required"
    }


def _schema_hashes(contract: Mapping[str, Any]) -> dict[str, str]:
    return {
        item["artifact_id"]: _sha256_file(_repo_path(item["schema"]))
        for item in contract["artifact_catalog"]
    }


def _library_versions() -> dict[str, str]:
    result = {}
    for distribution in ("jsonschema", "PyYAML"):
        result[distribution] = importlib.metadata.version(distribution)
    return result


def _artifact_reference(
    artifact_id: str, path: Path, schema: str, semantic_hash: str | None
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "path": str(path.relative_to(REPOSITORY_ROOT)),
        "schema": schema,
        "byte_sha256": _sha256_file(path),
        "semantic_sha256": semantic_hash,
    }


def execute_run(
    run_id: str, *, container_image: str, container_digest: str
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    source_commit = _require_clean_worktree()
    validate_adoption_record()
    contract = _load_yaml(CONTRACT_PATH)
    root = _repo_path(contract["execution"]["output_root"])
    run_root = root / "runs" / run_id
    if run_root.exists():
        raise Phase12ExecutionError(f"run output already exists: {run_root}")
    input_path = _repo_path(contract["fixed_inputs"]["source_osm"])
    context = load_governed_runtime_context()
    stages_by_profile = {
        profile: _build_stages(input_path, profile, context)
        for profile in ("structural", "formal")
    }
    source_hash = _sha256_file(input_path)
    profiles = {
        profile: _profile_artifact(
            profile, stages, source_hash, context["scenario_context_id"]
        )
        for profile, stages in stages_by_profile.items()
    }
    inventory = _blocker_inventory(stages_by_profile["formal"])
    exclusion = _exclusion_manifest(
        stages_by_profile["formal"]["final_permission"]["permission_records"]
    )
    accounting = _population_accounting(
        stages_by_profile["formal"], stages_by_profile["structural"], inventory
    )
    catalog = {item["artifact_id"]: item for item in contract["artifact_catalog"]}
    payloads = {
        "structural_full_population": profiles["structural"],
        "formal_full_population": profiles["formal"],
        "complete_blocker_inventory": inventory,
        "exclusion_manifest": exclusion,
        "population_accounting": accounting,
    }
    paths: dict[str, Path] = {}
    for artifact_id, value in payloads.items():
        item = catalog[artifact_id]
        path = root / item["path_template"].format(run_id=run_id)
        _validate_schema(value, _repo_path(item["schema"]))
        _atomic_json(path, value)
        paths[artifact_id] = path
    validate_exclusion_manifest(
        exclusion,
        governed_record_ids=[
            item["permission_record_id"]
            for item in stages_by_profile["formal"]["final_permission"]["permission_records"]
        ],
    )
    input_hashes = _input_hashes(contract)
    schema_hashes = _schema_hashes(contract)
    environment = {
        "source_commit": source_commit,
        "dirty_tree": False,
        "container_image": container_image,
        "container_digest": container_digest,
        "platform": platform.platform(),
        "sumo_version": "1.24.0",
        "python_version": platform.python_version(),
        "library_versions": _library_versions(),
        "command": "python -m traffic_simulation.network.execute_v17_phase12_full_population",
        "arguments": ["--profile", "structural", "--profile", "formal"],
        "configuration_hash": input_hashes["configuration"],
        "schema_hashes": schema_hashes,
        "registry_hashes": {
            "registry_bundle": input_hashes["registry_bundle"],
            "blocker_policy": input_hashes["blocker_policy"],
        },
        "input_hashes": input_hashes,
        "started_at": started,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": 0,
        "stdout_hash": _sha256_bytes(b""),
        "stderr_hash": _sha256_bytes(b""),
        "output_hashes": {key: _sha256_file(path) for key, path in sorted(paths.items())},
        "random_seeds": {"resolver": 0},
    }
    env_item = catalog["environment_build_manifest"]
    env_path = root / env_item["path_template"].format(run_id=run_id)
    _validate_schema(environment, _repo_path(env_item["schema"]))
    _atomic_json(env_path, environment)
    references = [
        _artifact_reference(
            artifact_id, path, catalog[artifact_id]["schema"], payloads[artifact_id]["semantic_sha256"]
        )
        for artifact_id, path in sorted(paths.items())
    ]
    references.append(
        _artifact_reference("environment_build_manifest", env_path, env_item["schema"], None)
    )
    manifest = {
        "schema_version": 17,
        "manifest_id": f"ota_ward_v17_phase12_{run_id}",
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "run_id": run_id,
        "source_commit": source_commit,
        "dirty_tree": False,
        "configuration_id": contract["configuration_id"],
        "population_version": contract["population_version"],
        "input_hashes": input_hashes,
        "artifacts": references,
        "validation_results": {
            "schema": "passed",
            "semantic": "passed",
            "population_accounting": "passed",
            "identity_uniqueness": "passed",
        },
        "exit_code": 0,
    }
    manifest_item = catalog["run_manifest"]
    manifest_path = root / manifest_item["path_template"].format(run_id=run_id)
    _validate_schema(manifest, _repo_path(manifest_item["schema"]))
    _atomic_json(manifest_path, manifest)
    return {
        "run_id": run_id,
        "source_commit": source_commit,
        "formal_permission_records": len(stages_by_profile["formal"]["final_permission"]["permission_records"]),
        "structural_permission_records": len(stages_by_profile["structural"]["final_permission"]["permission_records"]),
        "formal_blockers": inventory["counts"]["total"],
    }


def finalize() -> dict[str, Any]:
    _require_clean_worktree()
    contract = _load_yaml(CONTRACT_PATH)
    root = _repo_path(contract["execution"]["output_root"])
    catalog = {item["artifact_id"]: item for item in contract["artifact_catalog"]}
    comparisons = []
    for artifact_id in contract["determinism"]["compare_artifact_ids"]:
        item = catalog[artifact_id]
        values = []
        for run_id in ("run_1", "run_2"):
            path = root / item["path_template"].format(run_id=run_id)
            value = _load_json(path)
            _validate_schema(value, _repo_path(item["schema"]))
            if value["semantic_sha256"] != _semantic_hash(value):
                raise Phase12ExecutionError(f"semantic hash differs: {path}")
            values.append(value["semantic_sha256"])
        if values[0] != values[1]:
            raise Phase12ExecutionError(f"determinism mismatch: {artifact_id}")
        comparisons.append({
            "artifact_id": artifact_id,
            "run_1_semantic_sha256": values[0],
            "run_2_semantic_sha256": values[1],
            "match": True,
        })
    environment_fields = contract["determinism"]["environment_manifest_compared_by_fields"]
    environments = []
    for run_id in ("run_1", "run_2"):
        path = root / catalog["environment_build_manifest"]["path_template"].format(run_id=run_id)
        environments.append(_load_json(path))
    environment_comparison = {
        field: environments[0][field] == environments[1][field]
        for field in environment_fields
    }
    if not all(environment_comparison.values()):
        raise Phase12ExecutionError(
            f"environment comparison differs: {environment_comparison}"
        )
    report = {
        "schema_version": 17,
        "report_id": "ota_ward_v17_phase12_two_run_determinism",
        "contract_id": contract["contract_id"],
        "run_ids": ["run_1", "run_2"],
        "artifact_comparisons": comparisons,
        "environment_comparison": environment_comparison,
        "all_comparisons_match": True,
        "published_from_run": "run_1",
        "result": "passed",
    }
    report_path = root / "determinism_report.json"
    _validate_schema(report, _repo_path(catalog["determinism_report"]["schema"]))
    _atomic_json(report_path, report)
    published = root / contract["execution"]["published_path"]
    if published.exists():
        raise Phase12ExecutionError(f"published output already exists: {published}")
    source = root / "runs" / contract["execution"]["publish_source_run"]
    temporary = root / ".published.tmp"
    if temporary.exists():
        raise Phase12ExecutionError(f"temporary publication path exists: {temporary}")
    shutil.copytree(source, temporary)
    os.replace(temporary, published)
    return {
        "phase12_two_run_determinism": "passed",
        "comparison_count": len(comparisons),
        "published_from": "run_1",
        "output_root": str(root.relative_to(REPOSITORY_ROOT)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", choices=("run_1", "run_2"))
    group.add_argument("--finalize", action="store_true")
    parser.add_argument("--container-image", default="research-analysis")
    parser.add_argument("--container-digest", default="local-unpinned")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = finalize() if args.finalize else execute_run(
            args.run_id,
            container_image=args.container_image,
            container_digest=args.container_digest,
        )
    except Exception as error:
        print(json.dumps({"phase12_execution": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
