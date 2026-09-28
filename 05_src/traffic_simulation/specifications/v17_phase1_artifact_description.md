# v17属性解決工程 1 成果物説明書

## 0. 文書の目的

本書は、`ota_ward_attribute_resolution_policy_v17`をリポジトリ上で実装可能な状態へ移行するために作成すべき、以下の6成果物の目的、責任範囲、構成、作成手順および完了条件を定めるものである。

1. 仕様同期表
2. v17 Configuration
3. JSON Schema
4. 登録簿群
5. 意味上の不変条件一覧
6. 差分レビュー報告書

本書は、v17属性解決仕様そのものを再定義するものではない。各成果物が、規範仕様のどの要求を、どの形式で保持・検証・実行するかを説明する補助文書である。

v17属性解決の正本は、単一の仕様書ではなく、規範仕様、machine-readable 設定、ジェイソン形式 データ構造、登録簿、検証用データ、正解判定器、意味上の 検証器、実行成果物一覧および受入成果物の相互整合によって成立する。

---

# 1. 成果物全体の構成

## 1.1 成果物間の関係

```text
v17規範仕様書
  ├─ 1. 仕様同期表
  ├─ 2. v17 Configuration
  ├─ 3. JSON Schema
  ├─ 4. Registry群
  ├─ 5. Semantic Invariant一覧
  └─ 6. 差分レビュー報告書
          ↓
     Phase 1 完了判定
          ↓
 fixture・oracle固定
          ↓
 production implementation
```

## 1.2 責任の分離

| 成果物 | 主な責任 |
|---|---|
| 仕様同期表 | 仕様要求と実装先の対応を追跡する。 |
| 設定 | 当該実行で有効な方針、設定プロファイル、版、登録簿参照、判定基準条件を選択する。 |
| JSON Schema | 成果物の構造、型、必須項目、列挙値および一部のcross-項目制約を機械検証する。 |
| 登録簿群 | 状態、規則、停止コード、車両 概念体系、仮定等の有限語彙と意味を管理する。 |
| 意味上の不変条件一覧 | ジェイソン形式 データ構造だけでは表現しにくい意味上・集合上・母集団上の制約を定義する。 |
| 差分レビュー報告書 | 既存リポジトリとv17仕様との不一致、欠落、旧実装依存を記録する。 |

## 1.3 共通原則

6成果物は以下を共通して満たさなければならない。

- v16成果物を上書きしない。
- v16結果をv17結果として再ラベル付けしない。
- 同一概念に異なる名称・列挙値・規則 識別子を与えない。
- 同じ規則を複数成果物で矛盾して定義しない。
- 版、ハッシュ値および参照先を明示する。
- 未承認事項を暗黙に実装可能扱いしない。
- 正式運用 コードを規範の唯一の保管場所にしない。
- 不一致がある場合は不確実な場合は拒否とする。

---

# 2. 成果物1：仕様同期表

## 2.1 目的

仕様同期表は、v17規範仕様に含まれる各要求が、設定、データ構造、登録簿、検証器、検証用データ、正解判定器および正式運用 コードのどこへ反映されるかを追跡するための追跡可能性 行列である。

本成果物の目的は、以下である。

- 仕様書だけが更新され、機械可読成果物が旧仕様のまま残ることを防ぐ。
- 仕様要求がどこにも実装されない状態を検出する。
- 一つの規則が複数箇所で異なる意味に実装されることを防ぐ。
- 検証用データおよび正解判定器の被覆範囲を確認する。
- Phase 1、Phase 2および実装PRの進捗判定に使用する。

## 2.2 推奨ファイル

```text
05_src/traffic_simulation/specifications/
  v17_attribute_resolution_traceability_matrix.md
```

必要に応じて、機械集計用にコンマ区切り形式またはヤムル形式版を併設してよい。

```text
reproducibility/config/traffic_simulation/
  v17_attribute_resolution_traceability_matrix.csv
```

## 2.3 入力

- `10_approved_attribute_resolution_policy_v17_complete.md`
- 現行`sumo_network.yml`
- 現行ジェイソン形式 データ構造群
- 現行登録簿または規則 table
- 現行意味上の 検証器
- 現行検証用データ・正解判定器
- 現行正式運用 属性解決器実装
- `network_current_specification.md`
- v16 evidence manifest

## 2.4 最小列

