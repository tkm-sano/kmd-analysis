# 主張・証拠の対応

証拠分類は観測記録、導出値、条件付きモデル、未検証、不適合を区別する。INVALIDを含む不適合の報告自体は採用できる。全フィールドは `CLAIM_EVIDENCE_MAPPING.csv` に保存した。

## A01：採用可能

固定ODモデルの全36政策条件でPE加重・件数定時配達率は100%であり、古典単独対照との差は0ppである。

- 分類・対象：CONDITIONAL / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_SUMMARY_BY_CONDITION.csv` / D10-01..36
- SHA256：`abbfe42a6ef709b29f3e0d7857198564bd43d77c67e48ce8300139e4f6472caf`
- 計算：100×ΣqI(c<=due+102)/Σq。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：各条件78問題・556PE・312配送先
- 図表：F3-1;F5-5
- 限界：時間不変OD・理想サービス。現実の同等性を意味しない。

## A02：採用可能

QAOA採用1344判断、古典切替1464判断、正の出発遅延936判断であった。

- 分類・対象：DERIVED / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv` / 全2808 policy行
- SHA256：`663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302`
- 計算：採用方式・departure>0の行数。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：1344/2808;1464/2808;936/2808
- 図表：F3-1
- 限界：取得成功64問題を1344個の独立問題と数えない。

## A03：採用可能

取得成功64問題中59問題で訪問順が一致し、5問題で異なった。

- 分類・対象：DERIVED / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_POLICY_DECISIONS_2808.csv` / acquired=Trueのproblem_idを一意化
- SHA256：`663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302`
- 計算：Q_route_differs_from_C。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：59/64,5/64
- 図表：F3-1
- 限界：成功部分集合であり未取得14を除く政策全体ではない。

## A04：採用可能

経路のみの変更による問題別平均完了時刻差は−962.281〜＋5.859秒であった。

- 分類・対象：CONDITIONAL / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_PAIRED_PER_PROBLEM.csv` / A_MECHANISM ROUTE_QC_CC
- SHA256：`284dbed468eb09222be28671fb7d4e47c9742cbd263b7d89143a6ca5fb8a49f9`
- 計算：mean(4 complete_Q−4 complete_C)。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：64入力×36条件の入力別差の範囲
- 図表：F5-4
- 限界：全体平均・各配送先差・帰庫差とは異なる。

## A05：採用可能

出発のみの変更では、正の遅延768条件すべてで第4配送先までに遅延が吸収された。

- 分類・対象：CONDITIONAL / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv` / MECHANISM64 CC/CQ；departure difference>0
- SHA256：`1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1`
- 計算：Δcomplete_k=Δdeparture−Σ(wait_CC−wait_CQ)。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：768/768条件；第1〜3先完全吸収372/684/744
- 図表：F5-5
- 限界：同一経路・固定OD。道路上で遅れを取り戻した実測ではない。

## A06：採用可能

政策評価の最小期限余裕は3133.461531秒であった。

- 分類・対象：CONDITIONAL / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_DELIVERY_COMPLETION_BY_STOP.csv` / POLICY78 全11232配送先行
- SHA256：`1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1`
- 計算：min(deadline−complete)。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：3133.461531秒
- 図表：F5-5
- 限界：旧native候補3099秒とは別指標・別モデル。

## A07：採用可能

機構比較の1920armは計画利用可能時刻と出発準備を満たさない。

- 分類・対象：DERIVED / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_MECHANISM_COMPARISON.csv` / availability_feasible=False
- SHA256：`5152d4b060f3f68b54f8f058bbaeb32571c4d658731d78fc8619192efae77f89`
- 計算：departure >= max(0,plan_available+120) の否定。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：QC1152,QQ768 /9216arm
- 図表：F5-4
- 限界：裸の計画利用可能時刻より前という判定と区別。

## A08：使用不可

計算方法は配送システムへ影響しない、または同等である。

- 分類・対象：UNTESTED / A
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/A_SUMMARY_BY_CONDITION.csv` / 全36条件
- SHA256：`abbfe42a6ef709b29f3e0d7857198564bd43d77c67e48ce8300139e4f6472caf`
- 計算：0ppから一般化する推論は成立しない。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：同等性検定・実配送検証なし
- 図表：F5-5
- 限界：時刻差あり、指標飽和、対象と仮定に限定。

## B01：採用可能

