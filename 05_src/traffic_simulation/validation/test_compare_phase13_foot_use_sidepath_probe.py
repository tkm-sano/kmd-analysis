from __future__ import annotations

import json
from pathlib import Path

from traffic_simulation.network.compare_phase13_foot_use_sidepath_probe import compare


DECISION = Path(
    "reproducibility/config/traffic_simulation/"
    "v17_phase13_use_sidepath_semantics_decision_v1_1.yml"
)
REGISTRY = Path(
    "reproducibility/config/traffic_simulation/"
    "attribute_resolution_registries_v17.yml"
)
BASELINE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_source_hierarchy_specificity_full_population_probe/"
    "static_access_formal.json"
)
PROBE = Path(
    "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/"
    "phase13_20260820_foot_use_sidepath_full_population_probe_v2/"
    "static_access_formal.json"
)
SOURCE_OSM = Path(
    "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)


def test_real_c2_probe_passes_stable_id_and_specificity_guards() -> None:
    result = compare(
        decision_path=DECISION,
        registry_path=REGISTRY,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    assert result["status"] == "passed"
    assert all(result["acceptance"].values())
    assert result["stable_id_diff"]["affected_way_count"] == 4
    assert result["stable_id_diff"]["removed_blocker_id_count"] == 4
    assert result["stable_id_diff"]["new_blocker_id_count"] == 0
    assert result["specificity_guard"]["c2_static_maxima_count"] == 8


def test_persisted_c2_comparator_remains_semantically_reproducible() -> None:
    persisted = json.loads(
        (PROBE.parent / "foot_use_sidepath_stable_id_diff.json").read_text(
            encoding="utf-8"
        )
    )
    recomputed = compare(
        decision_path=DECISION,
        registry_path=REGISTRY,
        baseline_path=BASELINE,
        probe_path=PROBE,
        source_osm_path=SOURCE_OSM,
    )

    # The immutable C2 comparator binds the registry version current at its
    # creation.  Later approved registry amendments may change provenance and
    # the envelope hash without changing any C2 result.
    for key in (
        "status",
        "acceptance",
        "stable_id_diff",
        "specificity_guard",
        "successor_blockers",
    ):
        assert persisted[key] == recomputed[key]
    assert persisted["sources"]["registry"] != recomputed["sources"]["registry"]
