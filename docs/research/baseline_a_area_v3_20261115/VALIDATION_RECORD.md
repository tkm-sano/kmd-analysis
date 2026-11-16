# 実装検証の範囲

小規模人工網の検査と、凍結した研究規模の動作確認を区別する。前者は実装の正しさ、後者は全件入力と実行可能性の確認であり、いずれも配送実績の代表性を証明しない。

|要件|検証する既存/新規テスト|
|---|---|
|地点数保存、重複/漏れ、容量、最大便、拠点往復|`test_program_v2.py::test_independent_oracle_rejects_corrupt_plans`、`test_common.py::test_missing_repeated_unknown_visits_and_trip3`、`test_area_v3.py::test_full_program_double_validation_and_assignment_preservation`|
|バース重複、第2便接続、積込前出発、勤務終了|既存の破損計画パラメータ、`test_berth_overlap_and_valid_second_connection`、共通バース/勤務テスト、新規`test_measured_late_return_is_rejected`|
|移動・作業・距離/時間単位|既存2地点の手計算（3km、各arc ceil(1.2秒)、作業各120秒）、新規`test_loss_and_local_coordinates_are_dimensionally_explicit`|
|入力hash、不達、失敗保存、上書き拒否|`test_hash_and_unreachable_failures`、`test_failure_saved_and_output_never_overwritten`、新規model hash/不達/全保存物hashのテスト|
|割当を維持した新順序規則|NN/区域の両方式×6/120/240地点。NNはA2と全Tripが一致し、最終割当も一致する|
|区域の保存・決定性・極端例|同一点座標、葉容量、順序入力の反転、有限倍率での退出/再進入、無制限の連続訪問|
|実績の入力漏洩防止・分離|生成関数が実績順を受け取らない構造、公開zone非依存、前回pilotを含む拠点日除外、未使用拠点での検証|
|選択の公平性|NN維持を許す、同点は単純規則、失敗した校正候補の除外、研究損失の単位|
|計時と棄却|モデル/入力読込から一致確認まで含める。違反時は採用可能D/W/Tをnullとし、試行時間と原因を残す|
|実行入口・成果物|ROOT参照漏れ修正後、executeから入力ルート解決・生成・全保存物hash照合までの回帰テストを追加した|

最初の回帰は189 passedであった。実行入口の参照漏れ修正後、新規ファイルの24テストが18.38秒で通過した。最終の全回帰は `tests/toc_baseline_a tests/toc_common` を実行し、190 passed / 21.77秒であった。[ログ](FINAL_TESTS.log)を保存した。S1〜S3結果は最終報告およびその機械可読検証記録に記載する。

実行入口で発生した失敗も[修正記録](EXECUTION_CORRECTION.md)と最初の出力に保持した。依存ライブラリ準備中に停止したS2試行は計画生成まで達しておらず、成功/検証済みと数えない。

各規模の新しい計画確認は二重検証、全地点数、D/W一致、保存物hash、ソース不変を要求する。選択NNは2回の計画JSON一致も確認し、2回を独立需要とは数えない。未採択区域候補は各1回なので反復再現やT分布を確認したとは記載しない。
