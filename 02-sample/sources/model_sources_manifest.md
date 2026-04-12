# モデルに使用する文献・データの取得一覧

本一覧は、研究計画書で想定されているモデルの各構成要素に対応する公式データ源および主要文献を、実際に参照できるURL付きで整理したものである。

## 1. まず使うべき公式データ

### 1. 日本標準産業分類 第13回（平成25年10月改定）の概要

- 役割: 金属素材群・化学/高分子素材群・無機素材群への再編基準

- 優先度: 必須

- 機関: e-Stat / 総務省

- 表番号・ID等: 分類改定概要

- 備考: 2020年国勢調査の産業分類整合を優先するなら第13回改定を基準にするのが安全。

- URL: https://www.e-stat.go.jp/classifications/terms/revisions/10/03


### 2. 日本標準産業分類 改定の状況一覧

- 役割: 将来の分類対応表作成や第13回→第14回の対応確認

- 優先度: 補助

- 機関: e-Stat / 総務省

- 表番号・ID等: 改定状況一覧

- 備考: 主分析の基準分類にはしないが、将来更新時の対応付けに有用。

- URL: https://www.e-stat.go.jp/classifications/terms/revisions/10


### 3. 令和2年国勢調査 調査の結果

- 役割: 使用表の全体位置づけ確認、公表区分の確認

- 優先度: 必須

- 機関: 総務省統計局

- 表番号・ID等: 結果総覧

- 備考: 従業地・通学地集計、抽出詳細集計の入口ページ。

- URL: https://www.stat.go.jp/data/kokusei/2020/kekka.htm


### 4. 令和2年国勢調査 調査結果の利用案内（ユーザーズガイド）

- 役割: 表検索、利用上の注意、分類事項一覧の確認

- 優先度: 必須

- 機関: 総務省統計局

- 表番号・ID等: u_guide_2020.pdf

- 備考: 統計表の取得手順と引用・加工時の注意の確認用。

- URL: https://www.stat.go.jp/data/kokusei/2020/kekka/pdf/u_guide_2020.pdf


### 5. 従業・通学市区町村，男女別通勤者・通学者数－全国，都道府県，市区町村（常住地）

- 役割: 起点地域から主要都市への流動量の原表

- 優先度: 推奨

- 機関: e-Stat / 総務省

- 表番号・ID等: 表6-1 / 統計表表示ID 0003454527 / file lid 000001296018

- 備考: 通勤者と通学者が合算されるため，就業流動に限定する主分析では6-2の併用が望ましい。

- URL: https://www.e-stat.go.jp/index.php/stat-search/database?cycle=0&layout=datalist&month=24101210&statdisp_id=0003454527&tclass1=000001136469&tclass2val=0&toukei=00200521&tstat=000001136464&year=20200


### 6. 従業・通学市区町村，男女別通勤者数（15歳以上）－全国，都道府県，市区町村（常住地）

- 役割: 通勤者に限定した起点地域→都市の基礎流動量

- 優先度: 必須

- 機関: e-Stat / 総務省

- 表番号・ID等: 表6-2

- 備考: 研究対象が就業流動であるため，6-1よりこちらが主表に適する。

- URL: https://www.e-stat.go.jp/stat-search/files?collect_area=000&cycle=0&layout=datalist&page=1&result_page=1&stat_infid=000032214494&tclass1=000001136469&tclass2val=0&toukei=00200521&tstat=000001136464


### 7. 産業（大分類），従業地・通学地別就業者数（15歳以上）－全国，都道府県，21大都市，21大都市の区，県庁所在市，人口20万以上の市（常住地）

- 役割: 起点地域別に，どの都市へ，どの産業の就業者が向かうかを産業大分類レベルで取得

- 優先度: 最重要

- 機関: e-Stat / 総務省

- 表番号・ID等: 表9 / 統計表表示ID 0003454532

- 備考: 七都市を含む。公開表の中では，研究計画の起点地域×都市×産業群に最も近い核データ。

- URL: https://www.e-stat.go.jp/index.php/stat-search/database?cycle=0&layout=datalist&page=1&result_page=1&statdisp_id=0003454532&tclass1=000001136469&tclass2val=0&toukei=00200521&tstat=000001136464


### 8. 利用交通手段の種類数・利用交通手段，常住地又は従業地・通学地別通勤者・通学者数（15歳以上）－全国，都道府県，市区町村

