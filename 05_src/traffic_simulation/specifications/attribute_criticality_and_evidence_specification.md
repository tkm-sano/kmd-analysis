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

## Classification and Resolution Artifacts

Classification decides impact level; resolution decides whether and how a
value may be adopted. They are separate hash-linked artifacts and MUST NOT be
combined into one flat record.

`attribute_criticality_classification.json` MUST contain exactly one record for
every retained `(osm_way_id, attribute)` pair for the selected profile.

| Field | Meaning |
|---|---|
| `osm_way_id` | Stable OSM way identifier from the relation-closed input |
| `attribute` | Exactly `lanes` or `maxspeed` |
| `profile` | Exactly `structural` or `formal` |
| `criticality_level` | Attribute-specific level defined below |
| `criticality_rule_id` | One rule that produced the level |
| `predicate_evidence` | Hash-bound facts used by the rule |
| `source_artifact_sha256` | Hash of the classified relation-closed input |
| `classification_config_sha256` | Hash of the classification policy |

`attribute_resolution_decisions.json` MUST contain exactly one decision for
every classification tuple that is retained for value resolution.

| Field | Meaning |
|---|---|
| `classification_record_id` | Stable reference to the exact classification record |
| `classification_artifact_sha256` | Hash of the complete classification artifact |
| `evidence_required` | Evidence class required before adopting a value |
| `evidence_candidates` | Array of every applicable or rejected candidate considered |
| `selected_evidence_id` | Selected candidate, or empty while stopped |
| `rejected_evidence_ids` | Candidate IDs not selected |
| `conflict_resolution_rule_id` | Registered rule used to resolve a conflict, or empty |
| `resolution_action` | One allowed action defined in this specification |
| `resolution_rule_id` | Rule that resolves the value, or empty while stopped |
| `value_state` | Controlled value-origin or stopping state |
| `adopted_value` | Adopted canonical value, or empty while stopped/excluded |
| `unit` | Attribute-compatible unit, or empty where not applicable |
| `review_status` | `machine_resolved`, `review_required`, `reviewed`, or `stopped` |
| `reviewer` | Required only for a reviewed decision |
| `reviewed_at` | Required only for a reviewed decision |
| `stop_failure_codes` | One or more governed codes when stopped |

Each evidence candidate MUST identify its source, value, unit, direction,
segment, vehicle scope, observation/reference period, licence, source hash and
matching confidence. The policy schema MUST fix the confidence scale,
acceptance threshold and tie behavior before confidence may select evidence.

Unknown fields, duplicate or missing tuples, unknown rule IDs, predicate
contradictions, evidence without a registered source hash and a classification
hash mismatch MUST stop before Resolver execution.

## Predicate Consistency Before Classification

The classifier first validates predicate consistency and only then applies the
ordered first-match rules. It MUST stop rather than silently assign a level
when one way is simultaneously:

- excluded and a calibration or independent-validation segment;
- excluded and an accepted delivery route;
- excluded and required as topology support;
- outside the final subgraph and present in a retained governed route; or
- assigned any other predicate combination prohibited by the versioned
  classification policy.

If a way is completely excluded and is neither topology support nor part of a
retained governed route, its lane and maxspeed records MUST be `L0` and `S0`.
Different lane and maxspeed levels are permitted only where their
attribute-specific predicates differ and the classification records show that
difference.

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
| `LANE-CRIT-001` | governed subgraph decision is `excluded` and the way is not required as topology support | `L0` |
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
| `SPEED-CRIT-001` | governed subgraph decision is `excluded` and no retained route requires the way | `S0` |
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

The classifier may emit only these actions:

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

| Resolution action | Permitted value state | Review status |
|---|---|---|
| `adopt_explicit` | `explicit_osm` | `machine_resolved` or `reviewed` |
| `derive_osm_rule` | `derived_osm_rule` | `machine_resolved` or `reviewed` |
| `adopt_external_evidence` | `authoritative_external` | `machine_resolved` or `reviewed` |
| `apply_governed_rule` | `derived_validated_model` | `machine_resolved` or `reviewed` |
| `apply_structural_placeholder` | `structural_placeholder` | `machine_resolved` or `reviewed` |
| `require_human_review` | any unresolved/stopping state | `review_required` |
| `stop_unresolved` | `missing`, `unresolved`, `conflict`, `valid_but_unsupported`, `conditional`, `directionally_asymmetric`, or `invalid` | `stopped` |
| `exclude` | `excluded` | `machine_resolved` or `reviewed` |

No other action-state-review combination is valid. Human review does not
authorize a new value state: after review, the decision MUST transition to one
of the resolved actions above or remain stopped.

## Profile-specific Required Inputs

| Input | `structural` | `formal` |
|---|---|---|
| complete classification artifact | required | required |
| resolution-decision artifact | required for every retained unresolved tuple | required for every retained unresolved tuple |
| external evidence artifact | required when cited | required when cited |
| structural-placeholder rule | required only when used | prohibited |

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

Classification fixture oracles MUST contain the expected level and rule ID.
Resolution fixture oracles MUST separately contain the expected action, value
state, review status and failure code. Production code MUST NOT generate its
own oracle.

## Current Status

This specification fixes the classification vocabulary, predicate-validation
order and the separation between classification and resolution. The two
schemas, predicate-source artifacts, classifier, resolver integration and
fixtures are not implemented. Therefore the Ota Ward ways remain
`unclassified`, and this document does not change the 46,056-blocker Dry Run
result or authorize a new Resolver run.

For registered real-data execution, classification additionally depends on the
population-acceptance gate in
`02_resolver_specification.md#relation-closure-before-attribute-classification`.
The classifier schema and synthetic fixtures may be developed before that gate
passes, but no production classification artifact may be published against the
v15 population. After the next-version closure is accepted, complete
`(osm_way_id, attribute, profile)` coverage must be generated from the new
input rather than patched onto v15 records.
