# 小規模検証プロトコル

作成日: 2026-11-14 (JST)。本ファイルと検証コードを確定してから本測定を開始する。探索的なsmokeと本測定を区別する。S1〜S3、凍結需要、既存ODを一切読まない。

## 比較の分離

1. **同一アルゴリズムの実行基盤比較**: Qiskit 2.1.1、Qulacs 0.6.14、QURI Parts 0.28.0＋Qulacs。既存 `PricingAOA` の定式化、圧縮one-hotテンソル学習、COBYLA、exact ring XYを共有し、最終回路の構築と状態発展だけ変更する。
2. **Qamomileの定式化併用**: Qamomile 0.15.2 `BinaryModel.from_qubo().change_vartype(SPIN)` のIsing係数を既存回路に渡す。回路はQiskit。これはQamomileの標準QAOAコンパイラー性能の測定ではない。
3. **互換性検査**: QUBO全計算基底上のエネルギー、複数角度での状態忠実度とone-hot漏出、既存runとの学習履歴一致を検査する。標準QAOAコンバーターの実行確認は別記する。そのX mixer/+状態は既存XY mixer/one-hot初期状態と違うため、速度・品質比較に入れない。

## 入力と共通条件

`vehicle_day.fixtures.small_problem(4,2)` の人工4顧客、2車両、2バース、容量2、最大2便、120秒積込、120秒準備、120秒サービス、勤務終了1680秒、120秒刻みだけを用いる。ID順 `seed_plan` とそのPhase II RMPの顧客・車両・バース双対を使用する。B/Cの計画を参照しない。既存RMP/日程完成/RC/整数選択/検証関数を呼ぶ。

|ケース|量子候補の範囲|目的|
|---|---|---|
|macro|初期第1経路の2顧客を単独断片にする。slots=3、6 qubits。全断片を一度ずつ含む経路だけ採用|通常DWTの受理条件を小規模で維持する比較|
|selection|RMPの顧客双対上位3顧客。slots=4、12 qubits。実行可能な部分集合経路も採用|既存vehicle_day pricingに沿った選択可能ドメインの比較。通常DWTからのアルゴリズム差として扱う|

距離はfixtureの人工km。ペナルティは既存 `lambda_capacity=lambda_visit=1`、`penalty=customer_unique`、`fixed_depot=True`。目的は距離−顧客双対＋ALiM容量項＋顧客重複項。バース/車両/待機上限の双対を量子の代理目的へ追加しない。完成したday列で真のRCを再計算する。W上限はなし。one-hotをミキサーで保ち、容量・重複はペナルティとdecode検査で扱う。

共通 p=2、COBYLA maxiter=80、tol=0.001、restart=1、訓練1000 shots/評価、最終4096 shots。seedは1101〜1105の5個、初期角は既存 `PricingAOA.run` と同じ。COBYLAが早期停止したら実nfevを保存し、上限回数を消費した場合のsuccess=Falseも隠さない。

各seedの学習は全案で同じテンソル関数/PCG64 multinomialを使う。最終標本も同じPCG64 multinomialを同じone-hot基底順で使い、SDK固有PRNG差を除く。Qiskitの既存 `Statevector.sample_counts` とは最終標本法が異なる。したがって測定値は**計測アダプターの結果**であり、現行Dの未変更runそのものの全時間ではない。既存runも別途小規模再現して学習一致と標本法の差を記録する。全案に共有の新しい古典経路・修復・oracle列は注入しない。

## 資源と計時

隔離venv `/tmp/kmd-library-survey-20261114`。Python 3.11系。既存の履歴環境Python 3.12.11と異なるため過去時間との比較をしない。科学計算主要版は履歴のNumPy 2.3.1/SciPy 1.16.0/Qiskit 2.1.1を固定する。新規依存は本番に追加しない。

