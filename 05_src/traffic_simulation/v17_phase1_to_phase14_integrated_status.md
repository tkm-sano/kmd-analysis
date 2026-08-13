# v17 属性解決 Phase 1〜14 統合定義・現在地・証拠

> **文書状態**: 現状確認用の統合資料
>
> **基準日**: 2026-08-13（日本標準時）
>
> **対象**: 東京・大田区 SUMO 道路網の v17 属性解決ライフサイクル
>
> **構成識別子**: `ota_ward_sumo_network_v17`
>
> **方針識別子**: `ota_ward_attribute_resolution_policy_v17`
>
> **母集団版**: `ota_ward_relation_closure_v16`
>
> **現在地**: Phase 1〜11 は正式記録上合格。Phase 12 は新しい独立出力先で2回実行し、両runの単体completion gateと主要5成果物のsemantic hash一致まで確認済み。ただし、2run全体の`finalize()`と正式完了記録は未実施。Phase 13 は未着手、Phase 14 はゲート待ち。

## 1. この文書の目的

この文書は、これまで複数の仕様書、YAML記録、ロードマップ、学習資料に分散していた
v17 属性解決 Phase 1〜14について、次を一か所で確認できるようにする。

1. 各Phaseの定義と完了条件
2. 2026-08-13時点の状態
3. 状態判断の根拠となる実装、試験、記録、成果物
4. 未完了事項と次に進むための条件
5. `v17`、`v16`、`V&V`、Phase番号の区別

この文書は既存の規範仕様や機械可読契約を置き換えない。定義が競合する場合は、
承認済み規範仕様、機械可読設定・Schema、各Phase完了記録、実行ロードマップ、
この統合資料、学習資料の順に参照する。

## 2. 用語と番号の区別

### 2.1 `v` は version を表す

- `v17`は**属性解決方針・設定・Schema・実装契約のバージョン17**を表す。
- `v16`は**直前のバージョン16**を表す。
- 本作業は、受理済みの `ota_ward_relation_closure_v16` 母集団を変更せず、v17の規則で
  属性を再解決する。
- `v17 Phase 12`は「バージョン17のPhase 12」であり、「バージョン12」ではない。

### 2.2 `V&V` は version ではない

`V&V`は **Verification and Validation** の略である。

- Verificationは、仕様、規則、Schema、実装、変換、道路構造が意図どおりであるかの確認である。
- Validationは、モデルが定めた利用目的に対して現実を十分に表すかの確認である。
- v17 Phase 1〜14は、主に道路属性解決のVerificationと受入に属する。
- Phase 14合格だけでは、SUMO道路網統合、交通較正、独立Validationは完了しない。

### 2.3 Phase番号と旧「工程」番号を混同しない

現行の番号は、本書で使用する **v17 Phase 1〜14** である。
`attribute_resolution_execution_procedure.md`には別体系の「工程0〜17」が残っており、
番号は一対一に一致しない。例えば、同文書の「工程11 版17全件実行」は現行の
**Phase 12 Full-population Run**に相当する。状態判断にはPhase番号を優先する。

## 3. ライフサイクル全体

```text
v16履歴・母集団を固定
  ↓
v17規範仕様を承認
  ↓
Phase 1  Authority Synchronization
  ↓
Phase 2  Independent Fixtures and Oracles
  ↓
Phase 3  State Contract Migration
  ↓
Phase 4  Directed Segment Integration
  ↓
Phase 5  Directional Lane Resolution
  ↓
Phase 6  Static Access Resolution
  ↓
Phase 7  Conditional Access Resolution
  ↓
Phase 8  Final Permission Resolution
  ↓
Phase 9  Speed Resolution
  ↓
Phase 10 Formal Evidence Method
  ↓
Phase 11 Resolver Integration Test
  ↓
Phase 12 Full-population Run and Accounting
  ↓
Phase 13 Stop Record Resolution and Rerun
  ↓
Phase 14 Attribute Resolution Acceptance
  ↓
SUMO Network Integration Acceptance
  ↓
交通モデルのCalibration
  ↓
独立データによるValidation
  ↓
配送・古典最適化・Qiskit Aer QAOAの正式比較
```

