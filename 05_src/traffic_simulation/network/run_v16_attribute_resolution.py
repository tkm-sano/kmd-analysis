from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from traffic_simulation.network.classify_attribute_criticality import (
    classify_predicate_artifact,
    write_artifact as write_classification,
)
from traffic_simulation.network.generate_attribute_classification_predicates import (
    EXTERNAL_PREDICATES,
    file_ref,
    generate_predicate_artifact,
    write_artifact_atomic as write_predicates,
)
from traffic_simulation.network.resolve_attribute_values import (
    resolve_classification_artifact,
    write_artifact_atomic as write_resolution,
)
from traffic_simulation.network.validate_attribute_classification import (
    file_sha256,
    validate_classification_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/sumo_network.yml"
)
V16_OSM = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16.osm.xml"
)
V16_ROLES = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16_element_roles.json"
)
V16_MANIFEST = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "ota_ward_20260716_relation_closure_v16_manifest.json"
)
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/road_network/sumo/common/"
    "attribute_resolution_v16"
)
ORACLE_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "attribute_classification/oracles.json"
)
PINNED_ORACLE_SHA256 = (
    "98b6a007e4828e42570a17d9255bdd029295afddf6307d1a6f3f63f8bc96664a"
)


class V16ResolutionRunError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise V16ResolutionRunError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _highway_way_ids(
    osm_path: Path, governed_highway_values: set[str]
) -> set[str]:
    result: set[str] = set()
    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way":
            way_id = element.attrib.get("id")
            highway = next(
                (
                    tag.attrib.get("v")
                    for tag in element.findall("tag")
                    if tag.attrib.get("k") == "highway"
                ),
                None,
            )
            if way_id and highway in governed_highway_values:
                result.add(way_id)
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return result


