"""Load the explicitly governed research-stage status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG_PATH: Final = (
    REPOSITORY_ROOT
    / "reproducibility"
    / "config"
    / "traffic_simulation"
    / "research_stage.yml"
)
SCHEMA_VERSION: Final = 1
VALID_STATUSES: Final = frozenset({"completed", "in_progress", "planned"})


@dataclass(frozen=True, slots=True)
class ResearchStage:
    """One explicitly reviewed research stage."""

    stage_id: str
    label_ja: str
    status: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchProgress:
    """Versioned status used by documentation and review visualizations."""

    updated_at: str
    current_stage_id: str
    current_summary_ja: str
    stages: tuple[ResearchStage, ...]

    @property
    def current_stage(self) -> ResearchStage:
        return next(stage for stage in self.stages if stage.stage_id == self.current_stage_id)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def load_research_progress(path: Path = CONFIG_PATH) -> ResearchProgress:
    """Read and strictly validate the manually governed stage configuration."""

    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid research-stage YAML: {path}") from exc
    if not isinstance(document, dict):
        raise ValueError("research-stage configuration must be a mapping")
    expected_root = {
        "schema_version",
        "updated_at",
        "current_stage_id",
        "current_summary_ja",
        "stages",
    }
    if set(document) != expected_root:
        raise ValueError("research-stage configuration has missing or unknown fields")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported research-stage schema: {document['schema_version']!r}")
    raw_stages = document["stages"]
    if not isinstance(raw_stages, list) or not raw_stages:
        raise ValueError("research-stage stages must be a non-empty list")

    stages: list[ResearchStage] = []
    seen_ids: set[str] = set()
    for index, raw_stage in enumerate(raw_stages):
        if not isinstance(raw_stage, dict) or set(raw_stage) != {
            "id",
            "label_ja",
            "status",
            "evidence",
        }:
            raise ValueError(f"stages[{index}] has missing or unknown fields")
        stage_id = _text(raw_stage["id"], f"stages[{index}].id")
        if stage_id in seen_ids:
            raise ValueError(f"duplicate research-stage id: {stage_id}")
        seen_ids.add(stage_id)
        status = _text(raw_stage["status"], f"stages[{index}].status")
        if status not in VALID_STATUSES:
            raise ValueError(f"unsupported research-stage status: {status}")
        evidence = raw_stage["evidence"]
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            raise ValueError(f"stages[{index}].evidence must be a list of paths")
        for item in evidence:
            if Path(item).is_absolute() or ".." in Path(item).parts:
                raise ValueError(f"invalid evidence path: {item}")
        stages.append(
            ResearchStage(
                stage_id=stage_id,
                label_ja=_text(raw_stage["label_ja"], f"stages[{index}].label_ja"),
                status=status,
                evidence=tuple(evidence),
            )
        )

    current_stage_id = _text(document["current_stage_id"], "current_stage_id")
    matches = [stage for stage in stages if stage.stage_id == current_stage_id]
    if len(matches) != 1 or matches[0].status != "in_progress":
        raise ValueError("current_stage_id must identify one in-progress stage")
    if sum(stage.status == "in_progress" for stage in stages) != 1:
        raise ValueError("exactly one research stage must be in progress")
    return ResearchProgress(
        updated_at=_text(document["updated_at"], "updated_at"),
        current_stage_id=current_stage_id,
        current_summary_ja=_text(document["current_summary_ja"], "current_summary_ja"),
        stages=tuple(stages),
    )
