import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def _build_diff_panel(sim_df: pd.DataFrame) -> pd.DataFrame:
    agg = sim_df.groupby(["year", "destination_city_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = (
        agg.pivot(index=["year", "destination_city_id"], columns="compute_condition", values="inflow_sim")
           .reset_index()
    )
    pivot["abs_diff"] = pivot["quantum_enabled"] - pivot["classical_only"]
    pivot["pct_diff"] = pivot["abs_diff"] / pivot["classical_only"] * 100
    if pivot["year"].nunique() == 1:
        pivot["label"] = pivot["destination_city_id"]
    else:
        pivot["label"] = pivot["destination_city_id"] + " (" + pivot["year"].astype(str) + ")"
    return pivot.sort_values(["year", "abs_diff"], ascending=[True, False])

def plot_city_inflow(sim_df: pd.DataFrame, output_path: Path):
    pivot = _build_diff_panel(sim_df)

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)

    axes[0].bar(pivot["label"], pivot["abs_diff"], color="#1f77b4")
    axes[0].set_ylabel("Quantum - Classical")
    axes[0].set_title("City inflow difference by compute condition (absolute)")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].axhline(0, color="black", linewidth=0.8)

    axes[1].bar(pivot["label"], pivot["pct_diff"], color="#ff7f0e")
    axes[1].set_ylabel("Percent change (%)")
    axes[1].set_title("City inflow difference by compute condition (percent)")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].axhline(0, color="black", linewidth=0.8)

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_industry_diff(sim_df: pd.DataFrame, output_path: Path):
    agg = sim_df.groupby(["industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = agg.pivot(index="industry_group_id", columns="compute_condition", values="inflow_sim").reset_index()
    pivot["abs_diff"] = pivot["quantum_enabled"] - pivot["classical_only"]
    pivot["pct_diff"] = pivot["abs_diff"] / pivot["classical_only"] * 100
    pivot = pivot.sort_values("abs_diff", ascending=False)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)

    axes[0].bar(pivot["industry_group_id"], pivot["abs_diff"], color="#2a9d8f")
    axes[0].set_ylabel("Quantum - Classical")
    axes[0].set_title("Industry inflow difference by compute condition (absolute)")
    axes[0].axhline(0, color="black", linewidth=0.8)

    axes[1].bar(pivot["industry_group_id"], pivot["pct_diff"], color="#e76f51")
    axes[1].set_ylabel("Percent change (%)")
    axes[1].set_title("Industry inflow difference by compute condition (percent)")
    axes[1].axhline(0, color="black", linewidth=0.8)

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_city_industry_heatmap(sim_df: pd.DataFrame, output_path: Path):
    agg = sim_df.groupby(["destination_city_id", "industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = agg.pivot(
        index=["destination_city_id", "industry_group_id"],
        columns="compute_condition",
        values="inflow_sim"
    ).reset_index()
    pivot["pct_diff"] = (pivot["quantum_enabled"] - pivot["classical_only"]) / pivot["classical_only"] * 100
    matrix = pivot.pivot(index="destination_city_id", columns="industry_group_id", values="pct_diff")
    matrix = matrix.loc[sorted(matrix.index), sorted(matrix.columns)]

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title("City x industry inflow difference heatmap (%)")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix.iloc[i, j]:.3f}", ha="center", va="center", color="black", fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Percent change (%)")
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_anova_effects(anova_df: pd.DataFrame, output_path: Path):
    effects = [
        "C(destination_city_id)",
        "C(compute_condition)",
        "C(destination_city_id):C(compute_condition)",
    ]
    effect_labels = {
        "C(destination_city_id)": "City",
        "C(compute_condition)": "Compute",
        "C(destination_city_id):C(compute_condition)": "Interaction",
    }
    plot_df = anova_df[anova_df["effect"].isin(effects)].copy()
    matrix = plot_df.pivot(index="industry_group_id", columns="effect", values="partial_eta2")
    matrix = matrix[effects]

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    x = range(len(matrix.index))
    width = 0.22
    colors = ["#264653", "#2a9d8f", "#e9c46a"]

    for idx, effect in enumerate(effects):
        offset = (idx - 1) * width
        ax.bar(
            [i + offset for i in x],
            matrix[effect].values,
            width=width,
            label=effect_labels[effect],
            color=colors[idx],
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(matrix.index)
    ax.set_ylabel("Partial eta squared")
    ax.set_title("ANOVA effect sizes by industry")
    ax.legend()

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_sensitivity_levers(sensitivity_df: pd.DataFrame, output_path: Path):
    lever_labels = {
        "search_multiplier": "Search performance",
        "adoption_multiplier": "Adoption rate",
        "elasticity_multiplier": "Cost elasticity",
    }
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)

    for ax, (lever, sub) in zip(axes, sensitivity_df.groupby("lever", sort=False)):
        sub = sub.sort_values("level")
        ax.plot(sub["level"], sub["delta_abs"], marker="o", color="#1d3557")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(lever_labels.get(lever, lever))
        ax.set_xlabel("Multiplier")
        ax.set_ylabel("Quantum - Classical inflow")

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_monte_carlo_delta(mc_df: pd.DataFrame, output_path: Path):
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.hist(mc_df["delta_abs"], bins=12, color="#457b9d", edgecolor="white")
    ax.axvline(mc_df["delta_abs"].mean(), color="#e63946", linewidth=2, linestyle="--", label="Mean")
    ax.set_title("Monte Carlo distribution of inflow difference")
    ax.set_xlabel("Quantum - Classical inflow")
    ax.set_ylabel("Frequency")
    ax.legend()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