## 4. 状態の読み方

| 状態 | 意味 |
|---|---|
| 合格 | Git管理された完了記録があり、当該Phaseで要求された実装・検証ゲートを通過している |
| 実行済み・正式完了未認定 | 成果物は存在するが、正式な完了記録または完了ゲートの充足確認が不足している |
| 未着手 | 前提Phaseまたは開始条件を満たしておらず、正式作業を開始していない |
| ゲート待ち | 受入処理自体は未実行で、前提条件の充足を待っている |

Phase単体の「合格」は、属性解決全体、正式SUMO道路網、または研究全体のV&V完了を意味しない。

## 5. Phase 1〜14 統合一覧

| Phase | 定義・目的 | 主な完了条件 | 2026-08-13現在 | 主要証拠 | 残作業・次の条件 |
|---:|---|---|---|---|---|
| 1 | **Authority Synchronization**。v17規範仕様、設定、Schema、Registry、Semantic Invariant、トレーサビリティを同期する | 権威資料間の不整合がなく、validatorと試験が合格する | **合格**（2026-08-03） | `v17_phase1_completion.yml`、承認済みv17方針、`sumo_network_v17.yml`、同期レビュー | なし。当該Phaseの合格はruntime全件実行を意味しない |
| 2 | **Independent Fixtures and Oracles**。production実装から独立した小型入力、期待結果、manifestを固定する | fixture・oracle・manifestがSchemaに適合し、相互hashが一致する | **合格**（2026-08-03） | `v17_phase2_completion.yml`、`validation/fixtures/v17_attribute_resolution/` | なし。production統合は後続Phaseで実施 |
| 3 | **State Contract Migration**。`resolution_status`と`value_origin`を分離したv17状態契約へ移行する | legacy reader、v17 writer、cross-field validator、移行規則が実装・検証済み | **合格**（2026-08-03） | `v17_phase3_completion.yml`、`attribute_resolution_state_v17.py`、移行Registry | なし |
| 4 | **Directed Segment Integration**。OSM Wayを方向付き区間へ正規化し、方向・区間・relation来歴を保持する | `oneway`を含む方向正規化、canonical interval、relation mapping、独立fixtureが合格する | **合格**（2026-08-04） | `v17_phase4_completion.yml`、`directed_segments_v17.py` | formal停止は後続Phase 12〜13で扱う |
| 5 | **Directional Lane Resolution**。方向別車線数、`lanes:both_ways`、SUMO lane indexとの対応を解決する | formalとstructuralの境界を守り、formalで根拠のない算術補完を行わない | **合格**（2026-08-04） | `v17_phase5_completion.yml`、`directional_lanes_v17.py` | formalの未解決車線はPhase 13対象 |
| 6 | **Static Access Resolution**。静的な通行規則を車種・方向・車線軸で解決する | 最大適用規則選択と競合・未対応時のfail-closedが実装・検証済み | **合格**（2026-08-04） | `v17_phase6_completion.yml`、`static_access_v17.py` | conditional accessとfinal permissionはPhase 7〜8で実施済み |
| 7 | **Conditional Access Resolution**。日時・曜日・祝日等の条件付き通行規則を固定Scenario Contextで評価する | grammar、Registry、期間内変化のfail-closed、Scenario Contextが検証済み | **合格**（2026-08-04） | `v17_phase7_completion.yml`、`conditional_access_v17.py`、runtime context | 未解決条件はPhase 13対象 |
| 8 | **Final Permission Resolution**。static・conditional・scope・axis dominanceから最終通行権限期待値を作る | 全permission tupleを記録し、typemapをformal権威として使用しない | **合格**（2026-08-04） | `v17_phase8_completion.yml`、`final_permission_v17.py` | formal permission未解決はPhase 13対象 |
| 9 | **Speed Resolution**。方向別・条件付き速度、法定速度、助言速度、simulation速度を分離して解決する | 日本速度規則が承認・hash固定され、未根拠値をformalへ混入しない | **合格**（2026-08-04） | `v17_phase9_completion.yml`、`speed_resolution_v17.py`、`japan_speed_rules_v17.yml` | formal速度未解決はPhase 13対象 |
| 10 | **Formal Evidence Method**。外部・派生証拠をformal値へ使用する方法と境界を統制する | 未承認method、model-assumed donor、直接編集をfail-closedにし、origin auditが合格する | **合格**（2026-08-04） | `v17_phase10_completion.yml`、`evidence_resolution_v17.py`、origin audit | 承認済みformal evidence methodは現在0件。証拠なしの停止を解消済みとはしない |
| 11 | **Resolver Integration Test**。Phase 3〜10を統合し、Schema、意味、独立oracle、metamorphic relationを検査する | 4ゲートすべて合格し、cross-stage lineageが保たれる | **合格**（2026-08-04） | `v17_phase11_completion.yml`、`resolver_integration_v17.py`、統合fixture/oracle | Phase 11合格はfull-population acceptanceを意味しない |
| 12 | **Full-population Run and Accounting**。固定v16母集団をv17 structural/formal両profileで2回独立実行し、全停止・除外・母集団差を保存する | 必須8成果物、全Schema・意味検証、hash、母集団式、ID一意性、環境一致、2回決定論的一致、原子的公開がすべて合格する | **2回実行・run単体合格、正式完了未認定** | 固定契約、runner、各runのmanifest、`v17_phase12_independent_rerun_20260813.yml` | `run_id`だけが異なる実CLI引数の環境比較規則を修正し、全体`finalize()`、原子的公開、正式完了記録を実施する |
| 13 | **Stop Record Resolution and Rerun**。Phase 12の停止を根本原因別に解消し、全件成果物を再生成する | decision→Registry/表→Schema→Invariant→fixture→独立oracle→code→試験→全件runの順を守り、未証明recordを残さない | **未着手** | `v17_phase9_to_phase14_execution_roadmap.yml`、formal blocker policy | Phase 12の正式確定後、blockerを属性・停止コード・根本原因別に集計して解消する |
| 14 | **Attribute Resolution Acceptance**。formal属性成果物の最終受入判定を行う | blocker、review-required、stop-unresolved、model-assumedが各0件。全record解決、母集団式・permission被覆・Schema・意味・oracle・projection不変・2回一致が合格する | **ゲート待ち** | 実行ロードマップ、formal blocker policy | Phase 13再実行後に受入を実行する。合格しても正式SUMO道路網の承認とは別 |

