# Non-SUMO Route-Proxy Analysis Archive

This directory contains the synthetic EVRP route-proxy analysis that preceded the governed SUMO traffic-simulation workflow. Its data, code, reviewed figures, and reproduction package are kept together so they cannot be mistaken for current SUMO inputs or formal simulation results.

## Status and interpretation boundary

- Archive status: retained for provenance and historical reproduction.
- Traffic simulator: none. This analysis does not use SUMO, TraCI, sumolib, or `netconvert`.
- Route construction: KMeans vehicle assignment followed by a nearest-neighbour visit-order proxy.
- Distance: Haversine distance multiplied by a fixed road-distance factor.
- Travel time: proxy distance divided by a fixed assumed speed.
- Optimization: not an EVRP optimum and not a classical-versus-QAOA solver comparison.
- Formal use: prohibited for claims about observed Tokyo delivery performance, road-network travel time, congestion, or SUMO outcomes.

The retained CSVs explicitly identify these outputs as synthetic route-proxy evaluations. They may be used to explain the earlier exploratory stage, reproduce its calculations, or compare how the research design changed. They must not be mixed with `formal_accepted` SUMO outputs.

## Contents

```text
legacy/non_sumo_route_proxy_analysis/
├── data/processed/
│   ├── evrp_constraint_gap_inputs/  # frozen analysis-specific inputs
│   ├── scenario/                    # synthetic customers and configurations
│   ├── route_proxy/                 # Haversine-based route proxies
│   ├── constraints/                 # proxy constraint evaluations
│   ├── charger_access/              # proxy charger-access evaluations
│   └── quantum_gap/                 # literature-to-requirement gap tables
├── src/
│   ├── scenario_generation/
│   ├── constraint_evaluation/
│   ├── sensitivity/
│   ├── literature_analysis/
│   └── visualization/
├── outputs/tables/png/              # curated historical table images
└── reproducibility/                 # frozen notebook, environment, tests, and run outputs
```

Shared public-data inputs, including population, charging, vehicle, and literature records, remain in their governed repository locations because the current SUMO study also uses them. This archive records references to those shared inputs rather than duplicating them.

## Reproduction

The frozen third-party audit package is under [`reproducibility/`](reproducibility/). Its generated products remain excluded from Git. Run the archived checks from the repository root with:

```bash
docker compose run --rm analysis \
  pytest -q legacy/non_sumo_route_proxy_analysis/reproducibility/tests/test_audit.py
```

Some retained manifests and executed-notebook outputs contain former repository-relative paths. Those strings are historical evidence of the recorded run, not current path instructions. Current commands and source code use the consolidated paths above.
