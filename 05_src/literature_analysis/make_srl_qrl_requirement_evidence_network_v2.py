from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable

import matplotlib

# VSCode terminal / CI / SSH でも確実に画像保存できるように GUI backend を使わない。
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd


DEFAULT_OUTPUT = Path("06_outputs/figures/active/02_requirement_mapping/srl_qrl_requirement_evidence_network_ja.png")
DEFAULT_ALIGNMENT = Path("literature/206_20260626_social_quantum_readiness_alignment.csv")
DEFAULT_QRL_EVIDENCE = Path("literature/202_20260625_quantum_readiness_evidence.csv")
DEFAULT_SOCIAL_VARIABLES = Path("literature/208_20260625_social_stage_variable_extraction.csv")
DEFAULT_CIRCUIT_RESOURCES = Path("literature/200_20260625_circuit_resources.csv")

SRL_ORDER = [f"SRL{i}" for i in range(1, 6)]
QRL_ORDER = [f"QRL{i}" for i in range(1, 6)]

STAGE_TITLES = {
    "SRL1": "VRP計算",
    "SRL2": "都市配送",
    "SRL3": "EV配送",
    "SRL4": "動的EV物流",
    "SRL5": "実運用",
}

SRL_SHORT_JA = {
    "SRL1": "単純routing",
    "SRL2": "都市配送制約",
    "SRL3": "EV統合routing",
    "SRL4": "動的EV物流",
    "SRL5": "運用導入",
}

TRANSITION_LABELS = [
    "+ 容量・時間窓・depot・service",
    "+ SOC・battery・charging・energy",
    "+ traffic・需要変動・再最適化",
    "+ workflow・KPI・導入評価",
]

QRL_SHORT_JA = {
    "QRL1": "理論定式化",
    "QRL2": "小規模simulation",
    "QRL3": "NISQ / hardware-aware",
    "QRL4": "resource estimation",
    "QRL5": "early utility / FTQC候補",
}


# -----------------------------------------------------------------------------
# CLI / path handling
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SRL–QRL上に、VRP計算からEV配送・動的物流・実運用へ至る"
            "要求条件と量子側証拠の連結ネットワークを描画します。"
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="研究リポジトリのルート。省略時は script / cwd から自動検出します。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"出力PNG。相対パスはroot基準。既定: {DEFAULT_OUTPUT}",
    )
    parser.add_argument("--alignment", type=Path, default=DEFAULT_ALIGNMENT)
    parser.add_argument("--qrl-evidence", type=Path, default=DEFAULT_QRL_EVIDENCE)
    parser.add_argument("--social-variables", type=Path, default=DEFAULT_SOCIAL_VARIABLES)
    parser.add_argument("--circuit-resources", type=Path, default=DEFAULT_CIRCUIT_RESOURCES)
    parser.add_argument("--dpi", type=int, default=220, help="出力DPI。既定: 220")
    parser.add_argument(
        "--open",
        action="store_true",
        help="生成後にOS既定アプリでPNGを開きます。",
    )
    return parser.parse_args()


def find_project_root(explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        root = explicit_root.expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"--root が存在しません: {root}")
        return root

    starts = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    checked: set[Path] = set()
    for start in starts:
        for candidate in [start, *start.parents]:
            if candidate in checked:
                continue
            checked.add(candidate)
            if (candidate / "literature").is_dir():
                return candidate

    raise FileNotFoundError(
        "研究リポジトリのルートを自動検出できませんでした。"
        "\nリポジトリのルートで実行するか、--root /path/to/research を指定してください。"
    )


def resolve_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} が見つかりません: {path}")


# -----------------------------------------------------------------------------
# Data helpers
# -----------------------------------------------------------------------------

def require_columns(df: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"{label} に必要な列がありません: {', '.join(missing)}\n"
            f"現在の列: {', '.join(map(str, df.columns))}"
        )


