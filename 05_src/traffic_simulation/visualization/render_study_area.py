"""Render a governed study area, acquisition BBOX, and optional JARTIC sites."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

import folium
import geopandas as gpd
import pandas as pd
from branca.element import Element
from shapely.geometry import MultiPoint, Point, mapping

from traffic_simulation.network.study_areas import StudyArea, load_study_area
from traffic_simulation.paths import REPOSITORY_ROOT, RUN_OUTPUT_ROOT


DEFAULT_OUTPUT_DIRECTORY: Final = RUN_OUTPUT_ROOT / "visualization"
BOUNDARY_COLOR: Final = "#1565c0"
BBOX_COLOR: Final = "#d32f2f"
VALID_COLOR: Final = "#2e7d32"
MIXED_COLOR: Final = "#ef6c00"
INVALID_COLOR: Final = "#c62828"


def resolve_repository_path(value: str, *, label: str) -> Path:
    """Resolve a repository-relative CLI path without accepting host paths."""

    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be repository-relative")
    resolved = (REPOSITORY_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    return resolved


def _feature(geometry: Any, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(geometry),
    }


def _summary_panel(area: StudyArea) -> Element:
    west, south, east, north = area.acquisition_bbox
    content = f"""
    <div style="position: fixed; top: 10px; right: 10px; z-index: 9999;
                background: rgba(255,255,255,0.94); border: 1px solid #555;
                border-radius: 4px; padding: 10px; font: 12px sans-serif;
                max-width: 390px;">
      <div style="font-weight: bold; margin-bottom: 5px;">Study area review</div>
      <div>Region: {html.escape(area.region_id)}</div>
      <div>Name: {html.escape(area.name_ja)}</div>
      <div>Version: {area.version}</div>
      <div>Source: {html.escape(area.source_registry_id)}</div>
      <div>Source CRS: {html.escape(area.source_crs.to_string())}</div>
      <div>API CRS: {html.escape(area.api_crs.to_string())}</div>
      <div>Metric CRS: {html.escape(area.metric_crs.to_string())}</div>
      <div>Source features: {area.source_feature_count}</div>
      <div>Area: {area.metric_boundary.area / 1_000_000:.6f} km²</div>
      <div>BBOX: {west:.9f}, {south:.9f}, {east:.9f}, {north:.9f}</div>
      <div style="margin-top: 5px;">Raw SHA-256:<br>
        <span style="font-family: monospace; overflow-wrap: anywhere;">
          {html.escape(area.raw_sha256)}
        </span>
      </div>
    </div>
    """
    return Element(content)


def _legend() -> Element:
    content = f"""
    <div style="position: fixed; bottom: 25px; left: 10px; z-index: 9999;
                background: rgba(255,255,255,0.94); border: 1px solid #555;
                border-radius: 4px; padding: 9px; font: 12px sans-serif;">
      <div style="font-weight: bold; margin-bottom: 4px;">Legend</div>
      <div><span style="color:{BOUNDARY_COLOR};">━</span> N03 boundary</div>
      <div><span style="color:{BBOX_COLOR};">┄</span> acquisition BBOX</div>
      <div><span style="color:{VALID_COLOR};">●</span> all measurements valid</div>
      <div><span style="color:{MIXED_COLOR};">●</span> mixed validity</div>
      <div><span style="color:{INVALID_COLOR};">●</span> all measurements invalid</div>
      <div>Black ring: outside administrative boundary</div>
    </div>
    """
    return Element(content)


def add_boundary_layers(map_object: folium.Map, area: StudyArea) -> None:
    """Add the authoritative polygon and its mechanically derived envelope."""

    boundary_feature = _feature(
        area.api_boundary,
        {
            "region_id": area.region_id,
            "name_ja": area.name_ja,
            "version": area.version,
            "source_registry_id": area.source_registry_id,
            "role": "analysis_boundary",
        },
    )
    folium.GeoJson(
        boundary_feature,
        name="N03 administrative boundary",
        style_function=lambda _: {
            "color": BOUNDARY_COLOR,
            "weight": 3,
            "fillColor": BOUNDARY_COLOR,
            "fillOpacity": 0.12,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name_ja", "region_id", "role"],
            aliases=["Name", "Region", "Role"],
            localize=True,
        ),
        show=True,
    ).add_to(map_object)

    bbox_feature = _feature(
        area.api_boundary.envelope,
        {
            "region_id": area.region_id,
            "role": "acquisition_bbox_only",
        },
    )
    folium.GeoJson(
        bbox_feature,
        name="Mechanically derived acquisition BBOX",
        style_function=lambda _: {
            "color": BBOX_COLOR,
            "weight": 2,
            "dashArray": "7 5",
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["region_id", "role"],
            aliases=["Region", "Role"],
        ),
        show=True,
    ).add_to(map_object)


def read_jartic_observations(path: Path) -> gpd.GeoDataFrame:
    """Read and validate a normalized JARTIC observation GeoParquet."""

    if not path.is_file():
        raise FileNotFoundError(f"JARTIC observations do not exist: {path}")
    observations = gpd.read_parquet(path)
    if observations.empty:
        raise ValueError(f"JARTIC observations are empty: {path}")
    if observations.crs is None:
        raise ValueError(f"JARTIC observations lack a CRS: {path}")
    required = {"source_id", "observation_code", "valid_measurement", "geometry"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"JARTIC observations lack columns: {sorted(missing)}")
    unexpected = ~observations.geometry.geom_type.isin(["Point", "MultiPoint"])
    if unexpected.any():
        types = sorted(observations.loc[unexpected].geometry.geom_type.unique())
        raise ValueError(f"JARTIC observations contain unsupported geometry: {types}")
    return observations.to_crs("EPSG:4326")


def _points(geometry: Point | MultiPoint) -> Iterable[Point]:
    if isinstance(geometry, Point):
        yield geometry
    elif isinstance(geometry, MultiPoint):
        yield from geometry.geoms
    else:  # Guarded by read_jartic_observations and retained for direct callers.
        raise ValueError(f"unsupported JARTIC geometry: {geometry.geom_type}")


def _validity(values: pd.Series) -> tuple[str, int, int]:
    valid = values.fillna(False).astype(bool)
    valid_count = int(valid.sum())
    total_count = int(len(valid))
    if valid_count == total_count:
        return VALID_COLOR, valid_count, total_count
    if valid_count == 0:
        return INVALID_COLOR, valid_count, total_count
    return MIXED_COLOR, valid_count, total_count


def add_jartic_layer(
    map_object: folium.Map,
    area: StudyArea,
    observations: gpd.GeoDataFrame,
    *,
    source_label: str,
) -> int:
    """Add de-duplicated observation locations colored by measurement validity."""

    layer = folium.FeatureGroup(name=f"JARTIC: {source_label}", show=True)
    marker_count = 0
    group_columns = ["source_id", "observation_code"]
    for (source_id, observation_code), rows in observations.groupby(
        group_columns, dropna=False, sort=True
    ):
        color, valid_count, total_count = _validity(rows["valid_measurement"])
        reasons: list[str] = []
        if "invalid_reasons" in rows:
            for value in rows["invalid_reasons"].dropna().astype(str):
                reasons.extend(part for part in value.split(";") if part)
        reason_text = "; ".join(dict.fromkeys(reasons)) or "none"

        unique_points: dict[bytes, Point] = {}
        for geometry in rows.geometry:
            for point in _points(geometry):
                unique_points[point.wkb] = point
        for point in unique_points.values():
            inside = bool(area.api_boundary.covers(point))
            popup = folium.Popup(
                "<br>".join(
                    [
                        f"Source: {html.escape(str(source_id))}",
                        f"Observation code: {html.escape(str(observation_code))}",
                        f"Valid rows: {valid_count}/{total_count}",
                        f"Inside boundary: {'yes' if inside else 'no'}",
                        f"Invalid reasons: {html.escape(reason_text)}",
                        f"Longitude: {point.x:.8f}",
                        f"Latitude: {point.y:.8f}",
                    ]
                ),
                max_width=420,
            )
            folium.CircleMarker(
                location=(point.y, point.x),
                radius=5,
                color=color if inside else "#212121",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.88,
                tooltip=f"JARTIC {observation_code}",
                popup=popup,
            ).add_to(layer)
            marker_count += 1
    layer.add_to(map_object)
    return marker_count


def build_map(
    area: StudyArea,
    *,
    jartic_inputs: Sequence[tuple[str, gpd.GeoDataFrame]] = (),
    basemap: bool = True,
) -> tuple[folium.Map, int]:
    """Build the interactive review map without writing it to disk."""

    center = area.api_boundary.representative_point()
    map_object = folium.Map(
        location=(center.y, center.x),
        zoom_start=12,
        tiles="OpenStreetMap" if basemap else None,
        control_scale=True,
        prefer_canvas=True,
    )
    add_boundary_layers(map_object, area)
    marker_count = 0
    for label, observations in jartic_inputs:
        marker_count += add_jartic_layer(
            map_object,
            area,
            observations,
            source_label=label,
        )
    map_object.get_root().html.add_child(_summary_panel(area))
    map_object.get_root().html.add_child(_legend())
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.fit_bounds([[area.south, area.west], [area.north, area.east]])
    return map_object, marker_count


def write_map(map_object: folium.Map, output_path: Path, *, overwrite: bool) -> None:
    """Write HTML through a temporary file, refusing implicit replacement."""

    if output_path.suffix.lower() != ".html":
        raise ValueError("output path must end in .html")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite output: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(output_path.name + ".part")
    if partial.exists():
        partial.unlink()
    try:
        map_object.save(str(partial))
        os.replace(partial, output_path)
    finally:
        if partial.exists():
            partial.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a governed study-area boundary and optional JARTIC sites."
    )
    parser.add_argument("--region", required=True, help="Governed study-area ID")
    parser.add_argument(
        "--jartic",
        action="append",
        default=[],
        metavar="REPOSITORY_RELATIVE_PARQUET",
        help="Normalized JARTIC GeoParquet; may be specified more than once",
    )
    parser.add_argument(
        "--output",
        help=(
            "Repository-relative HTML path; defaults to "
            "reproducibility/outputs/traffic_simulation/visualization/<region>_study_area.html"
        ),
    )
    parser.add_argument(
        "--no-basemap",
        action="store_true",
        help="Do not request OpenStreetMap background tiles",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly replace an existing runtime visualization",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        area = load_study_area(args.region)
        inputs: list[tuple[str, gpd.GeoDataFrame]] = []
        for value in args.jartic:
            path = resolve_repository_path(value, label="JARTIC path")
            inputs.append((path.stem, read_jartic_observations(path)))
        if args.output:
            output_path = resolve_repository_path(args.output, label="output path")
        else:
            output_path = DEFAULT_OUTPUT_DIRECTORY / f"{args.region}_study_area.html"
        map_object, marker_count = build_map(
            area,
            jartic_inputs=inputs,
            basemap=not args.no_basemap,
        )
        write_map(map_object, output_path, overwrite=args.overwrite)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"region: {area.region_id}")
    print(f"boundary features: 1 (dissolved from {area.source_feature_count})")
    print(f"JARTIC markers: {marker_count}")
    print(f"map: {output_path.relative_to(REPOSITORY_ROOT)}")
    if args.no_basemap:
        print("note: opening the HTML requires network access for Leaflet assets")
    else:
        print("note: opening the HTML requires network access for Leaflet assets and tiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
