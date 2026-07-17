"""Acceptance tests for governed JARTIC observation preparation.

These tests intentionally skip as a module until ``prepare_jartic.py`` exists.
Once it is implemented, they define the required normalization, quality, and
provenance behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

try:
    from traffic_simulation.calibration import prepare_jartic
except ImportError:
    pytest.skip(
        "prepare_jartic.py has not been implemented yet",
        allow_module_level=True,
    )

from traffic_simulation.calibration.fetch_jartic import REGISTRY_FIELDS


SOURCE_ID = "jartic_1h_road3_tokyo_202607042200"
RAW_SHA256 = "a" * 64


def make_feature(
    *,
    feature_id: str = "t_travospublic_measure_1h.14416623",
    observation_code: int = 3110010,
    coordinates: list[list[float]] | None = None,
    overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    properties: dict[str, object] = {
        "常時観測点コード": observation_code,
        "収集時間フラグ（5分間／1時間）": "2",
        "観測年月日": 20260704,
        "時間帯": 2200,
        "時間コード": 202607042200,
        "道路種別": "3",
        "上り・小型交通量": 409,
        "上り・大型交通量": 16,
        "上り・車種判別不能交通量": 55,
        "上り・停電": "0",
        "上り・ループ異常": "0",
        "上り・超音波異常": "0",
        "上り・欠測": "0",
        "下り・小型交通量": 481,
        "下り・大型交通量": 19,
        "下り・車種判別不能交通量": 82,
        "下り・停電": "0",
        "下り・ループ異常": "0",
        "下り・超音波異常": "0",
        "下り・欠測": "0",
    }
    properties.update(overrides or {})
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "MultiPoint",
            "coordinates": coordinates or [[139.7049058, 35.58550262]],
        },
        "properties": properties,
    }


def make_payload(*features: dict[str, object]) -> dict[str, object]:
    selected = list(features) or [make_feature()]
    return {
        "type": "FeatureCollection",
        "features": selected,
        "numberReturned": len(selected),
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"},
        },
    }


def normalize(payload: dict[str, object] | None = None):
    return prepare_jartic.normalize_payload(
        payload or make_payload(),
        source_id=SOURCE_ID,
        layer="1h",
    )


def test_one_observation_becomes_two_measured_direction_rows() -> None:
    observations = normalize()

    assert len(observations) == 2
    assert set(observations["jartic_direction"]) == {"up", "down"}
    assert set(observations["direction_status"]) == {"unresolved"}
    assert observations["sumo_edge_id"].isna().all()
    assert observations["sumo_direction"].isna().all()
    assert observations.crs.to_epsg() == 4326

    by_direction = observations.set_index("jartic_direction")
    assert by_direction.loc["up", "small_volume"] == 409
    assert by_direction.loc["up", "large_volume"] == 16
    assert by_direction.loc["up", "unknown_volume"] == 55
    assert by_direction.loc["up", "total_volume"] == 480
    assert by_direction.loc["down", "small_volume"] == 481
    assert by_direction.loc["down", "large_volume"] == 19
    assert by_direction.loc["down", "unknown_volume"] == 82
    assert by_direction.loc["down", "total_volume"] == 582


def test_missing_volume_is_not_converted_to_zero() -> None:
    payload = make_payload(
        make_feature(
            overrides={
                "上り・大型交通量": None,
                "上り・欠測": "1",
            }
        )
    )

    up = normalize(payload).set_index("jartic_direction").loc["up"]

    assert pd.isna(up["large_volume"])
    assert pd.isna(up["total_volume"])
    assert bool(up["missing"]) is True
    assert bool(up["valid_measurement"]) is False
    assert "missing" in up["invalid_reasons"]


def test_sensor_anomaly_invalidates_only_its_measured_direction() -> None:
    payload = make_payload(
        make_feature(
            overrides={
                "下り・ループ異常": "1",
                "下り・超音波異常": "1",
            }
        )
    )

    rows = normalize(payload).set_index("jartic_direction")

    assert bool(rows.loc["up", "valid_measurement"]) is True
    assert bool(rows.loc["down", "valid_measurement"]) is False
    assert "loop_error" in rows.loc["down", "invalid_reasons"]
    assert "ultrasonic_error" in rows.loc["down", "invalid_reasons"]


def test_real_zero_volume_remains_a_valid_measurement() -> None:
    zero_fields = {
        "上り・小型交通量": 0,
        "上り・大型交通量": 0,
        "上り・車種判別不能交通量": 0,
    }

    up = normalize(make_payload(make_feature(overrides=zero_fields))).set_index(
        "jartic_direction"
    ).loc["up"]

    assert up["total_volume"] == 0
    assert bool(up["valid_measurement"]) is True


def test_duplicate_observation_time_direction_keys_are_rejected() -> None:
    duplicate = make_feature(feature_id="duplicate")

    with pytest.raises(ValueError, match="duplicate"):
        normalize(make_payload(make_feature(), duplicate))


@pytest.mark.parametrize(
    "coordinates",
    [
        [],
        [[181.0, 35.5]],
        [[139.7, 91.0]],
    ],
)
def test_invalid_geometry_is_rejected(coordinates: list[list[float]]) -> None:
    feature = make_feature()
    feature["geometry"] = {"type": "MultiPoint", "coordinates": coordinates}

    with pytest.raises(ValueError, match="geometry|coordinate"):
        normalize(make_payload(feature))


def test_quality_summary_counts_valid_and_invalid_rows() -> None:
    payload = make_payload(
        make_feature(overrides={"下り・欠測": "1", "下り・小型交通量": None})
    )
    observations = normalize(payload)

    summary = prepare_jartic.build_quality_summary(
        observations,
        source_id=SOURCE_ID,
        raw_sha256=RAW_SHA256,
    )

    assert summary["source_id"] == SOURCE_ID
    assert summary["raw_sha256"] == RAW_SHA256
    assert summary["normalized_row_count"] == 2
    assert summary["valid_row_count"] == 1
    assert summary["invalid_row_count"] == 1
    assert summary["observation_code_count"] == 1


def test_raw_sha256_mismatch_is_rejected(tmp_path: Path) -> None:
    raw_path = tmp_path / "snapshot.geojson"
    raw_path.write_text(
        json.dumps(make_payload(), ensure_ascii=False),
        encoding="utf-8",
    )
    actual = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    assert actual != RAW_SHA256
    with pytest.raises(ValueError, match="SHA-256|hash"):
        prepare_jartic.verify_raw_source(raw_path, RAW_SHA256)


def test_outputs_are_not_overwritten(tmp_path: Path) -> None:
    observations = normalize()
    summary = prepare_jartic.build_quality_summary(
        observations,
        source_id=SOURCE_ID,
        raw_sha256=RAW_SHA256,
    )
    parquet_path = tmp_path / "observations.parquet"
    summary_path = tmp_path / "quality_summary.json"

    prepare_jartic.write_outputs(
        observations,
        summary,
        observations_path=parquet_path,
        summary_path=summary_path,
    )

    assert parquet_path.exists()
    assert summary_path.exists()
    assert not list(tmp_path.glob("*.part"))
    with pytest.raises(FileExistsError):
        prepare_jartic.write_outputs(
            observations,
            summary,
            observations_path=parquet_path,
            summary_path=summary_path,
        )


def make_registry_row() -> dict[str, str]:
    row = {field: "" for field in REGISTRY_FIELDS}
    row.update(
        {
            "source_id": SOURCE_ID,
            "downloaded_at": "2026-07-17",
            "sha256": RAW_SHA256,
            "processing_script": (
                "05_src/traffic_simulation/calibration/fetch_jartic.py"
            ),
            "status": "raw_acquired",
        }
    )
    return row


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_mark_source_processed_is_idempotent_and_preserves_acquisition_script(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "sources.csv"
    write_registry(registry, [make_registry_row()])
    outputs = [
        "03_data/processed/traffic_simulation/calibration/observations.parquet",
        "03_data/processed/traffic_simulation/calibration/quality_summary.json",
    ]

    for _ in range(2):
        prepare_jartic.mark_source_processed(
            registry,
            source_id=SOURCE_ID,
            processed_outputs=outputs,
        )

    rows = read_registry(registry)
    assert len(rows) == 1
    assert rows[0]["status"] == "processed"
    assert "fetch_jartic.py" in rows[0]["processing_script"]
    assert "prepare_jartic.py" in rows[0]["processing_script"]
    assert rows[0]["processing_script"].count("prepare_jartic.py") == 1
    assert rows[0]["processed_outputs"] == ";".join(outputs)
