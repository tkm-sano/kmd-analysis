# Resolver仕様書

## 文書の位置付け

本書は
[`02_resolver_specification.md`](../02_resolver_specification.md)の日本語版で
ある。要件ID、failure code、test ID、機械可読フィールド名および状態値は
英語正本と同一である。両文書に差異がある場合は、機械可読設定と英語正本を
優先し、日本語版を修正する。日本語版だけで要件を追加または緩和しては
ならない。

## 対象範囲

Resolverは、OSMの`oneway`、車線数、速度、accessについて最終採用値を決める
唯一のコンポーネントである。lanes・maxspeedのcriticality、証拠適用可能性、
証拠順位、structural-placeholder gateは
`attribute_criticality_and_evidence_specification.md`を正本とする。`oneway`、
access、permission、共通の証拠登録形式、出典管理は
`network_attribute_governance.md`を正本とする。本書は両正本に基づく判断を
消費するResolverの実行境界を定め、証拠順位を重複定義しない。

Relation closureは上流の`prepare`責任である。PBF母集団の抽出、governed
relation memberの再帰的補足、cycle検出、hash登録済みOSM XML・closure
manifestの公開を行う。Resolverはそれらを検証・消費し、relation-scope会計を
記録し、contract不完全時に停止するが、PBF抽出やclosure公開は行わない。専用
closure仕様を分離するまでは、本書のclosure要件をResolver入力の規範的前提とする。

## 入力と出力

入力は、リポジトリ相対パスで指定され、hash登録されたOSM XML、版管理済み
設定、統制typemapでなければならない。完全なclassification artifactは両profile
で必須であり、全tuple record内に別々のclassification・resolution objectを持つ。
完全なpredicate artifactも必須である。resolution objectが外部証拠を参照する
場合はexternal evidence artifactが必須である。structural-placeholder ruleは
structuralでplaceholderを使用する場合だけ必須とし、formalでは禁止する。

- `normalized.osm.xml`
- `permission_expectations.schema.json`に適合する
  `permission_expectations.json`
- 道路属性audit CSV
- imputation summary JSON
通常の統制停止では、audit、imputation summary、`complete=false`のpermission
artifact、`failure_report.schema.json`に適合する`failure_report.json`を保持し、
`normalized.osm.xml`は公開しない。
整合した成果物集合を作る前に入力、設定、schema、公開処理が失敗した場合は、
failure reportだけを公開する。`profile=formal`の未解決状態禁止は、成功した
`complete=true` artifactへ適用し、統制済みfailure artifactは禁止しない。
CLIは成功時に0、分類済みResolver failureで2、failure reportも公開できない
場合に3を返す。

## 規範要件

| ID | 要件 | Failure | Test |
|---|---|---|---|
| RS-REQ-001 | OSM rootは`osm`でなければならない。保持するwayは、空でない一意のIDと一意のtag keyを持たなければならない。 | RS001 | RS-TST-001 |
| RS-REQ-002 | 明示的なtypemap whitelistに含まれる道路だけを保持できる。除外したすべてのhighway wayを数えなければならない。 | RS002 | RS-TST-002 |
| RS-REQ-003 | 成功出力の前に、保持する全wayについて`oneway`、方向別車線数、`maxspeed`、permissionを解決しなければならない。 | RS003 | RS-TST-003 |
| RS-REQ-004 | `missing`、`valid_but_unsupported`、`conditional`、`directionally_asymmetric`、`conflict`、`invalid`を別々の状態として保持しなければならない。 | RS004 | RS-TST-004 |
| RS-REQ-005 | structural imputationは、`L1`または`S1`と分類された真の欠損tupleに対し、`resolution_action=apply_structural_placeholder`で、全placeholder gateに合格し、事前登録済みの属性別unique-mode ruleが一つの値を決定する場合だけ適用できる。 | RS005 | RS-TST-005 |
| RS-REQ-006 | 成功した`profile=formal`、`complete=true` artifactにはstructural placeholderまたは未解決の停止状態を含めてはならない。 | RS006 | RS-TST-006 |
| RS-REQ-007 | `oneway=-1`は、方向依存属性を含む完全な変換が実装されるまで停止しなければならない。部分的な反転は禁止する。 | RS007 | RS-TST-007 |
| RS-REQ-008 | forward・backward tagのいずれについても、lane access値は各進行方向から見て左から右の順に読まなければならない。 | RS008 | RS-TST-008 |
| RS-REQ-009 | Resolverのlane position 0は、その進行方向の最左車線を意味しなければならない。 | RS009 | RS-TST-009 |
| RS-REQ-010 | 未対応のaccess key・value、方向suffixのない双方向lane access、lane value数の不一致は停止しなければならない。 | RS010 | RS-TST-010 |
| RS-REQ-011 | 期待permissionは、解決済みOSM permission、選択typemap baseline、governed vClassの積集合と一致しなければならない。 | RS011 | RS-TST-011 |
| RS-REQ-012 | expectation artifactはtype、方向、lane position、rule、hashの完全な来歴を含まなければならない。v13のmap-only形式はv15入力として無効である。 | RS012 | RS-TST-012 |
| RS-REQ-013 | 明示的に統制された開発用overrideを除き、出力は原子的に書き込み、入力と別pathにし、既存出力を上書きしてはならない。 | RS013 | RS-TST-013 |
| RS-REQ-014 | closure・Resolver artifactはsource type別にrelation scopeを分類し、governed vehicle固有restrictionを保持し、除外relationと補足要素を数え、governed trafficへ影響し得る未分類relation typeで停止しなければならない。 | RS014 | RS-TST-014 |

