# Ota Ward v15 Resolver Full Dry Run

## 1. Purpose and Scope

This record describes the first full `structural` Resolver run over the
registered Ota Ward input under configuration v15. Its purposes are to record
input identity, reproduce the Resolver input closure, identify governed
attribute blockers, and verify fail-closed publication behavior.

This is an internal dry-run evidence record. It is not a formal SUMO network
build, a final definition of the Ota Ward road subgraph, or evidence that
downstream simulation is authorized. The run exposed missing runtime
provenance that cannot be reconstructed retroactively; those limitations are
listed explicitly rather than filled with inferred values.

## 2. Run Identity and Status

| Field | Recorded value |
|---|---|
| Evidence record ID | `ota-ward-v15-structural-20260723-01` |
| Run window | approximately 2026-07-23 15:48:03 to 15:50:48 JST |
| Run-window source | local output-file timestamps; not a runtime-emitted timestamp |
| Configuration | `ota_ward_sumo_network_v15`, version 15 |
| Profile | `structural` |
| CLI exit code | 2 |
| Classified result | governed Resolver validation failure |
| Resolver output eligible | false |
| Formal build input ready | false |
| Formal network accepted | false |
| Normalized OSM published | no |

The failure report contains 46,056 governed blockers matching the audit stop
rows. Therefore exit code 2 in this run denotes a completed Resolver evaluation
that stopped at its materialization gate, not an unclassified program crash.
The approximate run window is useful for locating local files but is not a
substitute for an emitted start and end timestamp.

### CLI exit-code semantics

| Exit code | Resolver meaning | Publication behavior |
|---:|---|---|
| 0 | Resolution and artifact validation succeeded | Normalized OSM and the complete artifact set are published atomically |
| 2 | A classified Resolver failure was recorded, or argument parsing failed before execution | A coherent governed blocker run retains its audit artifacts and failure report but not normalized OSM; other classified failures may publish only the failure report |
| 3 | The Resolver could not publish a valid failure report | No governed success output is authorized |

These are the implemented CLI meanings in
`resolve_osm_attributes.py`; there is no implemented exit code 4. An exit code
alone is not sufficient to distinguish argument parsing from a governed
validation failure. The failure-report contents and artifact hashes make that
distinction for this run.

## 3. Eligibility Gates

The Resolver publication gate and the repository-wide readiness gates are
different decisions.

### Resolver publication gate

The v15 Resolver permits a normalized OSM output only when all of the following
conditions hold:

1. the input structure and retained relation references pass validation;
2. every retained way resolves `oneway`, directional lanes, `maxspeed` and
   permissions without a stopping audit decision;
3. the permission artifact contains one internally consistent expectation for
   every retained way;
4. the input, typemap and output provenance required by the artifact schemas is
   present; and
5. the staged artifact set passes schema validation and atomic publication.

| Resolver condition | Result | Evidence |
|---|---|---|
| Input XML and retained references accepted | pass | Resolver reached all 26,220 candidate ways |
| Audit stop rows equal zero | fail | 46,056 stop rows |
| Permission expectation completeness | fail | `complete=false`; 1,874 of 26,220 ways have generated expectation records |
| Incomplete permission artifact schema | pass | validated inside the Resolver |
| Failure-report schema | pass | validated inside the Resolver |
| Atomic failure publication | pass for the observed local state | audit artifacts exist; normalized output and `.part` files do not |

One blocker is sufficient to prevent normalized OSM publication. Warnings do
not independently authorize output and are not a substitute for resolving a
blocker.

### Repository-wide readiness gates

`formal_build_input_ready` additionally requires the materializer, reverse
oneway handler, formal attribute evidence, junction and signal review, vehicle
input validation, build pipeline, and environment manifest. The gate is false
even if Resolver blockers later reach zero. `formal_network_acceptance` is
evaluated only after a formal `netconvert` build and its post-build audits.
These requirements are defined in
`reproducibility/config/traffic_simulation/sumo_network.yml`.

## 4. Registered Input Provenance

