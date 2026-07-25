# Attribute Criticality and Evidence Specification

Japanese translation:
[`ja/attribute_criticality_and_evidence_specification_ja.md`](ja/attribute_criticality_and_evidence_specification_ja.md).
Machine-readable configuration and this English specification remain
authoritative if the translations differ.

## Purpose

This specification governs how missing `lanes` and `maxspeed` values are
classified before the Resolver may apply any structural value. It prevents the
45,749 bulk-missing rows observed in the Ota Ward v15 Dry Run from being
treated as one uniformly acceptable class.

Criticality is attribute-specific. It describes the consequence of using an
unsupported value for one attribute in one declared network profile. It is not
a general importance score for an OSM way, and it does not establish that the
road is socially or economically important.

This specification does not authorize values. It defines the classification
contract, evidence precedence, permissible actions and conditions that must be
implemented and fixture-tested before classification may be used.

## Observed-count Provenance

Numbers in this specification are historical v15 observations, not live
configuration constants. Their source is
`03_data/metadata/acquisition/20260723_ota_ward_v15_resolver_dry_run.md`,
which records the run inputs, config ID and SHA-256 values and the output
artifact hashes.

| Observation | Unit and calculation |
|---|---|
| 26,220 governed candidates | distinct retained way IDs after the v15 relation closure |
| 46,056 blockers | audit rows whose governed decision is a stopping state |
| 45,749 bulk missing | blocker rows with a genuinely absent `lanes` or `maxspeed` source value |
| 307 rule/data exceptions | blocker rows not counted as bulk missing; `46,056 - 45,749` |
| 3 omitted bus restrictions | distinct full-input relations with `type=restriction:bus` and governed turn semantics |

These counts MUST be regenerated from the next accepted closure. They MUST NOT
be copied into acceptance logic or treated as expected production totals.

## Governing Principles

1. The classification unit is one `(osm_way_id, attribute, profile)` tuple.
2. `lanes` and `maxspeed` MUST be classified independently.
3. A lower-criticality classification MUST NOT be reused for a higher-impact
   profile.
4. Explicit or authoritative evidence MUST NOT be overwritten by a lower-ranked
   structural rule.
5. A structural placeholder is permitted only in the `structural` profile,
   only for an eligible level, and never for formal research results.
6. Missing evidence, a contradictory predicate or incomplete classification
   coverage is a stopping state.
7. Classification and value resolution are separate decisions. A criticality
   level never supplies the attribute value by itself.
8. A later promotion, such as identifying a calibration or delivery-route
   edge, invalidates the earlier classification and all dependent artifacts.

## Analysis Profiles

| Profile | Permitted use | Criticality consequence |
|---|---|---|
| `structural` | topology, connectivity, permission and visualization checks | an approved placeholder may be considered only where the attribute-specific level permits it; travel-time, capacity and delivery conclusions are prohibited |
| `formal` | calibrated traffic, delivery evaluation and optimization comparison | structural placeholders are prohibited and every retained attribute requires governed evidence or a validated model allowed by the formal specification |

Changing a network from `structural` to `formal` requires reclassification.
The structural classification is not promoted automatically.

## Population and Subgraph Roles

The classification population is the governed candidate-way set in an OSM
input whose relation-closure acceptance gate has passed. The regional PBF and
the pre-closure BBOX extract are not classification populations. A changed
relation-closed input SHA-256 requires a new classification run.

Every governed candidate way, including a way not retained in the final SUMO
network, MUST have exactly one `subgraph_role`:

```text
final
topology_support
excluded
```

Multiple role booleans are prohibited. An `excluded` way remains in the
classification artifact with lane level `L0`, speed level `S0`,
`resolution_action=exclude`, `value_state=excluded`, and
`resolved_value=null`. A `topology_support` way is classified because it can
affect relation, connection or conversion behavior. Its base levels are
`L1/S1` in `structural` and `L2/S2` in `formal`, subject to promotion to
`L3/S3`.

## Tuple, Record and Revision Contract

The tuple is `(osm_way_id, attribute, profile)`. The way ID is a positive
decimal string, attribute is `lanes` or `maxspeed`, and profile is
`structural` or `formal`. One artifact contains one profile and exactly one
active record per tuple, including excluded ways.

The stable record ID is:

```text
acr:<osm_way_id>:<attribute>:<profile>
```

Records are sorted by numeric way ID and then `lanes` before `maxspeed`.
Classification and resolution are separate objects in the same record:

