# Phase 13根本原因解消からSUMO道路網受入までの実行TODO

> 実行環境更新（2026-08-25）: `固定analysis container`は過去の検証条件名として履歴に残す。今後の標準全回帰はHayate native Conda環境で`python -m pytest -q 05_src/traffic_simulation/validation`を実行し、Dockerは任意の追加クロスチェックとする。現行正本は`reproducibility/environment/README.md`である。

> 文書状態: 実行管理用TODO
>
> 基準日: 2026-08-14
>
> 対象構成: `ota_ward_sumo_network_v17`
>
> 固定母集団: `ota_ward_relation_closure_v16`
>
> 現在地: Phase 1〜12合格、Phase 13進行中、Phase 14ゲート待ち

## この文書の目的

本研究は、OpenStreetMap（OSM）を基礎道路データとして、交通シミュレーターSUMOで使用する
大田区の道路網を構築するものである。ただし、OSMの道路情報をそのままSUMOへコピーすることは
できない。道路によって、方向別車線数、速度、車種別通行権限、右左折関係などが欠損していたり、
複数の解釈が可能であったりするためである。

Phase 12までに確認したのは、固定した入力と実行環境から道路属性処理を2回独立に実行したとき、
同じ成果物を再現できることである。これは処理の決定性と再現性が確認できたという意味であり、
すべての道路属性が解決済みという意味ではない。Phase 12の正式baselineには、現状の情報・規則・
実装では正式値を決定できないblockerが108,189件保存されている。

Phase 13では、この108,189件を道路ごとに手修正しない。多数のblockerを発生させている少数の
共通原因を見つけ、判断根拠、Registry、Schema、実装を修正する。修正は小型fixture、独立oracle、
全道路stage probe、回帰試験で検証し、最終的に全道路を2回独立に再実行する。Phase 14では、
その道路属性成果物をSUMO変換へ渡してよい品質かを正式判定する。

Phase 14に合格した後も道路網は完成ではない。承認済み属性をSUMOのnode、edge、lane、connectionへ
変換し、構造・通行権限・接続・信号・実走行を検証したうえで、別のSUMO Network Integration
Acceptanceを行う。その後、一般交通を較正し、較正に使わなかった観測で独立Validationを行い、
初めて配送手法の比較へ進む。本書は、この一連の過程について、現在地、理由、実作業、成果物、
完了条件を第三者が追跡できるようにする実行計画書兼作業記録である。

## 現在地

Phase 1〜12は正式記録上合格している。Phase 13では、Phase 12公開成果物の入力固定、blocker
108,189件の10群への集計、最初のvehicle ontology判断、full-population static access stage
probe、固定analysis containerでの全回帰`597 passed`まで完了している。現在は`psv`、`motorcar`、
`horse`を含む残りの根本原因を処理する段階である。

現時点では、Phase 13正式全道路2-run、Final accounting、Phase 13 Completion、Phase 14は未完了で
ある。そのため、`formal_build_ready=false`、`attribute_resolution_acceptance=not_run`であり、
正式なSUMO道路網生成へはまだ進まない。

## 全体像

```text
OSM道路情報
  ↓
道路属性の解釈
  ↓
Phase 13：解釈できない原因を解消
  ↓
全道路を再実行・最終状態を集計
  ↓
Phase 14：道路属性をSUMOへ渡してよいか判定
  ↓
OSM属性 → SUMO node / edge / lane / connection
  ↓
SUMO道路網を生成・構造・走行検証
  ↓
SUMO Network Integration Acceptance
  ↓
交通較正・独立Validation
  ↓
配送比較実験
```

各境界の意味は異なる。blockerが減ったことだけではPhase 13完了ではない。Phase 14合格はSUMO道路網
完成を意味しない。`net.xml`の生成成功はNetwork Integration Acceptance合格を意味しない。また、
Network Integration Acceptance合格は、交通モデルの現実妥当性を独立Validationで確認したことを
意味しない。

| 工程 | 前工程から受け取るもの | 明らかにすること | 次工程へ渡すもの |
|---|---|---|---|
| Phase 13 | Phase 12の固定成果物とblocker inventory | blockerの根本原因を規則として解消できるか | 修正规則、検証証拠、再実行可能な実装 |
| Phase 13 full rerun | Phase 13の修正と固定入力 | 修正が全道路で再現可能に機能するか | 2-run成果物とdeterminism report |
| Final accounting | Phase 13正式成果物 | 全入力recordが最終的にどこへ行ったか | 最終状態台帳、保存則、除外・未解決監査 |
| Phase 14 | 最終状態と2-run証拠 | 属性成果物をSUMO変換へ渡してよいか | accepted属性成果物とAcceptance Record |
| OSM→SUMO conversion | accepted属性成果物 | 属性をnode/edge/lane/connectionへ正しく投影できたか | lineage付きSUMO build input/network候補 |
| Network Integration Acceptance | 生成networkと監査・走行結果 | networkを下流simulationへ使ってよいか | 固定された正式SUMO道路網 |
| Calibration / Validation | 正式道路網と観測データ | 交通状態が研究目的に対して妥当か | 検証済み交通条件 |
| Delivery experiment | 検証済み共通入力 | 配送手法による結果差は何か | 非最適化・古典最適化・QAOA比較結果 |

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

