# Ota Ward SUMO Network — v17 Attribute Resolution Specification

## Document control

- Policy ID: `ota_ward_attribute_resolution_policy_v17`
- Document role: normative component specification
- Target configuration: the first v17 network-state configuration derived from `ota_ward_sumo_network_v16`
- Source population lineage: `ota_ward_relation_closure_v16`
- SUMO interface version: `1.24.0`
- Specification state: approved normative repository baseline
- Approved by: repository owner directive
- Approval date: 2026-08-03
- Implementation state: not implied by this document
- Historical rule: v16 inputs, outputs, logs, hashes and acceptance evidence remain immutable and shall not be relabeled as v17 results

This specification fixes the v17 contract for attribute resolution. It does not approve a formal SUMO network and does not assert that the described implementation, fixtures or runtime evidence already exist.

## 1. Purpose

The purpose of v17 Attribute Resolution is to transform registered OpenStreetMap source records into deterministic, auditable and profile-specific attribute artifacts before SUMO network generation.

The Resolver shall distinguish:

- the state of a resolution decision;
- the origin of an effective value;
- the immutable source representation;
- the generated direction- and lane-specific representation;
- development-only structural assumptions;
- formal research inputs;
- governed population exclusions;
- unresolved, conflicting, invalid and unsupported records.

The Resolver shall not silently repair unsupported explicit OSM values, edit source OSM data, edit generated `net.xml`, or use input order as an implicit conflict-resolution rule.

## 2. Normative language

The terms **shall**, **shall not**, **must**, **must not**, **should** and **may** are normative.

- **shall / must**: mandatory for v17 conformance;
- **shall not / must not**: prohibited;
- **should**: recommended unless a recorded exception is approved;
- **may**: permitted but not required.

Examples are explanatory unless explicitly marked as fixture requirements.

## 3. Authority and precedence

The v17 authority shall consist of the following mutually consistent artifacts:

1. machine-readable v17 configuration;
2. JSON Schema for v17 records and manifests;
3. this component specification;
4. registered rule, value, vehicle, stop-code and assumption registries;
5. independent fixtures;
6. production-independent oracles;
7. semantic validators;
8. execution and acceptance manifests.

If these artifacts disagree, the run shall stop. The disagreement shall not be resolved by allowing the production implementation to choose one interpretation.

Precedence for correction shall be:

1. approved decision record;
2. machine-readable configuration and registries;
3. JSON Schema and semantic invariants;
4. this specification;
5. implementation.

The current-state summary document is not a second implementation contract.

## 4. External basis and project-specific decisions

### 4.1 Externally grounded principles

The following principles are adopted from public documentation and methodological guidance:

- OSM `forward` and `backward` are relative to the original Way node order.
- `oneway=-1` denotes one-way travel opposite to the OSM Way direction.
- direction- and lane-specific tags apply to the indicated direction and lane positions.
- OSM access restrictions may combine general, vehicle-specific, directional, conditional and lane-specific forms.
- SUMO plain XML is the editable network input representation; generated `.net.xml` shall not be manually edited.
- network coding errors shall be addressed before calibration.
- calibration, validation and software testing are different activities.
- provenance shall record inputs, processing activities and derived outputs.
- acceptance criteria shall be defined before a model or simulation artifact is accepted for use.
- deterministic JSON hashes require a fixed canonicalization procedure.

### 4.2 Project-specific normative decisions

The following are v17 project decisions rather than direct OSM or SUMO requirements:

- the two-field `resolution_status` / `value_origin` contract;
- the exact enum values defined below;
- the Directed Segment identifier;
- the separation between target scope and four semantic specificity axes;
- the set-inclusion/Pareto rule-combination algorithm;
- the structural and formal profile boundary;
- the prohibition of `model_assumed` values in formal artifacts;
- the Attribute Resolution Acceptance gate;
- the required hashes, manifests and zero-blocker conditions;
- the implementation order fixed in Section 21.

These decisions shall be verified by registered fixtures and independent oracles.

## 5. Scope

### 5.1 Geographic and modal scope

- Geography: Ota Ward analysis boundary with registered acquisition-envelope connectors.
- Traffic side: Japanese left-hand traffic.
- Governed SUMO vClasses:
  - `passenger`
  - `taxi`
  - `bus`
  - `coach`
  - `delivery`
  - `truck`
  - `motorcycle`
- The v17 core network is motorized-only.
- `moped`, bicycle, pedestrian, rail and ship modes are outside the governed permission universe unless a later configuration version explicitly adds them.
- A tag for a non-governed class shall not change the permission of a governed class.

### 5.2 Managed vehicle context

The baseline managed vehicle is `managed_urban_ev_delivery_v1`.

Its registered properties shall be read from the vehicle registry rather than duplicated in production code. The current intended values are:

- SUMO vClass: `delivery`
- maximum permissible mass: 3,500 kg
- unladen mass: 1,500 kg
- maximum payload: 2,000 kg
- length: 4.70 m
- width: 1.70 m
- height: 2.00 m
- maximum axle load: 2,000 kg
- hazardous-goods assignment: none
- permit assignment: none

The vehicle is not OSM `hgv` and shall not switch to `truck` within an experiment.

### 5.3 Attribute scope

v17 governs at least the following attributes:

- travel direction;
- directional lane allocation;
- lane position;
- maximum speed;
- static access;
- conditional access;
- final lane permission expectation;
- relation-to-Directed-Segment mapping;
- provenance and resolution state.

Surface information may be retained as contextual evidence. It shall not remove a governed road in v17 unless an explicit, versioned exclusion rule is registered. `highway=track` remains outside scope because of road function, not because a particular surface is assumed.

## 6. Core entities and record identity

### 6.1 Immutable source entities

The following source entities are immutable during resolution:

- OSM Node;
- OSM Way;
- OSM Relation;
- registered source PBF/XML;
- relation-closure artifact.

Production code shall not:

