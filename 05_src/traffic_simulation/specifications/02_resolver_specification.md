# Resolver Specification

Japanese translation:
[`ja/02_resolver_specification_ja.md`](ja/02_resolver_specification_ja.md).
Machine-readable configuration and this English specification remain
authoritative if the translations differ.

## Scope

The Resolver is the only component that adopts final OSM `oneway`, lane count,
speed and access values. Lane and maxspeed criticality, evidence applicability,
evidence precedence and the structural-placeholder gate are governed by
`attribute_criticality_and_evidence_specification.md`. `oneway`, access,
permission, the common evidence-registration format and source provenance are
governed by `network_attribute_governance.md`. This document defines the
Resolver execution boundary and consumes decisions made under those two
authorities; it does not redefine their precedence rules.

Relation closure is an upstream `prepare` responsibility. It extracts the PBF
population, recursively supplies governed relation members, detects cycles and
publishes the hash-registered OSM XML and closure manifest. The Resolver
validates and consumes those artifacts, records relation-scope accounting and
stops when their contract is incomplete; it does not perform PBF extraction or
closure publication itself. Closure requirements remain here as normative
Resolver input preconditions until a dedicated closure specification is
introduced.

## Inputs and Outputs

Inputs MUST be repository-relative, hash-registered OSM XML, versioned config
and a governed typemap. A complete classification artifact is mandatory for
both profiles. A resolution-decision artifact is mandatory whenever a retained
tuple is not resolved directly from supported OSM semantics. External evidence
is mandatory when a resolution decision cites it. A structural-placeholder
rule is mandatory only when the structural profile requests a placeholder and
is prohibited in the formal profile.

Successful output consists of:

- `normalized.osm.xml`
- `permission_expectations.json` conforming to `permission_expectations.schema.json`
- road-attribute audit CSV
- imputation summary JSON
An ordinary governed stop retains the audit, imputation summary, a
`complete=false` permission artifact and `failure_report.json`, but does not
publish `normalized.osm.xml`. An input, configuration, schema or publication
failure that occurs before a coherent result set is available publishes only
the failure report. `profile=formal` restrictions on unresolved states apply
to successful `complete=true` artifacts, not to governed failure artifacts.
The CLI returns zero on success, two on a classified Resolver failure and
three if even the failure report cannot be published.

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| RS-REQ-001 | The OSM root MUST be `osm`; retained ways MUST have unique nonempty IDs and unique tag keys. | RS001 | RS-TST-001 |
| RS-REQ-002 | Only the explicit typemap whitelist MAY be retained; every excluded highway way MUST be counted. | RS002 | RS-TST-002 |
| RS-REQ-003 | Every retained way MUST resolve `oneway`, directional lane counts, `maxspeed` and permissions before successful output. | RS003 | RS-TST-003 |
| RS-REQ-004 | `missing`, `valid_but_unsupported`, `conditional`, `directionally_asymmetric`, `conflict` and `invalid` MUST remain distinct states. | RS004 | RS-TST-004 |
| RS-REQ-005 | Structural imputation MAY apply only to a true missing tuple classified `L1` or `S1`, with `resolution_action=apply_structural_placeholder`, after every placeholder gate passes and a preregistered attribute-specific unique-mode rule determines one value. | RS005 | RS-TST-005 |
| RS-REQ-006 | A successful `profile=formal`, `complete=true` artifact MUST contain no structural placeholder or unresolved stopping state. | RS006 | RS-TST-006 |
| RS-REQ-007 | `oneway=-1` MUST stop until a complete direction-dependent transformation is implemented; no partial reversal is permitted. | RS007 | RS-TST-007 |
| RS-REQ-008 | Lane access values MUST be read left-to-right as viewed in their respective travel direction for both forward and backward tags. | RS008 | RS-TST-008 |
| RS-REQ-009 | Resolver lane position zero MUST mean the leftmost lane in that travel direction. | RS009 | RS-TST-009 |
| RS-REQ-010 | Unsupported access keys/values, unsuffixed bidirectional lane access and lane-value count mismatch MUST stop. | RS010 | RS-TST-010 |
| RS-REQ-011 | Expected permissions MUST equal the resolved OSM permission intersected with the selected typemap baseline and governed vClasses. | RS011 | RS-TST-011 |
| RS-REQ-012 | The expectation artifact MUST contain complete type, direction, lane-position, rule and hash provenance; the v13 map-only shape is not a valid v15 input. | RS012 | RS-TST-012 |
| RS-REQ-013 | Output writes MUST be atomic, distinct from inputs and non-overwriting unless an explicit governed development override is supplied. | RS013 | RS-TST-013 |
| RS-REQ-014 | Closure and Resolver artifacts MUST classify relation scope by source type, retain governed vehicle-specific restrictions, count discarded relations and supplemented elements, and stop on an unclassified relation type that may affect governed traffic. | RS014 | RS-TST-014 |

