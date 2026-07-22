# Failure Taxonomy

All failures are stable machine-readable codes. Messages may add context but MUST NOT replace codes.

## Resolver

| Code | Detection | Formal blocker | Retained output | Recovery |
|---|---|---|---|---|
| RS001 | invalid root, missing/duplicate way or tag ID | yes | failure/audit | repair input |
| RS002 | unknown or ungoverned highway classification | yes | audit | govern or exclude explicitly |
| RS003 | required attribute unresolved | yes | audit/expectation complete=false | provide governed value |
| RS004 | state classification inconsistency | yes | failure | fix resolver/schema |
| RS005 | prohibited imputation | yes | audit | remove placeholder/adopt evidence |
| RS006 | formal placeholder/stopping state | yes | audit | resolve all states |
| RS007 | `oneway=-1` unsupported | yes | audit | implement safe transform or exclude occurrence |
| RS008 | lane-order ambiguity | yes | audit | correct directional lane tags |
| RS009 | unsupported access semantics | yes | audit | add versioned rule/evidence |
| RS010 | permission composition mismatch | yes | failure | fix resolver/config |
| RS011 | expectation schema/incompleteness | yes | failure | regenerate v2 artifact |
| RS012 | unsafe output path/write | yes | failure | use new governed paths |

## Permission Materializer

| Code | Detection | Retained output | Recovery |
|---|---|---|---|
| PM001 | expectation schema invalid/incomplete | failure report | regenerate resolver output |
| PM002 | config/version mismatch | failure report | align artifacts |
| PM003 | input hash mismatch | failure report | restore registered input |
| PM004 | plain XML/XSD failure | failure report | repair provisional build |
| PM005 | governed universe/type mismatch | failure report | align config/typemap |
| PM006 | missing/duplicate edge provenance | audit/failure | regenerate lineage |
| PM007 | source node lineage mismatch | audit/failure | fix provisional builder |
| PM008 | zero/ambiguous direction interval | audit/failure | provide exact lineage |
| PM009 | coordinate-only formal mapping attempted | failure report | provide exact lineage |
| PM010 | missing/duplicate lane index | audit/failure | repair plain edge |
| PM011 | noncontiguous lane indices | audit/failure | repair plain edge |
| PM012 | lane-count disagreement | audit/failure | resolve source/build discrepancy |
| PM013 | lane maps zero or multiple times | audit/failure | fix mapping inputs |
| PM014 | empty/unknown permission token | audit/failure | use governed tokens |
| PM015 | `allow` and `disallow` both present | audit/failure | canonicalize upstream input |
| PM016 | unmanaged provisional permission | audit/failure | remove or govern class |
| PM017 | expected set exceeds baseline or mismatch | audit/failure | fix expectation/type |
| PM018 | empty-edge removal inconsistency | audit/failure | apply fixed removal rule |
| PM019 | incomplete/duplicate connection identity | audit/failure | make lane connection explicit |
| PM020 | connection references removed/missing lane | audit/failure | remove/review connection |
| PM021 | connection permission mismatch | audit/failure | fix expected intersection |
| PM022 | missing turn synthesized | audit/failure | preserve provisional topology |
| PM023 | unsupported connection-file element/reference | audit/failure | govern or remove element |
| PM024 | materializer attempts final TLS decision | failure report | route to TLS Review |
| PM025 | nondeterministic serialization | failure report | fix serializer |
| PM026 | output exists or unsafe path | failure report | use new output path |
| PM027 | partial success output remains | failure report | enforce atomic cleanup |
| PM028 | audit accounting/schema mismatch | failure report | fix audit generator |

## TLS Review

