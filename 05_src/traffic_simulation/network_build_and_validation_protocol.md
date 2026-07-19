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

The exact permission materialization format must pass the pinned SUMO 1.24.0 fixture before real-data use.

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
