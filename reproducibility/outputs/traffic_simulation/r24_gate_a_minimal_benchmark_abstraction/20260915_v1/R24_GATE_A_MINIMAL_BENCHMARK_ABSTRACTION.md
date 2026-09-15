# R24 Gate A minimal benchmark abstraction

Decision ID: `R24-GATE-A-MINIMAL-ABSTRACTION-20260915-v1`  
Decision date: 2026-09-15 JST  
Verdict: **`GATE_A_ACCEPTED_WITH_LIMITATIONS`**

R24 is frozen as an **Ota-grounded controlled CVRP benchmark**, not a reconstruction of real carrier operations.

## Adopted abstraction

The source universe is the saved synthetic day `2026-01-01`: 73,547 positive household-day demand records and 82,246 parcel-equivalents. Records with an assigned stable building are aggregated without loss to 39,956 positive-demand buildings. Each such building is one benchmark customer identity and is connected to the road network by its versioned routing proxy.

`synthetic household-day demand -> positive-demand building aggregate -> existing building-to-road relation -> Routing Proxy Customer Node`

The customer is a model entity. It is not an observed physical stop, entrance, carrier service event, curb location or loading point. Building aggregation is a declared benchmark construction rule, not evidence that the underlying demands were served in one visit.

## Gate A closure basis

Gate A closes because the source horizon, benchmark-customer semantics, routing-proxy semantics, eligibility predicate, exception treatment, demand-conservation contract and Instance Generation interface are now explicit and versioned. An observed entrance, actual service event, dispatch, wave or shift is not a required observational input for this controlled benchmark.

The 39,956 records are a reconstructable **candidate** population. They are not yet a fully materialized `C_eligible`: their saved all-population mapping is on historical run_2, whereas current accepted Routing Baseline run_3 reachability exists only for the old 10-customer fixture. Current-baseline remapping/compatibility and directed `DEP_006 <-> customer` reachability must be evaluated before a customer receives `eligible=true`. This limitation does not undo the Gate A semantic and interface closure.

## Verified snapshot facts

- Source horizon: 73,547 records / 82,246 parcel-equivalents, all dated 2026-01-01.
- Stable assigned building: 73,200 records / 81,859 parcel-equivalents.
- Source exceptions: 347 records / 387 parcel-equivalents (`unsupported_housing_type=321`, `no_candidate=26`).
- Positive building aggregates: 39,956 customers / 81,859 parcel-equivalents.
- Historical R03 mappings: 39,956 of 39,956; finite/in-range source coordinates: 39,956.
- Exact duplicate source coordinates: none.
- Shared historical edge: 28,294 customers in 10,022 shared-edge groups; 18,272 excess memberships beyond one customer per edge. These identities remain separate.

## Authority boundary

This decision supersedes contradictory current-use claims in older R24 design artifacts only for the benchmark-customer, service-event, routing-proxy, eligible-frame and Gate A questions. Historical files remain evidence of prior decisions. It does not authorize random, controlled or fixed-anchor instance generation, vehicle class, capacity, parcel mass, route costs or optimization execution.

`NEXT_EXECUTABLE_TASK = vehicle-class evidence review`

