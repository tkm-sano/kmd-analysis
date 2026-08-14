# Phase 13根本原因解消からSUMO道路網受入までの実行TODO

> 文書状態: 実行管理用TODO
>
> 基準日: 2026-08-14
>
> 対象構成: `ota_ward_sumo_network_v17`
>
> 固定母集団: `ota_ward_relation_closure_v16`
>
> 現在地: Phase 1〜12合格、Phase 13進行中、Phase 14ゲート待ち

## 0. このTODOの使い方

この文書は、各作業について次を一つずつ確認できるようにする。

- 確認するファイル・データ
- 判断する内容
- 更新するファイル
- 実行するcommand
- 残す成果物・証拠
- 完了条件
- 不合格時の戻り先

チェック状態は次の意味で使用する。

- `[x]`: 実行および証拠記録まで完了
- `[ ]`: 未実行、進行中、または完了証拠が不足

blocker総数が減っただけでは完了としない。各blockerはstable identityと根本原因で追跡し、
解決、証拠付き正式除外、または未解決維持のいずれかへ説明可能に遷移させる。

## 1. 正本・固定入力・実行記録

### 1.1 確認する正本

- [x] Phase 12完了記録を確認する。
  - `reproducibility/config/traffic_simulation/v17_phase12_completion.yml`
- [x] Phase 13入力固定記録を確認する。
  - `reproducibility/config/traffic_simulation/v17_phase13_input_lock.yml`
- [x] Phase 13 blocker集計を確認する。
  - `reproducibility/config/traffic_simulation/v17_phase13_blocker_aggregation.yml`
- [x] Phase 13実行履歴を確認する。
  - `reproducibility/config/traffic_simulation/v17_phase13_execution_log_20260814.yml`
- [x] Phase 13後の詳細計画を確認する。
  - `reproducibility/config/traffic_simulation/v17_post_phase13_to_experiment_execution_plan.yml`
- [x] Phase 9〜14ロードマップを確認する。
  - `reproducibility/config/traffic_simulation/v17_phase9_to_phase14_execution_roadmap.yml`
- [x] blocker・除外方針を確認する。
  - `reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml`
  - `05_src/traffic_simulation/specifications/11_formal_blocker_resolution_exclusion_policy_v17.md`

### 1.2 固定したPhase 13入力

- [x] 公開元を`run_1`へ固定する。
- [x] 公開7成果物のbyte SHA-256を固定する。
- [x] 主要5成果物のsemantic SHA-256を固定する。
- [x] `complete_blocker_inventory` 108,189件をPhase 13入力として固定する。
- [x] Phase 12公開成果物の直接編集・上書きを禁止する。
- [x] 入力固定validatorを実装する。
  - `05_src/traffic_simulation/network/validate_v17_phase13_input_lock.py`
  - `05_src/traffic_simulation/validation/test_phase13_input_lock_v17.py`
- [x] 次のcommandが合格することを確認する。

```bash
PYTHONPATH=05_src python -m traffic_simulation.network.validate_v17_phase13_input_lock
```

期待結果:

```text
phase13_input_lock=passed
source_run=run_1
artifact_count=7
complete_blocker_inventory=fixed
```

## 2. 現在までに完了したPhase 13作業

- [x] blocker 108,189件を次の軸で10群へ集計する。
  - `attribute_name`
  - `stop_code`
  - `root_cause_category`
- [x] 個別blocker recordを集計後も保存する。
- [x] upstream blockerとdownstream permission blockerを単純加算しない。
- [x] 最初のvehicle ontology判断を記録する。
  - `reproducibility/config/traffic_simulation/v17_phase13_vehicle_ontology_decision.yml`
- [x] `bicycle`、`foot`、`mofa`、`moped`をgoverned車種との明示的な空交差として登録する。
- [x] fixtureとproduction-independent oracleを追加する。
- [x] full-population static access probeを新しい一時出力で実行する。
  - `reproducibility/config/traffic_simulation/v17_phase13_vehicle_ontology_probe.yml`
