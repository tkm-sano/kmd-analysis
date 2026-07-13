#!/usr/bin/env python3
"""Render research tables and figures from canonical EVRP analysis CSVs.

This script performs no scenario generation or constraint calculation.  It
reads validated CSV outputs from ``run_tokyo_synthetic_evrp_analysis.py`` and
produces PNG/SVG assets plus one source-data CSV per figure.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

SRC_ROOT = Path(__file__).resolve().parents[1]
for module_dir in (SRC_ROOT / "visualization", SRC_ROOT / "constraint_evaluation"):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from table_rendering_utils import render_table_as_png, render_table_as_svg
from validation_utils import (
    find_repository_root,
    generate_output_manifest,
    read_csv_checked,
    write_csv_atomic,
)


RESEARCH_NOTE = (
    "本表はsynthetic customer configurationおよびroute proxyに基づく。東京都の実配送における"
    "観測失敗率を示すものではない。各数値は車両性能、顧客需要、配送可能時間、充電条件、"
    "およびルート生成方法の仮定に依存する。"
)


def parse_args() -> argparse.Namespace:
    """Parse renderer arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--reproduce",
        action="store_true",
        help="Clear and regenerate canonical table-image/figure directories.",
    )
    return parser.parse_args()


def configure_font() -> str:
    """Configure a locally installed Japanese-capable font when available."""

    from matplotlib import font_manager

    preferred = [
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Yu Gothic",
        "Noto Sans CJK JP",
        "IPAexGothic",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((name for name in preferred if name in installed), "DejaVu Sans")
    plt.rcParams.update(
        {
            "font.family": selected,
            "axes.unicode_minus": False,
            "svg.fonttype": "none",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    return selected


class Renderer:
    """CSV-driven renderer that tracks every generated artifact."""

    def __init__(self, root: Path, reproduce: bool) -> None:
        self.root = root
        self.outputs = root / "outputs"
        self.figure_png = self.outputs / "06_outputs/figures/active/png"
        self.figure_svg = self.outputs / "06_outputs/figures/active/svg"
        self.figure_source = self.outputs / "06_outputs/figures/active/source_data"
        self.table_png = self.outputs / "tables/png"
        self.table_svg = self.outputs / "tables/svg"
        self.table_csv = self.outputs / "tables/csv"
        self.validation = self.outputs / "validation"
        self.generated: list[Path] = []
        if not reproduce:
            raise RuntimeError(
                "Refusing to reuse or overwrite rendered assets without --reproduce."
            )
        for directory in [
            self.figure_png,
            self.figure_svg,
            self.figure_source,
            self.table_png,
            self.table_svg,
        ]:
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)
        self.validation.mkdir(parents=True, exist_ok=True)

    def read(self, relative: str, required: Iterable[str] | None = None) -> pd.DataFrame:
        """Read a non-empty canonical CSV with optional schema validation."""

        return read_csv_checked(
            self.root / relative,
            required_columns=list(required) if required else None,
            require_nonempty=True,
        )

    def save_figure(self, figure: plt.Figure, stem: str, source_data: pd.DataFrame) -> None:
        """Write a source CSV and matching high-resolution PNG/editable SVG."""

        source_path = self.figure_source / f"{stem}.csv"
        png_path = self.figure_png / f"{stem}.png"
        svg_path = self.figure_svg / f"{stem}.svg"
        write_csv_atomic(source_data, source_path)
        figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
        figure.savefig(svg_path, bbox_inches="tight", facecolor="white")
        plt.close(figure)
        self.generated.extend([source_path, png_path, svg_path])


def _rate_label(value: object) -> str:
    if pd.isna(value):
        return "Not evaluated"
    return f"{float(value) * 100:.1f}%"


def _render_tables(renderer: Renderer) -> None:
    table_specs = [
        (
            "table_01_scenario_design",
            "What conditions were compared?",
            [
                "scenario_id",
                "customer_count",
                "vehicle_count",
                "customers_per_vehicle",
                "independent_seed_count",
                "conditional_case_count",
                "charger_condition",
                "usable_range_km",
                "payload_capacity_kg",
                "operating_time_limit_min",
                "assumed_speed_kmh",
                "route_generation_method",
            ],
            8.0,
        ),
        (
            "table_02_constraint_unmet_variability",
            "Which constraints became binding, and how sensitive were they to customer locations?",
            [
                "constraint_name",
                "route_weighted_unmet_rate",
                "case_weighted_unmet_rate",
                "confidence_interval",
                "standard_deviation",
                "minimum",
                "maximum",
                "spatial_sensitivity",
                "evidence_status",
            ],
            9.0,
        ),
        (
            "table_03_quantum_vrp_gap",
            "Which operationally important requirements remain insufficiently covered by quantum VRP research?",
            [
                "evaluation_item",
                "synthetic_evrp_requirement",
                "analysis_importance",
                "quantum_vrp_coverage",
                "evidence_level",
                "evidence_gap",
                "gap_basis",
            ],
            7.2,
        ),
        (
            "table_04_integrated_research_summary",
            "Which constraints should be prioritized in future quantum-oriented EVRP research?",
            [
                "constraint_or_requirement",
                "route_weighted_unmet_rate",
                "spatial_variability",
                "parameter_sensitivity",
                "evidence_quality",
                "quantum_vrp_coverage",
                "evidence_gap",
                "research_priority",
                "interpretation",
            ],
            7.5,
        ),
        (
            "table_05_constraint_interpretation_full",
            "How should each numerical result be interpreted?",
            [
                "display_name_ja",
                "observed_value",
                "numerator_definition",
                "what_high_value_means",
                "main_assumptions",
                "valid_interpretation",
                "invalid_interpretation",
            ],
            7.5,
        ),
        (
            "table_05_constraint_interpretation_slide",
            "How should each numerical result be presented concisely?",
            ["constraint", "result", "what_this_result_shows", "main_caution"],
            9.0,
        ),
    ]
    for stem, question, columns, font_size in table_specs:
        raw = renderer.read(f"06_outputs/tables/csv/{stem}.csv")
        display = raw[columns].copy()
        if stem == "table_01_scenario_design":
            display["route_generation_method"] = "KMeans + nearest-neighbor proxy"
            display = display.rename(
                columns={
                    "scenario_id": "Scenario ID",
                    "customer_count": "Customers",
                    "vehicle_count": "Vehicles",
                    "customers_per_vehicle": "Customers/vehicle",
                    "independent_seed_count": "Seed count",
                    "conditional_case_count": "Case count",
                    "charger_condition": "Charger condition",
                    "usable_range_km": "Usable range (km)",
                    "payload_capacity_kg": "Payload (kg)",
                    "operating_time_limit_min": "Time limit (min)",
                    "assumed_speed_kmh": "Speed (km/h)",
                    "route_generation_method": "Route proxy",
                }
            )
            columns = list(display.columns)
        elif stem == "table_03_quantum_vrp_gap":
            display["quantum_vrp_coverage"] = display["quantum_vrp_coverage"].replace(
                {
                    "Reported in at least one reviewed study": "Reported in reviewed set",
                    "Not reported in the reviewed evidence set": "Not reported in reviewed set",
                    "Qualitative comparison reported; normalized metric Not reported": "Qualitative; normalized metric not reported",
                }
            )
            display["evidence_level"] = display["evidence_level"].map(
                lambda text: (
                    "Simulator + hardware"
                    if "Quantum simulator and quantum hardware" in str(text)
                    else "Classical emulation"
                    if "Classical emulation" in str(text)
                    else "Not reported"
                    if "Not reported" in str(text)
                    else str(text)
                )
            )
        elif stem == "table_04_integrated_research_summary":
            display["research_priority"] = display["research_priority"].replace(
                {"Evidence-dependent": "Evidence-\ndependent"}
            )
            display["quantum_vrp_coverage"] = display["quantum_vrp_coverage"].replace(
                {
                    "Reported in at least one reviewed study": "Reported in reviewed set",
                    "Not reported in the reviewed evidence set": "Not reported in reviewed set",
                }
            )
        for column in display.columns:
            if "rate" in column or column in {"observed_value", "result", "standard_deviation", "minimum", "maximum"}:
                display[column] = display[column].map(
                    lambda value: _rate_label(value)
                    if isinstance(value, (float, int, np.floating, np.integer))
                    or (isinstance(value, str) and value.replace(".", "", 1).isdigit())
                    else value
                )
        png = renderer.table_png / f"{stem}.png"
        svg = renderer.table_svg / f"{stem}.svg"
        render_table_as_png(
            display,
            png,
            title=question,
            note=RESEARCH_NOTE,
            emphasized_columns=[columns[0]],
            landscape=True,
            dpi=300,
            font_size=font_size,
        )
        render_table_as_svg(
            display,
            svg,
            title=question,
            note=RESEARCH_NOTE,
            emphasized_columns=[columns[0]],
            landscape=True,
            font_size=font_size,
        )
        renderer.generated.extend([png, svg])


def _figure_pipeline(renderer: Renderer) -> None:
    labels = [
        "Tokyo public-data proxies",
        "Synthetic customer configuration",
        "Route proxy",
        "Constraint evaluation",
        "Spatial & parameter sensitivity",
        "Quantum-VRP evidence gap",
        "Research priorities",
    ]
    source = pd.DataFrame(
        {
            "order": range(1, len(labels) + 1),
            "node": labels,
            "interpretation": [
                "Population mesh, logistics-facility proxies, OCM candidates, vehicle specification",
                "Not observed orders",
                "KMeans plus nearest-neighbor; not an EVRP optimum",
                "Model-conditional unmet rates",
                "Paired seed bootstrap and OAT assumptions",
                "Reviewed local evidence registry",
                "Ordinal, evidence-aware prioritization",
            ],
        }
    )
    fig, ax = plt.subplots(figsize=(16, 2.8))
    ax.axis("off")
    colors = plt.cm.Blues(np.linspace(0.35, 0.85, len(labels)))
    for index, row in source.iterrows():
        x = index / (len(labels) - 1)
        ax.text(
            x,
            0.56,
            row.node.replace(" ", "\n"),
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.6", facecolor=colors[index], edgecolor="#1f4e79"),
        )
        if index < len(labels) - 1:
            ax.annotate(
                "",
                xy=((index + 0.78) / (len(labels) - 1), 0.56),
                xytext=((index + 0.22) / (len(labels) - 1), 0.56),
                xycoords=ax.transAxes,
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#3b4c5a"),
            )
    ax.set_title("Data-to-analysis pipeline", fontsize=16, weight="bold", pad=18)
    ax.text(
        0.5,
        0.02,
        "Scope ends at constraint/gap interpretation; actual charging behavior and electricity demand are not evaluated.",
        ha="center",
        transform=ax.transAxes,
        fontsize=10,
        color="#7a1f1f",
    )
    renderer.save_figure(fig, "figure_01_data_to_analysis_pipeline", source)


def _figure_scenario_matrix(renderer: Renderer, configurations: pd.DataFrame) -> None:
    source = configurations.drop_duplicates(["customer_count", "vehicle_count"])[
        ["customer_count", "vehicle_count", "customers_per_vehicle"]
    ].sort_values(["customer_count", "vehicle_count"])
    matrix = source.pivot(index="customer_count", columns="vehicle_count", values="customers_per_vehicle")
    fig, ax = plt.subplots(figsize=(8.5, 6))
    image = ax.imshow(matrix.values, cmap="YlGnBu", aspect="auto")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix.iloc[i, j]:.1f}", ha="center", va="center", fontsize=13)
    ax.set_xticks(range(matrix.shape[1]), matrix.columns.astype(str))
    ax.set_yticks(range(matrix.shape[0]), matrix.index.astype(str))
    ax.set_xlabel("Vehicle count")
    ax.set_ylabel("Customer count")
    ax.set_title("Scenario design matrix: customers per vehicle\n(each cell evaluated under 3 charger conditions)")
    fig.colorbar(image, ax=ax, label="Customers per vehicle")
    renderer.save_figure(fig, "figure_02_scenario_design_matrix", source)


def _figure_customer_map(renderer: Renderer, customers: pd.DataFrame) -> None:
    source = customers[
        customers["customer_configuration_id"].eq("C050_S001")
    ][["customer_id", "latitude", "longitude", "demand_kg", "mesh_population"]].copy()
    fig, ax = plt.subplots(figsize=(9, 7))
    scatter = ax.scatter(
        source["longitude"],
        source["latitude"],
        c=source["demand_kg"],
        s=30 + np.sqrt(source["mesh_population"].clip(lower=0)),
        cmap="viridis",
        alpha=0.8,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Tokyo synthetic customer map: C=50, seed=1\nPopulation-weighted mesh centroids; not observed delivery stops")
    fig.colorbar(scatter, ax=ax, label="Synthetic demand (kg)")
    renderer.save_figure(fig, "figure_03_tokyo_synthetic_customer_map", source)


def _figure_route_map(renderer: Renderer, edges: pd.DataFrame) -> None:
    source = edges[
        edges["customer_count"].eq(50)
        & edges["vehicle_count"].eq(3)
        & edges["seed"].eq(1)
    ].copy()
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = plt.cm.Set2(np.linspace(0, 1, source["base_route_proxy_id"].nunique()))
    for color, (route_id, group) in zip(colors, source.groupby("base_route_proxy_id")):
        ordered = group.sort_values("proxy_edge_order")
        for row in ordered.itertuples(index=False):
            ax.plot(
                [row.from_longitude, row.to_longitude],
                [row.from_latitude, row.to_latitude],
                linestyle="--",
                linewidth=1.4,
                color=color,
                alpha=0.85,
            )
        ax.scatter(
            ordered["to_longitude"], ordered["to_latitude"], s=18, color=color, label=route_id
        )
    depot = source[source["from_node_type"].eq("depot_proxy")].iloc[0]
    ax.scatter(depot.from_longitude, depot.from_latitude, marker="s", s=110, color="black", label="Depot proxy")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Route proxy map: C=50, V=3, seed=1")
    ax.legend(fontsize=7, loc="best")
    ax.text(
        0.01,
        0.03,
        "Proxy edge showing visit order; not an actual road path.",
        transform=ax.transAxes,
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.9, edgecolor="#888888"),
    )
    renderer.save_figure(fig, "figure_04_route_proxy_map", source)


def _figure_distance_distribution(renderer: Renderer, routes: pd.DataFrame) -> None:
    source = routes.drop_duplicates("base_route_proxy_id")[
        ["base_route_proxy_id", "customer_count", "vehicle_count", "seed", "route_proxy_distance_km"]
    ].copy()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(source["route_proxy_distance_km"], bins=35, color="#377eb8", alpha=0.85, edgecolor="white")
    ax.axvline(source["route_proxy_distance_km"].median(), color="#e41a1c", linestyle="--", label="Median")
    ax.set_xlabel("Route-proxy distance (km)")
    ax.set_ylabel("Route count")
    ax.set_title("Route distance distribution\nDistance is a continuous outcome, not a separate unmet constraint")
    ax.legend()
    renderer.save_figure(fig, "figure_05_route_distance_distribution", source)


def _figure_constraint_rates(renderer: Renderer, summary: pd.DataFrame) -> None:
    source = summary[
        ["constraint_name", "route_weighted_unmet_rate", "evaluated_route_count", "evidence_status"]
    ].copy()
    plotted = source[source["route_weighted_unmet_rate"].notna()].copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(plotted["constraint_name"], plotted["route_weighted_unmet_rate"] * 100, color="#d95f02")
    for bar, value in zip(bars, plotted["route_weighted_unmet_rate"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{value * 100:.1f}%", va="center")
    ax.set_xlim(0, max(100, plotted["route_weighted_unmet_rate"].max() * 115))
    ax.set_xlabel("Route-weighted unmet rate (%)")
    ax.set_title("Constraint unmet rates under synthetic route-proxy assumptions\nSOC feasibility: Not evaluated")
    renderer.save_figure(fig, "figure_06_constraint_unmet_rate", source)


def _figure_seed_variability(renderer: Renderer, case_rates: pd.DataFrame) -> None:
    source = case_rates[case_rates["case_unmet_rate"].notna()][
        ["scenario_id", "seed", "constraint_name", "case_unmet_rate"]
    ].copy()
    constraints = list(source["constraint_name"].drop_duplicates())
    data = [source.loc[source["constraint_name"].eq(name), "case_unmet_rate"] * 100 for name in constraints]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.boxplot(data, tick_labels=[name.replace(" ", "\n") for name in constraints], showfliers=False)
    ax.set_ylabel("Case-level unmet rate (%)")
    ax.set_title("Seed and conditional-case variability\nCases are paired by seed; they are not independent trials")
    ax.tick_params(axis="x", labelsize=8)
    renderer.save_figure(fig, "figure_07_seed_variability", source)


def _figure_confidence_intervals(renderer: Renderer, scenario_summary: pd.DataFrame) -> None:
    source = scenario_summary[
        scenario_summary["charger_condition"].eq("balanced")
        & scenario_summary["constraint_name"].isin(["Operating-time limit", "Range feasibility"])
    ].copy()
    source["label"] = source.apply(
        lambda row: f"C{int(row.customer_count)} V{int(row.vehicle_count)} | {row.constraint_name}", axis=1
    )
    source = source.sort_values(["constraint_name", "customer_count", "vehicle_count"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 9))
    y = np.arange(len(source))
    means = source["route_weighted_unmet_rate"].to_numpy() * 100
    lower = (source["route_weighted_unmet_rate"] - source["confidence_interval_lower"]).to_numpy() * 100
    upper = (source["confidence_interval_upper"] - source["route_weighted_unmet_rate"]).to_numpy() * 100
    colors = np.where(source["constraint_name"].eq("Range feasibility"), "#7570b3", "#1b9e77")
    for position, (mean, low_error, high_error, color) in enumerate(
        zip(means, lower, upper, colors)
    ):
        ax.errorbar(
            mean,
            position,
            xerr=np.array([[low_error], [high_error]]),
            fmt="o",
            color=color,
            ecolor=color,
            capsize=3,
            markersize=5,
        )
    ax.set_yticks(y, source["label"])
    ax.set_xlabel("Route-weighted unmet rate with seed-cluster bootstrap 95% CI (%)")
    ax.set_title("Scenario-specific confidence intervals: balanced charger condition")
    ax.set_xlim(-5, 105)
    ax.grid(axis="x", alpha=0.25)
    renderer.save_figure(fig, "figure_08_scenario_confidence_intervals", source)


def _figure_sensitivity_heatmap(renderer: Renderer, sensitivity: pd.DataFrame) -> None:
    source = sensitivity[
        ["parameter", "constraint_name", "level", "unmet_rate_change_from_base"]
    ].copy()
    maximum = (
        source.assign(abs_change=source["unmet_rate_change_from_base"].abs())
        .groupby(["parameter", "constraint_name"])["abs_change"]
        .max()
        .reset_index()
    )
    matrix = maximum.pivot(index="parameter", columns="constraint_name", values="abs_change").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 9))
    image = ax.imshow(matrix.values * 100, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), [name.replace(" ", "\n") for name in matrix.columns], rotation=35, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title("Parameter sensitivity heatmap\nMaximum absolute change from each parameter's base level")
    fig.colorbar(image, ax=ax, label="Absolute unmet-rate change (percentage points)")
    renderer.save_figure(fig, "figure_09_parameter_sensitivity_heatmap", maximum)


def _figure_tornado(renderer: Renderer, sensitivity: pd.DataFrame) -> None:
    records: list[dict[str, object]] = []
    for parameter, group in sensitivity.groupby("parameter"):
        constraint_impacts = (
            group.assign(abs_change=group["unmet_rate_change_from_base"].abs())
            .groupby("constraint_name")["abs_change"]
            .max()
        )
        if constraint_impacts.dropna().empty:
            continue
        constraint = str(constraint_impacts.idxmax())
        selected = group[group["constraint_name"].eq(constraint)].set_index("level")
        records.append(
            {
                "parameter": parameter,
                "most_responsive_constraint": constraint,
                "low_change": float(selected.loc["low", "unmet_rate_change_from_base"]),
                "high_change": float(selected.loc["high", "unmet_rate_change_from_base"]),
                "maximum_absolute_change": float(constraint_impacts.max()),
            }
        )
    source = pd.DataFrame(records).sort_values("maximum_absolute_change")
    fig, ax = plt.subplots(figsize=(10, 8))
    y = np.arange(len(source))
    ax.barh(y, source["low_change"] * 100, color="#1f78b4", alpha=0.8, label="Low vs base")
    ax.barh(y, source["high_change"] * 100, color="#e31a1c", alpha=0.75, label="High vs base")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y, source["parameter"])
    ax.set_xlabel("Unmet-rate change for the most responsive constraint (percentage points)")
    ax.set_title("Exploratory tornado chart: one-at-a-time parameter response")
    ax.legend()
    renderer.save_figure(fig, "figure_10_tornado_chart", source)


