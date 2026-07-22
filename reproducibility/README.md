# Current Reproducibility Boundary

This directory contains the governed configuration and Git-ignored runtime outputs for the current SUMO traffic-simulation research line.

```text
reproducibility/
├── config/traffic_simulation/       # machine-readable current specifications
└── outputs/traffic_simulation/      # regenerable local run products
```

The prior non-SUMO synthetic EVRP route-proxy package is isolated under [`../legacy/non_sumo_route_proxy_analysis/`](../legacy/non_sumo_route_proxy_analysis/). Its inputs, outputs, environment, notebook, and tests are not part of the current SUMO execution path.
