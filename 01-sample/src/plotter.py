from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
import pandas as pd

from .config import RAW_DIR


@lru_cache(maxsize=1)
def _japanese_font_family() -> str:
    candidates = [
        "Hiragino Sans",
        "Yu Gothic",
        "IPAexGothic",
        "Noto Sans CJK JP",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate in available:
            return candidate
    return "sans-serif"


def _configure_japanese_font():
    plt.rcParams["font.family"] = _japanese_font_family()
    plt.rcParams["axes.unicode_minus"] = False


@lru_cache(maxsize=1)
def _load_label_maps():
    city_master = pd.read_csv(RAW_DIR / "city_master.csv")
    industry_master = pd.read_csv(RAW_DIR / "industry_group_master.csv", encoding="utf-8-sig")
    return {
        "city": dict(zip(city_master["city_id"], city_master["city_name_ja"])),
        "industry": dict(zip(industry_master["industry_group_id"], industry_master["industry_group_name_ja"])),
    }


def _city_label(city_id: str) -> str:
    return _load_label_maps()["city"].get(city_id, city_id)


def _industry_label(industry_id: str) -> str:
    return _load_label_maps()["industry"].get(industry_id, industry_id)

def _build_diff_panel(sim_df: pd.DataFrame) -> pd.DataFrame:
    _configure_japanese_font()
    agg = sim_df.groupby(["year", "destination_city_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = (
        agg.pivot(index=["year", "destination_city_id"], columns="compute_condition", values="inflow_sim")
           .reset_index()
    )
    pivot["abs_diff"] = pivot["quantum_enabled"] - pivot["classical_only"]
    pivot["pct_diff"] = pivot["abs_diff"] / pivot["classical_only"] * 100
    if pivot["year"].nunique() == 1:
        pivot["label"] = pivot["destination_city_id"].map(_city_label)
    else:
        pivot["label"] = pivot["destination_city_id"].map(_city_label) + "（" + pivot["year"].astype(str) + "年）"
    return pivot.sort_values(["year", "abs_diff"], ascending=[True, False])


def _build_industry_diff_panel(sim_df: pd.DataFrame) -> pd.DataFrame:
    _configure_japanese_font()
    agg = sim_df.groupby(["industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = agg.pivot(index="industry_group_id", columns="compute_condition", values="inflow_sim").reset_index()
    pivot["abs_diff"] = pivot["quantum_enabled"] - pivot["classical_only"]
    pivot["pct_diff"] = pivot["abs_diff"] / pivot["classical_only"] * 100
    pivot = pivot.sort_values("abs_diff", ascending=False)
    pivot["industry_label"] = pivot["industry_group_id"].map(_industry_label)
    return pivot


def _draw_box_with_points(ax, values_by_group, labels, colors):
    box = ax.boxplot(values_by_group, labels=labels, patch_artist=True, widths=0.5)
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    for median in box["medians"]:
        median.set_color("#111111")
        median.set_linewidth(1.5)

    for idx, values in enumerate(values_by_group, start=1):
        count = len(values)
        if count == 0:
            continue
        if count == 1:
            offsets = [0]
        else:
            offsets = [((i / (count - 1)) - 0.5) * 0.18 for i in range(count)]
        ax.scatter(
            [idx + offset for offset in offsets],
            values,
            color=colors[idx - 1],
            edgecolors="white",
            linewidths=0.6,
            s=36,
            zorder=3,
        )

def plot_city_inflow(sim_df: pd.DataFrame, output_path: Path):
    pivot = _build_diff_panel(sim_df)

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)

    axes[0].bar(pivot["label"], pivot["abs_diff"], color="#1f77b4")
    axes[0].set_ylabel("流入者数差（量子 - 古典）")
    axes[0].set_title("計算条件別の都市流入差分（実数）")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].axhline(0, color="black", linewidth=0.8)

    axes[1].bar(pivot["label"], pivot["pct_diff"], color="#ff7f0e")
    axes[1].set_ylabel("変化率（%）")
    axes[1].set_title("計算条件別の都市流入差分（割合）")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].axhline(0, color="black", linewidth=0.8)

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_industry_diff(sim_df: pd.DataFrame, output_path: Path):
    pivot = _build_industry_diff_panel(sim_df)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)

    axes[0].bar(pivot["industry_label"], pivot["abs_diff"], color="#2a9d8f")
    axes[0].set_ylabel("流入者数差（量子 - 古典）")
    axes[0].set_title("計算条件別の産業群流入差分（実数）")
    axes[0].axhline(0, color="black", linewidth=0.8)

    axes[1].bar(pivot["industry_label"], pivot["pct_diff"], color="#e76f51")
    axes[1].set_ylabel("変化率（%）")
    axes[1].set_title("計算条件別の産業群流入差分（割合）")
    axes[1].axhline(0, color="black", linewidth=0.8)

    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_condition_diff_overview(sim_df: pd.DataFrame, output_path: Path):
    city_pivot = _build_diff_panel(sim_df)
    industry_pivot = _build_industry_diff_panel(sim_df)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)

    axes[0, 0].bar(city_pivot["label"], city_pivot["abs_diff"], color="#1f77b4")
    axes[0, 0].set_title("都市別差分（実数）")
    axes[0, 0].set_ylabel("流入者数差（量子 - 古典）")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].axhline(0, color="black", linewidth=0.8)

    axes[0, 1].bar(industry_pivot["industry_label"], industry_pivot["abs_diff"], color="#2a9d8f")
    axes[0, 1].set_title("産業群別差分（実数）")
    axes[0, 1].set_ylabel("流入者数差（量子 - 古典）")
    axes[0, 1].axhline(0, color="black", linewidth=0.8)

    axes[1, 0].bar(city_pivot["label"], city_pivot["pct_diff"], color="#ff7f0e")
    axes[1, 0].set_title("都市別差分（割合）")
    axes[1, 0].set_ylabel("変化率（%）")
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].axhline(0, color="black", linewidth=0.8)

    axes[1, 1].bar(industry_pivot["industry_label"], industry_pivot["pct_diff"], color="#e76f51")
    axes[1, 1].set_title("産業群別差分（割合）")
    axes[1, 1].set_ylabel("変化率（%）")
    axes[1, 1].axhline(0, color="black", linewidth=0.8)

    fig.suptitle("条件差分の幅（都市別・産業群別）", fontsize=18)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_condition_diff_boxplot(sim_df: pd.DataFrame, output_path: Path):
    city_pivot = _build_diff_panel(sim_df)
    industry_pivot = _build_industry_diff_panel(sim_df)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    _draw_box_with_points(
        axes[0],
        [city_pivot["abs_diff"].tolist(), industry_pivot["abs_diff"].tolist()],
        ["都市別", "産業群別"],
        ["#1f77b4", "#2a9d8f"],
    )
    axes[0].set_title("条件差分の幅（実数）")
    axes[0].set_ylabel("流入者数差（量子 - 古典）")
    axes[0].axhline(0, color="black", linewidth=0.8)

    _draw_box_with_points(
        axes[1],
        [city_pivot["pct_diff"].tolist(), industry_pivot["pct_diff"].tolist()],
        ["都市別", "産業群別"],
        ["#ff7f0e", "#e76f51"],
    )
    axes[1].set_title("条件差分の幅（割合）")
    axes[1].set_ylabel("変化率（%）")
    axes[1].axhline(0, color="black", linewidth=0.8)

    fig.suptitle("条件差分の幅の分布", fontsize=18)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def _prepare_technology_cost_df(
    bench_df: pd.DataFrame,
    engineering_df: pd.DataFrame,
    cost_df: pd.DataFrame,
) -> pd.DataFrame:
    bench_cols = [
        "industry_group_id",
        "compute_condition",
        "search_performance_index",
    ]
    eng_cols = [
        "industry_group_id",
        "compute_condition",
        "industry_group_name_ja",
        "lambda_rate",
        "fuel_efficiency_gain",
    ]
    cost_cols = [
        "industry_group_id",
        "compute_condition",
        "unit_cost",
    ]
    df = (
        bench_df[bench_cols]
        .merge(engineering_df[eng_cols], on=["industry_group_id", "compute_condition"], how="inner")
        .merge(cost_df[cost_cols], on=["industry_group_id", "compute_condition"], how="inner")
    )
    ref_cost = (
        df[df["compute_condition"] == "classical_only"][["industry_group_id", "unit_cost"]]
        .rename(columns={"unit_cost": "unit_cost_ref"})
    )
    df = df.merge(ref_cost, on="industry_group_id", how="left")
    df["cost_reduction_rate_pct"] = (df["unit_cost_ref"] - df["unit_cost"]) / df["unit_cost_ref"] * 100
    return df