- reverse the stored node order of a source Way;
- replace a source tag;
- add a missing source tag;
- directly edit the registered source artifact;
- directly edit a generated `net.xml`.

Corrections to source data require a new registered source version.

### 6.2 Resolver tuple

A Resolver tuple shall be identified by the following dimensions, as applicable:

- `configuration_id`
- `population_version`
- `profile`
- `source_way_id`
- `directed_segment_id`
- `source_direction`
- `lane_position`
- `vehicle_class`
- `attribute_name`
- `scenario_context_id`

An attribute that is resolved before lanes or vehicle classes are expanded may use `null` for dimensions that are not applicable. `null` shall not be confused with an omitted required field.

### 6.3 Deterministic record ID

`record_id` shall be the SHA-256 hash of the RFC 8785 canonical JSON representation of the record-key object.

The record-key object shall contain only identity fields. It shall not contain mutable results, timestamps or explanatory text.

A separate `classification_record_id` shall identify the value-free classification decision. Resolution shall not overwrite the classification identity.

### 6.4 Minimum record structure

Every v17 resolution record shall contain:

```yaml
schema_version:
configuration_id:
population_version:
profile:
record_id:
classification_record_id:
source_way_id:
directed_segment_id:
source_direction:
lane_position:
vehicle_class:
attribute_name:
source_observations:
resolution_status:
value_origin:
effective_value:
rule_ids:
evidence_ids:
assumption_ids:
stop_code:
review_required:
provenance:
```

Fields that are not applicable shall use the Schema-defined `null` value. Required fields shall not be silently omitted.

## 7. Resolution state contract

### 7.1 Canonical field: `resolution_status`

The allowed values are:

| Value | Meaning |
|---|---|
| `resolved` | One materializable effective value has been determined under the active profile. |
| `unresolved` | Required information or an approved rule is missing. |
| `conflict` | Applicable rules, source statements or evidence require different results. |
| `invalid` | A source or generated value violates registered syntax, type, range or consistency rules. |
| `valid_but_unsupported` | The source value is valid in its source system but v17 has no approved representation or evaluator for it. |

`unexpected` and `out_of_scope` are not permitted `resolution_status` values.

An unregistered state is a schema error and formal blocker.

### 7.2 Canonical field: `value_origin`

The allowed values are:

| Value | Meaning | Formal eligibility |
|---|---|---:|
| `source_explicit` | The effective value is explicitly present and directly applicable in the source. | yes |
| `source_normalized` | An explicit source value is converted to a registered canonical equivalent without changing meaning. | yes |
| `rule_derived` | The value is deterministically derived by a registered interpretation rule. | yes |
| `evidence_derived` | The value is derived by an approved evidence-resolution method with traceable inputs. | yes |
| `derived_validated_model` | The value is produced by an independently validated and approved model. | yes |
| `model_assumed` | The value is a development assumption without formal evidential status. | no |

Legacy `derived_osm_rule` shall map to `rule_derived`. It shall not be emitted by a v17 writer.

### 7.3 Cross-field invariants

For `resolution_status=resolved`:

- `effective_value` shall be present;
- `value_origin` shall be non-null;
- `stop_code` shall be null;
- at least one source, rule, evidence or assumption reference shall explain the value;
- a formal record shall not contain `value_origin=model_assumed`;
- a formal record shall not contain an assumption ID.

For any non-resolved status:

- `effective_value` shall be null;
- `value_origin` shall be null;
- `stop_code` shall contain one registered code;
- unresolved candidate values may be preserved only in audit fields;
- the record shall not be materialized.

For `conflict`:

- at least two conflicting candidates and their provenance shall be recorded.

For `valid_but_unsupported`:

- the original source key and value shall be retained;
- the implementation shall not replace the value with a typemap or modal default.

### 7.4 Legacy compatibility

`value_state` is read compatibility only.

A v17 writer shall not emit `value_state`.

Legacy-to-v17 migration shall use an explicit mapping registry. A legacy value without a registered mapping shall stop with:

```text
LEGACY_STATE_MAPPING_UNSUPPORTED
```

No mapping may be inferred from field names or surrounding records.

## 8. Profiles

### 8.1 Structural profile

The structural profile exists only for:

- topology and direction development;
- lane-structure development;
- connection-candidate development;
- provenance development;
- Permission Materializer development;
- small-fixture SUMO runtime checks.

It may use only registered structural assumptions.

It shall not be used for:

- travel-time results;
- capacity results;
- delivery evaluation;
- classical/quantum solver comparison;
- calibration;
- validation;
- publication as a real-data formal network.

### 8.2 Formal profile

The formal profile is the only profile eligible for Attribute Resolution Acceptance.

A formal record is materializable only when:

```text
resolution_status = resolved
```

and:

```text
value_origin ∈ {
  source_explicit,
  source_normalized,
  rule_derived,
  evidence_derived,
  derived_validated_model
}
```

`model_assumed` is prohibited.

### 8.3 Registered structural assumptions

At minimum, v17 may register the following structural-only assumptions:

- `BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`
- `STRUCTURAL_TYPEMAP_SPEED_DEFAULT_V1`
- `STRUCTURAL_TYPEMAP_PERMISSION_CANDIDATE_V1`

Each assumption record shall include:

```yaml
assumption_id:
affected_attribute:
applicability_predicate:
generated_value_rule:
prohibited_source_conditions:
reason:
approver:
approval_date:
configuration_version:
```

An assumption shall never override:

- an unsupported explicit OSM value;
- an invalid source value;
- a conflict;
- `oneway=-1`;
- directionally asymmetric explicit values;
- an unsupported conditional expression;
- an unresolved permission;
- a bidirectional single-lane allocation.

## 9. Directed Segment model

### 9.1 Definition

A Directed Segment is a travel-direction representation derived from an immutable source Way interval.

Its identity shall be:

```text
ds:{source_way_id}:{source_start_index}:{source_end_index}:{source_direction}
```

where:

