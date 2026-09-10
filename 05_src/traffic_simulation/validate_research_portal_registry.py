"""Validate the manually governed Research Portal Registry v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable

import jsonschema
import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


REGISTRY_PATH: Final = (
    REPOSITORY_ROOT / "reproducibility/config/research_portal/registry.yml"
)
SCHEMA_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility/config/research_portal/research_portal_registry.schema.json"
)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Semantic validation result returned to callers and the CLI."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    counts: dict[str, int]

    @property
    def valid(self) -> bool:
        return not self.errors


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects silently overwritten mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML mapping key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"registry must be a mapping: {path}")
    return value


def _load_schema(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"schema must be a JSON object: {path}")
    jsonschema.Draft202012Validator.check_schema(value)
    return value


def _schema_errors(registry: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = []
    for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.path)):
        location = "/" + "/".join(str(part) for part in error.absolute_path)
        errors.append(f"schema {location}: {error.message}")
    return errors


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicated: set[str] = set()
    for value in values:
        if value in seen:
            duplicated.add(value)
        seen.add(value)
    return duplicated


def _is_git_tracked(repository_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative_path],
        cwd=repository_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in adjacency.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)


def validate_registry(
    registry_path: Path = REGISTRY_PATH,
    schema_path: Path = SCHEMA_PATH,
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> ValidationReport:
    """Validate schema, references, evidence rules, graph rules and portability."""

    registry = _load_yaml(registry_path)
    schema = _load_schema(schema_path)
    errors = _schema_errors(registry, schema)
    warnings: list[str] = []
    if errors:
        return ValidationReport(tuple(errors), (), {})

    nodes = registry["nodes"]
    relations = registry["relations"]
    evidence = registry["evidence"]
    views = registry["views"]
    conflicts = registry["known_conflicts"]
    groups = registry["groups"]
    node_by_id = {item["id"]: item for item in nodes}
    relation_by_id = {item["id"]: item for item in relations}
    evidence_by_id = {item["id"]: item for item in evidence}
    view_by_id = {item["id"]: item for item in views}
    conflict_by_id = {item["id"]: item for item in conflicts}
    group_by_id = {item["id"]: item for item in groups}

    for label, items in (
        ("node", nodes),
        ("relation", relations),
        ("evidence", evidence),
        ("view", views),
        ("conflict", conflicts),
        ("group", groups),
    ):
        for duplicate in sorted(_duplicates(item["id"] for item in items)):
            errors.append(f"duplicate {label} id: {duplicate}")

    if registry["default_view_id"] not in view_by_id:
        errors.append(f"missing default view: {registry['default_view_id']}")
    current_stage = node_by_id.get(registry["current_stage_ref"])
    if current_stage is None:
        errors.append(f"missing current stage: {registry['current_stage_ref']}")
    elif current_stage["kind"] != "stage":
        errors.append("current_stage_ref must reference exactly one stage node")

    for node in nodes:
        for evidence_ref in node["evidence_refs"]:
            if evidence_ref not in evidence_by_id:
                errors.append(f"node {node['id']} has missing evidence ref: {evidence_ref}")
        parent_ref = node.get("parent_node_ref")
        if parent_ref is not None and parent_ref not in node_by_id:
            errors.append(f"node {node['id']} has missing parent node ref: {parent_ref}")
        for group_ref in node.get("group_refs", []):
            if group_ref not in group_by_id:
                errors.append(f"node {node['id']} has missing group ref: {group_ref}")
        for scope_ref in node.get("scope_refs", []):
            if scope_ref not in node_by_id:
                errors.append(f"node {node['id']} has missing scope ref: {scope_ref}")
        if node.get("intentionally_isolated") and not node.get("isolation_reason_ja"):
            errors.append(f"intentional isolation requires a reason: {node['id']}")

    relation_pairs: set[tuple[str, str, str]] = set()
    for relation in relations:
        relation_id = relation["id"]
        source = relation["source"]
        target = relation["target"]
        if source not in node_by_id:
            errors.append(f"relation {relation_id} has missing source: {source}")
        if target not in node_by_id:
            errors.append(f"relation {relation_id} has missing target: {target}")
        for evidence_ref in relation["evidence_refs"]:
            if evidence_ref not in evidence_by_id:
                errors.append(
                    f"relation {relation_id} has missing evidence ref: {evidence_ref}"
                )
        relation_roles = {
            evidence_by_id[ref]["role"]
            for ref in relation["evidence_refs"]
            if ref in evidence_by_id
        }
        if relation["status"] == "planned" and "design_intent" not in relation_roles:
            errors.append(f"planned relation requires design_intent evidence: {relation_id}")
        pair = (source, target, relation["type"])
        if pair in relation_pairs:
            errors.append(f"duplicate relation endpoints/type: {pair}")
        relation_pairs.add(pair)

        if relation["type"] == "blocked_by":
            source_node = node_by_id.get(source)
            target_node = node_by_id.get(target)
            if source_node and source_node["kind"] != "issue":
                errors.append(f"blocked_by source must be issue node: {relation_id}")
            if target_node and target_node["status"] != "blocked":
                errors.append(f"blocked_by target must have blocked status: {relation_id}")
            if relation["status"] != "blocked":
                errors.append(f"blocked_by relation must have blocked status: {relation_id}")

        if relation["type"] == "compares_with":
            reverse = (target, source, "compares_with")
            if reverse in relation_pairs:
                errors.append(
                    f"compares_with must be stored once as a symmetric relation: {relation_id}"
                )
            instance = node_by_id.get(relation["common_instance_ref"])
            if instance is None or instance["kind"] != "experiment_instance":
                errors.append(
                    f"compares_with common_instance_ref must reference an experiment_instance: {relation_id}"
                )

        if relation["type"] in {"hypothesizes_influence_on", "projects_to"}:
            if relation["nature"] not in {"hypothesis", "external_model"}:
                errors.append(
                    f"future projection relation requires hypothesis/external_model nature: {relation_id}"
                )

    for node in nodes:
        if node["status"] == "blocked":
            incoming = [
                relation
                for relation in relations
                if relation["type"] == "blocked_by" and relation["target"] == node["id"]
            ]
            if not incoming:
                errors.append(f"blocked node has no incoming blocked_by relation: {node['id']}")

        roles = {
            evidence_by_id[ref]["role"]
            for ref in node["evidence_refs"]
            if ref in evidence_by_id
        }
        if node["status"] == "implemented":
            if node["kind"] in {"model", "method", "simulation", "analysis"}:
                if not {"implementation", "test"}.issubset(roles):
                    errors.append(
                        f"implemented {node['kind']} requires implementation and test evidence: {node['id']}"
                    )
            elif node["kind"] in {"dataset", "dataset_group"}:
                if not roles.intersection({"input_registry", "observation", "data_artifact", "acceptance_decision"}):
                    errors.append(
                        f"implemented {node['kind']} requires registry/observation/acceptance evidence: {node['id']}"
                    )
        if node["status"] == "planned" and "design_intent" not in roles:
            errors.append(f"planned node requires design_intent evidence: {node['id']}")
        if node["readiness"] == "accepted":
            effective_review = node.get("review", registry["review"])
            if "acceptance_decision" not in roles:
                errors.append(f"accepted node requires acceptance_decision evidence: {node['id']}")
            if effective_review["reviewed_by"] is None or effective_review["reviewed_at"] is None:
                errors.append(f"accepted node requires a completed review: {node['id']}")
        if node["kind"] == "issue" and "resolution_status" not in node:
            errors.append(f"issue requires resolution_status: {node['id']}")
        if "aer" in node["tags"]:
            if node.get("execution_modality") != "classical_quantum_circuit_simulator":
                errors.append(f"Aer node must declare classical simulator modality: {node['id']}")
            if node.get("hardware_execution") is not False:
                errors.append(f"Aer node must declare hardware_execution false: {node['id']}")
            if node.get("quantum_advantage_claimed") is not False:
                errors.append(f"Aer node must declare quantum_advantage_claimed false: {node['id']}")

        definition = node.get("metric_definition")
        if definition is not None:
            if not definition.get("unit"):
                errors.append(f"numeric metric requires unit: {node['id']}")
            if not definition.get("scope"):
                errors.append(f"numeric metric requires scope: {node['id']}")
            if not node["evidence_refs"]:
                errors.append(f"numeric metric requires evidence: {node['id']}")

    scale_by_id: dict[str, dict[str, Any]] = {}
    scale_edges: list[tuple[str, str]] = []
    for node in nodes:
        for scale in node.get("problem_scale", []):
            scale_id = scale["id"]
            if scale_id in scale_by_id:
                errors.append(f"duplicate problem scale id: {scale_id}")
            scale_by_id[scale_id] = scale
            if scale["owner_node_ref"] != node["id"]:
                errors.append(f"problem scale owner mismatch: {scale_id}")
            evidence_ref = scale["evidence_ref"]
            if evidence_ref is not None and evidence_ref not in evidence_by_id:
                errors.append(f"problem scale has missing evidence ref: {scale_id}: {evidence_ref}")
            if scale["value"] is None:
                if not scale.get("unknown_reason"):
                    errors.append(f"unknown problem scale requires unknown_reason: {scale_id}")
            else:
                if evidence_ref is None:
                    errors.append(f"valued problem scale requires evidence: {scale_id}")
                if not scale["unit"] or not scale["derivation_method"]:
                    errors.append(f"valued problem scale requires unit and derivation_method: {scale_id}")
            for source_ref in scale.get("derived_from_scale_refs", []):
                scale_edges.append((source_ref, scale_id))
    for source, target in scale_edges:
        if source not in scale_by_id:
            errors.append(f"problem scale {target} derives from missing scale: {source}")
    if _has_cycle(scale_edges):
        errors.append("problem scale derivation graph contains a cycle")

    for evidence_item in evidence:
        evidence_id = evidence_item["id"]
        if evidence_item["role"] in {
            "data_artifact",
            "run_artifact",
            "validation_result",
            "acceptance_decision",
        } and not evidence_item.get("generated_from_evidence_refs"):
            errors.append(f"generated evidence requires provenance refs: {evidence_id}")
        relative_path = evidence_item["path"]
        raw_path = Path(relative_path)
        if raw_path.is_absolute() or ".." in raw_path.parts:
            errors.append(f"unsafe evidence path: {evidence_id}: {relative_path}")
            continue
        unresolved = repository_root / raw_path
        resolved = unresolved.resolve()
        try:
            resolved.relative_to(repository_root.resolve())
        except ValueError:
            if unresolved.is_symlink() or any(part.is_symlink() for part in unresolved.parents if part != repository_root.parent):
                errors.append(f"symlink evidence path escapes repository: {evidence_id}: {relative_path}")
            else:
                errors.append(f"evidence path escapes repository: {evidence_id}: {relative_path}")
            continue
        if not resolved.exists():
            errors.append(f"missing evidence path: {evidence_id}: {relative_path}")
        elif not resolved.is_file():
            errors.append(f"evidence path is not a file: {evidence_id}: {relative_path}")
        elif not _is_git_tracked(repository_root, relative_path):
            warnings.append(
                f"untracked evidence is not deployment-portable: {evidence_id}: {relative_path}"
            )
        expected_sha = evidence_item.get("sha256")
        if expected_sha is not None and resolved.is_file():
            actual_sha = hashlib.sha256(resolved.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                errors.append(f"evidence sha256 mismatch: {evidence_id}")

        for support in evidence_item["supports"]:
            target_id = support["target_id"]
            expected = node_by_id if support["target_type"] == "node" else relation_by_id
            if target_id not in expected:
                errors.append(
                    f"evidence {evidence_id} supports missing {support['target_type']}: {target_id}"
                )
            elif evidence_id not in expected[target_id]["evidence_refs"]:
                errors.append(
                    f"evidence support is not reciprocated by {target_id}: {evidence_id}"
                )
        for source_ref in evidence_item.get("generated_from_evidence_refs", []):
            if source_ref not in evidence_by_id:
                errors.append(f"evidence {evidence_id} generated from missing evidence: {source_ref}")
        superseded_by = evidence_item.get("superseded_by")
        if superseded_by is not None and superseded_by not in evidence_by_id:
            errors.append(f"evidence {evidence_id} superseded by missing evidence: {superseded_by}")

    for target_type, items in (("node", nodes), ("relation", relations)):
        for item in items:
            for evidence_ref in item["evidence_refs"]:
                if evidence_ref not in evidence_by_id:
                    continue
                support = {"target_type": target_type, "target_id": item["id"]}
                if support not in evidence_by_id[evidence_ref]["supports"]:
                    errors.append(
                        f"{target_type} evidence ref is not reciprocated by evidence supports: {item['id']}: {evidence_ref}"
                    )

    generated_edges = [
        (item["id"], source_ref)
        for item in evidence
        for source_ref in item.get("generated_from_evidence_refs", [])
    ]
    superseded_evidence_edges = [
        (item["id"], item["superseded_by"])
        for item in evidence
        if item.get("superseded_by") is not None
    ]
    if _has_cycle(generated_edges):
        errors.append("generated evidence provenance graph contains a cycle")
    if _has_cycle(superseded_evidence_edges):
        errors.append("evidence superseded graph contains a cycle")

    for view in views:
        for node_ref in view["node_refs"]:
            if node_ref not in node_by_id:
                errors.append(f"view {view['id']} has missing node ref: {node_ref}")
        for relation_ref in view["relation_refs"]:
            if relation_ref not in relation_by_id:
                errors.append(f"view {view['id']} has missing relation ref: {relation_ref}")
        for conflict_ref in view.get("conflict_refs", []):
            if conflict_ref not in conflict_by_id:
                errors.append(f"view {view['id']} has missing conflict ref: {conflict_ref}")
        for group_ref in view["group_refs"]:
            if group_ref not in group_by_id:
                errors.append(f"view {view['id']} has missing group ref: {group_ref}")
        for rank in view["fixed_ranks"]:
            for node_ref in rank["node_refs"]:
                if node_ref not in view["node_refs"]:
                    errors.append(f"view {view['id']} rank references node outside view: {node_ref}")

    for group in groups:
        for node_ref in group["node_refs"]:
            if node_ref not in node_by_id:
                errors.append(f"group {group['id']} has missing node ref: {node_ref}")

    for conflict in conflicts:
        for evidence_ref in conflict["evidence_refs"]:
            if evidence_ref not in evidence_by_id:
                errors.append(
                    f"conflict {conflict['id']} has missing evidence ref: {evidence_ref}"
                )
        if conflict["resolution_status"] == "unresolved":
            warnings.append(f"unresolved known conflict: {conflict['id']}")

    dependency_edges = [
        (relation["source"], relation["target"])
        for relation in relations
        if relation["type"] in {"depends_on", "blocked_by"}
    ]
    if _has_cycle(dependency_edges):
        errors.append("depends_on/blocked_by graph contains a cycle")
    supersedes_edges = [
        (relation["source"], relation["target"])
        for relation in relations
        if relation["type"] == "supersedes"
    ]
    if _has_cycle(supersedes_edges):
        errors.append("supersedes graph contains a cycle")

    connected = {
        endpoint
        for relation in relations
        for endpoint in (relation["source"], relation["target"])
    }
    connected.add(registry["current_stage_ref"])
    connected.update(
        ref
        for node in nodes
        for ref in ([node.get("parent_node_ref")] if node.get("parent_node_ref") else [])
    )
    connected.update(node["id"] for node in nodes if node.get("parent_node_ref"))
    included_in_views = {node_ref for view in views for node_ref in view["node_refs"]}
    for node in nodes:
        if node["id"] not in included_in_views:
            warnings.append(f"node is not included in any view: {node['id']}")
        if node["id"] not in connected and not node.get("intentionally_isolated", False):
            warnings.append(f"isolated node: {node['id']}")

    counts = {
        "nodes": len(nodes),
        "relations": len(relations),
        "evidence": len(evidence),
        "issues": sum(node["kind"] == "issue" for node in nodes),
        "stages": sum(node["kind"] == "stage" for node in nodes),
        "metrics": sum(node["kind"] == "metric" for node in nodes),
        "remaining_unknowns": sum(len(node.get("unknowns", [])) for node in nodes),
        "remaining_conflicts": sum(
            conflict["resolution_status"] == "unresolved" for conflict in conflicts
        ),
        "warnings": len(warnings),
    }
    return ValidationReport(tuple(errors), tuple(warnings), counts)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = validate_registry(args.registry, args.schema)
    except (OSError, ValueError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        report = ValidationReport((str(exc),), (), {})

    if args.json:
        print(
            json.dumps(
                {
                    "valid": report.valid,
                    "errors": report.errors,
                    "warnings": report.warnings,
                    "counts": report.counts,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for error in report.errors:
            print(f"ERROR: {error}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        if report.valid:
            counts = " ".join(f"{key}={value}" for key, value in report.counts.items())
            print(f"VALID: {counts}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