This one-to-one requirement/failure/test mapping is the next-version contract.
The executed v15 Dry Run and its failure artifacts are immutable historical
evidence and retain their original codes. Resolver implementation, schemas and
fixtures MUST migrate together before another production run.

## Directional Lane Allocation

`formal` requires explicit, consistent `lanes:forward` and
`lanes:backward` for every bidirectional road. It never infers an equal split
from `lanes`. `structural` may split an even total equally only through
`resolution_action=apply_structural_placeholder` and
`value_state=structural_placeholder`; the audit records the registered
directional-allocation rule ID. `approved_assumption` is not used as a
Resolver action or value state. A single/odd total without explicit allocation
and every `lanes:both_ways` case stop with `RS008`.

## Imputation Donors

Donor eligibility is attribute-specific.

- A lane donor MUST have a resolvable direction, a consistent explicit lane
  value for the sampled unit, no lane-related conditional or conflicting tag,
  no `oneway=-1`, and resolvable permissions under the structural profile. A
  missing or unsupported maxspeed does not by itself disqualify a lane donor.
- A maxspeed donor MUST have a canonical numeric explicit speed for the sampled
  direction, no speed-related conditional, directional, variable or
  conflicting expression, no `oneway=-1`, and resolvable permissions. A
  missing or unsupported lane count does not by itself disqualify a maxspeed
  donor.

Both rules use the grouping keys, source-population hash, exclusion rules,
minimum sample size, minimum mode share, tie policy, sample unit and
canonicalization registered in `sumo_network.yml`. The target tuple is not a
donor because it is missing the sampled attribute. A missing grouping value,
an insufficient group or a tied qualifying mode stops without falling back to
an adjacent road class. Decimal-equivalent speeds such as `40` and `40.0`
share the canonical value `40`. A way that later stops for a donor-eligibility
condition is excluded from the affected attribute's donor population.

Criticality is classified per `(osm_way_id, attribute, profile)`, not once per
way. Classification and resolution are separate, hash-linked artifacts. The
governing vocabulary, evidence precedence, artifact fields and
structural-placeholder gate are defined in
`attribute_criticality_and_evidence_specification.md`. Until its schema,
predicate artifacts, classifier and fixtures are implemented, omitted
criticality input leaves every retained way `unclassified` and no structural
placeholder may pass.

The observed v15 exception population and its unresolved decision status are
registered in
`reproducibility/config/traffic_simulation/resolver_exception_decision_table.yml`.
Every row must match exactly one decision-table entry before a later Resolver
version may claim complete exception classification. A decision-table entry
does not authorize a resolution until its rule and independent fixture are
implemented.

## Permission Trace

Each way-direction-lane record contains only the rules applied to that lane. The ordered trace records typemap baseline, research-scope intersection and applicable general, class, directional or lane-specific OSM transitions, including source tag/value, lane-local value, and before/after vClass sets. A tag applying to another direction or lane MUST NOT appear in that lane's trace.

## Publication and Input Integrity

All artifacts are generated in one staging directory and validated before publication. Replacement uses backups and rollback so an exception cannot mix artifacts from different runs. `.part` files are removed in `finally` cleanup. `--overwrite` is a development override only; formal orchestration uses new run identities and paths.

OSM tags require nonempty `k` and present nonempty `v`; retained ways require
valid node references. The executed v15 implementation retained only
`type=restriction`. The full-input audit subsequently found three
`type=restriction:bus` relations with turn restrictions, so exact-type
retention is not sufficient for the governed vehicle universe. Before the next
formal candidate, a versioned relation-scope table MUST retain
`type=restriction`, govern applicable vehicle-specific restriction types, and
stop on an unclassified type that may affect governed traffic. Relations
classified as unrelated to road connectivity may be removed before member
validation. A retained restriction referencing an intentionally excluded
highway way is removed with that way, while an unknown member way stops.

