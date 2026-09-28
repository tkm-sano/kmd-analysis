<a id="東京自動車系sumo-typemap変更履歴"></a>

# 東京自動車系スーモ 道路種別の対応表：変更履歴

## 記録情報

```yaml
document_role: change_history
record_started_at: 2026-07-18
record_updated_through: 2026-07-31
current_configuration_id: ota_ward_sumo_network_v16
current_configuration_version: 16
approved_next_policy_id: ota_ward_attribute_resolution_policy_v17
current_typemap_policy_id: tokyo_motorized_v2
current_specification_reference: 05_src/traffic_simulation/network_current_specification.md

current_status:
  policy:
    approved_v17_core_decisions: fixed
    overall_network_policy: partially_fixed
  implementation: partial
  unit_static_validation: passed
  xsd_validation: passed
  runtime_governance_validation: failed
  real_data_validation: partial
  formal_build_ready: false
```

- 実施者：研究環境管理者（Codex支援）
- 対象ファイル：`reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml`
- 関連設定：`reproducibility/config/traffic_simulation/sumo_network.yml`
- 関連方針：`05_src/traffic_simulation/network_attribute_governance.md`
- 関連実装計画：`05_src/traffic_simulation/implementation_plan.md`

本文書は、道路種別の対応表、道路属性解決処理、通行権限処理、スーモ実変換検証用データおよび
正式 構築停止判断の**時系列変更履歴**である。本文書は現在有効な仕様書ではない。
現在有効な値解決規則と道路網生成順序は
`05_src/traffic_simulation/network_current_specification.md`を参照する。

過去節を単独で現行仕様として引用してはならない。後続節で置き換えられた判断は、
当時の設定と実装を説明する履歴としてのみ有効である。`decision_status`が
`superseded`または`partially_superseded`である節を、新規実装の根拠として使用しては
ならない。

## 現行仕様との責務境界

本文書が保持する内容は次に限定する。

- 道路種別の対応表設計と設定版の変更経緯
- 道路属性解決処理と通行権限反映処理の設計変更履歴
- 固定試験用データ、静的検査、XSD検査および実行時検査の結果
- 不合格内容と、それを受けた後続判断
- 正式 構築を停止した理由

想定条件 Profile、方向付き道路モデル、車線、接続、条件付き規制、速度、正式
道路網 構築 処理工程および実装検証 Stateの完全な現行仕様は、本文書では
再定義しない。現行仕様、設定、個別仕様書および阻害事項の正本は次である。

| 内容 | 現行参照先 |
|---|---|
| 現行道路網仕様 | `05_src/traffic_simulation/network_current_specification.md` |
| 機械可読設定と要件状態 | `reproducibility/config/traffic_simulation/sumo_network.yml` |
| 現在の阻害事項 | `05_src/traffic_simulation/current_issues_and_blockers.md` |
| 版16属性解決の実行記録 | `03_data/metadata/acquisition/20260730_ota_ward_v16_attribute_resolution_run.json` |
| 版16属性解決の今後の手順 | `05_src/traffic_simulation/attribute_resolution_execution_procedure.md` |
| 詳細仕様群 | `05_src/traffic_simulation/specifications/` |

版17の想定条件 Profile、方向付き道路モデル、方向別車線、接続の4軸比較および
二軸値状態は方針固定済みである。条件付き規制の完全な文法、許可台帳、日本速度規則、
正式運用統合および実行時間検証は未完了である。

## 現行方針を読むための要約

この節は履歴を誤読しないための索引であり、完全な決定表ではない。

<a id="typemapの現行責務"></a>

### 道路種別の対応表の現行責務

道路種別の対応表の責務は、採用道路種別の初期ホワイトリスト、仮道路構造生成時の基礎
車種候補、明示的破棄対象およびスーモ 優先順位の初期設定である。

道路種別の対応表は、正式な速度、正式な方向別車線数、正式な`oneway`、最終車線 通行許可
または欠損属性の検証を決定しない。`speed`、`numLanes`、`oneway`を道路種別の対応表から
省略しても、スーモ importerまたはglobal 既定値による補完は防止できない。

```text
typemap attribute omission
!= missing-value validation
```

<a id="permissionsの現行解釈"></a>

### 通行許可の現行解釈

初期設計では、道路種別の対応表 通行許可とオープンストリートマップ 通行許可の積集合を最終値とした。
この方式は後続判断で置き換えられた。現行方針では、道路種別の対応表 通行許可は仮候補、
道路属性解決処理が証拠と規則から生成するexpected 通行許可は正式 正本で
ある。

```text
typemap permissions = provisional candidate permissions
resolver expected permissions = formal authority
final permissions = resolver expected permissions
final permissions <= managed_vclass_universe
```

最終通行許可は生成済み`net.xml`を直接編集して反映しない。最終`netconvert`前の
明示入力へ反映し、車線と接続を再生成した後、期待値との完全一致を監査する。
この反映処理と実行時検証用データは未実装である。

接続規則の具体性は単一の並びではなく、次の軸を分けて扱う。

```yaml
specificity_axes:
  spatial_scope: [way, direction, lane]
  vehicle_scope: [access, vehicle, motor_vehicle, vehicle_class]
  temporal_scope: [unconditional, conditional]
  purpose_scope: [general, destination, delivery, customers]
```

比較原則は、空間軸では`lane > direction > way`、車種軸では
`vehicle_class > motor_vehicle > vehicle > access`、時間軸では適用中の条件付き
規則をunconditional 規則より具体的とし、目的軸ではexplicit 目的をgeneral
目的より具体的とする。異なる軸の規則が競合し一意に比較できない場合は、
便宜的に値を選ばず`conflict`として停止する。完全な接続決定表は現行接続仕様へ
委ねる。

<a id="方向車線およびplaceholderの現行解釈"></a>

### 方向、車線および仮置きの現行解釈

元オープンストリートマップ 道路地物は原典として変更しない。`oneway=-1`は道路地物基準の逆方向方向を意味する。
将来は元道路地物と別の方向付き区間として表現する。方向依存タグ、関係、車線順を
含む実行時検証用データが完成するまで、`oneway=-1`は停止対象として保持する。

```text
source Way direction
!= travel direction
!= SUMO edge ID sign
```

スーモ 道路区間 識別子の符号または座標最近傍を、正式な方向根拠として使用しない。

双方向道路で総車線数だけが明示され、方向別車線数がない場合、偶数総車線を均等配分
した値を正式値として自動採用しない。構造確認用に限って使用する場合は
`value_origin: model_assumed`および
`assumption_id: BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`を記録し、
`formal_eligible: false`とする。正式では
`stop_code: LANE_DIRECTIONAL_ALLOCATION_MISSING`として停止する。
`lanes:both_ways`、可逆車線および時間帯別車線は、受理済み規則がない間は
`unsupported`または`unresolved`とする。

一意最頻値、標本数30以上、最頻値比率50%以上による処理は
`structural_placeholder_generation`であり、`formal_attribute_resolution`ではない。
これは形状・接続確認専用であり、正式 道路網、較正、独立検証または配送評価に
使用できない。仮置きを含む道路網の較正結果を正式 道路網へ引き継がない。
集計母集団、道路地物数重み、道路長重み、範囲および閾値感度は未完了であり、これらの
閾値を東京の経験的代表値として解釈しない。

### 車両クラスと値状態の現行解釈

版17の基準車両は`managed_urban_ev_delivery_v1`である。スーモ `delivery`、電池
device、最大許容質量3,500 kg、非積載質量1,500 kg、最大積載量2,000 kgを使用し、
オープンストリートマップ `hgv`対象には含めない。これらは実在車両の測定値ではなく研究上のモデル値である。

値の解決結果は、可能な範囲で次の二軸として解釈する。

```yaml
resolution_status:
  - resolved
  - not_applicable
  - unresolved
  - conflict
  - unsupported
  - invalid
value_origin:
  - source_explicit
  - source_normalized
  - rule_derived
  - evidence_derived
  - model_assumed
  - derived_validated_model
```

正式候補は、`resolution_status=resolved`であり、かつ正式で承認された
`value_origin`を持つ場合に限る。`model_assumed`と未検証仮置きは正式不適格
である。`derived_validated_model`は、モデル識別子、版、学習母集団、検証母集団、
評価指標、受入規則および独立検証記録が揃う場合だけ正式候補となる。現行成果物の
旧`value_state`は読取互換だけに残し、版17新規成果物は二軸を正本とする。データ構造は
作成済みだが正式運用出力の移行は未完了である。

## 時系列作業ログ

### 1. 作業目的を確定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v4, until: v13}
superseded_by: [section-23, section-26, section-27]
```

初期スーモ道路網へ採用するオープンストリートマップ道路種別とスーモ 車種を明示的なホワイトリストとして固定し、歩行者、自転車、鉄道、船舶等の対象外リンクが標準道路種別の対応表の暗黙動作によって混入しない構成を目標とした。

また、`lanes`、`maxspeed`、`oneway`の欠損を道路種別の対応表既定値で黙って補完しないことを前提とした。これらの属性は、後続の属性ガバナンス処理で値状態と根拠を記録したうえで、変換用オープンストリートマップ 拡張マークアップ形式へ明示する。

### 2. 固定Docker環境の利用可否を確認した

```yaml
decision_status: historical_failure
effective_configuration: {from: v4, until: v4}
superseded_by: [section-13]
```

研究環境で固定しているスーモコンテナを使って`netconvert`の版を確認しようとしたが、Docker daemonが停止していたため実行できなかった。この時点ではホストへ別の`netconvert`を導入せず、研究設定と同じスーモ 1.24.0の公式ソースを参照して設計を進めることにした。

未実施となった確認：

```bash
docker compose run --rm sumo netconvert --version
```

<a id="3-sumo-1240の上流資料を固定した"></a>

### 3. スーモ 1.24.0の上流資料を固定した

```yaml
decision_status: active
effective_configuration: {from: v4, until: null}
superseded_by: []
```

最新ブランチではなく、研究設定と一致するGit 属性タグ `v1_24_0`から次の資料を参照した。

- 標準道路種別の対応表：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/typemap/osmNetconvert.typ.xml>
- types schema：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/types_file.xsd>
- base types schema：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/baseTypes.xsd>
- OSM import documentation：<https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html>

標準道路種別の対応表を取得し、SHA-256を計算した。

```bash
curl -fsSL \
  https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/typemap/osmNetconvert.typ.xml \
  | shasum -a 256
