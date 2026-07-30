"""Test fail-closed Resolver exception classification and its independent oracle."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from traffic_simulation.network import classify_resolver_exceptions as classifier
from traffic_simulation.paths import REPOSITORY_ROOT


FIXTURE_DIR = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/resolver_exception_rules"
)


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_fixture_covers_every_rule_and_matches_independent_oracle() -> None:
    table = classifier.load_table()
    cases = load_json("cases.json")["cases"]
    oracle = load_json("oracle.json")
    expected = {
        record["case_id"]: record["matched_rule_ids"]
        for record in oracle["expected"]
    }

    assert oracle["authorship"]["generated_by_production_classifier"] is False
    assert {case["case_type"] for case in cases} == {
        "normal",
        "abnormal",
        "boundary",
    }
    assert {case["case_id"] for case in cases} == set(expected)

    observed = {
        case["case_id"]: classifier.matching_rule_ids(
            case["row"], table["entries"]
        )
        for case in cases
    }
    assert observed == expected

    covered = {
        rule_id
        for rule_ids in expected.values()
        for rule_id in rule_ids
    }
    assert covered == {entry["id"] for entry in table["entries"]}


def test_unmatched_fixture_row_fails_closed() -> None:
    table = classifier.load_table()
    case = next(
        case
        for case in load_json("cases.json")["cases"]
        if case["case_id"] == "ABNORMAL-UNKNOWN-DERIVATION"
    )
    with pytest.raises(classifier.ExceptionClassificationError, match="matched 0"):
        classifier.classify_rows([case["row"]], table)


def test_overlapping_rules_fail_closed() -> None:
    table = classifier.load_table()
    duplicate = copy.deepcopy(table["entries"][0])
    duplicate["id"] = "DUPLICATE-RULE"
    entries = [*table["entries"], duplicate]
    case = load_json("cases.json")["cases"][0]["row"]
    modified = dict(table)
    modified["entries"] = entries

    with pytest.raises(classifier.ExceptionClassificationError, match="matched 2"):
        classifier.classify_rows([case], modified)


def test_all_307_baseline_rows_match_exactly_one_rule() -> None:
    summary = classifier.validate_baseline()

    assert summary["selected_rows"] == 307
    assert summary["classified_rows"] == 307
    assert summary["unmatched_rows"] == 0
    assert summary["overlapping_rows"] == 0
    assert summary["exactly_one_rule_per_row"] is True
