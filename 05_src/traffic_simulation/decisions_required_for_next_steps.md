# 今後の交通シミュレーション工程で決めるべき事項

> **文書状態:** 未決定事項の横断管理表
> **基準日:** 2026-08-01
> **対象:** 版17属性解決、正式SUMO道路網、較正、独立検証、正式比較
> **利用制限:** 本文書はmachine-readable authorityでも規範実装契約でもない

## 1. 目的

本文書は、今後の工程へ進む前に研究責任者、実装責任者、検証責任者が決める事項を、
依存順に整理するためのチェックリストである。既存の承認済み方針を再決定せず、未決定
事項の所在、必要な成果物、承認先、後続工程への影響を一枚で確認できるようにする。

本文書の`NEXT-DEC-*`は管理用識別子であり、既存の要件ID、`DEC-*`、`OPEN-PROP-*`、
停止コードを置き換えない。決定後は、該当する正本、機械可読設定、Schema、要件追跡表
へ反映し、本文書には参照先と承認状態だけを記録する。

## 2. 正本と責任分界

| 内容 | 正本・管理先 |
|---|---|
| 現行v16ネットワーク状態 | `reproducibility/config/traffic_simulation/sumo_network.yml` |
| ネットワーク状態の型 | `reproducibility/config/traffic_simulation/sumo_network.schema.json` |
| 版17属性解決baseline policy | `reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml` |
| 版17方針の説明 | `specifications/10_approved_attribute_resolution_policy.md` |
| 属性別の詳細な未決定事項 | `specifications/attribute_resolution_decisions_to_finalize.md` |
| `OPEN-PROP-*`の定義 | `specifications/initial_formal_attribute_resolution_specification_proposal.md` |
| 実装・実行・受理順序 | `attribute_resolution_execution_procedure.md` |
| 要件単位の実装状態 | `reproducibility/config/traffic_simulation/requirements_traceability.yml`および版17追跡表 |
| 研究工程と利用可否 | `reproducibility/config/traffic_simulation/research_stage.yml` |

本文書と正本が異なる場合は正本を優先する。未決定事項を承認しただけでは実装済み、
runtime検証済み、またはformal eligibleにならない。

## 3. 再決定しない事項

次は既に固定されているため、明示的な改版手続なしに再決定しない。

- 版16成果物、既存run、既存SHA-256を上書きせず、版17結果へ再ラベルしない。
- accepted v16 populationは26,220 waysである。
- Resolver expected permissionsを版17formal authorityとし、typemapをformal上限にしない。
- managed vClass universeと`managed_urban_ev_delivery_v1`の確定済み諸元を維持する。
- `resolution_status`と`value_origin`を版17canonical fieldsとする。
- formalでは`model_assumed`を許可しない。
- formalの双方向道路では`lanes:forward`と`lanes:backward`を明示的に要求する。
- `oneway=-1`では原典OSM Wayを変更せず、backward Directed Segmentを生成する。
- SUMO edge IDの符号と座標最近傍をformal方向証拠に使用しない。
- production出力から独立oracleを生成しない。
- generated `net.xml`を直接編集しない。
- SUMOの固定版は1.24.0である。
- Attribute Resolution AcceptanceとSUMO Network Integration Acceptanceを分離する。
- structural/provisional networkを較正、独立検証、配送、solver比較へ使用しない。

## 4. 状態と決定記録

各項目の状態は次から選ぶ。

| 状態 | 意味 |
|---|---|
| `not_started` | 検討を開始していない |
| `drafted` | 選択肢と根拠を整理したが未承認 |
| `evidence_required` | 判断に必要な証拠が不足している |
| `approved` | 承認者、承認日、版、根拠SHA-256を記録済み |
| `out_of_scope` | 除外範囲と理由を承認し、manifestへ記録済み |
| `superseded` | 後続版の決定に置き換えられた |