## 2.1 blockerとexclusionの違い

`blocker`は、本来は研究対象に含まれるrecordであるが、現在の情報、登録規則、または実装だけでは
正式値を決定できない状態である。例えば、研究対象道路に`lanes=2`としか書かれておらず、双方向の
配分根拠がない場合、その道路を消すのではなく、方向別車線のblockerとして保持する。

`exclusion`は、研究設計上、そもそも今回の対象外であることを、事前定義された規則とauthority evidence
から判断した状態である。exclusionは失敗を隠す手段ではなく、研究対象母集団の境界を説明する判断である。
道路ID、除外理由、登録Rule ID、根拠、承認者、日付、母集団への影響を追跡できなければならない。

したがって、次の理由では正式除外してはならない。

- 属性が欠損しているから
- 実装が難しいから
- blocker件数が多いから
- 調査時間が足りないから
- Phase 14へ早く進みたいから

つまり、`unresolved`または`blocker`をexclusionへ移して見かけの件数を減らすことは禁止である。
blockerは根拠を得て解決するか、必要な証拠を明示したまま保持する。exclusionへ移せるのは、研究対象外で
あることを独立したauthority evidenceと登録済み規則で証明できる場合だけである。

## 3. root cause修正の共通反復手順

### この手順の目的

Phase 13の基本方針は、108,189件を人手で個別修正することではなく、108,189件を発生させている
少数の共通原因を再実行可能な規則として直すことである。同じ原因から生じた道路を一括して正しく
処理できれば、修正理由と影響範囲を説明でき、同じ入力から同じ結果を再生成できる。

実作業では、まず実際に停止した道路とOSMタグを見る。次に、なぜ停止したかを分類し、OSM仕様、
法令、承認済み研究方針などの判断根拠を調べる。その人間の判断をdecision recordとRegistryへ
機械可読な規則として移し、小型fixtureとproduction-independent oracleで確認する。その後、全道路へ
stage probeを行い、修正前後をstable IDで比較し、最後に全回帰試験を実行する。decision、command、
終了コード、log、hashを記録することで、「たまたま動いた」のではなく、なぜ変更して何が変わったかを
再検証できるようにする。

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

### この工程の目的

OSMの車種表現を、本研究で管理するSUMO車種へ一意かつ根拠付きで対応させる工程である。OSMに
`motorcar=yes`と書かれていても、それが本研究の`passenger`、`taxi`、`delivery`のどこまでを
含むかを決めなければ、配送車両の通行可否を正式に判断できない。

### 現在何が問題なのか

最初のvehicle ontology修正後のstage probeでは、`horse` 130件、`motorcar` 154件、`psv` 16件が
未登録の車種domainとして残った。単に既存車種へ広く割り当てると、本来通れない配送車両を許可する
可能性がある。逆に空集合へすると、本来適用すべき通行規則を失う可能性がある。

### 実際に何をするのか

例えば`motorcar=yes`を持つWayについて、同じWayの`access`、`vehicle`、`goods`等を確認し、OSM仕様と
本研究のmanaged vehicle定義から対象車種集合を決める。判断をRegistryへ登録し、小型fixtureで
`delivery`への効果を確認した後、全道路へ適用してblocker差分を見る。

```text
OSMに motorcar=yes がある
  → motorcarがpassenger / taxi / deliveryのどこまでを表すか確認する
  → OSM仕様と研究車両定義を根拠に決定する
  → Registryへ登録する
  → fixtureと独立oracleで確認する
  → 全道路へ適用する
  → blocker ID差分を確認する
```

### この工程が終わると何が分かるか

OSMの`psv`、`motorcar`、`horse`表現が、本研究のどの車種へ影響するか、または影響しないかをRule IDと
根拠から説明できる。これにより、車種ontology不足と、本当に別のaccess根拠が不足している道路を
区別できる。

### 4.1 確認

- [x] 固定`complete_blocker_inventory`から`ACCESS_VEHICLE_HIERARCHY_MISSING`を抽出する。
- [x] Phase 13 probeで残った次の実例を抽出する。
  - `horse`: 130件
  - `motorcar`: 154件
  - `psv`: 16件
- [x] 各recordについて次を一覧化する。
  - OSM Way ID
  - source key/value
  - 同じWayにある`access`、`vehicle`、`motor_vehicle`、`goods`、`hgv`等
  - direction/lane scope
  - managed vehicle context
  - 抽出JSON:
    `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.json`
  - 抽出CSV:
    `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260814_vehicle_ontology_extraction/psv_motorcar_horse_records.csv`
  - 実行記録:
    `reproducibility/config/traffic_simulation/v17_phase13_vehicle_ontology_record_extraction.yml`
  - 固定inventoryの対象492件から300 Wayを抽出した。2 Wayには`motorcar`と`horse`が併存するため、
    source key所属件数と、DEC-P13-VEHICLE-ONTOLOGY-001反映後に最初に停止するkeyの件数を分けて記録した。
