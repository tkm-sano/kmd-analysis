# 東京自動車系SUMO typemap：変更履歴

## 記録情報

- 記録日：2026-07-18
- 実施者：研究環境管理者（Codex支援）
- 状態：`implemented_runtime_validation_failed`
- 設定ID：`ota_ward_sumo_network_v11`
- typemap方針ID：`tokyo_motorized_v2`
- 対象ファイル：`reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml`
- 関連設定：`reproducibility/config/traffic_simulation/sumo_network.yml`
- 関連方針：`05_src/traffic_simulation/network_attribute_governance.md`
- 関連実装計画：`05_src/traffic_simulation/implementation_plan.md`

本ファイルはtypemapと関連する道路網ガバナンスの時系列変更履歴である。現在有効な仕様は`05_src/traffic_simulation/network_current_specification.md`を参照し、過去節を現行仕様として部分引用しない。構築、較正、最適化の手順は各protocol文書へ分離する。

## 時系列作業ログ

### 1. 作業目的を確定した

初期SUMO道路網へ採用するOSM道路種別とSUMO vehicle classを明示的なホワイトリストとして固定し、歩行者、自転車、鉄道、船舶等の対象外リンクが標準typemapの暗黙動作によって混入しない構成を目標とした。

また、`lanes`、`maxspeed`、`oneway`の欠損をtypemap既定値で黙って補完しないことを前提とした。これらの属性は、後続の属性ガバナンス処理で値状態と根拠を記録したうえで、変換用OSM XMLへ明示する。

### 2. 固定Docker環境の利用可否を確認した

研究環境で固定しているSUMOコンテナを使って`netconvert`の版を確認しようとしたが、Docker daemonが停止していたため実行できなかった。この時点ではホストへ別の`netconvert`を導入せず、研究設定と同じSUMO 1.24.0の公式ソースを参照して設計を進めることにした。

未実施となった確認：

```bash
docker compose run --rm sumo netconvert --version
```

### 3. SUMO 1.24.0の上流資料を固定した

最新ブランチではなく、研究設定と一致するGit tag `v1_24_0`から次の資料を参照した。

- 標準typemap：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/typemap/osmNetconvert.typ.xml>
- types schema：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/types_file.xsd>
- base types schema：<https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/xsd/baseTypes.xsd>
- OSM import documentation：<https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html>

標準typemapを取得し、SHA-256を計算した。

```bash
curl -fsSL \
  https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/data/typemap/osmNetconvert.typ.xml \
  | shasum -a 256
```

結果：

```text
e3de4b6aadd2e6bf0d0f6186d84c621bbf807e65b81bba9aec8fe0d7b0d77786
```

### 4. リポジトリ内の対象範囲と上流typemapを照合した

標準typemapからOSM type IDとpriorityを抽出し、`sumo_network.yml`の`vehicle_scope.keep_vclasses`および実装計画の初期交通モードと照合した。その結果、共用自動車道路、SUMOのservice compound type、専用バスリンクを採用対象とした。

一方、歩行者、自転車、鉄道等の専用リンクと初期研究範囲外の道路種別は、暗黙に落とすのではなく`discard="true"`で明示的に除外する方針とした。typemapに存在しない未知typeは正式処理で採用せず、警告と除外件数をbuild summaryへ記録する方針とした。

### 5. typemapの採用規則を決定した

共用自動車道路として、次のOSM `highway`値を採用することにした。

```text
motorway, motorway_link,
trunk, trunk_link,
primary, primary_link,
secondary, secondary_link,
tertiary, tertiary_link,
unclassified, residential, living_street, service
```

基本の許可vehicle classを次に限定した。

```text
passenger,taxi,bus,coach,delivery,truck,motorcycle,moped
```

追加規則は次のとおりとした。

- `motorway`と`motorway_link`ではmopedを許可しない。
- `highway.service|psv`と`highway.service|bus`では`bus delivery`を許可する。
- `highway.bus_guideway`と`highway.busway`では`bus`だけを許可する。
- OSMの明示的な`access`、`vehicle`、`motor_vehicle`等は、typemapの基本権限をさらに制限できるものとする。
- `speed`、`numLanes`、`oneway`はtypemapに記述しない。
- priorityはSUMO 1.24.0標準typemapの道路階層を維持するが、速度、車線数、一方通行の代用にはしない。

明示的な除外対象は次のとおりとした。

- 未舗装・作業道等：`highway.unsurfaced`、`highway.track`
- 歩行者系：`highway.footway`、`highway.pedestrian`、`highway.path`、`highway.bridleway`、`highway.step`、`highway.steps`、`highway.stairs`
- 自転車専用：`highway.cycleway`
- 初期範囲外：`highway.raceway`、`highway.ford`、`highway.construction`
- 鉄道系：`railway.preserved`、`railway.tram`、`railway.subway`、`railway.light_rail`、`railway.rail`、`railway.highspeed`、`railway.construction`

### 6. カスタムtypemapを作成した

決定したホワイトリスト、許可vehicle class、除外type、標準priorityを反映して、次のファイルを作成した。

```text
reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml
```

上流標準typemapとの主な差は、多交通モードを含む汎用定義から東京の初期自動車系道路網に限定したこと、対象外typeを明示的にdiscardしたこと、`speed`、`numLanes`、`oneway`の既定値を削除したことである。

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

`sumo_network.yml`を設定版v4、設定ID `ota_ward_sumo_network_20260716_v4`へ更新した。`typemap_policy`へカスタムtypemapのパスとハッシュ、上流資料のURLとハッシュ、採用type、許可vehicle class、属性既定値を持たせない方針を記録した。

また、カスタムtypemapを未実装要件から外し、残る属性ガバナンス処理、補助表、道路網生成パイプラインを`implementation_plan.md`の未実装作業として整理した。取得記録READMEから本ファイルを参照できるようにした。

### 8. 設定とXMLの不整合を検出するテストを追加した

`05_src/traffic_simulation/validation/test_sumo_typemap.py`を追加し、次を検査するようにした。

- YAMLが参照するtypemapパスとSHA-256が実ファイルに一致する。
- XML内に重複type IDがない。
- 非discard typeがYAMLの明示的ホワイトリストと一致する。
- 許可vehicle classが研究対象classの部分集合である。
- `speed`、`numLanes`、`oneway`がtypemapに存在しない。
- 代表的な歩行者、自転車、鉄道、工事中typeが明示的にdiscardされる。

### 9. XSD検証と対象テストを実行した

SUMO 1.24.0のschemaを取得し、XMLを検証した。

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

ホスト環境でリポジトリ全体のpytestを実行したが、ホストPythonに`folium`がなく、`test_render_baseline_demand.py`のimport時に収集が停止した。`folium==0.20.0`は分析用Docker環境に固定されているため、ホストへ追加導入せず、Docker daemon復旧後に固定環境で再実行することにした。

Docker daemonが停止しているため、次の実行時検証は未実施である。

- Docker内の`netconvert --version`確認
- typemapを使った実OSM XMLの変換
- 生成した`net.xml`のSUMO CLI読込