def _figure_charger_map(renderer: Renderer, chargers: pd.DataFrame) -> None:
    priority = {"conservative": 0, "balanced": 1, "broad": 2}
    source = chargers.copy()
    source["condition_priority"] = source["charger_condition"].map(priority)
    source = source.sort_values("condition_priority").drop_duplicates("charger_candidate_id")
    fig, ax = plt.subplots(figsize=(9, 7))
    for condition, group in source.groupby("charger_condition"):
        ax.scatter(group["longitude"], group["latitude"], s=36, alpha=0.75, label=f"Most restrictive inclusion: {condition}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Charger candidate distribution\nCandidate registration does not establish actual availability")
    ax.legend(fontsize=8)
    renderer.save_figure(fig, "figure_11_charger_candidate_distribution", source)


def _figure_nearest_charger(renderer: Renderer, routes: pd.DataFrame) -> None:
    source = routes[
        ["scenario_route_proxy_id", "charger_condition", "nearest_charger_distance_km"]
    ].copy()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for condition, group in source.groupby("charger_condition"):
        ax.hist(group["nearest_charger_distance_km"], bins=30, alpha=0.45, label=condition)
    ax.set_xlabel("Nearest retained charger-candidate distance (km, road-adjusted proxy)")
    ax.set_ylabel("Route-condition count")
    ax.set_title("Nearest charger-candidate distance distribution")
    ax.legend()
    renderer.save_figure(fig, "figure_12_nearest_charger_distance_distribution", source)