```

結果：

```text
e3de4b6aadd2e6bf0d0f6186d84c621bbf807e65b81bba9aec8fe0d7b0d77786
```

<a id="4-リポジトリ内の対象範囲と上流typemapを照合した"></a>

### 4. リポジトリ内の対象範囲と上流道路種別の対応表を照合した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v4, until: v14}
superseded_by: [section-26, section-27]
```

標準道路種別の対応表からオープンストリートマップ 種類 識別子と優先順位を抽出し、`sumo_network.yml`の`vehicle_scope.keep_vclasses`および実装計画の初期交通モードと照合した。その結果、共用自動車道路、スーモの作業 compound 種類、専用バスリンクを採用対象とした。

一方、歩行者、自転車、鉄道等の専用リンクと初期研究範囲外の道路種別は、暗黙に落とすのではなく`discard="true"`で明示的に除外する方針とした。道路種別の対応表に存在しない未知種類は正式処理で採用せず、警告と除外件数を構築 まとめへ記録する方針とした。

<a id="5-typemapの採用規則を決定した"></a>

### 5. 道路種別の対応表の採用規則を決定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v4, until: v14}
superseded_by: [section-12, section-19, section-26, section-27]
```

共用自動車道路として、次のオープンストリートマップ `highway`値を採用することにした。

```text
motorway, motorway_link,
trunk, trunk_link,
primary, primary_link,
secondary, secondary_link,
tertiary, tertiary_link,
unclassified, residential, living_street, service
```

基本の許可車種を次に限定した。

```text
passenger,taxi,bus,coach,delivery,truck,motorcycle,moped
```

追加規則は次のとおりとした。

- `motorway`と`motorway_link`ではmopedを許可しない。
- `highway.service|psv`と`highway.service|bus`では`bus delivery`を許可する。
- `highway.bus_guideway`と`highway.busway`では`bus`だけを許可する。
- オープンストリートマップの明示的な`access`、`vehicle`、`motor_vehicle`等は、道路種別の対応表の基本権限をさらに制限できるものとする。
- `speed`、`numLanes`、`oneway`は道路種別の対応表に記述しない。
- 優先順位はスーモ 1.24.0標準道路種別の対応表の道路階層を維持するが、速度、車線数、一方通行の代用にはしない。

明示的な除外対象は次のとおりとした。

- 未舗装・作業道等：`highway.unsurfaced`、`highway.track`
- 歩行者系：`highway.footway`、`highway.pedestrian`、`highway.path`、`highway.bridleway`、`highway.step`、`highway.steps`、`highway.stairs`
- 自転車専用：`highway.cycleway`
- 初期範囲外：`highway.raceway`、`highway.ford`、`highway.construction`
- 鉄道系：`railway.preserved`、`railway.tram`、`railway.subway`、`railway.light_rail`、`railway.rail`、`railway.highspeed`、`railway.construction`

<a id="6-カスタムtypemapを作成した"></a>

### 6. カスタム道路種別の対応表を作成した

```yaml
decision_status: validation_record
effective_configuration: {from: v4, until: v4}
superseded_by: [section-12, section-14, section-26, section-27]
```

決定したホワイトリスト、許可車種、除外種類、標準優先順位を反映して、次のファイルを作成した。

```text
reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml
```

上流標準道路種別の対応表との主な差は、多交通モードを含む汎用定義から東京の初期自動車系道路網に限定したこと、対象外種類を明示的に破棄したこと、`speed`、`numLanes`、`oneway`の既定値を削除したことである。

作成後にSHA-256を計算した。

```bash
shasum -a 256 \
  reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml
```

結果：

```text
d86ab83e7b8afa94c4d13e0669a146cf18809e2e6af3ce8fee1e24a6a1fcd8c2
```

### 7. 設定と実装計画へ反映した

```yaml
decision_status: superseded
effective_configuration: {from: v4, until: v4}
superseded_by: [section-12]
```

`sumo_network.yml`を設定版v4、設定識別子 `ota_ward_sumo_network_20260716_v4`へ更新した。`typemap_policy`へカスタム道路種別の対応表のパスとハッシュ、上流資料のURLとハッシュ、採用種類、許可車種、属性既定値を持たせない方針を記録した。

また、カスタム道路種別の対応表を未実装要件から外し、残る属性ガバナンス処理、補助表、道路網生成パイプラインを`implementation_plan.md`の未実装作業として整理した。取得記録案内文書から本ファイルを参照できるようにした。

<a id="8-設定とxmlの不整合を検出するテストを追加した"></a>

### 8. 設定と拡張マークアップ形式の不整合を検出するテストを追加した

```yaml
decision_status: validation_record
effective_configuration: {from: v4, until: null}
superseded_by: []
```

`05_src/traffic_simulation/validation/test_sumo_typemap.py`を追加し、次を検査するようにした。

- ヤムル形式が参照する道路種別の対応表パスとSHA-256が実ファイルに一致する。
- 拡張マークアップ形式内に重複種類 識別子がない。
- 非破棄 種類がヤムル形式の明示的ホワイトリストと一致する。
- 許可車種が研究対象分類の部分集合である。
- `speed`、`numLanes`、`oneway`が道路種別の対応表に存在しない。
- 代表的な歩行者、自転車、鉄道、工事中種類が明示的に破棄される。

### 9. XSD検証と対象テストを実行した

```yaml
decision_status: validation_record
effective_configuration: {from: v4, until: v4}
superseded_by: []
```

スーモ 1.24.0のデータ構造を取得し、拡張マークアップ形式を検証した。

```bash
curl -fsSL \
  https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/types_file.xsd \
  -o /tmp/types_file.xsd
curl -fsSL \
  https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/baseTypes.xsd \
  -o /tmp/baseTypes.xsd
xmllint --noout --schema /tmp/types_file.xsd \
  reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml
```

結果：`osm_tokyo_motorized.typ.xml validates`

関連する単体テストも実行した。

```bash
PYTHONPATH=05_src pytest -q \
  05_src/traffic_simulation/validation/test_sumo_typemap.py \
  05_src/traffic_simulation/validation/test_analyze_osm_attributes.py \
  05_src/traffic_simulation/validation/test_research_stage.py
```

結果：`37 passed`

### 10. リポジトリ全体のテストと実行時検証を試みた

```yaml
decision_status: historical_failure
effective_configuration: {from: v4, until: v4}
superseded_by: [section-13]
```

ホスト環境でリポジトリ全体のpytestを実行したが、ホストPythonに`folium`がなく、`test_render_baseline_demand.py`の取込み時に収集が停止した。`folium==0.20.0`は分析用Docker環境に固定されているため、ホストへ追加導入せず、Docker daemon復旧後に固定環境で再実行することにした。

Docker daemonが停止しているため、次の実行時検証は未実施である。

- Docker内の`netconvert --version`確認
- 道路種別の対応表を使った実オープンストリートマップ 拡張マークアップ形式の変換
- 生成した`net.xml`のスーモ コマンド操作読込

実オープンストリートマップ 拡張マークアップ形式の変換は、`build_sumo_network.py`と属性ガバナンス処理も未実装であるため、現段階では実行できない。XSD適合と単体テスト成功だけでは`net.xml`生成成功を保証しない。

### 11. 現在の状態を確定した

```yaml
decision_status: superseded
effective_configuration: {from: v4, until: v4}
superseded_by: [section-13]
```

道路種別の対応表、設定、整合性テスト、本記録は作成済みである。一方、固定スーモ環境での実変換が完了していないため、状態を`implemented_not_runtime_validated`とし、`status.implementation: pending`および`formal_build_ready: false`を維持した。

<a id="12-欠損検出とpermissions迂回に関するレビューを反映した"></a>

### 12. 欠損検出と通行許可迂回に関するレビューを反映した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v5, until: v8}
superseded_by: [section-13, section-18, section-19, section-20]
```

初版作成後、道路種別の対応表から`speed`、`numLanes`、`oneway`を省略しても、`netconvert`のimporter-levelまたはglobal 既定値を防げず、属性欠損時の停止を保証しないとのレビューを受けた。スーモ公式文書でも`default.lanenumber=1`、`default.speed=13.89 m/s`が定義され、種類属性自体は任意であることを再確認した。また、`ignoring`は車線 通行許可を無視でき、`osm.lane-access`は既定で無効であることを確認した。

参照した公式資料：

- <https://sumo.dlr.de/docs/netconvert.html>
- <https://sumo.dlr.de/docs/Simulation/VehiclePermissions.html>
- <https://sumo.dlr.de/docs/SUMO_edge_type_file.html>
- <https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html>

この確認を受け、設定をv4からv5へ更新し、次を決定した。

- 属性省略は検証 mechanismではないと拡張マークアップ形式コメントと設定に明記する。
- 保持対象道路地物は`netconvert`前に`lanes`、`maxspeed`、`oneway`の採用値と必須来歴をすべて持たせ、不足時に停止する。
- `structural_placeholder`は構造確認用に限るが、使用道路地物を分離して全件記録する。
- `ignoring`、`custom1`、`custom2`と管理対象外vClassを`vType`、`vehicle`、`flow`、`trip`入力で禁止する。
- `osm.lane-access=true`と`osm.annotate-defaults=true`を固定する。
- 未知種類、未知compound 種類、道路区間追加失敗を停止対象とし、道路区間除外は明示的破棄と照合できない場合に停止する。
- 変換後に通行許可が道路種別の対応表の基本通行許可を超えていないことと、未承認既定値由来値がないことを監査する。
- 道路地物単位と車線単位の接続タグを含む検証用データによるスーモ 1.24.0実変換試験を必須とする。