実OSM XMLの変換は、`build_sumo_network.py`と属性ガバナンス処理も未実装であるため、現段階では実行できない。XSD適合と単体テスト成功だけでは`net.xml`生成成功を保証しない。

### 11. 現在の状態を確定した

typemap、設定、整合性テスト、本記録は作成済みである。一方、固定SUMO環境での実変換が完了していないため、状態を`implemented_not_runtime_validated`とし、`status.implementation: pending`および`formal_build_ready: false`を維持した。

### 12. 欠損検出とpermissions迂回に関するレビューを反映した

初版作成後、typemapから`speed`、`numLanes`、`oneway`を省略しても、`netconvert`のimporter-levelまたはglobal defaultを防げず、属性欠損時の停止を保証しないとのレビューを受けた。SUMO公式文書でも`default.lanenumber=1`、`default.speed=13.89 m/s`が定義され、type属性自体は任意であることを再確認した。また、`ignoring`はlane permissionsを無視でき、`osm.lane-access`は既定で無効であることを確認した。

参照した公式資料：

- <https://sumo.dlr.de/docs/netconvert.html>
- <https://sumo.dlr.de/docs/Simulation/VehiclePermissions.html>
- <https://sumo.dlr.de/docs/SUMO_edge_type_file.html>
- <https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html>

この確認を受け、設定をv4からv5へ更新し、次を決定した。

- 属性省略はvalidation mechanismではないとXMLコメントと設定に明記する。
- 保持対象wayは`netconvert`前に`lanes`、`maxspeed`、`oneway`の採用値と必須来歴をすべて持たせ、不足時に停止する。
- `structural_placeholder`は構造確認用に限るが、使用wayを分離して全件記録する。
- `ignoring`、`custom1`、`custom2`と管理対象外vClassを`vType`、`vehicle`、`flow`、`trip`入力で禁止する。
- `osm.lane-access=true`と`osm.annotate-defaults=true`を固定する。
- 未知type、未知compound type、edge追加失敗を停止対象とし、edge除外は明示的discardと照合できない場合に停止する。
- 変換後にpermissionsがtypemapの基本permissionsを超えていないことと、未承認default由来値がないことを監査する。
- way単位とlane単位のaccessタグを含むfixtureによるSUMO 1.24.0実変換試験を必須とする。

XMLのルール自体は変更せずコメントを訂正したため、ファイルの新しいSHA-256は次となった。旧ハッシュ`d86ab83e7b8afa94c4d13e0669a146cf18809e2e6af3ce8fee1e24a6a1fcd8c2`は初版の記録として残す。

```text
6c667e13f405b78b86b999abb141f13e99bc88c35187af8a007e2318cefb83cf
```

これらは現時点では設定とテストで固定した実装要件であり、前処理validator、車両入力validator、変換ログ・生成ネットワーク監査は未実装である。したがって、現ファイルだけで「欠損時に必ず停止する閉じたホワイトリストが完成した」とは扱わない。

修正後に同じXSD検証と関連テストを再実行し、XMLのXSD適合と`39 passed`を確認した。これは設定の静的整合性確認であり、未実装validatorや実際のaccess変換動作を検証した結果ではない。

### 13. 固定SUMO 1.24.0でgovernance fixtureを実変換した

Docker daemonが利用可能になったため、digest固定した`sumo`サービスで版を確認した。

```bash
docker compose run --rm sumo netconvert --version
```

結果は`Eclipse SUMO netconvert Version 1.24.0`であり、設定の期待版と一致した。

次に、`05_src/traffic_simulation/validation/fixtures/osm_typemap_governance.osm.xml`を作成した。このfixtureは、way単位の`access=no`と車種別例外、`motor_vehicle=no`、lane単位の`access:lanes`と`vehicle:lanes`、および`lanes`、`maxspeed`、`oneway`をすべて欠く負例を含む。カスタムtypemap、`osm.lane-access=true`、`osm.annotate-defaults=true`を指定して実変換した。

変換自体は終了コード0となったが、governance検証は次の理由で失敗と判定した。

- way 100の`access=no`、`bus=yes`から未知compound警告`Discarding unknown compound 'bus'`が発生し、生成laneに`bus bicycle`が許可された。`bicycle`はtypemapの基本permissionsを超える。
- way 200の`motor_vehicle=no`、`delivery=yes`は期待したdelivery限定にならず、typemapの基本8クラスがすべて残った。
- way 300の`access:lanes=no|yes`は、生成された2 laneのpermissionsを期待どおり制限しなかった。
- way 400の`vehicle:lanes=no|yes`では、生成laneの一つに`private`が追加され、typemapの基本permissionsを超えた。
- 属性欠損のway 600は停止せず、1 lane、13.89 m/sで生成され、`osmDefaults="numLanes speed"`が記録された。

この結果は、typemapの`allow`だけではOSM access変換後のpermissions上限を保証できず、属性省略だけでも欠損停止を保証できないことを実証した。設定へ実測した失敗状態と実際の警告文字列を記録し、`access_permission_mapping_resolution`を未完了要件へ追加した。前処理でaccessを正規化するか、対応compound typeを追加するかは、fixtureの全ケースを期待どおり変換できるまで確定しない。

記録と静的検査の更新後、関連ホストテストは`40 passed`、analysisコンテナ内のvalidation suiteは`135 passed`、SUMO 1.24.0 XSD検証は成功した。これらの成功はfixtureのgovernance不合格を解消するものではない。

### 14. `oneway`、左側通行、EV vClassの追加レビューを反映した

追加レビューで、type定義の`oneway`省略時は既定値`true`となるため、前処理漏れが道路を一方通行化し得るとの指摘を受けた。固定SUMO 1.24.0でfixtureを再変換し、`oneway`を欠くway 600について、正方向のedge `600`だけが生成され、逆方向edge `-600`が存在しないことを確認した。また、生成edgeの`osmDefaults`は`numLanes speed`だけを記録し、欠損`oneway`のfallbackを記録しなかった。

この結果から、`osm.annotate-defaults=true`による変換後監査だけでは`oneway`欠損を検出できないと判断した。一般道路をOSM規則により双方向と導出した場合も、前処理で`oneway=no`と来歴を変換用XMLへ必ずmaterializeする。値または来歴がない保持wayは`netconvert`前に停止する。

東京の左側通行については、`traffic_side.lefthand=true`と`netconvert.common_options.lefthand=true`が既に設定され、fixture実変換でも`--lefthand=true`を使用したことを確認した。OSMの一方通行方向自体を反転する設定ではないため、`reverse_osm_oneway_direction=false`を維持する。

EV配送車のvClassも明確化した。初期EV配送車は`vClass="delivery"`で道路利用区分を表し、電動パワートレインはSUMO battery deviceで別に設定する。typemapで許可していない`evehicle`は、`ignoring`、`custom1`、`custom2`とともに明示的禁止対象とした。`hov`と`trailer`を含むその他の非管理クラスも`reject_ungoverned_vclass=true`により拒否する。