- [x] Phase 12公開成果物が変更されていないことを確認する。
- [x] 固定analysis containerで全validation suiteを実行する。

```bash
docker compose run --rm -T analysis \
  python -m pytest -q 05_src/traffic_simulation/validation
```

- [x] 基準回帰結果`597 passed`を記録する。
- [x] ホスト環境では`rfc8785`、`folium`不足で収集不能だった事実と、固定containerでの代替実行を記録する。

## 3. root cause修正の共通反復手順

各root causeについて、次の順序を変更しない。

- [ ] 対象blocker IDを固定inventoryから抽出する。
- [ ] 実際のOSMタグ・方向・車線・車種・context・provenanceを一覧化する。
- [ ] 根本原因を再確認し、件数だけを理由に判断しない。
- [ ] authority evidenceを確認する。
- [ ] decision recordを新しいversion付きファイルとして作成する。
- [ ] Registryまたはdecision tableを更新する。
- [ ] 必要ならJSON Schemaを更新する。
- [ ] semantic invariantとtraceabilityを更新する。
- [ ] 小型fixtureを追加する。
- [ ] production実装から独立したoracleを追加する。
- [ ] resolver実装を更新する。Registry駆動で変更不要な場合は理由を記録する。
- [ ] fixture testを実行する。
- [ ] focused integration testを実行する。
- [ ] full-population stage probeを新規出力へ実行する。
- [ ] 修正前後のblocker ID差分レポートを生成する。
- [ ] 固定analysis containerで全回帰を実行する。
- [ ] command、終了コード、ログ、ログSHA-256、成果物SHA-256をPhase 13実行履歴へ追記する。

各反復の完了条件:

- 判断理由がOSM仕様、法令、承認済み研究方針または登録証拠へ結び付く。
- 対象外recordが変化していない、または全変化が説明されている。
- 新規の説明不能blockerが0件である。
- formal exclusionをblocker削減手段として使用していない。
- focused testと全回帰が合格している。

## 4. TODO A: `psv`・`motorcar`・`horse`の車種意味を確定する

### 4.1 確認

- [ ] 固定`complete_blocker_inventory`から`ACCESS_VEHICLE_HIERARCHY_MISSING`を抽出する。
- [ ] Phase 13 probeで残った次の実例を抽出する。
  - `horse`: 130件
  - `motorcar`: 154件
  - `psv`: 16件
- [ ] 各recordについて次を一覧化する。
  - OSM Way ID
  - source key/value
  - 同じWayにある`access`、`vehicle`、`motor_vehicle`、`goods`、`hgv`等
  - direction/lane scope
  - managed vehicle context
- [ ] 次を確認する。
  - `reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml`
  - `reproducibility/config/traffic_simulation/resolver_exception_decision_table.yml`
  - `05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md`
  - `05_src/traffic_simulation/specifications/japan_tokyo_osm_exception_classification_rules.md`
  - OSMの車種access key定義と根拠URL・参照日

### 4.2 判断

- [ ] `psv`が本研究の`bus`、`taxi`等へどう交差するか決定する。
- [ ] `motorcar`が`passenger`、`taxi`、`delivery`等へどう交差するか決定する。
- [ ] `horse`がgoverned motorized universeと空交差でよいか根拠を確認する。
- [ ] `delivery`を`motorcar`へ含めるかを車両定義と法的・OSM意味から明示判断する。
- [ ] 値を一意に決められないkeyはfail-closedを維持する。

### 4.3 更新

- [ ] keyごとに独立したdecision recordを作る。
- [ ] vehicle ontology Registryをversion更新する。
- [ ] semantic invariantとtraceabilityを同期する。
- [ ] fixture/oracleを追加する。
- [ ] 必要に応じてstatic/final permission resolverを更新する。

### 4.4 実行

- [ ] `test_static_access_v17.py`を実行する。
- [ ] `test_final_permission_v17.py`を実行する。
- [ ] `test_resolver_integration_v17.py`を実行する。
- [ ] full-population static access probeを新しい出力へ実行する。
- [ ] 固定container全回帰を実行する。

