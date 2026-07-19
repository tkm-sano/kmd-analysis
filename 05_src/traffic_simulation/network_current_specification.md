# Tokyo SUMO Network Current Specification

## Status

- Configuration: `ota_ward_sumo_network_v12`
- Created: 2026-07-18
- Last updated: 2026-07-19
- Configuration lineage date: 2026-07-16
- Runtime permission fixture: failed
- Formal build eligible: no

The machine-readable authority is `reproducibility/config/traffic_simulation/sumo_network.yml`. This document contains only currently effective requirements. Historical decisions are kept in `03_data/metadata/acquisition/20260718_sumo_tokyo_motorized_typemap_design.md`.

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

The fixed materializer interface is SUMO 1.24.0 plain XML. A provisional conversion writes `.nod.xml`, lane-expanded `.edg.xml`, `.con.xml` and `.tll.xml`; the materializer writes new `governed_permissions.edg.xml` and `governed_permissions.con.xml` files and never edits the provisional files or final `net.xml` in place. Each lane must carry exactly one OSM way ID through `param key="origId"`. Edge direction is determined from its orientation relative to the normalized OSM node order, never from the sign of a SUMO edge ID.

Resolver lane positions are OSM left-to-right in the travel direction, while SUMO lane indices are right-to-left. For `n` lanes, resolver position `p` maps to SUMO index `n - 1 - p`. The expected lane allow-set is the intersection of the resolver expectation, the typemap baseline and the governed vClass set. A candidate connection is retained only when the intersection of its from-lane allow-set, to-lane allow-set and any provisional connection restriction is nonempty. Empty intersections are removed and recorded; connections absent from the provisional topology are never synthesized. The pinned left-hand fixture must confirm these rules before real-data use. A mismatch changes the contract and configuration version; it is not repaired after conversion.

## Signal Structure

Signalized-junction selection and connection-to-TLS-link mapping are network structure. They must be reviewed before the formal baseline network is accepted. Cycle length, phases, splits and offsets are timing parameters and are calibrated after demand input. A later signal-structure change invalidates calibration and validation.

## Required Order

```text
structural network
  -> topology, direction and connection debugging
  -> governed attributes and permissions
  -> signal-junction and TLS-link structure
  -> formal baseline network
  -> demand
  -> signal timing and traffic calibration
  -> independent validation
  -> delivery, classical and QAOA evaluation
```

Structural output is not valid for travel-time, capacity, delivery or solver-comparison results.

## Verification State

| Formal-build requirement | Actual implementation | Unit/static evidence | Runtime evidence | Real-data evidence | Current result |
|---|---|---|---|---|---|
| Registered PBF, extract and hashes | implemented | configured hashes | acquisition/extraction completed | baseline quality summary exists | reverify in manifest |
| Typemap XML | implemented | unit and XSD passed | importer governance fixture failed | formal pipeline not run | blocked |
| Attribute resolver | implemented for governed partial scope | unit tests passed | positive/negative XML fixtures passed | actual extract not run | blocked |
| Permission expectation JSON | implemented | unit tests passed | resolver fixtures passed | actual extract not run | blocked |
| Permission materializer | not implemented; I/O and rules fixed | contract assertions only | not run | not run | blocked |
| Lane/connection post-audit | not implemented | policy assertions only | not run | not run | blocked |
| `oneway=-1` handling | fail-closed detector implemented; safe transform absent | unit test passed | not run | baseline count only, not a formal run | zero occurrences required |
| Formal attribute evidence and validated imputation | not implemented | partial policy assertions | not run | not run | blocked |
| Junction join review and reviewed node file | not implemented | policy assertions only | not run | not run | blocked |
| Signal junction and TLS-link review | not implemented | policy assertions only | not run | not run | blocked |
| SUMO vehicle-input validator | not implemented | policy assertions only | not run | not run | blocked |
| `prepare`/`validate` build pipeline | not implemented | not run | not run | not run | blocked |
| Environment fingerprint and build manifest | not implemented | required fields asserted | isolated pinned SUMO commands run without formal manifest | not run | blocked |
| Warning/exclusion auditor | not implemented | policy assertions only | known fixture warnings recorded, auditor not run | not run | blocked |
| Structural quality gate and thresholds | metrics fixed; thresholds pending preregistration | policy assertions only | not run | not run | blocked |
| Candidate-subgraph review | scope fixed, review not implemented | policy assertions only | not run | not run | blocked |
| Small reproducibility artifacts | retention policy fixed, publication not implemented | policy assertions only | not run | not run | blocked |
| Formal network and SUMO load | not built | not applicable | not run | not run | blocked |

Pytest counts are progress indicators, not sufficient evidence. Each recorded test run must include commit, container digest, exact command, collection hash, exit code, log hash and timestamps.
