"""Load and semantically validate the governed v17 runtime interval context."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network_v17.yml"
)


class ScenarioContextError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        stop_code: str = "ACCESS_CONTEXT_MISSING",
        status: str = "unresolved",
    ) -> None:
        super().__init__(message)
        self.stop_code = stop_code
        self.status = status


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ScenarioContextError(
            f"YAML root must be an object: {path}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ScenarioContextError(
            f"JSON root must be an object: {path}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return value


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise ScenarioContextError(
            f"invalid repository context artifact: {relative}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_reference(reference: Mapping[str, Any]) -> Path:
    path = _repo_file(str(reference["path"]))
    if _sha256(path) != reference["sha256"]:
        raise ScenarioContextError(
            f"context artifact hash mismatch: {reference['path']}",
            stop_code="UNREGISTERED_RULE",
            status="invalid",
        )
    return path


def _validate_schema(instance: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(item) for item in errors[0].path) or "$"
        raise ScenarioContextError(
            f"context Schema violation at {location}: {errors[0].message}",
            stop_code="ACCESS_CONTEXT_MISSING",
            status="invalid",
        )


def _parse_timestamp(value: Any, field: str) -> datetime:
    try:
        result = datetime.fromisoformat(str(value))
    except ValueError as error:
        raise ScenarioContextError(f"invalid {field}: {value!r}") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ScenarioContextError(f"{field} must include a UTC offset")
    return result


def validate_governed_runtime_context(
    context: Mapping[str, Any], *, config: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    schema_path = _repo_file(str(context["schema"]))
    _validate_schema(context, schema_path)

    interval = context["interval"]
    start = _parse_timestamp(interval["start_timestamp"], "start_timestamp")
    end = _parse_timestamp(interval["end_timestamp"], "end_timestamp")
    if start >= end:
        raise ScenarioContextError("start_timestamp must precede end_timestamp")
    duration = int((end - start).total_seconds())
    if duration != interval["duration_seconds"]:
        raise ScenarioContextError("duration_seconds differs from timestamp interval")
    try:
        timezone = ZoneInfo(interval["timezone"])
    except ZoneInfoNotFoundError as error:
        raise ScenarioContextError("registered timezone is unavailable") from error
    for name, timestamp in (("start_timestamp", start), ("end_timestamp", end)):
        expected_offset = timestamp.astimezone(timezone).utcoffset()
        if timestamp.utcoffset() != expected_offset:
            raise ScenarioContextError(f"{name} offset differs from configured timezone")
    if config is not None and interval["timezone"] != config["scenario_context"]["timezone"]:
        raise ScenarioContextError("context timezone differs from v17 Configuration")

    holiday_reference = context["holiday_calendar"]
    holiday_path = _verify_reference(holiday_reference)
    holiday = _load_yaml(holiday_path)
    _validate_schema(holiday, _repo_file(str(holiday["schema"])))
    if holiday["calendar_id"] != holiday_reference["calendar_id"]:
        raise ScenarioContextError("holiday calendar ID differs from context reference")
    if holiday["calendar_version"] != holiday_reference["calendar_version"]:
        raise ScenarioContextError("holiday calendar version differs from context reference")
    if holiday["timezone"] != interval["timezone"]:
        raise ScenarioContextError("holiday calendar timezone differs from interval")
    local_date = start.astimezone(timezone).date().isoformat()
    if not holiday["coverage"]["start_date"] <= local_date <= holiday["coverage"]["end_date"]:
        raise ScenarioContextError("runtime date is outside holiday calendar coverage")
    holiday_dates = {item["date"] for item in holiday["holidays"]}
    expected_public_holiday = local_date in holiday_dates
    if holiday_reference["public_holiday"] is not expected_public_holiday:
        raise ScenarioContextError("public_holiday differs from registered calendar")

    vehicle = context["vehicle_context"]
    profile_path = _verify_reference(
        {"path": vehicle["profile_path"], "sha256": vehicle["profile_sha256"]}
    )
    profile = _load_yaml(profile_path)
    _validate_schema(profile, _repo_file(str(profile["schema"])))
    equality_fields = {
        "vehicle_profile_id": "vehicle_profile_id",
        "vehicle_class": "sumo_vclass",
        "maximum_permissible_mass_kg": "maximum_permissible_mass_kg",
        "length_m": "length_m",
        "width_m": "width_m",
        "height_m": "height_m",
        "trip_purpose": "trip_purpose",
        "permit_ids": "permit_ids",
    }
    for context_field, profile_field in equality_fields.items():
        if vehicle[context_field] != profile[profile_field]:
            raise ScenarioContextError(
                f"vehicle context differs from profile: {context_field}"
            )
    for field in (
        "maximum_permissible_mass_kg",
        "length_m",
        "width_m",
        "height_m",
    ):
        if vehicle[field] <= 0:
            raise ScenarioContextError(f"vehicle context must be positive: {field}")
    for field in ("permit_ids", "authorization_ids"):
        if not isinstance(vehicle[field], list):
            raise ScenarioContextError(f"context field must be an explicit array: {field}")

    purpose = vehicle["trip_purpose"]
    return {
        "scenario_context_id": context["scenario_context_id"],
        "start_timestamp": interval["start_timestamp"],
        "end_timestamp": interval["end_timestamp"],
        "timezone": interval["timezone"],
        "simulation_interval_seconds": interval["duration_seconds"],
        "holiday_calendar_id": holiday["calendar_id"],
        "holiday_calendar_version": holiday["calendar_version"],
        "public_holiday": holiday_reference["public_holiday"],
        "vehicle_profile_id": vehicle["vehicle_profile_id"],
        "vehicle_class": vehicle["vehicle_class"],
        "maximum_permissible_mass_kg": vehicle["maximum_permissible_mass_kg"],
        "length_m": vehicle["length_m"],
        "width_m": vehicle["width_m"],
        "height_m": vehicle["height_m"],
        "trip_purpose": purpose,
        "trip_purpose_destination": purpose == "destination",
        "trip_purpose_delivery": purpose == "delivery",
        "trip_purpose_customer": purpose == "customers",
        "permit_ids": list(vehicle["permit_ids"]),
        "permit_assignment": bool(vehicle["permit_ids"]),
        "authorization_ids": list(vehicle["authorization_ids"]),
        "private_authorization": bool(vehicle["authorization_ids"]),
    }


def load_governed_runtime_context(
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    config = _load_yaml(config_path)
    reference = config["scenario_context"]["governed_runtime_interval_context"]
    context_path = _verify_reference(reference)
    context = _load_yaml(context_path)
    if context["context_version"] != reference["version"]:
        raise ScenarioContextError("context version differs from Configuration")
    return validate_governed_runtime_context(context, config=config)
