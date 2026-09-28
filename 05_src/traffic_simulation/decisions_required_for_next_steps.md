# 今後の交通シミュレーション工程で決めるべき事項

> **範囲 note (2026-09-10):** 本表は2026-08-01時点のnetwork/full-EVRP未決定事項を保持する
> 判断 registerである。現在の縮約した訪問順序 R20/R21/R22 合格とR23 ACCEPTED_WITH_LIMITATIONSは
> `EVRP_EXECUTION_PLAN.md`の別分岐で管理する。ここに残る未決定事項を縮約した 合格へ逆適用しない。

> **文書状態:** 未決定事項の横断管理表
> **基準日:** 2026-08-01
> **対象:** 版17属性解決、正式スーモ道路網、較正、独立検証、正式比較
> **利用制限:** 本文書はmachine-readable 正本でも規範実装契約でもない

## 1. 目的

本文書は、今後の工程へ進む前に研究責任者、実装責任者、検証責任者が決める事項を、
依存順に整理するためのチェックリストである。既存の承認済み方針を再決定せず、未決定
事項の所在、必要な成果物、承認先、後続工程への影響を一枚で確認できるようにする。

本文書の`NEXT-DEC-*`は管理用識別子であり、既存の要件識別子、`DEC-*`、`OPEN-PROP-*`、
停止コードを置き換えない。決定後は、該当する正本、機械可読設定、データ構造、要件追跡表
へ反映し、本文書には参照先と承認状態だけを記録する。

## 2. 正本と責任分界

| 内容 | 正本・管理先 |
|---|---|
| 現行v16ネットワーク状態 | `reproducibility/config/traffic_simulation/sumo_network.yml` |
| ネットワーク状態の型 | `reproducibility/config/traffic_simulation/sumo_network.schema.json` |
| 版17属性解決基準 方針 | `reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml` |
| 版17方針の説明 | `specifications/10_approved_attribute_resolution_policy.md` |
| 属性別の詳細な未決定事項 | `specifications/attribute_resolution_decisions_to_finalize.md` |
| `OPEN-PROP-*`の定義 | `specifications/initial_formal_attribute_resolution_specification_proposal.md` |
| 実装・実行・受理順序 | `attribute_resolution_execution_procedure.md` |
| 要件単位の実装状態 | `reproducibility/config/traffic_simulation/requirements_traceability.yml`および版17追跡表 |
| 研究工程と利用可否 | `reproducibility/config/traffic_simulation/research_stage.yml` |

本文書と正本が異なる場合は正本を優先する。未決定事項を承認しただけでは実装済み、
実行時間検証済み、または正式 対象条件を満たすにならない。

## 3. 再決定しない事項

次は既に固定されているため、明示的な改版手続なしに再決定しない。

- 版16成果物、既存実行、既存SHA-256を上書きせず、版17結果へ再ラベルしない。
- 受入済み v16 母集団は26,220 waysである。
- 属性解決器 expected 通行許可を版17formal 正本とし、道路種別の対応表を正式上限にしない。
- 管理された vClass universeと`managed_urban_ev_delivery_v1`の確定済み諸元を維持する。
- `resolution_status`と`value_origin`を版17canonical fieldsとする。
- 正式では`model_assumed`を許可しない。
- 正式の双方向道路では`lanes:forward`と`lanes:backward`を明示的に要求する。
- `oneway=-1`では原典オープンストリートマップ 道路地物を変更せず、逆方向 方向付き区間を生成する。
- スーモ 道路区間 識別子の符号と座標最近傍を正式方向証拠に使用しない。
- 正式運用出力から独立正解判定器を生成しない。
- 生成済み `net.xml`を直接編集しない。
- スーモの固定版は1.24.0である。
- 属性解決の受入と交通シミュレーターの道路網統合受入を分離する。
- structural/provisional 道路網を較正、独立検証、配送、求解器比較へ使用しない。

## 4. 状態と決定記録

各項目の状態は次から選ぶ。

| 状態 | 意味 |
|---|---|
| `not_started` | 検討を開始していない |
| `drafted` | 選択肢と根拠を整理したが未承認 |
| `evidence_required` | 判断に必要な証拠が不足している |
| `approved` | 承認者、承認日、版、根拠SHA-256を記録済み |
| `out_of_scope` | 除外範囲と理由を承認し、成果物一覧へ記録済み |
| `superseded` | 後続版の決定に置き換えられた |

各決定記録には最低限、管理識別子、既存識別子、質問、採用内容、適用範囲、選択理由、出典、
証拠SHA-256、競合時の処理、停止コード、影響する要件・検証用データ、承認者、承認日、
設定 版を含める。

