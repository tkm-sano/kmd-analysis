<a id="failure-taxonomy"></a>

# 不具合 Taxonomy

All failures are stable machine-readable codes. Messages may add context but MUST NOT replace codes.

<a id="resolver"></a>

## 属性解決器

| Code | 検出 | Formal blocker | Retained output | 復旧 |
|---|---|---|---|---|
| RS001 | invalid root, missing/duplicate way or tag ID | はい | failure/audit | repair input |
| RS002 | unknown or ungoverned highway classification | はい | 監査 | govern or exclude explicitly |
| RS003 | required attribute unresolved | はい | audit/expectation complete=false | provide governed value |
| RS004 | state classification inconsistency | はい | 不具合 | fix resolver/schema |
| RS005 | prohibited imputation | はい | 監査 | remove placeholder/adopt evidence |
| RS006 | formal placeholder/stopping state | はい | 監査 | resolve all states |
| RS007 | `oneway=-1` unsupported | はい | 監査 | implement safe transform or exclude occurrence |
| RS008 | lane-list read-order ambiguity | はい | 監査 | correct directional lane tags |
| RS009 | Resolver lane-position convention mismatch | はい | audit/failure | restore leftmost-first Resolver indexing |
| RS010 | unsupported access semantics | はい | 監査 | add versioned rule/evidence |
| RS011 | permission composition mismatch | はい | 不具合 | fix resolver/config |
| RS012 | expectation schema/incompleteness | はい | 不具合 | regenerate the governed artifact |
| RS013 | unsafe output path/write | はい | 不具合 | use new governed paths |
| RS014 | relation scope, closure or governed vehicle-restriction failure | はい | closure audit/failure | fix the relation-scope policy or closure |

CLI boundary mapping for the next Resolver version is fixed as follows:
malformed/missing OSM, invalid node/way/tag identity and XML parse failure map
to `RS001`; invalid config or typemap state maps to `RS004`; permission
artifact/schema/accounting failure maps to `RS012`; path collision, existing
output, staging/publication or filesystem write failure maps to `RS013`; and
relation identity, scope or closure failure maps to `RS014`. Governed
attribute blockers retain their more specific `RS003`, `RS007`, `RS008`,
`RS009`, `RS010` or `RS011` codes in both the incomplete permission artifact
and CLI failure report. Executed v15 artifacts retain their original codes and
are not rewritten; implementation and fixtures MUST migrate together before a
new production run.

<a id="attribute-criticality-and-evidence"></a>

## 属性重要度 ・ 根拠

| Code | 検出 | Formal blocker | 復旧 |
|---|---|---|---|
| AC001 | retained tuple missing | はい | generate complete tuple coverage |
| AC002 | tuple duplicated | はい | enforce unique tuple identity |
| AC003 | unknown rule ID | はい | register or correct the rule |
| AC004 | contradictory predicates | はい | repair governed predicate artifacts |
| AC005 | evidence not applicable | はい | provide direction/segment/time/vehicle-compatible evidence |
| AC006 | unresolved evidence conflict | はい | apply a registered conflict rule or stop |
| AC007 | required review incomplete | はい | complete review provenance |
| AC008 | structural-placeholder gate failed | はい | remove placeholder or satisfy every gate |
| AC009 | source, policy or classification hash mismatch | はい | regenerate from aligned inputs |
| AC010 | invalid action/state/review combination | はい | emit a permitted state transition |

<a id="permission-materializer"></a>

## 通行許可の具体化処理

| Code | 検出 | Retained output | 復旧 |
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

<a id="tls-review"></a>

## 信号制御の確認