| 列 | 内容 |
|---|---|
| `requirement_id` | 一意の要求識別子 |
| `specification_section` | 規範仕様の節番号 |
| `requirement_summary` | 要求の要約 |
| `normative_level` | shall / shall not / should / may |
| `configuration_location` | 設定上の反映先 |
| `schema_location` | データ構造上の反映先 |
| `registry_location` | 登録簿上の反映先 |
| `semantic_validator_location` | 検証器上の検査先 |
| `fixture_ids` | 対応検証用データ |
| `oracle_location` | 期待結果の所在 |
| `production_location` | 正式運用 コード上の実装先 |
| `current_status` | 状態 |
| `evidence` | 変更記録、ハッシュ値、試験 結果等 |
| `owner` | 担当者・役割 |
| `notes` | 留意点 |

<a id="25-要求id体系"></a>

## 2.5 要求識別子体系

要求識別子は、次のように領域別prefixを使用する。

```text
AR-STATE-xxx      状態・由来
AR-ID-xxx         record identity
AR-DIR-xxx        Directed Segment・oneway
AR-LANE-xxx       directional lane
AR-SPEED-xxx      speed
AR-ACCESS-xxx     access
AR-COND-xxx       conditional grammar
AR-EVID-xxx       evidence
AR-EXCL-xxx       exclusion
AR-PROV-xxx       provenance・hash
AR-ACC-xxx        acceptance
AR-TRANS-xxx      v16→v17移行
```

## 2.6 状態値

`current_status`は以下に統一する。

| 状態 | 意味 |
|---|---|
| `not_assessed` | まだ確認していない。 |
| `missing` | 必要成果物が存在しない。 |
| `conflicting` | 仕様と既存成果物が矛盾する。 |
| `partial` | 一部のみ反映されている。 |
| `aligned` | 仕様と一致している。 |
| `not_applicable` | 当該成果物への反映が不要である。 |
| `blocked` | 上流の未決定事項により評価不能である。 |

`implemented`や`passed`だけで表現してはならない。要求によっては、データ構造には反映済みだが検証用データが未作成という状態があるためである。

## 2.7 記入例

| requirement_id | requirement_summary | 設定 | データ構造 | 登録簿 | 検証用データ | 検証器 | Code | 状態 |
|---|---|---|---|---|---|---|---|---|
| AR-STATE-001 | v17 writerは`resolution_status`を出力する。 | 項目指定 | 列挙値定義 | state registry | STATE-001 | cross-field check | serializer | 部分的 |
| AR-DIR-004 | `oneway=-1`は逆方向のみ生成する。 | direction policy | segment enum | oneway rule | DIR-004 | lineage check | 生成器 | 部分的 |
| AR-ACCESS-012 | lane/directionを対象 範囲として扱う。 | access axes | AccessRule Schema | scope registry | ACCESS-012 | scope validator | 属性解決器 | 欠落 |

## 2.8 作成手順

1. 規範仕様のshall／shall notを抽出する。
2. 要求を一つの判定可能な文へ分割する。
3. 各要求に識別子を付与する。
4. 各成果物への反映要否を判定する。
5. リポジトリ上の現在位置を確認する。
6. `current_status`を付与する。
7. 不一致・欠落を差分レビューへ転記する。
8. 確認者が要求の抜けと重複を確認する。

## 2.9 完了条件

- 規範仕様のすべてのmandatory 要件が登録されている。
- 各要求の実装・検証先が特定されている。
- 反映不要の場合は理由が記録されている。
- `missing`、`conflicting`、`blocked`が差分レビューへ転記されている。
- 同じ要求が重複識別子で登録されていない。
- 仕様書のハッシュ値と同期表の対象版が記録されている。

---

<a id="3-成果物2v17-configuration"></a>

# 3. 成果物2：v17 設定

## 3.1 目的

v17 設定は、規範仕様を実行単位で有効化するmachine-readable 状態 正本である。

設定は「規則の意味」を長文で再定義するものではなく、以下を選択・固定する。

- policy ID
- configuration ID
- population version
- active profile
- Schema version
- registry version
- scenario context
- governed vehicle universe
- 構造上の 仮定の有効性
- 受入 判定基準条件
- 入力・出力 成果物の参照
- スーモおよび実行環境の固定条件

## 3.2 推奨ファイル

```text
reproducibility/config/traffic_simulation/
  sumo_network_v17.yml
```

または、既存命名規則を維持して以下とする。

```text
sumo_network.yml
```

ただし、v16 historyを上書きせず、v17 設定 識別子を明示しなければならない。

## 3.3 主な構成

### A. 同一性

