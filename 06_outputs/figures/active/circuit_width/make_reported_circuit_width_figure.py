#!/usr/bin/env python3
"""Render the audited circuit-width data in full and slide-ready forms.

The slide renderer deliberately uses a fixed four-bar composition modeled on
the supplied reference layout. Record selection and rendering are separate:
the script reads the existing normalized CSV and never recalculates widths.
"""

from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "figures" / "circuit_width"
PLOT_DATA = OUT / "618_20260711_reported_circuit_width_plot_data.csv"
SOURCE_AUDIT = OUT / "619_20260711_reported_circuit_width_source_audit.csv"

REVISED_SLIDE_STEM = "reported_circuit_width_by_instance_slide_revised"
REVISED_FULL_STEM = "reported_circuit_width_by_instance_full_revised"
LEGACY_SLIDE_STEM = "reported_circuit_width_by_instance_slide"

GROUP_ORDER = [
    "Hardware execution",
    "Hardware-aware / hardware-targeted analysis",
    "Quantum / classical simulation",
    "Resource estimation",
]


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def load_plot_data() -> pd.DataFrame:
    """Load and validate the previously normalized, source-audited data."""
    if not PLOT_DATA.exists():
        raise FileNotFoundError(f"Normalized plot data not found: {PLOT_DATA}")
    if not SOURCE_AUDIT.exists():
        raise FileNotFoundError(f"Source audit not found: {SOURCE_AUDIT}")

    df = pd.read_csv(PLOT_DATA)
    required = {
        "study_id",
        "citation_number",
        "problem_instance_label",
        "problem_instance_scale",
        "problem_instance_unit",
        "formulation",
        "encoding",
        "reported_circuit_width",
        "width_type",
        "evidence_type",
        "evidence_group",
        "source_file",
        "source_location",
        "main_figure_inclusion",
        "comparison_key",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Normalized plot data are missing columns: {missing}")

    df["reported_circuit_width"] = pd.to_numeric(df["reported_circuit_width"], errors="coerce")
    included = as_bool(df["main_figure_inclusion"])
    if df.loc[included, "reported_circuit_width"].isna().any():
        raise ValueError("An included record has no numeric circuit width.")
    if (df.loc[included, "reported_circuit_width"] <= 0).any():
        raise ValueError("An included circuit width is not positive.")
    if df.loc[included, "citation_number"].isna().any():
        raise ValueError("An included record has no citation number.")
    if df.loc[included, "source_location"].fillna("").str.len().eq(0).any():
        raise ValueError("An included record has no traceable source location.")
    return df


def select_slide_records(df: pd.DataFrame) -> pd.DataFrame:
    """Select one exact same-instance encoding pair and two resource estimates.

    Selection is data-driven. The comparable pair must share a non-empty
    comparison key, differ in encoding, and not be a resource estimate. The
    two largest verified resource estimates supply the lower pair.
    """
    included = df[as_bool(df["main_figure_inclusion"])].copy()
    comparisons: list[pd.DataFrame] = []
    for key, group in included.groupby("comparison_key", dropna=False):
        if not isinstance(key, str) or not key.strip():
            continue
        if group["evidence_group"].eq("Resource estimation").any():
            continue
        if group["encoding"].nunique() < 2:
            continue
        # Prefer the two most different verified widths for the same instance.
        ordered = group.sort_values("reported_circuit_width")
        comparisons.append(ordered.iloc[[0, -1]].copy())
    if not comparisons:
        raise ValueError("No exact same-instance, different-encoding pair was found.")

    # Prefer the compact comparison, which best matches the sparse slide design.
    pair = min(comparisons, key=lambda g: float(g["reported_circuit_width"].max()))
    pair = pair.sort_values("reported_circuit_width")

    resources = included[included["evidence_group"] == "Resource estimation"].copy()
    resources = resources.sort_values("reported_circuit_width")
    if len(resources) < 2:
        raise ValueError("Fewer than two verified resource-estimation records are available.")
    resources = resources.tail(2).sort_values("reported_circuit_width")

    selected = pd.concat([pair, resources], ignore_index=True)
    if len(selected) != 4:
        raise AssertionError("The revised slide selection must contain exactly four records.")
    if selected.iloc[:2]["comparison_key"].nunique() != 1:
        raise AssertionError("The first two records are not an exact comparable-instance pair.")
    if selected.iloc[:2]["encoding"].nunique() != 2:
        raise AssertionError("The comparable records do not have different encodings.")
    if not selected.iloc[2:]["evidence_group"].eq("Resource estimation").all():
        raise AssertionError("The lower pair are not both resource estimates.")
    return selected


def short_encoding(value: object) -> str:
    text = str(value).strip()
    replacements = {
        "minimal encoding": "Minimal",
        "full encoding": "Full",
        "HOBO / direct encoding": "HOBO/direct",
        "QAOA / VQE ansätze": "QAOA/VQE",
    }
    return replacements.get(text, text)


def concise_label(row: pd.Series) -> str:
    instance = str(row["problem_instance_label"])
    if instance.startswith("Golden_5 CVRP"):
        instance = "Golden_5 CVRP"
    citation = int(float(row["citation_number"]))
    return f"{instance} ({short_encoding(row['encoding'])}) [{citation}]"


def choose_log_scale(values: pd.Series) -> bool:
    minimum = float(values.min())
    maximum = float(values.max())
    return maximum / minimum >= 100


def configure_fonts() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str, include_pdf: bool = True) -> None:
    """Save without automatic cropping so the controlled 16:9 layout remains fixed."""
    fig.savefig(OUT / f"{stem}.png", dpi=300, facecolor="#000000", bbox_inches=None)
    fig.savefig(OUT / f"{stem}.svg", facecolor="#000000", bbox_inches=None)
    if include_pdf:
        fig.savefig(OUT / f"{stem}.pdf", facecolor="#000000", bbox_inches=None)


