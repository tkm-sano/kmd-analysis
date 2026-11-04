# 図表計画・掲載用キャプション

図番号は既存章構成に合わせた仮番号であり、DOCX編集時に相互参照を更新する。図のPNG/SVG/PDFを各10点保存した。表はtables/のCSV/MDから再利用する。画像は実際に閲覧し、文字化け・切れ・重なりを確認した（VISUAL_REVIEW.csv）。軸で省略した条件は下記キャプションと一体で掲載する。

## F3-1 計画取得から固定OD配送成果までの対応

計画取得から固定OD配送成果までの対応。対象：78問題×36条件、配送先4件／判断。各段階の件数を別集計。時間不変OD・102秒サービス。実配送成功を示さない。

- 掲載案：3.8節。
- 軸・単位・比較方向：件、% / 政策採用対古典単独。
- データ選択：POLICY78。
- 集計：各段階の件数を別集計。
- 読み取れる内容：取得失敗と採用期限による切替。
- 読み取れない内容：実配送成功を示さない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv`。SHA256 `663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302;1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1`。
- 生成物：figures/F3_1.png;figures/F3_1.svg;figures/F3_1.pdf。

## F3-2 材料・設計・質量・電力量の証拠到達範囲

材料・設計・質量・電力量の証拠到達範囲。対象：T08旧460主軌跡；T09 183設計行。モデルごとに分離。材料参照値は量子計算成果ではない。完成パック・実EVの改善を示さない。

- 掲載案：3.9節。
- 軸・単位・比較方向：kg、Wh / LP−S。
- データ選択：T08 / T09 separate。
- 集計：モデルごとに分離。
- 読み取れる内容：条件付き接続と未知部材の位置。
- 読み取れない内容：完成パック・実EVの改善を示さない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T09_COMPONENTS_183.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv`。SHA256 `4bdffa7249a93dba1f8e585769d94cd33f20305de223f0418cfedbb9a316960a;f9bb9823fe500547c3c1fe002af769f7ad1a81ab7fdd8fbb34c1bb7ff3a362d7`。
- 生成物：figures/F3_2.png;figures/F3_2.svg;figures/F3_2.pdf。

## F5-1 規模・設定別の古典初期解に対する目的値差

規模・設定別の古典初期解に対する目的値差。対象：460入力、8設定、10測定rep／入力設定。測定repを入力内平均後、規模内入力等重み。CPU計算・支持・予算は設定間で異なる。量子計算一般の優劣・配送時刻差を示さない。

- 掲載案：5.1節。
- 軸・単位・比較方向：秒 / 正は目的値悪化。
- データ選択：scale R0..R5。
- 集計：測定repを入力内平均後、規模内入力等重み。
- 読み取れる内容：小規模の改善例と大規模側の平均悪化。
- 読み取れない内容：量子計算一般の優劣・配送時刻差を示さない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv`。SHA256 `229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03`。
- 生成物：figures/F5_1.png;figures/F5_1.svg;figures/F5_1.pdf。

## F5-2 厳密参照値のある入力の最適性ギャップと参照範囲

厳密参照値のある入力の最適性ギャップと参照範囲。対象：407/460入力；R4 57/78、R5 38/70。repを先に平均、参照あり入力を規模内平均。53入力のgapを補完しない。未参照53入力を含む最適性を示さない。

- 掲載案：5.1節。
- 軸・単位・比較方向：%、入力数 / 100×(目的値−厳密参照値)/厳密参照値。
- データ選択：exact available only。
- 集計：repを先に平均、参照あり入力を規模内平均。
- 読み取れる内容：参照範囲内の規模別品質差。
- 読み取れない内容：未参照53入力を含む最適性を示さない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_EXACT_REFERENCE_COVERAGE.csv`。SHA256 `229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03;7b1d3632a219087ad9ec5f62e9be63d6e2effcf69a708133705f7f5d2df70eae`。
- 生成物：figures/F5_2.png;figures/F5_2.svg;figures/F5_2.pdf。

