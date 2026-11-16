# 再現コマンド

リポジトリrootで実行する。新しい未使用output名を使う。既存出力を削除/上書きしない。下記はcontract_checkの限定確認で、正式比較を起動しない。現環境は既存ad-pipeline-v1 Python、jsonschema 4.24.0を含む。外部インストールや実機利用は不要である。

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  -m pytest -q -rs tests/toc_comparison_v1 tests/toc_baseline_a tests/toc_dwt \
  --basetemp output/toc_delivery/comparison_reproduce_new_tests

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py register \
  --plan configs/toc_delivery/comparison_v1_20261115_A_identity_checks_r2.json \
  --output output/toc_delivery/comparison_reproduce_new_A

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py run \
  --registration output/toc_delivery/comparison_reproduce_new_A/REGISTERED.json

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py aggregate \
  --registration output/toc_delivery/comparison_reproduce_new_A/REGISTERED.json \
  --output output/toc_delivery/comparison_reproduce_new_A_tables

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py register \
  --plan configs/toc_delivery/comparison_v1_20261115_small_paths_r3.json \
  --output output/toc_delivery/comparison_reproduce_new_small

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py run \
  --registration output/toc_delivery/comparison_reproduce_new_small/REGISTERED.json

PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_comparison_v1.py aggregate \
  --registration output/toc_delivery/comparison_reproduce_new_small/REGISTERED.json \
  --output output/toc_delivery/comparison_reproduce_new_small_tables
```

小規模fixtureは `output/toc_delivery/comparison_integration_v1_20261115_inputs/ART_N12`。共通物理値を変えず12地点/4台/1バースの人工有向ODを使用し、実需要の研究結果と混ぜない。検算fixture生成は計時外のデータ準備として記録済みで、各方式はその共通入力からfresh生成する。既存S1〜S3 Route入力はそのまま参照する。

registerは、入力の共通物理検証と全file hash、凍結Aの7ファイル、設定、ソース、4物理コアを固定する。runは全入力を再読込/hash/検証してから、A直結またはBCD既存四枝を起動する。登録後にソース/凍結資産/inputが変われば拒否する。ソース版が変わった場合は新しい登録とoutputにし、旧SOURCE_SNAPSHOTを保持する。

Aの新規単独S2確認は、既存 `scripts/run_a_rule_v1.py --worker` を変更せず使用した。`output/toc_delivery/comparison_integration_v1_20261115_standalone_S2_01/manifest.json` とPROCESS.jsonに正確なコマンド/設定hash/native180秒/外側300秒を保存した。再現する場合はこのmanifestを新しい未使用directoryへ複製し、run_idを新しくして、同じ原CLIを起動する。新比較Tの参照にはこのnative時間を使わない。

最初のsmall01は90秒でBCDが初期化中に停止し、終了コード1だった。small02は登録後・実行前にPID/途中資源記録を補強したため、4件をNOT_STARTEDとして保全した。最終small03は外側420秒/BCD native90秒。これらを同じ条件の統計反復や成功率の本実験推定へ合算しない。全履歴はALL_EXECUTION_HISTORY.json、登録別の正式な集計は各tables directoryを参照する。

後続の正式manifestテンプレートは `configs/toc_delivery/comparison_v1_future_manifest_template.json`。scenario/scale/input、run集合、予算、参照件数/会員を未指定のまま実行できない。formal runには別工程での明示的許可に対応するCLIフラグも必要で、今回は使用していない。

`audit_completed_runs.py` は保存済み出力・原A計画・source snapshot・保全hashだけを読む監査で、solverや需要生成を起動しない。`build_final_report.py` はこれらの機械結果から報告を生成する。既存結果の上書きを避けるためexclusive createであり、再監査は別の新規文書directoryと参照設定で行う。
