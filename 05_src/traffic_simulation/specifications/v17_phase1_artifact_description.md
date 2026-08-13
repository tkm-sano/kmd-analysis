# v17属性解決 Phase 1 成果物説明書

## 0. 文書の目的

本書は、`ota_ward_attribute_resolution_policy_v17`をrepository上で実装可能な状態へ移行するために作成すべき、以下の6成果物の目的、責任範囲、構成、作成手順および完了条件を定めるものである。

1. 仕様同期表
2. v17 Configuration
3. JSON Schema
4. Registry群
5. Semantic Invariant一覧
6. 差分レビュー報告書

本書は、v17属性解決仕様そのものを再定義するものではない。各成果物が、規範仕様のどの要求を、どの形式で保持・検証・実行するかを説明する補助文書である。

v17属性解決のauthorityは、単一の仕様書ではなく、規範仕様、machine-readable configuration、JSON Schema、registry、fixture、oracle、semantic validator、実行manifestおよび受入artifactの相互整合によって成立する。

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
| Configuration | 当該runで有効なpolicy、profile、version、registry参照、gate条件を選択する。 |
| JSON Schema | artifactの構造、型、必須項目、enumおよび一部のcross-field制約を機械検証する。 |
| Registry群 | 状態、rule、stop code、vehicle ontology、assumption等の有限語彙と意味を管理する。 |
| Semantic Invariant一覧 | JSON Schemaだけでは表現しにくい意味上・集合上・母集団上の制約を定義する。 |
| 差分レビュー報告書 | 既存repositoryとv17仕様との不一致、欠落、旧実装依存を記録する。 |

## 1.3 共通原則

6成果物は以下を共通して満たさなければならない。

- v16成果物を上書きしない。
- v16結果をv17結果として再ラベル付けしない。
- 同一概念に異なる名称・enum・rule IDを与えない。
- 同じ規則を複数成果物で矛盾して定義しない。
- version、hashおよび参照先を明示する。
- 未承認事項を暗黙に実装可能扱いしない。
- production codeを規範の唯一の保管場所にしない。
- 不一致がある場合はfail-closedとする。

---

# 2. 成果物1：仕様同期表

## 2.1 目的

仕様同期表は、v17規範仕様に含まれる各要求が、configuration、Schema、registry、validator、fixture、oracleおよびproduction codeのどこへ反映されるかを追跡するためのtraceability matrixである。

本成果物の目的は、以下である。

- 仕様書だけが更新され、機械可読成果物が旧仕様のまま残ることを防ぐ。
- 仕様要求がどこにも実装されない状態を検出する。
- 一つの規則が複数箇所で異なる意味に実装されることを防ぐ。
- fixtureおよびoracleの被覆範囲を確認する。
- Phase 1、Phase 2および実装PRの進捗判定に使用する。

## 2.2 推奨ファイル

```text
05_src/traffic_simulation/specifications/
  v17_attribute_resolution_traceability_matrix.md
```

必要に応じて、機械集計用にCSVまたはYAML版を併設してよい。

```text
reproducibility/config/traffic_simulation/
  v17_attribute_resolution_traceability_matrix.csv
```

## 2.3 入力

- `10_approved_attribute_resolution_policy_v17_complete.md`
- 現行`sumo_network.yml`
- 現行JSON Schema群
- 現行registryまたはrule table
- 現行semantic validator
- 現行fixture・oracle
- 現行production Resolver実装
- `network_current_specification.md`
- v16 evidence manifest

## 2.4 最小列

| 列 | 内容 |
|---|---|
| `requirement_id` | 一意の要求ID |
| `specification_section` | 規範仕様の節番号 |
| `requirement_summary` | 要求の要約 |
| `normative_level` | shall / shall not / should / may |
| `configuration_location` | configuration上の反映先 |
| `schema_location` | Schema上の反映先 |
| `registry_location` | registry上の反映先 |
| `semantic_validator_location` | validator上の検査先 |
| `fixture_ids` | 対応fixture |
| `oracle_location` | 期待結果の所在 |
| `production_location` | production code上の実装先 |
| `current_status` | 状態 |
| `evidence` | commit、hash、test result等 |
| `owner` | 担当者・役割 |
| `notes` | 留意点 |

