from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .model import QuantumFoodHealthModel
from .report import render_report
from .stats import build_statistical_tests
from .utils import ensure_dir, number, pct, yen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "outputs"
FIG_DIR = OUTPUT_DIR / "figures"

GROUP_LABELS_EN = {
    "低所得層": "Low income",
    "中低所得層": "Lower-middle income",
    "中所得層": "Middle income",
    "中高所得層": "Upper-middle income",
    "高所得層": "High income",
}

DISEASE_LABELS_EN = {
    "2型糖尿病": "Type 2 diabetes",
    "虚血性心疾患": "Ischemic heart disease",
    "脳卒中": "Stroke",
}


def _setup_matplotlib() -> None:
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = [
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Yu Gothic",
        "IPAexGothic",
        "Noto Sans CJK JP",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False


def load_inputs() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    with (CONFIG_DIR / "sample_params.yaml").open("r", encoding="utf-8") as f:
        params = yaml.safe_load(f)
    groups = pd.read_csv(DATA_DIR / "population_groups.csv")
    diseases = pd.read_csv(DATA_DIR / "disease_burden.csv")
    return params, groups, diseases


def save_tables(
    group_results: pd.DataFrame,
    disease_results: pd.DataFrame,
    summary: dict[str, float],
    statistical_tests: pd.DataFrame,
) -> None:
    group_results.to_csv(OUTPUT_DIR / "group_results.csv", index=False, encoding="utf-8-sig")
    disease_results.to_csv(OUTPUT_DIR / "disease_results.csv", index=False, encoding="utf-8-sig")
    summary_df = pd.DataFrame(
        {"metric": list(summary.keys()), "value": list(summary.values())}
    )
    summary_df.to_csv(OUTPUT_DIR / "summary_metrics.csv", index=False, encoding="utf-8-sig")
    statistical_tests.to_csv(OUTPUT_DIR / "statistical_tests.csv", index=False, encoding="utf-8-sig")


def plot_cost_chain(transmission: dict[str, float]) -> None:
    _setup_matplotlib()
    import matplotlib.pyplot as plt

    stages = [
        ("窒素固定効率改善", transmission["quantum_nitrogen_efficiency_gain_pct"] * 100, "#1d4ed8"),
        ("肥料エネルギー低下", transmission["fertilizer_energy_reduction_pct"] * 100, "#0f766e"),
        ("肥料価格低下", transmission["fertilizer_price_reduction_pct"] * 100, "#0f766e"),
        ("野菜コスト低下", transmission["vegetable_cost_reduction_pct"] * 100, "#0f766e"),
        ("最終的な野菜価格変化", transmission["vegetable_price_change_pct"] * 100, "#b45309"),
    ]

    labels = [stage[0] for stage in stages]
    values = [stage[1] for stage in stages]
    colors = [stage[2] for stage in stages]

    cumulative = []
    running = 0.0
    for value in values[:-1]:
        cumulative.append(running)
        running += value
    cumulative.append(0.0)

    fig, ax = plt.subplots(figsize=(10.8, 6.2))
    x = list(range(len(labels)))
    width = 0.7

    for idx, (label, value, color) in enumerate(stages):
        if idx < len(stages) - 1:
            bottom = cumulative[idx]
            ax.bar(idx, value, bottom=bottom, color=color, width=width, edgecolor="white", linewidth=1.2)
            y = bottom + value
            ax.text(idx, y + 1.1, f"{value:+.2f}%", ha="center", va="bottom", fontsize=10, color="#0f172a")
            if idx < len(stages) - 2:
                next_bottom = cumulative[idx + 1]
                ax.plot(
                    [idx + width / 2, idx + 1 - width / 2],
                    [bottom + value, next_bottom],
                    color="#94a3b8",
                    linestyle="--",
                    linewidth=1.4,
                )
        else:
            ax.bar(idx, value, color=color, width=width, edgecolor="white", linewidth=1.2)
            y = value - 0.3 if value < 0 else value + 0.5
            va = "top" if value < 0 else "bottom"
            ax.text(idx, y, f"{value:+.2f}%", ha="center", va=va, fontsize=10, color="#0f172a")

    ax.set_xticks(x, labels, rotation=15, ha="right")
    ax.set_ylabel("変化率（%）")
    ax.set_title("コスト波及のウォーターフォール図", pad=14)
    ax.axhline(0, color="#475569", linewidth=1)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ymax = max(c + v for c, v in zip(cumulative[:-1], values[:-1]))
    ymin = min(values[-1], 0)
    ax.set_ylim(ymin - 2.5, ymax + 6)

    fig.text(
        0.11,
        0.02,
        "最初の4本は上流の改善・低下率、最後の1本は小売段階の最終的な野菜価格変化を示す。",
        fontsize=9,
        color="#475569",
    )
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    plt.savefig(FIG_DIR / "cost_chain.png", dpi=200)
    plt.close()


def plot_intake_by_group(group_results: pd.DataFrame) -> None:
    _setup_matplotlib()
    import matplotlib.pyplot as plt

    labels = group_results["group"].tolist()
    baseline = group_results["baseline_mean_intake_g_per_day"].tolist()
    new = group_results["new_mean_intake_g_per_day"].tolist()
    deltas = group_results["intake_change_g_per_day"].tolist()
    y_pos = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))

    for y, base, after in zip(y_pos, baseline, new):
        ax.plot([base, after], [y, y], color="#94a3b8", linewidth=2.5, zorder=1)

    ax.scatter(baseline, y_pos, s=95, color="#2563eb", label="基準", zorder=3)
    ax.scatter(new, y_pos, s=95, color="#ea580c", label="量子実装後", zorder=3)

    ax.set_yticks(y_pos, labels)
    ax.invert_yaxis()
    ax.set_xlabel("平均野菜摂取量（g/日）")
    ax.set_title("所得群別の平均野菜摂取量の変化", pad=14)
    ax.xaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    xmin = min(baseline) - 15
    xmax = max(new) + 22
    ax.set_xlim(xmin, xmax)

    for y, after, delta in zip(y_pos, new, deltas):
        ax.text(after + 2.2, y, f"+{delta:.2f} g", va="center", ha="left", fontsize=9.5, color="#9a3412")

    ax.legend(loc="upper right", frameon=False)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "intake_by_group.png", dpi=200)
    plt.close()


