#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def configure_style() -> None:
    plt.style.use("default")
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 150
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Hiragino Sans",
        "Yu Gothic",
        "Meiryo",
        "Noto Sans CJK JP",
        "IPAexGothic",
        "TakaoGothic",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def load_base_results(results_path: Path) -> pd.DataFrame:
    results = pd.read_csv(results_path)
    base = results[results["scenario"] == "base"].copy()
    if base.empty:
        raise ValueError("base シナリオの結果が見つからない。")
    return base


def build_city_chart(base: pd.DataFrame, output_path: Path) -> None:
    city = (
        base.groupby("city", as_index=False)
        .agg(delta_flow=("delta_flow", "sum"))
        .sort_values("delta_flow", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    bars = ax.barh(city["city"], city["delta_flow"], color="#1f5aa6")
    ax.set_title("基準シナリオにおける都市別流入差分")
    ax.set_xlabel("流入差分 (delta_flow)")
    ax.set_ylabel("都市")
    ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_axisbelow(True)

    max_val = float(city["delta_flow"].max())
    for bar, value in zip(bars, city["delta_flow"]):
        ax.text(
            value + max_val * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def build_industry_chart(base: pd.DataFrame, output_path: Path) -> None:
    industry = (
        base.groupby("industry_group", as_index=False)
        .agg(
            delta_flow=("delta_flow", "sum"),
            predicted_classical=("predicted_classical", "sum"),
        )
        .sort_values("delta_flow", ascending=False)
    )
    industry["pct_change"] = industry["delta_flow"] / industry["predicted_classical"] * 100.0

    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    bars = ax.bar(
        industry["industry_group"],
        industry["pct_change"],
        color=["#c44900", "#2a9d8f", "#6c757d"],
    )
    ax.set_title("基準シナリオにおける産業群別変化率")
    ax.set_ylabel("変化率 (%)")
    ax.set_xlabel("産業群")
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_axisbelow(True)

    max_val = float(industry["pct_change"].max())
    for bar, value in zip(bars, industry["pct_change"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max_val * 0.04,
            f"{value:.3f}%",
            va="bottom",
            ha="center",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="デモ分析結果の図を生成する")
    parser.add_argument(
        "--input_dir",
        default="data/output/demo_run_reproduced",
        help="results_by_city_industry.csv があるディレクトリ",
    )
    parser.add_argument(
        "--output_dir",
        default="outputs/figures/demo_run",
        help="図の出力先ディレクトリ",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    input_dir = (project_root / args.input_dir).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    configure_style()
    base = load_base_results(input_dir / "results_by_city_industry.csv")

    build_city_chart(base, output_dir / "city_delta_flow_base.png")
    build_industry_chart(base, output_dir / "industry_pct_change_base.png")

    print(f"図を出力した: {output_dir}")


if __name__ == "__main__":
    main()