The Resolver input closes every governed restriction member against the
registered regional PBF before XML conversion. Closure and Resolver artifacts
MUST count relation decisions by source `type`, retained restrictions, missing
member references and supplemented element type. A discarded relation MUST
NOT be interpreted as road evidence, but discard itself requires an explicit
scope rule. This accounting does not make discarded relations invalid OSM
data. A supplied criticality map requires a source file and exact retained-way
coverage. The v15 typemap contract is `allow`-only; any retained type with
`disallow` stops policy loading.

## Relation Closure Before Attribute Classification

Attribute criticality MUST NOT be applied to the registered real data until the
next-version relation closure has fixed the classification population. The
executed v15 closure retained only relations whose `type` was exactly
`restriction`. The type-level audit later identified three governed
vehicle-specific restrictions that v15 omitted:

| Relation ID | Source type | Restriction |
|---|---|---|
| `16016504` | `restriction:bus` | `only_straight_on` |
| `16016506` | `restriction:bus` | `no_straight_on` |
| `16026064` | `restriction:bus` | `only_straight_on` |

Because `bus` is part of the governed vClass universe, these relations cannot
be classified as unrelated non-road relations. They are a known formal
scope blocker. The v15 closure, its 26,220 candidate ways and its Dry Run
remain an immutable baseline; the next-version input MUST use a new config
identity and new artifact paths rather than silently changing that baseline.

### Next-version closure policy

The next closure implementation MUST:

1. start from the registered Ota Ward BBOX extract and the hash-registered
   Kanto regional PBF;
2. retain every `type=restriction` relation in the spatial extract;
3. retain `type=restriction:bus` and any other vehicle-specific restriction
   only after mapping its vehicle scope to the governed vClass universe;
4. stop on an unclassified relation type that may constrain governed traffic;
5. recursively supplement every retained relation member from the registered
   regional PBF;
6. distinguish supplemented topology-support nodes and ways from the final
   N03 analysis subgraph;
7. validate missing node, way and relation members and detect relation cycles;
8. record retained, discarded and stopped relations by source type and rule ID;
9. generate a relation-closed PBF and OSM XML atomically; and
10. record exact commands, tool versions, config and input hashes, output
    hashes and element-level additions in the prepare manifest.

Vehicle-specific restriction handling is not a string-prefix whitelist.
Applicability to the governed vehicle universe, restriction semantics and
source-tag form require an explicit versioned decision rule and fixture.

### Population acceptance gate

The real-data criticality classifier may start only after all of the following
conditions pass:

| Gate condition | Required evidence |
|---|---|
| The three known bus restrictions are retained | relation IDs and retained-rule IDs in the closure manifest |
| Every retained relation member is present | zero missing node, way and relation members |
| Closure is deterministic | identical semantic output from identical registered inputs |
| Support elements are identified | added node/way IDs and their support/final-subgraph status |
| Candidate population is recounted | distinct governed ways by origin and highway type |
| Change from v15 is explicit | added, removed and unchanged way/relation IDs |
| New artifacts are independently identifiable | new config ID, run ID, paths and SHA-256 values |

Failure of one condition leaves the classification population unaccepted.
Criticality records MUST NOT be generated for only the old 26,220-way
population and then patched with newly discovered ways.

### Downstream invalidation

Accepting a new closure invalidates every artifact whose coverage or hash
depends on the v15 relation-closed input, including:

- the road-attribute audit;
- permission expectations;
- imputation distributions;
- the exception queue and Dry Run summary;
- attribute criticality coverage;
- candidate-way counts; and
- any provisional network or mapping derived from those inputs.

The next run MUST regenerate these artifacts from the accepted closure and
report added, removed and unchanged blockers against the v15 baseline.

## Lane Order Authority

OSM lane lists are interpreted left-to-right in the respective direction of travel. Therefore a backward list is not reversed inside the Resolver merely because it travels opposite the OSM way. The Materializer later reverses lane positions when mapping to SUMO right-to-left indices.

## Success Condition

`complete=true` requires zero blockers, one expectation record per retained way, exact agreement between direction lane counts and lane records, and matching config/input/typemap hashes. A successful artifact with an empty governed vClass universe is prohibited.

For a successful artifact, `normalized_osm` records the repository-relative path and SHA-256 of the exact normalized XML emitted by the same run. Failed artifacts omit this reference because normalized XML is not published. Fixture validation of this format does not establish eligibility on the registered Ota Ward extract.