```yaml
configuration_id: ota_ward_sumo_network_v17
policy_id: ota_ward_attribute_resolution_policy_v17
population_version: ota_ward_relation_closure_v16
schema_version: 17
```

### B. 設定プロファイル

```yaml
active_profiles:
  - structural
  - formal

profile_policy:
  structural:
    allow_model_assumed: true
    eligible_for_attribute_resolution_acceptance: false
  formal:
    allow_model_assumed: false
    eligible_for_attribute_resolution_acceptance: true
```

<a id="c-resolution-contract"></a>

### C. 解決取り決め

```yaml
resolution_contract:
  status_field: resolution_status
  origin_field: value_origin
  legacy_read_field: value_state
  legacy_write_allowed: false
```

### D. 方向

```yaml
direction_model:
  representation: directed_segment
  preserve_source_way: true
  allow_source_way_reversal: false
  direction_evidence:
    - exact_source_node_lineage
```

<a id="e-lane"></a>

### E. 車線

```yaml
lane_resolution:
  source_lane_order: left_to_right_in_travel_direction
  sumo_lane_index_formula: "n - 1 - p"
  formal_even_split_allowed: false
  structural_assumption_ids:
    - BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1
```

### F. 通行

```yaml
access_resolution:
  target_scope_dimensions:
    - direction
    - lane
  specificity_axes:
    - spatial
    - vehicle
    - temporal
    - purpose
  maximal_rule_conflict_policy: stop
  conflict_stop_code: ACCESS_SPECIFICITY_CONFLICT
```

<a id="g-registry参照"></a>

### G. 登録簿参照

```yaml
registries:
  state_origin:
  stop_codes:
  oneway_rules:
  vehicle_ontology:
  access_values:
  conditional_grammar:
  assumptions:
  japan_speed_rules:
  evidence_methods:
  exclusions:
```

各参照には保存先、版、SHA-256を持たせる。

### H. 受入

```yaml
attribute_resolution_acceptance:
  require_complete: true
  maximum_blockers: 0
  maximum_review_required: 0
  maximum_stop_unresolved: 0
  maximum_model_assumed: 0
  require_schema_validation: true
  require_semantic_validation: true
  require_oracle_validation: true
  require_classification_projection_invariance: true
  require_two_run_determinism: true
```

<a id="34-configurationへ記載しないもの"></a>

## 3.4 設定へ記載しないもの

以下は設定へ長文で再定義しない。

- `resolved`の意味
- `oneway=-1`の意味論
- Pareto dominanceの数学的説明
- 停止コードの詳細なremediation
- 検証用データの期待出力
- validation implementation

これらは仕様書、登録簿、データ構造、正解判定器、検証器へ分離する。

## 3.5 作成手順

1. v16 設定を複製せず、lineageを明示してv17 設定を作成する。
2. v17仕様で確定した項目、設定プロファイル、登録簿参照を追加する。
3. v16固有の通行許可の正本をv17で無効化する。
4. 道路種別の対応表 通行許可を正式 正本として参照していないことを確認する。
5. 設定 データ構造を更新する。
6. cross-項目 検証器を更新する。
7. ハッシュ値を計算し、成果物一覧へ登録する。

## 3.6 完了条件

- 設定 識別子がv17として一意である。
- v16 設定を変更していない。
- v17 方針 識別子、データ構造、登録簿 版が明示されている。
- 構造上の／正式の差が機械可読である。
- 接続 対象 範囲とspecificity axesが分離されている。
- 受入 判定基準条件が機械可読である。
- 設定自身がデータ構造および意味上の 検証を通過する。

---

<a id="4-成果物3json-schema"></a>

# 4. 成果物3：ジェイソン形式 データ構造

## 4.1 目的

ジェイソン形式 データ構造は、v17 成果物の構造、型、列挙値、必須 項目および表現可能な一部のcross-項目 constraintを機械的に検証するものである。

ジェイソン形式 データ構造は、意味上のすべての妥当性を保証するものではない。集合包含、母集団整合、ハッシュ値不変性、出典 lineage等はSemantic 検証器で検査する。

<a id="42-必須schema群"></a>

## 4.2 必須データ構造群

少なくとも以下を作成・更新する。

```text
attribute_resolution_record_v17.schema.json
directed_segment_v17.schema.json
access_rule_v17.schema.json
exclusion_manifest_v17.schema.json
materialization_omission_v17.schema.json
environment_build_manifest_v17.schema.json
attribute_resolution_acceptance_v17.schema.json
sumo_network_v17.schema.json
```

