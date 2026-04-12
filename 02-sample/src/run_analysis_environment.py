#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from run_quantum_commuting_model import (  # type: ignore
    build_benchmark_comparison,
    build_industry_translation,
    load_controls,
    fit_ppml,
    coefficient_table,
    apply_counterfactual,
)
import pandas as pd


def resolve_file(input_dir: Path, candidates: list[str]) -> Path:
    for name in candidates:
        candidate = input_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"必要ファイルが見つからない: {candidates} in {input_dir}")


def run_once(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    evidence_path = resolve_file(input_dir, [
        "benchmark_evidence.csv",
        "benchmark_evidence_model_input.csv",
        "benchmark_evidence_model_input_template.csv",
        "benchmark_evidence_demo.csv",
    ])
    od_path = resolve_file(input_dir, [
        "od_flow.csv",
        "od_flow_demo.csv",
    ])
    translation_path = resolve_file(input_dir, [
        "translation_parameters.csv",
        "translation_parameters_demo.csv",
    ])
    controls_path = resolve_file(input_dir, [
        "model_controls.csv",
    ])

    evidence = pd.read_csv(evidence_path)
    od_data = pd.read_csv(od_path)
    translation_parameters = pd.read_csv(translation_path)
    controls = load_controls(controls_path)

    comparison = build_benchmark_comparison(evidence, controls)
    industry_translation = build_industry_translation(comparison, translation_parameters)
    result, fitted_od_data, car_dependency_mean = fit_ppml(od_data)
    industries = sorted(od_data["industry_group"].unique().tolist())
    coefficients = coefficient_table(result, industries)

    comparison.to_csv(output_dir / "benchmark_comparison.csv", index=False, encoding="utf-8-sig")
    industry_translation.to_csv(output_dir / "industry_translation.csv", index=False, encoding="utf-8-sig")
    coefficients.to_csv(output_dir / "coefficient_estimates.csv", index=False, encoding="utf-8-sig")

    all_by_od = []
    all_by_city_industry = []
    for scenario in ["low", "base", "high"]:
        by_od, by_city_industry = apply_counterfactual(
            result=result,
            fitted_od_data=fitted_od_data,
            industry_translation=industry_translation,
            scenario=scenario,
            car_dependency_mean=car_dependency_mean,
        )
        all_by_od.append(by_od)
        all_by_city_industry.append(by_city_industry)

    results_by_od = pd.concat(all_by_od, ignore_index=True)
    results_by_city_industry = pd.concat(all_by_city_industry, ignore_index=True)
    results_by_od.to_csv(output_dir / "results_by_od.csv", index=False, encoding="utf-8-sig")
    results_by_city_industry.to_csv(output_dir / "results_by_city_industry.csv", index=False, encoding="utf-8-sig")

    summary_lines = []
    summary_lines.append("統合分析環境から反実仮想モデルを実行した。")
    summary_lines.append(f"入力ディレクトリ: {input_dir}")
    summary_lines.append("")
    summary_lines.append("主要な推定係数")
    for _, row in coefficients.iterrows():
        summary_lines.append(
            f"- {row['industry_group']}: 平均自動車依存度における一般化交通費弾力性 = "
            f"{row['estimated_log_cost_elasticity_at_mean_car_dependency']:.3f}, "
            f"自動車依存度の追加感応度 = {row['estimated_additional_sensitivity_from_car_dependency']:.3f}"
        )
    (output_dir / "run_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"完了: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="統合分析環境の実行ラッパー")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    demo = subparsers.add_parser("demo", help="data/demo を使ってデモ実行する")
    demo.add_argument("--input_dir", default=str(Path("data/demo")), help="入力ディレクトリ")
    demo.add_argument("--output_dir", default=str(Path("data/output/demo_run")), help="出力ディレクトリ")

    actual = subparsers.add_parser("actual", help="実データで実行する")
    actual.add_argument("--input_dir", default=str(Path("data/actual_input")), help="入力ディレクトリ")
    actual.add_argument("--output_dir", default=str(Path("data/output/actual_run")), help="出力ディレクトリ")

    args = parser.parse_args()
    project_root = THIS_DIR.parent
    input_dir = (project_root / args.input_dir).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    run_once(input_dir=input_dir, output_dir=output_dir)


if __name__ == "__main__":
    main()
