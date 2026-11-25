# 統計仕様Freezeの検証・再現証跡

## 基準と保全

作業前HEADと作業後HEADはいずれも `ab79b9ddf52b604d5a162fc66c37b0fc967690d4`。ローカル正本は `/home/takuma/kmd-analysis`、originは `https://github.com/tkm-sano/kmd-analysis.git`。commit/push・本実験・需要生成・新規量子呼出しは0。

作業前の未コミット変更を前提として保持した。`GIT_DIFF_BEFORE.patch` と `GIT_STATUS_BEFORE.txt` が開始時の記録。開始時statusは既存未追跡成果物も全件列挙したため約14MBある。作業後は同じ大量列挙を繰り返さず、`acceptance_audit/GIT_STATUS_AFTER.txt` をディレクトリ単位のnormal表示にした。`acceptance_audit/GIT_DIFF_AFTER.patch` はHEAD基準、`acceptance_audit/TASK_CHANGES.patch` は今回の8既存ファイルだけの開始時基準差分。

`PRESERVATION_BEFORE.json` の231ファイルのうち、今回承認された既存変更8件を除く**223件すべて一致**。さらに全tracked差分を開始時と比較し、8件以外の差分は変化0。案内7件は追加通知の後ろに開始時の原文バイト列をそのまま保持し、before/に全原文を保存。CLIの今回差分は分岐6行の追加だけ。無関係な既存変更を復元/削除しない。

`acceptance_audit/PRESERVATION_AFTER.json` は上記に加え、既存勤務再生manifestの入力/OD/計画24 pinと統計POSTPROCESS_SOURCE_HASHESの2 pin、計26件の一致を記録する。過去の全sealが現在ツリーに一致すると主張するものではない。過去n/K/R報告などが既に記録している旧AGENTS等のdriftは、履歴を上書きして解消していない。

## 固定Freezeのhash

| 対象 | SHA-256 |
|---|---|
| 新統計 `FREEZE_SPEC.md` | `de48843978d08b9ef52b5f50b650152027ac5bc7e4a821e28ca5151ce8c9ba5a` |
| 新統計 `configs/statistical_scope_20261121_v1/policy.json` | `8bbb4d0d2d85cd18756d5dd8d06bebe0503ce3cb83e26c0d0693333e8888b496` |
| 旧研究仕様1〜7 | `297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be` |
| 旧FCFS運用仕様 | `51ab348d893c2044ec0d48e77b74a7d669e012c470e969cf6f971e6863578cd3` |
| 旧共通条件v1.1 | `bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2` |

最初の2つを `descriptive_v1/policy.py` の固定anchorとして検証する。本文変更に合わせて期待hashを自動再生成して承認する機能はない。コードと案内は `acceptance_audit/CODE_AND_GUIDE_HASHES.json`、証跡・最終出力は `FREEZE_SEAL.json` のチェックサムに記録。旧p/shots/最終採択/勤務・共通条件・関連実装と履歴成果物は開始時のhashと一致。

## 実行環境

統計処理: `/tmp/kmd-p1-pricing-20261118/bin/python`、Python 3.12.11、NumPy 2.3.1、Matplotlib 3.10.3、pytest 8.4.2。Linux 6.8.0-147-generic x86_64/glibc2.39。各ANALYSIS.jsonに実際のexecutable/platform/packagesと解析コード9ファイルのSHAを保存。入力証跡のSOURCE_HASHES.jsonも保存し、処理中の変化を再確認する。

旧共通完成器等の回帰テスト: `/tmp/kmd-library-validation-20261114-v2/bin/python`、Python 3.11系の既存検証環境。新たな依存インストールは行っていない。

## コマンドと結果

