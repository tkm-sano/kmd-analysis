# A〜D共通データ監査

2026-11-11。証拠の正本は`output/toc_delivery/common_v1_audit_20261111/`。本書はデータを再生成せずに読取・照合した結果である。

## v1.1改訂

時間条件は全A〜D共通の研究仮定として、積込30分/便、顧客先作業120秒/地点、帰着後準備0分とする。需要・道路の既存監査数値は下記v1.0時点の記録を保全する。現行条件はcommon_conditions_v1_1.json、追加の検証証拠はoutput/toc_delivery/common_v1_1_revision_20261111/。道路・OD・S1〜S3のHOLDは時間仮定変更だけで解除しない。

## 監査範囲と採用順序

開始HEADは8605d5412f6af62229a83095c35ab04c8c7dd9b1。git statusはmainがorigin/mainより7 commit先行し、README.md/.gitignoreに既存変更と大量の未追跡成果を含んだ。初期の完全一覧はGIT_STATUS_BEFORE.txt、既存47,440ファイル・21,422,393,920 bytesのhashはPRESERVATION_BEFORE.jsonへ記録した。リポジトリ内・親階層にAGENTS.mdは見つからなかった。読み取り専用の遠隔HEAD確認は1b00bd7927fa1e7688e4772ac1da9db46d9bac11で、merge/pull/resetはしていない。

README、11/8研究計画DOCX、TOC_DELIVERY_SPEC、11/10凍結需要とpin、11/11のD全関連文書（D_VEHICLE_DAY_*を含む）、現場課題調査、既存需要・道路・OD・シミュレーションコードを確認した。実際の旧道路生成実装の一部は保全領域へ移されており、通常の公開cloneの再現性とローカルで読めた事実を区別する。文書inventoryはaudit_results/DOCUMENT_INVENTORY.json。

|既存資料の値/方針|今回の採用・扱い|
|---|---|
|11/8のNの意味・人口再配分がHOLD|11/10凍結需要v1の一意配送地点を使う。元39,956の町丁目比、PASS34,912から固定抽出済み|
|旧PE/容量216、固定担当、作業102秒、帰庫32400秒|使用しない。1配送単位、60/便、作業120秒、8〜20時へ新規設定で固定|
|計画書の積込20分、7時は候補のままHOLD|今回の指示により30分、初便ready8〜9時均等、準備0分を採択（v1.0の15分から追加指示で改訂）|
|各車2便と空便条件が未確定|最大2便、未使用・1便を許容。使用便は非空|
|Aが代理割当・近傍・FCFS|出典付き実績/参照水準へ置換する方針。代理計画を実績としない|
|Bが一般的貪欲/探索、Dが旧訪問順QAOA|最新D文書のB=VeRyPy CW、C=OR-Tools、D=Huang CG＋AOAを維持|
|既存Dの日列・改善実験|人工小規模の成果を保全。今回の運行値の採用と大規模化は別|
|旧SUMO道路OD・固定担当内中心|新しいOSRM全有向ODに混ぜない|

矛盾する旧文書を上書きしていない。今回のCOMMON_*と共通設定が新入口であり、旧study.jsonのrequire_readyは引き続きHOLDを返す。

## 凍結需要8ファイル

全ファイルは`03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/`。11/10 FILE_HASHES.jsonと実読込bytesのSHA256が全て一致した。既存pin loaderと別実装のCSV検査を両方行い、A〜Dの読込hash一致、ID一意、各1単位、座標有限・範囲、S1⊂S2⊂S3を確認した。

|ファイル|SHA256|
|---|---|
|MANIFEST.json|9e1b0ba8afed05f9fbae6ff725489a3e0d602bf8b1e9f19e5b9e8a6a8eada776|
|SHA256SUMS|b1460b059cbe986d989406903d2802e51b64cf86217b2207d207a14fc07387e4|
|S1.csv|e3c2040766636b2cbd6de670f93a5356ba893dfbb8417bf1c136a5f785172398|
|S2.csv|7c8fcecabf34545d3021d53cf774e99df9d33967fcffdf324cd07f53e95a3cb2|
|S3.csv|b8b5b041e724c8337d697a538e9340e45c9cac8e10a55bb088321011913d253d|
|REGIONAL_ALLOCATION.csv|317299aab117a0de99e0fc6127a1c060d115e15ff7acabd209ac9e4bad46b881|
|READING_CONTRACT.md|b1cddc9395ab717a2197f7d0f39b8a716f8064321a7f66d94320fc101ba115a8|
|VALIDATION.json|9215b84dc696c56e1789f2600044649a4bd996a7b4eecc730a0a671fc574a931|