```json
{
  "classification_record_id": "acr:123456789:lanes:formal",
  "osm_way_id": "123456789",
  "attribute": "lanes",
  "profile": "formal",
  "classification": {
    "criticality_level": "L2",
    "selected_rule_id": "LANE-CRIT-006",
    "matched_rule_ids": ["LANE-CRIT-006"]
  },
  "resolution": {
    "resolution_action": "stop_unresolved",
    "resolution_rule_id": null,
    "value_state": "missing",
    "resolved_value": null
  }
}
```

The resolution object also records a structured `evidence_requirement`,
`evidence_candidates`, `selected_evidence_id`, `rejected_evidence_ids`,
`conflict_resolution_rule_id`, units, review provenance and stopping codes as
applicable. `evidence_requirement` separates the required flag, governing rule,
minimum authority and explanation; `L3` and `S3` require it and lower levels
must explicitly record that it is not required. Each candidate identifies source, value, unit, direction, segment,
vehicle scope, period, licence, source hash and matching confidence. Confidence
cannot select evidence until its scale, threshold and tie behavior are fixed
by policy.

The artifact is an immutable run snapshot. A changed decision creates a new
snapshot with the same `classification_record_id`, an incremented
`record_revision`, a new `record_sha256`, the prior
`supersedes_record_sha256`, and a governed `revision_reason_code`. Prior
snapshots are retained; multiple active revisions of one tuple MUST NOT appear
in one snapshot.

### Canonical record hash and ordering

`record_sha256` is the SHA-256 of the UTF-8 RFC 8785 JSON Canonicalization
Scheme representation of the record after removing only `record_sha256`
itself. RFC 8785 controls object-key, whitespace and number serialization;
array order is preserved. Explicit `null` and an omitted field are different,
and every field required by the schema remains present during hashing.

Records are ordered by numeric `osm_way_id`, then `lanes` before `maxspeed`,
then `structural` before `formal`, and finally `record_revision` ascending.
The profile key remains in the ordering contract even though a current
artifact contains one profile.

### Semantic validation

JSON Schema validates the local shape and state machine. The registered
`validate_attribute_classification.py` validator separately collects
cross-record failures with `ACV` codes. It verifies derived record IDs,
artifact/record profile agreement, tuple and evidence-ID uniqueness,
population coverage, both attributes per way, rule selection against
`road_criticality.classification_rule_priority`, evidence references,
completion state, revision history supplied explicitly to the validator,
RFC 8785 hashes, canonical ordering and referenced-file SHA-256 values.
Each record's `source_artifact_sha256` must equal the top-level predicate
artifact hash, and `classification_config_sha256` must equal the top-level
classification-policy hash.

The validator does not search directories to infer revision or evidence
sources. Every non-top-level source must be registered explicitly through the
validator source index, and predecessor snapshots must be supplied as history.
This prevents a same-named but unrelated file from being accepted implicitly.
Its CLI returns all detected errors in one JSON result:

```json
{
  "valid": false,
  "errors": [
    {
      "code": "ACV001",
      "json_pointer": "/records/0/classification_record_id",
      "message": "classification_record_id does not match osm_way_id, attribute, and profile",
      "expected": "acr:123:lanes:formal",
      "actual": "acr:999:maxspeed:structural"
    }
  ]
}
```

## Predicate Artifact

The classifier MUST consume `attribute_classification_predicates.json` and
MUST NOT rediscover predicates directly from OSM, routes, calibration settings
or reviews. The predicate artifact contains exactly one record per population
way, complete population and source hashes, the exclusive `subgraph_role`, and
at least these governed facts:

```text
is_calibration_segment
is_validation_segment
is_major_junction_approach
is_bridge
is_tunnel
is_grade_separated
has_directional_lane_semantics
has_reversible_lane_semantics
has_tidal_flow_semantics
has_turn_lane_semantics
has_bus_or_psv_lane_semantics
has_conflicting_lane_semantics
has_directional_speed_semantics
has_conditional_speed_semantics
has_variable_speed_semantics
has_vehicle_specific_speed_semantics
has_advisory_or_multiple_speed_semantics
is_accepted_delivery_route
is_sensitivity_elevated
```

Every predicate value requires a source artifact type and SHA-256, source
record locator and derivation rule ID. Unsupported evidence-free booleans are
prohibited.

`subgraph_role_evidence` is categorical rather than boolean. It records
`asserted_role` plus the same source provenance, and semantic validation
requires `asserted_role` to equal `subgraph_role`.
`topology_support_reason` is always present: it is a nonempty string only for
`topology_support` and is `null` for `final` and `excluded`.