- 役割: 常住地または従業地側の自動車依存度指標の構成

- 優先度: 必須

- 機関: e-Stat / 総務省

- 表番号・ID等: 表17-2 / 統計表表示ID 0003454513

- 備考: 起終点対ごとの直接値ではないため，旅客地域流動調査等と補完して用いるのが妥当。

- URL: https://www.e-stat.go.jp/dbview?sid=0003454513


### 9. 男女，産業（中分類）別就業者数（15歳以上）－全国，都道府県，21大都市，21大都市の区，県庁所在市，人口10万以上の市（従業地・通学地）

- 役割: 化学工業，プラスチック製品，ゴム製品，窯業・土石製品，鉄鋼業，非鉄金属製造業などを用いた三産業群再編

- 優先度: 推奨

- 機関: e-Stat / 総務省

- 表番号・ID等: 抽出詳細集計 表18-3 / 統計表表示ID 0003464368

- 備考: 抽出詳細集計なので標本誤差を含む点に注意。

- URL: https://www.e-stat.go.jp/stat-search/database?layout=datalist&page=1&statdisp_id=0003464368&tclass1=000001136468&toukei=00200521&tstat=000001136464


### 10. 貨物・旅客地域流動調査

- 役割: 広域移動関係，自動車依存度，地域間移動構造の補助把握

- 優先度: 推奨

- 機関: 国土交通省

- 表番号・ID等: 統計表入口

- 備考: ODの補助校正に有用。鉄道・自動車・海運・航空の地域間流動を扱う。

- URL: https://www.mlit.go.jp/statistics/details/sample03_2_00035.html


### 11. 石油製品価格調査 調査の結果

- 役割: ガソリン・軽油等のエネルギー費用系列

- 優先度: 必須

- 機関: 資源エネルギー庁

- 表番号・ID等: 週次ファイル（1990年以降）

- 備考: 週次の長期Excelファイルあり。通勤コストの燃料費部分に直接使用可能。

- URL: https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/results.html


### 12. JEPX スポット市場（Day Ahead Market）

- 役割: 電力価格シナリオの補助資料

- 優先度: 補助

- 機関: 日本卸電力取引所

- 表番号・ID等: spot / ave_day / ave_year

- 備考: 卸電力価格であり，家庭用充電単価の直接代理ではない。家庭用電気料金を別途置く場合の補助指標として使うのが望ましい。

- URL: https://www.jepx.jp/electricpower/market-data/spot/


### 13. 費用便益分析マニュアル（令和7年8月訂正版）

- 役割: 時間価値原単位・走行経費原単位・感度分析の実務基準

- 優先度: 必須

- 機関: 国土交通省 道路局・都市局

- 表番号・ID等: ben-eki_2.pdf

- 備考: 一般化交通費の構成を公的実務基準に合わせる際の中核資料。

- URL: https://www.mlit.go.jp/road/ir/ir-hyouka/ben-eki_2.pdf


## 2. 上流モデルに入れる主要文献

### 1. Gujarati, T.P. et al. (2023) Quantum computation of reactions on surfaces using local embedding. npj Quantum Information 9, 88.

- 役割: corrosion_interface / interface_adhesion の量子側証拠

- 優先度: 必須

- 種別: 査読論文（OA）

- 備考: 表面反応・局所埋め込み・資源削減の具体例。

- URL: https://www.nature.com/articles/s41534-023-00753-1


### 2. Cao, C. et al. (2023) Ab initio quantum simulation of strongly correlated materials with quantum embedding. npj Computational Materials 9, 78.

- 役割: 金属素材群・周期系材料の量子側証拠

- 優先度: 必須

- 種別: 査読論文（OA）

- 備考: 固体材料シミュレーションへの量子埋め込み。

- URL: https://www.nature.com/articles/s41524-023-01045-0


### 3. Clinton, L. et al. (2024) Towards near-term quantum simulation of materials. Nature Communications 15, 211.

- 役割: 量子条件の資源改善ポテンシャル整理

- 優先度: 必須

- 種別: 査読論文（OA）

- 備考: 材料ハミルトニアンと回路深さの改善例。

- URL: https://www.nature.com/articles/s41467-023-43479-6


### 4. Xu, Z. et al. (2025) Quantum annealing-assisted lattice optimization. npj Computational Materials 11, 4.

- 役割: disorder_search / lattice_optimization の量子側証拠

