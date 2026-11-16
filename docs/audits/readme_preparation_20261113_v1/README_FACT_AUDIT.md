# README事実監査（2026-11-13）

**総合判定：HOLD。** 読取監査・更新準備は完了。AのWeb参照分母、最新J、二比較の仮説判定が既存計画・実装と一致していない。最新条件を実装済みと説明するREADMEへの更新前に解消する。研究概要と未確定事項の材料は得た。

対象は /home/takuma/kmd-analysis の最新作業ツリー。HEAD 8605d5412f6af62229a83095c35ab04c8c7dd9b1（2026-11-04）。今回のユーザー指示を採用方針の正本とし、既存文書の新しさだけで方針を変更しない。[GitHub公開README](https://github.com/tkm-sano/kmd-analysis/blob/main/README.md)も読み、EV/面接研究の説明のままであることを確認した。ローカルの未追跡成果を公開済みとはしない。GitHubからfetch/pull等で作業ツリーを書き換えていない。

開始時追跡変更はREADME.mdと.gitignore。今回の書込はこの監査ディレクトリの4 Markdownのみ。ソルバー・量子回路・予備/本実験・図生成・過去結果の再計算は0件。テキスト/JSON/CSV/DOCX XML、npyヘッダ、容量、小規模な凍結ファイルのhashと件数、原画像・一次資料の閲覧に限定した。ODの分布は保存統計の読取であり、全配列の再集計ではない。

## 1. 件数・状態

120項目。VERIFIED 82件、DESIGN_ONLY 7件、PARTIAL 13件、NOT_RUN 2件、MISSING 5件、CONFLICT 9件、LEGACY 2件。

VERIFIEDは当該コード・保存データ・原資料で確認した意味で、実測運行や本実験の正しさまで保証しない。DESIGN_ONLY=方針/設計のみ、PARTIAL=部分確認、NOT_RUN=未実施、MISSING=探索範囲で必要物未確認、CONFLICT=不一致、LEGACY=旧研究。未取得と不存在を区別する。採否はREADMEへの限定付き掲載可否であり、本実験の実行許可ではない。索引は[FILE_LINK_INDEX.md](FILE_LINK_INDEX.md)。

## 2. RQ・単一仮説・判定方針

RQ：京浜トラックターミナルを起点とする大田区内のToC配送において、量子計算は、配送実績を想定するベースライン、従来的な手法、古典最適化計算と比較して、全車両の総走行距離、積込待機時間、配送計画の計算時間という三目的について、どのような性能差とトレードオフを示すか。

研究仮説：量子計算は、古典計算と比較して、積込待機時間と全車両の総走行距離のバランスをより良好に調整できる。

仮説はこの一つのみ。RQと仮説の文言は変更しない。J_m=0.5D_m/D_A+0.5W_m/W_A、重み0.5固定、Tは別報告。E[J_D−J_B]<0、E[J_D−J_C]<0の両方について、同一需要の対応差の95%CI上限が0未満なら支持する。これはユーザーの採用方針（DESIGN_ONLY）であり、現行のA2モデル・3指標score・S2距離Dの単一主比較とは異なる。現状の資料から新しいJを数値確定できない。

## 3. 証拠台帳

各行の状態は掲載候補の具体的記述に対応する。出典URLと原資料の工程/換算条件は§6にも集約した。


### 研究

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F001 対象|大田区・京浜トラックターミナル想定単一拠点・一般車・ToC|範囲|VERIFIED|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|仮想配送条件として可|現地実運行の再現ではない|
|F002 RQ|今回指定のRQとREADME冒頭・11/8 DOCXのRQは一致|原文|VERIFIED|[README.md](../../../README.md) L5 / [research_plan_toc_three_objectives_faceted_20261108.docx](../../../research_plan_toc_three_objectives_faceted_20261108.docx)|原文のまま採用|変更しない|
|F003 単一仮説|本指示§2.3の一文のみ採用。旧計画は追加効果仮説なし|原文|CONFLICT|[docs/research/TOC_DELIVERY_SPEC.md](../../research/TOC_DELIVERY_SPEC.md) L23|今回原文のみ採用|旧H1〜H3を加えない。計画への統合未完了|
|F004 現行A|Web調査による実績参照。計画生成器ではない|定義|CONFLICT|[src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L79|最新定義として可|コードと旧文書は規則A2を使用|
|F005 旧計画値|11/8 DOCXには216PE・102秒・積込20分・人口配分等が残る|候補|CONFLICT|[research_plan_toc_three_objectives_faceted_20261108.docx](../../../research_plan_toc_three_objectives_faceted_20261108.docx)|旧版と明記|最新正本全体と表示不可|
|F006 仮定と実績|S1〜S3の規模と全運行値はresearch_assumption|出典区分|VERIFIED|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|仮定として可|実事業者の実測ではない|
|F007 公開状態|現行ToC成果は多数未追跡。公開READMEはEV/面接研究|配布|PARTIAL|[README.md](../../../README.md) / [AGENTS.md](../../../AGENTS.md)|ローカル存在と公開を区別|公開cloneでの現行全再現未確認|

### 交通

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F008 境界|N03-20260101_13の13111大田区、6668→4326変換の記録|CRS|VERIFIED|[output/toc_delivery/visualization_20261113_v1/data/boundary.geojson](../../../output/toc_delivery/visualization_20261113_v1/data/boundary.geojson)|保存版・変換を明記|行政面積とグラフ範囲は別|
|F009 対象面積|使用境界版と整合した面積集計は未確認|km²|MISSING|[output/toc_delivery/visualization_20261113_v1/data/boundary.geojson](../../../output/toc_delivery/visualization_20261113_v1/data/boundary.geojson)|数値不可|他年度の公表面積を無条件転記しない|
|F010 出入口|lon139.7429862 lat35.5863301、西側中央車両進入通路|度|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/DEPOT_ENTRANCE_DECISION.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/DEPOT_ENTRANCE_DECISION.json)|地図モデルとして可|現地測量ではない、位置誤差目安20mも仮定|
|F011 出入口根拠|JMT公式構内図とOSM node2440398083/way235963579|出典|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/sources/JMT_SITE_PLAN.png](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/sources/JMT_SITE_PLAN.png) / [output/toc_delivery/ad_pipeline_20261112_route_v2/DEPOT_ENTRANCE_DECISION.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/DEPOT_ENTRANCE_DECISION.json)|根拠付きで可|営業上の通行許可・現地搬入口未確認|
|F012 道路範囲|関東PBF全体、区外経由を許容|範囲|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json)|大田区だけのグラフとしない|道路背景表示の範囲とも別|
|F013 OSM日時|2026-07-16T20:21:30Z、厳密な原取得日時は未確認|UTC|PARTIAL|[output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSM_SOURCE_PROVENANCE_ADDENDUM.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSM_SOURCE_PROVENANCE_ADDENDUM.json)|ヘッダと保存日を区別|日付付きURLは保存名からの推定|
|F014 道路hash|PBF aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d|SHA256|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json)|保存台帳値として可|今回PBF全体の再hashなし|
|F015 OSRM|5.27.1・MLD・標準car.lua固定hash|版|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSRM_RUNTIME_MANIFEST.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSRM_RUNTIME_MANIFEST.json)|実版を記載|HTTP文書v26.5.0と実バイナリ版は別|
|F016 有向経路|一方通行を反映、同一Route objectのdistance/duration|m/s|VERIFIED|[src/kmd_toc/pipeline/route_pairs.py](../../../src/kmd_toc/pipeline/route_pairs.py) L61|可|距離最短性の保証ではない|
|F017 経路の意味|静的car profile/routabilityによる経路|規則|VERIFIED|[docs/research/COMMON_OD_VALIDATION.md](../../research/COMMON_OD_VALIDATION.md)|留保付きで可|duration単独の数学的最小性は未証明|
|F018 速度・混雑|固定profile速度と道路属性、時刻変動なし|モデル|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json)|仮定として可|実測速度・混雑再現ではない|
|F019 内部グラフ規模|customizeログ：6061697 nodes/24666600 edges|内部表現|VERIFIED|[output/toc_delivery/ad_pipeline_20261112/OSRM_CUSTOMIZE.log](../../../output/toc_delivery/ad_pipeline_20261112/OSRM_CUSTOMIZE.log) L1|関東edge based graphと明記|大田区の交差点数/道路本数ではない|
|F020 原要素と背景|PBF59799475 nodes/9603616 ways、背景39618 ways|原/表示|VERIFIED|[output/toc_delivery/ad_pipeline_20261112/OSRM_EXTRACT_ATTEMPT2.log](../../../output/toc_delivery/ad_pipeline_20261112/OSRM_EXTRACT_ATTEMPT2.log) L20 / [output/toc_delivery/visualization_20261113_v1/ROAD_EXTRACTION.json](../../../output/toc_delivery/visualization_20261113_v1/ROAD_EXTRACTION.json)|内部graphと区別|異なる表現の数を混合しない|
|F021 道路総延長|使用グラフと定義が一致する値は未確認|km|MISSING|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/ROAD_METADATA.json)|数値不可|有向arc/実道路/旋回graphの定義要確定|
|F022 連結成分|extract8975 SCC、partition5836136 SCCのログ|SCC|PARTIAL|[output/toc_delivery/ad_pipeline_20261112/OSRM_EXTRACT_ATTEMPT2.log](../../../output/toc_delivery/ad_pipeline_20261112/OSRM_EXTRACT_ATTEMPT2.log) L216 / [output/toc_delivery/ad_pipeline_20261112/OSRM_PARTITION.log](../../../output/toc_delivery/ad_pipeline_20261112/OSRM_PARTITION.log) L4|単一値として不可|処理段階/表現が違い、同じ成分数とみなせない|
|F023 snap|元座標維持、候補審査、100m上限、往復到達性の保存記録|m|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/SNAP_REVIEW.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/SNAP_REVIEW.json) / [output/toc_delivery/ad_pipeline_20261112_route_v2/roads/CONNECTIVITY_REVIEW.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/CONNECTIVITY_REVIEW.json)|モデル上の審査として可|現地アクセス保証ではない|
|F024 未提供node|node_id=0を含むS1 115/S2 217/S3 421地点|地点|PARTIAL|[output/toc_delivery/visualization_20261113_v1/VISUALIZATION_REPORT.md](../../../output/toc_delivery/visualization_20261113_v1/VISUALIZATION_REPORT.md)|制限を明記|0の座標を創作しない|
|F025 権利|OSMはODbL、自作コードApache-2.0と区別|ライセンス|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSM_COPYRIGHT.html](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/sources/OSM_COPYRIGHT.html) / [LICENSE](../../../LICENSE)|帰属を記載|全データへApacheを一括適用不可|

