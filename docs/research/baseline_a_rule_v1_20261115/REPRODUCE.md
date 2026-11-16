# 再現方法

リポジトリrootで保存済みPython環境を使用する。出力ディレクトリが存在すれば拒否するので、例の出力名は新しい名前へ置き換える。既存需要/ODを再生成しない。READMEや旧A2を変更しない。

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  -m pytest -q tests/toc_baseline_a

PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_a_rule_v1.py \
  --config configs/toc_delivery/a_rule_v1_20261115.json \
  --output output/toc_delivery/a_rule_v1_reproduce_new_main

PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_a_rule_v1.py \
  --config configs/toc_delivery/a_rule_v1_20261115_berth_sensitivity.json \
  --output output/toc_delivery/a_rule_v1_reproduce_new_berths
```

主設定CLIはS1/S2/S3とS2再実行の4試行、感度CLIはS2の2/8バース2試行だけを登録し逐次実行する。入力、ソース、config hashを確認し、共通ライブラリimportは入力前に別計測する。4物理コアを解決できなければエラーとし、Aはその中の1コアで1プロセスを使う。native threadはworkerが1へ固定する。変更済み環境のhashが違う場合、元結果と同版再現と主張しない。

感度CLIは今回2バースがNO_FEASIBLE_PLANだったため終了コード1である。全試行はSUMMARY.jsonに保存される。失敗を消して成功へ変換しない。正式実験や無制限再試行の入口ではない。

各runのmanifest.json、plan/rejected_plan、events、search、metrics、validation、PROCESS、OUTPUT_HASHESを参照する。rootのREGISTRATION/SOURCE_SNAPSHOT/environment/SUMMARY/SOURCE_STABILITYにコード・設定・環境と試行契約がある。

`audit_results.py` と `build_report.py` は今回の保存済み結果を検査/集計するスクリプトであり、新しい科学計算を起動しない。成果物の既存上書きを避けるためexclusive createを使用している。再集計する場合は別の新規文書ディレクトリへコピーしてOUTPUTS/参照を設定する。元の監査記録を削除して再実行しない。

IMPLEMENTATION_SNAPSHOT.tar.gzは今回追加したコード・設定・テストと確定仕様を含む。各出力rootのSOURCE_SNAPSHOTは実行時の既存共通コードも含む。元の凍結需要・Route ODは登録パスとピンを維持して参照する。ソース公開/可搬環境のみで研究入力一式が自動取得されることを保証するものではない。
