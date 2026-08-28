import csv
import json
from pathlib import Path

import yaml

from traffic_simulation.calibration.finalize_external_observation_mapping import (
    BBOX,
    DATA_DIR,
    EXPECTED_MATCHING,
    HANEDA_DOWN,
    HANEDA_UP,
)


def rows(name: str):
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_all_ten_external_references_have_final_records():
    mapping = rows("external_observation_final_mapping.csv")
    inventory = rows("external_observation_final_inventory.csv")
    assert len(mapping) == len(inventory) == 10
    assert len({row["target_section_id"] for row in mapping}) == 10
    assert {row["target_section_id"] for row in mapping} == {row["target_section_id"] for row in inventory}


def test_all_eight_auto_accept_candidates_are_promoted_without_edge_or_coverage_change():
    candidate = {row["target_section_id"]: row for row in rows("external_observation_mapping_candidates.csv")}
    formal = {row["target_section_id"]: row for row in rows("external_observation_final_mapping.csv")}
    accepted = [row for row in candidate.values() if row["classification"] == "AUTO_ACCEPT"]
    assert len(accepted) == 8
    for before in accepted:
        after = formal[before["target_section_id"]]
        assert after["final_mapping_status"] == "RESOLVED"
        assert after["final_sumo_edge_sequence"] == before["candidate_edge_ids"]
        assert float(after["corridor_coverage_ratio"]) == float(before["candidate_corridor_coverage_ratio"])


def test_haneda_mapping_and_direction_are_separate_and_resolved():
    row = next(row for row in rows("external_observation_final_mapping.csv") if row["official_observation_section_id"] == "13200100070")
    assert row["final_mapping_status"] == "RESOLVED"
    assert row["direction_status"] == "RESOLVED"
    assert row["traffic_assignment_status"] == "USABLE"
    assert row["up_sumo_edge_sequence"].split(";") == HANEDA_UP
    assert row["down_sumo_edge_sequence"].split(";") == HANEDA_DOWN
    corridors = json.loads(row["final_sumo_corridors_json"])
    assert {item["role"] for item in corridors} == {"UP_TERMINUS_TO_ORIGIN", "DOWN_ORIGIN_TO_TERMINUS"}


def test_fixed_bbox_extension_records_before_after_coverage_and_status():
    row = rows("external_observation_network_extension_before_after.csv")[0]
    assert json.loads(row["fixed_bbox_wgs84_json"]) == {
        "west": BBOX[0], "south": BBOX[1], "east": BBOX[2], "north": BBOX[3]
    }
    assert float(row["before_coverage_ratio"]) == 0.245414
    assert float(row["after_coverage_ratio"]) == 0.835796
    assert float(row["after_uncovered_length_m"]) < float(row["before_uncovered_length_m"])
    assert row["after_mapping_status"] == "RESOLVED"
    assert row["bbox_auto_expanded"] == "False"


def test_every_adopted_corridor_has_zero_connection_violations():
    assert all(int(row["connection_violation_count"]) == 0 for row in rows("external_observation_final_mapping.csv"))
    assert all(row["connection_to_next_status"] == "CONNECTED" for row in rows("external_observation_mapping_final_edge_evidence.csv"))


def test_every_formal_record_has_layered_provenance_for_adopted_values():
    for row in rows("external_observation_final_mapping.csv"):
        provenance = json.loads(row["provenance_json"])
        assert set(provenance) == {"raw", "normalized", "adopted", "model_assumed", "sources", "rule"}
        assert provenance["adopted"]["edge_ids"]
        assert provenance["adopted"]["route_system"]
        assert provenance["rule"]["id"] == row["rule_id"]
        hashes = json.loads(row["input_hashes_json"])
        assert hashes and all(len(value) == 64 for value in hashes.values())


def test_no_arbitrary_representative_edge_is_selected():
    qa = json.loads((DATA_DIR / "external_observation_final_mapping_qa_summary.json").read_text())
    assert qa["guardrails"]["representative_edge_selected"] is False
    for row in rows("external_observation_final_mapping.csv"):
        assert len(row["final_sumo_edge_sequence"].split(";")) > 1


def test_matching_thresholds_are_unchanged():
    config_path = Path(__file__).resolve().parents[3] / "reproducibility/config/traffic_simulation/road_census_sumo_mapping.yml"
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    assert config["matching"] == EXPECTED_MATCHING
    qa = json.loads((DATA_DIR / "external_observation_final_mapping_qa_summary.json").read_text())
    assert qa["guardrails"]["matching_threshold_changed"] is False


def test_ota66_mapping_and_materialized_attributes_are_unchanged():
    regression = rows("ota66_network_extension_regression.csv")
    assert len(regression) == 66
    assert all(row["comparison_status"] == "UNCHANGED" for row in regression)
    assert all(row["before_final_edge_ids"] == row["after_final_edge_ids"] for row in regression)
    assert all(int(row[field]) == 0 for row in regression for field in (
        "edge_id_change_count", "edge_split_or_topology_change_count",
        "lane_attribute_change_count", "speed_attribute_change_count", "route_identity_change_count",
    ))
    assert sum(row["after_usable_for_traffic_assignment"] == "True" for row in regression) == 65


def test_partial_coverage_and_unresolved_direction_are_not_filled_or_coerced():
    formal = rows("external_observation_final_mapping.csv")
    route_316 = [row for row in formal if row["official_observation_section_id"] == "13403160320"]
    assert len(route_316) == 3
    assert all(float(row["corridor_coverage_ratio"]) == 0.580542 for row in route_316)
    assert all(float(row["uncovered_length_m"]) > 0 for row in route_316)
    assert sum(row["direction_status"] == "MODEL_ASSUMPTION_REQUIRED" for row in formal) == 9
    assert all(row["up_sumo_edge_sequence"] == row["down_sumo_edge_sequence"] == "" for row in formal if row["direction_status"] != "RESOLVED")
    qa = json.loads((DATA_DIR / "external_observation_final_mapping_qa_summary.json").read_text())
    assert qa["guardrails"]["missing_value_imputed_as_zero"] is False


def test_manifest_hashes_all_declared_outputs():
    manifest = json.loads((DATA_DIR / "external_observation_final_mapping_manifest.json").read_text())
    assert manifest["fixed_bbox_wgs84"] == {"west": BBOX[0], "south": BBOX[1], "east": BBOX[2], "north": BBOX[3]}
    assert manifest["tools"]["netconvert"] == "Eclipse SUMO netconvert Version 1.24.0"
    assert manifest["inputs"] and manifest["outputs"]
