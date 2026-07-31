# Tokyo SUMO Network Current Specification

## Status

- Configuration: `ota_ward_sumo_network_v16`
- Approved next policy: `ota_ward_attribute_resolution_policy_v17`
- Accepted relation-closure configuration: `ota_ward_relation_closure_v16`
- Created: 2026-07-18
- Last updated: 2026-07-31
- Configuration lineage date: 2026-07-16
- Typemap importer governance fixture: failed
- Permission materializer implementation: not_implemented
- Permission materializer runtime fixture: not_run
- Traffic simulation validation test suite: passed
- Formal build input ready: no
- Formal network accepted: no
- Downstream experiment ready: no
- Specification state: current governed draft; formal execution is not authorized

The machine-readable authority is `reproducibility/config/traffic_simulation/sumo_network.yml`. Its typed state contract is `reproducibility/config/traffic_simulation/sumo_network.schema.json`, and cross-field invariants are enforced by `validate_sumo_network_config.py`. Normative component contracts are under `05_src/traffic_simulation/specifications`; artifact formats are under `reproducibility/config/traffic_simulation/schemas`. This document is a current-state summary rather than a second normative implementation contract. Historical decisions are kept in `03_data/metadata/acquisition/20260718_sumo_tokyo_motorized_typemap_design.md`.

The approved policy for the next configuration is
`reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml`,
with normative explanation in
`05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy.md`.
It fixes the permission authority, four-axis access specificity, Directed
Segment model, managed delivery vehicle, directional-lane restrictions, and
two-field resolution contract. Its implementation and runtime validation are
incomplete. The v16 run remains immutable historical evidence and is not
relabeled as a v17 result.

Status values in this summary distinguish `passed`, `failed`,
`not_implemented`, `not_run`, `pending`, and `ineligible`. A missing
implementation or absent runtime record is not reported as `failed`. The
typemap importer governance fixture is the failed fixture recorded by the v16
authority; it is distinct from the unimplemented Permission Materializer and
its not-run runtime fixture.

The current `sumo_network.yml` is the v16 state authority and still places the
materializer and signal structure inside its legacy
`formal_build_input_ready` gate. That machine-readable v16 history is not
rewritten here. A v17 network-state configuration must express Attribute
Resolution Acceptance and SUMO Network Integration Acceptance as separate
gates before it can become the new state authority.

For a process-oriented view that separates operations, definitions, numeric
settings, mechanically derived values and pending decisions, see
`05_src/traffic_simulation/network_workflow_decisions_and_parameters.md`.

## Attribute Mapping

| OSM input | Resolver representation | SUMO representation |
|---|---|---|
| `lanes=*`, directional lane tags | total and direction-specific lane counts | `numLanes` and generated lanes |
| `maxspeed=*`, directional speed tags | governed speed in km/h before conversion | `speed` in m/s |
| `oneway=*` | governed directionality | generated edge directions |
| access, vehicle, class, direction and lane tags | expected permissions by way, direction and lane | lane `allow`/`disallow` and usable connections |

No unsupported explicit OSM value may be replaced by a structural placeholder. `oneway=-1`, directionally asymmetric speeds, unsupported conditionals, bidirectional single-lane allocation and unresolved permissions stop conversion until a governed representation exists.

An absent `oneway` tag is not itself classified as an unresolved travel direction. For an ordinary road, the Resolver preserves the source absence in its audit, derives the effective value `no` from the fixed OSM interpretation rule, records `derived_osm_rule`, and materializes that effective value for conversion. This is rule-based interpretation, not mode-value imputation. The approved v17 model represents travel directions as immutable-source Directed Segments and generates only the backward segment for `oneway=-1`. Until its generator, Schema integration, relation mapping, and runtime fixtures pass, production continues to stop on `oneway=-1`.

The accepted v16 closure contains 26,220 governed attribute-resolution
candidate ways; 13,494 intersect the final N03 Ota Ward analysis boundary.
These ways are not reviewed individually. Deterministic rules process ordinary
cases and the Dry Run records every decision, while human review is limited to
`unresolved`, `conflict`, `valid_but_unsupported`, `invalid` and unregistered
`unexpected` cases. A newly observed exception is first represented in the
decision table and a small fixture, then implemented and rerun over the
complete input. Direct one-off editing of the source OSM or a generated
`net.xml` is prohibited.

The historical v15 Dry Run contains 307 non-missing rule/data exception rows.
Twenty mutually exclusive exception-classification rules, normal, abnormal and
boundary fixtures, and a production-independent oracle are implemented. All
307 rows match exactly one rule; unmatched and overlapping counts are zero.
The value-free Classifier and the separate attribute-value Resolver have now
been executed over all 26,220 accepted v16 ways for both profiles. Each profile
contains 52,440 tuples and passes JSON Schema and semantic validation. The
structural artifact retains 785 stopped tuples; the formal artifact retains
24,741 stopped tuples and contains no structural placeholder. Classification
projections before and after resolution have identical SHA-256 values. This is
complete execution coverage, not formal-input acceptance: the formal artifact
remains `complete=false`.

