import pandas as pd
import yaml
from pathlib import Path

def build_search_performance(compute_df: pd.DataFrame, config_path: Path) -> pd.DataFrame:
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    w = cfg["score_weights"]
    df = compute_df.copy()
    df["search_performance_index"] = (
        w["search_space_score"] * df["search_space_score"]
        + w["evaluation_accuracy_score"] * df["evaluation_accuracy_score"]
        + w["engineering_validity_score"] * df["engineering_validity_score"]
    )
    # weighted by evidence weight
    df["search_performance_index"] = df["search_performance_index"] * df["evidence_weight"]
    panel = (
        df.groupby(["industry_group_id", "year", "compute_condition"], as_index=False)
          .agg(search_performance_index=("search_performance_index", "mean"),
               avg_quantum_algorithm_availability=("quantum_algorithm_availability","mean"),
               avg_classical_resource_level=("classical_resource_level","mean"),
               avg_quantum_resource_level=("quantum_resource_level","mean"))
    )
    return panel