| Input | Repository-relative path | SHA-256 |
|---|---|---|
| Geofabrik Kanto PBF | `03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf` | `aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d` |
| Registered Ota Ward BBOX extract | `03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf` | `10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041` |
| Resolver closure ID set | `03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.ids` | `306f82011002454037b1f871f5c7b2ae64d9dcfa8eadca1655b223c34557297f` |
| Resolver relation-closed PBF | `03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.osm.pbf` | `44374ffbb038a064c825a97445790d3584c16199d9a863c2c7acee29642d86b2` |
| Resolver input OSM XML | `03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716.osm.xml` | `87e074aefd79388084c127cf1f9c2b57fafa8173ff2703c7df03af604720c9df` |
| `sumo_network.yml` used by the run | `reproducibility/config/traffic_simulation/sumo_network.yml` | `6b45a611f5f25667003a55ec4cd99bc37d1a2eaad9a0bbe298089f34666d21b0` |
| Governed typemap | `reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml` | `81c7ed6c5f40ce0e06071bbba0ecc52b5abc2b2d8b8da64dc9cb2b3296c253be` |

The BBOX extract was rehashed before processing and matched its acquisition
record and quality summary. The configuration hash above identifies the
content used for the run; the file has subsequently changed as status and
evidence fields were updated.

## 5. Spatial Extent and Candidate Population

### Authoritative study area

The research analysis extent is the N03 Ota Ward administrative boundary, not
the PBF header BBOX or the coordinate extent of closure elements.

| Authority | Value |
|---|---|
| Study-area ID and version | `ota_ward`, version 1 |
| Boundary selector | `N03_007="13111"`, `N03_001="東京都"`, `N03_004="大田区"` |
| Boundary artifact | `03_data/processed/traffic_simulation/road_network/boundaries/ota_ward_n03_2026.parquet` |
| Boundary SHA-256 | `7b54c39e1826c224bf0a1f8617afe2a8434df45b1572c57d46e2a64a93325aca` |
| Study-area policy | `network_clip_method: intersects_boundary` |

The mechanically derived acquisition BBOX in EPSG:4326 is:

| West | South | East | North |
|---:|---:|---:|---:|
| 139.652974773 | 35.528198081 | 139.826027782 | 35.613210171 |

The BBOX is an acquisition envelope. A `complete_ways` extract can retain
nodes outside it, and it includes areas outside the N03 polygon. Neither class
of element is automatically an Ota Ward analysis observation.

### Dry-run population

This Resolver run did not apply the final N03 polygon clip. It audited every
v15-whitelisted motorized way in the relation-closed input:

| Population component | Distinct ways |
|---|---:|
| v15 candidates already in the registered BBOX extract | 26,204 |
| referenced ways added by relation closure | 16 |
| governed candidates audited | 26,220 |

All 16 added ways are governed road types and were consequently included in the
Resolver audit. They are support elements needed to interpret retained turn
restrictions, but this run does not decide whether their complete geometry
belongs in the final network. A later build-stage boundary rule must distinguish
topology support from the final analysis subgraph and must specify how
boundary-crossing ways are retained.

The earlier count of 26,201 was produced by a visualization or pre-v15
candidate filter and is not the denominator of this run. The exact v15 filter
gives 26,204 ways before closure; the 16 closure ways produce 26,220.

## 6. Relation Closure Procedure

The registered `complete_ways` extract contains 2,373 relations, including
partial non-road relations and turn restrictions. A direct Resolver run first
stopped on water multipolygon relation `32009`. Non-restriction relations are
outside Resolver scope and are discarded before member-reference validation.

A second run stopped on restriction relation `9435404` because its `from` way
was outside the BBOX extract. The retained source tags are:

```text
type=restriction
restriction:conditional=only_straight_on @ (07:00-08:30, 13:00-15:00)
except=bicycle
from=way/680507455
via=node/987412900
to=way/679571648
```

The closure ID set contains every node and way in the registered BBOX extract
and only its 581 `type=restriction` relations. It is reproducibly generated as:

```bash
osmium cat \
  03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf \
  -f opl |
awk '$1 ~ /^[nw]/ || ($1 ~ /^r/ && $0 ~ /(T|,)type=restriction(,| )/) { print $1 }' \
  > 03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.ids
```

The registered regional PBF is then used as the referenced-element authority:

```bash
osmium getid \
  03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf \
  --id-file 03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.ids \
  --add-referenced \
  --output 03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.osm.pbf

osmium cat \
  03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_resolver_input.osm.pbf \
  -f osm \
  --output 03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716.osm.xml
```

