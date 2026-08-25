"""Execute and persist one independent v17 Phase 12 full-population run."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
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
from traffic_simulation.network.validate_v17_phase12_run_completion import (
    MAJOR_ARTIFACT_IDS,
    VALIDATOR_IDS,
    aggregate_gate_results,
)
from traffic_simulation.paths import REPOSITORY_ROOT


class Phase12ExecutionError(ValueError):
    pass


CONTAINER_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def _validate_container_identity(
    container_image: str | None, container_digest: str | None
) -> tuple[str, str]:
    image = container_image.strip() if container_image is not None else ""
    digest = container_digest.strip() if container_digest is not None else ""
    if not image:
        raise Phase12ExecutionError("formal Phase 12 run requires a container image name")
    if not CONTAINER_DIGEST_PATTERN.fullmatch(digest):
        raise Phase12ExecutionError(
            "formal Phase 12 run requires --container-digest sha256:<64 lowercase hex>; "
            "unpinned or malformed digests are prohibited"
        )
    return image, digest


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


def _normalized_blocker(
    stage: str,
    blocker: Mapping[str, Any],
    *,
    permission_record: Mapping[str, Any] | None = None,
    root_cause_record_id: str | None = None,
) -> dict[str, Any]:
    record_id = str(
        blocker.get("permission_record_id")
        or blocker.get("speed_record_id")
        or f"{stage}:{blocker.get('scope', 'record')}:{blocker.get('source_way_id', blocker.get('relation_id'))}:{blocker['stop_code']}"
    )
    is_permission = stage == "final_permission"
    if is_permission and (permission_record is None or root_cause_record_id is None):
        raise Phase12ExecutionError("permission blocker lacks a causal record")
    source_way_id = blocker.get("source_way_id")
    root_ids = [root_cause_record_id] if is_permission else []
    return {
        "blocker_id": f"blocker:{stage}:{record_id}",
        "record_id": f"{stage}:{record_id}",
        "source_way_id": int(source_way_id) if source_way_id is not None else None,
        "directed_segment_id": (
            permission_record["directed_segment_id"]
            if permission_record is not None else blocker.get("directed_segment_id")
        ),
        "lane_position": (
            permission_record["lane_position"]
            if permission_record is not None else blocker.get("lane_position")
        ),
        "vehicle_class": (
            permission_record["vehicle_class"]
            if permission_record is not None else blocker.get("vehicle_class")
        ),
        "attribute_name": stage,
        "stop_code": str(blocker["stop_code"]),
        "root_cause_category": (
            "missing_registered_rule"
            if is_permission else _root_category(str(blocker["stop_code"]))
        ),
        "secondary_causes": [],
        "root_cause_record_ids": root_ids,
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


def _permission_causal_records(
    formal_stages: Mapping[str, Any]
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    permission = formal_stages["final_permission"]
    unresolved = [
        item
        for item in permission["permission_records"]
        if item["resolution_status"] != "resolved"
    ]
    grouped: dict[tuple[int, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for item in unresolved:
        grouped[
            (
                int(item["source_way_id"]),
                str(item["vehicle_class"]),
                str(item["scenario_context_id"]),
            )
        ].append(item)

    static_by_way = {
        int(item["source_way_id"]): item
        for item in formal_stages["static_access"]["normalized_rules"]
    }
    conditional_by_way = {
        int(item["source_way_id"]): item
        for item in formal_stages["conditional_access"]["conditional_rules"]
    }
    permission_to_root: dict[str, str] = {}
    root_records: list[dict[str, Any]] = []
    for (way_id, vehicle_class, context_id), records in sorted(grouped.items()):
        identity = {
            "cause_kind": "no_applicable_access_rule",
            "source_way_id": way_id,
            "vehicle_class": vehicle_class,
            "scenario_context_id": context_id,
        }
        digest = _sha256_bytes(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        )
        root_id = f"root-cause:access-rule-coverage:{digest}"
        static_item = static_by_way.get(way_id, {})
        conditional_item = conditional_by_way.get(way_id, {})
        static_rules = list(static_item.get("rules", []))
        conditional_rules = list(conditional_item.get("rules", []))
        access_keys = {
            str(rule.get("source_key"))
            for rule in static_rules + conditional_rules
            if rule.get("source_key")
        }
        access_keys.update(str(key) for key in static_item.get("deferred_conditional_tags", {}))
        candidate_rule_ids = sorted(
            {
                str(rule["rule_id"])
                for rule in static_rules + conditional_rules
                if "rule_id" in rule
            }
        )
        root_records.append({
            "root_cause_record_id": root_id,
            "source_way_id": way_id,
            "vehicle_class": vehicle_class,
            "scenario_context_id": context_id,
            "root_cause_category": "missing_registered_rule",
            "cause_kind": "no_applicable_access_rule",
            "access_tag_keys": sorted(access_keys),
            "candidate_rule_ids": candidate_rule_ids,
            "affected_permission_record_count": len(records),
            "resolution_status": "unresolved",
            "stop_code": "ACCESS_PERMISSION_UNRESOLVED",
        })
        for item in records:
            permission_to_root[str(item["permission_record_id"])] = root_id
    return permission_to_root, root_records


def _blocker_inventory(
    formal_stages: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    permission_by_id = {
        str(item["permission_record_id"]): item
        for item in formal_stages["final_permission"]["permission_records"]
    }
    permission_to_root, root_records = _permission_causal_records(formal_stages)
    blockers = []
    for item in _own_blockers(formal_stages):
        permission_id = item.get("permission_record_id")
        blockers.append(
            _normalized_blocker(
                item["stage"],
                item,
                permission_record=(
                    permission_by_id[str(permission_id)]
                    if permission_id is not None else None
                ),
                root_cause_record_id=(
                    permission_to_root[str(permission_id)]
                    if permission_id is not None else None
                ),
            )
        )
    inventory = build_blocker_inventory(
        blockers, inventory_id="ota_ward_v17_phase12_formal_blockers"
    )
    return inventory, root_records


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
    formal: Mapping[str, Any],
    structural: Mapping[str, Any],
    inventory: Mapping[str, Any],
    root_cause_records: Sequence[Mapping[str, Any]],
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
    root_ids = {item["root_cause_record_id"] for item in root_cause_records}
    causal_edges = []
    for item in permission_entries:
        if len(item["root_cause_record_ids"]) != 1:
            raise Phase12ExecutionError(
                f"permission blocker does not have exactly one causal link: {item['record_id']}"
            )
        root_id = item["root_cause_record_ids"][0]
        if root_id not in root_ids:
            raise Phase12ExecutionError(
                f"permission blocker references an absent root cause: {root_id}"
            )
        causal_edges.append({
            "root_cause_record_id": root_id,
            "downstream_record_id": item["record_id"],
            "relationship": "causes_permission_blocker",
        })
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

    shared_materialization_stop = "LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED"
    lane_source_blockers = [
        item for item in lanes["blockers"]
        if item["stop_code"] != shared_materialization_stop
    ]
    lane_materialization_blockers = [
        item for item in lanes["blockers"]
        if item["stop_code"] == shared_materialization_stop
    ]
    materialized_lane_way_count = len(
        {int(item["source_way_id"]) for item in lanes["segment_lanes"]}
    )
    units = [
        _unit(
            "formal_directional_lane_source_way", "directional_lanes", ["source_way_id"],
            _blocker_status_records(len(lanes["resolutions"]), lane_source_blockers, "lane_source"),
        ),
        _unit(
            "formal_lane_canonical_representation", "lane_canonical_representation", ["source_way_id"],
            _blocker_status_records(len(lanes["resolutions"]), lane_source_blockers, "lane_canonical"),
        ),
        _unit(
            "formal_lane_simulation_materialization", "lane_simulation_materialization", ["source_way_id"],
            _blocker_status_records(materialized_lane_way_count, lane_materialization_blockers, "lane_materialization"),
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
        "root_cause_records": list(root_cause_records),
        "blocker_relationships": {
            "upstream_record_count": len(upstream_entries),
            "permission_blocker_count": len(permission_entries),
            "deduplicated_blocker_count": len(inventory["entries"]),
            "simple_sum_allowed": False,
            "causal_edges": causal_edges,
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


def _run_completion_validators(run_id: str) -> dict[str, Any]:
    """Run each validator as a real CLI process and retain its exact evidence."""
    executions = []
    gate_results = []
    child_environment = os.environ.copy()
    source_root = str(REPOSITORY_ROOT / "05_src")
    inherited_pythonpath = child_environment.get("PYTHONPATH")
    child_environment["PYTHONPATH"] = (
        source_root
        if not inherited_pythonpath
        else source_root + os.pathsep + inherited_pythonpath
    )
    for validator_id in VALIDATOR_IDS:
        command = [
            sys.executable,
            "-m",
            "traffic_simulation.network.validate_v17_phase12_run_completion",
            "--run-id",
            run_id,
            "--validator",
            validator_id,
        ]
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=child_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        log = json.dumps(
            {"stdout": completed.stdout, "stderr": completed.stderr},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        try:
            reported = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            if completed.returncode == 0:
                raise Phase12ExecutionError(
                    f"run completion validator emitted invalid JSON: {validator_id}"
                ) from error
            reported = {
                "run_id": run_id,
                "validator_id": validator_id,
                "checks": {"required": 1, "completed": 0, "failed": 1},
                "result": "failed",
            }
        reported_result = str(reported.get("result", "failed"))
        reported_checks = reported.get("checks", {})
        evidence = {
            "validator_id": validator_id,
            "command": command,
            "exit_code": completed.returncode,
            "log": log,
            "log_sha256": _sha256_bytes(log.encode("utf-8")),
            "checks": reported_checks,
            "result": reported_result,
        }
        executions.append(evidence)
        if completed.returncode != 0:
            raise Phase12ExecutionError(
                f"run completion validator failed: {validator_id}; log={log.rstrip()}"
            )
        valid_report = (
            reported.get("run_id") == run_id
            and reported.get("validator_id") == validator_id
            and reported_result == "passed"
            and isinstance(reported_checks, dict)
            and reported_checks.get("failed") == 0
            and reported_checks.get("completed") == reported_checks.get("required")
        )
        if not valid_report:
            raise Phase12ExecutionError(
                f"run completion validator result differs: {validator_id}: {reported}"
            )
        gate_results.append(reported)
    aggregate = aggregate_gate_results(run_id, gate_results)
    if aggregate["result"] != "passed":
        raise Phase12ExecutionError(f"run completion failed: {aggregate}")
    return {
        "validator_executions": executions,
        "validation_results": aggregate["validation_results"],
        "result": aggregate["result"],
    }


def execute_run(
    run_id: str,
    *,
    container_image: str | None,
    container_digest: str | None,
    arguments: Sequence[str],
) -> dict[str, Any]:
    container_image, container_digest = _validate_container_identity(
        container_image, container_digest
    )
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
    inventory, root_cause_records = _blocker_inventory(stages_by_profile["formal"])
    exclusion = _exclusion_manifest(
        stages_by_profile["formal"]["final_permission"]["permission_records"]
    )
    accounting = _population_accounting(
        stages_by_profile["formal"],
        stages_by_profile["structural"],
        inventory,
        root_cause_records,
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
        "sumo_version": "not_invoked_phase12",
        "python_version": platform.python_version(),
        "library_versions": _library_versions(),
        "command": "python -m traffic_simulation.network.execute_v17_phase12_full_population",
        "arguments": list(arguments),
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
    completion = _run_completion_validators(run_id)
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
        "validation_results": completion["validation_results"],
        "validator_executions": completion["validator_executions"],
        "result": completion["result"],
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
        "permission_causal_links": len(
            accounting["blocker_relationships"]["causal_edges"]
        ),
        "permission_root_cause_records": len(root_cause_records),
    }


def _validate_completed_run_manifest(
    run_id: str,
    *,
    root: Path,
    contract: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Revalidate a completed run and all manifest evidence before publication."""
    manifest_item = catalog["run_manifest"]
    manifest_path = root / manifest_item["path_template"].format(run_id=run_id)
    manifest = _load_json(manifest_path)
    _validate_schema(manifest, _repo_path(manifest_item["schema"]))
    if manifest["run_id"] != run_id:
        raise Phase12ExecutionError(f"run manifest ID differs: {manifest_path}")

    executions = manifest["validator_executions"]
    execution_ids = [item["validator_id"] for item in executions]
    if len(execution_ids) != len(set(execution_ids)) or set(execution_ids) != set(VALIDATOR_IDS):
        raise Phase12ExecutionError(f"validator execution set differs: {run_id}")
    gate_results = []
    for execution in executions:
        validator_id = execution["validator_id"]
        expected_command_tail = [
            "-m",
            "traffic_simulation.network.validate_v17_phase12_run_completion",
            "--run-id",
            run_id,
            "--validator",
            validator_id,
        ]
        if execution["command"][1:] != expected_command_tail:
            raise Phase12ExecutionError(f"validator command differs: {run_id}/{validator_id}")
        if execution["log_sha256"] != _sha256_bytes(execution["log"].encode("utf-8")):
            raise Phase12ExecutionError(f"validator log hash differs: {run_id}/{validator_id}")
        checks = execution["checks"]
        valid = (
            execution["exit_code"] == 0
            and execution["result"] == "passed"
            and checks["failed"] == 0
            and checks["completed"] == checks["required"]
        )
        if not valid:
            raise Phase12ExecutionError(f"validator did not pass: {run_id}/{validator_id}")
        gate_results.append({
            "run_id": run_id,
            "validator_id": validator_id,
            "checks": checks,
            "result": execution["result"],
        })
    aggregate = aggregate_gate_results(run_id, gate_results)
    if (
        aggregate["result"] != "passed"
        or manifest["result"] != aggregate["result"]
        or manifest["validation_results"] != aggregate["validation_results"]
    ):
        raise Phase12ExecutionError(f"run manifest aggregate differs: {run_id}")

    expected_artifact_ids = set(MAJOR_ARTIFACT_IDS) | {"environment_build_manifest"}
    references = manifest["artifacts"]
    reference_ids = [item["artifact_id"] for item in references]
    if len(reference_ids) != len(set(reference_ids)) or set(reference_ids) != expected_artifact_ids:
        raise Phase12ExecutionError(f"run manifest artifact set differs: {run_id}")
    for reference in references:
        artifact_id = reference["artifact_id"]
        item = catalog[artifact_id]
        expected_path = root / item["path_template"].format(run_id=run_id)
        if reference["path"] != str(expected_path.relative_to(REPOSITORY_ROOT)):
            raise Phase12ExecutionError(f"artifact reference path differs: {run_id}/{artifact_id}")
        if reference["schema"] != item["schema"] or reference["byte_sha256"] != _sha256_file(expected_path):
            raise Phase12ExecutionError(f"artifact reference hash/schema differs: {run_id}/{artifact_id}")
        value = _load_json(expected_path)
        _validate_schema(value, _repo_path(item["schema"]))
        if artifact_id in MAJOR_ARTIFACT_IDS:
            if value["semantic_sha256"] != _semantic_hash(value):
                raise Phase12ExecutionError(f"artifact semantic hash differs: {run_id}/{artifact_id}")
            if reference["semantic_sha256"] != value["semantic_sha256"]:
                raise Phase12ExecutionError(f"artifact reference semantic hash differs: {run_id}/{artifact_id}")
        elif reference["semantic_sha256"] is not None:
            raise Phase12ExecutionError(f"environment semantic hash must be null: {run_id}")
    return manifest


