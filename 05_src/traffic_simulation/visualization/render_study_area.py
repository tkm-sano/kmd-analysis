"""Render a governed study area, registered OSM roads, and JARTIC sites."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, Sequence

import folium
import geopandas as gpd
import pandas as pd
from branca.element import Element
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    Point,
    mapping,
    shape,
)
from shapely.geometry.base import BaseGeometry

from traffic_simulation.network.study_areas import StudyArea, load_study_area
from traffic_simulation.paths import REPOSITORY_ROOT, RUN_OUTPUT_ROOT, SOURCE_REGISTRY
from traffic_simulation.research_stage import ResearchProgress, load_research_progress


DEFAULT_OUTPUT_DIRECTORY: Final = RUN_OUTPUT_ROOT / "visualization"
BOUNDARY_COLOR: Final = "#1565c0"
BBOX_COLOR: Final = "#d32f2f"
VALID_COLOR: Final = "#2e7d32"
MIXED_COLOR: Final = "#ef6c00"
INVALID_COLOR: Final = "#c62828"
SIGNAL_COLOR: Final = "#6a1b9a"
ROAD_FILTER: Final = (
    "w/highway=motorway,motorway_link,trunk,trunk_link,primary,primary_link,"
    "secondary,secondary_link,tertiary,tertiary_link,unclassified,residential,"
    "living_street,service,road"
)
ROAD_LAYER_STYLES: Final = {
    "expressway": {
        "label": "Expressway / trunk",
        "color": "#c62828",
        "weight": 3.2,
        "show": True,
    },
    "arterial": {
        "label": "Primary / secondary",
        "color": "#ef6c00",
        "weight": 2.6,
        "show": True,
    },
    "collector": {
        "label": "Tertiary / unclassified",
        "color": "#2e7d32",
        "weight": 1.9,
        "show": True,
    },
    "residential": {
        "label": "Residential / living street",
        "color": "#1976d2",
        "weight": 1.2,
        "show": False,
    },
    "service": {
        "label": "Service / other motor road",
        "color": "#757575",
        "weight": 1.0,
        "show": False,
    },
}


@dataclass(frozen=True, slots=True)
class OsmRoadData:
    """Provenance-checked road features prepared for interactive rendering."""

    source_id: str
    snapshot_date: str
    extract_path: Path
    extract_sha256: str
    highway_way_count: int
    features_by_layer: Mapping[str, tuple[dict[str, Any], ...]]
    signal_features: tuple[dict[str, Any], ...]

    @property
    def rendered_road_count(self) -> int:
        return sum(len(features) for features in self.features_by_layer.values())


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_source_row(source_id: str) -> dict[str, str]:
    with SOURCE_REGISTRY.open(newline="", encoding="utf-8-sig") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("source_id") == source_id
        ]
    if len(rows) != 1:
        raise ValueError(
            f"expected one source-registry row for {source_id}, found {len(rows)}"
        )
    return rows[0]


def _processed_paths(row: Mapping[str, str]) -> tuple[Path, Path]:
    values = [value for value in row.get("processed_outputs", "").split(";") if value]
    pbf_values = [value for value in values if value.endswith(".osm.pbf")]
    summary_values = [
        value for value in values if value.endswith("_quality_summary.json")
    ]
    if len(pbf_values) != 1 or len(summary_values) != 1:
        raise ValueError(
            "OSM source registry must identify one extract PBF and one quality summary"
        )
    return (
        resolve_repository_path(pbf_values[0], label="OSM extract path"),
        resolve_repository_path(summary_values[0], label="OSM summary path"),
    )


def load_osm_source(source_id: str, *, region_id: str) -> tuple[Path, dict[str, Any]]:
    """Resolve a registered OSM extract and verify its recorded SHA-256."""

    row = _read_source_row(source_id)
    if row.get("status") != "processed":
        raise ValueError(f"OSM source is not processed: {source_id}")
    extract_path, summary_path = _processed_paths(row)
    if not extract_path.is_file():
        raise FileNotFoundError(f"OSM extract does not exist: {extract_path}")
    if not summary_path.is_file():
        raise FileNotFoundError(f"OSM quality summary does not exist: {summary_path}")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"OSM quality summary is invalid JSON: {summary_path}"
        ) from exc
    if not isinstance(summary, dict):
        raise ValueError("OSM quality summary must be a JSON object")
    expected = {
        "source_id": source_id,
        "region_id": region_id,
        "extract_path": extract_path.relative_to(REPOSITORY_ROOT).as_posix(),
    }
    mismatches = [key for key, value in expected.items() if summary.get(key) != value]
    if mismatches:
        raise ValueError(
            "OSM source metadata does not match the requested map: "
            + ", ".join(mismatches)
        )
    recorded_digest = summary.get("extract_sha256")
    actual_digest = sha256_file(extract_path)
    if recorded_digest != actual_digest:
        raise ValueError(
            f"OSM extract SHA-256 mismatch: {actual_digest} != {recorded_digest}"
        )
    counts = summary.get("extract_counts")
    if not isinstance(counts, dict) or not isinstance(counts.get("highway_ways"), int):
        raise ValueError("OSM quality summary lacks highway way counts")
    return extract_path, summary


def _run_osmium(command: Sequence[str]) -> None:
    try:
        subprocess.run(list(command), check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise RuntimeError("osmium was not found in the analysis environment") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"osmium visualization command failed{suffix}") from exc


def _road_layer(highway: str) -> str:
    base = highway.removesuffix("_link")
    if base in {"motorway", "trunk"}:
        return "expressway"
    if base in {"primary", "secondary"}:
        return "arterial"
    if base in {"tertiary", "unclassified"}:
        return "collector"
    if base in {"residential", "living_street"}:
        return "residential"
    return "service"


def _line_parts(geometry: BaseGeometry) -> list[LineString]:
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, MultiLineString):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        parts: list[LineString] = []
        for member in geometry.geoms:
            parts.extend(_line_parts(member))
        return parts
    return []


def _display_properties(
    raw: Mapping[str, Any], *, osm_id: str, inside_boundary: bool
) -> dict[str, str]:
    return {
        "osm_id": osm_id,
        "name": str(raw.get("name") or ""),
        "ref": str(raw.get("ref") or ""),
        "highway": str(raw.get("highway") or ""),
        "oneway": str(raw.get("oneway") or ""),
        "lanes": str(raw.get("lanes") or ""),
        "maxspeed": str(raw.get("maxspeed") or ""),
        "access": str(raw.get("access") or ""),
        "inside_boundary": "yes" if inside_boundary else "no",
    }


def prepare_osm_roads(
    source_id: str,
    area: StudyArea,
    *,
    osmium_command: str = "osmium",
) -> OsmRoadData:
    """Filter, export, clip, and group registered OSM roads for display."""

    extract_path, summary = load_osm_source(source_id, region_id=area.region_id)
    layer_features: dict[str, list[dict[str, Any]]] = {
        key: [] for key in ROAD_LAYER_STYLES
    }
    signals: list[dict[str, Any]] = []
    bbox_geometry = area.api_boundary.envelope

    with tempfile.TemporaryDirectory(prefix="render-osm-") as temporary_directory:
        temporary = Path(temporary_directory)
        filtered_path = temporary / "roads.osm.pbf"
        exported_path = temporary / "roads.geojsonseq"
        _run_osmium(
            [
                osmium_command,
                "tags-filter",
                "--input-format",
                "pbf",
                "--output-format",
                "pbf",
                "--output",
                str(filtered_path),
                str(extract_path),
                ROAD_FILTER,
                "n/highway=traffic_signals",
            ]
        )
        _run_osmium(
            [
                osmium_command,
                "export",
                "--input-format",
                "pbf",
                "--output-format",
                "geojsonseq",
                "--geometry-types",
                "point,linestring",
                "--add-unique-id",
                "type_id",
                "--output",
                str(exported_path),
                str(filtered_path),
            ]
        )

        with exported_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.lstrip("\x1e").strip()
                if not text:
                    continue
                try:
                    feature = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid osmium GeoJSON sequence at line {line_number}"
                    ) from exc
                if not isinstance(feature, dict):
                    raise ValueError("osmium GeoJSON feature must be an object")
                properties = feature.get("properties")
                raw_geometry = feature.get("geometry")
                if not isinstance(properties, dict) or not isinstance(
                    raw_geometry, dict
                ):
                    continue
                geometry = shape(raw_geometry)
                if geometry.is_empty or not geometry.intersects(bbox_geometry):
                    continue
                osm_id = str(feature.get("id") or "")

                if isinstance(geometry, Point):
                    if properties.get("highway") != "traffic_signals":
                        continue
                    signal_properties = _display_properties(
                        properties,
                        osm_id=osm_id,
                        inside_boundary=bool(area.api_boundary.covers(geometry)),
                    )
                    signals.append(_feature(geometry, signal_properties))
                    continue

                highway = str(properties.get("highway") or "")
                if not highway:
                    continue
                clipped = geometry.intersection(bbox_geometry)
                parts = [part for part in _line_parts(clipped) if part.length > 0]
                if not parts:
                    continue
                display_geometry: BaseGeometry
                display_geometry = (
                    parts[0] if len(parts) == 1 else MultiLineString(parts)
                )
                display_properties = _display_properties(
                    properties,
                    osm_id=osm_id,
                    inside_boundary=bool(
                        area.api_boundary.intersects(display_geometry)
                    ),
                )
                layer_features[_road_layer(highway)].append(
                    _feature(display_geometry, display_properties)
                )

    if not any(layer_features.values()):
        raise ValueError("registered OSM extract produced no renderable motor roads")
    return OsmRoadData(
        source_id=source_id,
        snapshot_date=str(summary.get("snapshot_date") or ""),
        extract_path=extract_path,
        extract_sha256=str(summary["extract_sha256"]),
        highway_way_count=int(summary["extract_counts"]["highway_ways"]),
        features_by_layer={
            key: tuple(features) for key, features in layer_features.items()
        },
        signal_features=tuple(signals),
    )


def _research_progress_html(progress: ResearchProgress) -> str:
    styles = {
        "completed": ("✓", "#2e7d32", "完了"),
        "in_progress": ("▶", "#ef6c00", "進行中"),
        "planned": ("○", "#757575", "予定"),
    }
    rows: list[str] = []
    for stage in progress.stages:
        symbol, color, status_ja = styles[stage.status]
        emphasis = "font-weight:bold;" if stage.status == "in_progress" else ""
        rows.append(
            f'<div style="margin:2px 0; color:{color}; {emphasis}">'
            f'{symbol} {html.escape(stage.label_ja)} [{status_ja}]</div>'
        )
    return f"""
      <hr style="margin: 7px 0;">
      <div style="font-weight:bold;">研究の現在地</div>
      <div style="margin:3px 0 5px 0; color:#5d4037; font-weight:bold;">
        ▶ {html.escape(progress.current_stage.label_ja)}
      </div>
      <div style="margin-bottom:5px;">{html.escape(progress.current_summary_ja)}</div>
      <div style="color:#555; margin-bottom:4px;">
        状態更新日: {html.escape(progress.updated_at)} / 進捗率は使用しない
      </div>
      <details>
        <summary style="cursor:pointer;">全工程を表示</summary>
        <div style="margin-top:4px;">{''.join(rows)}</div>
      </details>
    """


def _summary_panel(
    area: StudyArea,
    osm_roads: OsmRoadData | None,
    research_progress: ResearchProgress,
) -> Element:
    west, south, east, north = area.acquisition_bbox
    osm_content = ""
    if osm_roads is not None:
        osm_content = f"""
      <hr style="margin: 6px 0;">
      <div style="font-weight: bold;">Registered OSM roads</div>
      <div>Source: {html.escape(osm_roads.source_id)}</div>
      <div>Snapshot: {html.escape(osm_roads.snapshot_date)}</div>
      <div>Registered highway ways: {osm_roads.highway_way_count:,}</div>
      <div>Rendered motor-road ways: {osm_roads.rendered_road_count:,}</div>
      <div>Traffic signals: {len(osm_roads.signal_features):,}</div>
      <div>Extract SHA-256:<br>
        <span style="font-family: monospace; overflow-wrap: anywhere;">
          {html.escape(osm_roads.extract_sha256)}
        </span>
      </div>
        """
    content = f"""
    <div style="position: fixed; top: 10px; left: 50px; z-index: 9999;
                background: rgba(255,255,255,0.94); border: 1px solid #555;
                border-radius: 4px; padding: 10px; font: 12px sans-serif;
                max-width: 430px; max-height: 45vh; overflow-y: auto;">
      <div style="font-weight: bold; margin-bottom: 5px;">Study area review</div>
      {_research_progress_html(research_progress)}
      <hr style="margin: 7px 0;">
      <div style="font-weight: bold; margin-bottom: 4px;">Study area inputs</div>
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
      {osm_content}
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
      <div><span style="color:#c62828;">━</span> motorway / trunk</div>
      <div><span style="color:#ef6c00;">━</span> primary / secondary</div>
      <div><span style="color:#2e7d32;">━</span> tertiary / unclassified</div>
      <div><span style="color:#1976d2;">━</span> residential</div>
      <div><span style="color:#757575;">━</span> service / other</div>
      <div><span style="color:{SIGNAL_COLOR};">◆</span> OSM traffic signal</div>
      <div><span style="color:{VALID_COLOR};">●</span> all measurements valid</div>
      <div><span style="color:{MIXED_COLOR};">●</span> mixed validity</div>
      <div><span style="color:{INVALID_COLOR};">●</span>
        all measurements invalid</div>
      <div>Black ring: outside administrative boundary</div>
    </div>
    """
    return Element(content)


def add_osm_layers(map_object: folium.Map, roads: OsmRoadData) -> None:
    """Add categorized motor-road and traffic-signal layers."""

    for key, style in ROAD_LAYER_STYLES.items():
        features = roads.features_by_layer.get(key, ())
        if not features:
            continue
        folium.GeoJson(
            {"type": "FeatureCollection", "features": list(features)},
            name=f"OSM {style['label']} ({len(features):,})",
            style_function=lambda _, style=style: {
                "color": style["color"],
                "weight": style["weight"],
                "opacity": 0.86,
            },
            highlight_function=lambda _: {"weight": 5, "opacity": 1},
            # Branca elements have one parent. Reusing a tooltip across layers
            # emits JavaScript that references the last parent before it exists.
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "osm_id",
                    "name",
                    "ref",
                    "highway",
                    "oneway",
                    "lanes",
                    "maxspeed",
                    "access",
                    "inside_boundary",
                ],
                aliases=[
                    "OSM ID",
                    "Name",
                    "Ref",
                    "Highway",
                    "Oneway",
                    "Lanes",
                    "Max speed",
                    "Access",
                    "Intersects N03 boundary",
                ],
                sticky=False,
            ),
            smooth_factor=1.0,
            show=bool(style["show"]),
        ).add_to(map_object)

    if roads.signal_features:
        folium.GeoJson(
            {
                "type": "FeatureCollection",
                "features": list(roads.signal_features),
            },
            name=f"OSM traffic signals ({len(roads.signal_features):,})",
            marker=folium.CircleMarker(
                radius=3,
                color=SIGNAL_COLOR,
                weight=1,
                fill=True,
                fill_color=SIGNAL_COLOR,
                fill_opacity=0.9,
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=["osm_id", "inside_boundary"],
                aliases=["OSM ID", "Inside N03 boundary"],
            ),
            show=False,
        ).add_to(map_object)


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
    osm_roads: OsmRoadData | None = None,
    jartic_inputs: Sequence[tuple[str, gpd.GeoDataFrame]] = (),
    basemap: bool = True,
    research_progress: ResearchProgress | None = None,
) -> tuple[folium.Map, int, int, int]:
    """Build the interactive review map without writing it to disk."""

    center = area.api_boundary.representative_point()
    map_object = folium.Map(
        location=(center.y, center.x),
        zoom_start=12,
        tiles="OpenStreetMap" if basemap else None,
        control_scale=True,
        prefer_canvas=True,
    )
    if osm_roads is not None:
        add_osm_layers(map_object, osm_roads)
    add_boundary_layers(map_object, area)
    marker_count = 0
    for label, observations in jartic_inputs:
        marker_count += add_jartic_layer(
            map_object,
            area,
            observations,
            source_label=label,
        )
    progress = research_progress or load_research_progress()
    map_object.get_root().html.add_child(_summary_panel(area, osm_roads, progress))
    map_object.get_root().html.add_child(_legend())
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.fit_bounds([[area.south, area.west], [area.north, area.east]])
    road_count = osm_roads.rendered_road_count if osm_roads is not None else 0
    signal_count = len(osm_roads.signal_features) if osm_roads is not None else 0
    return map_object, marker_count, road_count, signal_count


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
        "--osm-source-id",
        help=(
            "Processed OSM source-registry ID; resolves and verifies the local PBF "
            "without accepting an arbitrary file path"
        ),
    )
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
            "reproducibility/outputs/traffic_simulation/visualization/"
            "<region>_study_area.html"
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
        osm_roads = (
            prepare_osm_roads(args.osm_source_id, area)
            if args.osm_source_id
            else None
        )
        inputs: list[tuple[str, gpd.GeoDataFrame]] = []
        for value in args.jartic:
            path = resolve_repository_path(value, label="JARTIC path")
            inputs.append((path.stem, read_jartic_observations(path)))
        if args.output:
            output_path = resolve_repository_path(args.output, label="output path")
        else:
            output_path = DEFAULT_OUTPUT_DIRECTORY / f"{args.region}_study_area.html"
        map_object, marker_count, road_count, signal_count = build_map(
            area,
            osm_roads=osm_roads,
            jartic_inputs=inputs,
            basemap=not args.no_basemap,
        )
        write_map(map_object, output_path, overwrite=args.overwrite)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"region: {area.region_id}")
    print(f"boundary features: 1 (dissolved from {area.source_feature_count})")
    print(f"OSM rendered motor-road ways: {road_count}")
    print(f"OSM traffic signals: {signal_count}")
    print(f"JARTIC markers: {marker_count}")
    print(f"map: {output_path.relative_to(REPOSITORY_ROOT)}")
    if args.no_basemap:
        print("note: opening the HTML requires network access for Leaflet assets")
    else:
        print(
            "note: opening the HTML requires network access for Leaflet assets "
            "and tiles"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
