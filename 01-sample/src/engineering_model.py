import pandas as pd
import numpy as np
import yaml
from pathlib import Path

def translate_to_engineering(
    search_panel: pd.DataFrame,
    industry_df: pd.DataFrame,
    config_path: Path,
    adoption_multiplier: float = 1.0,
) -> pd.DataFrame:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    intercept = cfg["engineering"]["search_to_lambda_intercept"]
    slope = cfg["engineering"]["search_to_lambda_slope"]
    alpha = cfg["engineering"]["weight_to_fe_alpha_center"]
    df = search_panel.merge(industry_df, on="industry_group_id", how="left")
    df["effective_adoption_rate"] = (df["adoption_rate"] * adoption_multiplier).clip(lower=0, upper=1)
    df["lambda_rate_raw"] = intercept + slope * df["search_performance_index"]
    df["lambda_rate"] = df["lambda_rate_raw"].clip(lower=0, upper=df["lambda_max"])
    df["adoption_realization_factor"] = np.sqrt(df["effective_adoption_rate"])
    df["fuel_efficiency_gain"] = alpha * df["lambda_rate"] * df["adoption_realization_factor"]
    return df
