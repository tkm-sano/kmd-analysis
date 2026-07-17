from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import requests

from traffic_simulation.calibration import fetch_jartic


def make_config(**overrides: object) -> fetch_jartic.FetchConfig:
    values: dict[str, object] = {
        "layer": "1h",
        "road_type": "3",
        "time_code": "202607042200",
        "bbox": (139.1, 35.45, 140.0, 35.95),
        "area_label": "tokyo",
        "timeout": 30.0,
    }
    values.update(overrides)
    return fetch_jartic.FetchConfig(**values)  # type: ignore[arg-type]


def make_payload(
    *, time_code: int = 202607042200, road_type: str = "3"
) -> dict[str, object]:
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "MultiPoint",
            "coordinates": [[139.7049058, 35.58550262]],
        },
        "properties": {
            "常時観測点コード": 3110010,
            "時間コード": time_code,
            "道路種別": road_type,
            "上り・小型交通量": 409,
            "下り・小型交通量": 481,
        },
    }
    return {
        "type": "FeatureCollection",
        "features": [feature],
        "numberReturned": 1,
    }


def payload_bytes(**overrides: object) -> bytes:
    return json.dumps(make_payload(**overrides), ensure_ascii=False).encode("utf-8")


class FakeResponse:
    def __init__(self, content: bytes, error: requests.RequestException | None = None):
        self.content = content
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error


def test_build_cql_filter_uses_live_endpoint_syntax() -> None:
    cql_filter = fetch_jartic.build_cql_filter(make_config())

    assert cql_filter == (
        "道路種別=3 AND 時間コード=202607042200 "
        "AND BBOX(ジオメトリ,139.1,35.45,140,35.95,'EPSG:4326')"
    )
    assert '"道路種別"' not in cql_filter
    assert "道路種別='3'" not in cql_filter


@pytest.mark.parametrize(
    ("layer", "time_code"),
    [
        ("1h", "202607042230"),
        ("5m", "202607042203"),
        ("1h", "2026070422"),
        ("1h", "202602302200"),
    ],
)
def test_parse_time_code_rejects_invalid_values(layer: str, time_code: str) -> None:
    with pytest.raises(ValueError):
        fetch_jartic.parse_time_code(time_code, layer)