この変更で設定をv5からv6へ更新した。typemapのルール本体は変更せず、`oneway`、`speed`、`numLanes`の具体的fallbackリスクをコメントへ追記したため、typemapのSHA-256は次となった。旧v5ハッシュ`6c667e13f405b78b86b999abb141f13e99bc88c35187af8a007e2318cefb83cf`は前節の履歴として残す。

```text
4e4273a5a73b8d1298751aeee141a387dc6a1524d64ed8ddd704cae8db0af590
```

v6更新後、関連ホストテストは`41 passed`、analysisコンテナ内のvalidation suiteは`136 passed`、SUMO 1.24.0 XSD検証は成功した。設定ID、設定版、typemap SHA-256の一致も確認した。runtime fixtureは引き続き不合格であり、正式利用不可の状態は変えていない。

### 15. 設計判断の分類と感度分析を修正した

追加レビューを受け、`priority`、道路ホワイトリスト、vClass permissions、属性省略、validator未完成、fixture合成値を同じ「恣意性」尺度で評価する整理を修正した。感度分析前に影響の大小を順位付けせず、次のように区別する。

- `priority`：東京への地域適合性の制限を伴う設計判断
- 道路ホワイトリスト：研究対象範囲の設計判断
- vClass permissions：車種別通行条件の設計判断
- 専用バス道路：ネットワーク表現上の設計判断
- typemapでの属性省略：根拠付き属性を要求する設計判断
- validatorと変換後監査の未完成：高い実装・品質保証リスク
- fixture数値：東京代表値ではないが正式実験から隔離した合成テスト入力

SUMO公式資料を再確認し、標準`osmNetconvert.typ.xml`はドイツの市街地外道路向けとして説明されていることを記録した。SUMO 1.24.0標準priorityの継承は結果確認後の個別調整を避けるが、東京への実証的妥当性を保証しない。

- <https://sumo.dlr.de/docs/OsmNetconvert.typ.xml.html>
- <https://sumo.dlr.de/docs/SUMO_edge_type_file.html>
- <https://sumo.dlr.de/docs/Simulation/Routing.html>

また、固定SUMO 1.24.0の`sumo`と`duarouter`について`--save-template`を実行し、両方の`weights.priority-factor`既定値が`0`であることを確認した。基準条件でも`weights.priority-factor=0`を明示し、priorityを静的経路コストへ直接加えない。priorityは交差点のright-of-way、停止、待ち時間、遅延、実現旅行時間への影響を主に確認する。実現旅行時間を使う再経路探索では間接的に経路が変わり得るため、その場合は別に記録する。

vClass数も再確認した。管理集合は8クラスだが、通常道路が8、motorwayとmotorway_linkがmopedを除く7、service compoundが2、専用バス道路が1クラスである。「すべての道路で8クラスを許可する」とは表現しない。

設定をv6からv7へ更新し、`design_decision_assessment`と`design_sensitivity`を追加した。priorityはSUMO標準、全type同一priority 1、固定した3段階階層を比較し、交差点待ち時間、停止回数、旅行時間、遅延を主指標とする。service permissions、専用バス道路、`track`、未解決属性も、それぞれの作用経路に対応した接続性、到達可能性、経路、距離、fallback等の指標を固定した。

相対変化は基準値が0でない場合に`abs(M_alternative - M_baseline) / abs(M_baseline)`で報告し、基準値が0なら絶対差を報告する。「影響が小さい」と判定する数値閾値は根拠を伴う事前登録が未完了であるため、現時点では合否判定へ使用しない。typemap本体は変更しておらず、SHA-256はv6と同じである。

v7更新後、関連ホストテストは`42 passed`、analysisコンテナ内のvalidation suiteは`137 passed`、SUMO 1.24.0 XSD検証は成功した。設定ID、設定版、typemap SHA-256の一致も確認した。runtime fixtureの不合格と`formal_build_ready: false`は維持している。

### 16. 属性補完規則、正式利用条件、access解決順を固定した

追加レビューを受け、構造確認用placeholderの具体値を先に決めず、値を決める統計規則と正式実験へ使用できる状態を先に固定した。固定大田区OSM抽出の明示値を母集団とし、`lanes`は道路種別と一方通行・双方向、`maxspeed`は道路種別で集約する。一意な最頻値、標本数30以上、最頻値比率50%以上を満たす場合だけ非重要道路の`structural_placeholder`として使用し、同率、標本不足または比率不足では近い道路種別へ移らず`unresolved`とする。具体値は分布集計後に別途固定する。

`oneway`への統計補完は禁止した。明示値`yes`、`no`、`-1`を優先し、`-1`はway方向を反転して`yes`へmaterializeする。明示値がないroundaboutとmotorwayはOSM暗黙規則による`yes`、motorway_linkは`unresolved`、その他の一般道路はOSMデータ消費規則による`no`とした。現在の大田区基礎集計ではmotorway・motorway_linkの`oneway`欠損は0件だが、将来入力のために規則を固定した。

正式実験では未検証placeholderを禁止する一方、推定値一般を禁止するのではなく、事前定義した補完モデルと独立した検証記録を持つ`derived_validated_model`を値状態へ追加した。モデルID、版、学習母集団、検証母集団、評価指標、受入規則および検証記録を必須とした。

permissionsは、OSM内で`access`、`vehicle`、`motor_vehicle`、車種別、方向別、lane別の順に具体的規則を上書きした後、研究対象集合との積集合を取る。SUMO importerの結果が期待値と一致しない場合に許可する後処理は積集合による縮小だけとし、typemap基本集合の拡張を禁止した。補正後は接続を再検査する。

ネットワークの管理集合8クラスと用途別生成集合も分離した。配送経路用途は`delivery`と`truck`、初期背景交通用途は`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`とした。`moped`はpermissions管理集合には残すが、需要根拠を固定するまで背景交通として生成しない。専用バス道路は現行v1でbus-onlyを維持し、配送例外を採用する場合は新しいcompound type、fixtureおよび設定版を必要とする。

この変更で`sumo_network.yml`をv7からv8へ更新した。typemap本体は変更していないためSHA-256は変わらない。runtime fixtureの既知の不合格は未解消であり、`formal_build_ready: false`を維持する。

参照した仕様：

- <https://wiki.openstreetmap.org/wiki/Key:oneway>
- <https://wiki.openstreetmap.org/wiki/Key:access>
- <https://wiki.openstreetmap.org/wiki/Key:lanes>
- <https://wiki.openstreetmap.org/wiki/Key:maxspeed>
- <https://sumo.dlr.de/docs/netconvert.html>

### 17. OSM属性resolverと変換前品質ゲートを実装した

2026年7月19日、`05_src/traffic_simulation/network/resolve_osm_attributes.py`を追加した。このモジュールは、固定設定v8を検証してからOSM XMLの保持対象wayを処理し、`oneway`、`lanes`、`maxspeed`を変換用XMLへmaterializeする。way・方向・laneごとにOSM access規則を広い規則から具体的な規則へ解決し、typemap基本permissionsとの積集合を期待値として監査CSVへ保存する。permissions計算に使用したaccessタグは、SUMO importerによる別解釈を避けるため、品質ゲート合格後の正規化XMLから除去する。

