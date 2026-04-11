from pathlib import Path
import yaml
from .io_loader import load_raw_inputs
from .benchmark_model import build_search_performance
from .engineering_model import translate_to_engineering
from .cost_model import build_unit_costs
from .flow_model import simulate_flows
from .anova_model import run_two_way_anova
from .plotter import plot_city_inflow
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

    bench = build_search_performance(data["compute"], cfg_path)
    safe_to_parquet(bench, PROCESSED_DIR / "benchmark_panel.parquet")
    bench.to_csv(PROCESSED_DIR / "benchmark_panel.csv", index=False)

    eng = translate_to_engineering(bench, data["industry"], cfg_path)
    safe_to_parquet(eng, PROCESSED_DIR / "engineering_panel.parquet")
    eng.to_csv(PROCESSED_DIR / "engineering_panel.csv", index=False)

    cost = build_unit_costs(eng, data["energy"])
    safe_to_parquet(cost, PROCESSED_DIR / "cost_panel.parquet")
    cost.to_csv(PROCESSED_DIR / "cost_panel.csv", index=False)

    sim = simulate_flows(data["base_inflow"], cost, data["city_cond"], data["industry"], cfg_path)
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

    plot_city_inflow(sim, OUTPUT_FIGURES / "city_inflow.png")
    print("Pipeline completed.")

if __name__ == "__main__":
    main()