## 5. 最優先で決める事項：版17規範付録

以下が未承認の間、該当入力を正式 対象条件を満たすにしない。

### 5.1 停止理由と失敗コード

**管理識別子:** `NEXT-DEC-001`\
**既存識別子:** `OPEN-PROP-005`、`DEC-COMMON-009`から`012`\
**現在状態:** `not_started`

決めること：

- 名称付き停止理由と既存の安定した失敗コードの完全な対応表
- 未登録状態、未登録規則、未登録停止コードを検出した場合の停止方法
- 一つの原因が複数組へ波及する場合の集計単位
- 既存失敗コードを改名せず拡張する手順

必要成果物は、機械可読対応表、データ構造、正常・未知・重複検証用データ、承認記録である。

<a id="52-配送目的地とaccess目的scope"></a>

### 5.2 配送目的地と接続目的範囲

**管理識別子:** `NEXT-DEC-002`\
**既存識別子:** `OPEN-PROP-009`、`DEC-COND-009`、`DEC-PERMIT-003`、`004`\
**現在状態:** `not_started`

決めること：

- `destination`、`delivery`、`customers`の対象区域
- 配送先が道路内または沿道にあると判定する識別子と空間一致規則
- 通過交通、目的地進入、顧客訪問、配送業務の区別
- 一つの道路上に対象地点と非対象地点が混在する場合の扱い
- 必要な目的文脈が欠損した場合の停止コード

必要成果物は、目的範囲設定、地点・道路対応検証用データ、境界例、根拠SHA-256である。

<a id="53-conditional-expression-grammar"></a>

### 5.3 条件付き-式文法

**管理識別子:** `NEXT-DEC-003`\
**既存識別子:** `OPEN-PROP-010`、`DEC-COND-001`から`014`\
**現在状態:** `not_started`

決めること：

- 対応するオープンストリートマップ条件式の文法版とtoken集合
- 境界時刻の包含、夜間をまたぐ範囲、曜日・祝日・日付範囲
- 重量・寸法の単位、論理積・論理和・否定・括弧・セミコロン
- `Asia/Tokyo`での評価期間とsimulation interval
- 日付、時間、holiday、車両、重み、dimensions、trip 目的の必須文脈
- 未対応 syntax、欠落 文脈、期間内変化、競合時の停止コード

必要成果物は、grammar、解析器契約、条件設定プロファイル、祝日暦、正常・異常・境界正解判定器で
ある。

<a id="54-japan-speed-rule-table"></a>

### 5.4 日本速度-規則表

**管理識別子:** `NEXT-DEC-004`\
**既存識別子:** `OPEN-PROP-011`、`DEC-SPEED-001`から`010`\
**現在状態:** `evidence_required`

決めること：

- 2026年7月16日に有効な法令・行政資料と条項
- 指定速度、法定速度、助言速度、simulation 速度の区別
- 道路区分、中央線、車両通行帯、構造分離、車種ごとの決定表
- 数値`maxspeed`、方向-specific 速度、条件付き速度、法令導出の優先順位
- 制度改正時の適用日と設定改版方法

必要成果物は、適用期間付き機械可読速度表、出典台帳、データ構造、境界日検証用データである。

### 5.5 `JP:urban`用道路状態証拠

**管理識別子:** `NEXT-DEC-005`\
**既存識別子:** `OPEN-PROP-012`、`DEC-SPEED-004`、`005`、`009`\
**現在状態:** `evidence_required`

決めること：

- 法令導出に必要な道路状態の必須項目
- オープンストリートマップ、道路管理者資料、道路台帳、画像確認の権威順位
- 証拠の区間、方向、適用日を方向付き区間へ一致させる規則
- 道路状態が欠損または競合する場合の停止コード
- 目視証拠を認める場合の撮影日、位置、方向、確認者、SHA-256

<a id="56-permit-registry"></a>

### 5.6 許可登録簿

**管理識別子:** `NEXT-DEC-006`\
**既存識別子:** `DEC-PERMIT-001`から`010`\
**現在状態:** `not_started`

決めること：

- 許可台帳の管理責任者、版、改訂・失効手順
- 道路、区域、方向、車線、車種、車両、目的、適用期間の必須項目
- `private`、`permit`と具体的な車種別許可タグの評価関係
- 許可なし、期限切れ、対象不一致、競合時の停止規則
- 道路分割後も許可対象を方向付き区間へ追跡する方法

基準車両が特別許可を持たないという固定方針と、背景交通または将来想定条件用の台帳
設計を混同しない。

<a id="57-formal-unpaved-surface-rule"></a>

### 5.7 正式未舗装-路面規則

