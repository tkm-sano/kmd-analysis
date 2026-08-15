from __future__ import annotations

from traffic_simulation.network.build_urban_lastmile_vehicle_tables_v1 import (
    RECORDS_PATH,
    STRATA_PATH,
    _load,
    build_strata,
)
from traffic_simulation.network.validate_urban_lastmile_vehicle_population_v1 import validate
from traffic_simulation.network.validate_urban_lastmile_vehicle_population_v1 import (
    AUTHORITATIVE_SOURCES,
)


def test_population_validator_passes_all_contract_checks() -> None:
    result = validate()
    assert result == {
        "deterministic_projections": "passed",
        "deployment_evidence_count": 3,
        "record_count": 8,
        "schema_validation": "passed",
        "source_count": 12,
    }


def test_population_keeps_unknowns_and_variant_boundaries_explicit() -> None:
    records = {item["record_id"]: item for item in _load(RECORDS_PATH)["records"]}
    honda = records["F1-HONDA-NVAN-E-COMMON-2025"]
    npr = records["F6-ISUZU-ELF-EV-NPR-CAPABILITY"]
    assert honda["physical"]["curb_mass_kg"] is None
    assert honda["physical"]["gross_vehicle_mass_kg"] is None
    assert honda["record_type"] == "chassis_or_platform_capability"
    assert npr["record_type"] == "chassis_or_platform_capability"
    assert npr["physical"]["length_m"] is None
    assert npr["physical"]["height_m"] is None


def test_empirical_envelopes_are_exact_source_projections() -> None:
    output = build_strata(_load(RECORDS_PATH), _load(STRATA_PATH))
    f1 = output["strata"]["F1"]
    assert f1["independent_platform_family_count"] == 3
    assert f1["empirical_envelope"]["height_m"] == {
        "observed_min": 1.89,
        "observed_max": 1.96,
        "contributing_record_count": 3,
        "source_record_ids": [
            "F1-MITSUBISHI-MINICAB-EV-2S-2025",
            "F1-HONDA-NVAN-E-COMMON-2025",
            "F1-SUZUKI-E-EVERY-2S-2026",
        ],
    }
    assert output["strata"]["F2"]["evidence_status"] == "incomplete"
    assert output["strata"]["F2"]["bev_energy_parameter_status"] == "unresolved"
    assert output["strata"]["F3"]["empirical_envelope"]["length_m"]["contributing_record_count"] == 0
    assert output["strata"]["F3"]["empirical_envelope"]["length_m"]["source_record_ids"] == []


def test_sources_and_numeric_field_provenance_are_explicit() -> None:
    from traffic_simulation.network.build_urban_lastmile_vehicle_tables_v1 import CONFIG

    sources = _load(CONFIG / "evidence/lastmile_delivery_sources_v1.yml")
    assert {item["source_id"]: item["url"] for item in sources["sources"]} == AUTHORITATIVE_SOURCES
    records = _load(RECORDS_PATH)["records"]
    assert all("field_provenance" in item and "source_fields" not in item for item in records)
    assert len({item["platform_family_id"] for item in records}) == len(records)