各決定記録には最低限、管理ID、既存ID、質問、採用内容、適用範囲、選択理由、出典、
証拠SHA-256、競合時の処理、停止コード、影響する要件・fixture、承認者、承認日、
configuration versionを含める。

## 5. 最優先で決める事項：版17規範annex

以下が未承認の間、該当入力をformal eligibleにしない。

### 5.1 停止理由と失敗コード

**管理ID:** `NEXT-DEC-001`  
**既存ID:** `OPEN-PROP-005`、`DEC-COMMON-009`から`012`  
**現在状態:** `not_started`

決めること：

- 名称付き停止理由と既存の安定した失敗コードの完全な対応表
- 未登録状態、未登録規則、未登録停止コードを検出した場合の停止方法
- 一つの原因が複数tupleへ波及する場合の集計単位
- 既存失敗コードを改名せず拡張する手順

必要成果物は、機械可読対応表、Schema、正常・未知・重複fixture、承認記録である。

### 5.2 配送目的地とaccess目的scope

**管理ID:** `NEXT-DEC-002`  
**既存ID:** `OPEN-PROP-009`、`DEC-COND-009`、`DEC-PERMIT-003`、`004`  
**現在状態:** `not_started`

決めること：

- `destination`、`delivery`、`customers`の対象区域
- 配送先が道路内または沿道にあると判定する識別子と空間一致規則
- 通過交通、目的地進入、顧客訪問、配送業務の区別
- 一つの道路上に対象地点と非対象地点が混在する場合の扱い
- 必要な目的文脈が欠損した場合の停止コード

必要成果物は、目的scope設定、地点・道路対応fixture、境界例、根拠SHA-256である。

### 5.3 conditional-expression grammar

**管理ID:** `NEXT-DEC-003`  
**既存ID:** `OPEN-PROP-010`、`DEC-COND-001`から`014`  
**現在状態:** `not_started`

決めること：

- 対応するOSM条件式の文法版とtoken集合
- 境界時刻の包含、夜間をまたぐ範囲、曜日・祝日・日付範囲
- 重量・寸法の単位、論理積・論理和・否定・括弧・セミコロン
- `Asia/Tokyo`での評価期間とsimulation interval
- date、time、holiday、vehicle、weight、dimensions、trip purposeの必須context
- unsupported syntax、missing context、期間内変化、競合時の停止コード

必要成果物は、grammar、parser契約、条件profile、祝日暦、正常・異常・境界oracleで
ある。

### 5.4 Japan speed-rule table

**管理ID:** `NEXT-DEC-004`  
**既存ID:** `OPEN-PROP-011`、`DEC-SPEED-001`から`010`  
**現在状態:** `evidence_required`

決めること：

- 2026年7月16日に有効な法令・行政資料と条項
- 指定速度、法定速度、助言速度、simulation speedの区別
- 道路区分、中央線、車両通行帯、構造分離、車種ごとの決定表
- 数値`maxspeed`、direction-specific speed、条件付き速度、法令導出の優先順位
- 制度改正時の適用日と設定改版方法

必要成果物は、適用期間付き機械可読速度表、出典台帳、Schema、境界日fixtureである。

### 5.5 `JP:urban`用道路状態証拠

**管理ID:** `NEXT-DEC-005`  
**既存ID:** `OPEN-PROP-012`、`DEC-SPEED-004`、`005`、`009`  
**現在状態:** `evidence_required`

決めること：

- 法令導出に必要な道路状態の必須項目
- OSM、道路管理者資料、道路台帳、画像確認の権威順位
- 証拠の区間、方向、適用日をDirected Segmentへ一致させる規則
- 道路状態が欠損または競合する場合の停止コード
- 目視証拠を認める場合の撮影日、位置、方向、確認者、SHA-256

### 5.6 permit registry

**管理ID:** `NEXT-DEC-006`  
**既存ID:** `DEC-PERMIT-001`から`010`  
**現在状態:** `not_started`

決めること：

