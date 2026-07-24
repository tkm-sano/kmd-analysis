"""Validate accounting and fail-closed state of the Resolver decision table."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


TABLE_PATH = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/"
    "resolver_exception_decision_table.yml"
)
ALLOWED_DECISION_STATUSES = {
    "specification_required",
    "fixture_required",
    "implementation_required",
    "ready_for_fixture_execution",
    "implemented",
}


def load_table() -> dict:
    value = yaml.safe_load(TABLE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_decision_table_accounts_for_the_full_v15_exception_population() -> None:
    table = load_table()
    entries = table["entries"]
    expected = table["expected_totals"]

    assert table["schema_version"] == 1
    assert table["status"] == "classification_complete_resolution_pending"
    assert table["baseline"]["rule_or_data_exception_rows"] == 307
    assert len({entry["id"] for entry in entries}) == len(entries)
    assert all(entry["baseline_rows"] > 0 for entry in entries)
    assert all(
        entry["baseline_distinct_ways"] == entry["baseline_rows"]
        for entry in entries
    )

    by_attribute = Counter()
    by_failure_code = Counter()
    for entry in entries:
        by_attribute[entry["attribute"]] += entry["baseline_rows"]
        by_failure_code[entry["failure_code"]] += entry["baseline_rows"]

    assert dict(sorted(by_attribute.items())) == dict(
        sorted(expected["by_attribute"].items())
    )
    assert dict(sorted(by_failure_code.items())) == dict(
        sorted(expected["by_failure_code"].items())
    )
    assert sum(by_attribute.values()) == expected["all_entries"] == 307


def test_unimplemented_decision_entries_remain_fail_closed() -> None:
    table = load_table()

    for entry in table["entries"]:
        assert entry["decision_status"] in ALLOWED_DECISION_STATUSES
        assert entry["required_fixtures"]
        if entry["decision_status"] != "implemented":
            assert entry["current_action"] == "stop"

    relation_entries = table["relation_scope_findings"]["entries"]
    assert sum(entry["baseline_relations"] for entry in relation_entries) == 3
    assert all(entry["formal_action"] == "stop" for entry in relation_entries)
    assert all(entry["decision_status"] != "implemented" for entry in relation_entries)


def test_decision_table_references_existing_authorities() -> None:
    table = load_table()

    for value in table["authority"].values():
        assert (REPOSITORY_ROOT / value).is_file()
