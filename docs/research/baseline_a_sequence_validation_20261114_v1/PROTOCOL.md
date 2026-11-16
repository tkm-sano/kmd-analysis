# Aの訪問順生成に関する外部実績検証：事前固定手順

登録日は2026-11-14である。[固定設定](../../../configs/toc_delivery/a_sequence_external_v1.json)のSHA256は`cede2761a8bf75e19e30a4c49a8d48543303993c630125e6733bcbc81305dd6d`である。現行A2本体・凍結需要・道路・S1〜S3の結果は変更しない。本調査前に実績順序を使った係数推定・方法選択は行っていない。旧調査にAmazon trainingの地点数集計は存在するため、データセットそのものを初めて見たとは主張しない。

## 対象と検証できる範囲

Amazonの2018年米国5都市の公開実績を用い、担当配送先が与えられたときの訪問順生成だけを検証する。これはA本体を所与の割当リスト読込に置き換える処理ではない。多車両割当、容量60、最大2便、FCFS、大田区のD/W/Tはこのデータによって検証しない。

公式schemaには地点間の履歴平均移動時間があり、道路距離行列はない。次の2つを明確に区別する。

- **主：NN_time**：現行Aの`construction._nearest`をそのまま呼び、費用だけを公開移動時間に投影する。A2の道路距離最近隣そのものの検証ではない。
- **補助：NN_geodesic**：同じ規則を座標の大円距離へ適用する。匿名化座標に基づく診断であり、実走行距離Dではない。道路最短距離の代用として研究結果へ代入しない。

各公開routeの全Dropoffを保持し、Stationを起点として順序を生成する。容量で120地点に縮小したり、2便に分割したりしない。配達stopは荷物個数・世帯数・一意住所数とは必ずしも一致しない。時間窓・planned_service_timeの制約は今回の順序生成器には追加しないため、実務との差に対する代替説明となる。

## データ取得・利用

[AWS公式登録](https://registry.opendata.aws/amazon-last-mile-challenges/)、[データ論文](https://doi.org/10.1287/trsc.2022.1173)、[公式schema](https://github.com/MIT-CAVE/rc-cli/blob/main/templates/data_structures.md)を確認する。著作権者はAmazon.com, Inc.または関連会社、データのライセンスはCC BY-NC 4.0である。無署名の公開HTTPSで取得し、AWSアカウント・有料計算を使わない。原本は既存研究データと分けてローカルcacheへ保存する。

取得対象はtrainingに付属する小規模model_apply/model_scoreサンプルと公式evaluationのroute、travel_times、actual_sequencesの計6ファイルである。合計上限1,000,000,000 bytes、各ファイル600秒、解析300秒、native thread1とする。ファイルSHA256、ETag、Last-Modified、URL、byte数・取得時間を保存する。

原schema・公式採点コード・利用条件は`sources/`へ保存する。公式scorerのrepository LICENSE URLは取得404であり、その利用条件を本リポジトリのApacheライセンスとして扱わない。採点コードは研究上の参照・照合用である。自作の採点実装は独立した反復DPを用いる。

## 対象選択と情報の分離

実績順序を意味のあるデータとして解析する前に設定を固定する。原ファイルのbyte hash検証は先に行うが、actual JSONの順序は生成器に渡さない。

1. pilotはtraining sampleから`SHA256(seed|route_id)`順で2ルートとする。実装動作確認専用であり、係数・方法の調整に使わない。
2. evaluationはメタデータだけで、`SHA256(seed|station)`順に最大10拠点、その中で`SHA256(seed|station|date)`順に最大2日、各日に`SHA256(seed|route_id)`順に最大2ルートを選ぶ。最大40ルート、20拠点日である。native sampleのroute品質を使った選別はしない。
3. Stationが1つ、Dropoffが2つ以上、型・座標が適格であることをメタデータ段階の条件とする。除外は全件理由を残す。結果・所要時間・採点による除外は行わない。
4. 全選択ルートについてNN_time、NN_geodesic、無作為順序10個を生成し、全地点ちょうど1回・Station先頭を検査する。各random seedは固定seedとroute IDから派生する。
5. 順序ファイルとSHA256を`PROPOSALS_FROZEN.json`に保存してからactual_sequencesを解析する。pilotとevaluationのID重複は拒否する。後から方法や対象を選び直さない。

固定規則を評価するため、今回のpilotでモデル学習・校正は行わない。公式training/evaluationの分割を使うが、異なる拠点・日付の完全分離を保証する設計ではなく、地域移転の検証とは呼ばない。

## 指標・対照・統計

主指標は公式Amazon sequence score（sequence deviation × normalized ERP per edit）である。反復DPによる自作実装を公式コードの小規模全順列で照合する。公式normalizerはnested dictを変更するため、参照比較時にはdeepcopyする。

補助指標はsequence deviation、有向arc一致率、ゾーン再進入、公開行列上の閉路移動秒・実績順に対する比、正規化Kendall逆転率である。ゾーン再進入は既知zoneの地点部分列を連続区間に圧縮し、区間数−ユニークzone数とする。欠損zone数・既知地点数を併記し、完全なゾーン遷移を観測できたとは扱わない。

公式sequence deviationは、実績のDropoff順を完全反転した場合にも0となり得る。したがって公式scoreが小さいことだけで同じ順序・実務への適合を認定せず、有向arcとKendallも報告する。短い移動時間だけでも実務代表性は認定しない。

同じルートのrandom10個の平均を対照とし、主効果はNN_time score−random平均scoreである。拠点日ごとに差を平均し、拠点日を単位とする5,000回bootstrapの記述的95%区間を出す。上端<0なら「この標本でrandomより実績に近い」という限定した結果とする。NN_geodesicは補助分析であり、多数指標から有意なものを主結論に選ばない。拠点・都市間の相関や標本設計の限界から、米国全体・日本・大田区への母集団推論とはしない。

実務との同等性に対する根拠ある許容幅は未設定である。したがって同等性PASS、現行A2道路距離版の検証PASS、A全体の代表性PASSを出すことはできない。結果が弱ければそれをそのまま報告し、A2を恣意的に弱く/強く変更しない。

## 成果・次段階

選択ID、生成順序、全route/対照別指標、集計、失敗、入力/出力/コードhash、環境を保存する。解析wallは分析処理時間であり、A_programや人手計画時間として扱わない。

この検証後に必要な実務記録は、対象/類似ToC拠点の割当、便、距離、帰着、ready、積込開始/終了である。未取得項目のテンプレートを用意するが、事業者への連絡は行わない。RQ・仮説や既存の代表性判定は自動改訂しない。
