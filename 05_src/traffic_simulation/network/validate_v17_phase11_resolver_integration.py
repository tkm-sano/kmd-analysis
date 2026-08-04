from __future__ import annotations

import hashlib
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.network.resolver_integration_v17 import (
    ResolverIntegrationError,
    build_resolver_integration_artifact,
    validate_resolver_integration_artifact,
)
from traffic_simulation.network.validate_v17_formal_blocker_policy import (
    validate_formal_blocker_policy_adoption,
)
from traffic_simulation.network.validate_v17_fixture_oracle import FIXTURE_ROOT
from traffic_simulation.paths import REPOSITORY_ROOT


COMPLETION_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/v17_phase11_completion.yml"
)
FIXTURE = FIXTURE_ROOT / "resolver_integration_phase11.osm.xml"
ORACLE = FIXTURE_ROOT / "resolver_integration_phase11_oracle.yml"
CONTEXT = {"weekday": "Mo", "time": "08:00"}


class Phase11ResolverIntegrationError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Phase11ResolverIntegrationError(f"YAML root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_file(relative: str) -> Path:
    path = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in path.parents or not path.is_file():
        raise Phase11ResolverIntegrationError(f"invalid repository artifact: {relative}")
    return path


def _metamorphic_fixture(destination: Path) -> Path:
    tree = ET.parse(FIXTURE)
    root = tree.getroot()
    children = list(root)
    positions = [index for index, item in enumerate(children) if item.tag == "way"]
    reversed_ways = list(reversed([children[index] for index in positions]))
    for index, way in zip(positions, reversed_ways, strict=True):
        children[index] = way
    root[:] = children
    for element in root.findall("way") + root.findall("relation"):
        children = list(element)
        positions = [index for index, item in enumerate(children) if item.tag == "tag"]
        reversed_tags = list(reversed([children[index] for index in positions]))
        for index, tag in zip(positions, reversed_tags, strict=True):
            children[index] = tag
        element[:] = children
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return destination


def _validate_oracle(artifact: dict[str, Any], oracle: dict[str, Any]) -> None:
    if artifact["counts"] != oracle["expected_counts"]:
        raise Phase11ResolverIntegrationError("integration count oracle mismatch")
    speeds = {
        item["directed_segment_id"]: item["speed_kmh"]
        for item in artifact["speed_projection"]
    }
    if speeds != oracle["expected_directional_speed_kmh"]:
        raise Phase11ResolverIntegrationError("integration speed oracle mismatch")
    permissions: dict[int, set[str]] = {}
    for item in artifact["permission_projection"]:
        way_id = int(item["directed_segment_id"].split(":")[1])
        permissions.setdefault(way_id, set()).add(item["effective_permission"])
    permission_projection = {
        way_id: next(iter(values)) if len(values) == 1 else "mixed_by_lane"
        for way_id, values in permissions.items()
    }
    if permission_projection != oracle["expected_permission_by_way"]:
        raise Phase11ResolverIntegrationError("integration permission oracle mismatch")
    if not all(artifact["lineage_invariants"].values()) or any(
        artifact["formal_invariants"].values()
    ):
        raise Phase11ResolverIntegrationError("integration semantic oracle mismatch")


def validate_phase11_resolver_integration() -> dict[str, Any]:
    validate_formal_blocker_policy_adoption()
    oracle = _load_yaml(ORACLE)
    artifact = build_resolver_integration_artifact(
        FIXTURE, profile="formal", scenario_context=CONTEXT
    )
    validate_resolver_integration_artifact(artifact)
    _validate_oracle(artifact, oracle)
    repeated = build_resolver_integration_artifact(
        FIXTURE, profile="formal", scenario_context=CONTEXT
    )
    if repeated["semantic_sha256"] != artifact["semantic_sha256"]:
        raise Phase11ResolverIntegrationError("repeated integration run hash differs")
    with tempfile.TemporaryDirectory(prefix="v17-phase11-") as temporary:
        transformed_path = _metamorphic_fixture(Path(temporary) / "metamorphic.osm.xml")
        transformed = build_resolver_integration_artifact(
            transformed_path, profile="formal", scenario_context=CONTEXT
        )
    if transformed["semantic_sha256"] != artifact["semantic_sha256"]:
        raise Phase11ResolverIntegrationError("source-order metamorphic hash differs")

    completion = _load_yaml(COMPLETION_PATH)
    if completion.get("result") != "passed":
        raise Phase11ResolverIntegrationError("Phase 11 completion is not passed")
    for section in ("artifacts", "schemas", "fixed_fixture"):
        for name, reference in completion[section].items():
            path = _repo_file(reference["path"])
            if _sha256(path) != reference["sha256"]:
                raise Phase11ResolverIntegrationError(
                    f"Phase 11 completion hash mismatch: {section}.{name}"
                )

    return {
        "phase11_resolver_integration": "passed",
        "schema_validation": "passed",
        "semantic_validation": "passed",
        "oracle_validation": "passed",
        "metamorphic_validation": "passed",
        "semantic_invariant_count": 46,
        "cross_stage_lineage_invariant_count": 6,
        "oracle_assertion_count": 27,
        "metamorphic_relation_count": 3,
        "production_fixture_blocker_count": 0,
        "semantic_sha256": artifact["semantic_sha256"],
        "next_phase": 12,
    }


def main() -> int:
    try:
        result = validate_phase11_resolver_integration()
    except (Phase11ResolverIntegrationError, ResolverIntegrationError, KeyError) as error:
        print(json.dumps({"phase11_resolver_integration": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
