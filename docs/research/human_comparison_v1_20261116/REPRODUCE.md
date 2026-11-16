# 再現手順

既存コード・設定・OD・需要を変更しない。Pythonはローカルの `/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python` を使用した。新しく依存パッケージをインストールしていない。B/C/Dは不足する既存依存を `/opt/miniconda/envs/qgpu/lib/python3.12/site-packages` から読み込む。実際の版とパスはENVIRONMENT_PRECHECK.jsonおよび各子プロセスのRESULT.jsonを参照する。

## 限定実経路チェック

以下は人工12地点専用であり、人間の正式実測に使用しない。出力先は毎回新しい名前にする。各方式の上限240秒・機械200秒・native45秒、メモリ8192MiB、A〜D順次実行である。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
 docs/research/human_comparison_v1_20261116/run_limited_check.py \
 output/toc_delivery/human_comparison_v1_CHECK_NEW_ID
```

実行前のmanifestをLIMITED_VALIDATION_PLAN.jsonへ保存する。CLI_*.jsonに全コマンド・終了コード・標準出力を保存する。native/branches以下の未選択枝も残す。登録時点のソースsnapshotが正本であり、ソース変更後の旧registryは現在コードで無理に受理せず、snapshotを隔離環境で再現する。

path01は初回、path02は計時内訳の修正版である。path02の事後検証では、共有側の無関係な新規ソース更新をガードが検出したため、保存snapshotから検証した。再検証に使った展開済みソースは以下にある。新しい出力先を指定すれば、元の拒否ログを上書きせず再集計できる。

```bash
python output/toc_delivery/human_comparison_v1_20261116_path02/verification_source_snapshot/scripts/run_human_comparison_v1.py \
 --mode human_inclusive aggregate \
 --registration output/toc_delivery/human_comparison_v1_20261116_path02/registration/REGISTERED.json \
 --output output/toc_delivery/human_comparison_v1_PATH02_REAGGREGATE_NEW
```

正式計測では、事前にソースを隔離・固定した作業場を準備する。登録後のコード変更を無視する設定は設けない。今回のsnapshot補足設定とhashはSOURCE_ARCHIVE_VERIFICATION.json、拒否された共有ファイルのhashはARCHIVE_VERIFICATION_SETUP.jsonに保存した。

## 人手セッション

正式templateはそのままでは実行できない。HUMAN_MEASUREMENT_PROTOCOL.mdに従って別manifestへ実際の担当者・日時・手順・順序・上限・計画試行数・統計方針・実行許可を記入する。事前に対象caseを見ない。以下の `python` は上記環境、PLAN、REG、SESSION、RUN、IDは実際の新規値に置換する。

```bash
python scripts/run_human_comparison_v1.py --mode human_inclusive register --plan PLAN --output REG_DIR
python scripts/run_human_comparison_v1.py --mode human_inclusive prepare --registration REG_DIR/REGISTERED.json --run-id RUN --output SESSION --authorize-observation
python scripts/run_human_comparison_v1.py --mode human_inclusive start --session SESSION --confirm-unseen
python scripts/run_human_comparison_v1.py --mode human_inclusive activity --session SESSION --state begin --task assignment_order --actor ID
# この後に人間が需要を読み、車両割当・順序を決めてSESSION/assignment.csvへ入力する。
python scripts/run_human_comparison_v1.py --mode human_inclusive evaluate --session SESSION
# 棄却ならcorrectionの作業開始→人間によるCSV修正→evaluate。全履歴を保存する。
python scripts/run_human_comparison_v1.py --mode human_inclusive activity --session SESSION --state begin --task review --actor ID
python scripts/run_human_comparison_v1.py --mode human_inclusive accept --session SESSION --attest-human-authored --attest-reviewed
python scripts/run_human_comparison_v1.py --mode human_inclusive verify --registration REG_DIR/REGISTERED.json --session SESSION
```

休止はactivityのstate=end/task=pause、再開はbeginとする。abortは理由を明示する。異常終了・boot変更はrecoverで理由を記録する。Aのrun-systemを呼んでも自動計画は作られない。

B/C/Dの人間操作を含む場合もworkflow=humanでprepare/start/activity/input_operation/evaluate/review/acceptを使う。担当者が操作する工程をsystem_onlyと偽って計時外へ置かない。人間操作を必要としない登録済みsystem_onlyなら次を用いる。

```bash
python scripts/run_human_comparison_v1.py --mode human_inclusive run-system --registration REG_DIR/REGISTERED.json --run-id B_RUN --output B_SESSION --authorize-observation
python scripts/run_human_comparison_v1.py --mode human_inclusive aggregate --registration REG_DIR/REGISTERED.json --output NEW_SUMMARY_DIR
python scripts/run_human_comparison_v1.py --mode human_inclusive adopt --registration REG_DIR/REGISTERED.json --output NEW_ADOPTION.json
```

旧プログラム比較は `--mode legacy_program_only` を明示して旧run_comparison_v1.pyへ引数を渡す。human-inclusiveの時間と混ぜない。

## 回帰検証

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest \
 -q -p no:cacheprovider --basetemp=output/toc_delivery/human_comparison_v1_UNIT_NEW_ID \
 tests/toc_comparison_v1/test_human_comparison.py \
 tests/toc_baseline_a/test_human_v1.py tests/toc_baseline_a/test_rule_v1.py \
 tests/toc_comparison_v1/test_human_analysis_additional.py \
 tests/toc_comparison_v1/test_contract_and_evaluation.py tests/toc_comparison_v1/test_process_control.py
```

正式実験と同時にテストを走らせない。検証ログは本ディレクトリのTEST_*.log、最終記録はVALIDATION_RECORD.mdを参照する。
