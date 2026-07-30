# 属性別Criticality・証拠仕様書

## 文書の位置付け

本書は
[`attribute_criticality_and_evidence_specification.md`](../attribute_criticality_and_evidence_specification.md)
の日本語版である。rule ID、level、action、value state、機械可読フィールド名は
英語正本と同一である。差異がある場合は機械可読設定と英語正本を優先し、
日本語版を修正する。日本語版だけで分類規則や許容処理を変更してはならない。

## 目的

本仕様は、Resolverがstructural値を適用する前に、欠損した`lanes`と
`maxspeed`をどのように分類するかを統制する。大田区v15 Dry Runで観測した
45,749件のbulk missingを、すべて同じ許容可能な分類として扱うことを防ぐ。

Criticalityは属性別である。一つの明示されたnetwork profileにおいて、一つの
属性へ根拠のない値を使用した場合の影響を表す。OSM way全体の一般的重要度
scoreではなく、道路の社会的・経済的重要性も意味しない。

本仕様は値そのものを許可しない。分類contract、証拠順位、許容action、
実装とfixture合格後に限り分類を利用できる条件を定義する。

## 観測件数の来歴

本仕様に記載する件数は、設定定数ではなくv15の履歴観測値である。正本は
`03_data/metadata/acquisition/20260723_ota_ward_v15_resolver_dry_run.md`であり、
同文書がrun入力、config ID、各SHA-256、出力artifact hashを記録する。

| 観測値 | 集計単位と計算 |
|---|---|
| governed candidate 26,220件 | v15 relation closure後に保持したdistinct way ID |
| blocker 46,056件 | governed decisionが停止状態であるaudit row |
| bulk missing 45,749件 | source `lanes`または`maxspeed`が真に欠損したblocker row |
| rule・data exception 307件 | bulk missing以外のblocker row、すなわち`46,056 - 45,749` |
| 除外bus restriction 3件 | 全入力で`type=restriction:bus`かつgoverned turn意味を持つdistinct relation |

次の受理済みclosureから件数を再生成しなければならない。これらをacceptance
logicへ固定値として埋め込んだり、productionの期待総数として扱ってはならない。

## 統制原則

1. 分類単位は一つの`(osm_way_id, attribute, profile)` tupleとする。
2. `lanes`と`maxspeed`は独立に分類しなければならない。
3. 低criticalityの分類を、より影響の大きいprofileへ流用してはならない。
4. 明示的または権威ある証拠を、低順位のstructural ruleで上書きしては
   ならない。
5. structural placeholderは`structural` profileの適格levelでだけ許容し、
   formal研究結果には使用してはならない。
6. 証拠欠損、predicate矛盾、不完全な分類被覆は停止状態とする。
7. 分類と値解決は別の判断である。criticality level自体は属性値を与えない。
8. calibration edgeまたはdelivery-route edgeの特定などにより後から昇格した
   場合、以前の分類とすべての依存artifactを無効化する。

## 分析profile

| Profile | 許容用途 | Criticality上の意味 |
|---|---|---|
| `structural` | topology、connectivity、permission、可視化の確認 | 属性別levelが許可する場合だけ承認済みplaceholderを検討できる。travel time、capacity、deliveryに関する結論は禁止する |
| `formal` | 較正済み交通、配送評価、最適化比較 | structural placeholderを禁止し、保持する全属性に統制済み証拠またはformal仕様で許可された検証済みmodelを必要とする |

networkを`structural`から`formal`へ変更する場合は再分類が必要である。
structural分類を自動昇格してはならない。

## 母集団とSubgraph role

分類母集団は、relation closure受入gateに合格したOSM入力内のgoverned
candidate way集合とする。地域PBFやclosure前BBOX extractを直接母集団にしない。
relation-closed入力SHA-256が変われば、新しいclassification runを必要とする。

全candidate wayは、最終SUMOネットワークへ残さないwayを含め、次の
`subgraph_role`を正確に一つ持つ。

```text
final
topology_support
excluded
```

