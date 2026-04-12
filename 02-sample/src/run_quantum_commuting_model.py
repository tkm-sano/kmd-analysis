#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量子計算による材料探索効率の改善が都市への就業流入に及ぼす影響
二段階の静学的反実仮想モデルの実行用スクリプトである。

入力:
  - benchmark_evidence_demo.csv
  - od_flow_demo.csv
  - translation_parameters_demo.csv
  - model_controls.csv

出力:
  - benchmark_comparison.csv
  - industry_translation.csv
  - coefficient_estimates.csv
  - results_by_od.csv
  - results_by_city_industry.csv

注意:
  ここに同封した数値は動作確認用の例示値であり、実証値ではない。
  実証分析では、利用者が公的統計と文献レビューに基づいて置換すること。
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def weighted_mean(values: Iterable[float], weights: Iterable[float]) -> float:
    series = pd.Series(values, dtype=float)
    weight_series = pd.Series(weights, dtype=float)
    mask = (~series.isna()) & (~weight_series.isna())
    if mask.sum() == 0:
        return np.nan
    return float(np.average(series[mask], weights=weight_series[mask]))


def load_controls(path: Path) -> Dict[str, float]:
    controls_df = pd.read_csv(path)
    controls: Dict[str, float] = {}
    for _, row in controls_df.iterrows():
        key = str(row["key"])
        value = row["value"]
        if key == "scenario_default":
            controls[key] = str(value)
        else:
            controls[key] = float(value)
    return controls


def build_benchmark_comparison(evidence: pd.DataFrame, controls: Dict[str, float]) -> pd.DataFrame:
    required_columns = {
        "industry_group", "problem_class", "compute_condition", "quality_threshold",
        "cost_index", "time_hours", "quality_value", "valid_candidates",
        "quantum_algorithm_availability", "evidence_weight", "source_key"
    }
    missing = required_columns - set(evidence.columns)
    if missing:
        raise ValueError(f"benchmark_evidence に必要な列が不足している: {sorted(missing)}")

    comparison_rows = []
    for (industry_group, problem_class), group in evidence.groupby(["industry_group", "problem_class"]):
        classical = group[group["compute_condition"].str.lower() == "classical"]
        quantum = group[group["compute_condition"].str.lower() == "quantum"]
        if classical.empty or quantum.empty:
            continue

        classical_cost = weighted_mean(classical["cost_index"], classical["evidence_weight"])
        quantum_cost = weighted_mean(quantum["cost_index"], quantum["evidence_weight"])
        classical_time = weighted_mean(classical["time_hours"], classical["evidence_weight"])
        quantum_time = weighted_mean(quantum["time_hours"], quantum["evidence_weight"])
        classical_quality = weighted_mean(classical["quality_value"], classical["evidence_weight"])
        quantum_quality = weighted_mean(quantum["quality_value"], quantum["evidence_weight"])
        classical_valid = weighted_mean(classical["valid_candidates"], classical["evidence_weight"])
        quantum_valid = weighted_mean(quantum["valid_candidates"], quantum["evidence_weight"])
        quantum_availability = weighted_mean(quantum["quantum_algorithm_availability"], quantum["evidence_weight"])
        quality_threshold = weighted_mean(group["quality_threshold"], group["evidence_weight"])

        cost_reduction_ratio = classical_cost / quantum_cost
        time_reduction_ratio = classical_time / quantum_time
        candidate_yield_ratio = (quantum_valid / quantum_cost) / (classical_valid / classical_cost)

        quality_penalty = 1.0 if quantum_quality >= quality_threshold else controls["quality_fail_penalty"]

        quality_adjusted_gain = quantum_availability * quality_penalty * np.exp(
            controls["cost_weight"] * np.log(cost_reduction_ratio)
            + controls["time_weight"] * np.log(time_reduction_ratio)
            + controls["yield_weight"] * np.log(candidate_yield_ratio)
        )

        comparison_rows.append(
            {
                "industry_group": industry_group,
                "problem_class": problem_class,
                "classical_cost_index": classical_cost,
                "quantum_cost_index": quantum_cost,
                "classical_time_hours": classical_time,
                "quantum_time_hours": quantum_time,
                "classical_quality": classical_quality,
                "quantum_quality": quantum_quality,
                "classical_valid_candidates": classical_valid,
                "quantum_valid_candidates": quantum_valid,
                "quantum_algorithm_availability": quantum_availability,
                "evidence_weight": float(group["evidence_weight"].sum()),
                "cost_reduction_ratio": cost_reduction_ratio,
                "time_reduction_ratio": time_reduction_ratio,
                "candidate_yield_ratio": candidate_yield_ratio,
                "quality_adjusted_gain": quality_adjusted_gain,
                "source_key": " | ".join(group["source_key"].astype(str).tolist()),
                "note": "benchmark_evidence から自動生成",
            }
        )

    if not comparison_rows:
        raise ValueError("benchmark_evidence から比較表を生成できなかった。")
    return pd.DataFrame(comparison_rows)