- [ ] 次を確認する。
  - `reproducibility/config/traffic_simulation/attribute_resolution_registries_v17.yml`
  - `reproducibility/config/traffic_simulation/resolver_exception_decision_table.yml`
  - `05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md`
  - `05_src/traffic_simulation/specifications/japan_tokyo_osm_exception_classification_rules.md`
  - OSMの車種access key定義と根拠URL・参照日

### 4.2 判断

- [x] `psv`が本研究の`bus`、`coach`、`taxi`へどう交差するか決定する。
  - Decision: `DEC-P13-PSV-ONTOLOGY-001`
  - 結論: `bus=true`、`taxi=true`、`coach=false`。managed `delivery`への効果はない。
  - 根拠: OSM `Key:psv` revision 2960634、`Key:access` revision 3054035、SUMO `v1_24_0` commit `b72eb3fabc806681f8c9048999a33dd8d64092b1`。
- [ ] `motorcar`が`passenger`、`taxi`、`delivery`等へどう交差するか決定する。
- [x] `horse`がgoverned motorized universeと空交差でよいか根拠を確認する。
  - 判断: `horse=no/yes`は騎乗者に対する別車種制約であり、managed `delivery` permissionを変化させない。
  - Decision: `reproducibility/config/traffic_simulation/v17_phase13_horse_vehicle_ontology_decision.yml`
  - OSM `Key:horse` revision 3060819と`Key:access` hierarchy revision 3054035を2026-08-14に参照した。
  - `carriage=*`、未承認値、conditional・direction・lane scopeはこの判断へ含めず、fail-closedを維持する。
- [ ] `delivery`を`motorcar`へ含めるかを車両定義と法的・OSM意味から明示判断する。
- [ ] 値を一意に決められないkeyはfail-closedを維持する。

### 4.2.1 Vehicle population evidence prerequisite

- [x] 都市ラストマイル配送のvehicle universeを登録する。
- [x] 四輪配送車をF1〜F7へ層別化する。
- [x] 実運用evidence registryを登録する。
- [x] 実車variant recordを登録する。
- [x] 車格別`observed_empirical_envelope`を正本recordから生成する。
- [x] 独立min/max組合せを禁止する。
- [x] F2/F3のevidence gapを明示する。
- [ ] OSM `goods`/`hgv`の日本向け意味を、現行法令・道路標識定義・OSM Japan semanticsから再確認する。
- [x] population evidenceとactive runtime vehicle profileを区別する。
- [ ] 上記成果物を`motorcar` ontology decisionの参考証拠として参照する。

この前提作業は`motorcar`判断に先立つmanaged delivery EV profileの再検証である。populationを登録しただけでは
Phase 13 blockerは解消済みにならず、その作業時点のRegistry 1.4.0も変更しなかった。その後、承認済み
`psv` decisionを1.5.0、`horse` decisionを1.6.0として順にRegistryへ反映した。

#### この工程の目的

`motorcar`との対応や重量・高さ制限への適合を判断する前に、本研究のmanaged delivery vehicleが、実際に
東京都内・都市部のラストマイル配送等で使われるEV商用車のどの範囲を代表するかを確定する工程である。
車種の法的・物理的性質が未確定のままOSM車種ontologyへ対応させると、通行可能道路と配送実験の電力・
航続距離条件を同時に誤る可能性がある。

#### 現在何が問題なのか

現行`managed_urban_ev_delivery_v1`は、車両総重量3,500 kg、空車重量1,500 kg、最大積載量2,000 kg、
全長4.7 m、全幅1.7 m、全高2.0 mを研究上の固定条件として持つ。しかし、どの実在車両群を代表し、
分布内の中央値・典型値・上限のどこに位置するかが未確認である。また、バッテリー容量、電費、航続距離、
充電速度を同じ実車母集団から代表化する手順も未固定である。

#### 実際に何をするのか

- [ ] **対象車両群を定義する。**
  - 「東京都内・都市部でラストマイル配送等に使われる小型〜中型EV商用車」のように、何を代表させる
    車両なのかを明文化する。
  - 用途、販売・利用地域、車体区分、動力、積載用途、調査基準日、採用・不採用条件を先に固定する。
  - 軽EV商用車、EVバン、小型EVトラックのどこまでを同一母集団に含めるかを明記する。
- [ ] **実在車両を複数集める。**
  - 国内で実際に利用または販売されている軽EV商用車、EVバン、小型EVトラック等を複数収集する。
  - 車種、grade、model yearを区別し、同一車種の重複集計を防ぐ。
  - 全長、全幅、全高、車両重量、最大積載量、車両総重量、バッテリー容量、航続距離、電費、充電速度を
    収集する。
  - 各値について、メーカー仕様書・公式諸元表等の提供元、資料名、URL、参照日、単位、測定条件を残す。
  - 欠損値を推測で補完せず、欠損・非公表・異なる測定方式を明示する。
