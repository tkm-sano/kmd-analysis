# Research Overview and Roadmap v17

Status: `ADOPTED / CURRENT` research-navigation document  
As of: 2026-09-03  
Scope: research plan, dependencies, milestones, gates, and current status only

This document is the human-readable entry point for the research as a whole. It does not replace the machine-readable [current network completion authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml), its acceptance artifact, configs, schemas, or manifests. When a value or acceptance state conflicts, the current authority and its referenced artifacts take precedence.

## Research question

> 量子技術の発展が、移動技術を通じて都市社会・都市経済にどのような変化をもたらしうるか。

This research treats Mobility / Logistics as the mediator between technological change and social/economic change. It does not attempt to prove a direct causal effect from quantum technology to urban society. The final analysis is a **future scenario analysis**: assumptions, modeled mechanisms, simulation outcomes, and interpretations must remain distinguishable.

## Status vocabulary

| Label | Meaning |
|---|---|
| `ADOPTED / CURRENT` | Current accepted authority, definition, or active research position |
| `DONE` | Acceptance condition has been met and downstream use is allowed |
| `NEXT` | Immediate active stage after the last completed milestone |
| `PLANNED` | Work and gate are defined, but the stage is not complete |
| `CANDIDATE` | An option for later review; not adopted |
| `UNRESOLVED` | A required decision or value has not been fixed |
| `FUTURE` | Later work whose prerequisites are not yet complete |

The presence of code, a document, or an exploratory result does not by itself make a stage `DONE`.

## Conceptual model

```text
Quantum Technology
  → Mobility / Logistics Capability
  → Planning / Policy
  → Business / Economic Activity
  → Urban Society / Urban Economy
```

The arrows describe the mechanism to be examined under explicit scenarios, not established direct causality. In the empirical/implementation path, quantum capability may change optimization capability; optimization may change feasible logistics plans; executed delivery outcomes may expand or constrain planning and business options. Each link requires its own assumptions, evidence, and sensitivity analysis.

## Current position

| Position | Current value |
|---|---|
| Current completed milestone | **M1 Network Ready — DONE** |
| Current research stage | **Routing Baseline — NEXT** |
| Immediate next task | **どの配送instanceを対象に、どのStop間routing costを生成するかを正式に定義する** |

Current accepted network state (`ADOPTED / CURRENT`):

| Item | Accepted value |
|---|---|
| Demand baseline | `DONE` |
| Requests / Stops generation | `DONE` |
| Three-tier Formal Network Completion | `DONE` |
| SUMO Network Construction | `DONE` |
| lane / speed / permission validation | `PASS` |
| Stop mapping | `39,956 / 39,956` |
| Formal Network Acceptance | `ACCEPTED` |
| Acceptance flag | `FORMAL_NETWORK_ACCEPTED = true` |
| Network | `three_tier.net.xml` |
| SHA-256 | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |

The accepted network path and acceptance evidence are resolved through the current authority. This note intentionally records only the navigation-level state and does not become a second acceptance authority.

## Analysis pipeline and dependencies

```text
External / Open Data
  → Baseline Demand
  → Future Demand Parameterization
  → Requests / Stops
  → Structural Network
  → Formal Network Completion
  → SUMO Materialization
  → Stop Mapping
  → Formal Network Acceptance
  → Routing Baseline
  → Common Delivery Instance
  → Classical Optimization
  → QUBO Formulation
  → QAOA / Quantum Optimization
  → Delivery Simulation
  → Fulfillment Evaluation
  → Planning / Business Interpretation
  → Future Society Interpretation
```

This is the end-to-end analysis path, not a claim that every artifact is produced by one strictly linear job. In particular:

- Current Requests / Stops are accepted baseline artifacts produced from Baseline Demand; they do not imply that Future Demand Parameterization is complete.
- Future Demand Parameterization is a `PLANNED` scenario transformation that will generate scenario-specific Requests / Stops through the same governed interface.
- Network construction and demand preparation are upstream branches that join at Stop Mapping and Routing Baseline.
- Sensitivity / Robustness applies across routing, network fallback attributes, demand, battery, optimization, QUBO, and scenarios.
- Reproducibility / Publication Freeze is the final cross-cutting gate.

## Research stages, gates, and downstream dependencies

### Stage 1 — Routing Baseline (`NEXT`)

**Purpose:** Fix the movement costs needed for delivery optimization on the accepted Formal Network.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted SUMO network; accepted Stop mapping; Requests / Stops; depot; delivery vehicle class |
| Work | Define routing scope; Depot → Stop, Stop → Stop, and Stop → Depot costs; travel time; distance; routeability; route provenance |
| Output | Versioned routing methodology, scoped OD cost artifacts, validation report, provenance/commands |
| Acceptance gate | Routing methodology fixed; all required—not presumed all-pairs—OD costs generated; routing validation `PASS`; artifacts reproducible |
| Downstream dependency | Stage 2 Common Delivery Instance |

`39,956 × 39,956` all-pairs routing is **not** an adopted premise. The first task is to define which delivery instance(s) will be evaluated and exactly which Stop pairs those instances require.

Unresolved: depot location, instance sampling/selection rule, vehicle class details, routing cost scope, route generation method, unreachable-pair treatment, and provenance contract.

### Stage 2 — Common Delivery Instance (`PLANNED`)

**Purpose:** Integrate Demand, Routing, and Vehicle constraints into one solver-neutral problem shared by Classical and Quantum methods.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted Requests / Stops; selected depot; Stage 1 routing costs; travel time and distance; vehicle constraints; battery constraints |
| Required contents | Requests, Stops, parcel-equivalent, depot, routing costs, travel time, distance, vehicle constraints, battery constraints, provenance |
| Output | Versioned schema, validator, production-generation config/command, reproducible production instance |
| Acceptance gate | Schema fixed; validator available and passing; placeholder-free production instance generated reproducibly and accepted |
| Downstream dependency | Stage 3 Classical Optimization and Stage 4 QUBO formulation |

Repository check: `05_src/optimization/common_delivery_instance.py` is **absent from the current checkout**. A prior Git object contains a candidate solver-neutral validator requiring requests, stops, depot, vehicles, node order, distance/travel-time/vehicle-energy matrices, and provenance hashes. That historical design is useful review input, but it is not `ADOPTED / CURRENT`, not available as a current validator, and does not satisfy this stage gate. Whether to restore, revise, or replace it is `UNRESOLVED`.

### Stage 3 — Classical Optimization (`PLANNED`)

**Purpose:** Establish the classical baseline against which quantum methods can be compared.

`ADOPTED / CURRENT` research objective for the formulation: **maximize planned served parcel-equivalent**, with battery and other feasibility requirements treated as hard constraints. The exact mathematical formulation and optimizer remain `PLANNED` / `UNRESOLVED` until the Stage 3 gate.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted Common Delivery Instance; fixed objective semantics; fixed feasibility checker; solver budget and seeds |
| Required formulation | Decision variables; objective; route feasibility; vehicle capacity; battery feasibility; served demand; all additional adopted constraints |
| Output | Fixed mathematical formulation, implementation, correctness fixtures, production baseline and provenance |
| Acceptance gate | Formulation fixed; solver implemented; small-instance correctness validated; production baseline generated |
| Downstream dependency | Stage 4 comparison and Stage 6 Delivery Simulation |

Optimizer algorithm, fleet size, delivery capacity, battery value, and computation budget remain `UNRESOLVED`. No optimizer is adopted merely because it is a plausible candidate.

### Stage 4 — Quantum Optimization (`PLANNED`)

#### Stage 4A — QUBO formulation