def build_industry_translation(
    comparison: pd.DataFrame,
    translation_parameters: pd.DataFrame,
) -> pd.DataFrame:
    industry_gain_records = []
    for industry_group, group in comparison.groupby("industry_group"):
        industry_gain_records.append(
            {
                "industry_group": industry_group,
                "industry_gain": weighted_mean(group["quality_adjusted_gain"], group["evidence_weight"]),
            }
        )
    industry_gain = pd.DataFrame(industry_gain_records)

    merged = translation_parameters.merge(industry_gain, on="industry_group", how="left")
    if merged["industry_gain"].isna().any():
        missing = merged.loc[merged["industry_gain"].isna(), "industry_group"].tolist()
        raise ValueError(f"性能改善度を計算できない産業群がある: {missing}")

    records = []
    for _, row in merged.iterrows():
        for scenario in ["low", "base", "high"]:
            multiplier = float(row[f"{scenario}_multiplier"])
            scenario_adjusted_gain = float(row["industry_gain"]) * multiplier
            lightweighting_rate = float(row["max_lightweighting_rate"]) * (
                1.0 - np.exp(-float(row["response_curvature"]) * scenario_adjusted_gain)
            )
            efficiency_improvement_rate = float(row["efficiency_translation"]) * lightweighting_rate
            records.append(
                {
                    "industry_group": row["industry_group"],
                    "scenario": scenario,
                    "industry_gain": float(row["industry_gain"]),
                    "scenario_adjusted_gain": scenario_adjusted_gain,
                    "lightweighting_rate": lightweighting_rate,
                    "efficiency_improvement_rate": efficiency_improvement_rate,
                }
            )
    return pd.DataFrame(records)


def fit_ppml(od_data: pd.DataFrame) -> Tuple[sm.GLM, pd.DataFrame, float]:
    required_columns = {
        "origin_region", "city", "industry_group", "distance_km", "car_dependency",
        "time_cost", "non_energy_cost", "base_energy_cost_per_km", "flow_count"
    }
    missing = required_columns - set(od_data.columns)
    if missing:
        raise ValueError(f"od_flow に必要な列が不足している: {sorted(missing)}")

    data = od_data.copy()
    data["energy_cost_classical"] = (
        data["distance_km"] * data["car_dependency"] * data["base_energy_cost_per_km"]
    )
    data["generalized_cost_classical"] = (
        data["time_cost"] + data["non_energy_cost"] + data["energy_cost_classical"]
    )
    data["log_cost"] = np.log(data["generalized_cost_classical"])
    car_dependency_mean = float(data["car_dependency"].mean())
    data["car_dep_centered"] = data["car_dependency"] - car_dependency_mean
    data["car_dep_centered_log_cost"] = data["car_dep_centered"] * data["log_cost"]

    formula = (
        "flow_count ~ 0 + "
        "C(industry_group):log_cost + "
        "C(industry_group):car_dep_centered_log_cost + "
        "C(origin_region):C(industry_group) + "
        "C(city):C(industry_group)"
    )

    model = smf.glm(formula=formula, data=data, family=sm.families.Poisson())
    result = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": data["origin_region"]},
        maxiter=500,
        disp=0,
    )
    return result, data, car_dependency_mean


def coefficient_table(result, industries: list[str]) -> pd.DataFrame:
    log_cost_key = lambda g: f"C(industry_group)[{g}]:log_cost"
    interaction_key = lambda g: f"C(industry_group)[{g}]:car_dep_centered_log_cost"

    rows = []
    for industry_group in industries:
        rows.append(
            {
                "industry_group": industry_group,
                "estimated_log_cost_elasticity_at_mean_car_dependency": float(result.params[log_cost_key(industry_group)]),
                "estimated_additional_sensitivity_from_car_dependency": float(result.params[interaction_key(industry_group)]),
                "standard_error_log_cost": float(result.bse[log_cost_key(industry_group)]),
                "standard_error_interaction": float(result.bse[interaction_key(industry_group)]),
            }
        )
    return pd.DataFrame(rows)


