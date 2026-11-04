# 図表の反映

元図10点のうち8点を本文、2点を付録Cへ配置した。数値内容を変更せず、4点をA4横向き、残る複数panelを拡大配置した。Word内は19画像、元SVG/PDFは保持した。キャプションは固定文字列で管理し、元原稿と同じくSEQ/REF自動番号は新設していない。全キャプション・本文参照・原図IDを対応付け、bookmarkを一意に付与した。

## 図3-1（F3-1）

計画取得から固定OD配送成果までの対応。配置：本文3.8。画像数：1。

対象：78問題×36条件、配送先4件／判断。各段階の件数を別集計。時間不変OD・102秒サービス。実配送成功を示さない。出典：A_POLICY_DECISIONS_2808.csv,A_DELIVERY_COMPLETION_BY_STOP.csv（電子資料、原図ID 図3-1）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F3_1.png` SHA256 `113ffc8d1331b320fc5ab6870705a59bd5010846be0d176bc1c4caea6329dfc6`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv`、SHA256 `663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302;1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1`。変換：original PNG unchanged; landscape page for legibility。

## 図3-2（F3-2）

材料・設計・質量・電力量の証拠到達範囲。配置：本文3.9。画像数：1。

対象：T08旧460主軌跡；T09 183設計行。モデルごとに分離。材料参照値は量子計算成果ではない。完成パック・実EVの改善を示さない。出典：C_T09_COMPONENTS_183.csv,C_T08_ENERGY_FULL.csv（電子資料、原図ID 図3-2）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F3_2.png` SHA256 `7706a1d9d36195940caa68ae1025a4776c76c05325053985aea3624bac8f520d`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T09_COMPONENTS_183.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv`、SHA256 `4bdffa7249a93dba1f8e585769d94cd33f20305de223f0418cfedbb9a316960a;f9bb9823fe500547c3c1fe002af769f7ad1a81ab7fdd8fbb34c1bb7ff3a362d7`。変換：original PNG unchanged; landscape page for legibility。

## 図5-1（F5-1）

規模・設定別の古典初期解に対する目的値差。配置：本文5.1。画像数：2。

対象：460入力、8設定、10測定rep／入力設定。測定repを入力内平均後、規模内入力等重み。CPU計算・支持・予算は設定間で異なる。量子計算一般の優劣・配送時刻差を示さない。出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv（電子資料、原図ID 図5-1）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_1.png` SHA256 `23c0c176249d3d1815de1606b2dba599bea5e0ab05943cdba4bde7967b9d1022`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv`、SHA256 `229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 図5-2（F5-2）

厳密参照値のある入力の最適性ギャップと参照範囲。配置：本文5.1。画像数：1。

対象：407/460入力；R4 57/78、R5 38/70。repを先に平均、参照あり入力を規模内平均。53入力のgapを補完しない。未参照53入力を含む最適性を示さない。出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv,B_EXACT_REFERENCE_COVERAGE.csv（電子資料、原図ID 図5-2）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_2.png` SHA256 `63a7947a786de0e72a58fce547c0432a7b70c4a2bbc6098e998f817dbf9c70b1`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_EXACT_REFERENCE_COVERAGE.csv`、SHA256 `229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03;7b1d3632a219087ad9ec5f62e9be63d6e2effcf69a708133705f7f5d2df70eae`。変換：original PNG unchanged; landscape page for legibility。

## 図5-4（F5-4）

経路変更と出発変更の機構比較。配置：本文5.2。画像数：1。

対象：64問題×36条件×4arm＝9,216 arm。各問題の4配送先平均を64入力で等重み平均。反実仮想比較であり政策採用結果とは別。利用可能時刻より早い出発を実運用可能とはしない。出典：A_MECHANISM_SUMMARY.csv,A_MECHANISM_COMPARISON.csv（電子資料、原図ID 図5-4）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_4.png` SHA256 `a5e27490208d60c9da8616b3a4e17f7f80cc7639943a9cab0e5cadb9c042c369`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_MECHANISM_SUMMARY.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_MECHANISM_COMPARISON.csv`、SHA256 `ef687f28a91f87bfe16fa48d3a2201422b8776a05bd7dcf44774a64ea50f110a;5152d4b060f3f68b54f8f058bbaeb32571c4d658731d78fc8619192efae77f89`。変換：original PNG unchanged; landscape page for legibility。

## 図5-5（F5-5）

早着待機による遅延吸収と定時指標の飽和。配置：本文5.2。画像数：2。

対象：左64×36中768条件、右78問題×36条件の問題別最小。左は配送順ごとの平均；右は問題別最小の分布。固定OD、同一経路、102秒サービス。現実交通で同じ吸収が起こるとはいえない。出典：A_DELIVERY_COMPLETION_BY_STOP.csv,A_POLICY_DECISIONS_2808.csv（電子資料、原図ID 図5-5）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_5.png` SHA256 `586ceb6978ee4d8f02f59c94d56d44246eb2bc341a745c55b563aac5aedd87b9`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv;/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv`、SHA256 `1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1;663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 図5-6（F5-6）

