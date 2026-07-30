from __future__ import annotations

import argparse
import copy
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.classify_attribute_criticality import (
    validate_criticality_artifact,
)
from traffic_simulation.network.validate_attribute_classification import (
    calculate_record_sha256,
    validate_classification_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


NUMERIC_SPEED = re.compile(r"^[1-9][0-9]*(?:\.[0-9]*[1-9])?$")
LANE_COMPLEX_PREDICATES = {
    "has_directional_lane_semantics",
    "has_reversible_lane_semantics",
    "has_tidal_flow_semantics",
    "has_turn_lane_semantics",
    "has_bus_or_psv_lane_semantics",
    "has_conflicting_lane_semantics",
}
SPEED_CONDITIONAL_PREDICATES = {
    "has_conditional_speed_semantics",
    "has_variable_speed_semantics",
    "has_vehicle_specific_speed_semantics",
    "has_advisory_or_multiple_speed_semantics",
}


class AttributeResolutionError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AttributeResolutionError(f"JSON root must be an object: {path}")
    return value


def _repository_path(relative_path: str) -> Path:
    path = (REPOSITORY_ROOT / relative_path).resolve()
    root = REPOSITORY_ROOT.resolve()
    if path != root and root not in path.parents:
        raise AttributeResolutionError(
            f"artifact reference escapes repository: {relative_path}"
        )
    return path


def _file_ref(path: Path) -> dict[str, str]:
    from traffic_simulation.network.validate_attribute_classification import (
        file_sha256,
    )

    return {
        "path": path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix(),
        "sha256": file_sha256(path),
    }


def load_osm_attribute_values(
    osm_path: Path, way_ids: set[str]
) -> dict[str, dict[str, str]]:
    values: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way":
            way_id = element.attrib.get("id")
            if way_id in way_ids:
                values[way_id] = {
                    tag.attrib["k"]: tag.attrib.get("v", "")
                    for tag in element.findall("tag")
                    if "k" in tag.attrib
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    missing = way_ids - set(values)
    if missing:
        sample = sorted(missing, key=int)[:10]
        raise AttributeResolutionError(
            f"classification references {len(missing)} absent OSM ways; sample={sample}"
        )
    return values


def _predicate_values(
    predicate_artifact: Mapping[str, Any],
) -> dict[str, dict[str, bool]]:
    result: dict[str, dict[str, bool]] = {}
    for record in predicate_artifact["records"]:
        result[record["osm_way_id"]] = {
            name: bool(evidence["value"])
            for name, evidence in record["predicates"].items()
        }
    return result


def _empty_requirement() -> dict[str, Any]:
    return {
        "required": False,
        "requirement_rule_id": None,
        "minimum_authority": None,
        "description": None,
    }


def _high_requirement() -> dict[str, Any]:
    return {
        "required": True,
        "requirement_rule_id": "EVID-REQ-HIGH-001",
        "minimum_authority": "reviewed_public_source",
        "description": (
            "High-criticality resolution requires governed "
            "attribute-specific evidence."
        ),
    }


def _base_resolution(
    *,
    action: str,
    state: str,
    value: int | str | None,
    unit: str | None,
    requirement: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    rule_id: str | None = None,
    selected: str | None = None,
    rejected: Sequence[str] = (),
    conflict_rule: str | None = None,
    review_status: str = "machine_classified",
    reviewer: str | None = None,
    reviewed_at: str | None = None,
    stop_codes: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "resolution_action": action,
        "resolution_rule_id": rule_id,
        "value_state": state,
        "resolved_value": value,
        "unit": unit,
        "evidence_requirement": copy.deepcopy(dict(requirement)),
        "evidence_candidates": copy.deepcopy(list(candidates)),
        "selected_evidence_id": selected,
        "rejected_evidence_ids": list(rejected),
        "conflict_resolution_rule_id": conflict_rule,
        "review_status": review_status,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "stop_failure_codes": list(stop_codes),
    }


def _stop(
    *,
    state: str,
    requirement: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    code: str,
    human_review: bool = False,
) -> dict[str, Any]:
    return _base_resolution(
        action="require_human_review" if human_review else "stop_unresolved",
        state=state,
        value=None,
        unit=None,
        requirement=requirement,
        candidates=candidates,
        review_status="review_required" if human_review else "stopped",
        stop_codes=[code],
    )


def resolve_record(
    classification_record: Mapping[str, Any],
    *,
    osm_attributes: Mapping[str, Any],
    predicates: Mapping[str, bool],
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one value without mutating or replacing its classification."""

    context = context or {}
    candidates = context.get("evidence_candidates", [])
    if not isinstance(candidates, list):
        raise AttributeResolutionError("evidence_candidates must be an array")
    classification = classification_record["classification"]
    level = classification["criticality_level"]
    high = level in {"L3", "S3"}
    requirement = _high_requirement() if high else _empty_requirement()
    attribute = classification_record["attribute"]
    profile = classification_record["profile"]

    if context.get("requested_structural_placeholder") is True and profile == "formal":
        return _stop(
            state="invalid",
            requirement=requirement,
            candidates=candidates,
            code="AC008",
        )

    if classification_record["subgraph_role"] == "excluded":
        return _base_resolution(
            action="exclude",
            state="excluded",
            value=None,
            unit=None,
            requirement=requirement,
            candidates=candidates,
        )

    applicable = [
        candidate
        for candidate in candidates
        if candidate.get("applicable") is True
        and candidate.get("rejection_reason_code") is None
    ]
    rejected = [
        candidate["evidence_id"]
        for candidate in candidates
        if candidate not in applicable
    ]
    if candidates:
        if len(applicable) != 1:
            return _stop(
                state="conflict" if len(applicable) > 1 else "valid_but_unsupported",
                requirement=requirement,
                candidates=candidates,
                code="AC006" if len(applicable) > 1 else "AC005",
            )
        review = context.get("review")
        if not isinstance(review, Mapping) or not review.get("reviewer") or not review.get(
            "reviewed_at"
        ):
            return _stop(
                state="conflict",
                requirement=requirement,
                candidates=candidates,
                code="AC007",
                human_review=True,
            )
        selected = applicable[0]
        value = selected["value"]
        if attribute == "lanes":
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                return _stop(
                    state="invalid",
                    requirement=requirement,
                    candidates=candidates,
                    code="AC005",
                )
        elif not isinstance(value, str) or NUMERIC_SPEED.fullmatch(value) is None:
            return _stop(
                state="invalid",
                requirement=requirement,
                candidates=candidates,
                code="AC005",
            )
        return _base_resolution(
            action="adopt_external_evidence",
            state="authoritative_external",
            value=value,
            unit="lanes" if attribute == "lanes" else "km/h",
            requirement=requirement,
            candidates=candidates,
            selected=selected["evidence_id"],
            rejected=rejected,
            conflict_rule=(
                "EVID-CONFLICT-AUTHORITY-001" if len(candidates) > 1 else None
            ),
            review_status="reviewed",
            reviewer=str(review["reviewer"]),
            reviewed_at=str(review["reviewed_at"]),
        )

    if attribute == "lanes":
        complex_semantics = any(
            predicates.get(name, False) for name in LANE_COMPLEX_PREDICATES
        )
        raw = osm_attributes.get("lanes")
        explicit = (
            raw
            if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0
            else int(raw)
            if isinstance(raw, str) and raw.isdigit() and int(raw) > 0
            else None
        )
        state = "directionally_asymmetric" if complex_semantics else "missing"
        placeholder_value: int | str = 1
        placeholder_rule = "LANE-PLACEHOLDER-001"
        unit = "lanes"
    else:
        conditional = any(
            predicates.get(name, False) for name in SPEED_CONDITIONAL_PREDICATES
        )
        directional = predicates.get("has_directional_speed_semantics", False)
        raw = osm_attributes.get("maxspeed")
        explicit = (
            raw
            if isinstance(raw, str) and NUMERIC_SPEED.fullmatch(raw) is not None
            else None
        )
        complex_semantics = conditional or directional
        state = (
            "conditional"
            if conditional
            else "directionally_asymmetric"
            if directional
            else "missing"
        )
        placeholder_value = "30"
        placeholder_rule = "SPEED-PLACEHOLDER-001"
        unit = "km/h"

    if complex_semantics:
        return _stop(
            state=state,
            requirement=requirement,
            candidates=candidates,
            code="AC007" if high else "AC005",
            human_review=high,
        )

    if explicit is not None:
        if high:
            review = context.get("review")
            if not isinstance(review, Mapping) or not review.get(
                "reviewer"
            ) or not review.get("reviewed_at"):
                return _stop(
                    state="valid_but_unsupported",
                    requirement=requirement,
                    candidates=candidates,
                    code="AC007",
                    human_review=True,
                )
            review_status = "reviewed"
            reviewer = str(review["reviewer"])
            reviewed_at = str(review["reviewed_at"])
        else:
            review_status = "machine_classified"
            reviewer = None
            reviewed_at = None
        return _base_resolution(
            action="adopt_explicit",
            state="explicit_osm",
            value=explicit,
            unit=unit,
            requirement=requirement,
            candidates=candidates,
            review_status=review_status,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
        )

    if profile == "structural" and level in {"L1", "S1"}:
        return _base_resolution(
            action="apply_structural_placeholder",
            state="structural_placeholder",
            value=placeholder_value,
            unit=unit,
            requirement=requirement,
            candidates=candidates,
            rule_id=placeholder_rule,
        )

    return _stop(
        state="missing",
        requirement=requirement,
        candidates=candidates,
        code="AC005",
    )


def resolve_classification_artifact(
    classification_path: Path,
    *,
    osm_path: Path,
    context_path: Path | None = None,
) -> dict[str, Any]:
    classification_artifact = _load_json(classification_path)
    validate_criticality_artifact(classification_artifact)
    before = copy.deepcopy(classification_artifact)

    predicate_path = _repository_path(
        classification_artifact["predicate_artifact"]["path"]
    )
    predicate_artifact = _load_json(predicate_path)
    predicate_by_way = _predicate_values(predicate_artifact)
    way_ids = {
        record["osm_way_id"] for record in classification_artifact["records"]
    }
    osm_by_way = load_osm_attribute_values(osm_path, way_ids)
    contexts: Mapping[str, Any] = {}
    if context_path is not None:
        context_artifact = _load_json(context_path)
        contexts = context_artifact.get("records", {})
        if not isinstance(contexts, Mapping):
            raise AttributeResolutionError("resolution context records must be an object")

    records: list[dict[str, Any]] = []
    blocker_counts: dict[str, int] = {}
    for source in classification_artifact["records"]:
        record = copy.deepcopy(source)
        record["resolution"] = resolve_record(
            source,
            osm_attributes=osm_by_way[source["osm_way_id"]],
            predicates=predicate_by_way[source["osm_way_id"]],
            context=contexts.get(source["classification_record_id"], {}),
        )
        for code in record["resolution"]["stop_failure_codes"]:
            blocker_counts[code] = blocker_counts.get(code, 0) + 1
        record["record_sha256"] = calculate_record_sha256(record)
        records.append(record)

    if classification_artifact != before:
        raise AttributeResolutionError("classification artifact was mutated")
    for source, resolved in zip(classification_artifact["records"], records):
        if source["classification"] != resolved["classification"]:
            raise AttributeResolutionError(
                f"classification changed during resolution: "
                f"{source['classification_record_id']}"
            )

    blockers = [
        {
            "code": code,
            "message": f"{count} attribute tuples stopped with {code}",
            "component": "attribute_criticality",
            "formal_blocker": True,
            "context": {"record_count": count},
        }
        for code, count in sorted(blocker_counts.items())
    ]
    artifact = {
        "artifact_type": "attribute_classification",
        "schema_version": 1,
        "config_id": classification_artifact["config_id"],
        "config_version": classification_artifact["config_version"],
        "run_id": classification_artifact["run_id"],
        "profile": classification_artifact["profile"],
        "complete": not blockers,
        "relation_closed_osm": classification_artifact["relation_closed_osm"],
        "predicate_artifact": classification_artifact["predicate_artifact"],
        "classification_policy": classification_artifact[
            "classification_policy"
        ],
        "population_way_count": classification_artifact[
            "population_way_count"
        ],
        "records": records,
        "blockers": blockers,
    }
    validation = validate_classification_artifact(
        artifact, artifact_root=REPOSITORY_ROOT
    )
    if not validation.valid:
        first = validation.errors[0]
        raise AttributeResolutionError(
            f"integrated artifact failed {first.code} at "
            f"{first.json_pointer}: {first.message}"
        )
    return artifact


def write_artifact_atomic(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite resolution: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        artifact, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve lanes and maxspeed values while preserving criticality results"
        )
    )
    parser.add_argument("--classification", required=True, type=Path)
    parser.add_argument("--osm", required=True, type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = resolve_classification_artifact(
        args.classification,
        osm_path=args.osm,
        context_path=args.context,
    )
    write_artifact_atomic(artifact, args.output)
    print(
        json.dumps(
            {
                "valid": True,
                "complete": artifact["complete"],
                "record_count": len(artifact["records"]),
                "blockers": artifact["blockers"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
