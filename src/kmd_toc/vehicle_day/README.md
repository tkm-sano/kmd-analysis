# 車両日列の独立小規模参照

外部コード監査と計画を先に保存し、VRPyのRMP/価格付け分離とPyVRPの便/活動時刻構造を参考に独立実装した。外部コードのコピー・直接依存はない。Huangの既存Qiskit実装は変更しない。

## 入出力・責務

|モジュール|入力→出力|検証・エラー|
|---|---|---|
|model.py|人工Instance、明示運行値→不変DayProblem/Vehicle/TripSchedule/DayColumn、profile|整数秒・欠損・容量・gridの不正を拒否。日列IDは入力hash/車両/順序/開始時刻から生成|
|generation.py|既存便又は全便、時刻候補→0/1/2便、全格子日列、初期規則計画|容量・帰着/準備・勤務を構築時確認。列数/顧客/車両/時間slotのguardあり|
|master.py|日列、目的profile→LP/全dual/rc、Phase I、限定整数解|HiGHS marginalと全rc、primal/dualを確認。未配送人工変数を最終計画へ含めない|
|pricing.py|RMP dual又は全日列→厳密価格付け、AOA便を含む完成候補|原著AOAはtripだけ。完成後の車両/slot/補助双対込みrcで負列を判定|
|runner.py|人工問題、初期列/全列参照、有限停止→全履歴/計画/失敗|AOA未取得は証明でない。oracle列補充なし。診断時間を分離|
|validation.py|元入力と保存計画→独立再計算・原因・バース割当・2車両全組合せ参照|生成器の保存値を信用しない。全顧客一度、容量、準備、勤務、排他を確認|
|fixtures.py|n=4/5/6、B=1/2→固定人工入力|実道路・実績値・研究車両値ではない|

Qiskit/SciPy/NumPyの版はreproducibility/environment/vehicle_day_v1/requirements.lock.txt、Pythonは3.12.11である。solver_seedは新しい人工検証のみに用い、需要seedを導入・変更しない。設定JSONは固定fixtureの条件と探索設定の記録であり、全ての数値を変更して任意研究条件を生成する汎用入口ではない。実入力行列/条件はrunのINPUT_*.jsonを正本とし、設定との一致を結果監査する。

量子は顧客/順序候補を測定し、古典が便の結合・時刻・主問題選択を処理する。全追加日列が測定便を含むことと、新規測定便か既知便の再利用かを由来台帳で分ける。

数学的根拠と研究規模のHOLDは[定式化](../../../docs/research/toc_delivery_d/D_VEHICLE_DAY_FORMULATION.md)、[検証](../../../docs/research/toc_delivery_d/D_VEHICLE_DAY_VALIDATION.md)、[接続判定](../../../docs/research/toc_delivery_d/D_VEHICLE_DAY_READINESS.md)を参照する。現在は6顧客/2車両/40slot以下の検証専用であり、S1〜S3の実行入口ではない。

既存のkmd_toc.column_generationとtests/toc_cgの挙動を維持する。再実行時は新しい出力先を使い、保存済みの監査/計画gateを来歴として参照する。原著コード・外部VRPコードの再現成功、研究規模の実行可能性、量子優位性は主張しない。
