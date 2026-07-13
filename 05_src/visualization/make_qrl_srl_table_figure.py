from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "stage_layer_table_d" / "qrl_wise_srl_score_summary.csv"
OUTPUT = ROOT / "figures" / "01_quantum_vrp_evidence" / "qrl_srl_score_summary_table.png"


def wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(str(text), width=width, break_long_words=False))


def read_rows() -> list[dict[str, str]]:
    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def row_interpretation(row: dict[str, str]) -> str:
    qrl = row["qrl_evidence_level"]
    if qrl == "QRL2":
        return "Constrained routing appears at simulation stage, but not yet as hardware-aware workflow."
    if qrl == "QRL3":
        return "Hardware-aware evidence exists, but problem settings remain small or decomposed."
    if qrl == "QRL4":
        return "Higher SRL comes from Golden_5 resource pressure, not deployment or utility evidence."
    return row["interpretation"]


def draw_table(rows: list[dict[str, str]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(15.5, 7.2), dpi=220)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.patch.set_facecolor("#F7F7F2")
    ax.set_facecolor("#F7F7F2")

    ax.text(
        0.035,
        0.955,
        "QRL-wise SRL Scoring Summary",
        ha="left",
        va="top",
        fontsize=22,
        fontweight="bold",
        color="#1F2A33",
    )
    ax.text(
        0.035,
        0.905,
        "How quantum-readiness evidence maps to social-readiness evidence in the Figure 1 source CSV",
        ha="left",
        va="top",
        fontsize=10.5,
        color="#51606A",
    )

    left = 0.035
    right = 0.965
    top = 0.84
    header_h = 0.075
    row_h = 0.18
    col_widths = [0.12, 0.13, 0.11, 0.15, 0.27, 0.22]
    headers = [
        "QRL evidence",
        "Mean SRL score",
        "Evidence rows",
        "SRL composition",
        "Problem evidence",
        "Interpretation",
    ]

    total_w = right - left
    col_x = [left]
    for width in col_widths[:-1]:
        col_x.append(col_x[-1] + width * total_w)
    col_abs = [width * total_w for width in col_widths]

    header_color = "#243746"
    grid_color = "#D6D4CB"
    row_colors = ["#FFFFFF", "#F1F5F3", "#FFFFFF"]
    qrl_colors = {"QRL2": "#2E7D73", "QRL3": "#7B6FB0", "QRL4": "#B84A62"}

    ax.add_patch(Rectangle((left, top - header_h), total_w, header_h, facecolor=header_color, edgecolor=header_color))
    for i, header in enumerate(headers):
        ax.text(
            col_x[i] + 0.012,
            top - header_h / 2,
            header,
            ha="left",
            va="center",
            fontsize=10,
            color="white",
            fontweight="bold",
        )

    y = top - header_h
    for r_idx, row in enumerate(rows):
        y_next = y - row_h
        ax.add_patch(
            Rectangle((left, y_next), total_w, row_h, facecolor=row_colors[r_idx % len(row_colors)], edgecolor=grid_color, linewidth=0.8)
        )

        qrl = row["qrl_evidence_level"]
        chip_w = col_abs[0] - 0.028
        chip_h = 0.052
        chip_x = col_x[0] + 0.014
        chip_y = y_next + row_h / 2 - chip_h / 2
        ax.add_patch(Rectangle((chip_x, chip_y), chip_w, chip_h, facecolor=qrl_colors.get(qrl, "#6A7178"), edgecolor="none"))
        ax.text(chip_x + chip_w / 2, chip_y + chip_h / 2, qrl, ha="center", va="center", fontsize=11, color="white", fontweight="bold")

        values = [
            "",
            f"{row['qrl_mean_srl_score']} / 3",
            row["evidence_rows"],
            row["srl_composition"],
            wrap(row["problem_instance_summary"], 43),
            wrap(row_interpretation(row), 37),
        ]
        for c_idx, value in enumerate(values[1:], start=1):
            ax.text(
                col_x[c_idx] + 0.012,
                y_next + row_h / 2,
                value,
                ha="left",
                va="center",
                fontsize=9.3,
                color="#25323A",
                linespacing=1.25,
            )
        y = y_next

    for i in range(len(headers) + 1):
        x = left + sum(col_widths[:i]) * total_w
        ax.plot([x, x], [top - header_h - row_h * len(rows), top], color=grid_color, linewidth=0.8)
    ax.plot([left, right], [top, top], color=header_color, linewidth=1.0)
    ax.plot([left, right], [top - header_h - row_h * len(rows), top - header_h - row_h * len(rows)], color=grid_color, linewidth=1.0)

    note_y = 0.118
    ax.add_patch(Rectangle((left, note_y - 0.063), total_w, 0.096, facecolor="#ECE9DF", edgecolor="none"))
    ax.text(
        left + 0.018,
        note_y,
        "Scoring rule: SRL score is the mean of five social-readiness axes scored as low=0, medium=1, high=2, very_high=3.\n"
        "QRL is an evidence-stage label based on validation evidence; it is not an averaged performance score.",
        ha="left",
        va="center",
        fontsize=9.3,
        color="#3A444B",
        linespacing=1.35,
    )

    fig.savefig(OUTPUT, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    rows = read_rows()
    draw_table(rows)
    print(OUTPUT)


if __name__ == "__main__":
    main()