複数booleanによるrole表現は禁止する。`excluded` wayもartifactへ残し、lanesを
`L0`、maxspeedを`S0`、`resolution_action=exclude`、
`value_state=excluded`、`resolved_value=null`とする。`topology_support`は
relation、connection、変換へ影響し得るため分類対象とし、基本levelをstructuralで
`L1/S1`、formalで`L2/S2`とする。高criticality predicateに該当すれば
`L3/S3`へ昇格する。

## Tuple・Record・改訂contract

tupleは`(osm_way_id, attribute, profile)`とする。way IDは正の10進文字列、
attributeは`lanes`または`maxspeed`、profileは`structural`または`formal`とする。
一artifactには一profileだけを含め、excluded wayを含む各tupleにactive recordを
正確に一つ持つ。

安定record IDは次の形式とする。

```text
acr:<osm_way_id>:<attribute>:<profile>
```

recordはway IDを数値昇順に並べ、同じwayでは`lanes`、`maxspeed`の順にする。
classificationとresolutionは同一record内の別objectとする。

```json
{
  "classification_record_id": "acr:123456789:lanes:formal",
  "osm_way_id": "123456789",
  "attribute": "lanes",
  "profile": "formal",
  "classification": {
    "criticality_level": "L2",
    "selected_rule_id": "LANE-CRIT-006",
    "matched_rule_ids": ["LANE-CRIT-006"]
  },
  "resolution": {
    "resolution_action": "stop_unresolved",
    "resolution_rule_id": null,
    "value_state": "missing",
    "resolved_value": null
  }
}
```

resolution objectは構造化した`evidence_requirement`、`evidence_candidates`、
`selected_evidence_id`、`rejected_evidence_ids`、
`conflict_resolution_rule_id`、単位、review来歴、停止codeも記録する。各候補は
source、値、単位、方向、segment、vehicle scope、期間、license、source hash、
matching confidenceを持つ。`evidence_requirement`は要否、統制rule、最低権威
水準、説明を分離し、`L3`と`S3`では必須、それ未満では不要を明示する。
confidenceのscale、threshold、同率処理をpolicyで
固定するまで値選択へ使わない。

artifactはimmutableなrun snapshotとする。判断変更時は同じ
`classification_record_id`で`record_revision`を増加させ、新しい
`record_sha256`、以前の`supersedes_record_sha256`、統制済み
`revision_reason_code`を持つ新snapshotを作る。旧snapshotを保持し、一snapshotに
同じtupleの複数active revisionを含めない。

### Canonical record hashと順序

`record_sha256`は、recordから`record_sha256`自身だけを除外し、RFC 8785 JSON
Canonicalization Schemeでcanonical化したUTF-8 byte列のSHA-256とする。
object key、whitespace、数値表現はRFC 8785に従い、array順序は保持する。
明示的`null`とfield省略は異なるものとして扱い、schemaが必須とするfieldは
hash計算時にも省略しない。

recordは、数値としての`osm_way_id`昇順、`lanes`から`maxspeed`、
`structural`から`formal`、最後に`record_revision`昇順で並べる。現在のartifactは
単一profileであるが、将来互換性のためprofile順序をcontractに残す。

### Semantic validation

JSON Schemaは局所的な形式と状態機械を検査する。登録済み
`validate_attribute_classification.py`は、cross-record failureを`ACV` codeで
可能な限り収集する。派生record ID、artifact・record profile一致、tupleと
evidence IDの一意性、母集団被覆、wayごとの両属性、
`road_criticality.classification_rule_priority`に基づくrule選択、evidence参照、
完了状態、明示的に渡されたrevision履歴、RFC 8785 hash、canonical順序、
参照fileのSHA-256を検査する。
各recordの`source_artifact_sha256`はtop-level predicate artifact hashと一致し、
`classification_config_sha256`はtop-level classification-policy hashと一致
しなければならない。