- `source_start_index < source_end_index`;
- indices refer to the original source Way node sequence;
- `source_direction` is `forward` or `backward`;
- the same canonical source interval is used for both directions.

For a backward segment, geometry may be materialized in reverse traversal order, but the source Way and canonical interval shall remain unchanged.

### 9.2 Direction meaning

- `forward`: travel follows the original OSM Way node order.
- `backward`: travel is opposite to the original OSM Way node order.

The sign or spelling of a SUMO edge ID shall not be formal direction evidence.

Coordinate-nearest matching shall not be formal direction evidence.

Direction shall be established through exact source-node lineage.

### 9.3 Base `oneway` normalization

The following explicit values shall be supported:

| Source value | Canonical value | Origin |
|---|---|---|
| `yes` | `yes` | `source_explicit` |
| `1` | `yes` | `source_normalized` |
| `true` | `yes` | `source_normalized` |
| `no` | `no` | `source_explicit` |
| `0` | `no` | `source_normalized` |
| `false` | `no` | `source_normalized` |
| `-1` | `-1` | `source_explicit` |
| `reverse` | `-1` | `source_normalized` |

Unregistered explicit values shall not be replaced by a default.

Syntactically invalid values shall stop with `ONEWAY_VALUE_INVALID`.

Valid but unsupported values shall stop with `ONEWAY_VALUE_UNSUPPORTED`.

### 9.4 Directed Segment generation

- canonical `yes`: generate forward segments only;
- canonical `no`: generate forward and backward segments;
- canonical `-1`: generate backward segments only.

For `oneway=-1`, production code shall not reverse the source Way and relabel it as forward.

### 9.5 Missing `oneway`

When `oneway` is absent, the Resolver shall apply the registered `oneway_rule_registry` in deterministic priority order.

The registry shall cover:

1. registered OSM implicit one-way cases;
2. registered road-class-specific cases;
3. the ordinary-road default.

For an ordinary road, the default rule shall be:

```yaml
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
effective_value: "no"
value_origin: rule_derived
```

The source absence shall remain visible in audit data.

If no rule matches, resolution shall stop with `ONEWAY_RULE_NOT_REGISTERED`.

### 9.6 Class-specific directional exceptions

A governed class-specific directional rule shall not mutate base source direction.

The generated topology shall be the union of directions needed by at least one governed class. Final access permissions shall restrict each direction to the appropriate governed classes.

An unsupported class-specific topology exception shall stop rather than being ignored.

### 9.7 Turn-restriction relation mapping

Each original relation member shall be mapped to Directed Segment candidates using:

- exact source Way membership;
- exact source-node lineage;
- the relation `via` member;
- the source direction;
- registered turn-restriction semantics.

Candidate counts shall be handled as follows:

| Candidate count | Result |
|---:|---|
| 1 | adopt the unique candidate |
| 0 | stop with `RELATION_DIRECTED_MAPPING_MISSING` |
| 2 or more | stop with `RELATION_DIRECTED_MAPPING_AMBIGUOUS` |

Directional source tags shall remain attached to their source direction. They shall not be destructively swapped on the source Way.

### 9.8 Directed Segment acceptance tests

Fixtures shall demonstrate:

- `oneway=yes` generates forward only;
- `oneway=no` generates both directions;
- `oneway=-1` generates backward only;
- missing ordinary-road `oneway` derives `no`;
- source Way bytes and hash are unchanged;
- split intervals have stable IDs;
- relation mapping has unique, missing and ambiguous cases;
- no direction depends on SUMO edge-ID sign;
- rerunning with the same input produces identical Directed Segment hashes.

## 10. Directional lane resolution

### 10.1 Lane concepts

The Resolver shall distinguish:

- total moving lanes;
- forward lanes;
- backward lanes;
- both-ways lanes;
- lane-position vectors;
- SUMO lane indices.

Parking lanes and shoulders shall not be counted as governed moving lanes unless a registered rule explicitly classifies them as such.

### 10.2 One-way roads

For a one-way road:

- an explicit directional count for the active direction is adopted;
- an explicit total lane count may be assigned to the active direction by a registered deterministic rule;
- a directional count for the inactive direction greater than zero is a conflict unless a governed class-specific exception requires that direction;
- `oneway=-1` assigns the active directional lane structure to backward.

`DEC-P13-LANE-COUNT-FROM-ROAD-LANE-VECTOR-001` approves one additional formal
deterministic rule for a missing one-way moving-lane count. When canonical
`oneway` is `yes` or `-1`, explicit total and active-direction lane counts are
absent, lane-conditional semantics are absent, and at least one exact
`turn:lanes`, `destination:lanes`, or `destination:ref:lanes` tag exists, the
Resolver may adopt their common positive pipe-field count as the active and
total moving-lane count. The result uses `value_origin=rule_derived`, is formal
eligible, preserves every source vector, and records rule ID
`OSM_ONEWAY_ROAD_LANE_VECTOR_TO_ACTIVE_COUNT_V1`.

This authority does not extend to general `*:lanes`, bicycle, cycleway, bus,
access, conditional, or unknown vector families. Approved vectors with
different field counts remain fail-closed. An explicit lane count remains
authoritative and every source vector is subsequently validated against it;
mismatch stops with `LANE_VECTOR_LENGTH_MISMATCH`.

### 10.3 Bidirectional roads

For a formal bidirectional road, directional allocation shall be established by one of:

1. explicit `lanes:forward`, `lanes:backward` and, where applicable, `lanes:both_ways`;
2. an approved deterministic `rule_derived` interpretation;
3. an approved `evidence_derived` method;
4. an approved `derived_validated_model`.

If a total lane count is present, the following consistency equation shall hold:

```text
lanes = lanes:forward + lanes:backward + lanes:both_ways
```

A mismatch shall stop with `LANE_COUNT_CONFLICT`.

