# 読取元と記号

|記号|実在する絶対パス|役割|
|---|---|---|
|R|/home/takuma/kmd-analysis|現repository。HEAD/remoteはevidence/START.json|
|O|/home/takuma/kmd-analysis/review_outputs/quantum_ev_step2_analysis_trial_20261104_155535|今回独立Step2出力|
|S1|/home/takuma/kmd-analysis/review_outputs/quantum_ev_step1_design_trial_20261104_153058|評価仕様・provenance・保全基準|
|T|/home/takuma/kmd-analysis/review_outputs/quantum_ev_conditions_full_trial_20261104_125659|既存統合trial|
|P|/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01|B/C全件CSV・旧統計コード|
|U|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked|保全された元実行結果・コード|
|W|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/unified_no_windows_r0_r8_20261022|B NPZ・古典初期・SCIP reference/LP/log/solution|
|S|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102|B8設定のprotocol/SOURCE_SNAPSHOT/保存結果|
|T8|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/material_ev_stage2_20261026/run02|T08 scenario/model/保存energy|
|T9|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01|T09部材モデル・geometry・原入力|
|BR|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t08_t09_conditional_bridge_20261030/run01|既知部材差とmass/DC bridge|
|C|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/cpu_matched_classical_swaps_r0_r5_20261101|古典近似2法の原経路・実行コード|

全記号はこれら実在確認済みの基準パス。個別版/hashはSOURCE_PROVENANCE.csv、旧記録から実在へ解決したものはevidence/*_RELOCATIONS.csv。元データや正式原稿をOへ上書きしていない。新試行の再現先は新たな一意ディレクトリを作る。trial内の中間派生物が更新された履歴hashはSOURCE_HISTORY.csvで区別し、元研究の保全検査には外部・旧trialのみを使う。