validatorはrevisionやevidence sourceをdirectoryから暗黙探索しない。top-level
以外のsourceはsource indexへ明示登録し、predecessor snapshotはhistoryとして
渡す。これにより、同名だが無関係なfileの誤採用を防ぐ。
CLIは検出したfailureを一つで停止せず、`valid`、`errors`、`ACV` code、
JSON Pointer、message、expected、actualを持つ一つのJSON結果として返す。

## Predicate artifact

classifierは`attribute_classification_predicates.json`を消費し、OSM、route、
calibration設定、reviewからpredicateを直接再調査してはならない。predicate
artifactは母集団wayごとに正確に一recordを持ち、完全な母集団・source hash、
排他的`subgraph_role`と、英語正本に列挙した道路構造、lane・speed意味、
accepted delivery route、sensitivity昇格の各predicateを保存する。

全predicate値はsource artifact type・SHA-256、source record locator、
derivation rule IDを必要とする。根拠のないbooleanは禁止する。

`subgraph_role_evidence`はbooleanではなくcategory evidenceであり、
`asserted_role`と同じsource provenanceを記録する。semantic validationは
`asserted_role`と`subgraph_role`の一致を要求する。
`topology_support_reason`は常時存在し、`topology_support`では非空文字列、
`final`と`excluded`では`null`とする。

### Predicate Generatorの契約

`generate_attribute_classification_predicates.py`は、relation closure済みOSM
XML、`predicate_source_registry.schema.json`に適合するsource registry、
固定済み`sumo_network.yml` policyの三つを明示入力とする。統制対象母集団は、
`highway` tagを持つ全OSM wayと、`topology_support`として明示登録した
非highway wayだけで構成する。role registryはこの母集団を重複なく完全に
被覆しなければならない。

bridge、tunnel、grade separation、lane semantics、speed semanticsのpredicateは
OSM tagから決定論的に導出する。calibration、independent validation、
major junction、accepted delivery route、sensitivityのpredicateは、
hash登録された外部sourceだけから得る。trueとfalseの両方にsource provenanceを
保持する。review済みoverrideは、そのsource、locator、derivation rule IDを
登録した場合に限り、一つの導出値を置換できる。

生成はfail-closedである。未受理母集団、role被覆不足、母集団外の外部ID、
source欠損・hash不一致、schema・semantic検証失敗、既存output pathを検出すると
停止する。書込みはatomicで、recordはOSM way IDの数値昇順とする。登録済み
実データにはpopulation acceptance artifactとconfig version 16以降を追加で
要求するため、v15 Dry Runはproduction入力にできない。synthetic fixtureは
`synthetic_fixture` scopeを明示し、実データ受理の証拠にはならない。

## 分類前のPredicate整合性検証

検査順序は、schema、artifact・source hash、way ID重複、母集団完全被覆、role
enum、role矛盾、calibration・validation排他性、道路構造矛盾、属性別predicate、
classification ruleとする。

次の場合はfirst-match前に停止する。

- `excluded`とcalibration、validation、accepted route、sensitivity昇格または
  major-junction状態の併存
- `topology_support`に統制済みsupport reasonがない
- 同じwayがcalibrationとindependent validationの両方
- 同じwayがbridgeとtunnelの両方で、統制済みway分割または個別reviewがない

bridgeとtunnelの併存は、way splitまたはreview済み例外により正当になり得るため、
JSON Schemaで無条件の相互排他にはしない。predicate source registryは、この
裁定をhash-linkedなreview済みoverrideとして明示する。その裁定がなければ、
semantic validatorは推測せず停止する。

directional laneとbus・PSV lane意味は併存できる。属性別predicateが異なる場合は、
lanesとmaxspeedで異なるlevelを許容する。

## Lane criticality

Lane criticalityは、capacity、方向配分、lane change、junction connection、
flowへの影響を扱う。道路の幾何学的重要性を意味しない。