## Network Scope

- Geography: Ota Ward boundary with retained acquisition-envelope connectors.
- Traffic side: Japanese left-hand traffic.
- Governed vClasses: `passenger`, `taxi`, `bus`, `coach`, `delivery`, `truck`, `motorcycle`.
- Mode scope: motorized-only throughout network generation, traffic simulation, delivery evaluation and method comparison; no multimodal network is planned within this research.
- `moped` is outside the governed delivery-research scope. Its class-specific OSM access tags do not affect the seven governed classes. Dedicated bus links remain in the network and allow `bus` only.
- The baseline managed vehicle is
  `managed_urban_ev_delivery_v1`: a research-model battery-electric
  `delivery` vehicle with a 3,500 kg maximum permissible mass, 1,500 kg
  unladen mass, 2,000 kg maximum payload, 4.70 m length, 1.70 m width,
  2.00 m height, and 2,000 kg maximum axle load. It has no hazardous-goods
  or permit assignment. It is not classified as OSM `hgv`. The profile is
  not a measured real vehicle and cannot switch to `truck` within an
  experiment.
- `highway=track` is excluded because its land-access function is outside the governed motorized network, not because it is necessarily unpaved.
- Surface state is evaluated independently from road function using `surface`, with `smoothness` and `tracktype` as supporting evidence. The formal unpaved-road rule is pending.

Overseas driving-behavior evidence, weather and incident data, and pedestrian-related fields in driving-behavior sources are retained for later-stage contextual or sensitivity analyses. They are not inputs to the core comparison. Pedestrian-related fields are covariates describing a motorized driver's context; they do not add pedestrian agents or a pedestrian network mode.

## Permission Governance

The approved v17 authority is the Resolver's expected permission set. Typemap
permissions are provisional topology candidates, not a formal upper bound.
Final permissions must equal the Resolver expectation and remain within the
managed vClass universe.

The resolver computes expected permissions before conversion. A dedicated materializer must write those permissions into the explicit input of the final `netconvert` run so that lanes and connections are built from the governed permissions.

Generated `net.xml` permissions must not be edited. Post-conversion processing is audit-only. Every lane and applicable connection must exactly match the expectation; otherwise the build stops, the pre-conversion input is corrected, and final `netconvert` is rerun.

This materializer and its fixed-SUMO runtime fixture are not implemented. Permission governance therefore remains formal-blocking.

The fixed materializer interface is SUMO 1.24.0 plain XML. A provisional conversion writes `.nod.xml`, lane-expanded `.edg.xml`, `.con.xml`, `.tll.xml` and exact `edge_provenance.json`; the materializer writes new `governed_permissions.edg.xml` and `governed_permissions.con.xml` files and never edits provisional files or final `net.xml` in place. Each external lane must carry exactly one OSM way ID through `param key="origId"`. Edge direction comes from exact source-node lineage indices. Coordinate-nearest matching and the sign of a SUMO edge ID are prohibited as formal direction evidence.

Resolver lane positions are OSM left-to-right as viewed in each respective travel direction, while SUMO lane indices are right-to-left. Forward and backward both use `sumo_index = n - 1 - p`; the Resolver does not reverse backward OSM lists. A partially empty edge keeps empty lanes as `disallow="all"`; a directed edge whose lanes are all empty is removed with incident connections before TLS review. Connections are explicit lane-to-lane candidates and are never synthesized. The pinned fixture must confirm these rules before real-data use.

The v16 Resolver and configuration still calculate the expected set through a
typemap-baseline intersection. That implementation is superseded for v17 and
must be migrated before a v17 full run. Static documentation of the new
authority does not make the current materializer or runtime fixture complete.

Applicable access rules are normalized on spatial, vehicle, temporal, and
purpose axes. Pareto-dominated rules are removed. Multiple maximal rules with
the same result are adopted once; differing results stop with
`ACCESS_SPECIFICITY_CONFLICT`. This algorithm is approved but is not yet
integrated into the production Resolver.

Conditional access enters the applicable-rule set only when the registered
scenario date, time, vehicle, weight, dimensions, and trip purpose provide all
required context and the expression evaluates true. Unsupported syntax,
missing context, or a permission result that changes within one simulation
interval remains formal-blocking. Approval of the conditional grammar, permit
registry, and Japan speed-rule table is still pending.