`DEC-P13-LANE-BIDIRECTIONAL-TOTAL-2-FORMAL-001` approves exactly one
deterministic bidirectional total-lane interpretation for the v17 formal
profile: when canonical `oneway=no`, `lanes=2`, `lanes:forward`,
`lanes:backward`, `lanes:both_ways`, lane-conditional, reversible and
alternating evidence are absent, the Resolver may derive
`forward=1`, `backward=1`, and `both_ways=0` with
`value_origin=rule_derived` and rule ID
`OSM_BIDIRECTIONAL_TOTAL_2_TO_ONE_ONE_V1`. This decision does not generalize
arithmetic complement or structural even split to `lanes=4`, higher even
totals, odd totals, single-lane bidirectional roads, missing lane counts, or
one-way lane-count missing cases.

`DEC-P13-LANE-BIDIRECTIONAL-SHARED-SINGLE-LANE-001` approves a separate
deterministic source-semantic rule. When canonical `oneway=no`, `lanes=1`, and
the registered strict guards exclude directional counts, `lanes:both_ways`,
motorized oneway conditional, reversible/alternating, lane-conditional,
lane-vector, and non-current lifecycle evidence, the Resolver emits
`kind=shared_bidirectional_single_moving_lane`, physical moving-lane count one,
pre-access source directions `forward` and `backward`, and zero dedicated
directional lanes with `value_origin=rule_derived` and rule ID
`OSM_BIDIRECTIONAL_TOTAL_1_TO_SHARED_SINGLE_V1`.

This rule does not create `forward=1` plus `backward=1`, does not rewrite the
source as `lanes:both_ways=1`, and grants no access, priority, passing,
alternating, capacity, or SUMO behavior. Target materialization is a separate
record. While no approved shared-physical-lane materializer exists, no segment
lane tuple is emitted and the target attempt is acceptance-blocked by
`LANE_SHARED_PHYSICAL_MATERIALIZATION_UNSUPPORTED` while the source semantic
record remains resolved. Every other odd or single-lane case retains the
existing fail-closed behavior.

If directional allocation is missing, the formal profile shall stop with:

```text
LANE_DIRECTIONAL_ALLOCATION_MISSING
```

### 10.4 Structural even split

The structural profile may apply `BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1` only when:

- the road is bidirectional;
- total moving lanes are explicit and positive;
- total moving lanes are even;
- no directional lane count is present;
- no `lanes:both_ways` is present;
- no lane-conditional value applies;
- no explicit contradictory lane evidence exists.

The result shall use `value_origin=model_assumed`.

Odd totals, single-lane bidirectional roads and explicit asymmetric evidence shall not be structurally split by this assumption.

### 10.5 Lane-vector consistency

For each directional lane vector:

- the number of entries shall equal the resolved directional lane count;
- empty entries shall remain explicit empty lane values;
- an omitted vector shall not be treated as an all-empty vector;
- inconsistent vector lengths shall stop with `LANE_VECTOR_LENGTH_MISMATCH`.

### 10.6 Lane orientation and SUMO mapping

Resolver lane positions shall be indexed left-to-right as viewed in the respective travel direction:

```text
lane_position = 0  # leftmost in travel direction
```

SUMO lane indices are right-to-left. Therefore:

```text
sumo_index = lane_count - 1 - lane_position
```

The same equation shall be used for forward and backward Directed Segments.

The Resolver shall not reverse a backward OSM lane vector a second time.

## 11. Speed resolution

### 11.1 Canonical unit

Resolver speeds shall be represented in km/h.

Materialization into SUMO plain XML shall convert to m/s using:

```text
speed_mps = speed_kmh / 3.6
```

Unit conversion shall not change `value_origin`.

### 11.2 Priority of speed sources

For each Directed Segment, speed shall be resolved in the following order:

1. applicable explicit directional `maxspeed`;
2. applicable explicit general `maxspeed`;
3. applicable supported conditional speed;
4. registered symbolic-value rule;
5. registered Japan road-class speed rule;
6. approved evidence method;
7. structural-only typemap assumption.

A lower-priority source shall not override a higher-priority applicable source.

### 11.3 Explicit and symbolic values

Numeric source values shall be normalized with their registered unit.

Symbolic values such as national or urban defaults shall be resolved only through the versioned Japan speed-rule registry.

If a symbolic value or absent speed has no registered rule, formal resolution shall stop with `SPEED_RULE_NOT_REGISTERED`.

Invalid values shall stop with `SPEED_VALUE_INVALID`.

Valid but unsupported values shall stop with `SPEED_VALUE_UNSUPPORTED`.

### 11.4 Directional asymmetry

Different valid forward and backward speeds shall remain separate.

A directionally asymmetric explicit speed shall never be replaced by one symmetric structural value.

### 11.5 Conditional speed

Conditional speed shall use the same scenario interval and grammar-governance principles as conditional access.

Missing required context shall stop with `SPEED_CONDITIONAL_CONTEXT_MISSING`.

If the effective speed changes within one simulation interval, the run shall either split the scenario interval through an approved scenario transformation or stop with `SPEED_WITHIN_INTERVAL_CHANGE`.

The Resolver shall not average changing speed limits over an interval.

## 12. Access-rule normalized representation

### 12.1 AccessRule record

Each parsed access statement shall be normalized to an `AccessRule` containing at least:

```yaml
rule_id:
source_key:
source_value:
source_element:
target_scope:
spatial_domain:
vehicle_domain:
temporal_domain:
purpose_domain:
effect:
authorization_requirement:
source_order:
provenance:
```

`source_order` may be used only where OSM semantics explicitly depend on order within the same conditional tag. It shall not resolve conflicts between independent tags or records.

### 12.2 Target scope

Target scope shall be separate from the four semantic specificity axes.

Allowed scope components are:

```yaml
direction_scope:
  - forward
  - backward
  - both

lane_scope:
  type: all | explicit_positions
  positions: []
```

A rule becomes a candidate only for tuples contained in its target scope.

