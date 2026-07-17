"""Acquire an immutable Geofabrik Kantō PBF and extract a governed study area.

The formal workflow intentionally supports only a dated PBF source.  It does not
fall back to Overpass or accept a user-supplied bounding box.  The bounding box
is always derived from the registered N03 study-area boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final, Mapping, Sequence
from zoneinfo import ZoneInfo

import requests

from traffic_simulation.network.study_areas import StudyArea, load_study_area
from traffic_simulation.paths import (
    PROCESSED_DATASETS,
    RAW_DATASETS,
    REPOSITORY_ROOT,
    SOURCE_REGISTRY,
)


GEOFABRIK_JAPAN_ROOT: Final = "https://download.geofabrik.de/asia/japan"
PROCESSING_SCRIPT: Final = "05_src/traffic_simulation/network/fetch_osm.py"
LICENSE: Final = "Open Database License (ODbL) 1.0"
JST: Final = ZoneInfo("Asia/Tokyo")
SNAPSHOT_PATTERN: Final = re.compile(r"^\d{8}$")
SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
# Osmium 1.15 serializes header bounds at seven decimal places.  This tolerance
# accepts only that representation difference; it does not expand the extract.
PBF_BBOX_TOLERANCE_DEGREES: Final = 5e-8
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


@dataclass(frozen=True, slots=True)
class PbfConfig:
    """Validated parameters for one dated Kantō snapshot and local extract."""

    region_id: str
    snapshot_date: date
    timeout: float = 120.0
    osmium_command: str = "osmium"

    @property
    def compact_date(self) -> str:
        return self.snapshot_date.strftime("%Y%m%d")

    @property
    def geofabrik_date(self) -> str:
        return self.snapshot_date.strftime("%y%m%d")

    @property
    def source_id(self) -> str:
        return f"osm_geofabrik_kanto_{self.compact_date}"

    @property
    def original_filename(self) -> str:
        return f"kanto-{self.geofabrik_date}.osm.pbf"

    @property
    def source_url(self) -> str:
        return f"{GEOFABRIK_JAPAN_ROOT}/{self.original_filename}"

    @property
    def raw_path(self) -> Path:
        return RAW_DATASETS["osm"] / self.original_filename

    @property
    def extract_path(self) -> Path:
        return (
            PROCESSED_DATASETS["road_network"]
            / "osm_extracts"
            / f"osm_{self.region_id}_{self.compact_date}.osm.pbf"
        )

    @property
    def summary_path(self) -> Path:
        return (
            PROCESSED_DATASETS["validation"]
            / f"osm_{self.region_id}_{self.compact_date}_quality_summary.json"
        )


@dataclass(frozen=True, slots=True)
class PbfInfo:
    """Normalized metadata reported by ``osmium fileinfo``."""

    node_count: int
    way_count: int
    relation_count: int
    header_bbox: tuple[float, float, float, float] | None
    data_timestamp: str | None


def parse_snapshot_date(value: str) -> date:
    """Parse an explicit YYYYMMDD snapshot date."""

    if not SNAPSHOT_PATTERN.fullmatch(value):
        raise ValueError("snapshot date must contain exactly 8 digits: YYYYMMDD")
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError(f"invalid snapshot date: {value}") from exc


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for a potentially large PBF."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside the repository: {path}") from exc


def _partial_path(path: Path) -> Path:
    return path.with_name(path.name + ".part")


def _read_registry(path: Path = SOURCE_REGISTRY) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
            raise ValueError(f"unexpected source-registry columns in {path}")
        rows = list(reader)
    source_ids = [row["source_id"] for row in rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id in source registry")
    return rows


def _registered_row(
    source_id: str, path: Path = SOURCE_REGISTRY
) -> dict[str, str] | None:
    matches = [row for row in _read_registry(path) if row["source_id"] == source_id]
    if len(matches) > 1:
        raise ValueError(f"duplicate registry rows for {source_id}")
    return matches[0] if matches else None


def _verify_registered_hash(
    config: PbfConfig, digest: str, registry_path: Path = SOURCE_REGISTRY
) -> None:
    row = _registered_row(config.source_id, registry_path)
    if row is None:
        return
    registered = row.get("sha256", "")
    if not SHA256_PATTERN.fullmatch(registered):
        raise ValueError(f"registry row {config.source_id} has an invalid SHA-256")
    if registered != digest:
        raise ValueError(
            f"registered PBF hash mismatch for {config.raw_path}: "
            f"{digest} != {registered}"
        )


def download_pbf(
    config: PbfConfig,
    *,
    session: requests.Session | None = None,
    registry_path: Path = SOURCE_REGISTRY,
) -> tuple[str, PbfInfo, bool]:
    """Validate an existing raw PBF or atomically download a dated snapshot."""

    destination = config.raw_path
    if destination.exists():
        if not destination.is_file():
            raise ValueError(f"raw PBF path is not a file: {destination}")
        digest = sha256_file(destination)
        _verify_registered_hash(config, digest, registry_path)
        return digest, inspect_pbf(destination, config.osmium_command), False

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = _partial_path(destination)
    if partial.exists():
        partial.unlink()

    client = session or requests.Session()
    owns_session = session is None
    committed = False
    try:
        with client.get(
            config.source_url,
            stream=True,
            timeout=config.timeout,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            expected_length = response.headers.get("Content-Length")
            expected_size = int(expected_length) if expected_length else None
            if expected_size is not None and expected_size <= 0:
                raise ValueError("PBF response declares an invalid Content-Length")

            digest_builder = hashlib.sha256()
            downloaded_size = 0
            with partial.open("xb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest_builder.update(chunk)
                    downloaded_size += len(chunk)

        if downloaded_size == 0:
            raise ValueError("downloaded PBF is empty")
        if expected_size is not None and downloaded_size != expected_size:
            raise ValueError(
                "PBF download size mismatch: "
                f"{downloaded_size} != {expected_size}"
            )
        digest = digest_builder.hexdigest()
        _verify_registered_hash(config, digest, registry_path)
        info = inspect_pbf(partial, config.osmium_command)
        os.replace(partial, destination)
        committed = True
        return digest, info, True
    finally:
        if not committed and partial.exists():
            partial.unlink()
        if owns_session:
            client.close()


def _run_osmium(
    command: Sequence[str], *, capture_output: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "osmium was not found; install osmium-tool in the analysis environment"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"osmium command failed{suffix}") from exc


def osmium_version(command: str = "osmium") -> str:
    """Return the first line of the installed osmium version output."""

    completed = _run_osmium([command, "--version"])
    line = completed.stdout.splitlines()[0].strip() if completed.stdout else ""
    if not line:
        raise ValueError("osmium --version returned no version information")
    return line


def _coerce_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} is not an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not an integer") from exc
    if result < 0:
        raise ValueError(f"{label} is negative")
    return result


def _parse_header_bbox(
    header: Mapping[str, Any],
) -> tuple[float, float, float, float] | None:
    boxes = header.get("boxes")
    if not boxes:
        return None
    if (
        not isinstance(boxes, list)
        or not isinstance(boxes[0], list)
        or len(boxes[0]) != 4
    ):
        raise ValueError("osmium fileinfo returned an invalid bounding box")
    west, south, east, north = (float(value) for value in boxes[0])
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("osmium fileinfo returned out-of-range bounds")
    return west, south, east, north


def parse_fileinfo(payload: Mapping[str, Any]) -> PbfInfo:
    """Normalize the stable fields needed from ``osmium fileinfo -e -j``."""

    data = payload.get("data")
    header = payload.get("header")
    if not isinstance(data, Mapping) or not isinstance(header, Mapping):
        raise ValueError("osmium fileinfo JSON lacks data or header metadata")
    counts = data.get("count")
    if not isinstance(counts, Mapping):
        raise ValueError("osmium fileinfo JSON lacks element counts")

    options = header.get("option", {})
    if not isinstance(options, Mapping):
        raise ValueError("osmium fileinfo JSON has invalid header options")
    timestamp = options.get("osmosis_replication_timestamp")
    if timestamp is not None and not isinstance(timestamp, str):
        raise ValueError("osmium fileinfo returned an invalid replication timestamp")
    return PbfInfo(
        node_count=_coerce_nonnegative_int(counts.get("nodes"), "node count"),
        way_count=_coerce_nonnegative_int(counts.get("ways"), "way count"),
        relation_count=_coerce_nonnegative_int(
            counts.get("relations"), "relation count"
        ),
        header_bbox=_parse_header_bbox(header),
        data_timestamp=timestamp,
    )


def inspect_pbf(path: Path, command: str = "osmium") -> PbfInfo:
    """Validate a PBF with osmium and return extended element counts."""

    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"PBF is missing or empty: {path}")
    completed = _run_osmium(
        [
            command,
            "fileinfo",
            "--extended",
            "--json",
            "--no-crc",
            "--input-format",
            "pbf",
            str(path),
        ]
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("osmium fileinfo did not return valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("osmium fileinfo returned a non-object JSON document")
    info = parse_fileinfo(payload)
    if info.node_count == 0 or info.way_count == 0:
        raise ValueError("PBF contains no nodes or ways")
    return info


def count_highway_ways(path: Path, command: str = "osmium") -> int:
    """Count ways carrying a highway tag without writing another extract."""

    completed = _run_osmium(
        [
            command,
            "tags-filter",
            "--input-format",
            "pbf",
            "--omit-referenced",
            "--output-format",
            "opl",
            str(path),
            "w/highway",
        ]
    )
    total = sum(1 for line in completed.stdout.splitlines() if line.startswith("w"))
    if total <= 0:
        raise ValueError("PBF extract contains no highway-tagged ways")
    return total


def bbox_text(area: StudyArea) -> str:
    """Format the governed WGS84 BBOX without rounding its stored values."""

    return ",".join(format(value, ".15g") for value in area.acquisition_bbox)


def extract_pbf(
    config: PbfConfig,
    area: StudyArea,
    *,
    source_digest: str,
    osmium: str | None = None,
) -> tuple[PbfInfo, int, str, bool]:
    """Create or validate an atomic ``complete_ways`` BBOX extract."""

    command = osmium or config.osmium_command
    destination = config.extract_path
    summary_path = config.summary_path

    if destination.exists() != summary_path.exists():
        raise ValueError(
            "OSM extract and quality summary must either both exist or both be absent"
        )
    if destination.exists():
        summary = load_summary(summary_path)
        digest = sha256_file(destination)
        _validate_existing_summary(summary, config, area, source_digest, digest)
        info = inspect_pbf(destination, command)
        highway_way_count = count_highway_ways(destination, command)
        return info, highway_way_count, digest, False

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = _partial_path(destination)
    if partial.exists():
        partial.unlink()

    committed = False
    try:
        _run_osmium(
            [
                command,
                "extract",
                "--bbox",
                bbox_text(area),
                "--strategy",
                "complete_ways",
                "--set-bounds",
                "--output-format",
                "pbf",
                "--output",
                str(partial),
                str(config.raw_path),
            ]
        )
        info = inspect_pbf(partial, command)
        if info.header_bbox is None:
            raise ValueError("PBF extract does not declare its extraction bounds")
        if any(
            abs(actual - expected) > PBF_BBOX_TOLERANCE_DEGREES
            for actual, expected in zip(info.header_bbox, area.acquisition_bbox)
        ):
            raise ValueError("PBF extract bounds do not match the governed BBOX")
        highway_way_count = count_highway_ways(partial, command)
        digest = sha256_file(partial)
        os.replace(partial, destination)
        committed = True
        return info, highway_way_count, digest, True
    finally:
        if not committed and partial.exists():
            partial.unlink()


def build_quality_summary(
    config: PbfConfig,
    area: StudyArea,
    raw_info: PbfInfo,
    extract_info: PbfInfo,
    highway_way_count: int,
    *,
    raw_digest: str,
    extract_digest: str,
    osmium_version_text: str,
) -> dict[str, Any]:
    """Build provenance and structural checks for one PBF extraction."""

    west, south, east, north = area.acquisition_bbox
    return {
        "schema_version": 1,
        "source_id": config.source_id,
        "source_url": config.source_url,
        "snapshot_date": config.snapshot_date.isoformat(),
        "region_id": area.region_id,
        "study_area_version": area.version,
        "boundary_source_registry_id": area.source_registry_id,
        "boundary_raw_sha256": area.raw_sha256,
        "acquisition_bbox": {
            "west": west,
            "south": south,
            "east": east,
            "north": north,
        },
        "extraction_strategy": "complete_ways",
        "osmium_version": osmium_version_text,
        "raw_path": _relative_path(config.raw_path),
        "raw_sha256": raw_digest,
        "raw_size_bytes": config.raw_path.stat().st_size,
        "raw_data_timestamp": raw_info.data_timestamp,
        "raw_counts": {
            "nodes": raw_info.node_count,
            "ways": raw_info.way_count,
            "relations": raw_info.relation_count,
        },
        "raw_header_bbox": raw_info.header_bbox,
        "extract_path": _relative_path(config.extract_path),
        "extract_sha256": extract_digest,
        "extract_size_bytes": config.extract_path.stat().st_size,
        "extract_data_timestamp": extract_info.data_timestamp,
        "extract_counts": {
            "nodes": extract_info.node_count,
            "ways": extract_info.way_count,
            "relations": extract_info.relation_count,
            "highway_ways": highway_way_count,
        },
        "extract_header_bbox": extract_info.header_bbox,
        "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
    }


def load_summary(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"quality summary is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"quality summary is not an object: {path}")
    return payload


def _validate_existing_summary(
    summary: Mapping[str, Any],
    config: PbfConfig,
    area: StudyArea,
    raw_digest: str,
    extract_digest: str,
) -> None:
    expected_bbox = {
        "west": area.west,
        "south": area.south,
        "east": area.east,
        "north": area.north,
    }
    expected = {
        "source_id": config.source_id,
        "region_id": area.region_id,
        "study_area_version": area.version,
        "boundary_raw_sha256": area.raw_sha256,
        "acquisition_bbox": expected_bbox,
        "extraction_strategy": "complete_ways",
        "raw_sha256": raw_digest,
        "extract_sha256": extract_digest,
    }
    mismatches = [key for key, value in expected.items() if summary.get(key) != value]
    if mismatches:
        raise ValueError(
            "existing OSM quality summary does not match current inputs: "
            + ", ".join(mismatches)
        )


def write_summary(summary: Mapping[str, Any], destination: Path) -> None:
    """Atomically write a new summary without replacing existing evidence."""

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite quality summary: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = _partial_path(destination)
    if partial.exists():
        partial.unlink()
    committed = False
    try:
        partial.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(partial, destination)
        committed = True
    finally:
        if not committed and partial.exists():
            partial.unlink()


def registry_row(
    config: PbfConfig,
    area: StudyArea,
    summary: Mapping[str, Any],
) -> dict[str, str]:
    """Create the source-registry row for the raw PBF and its local extract."""

    west, south, east, north = area.acquisition_bbox
    data_timestamp = summary.get("raw_data_timestamp")
    observation = (
        str(data_timestamp) if data_timestamp else config.snapshot_date.isoformat()
    )
    return {
        "source_id": config.source_id,
        "dataset_name": "Geofabrik OpenStreetMap Kantō regional extract",
        "provider": "Geofabrik GmbH / OpenStreetMap contributors",
        "source_url": config.source_url,
        "downloaded_at": datetime.now(JST).date().isoformat(),
        "observation_start": observation,
        "observation_end": observation,
        "geographic_scope": (
            "Kantō source; "
            f"{area.region_id} bbox {west:.9f} {south:.9f} {east:.9f} {north:.9f}"
        ),
        "license_or_terms": LICENSE,
        "original_filename": config.original_filename,
        "local_raw_path": _relative_path(config.raw_path),
        "sha256": str(summary["raw_sha256"]),
        "processing_script": PROCESSING_SCRIPT,
        "processed_outputs": ";".join(
            (_relative_path(config.extract_path), _relative_path(config.summary_path))
        ),
        "status": "processed",
        "limitations": (
            "OpenStreetMap completeness and tag accuracy vary; the local network is "
            "limited to the N03-derived acquisition BBOX; routes outside the BBOX are "
            "not represented; signal timing plans are not included"
        ),
    }


def upsert_registry(
    row: Mapping[str, str], registry: Path = SOURCE_REGISTRY
) -> None:
    """Atomically register one immutable raw PBF without allowing hash drift."""

    missing = set(REGISTRY_FIELDS) - set(row)
    unknown = set(row) - set(REGISTRY_FIELDS)
    if missing or unknown:
        raise ValueError(
            f"invalid registry row fields; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )
    rows = _read_registry(registry)
    replacement = dict(row)
    replaced = False
    for index, current in enumerate(rows):
        if current["source_id"] != replacement["source_id"]:
            continue
        if current.get("sha256") != replacement["sha256"]:
            raise ValueError(
                f"registry hash conflict for {replacement['source_id']}: "
                f"{current.get('sha256')} != {replacement['sha256']}"
            )
        replacement["downloaded_at"] = (
            current.get("downloaded_at") or replacement["downloaded_at"]
        )
        rows[index] = replacement
        replaced = True
        break
    if not replaced:
        rows.append(replacement)

    registry.parent.mkdir(parents=True, exist_ok=True)
    partial = _partial_path(registry)
    if partial.exists():
        partial.unlink()
    try:
        with partial.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=REGISTRY_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(partial, registry)
    finally:
        if partial.exists():
            partial.unlink()


def run(config: PbfConfig) -> tuple[dict[str, Any], bool, bool]:
    """Download, validate, extract, summarize, and register one OSM snapshot."""

    area = load_study_area(config.region_id)
    version = osmium_version(config.osmium_command)
    raw_digest, raw_info, downloaded = download_pbf(config)

    extract_info, highway_way_count, extract_digest, extracted = extract_pbf(
        config,
        area,
        source_digest=raw_digest,
    )
    if extracted:
        summary = build_quality_summary(
            config,
            area,
            raw_info,
            extract_info,
            highway_way_count,
            raw_digest=raw_digest,
            extract_digest=extract_digest,
            osmium_version_text=version,
        )
        try:
            write_summary(summary, config.summary_path)
        except Exception:
            config.extract_path.unlink(missing_ok=True)
            raise
    else:
        summary = load_summary(config.summary_path)

    upsert_registry(registry_row(config, area, summary))
    return summary, downloaded, extracted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire a dated Geofabrik Kantō PBF and extract a governed "
            "study-area BBOX."
        )
    )
    parser.add_argument("--region", required=True, help="Governed study-area ID")
    parser.add_argument(
        "--snapshot-date",
        required=True,
        help="Available Geofabrik snapshot date as YYYYMMDD",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP connection/read timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--osmium-command",
        default="osmium",
        help="osmium executable name or path (default: osmium)",
    )
    return parser


def config_from_args(args: argparse.Namespace) -> PbfConfig:
    if args.timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if not args.osmium_command or not str(args.osmium_command).strip():
        raise ValueError("osmium command must not be empty")
    if Path(str(args.osmium_command)).name != str(args.osmium_command):
        resolved = Path(str(args.osmium_command)).expanduser()
        if not resolved.is_absolute():
            raise ValueError("osmium command path must be absolute")
    return PbfConfig(
        region_id=args.region,
        snapshot_date=parse_snapshot_date(args.snapshot_date),
        timeout=float(args.timeout),
        osmium_command=str(args.osmium_command),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = config_from_args(args)
        summary, downloaded, extracted = run(config)
    except (
        OSError,
        RuntimeError,
        ValueError,
        requests.RequestException,
        subprocess.SubprocessError,
    ) as exc:
        parser.exit(1, f"error: {exc}\n")

    bbox = summary["acquisition_bbox"]
    print(f"raw PBF: {'downloaded' if downloaded else 'validated existing'}")
    print(f"BBOX extract: {'created' if extracted else 'validated existing'}")
    print(
        "acquisition bbox: "
        f"{bbox['west']:.9f},{bbox['south']:.9f},"
        f"{bbox['east']:.9f},{bbox['north']:.9f}"
    )
    print(f"raw sha256: {summary['raw_sha256']}")
    print(f"extract sha256: {summary['extract_sha256']}")
    print(f"raw path: {summary['raw_path']}")
    print(f"extract path: {summary['extract_path']}")
    print(f"quality summary: {_relative_path(config.summary_path)}")
    print(f"registry: {_relative_path(SOURCE_REGISTRY)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