拡張マークアップ形式のルール自体は変更せずコメントを訂正したため、ファイルの新しいSHA-256は次となった。旧ハッシュ`d86ab83e7b8afa94c4d13e0669a146cf18809e2e6af3ce8fee1e24a6a1fcd8c2`は初版の記録として残す。

```text
6c667e13f405b78b86b999abb141f13e99bc88c35187af8a007e2318cefb83cf
```

これらは現時点では設定とテストで固定した実装要件であり、前処理検証器、車両入力検証器、変換ログ・生成ネットワーク監査は未実装である。したがって、現ファイルだけで「欠損時に必ず停止する閉じたホワイトリストが完成した」とは扱わない。

修正後に同じXSD検証と関連テストを再実行し、拡張マークアップ形式のXSD適合と`39 passed`を確認した。これは設定の静的整合性確認であり、未実装検証器や実際の接続変換動作を検証した結果ではない。

<a id="13-固定sumo-1240でgovernance-fixtureを実変換した"></a>

### 13. 固定スーモ 1.24.0で管理検証用データを実変換した

```yaml
decision_status: validation_record
effective_configuration: {from: v5, until: null}
superseded_by: []
```

Docker daemonが利用可能になったため、ハッシュ値固定した`sumo`サービスで版を確認した。

```bash
docker compose run --rm sumo netconvert --version
```

結果は`Eclipse SUMO netconvert Version 1.24.0`であり、設定の期待版と一致した。

次に、`05_src/traffic_simulation/validation/fixtures/osm_typemap_governance.osm.xml`を作成した。この検証用データは、道路地物単位の`access=no`と車種別例外、`motor_vehicle=no`、車線単位の`access:lanes`と`vehicle:lanes`、および`lanes`、`maxspeed`、`oneway`をすべて欠く負例を含む。カスタム道路種別の対応表、`osm.lane-access=true`、`osm.annotate-defaults=true`を指定して実変換した。

変換自体は終了コード0となったが、governance検証は次の理由で失敗と判定した。

- 道路地物 100の`access=no`、`bus=yes`から未知compound警告`Discarding unknown compound 'bus'`が発生し、生成車線に`bus bicycle`が許可された。`bicycle`は道路種別の対応表の基本通行許可を超える。
- 道路地物 200の`motor_vehicle=no`、`delivery=yes`は期待した配送限定にならず、道路種別の対応表の基本8クラスがすべて残った。
- 道路地物 300の`access:lanes=no|yes`は、生成された2 車線の通行許可を期待どおり制限しなかった。
- 道路地物 400の`vehicle:lanes=no|yes`では、生成車線の一つに`private`が追加され、道路種別の対応表の基本通行許可を超えた。
- 属性欠損の道路地物 600は停止せず、1 車線、13.89 m/sで生成され、`osmDefaults="numLanes speed"`が記録された。

この結果は、道路種別の対応表の`allow`だけではオープンストリートマップ 接続変換後の通行許可上限を保証できず、属性省略だけでも欠損停止を保証できないことを実証した。設定へ実測した失敗状態と実際の警告文字列を記録し、`access_permission_mapping_resolution`を未完了要件へ追加した。前処理で接続を正規化するか、対応compound 種類を追加するかは、検証用データの全ケースを期待どおり変換できるまで確定しない。

記録と静的検査の更新後、関連ホストテストは`40 passed`、analysisコンテナ内の検証 検証一式は`135 passed`、スーモ 1.24.0 XSD検証は成功した。これらの成功は検証用データのgovernance不合格を解消するものではない。

<a id="14-oneway左側通行ev-vclassの追加レビューを反映した"></a>

### 14. `oneway`、左側通行、電気自動車 vClassの追加レビューを反映した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v6, until: v14}
superseded_by: [section-18, section-26, section-27, section-28]
```

追加レビューで、種類定義の`oneway`省略時は既定値`true`となるため、前処理漏れが道路を一方通行化し得るとの指摘を受けた。固定スーモ 1.24.0で検証用データを再変換し、`oneway`を欠く道路地物 600について、正方向の道路区間 `600`だけが生成され、逆方向道路区間 `-600`が存在しないことを確認した。また、生成道路区間の`osmDefaults`は`numLanes speed`だけを記録し、欠損`oneway`の代替値を記録しなかった。

この結果から、`osm.annotate-defaults=true`による変換後監査だけでは`oneway`欠損を検出できないと判断した。一般道路をオープンストリートマップ規則により双方向と導出した場合も、前処理で`oneway=no`と来歴を変換用拡張マークアップ形式へ必ず具体化する。値または来歴がない保持道路地物は`netconvert`前に停止する。

東京の左側通行については、`traffic_side.lefthand=true`と`netconvert.common_options.lefthand=true`が既に設定され、検証用データ実変換でも`--lefthand=true`を使用したことを確認した。オープンストリートマップの一方通行方向自体を反転する設定ではないため、`reverse_osm_oneway_direction=false`を維持する。

電気自動車配送車のvClassも明確化した。初期電気自動車配送車は`vClass="delivery"`で道路利用区分を表し、電動パワートレインはスーモ 電池 deviceで別に設定する。道路種別の対応表で許可していない`evehicle`は、`ignoring`、`custom1`、`custom2`とともに明示的禁止対象とした。`hov`と`trailer`を含むその他の非管理クラスも`reject_ungoverned_vclass=true`により拒否する。

この変更で設定をv5からv6へ更新した。道路種別の対応表のルール本体は変更せず、`oneway`、`speed`、`numLanes`の具体的代替値リスクをコメントへ追記したため、道路種別の対応表のSHA-256は次となった。旧v5ハッシュ`6c667e13f405b78b86b999abb141f13e99bc88c35187af8a007e2318cefb83cf`は前節の履歴として残す。

```text
4e4273a5a73b8d1298751aeee141a387dc6a1524d64ed8ddd704cae8db0af590
```

v6更新後、関連ホストテストは`41 passed`、analysisコンテナ内の検証 検証一式は`136 passed`、スーモ 1.24.0 XSD検証は成功した。設定識別子、設定版、道路種別の対応表 SHA-256の一致も確認した。実行時間 検証用データは引き続き不合格であり、正式利用不可の状態は変えていない。

### 15. 設計判断の分類と感度分析を修正した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v7, until: v14}
superseded_by: [section-26, section-27]
```

追加レビューを受け、`priority`、道路ホワイトリスト、vClass 通行許可、属性省略、検証器未完成、検証用データ合成値を同じ「恣意性」尺度で評価する整理を修正した。感度分析前に影響の大小を順位付けせず、次のように区別する。

- `priority`：東京への地域適合性の制限を伴う設計判断
- 道路ホワイトリスト：研究対象範囲の設計判断
- vClass 通行許可：車種別通行条件の設計判断
- 専用バス道路：ネットワーク表現上の設計判断
- 道路種別の対応表での属性省略：根拠付き属性を要求する設計判断
- 検証器と変換後監査の未完成：高い実装・品質保証リスク
- 検証用データ数値：東京代表値ではないが正式実験から隔離した合成テスト入力

スーモ公式資料を再確認し、標準`osmNetconvert.typ.xml`はドイツの市街地外道路向けとして説明されていることを記録した。スーモ 1.24.0標準優先順位の継承は結果確認後の個別調整を避けるが、東京への実証的妥当性を保証しない。

- <https://sumo.dlr.de/docs/OsmNetconvert.typ.xml.html>
- <https://sumo.dlr.de/docs/SUMO_edge_type_file.html>
- <https://sumo.dlr.de/docs/Simulation/Routing.html>

また、固定スーモ 1.24.0の`sumo`と`duarouter`について`--save-template`を実行し、両方の`weights.priority-factor`既定値が`0`であることを確認した。基準条件でも`weights.priority-factor=0`を明示し、優先順位を静的経路コストへ直接加えない。優先順位は交差点のright-of-道路地物、停止、待ち時間、遅延、実現旅行時間への影響を主に確認する。実現旅行時間を使う再経路探索では間接的に経路が変わり得るため、その場合は別に記録する。

vClass数も再確認した。管理集合は8クラスだが、通常道路が8、motorwayとmotorway_linkがmopedを除く7、作業 compoundが2、専用バス道路が1クラスである。「すべての道路で8クラスを許可する」とは表現しない。

設定をv6からv7へ更新し、`design_decision_assessment`と`design_sensitivity`を追加した。優先順位はスーモ標準、全種類同一優先順位 1、固定した3段階階層を比較し、交差点待ち時間、停止回数、旅行時間、遅延を主指標とする。作業 通行許可、専用バス道路、`track`、未解決属性も、それぞれの作用経路に対応した接続性、到達可能性、経路、距離、代替値等の指標を固定した。

相対変化は基準値が0でない場合に`abs(M_alternative - M_baseline) / abs(M_baseline)`で報告し、基準値が0なら絶対差を報告する。「影響が小さい」と判定する数値閾値は根拠を伴う事前登録が未完了であるため、現時点では合否判定へ使用しない。道路種別の対応表本体は変更しておらず、SHA-256はv6と同じである。

v7更新後、関連ホストテストは`42 passed`、analysisコンテナ内の検証 検証一式は`137 passed`、スーモ 1.24.0 XSD検証は成功した。設定識別子、設定版、道路種別の対応表 SHA-256の一致も確認した。実行時間 検証用データの不合格と`formal_build_ready: false`は維持している。

<a id="16-属性補完規則正式利用条件access解決順を固定した"></a>

