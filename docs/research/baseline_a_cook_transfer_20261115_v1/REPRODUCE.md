# 再現手順

本手順は少数ルートの外部順序試験である。大田区の新規需要生成、S1〜S3本実験、B/C/D実行を含まない。既存出力名は使用せず、必ず新しい出力ディレクトリを指定する。

## 保存された対象

- 設定：`configs/toc_delivery/a_cook_transfer_v1.json`
- 入口：`scripts/run_cook_transfer_study.py`
- 固定入力：`output/toc_delivery/a_cook_transfer_20261115_plan04/`
- 推論実行：`output/toc_delivery/a_cook_transfer_20261115_run02/`
- 最終集計：`output/toc_delivery/a_cook_transfer_20261115_finalized01/`（同じ保存提案からの再集計であり、追加推論ではない）
- 原データ：`/home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1/`
- 著者コード：`/home/takuma/.cache/kmd-analysis/external/cook_jpt_amz_dc4ebc0_20261115_v1/`
- Python環境：`/home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python`

著者commitは`dc4ebc0aa091d4d1eb7dc7d9b9b2d8f8c19664ce`、ライセンスはMITである。原本を`AUTHOR_SOURCE.tar.gz`へ保存した。LKHソースに変更を加えていない。原データのライセンスは保存済みMANIFESTのCC BY-NC 4.0であり、著者コードのMITと区別する。

環境はPython3.13.5、NumPy2.3.5、natsort8.4.0である。実行時のCPU affinity・gcc版・ソースとバイナリhashは最終出力のENVIRONMENT.jsonにある。仮想環境Pythonのシンボリックリンクを実体へ解決すると基底Pythonになり得るため、そのままのパスを渡す。

## 著者コードをコンパイルする場合

保存した版を新しい専用ディレクトリへ展開するか、公開リポジトリから当該commitを取得する。原版のトップMakefileは内部で`-j16`を指定するため、今回は次のSRCだけをコンパイルした。計算時は専用入口が1コアへ固定する。コンパイル時間は推論時間に含めずBUILD.jsonへ保存した。

```bash
make -C /home/takuma/.cache/kmd-analysis/external/cook_jpt_amz_dc4ebc0_20261115_v1/LKH-AMZ/SRC -j 1 all
```

著者`model_build.sh`/`model_apply.sh`はそのまま実行しない。本入口は必要な学習・TSPLIB生成PythonとCソルバーを隔離出力へ呼ぶ。2定式化と著者の1%選択規則を使用し、元の動的時間配分・16並列は本試験の明示上限へ置き換えた。

## 分割の再作成と再実行

まずplanを再作成できる。既存キャッシュ3ファイルのhashを検証し、保存済みの過去使用ID・拠点日を除外して、同じ24 IDを選ぶ。新しい評価実績をモデルへ渡す工程ではない。

```bash
timeout 120s /home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python -B \
  scripts/run_cook_transfer_study.py plan \
  --data /home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1 \
  --output output/toc_delivery/a_cook_transfer_new_plan
```

保存済みplan04を使った再実行は次である。外側上限960秒、内部900秒である。time-limit停止による探索結果の変動を記録し、同じ順序を保証するという意味の再現性とは区別する。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 timeout 960s \
  /home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python -B \
  scripts/run_cook_transfer_study.py run \
  --data /home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1 \
  --plan output/toc_delivery/a_cook_transfer_20261115_plan04 \
  --output output/toc_delivery/a_cook_transfer_new_run \
  --code /home/takuma/.cache/kmd-analysis/external/cook_jpt_amz_dc4ebc0_20261115_v1 \
  --author-python /home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python
```

全提案を固定した後に公式scorerで採点する。`SUMMARY.json`に平均、`METRICS.json`に全ルート、`PROCESS_CALLS.json`に未選択・再実行を含む全プロセス、`SOLVER_TRACES.json`に2定式化と選択理由が残る。平均だけを保存する方式ではない。

本実行run02で生じた集計保存時の型変換不具合から、探索を繰り返さず復帰した実際のコマンドは次である。保存提案とモデルのhashを照合し、新規出力へコピーした後、指標と照合結果だけを再計算する。修正後の通常runには同じ型変換修正が含まれる。

```bash
timeout 120s /home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python -B \
  scripts/run_cook_transfer_study.py finalize \
  --data /home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1 \
  --plan output/toc_delivery/a_cook_transfer_20261115_plan04 \
  --existing-run output/toc_delivery/a_cook_transfer_20261115_run02 \
  --output output/toc_delivery/a_cook_transfer_new_finalization \
  --code /home/takuma/.cache/kmd-analysis/external/cook_jpt_amz_dc4ebc0_20261115_v1
```

## 独立監査

次の監査は推論を再実行しない。元の評価実績と行列から訪問集合・有向辺・閉路時間を再集計し、著者自身のtour→JSON変換とも照合する。

```bash
python -B docs/research/baseline_a_cook_transfer_20261115_v1/audit_results.py \
  --run output/toc_delivery/a_cook_transfer_20261115_finalized01 \
  --plan output/toc_delivery/a_cook_transfer_20261115_plan04 \
  --data /home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1 \
  --code /home/takuma/.cache/kmd-analysis/external/cook_jpt_amz_dc4ebc0_20261115_v1 \
  --author-python /home/takuma/.cache/kmd-analysis/venvs/cook-reproduction-v1/bin/python \
  --output output/toc_delivery/a_cook_transfer_new_audit
```

回帰検査は次である。既存テスト環境を使い、研究用の凍結入力・旧実行ファイルは変更しない。

```bash
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest -q \
  tests/toc_baseline_a/test_cook_transfer.py \
  tests/toc_baseline_a/test_sequence_validation.py
```
