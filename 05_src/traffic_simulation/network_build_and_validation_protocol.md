# SUMO Network Build and Validation Protocol

## Build Boundary

The structural profile is used only to debug geometry, direction, connectivity, conversion behavior and provenance. Before formal generation, all governed attributes, permissions, reviewed junction joins and signal structure must be fixed. A formal network change invalidates downstream calibration and validation.

## Permission-Safe Build

1. Verify the registered PBF, typemap and configuration hashes.
2. Convert PBF to raw OSM XML in the pinned analysis environment.
3. Resolve attributes and compute way-direction-lane permission expectations.
4. Materialize expected permissions into explicit final-conversion input.
5. Run final `netconvert` from the materialized input.
6. Audit, without editing `net.xml`, every generated lane and applicable connection.
7. On mismatch, stop, fix the input and rerun final conversion.

### Materializer I/O Contract

The fixed interchange format is SUMO 1.24.0 plain XML. After the resolver has written immutable permission expectations, create a topology-only OSM copy with consumed access tags removed and run provisional `netconvert` with `--plain-output-prefix governed_provisional`, `--plain-output.lanes true`, `--output.original-names true`, `--lefthand true` and `--osm.lane-access true`. The required provisional files are `governed_provisional.nod.xml`, `.edg.xml`, `.con.xml` and `.tll.xml`.

The materializer never mutates provisional files. It writes `governed_permissions.edg.xml` and `governed_permissions.con.xml`, conforming respectively to the pinned container's `edges_file.xsd` and `connections_file.xsd`. Final `netconvert` receives the provisional node/TLS files and materialized edge/connection files through `--node-files`, `--edge-files`, `--connection-files` and `--tllogic-files`. The generated `net.xml` is audit-only.

Each plain lane must have exactly one `param key="origId"`. One OSM way may map to multiple edges and lanes. Direction is determined by comparing each edge orientation with the normalized OSM way node order; an edge ID sign is not evidence. Any incomplete or ambiguous mapping stops the build.

### Lane Permission Rule

The resolver records lane positions in OSM order, left-to-right when viewed in the direction of travel. SUMO indices lanes right-to-left. With `n` lanes, resolver position `p` maps to SUMO lane index `n - 1 - p`. The materialized set is:

```text
lane_allow = resolver_allow(way, direction, p)
             intersect typemap_baseline(way_type)
             intersect governed_vclasses
```

Lane counts must agree, the set must not exceed the typemap baseline, and `allow` is serialized as lexicographically sorted, space-separated vClasses. The materializer removes `disallow`; an empty lane set is serialized as `allow=""`. The pinned left-hand fixture must verify that SUMO 1.24.0 preserves this representation and lane ordering. Failure stops real-data use and requires a versioned contract change.

### Connection Permission Rule

Only provisional connections are candidates, preserving importer topology and turn restrictions. The materializer does not synthesize an absent connection. For candidate `c`:

```text
connection_allow(c) = from_lane_allow(c)
                      intersect to_lane_allow(c)
                      intersect provisional_connection_allow(c)
```

An absent provisional `allow` is unrestricted before the endpoint intersection. A nonempty set is written as an exact sorted `allow` value with `disallow` removed. A zero set causes the connection to be omitted and the reason to be recorded. Post-conversion audit requires every nonempty expected connection, prohibits every zero-set and unexplained connection, and compares effective permissions exactly.

The materializer is not yet implemented. The earlier importer governance fixture failed, and a materialized-output fixture has not been run. XSD inspection and a provisional plain-export probe establish only that these interfaces and `origId` are available; they do not validate the mapping rules.

## Formal Build Completeness

Permissions are only one formal gate. Formal generation also requires registered input/hash revalidation, zero unresolved governed attributes, accepted formal evidence or validated imputation, safe handling or zero occurrence of `oneway=-1`, reviewed junction joins and node file, reviewed signal junction/TLS-link structure, a vehicle-input validator, complete environment manifest, classified warnings and exclusions, preregistered structural thresholds, vClass-directional connectivity, candidate-subgraph review, immutable small artifacts, and successful final SUMO load. The current status of each requirement is authoritative in `network_current_specification.md` and `sumo_network.yml`; policy text or pytest assertions alone do not count as runtime or real-data verification.

## Structural Gate

Report both way-count and road-length retention. Evaluate directed reachability separately for all governed vClasses, including depot-to-customer/charger and return-to-depot reachability. Also report major-road-pair reachability, largest drivable-component length share, direction mismatches, representative OD route success, XML/SUMO load status and classified warnings.

Thresholds require result-blind preregistration and rationale. An unclassified warning or untraceable lane stops the build. `output.original-names=true` supports the one-to-many provenance chain from OSM way to SUMO edges and lanes.

## Artifacts

Large generated OSM and `net.xml` files may remain outside Git. The `.netccfg`, build manifest, build summary, warning classification and artifact checksum list require immutable versioning in Git or content-addressed artifact storage, with a tracked index when external storage is used.

The manifest records both container digests, SUMO, `netconvert`, PROJ, `osmium`, Python and dependency versions, locale, platform, precision options, all governed hashes and exact commands.

## Evidence Priority

1. Pinned SUMO 1.24.0 runtime fixture.
2. SUMO `v1_24_0` source or XSD.
3. Dated and hashed official-document snapshot.
4. Current official documentation.

Current documentation alone does not establish version-specific importer behavior.