### 4.5 成果物・完了条件

- [ ] OSM keyからgoverned車種集合への対応表を残す。
- [ ] decision、Registry、fixture、oracle、test log、probe、before/after reportを残す。
- [ ] `OSMタグ → 登録規則 → 対象車種への効果`を第三者が説明できる。
- [ ] blockerが残る場合、その理由と必要な追加証拠を記録する。

## 5. TODO B: 速度blocker 78,616件を原因別に解消する

対象内訳:

- `SPEED_RULE_NOT_REGISTERED`: 78,601件
- `SPEED_VALUE_UNSUPPORTED`: 15件

### 5.1 確認・再分類

- [ ] 固定inventoryから速度blockerを抽出する。
- [ ] 各recordへ次を結合する。
  - OSM Way ID
  - directed segment ID/direction
  - `highway`
  - `maxspeed`
  - `maxspeed:forward`
  - `maxspeed:backward`
  - `maxspeed:conditional`
  - `zone:*`
  - road contextと既存provenance
- [ ] 道路種別・方向・タグ組合せ別の件数を集計する。
- [ ] 次の原因へ再分類する。
  - 明示速度あり・既対応
  - 明示速度あり・構文未対応
  - 速度欠損・登録済み規則で導出可能
  - 速度欠損・根拠不足
  - 複数証拠の競合
- [ ] 15件のunsupported実値を全件一覧化する。
- [ ] `signals`、`walk`等の特殊表記を正式意味と利用目的に照らして判断する。

### 5.2 判断・更新

- [ ] `maxspeed`欠損を一律値で埋めない。
- [ ] 「道路条件＋authority evidence→正式速度」という規則単位で判断する。
- [ ] 次を確認・更新する。
  - `reproducibility/config/traffic_simulation/japan_speed_rules_v17.yml`
  - `reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml`
  - `05_src/traffic_simulation/network/speed_resolution_v17.py`
  - 関連Schema、Invariant、traceability
- [ ] 各規則へ出典、適用範囲、例外、優先順位、versionを記録する。
- [ ] 根拠不足recordは`remain_blocked`を維持する。

### 5.3 実行・成果物

- [ ] 明示速度、規則導出、unsupported、根拠不足、競合のfixture/oracleを追加する。
- [ ] speed focused testを実行する。
- [ ] full-population speed probeを新規出力へ実行する。
- [ ] before/resolved/remaining/new/unexpectedをID単位で比較する。
- [ ] 固定container全回帰を実行する。
- [ ] 原因別のPhase 12/Phase 13比較表を残す。

完了条件:

- 全解決値にauthority evidenceまたは承認済み規則がある。
- `model_assumed`をformalへ混入していない。
- 残存blockerの必要証拠と道路網影響が説明されている。

## 6. TODO C: 方向別車線blocker 24,138件を原因別に解消する

対象内訳:

- `LANE_DIRECTIONAL_ALLOCATION_MISSING`: 24,114件
- `LANE_VECTOR_LENGTH_MISMATCH`: 18件
- `LANE_COUNT_CONFLICT`: 6件

### 6.1 確認・分類

- [ ] 各Wayについて次の組合せを抽出する。
  - `lanes`
  - `lanes:forward`
  - `lanes:backward`
  - `lanes:both_ways`
  - `oneway`
  - directed segment direction
  - lane-local vectors
- [ ] 次のパターンへ分類する。
  - 一方向で総車線数を方向車線数として使用可能
  - 双方向でforward/backward明示あり
  - 双方向で総車線数のみ
  - both-ways laneあり
  - vector長不一致
  - 算術・タグ競合
- [ ] 18件のvector conflictを1件ずつ確認する。
- [ ] 6件のlane count conflictを1件ずつ確認する。

### 6.2 判断・更新

