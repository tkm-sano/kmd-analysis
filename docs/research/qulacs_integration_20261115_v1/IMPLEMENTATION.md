# 条件Dの任意Qulacsバックエンドの実装

2026-11-15。前回の[最終採用判定](../library_implementation_20261114_v2/FINAL_ADOPTION_DECISION.md)に従い、**Qiskitを既定として維持し、DWT条件Dの最終状態計算にQulacsを明示選択できるようにした**。現行の通常実行入口に接続済み。QURI Partsは前回の比較・照合コードを維持し、Qamomileを必須依存へ追加しない。

## 使い方と範囲

既存の既定設定は変更していない。`D.statevector_backend`を省略すると`qiskit`、明示的に`qulacs`を指定するとQulacs直接APIを使用する。その他の値はエラーとする。

[任意Qulacs設定](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel_qulacs.json)を別ファイルとして追加した。元の4プロセス設定との差分は版名、出力先、採用注記、バックエンド指定だけである。研究条件、計算予算、4枝・各1コア/native 1 thread、seed生成、保留中の本実験指定を維持する。

```json
{
  "D": {
    "statevector_backend": "qulacs"
  }
}
```

この断片は既存設定の`D`へ1項目を追加する例であり、単独の実行設定ではない。実行入口は従来の`scripts/run_dwt.py` / `scripts/run_dwt_bundle.py`のまま、`--config`で選択する。各設定は新しい出力先・新しい登録を使用し、既存登録・試行を上書きしない。登録済み実験の設定変更はしない。

Qulacsは[任意依存定義](../../../reproducibility/environment/dwt_qulacs_v1/requirements-optional.txt)に`qulacs==0.6.14`で固定した。本番の既存依存定義と既存環境を変更していない。Qiskitは共通samplerと基準回路のため引き続き必要。Qulacs未導入時は明示エラーで停止し、自動代替しない。バックエンドとsamplerの名前・版を登録時に保存し、`run_registered`で版の不一致を実行前に拒否する。過去のバックエンド指定・新メタデータがない登録は従来のQiskit経路として扱う。

## 変更した実装

|対象|変更内容|
|---|---|
|[column_generation/backends.py](../../../src/kmd_toc/column_generation/backends.py)|選択値の検証、任意依存の遅延import、版の取得、Qulacs回路・状態計算、量子処理時間の集計を追加|
|[column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py)|`AOAConfig.statevector_backend`、最終状態の実行分岐、全restartの構築/状態/検証/抽出/decodeの計測を追加。`circuit()`は両設定ともQiskit基準回路を返す|
|[dwt/methods.py](../../../src/kmd_toc/dwt/methods.py)|選択をAOAへ伝達。最終restartだけを測っていた計測用subclassを置き換え、AOAの全restart計測を保存|
|[dwt/setup.py](../../../src/kmd_toc/dwt/setup.py)、[worker.py](../../../src/kmd_toc/dwt/worker.py)|T開始前の共通依存importに選択バックエンドを含める。入力読込・回路作成・状態計算は準備段階で実行しない。実行版を記録|
|[dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py)|全枝のバックエンド・版と各処理時間を記録し、未選択枝も合算。失敗・強制停止時の未完了処理総量をunknownとして保持|
|[dwt/experiment.py](../../../src/kmd_toc/dwt/experiment.py)|登録・実行前の任意依存と版確認、失敗行にも設定バックエンドを保存。新規出力ディレクトリの登録時作成も修正|
|[検算スクリプト](../../../scripts/verify_dwt_statevector_backends.py)|人工6顧客で両バックエンドの実際の4枝実行と微小予算での停止を確認。出力先は新規ディレクトリのみ|

学習は元の圧縮one-hot tensor、有限shots目的評価、COBYLAを維持する。今回Qulacsへ渡すのは最適化後の最終回路であり、学習全体をQulacsへ移したものではない。Ising係数、ALiM式、one-hot初期状態、exact ring XY、パラメータ、乱数消費順、共通Qiskit `Statevector.sample_counts`、decodeを保持する。

Qulacsの回転符号をQiskitと対応させ、RZ/RZZに`-2γ係数`を使う。bit bは両者とも整数maskのbit bとする。XYは同じ行列指数のDenseMatrixであり、Trotter近似へ変更しない。定数Hamiltonianによる全体位相のみ省略する。Qulacsの最終状態を共通Qiskit samplerへ渡すが、通常実行でQiskit側の状態発展を二重実行しない。

現行DWTの顧客集合・経路探索範囲、全macro順列の受理条件、独立した初期解、古典完成処理、車両/2便/容量/バース/勤務終了制約、最終二重検証を維持する。B/Cの解は使わない。前回の試験用updated CGの集合変更・双対再求解アルゴリズムを今回のバックエンド設定へ混在させていない。研究上の探索範囲の制約は前回報告のまま残る。

## 記録と互換性

