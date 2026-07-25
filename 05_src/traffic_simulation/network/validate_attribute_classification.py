"""Validate attribute-classification artifacts beyond JSON Schema constraints."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

import rfc8785
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from traffic_simulation.paths import REPOSITORY_ROOT


SCHEMA_DIR = (
    REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/schemas"
)
SPECIFICATION_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/"
    "attribute_criticality_and_evidence_specification.md"
)
SCHEMA_BY_ARTIFACT_TYPE = {
    "attribute_classification_predicates": "classification_predicates.schema.json",
    "attribute_classification": "attribute_classification.schema.json",
    "attribute_classification_fixture": "attribute_classification_fixture.schema.json",
}
ATTRIBUTE_ORDER = {"lanes": 0, "maxspeed": 1}
PROFILE_ORDER = {"structural": 0, "formal": 1}
STOP_ACTIONS = {"require_human_review", "stop_unresolved"}
STOP_STATUSES = {"review_required", "stopped"}
RESOLUTION_STATE_MACHINE = {
    "adopt_explicit": (
        {"explicit_osm"},
        {"machine_classified", "reviewed"},
        True,
    ),
    "derive_osm_rule": (
        {"derived_osm_rule"},
        {"machine_classified", "reviewed"},
        True,
    ),
    "adopt_external_evidence": (
        {"authoritative_external"},
        {"reviewed"},
        True,
    ),
    "apply_governed_rule": (
        {"derived_validated_model"},
        {"machine_classified", "reviewed"},
        True,
    ),
    "apply_structural_placeholder": (
        {"structural_placeholder"},
        {"machine_classified", "reviewed"},
        True,
    ),
    "require_human_review": (
        {
            "missing",
            "conflict",
            "conditional",
            "valid_but_unsupported",
            "directionally_asymmetric",
        },
        {"review_required"},
        False,
    ),
    "stop_unresolved": (
        {
            "missing",
            "unresolved",
            "conflict",
            "valid_but_unsupported",
            "conditional",
            "directionally_asymmetric",
            "invalid",
        },
        {"stopped"},
        False,
    ),
    "exclude": ({"excluded"}, {"machine_classified"}, False),
}
FIXTURE_ID_PATTERNS = {
    "positive": re.compile(r"AC-POS-[0-9]{3}\Z"),
    "negative": re.compile(r"AC[0-9]{3}-NEG-[0-9]{3}\Z"),
    "boundary": re.compile(r"AC-BND-[0-9]{3}\Z"),
    "repeat": re.compile(r"AC-REP-[0-9]{3}\Z"),
}


@dataclass(frozen=True)
class SemanticValidationError:
    """One stable, machine-readable semantic validation failure."""

    code: str
    json_pointer: str
    message: str
    expected: Any = None
    actual: Any = None


@dataclass(frozen=True)
class SemanticValidationResult:
    """Collected validation outcome; validation never stops at the first error."""

    valid: bool
    errors: tuple[SemanticValidationError, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [asdict(error) for error in self.errors],
        }


class ErrorCollector:
    def __init__(self) -> None:
        self.errors: list[SemanticValidationError] = []

    def add(
        self,
        code: str,
        pointer: str,
        message: str,
        *,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        self.errors.append(
            SemanticValidationError(
                code=code,
                json_pointer=pointer,
                message=message,
                expected=expected,
                actual=actual,
            )
        )

    def result(self) -> SemanticValidationResult:
        return SemanticValidationResult(not self.errors, tuple(self.errors))


def _json_pointer(parts: Iterable[Any]) -> str:
    encoded = []
    for part in parts:
        encoded.append(str(part).replace("~", "~0").replace("/", "~1"))
    return "/" + "/".join(encoded) if encoded else ""


def _schema_registry(schema_dir: Path = SCHEMA_DIR) -> Registry:
    resources = []
    for path in schema_dir.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validate_schema(
    artifact: Mapping[str, Any],
    schema_name: str,
    collector: ErrorCollector,
    schema_dir: Path,
) -> None:
    schema = json.loads((schema_dir / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(schema_dir),
        format_checker=FormatChecker(),
    )
    for error in sorted(validator.iter_errors(artifact), key=lambda item: list(item.path)):
        collector.add(
            "ACV000",
            _json_pointer(error.absolute_path),
            f"JSON Schema validation failed: {error.message}",
            actual=error.instance,
        )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Return RFC 8785 JSON Canonicalization Scheme bytes."""

    return rfc8785.dumps(value)


