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

## Classification・Resolution artifact

Classificationは影響levelを決め、resolutionは値を採用できるか、どの方法で
採用するかを決める。両者は別々のhash-linked artifactとし、一つのflat recordへ
混在させてはならない。

`attribute_criticality_classification.json`は、選択profileについて、保持する
すべての`(osm_way_id, attribute)` pairごとに正確に1 recordを含まなければ
ならない。

| Field | 意味 |
|---|---|
| `osm_way_id` | relation-closed入力内の安定したOSM way ID |
| `attribute` | `lanes`または`maxspeed` |
| `profile` | `structural`または`formal` |
| `criticality_level` | 本書で定義する属性別level |
| `criticality_rule_id` | levelを決定した一つのrule |
| `predicate_evidence` | ruleが使用したhash拘束済み事実 |
| `source_artifact_sha256` | 分類対象relation-closed入力のhash |
| `classification_config_sha256` | 分類policyのhash |

`attribute_resolution_decisions.json`は、値解決対象として保持する全
classification tupleごとに正確に1 decisionを含まなければならない。

| Field | 意味 |
|---|---|
| `classification_record_id` | classification recordへの安定した参照 |
| `classification_artifact_sha256` | classification artifact全体のhash |
| `evidence_required` | 値採用前に必要な証拠class |
| `evidence_candidates` | 検討した適用可能・却下候補の配列 |
| `selected_evidence_id` | 選択候補。停止中は空 |
| `rejected_evidence_ids` | 選択しなかった候補ID |
| `conflict_resolution_rule_id` | conflict解決rule。未使用時は空 |
| `resolution_action` | 本書で許可するaction |
| `resolution_rule_id` | 値を解決するrule。停止中は空 |
| `value_state` | 統制された値由来または停止state |
| `adopted_value` | 採用canonical値。停止・除外時は空 |
| `unit` | 属性に適合する単位。不要時は空 |
| `review_status` | `machine_resolved`、`review_required`、`reviewed`、`stopped` |
| `reviewer` | reviewed判断だけで必須 |
| `reviewed_at` | reviewed判断だけで必須 |
| `stop_failure_codes` | 停止時の一つ以上の統制code |

各evidence candidateはsource、値、単位、方向、segment、vehicle scope、
観測・基準期間、license、source hash、matching confidenceを持たなければ
ならない。confidenceを選択に使う前に、policy schemaでscale、採用threshold、
同率処理を固定する。

未知field、重複・欠損tuple、未知rule ID、predicate矛盾、登録source hashのない
証拠、classification hash不一致はResolver実行前に停止しなければならない。

## 分類前のPredicate整合性検証

classifierは、predicate整合性を先に検証し、その後に順序付きfirst-match ruleを
適用する。同じwayが次の組合せを同時に持つ場合はlevelを黙って割り当てず停止する。

- excludedかつcalibration・independent-validation segment
- excludedかつaccepted delivery route
- excludedかつtopology supportとして必要
- final subgraph外かつ保持governed route内
- 版管理済みclassification policyが禁止するその他の組合せ

wayを完全に除外し、topology supportでも保持governed routeの一部でもない場合、
laneとmaxspeed recordは`L0`と`S0`に揃える。属性固有predicateが異なり、その
差をclassification recordで示す場合だけ、laneとmaxspeedで異なるlevelを許容する。

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
| `LANE-CRIT-001` | governed subgraph判断が`excluded`で、wayがtopology supportとして不要 | `L0` |
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
| `SPEED-CRIT-001` | governed subgraph判断が`excluded`で保持routeにも不要 | `S0` |
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

classifierは次のactionだけを出力できる。

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

| Resolution action | 許容value state | Review status |
|---|---|---|
| `adopt_explicit` | `explicit_osm` | `machine_resolved`または`reviewed` |
| `derive_osm_rule` | `derived_osm_rule` | `machine_resolved`または`reviewed` |
| `adopt_external_evidence` | `authoritative_external` | `machine_resolved`または`reviewed` |
| `apply_governed_rule` | `derived_validated_model` | `machine_resolved`または`reviewed` |
| `apply_structural_placeholder` | `structural_placeholder` | `machine_resolved`または`reviewed` |
| `require_human_review` | 未解決・停止state | `review_required` |
| `stop_unresolved` | `missing`、`unresolved`、`conflict`、`valid_but_unsupported`、`conditional`、`directionally_asymmetric`、`invalid` | `stopped` |
| `exclude` | `excluded` | `machine_resolved`または`reviewed` |

その他のaction・state・review組合せは禁止する。人手reviewは新しいvalue stateを
許可しない。review後は解決済みactionへ遷移するか、停止を継続する。

## Profile別必須入力

| Input | `structural` | `formal` |
|---|---|---|
| 完全なclassification artifact | 必須 | 必須 |
| resolution-decision artifact | 保持する未解決tupleごとに必須 | 保持する未解決tupleごとに必須 |
| external evidence artifact | 参照時に必須 | 参照時に必須 |
| structural-placeholder rule | 使用時だけ必須 | 禁止 |

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

Classification fixture oracleは期待levelとrule IDを含める。Resolution fixture
oracleは期待action、value state、review status、failure codeを別に含める。
production codeが自身のoracleを生成してはならない。

## 現在の状態

本仕様は分類語彙、predicate検証順序、classificationとresolutionの分離を
固定した。二つのschema、predicate-source artifact、classifier、Resolver統合、
fixtureは未実装である。したがって、大田区wayは`unclassified`のままであり、
本書は46,056-blocker Dry Runの結果を変更せず、新しいResolver runも許可しない。

登録済み実データの分類は、さらに
`02_resolver_specification.md`の
`Relation Closure Before Attribute Classification`で定義した母集団受入gate
に依存する。classifier schemaとsynthetic fixtureはgate合格前に開発できるが、
v15母集団に対するproduction classification artifactを公開してはならない。
次版closure受理後、新しい入力から完全な
`(osm_way_id, attribute, profile)`被覆を生成し、v15 recordへ追加しては
ならない。