|系列|地点/需要単位|車両/バース|元監査overall PASS|現実の道路アクセス|
|---|---:|---:|---:|---|
|S1|1000/1000|10/2|1000|全1000地点UNVERIFIED_MODEL_SERVICE_POINT、新研究道路採用HOLD|
|S2|2000/2000|20/4|2000|全2000地点同上|
|S3|4000/4000|40/8|4000|全4000地点同上|

元監査のroad_mapping_statusとroad_reachability_statusも選択地点は全てPASSだった。ただしこれは凍結SUMOモデル内の確認であり、現実の入口・OSRM対応が検証済みという意味ではない。監査元ALL_STOPS_AUDIT.csvのhashはe785f8fe9e26e37a8a8ccc9b047d8eb04138034f7ec5a13bb2e3378ba1178b7b。最終照合はaudit_final/DEMAND_AUDIT.json、ROAD_AUDIT.jsonを正本とし、初回audit_results/も保全する。

## 拠点・道路・OD

既存DEP_006は緯度35.586971、経度139.745306。DEPOT_ROUTING_DEFINITIONと施設freezeで一致するが、proxyのままである。旧SUMO edge617631294/lane617631294_0と位置12.5074mは道路モデル内の代理位置であり、実際の車両用出入口の確認根拠にはしない。

公式[日本自動車ターミナル施設案内](https://www.j-m-t.co.jp/terminal/modal/keihin_map.html)は大田区平和島2-1-1と車アクセスを掲載するが、今回車両入口の数値座標を確定できなかった。構内図画像取得も503で失敗し、未確認のまま保存する。住所・代理座標から入口を推測して採択しない。Depot.entrance_verified=falseの入力は共通実行入口が拒否する。

|道路資産|取得元/日時/版|実測SHA256|
|---|---|---|
|kanto-260716.osm.pbf、476,772,780 bytes|Geofabrik https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf 、OSM日時2026-07-16T20:21:30Z|aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d|
|osm_ota_ward_20260716.osm.pbf、12,218,967 bytes|同rawからcomplete_ways抽出、生成記録2026-07-17T23:19:56+09:00|10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041|

実測hashは既存quality_summaryの記録と一致した。rawの厳密なダウンロード時刻は独立確認できず、上記生成時刻を取得時刻と偽らない。道路source_id=osm_geofabrik_kanto_20260716。旧データは存在するが、OSRM用graph/profile/実行版・生成hashは未整備。現在読める旧ODはSUMO・固定担当/旧施設条件で、S1〜S3の共通OSRM行列として採用できない。

## 整備方法と残る確認

1. 施設案内・地図・必要なら現場確認で車両入口を確定し、座標・根拠・採択日・証拠hashを別保存する。
2. 関東rawまたは余裕を持った抽出範囲からOSRM graphを作る。区境で切ると区外経由の経路や接続が失われ得るため、大田区だけの抽出を自動採用しない。
3. OSRM binary/containerの版・digest、Lua profileとhash、extract/contract等のコマンド、生成物hashをmanifestへ固定する。公式v26.5.0仕様にはdistance,duration同時tableのCH例があるため、まずCHの小例で対応を確認し、未対応の構成は採択しない。
4. 凍結地点をnearestへ対応付け、複数候補・snap距離・hint・node候補・道路アクセス・一方通行/車線を確認する。原需要は変更せず別表に保存する。異常なsnap、未確認、未接続はHOLDとする。
5. 同じgraph/hint/profileで全有向ODをブロック生成し、raw応答と前処理wall秒を保存する。null・欠損・snap変化を検出する。推定値・直線距離による補完を禁じる。
6. tableとrouteの独立経路照合、小規模実道路の時刻整合、全OD到達性を確認してからS1の可行参照計画へ進む。現在は実道路route照合をしていない。

公共OSRMへの要求は0件。ローカルtable生成器はstubで検証済みで、実サーバE2Eは未検証。道路・ODの実データ判定はHOLDである。

## S3資源の事前評価

4001地点、16,008,001ペア。float64距離+float64時間+bool到達性の生配列は272,136,017 bytes（259.53MiB）で、.npy header・metadata・raw応答・ファイルシステム分は別。100×100ブロックなら最大41²=1681 table要求、最大200座標/要求（同一IDは重複除去）。1応答を処理してmmapへ書くため、16M個のPython辞書を保持しない。

ブロック監査の一時配列は概ね数MiBで、mmapページcache・OSRMサーバgraph・OSRM構築・solverメモリは別に必要である。Dの現入力bridgeは既存dense km行列コピーと全travel tupleを作るので、S3向け省メモリsolver接続を達成したとはしない。

実生成時間は未計測でnull。必要時間はgraph構築時間＋1681×実測block秒＋hash/I/O秒として、ローカルCHで複数ブロックの分位点を測ってから見積もる。OSRM構築のpeak RSSも未測定であり、rawファイルサイズだけでRAMを予測しない。先に入口・profile・snapが確定する必要がある。
