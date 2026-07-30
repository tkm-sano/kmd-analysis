from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from traffic_simulation.network.resolve_attribute_values import (
    load_osm_attribute_values,
    resolve_record,
)
from traffic_simulation.network.validate_attribute_classification import file_sha256
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/attribute_classification"
)
INPUTS_PATH = FIXTURE_ROOT / "inputs.json"
ORACLE_PATH = FIXTURE_ROOT / "oracles.json"
PINNED_ORACLE_SHA256 = (
    "98b6a007e4828e42570a17d9255bdd029295afddf6307d1a6f3f63f8bc96664a"
)
SUCCESS_CASES = {
    "AC-BND-001",
    "AC-BND-002",
    "AC-BND-003",
    "AC-BND-004",
    "AC-POS-001",
    "AC-POS-002",
    "AC-POS-003",
    "AC-POS-004",
    "AC-REP-001",
}
FIXTURE_REVIEW = {
    "reviewer": "independent-fixture-author",
    "reviewed_at": "2026-07-25T00:00:00Z",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _record(
    tuple_input: dict[str, Any], oracle_record: dict[str, Any]
) -> dict[str, Any]:
    return {
        "classification_record_id": oracle_record["classification_record_id"],
        "osm_way_id": tuple_input["osm_way_id"],
        "attribute": tuple_input["attribute"],
        "profile": tuple_input["profile"],
        "subgraph_role": tuple_input["subgraph_role"],
        "classification": copy.deepcopy(oracle_record["classification"]),
    }


def _context(case_id: str, tuple_input: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {
        "evidence_candidates": copy.deepcopy(tuple_input["evidence_candidates"])
    }
    if case_id in {"AC-BND-003", "AC-POS-004"}:
        context["review"] = FIXTURE_REVIEW
    return context


@pytest.mark.parametrize("case_id", sorted(SUCCESS_CASES))
def test_fixed_cases_match_independent_resolution_oracle(case_id: str) -> None:
    assert file_sha256(ORACLE_PATH) == PINNED_ORACLE_SHA256
    inputs = _load(INPUTS_PATH)["cases"][case_id]["scenario"]["tuples"]
    expected_records = _load(ORACLE_PATH)["cases"][case_id]["records"]
    expected_by_id = {
        record["classification_record_id"]: record for record in expected_records
    }

    observed: list[dict[str, Any]] = []
    for tuple_input in inputs:
        record_id = (
            f"acr:{tuple_input['osm_way_id']}:{tuple_input['attribute']}:"
            f"{tuple_input['profile']}"
        )
        oracle_record = expected_by_id[record_id]
        classification_record = _record(tuple_input, oracle_record)
        before = copy.deepcopy(classification_record["classification"])
        resolution = resolve_record(
            classification_record,
            osm_attributes=tuple_input["osm_attributes"],
            predicates=tuple_input["predicates"],
            context=_context(case_id, tuple_input),
        )
        assert classification_record["classification"] == before
        assert resolution == oracle_record["resolution"]
        observed.append(
            {
                "classification_record_id": record_id,
                "classification": classification_record["classification"],
                "resolution": resolution,
            }
        )
    assert observed == expected_records


def test_evidence_conflict_stops_without_changing_classification() -> None:
    classification = {
        "classification_record_id": "acr:1006:lanes:formal",
        "osm_way_id": "1006",
        "attribute": "lanes",
        "profile": "formal",
        "subgraph_role": "final",
        "classification": {
            "criticality_level": "L2",
            "selected_rule_id": "LANE-CRIT-006",
            "matched_rule_ids": ["LANE-CRIT-006"],
        },
    }
    candidates = [
        {
            "evidence_id": evidence_id,
            "value": value,
            "applicable": True,
            "rejection_reason_code": None,
        }
        for evidence_id, value in (("candidate-a", 1), ("candidate-b", 2))
    ]
    before = copy.deepcopy(classification)

    resolution = resolve_record(
        classification,
        osm_attributes={},
        predicates={},
        context={"evidence_candidates": candidates},
    )

    assert classification == before
    assert resolution["value_state"] == "conflict"
    assert resolution["resolution_action"] == "stop_unresolved"
    assert resolution["stop_failure_codes"] == ["AC006"]


def test_formal_profile_rejects_requested_structural_placeholder() -> None:
    classification = {
        "classification_record_id": "acr:1008:lanes:formal",
        "osm_way_id": "1008",
        "attribute": "lanes",
        "profile": "formal",
        "subgraph_role": "final",
        "classification": {
            "criticality_level": "L2",
            "selected_rule_id": "LANE-CRIT-006",
            "matched_rule_ids": ["LANE-CRIT-006"],
        },
    }

    resolution = resolve_record(
        classification,
        osm_attributes={},
        predicates={},
        context={"requested_structural_placeholder": True},
    )

    assert resolution["resolution_action"] == "stop_unresolved"
    assert resolution["value_state"] == "invalid"
    assert resolution["stop_failure_codes"] == ["AC008"]


def test_repeat_execution_is_deterministic() -> None:
    inputs = _load(INPUTS_PATH)["cases"]["AC-REP-001"]["scenario"]["tuples"]
    oracle = _load(ORACLE_PATH)["cases"]["AC-REP-001"]["records"]
    expected_by_id = {
        record["classification_record_id"]: record for record in oracle
    }

    def execute() -> bytes:
        output = []
        for tuple_input in inputs:
            record_id = (
                f"acr:{tuple_input['osm_way_id']}:{tuple_input['attribute']}:"
                f"{tuple_input['profile']}"
            )
            classification_record = _record(
                tuple_input, expected_by_id[record_id]
            )
            output.append(
                resolve_record(
                    classification_record,
                    osm_attributes=tuple_input["osm_attributes"],
                    predicates=tuple_input["predicates"],
                    context=_context("AC-REP-001", tuple_input),
                )
            )
        return json.dumps(output, sort_keys=True, separators=(",", ":")).encode()

    assert execute() == execute()


def test_oracle_authorship_and_hash_remain_independent_and_pinned() -> None:
    oracle = _load(ORACLE_PATH)
    assert file_sha256(ORACLE_PATH) == PINNED_ORACLE_SHA256
    assert oracle["authorship"]["production_classifier_existed_at_authorship"] is False
    assert oracle["authorship"]["independent_from_production_code"] is True


def test_streaming_osm_reader_retains_way_tags(tmp_path: Path) -> None:
    osm = tmp_path / "input.osm.xml"
    osm.write_text(
        """<osm version="0.6">
  <node id="1" lat="35" lon="139"/>
  <node id="2" lat="35.1" lon="139.1"/>
  <way id="123">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="highway" v="residential"/>
    <tag k="lanes" v="2"/>
    <tag k="maxspeed" v="40"/>
  </way>
</osm>
""",
        encoding="utf-8",
    )

    assert load_osm_attribute_values(osm, {"123"}) == {
        "123": {
            "highway": "residential",
            "lanes": "2",
            "maxspeed": "40",
        }
    }
