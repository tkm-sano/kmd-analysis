# Ota Ward Relation Closure v16

## Purpose and decision

This record fixes the accepted relation-closure population used before road
attribute classification. It replaces neither the historical v15 Dry Run nor
its artifacts. The accepted configuration identity is
`ota_ward_relation_closure_v16`, version 16, and the run identity is
`ota-ward-relation-closure-v16-20260730-01`.

The closure retains ordinary turn restrictions and bus-specific turn
restrictions as separate governed categories. Other relation types are counted
and discarded under an explicit unrelated-type rule. An unclassified
`restriction:*` type stops the process rather than being discarded.

## Registered inputs

| Input | Repository path | SHA-256 |
|---|---|---|
| Ota Ward acquisition-envelope extract | `03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf` | `10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041` |
| Kanto regional source authority | `03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf` | `aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d` |
| Historical v15 comparison input | `03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.osm.pbf` | `44374ffbb038a064c825a97445790d3584c16199d9a863c2c7acee29642d86b2` |
| v16 closure configuration | `reproducibility/config/traffic_simulation/relation_closure_v16.yml` | `00f1c7d4b43753dc29a6e63df823b304c7a6899d4cb4220bcf4c6e927bfad0f5` |

The regional PBF is the source authority for every referenced element absent
from the acquisition-envelope extract. The toolchain uses `osmium 1.15.0` in
the repository's fixed `analysis` service.

## Selection and closure rules

1. Every node and way in the registered BBOX extract enters the closure seed.
2. Every exact `type=restriction` relation enters category
   `ordinary_turn_restriction` under `REL-ORDINARY-001`.
3. Every exact `type=restriction:bus` relation enters category
   `bus_turn_restriction` under `REL-BUS-001`.
4. A different `restriction:*` type is formal-blocking until a vehicle-scope
   rule is registered.
5. Referenced nodes, ways and nested relations are recursively supplied from
   the regional source.
6. Missing references, relation cycles and duplicate identifiers within an
   OSM element namespace stop publication.
7. Outputs are staged and published only after every check and fixed
   acceptance count passes.

OSM identifiers have separate node, way and relation namespaces. The duplicate
check therefore rejects two node IDs, two way IDs or two relation IDs with the
same value; it does not treat `node/1` and `way/1` as a collision.

## Commands

The implementation entry point is:

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.network.build_sumo_network prepare
```

The entry point verifies input hashes, constructs the seed ID file and runs the
following governed operations in a staging directory:

```text
osmium getid <regional-pbf> --id-file <v16-id-set> --add-referenced --output <v16-pbf>
osmium cat <v16-pbf> -f osm --output <v16-osm-xml>
```

The exact expanded commands are retained in the generated manifest. The
second execution used `--overwrite` only to test determinism after the first
accepted output set existed.

## Relation and element results

| Measure | Result |
|---|---:|
| Ordinary `type=restriction` relations | 581 |
| Bus `type=restriction:bus` relations | 3 |
| Closed-input relations | 584 |
| BBOX nodes | 1,709,568 |
| Closed-input nodes | 1,709,627 |
| Supplemented nodes | 59 |
| BBOX ways | 323,393 |
| Closed-input ways | 323,409 |
| Supplemented ways | 16 |
| Missing node references | 0 |
| Missing way members | 0 |
| Missing relation members | 0 |
| Relation cycles | 0 |
| Duplicate identifiers | 0 |

The three required bus relations are `16016504`, `16016506` and `16026064`.
All are present in the accepted manifest.

## Road roles and populations

The closure retains more source context than the final analysis needs. Roles
are therefore assigned separately:

| Role or population | Rule | Ways |
|---|---|---:|
| Governed attribute-resolution candidate | highway type is in the motorized whitelist | 26,220 |
| Final analysis target | governed way geometry intersects the N03 Ota Ward boundary | 13,494 |
| Topology support | member of a retained governed relation but not a final analysis target | 555 |
| Excluded source context | retained in the closure but neither final nor topology support | 309,360 |

The roles are mutually exclusive over all 323,409 closed-input ways. A
topology-support way is retained to preserve a governed relation; this does not
automatically make it a delivery-analysis road.

Relative to v15, the governed candidate-way population has zero added ways,
zero removed ways and 26,220 unchanged ways. The three bus relations add
governed semantics but introduce no new candidate way because their member
ways were already present through the ordinary closure.

## Fixed outputs

| Output | SHA-256 |
|---|---|
| ID set | `9e9e25bc2db3c340a1fa1e085071a41626884ed2760c293ace226b11f4e9b789` |
| Relation-closed PBF | `ea9c20b4c1214c7f6cb00afb977638f5e9b69535c53787e2108006814e61591d` |
| Relation-closed OSM XML | `8b5157e48c3c87c2b4430f56d6abe292ce1ea5449b374ae4cb395fc19475b67d` |
| Element-role artifact | `09284abce54e6e2c0e3e424f3cf389c15051c8cbd04a2421034c2928fc7bbea2` |
| Accepted manifest | `41e5d6741115d6c99babf2625613c7355d2b4797b2cdf43fd809667748e95888` |

The first and second executions produced identical hashes for the ID set, PBF,
OSM XML and role artifact. The manifest hash changes when its generation time
or registered configuration hash changes; the hash above identifies the
accepted final manifest. The role artifact records each supplemented node and
way as `final_analysis_target`, `topology_support`, or `excluded`; all 59
supplemented nodes and 16 supplemented ways are topology support in this run.

## Acceptance and downstream limit

The relation-closure population is accepted. This acceptance does not make a
formal SUMO network available. The Classifier and Resolver must consume the
new XML hash and role artifact, regenerate complete managed-attribute records,
and reach zero blockers before normalized OSM can be published. Bus
restrictions must later be materialized and audited in SUMO connection
semantics; retaining the source relation alone does not establish that
downstream behavior.