Transform the fixed Classical problem into QUBO. Required checks are objective equivalence, constraint penalties, variable mapping, coefficient scaling, and correctness. Inputs are the accepted Common Delivery Instance and fixed Classical formulation. Output is a versioned formulation and encoder/decoder contract. The gate remains closed until equivalence and feasible-solution semantics are demonstrated.

#### Stage 4B — QUBO validation

For small instances, compare the Classical optimum with the QUBO optimum. Output must include exact fixtures, penalty settings, decoded solutions, feasibility checks, and mismatch diagnostics. Acceptance requires agreement under the declared equivalence criteria, not only a low QUBO energy.

#### Stage 4C — QAOA

Connect the validated QUBO to QAOA or another explicitly adopted quantum optimization path. Required inputs include the accepted QUBO, execution backend assumptions, circuit parameters, seeds, sampling/decoding/repair rules, and measurement boundary. QAOA depth and quantum hardware assumptions are `UNRESOLVED`.

#### Stage 4D — Classical vs Quantum comparison

Candidate comparison dimensions are solution quality, served parcel-equivalent, feasibility, runtime, problem size, and circuit/resource requirements. Shared instance and evaluation rules are mandatory. Quantum advantage is **not** assumed; absence of advantage or inability to scale is a valid result.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted Stage 2 instance; accepted Stage 3 reference; validated QUBO; fixed quantum execution and comparison protocol |
| Output | QUBO formulation/validation evidence, quantum candidate solutions, fair Classical-vs-Quantum comparison |
| Acceptance gate | 4A–4D gates pass with reproducible settings and feasibility evaluated by the common checker |
| Downstream dependency | Stage 6 Delivery Simulation and Stage 9 mechanism interpretation |

QUBO coefficients, penalty values, QAOA depth, optimizer choice, and backend/hardware assumptions are `UNRESOLVED`.

### Stage 5 — Future Technology / Demand Scenarios (`PLANNED`)

Technology scenarios and social/demand scenarios must be separate inputs, even when combined in an experiment.

| Scenario family | Candidate dimensions | Current status |
|---|---|---|
| Technology scenario | EV battery capability; vehicle capability; routing/optimization capability; quantum computing capability | `CANDIDATE`; parameter values and evidence not fixed |
| Social / Demand scenario | Population change; total delivery demand change; spatial demand change | `CANDIDATE`; **Future Demand Parameterization is incomplete** |

| Gate field | Definition |
|---|---|
| Required inputs | Accepted baseline; evidence-backed scenario definitions; parameter provenance; scope and comparison year if adopted |
| Output | Separate versioned technology and demand scenario configs, then preregistered combinations |
| Acceptance gate | Parameters, sources, ranges, transformation rules, and baseline comparison are fixed and validated without overwriting the baseline |
| Downstream dependency | Scenario-specific Requests / Stops, Common Delivery Instances, optimization, simulation, and interpretation |

Demand growth rate and scenario year are `UNRESOLVED`.

### Stage 6 — Delivery Simulation (`PLANNED`)

**Purpose:** Execute optimization plans in SUMO or another explicitly accepted simulation environment.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted network; accepted Common Delivery Instance; Classical and/or Quantum plan; traffic/scenario config; execution seeds |
| Output | Actual route traces, travel time, waiting, battery use, completed deliveries, failed deliveries, and congestion interactions |
| Acceptance gate | Plans are translated reproducibly; execution and failure accounting validate; outputs retain plan and run provenance |
| Downstream dependency | Stage 7 Fulfillment Evaluation |

Optimization output is a planned solution; simulation output is realized modeled behavior. They must not be treated as identical.

### Stage 7 — Fulfillment Evaluation (`PLANNED`)

Primary metric:

```text
delivery_fulfillment_rate
  = delivered_parcel_equivalent / total_parcel_equivalent
```

The denominator scope, time horizon, and treatment of unreachable or excluded demand must be fixed before formal use.