## F5-3 計算時間の工程別記述

計算時間の工程別記述。対象：3,680保存fit；10測定repを重複加算しない。各規模の固有fit平均。CPUシミュレータの工程記録、QPU時間ではない。同一予算・同一ハードウェアの速度比較ではない。

- 掲載案：5.1節。
- 軸・単位・比較方向：秒 / 設定別、工程別。
- データ選択：wall fields; FIT / FINAL_VALIDATION / RESULT separate。
- 集計：各規模の固有fit平均。
- 読み取れる内容：最終検証を省くと時間評価が変わる。
- 読み取れない内容：同一予算・同一ハードウェアの速度比較ではない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_RESOURCE_SCOPE_SUMMARY.csv`。SHA256 `5ab225e5a1f1fa6ad3fab69127f3dd2a685cbc9f49b8d7ea144609a5897fffd0`。
- 生成物：figures/F5_3.png;figures/F5_3.svg;figures/F5_3.pdf。

## F5-4 経路変更と出発変更の機構比較

経路変更と出発変更の機構比較。対象：64問題×36条件×4arm＝9,216 arm。各問題の4配送先平均を64入力で等重み平均。反実仮想比較であり政策採用結果とは別。利用可能時刻より早い出発を実運用可能とはしない。

- 掲載案：5.2節。
- 軸・単位・比較方向：秒 / QC/CQ/QQ − CC；正は遅い。
- データ選択：MECHANISM64, all36。
- 集計：各問題の4配送先平均を64入力で等重み平均。
- 読み取れる内容：経路・出発・組合せの差。
- 読み取れない内容：利用可能時刻より早い出発を実運用可能とはしない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_MECHANISM_SUMMARY.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_MECHANISM_COMPARISON.csv`。SHA256 `ef687f28a91f87bfe16fa48d3a2201422b8776a05bd7dcf44774a64ea50f110a;5152d4b060f3f68b54f8f058bbaeb32571c4d658731d78fc8619192efae77f89`。
- 生成物：figures/F5_4.png;figures/F5_4.svg;figures/F5_4.pdf。

## F5-5 早着待機による遅延吸収と定時指標の飽和

早着待機による遅延吸収と定時指標の飽和。対象：左64×36中768条件、右78問題×36条件の問題別最小。左は配送順ごとの平均；右は問題別最小の分布。固定OD、同一経路、102秒サービス。現実交通で同じ吸収が起こるとはいえない。

- 掲載案：5.2節。
- 軸・単位・比較方向：秒、分、問題数 / 出発のみCQ−CC／deadline−complete。
- データ選択：CC/CQ positive departure and POLICY78。
- 集計：左は配送順ごとの平均；右は問題別最小の分布。
- 読み取れる内容：最終配送先で768/768条件の遅延吸収、政策最小余裕3133.46秒。
- 読み取れない内容：現実交通で同じ吸収が起こるとはいえない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv`。SHA256 `1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1;663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302`。
- 生成物：figures/F5_5.png;figures/F5_5.svg;figures/F5_5.pdf。

## F5-6 未知部材による軽量化の相殺・逆転条件

未知部材による軽量化の相殺・逆転条件。対象：2代表設計×既存7未知質量差条件。同じ質量条件の重複を除去し、既存点を直線で結ぶ。未知質量差は未実測；bは代表設計の既知部材差。T09完成パックの質量は確定しない。

- 掲載案：5.3節。
- 軸・単位・比較方向：kg / LP−S=b−δ。
- データ選択：B015/B051 saved seven probes。
- 集計：同じ質量条件の重複を除去し、既存点を直線で結ぶ。
- 読み取れる内容：δ<bで軽量、δ=bで相殺、δ>bで逆転。
- 読み取れない内容：T09完成パックの質量は確定しない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_BRIDGE_MASS_DC_FULL.csv`。SHA256 `d0771ef9c94a28c7a2373ebb8bcbb068aae923730ce25cb0e32b2362c82fc90c`。
- 生成物：figures/F5_6.png;figures/F5_6.svg;figures/F5_6.pdf。

