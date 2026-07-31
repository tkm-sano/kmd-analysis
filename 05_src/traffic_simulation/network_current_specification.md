# Tokyo SUMO Network Current Specification

## Status

- Configuration: `ota_ward_sumo_network_v16`
- Approved v17 baseline policy: `ota_ward_attribute_resolution_policy_v17`
- Accepted relation-closure configuration: `ota_ward_relation_closure_v16`
- Created: 2026-07-18
- Last updated: 2026-07-31
- Configuration lineage date: 2026-07-16
- Typemap importer governance fixture: failed
- Permission materializer implementation: not_implemented
- Permission materializer runtime fixture: not_run
- Traffic simulation code test suite: passed
- Independent traffic-model validation: not_run
- Formal build input ready: no
- Formal network accepted: no
- Downstream experiment ready: no
- Specification state: current governed draft; formal execution is not authorized

The machine-readable authority is `reproducibility/config/traffic_simulation/sumo_network.yml`. Its typed state contract is `reproducibility/config/traffic_simulation/sumo_network.schema.json`, and cross-field invariants are enforced by `validate_sumo_network_config.py`. Normative component contracts are under `05_src/traffic_simulation/specifications`; artifact formats are under `reproducibility/config/traffic_simulation/schemas`. This document is a current-state summary rather than a second normative implementation contract. Historical decisions are kept in `03_data/metadata/acquisition/20260718_sumo_tokyo_motorized_typemap_design.md`.

The approved v17 baseline policy is
`reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml`,
with normative explanation in
`05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy.md`.
It fixes the permission authority, four-axis access specificity, Directed
Segment model, managed delivery vehicle, directional-lane restrictions, and
two-field resolution contract. Its implementation and runtime validation are
incomplete. The v16 run remains immutable historical evidence and is not
relabeled as a v17 result.

The baseline policy does not approve every normative annex or registry needed
for v17 execution. The conditional-expression grammar, permit registry, Japan
speed-rule table, and formal unpaved-surface rule remain pending approval.
Inputs that depend on any of them are not formal eligible until the applicable
annex or registry is approved, versioned, and hash-bound.

`Current result` uses exactly seven values:

- `passed`: implementation and the required runtime or real-data evidence both
  satisfy the acceptance condition.
- `failed`: a required fixture, validation, or acceptance check was run and a
  failing result was recorded.
- `not_implemented`: the required implementation does not exist.
- `not_run`: an implementation or prerequisite exists, but the required
  runtime check has not been run.
- `pending`: part of the requirement is implemented or verified, but the whole
  requirement does not satisfy its acceptance condition.
- `eligible`: an artifact satisfies the necessary conditions to be a candidate
  input to the next step; this does not imply passage of a higher-level gate.
- `ineligible`: a blocker, unapproved condition, or incompleteness prevents use
  as a formal input to the next step.

A missing implementation or absent runtime record is not reported as
`failed`. The typemap importer governance fixture is the failed fixture
recorded by the v16 authority; it is distinct from the unimplemented
Permission Materializer and its not-run runtime fixture.

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

The Permission Materializer is not implemented, and its required fixed-SUMO
runtime fixture has not been run. Permission governance therefore remains
formal-blocking.

The fixed materializer interface is SUMO 1.24.0 plain XML. A provisional conversion writes `.nod.xml`, lane-expanded `.edg.xml`, `.con.xml`, `.tll.xml` and exact `edge_provenance.json`; the materializer writes new `governed_permissions.edg.xml` and `governed_permissions.con.xml` files and never edits provisional files or final `net.xml` in place. Each external lane must carry exactly one OSM way ID through `param key="origId"`. Edge direction comes from exact source-node lineage indices. Coordinate-nearest matching and the sign of a SUMO edge ID are prohibited as formal direction evidence.

