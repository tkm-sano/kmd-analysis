import pandas as pd

def build_unit_costs(engineering_df: pd.DataFrame, energy_df: pd.DataFrame) -> pd.DataFrame:
    df = engineering_df.merge(energy_df, on="year", how="left")
    # use gasoline as default energy price for baseline
    df["unit_energy_price"] = df["gasoline_jpy_per_l"]
    df["unit_cost"] = df["unit_energy_price"] * df["baseline_energy_intensity_e0"] * (1 - df["fuel_efficiency_gain"])
    return df
