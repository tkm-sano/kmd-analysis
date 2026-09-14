# Researcher arbitrariness review

| Choice | Risk | Pre-fix rule |
|---|---|---|
| Clustering method | HIGH | Freeze service-time/density hierarchy first; choose deterministic medoid implementation |
| Number of clusters | HIGH | Data-derived quantile cells and nonempty-cell merge rule |
| Representative rule | HIGH | Weighted standardized feature centroid medoid, SHA tie-break |
| Customer count | HIGH | Derive from selected cluster and resource gate; never globally assume n |
| Demand proxy/unit | HIGH | Adopt one documented q unit and transformation before execution |
| Capacity | HIGH | Same-unit Q authority, fixed before sampling/results |
| Vehicle count | HIGH | `m=ceil(sum q/Q)`; spare fleet is a new protocol |
| QUBO encoding | MEDIUM | Position-based primary, arc/assignment cross-check where gated |
| Penalty | HIGH | Instance-specific sufficient bound or stop |
| Sample seed | MEDIUM | Freeze seed and source SHA before selection |
| Aggregation weight | HIGH | Choose customer-share or demand-share by estimand before results |

