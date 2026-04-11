import pandas as pd
import yaml
from pathlib import Path

def translate_to_engineering(search_panel: pd.DataFrame, industry_df: pd.DataFrame, config_path: Path) -> pd.DataFrame:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    intercept = cfg["engineering"]["search_to_lambda_intercept"]
    slope = cfg["engineering"]["search_to_lambda_slope"]
    alpha = cfg["engineering"]["weight_to_fe_alpha_center"]
    df = search_panel.merge(industry_df, on="industry_group_id", how="left")
    df["lambda_rate_raw"] = intercept + slope * df["search_performance_index"]
    df["lambda_rate"] = (df["lambda_rate_raw"].clip(lower=0) * df["adoption_rate"]).clip(upper=df["lambda_max"])
    df["fuel_efficiency_gain"] = alpha * df["lambda_rate"]
    return df
