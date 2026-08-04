"""Resolve v17 Directed Segment speeds with dated Japan speed rules."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from traffic_simulation.network.conditional_access_v17 import (
    ConditionalAccessError,
    _evaluate,
    _interval_points,
    _split_top_level,
    parse_condition,
)
from traffic_simulation.network.directed_segments_v17 import (
    build_production_artifact as build_directed_segment_artifact,
)
from traffic_simulation.network.static_access_v17 import _source_way_tags
from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/japan_speed_rules_v17.yml"
)
REGISTRY_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/japan_speed_rules_v17.schema.json"
)
RECORD_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/speed_resolution_record_v17.schema.json"
)
NUMERIC_SPEED = re.compile(r"^(?P<value>\d+(?:\.\d+)?)$")
NUMERIC_LIKE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
SPEED_CLAUSE = re.compile(r"^\s*(?P<value>[^@]+?)\s*@\s*\((?P<condition>.*)\)\s*$", re.DOTALL)
SUPPORTED_SYMBOLIC_VALUES = {"JP:urban"}


class SpeedResolutionError(ValueError):
    def __init__(self, message: str, *, stop_code: str, status: str) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


@dataclass(frozen=True)
class SpeedClause:
    value: str
    condition: tuple[Any, ...]
    source_order: int
    source_text: str


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SpeedResolutionError(
            f"YAML root must be an object: {path}",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SpeedResolutionError(
            f"JSON root must be an object: {path}",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    return value


@lru_cache(maxsize=1)
def load_japan_speed_registry() -> dict[str, Any]:
    registry = _load_yaml(REGISTRY_PATH)
    schema = _load_json(REGISTRY_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(registry)
    source_ids = {item["source_id"] for item in registry["source_authorities"]}
    for rule in registry["rules"]:
        if not set(rule["source_ids"]) <= source_ids:
            raise SpeedResolutionError(
                f"Japan speed rule has an unknown source: {rule['rule_id']}",
                stop_code="SPEED_RULE_NOT_REGISTERED",
                status="unresolved",
            )
        if rule["effective_end"] is not None and date.fromisoformat(
            rule["effective_end"]
        ) < date.fromisoformat(rule["effective_start"]):
            raise SpeedResolutionError(
                f"Japan speed rule has a reversed interval: {rule['rule_id']}",
                stop_code="SPEED_RULE_NOT_REGISTERED",
                status="unresolved",
            )
    return registry


@lru_cache(maxsize=1)
def _record_validator() -> jsonschema.Draft202012Validator:
    schema = _load_json(RECORD_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def normalize_numeric_speed(value: str) -> float:
    normalized = value.strip()
    match = NUMERIC_SPEED.fullmatch(normalized)
    if match is None:
        if NUMERIC_LIKE.fullmatch(normalized):
            raise SpeedResolutionError(
                f"speed must be positive: {value!r}",
                stop_code="SPEED_VALUE_INVALID",
                status="invalid",
            )
        raise SpeedResolutionError(
            f"speed value is valid but unsupported: {value!r}",
            stop_code="SPEED_VALUE_UNSUPPORTED",
            status="valid_but_unsupported",
        )
    speed = float(match.group("value"))
    if speed <= 0 or speed > 200:
        raise SpeedResolutionError(
            f"speed is outside the registered range: {value!r}",
            stop_code="SPEED_VALUE_INVALID",
            status="invalid",
        )
    return speed


def _parse_speed_clause(expression: str) -> tuple[SpeedClause, ...]:
    clauses: list[SpeedClause] = []
    try:
        values = _split_top_level(expression, ";")
        for order, source in enumerate(values):
            match = SPEED_CLAUSE.fullmatch(source)
            if match is None:
                raise SpeedResolutionError(
                    f"unsupported conditional speed clause: {source!r}",
                    stop_code="SPEED_VALUE_UNSUPPORTED",
                    status="valid_but_unsupported",
                )
            normalize_numeric_speed(match.group("value"))
            clauses.append(
                SpeedClause(
                    value=match.group("value").strip(),
                    condition=parse_condition(match.group("condition")),
                    source_order=order,
                    source_text=source,
                )
            )
    except ConditionalAccessError as error:
        raise SpeedResolutionError(
            str(error),
            stop_code="SPEED_VALUE_UNSUPPORTED",
            status="valid_but_unsupported",
        ) from error
    return tuple(clauses)


def _selected_speed_clause(
    clauses: Sequence[SpeedClause], context: Mapping[str, Any]
) -> SpeedClause | None:
    selected = None
    for clause in clauses:
        if _evaluate(clause.condition, context):
            selected = clause
    return selected


def evaluate_conditional_speed(
    expression: str, context: Mapping[str, Any]
) -> SpeedClause | None:
    clauses = _parse_speed_clause(expression)
    try:
        points = _interval_points(clauses, context)  # type: ignore[arg-type]
        if points is None:
            return _selected_speed_clause(clauses, context)
        selected = [_selected_speed_clause(clauses, point) for point in points]
    except ConditionalAccessError as error:
        code = (
            "SPEED_WITHIN_INTERVAL_CHANGE"
            if error.stop_code == "ACCESS_WITHIN_INTERVAL_CHANGE"
            else "SPEED_CONDITIONAL_CONTEXT_MISSING"
        )
        status = "conflict" if code == "SPEED_WITHIN_INTERVAL_CHANGE" else "unresolved"
        raise SpeedResolutionError(str(error), stop_code=code, status=status) from error
    signatures = {None if item is None else normalize_numeric_speed(item.value) for item in selected}
    if len(signatures) > 1:
        raise SpeedResolutionError(
            "conditional speed changes within the simulation interval",
            stop_code="SPEED_WITHIN_INTERVAL_CHANGE",
            status="conflict",
        )
    matched = [item for item in selected if item is not None]
    return max(matched, key=lambda item: item.source_order) if matched else None


def _scenario_reference_date(context: Mapping[str, Any]) -> date | None:
    if "start_timestamp" in context:
        try:
            return date.fromisoformat(str(context["start_timestamp"])[:10])
        except ValueError:
            return None
    if "date" in context:
        try:
            return date.fromisoformat(str(context["date"]))
        except ValueError:
            return None
    return None


def resolve_japan_speed_rule(
    *,
    symbolic_value: str | None,
    context: Mapping[str, Any],
    road_state_evidence: Mapping[str, Any] | None,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_registry = dict(registry or load_japan_speed_registry())
    # Phase 2's synthetic symbolic registry is intentionally independent of
    # the production legal-rule table.
    if symbolic_value is not None and symbolic_value in selected_registry and isinstance(
        selected_registry[symbolic_value], (int, float)
    ):
        speed = float(selected_registry[symbolic_value])
        if speed <= 0:
            raise SpeedResolutionError(
                "fixture symbolic speed is invalid",
                stop_code="SPEED_VALUE_INVALID",
                status="invalid",
            )
        return {
            "speed_kmh": speed,
            "speed_kind": "symbolic_fixture",
            "rule_ids": [f"FIXTURE_SYMBOLIC_{symbolic_value}"],
            "source_ids": [],
        }
    symbolic = selected_registry.get("symbolic_values", {})
    if symbolic_value is not None and symbolic_value not in symbolic:
        raise SpeedResolutionError(
            f"symbolic speed has no registered rule: {symbolic_value}",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    reference_date = _scenario_reference_date(context)
    evidence = dict(road_state_evidence or {})
    evidence.setdefault("reference_date", reference_date.isoformat() if reference_date else None)
    required = {"reference_date", "road_category", "vehicle_category", "designated_speed_present"}
    if any(evidence.get(field) is None for field in required):
        raise SpeedResolutionError(
            "Japan speed rule requires dated road-state and designated-speed evidence",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    try:
        evidence_date = date.fromisoformat(str(evidence["reference_date"]))
    except ValueError as error:
        raise SpeedResolutionError(
            "Japan speed evidence date is invalid",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        ) from error
    matches = []
    for rule in selected_registry["rules"]:
        start = date.fromisoformat(rule["effective_start"])
        end = date.max if rule["effective_end"] is None else date.fromisoformat(rule["effective_end"])
        if not start <= evidence_date <= end:
            continue
        if any(evidence.get(field) != rule[field] for field in ("road_category", "vehicle_category", "designated_speed_present")):
            continue
        if any(evidence.get(field) != value for field, value in rule["road_state"].items()):
            continue
        matches.append(rule)
    if not matches:
        raise SpeedResolutionError(
            "dated Japan speed rule has no exact road-state match",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    speeds = {float(item["speed_kmh"]) for item in matches}
    if len(speeds) != 1:
        raise SpeedResolutionError(
            "dated Japan speed rules produce conflicting speeds",
            stop_code="SPEED_VALUE_INVALID",
            status="conflict",
        )
    return {
        "speed_kmh": next(iter(speeds)),
        "speed_kind": matches[0]["speed_kind"],
        "rule_ids": sorted(item["rule_id"] for item in matches),
        "source_ids": sorted({source for item in matches for source in item["source_ids"]}),
    }


def _resolved(
    speed_kmh: float,
    *,
    origin: str,
    speed_kind: str,
    source_key: str | None,
    source_value: str | None,
    rule_ids: Sequence[str] = (),
    source_ids: Sequence[str] = (),
    assumption_ids: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "resolution_status": "resolved",
        "value_origin": origin,
        "speed_kmh": speed_kmh,
        "speed_mps": speed_kmh / 3.6,
        "speed_kind": speed_kind,
        "source_key": source_key,
        "source_value": source_value,
        "rule_ids": sorted(rule_ids),
        "source_ids": sorted(source_ids),
        "assumption_ids": sorted(assumption_ids),
        "stop_code": None,
        "review_required": False,
    }


def _symbolic_candidate(tags: Mapping[str, str], direction: str) -> tuple[str | None, str | None]:
    directional = tags.get(f"maxspeed:{direction}")
    if directional is not None and directional.startswith("JP:"):
        return f"maxspeed:{direction}", directional
    general = tags.get("maxspeed")
    if general is not None and general.startswith("JP:"):
        return "maxspeed", general
    value = tags.get("maxspeed:type")
    return ("maxspeed:type", value) if value is not None else (None, None)


def resolve_segment_speed(
    tags: Mapping[str, str],
    *,
    direction: str,
    profile: str,
    scenario_context: Mapping[str, Any],
    road_state_evidence: Mapping[str, Any] | None = None,
    japan_registry: Mapping[str, Any] | None = None,
    structural_typemap_speed_kmh: float | None = None,
) -> dict[str, Any]:
    if profile not in {"formal", "structural"}:
        raise SpeedResolutionError(
            f"unknown profile: {profile}",
            stop_code="SPEED_VALUE_INVALID",
            status="invalid",
        )
    direction_key = f"maxspeed:{direction}"
    if direction_key in tags:
        value = tags[direction_key]
        if not value.startswith("JP:"):
            speed = normalize_numeric_speed(value)
            return _resolved(
                speed,
                origin="source_normalized",
                speed_kind="source_maxspeed",
                source_key=direction_key,
                source_value=value,
            )
    if "maxspeed" in tags:
        value = tags["maxspeed"]
        if not value.startswith("JP:"):
            speed = normalize_numeric_speed(value)
            return _resolved(
                speed,
                origin="source_normalized",
                speed_kind="source_maxspeed",
                source_key="maxspeed",
                source_value=value,
            )
    for key in (f"maxspeed:{direction}:conditional", "maxspeed:conditional"):
        if key in tags:
            clause = evaluate_conditional_speed(tags[key], scenario_context)
            if clause is not None:
                speed = normalize_numeric_speed(clause.value)
                return _resolved(
                    speed,
                    origin="source_normalized",
                    speed_kind="conditional_source_maxspeed",
                    source_key=key,
                    source_value=tags[key],
                    rule_ids=[
                        "speed-condition:"
                        + hashlib.sha256(clause.source_text.encode("utf-8")).hexdigest()
                    ],
                )
    symbolic_key, symbolic_value = _symbolic_candidate(tags, direction)
    if symbolic_value is not None and not symbolic_value.startswith("JP:"):
        raise SpeedResolutionError(
            f"symbolic speed has no registered rule: {symbolic_value}",
            stop_code="SPEED_RULE_NOT_REGISTERED",
            status="unresolved",
        )
    related_unsupported = sorted(
        key
        for key in tags
        if key.startswith("maxspeed:")
        and key
        not in {
            "maxspeed:type",
            "maxspeed:advisory",
            "maxspeed:conditional",
            f"maxspeed:{direction}",
            f"maxspeed:{direction}:conditional",
            "maxspeed:forward",
            "maxspeed:backward",
        }
    )
    if related_unsupported:
        raise SpeedResolutionError(
            f"unsupported speed scope: {related_unsupported}",
            stop_code="SPEED_VALUE_UNSUPPORTED",
            status="valid_but_unsupported",
        )
    try:
        legal = resolve_japan_speed_rule(
            symbolic_value=symbolic_value,
            context=scenario_context,
            road_state_evidence=road_state_evidence,
            registry=japan_registry,
        )
        return _resolved(
            legal["speed_kmh"],
            origin="rule_derived",
            speed_kind=legal["speed_kind"],
            source_key=symbolic_key,
            source_value=symbolic_value,
            rule_ids=legal["rule_ids"],
            source_ids=legal["source_ids"],
        )
    except SpeedResolutionError:
        if profile == "structural" and structural_typemap_speed_kmh is not None:
            speed = float(structural_typemap_speed_kmh)
            if speed <= 0:
                raise SpeedResolutionError(
                    "structural typemap speed is invalid",
                    stop_code="SPEED_VALUE_INVALID",
                    status="invalid",
                )
            return _resolved(
                speed,
                origin="model_assumed",
                speed_kind="structural_simulation_speed",
                source_key=None,
                source_value=None,
                assumption_ids=["STRUCTURAL_TYPEMAP_SPEED_DEFAULT_V1"],
            )
        raise


def _record_id(identity: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(identity), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _advisory(tags: Mapping[str, str]) -> dict[str, Any] | None:
    if "maxspeed:advisory" not in tags:
        return None
    value = tags["maxspeed:advisory"]
    try:
        speed = normalize_numeric_speed(value)
    except SpeedResolutionError:
        speed = None
    return {"source_value": value, "speed_kmh": speed, "legal_maxspeed": False}


def _build_record(
    segment: Mapping[str, Any],
    *,
    population_version: str,
    profile: str,
    scenario_context_id: str,
    tags: Mapping[str, str],
    resolution: Mapping[str, Any],
) -> dict[str, Any]:
    registry = load_japan_speed_registry()
    identity = {
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": population_version,
        "profile": profile,
        "source_way_id": segment["source_way_id"],
        "directed_segment_id": segment["directed_segment_id"],
        "source_direction": segment["source_direction"],
        "scenario_context_id": scenario_context_id,
    }
    record = {
        "speed_record_id": _record_id(identity),
        **identity,
        "resolution_status": resolution["resolution_status"],
        "value_origin": resolution["value_origin"],
        "speed_kmh": resolution["speed_kmh"],
        "speed_mps": resolution["speed_mps"],
        "speed_kind": resolution["speed_kind"],
        "source_key": resolution["source_key"],
        "source_value": resolution["source_value"],
        "rule_ids": list(resolution["rule_ids"]),
        "source_ids": list(resolution["source_ids"]),
        "assumption_ids": list(resolution["assumption_ids"]),
        "stop_code": resolution["stop_code"],
        "review_required": resolution["review_required"],
        "advisory_speed": _advisory(tags),
        "source_observations": {
            key: tags[key] for key in sorted(tags) if key.startswith("maxspeed")
        },
        "provenance": {
            "resolution": "speed_resolution_v17",
            "canonical_unit": "km/h",
            "sumo_conversion": "speed_mps = speed_kmh / 3.6",
            "advisory_is_legal_maxspeed": False,
            "typemap_used_as_formal_evidence": False,
            "japan_speed_registry_id": registry["registry_id"],
            "japan_speed_registry_version": registry["registry_version"],
            "unresolved_policy": registry["unresolved_policy"],
        },
    }
    _record_validator().validate(record)
    return record


def build_speed_production_artifact(
    input_path: Path,
    *,
    profile: str,
    scenario_context: Mapping[str, Any] | None = None,
    road_state_evidence_by_way: Mapping[int, Mapping[str, Any]] | None = None,
    structural_typemap_speeds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    if scenario_context is None:
        from traffic_simulation.network.scenario_context_v17 import load_governed_runtime_context

        scenario_context = load_governed_runtime_context()
    context = dict(scenario_context)
    scenario_context_id = str(context.get("scenario_context_id", "fixture_context"))
    directed = build_directed_segment_artifact(input_path)
    tags_by_way = _source_way_tags(input_path)
    evidence = dict(road_state_evidence_by_way or {})
    typemap = dict(structural_typemap_speeds or {})
    records: list[dict[str, Any]] = []
    for segment in directed["directed_segments"]:
        way_id = int(segment["source_way_id"])
        tags = tags_by_way[way_id]
        try:
            resolution = resolve_segment_speed(
                tags,
                direction=segment["source_direction"],
                profile=profile,
                scenario_context=context,
                road_state_evidence=evidence.get(way_id),
                structural_typemap_speed_kmh=typemap.get(tags.get("highway", "")),
            )
        except SpeedResolutionError as error:
            resolution = {
                "resolution_status": error.status,
                "value_origin": None,
                "speed_kmh": None,
                "speed_mps": None,
                "speed_kind": None,
                "source_key": None,
                "source_value": None,
                "rule_ids": [],
                "source_ids": [],
                "assumption_ids": [],
                "stop_code": error.stop_code,
                "review_required": True,
            }
        records.append(
            _build_record(
                segment,
                population_version=directed["population_version"],
                profile=profile,
                scenario_context_id=scenario_context_id,
                tags=tags,
                resolution=resolution,
            )
        )
    records.sort(key=lambda item: item["speed_record_id"])
    blockers = [item for item in records if item["resolution_status"] != "resolved"]
    payload = json.dumps(
        {"speed_records": records, "upstream_blockers": directed["blockers"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    statuses = Counter(item["resolution_status"] for item in records)
    origins = Counter(item["value_origin"] for item in records if item["value_origin"])
    return {
        "schema_version": 17,
        "artifact_type": "speed_resolution_production_collection",
        "configuration_id": directed["configuration_id"],
        "population_version": directed["population_version"],
        "profile": profile,
        "source": directed["source"],
        "scenario_context": context,
        "japan_speed_registry": {
            "path": str(REGISTRY_PATH.relative_to(REPOSITORY_ROOT)),
            "registry_id": load_japan_speed_registry()["registry_id"],
            "registry_version": load_japan_speed_registry()["registry_version"],
            "sha256": hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest(),
        },
        "canonical_unit": "km/h",
        "sumo_conversion": "speed_mps = speed_kmh / 3.6",
        "speed_records": records,
        "blockers": [
            {
                "speed_record_id": item["speed_record_id"],
                "source_way_id": item["source_way_id"],
                "directed_segment_id": item["directed_segment_id"],
                "resolution_status": item["resolution_status"],
                "stop_code": item["stop_code"],
            }
            for item in blockers
        ],
        "upstream_relation_blockers": directed["blockers"],
        "counts": {
            "governed_directed_segments": len(directed["directed_segments"]),
            "speed_records": len(records),
            "resolved_speeds": statuses["resolved"],
            "unresolved_speeds": statuses["unresolved"],
            "invalid_speeds": statuses["invalid"],
            "unsupported_speeds": statuses["valid_but_unsupported"],
            "conflicting_speeds": statuses["conflict"],
            "model_assumed_speeds": origins["model_assumed"],
            "speed_blockers": len(blockers),
            "upstream_relation_blockers": len(directed["blockers"]),
        },
        "record_coverage_complete": len(records) == len(directed["directed_segments"]),
        "formal_speed_complete": not blockers and not directed["blockers"],
        "blocker_stop_codes": dict(
            sorted(Counter(item["stop_code"] for item in blockers).items())
        ),
        "semantic_sha256": hashlib.sha256(payload).hexdigest(),
    }


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite speed artifact: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output_path.parent,
            prefix=f".{output_path.name}.", suffix=".tmp", delete=False
        ) as handle:
            json.dump(artifact, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, output_path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve v17 Directed Segment speeds.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    parser.add_argument("--scenario-context", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = None if args.scenario_context is None else json.loads(
        args.scenario_context.read_text(encoding="utf-8")
    )
    artifact = build_speed_production_artifact(
        args.input, profile=args.profile, scenario_context=context
    )
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 0 if artifact["formal_speed_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
