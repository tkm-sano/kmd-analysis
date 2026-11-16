# Step5成果物

入口はSTEP5_FINAL_REPORT.md、論文はTHESIS_STEP5_REVISED.docx / THESIS_STEP5_REVISED.pdfである。総合判定はCONDITIONAL COMPLETEであり、未検証科学事項と提出体裁のHOLDを残す。

再現順序はscripts/analyze.py → scripts/write_reports.py → scripts/verify_science.py → scripts/refine_figures.py → scripts/build_thesis.py → scripts/render_thesis.py → scripts/final_audit.py → scripts/close_step5.pyである。元実験の再探索ではなく保存データの再集計/検算である。既存Step5を上書き再実行する場合は新しい独立ディレクトリへscriptsと開始台帳を移し、入力/環境/出力の依存を確認する。現成果物の再実行を承認済み元版の書換えへ転用しない。

本文のΔJ=候補−greedyはStep1〜4の旧符号と逆である。旧付録Bは保全履歴として読み、現在の定義/採用値を復活させない。図はF1〜F4、数値正本はdata/、来歴/検算/学術監査はevidence/にある。SHA256出力一覧はOUTPUT_SHA256_MANIFEST.csvを参照する。
