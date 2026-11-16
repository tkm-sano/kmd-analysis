"""Read-only, hash-pinned ToC demand shared by A/B/C/D; no generation imports."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import io
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = {"S1": (1000, 10, 2), "S2": (2000, 20, 4), "S3": (4000, 40, 8)}
COLUMNS = ("scenario_id", "stop_id", "building_id", "chocho_code",
           "longitude", "latitude", "parcel_count")
PAYLOAD_NAMES = {"S1.csv", "S2.csv", "S3.csv", "REGIONAL_ALLOCATION.csv",
                 "VALIDATION.json", "READING_CONTRACT.md"}


class FrozenDemandError(ValueError):
    """Missing, inconsistent, modified, or unapproved demand; do not plan routes."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def stop_set_sha256(stop_ids):
    """Versioned, length-delimited UTF-8 ID set; no trimming or normalization."""
    identifiers = sorted((s.encode("utf-8") for s in stop_ids))
    if len(set(identifiers)) != len(identifiers):
        raise FrozenDemandError("Duplicate stop IDs")
    digest = hashlib.sha256(b"toc-stop-set-v1\x00")
    for identifier in identifiers:
        digest.update(len(identifier).to_bytes(4, "big"))
        digest.update(identifier)
    return digest.hexdigest()


def read_csv(data, columns=None):
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
        names = reader.fieldnames
        if not names or len(names) != len(set(names)):
            raise FrozenDemandError("Missing/duplicate CSV columns")
        if columns is not None and tuple(names) != tuple(columns):
            raise FrozenDemandError("Unexpected CSV schema")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise FrozenDemandError("Malformed CSV record")
        return rows
    except (UnicodeError, csv.Error) as error:
        raise FrozenDemandError("Invalid UTF-8 CSV") from error