- 許可台帳の管理責任者、版、改訂・失効手順
- 道路、区域、方向、車線、車種、車両、目的、適用期間の必須項目
- `private`、`permit`と具体的な車種別許可タグの評価関係
- 許可なし、期限切れ、対象不一致、競合時の停止規則
- 道路分割後も許可対象をDirected Segmentへ追跡する方法

基準車両が特別許可を持たないという固定方針と、背景交通または将来scenario用の台帳
設計を混同しない。

### 5.7 formal unpaved-surface rule

**管理ID:** `NEXT-DEC-007`  
**既存ID:** 新しい規範annexとして登録が必要  
**現在状態:** `evidence_required`

決めること：

- `surface`、`smoothness`、`tracktype`の役割と優先順位
- unpaved判定の対象道路機能、車種、速度・accessへの影響
- 欠損、未知値、タグ競合時の停止条件
- structural-only仮定とformal証拠の境界

`highway=track`のscope除外理由と、舗装状態の判定を混同しない。

### 5.8 production-independent oracle

**管理ID:** `NEXT-DEC-008`  
**既存ID:** `OPEN-PROP-015`、`DEC-FIXTURE-001`から`005`  
**現在状態:** `not_started`

決めること：

- production実装と独立した入力・正解の作成手順
- oracle作成者、レビュー担当者、独立性宣言
- 正常、異常、境界、再実行、規則改訂の必須coverage
- 入力、正解、規則、出典、manifestのSHA-256固定方法
- 正本改訂時に旧oracleを上書きしない版管理方法

## 6. production統合前に決める事項

### 6.1 v17設定とSchemaの配置・版

**管理ID:** `NEXT-DEC-009`  
**現在状態:** `not_started`

- 各annex、registry、scenario profileの正本パスとSchema
- `approved_attribute_resolution_policy_v17.yml`を改版する条件
- v17 network-state configurationのID、版、v16との継承関係
- `resolution_status`、`value_origin`、exclusion manifestの互換境界
- production入出力境界ごとの許容Schema版

### 6.2 vehicle-input validatorの境界

**管理ID:** `NEXT-DEC-010`  
**現在状態:** `not_started`

- どのCLI、runner、materializer、SUMO入力境界で検証するか
- profile ID、vClass、重量、寸法、積載、permit状態の必須項目
- profileとruntime inputが不一致の場合の停止コード
- 同一experiment内のvehicle class切替禁止を検査する方法

### 6.3 exclusionと母集団version

**管理ID:** `NEXT-DEC-011`  
**現在状態:** `drafted`

- `resolution_status=excluded`を追加せず別manifestを使う方針の正式承認先
- exclusion rule ID、承認者、承認日、根拠SHA-256のSchema
- `input population = governed population + excluded population`の検査方法
- population versionを更新する条件
- `complete=true`とpermission completenessの分母
- materialization omissionをscope exclusionへ数えない検査

### 6.4 v17 runnerとrun identity

**管理ID:** `NEXT-DEC-012`  
**現在状態:** `not_started`

- runnerのCLI、必須引数、明示run ID、出力ディレクトリ規則
- 不完全runの原子的破棄または隔離方法
- input、configuration、Schema、oracle、output、exclusion manifestのhash manifest
- v16成果物と出力先を共有しない検査
- rerun、規則改訂、停止解消反復のrun命名規則

### 6.5 独立停止記録review

**管理ID:** `NEXT-DEC-013`  
**現在状態:** `not_started`

- review対象、sampleではなく全件確認が必要な区分
- reviewerの独立性、承認権限、期限
- 証拠不足、規則不足、実装不具合、承認済み除外の分類基準
- review findingの解消、再実行、再承認手順

## 7. Attribute Resolution Acceptance前に決める事項

**管理ID:** `NEXT-DEC-014`  
**現在状態:** `drafted`

決めること：

- acceptance manifestのSchema、保管先、承認者
- `complete=true`、blocker、review、unresolved、formal `model_assumed`の判定方法
- population、record、attribute、permission coverageの分母と検査器
- classification projection、semantic consistency、record/self-hash、run manifestの
  validator責務とCLI