```bash
PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python -m pytest -q tests/descriptive_v1
# 35 passed in 20.20s, exit 0

PYTHONPATH=src /tmp/kmd-library-validation-20261114-v2/bin/python -m pytest -q tests/fcfs_v1 tests/d_final_selection_v1 tests/duty_break_v1 -k 'not existing_sources_conditions_results_seeds_unchanged'
# 114 passed, 1 deselected, 5 warnings in 20.31s, exit 0

PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/verify_statistical_scope_v1.py
# specification PASS / formal J HOLD

PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/statistical_scope_20261121_v1/audit_and_demo.py --output output/statistical_scope_20261121_v1/verified_v4
# legacy observations 30, eligible new outer trials 0, synthetic arithmetic rows 54, formal J HOLD

PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/statistical_scope_20261121_v1/finalize_audit.py --output docs/research/statistical_scope_20261121_v1/acceptance_audit
# PASS, protected unchanged 223, old source pins 26, unexpected tracked changes []
```

監査/デモ/finalizeは出力が存在する場合は上書きしない。再実行には新しい出力先が必要。finalizeも --output に未作成ディレクトリを指定して証跡を区別する。単体テストはpytestの新規一時ディレクトリを使用する。新規CLIの `--statistics-registration` 分岐もsubprocessで試験済み。

`TESTS_ACCEPTANCE.txt` と `TESTS_ACCEPTANCE.json` に新規テスト最終出力・コマンド・exitを保存。回帰は `REGRESSION_TEST_RESULT.json` に範囲・結果を記録。5警告は旧SWIGのDeprecationWarning 3件と旧HiGHSへのthreads引渡しOptimizeWarning 2件で、計算失敗ではない。1 deselectedは前作業時点のAGENTS/README等のhash固定テスト。今回のユーザーがそれらの案内更新を承認したため、旧テスト・旧sealを変更せず、今回開始時点の保全検査を実行した。回帰スイート全件PASSと表現しない。

初回はPYTHONPATH未設定の収集エラー、その後CLI表示にHOLDがない1件が失敗した。PYTHONPATH設定とCLIのformal_J_status出力追加後に解消。1試行のみのMCSEは独立性未確認と混同せずJ<2による未定義として保存し、ゼロC基準をI_dual=0へ読み替えない図注にした。最終テスト時のコードを用いてverified_v4を生成した。verified_v4より前の本作業のデモ出力も消去せず保存し、最新の証拠と区別する。

## テストの意味

記述統計/SD/MCSE、J<2、観測SD0、非有限値拒否、四分位補間、Tukey境界、外れ値保持、試行差からのSD、独立2群、I_dualのゼロ基準/厳密両立、平均I_dualと平均値代入の区別、5比較、Aの整合性ゲート、対応根拠、基準試行再使用、RNG重複、内部枝/再試行/失敗欠測、入力/計画/証跡hash、FCFS/勤務版再評価、版混在拒否、出力非上書き、固定spec改変拒否、CLI、既存原文の保全を確認した。

グラフ検査は実際のMatplotlib errorbar引数でyerr=SDを確認し、MCSEではないことを検査。上下端・箱パラメータ・ノッチなし・PNG/PDF個数・fixtureラベル・internal分離も検査した。主要8種と内部4種を生成し、距離平均SD図とI_dual箱を目視確認。これらは合成数値の図であり実配送の性能図ではない。

## 現行資料と未検証

最新出力は `output/statistical_scope_20261121_v1/verified_v4/`。current_audit/の全18統計セルJ=0、30比較スロットを保持。旧C/D30件、n/K/R6完了条件、固定経路再生9件を適格な新反復へ転用しない。A比較整合性、外側反復、対応/C参照、数値MCSE基準・資源制約、失敗欠測の最終推定対象、正式JはHOLD。新最適化・本実験を実行していないため、新しい手法優位や十分Jを確認したとは主張しない。

将来の保存計画の登録形式・再現方法は[INPUT_AND_REPRODUCE.md](INPUT_AND_REPRODUCE.md)。学術的根拠の確認範囲・取得不能は[LITERATURE.md](LITERATURE.md)。今回のFreezeは統計解析範囲のみであり、勤務条件の現実可行性・n/K/R/停止条件・共通T・D正式全体入口などの既存HOLDを解除しない。