<a id="43-resolver-record-schema"></a>

## 4.3 属性解決器 記録 データ構造

必須項目は、少なくとも以下である。

```text
schema_version
configuration_id
population_version
profile
record_id
classification_record_id
source_way_id
directed_segment_id
source_direction
lane_position
vehicle_class
attribute_name
source_observations
resolution_status
value_origin
effective_value
rule_ids
evidence_ids
assumption_ids
stop_code
review_required
provenance
```

## 4.4 列挙値

### resolution_status

```text
resolved
unresolved
conflict
invalid
valid_but_unsupported
```

### value_origin

```text
source_explicit
source_normalized
rule_derived
evidence_derived
derived_validated_model
model_assumed
null
```

### source_direction

```text
forward
backward
null
```

<a id="profile"></a>

### 設定プロファイル

```text
structural
formal
```

<a id="45-json-schemaで表現するcross-field条件"></a>

## 4.5 ジェイソン形式データ構造で表現するcross-項目条件

<a id="resolved-record"></a>

### 解決済み 記録

- `effective_value`はnull不可である。
- `value_origin`はnull不可である。
- `stop_code`はnullである。

<a id="non-resolved-record"></a>

### non-解決済み記録

- `effective_value`はnullである。
- `value_origin`はnullである。
- `stop_code`はnull不可である。

<a id="formal-record"></a>

### 正式 記録

- `value_origin=model_assumed`を禁止する。
- `assumption_ids`は空配列である。

<a id="conflict-record"></a>

### 矛盾 記録

- conflicting 候補配列を必須にする。

<a id="directed-segment"></a>

### 方向付き区間

- `source_start_index < source_end_index`自体は意味上の 検証器で検査する。
- `source_direction`は順方向または逆方向である。
- 識別子 patternを正規表現で制約する。

<a id="46-json-schemaだけでは扱わない条件"></a>

## 4.6 ジェイソン形式 データ構造だけでは扱わない条件

以下はSemantic 検証器へ委譲する。

- `record_id`のSHA-256再計算一致
- RFC 8785 canonicalization
- source node lineage
- 出典 道路地物不変性
- 車両 概念体系の集合包含
- rule dominance
- lane count equation
- population equation
- fixture coverage
- 分類 projection ハッシュ値不変性
- two-run determinism
- 登録簿参照の意味的一致

<a id="47-schema-test"></a>

## 4.7 データ構造 試験

各データ構造について、次を用意する。

- minimum valid fixture
- full valid fixture
- missing required field
- invalid enum
- invalid null
- resolved/non-resolved invariant violation
- formal/model_assumed violation
- unexpected 項目の扱い
- 重複 キー rejectionは解析器層で実施

## 4.8 完了条件

- 全有効 検証用データが通過する。
- 全負 検証用データが期待どおり失敗する。
- v17 writer出力に`value_state`が存在しない。
- 列挙値が仕様・登録簿・設定と一致する。
- データ構造 版とSHA-256が記録されている。
- データ構造で表現できない条件が意味上の不変条件一覧へ漏れなく転記されている。

---

<a id="5-成果物4registry群"></a>

# 5. 成果物4：登録簿群

## 5.1 目的

登録簿群は、正式運用 コード内へ埋め込むべきでない有限語彙、規則、概念体系、仮定および配送地点 条件を、versioned machine-readable 成果物として管理する。

登録簿を分離する目的は以下である。

- magic 値を排除する。
- 規則追加・変更を追跡可能にする。
- 検証用データと停止コードを対応付ける。
- 設定ごとに使用する規則 版を固定する。
- 実装とは独立して規範的語彙を確認できるようにする。

<a id="52-必須registry"></a>

## 5.2 必須登録簿

<a id="521-stateorigin-registry"></a>

### 5.2.1 状態／由来登録簿

管理対象：

- `resolution_status`
- `value_origin`
- formal eligibility
- legacy `value_state` mapping

最低項目：

```yaml
value:
definition:
formal_eligible:
allowed_profiles:
legacy_mappings:
```

<a id="522-stop-code-registry"></a>

### 5.2.2 停止-コード登録簿

最低項目：

```yaml
stop_code:
trigger_condition:
applicable_attributes:
resolution_status:
review_required:
permitted_remediation:
fixture_ids:
```

未登録停止コードは正式 阻害要因である。

<a id="523-oneway-rule-registry"></a>

### 5.2.3 一方通行規則登録簿

