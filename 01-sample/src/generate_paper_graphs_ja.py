#!/usr/bin/env python3
from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

import matplotlib
from matplotlib import font_manager

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


CITY_LABELS = {
    "tokyo": "東京",
    "osaka": "大阪",
    "nagoya": "名古屋",
    "fukuoka": "福岡",
    "hiroshima": "広島",
    "sendai": "仙台",
    "sapporo": "札幌",
}

INDUSTRY_LABELS = {
    "metal": "金属素材群",
    "chem_polymer": "化学・高分子素材群",
    "inorganic": "無機素材群",
}


@lru_cache(maxsize=1)
def japanese_font_family() -> str:
    candidates = [
        "Hiragino Sans",
        "Yu Gothic",
        "Meiryo",
        "Noto Sans CJK JP",
        "IPAexGothic",
        "TakaoGothic",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate in available:
            return candidate
    return "DejaVu Sans"


def configure_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 300,
            "font.family": japanese_font_family(),
            "font.size": 11,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#555555",
            "axes.linewidth": 0.8,
            "axes.labelcolor": "#222222",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "grid.color": "#d7d7d7",
            "grid.linestyle": "--",
            "grid.linewidth": 0.7,
        }
    )


def load_differences(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(input_dir / "inflow_summary.csv")
    pivot = (
        df.pivot_table(
            index=["destination_city_id", "industry_group_id"],
            columns="compute_condition",
            values="inflow_sim",
            aggfunc="sum",
        )
        .reset_index()
    )
    pivot["delta_abs"] = pivot["quantum_enabled"] - pivot["classical_only"]
    pivot["delta_pct"] = pivot["delta_abs"] / pivot["classical_only"] * 100.0

    city = (
        pivot.groupby("destination_city_id", as_index=False)
        .agg(
            delta_abs=("delta_abs", "sum"),
            classical=("classical_only", "sum"),
        )
        .sort_values("delta_abs", ascending=False)
    )
    city["delta_pct"] = city["delta_abs"] / city["classical"] * 100.0
    city["city_label"] = city["destination_city_id"].map(CITY_LABELS).fillna(city["destination_city_id"])

    industry_order = ["metal", "chem_polymer", "inorganic"]
    industry = (
        pivot.groupby("industry_group_id", as_index=False)
        .agg(
            delta_abs=("delta_abs", "sum"),
            classical=("classical_only", "sum"),
        )
    )
    industry["delta_pct"] = industry["delta_abs"] / industry["classical"] * 100.0
    industry["industry_label"] = industry["industry_group_id"].map(INDUSTRY_LABELS).fillna(industry["industry_group_id"])
    industry["order"] = industry["industry_group_id"].map({k: i for i, k in enumerate(industry_order)})
    industry = industry.sort_values("order").drop(columns="order")
    return city, industry


def save_city_chart(city: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    bars = ax.bar(
        city["city_label"],
        city["delta_abs"],
        color="#2b6ea6",
        width=0.72,
    )

    for bar, pct in zip(bars, city["delta_pct"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.18,
            f"古典条件に対する増加率:\n{pct:.3f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#333333",
        )

    ax.set_title("都市別流入就業者数の増加分", fontsize=13, pad=10, fontweight="bold")
    ax.set_ylabel("増加人数（量子条件 - 古典条件）")
    ax.set_xlabel("都市")
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)

    path = output_dir / "figure_city_inflow_change_ja_01sample.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_industry_chart(industry: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    bars = ax.bar(
        industry["industry_label"],
        industry["delta_abs"],
        color=["#6b5b95", "#2a9d8f", "#c75b12"],
        width=0.62,
    )

    for bar, pct in zip(bars, industry["delta_pct"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.22,
            f"古典条件に対する増加率:\n{pct:.3f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#333333",
        )

    ax.set_title("産業群別流入就業者数の増加分", fontsize=13, pad=10, fontweight="bold")
    ax.set_ylabel("増加人数（量子条件 - 古典条件）")
    ax.set_xlabel("産業群")
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)

    path = output_dir / "figure_industry_inflow_change_ja_01sample.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="01-sample の論文向け日本語図を生成する")
    parser.add_argument(
        "--input_dir",
        default="outputs/tables",
        help="inflow_summary.csv があるディレクトリ",
    )
    parser.add_argument(
        "--output_dir",
        default="outputs/figures/paper_ja",
        help="図の出力先ディレクトリ",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    input_dir = (project_root / args.input_dir).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    configure_style()
    city, industry = load_differences(input_dir)
    outputs = [
        save_city_chart(city, output_dir),
        save_industry_chart(industry, output_dir),
    ]
    for path in outputs:
        print(f"Saved figure to {path}")


if __name__ == "__main__":
    main()
