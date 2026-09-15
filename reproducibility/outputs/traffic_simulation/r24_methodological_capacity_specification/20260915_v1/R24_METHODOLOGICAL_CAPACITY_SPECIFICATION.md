# R24 methodological capacity specification

Specification ID: `R24-METHODOLOGICAL-CAPACITY-20260915-v1`  
Status: **FROZEN**  
Benchmark scope: **methodological parcel-equivalent capacity CVRP**

## Frozen parameters

`R24_PRIMARY_CAPACITY_DIMENSION = methodological parcel-equivalent count`

`R24_CAPACITY_UNIT = METHODOLOGICAL_PARCEL_EQUIVALENT`

`R24_METHODOLOGICAL_CAPACITY_Q = 14 parcel-equivalents`

For benchmark customer `i`:

\[
q_i=N_i,
\]

where `N_i` is the positive integer `parcel_equivalent` value already aggregated to the building in the frozen synthetic snapshot. No load is newly generated.

For vehicle `k`, the standard capacity constraint is:

\[
\sum_i q_i y_{ik}\le Q \qquad \forall k.
\]

An equivalent arc-based or route-based expression may be used only if it enforces the identical per-vehicle sum and unit.

## Capacity regimes and fleet rule

The frozen targets are:

| Regime | `rho_target` | Authority |
|---|---:|---|
| `LOOSE` | 0.50 | `CONTROLLED_BENCHMARK_PARAMETER` |
| `MODERATE` | 0.70 | `CONTROLLED_BENCHMARK_PARAMETER` |
| `TIGHT` | 0.90 | `CONTROLLED_BENCHMARK_PARAMETER` |

For an instance with `D=sum_i q_i`:

\[
m(\rho^*)=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\qquad
\rho_{actual}=\frac{D}{mQ}.
\]

`Q` is constant across all primary R24 instances. `m` is derived, never fitted to solver outcomes. Both `rho_target` and `rho_actual` are stored. Because of the ceiling, `rho_actual <= rho_target`.

The necessary total-capacity condition is:

\[
mQ\ge D,
\qquad
m_{min}=\left\lceil\frac{D}{Q}\right\rceil.
\]

`m_min` is a capacity-only lower bound, not an observed or sufficient fleet size. Bin-packing and routing feasibility still require instance-level validation.

## Meaning boundary

The capacity unit is not kg, m³, observed parcels, a manufacturer rating, or physical vehicle utilization. `m` is a methodological available fleet size. `rho` is benchmark capacity tightness, not payload or operational utilization.

The selected kei-class EV class remains the routing/vehicle-class abstraction. Its approximately 350 kg variant-specific payload evidence is not converted to 350 parcel-equivalents and does not determine `Q`.

## Q selection

The saved building snapshot has 39,956 customers, total demand 81,859, and `q_i` range 1–14. `Q=14` is the unique smallest integer that makes every saved candidate customer individually feasible without capacity-based population censoring. Smaller candidates exclude tail customers; larger candidates add unsupported headroom, weaken small-instance capacity separation, and at `Q>=16` increase a simple binary-slack width from four to five bits.

Small instances can still be capacity-redundant or map multiple target regimes to the same integer `m`. This is recorded rather than repaired by changing `Q`, redrawing after solver results, or forcing binding.

## Gate status

- `GATE_C = GATE_C_ACCEPTED_WITH_LIMITATIONS`
- `GATE_D = GATE_D_ACCEPTED_WITH_LIMITATIONS`
- `q_i`, `Q`, regime targets and the `m` derivation rule are frozen.
- concrete instance-level `m` is not materialized until the customer set exists.
- physical kg and volume scenarios remain deferred.

No eligible manifest, customer sample, instance, route, MILP, QUBO, QAOA, Aer or optimization result was generated.

`NEXT_EXECUTABLE_TASK = routing compatibility revalidation`
