from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import requests

from traffic_simulation.network import fetch_osm


TEST_BBOX = (139.652974773, 35.528198081, 139.826027782, 35.613210171)


@pytest.fixture
def runtime_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    paths = {
        "root": tmp_path,
        "raw": tmp_path / "03_data/raw/traffic_simulation/osm",
        "road_network": tmp_path / "03_data/processed/traffic_simulation/road_network",
        "validation": tmp_path / "03_data/processed/traffic_simulation/validation",
        "registry": tmp_path / "03_data/metadata/traffic_simulation_sources.csv",
    }
    monkeypatch.setattr(fetch_osm, "REPOSITORY_ROOT", paths["root"])
    monkeypatch.setattr(fetch_osm, "RAW_DATASETS", {"osm": paths["raw"]})
    monkeypatch.setattr(
        fetch_osm,
        "PROCESSED_DATASETS",
        {
            "road_network": paths["road_network"],
            "validation": paths["validation"],
        },
    )
    monkeypatch.setattr(fetch_osm, "SOURCE_REGISTRY", paths["registry"])
    return paths


def make_config(**overrides: Any) -> fetch_osm.PbfConfig:
    values: dict[str, Any] = {
        "region_id": "ota_ward",
        "snapshot_date": date(2026, 7, 16),
        "timeout": 120.0,
        "osmium_command": "osmium",
    }
    values.update(overrides)
    return fetch_osm.PbfConfig(**values)


def make_area(
    bbox: tuple[float, float, float, float] = TEST_BBOX,
) -> SimpleNamespace:
    west, south, east, north = bbox
    return SimpleNamespace(
        region_id="ota_ward",
        version=1,
        source_registry_id="mlit_n03_2026_tokyo",
        raw_sha256="a" * 64,
        acquisition_bbox=bbox,
        west=west,
        south=south,
        east=east,
        north=north,
    )


def make_info(
    *,
    bbox: tuple[float, float, float, float] | None = TEST_BBOX,
    nodes: int = 10,
    ways: int = 3,
    relations: int = 1,
) -> fetch_osm.PbfInfo:
    return fetch_osm.PbfInfo(
        node_count=nodes,
        way_count=ways,
        relation_count=relations,
        header_bbox=bbox,
        data_timestamp="2026-07-16T20:21:30Z",
    )


def completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")


class FakeResponse:
    def __init__(
        self,
        content: bytes,
        *,
        error: requests.RequestException | None = None,
        declared_size: int | None = None,
    ) -> None:
        self.content = content
        self.error = error
        size = len(content) if declared_size is None else declared_size
        self.headers = {"Content-Length": str(size)}

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error

    def iter_content(self, chunk_size: int) -> list[bytes]:
        return [
            self.content[index : index + chunk_size]
            for index in range(0, len(self.content), chunk_size)
        ]


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.response


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fetch_osm.REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def blank_registry_row(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in fetch_osm.REGISTRY_FIELDS}
    row.update(overrides)
    return row


def test_dated_geofabrik_identity_and_paths(runtime_paths: dict[str, Path]) -> None:
    config = make_config()

    assert config.source_id == "osm_geofabrik_kanto_20260716"
    assert config.original_filename == "kanto-260716.osm.pbf"
    assert config.source_url == (
        "https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf"
    )
    assert config.raw_path == runtime_paths["raw"] / "kanto-260716.osm.pbf"
    assert config.extract_path.name == "osm_ota_ward_20260716.osm.pbf"
    assert config.summary_path.name.endswith("_quality_summary.json")


@pytest.mark.parametrize("value", ["202607", "2026-07-16", "20260230", "abcdefgh"])
def test_parse_snapshot_date_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        fetch_osm.parse_snapshot_date(value)


def test_cli_has_governed_region_but_no_bbox_or_source_switch() -> None:
    parser = fetch_osm.build_parser()
    destinations = {action.dest for action in parser._actions}

    assert "region" in destinations
    assert "snapshot_date" in destinations
    assert "bbox" not in destinations
    assert "source_url" not in destinations
    assert "source" not in destinations


def test_config_from_args_rejects_nonpositive_timeout() -> None:
    parser = fetch_osm.build_parser()
    args = parser.parse_args(
        ["--region", "ota_ward", "--snapshot-date", "20260716", "--timeout", "0"]
    )

    with pytest.raises(ValueError, match="timeout"):
        fetch_osm.config_from_args(args)


def test_bbox_text_preserves_governed_coordinates() -> None:
    assert fetch_osm.bbox_text(make_area()) == (
        "139.652974773,35.528198081,139.826027782,35.613210171"
    )