def render_slide_ready_four_bar(selected: pd.DataFrame) -> None:
    """Render the strict four-bar, chart-only 16:9 reference composition."""
    configure_fonts()
    values = selected["reported_circuit_width"].astype(float)
    log_scale = choose_log_scale(values)
    minimum = float(values.min())
    maximum = float(values.max())

    fig = plt.figure(figsize=(16, 9), facecolor="#000000")
    # Explicit axes coordinates preserve the requested label/bar/right-margin ratios.
    ax = fig.add_axes([0.295, 0.105, 0.655, 0.82], facecolor="#000000")
    if log_scale:
        ax.set_xscale("log")
        x_origin = 1.0 if minimum >= 1 else minimum / 10.0
        x_limit = maximum * 1.15
    else:
        x_origin = 0.0
        x_limit = maximum * 1.15
    ax.set_xlim(x_origin, x_limit)
    ax.set_ylim(0.0, 5.25)

    # Fixed top-to-bottom positions match the reference hierarchy and spacing.
    y_positions = [3.90, 3.20, 1.86, 1.16]
    bar_height = 0.36
    colors = ["#008FA3", "#008FA3", "#B8B8B8", "#B8B8B8"]
    for (_, row), y, color in zip(selected.iterrows(), y_positions, colors):
        value = float(row["reported_circuit_width"])
        width = value - x_origin
        ax.barh(
            y,
            width,
            left=x_origin,
            height=bar_height,
            color=color,
            edgecolor="none",
            linewidth=0,
            align="center",
            zorder=3,
        )
        ax.annotate(
            concise_label(row),
            xy=(x_origin, y),
            xytext=(-22, 0),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=20,
            color="#666666",
            annotation_clip=False,
            zorder=5,
        )

    # Annotations are intentionally secondary and aligned just right of the y-axis.
    annotation_x = 1.34 if log_scale else maximum * 0.015
    ax.text(
        annotation_x,
        4.58,
        "Similar problem-instance scales may produce different circuit widths\n"
        "depending on formulation and encoding.",
        ha="left",
        va="center",
        fontsize=19,
        linespacing=1.18,
        color="#5C5C5C",
        zorder=5,
    )
    ax.text(
        annotation_x,
        2.50,
        "Large reported circuit widths in this group may represent resource estimates.",
        ha="left",
        va="center",
        fontsize=19,
        color="#5C5C5C",
        zorder=5,
    )

    # Minimal arrow axes. Standard spines, ticks, labels, and grids remain hidden.
    axis_color = "#555555"
    horizontal_y = 0.58
    arrow_end_x = maximum * 1.12
    ax.annotate(
        "",
        xy=(x_origin, 4.96),
        xytext=(x_origin, horizontal_y),
        arrowprops=dict(arrowstyle="-|>", color=axis_color, lw=1.35, mutation_scale=13),
        annotation_clip=False,
        zorder=2,
    )
    ax.annotate(
        "",
        xy=(arrow_end_x, horizontal_y),
        xytext=(x_origin, horizontal_y),
        arrowprops=dict(arrowstyle="-|>", color=axis_color, lw=1.35, mutation_scale=13),
        annotation_clip=False,
        zorder=2,
    )
    ax.text(
        0.50,
        0.018,
        "Reported circuit width",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=17,
        color="#5C5C5C",
    )

    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    save_figure(fig, REVISED_SLIDE_STEM, include_pdf=True)
    plt.close(fig)


