# KMD修士研究 Step 1 評価設計・既存結果確定 trial

目的：量子技術がEV配送へ寄与する条件を検討するため、保存実験・実装・既存統計・原稿を照合し、Step2の評価仕様を具体化する。独立trialであり正式採用・統合は未実施。元データ・コード・既存trial・原稿を変更しない。commit/push/公開なし、新規QAOA/SUMO/厳密求解なし、Step2の統計計算・追加実験を開始していない。

読取元はSOURCE_MAP.mdとSOURCE_PROVENANCE.csv。現行Bの元NPZ/測定JSON/証明、旧C保存速度、T08/T09モデル、11月2日全件監査、11月4日統合trial、正式側DOCX候補と独立THESIS_TRIALを区別した。上流の一部はリポジトリ外のpreservationに実在するため、このtrialだけを他環境へ移しても全再検証できない。

|課題|成果物|
|---|---|
|1-1|RQ_INDICATOR_ALIGNMENT.md / POLICY_CONSISTENCY_AUDIT.md|
|1-2|PATH1_COMPARISON_BASELINES.md / PATH1_METRIC_SPECIFICATION.md / PATH1_REFERENCE_COVERAGE.csv|
|1-3|PATH1_RUNTIME_SCOPE_INVENTORY.csv / PATH1_RESOURCE_SCOPE.md / PATH1_TIME_CONDITION_SPEC.md|
|1-4|PATH2_MODEL_ROLE_SPECIFICATION.md / PATH2_INPUT_PARAMETER_DICTIONARY.csv / PATH2_BOUNDARY_DEFINITION_TABLE.csv / CONTROLLED_DC_SCOPE_AUDIT.md|
|1-5|PATH1_STATISTICAL_ANALYSIS_PLAN.md / PATH2_UNCERTAINTY_ANALYSIS_PLAN.md / STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv|
|横断|STEP1_DECISION_RECORD.md / STEP1_COMPLETION_MATRIX.csv / STEP2_HANDOFF.md / STEP1_FINAL_AUDIT.md / HOLD_REGISTER.md|
|根拠・保全|SOURCE_MAP.md / SOURCE_PROVENANCE.csv / evidence/ / OUTPUT_SHA256_MANIFEST.csv|
|監査コード|scripts/audit_sources.py / scripts/supplement_audit.py / scripts/write_design.py / scripts/finalize.py|

まずSTEP1_FINAL_AUDIT.mdで判定と限界、STEP2_HANDOFF.mdで次工程、各仕様書で定義を確認する。evidence/NUMERICAL_CHECKS.csvとSUPPLEMENT_CHECKS.csvは今回独立に検査した範囲であり、既存trialの検査件数を今回実行した数として引用しない。

再検証は監査スクリプトを新しいtrialへコピーして使い、元trialを再実行で上書きしない。scripts内の出力先は__file__から決まるため、コピー先の一意ディレクトリでのみ実行する。write_design.pyは本Step1の編集内容を出力する専用スクリプトであり、将来の新事実を自動反映するものではない。

追加監査コード：scripts/audit_history.py（旧A・B初期構築・凍結source hash・49点格子）。監査の実行順はaudit_sources.py → supplement_audit.py → audit_history.py → finalize.py。write_design.pyは本文生成用で、既存成果を再生成する科学実験ではない。