### OD

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F026 S1|1001²=1002001組、非対角1001000、3npy17034401bytes|組/bytes|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1/od/manifest.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1/od/manifest.json)|保存実数として可|npyヘッダ・容量確認、再生成なし|
|F027 S2|2001²=4004001組、非対角4002000、3npy68068401bytes|組/bytes|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S2/od/manifest.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S2/od/manifest.json)|保存実数として可|同上|
|F028 S3|4001²=16008001組、非対角16004000、3npy272136401bytes|組/bytes|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S3/od/manifest.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S3/od/manifest.json)|保存実数として可|生配列とヘッダ/metadata/raw容量を区別|
|F029 保存形式|distance_m/duration_sはfloat64、reachableはbool、ID順manifest|m/s/bool|VERIFIED|[src/kmd_toc/common/od.py](../../../src/kmd_toc/common/od.py) L103|可|距離をkmとして直接合計しない|
|F030 品質記録|全規模で到達不能/非有限/負値/非ゼロ対角0|保存診断|VERIFIED|[output/toc_delivery/visualization_20261113_v1/OD_VALIDATION.csv](../../../output/toc_delivery/visualization_20261113_v1/OD_VALIDATION.csv)|既存検査として可|今回全要素再検査なし|
|F031 非対称セル|S1 984546/S2 3937144/S3 15734350|有向セル|VERIFIED|[output/toc_delivery/visualization_20261113_v1/OD_VALIDATION.csv](../../../output/toc_delivery/visualization_20261113_v1/OD_VALIDATION.csv)|正常な有向性として可|i<jの無向対数とは異なる|
|F032 分布|全非対角のmean/median/Q25/Q75/min/maxを保存|km/分|VERIFIED|[output/toc_delivery/visualization_20261113_v1/data/dashboard.json](../../../output/toc_delivery/visualization_20261113_v1/data/dashboard.json) / [output/toc_delivery/visualization_20261113_v1/build_data.py](../../../output/toc_delivery/visualization_20261113_v1/build_data.py) L60|保存統計として可|今回再集計なし。散布図のみ等間隔2500標本|
|F033 Tableの拒否|旧Tableで負距離・Route差、現行は全ordered pair Route|方式|VERIFIED|[docs/research/COMMON_OD_VALIDATION.md](../../research/COMMON_OD_VALIDATION.md) / [src/kmd_toc/pipeline/route_pairs.py](../../../src/kmd_toc/pipeline/route_pairs.py)|旧版を混ぜない|旧Table結果も削除せず保全|
|F034 設定の残存|v1.1はsame_table_response/block100、実装はRoute/block25|仕様|CONFLICT|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json) / [src/kmd_toc/pipeline/route_pairs.py](../../../src/kmd_toc/pipeline/route_pairs.py) L30|運行正本と道路正本を分離|新設定版による統合未完了|
|F035 生成・再開|分割・gzip raw・context/hash・S1→S2→S3祖先参照|I/O|VERIFIED|[scripts/build_route_pair_od.py](../../../scripts/build_route_pair_od.py) / [src/kmd_toc/pipeline/route_pairs.py](../../../src/kmd_toc/pipeline/route_pairs.py)|可|公共OSRM大量要求を前提にしない|
|F036 共通参照|input hashとOD hashを同一問題の全手法が使用|同一性|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/roads/COMMON_BUNDLES.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/COMMON_BUNDLES.json) / [src/kmd_toc/dwt/worker.py](../../../src/kmd_toc/dwt/worker.py) L43|可|入力hashが異なる結果を同じ比較点にしない|