| Level | 機械的な意味 | 許容される解決 |
|---|---|---|
| `L0` | 統制済みfinal subgraph判断でwayを除外し、materializationを必要とするtopology-support elementでもない | `excluded`を記録し、lane値を生成しない |
| `L1` | 選択profileが`structural`で、`L3` predicateがなく、許容されたstructural確認だけに値を使用する | 来歴とsensitivity状態を伴う承認済みstructural ruleを適用できる |
| `L2` | lane値がformalのcapacity、flow、connection、delivery評価へ参加するが、`L3` predicateはない | 明示OSM、公的証拠、review済み証拠、許可された検証済みmodelのいずれかが必要 |
| `L3` | calibration・validation segment、review済み主要junction approach、複雑な方向・lane意味を持つway、または採用済みdelivery route・感度分析により昇格したway | 自動placeholder禁止。属性固有の証拠と必要な人手reviewを必須とする |

### Lane分類順序

predicate整合性検証の合格後、次の順序で最初に一致したruleがlevelを決定する。

| Rule ID | Predicate | Level |
|---|---|---|
| `LANE-CRIT-001` | `subgraph_role=excluded` | `L0` |
| `LANE-CRIT-002` | calibrationまたはindependent-validation segment | `L3` |
| `LANE-CRIT-003` | lane数がgoverned connectionへ影響するreview済みmajor-junction approach、bridge、tunnel、grade-separated structure | `L3` |
| `LANE-CRIT-004` | directional、reversible、tidal-flow、turn-lane、bus-lane、PSV-lane、conflictするlane tagの解釈が必要 | `L3` |
| `LANE-CRIT-005` | accepted delivery routeまたは登録済みsensitivity結果がwayを昇格 | `L3` |
| `LANE-CRIT-006` | profileが`formal` | `L2` |
| `LANE-CRIT-007` | profileが`structural`で上記ruleに一致しない | `L1` |

`major junction approach`や`topology support`などのpredicateには別の統制済み
artifactが必要である。名称または道路classだけから暗黙に設定してはならない。
post-buildまたはrouteに基づく昇格は、formal利用前に以前の分類を無効化する。

## Maxspeed criticality

Maxspeed criticalityは、自由流travel time、route choice、arrival time、
delivery feasibility、energy計算への影響を扱う。観測交通速度を法的速度制限
として扱わない。

| Level | 機械的な意味 | 許容される解決 |
|---|---|---|
| `S0` | governed final subgraph判断でwayを除外し、保持routeにも不要 | `excluded`を記録し、speed値を生成しない |
| `S1` | profileが`structural`で、報告対象travel-time、capacity、energy、delivery結果にspeedを使用せず、`S3` predicateがない | 承認済みstructural ruleを適用し、non-formalと表示できる |
| `S2` | speedがformal routing、travel-time、energy、delivery評価へ参加するが、`S3` predicateがない | 法的・行政的証拠、対応済み明示OSM証拠、許可された検証済みmodelが必要 |
| `S3` | calibration・validation segment、conditional・directional・variable speed意味を持つway、または採用route・感度分析で昇格したway | 自動placeholder禁止。時刻・方向・vehicleに適合する証拠が必要 |

### Maxspeed分類順序

| Rule ID | Predicate | Level |
|---|---|---|
| `SPEED-CRIT-001` | `subgraph_role=excluded` | `S0` |
| `SPEED-CRIT-002` | calibrationまたはindependent-validation segment | `S3` |
| `SPEED-CRIT-003` | directional、conditional、variable、vehicle-specific、advisory、multiple speed表現の解釈が必要 | `S3` |
| `SPEED-CRIT-004` | accepted delivery routeまたは登録済みsensitivity結果がwayを昇格 | `S3` |
| `SPEED-CRIT-005` | profileが`formal` | `S2` |
| `SPEED-CRIT-006` | profileが`structural`で上記ruleに一致しない | `S1` |

JARTICの観測旅行速度はcalibrationまたはvalidation証拠であり、`maxspeed`へ
変換してはならない。

## 証拠hierarchy

証拠は優先順位の前に適用可能性を評価する。別方向、別日、別vehicle class、
別segmentを参照する証拠は、適用可能な証拠と競合させない。