### 16. 属性補完規則、正式利用条件、接続解決順を固定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v8, until: v8}
superseded_by: [section-18, section-19, section-25, section-30]
```

追加レビューを受け、構造確認用仮置きの具体値を先に決めず、値を決める統計規則と正式実験へ使用できる状態を先に固定した。固定大田区オープンストリートマップ抽出の明示値を母集団とし、`lanes`は道路種別と一方通行・双方向、`maxspeed`は道路種別で集約する。一意な最頻値、標本数30以上、最頻値比率50%以上を満たす場合だけ非重要道路の`structural_placeholder`として使用し、同率、標本不足または比率不足では近い道路種別へ移らず`unresolved`とする。具体値は分布集計後に別途固定する。

`oneway`への統計補完は禁止した。明示値`yes`、`no`、`-1`を優先し、`-1`は道路地物方向を反転して`yes`へ具体化する。明示値がない環状交差点とmotorwayはオープンストリートマップ暗黙規則による`yes`、motorway_linkは`unresolved`、その他の一般道路はオープンストリートマップデータ消費規則による`no`とした。現在の大田区基礎集計ではmotorway・motorway_linkの`oneway`欠損は0件だが、将来入力のために規則を固定した。

正式実験では未検証仮置きを禁止する一方、推定値一般を禁止するのではなく、事前定義した補完モデルと独立した検証記録を持つ`derived_validated_model`を値状態へ追加した。モデル識別子、版、学習母集団、検証母集団、評価指標、受入規則および検証記録を必須とした。

通行許可は、オープンストリートマップ内で`access`、`vehicle`、`motor_vehicle`、車種別、方向別、車線別の順に具体的規則を上書きした後、研究対象集合との積集合を取る。スーモ importerの結果が期待値と一致しない場合に許可する後処理は積集合による縮小だけとし、道路種別の対応表基本集合の拡張を禁止した。補正後は接続を再検査する。

ネットワークの管理集合8クラスと用途別生成集合も分離した。配送経路用途は`delivery`と`truck`、初期背景交通用途は`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`とした。`moped`は通行許可管理集合には残すが、需要根拠を固定するまで背景交通として生成しない。専用バス道路は現行v1でbus-onlyを維持し、配送例外を採用する場合は新しいcompound 種類、検証用データおよび設定版を必要とする。

この変更で`sumo_network.yml`をv7からv8へ更新した。道路種別の対応表本体は変更していないためSHA-256は変わらない。実行時間 検証用データの既知の不合格は未解消であり、`formal_build_ready: false`を維持する。

参照した仕様：

- <https://wiki.openstreetmap.org/wiki/Key:oneway>
- <https://wiki.openstreetmap.org/wiki/Key:access>
- <https://wiki.openstreetmap.org/wiki/Key:lanes>
- <https://wiki.openstreetmap.org/wiki/Key:maxspeed>
- <https://sumo.dlr.de/docs/netconvert.html>

<a id="17-osm属性resolverと変換前品質ゲートを実装した"></a>

### 17. オープンストリートマップ属性属性解決器と変換前品質ゲートを実装した

```yaml
decision_status: superseded
effective_configuration: {from: v8, until: v8}
superseded_by: [section-18, section-19, section-20, section-24, section-30]
```

2026年7月19日、`05_src/traffic_simulation/network/resolve_osm_attributes.py`を追加した。このモジュールは、固定設定v8を検証してからオープンストリートマップ 拡張マークアップ形式の保持対象道路地物を処理し、`oneway`、`lanes`、`maxspeed`を変換用拡張マークアップ形式へ具体化する。道路地物・方向・車線ごとにオープンストリートマップ 接続規則を広い規則から具体的な規則へ解決し、道路種別の対応表基本通行許可との積集合を期待値として監査コンマ区切り形式へ保存する。通行許可計算に使用した接続タグは、スーモ importerによる別解釈を避けるため、品質ゲート合格後の正規化拡張マークアップ形式から除去する。

`oneway=-1`はノード順と方向別タグを反転して`oneway=yes`へ正規化する。環状交差点とmotorwayの暗黙規則、motorway_link欠損の停止、一般道路の双方向導出も実装した。`lanes`と`maxspeed`は明示値を優先し、構造確認用では非重要道路に限り、v8で事前固定した一意最頻値規則を適用できる。重要度が未分類の道路地物へ仮置きを自動適用しない。正式処理設定では構造用仮置きを使用しない。

接続 属性解決器はv8で明示した`access`、`vehicle`、`motor_vehicle`、`motorcar`、`hgv`、`bus`、`delivery`と、方向別・車線別の対応タグを管理する。`goods`、`coach`、`taxi`、`psv`、`motorcycle`、`moped`等を含む未登録の車種別タグ、未対応値、条件付きタグ、曖昧な双方向車線指定、車線数不一致、管理外の接続規則は`unresolved`として停止する。対応範囲の拡張は設定版を上げて行う。生成通行許可を広げる処理は実装していない。

正常系と欠損負例を次へ分離した。

```text
05_src/traffic_simulation/validation/fixtures/osm_attribute_resolution_positive.osm.xml
05_src/traffic_simulation/validation/fixtures/osm_attribute_resolution_negative.osm.xml
```

`test_resolve_osm_attributes.py`では、v8設定読込、最頻値条件、明示・暗黙方向、`-1`反転、構造用補完、正式停止、接続上書き、車線別通行許可、条件付き規則、属性矛盾、監査コンマ区切り形式および原子的拡張マークアップ形式出力を検査する。属性解決器と道路種別の対応表の対象テストは`36 passed`であった。

この実装はPBFからオープンストリートマップ 拡張マークアップ形式への変換、外部データ補完表の取込み、重要道路の機械判定、生成`net.xml`への通行許可適用、変換ログ・出力監査、スーモ コマンド操作読込を含まない。既存実行時間 検証用データの不合格は未解消であり、正式構築は引き続き禁止する。

<a id="18-resolverレビューを反映し停止境界と監査成果物を強化した"></a>

### 18. 属性解決器レビューを反映し、停止境界と監査成果物を強化した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v9, until: v13}
superseded_by: [section-19, section-23, section-25, section-30]
```

2026年7月19日、17節の実装に対して、除外道路が拡張マークアップ形式に残る、未対応の明示値を構造用最頻値で上書きし得る、双方向1車線を各方向1車線として扱う、接続タグ削除後の期待通行許可が専用成果物に残らない、`oneway=-1`反転が左右依存タグを壊し得る、というレビューを受けた。これらは定量評価以前に解消すべき実装上の問題と判断した。

設定をv8からv9へ更新し、次を実装した。

- 保持対象外の`highway=*` 道路地物を正規化拡張マークアップ形式ツリーから物理的に削除する。
- `missing`、`invalid`、`valid_but_unsupported`、`conflict`、`conditional`、`directionally_asymmetric`を分離し、構造用最頻値を真の欠損だけに適用する。
- `50 mph`等の未対応明示値、方向別に異なる速度、条件付き速度、未対応方向別車線表現を補完で上書きせず停止する。
- 双方向`lanes=1`を各方向1車線へ複製せず、車線方向配分を未解決として停止する。方向別タグのない偶数総車線は均等分割仮定を専用監査行へ記録し、感度分析未完了として扱う。
- `oneway=-1`は有効なオープンストリートマップ値だが、左右・方向依存タグを安全に網羅変換できるまでは元道路地物を変更せず停止する。
- 接続タグを正規化拡張マークアップ形式に保持し、道路地物・方向・車線別の期待通行許可を必須ジェイソン形式へ永続化する。生成`net.xml`への縮小方向の反映と全車線照合は後続実装とし、完了まで正式構築を禁止する。
- `designated`をキーと値の組合せで評価し、一般キーの`access=designated`を停止する。車種別適用順はヤムル形式の並びではなくコード側の固定順から作る。
- 車線数と速度の補完閾値を別フィールドとして読み、両者が同値であることをコードで強制しない。
- 補完集計を「local」ではなく`input_extent_way_count_unique_mode`と呼び、入力オープンストリートマップ SHA-256、母集団範囲、道路地物個数という標本単位、グループ定義、属性別閾値、完全分布、採用値、最頻値比率、判断を必須ジェイソン形式へ保存する。

補完母集団が入力範囲とオープンストリートマップ 道路地物分割に依存する問題、道路地物個数重みと道路延長重みの比較、抽出範囲・集約範囲・閾値の感度分析、属性別重要度の根拠スキーマはデータと事前登録を要する方法論課題であり、コードだけで値を決めなかった。これらをv9の未完了要件へ登録し、`structural`成果物は引き続き形状・接続確認専用、`formal_build_ready: false`とした。

この節は17節の`oneway=-1`反転と接続タグ削除の記述を置き換える。履歴を時系列で追跡できるよう、17節の初期実装記録自体は削除していない。

v9更新後、属性解決器と道路種別の対応表の対象テストは`42 passed`、固定`analysis`コンテナ内の検証 検証一式は`170 passed`であった。これは前処理の停止境界と静的整合性を検査した結果であり、既知のスーモ 実行時間 検証用データ不合格、通行許可後処理、実PBF 構築、定量評価への適格性を解消するものではない。

<a id="19-formal先行順序と交通モデル品質ゲートを固定した"></a>