**管理識別子:** `NEXT-DEC-007`\
**既存識別子:** 新しい規範annexとして登録が必要\
**現在状態:** `evidence_required`

決めること：

- `surface`、`smoothness`、`tracktype`の役割と優先順位
- unpaved判定の対象道路機能、車種、速度・接続への影響
- 欠損、未知値、タグ競合時の停止条件
- 構造上の-only仮定と正式証拠の境界

`highway=track`の範囲除外理由と、舗装状態の判定を混同しない。

<a id="58-production-independent-oracle"></a>

### 5.8 正式運用-独立正解判定器

**管理識別子:** `NEXT-DEC-008`\
**既存識別子:** `OPEN-PROP-015`、`DEC-FIXTURE-001`から`005`\
**現在状態:** `not_started`

決めること：

- 正式運用実装と独立した入力・正解の作成手順
- 正解判定器作成者、レビュー担当者、独立性宣言
- 正常、異常、境界、再実行、規則改訂の必須網羅率
- 入力、正解、規則、出典、成果物一覧のSHA-256固定方法
- 正本改訂時に旧正解判定器を上書きしない版管理方法

<a id="6-production統合前に決める事項"></a>

## 6. 正式運用統合前に決める事項

<a id="61-v17設定とschemaの配置版"></a>

### 6.1 v17設定とデータ構造の配置・版

**管理識別子:** `NEXT-DEC-009`\
**現在状態:** `not_started`

- 各annex、登録簿、想定条件 設定プロファイルの正本パスとデータ構造
- `approved_attribute_resolution_policy_v17.yml`を改版する条件
- v17 道路網-状態 設定の識別子、版、v16との継承関係
- `resolution_status`、`value_origin`、除外 成果物一覧の互換境界
- 正式運用入出力境界ごとの許容データ構造版

<a id="62-vehicle-input-validatorの境界"></a>

### 6.2 車両-入力 検証器の境界

**管理識別子:** `NEXT-DEC-010`\
**現在状態:** `not_started`

- どのコマンド操作、実行器、具体化処理、スーモ入力境界で検証するか
- 設定プロファイル 識別子、vClass、重量、寸法、積載、permit状態の必須項目
- 設定プロファイルと実行時間 入力が不一致の場合の停止コード
- 同一experiment内の車種切替禁止を検査する方法

<a id="63-exclusionと母集団version"></a>

### 6.3 除外と母集団版

**管理識別子:** `NEXT-DEC-011`\
**現在状態:** `drafted`

- `resolution_status=excluded`を追加せず別成果物一覧を使う方針の正式承認先
- 除外 規則 識別子、承認者、承認日、根拠SHA-256のデータ構造
- `input population = governed population + excluded population`の検査方法
- 母集団 版を更新する条件
- `complete=true`と通行許可 completenessの分母
- 具体化 欠落を範囲 除外へ数えない検査

<a id="64-v17-runnerとrun-identity"></a>

### 6.4 v17 実行器と実行 同一性

**管理識別子:** `NEXT-DEC-012`\
**現在状態:** `not_started`

- 実行器のコマンド操作、必須引数、明示実行 識別子、出力ディレクトリ規則
- 不完全実行の原子的破棄または隔離方法
- 入力、設定、データ構造、正解判定器、出力、除外 成果物一覧のハッシュ値 成果物一覧
- v16成果物と出力先を共有しない検査
- rerun、規則改訂、停止解消反復の実行命名規則

<a id="65-独立停止記録review"></a>

### 6.5 独立停止記録確認

**管理識別子:** `NEXT-DEC-013`\
**現在状態:** `not_started`

- 確認対象、標本ではなく全件確認が必要な区分
- 確認者の独立性、承認権限、期限
- 証拠不足、規則不足、実装不具合、承認済み除外の分類基準
- 確認 findingの解消、再実行、再承認手順

<a id="7-attribute-resolution-acceptance前に決める事項"></a>

## 7. 属性解決の受入前に決める事項

**管理識別子:** `NEXT-DEC-014`\
**現在状態:** `drafted`

決めること：

- 受入 成果物一覧のデータ構造、保管先、承認者
- `complete=true`、阻害要因、確認、未解決、正式 `model_assumed`の判定方法
- 母集団、記録、属性、通行許可 網羅率の分母と検査器
- 分類 projection、意味上の consistency、record/self-hash、実行 成果物一覧の
  検証器責務とコマンド操作
- 除外 成果物一覧のハッシュ値、規則登録、母集団 版整合の検査
- 旧版 `value_state`だけの成果物を拒否する検査
- 正式 evidence/imputation未実装時に受入を拒否する検査

