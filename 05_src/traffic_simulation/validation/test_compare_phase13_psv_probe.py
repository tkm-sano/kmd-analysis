from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from traffic_simulation.network.compare_phase13_psv_probe import (
    PsvProbeComparisonError,
    _semantic_hash,
    _static_access_semantic_hash,
    compare_psv_probe,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "v17_attribute_resolution"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _recompute_probe_hash(probe: dict) -> dict:
    probe["semantic_sha256"] = _static_access_semantic_hash(probe)
    return probe


def _recompute_extraction_hash(extraction: dict) -> dict:
    extraction["semantic_sha256"] = _semantic_hash(extraction)
    return extraction


def _mutate_osm_without_tourist_bus_yes(*, source_osm_path: Path, way_id: int, output_path: Path) -> None:
    tree = ET.parse(str(source_osm_path))
    root = tree.getroot()
    removed = False
    for way in root.findall("way"):
        if int(way.attrib["id"]) != way_id:
            continue
        for tag in list(way.findall("tag")):
            if tag.attrib.get("k") == "tourist_bus" and tag.attrib.get("v") == "yes":
                way.remove(tag)
                removed = True
                break
        if removed:
            break
    assert removed is True
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def test_compare_phase13_psv_probe_accepts_real_artifacts() -> None:
    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        ),
        probe_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        ),
        source_osm_path=Path(
            "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
        ),
    )
    assert result["status"] == "passed"
    assert result["acceptance"]["psv_hierarchy_blockers_are_zero"] is True
    assert result["acceptance"]["resolved_blocker_count_is_16"] is True
    assert result["acceptance"]["tourist_bus_yes_way_set_preserved"] is True


def test_compare_phase13_psv_probe_fails_on_missing_key_value_lineage(tmp_path: Path) -> None:
    base = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        )
    )
    mutated = json.loads(json.dumps(base))
    mutated["normalized_rules"] = [
        {
            "source_way_id": rule["source_way_id"],
            "rules": [
                {
                    **item,
                    "source_value": "no" if item.get("source_key") == "psv" and int(rule["source_way_id"]) == 322744966 else item.get("source_value"),
                }
                for item in rule["rules"]
            ],
        }
        for rule in mutated["normalized_rules"]
    ]
    _recompute_probe_hash(mutated)
    probe_path = tmp_path / "mutated_psv_probe_missing_lineage.json"
    probe_path.write_text(json.dumps(mutated, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        ),
        probe_path=probe_path,
        source_osm_path=Path(
            "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
        ),
    )
    assert result["status"] == "failed"
    assert result["acceptance"]["source_key_value_pairs_preserved"] is False


def test_compare_phase13_psv_probe_fails_when_hash_contract_is_invalid() -> None:
    base = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        )
    )
    base["semantic_sha256"] = "deadbeef" * 4
    fixed_inventory = Path(
        "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
    )
    extraction = Path(
        "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
    )
    probe_path = FIXTURE_DIR / "mutated_psv_probe_bad_hash.json"
    probe_path.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    with pytest.raises(PsvProbeComparisonError):
        compare_psv_probe(
            fixed_inventory_path=fixed_inventory,
            extraction_path=extraction,
            probe_path=probe_path,
            source_osm_path=Path(
                "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
            ),
        )


def test_compare_phase13_psv_probe_fails_when_one_fixed_blocker_remains_in_probe(tmp_path: Path) -> None:
    probe = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        )
    )
    extraction = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        )
    )
    mutated = json.loads(json.dumps(probe))
    retained_record = next(
        record
        for record in extraction["records"]
        if record["selected_blocking_base_key_after_decision_001"] == "psv"
        and int(record["source_way_id"]) == 322744966
    )
    retained = {
        "scope": "source_way",
        "source_way_id": retained_record["source_way_id"],
        "resolution_status": "unresolved",
        "stop_code": retained_record["stop_code"],
        "message": "mutated blocker should have been resolved",
    }
    mutated["blockers"].append(retained)
    _recompute_probe_hash(mutated)
    probe_path = tmp_path / "mutated_psv_probe_one_fixed_blocker_remains.json"
    probe_path.write_text(json.dumps(mutated, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        ),
        probe_path=probe_path,
        source_osm_path=Path(
            "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
        ),
    )
    assert result["status"] == "failed"
    assert result["acceptance"]["psv_hierarchy_blockers_are_zero"] is False
    assert result["stable_id_diff"]["remaining_psv_blocker_count"] > 0


def test_compare_phase13_psv_probe_fails_when_lane_empty_position_values_are_mutated(tmp_path: Path) -> None:
    extraction = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        )
    )
    mutated = json.loads(json.dumps(extraction))
    changed = False
    for record in mutated["records"]:
        if record["selected_blocking_base_key_after_decision_001"] != "psv":
            continue
        for occurrence in record.get("target_occurrences", []):
            if occurrence.get("lane_scoped") and occurrence.get("source_key") == "psv:lanes":
                occurrence["source_value"] = "designated|yes||"
                changed = True
                break
        if changed:
            break
    assert changed is True
    _recompute_extraction_hash(mutated)
    extraction_path = tmp_path / "mutated_psv_extraction_lane_empty_position.json"
    extraction_path.write_text(json.dumps(mutated, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=extraction_path,
        probe_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        ),
        source_osm_path=Path(
            "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
        ),
    )
    assert result["status"] == "failed"
    assert result["acceptance"]["lane_scoped_positions_preserved"] is False
    assert result["lineage_preservation"]["lane_positions_preserved"] is False


def test_compare_phase13_psv_probe_fails_when_psv_blocker_remains(tmp_path: Path) -> None:
    probe = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        )
    )
    extraction = _json(
        Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        )
    )
    mutated = json.loads(json.dumps(probe))
    retained_record = next(
        record
        for record in extraction["records"]
        if record["selected_blocking_base_key_after_decision_001"] == "psv"
        and int(record["source_way_id"]) == 322744966
    )
    retained = {
        "scope": "source_way",
        "source_way_id": retained_record["source_way_id"],
        "resolution_status": "unresolved",
        "stop_code": retained_record["stop_code"],
        "message": "mutated blocker should have been resolved",
    }
    mutated["blockers"].append(retained)
    _recompute_probe_hash(mutated)
    probe_path = tmp_path / "mutated_psv_probe_blocker_remains.json"
    probe_path.write_text(json.dumps(mutated, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        ),
        probe_path=probe_path,
        source_osm_path=Path(
            "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
        ),
    )
    assert result["status"] == "failed"
    assert result["acceptance"]["psv_hierarchy_blockers_are_zero"] is False
    assert result["stable_id_diff"]["remaining_psv_blocker_count"] > 0


def test_compare_phase13_psv_probe_fails_when_tourist_bus_yes_way_is_missing(tmp_path: Path) -> None:
    source_osm_path = Path(
        "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
    )
    way_id = 322744966
    mutated_osm_path = tmp_path / "mutated_ota_ward_tourist_bus_missing.osm.xml"
    _mutate_osm_without_tourist_bus_yes(
        source_osm_path=source_osm_path,
        way_id=way_id,
        output_path=mutated_osm_path,
    )

    result = compare_psv_probe(
        fixed_inventory_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/published/formal/blocker_inventory.json"
        ),
        extraction_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json"
        ),
        probe_path=Path(
            "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260815_psv_full_population_probe/static_access_formal.json"
        ),
        source_osm_path=mutated_osm_path,
    )
    assert result["status"] == "failed"
    assert result["acceptance"]["tourist_bus_yes_way_set_preserved"] is False