- a non-directional, non-lane rule targets all applicable Directed Segments and lanes;
- a directional rule targets only the stated source direction;
- a lane rule targets only its registered lane positions;
- lane-local provenance shall not be copied to other lanes.

### 12.3 Four semantic specificity axes

The four axes are:

1. `spatial`
2. `vehicle`
3. `temporal`
4. `purpose`

#### Spatial domain

Spatial domains shall be represented as explicit sets or registered predicates over the governed population.

Typical containment levels are:

```text
network default
⊇ road-type default
⊇ source-element explicit rule
⊇ source-subsegment explicit rule
```

Direction and lane are excluded from this axis because they are represented in target scope.

#### Vehicle domain

Vehicle domains shall be explicit subsets of the governed vClass universe.

Containment shall be calculated through the registered vehicle ontology, not string similarity.

A more specific transport mode may override a less specific parent mode because its vehicle set is a proper subset.

Governed-domain projection shall not erase a registered source transport-mode
ancestry relation. When a child and parent project to the same governed vehicle
set, the registered child remains strictly more vehicle-specific for that set.
No ancestry may be inferred from equal projected sets or key-name similarity.

#### Temporal domain

Temporal domains shall denote sets of instants over the registered scenario horizon.

A conditional time range is more specific than an unconditional rule when its temporal set is a proper subset.

#### Purpose domain

Purpose domains shall denote registered trip-purpose and authorization states, including as applicable:

- general travel;
- destination access;
- delivery;
- customers;
- agricultural use;
- forestry use;
- private authorization;
- permit authorization.

The managed vehicle's trip purpose and authorization context shall be explicit in the scenario context.

### 12.4 Scope-and-axis dominance

Rule A dominates Rule B for a given tuple when all of the following hold:

1. A's target scope is equal to or narrower than B's target scope;
2. A's spatial domain is a subset of B's spatial domain;
3. A's vehicle domain is a subset of B's vehicle domain;
4. A's temporal domain is a subset of B's temporal domain;
5. A's purpose domain is a subset of B's purpose domain;
6. at least one of conditions 1–5 is strict, or A's registered source vehicle
   key is a descendant of B's source vehicle key while their projected vehicle
   domains are equal.

This is a partial order. It is not a source-order rule.

Rules dominated by another applicable rule shall be removed.

Rules not dominated by another applicable rule are maximal rules.

### 12.5 Maximal-rule decision

- one maximal rule: adopt its effect;
- multiple maximal rules with the same effect: adopt the effect once and preserve all provenance;
- multiple maximal rules with different effects: stop with `ACCESS_SPECIFICITY_CONFLICT`.

The implementation shall not choose the first, last or shortest independent rule.

## 13. Access values and permissions

### 13.1 Permission output

For every governed way/direction/lane/vehicle/scenario tuple, the Resolver shall output one of:

- allowed;
- denied;
- unresolved through a non-resolved record.

The formal permission expectation shall be complete for every governed tuple.

### 13.2 Core access-value semantics

The access-value registry shall at minimum define:

| Access value | Normalized interpretation |
|---|---|
| `yes` | allowed |
| `designated` | allowed, with designation provenance |
| `permissive` | allowed, with revocable-permission provenance |
| `no` | denied |
| `destination` | allowed only when destination-purpose context is true |
| `delivery` | allowed only when delivery-purpose context is true |
| `customers` | allowed only when customer-purpose context is true |
| `private` | allowed only with registered private authorization |
| `permit` | allowed only with the required registered permit |
| `agricultural` | allowed only for the registered agricultural vehicle/purpose context |
| `forestry` | allowed only for the registered forestry vehicle/purpose context |
| `unknown` | valid but unsupported |
| `variable` | valid but unsupported unless a registered evaluator exists |

The registry may support additional values, but unregistered values shall not be guessed.

If required purpose or authorization context is absent, the record shall stop with `ACCESS_CONTEXT_MISSING`.

A known negative context, such as the managed vehicle explicitly having no permit, shall evaluate to denied rather than missing.

### 13.3 Typemap permissions

Typemap permissions are provisional topology candidates.

They are not a formal upper bound and are not formal permission authority.

The final permission set shall equal the Resolver expectation and remain within the governed vClass universe.

The current v16 typemap-baseline intersection shall not be used as the v17 final authority.

## 14. Conditional grammar and evaluation

### 14.1 Supported v17 structure

A supported conditional value shall have one or more clauses:

```text
value @ (condition)
```

Multiple clauses in the same source value may be separated by semicolons.

Within the same OSM conditional tag, when multiple clauses match, the last matching clause shall become the normalized source result, consistent with OSM conditional-tag semantics.

After this intra-tag normalization, independent rules shall be combined through Section 12 rather than source order.

### 14.2 Supported condition categories

The v17 grammar may support only registered forms of:

- weekday sets and ranges;
- clock-time intervals;
- calendar-date intervals;
- registered public holidays;
- Boolean `AND`;
- Boolean `OR`;
- parentheses;
- governed vehicle classes;
- registered mass and dimension predicates;
- registered trip purposes;
- registered permit and authorization predicates.

The exact grammar and token registry shall be versioned and hash-bound.

School holidays, sunrise/sunset, weather, event-dependent access, free text and any unregistered token are unsupported unless explicitly added.

### 14.3 Scenario context

The scenario context shall include all fields required by a potentially applicable registered rule, including:

- start and end timestamp;
- timezone;
- simulation interval duration;
- holiday-calendar version;
- governed vehicle class;
- vehicle mass and dimensions;
- trip purpose;
- authorization and permit assignments.

A required field that is absent shall not be treated as false.

It shall stop with `ACCESS_CONTEXT_MISSING`.

### 14.4 Within-interval changes

The evaluator shall identify all registered conditional boundaries within the simulation interval.

If the effective permission differs between subintervals, the pipeline shall:

1. use an approved scenario-splitting transformation; or
2. stop with `ACCESS_WITHIN_INTERVAL_CHANGE`.

It shall not adopt the value at only the start or end of the interval and shall not average permissions.

