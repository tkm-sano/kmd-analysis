#!/usr/bin/env python3
"""Build canonical SUMO calibration detector locations.

Principles
----------
- Input population is the canonical external-observation final inventory.
- Only CALIBRATION_USABLE current observation sections are used.
- UP/DOWN direction is inherited from the formally resolved canonical corridors.
- Official GeoJSON coordinate order is NOT used as direction evidence.
- Official geometry is used only to choose a representative cross-section
  position within already direction-resolved corridors.
- One representative SUMO edge is selected per
  official_observation_section_id x direction.
- Detectors are placed on all motorized lanes of that representative edge.
- No SUMO network, mapping, observation, or threshold input is modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd

from traffic_simulation.paths import REPOSITORY_ROOT
from traffic_simulation.calibration import fix_ota_sumo_measurement_locations as legacy


SCRIPT_VERSION = "1.0.0"
RUN_ID = "canonical_calibration_detectors_20260827_v1"

BASE = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration"
    / "road_census_sumo_mapping_20260826"
)

CANONICAL_FINAL_DIR = BASE / "external_observation_finalization_20260827"

INVENTORY_CSV = (
    CANONICAL_FINAL_DIR
    / "external_observation_final_inventory.csv"
)

OBSERVATIONS_CSV = (
    CANONICAL_FINAL_DIR
    / "final_traffic_observations.csv"
)

NETWORK = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation"
    / "attribute_resolution_v17"
    / "phase13_20260823_v17_oneway_materialization_tdd"
    / "ota_ward_explicit_v17_oneway.net.xml"
)

TILE_DIR = (
    REPOSITORY_ROOT
    / "03_data/raw/traffic_simulation/road_census"
    / "mlit_r3_tokyo_20260823"
    / "webmap_tiles"
)

LEGACY_V4_DIR = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/calibration"
    / "20260823_ota_sumo_measurement_locations_v4"
)

LEGACY_DETECTOR_XML = (
    LEGACY_V4_DIR
    / "official_traffic_measurement_detectors.add.xml"
)

DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "reproducibility/outputs/traffic_simulation/calibration"
    / RUN_ID
)

SAMPLE_FRACTIONS = (0.25, 0.35, 0.50, 0.65, 0.75)

EXPECTED_SECTIONS = {
    "13400020040",
    "13400110130",
    "13604210030",
}

# Diagnostic result already reproduced from the canonical corridors.
# These are validation expectations, not hard-coded selection outputs.
EXPECTED_REPRESENTATIVE_EDGES = {
    ("13400020040", "UP"): "254079818#19",
    ("13400020040", "DOWN"): "309829214#19",
    ("13400110130", "UP"): "-261270870#14",
    ("13400110130", "DOWN"): "261270870#14",
    ("13604210030", "UP"): "-295461976#6",
    ("13604210030", "DOWN"): "295461976#6",
}

LEGACY_V4_REFERENCE = {
    ("13400020040", "UP"): "254079818#19",
    ("13400020040", "DOWN"): "309829214#19",
    ("13604210030", "UP"): "-295461976#6",
    ("13604210030", "DOWN"): "295461976#6",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    """Return a stable manifest key.

    Repository artifacts use repository-relative paths.
    Temporary test outputs outside the repository use only their filename.
    """
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return resolved.name


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def split_edges(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [item for item in str(value).split(";") if item]


def corridors_by_direction(row: pd.Series) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    pairs = [
        (
            row["selected_corridor_role"],
            split_edges(row["selected_edge_sequence"]),
        ),
        (
            row["opposite_corridor_role"],
            split_edges(row["opposite_edge_sequence"]),
        ),
    ]

    for role, edge_ids in pairs:
        if role == "UP_TERMINUS_TO_ORIGIN":
            result["UP"] = edge_ids
        elif role == "DOWN_ORIGIN_TO_TERMINUS":
            result["DOWN"] = edge_ids
        else:
            raise ValueError(f"unexpected canonical corridor role: {role}")

    if set(result) != {"UP", "DOWN"}:
        raise ValueError(
            f"both canonical directions are not available for "
            f"target {row['target_id']}"
        )

    return result


def nearest_corridor_edge(
    point: Any,
    edge_ids: list[str],
    edges: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    for edge_id in edge_ids:
        if edge_id not in edges:
            raise ValueError(f"canonical edge missing from SUMO network: {edge_id}")

        edge = edges[edge_id]
        line = edge["shape"]
        edge_position = line.project(point)
        nearest = line.interpolate(edge_position)

        candidates.append(
            {
                "edge": edge,
                "edge_id": edge_id,
                "edge_position_m": edge_position,
                "distance_m": point.distance(nearest),
                "endpoint_clearance_m": min(
                    edge_position,
                    max(0.0, line.length - edge_position),
                ),
            }
        )

    if not candidates:
        raise ValueError("empty canonical corridor")

    return min(
        candidates,
        key=lambda item: (
            item["distance_m"],
            -item["endpoint_clearance_m"],
            item["edge_id"],
        ),
    )


def select_representative_pair(
    official: Any,
    corridors: dict[str, list[str]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []

    for fraction in SAMPLE_FRACTIONS:
        official_point = official.interpolate(official.length * fraction)

        up = nearest_corridor_edge(
            official_point,
            corridors["UP"],
            edges,
        )
        down = nearest_corridor_edge(
            official_point,
            corridors["DOWN"],
            edges,
        )

        score = (
            -min(
                up["endpoint_clearance_m"],
                down["endpoint_clearance_m"],
            ),
            max(
                up["distance_m"],
                down["distance_m"],
            ),
            up["distance_m"] + down["distance_m"],
            abs(fraction - 0.5),
            up["edge_id"],
            down["edge_id"],
        )

        attempts.append(
            {
                "sample_fraction": fraction,
                "official_point": official_point,
                "UP": up,
                "DOWN": down,
                "score": score,
            }
        )

    return min(attempts, key=lambda item: item["score"])


def detector_template() -> tuple[str, dict[str, str]]:
    """Reuse the established v4 SUMO detector element semantics.

    We intentionally do not invent a new SUMO detector type or output policy.
    Only detector-specific id/lane/pos values are replaced.
    """
    root = ET.parse(LEGACY_DETECTOR_XML).getroot()
    children = list(root)

    if not children:
        raise ValueError("legacy v4 detector XML is empty")

    first = children[0]
    fixed = {
        key: value
        for key, value in first.attrib.items()
        if key not in {"id", "lane", "pos"}
    }

    return first.tag, fixed


def write_detector_xml(
    path: Path,
    detector_rows: list[dict[str, Any]],
) -> None:
    tag, fixed_attributes = detector_template()

    root = ET.Element("additional")

    for row in detector_rows:
        attrs = dict(fixed_attributes)
        attrs.update(
            {
                "id": str(row["detector_id"]),
                "lane": str(row["lane_id"]),
                "pos": f"{float(row['position_m']):.3f}",
            }
        )
        ET.SubElement(root, tag, attrs)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(
        path,
        encoding="utf-8",
        xml_declaration=True,
    )


def build(output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"immutable output already exists: {output}")

    output.mkdir(parents=True)

    inventory = pd.read_csv(INVENTORY_CSV)

    usable = inventory[
        inventory["calibration_usability_status"] == "CALIBRATION_USABLE"
    ].copy()

    if usable["target_id"].nunique() != 5:
        raise ValueError("canonical inventory does not contain five usable targets")

    if set(
        usable["official_observation_section_id"].astype(str).unique()
    ) != EXPECTED_SECTIONS:
        raise ValueError(
            "canonical usable independent observation-section population "
            "is not the expected three sections"
        )

    # The three Route 11 targets share one canonical observation section and
    # identical direction-resolved corridors. Keep one row per independent
    # official observation section for count-location generation.
    section_rows = (
        usable
        .sort_values("target_id")
        .drop_duplicates("official_observation_section_id")
    )

    net = legacy.load_net(NETWORK)

    official_features = legacy.load_official_features(
        TILE_DIR,
        EXPECTED_SECTIONS,
        net["location"],
    )

    registry = legacy.DetectorRegistry()

    count_locations: list[dict[str, Any]] = []
    selection_attempts: list[dict[str, Any]] = []

    for _, row in section_rows.iterrows():
        section = str(row["official_observation_section_id"])
        corridors = corridors_by_direction(row)

        selected = select_representative_pair(
            official_features[section],
            corridors,
            net["edges"],
        )

        for fraction in SAMPLE_FRACTIONS:
            candidate = next(
                item
                for item in [
                    select_attempt
                    for select_attempt in [
                        {
                            "sample_fraction": f,
                            "official_point": official_features[section].interpolate(
                                official_features[section].length * f
                            ),
                        }
                        for f in SAMPLE_FRACTIONS
                    ]
                ]
                if item["sample_fraction"] == fraction
            )

            for direction in ("UP", "DOWN"):
                item = nearest_corridor_edge(
                    candidate["official_point"],
                    corridors[direction],
                    net["edges"],
                )
                selection_attempts.append(
                    {
                        "official_observation_section_id": section,
                        "direction": direction,
                        "sample_fraction": fraction,
                        "edge_id": item["edge_id"],
                        "edge_position_m": round(item["edge_position_m"], 3),
                        "distance_from_official_geometry_m": round(
                            item["distance_m"], 3
                        ),
                        "endpoint_clearance_m": round(
                            item["endpoint_clearance_m"], 3
                        ),
                    }
                )

        for direction in ("UP", "DOWN"):
            item = selected[direction]
            edge = item["edge"]
            edge_point = edge["shape"].interpolate(item["edge_position_m"])

            group_id = f"MLIT_R3_{section}_{direction}"

            detector_ids = legacy.lane_detectors_at_point(
                registry,
                group_id,
                edge,
                edge_point,
            )

            expected_edge = EXPECTED_REPRESENTATIVE_EDGES[(section, direction)]
            if edge["id"] != expected_edge:
                raise ValueError(
                    f"representative-edge regression mismatch for "
                    f"{section} {direction}: "
                    f"selected={edge['id']} expected={expected_edge}"
                )

            legacy_reference = LEGACY_V4_REFERENCE.get((section, direction))

            count_locations.append(
                {
                    "official_observation_section_id": section,
                    "direction": direction,
                    "direction_source":
                        "CANONICAL_EXTERNAL_OBSERVATION_FINAL_INVENTORY",
                    "direction_inference_from_geometry": False,
                    "sample_fraction": selected["sample_fraction"],
                    "representative_edge_id": edge["id"],
                    "edge_position_m": round(item["edge_position_m"], 3),
                    "distance_from_official_geometry_m": round(
                        item["distance_m"], 3
                    ),
                    "endpoint_clearance_m": round(
                        item["endpoint_clearance_m"], 3
                    ),
                    "detector_group_id": group_id,
                    "detector_ids": ";".join(detector_ids),
                    "lane_aggregation_semantics":
                        "SUM_ALL_MOTORIZED_LANES_ON_REPRESENTATIVE_EDGE",
                    "cross_section_aggregation_semantics":
                        "KEEP_UP_AND_DOWN_SEPARATE",
                    "legacy_v4_reference_edge": legacy_reference or "",
                    "legacy_v4_edge_match":
                        (
                            ""
                            if legacy_reference is None
                            else str(edge["id"] == legacy_reference).lower()
                        ),
                    "selection_rule_id":
                        "CANONICAL_CORRIDOR_CROSS_SECTION_SELECTION_V1",
                    "status": "ACCEPTED",
                }
            )

    count_locations.sort(
        key=lambda row: (
            row["official_observation_section_id"],
            row["direction"],
        )
    )

    detector_rows: list[dict[str, Any]] = []

    for record in registry.records:
        groups = sorted(record["observation_groups"])

        if len(groups) != 1:
            raise ValueError(
                f"canonical detector unexpectedly shared by groups: {groups}"
            )

        group_id = groups[0]
        parts = group_id.split("_")

        section = parts[-2]
        direction = parts[-1]

        detector_rows.append(
            {
                "detector_id": record["detector_id"],
                "official_observation_section_id": section,
                "direction": direction,
                "detector_group_id": group_id,
                "edge_id": record["edge_id"],
                "lane_id": record["lane_id"],
                "position_m": record["position_m"],
                "aggregation_role":
                    "SUM_WITHIN_SECTION_DIRECTION_HOUR",
            }
        )

    detector_rows.sort(key=lambda row: row["detector_id"])

    count_csv = output / "canonical_calibration_count_locations.csv"
    lanes_csv = output / "canonical_calibration_detector_lanes.csv"
    attempts_csv = output / "canonical_calibration_count_location_attempts.csv"
    detector_xml = output / "canonical_calibration_detectors.add.xml"
    qa_json = output / "canonical_calibration_detector_qa.json"
    manifest_json = output / "canonical_calibration_detector_manifest.json"

    write_csv(count_csv, count_locations)
    write_csv(lanes_csv, detector_rows)
    write_csv(attempts_csv, selection_attempts)
    write_detector_xml(detector_xml, detector_rows)

    selected_map = {
        (
            row["official_observation_section_id"],
            row["direction"],
        ): row["representative_edge_id"]
        for row in count_locations
    }

    old_v4_match_count = sum(
        selected_map[key] == value
        for key, value in LEGACY_V4_REFERENCE.items()
    )

    qa = {
        "status": "PASSED",
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "independent_official_observation_section_count": len(EXPECTED_SECTIONS),
        "directional_count_location_count": len(count_locations),
        "detector_lane_count": len(detector_rows),
        "expected_directional_count_location_count": 6,
        "legacy_v4_reference_count": len(LEGACY_V4_REFERENCE),
        "legacy_v4_match_count": old_v4_match_count,
        "direction_policy": {
            "source": "canonical final inventory",
            "official_geometry_coordinate_order_used": False,
            "bearing_used_as_direction_evidence": False,
        },
        "selection_policy": {
            "candidate_population": "FORMALLY_ACCEPTED_DIRECTIONAL_CORRIDOR_ONLY",
            "sample_fractions": list(SAMPLE_FRACTIONS),
            "score_order": [
                "maximize minimum endpoint clearance",
                "minimize maximum official-geometry distance",
                "minimize total official-geometry distance",
                "minimize distance from fraction 0.5",
                "edge id deterministic tie-break",
            ],
        },
        "aggregation_policy": {
            "within_direction":
                "SUM_ALL_MOTORIZED_LANES_ON_REPRESENTATIVE_EDGE",
            "between_directions": "KEEP_UP_AND_DOWN_SEPARATE",
            "between_corridor_edges":
                "DO_NOT_SUM_MULTIPLE_EDGES",
            "duplicate_target_policy":
                "ONE_INDEPENDENT_OBSERVATION_SECTION_DIRECTION_HOUR",
        },
        "selected_representative_edges": {
            f"{section}:{direction}": edge
            for (section, direction), edge in sorted(selected_map.items())
        },
    }

    qa_json.write_text(
        json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    inputs = [
        INVENTORY_CSV,
        OBSERVATIONS_CSV,
        NETWORK,
        LEGACY_DETECTOR_XML,
    ]

    outputs = [
        count_csv,
        lanes_csv,
        attempts_csv,
        detector_xml,
        qa_json,
    ]

    manifest = {
        "run_id": RUN_ID,
        "generator_version": SCRIPT_VERSION,
        "input_hashes": {
            relative(path): sha256_file(path)
            for path in inputs
        },
        "output_hashes": {
            relative(path): sha256_file(path)
            for path in outputs
        },
        "non_mutation_contract": {
            "sumo_network_modified": False,
            "canonical_inventory_modified": False,
            "traffic_observations_modified": False,
            "mapping_modified": False,
            "threshold_modified": False,
        },
    }

    manifest_json.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "PASSED",
        "output_dir": str(output),
        "independent_observation_sections": 3,
        "directional_count_locations": len(count_locations),
        "detector_lanes": len(detector_rows),
        "legacy_v4_matches": old_v4_match_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove an existing output directory before rebuilding.",
    )
    args = parser.parse_args()

    output = args.output

    if output.exists() and args.replace:
        shutil.rmtree(output)

    result = build(output)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
