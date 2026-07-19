# Tokyo SUMO Network Current Specification

## Status

- Configuration: `ota_ward_sumo_network_v11`
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

| Requirement | Implementation | Unit/static test | Runtime fixture | Real data | Formal eligible |
|---|---|---|---|---|---|
| Typemap XML | implemented | passed, including XSD | not applicable to XSD validation | not run | blocked by permissions |
| Attribute resolver | partial governed scope | passed | not applicable | not run | no |
| Permission materialization | not implemented | policy only | failed importer fixture | not run | no |
| Signal structure review | not implemented | policy only | not run | not run | no |
| Formal network | not built | not applicable | not run | not run | no |

Pytest counts are progress indicators, not sufficient evidence. Each recorded test run must include commit, container digest, exact command, collection hash, exit code, log hash and timestamps.