未知部材による軽量化の相殺・逆転条件。配置：本文5.3。画像数：2。

対象：2代表設計×既存7未知質量差条件。同じ質量条件の重複を除去し、既存点を直線で結ぶ。未知質量差は未実測；bは代表設計の既知部材差。T09完成パックの質量は確定しない。出典：C_BRIDGE_MASS_DC_FULL.csv（電子資料、原図ID 図5-6）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_6.png` SHA256 `6ba4d400f6f45613b183e674a88df2fe8e3f648371e31bc124639a1336285b00`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_BRIDGE_MASS_DC_FULL.csv`、SHA256 `d0771ef9c94a28c7a2373ebb8bcbb068aae923730ce25cb0e32b2362c82fc90c`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 図5-7（F5-7）

T08簡略質量モデルの固定軌跡DC感度。配置：本文5.3。画像数：2。

対象：旧460主軌跡、2 Crr条件。個別分布と総量加重率を区別。質量差5.448297415kg、速度固定、回生・補機なし。実EV改善・現行BのDCではない。出典：C_T08_PAIRED_DIFFERENCES.csv（電子資料、原図ID 図5-7）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_7.png` SHA256 `d7685a80025a92f7bd5cf61b90bb84ec265df5ee62a4dfa28fb0e1505fd7fb8b`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_PAIRED_DIFFERENCES.csv`、SHA256 `b5957b5c4c9cd6649bd25cff433222ef53187618369dc5a8807491f917679f8c`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 付図C-1（F5-3）

計算時間の工程別記述。配置：付録C.1。画像数：3。

対象：3,680保存fit；10測定repを重複加算しない。各規模の固有fit平均。CPUシミュレータの工程記録、QPU時間ではない。同一予算・同一ハードウェアの速度比較ではない。出典：B_RESOURCE_SCOPE_SUMMARY.csv（電子資料、原図ID 付図C-1）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/F5_3.png` SHA256 `3357044e3f2aaf73f23fb924f08b2936c2130afd142ca81f2ea3059bc37b5827`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_RESOURCE_SCOPE_SUMMARY.csv`、SHA256 `5ab225e5a1f1fa6ad3fab69127f3dd2a685cbc9f49b8d7ea144609a5897fffd0`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 付図C-2（FA-1）

T09代表設計と未知部材差の条件付きDC感度。配置：付録C.2。画像数：4。

対象：各点旧460保存速度、全25,760条件行。各条件の総量加重率。1200/1400kgは既存感度の参照質量であり完成パックやB車両ではない。T08とT09の完成パック性能比較ではない。出典：C_BRIDGE_MASS_DC_FULL.csv（電子資料、原図ID 付図C-2）。

