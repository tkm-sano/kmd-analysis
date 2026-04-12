import pandas as pd
from pathlib import Path
from .config import RAW_DIR

def load_raw_inputs():
    return {
        "city": pd.read_csv(RAW_DIR / "city_master.csv"),
        "industry": pd.read_csv(RAW_DIR / "industry_group_master.csv"),
        "compute": pd.read_csv(RAW_DIR / "compute_resource_conditions.csv"),
        "energy": pd.read_csv(RAW_DIR / "energy_price.csv"),
        "base_inflow": pd.read_csv(RAW_DIR / "base_inflow_2025.csv"),
        "city_cond": pd.read_csv(RAW_DIR / "city_condition_index.csv"),
        "literature": pd.read_csv(Path(__file__).resolve().parents[1] / "docs" / "literature_registry.csv"),
    }