- [ ] **代表値の決め方をデータ集計前に固定する。**
  - 基本値は外れ値の影響を受けにくい中央値とする。
  - 必要に応じて小型／標準／大型の3条件を定義し、各条件の境界と採用車両を固定する。
  - 平均値、中央値、最小値、最大値、四分位範囲、標本数を併記し、中央値だけで分布を隠さない。
  - 値ごとに異なる車両の中央値を組み合わせた結果、実在しない不整合車両にならないかを確認する。
- [ ] **現行寸法・重量と実車分布を比較する。**
  - 車両総重量3,500 kg、全長4.7 m、全幅1.7 m、全高2.0 mが分布内か、典型値か、上限寄りかを示す。
  - 現行値ごとにpercentileまたは分布上の位置、差分、維持・変更判断を記録する。
- [ ] **最大積載量2,000 kgを再検証する。**
  - 車両総重量3,500 kg、空車重量1,500 kg、最大積載量2,000 kgの同時成立を実車諸元で確認する。
  - `車両重量 + 最大積載量`だけでなく、乗員・架装・付属品等を含む車両総重量の定義差を確認する。
  - 都市型EV配送車の代表条件として妥当か、上限条件または感度分析条件へ移すべきかを判断する。
- [ ] **EVとして必要な値を同じ対象車両群から代表化する。**
  - バッテリー容量、電費、航続距離、普通・急速充電速度、利用可能容量の扱いを定める。
  - WLTC等の試験値と実走行・積載時の値を混同せず、測定方式と前提条件を保持する。
  - 道路access用の寸法・重量と、後続配送実験用のエネルギー値を同じprofile lineageで追跡する。
- [ ] **根拠をvehicle profileへ紐付ける。**
  - 各値へ`value_origin`を付け、少なくとも`real_vehicle_median`、`legal_classification`、
    `research_fixed_condition`、`derived_value`、`sensitivity_scenario`を区別する。
  - source vehicle IDs、算出式、標本数、単位変換、根拠URL、参照日を値単位で追跡可能にする。
  - 現行`managed_urban_ev_delivery_v1.yml`は固定baselineとして直接上書きしない。
  - 値を変更する場合は、新しいprofile IDと新規ファイルversion（例：`managed_urban_ev_delivery_v2.yml`）を
    作り、Schema、参照config、decision、manifestの移行関係を記録する。
- [ ] **vehicle profile受入判定後に`motorcar`等との対応を決める。**
  - 代表車両の法的・物理的性質を確定してから、OSM `motorcar`に含まれるかを判断する。
  - 重量、全高、全幅、全長、積載目的等の制限を通過できるかを、固定profileに対して評価する。
  - profile未確定中は`motorcar`から`delivery`への対応を推測せず、fail-closedを維持する。

- [ ] **OSM `goods`・`hgv`の日本向けontologyを別decisionで確定する。**
  - 3.5t以下、3.5〜5t、5〜8t、8t以上、最大積載量5t境界を区別して確認する。
  - OSMの一般的な重量境界を日本へ無条件適用せず、日本の現行法令、道路標識定義、OSM Japan semanticsを
    根拠として照合する。
  - eCanterの車両総重量5.87t等を、重量だけから自動的に`hgv=true`としない。
  - `goods`、`hgv`、SUMO `delivery`、SUMO `truck`の対応はそれぞれ別概念として記録する。

#### この工程が終わると何が分かるか

現行profileが実車分布のどこに位置するか、各値が実車中央値・法規区分・研究固定条件のどれに由来するか、
また道路accessと配送エネルギー実験に同じ代表車両を使用できるかが分かる。これを受け入れた後に初めて、
`motorcar`とmanaged `delivery`の交差を根拠付きで決定できる。

### 4.3 更新

- [ ] keyごとに独立したdecision recordを作る。
  - [x] `horse`: `DEC-P13-HORSE-ONTOLOGY-001`
  - [ ] `motorcar`
  - [x] `psv`: `DEC-P13-PSV-ONTOLOGY-001`
- [x] `psv`を`{bus, taxi}`としてRegistry 1.5.0へ登録し、続いて`horse`を空domainとしてRegistry 1.6.0へ登録する（`motorcar`は未決定）。
- [x] `psv` decisionをsemantic invariant `AR-ACCESS-010`、`horse` decisionを`AR-ACCESS-009`としてtraceabilityへ同期する。
- [x] `psv`・`horse`それぞれの専用fixture/oracleを追加する。
- [x] static access resolverへ`psv`の承認済みdomain・fail-closed境界と、`horse`の承認済みscalar `yes/no`・fail-closed境界を反映する。

### 4.4 実行