`oneway=-1`はnode順と方向別タグを反転して`oneway=yes`へ正規化する。roundaboutとmotorwayの暗黙規則、motorway_link欠損の停止、一般道路の双方向導出も実装した。`lanes`と`maxspeed`は明示値を優先し、構造確認用では非重要道路に限り、v8で事前固定した一意最頻値規則を適用できる。重要度が未分類のwayへplaceholderを自動適用しない。formal profileでは構造用placeholderを使用しない。

access resolverはv8で明示した`access`、`vehicle`、`motor_vehicle`、`motorcar`、`hgv`、`bus`、`delivery`と、方向別・lane別の対応タグを管理する。`goods`、`coach`、`taxi`、`psv`、`motorcycle`、`moped`等を含む未登録の車種別タグ、未対応値、条件付きタグ、曖昧な双方向lane指定、lane数不一致、管理外のaccess規則は`unresolved`として停止する。対応範囲の拡張は設定版を上げて行う。生成permissionsを広げる処理は実装していない。

正常系と欠損負例を次へ分離した。

```text
05_src/traffic_simulation/validation/fixtures/osm_attribute_resolution_positive.osm.xml
05_src/traffic_simulation/validation/fixtures/osm_attribute_resolution_negative.osm.xml
```

`test_resolve_osm_attributes.py`では、v8設定読込、最頻値条件、明示・暗黙方向、`-1`反転、構造用補完、formal停止、access上書き、lane別permissions、条件付き規則、属性矛盾、監査CSVおよび原子的XML出力を検査する。resolverとtypemapの対象テストは`36 passed`であった。

この実装はPBFからOSM XMLへの変換、外部データ補完表の取込み、重要道路の機械判定、生成`net.xml`へのpermissions適用、変換ログ・出力監査、SUMO CLI読込を含まない。既存runtime fixtureの不合格は未解消であり、正式buildは引き続き禁止する。

### 18. resolverレビューを反映し、停止境界と監査成果物を強化した

2026年7月19日、17節の実装に対して、除外道路がXMLに残る、未対応の明示値を構造用最頻値で上書きし得る、双方向1車線を各方向1車線として扱う、accessタグ削除後の期待permissionsが専用成果物に残らない、`oneway=-1`反転が左右依存タグを壊し得る、というレビューを受けた。これらは定量評価以前に解消すべき実装上の問題と判断した。

設定をv8からv9へ更新し、次を実装した。

- 保持対象外の`highway=*` wayを正規化XMLツリーから物理的に削除する。
- `missing`、`invalid`、`valid_but_unsupported`、`conflict`、`conditional`、`directionally_asymmetric`を分離し、構造用最頻値を真の欠損だけに適用する。
- `50 mph`等の未対応明示値、方向別に異なる速度、条件付き速度、未対応方向別車線表現を補完で上書きせず停止する。
- 双方向`lanes=1`を各方向1車線へ複製せず、lane方向配分を未解決として停止する。方向別タグのない偶数総車線は均等分割仮定を専用監査行へ記録し、感度分析未完了として扱う。
- `oneway=-1`は有効なOSM値だが、左右・方向依存タグを安全に網羅変換できるまでは元wayを変更せず停止する。
- accessタグを正規化XMLに保持し、way・方向・lane別の期待permissionsを必須JSONへ永続化する。生成`net.xml`への縮小方向の反映と全lane照合は後続実装とし、完了まで正式buildを禁止する。
- `designated`をキーと値の組合せで評価し、一般キーの`access=designated`を停止する。車種別適用順はYAMLの並びではなくコード側の固定順から作る。
- 車線数と速度の補完閾値を別フィールドとして読み、両者が同値であることをコードで強制しない。
- 補完集計を「local」ではなく`input_extent_way_count_unique_mode`と呼び、入力OSM SHA-256、母集団範囲、way個数という標本単位、グループ定義、属性別閾値、完全分布、採用値、最頻値比率、判断を必須JSONへ保存する。

補完母集団が入力範囲とOSM way分割に依存する問題、way個数重みと道路延長重みの比較、抽出範囲・集約範囲・閾値の感度分析、属性別criticalityの根拠スキーマはデータと事前登録を要する方法論課題であり、コードだけで値を決めなかった。これらをv9の未完了要件へ登録し、`structural`成果物は引き続き形状・接続確認専用、`formal_build_ready: false`とした。

この節は17節の`oneway=-1`反転とaccessタグ削除の記述を置き換える。履歴を時系列で追跡できるよう、17節の初期実装記録自体は削除していない。

v9更新後、resolverとtypemapの対象テストは`42 passed`、固定`analysis`コンテナ内のvalidation suiteは`170 passed`であった。これは前処理の停止境界と静的整合性を検査した結果であり、既知のSUMO runtime fixture不合格、permissions後処理、実PBF build、定量評価への適格性を解消するものではない。

### 19. formal先行順序と交通モデル品質ゲートを固定した

2026年7月19日、道路構造、需要・信号、較正、独立検証、配送最適化を分離する段階方針を再検討した。`structural_placeholder`を含む道路網で較正した後にformal道路属性を変更すると、較正値が構造誤差を補償し得るため、formal基準ネットワークの完成を需要投入と較正より前へ明示的に移した。

設定をv9からv10へ更新し、次を決定した。

- `structural生成 → 構造デバッグ → 属性・permissions確定 → formal基準ネットワーク → 需要・信号 → 較正 → 独立検証 → 配送・古典・QAOA評価`の順序を必須とする。
- formalネットワークまたは需要定義を変更した場合、それ以前の較正・検証結果を失効させる。
- 構造ゲートでは、管理対象OSM wayの説明可能な保持率、主要道路対の到達可能率、最大連結成分の道路長割合、方向不一致件数、代表OD経路成功率、SUMO読込、warning分類を計算する。
- 合格数値は結果を見る前に根拠付きで登録し、未登録の間はformalへ昇格させない。普遍的根拠のない95%等の値をコードへ仮置きしない。
- warningを停止対象、承認済み、情報通知へ分類し、未分類warningは停止する。
- OSM wayとSUMO laneを一対一と仮定せず、`OSM way → 複数SUMO edge → 複数lane`の来歴を保存する。全laneをOSM由来情報または明示生成規則へ追跡できなければ停止する。
- permissions後処理は縮小だけに限定せず、明示OSMタグ、公的規制情報またはレビュー済み証拠から導出した期待値へ完全一致させる。根拠のない拡張とtypemap基本集合を超える拡張は禁止する。
- SUMO版だけでなく、両コンテナのdigest、PROJ、`osmium`、Python、依存lock、platform、locale、出力精度、全入力・設定・`.netccfg`のSHA-256および完全なコマンドをbuild manifestへ保存する。
- JARTIC等の保存期間が短い観測データは道路網パイプラインと並行取得する。モデル投入はformal完成後とする。
- 交通量、速度、旅行時間、渋滞、信号条件は原則として同一日・同一時間帯で組み合わせ、異なる日時を混ぜる場合は補正と追加不確かさを記録する。
- 較正は需要、容量・飽和交通流、経路選択、旅行時間・速度・待ち行列、局所微調整の順に行い、全パラメータ群を同時に自由化しない。
- 較正・検証は事前固定した複数seed、ウォームアップ規則、評価時間帯で行い、反復数は出力分散と必要な信頼区間から決める。
- 道路属性レビューは最終経路だけでなく、デポ、全顧客、充電施設間で全比較手法が選択可能な候補部分グラフを対象とする。
- 古典手法とQAOAは同一インスタンス、目的関数、制約、実行可能性判定、復号・修復規則、seed集合で比較し、同一予算比較と最良基準比較を分離する。

