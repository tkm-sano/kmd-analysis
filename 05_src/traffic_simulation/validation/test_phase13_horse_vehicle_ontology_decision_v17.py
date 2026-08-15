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
    assert governed["authority_byte_sha256"] == _sha256(network_path)
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
