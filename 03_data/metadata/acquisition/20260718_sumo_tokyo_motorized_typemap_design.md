# 東京自動車系SUMO typemap：時系列作業記録

## 記録情報

- 記録日：2026-07-18
- 実施者：研究環境管理者（Codex支援）
- 状態：`implemented_runtime_validation_failed`
- 設定ID：`ota_ward_sumo_network_20260716_v10`
- typemap方針ID：`tokyo_motorized_v1`
- 対象ファイル：`reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml`
- 関連設定：`reproducibility/config/traffic_simulation/sumo_network.yml`
- 関連方針：`05_src/traffic_simulation/network_attribute_governance.md`
- 関連実装計画：`05_src/traffic_simulation/implementation_plan.md`

本ファイルを、このtypemapの設計、作成、検証に関する唯一の作業メモとする。第三者データの取得記録やSUMO道路網の生成記録ではない。

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
- permissions処理：OSM内の上書き関係を先に解決し、根拠付き期待値へ完全一致させる。根拠のない拡張とtypemap基本集合を超える拡張は禁止する
- resolver監査：期待permissionsと補完完全分布を専用JSONへ保存し、accessタグは変換後照合が完成するまで保持する
- 用途別vClass：配送経路用と背景交通用を分け、ネットワークの管理集合8クラスと混同しない
- 工程順序：placeholderを除去したformal基準ネットワークを需要投入・較正より前に完成させる
- 実行環境：SUMO、PROJ、依存環境を含むコンテナdigestと全入力・設定・コマンドのfingerprintを保存する

## 残作業と変更管理

固定環境で次を確認する。

```bash
docker compose build analysis
docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q
```

その後、属性ガバナンス処理、保持wayの属性・来歴validator、SUMO車両入力validator、変換ログ・生成ネットワーク監査、道路網生成パイプラインを実装する。実OSM XMLからの変換、生成`net.xml`の読込、未知type、compound type、条件付きaccess、permissions、default由来値を検証する必要がある。

priority階層は東京の実道路優先関係を検証した結果ではない。また、SUMOの`motorcycle`は日本の排気量区分別規制を完全には表現しない。採用type、vehicle class、priorityを変更する場合は、typemap方針IDと`sumo_network.yml`の設定版を上げ、変更理由と再検証結果を本ファイルへ時系列で追記する。

Git管理対象は、カスタムtypemap、`sumo_network.yml`、typemap単体テスト、本記録とする。生成されるOSM XML、`.netccfg`、manifest、`net.xml`、build summaryはGit管理対象外とし、後続のSUMO道路網生成記録にSHA-256と実行結果を保存する。