これらは方法論と停止条件の固定であり、具体的な構造ゲート閾値、較正指標閾値、seed集合、ウォームアップ時間、JARTIC定期取得、permissions後処理および来歴監査の実装完了を意味しない。これらをv10の未完了要件へ登録し、`runtime_validation: failed_governance_fixture`と`formal_build_ready: false`を維持した。

v10更新後、resolverとtypemapの対象テストは`47 passed`、固定`analysis`コンテナ内のvalidation suiteは`175 passed`であった。これは設定と既存実装の静的整合性を検査した結果であり、実PBFからのformalネットワーク生成や交通較正を検証した結果ではない。

### 20. permissions生成順、信号構造、現行仕様の責務を修正した

2026年7月19日、v10の「生成後に根拠付きpermissionsへ完全一致させる」方針を再検討した。生成済み`net.xml`のlane permissionsを拡張しても、そのclassに必要なconnectionが生成済みである保証がないため、formal生成前の停止事項と判断した。また、信号交差点の採否とconnectionからTLS linkへの対応は時間制御ではなくネットワーク構造であり、formal基準ネットワークより前に確定すべきと整理した。

設定をv10からv11へ更新し、次を決定した。

- 期待permissionsを最終`netconvert`前の明示入力へmaterializeし、最終変換でlaneとconnectionを再構築する。
- 生成`net.xml`は編集せず、lane・connectionの完全一致監査だけを行う。不一致時は入力を修正して最終変換から再実行する。
- 信号交差点とTLS link構造をformalネットワークの一部とし、サイクル、現示、スプリット、オフセットを需要投入後の較正対象とする。
- 構造ゲートをvClass別・有向で評価し、デポから顧客・充電施設への到達と帰着可能性を分離する。保持率はway数と道路長の両方で報告する。
- 道路機能と舗装状態を分離する。`highway=track`は土地アクセス機能を理由に除外し、未舗装性は`surface`を中心に`smoothness`、`tracktype`を補助として判定する。
- 共通環境seedと解法固有seedを分離し、同じ整数を異種アルゴリズムへ渡しても同等乱数とは解釈しない。
- 小型配送車を`delivery`、重量貨物車を`truck`へ固定し、同一問題内で都合よくvClassを切り替えない。
- 大容量の正規化OSMと`net.xml`はGit外に置けるが、`.netccfg`、manifest、build summary、warning分類、checksum一覧はGitまたは改変不能なartifact storageで版管理する。
- SUMO 1.24.0 fixture、`v1_24_0`ソース・XSD、取得日とSHA-256を固定した公式文書、最新版文書の順に証拠を優先する。
- pytest件数だけでなく、commit、container digest、完全コマンド、collection hash、終了コード、log hash、開始・終了時刻を試験証拠として保存する。
- 本ファイルを変更履歴とし、現行仕様、network build、交通較正、最適化比較を別文書へ分離する。

要件状態を`policy_fixed`、実装、単体検証、runtime検証、実データ検証、formal適格性へ分解した。permissions materializer、信号構造レビュー、artifact publicationは方針固定のみで未実装である。固定SUMO runtime fixtureは不合格、実PBF検証は未実施であり、`formal_build_ready: false`を維持する。

v11更新後、resolverとtypemapの対象テストは`54 passed`、固定`analysis`コンテナ内のvalidation suiteは`182 passed`であった。typemapのXSD検証成功はruntime検証とは分類せず、permission importer fixtureの不合格を解消したとは扱わない。

### 21. materializer契約とformal停止条件をv12で固定した

2026年7月19日、Verification Stateを実装・実行済みの範囲と照合した。従来表ではtypemapのXSD検証をruntime非該当と記載していた一方、既に実行して不合格だったSUMO importer governance fixtureが同じ行に反映されていなかった。また、resolver、permissions期待値、materializer、変換後監査をまとめて記述しており、実装済み範囲を判別しにくかった。このため、設定をv11からv12へ更新し、policy、implementation、unit/static、XSD、runtime、real-data、formal eligibilityを要件ごとに分離した。

SUMO 1.24.0の固定コンテナで`edges_file.xsd`と`connections_file.xsd`を確認し、`--plain-output-prefix`、`--plain-output.lanes true`、`--output.original-names true`を使用したprovisional plain exportを正常系resolver fixtureに対して実行した。`.edg.xml`のlaneへ`param key="origId"`が出力されることと、plain edge/connection XMLが再入力interfaceとして利用できることを確認した。ただし、この実行では既知の`bus` compound warningと不正なimporter permissionsが残り、接続を持たないfixtureであったため、materializer、lane順、connection規則の正しさを検証した証拠ではない。

fixture実装前の契約として次を固定した。

- resolverの期待値JSONを不変成果物として保存した後、消費済みaccessタグを除いたtopology用OSM copyからprovisional plain XMLを生成する。
- materializerはprovisional fileを上書きせず、`governed_permissions.edg.xml`と`governed_permissions.con.xml`を生成する。最終`net.xml`は監査対象であり編集しない。
- laneは`origId`でOSM wayへ追跡し、edge方向は正規化OSM node順との比較で決める。edge IDの符号は方向根拠に使わない。
- resolver lane位置は進行方向から見たOSMの左から右、SUMO lane indexは右から左とし、`n` laneの位置`p`を`n - 1 - p`へ写像する。この規則は`--lefthand true`の固定fixtureで確認し、不一致なら実データへ進まず契約版を更新する。
- lane期待集合はresolver期待値、typemap基本集合、管理vClass集合の積集合とする。空集合は`allow=""`、非空集合は辞書順の空白区切りで書き、`disallow`を併記しない。
- connectionはprovisionalに存在する候補だけを扱い、from-lane、to-lane、provisional connection制限の積集合を期待値とする。空集合のconnectionは削除して理由を記録し、存在しないturnを新規生成しない。
- materialized edge/connection XMLのXSD適合、最終`netconvert`成功、SUMO読込、lane・connection完全一致、未追跡要素ゼロ、未分類warningゼロをfixture合格条件とする。

