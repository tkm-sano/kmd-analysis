"""Fail-closed governance for v17 formal blockers and exclusions."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


POLICY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml"
)
POLICY_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/formal_blocker_policy_v17.schema.json"
)
INVENTORY_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/formal_blocker_inventory_v17.schema.json"
)
EXCLUSION_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/exclusion_manifest_v17.schema.json"
)
IDENTITY_FIELDS = (
    "record_id",
    "source_way_id",
    "directed_segment_id",
    "lane_position",
    "vehicle_class",
    "attribute_name",
    "stop_code",
)


class FormalBlockerGovernanceError(ValueError):
    def __init__(self, message: str, *, stop_code: str = "UNREGISTERED_STATE") -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = "invalid"


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FormalBlockerGovernanceError(f"YAML root must be an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FormalBlockerGovernanceError(f"JSON root must be an object: {path}")
    return value


def _validate_schema(instance: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(instance)
    except jsonschema.ValidationError as error:
        raise FormalBlockerGovernanceError(
            f"{schema_path.name}: {error.message}"
        ) from error


def _semantic_hash(value: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(item) for key, item in value.items() if key != "semantic_sha256"}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@lru_cache(maxsize=1)
def load_formal_blocker_policy() -> dict[str, Any]:
    policy = _load_yaml(POLICY_PATH)
    validate_formal_blocker_policy(policy)
    return policy


def validate_formal_blocker_policy(policy: Mapping[str, Any]) -> None:
    _validate_schema(policy, POLICY_SCHEMA_PATH)
    expected_causes = {
        "implementation_defect",
        "missing_registered_rule",
        "unsupported_source_syntax",
        "missing_scenario_context",
        "missing_vehicle_ontology",
        "missing_evidence",
        "genuine_rule_conflict",
        "outside_research_scope",
        "undetermined",
    }
    if set(policy["root_cause_categories"]) != expected_causes:
        raise FormalBlockerGovernanceError("root-cause registry differs")
    rule_ids = [item["exclusion_rule_id"] for item in policy["registered_exclusion_rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise FormalBlockerGovernanceError("duplicate exclusion rule ID")


def _registered_rule(policy: Mapping[str, Any], rule_id: Any) -> Mapping[str, Any] | None:
    return next(
        (
            item
            for item in policy["registered_exclusion_rules"]
            if item["exclusion_rule_id"] == rule_id
        ),
        None,
    )


def classify_blocker(
    blocker: Mapping[str, Any], *, policy: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    selected_policy = copy.deepcopy(dict(policy or load_formal_blocker_policy()))
    validate_formal_blocker_policy(selected_policy)
    missing = [field for field in IDENTITY_FIELDS if field not in blocker]
    if missing:
        raise FormalBlockerGovernanceError(
            f"blocker identification fields omitted: {missing}"
        )
    for field in ("root_cause_category", "secondary_causes", "research_scope_status", "remediation"):
        if field not in blocker:
            raise FormalBlockerGovernanceError(f"blocker field omitted: {field}")
    root_cause = blocker["root_cause_category"]
    if root_cause not in selected_policy["root_cause_categories"]:
        raise FormalBlockerGovernanceError(f"unregistered root cause: {root_cause}")
    scope = blocker["research_scope_status"]
    if not isinstance(scope, Mapping) or scope.get("value") not in {
        "governed",
        "outside_scope",
        "undetermined",
    }:
        raise FormalBlockerGovernanceError("invalid research scope status")
    if not scope.get("reason") or not isinstance(scope.get("evidence_ids"), list):
        raise FormalBlockerGovernanceError("research scope evidence is incomplete")

    if scope["value"] == "outside_scope":
        if root_cause != "outside_research_scope" or not scope["evidence_ids"]:
            raise FormalBlockerGovernanceError(
                "outside-scope status lacks authoritative evidence"
            )
        rule_id = blocker["remediation"].get("rule_id")
        rule = _registered_rule(selected_policy, rule_id)
        if rule is None:
            raise FormalBlockerGovernanceError(
                f"unregistered exclusion rule: {rule_id}",
                stop_code="EXCLUSION_RULE_UNREGISTERED",
            )
        strategy = "formal_exclusion"
        reason = (
            f"Registered rule {rule_id} proves this record is outside the current "
            "Configuration scope."
        )
    elif scope["value"] == "undetermined":
        strategy = "remain_blocked"
        reason = "Research-scope membership is not proven, so fail-closed state is retained."
    elif root_cause in selected_policy["preserve_and_resolve_causes"]:
        strategy = "preserve_and_resolve"
        reason = (
            f"The governed record has root cause {root_cause}, which requires a registered "
            "remedy and is not an exclusion condition."
        )
    else:
        strategy = "remain_blocked"
        reason = (
            f"The governed record has root cause {root_cause}, but sufficient formal "
            "resolution authority is not currently registered."
        )

    root_ids = blocker.get("root_cause_record_ids", [])
    if blocker["attribute_name"] == "final_permission" and not root_ids:
        raise FormalBlockerGovernanceError(
            "permission blocker omits root-cause record IDs"
        )
    payload = {
        "blocker_id": str(blocker.get("blocker_id") or f"blocker:{blocker['record_id']}"),
        **{field: copy.deepcopy(blocker[field]) for field in IDENTITY_FIELDS},
        "root_cause_category": root_cause,
        "secondary_causes": list(blocker["secondary_causes"]),
        "root_cause_record_ids": list(root_ids),
        "research_scope_status": copy.deepcopy(dict(scope)),
        "selected_strategy": {"value": strategy, "reason": reason},
        "remediation": copy.deepcopy(dict(blocker["remediation"])),
    }
    return payload


def build_blocker_inventory(
    blockers: Sequence[Mapping[str, Any]],
    *,
    inventory_id: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    entries = sorted(
        (classify_blocker(item, policy=policy) for item in blockers),
        key=lambda item: item["blocker_id"],
    )
    ids = [item["blocker_id"] for item in entries]
    record_ids = [item["record_id"] for item in entries]
    if len(ids) != len(set(ids)) or len(record_ids) != len(set(record_ids)):
        raise FormalBlockerGovernanceError("duplicate blocker or record ID")
    strategy_counts = Counter(item["selected_strategy"]["value"] for item in entries)
    cause_counts = Counter(item["root_cause_category"] for item in entries)
    inventory = {
        "schema_version": 17,
        "inventory_id": inventory_id,
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "policy_id": "FORMAL_BLOCKER_POLICY_V17",
        "entries": entries,
        "counts": {
            "total": len(entries),
            "by_strategy": dict(sorted(strategy_counts.items())),
            "by_root_cause": dict(sorted(cause_counts.items())),
        },
    }
    inventory["semantic_sha256"] = _semantic_hash(inventory)
    validate_blocker_inventory(inventory)
    return inventory


def validate_blocker_inventory(inventory: Mapping[str, Any]) -> None:
    _validate_schema(inventory, INVENTORY_SCHEMA_PATH)
    if inventory["semantic_sha256"] != _semantic_hash(inventory):
        raise FormalBlockerGovernanceError("blocker inventory hash differs")
    entries = inventory["entries"]
    if inventory["counts"]["total"] != len(entries):
        raise FormalBlockerGovernanceError("blocker inventory count differs")


def validate_exclusion_manifest(
    manifest: Mapping[str, Any],
    *,
    governed_record_ids: Sequence[str],
    policy: Mapping[str, Any] | None = None,
) -> None:
    selected_policy = dict(policy or load_formal_blocker_policy())
    validate_formal_blocker_policy(selected_policy)
    _validate_schema(manifest, EXCLUSION_SCHEMA_PATH)
    if manifest["semantic_sha256"] != _semantic_hash(manifest):
        raise FormalBlockerGovernanceError("exclusion manifest hash differs")
    counts = manifest["population_counts"]
    if counts["input"] != counts["governed"] + counts["excluded"]:
        raise FormalBlockerGovernanceError("population equation differs")
    if counts["excluded"] != len(manifest["entries"]):
        raise FormalBlockerGovernanceError("excluded population count differs")
    governed = set(governed_record_ids)
    excluded_ids: set[str] = set()
    for entry in manifest["entries"]:
        if _registered_rule(selected_policy, entry["exclusion_rule_id"]) is None:
            raise FormalBlockerGovernanceError(
                f"unregistered exclusion rule: {entry['exclusion_rule_id']}",
                stop_code="EXCLUSION_RULE_UNREGISTERED",
            )
        record_id = entry["record_id"]
        if record_id in governed or record_id in excluded_ids:
            raise FormalBlockerGovernanceError(
                "governed/excluded overlap or duplicate exclusion"
            )
        excluded_ids.add(record_id)
