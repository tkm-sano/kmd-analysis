# Gate C and Gate D reassessment

## Gate C

`GATE_C_VERDICT = GATE_C_ACCEPTED_WITH_LIMITATIONS`

`R24_PRIMARY_CAPACITY_DIMENSION = methodological parcel-equivalent count`

Gate C closes because R24 is now explicitly a methodological benchmark: demand and capacity share the frozen abstract unit without a false conversion to kg, m³ or actual parcels. Physical capacity remains deferred rather than implied.

## Gate D

`GATE_D_VERDICT = GATE_D_ACCEPTED_WITH_LIMITATIONS`

The design-level requirements are resolved:

- `q_i=N_i` from the existing building aggregate;
- `Q=14` for all primary instances;
- `rho_target in {0.50,0.70,0.90}`;
- `m=ceil(D/(rho_target Q))`;
- instance-level validation and exclusion rules are frozen.

Concrete `m`, `rho_actual`, packing feasibility and redundancy flags cannot be materialized before an instance customer set exists. This is an execution limitation, not an unresolved parameter-selection rule.

## Remaining limitations

- the load unit is methodological, not physical;
- no observed service event, physical stop, dispatch wave or fleet exists;
- very small `n` can collapse regimes to the same `m` or make capacity redundant;
- aggregate capacity is not sufficient for indivisible-demand packing or routing feasibility;
- the full candidate population still needs accepted current-baseline kei-class routing compatibility and directed reachability;
- final `C_eligible` and all instances remain ungenerated.

Routing compatibility revalidation is now the next dependency before final population/instance construction.

`NEXT_EXECUTABLE_TASK = routing compatibility revalidation`
