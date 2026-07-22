"""Load and render the explicitly governed research-stage status."""

from __future__ import annotations

import argparse
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
OUTPUT_PATH: Final = REPOSITORY_ROOT / "RESEARCH_STATUS.md"
SCHEMA_VERSION: Final = 2
VALID_STATUSES: Final = frozenset({"completed", "in_progress", "planned"})


@dataclass(frozen=True, slots=True)
class ResearchStage:
    """One explicitly reviewed research stage."""

    stage_id: str
    label_ja: str
    status: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchReadiness:
    """One explicit decision about whether an output may be used."""

    readiness_id: str
    label_ja: str
    status: str
    status_label_ja: str
    note_ja: str


@dataclass(frozen=True, slots=True)
class ResearchProgress:
    """Versioned status used by documentation and review visualizations."""

    updated_at: str
    current_stage_id: str
    current_summary_ja: str
    readiness: tuple[ResearchReadiness, ...]
    blockers: tuple[str, ...]
    next_actions: tuple[str, ...]
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
        "readiness",
        "blockers",
        "next_actions",
        "stages",
    }
    if set(document) != expected_root:
        raise ValueError("research-stage configuration has missing or unknown fields")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported research-stage schema: {document['schema_version']!r}")
    raw_stages = document["stages"]
    if not isinstance(raw_stages, list) or not raw_stages:
        raise ValueError("research-stage stages must be a non-empty list")

    raw_readiness = document["readiness"]
    if not isinstance(raw_readiness, list) or not raw_readiness:
        raise ValueError("research-stage readiness must be a non-empty list")
    readiness: list[ResearchReadiness] = []
    seen_readiness_ids: set[str] = set()
    for index, raw_item in enumerate(raw_readiness):
        expected_fields = {"id", "label_ja", "status", "status_label_ja", "note_ja"}
        if not isinstance(raw_item, dict) or set(raw_item) != expected_fields:
            raise ValueError(f"readiness[{index}] has missing or unknown fields")
        readiness_id = _text(raw_item["id"], f"readiness[{index}].id")
        if readiness_id in seen_readiness_ids:
            raise ValueError(f"duplicate research-readiness id: {readiness_id}")
        seen_readiness_ids.add(readiness_id)
        readiness.append(
            ResearchReadiness(
                readiness_id=readiness_id,
                label_ja=_text(raw_item["label_ja"], f"readiness[{index}].label_ja"),
                status=_text(raw_item["status"], f"readiness[{index}].status"),
                status_label_ja=_text(
                    raw_item["status_label_ja"], f"readiness[{index}].status_label_ja"
                ),
                note_ja=_text(raw_item["note_ja"], f"readiness[{index}].note_ja"),
            )
        )

    def text_list(field: str) -> tuple[str, ...]:
        values = document[field]
        if not isinstance(values, list) or not values:
            raise ValueError(f"research-stage {field} must be a non-empty list")
        return tuple(_text(value, f"{field}[{index}]") for index, value in enumerate(values))

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
        readiness=tuple(readiness),
        blockers=text_list("blockers"),
        next_actions=text_list("next_actions"),
        stages=tuple(stages),
    )


STATUS_LABELS: Final = {
    "completed": "完了",
    "in_progress": "進行中",
    "planned": "未着手",
}


def render_research_status(progress: ResearchProgress) -> str:
    """Render the review dashboard solely from the governed YAML state."""

    current_index = progress.stages.index(progress.current_stage) + 1
    completed_count = sum(stage.status == "completed" for stage in progress.stages)
    current = progress.current_stage
    evidence_links = []
    for stage in progress.stages:
        links = "<br>".join(f"[{Path(path).name}]({path})" for path in stage.evidence)
        evidence_links.append(links or "-")

    lines = [
        "<!-- Generated from reproducibility/config/traffic_simulation/research_stage.yml. -->",
        "<!-- Do not edit this file directly. Run the write command documented below. -->",
        "",
        "# 研究進捗ダッシュボード",
        "",
        f"**状態更新日:** {progress.updated_at}",
        "",
        "## 現在地",
        "",
        "| 項目 | 状態 |",
        "|---|---|",
        f"| 現在工程 | {current_index} / {len(progress.stages)}: **{current.label_ja}** |",
        f"| 完了工程 | {completed_count}工程 |",
        f"| 概要 | {progress.current_summary_ja} |",
        "",
        "```mermaid",
        "flowchart LR",
        f'    completed["工程1-{completed_count}<br>完了"] --> current["工程{current_index}<br>{current.label_ja}"]',
        f'    current --> future["工程{current_index + 1}-{len(progress.stages)}<br>未着手"]',
        "    classDef done fill:#daf5e5,stroke:#238636,color:#111827;",
        "    classDef active fill:#fff1c2,stroke:#9a6700,color:#111827;",
        "    classDef future fill:#eef1f4,stroke:#8c959f,color:#111827;",
        "    class completed done;",
        "    class current active;",
        "    class future future;",
        "```",
        "",
        "工程ごとの作業量が均等ではないため、進捗率は表示しない。",
        "",
        "## 研究利用可否",
        "",
        "| 対象 | 判定 | 説明 |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {item.label_ja} | **{item.status_label_ja}** (`{item.status}`) | {item.note_ja} |"
        for item in progress.readiness
    )
    lines.extend(["", "## 現在の阻害事項", ""])
    lines.extend(f"- {blocker}" for blocker in progress.blockers)
    lines.extend(["", "## 次の作業", ""])
    lines.extend(f"{index}. {action}" for index, action in enumerate(progress.next_actions, start=1))
    lines.extend(
        [
            "",
            "## 全工程",
            "",
            "| # | 工程ID | 工程 | 状態 | 証拠 |",
            "|---:|---|---|---|---|",
        ]
    )
    for index, (stage, evidence) in enumerate(zip(progress.stages, evidence_links), start=1):
        emphasis = "**" if stage.status == "in_progress" else ""
        lines.append(
            f"| {index} | `{stage.stage_id}` | {emphasis}{stage.label_ja}{emphasis} | "
            f"{emphasis}{STATUS_LABELS[stage.status]}{emphasis} | {evidence} |"
        )
    lines.extend(
        [
            "",
            "## 更新方法",
            "",
            "状態は次のYAMLだけを編集する。成果物の存在だけで工程を自動昇格させない。",
            "",
            "`reproducibility/config/traffic_simulation/research_stage.yml`",
            "",
            "YAML更新後にダッシュボードを再生成する。",
            "",
            "```bash",
            "PYTHONPATH=05_src python -m traffic_simulation.research_stage --write",
            "```",
            "",
            "同期状態だけを確認する場合は次を実行する。",
            "",
            "```bash",
            "PYTHONPATH=05_src python -m traffic_simulation.research_stage --check",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """Write or verify the generated repository dashboard."""

    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="write RESEARCH_STATUS.md")
    action.add_argument("--check", action="store_true", help="fail if RESEARCH_STATUS.md is stale")
    args = parser.parse_args()
    expected = render_research_status(load_research_progress())
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected:
            print(f"stale research dashboard: {OUTPUT_PATH}")
            return 1
        print(f"research dashboard is current: {OUTPUT_PATH}")
        return 0
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    print(f"wrote research dashboard: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
