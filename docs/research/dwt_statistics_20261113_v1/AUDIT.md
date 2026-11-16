# 統計的試行数設計：読み取り監査と採用差分

2026-11-13。今回は文書・設定の策定のみ。実験・ソルバー・量子計算・需要/OD生成・D/W/Tの測定や再計算・7図生成を実施していない。Python標準ライブラリによるJSON/リンク/設定整合・ファイルhashの検査だけを最終確認に用いる。既存テスト207件や233件を今回再実行したという報告はしない。

## 確認したローカル資料

- `/AGENTS.md`、`/home/AGENTS.md`、`/home/takuma/AGENTS.md`、repo/調査対象下のAGENTS.md：該当なし。README.mdとgit statusを確認。
- `docs/research/TOC_DELIVERY_SPEC.md`（主ケースS2・旧7図・凍結需要追補）、`configs/toc_delivery/study.json`（古い未採択HOLD契約）。
- `configs/toc_delivery/common_conditions_v1_1.json`、`ad_pipeline_v2_route.json`、`dwt_balance_v1_3_1.json`。
- `configs/toc_delivery/frozen_demand_v1.json`、`src/kmd_toc/frozen_demand.py`、凍結v1の`READING_CONTRACT.md`。同フォルダ8ファイルをhash保全。
- `docs/research/A_TO_D_PIPELINE_FINAL_REPORT.md`、`COMMON_CONSTRAINT_AUDIT.md`、`INDEPENDENT_VALIDATION.md`、`REPRODUCE.md`。
- `docs/research/DWT_MULTI_OBJECTIVE_FORMULATION.md`、`DWT_EXPERIMENT_DESIGN.md`、`DWT_VALIDATION_REPORT.md`、`DWT_FINAL_COMPARISON.md`。
- `docs/research/toc_delivery_a/A_RULE_FINAL_DECISION.md`、`configs/toc_delivery/a_human_route_time_reference_v1.json`。古いAのHOLDや3規則の記録より最新の単一A2定義を採用。
- `docs/research/D_SHOTS_AUDIT.md`、`D_SHOTS_VALIDATION_PLAN.md`。
- `src/kmd_toc/pipeline/{classical,completion,hybrid,execution}.py`の今回/直前のコード監査記録、今回の`src/kmd_toc/dwt/{budget,experiment,worker,evaluation,analysis}.py`、`common/models.py`、`column_generation/aoa.py`。現在のスキーマ・seed・shots・固定需要検証・解析範囲を確認。
- Route-v2の`roads/inputs/{S1,S2,S3}/od/manifest.json`、固定共通入力、保存された`experiments/**/{result,plan}.json`を保全対象として特定。
- `output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1/trials/limited_S1_{B,C,D}_W422.45_T90_r0/metrics.json`を読み取り。instance_id=S1_frozen_v1、repetition_id=0、demand_seed=null、各solver/quantum seedとCPU0を確認。D/W/Tを再評価していない。
- 同DWT根のALL_TRIALS.json、ARTIFACT_INDEX.jsonを特定・保全。各セル1観測であり、正式pilotへ自動昇格しない。

依存・実装参照：既存記録のNumPy2.3.1、SciPy1.16.0、OR-Tools9.14.6206、Qiskit2.1.1。現行AOAは訓練テンソル+有限標本、最終Qiskit Statevector標本であり、実機計算ではない。今回これらのライブラリを実行して分散や時間を取得していない。

## 採用差分

|差分|今回の判断|
|---|---|
|旧README/研究契約に古い運行HOLDや容量候補が残る|最新共通v1.1と採用Route-v2入力を優先。旧ファイルを上書きしない|
|旧7図と今回の図1〜7表が異なる|今回のユーザー指示§11を正本にし、DWT_7_FIGURES_SPEC.mdへ差分を明記|
|S1の実装優先と旧主ケースS2|工程順と主たる科学比較を分け、S2主ケースを維持。変更するなら予備結果を見る前の新しい登録が必要|
|旧5反復/10%半幅の暫定案|既定にしない。DWT_EXPERIMENT_DESIGN.mdへ追補だけを追加し、元本文を保存|
|各規模1凍結需要、需要seedなし|新しい独立familyとsolver反復を別設計。v1のpinを外さず、別版/ODの承認を必須とする|
|S3母集団を既存4,000地点に限定する案|4,000非復元選択では同じ集合になるため、S3の需要間分散の標本にはならない|
|可行率のWilsonにnrを使う案|依存を無視するため不採用。反復0のn独立BernoulliでWilson、全rではfamily処理|
|成功した対応差だけをnr本の独立標本にする案|不採用。成功率を別記し、family単位の条件付き比率推定と必要数を設計|
|AのT_programをT_humanの代用にする案|不採用。人手全体T未校正のまま、B〜DのT front/Jに入れない|

## 本実験を妨げる事項

独立需要新版と新OD、h/δ/可行率精度、S2/S3の共通セル・資源、正式予備の分散/失敗過程、最終shots、実効HiGHS設定、将来のinstance registry/統計解析器、n/r/seed/順序/図閾値が未確定。統計設計GOは、これらの入力・実装・実行が完了したことを意味しない。

## 保全

開始時の追跡変更はREADME.md、.gitignore。417既存ファイルの開始hashをPRESERVATION_BEFORE.jsonへ記録。意図する既存文書変更は`docs/research/DWT_EXPERIMENT_DESIGN.md`への追補1件だけで、元はDWT_EXPERIMENT_DESIGN_BEFORE.mdに保全。新規4文書・統計設定・監査記録を追加。コード、旧設定、凍結需要、旧実験結果、ODは変更しない。最終照合はPRESERVATION_AFTER.jsonとVALIDATION.json。commit/pushなし。
