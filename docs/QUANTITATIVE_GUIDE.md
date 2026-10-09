# Quantitative Research Guide

正式API・保存結果・小規模再利用の統合ガイドです。科学的凍結報告とは別の利用説明であり、研究の数値・RQ・仮説は変更しません。

- [0. Open Data to Frozen Results](#0-open-data-to-frozen-results)
- [1. Research Scope](#1-research-scope)
- [2. Model Architecture](#2-model-architecture)
- [3. Routing Model](#3-routing-model)
- [4. Quantum Model and Protocol V2](#4-quantum-model-and-protocol-v2)
- [5. Simulation and Trajectories](#5-simulation-and-trajectories)
- [6. Battery and Controlled-DC Energy](#6-battery-and-controlled-dc-energy)
- [7. Analysis and Frozen Results](#7-analysis-and-frozen-results)
- [8. Data and Configuration](#8-data-and-configuration)
- [9. Notebook Guide](#9-notebook-guide)
- [10. Quickstart and Dependencies](#10-quickstart-and-dependencies)
- [11. Reproducibility and Verification](#11-reproducibility-and-verification)
- [12. GitHub and Hayate Responsibilities](#12-github-and-hayate-responsibilities)
- [13. Data Attribution and Licensing](#13-data-attribution-and-licensing)
- [14. Limitations and Provenance](#14-limitations-and-provenance)

## 0. Open Data to Frozen Results

本節は研究上の課題からデータ取得、加工、計算、結果の確定までを順に説明する。**CONFIRMED**は保存資料・実行記録で確認した事実、**RECONSTRUCTED**は複数の証拠を接続して再構成した経緯、**INFERRED**は研究設計からの推定、**UNKNOWN**は証拠不足である。過去の実行記録を読むことと、その工程を今回再実行することは別である。以下では新しい科学実験・需要生成・道路再構築を行っていない。全体の研究課題と今後の研究は[研究基準文書](research/RESEARCH_BASELINE_20261009.md)を参照する。

### 0.1 研究上の問題意識

**CONFIRMED：** 上位目的は必要な物流サービスを確保しながらエネルギー消費を下げることであり、正式RQはEV配送の経路計算とBattery性能を介した量子技術の影響を問う。そこで、経路を変えるPath 1と、同じ走行軌跡でパック・車両質量条件を変えるPath 2を接続した。実施済みの評価対象はDC牽引電力量であり、社会全体の消費、充電込みの主仮説の検証完了ではない。正式RQと仮説の原文は[第1節](#1-research-scope)に保持する。

### 0.2 なぜオープンデータを組み合わせたか

**RECONSTRUCTED：** 直線距離だけでは、道路の接続、向き、通行可能性が経路選択と走行に与える制約を表せない。一方、道路だけでは配送先の分布や需要量は分からない。このため、OSMの道路、PLATEAUの建物、行政界、公的統計の人口・世帯・受取頻度を異なる役割の入力として接続した。取得台帳、需要工程台帳、最終入力契約の対応から、この設計を再構成できる。道路属性の観測、統計による較正、研究者の仮定は同じ確実性を持たない。

**INFERRED：** 個別企業の注文記録に依存せず、入力の出所と仮定を追跡できる比較問題を構成することは、合成需要を採用する合理的な理由である。ただし、配送会社へのデータ提供依頼や不許可の履歴を確認したわけではなく、「注文データを入手できなかったから」と過去の意思決定を断定しない。**CONFIRMED：** 実際に用いたのは統計から生成した需要であり、配送会社の実注文履歴ではない。

### 0.3 対象地域とデータ選定

**CONFIRMED：** 初期実装計画は、東京全域へ直ちに進まず、環境・データ統合検証を大田区で開始すると定めている。研究範囲は国土数値情報N03の2026年東京都行政界から行政区域コード`13111`を選び、東京都・大田区の名称も照合して固定した。観測点数や結果の良否で境界を動かさない設計である。境界矩形は取得用、行政界ポリゴンは地域判定用であり、同一ではない。

**INFERRED：** 一自治体に限定し、道路・建物・統計を共通の地域キーで接続することは、都市規模のデータ処理を管理可能にする。**UNKNOWN：** 大田区を他自治体より優先した理由を、空港・工業地帯・所属機関との近さ等に帰す根拠は今回確認していない。都市の特性から後付けの選定理由を作らない。

### 0.4 何を、どこから、どう取得したか

**CONFIRMED：** OSMには地域ごとの固定snapshotを取得できるGeofabrikを用いた。2026-07-17の取得記録と出典台帳は、関東の`kanto-260716.osm.pbf`、データ時点`2026-07-16T20:21:30Z`、476,772,780 bytes、SHA256 `aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d`を記録する。[関東配布ページ](https://download.geofabrik.de/asia/japan/kanto.html)と[当時の日付固定URL](https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf)を区別する。現在のlatestは別のsnapshotであり、代用して同じ実験としない。日付固定URLの現在の取得成功までは保証しない。

取得記録に残るコマンドは次である。これは当時のDocker・Hayate側コードを必要とする**履歴上の実行手順**であり、現在の小規模GitHub配布だけで実行できるコマンドではない。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.network.fetch_osm \
  --region ota_ward --snapshot-date 20260716
```

同処理は日付固定URLを組み立て、`.part`へ取得し、サイズ・PBF形式・要素数・SHA256を検査してから原本を確定した。Overpassやブラウザの手動エクスポートを用いたという記録ではない。道路データベースの出典は© OpenStreetMap contributors、利用条件はODbL 1.0であり、詳細は[帰属表示と配布](#13-data-attribution-and-licensing)を参照する。

**CONFIRMED：** 建物には国土交通省Project PLATEAUの[3D都市モデル（大田区）（2025年度）](https://www.geospatial.jp/ckan/dataset/plateau-13111-ota-ku-2025)のCityGMLを採用した。保存ZIPは`13111_ota-ku_pref_2025_citygml_1_op.zip`、543,501,320 bytes、SHA256 `820f2b6c7af9e2a097c0868f3452953cbbe90f81c450ae5880f31eb52d159800`である。保存取得資料は2026-08-21、ZIP内READMEは作成2026-03-13・製品仕様第5.0版を示す。データ年度、README作成日、取得日を混同しない。

**RECONSTRUCTED：** 配布ページで大田区2025年度を選び、CityGMLのZIP resourceを取得し、ファイル名・README・hashを保存するという取得経路が資料と整合する。**UNKNOWN：** 個別のブラウザクリック列や当時のcurlコマンドは確認できないため提示しない。建物形状・用途と位置を接続できることが研究上の採用意義であるが、CityGMLの全属性を計算に使ったとはしない。利用条件は配布ZIPの表示と提供元の条件を優先し、研究コードのApache-2.0を適用しない。

**CONFIRMED：** 需要統計はe-Stat等の公的集計を用いた。2020年国勢調査の小地域CSV（表ID`000032163278`）と500mメッシュ（`T001141034`等）、2023年住宅・土地統計調査（表ID`000040209857`）は世帯構成・住宅区分・地域配分へ接続する。元表の全採用セルと合成世帯への変換は完全には復元できていない。

受取頻度は[国土交通省・東京都市圏物資流動調査、令和6年度「個人のモノの受取調査」](https://www.e-stat.go.jp/stat-search/files?layout=dataset&tclass1=000001223521&tclass2=000001234242&toukei=00600520&tstat=000001078042)のss521「世帯人数別・世帯構成別宅配受取頻度（回数）・再配達頻度（割合）」である。`ss521_r06a.xlsx`、シート`ss521_R06`、SHA256 `5b6ae34c771739869648147487780d4f0bb1f2a556f36c5ff97ee0514de664e0`を保存manifestで識別できる。取得観測日は2026-08-23、manifest固定は08-29である。08-25の9表の原本固定記録にはss521は含まれないため、後続manifestと採用強度CSVで接続を確認した。

**RECONSTRUCTED：** e-Statの該当統計・年度・表分類からExcelを取得することが一般的な取得手順である。ss521はworkspaceから供給されたファイルとの記録であり、当該URLから直接通信したログを意味しない。2026-10-09の説明整備時、Geofabrik配布ページは閲覧できたが、PLATEAU・e-Statの上記ページは閲覧ツールで取得できず、年度・取得日は保存された資料に基づいている。

### 0.5 道路を走行計算に使える形へ加工する

**CONFIRMED：** まずN03行政界からEPSG:4326の外接矩形（西139.652974773、南35.528198081、東139.826027782、北35.613210171）を機械生成した。osmium-tool 1.15.0の`extract --strategy complete_ways --set-bounds`で交差するwayの参照ノードを保持し、12,218,967 bytesの大田区抽出PBFを得た。wayを矩形境界で切断しないため、含まれるノードの範囲は取得矩形より広がり得る。初期抽出には40,880のhighway wayがあるが、その数を最終走行可能edge数としない。

**RECONSTRUCTED：** 抽出だけではrelationの参照、方向、車線、速度、通行規制を確定できないため、後続の関係閉包・属性解決工程へ進んだ。保存された入力は`ota_ward_20260716_relation_closure_v16.osm.xml`であり、v17のblocker記録と属性補完へ接続する。highway種別にはmotorway/trunk/primary/secondary/tertiaryと各link、unclassified/residential/service/living_street等がある。自動車系の種別選択と、個別のdelivery車両の通行可否は別の判断である。

**CONFIRMED（保存コードの内容）：** three-tier補完器は元の`lanes`、`maxspeed`、`access`等を読み、明示値・推定値・fallbackを分けて記録する。例えば保存コードの速度表はmotorway80、trunk60、primary50、secondary/tertiary40、residential30、service/living_street20 km/h等である。これらは欠損時のモデル規則であり、実測速度ではない。保存された値決定関数はaccess=noをno、他をyesへ処理する箇所を持つため、全法的通行規制を精密に復元したとは説明できない。`EXTRATREES_BENCHMARK_PROXY`という名称だけから学習済み機械学習モデルの使用を推定しない。採用runner・全補完レコード・最終値の完全な対応確認は未完了である。

**RECONSTRUCTED：** 補完OSMをSUMO/netconvert 1.24.0で`--osm-files --proj.utm --ignore-errors`等の保存コマンドにより変換し、junction（接続点）、edge（有向道路）、lane（走行車線）を得た。OSMのwayとSUMO edgeは単純な一対一ではなく、道路接続と車線許可を含む変換である。変換成功だけで実都市の完全な通行再現や信号・交通量の妥当性を保証しない。

**CONFIRMED／UNKNOWN：** 最終幾何補正の実コマンド・`repair_network_geometry_lengths.py`・repair報告は、lane形状をjunction端点へ接続し、接続後の折線長をlane lengthへ反映したと記録する。一方、config snapshotには「length維持」と実在を確認できない別generator名があり、整合しない。本説明は実在コード・コマンド・変換報告に基づくが、PBFから最終XMLまで完全な同一再生成が可能とはしない。最終XMLのhashは`460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`であり、下流planと一致する。この実ファイルを[道路データRelease](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)で提供している。

### 0.6 建物と統計を需要の基礎へ加工する

**CONFIRMED：** 現在のHayateには建物候補CSVが存在し、building_id、building_usage、住宅区分との適合、geometry参照、階数・地下階数・高さ、source_file/feature_id、除外状態を記録している。過去の監査で未回収とされたCSVは今回実在を確認したが、中間parquetの生成器の回復を意味しない。保存されている高さ・階数の列を、そのまま世帯配分の重みとして使ったとはしない。

**RECONSTRUCTED：** CityGMLの建物ID・用途を住宅候補へ対応させ、町丁目との空間的な対応を作り、代表点を後段の配送地点へ渡したという流れが工程台帳と保存出力から読める。**INFERRED：** 通常この接続には座標系を合わせた形状読込み、代表点の計算、行政区画への空間結合が必要である。しかし、代表点が重心か内部点か、使用した全用途コード、境界処理、入力ZIPの混合有無は確認できない。

**UNKNOWN：** `plateau_buildings_all_with_chocho_points.geo.parquet`の記録hashは`6779656a0719bb91b9bf97513e23498d88f5bc9eacdebccfcc7d5b1b5e161fa0`であるが、原本と直接生成コード・ログは未回復である。ZIP内説明のLOD1建築物158,860棟と工程台帳の候補195,311行は一致しない。その理由を重複や建物分割だと断定しない。ZIP→候補→この中間parquetの完全来歴が残る確認点である。

**CONFIRMED：** 公的統計から生成した合成世帯は384,353である。住宅区分は市区町村集計に基づく多項・カテゴリ割当、seed20260830との記録がある。これは実在世帯の個票や居住建物を観測したものではない。建物への割当では許された住宅候補からの一様離散選択を採用し、住戸数、入口、建物収容能力、最寄り候補による救済は使用していないと保存summaryに明示される。全世帯生成の乱数環境・固定行順・採用セルの詳細は未回復である。

### 0.7 世帯から一日の合成配送需要を生成する

**CONFIRMED：** 基準需要設定は2024年全国宅配便取扱量5,031,470,000、全国人口123,802,000、大田区人口736,652、365日を採用した。全国一人当たり日量を大田区人口へ移す式は`5,031,470,000 / 123,802,000 / 365 × 736,652`で、保存台帳の値は82,023.204937、整数の期待日量は82,023 parcel-equivalentである。これは全国規模の取扱量の人口比例移転であり、大田区住宅の実注文総数の実測・推定精度を保証しない。全国量には住宅B2C以外も含まれ得る。

基準メッシュ工程は2020年人口メッシュを行政界との面積で按分し、2024年大田区人口へ再尺度化し、最大剰余法で整数を配分した。世帯への期待値配分では、ss521の受取経験のある世帯の人数別小計を使用する。採用週頻度は1人0.65148273、2人0.93035232、3〜4人1.18813494、5人以上1.45298673回/週である。共通参照0.8498914166013274回/週で割った相対強度rを用い、`lambda_h = 82023 × r_h / sum(r_h)`として各世帯の日量期待値を与える。週頻度をそのまま全世帯の実日量と解釈せず、都市全体の期待日量を配分する相対情報として使用している。

**CONFIRMED：** 保存された生成仕様は`N_h,d ~ Poisson(lambda_h)`、seed20260829、合成評価日2026-01-01である。評価日の文字列は取得日より前でも、実際にその日に観測したという意味ではない。Poissonと世帯間独立性はモデル仮定であり、実測分散に適合したことを確認したものではない。保存された期待値合計82,023.00000048117と目標82,023の差は記録された許容差内である。乱数生成ライブラリ・全行順を含む原生成器は未回復なので、seedだけで全く同じ標本を再生成できるとはしない。

|段階|保存値|何を数えるか|
|---|---:|---|
|合成世帯|384,353|統計から作った世帯record|
|一日の期待総量|82,023|parcel-equivalent、乱数実現値ではない|
|正の需要record|73,547|正の世帯日需要record（複数parcel-equivalentを含み得る）|
|生成需要総量|82,246|parcel-equivalent、注文record数ではない|
|建物対応済み世帯|382,369|全合成世帯のうち割当済み|
|需要のある対応済みrecord|73,200|建物へ対応した需要record|
|建物対応済み需要量|81,859|parcel-equivalent|
|需要のある建物／配送地点|39,956|同一建物でまとめたstop|

**CONFIRMED：** 後段のscoped summaryは、候補なし206世帯・住宅型非対応1,778世帯を残し、割当済み世帯を85,690建物へ対応させる。正の需要を持つrecordをbuilding IDで集約してparcel-equivalentを加算し、39,956地点とした。`matched`および`matched_cross_boundary`の範囲を採用し、曖昧・範囲外等を無断補完しない。生成総量82,246全体の保存ではなく、割当範囲内の81,859だけがstopへ保存されている。初期summaryのactive_buildings=0は建物割当以前の記録であり、後段の39,956を打ち消さない。

### 0.8 配送地点から比較可能な配送問題へ

**CONFIRMED：** 建物代表点は入口・停車場所ではない。配送地点を道路上のMODEL_SERVICE_POINTへ対応させ、delivery車両が利用する有向edge・lane・道路上位置を固定した。デポDEP_006はP31物流施設候補に由来する研究上の代理拠点であり、配送会社の営業区域を観測したものではない。位置の道路対応を確定してから、位置付きの有向OD旅行時間・距離、到達可能性を計算した。同一edge上でも進行方向により周回が必要となるため、専用position-aware routerを利用する。

容量216 parcel-equivalentは実車積載kgから換算した値ではない。保存された設計はgroup需要中央値431を代表として`ceil(431/2)=216`を提案し、2026-09-30のcapacity freezeが採用を記録する。「代表groupを二つの容量予算で扱う」という方法論上の選択である。一次比較で固定し、108/432の感度候補と混ぜない。

固定割当はgroup内の道路対応座標を1m整数格子へ置き、Morton/Z順で並べ、需要合計が216を超えない連続next-fit区間に分割する。顧客を分割・他groupへ移動・後から詰め替えない。得られた182 group・465 rosterは容量上の編成であり、時間窓・SOC可行性や最適車両台数を保証しない。空間順序は割当用で、訪問順は後のsolverが選ぶ。

最終matched設計は、125顧客以上の26 parent・25 groupを選び、固定hash順から各3 replicateのnested部分集合n=3/4/5/25/99/125を作る。初期のPPS10顧客fixtureやEV41kWhの設計枝を、この最終20kWh評価へ混ぜない。親の需要・OD・時間窓を継承し、固定1車両、サービス102秒、時間窓幅7,200秒、出発0秒・帰還32,400秒を用いる。これらは研究条件であり実サービス時間の観測値ではない。102秒・時間窓幅の根拠の全来歴を今回独立に確定したとはしない。

### 0.9 同じ入力で古典計算と量子計算を比較する

**CONFIRMED：** 古典側は訪問順についてデポ発着を含む道路旅行時間を最小化し、容量・時間窓・全顧客一度訪問・帰還を独立に検査する。n≤5は完全列挙、n≥25は確定的ヒューリスティックとassignment LP下界である。**INFERRED：** 旅行時間を共通目的とし、その後で電力量を別評価する設計は、求解対象と物理的影響を分離するために有効であるが、この説明を当初の選定理由の逐語記録とはしない。

**CONFIRMED：** 量子を比較対象とした根拠は正式RQである。同じ物理入力・固定割当・制約をCandidate Cの補助変数なし位置PUBOへ写し、旅行時間と罰則を計算する。正式Protocol V2は理想Statevector、p=1、H初期状態、X mixer、COBYLA最大100評価×2,048 shots、独立最終4,096 shotsである。古典前処理の全順列可行性表を用い、最終標本の復号・独立検査後に最小旅行時間の経路を選ぶ。計算本体・bit順序・同点規則は[第3・4節](#4-quantum-model-and-protocol-v2)を参照する。量子はR0/R1の小規模比較だけであり、古典6規模すべてで量子を実行したわけではない。

### 0.10 訪問順をSUMOの走行軌跡へ接続する

**CONFIRMED：** 最適化結果のcustomer_orderを配送端点列へ対応させ、隣接端点ごとの道路legを専用`duarouter_loop`で得る。leg境界の重複edgeを処理して一本のrouteへ連結し、停車lane・endPos・duration=102秒・予定出発までのuntilを設定する。走行typeはdeliveryで、保存planはSUMO1.24の既存挙動、seed20260930、step/FCD周期1秒、単独車両・背景交通なしを指定する。初期計画の状態表示は作成時点の記録であり、後続trajectory freezeを完了の根拠とする。

native time-zero forkで実行し、時刻・速度・座標・lane/edge等を保存した。OD旅行時間は最適化の目的、SUMO観測所要時間は停車・待機・走行挙動を含む結果、DC入力は保存した1秒時刻・速度列である。lane上のpositionを累積走行距離としない。DC側の観測距離は区間速度×dtであり、tripinfoのrouteLengthとも別に記録する。背景交通や複数車両の相互作用を検証したとはしない。

R0の同一経路78件はClassical軌跡に結合し、R1は同一59・異経路5の取得経路に対して下流評価した。未取得経路の架空軌跡は生成しない。全量再現には専用router、native fork、端点・assignment・道路網・保存planが必要で、標準SUMOのみで同一実験になるとは保証しない。[第5節](#5-simulation-and-trajectories)に入出力契約を示す。

### 0.11 軌跡を固定してBattery条件と電力量を比較する

**CONFIRMED：** Path 2は容量20kWhを固定し、比エネルギー180/220/250Wh/kgをパック質量111.111111/90.909091/80kgへ写す。共通の車体等の残余質量を保持して車両質量へ反映するため、車体自体を軽量化した実験ではない。量子計算がこのBattery性能を実現したという結果でもない。

各経路の保存軌跡を全Battery条件で共通使用し、質量差によってSUMOを再走行させない。Controlled-DCは転がり・並進・回転・空気抵抗の仕事から正のwheel仕事を取り、効率0.90でBattery側DC Whへ換算する。平坦・回生なし、補機等は評価外である。18kWhからの累積消費による残量会計・負残量検出は行うが、SOC停止、充電、再計画は行わない。[第6節](#6-battery-and-controlled-dc-energy)の正式式・単位・freezeを優先する。

### 0.12 保存結果を対応させ、最終結果として固定する

**CONFIRMED：** 最終science実行はR0/R1各78件であるが、経路取得はR0が78/78、R1が64/78である。parent/replicateで対応した共通64ブロックについて両method・両scale・Battery条件・Crr条件を比較し、未取得14件を配送不能や電力量ゼロへ置換しない。

Battery削減率は各条件のB0 DC Whを分母にした百分率、DはClassical−Quantumの削減率差、TはD_R1−D_R0であり単位はppである。全4比較条件でT=0が59、非ゼロが5（正1・負4）であり、非ゼロは異経路5件に一致する。古典6規模は468論理・460異なる問題で、SUMO時刻診断の遅延136停止・116経路、帰還期限超過4経路を保持する。[正式報告](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)と[第7節](#7-analysis-and-frozen-results)が数値の正本・解釈境界への入口である。

**RECONSTRUCTED：** 以上は「地理・合成需要 → 制約付き経路 → 軌跡 → 質量感度」という接続を示す。ただし顧客数と同時に地理・時間窓・解法も変わり、経路取得subsetの偏りがある。量子優位、純粋な規模因果効果、物流全体の省エネルギーを実証したとはしない。最終freezeはこの限定された定量branchの保存結果を固定したもので、論文全体の完成を意味しない。

### 0.13 再実行できる部分と未確認部分

**CONFIRMED：** GitHubのNotebook01〜03は合成入力によるRouting・教材QAOA・Battery/Controlled-DCの計算例、04〜05は正式保存結果の参照である。これらを連続実行しても、原OSM・CityGML・統計から全量研究を再生成するものではない。道路Releaseの内容・hash検証、正式APIの軽量計算、保存集計の照合は公開範囲で行える。[Quickstart](#10-quickstart-and-dependencies)を利用する。

**UNKNOWN：** 原建物parquetの生成器・入力組合せ、合成世帯の全採用セル・RNG環境、道路補完と最終geometryまでの完全な再生成対応が未確認である。以下の台帳では「ファイルがある」「処理の内容が分かる」「当時その処理で当該出力を生成したことを確認できる」を分ける。Hayate資料は現行GitHubリンクとして提示しない。旧資料のGit管理済みという記述も当時の状態であり、現在の配布を意味しない。

### 工程の追跡表

文章を読んだ後の確認用である。**H**はHayateのみ、**P**は現在のGitHubで参照可能である。Hのコード名は取得後に実行可能であることを保証しない。下の根拠キーから原位置へ追跡できる。

|工程|取得元|入力|加工方法|実行コード|設定|出力|次工程|根拠|確認状態|
|---|---|---|---|---|---|---|---|---|---|
|地域・道路取得|Geofabrik／国交省N03|関東PBF・東京都行政界|固定日取得・complete_ways抽出|H `network/fetch_osm.py`|13111・固定BBOX|大田区抽出PBF|関係閉包|H1|CONFIRMED|
|道路属性・変換|OSM加工物|閉包OSM・blocker|値補完、netconvert、幾何修正|H `network/execute_three_tier_completion_streaming.py`、`network/repair_network_geometry_lengths.py`|SUMO1.24・保存規則|three_tier.net.xml|端点・OD|H2|RECONSTRUCTED／再生成UNKNOWN|
|建物候補|PLATEAU|2025大田区ZIP|用途・形状・町丁目対応|直接生成器未回復|使用全属性・中間設定未回復|候補CSV・中間parquet|世帯割当|H3・H4|CSV CONFIRMED／上流UNKNOWN|
|基準需要|国勢・人口・宅配便統計|人口メッシュ・全国量|面積按分・人口比例・最大剰余|H `demand/prepare_baseline_demand.py`|baseline_demand.yml|期待82,023/日|世帯期待値|H4・H5|CONFIRMED|
|世帯・頻度|国勢・住宅統計・ss521|世帯集計・条件付き週頻度|世帯展開・住宅型割当・相対強度|元世帯生成器未回復|384,353世帯・seed記録|lambda_h|Poisson需要|H4・H6|記録CONFIRMED／全生成UNKNOWN|
|需要と地点|合成世帯・建物|lambda・候補・割当|Poisson、一様割当、建物別集約|元生成器未回復|20260829／20260830|81,859量・39,956地点|道路対応|H4・H7|保存出力CONFIRMED|
|固定割当|研究需要|地点・需要q|Morton next-fit|H 固定割当protocol参照|Q216・182group|465 roster|nested部分問題|H8|CONFIRMED|
|経路計算|固定OD・割当|n=3/4/5/25/99/125|厳密／heuristic・PUBO/QAOA|P [Routing](../src/kmd_quantitative/routing/solver.py)、[Quantum](../src/kmd_quantitative/quantum/formal.py)|最終Protocol V2|訪問順・取得状態|SUMO|H9・P1|CONFIRMED|
|走行|保存道路網|取得訪問順・端点|leg接続・native走行|H generate.py・native fork|1秒・seed20260930|時刻・速度軌跡|DC入力|H10|CONFIRMED|
|Battery・DC|モデルfreeze|保存軌跡・B0/B1/B2|質量反映・DC積算|P [Battery](../src/kmd_quantitative/battery/mass.py)、[Energy](../src/kmd_quantitative/energy/controlled_dc.py)|20/18kWh・Crr二条件|DC Wh・残量|比較|P2|CONFIRMED|
|分析・凍結|保存結果|共通64・古典6規模|対応比較・保存値照合|P [Analysis読込み](../src/kmd_quantitative/analysis/result_io.py)、H 最終分析器|D・T・母数定義|最終freeze|解釈・再利用|P1・P3|CONFIRMED|

Hコードの`network/`・`demand/`は`05_src/traffic_simulation/`以下である。根拠資料は次である（Hは公開リンクではない）。

- **H1**：`03_data/metadata/acquisition/20260717_osm_ota_ward_acquisition.md`、`03_data/metadata/traffic_simulation_sources.csv`、`05_src/traffic_simulation/implementation_plan.md`。
- **H2**：`reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/`のrun_2／run_3記録、および上記repairコード。道路再生成の不足は第13節にも保持する。
- **H3**：`03_data/raw/external_statistics/plateau_ota_2025/`の保存ZIP・カタログとZIP内README。
- **H4**：`reproducibility/outputs/traffic_simulation/pipeline_authority_and_r24_capacity_plan/20260914_v1/CURRENT_PIPELINE_STAGES.csv`。工程名・式・採用値と未回復処理を区別する台帳である。
- **H5**：`reproducibility/config/traffic_simulation/baseline_demand.yml`、`05_src/traffic_simulation/demand/prepare_baseline_demand.py`。
- **H6**：`03_data/raw/traffic_simulation/demand_proxy/mlit_tokyo_metropolitan_goods_movement_survey_2024_20260823/manifest.json`、`03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/relative_parcel_propensity.csv`。
- **H7**：同`pipelines_v1/`の`pipeline_run_summary.json`、`stop_generation_run_summary.json`、`daily_requests.csv`、`household_building_assignment_scoped.csv`、`building_delivery_stops_scoped.csv`。初期と後段の状態を区別する。
- **H8**：`01_research_design/scenario_evaluation/baseline_capacity_fleet_assignment_20260930/`の`CAPACITY_FREEZE_MANIFEST.json`・`FIXED_ASSIGNMENT_PROTOCOL.md`。
- **H9**：`01_research_design/methodology/PREPARED_ROUTE_SCALE_EXPERIMENT_PROTOCOL.md`。事前計画の状態と後続結果を混同しない。
- **H10**：`01_research_design/scenario_evaluation/matched_classical_trajectories_20261007/GENERATION_PLAN.json`、同`generate.py`、共有`05_src/literature_analysis/generate_canonical_delivery_trajectories.py`。完了の追跡は[P1のauthority](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_FREEZE_AUTHORITY_CHAIN.csv)を用いる。
- **P1**：[最終結果freeze](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)。
- **P2**：[Controlled-DCモデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)。
- **P3**：[保存結果Index](../results/indexes/CANONICAL_RESULTS.json)。

## 1. Research Scope

必要な配送サービスを充足しながら、その実現に伴うエネルギー消費を低減することが上位の問題意識です。本配布物はEVラストマイル配送の限定された定量モデルと保存結果を扱います。

正式RQ（原文引用）：> 量子技術の進展は、電気自動車配送の経路計算とバッテリー性能の変化を通じて、ラストマイル配送の運用電力量にどのような影響を与えるか。

正式主仮説（原文引用）：

> 同一の充電を考慮した電気自動車配送問題において、古典計算を用いた場合と比較して、量子計算を用いた場合の方が、バッテリー性能の違いによる電気自動車配送の運用電力量の差が大きくなる。

正本はHayate保存の `01_research_design/RESEARCH_QUESTION_AND_HYPOTHESIS.md`（SHA256 `abe729fc925372782bc62c5a4f3e597c09b5c214acfd31c3ec912f3efb85cb33`）。上記はその文言の引用であり、新しいRQ・仮説ではありません。**充電を考慮した正式主仮説と、今回配布する無充電・固定軌跡の評価範囲は同一ではありません。主仮説の検証完了を主張しません。**

## 2. Model Architecture

需要/地点→固定割当・時間窓・OD→古典baseline→R0/R1共通Protocol V2→取得経路→保存SUMO軌跡→Battery質量条件・Controlled-DC→Method×Battery/古典6規模→正式freeze、という接続です。

|配置|役割|
|---|---|
|`src/kmd_quantitative/routing/`|訪問順の決定と独立した可行性検査|
|`quantum/`（同src配下）|Candidate C PUBO・正式標本選択・qualification処理|
|`simulation/`|保存CSV/CSV.gzの時刻・速度読込み|
|`battery/` / `energy/`|質量条件とControlled-DC|
|`analysis/`|保存結果の検査・読込み。科学的再集計ではない|
|`configs/` / `data/examples/`|設定参照と小規模合成入力|
|`results/indexes/`|正本結果の所在・hash・schema|
|`notebooks/` / `tests/` / `scripts/`|公開利用・軽量検証|
|`reproducibility/`|環境lock・配布Manifest・凍結原本対応|

通常の利用入口はsrc APIです。旧sourceを利用者のsys.pathへ追加しません。結果原本は01_research_designに保持します。需要生成・全量割当・OD・全量SUMOの実行入口を提供する配布ではありません。

## 3. Routing Model

[solver.py](../src/kmd_quantitative/routing/solver.py)と[independent.py](../src/kmd_quantitative/routing/independent.py)が正式入口です。固定顧客集合・固定割当の単一車両/単一巡回について道路旅行時間を最小化し、訪問・時間窓・容量・帰還期限を独立に確認します。道路グラフ上のedge経路と顧客訪問順は別です。

Notebook01はデポ＋3顧客の合成fixtureで厳密探索、訪問順・旅行時間・制約を確認し、時間窓を変えて再計算します。需要の単位parcel-equivalentをkgと混同しません。小規模の厳密解法と、保存済み大規模結果のヒューリスティック・LP下界を区別します（第7節）。経路取得と配送充足も別です。

## 4. Quantum Model and Protocol V2

### PUBO構築

[builder.py](../src/kmd_quantitative/quantum/builder.py)の `build_C(model,a)` は `(q, poly)` を返す。q=n²、polyはビットindexのtupleをキーとするDecimal係数。変数indexは `(customer-1)*n+position`。`route_code(order,n)` はindexを下位bitから数える整数で、Qiskit表示文字列の左端がbit0という意味ではない。両one-hot、道路旅行時間、可行性事前表の違反完全順列に対するn次罰則を元の関数ASTから計算する。罰則Aはmodelのpenalty_s。目的は電力量でなく道路旅行時間。

入力aはnodes/travel/distance/ready/due/service/demand等の正式配列契約、modelはn/penalty_s/capacity_ok/permutations等の完全な事前情報。欠落した順列表を補ったり、任意の配送問題向けに制約を一般化するAPIではない。

### 復号と可行性

[formal.py](../src/kmd_quantitative/quantum/formal.py)が正式処理へのadapter。

- `feasible_route_table(model,a)`：事前表でcapacity/TIME_WINDOW/RETURN_HORIZONを満たす順列をroutingの独立validatorで検査し、code→経路表と事後評価用の厳密最小旅行時間を返す。表が空なら元実装と同じAssertionError。
- `parse_sample_counts(raw_counts,shots)`：Qiskit形式の文字列キーを整数へ変換し総shotsを検査。空白区切りを除去する元処理。非binary文字はValueError、shots不一致はProtocolFailure。
- `evaluate_final_counts(model,a,counts)`：整数codeを可行表へ照合し、最終経路を再度独立validatorで検査して返す。返り値は `final_feasible_count`, `sampled_feasible_routes`, `best_final_feasible_route`。

このAPIは信頼されたsampler契約の入力用。幅・負数・bool等に対する包括的入力防御を元コードに追加したものではない。未知の整数codeは除外される。正しい可行問題に可行標本がない場合は空経路一覧・Noneであり、可行問題自体がない場合とは異なる。`python -O` は使わない（正式validatorはassertを利用）。

### 最終経路選択

`select_final_route(routes)` は独立検査済みの正式recordを前提とする低水準API。道路旅行時間のDecimal値、整数bitstringの昇順でminを選ぶ。頻度・最適フラグは同点の基準ではない。空一覧はNone。正式標本の復号も必要ならevaluate_final_countsを使う。

parameter incumbentの選択は別規則：域内・有限評価から可行標本数最大→平均エネルギー最小→評価index最小、可行標本ゼロなら平均エネルギー→index。バイト一致のquantum/protocol_v2/protocol.pyに保持する。最終4096標本のみが経路取得のauthority。probe標本を混ぜない。

### 古典・量子の分担

入力構築、全順列可行性、PUBO、COBYLA、復号・独立検証・経路選択は古典処理。正式QAOAは理想StatevectorSamplerであり実機ではない。p=1、H初期状態、X mixer、最大100目的評価・各2048shots、独立seedの最終4096shots。詳細条件は凍結protocol/planを優先する。

静的回路生成元は static_reduced_circuit_resources.py（Hayate保存参照: `05_src/traffic_simulation/matched_quantum_qualification/static_reduced_circuit_resources.py`、公開ツリー非同梱） のbinary_poly_to_z/make_circuit。回路はAで正規化したpolyをx=(1−Z)/2へ変換し、RZ/RZZ/CXパリティ列とRx(2β)を構成する。scienceは保存QPYを読み、目的評価のmean_energy_sには非正規化PUBOを使用する。この違いを同一視しない。生成scriptはトップレベルに出力処理があり、importしない。今回回路生成・実験は行っていない。

### 利用例

repo rootから `PYTHONPATH=src python -B`、またはJupyterでrepoのsrcをsys.pathへ加える。既存Notebook環境を利用する。

```python
from kmd_quantitative.quantum import builder, formal
# aとmodelは02 Notebookまたは正式入力契約に従って用意する。
q, poly = builder.build_C(model, a)
counts = formal.parse_sample_counts(raw_counts, shots)
result = formal.evaluate_final_counts(model, a, counts)
print(result['best_final_feasible_route'])  # Noneも正当な結果
```

例のa/model/raw_countsは自動取得されない。環境と検証は第10・11節を参照。

### qualificationとの差

qualification_builder.pyはprefix-AND補助変数を含むQUBOで、正式Candidate Cは補助変数なしのPUBO。前者の可行性・罰則metadataは最終V2にも利用される。decoder.pyはbit配列の幅・binary・one-hot・物理条件・ancillaを独立検査する。正式V2はこのdecoderを呼ばず可行表とvalidatorを使う。両者の入力・エラー・出力形式も異なる。

### Notebookとの差

02の回路は未正規化PUBOのdense教材回路、既定64shots、最大6評価の任意最適化は未検証。正式QPYの正規化、角度、seed、2048/4096shotsの再現ではない。PUBOと最終標本判定のみ正式APIへ統一した。既定の最終可行0/64はNOT_ACQUIREDのまま。教材結果を正式R0/R1結果に置き換えない。

## 5. Simulation and Trajectories

### Routingとの接続

routingは顧客の訪問順を決定する。SUMOの道路edge列とは別物。matched Classicalの `generate.py:prepare` は保存resultのcustomer_orderをroute_sequenceへ対応付け、端点ごとのtripを作成し、position-aware duarouter_loopの保存edge経路を用いる。共有 `generate_canonical_delivery_trajectories.py:build` が隣接legの重複境界edgeを連結し、stopのlane/endPos/duration/untilを設定する。

Quantumは最終取得経路のみを扱う。最終R0 commonは78件が同一経路で保存Classical軌跡へ結合、R1は同一59件・異経路5件という既存系譜を維持する。未取得経路を新規に補完しない。今回これらの生成・再結合は実行していない。

### 道路・OD

道路networkは凍結GENERATION_PLAN.jsonのnetwork/sha256で指定。FROZEN_ENDPOINTS.parquetからnode_id/role別のedge/lane/positionをENDPOINT_READBACKへ写す。OD旅行時間はrouting目的、SUMO観測走行時間は別指標。道路グラフ読込みはnative router/SUMO側で、Pythonの汎用road APIを今回新設しない。

### Simulation入力と実行

固定訪問順、端点、道路network、leg経路、車両type、service stop条件が必要。既存planはstep/FCD周期1秒、seed=20260930、独立単一車両・背景交通なし。matched生成は `canonical_sumo_fork.cpp` のnative time-zero forkを利用する。標準SUMOバイナリだけで同じ実行環境が成立すると仮定しない。

### Trajectory出力

canonical CSVの保存列はroute_id、vehicle_id、timestamp_s、speed_m_s、x_m、y_m、lane_id、edge_id、position_m、angle_deg、slope_deg。matched版はphysical_instance_idとcanonical_trajectory_idも含む。x/y/positionはm、角度・勾配はdegree。position_mはlane上の位置で、累積走行距離ではない。

時刻はSUMO simulation時刻s、速度m/s。delta_time列・累積distance列・departure_time/arrival_time列はこのCSVにない。dtは隣接時刻差、出発/到着・native routeLengthはtripinfo/manifestの別記録。FCD観測はdeparture, arrival)で、DC評価は最初〜最後の観測点間だけ。最後の観測から到着eventまでを補間しない。

### Controlled-DCへの受渡し

```python
from kmd_quantitative.simulation.trajectory_io import read_dc_input
# repo rootからPYTHONPATH=src、またはsrcをsys.pathへ追加
# manifest_rowとhashは正式manifestから別途取得する。
t, speed = read_dc_input(path, expected_sha256=hash_value, metadata=manifest_row)
# 既存run_full_controlled_dc.pyのevaluateへ、この2配列をそのまま渡す。
```

読込みは既存 `apply_r0_method_battery.py` のdf/t/speed代入3文をSHA256確認後にASTで実行する。このR0 sourceは最終R1/R0 commonの現役依存でもある。トップレベルの監査・出力・計算loopは実行しない。エネルギー式をadapterへ移さない。

新APIの入力guardは長さ2以上の同長1次元・有限数値・非負速度・厳密1秒刻みを要求する。不正入力はValueError等で拒否し、並べ替え・補間・欠損補充しない。有効配列の数値・dtype・行順は元pandas読込みと一致。optional hashは圧縮file bytes、optional metadataはsample_count/integration_interval_count/first_sample_s/last_sample_sを確認する。これらのguardはAPI境界の検査であり、配送制約判定の変更ではない。

Controlled-DCは右端速度×dtで区間距離を扱い、Whを返す。CSVのposition差やOD距離へ置換しない。元DCの非1秒刻みassertと、新APIの早期ValueErrorは例外型が異なる。全フィールド・SUMO完了・時間窓をこの2列loaderだけで検証したとは扱わない。

保存軌跡の読込みにSUMO本体は不要です。全量生成にはnative SUMO1.24・専用duarouter_loop・canonical_sumo_fork・道路網・端点・固定assignment/result等が必要で、標準SUMOだけで同条件になるとは仮定しません。

## 6. Battery and Controlled-DC Energy

### Path 2の対象

容量20 kWhを固定し、パック比エネルギー180/220/250 Wh/kgによるパック質量の変化を車両質量へ反映する。容量増加や量子材料計算を扱わない。同一の保存走行軌跡に異なる質量条件を与える感度評価であり、実電池性能の達成・実車検証ではない。

### Battery入力・出力

[mass.py](../src/kmd_quantitative/battery/mass.py) は `official_mass_stages()` と `mass_at_specific_energy(selected)` を提供する。前者は元stage loopの全mass record、後者は既存Notebookと同じCUSTOM感度条件。入力selectedはWh/kg、計算容量は20 kWh固定。

[scenarios.py](../src/kmd_quantitative/battery/scenarios.py) の `load_model()` はhash固定の [モデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json) を新しいdictとして読む。`stage_inputs()` はEnergyに渡すB0/B1/B2の凍結入力。呼出しごとに読み直すため返却dictの編集はfreezeを書き換えない。編集した条件は正式条件ではない。

### 比エネルギーとパック質量

原sourceの関係は `m_pack = 20000 / e_pack`。B0/B1/B2のパック質量は約111.111111 / 90.909091 / 80 kg。新APIへ数式をコピーせず、review_pack_specific_energy.pyのcalcとstage loop、またはcustom用の元3文をASTとして呼ぶ。レビューsourceのmain全体・文献処理・表書込みは起動しない。stage選定用の相関式を今回変更・更新していない。

### 車両質量

B0車両基準1100 kgからB0パック質量を差し引いた共通残余に各パック質量を加える。車両質量は1100 / 1079.79797979798 / 1068.888888888889 kg。Energyに渡すrunning_mass_kgは共通運転者55 kgを含む1155 / 1134.79797979798 / 1123.888888888889 kg。積載・追加設備は0 kg。パック軽量化の結果として車両質量が変わる。

### Controlled-DC入力

[controlled_dc.py](../src/kmd_quantitative/energy/controlled_dc.py) の `evaluate(t,v,model,pressure,stage)` は元run_full_controlled_dc.pyの関数そのものを公開する。tは秒、vはm/s、1秒間隔の同長numpy配列、pressureは既存Crr条件p_bar、stageはrunning_mass_kg等の凍結dict。配列順を変更しない。

CSV入力はSimulation API `read_dc_input` で検査する。Energy低水準APIのassert/例外は元関数と同一で、一般的入力validatorではない。一部の異長配列はNumPy broadcastで計算され得るため、直接呼ぶ側も契約を守る。Simulationの等長/有限値/1秒guardを通す。`python -O` は使わない。欠損補充・端点補間・並べ替えはしない。

### 出力と18 kWh

返り値は `(out, arrays)`。outの主項目はtraction_DC_Wh/net_DC_Wh/cumulative_DC_Wh、observed_interval_count/observed_distance_m、成分Wh、Wh_per_observed_km、initial/minimum/terminal_stock_Wh、stock_integrity、boundary等。arraysはroll/translational/rotational/aero/wheel/dcの区間Wh配列（N−1要素）。負仕事は符号付き成分と非負の負側magnitudeを区別する。

**18 kWhは実際の残量会計に使われる。** 元核は `18000 - np.cumsum(dc)` を計算し、負残量をSTOCK_INTEGRITY_FAILとして記録する。18000は核内固定値であり、返却modelのstock_accountingだけを編集して可変SOCモデルにできるわけではない。残量で走行を打ち切らず、clampせず、充電やSOC依存効率を計算しない。

### 物理モデル・評価境界

元freeze/実装では右端速度×dtで区間距離、隣接速度二乗差で並進・回転運動エネルギーを扱う（加速度配列は返さない）。転がり抵抗係数は `0.005+(0.01+0.0095*(3.6*v/100)^2)/p_bar`。p_bar=4.5/2.6はCrrの上下境界で、実際の圧力変更実験や信頼区間ではない。

g=9.80665 m/s²、rho=1.2041 kg/m³、CdA=1.175 m²、回転等価質量61 kgは段階共通。roll+translation+rotation+aeroの仕事を3600でJ→Whへ変換し、合計wheelの正側を一定効率0.90で除してDC電力量とする。成分ごとに正側を先に切り取る処理ではない。平坦、回生なし、補機対象外、turn loss対象外。負wheel仕事を充電として扱わない。

内部会計のnearは相対1e-11・絶対1e-7 Wh。新APIの数値回帰は元関数との完全一致。`scalar_check` も元関数を公開する。

### Simulation接続・実行例

既存Notebook環境でrepo rootから `PYTHONPATH=src python -B`：

```python
from pathlib import Path
from kmd_quantitative.simulation.trajectory_io import read_dc_input
from kmd_quantitative.battery.scenarios import load_model, stage_inputs
from kmd_quantitative.energy.controlled_dc import evaluate

t, speed = read_dc_input(Path('notebooks/fixtures/speed.csv'))
model = load_model()
for stage in stage_inputs():
    out, arrays = evaluate(t, speed, model, 4.5, stage)
    print(stage['stage_id'], out['net_DC_Wh'])
```

このCSVは人工4標本で、SUMOの科学結果ではない。正式保存軌跡を使う場合はmanifestと圧縮ファイルhashをread_dc_inputへ渡す。実軌跡1,319標本も過去の移行検証で6条件の回帰に使用したが、配布fixtureに複製していない。

## 7. Analysis and Frozen Results

### 対象と正式な実装

`src/kmd_quantitative/analysis/` は保存結果の読込み専用APIです。既存の分析ソース・表・freezeは原位置で保持します。物理移動、科学的集計の再実装、新規実験、欠損補完は行いません。

- [method_battery.py](../src/kmd_quantitative/analysis/method_battery.py)：最終共通Protocol R0/R1。
- [scale_analysis.py](../src/kmd_quantitative/analysis/scale_analysis.py)：古典6規模の保存表と診断。
- [result_io.py](../src/kmd_quantitative/analysis/result_io.py)：13の保存ファイルについてSHA256・サイズ・列/キー・行数を検査。返却値は新しいdict/DataFrameです。

統合分析ソース（Hayate保存参照: `01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/analyze_frozen_results.py`、公開ツリー非同梱）と古典Scale×Battery分析ソース（Hayate保存参照: `05_src/literature_analysis/analyze_classical_scale_battery.py`、公開ツリー非同梱）にはトップレベルの検証・集計・書込みがあります。APIはこれらをimportしません。数式をAPIに複製せず、生成済み結果を読みます。

### Method×Batteryの比較構造

正式R0は3顧客、R1は4顧客。各78実験条件で最終標本からR0は78経路、R1は64経路を取得しました。R1の14未取得は配送不可能を意味しません。歴史的R0の40/78取得結果とは別です。

`parent_id, replicate_id` で対応する計画78ブロックから、両側に経路がある64を使用します。26 parent・25 groupに属し、3 subset replicateは独立した量子反復や独立地理標本ではありません。R0/R1で同じ顧客課題でもありません。未取得14の値をゼロにせず、`population()`は除外理由と空欄を残します。

`contrasts()`は64×2 Crr×2比較＝256行。`energies()`は64×2 Crr×3 Battery＝384行。全R0で同一経路、R1で59同一・5異経路。4条件それぞれTゼロ59・非ゼロ5（正1・負4）で、4条件を256独立標本にまとめません。

### 古典6規模の比較構造

n=3,4,5,25,99,125。各78論理インスタンス、合計468論理に対して460実体です。R5は78論理が70実体を参照し、他の規模は各78実体。重複対応を独立サンプルとして数えません。

n≤5はEXHAUSTIVE_PERMUTATIONS / PROVED_OPTIMAL。n≥25はDETERMINISTIC_HEURISTIC_3_SWEEPS_PLUS_HIGHS_ASSIGNMENT_LP / BOUNDED_GAP_NOT_GLOBAL_OPTIMUM。顧客構成、地理、時間窓、解法が異なるため、顧客数単独の因果効果ではありません。大規模側の量子計算結果はありません。

`conditions()`はデポDEP_006、容量216 parcel-equivalent（kgではない）、静的departure=0 s、return deadline=32400 s、TW幅7200 s、顧客service=102 s等の保存条件を返します。実業務の条件を実測したことは意味しません。

### 評価指標

正式freezeの定義：

- Battery saving (%) = `100*(E_B0-E_Bk)/E_B0`。分母は各scale・method・経路・Crr条件のB0 DC Wh。
- D = Classical saving − Quantum saving。
- T = D_R1 − D_R0。主表示単位はpercentage points（pp）。元の正式仮説のkWh応答差と同一ではありません。
- `_Wh`のsaving contrastも保存されていますが、ppと混ぜません。
- 直接の電力量差はQuantum − Classical。saving Dと符号の定義が異なります。

`summary()`は最終freezeの4条件の保存集計です。母数64、中央値0、標準偏差はddof=1。`mean_decimal`は元のDecimal文字列を保持します。T=0は計算性能の同等性、量子優位性、統計的有意差を示しません。

### 古典側の集計単位

`battery_summary()`は24行、各scale×Crr×B1/B2について78論理の削減率分布（percent）。Scale×Battery interactionの集計そのものではありません。

`interaction_summary()`は既存112行を返します。40行のEQUAL_PARENT_MEAN_CONTRASTはブロック内の規模差→parent内3replicate平均→26parent等重みの集計（pp）です。他の72行はREPLICATE_LOGICAL_REDUCTION、UNIQUE_PHYSICAL_REDUCTION、EQUAL_PARENT_REDUCTION（percent）。`summary_type`, `unit`, `count`, `planned_count`, `algorithm_stratum` を保ち、異なる推定対象を混ぜません。B2が元分析の主対象、B1は副対象です。

### 入力ファイル

`result_io.artifacts()`がパス・SHA256・サイズ・schema・保存行数の一覧を返します。ファイルは既存パスで配布する必要があります。主な所在：

| API | 保存入力 |
|---|---|
| freeze / summary | `final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json`, `FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv` |
| population / contrasts / energies | `matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv`, `SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv`, `DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv` |
| routes / battery_summary / interaction_summary | `01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv`, `MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv`, `CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv` |
| methods / conditions / service_diagnostics | `quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv`, `SCALE_INSTANCE_COMPARISON.csv`, `LOGISTICS_SERVICE_SCOPE.csv` |
| battery_conditions / trajectory_validation | `01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`, `MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json` |

上表のディレクトリ短縮名は `01_research_design/scenario_evaluation/` 配下です。既存結果をコピー・加工した新しいfreezeは作成しません。

### 出力と検査

JSONはdict、CSVは既存Notebookと同じ `pandas.read_csv` のDataFrameを返します。CSVで `raw=True` を指定すると文字列dictのリストになり、Decimalの原文・空欄・行順を保持します。DataFrame表示では空欄がNaNへ変換されますが、ゼロ補完・行除外・再集計はしません。APIはファイル出力を行いません。

欠損はFileNotFoundError、改変はValueError、未登録artifact keyはKeyError。hash確認とschema確認はバイト整合性検査で、モデルの科学的妥当性を新たに証明するものではありません。証拠内の絶対パスや外部ファイル参照は来歴文字列で、自動追跡しません。`root=`は同じ相対配置を復元したディレクトリに指定でき、hashを回避する機能ではありません。

### Authority・処理区分

FROZEN_RESULTは元の保存値、NOTEBOOK_PRESENTATIONはその表示、SMOKE_TESTはAPI接続検査です。今回はDETERMINISTIC_REAGGREGATIONを公開APIに追加していません。テスト内のDecimal恒等式・件数照合は保存値の整合性確認に限定し、新しい結果や検定を保存しません。

release manifest（Hayate保存参照: `reproducibility/release/RELEASE_MANIFEST.json`、公開ツリー非同梱）と正式source/freezeは変更しません。Phase6の入力hash catalogは再利用の契約であり、過去のauthorityを置換しません。古典側はroute execution、Battery validation、後続Scale×Battery分析の保存記録を区別します。先行validationのNOT_YET_EXECUTEDを後続分析未実施と誤読しません。

### 配送充足の境界

静的可行性、SUMO走行完了、SUMO観測時刻の診断、現実の全需要充足を区別します。古典matched460はL2 COMPLETEでも、L3遅延はR4が73停止/61経路、R5が63停止/55経路、合計136停止/116経路。帰還期限超過はR4=1、R5=3の計4経路です。全域465経路の別診断と混同しません。

APIはこれらを除外しません。native VRPTW全条件再検証はFalse、実業務充足は未検証。電力量を計算できることと配送条件を満たすことは別です。未配送による低消費を省エネルギー達成としません。

### エネルギー境界

20 kWh容量固定、180/220/250 Wh/kgによるパック・車両質量条件、同一軌跡内の比較です。18 kWhは既存残量会計条件。2 Crr境界は圧力変更実験・信頼区間ではありません。DC Whは保存観測区間のみ、平坦・回生なし・補機対象外・エネルギー側積載0 kg・効率一定。充電・計算・通信・設備・製造を含む社会全体のエネルギーではありません。

入口は[正式結果Index](../results/indexes/CANONICAL_RESULTS.json)と[凍結研究報告](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)です。Indexは新しいfreezeではなく、13保存ファイルを参照します。`from kmd_quantitative.analysis import method_battery as mb, scale_analysis as scale` の後、`mb.summary()`、`scale.service_diagnostics()`等を利用できます。

## 8. Data and Configuration

[CANONICAL_CONFIG_INDEX.csv](../configs/CANONICAL_CONFIG_INDEX.csv)は19の役割別参照です。需要・固定割当・OD・routing・PUBO/QAOA・SUMO・Battery/DC・統合分析・古典6規模・検証を対象とします。同じfreezeを複数の役割が参照します。設定だけでなく、入力bindingや実験計画も区別して記録しています。

正式設定は元位置に保持します。Indexのsource_path、SHA256、サイズ、using_implementation、パラメータ参照、既定値抜粋、seed方針、外部入力を確認してください。物理移動・設定値の変更・正式設定のコピーは行っていません。source freezeとauthority chainは既存のままです。Index自身は新しいfreezeではありません。

[examples/NOTEBOOK_INPUTS.json](../configs/examples/NOTEBOOK_INPUTS.json)は小規模Notebookの**入力パスを指定する設定例**です。正式実験設定ではなく、QAOAの回路・角度・seed・shots・最適化条件を上書きしません。Notebook02の既定値はgamma=0.001、beta=0.2、shots=64、seed=20261009、DO_OPTIMIZE=False。正式Protocol V2のp=1・最終4096標本等とは別です。

Notebook adapterはこの設定からdata/examplesのfixtureを選び、登録hashを検査します。入力が欠損・改変されていれば停止し、旧fixtureへ自動フォールバックしません。初期入力の値を変える場合はNotebookのメモリ上の条件変更例を使ってください。新しい入力ファイルを登録する場合は独立したDEMONSTRATIONとして来歴・hashを更新し、正式freezeを書き換えないでください。




[examples/PROVENANCE.json](../data/examples/PROVENANCE.json)に、既存fixtureからの3つのバイト一致コピーと元SHA256を記録しました。実験データの抽出や再生成はしていません。旧notebooks/fixturesは既存テストの互換参照として保持します。配布コピーを独立に変更せず、一致検査を継続します。

|配布入力|用途・単位|種別|
|---|---|---|
|[three_customers.json](../data/examples/three_customers.json)|デポとA/B/C、4×4 travel秒・distance m、時間窓/サービス秒、需要parcel-equivalent、期待40秒の巡回|既存の合成routing/PUBO fixture。実座標・実道路・現実の配送地点を含まない|
|[speed.csv](../data/examples/speed.csv)|timestamp_s、speed_m_s、4標本の0〜3秒・10m/s|合成軌跡。保存SUMO実験の実測軌跡ではない|
|[speed.json](../data/examples/speed.json)|既存の同じ小規模軌跡・期待電力量等|Controlled-DC検証用の既存証拠|

Battery条件は[正式モデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)を参照し、別の条件表を複製しません。容量20 kWh、初期利用可能18 kWh、比エネルギー180/220/250 Wh/kg。18 kWhは残量会計・負残量判定に使用し、SOCによる停止・充電・再計画は実装していません。

Notebook01/02は共通のrouting fixture、03は速度CSVをconfigs/examples経由で取得します。APIは既存の科学処理を呼びます。欠損時の代替結果はありません。

## 9. Notebook Guide

各冊は独立kernelで上からRun All。順序は00→01→02→03→04→05です。

|Notebook|用途・変更できる条件|
|---|---|
|[00_start_here](../notebooks/00_start_here.ipynb)|依存とhash・環境の確認|
|[01_classical_routing](../notebooks/01_classical_routing.ipynb)|3顧客の正式古典solver、時間窓変更|
|[02_pubo_qaoa](../notebooks/02_pubo_qaoa.ipynb)|正式PUBO/判定と教材回路、γ/β/seed/shots|
|[03_battery_energy](../notebooks/03_battery_energy.ipynb)|質量・保存軌跡・DC、比エネルギー/速度係数|
|[04_quantitative_results](../notebooks/04_quantitative_results.ipynb)|R0/R1・Method×Battery保存結果と表示フィルタ|
|[05_scale_analysis](../notebooks/05_scale_analysis.ipynb)|古典6規模保存結果と表示フィルタ|

01〜03は小規模計算、04〜05は保存結果表示で、新しい科学結果ではありません。fixtureは人工データ、各assertは初期条件の基準値を含みます。任意の問題規模に対応する汎用solver UIではありません。02の既定値はgamma=0.001、beta=0.2、shots=64、seed=20261009、DO_OPTIMIZE=False。任意COBYLA最大6評価は通常無効で自動検証外。既定0/64・NOT_ACQUIREDを隠したり正式科学結果に置き換えたりしません。

adapters.pyは[依存台帳](../notebooks/fixtures/dependencies.json)の38依存をhash照合し、正式APIへ接続します。数理処理をNotebookへ重複実装しません。通常の検証はNotebookを保存し直しません。`notebooks/test_notebooks.py --save-outputs` は表示出力を保存するため、比較検証では一時配置のみで使います。`--report NEW_PATH.json` は新規報告先を指定します。

## 10. Quickstart and Dependencies

Python3.12.3/Linuxで新規venvへのインストールと公開cloneの実行を検証済みです。今回の文書統合では既存の検証用venvを使います。他OS/Python・Colabは未検証です。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/environment/requirements-quickstart.lock.txt
.venv/bin/python -m pip check
.venv/bin/python -B scripts/verify_quickstart.py
```

リポジトリ直下で実行します。lockは実際に解決したランタイム依存版で、全OSのwheelハッシュロックではありません。[直接依存](../notebooks/requirements.txt)と[固定版](../reproducibility/environment/requirements-quickstart.lock.txt)を参照してください。UIは不要です。既存Jupyter UIから使うkernel登録例は `.venv/bin/python -m ipykernel install --user --name kmd-notebooks`（UI操作自体は未検証）。通常のPython利用はrepo rootで `PYTHONPATH=src .venv/bin/python -B`。wheelとしてのpipインストールを提供したものではありません。


|範囲|必要なもの|今回の扱い|
|---|---|---|
|CORE|Python3.12.3、numpy2.3.1、pandas2.2.3、scipy1.16.0、highspy1.15.1、正式source・小規模fixture・保存集計|軽量API検証。凍結ソースの必要部分への接続を含む|
|NOTEBOOK|CORE、qiskit2.1.1、nbformat5.10.4、nbclient0.10.2、ipykernel6.30.1と推移依存|6冊の既定セル。教材回路のためQiskitはquickstartに含む|
|QUANTUM_OPTIONAL|正式Protocolの専用環境、worker/QPY等|本番最適化・実機・高負荷シミュレーションは未復元|
|SUMO_OPTIONAL|SUMO/native fork、専用router、道路ネットワーク、全OD、worker設定|保存軌跡APIはSUMO不要。全量運行は対象外|
|FULL_RESEARCH|元のanalysis/qgpu/native環境、大容量入力と全量証拠|既存requirements-analysis.txtとRelease Manifestを保持。quickstartとの同一環境化はしない|

[quickstart lock](../reproducibility/environment/requirements-quickstart.lock.txt)はNOTEBOOKまでの実測解決版です。既存analysis定義（Hayate保存参照: `reproducibility/environment/requirements-analysis.txt`、公開ツリー非同梱）のnumpy/scipy等とは用途が異なるため上書きしません。これは正式研究環境の完全復元ではありません。OS、ネイティブライブラリ、配布物の永続保存は別途必要です。

外部ライブラリはpipで取得し、ソースをこのリポジトリへ再配布しません。インストール成功はライセンス互換性・自作コードの公開権限確認とは別です。

## 11. Reproducibility and Verification

### 実行用コピーの方針


[対応表](../reproducibility/release/FROZEN_RUNTIME_SOURCES.json) に凍結原本・実行用配置・SHA256・読込み範囲を記録しています。5ファイルをバイト一致で配置し、科学的な計算文を変更していません。旧原本は研究当時の証拠として元位置に保持します。コピーを別の現役実装として改良・管理しません。変更が必要になった場合は、原本のfreezeを更新せず、別の科学的変更として検討してください。

| 機能 | 実行用配置（src/kmd_quantitative/以下） | 接続方法 |
|---|---|---|
| Candidate Cと正式標本判定 | quantum/protocol_v2/science.py | builder/formalが既存の必要な関数・文だけをASTで読み込む |
| NotebookのProtocol定義 | quantum/protocol_v2/protocol.py | 定義のみ読込み |
| Battery質量 | battery/frozen_sources/review_pack_specific_energy.py | massが既存の計算文のみをASTで読み込む |
| Controlled-DC | energy/frozen_sources/run_full_controlled_dc.py | controlled_dcがevaluate/scalar_check/nearを公開 |
| 保存軌跡読込み | simulation/frozen_sources/apply_r0_method_battery.py | trajectory_ioが読込みの3文だけをASTで読み込む |

### 実行してはいけない入口

コピーしたファイル全体を汎用CLIとして起動しないでください。`__file__` から構築される全量実験用パスは新配置に移植していません。特に旧R0軌跡sourceにはトップレベルの科学計算・書込みがあり、直接importしてはいけません。公開adapterが選ぶ処理のみが検証対象です。Controlled-DCのmain/preflight、scienceの実験worker・最適化は呼び出しません。

### 原位置に残すもの

旧science・R1 worker・Battery/Controlled-DC原本は、source freezeと研究結果の追跡用に保持します。R1 workerは回帰テストがAST比較の証拠として読むため配布集合に残しますが、通常のAPIとNotebookはworkerを起動しません。全量QAOA/SUMO workerの旧パス依存は今回の移植対象外です。

`01_research_design/` のモデルfreezeと正式結果は、設定・保存結果の読込み依存として残します。これは旧配置の計算コード実行とは異なります。結果の入口は [保存結果の入口](#7-analysis-and-frozen-results) と結果Indexです。元のfreezeやauthority chainのパス・値・hashは変更しません。



### 軽量検証と保全

第10節の1コマンドで既存45 API/契約テスト＋原本一致1テスト、Notebook6冊を実行します。`-O`はassertを無効化するため禁止。全量SUMO/OD、正式QAOA最適化、旧互換リンクの検証は含めません。CIも同じ入口を使います。

公開基準commit 2efe70f854c4871547db6fac9c169db8cd06e706では実clone検証・GitHub Actions成功の記録があります。[基準CI](https://github.com/tkm-sano/kmd-analysis/actions/runs/37904061464)。その後の構造再編はcommit `84bb501`で公開済みであり、研究基準文書追加commit `1376dc5`でも実clone・46テスト・Notebook6冊および[リモートCI成功](https://github.com/tkm-sano/kmd-analysis/actions/runs/37911349043)を確認しています。この履歴は全量科学実験の再現を意味しません。

Distribution Manifestは配布hashを管理し、科学的Release Manifestとは別です。歴史的rights/publicationフィールドは準備時点の記録であり、後続の公開実施記録と区別してください。元のsource freeze・authority・結果は変更しません。Notebook01〜05は基準出力との完全一致を検査し、00の依存表示差を別扱いにします。

## 12. GitHub and Hayate Responsibilities

GitHubは正式API・小規模入力・Notebook・主要集計・検証の利用場所、Hayateは全量科学データ・過去の研究環境と監査の保存場所です。元13,360件のRelease Manifest、全OD、全軌跡、中間成果、native fork/専用router環境、全量worker/QPY/instance/validator等はGitHubにすべて含まれません。小規模利用の成功を全量科学実験の再現成功としません。

Hayate原位置で保持することと、独立した永続バックアップを持つことは別です。研究保存台帳・生成記録はdocs/audits等にあり、公開文書の統合対象外です。Git追跡解除は物理削除ではなく、現行treeから外れても過去のGit履歴には残ります。

全量研究の設定・入力・source対応はHayateのRELEASE_MANIFEST.jsonとRELEASE_ARTIFACT_REGISTER.csv、公開側のconfigs/CANONICAL_CONFIG_INDEX.csvに記録されています。後者に辿れることは、未配布の入力を取得したことを意味しません。

## 13. Data Attribution and Licensing

### ライセンス適用範囲


既存の[LICENSE](../LICENSE)はApache License, Version 2.0（SPDX: `Apache-2.0`）です。TAKUMA SANOが公開・ライセンス適用権限を持つ**自作コードおよびNotebookの自作部分**には、既に承認された方針に基づき同ライセンスを適用しています。これは将来の適用候補ではなく、この範囲への適用宣言です。LICENSE本文は変更していません。

配布Manifestのlicense_scopeは元の適用記録です。ただし全内容について単独著作・権利処理完了を認定したものではありません。共同研究・所属機関・第三者由来の部分、Notebookの保存研究結果や外部データはこの宣言から除外し、該当権利者の承認・元の利用条件を別途確認します。今回の公開判断を、第三者由来部分の独立した権利確認完了や新たな許諾とは扱いません。

研究結果・fixture・文書へApache-2.0を一括適用しません。第三者ライブラリは各自のライセンスに従います。適用対象の利用・改変・再配布では、LICENSEの提供、改変表示、必要な著作権・帰属表示と該当NOTICEの保持等、LICENSEの条件に従ってください。元のLICENSE付録の`[yyyy]`/`[name of copyright owner]`は記入例であり、全成果物の権利者の認定ではありません。

既存の公開Git履歴もこの宣言によって新たに権利処理済みにはなりません。公開判断の前提と独立検証の限界は、下記のデータRelease説明にも記録しています。


### 外部入力の帰属と加工


以下は保存済み科学結果の生成に使われた研究入力です。上記の合成3顧客・4標本fixtureとは別です。元のPBF、CityGML、統計表、全OD、道路網、全走行軌跡はコード配布に同梱していません。

|提供元・出典|確認できた版・取得記録|研究上の加工・用途|
|---|---|---|
|© OpenStreetMap contributors、[OSM](https://www.openstreetmap.org/copyright)、[Geofabrik関東](https://download.geofabrik.de/asia/japan/kanto.html)|`kanto-260716.osm.pbf`、2026-07-16版、台帳取得2026-07-17|地域抽出、道路属性・形状補正、SUMO道路網、OD・経路・走行評価へ利用。道路データベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)|
|国土交通省Project PLATEAU、[3D都市モデル（大田区）（2025年度）](https://www.geospatial.jp/ckan/dataset/plateau-13111-ota-ku-2025)|保存された配布元メタデータはCityGML v5、`13111_ota-ku_pref_2025_citygml_1_op.zip`。2026-08-21の調査・取得記録。需要工程台帳も同名ZIPを記載|建物候補・代表点へ加工し、合成世帯の建物割当と配送地点を作成。研究側の加工であり提供機関の公式需要・配送結果ではない。最終scoped parquetまでの変換履歴は未回復|
|国土交通省、[東京都市圏物資流動調査・個人のモノの受取調査（令和6年度）](https://www.e-stat.go.jp/stat-search/files?layout=dataset&tclass1=000001223521&tclass2=000001234242&toukei=00600520&tstat=000001078042)|表ss521「世帯人数別・世帯構成別宅配受取頻度（回数）・再配達頻度（割合）」、`ss521_r06a.xlsx` / `ss521_R06`。保存記録の取得日2026-08-23、manifest固定08-29|受取経験のある世帯の人数別小計を相対需要強度へ加工。週頻度0.65148273 / 0.93035232 / 1.18813494 / 1.45298673（1人、2人、3〜4人、5人以上）。実注文の記録ではない|
|総務省統計局・e-Stat、2020年国勢調査、2023年住宅・土地統計調査|需要工程記録の表ID `000032163278`、`000040209857`、メッシュ重み `T001141034`。対象は大田区等。全採用セル・加工設定の対応は未確認|合成世帯・住宅区分、需要重み。表名や採用セルの未確認部分を確定出典として補っていない|

PLATEAUの利用条件は[サイトポリシー](https://www.mlit.go.jp/plateau/site-policy/)および各配布データの個別条件によります。出典と研究者による加工を明示し、各地方公共団体等の権利を保持します。上表の年度・ファイル名は保存資料に基づく確認であり、失われた中間parquetの同一性を保証しません。

e-Statの[利用規約](https://www.e-stat.go.jp/terms-of-use)では数値データ等の利用と著作物の条件を区別しています。ここでは数値表を加工した合成需要の出典を示しています。需要工程記録には日量期待値82,023、世帯数384,353、Poisson seed 20260829、建物割当seed 20260830があり、正の需要record73,547件・生成需要量82,246 parcel-equivalent、建物へ割当済み需要量81,859 parcel-equivalent、39,956地点です。母数の違いを維持します。生成プログラム・全採用統計セルの完全な復元は未確認です。

行政界等の補助入力には国土数値情報N03（2026年）等の記録もあります。全量再現にはこれらの入力と加工履歴が必要です。ここに元データの再配布許諾や復元可能な外部アーカイブの存在を追加で認定するものではありません。

追加確認：保存PLATEAU ZIP内READMEは、政府標準利用規約2.0、CC BY 4.0、ODC BY、ODbLの選択肢を記載しています。これは当該ZIPの条件であり、未回復の中間建物データが同ZIPだけに由来する証明ではありません。

最終道路網の変換記録は、既存lane形状をjunction座標へ接続し、lane lengthを接続後の折線長へ更新したと記録しています。保存config_snapshotの「length維持」および生成器名とは不一致があります。道路網の配布候補は最終hashが一致する実ファイルであり、再生成手順の完全性は未確認です。

### 道路データの取得

[データ専用Release](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)から[道路データパッケージ](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz)と[SHA256](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz.sha256)を取得できます。14ファイル、48,285,157 bytes。archive SHA256：`e160e4fd83cbb529a81815a780c67ce1462f3e17048bdbccab8f087171ce189b`。データ専用タグは最新版のモデルコードを示しません。

空の領域に展開し、package rootで `python -B VERIFY.py` を実行してください。最終道路XMLのSHA256は `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。SUMOの実行や全量科学実験の再現ではなく、内容とXML構造の確認です。

公開条件充足を前提とした研究者の指示により提供しました。package内の準備時点のBLOCKED/未承認表示は、配布バイトを維持した過去の記録です。後続の公開承認はRelease説明に記載しています。3集計の法的分類、追加内容/中間DBの提供範囲、PLATEAU中間加工履歴が独立に解決済みであるとは主張しません。元データの来歴を補作せず、研究の数値を維持しています。

### 保存結果の帰属範囲


以下の13件について、[入力データの出典・加工表示](#13-data-attribution-and-licensing)を関連する帰属表示とします。© OpenStreetMap contributors。道路入力は[OpenStreetMap](https://www.openstreetmap.org/copyright)データベースに由来し、そのデータベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)で利用できます。PLATEAU・e-Stat等の出典と加工は上記data文書に記載しています。

これらは原道路網・元統計表そのものではありません。研究結果のCSVであることだけでDerivative Databaseと判定せず、逆に統計的集計であることだけでODbLの条件がなくなるとも判断していません。改変道路データからのProduced Workに該当する公開では、ODbL §4.3の表示と、§4.4・§4.6の改変データまたは全変更方法・追加内容の提供条件を確認する必要があります。最終道路網は下記Releaseから取得できます。最終XMLの提供が中間DBを含む全義務を満たすか、また一部集計の法的分類は独立に確定していません。帰属表示と提供の実施を、法的判断の確定と混同しません。

|保存ファイル|内容・公開前の残件|
|---|---|
|[CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)|集計・シミュレーション結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)|集計・道路OD派生結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json](../01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json)|シミュレーション検証/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_RESULT_FREEZE.json](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)|統合集計/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_STUDY_REPORT.md](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)|研究説明。道路データの提供条件の充足を要確認|
|[FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[COMMON_MATCHED_POPULATION.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv)|研究内部識別子・可用性。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv)|ブロック別シミュレーション出力。道路データの提供条件の充足を要確認|
|[SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv)|ブロック別派生指標。道路データの提供条件の充足を要確認|
|[CLASSICAL_QUANTUM_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)|計算/研究設計の集計。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[LOGISTICS_SERVICE_SCOPE.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)|シミュレーション時刻診断集計。道路データの提供条件の充足を要確認|
|[SCALE_INSTANCE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/SCALE_INSTANCE_COMPARISON.csv)|座標範囲・識別子・集計値。bboxの元建物加工履歴および道路データ提供条件を要確認|

座標範囲を持つSCALE_INSTANCE_COMPARISONは、建物代表点のmin/maxを含みます。全建物集合ではありませんが公開地理情報との照合可能性は残ります。科学的数値・freezeは変更していません。本節は条件整理であり、研究結果へのApache-2.0一括適用ではありません。

## 14. Limitations and Provenance

静的可行性、SUMO走行完了、実時刻での時間窓・帰還診断、実業務の全配送充足は別です。未配送で電力量が減ったことを省エネルギー成果としません。量子優位、量子実機、量子材料計算、全車両同時運行、社会全体の省エネルギーは実証していません。充電を含む主仮説の成立を本モデルだけで判定しません。

### 凍結報告の非配布参照

凍結報告と同階層の次の6資料はHayateに保持し、GitHubに含めません。報告のリンクは歴史的証拠として書き換えず、GitHub上では開けません。主要API/Notebook実行には不要ですが、これらを必要とする詳細検証は公開コードだけでは完結しません。

|ファイル|扱い|
|---|---|
|`FINAL_ARTIFACT_MANIFEST.csv`|成果物の対応・検証証拠|
|`FINAL_MECHANISM_SUMMARY.csv`|機構別集計|
|`FINAL_SPEED_DISTRIBUTION_SUMMARY.csv`|速度分布集計|
|`FINAL_SENSITIVITY_VERIFICATION.csv`|感度検証証拠|
|`FINAL_RESULT_SUMMARY.csv`|詳細結果集計|
|`FINAL_IDENTIFIABILITY_AND_LIMITATIONS.md`|研究当時の識別可能性・限界|

### 旧ガイドからの対応

次の旧文書はHayateに保持し、公開treeでは本ガイドへ集約しました。旧URLが自動転送されるとは限りません。過去の文書にある旧候補件数、未公開表示、移行途中の依存説明を現在の状態と混同しないでください。

|旧パス|現在の公開先|
|---|---|
|`CURRENT_EXECUTION.md`|[第10節](#10-quickstart-and-dependencies)|
|`configs/README.md`|[第8節](#8-data-and-configuration)|
|`data/README.md`|[第8節](#8-data-and-configuration)|
|`docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md`|[第7節](#7-analysis-and-frozen-results)|
|`docs/quantitative/BATTERY_AND_ENERGY_API.md`|[第6節](#6-battery-and-controlled-dc-energy)|
|`docs/quantitative/CURRENT_EXECUTION_GUIDE.md`|[第10節](#10-quickstart-and-dependencies)|
|`docs/quantitative/GITHUB_AND_HAYATE.md`|[第12節](#12-github-and-hayate-responsibilities)|
|`docs/quantitative/QUANTITATIVE_MODEL_INDEX.md`|[第2節](#2-model-architecture)|
|`docs/quantitative/QUANTUM_API_AND_FROZEN_PROTOCOL.md`|[第4節](#4-quantum-model-and-protocol-v2)|
|`docs/quantitative/RUNTIME_AND_FROZEN_SOURCES.md`|[第11節](#11-reproducibility-and-verification)|
|`docs/quantitative/SIMULATION_AND_TRAJECTORY_API.md`|[第5節](#5-simulation-and-trajectories)|
|`notebooks/README.md`|[第9節](#9-notebook-guide)|
|`reproducibility/environment/DEPENDENCY_SCOPE.md`|[第10節](#10-quickstart-and-dependencies)|
|`reproducibility/environment/QUICKSTART_ENVIRONMENT.md`|[第10節](#10-quickstart-and-dependencies)|
|`results/README.md`|[第7節](#7-analysis-and-frozen-results)|
