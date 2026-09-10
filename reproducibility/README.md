# Current Reproducibility Boundary

This directory contains the governed configuration and Git-ignored runtime outputs for the current SUMO traffic-simulation research line.

```text
reproducibility/
├── config/traffic_simulation/       # machine-readable current specifications
└── outputs/traffic_simulation/      # regenerable local run products
```

The prior non-SUMO synthetic EVRP route-proxy package is isolated under [`../legacy/non_sumo_route_proxy_analysis/`](../legacy/non_sumo_route_proxy_analysis/). Its inputs, outputs, environment, notebook, and tests are not part of the current SUMO execution path.

## Reduced quantum-stage evidence

Generated stage artifacts remain Git-ignored runtime products; authority is
established by run ID, SHA-256, source/evidence commit lineage, and the status
record in [`../EVRP_EXECUTION_PLAN.md`](../EVRP_EXECUTION_PLAN.md).

- R21 authoritative run: `outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/`
  (`validation_results.json` SHA-256 `c4baeead366ea2f750cd4ecdd18acc507746dfecd744d0803ed74b5bbb46049f`,
  `manifest.json` SHA-256 `9a6fc459ef1f5cbf1824b9b0197a2f56f9d67cc88de18bd6bcd8ff7f575691a2`).
- R22 authoritative run: `outputs/traffic_simulation/r22_ising_conversion/20260910_formal_reduced_v1/`
  (`conversion_results.json` SHA-256 `1b6015bcaf38d58fb98a743f47346be9e68601c0b0f7c09567ca77186ea26cea`,
  `manifest.json` SHA-256 `2bd1bed556b265cc4b6f555497f78e1e432c8d22dabfcccb722fe0faf0da46d9`).

These artifacts validate only the initial reduced route-ordering scope. R23
implementation smoke outputs are non-authoritative and must not be substituted
for the governed pilot or formal baseline.