### 14.5 Unsupported syntax

Unsupported conditional syntax shall stop with:

```text
ACCESS_CONDITIONAL_SYNTAX_UNSUPPORTED
```

The static rule shall not be used as if the unsupported conditional tag did not exist.

## 15. Evidence-based resolution

### 15.1 No generic imputation fallback

v17 shall not contain a generic mode, median, nearest-neighbour or equal-split fallback for formal values.

A missing value remains unresolved unless an approved rule or evidence method applies.

### 15.2 Evidence method registry

An evidence-based method shall be enabled only through a versioned method record containing:

```yaml
method_id:
target_attribute:
eligible_population:
required_inputs:
donor_eligibility:
estimator_or_model:
validation_dataset:
validation_metrics:
acceptance_thresholds:
uncertainty_output:
provenance_fields:
approver:
approval_date:
implementation_hash:
fixture_hash:
oracle_hash:
```

If no approved method is registered, `evidence_derived` and `derived_validated_model` shall not be emitted.

### 15.3 Minimum donor eligibility

A donor used for formal evidence resolution shall:

- belong to the registered eligible population;
- have formally resolved direction;
- have formally resolved directional lanes where relevant;
- have formally resolved speed where relevant;
- have no unsupported conditional tag relevant to the target;
- have formally resolved permissions where relevant;
- contain no structural assumption;
- contain no `model_assumed` value;
- have traceable source and configuration hashes.

An ineligible donor shall stop the method with `EVIDENCE_DONOR_INELIGIBLE`.

### 15.4 Manual evidence

Human review may register evidence, but shall not directly edit a production output.

The evidence shall be stored in a separate, versioned evidence record with:

- source;
- reviewer;
- decision;
- reason;
- affected records;
- date;
- hash.

The Resolver shall consume the registered evidence and regenerate the complete artifact.

## 16. Exclusions and population accounting

### 16.1 Exclusion is not a resolution status

`out_of_scope` shall not be added to `resolution_status`.

A record excluded from the governed population shall appear in a separate exclusion manifest.

### 16.2 Exclusion manifest

Each exclusion entry shall contain:

```yaml
source_way_id:
directed_segment_id:
lane_position:
reason:
exclusion_rule_id:
approver:
approval_date:
evidence_sha256:
population_version:
```

An unregistered exclusion rule shall stop with `EXCLUSION_RULE_UNREGISTERED`.

### 16.3 Population equation

Every run shall report:

```text
input population = governed population + excluded population
```

Counts shall be reported separately for:

- source Ways;
- Directed Segments;
- directional lane tuples;
- governed vehicle-permission tuples;
- attribute records.

A population-definition change requires a new population or configuration version.

The accepted v16 population shall not be retroactively changed.

### 16.4 Materialization omission

A Directed Segment whose formally resolved permission set is empty for all lanes may be omitted from SUMO materialization only as a recorded `materialization_omission`.

This is not a population exclusion.

The omission record shall contain:

```yaml
source_way_id:
directed_segment_id:
resolver_tuple_ids:
reason_code:
expected_permission_set:
omitted_edge_id:
affected_connection_ids:
configuration_hash:
permission_expectation_hash:
materializer_output_hash:
```

The original Resolver tuples remain in permission-completeness denominators.

An empty resolved permission set shall be distinguished from an unresolved permission.

## 17. Provenance, canonicalization and manifests

### 17.1 Provenance

Each effective value shall be traceable to one or more of:

- source observations;
- normalization rules;
- derivation rules;
- evidence records;
- validated models;
- structural assumptions.

Provenance shall identify the processing activity and the software/configuration version that produced the record.

### 17.2 Canonical JSON

JSON artifacts used for identity or acceptance hashes shall be canonicalized using RFC 8785 JCS before SHA-256 calculation.

Duplicate JSON object keys shall be rejected.

Hash-bearing fields shall not be included in the bytes from which their own hash is calculated unless a separate envelope format is defined.

### 17.3 Environment/build manifest

Every registered run shall record at least:

- source commit;
- dirty-tree status;
- container image and digest;
- operating platform;
- SUMO version;
- Python and relevant library versions;
- exact command;
- arguments;
- configuration hash;
- Schema hash;
- registry hashes;
- input hashes;
- start and end timestamps;
- exit code;
- stdout/stderr log hashes;
- output hashes;
- random seeds, including an explicit statement when no random process is used.

### 17.4 Determinism

Two clean runs with the same registered inputs, environment and command shall produce identical canonical artifact hashes.

A mismatch shall block acceptance and require a recorded investigation.

## 18. Validation and acceptance

### 18.1 Validation layers

The pipeline shall distinguish:

1. JSON Schema validation;
2. semantic and cross-field validation;
3. fixture/oracle validation;
4. full-population accounting;
5. Attribute Resolution Acceptance;
6. SUMO Network Integration Acceptance;
7. software test-suite execution;
8. calibration;
9. independent traffic-model validation.

Passing one layer shall not imply passing another.

### 18.2 Attribute Resolution Acceptance scope

Attribute Resolution Acceptance applies only to the formal Resolver artifact.

It does not approve:

- plain XML;
- `net.xml`;
- connections;
- TLS;
- calibration;
- traffic-model validity;
- downstream experiments.

### 18.3 Required acceptance conditions

The gate shall pass only when all of the following are true:

```text
complete = true
blockers = []
review_required = 0
stop_unresolved = 0
model_assumed = 0
```

In addition:

- all governed records are accounted for;
- no record has `unresolved`, `conflict`, `invalid` or `valid_but_unsupported`;
- no unregistered state, origin, rule, value, stop code or assumption exists;
- no v17 output contains legacy `value_state`;
- no formal record contains `model_assumed` or an assumption ID;
- input/governed/excluded population equations match;
- permission completeness covers every governed way/direction/lane/vehicle tuple;
- JSON Schema validation passes;
- semantic validation passes;
- cross-field invariants pass;
- independent fixture/oracle comparison passes;
- classification rule coverage has zero unmatched and zero overlapping cases;
- the value-free classification projection hash is unchanged by resolution;
- two clean full runs have identical output hashes;
- required source, configuration, Schema, registry, fixture, oracle, exclusion, output and validation hashes are recorded;
- structural and formal artifacts are stored separately;
- direct edits to source OSM or generated `net.xml` are absent.

