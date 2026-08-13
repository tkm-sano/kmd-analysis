"""Validate completion of one v17 Phase 12 run, independently of the other run."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network.formal_blocker_governance_v17 import (
    validate_exclusion_manifest,
)
from traffic_simulation.network.validate_v17_phase12_output_contract import CONTRACT_PATH
from traffic_simulation.paths import REPOSITORY_ROOT


MAJOR_ARTIFACT_IDS = (
    "structural_full_population",
    "formal_full_population",
    "complete_blocker_inventory",
    "exclusion_manifest",
    "population_accounting",
)
VALIDATOR_IDS = (
    "required_artifacts",
    "schema",
    "semantic_hash",
    "semantic",
    "identity_uniqueness",
    "population_accounting",
    "registered_values",
    "blocker_exclusion",
)
STAGES = (
    "directed_segments",
    "directional_lanes",
    "static_access",
    "conditional_access",
    "final_permission",
    "speed",
)
ACCOUNTED_STATUSES = (
    "resolved",
    "unresolved",
    "conflict",
    "invalid",
    "valid_but_unsupported",
)


class Phase12RunCompletionError(ValueError):
    """A single Phase 12 run failed a completion gate."""

    def __init__(self, gate: str, message: str) -> None:
        super().__init__(f"{gate}: {message}")
        self.gate = gate


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase12RunCompletionError("required_artifacts", f"YAML root is not an object: {path}")
    return value


def _load_json(path: Path, *, gate: str = "required_artifacts") -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Phase12RunCompletionError(gate, f"cannot load JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise Phase12RunCompletionError(gate, f"JSON root is not an object: {path}")
    return value


def _repo_path(relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise Phase12RunCompletionError("required_artifacts", f"unsafe repository path: {relative}")
    resolved = (REPOSITORY_ROOT / Path(*candidate.parts)).resolve()
    if not resolved.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise Phase12RunCompletionError("required_artifacts", f"path escapes repository: {relative}")
    return resolved


def _semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(item) for key, item in value.items() if key != "semantic_sha256"}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _require_unique(values: Iterable[Any], label: str) -> None:
    items = list(values)
    if len(items) != len(set(items)):
        duplicates = [str(item) for item, count in Counter(items).items() if count > 1]
        raise Phase12RunCompletionError(
            "identity_uniqueness", f"duplicate {label}: {duplicates[:5]}"
        )


def _validate_schema(value: Mapping[str, Any], schema_path: Path, artifact_id: str) -> None:
    schema = _load_json(schema_path, gate="schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(value)
    except jsonschema.ValidationError as error:
        raise Phase12RunCompletionError(
            "schema", f"{artifact_id}: {error.message}"
        ) from error


def _walk_assumption_ids(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key == "assumption_ids" and isinstance(child, list):
                yield from (str(item) for item in child)
            else:
                yield from _walk_assumption_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_assumption_ids(child)


def _raw_blocker_record_id(stage: str, blocker: Mapping[str, Any]) -> str:
    record_id = (
        blocker.get("permission_record_id")
        or blocker.get("speed_record_id")
        or f"{stage}:{blocker.get('scope', 'record')}:{blocker.get('source_way_id', blocker.get('relation_id'))}:{blocker['stop_code']}"
    )
    return f"{stage}:{record_id}"


def _status_counter(records: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(item.get("resolution_status")) for item in records)


def _expected_population_statuses(formal: Mapping[str, Any]) -> dict[str, Counter[str]]:
    stages = formal["stage_outputs"]
    lanes = stages["directional_lanes"]
    static = stages["static_access"]
    conditional = stages["conditional_access"]
    return {
        "formal_directional_lane_source_way": _status_counter(
            [*lanes["resolutions"], *lanes["blockers"]]
        ),
        "formal_static_access_source_way": _status_counter(
            [{"resolution_status": "resolved"} for _ in static["normalized_rules"]]
            + list(static["blockers"])
        ),
        "formal_conditional_access_source_way": _status_counter(
            [{"resolution_status": "resolved"} for _ in conditional["conditional_rules"]]
            + list(conditional["blockers"])
        ),
        "formal_permission_lane_tuple": _status_counter(
            stages["final_permission"]["permission_records"]
        ),
        "formal_speed_directed_segment": _status_counter(stages["speed"]["speed_records"]),
    }


def _validate_profile(
    artifact: Mapping[str, Any], expected_profile: str
) -> None:
    if artifact["profile"] != expected_profile:
        raise Phase12RunCompletionError(
            "semantic", f"expected {expected_profile} profile, got {artifact['profile']}"
        )
    stages = artifact["stage_outputs"]
    if set(stages) != set(STAGES):
        raise Phase12RunCompletionError("semantic", f"{expected_profile} stage set differs")
    expected_counts = {
        f"{stage}.{key}": count
        for stage, stage_value in stages.items()
        for key, count in stage_value.get("counts", {}).items()
        if isinstance(count, int) and not isinstance(count, bool)
    }
    if artifact["counts"] != dict(sorted(expected_counts.items())):
        raise Phase12RunCompletionError("semantic", f"{expected_profile} flattened counts differ")
    expected_blockers = sum(len(stages[stage]["blockers"]) for stage in STAGES)
    if len(artifact["blockers"]) != expected_blockers:
        raise Phase12RunCompletionError("semantic", f"{expected_profile} blocker aggregation differs")

    directed = stages["directed_segments"]
    lanes = stages["directional_lanes"]
    final = stages["final_permission"]
    speed = stages["speed"]
    expected_stage_counts = {
        ("directed_segments", "directed_segments"): len(directed["directed_segments"]),
        ("directed_segments", "blockers"): len(directed["blockers"]),
        ("directional_lanes", "resolved_source_ways"): len(lanes["resolutions"]),
        ("directional_lanes", "lane_blockers"): len(lanes["blockers"]),
        ("directional_lanes", "directional_lanes"): sum(
            len(item["lanes"]) for item in lanes["segment_lanes"]
        ),
        ("final_permission", "permission_records"): len(final["permission_records"]),
        ("final_permission", "permission_blockers"): len(final["blockers"]),
        ("speed", "speed_records"): len(speed["speed_records"]),
        ("speed", "speed_blockers"): len(speed["blockers"]),
    }
    for (stage, count_name), expected in expected_stage_counts.items():
        if count_name in stages[stage]["counts"] and stages[stage]["counts"][count_name] != expected:
            raise Phase12RunCompletionError(
                "semantic", f"{expected_profile}.{stage}.{count_name} differs"
            )

    chain = (
        ("directional_lanes", "directed_segment_semantic_sha256", "directed_segments"),
        ("static_access", "directional_lane_semantic_sha256", "directional_lanes"),
        ("conditional_access", "static_access_semantic_sha256", "static_access"),
        ("final_permission", "conditional_access_semantic_sha256", "conditional_access"),
    )
    for downstream, reference_field, upstream in chain:
        if stages[downstream].get(reference_field) != stages[upstream].get("semantic_sha256"):
            raise Phase12RunCompletionError(
                "semantic", f"{expected_profile} stage lineage differs: {upstream} -> {downstream}"
            )


def _validate_identities(artifacts: Mapping[str, Mapping[str, Any]]) -> None:
    for profile_id in ("structural_full_population", "formal_full_population"):
        stages = artifacts[profile_id]["stage_outputs"]
        _require_unique(
            (item["directed_segment_id"] for item in stages["directed_segments"]["directed_segments"]),
            f"{profile_id} directed-segment ID",
        )
        _require_unique(
            (item["directed_segment_id"] for item in stages["directional_lanes"]["segment_lanes"]),
            f"{profile_id} segment-lane ID",
        )
        for segment in stages["directional_lanes"]["segment_lanes"]:
            _require_unique(
                (item["lane_position"] for item in segment["lanes"]),
                f"{profile_id} lane position in {segment['directed_segment_id']}",
            )
        permissions = stages["final_permission"]["permission_records"]
        _require_unique((item["permission_record_id"] for item in permissions), f"{profile_id} permission record ID")
        _require_unique(
            ((item["directed_segment_id"], item["lane_position"], item["vehicle_class"]) for item in permissions),
            f"{profile_id} permission identity",
        )
        speeds = stages["speed"]["speed_records"]
        _require_unique((item["speed_record_id"] for item in speeds), f"{profile_id} speed record ID")
        _require_unique((item["directed_segment_id"] for item in speeds), f"{profile_id} speed segment ID")

    inventory = artifacts["complete_blocker_inventory"]
    _require_unique((item["blocker_id"] for item in inventory["entries"]), "blocker ID")
    _require_unique((item["record_id"] for item in inventory["entries"]), "blocker record ID")
    exclusion = artifacts["exclusion_manifest"]
    _require_unique((item["record_id"] for item in exclusion["entries"]), "exclusion record ID")
    accounting = artifacts["population_accounting"]
    _require_unique((item["population_unit_id"] for item in accounting["population_units"]), "population unit ID")
    _require_unique((item["root_cause_record_id"] for item in accounting["root_cause_records"]), "root-cause ID")
    _require_unique(
        (item["downstream_record_id"] for item in accounting["blocker_relationships"]["causal_edges"]),
        "causal downstream record ID",
    )


def _validate_population(
    artifacts: Mapping[str, Mapping[str, Any]], registry: Mapping[str, Any]
) -> None:
    accounting = artifacts["population_accounting"]
    units = {item["population_unit_id"]: item for item in accounting["population_units"]}
    expected = _expected_population_statuses(artifacts["formal_full_population"])
    if set(units) != set(expected):
        raise Phase12RunCompletionError("population_accounting", "population unit set differs")
    for unit_id, unit in units.items():
        if unit["input"] != unit["governed"] + unit["excluded"]:
            raise Phase12RunCompletionError("population_accounting", f"input equation differs: {unit_id}")
        status_total = sum(unit[name] for name in ACCOUNTED_STATUSES)
        if unit["governed"] != status_total:
            raise Phase12RunCompletionError("population_accounting", f"governed equation differs: {unit_id}")
        actual = expected[unit_id]
        if any(unit[name] != actual[name] for name in ACCOUNTED_STATUSES):
            raise Phase12RunCompletionError("population_accounting", f"status counts differ: {unit_id}")
        if unit["governed"] != sum(actual.values()):
            raise Phase12RunCompletionError("population_accounting", f"governed source count differs: {unit_id}")

    difference = accounting["profile_population_difference"]
    structural_records = artifacts["structural_full_population"]["stage_outputs"]["final_permission"]["permission_records"]
    formal_records = artifacts["formal_full_population"]["stage_outputs"]["final_permission"]["permission_records"]
    if difference["structural_record_count"] != len(structural_records) or difference["formal_record_count"] != len(formal_records):
        raise Phase12RunCompletionError("population_accounting", "profile record counts differ")
    if difference["structural_record_count"] != difference["formal_record_count"] + difference["difference"]:
        raise Phase12RunCompletionError("population_accounting", "profile difference equation differs")
    structural_keys = {
        (item["directed_segment_id"], item["lane_position"], item["vehicle_class"])
        for item in structural_records
    }
    formal_keys = {
        (item["directed_segment_id"], item["lane_position"], item["vehicle_class"])
        for item in formal_records
    }
    structural_segments = {
        item["directed_segment_id"]: item
        for item in artifacts["structural_full_population"]["stage_outputs"]["directional_lanes"]["segment_lanes"]
    }
    actual_assumptions: Counter[str] = Counter()
    for segment_id, _lane_position, _vehicle_class in structural_keys - formal_keys:
        if segment_id not in structural_segments:
            raise Phase12RunCompletionError("population_accounting", f"structural-only segment lacks lane lineage: {segment_id}")
        for assumption_id in structural_segments[segment_id].get("assumption_ids", []):
            actual_assumptions[str(assumption_id)] += 1
    if difference["by_assumption_id"] != dict(sorted(actual_assumptions.items())):
        raise Phase12RunCompletionError("population_accounting", "profile difference assumption counts differ")
    if difference["difference"] != len(structural_keys - formal_keys):
        raise Phase12RunCompletionError("population_accounting", "profile identity difference differs")
    detected_missing = bool(formal_keys - structural_keys)
    detected_duplicates = len(structural_keys) != len(structural_records)
    if (
        difference["missing_formal_record_detected"] != detected_missing
        or difference["duplicate_structural_record_detected"] != detected_duplicates
        or difference["unregistered_assumption_detected"]
        or detected_missing
        or detected_duplicates
    ):
        raise Phase12RunCompletionError("population_accounting", "profile population integrity flag is set")


def _validate_blockers_and_exclusions(
    artifacts: Mapping[str, Mapping[str, Any]], policy: Mapping[str, Any]
) -> None:
    formal = artifacts["formal_full_population"]
    inventory = artifacts["complete_blocker_inventory"]
    exclusion = artifacts["exclusion_manifest"]
    accounting = artifacts["population_accounting"]
    entries = inventory["entries"]
    raw_ids = {
        _raw_blocker_record_id(stage, blocker)
        for stage in STAGES
        for blocker in formal["stage_outputs"][stage]["blockers"]
    }
    inventory_ids = {item["record_id"] for item in entries}
    if raw_ids != inventory_ids or len(raw_ids) != len(entries):
        raise Phase12RunCompletionError("blocker_exclusion", "formal blockers and inventory identities differ")
    if inventory["counts"]["total"] != len(entries):
        raise Phase12RunCompletionError("blocker_exclusion", "blocker total differs")
    if inventory["counts"]["by_strategy"] != dict(sorted(Counter(item["selected_strategy"]["value"] for item in entries).items())):
        raise Phase12RunCompletionError("blocker_exclusion", "blocker strategy counts differ")
    if inventory["counts"]["by_root_cause"] != dict(sorted(Counter(item["root_cause_category"] for item in entries).items())):
        raise Phase12RunCompletionError("blocker_exclusion", "blocker root-cause counts differ")

    relationships = accounting["blocker_relationships"]
    permission = [item for item in entries if item["attribute_name"] == "final_permission"]
    upstream = [item for item in entries if item["attribute_name"] != "final_permission"]
    if relationships["permission_blocker_count"] != len(permission) or relationships["upstream_record_count"] != len(upstream) or relationships["deduplicated_blocker_count"] != len(entries):
        raise Phase12RunCompletionError("blocker_exclusion", "blocker relationship counts differ")
    roots = {item["root_cause_record_id"]: item for item in accounting["root_cause_records"]}
    expected_edges = set()
    root_effects: Counter[str] = Counter()
    for item in permission:
        if len(item["root_cause_record_ids"]) != 1 or item["root_cause_record_ids"][0] not in roots:
            raise Phase12RunCompletionError("blocker_exclusion", f"permission blocker lacks a valid root cause: {item['record_id']}")
        root_id = item["root_cause_record_ids"][0]
        expected_edges.add((root_id, item["record_id"]))
        root_effects[root_id] += 1
    actual_edges = {(item["root_cause_record_id"], item["downstream_record_id"]) for item in relationships["causal_edges"]}
    if actual_edges != expected_edges or len(actual_edges) != len(relationships["causal_edges"]):
        raise Phase12RunCompletionError("blocker_exclusion", "permission causal edges differ")
    if any(root["affected_permission_record_count"] != root_effects[root_id] for root_id, root in roots.items()):
        raise Phase12RunCompletionError("blocker_exclusion", "root-cause affected counts differ")
    suppressed_ids = [item["root_cause_record_id"] for item in relationships["suppressed_candidates"]]
    if set(suppressed_ids) != {item["record_id"] for item in upstream} or len(suppressed_ids) != len(upstream):
        raise Phase12RunCompletionError("blocker_exclusion", "suppressed-candidate coverage differs")

    formal_permission_ids = [
        item["permission_record_id"]
        for item in formal["stage_outputs"]["final_permission"]["permission_records"]
    ]
    try:
        validate_exclusion_manifest(exclusion, governed_record_ids=formal_permission_ids, policy=policy)
    except ValueError as error:
        raise Phase12RunCompletionError("blocker_exclusion", str(error)) from error
    excluded_ids = {item["record_id"] for item in exclusion["entries"]}
    strategy_ids = {item["record_id"] for item in entries if item["selected_strategy"]["value"] == "formal_exclusion"}
    if excluded_ids != strategy_ids:
        raise Phase12RunCompletionError("blocker_exclusion", "formal exclusions and blocker strategies differ")
    if exclusion["population_counts"]["governed"] != len(formal_permission_ids):
        raise Phase12RunCompletionError("blocker_exclusion", "exclusion governed count differs")
    audit = accounting["exclusion_audit"]
    if not exclusion["entries"]:
        if any((audit["excluded_way_count"], audit["excluded_way_ratio"], audit["excluded_length_m"], audit["excluded_length_ratio"])) or audit["by_highway_class"] or audit["by_original_stop_code"]:
            raise Phase12RunCompletionError("blocker_exclusion", "empty exclusions have non-empty audit impact")
        impact = accounting["exclusion_network_impact"]
        if impact["removed_edge_count"] != 0 or impact["removed_total_length_m"] != 0 or impact["critical_connector_removed"] or impact["result"] != "passed":
            raise Phase12RunCompletionError("blocker_exclusion", "empty exclusions have network removal impact")


def _validate_registered_values(
    artifacts: Mapping[str, Mapping[str, Any]], registry: Mapping[str, Any], policy: Mapping[str, Any]
) -> None:
    registered_assumptions = {
        item["assumption_id"]: set(item["allowed_profiles"])
        for item in registry["assumptions"]
    }
    for artifact_id, profile in (
        ("structural_full_population", "structural"),
        ("formal_full_population", "formal"),
    ):
        assumptions = list(_walk_assumption_ids(artifacts[artifact_id]["stage_outputs"]))
        invalid = sorted({
            item
            for item in assumptions
            if item not in registered_assumptions or profile not in registered_assumptions[item]
        })
        if invalid:
            raise Phase12RunCompletionError(
                "registered_values", f"unregistered or profile-ineligible assumption IDs: {invalid}"
            )
    difference_ids = set(
        artifacts["population_accounting"]["profile_population_difference"]["by_assumption_id"]
    )
    if not difference_ids.issubset(registered_assumptions):
        raise Phase12RunCompletionError("registered_values", "unregistered profile-difference assumption ID")

    formal = artifacts["formal_full_population"]
    registered_statuses = {item["value"] for item in registry["state_origin"]["resolution_status"]}
    stop_status = {item["stop_code"]: item["resolution_status"] for item in registry["stop_codes"]}
    status_records = [
        *(item for stage in STAGES for item in formal["stage_outputs"][stage]["blockers"]),
        *formal["stage_outputs"]["directional_lanes"]["resolutions"],
        *formal["stage_outputs"]["final_permission"]["permission_records"],
        *formal["stage_outputs"]["speed"]["speed_records"],
    ]
    for record in status_records:
        status = record["resolution_status"]
        stop_code = record.get("stop_code")
        valid_pair = status in registered_statuses and (
            (status == "resolved" and stop_code is None) or stop_status.get(stop_code) == status
        )
        if not valid_pair:
            raise Phase12RunCompletionError(
                "registered_values", f"unregistered status/stop-code pair: {status}/{stop_code}"
            )
    registered_exclusions = {
        item["exclusion_rule_id"] for item in policy["registered_exclusion_rules"]
    }
    used_exclusions = {
        item["exclusion_rule_id"] for item in artifacts["exclusion_manifest"]["entries"]
    }
    if not used_exclusions.issubset(registered_exclusions):
        raise Phase12RunCompletionError("registered_values", "unregistered exclusion rule ID")


def _validate_semantics(
    artifacts: Mapping[str, Mapping[str, Any]]
) -> int:
    structural = artifacts["structural_full_population"]
    formal = artifacts["formal_full_population"]
    for field in ("configuration_id", "population_version", "scenario_context_id", "source_sha256"):
        if structural[field] != formal[field]:
            raise Phase12RunCompletionError("semantic", f"profiles differ on {field}")
    _validate_profile(structural, "structural")
    _validate_profile(formal, "formal")
    return 2


def _validate_semantic_hashes(artifacts: Mapping[str, Mapping[str, Any]]) -> int:
    for artifact_id, value in artifacts.items():
        if value.get("semantic_sha256") != _semantic_hash(value):
            raise Phase12RunCompletionError("semantic_hash", f"{artifact_id} hash differs")
    return len(artifacts)


def _gate_result(
    run_id: str, validator_id: str, *, required_checks: int, completed_checks: int
) -> dict[str, Any]:
    failed_checks = required_checks - completed_checks
    result = "passed" if required_checks > 0 and failed_checks == 0 else "failed"
    return {
        "run_id": run_id,
        "validator_id": validator_id,
        "checks": {
            "required": required_checks,
            "completed": completed_checks,
            "failed": failed_checks,
        },
        "result": result,
    }


def validate_major_artifacts(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    registry: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, str]:
    """Apply all cross-artifact semantic gates to the five major artifacts."""
    if set(artifacts) != set(MAJOR_ARTIFACT_IDS):
        raise Phase12RunCompletionError("required_artifacts", "major artifact set differs")
    semantic_hash_count = _validate_semantic_hashes(artifacts)
    semantic_profile_count = _validate_semantics(artifacts)
    _validate_identities(artifacts)
    _validate_population(artifacts, registry)
    _validate_registered_values(artifacts, registry, policy)
    _validate_blockers_and_exclusions(artifacts, policy)
    completed = {
        "schema": len(artifacts) == len(MAJOR_ARTIFACT_IDS),
        "semantic": (
            semantic_hash_count == len(MAJOR_ARTIFACT_IDS)
            and semantic_profile_count == 2
        ),
        "population_accounting": True,
        "identity_uniqueness": True,
    }
    return {
        validator_id: "passed" if succeeded else "failed"
        for validator_id, succeeded in completed.items()
    }


def validate_run_completion(
    run_id: str, *, contract_path: Path = CONTRACT_PATH, output_root: Path | None = None
) -> dict[str, Any]:
    """Validate the five major outputs for exactly one run."""
    gate_results = [
        validate_run_gate(
            run_id,
            validator_id,
            contract_path=contract_path,
            output_root=output_root,
        )
        for validator_id in VALIDATOR_IDS
    ]
    return aggregate_gate_results(run_id, gate_results)


def aggregate_gate_results(
    run_id: str, gate_results: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Derive per-field and whole-run status only from returned validator results."""
    by_id = {str(item["validator_id"]): item for item in gate_results}
    exact_set = len(by_id) == len(gate_results) and set(by_id) == set(VALIDATOR_IDS)

    def combined_result(validator_ids: Sequence[str]) -> str:
        succeeded = all(
            validator_id in by_id
            and by_id[validator_id].get("result") == "passed"
            and by_id[validator_id].get("checks", {}).get("failed") == 0
            and by_id[validator_id].get("checks", {}).get("completed")
            == by_id[validator_id].get("checks", {}).get("required")
            for validator_id in validator_ids
        )
        return "passed" if succeeded else "failed"

    gates = {
        validator_id: (
            str(by_id[validator_id].get("result", "failed"))
            if validator_id in by_id else "failed"
        )
        for validator_id in VALIDATOR_IDS
    }
    validation_results = {
        "schema": combined_result(("schema",)),
        "semantic": combined_result(
            ("semantic_hash", "semantic", "registered_values", "blocker_exclusion")
        ),
        "population_accounting": combined_result(("population_accounting",)),
        "identity_uniqueness": combined_result(("identity_uniqueness",)),
    }
    result = combined_result(VALIDATOR_IDS) if exact_set else "failed"
    return {
        "phase12_run_completion": result,
        "run_id": run_id,
        "major_artifact_count": len(MAJOR_ARTIFACT_IDS),
        "gates": gates,
        "validation_results": validation_results,
        "result": result,
    }