Resolver lane positions are OSM left-to-right as viewed in each respective travel direction, while SUMO lane indices are right-to-left. Forward and backward both use `sumo_index = n - 1 - p`; the Resolver does not reverse backward OSM lists. A partially empty edge keeps empty lanes as `disallow="all"`. Connections are explicit lane-to-lane candidates and are never synthesized. The pinned fixture must confirm these rules before real-data use.

A directed edge whose lanes all have a resolved empty permission set is not
generated, or is removed with its incident connections before TLS review. This
is a `materialization omission` derived from permission resolution, not an
`out_of_scope` exclusion and not a population change. A dedicated audit
artifact or manifest records at least `source_way_id`, `directed_segment_id`,
`resolver_tuple_ids`, `reason_code`, `expected_permission_set`,
`omitted_or_removed_edge_id`, `affected_connection_ids`, `configuration_hash`,
`permission_expectation_hash`, and `materializer_output_hash`.

The source Resolver tuples remain in the permission-completeness denominator.
Materialization omission is never counted in the excluded population. An empty
resolved permission set is distinct from `unresolved` or `conflict`; omission
caused by an unresolved or conflicting result is a formal blocker. Edge and
connection non-generation must be reproducible from the hash-bound audit.

The v16 Resolver and configuration still calculate the expected set through a
typemap-baseline intersection. That implementation is superseded for v17 and
must be migrated before a v17 full run. Static documentation of the new
authority does not make the current materializer or runtime fixture complete.

Four-axis access specificity means exactly the `spatial`, `vehicle`,
`temporal`, and `purpose` axes. `direction` and `lane` are target scope: they
first restrict candidate rules to the way/direction/lane tuple being resolved
and are not additional Pareto axes. General access tags,
vehicle-class-specific tags, directional tags, and lane-specific tags are
source-tag hierarchy and normalization inputs; they map to target scope or an
approved specificity axis rather than creating separate axes.

The governed processing order is:

1. Normalize source tags and map the tag hierarchy to target scope and the
   approved axes.
2. Restrict candidate rules by the `direction` and `lane` target scope.
3. Confirm the scenario context required by conditional rules.
4. Remove Pareto-dominated rules on the `spatial`, `vehicle`, `temporal`, and
   `purpose` axes.
5. Adopt multiple maximal rules once when they produce the same permission.
6. Stop differing maximal results with `ACCESS_SPECIFICITY_CONFLICT`.
7. Preserve lane-local provenance and emit a complete permission expectation.

This approved baseline algorithm is implemented only as an isolated utility;
production Resolver integration remains incomplete.

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

Access processing has three implementation responsibilities: static tag
normalization and scope mapping, conditional parsing and evaluation, and final
permission resolution. The baseline policy and normative explanation own the
four-axis comparison; this summary only states the execution boundary and does
not create a second rule definition.

`out_of_scope` never silently deletes an input record. Until the approved v17
Schema is explicitly revised, exclusion is recorded in a separate exclusion
manifest rather than by adding an unapproved `resolution_status` enum value.
Each entry records the reason, rule ID, affected road, direction and lane,
approver, approval date, and evidence SHA-256. If exclusions change the
population definition, a new population/configuration version is required;
the accepted v16 population of 26,220 ways is immutable. A v17 run reports the
input, governed, and excluded populations separately. `complete=true` uses the
declared governed population as its denominator, while permission completeness
uses every governed way/direction/lane tuple, including tuples whose edges are
later omitted during materialization. Excluded records remain accounted for
and cannot be used to disguise blockers as zero.

## Signal Structure

Signalized-junction selection and connection-to-TLS-link mapping are network structure. In pinned SUMO 1.24.0 plain XML, TLS connection/link records belong to `.tll.xml`, not the permission `.con.xml` connection type. Provisional TLS output is review evidence only. After the governed connection set is fixed, reviewers produce `governed_reviewed.con.xml`, `governed_reviewed.tll.xml` and a hash-bound review manifest. Every controlled connection must have a reviewed link index, and each phase-state length must equal the controlled-link count. A later connection or signal-structure change invalidates the review, calibration and validation.

