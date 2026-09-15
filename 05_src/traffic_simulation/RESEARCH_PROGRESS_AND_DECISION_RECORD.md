# Research Progress and Decision Record

Document ID: `RESEARCH-PROGRESS-DECISION-RECORD-20260915-v2`

Role: **historical decision record**

Current through: 2026-09-15 JST

## 1. Purpose and authority boundary

This document records how the research moved from a routing foundation and the R23 reduced problem to the current R24 controlled CVRP design. It explains dependencies, decisions, rejected alternatives, deferred scopes, and the current executable next task. It does not replace immutable run manifests or stage-specific evidence.

For the design currently in force, use [CURRENT_RESEARCH_DESIGN.md](CURRENT_RESEARCH_DESIGN.md). Where an older artifact has a different Gate status or `NEXT_EXECUTABLE_TASK`, the later accepted decision recorded here and in the current-design document prevails for that field. Historical artifacts remain evidence of the decision path, not competing current authorities.

No experiment, demand generation, routing generation, instance generation, or optimization was performed to create this record.

## 2. Research objective

The research evaluates how changes in technical and social conditions—including quantum technologies as candidate technologies or solution methods—propagate through electric residential B2C last-mile delivery into routing, operational outcomes, and the defined economic outcome. Quantum advantage is an empirical question; it is not assumed.

The intended chain is:

```text
technology / society / environment
  -> demand, vehicle, network, energy, and method parameters
  -> routing plan
  -> operational outcomes
  -> operating electricity expenditure
  -> scenario comparison
```

## 3. Initial spatial and routing foundation

The geographic scope was fixed to Ota Ward, Tokyo. OSM road data, the N03 administrative boundary, PLATEAU buildings, census and housing statistics, and parcel-related public statistics were assembled into a common spatial foundation. Buildings were assigned stable identifiers and representative coordinates, then mapped to versioned road-network endpoints.

The accepted Routing Baseline established four rules that remain current:

1. the network is directed;
2. `i -> j` and `j -> i` are separate ordered pairs;
3. route cost is directed model travel time, with road distance reported on the same selected path;
4. unreachable or missing costs remain explicit and are never replaced by zero or an artificial finite cost.

The accepted run_3/V18 network is a model-completed SUMO 1.24.0 graph. Its travel time is length divided by model speed under the Routing Baseline, not observed carrier travel time or dynamic congested travel time. DEP_006 was adopted as a controlled benchmark origin/depot proxy, not as an observed carrier depot or catchment.

## 4. R23 reduced routing study

R23 isolated a **Single-Vehicle Route Ordering Problem**: depart from one depot, visit every selected customer exactly once, and return. It used customer-position variables (`n^2` logical variables), a directed travel-time objective, squared exact-one QUBO penalties, exact permutation references, QUBO-to-Ising conversion, and depth-one QAOA on CPU Aer exact statevectors.

The accepted formal scope covered `n=2,3,4` with `lambda=3.0`, followed by `n=5` with `lambda=4.0`. Across the final provenance-complete `n=5` clean runs, the exact optimal route was recovered in 3/3 cases while the classical optimizer reported success in 2/3; these outcomes were deliberately kept distinct. The implementation benchmark showed a large single-workload runtime and memory reduction after remediation, but only for one `n=5` workload and one valid run per implementation.

R23 did **not** model multiple vehicles, capacity, time windows, service time, battery/SOC, charging, observed operations, QPU execution, or quantum advantage. Small cases were computational tests, not statistically representative Ota delivery samples. B2 derived-artifact SHA discrepancies, limited repetitions, historical lineage gaps, and exact-statevector resource limits remain documented.

Final status: **`R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS`**. R23 was closed rather than retrofitted into a CVRP; R24 was created as the next problem layer.

## 5. End-to-End redesign

The work was reorganized because an R24-only formulation could not by itself distinguish source data, synthetic transformations, customer semantics, instance construction, physical assumptions, routing, operation, and economics. The end-to-end architecture separated those responsibilities:

```text
Open Data
  -> Synthetic Demand
  -> Requests
  -> Stops
  -> Planning Horizon
  -> Instance Generation
  -> Vehicle / Capacity
  -> Routing
  -> Operational Outcomes
  -> Economic Outcome
```

