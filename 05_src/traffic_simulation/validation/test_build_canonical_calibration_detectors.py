import csv
import hashlib
import json
import xml.etree.ElementTree as ET

from traffic_simulation.calibration import build_canonical_calibration_detectors as subject


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_canonical_detector_set(tmp_path):
    output = tmp_path / "canonical_detectors"

    result = subject.build(output)

    assert result["status"] == "PASSED"
    assert result["independent_observation_sections"] == 3
    assert result["directional_count_locations"] == 6
    assert result["legacy_v4_matches"] == 4

    locations = read_csv(
        output / "canonical_calibration_count_locations.csv"
    )

    assert len(locations) == 6

    keys = {
        (
            row["official_observation_section_id"],
            row["direction"],
        )
        for row in locations
    }

    assert keys == set(subject.EXPECTED_REPRESENTATIVE_EDGES)

    selected = {
        (
            row["official_observation_section_id"],
            row["direction"],
        ): row["representative_edge_id"]
        for row in locations
    }

    assert selected == subject.EXPECTED_REPRESENTATIVE_EDGES


def test_direction_not_inferred_from_geometry(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    rows = read_csv(
        output / "canonical_calibration_count_locations.csv"
    )

    assert all(
        row["direction_source"]
        == "CANONICAL_EXTERNAL_OBSERVATION_FINAL_INVENTORY"
        for row in rows
    )

    assert all(
        row["direction_inference_from_geometry"] == "False"
        for row in rows
    )


def test_lane_aggregation_semantics(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    rows = read_csv(
        output / "canonical_calibration_count_locations.csv"
    )

    assert all(
        row["lane_aggregation_semantics"]
        == "SUM_ALL_MOTORIZED_LANES_ON_REPRESENTATIVE_EDGE"
        for row in rows
    )

    assert all(
        row["cross_section_aggregation_semantics"]
        == "KEEP_UP_AND_DOWN_SEPARATE"
        for row in rows
    )


def test_detector_lanes_only_reference_selected_edges(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    locations = read_csv(
        output / "canonical_calibration_count_locations.csv"
    )
    lanes = read_csv(
        output / "canonical_calibration_detector_lanes.csv"
    )

    selected = {
        (
            row["official_observation_section_id"],
            row["direction"],
        ): row["representative_edge_id"]
        for row in locations
    }

    assert lanes

    for row in lanes:
        key = (
            row["official_observation_section_id"],
            row["direction"],
        )
        assert row["edge_id"] == selected[key]


def test_detector_xml_matches_detector_lane_csv(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    lanes = read_csv(
        output / "canonical_calibration_detector_lanes.csv"
    )

    root = ET.parse(
        output / "canonical_calibration_detectors.add.xml"
    ).getroot()

    children = list(root)

    assert len(children) == len(lanes)

    xml_ids = {item.attrib["id"] for item in children}
    csv_ids = {row["detector_id"] for row in lanes}

    assert xml_ids == csv_ids


def test_qa_policy(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    qa = json.loads(
        (
            output
            / "canonical_calibration_detector_qa.json"
        ).read_text(encoding="utf-8")
    )

    assert qa["status"] == "PASSED"
    assert qa["independent_official_observation_section_count"] == 3
    assert qa["directional_count_location_count"] == 6

    assert (
        qa["direction_policy"][
            "official_geometry_coordinate_order_used"
        ]
        is False
    )

    assert (
        qa["aggregation_policy"]["between_corridor_edges"]
        == "DO_NOT_SUM_MULTIPLE_EDGES"
    )


def test_manifest_hashes(tmp_path):
    output = tmp_path / "canonical_detectors"

    subject.build(output)

    manifest = json.loads(
        (
            output
            / "canonical_calibration_detector_manifest.json"
        ).read_text(encoding="utf-8")
    )

    for relative, expected in manifest["input_hashes"].items():
        path = subject.REPOSITORY_ROOT / relative
        assert path.is_file()
        assert sha256_file(path) == expected

    for relative, expected in manifest["output_hashes"].items():
        path = subject.REPOSITORY_ROOT / relative
        if not path.is_file():
            # tmp_path outputs are outside repository; use filename under tmp.
            path = output / relative.split("/")[-1]
        assert path.is_file()
        assert sha256_file(path) == expected

    assert not any(
        manifest["non_mutation_contract"].values()
    )