- [ ] formalでは「総車線数2だから1+1」の自動仮定を使用しない。
- [ ] 一方向・明示方向タグなど、証拠から決定可能な場合だけ規則化する。
- [ ] 外部証拠による配分を採用する場合、方法をversion付きで登録する。
- [ ] 真正競合を自動補正しない。
- [ ] 次を確認・更新する。
  - `05_src/traffic_simulation/network/directional_lanes_v17.py`
  - `reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml`
  - 関連Schema、Invariant、traceability

### 6.3 実行・成果物

- [ ] パターン別fixture/oracleを追加する。
- [ ] lane focused testを実行する。
- [ ] full-population lane probeを新規出力へ実行する。
- [ ] blocker ID差分を生成する。
- [ ] 固定container全回帰を実行する。
- [ ] 解決件数と根拠不足・競合の残存件数を分離して記録する。

## 7. TODO D: final permission blocker 4,864件を原因別に解消する

### 7.1 確認・分類

- [ ] 全4,864 permission recordと1,130 root-cause recordを抽出する。
- [ ] 各recordについて適用直前まで到達したstatic/conditional ruleを出力する。
- [ ] 次を記録する。
  - source Way ID
  - directed segment ID
  - lane position
  - vehicle class
  - scenario context
  - candidate/maximal rule IDs
  - permission record ID
  - root-cause record IDs
- [ ] 次の原因へ分類する。
  - 車種対応規則なし
  - access value未登録
  - applicable access ruleなし
  - conditional context不足
  - specificity conflict
  - upstream lane/relation blocker
- [ ] upstream原因とdownstream permission stopを二重計上しない。

### 7.2 判断・更新

- [ ] managed `delivery`についてOSM access情報から最終permissionへの判断表を作る。
- [ ] typemapをformal permission authorityとして使用しない。
- [ ] 道路に明示access tagがないことだけを理由に、無条件許可・拒否を追加しない。
- [ ] Registryへ追加可能な規則と、証拠不足で残すrecordを分ける。
- [ ] lane/direction単位のpermission provenanceを保存する。
- [ ] 次を確認・更新する。
  - `05_src/traffic_simulation/network/static_access_v17.py`
  - `05_src/traffic_simulation/network/conditional_access_v17.py`
  - `05_src/traffic_simulation/network/final_permission_v17.py`
  - access Registry、Schema、Invariant、traceability

### 7.3 実行・成果物

- [ ] 原因別fixture/oracleを追加する。
- [ ] permission focused testを実行する。
- [ ] full-population permission probeを新規出力へ実行する。
- [ ] 修正前後の4,864 recordをstable IDで比較する。
- [ ] 固定container全回帰を実行する。
- [ ] 各解決recordについて`OSM情報 → Rule ID → delivery permission`を追跡可能にする。

## 8. TODO E: 少数blockerを種類別に処理する

### 8.1 relation direction 48件

- [ ] 対象relation IDとmemberを一覧化する。
- [ ] `from`、`via`、`to`とDirected Segment候補を記録する。
- [ ] 0候補と複数候補を分ける。
- [ ] 一意性を証明できる追加規則または証拠を判断する。
- [ ] 複数候補が残る場合はblockerを維持する。
- [ ] relation fixture/oracle、probe、差分、回帰結果を残す。

### 8.2 unsupported access value 27件

- [ ] 実値をユニーク化する。Phase 12では`use_sidepath`が確認されている。
- [ ] typo、正式OSM値、未対応値を区別する。
- [ ] 正式値だけを根拠付きでRegistryへ追加する。
- [ ] 不明値を既知値へ勝手に読み替えない。
- [ ] fixture/oracle、probe、差分、回帰結果を残す。

### 8.3 speed unsupported value 15件

- [ ] 全実値と対象Way/directionを一覧化する。
- [ ] 特殊表記の正式意味とsimulation speedへの変換可否を判断する。
- [ ] 正式解釈がある構文だけparser/Registryへ追加する。
- [ ] fixture/oracle、probe、差分、回帰結果を残す。

### 8.4 conditional access syntax 4件

