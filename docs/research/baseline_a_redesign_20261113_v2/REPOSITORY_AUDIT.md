# A再設計の開始時リポジトリ監査

2026-11-13、`/home/takuma/kmd-analysis`を調査した。作業順はAGENTS→README→Git状態/HEAD→実装→既存A証拠・確定仕様→入出力追跡である。HEADは`8605d5412f6af62229a83095c35ab04c8c7dd9b1`である。開始時状態は[INITIAL_GIT_STATUS.txt](INITIAL_GIT_STATUS.txt)、既存112ファイルのSHA256は[INITIAL_AUDIT.json](INITIAL_AUDIT.json)に保存した。既存READMEと.gitignoreは変更済み、配送研究の多くはuntrackedであった。今回の作業では既存ファイルを上書きせず、新規ファイルを追加する。

## 実装経路と現状

|対象|確認した実装・設定|実装済み/予定/未検証の区別|
|---|---|---|
|旧単一車両研究|README後半、kmd_quantitative等|旧EV/3–4顧客の結果である。複数車両Aの検証へ転用しない|
|旧A1/A2/A3|baseline_a/construction.py、config.py、a_rule_baseline_v1.json|角度3条件×規則3条件、容量・FCFS・時刻生成を実装済み。A2は最大V回の境界移動、最近隣、容量分割、距離relocation/2-optなしである|
|旧A限定検証|tests/toc_baseline_a、output/toc_delivery/a_rule_v1_20261112|人工網の実装検証・限定条件と研究規模を区別する。人工値は実ODの代替でない|
|旧A実行|baseline_a/runner.py、pipeline/execution.py、common/runtime.py|runnerの共通検査と別再計算の呼び位置を確認した。pipeline/executionでは第二再計算が共通run_measuredの計時後であり、計時説明をそのまま採用できない。人手T感度を主Tに流用しない|
|旧確定設計|baseline_a_final_20261113_v1 の3文書|A2/0度/FCFS＋program Tの設計はあるが、恒久CLI・総合評価接続・S2/S3確認は今後と記載される。設計済みと実装済みを区別する|
|現DWTのA|dwt/methods.py generateのA分岐|A2の後にshared completeを呼ぶ実装であり純粋FCFSとは別方式である。今回この経路を呼ばない|
|現B|pipeline/classical.py、dwt/methods.py、completion.py|有向Clarke–Wright候補と共通完成器である。Aの弱いsolver設定ではなく区域政策と候補生成・スケジュール政策が異なる|
|現C|同上、Routing/CP処理|OR-Tools Routing＋完成器、限られた予算での探索であり全VRP最適性を保証しない|
|現D|pipeline/hybrid.py、column_generation、dwt/methods.py|限定マクロ量子提案・日列・古典完成器である。シミュレータを実機の性能と解釈しない|
|B〜D並列既定|dwt_balance_v1_4_cpu_parallel.json、dwt/parallel.py|手法内4枝、native1 thread、親入力から全枝停止・候補選択・二重検証まで計時。今回変更・実行しない|
|共通入力|common/models.py、od.py、frozen_demand.py|共通v1.1・凍結需要・hash検査あり。デポ入口のシステム上の確認フラグと現地確認済みという主張を区別する|
|道路|ad_pipeline_20261112 と ad_pipeline_20261112_route_v2|旧Tableと新Routeは別の入力・結果である。今回Route版S1〜S3をファイル単位でpinする|
|旧DWT評価|dwt/evaluation.py、v1.4設定|Aをprogram J/Paretoから除外する旧契約、人手時間・60秒参照の履歴が残る。A新Tで自動置換しない|

## 今回の変更理由・範囲

代表性の資料不足をアルゴリズム変更で埋めない。暫定A2を保持して、新規program.py、program_validation.py、CLI、pin設定、単体テストを追加する。新規独立検証器を採用し、B〜Dも使用する旧independent.pyは変更しない。共通モデル・B〜Dアルゴリズム・既存凍結設定・既存結果は保全する。RQ/仮説は変更しない。

共通条件の道路説明に旧Table用の文言が残り、現Route版の実データメタデータとは異なる。また、旧DWTのAはCP完成器と旧評価契約を持つ。これらは新Aの主比較への接続に際して必要な研究設計上の不整合として報告する。既存の確定条件を黙って書き換える対応は採らない。
