from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "figures" / "01_quantum_vrp_evidence" / "srl_qrl_methodology_design.png"


def set_font() -> None:
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            fm.fontManager.addfont(path)
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            break


def wrapped(text: str, width: int = 34) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def box(ax, x, y, w, h, title, body, face, edge, title_color="#24282B"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.25,
    )
    ax.add_patch(patch)
    wrap_width = max(24, int(w * 95))
    ax.text(x + 0.035, y + h - 0.055, title, ha="left", va="top", fontsize=12.0, fontweight="bold", color=title_color)
    ax.text(x + 0.035, y + h - 0.125, wrapped(body, wrap_width), ha="left", va="top", fontsize=8.2, color="#30363A", linespacing=1.12)


def arrow(ax, start, end, color="#6B7378"):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=1.45,
            color=color,
            shrinkA=5,
            shrinkB=5,
            connectionstyle="arc3,rad=0.0",
        )
    )


def main() -> None:
    set_font()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(15.8, 8.6), dpi=200)
    fig.patch.set_facecolor("#F8F7F3")
    ax.set_facecolor("#F8F7F3")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    text = "#24282B"
    blue = "#DCECEF"
    green = "#E5F1EA"
    amber = "#F3E7D7"
    rose = "#F2DFE3"
    gray = "#EEF0EF"
    edge = "#B8C1C0"

    fig.text(0.055, 0.945, "SRL/QRL Methodology Design", fontsize=22, fontweight="bold", color=text)
    fig.text(
        0.055,
        0.905,
        "How literature evidence and EV-side readiness indicators are converted into scored Figure 1 outputs.",
        fontsize=11.5,
        color="#5B6266",
    )

    # Main pipeline.
    y = 0.58
    h = 0.24
    w = 0.19
    xs = [0.055, 0.295, 0.535, 0.775]
    box(
        ax,
        xs[0],
        y,
        w,
        h,
        "1. Evidence Inputs",
        "Quantum VRP/CVRP papers and source notes. EV/logistics context from World Bank LPI, IEA, NREL, and related sources.",
        blue,
        edge,
    )
    box(
        ax,
        xs[1],
        y,
        w,
        h,
        "2. Extract Variables",
        "Technical variables: width, depth, backend, shots, gates, resource estimate. EV-side variables: charging, depot/grid, fleet/workflow.",
        green,
        edge,
    )
    box(
        ax,
        xs[2],
        y,
        w,
        h,
        "3. Define Rules",
        "Researcher-defined coding: SRL1-5, QRL1-5, inclusion criteria, validation stages, and SRL score scale.",
        amber,
        edge,
    )
    box(
        ax,
        xs[3],
        y,
        w,
        h,
        "4. Apply to Rows",
        "Add QRL/SRL labels, social_readiness_score, assignment basis, and QRL-wise mean scores to the Figure 1 data.",
        gray,
        edge,
    )

    for i in range(3):
        arrow(ax, (xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2))

    # Supporting CSVs.
    box(
        ax,
        0.055,
        0.35,
        0.89,
        0.17,
        "Traceability CSVs",
        "Definition and rule support: 207_20260705_social_stage_sources.csv, 210_20260625_technical_stage_sources.csv, 208_20260625_social_stage_variable_extraction.csv, 211_20260625_technical_stage_variable_extraction.csv, 206_20260626_social_quantum_readiness_alignment.csv, 202_20260625_quantum_readiness_evidence.csv.",
        "#FFFFFF",
        "#D0D5D3",
    )
    arrow(ax, (0.50, 0.58), (0.50, 0.46))

    # Outputs.
    box(
        ax,
        0.145,
        0.14,
        0.30,
        0.17,
        "Figure 1",
        "Width evidence by instance and validation stage.",
        rose,
        edge,
    )
    box(
        ax,
        0.555,
        0.14,
        0.30,
        0.17,
        "QRL-wise SRL Score Table",
        "Mean SRL score and instance summaries by QRL level.",
        rose,
        edge,
    )
    arrow(ax, (0.37, 0.35), (0.30, 0.31))
    arrow(ax, (0.63, 0.35), (0.70, 0.31))

    # Side note.
    note = FancyBboxPatch(
        (0.055, 0.045),
        0.89,
        0.055,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor="#FFFFFF",
        edgecolor="#D0D5D3",
        linewidth=1.0,
    )
    ax.add_patch(note)
    ax.text(
        0.075,
        0.073,
        "Key distinction: width/depth/backend are extracted from papers; SRL/QRL labels and scores are researcher-defined operational coding for comparison.",
        ha="left",
        va="center",
        fontsize=9.2,
        color="#4F575B",
    )

    fig.savefig(OUT_PNG, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(OUT_PNG)


if __name__ == "__main__":
    main()
