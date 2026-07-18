"""Tests for governed population-mesh and synthetic-demand preparation."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from decimal import Decimal
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from pyproj import CRS
from shapely.geometry import Polygon

from traffic_simulation.demand import prepare_baseline_demand as baseline
from traffic_simulation.network.study_areas import REGISTRY_FIELDS, StudyArea


def synthetic_area() -> StudyArea:
    first = baseline.mesh_500m_polygon("533935991")
    second = baseline.mesh_500m_polygon("533935992")
    west, south, _, north = first.bounds
    _, _, second_east, _ = second.bounds
    second_west = second.bounds[0]
    boundary = Polygon(
        [
            (west, south),
            ((second_west + second_east) / 2, south),
            ((second_west + second_east) / 2, north),
            (west, north),
            (west, south),
        ]
    )
    source_crs = CRS.from_epsg(6668)
    metric_crs = CRS.from_epsg(6677)
    metric_boundary = gpd.GeoSeries([boundary], crs=source_crs).to_crs(metric_crs).iloc[0]
    return StudyArea(
        region_id="ota_ward",
        version=1,
        name_ja="試験境界",
        source_registry_id="boundary",
        source_crs=source_crs,
        api_crs=source_crs,
        metric_crs=metric_crs,
        source_boundary=boundary,
        api_boundary=boundary,
        metric_boundary=metric_boundary,
        acquisition_bbox=tuple(boundary.bounds),
        source_feature_count=1,
        raw_sha256="a" * 64,
    )


def test_repository_config_is_strict_and_contains_no_absolute_path() -> None:
    config = baseline.load_config()

    assert config.region_id == "ota_ward"
    assert config.target_days == 1
    assert config.population["mesh_crs"] == "EPSG:6668"
    assert config.demand_proxy["annual_parcel_count"] == 5_031_470_000
    serialized = json.dumps(
        {
            "population": config.population,
            "demand_proxy": config.demand_proxy,
            "outputs": config.outputs,
        },
        ensure_ascii=False,
    )
    assert "/Users/" not in serialized


def test_mesh_code_decoding_creates_adjacent_half_meshes() -> None:
    west = baseline.mesh_500m_polygon("533935991")
    east = baseline.mesh_500m_polygon("533935992")

    assert west.is_valid and east.is_valid
    assert west.bounds[2] == pytest.approx(east.bounds[0])
    assert west.bounds[1] == pytest.approx(east.bounds[1])
    assert west.bounds[3] == pytest.approx(east.bounds[3])
    assert west.bounds[2] - west.bounds[0] == pytest.approx(1 / 160)
    assert west.bounds[3] - west.bounds[1] == pytest.approx(1 / 240)


@pytest.mark.parametrize("mesh_code", ["", "53393599", "533935990", "533985991"])
def test_invalid_mesh_codes_are_rejected(mesh_code: str) -> None:
    with pytest.raises(ValueError, match="mesh code|subdivision"):
        baseline.mesh_500m_polygon(mesh_code)


def test_largest_remainder_uses_key_order_for_equal_remainders() -> None:
    result = baseline.largest_remainder(
        [Decimal("1.4"), Decimal("1.4"), Decimal("1.2")],
        total=4,
        keys=["b", "a", "c"],
    )

    assert result == [1, 2, 1]
    assert sum(result) == 4


def population_zip(path: Path, *, member: str = "official.txt") -> None:
    payload = (
        "KEY_CODE,T001141001\n"
        ",人口総数\n"
        "533935991,100\n"
        "533935992,100\n"
    ).encode("cp932")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(".nfs-test", b"must not be selected")
        archive.writestr(member, payload)


def test_population_zip_reads_only_the_configured_member(tmp_path: Path) -> None:
    path = tmp_path / "mesh.zip"
    population_zip(path)

    frame, members = baseline.read_population_mesh(
        path,
        member="official.txt",
        encoding="cp932",
        mesh_code_column="KEY_CODE",
        population_column="T001141001",
    )

    assert members == [".nfs-test", "official.txt"]
    assert list(frame["mesh_code"]) == ["533935991", "533935992"]
    assert list(frame["census_population_2020"]) == [100, 100]


def test_population_zip_requires_exact_member(tmp_path: Path) -> None:
    path = tmp_path / "mesh.zip"
    population_zip(path, member="wrong.txt")

    with pytest.raises(ValueError, match="configured mesh member"):
        baseline.read_population_mesh(
            path,
            member="official.txt",
            encoding="cp932",
            mesh_code_column="KEY_CODE",
            population_column="T001141001",
        )


def test_boundary_weighting_rescaling_and_demand_preserve_totals() -> None:
    mesh = pd.DataFrame(
        {
            "mesh_code": ["533935991", "533935992"],
            "census_population_2020": [100, 100],
        }
    )

    frame, summary = baseline.build_population_and_demand(
        mesh,
        area=synthetic_area(),
        target_population=100,
        q_base=Decimal("0.1"),
        target_days=1,
        mesh_crs="EPSG:6668",
    )

    rows = frame.set_index("mesh_code")
    assert len(frame) == 2
    assert summary["full_mesh_count"] == 1
    assert summary["partial_boundary_mesh_count"] == 1
    assert rows.loc["533935991", "boundary_overlap_ratio"] == pytest.approx(1.0)
    assert rows.loc["533935992", "boundary_overlap_ratio"] == pytest.approx(0.5, abs=1e-5)
    assert rows.loc["533935991", "population_2024"] == 67
    assert rows.loc["533935992", "population_2024"] == 33
    assert int(frame["population_2024"].sum()) == 100
    assert int(frame["demand_parcel_equivalent"].sum()) == 10
    assert summary["allocated_demand_parcel_equivalent"] == 10


def registry_row(path: Path, sha256: str) -> dict[str, str]:
    row = {field: "" for field in REGISTRY_FIELDS}
    row.update(
        {
            "source_id": "source",
            "dataset_name": "source",
            "provider": "provider",
            "source_url": "https://example.invalid/source",
            "downloaded_at": "2026-07-18",
            "observation_start": "2020-10-01",
            "observation_end": "2020-10-01",
            "geographic_scope": "test",
            "license_or_terms": "test",
            "original_filename": path.name,
            "local_raw_path": str(path),
            "sha256": sha256,
            "status": "raw_acquired",
        }
    )
    return row


def test_source_hash_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw" / "source.bin"
    raw.parent.mkdir()
    raw.write_bytes(b"source")
    registry = tmp_path / "registry.csv"
    row = registry_row(Path("raw/source.bin"), "a" * 64)
    with registry.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    monkeypatch.setattr(baseline, "REPOSITORY_ROOT", tmp_path)

    with pytest.raises(ValueError, match="SHA-256 hash mismatch"):
        baseline.verify_source("source", registry)


def test_distributor_filename_may_differ_from_local_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw" / "locally_named.bin"
    raw.parent.mkdir()
    raw.write_bytes(b"source")
    registry = tmp_path / "registry.csv"
    row = registry_row(
        Path("raw/locally_named.bin"), hashlib.sha256(raw.read_bytes()).hexdigest()
    )
    row["original_filename"] = "distributor_name.bin"
    with registry.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    monkeypatch.setattr(baseline, "REPOSITORY_ROOT", tmp_path)

    resolved, digest = baseline.verify_source("source", registry)

    assert resolved == raw
    assert digest == row["sha256"]


def test_outputs_are_atomic_and_not_overwritten(tmp_path: Path) -> None:
    mesh = pd.DataFrame(
        {
            "mesh_code": ["533935991", "533935992"],
            "census_population_2020": [100, 100],
        }
    )
    frame, summary = baseline.build_population_and_demand(
        mesh,
        area=synthetic_area(),
        target_population=100,
        q_base=Decimal("0.1"),
        target_days=1,
        mesh_crs="EPSG:6668",
    )
    parquet = tmp_path / "demand.parquet"
    quality = tmp_path / "quality.json"

    written = baseline.write_outputs(
        frame,
        summary,
        parquet_path=parquet,
        summary_path=quality,
    )

    assert parquet.exists() and quality.exists()
    assert written["population_and_demand_sha256"] == hashlib.sha256(
        parquet.read_bytes()
    ).hexdigest()
    assert not list(tmp_path.glob("*.part"))
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        baseline.write_outputs(
            frame,
            summary,
            parquet_path=parquet,
            summary_path=quality,
        )