このゲートにスーモ 道路区間、車線、接続、信号制御、到達可能性の検査を含めない。

<a id="8-正式道路網build前に決める事項"></a>

## 8. 正式道路網構築前に決める事項

<a id="81-environmentbuild-manifest"></a>

### 8.1 environment/build 成果物一覧

**管理識別子:** `NEXT-DEC-015`\
**現在状態:** `not_started`

- 変更記録、コンテナー ハッシュ値、スーモ版、コマンド、設定・入力・出力ハッシュ値の必須項目
- 基本ソフト、architecture、locale、timezone、依存package、random 乱数の種の記録範囲
- 再現不能な環境差分を検出した場合の停止条件

<a id="82-junction-join-review"></a>

### 8.2 交差点-結合確認

**管理識別子:** `NEXT-DEC-016`\
**現在状態:** `not_started`

- 交差点 join候補を採用・却下する証拠と確認者
- 10 m候補検索後の形状、level、接続、信号確認基準
- 管理対象の ノード ファイルのデータ構造、版、ハッシュ値、再確認条件
- automatic joinを正式 conversionで無効化したことの検査

<a id="83-exact-edge-provenance"></a>

### 8.3 厳密 道路区間 出典・来歴

**管理識別子:** `NEXT-DEC-017`\
**現在状態:** `drafted`

- 道路地物、分割区間、方向付き区間、スーモ 道路区間、車線の一対多関係データ構造
- 出典 ノード lineage 索引と`origId`の必須条件
- 分割・削除・内部道路区間を追跡する方法
- 未対応道路区間、車線、接続を検出した場合の停止コード

<a id="84-permission-materializerとomission-audit"></a>

### 8.4 通行許可の具体化処理と欠落 監査

**管理識別子:** `NEXT-DEC-018`\
**現在状態:** `drafted`

- plain 拡張マークアップ形式入出力、原子的出力、決定的順序、失敗時の処理
- 車線順、空通行許可 set、部分的に空の車線、全車線空道路区間の規則
- 具体化 欠落の理由 コード
- 欠落 監査に必要な出典 道路地物、方向付き区間、属性解決器 組、道路区間、接続、
  設定、通行許可 期待値、具体化処理 出力の各ハッシュ値
- empty 解決済み 通行許可とunresolved/conflictを区別する検査
- pinned スーモ 1.24.0 検証用データの正常、異常、境界正解判定器

<a id="85-final-connection-setとsignaltls-review"></a>

### 8.5 最終接続集合とsignal/TLS 確認

**管理識別子:** `NEXT-DEC-019`\
**現在状態:** `not_started`

- 接続候補の生成責任と、存在しない接続を新規生成しない検査
- 右左折制限 対応付け 監査の対象と合格条件
- 最終 接続 setを固定する成果物とハッシュ値
- 信号 交差点、信号制御 リンク、段階を確認する責任者
- 条件を統制した 接続数と段階-状態長の一致検査
- 接続変更時に確認、較正、検証を無効化する範囲

<a id="86-warningexclusion-audit"></a>

### 8.6 warning/exclusion 監査

**管理識別子:** `NEXT-DEC-020`\
**現在状態:** `not_started`

- スーモ 注意事項の分類、許容可否、根拠、承認者
- 範囲 除外、具体化 欠落、変換注意事項の区別
- 未登録注意事項または未監査除外を検出した場合の停止条件
- 監査 成果物のデータ構造とハッシュ値 binding

<a id="87-structural-quality-threshold"></a>

### 8.7 構造上の品質しきい値

**管理識別子:** `NEXT-DEC-021`\
**現在状態:** `not_started`

- 道路区間、車線、接続、component、dead 終了、到達可能性等の評価指標
- 指標ごとのしきい値と根拠
- 配送拠点、顧客、充電設備、主要道路間の必須到達性集合
- 車種別・方向別の往復到達性条件
- 構築結果を見る前にしきい値を固定するpreregistration手順

<a id="88-immutable-acceptance-artifacts"></a>

### 8.8 変更不可受入成果物

**管理識別子:** `NEXT-DEC-022`\
**現在状態:** `not_started`

- Git管理する小型成果物と外部保管する大容量成果物
- 相互参照するSHA-256、成果物一覧、署名または承認記録
- 最終 `net.xml`、plain 拡張マークアップ形式、出典・来歴、確認、監査、環境 成果物一覧の保管先
- 変更時に新しい道路網 版を発行し下流成果物を無効化する手順

<a id="9-sumo-network-integration-acceptance前に決める事項"></a>

## 9. 交通シミュレーターの道路網統合受入前に決める事項