@pytest.mark.parametrize(
    "bbox",
    [
        (140.0, 35.45, 139.1, 35.95),
        (139.1, 35.95, 140.0, 35.45),
        (-181.0, 35.45, 140.0, 35.95),
        (139.1, -91.0, 140.0, 35.95),
    ],
)
def test_validate_bbox_rejects_invalid_bounds(bbox: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        fetch_jartic.validate_bbox(bbox)


@pytest.mark.parametrize(
    "raw_bytes",
    [
        b"not json",
        json.dumps({"message": "bad request"}).encode(),
        json.dumps({"type": "FeatureCollection", "features": []}).encode(),
    ],
)
def test_load_and_validate_rejects_invalid_or_empty_responses(raw_bytes: bytes) -> None:
    with pytest.raises(ValueError):
        fetch_jartic.load_and_validate(raw_bytes, make_config())


def test_validation_rejects_unexpected_query_attributes() -> None:
    with pytest.raises(ValueError, match="time code"):
        fetch_jartic.load_and_validate(
            payload_bytes(time_code=202607042100), make_config()
        )
    with pytest.raises(ValueError, match="road type"):
        fetch_jartic.load_and_validate(payload_bytes(road_type="1"), make_config())


def test_fetch_snapshot_atomically_writes_valid_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "snapshot.geojson"
    raw_bytes = payload_bytes()
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(raw_bytes)

    monkeypatch.setattr(fetch_jartic.requests, "get", fake_get)

    payload, digest, downloaded = fetch_jartic.fetch_snapshot(
        make_config(), destination
    )

    assert downloaded is True
    assert payload["numberReturned"] == 1
    assert destination.read_bytes() == raw_bytes
    assert not destination.with_name("snapshot.geojson.part").exists()
    assert digest == fetch_jartic.sha256_bytes(raw_bytes)
    assert captured["url"] == fetch_jartic.BASE_URL
    assert captured["timeout"] == 30.0
    assert captured["params"] == fetch_jartic.build_request_params(make_config())


def test_existing_snapshot_is_validated_without_network_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "snapshot.geojson"
    raw_bytes = payload_bytes()
    destination.write_bytes(raw_bytes)

    def unexpected_get(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access must not occur for an existing snapshot")

    monkeypatch.setattr(fetch_jartic.requests, "get", unexpected_get)

    _, digest, downloaded = fetch_jartic.fetch_snapshot(make_config(), destination)

    assert downloaded is False
    assert destination.read_bytes() == raw_bytes
    assert digest == fetch_jartic.sha256_bytes(raw_bytes)


def test_http_error_does_not_create_raw_or_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "snapshot.geojson"

    def fake_get(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(b'{"message":"bad request"}', requests.HTTPError("400"))

    monkeypatch.setattr(fetch_jartic.requests, "get", fake_get)

    with pytest.raises(requests.HTTPError):
        fetch_jartic.fetch_snapshot(make_config(), destination)

    assert not destination.exists()
    assert not destination.with_name("snapshot.geojson.part").exists()


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fetch_jartic.REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_registry_upsert_is_idempotent(tmp_path: Path) -> None:
    registry = tmp_path / "sources.csv"
    row = {field: "" for field in fetch_jartic.REGISTRY_FIELDS}
    row.update(
        {
            "source_id": "jartic_1h_road3_tokyo_202607042200",
            "downloaded_at": "2026-07-17",
            "sha256": "abc123",
            "status": "raw_acquired",
        }
    )

    fetch_jartic.upsert_registry(row.copy(), registry)
    updated = row.copy()
    updated["processing_script"] = "fetch_jartic.py"
    updated["downloaded_at"] = "2099-01-01"
    fetch_jartic.upsert_registry(updated, registry)

    rows = read_registry(registry)
    assert len(rows) == 1
    assert rows[0]["downloaded_at"] == "2026-07-17"
    assert rows[0]["processing_script"] == "fetch_jartic.py"
    assert not registry.with_name("sources.csv.part").exists()


def test_registry_rejects_hash_conflict(tmp_path: Path) -> None:
    registry = tmp_path / "sources.csv"
    existing = {field: "" for field in fetch_jartic.REGISTRY_FIELDS}
    existing.update({"source_id": "snapshot", "sha256": "original"})
    write_registry(registry, [existing])

    replacement = existing.copy()
    replacement["sha256"] = "different"

    with pytest.raises(ValueError, match="hash conflict"):
        fetch_jartic.upsert_registry(replacement, registry)

    assert read_registry(registry)[0]["sha256"] == "original"


def test_fetch_upsert_preserves_downstream_processing_provenance(tmp_path: Path) -> None:
    registry = tmp_path / "sources.csv"
    current = {field: "" for field in fetch_jartic.REGISTRY_FIELDS}
    current.update(
        {
            "source_id": "snapshot",
            "sha256": "unchanged",
            "processing_script": "fetch_jartic.py;prepare_jartic.py",
            "processed_outputs": "observations.parquet;quality_summary.json",
            "status": "processed",
        }
    )
    write_registry(registry, [current])

    refreshed = current.copy()
    refreshed.update(
        {
            "processing_script": "fetch_jartic.py",
            "processed_outputs": "",
            "status": "raw_acquired",
        }
    )
    fetch_jartic.upsert_registry(refreshed, registry)

    saved = read_registry(registry)[0]
    assert saved["processing_script"] == "fetch_jartic.py;prepare_jartic.py"
    assert saved["processed_outputs"] == (
        "observations.parquet;quality_summary.json"
    )
    assert saved["status"] == "processed"