各測定は独立子プロセス、同じCPU ID 0の単一コアaffinity、native 1 thread、アドレス空間上限4 GiB。全候補のライブラリの共通importは計時前、import/起動時間は別記する。主測定はライブラリ間を逐次実行し、seedごとに順番を循環する。これは**Pricing部品検証**であり、通常DWTの4並列マルチスタートの代替実験ではない。DWT CLIの逐次互換経路は使用しない。

- 回路構築: 最適化後の全p層、Isingゲート、XY行列expm、回路への追加。
- 学習: 全objective評価、1000-shot訓練抽出、COBYLA。全案同一の既存テンソル計算。
- 状態発展: 全量状態ベクトルの生成と取得。QURIではQulacsへの変換も含む。
- 最終sampling: 4096-shot共通抽出のみ。検証/復号時間を含めない。
- Pricing kernel: 学習＋構築＋状態発展＋抽出＋Qamomile定式化アダプター時間。既存 `PricingAOA` 初期化等はsetupに分離。
- 小規模pipeline: 人工入力作成→初期RMP→Pricing初期化→学習→最終量子処理→復号→有限グリッドday完成→真RC→最大20負列追加→LP再求解→整数選択→日程検証まで。ファイル出力と依存importを除く。これは本研究のT_programとは別指標。
- 最大RSS: Linux `ru_maxrss` KiB、fresh processのimport込み絶対ピーク。共有importを揃えるので最小構成のライブラリ別メモリ比較には使わない。アドレス空間上限はRSS制限ではない。
- 回路深さ: 密なXYを1論理ゲートと数えたSDK深さ。実機native深さは未測定。量子ビットは圧縮テンソルの64状態等と混同しない。

## 品質・資源の定義

実行可能率はdecodeがVALIDとなる**最終shotsの割合**。空/重複/容量違反を拒否し、macroで全断片に満たない標本は生の実行可能率とは別に棄却する。異経路数は顧客順tupleのunique数。顧客集合変化数は初期経路のどのfrozensetとも一致しない受理経路数。未観測経路や列挙oracleを生成能力の実測数へ足さない。

最良値はペナルティ込み標本energy、VALID標本energy、trip代理RC、完成dayの真RC、最終有限列IP距離を別記する。負の有効列数は勤務・容量・2便等を検査した、初期poolにないday identityのRC < −1e−7の数。時刻・車両違いを別列として数えるため異経路数とは違う。単独day列は他dayとのバース競合をまだ解決しておらず、全体の実行可能性はmaster/validate_planで検査する。

訓練shots=nfev×1000、最終shots=4096、全seed/全案を保存する。5 seedsは同じ人工入力に対する内部乱数感度であり独立需要5件ではない。median/rangeを示すだけで母集団優越性・仮説支持を主張しない。Statevectorだけを使い、実機・通信・待ち行列・ノイズ結果と混ぜない。

## 事前の採否方針

同等状態が得られることを必須とする。回路差・目的差・異なるsamplingやアルゴリズムの差をライブラリによる品質改善としない。部分高速化があっても通常DWTの4枝・親を含むT_program/D/W改善を確認するまでは全面的な採用推奨としない。S1〜S3は実行しない。

実行: `code/run_benchmarks.py`。環境固定: `evidence/requirements.lock.txt`、実行ログ/各プロセスJSON、プロトコルとコードのSHA256を保存する。

初回資源チェックの修正: 4 GiB制限下の最初のmacro/Qiskit子プロセスはnative solverの終了(-6)により測定値を出さなかった。既存day masterはHiGHS threadsを指定しないため、本検証プロセス内だけ `linprog/milp` のoptionsへ `threads=1` を追加するアダプターを入れ、全案共通に適用する。モデル・solverの他options・本番ソースは変更しない。原因はthread/メモリ確保との整合性が疑われるが厳密なnative障害原因は未確定。失敗ログと最初のfreezeを `*_resource_attempt.json` に保全し、修正後のfreezeで全測定を開始し直す。