## 6. 現在地の詳細

### 6.1 正式に確定している状態

- Git管理された累積完了記録は、Phase 1〜11を `passed` としている。
- Phase 11時点で、Schema、Semantic Invariant、production-independent oracle、
  metamorphic validationが合格している。
- `formal_build_ready` は `false` である。
- `attribute_resolution_acceptance` は `not_run` である。
- 正式SUMO道路網は未承認であり、較正、独立Validation、配送・QAOA正式評価へ進めない。

### 6.2 Phase 12の実行成果物

Phase 12の出力先は `.gitignore` 対象だが、ローカルには2026-08-13に新しい独立出力先で
生成した次の成果物が存在する。

- `runs/run_1/`
- `runs/run_2/`

記録された2回の実行は同一commit
`c86c7548bcd39b2f6fcdccd0b1e6c813fe10636c`、固定container digest
`sha256:fbc7489e297359ccbd70a0030613d95d2f3dade061b6501b281d834e24bd3002`、
同一固定入力を使用した。両runは終了コード0で、8個のrun単体validatorと実行後の独立CLI再検査に
合格し、主要5成果物のsemantic SHA-256がすべて一致した。各run manifestには、実際のCLI引数、
各validatorのcommand、終了コード、stdout/stderrログ、そのSHA-256、検査件数、検査結果が記録される。
Phase 12全体の`finalize()`は未実行なので、`published/`と`determinism_report.json`はこの新出力先では
まだ正式成果物として生成していない。