### Predicate Generator Contract

`generate_attribute_classification_predicates.py` consumes three explicit
inputs: a relation-closed OSM XML file, a
`predicate_source_registry.schema.json`-conforming source registry, and the
pinned `sumo_network.yml` policy. The governed population consists of every
OSM way carrying a `highway` tag plus only those non-highway ways explicitly
registered as `topology_support`. The role registry must cover that population
exactly once.

Bridge, tunnel, grade-separation, lane-semantics and speed-semantics
predicates are derived deterministically from OSM tags. Calibration,
independent-validation, major-junction, accepted-delivery-route and
sensitivity predicates come only from hash-registered external sources.
Both true and false values retain source provenance. A reviewed override may
replace one derived value only when its own source, locator and derivation-rule
ID are registered.

Generation is fail-closed. It stops on an unaccepted population, incomplete
role coverage, an out-of-population external ID, a missing or mismatched source
hash, schema or semantic validation failure, or an existing output path.
Writing is atomic and records are ordered by numeric OSM way ID. Registered
real data additionally requires a population-acceptance artifact and
configuration version 16 or later. The v15 Dry Run is therefore not an
eligible production input. Synthetic fixtures use an explicit
`synthetic_fixture` scope and cannot establish real-data acceptance.

## Predicate Consistency Before Classification

Validation occurs in this order: schema; artifact/source hashes; duplicate way
IDs; complete population coverage; role enum; role contradictions;
calibration/validation exclusivity; structural contradictions;
attribute-specific predicates; then classification rules.

The classifier stops before first-match evaluation when:

- `excluded` is combined with calibration, validation, accepted-route,
  sensitivity-elevated or major-junction status;
- `topology_support` lacks a governed support reason;
- one way is both a calibration and independent-validation segment; or
- one way is both bridge and tunnel without a governed way split or individual
  review.

Bridge/tunnel coexistence is not made unconditionally exclusive in JSON
Schema because a split or reviewed exception can make it valid. The predicate
source registry exposes a hash-linked reviewed override for that adjudication.
Without such an adjudication, the semantic validator stops the case rather
than guessing.

Directional-lane and bus/PSV-lane semantics may coexist. Different lane and
maxspeed levels are permitted where their attribute-specific predicates differ.

## Lane Criticality

Lane criticality concerns capacity, directional allocation, lane-changing,
junction connections and flow. It does not describe the geometric importance
of a road.

| Level | Machine meaning | Permitted resolution |
|---|---|---|
| `L0` | The way is excluded by the governed final subgraph decision and is not a topology-support element that requires materialization | Record `excluded`; no lane value is created |
| `L1` | The selected profile is `structural`, no `L3` predicate applies, and the value is used only for the allowed structural checks | An approved structural rule may be applied with provenance and sensitivity status |
| `L2` | The lane value participates in formal capacity, flow, connection or delivery evaluation, but no `L3` predicate applies | Explicit OSM, public evidence, reviewed evidence or an allowed validated model is required |
| `L3` | The way is a calibration/validation segment, a reviewed major junction approach, has complex directional/lane semantics, or is promoted by an accepted delivery-route or sensitivity analysis | Automatic placeholder prohibited; attribute-specific evidence and any required human review are mandatory |

### Lane classification order

After predicate consistency passes, the first matching rule in this order
determines the level:

| Rule ID | Predicate | Level |
|---|---|---|
| `LANE-CRIT-001` | `subgraph_role=excluded` | `L0` |
| `LANE-CRIT-002` | the way is a calibration or independent-validation segment | `L3` |
| `LANE-CRIT-003` | the way is a reviewed major-junction approach, bridge, tunnel or grade-separated structure whose lane count affects a governed connection | `L3` |
| `LANE-CRIT-004` | directional, reversible, tidal-flow, turn-lane, bus-lane, PSV-lane or conflicting lane tags require interpretation | `L3` |
| `LANE-CRIT-005` | an accepted delivery route or registered sensitivity result promotes the way | `L3` |
| `LANE-CRIT-006` | profile is `formal` | `L2` |
| `LANE-CRIT-007` | profile is `structural` and none of the rules above applies | `L1` |

Predicates such as `major junction approach` and `topology support` require
separate governed artifacts; a name or road class alone MUST NOT silently set
them. Post-build or route-based promotion invalidates the earlier
classification before formal use.