### 18.4 Definition of `complete`

`complete=true` means:

- every expected governed record exists exactly once;
- every governed record is resolved;
- every resolved value is eligible for the active profile;
- every required provenance link is present;
- every denominator and manifest count agrees.

Execution over every input is not sufficient if non-resolved records remain.

### 18.5 Gate result

The acceptance artifact shall use:

| Result | Meaning |
|---|---|
| `passed` | Gate was executed and all conditions passed. |
| `failed` | Gate was executed and at least one condition failed. |
| `not_run` | Required implementation, artifact or evidence was absent, so the gate was not executed. |

Missing evidence shall not be reported as `passed`.

### 18.6 Acceptance artifact

The gate shall emit:

```yaml
gate_name: attribute_resolution_acceptance
policy_id:
configuration_id:
population_version:
configuration_hash:
schema_hash:
registry_hashes:
input_hashes:
formal_artifact_hash:
oracle_hash:
exclusion_manifest_hash:
classification_projection_hash:
population_counts:
validation_results:
blocker_counts:
review_required_count:
model_assumed_count:
determinism_check:
result:
accepted_by:
accepted_at:
```

## 19. Independent fixtures and oracles

### 19.1 Independence

Production code shall not generate expected oracle values.

Fixture authors and reviewers shall record:

- author role;
- source specification hash;
- oracle authored before production implementation where applicable;
- production code not used to derive expected values;
- independent reviewer;
- review timestamp.

### 19.2 Required case families

Fixtures shall include at least:

- ordinary bidirectional road with missing `oneway`;
- `oneway=yes`;
- `oneway=no`;
- `oneway=-1`;
- implicit one-way rule;
- explicit directional lanes;
- total/directional lane consistency;
- structural even split;
- formal missing directional allocation;
- odd and single-lane bidirectional cases;
- directionally asymmetric speed;
- symbolic and missing speed rules;
- general access;
- vehicle-specific access;
- directional access;
- lane-specific access;
- conditional access;
- same-result maximal rules;
- conflicting maximal rules;
- missing scenario context;
- unsupported conditional syntax;
- within-interval permission change;
- relation mapping unique/missing/ambiguous;
- empty resolved permission set;
- exclusion accounting;
- legacy state migration;
- unregistered state/rule/stop-code rejection.

### 19.3 Boundary and metamorphic tests

The fixture suite shall include:

- minimum and maximum valid numeric values;
- empty and null distinctions;
- source-order changes between independent rules;
- repeated runs;
- source Way immutability;
- forward/backward symmetry where applicable;
- classification projection invariance;
- record-order invariance;
- JSON canonicalization invariance.

Changing independent record order shall not change the result.

Changing clause order within a single conditional tag may change the result only where OSM last-match semantics apply.

## 20. Stop-code registry

The v17 registry shall include at least:

```text
LEGACY_STATE_MAPPING_UNSUPPORTED
ONEWAY_VALUE_INVALID
ONEWAY_VALUE_UNSUPPORTED
ONEWAY_RULE_NOT_REGISTERED
DIRECTED_SEGMENT_LINEAGE_INVALID
RELATION_DIRECTED_MAPPING_MISSING
RELATION_DIRECTED_MAPPING_AMBIGUOUS
LANE_COUNT_INVALID
LANE_COUNT_CONFLICT
LANE_DIRECTIONAL_ALLOCATION_MISSING
LANE_VECTOR_LENGTH_MISMATCH
SPEED_VALUE_INVALID
SPEED_VALUE_UNSUPPORTED
SPEED_RULE_NOT_REGISTERED
SPEED_CONDITIONAL_CONTEXT_MISSING
SPEED_WITHIN_INTERVAL_CHANGE
ACCESS_VALUE_INVALID
ACCESS_VALUE_UNSUPPORTED
ACCESS_VEHICLE_HIERARCHY_MISSING
ACCESS_CONDITIONAL_SYNTAX_UNSUPPORTED
ACCESS_CONTEXT_MISSING
ACCESS_WITHIN_INTERVAL_CHANGE
ACCESS_SPECIFICITY_CONFLICT
ACCESS_PERMISSION_UNRESOLVED
EVIDENCE_METHOD_NOT_APPROVED
EVIDENCE_DONOR_INELIGIBLE
EXCLUSION_RULE_UNREGISTERED
UNREGISTERED_RULE
UNREGISTERED_STATE
UNREGISTERED_STOP_CODE
```

Each code shall define:

- trigger condition;
- applicable attributes;
- resolution status;
- whether human review is required;
- permitted remediation;
- fixture ID.

## 21. Required implementation order

The following dependency order is normative for reaching v17 acceptance:

```text
Phase 0  freeze v16 history and evidence
Phase 1  approve this specification, v17 configuration, Schema and registries
Phase 2  freeze independent fixtures and production-independent oracles
Phase 3  migrate to resolution_status / value_origin
Phase 4  integrate Directed Segments into the production pipeline
Phase 5  implement directional lane resolution
Phase 6  implement static access normalization and target scopes
Phase 7  implement conditional parsing and scenario-context evaluation
Phase 8  integrate scope-and-axis dominance and final permission resolution
Phase 9  implement speed resolution and the Japan speed-rule registry
Phase 10 approve and implement any formal evidence-resolution methods
Phase 11 execute Resolver integration tests
Phase 12 execute the v17 full-population structural and formal runs
Phase 13 resolve stop records through registered rules/evidence and rerun
Phase 14 execute Attribute Resolution Acceptance
```