**管理識別子:** `NEXT-DEC-023`\
**現在状態:** `drafted`

決めること：

- 受入 成果物一覧のデータ構造、承認者、保管先
- typemap governance fixture、materializer fixture、lane/connection audit、turn audit、
  注意事項 監査、quality 判定基準の合格証拠
- 属性解決の受入 成果物を入力として固定する方法
- 管理対象の ノード ファイル、厳密 出典・来歴、最終 接続、信号制御 確認のハッシュ値 binding
- 最終 `net.xml`のスーモ 1.24.0 負荷、left-hand 交通、到達可能性の合格条件
- 不合格時に上流へ戻る工程と、新しいbuild/run 識別子の規則

このゲート合格前に正式 道路網を承認しない。

## 10. 較正・独立検証前に決める事項

### 10.1 需要と観測

**管理識別子:** `NEXT-DEC-024`\
**現在状態:** `evidence_required`

- demandの対象日、時間帯、車種構成、出発地・到着地、経路 choice
- 日本道路交通情報センター等の観測期間、地点、品質条件、欠測処理
- 較正用とindependent 検証用データの事前分割
- 同じ観測を調整と最終評価の両方へ使わない検査

<a id="102-calibration-protocol"></a>

### 10.2 較正 手順

**管理識別子:** `NEXT-DEC-025`\
**現在状態:** `not_started`

- 調整対象パラメーター、探索範囲、固定パラメーター
- 評価指標、しきい値、乱数の種 set、warm-up、replication数
- overfitting防止と停止条件
- 道路網、信号 structure、demand変更時の再較正条件

<a id="103-independent-validation-protocol"></a>

### 10.3 独立検証手順

**管理識別子:** `NEXT-DEC-026`\
**現在状態:** `not_started`

- 較正で未使用の観測集合
- metric、acceptance threshold、seed、confidence interval
- 不合格時にモデル改訂と再検証を分離する方法
- pytest成功を経験分布の 検証として扱わない報告形式

## 11. 正式比較前に決める事項

### 11.1 共通配送問題

**管理識別子:** `NEXT-DEC-027`\
**現在状態:** `not_started`

- 配送拠点、顧客、充電設備、需要、時間枠、車両、電池、積載制約
- 受入済み道路網から生成する距離、旅行時間、電力費用の版
- infeasible 問題例の扱いと修復規則

<a id="112-classicalqaoa比較"></a>

### 11.2 古典計算・量子近似最適化アルゴリズム比較

**管理識別子:** `NEXT-DEC-028`\
**現在状態:** `not_started`

- 全手法に共通する問題例、目的関数、制約、乱数の種、時間・evaluation 予算
- 生の解と修復後の解へ適用する共通評価器
- solution qualityと計算資源を分離する指標
- 古典計算、シミュレーター 量子近似最適化アルゴリズム、将来実機実行の比較範囲
- 統計報告、失敗実行、timeout、欠測の扱い

正式比較へ進めるのはindependent 交通-モデル検証合格後だけである。

## 12. 決定順序と並行可能作業

```text
NEXT-DEC-001..008  v17 normative annexes and oracle
  -> NEXT-DEC-009..014  production contract, runner, attribute acceptance
  -> NEXT-DEC-015..023  reproducible build and network acceptance
  -> NEXT-DEC-024..026  demand, calibration, independent validation
  -> NEXT-DEC-027..028  formal comparison
```

小型検証用データを用いる暫定 構築、通行許可の具体化処理、スーモ 実行時間 検証用データの
開発は、属性停止記録の解消と並行できる。ただし、実データ正式 道路網 受入
は属性解決の受入後、正式比較は独立検証後でなければ実施しない。

## 13. 直近の作業チェックリスト

- [ ] `NEXT-DEC-001`から`008`のownerとapproverを割り当てる。
- [ ] `OPEN-PROP-005`、`009`から`012`、`015`に対応する決定案を作る。
- [ ] 法令・行政資料・祝日暦・許可台帳候補を取得しSHA-256を記録する。
- [ ] 正式 unpaved-surface 規則の新規annex 識別子と管理先を決める。
- [ ] 正式運用-independent 正解判定器の作成者と確認者を分離する。
- [ ] 各決定に必要な正常、異常、境界検証用データ 識別子を割り当てる。
- [ ] 承認後の機械可読設定・データ構造改版計画を作る。
- [ ] `NEXT-DEC-009`以降は上流決定の承認状態を確認して着手する。

最初の完了基準は、`NEXT-DEC-001`から`008`が`approved`または根拠付き
`out_of_scope`となり、正本、設定、データ構造、検証用データ、正解判定器へ反映する作業票が揃う
ことである。