- exclusion manifestのhash、rule登録、population version整合の検査
- legacy `value_state`だけのartifactを拒否する検査
- formal evidence/imputation未実装時にacceptanceを拒否する検査

このゲートにSUMO edge、lane、connection、TLS、reachabilityの検査を含めない。

## 8. 正式道路網build前に決める事項

### 8.1 environment/build manifest

**管理ID:** `NEXT-DEC-015`  
**現在状態:** `not_started`

- commit、container digest、SUMO版、command、設定・入力・出力hashの必須項目
- OS、architecture、locale、timezone、依存package、random seedの記録範囲
- 再現不能な環境差分を検出した場合の停止条件

### 8.2 junction-join review

**管理ID:** `NEXT-DEC-016`  
**現在状態:** `not_started`

- junction join候補を採用・却下する証拠とreviewer
- 10 m候補検索後のgeometry、level、connection、signal確認基準
- governed node fileのSchema、版、hash、再review条件
- automatic joinをformal conversionで無効化したことの検査

### 8.3 exact edge provenance

**管理ID:** `NEXT-DEC-017`  
**現在状態:** `drafted`

- Way、分割区間、Directed Segment、SUMO edge、laneの一対多関係Schema
- source node lineage indexと`origId`の必須条件
- 分割・削除・内部edgeを追跡する方法
- 未対応edge、lane、connectionを検出した場合の停止コード

### 8.4 Permission Materializerとomission audit

**管理ID:** `NEXT-DEC-018`  
**現在状態:** `drafted`

- plain XML入出力、原子的出力、決定的順序、失敗時の処理
- lane順、空permission set、部分的に空のlane、全lane空edgeの規則
- materialization omissionのreason code
- omission auditに必要なsource way、Directed Segment、Resolver tuple、edge、connection、
  configuration、permission expectation、materializer outputの各hash
- empty resolved permissionとunresolved/conflictを区別する検査
- pinned SUMO 1.24.0 fixtureの正常、異常、境界oracle

### 8.5 final connection setとsignal/TLS review

**管理ID:** `NEXT-DEC-019`  
**現在状態:** `not_started`

- connection候補の生成責任と、存在しない接続を新規生成しない検査
- turn restriction mapping auditの対象と合格条件
- final connection setを固定するartifactとhash
- signal junction、TLS link、phaseをreviewする責任者
- controlled connection数とphase-state長の一致検査
- connection変更時にreview、較正、validationを無効化する範囲

### 8.6 warning/exclusion audit

**管理ID:** `NEXT-DEC-020`  
**現在状態:** `not_started`

- SUMO warningの分類、許容可否、根拠、承認者
- scope exclusion、materialization omission、変換warningの区別
- 未登録warningまたは未監査exclusionを検出した場合の停止条件
- audit artifactのSchemaとhash binding

### 8.7 structural quality threshold

**管理ID:** `NEXT-DEC-021`  
**現在状態:** `not_started`

- edge、lane、connection、component、dead end、reachability等の評価指標
- 指標ごとのthresholdと根拠
- depot、customer、charger、主要道路間の必須到達性集合
- 車種別・方向別の往復到達性条件
- build結果を見る前にthresholdを固定するpreregistration手順

### 8.8 immutable acceptance artifacts

**管理ID:** `NEXT-DEC-022`  
**現在状態:** `not_started`

- Git管理する小型artifactと外部保管する大容量artifact
- 相互参照するSHA-256、manifest、署名または承認記録
- final `net.xml`、plain XML、provenance、review、audit、environment manifestの保管先
- 変更時に新しいnetwork versionを発行し下流成果物を無効化する手順

## 9. SUMO Network Integration Acceptance前に決める事項

**管理ID:** `NEXT-DEC-023`  
**現在状態:** `drafted`

決めること：

- acceptance manifestのSchema、承認者、保管先
- typemap governance fixture、materializer fixture、lane/connection audit、turn audit、
  warning audit、quality gateの合格証拠