### 需要

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F037 配送先の意味|建物に対応する一意stop、人数/世帯数ではない|地点|VERIFIED|[03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md)|可|旧顧客数のHOLDを引き継がない|
|F038 母集団|元39956、監査PASS34912、182町丁目|地点/地域|VERIFIED|[03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json)|元比率とeligible集合を区別|実需要観測ではない|
|F039 地域配分|元地点比を最大剰余法で整数化、SHA256順位で非復元抽出|方法|VERIFIED|[03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json) / [src/kmd_toc/freeze_demand.py](../../../src/kmd_toc/freeze_demand.py)|可|人口メッシュでの再配分なし|
|F040 需要seed|決定論的hash順位、demand_seed=null、入力seedと別|乱数|VERIFIED|[src/kmd_toc/dwt/worker.py](../../../src/kmd_toc/dwt/worker.py) L116 / [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json)|可|SHA順位をPRNGと呼ばない|
|F041 荷量|1地点1配送単位＝制御上1荷物|単位|VERIFIED|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|仮定として可|実測kg/個数ではない|
|F042 集合|S1/S2/S3は1000/2000/4000、重複なし、厳密包含|地点|VERIFIED|[03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/VALIDATION.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/VALIDATION.json)|今回CSV読取でも照合|3規模を独立3事例としない|
|F043 凍結pin|8ファイル、manifest/checksums/configのソースpinとpayload照合|SHA256|VERIFIED|[src/kmd_toc/frozen_demand_pin.py](../../../src/kmd_toc/frozen_demand_pin.py) / [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/SHA256SUMS](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/SHA256SUMS)|現物hash後掲|凍結再生成なし|
|F044 独立需要|各規模固定1事例、新独立family生成は未承認|n|MISSING|[configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json)|本番入力不足を明記|rやshotsを増やしてもnは増えない|