| Metric role | Metrics |
|---|---|
| Primary | `delivery_fulfillment_rate` |
| Supporting | delivered parcel-equivalent; unmet parcel-equivalent; vehicle utilization; travel time; distance; battery use; unreachable demand |

| Gate field | Definition |
|---|---|
| Required inputs | Accepted simulation outcomes; fixed evaluation population and denominator; common metric implementation |
| Output | Primary and supporting metrics with uncertainty/failure decomposition |
| Acceptance gate | Formula, units, scope, denominator, exclusions, and aggregation are fixed; evaluator validates on fixtures; results reproduce |
| Downstream dependency | Stage 8 Planning / Business Interpretation and Stage 10 robustness |

### Stage 8 — Planning / Business Interpretation (`PLANNED`)

**Purpose:** Connect technical outcomes to conditional social and economic meaning.

| Interpretation branch | Candidate questions |
|---|---|
| Planning / Policy | logistics accessibility; service coverage; infrastructure requirement; policy choices; resilience |
| Business / Economy | feasible delivery scale; operating constraints; service area; business opportunity; resource requirement |

| Gate field | Definition |
|---|---|
| Required inputs | Stage 7 evidence; declared scenarios; uncertainty and sensitivity results; external contextual evidence |
| Output | Conditional planning/policy and business/economic interpretations with limitations |
| Acceptance gate | Each claim traces to a modeled outcome and scenario assumption; alternatives and uncertainty are stated; no direct social causality is asserted from simulation alone |
| Downstream dependency | Stage 9 Future Society Interpretation |

### Stage 9 — Future Society Interpretation (`PLANNED`)

The final mechanism to examine is:

```text
Quantum capability
  → Optimization capability
  → Mobility / Logistics capability
  → Delivery fulfillment
  → Planning / Business options
  → Urban society / economy
```

| Gate field | Definition |
|---|---|
| Required inputs | Stages 4, 7, 8, and scenario evidence; explicit mechanism assumptions and limitations |
| Output | Integrated future-society interpretation and bounded conclusions |
| Acceptance gate | Every link distinguishes measured/modelled result from scenario assumption; rival explanations and limits are addressed; quantum advantage is not presupposed |
| Downstream dependency | Stage 10 robustness and final conclusions |

### Stage 10 — Sensitivity / Robustness (`PLANNED`)

Minimum sensitivity domains: routing assumptions; inferred/fallback network attributes; demand assumptions; battery assumptions; optimization parameters; QUBO penalties; and scenario assumptions.

| Gate field | Definition |
|---|---|
| Required inputs | Accepted baseline results; preregistered uncertain parameters/ranges; rerun and comparison protocol |
| Output | Sensitivity matrix, robustness summaries, failure boundaries, interpretation changes |
| Acceptance gate | Material assumptions are varied systematically; conclusions are classified as robust, conditional, or unsupported |
| Downstream dependency | Stage 11 freeze and publication claims |

### Stage 11 — Reproducibility / Publication Freeze (`FUTURE`)

| Gate field | Definition |
|---|---|
| Required inputs | Accepted outputs and validation evidence from all claimed stages |
| Output | Frozen current authority pointers, configs, schemas, accepted artifacts, hashes, software versions, commands, Portal, and this research overview |
| Acceptance gate | Clean reproducibility audit; all publication claims trace to frozen evidence; Portal and overview agree; internal references validate |
| Downstream dependency | Publication/submission/archive release |

## Milestones

