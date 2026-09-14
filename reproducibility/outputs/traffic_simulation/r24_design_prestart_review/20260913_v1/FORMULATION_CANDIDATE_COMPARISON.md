# Formulation candidates

| Candidate | Capacity affects structure | Change from R23 | Exact small-scale validation | Assessment |
|---|---|---|---|---|
| A: one vehicle, one trip | No | Minimal | Trivial permutation check | Reject: capacity-only trivial |
| B: one vehicle, two trips | Yes, customer partition | Moderate | Exhaustive partition and route enumeration | Recommended |
| C: two vehicles, capacity | Yes, vehicle assignment and partition | Large | Exhaustive assignment and route enumeration | Defer |
| D: time window first | Yes, order and timing | Large | Possible only after time discretization is frozen | Defer |

## B versus C

| Dimension | Single vehicle + multiple trips | Multiple vehicles + capacity |
|---|---|---|
| R23からの変更量 | Smaller: add trip index, separator/depot consistency, per-trip load | Larger: add vehicle identity, assignment, route balance, fleet semantics |
| Capacityの意味 | Directly changes customer partition and trip count | Directly changes customer-to-vehicle assignment and partition |
| Decision variables | Trip-position route variables plus customer-trip assignment and activation | Vehicle-position route variables plus customer-vehicle assignment and activation |
| Qubit growth | With two trips, `2(n²+n+1+s)` in the selected encoding | With two vehicles, the same leading count, plus future fleet decisions |
| Exact enumeration | `(n+1)n!` labelled trip route structures before capacity filtering | `(n+1)n!` labelled vehicle route structures before capacity filtering |
| Real delivery relevance | One vehicle returning to reload is plausible and isolates capacity | More directly models fleet operations |
| Future EVRP extensibility | Can later add reload/time/SOC without fleet-size confounding | Best long-term path to CVRP/EVRP |
| Researcher arbitrariness | Two trips must be frozen and justified; low after freeze | Fleet count and vehicle heterogeneity add unresolved choices |
| R24 recommendation | **Yes, minimal R24** | No, defer to a later fleet phase |

B and C have similar leading qubit counts for exactly two labelled routes. B is preferred because it isolates the capacity mechanism while retaining one-vehicle comparability with R23. Two trips are fixed before data inspection; a third trip is a new protocol version.