def full_plot_label(row: pd.Series) -> str:
    citation = int(float(row["citation_number"]))
    return f"{row['problem_instance_label']} [{citation}]\n{row['formulation']} / {row['encoding']}"


def comma_formatter(value: float, _position: object = None) -> str:
    return f"{int(round(value)):,}" if value > 0 else ""


def render_full_revised(df: pd.DataFrame) -> None:
    """Render all eligible records separately from the sparse slide asset."""
    configure_fonts()
    full = df[as_bool(df["main_figure_inclusion"])].copy()
    full["group_rank"] = full["evidence_group"].map({g: i for i, g in enumerate(GROUP_ORDER)})
    full = full.sort_values(["group_rank", "reported_circuit_width", "study_id"])
    values = full["reported_circuit_width"].astype(float)
    log_scale = choose_log_scale(values)

    y_positions: list[float] = []
    group_spans: dict[str, tuple[float, float]] = {}
    cursor = 0.0
    for group in GROUP_ORDER:
        indices = full.index[full["evidence_group"] == group].tolist()
        if not indices:
            continue
        start = cursor
        for idx in indices:
            full.loc[idx, "y"] = cursor
            y_positions.append(cursor)
            cursor += 1.0
        group_spans[group] = (start - 0.46, cursor - 0.54)
        cursor += 0.85

    fig_height = max(12.0, 0.55 * len(full) + 4.8)
    fig, ax = plt.subplots(figsize=(17, fig_height), facecolor="#000000")
    ax.set_facecolor("#000000")
    fig.subplots_adjust(left=0.34, right=0.96, top=0.90, bottom=0.10)

    group_colors = {
        "Hardware execution": "#008FA3",
        "Hardware-aware / hardware-targeted analysis": "#2A9FAC",
        "Quantum / classical simulation": "#4A94A0",
        "Resource estimation": "#B8B8B8",
    }
    hatches = {
        "Hardware execution": "",
        "Hardware-aware / hardware-targeted analysis": "//",
        "Quantum / classical simulation": "..",
        "Resource estimation": "xx",
    }

    minimum = float(values.min())
    maximum = float(values.max())
    x_origin = 1.0 if log_scale else 0.0
    for _, row in full.iterrows():
        group = row["evidence_group"]
        value = float(row["reported_circuit_width"])
        ax.barh(
            float(row["y"]),
            value - x_origin,
            left=x_origin,
            height=0.62,
            color=group_colors[group],
            hatch=hatches[group],
            edgecolor="#D0D0D0" if hatches[group] else "none",
            linewidth=0.5 if hatches[group] else 0,
        )
        ax.text(value * 1.10 if log_scale else value + maximum * 0.01, float(row["y"]), f"{int(value):,}",
                ha="left", va="center", fontsize=9, color="#D5D5D5", fontweight="bold")

    for group, (y0, y1) in group_spans.items():
        ax.axhspan(y0, y1, color=group_colors[group], alpha=0.055, lw=0, zorder=0)
        ax.text(0.002, y0 - 0.26, group.upper(), transform=ax.get_yaxis_transform(),
                ha="left", va="bottom", fontsize=9, color=group_colors[group], fontweight="bold")

    if log_scale:
        ax.set_xscale("log")
        ax.set_xlim(1, maximum * 4.0)
        ax.xaxis.set_major_locator(LogLocator(base=10))
        ax.xaxis.set_major_formatter(FuncFormatter(comma_formatter))
    else:
        ax.set_xlim(0, maximum * 1.20)
        ax.xaxis.set_major_formatter(FuncFormatter(comma_formatter))
    ax.set_ylim(float(full["y"].max()) + 0.70, -1.25)
    ax.set_yticks(full["y"].tolist())
    ax.set_yticklabels([full_plot_label(row) for _, row in full.iterrows()], fontsize=10, color="#B0B0B0")
    ax.tick_params(axis="y", length=0, pad=12)
    ax.tick_params(axis="x", colors="#777777", labelsize=9)
    ax.set_xlabel("Reported circuit width / qubits" + (" (log scale)" if log_scale else ""),
                  fontsize=12, color="#888888", labelpad=12)
    ax.grid(False)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#555555")
    fig.text(0.035, 0.955, "Reported Circuit Width Across Transport Problem Instances",
             ha="left", va="top", fontsize=23, color="#EAEAEA", fontweight="bold")
    fig.text(0.035, 0.920, "Full audited dataset, separated by evidence level",
             ha="left", va="top", fontsize=12, color="#777777")

    save_figure(fig, REVISED_FULL_STEM, include_pdf=True)
    plt.close(fig)


