# Source Horizon versus Optimization Instance

`Source Horizon != Optimization Instance` and `Synthetic Day != Observed Carrier Day`.

| Object | Frozen meaning | Identity/membership | Not implied |
|---|---|---|---|
| Source Horizon | saved synthetic demand universe dated 2026-01-01 | exact `evaluation_date` filter plus snapshot hashes and explicit unmapped exceptions | dispatch, shift, route, fleet feasibility, all-day CVRP |
| Candidate proxy population | 39,956 positive mapped building-day aggregates with saved road relations | existing stable source IDs; still candidate-only | physical entrances or service events |
| Eligible population `C_eligible` | later accepted routing-proxy/customer-node frame inside the source horizon | future versioned manifest/hash after Gate A remediation | sample size, seed or selected instance |
| Optimization Instance `C_(n,r)` | finite controlled benchmark subset of `C_eligible` | selected IDs and future instance manifest | one carrier day/dispatch or Ota-representative operation |

Flow: Designated Synthetic Day -> `C_eligible` -> Instance Generation (repeated random / controlled structural / fixed anchor) -> Optimization Instance.

The horizon owns temporal source inclusion. Eligibility owns admissible proxy/customer records and exceptions. Instance Generation owns n, RNG/seed/replicate, clustering/dispersion rules, anchors and selected IDs. Later vehicle/load/cost gates complete a concrete CVRP instance; this decision supplies none of them.