保存best計画は全36800参照で取得され、固定ODの実行可能性条件を満たした。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv` / 全36800行
- SHA256：`00ecaeb1706f06bd773c8f251baebf7f9752325073ffcc3cd6fbd745cdc142dd`
- 計算：permutation,ΣPE<=216,J+102n<=32400。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：36800/36800;460入力×8設定×10rep
- 図表：F5-1
- 限界：8192shot後のbest。各shot成功率や実配送成功率ではない。

## B02：採用可能

6設定の保存目的値および訪問順は古典初期解と一致した。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv` / MEAN,CVAR10,CVAR01,COHERENT2,COHERENT4,ACTIVE
- SHA256：`00ecaeb1706f06bd773c8f251baebf7f9752325073ffcc3cd6fbd745cdc142dd`
- 計算：Fraction(objective)==initial；route list equality。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：27600/27600参照
- 図表：F5-1
- 限界：目的値一致だけから経路一致を推論せず、リストを直接照合した。

## B03：採用可能

mirror5設定では初期解が同じ制限支持内の厳密最小値と一致した。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_CLASSICAL_ORBIT_COMPARISON.csv` / mirror_family 2300fit
- SHA256：`fb92155db74990c0418598031a7934caf70c6bba28a8b16286005d766832a9f3`
- 計算：保存orbit optimum vs initial；元JSONも照合。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：2300fit全件一致
- 図表：F5-1
- 限界：全配送先を残した2^floor(n/2)支持。全n!最適の証明ではない。

## B04：採用可能

active設定では保存した3点gridでt=0が460入力すべてで選択された。

- 分類・対象：OBSERVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_ACTIVE_GRID_SELECTION.csv` / 460入力 selected_t
- SHA256：`71992b4018501f430440ff3e48bb9dcc9b63c6a0c5ca1fd9581929145e4b0f19`
- 計算：保存grid選択のreadback。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：460/460
- 図表：F5-1
- 限界：連続角度や別初期状態を含む一般QAOAの改善不能ではない。

## B05：採用可能

Grover P2/P3の全入力平均目的値差は＋1765.006／＋1760.995秒であった。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv` / ALL GROVER_P2/P3
- SHA256：`229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03`
- 計算：入力内10rep平均→460入力等重み。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：460入力；正は初期解より大きい
- 図表：F5-1
- 限界：全規模混合は補助。主は規模別。異なる予算間の一般優劣ではない。

## B06：採用可能

Grover P2/P3の改善・同値・悪化は各70・2270・2260参照であった。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv` / 各Grover設定4600行
- SHA256：`00ecaeb1706f06bd773c8f251baebf7f9752325073ffcc3cd6fbd745cdc142dd`
- 計算：有理数の目的値比較。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：1.521739% /49.347826% /49.130435%
- 図表：F5-1
- 限界：repは独立配送問題ではない。改善70参照は7物理入力に対応。

## B07：採用可能

厳密参照は407入力に存在し、53入力のgapは未確定である。

- 分類・対象：DERIVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_EXACT_REFERENCE_COVERAGE.csv` / R4 21、R5 32 missing
- SHA256：`7b1d3632a219087ad9ec5f62e9be63d6e2effcf69a708133705f7f5d2df70eae`
- 計算：exact availabilityの一意入力集計。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：407/460；gap潜在32560/36800参照
- 図表：F5-2
- 限界：未確定を0としない。参照solverを今回再実行していない。

## B08：採用可能

学習時間だけでは最終検証工程を含む処理時間を表せない。

- 分類・対象：OBSERVED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_RESOURCE_SCOPE_SUMMARY.csv` / GROVER_P3 FINAL_VALIDATION wall
- SHA256：`5ab225e5a1f1fa6ad3fab69127f3dd2a685cbc9f49b8d7ea144609a5897fffd0`
- 計算：工程別保存値。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：R3/R4/R5平均168.745/193.651/226.554秒
- 図表：F5-3
- 限界：CPU環境固有。QPU時間・共通end-to-end時間は未確定。

## B09：使用不可

今回の結果は量子計算一般が古典計算より劣ることを証明した。

- 分類・対象：UNTESTED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv` / 全設定
- SHA256：`229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03`
- 計算：支持・定式化・予算が異なる比較。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：一般的優劣は判定できない
- 図表：F5-1;F5-3
- 限界：量子実機の速度・回路資源は未検証。

## B10：使用不可

系列Bの計画差が走行DCを変化させた。

- 分類・対象：UNTESTED / B
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv` / B_DC_status
- SHA256：`00ecaeb1706f06bd773c8f251baebf7f9752325073ffcc3cd6fbd745cdc142dd`
- 計算：保存DC列なし。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：走行DC評価0件
- 図表：F3-1
- 限界：旧C軌跡で代用しない。

## C01：採用可能