管理対象：

- explicit normalization
- implicit one-way
- ordinary-road default
- 未対応・不正判定
- deterministic priority

最低項目：

```yaml
rule_id:
priority:
predicate:
canonical_value:
value_origin:
stop_code:
evidence:
```

<a id="524-vehicle-ontology-registry"></a>

### 5.2.4 車両概念体系登録簿

管理対象：

- governed SUMO vClass
- OSM transport mode
- parent-child relationship
- explicit domain set
- non-governed class
- managed vehicle mapping

文字列類似ではなく、登録済み集合関係によってspecificityを評価する。

<a id="525-access-value-registry"></a>

### 5.2.5 通行-値登録簿

各接続 値について以下を持つ。

```yaml
source_value:
normalized_effect:
required_context:
authorization_requirement:
supported:
unsupported_status:
stop_code:
```

<a id="526-conditional-grammar-registry"></a>

### 5.2.6 条件付き文法登録簿

管理対象：

- clause separator
- 演算子
- weekday
- time interval
- date interval
- public holiday
- mass・dimension predicate
- 目的
- permit
- unsupported token

grammar 版とtoken 登録簿 ハッシュ値を固定する。

<a id="527-assumption-registry"></a>

### 5.2.7 仮定登録簿

構造上の-only 仮定を管理する。

最低項目：

```yaml
assumption_id:
affected_attribute:
applicability_predicate:
generated_value_rule:
prohibited_source_conditions:
allowed_profiles:
approver:
approval_date:
configuration_version:
fixture_ids:
```

<a id="528-japan-speed-rule-registry"></a>

### 5.2.8 日本速度-規則登録簿

管理対象：

- explicit symbolic value
- absent maxspeed
- road class
- 文脈
- effective km/h
- 根拠
- 版
- applicability boundary

<a id="529-evidence-method-registry"></a>

### 5.2.9 根拠 手法 登録簿

正式補完を将来有効化する場合に使用する。

承認済み手法が存在しない限り、`evidence_derived`または`derived_validated_model`を正式運用 出力してはならない。

<a id="5210-exclusion-rule-registry"></a>

### 5.2.10 除外規則登録簿

管理対象：

- 管理対象の 母集団から除外可能な条件
- 理由
- population impact
- approval
- 根拠
- versioning requirement

<a id="53-registry共通構造"></a>

## 5.3 登録簿共通構造

各登録簿は以下を持つ。

```yaml
registry_id:
schema_version:
registry_version:
policy_id:
effective_from:
entries:
approver:
approved_at:
source_references:
```

登録簿 成果物全体および各入口についてstable 識別子を付与する。

## 5.4 作成手順

1. 仕様書に現れる列挙値、規則 識別子、停止コード、仮定 識別子を抽出する。
2. 現行コード・ヤムル形式・軽量マークアップ文書内の既存値を収集する。
3. 重複、別名、deprecated 値を整理する。
4. 正本 値を決定する。
5. 各入口に意味・trigger・remediation・検証用データを付与する。
6. 登録簿 データ構造を作成する。
7. 意味上の 検証器から登録簿参照を行う。
8. 設定に登録簿 保存先、版、ハッシュ値を登録する。

## 5.5 完了条件

- 仕様書に登場する全識別子が登録簿へ登録されている。
- 正式運用 コード固有の未登録magic 値がない。
- deprecated 値の扱いが明示されている。
- 検証用データと停止コードの対応が存在する。
- 設定が使用登録簿を一意に参照する。
- 登録簿の変更によりハッシュ値が変化する。
- unregistered 規則、状態、停止コードを検証器が拒否する。

---

<a id="6-成果物5semantic-invariant一覧"></a>

# 6. 成果物5：意味上の不変条件一覧

## 6.1 目的

意味上の不変条件一覧は、ジェイソン形式 データ構造だけでは十分に表現できない、意味上、集合上、母集団上および出典・来歴上の制約を定義する。

本成果物は、仕様書の自然言語要求を、意味上の 検証器で実装可能な判定単位へ分解したものである。

## 6.2 推奨ファイル

```text
05_src/traffic_simulation/specifications/
  v17_semantic_invariants.md
```

機械可読版を併設する場合：

```text
reproducibility/config/traffic_simulation/
  v17_semantic_invariants.yml
```

<a id="63-invariantの最小構造"></a>

## 6.3 不変条件の最小構造