Phase 12成果物が示す主な数値は次のとおりである。異なる母集団単位の件数を単純合算して
モデル全体の欠損率などと解釈してはならない。

| 項目 | 件数・状態 |
|---|---:|
| blocker inventory総件数 | 108,189 |
| directional lane governed | 26,220 |
| directional lane resolved | 2,082 |
| directional lane unresolved | 24,114 |
| directional lane conflict | 24 |
| static access governed | 2,082 |
| static access resolved | 1,563 |
| final permission governed | 6,984 |
| final permission resolved | 2,120 |
| final permission unresolved | 4,864 |
| speed governed | 94,745 |
| speed resolved | 16,129 |
| speed unresolved | 78,601 |
| production exclusion | 0 |
| structural permission record | 16,330 |
| formal permission record | 6,984 |
| structural/formal差 | 9,346（登録済み仮定 `BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`） |
| run_1 単体completion | passed（8 validator、失敗0） |
| run_2 単体completion | passed（8 validator、失敗0） |
| 主要5成果物の2run semantic hash一致 | passed |
| Phase 12全体`finalize()` | 未実行 |

### 6.3 Phase 12を正式完了としない理由

両runが単体検査に合格していても、次の全体ゲートが未完了であるため、本書ではPhase 12を
「2回実行・run単体合格、正式完了未認定」とする。

1. 実CLI引数を正しく記録すると、`run_1`と`run_2`では`--run-id`の値が必ず異なる。一方、
   現行契約は環境比較対象に`arguments`全体を含めるため、そのままでは正しい2runを同一環境と
   判定できない。実記録を改変せず、比較時だけrun固有値を正規化する規則が必要である。
2. 上記規則を実装・試験した後の全体`finalize()`、2run決定論report、原子的公開が未実行である。
3. Git管理されたPhase 12正式完了記録とロードマップ更新が未作成である。
4. runnerとvalidatorの正常系・成果物欠落・値改変・ID重複・母集団不整合・上書き拒否・
   公開禁止の試験は合格しているが、小型fixtureによる2runから`finalize()`までの全経路試験が残る。
5. 108,189件のgoverned blockerが残り、`formal_build_ready`は`false`である。これはPhase 13で
   根本原因別に解消すべき内容であり、run単体validator合格によって解消されたとは扱わない。

したがって新しい2run成果物は、Phase 12全体最終化、blocker分析、Phase 13設計には使用できるが、
現状のままPhase 12の正式完了証拠またはPhase 14の受入証拠にはしない。

## 7. Phase 12からPhase 14までの次の実行順序

1. **実装済み:** Phase 12 runnerが実際に受け取ったCLI引数列をmanifest生成へ渡し、
   正式runでは`sha256:<64桁>`のcontainer digestを必須として未固定値を開始前に拒否する。
2. **実装・検証済み:** 各run単体で存在、Schema、semantic hash、意味整合、ID一意性、
   母集団保存則、登録値、blocker/exclusion整合を検査する。各validatorの実command、終了コード、
   stdout/stderrログ、ログSHA-256は新規run manifestへ記録する。項目別・run全体の合否は
   各validatorの検査件数と結果から集約し、固定の`passed`を使用しない。`finalize()`はrun manifest、
   environment manifest、全byte hashを再検査する。
3. runner、失敗時、2回実行、finalize、公開処理の試験を追加する。
   正常系、成果物欠落、値改変、ID重複、母集団不整合、成果物上書き拒否、失敗runの公開禁止、
   既存`published`上書き拒否は実装済みである。残るのは小型fixtureによる2回実行全経路である。
4. 既存成果物を直接編集せず、新しい出力先または新しいrun識別子で2回再実行する。
   新しい固定出力先は
   `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun`
   とする。**2026-08-13実行済み:** 固定container digest、同一source commit、同一入力から
   `run_1`と`run_2`を独立実行し、双方が8個のrun単体gateおよび実行後の独立CLI再検査に合格した。
   主要5成果物のsemantic SHA-256も2runで一致した。実行証拠は
   `v17_phase12_independent_rerun_20260813.yml`に記録した。