この要件・failure・testの一対一対応は次版contractである。実行済みv15 Dry Runと
failure artifactは不変の履歴証拠として元のcodeを保持する。次のproduction run
より前にResolver実装、schema、fixtureを同時に移行しなければならない。

## 方向別車線配分

`formal`では、すべての双方向道路について、明示的で整合する
`lanes:forward`と`lanes:backward`を必要とする。`lanes`からの等分推定は
行わない。`structural`では、偶数の総車線数に限り、
`resolution_action=apply_structural_placeholder`、
`value_state=structural_placeholder`として等分し、方向配分rule IDをauditへ
記録できる。`approved_assumption`はResolverのactionまたはvalue stateとして
使用しない。明示的な方向配分がない1車線または奇数車線、およびすべての
`lanes:both_ways`は`RS008`で停止する。

## Imputation donor

donor適格性は属性別に判定する。lane donorは、解決可能な方向、sample単位に
対応する整合した明示lane値、lane関連conditional・conflict tagなし、
`oneway=-1`なし、structuralで解決可能なpermissionを必要とする。maxspeed欠損
だけを理由にlane donorから除外しない。maxspeed donorは、sample方向に対応する
canonicalな明示数値速度、speed関連conditional・directional・variable・
conflict表現なし、`oneway=-1`なし、解決可能なpermissionを必要とする。lane欠損
だけを理由にmaxspeed donorから除外しない。

両ruleは`sumo_network.yml`に登録したgrouping key、source-population hash、
除外条件、minimum sample size、minimum mode share、tie policy、sample unit、
canonicalizationを使用する。対象tuple自身はsample属性が欠損しているためdonorに
含めない。grouping値欠損、sample不足、同率modeは、隣接道路classへfallbackせず
停止する。`40`と`40.0`のような小数として等価な速度はcanonical値`40`へ統合
する。

Criticalityはway単位で一度だけではなく、
`(osm_way_id, attribute, profile)`ごとに分類する。classificationとresolutionは
同じimmutable profile snapshot内の別objectとし、hash-linked predicate artifactを
使用する。統制語彙、証拠順位、artifact field、
structural-placeholder gateは
`attribute_criticality_and_evidence_specification.md`で定義する。4 schema、
Predicate Generator、Semantic Validator、production fixture collectionは
実装済みである。fixture collectionの独立受理と、Classifier・Resolver stageの
実装・固定fixture検証が完了するまでは、classification・resolution統合入力を
省略した全wayを`unclassified`とし、structural placeholderを通過させては
ならない。

観測されたv15例外母集団と未解決のdecision状態は、
`reproducibility/config/traffic_simulation/resolver_exception_decision_table.yml`
へ登録する。後続Resolver版が例外分類完了を主張するには、全行がちょうど1件の
decision-table entryへ一致しなければならない。entryのruleと独立fixtureが
実装されるまで、entryの存在だけで解決を許可してはならない。

## Permission trace

各way・方向・lane recordには、そのlaneへ実際に適用したruleだけを含める。
順序付きtraceには、typemap baseline、研究scopeとの積集合、適用可能な一般、
class、方向、lane固有のOSM遷移を記録する。source tag・value、lane-local値、
変更前後のvClass集合を含める。別方向または別laneへ適用されるtagを、その
laneのtraceへ含めてはならない。

## 公開処理と入力完全性

すべてのartifactは一つのstaging directoryで生成し、検証後に公開する。
置換時はbackupとrollbackを用い、例外発生時に異なるrunのartifactが混在
しないようにする。`.part`は`finally`で削除する。`--overwrite`は開発用
overrideに限り、formal orchestrationでは新しいrun identityとpathを使用する。

OSM tagは空でない`k`と、存在し空でない`v`を必要とする。保持するwayは有効な
node参照を持たなければならない。実行済みv15は、`type=restriction`だけを
保持した。その後の全入力auditでturn restrictionを持つ
`type=restriction:bus`が3件見つかったため、完全一致によるtype保持だけでは
governed vehicle universeに不十分である。次のformal候補を作る前に、版管理
されたrelation-scope表で`type=restriction`を保持し、適用可能な車種固有
restriction typeを統制し、governed trafficへ影響し得る未分類typeで停止
しなければならない。道路接続に無関係と分類済みのrelationは、member参照検証
前に除去できる。保持したrestrictionが意図的に除外したhighway wayを参照する
場合はrestrictionも除去し、不明なmember wayを参照する場合は停止する。