def _json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise FrozenDemandError("Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              FrozenDemandError("Non-finite JSON")))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise FrozenDemandError("Invalid JSON") from error


def _regular_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise FrozenDemandError(f"Missing or non-regular input: {path}")
    return path.read_bytes()


def _verify_bundle(directory, expected_manifest_hash):
    """Internal verifier. The public API obtains its hash from the source pin."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise FrozenDemandError("Missing/non-regular frozen directory")
    expected_names = PAYLOAD_NAMES | {"MANIFEST.json", "SHA256SUMS"}
    if {p.name for p in directory.iterdir()} != expected_names:
        raise FrozenDemandError("Missing or extra frozen files")
    data = {name: _regular_bytes(directory / name) for name in expected_names}
    if sha256(data["MANIFEST.json"]) != expected_manifest_hash:
        raise FrozenDemandError("MANIFEST.json differs from the approved source pin")
    manifest = _json(data["MANIFEST.json"])
    if manifest.get("dataset_id") != "ota-toc-frozen-demand-v1" or manifest.get("schema_version") != 1:
        raise FrozenDemandError("Unapproved demand version")
    if set(manifest.get("files", {})) != PAYLOAD_NAMES:
        raise FrozenDemandError("Manifest payload inventory mismatch")
    for name, entry in manifest["files"].items():
        if sha256(data[name]) != entry["sha256"] or len(data[name]) != entry["bytes"]:
            raise FrozenDemandError(f"Modified frozen payload: {name}")
    checksums = b"".join(
        f"{sha256(data[name])}  {name}\n".encode("utf-8")
        for name in sorted(PAYLOAD_NAMES | {"MANIFEST.json"}, key=lambda s: s.encode("utf-8")))
    if data["SHA256SUMS"] != checksums:
        raise FrozenDemandError("SHA256SUMS mismatch")

    scenarios = {}
    allocation = read_csv(data["REGIONAL_ALLOCATION.csv"])
    if len(allocation) != 3 * 182:
        raise FrozenDemandError("Regional allocation record count mismatch")
    for scenario_id, (count, vehicles, berths) in SCENARIOS.items():
        metadata = manifest["scenarios"][scenario_id]
        if (metadata["N"], metadata["vehicles"], metadata["berths"], metadata["total_parcels"]) != (
                count, vehicles, berths, count):
            raise FrozenDemandError("Scenario definition drift")
        rows = read_csv(data[scenario_id + ".csv"], COLUMNS)
        if len(rows) != count:
            raise FrozenDemandError("Wrong scenario count")
        ids, buildings, regions = [], set(), {}
        for row in rows:
            if any(not value for value in row.values()):
                raise FrozenDemandError("Missing demand field")
            if row["scenario_id"] != scenario_id or row["parcel_count"] != "1":
                raise FrozenDemandError("Scenario/parcel value changed")
            if not re.fullmatch(r"[0-9]{6}", row["chocho_code"]):
                raise FrozenDemandError("Invalid six-digit region")
            if row["building_id"] in buildings:
                raise FrozenDemandError("Duplicate building")
            buildings.add(row["building_id"])
            ids.append(row["stop_id"])
            regions[row["chocho_code"]] = regions.get(row["chocho_code"], 0) + 1
            try:
                lon, lat = Decimal(row["longitude"]), Decimal(row["latitude"])
                if not (lon.is_finite() and lat.is_finite() and -180 <= lon <= 180 and -90 <= lat <= 90):
                    raise FrozenDemandError("Invalid coordinates")
            except InvalidOperation as error:
                raise FrozenDemandError("Invalid coordinate format") from error
        if ids != sorted(ids, key=lambda s: s.encode("utf-8")):
            raise FrozenDemandError("Unstable row order")
        if stop_set_sha256(ids) != metadata["stop_set_sha256"]:
            raise FrozenDemandError("Wrong stop set")
        regional = [r for r in allocation if r["scenario_id"] == scenario_id]
        if len(regional) != 182 or len({r["chocho_code"] for r in regional}) != 182:
            raise FrozenDemandError("Missing/duplicate regional rows")
        if any(regions.get(r["chocho_code"], 0) != int(r["selected_count"]) or
               r["selected_count"] != r["allocated_count"] for r in regional):
            raise FrozenDemandError("Regional count mismatch")
        scenarios[scenario_id] = rows
    a, b, c = (set(r["stop_id"] for r in scenarios[s]) for s in SCENARIOS)
    if not a < b < c:
        raise FrozenDemandError("Required strict nesting violated")
    # A shared stop must retain ALL payload attributes apart from scenario_id.
    reference = {r["stop_id"]: {k: v for k, v in r.items() if k != "scenario_id"}
                 for r in scenarios["S3"]}
    if any({k: v for k, v in r.items() if k != "scenario_id"} != reference[r["stop_id"]]
           for rows in scenarios.values() for r in rows):
        raise FrozenDemandError("Shared stop attributes differ across scenarios")
    return manifest, scenarios


def _read_trust_root():
    try:
        from .frozen_demand_pin import (MANIFEST_SHA256, CHECKSUMS_SHA256,
                                        CONFIG_SHA256, CONFIG_RELATIVE_PATH)
    except ImportError as error:
        raise FrozenDemandError("v1 has not been published/pinned") from error
    config_data = _regular_bytes(ROOT / CONFIG_RELATIVE_PATH)
    if sha256(config_data) != CONFIG_SHA256:
        raise FrozenDemandError("Frozen demand config differs from source pin")
    config = _json(config_data)
    if config["manifest_sha256"] != MANIFEST_SHA256 or config["methods"] != ["A", "B", "C", "D"]:
        raise FrozenDemandError("Invalid common consumer contract")
    return config, MANIFEST_SHA256, CHECKSUMS_SHA256


@dataclass(frozen=True)
class FrozenStop:
    stop_id: str
    building_id: str
    chocho_code: str
    longitude: str
    latitude: str
    parcel_count: int


@dataclass(frozen=True)
class FrozenDemand:
    scenario_id: str
    consumer_method_id: str
    N: int
    vehicles: int
    berths: int
    stops: tuple[FrozenStop, ...]
    manifest_sha256: str
    csv_sha256: str
    stop_set_sha256: str


def load_frozen_demand(scenario_id, *, method_id, bundle_dir=None):
    """Validate the pinned COMPLETE v1 bundle, then return immutable demand.

    A bundle_dir override may contain an identical archival/test copy only;
    callers cannot supply a replacement manifest hash, population, or seed.
    This function never imports or invokes the generation code.
    """
    if scenario_id not in SCENARIOS or method_id not in ("A", "B", "C", "D"):
        raise FrozenDemandError("Unsupported scenario/method")
    config, manifest_hash, checksum_hash = _read_trust_root()
    directory = ROOT / config["bundle_relative_path"] if bundle_dir is None else Path(bundle_dir)
    # Read/verify each snapshot as bytes before decoding: no check-then-reopen CSV.
    manifest, scenarios = _verify_bundle(directory, manifest_hash)
    if sha256(_regular_bytes(directory / "SHA256SUMS")) != checksum_hash:
        raise FrozenDemandError("Checksum inventory differs from source pin")
    count, vehicles, berths = SCENARIOS[scenario_id]
    stops = tuple(FrozenStop(r["stop_id"], r["building_id"], r["chocho_code"],
                             r["longitude"], r["latitude"], int(r["parcel_count"]))
                  for r in scenarios[scenario_id])
    return FrozenDemand(scenario_id, method_id, count, vehicles, berths, stops,
                        manifest_hash, manifest["files"][scenario_id + ".csv"]["sha256"],
                        manifest["scenarios"][scenario_id]["stop_set_sha256"])