## 2.5 要求ID体系

要求IDは、次のように領域別prefixを使用する。

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

`implemented`や`passed`だけで表現してはならない。要求によっては、Schemaには反映済みだがfixtureが未作成という状態があるためである。

## 2.7 記入例

| requirement_id | requirement_summary | Configuration | Schema | Registry | Fixture | Validator | Code | Status |
|---|---|---|---|---|---|---|---|---|
| AR-STATE-001 | v17 writerは`resolution_status`を出力する。 | field指定 | enum定義 | state registry | STATE-001 | cross-field check | serializer | partial |
| AR-DIR-004 | `oneway=-1`はbackwardのみ生成する。 | direction policy | segment enum | oneway rule | DIR-004 | lineage check | generator | partial |
| AR-ACCESS-012 | lane/directionをtarget scopeとして扱う。 | access axes | AccessRule Schema | scope registry | ACCESS-012 | scope validator | resolver | missing |

## 2.8 作成手順

1. 規範仕様のshall／shall notを抽出する。
2. 要求を一つの判定可能な文へ分割する。
3. 各要求にIDを付与する。
4. 各成果物への反映要否を判定する。
5. repository上の現在位置を確認する。
6. `current_status`を付与する。
7. 不一致・欠落を差分レビューへ転記する。
8. reviewerが要求の抜けと重複を確認する。

## 2.9 完了条件

- 規範仕様のすべてのmandatory requirementが登録されている。
- 各要求の実装・検証先が特定されている。
- 反映不要の場合は理由が記録されている。
- `missing`、`conflicting`、`blocked`が差分レビューへ転記されている。
- 同じ要求が重複IDで登録されていない。
- 仕様書のhashと同期表の対象versionが記録されている。

---

# 3. 成果物2：v17 Configuration

## 3.1 目的

v17 Configurationは、規範仕様をrun単位で有効化するmachine-readable state authorityである。

Configurationは「規則の意味」を長文で再定義するものではなく、以下を選択・固定する。

- policy ID
- configuration ID
- population version
- active profile
- Schema version
- registry version
- scenario context
- governed vehicle universe
- structural assumptionの有効性
- acceptance gate条件
- input・output artifactの参照
- SUMOおよび実行環境の固定条件

## 3.2 推奨ファイル

```text
reproducibility/config/traffic_simulation/
  sumo_network_v17.yml
```

または、既存命名規則を維持して以下とする。

```text
sumo_network.yml
```

ただし、v16 historyを上書きせず、v17 configuration IDを明示しなければならない。

## 3.3 主な構成

### A. Identity

```yaml
configuration_id: ota_ward_sumo_network_v17
policy_id: ota_ward_attribute_resolution_policy_v17
population_version: ota_ward_relation_closure_v16
schema_version: 17
```

### B. Profile

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

### C. Resolution contract

```yaml
resolution_contract:
  status_field: resolution_status
  origin_field: value_origin
  legacy_read_field: value_state
  legacy_write_allowed: false
```

### D. Direction

```yaml
direction_model:
  representation: directed_segment
  preserve_source_way: true
  allow_source_way_reversal: false
  direction_evidence:
    - exact_source_node_lineage
```

### E. Lane

```yaml
lane_resolution:
  source_lane_order: left_to_right_in_travel_direction
  sumo_lane_index_formula: "n - 1 - p"
  formal_even_split_allowed: false
  structural_assumption_ids:
    - BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1
```

### F. Access

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

### G. Registry参照

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

各参照にはpath、version、SHA-256を持たせる。

### H. Acceptance

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

## 3.4 Configurationへ記載しないもの

以下はConfigurationへ長文で再定義しない。

- `resolved`の意味
- `oneway=-1`の意味論
- Pareto dominanceの数学的説明
- stop codeの詳細なremediation
- fixtureの期待出力
- validation implementation

