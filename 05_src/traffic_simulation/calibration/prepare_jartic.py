"""Normalize registered JARTIC snapshots for traffic calibration and mapping."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final, Sequence

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPoint

from traffic_simulation.calibration.fetch_jartic import (
    JST,
    REGISTRY_FIELDS,
    parse_time_code,
)
from traffic_simulation.paths import (
    PROCESSED_DATASETS,
    REPOSITORY_ROOT,
    SOURCE_REGISTRY,
)


PREPARATION_SCRIPT: Final = (
    "05_src/traffic_simulation/calibration/prepare_jartic.py"
)
VOLUME_SUFFIXES: Final = {
    "small_volume": "小型交通量",
    "large_volume": "大型交通量",
    "unknown_volume": "車種判別不能交通量",
}
FLAG_SUFFIXES: Final = {
    "power_outage": "停電",
    "loop_error": "ループ異常",
    "ultrasonic_error": "超音波異常",
    "missing": "欠測",
}
DIRECTION_PREFIXES: Final = {"up": "上り", "down": "下り"}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _nullable_volume(value: Any, label: str) -> tuple[int | pd._libs.missing.NAType, str | None]:
    if value is None or value == "":
        return pd.NA, "missing_volume"
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer or null")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer or null") from exc
    if not numeric.is_integer():
        raise ValueError(f"{label} must be an integer or null")
    integer = int(numeric)
    if integer < 0:
        return integer, "negative_volume"
    return integer, None


def _flag_value(value: Any, label: str) -> tuple[bool, str | None]:
    if value in (0, "0"):
        return False, None
    if value in (1, "1"):
        return True, None
    if value is None or value == "":
        return False, f"unknown_{label}"
    raise ValueError(f"{label} flag must be 0, 1, or blank")


def _geometry(value: Any, feature_index: int) -> MultiPoint:
    geometry = _require_mapping(value, f"feature {feature_index} geometry")
    if geometry.get("type") != "MultiPoint":
        raise ValueError(f"feature {feature_index} geometry must be MultiPoint")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError(f"feature {feature_index} geometry has no coordinates")

    validated: list[tuple[float, float]] = []
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            raise ValueError(f"feature {feature_index} has an invalid coordinate")
        try:
            longitude, latitude = float(coordinate[0]), float(coordinate[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"feature {feature_index} has a non-numeric coordinate"
            ) from exc
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError(f"feature {feature_index} coordinate is out of range")
        validated.append((longitude, latitude))
    return MultiPoint(validated)


def _observation_times(time_code: str, layer: str) -> tuple[datetime, datetime, int]:
    start = parse_time_code(time_code, layer)
    interval_minutes = 60 if layer == "1h" else 5
    end = start + timedelta(minutes=interval_minutes) - timedelta(seconds=1)
    return start, end, interval_minutes


def normalize_payload(
    payload: dict[str, Any], *, source_id: str, layer: str
) -> gpd.GeoDataFrame:
    """Convert each JARTIC feature into separate measured up/down rows.

    JARTIC directions remain unresolved with respect to SUMO directed edges.
    No directional traffic value is estimated, divided, or imputed.
    """

    if layer not in {"1h", "5m"}:
        raise ValueError("layer must be '1h' or '5m'")
    root = _require_mapping(payload, "payload")
    if root.get("type") != "FeatureCollection":
        raise ValueError("payload is not a GeoJSON FeatureCollection")
    features = root.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("payload contains no features")
    reported = root.get("numberReturned")
    if reported is not None and int(reported) != len(features):
        raise ValueError("numberReturned does not match the feature count")

    rows: list[dict[str, Any]] = []
    for feature_index, raw_feature in enumerate(features):
        feature = _require_mapping(raw_feature, f"feature {feature_index}")
        properties = _require_mapping(
            feature.get("properties"), f"feature {feature_index} properties"
        )
        geometry = _geometry(feature.get("geometry"), feature_index)
        observation_code = properties.get("常時観測点コード")
        time_value = properties.get("時間コード")
        road_type = properties.get("道路種別")
        if observation_code in (None, ""):
            raise ValueError(f"feature {feature_index} lacks observation code")
        if time_value in (None, ""):
            raise ValueError(f"feature {feature_index} lacks time code")
        if road_type in (None, ""):
            raise ValueError(f"feature {feature_index} lacks road type")

        time_code = str(time_value)
        start, end, interval_minutes = _observation_times(time_code, layer)
        for jartic_direction, prefix in DIRECTION_PREFIXES.items():
            row: dict[str, Any] = {
                "source_id": source_id,
                "feature_id": str(feature.get("id", "")),
                "observation_code": str(observation_code),
                "time_code": time_code,
                "observation_start_jst": start,
                "observation_end_jst": end,
                "interval_minutes": interval_minutes,
                "road_type": str(road_type),
                "jartic_direction": jartic_direction,
                "direction_status": "unresolved",
                "sumo_edge_id": pd.NA,
                "sumo_direction": pd.NA,
                "geometry_point_count": len(geometry.geoms),
                "geometry": geometry,
            }
            invalid_reasons: list[str] = []
            volumes: list[int | pd._libs.missing.NAType] = []
            for column, suffix in VOLUME_SUFFIXES.items():
                label = f"{prefix}・{suffix}"
                volume, reason = _nullable_volume(properties.get(label), label)
                row[column] = volume
                volumes.append(volume)
                if reason and reason not in invalid_reasons:
                    invalid_reasons.append(reason)

            for column, suffix in FLAG_SUFFIXES.items():
                label = f"{prefix}・{suffix}"
                flag, reason = _flag_value(properties.get(label), column)
                row[column] = flag
                if flag:
                    invalid_reasons.append(column)
                if reason:
                    invalid_reasons.append(reason)

            if any(pd.isna(value) or int(value) < 0 for value in volumes):
                row["total_volume"] = pd.NA
            else:
                row["total_volume"] = sum(int(value) for value in volumes)
            row["valid_measurement"] = not invalid_reasons
            row["invalid_reasons"] = ";".join(dict.fromkeys(invalid_reasons))
            rows.append(row)

    observations = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    key = ["source_id", "observation_code", "time_code", "jartic_direction"]
    if observations.duplicated(key, keep=False).any():
        raise ValueError("duplicate observation/time/direction key detected")

    for column in (*VOLUME_SUFFIXES, "total_volume"):
        observations[column] = pd.array(observations[column], dtype="Int64")
    for column in (*FLAG_SUFFIXES, "valid_measurement"):
        observations[column] = observations[column].astype("boolean")
    observations["observation_code"] = observations["observation_code"].astype("string")
    observations["time_code"] = observations["time_code"].astype("string")
    observations["road_type"] = observations["road_type"].astype("string")
    return observations


def build_quality_summary(
    observations: gpd.GeoDataFrame, *, source_id: str, raw_sha256: str
) -> dict[str, Any]:
    """Summarize validity without removing invalid directional measurements."""

    valid = observations["valid_measurement"].fillna(False).astype(bool)
    return {
        "source_id": source_id,
        "raw_sha256": raw_sha256,
        "normalized_row_count": int(len(observations)),
        "valid_row_count": int(valid.sum()),
        "invalid_row_count": int((~valid).sum()),
        "missing_row_count": int(observations["missing"].fillna(False).sum()),
        "anomaly_counts": {
            column: int(observations[column].fillna(False).sum())
            for column in FLAG_SUFFIXES
        },
        "observation_code_count": int(observations["observation_code"].nunique()),
        "time_codes": sorted(str(value) for value in observations["time_code"].unique()),
        "road_types": sorted(str(value) for value in observations["road_type"].unique()),
        "crs": observations.crs.to_string() if observations.crs else None,
        "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
    }


def verify_raw_source(raw_path: Path, expected_sha256: str) -> tuple[dict[str, Any], str]:
    """Verify the registered raw hash, then decode the immutable GeoJSON."""

    raw_bytes = raw_path.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"raw SHA-256 hash mismatch for {raw_path}: "
            f"{actual_sha256} != {expected_sha256}"
        )
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"raw source is not valid UTF-8 JSON: {raw_path}") from exc
    return _require_mapping(payload, "raw payload"), actual_sha256


def write_outputs(
    observations: gpd.GeoDataFrame,
    summary: dict[str, Any],
    *,
    observations_path: Path,
    summary_path: Path,
) -> None:
    """Write GeoParquet and JSON through temporary files without overwriting."""

    existing = [path for path in (observations_path, summary_path) if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite output: {existing[0]}")
    observations_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    observations_part = observations_path.with_name(observations_path.name + ".part")
    summary_part = summary_path.with_name(summary_path.name + ".part")
    for partial in (observations_part, summary_part):
        if partial.exists():
            partial.unlink()

    parquet_committed = False
    summary_committed = False
    try:
        observations.to_parquet(observations_part, index=False)
        summary_to_write = dict(summary)
        summary_to_write["observations_sha256"] = hashlib.sha256(
            observations_part.read_bytes()
        ).hexdigest()
        summary_part.write_text(
            json.dumps(summary_to_write, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        os.replace(observations_part, observations_path)
        parquet_committed = True
        os.replace(summary_part, summary_path)
        summary_committed = True
    finally:
        for partial in (observations_part, summary_part):
            if partial.exists():
                partial.unlink()
        if not summary_committed:
            if parquet_committed and observations_path.exists():
                observations_path.unlink()
            if summary_path.exists():
                summary_path.unlink()


def _read_registry(registry: Path) -> list[dict[str, str]]:
    with registry.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
            raise ValueError(f"unexpected source-registry columns in {registry}")
        return list(reader)


def _write_registry(registry: Path, rows: list[dict[str, str]]) -> None:
    partial = registry.with_name(registry.name + ".part")
    try:
        with partial.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=REGISTRY_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(partial, registry)
    finally:
        if partial.exists():
            partial.unlink()


def _merge_semicolon_values(existing: str, additions: Sequence[str]) -> str:
    values = [value for value in existing.split(";") if value]
    for addition in additions:
        if addition and addition not in values:
            values.append(addition)
    return ";".join(values)


def mark_source_processed(
    registry: Path,
    *,
    source_id: str,
    processed_outputs: Sequence[str],
) -> None:
    """Record processing provenance idempotently for one registered source."""

    rows = _read_registry(registry)
    matches = [index for index, row in enumerate(rows) if row["source_id"] == source_id]
    if len(matches) != 1:
        raise ValueError(f"expected one registry row for {source_id}, found {len(matches)}")
    row = dict(rows[matches[0]])
    row["processing_script"] = _merge_semicolon_values(
        row.get("processing_script", ""), [PREPARATION_SCRIPT]
    )
    row["processed_outputs"] = ";".join(dict.fromkeys(processed_outputs))
    row["status"] = "processed"
    rows[matches[0]] = row
    _write_registry(registry, rows)


def lookup_source(source_id: str, registry: Path = SOURCE_REGISTRY) -> dict[str, str]:
    matches = [row for row in _read_registry(registry) if row["source_id"] == source_id]
    if len(matches) != 1:
        raise ValueError(f"expected one registry row for {source_id}, found {len(matches)}")
    row = matches[0]
    for field in ("local_raw_path", "sha256"):
        if not row.get(field):
            raise ValueError(f"registry row {source_id} lacks {field}")
    return row


def resolve_raw_path(relative_path: str) -> Path:
    raw_path = (REPOSITORY_ROOT / relative_path).resolve()
    try:
        raw_path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise ValueError("registered raw path escapes the repository") from exc
    return raw_path


def layer_from_source_id(source_id: str) -> str:
    match = re.fullmatch(r"jartic_(1h|5m)_.+", source_id)
    if not match:
        raise ValueError(f"cannot determine JARTIC layer from source id: {source_id}")
    return match.group(1)


def run(source_id: str) -> tuple[Path, Path, dict[str, Any]]:
    source = lookup_source(source_id)
    raw_path = resolve_raw_path(source["local_raw_path"])
    payload, raw_sha256 = verify_raw_source(raw_path, source["sha256"])
    observations = normalize_payload(
        payload,
        source_id=source_id,
        layer=layer_from_source_id(source_id),
    )
    summary = build_quality_summary(
        observations,
        source_id=source_id,
        raw_sha256=raw_sha256,
    )

    output_directory = PROCESSED_DATASETS["calibration"]
    observations_path = output_directory / f"{source_id}_observations.parquet"
    summary_path = output_directory / f"{source_id}_quality_summary.json"
    write_outputs(
        observations,
        summary,
        observations_path=observations_path,
        summary_path=summary_path,
    )
    relative_outputs = [
        observations_path.relative_to(REPOSITORY_ROOT).as_posix(),
        summary_path.relative_to(REPOSITORY_ROOT).as_posix(),
    ]
    mark_source_processed(
        SOURCE_REGISTRY,
        source_id=source_id,
        processed_outputs=relative_outputs,
    )
    return observations_path, summary_path, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize a registered JARTIC snapshot for calibration."
    )
    parser.add_argument("--source-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        observations_path, summary_path, summary = run(args.source_id)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"normalized rows: {summary['normalized_row_count']}")
    print(f"valid rows: {summary['valid_row_count']}")
    print(f"invalid rows: {summary['invalid_row_count']}")
    print(f"observations: {observations_path.relative_to(REPOSITORY_ROOT)}")
    print(f"quality summary: {summary_path.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