```yaml
invariant_id:
name:
scope:
precondition:
assertion:
failure_status:
stop_code:
severity:
fixture_ids:
validator_location:
```

<a id="64-必須invariant群"></a>

## 6.4 必須不変条件群

<a id="a-state-contract"></a>

### A. 状態取り決め

- 解決済みならeffective 値と出発地が存在する。
- non-解決済みならeffective 値と出発地がnullである。
- 正式 記録に`model_assumed`が存在しない。
- 正式 記録に仮定 識別子が存在しない。
- v17 writer 出力に`value_state`が存在しない。
- 停止コードは登録簿に存在する。

<a id="b-record-identity"></a>

### B. 記録 同一性

- 記録-キー 対象のRFC 8785 正本 ジェイソン形式からSHA-256を再計算し、`record_id`と一致する。
- mutable 項目は同一性 ハッシュ値に含めない。
- `classification_record_id`は解決によって変更されない。
- 重複 記録 識別子が存在しない。

<a id="c-directed-segment"></a>

### C. 方向付き区間

- 出典 start 索引は出典 終了 索引より小さい。
- 索引は出典 道路地物 ノード配列の範囲内である。
- forward/backwardは同じ正本 intervalを参照する。
- `oneway=-1`は逆方向のみを生成する。
- 出典 道路地物 ハッシュ値は処理前後で不変である。
- スーモ 道路区間 識別子の符号は方向根拠に使われていない。
- 関係 対応付け 候補数に応じてunique／欠落／ambiguousを判定する。

<a id="d-lane"></a>

### D. 車線

- one-道路地物の有効 方向と車線 allocationが一致する。
- 合計 車線 件数と方向別 件数の和が一致する。
- 車線 vector長と方向別 車線 件数が一致する。
- 正式処理設定でeven splitが使われていない。
- 構造上の even splitは登録条件をすべて満たす。
- `sumo_index = n - 1 - p`が成立する。

<a id="e-speed"></a>

### E. 速度

- km/hからm/sへの変換が正しい。
- 方向別 asymmetric 速度を保持する。
- symbolic 値は速度 登録簿に存在する。
- lower-優先順位 出典がhigher-優先順位 出典を上書きしていない。
- within-interval changeを平均していない。

### F. 通行

- direction/lane 範囲外の組に規則を適用していない。
- 車両 領域は概念体系の明示集合である。
- dominated 規則がmaximal setに残っていない。
- maximal 規則が異なるeffectを持つ場合に停止している。
- independent 記録 順序を変えても結果が不変である。
- same-結果 maximal 規則の出典・来歴が保持される。
- 道路種別の対応表 通行許可が正式 正本になっていない。

### G. 条件付き

- 必須 文脈欠損を偽として扱っていない。
- 未対応 syntaxを無視していない。
- 同一条件付き 属性タグ内だけlast-matchを適用している。
- 独立属性タグ間の競合を出典 順序で解決していない。
- within-interval 通行許可 changeを検出する。

<a id="h-evidence"></a>

### H. 根拠

- approved 手法以外から`evidence_derived`を出力していない。
- 属性提供元が正式 対象条件を満たすである。
- 属性提供元に構造上の 仮定がない。
- manual 根拠が別成果物として登録されている。
- 正式運用 出力を直接編集していない。

### I. 母集団

- `input = governed + excluded`が成立する。
- 除外 規則が登録簿に存在する。
- 具体化 欠落を除外として数えていない。
- omitted 道路区間の元組が通行許可 分母に残る。
- 母集団 版と除外 成果物一覧が一致する。

<a id="j-provenancedeterminism"></a>

### J. 出典・来歴・決定性

- 必須 ハッシュ値がすべて記録されている。
- RFC 8785 正規化が適用される。
- 重複 ジェイソン形式 キーが拒否される。
- 同一環境・入力・コマンドの2回実行でハッシュ値が一致する。
- 構造上の 成果物と正式 成果物の出力先が分離される。

### K. 受入

- `complete=true`の定義をすべて満たす。
- 阻害要因、review_required、配送地点、model_assumedがゼロである。
- 分類 projection ハッシュ値が不変である。
- 検証用データ・正解判定器 検証が通過している。
- 正式 成果物にnon-解決済み 記録がない。

## 6.5 作成手順

1. 規範仕様のcross-項目、集合、順序、母集団に関する要求を抽出する。
2. 一つの真偽値判定に分解する。
3. invariant 識別子を付与する。
4. 不具合時の状況・停止コードを割り当てる。
5. 検証用データ 識別子を割り当てる。
6. 検証器実装予定位置を記録する。
7. ジェイソン形式 データ構造との重複を確認する。
8. 同じ条件をデータ構造と検証器で矛盾して定義していないか確認する。