### 19. 正式先行順序と交通モデル品質ゲートを固定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v10, until: v10}
superseded_by: [section-20, section-21, section-23]
```

2026年7月19日、道路構造、需要・信号、較正、独立検証、配送最適化を分離する段階方針を再検討した。`structural_placeholder`を含む道路網で較正した後に正式道路属性を変更すると、較正値が構造誤差を補償し得るため、正式基準ネットワークの完成を需要投入と較正より前へ明示的に移した。

設定をv9からv10へ更新し、次を決定した。

- `structural生成 → 構造デバッグ → 属性・permissions確定 → formal基準ネットワーク → 需要・信号 → 較正 → 独立検証 → 配送・古典・QAOA評価`の順序を必須とする。
- 正式ネットワークまたは需要定義を変更した場合、それ以前の較正・検証結果を失効させる。
- 構造ゲートでは、管理対象オープンストリートマップ 道路地物の説明可能な保持率、主要道路対の到達可能率、最大連結成分の道路長割合、方向不一致件数、代表出発地・到着地経路成功率、スーモ読込、注意事項分類を計算する。
- 合格数値は結果を見る前に根拠付きで登録し、未登録の間は正式へ昇格させない。普遍的根拠のない95%等の値をコードへ仮置きしない。
- 注意事項を停止対象、承認済み、情報通知へ分類し、未分類注意事項は停止する。
- オープンストリートマップ 道路地物とスーモ 車線を一対一と仮定せず、`OSM way → 複数SUMO edge → 複数lane`の来歴を保存する。全車線をオープンストリートマップ由来情報または明示生成規則へ追跡できなければ停止する。
- 通行許可後処理は縮小だけに限定せず、明示オープンストリートマップタグ、公的規制情報またはレビュー済み証拠から導出した期待値へ完全一致させる。根拠のない拡張と道路種別の対応表基本集合を超える拡張は禁止する。
- スーモ版だけでなく、両コンテナのハッシュ値、PROJ、`osmium`、Python、依存固定、platform、locale、出力精度、全入力・設定・`.netccfg`のSHA-256および完全なコマンドを構築 成果物一覧へ保存する。
- 日本道路交通情報センター等の保存期間が短い観測データは道路網パイプラインと並行取得する。モデル投入は正式完成後とする。
- 交通量、速度、旅行時間、渋滞、信号条件は原則として同一日・同一時間帯で組み合わせ、異なる日時を混ぜる場合は補正と追加不確かさを記録する。
- 較正は需要、容量・飽和交通流、経路選択、旅行時間・速度・待ち行列、局所微調整の順に行い、全パラメータ群を同時に自由化しない。
- 較正・検証は事前固定した複数乱数の種、ウォームアップ規則、評価時間帯で行い、反復数は出力分散と必要な信頼区間から決める。
- 道路属性レビューは最終経路だけでなく、デポ、全顧客、充電施設間で全比較手法が選択可能な候補部分グラフを対象とする。
- 古典手法と量子近似最適化アルゴリズムは同一インスタンス、目的関数、制約、実行可能性判定、復号・修復規則、乱数の種集合で比較し、同一予算比較と最良基準比較を分離する。

これらは方法論と停止条件の固定であり、具体的な構造ゲート閾値、較正指標閾値、乱数の種集合、ウォームアップ時間、日本道路交通情報センター定期取得、通行許可後処理および来歴監査の実装完了を意味しない。これらをv10の未完了要件へ登録し、`runtime_validation: failed_governance_fixture`と`formal_build_ready: false`を維持した。

v10更新後、属性解決器と道路種別の対応表の対象テストは`47 passed`、固定`analysis`コンテナ内の検証 検証一式は`175 passed`であった。これは設定と既存実装の静的整合性を検査した結果であり、実PBFからの正式ネットワーク生成や交通較正を検証した結果ではない。

<a id="20-permissions生成順信号構造現行仕様の責務を修正した"></a>

### 20. 通行許可生成順、信号構造、現行仕様の責務を修正した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v11, until: v11}
superseded_by: [section-21, section-22, section-23]
```

2026年7月19日、v10の「生成後に根拠付き通行許可へ完全一致させる」方針を再検討した。生成済み`net.xml`の車線 通行許可を拡張しても、その分類に必要な接続が生成済みである保証がないため、正式生成前の停止事項と判断した。また、信号交差点の採否と接続から信号制御 リンクへの対応は時間制御ではなくネットワーク構造であり、正式基準ネットワークより前に確定すべきと整理した。

設定をv10からv11へ更新し、次を決定した。

- 期待通行許可を最終`netconvert`前の明示入力へ具体化し、最終変換で車線と接続を再構築する。
- 生成`net.xml`は編集せず、車線・接続の完全一致監査だけを行う。不一致時は入力を修正して最終変換から再実行する。
- 信号交差点と信号制御 リンク構造を正式ネットワークの一部とし、サイクル、現示、スプリット、オフセットを需要投入後の較正対象とする。
- 構造ゲートをvClass別・有向で評価し、デポから顧客・充電施設への到達と帰着可能性を分離する。保持率は道路地物数と道路長の両方で報告する。
- 道路機能と舗装状態を分離する。`highway=track`は土地アクセス機能を理由に除外し、未舗装性は`surface`を中心に`smoothness`、`tracktype`を補助として判定する。
- 共通環境乱数の種と解法固有乱数の種を分離し、同じ整数を異種アルゴリズムへ渡しても同等乱数とは解釈しない。
- 小型配送車を`delivery`、重量貨物車を`truck`へ固定し、同一問題内で都合よくvClassを切り替えない。
- 大容量の正規化オープンストリートマップと`net.xml`はGit外に置けるが、`.netccfg`、成果物一覧、構築 まとめ、注意事項分類、検査値一覧はGitまたは改変不能な成果物 storageで版管理する。
- スーモ 1.24.0 検証用データ、`v1_24_0`ソース・XSD、取得日とSHA-256を固定した公式文書、最新版文書の順に証拠を優先する。
- pytest件数だけでなく、変更記録、コンテナー ハッシュ値、完全コマンド、collection ハッシュ値、終了コード、記録 ハッシュ値、開始・終了時刻を試験証拠として保存する。
- 本ファイルを変更履歴とし、現行仕様、道路網 構築、交通較正、最適化比較を別文書へ分離する。

要件状態を`policy_fixed`、実装、単体検証、実行時間検証、実データ検証、正式適格性へ分解した。通行許可 具体化処理、信号構造レビュー、成果物 publicationは方針固定のみで未実装である。固定スーモ 実行時間 検証用データは不合格、実PBF検証は未実施であり、`formal_build_ready: false`を維持する。

v11更新後、属性解決器と道路種別の対応表の対象テストは`54 passed`、固定`analysis`コンテナ内の検証 検証一式は`182 passed`であった。道路種別の対応表のXSD検証成功は実行時間検証とは分類せず、通行許可 importer 検証用データの不合格を解消したとは扱わない。

<a id="21-materializer契約とformal停止条件をv12で固定した"></a>

### 21. 具体化処理契約と正式停止条件をv12で固定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v12, until: v12}
superseded_by: [section-22, section-23]
```

2026年7月19日、実装検証 Stateを実装・実行済みの範囲と照合した。従来表では道路種別の対応表のXSD検証を実行時間非該当と記載していた一方、既に実行して不合格だったスーモ importer governance 検証用データが同じ行に反映されていなかった。また、属性解決器、通行許可期待値、具体化処理、変換後監査をまとめて記述しており、実装済み範囲を判別しにくかった。このため、設定をv11からv12へ更新し、方針、実装、unit/static、XSD、実行時間、real-data、正式 eligibilityを要件ごとに分離した。

スーモ 1.24.0の固定コンテナで`edges_file.xsd`と`connections_file.xsd`を確認し、`--plain-output-prefix`、`--plain-output.lanes true`、`--output.original-names true`を使用した暫定 plain 出力を正常系属性解決器 検証用データに対して実行した。`.edg.xml`の車線へ`param key="origId"`が出力されることと、plain edge/connection 拡張マークアップ形式が再入力interfaceとして利用できることを確認した。ただし、この実行では既知の`bus` compound 注意事項と不正なimporter 通行許可が残り、接続を持たない検証用データであったため、具体化処理、車線順、接続規則の正しさを検証した証拠ではない。

検証用データ実装前の契約として次を固定した。

- 属性解決器の期待値ジェイソン形式を不変成果物として保存した後、消費済み接続タグを除いた接続構造用オープンストリートマップ コピーから暫定 plain 拡張マークアップ形式を生成する。
- 具体化処理は暫定 ファイルを上書きせず、`governed_permissions.edg.xml`と`governed_permissions.con.xml`を生成する。最終`net.xml`は監査対象であり編集しない。
- 車線は`origId`でオープンストリートマップ 道路地物へ追跡し、道路区間方向は正規化オープンストリートマップ ノード順との比較で決める。道路区間 識別子の符号は方向根拠に使わない。
- 属性解決器 車線位置は進行方向から見たオープンストリートマップの左から右、スーモ 車線 索引は右から左とし、`n` 車線の位置`p`を`n - 1 - p`へ写像する。この規則は`--lefthand true`の固定検証用データで確認し、不一致なら実データへ進まず契約版を更新する。
- 車線期待集合は属性解決器期待値、道路種別の対応表基本集合、管理vClass集合の積集合とする。空集合は`allow=""`、非空集合は辞書順の空白区切りで書き、`disallow`を併記しない。
- 接続は暫定に存在する候補だけを扱い、from-車線、to-車線、暫定 接続制限の積集合を期待値とする。空集合の接続は削除して理由を記録し、存在しない右左折を新規生成しない。
- materialized edge/connection 拡張マークアップ形式のXSD適合、最終`netconvert`成功、スーモ読込、車線・接続完全一致、未追跡要素ゼロ、未分類注意事項ゼロを検証用データ合格条件とする。

実装検証 Stateには通行許可以外も含め、入力ハッシュ値再検証、正式属性根拠、`oneway=-1`、交差点 join、信号junction/TLS-link、車両入力検証器、prepare/validate 処理工程、実行環境成果物一覧、warning/exclusion監査、構造品質閾値、候補部分グラフ確認、小型再現性成果物、最終スーモ 負荷を正式停止条件として列挙した。これらの方針assertionは実行時間または実データ検証の代替ではない。v12時点で具体化処理と正式 道路網は未実装・未生成であり、`formal_build_ready: false`を維持する。

<a id="22-readiness-gatetls-handoff型付き状態をv13で修正した"></a>

### 22. 準備状況 判定基準、信号制御 引継ぎ、型付き状態をv13で修正した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v13, until: v13}
superseded_by: [section-23]
```

2026年7月20日、v12の全要件を一つの正式 構築開始条件として評価すると、生成後にしか完了できない正式 道路網、注意事項監査、成果物公開まで生成前に要求する循環が生じるとのレビューを受けた。また、`formal_eligibility`に真偽値と文字列が混在し、単純なtruth-値評価で未完了状態を合格と扱い得ることを確認した。

設定をv12から`ota_ward_sumo_network_v13`へ更新し、次を変更した。

