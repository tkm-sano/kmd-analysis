# Reduction strategy comparison

| Strategy | Ota representativeness | Reproducibility | CVRP validity | Exact/QUBO scale | Decision |
|---|---|---|---|---|---|
| A. Random small-CVRP sampling | Low and unstable; can miss geography, density, depot relation | Seed-dependent | Valid only for selected points | Easy | Reject as primary; retain only as sensitivity |
| B. Spatial representative subproblem | Medium to high if spatial coverage and demand are jointly checked | High with fixed clustering and medoid rule | Valid | Depends on selected cluster size | Component of R24 |
| C. Hierarchical service-area decomposition | High: retains system population, depot relation, spatial and demand strata | High after rules are frozen | Valid sub-CVRPs with explicit boundary | Controlled at second stage | **Recommended** |

K-means/k-medoids, grids, and road-network clustering are implementation candidates inside B/C. The method is selected for population and demand representation before quantum tractability is assessed. Qubit limits may reduce the number of sub-instances evaluated, but may not change the population or selection rule.

