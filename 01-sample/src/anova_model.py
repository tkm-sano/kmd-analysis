import pandas as pd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

def partial_eta_squared(anova_table: pd.DataFrame, effect_name: str) -> float:
    row = anova_table.loc[effect_name]
    ss_effect = row["sum_sq"]
    ss_error = anova_table.loc["Residual", "sum_sq"]
    return float(ss_effect / (ss_effect + ss_error)) if (ss_effect + ss_error) != 0 else 0.0

def run_two_way_anova(sim_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for g, sub in sim_df.groupby("industry_group_id"):
        df = sub[["destination_city_id", "compute_condition", "log_inflow_sim"]].copy()
        df["destination_city_id"] = df["destination_city_id"].map(str).astype(object)
        df["compute_condition"] = df["compute_condition"].map(str).astype(object)
        df["log_inflow_sim"] = df["log_inflow_sim"].astype(float)
        model = ols("log_inflow_sim ~ C(destination_city_id) * C(compute_condition)", data=df).fit()
        table = anova_lm(model, typ=2)
        for eff in table.index:
            rows.append({
                "industry_group_id": g,
                "effect": eff,
                "sum_sq": table.loc[eff, "sum_sq"],
                "df": table.loc[eff, "df"],
                "F": table.loc[eff, "F"] if "F" in table.columns else None,
                "PR(>F)": table.loc[eff, "PR(>F)"] if "PR(>F)" in table.columns else None,
                "partial_eta2": partial_eta_squared(table, eff) if eff != "Residual" else None
            })
    return pd.DataFrame(rows)