SUMO's junction-joining heuristic is used only to extract candidates for treating multiple nearby OSM nodes as one SUMO junction. It does not determine whether road geometries cross or whether vehicles can move between them. The 10 m distance is a candidate-search width, not an acceptance rule. Formal conversion disables automatic joining and applies only reviewed joins recorded in the governed node file.

## Required Order

```text
freeze current state and v16 history
  -> approve remaining v17 normative decisions
  -> finalize specification, machine-readable configuration and Schema
  -> freeze independent fixtures and production-independent oracles
  -> implement vehicle-input validator
  -> integrate Directed Segments into production
  -> implement directional lanes
  -> implement static access normalization
  -> implement conditional parsing and evaluation
  -> integrate static and conditional rules into final permission expectations
  -> implement speed resolution
  -> implement formal evidence/imputation
  -> Resolver integration tests
  -> v17 full-population run
  -> resolve and independently review stop records
  -> Attribute Resolution Acceptance
  -> register environment/build manifest
  -> provisional structural build
  -> review junction joins and generate governed node file
  -> generate exact edge provenance
  -> Permission Materializer implementation
  -> Permission Materializer pinned runtime fixture
  -> materialize governed lane and connection permissions
  -> lane/connection post-audit
  -> fix final connection set
  -> signal/TLS review
  -> warning/exclusion audit
  -> structural quality gate
  -> publish immutable hash-bound acceptance artifacts
  -> final net.xml generation and SUMO 1.24.0 load
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

An environment/build manifest is required before a reproducible formal build.
Structural-quality thresholds must be preregistered before formal evaluation,
not selected after observing build results. Independent validation follows
calibration. The traffic-simulation code pytest suite is software verification
and does not substitute for independent empirical traffic-model validation.

## Acceptance Gates

Attribute Resolution Acceptance applies only to the Resolver's formal
attribute artifact. The v17 machine-readable gate must require all of the
following before acceptance:

- `complete=true`, `blockers=[]`, `review_required=0`, `stop_unresolved=0`, and
  formal `model_assumed=0`.
- Declared population, record, attribute-coverage, and permission-coverage
  denominators match the artifacts.
- `input population = governed population + excluded population`.
- The exclusion-manifest SHA-256 is recorded; every exclusion rule ID is
  registered; and its population version matches the configuration.
- Permission completeness uses every governed way/direction/lane tuple. A
  tuple remains in this denominator even if materialization later omits its
  edge.
- Classification and attribute-resolution JSON Schema validation, semantic
  validation, unchanged classification projection, record/self-hash,
  permission-completeness, and run-manifest checks pass.
- SHA-256 values are recorded for inputs, configuration, Schema, outputs,
  exclusion manifest, and production-independent oracle.
- `resolution_status` and `value_origin` are used as the v17 canonical fields.
  An artifact generated only with legacy `value_state` is not v17-eligible.
- Unregistered states, rules, stop codes, and exclusion rules are zero; and
  structural and formal artifacts are not mixed.
- Formal evidence/imputation is implemented and validated. While it is absent,
  the formal artifact cannot set `complete=true`.

Passing Attribute Resolution Acceptance does not approve a SUMO network.

SUMO Network Integration Acceptance is separate and requires all of the
following:

- The typemap importer governance fixture is `passed`.
- A specific Attribute Resolution Acceptance artifact is fixed as input.
- Governed junction-join review is complete, and the governed node file is
  hash-bound.
- Exact edge provenance is generated and validated.
- Permission Materializer implementation exists, and its pinned runtime
  fixture is `passed`.
- Governed lane and connection permissions exactly equal the Resolver
  expectation; lane/connection post-audit and turn-restriction mapping audit
  are `passed`.
- Every all-lanes-empty edge omission and affected connection is present in the
  hash-bound materialization-omission audit, without changing population or
  permission-completeness denominators.
- Signal/TLS review is complete; controlled-connection count and phase-state
  length agree.
- Warning/exclusion audit is `passed`.
- Structural-quality thresholds were fixed before evaluation and all are met.
- The environment/build manifest is registered.
- Immutable acceptance artifacts are published or registered and mutually
  bound by SHA-256.
- Final `net.xml` loads in SUMO 1.24.0 without post-generation editing.
- Left-hand-traffic and governed reachability audits pass.

This second gate alone can approve the formal network. These lists summarize
the existing authorities and required v17 state migration; this summary does
not replace their machine-readable contracts.

## Verification State

| Gate | Requirement | Actual implementation | Runtime/real-data evidence | Current result |
|---|---|---|---|---|
| History freeze | Registered PBF, relation scope, recursive closure and hashes | implemented for v16 | v16 real-data closure accepted; ordinary 581 and bus 3 restrictions retained; reference errors zero | eligible |
| History freeze | relation-closure `prepare` pipeline | implemented | v16 registered inputs reproduced identical PBF/XML/ID/role hashes twice | eligible |
| Normative decision | Remaining v17 annexes and registries | baseline policy fixed; conditional grammar, permit registry, Japan speed table, and formal unpaved rule not approved | dependent inputs remain formal-ineligible | pending |
| Contract finalization | v17 specification, machine-readable configuration, and Schema integration | baseline policy and base Schemas exist; production boundaries and v17 state configuration incomplete | isolated Schema tests only | pending |
| Fixture freeze | v17 independent fixtures and production-independent oracles | v16 fixtures/oracles exist; v17 coverage and hash-bound manifest incomplete | v17 integrated fixture run not available | pending |
| Resolver input | Managed vehicle profile | profile values, Schema, and static checks implemented | static profile and mass checks passed; runtime-boundary validation absent | pending |
| Resolver input | Vehicle-input validator | required validator does not exist | runtime check cannot run until implementation exists | not_implemented |
| Resolver | Directed Segment production integration | Schema and pure generator implemented; production mapping absent | unit generation passed; integrated runtime fixture not run | pending |
| Resolver | `oneway=-1` | pure generator unit generation passed; production mapping, Schema integration at production boundaries, relation mapping, and runtime fixture incomplete | one occurrence stopped in the registered structural Dry Run; not usable as formal build input | pending |
| Resolver | Directional lanes | baseline policy fixed; production integration incomplete | formal explicit-direction rule lacks integrated runtime evidence | pending |
| Resolver | Static access normalization and four-axis access specificity | Pareto comparison and conflict output implemented as an isolated utility; target-scope and production integration incomplete | isolated unit tests passed; production fixture not run | pending |
| Resolver | Conditional parsing and evaluation | approved baseline requires it; grammar annex and production implementation incomplete | runtime fixture not run | pending |
| Resolver | Final permission resolution | v16 permission artifact exists; v17 authority, target scope, and static/conditional integration incomplete | v16 fixture emits `complete=false` while blockers remain | pending |
| Resolver | Permission expectation JSON | full-way completeness gate and lane-local rule trace implemented in v16 shape; v17 migration incomplete | v16 fixture confirms `complete=false` and no normalized XML while blockers remain | pending |
| Resolver | Speed resolution | v16 value resolution exists; pending speed-rule annex and v17 production integration remain | no v17 runtime evidence | pending |
| Resolver | Formal attribute evidence/imputation | required implementation does not exist | formal completion cannot be evaluated until implementation exists | not_implemented |
| Resolver verification | Resolver integration tests | component tests exist; full v17 production-boundary integration is incomplete | no complete v17 integration run | pending |
| Resolver execution | v17 full-population runner and run | dedicated v17 runner is not implemented | v16 execution evidence is historical and is not v17 evidence | not_implemented |
| Resolver review | Stop-record resolution and independent review | process specified; v17 stop records do not yet exist | not runnable before v17 full-population run | not_run |
| Attribute acceptance | Attribute Resolution Acceptance | gate specified; v17 machine-readable gate and accepted artifact absent | acceptance not run | not_run |
| Network prerequisite | Typemap importer governance fixture | importer and fixture exist | fixture ran and failed | failed |
| Reproducible build | Environment/build manifest | required manifest implementation does not exist | isolated commands do not constitute a manifest | not_implemented |
| Structural build | Provisional structural build | small exploratory commands exist; governed build pipeline absent | no complete governed build manifest | not_implemented |
| Structural build | Junction-join review and governed node file | required review and generator do not exist | runtime review cannot run until implementation exists | not_implemented |
| Structural build | Exact edge provenance | contract exists; production generator/validator absent | no real-data provenance validation | not_implemented |
| Permission materialization | Permission Materializer implementation | contract fixed; implementation absent | runtime fixture cannot pass until implementation exists | not_implemented |
| Permission materialization | Permission Materializer pinned runtime fixture | fixture requirement exists; implementation prerequisite absent | not run | not_run |
| Permission materialization | Governed lane/connection permission materialization | materializer absent | cannot run until materializer implementation and fixture pass | not_implemented |
| Network audit | Lane/connection post-audit | required auditor does not exist | runtime audit cannot run until implementation exists | not_implemented |
| Network audit | Turn-restriction mapping audit | Directed Segment mapping requirements fixed; auditor incomplete | no integrated runtime evidence | pending |
| Network structure | Final connection set | procedure specified; production generation and review incomplete | no accepted final connection artifact | pending |
| Network structure | Post-permission signal/TLS review | required review implementation does not exist | runtime review cannot run until final connections exist | not_implemented |
| Network audit | Warning/exclusion audit | required auditor does not exist | known warnings alone are not an audit | not_implemented |
| Network acceptance | Structural quality gate | metrics fixed; thresholds not preregistered | gate not run | pending |
| Network acceptance | Immutable hash-bound acceptance artifacts | publication policy fixed; artifacts not issued | no published acceptance set | pending |
| Network acceptance | Final `net.xml` and SUMO 1.24.0 load | formal network not built; SUMO runtime exists | formal load not run | not_run |
| Network acceptance | SUMO Network Integration Acceptance | gate specified; prerequisites incomplete | acceptance not run | not_run |
| Downstream | Demand and observation inputs | incomplete | formal network prerequisite not satisfied | pending |
| Downstream | Calibration | design and inputs incomplete | calibration not run | not_run |
| Downstream | Independent traffic-model validation | protocol stage exists; accepted network and calibrated model absent | independent empirical validation not run | not_run |
| Downstream | Delivery, classical, and QAOA evaluation | comparison policy partially fixed; accepted inputs absent | formal evaluation not run | not_run |
| Software verification | Traffic simulation code pytest suite | implemented | latest recorded suite passed; retain the recorded count only in its evidence record | passed |

Pytest counts are progress indicators, not sufficient evidence. A passed code
suite does not mean formal network acceptance, calibration completion,
empirical traffic-model validity, independent validation completion, or
downstream experiment readiness. Each recorded test run must include commit,
container digest, exact command, collection hash, exit code, log hash and
timestamps.

## Summary and Remaining Formal Blockers

This revision makes state vocabulary, access-rule structure, execution order,
and the two acceptance gates explicit while retaining v16 as immutable
historical execution evidence. It does not promote this summary to an
authority or claim that v17 execution is available.

Remaining formal blockers include:

- approval and hash-binding of the conditional grammar, permit registry, Japan
  speed-rule table, and formal unpaved-surface rule;
- vehicle-input validation, v17 production integration, formal
  evidence/imputation, full-population runner, and independent stop review;
- the failed typemap importer governance fixture;
- environment/build manifest, governed provisional build, junction review,
  exact provenance, Permission Materializer, and pinned runtime fixture;
- lane/connection and turn-restriction audits, final connections, signal/TLS
  review, warning/exclusion audit, and preregistered structural thresholds;
- immutable acceptance artifacts, final SUMO 1.24.0 load, and both acceptance
  records;
- calibration and independent empirical traffic-model validation before any
  formal delivery, classical, or QAOA evaluation.