これらは仕様書、registry、Schema、oracle、validatorへ分離する。

## 3.5 作成手順

1. v16 configurationを複製せず、lineageを明示してv17 configurationを作成する。
2. v17仕様で確定したfield、profile、registry参照を追加する。
3. v16固有のpermission authorityをv17で無効化する。
4. typemap permissionをformal authorityとして参照していないことを確認する。
5. configuration Schemaを更新する。
6. cross-field validatorを更新する。
7. hashを計算し、manifestへ登録する。

## 3.6 完了条件

- configuration IDがv17として一意である。
- v16 configurationを変更していない。
- v17 policy ID、Schema、registry versionが明示されている。
- structural／formalの差が機械可読である。
- access target scopeとspecificity axesが分離されている。
- acceptance gate条件が機械可読である。
- configuration自身がSchemaおよびsemantic validationを通過する。

---

# 4. 成果物3：JSON Schema

## 4.1 目的

JSON Schemaは、v17 artifactの構造、型、enum、required fieldおよび表現可能な一部のcross-field constraintを機械的に検証するものである。

JSON Schemaは、意味上のすべての妥当性を保証するものではない。集合包含、母集団整合、hash不変性、source lineage等はSemantic Validatorで検査する。

## 4.2 必須Schema群

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

## 4.3 Resolver record Schema

必須fieldは、少なくとも以下である。

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

## 4.4 Enum

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

### profile

```text
structural
formal
```

## 4.5 JSON Schemaで表現するcross-field条件

### resolved record

- `effective_value`はnull不可である。
- `value_origin`はnull不可である。
- `stop_code`はnullである。

### non-resolved record

- `effective_value`はnullである。
- `value_origin`はnullである。
- `stop_code`はnull不可である。

### formal record

- `value_origin=model_assumed`を禁止する。
- `assumption_ids`は空配列である。

### conflict record

- conflicting candidate配列を必須にする。

### Directed Segment

- `source_start_index < source_end_index`自体はsemantic validatorで検査する。
- `source_direction`はforwardまたはbackwardである。
- ID patternを正規表現で制約する。

## 4.6 JSON Schemaだけでは扱わない条件

以下はSemantic Validatorへ委譲する。

- `record_id`のSHA-256再計算一致
- RFC 8785 canonicalization
- source node lineage
- source Way不変性
- vehicle ontologyの集合包含
- rule dominance
- lane count equation
- population equation
- fixture coverage
- classification projection hash不変性
- two-run determinism
- registry参照の意味的一致

## 4.7 Schema test

各Schemaについて、次を用意する。

- minimum valid fixture
- full valid fixture
- missing required field
- invalid enum
- invalid null
- resolved/non-resolved invariant violation
- formal/model_assumed violation
- unexpected fieldの扱い
- duplicate key rejectionはparser層で実施

## 4.8 完了条件

- 全valid fixtureが通過する。
- 全negative fixtureが期待どおり失敗する。
- v17 writer出力に`value_state`が存在しない。
- enumが仕様・registry・configurationと一致する。
- Schema versionとSHA-256が記録されている。
- Schemaで表現できない条件がSemantic Invariant一覧へ漏れなく転記されている。

---

# 5. 成果物4：Registry群

## 5.1 目的

Registry群は、production code内へ埋め込むべきでない有限語彙、rule、ontology、assumptionおよびstop conditionを、versioned machine-readable artifactとして管理する。

Registryを分離する目的は以下である。

- magic valueを排除する。
- rule追加・変更を追跡可能にする。
- fixtureとstop codeを対応付ける。
- configurationごとに使用するrule versionを固定する。
- implementationとは独立して規範的語彙をreviewできるようにする。

## 5.2 必須Registry

### 5.2.1 State／Origin Registry

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

### 5.2.2 Stop-code Registry

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

未登録stop codeはformal blockerである。

### 5.2.3 Oneway Rule Registry

管理対象：

- explicit normalization
- implicit one-way
- ordinary-road default
- unsupported・invalid判定
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

