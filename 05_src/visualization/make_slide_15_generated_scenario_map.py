#!/usr/bin/env python3
"""Create the slide-15 representative synthetic scenario map."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
import pandas as pd

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT / "constraint_evaluation"))

from validation_utils import find_repository_root, read_csv_checked, write_csv_atomic


SCENARIO_ID = "C050_V03_CHG_balanced_SPEED25_T480"
SEED = 1
CUSTOMER_COUNT = 50
VEHICLE_COUNT = 3
CHARGER_CONDITION = "balanced"


def configure_font() -> None:
    """Use a presentation-safe installed sans-serif font."""

    installed = {font.name for font in font_manager.fontManager.ttflist}
    preferred = ["Aptos", "Arial", "Hiragino Sans", "DejaVu Sans"]
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


def main() -> None:
    """Build PNG, SVG, and traceable source data for one confirmed scenario."""

    root = find_repository_root(Path(__file__).resolve())
    edges = read_csv_checked(
        root / "03_data/processed/route_proxy/438_20260711_route_proxy_edges.csv",
        required_columns=[
            "base_route_proxy_id",
            "customer_count",
            "vehicle_count",
            "seed",
            "proxy_edge_order",
            "from_node_id",
            "from_node_type",
            "from_latitude",
            "from_longitude",
            "to_node_id",
            "to_node_type",
            "to_latitude",
            "to_longitude",
        ],
        require_nonempty=True,
    )
    members = read_csv_checked(
        root / "03_data/processed/route_proxy/439_20260711_route_proxy_members.csv",
        required_columns=[
            "base_route_proxy_id",
            "customer_count",
            "vehicle_count",
            "seed",
            "node_id",
            "node_type",
            "latitude",
            "longitude",
        ],
        require_nonempty=True,
    )
    chargers = read_csv_checked(
        root / "03_data/processed/charger_access/403_20260711_eligible_charger_candidates.csv",
        required_columns=[
            "charger_candidate_id",
            "charger_condition",
            "latitude",
            "longitude",
        ],
        require_nonempty=True,
    )
    routes = read_csv_checked(
        root / "03_data/processed/route_proxy/440_20260711_route_proxy_results.csv",
        required_columns=[
            "scenario_id",
            "seed",
            "base_route_proxy_id",
            "nearest_candidate_charger_id",
        ],
        require_nonempty=True,
    )

    edge_subset = edges[
        edges["customer_count"].eq(CUSTOMER_COUNT)
        & edges["vehicle_count"].eq(VEHICLE_COUNT)
        & edges["seed"].eq(SEED)
    ].copy()
    member_subset = members[
        members["customer_count"].eq(CUSTOMER_COUNT)
        & members["vehicle_count"].eq(VEHICLE_COUNT)
        & members["seed"].eq(SEED)
    ].copy()
    charger_subset = chargers[
        chargers["charger_condition"].eq(CHARGER_CONDITION)
    ].drop_duplicates("charger_candidate_id").copy()
    scenario_routes = routes[
        routes["scenario_id"].eq(SCENARIO_ID) & routes["seed"].eq(SEED)
    ].copy()

    if edge_subset["base_route_proxy_id"].nunique() != VEHICLE_COUNT:
        raise ValueError("Representative scenario does not contain exactly three route proxies.")
    if member_subset[member_subset["node_type"].eq("synthetic_customer")]["node_id"].nunique() != CUSTOMER_COUNT:
        raise ValueError("Representative scenario does not contain exactly 50 synthetic customers.")
    if scenario_routes.empty:
        raise ValueError(f"Scenario {SCENARIO_ID!r}, seed {SEED} is unavailable.")

    route_ids = sorted(edge_subset["base_route_proxy_id"].unique())
    colors = ["#2563EB", "#F59E0B", "#7C3AED"]
    color_lookup = dict(zip(route_ids, colors))
    configure_font()

    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    ax.scatter(
        charger_subset["longitude"],
        charger_subset["latitude"],
        marker="^",
        s=26,
        facecolor="#14B8A6",
        edgecolor="white",
        linewidth=0.4,
        alpha=0.42,
        zorder=1,
    )

    for route_id in route_ids:
        color = color_lookup[route_id]
        route_edges = edge_subset[edge_subset["base_route_proxy_id"].eq(route_id)].sort_values(
            "proxy_edge_order"
        )
        for row in route_edges.itertuples(index=False):
            ax.plot(
                [row.from_longitude, row.to_longitude],
                [row.from_latitude, row.to_latitude],
                color=color,
                linestyle=(0, (4, 3)),
                linewidth=1.5,
                alpha=0.86,
                zorder=2,
            )
        route_members = member_subset[
            member_subset["base_route_proxy_id"].eq(route_id)
            & member_subset["node_type"].eq("synthetic_customer")
        ]
        ax.scatter(
            route_members["longitude"],
            route_members["latitude"],
            s=42,
            facecolor=color,
            edgecolor="white",
            linewidth=0.8,
            alpha=0.94,
            zorder=3,
        )

    depot = member_subset[member_subset["node_type"].eq("depot_proxy")].iloc[0]
    ax.scatter(
        depot["longitude"],
        depot["latitude"],
        marker="s",
        s=155,
        facecolor="#17243A",
        edgecolor="white",
        linewidth=1.1,
        zorder=5,
    )

    nearest_ids = set(scenario_routes["nearest_candidate_charger_id"].dropna().astype(str))
    nearest = charger_subset[
        charger_subset["charger_candidate_id"].astype(str).isin(nearest_ids)
    ]
    ax.scatter(
        nearest["longitude"],
        nearest["latitude"],
        marker="^",
        s=88,
        facecolor="#0F766E",
        edgecolor="white",
        linewidth=1.0,
        zorder=4,
    )

    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#2563EB", markeredgecolor="white", markersize=8, label="Synthetic customers — Route 1"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#F59E0B", markeredgecolor="white", markersize=8, label="Synthetic customers — Route 2"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#7C3AED", markeredgecolor="white", markersize=8, label="Synthetic customers — Route 3"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#17243A", markeredgecolor="white", markersize=9, label="Selected depot proxy"),
        Line2D([0], [0], color="#475569", linestyle=(0, (4, 3)), linewidth=1.7, label="Route proxy"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#14B8A6", alpha=0.65, markersize=8, label="Balanced charger candidates"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#0F766E", markeredgecolor="white", markersize=9, label="Nearest candidate by route"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper left",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=9,
        ncol=2,
    )
    ax.set_title(
        "Representative Synthetic Scenario — 50 Customers / 3 Vehicles / Balanced Charger Condition",
        loc="left",
        fontsize=17,
        color="#17243A",
        pad=14,
        weight="semibold",
    )
    ax.set_xlabel("Longitude", color="#475569")
    ax.set_ylabel("Latitude", color="#475569")
    ax.tick_params(colors="#64748B")
    ax.grid(color="#E2E8F0", linewidth=0.7, alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color("#CBD5E1")
    ax.text(
        0.005,
        -0.13,
        "Proxy edges show visit order only; they are not actual road-network paths or optimized EVRP routes.",
        transform=ax.transAxes,
        fontsize=9.5,
        color="#64748B",
        ha="left",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    png_path = root / "06_outputs/06_outputs/figures/active/active/png/637_20260711_slide_15_generated_scenario_map.png"
    svg_path = root / "06_outputs/06_outputs/figures/active/active/svg/673_20260711_slide_15_generated_scenario_map.svg"
    source_path = root / "06_outputs/06_outputs/figures/active/active/source_data/655_20260711_slide_15_generated_scenario_map.csv"
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    edge_source = edge_subset.assign(
        layer="route_proxy_edge",
        scenario_id=SCENARIO_ID,
        charger_condition=CHARGER_CONDITION,
        latitude=pd.NA,
        longitude=pd.NA,
    )
    member_source = member_subset.assign(
        layer=member_subset["node_type"],
        scenario_id=SCENARIO_ID,
        charger_condition=CHARGER_CONDITION,
        from_latitude=pd.NA,
        from_longitude=pd.NA,
        to_latitude=pd.NA,
        to_longitude=pd.NA,
    )
    charger_source = charger_subset.assign(
        layer="charger_candidate",
        scenario_id=SCENARIO_ID,
        seed=SEED,
        customer_count=CUSTOMER_COUNT,
        vehicle_count=VEHICLE_COUNT,
        base_route_proxy_id=pd.NA,
        node_id=charger_subset["charger_candidate_id"],
        node_type="charger_candidate",
        from_latitude=pd.NA,
        from_longitude=pd.NA,
        to_latitude=pd.NA,
        to_longitude=pd.NA,
    )
    source_columns = [
        "layer",
        "scenario_id",
        "seed",
        "customer_count",
        "vehicle_count",
        "charger_condition",
        "base_route_proxy_id",
        "node_id",
        "node_type",
        "latitude",
        "longitude",
        "from_latitude",
        "from_longitude",
        "to_latitude",
        "to_longitude",
    ]
    combined = pd.concat(
        [
            edge_source.reindex(columns=source_columns),
            member_source.reindex(columns=source_columns),
            charger_source.reindex(columns=source_columns),
        ],
        ignore_index=True,
    )
    write_csv_atomic(combined, source_path)
    print(png_path)
    print(svg_path)
    print(source_path)


if __name__ == "__main__":
    main()
