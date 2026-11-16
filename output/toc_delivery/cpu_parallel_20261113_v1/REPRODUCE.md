# CPU並列化の再現手順

リポジトリroot `/home/takuma/kmd-analysis` で実行。既存環境 `/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python`、版はENVIRONMENT.json。以下は人工問題とテストのみで、道路予備/本実験を起動しない。

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest tests/toc_dwt/test_cpu_parallel.py -q -p no:cacheprovider
```

既存回帰は以下の範囲を実行した。スレッドの多重化を避け、単一CPUにテストプロセスを固定した。新規並列実プロセス確認はこの制限とは別に行う。

```bash
taskset -c 4 env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest tests/toc_dwt/test_dwt.py tests/toc_pipeline tests/toc_baseline_a tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement tests/test_toc_contracts.py -q -p no:cacheprovider
```

人工6/20地点でB/C/D/量子なし対照の実プロセスを確認する場合は、**未使用の新しい出力パス**を指定する。以下は次回用の例で、この再実行先は今回作成していない。

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B scripts/verify_cpu_parallel.py --output output/toc_delivery/cpu_parallel_recheck_01 --prepare-only
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B scripts/verify_cpu_parallel.py --output output/toc_delivery/cpu_parallel_recheck_01
```

4CPUのaffinityが必要。不足時はエラー。実行時間はライブラリ初回importとストレージ負荷の影響を受ける。各外側試行20秒、4内部枝、固定された試験用root seedから全枝seedを導出しspec.jsonに保存する。既存trialがあれば上書きせず停止する。極小予算の失敗検査も行う。人工GeoJSONは道路形状を捏造せずgeometry=nullとして保存する。

通常のB〜D入口は scripts/run_dwt.py、既定は configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json。登録/実行は研究実験になるため、今回の再現確認には含めない。旧逐次再現のみ --historical-serial-reproduction を使用する。既存保存結果の上書きはしない。