- [ ] 実際の4式を全文・source Way ID付きで抽出する。
- [ ] parser未対応と、formalに解釈困難な式を分ける。
- [ ] 対応する場合はgrammar、Schema、fixture、oracleを同時更新する。
- [ ] 条件評価に必要なcontextがなければblockerを維持する。
- [ ] probe、差分、回帰結果を残す。

## 9. 修正単位ごとのblocker差分レポート

各decisionについて次を機械比較する。

- [ ] 消えたblocker ID
- [ ] 新規blocker ID
- [ ] stop codeが変化したID
- [ ] resolution statusが変化したID
- [ ] effective valueが変化したID
- [ ] root-cause linkが変化したID
- [ ] 影響を受けなかったID
- [ ] 除外へ遷移したIDと登録exclusion rule

差分レポート最低項目:

```text
decision_id
target_group
before_count
resolved_count
excluded_count
remaining_count
new_blocker_count
changed_stop_code_count
unexpected_change_count
before_inventory_sha256
after_inventory_sha256
```

完了条件:

- [ ] `unexpected_change_count=0`
- [ ] 新規blockerはすべて説明・登録されている。
- [ ] 消えたblockerは解決または正式除外へ対応する。
- [ ] 総数だけでなくstable identityとroot causeで比較している。

## 10. Phase 13正式全道路再実行

probeはPhase 13正式runではない。主要root causeのdecisionと回帰が完了した後、次を行う。

### 10.1 実行前固定

- [ ] Phase 13用の新しいversion付きoutput rootを決める。
- [ ] Phase 12 input lockを参照する。
- [ ] source commitを固定する。
- [ ] configuration、Registry、Schema、decision recordのhashを固定する。
- [ ] `sha256:<64桁>`のcontainer digestを固定する。
- [ ] run開始前にworktree状態と実行対象commitを記録する。
- [ ] Phase 12 `published/`を読み取り専用の比較元として扱う。

### 10.2 run 1

- [ ] `run_1`を独立directoryで実行する。
- [ ] 実際のCLI引数をmanifestへ記録する。
- [ ] 主要成果物を新規生成する。
  - structural full population
  - formal full population
  - complete blocker inventory
  - exclusion manifest
  - population accounting
  - environment/build manifest
  - run manifest
- [ ] 各run completion validatorを実行する。
- [ ] command、exit code、stdout/stderr、ログSHA-256をmanifestへ記録する。
- [ ] 固定文字列ではなくvalidator実結果からrun合否を生成する。

### 10.3 run 2

- [ ] `run_2`を`run_1`とは別directoryへ最初から実行する。
- [ ] `run_1`成果物を入力として読ませない。
- [ ] input lock、commit、container、configurationを`run_1`と一致させる。
- [ ] completion validatorを独立に実行する。
- [ ] 実command、exit code、ログ、ログSHA-256を記録する。

### 10.4 2-run比較・最終化

- [ ] 主要5成果物のsemantic hashを比較する。
- [ ] CLI引数を比較する。規定されたrun ID以外を無視しない。
- [ ] container digest、Python、library、seed、input、configuration、Schema、Registry、commitを比較する。
- [ ] `determinism_report`を生成する。
- [ ] 両runの単体検査とdeterminismが合格した場合だけ公開候補を選ぶ。
- [ ] 公開元run、全成果物path、byte hash、semantic hashを固定する。
- [ ] 既存Phase 12公開物を上書きしない。

## 11. Phase 13後の道路母集団台帳

- [ ] Way IDを主軸とするmaster tableを生成する。
- [ ] 必要に応じてdirection、lane、vehicle、attribute単位の子recordを保持する。
- [ ] 各Wayへ次を記録する。
  - source Way ID
  - final state
  - reason/stop code
  - evidence IDs
  - decision/rule ID
  - directed segment IDs
  - generated/excluded/unresolved status
- [ ] 次を集計する。
  - input
  - governed
  - resolved
  - excluded
  - unresolved
  - conflict
  - invalid
  - valid-but-unsupported