On 2026-07-23 these commands were replayed into temporary paths with
`osmium 1.15.0`. They reproduced both the registered PBF and XML SHA-256
exactly. `--add-referenced` adds referenced members from the fixed regional
authority; the selected relation set contains no relation-to-relation members,
so this run has no recursive relation cycle.

### Closure and reference checks

| Check | Result |
|---|---:|
| Nodes in relation-closed input | 1,709,627 |
| Ways in relation-closed input | 323,409 |
| Retained restriction relations | 581 |
| Non-restriction relations omitted from the BBOX extract | 1,792 |
| Nodes added relative to BBOX extract | 59 |
| Ways added relative to BBOX extract | 16 |
| Missing node references in ways | 0 |
| Missing node members in retained relations | 0 |
| Missing way members in retained relations | 0 |
| Missing relation members in retained relations | 0 |
| Relation-to-relation members | 0 |
| Cyclic relation references | 0 |

The 1,792 non-restriction relations omitted from the closure ID set are:

| OSM `type` value | Relations |
|---|---:|
| `boundary` | 635 |
| `route` | 477 |
| `multipolygon` | 322 |
| `route_master` | 148 |
| `public_transport` | 118 |
| `building` | 44 |
| `network` | 12 |
| `waterway` | 10 |
| `bridge` | 6 |
| `superroute` | 4 |
| `restriction:bus` | 3 |
| `site` | 3 |
| `destination_sign` | 3 |
| `enforcement` | 2 |
| `tunnel` | 2 |
| `collection` | 1 |
| `provides_feature` | 1 |
| `tracks` | 1 |
| Total | 1,792 |

These relations were omitted from v15 Resolver member validation. The count is
an audit of the executed scope, not a claim that the relations are invalid OSM
data.

### Retrospective relation-scope blocker

The type-level audit found three `type=restriction:bus` relations:

| Relation | Restriction |
|---|---|
| `16016504` | `only_straight_on` |
| `16016506` | `no_straight_on` |
| `16026064` | `only_straight_on` |

These are vehicle-specific turn restrictions and cannot be classified as
non-road relations. Because `bus` is a governed vClass, the next configuration
must include them in relation closure and Resolver validation, or establish a
documented alternative representation. The v15 Dry Run omitted them under its
exact `type=restriction` rule. This does not alter the recorded 307 attribute
exceptions, but it is an additional formal blocker and means the v15 relation
scope is not sufficient for a formal network.

The Resolver subsequently excluded four restriction relations because their
way members belonged to highway types intentionally excluded by the typemap
whitelist. The regional header retained by `osmium getid` is not an analysis
extent.

## 7. Configuration Loading and Execution Environment

The CLI has no configuration-path argument. `load_policy()` reads the
repository-root-relative constant:

```text
reproducibility/config/traffic_simulation/sumo_network.yml
```

It requires `config_version: 15`, selects the requested `structural` profile,
reads the typemap path from `typemap_policy.path`, and refuses to continue if
the actual typemap SHA-256 differs from the hash stored in the configuration.
The working directory for the container is `/workspace`, but configuration
resolution uses `REPOSITORY_ROOT` rather than the shell working directory.

### Environment observed for the run

| Field | Value or evidence status |
|---|---|
| Compose service | `analysis`, `linux/amd64` |
| Local image ID | `sha256:90d04077f751a281655bc93910614b826eac8043e1ad06af71534a0d496d15e0` |
| Registry digest | not available; the analysis image was locally built |
| Base image declaration | `python:3.11-slim-bookworm` |
| OS and architecture | Debian 12, Linux x86_64 |
| Python | 3.11.15 |
| XML parser | CPython `xml.etree.ElementTree`, Expat 2.7.4 |
| JSON Schema validator | `jsonschema` 4.24.0 |
| YAML parser | PyYAML 6.0.2 |
| `osmium` / `libosmium` | 1.15.0 / 2.19.0 |
| Analysis requirements SHA-256 | `aeed51e4ca89084d763062f369159a038b6d499202046931f7451633f7697f72` |
| Repository HEAD observed after the run | `7f97dfe92bd6d5cf8c68412ededd0d55873595ce` |
| Working tree at run | dirty; v15 Resolver changes were not represented by a single commit |

The local image was created before this run and remains available, but the
original execution did not emit an immutable registry digest or environment
manifest. The repository HEAD does not identify the exact dirty source tree.
Consequently this section supports local reconstruction but does not satisfy
the formal runtime-fingerprint requirement. Future orchestration must emit the
container digest, source-tree identity, dependency hashes, platform, locale and
timestamps into a run manifest before execution.