| Code | Detection | Formal blocker | Recovery |
|---|---|---|---|
| TLS001 | permission-connection or reviewed-node hash mismatch | yes | restore inputs or start a new review |
| TLS002 | provisional TLS artifact selected as final input | yes | replace it with reviewed TLS input |
| TLS003 | controlled connection has no unique TLS/link assignment | yes | complete the reviewed mapping |
| TLS004 | link index is duplicated, negative or noncontiguous | yes | correct and re-review indices |
| TLS005 | phase-state length differs from controlled-link count | yes | correct and re-review the program |
| TLS006 | reviewed connection identity or permission differs from materialized input | yes | restore exact connections and re-review |
| TLS007 | node, edge, connection or permission hash changed after review | yes | mark invalidated and re-review |
| TLS008 | reviewer, UTC time, evidence or decision record is incomplete | yes | complete review provenance |
| TLS009 | reviewed XML or manifest fails pinned XSD/schema | yes | repair the review artifact |
| TLS010 | unobserved timing is not labelled `initialized` | yes | correct timing provenance |

## Final Build

| Code | Detection | Formal blocker | Recovery |
|---|---|---|---|
| BLD001 | formal build input readiness is false | yes | satisfy every input requirement |
| BLD002 | config ID, version, schema version or input hash mismatch | yes | align registered artifacts |
| BLD003 | readiness dependency graph is cyclic or mispartitioned | yes | repair governed gate configuration |
| BLD004 | changed upstream hash did not invalidate a dependent state | yes | invalidate and recreate dependents |
| BLD005 | structural and formal profiles share an output identity/path | yes | separate run IDs and directories |
| BLD006 | container digest or required tool/environment version mismatch | yes | run the pinned environment |
| BLD007 | ordered argv, working directory or required command provenance is absent | yes | regenerate the manifest |
| BLD008 | a prohibited formal `netconvert` option is enabled | yes | use the governed formal options |
| BLD009 | an input fails its pinned schema or XSD | yes | repair the owning input |
| BLD010 | `netconvert` exits nonzero or output publication is non-atomic | yes | retain logs, repair inputs and rerun |
| BLD011 | target formal output already exists | yes | allocate a new governed run ID |
| BLD012 | repeated identical semantic inputs yield different semantic content | yes | investigate environment/canonicalizer |
| BLD013 | raw or semantic digest cannot be generated/verified | yes | repair digest generation |
| BLD014 | failed run leaves a success manifest, accepted network or partial success output | yes | clean publication logic and rerun |

## Post-build Audit

| Code | Detection | Formal blocker | Recovery |
|---|---|---|---|
| PA001 | final network fails pinned XSD | yes | fix governed input and rebuild |
| PA002 | pinned SUMO cannot load final network | yes | fix governed input and rebuild |
| PA003 | expected external edge/lane lacks exact lineage | yes | repair provenance and rebuild |
| PA004 | expected lane/connection is missing | yes | repair governed inputs and rebuild |
| PA005 | unexpected lane/connection exists | yes | repair governed inputs and rebuild |
| PA006 | lane/connection cannot be mapped to an expectation | yes | repair provenance and rebuild |
| PA007 | effective lane/connection permission differs from expectation | yes | repair materialized input and rebuild |
| PA008 | unmanaged vClass exists | yes | fix permission governance and rebuild |
| PA009 | unexpected directed edge exists | yes | fix direction governance and rebuild |
| PA010 | TLS ID, link, connection or phase state differs from review | yes | repair reviewed inputs and rebuild |
| PA011 | warning is blocking or unclassified | yes | classify through governed review or fix cause |
| PA012 | removed/excluded edge has no approved input action | yes | reconcile exclusion and rebuild |
| PA013 | structural threshold is unregistered or fails | yes | preregister or improve governed input |
| PA014 | audit schema/accounting/acceptance logic is inconsistent | yes | fix auditor and rerun audit |
| PA015 | identical inputs and auditor yield different audit results | yes | fix auditor determinism |

Every code above and in the Resolver/Materializer tables has the mandatory negative fixture ID `<code>-NEG-001` defined by `07_fixture_specification.md`. No failure code permits an automatic patch of final `net.xml`.