- [ ] 異なるidentity unitの件数を単純加算しない。
- [ ] どの入力道路も所在不明にならないことを検査する。

保存則:

```text
input = governed + excluded
governed = resolved + unresolved + conflict + invalid + valid_but_unsupported
governed IDs ∩ excluded IDs = ∅
```

## 12. 正式除外を行う場合のTODO

現状は`no_formal_exclusion_authorized: true`である。

- [ ] 除外が必要な場合、研究対象外であるauthority evidenceを先に確認する。
- [ ] version付きexclusion ruleを登録する。
- [ ] 対象道路IDを抽出する。
- [ ] 各除外へ次を記録する。
  - source road ID
  - exclusion reason
  - registered rule ID
  - evidence IDs
  - approver
  - approval date
  - population version
  - 道路延長・接続性・配送到達性への影響
- [ ] exclusion manifestを新規生成する。
- [ ] governed/excluded overlapが0件であることを検査する。
- [ ] 除外をresolvedとして数えない。
- [ ] 欠損、未実装、費用、件数、日程、受入圧力を除外理由にしない。

## 13. Phase 13 Completion Record

- [ ] 次を記載したversion付き完了記録を作る。
  - Phase 12 baseline blocker: 108,189
  - root cause別before/resolved/excluded/remaining
  - 最終道路状態集計
  - run 1/run 2 manifest hash
  - 主要成果物semantic hash
  - determinism report hash/result
  - container digest、source commit、configuration/Registry version
  - 未解決recordと必要証拠
- [ ] blocker減少だけをPhase 13完了理由にしない。
- [ ] 全decision、試験、probe、正式run、差分、保存則を完了記録へ結び付ける。
- [ ] ロードマップと統合状況資料を更新する。

Phase 13完了条件:

- 全対象root causeがdecision済み、または証拠不足として明示的に残されている。
- 全道路再実行が2回独立に合格している。
- blocker遷移に説明不能差分がない。
- 母集団保存則が成立している。
- Phase 14入口値が機械可読である。

## 14. Phase 14 Attribute Resolution Acceptance

ここで初めて「道路属性成果物をSUMOへ入力してよい」と判断する。

### 14.1 入口条件

- [ ] governed blocker count = 0
- [ ] review-required count = 0
- [ ] stop-unresolved count = 0
- [ ] model-assumed count = 0
- [ ] 全governed recordがresolved
- [ ] permission coverage complete
- [ ] population equations valid
- [ ] 全除外に登録規則とauthority evidenceがある。
- [ ] Phase 13 2-run determinismが合格している。

入口条件を満たさない場合はPhase 14を合格扱いにせず、Phase 13へ戻る。

### 14.2 Acceptance検査

- [ ] fixed inputとの対応
- [ ] required artifactsの存在
- [ ] JSON Schema validation
- [ ] semantic invariant validation
- [ ] production-independent oracle validation
- [ ] classification projection invariance
- [ ] ID一意性
- [ ] direction解決
- [ ] lane解決
- [ ] speed解決
- [ ] permission解決
- [ ] relation mapping
- [ ] provenance完全性
- [ ] exclusion traceability
- [ ] population conservation
- [ ] run 1/run 2 determinism

### 14.3 成果物

- [ ] `phase14_acceptance_report`を生成する。
- [ ] Phase 14 completion recordを生成する。
- [ ] pass/failを実検査結果から決定する。
- [ ] 合格の意味を「SUMO build inputとして使用可能」に限定する。
- [ ] Phase 14合格がSUMO道路網受入や交通Validationを意味しないと明記する。

## 15. Accepted属性成果物のfreeze

- [ ] acceptance IDを発行する。
- [ ] accepted runだけを公開元として固定する。
- [ ] 全入力artifactのbyte/semantic hashを固定する。
- [ ] source commit、configuration、Schema、Registry、decision、environmentを固定する。
- [ ] SUMO versionとcontainer digestを固定する。
- [ ] formal SUMO build input manifestを生成する。
- [ ] 上書きを禁止し、変更時は新versionとPhase 14再判定を要求する。