## 6.6 完了条件

- 仕様書の意味的要求がすべて登録されている。
- 各invariantが判定可能な文になっている。
- 不具合時の処理が明示されている。
- 対応検証用データが存在する、または作成計画が登録されている。
- データ構造で検証する条件と意味上の 検証器で検証する条件が分離されている。
- 受入 判定基準が参照するinvariantが明示されている。

---

# 7. 成果物6：差分レビュー報告書

## 7.1 目的

差分レビュー報告書は、完成したv17規範仕様と、既存リポジトリに存在する設定、データ構造、登録簿、検証器、検証用データ、正解判定器および正式運用 コードとの差異を記録する成果物である。

本成果物は修正後の仕様ではなく、Phase 1開始時点の実装状況およびPhase 1完了時点の残差を示す。

## 7.2 推奨ファイル

```text
05_src/traffic_simulation/
  v17_authority_synchronization_review.md
```

## 7.3 差分分類

| 差分種別 | 意味 |
|---|---|
| `missing_artifact` | 必要成果物が存在しない。 |
| `missing_field` | 必須項目が存在しない。 |
| `legacy_only` | v16表現だけが存在する。 |
| `enum_conflict` | 列挙値が仕様と一致しない。 |
| `semantic_conflict` | 実装意味が仕様と異なる。 |
| `authority_conflict` | 正式 正本が誤った成果物に置かれている。 |
| `unregistered_rule` | コード・検証用データで未登録規則が使用されている。 |
| `fixture_gap` | 必須事例の検証用データがない。 |
| `oracle_gap` | 独立正解判定器がない。 |
| `validator_gap` | 意味上の checkがない。 |
| `evidence_gap` | ハッシュ値、成果物一覧、実行時間 根拠がない。 |
| `obsolete_v16_behavior` | v17で廃止すべきv16挙動が残る。 |
| `documentation_only` | 文書上のみ存在し、機械成果物へ未反映である。 |

## 7.4 レビュー対象

最低限、以下を確認する。

- `sumo_network.yml`
- configuration Schema
- attribute classification Schema
- attribute resolution Schema
- Directed Segment Schema
- AccessRule表現
- semantic validator
- 状態／停止コード定義
- 一方通行処理
- lane resolution
- access specificity utility
- conditional parser
- speed resolution
- 検証用データ
- 正解判定器
- evidence manifest
- acceptance gate
- network current specification

## 7.5 差分記録形式

| 項目 | 内容 |
|---|---|
| `finding_id` | 一意の差分識別子 |
| `requirement_id` | 対応する仕様要求 |
| `category` | 差分種別 |
| `repository_location` | file、class、function、range |
| `current_behavior` | 現状 |
| `required_behavior` | v17仕様 |
| `impact` | 影響 |
| `severity` | critical / major / minor |
| `recommended_action` | 修正方針 |
| `target_phase` | Phase 1、2、3以降 |
| `owner` | 担当 |
| `status` | open / planned / resolved / accepted_exception |
| `evidence` | commit、test、hash |

<a id="76-severity"></a>

## 7.6 重大度

### 重大

- v16成果物を書き換える。
- 出典 オープンストリートマップまたは生成済み `net.xml`を直接編集する。
- `model_assumed`を正式に使用する。
- 未解決 記録を具体化する。
- 道路種別の対応表 通行許可をv17 正式 正本とする。
- `oneway=-1`を誤方向へ生成する。
- 受入を証拠なしで合格とする。

### 主要

- データ構造／登録簿／設定の不一致。
- 必須 検証用データ・正解判定器の欠落。
- 対象 範囲とspecificityの混同。
- state/origin 取り決め未移行。
- 停止コード未登録。
- 意味上の 検証器欠落。

### 軽微

- 説明文の不足。
- naming inconsistency。
- non-normative 付随情報の欠落。
- 参照保存先の整理不足。

## 7.7 レビュー手順

1. 仕様同期表を基準にリポジトリを調査する。
2. 各要求について現状の実装・成果物を確認する。
3. `aligned`以外をfindingとして登録する。
4. 重大度を付与する。
5. Phase 1で解消する項目と、Phase 2以降へ送る項目を分ける。
6. Phase 1修正後に再レビューする。
7. 未解決 重大な findingがないことを確認する。
8. Phase 1 完了判定 記録を作成する。