### Lanes

1. 整合する明示的な方向別OSM lane tag
2. 方向配分が不要な場合の整合する明示的OSM総車線数
3. 方向・segment定義が適合する公的道路交通census lane field
4. 照合済みroad ledger証拠
5. 範囲限定しreviewした権威あるimagery
6. 選択profileで許可された事前登録・検証済みderivation model
7. `L1`だけで許可する承認済みstructural placeholder
8. unresolved

### Maxspeed

1. 日付、方向、vehicle scopeが適合する法的・行政的交通規制証拠
2. reference dateと意味が適合する対応済み明示OSM speed tag
3. 同じsegment・方向に対するreview済みpublic-authority証拠
4. road-state仮定を検証した日付付き法的導出
5. 選択profileで許可された事前登録・検証済みderivation model
6. `S1`だけで許可する承認済みstructural placeholder
7. unresolved

この番号は無条件の上書き順位ではない。conflictは、法的・行政的権威、
reference date、segment・方向match、属性定義、license適合性、match confidence
により解決する。解決できないconflictは停止する。

## Resolution actionと状態

Resolverは次のresolution actionだけを出力できる。

| Action | 意味 |
|---|---|
| `adopt_explicit` | 対応済みの明示source値を使用 |
| `derive_osm_rule` | 決定的なOSM意味ruleを適用 |
| `adopt_external_evidence` | hash登録済みで適用可能な外部値を使用 |
| `apply_governed_rule` | 事前登録済みのnon-placeholder derivationを適用 |
| `apply_structural_placeholder` | structural profileの`L1`または`S1`だけで適用 |
| `require_human_review` | 指定証拠がreviewされるまで停止 |
| `stop_unresolved` | 許容可能な値がないため停止 |
| `exclude` | 別途統制されたsubgraph判断により除外 |

対応するvalue stateは次のとおりである。

```text
explicit_osm
derived_osm_rule
authoritative_external
derived_validated_model
structural_placeholder
missing
unresolved
conflict
valid_but_unsupported
conditional
directionally_asymmetric
invalid
excluded
```

`resolved`だけでは値の由来が分からないため、有効なstateではない。

許容する組合せは次のとおりである。

| Resolution action | 許容value state | `resolved_value` | Review status |
|---|---|---|---|
| `adopt_explicit` | `explicit_osm` | 必須 | `machine_classified`または`reviewed` |
| `derive_osm_rule` | `derived_osm_rule` | 必須 | `machine_classified`または`reviewed` |
| `adopt_external_evidence` | `authoritative_external` | 必須 | `reviewed` |
| `apply_governed_rule` | `derived_validated_model` | 必須 | `machine_classified`または`reviewed` |
| `apply_structural_placeholder` | `structural_placeholder` | 必須 | `machine_classified`または`reviewed` |
| `require_human_review` | `missing`、`conflict`、`conditional`、`valid_but_unsupported`、`directionally_asymmetric` | `null` | `review_required` |
| `stop_unresolved` | `missing`、`unresolved`、`conflict`、`valid_but_unsupported`、`conditional`、`directionally_asymmetric`、`invalid` | `null` | `stopped` |
| `exclude` | `excluded` | `null` | `machine_classified` |

`invalidated`は現在のresolution statusとして使用しない。supersessionはrevision
metadataとimmutableな旧snapshotだけで表現する。`L0/S0`は`exclude`だけ、
`L1/S1`は全action、`L2/S2`と`L3/S3`はstructural placeholder以外を許容する。
採用済み`L3/S3`は必ず`reviewed`とする。

## Componentの責務

処理境界を次のように固定する。

```text
Predicate Generator
    -> classificationに必要な統制済み事実を生成する
Classifier
    -> criticality_level、selected_rule_id、matched_rule_idsを決定する
Resolver
    -> resolution action、value state、採用値、evidence、conflict結果、
       review状態、stop codeを決定する
Semantic Validator
    -> 統合immutable artifactとsource hashを検証する
```