def normalize_level_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def sort_by_level(df: pd.DataFrame, level_col: str, order: list[str]) -> pd.DataFrame:
    work = df.copy()
    work[level_col] = normalize_level_series(work[level_col])
    work[level_col] = pd.Categorical(work[level_col], categories=order, ordered=True)
    work = work.sort_values(level_col)
    work[level_col] = work[level_col].astype(str)
    return work


def first_existing(row: pd.Series, candidates: Iterable[str], default: str = "") -> str:
    for key in candidates:
        if key in row.index and pd.notna(row[key]):
            value = str(row[key]).strip()
            if value and value.lower() != "nan":
                return value
    return default


def parse_qrl_level(value: object, fallback: int) -> str:
    match = re.search(r"QRL\s*([1-5])", str(value), flags=re.IGNORECASE)
    return f"QRL{match.group(1)}" if match else f"QRL{fallback}"


def level_number(level: str, fallback: int) -> int:
    match = re.search(r"([1-5])", level)
    return int(match.group(1)) if match else fallback


def wrap(text: object, width: int) -> str:
    value = str(text).strip()
    if not value or value.lower() == "nan":
        return ""
    return "\n".join(
        textwrap.wrap(value, width=width, break_long_words=False, replace_whitespace=False)
    )


def shorten_text(text: object, max_chars: int) -> str:
    value = str(text).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def split_source_ids(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    return {
        part.strip()
        for part in re.split(r"[;,]", str(value))
        if part.strip()
    }


def extract_numeric_widths(value: object) -> list[float]:
    if pd.isna(value):
        return []
    text = str(value)
    # "n logical qubits" のような式は数値値ではないので除外。
    if not re.search(r"\d", text):
        return []
    return [float(v) for v in re.findall(r"\b\d+(?:\.\d+)?\b", text)]


def social_variable_summary(social_vars: pd.DataFrame | None, srl: str, limit: int = 4) -> str:
    if social_vars is None or "social_readiness_level" not in social_vars.columns:
        return ""

    level_series = social_vars["social_readiness_level"].astype(str).str.upper()
    subset = social_vars[level_series.str.contains(rf"\b{srl}\b", regex=True, na=False)].copy()
    if subset.empty:
        return ""

    confidence_rank = {"high": 0, "medium": 1, "low": 2}
    subset["_confidence_rank"] = (
        subset.get("confidence", pd.Series(index=subset.index, dtype=object))
        .astype(str)
        .str.lower()
        .map(confidence_rank)
        .fillna(3)
    )
    subset["_primary_rank"] = ~(
        subset.get("primary_evidence_status", pd.Series(index=subset.index, dtype=object))
        .astype(str)
        .str.contains("primary", case=False, na=False)
    )
    subset = subset.sort_values(["_primary_rank", "_confidence_rank"])

    names: list[str] = []
    for value in subset.get("variable_name", pd.Series(dtype=object)).dropna():
        name = str(value).strip()
        if name and name not in names:
            names.append(name)
        if len(names) >= limit:
            break
    return " / ".join(names)


def qrl_evidence_summary(row: pd.Series) -> str:
    """QRL CSVの証拠列から、図中に入る短いキーワード列を作る。"""
    column_labels = [
        ("width_evidence", "width"),
        ("depth_evidence", "depth"),
        ("gate_count_evidence", "gates"),
        ("shots_evidence", "shots"),
        ("runtime_evidence", "runtime"),
        ("feasibility_evidence", "feasibility"),
        ("resource_estimate_evidence", "resource estimate"),
    ]
    keywords: list[str] = []
    for col, label in column_labels:
        if col not in row.index or pd.isna(row[col]):
            continue
        text = str(row[col]).strip().lower()
        if not text or text in {"nan", "not applicable", "not required", "usually not operationally tested"}:
            continue
        keywords.append(label)

    # 図中では最大3要素に制限し、文章の重なりを防ぐ。
    return " / ".join(keywords[:3]) or first_existing(
        row, ["technical_stage", "status"], "evidence stage"
    )


def qrl_resource_stat(row: pd.Series, circuit_resources: pd.DataFrame | None) -> str:
    if circuit_resources is None:
        return ""
    if "paper_id" not in circuit_resources.columns or "circuit_width_qubits" not in circuit_resources.columns:
        return ""

    source_ids = split_source_ids(row.get("primary_evidence_sources", ""))
    if not source_ids:
        return ""

    subset = circuit_resources[circuit_resources["paper_id"].astype(str).isin(source_ids)]
    if subset.empty:
        return ""

    widths: list[float] = []
    for value in subset["circuit_width_qubits"]:
        widths.extend(extract_numeric_widths(value))

    if widths:
        low = int(min(widths)) if min(widths).is_integer() else min(widths)
        high = int(max(widths)) if max(widths).is_integer() else max(widths)
        return f"resource records: {len(subset)} / reported width: {low}–{high}"
    return f"resource records: {len(subset)}"


# -----------------------------------------------------------------------------
# Drawing helpers
# -----------------------------------------------------------------------------

def setup_font(root: Path) -> str | None:
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        str(root / "future_design_analysis_methods/assets/fonts/101_20260705_droidsansfallbackfull.ttf"),
    ]

    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            try:
                fm.fontManager.addfont(str(path))
                family = fm.FontProperties(fname=str(path)).get_name()
                plt.rcParams["font.family"] = family
                plt.rcParams["font.sans-serif"] = [family, "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                return family
            except Exception:
                continue

    for family in ["Hiragino Sans", "Noto Sans CJK JP", "Yu Gothic", "Meiryo", "IPAexGothic"]:
        try:
            font_path = fm.findfont(family, fallback_to_default=False)
            if font_path and Path(font_path).exists():
                plt.rcParams["font.family"] = family
                plt.rcParams["axes.unicode_minus"] = False
                return family
        except Exception:
            continue

    plt.rcParams["axes.unicode_minus"] = False
    return None


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    face: str,
    edge: str,
    lw: float = 1.25,
    radius: float = 0.04,
    zorder: int = 3,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=lw,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    lw: float = 1.2,
    rad: float = 0.0,
    ms: float = 14,
    linestyle: str = "solid",
    zorder: int = 4,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=ms,
            linewidth=lw,
            color=color,
            linestyle=linestyle,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=3,
            shrinkB=3,
            zorder=zorder,
        )
    )