- [x] `test_static_access_v17.py`を実行する。
- [x] `test_final_permission_v17.py`を実行する。
- [x] `test_resolver_integration_v17.py`を実行する。
- [x] full-population static access probeを新しい出力へ実行する（horse hierarchy残存0件・新規stable blocker ID 2件、PSV固定blocker 16件解消・新規blocker 0件）。
- [x] 固定container全回帰を実行する（609 passed）。

### 4.5 成果物・完了条件

- [ ] OSM keyからgoverned車種集合への対応表を残す。
- [x] `horse`・`psv`についてdecision、Registry、fixture、oracle、test、probe、stable-ID/permission差分を残す。
- [ ] `OSMタグ → 登録規則 → 対象車種への効果`を第三者が説明できる。
- [ ] blockerが残る場合、その理由と必要な追加証拠を記録する。

## 5. TODO B: 速度blocker 78,616件を原因別に解消する

### この工程の目的

各Directed Segmentの正式な速度を、明示OSM値または承認済み根拠から決められるようにする工程である。
速度は旅行時間、渋滞、電力消費、配送順序の評価へ直接影響するため、根拠のない一律値をformal成果物へ
入れてはならない。

### 現在何が問題なのか

Phase 12 baselineでは、速度規則または証拠を登録できていないrecordが78,601件、未対応の速度表記が
15件ある。`maxspeed`がない道路、別タグから判断できる可能性がある道路、特殊表記を持つ道路が同じ群に
含まれており、現状の総数だけでは解決可能性を判断できない。

### 実際に何をするのか

`maxspeed`がない道路を抽出し、`highway`種別、方向別タグ、zone、条件付きタグ等で分類する。法令や
登録データから正式速度を導ける条件だけをJapan speed rule tableへ登録し、根拠がない道路はblockerの
まま維持する。

```text
maxspeedがない道路を抽出する
  → highway種別・方向・関連タグで分類する
  → 正式な速度根拠を確認する
  → 根拠がある条件だけ規則化する
  → 根拠がない道路はblockerとして維持する
```

### この工程が終わると何が分かるか

正式な根拠から速度を決められる道路と、追加証拠なしには決められない道路を区別できる。解決した速度は
出典、適用条件、Rule IDまで追跡でき、残存blockerには必要な証拠が明示される。

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

### この工程の目的

OSMの総車線数を、走行方向ごとの車線数へ正式に対応させる工程である。SUMOでは方向ごとにedgeとlaneを
生成するため、方向別車線数が不明なままでは正式道路網へ変換できない。

### 現在何が問題なのか

Phase 12 baselineでは、方向別配分の根拠不足が24,114件、lane vector長の競合が18件、車線数の競合が
6件ある。特に双方向道路に`lanes=2`だけがある場合、形式上は`1+1`が自然に見えても、付加車線や
中央車線などの可能性をOSMタグだけで排除できない。structural確認用の仮定をformal値へ昇格してはならない。

### 実際に何をするのか

`lanes`、`lanes:forward`、`lanes:backward`、`lanes:both_ways`、`oneway`を組み合わせて分類する。
一方向道路や方向別明示値など証拠が十分な場合だけ解決規則を適用する。`lanes=2`しかない双方向道路を、
根拠なく正式な`1+1`へ変換せず、必要な外部証拠がなければblockerを維持する。

### この工程が終わると何が分かるか

方向別車線を正式に確定できる道路、タグ競合がある道路、証拠不足で残る道路を区別できる。SUMO laneの
生成根拠と、未生成または停止理由をWay・direction単位で説明できる。

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

### この工程の目的

道路・方向・車線・車種・時刻ごとに、最終的に通行できるかを一つのpermission expectationとして
確定する工程である。特にmanaged `delivery`車両について、どのOSM情報と規則から許可・拒否を決めたかを
追跡できなければ、配送実験で通行可能範囲を正しく定義できない。

### 現在何が問題なのか

4,864件のpermission recordは、適用可能な最終規則を選べず停止している。その上流には1,130件の
root-cause recordがあり、車種対応、未登録access値、条件context、競合、上流lane/relation blockerなどが
混在する。下流permission blockerだけを数えても、直すべき原因は分からない。

### 実際に何をするのか

各permission recordについて、最終判断直前まで到達したstatic/conditional rule、lane、direction、
vehicle class、scenario contextを出力する。例えば`access=no`と`delivery=yes`がある場合、どの規則が
より具体的で、対象時刻・車線へ適用されるかを判断表で確認する。解決結果には候補Rule IDとprovenanceを
残し、before/afterをpermission record IDで比較する。

### この工程が終わると何が分かるか

任意の対象車線について、「OSMのどのaccess情報をどの登録規則で解釈したため、deliveryが通行可能または
通行不可になったか」を説明できる。残存recordは、どの上流原因の解消を待つかが明確になる。

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

### この工程の目的

件数が少なくても、relation方向、未対応access値、速度構文、条件式の誤りは道路接続や通行可否を大きく
変える可能性がある。この工程では、少数blockerを大きな群へ混ぜず、実値と道路を一件ずつ確認して、
安全に規則化できるものだけを解決する。

