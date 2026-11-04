# 根拠の参照記号

全パスは存在を検査した入力。ハッシュと版はSOURCE_PROVENANCE.csv、保存先変更はevidence/PATH_RELOCATION_MAP.csv。相対表記P/T等は以下の絶対パスを基準とする。

|記号|実在する場所|主な用途|
|---|---|---|
|R|/home/takuma/kmd-analysis|現作業ツリー。HEADはevidence/START.json|
|P|/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01|11月2日全件監査。run_b.py/run_c.py/statistics_tables.py、B/C全件CSV|
|T|/home/takuma/kmd-analysis/review_outputs/quantum_ev_conditions_full_trial_20261104_125659|11月4日統合trial。RQ_REDESIGN_TRIAL.md、analyze.py、原稿THESIS_TRIAL.docx|
|S|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102|B実行原本。mirror_family/grover_depth/active_adjacent_p3のPROTOCOL.json、SOURCE_SNAPSHOT、RUNS|
|T8|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/material_ev_stage2_20261026/run02|T08元SCENARIOS.json、T08.json、MATERIAL_ENERGY.csv、SOURCE_SNAPSHOT|
|T9|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01|T09 model.py、analyze.py、RUN_CONFIG.json、PARAMETER_SOURCES.csv、PACK_20KWH_SENSITIVITY.csv|
|BR|/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t08_t09_conditional_bridge_20261030/run01|T09_MASS_BOUNDARIES.csv、MASS_COMPONENT_BRIDGE.csv、DC_MASS_RESPONSE.csv、integrate.py|

権威順位：今回ユーザーが確定した方針 > 方針記録run03/01_POLICY_AND_SCOPE.txt > 元データ・実行コードの事実 > 既存trialの解釈。正式採用状況は変更しない。旧正式方針の文面を今回の方針へ自動昇格しない。

インターネット上の最新版や論文一次資料の再調査は今回のローカル監査には含めない。材料の報告値は保存シナリオ内の記録として扱い、掲載論文を今回再検証したという意味ではない。

実行時の検査修正：初期構築時間のCSVとJSONの比較を、pandas標準float parserの丸めが混入しない文字列読込に修正した。元CSVの十進数文字列は元JSONの値と一致した。この修正は本trialの監査コードのみで、入力データの訂正ではない。