### 5.2.4 Vehicle Ontology Registry

管理対象：

- governed SUMO vClass
- OSM transport mode
- parent-child relationship
- explicit domain set
- non-governed class
- managed vehicle mapping

文字列類似ではなく、登録済み集合関係によってspecificityを評価する。

### 5.2.5 Access-value Registry

各access valueについて以下を持つ。

```yaml
source_value:
normalized_effect:
required_context:
authorization_requirement:
supported:
unsupported_status:
stop_code:
```

### 5.2.6 Conditional Grammar Registry

管理対象：

- clause separator
- operator
- weekday
- time interval
- date interval
- public holiday
- mass・dimension predicate
- purpose
- permit
- unsupported token

grammar versionとtoken registry hashを固定する。

### 5.2.7 Assumption Registry

structural-only assumptionを管理する。

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

### 5.2.8 Japan Speed-rule Registry

管理対象：

- explicit symbolic value
- absent maxspeed
- road class
- context
- effective km/h
- evidence
- version
- applicability boundary

### 5.2.9 Evidence Method Registry

正式補完を将来有効化する場合に使用する。

承認済みmethodが存在しない限り、`evidence_derived`または`derived_validated_model`をproduction outputしてはならない。

### 5.2.10 Exclusion Rule Registry

管理対象：

- governed populationから除外可能な条件
- reason
- population impact
- approval
- evidence
- versioning requirement

## 5.3 Registry共通構造

各registryは以下を持つ。

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

Registry artifact全体および各entryについてstable IDを付与する。

## 5.4 作成手順

1. 仕様書に現れるenum、rule ID、stop code、assumption IDを抽出する。
2. 現行code・YAML・Markdown内の既存値を収集する。
3. 重複、別名、deprecated valueを整理する。
4. canonical valueを決定する。
5. 各entryに意味・trigger・remediation・fixtureを付与する。
6. Registry Schemaを作成する。
7. semantic validatorからregistry参照を行う。
8. configurationにregistry path、version、hashを登録する。

## 5.5 完了条件

- 仕様書に登場する全IDがregistryへ登録されている。
- production code固有の未登録magic valueがない。
- deprecated valueの扱いが明示されている。
- fixtureとstop codeの対応が存在する。
- configurationが使用registryを一意に参照する。
- registryの変更によりhashが変化する。
- unregistered rule、state、stop codeをvalidatorが拒否する。

---

# 6. 成果物5：Semantic Invariant一覧

## 6.1 目的

Semantic Invariant一覧は、JSON Schemaだけでは十分に表現できない、意味上、集合上、母集団上およびprovenance上の制約を定義する。

本成果物は、仕様書の自然言語要求を、semantic validatorで実装可能な判定単位へ分解したものである。

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

## 6.3 Invariantの最小構造

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

## 6.4 必須Invariant群

### A. State contract

- resolvedならeffective valueとoriginが存在する。
- non-resolvedならeffective valueとoriginがnullである。
- formal recordに`model_assumed`が存在しない。
- formal recordにassumption IDが存在しない。
- v17 writer outputに`value_state`が存在しない。
- stop codeはregistryに存在する。

### B. Record identity

- record-key objectのRFC 8785 canonical JSONからSHA-256を再計算し、`record_id`と一致する。
- mutable fieldはidentity hashに含めない。
- `classification_record_id`はresolutionによって変更されない。
- duplicate record IDが存在しない。

### C. Directed Segment

- source start indexはsource end indexより小さい。
- indexはsource Way node配列の範囲内である。
- forward/backwardは同じcanonical intervalを参照する。
- `oneway=-1`はbackwardのみを生成する。
- source Way hashは処理前後で不変である。
- SUMO edge IDの符号は方向根拠に使われていない。
- relation mapping candidate数に応じてunique／missing／ambiguousを判定する。

### D. Lane

- one-wayのactive directionとlane allocationが一致する。
- total lane countとdirectional countの和が一致する。
- lane vector長とdirectional lane countが一致する。
- formal profileでeven splitが使われていない。
- structural even splitは登録条件をすべて満たす。
- `sumo_index = n - 1 - p`が成立する。