This redesign also established that the displayed conceptual order is not always the execution dependency order. In particular, a final eligible population and executable instance policy depend on accepted customer semantics, vehicle/access compatibility, capacity semantics, and routing reachability.

The architecture audit initially left Gate A and later data gates open. Its architecture and economic boundary remain current, while its dated Gate statuses and next-task text were superseded by the later decisions below.

## 6. Gate A evidence reconstruction and abstraction

### 6.1 Evidence finding

The saved source horizon contains 73,547 positive synthetic household-day rows and 82,246 parcel-equivalents for `2026-01-01`. It does not contain individual observed parcel identifiers, observed entrances, physical curb/loading points, carrier service-event identities, dispatch batches, waves, or shifts. The original demand generator provenance is incomplete, although the saved snapshot can be inspected and conserved.

An observational service-event reconstruction was therefore not supportable. Requiring it would have changed R24 from a controlled methodological benchmark into an unsupported carrier-operation reconstruction.

### 6.2 Adopted minimum abstraction

The decision was:

```text
synthetic household-day demand
  -> positive-demand building aggregate
  -> existing building-to-road mapping
  -> Routing Proxy Customer Node
```

One positive-demand mapped building is one benchmark customer identity. The benchmark identity is defined by the building record, not by an observed delivery service event. The road endpoint is a routing proxy, not a physical stop or entrance.

Multiple buildings mapped to one proxy remain separate customers. Duplicate proxy locations/nodes are flagged; they are not silently aggregated into a service event. Selected instances must inspect zero-distance and zero-time effects.

Gate A also froze source membership, customer and routing-proxy semantics, eligibility and exception contracts, demand conservation, and the common interface to future instance generators.

Verdict: **`GATE_A_ACCEPTED_WITH_LIMITATIONS`**.

## 7. Planning Horizon decision

The Planning Horizon was frozen as the **designated synthetic day `2026-01-01` used as the source horizon**. It determines which saved demand records enter the source population. It is not an optimization instance, observed carrier day, dispatch wave, shift, tour, or operating period.

Dispatch, wave, and shift were rejected as mandatory R24 Gate A fields because no supporting operational evidence exists. They remain future operational-model concepts. This allowed stable source membership without fabricating temporal operations.

## 8. Gate B vehicle-class decision

Vehicle class was separated from a specific commercial model. Eight predeclared criteria were used: residential B2C relevance, urban last-mile suitability, public specification authority, capacity-data availability, EVRP-data availability, routing compatibility, modeling simplicity, and researcher arbitrariness.

Decision:

- primary: **kei-class electric commercial van**;
- coherent real-vehicle references: Honda N-VAN e:, Mitsubishi Minicab EV, and Suzuki e Every;
- secondary scenario: light-duty electric truck;
- compact electric delivery van: insufficient matched Japanese evidence for the primary role;
- `managed_urban_ev_delivery_v1`: `REFERENCE_ONLY` fixed research assumption.

The real models form a source-record-preserving reference envelope; no unsupported cross-model average vehicle was created. The historical profile's `Q=2,000 kg` was not inherited by R24.

Verdict: **`GATE_B_ACCEPTED_WITH_LIMITATIONS`**. It triggered a later vehicle/routing compatibility check rather than blocking class selection.

## 9. Gate C physical-capacity investigation

Mass, volume, parcel count, standardized load units, and multidimensional capacity were compared. Vehicle-side mass evidence was strongest: primary-class variants commonly provide official payload records around 350 kg, subject to trim-specific exceptions. That alone could not establish `unit(q_i)=unit(Q)`.

A targeted search for Japanese residential B2C parcel mass evidence found no publicly usable, population-compatible parcel-level observations, histogram/CDF, or supported fitted distribution. The MLIT logistics census is establishment/freight-flow based and cannot isolate the required residential B2C last-mile population. Carrier price/size/weight limits are allowable maxima, not observed distributions. The closest domestic studies either reported aggregates, had small or rural populations, or did not expose a usable distribution.

Verdict: **`DEMAND_SIDE_MASS_AUTHORITY_INSUFFICIENT`**. No `F_W`, mean parcel mass, synthetic parcel mass, or kg conversion was authorized. Physical mass and volume scenarios were deferred.

## 10. Methodological capacity freeze

Stopping at the physical-evidence gap was rejected because R24's immediate purpose is a controlled methodological CVRP benchmark. The primary unit was explicitly labeled:

`METHODOLOGICAL_PARCEL_EQUIVALENT`

For customer `i`:

\[
q_i=N_i,
\]

where `N_i` is the saved building aggregate of realized parcel-equivalents. It is a non-negative integer in the general model and a positive integer in the eligible population. No new load was generated.

The pre-routing candidate snapshot had the following distribution:

| Statistic | Value |
|---|---:|
| Customers | 39,956 |
| Total | 81,859 |
| Minimum / maximum | 1 / 14 |
| Mean | 2.048729 |
| Median | 2 |
| P75 / P90 / P95 / P99 | 3 / 4 / 5 / 7 |

The common capacity was frozen at:

\[
Q=14\ \text{methodological parcel-equivalents}.
\]

`Q=14` is the smallest integer that leaves every candidate customer individually feasible; it was not selected to improve a solver result or copied from a vehicle payload. The controlled capacity-pressure targets are:

\[
\rho^*\in\{0.50,0.70,0.90\},
\]

labeled `LOOSE`, `MODERATE`, and `TIGHT`. With `D=sum_i q_i`, methodological available fleet size is derived by:

\[
m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\qquad
\rho_{actual}=\frac{D}{mQ}.
\]

Both target and actual pressure must be stored. Neither `m` nor `rho` is an observed fleet or physical utilization measure. Instance validation must additionally test indivisible-demand packing, same-`m` regime degeneracy, and capacity redundancy.

Final status: **`GATE_C_ACCEPTED_WITH_LIMITATIONS`** and **`GATE_D_ACCEPTED_WITH_LIMITATIONS`**.

## 11. Routing compatibility revalidation

Although this consolidation was requested as preparation for routing revalidation, the repository's actual sequence has already completed that task. The record therefore preserves the completed result rather than reverting the status.

The historical run_2 mapping supplied all 39,956 building-to-edge proxies. The accepted run_3/V18 graph was derived from the same topology and preserved edge IDs, node IDs, one-way direction, permissions, and delivery access while repairing geometry and lengths. Every mapped edge ID and stored from/to-node relation was checked. The prior proxy point transfers to the current edge geometry; historical costs do not transfer and must be recomputed on run_3 for selected instances.

For the SUMO `delivery` permission domain, connection-aware strongly connected components were used instead of constructing approximately 1.596 billion ordered customer pairs. DEP_006 and 39,930 customers lie in the same delivery SCC, which proves directed mutual reachability at the population graph level. The result was:

| Routing result | Customers | Parcel-equivalents |
|---|---:|---:|
| Candidates checked | 39,956 | 81,859 |
| Final `C_eligible` | 39,930 | 81,793 |
| Excluded | 26 | 66 |

The 26 exclusions comprise one outbound-only, one inbound-only, and 24 unreachable candidates. No mapping-invalid row was found. Rebuild and remap were not required. This is graph/model compatibility for a kei-class EV van abstraction, not proof of legal or physical curb access.

Verdict: **`ROUTING_COMPATIBILITY_ACCEPTED_WITH_LIMITATIONS`** and **`FINAL_C_ELIGIBLE_READY = YES_WITH_LIMITATIONS`**.

## 12. Adopted, rejected, and deferred decisions

### Adopted for current R24

- Ota-grounded controlled CVRP benchmark;
- designated synthetic source day `2026-01-01`;
- positive-demand mapped building as benchmark customer;
- versioned edge-offset routing proxy;
- final routing-eligible population of 39,930 customers;
- kei-class electric commercial van as primary vehicle class;
- methodological parcel-equivalent capacity;
- `q_i=N_i`, `Q=14`, three pressure regimes, and derived `m`;
- multi-vehicle capacitated directed travel-time minimization;
- population SCC screening followed by selected-instance complete ordered-pair routing validation.

### Rejected or superseded as current defaults

- building = observed customer or physical stop;
- mandatory observed service-event reconstruction;
- mandatory dispatch batch, wave, or shift;
- daily demand = one vehicle-tour load;
- automatic `Q=2,000 kg` or 350 kg-to-count conversion;
- quartile × tertile primary design;
- nested PPS as primary R24 sampling;
- representative-small-`n` claims;
- choosing capacity or instances after viewing solver performance.

### Deferred