def plot_daly_reduction(disease_results: pd.DataFrame) -> None:
    _setup_matplotlib()
    import matplotlib.pyplot as plt

    ordered = disease_results.sort_values("daly_reduction", ascending=False).reset_index(drop=True)
    labels = ordered["disease"].tolist()
    daly = ordered["daly_reduction"].tolist()
    cost = ordered["medical_cost_reduction_jpy"].tolist()
    y_pos = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bars = ax.barh(y_pos, daly, color=["#b91c1c", "#ea580c", "#ca8a04"], height=0.58)

    ax.set_yticks(y_pos, labels)
    ax.invert_yaxis()
    ax.set_xlabel("DALY 減少量")
    ax.set_title("疾患別の健康負担減少", pad=14)
    ax.xaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    xmax = max(daly) * 1.32
    ax.set_xlim(0, xmax)

    for rank, (bar, daly_value, cost_value) in enumerate(zip(bars, daly, cost), start=1):
        y = bar.get_y() + bar.get_height() / 2
        ax.text(
            daly_value + xmax * 0.015,
            y,
            f"#{rank}  {daly_value:,.0f} DALY\n医療費 -{cost_value/1e9:.2f} 億円",
            va="center",
            ha="left",
            fontsize=9.3,
            color="#0f172a",
        )

    plt.tight_layout()
    plt.savefig(FIG_DIR / "daly_reduction.png", dpi=200)
    plt.close()


def format_group_rows(group_results: pd.DataFrame) -> list[list[str]]:
    rows: list[list[str]] = []
    for _, row in group_results.iterrows():
        rows.append(
            [
                str(row["group"]),
                f"{number(row['baseline_mean_intake_g_per_day'], 2)} g/日",
                f"{number(row['new_mean_intake_g_per_day'], 2)} g/日",
                f"{number(row['intake_change_g_per_day'], 2)} g/日",
                pct(float(row["baseline_recommended_share"])),
                pct(float(row["new_recommended_share"])),
            ]
        )
    return rows


def format_disease_rows(disease_results: pd.DataFrame) -> list[list[str]]:
    rows: list[list[str]] = []
    for _, row in disease_results.iterrows():
        rows.append(
            [
                str(row["disease"]),
                pct(float(row["risk_reduction_pct"])),
                number(float(row["cases_reduction"]), 2),
                number(float(row["daly_reduction"]), 2),
                yen(float(row["medical_cost_reduction_jpy"])),
            ]
        )
    return rows


def format_statistical_test_rows(statistical_tests: pd.DataFrame) -> list[list[str]]:
    rows: list[list[str]] = []
    for _, row in statistical_tests.iterrows():
        rows.append(
            [
                str(row["metric"]),
                str(row["analysis_unit"]),
                str(int(row["n_non_zero"])),
                str(int(row["positive_diffs"])),
                str(int(row["negative_diffs"])),
                f"{number(float(row['mean_change']), 4)} {row['unit']}",
                f"{float(row['one_sided_p_value']):.5f}",
                "有意" if bool(row["significant_at_5pct_one_sided"]) else "有意ではない",
            ]
        )
    return rows


def run_pipeline() -> dict[str, Any]:
    ensure_dir(OUTPUT_DIR)
    ensure_dir(FIG_DIR)

    params, groups, diseases = load_inputs()
    model = QuantumFoodHealthModel(params)
    outputs = model.run(groups, diseases)
    statistical_tests = build_statistical_tests(outputs.group_results, outputs.disease_results)

    save_tables(outputs.group_results, outputs.disease_results, outputs.summary, statistical_tests)

    group_rows = format_group_rows(outputs.group_results)
    disease_rows = format_disease_rows(outputs.disease_results)
    statistical_test_rows = format_statistical_test_rows(statistical_tests)
    report_text = render_report(
        OUTPUT_DIR,
        params,
        outputs.transmission,
        outputs.summary,
        group_rows,
        disease_rows,
        statistical_test_rows,
    )

    try:
        plot_cost_chain(outputs.transmission)
        plot_intake_by_group(outputs.group_results)
        plot_daly_reduction(outputs.disease_results)
    except Exception as exc:
        print(f"図表生成をスキップした: {exc}")

    return {
        "params": params,
        "transmission": outputs.transmission,
        "summary": outputs.summary,
        "statistical_tests": statistical_tests,
        "report_text": report_text,
    }