def test_parse_fileinfo_normalizes_counts_bounds_and_timestamp() -> None:
    info = fetch_osm.parse_fileinfo(
        {
            "header": {
                "boxes": [[139.6, 35.5, 139.8, 35.7]],
                "option": {
                    "osmosis_replication_timestamp": "2026-07-16T20:21:30Z"
                },
            },
            "data": {
                "count": {"nodes": 100, "ways": 20, "relations": 4}
            },
        }
    )

    assert info == fetch_osm.PbfInfo(
        node_count=100,
        way_count=20,
        relation_count=4,
        header_bbox=(139.6, 35.5, 139.8, 35.7),
        data_timestamp="2026-07-16T20:21:30Z",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"header": {}, "data": {}},
        {"header": {"boxes": []}, "data": {"count": {"nodes": -1}}},
        {
            "header": {"boxes": [[140.0, 36.0, 139.0, 35.0]]},
            "data": {"count": {"nodes": 1, "ways": 1, "relations": 0}},
        },
    ],
)
def test_parse_fileinfo_rejects_incomplete_or_invalid_metadata(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        fetch_osm.parse_fileinfo(payload)


def test_inspect_pbf_rejects_empty_elements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "empty.osm.pbf"
    path.write_bytes(b"pbf")
    payload = {
        "header": {"boxes": [], "option": {}},
        "data": {"count": {"nodes": 0, "ways": 0, "relations": 0}},
    }
    monkeypatch.setattr(
        fetch_osm,
        "_run_osmium",
        lambda command: completed(json.dumps(payload)),
    )

    with pytest.raises(ValueError, match="no nodes or ways"):
        fetch_osm.inspect_pbf(path)


def test_count_highway_ways_uses_way_only_filter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "extract.osm.pbf"
    path.write_bytes(b"pbf")
    captured: list[str] = []

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        captured.extend(command)
        return completed("w1 v1 Thighway=residential\nw2 v1 Thighway=primary\n")

    monkeypatch.setattr(fetch_osm, "_run_osmium", fake_run)

    assert fetch_osm.count_highway_ways(path) == 2
    assert "--omit-referenced" in captured
    assert "w/highway" in captured


def test_count_highway_ways_rejects_extract_without_roads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "extract.osm.pbf"
    path.write_bytes(b"pbf")
    monkeypatch.setattr(fetch_osm, "_run_osmium", lambda command: completed(""))

    with pytest.raises(ValueError, match="no highway-tagged ways"):
        fetch_osm.count_highway_ways(path)


def test_download_is_atomic_and_validated_before_commit(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    raw_bytes = b"valid mocked pbf"
    session = FakeSession(FakeResponse(raw_bytes))
    monkeypatch.setattr(fetch_osm, "inspect_pbf", lambda path, command: make_info())

    digest, info, downloaded = fetch_osm.download_pbf(
        config,
        session=session,  # type: ignore[arg-type]
        registry_path=runtime_paths["registry"],
    )

    assert downloaded is True
    assert info == make_info()
    assert digest == hashlib.sha256(raw_bytes).hexdigest()
    assert config.raw_path.read_bytes() == raw_bytes
    assert not config.raw_path.with_name(config.raw_path.name + ".part").exists()
    assert session.calls[0][0] == config.source_url
    assert session.calls[0][1]["stream"] is True


def test_download_failure_removes_partial_file(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    session = FakeSession(FakeResponse(b"not a pbf"))

    def reject(path: Path, command: str) -> fetch_osm.PbfInfo:
        raise ValueError("invalid PBF")

    monkeypatch.setattr(fetch_osm, "inspect_pbf", reject)

    with pytest.raises(ValueError, match="invalid PBF"):
        fetch_osm.download_pbf(
            config,
            session=session,  # type: ignore[arg-type]
            registry_path=runtime_paths["registry"],
        )

    assert not config.raw_path.exists()
    assert not config.raw_path.with_name(config.raw_path.name + ".part").exists()


def test_existing_raw_pbf_must_match_registered_hash(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    config.raw_path.parent.mkdir(parents=True)
    config.raw_path.write_bytes(b"changed")
    write_registry(
        runtime_paths["registry"],
        [
            blank_registry_row(
                source_id=config.source_id,
                sha256=hashlib.sha256(b"original").hexdigest(),
            )
        ],
    )
    monkeypatch.setattr(fetch_osm, "inspect_pbf", lambda path, command: make_info())

    with pytest.raises(ValueError, match="hash mismatch"):
        fetch_osm.download_pbf(config, registry_path=runtime_paths["registry"])


def test_extract_uses_complete_ways_and_governed_bbox(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    area = make_area()
    config.raw_path.parent.mkdir(parents=True)
    config.raw_path.write_bytes(b"source")
    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(b"extracted")
        return completed()

    monkeypatch.setattr(fetch_osm, "_run_osmium", fake_run)
    monkeypatch.setattr(fetch_osm, "inspect_pbf", lambda path, command: make_info())
    monkeypatch.setattr(fetch_osm, "count_highway_ways", lambda path, command: 7)

    info, highway_count, digest, created = fetch_osm.extract_pbf(
        config,
        area,  # type: ignore[arg-type]
        source_digest="b" * 64,
    )

    assert created is True
    assert info == make_info()
    assert highway_count == 7
    assert digest == hashlib.sha256(b"extracted").hexdigest()
    assert config.extract_path.read_bytes() == b"extracted"
    command = commands[0]
    assert command[1] == "extract"
    assert command[command.index("--bbox") + 1] == fetch_osm.bbox_text(area)
    assert command[command.index("--strategy") + 1] == "complete_ways"
    assert "--set-bounds" in command
    partial = config.extract_path.with_name(config.extract_path.name + ".part")
    assert not partial.exists()


def test_extract_accepts_only_pbf_header_precision_difference(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    config.raw_path.parent.mkdir(parents=True)
    config.raw_path.write_bytes(b"source")
    rounded_bbox = (139.6529748, 35.5281981, 139.8260278, 35.6132102)

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(b"rounded header")
        return completed()

    monkeypatch.setattr(fetch_osm, "_run_osmium", fake_run)
    monkeypatch.setattr(
        fetch_osm,
        "inspect_pbf",
        lambda path, command: make_info(bbox=rounded_bbox),
    )
    monkeypatch.setattr(fetch_osm, "count_highway_ways", lambda path, command: 7)

    _, _, _, created = fetch_osm.extract_pbf(
        config,
        make_area(),  # type: ignore[arg-type]
        source_digest="b" * 64,
    )

    assert created is True


def test_extract_rejects_wrong_output_bounds_and_cleans_partial(
    runtime_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = make_config()
    config.raw_path.parent.mkdir(parents=True)
    config.raw_path.write_bytes(b"source")

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(b"wrong bounds")
        return completed()

    monkeypatch.setattr(fetch_osm, "_run_osmium", fake_run)
    monkeypatch.setattr(
        fetch_osm,
        "inspect_pbf",
        lambda path, command: make_info(bbox=(139.0, 35.0, 140.0, 36.0)),
    )

    with pytest.raises(ValueError, match="bounds"):
        fetch_osm.extract_pbf(
            config,
            make_area(),  # type: ignore[arg-type]
            source_digest="b" * 64,
        )

    assert not config.extract_path.exists()
    partial = config.extract_path.with_name(config.extract_path.name + ".part")
    assert not partial.exists()


def test_extract_refuses_incomplete_existing_output_pair(
    runtime_paths: dict[str, Path],
) -> None:
    config = make_config()
    config.extract_path.parent.mkdir(parents=True)
    config.extract_path.write_bytes(b"orphan")

    with pytest.raises(ValueError, match="both exist or both be absent"):
        fetch_osm.extract_pbf(
            config,
            make_area(),  # type: ignore[arg-type]
            source_digest="b" * 64,
        )


def test_quality_summary_records_provenance_and_road_count(
    runtime_paths: dict[str, Path],
) -> None:
    config = make_config()
    config.raw_path.parent.mkdir(parents=True)
    config.extract_path.parent.mkdir(parents=True)
    config.raw_path.write_bytes(b"raw")
    config.extract_path.write_bytes(b"extract")

    summary = fetch_osm.build_quality_summary(
        config,
        make_area(),  # type: ignore[arg-type]
        make_info(bbox=(138.0, 34.0, 141.0, 37.0), nodes=100, ways=30),
        make_info(nodes=20, ways=8),
        6,
        raw_digest="c" * 64,
        extract_digest="d" * 64,
        osmium_version_text="osmium version 1.15.0",
    )

    assert summary["acquisition_bbox"]["west"] == TEST_BBOX[0]
    assert summary["extraction_strategy"] == "complete_ways"
    assert summary["extract_counts"]["highway_ways"] == 6
    assert summary["raw_sha256"] == "c" * 64
    assert summary["extract_sha256"] == "d" * 64
    assert summary["osmium_version"] == "osmium version 1.15.0"


def test_write_summary_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "quality.json"
    fetch_osm.write_summary({"status": "ok"}, destination)

    assert json.loads(destination.read_text()) == {"status": "ok"}
    assert not destination.with_name("quality.json.part").exists()
    with pytest.raises(FileExistsError):
        fetch_osm.write_summary({"status": "changed"}, destination)


def test_registry_upsert_is_idempotent_and_rejects_hash_drift(
    runtime_paths: dict[str, Path],
) -> None:
    registry = runtime_paths["registry"]
    row = blank_registry_row(
        source_id="osm_geofabrik_kanto_20260716",
        downloaded_at="2026-07-17",
        sha256="e" * 64,
        status="processed",
    )

    fetch_osm.upsert_registry(row, registry)
    fetch_osm.upsert_registry(row, registry)
    with registry.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["sha256"] == "e" * 64

    changed = dict(row)
    changed["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="hash conflict"):
        fetch_osm.upsert_registry(changed, registry)
