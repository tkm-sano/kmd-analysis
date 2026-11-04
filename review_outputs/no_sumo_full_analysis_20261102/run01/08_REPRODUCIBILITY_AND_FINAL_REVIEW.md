# 再現性と最終レビュー

算術・追跡性PASS、モデル解釈CONDITIONAL。独立全件検算756,579項目、統計・interval・再実行検算16,090項目に不一致0。独立C DC最大差2.73e-12Wh。主出力14CSVは再実行でbyte hash一致 (`REPLAY_OUTPUT_HASH_CHECK.csv`)。

## 状態を分離

|対象|判定|
|---|---|
|A/D11判断・時刻・分母とモデル再実行|PASS算術／CONDITIONAL理想OD|
|B全計画・407参照のgap・保存CPU資源|PASS算術／CONDITIONAL支持・CPU比較|
|B exact53、compiled資源、統一旧実行環境|HOLD・NULL保持|
|C T08/T09既知部材と固定速度DC|PASS算術／CONDITIONAL工学適用|
|T09完成pack183|HOLD|
|T09全面対向1|FAILを保持|
|道路N0/N1地域受入|FAILを保持|
|B計画→DC、量子解析→材料改善|UNTESTED|

## コマンド

既存環境 `.conda/bin/python -B`、現在versionは `ANALYSIS_ENVIRONMENT.json`。実コードSHA、入力SHA、出力SHAは `SOURCE_AND_OUTPUT_HASHES.csv` と `ARTIFACT_MANIFEST.json`。`OUTPUT_SCHEMAS_FROZEN.json` は事前契約、`DATA_SCHEMA_AUDIT.json` は実際の全CSV構造・PK検査。

```bash
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/stage0.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_independent.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/batch_gate.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_independent.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/statistics_tables.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/resource_and_sensitivity.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_statistics.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/write_reports.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/final_review.py
```

再実行はレビュー一式を新領域へ複製して行う。コードOは自ファイルの親を使用し、旧科学runnerは起動しない。入力R/U/B/Lの保全パスが必要で、公開Gitだけでの全再現性を達成したとは言えない。原文献から全入力を再生成したわけでもなく、現実配送・電池・車両妥当性は未達。

## 資源実測

|process|wall秒|CPU秒（累積）|最大RSS bytes|
|---|---:|---:|---:|
|STAGE0|5.252369|2.101253|69,206,016|
|A_BATCH|0.132786|0.140978|47,153,152|
|B_BATCH|0.736516|0.757592|163,577,856|
|C_BATCH|1.941586|2.251532|500,764,672|
|VERIFY_BATCH|0.274562|0.553073|147,075,072|
|A_FULL|2.113247|2.053760|182,452,224|
|B_FULL|19.949940|15.980590|814,743,552|
|C_FULL|58.939105|58.734721|633,241,600|
|VERIFY_FULL|30.330964|30.279230|878,661,632|
|A_REPLAY|2.046574|2.059865|182,452,224|
|B_REPLAY|18.960293|16.136001|824,180,736|
|C_REPLAY|58.708203|58.737925|633,270,272|
|STATISTICS|5.088007|5.001931|913,739,776|
|SUPPLEMENT|15.733594|132.941317|496,771,072|

測定はprocessごと。wallはmain内、CPUはimport等も含むprocess累積で、thread実行等によって単純比較できない。上表は今回の既存データ分析費用で、保存量子計算の元実験コストとは別。primaryチェックログは100,000行で上限を設けた場合があるが、検査ループは全行を処理し、不一致なら直ちに失敗する。独立検証は全756,579照合を数え、件数・PK・分母と再実行を別途検査した。

## 保全・修正・残作業

`FINAL_REVIEW.json`、`INPUT_HASH_FINAL.csv`、`GIT_DIFF_FINAL.patch`、`GIT_STATUS_FINAL.txt` に最終保全を記録する。書込みは新レビュー領域のみ。元の道路・OD・計画・FREEZE・docs・DOCXを変更していない。確認範囲は台帳記載ファイルであり、未読バックアップの全内容を監査したという主張ではない。

統計検証の初回は変数名metricが関数を隠し、数値照合後の資源記録で停止した。元データ不一致は0。修正前コード／ログ、diffをrevisionsへ保存し、修正後に全統計検証を再実行してPASSを確認。集計CSVの追跡用metadataを追加し、物理入力SHAと集計元table hashのscopeを明記して再検証した。科学的評価条件は変更していない。

論文転記前には表の符号・分母・単位・scopeを確認する。文章・図表の編集、モデル仮定の章間整合、引用／付録、外部保全データの配布範囲が残作業。今回の全件分析と検証はここで停止し、新規地域実験や論文編集を自動開始しない。

<!-- FINAL_AUDIT -->

## 最終保全照合

調査入力・旧成果10,050ファイルを終了時に再ハッシュし、不一致0。旧4レビューの1,047成果物を保持。保存資源の元JSON pointer照合41,860件、最終検査63,991項目はPASS。tracked Git差分0bytes。主CSV14件の再実行はbyte一致。詳細はFINAL_REVIEW.jsonとINPUT_HASH_FINAL.csv。