- `formal_build_input_ready`、`formal_network_acceptance`、`downstream_experiment_ready`を依存順に分離し、要件 行列を重複なく三つへ割り当てた。正式 道路網生成物や候補部分グラフ確認を構築開始条件に含めない。
- 各要件の状態を`eligible: boolean`、列挙型`state`、必須`reason`へ統一した。設定をデータ構造 版 2とし、Git管理のジェイソン形式 データ構造と、重複ヤムル形式 キー、型、ゲート分割、版番号、主要なcross-項目 invariantを検査する専用検証器を追加した。
- 仕様状態を`current_governed_draft`へ変更し、固定済み方針と明示的阻害要因だけが承認範囲で、正式実行は未承認とした。
- 接続 通行許可 仮置きを禁止し、構造上の 監査へ未解決状態を記録できることとは別の設定にした。
- 通行許可 具体化後に暫定 信号制御 割当を全て除去し、最終接続集合の確定後に`governed_reviewed.con.xml`と`governed_reviewed.tll.xml`を作る順序へ変更した。暫定 `.tll.xml`は確認 入力に限定し、最終変換では使用しない。
- 空車線 通行許可は`allow=""`ではなく、固定検証用データで受理を確認することを条件に`disallow="all"`で非走行車線として表現する。空接続は削除して理由を記録する。
- 管理対象の 出典・来歴の単純性を維持するため`geometry.remove=false`をcommon/formal双方で固定した。将来道路区間結合を採用する場合は、複数オープンストリートマップ 道路地物、premerge 道路区間、removed ノードを表現する新しい来歴データ構造と設定版を必要とする。
- 属性解決器の全値の状態を最終出典・来歴集合へ反映し、未追跡lane/connection、予期しない・欠落接続、信号制御 link/phase長不一致、未分類注意事項、未照合道路区間削除を正式なpost-conversionゼロ件条件へ追加した。
- 道路交通センサスの確認済み用途を車線、道路幅、交通量、旅行速度へ限定し、指定最高速度と一方通行は具体的な項目定義確認待ちへ移した。日本道路交通情報センター規制には規制種別、有効期間、反復、車種範囲、法的・行政的出典、保存時点の記録日を必須とした。

v13は循環しない合否判定と通行許可から信号制御への引継ぎを定義したが、具体化処理、確認 画面、post-auditorおよび実行時間 検証用データの実装完了を意味しない。三つの準備状況状態は全て偽である。

### 23. 実装前の完全仕様パッケージをv14で固定した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v14, until: v14}
superseded_by: [section-24, section-25, section-27, section-30]
```

2026年7月22日、検証用データと通行許可の具体化処理を実装する前に、研究利用条件から構築後監査までの責任境界、全入出力形式、不具合 コード、検証用データ catalogue、要件・試験対応を一つの仕様体系として固定する必要があると判断した。設定を`ota_ward_sumo_network_v13`から`ota_ward_sumo_network_v14`へ更新した。

`05_src/traffic_simulation/specifications/`へ、研究要件、道路網 構築 architecture、属性解決器、通行許可の具体化処理、信号制御の確認、最終構築、構築後監査、検証用データ、不具合 taxonomy、追跡可能性の10文書を追加した。設定値と状態は`sumo_network.yml`、コンポーネントの規範動作はこれらの仕様書、成果物形式はジェイソン形式 データ構造を正本とし、同じ判断を複数文書が独立に決定しない構成とした。

具体化処理の正式 道路区間方向判定では座標近傍照合を禁止し、暫定構築が生成する`edge_provenance.json`のオープンストリートマップ ノード lineage 索引を使用する。出典 start 索引が終了 索引より小さい場合を順方向、大きい場合を逆方向とし、同値、欠落または曖昧な場合は停止する。オープンストリートマップの車線 listはforward/backwardとも各進行方向から見た左から右であり、属性解決器内で逆方向 listを反転しない。スーモ 車線 索引は右端を0とするため、両方向に`n - 1 - p`を適用する。

通行許可 tokenについて、省略、`all`、明示allow、明示disallowの集合演算を固定し、空token、未知・管理外分類、allow/disallow併記を停止対象とした。一部車線だけ空の場合は`disallow="all"`、directed 道路区間の全車線が空の場合は道路区間とincident 接続を削除する。接続は`from,to,fromLane,toLane`を一意キーとする明示車線-to-車線要素だけを対象とし、右左折を新規推測しない。

固定スーモ 1.24.0の`connections_file.xsd`と`tllogic_file.xsd`を再確認し、`tl`、`linkIndex`、`linkIndex2`を持つ信号制御 接続 記録は`.tll.xml`側に存在し、通行許可 `.con.xml`の接続 種類には存在しないことを記録した。このため具体化処理は暫定 信号制御 割当を接続から削除するのではなく、暫定 `.tll.xml`を最終 入力へコピーしない。最終接続集合の確定後、信号制御の確認がreviewed `.tll.xml`とハッシュ値-境界 成果物一覧を生成する。

`reproducibility/config/traffic_simulation/schemas/`へ共通成果物、通行許可 expectations、道路区間 出典・来歴、具体化 audit/summary、不具合 報告、信号制御 確認 成果物一覧、構築 manifest/summary、post-構築 監査、要件 追跡可能性のデータ構造を追加した。70件の規範要件を個別試験 識別子、検証用データ 分類、実装状態へ対応付けたmachine-readable 登録簿も追加した。

v14は仕様の解釈を固定する版であり、v14形式の属性解決器 成果物、道路区間 出典・来歴、具体化処理、信号制御の確認、最終構築、構築後監査および対応検証用データの実装完了を意味しない。現行属性解決器が出力するv13形式の通行許可 ジェイソン形式はv14 具体化処理の適格入力ではなく、データ構造 migrationを次工程の阻害要因として登録した。

外部仕様根拠：

- <https://wiki.openstreetmap.org/wiki/Lanes>
- <https://wiki.openstreetmap.org/wiki/Forward_and_backward>
- <https://sumo.dlr.de/docs/Networks/PlainXML.html>
- pinned SUMO 1.24.0 XSD: `edges_file.xsd`, `connections_file.xsd`, `tllogic_file.xsd`

## v14仕様作成時点で固定した内容

```yaml
decision_status: partially_superseded
effective_configuration: {from: v14, until: v14}
superseded_by: [section-24, section-25, section-27, section-28, section-30]
```

この一覧はv14仕様作成時点の履歴であり、現在有効な仕様一覧ではない。後続節および
現行仕様書と異なる場合は、後続節と現行仕様書を優先する。

- 採用方式：自動車系道路種類の明示的ホワイトリスト
- 車種：`passenger,taxi,bus,coach,delivery,truck,motorcycle,moped`の範囲内
- 専用バスリンク：保持するが配送車の通行は許可しない
- 属性既定値：`speed`、`numLanes`、`oneway`を道路種別の対応表で補完しない。ただし、省略自体は欠損検出に使わない
- `oneway`：双方向の導出値も`oneway=no`として変換前に明示し、欠損を`osmDefaults`監査へ委ねない
- `oneway=-1`：左右・方向依存タグの安全な変換実装が完成するまで原データを変更せず停止する
- `oneway`暗黙規則：環状交差点とmotorwayは`yes`、motorway_link欠損は`unresolved`とし、統計的仮置きを使わない
- 構造用補完：`lanes`と`maxspeed`だけを対象に、一意な最頻値、標本数30以上、最頻値比率50%以上を要求する
- 構造用補完の入力：真の欠損だけを対象とし、未対応明示値、矛盾、条件付き値、方向非対称値を上書きしない
- 正式用補完：独立した検証記録を持つ`derived_validated_model`だけを許容し、未検証仮置きを禁止する
- 通行側：`lefthand=true`を設定と実行で必須とし、一方通行方向自体は反転しない
- 優先順位：スーモ 1.24.0標準値を継承する
- 対象外種類：`discard="true"`で明示する
- 未知種類：採用せず、後続パイプラインでは検出時に停止して構築 まとめへ記録する
- スーモ入力vClass：管理対象8クラスだけを許可し、`ignoring`、`custom1`、`custom2`、`evehicle`を禁止する
- 電気自動車配送表現：`vClass="delivery"`とスーモ 電池 deviceを組み合わせ、`evehicle`を禁止する
- 接続処理：`osm.lane-access=true`を固定し、検証用データと生成通行許可監査で動作を確認する
- 通行許可処理：期待値を最終変換前の明示入力へ具体化し、生成`net.xml`は編集せず車線・接続を完全一致監査する
- 属性解決器監査：期待通行許可と補完完全分布を専用ジェイソン形式へ保存し、接続タグは変換後照合が完成するまで保持する
- 用途別vClass：配送経路用と背景交通用を分け、ネットワークの管理集合8クラスと混同しない
- 工程順序：仮置きを除去した正式基準ネットワークを需要投入・較正より前に完成させる
- 実行環境：スーモ、PROJ、依存環境を含むコンテナハッシュ値と全入力・設定・コマンドのfingerprintを保存する
- 信号：交差点と信号制御 リンク構造は正式前、時間制御は需要投入後に固定・較正する
- 道路表面：道路機能と舗装状態を分離し、`surface`を主要判定タグとする

## v14仕様作成時点の残作業と変更管理

```yaml
decision_status: partially_superseded
effective_configuration: {from: v14, until: v14}
superseded_by: [section-24, section-25, section-27, section-29, section-30]
```

以下はv14時点の残作業記録である。現在の残作業は
`05_src/traffic_simulation/current_issues_and_blockers.md`を参照する。

固定環境で次を確認する。

```bash
docker compose build analysis
docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q
```

その後、属性ガバナンス処理、保持道路地物の属性・来歴検証器、スーモ車両入力検証器、変換ログ・生成ネットワーク監査、道路網生成パイプラインを実装する。実オープンストリートマップ 拡張マークアップ形式からの変換、生成`net.xml`の読込、未知種類、compound 種類、条件付き接続、通行許可、既定値由来値を検証する必要がある。

優先順位階層は東京の実道路優先関係を検証した結果ではない。また、スーモの`motorcycle`は日本の排気量区分別規制を完全には表現しない。採用種類、車種、優先順位を変更する場合は、道路種別の対応表方針識別子と`sumo_network.yml`の設定版を上げ、変更理由と再検証結果を本ファイルへ時系列で追記する。

Git管理対象には、カスタム道路種別の対応表、`sumo_network.yml`、テスト、現行仕様、手順、変更履歴を含める。大容量の生成オープンストリートマップ 拡張マークアップ形式と`net.xml`はGit管理外にできるが、`.netccfg`、成果物一覧、構築 まとめ、注意事項分類、検査値一覧はGitまたは改変不能なcontent-addressed 成果物 storageで版管理し、外部保存時はGit管理の索引から参照できるようにする。

<a id="24-resolverのpermission成果物をv14形式へ移行した"></a>

### 24. 属性解決器の通行許可成果物をv14形式へ移行した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v14, until: v15}
superseded_by: [section-27, section-29, section-30]
```