Classifierは属性値を選択・補完せず、resolution actionも出力しない。Resolverは
Classifier結果、明示OSM値、登録済み外部証拠、許可済み検証model、
structural-placeholder ruleを入力とする。将来一つの実行entry pointへ統合する場合も、
object contractと判断責務は分離したままとする。

## Profile別必須artifact

| Artifact | 処理上の役割 | `structural` | `formal` |
|---|---|---|---|
| 完全なpredicate artifact | Classifier入力 | 必須 | 必須 |
| classification result | Classifier出力・Resolver入力 | 必須 | 必須 |
| external evidence artifact | Resolver入力 | 参照時に必須 | 参照時に必須 |
| structural-placeholder rule | Resolver入力 | 使用時だけ必須 | 禁止 |
| classification・resolution統合artifact | Resolver出力・Semantic Validator対象 | 必須 | 必須 |

## Resolution判断順序

Resolutionは、excluded role、適用可能な明示OSM値、決定的OSM意味rule、適用可能で
review済みの外部証拠、許可済み検証model、適格な`L1/S1` structural placeholder、
人手review、統制済みunresolved stopの順に評価する。Criticality自体は値を生成
しない。

## Structural placeholder gate

次の条件をすべて満たす場合に限り、structural placeholderを検討できる。

1. profileが`structural`である。
2. tupleが`L1`または`S1`である。
3. 適用可能な高順位証拠がない。
4. conflict、conditional表現、unsupported表現、方向ambiguityがない。
5. 属性別donor population、source hash、grouping key、除外条件、sample unit、
   方向処理、canonicalization、minimum sample size、distribution、
   selected value、mode share、tie ruleが`sumo_network.yml`を満たす。
6. adopted valueとrule IDをauditへ記録する。
7. formal研究利用を引き続き禁止する。
8. sensitivity状態を記録する。

一つでも満たさない場合は`stop_unresolved`とする。多数道路から得たmodeは、
特定道路の値が正しいことの証拠ではない。

## Failure code

| Requirement | Failure code | Test | 検出内容 |
|---|---|---|---|
| `AC-REQ-001` | `AC001` | `AC-TST-001` | 保持tuple欠損 |
| `AC-REQ-002` | `AC002` | `AC-TST-002` | tuple重複 |
| `AC-REQ-003` | `AC003` | `AC-TST-003` | 未知rule ID |
| `AC-REQ-004` | `AC004` | `AC-TST-004` | predicate組合せ矛盾 |
| `AC-REQ-005` | `AC005` | `AC-TST-005` | 証拠がtupleへ適用不能 |
| `AC-REQ-006` | `AC006` | `AC-TST-006` | 証拠conflict未解決 |
| `AC-REQ-007` | `AC007` | `AC-TST-007` | 必須review未完了 |
| `AC-REQ-008` | `AC008` | `AC-TST-008` | structural-placeholder gate不合格 |
| `AC-REQ-009` | `AC009` | `AC-TST-009` | source・policy・classification hash不一致 |
| `AC-REQ-010` | `AC010` | `AC-TST-010` | action・value state・review status組合せ不正 |

各failure codeにはnegative fixture`<code>-NEG-001`も必要とする。

## Fixture contract

production classificationの前に、独立fixtureで次を検証しなければならない。

- すべてのlane・speed level
- 二つの証拠source間のprecedenceとconflict
- 完全tuple被覆と重複tuple
- structuralからformalへの再分類
- post-critical昇格と依存artifact無効化
- 許可・禁止されるstructural placeholder
- 未対応conditional・directional表現
- 除外とtopology-support保持の区別
- 決定的な繰り返し分類

fixture oracleは、期待tuple record内でclassification objectとresolution objectを
分ける。selected・matched rule ID、level、action、value state、resolved value、
review status、failure codeを含める。production codeが自身のoracleを生成しては
ならない。

