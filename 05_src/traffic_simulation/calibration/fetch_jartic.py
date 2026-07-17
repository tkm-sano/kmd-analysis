"""Fetch and register immutable JARTIC traffic-volume API snapshots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Final, Sequence

import requests

from traffic_simulation.paths import RAW_DATASETS, REPOSITORY_ROOT, SOURCE_REGISTRY


BASE_URL: Final = "https://api.jartic-open-traffic.org/geoserver"
SOURCE_URL: Final = "https://www.jartic-open-traffic.org/"
JST: Final = timezone(timedelta(hours=9))
LAYERS: Final = {
    "1h": "t_travospublic_measure_1h",
    "5m": "t_travospublic_measure_5m",
}
ROAD_TYPES: Final = {"1", "3"}
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


@dataclass(frozen=True)
class FetchConfig:
    """Validated parameters for one immutable API snapshot."""

    layer: str
    road_type: str
    time_code: str
    bbox: tuple[float, float, float, float]
    area_label: str
    timeout: float

    @property
    def type_name(self) -> str:
        return LAYERS[self.layer]

    @property
    def source_id(self) -> str:
        return f"jartic_{self.layer}_road{self.road_type}_{self.area_label}_{self.time_code}"

    @property
    def filename(self) -> str:
        return f"{self.source_id}.geojson"


def parse_time_code(value: str, layer: str) -> datetime:
    """Validate a JARTIC YYYYMMDDhhmm time code and return it in JST."""

    if not re.fullmatch(r"\d{12}", value):
        raise ValueError("time code must contain exactly 12 digits: YYYYMMDDhhmm")
    try:
        observed_at = datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=JST)
    except ValueError as exc:
        raise ValueError(f"invalid calendar time code: {value}") from exc

    if layer == "1h" and observed_at.minute != 0:
        raise ValueError("a 1h time code must end in minute 00")
    if layer == "5m" and observed_at.minute % 5 != 0:
        raise ValueError("a 5m time-code minute must be a multiple of 5")
    return observed_at


def validate_bbox(values: Sequence[float]) -> tuple[float, float, float, float]:
    """Validate a WGS84 bounding box ordered west, south, east, north."""

    if len(values) != 4:
        raise ValueError("bbox requires four values: west south east north")
    west, south, east, north = (float(value) for value in values)
    if not (-180 <= west < east <= 180):
        raise ValueError("bbox longitudes must satisfy -180 <= west < east <= 180")
    if not (-90 <= south < north <= 90):
        raise ValueError("bbox latitudes must satisfy -90 <= south < north <= 90")
    return west, south, east, north


def build_cql_filter(config: FetchConfig) -> str:
    """Build the CQL syntax accepted by the public JARTIC endpoint."""

    bbox = ",".join(format(value, ".12g") for value in config.bbox)
    # The live endpoint rejects quoted Japanese identifiers in this expression.
    return (
        f"道路種別={config.road_type} AND 時間コード={config.time_code} "
        f"AND BBOX(ジオメトリ,{bbox},'EPSG:4326')"
    )


def build_request_params(config: FetchConfig) -> dict[str, str]:
    """Return the WFS 2.0 query parameters for a snapshot."""

    return {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": config.type_name,
        "srsName": "EPSG:4326",
        "outputFormat": "application/json",
        "exceptions": "application/json",
        "cql_filter": build_cql_filter(config),
    }


def validate_feature_collection(payload: Any, config: FetchConfig) -> dict[str, Any]:
    """Reject API errors, empty results, and records outside the query."""

    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("JARTIC response is not a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("JARTIC response contains no features")

    reported = payload.get("numberReturned")
    if reported is not None and int(reported) != len(features):
        raise ValueError(
            f"numberReturned={reported} does not match feature count={len(features)}"
        )

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ValueError(f"feature {index} is not an object")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise ValueError(f"feature {index} lacks properties or geometry")
        if str(properties.get("時間コード", "")) != config.time_code:
            raise ValueError(f"feature {index} has an unexpected time code")
        if str(properties.get("道路種別", "")) != config.road_type:
            raise ValueError(f"feature {index} has an unexpected road type")
        if geometry.get("type") != "MultiPoint" or not geometry.get("coordinates"):
            raise ValueError(f"feature {index} lacks a JARTIC MultiPoint geometry")
    return payload


def load_and_validate(raw_bytes: bytes, config: FetchConfig) -> dict[str, Any]:
    """Decode and validate raw response bytes without modifying them."""

    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JARTIC response is not valid UTF-8 JSON") from exc
    return validate_feature_collection(payload, config)


def sha256_bytes(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def fetch_snapshot(config: FetchConfig, destination: Path) -> tuple[dict[str, Any], str, bool]:
    """Validate an existing snapshot or atomically fetch a new one.

    Returns the payload, SHA-256 digest, and whether a new file was downloaded.
    """

    if destination.exists():
        raw_bytes = destination.read_bytes()
        payload = load_and_validate(raw_bytes, config)
        return payload, sha256_bytes(raw_bytes), False

    response = requests.get(
        BASE_URL,
        params=build_request_params(config),
        timeout=config.timeout,
    )
    response.raise_for_status()
    raw_bytes = response.content
    payload = load_and_validate(raw_bytes, config)

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if partial.exists():
        partial.unlink()
    committed = False
    try:
        partial.write_bytes(raw_bytes)
        os.replace(partial, destination)
        committed = True
    finally:
        if not committed and partial.exists():
            partial.unlink()
    return payload, sha256_bytes(raw_bytes), True


def observation_interval(config: FetchConfig) -> tuple[str, str]:
    start = parse_time_code(config.time_code, config.layer)
    duration = timedelta(hours=1) if config.layer == "1h" else timedelta(minutes=5)
    end = start + duration - timedelta(seconds=1)
    return start.isoformat(), end.isoformat()


def registry_row(config: FetchConfig, destination: Path, digest: str) -> dict[str, str]:
    start, end = observation_interval(config)
    relative_path = destination.relative_to(REPOSITORY_ROOT).as_posix()
    script_path = Path(__file__).resolve().relative_to(REPOSITORY_ROOT).as_posix()
    interval_name = "1時間" if config.layer == "1h" else "5分"
    west, south, east, north = config.bbox
    return {
        "source_id": config.source_id,
        "dataset_name": f"JARTIC常設トラカン{interval_name}交通量",
        "provider": "JARTIC / MLIT xROAD",
        "source_url": SOURCE_URL,
        "downloaded_at": datetime.now(JST).date().isoformat(),
        "observation_start": start,
        "observation_end": end,
        "geographic_scope": (
            f"{config.area_label} bbox {west:g} {south:g} {east:g} {north:g}"
        ),
        "license_or_terms": "JARTIC traffic-volume API terms",
        "original_filename": destination.name,
        "local_raw_path": relative_path,
        "sha256": digest,
        "processing_script": script_path,
        "processed_outputs": "",
        "status": "raw_acquired",
        "limitations": (
            f"Road type {config.road_type} only; one {config.layer} snapshot; "
            "sensor anomaly and missing-data flags require validation"
        ),
    }


def upsert_registry(row: dict[str, str], registry: Path = SOURCE_REGISTRY) -> None:
    """Atomically insert or update one source row without allowing hash drift."""

    existing: list[dict[str, str]] = []
    if registry.exists():
        with registry.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
                raise ValueError(f"unexpected source-registry columns in {registry}")
            existing = list(reader)

    replaced = False
    for index, current in enumerate(existing):
        if current.get("source_id") != row["source_id"]:
            continue
        old_digest = current.get("sha256", "")
        if old_digest and old_digest != row["sha256"]:
            raise ValueError(
                f"registry hash conflict for {row['source_id']}: "
                f"{old_digest} != {row['sha256']}"
            )
        row["downloaded_at"] = current.get("downloaded_at") or row["downloaded_at"]
        scripts = [
            value
            for value in (
                current.get("processing_script", "") + ";" + row["processing_script"]
            ).split(";")
            if value
        ]
        row["processing_script"] = ";".join(dict.fromkeys(scripts))
        if current.get("processed_outputs"):
            row["processed_outputs"] = current["processed_outputs"]
            row["status"] = current.get("status") or row["status"]
        existing[index] = row
        replaced = True
        break
    if not replaced:
        existing.append(row)

    registry.parent.mkdir(parents=True, exist_ok=True)
    partial = registry.with_name(registry.name + ".part")
    try:
        with partial.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=REGISTRY_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(existing)
        os.replace(partial, registry)
    finally:
        if partial.exists():
            partial.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch and register one immutable JARTIC traffic-volume snapshot."
    )
    parser.add_argument("--layer", choices=tuple(LAYERS), required=True)
    parser.add_argument("--road-type", choices=tuple(sorted(ROAD_TYPES)), required=True)
    parser.add_argument("--time-code", required=True, help="JST time as YYYYMMDDhhmm")
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        required=True,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    parser.add_argument(
        "--area-label",
        default="tokyo",
        help="safe filename label for the requested area (default: tokyo)",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def config_from_args(args: argparse.Namespace) -> FetchConfig:
    if not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", args.area_label):
        raise ValueError("area label may contain lowercase letters, digits, '-' and '_'")
    if args.timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    parse_time_code(args.time_code, args.layer)
    return FetchConfig(
        layer=args.layer,
        road_type=args.road_type,
        time_code=args.time_code,
        bbox=validate_bbox(args.bbox),
        area_label=args.area_label,
        timeout=args.timeout,
    )


def run(config: FetchConfig) -> tuple[Path, int, str, bool]:
    destination = RAW_DATASETS["jartic"] / config.filename
    payload, digest, downloaded = fetch_snapshot(config, destination)
    upsert_registry(registry_row(config, destination, digest))
    return destination, len(payload["features"]), digest, downloaded


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = config_from_args(args)
        destination, feature_count, digest, downloaded = run(config)
    except (OSError, ValueError, requests.RequestException) as exc:
        parser.exit(1, f"error: {exc}\n")

    action = "downloaded" if downloaded else "validated existing"
    print(f"JARTIC snapshot: {action}")
    print(f"features: {feature_count}")
    print(f"sha256: {digest}")
    print(f"raw path: {destination.relative_to(REPOSITORY_ROOT)}")
    print(f"registry: {SOURCE_REGISTRY.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