| Milestone | Status | Purpose | Inputs | Required outputs | Acceptance condition | Dependent next milestone |
|---|---|---|---|---|---|---|
| M1 Network Ready | `DONE` | Provide an accepted, delivery-usable Formal/SUMO network | Structural network, three-tier completion policy, SUMO materialization, validation, Stops | Accepted `three_tier.net.xml`, acceptance and mapping evidence, hash and provenance | `FORMAL_NETWORK_ACCEPTED = true`; lane/speed/permission validation `PASS`; `39,956 / 39,956` Stops mapped | M2 Routing Ready |
| M2 Routing Ready | `NEXT` | Fix scoped movement costs needed by delivery instances | M1 network, mapped Stops, Requests, depot, vehicle class, routing scope | Routing methodology, required OD costs, validation, provenance | Method fixed; required OD set complete; validation `PASS`; artifacts reproducible | M3 Optimization Ready |
| M3 Optimization Ready | `FUTURE` | Freeze common problem and establish Classical baseline | M2 costs, demand, depot/vehicle/battery constraints | Accepted Common Delivery Instance; validator; Classical formulation, solver, correctness and production baseline | Stage 2 and Stage 3 gates pass | M4 Quantum Comparison Ready |
| M4 Quantum Comparison Ready | `FUTURE` | Validate QUBO/QAOA path and compare without presuming advantage | M3 instance/reference, QUBO/QAOA protocol | Validated QUBO; quantum results; fair comparison evidence | Small-instance equivalence and common-evaluator comparison pass | M5 Scenario Simulation Ready |
| M5 Scenario Simulation Ready | `FUTURE` | Execute baseline and accepted future scenarios | M3/M4 plans, accepted technology/demand scenarios, SUMO configs | Reproducible simulation runs and plan-to-execution traces | Scenario inputs accepted; run/failure validation passes | M6 Evaluation Complete |
| M6 Evaluation Complete | `FUTURE` | Quantify fulfillment and supporting outcomes | M5 outputs and fixed metric contract | Fulfillment rate and supporting metrics with uncertainty | Metric definition/denominator fixed; evaluator validates; results reproduce | M7 Research Interpretation Complete |
| M7 Research Interpretation Complete | `FUTURE` | Interpret planning, business, and future-society implications | M4 comparison, M6 evaluation, sensitivity evidence, external context | Bounded mechanism-based interpretation and limitations | Claims trace to evidence/scenarios and avoid unsupported causal claims | M8 Reproducibility / Publication Freeze |
| M8 Reproducibility / Publication Freeze | `FUTURE` | Freeze the complete evidence chain for publication | All accepted milestones and artifacts | Authority/config/schema/artifact hashes, versions, commands, Portal, overview | Reproduction and link audits pass; all public claims trace to frozen evidence | Publication/archive |

## Research-wide status

| Area | Status | Main artifact | Next action |
|---|---|---|---|
| Demand baseline | `DONE` | Governed baseline demand artifacts/config | Preserve as baseline input; do not conflate with future demand |
| Future demand | `PLANNED` | No accepted parameterization | Fix evidence, scenario year/rates, spatial transformation, and validation |
| Requests / Stops | `DONE` | Accepted Requests / Stops; 39,956 Stops | Select delivery-instance scope without assuming all Stops per instance |
| Formal Network | `DONE` | Three-tier completed Formal Network | Use only through current authority |
| SUMO Network | `DONE` | `three_tier.net.xml` | Consume as Stage 1 network input |
| Stop Mapping | `DONE` | Mapping acceptance: 39,956 / 39,956 | Define scoped routing endpoints |
| Network Acceptance | `DONE` | `network_acceptance.json`; `FORMAL_NETWORK_ACCEPTED = true` | Preserve authority and hash binding |
| Routing | `NEXT` | None accepted | Define delivery-instance routing scope and methodology |
| Common Delivery Instance | `PLANNED` | Historical candidate contract only; absent on current checkout | Decide contract disposition after routing scope is fixed |
| Classical Optimization | `PLANNED` | Comparison protocol; no accepted solver/result | Fix formulation after Common Delivery Instance gate |
| QUBO | `PLANNED` | No accepted formulation | Define only after Classical equivalence target is fixed |
| QAOA | `FUTURE` | No accepted implementation/result | Connect only to validated QUBO |
| Simulation | `PLANNED` | No accepted delivery execution for this pipeline | Run only after plans and scenarios are accepted |
| Fulfillment Evaluation | `PLANNED` | Candidate formula in this roadmap | Fix denominator/scope and evaluator before formal results |
| Interpretation | `FUTURE` | Conceptual mechanism | Interpret accepted results as conditional scenarios |
| Reproducibility | `PLANNED` | Current authority and repository indexes exist; final freeze not done | Extend artifact/version/command freeze as milestones pass |

