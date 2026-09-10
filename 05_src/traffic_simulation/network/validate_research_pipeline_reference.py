"""Validate the current pipeline reference without executing research pipelines."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "RESEARCH_PIPELINE_REFERENCE.md"
INDEX = ROOT / "reproducibility/indexes/research_repository_index_v17.yml"
MAP = ROOT / "reproducibility/config/research_portal/research_map_v1.yml"
AUTHORITY = ROOT / "reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml"
CATALOG = ROOT / "05_src/research_cli/catalog.py"

PIPELINES = (
    "A. 外部・オープンデータ",
    "B. 需要",
    "C. リクエスト・配送先",
    "D. ネットワーク構築",
    "E. 配送先マッピング",
    "F. ネットワーク受入",
    "G. 経路計算ベースライン",
    "H. 共通配送インスタンス",
    "I. 古典最適化",
    "J. QUBO",
    "K. QAOA",
    "L. シナリオ構築",
    "M. 配送シミュレーション",
    "N. 評価",
    "O. エビデンスに基づく解釈",
    "P. 感度・頑健性",
    "Q. 公開・再現性凍結",
)
TEMPLATE_HEADINGS = (
    "目的",
    "現在の状態",
    "開始条件",
    "正本入力",
    "コマンド",
    "実装",
    "出力",
    "正本・信頼源",
    "検証",
    "受入・DONE条件",
    "来歴",
    "既知の制約",
    "未解決の判断",
    "次工程への引渡し",
)
LINK_PATTERN = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def validate() -> dict:
    text = REFERENCE.read_text(encoding="utf-8")
    index = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    research_map = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    authority = yaml.safe_load(AUTHORITY.read_text(encoding="utf-8"))
    accepted = authority["accepted_run"]
    acceptance = json.loads((ROOT / accepted["acceptance_artifact"]).read_text(encoding="utf-8"))

    required_top = (
        "## 更新方針",
        "## 現在の研究位置 — 今何をすべきか",
        "## パイプライン全体図",
        "## 研究コマンド索引",
        "## 成果物・正本対応表",
        "## 検証対応表",
        "## 依存関係表",
        "## 現行ライフサイクル境界",
        "## 文書の役割分担",
    )
    for heading in required_top:
        assert heading in text, f"missing required heading: {heading}"

    section_offsets = []
    for pipeline in PIPELINES:
        marker = f"## {pipeline}"
        offset = text.find(marker)
        assert offset >= 0, f"missing pipeline section: {pipeline}"
        section_offsets.append((pipeline, offset))
    assert section_offsets == sorted(section_offsets, key=lambda item: item[1])
    for index_position, (pipeline, start) in enumerate(section_offsets):
        end = section_offsets[index_position + 1][1] if index_position + 1 < len(section_offsets) else text.find("## 研究コマンド索引", start)
        section = text[start:end]
        for heading in TEMPLATE_HEADINGS:
            assert f"### {heading}" in section, f"{pipeline}: missing template heading: {heading}"

    broken_links = []
    checked_links = 0
    for raw_target in LINK_PATTERN.findall(text):
        target = raw_target.strip().strip("<>").split(maxsplit=1)[0].strip("'\"")
        if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        checked_links += 1
        if not (REFERENCE.parent / target).resolve().exists():
            broken_links.append(raw_target)
    assert not broken_links, f"broken local links: {broken_links}"

    catalog_text = CATALOG.read_text(encoding="utf-8")
    commands = re.findall(r'CommandInfo\("[^"]+", "([^"]+)"', catalog_text)
    assert len(commands) == 41 and len(commands) == len(set(commands))
    missing_commands = [command for command in commands if f"./research {command}" not in text]
    assert not missing_commands, f"catalog commands absent from reference: {missing_commands}"

    assert index["pipeline_reference"] == str(REFERENCE.relative_to(ROOT))
    important = next(item for item in index["important_markdown"] if item["path"] == index["pipeline_reference"])
    assert important["document_id"] == "DOC-RESEARCH-PIPELINE-REFERENCE"
    assert important["role"] == "CURRENT_REFERENCE"
    assert important["lifecycle"] == "CURRENT"
    assert research_map["current_position"]["current_stage"] == "Routing Baseline"
    assert research_map["current_position"]["immediate_next_task"] == "Define routing scope for delivery instances"
    assert "現在の研究工程 | `Routing Baseline — NEXT`" in text
    assert "直ちに行う作業 | 配送インスタンス用の経路計算範囲を定義する。" in text
    assert accepted["network_file"] in text
    assert accepted["network_sha256"] in text
    assert "ネットワークグラフ規模（`|V|`ノード・`|E|`有向edge・lane数）" in text
    assert "`required_od_pair_count`は`NOT YET AVAILABLE`" in text
    assert sha256(ROOT / accepted["network_file"]) == accepted["network_sha256"]
    assert acceptance["FORMAL_NETWORK_ACCEPTED"] is True
    assert "`HISTORICAL`: strict v17" in text
    assert "`SUPERSEDED`: Hierarchical Hybrid" in text

    return {
        "pipeline_reference": "passed",
        "pipeline_sections": len(PIPELINES),
        "commands": len(commands),
        "checked_local_links": checked_links,
        "broken_local_links": len(broken_links),
        "current_stage": research_map["current_position"]["current_stage"],
        "accepted_network_sha256": accepted["network_sha256"],
        "formal_network_accepted": acceptance["FORMAL_NETWORK_ACCEPTED"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