5. `run_id`を除く実CLI引数の環境比較規則を実装・試験し、全体`finalize()`を実行する。
6. 全完了ゲート合格後、Phase 12完了記録とロードマップを更新する。
7. blockerを `attribute_name`、`stop_code`、`root_cause_category` で集計する。
8. Phase 13の順序に従って根本原因を解消し、全件runを再実行する。
9. governed blocker等がすべて0件になった後、Phase 14 Acceptanceを実行する。
10. Phase 14合格後にのみ、formal属性をSUMO Network Integrationへ渡す。

## 8. Phase 14後に残る工程

Phase 14は属性解決の受入であり、道路網全体や交通モデル全体のV&V完了ではない。
少なくとも次が後続する。

1. provisional structural buildとexact provenance生成
2. Permission Materializerによるlane・connection permission反映
3. final connection setの確定
4. signal junction・TLS review
5. SUMO 1.24.0によるNetwork Integration Acceptance
6. 一般交通需要、信号、車両、運転行動設定
7. 交通モデルのCalibration
8. 未使用データによる独立Validation
9. EV配送、古典最適化、Qiskit Aer QAOAの正式比較

## 9. 正本・証拠索引

### 9.1 全体定義と現行ロードマップ

- `05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md`
- `05_src/traffic_simulation/learning/v17_phase1_beginner_guide_full_intent_hierarchy_ja.md`
- `reproducibility/config/traffic_simulation/v17_phase9_to_phase14_execution_roadmap.yml`
- `05_src/traffic_simulation/specifications/11_formal_blocker_resolution_exclusion_policy_v17.md`
- `reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml`

### 9.2 Phase 1〜11の完了記録

- `reproducibility/config/traffic_simulation/v17_phase1_to_phase11_record.yml`
- `reproducibility/config/traffic_simulation/v17_phase1_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase2_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase3_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase4_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase5_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase6_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase7_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase8_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase9_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase10_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase11_completion.yml`

### 9.3 Phase 12の契約、実装、試験、成果物

- `05_src/traffic_simulation/specifications/12_phase12_full_population_output_contract_v17.md`
- `reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml`
- `reproducibility/config/traffic_simulation/v17_phase12_output_contract_adoption.yml`
- `05_src/traffic_simulation/network/execute_v17_phase12_full_population.py`
- `05_src/traffic_simulation/network/validate_v17_phase12_run_completion.py`
- `05_src/traffic_simulation/network/validate_v17_phase12_output_contract.py`
- `05_src/traffic_simulation/validation/test_phase12_output_contract_v17.py`
- `05_src/traffic_simulation/validation/test_phase12_run_completion_v17.py`
- `reproducibility/config/traffic_simulation/v17_phase12_independent_rerun_20260813.yml`
- `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/`

### 9.4 V&V全体と後続工程

- `05_src/traffic_simulation/simulation_model_development_and_vv.md`
- `05_src/traffic_simulation/attribute_resolution_execution_procedure.md`
- `reproducibility/config/traffic_simulation/research_stage.yml`

## 10. 更新規則

この文書を最新状態として維持する場合、次のいずれかが起きた時点で同じ変更セット内で更新する。

- Phase完了記録を追加・変更したとき
- Phase 12以降のrunを新規生成したとき
- blocker件数または根本原因分類が変わったとき
- `formal_build_ready`または`attribute_resolution_acceptance`が変わったとき
- v17から新しいversionへ移行したとき
- Phaseの定義、順序、完了条件を変更したとき

新しいversionへ移行する場合は、本文中の`v17`を機械的に置換しない。母集団版、方針ID、
構成ID、Schema版、完了記録、成果物hashを個別に確認し、旧versionの履歴を保持する。
