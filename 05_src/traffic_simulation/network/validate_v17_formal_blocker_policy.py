from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.formal_blocker_governance_v17 import (
    POLICY_PATH,
    FormalBlockerGovernanceError,
    build_blocker_inventory,
    classify_blocker,
    load_formal_blocker_policy,
    validate_exclusion_manifest,
)
from traffic_simulation.network.validate_v17_phase10_evidence_resolution import (
    validate_phase10_evidence_resolution,
)
from traffic_simulation.network.validate_v17_fixture_oracle import FIXTURE_ROOT
from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
FIXTURES = FIXTURE_ROOT / "formal_blocker_phase13_fixture.yml"
ORACLES = FIXTURE_ROOT / "formal_blocker_phase13_oracle.yml"
HASH = "a" * 64


class FormalBlockerPolicyValidationError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FormalBlockerPolicyValidationError(f"YAML root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_policy() -> dict[str, Any]:
    policy = copy.deepcopy(load_formal_blocker_policy())
    policy["registered_exclusion_rules"] = [
        {
            "exclusion_rule_id": "FIXTURE-OUTSIDE-AREA-V1",
            "rule_version": "1.0.0",
            "decision_id": "FIXTURE-DECISION-002",
            "scope_predicate": {"fixture_outside_area": True},
            "evidence_sha256": HASH,
            "approver": "independent_fixture_authority",
            "approval_date": "2026-08-04",
        }
    ]
    return policy


def _semantic_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_formal_blocker_policy_adoption() -> dict[str, Any]:
    validate_phase10_evidence_resolution()
    policy = load_formal_blocker_policy()
    reference = _load_yaml(REGISTRY_BUNDLE_PATH)["formal_blocker_policy"]
    if reference["policy_id"] != policy["policy_id"]:
        raise FormalBlockerPolicyValidationError("formal blocker policy ID mismatch")
    if reference["policy_version"] != policy["policy_version"]:
        raise FormalBlockerPolicyValidationError("formal blocker policy version mismatch")
    if reference["sha256"] != _sha256(POLICY_PATH):
        raise FormalBlockerPolicyValidationError("formal blocker policy hash mismatch")
    if policy["registered_exclusion_rules"] or reference["registered_exclusion_rule_count"]:
        raise FormalBlockerPolicyValidationError("unproven production exclusion rule exists")

    fixtures = {
        item["fixture_id"]: item["input"]
        for item in _load_yaml(FIXTURES)["cases"]
    }
    oracles = {
        item["fixture_id"]: item
        for item in _load_yaml(ORACLES)["oracles"]
    }
    classified = []
    for fixture_id in ("FB-POS-001", "FB-POS-002", "FB-POS-003"):
        result = classify_blocker(fixtures[fixture_id])
        if result["selected_strategy"]["value"] != oracles[fixture_id]["selected_strategy"]:
            raise FormalBlockerPolicyValidationError(
                f"formal blocker strategy oracle mismatch: {fixture_id}"
            )
        classified.append(fixtures[fixture_id])
    try:
        classify_blocker(fixtures["FB-NEG-001"])
    except FormalBlockerGovernanceError as error:
        if error.stop_code != oracles["FB-NEG-001"]["stop_code"]:
            raise FormalBlockerPolicyValidationError("unregistered exclusion oracle mismatch") from error
    else:
        raise FormalBlockerPolicyValidationError("unregistered exclusion fixture passed")
    fixture_exclusion = classify_blocker(
        fixtures["FB-POS-004"], policy=_fixture_policy()
    )
    if fixture_exclusion["selected_strategy"]["value"] != "formal_exclusion":
        raise FormalBlockerPolicyValidationError("registered fixture exclusion did not classify")

    inventory = build_blocker_inventory(
        classified, inventory_id="FORMAL-BLOCKER-VALIDATION-INVENTORY-V1"
    )
    repeated = build_blocker_inventory(
        list(reversed(classified)),
        inventory_id="FORMAL-BLOCKER-VALIDATION-INVENTORY-V1",
    )
    if inventory != repeated:
        raise FormalBlockerPolicyValidationError("blocker inventory order changed semantics")
    empty_manifest = {
        "schema_version": 17,
        "manifest_id": "FORMAL-EMPTY-EXCLUSION-MANIFEST-V1",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "policy_id": "FORMAL_BLOCKER_POLICY_V17",
        "entries": [],
        "population_counts": {"input": 3, "governed": 3, "excluded": 0},
    }
    empty_manifest["semantic_sha256"] = _semantic_hash(empty_manifest)
    validate_exclusion_manifest(
        empty_manifest,
        governed_record_ids=[item["record_id"] for item in classified],
    )

    return {
        "formal_blocker_policy_adoption": "passed",
        "production_exclusion_rule_count": 0,
        "fixed_oracle_comparison_count": 5,
        "exclusive_strategy_count": 3,
        "population_equation": "passed",
        "two_run_determinism": "passed",
        "phase13_completion_claimed": False,
    }


def main() -> int:
    try:
        result = validate_formal_blocker_policy_adoption()
    except (
        FormalBlockerPolicyValidationError,
        FormalBlockerGovernanceError,
        KeyError,
    ) as error:
        print(json.dumps({"formal_blocker_policy_adoption": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