### 現在何が問題なのか

relation方向48件、unsupported access value 27件、unsupported speed value 15件、conditional syntax
4件などが残る。これらは件数が少ないため一括defaultで消したくなるが、typo、正式OSM値、未知構文、
真正競合が混在し得る。

### 実際に何をするのか

対象relation、値、式をユニーク化し、元Way・member・タグとともに確認する。parser未対応で正式意味が
存在する場合だけRegistry、grammar、実装へ追加する。意味が一意でない場合は自動補正せずblockerを維持する。

### この工程が終わると何が分かるか

少数blockerのうち、実装不足で解決できたものと、データ競合・証拠不足で残るものを一件単位で説明できる。

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

### この工程の目的

fixtureやstage probeで正しく動いた修正が、固定母集団の全道路へ適用しても正しく、かつ同じ条件から
同じ結果を再現できることを確認する工程である。probeは特定stageの影響を見る診断であり、主要成果物、
全validator、2-run決定性を満たす正式runではない。

### 現在何が問題なのか

現在は最初のvehicle ontology修正についてstage probeと全回帰まで完了したが、残りのroot cause処理と
Phase 13正式2-runは未実行である。そのため、Phase 13後のblocker総数、最終成果物、決定性はまだ確定して
いない。

### 実際に何をするのか

主要root causeのdecisionと回帰が完了した後、新しいversion付きoutput rootで`run_1`と`run_2`を完全に
独立実行する。各runで全成果物を最初から生成し、completion validatorを通し、最後にsemantic hashと
実行条件を比較する。`run_2`は`run_1`成果物を読まず、Phase 12公開物も上書きしない。

### この工程が終わると何が分かるか

Phase 13の修正が全道路へ適用された正式成果物と、2回の独立実行で一致する再現性が得られる。また、
Phase 12からどのblockerが解決・残存・変化したかを正式に比較できる。

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

## 11. Final accounting：Phase 13後の道路母集団台帳

### この工程の目的

単なる総件数ではなく、すべての入力道路とその属性recordが最終的にどこへ行ったか分かる状態を作る
工程である。入力に存在した道路が、説明なしに成果物から消えることを防ぐ。

### 現在何が問題なのか

Phase 12にはstage別のpopulation accountingがあるが、Phase 13修正後のresolved、excluded、unresolved等は
まだ再集計されていない。また、Way、direction、lane、vehicle、attributeではidentity unitが異なるため、
総数だけでは道路単位の所在を説明できない。

### 実際に何をするのか

Way IDを入口に、必要に応じてdirection、lane、vehicle、attributeの子recordを結び付け、最終状態、理由、
evidence、Rule IDを記録する。概念上は次のような台帳であるが、実際のidentity unitと保存則は既存仕様を
変更せず使用する。

| OSM Way | 最終状態 | 理由 |
|---|---|---|
| Way A | resolved | 全必要属性を正式に解決 |
| Way B | excluded | 登録済み研究対象外規則に適合 |
| Way C | unresolved | 方向別車線数の根拠不足 |

### この工程が終わると何が分かるか

任意の入力道路について、解決済み、正式除外、未解決等のどこに属するか、その理由と根拠を説明できる。
同時に、母集団保存則から欠落・重複・二重計上がないことを機械検査できる。

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

### この工程の目的

ここで初めて「道路属性成果物をSUMO変換へ入力してよい品質か」を正式に判断する。Phase 13は問題を
修正する工程であり、修正者自身が件数減少だけを見て下流利用を許可する工程ではない。Phase 14は、
独立した入口条件と検査により、属性成果物の利用可否を判定するゲートである。

### 現在何が問題なのか

Phase 13正式2-run、Final accounting、exclusion traceability、残存blocker影響評価が未完了である。
したがってPhase 14の入口条件をまだ満たさず、`attribute_resolution_acceptance=not_run`である。

### 実際に何をするのか

required artifact、Schema、semantic invariant、oracle、stable identity、population conservation、全permission
coverage、exclusion根拠、2-run determinismを機械検査する。すべての入口条件とacceptance検査に合格した
場合だけ、accepted runと成果物hashを記録する。

### この工程が終わると何が分かるか

道路属性成果物をformal SUMO build inputとして使用してよいかがpass/failで確定する。ただし、Phase 14が
承認するのは変換前の属性成果物であり、SUMO道路網の生成完了やNetwork Integration Acceptance合格を
意味しない。

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

### この工程の目的

Phase 14で承認した道路属性を、SUMOが読み込めるnode、edge、lane、connection等の入力形式へ変換する工程で
ある。OSM Wayは一つの道路形状を表すが、SUMOでは走行方向、区間、車線、接続を別の要素として表すため、
単純コピーではなく、承認済みの解釈結果を明示的に投影する必要がある。

### 現在何が問題なのか

Phase 14が未実行であるため、formal SUMO build inputはまだ承認・固定されていない。また、現在の成果物を
SUMO形式へ変換しても、それを正式道路網として使用する権限はない。

