from pathlib import Path
import yaml
from .io_loader import load_raw_inputs
from .benchmark_model import build_search_performance
from .engineering_model import translate_to_engineering
from .cost_model import build_unit_costs
from .flow_model import simulate_flows
from .anova_model import run_two_way_anova
from .plotter import (
    plot_anova_effects,
    plot_city_industry_heatmap,
    plot_city_inflow,
    plot_industry_diff,
    plot_monte_carlo_delta,
    plot_sensitivity_levers,
)
from .scenario_analysis import build_pipeline_outputs, run_monte_carlo, run_sensitivity_suite
from .config import BASE_DIR, PROCESSED_DIR, OUTPUT_TABLES, OUTPUT_FIGURES
from .utils import safe_to_parquet

def main():
    cfg_path = BASE_DIR / "src" / "config.yaml"
    cfg = yaml.safe_load(open(cfg_path, "r", encoding="utf-8"))
    years = set(cfg["simulation"]["years"])
    compute_conditions = set(cfg["simulation"]["compute_conditions"])

    data = load_raw_inputs()
    data["compute"] = data["compute"][
        data["compute"]["year"].isin(years)
        & data["compute"]["compute_condition"].isin(compute_conditions)
    ].copy()
    data["energy"] = data["energy"][data["energy"]["year"].isin(years)].copy()

    outputs = build_pipeline_outputs(data, cfg_path)
    bench = outputs["bench"]
    safe_to_parquet(bench, PROCESSED_DIR / "benchmark_panel.parquet")
    bench.to_csv(PROCESSED_DIR / "benchmark_panel.csv", index=False)

    eng = outputs["eng"]
    safe_to_parquet(eng, PROCESSED_DIR / "engineering_panel.parquet")
    eng.to_csv(PROCESSED_DIR / "engineering_panel.csv", index=False)

    cost = outputs["cost"]
    safe_to_parquet(cost, PROCESSED_DIR / "cost_panel.parquet")
    cost.to_csv(PROCESSED_DIR / "cost_panel.csv", index=False)

    sim = outputs["sim"]
    safe_to_parquet(sim, PROCESSED_DIR / "inflow_simulated.parquet")
    sim.to_csv(PROCESSED_DIR / "anova_input.csv", index=False)
    sim.to_csv(PROCESSED_DIR / "inflow_simulated.csv", index=False)

    anova = run_two_way_anova(sim)
    anova.to_csv(OUTPUT_TABLES / "anova_results.csv", index=False)

    bench.to_csv(OUTPUT_TABLES / "benchmark_summary.csv", index=False)
    eng.to_csv(OUTPUT_TABLES / "engineering_summary.csv", index=False)
    cost.to_csv(OUTPUT_TABLES / "cost_summary.csv", index=False)
    sim.groupby(["destination_city_id","industry_group_id","compute_condition"], as_index=False)["inflow_sim"].sum().to_csv(
        OUTPUT_TABLES / "inflow_summary.csv", index=False
    )
    sensitivity_df, sensitivity_industry_df = run_sensitivity_suite(data, cfg_path)
    sensitivity_df.to_csv(OUTPUT_TABLES / "sensitivity_summary.csv", index=False)
    sensitivity_industry_df.to_csv(OUTPUT_TABLES / "sensitivity_industry_summary.csv", index=False)
    monte_carlo_df, monte_carlo_summary = run_monte_carlo(data, cfg_path)
    monte_carlo_df.to_csv(OUTPUT_TABLES / "monte_carlo_overall.csv", index=False)
    monte_carlo_summary.to_csv(OUTPUT_TABLES / "monte_carlo_summary.csv", index=False)

    plot_city_inflow(sim, OUTPUT_FIGURES / "city_inflow.png")
    plot_industry_diff(sim, OUTPUT_FIGURES / "industry_inflow_diff.png")
    plot_city_industry_heatmap(sim, OUTPUT_FIGURES / "city_industry_heatmap.png")
    plot_anova_effects(anova, OUTPUT_FIGURES / "anova_effect_sizes.png")
    plot_sensitivity_levers(sensitivity_df, OUTPUT_FIGURES / "sensitivity_levers.png")
    plot_monte_carlo_delta(monte_carlo_df, OUTPUT_FIGURES / "monte_carlo_delta.png")
    print("Pipeline completed.")

if __name__ == "__main__":
    main()