def _role_decisions(
    osm_path: Path,
    roles_path: Path,
    governed_highway_values: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    roles = _load_json(roles_path)["ways"]
    final = {str(way_id) for way_id in roles["final_analysis_target"]}
    support = {str(way_id) for way_id in roles["topology_support"]}
    if final & support:
        raise V16ResolutionRunError("v16 final and topology-support roles overlap")
    population = _highway_way_ids(osm_path, governed_highway_values)
    decisions: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for way_id in sorted(population, key=int):
        if way_id in final:
            role = "final"
            reason = None
            locator = f"ways/final_analysis_target/{way_id}"
        elif way_id in support:
            role = "topology_support"
            reason = "Retained by the accepted v16 relation closure."
            locator = f"ways/topology_support/{way_id}"
        else:
            role = "excluded"
            reason = None
            locator = f"ways/excluded/{way_id}"
        counts[role] += 1
        decisions.append(
            {
                "osm_way_id": way_id,
                "subgraph_role": role,
                "topology_support_reason": reason,
                "source_record_locator": locator,
                "derivation_rule_id": "PRED-V16-ROLE-001",
            }
        )
    return decisions, dict(sorted(counts.items()))


def _assert_v16_inputs() -> dict[str, Any]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = _load_json(V16_MANIFEST)
    if config.get("config_id") != "ota_ward_sumo_network_v16":
        raise V16ResolutionRunError("current SUMO policy is not version 16")
    if config.get("config_version") != 16:
        raise V16ResolutionRunError("current SUMO policy version is not 16")
    if manifest.get("status") != "accepted":
        raise V16ResolutionRunError("relation closure v16 is not accepted")
    if manifest.get("config_version") != 16:
        raise V16ResolutionRunError("relation closure manifest is not version 16")
    expected = manifest["outputs"]
    checks = {
        V16_OSM: expected["relation_closed_xml"]["sha256"],
        V16_ROLES: expected["element_roles"]["sha256"],
    }
    for path, expected_hash in checks.items():
        actual_hash = file_sha256(path)
        if actual_hash != expected_hash:
            raise V16ResolutionRunError(
                f"v16 input hash mismatch: {path}; "
                f"expected={expected_hash}; actual={actual_hash}"
            )
    if file_sha256(ORACLE_PATH) != PINNED_ORACLE_SHA256:
        raise V16ResolutionRunError("independent fixture oracle hash changed")
    return manifest


def _blocker_counts(artifact: Mapping[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in artifact["records"]:
        counts.update(record["resolution"]["stop_failure_codes"])
    return dict(sorted(counts.items()))


def execute(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    manifest = _assert_v16_inputs()
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    staging = output_dir
    try:
        external_path = staging / "external-predicate-assignments.json"
        external = {
            "artifact_type": "v16_external_predicate_assignments",
            "schema_version": 1,
            "config_id": "ota_ward_sumo_network_v16",
            "config_version": 16,
            "run_id": "ota-ward-attribute-resolution-v16-20260730-01",
            "relation_closed_osm_sha256": file_sha256(V16_OSM),
            "status": "no_positive_assignments_accepted",
            "interpretation": (
                "Each empty list is an explicit accepted empty positive set; "
                "all population ways are in false_scope."
            ),
            "true_way_ids": {name: [] for name in EXTERNAL_PREDICATES},
        }
        _write_json(external_path, external)

        governed_highway_values = set(
            manifest["road_population"]["candidate_by_highway"]
        )
        decisions, role_counts = _role_decisions(
            V16_OSM,
            V16_ROLES,
            governed_highway_values,
        )
        expected_population = manifest["road_population"]["governed_candidate_ways"]
        if len(decisions) != expected_population:
            raise V16ResolutionRunError(
                f"v16 population differs from accepted manifest: "
                f"expected={expected_population}; actual={len(decisions)}"
            )

        registry_path = staging / "predicate-source-registry.json"
        external_ref = file_ref(external_path)
        registry = {
            "artifact_type": (
                "attribute_classification_predicate_source_registry"
            ),
            "schema_version": 1,
            "config_id": "ota_ward_sumo_network_v16",
            "config_version": 16,
            "run_id": "ota-ward-attribute-resolution-v16-20260730-01",
            "population_acceptance": {
                "scope": "registered_real_data",
                "accepted": True,
                "acceptance_artifact": file_ref(V16_MANIFEST),
            },
            "relation_closed_osm": file_ref(V16_OSM),
            "role_source_artifact_type": "relation_closure_element_roles",
            "role_source": file_ref(V16_ROLES),
            "role_decisions": decisions,
            "external_predicate_sources": {
                name: {
                    "source_artifact_type": (
                        "accepted_empty_external_predicate_assignment"
                    ),
                    "source": external_ref,
                    "derivation_rule_id": f"PRED-V16-EXTERNAL-{index:03d}",
                    "true_way_ids": [],
                    "false_scope": "all_other_population_ways",
                }
                for index, name in enumerate(EXTERNAL_PREDICATES, start=1)
            },
            "predicate_overrides": [],
        }
        _write_json(registry_path, registry)

        predicate_path = staging / "classification-predicates.json"
        predicate_artifact = generate_predicate_artifact(
            osm_path=V16_OSM,
            source_registry_path=registry_path,
            policy_path=CONFIG_PATH,
        )
        write_predicates(predicate_artifact, predicate_path)

        artifacts: dict[str, dict[str, Any]] = {}
        paths: dict[str, Path] = {
            "external_predicate_assignments": external_path,
            "predicate_source_registry": registry_path,
            "classification_predicates": predicate_path,
        }
        for profile in ("structural", "formal"):
            classification_path = staging / f"{profile}-criticality.json"
            classification = classify_predicate_artifact(
                predicate_path,
                profile=profile,
                policy_path=CONFIG_PATH,
                predecessor_path=None,
                revision_reason_code="ACR-INITIAL-V16",
            )
            write_classification(classification, classification_path)
            paths[f"{profile}_criticality"] = classification_path

            resolution_path = staging / f"{profile}-attribute-resolution.json"
            resolved = resolve_classification_artifact(
                classification_path,
                osm_path=V16_OSM,
            )
            validation = validate_classification_artifact(
                resolved, artifact_root=REPOSITORY_ROOT
            )
            if not validation.valid:
                raise V16ResolutionRunError(
                    f"{profile} integrated artifact failed semantic validation: "
                    f"{validation.to_dict()}"
                )
            write_resolution(resolved, resolution_path)
            paths[f"{profile}_attribute_resolution"] = resolution_path
            artifacts[profile] = resolved

        summary = {
            "artifact_type": "v16_attribute_resolution_run_summary",
            "schema_version": 1,
            "config_id": "ota_ward_sumo_network_v16",
            "config_version": 16,
            "run_id": "ota-ward-attribute-resolution-v16-20260730-01",
            "source_population": {
                "manifest": file_ref(V16_MANIFEST),
                "relation_closed_osm": file_ref(V16_OSM),
                "element_roles": file_ref(V16_ROLES),
                "accepted_way_count": expected_population,
                "role_counts": role_counts,
                "v15_records_reused": False,
            },
            "fixture_oracle": {
                "path": ORACLE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
                "sha256": PINNED_ORACLE_SHA256,
                "changed_by_execution": False,
            },
            "profiles": {
                profile: {
                    "record_count": len(artifact["records"]),
                    "complete": artifact["complete"],
                    "blocker_counts": _blocker_counts(artifact),
                    "schema_and_semantic_validation": "passed",
                }
                for profile, artifact in artifacts.items()
            },
            "outputs": {
                name: file_ref(path) for name, path in sorted(paths.items())
            },
        }
        summary_path = staging / "run-summary.json"
        _write_json(summary_path, summary)
        return summary
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run fresh v16 predicate, classification, and resolution stages"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = execute(args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