### 実際に何をするのか

関係は次のとおりである。

```text
OSM Way
  → Directed Segment（OSM Wayを方向と区間へ分けた研究側record）
  → SUMO Edge（SUMO上の一方向道路区間）
  → SUMO Lane（Edge内の個別車線）
```

OSMにある方向、車線、速度、access等を研究側の承認済み規則で解釈し、その確定結果からSUMO plain XMLを
生成する。同時に、SUMO LaneからDirected Segment、元OSM Wayへ逆引きできるlineageを保存する。

### この工程が終わると何が分かるか

任意のSUMO edge/laneについて、どのOSM Way、方向区間、承認済み属性から生成されたか説明できる。また、
OSM道路がSUMOへ入った、分割された、または省略された理由を後続監査で追跡できる。

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

### この工程の目的

Phase 13〜14で確定した車種別通行判断を、SUMOが実際に強制できる`allow/disallow`へ変換する工程である。
resolverが「deliveryはこの車線を通行できる」と判断しただけでは、SUMOはその判断を知らない。
Permission Materializerがpermission expectationをlaneとconnectionへ書き込むことで、simulation実行時の
経路探索と走行制限へ反映される。

### 現在何が問題なのか

formal permission expectationとSUMO XMLの間には、lane positionの並び、SUMO lane index、connection、
全車種禁止等の変換規則が必要である。この投影が不完全だと、属性側で拒否した車両がSUMOでは通れたり、
許可した車両が経路を作れなかったりする。

### 実際に何をするのか

permission expectationを読み、OSM lane positionをSUMO lane indexへ対応させ、laneとconnectionの
`allow/disallow`を生成する。全lane禁止edgeなどmaterializeできないものは黙って消さず、omission manifestへ
理由を残す。final `net.xml`を人間が直接編集すると、正式入力と生成結果の関係が失われ再現できないため、
修正はgoverned input、Registry、または変換実装へ行い、再度`netconvert`する。

### この工程が終わると何が分かるか

属性成果物で決めた車種別permissionと、SUMO lane/connectionに書かれたpermissionが完全に対応する。
配送車両がなぜ通れる、または通れないかをOSMタグからSUMO XMLまで追跡できる。

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

### この工程の目的

道路同士がどこで接続し、どの車線からどこへ曲がれ、信号がどの接続を制御するかを確定する工程である。
道路属性が正しくても、junction統合やconnection、信号構造が誤っていれば車両は正しく走れない。

### 現在何が問題なのか

SUMOの自動変換は、近接nodeを一つのjunctionへまとめたり、lane間connectionやTLS link indexを生成したり
する。自動候補が研究対象道路の右左折規制、車線構成、信号構造と一致するとは限らない。

### 実際に何をするのか

暫定変換からjunction merge、turn restriction、lane-to-lane connection、signal connection、TLS linkと
phaseの候補を抽出し、元OSMと承認済み規則へ照合する。必要な修正はgoverned XMLまたはdecisionへ記録し、
その入力から再生成する。

### この工程が終わると何が分かるか

各交差点で、どの進入車線からどの退出車線へ接続し、どの右左折が禁止され、どの信号phaseが通行を
制御するか説明できる。

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

### この工程の目的

承認済みnode、edge、connection、TLS、permissionから、再現可能な正式候補`net.xml`を生成する工程である。
これは道路網ファイルを作る工程であり、作られた道路網を下流利用してよいと承認する工程ではない。

### 現在何が問題なのか

Phase 14と各変換・レビューが未完了であるため、正式build inputはまだ存在しない。また、`netconvert`が
exit code 0で終了しても、警告、欠落道路、permission誤投影、接続不良が残る可能性がある。

### 実際に何をするのか

固定したplain XMLと環境を`netconvert`へ渡し、command、全引数、SUMO version、input hash、log、warning、
exit codeをbuild manifestへ記録する。生成後にXSDとSUMO loadを検査し、`net.xml`のhashを固定する。

### この工程が終わると何が分かるか

同じ固定入力と環境から同じ正式候補networkを再生成できる。ただし、構造・lineage・permission・走行の
後続検証に合格するまではaccepted networkではない。

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

### この工程の目的

全入力道路がSUMO側でどのようなnode、edge、laneになったかを数量とidentityの両方で監査する工程である。
単にedge数を数えるのではなく、生成されなかった道路とその理由まで説明できる状態を作る。

### 現在何が問題なのか

OSM Wayは方向分割や交差点分割によって複数SUMO edgeになり得るため、OSM道路数とSUMO edge数は単純には
一致しない。件数差だけでは、正しい分割、正式省略、変換漏れを区別できない。

### 実際に何をするのか

`OSM governed Way → Directed Segment → SUMO Edge → SUMO Lane`をstable identityで結び、基本統計、分割、
非生成、omission、permission、孤立、到達不能を集計する。配送車両については通行可能edge数、延長、
到達範囲を別に算出する。

