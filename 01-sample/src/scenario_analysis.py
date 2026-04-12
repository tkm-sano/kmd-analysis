from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from .benchmark_model import build_search_performance
from .engineering_model import translate_to_engineering
from .cost_model import build_unit_costs
from .flow_model import simulate_flows


def build_pipeline_outputs(
    data: dict,
    config_path: Path,
    search_multiplier: float = 1.0,
    adoption_multiplier: float = 1.0,
    elasticity_multiplier: float = 1.0,
) -> dict:
    bench = build_search_performance(data["compute"], config_path, search_multiplier=search_multiplier)
    eng = translate_to_engineering(
        bench,
        data["industry"],
        config_path,
        adoption_multiplier=adoption_multiplier,
    )
    cost = build_unit_costs(eng, data["energy"])
    sim = simulate_flows(
        data["base_inflow"],
        cost,
        data["city"],
        data["city_cond"],
        data["industry"],
        config_path,
        elasticity_multiplier=elasticity_multiplier,
    )
    return {"bench": bench, "eng": eng, "cost": cost, "sim": sim}


def _overall_delta(sim_df: pd.DataFrame) -> tuple[float, float, float]:
    totals = sim_df.groupby("compute_condition")["inflow_sim"].sum()
    classical = float(totals.get("classical_only", 0.0))
    quantum = float(totals.get("quantum_enabled", 0.0))
    delta_abs = quantum - classical
    delta_pct = (delta_abs / classical * 100) if classical else 0.0
    return classical, quantum, delta_abs, delta_pct


def run_sensitivity_suite(data: dict, config_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    lever_levels = {
        "search_multiplier": cfg["sensitivity"]["search_multipliers"],
        "adoption_multiplier": cfg["sensitivity"]["adoption_multipliers"],
        "elasticity_multiplier": cfg["sensitivity"]["elasticity_multipliers"],
    }
    overall_rows = []
    industry_rows = []

    for lever, levels in lever_levels.items():
        for level in levels:
            params = {
                "search_multiplier": 1.0,
                "adoption_multiplier": 1.0,
                "elasticity_multiplier": 1.0,
            }
            params[lever] = float(level)
            outputs = build_pipeline_outputs(data, config_path, **params)
            classical, quantum, delta_abs, delta_pct = _overall_delta(outputs["sim"])
            overall_rows.append({
                "lever": lever,
                "level": level,
                "classical_total_inflow": classical,
                "quantum_total_inflow": quantum,
                "delta_abs": delta_abs,
                "delta_pct": delta_pct,
            })

            industry = outputs["sim"].groupby(["industry_group_id", "compute_condition"], as_index=False)["inflow_sim"].sum()
            pivot = industry.pivot(index="industry_group_id", columns="compute_condition", values="inflow_sim").reset_index()
            pivot["delta_abs"] = pivot["quantum_enabled"] - pivot["classical_only"]
            pivot["delta_pct"] = pivot["delta_abs"] / pivot["classical_only"] * 100
            for _, row in pivot.iterrows():
                industry_rows.append({
                    "lever": lever,
                    "level": level,
                    "industry_group_id": row["industry_group_id"],
                    "classical_total_inflow": row["classical_only"],
                    "quantum_total_inflow": row["quantum_enabled"],
                    "delta_abs": row["delta_abs"],
                    "delta_pct": row["delta_pct"],
                })

    return pd.DataFrame(overall_rows), pd.DataFrame(industry_rows)


def run_monte_carlo(data: dict, config_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    mc_cfg = cfg["monte_carlo"]
    sim_cfg = cfg["simulation"]
    rng = np.random.default_rng(sim_cfg["random_seed"])
    rows = []

    for replicate in range(sim_cfg["n_replicates"]):
        search_multiplier = max(0.5, rng.normal(1.0, mc_cfg["search_multiplier_std"]))
        adoption_multiplier = max(0.5, rng.normal(1.0, mc_cfg["adoption_multiplier_std"]))
        elasticity_multiplier = max(0.3, rng.normal(1.0, mc_cfg["elasticity_multiplier_std"]))

        outputs = build_pipeline_outputs(
            data,
            config_path,
            search_multiplier=search_multiplier,
            adoption_multiplier=adoption_multiplier,
            elasticity_multiplier=elasticity_multiplier,
        )
        classical, quantum, delta_abs, delta_pct = _overall_delta(outputs["sim"])
        rows.append({
            "replicate": replicate + 1,
            "search_multiplier": search_multiplier,
            "adoption_multiplier": adoption_multiplier,
            "elasticity_multiplier": elasticity_multiplier,
            "classical_total_inflow": classical,
            "quantum_total_inflow": quantum,
            "delta_abs": delta_abs,
            "delta_pct": delta_pct,
        })

    mc_df = pd.DataFrame(rows)
    summary = pd.DataFrame([{
        "metric": "delta_abs",
        "mean": mc_df["delta_abs"].mean(),
        "std": mc_df["delta_abs"].std(ddof=1),
        "p05": mc_df["delta_abs"].quantile(0.05),
        "p50": mc_df["delta_abs"].quantile(0.50),
        "p95": mc_df["delta_abs"].quantile(0.95),
    }, {
        "metric": "delta_pct",
        "mean": mc_df["delta_pct"].mean(),
        "std": mc_df["delta_pct"].std(ddof=1),
        "p05": mc_df["delta_pct"].quantile(0.05),
        "p50": mc_df["delta_pct"].quantile(0.50),
        "p95": mc_df["delta_pct"].quantile(0.95),
    }])
    return mc_df, summary
