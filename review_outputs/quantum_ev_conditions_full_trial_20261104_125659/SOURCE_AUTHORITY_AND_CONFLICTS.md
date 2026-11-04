# 根拠の優先順位と矛盾の扱い

1. 今回の依頼（2026-11-04）：寄与条件へ重点移行、定時配達率を主指標から除外、既存境界維持、全変更をtrial提案とする。正式記録は変更しない。
2. 最新方針との整合確認：poster_policy_revision_20261104/run02/01_POLICY_AND_SCOPE.txt は条件候補・制約・未接続を重視し、インタビュー・RIQ・M1作成を工程から外している。今回も新しい面接結果を作らない。
3. 現行数値の主系列：no_sumo_full_analysis_20261102/run01 の全件CSVと、その上流NPZ・保存計画・SCENARIOS.json・保存速度。新規解析はハッシュを確認し、Bの全目的値とCの質量・DCを再計算した。
4. 正式凍結・旧ガイド：数式と過去の位置付けの根拠である。READMEの定時率・面接中心、QUANTITATIVE_GUIDEの時間窓あり・R4=99を、現行Bへ適用しない。旧正式量子は3/4顧客、現行Bは3/4/5/25/100/125である。
5. 原稿：tmp_RsrchMstrDc_1026_results_integrated.docx は5章に現行A/B/Cが入り、旧節を付録Bに保存し、11月3日統合記録が指すファイルであるためtrialの元に選定した。更新日時のみの選択ではない。tmp_RsrchMstrDc_1026_revised.docx と revisions/v07_results_integrated.docx も候補として照合対象にした。

旧レビューのPASSは、当時の算術・再現範囲に限定する。研究解釈CONDITIONAL、道路N0/N1 FAIL、T09完成pack HOLD、全面対向1件FAILを優先的に保持した。旧「新規計算禁止」「論文編集禁止」は当時のタスク境界であり、今回依頼はtrial内の軽量分析・複製編集を許可している。ただし物理モデルの凍結仕様は変更しない。

文献は11月2日の未同定表より、11月3日のREFERENCE_UPDATESと今回の一次照合を優先する。Papachristos2018の元引用意図は未確定のままである。

AGENTS.md は祖先3階層と対象リポジトリ（環境・第三者ツールを除く探索）で該当を確認できなかった。既存Git未追跡ファイルは開始時に存在しており、本trialで生成したものと区別してGIT_STATUS_START.txtに保存した。

## DOCX候補の直接比較

ルート統合原稿とrevisions/v07はSHA256が異なった。段落908、表27、画像19と本文は一致し、ZIP内の差分はdocument.xmlのkeepNext（次段落と分離しない）という組版設定であった。ルート原稿のSHAは11月3日の最終統合・render08記録に一致するため、これを選定した。byte一致と誤認せず、sources/SOURCE_DOCX_VERSION_COMPARISON.jsonとXML差分を保存した。

## 作業中に検出した追加成果

開始後、poster_policy_revision_20261104/run03の未追跡ファイル追加を検出した。01_POLICY_AND_SCOPEの内容は寄与条件中心、定時配達率・面接を主分析に含めない方針を維持していた。本trialは開始時に監査したrun02およびピン留めしたA/B/Cを基準とし、同時期のrun03の新しい派生分析は統合していない。追跡対象・元データ・原稿の保全と、Git未追跡集合の増加は別に報告する。