元画像 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/figures/FA_1.png` SHA256 `9fcb5fd7fb92e9cf75e5270435ad187fb96eab8fbcb3fd93052fd96854f46fa2`。元CSV `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_BRIDGE_MASS_DC_FULL.csv`、SHA256 `d0771ef9c94a28c7a2373ebb8bcbb068aae923730ce25cb0e32b2362c82fc90c`。変換：unchanged numerical content; panels cropped without recomputation; all original panels retained。

## 表

元8表のセル・XMLを全て保持し、新規19表を追加した（合計27表）。元需要表と旧局所表には題名だけを追加した。新表は繰返し見出し行と行内分割禁止を設定し、ページ跨ぎでヘッダーを再表示する。全1,176補助区間は電子付録S-1を明示し、本文の説明例のみを選び直した主結果として扱わない。

- 表3-1：主分析の対象と評価範囲。4行×4列、出典：T3-1_COHORTS.csv。26親・25需要群の依存を保持。Cの旧460速度とBの460入力は別系列。
- 表3-2：配送需要の生成・採用段階。6行×4列、出典：original DOCX table 1。既存表のXML・セル内容を変更せず題名のみ追加
- 表5-1：規模別の古典初期解に対する平均目的値差。6行×4列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。単位は秒、保存best−古典初期。入力内10repを平均後、入力等重み。同値6設定の名称・全率は付表D-2。
- 表5-2：厳密参照値のカバー範囲。6行×4列、出典：B_EXACT_REFERENCE_COVERAGE.csv。合計460、参照407、未確定53。未確定をgap0にしない。
- 表5-3：保存工程別の平均wall時間。8行×3列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv;B_RESOURCE_SCOPE_SUMMARY.csv。各設定460固有fit。FITは最終検証等を含まない。activeのRESULTとは同範囲でない。最終検証時間は本文と付図C-1。
- 表5-4：T08の固定軌跡DC感度。2行×4列、出典：C_T08_PAIRED_DIFFERENCES.csv。各条件旧460速度、質量差5.448297415kg。実EV・現行BのDCではない。個別率平均は本文と電子資料を参照。
- 付表A-1：旧局所系列の最適値一致と代表回路。9行×5列、出典：original DOCX table 7。既存表のXML・セル内容を変更せず題名のみ追加
- 付表D-1a：政策条件 L=900秒。12行×7列、出典：A_SUMMARY_BY_CONDITION.csv。各行78問題・556PE・312配送先。全行PE/件数率100%、古典対照差0pp。時間差は政策−古典単独。
- 付表D-1b：政策条件 L=3600秒。12行×7列、出典：A_SUMMARY_BY_CONDITION.csv。各行78問題・556PE・312配送先。全行PE/件数率100%、古典対照差0pp。時間差は政策−古典単独。
- 付表D-1c：政策条件 L=7200秒。12行×7列、出典：A_SUMMARY_BY_CONDITION.csv。各行78問題・556PE・312配送先。全行PE/件数率100%、古典対照差0pp。時間差は政策−古典単独。
- 付表D-2a：ACTIVE_ADJACENT_P3_GRID。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2b：COHERENT2_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2c：COHERENT4_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2d：CVAR01_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2e：CVAR10_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2f：GROVER_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2g：GROVER_P3。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-2h：MEAN_P2。6行×6列、出典：B_SUMMARY_BY_SCALE_AND_METHOD.csv。入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。
- 付表D-3a：固定担持。28行×6列、出典：C_CONDITIONAL_MASS_DC_SUMMARY.csv。各行旧460軌跡。δ＝未知部材S−LP差、正味軽量化b−δ。完成パックは未確定。
- 付表D-3b：固定面積。28行×6列、出典：C_CONDITIONAL_MASS_DC_SUMMARY.csv。各行旧460軌跡。δ＝未知部材S−LP差、正味軽量化b−δ。完成パックは未確定。
- 付表E-1：主要分析結果のSHA256。7行×2列、出典：各元ファイル。完全な入力・コード・出力台帳は電子資料を参照。

図のpanel切出し範囲とファイルはfigure_panels/と生成コードに残した。手作業による数値・軸・凡例変更は行っていない。原稿の本文参照は図3-1/2、図5-1/2/4/5/6/7、付図C-1/2へ正規化した。表示確認は05を参照する。