## Maxspeed Criticality

Maxspeed criticality concerns free-flow travel time, route choice, arrival
time, delivery feasibility and energy calculation. It does not treat observed
traffic speed as a legal speed limit.

| Level | Machine meaning | Permitted resolution |
|---|---|---|
| `S0` | The way is excluded by the governed final subgraph decision and is not required for a retained route | Record `excluded`; no speed value is created |
| `S1` | The selected profile is `structural`, speed is not used for a reported travel-time, capacity, energy or delivery result, and no `S3` predicate applies | An approved structural rule may be applied and labelled non-formal |
| `S2` | Speed participates in formal routing, travel-time, energy or delivery evaluation, but no `S3` predicate applies | Legal/administrative evidence, explicit supported OSM evidence or an allowed validated model is required |
| `S3` | The way is a calibration/validation segment, contains conditional/directional/variable speed semantics, or is promoted by an accepted route or sensitivity analysis | Automatic placeholder prohibited; time-, direction- and vehicle-compatible evidence is mandatory |

### Maxspeed classification order

| Rule ID | Predicate | Level |
|---|---|---|
| `SPEED-CRIT-001` | `subgraph_role=excluded` | `S0` |
| `SPEED-CRIT-002` | the way is a calibration or independent-validation segment | `S3` |
| `SPEED-CRIT-003` | directional, conditional, variable, vehicle-specific, advisory or multiple speed expressions require interpretation | `S3` |
| `SPEED-CRIT-004` | an accepted delivery route or registered sensitivity result promotes the way | `S3` |
| `SPEED-CRIT-005` | profile is `formal` | `S2` |
| `SPEED-CRIT-006` | profile is `structural` and none of the rules above applies | `S1` |

JARTIC observed travel speed is calibration or validation evidence and MUST NOT
be converted into `maxspeed`.

## Evidence Hierarchy

Evidence is evaluated for applicability before precedence. An evidence record
that refers to another direction, date, vehicle class or segment cannot compete
with an applicable record.

### Lanes

1. consistent explicit direction-specific OSM lane tags;
2. consistent explicit OSM total lanes where directional allocation is not
   required;
3. matched public road-traffic-census lane fields with compatible direction and
   segment definitions;
4. matched road-ledger evidence;
5. scoped and reviewed authoritative imagery;
6. a preregistered, validated derivation model allowed by the selected profile;
7. an approved structural placeholder for `L1` only; and
8. unresolved.

### Maxspeed

1. applicable legal or administrative traffic-regulation evidence with date,
   direction and vehicle scope;
2. supported explicit OSM speed tags whose reference date and semantics are
   compatible;
3. reviewed public-authority evidence for the same segment and direction;
4. a dated legal derivation whose road-state assumptions are verified;
5. a preregistered, validated derivation model allowed by the selected profile;
6. an approved structural placeholder for `S1` only; and
7. unresolved.

The numbered lists are not unconditional overwrite rules. Conflicts are
resolved by legal authority, reference date, segment and direction match,
attribute definition, licence compatibility and match confidence. An
unresolved conflict stops.

## Resolution Actions and States

The Resolver may emit only these resolution actions:

| Action | Meaning |
|---|---|
| `adopt_explicit` | Use a supported explicit source value |
| `derive_osm_rule` | Apply a deterministic OSM semantic rule |
| `adopt_external_evidence` | Use a hash-registered, applicable external value |
| `apply_governed_rule` | Apply a preregistered non-placeholder derivation |
| `apply_structural_placeholder` | Apply only for `L1` or `S1` in the structural profile |
| `require_human_review` | Stop until the specified evidence is reviewed |
| `stop_unresolved` | Stop because no admissible value is available |
| `exclude` | Exclude under a separately governed subgraph decision |

The corresponding value states are:

```text
explicit_osm
derived_osm_rule
authoritative_external
derived_validated_model
structural_placeholder
missing
unresolved
conflict
valid_but_unsupported
conditional
directionally_asymmetric
invalid
excluded
```

`resolved` by itself is not a valid state because it does not identify value
origin.

The permitted combinations are:

| Resolution action | Permitted value state | `resolved_value` | Review status |
|---|---|---|---|
| `adopt_explicit` | `explicit_osm` | required | `machine_classified` or `reviewed` |
| `derive_osm_rule` | `derived_osm_rule` | required | `machine_classified` or `reviewed` |
| `adopt_external_evidence` | `authoritative_external` | required | `reviewed` |
| `apply_governed_rule` | `derived_validated_model` | required | `machine_classified` or `reviewed` |
| `apply_structural_placeholder` | `structural_placeholder` | required | `machine_classified` or `reviewed` |
| `require_human_review` | `missing`, `conflict`, `conditional`, `valid_but_unsupported`, or `directionally_asymmetric` | null | `review_required` |
| `stop_unresolved` | `missing`, `unresolved`, `conflict`, `valid_but_unsupported`, `conditional`, `directionally_asymmetric`, or `invalid` | null | `stopped` |
| `exclude` | `excluded` | null | `machine_classified` |

`invalidated` is not a current resolution status. Supersession is represented
only by revision metadata and the immutable prior snapshot. `L0/S0` permit
only `exclude`; `L1/S1` permit all actions; `L2/S2` and `L3/S3` prohibit
structural placeholders. Every adopted `L3/S3` decision requires `reviewed`.
No other action-state-review-value combination is valid.

## Component Responsibilities

The processing boundary is:

```text
Predicate Generator
    -> produces governed facts required for classification
Classifier
    -> determines criticality_level, selected_rule_id and matched_rule_ids
Resolver
    -> determines resolution action, value state, adopted value, evidence,
       conflict outcome, review state and stop codes
Semantic Validator
    -> validates the combined immutable artifact and its source hashes
```

The Classifier MUST NOT select or impute an attribute value and MUST NOT emit a
resolution action. The Resolver consumes the Classifier result together with
explicit OSM values, registered external evidence, permitted validated models
and structural-placeholder rules. Classification and resolution may later
share one executable entry point, but their object contracts and decision
responsibilities remain separate.

## Profile-specific Required Artifacts

| Artifact | Processing role | `structural` | `formal` |
|---|---|---|---|
| complete predicate artifact | Classifier input | required | required |
| classification result | Classifier output and Resolver input | required | required |
| external evidence artifact | Resolver input | required when cited | required when cited |
| structural-placeholder rule | Resolver input | required only when used | prohibited |
| combined classification-resolution artifact | Resolver output and Semantic Validator target | required | required |

## Resolution Order

Resolution evaluates, in order: excluded role; applicable explicit OSM value;
deterministic OSM semantic rule; applicable reviewed external evidence;
permitted validated model; eligible `L1/S1` structural placeholder; human
review; then governed unresolved stop. Criticality never supplies a value by
itself.

## Structural Placeholder Gate

A structural placeholder may be considered only if all conditions hold:

1. the profile is `structural`;
2. the tuple is classified `L1` or `S1`;
3. no higher-ranked applicable evidence exists;
4. no conflict, conditional expression, unsupported expression or directional
   ambiguity exists;
5. the attribute-specific donor population, source hash, grouping key,
   exclusions, sample unit, direction treatment, canonicalization, minimum
   sample size, distribution, selected value, mode share and tie rule satisfy
   `sumo_network.yml`;
6. the adopted value and rule ID are written to the audit;
7. the output remains prohibited from formal research use; and
8. sensitivity status is recorded.

Failure of any condition produces `stop_unresolved`. A mode derived from many
roads is not evidence that the value is correct for a particular road.

## Failure Codes

Criticality and evidence validation uses one stable code per requirement:

| Requirement | Failure code | Test | Detection |
|---|---|---|---|
| `AC-REQ-001` | `AC001` | `AC-TST-001` | retained tuple is missing |
| `AC-REQ-002` | `AC002` | `AC-TST-002` | tuple is duplicated |
| `AC-REQ-003` | `AC003` | `AC-TST-003` | rule ID is unknown |
| `AC-REQ-004` | `AC004` | `AC-TST-004` | predicate combination is contradictory |
| `AC-REQ-005` | `AC005` | `AC-TST-005` | evidence is not applicable to the tuple |
| `AC-REQ-006` | `AC006` | `AC-TST-006` | evidence conflict is unresolved |
| `AC-REQ-007` | `AC007` | `AC-TST-007` | required review is incomplete |
| `AC-REQ-008` | `AC008` | `AC-TST-008` | structural-placeholder gate fails |
| `AC-REQ-009` | `AC009` | `AC-TST-009` | source, policy or classification hash mismatches |
| `AC-REQ-010` | `AC010` | `AC-TST-010` | action, value state and review status combination is invalid |

Every failure code also requires the negative fixture `<code>-NEG-001`.

## Fixture Contract

Before production classification, independent fixtures MUST cover:

- every lane and speed level;
- precedence and conflict between two evidence sources;
- complete and duplicate tuple coverage;
- structural-to-formal reclassification;
- post-critical promotion and dependent-artifact invalidation;
- a permitted and a prohibited structural placeholder;
- unsupported conditional and directional expressions;
- exclusion versus topology-support retention; and
- deterministic repeated classification.

Fixture oracles MUST keep expected classification and resolution objects
separate within the expected tuple record. They contain the selected and
matched rule IDs, level, action, value state, resolved value, review status and
failure code. Production code MUST NOT generate its own oracle.

`inputs.json` is a complete execution-input catalogue, not a case index. Every
case identifies its target tuple even when validation stops before record
emission, and records OSM attributes, predicates, evidence candidates, profile
and revision state. Each oracle case declares machine-readable assertions and
a record-emission policy. Manifest coverage links each coverage ID to assertion
IDs; level and scenario indexes are derived rather than manually maintained.

Negative fixture IDs retain the failure code form `<code>-NEG-001`. Positive,
boundary and repeat IDs use `AC-POS`, `AC-BND` and `AC-REP` namespaces because
they are not witnesses for one failure code. These are two governed namespaces,
not inconsistent spellings of one namespace.

A `repeat` fixture records baseline and repeated output hashes, byte or
canonical-content comparison mode, and explicit JSON Pointers excluded from a
canonical comparison. The runner removes only those pointers and then compares
RFC 8785 content. Non-repeat fixtures carry an explicit `null`
`repeat_assertion`.

`review.json` stores structured check results, evidence references, reviewer
identity and independence attestations, observed hashes and blocking findings.
`acceptance_allowed` is derived: it is true if and only if collection status is
`independently_accepted`, every required check passed or is not applicable, and
no unresolved blocking finding remains.

An oracle is authored in a separate fixture-authoring step and reviewed by a
person other than the production-output generator author where practicable.
The test runner verifies the oracle file hash and specification hash. Process
independence cannot be proven from JSON content alone, so the author and
review evidence must be retained in the fixture review record.

## Current Status

This specification fixes the population, tuple identity, predicate contract,
classification order and the object boundary between classification and
resolution. The predicate, predicate-source-registry, combined
attribute-classification and fixture schemas are implemented and registered in
`sumo_network.yml`. The predicate generator, its fail-closed synthetic tests,
and standalone source-registry expansion in the semantic validator are
implemented. The Classifier and Resolver stages are not implemented. The
cross-record semantic validator and independent production fixture collection
are implemented. The fixture collection was
authored before the classifier and is not generated by production code;
independent human acceptance and pinned Classifier-Resolver execution remain
pending.
These artifacts have not been applied to a next-version accepted real-data
population. Therefore the Ota Ward ways remain
`unclassified`, and this document does not change the 46,056-blocker Dry Run
result or authorize a new Resolver run.

For registered real-data execution, classification additionally depends on the
population-acceptance gate in
`02_resolver_specification.md#relation-closure-before-attribute-classification`.
Fixture review and classifier development may proceed before that gate passes,
but no production classification artifact may be published against the v15
population. After the next-version closure is accepted, complete
`(osm_way_id, attribute, profile)` coverage must be generated from the new
input rather than patched onto v15 records.

## Current Implementation Order

1. Verify and commit the current four schemas, Predicate Generator, Semantic
   Validator, RFC 8785 hashing, fixture collection, tests and specifications.
2. Complete independent human review of the existing fixture collection,
   resolve every blocking finding, pin the reviewed hashes and derive
   `acceptance_allowed=true`.
3. Re-run the implemented Predicate Generator against the pinned synthetic
   fixture and retain deterministic success and fail-closed evidence.
4. Implement the Classifier with responsibility limited to
   `criticality_level`, `selected_rule_id` and `matched_rule_ids`.
5. Implement the Resolver separately, or as an explicitly separated stage in
   one executable, to determine values, evidence selection, conflicts, review
   state and stopping outcomes.
6. Execute the Classifier and Resolver against positive, negative, boundary,
   repeat, revision, evidence-conflict and placeholder fixtures. Production
   output MUST NOT be used to rewrite the independent oracle.
7. Accept a next-version relation closure containing the three known
   `type=restriction:bus` relations, complete references, recounted population
   and new input hashes. The v15 population remains ineligible.
8. Generate separate structural and formal artifacts for the accepted
   population, retain stopped tuples as stop records, validate them
   semantically and publish atomically.