2026年7月22日、`ota_ward_sumo_network_v14`の実装として、属性解決器が出力する旧マップ形式の通行許可 ジェイソン形式を、`permission_expectations.schema.json` 版 2に適合する成果物へ置換した。成果物にはartifact/config 同一性、設定プロファイル、入力オープンストリートマップ、成功時の正規化オープンストリートマップ、道路種別の対応表の保存先・SHA-256・方針 識別子、管理対象vClass、オープンストリートマップ 道路地物、スーモ 種類、方向、車線位置、期待vClass集合、適用規則 識別子を記録する。失敗時は文字列だけでなく、stable RS コード、component、位置、値の状態および出典 値を持つ型付き阻害要因を記録し、正規化オープンストリートマップは公開しない。

正式運用コードからgoldenを生成しない方針に従い、正常検証用データ、欠損属性検証用データおよびforward/backward各2車線の双方向検証用データに対する独立正解判定器を追加した。両方向ともオープンストリートマップの各進行方向から見た左から右の順を保持し、属性解決器内で逆方向配列を反転しない。ジェイソン形式 データ構造検証、旧v13 マップ-only形状の拒否、入力・出力ハッシュ値および規則 出典・来歴をテスト対象とした。

この変更は検証用データ上のv14成果物実装を示すが、登録済み大田区オープンストリートマップ extractに対する実行証拠ではない。`permission_expectation_artifact`の状態は`pending`とし、正式 構築 入力 準備状況は偽のまま維持する。次の停止条件は登録済みextractでの属性解決器実行ではなく、まず厳密 `edge_provenance.json`を生成する暫定構築の実装とする。

<a id="25-resolver-v14のformal安全性と監査粒度を修正した"></a>

### 25. 属性解決器 v14の正式安全性と監査粒度を修正した

```yaml
decision_status: partially_superseded
effective_configuration: {from: v14, until: v15}
superseded_by: [section-29, section-30]
```

2026年7月22日、`ota_ward_sumo_network_v14` 属性解決器の外部レビューで、正式処理設定でも双方向偶数車線を等分できること、停止道路地物が構造用補完属性提供元へ混入し得ること、通行許可 出典・来歴が道路地物上の全接続 属性タグを全車線へ付与すること、および`--overwrite`中の失敗で異なる実行の成果物が混在し得ることが指摘された。これらは正式利用を妨げる実装上の問題として修正した。

正式では`lanes:forward`と`lanes:backward`の明示を必須とし、等分仮定は構造上のの偶数総車線だけへ限定した。補完属性提供元は、解決可能な一方通行、整合する明示車線と正本 maxspeed、条件付き不在、通行許可解決成功を全て満たす道路地物だけとした。`oneway=-1`や方向別速度矛盾を持つ道路地物は属性提供元から除外する。`service|bus`と`service|psv`を含む保持判定は厳密 スーモ 種類 識別子へ統一した。

通行許可 成果物には、道路種別の対応表 基準、研究vClass積集合、実際に適用した一般・車種・方向・車線別オープンストリートマップ 属性タグについて、車線ごとの出典 値、車線 値、適用前後vClass集合を順序付き追跡として保存する。他方向・他車線だけに作用する属性タグは記録しない。全成果物はstagingで生成・検査後、backupとrollbackを伴って一括公開する。書込み例外時の`.part`も削除する。

さらに、malformed 属性タグ、node/Relation参照、重要度 出典と網羅率、道路種別の対応表 `disallow`禁止、補完閾値範囲、Decimal速度正規化を検証対象とした。属性解決器 コマンド操作は不具合 報告 保存先を必須入力とし、通常の阻害要因は固有RS コードを保持し、XML/input 同一性を`RS001`、config/typemap/criticalityを`RS004`、Schema/accountingを`RS011`、path/write/publicationを`RS012`へ分類する。検証用データ検証は実データ適格性の代替ではないため、全準備状況状態は偽のまま維持する。

### 26. 自動車系単一モードを全研究工程の範囲として明確化した

```yaml
decision_status: superseded
effective_configuration: {from: v14, until: v14}
superseded_by: [section-27]
```

2026年7月23日、`ota_ward_sumo_network_v14`について、「初期道路網は自動車系単一モード」とする記述が、後続段階で歩行者、自転車、鉄道または船舶を含むマルチモーダル道路網へ拡張する可能性を残していたため、研究範囲を明確化した。本研究は、道路網生成、交通シミュレーション、配送評価および手法比較の全工程を通じて、`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`、`moped`の統制済み8クラスだけを道路通行許可の管理集合とする。

歩行者、自転車、鉄道および船舶の専用リンクと需要は後続工程でも追加せず、マルチモーダル版は本研究の範囲外とした。自動車との共用道路は、歩行者または自転車も通行可能であることだけを理由には除外しない。緊急車両、行政車両など管理集合外の自動車系スーモ 分類も追加しない。

この変更は、保持種類、8クラスの集合、車線 通行許可または接続 通行許可の実効値を変更せず、研究期間に関する既存方針の曖昧さを除くものである。そのため設定 同一性はv14を維持した。一方、道路種別の対応表内コメントを統一したことでファイルSHA-256は`0e3a618cb47108a3b78af77ea8fa738c9ef25fb4864756a0bfa032ef3d457120`へ変わったため、`sumo_network.yml`と独立検証用データ 正解判定器の登録ハッシュ値を同時に更新した。旧ハッシュ値を参照する未承認の検証用データ成果物は新ハッシュ値で再検証し、異なる道路種別の対応表 ハッシュ値の成果物を混在させない。

### 27. mopedを除外し、専用バスと後続利用データの位置付けを固定した

```yaml
decision_status: active
effective_configuration: {from: v15, until: null}
superseded_by: []
```

2026年7月23日、配送研究との対応を再確認し、`moped`を道路通行許可の管理集合、スーモ車両入力、背景交通生成、到達可能性評価および属性解決器の車種別解決対象から除外した。通常道路とmotorwayを含む保持道路の最大管理集合は、`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`の7クラスとなる。これは実効通行許可集合を変更するため、設定を`ota_ward_sumo_network_v14`から`ota_ward_sumo_network_v15`へ更新した。

専用バス道路は配送車の経路候補ではないが、背景交通としてのバス運行と道路網上の交通条件を表すために保持する。`highway.busway`と`highway.bus_guideway`は引き続き`bus`だけを許可し、配送例外を暗黙に追加しない。車種集合の変更に伴い道路種別の対応表方針識別子を`tokyo_motorized_v2`へ上げた。道路種別の対応表のSHA-256は`81c7ed6c5f40ce0e06071bbba0ecc52b5abc2b2d8b8da64dc9cb2b3296c253be`へ更新し、独立正解判定器も`permission_expectations_v15.oracle.json`として更新した。

海外の運転行動データ、天候、事故、および運転行動データに含まれる歩行者関連項目は削除しない。ただし、これらはコア比較の入力ではなく、別に統制する後続段階の文脈分析または感度分析に限って使用する。海外データの絶対値を東京へ直接移植せず、天候と事故は通常条件の基準モデルが較正・独立検証された後に導入する。歩行者関連項目は自動車運転者が直面した状況を表す共変量であり、歩行者agent、歩行者需要または歩行者ネットワークモードを導入するものではない。

<a id="28-onewayタグ欠損と方向未解決を区別した"></a>

### 28. 一方通行タグ欠損と方向未解決を区別した

```yaml
decision_status: active
effective_configuration: {from: v15, until: null}
superseded_by: []
```

2026年7月23日、`ota_ward_sumo_network_v15`の`oneway`基礎集計におけるタグ欠損を、そのまま通行方向の未解決件数として読める表現が残っていたため修正した。一般道路で`oneway`タグが明示されていない場合は、元タグの不在を保持したまま、オープンストリートマップの通常解釈と固定属性解決器規則により実効値`no`を導出する。これは最頻値による欠損補完ではなく、監査上は`source_value=""`、`adopted_value="no"`、`value_state="derived_osm_rule"`および適用規則として分離する。

対象26,201 道路地物のうち、明示的な`oneway`タグがない道路地物は19,753であるが、欠損集合に`motorway`、`motorway_link`または`junction=roundabout`はなく、基礎集計上、タグ欠損だけを理由に意味を導出できない道路地物は0である。一方、保持候補にある`oneway=-1`の1 道路地物は意味と入力値が妥当であり、`invalid`または`unknown`ではなく`valid_but_unsupported`、不具合 コード `RS007`として扱う。正式な実データ属性解決器実行と構築後監査は未完了であるため、安全に変換可能な全件数と生成後の方向道路区間不一致件数は未確定のままとする。

この変更は属性解決器の実効動作を変更せず、既存の監査状態、機械可読設定およびテストを明示化するものである。`oneway`タグ欠損には同種道路や周辺道路の最頻値を使用しないという方針も、より具体的な表現へ統一した。

同時に、26,201 道路地物を一件ずつ目視確認するのではなく、明示値と固定規則で通常ケースを全件処理し、`unresolved`、`conflict`、`valid_but_unsupported`、`invalid`および未登録の`unexpected`だけを人のレビュー対象とする運用を固定した。新規例外は個別データを直接修正せず、決定表、検証用データ、属性解決器、登録済み入力の全件試行実行の順に反映する。進捗正本もv15 属性解決器の試行実行と例外キュー生成を次作業として更新した。

<a id="29-登録済み入力でv15-resolverの全件dry-runを実行した"></a>