- physical kg and m³ capacity;
- actual carrier fleet, tours, reloads, and dispatch structure;
- observed entrances, stops, service events, and service time;
- operational representativeness of Ota deliveries;
- VRPTW time-window authority;
- EVRP energy/SOC/charging model;
- electricity tariff and numerical economic evaluation.

These deferrals limit claims but do not block the methodological R24 benchmark.

## 13. Current position and critical path

Completed dependency chain:

```text
R23 closure
  -> End-to-End architecture
  -> Gate A customer/horizon/proxy semantics
  -> Gate B vehicle class
  -> Gate C physical evidence review
  -> Gate C/D methodological capacity freeze
  -> routing compatibility revalidation
  -> final C_eligible manifest
```

Current executable path:

```text
generate R24 benchmark instance suite
  -> Classical R24 CVRP and validation
  -> R24 QUBO
  -> Resource Gate
  -> QAOA where authorized
  -> R23/R24 comparison
  -> VRPTW
  -> EVRP
  -> Operational Outcomes
  -> Economic Outcome
  -> Scenario Comparison
```

`NEXT_EXECUTABLE_TASK = generate R24 benchmark instance suite`

## 14. Instance-generation specification freeze

The specification was frozen before generating any instance or route matrix. The primary repeated-random suite uses hash-ranked SRSWOR from the final 39,930-customer eligible frame: quantum-comparable `n={2,3,4}` and classical-extension `n={5,8,10,15,20}`, with 10 repetitions per n. Seeds are SHA-256-derived from the protocol/suite/n/repetition identity and cannot be searched or manually selected.

The controlled structural suite uses `CLUSTERED`, `DISPERSED`, and `MIXED` at `n={4,10,20}`, three deterministic repetitions each, using EPSG:6677 Euclidean distance and fully specified hash-anchor, nearest, farthest-point, quota, and tie rules. Fixed anchors are the exact `R01` primary subsets at n=4,10,20; they are never post-hoc replacements.

The frozen no-redraw rule preserves every selected subset under its planned ID. Duplicate proxies and validated zero arcs are reported but not rejected. Every selected base requires complete ordered-pair run_3 routing and connection validation. The same base serves all three capacity regimes. Exact deterministic packing preflight may mark a capacity condition `PACKING_INFEASIBLE` but never redraw or reject the customer subset; equal-m targets are retained and excluded only from capacity-effect comparison.

Verdict: **`R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS`**. Scientific experiment, instance generation, routing generation, and optimization in this freeze step were all `NONE`.

## 15. Principal evidence links

- [R23 current status](R23_STATUS.md)
- [End-to-End Workflow Authority](../../reproducibility/outputs/traffic_simulation/end_to_end_workflow_feasibility_audit/20260914_v2/END_TO_END_WORKFLOW_AUTHORITY.md)
- [Planning Horizon decision](../../reproducibility/outputs/traffic_simulation/r24_planning_horizon_decision/20260915_v1/R24_PLANNING_HORIZON_DECISION.md)
- [Gate A sign-off](../../reproducibility/outputs/traffic_simulation/r24_gate_a_minimal_benchmark_abstraction/20260915_v1/GATE_A_SIGNOFF.md)
- [Gate B vehicle decision](../../reproducibility/outputs/traffic_simulation/r24_gate_b_vehicle_class/20260915_v1/R24_GATE_B_VEHICLE_CLASS_DECISION.md)
- [Demand-side mass review](../../reproducibility/outputs/traffic_simulation/r24_demand_side_mass_evidence/20260915_v1/R24_DEMAND_SIDE_MASS_EVIDENCE_REVIEW.md)
- [Methodological capacity specification](../../reproducibility/outputs/traffic_simulation/r24_methodological_capacity_specification/20260915_v1/R24_METHODOLOGICAL_CAPACITY_SPECIFICATION.md)
- [Routing compatibility revalidation](../../reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/R24_ROUTING_COMPATIBILITY_REVALIDATION.md)
- [Frozen instance-generation specification](../../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md)

## 16. Documentation consolidation execution receipt

| Activity | Execution in this task |
|---|---|
| Scientific experiment | `NONE` |
| Demand generation | `NONE` |
| Routing generation | `NONE` |
| Instance generation | `NONE` |
| Optimization | `NONE` |

This task inspected existing tracked and gitignored authority artifacts and changed documentation only.
