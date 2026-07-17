"""Tests for governed administrative study-area loading and materialization."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import geopandas as gpd
import pytest
import yaml
from shapely.geometry import Polygon, mapping

from traffic_simulation.network import study_areas


SOURCE_ID = "mlit_n03_2026_tokyo"
RAW_RELATIVE_PATH = (
    "03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip"
)


def area_configuration() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_areas": {
            "ota_ward": {
                "version": 1,
                "status": "active",
                "name_ja": "東京都大田区行政区域",
                "geometry_type": "administrative_boundary",
                "boundary_source": {
                    "dataset": "MLIT_N03",
                    "source_registry_id": SOURCE_ID,
                    "code_field": "N03_007",
                    "code_value": "13111",
                    "prefecture_field": "N03_001",
                    "prefecture_value": "東京都",
                    "municipality_field": "N03_004",
                    "municipality_value": "大田区",
                },
                "api_crs": "EPSG:4326",
                "metric_crs": "EPSG:6677",
                "acquisition_extent_method": "boundary_envelope",
                "network_clip_method": "intersects_boundary",
                "intended_uses": [
                    "osm_acquisition",
                    "sumo_network_validation",
                    "jartic_edge_mapping",
                ],
            }
        },
    }


def write_configuration(path: Path, document: dict[str, object] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            document or area_configuration(),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def n03_feature(
    index: int,
    *,
    code: str = "13111",
    prefecture: str = "東京都",
    municipality: str = "大田区",
) -> dict[str, object]:
    west = 139.66 + index * 0.01
    south = 35.55 + (index % 2) * 0.01
    geometry = Polygon(
        [
            (west, south),
            (west + 0.008, south),
            (west + 0.008, south + 0.008),
            (west, south + 0.008),
            (west, south),
        ]
    )
    return {
        "type": "Feature",
        "properties": {
            "N03_001": prefecture,
            "N03_002": None,
            "N03_003": None,
            "N03_004": municipality,
            "N03_005": None,
            "N03_007": code,
        },
        "geometry": mapping(geometry),
    }


def write_n03_zip(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    features = [n03_feature(index) for index in range(6)]
    # Each near-match fails a different part of the three-condition selection.
    features.extend(
        [
            n03_feature(10, code="13112"),
            n03_feature(11, prefecture="神奈川県"),
            n03_feature(12, municipality="世田谷区"),
        ]
    )
    payload = {
        "type": "FeatureCollection",
        "name": "N03-20260101_13",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::6668"},
        },
        "features": features,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "N03-20260101_13.geojson",
            json.dumps(payload, ensure_ascii=False),
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_row(sha256: str) -> dict[str, str]:
    row = {field: "" for field in study_areas.REGISTRY_FIELDS}
    row.update(
        {
            "source_id": SOURCE_ID,
            "dataset_name": "国土数値情報N03行政区域データ2026年東京都版",
            "provider": "国土交通省",
            "source_url": "https://example.invalid/n03",
            "downloaded_at": "2026-07-17",
            "observation_start": "2026-01-01",
            "observation_end": "2026-01-01",
            "geographic_scope": "東京都",
            "license_or_terms": "CC BY 4.0",
            "original_filename": "N03-20260101_13_GML.zip",
            "local_raw_path": RAW_RELATIVE_PATH,
            "sha256": sha256,
            "status": "raw_acquired",
        }
    )
    return row


def write_registry(path: Path, row: dict[str, str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=study_areas.REGISTRY_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(row)
    return path


@pytest.fixture
def governed_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    monkeypatch.setattr(study_areas, "REPOSITORY_ROOT", tmp_path)
    raw_path = tmp_path / RAW_RELATIVE_PATH
    raw_sha256 = write_n03_zip(raw_path)
    config_path = write_configuration(tmp_path / "study_areas.yml")
    registry_path = write_registry(tmp_path / "registry.csv", registry_row(raw_sha256))
    return {
        "raw": raw_path,
        "config": config_path,
        "registry": registry_path,
    }


def test_repository_configuration_contains_no_bbox_or_absolute_path() -> None:
    configurations = study_areas.load_config()

    assert "ota_ward" in configurations
    area = configurations["ota_ward"]
    serialized = json.dumps(area, ensure_ascii=False, default=dict)
    assert "bbox" not in serialized.lower()
    assert "/Users/" not in serialized
    assert area["boundary_source"]["source_registry_id"] == SOURCE_ID


def test_loads_and_dissolves_only_three_condition_matches(
    governed_inputs: dict[str, Path],
) -> None:
    area = study_areas.load_study_area(
        "ota_ward",
        config_path=governed_inputs["config"],
        registry_path=governed_inputs["registry"],
    )

    assert area.region_id == "ota_ward"
    assert area.source_feature_count == 6
    assert area.source_crs.to_epsg() == 6668
    assert area.api_crs.to_epsg() == 4326
    assert area.metric_crs.to_epsg() == 6677
    assert area.source_boundary.geom_type == "MultiPolygon"
    assert area.source_boundary.is_valid
    assert area.api_boundary.is_valid
    assert area.metric_boundary.is_valid
    assert area.metric_boundary.area > 0


def test_bbox_is_derived_from_and_contains_the_api_boundary(
    governed_inputs: dict[str, Path],
) -> None:
    area = study_areas.load_study_area(
        "ota_ward",
        config_path=governed_inputs["config"],
        registry_path=governed_inputs["registry"],
    )

    assert area.acquisition_bbox == tuple(area.api_boundary.bounds)
    west, south, east, north = area.acquisition_bbox
    assert -180 <= west < east <= 180
    assert -90 <= south < north <= 90
    assert area.api_boundary.envelope.covers(area.api_boundary)


def test_study_area_is_frozen(governed_inputs: dict[str, Path]) -> None:
    area = study_areas.load_study_area(
        "ota_ward",
        config_path=governed_inputs["config"],
        registry_path=governed_inputs["registry"],
    )

    with pytest.raises(FrozenInstanceError):
        area.version = 2  # type: ignore[misc]


def test_unknown_and_inactive_regions_are_rejected(
    governed_inputs: dict[str, Path],
) -> None:
    with pytest.raises(ValueError, match="unknown study area"):
        study_areas.load_study_area(
            "unknown",
            config_path=governed_inputs["config"],
            registry_path=governed_inputs["registry"],
        )

    document = area_configuration()
    document["study_areas"]["ota_ward"]["status"] = "retired"  # type: ignore[index]
    write_configuration(governed_inputs["config"], document)
    with pytest.raises(ValueError, match="not active"):
        study_areas.load_study_area(
            "ota_ward",
            config_path=governed_inputs["config"],
            registry_path=governed_inputs["registry"],
        )


def test_sha256_mismatch_is_rejected(governed_inputs: dict[str, Path]) -> None:
    bad_row = registry_row("a" * 64)
    write_registry(governed_inputs["registry"], bad_row)

    with pytest.raises(ValueError, match="SHA-256 hash mismatch"):
        study_areas.load_study_area(
            "ota_ward",
            config_path=governed_inputs["config"],
            registry_path=governed_inputs["registry"],
        )


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("status", "unknown", "status"),
        ("api_crs", "EPSG:6677", "api_crs"),
        ("metric_crs", "EPSG:4326", "metric_crs"),
        ("name_ja", "/Users/example/secret", "absolute path"),
    ],
)
def test_invalid_area_configuration_is_rejected(
    tmp_path: Path, key: str, value: str, message: str
) -> None:
    document = area_configuration()
    document["study_areas"]["ota_ward"][key] = value  # type: ignore[index]
    path = write_configuration(tmp_path / "study_areas.yml", document)

    with pytest.raises(ValueError, match=message):
        study_areas.load_config(path)


def test_unknown_configuration_field_is_rejected(tmp_path: Path) -> None:
    document = area_configuration()
    document["study_areas"]["ota_ward"]["bbox"] = [0, 0, 1, 1]  # type: ignore[index]
    path = write_configuration(tmp_path / "study_areas.yml", document)

    with pytest.raises(ValueError, match="unknown fields"):
        study_areas.load_config(path)


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "study_areas.yml"
    path.write_text(
        "schema_version: 1\nschema_version: 1\nstudy_areas: {}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate YAML key"):
        study_areas.load_config(path)


def test_unsupported_schema_version_is_rejected(tmp_path: Path) -> None:
    document = area_configuration()
    document["schema_version"] = 2
    path = write_configuration(tmp_path / "study_areas.yml", document)

    with pytest.raises(ValueError, match="unsupported schema_version"):
        study_areas.load_config(path)


@pytest.mark.parametrize(
    "bounds",
    [
        (140.0, 35.0, 139.0, 36.0),
        (139.0, 36.0, 140.0, 35.0),
        (-181.0, 35.0, 140.0, 36.0),
        (139.0, -91.0, 140.0, 36.0),
    ],
)
def test_invalid_bbox_is_rejected(bounds: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValueError, match="bounds"):
        study_areas._validate_bbox(bounds)


def test_writes_source_crs_boundary_and_refuses_overwrite(
    governed_inputs: dict[str, Path], tmp_path: Path
) -> None:
    area = study_areas.load_study_area(
        "ota_ward",
        config_path=governed_inputs["config"],
        registry_path=governed_inputs["registry"],
    )
    summary = study_areas.build_quality_summary(area)
    boundary_path = tmp_path / "outputs" / "boundary.parquet"
    summary_path = tmp_path / "outputs" / "summary.json"

    study_areas.write_outputs(
        area,
        summary,
        boundary_path=boundary_path,
        summary_path=summary_path,
    )

    boundary = gpd.read_parquet(boundary_path)
    written_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(boundary) == 1
    assert boundary.crs.to_epsg() == 6668
    assert boundary.geometry.iloc[0].is_valid
    assert written_summary["source_feature_count"] == 6
    assert written_summary["output_feature_count"] == 1
    assert written_summary["boundary_sha256"] == hashlib.sha256(
        boundary_path.read_bytes()
    ).hexdigest()
    assert not list(boundary_path.parent.glob("*.part"))

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        study_areas.write_outputs(
            area,
            summary,
            boundary_path=boundary_path,
            summary_path=summary_path,
        )
