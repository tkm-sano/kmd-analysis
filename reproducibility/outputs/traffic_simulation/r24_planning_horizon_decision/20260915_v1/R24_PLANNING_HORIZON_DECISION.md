# R24 Planning Horizon decision
Decision ID: R24-PLANNING-HORIZON-20260915-v1. Date: 2026-09-15 JST.
Scope: PLANNING HORIZON DECISION / SEMANTIC FREEZE ONLY.

Verdict: **PLANNING_HORIZON_FROZEN_WITH_LIMITATIONS**.

`PLANNING_HORIZON = designated synthetic day (2026-01-01) as source horizon; optimization instances are separately generated controlled benchmark subsets of a later accepted eligible routing-proxy-stop population.`

`NEXT_EXECUTABLE_TASK = finalize routing-proxy stop policy`

## Frozen meaning

Planning Horizon defines the source temporal and demand-universe boundary for one downstream instance-construction program. The immutable source boundary is all 73,547 saved synthetic household-day demand records dated 2026-01-01 (82,246 parcel-equivalents), with 73,200 mapped records / 81,859 units and 347 records / 387 units retained as explicit mapping exceptions. The 39,956 positive mapped building-day aggregates are a candidate routing-proxy population, not the horizon itself and not yet eligible customer nodes.

The horizon is not an actual carrier operating day, dispatch, wave, shift, route or observed operational period. It creates no clock time. It does not require all 39,956 candidate locations to enter one CVRP. `C_eligible` is established after the routing-proxy/event/exception remediation; Instance Generation later selects finite `C_(n,r) subset C_eligible` under repeated-random, controlled-structural or fixed-anchor policies. n, seeds, replicates and spatial structure are not Planning Horizon decisions.

This combines Option A for the source boundary with Option B for optimization semantics. Option C is rejected: treating the whole synthetic day as an operational R24 horizon would add unsupported fleet, capacity, one-tour and service-event meanings at 39,956-stop scale. Option D dispatch/wave/shift forms remain future typed specializations and are unsupported for the current baseline.

## Benchmark claims

R24 remains an **Ota-grounded controlled benchmark**. Permitted claims: Ota geographic grounding, saved synthetic-demand grounding, conditional Routing Baseline grounding and controlled computational comparison. Prohibited claims: one real dispatch, observed route, actual carrier day, or statistical representation of Ota delivery operations. Snapshot continuity does not repair the original generator provenance.

## Dependencies and Gate A effect

Planning Horizon/source-membership remediation is closed by this decision. It can freeze before service-event or routing-proxy adoption because it selects source records by an existing date and makes no claim about visit identity. Physical-stop evidence is likewise not needed to define this source universe. Gate A remains `GATE_A_REQUIRES_TARGETED_REMEDIATION`: the next dependency is explicit adoption/rejection of the `ROUTING_PROXY_STOP` policy, followed by the compatible benchmark service-event/customer-node abstraction, conservation/exception contract and formal Gate A sign-off. Their policies may narrow `C_eligible` but cannot rewrite the frozen date/source universe silently.

Observed entrances are not required merely to freeze this controlled source horizon. A future routing-proxy decision may accept modeled access with limitations; this decision does not do so. Parcel mass, capacity and vehicle class are later gates. Generator STOP remains `BLOCKS_REGENERATION_ONLY`.

No demand, timestamp, membership, event, access, eligible population or instance was generated. Historical artifacts were not edited. The migration CSV is a versioned amendment proposal only.