Verification Stateにはpermissions以外も含め、入力hash再検証、formal属性根拠、`oneway=-1`、junction join、信号junction/TLS-link、車両入力validator、prepare/validate pipeline、実行環境manifest、warning/exclusion監査、構造品質閾値、候補部分グラフreview、小型再現性成果物、最終SUMO loadをformal停止条件として列挙した。これらの方針assertionはruntimeまたは実データ検証の代替ではない。v12時点でmaterializerとformal networkは未実装・未生成であり、`formal_build_ready: false`を維持する。

### 22. readiness gate、TLS handoff、型付き状態をv13で修正した

2026年7月20日、v12の全要件を一つのformal build開始条件として評価すると、生成後にしか完了できないformal network、warning監査、成果物公開まで生成前に要求する循環が生じるとのレビューを受けた。また、`formal_eligibility`にbooleanと文字列が混在し、単純なtruth-value評価で未完了状態を合格と扱い得ることを確認した。

設定をv12から`ota_ward_sumo_network_v13`へ更新し、次を変更した。

- `formal_build_input_ready`、`formal_network_acceptance`、`downstream_experiment_ready`を依存順に分離し、requirement matrixを重複なく三つへ割り当てた。formal network生成物や候補部分グラフreviewをbuild開始条件に含めない。
- 各要件の状態を`eligible: boolean`、列挙型`state`、必須`reason`へ統一した。設定をschema version 2とし、Git管理のJSON Schemaと、重複YAML key、型、ゲート分割、版番号、主要なcross-field invariantを検査する専用validatorを追加した。
- specification状態を`current_governed_draft`へ変更し、固定済み方針と明示的blockerだけが承認範囲で、formal実行は未承認とした。
- access permission placeholderを禁止し、structural auditへ未解決状態を記録できることとは別の設定にした。
- permission materialization後にprovisional TLS assignmentを全て除去し、最終connection集合の確定後に`governed_reviewed.con.xml`と`governed_reviewed.tll.xml`を作る順序へ変更した。provisional `.tll.xml`はreview inputに限定し、最終変換では使用しない。
- 空lane permissionsは`allow=""`ではなく、固定fixtureで受理を確認することを条件に`disallow="all"`で非走行laneとして表現する。空connectionは削除して理由を記録する。
- governed provenanceの単純性を維持するため`geometry.remove=false`をcommon/formal双方で固定した。将来edge結合を採用する場合は、複数OSM way、premerge edge、removed nodeを表現する新しい来歴schemaと設定版を必要とする。
- resolverの全value stateを最終provenance集合へ反映し、未追跡lane/connection、予期しない・欠落connection、TLS link/phase長不一致、未分類warning、未照合edge削除を正式なpost-conversionゼロ件条件へ追加した。
- 道路交通センサスの確認済み用途をlane、道路幅、交通量、旅行速度へ限定し、指定最高速度と一方通行は具体的な項目定義確認待ちへ移した。JARTIC規制には規制種別、有効期間、反復、車種範囲、法的・行政的出典、snapshot日を必須とした。

v13は循環しない合否判定とpermissionからTLSへのhandoffを定義したが、materializer、review UI、post-auditorおよびruntime fixtureの実装完了を意味しない。三つのreadiness状態は全てfalseである。

### 23. 実装前の完全仕様パッケージをv14で固定した

2026年7月22日、fixtureとPermission Materializerを実装する前に、研究利用条件からPost-build Auditまでの責任境界、全入出力形式、failure code、fixture catalogue、要件・試験対応を一つの仕様体系として固定する必要があると判断した。設定を`ota_ward_sumo_network_v13`から`ota_ward_sumo_network_v14`へ更新した。

`05_src/traffic_simulation/specifications/`へ、研究要件、network build architecture、Resolver、Permission Materializer、TLS Review、Final Build、Post-build Audit、fixture、failure taxonomy、traceabilityの10文書を追加した。設定値と状態は`sumo_network.yml`、コンポーネントの規範動作はこれらの仕様書、成果物形式はJSON Schemaを正本とし、同じ判断を複数文書が独立に決定しない構成とした。

Materializerのformal edge方向判定では座標近傍照合を禁止し、Provisional Buildが生成する`edge_provenance.json`のOSM node lineage indexを使用する。source start indexがend indexより小さい場合をforward、大きい場合をbackwardとし、同値、欠落または曖昧な場合は停止する。OSMのlane listはforward/backwardとも各進行方向から見た左から右であり、Resolver内でbackward listを反転しない。SUMO lane indexは右端を0とするため、両方向に`n - 1 - p`を適用する。

Permission tokenについて、省略、`all`、明示allow、明示disallowの集合演算を固定し、空token、未知・管理外class、allow/disallow併記を停止対象とした。一部laneだけ空の場合は`disallow="all"`、directed edgeの全laneが空の場合はedgeとincident connectionを削除する。connectionは`from,to,fromLane,toLane`を一意キーとする明示lane-to-lane要素だけを対象とし、turnを新規推測しない。

固定SUMO 1.24.0の`connections_file.xsd`と`tllogic_file.xsd`を再確認し、`tl`、`linkIndex`、`linkIndex2`を持つTLS connection recordは`.tll.xml`側に存在し、permission `.con.xml`のconnection typeには存在しないことを記録した。このためMaterializerはprovisional TLS assignmentをconnectionから削除するのではなく、provisional `.tll.xml`をfinal inputへコピーしない。最終connection集合の確定後、TLS Reviewがreviewed `.tll.xml`とhash-bound manifestを生成する。

`reproducibility/config/traffic_simulation/schemas/`へ共通artifact、permission expectations、edge provenance、materialization audit/summary、failure report、TLS review manifest、build manifest/summary、post-build audit、requirements traceabilityのSchemaを追加した。70件の規範要件を個別test ID、fixture class、実装状態へ対応付けたmachine-readable registryも追加した。

v14は仕様の解釈を固定する版であり、v14形式のResolver artifact、edge provenance、Materializer、TLS Review、Final Build、Post-build Auditおよび対応fixtureの実装完了を意味しない。現行Resolverが出力するv13形式のpermissions JSONはv14 Materializerの適格入力ではなく、schema migrationを次工程のblockerとして登録した。

外部仕様根拠：

- <https://wiki.openstreetmap.org/wiki/Lanes>
- <https://wiki.openstreetmap.org/wiki/Forward_and_backward>
- <https://sumo.dlr.de/docs/Networks/PlainXML.html>
- pinned SUMO 1.24.0 XSD: `edges_file.xsd`, `connections_file.xsd`, `tllogic_file.xsd`

## 最終的に固定した内容

