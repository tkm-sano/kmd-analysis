from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DECISION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_horse_vehicle_ontology_decision.yml"
)
EXTRACTION_RECORD_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_vehicle_ontology_record_extraction.yml"
)
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml"
)
INVARIANTS_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_semantic_invariants.yml"
)
TRACEABILITY_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/v17_attribute_resolution_traceability_matrix.md"
)
HORSE_FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "phase13_horse_vehicle_domain_fixture.yml"
)
HORSE_ORACLE_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/"
    "phase13_horse_vehicle_domain_oracle.yml"
)
HORSE_PROBE_RECORD_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "v17_phase13_horse_full_population_probe.yml"
)


def _yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_horse_decision_is_fixed_and_matches_research_vehicle_authorities() -> None:
    decision = _yaml(DECISION_PATH)
    profile_path = REPOSITORY_ROOT / decision["research_vehicle_authority"][
        "managed_vehicle_profile"
    ]["path"]
    network_path = REPOSITORY_ROOT / decision["research_vehicle_authority"][
        "governed_universe"
    ]["authority_path"]
    profile = _yaml(profile_path)
    network = _yaml(network_path)

    assert decision["status"] == "approved"
    assert decision["decision"]["result"] == "approved_empty_intersection"
    assert decision["decision"]["registered_vehicle_domain"] == []
    assert decision["decision"]["formal_exclusion"] is False
    assert decision["decision"]["source_record_preserved"] is True
    assert set(decision["decision"]["approved_source_values"]) == {"no", "yes"}

    asserted_profile = decision["research_vehicle_authority"][
        "managed_vehicle_profile"
    ]
    assert asserted_profile["byte_sha256"] == _sha256(profile_path)
    assert asserted_profile["profile_id"] == profile["vehicle_profile_id"]
    assert asserted_profile["sumo_vclass"] == profile["sumo_vclass"] == "delivery"
    assert asserted_profile["powertrain"] == profile["powertrain"] == "battery_electric"
    assert asserted_profile["osm_access_membership"] == profile[
        "osm_access_membership"
    ]

    governed = decision["research_vehicle_authority"]["governed_universe"]
    # The Horse decision is an immutable historical record.  The governed
    # configuration is allowed to change bytes when later Phase 13 decisions
    # update registry references, provided the governed vehicle universe
    # relevant to this decision remains semantically unchanged.
    assert governed["authority_byte_sha256"] == (
        "6cf1b81d07ce7c947063101f0b8beed7d0befe99c11c62a3af313feb47438d78"
    )
    assert governed["vclasses"] == network["permissions"]["governed_vclasses"]
    assert "horse" not in governed["vclasses"]
    assert decision["formal_reasoning"]["sets"]["H"] == []
    assert decision["formal_reasoning"]["sets"]["D"] == ["delivery"]


def test_horse_decision_matches_fixed_record_evidence_and_preserves_boundaries() -> None:
    decision = _yaml(DECISION_PATH)
    extraction = _yaml(EXTRACTION_RECORD_PATH)
    evidence = decision["fixed_record_evidence"]

    assert evidence["source_way_count"] == extraction["results"][
        "source_way_memberships"
    ]["horse"] == 130
    assert evidence["source_value_counts"] == {"no": 125, "yes": 5}
    assert evidence["direction_or_lane_scoped_record_count"] == 0
    assert len(decision["osm_authority_evidence"]) == 2
    assert all(
        item["url"].startswith("https://wiki.openstreetmap.org/w/index.php?")
        and "oldid=" in item["url"]
        and item["accessed_at"] == "2026-08-14"
        for item in decision["osm_authority_evidence"]
    )

    boundaries = "\n".join(decision["mandatory_boundaries"])
    assert "horse=yes cannot override access=no" in boundaries
    assert "horse=no cannot deny a delivery vehicle" in boundaries
    assert "carriage is not horse" in boundaries
    assert "must not be moved to the exclusion population" in boundaries
    assert "ACCESS_VEHICLE_HIERARCHY_MISSING" in boundaries


def test_horse_decision_is_synchronized_to_registry_invariant_and_test_vectors() -> None:
    decision = _yaml(DECISION_PATH)
    registry = _yaml(REGISTRY_PATH)
    invariants = _yaml(INVARIANTS_PATH)
    fixture = _yaml(HORSE_FIXTURE_PATH)
    oracle = _yaml(HORSE_ORACLE_PATH)
    registered = registry["vehicle_ontology"]["non_governed_domain_decisions"][
        "horse"
    ]

    assert registry["registry_version"] == "1.7.0"
    assert registry["vehicle_ontology"]["domains"]["horse"] == []
    assert registered["decision_id"] == decision["decision_id"]
    assert registered["rule_id"] == decision["decision"]["rule_id"]
    assert registered["approved_source_values"] == decision["decision"][
        "approved_source_values"
    ]
    assert registered["registered_vehicle_domain"] == []
    assert registered["formal_exclusion"] is False

    invariant = next(
        item for item in invariants["invariants"] if item["invariant_id"] == "AR-ACCESS-009"
    )
    assert invariants["version"] == "1.4.0"
    assert "scalar yes/no" in invariant["assertion"]
    assert "never creates a formal exclusion" in invariant["assertion"]

    assert fixture["decision_id"] == oracle["decision_id"] == decision["decision_id"]
    assert fixture["rule_id"] == oracle["rule_id"] == decision["decision"]["rule_id"]
    assert len(fixture["cases"]) == 5
    assert len(fixture["fail_closed_cases"]) == 5
    assert oracle["expected_horse_vehicle_domain"] == []
    assert oracle["permission_effect_on_governed_vclasses"] == "none"
    assert oracle["formal_exclusion"] is False

    traceability = TRACEABILITY_PATH.read_text(encoding="utf-8")
    for token in (
        decision["decision_id"],
        decision["decision"]["rule_id"],
        "AR-ACCESS-009",
        HORSE_FIXTURE_PATH.name,
        HORSE_ORACLE_PATH.name,
    ):
        assert token in traceability


def test_horse_full_population_probe_records_strict_failure_without_hiding_it() -> None:
    decision = _yaml(DECISION_PATH)
    probe = _yaml(HORSE_PROBE_RECORD_PATH)
    result = probe["horse_130_result"]
    permission = probe["managed_delivery_permission_result"]

    assert decision["decision_version"] == "1.2.0"
    assert decision["implementation_state"]["full_population_probe"] == (
        "failed_strict_new_stable_blocker_id_acceptance"
    )
    assert probe["status"] == "failed_strict_new_stable_blocker_id_acceptance"
    assert result["fixed_horse_blocker_count"] == 130
    assert result["remaining_horse_hierarchy_blocker_count"] == 0
    assert result["new_blocked_source_way_count"] == 0
    assert result["new_stable_blocker_id_count"] == 2
    assert result["unexpected_blocker_transition_count"] == 0
    assert permission["compared_lane_tuple_count"] == 336
    assert permission["unexpected_permission_change_count"] == 0
    assert probe["acceptance"]["new_stable_blocker_ids_are_zero"] is False
    assert probe["acceptance"]["overall_pass"] is False

    implementation = probe["stable_id_and_permission_comparison"]["implementation"]
    implementation_path = REPOSITORY_ROOT / implementation["path"]
    assert implementation["byte_sha256"] == _sha256(implementation_path)