- AOA各処理時間は**全restartの累積値**。`training_seconds`、`circuit_build_seconds`、`statevector_seconds`、`state_validation_seconds`、`sampling_seconds`、`decode_seconds`を保存する。Qulacs→共通Statevectorの配列受渡しは状態計算時間に含む。直接構築なので独立したQiskit→Qulacs変換工程はない。
- `final_processing_seconds`は構築・状態・検証・抽出・decodeを包含する。各内訳と二重加算しない。旧`qiskit_seconds`は互換aliasとして保持し、そのscopeと実際のバックエンドを併記する。旧`qiskit_tensor_max_infidelity` / `qiskit_one_hot_max_leakage`も互換名であり、選択バックエンドとtensorの照合値を意味する。
- `logical_gates`は選択バックエンドのゲート名で、名前の違いを明示する。exact XY blockを論理1ゲートとして扱う。`native_depth=True`はQiskit基準回路のtranspile診断であり、実機接続やQulacsのnativeゲート分解を意味しない。その時間も別記しAOA総時間に含める。
- DWT各呼出・枝・親に実行backend/versionを保存する。全枝の各量子処理時間の和は並列に重なる**処理観測値の和**であり、親wall timeのT_programと同一視しない。完了callの`observed_quantum_timing_s`と、完全計上できた場合だけの`total_quantum_timing_s`を区別する。強制停止で未知の作業は0と推定しない。
- 親T_programの境界は入力読込から全枝停止/join、候補選択、最終二重検証まで。共通依存/待機プロセスの準備と最終成果物出力は従来どおり別記する。stage証拠の記録は従来どおり計時内。

## 検証結果

Python **3.12.11**、Qiskit **2.1.1**、Qulacs **0.6.14**、NumPy **2.3.1**、SciPy **1.16.0**、OR-Tools **9.14.6206**の新規隔離環境で実行した。[環境](evidence/environment.json)、[全依存lock](evidence/requirements.lock.txt)、[再現手順](evidence/reproduce.sh)を保存した。

|検証|結果・根拠|
|---|---|
|CG/vehicle-day/pipeline/DWT回帰|**118 passed**。[ログ](evidence/regression_tests.log)。追加19件を含む|
|任意依存なしの既存Python3.12環境|**27 passed, 7 skipped**。Qulacs未導入を確認し、既定Qiskit経路を検証。[環境](evidence/default_environment.json)、[ログ](evidence/default_environment_tests.log)|
|数値同等性|q2/6/12、p1/2/3、固定/可変depotを確認。全体位相を除いた振幅最大誤差・確率分布L1誤差<1e-10、期待値絶対誤差<1e-9、infidelity<1e-10。[テスト](../../../tests/toc_cg/test_backends.py)|
|学習/抽出同等性|全restartの学習履歴、最終bit列とcount、経路、制約違反集計が一致。旧ソースとの核計算比較は[保存結果](evidence/legacy_kernel.json)と[検算コード](evidence/verify_legacy_kernel.py)|
|実際の4枝比較|**31項目通過**。両方の全4枝がVALIDATED、PID/1コアaffinity/seed/版/全shotsを保存、学習と抽出履歴一致。[生結果](evidence/parallel_smoke/VERIFICATION.json)|
|ワーカー/監視/標準出力|Qulacsでfresh exec→4枝→二重検証→標準7成果物まで**COMPLETE**。[検算](evidence/wrapper_smoke/VERIFICATION.json)、[コード](evidence/verify_wrapper.py)|
|失敗時の計上|極小予算1e-7秒で計画を捏造せずTIME_BUDGET_EXCEEDED、全枝停止/join、未完了量子総時間・総shotsはnull。[31項目検算内のfailure_case](evidence/parallel_smoke/VERIFICATION.json)|

6顧客・2車両・1バースの人工問題の1回ずつの動作確認値を示す。全4枝で各2回、計8回の量子呼出、学習233,000 shots、最終32,768 shotsを両方式で記録した。統計的反復は各1であり、4枝を4反復として扱わない。

|backend|D km|W min|親T_program s|準備 s|全枝の状態計算累積 s|
|---|---:|---:|---:|---:|---:|
|Qiskit|0.834|0|1.798919|1.751625|0.040053|
|Qulacs|0.834|0|1.827054|1.269476|0.018019|

今回は実装検証で、ウォームアップ・順序ランダム化・性能分布の反復測定を行っていない。この表から全体T改善や統計的有意性を主張しない。D/Wは同じであり、全体Tの観測値はQulacsの方が僅かに長い。CPUの状態ベクトル計算であり量子実機での高速化ではない。性能・採用の根拠は前回の比較報告と併せて評価する。

Qulacsなしでも動作する既定経路を残し、利用者が同一アルゴリズムの状態計算だけを切り替えられる実装とした。次の研究上の検証は、制約が実際に拘束する小規模問題での十分なpaired反復、およびバックエンド変更と探索空間変更を分けた評価となる。今回S1〜S3と凍結需要生成は実行していない。

## 保全と開発中の記録

[開始時hash](evidence/preservation_before.json)、[保全検査](evidence/preservation_check.json)、変更前ソース、差分、ログを保存する。既存README、設定、依存定義、過去の調査資料・結果は維持した。変更した既存ファイルは上記6ソースとテストの引数追従1箇所だけで、他は新規追加。commit/pushは実施していない。

開発初回の追加テストでは登録先ディレクトリ未作成を1件検出した（[初回ログ](evidence/backend_tests.log)）。入力/環境を検証後に新規登録先を作成するよう修正し、118件の最終回帰で通過した。旧核比較の初回は結果JSON保存でNumPy整数の変換が不足したため失敗した（[初回ログ](evidence/legacy_kernel.log)）。検算の保存処理を修正して再実行し、最終結果と[再実行ログ](evidence/legacy_kernel_retry.log)を保存した。これらを本実験の失敗や量子解の不一致として集計していない。