- Attribute Resolution Acceptance artifactを入力として固定する方法
- governed node file、exact provenance、final connections、TLS reviewのhash binding
- final `net.xml`のSUMO 1.24.0 load、left-hand traffic、reachabilityの合格条件
- 不合格時に上流へ戻る工程と、新しいbuild/run IDの規則

このゲート合格前にformal networkを承認しない。

## 10. 較正・独立検証前に決める事項

### 10.1 demandと観測

**管理ID:** `NEXT-DEC-024`  
**現在状態:** `evidence_required`

- demandの対象日、時間帯、車種構成、OD、route choice
- JARTIC等の観測期間、地点、品質条件、欠測処理
- calibration用とindependent validation用データの事前分割
- 同じ観測を調整と最終評価の両方へ使わない検査

### 10.2 calibration protocol

**管理ID:** `NEXT-DEC-025`  
**現在状態:** `not_started`

- 調整対象parameter、探索範囲、固定parameter
- metric、threshold、seed set、warm-up、replication数
- overfitting防止と停止条件
- network、signal structure、demand変更時の再較正条件

### 10.3 independent validation protocol

**管理ID:** `NEXT-DEC-026`  
**現在状態:** `not_started`

- calibrationで未使用の観測集合
- metric、acceptance threshold、seed、confidence interval
- 不合格時にmodel改訂と再validationを分離する方法
- pytest成功をempirical validationとして扱わない報告形式

## 11. 正式比較前に決める事項

### 11.1 共通配送問題

**管理ID:** `NEXT-DEC-027`  
**現在状態:** `not_started`

- depot、customer、charger、需要、時間枠、車両、電池、積載制約
- accepted networkから生成する距離、旅行時間、電力costの版
- infeasible instanceの扱いと修復規則

### 11.2 classical・QAOA比較

**管理ID:** `NEXT-DEC-028`  
**現在状態:** `not_started`

- 全手法に共通するinstance、目的関数、制約、seed、time・evaluation budget
- 生の解と修復後の解へ適用する共通evaluator
- solution qualityと計算資源を分離する指標
- classical、simulator QAOA、将来hardware実行の比較範囲
- 統計報告、失敗run、timeout、欠測の扱い

正式比較へ進めるのはindependent traffic-model validation合格後だけである。

## 12. 決定順序と並行可能作業

```text
NEXT-DEC-001..008  v17 normative annexes and oracle
  -> NEXT-DEC-009..014  production contract, runner, attribute acceptance
  -> NEXT-DEC-015..023  reproducible build and network acceptance
  -> NEXT-DEC-024..026  demand, calibration, independent validation
  -> NEXT-DEC-027..028  formal comparison
```

小型fixtureを用いるprovisional build、Permission Materializer、SUMO runtime fixtureの
開発は、属性停止記録の解消と並行できる。ただし、実データformal network acceptance
はAttribute Resolution Acceptance後、formal比較は独立検証後でなければ実施しない。

## 13. 直近の作業チェックリスト

- [ ] `NEXT-DEC-001`から`008`のownerとapproverを割り当てる。
- [ ] `OPEN-PROP-005`、`009`から`012`、`015`に対応する決定案を作る。
- [ ] 法令・行政資料・祝日暦・許可台帳候補を取得しSHA-256を記録する。
- [ ] formal unpaved-surface ruleの新規annex IDと管理先を決める。
- [ ] production-independent oracleの作成者とreviewerを分離する。
- [ ] 各決定に必要な正常、異常、境界fixture IDを割り当てる。
- [ ] 承認後の機械可読設定・Schema改版計画を作る。
- [ ] `NEXT-DEC-009`以降は上流決定の承認状態を確認して着手する。

最初の完了基準は、`NEXT-DEC-001`から`008`が`approved`または根拠付き
`out_of_scope`となり、正本、設定、Schema、fixture、oracleへ反映する作業票が揃う
ことである。