def calculate_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash a record after omitting only its self-referential hash field."""

    payload = dict(record)
    payload.pop("record_sha256", None)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _resolve_relative_path(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    root = root.resolve()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate


def _validate_file_ref(
    ref: Any,
    pointer: str,
    collector: ErrorCollector,
    root: Path,
) -> Path | None:
    if not isinstance(ref, Mapping):
        return None
    relative_path = ref.get("path")
    expected_hash = ref.get("sha256")
    if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
        return None
    path = _resolve_relative_path(root, relative_path)
    if path is None:
        collector.add(
            "ACV014",
            f"{pointer}/path",
            "artifact path escapes the configured artifact root",
            actual=relative_path,
        )
        return None
    if not path.is_file():
        collector.add(
            "ACV014",
            f"{pointer}/path",
            "referenced artifact does not exist",
            actual=relative_path,
        )
        return None
    actual_hash = file_sha256(path)
    if actual_hash != expected_hash:
        collector.add(
            "ACV014",
            f"{pointer}/sha256",
            "referenced artifact SHA-256 does not match file content",
            expected=expected_hash,
            actual=actual_hash,
        )
    return path


def _validate_source_hash(
    sha256: Any,
    pointer: str,
    collector: ErrorCollector,
    source_index: Mapping[str, Path],
) -> None:
    if not isinstance(sha256, str):
        return
    path = source_index.get(sha256)
    if path is None:
        collector.add(
            "ACV014",
            pointer,
            "source SHA-256 is not registered in the validator source index",
            actual=sha256,
        )
        return
    if not path.is_file():
        collector.add(
            "ACV014",
            pointer,
            "registered source artifact does not exist",
            actual=str(path),
        )
        return
    actual_hash = file_sha256(path)
    if actual_hash != sha256:
        collector.add(
            "ACV014",
            pointer,
            "registered source artifact SHA-256 does not match",
            expected=sha256,
            actual=actual_hash,
        )


def _register_predicate_registry_sources(
    registry_path: Path,
    collector: ErrorCollector,
    source_paths: dict[str, Path],
    artifact_root: Path,
    schema_dir: Path,
) -> None:
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        collector.add(
            "ACV014",
            "/source_registry",
            f"predicate source registry cannot be read as JSON: {error}",
        )
        return
    if not isinstance(registry, Mapping):
        collector.add(
            "ACV014",
            "/source_registry",
            "predicate source registry root must be an object",
            actual=registry,
        )
        return
    _validate_schema(
        registry,
        "predicate_source_registry.schema.json",
        collector,
        schema_dir,
    )
    references: list[tuple[Any, str]] = [
        (registry.get("relation_closed_osm"), "/source_registry/relation_closed_osm"),
        (registry.get("role_source"), "/source_registry/role_source"),
    ]
    acceptance = registry.get("population_acceptance")
    if isinstance(acceptance, Mapping) and acceptance.get("acceptance_artifact") is not None:
        references.append(
            (
                acceptance.get("acceptance_artifact"),
                "/source_registry/population_acceptance/acceptance_artifact",
            )
        )
    external_sources = registry.get("external_predicate_sources")
    if isinstance(external_sources, Mapping):
        for predicate, source in external_sources.items():
            if isinstance(source, Mapping):
                references.append(
                    (
                        source.get("source"),
                        f"/source_registry/external_predicate_sources/{predicate}/source",
                    )
                )
    overrides = registry.get("predicate_overrides")
    if isinstance(overrides, list):
        for index, override in enumerate(overrides):
            if isinstance(override, Mapping):
                references.append(
                    (
                        override.get("source"),
                        f"/source_registry/predicate_overrides/{index}/source",
                    )
                )
    for ref, pointer in references:
        path = _validate_file_ref(ref, pointer, collector, artifact_root)
        if path is not None and isinstance(ref, Mapping):
            source_paths[str(ref.get("sha256"))] = path


def validate_predicate_artifact(
    artifact: Mapping[str, Any],
    *,
    artifact_root: Path = REPOSITORY_ROOT,
    source_index: Mapping[str, Path] | None = None,
    schema_dir: Path = SCHEMA_DIR,
) -> SemanticValidationResult:
    collector = ErrorCollector()
    _validate_schema(
        artifact, "classification_predicates.schema.json", collector, schema_dir
    )
    source_paths = dict(source_index or {})
    registry_path: Path | None = None
    for field in ("relation_closed_osm", "source_registry", "predicate_policy"):
        path = _validate_file_ref(
            artifact.get(field), f"/{field}", collector, artifact_root
        )
        ref = artifact.get(field)
        if path is not None and isinstance(ref, Mapping):
            source_paths[str(ref.get("sha256"))] = path
        if field == "source_registry":
            registry_path = path
    if registry_path is not None:
        _register_predicate_registry_sources(
            registry_path,
            collector,
            source_paths,
            artifact_root,
            schema_dir,
        )

    records = artifact.get("records")
    if not isinstance(records, list):
        return collector.result()
    population = artifact.get("population_way_count")
    if isinstance(population, int) and len(records) != population:
        collector.add(
            "ACV016",
            "/records",
            "predicate record count does not equal population_way_count",
            expected=population,
            actual=len(records),
        )

    seen_way_ids: set[str] = set()
    excluded_true_predicates = {
        "is_calibration_segment",
        "is_validation_segment",
        "is_major_junction_approach",
        "is_accepted_delivery_route",
        "is_sensitivity_elevated",
    }
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        base = f"/records/{index}"
        way_id = record.get("osm_way_id")
        if isinstance(way_id, str):
            if way_id in seen_way_ids:
                collector.add(
                    "ACV016",
                    f"{base}/osm_way_id",
                    "predicate osm_way_id is duplicated",
                    actual=way_id,
                )
            seen_way_ids.add(way_id)

        role = record.get("subgraph_role")
        role_evidence = record.get("subgraph_role_evidence")
        if isinstance(role_evidence, Mapping):
            asserted_role = role_evidence.get("asserted_role")
            if asserted_role != role:
                collector.add(
                    "ACV015",
                    f"{base}/subgraph_role_evidence/asserted_role",
                    "asserted role does not equal subgraph_role",
                    expected=role,
                    actual=asserted_role,
                )
            _validate_source_hash(
                role_evidence.get("source_artifact_sha256"),
                f"{base}/subgraph_role_evidence/source_artifact_sha256",
                collector,
                source_paths,
            )

        predicates = record.get("predicates")
        if not isinstance(predicates, Mapping):
            continue
        true_predicates = {
            name
            for name, evidence in predicates.items()
            if isinstance(evidence, Mapping) and evidence.get("value") is True
        }
        if role == "excluded":
            for name in sorted(excluded_true_predicates & true_predicates):
                collector.add(
                    "ACV016",
                    f"{base}/predicates/{name}/value",
                    "excluded way has a prohibited true predicate",
                    expected=False,
                    actual=True,
                )
        if {
            "is_calibration_segment",
            "is_validation_segment",
        } <= true_predicates:
            collector.add(
                "ACV016",
                f"{base}/predicates",
                "calibration and independent-validation predicates are both true",
            )
        for name, evidence in predicates.items():
            if isinstance(evidence, Mapping):
                _validate_source_hash(
                    evidence.get("source_artifact_sha256"),
                    f"{base}/predicates/{name}/source_artifact_sha256",
                    collector,
                    source_paths,
                )
    return collector.result()


def _load_rule_priority(policy_path: Path | None) -> dict[str, list[str]] | None:
    if policy_path is None or not policy_path.is_file():
        return None
    with policy_path.open(encoding="utf-8") as handle:
        if policy_path.suffix.lower() == ".json":
            policy = json.load(handle)
        else:
            policy = yaml.safe_load(handle)
    if not isinstance(policy, Mapping):
        return None
    road_policy = policy.get("road_criticality", policy)
    if not isinstance(road_policy, Mapping):
        return None
    priority = road_policy.get("classification_rule_priority")
    if not isinstance(priority, Mapping):
        return None
    result: dict[str, list[str]] = {}
    for attribute in ("lanes", "maxspeed"):
        values = priority.get(attribute)
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            return None
        result[attribute] = values
    return result


def _record_sort_key(record: Mapping[str, Any]) -> tuple[int, int, int, int]:
    try:
        way_id = int(str(record.get("osm_way_id")))
    except ValueError:
        way_id = 2**63 - 1
    return (
        way_id,
        ATTRIBUTE_ORDER.get(str(record.get("attribute")), 99),
        PROFILE_ORDER.get(str(record.get("profile")), 99),
        int(record.get("record_revision", 0))
        if isinstance(record.get("record_revision"), int)
        else 0,
    )


def _validate_evidence_references(
    resolution: Mapping[str, Any],
    base: str,
    collector: ErrorCollector,
    source_index: Mapping[str, Path],
) -> None:
    candidates = resolution.get("evidence_candidates")
    if not isinstance(candidates, list):
        return
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            continue
        evidence_id = candidate.get("evidence_id")
        if not isinstance(evidence_id, str):
            continue
        if evidence_id in by_id:
            collector.add(
                "ACV007",
                f"{base}/evidence_candidates/{index}/evidence_id",
                "evidence_id is duplicated",
                actual=evidence_id,
            )
        by_id[evidence_id] = candidate
        _validate_source_hash(
            candidate.get("source_sha256"),
            f"{base}/evidence_candidates/{index}/source_sha256",
            collector,
            source_index,
        )

    selected = resolution.get("selected_evidence_id")
    rejected = resolution.get("rejected_evidence_ids")
    rejected_ids = rejected if isinstance(rejected, list) else []
    if isinstance(selected, str) and selected not in by_id:
        collector.add(
            "ACV007",
            f"{base}/selected_evidence_id",
            "selected evidence does not exist in evidence_candidates",
            actual=selected,
        )
    for index, evidence_id in enumerate(rejected_ids):
        if evidence_id not in by_id:
            collector.add(
                "ACV007",
                f"{base}/rejected_evidence_ids/{index}",
                "rejected evidence does not exist in evidence_candidates",
                actual=evidence_id,
            )
    if isinstance(selected, str) and selected in rejected_ids:
        collector.add(
            "ACV007",
            f"{base}/selected_evidence_id",
            "selected evidence is also rejected",
            actual=selected,
        )
    if resolution.get("resolution_action") == "adopt_external_evidence":
        candidate = by_id.get(selected) if isinstance(selected, str) else None
        if candidate is None:
            collector.add(
                "ACV008",
                f"{base}/selected_evidence_id",
                "external evidence adoption requires a selected candidate",
                actual=selected,
            )
        elif candidate.get("applicable") is not True:
            collector.add(
                "ACV008",
                f"{base}/selected_evidence_id",
                "external evidence adoption selected an inapplicable candidate",
                expected=True,
                actual=candidate.get("applicable"),
            )


def _validate_resolution_state(
    resolution: Mapping[str, Any],
    base: str,
    collector: ErrorCollector,
    code: str,
) -> None:
    action = resolution.get("resolution_action")
    contract = RESOLUTION_STATE_MACHINE.get(action)
    if contract is None:
        return
    states, statuses, value_required = contract
    state = resolution.get("value_state")
    status = resolution.get("review_status")
    value = resolution.get("resolved_value")
    valid_value = value is not None if value_required else value is None
    if state not in states or status not in statuses or not valid_value:
        collector.add(
            code,
            base,
            "resolution action, value state, resolved value and review status are inconsistent",
            expected={
                "value_states": sorted(states),
                "review_statuses": sorted(statuses),
                "resolved_value_required": value_required,
            },
            actual={
                "resolution_action": action,
                "value_state": state,
                "resolved_value": value,
                "review_status": status,
            },
        )


def _validate_evidence_requirement(
    level: Any,
    resolution: Mapping[str, Any],
    base: str,
    collector: ErrorCollector,
    code: str,
) -> None:
    requirement = resolution.get("evidence_requirement")
    if not isinstance(requirement, Mapping) or not isinstance(level, str):
        return
    expected = level in {"L3", "S3"}
    if requirement.get("required") is not expected:
        collector.add(
            code,
            f"{base}/evidence_requirement/required",
            "evidence requirement does not match the criticality level",
            expected=expected,
            actual=requirement.get("required"),
        )


def _history_by_hash(
    history_artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for artifact in history_artifacts:
        records = artifact.get("records")
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, Mapping) and isinstance(
                record.get("record_sha256"), str
            ):
                result[str(record["record_sha256"])] = record
    return result


def _validate_revision(
    record: Mapping[str, Any],
    base: str,
    history: Mapping[str, Mapping[str, Any]],
    collector: ErrorCollector,
) -> None:
    revision = record.get("record_revision")
    if not isinstance(revision, int) or revision <= 1:
        return
    predecessor_hash = record.get("supersedes_record_sha256")
    predecessor = history.get(predecessor_hash) if isinstance(predecessor_hash, str) else None
    if predecessor is None:
        collector.add(
            "ACV011",
            f"{base}/supersedes_record_sha256",
            "revision predecessor was not supplied in history artifacts",
            actual=predecessor_hash,
        )
        return
    if predecessor.get("classification_record_id") != record.get(
        "classification_record_id"
    ):
        collector.add(
            "ACV011",
            f"{base}/supersedes_record_sha256",
            "revision predecessor has a different classification_record_id",
            expected=record.get("classification_record_id"),
            actual=predecessor.get("classification_record_id"),
        )
    expected_revision = (
        predecessor.get("record_revision") + 1
        if isinstance(predecessor.get("record_revision"), int)
        else None
    )
    if expected_revision != revision:
        collector.add(
            "ACV011",
            f"{base}/record_revision",
            "record_revision is not predecessor revision plus one",
            expected=expected_revision,
            actual=revision,
        )
    seen = {str(record.get("record_sha256"))}
    current = predecessor
    while isinstance(current, Mapping):
        current_hash = current.get("record_sha256")
        if isinstance(current_hash, str):
            if current_hash in seen:
                collector.add(
                    "ACV011",
                    f"{base}/supersedes_record_sha256",
                    "revision chain contains a cycle",
                    actual=current_hash,
                )
                break
            seen.add(current_hash)
        prior_hash = current.get("supersedes_record_sha256")
        if prior_hash is None:
            break
        current = history.get(prior_hash) if isinstance(prior_hash, str) else None
        if current is None:
            collector.add(
                "ACV011",
                f"{base}/supersedes_record_sha256",
                "revision chain is incomplete",
                actual=prior_hash,
            )
            break


def validate_classification_artifact(
    artifact: Mapping[str, Any],
    *,
    artifact_root: Path = REPOSITORY_ROOT,
    source_index: Mapping[str, Path] | None = None,
    history_artifacts: Sequence[Mapping[str, Any]] = (),
    schema_dir: Path = SCHEMA_DIR,
) -> SemanticValidationResult:
    collector = ErrorCollector()
    _validate_schema(
        artifact, "attribute_classification.schema.json", collector, schema_dir
    )
    source_paths = dict(source_index or {})
    resolved_paths: dict[str, Path | None] = {}
    for field in (
        "relation_closed_osm",
        "predicate_artifact",
        "classification_policy",
    ):
        path = _validate_file_ref(
            artifact.get(field), f"/{field}", collector, artifact_root
        )
        resolved_paths[field] = path
        ref = artifact.get(field)
        if path is not None and isinstance(ref, Mapping):
            source_paths[str(ref.get("sha256"))] = path
    priorities = _load_rule_priority(resolved_paths["classification_policy"])
    if priorities is None:
        collector.add(
            "ACV006",
            "/classification_policy",
            "classification policy does not define lane and maxspeed rule priority",
        )

    records = artifact.get("records")
    if not isinstance(records, list):
        return collector.result()
    artifact_profile = artifact.get("profile")
    complete = artifact.get("complete")
    population = artifact.get("population_way_count")
    seen_ids: set[str] = set()
    seen_tuples: set[tuple[Any, Any, Any]] = set()
    attributes_by_way: dict[str, list[str]] = {}
    history = _history_by_hash(history_artifacts)
    predicate_ref = artifact.get("predicate_artifact")
    policy_ref = artifact.get("classification_policy")
    expected_source_hash = (
        predicate_ref.get("sha256") if isinstance(predicate_ref, Mapping) else None
    )
    expected_config_hash = (
        policy_ref.get("sha256") if isinstance(policy_ref, Mapping) else None
    )

    expected_order = sorted(records, key=_record_sort_key)
    if records != expected_order:
        collector.add(
            "ACV013",
            "/records",
            "records are not in canonical way, attribute, profile and revision order",
        )

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        base = f"/records/{index}"
        way_id = record.get("osm_way_id")
        attribute = record.get("attribute")
        profile = record.get("profile")
        record_id = record.get("classification_record_id")
        expected_id = f"acr:{way_id}:{attribute}:{profile}"
        if record_id != expected_id:
            collector.add(
                "ACV001",
                f"{base}/classification_record_id",
                "classification_record_id does not match osm_way_id, attribute, and profile",
                expected=expected_id,
                actual=record_id,
            )
        if profile != artifact_profile:
            collector.add(
                "ACV002",
                f"{base}/profile",
                "record profile does not match artifact profile",
                expected=artifact_profile,
                actual=profile,
            )
        if isinstance(record_id, str):
            if record_id in seen_ids:
                collector.add(
                    "ACV003",
                    f"{base}/classification_record_id",
                    "classification_record_id is duplicated",
                    actual=record_id,
                )
            seen_ids.add(record_id)
        tuple_key = (way_id, attribute, profile)
        if tuple_key in seen_tuples:
            collector.add(
                "ACV004",
                base,
                "osm_way_id, attribute and profile tuple is duplicated",
                actual=list(tuple_key),
            )
        seen_tuples.add(tuple_key)
        if isinstance(way_id, str) and isinstance(attribute, str):
            attributes_by_way.setdefault(way_id, []).append(attribute)

        classification = record.get("classification")
        if isinstance(classification, Mapping):
            selected_rule = classification.get("selected_rule_id")
            matched_rules = classification.get("matched_rule_ids")
            if isinstance(matched_rules, list) and selected_rule not in matched_rules:
                collector.add(
                    "ACV005",
                    f"{base}/classification/selected_rule_id",
                    "selected_rule_id is not present in matched_rule_ids",
                    actual=selected_rule,
                )
            if (
                priorities is not None
                and attribute in priorities
                and isinstance(matched_rules, list)
                and matched_rules
            ):
                priority = priorities[str(attribute)]
                known_matches = [rule for rule in priority if rule in matched_rules]
                if not known_matches:
                    collector.add(
                        "ACV006",
                        f"{base}/classification/matched_rule_ids",
                        "matched_rule_ids contain no rule registered by policy",
                        actual=matched_rules,
                    )
                elif selected_rule != known_matches[0]:
                    collector.add(
                        "ACV006",
                        f"{base}/classification/selected_rule_id",
                        "selected rule is not the highest-priority matched rule",
                        expected=known_matches[0],
                        actual=selected_rule,
                    )

        resolution = record.get("resolution")
        if isinstance(resolution, Mapping):
            _validate_resolution_state(
                resolution, f"{base}/resolution", collector, "ACV009"
            )
            level = (
                classification.get("criticality_level")
                if isinstance(classification, Mapping)
                else None
            )
            _validate_evidence_requirement(
                level,
                resolution,
                f"{base}/resolution",
                collector,
                "ACV009",
            )
            _validate_evidence_references(
                resolution, f"{base}/resolution", collector, source_paths
            )
            if complete is True and (
                resolution.get("resolution_action") in STOP_ACTIONS
                or resolution.get("review_status") in STOP_STATUSES
            ):
                collector.add(
                    "ACV009",
                    f"{base}/resolution",
                    "complete artifact contains an unresolved or review-pending record",
                    actual={
                        "resolution_action": resolution.get("resolution_action"),
                        "review_status": resolution.get("review_status"),
                    },
                )

        expected_hash = record.get("record_sha256")
        try:
            actual_hash = calculate_record_sha256(record)
        except (rfc8785.CanonicalizationError, TypeError, ValueError) as error:
            collector.add(
                "ACV012",
                f"{base}/record_sha256",
                f"record cannot be canonicalized using RFC 8785: {error}",
            )
        else:
            if expected_hash != actual_hash:
                collector.add(
                    "ACV012",
                    f"{base}/record_sha256",
                    "record_sha256 does not match RFC 8785 canonical content",
                    expected=expected_hash,
                    actual=actual_hash,
                )
        _validate_revision(record, base, history, collector)
        source_hash = record.get("source_artifact_sha256")
        if source_hash != expected_source_hash:
            collector.add(
                "ACV014",
                f"{base}/source_artifact_sha256",
                "record source hash does not equal predicate_artifact SHA-256",
                expected=expected_source_hash,
                actual=source_hash,
            )
        _validate_source_hash(
            source_hash,
            f"{base}/source_artifact_sha256",
            collector,
            source_paths,
        )
        config_hash = record.get("classification_config_sha256")
        if config_hash != expected_config_hash:
            collector.add(
                "ACV014",
                f"{base}/classification_config_sha256",
                "record config hash does not equal classification_policy SHA-256",
                expected=expected_config_hash,
                actual=config_hash,
            )
        _validate_source_hash(
            config_hash,
            f"{base}/classification_config_sha256",
            collector,
            source_paths,
        )

    way_count = len(attributes_by_way)
    if complete is True and isinstance(population, int) and way_count != population:
        collector.add(
            "ACV010",
            "/population_way_count",
            "unique classified way count does not equal population_way_count",
            expected=population,
            actual=way_count,
        )
    if complete is True and isinstance(population, int) and len(records) != population * 2:
        collector.add(
            "ACV010",
            "/records",
            "classification record count does not equal population_way_count times two",
            expected=population * 2,
            actual=len(records),
        )
    if complete is True:
        for way_id, attributes in sorted(
            attributes_by_way.items(),
            key=lambda item: (
                int(item[0]) if str(item[0]).isdigit() else 2**63 - 1
            ),
        ):
            for required_attribute in ("lanes", "maxspeed"):
                if attributes.count(required_attribute) != 1:
                    collector.add(
                        "ACV010",
                        "/records",
                        "way does not have exactly one record for each required attribute",
                        expected={
                            "osm_way_id": way_id,
                            "attribute": required_attribute,
                            "count": 1,
                        },
                        actual=attributes.count(required_attribute),
                    )
    return collector.result()


def _decode_pointer(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON Pointer: {pointer}")
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _remove_pointer(value: Any, pointer: str) -> None:
    tokens = _decode_pointer(pointer)
    if not tokens:
        raise ValueError("the document root cannot be excluded")
    parent = value
    for token in tokens[:-1]:
        if isinstance(parent, list):
            parent = parent[int(token)]
        else:
            parent = parent[token]
    final = tokens[-1]
    if isinstance(parent, list):
        del parent[int(final)]
    else:
        parent.pop(final, None)


def _validate_repeat(
    artifact: Mapping[str, Any],
    collector: ErrorCollector,
    baseline_output: Path | None,
    repeated_output: Path | None,
) -> None:
    assertion = artifact.get("repeat_assertion")
    if artifact.get("case_type") != "repeat" or not isinstance(assertion, Mapping):
        return
    if baseline_output is None or repeated_output is None:
        collector.add(
            "ACV019",
            "/repeat_assertion",
            "repeat fixture requires baseline and repeated output files",
        )
        return
    for path, field in (
        (baseline_output, "baseline_output_sha256"),
        (repeated_output, "repeated_output_sha256"),
    ):
        if not path.is_file():
            collector.add(
                "ACV019",
                f"/repeat_assertion/{field}",
                "repeat output file does not exist",
                actual=str(path),
            )
            return
        actual_hash = file_sha256(path)
        if assertion.get(field) != actual_hash:
            collector.add(
                "ACV019",
                f"/repeat_assertion/{field}",
                "repeat output SHA-256 does not match",
                expected=assertion.get(field),
                actual=actual_hash,
            )
    if not baseline_output.is_file() or not repeated_output.is_file():
        return
    mode = assertion.get("comparison_mode")
    if mode == "byte_equal":
        equal = baseline_output.read_bytes() == repeated_output.read_bytes()
    else:
        try:
            baseline = json.loads(baseline_output.read_text(encoding="utf-8"))
            repeated = json.loads(repeated_output.read_text(encoding="utf-8"))
            for pointer in assertion.get("excluded_json_pointers", []):
                _remove_pointer(baseline, pointer)
                _remove_pointer(repeated, pointer)
            equal = canonical_json_bytes(baseline) == canonical_json_bytes(repeated)
        except (
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            rfc8785.CanonicalizationError,
        ) as error:
            collector.add(
                "ACV019",
                "/repeat_assertion",
                f"repeat canonical comparison failed: {error}",
            )
            return
    if not equal:
        collector.add(
            "ACV019",
            "/repeat_assertion",
            "repeat outputs are not equal under the selected comparison mode",
            expected=True,
            actual=False,
        )


def _validate_fixture_assertions(
    artifact: Mapping[str, Any],
    expected: Mapping[str, Any],
    collector: ErrorCollector,
) -> None:
    records = expected.get("records")
    record_values = records if isinstance(records, list) else []
    policy = expected.get("record_emission_policy")
    if isinstance(policy, Mapping):
        has_records = bool(record_values)
        for field in ("records_emitted", "resolution_emitted"):
            if policy.get(field) is not has_records:
                collector.add(
                    "ACV022",
                    f"/expected/record_emission_policy/{field}",
                    "record-emission policy does not match expected records",
                    expected=has_records,
                    actual=policy.get(field),
                )
        publication_expected = expected.get("outcome") == "success"
        if policy.get("artifact_publication_allowed") is not publication_expected:
            collector.add(
                "ACV022",
                "/expected/record_emission_policy/artifact_publication_allowed",
                "artifact publication policy does not match fixture outcome",
                expected=publication_expected,
                actual=policy.get("artifact_publication_allowed"),
            )

    assertions = expected.get("assertions")
    if not isinstance(assertions, list):
        return
    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, Mapping):
            continue
        assertion_type = assertion.get("type")
        assertion_expected = assertion.get("expected")
        values = assertion_expected if isinstance(assertion_expected, Mapping) else {}
        pointer = f"/expected/assertions/{index}"
        if assertion_type == "rule_priority":
            multiple = [
                record
                for record in record_values
                if isinstance(record, Mapping)
                and isinstance(record.get("classification"), Mapping)
                and len(record["classification"].get("matched_rule_ids", [])) > 1
            ]
            selected = [
                record["classification"]["selected_rule_id"] for record in multiple
            ]
            if not multiple or selected != values.get("selected_rules"):
                collector.add(
                    "ACV022",
                    pointer,
                    "rule-priority assertion is not observable in expected records",
                    expected=values,
                    actual={"selected_rules": selected},
                )
        elif assertion_type == "evidence_selection":
            resolutions = [
                record.get("resolution")
                for record in record_values
                if isinstance(record, Mapping)
                and isinstance(record.get("resolution"), Mapping)
            ]
            rejected_inapplicable = False
            resolved_conflict = False
            for resolution in resolutions:
                candidates = {
                    candidate.get("evidence_id"): candidate
                    for candidate in resolution.get("evidence_candidates", [])
                    if isinstance(candidate, Mapping)
                }
                rejected = resolution.get("rejected_evidence_ids", [])
                rejected_inapplicable |= any(
                    evidence_id in candidates
                    and candidates[evidence_id].get("applicable") is False
                    for evidence_id in rejected
                )
                resolved_conflict |= (
                    len(candidates) > 1
                    and isinstance(resolution.get("selected_evidence_id"), str)
                    and bool(rejected)
                    and resolution.get("conflict_resolution_rule_id")
                    == values.get("conflict_resolution_rule_id")
                )
            if (
                values.get("reject_inapplicable") is True
                and not rejected_inapplicable
            ) or (
                values.get("resolve_applicable_conflict") is True
                and not resolved_conflict
            ):
                collector.add(
                    "ACV022",
                    pointer,
                    "evidence-selection assertion is not observable in records",
                    expected=values,
                )
        elif assertion_type == "repeated_output_equality":
            repeat = artifact.get("repeat_assertion")
            if not isinstance(repeat, Mapping) or values.get("repeat_count") != 2:
                collector.add(
                    "ACV022",
                    pointer,
                    "repeat assertion lacks its two-run comparison contract",
                    expected=values,
                    actual=repeat,
                )


def validate_fixture_artifact(
    artifact: Mapping[str, Any],
    *,
    artifact_root: Path = REPOSITORY_ROOT,
    specification_path: Path = SPECIFICATION_PATH,
    baseline_output: Path | None = None,
    repeated_output: Path | None = None,
    schema_dir: Path = SCHEMA_DIR,
) -> SemanticValidationResult:
    collector = ErrorCollector()
    _validate_schema(
        artifact, "attribute_classification_fixture.schema.json", collector, schema_dir
    )
    case_type = artifact.get("case_type")
    fixture_id = artifact.get("fixture_id")
    pattern = FIXTURE_ID_PATTERNS.get(case_type)
    if pattern is not None and (
        not isinstance(fixture_id, str) or pattern.fullmatch(fixture_id) is None
    ):
        collector.add(
            "ACV017",
            "/fixture_id",
            "fixture_id does not match case_type",
            expected=pattern.pattern,
            actual=fixture_id,
        )
    expected = artifact.get("expected")
    if isinstance(expected, Mapping):
        records = expected.get("records")
        if isinstance(records, list):
            for index, record in enumerate(records):
                if not isinstance(record, Mapping):
                    continue
                classification = record.get("classification")
                if isinstance(classification, Mapping):
                    selected = classification.get("selected_rule_id")
                    matched = classification.get("matched_rule_ids")
                    if isinstance(matched, list) and selected not in matched:
                        collector.add(
                            "ACV017",
                            f"/expected/records/{index}/classification/selected_rule_id",
                            "fixture selected_rule_id is not in matched_rule_ids",
                            actual=selected,
                        )
                    record_id = record.get("classification_record_id")
                    is_lanes = isinstance(record_id, str) and ":lanes:" in record_id
                    expected_level_prefix = "L" if is_lanes else "S"
                    expected_rule_prefix = "LANE-" if is_lanes else "SPEED-"
                    level = classification.get("criticality_level")
                    rules = [
                        classification.get("selected_rule_id"),
                        *(classification.get("matched_rule_ids") or []),
                    ]
                    if not isinstance(level, str) or not level.startswith(
                        expected_level_prefix
                    ):
                        collector.add(
                            "ACV017",
                            f"/expected/records/{index}/classification/criticality_level",
                            "fixture criticality family does not match record attribute",
                            expected=expected_level_prefix,
                            actual=level,
                        )
                    if any(
                        not isinstance(rule, str)
                        or not rule.startswith(expected_rule_prefix)
                        for rule in rules
                    ):
                        collector.add(
                            "ACV017",
                            f"/expected/records/{index}/classification",
                            "fixture rule family does not match record attribute",
                            expected=expected_rule_prefix,
                            actual=rules,
                        )
                resolution = record.get("resolution")
                if isinstance(resolution, Mapping):
                    _validate_resolution_state(
                        resolution,
                        f"/expected/records/{index}/resolution",
                        collector,
                        "ACV018",
                    )
                    level = (
                        classification.get("criticality_level")
                        if isinstance(classification, Mapping)
                        else None
                    )
                    _validate_evidence_requirement(
                        level,
                        resolution,
                        f"/expected/records/{index}/resolution",
                        collector,
                        "ACV018",
                    )
        outcome = expected.get("outcome")
        failure_codes = expected.get("failure_codes")
        if outcome == "success" and (
            not isinstance(failure_codes, list) or failure_codes
        ):
            collector.add(
                "ACV018",
                "/expected/failure_codes",
                "successful fixture must have no failure codes",
                expected=[],
                actual=failure_codes,
            )
        if outcome == "governed_stop" and (
            not isinstance(failure_codes, list) or not failure_codes
        ):
            collector.add(
                "ACV018",
                "/expected/failure_codes",
                "governed-stop fixture requires at least one failure code",
                actual=failure_codes,
            )
        _validate_fixture_assertions(artifact, expected, collector)
    oracle = artifact.get("oracle")
    if isinstance(oracle, Mapping):
        _validate_file_ref(oracle, "/oracle", collector, artifact_root)
        if specification_path.is_file():
            actual_spec_hash = file_sha256(specification_path)
            if oracle.get("source_specification_sha256") != actual_spec_hash:
                collector.add(
                    "ACV020",
                    "/oracle/source_specification_sha256",
                    "oracle source specification SHA-256 does not match",
                    expected=oracle.get("source_specification_sha256"),
                    actual=actual_spec_hash,
                )
        else:
            collector.add(
                "ACV020",
                "/oracle/source_specification_sha256",
                "oracle source specification file does not exist",
                actual=str(specification_path),
            )
    _validate_repeat(artifact, collector, baseline_output, repeated_output)
    return collector.result()


def validate_fixture_review_artifact(
    review: Mapping[str, Any],
    oracles: Mapping[str, Any],
    *,
    artifact_root: Path = REPOSITORY_ROOT,
    specification_path: Path = SPECIFICATION_PATH,
) -> SemanticValidationResult:
    collector = ErrorCollector()
    checks = review.get("required_review_checks")
    check_values = checks if isinstance(checks, list) else []
    all_passed = bool(check_values) and all(
        isinstance(check, Mapping)
        and check.get("status") in {"passed", "not_applicable"}
        for check in check_values
    )
    findings = review.get("findings")
    finding_values = findings if isinstance(findings, list) else []
    no_blocking_findings = not any(
        isinstance(finding, Mapping)
        and finding.get("blocking") is True
        and finding.get("status") != "resolved"
        for finding in finding_values
    )
    expected_acceptance = (
        review.get("collection_status") == "independently_accepted"
        and all_passed
        and no_blocking_findings
    )
    if review.get("acceptance_allowed") is not expected_acceptance:
        collector.add(
            "ACV021",
            "/acceptance_allowed",
            "acceptance must be derived from status, checks and blocking findings",
            expected=expected_acceptance,
            actual=review.get("acceptance_allowed"),
        )

    basis = review.get("authoring_basis")
    if isinstance(basis, Mapping) and specification_path.is_file():
        specification_hash = file_sha256(specification_path)
        if basis.get("sha256") != specification_hash:
            collector.add(
                "ACV021",
                "/authoring_basis/sha256",
                "reviewed specification SHA-256 does not match",
                expected=specification_hash,
                actual=basis.get("sha256"),
            )
        if oracles.get("source_specification_sha256") != basis.get("sha256"):
            collector.add(
                "ACV021",
                "/authoring_basis/sha256",
                "review and oracle specification hashes differ",
                expected=oracles.get("source_specification_sha256"),
                actual=basis.get("sha256"),
            )

    observations = review.get("hash_observations")
    if isinstance(observations, list):
        for index, observation in enumerate(observations):
            if not isinstance(observation, Mapping):
                continue
            pointer = f"/hash_observations/{index}"
            relative_path = observation.get("artifact_path")
            path = (
                _resolve_relative_path(artifact_root, relative_path)
                if isinstance(relative_path, str)
                else None
            )
            actual_hash = file_sha256(path) if path is not None and path.is_file() else None
            matched = (
                actual_hash is not None
                and observation.get("expected_hash") == actual_hash
                and observation.get("observed_hash") == actual_hash
            )
            if observation.get("matched") is not matched:
                collector.add(
                    "ACV021",
                    f"{pointer}/matched",
                    "stored hash observation does not match current bytes",
                    expected=matched,
                    actual=observation.get("matched"),
                )
    return collector.result()


def validate_artifact(
    artifact: Mapping[str, Any],
    **kwargs: Any,
) -> SemanticValidationResult:
    artifact_type = artifact.get("artifact_type")
    if artifact_type == "attribute_classification_predicates":
        return validate_predicate_artifact(artifact, **kwargs)
    if artifact_type == "attribute_classification":
        return validate_classification_artifact(artifact, **kwargs)
    if artifact_type == "attribute_classification_fixture":
        return validate_fixture_artifact(artifact, **kwargs)
    collector = ErrorCollector()
    collector.add(
        "ACV000",
        "/artifact_type",
        "unsupported attribute-classification artifact type",
        actual=artifact_type,
    )
    return collector.result()


def _parse_source(value: str) -> tuple[str, Path]:
    sha256, separator, path = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("source must have SHA256=PATH form")
    return sha256, Path(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate attribute-classification artifact semantics."
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--artifact-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--source", action="append", type=_parse_source, default=[])
    parser.add_argument("--history", action="append", type=Path, default=[])
    parser.add_argument("--baseline-output", type=Path)
    parser.add_argument("--repeated-output", type=Path)
    parser.add_argument("--specification", type=Path, default=SPECIFICATION_PATH)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    source_index = dict(args.source)
    artifact_type = artifact.get("artifact_type")
    if artifact_type == "attribute_classification":
        history = [
            json.loads(path.read_text(encoding="utf-8")) for path in args.history
        ]
        result = validate_classification_artifact(
            artifact,
            artifact_root=args.artifact_root,
            source_index=source_index,
            history_artifacts=history,
        )
    elif artifact_type == "attribute_classification_predicates":
        result = validate_predicate_artifact(
            artifact,
            artifact_root=args.artifact_root,
            source_index=source_index,
        )
    elif artifact_type == "attribute_classification_fixture":
        result = validate_fixture_artifact(
            artifact,
            artifact_root=args.artifact_root,
            specification_path=args.specification,
            baseline_output=args.baseline_output,
            repeated_output=args.repeated_output,
        )
    else:
        result = validate_artifact(artifact)
    payload = json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
