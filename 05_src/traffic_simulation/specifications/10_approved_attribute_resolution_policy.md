# Approved Road-Attribute Resolution Policy

## Status

- Policy ID: `ota_ward_attribute_resolution_policy_v17`
- Effective configuration: v17 and later
- Policy state: fixed
- Implementation state: partial
- Runtime validation state: incomplete
- Formal build ready: no

The machine-readable authority is
`reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml`.
The configuration is validated by
`reproducibility/config/traffic_simulation/schemas/approved_attribute_resolution_policy.schema.json`.
This specification does not retroactively change the v16 run record.

## Permission Authority

Typemap permissions are provisional candidates for topology generation. They
are not the formal permission authority. The Resolver determines expected
permissions from governed evidence, the active Scenario Profile, and approved
decision rules.

```text
typemap permissions = provisional candidate permissions
final permissions = resolver expected permissions
final permissions subset-of managed vClass universe
```

Expected permissions are materialized into explicit edge and connection input
before the final `netconvert` run. The final `net.xml` is not patched. Final
lanes and connections are regenerated and audited for exact equality with the
Resolver expectation.

## Access Specificity

Each applicable access rule has four independent specificity coordinates:

- Spatial: `way < direction < lane`
- Vehicle: `access < vehicle < motor_vehicle < vehicle_class`
- Temporal: `unconditional < active conditional`
- Purpose: `general < destination`, `delivery`, or `customers`

Rule A dominates rule B when A is at least as specific on every axis and more
specific on at least one axis. Only non-dominated maximal rules remain. Equal
results from multiple maximal rules are adopted once. Different results stop
with `ACCESS_SPECIFICITY_CONFLICT`.

A conditional rule is applicable only when its required date, time, vehicle,
and purpose context is available and the condition evaluates true. Unsupported
syntax, missing context, or a result that changes during the simulation
interval remains formal-blocking.

## Directed Road Model

Source OSM Ways are immutable evidence. Travel directions are represented as
separate Directed Segments.

```text
way/{osm_way_id}/segment/{segment_index_4digits}/direction/{F|B}
```

`F` follows source Way node order. `B` travels opposite that order.
`oneway=-1` generates only `B`. Segment indices start at zero and follow the
source Way node order. The sign of a SUMO edge ID, coordinate-nearest matching,
and generation order are prohibited as formal direction evidence.

Direction-dependent attributes retain their source direction and target
Directed Segment. Turn-restriction mappings must be unique. Missing mappings
stop with `RELATION_DIRECTED_MAPPING_MISSING`; ambiguous mappings stop with
`RELATION_DIRECTED_MAPPING_AMBIGUOUS`.

Until the generator, Schema, mappings, and pinned runtime fixtures pass, the
production pipeline continues to stop on `oneway=-1`.

## Managed Delivery Vehicle

The baseline vehicle is
`reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml`.
It is a research model assumption, not a measured production vehicle. It uses
SUMO `delivery`; electric propulsion is represented by the SUMO battery device.
It is not treated as OSM `hgv`. A vehicle may not switch to `truck` within one
experiment.

## Directional Lanes

An even total lane count on a bidirectional road is not divided equally in the
formal profile when directional lane tags are absent. Formal processing stops
with `LANE_DIRECTIONAL_ALLOCATION_MISSING`.

The equal split may be used only for structural review, with
`value_origin=model_assumed`,
`assumption_id=BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`, and
`formal_eligible=false`.

When exactly one travel direction exists and the total lane count is explicit,
that count may be adopted for the sole Directed Segment with
`value_origin=rule_derived`. `lanes:both_ways`, reversible lanes, and
time-dependent lanes remain unsupported until dedicated rules and fixtures
exist.

## Structural Placeholders

Mode-based placeholder generation is
`structural_placeholder_generation`, not formal attribute resolution.
Placeholder output is limited to topology and connection review. It is
prohibited for the formal network, calibration, independent validation, and
delivery evaluation. Calibration performed against a placeholder network
cannot be transferred to the formal network.

## Resolution Contract

New artifacts use two canonical fields:

```text
resolution_status
value_origin
```

Allowed status values are `resolved`, `not_applicable`, `unresolved`,
`conflict`, `unsupported`, and `invalid`. Allowed origins are
`source_explicit`, `source_normalized`, `rule_derived`, `evidence_derived`,
`model_assumed`, and `derived_validated_model`.

Formal values require `resolution_status=resolved` and an approved origin.
`model_assumed` is never formal eligible. The legacy `value_state` field is
read compatibility only and is not written by new artifacts.

## Remaining Implementation Gates

- Update the Resolver and configuration so typemap candidates are not treated
  as the formal authority.
- Implement access-rule normalization, dominance, maximal-rule selection, and
  conflict output.
- Migrate artifact Schema and production output to the two-field contract.
- Implement Directed Segment generation and direction-dependent relation,
  attribute, and lane mappings.
- Validate the managed vehicle profile at every vehicle-input boundary.
- Implement Permission Materializer, final connection regeneration, exact
  post-conversion audit, and final SUMO load.

These gates remain incomplete. This policy does not authorize a formal build.

## Version 17 Requirements

| Requirement ID | Normative requirement | Test ID |
|---|---|---|
| `RS-REQ-015` | Applicable access rules MUST be compared on spatial, vehicle, temporal and purpose specificity by Pareto dominance; conflicting non-dominated results MUST stop with `ACCESS_SPECIFICITY_CONFLICT`. | `RS-TST-015` |
| `RS-REQ-016` | New v17 results MUST write separate `resolution_status` and `value_origin` fields and MUST NOT write legacy `value_state`. | `RS-TST-016` |
| `ARC-REQ-007` | Travel directions MUST use deterministic Directed Segment identifiers derived from immutable OSM Way lineage; SUMO edge-ID signs, coordinate-nearest matching and generation order MUST NOT be direction evidence. | `ARC-TST-007` |
| `RS-REQ-017` | `oneway=yes`, `no` and `-1` MUST generate respectively forward-only, both-direction and backward-only Directed Segments from immutable source-node order. | `RS-TST-017` |
| `RS-REQ-018` | Every access evaluation MUST use the registered managed vehicle profile; the baseline profile MUST remain SUMO `delivery`, battery-electric and outside OSM `hgv`. | `RS-TST-018` |
| `RS-REQ-019` | A bidirectional road with only an even total lane count MUST stop formal resolution with `LANE_DIRECTIONAL_ALLOCATION_MISSING`; equal division is permitted only as a non-formal structural assumption. | `RS-TST-019` |
| `RS-REQ-020` | In v17, Resolver expected permissions MUST be the formal authority and a subset of the governed vClass universe; typemap and provisional permissions MUST NOT be treated as formal upper bounds. | `RS-TST-020` |