## F5-7 T08簡略質量モデルの固定軌跡DC感度

T08簡略質量モデルの固定軌跡DC感度。対象：旧460主軌跡、2 Crr条件。個別分布と総量加重率を区別。質量差5.448297415kg、速度固定、回生・補機なし。実EV改善・現行BのDCではない。

- 掲載案：5.3節。
- 軸・単位・比較方向：% / 100×(LP−S)/LP DC。
- データ選択：CLASSICAL COND_S200_REF。
- 集計：個別分布と総量加重率を区別。
- 読み取れる内容：条件付き小幅なDC感度。
- 読み取れない内容：実EV改善・現行BのDCではない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_PAIRED_DIFFERENCES.csv`。SHA256 `b5957b5c4c9cd6649bd25cff433222ef53187618369dc5a8807491f917679f8c`。
- 生成物：figures/F5_7.png;figures/F5_7.svg;figures/F5_7.pdf。

## FA-1 T09代表設計と未知部材差の条件付きDC感度

T09代表設計と未知部材差の条件付きDC感度。対象：各点旧460保存速度、全25,760条件行。各条件の総量加重率。1200/1400kgは既存感度の参照質量であり完成パックやB車両ではない。T08とT09の完成パック性能比較ではない。

- 掲載案：付録C節。
- 軸・単位・比較方向：kg、% / 100×(基準DC−条件DC)/基準DC。
- データ選択：B015/B051, 7 original probes, 2 masses,2 Crr。
- 集計：各条件の総量加重率。
- 読み取れる内容：未知部材差・参照質量・Crrに依存するDC符号。
- 読み取れない内容：T08とT09の完成パック性能比較ではない。
- 元データ：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_BRIDGE_MASS_DC_FULL.csv`。SHA256 `d0771ef9c94a28c7a2373ebb8bcbb068aae923730ce25cb0e32b2362c82fc90c`。
- 生成物：figures/FA_1.png;figures/FA_1.svg;figures/FA_1.pdf。

## 表の掲載計画

|仮番号|ファイル|掲載案・対象|
|---|---|---|
|表3-1|T3-1_COHORTS.csv|3.4：A/B/Cの系列・統計単位・未評価範囲|
|表5-1|T5-1_B_OBJECTIVE.md/csv|5.1：全8設定×6規模の秒差、改善・同値・悪化率|
|表5-2|T5-2_B_EXACT.md/csv|5.1：407/53とgapの分母|
|表5-3|T5-3_RESOURCE_SCOPES.md/csv|5.1本文は工程例、完全表は付録。CPU/wall/RSSの保存範囲|
|表5-4|T5-4_T08_DC.md/csv|5.3：2Crr別の質量・総Wh差・加重率・個別率平均|
|付表A-1|TA-1_ALL_36_POLICIES.md/csv|全36政策の値・率・時刻差を無選択で掲載|
|付表C-1|TA-2_C_BRIDGE.md/csv|全56感度条件、各460軌跡|
|付表S-1|TA-3_SUPPLEMENT_INTERVALS.md/csv|全1,176補助区間。主結果のp値表にはしない|

同値6設定はMEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2、ACTIVE_ADJACENT_P3_GRIDである（図F5-1では重なりをまとめて表示）。図F5-2の数値は小数第2位丸めで、0.00%表示は丸めである可能性を含むため、厳密一致は表のoptimal_match_percentを用いる。図F5-3の各panelで尺度が異なることを保持する。図FA-1の2Crr曲線は接近しているが、元数値は付表C-1で識別可能である。

生成コマンドは `.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/make_figures.py` である。図とCSVの対応・SHA256はFIGURE_SOURCE_MAPPING.csv、出力自身のhashはSHA256_MANIFEST.csvを参照する。対象環境ではSVG文字をpath化しPDFへフォントを埋め込み、PNGを220dpiで出力した。Word上の縮小率・ページ組版は次回確認する。