def plot_technology_cost_flow(
    bench_df: pd.DataFrame,
    engineering_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    output_path: Path,
):
    _configure_japanese_font()

    df = _prepare_technology_cost_df(bench_df, engineering_df, cost_df)

    order = (
        df[df["compute_condition"] == "quantum_enabled"]
        .sort_values("search_performance_index", ascending=False)["industry_group_id"]
        .tolist()
    )
    if not order:
        order = sorted(df["industry_group_id"].unique())

    stage_specs = [
        {
            "column": "search_performance_index",
            "title": "探索性能",
            "xlabel": "探索性能指数",
            "formatter": lambda delta: f"{delta:+.3f}",
        },
        {
            "column": "lambda_rate",
            "title": "軽量化",
            "xlabel": "軽量化率",
            "formatter": lambda delta: f"{delta:+.3f}",
        },
        {
            "column": "cost_reduction_rate_pct",
            "title": "費用削減",
            "xlabel": "古典条件比の費用削減率（%）",
            "formatter": lambda delta: f"{delta:+.2f}%",
        },
    ]
    cond_colors = {
        "classical_only": "#4c566a",
        "quantum_enabled": "#2a9d8f",
    }
    cond_labels = {
        "classical_only": "古典",
        "quantum_enabled": "量子",
    }

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 6), sharey=True, constrained_layout=False)
    y_positions = list(range(len(order)))
    y_map = {industry_id: pos for pos, industry_id in enumerate(order)}
    industry_labels = [
        df[df["industry_group_id"] == industry_id]["industry_group_name_ja"].iloc[0]
        for industry_id in order
    ]

    for ax, stage in zip(axes, stage_specs):
        column = stage["column"]
        for industry_id in order:
            sub = df[df["industry_group_id"] == industry_id].set_index("compute_condition")
            y = y_map[industry_id]
            classical_val = sub.loc["classical_only", column]
            quantum_val = sub.loc["quantum_enabled", column]
            delta = quantum_val - classical_val
            x_mid = (classical_val + quantum_val) / 2
            delta_label = stage["formatter"](delta)

            ax.plot(
                [classical_val, quantum_val],
                [y, y],
                color="#c7c7c7",
                linewidth=2,
                zorder=1,
            )
            ax.scatter(
                classical_val,
                y,
                color=cond_colors["classical_only"],
                s=70,
                zorder=3,
            )
            ax.scatter(
                quantum_val,
                y,
                color=cond_colors["quantum_enabled"],
                s=70,
                zorder=3,
            )
            ax.text(
                x_mid,
                y - 0.08,
                delta_label,
                ha="center",
                va="center",
                fontsize=9,
                color="#2f2f2f",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 0.4},
                zorder=4,
            )

        ax.set_title(stage["title"], fontsize=13, pad=10)
        ax.set_xlabel(stage["xlabel"])
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        ax.tick_params(axis="y", length=0)

    axes[0].set_yticks(y_positions)
    axes[0].set_yticklabels(industry_labels)
    axes[0].invert_yaxis()
    axes[0].set_ylabel("産業群")

    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=cond_colors["classical_only"], markersize=9, label=cond_labels["classical_only"]),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=cond_colors["quantum_enabled"], markersize=9, label=cond_labels["quantum_enabled"]),
    ]
    fig.subplots_adjust(top=0.86, wspace=0.05)
    fig.suptitle("技術仮定 → 軽量化 → 費用の関係", fontsize=18, y=0.975)
    fig.legend(handles=legend_handles, loc="upper right", ncol=2, frameon=False, bbox_to_anchor=(0.98, 0.965))
    fig.text(0.34, 0.845, "→", ha="center", va="center", fontsize=18, color="#666666")
    fig.text(0.66, 0.845, "→", ha="center", va="center", fontsize=18, color="#666666")

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_technology_flow_diagram(
    bench_df: pd.DataFrame,
    engineering_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    output_path: Path,
):
    _configure_japanese_font()
    df = _prepare_technology_cost_df(bench_df, engineering_df, cost_df)
    summary = (
        df.groupby("compute_condition", as_index=True)[
            ["search_performance_index", "lambda_rate", "cost_reduction_rate_pct"]
        ]
        .mean()
        .round(3)
    )

    classical = summary.loc["classical_only"]
    quantum = summary.loc["quantum_enabled"]

    stages = [
        {
            "x": 0.06,
            "title": "技術仮定",
            "subtitle": "探索性能指数",
            "body": [
                "入力: 計算資源条件・アルゴリズム可用性",
                f"古典平均  {classical['search_performance_index']:.3f}",
                f"量子平均  {quantum['search_performance_index']:.3f}",
                f"平均差    {quantum['search_performance_index'] - classical['search_performance_index']:+.3f}",
            ],
            "formula": "探索性能 = f(技術仮定)",
            "facecolor": "#e8f1fb",
            "edgecolor": "#4f81bd",
        },
        {
            "x": 0.37,
            "title": "軽量化",
            "subtitle": "軽量化率",
            "body": [
                "換算: 探索性能を軽量化率へ変換",
                f"古典平均  {classical['lambda_rate']:.3f}",
                f"量子平均  {quantum['lambda_rate']:.3f}",
                f"平均差    {quantum['lambda_rate'] - classical['lambda_rate']:+.3f}",
            ],
            "formula": "lambda_rate = g(探索性能)",
            "facecolor": "#e9f7ef",
            "edgecolor": "#2a9d8f",
        },
        {
            "x": 0.68,
            "title": "費用",
            "subtitle": "古典条件比の費用削減率",
            "body": [
                "反映: 燃費改善を通じて費用へ反映",
                f"古典平均  {classical['cost_reduction_rate_pct']:.2f}%",
                f"量子平均  {quantum['cost_reduction_rate_pct']:.2f}%",
                f"平均差    {quantum['cost_reduction_rate_pct'] - classical['cost_reduction_rate_pct']:+.2f}%",
            ],
            "formula": "削減率 = (古典費用 - 現在費用) / 古典費用",
            "facecolor": "#fff4df",
            "edgecolor": "#d77a00",
        },
    ]

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box_w = 0.24
    box_h = 0.62
    box_y = 0.18

    for stage in stages:
        patch = FancyBboxPatch(
            (stage["x"], box_y),
            box_w,
            box_h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=2,
            edgecolor=stage["edgecolor"],
            facecolor=stage["facecolor"],
        )
        ax.add_patch(patch)
        ax.text(stage["x"] + 0.02, box_y + box_h - 0.08, stage["title"], fontsize=18, weight="bold", color="#222222")
        ax.text(stage["x"] + 0.02, box_y + box_h - 0.14, stage["subtitle"], fontsize=12, color="#444444")
        ax.text(stage["x"] + 0.02, box_y + box_h - 0.23, stage["formula"], fontsize=11, color="#333333")
        ax.text(
            stage["x"] + 0.02,
            box_y + box_h - 0.31,
            "\n".join(stage["body"]),
            fontsize=11.5,
            color="#333333",
            va="top",
            linespacing=1.6,
        )

    arrow_style = dict(arrowstyle="->", lw=2.5, color="#6b7280")
    ax.annotate("", xy=(0.37, 0.50), xytext=(0.30, 0.50), arrowprops=arrow_style)
    ax.annotate("", xy=(0.68, 0.50), xytext=(0.61, 0.50), arrowprops=arrow_style)
    ax.text(0.335, 0.54, "探索性能を\n軽量化率へ換算", ha="center", va="bottom", fontsize=11, color="#4b5563")
    ax.text(0.645, 0.54, "燃費改善を通じて\n費用へ反映", ha="center", va="bottom", fontsize=11, color="#4b5563")

    ax.text(0.06, 0.90, "技術仮定 → 軽量化 → 費用のフロー図", fontsize=22, weight="bold", color="#111111")
    ax.text(0.06, 0.85, "量子条件と古典条件の代表値を用いて、3段階の関係を箱と矢印で整理", fontsize=11.5, color="#555555")

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_paper_main_results(sim_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    city_pivot = _build_diff_panel(sim_df)
    industry_pivot = _build_industry_diff_panel(sim_df)

    agg = sim_df.groupby(["destination_city_id", "industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    heat = agg.pivot(
        index=["destination_city_id", "industry_group_id"],
        columns="compute_condition",
        values="inflow_sim",
    ).reset_index()
    heat["pct_diff"] = (heat["quantum_enabled"] - heat["classical_only"]) / heat["classical_only"] * 100
    matrix = heat.pivot(index="destination_city_id", columns="industry_group_id", values="pct_diff")
    matrix = matrix.loc[sorted(matrix.index), sorted(matrix.columns)]
    matrix.index = [_city_label(city_id) for city_id in matrix.index]
    matrix.columns = [_industry_label(industry_id) for industry_id in matrix.columns]

    totals = sim_df.groupby("compute_condition", as_index=False)["inflow_sim"].sum()
    totals["label"] = totals["compute_condition"].map({
        "classical_only": "古典条件",
        "quantum_enabled": "量子条件",
    })
    total_delta = float(
        totals.loc[totals["compute_condition"] == "quantum_enabled", "inflow_sim"].iloc[0]
        - totals.loc[totals["compute_condition"] == "classical_only", "inflow_sim"].iloc[0]
    )
    total_pct = float(
        total_delta
        / totals.loc[totals["compute_condition"] == "classical_only", "inflow_sim"].iloc[0]
        * 100
    )

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), constrained_layout=True)

    ax = axes[0, 0]
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=18, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title("A. 都市 × 産業群の流入差分（%）", loc="left", fontsize=13, fontweight="bold")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix.iloc[i, j]:.3f}", ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("変化率（%）")

    ax = axes[0, 1]
    ax.barh(city_pivot["label"], city_pivot["abs_diff"], color="#3a7ca5")
    ax.invert_yaxis()
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("B. 都市別の流入差分（実数）", loc="left", fontsize=13, fontweight="bold")
    ax.set_xlabel("流入者数差（量子 - 古典）")
    for y, val in enumerate(city_pivot["abs_diff"]):
        ax.text(val + 0.12, y, f"{val:.2f}", va="center", fontsize=9, color="#2f2f2f")

    ax = axes[1, 0]
    ax.bar(industry_pivot["industry_label"], industry_pivot["pct_diff"], color="#e07a5f")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("C. 産業群別の流入差分（%）", loc="left", fontsize=13, fontweight="bold")
    ax.set_ylabel("変化率（%）")
    for x, val in enumerate(industry_pivot["pct_diff"]):
        ax.text(x, val + 0.002, f"{val:.3f}", ha="center", va="bottom", fontsize=9, color="#2f2f2f")

    ax = axes[1, 1]
    colors = ["#4c566a", "#2a9d8f"]
    ax.bar(totals["label"], totals["inflow_sim"], color=colors, width=0.55)
    ax.set_title("D. 総流入量の比較", loc="left", fontsize=13, fontweight="bold")
    ax.set_ylabel("総流入者数")
    ymax = totals["inflow_sim"].max()
    ax.text(
        0.5,
        ymax * 1.0007,
        f"差分 {total_delta:.2f}（{total_pct:.3f}%）",
        ha="center",
        va="bottom",
        fontsize=11,
        color="#2f2f2f",
    )
    ax.set_ylim(0, ymax * 1.01)

    fig.suptitle("主結果: 量子条件による流入差分", fontsize=18, fontweight="bold")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_paper_robustness_results(
    sensitivity_df: pd.DataFrame,
    mc_df: pd.DataFrame,
    output_path: Path,
):
    _configure_japanese_font()
    lever_labels = {
        "search_multiplier": "探索性能",
        "adoption_multiplier": "採用率",
        "elasticity_multiplier": "コスト弾力性",
    }
    colors = {
        "search_multiplier": "#1d3557",
        "adoption_multiplier": "#2a9d8f",
        "elasticity_multiplier": "#e76f51",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

    ax = axes[0]
    for lever, sub in sensitivity_df.groupby("lever", sort=False):
        sub = sub.sort_values("level")
        ax.plot(
            sub["level"],
            sub["delta_abs"],
            marker="o",
            linewidth=2.2,
            color=colors[lever],
            label=lever_labels.get(lever, lever),
        )
    ax.set_title("A. 感度分析", loc="left", fontsize=13, fontweight="bold")
    ax.set_xlabel("倍率")
    ax.set_ylabel("流入者数差（量子 - 古典）")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(frameon=False)

    ax = axes[1]
    ax.hist(mc_df["delta_abs"], bins=12, color="#a8dadc", edgecolor="white")
    mean_val = mc_df["delta_abs"].mean()
    p05 = mc_df["delta_abs"].quantile(0.05)
    p95 = mc_df["delta_abs"].quantile(0.95)
    ax.axvline(mean_val, color="#1d3557", linewidth=2, linestyle="-", label=f"平均 {mean_val:.2f}")
    ax.axvline(p05, color="#e76f51", linewidth=1.8, linestyle="--", label=f"5%点 {p05:.2f}")
    ax.axvline(p95, color="#e76f51", linewidth=1.8, linestyle="--", label=f"95%点 {p95:.2f}")
    ax.set_title("B. モンテカルロ分布", loc="left", fontsize=13, fontweight="bold")
    ax.set_xlabel("流入者数差（量子 - 古典）")
    ax.set_ylabel("度数")
    ax.legend(frameon=False)

    fig.suptitle("頑健性確認: 感度分析と不確実性", fontsize=18, fontweight="bold")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _build_city_industry_matrix(sim_df: pd.DataFrame) -> pd.DataFrame:
    agg = sim_df.groupby(["destination_city_id", "industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
    pivot = agg.pivot(
        index=["destination_city_id", "industry_group_id"],
        columns="compute_condition",
        values="inflow_sim"
    ).reset_index()
    pivot["pct_diff"] = (pivot["quantum_enabled"] - pivot["classical_only"]) / pivot["classical_only"] * 100
    matrix = pivot.pivot(index="destination_city_id", columns="industry_group_id", values="pct_diff")
    matrix = matrix.loc[sorted(matrix.index), sorted(matrix.columns)]
    matrix.index = [_city_label(city_id) for city_id in matrix.index]
    matrix.columns = [_industry_label(industry_id) for industry_id in matrix.columns]
    return matrix


def plot_paper_heatmap(sim_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    matrix = _build_city_industry_matrix(sim_df)

    fig, ax = plt.subplots(figsize=(9.2, 6.4), constrained_layout=True)
    vmin = float(matrix.min().min())
    vmax = float(matrix.max().max())
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=18, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_xlabel("産業群")
    ax.set_ylabel("都市")
    ax.set_title("量子条件による都市・産業群別の流入差分", fontsize=15, fontweight="bold", pad=12)

    threshold = (vmin + vmax) / 2
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            ax.text(
                j,
                i,
                f"{value:.3f}",
                ha="center",
                va="center",
                color="white" if value >= threshold else "#1f2937",
                fontsize=8.5,
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("流入差分（%）")
    ax.text(
        0.0,
        -0.14,
        "注: 値は (量子条件 - 古典条件) / 古典条件 × 100",
        transform=ax.transAxes,
        fontsize=10,
        color="#555555",
    )
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_paper_sensitivity_analysis(sensitivity_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    lever_labels = {
        "search_multiplier": "探索性能",
        "adoption_multiplier": "採用率",
        "elasticity_multiplier": "コスト弾力性",
    }
    colors = {
        "search_multiplier": "#1d3557",
        "adoption_multiplier": "#2a9d8f",
        "elasticity_multiplier": "#e76f51",
    }
    order = ["search_multiplier", "adoption_multiplier", "elasticity_multiplier"]

    fig, ax = plt.subplots(figsize=(8.8, 5.8), constrained_layout=True)
    for lever in order:
        sub = sensitivity_df[sensitivity_df["lever"] == lever].sort_values("level")
        ax.plot(
            sub["level"],
            sub["delta_abs"],
            marker="o",
            markersize=7,
            linewidth=2.5,
            color=colors[lever],
        )
        ax.text(
            float(sub["level"].iloc[-1]) + 0.01,
            float(sub["delta_abs"].iloc[-1]),
            lever_labels[lever],
            color=colors[lever],
            fontsize=11,
            va="center",
        )
        baseline = sub.loc[sub["level"] == 1.0, "delta_abs"]
        if not baseline.empty:
            ax.scatter([1.0], [float(baseline.iloc[0])], color=colors[lever], s=44, zorder=4)

    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(1.0, color="#9ca3af", linewidth=1.0, linestyle=":")
    ax.set_xlim(0.84, 1.19)
    ax.set_xlabel("倍率")
    ax.set_ylabel("流入者数差（量子 - 古典）")
    ax.set_title("感度分析: 主要レバーによる流入差分の変化", fontsize=15, fontweight="bold", pad=12)
    ax.text(0.01, 0.98, "基準ケースは倍率 1.0", transform=ax.transAxes, ha="left", va="top", fontsize=10, color="#555555")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

def plot_city_industry_heatmap(sim_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    matrix = _build_city_industry_matrix(sim_df)

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title("都市 × 産業群の流入差分ヒートマップ（%）")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix.iloc[i, j]:.3f}", ha="center", va="center", color="black", fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("変化率（%）")
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_anova_effects(anova_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    effects = [
        "C(destination_city_id)",
        "C(compute_condition)",
        "C(destination_city_id):C(compute_condition)",
    ]
    effect_labels = {
        "C(destination_city_id)": "都市",
        "C(compute_condition)": "計算条件",
        "C(destination_city_id):C(compute_condition)": "交互作用",
    }
    plot_df = anova_df[anova_df["effect"].isin(effects)].copy()
    matrix = plot_df.pivot(index="industry_group_id", columns="effect", values="partial_eta2")
    matrix = matrix[effects]
    matrix.index = [_industry_label(industry_id) for industry_id in matrix.index]

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
    ax.set_ylabel("偏イータ二乗")
    ax.set_title("産業群別の ANOVA 効果量")
    ax.legend()

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_sensitivity_levers(sensitivity_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    lever_labels = {
        "search_multiplier": "探索性能",
        "adoption_multiplier": "採用率",
        "elasticity_multiplier": "コスト弾力性",
    }
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)

    for ax, (lever, sub) in zip(axes, sensitivity_df.groupby("lever", sort=False)):
        sub = sub.sort_values("level")
        ax.plot(sub["level"], sub["delta_abs"], marker="o", color="#1d3557")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(lever_labels.get(lever, lever))
        ax.set_xlabel("倍率")
        ax.set_ylabel("流入者数差（量子 - 古典）")

    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_monte_carlo_delta(mc_df: pd.DataFrame, output_path: Path):
    _configure_japanese_font()
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.hist(mc_df["delta_abs"], bins=12, color="#457b9d", edgecolor="white")
    ax.axvline(mc_df["delta_abs"].mean(), color="#e63946", linewidth=2, linestyle="--", label="平均")
    ax.set_title("モンテカルロによる流入差分の分布")
    ax.set_xlabel("流入者数差（量子 - 古典）")
    ax.set_ylabel("度数")
    ax.legend()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
