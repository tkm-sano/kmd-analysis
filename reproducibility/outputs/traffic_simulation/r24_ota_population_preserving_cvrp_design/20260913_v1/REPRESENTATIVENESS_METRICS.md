# Representativeness metrics

The required pre-run diagnostics compare each selected `C_s` and `C_{s,r}` with `C_all` and its parent stratum: customer count/share, demand sum/share, demand quantiles, mean and median depot travel time, travel-time quantiles, pairwise road-distance quantiles, reachable-arc rate, spatial dispersion, and local road-network density. The primary acceptance view is joint stratum preservation; no single metric can certify representativeness.

For future ward aggregation, customer-share and demand-share weights are compared. Demand share is the preferred operational weight when the estimand is delivered demand; customer share is preferred for customer-level estimands. Area share is descriptive only. Aggregation remains a design possibility, `Y_Ota = sum_s w_s Y_s`, and is not executed in R24.