T08簡略質量会計のLP−S差は5.448297415kgであった。

- 分類・対象：CONDITIONAL / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv` / COND_LP_REF/COND_S200_REF
- SHA256：`f9bb9823fe500547c3c1fe002af769f7ad1a81ab7fdd8fbb34c1bb7ff3a362d7`
- 計算：塗工材＋固定19kg＋15kg。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：96.145654799−90.697357384kg
- 図表：F3-2;F5-7
- 限界：完成パック製造や実材料改善を実証していない。

## C02：採用可能

T08下側Crrの固定軌跡DC差の総和は5941.555975Wh、総量加重削減率は0.412579010%であった。

- 分類・対象：CONDITIONAL / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_PAIRED_DIFFERENCES.csv` / CLASSICAL,S200,CRR_LOWER_BOUND
- SHA256：`b5957b5c4c9cd6649bd25cff433222ef53187618369dc5a8807491f917679f8c`
- 計算：Σ(DC_LP−DC_S)、100Σ差/Σ基準。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：旧460軌跡；基準1440101.369798Wh
- 図表：F5-7
- 限界：保存軌跡・空荷・回生なし等の境界に依存。実EV削減率ではない。

## C03：採用可能

T09の代表既知部材差は固定担持9.722608121kg、固定面積5.977891152kgであった。

- 分類・対象：CONDITIONAL / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T09_COMPONENTS_183.csv` / B015/B051に対応する代表行
- SHA256：`4bdffa7249a93dba1f8e585769d94cd33f20305de223f0418cfedbb9a316960a`
- 計算：既知6部材LP−Sの和。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：2代表設計；全設計一律ではない
- 図表：F5-6
- 限界：T08との完成パック性能比較ではない。

## C04：採用可能

既知軽量化bは未知部材S−LP差δで相殺され、正味軽量化はb−δとなる。

- 分類・対象：CONDITIONAL / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_BRIDGE_MASS_DC_FULL.csv` / B015/B051 全7probe
- SHA256：`d0771ef9c94a28c7a2373ebb8bcbb068aae923730ce25cb0e32b2362c82fc90c`
- 計算：(knownLP−knownS)−(unknownS−unknownLP)。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：δ=bで0、δ>bで逆転
- 図表：F5-6;FA-1
- 限界：未知部材の実測分布を得たわけではない。

## C05：採用可能

T09完成パック質量183行は未確定で、全面対向の1行は不適合である。

- 分類・対象：INVALID / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T09_COMPONENTS_183.csv` / complete_pack_mass_kg；overlap_condition
- SHA256：`4bdffa7249a93dba1f8e585769d94cd33f20305de223f0418cfedbb9a316960a`
- 計算：NULL/FAILの保持。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：183 HOLD、うち幾何FAIL1
- 図表：F3-2
- 限界：不適合の記載は採用可能。設計成功という主張は禁止。

## C06：使用不可

量子計算による材料改善と実EV電力削減を実証した。

- 分類・対象：UNTESTED / C
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv` / 材料参照はChen文献由来
- SHA256：`f9bb9823fe500547c3c1fe002af769f7ad1a81ab7fdd8fbb34c1bb7ff3a362d7`
- 計算：古典DFT・電極試験と量子計算を区別。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：対象量子改善の実証0件
- 図表：F3-2
- 限界：計算算術の正確性は工学的成立を保証しない。

## S01：採用可能

25需要群bootstrapの区間は群構成に対する補助的感度である。

- 分類・対象：CONDITIONAL / STAT
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/CLUSTER_SENSITIVITY_INTERVALS.csv` / 全1176行
- SHA256：`102b5ae1712773c97bfd236124746d7b52cf7d1ed64c66cb5bac72ee8941f38d`
- 計算：25群を丸ごと10000回再標本化；percentile2.5/97.5。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/statistics_tables.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：26親を含む25群；検定0
- 図表：付表S-1
- 限界：交通・材料・モデル構造誤差や現実母集団のCIではない。

## S02：使用不可

定時率差0ppの区間[0,0]は実配送における同等性を証明した。

- 分類・対象：UNTESTED / STAT
- 入力・行：`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/CLUSTER_SENSITIVITY_INTERVALS.csv` / A_POLICY delta_F_PE_pp
- SHA256：`102b5ae1712773c97bfd236124746d7b52cf7d1ed64c66cb5bac72ee8941f38d`
- 計算：飽和した固定cohortの再標本化。実装 `/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/statistics_tables.py`、今回照合 `/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py`。
- 結果・分母：同等性検定なし
- 図表：F5-5
- 限界：無効果・同等性の一般化は禁止。
