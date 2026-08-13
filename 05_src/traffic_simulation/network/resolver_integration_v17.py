"""Integrate the v17 Resolver stages and enforce their cross-stage contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema

from traffic_simulation.network.conditional_access_v17 import (
    build_conditional_access_production_artifact,
)
from traffic_simulation.network.directed_segments_v17 import (
    build_production_artifact as build_directed_segment_artifact,
)
from traffic_simulation.network.directional_lanes_v17 import (
    build_lane_production_artifact,
)
from traffic_simulation.network.evidence_resolution_v17 import audit_production_origins
from traffic_simulation.network.final_permission_v17 import (
    build_final_permission_production_artifact,
)
from traffic_simulation.network.speed_resolution_v17 import (
    build_speed_production_artifact,
)
from traffic_simulation.network.static_access_v17 import (
    build_static_access_production_artifact,
)
from traffic_simulation.paths import REPOSITORY_ROOT


SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/schemas/resolver_integration_v17.schema.json"
)


class ResolverIntegrationError(ValueError):
    pass


def _canonical_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _load_schema() -> dict[str, Any]:
    value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ResolverIntegrationError("resolver integration Schema is not an object")
    return value


def validate_resolver_integration_artifact(artifact: Mapping[str, Any]) -> None:
    schema = _load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(artifact)
    payload = {key: copy.deepcopy(value) for key, value in artifact.items() if key != "semantic_sha256"}
    if artifact["semantic_sha256"] != _canonical_hash(payload):
        raise ResolverIntegrationError("resolver integration semantic hash differs")
    if artifact["counts"]["blockers"] != len(artifact["blockers"]):
        raise ResolverIntegrationError("resolver integration blocker count differs")


def build_resolver_integration_artifact(
    input_path: Path,
    *,
    profile: str,
    scenario_context: Mapping[str, Any],
) -> dict[str, Any]:
    directed = build_directed_segment_artifact(input_path)
    lanes = build_lane_production_artifact(input_path, profile=profile)
    static = build_static_access_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )
    conditional = build_conditional_access_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )
    permissions = build_final_permission_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )
    speeds = build_speed_production_artifact(
        input_path, profile=profile, scenario_context=scenario_context
    )

    directed_ids = {item["directed_segment_id"] for item in directed["directed_segments"]}
    lane_segment_ids = {item["directed_segment_id"] for item in lanes["segment_lanes"]}
    permission_segment_ids = {
        item["directed_segment_id"] for item in permissions["permission_records"]
    }
    speed_segment_ids = {item["directed_segment_id"] for item in speeds["speed_records"]}
    permission_tuple_ids = {
        (
            item["directed_segment_id"],
            int(item["lane_position"]),
            item["vehicle_class"],
        )
        for item in permissions["permission_records"]
    }
    expected_permission_tuples = {
        (segment["directed_segment_id"], int(lane["lane_position"]), "delivery")
        for segment in lanes["segment_lanes"]
        for lane in segment["lanes"]
    }
    stage_hash_chain_valid = (
        lanes["directed_segment_semantic_sha256"] == directed["semantic_sha256"]
        and static["directional_lane_semantic_sha256"] == lanes["semantic_sha256"]
        and conditional["static_access_semantic_sha256"] == static["semantic_sha256"]
        and permissions["conditional_access_semantic_sha256"]
        == conditional["semantic_sha256"]
    )
    lineage = {
        "lane_segments_equal_directed_segments": lane_segment_ids == directed_ids,
        "permission_segments_equal_lane_segments": permission_segment_ids == lane_segment_ids,
        "speed_segments_equal_directed_segments": speed_segment_ids == directed_ids,
        "one_permission_per_governed_lane_tuple": permission_tuple_ids
        == expected_permission_tuples,
        "one_speed_per_directed_segment": len(speeds["speed_records"])
        == len(speed_segment_ids)
        == len(directed_ids),
        "stage_hash_chain_valid": stage_hash_chain_valid,
    }
    if not all(lineage.values()):
        raise ResolverIntegrationError(f"cross-stage lineage invariant failed: {lineage}")

    origin_audit = audit_production_origins(
        {
            "directional_lanes": lanes["resolutions"],
            "final_permissions": permissions["permission_records"],
            "speed": speeds["speed_records"],
        }
    )
    formal_records = (
        list(lanes["resolutions"])
        + list(permissions["permission_records"])
        + list(speeds["speed_records"])
    )
    formal_invariants = {
        "model_assumed_count": sum(
            item.get("value_origin") == "model_assumed" for item in formal_records
        ),
        "assumption_id_count": sum(
            len(item.get("assumption_ids", [])) for item in formal_records
        ),
        "unapproved_evidence_origin_count": origin_audit[
            "unapproved_evidence_emission_count"
        ],
    }
    if profile == "formal" and any(formal_invariants.values()):
        raise ResolverIntegrationError(
            f"formal integration invariant failed: {formal_invariants}"
        )

    blockers = (
        list(directed["blockers"])
        + list(lanes["blockers"])
        + list(static["blockers"])
        + list(conditional["blockers"])
        + list(permissions["blockers"])
        + list(speeds["blockers"])
    )
    artifact = {
        "schema_version": 17,
        "artifact_type": "resolver_integration_collection",
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": directed["population_version"],
        "profile": profile,
        "scenario_context": copy.deepcopy(dict(scenario_context)),
        "stage_semantic_sha256": {
            "directed_segments": directed["semantic_sha256"],
            "directional_lanes": lanes["semantic_sha256"],
            "static_access": static["semantic_sha256"],
            "conditional_access": conditional["semantic_sha256"],
            "final_permission": permissions["semantic_sha256"],
            "speed": speeds["semantic_sha256"],
        },
        "counts": {
            "source_ways": directed["counts"]["source_ways"],
            "directed_segments": directed["counts"]["directed_segments"],
            "directional_lane_records": lanes["counts"]["resolved_source_ways"],
            "directional_lanes": lanes["counts"]["directional_lanes"],
            "static_rule_groups": static["counts"]["normalized_source_ways"],
            "conditional_rule_groups": conditional["counts"][
                "normalized_conditional_source_ways"
            ],
            "permission_records": permissions["counts"]["permission_records"],
            "speed_records": speeds["counts"]["speed_records"],
            "blockers": len(blockers),
        },
        "lineage_invariants": lineage,
        "formal_invariants": formal_invariants,
        "lane_projection": sorted(
            (
                {
                    "directed_segment_id": item["directed_segment_id"],
                    "moving_lane_count": item["moving_lane_count"],
                    "lane_positions": [lane["lane_position"] for lane in item["lanes"]],
                }
                for item in lanes["segment_lanes"]
            ),
            key=lambda item: item["directed_segment_id"],
        ),
        "permission_projection": sorted(
            (
                {
                    "permission_record_id": item["permission_record_id"],
                    "directed_segment_id": item["directed_segment_id"],
                    "lane_position": item["lane_position"],
                    "effective_permission": item["effective_permission"],
                }
                for item in permissions["permission_records"]
            ),
            key=lambda item: item["permission_record_id"],
        ),
        "speed_projection": sorted(
            (
                {
                    "directed_segment_id": item["directed_segment_id"],
                    "speed_kmh": item["speed_kmh"],
                }
                for item in speeds["speed_records"]
            ),
            key=lambda item: item["directed_segment_id"],
        ),
        "evidence_origin_audit": origin_audit,
        "blockers": blockers,
    }
    artifact["semantic_sha256"] = _canonical_hash(artifact)
    validate_resolver_integration_artifact(artifact)
    return artifact
