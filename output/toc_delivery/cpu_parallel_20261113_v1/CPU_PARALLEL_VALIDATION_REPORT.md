# CPU並列化の実装・検証報告（2026-11-13）

判定：**並列実装はGO（Linux・人工6/20地点で検証）／本実験開始はHOLD**。B/C/Dそれぞれを4CPU・4内部プロセスで実行する方式を通常CLIの既定へ接続した。本実験、S1〜S3道路配送計画、道路予備実験は実行していない。

## 完了内容

- B/C/Dおよび量子なしD対照を同一の4CPU枠で内部マルチスタート。各枝native thread=1、外側の手法間実行は逐次。
- 枝ごとのseedをSeedSequenceで派生し、全PID・affinity・成功/失敗・D/W・CPU/wall・RSS・量子処理を保存。内部4枝は外側1試行。
- 親時計開始後に共通入力を読み込み、全枝の探索、停止/join、全利用可能候補の独立検査、選択後二重検証を実施。最小D、次にW、枝番号の固定規則で選択。
- τの80%で全枝を停止し、20%を親検証用に予約。実測T>τは失敗。準備/出力は別計時。
- 終了した全枝を含むCPU・量子総量を保存。欠測枝がある場合は全量null、観測済み部分と区別する。
- CLIで旧逐次設定や旧逐次登録の無指定実行を拒否。過去再現のみ専用flagで許容。
- 共通標準7出力と独立検査へ接続。道路形状監査のaffinity検査も4CPU/旧1CPU双方に対応。

## 実際の小規模結果

すべて人工ネットワーク上の実装確認。大田区実道路の性能値・佐川急便の実測・統計的性能推定ではない。W=30分上限、外側τ=20秒、各1試行。

| 配送先 | 手法 | D [km] | W [分] | 親T [秒] | 全プロセスCPU [秒] | 4枝結果 |
|---:|---|---:|---:|---:|---:|---|
| 6 | B | 0.834 | 0.00 | 2.515196 | 0.079035 | 全枝VALIDATED |
| 6 | C | 0.812 | 0.00 | 10.209458 | 28.105128 | 全枝VALIDATED |
| 6 | D | 0.834 | 0.00 | 4.595850 | 0.644861 | 全枝VALIDATED |
| 6 | D_CLASSICAL_CONTROL | 0.834 | 0.00 | 2.093800 | 0.177844 | 全枝VALIDATED |
| 20 | B | 2.641 | 0.00 | 2.044489 | 0.091530 | 全枝VALIDATED |
| 20 | C | 2.217 | 0.00 | 8.868613 | 28.121217 | 全枝VALIDATED |
| 20 | D | 2.641 | 0.00 | 5.033046 | 0.736624 | 全枝VALIDATED |
| 20 | D_CLASSICAL_CONTROL | 2.641 | 0.00 | 1.800095 | 0.203750 | 全枝VALIDATED |

各8条件で4PID・4CPUと探索時間区間の重なりを確認し、全枝を回収した。Cでは全プロセスCPU時間が親wall時間を上回り、実際のCPU並列計算とも整合する。逐次版との速度比は今回測定していない。B/DのD/W一致はこの人工問題の観測であり、量子由来改善の証拠ではない。

共通ライブラリ準備は 129.351725 秒。各試行の待機プロセス起動はparallel_setup.jsonに別記。長い初回importをTから除いたことを速度向上として主張しない。

各親max RSSは153,600 KiB、各プロセスhigh-water mark合計上界は584,592〜687,548 KiB。共有ページを含む合計であり、同時物理RSSピークではない。S1〜S3のメモリを外挿しない。

極小τ=1e−9秒のBはTIME_BUDGET_EXCEEDEDとなり、4枝を回収し、架空のplan.jsonを作成しなかった。失敗経過時間・枝状態を保持している。

## 検証

| 検査 | 実測結果 | 証拠 |
|---|---:|---|
| 既存回帰pytest | 233 passed / 179.62秒 | [REGRESSION_TESTS.log](REGRESSION_TESTS.log) |
| 新規pytest | 13 passed / 6.18秒 | [UNIT_TESTS_FINAL.log](UNIT_TESTS_FINAL.log) |
| 実並列・停止・計時・標準出力 | 90/90 | [PARALLEL_SMOKE_VALIDATION.json](smoke/PARALLEL_SMOKE_VALIDATION.json) |
| 生JSON/NPYから独立再計算 | 290/290 | [INDEPENDENT_DWT_VALIDATION.json](smoke/INDEPENDENT_DWT_VALIDATION.json) |
| 道路形状監査のCPU検査互換性 | 3/3ケース | [CPU_AFFINITY_COMPATIBILITY.json](CPU_AFFINITY_COMPATIBILITY.json) |
| ソース構文（実行せずcompile） | 9/9 | 同上 |

新規13件と既存233件は計246テスト。初回10件は新規13件に含まれ、重複加算しない。回帰の11 warningsは既存SWIG非推奨3件、旧route-pairs fixtureのfork警告8件。新しい並列入口のfork条件はnative thread=1かつimport-onlyである。SciPy→HiGHSのthreads転送警告は枝実行ログに残す。

## 実装・変更箇所

新規：AGENTS.md、src/kmd_toc/dwt/parallel.py、configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json、scripts/verify_cpu_parallel.py、tests/toc_dwt/test_cpu_parallel.py、docs/research/CPU_PARALLEL_EXECUTION.md。

既存10ファイルの意図した変更：worker（並列dispatch/CPU計測）、experiment（登録CPU/dispatch）、methodsとpipeline/hybrid（HiGHS native上限）、run_dwt/run_dwt_bundle（既定設定・旧再現flag・小規模既定）、audit_dwt_standard_geometry（並列affinity検査）、DWT_EXPERIMENT_DESIGN/DWT_STATISTICAL_PROTOCOL/DWT_PILOT_DESIGN（末尾の実行方式追補）。探索アルゴリズムの置換や研究上の新しい統計条件の採用はしていない。並列内部探索により結果分布は旧版と変わり得る。

変更前後はSOURCE_BEFORE/SOURCE_AFTER、差分はSOURCE_CHANGES.patch。保全対象406ファイル＋追加監査スクリプトの照合はPRESERVATION_FINAL.jsonに記録する。README・.gitignoreの既存変更を保持し、凍結需要8ファイル・旧OD・過去結果・旧設定を変更しない。

## 限界・次の作業

- 実プロセス検証はLinuxのforkのみ。spawn経路は実装・構文確認済みだが実プロセスでは未検証。別環境への保証はしない。
- 新しい4CPU条件での道路小規模適格性確認、実行時間/メモリの予備測定、統計的n/rとshotsの採用は未完了。S1〜S3本実験は未実施。
- 並列化自体は量子固有改善を意味しない。Dの全枝量子処理と古典対照を分けて評価する。
- README全面監査、AのWeb参照化、最新J/仮説と既存実装の整合性は別作業として残す。今回の旧設定継承を研究上の採用決定と解釈しない。
- commit/pushは実施していない。

## 環境

Python 3.12.11 / Linux-6.8.0-147-generic-x86_64-with-glibc2.39 / AMD EPYC 9684X 96-Core Processor。割当0,1,2,3を使用。

numpy 2.3.1, scipy 1.16.0, ortools 9.14.6206, qiskit 2.1.1, pytest 8.4.2。環境の詳細は[ENVIRONMENT.json](ENVIRONMENT.json)。

再現手順は[REPRODUCE.md](REPRODUCE.md)、今後の方針は[CPU_PARALLEL_EXECUTION.md](../../../docs/research/CPU_PARALLEL_EXECUTION.md)。