## 8. Exact Resolver Command

```bash
PYTHONPATH=05_src python -m traffic_simulation.network.resolve_osm_attributes \
  --profile structural \
  --input-osm 03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716.osm.xml \
  --output-osm 03_data/processed/traffic_simulation/road_network/sumo/structural/ota_ward_20260716_resolved.osm.xml \
  --audit-csv 03_data/processed/traffic_simulation/validation/ota_ward_20260716_road_attribute_audit.csv \
  --permission-expectations-json 03_data/processed/traffic_simulation/validation/ota_ward_20260716_permission_expectations.json \
  --imputation-summary-json 03_data/processed/traffic_simulation/validation/ota_ward_20260716_imputation_summary.json \
  --failure-report-json 03_data/processed/traffic_simulation/validation/ota_ward_20260716_resolver_failure_report.json
```

No criticality CSV was supplied. All ways therefore remained `unclassified`,
and structural mode values were not applied. The attribute-specific
criticality contract and its admissible evidence must be completed before such
values can be used.

## 9. Counting Units and Classification Definitions

An audit row represents one governed attribute decision for one OSM way.
Several attributes on the same way can stop, so blocker rows and blocked ways
are not interchangeable.

`bulk missing` means a stop row whose `value_state` is exactly `missing`. In
this run the source attribute was absent, no governed derivation supplied a
value, and the unclassified way was not eligible for a structural placeholder.

`rule or data exception` means a stop row whose `value_state` is one of
`conflict`, `invalid`, `unresolved`, or `valid_but_unsupported`. It represents
a present value or tag combination that cannot yet be resolved by the governed
implementation. These categories are mutually exclusive for this summary.

| Metric | Counting unit | Count | Denominator | Rate |
|---|---|---:|---:|---:|
| Governed candidates | distinct ways | 26,220 | 26,220 | 100.00% |
| Ways with at least one blocker | distinct ways | 24,346 | 26,220 | 92.85% |
| Ways with no blocker across governed attributes | distinct ways | 1,874 | 26,220 | 7.15% |
| Audit decisions | attribute-way rows | 83,884 | - | - |
| Blockers | attribute-way rows | 46,056 | - | - |
| Bulk missing | blocker rows | 45,749 | 46,056 | 99.33% |
| Rule or data exceptions | blocker rows | 307 | 46,056 | 0.67% |

The 1,874 permission records are generated only for ways that reached complete
governed attribute resolution. They must not be described as the number of
ways whose permissions alone are complete.

## 10. Resolver Results

### Blockers by attribute

| Attribute | Blocker rows |
|---|---:|
| `maxspeed` | 23,135 |
| `lanes` | 22,656 |
| permissions | 264 |
| `oneway` | 1 |

### Failure-code definitions and results

The normative requirements are in
`05_src/traffic_simulation/specifications/02_resolver_specification.md`.

| Code | Formal meaning in this run | Trigger condition | Attribute | Severity | Rows | Required response |
|---|---|---|---|---|---:|---|
| RS003 | Required attribute unresolved | A retained way lacks an adopted required value after allowed rules | `lanes`, `maxspeed` | formal blocker | 45,771 | provide governed evidence or an eligible rule |
| RS007 | Reverse oneway transformation absent | `oneway=-1` requires a direction-safe transformation not yet implemented | `oneway` | formal blocker | 1 | implement and fixture-test the full transformation |
| RS008 | Directional lane allocation unresolved | directional lane encoding is incomplete, conflicting, or cannot be allocated safely | `lanes`, permissions | formal blocker | 82 | specify and fixture-test allocation rules |
| RS009 | Unsupported access semantics | a present OSM access key/value or conditional/lane form has no governed interpretation | permissions | formal blocker | 202 | add an explicit decision-table rule and fixture |

The code assignment follows `_resolver_failure()` in the v15 Resolver. RS010
would represent a typemap-intersection error but did not occur in this run.

### Rule and data exceptions

| Attribute and state | Rows |
|---|---:|
| permissions, unresolved | 264 |
| `maxspeed`, valid but unsupported | 22 |
| `lanes`, valid but unsupported | 19 |
| `oneway`, valid but unsupported | 1 |
| `lanes`, conflict | 1 |