def _scenario_feasibility_heatmaps(
    renderer: Renderer,
    routes: pd.DataFrame,
    column: str,
    evaluated_column: str | None,
    stem: str,
    title: str,
) -> None:
    frame = routes.copy()
    if evaluated_column:
        frame = frame[frame[evaluated_column].fillna(False).astype(bool)]
    source = (
        frame.groupby(["customer_count", "vehicle_count", "charger_condition"], as_index=False)[column]
        .mean()
        .rename(columns={column: "feasible_share"})
    )
    conditions = ["conservative", "balanced", "broad"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)
    image = None
    for ax, condition in zip(axes, conditions):
        selected = source[source["charger_condition"].eq(condition)]
        matrix = selected.pivot(index="customer_count", columns="vehicle_count", values="feasible_share").sort_index()
        matrix = matrix.astype(float)
        image = ax.imshow(matrix.to_numpy(dtype=float) * 100, vmin=0, vmax=100, cmap="YlGn", aspect="auto")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix.iloc[i, j] * 100:.0f}%", ha="center", va="center")
        ax.set_xticks(range(matrix.shape[1]), matrix.columns.astype(str))
        ax.set_yticks(range(matrix.shape[0]), matrix.index.astype(str))
        ax.set_xlabel("Vehicles")
        ax.set_title(condition)
    axes[0].set_ylabel("Customers")
    fig.suptitle(title)
    if image is not None:
        fig.colorbar(image, ax=axes.ravel().tolist(), label="Feasible share (%)", shrink=0.8)
    renderer.save_figure(fig, stem, source)