## 16. OSM属性からSUMO plain XMLへの変換

- [ ] accepted属性から次を生成する。
  - `.nod.xml`
  - `.edg.xml`
  - `.con.xml`
  - `.tll.xml`
- [ ] 次のlineage tableを生成する。

```text
OSM Way ID
→ Directed Segment ID
→ SUMO Edge ID
→ SUMO Lane ID
```

- [ ] direction、lane count/index、speed、accessを変換する。
- [ ] omissionと変換判断をmachine-readable recordへ残す。
- [ ] SUMO edge IDから元OSM道路を逆引きできることを検査する。

## 17. Permission Materializer

- [ ] 次を確認する。
  - `05_src/traffic_simulation/specifications/03_permission_materializer_specification.md`
  - `05_src/traffic_simulation/learning/permission_materializer_reproducible_implementation_guide.md`
- [ ] resolverのpermission expectationを読み込む。
- [ ] SUMO lane単位の`allow/disallow`へ変換する。
- [ ] connection permissionへ反映する。
- [ ] OSM lane positionとSUMO lane indexの反転規則を実装・検査する。
- [ ] empty permission laneを`disallow="all"`とする。
- [ ] 全lane禁止edgeのmaterialization omissionをmanifestへ記録する。
- [ ] fixed SUMO fixtureと独立oracleを実行する。
- [ ] expected permissionと生成XMLを全件比較する。
- [ ] final `net.xml`を直接編集しない。

## 18. junction・connection・TLSレビュー

- [ ] 暫定変換から候補を抽出する。
- [ ] 近接junction merge候補を確認する。
- [ ] lane-to-lane connectionを確認する。
- [ ] turn restrictionを確認する。
- [ ] traffic signal connectionを確認する。
- [ ] TLS link indexを確認する。
- [ ] phase数、phase長、program、offsetを確認する。
- [ ] 必要な修正をgoverned XML/decisionへ登録する。
- [ ] 手編集した最終`net.xml`ではなく、登録入力から再度`netconvert`する。

## 19. 正式`net.xml`生成

- [ ] 固定node、edge、connection、TLS、permissionを`netconvert`へ渡す。
- [ ] 実際のcommandと全CLI引数をbuild manifestへ記録する。
- [ ] 次を記録する。
  - SUMO version
  - container digest
  - source commit
  - input hashes
  - stdout/stderr
  - exit code
  - warning一覧と分類
  - log SHA-256
- [ ] exit code 0を確認する。
- [ ] XSD validationとSUMO loadを確認する。
- [ ] unexplained warningが0件であることを確認する。
- [ ] `net.xml`のbyte SHA-256を固定する。

## 20. OSM→SUMO変換・構造監査

- [ ] 次の基本統計を算出する。
  - node数
  - edge数
  - lane数
  - 道路延長
  - signalized junction数
- [ ] 次の段階別件数とidentity mappingを作る。

```text
OSM governed ways
→ directed segments
→ SUMO edges
→ SUMO lanes
```

- [ ] 消えた道路を一覧化する。
- [ ] 分割された道路を一覧化する。
- [ ] omitted edgeを一覧化する。
- [ ] 全非生成道路について理由を記録する。
- [ ] permissionにより配送車両が通れないedgeを一覧化する。
- [ ] 配送車両が通行可能なedge数・道路延長・到達範囲を算出する。
- [ ] weak/strong component、孤立edge、到達不能領域、不正接続を検査する。
- [ ] 「なぜこのOSM道路はSUMOに存在しないか」をID単位で説明可能にする。

## 21. SUMO runtime走行検証

- [ ] 代表ODとexpected oracleを事前固定する。
- [ ] 次のscenarioを含める。
  - 幹線道路のみ
  - 住宅道路を含む
  - 一方通行を含む
  - 通行規制付近
  - 信号交差点
  - 大田区内長距離