## 7.8 工程 1で解消すべき差分

Phase 1では、少なくとも以下を解消する。

- 設定のv17化
- データ構造 列挙値・項目の同期
- 登録簿の作成
- 意味上の invariantの定義
- v16／v17 正本の分離
- `resolution_status`／`value_origin`の規範上の一致
- 方向付き区間 識別子・方向 規則の一致
- 対象 範囲／specificity axesの一致
- 構造上の／正式処理設定の一致
- 受入 判定基準 条件の一致

以下は、Phase 2以降の実装課題として残ってよい。

- 正式運用 コードの全面統合
- 全検証用データ・正解判定器の実行成功
- full-population run
- 配送地点 記録の解消
- 属性解決の受入
- 通行許可の具体化処理
- 交通シミュレーターの道路網統合受入

## 7.9 完了条件

- 仕様同期表上の`conflicting`がゼロである。
- 未解決 重大な findingがゼロである。
- Phase 1対象の主要な findingがゼロである。
- Phase 2以降へ送るfindingに対象 段階とownerがある。
- v16／v17の正本境界が明記されている。
- 修正済み成果物の変更記録およびハッシュ値が記録されている。
- 確認者がPhase 1 完了判定を承認している。

---

# 8. 6成果物の作成順序

推奨順序は以下である。

```text
1. 仕様同期表の初版を作る
2. 差分レビューの初回調査を行う
3. v17 Configurationを作る
4. JSON Schemaを作る
5. Registry群を作る
6. Semantic Invariant一覧を作る
7. Configuration・Schema・Registryを再同期する
8. 差分レビューを更新する
9. 仕様同期表を最終更新する
10. Phase 1完了判定を行う
```

番号上は差分レビューが成果物6であるが、作業上は初期調査と最終確認の二回使用する。

---

# 9. 工程 1 完了判定

以下をすべて満たした場合に、6成果物の作成が完了したと判定する。

```text
[ ] 仕様同期表が全mandatory requirementを含む
[ ] v17 Configurationが作成されている
[ ] v17 ConfigurationがSchema・semantic validationを通過する
[ ] 必須JSON Schema群が作成されている
[ ] Registry群が作成されている
[ ] Semantic Invariant一覧が作成されている
[ ] 差分レビューのcritical findingがゼロである
[ ] Phase 1対象のmajor findingがゼロである
[ ] v16成果物が変更されていない
[ ] v17出力先がv16から分離されている
[ ] 仕様、configuration、Schema、registryのenumが一致する
[ ] unresolved normative decisionが残っていない
[ ] Phase 2で作成するfixture・oracleの対象が確定している
[ ] 各成果物のversionとSHA-256が記録されている
```

Phase 1の完了は、正式運用 実装または属性解決の受入の完了を意味しない。

---

# 10. 工程 1 完了後の次工程

Phase 1完了後は、以下へ進む。

## 工程 2

- independent 検証用データ作成
- 正式運用-independent 正解判定器作成
- 検証用データ author・確認者記録
- 配送地点-コード 網羅率確認
- metamorphic 試験設計

## 工程 3

- `resolution_status`／`value_origin` migration
- legacy reader
- v17 writer
- 意味上の 検証器実装

## 工程 4以降

- 方向付き区間 正式運用統合
- directional lane resolution
- access normalization
- conditional evaluation
- final permission resolution
- speed resolution
- full-population run
- 属性解決の受入

---

# 11. 成果物一覧

| No. | 成果物 | 推奨形式 | Phase 1での目的 |
|---:|---|---|---|
| 1 | 仕様同期表 | Markdown＋CSV | 仕様要求と実装先を対応付ける。 |
| 2 | v17 Configuration | ヤムル形式 | 実行で有効な方針・設定プロファイル・登録簿・判定基準を固定する。 |
| 3 | JSON Schema | ジェイソン形式 | 成果物構造と基本制約を検証する。 |
| 4 | 登録簿群 | YAML／JSON | 有限語彙、規則、概念体系、仮定を管理する。 |
| 5 | 意味上の不変条件一覧 | Markdown＋YAML | 意味上の検証条件を定義する。 |
| 6 | 差分レビュー報告書 | 軽量マークアップ文書 | 既存リポジトリとの不一致を管理する。 |

本書により、v17規範仕様を、実装可能かつ第三者が監査可能なmachine-readable 正本へ展開するための成果物構成と完了条件を固定する。
