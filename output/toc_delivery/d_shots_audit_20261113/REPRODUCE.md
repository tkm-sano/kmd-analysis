# D shots監査9の再現手順

対象は2026-11-13の作業ツリーと`ad_pipeline_20261112_route_v2`の保存結果。旧結果を変更せず、本ディレクトリに監査結果だけを保存する。

## 環境と実行

Python3.12、NumPy2.3.1、SciPy1.16.0、Qiskit2.1.1、pytest8.4.2。既存の`ad-pipeline-v1`venvを読み取り利用した。パッケージ追加・更新は行っていない。リポジトリ直下から次を実行する。

```bash
env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B output/toc_delivery/d_shots_audit_20261113/audit_saved_shots.py

env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B output/toc_delivery/d_shots_audit_20261113/build_validation_plan.py

env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest tests/toc_cg/test_reference.py tests/toc_pipeline/test_pipeline.py::test_actual_aoa_candidates_have_finite_scope_and_no_global_claim tests/toc_pipeline/test_pipeline.py::test_registered_config_consistency_and_runtime_defaults -q -p no:cacheprovider --basetemp /tmp/kmd-d-shots-audit-pytest
```

最初のコマンドは保存された角度・評価履歴から34個の12-qubit状態と既存4,096-shotのcountsを再生する。COBYLAやS1全体の計画作成、日列列挙、LP/IPは実行しない。最適化履歴の再生は保存角度での乱数消費を復元するためであり、新たなパラメータ最適化ではない。次のコマンドは予定seed表を作るだけで、6120回のshots実験を実行しない。pytestは既存の小規模回帰だけを使う。

既存実験を再実行する`run_ad_experiments.py`、`audit_d_macro_scope.py --include-s1`、外部サービスは今回実行していない。後者の全列参照は既存保存ログを読み取り照合した。

全検査・文書保存後の保全照合と成果物hash更新は、`python -B output/toc_delivery/d_shots_audit_20261113/finalize_audit.py`。最終記録は新規監査ファイル38（報告文書2を含む）、既存ファイル変更0。

## 成果物

- `AUDIT_SUMMARY.json`：主S1の集計、有限マクロの距離/時間、環境と監査資源。
- `S1_ALL_CONDITIONS.csv/json`：全7保存D条件の訓練・最終標本数と結果。独立7反復の意味ではない。
- `S1_KERNEL_CALLS.csv`：34局所回路の深さ、seed、nfev、取得数、再生一致。
- `S1_BITSTRING_FREQUENCIES.csv`：全64 one-hot基底×34回路。0観測も含め、頻度と理想確率を別記。
- `S1_MACRO_CANDIDATES.csv`：全102経路の距離、便所要時間、2roundの頻度/理想確率、出所。
- `S1_EVENT_PROBABILITIES.csv`：回路別・事象別の95% exact区間。部分便VALIDと完全マクロ、proxy負RC等を分離。
- `S1_FROZEN_PARAMETER_BANK.json`：将来の固定角度診断用bank。既存ソルバーがこのファイルを使うようには変更していない。
- `ANALYTIC_COVERAGE_PROJECTIONS.csv`：6条件の理想分布からの解析予測。shots感度実験ではない。
- `BINOMIAL_DESIGN.csv`、`REPETITION_PRECISION.csv`：必要p、0観測区間、反復数の精度。
- `B_D_PLAN_LINEAGE.json`：Bからの経路/seed再利用と、Dの日列masterによる車両・時刻再割当を区別。
- `PILOT_SEEDS.csv`、`SHOT_EXPERIMENT_PLAN.json`：未実行の検証計画・6120の予定測定seed。製品設定ではない。
- `VALIDATION.json`：4,126項目の監査検査。`PLAN_VALIDATION.json`は計画seed等の別検査。
- `FINAL_VALIDATION.json`：最終18項目の数値・文書・保全照合。`FINDINGS.csv/json`は8件の重要度・コード行・影響・必要な修正・修正後検証。
- `SEED_128BIT_COMPATIBILITY.json`：予定seed形式を実際のQiskitで受け取れることを1-qubit、32shots×同seed再生で確認した記録。性能実験ではない。
- `PYTEST.log`：関連21テスト合格。旧207テスト全体を今回再実行したわけではない。
- `PRESERVATION_BEFORE.json`：既存235ファイルのhash。凍結需要8・src/kmd_toc・設定・S1等の結果/計画を含む。
- `ARTIFACT_INDEX.json`：新規監査成果物のhash。

## 失敗・仮説不一致の保全

`PYTEST_INITIAL_IMPORT_FAILURE.log`はPYTHONPATH未指定による初回失敗。`AUDIT_INITIAL_SERIALIZATION_FAILURE.log`は新規監査スクリプトのNumPy整数保存エラー。環境と監査保存処理だけを修正し、既存アルゴリズムは変更していない。

`INITIAL_PLAN_IDENTITY_CHECK.json`は、B/Dの全物理便が同一という仮説が不一致だった記録。経路集合は同じ17本だが、割当と積込開始時刻は10/17便で変わっていた。これを消去せず、正確な帰属を`B_D_PLAN_LINEAGE.json`へ記録した。

監査報告は`docs/research/D_SHOTS_AUDIT.md`、実験計画は`docs/research/D_SHOTS_VALIDATION_PLAN.md`。shots実験の採用値はHOLD/null。8,192を本実験採用済みと読み替えない。

## 方法の一次資料

- Qiskit2.1 Statevector：[IBM公式API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.1/qiskit.quantum_info.Statevector)。インストール済み関数本文を`INSTALLED_STATEVECTOR_SAMPLE_COUNTS.py.txt`へ保存。
- 独立子系列：[NumPy公式](https://numpy.org/doc/stable/reference/random/parallel.html)。実環境2.3.1でSeedSequenceと128-bit整数seedの機能を確認。
- 二項exact区間：[SciPy1.16公式](https://docs.scipy.org/doc/scipy-1.16.0/reference/generated/scipy.stats.binomtest.html)、[NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)。

問い合わせ・有料サービス・実機ジョブ・本実験・commit/pushは行っていない。