- 採用方式：自動車系道路typeの明示的ホワイトリスト
- vehicle class：`passenger,taxi,bus,coach,delivery,truck,motorcycle,moped`の範囲内
- 専用バスリンク：保持するが配送車の通行は許可しない
- 属性既定値：`speed`、`numLanes`、`oneway`をtypemapで補完しない。ただし、省略自体は欠損検出に使わない
- `oneway`：双方向の導出値も`oneway=no`として変換前に明示し、欠損を`osmDefaults`監査へ委ねない
- `oneway=-1`：左右・方向依存タグの安全な変換実装が完成するまで原データを変更せず停止する
- `oneway`暗黙規則：roundaboutとmotorwayは`yes`、motorway_link欠損は`unresolved`とし、統計的placeholderを使わない
- 構造用補完：`lanes`と`maxspeed`だけを対象に、一意な最頻値、標本数30以上、最頻値比率50%以上を要求する
- 構造用補完の入力：真の欠損だけを対象とし、未対応明示値、矛盾、条件付き値、方向非対称値を上書きしない
- 正式用補完：独立した検証記録を持つ`derived_validated_model`だけを許容し、未検証placeholderを禁止する
- 通行側：`lefthand=true`を設定と実行で必須とし、一方通行方向自体は反転しない
- priority：SUMO 1.24.0標準値を継承する
- 対象外type：`discard="true"`で明示する
- 未知type：採用せず、後続パイプラインでは検出時に停止してbuild summaryへ記録する
- SUMO入力vClass：管理対象8クラスだけを許可し、`ignoring`、`custom1`、`custom2`、`evehicle`を禁止する
- EV配送表現：`vClass="delivery"`とSUMO battery deviceを組み合わせ、`evehicle`を禁止する
- access処理：`osm.lane-access=true`を固定し、fixtureと生成permissions監査で動作を確認する
- permissions処理：期待値を最終変換前の明示入力へmaterializeし、生成`net.xml`は編集せずlane・connectionを完全一致監査する
- resolver監査：期待permissionsと補完完全分布を専用JSONへ保存し、accessタグは変換後照合が完成するまで保持する
- 用途別vClass：配送経路用と背景交通用を分け、ネットワークの管理集合8クラスと混同しない
- 工程順序：placeholderを除去したformal基準ネットワークを需要投入・較正より前に完成させる
- 実行環境：SUMO、PROJ、依存環境を含むコンテナdigestと全入力・設定・コマンドのfingerprintを保存する
- 信号：交差点とTLS link構造はformal前、時間制御は需要投入後に固定・較正する
- 道路表面：道路機能と舗装状態を分離し、`surface`を主要判定タグとする

## 残作業と変更管理

固定環境で次を確認する。

```bash
docker compose build analysis
docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q
```

その後、属性ガバナンス処理、保持wayの属性・来歴validator、SUMO車両入力validator、変換ログ・生成ネットワーク監査、道路網生成パイプラインを実装する。実OSM XMLからの変換、生成`net.xml`の読込、未知type、compound type、条件付きaccess、permissions、default由来値を検証する必要がある。

priority階層は東京の実道路優先関係を検証した結果ではない。また、SUMOの`motorcycle`は日本の排気量区分別規制を完全には表現しない。採用type、vehicle class、priorityを変更する場合は、typemap方針IDと`sumo_network.yml`の設定版を上げ、変更理由と再検証結果を本ファイルへ時系列で追記する。

Git管理対象には、カスタムtypemap、`sumo_network.yml`、テスト、現行仕様、protocol、変更履歴を含める。大容量の生成OSM XMLと`net.xml`はGit管理外にできるが、`.netccfg`、manifest、build summary、warning分類、checksum一覧はGitまたは改変不能なcontent-addressed artifact storageで版管理し、外部保存時はGit管理のindexから参照できるようにする。

### 24. Resolverのpermission成果物をv14形式へ移行した

2026年7月22日、`ota_ward_sumo_network_v14`の実装として、Resolverが出力する旧map形式のpermissions JSONを、`permission_expectations.schema.json` version 2に適合する成果物へ置換した。成果物にはartifact/config identity、profile、入力OSM、成功時の正規化OSM、typemapのpath・SHA-256・policy ID、管理対象vClass、OSM way、SUMO type、方向、車線位置、期待vClass集合、適用rule IDを記録する。失敗時は文字列だけでなく、stable RS code、component、location、value stateおよびsource valueを持つ型付きblockerを記録し、正規化OSMは公開しない。

productionコードからgoldenを生成しない方針に従い、正常fixture、欠損属性fixtureおよびforward/backward各2車線の双方向fixtureに対する独立oracleを追加した。両方向ともOSMの各進行方向から見た左から右の順を保持し、Resolver内でbackward配列を反転しない。JSON Schema検証、旧v13 map-only形状の拒否、入力・出力hashおよびrule provenanceをテスト対象とした。

この変更はfixture上のv14成果物実装を示すが、登録済み大田区OSM extractに対する実行証拠ではない。`permission_expectation_artifact`の状態は`pending`とし、formal build input readinessはfalseのまま維持する。次の停止条件は登録済みextractでのResolver実行ではなく、まずexact `edge_provenance.json`を生成するProvisional Buildの実装とする。

### 25. Resolver v14のformal安全性と監査粒度を修正した

2026年7月22日、`ota_ward_sumo_network_v14` Resolverの外部レビューで、formal profileでも双方向偶数車線を等分できること、停止wayが構造用補完donorへ混入し得ること、permission provenanceがway上の全access tagを全laneへ付与すること、および`--overwrite`中の失敗で異なるrunの成果物が混在し得ることが指摘された。これらはformal利用を妨げる実装上の問題として修正した。

formalでは`lanes:forward`と`lanes:backward`の明示を必須とし、等分仮定はstructuralの偶数総車線だけへ限定した。補完donorは、解決可能なoneway、整合する明示lanesとcanonical maxspeed、conditional不在、permission解決成功を全て満たすwayだけとした。`oneway=-1`や方向別speed矛盾を持つwayはdonorから除外する。`service|bus`と`service|psv`を含む保持判定はexact SUMO type IDへ統一した。

permission artifactには、typemap baseline、研究vClass積集合、実際に適用した一般・車種・方向・車線別OSM tagについて、laneごとのsource value、lane value、適用前後vClass集合を順序付きtraceとして保存する。他方向・他laneだけに作用するtagは記録しない。全成果物はstagingで生成・検査後、backupとrollbackを伴って一括公開する。書込み例外時の`.part`も削除する。

さらに、malformed tag、node/Relation参照、criticality sourceとcoverage、typemap `disallow`禁止、補完閾値範囲、Decimal速度正規化を検証対象とした。Resolver CLIはfailure report pathを必須入力とし、通常のblockerは固有RS codeを保持し、XML/input identityを`RS001`、config/typemap/criticalityを`RS004`、Schema/accountingを`RS011`、path/write/publicationを`RS012`へ分類する。fixture検証は実データ適格性の代替ではないため、全readiness状態はfalseのまま維持する。

### 26. 自動車系単一モードを全研究工程の範囲として明確化した

2026年7月23日、`ota_ward_sumo_network_v14`について、「初期道路網は自動車系単一モード」とする記述が、後続段階で歩行者、自転車、鉄道または船舶を含むマルチモーダル道路網へ拡張する可能性を残していたため、研究範囲を明確化した。本研究は、道路網生成、交通シミュレーション、配送評価および手法比較の全工程を通じて、`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`、`moped`の統制済み8クラスだけを道路permissionsの管理集合とする。

