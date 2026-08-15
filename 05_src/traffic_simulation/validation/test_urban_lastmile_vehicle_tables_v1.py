from __future__ import annotations

import csv
import io

from traffic_simulation.network.build_urban_lastmile_vehicle_tables_v1 import (
    CSV_PATH,
    MARKDOWN_PATH,
    generated_content,
)


def test_generated_outputs_are_byte_deterministic_and_current() -> None:
    first = generated_content()
    second = generated_content()
    assert first == second
    for path, expected in first.items():
        assert path.read_text(encoding="utf-8") == expected


def test_generated_csv_is_canonical_record_projection() -> None:
    rows = list(csv.DictReader(io.StringIO(CSV_PATH.read_text(encoding="utf-8"))))
    assert len(rows) == 8
    assert len({row["record_id"] for row in rows}) == 8
    assert next(row for row in rows if row["record_id"] == "F1-HONDA-NVAN-E-COMMON-2025")["curb_mass_kg"] == ""


def test_generated_markdown_contains_exactly_the_four_required_tables() -> None:
    text = MARKDOWN_PATH.read_text(encoding="utf-8")
    headings = [line for line in text.splitlines() if line.startswith("## Table ")]
    assert headings == [
        "## Table A — Last-mile vehicle universe",
        "## Table B — Four-wheel vehicle strata",
        "## Table C — Real vehicle evidence records",
        "## Table D — Empirical envelopes",
    ]
    assert "F2" in text and "incomplete" in text
    assert "observed_empirical_envelope" in text
