# 統合入力と出力の所在

元文書 `/home/takuma/kmd-analysis/tmp_RsrchMstrDc_1026_revised.docx`、SHA256 `ea25f2cc71368669a691ebe1e7643a25f30f288c00ce34cd66ed0590d95b3da3`。統合出力 `/home/takuma/kmd-analysis/tmp_RsrchMstrDc_1026_results_integrated.docx`、SHA256 `53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99f`。元文書は未変更である。既存研究データ・コード・FREEZE・図表・前段報告の読取対象317ファイルをSOURCE_HASHES_BEFORE.csvへ固定し、SOURCE_PROTECTION_CHECKS.csvで一致を確認した。前段の図表・原稿142成果物と全件分析171成果物を、各台帳のhashで照合してから使用した。

|区分|入力|対応する記録|
|---|---|---|
|反映方針|thesis_results_interpretation_20261102/run01の00〜09、DOCX_INSERTION_MAPPING.csv|32件のアンカー照合とINSERTION_EXECUTION.csv|
|新原稿|04_THESIS_METHODS_DRAFT、05_THESIS_RESULTS_DRAFT、06_THESIS_DISCUSSION_DRAFT、07_THESIS_CONCLUSION_DRAFT|新本文と付録Bの旧原文移動|
|図|FIGURE_SOURCE_MAPPING.csv、figures/の既存PNG|FIGURE_INTEGRATION.csv、元SVG/PDFは未変更|
|表|tables/の既存CSVおよび元8表|TABLE_INTEGRATION.csv、全旧表XML一致|
|数値|no_sumo_full_analysis_20261102/run01のA/B/C主要CSV|凍結結果と少数の保存集計行のreadback。再求解なし|
|Controlled-DC|CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json|SHA維持。式・境界を転記|
|参考文献|元参考文献と一次資料書誌|REFERENCE_UPDATES.json（確認日2026-11-03）|

全パス・SHA256はSOURCE_HASHES_BEFORE.csvとOUTPUT_SHA256_MANIFEST.csvを参照する。原raw/snapshotの一部は外部保全領域にあり、公開Gitに全て含まれるとは記述しない。今回のレンダラー・Python補助ライブラリはreview内のrendering_tools/へローカル展開した。システムや研究コードへインストール・変更していない。
