"""Tests for the governed research-stage status."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from traffic_simulation.research_stage import load_research_progress


def valid_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "updated_at": "2026-07-17",
        "current_stage_id": "sumo_network",
        "current_summary_ja": "SUMO道路網を生成する段階",
        "stages": [
            {
                "id": "input",
                "label_ja": "入力取得",
                "status": "completed",
                "evidence": ["03_data/metadata/source.csv"],
            },
            {
                "id": "sumo_network",
                "label_ja": "SUMO道路網",
                "status": "in_progress",
                "evidence": [],
            },
            {
                "id": "evaluation",
                "label_ja": "比較評価",
                "status": "planned",
                "evidence": [],
            },
        ],
    }


def write_config(path: Path, document: dict[str, object]) -> Path:
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    return path


def test_loads_current_stage(tmp_path: Path) -> None:
    progress = load_research_progress(write_config(tmp_path / "stage.yml", valid_document()))
    assert progress.current_stage.stage_id == "sumo_network"
    assert progress.current_stage.status == "in_progress"
    assert [stage.status for stage in progress.stages] == [
        "completed",
        "in_progress",
        "planned",
    ]


def test_rejects_multiple_in_progress_stages(tmp_path: Path) -> None:
    document = valid_document()
    stages = document["stages"]
    assert isinstance(stages, list)
    stages[2]["status"] = "in_progress"
    with pytest.raises(ValueError, match="exactly one"):
        load_research_progress(write_config(tmp_path / "stage.yml", document))


def test_rejects_escaping_evidence_path(tmp_path: Path) -> None:
    document = valid_document()
    stages = document["stages"]
    assert isinstance(stages, list)
    stages[0]["evidence"] = ["../outside.txt"]
    with pytest.raises(ValueError, match="invalid evidence path"):
        load_research_progress(write_config(tmp_path / "stage.yml", document))