def _normalize_environment_value(
    field: str,
    value: Any,
    *,
    run_id: str,
    normalization: Mapping[str, Any],
) -> Any:
    rule = normalization.get(field)
    if rule is None:
        return copy.deepcopy(value)
    if rule != {
        "method": "replace_cli_option_value",
        "option": "--run-id",
        "replacement": "<run_id>",
        "require_value_equals_run_id": True,
    }:
        raise Phase12ExecutionError(f"unsupported environment normalization: {field}")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise Phase12ExecutionError(f"environment field is not a string argument vector: {field}")
    option = rule["option"]
    positions = [index for index, item in enumerate(value) if item == option]
    if len(positions) != 1 or positions[0] + 1 >= len(value):
        raise Phase12ExecutionError(f"run-specific option occurrence differs: {run_id}/{option}")
    position = positions[0]
    if value[position + 1] != run_id:
        raise Phase12ExecutionError(f"run-specific option value differs: {run_id}/{option}")
    normalized = list(value)
    normalized[position + 1] = rule["replacement"]
    return normalized


def finalize() -> dict[str, Any]:
    _require_clean_worktree()
    contract = _load_yaml(CONTRACT_PATH)
    root = _repo_path(contract["execution"]["output_root"])
    catalog = {item["artifact_id"]: item for item in contract["artifact_catalog"]}
    report_path = root / catalog["determinism_report"]["path_template"]
    published = root / contract["execution"]["published_path"]
    temporary = root / ".published.tmp"
    for path, label in (
        (report_path, "determinism report"),
        (published, "published output"),
        (temporary, "temporary publication path"),
    ):
        if path.exists():
            raise Phase12ExecutionError(f"{label} already exists: {path}")
    for run_id in contract["execution"]["required_run_ids"]:
        _validate_completed_run_manifest(
            run_id, root=root, contract=contract, catalog=catalog
        )
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
    normalization = contract["determinism"].get("environment_field_normalization", {})
    normalized_environments = [
        {
            field: _normalize_environment_value(
                field,
                environment[field],
                run_id=run_id,
                normalization=normalization,
            )
            for field in environment_fields
        }
        for run_id, environment in zip(("run_1", "run_2"), environments, strict=True)
    ]
    environment_comparison = {
        field: normalized_environments[0][field] == normalized_environments[1][field]
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
        "environment_argument_comparison": {
            "run_1_recorded": environments[0]["arguments"],
            "run_2_recorded": environments[1]["arguments"],
            "normalization": normalization["arguments"],
            "run_1_normalized": normalized_environments[0]["arguments"],
            "run_2_normalized": normalized_environments[1]["arguments"],
            "match": environment_comparison["arguments"],
        },
        "all_comparisons_match": True,
        "published_from_run": "run_1",
        "result": "passed",
    }
    _validate_schema(report, _repo_path(catalog["determinism_report"]["schema"]))
    _atomic_json(report_path, report)
    source = root / "runs" / contract["execution"]["publish_source_run"]
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
    parser.add_argument(
        "--container-digest",
        help="required for a formal run; sha256:<64 lowercase hexadecimal characters>",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    actual_arguments = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(actual_arguments)
    try:
        result = finalize() if args.finalize else execute_run(
            args.run_id,
            container_image=args.container_image,
            container_digest=args.container_digest,
            arguments=actual_arguments,
        )
    except Exception as error:
        print(json.dumps({"phase12_execution": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