### この工程が終わると何が分かるか

任意のOSM Wayについて、SUMOへどのように生成されたか、またはなぜ生成されなかったかを説明できる。
道路網の規模と配送車両が実際に利用可能な範囲も定量化できる。

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

### この工程の目的

道路ファイルを生成・loadできることと、車両が意図どおり走行できることは別である。この工程では、
代表的な出発地・目的地（OD）間で実車両を走らせ、静的なXML検査だけでは見つけにくい接続・permission・
信号の問題を確認する。

### 現在何が問題なのか

network候補は未生成であり、route探索、走行、信号通過のruntime検証も未実施である。XMLが妥当でも、
lane connectionが途切れてrouteを作れない、permissionが誤って禁止道路を許可する、信号linkが接続と
対応しない等の問題があり得る。

### 実際に何をするのか

代表ODと期待結果を事前固定して配送車両を走らせる。確認項目の意味は次のとおりである。

- 一方通行: 許可された方向だけを走ること。
- access制限: `delivery`が禁止車線へ入らず、許可車線は利用できること。
- lane connection: 進入車線から正しい退出車線へ連続して移動できること。
- turn restriction: 禁止された右左折・U-turnを経路が使用しないこと。
- signal: 車両が対応する信号linkとphaseに従って停止・進行すること。
- route failure: 到達可能な代表ODで経路生成に失敗しないこと。
- teleport: 接続不良や長時間停止によりSUMOが車両を強制移動していないこと。

### この工程が終わると何が分かるか

配送車両が代表的な道路条件で、方向、permission、connection、turn、signalを守って走行できることが
確認できる。失敗した場合は、どのbuildまたはreview工程へ戻るべきかを特定できる。

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

### この工程の目的

実際に生成されたSUMO道路網そのものを、交通較正、Validation、配送実験へ使用してよいか正式判断する
工程である。Phase 14が変換前の道路属性データを審査するのに対し、本Acceptanceは変換・生成後のnetworkを
審査する。

### 現在何が問題なのか

Phase 14、OSM→SUMO変換、permission投影、構造監査、runtime検証が未完了であるため、道路網候補を下流で
使用する根拠はまだない。`netconvert`が成功したという事実だけでは、lineage、coverage、connectivity、
走行可能性を保証できない。

### 実際に何をするのか

build再現性、XSD/load、warning、OSM→SUMO lineage、permission projection、coverage、omission、connectivity、
runtime試験をまとめて検査し、acceptance reportでpass/failを決定する。不合格時は、失敗原因に対応する
変換、junction、permission、build工程へ戻る。

### この工程が終わると何が分かるか

生成された道路網を下流simulationへ使用してよいかが正式に確定する。ただし、これは道路網の構造・機能の
受入であり、一般交通が現実を十分再現するというValidation合格を意味しない。

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

1. [x] sourcesを登録する。
2. [x] deployment evidenceを実車specと分離して登録する。
3. [x] 1 record = 1実車variantまたはchassis capabilityとするreal vehicle recordsを登録する。
4. [x] M0〜M6のuniverseとF1〜F7のstrataを登録する。
5. [x] canonical recordsだけから`observed_empirical_envelope`を生成するrange generatorを実装する。
6. [x] canonical YAMLからMarkdown 4表を自動生成する。
7. [x] population validatorと自動生成物testを実装し、固定container全回帰まで実行する。
8. [x] TODO、decision record、completion record、Phase 13実行履歴へtraceabilityを追記する。
9. [x] `horse`をmanaged motorized vehicle universeと空交差にする独立decisionを固定する。
   - [x] 固定decisionをRegistry・Invariant・traceability・fixture・oracle・resolverへ実装する。
   - [x] focused testと固定container全回帰を実行する。
   - [x] full-population probeとblocker stable-ID差分を実行する（新規stable blocker ID 2件のため受入不合格）。
10. [x] `psv`とgoverned `bus`・`coach`・`taxi`の交差を独立decisionで決定する（`bus`・`taxi`のみ交差）。
11. [ ] 固定済みの実recordとvehicle populationを参考証拠とし、`motorcar`とmanaged `delivery`の交差、および日本向け`goods`/`hgv`意味論を別decisionで決定する。
12. [ ] 承認されたontology decisionのみをRegistry・Schema・Invariant・traceability・fixture・oracleへ順に反映し、full-population probe、blocker stable-ID差分、固定container全回帰を実行する。
13. [ ] 実行command、結果、ログhash、成果物hashを実行履歴へ追記し、次のroot causeへ反復する。主要root cause処理後はPhase 13正式全道路runを2回独立実行する。

この順序では、vehicle populationは根拠層として固定する。`managed_urban_ev_delivery_v1`は変更せず、Registry 1.6.0には承認済み`psv`・`horse` decisionのみを反映し、`motorcar`は未決定のままとする。
Population追加だけでblocker解消とは判定せず、各ontology decisionの実装とstable-ID差分で効果を確認する。

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