| Code | 検出 | Formal blocker | 復旧 |
|---|---|---|---|
| TLS001 | permission-connection or reviewed-node hash mismatch | はい | restore inputs or start a new review |
| TLS002 | provisional TLS artifact selected as final input | はい | replace it with reviewed TLS input |
| TLS003 | controlled connection has no unique TLS/link assignment | はい | complete the reviewed mapping |
| TLS004 | link index is duplicated, negative or noncontiguous | はい | correct and re-review indices |
| TLS005 | phase-state length differs from controlled-link count | はい | correct and re-review the program |
| TLS006 | reviewed connection identity or permission differs from materialized input | はい | restore exact connections and re-review |
| TLS007 | node, edge, connection or permission hash changed after review | はい | mark invalidated and re-review |
| TLS008 | reviewer, UTC time, evidence or decision record is incomplete | はい | complete review provenance |
| TLS009 | reviewed XML or manifest fails pinned XSD/schema | はい | repair the review artifact |
| TLS010 | unobserved timing is not labelled `initialized` | はい | correct timing provenance |

<a id="final-build"></a>

## 最終構築

| Code | 検出 | Formal blocker | 復旧 |
|---|---|---|---|
| BLD001 | formal build input readiness is false | はい | satisfy every input requirement |
| BLD002 | config ID, version, schema version or input hash mismatch | はい | align registered artifacts |
| BLD003 | readiness dependency graph is cyclic or mispartitioned | はい | repair governed gate configuration |
| BLD004 | changed upstream hash did not invalidate a dependent state | はい | invalidate and recreate dependents |
| BLD005 | structural and formal profiles share an output identity/path | はい | separate run IDs and directories |
| BLD006 | container digest or required tool/environment version mismatch | はい | run the pinned environment |
| BLD007 | ordered argv, working directory or required command provenance is absent | はい | regenerate the manifest |
| BLD008 | a prohibited formal `netconvert` option is enabled | はい | use the governed formal options |
| BLD009 | an input fails its pinned schema or XSD | はい | repair the owning input |
| BLD010 | `netconvert` exits nonzero or output publication is non-atomic | はい | retain logs, repair inputs and rerun |
| BLD011 | target formal output already exists | はい | allocate a new governed run ID |
| BLD012 | repeated identical semantic inputs yield different semantic content | はい | investigate environment/canonicalizer |
| BLD013 | raw or semantic digest cannot be generated/verified | はい | repair digest generation |
| BLD014 | failed run leaves a success manifest, accepted network or partial success output | はい | clean publication logic and rerun |

<a id="post-build-audit"></a>

## 構築後監査

| Code | 検出 | Formal blocker | 復旧 |
|---|---|---|---|
| PA001 | final network fails pinned XSD | はい | fix governed input and rebuild |
| PA002 | pinned SUMO cannot load final network | はい | fix governed input and rebuild |
| PA003 | expected external edge/lane lacks exact lineage | はい | repair provenance and rebuild |
| PA004 | expected lane/connection is missing | はい | repair governed inputs and rebuild |
| PA005 | unexpected lane/connection exists | はい | repair governed inputs and rebuild |
| PA006 | lane/connection cannot be mapped to an expectation | はい | repair provenance and rebuild |
| PA007 | effective lane/connection permission differs from expectation | はい | repair materialized input and rebuild |
| PA008 | unmanaged vClass exists | はい | fix permission governance and rebuild |
| PA009 | unexpected directed edge exists | はい | fix direction governance and rebuild |
| PA010 | TLS ID, link, connection or phase state differs from review | はい | repair reviewed inputs and rebuild |
| PA011 | warning is blocking or unclassified | はい | classify through governed review or fix cause |
| PA012 | removed/excluded edge has no approved input action | はい | reconcile exclusion and rebuild |
| PA013 | structural threshold is unregistered or fails | はい | preregister or improve governed input |
| PA014 | audit schema/accounting/acceptance logic is inconsistent | はい | fix auditor and rerun audit |
| PA015 | identical inputs and auditor yield different audit results | はい | fix auditor determinism |

Every code above and in the Resolver/Materializer tables has the mandatory negative fixture ID `<code>-NEG-001` defined by `07_fixture_specification.md`. No failure code permits an automatic patch of final `net.xml`.