### E. Speed

- km/hからm/sへの変換が正しい。
- directional asymmetric speedを保持する。
- symbolic valueはspeed registryに存在する。
- lower-priority sourceがhigher-priority sourceを上書きしていない。
- within-interval changeを平均していない。

### F. Access

- direction/lane scope外のtupleにruleを適用していない。
- vehicle domainはontologyの明示集合である。
- dominated ruleがmaximal setに残っていない。
- maximal ruleが異なるeffectを持つ場合に停止している。
- independent record orderを変えても結果が不変である。
- same-result maximal ruleのprovenanceが保持される。
- typemap permissionがformal authorityになっていない。

### G. Conditional

- required context欠損をfalseとして扱っていない。
- unsupported syntaxを無視していない。
- 同一conditional tag内だけlast-matchを適用している。
- 独立tag間の競合をsource orderで解決していない。
- within-interval permission changeを検出する。

### H. Evidence

- approved method以外から`evidence_derived`を出力していない。
- donorがformal eligibleである。
- donorにstructural assumptionがない。
- manual evidenceが別artifactとして登録されている。
- production outputを直接編集していない。

### I. Population

- `input = governed + excluded`が成立する。
- exclusion ruleがregistryに存在する。
- materialization omissionをexclusionとして数えていない。
- omitted edgeの元tupleがpermission denominatorに残る。
- population versionとexclusion manifestが一致する。

### J. Provenance・determinism

- required hashがすべて記録されている。
- RFC 8785 canonicalizationが適用される。
- duplicate JSON keyが拒否される。
- 同一環境・入力・commandの2回実行でhashが一致する。
- structural artifactとformal artifactの出力先が分離される。

### K. Acceptance

- `complete=true`の定義をすべて満たす。
- blocker、review_required、stop、model_assumedがゼロである。
- classification projection hashが不変である。
- fixture・oracle validationが通過している。
- formal artifactにnon-resolved recordがない。

## 6.5 作成手順

1. 規範仕様のcross-field、集合、順序、母集団に関する要求を抽出する。
2. 一つのboolean判定に分解する。
3. invariant IDを付与する。
4. failure時のstatus・stop codeを割り当てる。
5. fixture IDを割り当てる。
6. validator実装予定位置を記録する。
7. JSON Schemaとの重複を確認する。
8. 同じ条件をSchemaとvalidatorで矛盾して定義していないか確認する。

## 6.6 完了条件

- 仕様書の意味的要求がすべて登録されている。
- 各invariantが判定可能な文になっている。
- failure時の処理が明示されている。
- 対応fixtureが存在する、または作成計画が登録されている。
- Schemaで検証する条件とsemantic validatorで検証する条件が分離されている。
- acceptance gateが参照するinvariantが明示されている。

---

# 7. 成果物6：差分レビュー報告書

## 7.1 目的

差分レビュー報告書は、完成したv17規範仕様と、既存repositoryに存在するconfiguration、Schema、registry、validator、fixture、oracleおよびproduction codeとの差異を記録する成果物である。

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
| `missing_field` | 必須fieldが存在しない。 |
| `legacy_only` | v16表現だけが存在する。 |
| `enum_conflict` | enumが仕様と一致しない。 |
| `semantic_conflict` | 実装意味が仕様と異なる。 |
| `authority_conflict` | formal authorityが誤った成果物に置かれている。 |
| `unregistered_rule` | code・fixtureで未登録ruleが使用されている。 |
| `fixture_gap` | 必須caseのfixtureがない。 |
| `oracle_gap` | 独立oracleがない。 |
| `validator_gap` | semantic checkがない。 |
| `evidence_gap` | hash、manifest、runtime evidenceがない。 |
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
- state／stop code定義
- oneway処理
- lane resolution
- access specificity utility
- conditional parser
- speed resolution
- fixture
- oracle
- evidence manifest
- acceptance gate
- network current specification

## 7.5 差分記録形式

