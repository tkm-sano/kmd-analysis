"""Tests for population and synthetic-demand map layers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import folium
import geopandas as gpd
import pytest
from shapely.geometry import box

from traffic_simulation.visualization import render_study_area as render


def demand_frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "region_id": ["ota_ward", "ota_ward"],
            "mesh_code": ["533935991", "533935992"],
            "census_population_2020": [100, 200],
            "boundary_overlap_ratio": [1.0, 0.5],
            "boundary_class": ["full", "partial"],
            "population_2024": [120, 240],
            "demand_parcel_equivalent": [13, 27],
        },
        geometry=[box(139.70, 35.55, 139.71, 35.56), box(139.71, 35.55, 139.72, 35.56)],
        crs="EPSG:4326",
    )


def demand_data() -> render.BaselineDemandData:
    return render.BaselineDemandData(
        frame=demand_frame(),
        path=Path("demand.parquet"),
        sha256="a" * 64,
        q_base="0.111345933951539499",
        population_total=360,
        demand_total=40,
        partial_boundary_mesh_count=1,
    )


def test_demand_layers_render_switchable_population_and_demand() -> None:
    map_object = folium.Map(location=(35.55, 139.70))

    render.add_baseline_demand_layers(map_object, demand_data())
    folium.LayerControl(collapsed=False).add_to(map_object)
    rendered = map_object.get_root().render()

    expected_labels = (
        "2024年推定人口（500メートル、2件）",
        "1日当たり合成配送需要（500メートル、2件）",
        "1日当たり配送需要相当",
    )
    for label in expected_labels:
        escaped = json.dumps(label, ensure_ascii=True)[1:-1]
        assert escaped in rendered
    assert "533935991" in rendered


def test_display_breaks_and_colors_are_deterministic() -> None:
    breaks = render._quantile_breaks(demand_frame()["population_2024"])

    assert len(breaks) == 5
    assert render._palette_color(0, breaks) == render.DEMAND_PALETTE[0]
    assert render._palette_color(10_000, breaks) == render.DEMAND_PALETTE[-1]


def write_governed_outputs(tmp_path: Path) -> tuple[Path, Path, str]:
    parquet = tmp_path / "demand.parquet"
    summary = tmp_path / "quality.json"
    demand_frame().to_parquet(parquet, index=False)
    digest = render.sha256_file(parquet)
    summary.write_text(
        json.dumps(
            {
                "region_id": "ota_ward",
                "config_sha256": "c" * 64,
                "population_and_demand_sha256": digest,
                "intersecting_mesh_count": 2,
                "allocated_population_2024": 360,
                "allocated_demand_parcel_equivalent": 40,
                "partial_boundary_mesh_count": 1,
                "q_base": "0.111345933951539499",
            }
        ),
        encoding="utf-8",
    )
    return parquet, summary, digest


def test_load_baseline_demand_verifies_governed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parquet, summary, digest = write_governed_outputs(tmp_path)
    config = SimpleNamespace(region_id="ota_ward", config_sha256="c" * 64)
    monkeypatch.setattr(render, "load_baseline_demand_config", lambda: config)
    monkeypatch.setattr(
        render, "baseline_demand_output_paths", lambda _: (parquet, summary)
    )

    result = render.load_baseline_demand("ota_ward")

    assert result.sha256 == digest
    assert result.population_total == 360
    assert result.demand_total == 40


def test_load_baseline_demand_rejects_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parquet, summary, _ = write_governed_outputs(tmp_path)
    document = json.loads(summary.read_text(encoding="utf-8"))
    document["population_and_demand_sha256"] = "0" * 64
    summary.write_text(json.dumps(document), encoding="utf-8")
    config = SimpleNamespace(region_id="ota_ward", config_sha256="c" * 64)
    monkeypatch.setattr(render, "load_baseline_demand_config", lambda: config)
    monkeypatch.setattr(
        render, "baseline_demand_output_paths", lambda _: (parquet, summary)
    )

    with pytest.raises(ValueError, match="metadata mismatch"):
        render.load_baseline_demand("ota_ward")
