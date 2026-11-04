# 資料・主要結果・実装の所在

2026-11-02、HEAD `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。新規レビュー領域のみへ保存した。保存結果の学術的解釈と軽量集計を対象とし、実験の再実行は行っていない。本文案は「である」調であり、DOCXを編集する指示書とは分離している。

## 正式採用と版

主資料は `review_outputs/no_sumo_full_analysis_20261102/run01/ARTIFACT_MANIFEST.json` で固定された171成果物である。開始時の171件のSHA256不一致は0件である。旧監査4領域を保持し、代替分析仕様と全件分析の凍結仕様を優先した。詳細入力は同領域 `INPUT_LEDGER.csv`、行別source_path/source_sha256、`*_FULL_SOURCES.json` に遡る。`BASELINE_PINNED_SOURCES.csv` と各 `*_SOURCES.json` に今回読んだ実パス・SHA256・保存区分を記録した。終了時照合は `PRESERVATION_CHECKS.csv` と `09_FINAL_QUALITY_REVIEW.md` を参照する。

実験当時のraw JSON・snapshotの一部は `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/`、`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup/` 等の外部保全領域にある。公開Gitに全入力が揃うとは主張しない。パスの再配置は `scripts/evidence.py` の4根探索で明示し、hashで同一性を確認した。

|系列|主要保存表|計算・独立検証|今回の再照合|
|---|---|---|---|
|A|A_POLICY_DECISIONS_2808、A_DELIVERY_COMPLETION_BY_STOP、A_MECHANISM_COMPARISON|run_a.py、verify_independent.py（別のmax-plus展開）|2,808政策・9,216arm、待機と帰庫の厳密有理数会計|
|B|B_PLAN_REFERENCES_36800、B_EXACT_REFERENCE_COVERAGE、B_RESOURCES_PER_FIT|run_b.py、verify_independent.py（NPZの別加算）|36,800参照の比較分類・経路リスト、2,300mirror元JSON|
|C|C_T08_ENERGY_FULL、C_T09_COMPONENTS_183、C_BRIDGE_MASS_DC_FULL|run_c.py、verify_independent.py（質量係数式）|旧460主軌跡のDC個別行集計、183NULL・1FAIL保持|
|統計|CLUSTER_SENSITIVITY_INTERVALS、PARENT_GROUP_MAPPING|statistics_tables.py、verify_statistics.py|群単位・分母・工程区分をコードで確認。bootstrap再実行なし|

ファイル名の末尾`.csv`は表中で省略した。前回検証の再使用と今回の検算を混同しない。前回全件検証756,579項目等の記録と、今回の 32,269 項目・不一致 0 件は別である。

## 論文と文献

`tmp_RsrchMstrDc_1026_revised.docx` は存在し、610段落・8表である。SHA256は `ea25f2cc71368669a691ebe1e7643a25f30f288c00ce34cd66ed0590d95b3da3`。読み取り専用で本文、見出し、参考文献、表、OMML数式文字を抽出した。Word上のページ位置・組版は未検証である。章対応は08、抽出原表は `DOCX_PARAGRAPHS.csv` 等に保存した。

量子法の一次原著は[Farhi et al. 2014](https://arxiv.org/abs/1411.4028)、[Hadfield et al.](https://arxiv.org/abs/1709.03489)、[Bärtschi and Eidenbenz 2020](https://arxiv.org/abs/2006.00354)の表題・著者・版を確認した。材料は[Chen et al. 2020](https://www.nature.com/articles/s41467-020-17126-3)の保存原論文Fig.5gとMethodsに遡る。群bootstrapは[Field and Welsh 2007](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x)を方法論の参照とし、今回の標本設計を正当化する根拠にはしない。

`LITERATURE_VERIFICATION.csv` に照合範囲を限定して記録した。背景節のIPCC 2023等8件は対応する末尾文献の整備がHOLD、Faraji-Niri et al.のDOIは未確認である。既存の研究docs・DOCXへ追記していない。指定された主資料・DOCXの欠落は0件である。

<!-- MAIN_HASH_INVENTORY -->
## 主資料のSHA256

以下はすべて `review_outputs/no_sumo_full_analysis_20261102/run01/` 内である。全読取資料2,532件のhashはSOURCE_INVENTORY_SHA256.csvに保存した。

|ファイル|SHA256|
|---|---|
|A_POLICY_DECISIONS_2808.csv|`663d36df04146600822d25c3239ec8181f366bef1e2eb76ec0c198284ee45302`|
|A_DELIVERY_COMPLETION_BY_STOP.csv|`1d5cb90d576633e8fbe0c166bccbd4f62d56fa26d4e0844c6ae944855b19d2c1`|
|A_MECHANISM_COMPARISON.csv|`5152d4b060f3f68b54f8f058bbaeb32571c4d658731d78fc8619192efae77f89`|
|B_PLAN_REFERENCES_36800.csv|`00ecaeb1706f06bd773c8f251baebf7f9752325073ffcc3cd6fbd745cdc142dd`|
|B_SUMMARY_BY_SCALE_AND_METHOD.csv|`229d380328866b632659f16af787064a16b69068aa32614719d9cd364e9c9a03`|
|C_CONDITIONAL_MASS_DC_SUMMARY.csv|`d5104475de4256d3304da06c04733230b39a3c1757a691ad3418d71fcea63e2e`|
|PAIRED_COMPARISONS.csv|`82f160e7b658d86e2ed8c4fa5441c4d9c757732245abb31d9e036c6f71c7c31d`|
|run_a.py|`be6c83b0790098752aed3b940fff1521f980cf67f9c5ffd40f946d86a60f48d9`|
|run_b.py|`f8fd2baf9afd75ea69737f2d89d0218f3f15e2be59766f9e63415dc5c8c2f299`|
|run_c.py|`cdd7000ac17c346faa6e153317ea434988153591f8b4f6759c39866fa4d128e6`|
|statistics_tables.py|`1b5793f91ee789f15ad94d9d938ea43edf1ead3fe4463c52a9d9aa96012c6eea`|
|verify_independent.py|`839954d8171cf2d4496ff62903afa3b6ddf93df555270869c3121905f48ebe68`|
|verify_statistics.py|`1c65ac55e90d661dc7d19b0aee515350090e6b1f57b79542994bc811ccc2c159`|
