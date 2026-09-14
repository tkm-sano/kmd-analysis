# Hierarchical reduction design

The proposed hierarchy is `C_all -> C_s -> C_{s,r}`. First compute frozen service bands from depot shortest-path time and demand-density strata from the complete candidate population. Cross these variables only when each cell has sufficient population; otherwise merge adjacent cells by a predeclared rule and record the merge. This avoids inventing empty dense/far categories.

Within each nonempty stratum `C_s`, select a representative cluster or medoid using joint standardized features: demand density, depot travel time, travel-time quantiles, local road density, and coordinates. The second stage selects a small `C_{s,r}` for exact CVRP/QUBO evaluation while retaining its inclusion probability and expansion weight. System scale is 39,956 candidate stops; solver scale is a separate evaluation unit.

The initial proposed strata are data-derived quartiles of depot travel time crossed with data-derived demand-density tertiles, subject to the nonempty-cell merge rule. These quantiles are computed from the full population before any solver result is observed. The final number of cells is therefore data-derived, not a fixed four-cell story.

