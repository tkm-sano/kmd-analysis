import pandas as pd
import numpy as np
import yaml
from pathlib import Path

def simulate_flows(
    base_inflow: pd.DataFrame,
    cost_df: pd.DataFrame,
    city_df: pd.DataFrame,
    city_cond: pd.DataFrame,
    industry_df: pd.DataFrame,
    config_path: Path,
    elasticity_multiplier: float = 1.0,
) -> pd.DataFrame:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    theta = cfg["city_condition_theta"]
    flow_cfg = cfg["flow"]
    base = base_inflow.copy()
    cityc = city_cond.copy()
    city = city_df[["city_id", "wage_index", "agglomeration_index"]].copy()
    ind = industry_df[["industry_group_id","cost_elasticity_beta"]].copy()
    # baseline unit costs under classical_only by industry/year
    ref = cost_df[cost_df["compute_condition"]=="classical_only"][["industry_group_id","year","unit_cost"]].rename(columns={"unit_cost":"unit_cost_ref"})
    sim = base.merge(cost_df[["industry_group_id","year","compute_condition","unit_cost"]], on="industry_group_id", how="left")
    sim = sim.merge(ref, on=["industry_group_id","year"], how="left")
    sim = sim.merge(city, left_on="destination_city_id", right_on="city_id", how="left")
    sim = sim.merge(cityc, left_on="destination_city_id", right_on="city_id", how="left")
    sim = sim.merge(ind, on="industry_group_id", how="left")
    sim["condition_multiplier"] = (
        1
        + theta["it"] * (sim["it_level_index"] - 1)
        + theta["living"] * (sim["living_level_index"] - 1)
        + theta["mobility"] * (sim["mobility_infra_index"] - 1)
    )
    sim["city_attractiveness_multiplier"] = np.exp(
        flow_cfg["city_wage_attractiveness_phi"] * (sim["wage_index"] - 1)
        + flow_cfg["city_agglomeration_attractiveness_phi"] * (sim["agglomeration_index"] - 1)
    )
    sim["cost_ref"] = sim["representative_distance_km"] * sim["unit_cost_ref"]
    sim["cost_now"] = sim["representative_distance_km"] * sim["unit_cost"]
    # split baseline into car / non-car
    sim["base_car"] = sim["inflow_2025"] * sim["car_share"]
    sim["base_noncar"] = sim["inflow_2025"] * (1 - sim["car_share"])
    sim["relative_cost_change"] = (sim["cost_now"] - sim["cost_ref"]) / sim["cost_ref"]
    sim["effective_cost_elasticity_beta"] = (
        sim["cost_elasticity_beta"]
        * elasticity_multiplier
        * (
            1
            + flow_cfg["city_wage_elasticity_weight"] * (sim["wage_index"] - 1)
            + flow_cfg["city_agglomeration_elasticity_weight"] * (sim["agglomeration_index"] - 1)
        )
    )
    sim["car_response_multiplier"] = np.exp(sim["effective_cost_elasticity_beta"] * sim["relative_cost_change"])
    sim["noncar_response_multiplier"] = np.exp(
        flow_cfg["noncar_cost_sensitivity"] * sim["effective_cost_elasticity_beta"] * sim["relative_cost_change"]
    )
    sim["inflow_sim"] = (
        sim["base_noncar"] * sim["noncar_response_multiplier"] * sim["city_attractiveness_multiplier"]
        + sim["base_car"] * sim["car_response_multiplier"] * sim["condition_multiplier"] * sim["city_attractiveness_multiplier"]
    )
    sim["log_inflow_sim"] = np.log(sim["inflow_sim"].clip(lower=1e-6))
    return sim[[
        "origin_region_id","destination_city_id","industry_group_id","year","compute_condition",
        "inflow_2025","inflow_sim","log_inflow_sim","relative_cost_change","cost_ref","cost_now",
        "effective_cost_elasticity_beta","city_attractiveness_multiplier"
    ]]
