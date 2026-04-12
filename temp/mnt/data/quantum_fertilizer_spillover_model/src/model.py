from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from .utils import normal_cdf


@dataclass
class ScenarioOutputs:
    transmission: dict[str, float]
    summary: dict[str, float]
    group_results: pd.DataFrame
    disease_results: pd.DataFrame


class QuantumFoodHealthModel:
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def compute_transmission(self) -> dict[str, float]:
        p = self.params
        demand_abs = abs(float(p["vegetable_demand_elasticity"]))
        supply = float(p["vegetable_supply_elasticity"])

        fertilizer_energy_reduction_pct = (
            float(p["quantum_nitrogen_efficiency_gain_pct"])
            * float(p["nitrogen_to_fertilizer_energy_linkage"])
        )
        fertilizer_price_reduction_pct = (
            fertilizer_energy_reduction_pct
            * float(p["energy_cost_share_in_fertilizer"])
            * float(p["energy_to_fertilizer_price_pass_through"])
        )
        vegetable_cost_reduction_pct = (
            fertilizer_price_reduction_pct
            * float(p["fertilizer_cost_share_in_vegetable_price"])
            * float(p["fertilizer_to_vegetable_price_pass_through"])
        )

        price_change_pct = -(supply / (supply + demand_abs)) * vegetable_cost_reduction_pct
        quantity_change_pct = (
            (supply * demand_abs) / (supply + demand_abs)
        ) * vegetable_cost_reduction_pct

        baseline_price = float(p["baseline_vegetable_price_jpy_per_kg"])
        new_price = baseline_price * (1.0 + price_change_pct)

        return {
            "quantum_nitrogen_efficiency_gain_pct": float(p["quantum_nitrogen_efficiency_gain_pct"]),
            "fertilizer_energy_reduction_pct": fertilizer_energy_reduction_pct,
            "fertilizer_price_reduction_pct": fertilizer_price_reduction_pct,
            "vegetable_cost_reduction_pct": vegetable_cost_reduction_pct,
            "vegetable_price_change_pct": price_change_pct,
            "vegetable_quantity_change_pct": quantity_change_pct,
            "baseline_vegetable_price_jpy_per_kg": baseline_price,
            "new_vegetable_price_jpy_per_kg": new_price,
        }

    def compute_group_results(
        self,
        groups: pd.DataFrame,
        transmission: dict[str, float],
    ) -> pd.DataFrame:
        p = self.params
        demand_abs = abs(float(p["vegetable_demand_elasticity"]))
        recommended = float(p["recommended_intake_g_per_day"])
        price_change_abs = abs(transmission["vegetable_price_change_pct"])
        target_quantity_growth = float(transmission["vegetable_quantity_change_pct"])

        df = groups.copy()
        df["baseline_total_intake_g_per_day"] = df["population"] * df["baseline_mean_intake_g_per_day"]

        df["raw_growth_pct"] = (
            demand_abs * price_change_abs * df["price_sensitivity_multiplier"]
        )
        df["raw_new_mean_intake_g_per_day"] = (
            df["baseline_mean_intake_g_per_day"] * (1.0 + df["raw_growth_pct"])
        )

        baseline_total = df["baseline_total_intake_g_per_day"].sum()
        raw_total = (df["population"] * df["raw_new_mean_intake_g_per_day"]).sum()
        target_total = baseline_total * (1.0 + target_quantity_growth)

        if raw_total > baseline_total:
            scale = (target_total - baseline_total) / (raw_total - baseline_total)
        else:
            scale = 1.0
        scale = max(scale, 0.0)

        df["new_mean_intake_g_per_day"] = (
            df["baseline_mean_intake_g_per_day"]
            + (df["raw_new_mean_intake_g_per_day"] - df["baseline_mean_intake_g_per_day"]) * scale
        )
        df["intake_change_g_per_day"] = (
            df["new_mean_intake_g_per_day"] - df["baseline_mean_intake_g_per_day"]
        )

        def threshold_share(mean: float, std: float) -> float:
            z = (recommended - mean) / std
            return 1.0 - normal_cdf(z)

        df["baseline_recommended_share"] = df.apply(
            lambda row: threshold_share(
                float(row["baseline_mean_intake_g_per_day"]),
                float(row["std_intake_g_per_day"]),
            ),
            axis=1,
        )
        df["new_recommended_share"] = df.apply(
            lambda row: threshold_share(
                float(row["new_mean_intake_g_per_day"]),
                float(row["std_intake_g_per_day"]),
            ),
            axis=1,
        )
        df["baseline_population_meeting_recommendation"] = (
            df["population"] * df["baseline_recommended_share"]
        )
        df["new_population_meeting_recommendation"] = (
            df["population"] * df["new_recommended_share"]
        )

        return df

    def compute_disease_results(
        self,
        disease_df: pd.DataFrame,
        group_results: pd.DataFrame,
    ) -> pd.DataFrame:
        total_population = float(group_results["population"].sum())
        baseline_avg_intake = (
            group_results["population"] * group_results["baseline_mean_intake_g_per_day"]
        ).sum() / total_population
        new_avg_intake = (
            group_results["population"] * group_results["new_mean_intake_g_per_day"]
        ).sum() / total_population
        avg_intake_delta = new_avg_intake - baseline_avg_intake

        df = disease_df.copy()
        df["baseline_cases"] = df["baseline_incidence_rate"] * total_population
        df["risk_reduction_pct"] = (
            df["risk_reduction_per_10g"] * (avg_intake_delta / 10.0)
        ).clip(lower=0.0, upper=df["max_risk_reduction"])
        df["new_cases"] = df["baseline_cases"] * (1.0 - df["risk_reduction_pct"])
        df["cases_reduction"] = df["baseline_cases"] - df["new_cases"]
        df["daly_reduction"] = df["baseline_dalys"] * df["risk_reduction_pct"]
        df["new_dalys"] = df["baseline_dalys"] - df["daly_reduction"]
        df["medical_cost_reduction_jpy"] = (
            df["annual_medical_cost_jpy"] * df["risk_reduction_pct"]
        )
        df["new_annual_medical_cost_jpy"] = (
            df["annual_medical_cost_jpy"] - df["medical_cost_reduction_jpy"]
        )
        return df

    def summarize(
        self,
        transmission: dict[str, float],
        group_results: pd.DataFrame,
        disease_results: pd.DataFrame,
    ) -> dict[str, float]:
        p = self.params
        total_population = float(group_results["population"].sum())

        baseline_avg_intake = (
            group_results["population"] * group_results["baseline_mean_intake_g_per_day"]
        ).sum() / total_population
        new_avg_intake = (
            group_results["population"] * group_results["new_mean_intake_g_per_day"]
        ).sum() / total_population

        baseline_recommended_share = (
            group_results["baseline_population_meeting_recommendation"].sum() / total_population
        )
        new_recommended_share = (
            group_results["new_population_meeting_recommendation"].sum() / total_population
        )

        baseline_annual_quantity_tons = (
            group_results["population"] * group_results["baseline_mean_intake_g_per_day"]
        ).sum() * 365.0 / 1_000_000.0
        new_annual_quantity_tons = (
            group_results["population"] * group_results["new_mean_intake_g_per_day"]
        ).sum() * 365.0 / 1_000_000.0

        total_daly_baseline = float(disease_results["baseline_dalys"].sum())
        total_daly_new = float(disease_results["new_dalys"].sum())
        total_daly_reduction = float(disease_results["daly_reduction"].sum())

        healthy_life_gain_years = total_daly_reduction / total_population
        healthy_life_baseline = float(p["baseline_healthy_life_expectancy_proxy_years"])
        healthy_life_new = healthy_life_baseline + healthy_life_gain_years

        baseline_premium = float(p["baseline_social_insurance_premium_total_jpy"])
        premium_reduction = float(disease_results["medical_cost_reduction_jpy"].sum()) * float(
            p["medical_cost_to_premium_linkage"]
        )
        new_premium = baseline_premium - premium_reduction

        return {
            "population_total": total_population,
            "baseline_avg_intake_g_per_day": baseline_avg_intake,
            "new_avg_intake_g_per_day": new_avg_intake,
            "avg_intake_change_g_per_day": new_avg_intake - baseline_avg_intake,
            "baseline_recommended_share": baseline_recommended_share,
            "new_recommended_share": new_recommended_share,
            "recommended_share_change_pct_pt": (new_recommended_share - baseline_recommended_share) * 100.0,
            "baseline_annual_quantity_tons": baseline_annual_quantity_tons,
            "new_annual_quantity_tons": new_annual_quantity_tons,
            "annual_quantity_change_tons": new_annual_quantity_tons - baseline_annual_quantity_tons,
            "total_daly_baseline": total_daly_baseline,
            "total_daly_new": total_daly_new,
            "total_daly_reduction": total_daly_reduction,
            "healthy_life_expectancy_proxy_baseline_years": healthy_life_baseline,
            "healthy_life_expectancy_proxy_new_years": healthy_life_new,
            "healthy_life_expectancy_proxy_gain_days": healthy_life_gain_years * 365.0,
            "social_insurance_premium_baseline_jpy": baseline_premium,
            "social_insurance_premium_new_jpy": new_premium,
            "social_insurance_premium_reduction_jpy": premium_reduction,
        }

    def run(self, groups: pd.DataFrame, disease_df: pd.DataFrame) -> ScenarioOutputs:
        transmission = self.compute_transmission()
        group_results = self.compute_group_results(groups, transmission)
        disease_results = self.compute_disease_results(disease_df, group_results)
        summary = self.summarize(transmission, group_results, disease_results)
        return ScenarioOutputs(
            transmission=transmission,
            summary=summary,
            group_results=group_results,
            disease_results=disease_results,
        )