歩行者、自転車、鉄道および船舶の専用リンクと需要は後続工程でも追加せず、マルチモーダル版は本研究の範囲外とした。自動車との共用道路は、歩行者または自転車も通行可能であることだけを理由には除外しない。緊急車両、行政車両など管理集合外の自動車系SUMO classも追加しない。

この変更は、保持type、8クラスの集合、lane permissionまたはconnection permissionの実効値を変更せず、研究期間に関する既存方針の曖昧さを除くものである。そのためconfig identityはv14を維持した。一方、typemap内コメントを統一したことでファイルSHA-256は`0e3a618cb47108a3b78af77ea8fa738c9ef25fb4864756a0bfa032ef3d457120`へ変わったため、`sumo_network.yml`と独立fixture oracleの登録hashを同時に更新した。旧hashを参照する未承認のfixture成果物は新hashで再検証し、異なるtypemap hashの成果物を混在させない。

### 27. mopedを除外し、専用バスと後続利用データの位置付けを固定した

2026年7月23日、配送研究との対応を再確認し、`moped`を道路permissionsの管理集合、SUMO車両入力、背景交通生成、到達可能性評価およびResolverの車種別解決対象から除外した。通常道路とmotorwayを含む保持道路の最大管理集合は、`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`の7クラスとなる。これは実効permission集合を変更するため、設定を`ota_ward_sumo_network_v14`から`ota_ward_sumo_network_v15`へ更新した。

専用バス道路は配送車の経路候補ではないが、背景交通としてのバス運行と道路網上の交通条件を表すために保持する。`highway.busway`と`highway.bus_guideway`は引き続き`bus`だけを許可し、配送例外を暗黙に追加しない。vehicle class集合の変更に伴いtypemap方針IDを`tokyo_motorized_v2`へ上げた。typemapのSHA-256は`81c7ed6c5f40ce0e06071bbba0ecc52b5abc2b2d8b8da64dc9cb2b3296c253be`へ更新し、独立oracleも`permission_expectations_v15.oracle.json`として更新した。

海外の運転行動データ、天候、事故、および運転行動データに含まれる歩行者関連項目は削除しない。ただし、これらはコア比較の入力ではなく、別に統制する後続段階の文脈分析または感度分析に限って使用する。海外データの絶対値を東京へ直接移植せず、天候と事故は通常条件の基準モデルが較正・独立検証された後に導入する。歩行者関連項目は自動車運転者が直面した状況を表す共変量であり、歩行者agent、歩行者需要または歩行者ネットワークモードを導入するものではない。

### 28. onewayタグ欠損と方向未解決を区別した

2026年7月23日、`ota_ward_sumo_network_v15`の`oneway`基礎集計におけるタグ欠損を、そのまま通行方向の未解決件数として読める表現が残っていたため修正した。一般道路で`oneway`タグが明示されていない場合は、元タグの不在を保持したまま、OSMの通常解釈と固定Resolver規則により実効値`no`を導出する。これは最頻値による欠損補完ではなく、監査上は`source_value=""`、`adopted_value="no"`、`value_state="derived_osm_rule"`および適用規則として分離する。

対象26,201 wayのうち、明示的な`oneway`タグがないwayは19,753であるが、欠損集合に`motorway`、`motorway_link`または`junction=roundabout`はなく、基礎集計上、タグ欠損だけを理由に意味を導出できないwayは0である。一方、保持候補にある`oneway=-1`の1 wayは意味と入力値が妥当であり、`invalid`または`unknown`ではなく`valid_but_unsupported`、failure code `RS007`として扱う。正式な実データResolver実行とPost-build Auditは未完了であるため、安全に変換可能な全件数と生成後の方向edge不一致件数は未確定のままとする。

この変更はResolverの実効動作を変更せず、既存の監査状態、機械可読設定およびテストを明示化するものである。`oneway`タグ欠損には同種道路や周辺道路の最頻値を使用しないという方針も、より具体的な表現へ統一した。

同時に、26,201 wayを一件ずつ目視確認するのではなく、明示値と固定規則で通常ケースを全件処理し、`unresolved`、`conflict`、`valid_but_unsupported`、`invalid`および未登録の`unexpected`だけを人のレビュー対象とする運用を固定した。新規例外は個別データを直接修正せず、決定表、fixture、Resolver、登録済み入力の全件Dry Runの順に反映する。進捗正本もv15 ResolverのDry Runと例外キュー生成を次作業として更新した。

### 29. 登録済み入力でv15 Resolverの全件Dry Runを実行した

2026年7月23日、`ota_ward_sumo_network_v15`を用いて登録済み大田区入力の`structural` Dry Runを実行した。BBOX抽出PBFのSHA-256は取得記録と一致した。`complete_ways`抽出には部分relationが含まれるため、道路接続に不要なrelationを参照検証前に除外し、抽出内581件のturn restriction relationについては、登録済み関東PBFから参照node・wayを再帰的に補足したResolver専用入力を作成した。非道路relationは削除するが、不完全なturn restriction relationは停止する規則を固定した。

最終入力では26,220 wayを処理し、83,884 audit行を生成した。24,346 wayに46,056 blockerが残り、正規化OSMは公開されなかった。内訳は、bulk欠損45,749行、permission未解決264行、車線表現未対応19行、速度表現未対応22行、`oneway=-1` 1行、車線矛盾1行である。permission期待値が完全なwayは1,874であった。`oneway`は、一般道路の双方向導出19,764、明示値6,455、妥当だが実装未対応の逆向き一方通行1であった。

全件実行により、除外wayを約170万nodeを持つXML rootから一件ずつ削除する二次的処理も発見した。除外対象を収集してrootを一度だけfilterする線形処理へ変更し、fixtureで同じ除外結果を確認した。実行コマンド、relation closure、入力・成果物hash、Failure Code分布および次作業は`03_data/metadata/acquisition/20260723_ota_ward_v15_resolver_dry_run.md`へ固定した。正式ネットワーク適格性はfalseのままである。

### 30. 版16母集団へ属性重要度分類と属性値解決を接続した

2026年7月30日、受理済みrelation closure版16を属性重要度分類と属性値解決の入力にするため、設定を`ota_ward_sumo_network_v16`へ更新した。版16の受理manifest、relation-closed OSM XMLおよび道路役割成果物のSHA-256を出典台帳へ直接登録し、版15の分類・解決記録を前版として参照しない初回生成とする。

属性値解決処理は分類専用成果物を読み取り専用として扱い、採用値、証拠候補と選択結果、競合解決規則、確認状態および停止コードだけを追加する。統合後はレコード全体の自己ハッシュを再計算するが、重要度、選択規則および一致規則は変更しない。未解決組は削除せず停止記録として保持し、一件でも残る場合は`complete=false`とする。

外部管理の判定事実について、較正区間、独立検証区間、主要交差点進入部、受理済み配送経路および感度分析対象は、この時点で受理済みの正例割当がないことを明示する。空集合は値の欠損や暗黙の偽値ではなく、版16全道路を負の適用範囲とする独立成果物として固定する。後に正例を受理する場合は、その出典成果物と規則版を更新して分類レコードを新規改訂する。
