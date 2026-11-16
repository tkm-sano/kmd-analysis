# 共通実道路ODの検証

2026-11-12。S1/S2/S3入力生成・全OD検査：GO（地図と静的profileによる研究用道路モデルの範囲）。現地進入可否の保証ではない。

道路は既存関東PBF、OSM timestamp `2026-07-16T20:21:30Z`、raw SHA256 `aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d`。元の取得記録は残っておらず、2026-07-17の保存日とPBFヘッダを区別している。推定取得日を実測運行日とはしない。
ROAD_METADATAの年月日付きsource_urlは保存ファイル名からの推定で、元のダウンロードURLを確認した記録ではない。現在の公開URLから同日版を再取得できるとは確認できなかった。ヘッダのGeofabrik replication baseを根拠とし、再現時は保全済みPBFとhashを使う。詳細はsources/OSM_SOURCE_PROVENANCE_ADDENDUM.json。latestを同版として代入しない。
OSRM 5.27.1、標準car.lua SHA256 `cb3df0546318665609606b746a1297f3d65ca3c2ff825f8a6f3c57247d86a2d3`、MLD。公式GHCR amd64 image digestはsources/OSRM_RUNTIME_MANIFEST.jsonに固定。Docker権限不足をユーザー空間の同じ公式バイナリで解決した。無料ローカル処理であり、公共OSRMへ大量要求していない。

OSM/OSRM出典：[OSM利用条件](https://www.openstreetmap.org/copyright)、[Geofabrik関東](https://download.geofabrik.de/asia/japan/kanto.html)、[OSRM Table/Route仕様](https://project-osrm.org/docs/v26.4.0/http)。© OpenStreetMap contributors。OSMはODbL、OSRM/VeRyPy等のソフトウェアライセンスは取得元manifest/LICENSEを参照。

拠点は[日本自動車ターミナル公式京浜案内](https://www.j-m-t.co.jp/terminal/keihin.html)と[公式構内図](https://www.j-m-t.co.jp/images/terminal/keihin/kei_map1.png)、OSM way235963579/node2440398083を照合し、西側中央の車両進入通路 `(lon139.7429862, lat35.5863301)` を採用。図面に基づく入口モデルで位置誤差目安20m、現地測量ではない。根拠はDEPOT_ENTRANCE_DECISION.json、原画像・地物図はsources/。

座標系はEPSG:4326、lon/lat。凍結地点の元座標を維持し、5候補から道路属性・同一OSM node pair・100m上限を検査。産業道路の地上trunk2wayは個別に通行属性を確認した例外で、全trunkを無条件許可していない。初回12地点の非連結を検出し、最大100候補へ拡張して同じ100m内の拠点往復可能候補を採用。元需要の間引き・移動はない。アクセス権の現地確認や建物搬入口確認を済ませたとはしない。

最終全4001地点・16,008,001組、到達不能0、距離非対称セル15,734,350。全自己距離/時間0、非負・有限・単位m/sを検査。**採用ODは全ordered pairをRoute APIから生成し、同じRoute objectのdistance/durationと注釈node列を保存した。Table距離は採用していない。**

初回Table版では負距離11組を検出し、さらに代表S1の91便中12便でRoute距離と不一致（固有7arc、0.8〜41.8m差、時間一致）。OSRM26.11.0を同じPBF/同じprofileで再構築しても差を再現した。Table値や差の原因を推定で正当化せず、初回入力/全結果を`output/toc_delivery/ad_pipeline_20261112/`に保全しTABLE_DISTANCE_REJECTION.mdで正式採用を保留した。最新版graphは診断専用で、採用データへ混在させていない。

v2はRoute全組方式へ変更した。S1→S2→S3の順に生成し、既に得た同じID pairの経路をOD hash/元block参照で引き継ぐ。各pairの元座標+同じhint、返却snap同一性、Routeの非負distance/duration・annotated nodesを確認し、推定速度・直線距離・0埋めを使わない。保存したS1可行計画の全497便で、連結Routeの全legとpair ODが距離/時間とも丸め許容0.25m/0.25秒以内に一致（497/497）。顧客停車時の方向変更を許す`continue_straight=false`という共通ODモデルの仮定を明記する。

生成器とは別実装で、全21,014,003件の保存pair recordを配列と照合した。注釈付き実Route応答16,008,001組と祖先参照5,006,002組のID・hash・距離/時間・snap・node列を確認し、S1⊆S2⊆S3の3配列が全組で同一と検証。ALL_ROUTE_DATA_INDEPENDENT_AUDIT.jsonを参照。

25×25のblock、S3は25921block。gzip原Route応答・SHA256・context pin・mmapで再開する。S1は4thread、その後8fork worker/同じOSRM graphの8threadへ実行資源だけを変更した。OD_RESOURCE_REVISION_1.jsonに停止前後と変更しない条件を記録。キャッシュの全hashと完成配列hashを確認し、既完成S1はそのまま再利用。S3段階wallは1336.650秒で、S1/S2やgraph構築を含む全取得時間ではない。全段階のROUTE_OD_BUILD*RESOURCES、各route_S*/CHECKPOINTへ実測を保存した。

|規模|地点|OD組|3配列bytes|MiB|OD SHA256|
|---|---|---|---|---|---|
|S1|1001|1002001|17034401|16.245271|9b90a13dc3bfd1a5e50afb3c6eaf5070a043b79695da8b4643a2eed5332b0280|
|S2|2001|4004001|68068401|64.915086|81755ba57345f706182a13fc13e2a0f0d4df793064ca77bbf57f455b17c26345|
|S3|4001|16008001|272136401|259.529496|254bb8f3fb28d86419f36ad6814efbad15d88822a3186952e79d53f40c864e81|


S1/S2の既計算pairをS3へ引き継ぐので、重複するID pairの距離/時間は同一。地点順とfingerprintを固定し、全方法は同じinput.json/manifest/npyを読む。入力hashとOD hashはCOMMON_BUNDLES.json/比較CSVに記録。S3の3配列は約260MiB。関東graphは約3.6GB、graph処理最大RSSは約3.6GiB。道路データ・profile・全graphのhashと生成コマンドはROAD_METADATA.jsonに保存。

注意：car profileの静的速度はモデル仮定。weight_name=routabilityを原応答に残しており、仕様上のfastest_same_routeはOSRM profileによる経路選択を指す。duration単独の数学的最小性を証明していない。渋滞・時刻変動・全車両の寸法規制・実走行距離は表していない。徒歩区間を道路ODへ追加しない。

証拠根：`output/toc_delivery/ad_pipeline_20261112_route_v2/`。設定：`configs/toc_delivery/ad_pipeline_v2_route.json`。実行前計画：`docs/research/A_TO_D_PIPELINE_IMPLEMENTATION_PLAN.md`。共通schema差分：`docs/research/A_TO_D_COMMON_INTERFACE.md`。
