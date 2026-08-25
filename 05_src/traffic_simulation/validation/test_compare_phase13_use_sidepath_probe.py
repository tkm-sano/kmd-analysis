from __future__ import annotations

import json
from pathlib import Path

from traffic_simulation.network.compare_phase13_use_sidepath_probe import compare


DECISION = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_use_sidepath_semantics_decision.yml"
)
REGISTRY = Path(
    "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
BASELINE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260818_motorcar_full_population_probe/static_access_formal.json"
)
PROBE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_bicycle_use_sidepath_full_population_probe/"
    "static_access_formal.json"
)
SOURCE_OSM = Path(
    "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)


def test_real_c1_probe_passes_stable_id_and_permission_guards() -> None:
    result = compare(
        decision_path=DECISION,
        registry_path=REGISTRY,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    assert result["status"] == "passed"
    assert all(result["acceptance"].values())
    assert result["stable_id_diff"]["affected_way_count"] == 27
    assert result["stable_id_diff"]["removed_blocker_id_count"] == 27
    assert result["stable_id_diff"]["new_blocker_id_count"] == 0


def test_comparator_records_observed_successor_blockers() -> None:
    result = compare(
        decision_path=DECISION,
        registry_path=REGISTRY,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    assert result["successor_blockers"]["count"] == len(
        result["successor_blockers"]["records"]
    )
    assert result["successor_blockers"][
        "c2_access_specificity_conflict_exposed"
    ] is False
    for record in result["successor_blockers"]["records"]:
        assert record["source_way_id"]
        assert record["stop_code"]
        assert record["source_tags"]


def test_persisted_comparator_matches_recomputed_result() -> None:
    persisted_path = PROBE.parent / "bicycle_use_sidepath_stable_id_diff.json"
    persisted = json.loads(persisted_path.read_text(encoding="utf-8"))

    # This is immutable C1 evidence produced against registry v1.8.0. Later
    # versioned amendments must not turn its registry hash into a rolling hash.
    assert persisted["status"] == "passed"
    assert all(persisted["acceptance"].values())
    assert persisted["stable_id_diff"]["affected_way_count"] == 27
    assert persisted["stable_id_diff"]["removed_blocker_id_count"] == 27
