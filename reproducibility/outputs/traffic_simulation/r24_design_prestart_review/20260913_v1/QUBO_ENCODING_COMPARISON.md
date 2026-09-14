# QUBO encoding comparison

| Encoding | Logical variables (K=2) | Strength | Weakness | R24 decision |
|---|---:|---|---|---|
| 1. trip-position + assignment + binary slack | `K(n²+n+1+s)` | Direct R23 extension; compact | Weighted slack needs exact bounds and linking penalties | **Recommended** |
| 2. vehicle/trip assignment + route ordering | Same leading count for K=2 | Natural CVRP path | Vehicle/trip semantics and symmetry are larger than needed | Defer |
| 3. one-hot load state | `K(n²+n+1+n(Q+1))` | Exact load-state interpretation | Qubit growth is severe; many transition penalties | Reject for R24 |

Encoding 1 uses `s=ceil(log2(Q+1))` binary slack bits per trip and quadratic penalties for customer exactly-once, position activation, assignment linking, and load equality. Encoding 2 is a later multi-vehicle formulation. One-hot load is retained only as an independent verification encoding for the smallest fixture, if needed.

