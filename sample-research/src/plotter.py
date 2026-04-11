import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_city_inflow(sim_df: pd.DataFrame, output_path: Path):
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
    pivot = pivot.sort_values(["year", "abs_diff"], ascending=[True, False])

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