- [ ] 配送車両を実際に走行させる。
- [ ] route計算成功を確認する。
- [ ] 禁止道路を通行しないことを確認する。
- [ ] 一方通行遵守を確認する。
- [ ] connectionが正常であることを確認する。
- [ ] 信号link/phaseが正常であることを確認する。
- [ ] teleport、route failure、unexpected warningが0件であることを確認する。
- [ ] command、route、tripinfo、ログ、hash、判定をruntime manifestへ記録する。

## 22. SUMO Network Integration Acceptance

- [ ] reproducible buildを検査する。
- [ ] XSD・SUMO loadを検査する。
- [ ] warning auditを検査する。
- [ ] OSM→SUMO lineageを検査する。
- [ ] lane/connection permission projectionを検査する。
- [ ] coverageとomission理由を検査する。
- [ ] connectivity/reachabilityを検査する。
- [ ] runtime走行検証を検査する。
- [ ] formal network acceptance reportを生成する。
- [ ] 合格networkと全入力・環境hashを固定する。

この判定はPhase 14とは別である。

- Phase 14: 道路属性をSUMO変換へ渡してよいか。
- Network Integration Acceptance: 生成されたSUMO道路網を下流で使用してよいか。

## 23. 道路網受入後の後続TODO

### 23.1 交通較正

- [ ] 較正用観測と独立Validation用観測をparameter調整前に分離・固定する。
- [ ] 正式道路網へ一般交通需要を投入する。
- [ ] 交通量、速度、旅行時間を対象として較正する。
- [ ] parameter探索、seed、評価指標、不確実性を記録する。

### 23.2 独立Validation

- [ ] 較正に未使用の日時または地点を使用する。
- [ ] 結果確認前に合否閾値を固定する。
- [ ] Validation結果を見てparameterを変更した場合、当該データを較正用へ再分類する。
- [ ] 独立Validation decisionを発行する。

### 23.3 配送比較共通入力

- [ ] 検証済み道路網を固定する。
- [ ] 検証済み交通条件を固定する。
- [ ] 配送需要を固定する。
- [ ] 車両、積載量、バッテリー、出発時刻、電力条件を固定する。
- [ ] scenario matrixとrandom seedを固定する。
- [ ] 非最適化、古典最適化、QAOAで解法以外の条件を同一にする。

### 23.4 配送手法比較

- [ ] 次の手法を同一条件で実行する。
  - 非最適化
  - 古典最適化
  - QAOA
- [ ] 次を比較する。
  - 距離
  - 時間
  - 遅延
  - 電力消費
  - 配送需要充足率
- [ ] run別結果、集計、不確実性、seed分析、reproducibility manifestを残す。

## 24. 直近の実行順序

1. [ ] `psv`、`motorcar`、`horse`の実recordを抽出する。
2. [ ] keyごとにauthority evidenceを確認し、独立decisionを作る。
3. [ ] Registry・Invariant・fixture・oracleを更新する。
4. [ ] focused testを実行する。
5. [ ] full-population static access probeを新規出力へ実行する。
6. [ ] blocker ID差分を生成する。
7. [ ] 固定containerで全回帰を実行する。
8. [ ] 実行command、結果、ログhash、成果物hashをPhase 13実行履歴へ追記する。
9. [ ] 次のactionable root causeへ同じ手順を反復する。
10. [ ] 主要root cause処理後、Phase 13正式全道路runを2回独立実行する。

## 25. 全体の判定境界

```text
Phase 13: blockerの根本原因を修正する
  ↓
Phase 13 full rerun: 修正が全道路で機能し、再現することを確認する
  ↓
Final accounting: 全道路の解決・除外・未解決と保存則を確定する
  ↓
Phase 14: 属性成果物をSUMOへ渡してよいか正式判断する
  ↓
OSM→SUMO: accepted属性をnode・edge・lane・connectionへ変換する
  ↓
SUMO Network Integration Acceptance: 生成道路網を正式承認する
  ↓
Calibration / independent Validation: 交通モデルの目的適合性を確認する
  ↓
Delivery experiment: 共通条件で非最適化・古典最適化・QAOAを比較する
```