### 運行

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F045 S1〜S3|1000/10/2、2000/20/4、4000/40/8|地点/台/バース|VERIFIED|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|研究仮定として可|施設実績ではない|
|F046 便・容量|最大2便/車、60単位/便、未使用/1便可|便/単位|VERIFIED|[src/kmd_toc/common/models.py](../../../src/kmd_toc/common/models.py) L168 / [src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L87|可|便数は固定2必須ではない|
|F047 積込|1800秒/活動便、排他・中断なし|s|VERIFIED|[src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L69 / [configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|可|30分は便間の固定休止ではない|
|F048 作業|顧客120秒/地点|s|VERIFIED|[src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L16|固定仮定として可|計画を人が考える時間Tではない|
|F049 帰着準備|0秒、第2便readyは前便帰着|s|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L98|可|第2便出発は積込完了後|
|F050 勤務・ready|8〜20時、a_v=28800+floor(3600(v+.5)/V)|JST秒|VERIFIED|[src/kmd_toc/common/config.py](../../../src/kmd_toc/common/config.py) L46|可|労働法令全体の充足主張不可|
|F051 割当・時間窓|割当と順序を両方計画、顧客時間窓なし|制約|VERIFIED|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json) / [src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L57|可|顧客時間窓なしを実態としない|
|F052 全被覆・空便|全stop一度、活動便非空、未使用可、違反は拒否|制約|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L66|可|違反指標はnull、自動成功化なし|
|F053 積込出発と接続|積込終了時出発、ceil移動＋120秒を伝播、帰着期限|時刻|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L98 / [src/kmd_toc/common/od.py](../../../src/kmd_toc/common/od.py) L82|可|負待機を0にしない|
|F054 バース|半開区間・排他・同時数制約、積込時間固定|時刻|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L168 / [src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L81|可|バースID彩色は開始時刻を改変しない|
|F055 容量下界|総容量1200/2400/4800、最低17/34/67便|単位/便|VERIFIED|[docs/research/COMMON_CONSTRAINT_AUDIT.md](../../research/COMMON_CONSTRAINT_AUDIT.md)|必要条件として可|S2/S3可行性の証明ではない|

### A

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F056 D外部例|佐川都市担当者2025-01-10の13km、通常約20kmは別説明|km/担当車両日|VERIFIED|[output/toc_delivery/a_sagawa_relative_20261112/sources/SAGAWA_DISTANCE.txt](../../../output/toc_delivery/a_sagawa_relative_20261112/sources/SAGAWA_DISTANCE.txt) L180|背景参照のみ|全車両数/N/便数/集荷割合不明、×V換算不可|
|F057 W26分|木更津/STLC等の拠点間輸送で平均荷積み待ち26分|分/工程|VERIFIED|[output/toc_delivery/a_sagawa_relative_20261112/sources/KANTO_PAGE-60.png](../../../output/toc_delivery/a_sagawa_relative_20261112/sources/KANTO_PAGE-60.png)|W_Aへ不採用|ready境界不明、二欄合計52分にしない|
|F058 一般貨物60分|国交省2025年度の運行単位の一般荷待ち|分/運行|PARTIAL|[docs/research/toc_delivery_a/A_REFERENCE_VALUES.md](../../research/toc_delivery_a/A_REFERENCE_VALUES.md) L12|背景のみ|本研究W_Aと異なる、今回原PDF再閲覧なし|
|F059 日本郵便T|熟練300〜600秒、新人1800〜3600秒、2021年時点の紙地図ルート作成|秒/工程|VERIFIED|[docs/research/toc_delivery_a/A_REFERENCE_VALUES.md](../../research/toc_delivery_a/A_REFERENCE_VALUES.md) L13|工程外部参照|N/V/P・入力/割当/バース/全体検査不明、CIではない|
|F060 行政T|協栄流通・1センター毎日7〜8時間＝25200〜28800秒|秒/センター日|VERIFIED|[docs/research/toc_delivery_a/A_GOVERNMENT_EVIDENCE_REGISTER.csv](../../research/toc_delivery_a/A_GOVERNMENT_EVIDENCE_REGISTER.csv)|外部配車工程参照|対象N/V/P、wall/人時が不明、S1換算不可|
|F061 Loogia差分図|距離10/9/11km・ルート組み10/15/30分の削減のみ|差分|VERIFIED|[output/toc_delivery/a_sagawa_relative_20261112/sources/OPTIMIND_CHART.jpg](../../../output/toc_delivery/a_sagawa_relative_20261112/sources/OPTIMIND_CHART.jpg)|改善前絶対値/率へ不採用|分母がなく改善率作成不可|
|F062 正規化の分母|共通計画単位のWeb由来D_A/W_Aは未取得|km/分|MISSING|[docs/research/toc_delivery_a/A_REFERENCE_VALUES.json](../../research/toc_delivery_a/A_REFERENCE_VALUES.json)|J数値確定不可|数値が正であるだけでは適格にならない|
|F063 合成参照|異なる資料から構成するなら合成ベースラインと明記|定義|DESIGN_ONLY|[docs/research/toc_delivery_a/A_REFERENCE_VALUES.md](../../research/toc_delivery_a/A_REFERENCE_VALUES.md)|最新方針として可|単一実在計画のD/W/T点にしない|
|F064 旧A2|D551.1398/W422.45、DWT完成後はW416.4、研究計画の推計|km/分|CONFLICT|[docs/research/DWT_FINAL_COMPARISON.md](../../research/DWT_FINAL_COMPARISON.md) / [configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json)|現行Web基準へ不採用|旧規則ベース成果として保全|
|F065 人手T感度|3860〜60500秒等は工程仮定の未校正感度|s|PARTIAL|[docs/research/A_HUMAN_TIME_CALIBRATION.md](../../research/A_HUMAN_TIME_CALIBRATION.md) / [docs/research/toc_delivery_a/A_METHOD_AND_HUMAN_T_EVIDENCE_DECISION.md](../../research/toc_delivery_a/A_METHOD_AND_HUMAN_T_EVIDENCE_DECISION.md)|実測/CIとして不可|全体T未取得を範囲で埋めない|

### 実装

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F066 Bの方式|VeRyPy savings生成を利用した自作有向tail→head CW拡張|方法|VERIFIED|[src/kmd_toc/pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py) L6|標準VeRyPy全体と区別|上流の対称版coreをそのまま使用していない|
|F067 Bの制約|生成時容量/便数、超過ルートを挿入削減、時間/バースは完成器|範囲|VERIFIED|[src/kmd_toc/pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py) L15 / [src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L93|完成器込みで説明|初期生成だけで全制約を満たすとはしない|
|F068 VeRyPy版|8698f910ffcfb4bc8743aedbf203d6de72fbe006、MIT|commit|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/VERY_PY_PROVENANCE.json](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/VERY_PY_PROVENANCE.json)|可|外部cloneとpth依存あり|
|F069 Cモデル|Routingで仮想2V便・単位容量・距離0.1m整数cost|モデル|VERIFIED|[src/kmd_toc/pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py) L39|可|物理車両/日程は次段|
|F070 C探索|CW初期、PARALLEL_CHEAPEST_INSERTION、GUIDED_LOCAL_SEARCH、時間上限|設定|VERIFIED|[src/kmd_toc/pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py) L46|可|strategy名だけでCPU並列としない|
|F071 Cの接続|Routingは容量距離、物理2便・勤務・バースはCP-SAT完成|範囲|VERIFIED|[src/kmd_toc/pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py) L63 / [src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L57|可|全VRP最適性保証なし|
|F072 共通完成器|有限プールの被覆、物理車両便、積込時刻、累積バース|CP-SAT|VERIFIED|[src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L57|FEASIBLE/OPTIMALを区別|OPTIMALでも有限プール内|
|F073 D原著|Huang/Matsuyama/Yamashiro 2025 arXiv2503.17051v1を参考に独立実装|原著|VERIFIED|[docs/research/toc_delivery_d/D_REFERENCE_IMPLEMENTATION_REPORT.md](../../research/toc_delivery_d/D_REFERENCE_IMPLEMENTATION_REPORT.md) L3|参考実装と明記|著者コード・全原著数値の再現ではない|
|F074 D経路|CW→初期完成→有限日列LP/IP→AOA→日列拡張→共通完成|処理|VERIFIED|[src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L111|可|有限時間・候補領域の制限|
|F075 D探索空間|最大3断片の便内並替と初期時刻由来の有限日列|範囲|VERIFIED|[src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L175 / [src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L244|限定AOAと記載|全VRP価格付け/整数最適性証明ではない|
|F076 AOA数理|ALiM型二次penalty・Ising・one-hot・exact ring XY mixer|回路|VERIFIED|[src/kmd_toc/column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py) L123 / [src/kmd_toc/column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py) L183|可|旧単一車両QAOAとは別|
|F077 量子backend|訓練one-hot tensor＋multinomial、最終Qiskit Statevector.sample_counts|CPU simulation|VERIFIED|[src/kmd_toc/column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py) L240|可|Sampler/Aer/実機実行としない|
|F078 回路設定|通常12qubit、p2・4角度、COBYLA最大80評価・1restart|設定|VERIFIED|[configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json) / [src/kmd_toc/column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py) L98|制限を併記|深さは回路依存、代表保存S1はlogical33/native未展開|
|F079 shots|訓練1000/評価・最終4096/回路、主実験値未確定|測定相当数|PARTIAL|[configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json) / [docs/research/D_SHOTS_AUDIT.md](../../research/D_SHOTS_AUDIT.md)|既存実効値として可|10000妥当性を認定済みとしない|
|F080 復号|重複/空/容量違反拒否、全断片一度の候補を元便へ展開|候補|VERIFIED|[src/kmd_toc/column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py) L202 / [src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L254|可|不正標本を自動成功化しない|
|F081 D寄与|旧S1/限定DWTの新量子経路最終採用0の記録|観測|VERIFIED|[docs/research/DWT_FINAL_COMPARISON.md](../../research/DWT_FINAL_COMPARISON.md) / [output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1/D_QUANTUM_ATTRIBUTION.json](../../../output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1/D_QUANTUM_ATTRIBUTION.json)|量子改善主張不可|古典incumbentの非悪化保証を分離|
|F082 量子なし対照|D_CLASSICAL_CONTROL、schema互換でplan method_idはB|対照|VERIFIED|[src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L302|試行ラベルで分離|通常Bへ集計しない|
|F083 CPU並列|各手法4プロセス×1native thread、共通4CPU枠、手法間逐次|実行|VERIFIED|[AGENTS.md](../../../AGENTS.md) / [src/kmd_toc/dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py) L23|今後の既定として可|内部枝は外側の反復数でない|
|F084 並列検証範囲|人工6/20地点のみ、S1〜S3並列道路実験なし|範囲|PARTIAL|[output/toc_delivery/cpu_parallel_20261113_v1/CPU_PARALLEL_VALIDATION_REPORT.md](../../../output/toc_delivery/cpu_parallel_20261113_v1/CPU_PARALLEL_VALIDATION_REPORT.md)|対象範囲付きで可|実装GOと本番準備を分離|

### 指標

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F085 D|活動全便の有向OD距離mの合計/1000|km|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L32 / [src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L12|可|d_ijの単位を明記|
|F086 W|Σ(load_start-ready)/60、負待機拒否、積込自体を除外|分|VERIFIED|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L98 / [src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L160|可|ready付替え禁止|
|F087 T_program|親入力読込前→全枝回収・選択・最終二重検証|wall秒|VERIFIED|[src/kmd_toc/dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py) L226|可|準備/出力/可視化を別計測|
|F088 旧T境界|Route v2・DWT逐次・現行並列の境界/資源は異なる|s|PARTIAL|[docs/research/REPRODUCE.md](../../research/REPRODUCE.md) / [src/kmd_toc/dwt/worker.py](../../../src/kmd_toc/dwt/worker.py) L134 / [src/kmd_toc/dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py) L313|版を明記|同じ性能分布へ混合不可|
|F089 新J|J=.5D/D_A+.5W/W_A、Tは別|無次元|DESIGN_ONLY|[src/kmd_toc/dwt/evaluation.py](../../../src/kmd_toc/dwt/evaluation.py) L34|今回方針として可|分母と専用評価が未整備|
|F090 既存J|3要素D/W/T、正の3参照を必須、4重み条件|無次元|CONFLICT|[src/kmd_toc/dwt/evaluation.py](../../../src/kmd_toc/dwt/evaluation.py) L34 / [configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json)|新J実装済みと不可|(.5,.5,0)でもT必須。主設定とも不一致|
|F091 仮説の判定|D対BとD対CのJ対応差、両95%CI上限<0|対応差|DESIGN_ONLY|[docs/research/DWT_STATISTICAL_PROTOCOL.md](../../research/DWT_STATISTICAL_PROTOCOL.md) L19|最新ユーザー方針として記載|既存はS2距離Dの単一比較|
|F092 旧主比較|S2のD対C・D_kmを確認的、その他探索的|推論|CONFLICT|[configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json) / [docs/research/DWT_STATISTICAL_PROTOCOL.md](../../research/DWT_STATISTICAL_PROTOCOL.md) L19|最新検定として不可|Jと両比較用の分散/CI/n/rへ要改訂|
|F093 パレート|同一input hashの受理B〜D点、Decimal格子支配|集合|VERIFIED|[src/kmd_toc/dwt/evaluation.py](../../../src/kmd_toc/dwt/evaluation.py) L45|観測非支配集合として可|数学的最適性は未証明|

### 統計

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F094 n/r/枝/shots|独立需要n、外側反復r、内部4枝、回路shotsは別|単位|VERIFIED|[docs/research/CPU_PARALLEL_EXECUTION.md](../../research/CPU_PARALLEL_EXECUTION.md) / [configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json)|可|内部枝を擬似反復にしない|
|F095 必要試行数|n/r・分散・h/δ・最終主セルはnull|設計|DESIGN_ONLY|[configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json)|未確定を明記|J差の目標精度も必要|
|F096 予備12×3|分散設計の初期案、実施結果や本番必要数でない|n/r案|DESIGN_ONLY|[configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json)|暫定案と記載|旧30×5・既定5回を採用しない|
|F097 算定式|n(r)≥z²(σ_b²+σ_w²/r)/h²、検出力式も併用|式|DESIGN_ONLY|[docs/research/DWT_SAMPLE_SIZE_PIPELINE.md](../../research/DWT_SAMPLE_SIZE_PIPELINE.md)|方法として可|最新J差への更新と予備分散未取得|
|F098 seed保存|外側登録seed→内部SeedSequence→局所AOA系列、全件ログ|乱数|VERIFIED|[src/kmd_toc/dwt/experiment.py](../../../src/kmd_toc/dwt/experiment.py) L80 / [src/kmd_toc/dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py) L62 / [src/kmd_toc/dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) L247|可|訓練/最終は枝内同じ系列を順次使用|
|F099 CI実装|階層/Fieller/Wilson/cluster法は設計あり、analysisはfront/値リスト|統計処理|PARTIAL|[docs/research/DWT_STATISTICAL_PROTOCOL.md](../../research/DWT_STATISTICAL_PROTOCOL.md) / [src/kmd_toc/dwt/analysis.py](../../../src/kmd_toc/dwt/analysis.py)|CI実装済み不可|最新J対応差・7統計図の生成器未確認|
|F100 失敗|D/W/受理計画Tをnull、経過/失敗理由/登録試行を保持|欠測|VERIFIED|[src/kmd_toc/dwt/worker.py](../../../src/kmd_toc/dwt/worker.py) L111 / [src/kmd_toc/dwt/standard.py](../../../src/kmd_toc/dwt/standard.py) L43|可|成功のみから全体性能を主張しない|
|F101 旧限定観測|同一需要でε/τとseedが異なる各セル1観測|n|VERIFIED|[docs/research/DWT_FINAL_COMPARISON.md](../../research/DWT_FINAL_COMPARISON.md)|記述のみ可|独立需要・純粋な予算因果効果としない|
|F102 主実験|最新A/J・独立需要/反復条件で全規模の主実験なし|結果|NOT_RUN|[configs/toc_delivery/dwt_statistical_protocol_v1.json](../../../configs/toc_delivery/dwt_statistical_protocol_v1.json) / [docs/research/DWT_FINAL_COMPARISON.md](../../research/DWT_FINAL_COMPARISON.md)|未実施を明記|旧限定実行を本実験へ昇格しない|

### 図表

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F103 7図設計|総合/D/W/T/S1/S2/S3の設計書は存在|図番号|DESIGN_ONLY|[docs/research/DWT_7_FIGURES_SPEC.md](../../research/DWT_7_FIGURES_SPEC.md)|全図作成予定|専用統計生成器は未完成|
|F104 旧番号|DOCX/TOC_SPECの図番号と現在7図、renderの3図は別|構成|CONFLICT|[docs/research/DWT_7_FIGURES_SPEC.md](../../research/DWT_7_FIGURES_SPEC.md) L5 / [scripts/render_dwt.py](../../../scripts/render_dwt.py) L32|旧図は別枠|7統計図完成としない|
|F105 色|設計A灰/B青緑/C青/D橙、renderはB青/C緑/D紫|表示|CONFLICT|[docs/research/DWT_7_FIGURES_SPEC.md](../../research/DWT_7_FIGURES_SPEC.md) L23 / [scripts/render_dwt.py](../../../scripts/render_dwt.py) L20|予定色へ要統一|色の意味を混合しない|
|F106 標準出力|plan/routes/stops/berth_events/metrics/manifest/validation|JSON/GeoJSON/CSV|VERIFIED|[src/kmd_toc/dwt/standard.py](../../../src/kmd_toc/dwt/standard.py) L10|可|失敗時は架空planなし|
|F107 生成データ|7図用CI/対応差/EAF生成器と本実験データが不足|成果物|MISSING|[scripts/render_dwt.py](../../../scripts/render_dwt.py) / [docs/research/DWT_7_FIGURES_SPEC.md](../../research/DWT_7_FIGURES_SPEC.md)|作成予定|単発に箱ひげ/CIを作らない|
|F108 ダッシュボード|4タブと静止図、旧S1・ODを保存済み|可視化|VERIFIED|[output/toc_delivery/visualization_20261113_v1/index.html](../../../output/toc_delivery/visualization_20261113_v1/index.html) / [output/toc_delivery/visualization_20261113_v1/VISUALIZATION_REPORT.md](../../../output/toc_delivery/visualization_20261113_v1/VISUALIZATION_REPORT.md)|旧限定結果の表示として可|最新Web A/Jに対応済みではない|

### 結果

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F109 Route v2 S1|B444.1768/285.75/33.0578014、C410.1098/342/93.1386804、D444.1768/285.75/82.3859066|km/分/秒|VERIFIED|[output/toc_delivery/ad_pipeline_20261112_route_v2/A_TO_D_COMPARISON.csv](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/A_TO_D_COMPARISON.csv)|過去限定検証として可|現行並列の本実験値でない|
|F110 DWT限定|全41試行、limited12中11受理、観測front B2/C3/D1|保存記録|VERIFIED|[output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1/THREE_OBJECTIVE_EVALUATION.json](../../../output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1/THREE_OBJECTIVE_EVALUATION.json)|n=1各セルと明記|有意順位や仮説支持でない|
|F111 S2/S3計画|ODはあるが全規模B〜D主比較結果なし|実験|NOT_RUN|[docs/research/DWT_FINAL_COMPARISON.md](../../research/DWT_FINAL_COMPARISON.md)|未実行を明記|OD完了を配送実験完了としない|
|F112 BとD|旧S1便経路集合は一致、車両日/時刻まで同じではない|計画|VERIFIED|[output/toc_delivery/visualization_20261113_v1/B_D_COMPARISON.json](../../../output/toc_delivery/visualization_20261113_v1/B_D_COMPARISON.json)|区別して記載|D/W一致だけで同一計画/量子効果としない|

### 再現

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F113 環境|Python3.12.11/NumPy2.3.1/SciPy1.16.0/OR-Tools9.14.6206/Qiskit2.1.1|版|VERIFIED|[output/toc_delivery/cpu_parallel_20261113_v1/ENVIRONMENT.json](../../../output/toc_delivery/cpu_parallel_20261113_v1/ENVIRONMENT.json)|保存環境として可|今回import/実験なし|
|F114 CPU|Linux AMD EPYC9684X、今後4CPU、旧1worker等とは別|資源|VERIFIED|[docs/research/CPU_PARALLEL_EXECUTION.md](../../research/CPU_PARALLEL_EXECUTION.md)|可|S1並列資源実測は未取得|
|F115 lock/導入|旧D/vehicle-day lockはあるが全依存統合portable installer未確認|配布|PARTIAL|[reproducibility/environment/vehicle_day_v1/requirements.lock.txt](../../../reproducibility/environment/vehicle_day_v1/requirements.lock.txt) / [docs/research/REPRODUCE.md](../../research/REPRODUCE.md)|限定記載|旧quickstartを現行VRP全再現としない|
|F116 形状コード依存|standard.Geometryがoutput内data_access.py/保存経路/索引へ依存|実装依存|PARTIAL|[src/kmd_toc/dwt/standard.py](../../../src/kmd_toc/dwt/standard.py) L16|必須資産として記載|outputを全て消して再現できるとはしない|
|F117 版照合|登録はsource hash記録、run_registeredで全source再照合は未確認|保証|PARTIAL|[src/kmd_toc/dwt/experiment.py](../../../src/kmd_toc/dwt/experiment.py) L58 / [src/kmd_toc/dwt/experiment.py](../../../src/kmd_toc/dwt/experiment.py) L158|記録と強制検証を区別|実行時コードの不変保証要整備|
|F118 テスト記録|233既存＋13並列＝246、並列90/独立290検査|保存記録|VERIFIED|[output/toc_delivery/cpu_parallel_20261113_v1/CPU_PARALLEL_VALIDATION_REPORT.md](../../../output/toc_delivery/cpu_parallel_20261113_v1/CPU_PARALLEL_VALIDATION_REPORT.md)|過去の検証として可|今回の実行件数0|

### 旧研究

|ID・項目|記述・数値・定義|単位|状態|根拠ファイル・箇所|README採否|未確認/留保|
|---|---|---|---|---|---|---|
|F119 TSP/電力|src/kmd_quantitativeの単一車両routing/quantum、電池/電力量|履歴|LEGACY|[src/kmd_quantitative/routing/solver.py](../../../src/kmd_quantitative/routing/solver.py) / [src/kmd_quantitative/quantum/formal.py](../../../src/kmd_quantitative/quantum/formal.py)|履歴案内のみ|現行複数車両B〜Dと混ぜない|
|F120 面接/仮説|旧H1〜H3・反証インタビュー・RIQ|履歴|LEGACY|[docs/research/EXPERT_INTERVIEW_PROTOCOL.md](../../research/EXPERT_INTERVIEW_PROTOCOL.md) / [docs/research/RESEARCH_DESIGN_SUMMARY.md](../../research/RESEARCH_DESIGN_SUMMARY.md)|履歴案内のみ|現行の単一仮説へ追加しない|

## 4. 共通運行条件：設定と実装

|項目|S1|S2|S3|設定/実装の根拠|
|---|---:|---:|---:|---|
|配送先数|1000|2000|4000|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|
|車両数|10|20|40|[src/kmd_toc/common/models.py](../../../src/kmd_toc/common/models.py) L194|
|バース数|2|4|8|[configs/toc_delivery/common_conditions_v1_1.json](../../../configs/toc_delivery/common_conditions_v1_1.json)|
|最大便数|2|2|2|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L87|
|容量 [単位/便]|60|60|60|[src/kmd_toc/common/models.py](../../../src/kmd_toc/common/models.py) L168|
|積込 [秒/便]|1800|1800|1800|[src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L69|
|顧客作業 [秒/地点]|120|120|120|[src/kmd_toc/pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py) L34|
|最終帰着 [JST]|20:00|20:00|20:00|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L151|
|帰着後準備 [秒]|0|0|0|[src/kmd_toc/common/validation.py](../../../src/kmd_toc/common/validation.py) L98|

すべて研究仮定としてのVERIFIED。30分は積込であり帰着後の固定休止ではない。勤務8〜20時、初便ready=28800+floor(3600(v+0.5)/V)、第2便ready=前便帰着。積込終了時に出発、各有向移動をceil秒・顧客作業120秒で伝播する。休憩・労働関係法令全体を満たすとは主張しない。

全被覆/重複禁止、容量、拠点往復、最大便数、便接続、積込準備、バース排他/同時数、積込完了、移動/作業、勤務、非空便、違反拒否はcommon/validation.py L66以降にある。未使用車両は便を生成しない。初期ルート生成で全日程を直接満たすわけではなく、完成器と最終検査を含む手法として説明する。総容量1200/2400/4800、必要便数17/34/67は必要条件でありS2/S3可行性証明ではない。

## 5. 共通道路ODの数値

距離m・時間s・到達性boolを保存する。npyヘッダと実ファイル容量を読み、S1/S2/S3の(1001/2001/4001)²を確認した。理論上必要な全組と保存済み行列要素数は同じ。自己地点は各n個、非対角はn(n−1)。gzip raw・注釈node・道路graph・metadataの容量は3npy容量へ含めていない。

以下は保存済みdashboard.json.statsの全非対角の統計。build_data.py L60の対象配列・単位と照合しただけで、今回平均・分位点を再計算していない。

|規模|距離 min/Q25/median/Q75/max [km]|平均距離 [km]|時間 min/Q25/median/Q75/max [分]|平均時間 [分]|
|---|---|---:|---|---:|
|S1|0.000000 / 2.561300 / 3.975600 / 5.615700 / 13.442200|4.204016740|0.000000 / 5.235000 / 7.406667 / 9.738333 / 20.355000|7.626496891|
|S2|0.000000 / 2.562100 / 3.974700 / 5.607900 / 13.442200|4.203078522|0.000000 / 5.260000 / 7.416667 / 9.728333 / 20.620000|7.634900311|
|S3|0.000000 / 2.564900 / 3.979800 / 5.615400 / 13.442200|4.208665152|0.000000 / 5.265000 / 7.431667 / 9.753333 / 20.953333|7.650917324|

非対角最小0は別IDが同じsnapを共有する可能性を含み、直ちに欠損/到達不能や0埋めとは判定しない。方向差はi<jのd(i,j)−d(j,i)。散布図のみ等間隔2500組で、分布は全非対角。全ODの欠損/非有限/負/非ゼロ対角/到達不能0は既存検査の記録を参照した。

OSRM内部graphは処理段階別に数値が異なる。customizeの6,061,697 nodes/24,666,600 edges、原PBFの59,799,475 nodes/9,603,616 ways、背景39,618 waysを一つの大田区ネットワークの数にしない。extract/partitionのSCCも同じ表現の連結成分として統一解釈する根拠は未確認。使用境界版の面積・採用graph道路総延長は未確認のまま残す。

## 6. Aの一次資料・値・換算・採否

|出典と箇所|主体・公開/対象期間・業務|原値と性質|N/V/P・測定境界・換算/不確実性|採否|
|---|---|---|---|---|
|[佐川公式「歩数検証」](https://www.sagawa-exp.co.jp/about-csr/column/article_33.html)、検証結果/都市担当者|佐川急便、記事2025-02-06、観測2025-01-10、東京集配|トラック13km、事業者公表の単日観測。通常約20kmは別説明|N/便数/全車台数・原距離ログ不明。徒歩約14kmとは別。×V/便数換算未承認|D_Aには不適格、外部背景のみ|
|[関東運輸局PDF](https://wwwtb.mlit.go.jp/kanto/jidou_koutu/kamotu/kamotu_kyougikai/date/kanagawa/12/4.pdf#page=60)、PDF p.60（印刷-59-内の事例-5-）|行政掲載の佐川関連一般貨物/拠点間輸送、原計測期間未確認|木更津・STLC等の欄に平均荷積み待ち26分|ready境界不明。二欄を合計52分にせず、S1便数倍もしない|ToC W_Aへ不採用|
|[日本郵便・Loogia](https://loogia.jp/cases/nihonyubin/)、導入前の課題|オプティマインド掲載・日本郵便担当者インタビュー、2021年時点、ゆうパック|熟練5〜10分、新人30分〜1時間程度の紙地図ルート作成|分×60のみ。300〜600/1800〜3600秒。N/V/P、割当・バース・入力/検査の包含範囲不明。CIでない|個別工程の外部T参照、全計画Tへ不採用|
|[国交省ITツール活用ガイド](https://www.mlit.go.jp/jidosha/content/001311692.pdf#page=7)、PDF p.7・印刷p.11|行政掲載・協栄流通事例、1センター毎日の配車、原観測期間未確認|改善前7〜8時間＝25200〜28800秒、企業事例値|対象センターN/V/P、wallか総人時か不明。全社台数をセンター数で割らない|全体配車の外部参照のみ、S1〜S3へ比例換算不可|
|[Loogia結果画像](https://www.optimind.tech/wp-content/uploads/cms/png2.jpg)|オプティマインド、2020実地検証を2021発表、担当/代走/新人応援|距離10/9/11km、ルート組み10/15/30分の短縮という差分|分母と改善前後絶対値なし、図の矢印長から率を作らない|改善前D/Tや改善率へ不採用|
|既存A2計画・設定|研究規則と共通完成器|D551.1398/W422.45、DWT完成後W416.4のシミュレーション|Web実績への変換不可|今回A/Jの分母に不採用、過去成果として保全|

Dの全車両総距離D_A、ready基準の積込待機総和W_A、入力〜全体検査のT_AはいずれもWeb資料から共通計画単位へ確定できていない。A_REFERENCE_VALUES.jsonの各S*値もnull。資料が違う値を同一計画の(D,W,T)と表現しない。正値性だけで正規化に採用せず、出典/規模/単位/定義/換算式/仮定を満たす必要がある。合成Aを使う場合はその構成を公開し、参照の感度と統計CIを分離する。

今回のWeb再確認では日本郵便の回答と国交省PDF p.7の原文を読んだ。佐川はページ取得後の本文位置再取得がtimeoutとなったため、保存原文SAGAWA_DISTANCE.txt L180〜190で13kmと通常約20kmを照合。関東PDFはWebサイズ制限で失敗し、保存原画像KANTO_PAGE-60.pngを目視した。Loogia結果画像も目視し差分ラベルのみと確認した。一般貨物60分、その他行政事例は既存台帳の確認で、今回未閲覧の原資料を再検証済みとはしない。各URLへの到達成功と原数値の検証を区別する。

公表主体の優先順だけで採用しない。job tagの区域/順序/帰所再積込や国交省の割当/経路工程は定性的根拠であり、最大2便や人手T係数を実証するものではない。行政調査・事例値も独立時計ログとは限らない。

## 7. 統計と新仮説判定の整合性

同じ需要iに対する差は、D_A/W_Aを固定正基準とする場合、ΔJ_DB,i=.5(D_D,i−D_B,i)/D_A+.5(W_D,i−W_B,i)/W_A（D対Cも同形）である。反復の集約・対応と失敗時の推論対象を先に固定する必要がある。Aの参照自体が不確かなら、固定基準条件付きCIと参照感度を区別する。

旧主比較はS2の距離DのD対Cのみであり、新しい二つのJ差を検証しない。分散推定、必要数、h/δ、主規模・ε/τ、CI処理を新方針へ対応させる。需要事例間/内の分散を分離し、n(r)≥z²(σ_b²+σ_w²/r)/h²と検出力式の大きい方を候補として、有限標本・分散不確実性・資源で校正する。現状各規模固定1需要で、需要一般化の95%CIは取得できない。12×3は初期予備案、30×5や5回を確定値としない。

「両方の95%CI上限<0」の全体支持判定はintersection–union型として事前規定できる。二比較の独立性は不要で、全体帰無が成立する場合は少なくとも一方の非改善成分を誤って棄却しなければ両方の条件は成立しない。両側95%CI上限は片側判定では保守的。一方、個別二比較や全規模/全セルの同時保証を別々に主張するならHolm等の適用範囲を事前定義する。これは監査上の整合案で、今回protocolを改訂したものではない。

失敗は削除せず、取得率と成功条件下/両成功条件下の性能を分ける。旧Fieller/cluster/Wilson設計は参考になるが新JのCI実装は未確認。標準偏差/標準誤差/CIと文献範囲・仮定感度を混同しない。S1〜S3を独立3需要としてプールしない。

## 8. 7図の対応と不足

|図|目的・軸/単位|比較・記号/誤差|元データ・集計/生成・状態|
|---|---|---|---|
|1 総合|手法横軸、D[km]/W[分]/T[秒]の別パネル|分布・中央値・n/r/成功数。Aは外部参照/別欄|主実験データ/専用統計生成器不足：作成予定|
|2 D|手法/規模とD[km]、対応差の別パネル|平均95%CI・元単位効果量、適格Aなら基準線|CI実装未確認、作成予定|
|3 W|手法/規模とW[分]、対応差|95%CI、0分母に微小値を足さない|同上、作成予定|
|4 T|手法/規模とT_program[秒]、必要なら対数軸|実測分布/95%CI、τ別線、A人手参照別枠|並列版主測定なし、作成予定|
|5 S1 3目的|D/W/T点・D–W平面とT表現・固定T断面|同一需要内の観測front、将来EAF点ごと95%CI|旧単発front画像はあるが統計7図の完成ではない、作成予定|
|6 S2 3目的|図5同様S2|同上、規模間対応を維持|ODのみ、計画主データなし、作成予定|
|7 S3 3目的|図5同様S3|同上|ODのみ、計画主データなし、作成予定|

既定の予定色はA灰#808080/B青緑#008C95/C青#2563EB/D橙#EA8A23。render_dwt.pyの色は別で統一未完了。箱ひげの1.5IQRひげは95%CIではない。EAFの閾値/T断面/再標本化回数は未確定で、集合の不確実性は独立family全体を再標本化する設計が必要。Aの出典間の値を確率分布や一つの3D点へ合成しない。旧A規則に基づく7図仕様の記述も今回のWeb Aへ読み替える必要がある。

元データは登録→需要/OD→seed→raw plan/metrics→独立検査→解析→図データで追跡する設計だが、本実験のこの列はまだない。scripts/render_dwt.pyの3図、旧4タブダッシュボード、人工検証図を現行7統計図と数えない。

## 9. 再現性・旧研究

入口：run_dwt.py→dwt.experiment→worker.execute_trial→parallel→枝worker.execute→methods→共通完成器→共通/第二検査→standard→analysis。入力はRoute v2のroads/inputs、通常設定はv1.4 CPU並列。旧run_ad_method.pyや旧TSPは別版である。

OSRM/VeRyPy/OR-Toolsの外部依存、保存PBF/graph/注釈経路、output内のdata_access.py/ノード索引が必要。現行ToCの多くは未追跡で公開READMEにも未掲載のため、公開cloneだけの一括完全再現を主張しない。実行予定コマンド・入口はREADME_REVISION_PLANと索引へ整理したが今回実行していない。

旧単一車両TSP、EV電力量/電池材料、旧H1〜H3/面接研究は履歴参照として残し、現行の方法/仮説/結果へ転記しない。過去資料や結果を削除する提案はしない。

既存README冒頭の「Nの解釈HOLD」「全体ソルバー未実装」等は後続の凍結需要・共通基盤・限定実行とずれている（CONFLICT：F005/F007の版差分）。EV/面接部も現行の研究内容と混同せず履歴へ案内する。

## 10. 保全

状態：**VERIFIED／意図しない既存変更0**。既存のREADME.mdと.gitignoreの未コミット変更を開始時のまま保持。HEAD・origin URLも不変。新規作成はこのディレクトリの4 Markdownのみ。

|保全対象|件数|開始/終了の照合|集約SHA256|
|---|---:|---|---|
|README|3|一致|d700274286f2ec68df0717960cf1ca459e97d15abc80cf78f4ed332faf2a482d|
|code_config_docs|245|一致|0b6993185896bf87db663fa305c4de528e18b94ccb0c52a517e4f411e9b6909d|
|frozen_demand|8|一致|1de446b6052e41a92685d5519910d723e8dfd49488a33dcab581d4ab36df087a|
|existing_output_metadata|85113|一致|46e2a88542adb10f870152e601da124a28c418e898eded5a419f167536f4dc5c|

code_config_docsはsrc内Python、scripts直下Python、configs内JSON、docs/research内Markdown/JSON。README群はREADME.md/.gitignore/AGENTS.md。凍結8ファイルは現物の内容hashを照合した。既存output 85,113ファイルはパス・bytes・mtime_nsの索引hashを前後照合したもので、全ファイルの内容hashを今回再計算したとはしない。

追加の軽量整合性確認：凍結payload6件＋manifest/checksums/configのソースpin＋SHA256SUMS内容が全一致。S1〜S3のOD配列9ファイルをstdlibのstreaming SHA256で各manifestと照合し9/9一致。OD統計・計画・過去D/W/Tを再計算したものではない。

ローカルファイルリンク514件を照合し、欠損0。索引対象322ファイル。HTTP URLの全件到達性検査とは異なる。リンク確認後に新規監査4文書内だけへ本保全記録を追記した。

今回実行したソルバー/量子回路/予備実験/本実験/図生成/既存テストはすべて0。保存済み246テスト・各監査の件数は過去の検証証拠であり今回の実行結果として数えない。

成果物は本書、FILE_LINK_INDEX、README_REVISION_PLAN、OPEN_DECISIONSの4 Markdownのみ。既存README/コード/設定/需要/OD/結果は変更せず、commit/push/リモート変更なし。

- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json): 9e1b0ba8afed05f9fbae6ff725489a3e0d602bf8b1e9f19e5b9e8a6a8eada776
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md): b1cddc9395ab717a2197f7d0f39b8a716f8064321a7f66d94320fc101ba115a8
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/REGIONAL_ALLOCATION.csv](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/REGIONAL_ALLOCATION.csv): 317299aab117a0de99e0fc6127a1c060d115e15ff7acabd209ac9e4bad46b881
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S1.csv](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S1.csv): e3c2040766636b2cbd6de670f93a5356ba893dfbb8417bf1c136a5f785172398
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S2.csv](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S2.csv): 7c8fcecabf34545d3021d53cf774e99df9d33967fcffdf324cd07f53e95a3cb2
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S3.csv](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/S3.csv): b8b5b041e724c8337d697a538e9340e45c9cac8e10a55bb088321011913d253d
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/SHA256SUMS](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/SHA256SUMS): b1460b059cbe986d989406903d2802e51b64cf86217b2207d207a14fc07387e4
- [03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/VALIDATION.json](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/VALIDATION.json): 9215b84dc696c56e1789f2600044649a4bd996a7b4eecc730a0a671fc574a931