- 優先度: 推奨

- 種別: 査読論文（OA）

- 備考: 高エントロピー合金の格子最適化。

- URL: https://www.nature.com/articles/s41524-024-01505-1


### 5. Nguyen, N. et al. (2026) Quantum computing for corrosion simulation: workflow and resource analysis. npj Quantum Information 12, 27.

- 役割: 金属素材群の中心候補文献

- 優先度: 推奨

- 種別: 査読論文（OA）

- 備考: 腐食ワークフローと資源分析を同時に提示。

- URL: https://www.nature.com/articles/s41534-025-01171-1


### 6. Joost, W.J. (2012) Reducing Vehicle Weight and Improving U.S. Energy Efficiency Using Integrated Computational Materials Engineering. JOM 64, 1032–1038.

- 役割: 10%軽量化あたりの燃費改善率レンジ（約6–8%）の根拠

- 優先度: 必須

- 種別: 査読論文

- 備考: 軽量化と燃費改善の定量関係の学術的出発点。

- URL: https://link.springer.com/article/10.1007/s11837-012-0424-z


### 7. Isenstadt, A. & German, J. (2017) Lightweighting technology developments. International Council on Clean Transportation.

- 役割: 軽量化技術の制約・コスト・政策レビュー

- 優先度: 必須

- 種別: 政策技術レビュー

- 備考: 燃費・CO2との関係，材料別の動向整理。

- URL: https://theicct.org/publication/lightweighting-technology-developments/


### 8. Santos Silva, J.M.C. & Tenreyro, S. (2006) The Log of Gravity. Review of Economics and Statistics 88(4), 641–658.

- 役割: 対数線形OLSではなくPPMLを採用する理論的根拠

- 優先度: 必須

- 種別: 査読論文（OA）

- 備考: 重力方程式推定の古典的参照。

- URL: https://direct.mit.edu/rest/article/88/4/641/57668/The-Log-of-Gravity


### 9. Santos Silva, J.M.C. & Tenreyro, S. (2022) The Log of Gravity at 15. Portuguese Economic Journal 21, 423–437.

- 役割: 重力モデル推定の近年レビュー

- 優先度: 推奨

- 種別: 査読論文（OA）

- 備考: PPMLの位置づけと発展を整理。

- URL: https://link.springer.com/article/10.1007/s10258-021-00203-w


### 10. Correia, S., Guimarães, P., & Zylkin, T. (2020) Fast Poisson estimation with high-dimensional fixed effects. The Stata Journal 20(1), 95–115.

- 役割: ppmlhdfe 実装，分離診断，HDFEを含むPPML推定

- 優先度: 必須

- 種別: 査読論文

- 備考: 実装論文。固定効果と推定可能性の診断に有用。

- URL: https://journals.sagepub.com/doi/10.1177/1536867X20909691


### 11. Persyn, D. & Torfs, W. (2016) A gravity equation for commuting with an application to estimating regional border effects in Belgium. Journal of Economic Geography 16(1), 155–175.

- 役割: 通勤流動に対する重力方程式の直接的先行研究

- 優先度: 必須

- 種別: 査読論文（OA）

- 備考: 通勤文脈での重力モデルの明示的参照。

- URL: https://academic.oup.com/joeg/article/16/1/155/2413035


## 3. 実装上の最短ルート

1. 産業群の再編は、まず日本標準産業分類第13回改定を基準に固定する。

2. 起点地域→都市の就業流動は、国勢調査の表6-2と表9を中核にする。

3. 自動車依存度は、表17-2と旅客地域流動調査を組み合わせて構成する。

4. 一般化交通費の時間価値・走行経費は、国土交通省の費用便益分析マニュアルに合わせる。

5. 燃料費は資源エネルギー庁の石油製品価格調査、電力価格は必要に応じてJEPXを補助的に使う。

6. 上流のベンチマーク表は、benchmark_evidence_seed.csv を初期種として拡張する。


## 4. 取得に当たっての注意

- 国勢調査の公開表だけで十分に構築できる部分と、抽出詳細集計や補助統計で補う部分を分けて扱うこと。

- JEPXは卸市場価格であり、家庭用充電単価の直接代理ではない。

- 抽出詳細集計は標本誤差を含むため、主分析と補助分析を分けること。

- 引用・転載時は、総務省統計局の出典表示ルールに従うこと。