def validate_run_gate(
    run_id: str,
    validator_id: str,
    *,
    contract_path: Path = CONTRACT_PATH,
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Execute exactly one independently callable run-completion validator."""
    if validator_id not in VALIDATOR_IDS:
        raise Phase12RunCompletionError("required_artifacts", f"unknown validator ID: {validator_id}")
    contract = _load_yaml(contract_path)
    if run_id not in contract["execution"]["required_run_ids"]:
        raise Phase12RunCompletionError("required_artifacts", f"unknown run ID: {run_id}")
    root = output_root or _repo_path(contract["execution"]["output_root"])
    catalog = {item["artifact_id"]: item for item in contract["artifact_catalog"]}
    paths = {
        artifact_id: root / catalog[artifact_id]["path_template"].format(run_id=run_id)
        for artifact_id in MAJOR_ARTIFACT_IDS
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise Phase12RunCompletionError("required_artifacts", f"missing major artifacts: {missing}")
    if validator_id == "required_artifacts":
        return _gate_result(
            run_id,
            validator_id,
            required_checks=len(paths),
            completed_checks=sum(path.is_file() for path in paths.values()),
        )

    artifacts = {artifact_id: _load_json(path) for artifact_id, path in paths.items()}
    required_checks = 1
    completed_checks = 0
    if validator_id == "schema":
        required_checks = len(artifacts)
        for artifact_id, value in artifacts.items():
            _validate_schema(value, _repo_path(catalog[artifact_id]["schema"]), artifact_id)
            completed_checks += 1
    elif validator_id == "semantic_hash":
        required_checks = len(artifacts)
        completed_checks = _validate_semantic_hashes(artifacts)
    elif validator_id == "semantic":
        required_checks = 2
        completed_checks = _validate_semantics(artifacts)
    elif validator_id == "identity_uniqueness":
        _validate_identities(artifacts)
        completed_checks = 1
    elif validator_id == "population_accounting":
        registry = _load_yaml(_repo_path(contract["fixed_inputs"]["registry_bundle"]))
        _validate_population(artifacts, registry)
        completed_checks = 1
    elif validator_id == "registered_values":
        registry = _load_yaml(_repo_path(contract["fixed_inputs"]["registry_bundle"]))
        policy = _load_yaml(_repo_path(contract["fixed_inputs"]["blocker_policy"]))
        _validate_registered_values(artifacts, registry, policy)
        completed_checks = 1
    elif validator_id == "blocker_exclusion":
        policy = _load_yaml(_repo_path(contract["fixed_inputs"]["blocker_policy"]))
        _validate_blockers_and_exclusions(artifacts, policy)
        completed_checks = 1
    return _gate_result(
        run_id,
        validator_id,
        required_checks=required_checks,
        completed_checks=completed_checks,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, choices=("run_1", "run_2"))
    parser.add_argument("--validator", choices=VALIDATOR_IDS)
    args = parser.parse_args(argv)
    try:
        result = (
            validate_run_gate(args.run_id, args.validator)
            if args.validator
            else validate_run_completion(args.run_id)
        )
    except (Phase12RunCompletionError, jsonschema.SchemaError, KeyError, TypeError) as error:
        print(json.dumps({
            "run_id": args.run_id,
            "validator_id": args.validator or "all",
            "result": "failed",
            "error": str(error),
        }, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