Resolver入力は、XML変換前に、governed restrictionの全memberを登録済み地域
PBFからclosureする。closure・Resolver artifactはsource `type`別のrelation
判断、保持restriction、欠損member参照、補足要素種別を数えなければならない。
除外relationを道路証拠として解釈してはならないが、除外には明示的なscope rule
が必要である。この会計は、除外relationが不正なOSMデータであることを意味
しない。criticality mapを与える場合はsource fileと保持wayの完全被覆が必要で
ある。v15 typemap contractは`allow`だけを許可し、保持typeに`disallow`が
あればpolicy読込を停止する。

## 属性分類前のrelation closure

次版relation closureにより分類母集団が固定されるまで、登録済み実データへ
attribute criticalityを適用してはならない。実行済みv15 closureは、`type`が
完全に`restriction`と一致するrelationだけを保持した。その後のtype別auditで、
v15が除外したgoverned vehicle固有restrictionを3件確認した。

| Relation ID | Source type | Restriction |
|---|---|---|
| `16016504` | `restriction:bus` | `only_straight_on` |
| `16016506` | `restriction:bus` | `no_straight_on` |
| `16026064` | `restriction:bus` | `only_straight_on` |

`bus`はgoverned vClass universeに含まれるため、これらを道路外relationと分類
できない。これは既知のformal scope blockerである。v15 closure、26,220件の
候補way、Dry Runは不変baselineとして保持する。次版入力ではbaselineを暗黙に
変更せず、新しいconfig identityとartifact pathを使用しなければならない。

### 次版closure方針

次版closure実装は、次の条件を満たさなければならない。

1. 登録済み大田区BBOX extractとhash登録済み関東PBFから開始する。
2. spatial extract内の全`type=restriction`を保持する。
3. `type=restriction:bus`および他の車種固有restrictionは、そのvehicle scopeを
   governed vClass universeへ対応づけた後に限り保持する。
4. governed trafficを制約し得る未分類relation typeで停止する。
5. 保持relationの全memberを登録済み地域PBFから再帰的に補足する。
6. 補足したtopology-support node・wayと最終N03 analysis subgraphを区別する。
7. node、way、relation member欠損を検証し、relation cycleを検出する。
8. 保持、除外、停止relationをsource type・rule ID別に記録する。
9. relation-closed PBFとOSM XMLを原子的に生成する。
10. exact command、tool version、config・input hash、output hash、追加要素を
    prepare manifestへ記録する。

車種固有restrictionの処理は、文字列prefix whitelistではない。governed
vehicle universeへの適用可能性、restrictionの意味、source-tag形式には、
明示的で版管理されたdecision ruleとfixtureが必要である。

### 母集団受入gate

実データcriticality classifierは、次の条件がすべて合格した後に限り開始
できる。

| Gate条件 | 必要な証拠 |
|---|---|
| 既知のbus restriction 3件を保持 | closure manifest内のrelation IDとretained-rule ID |
| 保持relationの全memberが存在 | node、way、relation member欠損が0 |
| closureが決定的 | 同一登録入力から同一semantic output |
| support elementを識別 | 追加node・way IDとsupport・final-subgraph状態 |
| 候補母集団を再集計 | origin・highway type別distinct governed way |
| v15との差分を明示 | 追加・除去・不変のway・relation ID |
| 新artifactを独立識別 | 新config ID、run ID、path、SHA-256 |

一つでも不合格なら、分類母集団は未受理とする。旧26,220-way母集団だけに
criticality recordを生成し、後から新規wayを追加してはならない。

### 下流成果物の無効化

新しいclosureを受理すると、v15 relation-closed入力の被覆またはhashに依存する
次のartifactを無効化する。

- 道路属性audit
- permission expectations
- imputation distributions
- exception queueとDry Run summary
- attribute criticality coverage
- candidate-way counts
- これらの入力から作ったprovisional networkまたはmapping

次回runでは、受理済みclosureからこれらを再生成し、v15 baselineに対する
追加・除去・不変blockerを報告しなければならない。

## Lane順序の正本

OSM lane listは、各進行方向から見て左から右に解釈する。backward listはOSM
wayと逆方向に走るという理由だけでResolver内部で反転しない。Materializerが
後でSUMOの右から左のindexへ対応づける際にlane positionを反転する。

## 成功条件

`complete=true`には、blocker 0、保持する全wayにつき1件のexpectation record、
方向別lane countとlane recordの完全一致、config・input・typemap hashの一致が
必要である。governed vClass universeが空の成功artifactは禁止する。

成功artifactでは、`normalized_osm`に同一runが出力した正規化XMLの
repository-relative pathとSHA-256を記録する。失敗artifactは正規化XMLを公開
しないため、この参照を含めない。この形式のfixture検証だけでは、登録済み
大田区extractに対する適格性を示さない。
