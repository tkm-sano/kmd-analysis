"""Load, validate, and materialize governed traffic-simulation study areas."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence
from zoneinfo import ZoneInfo

import geopandas as gpd
import yaml
from pyproj import CRS
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from traffic_simulation.paths import (
    PROCESSED_DATASETS,
    REPOSITORY_ROOT,
    SOURCE_REGISTRY,
)


SCHEMA_VERSION: Final = 1
CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility"
    / "config"
    / "traffic_simulation"
    / "study_areas.yml"
)
PROCESSING_SCRIPT: Final = "05_src/traffic_simulation/network/study_areas.py"
JST: Final = ZoneInfo("Asia/Tokyo")
REGION_ID_PATTERN: Final = re.compile(r"^[a-z0-9_]+$")
SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
VALID_STATUSES: Final = frozenset({"draft", "active", "retired"})
VALID_USES: Final = frozenset(
    {"osm_acquisition", "sumo_network_validation", "jartic_edge_mapping"}
)
REGISTRY_FIELDS: Final = (
    "source_id",
    "dataset_name",
    "provider",
    "source_url",
    "downloaded_at",
    "observation_start",
    "observation_end",
    "geographic_scope",
    "license_or_terms",
    "original_filename",
    "local_raw_path",
    "sha256",
    "processing_script",
    "processed_outputs",
    "status",
    "limitations",
)
AREA_FIELDS: Final = frozenset(
    {
        "version",
        "status",
        "name_ja",
        "geometry_type",
        "boundary_source",
        "api_crs",
        "metric_crs",
        "acquisition_extent_method",
        "network_clip_method",
        "intended_uses",
    }
)
SOURCE_FIELDS: Final = frozenset(
    {
        "dataset",
        "source_registry_id",
        "code_field",
        "code_value",
        "prefecture_field",
        "prefecture_value",
        "municipality_field",
        "municipality_value",
    }
)


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True, slots=True)
class StudyArea:
    """An immutable administrative study area in source, API, and metric CRS."""

    region_id: str
    version: int
    name_ja: str
    source_registry_id: str
    source_crs: CRS
    api_crs: CRS
    metric_crs: CRS
    source_boundary: BaseGeometry
    api_boundary: BaseGeometry
    metric_boundary: BaseGeometry
    acquisition_bbox: tuple[float, float, float, float]
    source_feature_count: int
    raw_sha256: str

    @property
    def west(self) -> float:
        return self.acquisition_bbox[0]

    @property
    def south(self) -> float:
        return self.acquisition_bbox[1]

    @property
    def east(self) -> float:
        return self.acquisition_bbox[2]

    @property
    def north(self) -> float:
        return self.acquisition_bbox[3]


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} keys must be strings")
    return value


def _require_exact_fields(
    value: dict[str, Any], expected: frozenset[str], label: str
) -> None:
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing:
        raise ValueError(f"{label} lacks fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {sorted(unknown)}")


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if Path(value).is_absolute():
        raise ValueError(f"{label} must not contain an absolute path")
    return value


def _parse_crs(value: Any, label: str) -> CRS:
    text = _require_text(value, label)
    try:
        return CRS.from_user_input(text)
    except Exception as exc:
        raise ValueError(f"{label} is not a valid CRS: {text}") from exc


def load_config(path: Path = CONFIG_PATH) -> Mapping[str, Mapping[str, Any]]:
    """Read and strictly validate the versioned study-area configuration."""

    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}") from exc
    root = _require_mapping(document, "study-area configuration")
    _require_exact_fields(root, frozenset({"schema_version", "study_areas"}), "root")
    if isinstance(root["schema_version"], bool) or root["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {root['schema_version']!r}")

    raw_areas = _require_mapping(root["study_areas"], "study_areas")
    if not raw_areas:
        raise ValueError("study_areas must not be empty")
    validated: dict[str, Mapping[str, Any]] = {}
    for region_id, raw_area in raw_areas.items():
        if not REGION_ID_PATTERN.fullmatch(region_id):
            raise ValueError(f"invalid region id: {region_id!r}")
        area = _require_mapping(raw_area, f"study_areas.{region_id}")
        _require_exact_fields(area, AREA_FIELDS, f"study_areas.{region_id}")
        if isinstance(area["version"], bool) or not isinstance(area["version"], int):
            raise ValueError(f"{region_id}.version must be an integer")
        if area["version"] < 1:
            raise ValueError(f"{region_id}.version must be positive")
        if area["status"] not in VALID_STATUSES:
            raise ValueError(f"{region_id}.status is not supported")
        _require_text(area["name_ja"], f"{region_id}.name_ja")
        if area["geometry_type"] != "administrative_boundary":
            raise ValueError(f"{region_id}.geometry_type is not supported")
        if area["acquisition_extent_method"] != "boundary_envelope":
            raise ValueError(f"{region_id}.acquisition_extent_method is not supported")
        if area["network_clip_method"] != "intersects_boundary":
            raise ValueError(f"{region_id}.network_clip_method is not supported")

        source = _require_mapping(area["boundary_source"], f"{region_id}.boundary_source")
        _require_exact_fields(source, SOURCE_FIELDS, f"{region_id}.boundary_source")
        if source["dataset"] != "MLIT_N03":
            raise ValueError(f"{region_id}.boundary_source.dataset is not supported")
        for key, value in source.items():
            _require_text(value, f"{region_id}.boundary_source.{key}")

        api_crs = _parse_crs(area["api_crs"], f"{region_id}.api_crs")
        metric_crs = _parse_crs(area["metric_crs"], f"{region_id}.metric_crs")
        if api_crs.to_epsg() != 4326:
            raise ValueError(f"{region_id}.api_crs must be EPSG:4326")
        if not metric_crs.is_projected:
            raise ValueError(f"{region_id}.metric_crs must be projected")

        uses = area["intended_uses"]
        if not isinstance(uses, list) or not uses or len(uses) != len(set(uses)):
            raise ValueError(f"{region_id}.intended_uses must be a unique non-empty list")
        if not all(isinstance(use, str) and use in VALID_USES for use in uses):
            raise ValueError(f"{region_id}.intended_uses contains an unsupported value")
        validated[region_id] = MappingProxyType(dict(area))
    return MappingProxyType(validated)


def _read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
            raise ValueError(f"unexpected source-registry columns in {path}")
        rows = list(reader)
    source_ids = [row["source_id"] for row in rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id in source registry")
    return rows


def lookup_source(source_id: str, registry_path: Path = SOURCE_REGISTRY) -> dict[str, str]:
    matches = [row for row in _read_registry(registry_path) if row["source_id"] == source_id]
    if len(matches) != 1:
        raise ValueError(f"expected one registry row for {source_id}, found {len(matches)}")
    row = matches[0]
    for field in ("original_filename", "local_raw_path", "sha256"):
        if not row.get(field):
            raise ValueError(f"registry row {source_id} lacks {field}")
    if not SHA256_PATTERN.fullmatch(row["sha256"]):
        raise ValueError(f"registry row {source_id} has an invalid SHA-256")
    return row


def resolve_raw_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError("registered raw path must be repository-relative")
    raw_path = (REPOSITORY_ROOT / candidate).resolve()
    try:
        raw_path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise ValueError("registered raw path escapes the repository") from exc
    return raw_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_raw_source(row: Mapping[str, str]) -> tuple[Path, str]:
    raw_path = resolve_raw_path(row["local_raw_path"])
    if not raw_path.is_file():
        raise FileNotFoundError(f"registered raw source does not exist: {raw_path}")
    if raw_path.name != row["original_filename"]:
        raise ValueError("registered raw path and original filename do not match")
    actual = sha256_file(raw_path)
    if actual != row["sha256"]:
        raise ValueError(
            f"raw SHA-256 hash mismatch for {raw_path}: {actual} != {row['sha256']}"
        )
    if not zipfile.is_zipfile(raw_path):
        raise ValueError(f"registered N03 source is not a valid ZIP: {raw_path}")
    return raw_path, actual


def _geojson_member(raw_path: Path) -> str:
    with zipfile.ZipFile(raw_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".geojson")]
        if len(members) != 1:
            raise ValueError(f"expected one GeoJSON in {raw_path}, found {len(members)}")
        member = members[0]
        if Path(member).is_absolute() or ".." in Path(member).parts:
            raise ValueError("unsafe GeoJSON member path in N03 ZIP")
        return member


def _read_n03(raw_path: Path) -> gpd.GeoDataFrame:
    member = _geojson_member(raw_path)
    frame = gpd.read_file(f"zip://{raw_path}!{member}")
    if frame.empty:
        raise ValueError("N03 source contains no features")
    if frame.crs is None:
        raise ValueError("N03 source does not declare a CRS")
    return frame


def _select_boundary(
    frame: gpd.GeoDataFrame, source: Mapping[str, Any]
) -> tuple[BaseGeometry, int]:
    fields = (
        source["code_field"],
        source["prefecture_field"],
        source["municipality_field"],
    )
    missing = set(fields) - set(frame.columns)
    if missing:
        raise ValueError(f"N03 source lacks selection fields: {sorted(missing)}")
    mask = (
        frame[fields[0]].astype("string").eq(source["code_value"])
        & frame[fields[1]].astype("string").eq(source["prefecture_value"])
        & frame[fields[2]].astype("string").eq(source["municipality_value"])
    )
    selected = frame.loc[mask].copy()
    if selected.empty:
        raise ValueError("N03 selection returned no features")
    if len(selected[list(fields)].drop_duplicates()) != 1:
        raise ValueError("N03 selection contains multiple administrative areas")
    if selected.geometry.isna().any() or selected.geometry.is_empty.any():
        raise ValueError("N03 selection contains an empty geometry")
    if not selected.geometry.is_valid.all():
        raise ValueError("N03 selection contains an invalid geometry")

    boundary = unary_union(selected.geometry.array)
    if boundary.is_empty or not boundary.is_valid:
        raise ValueError("dissolved N03 boundary is empty or invalid")
    if boundary.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"unexpected dissolved geometry type: {boundary.geom_type}")
    return boundary, len(selected)


def _transform_geometry(geometry: BaseGeometry, source: CRS, target: CRS) -> BaseGeometry:
    frame = gpd.GeoSeries([geometry], crs=source).to_crs(target)
    transformed = frame.iloc[0]
    if transformed.is_empty or not transformed.is_valid:
        raise ValueError(f"invalid geometry after transformation to {target.to_string()}")
    return transformed


def _validate_bbox(bounds: Sequence[float]) -> tuple[float, float, float, float]:
    if len(bounds) != 4:
        raise ValueError("boundary bounds must contain four values")
    west, south, east, north = (float(value) for value in bounds)
    if not (-180 <= west < east <= 180):
        raise ValueError("boundary longitude bounds are invalid")
    if not (-90 <= south < north <= 90):
        raise ValueError("boundary latitude bounds are invalid")
    return west, south, east, north


def load_study_area(
    region_id: str,
    *,
    config_path: Path = CONFIG_PATH,
    registry_path: Path = SOURCE_REGISTRY,
) -> StudyArea:
    """Resolve one active region from governed configuration and raw N03 data."""

    configurations = load_config(config_path)
    if region_id not in configurations:
        raise ValueError(f"unknown study area: {region_id}")
    config = configurations[region_id]
    if config["status"] != "active":
        raise ValueError(f"study area is not active: {region_id}")
    source_config = _require_mapping(config["boundary_source"], "boundary_source")
    source_row = lookup_source(source_config["source_registry_id"], registry_path)
    raw_path, raw_sha256 = verify_raw_source(source_row)
    frame = _read_n03(raw_path)
    source_crs = CRS.from_user_input(frame.crs)
    api_crs = _parse_crs(config["api_crs"], f"{region_id}.api_crs")
    metric_crs = _parse_crs(config["metric_crs"], f"{region_id}.metric_crs")
    source_boundary, source_feature_count = _select_boundary(frame, source_config)
    api_boundary = _transform_geometry(source_boundary, source_crs, api_crs)
    metric_boundary = _transform_geometry(source_boundary, source_crs, metric_crs)
    bbox = _validate_bbox(api_boundary.bounds)
    if metric_boundary.area <= 0:
        raise ValueError("projected N03 boundary has non-positive area")

    return StudyArea(
        region_id=region_id,
        version=config["version"],
        name_ja=config["name_ja"],
        source_registry_id=source_config["source_registry_id"],
        source_crs=source_crs,
        api_crs=api_crs,
        metric_crs=metric_crs,
        source_boundary=source_boundary,
        api_boundary=api_boundary,
        metric_boundary=metric_boundary,
        acquisition_bbox=bbox,
        source_feature_count=source_feature_count,
        raw_sha256=raw_sha256,
    )


def build_quality_summary(area: StudyArea) -> dict[str, Any]:
    """Create a JSON-serializable provenance and geometry summary."""

    return {
        "region_id": area.region_id,
        "version": area.version,
        "source_registry_id": area.source_registry_id,
        "raw_sha256": area.raw_sha256,
        "source_feature_count": area.source_feature_count,
        "output_feature_count": 1,
        "geometry_type": area.api_boundary.geom_type,
        "source_crs": area.source_crs.to_string(),
        "api_crs": area.api_crs.to_string(),
        "metric_crs": area.metric_crs.to_string(),
        "acquisition_bbox": {
            "west": area.west,
            "south": area.south,
            "east": area.east,
            "north": area.north,
        },
        "area_km2": area.metric_boundary.area / 1_000_000,
        "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
    }


def output_paths(area: StudyArea, source_row: Mapping[str, str]) -> tuple[Path, Path]:
    year_match = re.fullmatch(r"(\d{4})-\d{2}-\d{2}", source_row["observation_start"])
    if not year_match:
        raise ValueError("N03 registry observation_start must be YYYY-MM-DD")
    stem = f"{area.region_id}_n03_{year_match.group(1)}"
    boundary_path = PROCESSED_DATASETS["road_network"] / "boundaries" / f"{stem}.parquet"
    summary_path = PROCESSED_DATASETS["validation"] / f"{stem}_quality_summary.json"
    return boundary_path, summary_path


def write_outputs(
    area: StudyArea,
    summary: dict[str, Any],
    *,
    boundary_path: Path,
    summary_path: Path,
) -> None:
    """Write the canonical source-CRS boundary and summary without overwriting."""

    existing = [path for path in (boundary_path, summary_path) if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite output: {existing[0]}")
    boundary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    boundary_part = boundary_path.with_name(boundary_path.name + ".part")
    summary_part = summary_path.with_name(summary_path.name + ".part")
    for partial in (boundary_part, summary_part):
        if partial.exists():
            partial.unlink()

    boundary_committed = False
    summary_committed = False
    try:
        frame = gpd.GeoDataFrame(
            [
                {
                    "region_id": area.region_id,
                    "version": area.version,
                    "name_ja": area.name_ja,
                    "source_registry_id": area.source_registry_id,
                    "raw_sha256": area.raw_sha256,
                    "source_feature_count": area.source_feature_count,
                    "geometry": area.source_boundary,
                }
            ],
            geometry="geometry",
            crs=area.source_crs,
        )
        frame.to_parquet(boundary_part, index=False)
        summary_to_write = dict(summary)
        summary_to_write["boundary_sha256"] = sha256_file(boundary_part)
        summary_part.write_text(
            json.dumps(summary_to_write, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(boundary_part, boundary_path)
        boundary_committed = True
        os.replace(summary_part, summary_path)
        summary_committed = True
    finally:
        for partial in (boundary_part, summary_part):
            if partial.exists():
                partial.unlink()
        if not summary_committed:
            if boundary_committed and boundary_path.exists():
                boundary_path.unlink()
            if summary_path.exists():
                summary_path.unlink()


def run(region_id: str) -> tuple[Path, Path, dict[str, Any]]:
    area = load_study_area(region_id)
    source_row = lookup_source(area.source_registry_id)
    boundary_path, summary_path = output_paths(area, source_row)
    summary = build_quality_summary(area)
    write_outputs(
        area,
        summary,
        boundary_path=boundary_path,
        summary_path=summary_path,
    )
    return boundary_path, summary_path, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a registered administrative study-area boundary."
    )
    parser.add_argument("--region", required=True, help="Governed study-area ID")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        boundary_path, summary_path, summary = run(args.region)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(1, f"error: {exc}\n")
    bbox = summary["acquisition_bbox"]
    print(f"source features: {summary['source_feature_count']}")
    print(f"area: {summary['area_km2']:.6f} km2")
    print(
        "acquisition bbox: "
        f"{bbox['west']:.9f},{bbox['south']:.9f},"
        f"{bbox['east']:.9f},{bbox['north']:.9f}"
    )
    print(f"boundary: {boundary_path.relative_to(REPOSITORY_ROOT)}")
    print(f"quality summary: {summary_path.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