def build_figure(
    *,
    alignment: pd.DataFrame,
    qrl: pd.DataFrame,
    social_vars: pd.DataFrame | None,
    circuit_resources: pd.DataFrame | None,
    output: Path,
    dpi: int,
) -> tuple[int, int]:
    # 16:9。PowerPoint / 学会発表スライドに貼りやすい比率。
    fig_w, fig_h = 16.0, 9.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.subplots_adjust(left=0.055, right=0.955, top=0.825, bottom=0.105)

    bg = "#F7F7F3"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(-1.55, 6.55)
    ax.set_ylim(0.42, 5.58)
    ax.set_aspect("auto")

    # 5×5 SRL–QRL grid
    for x in range(1, 6):
        ax.axvline(x, color="#DCE2DF", linewidth=0.9, zorder=0)
    for y in range(1, 6):
        ax.axhline(y, color="#DCE2DF", linewidth=0.9, zorder=0)

    # 対応の目安。等値線ではないことを注記する。
    ax.plot([1, 5], [1, 5], color="#D8C8AF", linewidth=18, alpha=0.14, zorder=0)

    title_color = "#1F2933"
    subtitle_color = "#57606A"
    node_edge = "#7891A8"
    path_color = "#315F7A"
    thin_color = "#9CA6AF"

    fig.text(
        0.055,
        0.962,
        "SRL–QRL上の要求・証拠連結ネットワーク",
        fontsize=22,
        fontweight="bold",
        color=title_color,
    )
    fig.text(
        0.055,
        0.922,
        "VRP計算からEV配送・動的物流・実運用へ至る要求追加と、量子側証拠段階の対応を整理する。",
        fontsize=11.2,
        color=subtitle_color,
    )
    fig.text(
        0.945,
        0.962,
        "※ 配置は対応の目安。SRLx = QRLx を意味しない。",
        ha="right",
        va="top",
        fontsize=9.2,
        color="#7B6044",
    )

    # 軸
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xticklabels(QRL_ORDER, fontsize=11, fontweight="bold")
    ax.set_yticklabels(SRL_ORDER, fontsize=11, fontweight="bold")
    ax.xaxis.tick_top()
    ax.set_ylabel("SRL：EV・物流側の要求段階", fontsize=12.2, fontweight="bold", labelpad=14)
    fig.text(
        0.54,
        0.855,
        "QRL：量子側の証拠・検証段階",
        ha="center",
        fontsize=12.2,
        fontweight="bold",
        color=title_color,
    )
    ax.tick_params(length=0, pad=5)

    # QRL短縮ラベルを上部に追加
    for i, qrl_level in enumerate(QRL_ORDER, start=1):
        ax.text(
            i,
            5.49,
            QRL_SHORT_JA[qrl_level],
            ha="center",
            va="top",
            fontsize=7.9,
            color="#5B6670",
        )

    center_colors = ["#E5EFF8", "#E4F1EA", "#FFF0D8", "#F5E1E7", "#E9EBF1"]
    center_w, center_h = 1.15, 0.55
    left_x, left_w, left_h = -1.43, 1.25, 0.66
    right_x, right_w, right_h = 5.22, 1.18, 0.66

    for idx, srl_level in enumerate(SRL_ORDER, start=1):
        row = alignment.loc[alignment["social_readiness_level"] == srl_level].iloc[0]
        social_label = first_existing(row, ["social_readiness_label", "label"], srl_level)
        social_condition = first_existing(
            row,
            ["social_condition", "definition", "social_readiness_definition"],
            "社会側要求条件",
        )
        qrl_level = parse_qrl_level(row.get("corresponding_quantum_readiness", ""), idx)
        qrl_num = level_number(qrl_level, idx)
        center_x = float(qrl_num)
        center_y = float(idx)

        # 左：社会側要求の根拠カード
        ly = center_y - left_h / 2
        add_box(ax, left_x, ly, left_w, left_h, "#FFFFFF", "#AFC5D6", lw=1.05)
        ax.text(
            left_x + 0.06,
            ly + left_h - 0.09,
            f"{srl_level} / {SRL_SHORT_JA[srl_level]}",
            ha="left",
            va="top",
            fontsize=8.8,
            fontweight="bold",
            color=title_color,
        )
        ax.text(
            left_x + 0.06,
            ly + left_h - 0.26,
            wrap(shorten_text(social_condition, 70), 24),
            ha="left",
            va="top",
            fontsize=7.0,
            color="#37414A",
            linespacing=1.10,
        )
        var_summary = social_variable_summary(social_vars, srl_level, limit=3)
        if var_summary:
            ax.text(
                left_x + 0.06,
                ly + 0.06,
                wrap(f"変数例: {shorten_text(var_summary, 58)}", 24),
                ha="left",
                va="bottom",
                fontsize=6.8,
                color="#567080",
            )

        # 中央：代表的な連結ノード
        cx = center_x - center_w / 2
        cy = center_y - center_h / 2
        add_box(ax, cx, cy, center_w, center_h, center_colors[idx - 1], node_edge, lw=1.45)
        ax.text(
            center_x,
            cy + center_h - 0.09,
            STAGE_TITLES[srl_level],
            ha="center",
            va="top",
            fontsize=10.8,
            fontweight="bold",
            color=title_color,
        )
        ax.text(
            center_x,
            cy + 0.09,
            f"{srl_level} / 対応証拠: {qrl_level}",
            ha="center",
            va="bottom",
            fontsize=7.3,
            color="#46545F",
        )

        # 右：量子側証拠カード
        qrow = qrl.loc[qrl["quantum_readiness_level"] == qrl_level].iloc[0]
        q_label = QRL_SHORT_JA[qrl_level]
        evidence = qrl_evidence_summary(qrow)
        resource_stat = qrl_resource_stat(qrow, circuit_resources)

        ry = center_y - right_h / 2
        add_box(ax, right_x, ry, right_w, right_h, "#FFFFFF", "#D6B28B", lw=1.05)
        ax.text(
            right_x + 0.06,
            ry + right_h - 0.09,
            f"{qrl_level} / {q_label}",
            ha="left",
            va="top",
            fontsize=8.7,
            fontweight="bold",
            color=title_color,
        )
        ax.text(
            right_x + 0.06,
            ry + right_h - 0.27,
            wrap(evidence, 22),
            ha="left",
            va="top",
            fontsize=7.0,
            color="#37414A",
            linespacing=1.08,
        )
        if resource_stat:
            ax.text(
                right_x + 0.06,
                ry + 0.06,
                wrap(resource_stat, 25),
                ha="left",
                va="bottom",
                fontsize=6.6,
                color="#795B3E",
            )

        # 細線：社会側要求 → 代表ノード → 量子側証拠
        add_arrow(
            ax,
            (left_x + left_w, center_y),
            (cx, center_y),
            thin_color,
            lw=1.0,
            ms=8,
        )
        add_arrow(
            ax,
            (cx + center_w, center_y),
            (right_x, center_y),
            thin_color,
            lw=1.0,
            ms=8,
        )

        # 太線：代表的な連結経路
        if idx < 5:
            next_row = alignment.loc[
                alignment["social_readiness_level"] == SRL_ORDER[idx]
            ].iloc[0]
            next_qrl = parse_qrl_level(
                next_row.get("corresponding_quantum_readiness", ""), idx + 1
            )
            next_x = float(level_number(next_qrl, idx + 1))
            next_y = float(idx + 1)
            add_arrow(
                ax,
                (center_x + center_w / 2, center_y + 0.03),
                (next_x - center_w / 2, next_y - 0.03),
                path_color,
                lw=3.2,
                rad=0.04,
                ms=17,
            )
            mid_x = (center_x + next_x) / 2
            mid_y = (center_y + next_y) / 2 + 0.13
            ax.text(
                mid_x,
                mid_y,
                TRANSITION_LABELS[idx - 1],
                ha="center",
                va="center",
                fontsize=7.5,
                color="#40505C",
                bbox=dict(
                    boxstyle="round,pad=0.18",
                    facecolor=bg,
                    edgecolor="none",
                    alpha=0.96,
                ),
                zorder=6,
            )

    # 凡例・解釈ルール
    ax.text(
        -1.42,
        0.53,
        "太線：代表的な要求追加の経路   ｜   細線：要求条件と証拠段階の対応   ｜   セル位置：性能スコアではない",
        ha="left",
        va="center",
        fontsize=7.5,
        color="#55616A",
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    # 出典ファイルはfigure footerへ。
    fig.text(
        0.055,
        0.028,
        "社会側根拠: 208_20260625_social_stage_variable_extraction.csv / 206_20260626_social_quantum_readiness_alignment.csv   |   "
        "量子側根拠: 202_20260625_quantum_readiness_evidence.csv / 200_20260625_circuit_resources.csv",
        fontsize=7.7,
        color="#657079",
    )
    fig.text(
        0.945,
        0.028,
        "概念図：実装確率・量子優位・正式TRLを示さない",
        ha="right",
        fontsize=7.7,
        color="#657079",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, facecolor=fig.get_facecolor())
    plt.close(fig)

    return int(fig_w * dpi), int(fig_h * dpi)


# -----------------------------------------------------------------------------
# Result output / preview
# -----------------------------------------------------------------------------

def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def open_file(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            opener = shutil.which("xdg-open")
            if opener:
                subprocess.Popen([opener, str(path)])
    except Exception as exc:
        print(f"[WARN] 生成ファイルを自動で開けませんでした: {exc}")


def print_result(
    *,
    output: Path,
    width_px: int,
    height_px: int,
    input_files: list[Path],
    font_name: str | None,
) -> None:
    print("\n" + "=" * 72)
    print("[OK] SRL–QRL 要求・証拠連結ネットワークを生成しました")
    print("=" * 72)
    print(f"出力PNG : {output}")
    print(f"ファイル : {human_size(output.stat().st_size)}")
    print(f"解像度   : {width_px} × {height_px} px (16:9 canvas)")
    print(f"日本語font: {font_name or '自動検出できず（文字化け時は日本語fontを確認）'}")
    print("\n使用データ:")
    for path in input_files:
        status = "OK" if path.is_file() else "optional / not found"
        print(f"  - [{status}] {path}")

    print("\nVSCodeで開く:")
    print(f'  code "{output}"')
    print("\nFinder / 既定アプリで開く（macOS）:")
    print(f'  open "{output}"')
    print("=" * 72)


def main() -> int:
    args = parse_args()
    root = find_project_root(args.root)

    output = resolve_path(root, args.output)
    alignment_path = resolve_path(root, args.alignment)
    qrl_path = resolve_path(root, args.qrl_evidence)
    social_vars_path = resolve_path(root, args.social_variables)
    circuit_path = resolve_path(root, args.circuit_resources)

    require_file(alignment_path, "SRL–QRL alignment CSV")
    require_file(qrl_path, "QRL evidence CSV")

    alignment = pd.read_csv(alignment_path)
    qrl = pd.read_csv(qrl_path)

    require_columns(
        alignment,
        ["social_readiness_level", "social_readiness_label", "corresponding_quantum_readiness"],
        "alignment CSV",
    )
    require_columns(
        qrl,
        ["quantum_readiness_level", "quantum_readiness_label"],
        "QRL evidence CSV",
    )

    alignment = sort_by_level(alignment, "social_readiness_level", SRL_ORDER)
    qrl = sort_by_level(qrl, "quantum_readiness_level", QRL_ORDER)

    missing_srl = [level for level in SRL_ORDER if level not in set(alignment["social_readiness_level"])]
    missing_qrl = [level for level in QRL_ORDER if level not in set(qrl["quantum_readiness_level"])]
    if missing_srl:
        raise ValueError(f"alignment CSV に不足しているSRLがあります: {missing_srl}")
    if missing_qrl:
        raise ValueError(f"QRL evidence CSV に不足しているQRLがあります: {missing_qrl}")

    social_vars = pd.read_csv(social_vars_path) if social_vars_path.is_file() else None
    circuit_resources = pd.read_csv(circuit_path) if circuit_path.is_file() else None

    font_name = setup_font(root)
    width_px, height_px = build_figure(
        alignment=alignment,
        qrl=qrl,
        social_vars=social_vars,
        circuit_resources=circuit_resources,
        output=output,
        dpi=args.dpi,
    )

    print_result(
        output=output,
        width_px=width_px,
        height_px=height_px,
        input_files=[alignment_path, qrl_path, social_vars_path, circuit_path],
        font_name=font_name,
    )

    if args.open:
        open_file(output)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        print("\n例:", file=sys.stderr)
        print(
            "  python3 05_src/literature_analysis/make_srl_qrl_requirement_evidence_network_v2.py --root . --open",
            file=sys.stderr,
        )
        raise SystemExit(1)