## Unresolved decisions register

The following must not be inferred or silently filled:

| Decision | Status | Earliest gate that requires it |
|---|---|---|
| Delivery instance selection/sampling and Stop scope | `UNRESOLVED` | Stage 1 |
| Depot location | `UNRESOLVED` | Stage 1 |
| Delivery vehicle class details | `UNRESOLVED` | Stage 1 |
| Routing method and required OD set | `UNRESOLVED` | Stage 1 |
| Common Delivery Instance contract disposition | `UNRESOLVED` | Stage 2 |
| Vehicle fleet size | `UNRESOLVED` | Stage 2 |
| Vehicle delivery capacity | `UNRESOLVED` | Stage 2 |
| Battery value/model and energy cost semantics | `UNRESOLVED` | Stage 2 |
| Classical optimizer algorithm and compute budget | `UNRESOLVED` | Stage 3 |
| QUBO coefficients and penalty values | `UNRESOLVED` | Stage 4A/4B |
| QAOA depth, optimizer, shots, backend, and hardware assumptions | `UNRESOLVED` | Stage 4C |
| Scenario year | `UNRESOLVED` | Stage 5 |
| Demand growth rate and spatial change parameters | `UNRESOLVED` | Stage 5 |
| Fulfillment denominator scope and time horizon | `UNRESOLVED` | Stage 7 |

## Repository and Portal integration

`RESEARCH_OVERVIEW.md` was selected as the stable root-level name because this file is the main research entry point and therefore falls under the fixed-name exception in the repository naming rules. No other current Stage 1–11 roadmap was found. `RESEARCH_STATUS.md` is an older generated dashboard with a different, narrower 21-step source taxonomy; dated project-management documents remain historical design/status records rather than parallel current roadmaps.

- Current machine-readable network authority: [current_network_completion_authority_v17.yml](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)
- Repository entry index: [research_repository_index_v17.yml](reproducibility/indexes/research_repository_index_v17.yml)
- Human navigation map: [research_repository_map_v17.md](reproducibility/indexes/research_repository_map_v17.md)
- Repository inventory: [research_repository_inventory_v17.md](reproducibility/indexes/research_repository_inventory_v17.md)
- Portal stage graph: [research_map_v1.yml](reproducibility/config/research_portal/research_map_v1.yml)
- Unified research CLI: [research_cli.md](docs/research_cli.md) (`./research commands` is the canonical command index)
- Classical/quantum fairness notes: [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md)

The Repository Index points to this file as the main human-readable overview. The Portal uses the same Stage 1–11 labels and order; it does not define a separate stage taxonomy. The Portal and this Markdown are navigation/interpretation layers, while acceptance truth remains in machine-readable authority and accepted artifacts.

## Validation checklist

- [x] Accepted network state matches current authority.
- [x] `FORMAL_NETWORK_ACCEPTED = true`.
- [x] Network milestone is `M1 Network Ready — DONE`.
- [x] `Routing Baseline` is `NEXT`.
- [x] Future stages are not marked `DONE`.
- [x] The accepted network name and SHA-256 match the current authority.
- [x] Stop mapping is `39,956 / 39,956`.
- [x] No depot, fleet size, battery value, demand growth rate, QUBO coefficient, QAOA depth, optimizer, scenario year, quantum hardware assumption, or delivery capacity was invented.
- [x] This file is a human-readable navigation document and does not replace machine-readable authority.

---

**Current Milestone = M1 Network Ready — DONE**  
**Current Research Stage = Routing Baseline**  
**Immediate Next Task = Define routing scope for delivery instances**
