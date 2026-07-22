# Tokyo SUMO Network Current Specification

## Status

- Configuration: `ota_ward_sumo_network_v14`
- Created: 2026-07-18
- Last updated: 2026-07-22
- Configuration lineage date: 2026-07-16
- Runtime permission fixture: failed
- Formal build input ready: no
- Formal network accepted: no
- Downstream experiment ready: no
- Specification state: current governed draft; formal execution is not authorized

The machine-readable authority is `reproducibility/config/traffic_simulation/sumo_network.yml`. Its typed state contract is `reproducibility/config/traffic_simulation/sumo_network.schema.json`, and cross-field invariants are enforced by `validate_sumo_network_config.py`. Normative component contracts are under `05_src/traffic_simulation/specifications`; artifact formats are under `reproducibility/config/traffic_simulation/schemas`. This document is a current-state summary rather than a second normative implementation contract. Historical decisions are kept in `03_data/metadata/acquisition/20260718_sumo_tokyo_motorized_typemap_design.md`.

## Attribute Mapping

| OSM input | Resolver representation | SUMO representation |
|---|---|---|
| `lanes=*`, directional lane tags | total and direction-specific lane counts | `numLanes` and generated lanes |
| `maxspeed=*`, directional speed tags | governed speed in km/h before conversion | `speed` in m/s |
| `oneway=*` | governed directionality | generated edge directions |
| access, vehicle, class, direction and lane tags | expected permissions by way, direction and lane | lane `allow`/`disallow` and usable connections |

No unsupported explicit OSM value may be replaced by a structural placeholder. `oneway=-1`, directionally asymmetric speeds, unsupported conditionals, bidirectional single-lane allocation and unresolved permissions stop conversion until a governed representation exists.

## Network Scope

- Geography: Ota Ward boundary with retained acquisition-envelope connectors.
- Traffic side: Japanese left-hand traffic.
- Governed vClasses: `passenger`, `taxi`, `bus`, `coach`, `delivery`, `truck`, `motorcycle`, `moped`.
- Small delivery vans use `delivery`; heavy freight vehicles use `truck`. A vehicle cannot change vClass within an optimization instance.
- `highway=track` is excluded because its land-access function is outside the initial general motorized network, not because it is necessarily unpaved.
- Surface state is evaluated independently from road function using `surface`, with `smoothness` and `tracktype` as supporting evidence. The formal unpaved-road rule is pending.

## Permission Governance

The resolver computes expected permissions before conversion. A dedicated materializer must write those permissions into the explicit input of the final `netconvert` run so that lanes and connections are built from the governed permissions.

Generated `net.xml` permissions must not be edited. Post-conversion processing is audit-only. Every lane and applicable connection must exactly match the expectation; otherwise the build stops, the pre-conversion input is corrected, and final `netconvert` is rerun.

This materializer and its fixed-SUMO runtime fixture are not implemented. Permission governance therefore remains formal-blocking.

The fixed materializer interface is SUMO 1.24.0 plain XML. A provisional conversion writes `.nod.xml`, lane-expanded `.edg.xml`, `.con.xml`, `.tll.xml` and exact `edge_provenance.json`; the materializer writes new `governed_permissions.edg.xml` and `governed_permissions.con.xml` files and never edits provisional files or final `net.xml` in place. Each external lane must carry exactly one OSM way ID through `param key="origId"`. Edge direction comes from exact source-node lineage indices. Coordinate-nearest matching and the sign of a SUMO edge ID are prohibited as formal direction evidence.

Resolver lane positions are OSM left-to-right as viewed in each respective travel direction, while SUMO lane indices are right-to-left. Forward and backward both use `sumo_index = n - 1 - p`; the Resolver does not reverse backward OSM lists. The expected lane allow-set is the intersection of the resolver expectation, typemap baseline, governed vClasses and effective provisional restriction. A partially empty edge keeps empty lanes as `disallow="all"`; a directed edge whose lanes are all empty is removed with incident connections before TLS review. Connections are explicit lane-to-lane candidates and are never synthesized. The pinned fixture must confirm these rules before real-data use.

For bidirectional roads, the formal Resolver requires explicit `lanes:forward` and `lanes:backward`; equal division of an even total is structural-only and is audited as an assumption. Structural imputation donors must themselves pass direction, lane, speed, conditional-tag and permission eligibility checks. Permission provenance is lane-local: a directional or lane-specific access tag is recorded only for the lanes to which it was applied.

## Signal Structure

Signalized-junction selection and connection-to-TLS-link mapping are network structure. In pinned SUMO 1.24.0 plain XML, TLS connection/link records belong to `.tll.xml`, not the permission `.con.xml` connection type. Provisional TLS output is review evidence only. After the governed connection set is fixed, reviewers produce `governed_reviewed.con.xml`, `governed_reviewed.tll.xml` and a hash-bound review manifest. Every controlled connection must have a reviewed link index, and each phase-state length must equal the controlled-link count. A later connection or signal-structure change invalidates the review, calibration and validation.

## Required Order

```text
structural network
  -> topology, direction and connection debugging
  -> governed attributes and lane permissions
  -> provisional connections
  -> connection permissions and final connection set
  -> reviewed signal-junction and TLS-link structure
  -> formal baseline network
  -> demand
  -> signal timing and traffic calibration
  -> independent validation
  -> delivery, classical and QAOA evaluation
```

Structural output is not valid for travel-time, capacity, delivery or solver-comparison results.

## Verification State

| Gate | Requirement | Actual implementation | Runtime/real-data evidence | Current result |
|---|---|---|---|---|
| Build input | Registered PBF, extract and hashes | implemented | acquisition/extraction completed; manifest recheck pending | pending |
| Build input | Typemap XML | implemented | XSD passed; importer governance fixture failed | ineligible |
| Build input | Attribute resolver | partial governed scope implemented | strict input, donor, compound type, relation, transaction and CLI failure fixtures passed; registered extract not run | pending |
| Build input | Permission expectation JSON | v14 Schema output with lane-local rule trace implemented | positive, negative and bidirectional fixture oracles passed; registered extract not run | pending |
| Build input | Permission materializer | contract fixed, implementation absent | materialized fixture not run | ineligible |
| Build input | `oneway=-1` | fail-closed detection only | formal occurrence check not run | conditional |
| Build input | Formal attribute evidence/imputation | not implemented | not run | pending |
| Build input | Junction join review/node file | not implemented | not run | pending |
| Build input | Post-permission signal/TLS review | not implemented | not run | pending |
| Build input | Vehicle-input validator | not implemented | not run | pending |
| Build input | `prepare`/`validate` pipeline | not implemented | not run | pending |
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

Pytest counts are progress indicators, not sufficient evidence. Each recorded test run must include commit, container digest, exact command, collection hash, exit code, log hash and timestamps.