### Permission exceptions by exact Resolver cause

Each permission blocker in this run belongs to one distinct way, so `rows` and
`distinct ways` are equal in this table.

| Resolver cause | Rows | Distinct ways | Required specification status |
|---|---:|---:|---|
| Unsupported `hgv:conditional` | 79 | 79 | conditional parser and policy required |
| Unsupported `motorcycle` | 74 | 74 | governed class rule and fixture required |
| Bidirectional lane allocation unresolved | 62 | 62 | directional allocation specification required |
| Unsupported `motor_vehicle:conditional` | 9 | 9 | conditional parser and policy required |
| Unsupported `psv` | 9 | 9 | class-mapping policy required |
| Unsupported `goods:conditional` with `vehicle:conditional` | 7 | 7 | conditional precedence policy required |
| `access=private` | 7 | 7 | inclusion policy decision required |
| Unsupported `goods` with `motor_vehicle:conditional` | 3 | 3 | precedence and conditional policy required |
| Unsupported `goods` with `vehicle:conditional` | 3 | 3 | precedence and conditional policy required |
| Unsupported `psv:lanes` | 3 | 3 | lane-specific class policy required |
| `access=destination` | 3 | 3 | inclusion policy decision required |
| `hgv=destination` | 3 | 3 | freight-class policy decision required |
| Unsupported `goods:conditional` | 1 | 1 | conditional parser and policy required |
| `access=permit` | 1 | 1 | inclusion policy decision required |
| Total | 264 | 264 | unresolved |

No item in this table authorizes a one-off OSM edit. Repeated causes must become
versioned decision-table rules and representative fixtures.

### Oneway decisions

The report-local rule IDs below cross-reference the v15 configuration keys.
They organize this evidence record; they do not create a second normative
policy.

| Report rule | Config condition | Result | Ways | Rate |
|---|---|---|---:|---:|
| ONEWAY-01 | explicit `oneway=yes/no` | adopt explicit value | 6,455 | 24.62% |
| ONEWAY-02 | missing explicit value and `junction=roundabout` | derive `yes` before ordinary-road handling | 0 observed | 0.00% |
| ONEWAY-03 | missing explicit value and `highway=motorway` | derive `yes` before ordinary-road handling | 0 observed | 0.00% |
| ONEWAY-04 | ordinary road after explicit and implicit checks | derive and materialize `no` | 19,764 | 75.38% |
| ONEWAY-05 | explicit `oneway=-1` | stop pending direction-safe transformation | 1 | 0.004% |

No missing-tag roundabout or motorway case occurred in this run; all 19,764
derived states used the ordinary-road bidirectional rule. The expected
`oneway=-1` transformation must update way direction and every
direction-dependent lane/access tag consistently; v15 deliberately does not
perform a partial node-order reversal.

## 11. Artifact Manifest and Publication Check

| Artifact | SHA-256 |
|---|---|
| Road attribute audit CSV | `2b1c40e6877817303507638437bf621a41b5a0b461976cc99d4cdbac4965671b` |
| Permission expectations JSON | `f80d8efe575b6bc44e2a8f12b1264d70f954d6ff8d0d8f8fe3216628f578975f` |
| Imputation summary JSON | `402e2d2d756a86ca93200693ec3a4c5ae6ce3783c4140b49804f52ffba688cc7` |
| Resolver failure report JSON | `da5f70cfa936c2b651c1ccd24922497fadd2869fffb6083a0097c647f93068cb` |
| Resolver exception queue CSV | `89a0edc656244619dd81e2dc53ddd1b6c6d0abc2650dab7604de110ff7cad858` |
| Dry-run summary JSON | `da3ef6d95dbcd5152532b780938c93b8437fbda4fb073a7f8b63eee7e289f102` |

Observed failure-publication state:

- the requested normalized OSM path does not exist;
- no Resolver `.part` file remains under the processed-data tree;
- the structural output directory contains no prior successful file that could
  have been overwritten;
- the audit, incomplete permission artifact, imputation summary and failure
  report were retained; and
- the failure report declares `partial_outputs_published=false`.

The artifacts are held in Git-ignored local processed-data paths. Their hashes
detect modification but do not guarantee long-term availability. No external
artifact repository or retention period is registered yet. Formal evidence
therefore requires either durable artifact storage or a manifest-driven,
independently tested regeneration procedure.