For bidirectional roads, the formal Resolver requires explicit `lanes:forward` and `lanes:backward`; equal division of an even total is structural-only, uses assumption ID `BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`, and is never formal eligible. Formal processing stops with `LANE_DIRECTIONAL_ALLOCATION_MISSING`. Structural imputation donors must themselves pass direction, lane, speed, conditional-tag and permission eligibility checks. Permission provenance is lane-local: a directional or lane-specific access tag is recorded only for the lanes to which it was applied.

New v17 artifacts use `resolution_status` and `value_origin` as canonical
fields under the approved v17 contract; they are not a proposal. Legacy
`value_state` is read compatibility only. The current v16
artifacts still use `value_state`; Schema, implementation, fixture, and
full-data migration remain required.

A v17 value is a formal candidate only when `resolution_status=resolved` and
`value_origin` is `source_explicit`, `source_normalized`, `rule_derived`,
`evidence_derived`, or an approved `derived_validated_model`.
`model_assumed` is never formal eligible.

Turn restrictions map the original relation's `from`, `via`, and `to`
members to Directed Segment candidates. A unique mapping may be adopted;
zero candidates stop with `RELATION_DIRECTED_MAPPING_MISSING`, and multiple
candidates stop with `RELATION_DIRECTED_MAPPING_AMBIGUOUS`. Directional tags
remain attached to source direction and target segment rather than being
destructively swapped on the source Way.

Access processing has three separate responsibilities. Static access
normalization compares spatial, vehicle, purpose, lane, direction, and
general/specific rules, removes Pareto-dominated rules, and selects the maximal
static rules. Conditional parsing and evaluation handles date, time, holiday,
vehicle, weight, dimensions, trip purpose, missing context, unsupported
syntax, and within-interval changes. Final permission resolution combines the
static and conditional results, adopts multiple maximal rules only when their
results agree, stops differing maximal results with
`ACCESS_SPECIFICITY_CONFLICT`, preserves lane-local provenance, and emits the
complete permission expectation. The approved v17 policy and its normative
explanation own these rules; this summary does not redefine them.

`out_of_scope` never silently deletes an input record. Until the approved v17
Schema is explicitly revised, exclusion is recorded in a separate exclusion
manifest rather than by adding an unapproved `resolution_status` enum value.
Each entry records the reason, rule ID, affected road, direction and lane,
approver, approval date, and evidence SHA-256. If exclusions change the
population definition, a new population/configuration version is required;
the accepted v16 population of 26,220 ways is immutable. A v17 run reports the
input, governed, and excluded populations separately. `complete=true` uses the
declared governed population as its denominator, while permission completeness
uses every governed way/direction/lane tuple. Excluded records remain
accounted for and cannot be used to disguise blockers as zero.

## Signal Structure

Signalized-junction selection and connection-to-TLS-link mapping are network structure. In pinned SUMO 1.24.0 plain XML, TLS connection/link records belong to `.tll.xml`, not the permission `.con.xml` connection type. Provisional TLS output is review evidence only. After the governed connection set is fixed, reviewers produce `governed_reviewed.con.xml`, `governed_reviewed.tll.xml` and a hash-bound review manifest. Every controlled connection must have a reviewed link index, and each phase-state length must equal the controlled-link count. A later connection or signal-structure change invalidates the review, calibration and validation.

SUMO's junction-joining heuristic is used only to extract candidates for treating multiple nearby OSM nodes as one SUMO junction. It does not determine whether road geometries cross or whether vehicles can move between them. The 10 m distance is a candidate-search width, not an acceptance rule. Formal conversion disables automatic joining and applies only reviewed joins recorded in the governed node file.

## Required Order

```text
freeze current state and v16 history
  -> approve remaining v17 decisions
  -> finalize specification, machine-readable configuration and Schema
  -> freeze independent fixtures and oracles
  -> integrate Directed Segments into production
  -> implement directional lanes
  -> implement static access normalization
  -> implement conditional parsing and evaluation
  -> integrate static and conditional rules into final permission expectations
  -> implement speed resolution
  -> Resolver integration tests
  -> v17 full-population run
  -> resolve stop records
  -> Attribute Resolution Acceptance
  -> provisional structural build and exact edge provenance
  -> Permission Materializer
  -> final connection set
  -> signal/TLS review
  -> SUMO Network Integration Acceptance
  -> demand
  -> calibration
  -> independent validation
  -> delivery, classical and QAOA evaluation
```

Small-fixture provisional builds, Permission Materializer development, and
pinned SUMO runtime fixtures may proceed in parallel with resolution of
attribute stop records. A structural/provisional network exists only to
develop and review topology, direction, connections, provenance, and the
materializer. It may contain structural assumptions and may be generated as a
small fixture or development output before all formal attribute stops are
resolved. It is not a publishable real-data formal network and is invalid for
travel-time, capacity, delivery, solver comparison, or calibration results.

