# v17 Attribute Resolution Semantic Invariants

## Document control

- Invariant set: `ota_ward_attribute_resolution_semantic_invariants_v17`
- Version: `1.0.0`
- Policy: `ota_ward_attribute_resolution_policy_v17`
- Machine-readable authority: `reproducibility/config/traffic_simulation/v17_semantic_invariants.yml`
- Schema: `reproducibility/config/traffic_simulation/schemas/semantic_invariants_v17.schema.json`

This document separates constraints that JSON Schema can enforce locally from
cross-record, set, population, provenance, and determinism constraints. The
machine-readable file fixes each invariant's ID, assertion, failure state,
stop code, severity, and implementation phase.

## Invariant families

| Family | IDs | Responsibility |
|---|---|---|
| State contract | `AR-STATE-001`–`005` | resolved/non-resolved fields, formal eligibility, legacy output, conflict evidence |
| Identity | `AR-ID-001`–`003` | RFC 8785 record identity, uniqueness, classification projection invariance |
| Directed Segment | `AR-DIR-001`–`005` | canonical interval, lineage, `oneway=-1`, relation mapping, prohibited direction evidence |
| Directional lanes | `AR-LANE-001`–`004` | count equation, vector length, profile boundary, SUMO index mapping |
| Speed | `AR-SPEED-001`–`003` | unit conversion, priority/asymmetry, interval changes |
| Access | `AR-ACCESS-001`–`009` | scope separation, ontology sets, dominance, order invariance, permission authority, non-governed domain intersection |
| Conditional | `AR-COND-001`–`004` | context, syntax boundary, last-match boundary, interval changes |
| Evidence | `AR-EVID-001`–`003` | method approval, donor eligibility, immutable manual evidence |
| Population | `AR-EXCL-001`–`003` | population equation, registered exclusions, omission accounting |
| Provenance | `AR-PROV-001`–`004` | canonicalization, manifests, determinism, profile-separated outputs |
| Acceptance | `AR-ACC-001`–`003` | zero-blocker gate, validation layers, missing-evidence result |

## Validation boundary

JSON Schema validates required fields, types, enums, local nullability, the
formal prohibition on `model_assumed`, and manifest shapes. The Phase 1
authority validator validates configuration/Schema/Registry synchronization,
registered references, hashes, uniqueness, and invariant coverage. Runtime
semantic evaluation of Resolver output is implemented in the target phase
recorded for each invariant; Phase 1 completion does not claim those later
runtime checks have executed.

An invariant failure is fail-closed. A missing implementation or missing
runtime artifact is not evidence that an invariant passed.
