from traffic_simulation.calibration.build_road_census_sumo_rebaseline import (
    DEFAULT_DATA_DIR,
    build_snapshot,
    render_markdown,
)


def test_current_baseline_covers_all_66_sections() -> None:
    snapshot = build_snapshot(DEFAULT_DATA_DIR)

    assert snapshot["mapping"]["usable_sections"] == 65
    assert snapshot["section_statuses"]["lane"]["counts"] == {
        "DATA_CONFLICT": 2,
        "MODEL_ASSUMPTION_REQUIRED": 19,
        "NO_ASSUMPTION_NEEDED": 40,
        "UNRESOLVED": 5,
    }
    assert snapshot["section_statuses"]["speed"]["counts"] == {
        "DATA_CONFLICT": 10,
        "NO_ASSUMPTION_NEEDED": 55,
        "UNRESOLVED": 1,
    }
    assert snapshot["section_statuses"]["traffic"]["counts"] == {
        "DATA_NOT_AVAILABLE": 11,
        "MODEL_ASSUMPTION_REQUIRED": 1,
        "NO_ASSUMPTION_NEEDED": 34,
        "UNRESOLVED": 20,
    }
    for target in ("lane", "speed", "traffic"):
        assert sum(snapshot["section_statuses"][target]["counts"].values()) == 66


def test_baseline_records_external_formalization_and_preserves_remaining_gaps() -> None:
    snapshot = build_snapshot(DEFAULT_DATA_DIR)

    assert snapshot["external_observation_mapping"]["processing_omission_sections"] == 10
    assert snapshot["external_observation_mapping"]["municipality_counts"] == {
        "13109_shinagawa": 7,
        "13112_setagaya": 3,
    }
    assert snapshot["external_observation_mapping"]["mapping_status"] == "FORMALIZED_10_OF_10"
    assert snapshot["external_observation_mapping"]["classification_counts"] == {
        "AUTO_ACCEPT": 8,
        "REVIEW_REQUIRED": 1,
        "NETWORK_EXTENSION_REQUIRED": 1,
        "UNRESOLVED": 0,
    }
    assert snapshot["external_observation_mapping"]["formal_mapping_status_counts"] == {"RESOLVED": 10}
    assert snapshot["external_observation_mapping"]["direction_status_counts"] == {
        "MODEL_ASSUMPTION_REQUIRED": 9,
        "RESOLVED": 1,
    }
    assert snapshot["external_observation_mapping"]["limited_network_extension"]["coverage_ratio"] == 0.835796
    assert snapshot["formalization_gaps"]["external_observation_mapping"] == "COMPLETE_10_OF_10_LAYERED_FINAL_STATUS"
    assert snapshot["formalization_gaps"]["final_inventory_330_cells"] == "NOT_GENERATED"
    assert snapshot["formal_artifacts"]["final_sumo_road_attributes.csv"]["exists"] is False
    assert snapshot["formal_artifacts"]["final_traffic_observations.csv"]["exists"] is False
    assert snapshot["formal_artifacts"]["external_observation_final_mapping.csv"]["formal_contract_complete"] is True
    assert len(snapshot["source_manifest"]) == 17


def test_markdown_calls_out_partial_stage_corrections() -> None:
    snapshot = build_snapshot(DEFAULT_DATA_DIR)
    markdown = render_markdown(snapshot, DEFAULT_DATA_DIR / "baseline.json")

    assert "65/66" in markdown
    assert "40/19/2/5" in markdown
    assert "部分工程の件数を66区間全体の件数として扱わない" in markdown