| 項目 | 内容 |
|---|---|
| `finding_id` | 一意の差分ID |
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

## 7.6 Severity

### Critical

- v16成果物を書き換える。
- source OSMまたはgenerated `net.xml`を直接編集する。
- `model_assumed`をformalに使用する。
- unresolved recordをmaterializeする。
- typemap permissionをv17 formal authorityとする。
- `oneway=-1`を誤方向へ生成する。
- acceptanceを証拠なしでpassedとする。

### Major

- Schema／registry／configurationの不一致。
- required fixture・oracleの欠落。
- target scopeとspecificityの混同。
- state/origin contract未移行。
- stop code未登録。
- semantic validator欠落。

### Minor

- 説明文の不足。
- naming inconsistency。
- non-normative metadataの欠落。
- 参照pathの整理不足。

## 7.7 レビュー手順

1. 仕様同期表を基準にrepositoryを調査する。
2. 各要求について現状の実装・成果物を確認する。
3. `aligned`以外をfindingとして登録する。
4. Severityを付与する。
5. Phase 1で解消する項目と、Phase 2以降へ送る項目を分ける。
6. Phase 1修正後に再レビューする。
7. unresolved critical findingがないことを確認する。
8. Phase 1 completion recordを作成する。

## 7.8 Phase 1で解消すべき差分

Phase 1では、少なくとも以下を解消する。

- configurationのv17化
- Schema enum・fieldの同期
- registryの作成
- semantic invariantの定義
- v16／v17 authorityの分離
- `resolution_status`／`value_origin`の規範上の一致
- Directed Segment ID・direction ruleの一致
- target scope／specificity axesの一致
- structural／formal profileの一致
- acceptance gate conditionの一致

以下は、Phase 2以降の実装課題として残ってよい。

- production codeの全面統合
- 全fixture・oracleの実行成功
- full-population run
- stop recordの解消
- Attribute Resolution Acceptance
- Permission Materializer
- SUMO Network Integration Acceptance

## 7.9 完了条件

- 仕様同期表上の`conflicting`がゼロである。
- unresolved critical findingがゼロである。
- Phase 1対象のmajor findingがゼロである。
- Phase 2以降へ送るfindingにtarget phaseとownerがある。
- v16／v17のauthority境界が明記されている。
- 修正済み成果物のcommitおよびhashが記録されている。
- reviewerがPhase 1 completionを承認している。

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

# 9. Phase 1 完了判定

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

Phase 1の完了は、production implementationまたはAttribute Resolution Acceptanceの完了を意味しない。

---

# 10. Phase 1 完了後の次工程

Phase 1完了後は、以下へ進む。

## Phase 2

- independent fixture作成
- production-independent oracle作成
- fixture author・reviewer記録
- stop-code coverage確認
- metamorphic test設計

## Phase 3

- `resolution_status`／`value_origin` migration
- legacy reader
- v17 writer
- semantic validator実装

## Phase 4以降

- Directed Segment production統合
- directional lane resolution
- access normalization
- conditional evaluation
- final permission resolution
- speed resolution
- full-population run
- Attribute Resolution Acceptance

---

# 11. 成果物一覧

| No. | 成果物 | 推奨形式 | Phase 1での目的 |
|---:|---|---|---|
| 1 | 仕様同期表 | Markdown＋CSV | 仕様要求と実装先を対応付ける。 |
| 2 | v17 Configuration | YAML | runで有効なpolicy・profile・registry・gateを固定する。 |
| 3 | JSON Schema | JSON | artifact構造と基本制約を検証する。 |
| 4 | Registry群 | YAML／JSON | 有限語彙、rule、ontology、assumptionを管理する。 |
| 5 | Semantic Invariant一覧 | Markdown＋YAML | 意味上の検証条件を定義する。 |
| 6 | 差分レビュー報告書 | Markdown | 既存repositoryとの不一致を管理する。 |

本書により、v17規範仕様を、実装可能かつ第三者が監査可能なmachine-readable authorityへ展開するための成果物構成と完了条件を固定する。