### 29. 登録済み入力でv15 属性解決器の全件試行実行を実行した

```yaml
decision_status: validation_record
effective_configuration: {from: v15, until: v15}
superseded_by: [section-30]
```

2026年7月23日、`ota_ward_sumo_network_v15`を用いて登録済み大田区入力の`structural` 試行実行を実行した。境界矩形抽出PBFのSHA-256は取得記録と一致した。`complete_ways`抽出には部分関係が含まれるため、道路接続に不要な関係を参照検証前に除外し、抽出内581件の右左折制限 関係については、登録済み関東PBFから参照ノード・道路地物を再帰的に補足した属性解決器専用入力を作成した。非道路関係は削除するが、不完全な右左折制限 関係は停止する規則を固定した。

最終入力では26,220 道路地物を処理し、83,884 監査行を生成した。24,346 道路地物に46,056 阻害要因が残り、正規化オープンストリートマップは公開されなかった。内訳は、bulk欠損45,749行、通行許可未解決264行、車線表現未対応19行、速度表現未対応22行、`oneway=-1` 1行、車線矛盾1行である。通行許可期待値が完全な道路地物は1,874であった。`oneway`は、一般道路の双方向導出19,764、明示値6,455、妥当だが実装未対応の逆向き一方通行1であった。

全件実行により、除外道路地物を約170万ノードを持つ拡張マークアップ形式 最上位から一件ずつ削除する二次的処理も発見した。除外対象を収集して最上位を一度だけ絞り込みする線形処理へ変更し、検証用データで同じ除外結果を確認した。実行コマンド、関係要素の参照先の補完、入力・成果物ハッシュ値、不具合コード分布および次作業は`03_data/metadata/acquisition/20260723_ota_ward_v15_resolver_dry_run.md`へ固定した。正式ネットワーク適格性は偽のままである。

### 30. 版16母集団へ属性重要度分類と属性値解決を接続した

```yaml
decision_status: validation_record
effective_configuration: {from: v16, until: null}
superseded_by: []
```

2026年7月30日、受理済み関係要素の参照先の補完版16を属性重要度分類と属性値解決の入力にするため、設定を`ota_ward_sumo_network_v16`へ更新した。版16の受理成果物一覧、関係-closed オープンストリートマップ 拡張マークアップ形式および道路役割成果物のSHA-256を出典台帳へ直接登録し、版15の分類・解決記録を前版として参照しない初回生成とする。

属性値解決処理は分類専用成果物を読み取り専用として扱い、採用値、証拠候補と選択結果、競合解決規則、確認状態および停止コードだけを追加する。統合後はレコード全体の自己ハッシュを再計算するが、重要度、選択規則および一致規則は変更しない。未解決組は削除せず停止記録として保持し、一件でも残る場合は`complete=false`とする。

外部管理の判定事実について、較正区間、独立検証区間、主要交差点進入部、受理済み配送経路および感度分析対象は、この時点で受理済みの正例割当がないことを明示する。空集合は値の欠損や暗黙の偽値ではなく、版16全道路を負の適用範囲とする独立成果物として固定する。後に正例を受理する場合は、その出典成果物と規則版を更新して分類レコードを新規改訂する。

### 31. 版17道路属性解決の中核方針を固定した

```yaml
decision_status: active
effective_configuration: {from: v17, until: null}
superseded_by: []
```

2026年7月30日、通行許可 正本、接続の4軸specificity、方向付き区間、
管理配送車両、方向別車線の正式除外および二軸値状態を
`ota_ward_attribute_resolution_policy_v17`として固定した。機械可読正本は
`reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml`、
規範説明は
`05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy.md`
とする。

版16実行記録は変更せず、版17成果物として再表示しない。版17では道路種別の対応表 通行許可を
仮候補、属性解決器 expected 通行許可を正式 正本とする。接続は空間、車種、
時間および目的の4軸でPareto比較し、異なる結果を持つ複数極大規則は
`ACCESS_SPECIFICITY_CONFLICT`で停止する。

元道路地物は不変に保ち、`oneway=-1`はB方向の方向付き区間だけを生成する。基準車両は
`managed_urban_ev_delivery_v1`とし、新規属性成果物は`resolution_status`と
`value_origin`を正本とする。方針、データ構造、車両プロファイル、接続比較の純粋関数および
方向付き区間の純粋関数は追加したが、正式運用 属性解決器、関係写像、通行許可
具体化処理および版17全件実行への統合は未完了である。したがって、
`formal_build_ready=false`を維持する。

<a id="現在のverification-state"></a>

## 現在の実装検証状態

この表は2026年7月30日時点の記録である。`pytest`合格、XSD適合、固定スーモ
実行時間 検証用データ、実データ全件実行および正式適格性は、相互に代替できない独立状態
として記録する。

| 対象 | Policy | 実装 | Unit/static | XSD | Runtime fixture | Real data | Formal eligible |
|---|---|---|---|---|---|---|---|
| typemap XML | fixed for v16 | 実装済み | 合格 | 合格 | failed importer governance fixture | not run with formal pipeline | いいえ |
| attribute resolver | v17 core policy fixed | 部分的 | 合格 | v17 resolution Schema added | resolver fixtures passed | v16全件実行済み、停止組あり | いいえ |
| permissions resolver | v17 authority and access policy fixed | partial utility only | v17 policy utility passed | JSON Schema passed | importer fixture failed | v16不完全成果物を生成済み | いいえ |
| permissions materializer | policy draft exists | not implemented | not completed | output XSD not exercised | not run | not run | いいえ |
| `oneway=-1` | Directed Segment policy fixed | pure generator and fail-closed detection | unit fixture passed | Directed Segment Schema passed | integrated fixture not run | 1件を停止として確認 | いいえ |
| lane mapping | formal policy fixed | partial resolver support | passed for resolver fixtures | v17 state Schema passed | materializer fixture not run | 正式全件解決未完了 | いいえ |
| final `net.xml` | partially fixed | not implemented | not completed | not completed | not run | not generated | いいえ |

集約状態は、版17中核方針が`fixed`、道路網全体の方針が`partially_fixed`、実装が
`partial`である。単体・静的検査と既存XSD検査は合格、スーモ importer governance
検証用データは不合格、実データ検証は一部完了、`formal_build_ready=false`である。

## 現在も保持する既知の実行時失敗

固定スーモ 1.24.0のgovernance 検証用データでは、次の失敗を確認している。これらは道路種別の対応表
またはスーモ importerを正式な通行許可 属性解決器として信頼しない根拠である。

- `access=no`と車種別例外が期待どおり変換されなかった。
- `motor_vehicle=no`と`delivery=yes`が期待どおり変換されなかった。
- `access:lanes`が期待どおり反映されなかった。
- `vehicle:lanes`により管理外分類が追加された。
- 欠損道路地物が1 車線、13.89 m/sで生成された。
- `oneway`欠損が変換後の既定値 annotationだけでは検出できなかった。

後続の静的試験、ジェイソン形式 データ構造検査または版16属性解決の全件実行は、この実行時間
検証用データ不合格を解消した証拠ではない。

## 現在の未完了事項

- 版16formal属性解決には24,741停止組が残り、`complete=false`である。
- 管理配送車両の方針とデータ構造は固定済みだが、車両入力境界への統合が未完了である。
- 方向付き道路モデルの方針、データ構造および純粋生成関数は固定済みだが、方向依存タグ、
  関係、車線順および正式運用 処理工程の一体検証用データが未完成である。
- 条件付き規制の正式文法、目的別接続、許可台帳および日本速度規則の適用条件が
  未確定である。
- 通行許可 具体化処理、接続再生成、変換後完全一致監査が未実装である。
- 暫定 構築、信号制御 確認、最終 構築、post-構築 監査および最終スーモ読込が
  未実施である。
- 構造上の 仮置きの母集団、重み、範囲および閾値感度分析が未完了である。
- 正式道路網を用いた較正と独立検証は未実施である。

## 現行仕様へ移した内容と残件

次の内容は版17規範仕様と機械可読方針へ移した。本文書の要約だけでは実装根拠に
ならない。

- 接続の空間、車種、時間、目的の各具体性軸と軸間競合の停止規則
- `resolution_status`と`value_origin`の二軸状態、および旧`value_state`からの移行規則
- 方向付き道路モデルと`oneway=-1`の正式表現
- 方向別車線、`lanes:both_ways`、可逆車線および時間帯別車線の正式規則
- 車両プロファイルとオープンストリートマップ車種キーの対応
- 属性解決器 expected 通行許可を正式 正本とする入出力契約
- 条件付き規制文法、許可台帳および速度証拠の決定表は未決定のままである。

正本は`10_approved_attribute_resolution_policy.md`と
`approved_attribute_resolution_policy_v17.yml`である。初期正式仕様案は履歴であり、
新規実装の根拠として使用しない。

## 文書と実装・設定の不一致

2026年7月30日時点で、次の不一致を確認した。本文書の修正だけでは解消しないため、
後続の仕様・設定・実装変更まで正式 構築を停止する。

1. 現行方針では属性解決器 expected 通行許可を正式 正本とする一方、
   `sumo_network.yml`と`resolve_osm_attributes.py`には道路種別の対応表 基準との積集合を
   expected 通行許可とするv14以前の契約が残る。
2. 現行方針では接続具体性を複数軸で評価し、軸間競合を停止するが、現行属性解決器は
   v16設定の一次元的な適用順と道路種別の対応表 基準を前提とする。完全な多軸競合判定は
   未実装である。
3. 現行方針では`resolution_status`と`value_origin`を分離するが、版16成果物とデータ構造
   は旧`value_state`を使用する。移行規則は未決定である。
4. 現行方針では元道路地物と別の方向付き区間を要求するが、方向付き道路生成器は未実装で
   あり、現行コードは`oneway=-1`を不確実な場合は拒否で停止する段階にある。
5. 道路種別の対応表と設定には過去の通行許可候補が残るが、固定スーモ importer 検証用データは
   その解釈に不合格である。具体化処理と変換後監査が未実装であるため、最終
   通行許可の実行証拠はない。
