"""Parse and evaluate v17 conditional access without final permission resolution."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.static_access_v17 import (
    ACCESS_BASE_KEYS,
    StaticAccessError,
    _evaluate_context,
    _parse_access_key,
    _rule_validator,
    _scope_sets,
    _source_way_tags,
    _vehicle_domain,
    build_static_access_production_artifact,
    normalize_static_access_rules,
    write_artifact_atomic,
)


WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
WEEKDAY_INDEX = {value: index for index, value in enumerate(WEEKDAYS)}
CLAUSE_PATTERN = re.compile(r"^\s*([a-z_]+)\s*@\s*\((.*)\)\s*$", re.DOTALL)
TIME_RANGE_PATTERN = re.compile(
    r"^(?P<start>[0-2]?\d:[0-5]\d)-(?P<end>[0-2]?\d:[0-5]\d)$"
)
WEEKDAY_PATTERN = re.compile(
    r"^(?P<start>Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?P<end>Mo|Tu|We|Th|Fr|Sa|Su))?$"
)
DATE_PATTERN = re.compile(
    r"^(?P<start>\d{4}-\d{2}-\d{2})(?:--(?P<end>\d{4}-\d{2}-\d{2}))?$"
)
COMPARISON_PATTERN = re.compile(
    r"^(?P<field>mass|maxweight|length|width|height)(?P<operator><=|>=|=|<|>)(?P<value>\d+(?:\.\d+)?)$"
)
GOVERNED_VEHICLES = {
    "passenger",
    "taxi",
    "bus",
    "coach",
    "delivery",
    "truck",
    "motorcycle",
}


@dataclass(frozen=True)
class ConditionalClause:
    value: str
    condition: tuple[Any, ...]
    source_order: int
    source_text: str


class ConditionalAccessError(StaticAccessError):
    pass


def _stop(message: str, *, stop_code: str, status: str) -> ConditionalAccessError:
    return ConditionalAccessError(message, stop_code=stop_code, status=status)


def _unsupported(message: str) -> ConditionalAccessError:
    return _stop(
        message,
        stop_code="ACCESS_CONDITIONAL_SYNTAX_UNSUPPORTED",
        status="valid_but_unsupported",
    )


def _split_top_level(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    index = 0
    while index < len(text):
        character = text[index]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise _unsupported("unbalanced conditional parentheses")
        if depth == 0 and text.startswith(separator, index):
            parts.append(text[start:index].strip())
            start = index + len(separator)
            index = start
            continue
        index += 1
    if depth != 0:
        raise _unsupported("unbalanced conditional parentheses")
    parts.append(text[start:].strip())
    return parts


def _strip_outer_parentheses(text: str) -> str:
    result = text.strip()
    while result.startswith("(") and result.endswith(")"):
        depth = 0
        wraps_all = True
        for index, character in enumerate(result):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(result) - 1:
                    wraps_all = False
                    break
            if depth < 0:
                raise _unsupported("unbalanced conditional parentheses")
        if depth != 0:
            raise _unsupported("unbalanced conditional parentheses")
        if not wraps_all:
            break
        result = result[1:-1].strip()
    return result


def _split_word_operator(text: str, operator: str) -> list[str]:
    result: list[str] = []
    depth = 0
    start = 0
    index = 0
    token = f" {operator} "
    while index < len(text):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        if depth == 0 and text.startswith(token, index):
            result.append(text[start:index].strip())
            start = index + len(token)
            index = start
            continue
        index += 1
    if result:
        result.append(text[start:].strip())
    return result


def _split_implicit_and(text: str) -> list[str]:
    result: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character.isspace() and depth == 0:
            part = text[start:index].strip()
            if part:
                result.append(part)
            start = index + 1
    part = text[start:].strip()
    if part:
        result.append(part)
    return result


def _minutes(value: str) -> int:
    hour_text, minute_text = value.split(":")
    hour, minute = int(hour_text), int(minute_text)
    if hour > 24 or (hour == 24 and minute != 0):
        raise _unsupported(f"invalid clock time: {value}")
    return hour * 60 + minute


def _parse_atom(text: str) -> tuple[Any, ...]:
    weekday = WEEKDAY_PATTERN.fullmatch(text)
    if weekday:
        start = WEEKDAY_INDEX[weekday.group("start")]
        end = WEEKDAY_INDEX[weekday.group("end") or weekday.group("start")]
        values = (
            set(range(start, end + 1))
            if start <= end
            else set(range(start, 7)) | set(range(0, end + 1))
        )
        return ("weekday", tuple(sorted(values)))
    time_range = TIME_RANGE_PATTERN.fullmatch(text)
    if time_range:
        return (
            "time",
            _minutes(time_range.group("start")),
            _minutes(time_range.group("end")),
        )
    calendar_date = DATE_PATTERN.fullmatch(text)
    if calendar_date:
        try:
            start = date.fromisoformat(calendar_date.group("start"))
            end = date.fromisoformat(calendar_date.group("end") or calendar_date.group("start"))
        except ValueError as error:
            raise _unsupported(f"invalid calendar date: {text}") from error
        if end < start:
            raise _unsupported(f"reversed calendar-date interval: {text}")
        return ("date", start.isoformat(), end.isoformat())
    if text == "PH":
        return ("public_holiday",)
    if text in GOVERNED_VEHICLES:
        return ("vehicle_class", text)
    if text.startswith("trip_purpose=") and text.split("=", 1)[1] in {
        "destination",
        "delivery",
        "customers",
    }:
        return ("trip_purpose", text.split("=", 1)[1])
    if text.startswith("permit:") and len(text.split(":", 1)[1]) > 0:
        return ("permit", text.split(":", 1)[1])
    if text.startswith("authorization:") and len(text.split(":", 1)[1]) > 0:
        return ("authorization", text.split(":", 1)[1])
    comparison = COMPARISON_PATTERN.fullmatch(text)
    if comparison:
        return (
            "comparison",
            comparison.group("field"),
            comparison.group("operator"),
            float(comparison.group("value")),
        )
    raise _unsupported(f"unregistered conditional token: {text!r}")


def parse_condition(text: str) -> tuple[Any, ...]:
    normalized = re.sub(r"(?<=\d)\s*-\s*(?=\d)", "-", text.strip())
    normalized = _strip_outer_parentheses(normalized)
    if not normalized:
        raise _unsupported("empty conditional expression")
    for operator in ("OR", "AND"):
        parts = _split_word_operator(normalized, operator)
        if parts:
            if any(not part for part in parts):
                raise _unsupported(f"empty operand for {operator}")
            return (operator.lower(), tuple(parse_condition(part) for part in parts))
    implicit = _split_implicit_and(normalized)
    if len(implicit) > 1:
        return ("and", tuple(parse_condition(part) for part in implicit))
    return _parse_atom(normalized)


def parse_conditional_value(value: str) -> tuple[ConditionalClause, ...]:
    clauses: list[ConditionalClause] = []
    for source_order, source_clause in enumerate(_split_top_level(value, ";")):
        match = CLAUSE_PATTERN.fullmatch(source_clause)
        if match is None:
            raise _unsupported(f"unsupported conditional clause: {source_clause!r}")
        clauses.append(
            ConditionalClause(
                value=match.group(1),
                condition=parse_condition(match.group(2)),
                source_order=source_order,
                source_text=source_clause,
            )
        )
    if not clauses:
        raise _unsupported("conditional value has no clauses")
    return tuple(clauses)


def _required(context: Mapping[str, Any], field: str) -> Any:
    if field not in context:
        raise _stop(
            f"required conditional context is missing: {field}",
            stop_code="ACCESS_CONTEXT_MISSING",
            status="unresolved",
        )
    return context[field]


def _compare(left: float, operator: str, right: float) -> bool:
    return {
        "<": left < right,
        "<=": left <= right,
        "=": left == right,
        ">=": left >= right,
        ">": left > right,
    }[operator]


def _evaluate(condition: tuple[Any, ...], context: Mapping[str, Any]) -> bool:
    kind = condition[0]
    if kind == "and":
        values = [_evaluate(item, context) for item in condition[1]]
        return all(values)
    if kind == "or":
        values = [_evaluate(item, context) for item in condition[1]]
        return any(values)
    if kind == "weekday":
        weekday = context.get("_weekday_index")
        if weekday is None:
            value = _required(context, "weekday")
            if value not in WEEKDAY_INDEX:
                raise _stop(
                    f"invalid weekday context: {value!r}",
                    stop_code="ACCESS_CONTEXT_MISSING",
                    status="unresolved",
                )
            weekday = WEEKDAY_INDEX[value]
        return weekday in condition[1]
    if kind == "time":
        minute = context.get("_minute")
        if minute is None:
            minute = _minutes(str(_required(context, "time")))
        start, end = condition[1], condition[2]
        if start < end:
            return start <= minute < end
        return minute >= start or minute < end
    if kind == "date":
        current = context.get("_date")
        if current is None:
            current = date.fromisoformat(str(_required(context, "date")))
        return date.fromisoformat(condition[1]) <= current <= date.fromisoformat(condition[2])
    if kind == "public_holiday":
        _required(context, "holiday_calendar_version")
        value = _required(context, "public_holiday")
        if not isinstance(value, bool):
            raise _stop(
                "public_holiday context must be Boolean",
                stop_code="ACCESS_CONTEXT_MISSING",
                status="unresolved",
            )
        return value
    if kind == "vehicle_class":
        return _required(context, "vehicle_class") == condition[1]
    if kind == "trip_purpose":
        return _required(context, "trip_purpose") == condition[1]
    if kind == "permit":
        return condition[1] in _required(context, "permit_ids")
    if kind == "authorization":
        return condition[1] in _required(context, "authorization_ids")
    if kind == "comparison":
        field_map = {
            "mass": "actual_mass_kg",
            "maxweight": "maximum_permissible_mass_kg",
            "length": "length_m",
            "width": "width_m",
            "height": "height_m",
        }
        value = _required(context, field_map[condition[1]])
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise _stop(
                f"conditional numeric context is invalid: {field_map[condition[1]]}",
                stop_code="ACCESS_CONTEXT_MISSING",
                status="unresolved",
            )
        return _compare(float(value), condition[2], condition[3])
    raise AssertionError(f"unknown condition node: {kind}")


def _selected_clause(
    clauses: Sequence[ConditionalClause], context: Mapping[str, Any]
) -> ConditionalClause | None:
    selected = None
    for clause in clauses:
        if _evaluate(clause.condition, context):
            selected = clause
    return selected


def _time_boundaries(condition: tuple[Any, ...]) -> set[int]:
    if condition[0] in {"and", "or"}:
        result: set[int] = set()
        for item in condition[1]:
            result.update(_time_boundaries(item))
        return result
    if condition[0] == "time":
        return {condition[1], condition[2]}
    return set()


def _interval_points(
    clauses: Sequence[ConditionalClause], context: Mapping[str, Any]
) -> tuple[dict[str, Any], ...] | None:
    if "interval" in context:
        pieces = str(context["interval"]).split("/")
        if len(pieces) != 2:
            raise _stop(
                "conditional interval must be start/end",
                stop_code="ACCESS_CONTEXT_MISSING",
                status="unresolved",
            )
        start, end = _minutes(pieces[0]), _minutes(pieces[1])
        if end <= start:
            end += 1440
        weekday_value = context.get("weekday")
        weekday = WEEKDAY_INDEX.get(str(weekday_value)) if weekday_value is not None else None
        boundaries = {start, end}
        if start < 1440 < end:
            boundaries.add(1440)
        for clause in clauses:
            for boundary in _time_boundaries(clause.condition):
                for offset in (0, 1440):
                    absolute = boundary + offset
                    if start < absolute < end:
                        boundaries.add(absolute)
        ordered = sorted(boundaries)
        points = []
        for left, right in zip(ordered, ordered[1:]):
            minute = (left + right) // 2
            point = dict(context)
            point["_minute"] = minute % 1440
            if weekday is not None:
                point["_weekday_index"] = (weekday + minute // 1440) % 7
            points.append(point)
        return tuple(points)
    if "start_timestamp" in context or "end_timestamp" in context:
        start = datetime.fromisoformat(str(_required(context, "start_timestamp")))
        end = datetime.fromisoformat(str(_required(context, "end_timestamp")))
        _required(context, "timezone")
        if end <= start:
            raise _stop(
                "conditional interval end must follow start",
                stop_code="ACCESS_CONTEXT_MISSING",
                status="unresolved",
            )
        boundaries = {start, end}
        day = start.date() - timedelta(days=1)
        while day <= end.date():
            midnight = datetime.combine(
                day, datetime.min.time(), tzinfo=start.tzinfo
            )
            if start < midnight < end:
                boundaries.add(midnight)
            for clause in clauses:
                for minute in _time_boundaries(clause.condition):
                    boundary = midnight + timedelta(minutes=minute)
                    if start < boundary < end:
                        boundaries.add(boundary)
            day += timedelta(days=1)
        ordered = sorted(boundaries)
        points = []
        for left, right in zip(ordered, ordered[1:]):
            current = left + (right - left) / 2
            point = dict(context)
            point["_minute"] = current.hour * 60 + current.minute
            point["_weekday_index"] = current.weekday()
            point["_date"] = current.date()
            points.append(point)
        return tuple(points)
    return None


def evaluate_conditional_value(
    value: str, context: Mapping[str, Any]
) -> ConditionalClause | None:
    clauses = parse_conditional_value(value)
    interval_points = _interval_points(clauses, context)
    if interval_points is None:
        return _selected_clause(clauses, context)
    selected = [_selected_clause(clauses, point) for point in interval_points]
    signatures = {None if item is None else item.value for item in selected}
    if len(signatures) > 1:
        raise _stop(
            "conditional access changes within the simulation interval",
            stop_code="ACCESS_WITHIN_INTERVAL_CHANGE",
            status="conflict",
        )
    matched = [item for item in selected if item is not None]
    return max(matched, key=lambda item: item.source_order) if matched else None


def _static_key(conditional_key: str) -> str:
    parts = [part for part in conditional_key.split(":") if part != "conditional"]
    return ":".join(parts)


def _conditional_rule_id(
    source_way_id: int,
    source_key: str,
    lane_position: int | None,
    clause: ConditionalClause,
) -> str:
    payload = json.dumps(
        {
            "source_way_id": source_way_id,
            "source_key": source_key,
            "lane_position": lane_position,
            "source_order": clause.source_order,
            "source_clause": clause.source_text,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"car:{hashlib.sha256(payload).hexdigest()}"


def _promote_rule(
    rule: Mapping[str, Any],
    *,
    source_key: str,
    source_expression: str,
    clause: ConditionalClause,
) -> dict[str, Any]:
    result = copy.deepcopy(dict(rule))
    positions = result["target_scope"]["lane_scope"]["positions"]
    lane_position = positions[0] if positions else None
    result["rule_id"] = _conditional_rule_id(
        result["source_element"]["id"], source_key, lane_position, clause
    )
    result["source_key"] = source_key
    result["source_value"] = source_expression
    condition_hash = hashlib.sha256(clause.source_text.encode("utf-8")).hexdigest()
    result["temporal_domain"] = [f"condition:{condition_hash}"]
    result["source_order"] = clause.source_order
    result["provenance"] = {
        **result["provenance"],
        "normalization": "conditional_access_v17",
        "conditional_grammar_id": "OSM_CONDITIONAL_V17_CORE",
        "matched_clause": clause.source_text,
        "last_match_applied": True,
    }
    _rule_validator().validate(result)
    return result


def evaluate_conditional_access_rules(
    *,
    source_way_id: int,
    conditional_tags: Mapping[str, str],
    tags: Mapping[str, str],
    lane_counts: Mapping[str, int],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    for source_key in sorted(conditional_tags):
        static_key = _static_key(source_key)
        parsed_key = _parse_access_key(static_key)
        if parsed_key is None:
            raise _unsupported(f"unsupported conditional access key: {source_key}")
        base_key, direction, lane_scoped = parsed_key
        vehicle_domain = _vehicle_domain(base_key)
        if context.get("vehicle_class") not in vehicle_domain:
            evaluations.append(
                {"source_key": source_key, "outcome": "vehicle_not_applicable"}
            )
            continue
        if direction in {"forward", "backward"} and lane_counts.get(direction, 0) == 0:
            evaluations.append(
                {"source_key": source_key, "outcome": "direction_not_applicable"}
            )
            continue
        expression = conditional_tags[source_key]
        if lane_scoped:
            target_direction = direction
            if target_direction == "both":
                active = [item for item in ("forward", "backward") if lane_counts.get(item, 0)]
                if len(active) != 1:
                    raise _unsupported(
                        f"unsuffixed conditional lane access is ambiguous: {source_key}"
                    )
                target_direction = active[0]
            entries = expression.split("|")
            if len(entries) != lane_counts.get(target_direction, 0):
                raise _stop(
                    f"conditional lane vector length differs for {source_key}",
                    stop_code="LANE_VECTOR_LENGTH_MISMATCH",
                    status="conflict",
                )
            selected_entries: list[str] = []
            clauses_by_position: dict[int, ConditionalClause] = {}
            for position, entry in enumerate(entries):
                if not entry:
                    selected_entries.append("")
                    continue
                selected = evaluate_conditional_value(entry, context)
                selected_entries.append("" if selected is None else selected.value)
                if selected is not None:
                    clauses_by_position[position] = selected
            static_tags = {**tags, static_key: "|".join(selected_entries)}
            built = normalize_static_access_rules(
                source_way_id=source_way_id,
                tags=static_tags,
                lane_counts=lane_counts,
                candidate_keys={static_key},
            )["rules"]
            for rule in built:
                position = rule["target_scope"]["lane_scope"]["positions"][0]
                rules.append(
                    _promote_rule(
                        rule,
                        source_key=source_key,
                        source_expression=expression,
                        clause=clauses_by_position[position],
                    )
                )
            evaluations.append(
                {
                    "source_key": source_key,
                    "outcome": "matched" if built else "not_matched",
                    "matched_lane_positions": sorted(clauses_by_position),
                }
            )
        else:
            selected = evaluate_conditional_value(expression, context)
            if selected is None:
                evaluations.append(
                    {"source_key": source_key, "outcome": "not_matched"}
                )
                continue
            built = normalize_static_access_rules(
                source_way_id=source_way_id,
                tags={**tags, static_key: selected.value},
                lane_counts=lane_counts,
                candidate_keys={static_key},
            )["rules"]
            rules.extend(
                _promote_rule(
                    rule,
                    source_key=source_key,
                    source_expression=expression,
                    clause=selected,
                )
                for rule in built
            )
            evaluations.append(
                {
                    "source_key": source_key,
                    "outcome": "matched",
                    "matched_clause_order": selected.source_order,
                }
            )
    rules.sort(key=lambda item: item["rule_id"])
    return {"rules": rules, "evaluations": evaluations}


def _profile_context(base: Mapping[str, Any]) -> dict[str, Any]:
    from traffic_simulation.network.static_access_v17 import _load_yaml, VEHICLE_PROFILE_PATH

    profile = _load_yaml(VEHICLE_PROFILE_PATH)
    return {
        **dict(base),
        "trip_purpose": profile["trip_purpose"],
        "maximum_permissible_mass_kg": profile["maximum_permissible_mass_kg"],
        "length_m": profile["length_m"],
        "width_m": profile["width_m"],
        "height_m": profile["height_m"],
        "permit_ids": list(profile["permit_ids"]),
    }


def build_conditional_access_production_artifact(
    input_path: Path,
    *,
    profile: str,
    scenario_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    static = build_static_access_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )
    context = _profile_context(static["managed_scenario_context"])
    source_tags_by_way = _source_way_tags(input_path)
    lane_counts_by_way: dict[int, dict[str, int]] = {}
    for value in static["static_maxima"]:
        way_id = int(value["source_way_id"])
        direction = value["source_direction"]
        counts = lane_counts_by_way.setdefault(way_id, {})
        counts[direction] = max(
            counts.get(direction, 0), int(value["lane_position"]) + 1
        )
    normalized: list[dict[str, Any]] = []
    tuple_results: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    rules_by_way: dict[int, list[dict[str, Any]]] = {}
    blocked_ways: set[int] = set()
    for item in static["normalized_rules"]:
        way_id = int(item["source_way_id"])
        conditional_tags = item["deferred_conditional_tags"]
        if not conditional_tags:
            continue
        lane_counts = lane_counts_by_way.get(way_id, {})
        source_tags = source_tags_by_way[way_id]
        try:
            result = evaluate_conditional_access_rules(
                source_way_id=way_id,
                conditional_tags=conditional_tags,
                tags=source_tags,
                lane_counts=lane_counts,
                context=context,
            )
            rules_by_way[way_id] = result["rules"]
            normalized.append(
                {
                    "source_way_id": way_id,
                    "rules": result["rules"],
                    "evaluations": result["evaluations"],
                }
            )
        except (StaticAccessError, KeyError, ValueError) as error:
            blocked_ways.add(way_id)
            if isinstance(error, StaticAccessError):
                status, stop_code = error.status, error.stop_code
            else:
                status, stop_code = "unresolved", "ACCESS_CONTEXT_MISSING"
            blockers.append(
                {
                    "scope": "source_way",
                    "source_way_id": way_id,
                    "resolution_status": status,
                    "stop_code": stop_code,
                    "message": str(error),
                }
            )
    for value in static["static_maxima"]:
        way_id = int(value["source_way_id"])
        if way_id in blocked_ways:
            continue
        applicable = []
        direction_lane_count = lane_counts_by_way.get(way_id, {}).get(
            value["source_direction"], 1
        )
        for rule in rules_by_way.get(way_id, []):
            directions, lanes = _scope_sets(rule, direction_lane_count)
            if (
                value["source_direction"] in directions
                and int(value["lane_position"]) in lanes
                and context["vehicle_class"] in rule["vehicle_domain"]
            ):
                applicable.append(_evaluate_context(rule, context))
        tuple_results.append(
            {
                **value,
                "applicable_conditional_rule_ids": sorted(
                    item["rule_id"] for item in applicable
                ),
                "conditional_effects": sorted({item["effect"] for item in applicable}),
                "pending_conditional_integration": False,
                "pending_final_permission_resolution": True,
            }
        )
    payload = json.dumps(
        {"conditional_rules": normalized, "access_candidates": tuple_results},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 17,
        "artifact_type": "conditional_access_production_collection",
        "configuration_id": static["configuration_id"],
        "population_version": static["population_version"],
        "profile": profile,
        "source": static["source"],
        "static_access_semantic_sha256": static["semantic_sha256"],
        "scenario_context": context,
        "conditional_rules": normalized,
        "access_candidates": tuple_results,
        "blockers": blockers,
        "upstream_static_access_blockers": static["blockers"],
        "upstream_lane_blockers": static["upstream_lane_blockers"],
        "upstream_relation_blockers": static["upstream_relation_blockers"],
        "counts": {
            "source_ways_with_conditional_tags": len(normalized) + len(blockers),
            "normalized_conditional_source_ways": len(normalized),
            "normalized_conditional_rules": sum(len(item["rules"]) for item in normalized),
            "conditional_access_lane_tuples": len(tuple_results),
            "lane_tuples_with_applicable_conditional_rules": sum(
                bool(item["applicable_conditional_rule_ids"]) for item in tuple_results
            ),
            "conditional_access_blockers": len(blockers),
            "upstream_static_access_blockers": len(static["blockers"]),
            "upstream_lane_blockers": len(static["upstream_lane_blockers"]),
            "upstream_relation_blockers": len(static["upstream_relation_blockers"]),
        },
        "blocker_stop_codes": dict(
            sorted(
                {
                    code: sum(item["stop_code"] == code for item in blockers)
                    for code in {item["stop_code"] for item in blockers}
                }.items()
            )
        ),
        "semantic_sha256": hashlib.sha256(payload).hexdigest(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate v17 conditional access without final dominance."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    parser.add_argument("--scenario-context", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = None
    if args.scenario_context is not None:
        context = json.loads(args.scenario_context.read_text(encoding="utf-8"))
    artifact = build_conditional_access_production_artifact(
        args.input, profile=args.profile, scenario_context=context
    )
    write_artifact_atomic(artifact, args.output)
    print(json.dumps(artifact["counts"], sort_keys=True))
    return 1 if (
        artifact["blockers"]
        or artifact["upstream_static_access_blockers"]
        or artifact["upstream_lane_blockers"]
        or artifact["upstream_relation_blockers"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
