"""Classify road-attribute criticality without selecting attribute values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from traffic_simulation.network.validate_attribute_classification import (
    calculate_record_sha256,
    file_sha256,
    validate_predicate_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
SCHEMA_DIR: Final = (
    REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/schemas"
)
CLASSIFICATION_SCHEMA: Final = (
    SCHEMA_DIR / "attribute_criticality_classification.schema.json"
)
ATTRIBUTES: Final = ("lanes", "maxspeed")


class CriticalityClassificationError(ValueError):
    """Raised when classification cannot produce a complete governed artifact."""


def _file_ref(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise CriticalityClassificationError(
            f"artifact path must be inside the repository: {path}"
        ) from error
    return {"path": relative, "sha256": file_sha256(resolved)}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CriticalityClassificationError(f"JSON root must be an object: {path}")
    return value


def _predicate_values(record: Mapping[str, Any]) -> dict[str, bool]:
    predicates = record["predicates"]
    return {name: bool(evidence["value"]) for name, evidence in predicates.items()}


RULE_LEVELS: Final = {
    "LANE-CRIT-001": "L0",
    "LANE-CRIT-002": "L3",
    "LANE-CRIT-003": "L3",
    "LANE-CRIT-004": "L3",
    "LANE-CRIT-005": "L3",
    "LANE-CRIT-006": "L2",
    "LANE-CRIT-007": "L1",
    "SPEED-CRIT-001": "S0",
    "SPEED-CRIT-002": "S3",
    "SPEED-CRIT-003": "S3",
    "SPEED-CRIT-004": "S3",
    "SPEED-CRIT-005": "S2",
    "SPEED-CRIT-006": "S1",
}


def _matches(
    attribute: str,
    profile: str,
    role: str,
    predicates: Mapping[str, bool],
) -> list[tuple[str, str]]:
    common_high = (
        predicates["is_calibration_segment"]
        or predicates["is_validation_segment"]
    )
    promoted = (
        predicates["is_accepted_delivery_route"]
        or predicates["is_sensitivity_elevated"]
    )
    if attribute == "lanes":
        rules = [
            ("LANE-CRIT-001", "L0", role == "excluded"),
            ("LANE-CRIT-002", "L3", common_high),
            (
                "LANE-CRIT-003",
                "L3",
                predicates["is_major_junction_approach"]
                or predicates["is_bridge"]
                or predicates["is_tunnel"]
                or predicates["is_grade_separated"],
            ),
            (
                "LANE-CRIT-004",
                "L3",
                any(
                    predicates[name]
                    for name in (
                        "has_directional_lane_semantics",
                        "has_reversible_lane_semantics",
                        "has_tidal_flow_semantics",
                        "has_turn_lane_semantics",
                        "has_bus_or_psv_lane_semantics",
                        "has_conflicting_lane_semantics",
                    )
                ),
            ),
            ("LANE-CRIT-005", "L3", promoted),
            (
                "LANE-CRIT-006",
                "L2",
                profile == "formal"
                and role != "excluded"
                and not common_high
                and not promoted
                and not any(
                    predicates[name]
                    for name in (
                        "is_major_junction_approach",
                        "is_bridge",
                        "is_tunnel",
                        "is_grade_separated",
                        "has_directional_lane_semantics",
                        "has_reversible_lane_semantics",
                        "has_tidal_flow_semantics",
                        "has_turn_lane_semantics",
                        "has_bus_or_psv_lane_semantics",
                        "has_conflicting_lane_semantics",
                    )
                ),
            ),
            (
                "LANE-CRIT-007",
                "L1",
                profile == "structural"
                and role != "excluded"
                and not common_high
                and not promoted
                and not any(
                    predicates[name]
                    for name in (
                        "is_major_junction_approach",
                        "is_bridge",
                        "is_tunnel",
                        "is_grade_separated",
                        "has_directional_lane_semantics",
                        "has_reversible_lane_semantics",
                        "has_tidal_flow_semantics",
                        "has_turn_lane_semantics",
                        "has_bus_or_psv_lane_semantics",
                        "has_conflicting_lane_semantics",
                    )
                ),
            ),
        ]
    else:
        rules = [
            ("SPEED-CRIT-001", "S0", role == "excluded"),
            ("SPEED-CRIT-002", "S3", common_high),
            (
                "SPEED-CRIT-003",
                "S3",
                any(
                    predicates[name]
                    for name in (
                        "has_directional_speed_semantics",
                        "has_conditional_speed_semantics",
                        "has_variable_speed_semantics",
                        "has_vehicle_specific_speed_semantics",
                        "has_advisory_or_multiple_speed_semantics",
                    )
                ),
            ),
            ("SPEED-CRIT-004", "S3", promoted),
            (
                "SPEED-CRIT-005",
                "S2",
                profile == "formal"
                and role != "excluded"
                and not common_high
                and not promoted
                and not any(
                    predicates[name]
                    for name in (
                        "has_directional_speed_semantics",
                        "has_conditional_speed_semantics",
                        "has_variable_speed_semantics",
                        "has_vehicle_specific_speed_semantics",
                        "has_advisory_or_multiple_speed_semantics",
                    )
                ),
            ),
            (
                "SPEED-CRIT-006",
                "S1",
                profile == "structural"
                and role != "excluded"
                and not common_high
                and not promoted
                and not any(
                    predicates[name]
                    for name in (
                        "has_directional_speed_semantics",
                        "has_conditional_speed_semantics",
                        "has_variable_speed_semantics",
                        "has_vehicle_specific_speed_semantics",
                        "has_advisory_or_multiple_speed_semantics",
                    )
                ),
            ),
        ]
    matches = [(rule_id, level) for rule_id, level, applies in rules if applies]
    if not matches:
        raise CriticalityClassificationError(
            f"no {attribute} criticality rule matched"
        )
    return matches


def validate_criticality_artifact(artifact: Mapping[str, Any]) -> None:
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        resource = Resource.from_contents(_load_json(path))
        registry = registry.with_resource(path.name, resource)
    schema = _load_json(CLASSIFICATION_SCHEMA)
    errors = sorted(
        Draft202012Validator(
            schema, registry=registry, format_checker=FormatChecker()
        ).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise CriticalityClassificationError(
            f"classification artifact schema failure at {pointer}: {error.message}"
        )
    records = artifact["records"]
    expected_order = sorted(
        records,
        key=lambda record: (
            int(record["osm_way_id"]),
            ATTRIBUTES.index(record["attribute"]),
        ),
    )
    if records != expected_order:
        raise CriticalityClassificationError(
            "classification records are not in canonical way and attribute order"
        )
    if len(records) != artifact["population_way_count"] * len(ATTRIBUTES):
        raise CriticalityClassificationError(
            "classification record count does not cover every way and attribute"
        )
    seen: set[str] = set()
    for record in records:
        record_id = record["classification_record_id"]
        expected_id = (
            f"acr:{record['osm_way_id']}:{record['attribute']}:{record['profile']}"
        )
        if record_id != expected_id:
            raise CriticalityClassificationError(
                f"classification record ID differs from tuple: {record_id}"
            )
        if record["profile"] != artifact["profile"]:
            raise CriticalityClassificationError(
                f"record profile differs from artifact profile: {record_id}"
            )
        if record_id in seen:
            raise CriticalityClassificationError(
                f"duplicate classification record: {record_id}"
            )
        seen.add(record_id)
        classification = record["classification"]
        selected = classification["selected_rule_id"]
        unknown_rules = [
            rule_id
            for rule_id in classification["matched_rule_ids"]
            if rule_id not in RULE_LEVELS
        ]
        if unknown_rules:
            raise CriticalityClassificationError(
                f"classification contains unknown rules: {unknown_rules}"
            )
        if classification["matched_rule_ids"][0] != selected:
            raise CriticalityClassificationError(
                f"selected rule is not the first matched rule: {record_id}"
            )
        if RULE_LEVELS[selected] != classification["criticality_level"]:
            raise CriticalityClassificationError(
                f"criticality level does not match selected rule: {record_id}"
            )
        if record["source_artifact_sha256"] != artifact["predicate_artifact"]["sha256"]:
            raise CriticalityClassificationError(
                f"record predicate hash differs from artifact reference: {record_id}"
            )
        if (
            record["classification_config_sha256"]
            != artifact["classification_policy"]["sha256"]
        ):
            raise CriticalityClassificationError(
                f"record policy hash differs from artifact reference: {record_id}"
            )
        if record["subgraph_role"] == "excluded" and classification[
            "criticality_level"
        ] not in {"L0", "S0"}:
            raise CriticalityClassificationError(
                f"excluded record has non-excluded criticality: {record_id}"
            )
        if calculate_record_sha256(record) != record["record_sha256"]:
            raise CriticalityClassificationError(
                f"classification record hash differs from content: {record_id}"
            )


def classify_predicate_artifact(
    predicate_path: Path,
    *,
    profile: str,
    policy_path: Path = CONFIG_PATH,
    predecessor_path: Path | None = None,
    revision_reason_code: str = "ACR-INITIAL",
) -> dict[str, Any]:
    """Return classification-only records; no attribute value is read or emitted."""

    if profile not in {"structural", "formal"}:
        raise CriticalityClassificationError(f"unsupported profile: {profile}")
    predicate_artifact = _load_json(predicate_path)
    predicate_result = validate_predicate_artifact(
        predicate_artifact, artifact_root=REPOSITORY_ROOT
    )
    if not predicate_result.valid:
        first = predicate_result.errors[0]
        raise CriticalityClassificationError(
            f"predicate artifact failed {first.code} at "
            f"{first.json_pointer}: {first.message}"
        )
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise CriticalityClassificationError("classification policy must be a mapping")
    if (
        predicate_artifact["config_id"] != policy.get("config_id")
        or predicate_artifact["config_version"] != policy.get("config_version")
    ):
        raise CriticalityClassificationError(
            "predicate artifact and classification policy identities differ"
        )

    predecessor_by_id: dict[str, Mapping[str, Any]] = {}
    if predecessor_path is not None:
        predecessor = _load_json(predecessor_path)
        validate_criticality_artifact(predecessor)
        if predecessor.get("profile") != profile:
            raise CriticalityClassificationError(
                "predecessor profile differs from requested profile"
            )
        predecessor_by_id = {
            record["classification_record_id"]: record
            for record in predecessor["records"]
        }

    predicate_hash = file_sha256(predicate_path)
    policy_hash = file_sha256(policy_path)
    records: list[dict[str, Any]] = []
    for source_record in predicate_artifact["records"]:
        values = _predicate_values(source_record)
        role = source_record["subgraph_role"]
        for attribute in ATTRIBUTES:
            record_id = (
                f"acr:{source_record['osm_way_id']}:{attribute}:{profile}"
            )
            matches = _matches(attribute, profile, role, values)
            prior = predecessor_by_id.get(record_id)
            revision = int(prior["record_revision"]) + 1 if prior else 1
            record = {
                "classification_record_id": record_id,
                "osm_way_id": source_record["osm_way_id"],
                "attribute": attribute,
                "profile": profile,
                "subgraph_role": role,
                "record_revision": revision,
                "record_sha256": "",
                "supersedes_record_sha256": (
                    prior["record_sha256"] if prior else None
                ),
                "revision_reason_code": revision_reason_code,
                "source_artifact_sha256": predicate_hash,
                "classification_config_sha256": policy_hash,
                "classification": {
                    "criticality_level": matches[0][1],
                    "selected_rule_id": matches[0][0],
                    "matched_rule_ids": [rule_id for rule_id, _ in matches],
                },
            }
            record["record_sha256"] = calculate_record_sha256(record)
            records.append(record)

    artifact = {
        "artifact_type": "attribute_criticality_classification",
        "schema_version": 1,
        "config_id": predicate_artifact["config_id"],
        "config_version": predicate_artifact["config_version"],
        "run_id": predicate_artifact["run_id"],
        "profile": profile,
        "complete": True,
        "relation_closed_osm": predicate_artifact["relation_closed_osm"],
        "predicate_artifact": _file_ref(predicate_path),
        "classification_policy": _file_ref(policy_path),
        "population_way_count": predicate_artifact["population_way_count"],
        "records": records,
    }
    validate_criticality_artifact(artifact)
    return artifact


def write_artifact(artifact: Mapping[str, Any], output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite classification: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify lanes and maxspeed criticality without resolving values"
    )
    parser.add_argument("--predicate-artifact", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("structural", "formal"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--policy", type=Path, default=CONFIG_PATH)
    parser.add_argument("--predecessor", type=Path)
    parser.add_argument("--revision-reason", default="ACR-INITIAL")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = classify_predicate_artifact(
        args.predicate_artifact,
        profile=args.profile,
        policy_path=args.policy,
        predecessor_path=args.predecessor,
        revision_reason_code=args.revision_reason,
    )
    write_artifact(artifact, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