def _figure_quantum_landscape(renderer: Renderer, evidence: pd.DataFrame) -> None:
    coverage = [
        "customer_scale_coverage",
        "multiple_vehicle_coverage",
        "capacity_coverage",
        "time_window_coverage",
        "battery_soc_coverage",
        "charging_station_coverage",
        "charging_duration_coverage",
        "multi_depot_coverage",
        "heterogeneous_vehicle_coverage",
        "dynamic_demand_coverage",
        "traffic_coverage",
        "driver_hours_coverage",
    ]
    long = evidence[["reference_id", *coverage]].melt(
        id_vars="reference_id", var_name="requirement", value_name="reported_text"
    )
    long["coverage_indicator"] = (~long["reported_text"].astype(str).str.lower().str.startswith("not reported")).astype(int)
    matrix = long.pivot(index="reference_id", columns="requirement", values="coverage_indicator")
    fig, ax = plt.subplots(figsize=(14, 4.8))
    image = ax.imshow(matrix.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), [name.replace("_coverage", "").replace("_", "\n") for name in matrix.columns], rotation=35, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title("Quantum VRP evidence landscape\nCoverage recorded only when confirmed in the local extraction note")
    cbar = fig.colorbar(image, ax=ax, ticks=[0, 1])
    cbar.ax.set_yticklabels(["Not reported", "Reported/limited"])
    renderer.save_figure(fig, "figure_15_quantum_vrp_evidence_landscape", long)


