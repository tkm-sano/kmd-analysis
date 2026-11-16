# 再現手順

条件登録はPREREGISTRATION.json、方法はdocs/research/toc_delivery_a/A_RULE_BASELINE_SPEC.md。出力先は必ず新規ディレクトリ。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python -m pytest tests/toc_baseline_a tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement tests/test_toc_contracts.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python scripts/run_a_rule_baseline.py --output /tmp/a-rule-new-output
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OPENBLAS_NUM_THREADS=1 /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python output/toc_delivery/a_rule_v1_20261112/audit_results.py
```

人工6/20/120/240地点のみで36計画。S1〜S3は凍結読込監査と構造感度のみでD/Wを未計算。共通bundleが完成したら--inputs-rootで親ディレクトリを指定する。仮ODや新たな需要生成によるfallbackはない。
初回pytestの1失敗は一象限で角度を変えると必ず割当が変わるというテスト仮定。算法/登録パラメータを変更せず地理入力に依存する割当という検査へ修正した。旧ログを保全。
既存検査器の変更前コピーは、着手前に全バイトhashを保存し、予定したmethod_id 1箇所変更を逆転して照合した完全一致原文。その他の入口3文書は追記前の全バイトをSOURCE_BEFOREへ保存。