### 21.1 Phase completion conditions

#### Phase 0

- v16 artifacts and hashes are registered;
- v16 outputs are write-protected by workflow policy;
- v17 output paths are separate.

#### Phase 1

- document, configuration, Schema and registries use the same enums and rules;
- no unresolved normative wording remains in the six core areas:
  - state contract;
  - Directed Segments;
  - access scope/specificity;
  - profile boundary;
  - acceptance gate;
  - implementation order.

#### Phase 2

- fixtures cover all registered stop codes;
- independent oracle review is recorded.

#### Phase 3

- v17 writers emit no `value_state`;
- legacy read compatibility passes;
- cross-field invariants pass.

#### Phase 4

- source Way immutability passes;
- `oneway=-1` integrated fixture passes;
- relation mapping fixtures pass.

#### Phase 5

- lane-count and vector consistency pass;
- formal and structural outputs differ only through registered profile rules.

#### Phases 6–8

- lane/direction scope is preserved;
- vehicle ontology is registered;
- conditional grammar is hash-bound;
- access results are independent of independent-record order;
- conflicting maximal rules stop.

#### Phase 9

- all symbolic/default speed values reference a versioned rule;
- directionally asymmetric speeds are preserved.

#### Phase 10

- no evidence-derived value is emitted before method approval;
- donor eligibility and validation evidence are registered.

#### Phase 11

- Schema, semantic, oracle and metamorphic tests pass.

#### Phase 12

- all input records are accounted for;
- structural/formal outputs and manifests are separate;
- full-run hashes are recorded.

#### Phase 13

- new exceptions are added first to decision tables and small fixtures;
- no direct one-off source/output edit is used.

#### Phase 14

- every Section 18 acceptance condition passes.

### 21.2 Permitted parallel development

After Phase 2, the following may proceed on small fixtures in parallel:

- provisional structural plain-XML build;
- exact edge-provenance prototype;
- Permission Materializer implementation;
- pinned SUMO runtime fixture;
- connection and TLS review tooling.

This parallel work shall not:

- approve a real-data formal network;
- bypass Attribute Resolution Acceptance;
- produce publishable travel-time or capacity results;
- transfer calibration from structural to formal networks.

## 22. Transition from v16

The transition shall preserve the following facts:

- v16 remains the current historical state authority until a v17 state configuration is approved;
- v16 classification and resolution execution evidence remains unchanged;
- v16 `value_state` artifacts remain readable;
- v17 canonical output uses `resolution_status` and `value_origin`;
- v16 typemap-baseline permission intersection is superseded for v17;
- v17 final permission authority is the Resolver expectation;
- existing v16 stopped records are not automatically resolved by adopting this specification;
- a new v17 full-population run and acceptance artifact are required.

The following implementation results shall not be inferred from specification completion:

- Permission Materializer implementation;
- Permission Materializer runtime fixture;
- full v17 Resolver integration;
- formal evidence methods;
- accepted formal network;
- calibration;
- independent validation;
- downstream experiment readiness.

## 23. Source references

### OSM semantics

- OpenStreetMap Wiki, `oneway=-1`  
  https://wiki.openstreetmap.org/wiki/Tag%3Aoneway%3D-1

- OpenStreetMap Wiki, Forward and backward  
  https://wiki.openstreetmap.org/wiki/Forward

- OpenStreetMap Wiki, lanes and directional lanes  
  https://wiki.openstreetmap.org/wiki/Key%3Alanes%3Aforward

- OpenStreetMap Wiki, lane-specific tags  
  https://wiki.openstreetmap.org/wiki/Key%3A%2A%3Alanes

- OpenStreetMap Wiki, access tags and transport-mode hierarchy  
  https://wiki.openstreetmap.org/wiki/Access_tags

- OpenStreetMap Wiki, conditional restrictions and conflict evaluation  
  https://wiki.openstreetmap.org/wiki/Conditional_restrictions

### SUMO network generation

- SUMO Documentation, OpenStreetMap import  
  https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html

- SUMO Documentation, PlainXML  
  https://sumo.dlr.de/docs/Networks/PlainXML.html

- SUMO Documentation, netconvert  
  https://sumo.dlr.de/docs/netconvert.html

### Modeling, simulation and validation

- FHWA Traffic Analysis Toolbox Volume III, Error Checking  
  https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter4.htm

- FHWA Traffic Analysis Toolbox Volume III, Model Calibration  
  https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm

- NASA-STD-7009B, Standard for Models and Simulations  
  https://standards.nasa.gov/node/263

- NASA-HDBK-7009B, Implementation Guide  
  https://standards.nasa.gov/standard/nasa/nasa-hdbk-7009

### Provenance, Schema and reproducibility

- W3C PROV-O  
  https://www.w3.org/TR/prov-o/

- JSON Schema, enumerated values  
  https://json-schema.org/understanding-json-schema/reference/enum

- JSON Schema, conditional validation  
  https://json-schema.org/understanding-json-schema/reference/conditionals

- RFC 8785, JSON Canonicalization Scheme  
  https://www.rfc-editor.org/rfc/rfc8785.html

- Workflow Run RO-Crate  
  https://www.researchobject.org/workflow-run-crate/

## 24. Approval checklist

The repository baseline approval record is:

```text
[x] resolution_status enum is accepted
[x] value_origin enum is accepted
[x] legacy mapping rule is accepted
[x] Directed Segment identity is accepted
[x] one-way generation rules are accepted
[x] directional lane rules are accepted
[x] target scope is separated from the four semantic axes
[x] scope-and-axis dominance is accepted
[x] conditional grammar boundary is accepted
[x] structural/formal profile boundary is accepted
[x] evidence-method extension contract is accepted
[x] exclusion and materialization-omission accounting is accepted
[x] Attribute Resolution Acceptance conditions are accepted
[x] implementation order is accepted
[x] configuration, Schema and registries are updated to match
[x] fixture and oracle requirements and the Phase 2 scope are fixed
```