def _figure_priority_matrix(renderer: Renderer, integrated: pd.DataFrame) -> None:
    source = integrated.copy()
    gap_map = {"Not assessable": 0, "Low": 1, "Medium": 2, "High": 3}
    sensitivity_map = {"Not assessable": 0.02, "Low": 0.04, "Medium": 0.09, "High": 0.16}
    plotted = source[source["route_weighted_unmet_rate"].notna()].copy()
    plotted["gap_axis"] = plotted["evidence_gap"].map(gap_map).fillna(0)
    plotted["size"] = plotted["parameter_sensitivity"].map(sensitivity_map).fillna(0.02) * 1800
    colors = {"High": "#d73027", "Medium": "#fc8d59", "Evidence-dependent": "#91bfdb"}
    fig, ax = plt.subplots(figsize=(10, 7))
    for priority, group in plotted.groupby("research_priority"):
        ax.scatter(
            group["gap_axis"],
            group["route_weighted_unmet_rate"] * 100,
            s=group["size"],
            alpha=0.75,
            color=colors.get(priority, "#888888"),
            label=priority,
            edgecolor="white",
        )
        for row in group.itertuples(index=False):
            ax.annotate(row.constraint_or_requirement, (row.gap_axis, row.route_weighted_unmet_rate * 100), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlim(-0.2, 3.75)
    ax.set_xticks(list(gap_map.values()), list(gap_map.keys()))
    ax.set_ylabel("Route-weighted unmet rate (%)")
    ax.set_xlabel("Evidence gap (ordinal; not a metric scale)")
    ax.set_title("Integrated research-priority matrix\nMarker size reflects ordinal parameter sensitivity")
    ax.legend(title="Research priority")
    ax.grid(alpha=0.2)
    renderer.save_figure(fig, "figure_16_integrated_research_priority_matrix", source)


def _figure_limitations(renderer: Renderer, limitations: pd.DataFrame) -> None:
    source = limitations.copy()
    import textwrap

    fig, axes = plt.subplots(1, 2, figsize=(16, 11))
    fig.suptitle("Assumptions and limitations", fontsize=18, weight="bold", y=0.98)
    midpoint = int(np.ceil(len(source) / 2))
    for ax, subset in zip(axes, [source.iloc[:midpoint], source.iloc[midpoint:]]):
        ax.axis("off")
        y_positions = np.linspace(0.93, 0.08, len(subset))
        for y, row in zip(y_positions, subset.itertuples(index=False)):
            wrapped = textwrap.fill(f"{row.topic}: {row.limitation}", width=68)
            ax.text(
                0.02,
                y,
                wrapped,
                transform=ax.transAxes,
                fontsize=8.8,
                va="center",
                ha="left",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#f5f8fa", edgecolor="#ccd6dd"),
            )
    fig.text(
        0.5,
        0.015,
        "Unmet rates are conditional outputs of synthetic configurations and route proxies, not observed Tokyo delivery failure rates.",
        ha="center",
        fontsize=11,
        color="#7a1f1f",
        weight="bold",
    )
    fig.subplots_adjust(top=0.93, bottom=0.06, wspace=0.06)
    renderer.save_figure(fig, "figure_17_assumptions_and_limitations", source)


def main() -> None:
    """Render all requested tables and figures from existing analysis CSVs."""

    args = parse_args()
    root = args.root.expanduser().resolve() if args.root else find_repository_root(Path.cwd())
    font = configure_font()
    renderer = Renderer(root, args.reproduce)

    configurations = renderer.read(
        "03_data/processed/scenario/446_20260711_scenario_configurations.csv",
        ["scenario_id", "customer_count", "vehicle_count", "charger_condition"],
    )
    customers = renderer.read(
        "03_data/processed/scenario/447_20260711_synthetic_customers.csv",
        ["customer_configuration_id", "latitude", "longitude", "demand_kg"],
    )
    edges = renderer.read(
        "03_data/processed/route_proxy/438_20260711_route_proxy_edges.csv",
        ["base_route_proxy_id", "proxy_edge_order", "from_latitude", "to_latitude"],
    )
    routes = renderer.read(
        "03_data/processed/route_proxy/440_20260711_route_proxy_results.csv",
        ["scenario_route_proxy_id", "route_proxy_distance_km", "charger_condition"],
    )
    constraint_summary = renderer.read(
        "03_data/processed/constraints/407_20260711_constraint_summary.csv",
        ["constraint_name", "route_weighted_unmet_rate"],
    )
    case_rates = renderer.read(
        "03_data/processed/constraints/405_20260711_constraint_case_rates.csv",
        ["scenario_id", "seed", "constraint_name", "case_unmet_rate"],
    )
    scenario_summary = renderer.read(
        "03_data/processed/constraints/scenario_407_20260711_constraint_summary.csv",
        ["scenario_id", "constraint_name", "confidence_interval_lower", "confidence_interval_upper"],
    )
    sensitivity = renderer.read(
        "03_data/processed/constraints/411_20260711_sensitivity_summary.csv",
        ["parameter", "level", "constraint_name", "unmet_rate_change_from_base"],
    )
    chargers = renderer.read(
        "03_data/processed/charger_access/403_20260711_eligible_charger_candidates.csv",
        ["charger_candidate_id", "charger_condition", "latitude", "longitude"],
    )
    evidence = renderer.read(
        "03_data/processed/quantum_gap/434_20260711_quantum_vrp_evidence.csv",
        ["reference_id", "customer_scale_coverage", "capacity_coverage"],
    )
    integrated = renderer.read(
        "06_outputs/tables/csv/691_20260711_table_04_integrated_research_summary.csv",
        ["constraint_or_requirement", "route_weighted_unmet_rate", "evidence_gap"],
    )
    limitations = renderer.read(
        "03_data/processed/scenario/442_20260711_assumptions_and_limitations.csv", ["topic", "limitation"]
    )

    _render_tables(renderer)
    _figure_pipeline(renderer)
    _figure_scenario_matrix(renderer, configurations)
    _figure_customer_map(renderer, customers)
    _figure_route_map(renderer, edges)
    _figure_distance_distribution(renderer, routes)
    _figure_constraint_rates(renderer, constraint_summary)
    _figure_seed_variability(renderer, case_rates)
    _figure_confidence_intervals(renderer, scenario_summary)
    _figure_sensitivity_heatmap(renderer, sensitivity)
    _figure_tornado(renderer, sensitivity)
    _figure_charger_map(renderer, chargers)
    _figure_nearest_charger(renderer, routes)
    _scenario_feasibility_heatmaps(
        renderer,
        routes,
        "charger_geographically_accessible",
        None,
        "figure_13_charger_access_feasibility_by_scenario",
        "Charger-candidate geographic access feasibility by scenario",
    )
    _scenario_feasibility_heatmaps(
        renderer,
        routes,
        "charging_assisted_range_feasible",
        "charging_assisted_range_evaluated",
        "figure_14_charging_assisted_range_feasibility_by_scenario",
        "Simplified charging-assisted range feasibility among range-infeasible routes",
    )
    _figure_quantum_landscape(renderer, evidence)
    _figure_priority_matrix(renderer, integrated)
    _figure_limitations(renderer, limitations)

    status = pd.DataFrame(
        [
            {
                "status": "success",
                "japanese_font": font,
                "table_png_count": len(list(renderer.table_png.glob("*.png"))),
                "table_svg_count": len(list(renderer.table_svg.glob("*.svg"))),
                "figure_png_count": len(list(renderer.figure_png.glob("*.png"))),
                "figure_svg_count": len(list(renderer.figure_svg.glob("*.svg"))),
                "figure_source_csv_count": len(list(renderer.figure_source.glob("*.csv"))),
            }
        ]
    )
    status_path = renderer.validation / "685_20260711_render_status.csv"
    write_csv_atomic(status, status_path)
    renderer.generated.append(status_path)
    manifest = generate_output_manifest(renderer.generated, root=root, include_csv_shape=True)
    manifest_path = renderer.validation / "render_output_902_20260711_v04_manifest.csv"
    write_csv_atomic(manifest, manifest_path)
    print(f"Rendered {status.iloc[0]['figure_png_count']} figures and {status.iloc[0]['table_png_count']} tables.")
    print(f"Japanese-capable font selection: {font}")


if __name__ == "__main__":
    main()