A formal network takes an Attribute Resolution Acceptance artifact as input,
reflects governed permissions, final connections, and reviewed TLS structure,
and becomes an accepted formal network only after SUMO Network Integration
Acceptance. Downstream research may use it only after independent validation.
Calibration performed on a network containing structural placeholders cannot
be transferred to the formal network. Real-data formal network acceptance may
not begin before Attribute Resolution Acceptance.

## Acceptance Gates

Attribute Resolution Acceptance applies only to the Resolver's formal
attribute artifact. It requires `complete=true`, `blockers=[]`,
`review_required=0`, `stop_unresolved=0`, `model_assumed=0`, matching declared
population/record/coverage denominators, JSON Schema and semantic validation,
an unchanged classification projection, recorded SHA-256 values for inputs,
configuration, Schema, outputs and the independent oracle, zero unregistered
states/rules/stop codes, and no structural/formal mixture. Passing this gate
does not approve a SUMO network.

SUMO Network Integration Acceptance follows the provisional build, exact edge
provenance, Permission Materializer, lane and connection permission
materialization, final connection set, signal/TLS review, final `net.xml`
generation, and SUMO 1.24.0 load. It audits lanes, connections, turn
restrictions, left-hand traffic, warnings, exclusions, and reachability. This
second gate alone can approve the formal network.

## Verification State

| Gate | Requirement | Actual implementation | Runtime/real-data evidence | Current result |
|---|---|---|---|---|
| Build input | Registered PBF, relation scope, recursive closure and hashes | implemented | v16 real-data closure accepted; ordinary 581 and bus 3 restrictions retained; reference errors zero | eligible |
| Build input | Typemap importer governance fixture | implemented | XSD passed; fixture failed | failed |
| Build input | Attribute resolver | v16 value-free classification and value resolution implemented; v17 authority and two-field state migration incomplete | all 26,220 v16 ways and 52,440 tuples per profile generated; Schema and semantic checks pass; structural 785 and formal 24,741 stopped tuples remain; formal placeholders zero | pending |
| Build input | Permission expectation JSON | full-way completeness gate and lane-local rule trace implemented | fixture confirms `complete=false` and no normalized XML while blockers remain | pending |
| Build input | Permission materializer implementation | contract fixed; implementation absent | not applicable | not_implemented |
| Build input | Permission materializer runtime fixture | depends on materializer implementation | not run | not_run |
| Build input | `oneway=-1` | Directed Segment Schema and pure generator implemented; production mapping absent; current pipeline remains fail-closed | unit generation passed; one occurrence confirmed and stopped in registered structural Dry Run; integrated runtime fixture not run | conditional |
| Build input | Managed vehicle profile | v17 model values, Schema and static consistency checks implemented; runtime-boundary validator not implemented | static profile and mass consistency validation passed | pending |
| Build input | Access specificity | four-axis Pareto comparison, maximal-rule selection and conflict output implemented as an isolated utility; production integration absent | registered unit tests passed; conditional-expression runtime fixture not run | pending |
| Build input | Formal attribute evidence/imputation | not implemented | not run | pending |
| Build input | Junction join review/node file | not implemented | not run | pending |
| Build input | Post-permission signal/TLS review | not implemented | not run | pending |
| Build input | Vehicle-input validator | not implemented | not run | pending |
| Build input | relation-closure `prepare` pipeline | implemented | v16 registered inputs reproduced identical PBF/XML/ID/role hashes twice | eligible |
| Build input | Environment/build manifest | not implemented | isolated commands only | pending |
| Network acceptance | Lane/connection post-audit | not implemented | not run | pending |
| Network acceptance | Warning/exclusion audit | not implemented | known warnings recorded only | pending |
| Network acceptance | Structural quality gate | metrics fixed; thresholds pending | not run | pending |
| Network acceptance | Immutable small artifacts | policy fixed; not published | not run | pending |
| Network acceptance | Formal network and SUMO load | not built | not run | pending |
| Downstream | Candidate-subgraph review | scope fixed; not implemented | requires accepted network | pending |
| Downstream | Demand and observation inputs | not implemented | not run | pending |
| Downstream | Calibration design | incomplete | thresholds, seeds and warm-up pending | pending |
| Downstream | Optimization comparison design | policy partially fixed | instances and budgets pending | pending |
| Validation | Traffic simulation pytest suite | implemented | latest recorded suite passed; retain the recorded count only in its evidence record | passed |

Pytest counts are progress indicators, not sufficient evidence. Each recorded test run must include commit, container digest, exact command, collection hash, exit code, log hash and timestamps.