def validate_selected_records(selected: pd.DataFrame) -> None:
    expected_order = ["Hardware execution", "Hardware execution", "Resource estimation", "Resource estimation"]
    if selected["evidence_group"].tolist() != expected_order:
        raise AssertionError(f"Unexpected evidence order: {selected['evidence_group'].tolist()}")
    if selected["reported_circuit_width"].tolist() != sorted(selected["reported_circuit_width"].tolist()):
        raise AssertionError("The four selected widths are not in the intended top-to-bottom order.")
    if selected["citation_number"].isna().any():
        raise AssertionError("A selected record is missing its citation number.")
    if selected["source_location"].fillna("").str.len().eq(0).any():
        raise AssertionError("A selected record is missing its source location.")


def overwrite_legacy_slide() -> None:
    """Overwrite legacy PNG/SVG only after revised files have been reviewed."""
    for suffix in ["png", "svg"]:
        source = OUT / f"{REVISED_SLIDE_STEM}.{suffix}"
        if not source.exists() or source.stat().st_size == 0:
            raise FileNotFoundError(f"Validated revised asset is missing: {source}")
        shutil.copy2(source, OUT / f"{LEGACY_SLIDE_STEM}.{suffix}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite-legacy-slide",
        action="store_true",
        help="Copy the revised PNG/SVG over the previous slide assets after visual validation.",
    )
    parser.add_argument("--skip-full", action="store_true", help="Skip regeneration of the separate full-data figure.")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    df = load_plot_data()
    selected = select_slide_records(df)
    validate_selected_records(selected)
    render_slide_ready_four_bar(selected)
    if not args.skip_full:
        render_full_revised(df)
    if args.overwrite_legacy_slide:
        overwrite_legacy_slide()

    scale = "logarithmic" if choose_log_scale(selected["reported_circuit_width"]) else "linear"
    print("Selected revised-slide records:")
    for _, row in selected.iterrows():
        print(
            f"  {concise_label(row)} | {int(row['reported_circuit_width']):,} | "
            f"{row['evidence_type']}"
        )
    print(f"Axis scale: {scale}")


if __name__ == "__main__":
    main()