def apply_counterfactual(
    result,
    fitted_od_data: pd.DataFrame,
    industry_translation: pd.DataFrame,
    scenario: str,
    car_dependency_mean: float,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    scenario = scenario.lower()
    scenario_rows = industry_translation[industry_translation["scenario"].str.lower() == scenario]
    if scenario_rows.empty:
        raise ValueError(f"指定したシナリオが存在しない: {scenario}")
    efficiency_map = dict(
        zip(
            scenario_rows["industry_group"],
            scenario_rows["efficiency_improvement_rate"],
        )
    )

    data = fitted_od_data.copy()
    data["efficiency_improvement_rate"] = data["industry_group"].map(efficiency_map).astype(float)
    data["energy_cost_quantum"] = data["energy_cost_classical"] * (1.0 - data["efficiency_improvement_rate"])
    data["generalized_cost_quantum"] = (
        data["time_cost"] + data["non_energy_cost"] + data["energy_cost_quantum"]
    )

    classical_prediction_data = data.copy()
    classical_prediction_data["log_cost"] = np.log(classical_prediction_data["generalized_cost_classical"])
    classical_prediction_data["car_dep_centered"] = classical_prediction_data["car_dependency"] - car_dependency_mean
    classical_prediction_data["car_dep_centered_log_cost"] = (
        classical_prediction_data["car_dep_centered"] * classical_prediction_data["log_cost"]
    )
    data["predicted_classical"] = result.predict(classical_prediction_data)

    quantum_prediction_data = data.copy()
    quantum_prediction_data["log_cost"] = np.log(quantum_prediction_data["generalized_cost_quantum"])
    quantum_prediction_data["car_dep_centered"] = quantum_prediction_data["car_dependency"] - car_dependency_mean
    quantum_prediction_data["car_dep_centered_log_cost"] = (
        quantum_prediction_data["car_dep_centered"] * quantum_prediction_data["log_cost"]
    )
    data["predicted_quantum"] = result.predict(quantum_prediction_data)

    data["delta_flow"] = data["predicted_quantum"] - data["predicted_classical"]
    data["pct_change"] = np.where(
        data["predicted_classical"] > 0,
        data["delta_flow"] / data["predicted_classical"],
        np.nan,
    )
    data["scenario"] = scenario

    by_city_industry = (
        data.groupby(["scenario", "city", "industry_group"], as_index=False)
        .agg(
            predicted_classical=("predicted_classical", "sum"),
            predicted_quantum=("predicted_quantum", "sum"),
            delta_flow=("delta_flow", "sum"),
        )
    )
    by_city_industry["pct_change"] = np.where(
        by_city_industry["predicted_classical"] > 0,
        by_city_industry["delta_flow"] / by_city_industry["predicted_classical"],
        np.nan,
    )
    return data, by_city_industry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, default=".", help="入力ファイルがあるディレクトリ")
    parser.add_argument("--output_dir", type=str, default="./model_output", help="出力先ディレクトリ")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    evidence = pd.read_csv(input_dir / "benchmark_evidence_demo.csv")
    od_data = pd.read_csv(input_dir / "od_flow_demo.csv")
    translation_parameters = pd.read_csv(input_dir / "translation_parameters_demo.csv")
    controls = load_controls(input_dir / "model_controls.csv")

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
    summary_lines.append("量子条件の反実仮想モデルを実行した。")
    summary_lines.append("")
    summary_lines.append("主要な推定係数")
    for _, row in coefficients.iterrows():
        summary_lines.append(
            f"- {row['industry_group']}: 平均自動車依存度における一般化交通費弾力性 = "
            f"{row['estimated_log_cost_elasticity_at_mean_car_dependency']:.3f}, "
            f"自動車依存度の追加感応度 = {row['estimated_additional_sensitivity_from_car_dependency']:.3f}"
        )
    summary_lines.append("")
    base_results = results_by_city_industry[results_by_city_industry["scenario"] == "base"].copy()
    base_results = base_results.sort_values("pct_change", ascending=False).head(10)
    summary_lines.append("基準シナリオで変化率が大きい都市×産業群")
    for _, row in base_results.iterrows():
        summary_lines.append(
            f"- {row['city']} / {row['industry_group']}: "
            f"差分 = {row['delta_flow']:.3f}, 変化率 = {row['pct_change']:.4%}"
        )

    (output_dir / "run_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"出力先: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