`inputs.json`はcase indexではなく完全な実行入力catalogueとする。record生成前に
停止するcaseも対象tupleを持ち、OSM属性、predicate、evidence candidate、profile、
revision状態を記録する。各oracle caseはmachine-readable assertionとrecord発行
方針を持つ。manifestのcoverageはcoverage IDとassertion IDを対応づけ、level・
scenario索引は手書きせず導出する。

negative fixture IDはfailure codeを含む`<code>-NEG-001`を維持する。positive、
boundary、repeatは単一failureの証人ではないため、それぞれ`AC-POS`、`AC-BND`、
`AC-REP` namespaceを使用する。

`repeat` fixtureはbaseline・repeated output hash、byte比較またはcanonical content
比較mode、canonical比較から除外する明示的JSON Pointerを記録する。runnerは指定
pointerだけを除去し、RFC 8785 contentを比較する。repeat以外のfixtureは
`repeat_assertion=null`を明示する。

`review.json`は構造化したcheck結果、evidence参照、reviewer identity、独立性宣誓、
observed hash、blocking findingを保存する。`acceptance_allowed`は、
`collection_status=independently_accepted`、全必須check合格または非該当、
未解決blocking findingなし、の全条件から導出する。
研究責任者は2026-07-30に独立human reviewを省略すると決定した。この省略は
`acceptance_allowed=true`を意味せず、独立受理済みと報告してはならない。
実装順序から当該reviewを外すが、固定hash検査、semantic validation、
production codeからのoracle独立性は引き続き必須とする。

oracleはproduction output生成とは別のfixture authoring手順で作成し、可能な場合は
production generator作成者とは別の者がreviewする。test runnerはoracle file hashと
source specification hashを検査する。生成processの独立性はJSON内容だけでは完全に
証明できないため、authorとreviewの証拠をfixture review recordへ保持する。

## 現在の状態

本仕様は母集団、tuple identity、predicate contract、classification順序、
classification・resolution object境界を固定した。predicate、
predicate-source-registry、統合attribute classification、fixtureの4 schemaは
実装し、`sumo_network.yml`へ登録済みである。predicate generator、
fail-closed synthetic test、semantic validatorによるsource registry展開は
実装済みである。ClassifierとResolverの各stageは未実装である。cross-record
semantic validatorと独立production fixture collectionは実装済みである。
fixture collectionはclassifierより前に作成し、production codeで
oracleを生成していない。独立human reviewは研究責任者判断で省略し、固定
Classifier・Resolver実行は未完了である。
これらは次版で受理された実データ母集団には未適用である。したがって、大田区wayは
`unclassified`のままであり、
本書は46,056-blocker Dry Runの結果を変更せず、新しいResolver runも許可しない。

登録済み実データの分類は、さらに
`02_resolver_specification.md`の
`Relation Closure Before Attribute Classification`で定義した母集団受入gate
に依存する。fixture reviewとclassifier開発はgate合格前に進められるが、v15
母集団に対するproduction classification artifactを公開してはならない。
次版closure受理後、新しい入力から完全な
`(osm_way_id, attribute, profile)`被覆を生成し、v15 recordへ追加しては
ならない。

## 現在の実装順序

1. 実装済みPredicate Generatorを固定synthetic fixtureで再実行し、決定的な成功と
   fail-closedの証拠を保持する。
2. `criticality_level`、`selected_rule_id`、`matched_rule_ids`だけを決める
   Classifierを実装する。
3. 値、evidence選択、conflict、review状態、停止結果を決めるResolverを独立実装
   する。または一つの実行program内で明示的に分離したstageとして実装する。
4. positive、negative、boundary、repeat、revision、evidence conflict、
   placeholder fixtureでClassifierとResolverを実行する。production outputを
   独立oracleの書換えに使用してはならない。
5. 既知の`type=restriction:bus` 3 relation、完全な参照、再集計した母集団、
   新input hashを持つ次版relation closureを受理する。v15は使用不可のままとする。
6. 受理済み母集団からstructural・formal artifactを別々に生成し、未解決tupleを
   stop recordとして保持し、semantic validation後にatomic publishする。
