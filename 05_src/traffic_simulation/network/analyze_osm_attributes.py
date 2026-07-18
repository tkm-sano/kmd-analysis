"""Create a reproducible baseline audit of selected OSM road attributes.

This is a pre-resolution coverage audit. It deliberately does not infer implicit
OSM rules, supplement values from external sources, or determine SUMO access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
JST: Final = ZoneInfo("Asia/Tokyo")
LANES_PATTERN: Final = re.compile(r"[1-9][0-9]*\Z")
MAXSPEED_PATTERN: Final = re.compile(r"[1-9][0-9]*(?:\.[0-9]+)?\Z")
ALLOWED_ONEWAY: Final = frozenset({"yes", "no", "-1"})
AUDITED_ATTRIBUTES: Final = ("lanes", "maxspeed", "oneway")
RELATED_TAGS: Final = {
    "lanes": ("lanes:forward", "lanes:backward", "lanes:both_ways"),
    "maxspeed": (
        "maxspeed:forward",
        "maxspeed:backward",
        "maxspeed:conditional",
        "maxspeed:type",
        "maxspeed:advisory",
        "source:maxspeed",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid_lanes(value: Any) -> bool:
    return isinstance(value, str) and LANES_PATTERN.fullmatch(value) is not None


def is_valid_maxspeed(value: Any) -> bool:
    return isinstance(value, str) and MAXSPEED_PATTERN.fullmatch(value) is not None


def is_valid_oneway(value: Any) -> bool:
    return isinstance(value, str) and value in ALLOWED_ONEWAY


VALIDATORS: Final = {
    "lanes": is_valid_lanes,
    "maxspeed": is_valid_maxspeed,
    "oneway": is_valid_oneway,
}


def haversine_m(
    first: Sequence[float], second: Sequence[float], earth_radius_m: float
) -> float:
    lon1, lat1 = math.radians(first[0]), math.radians(first[1])
    lon2, lat2 = math.radians(second[0]), math.radians(second[1])
    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1
    term = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_m * math.asin(min(1.0, math.sqrt(term)))


def linestring_length_m(coordinates: Sequence[Sequence[float]], radius: float) -> float:
    return sum(
        haversine_m(first, second, radius)
        for first, second in zip(coordinates, coordinates[1:])
    )


def read_geojson_sequence(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = line.lstrip("\x1e").strip()
            if not payload:
                continue
            try:
                feature = json.loads(payload)
            except json.JSONDecodeError as error:
                message = f"invalid GeoJSON sequence at line {line_number}"
                raise ValueError(message) from error
            if not isinstance(feature, dict):
                raise ValueError(f"feature at line {line_number} is not an object")
            yield feature


def attribute_state(properties: Mapping[str, Any], attribute: str) -> str:
    value = properties.get(attribute)
    if value is None or value == "":
        return "missing"
    return "valid" if VALIDATORS[attribute](value) else "invalid"


def _rounded_length(value_m: float) -> float:
    return round(value_m, 3)


def summarize_features(
    features: Iterable[Mapping[str, Any]],
    highway_types: Sequence[str],
    earth_radius_m: float,
) -> dict[str, Any]:
    selected_types = frozenset(highway_types)
    total_ways = 0
    total_length_m = 0.0
    attribute_counts = {name: Counter() for name in AUDITED_ATTRIBUTES}
    invalid_values = {name: Counter() for name in AUDITED_ATTRIBUTES}
    attribute_lengths = {name: defaultdict(float) for name in AUDITED_ATTRIBUTES}
    patterns: Counter[str] = Counter()
    type_total: Counter[str] = Counter()
    type_unresolved: Counter[str] = Counter()
    type_lengths: defaultdict[str, float] = defaultdict(float)
    type_unresolved_lengths: defaultdict[str, float] = defaultdict(float)
    diagnostics: Counter[str] = Counter()

    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties")
        if not isinstance(geometry, Mapping) or not isinstance(properties, Mapping):
            continue
        highway = properties.get("highway")
        if highway not in selected_types or geometry.get("type") != "LineString":
            continue
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue

        length_m = linestring_length_m(coordinates, earth_radius_m)
        states = {
            attribute: attribute_state(properties, attribute)
            for attribute in AUDITED_ATTRIBUTES
        }
        unresolved = tuple(
            attribute
            for attribute in AUDITED_ATTRIBUTES
            if states[attribute] != "valid"
        )
        pattern = ",".join(unresolved) if unresolved else "none"

        total_ways += 1
        total_length_m += length_m
        type_total[str(highway)] += 1
        type_lengths[str(highway)] += length_m
        patterns[pattern] += 1
        if unresolved:
            type_unresolved[str(highway)] += 1
            type_unresolved_lengths[str(highway)] += length_m

        for attribute, state in states.items():
            attribute_counts[attribute][state] += 1
            attribute_lengths[attribute][state] += length_m
            if state == "invalid":
                invalid_values[attribute][str(properties[attribute])] += 1

        if states["lanes"] == "missing":
            has_directional_lanes = any(
                properties.get(tag) not in (None, "")
                for tag in RELATED_TAGS["lanes"]
            )
            if has_directional_lanes:
                diagnostics["lanes_missing_with_directional_tag"] += 1
            if properties.get("width") not in (None, ""):
                diagnostics["lanes_missing_with_width"] += 1
            if properties.get("lane_markings") not in (None, ""):
                diagnostics["lanes_missing_with_lane_markings"] += 1
        if states["maxspeed"] == "missing" and any(
            properties.get(tag) not in (None, "") for tag in RELATED_TAGS["maxspeed"]
        ):
            diagnostics["maxspeed_missing_with_related_tag"] += 1
        if states["oneway"] == "missing" and str(highway) in {
            "motorway",
            "motorway_link",
        }:
            diagnostics["oneway_missing_on_motorway_or_link"] += 1
        if states["oneway"] == "missing" and properties.get("junction") == "roundabout":
            diagnostics["oneway_missing_on_roundabout"] += 1

    if total_ways == 0:
        raise ValueError("no candidate OSM ways were selected")

    attributes: dict[str, Any] = {}
    for attribute in AUDITED_ATTRIBUTES:
        missing = attribute_counts[attribute]["missing"]
        invalid = attribute_counts[attribute]["invalid"]
        unresolved = missing + invalid
        unresolved_length = (
            attribute_lengths[attribute]["missing"]
            + attribute_lengths[attribute]["invalid"]
        )
        attributes[attribute] = {
            "missing_ways": missing,
            "invalid_ways": invalid,
            "unresolved_ways": unresolved,
            "unresolved_way_ratio": round(unresolved / total_ways, 6),
            "unresolved_length_m": _rounded_length(unresolved_length),
            "unresolved_length_ratio": round(unresolved_length / total_length_m, 6),
            "invalid_value_counts": dict(invalid_values[attribute].most_common()),
        }

    by_highway = {}
    for highway in highway_types:
        count = type_total[highway]
        if not count:
            continue
        by_highway[highway] = {
            "ways": count,
            "length_m": _rounded_length(type_lengths[highway]),
            "ways_with_any_unresolved": type_unresolved[highway],
            "unresolved_way_ratio": round(type_unresolved[highway] / count, 6),
            "unresolved_length_m": _rounded_length(type_unresolved_lengths[highway]),
        }

    return {
        "candidate_ways": total_ways,
        "candidate_length_m": _rounded_length(total_length_m),
        "attributes": attributes,
        "unresolved_patterns": dict(patterns.most_common()),
        "ways_with_any_unresolved": total_ways - patterns["none"],
        "ways_with_all_simple_values_valid": patterns["none"],
        "by_highway": by_highway,
        "related_tag_diagnostics": {
            key: diagnostics[key]
            for key in (
                "lanes_missing_with_directional_tag",
                "lanes_missing_with_width",
                "lanes_missing_with_lane_markings",
                "maxspeed_missing_with_related_tag",
                "oneway_missing_on_motorway_or_link",
                "oneway_missing_on_roundabout",
            )
        },
    }


def load_audit_config(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        full_config = yaml.safe_load(handle)
    if not isinstance(full_config, dict):
        raise ValueError("SUMO network config must be a mapping")
    audit = full_config.get("osm_attribute_baseline_audit")
    source = full_config.get("source")
    if not isinstance(audit, dict) or not isinstance(source, dict):
        raise ValueError("config lacks source or osm_attribute_baseline_audit")
    expected_validators = {
        "lanes": "positive_integer",
        "maxspeed": "positive_plain_numeric_kmh",
        "oneway_allowed": ["yes", "no", "-1"],
    }
    if audit.get("simple_value_validators") != expected_validators:
        raise ValueError("unsupported simple_value_validators definition")
    expected_length_method = "haversine_between_consecutive_geojson_coordinates"
    if audit.get("length", {}).get("method") != expected_length_method:
        raise ValueError("unsupported length calculation method")
    return full_config, audit


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def analyze(config_path: Path, *, overwrite: bool = False) -> Path:
    full_config, audit = load_audit_config(config_path)
    source = full_config["source"]["extracted_pbf"]
    pbf_path = REPOSITORY_ROOT / source["path"]
    output_path = REPOSITORY_ROOT / audit["output"]
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {output_path}")
    actual_pbf_sha = sha256_file(pbf_path)
    if actual_pbf_sha != source["sha256"]:
        raise ValueError(f"PBF SHA-256 mismatch: {actual_pbf_sha}")

    with tempfile.TemporaryDirectory(prefix="osm-attribute-audit-") as directory:
        temporary = Path(directory)
        highway_pbf = temporary / "highways.osm.pbf"
        geojsonseq = temporary / "highways.geojsonseq"
        commands = [
            [
                "osmium",
                "tags-filter",
                str(pbf_path),
                "w/highway",
                "-o",
                str(highway_pbf),
            ],
            [
                "osmium",
                "export",
                str(highway_pbf),
                "--geometry-types=linestring",
                "--add-unique-id=type_id",
                "-f",
                "geojsonseq",
                "-o",
                str(geojsonseq),
            ],
        ]
        for command in commands:
            _run(command)
        result = summarize_features(
            read_geojson_sequence(geojsonseq),
            audit["selection"]["highway_types"],
            float(audit["length"]["earth_radius_m"]),
        )
        osmium_version = _run(["osmium", "--version"]).stdout.splitlines()[0]

    summary = {
        "schema_version": 1,
        "method_version": audit["method_version"],
        "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
        "config_id": full_config["config_id"],
        "config_version": full_config["config_version"],
        "config_path": str(config_path.relative_to(REPOSITORY_ROOT)),
        "config_sha256": sha256_file(config_path),
        "source_registry_id": full_config["source"]["source_registry_id"],
        "source_pbf": str(pbf_path.relative_to(REPOSITORY_ROOT)),
        "source_pbf_sha256": actual_pbf_sha,
        "tool_version": osmium_version,
        "selection": audit["selection"],
        "simple_value_validators": audit["simple_value_validators"],
        "length": audit["length"],
        "interpretation": audit["interpretation"],
        "commands": [
            "osmium tags-filter <governed-pbf> w/highway -o <temporary-pbf>",
            "osmium export <temporary-pbf> --geometry-types=linestring "
            "--add-unique-id=type_id -f geojsonseq -o <temporary-geojsonseq>",
        ],
        "result": result,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_suffix(output_path.suffix + ".part")
    partial.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    partial.replace(output_path)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = args.config.expanduser().resolve()
    output = analyze(config_path, overwrite=args.overwrite)
    print(output.relative_to(REPOSITORY_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
