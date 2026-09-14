# QUBO encoding comparison

| Encoding | Representative variable structure | Capacity/subtour treatment | Decision |
|---|---|---|---|
| Arc-based | `m*n(n+1)` directed route arcs, excluding self arcs | capacity slack plus explicit subtour penalties/order auxiliaries | Exact semantics, but largest quadratic model |
| Vehicle-customer assignment + ordering | `mn` assignment plus position/order variables | capacity slack; ordering enforces route continuity | Useful cross-check, moderate-to-large |
| Position-based vehicle encoding | `mn²` customer-position variables plus activation | assignment/position exact-one and capacity slack; no separate subtour cuts | **Recommended for smallest R24 instances** |
| Assignment + binary capacity slack | Added to either route encoding | `s=ceil(log2(Q+1))` bits per vehicle with equality/inequality penalty | Required capacity component, not a complete route encoding |

The recommended encoding is position-based vehicle routing plus assignment variables and binary capacity slack. It is selected after population reduction and only for the resource-gated subproblem. The arc-based model is the classical-semantic cross-check where feasible. All QUBO decoders discard invalid states, repair none, and preserve the full-state probability denominator.

