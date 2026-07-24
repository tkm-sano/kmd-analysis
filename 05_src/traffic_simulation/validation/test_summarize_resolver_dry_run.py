from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from traffic_simulation.network import summarize_resolver_dry_run as summarizer


def test_build_outputs_separates_bulk_missing_from_review_exceptions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(summarizer, "REPOSITORY_ROOT", tmp_path)
    audit_path = tmp_path / "audit.csv"
    failure_path = tmp_path / "failure.json"
    permissions_path = tmp_path / "permissions.json"
    input_path = tmp_path / "input.osm.xml"
    input_path.write_text("<osm version=\"0.6\"/>", encoding="utf-8")
    rows = [
        {
            field: value
            for field, value in zip(
                summarizer.AUDIT_FIELDS,
                (
                    "1",
                    "residential",
                    "",
                    "lanes",
                    "",
                    "",
                    "missing",
                    "",
                    "no_admissible_lane_value",
                    "",
                    "not_matched",
                    "none",
                    "unclassified",
                    "stop",
                    "",
                    "",
                ),
            )
        },
        {
            field: value
            for field, value in zip(
                summarizer.AUDIT_FIELDS,
                (
                    "2",
                    "unclassified",
                    "",
                    "oneway",
                    "-1",
                    "",
                    "valid_but_unsupported",
                    "",
                    "reverse_oneway_requires_directional_tag_safe_transform",
                    "",
                    "not_matched",
                    "none",
                    "unclassified",
                    "stop",
                    "",
                    "",
                ),
            )
        },
    ]
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summarizer.AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failure_path.write_text(
        json.dumps(
            {
                "config_id": "ota_ward_sumo_network_v15",
                "config_version": 15,
                "failures": [
                    {
                        "code": "RS003",
                        "formal_blocker": True,
                        "location": "osm/way/1/lanes",
                        "message": "missing lanes",
                    },
                    {
                        "code": "RS007",
                        "formal_blocker": True,
                        "location": "osm/way/2/oneway",
                        "message": "reverse unsupported",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    permissions_path.write_text(
        json.dumps(
            {
                "profile": "structural",
                "complete": False,
                "ways": [],
                "blockers": [{}, {}],
            }
        ),
        encoding="utf-8",
    )

    exception_rows, summary = summarizer.build_outputs(
        audit_path, failure_path, permissions_path, input_path
    )

    assert [row["failure_code"] for row in exception_rows] == ["RS003", "RS007"]
    assert summary["counts"]["candidate_way_count"] == 1
    assert summary["counts"]["stop_row_count"] == 2
    assert summary["counts"]["bulk_missing_row_count"] == 1
    assert summary["counts"]["rule_or_data_exception_row_count"] == 1
    assert summary["distributions"]["failure_code"] == {"RS003": 1, "RS007": 1}
    assert summary["distributions"]["review_exception_attribute_state"] == {
        "oneway|valid_but_unsupported": 1
    }