## 12. Implementation Finding

The first full attempt exposed quadratic XML removal: excluded ways were
removed individually from a root containing approximately 1.7 million nodes.
The Resolver now collects excluded ways and relations and filters the root
once.

This is a qualitative implementation finding, not a performance benchmark.
The interrupted earlier attempt had no preregistered timeout, repeated runs,
peak-memory measurement, immutable source commit, or runtime manifest.
Consequently this record makes no quantitative speedup claim. Fixture tests
verify exclusion semantics, while a separate benchmark protocol would be
needed to report wall-time or memory improvement.

## 13. Limitations

1. The exact dirty source tree used by the run is not represented by one Git
   commit.
2. The locally built analysis image has an immutable local image ID but no
   recorded registry digest.
3. Start and end timestamps were reconstructed from file metadata rather than
   emitted by the Resolver.
4. The closure procedure is now hash-reproducible, but the ID set and large
   artifacts remain local and Git-ignored.
5. The Dry Run candidate population includes the BBOX envelope and 16 closure
   support ways; it is not the final N03-clipped SUMO subgraph.
6. Relation member completeness was checked, but semantic correctness of all
   581 retained restrictions has not been manually or externally validated;
   three `type=restriction:bus` relations were outside the executed v15 scope.
7. Criticality, evidence availability and structural placeholders were not
   applied, so the 45,749 bulk missing rows are a pre-classification result.
8. Passing schemas proves artifact structure, not correctness of the unresolved
   permission semantics or eligibility for simulation.

## 14. Ordered Next Actions

1. Implement the schema and classifier defined by
   `attribute_criticality_and_evidence_specification.md`; the classification
   vocabulary and decision order are now specified, but no production
   classification is authorized.
2. Add fixtures that verify complete criticality coverage, precedence,
   profile changes, promotion and failure behavior.
3. Add `type=restriction:bus` to the governed relation-scope decision,
   regenerate closure, and fixture-test its three retained restrictions before
   applying criticality to the registered real data.
4. Accept and record the new candidate population, then generate complete
   real-data criticality coverage from the new input hash. Do not patch the
   v15 26,220-way population.
5. Resolve the specification-required entries in
   `resolver_exception_decision_table.yml`, which assigns all 307 v15
   attribute exceptions to mutually exclusive frequency-ranked categories.
6. Add representative fixtures containing source tags, expected state,
   expected value and expected RS code for every adopted rule.
7. Group the newly generated classification by road class, directionality,
   criticality and evidence availability.
8. Define separate evidence hierarchies for missing `maxspeed` and missing
   `lanes`; do not treat them as one generic imputation problem.
9. Integrate relation closure and the N03 boundary/support-element decision
   into `build_sumo_network.py prepare`, with a generated manifest rather than
   relying on manually retained intermediate files.
10. Rerun the full Resolver input and automatically compare blocker rows,
   distinct blocked ways, attributes and RS codes against this baseline.
11. Implement a machine-readable Resolver and formal-build readiness decision;
   zero Resolver blockers alone must not imply formal readiness.
12. Continue the permission materializer only on synthetic, fully resolved
    fixtures until the registered production permission artifact is complete.
13. Execute formal `netconvert` only after every
    `formal_build_input_ready` requirement passes.

## 15. Next-Run Comparison Baseline

Every later full run must compare its result with this baseline. A resolved
blocker, a new blocker and a blocker whose code or resolution method changes
are different outcomes and must be reported separately.

| Metric | v15 baseline | Next run | Difference |
|---|---:|---:|---:|
| Governed candidate ways | 26,220 | pending | pending |
| Ways with blockers | 24,346 | pending | pending |
| Blocker rows | 46,056 | pending | pending |
| Bulk missing rows | 45,749 | pending | pending |
| Rule/data exception rows | 307 | pending | pending |
| Permission blockers | 264 | pending | pending |
| Bidirectional lane-allocation blockers | 62 | pending | pending |
| Unsupported `maxspeed` expressions | 22 | pending | pending |
| Unsupported lane expressions | 19 | pending | pending |
| Reverse oneway blockers | 1 | pending | pending |
| Conflict rows | 1 | pending | pending |

The comparison artifact must contain at least:

```text
resolved_since_previous_run
new_since_previous_run
unchanged_since_previous_run
failure_code_changed
resolution_method_changed
```
