# 実行・集計

使用した既存環境とライブラリ探索順（新規子にも同じ順序を登録する）:

```bash
export PYTHONPATH=/opt/miniconda/envs/qgpu/lib/python3.12/site-packages:src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PY=/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python
```

予備実験パイプライン全体（既存出力への上書きを拒否する。再実行時は別出力を指定し、既存結果と混ぜない）:

```bash
"$PY" scripts/run_comparison_design.py \
  --output output/toc_delivery/comparison_design_20261116_v1
```

段階別の登録済みmanifestと全試行集計はそれぞれ`selection_lean/`、`selection_retained/`、`variance/`、`confirmation/`に保存する。
`runs/*/result.json`は既存comparison_v1の四軸状態、`tables/ALL_ATTEMPTS.json`は未実行を含む予定全件。
途中でコーディネータが中断された場合、完了済み段階の自動再実行はしない。`--resume`は集計済み段階だけを再利用でき、未完段階は監査を要求する。

既存入口による集計の再現（出力ディレクトリは新規にする）:

```bash
"$PY" scripts/run_comparison_v1.py aggregate \
  --registration output/toc_delivery/comparison_design_20261116_v1/variance/REGISTERED.json \
  --output output/toc_delivery/comparison_design_20261116_v1/variance_tables_reproduction
```

選択・分散・確認結果は混ぜない。`design/*_ANALYSIS.json`は固定入力の独立Welch解析。
`design/CANDIDATES.csv`とJSONは精度/確率精度/配分/分散感度/総費用ごとの候補。
`GENERALIZATION_SENSITIVITY.json`は仮定表であり、一般化の実測結果ではない。
`TELEMETRY.json`は全枝を含む品質履歴、CPU/RSS、量子呼出し、shots、観測範囲。
生の`RESOURCE_SAMPLES.jsonl`と`native/branches/*/design_trace.jsonl`を保全する。

本実験の具体的な固定manifest作成は、研究者が精度・費用を選び、資格ゲートと必要分散を満たした場合だけ可能。
以下は引数形式の例であり、このhや費用を採用したことを意味しない:

```bash
"$PY" scripts/run_comparison_design.py \
  --output output/toc_delivery/comparison_design_20261116_v1 \
  --finalize-main --h-D 5 --rate-halfwidth 0.1 --main-budget-s 86400 \
  --allocation equal --sensitivity normal_variance_upper \
  --main-registration output/toc_delivery/comparison_design_20261116_v1_main_S2
```

この操作も本実験を実行しない。候補なし・資源超過・未識別分散・code/config/input変更時は拒否する。
固定manifestは全seed・実行順序・A参照会員・試行一覧hashを持ち、途中のp値に応じた件数変更を拒否する。
実行する場合の既存コマンドは以下で、本作業では実行しない:

```bash
"$PY" scripts/run_comparison_v1.py run \
  --registration output/toc_delivery/comparison_design_20261116_v1_main_S2/REGISTERED.json \
  --authorize-formal-experiment
```

検証:

```bash
"$PY" -m pytest tests/toc_comparison_v1 tests/toc_dwt/test_dwt.py \
  tests/toc_dwt/test_cpu_parallel.py -q --disable-warnings
```

上記solver検証と科学予備実験の計時は同時実行しない。
`validation/`に互換修正前の失敗、修正後89件、新規9件のログを保存。
人工fixtureでの全5手法の確認は`output/toc_delivery/comparison_design_20261116_v1_smoke_r2/`。
初回smoke中のソース変更でガードが作動した記録は`..._smoke/`に保全し、研究予備へ流用しない。
`..._report_fixture/`は1成功/cellの分散不足をHOLDとする集計器チェックであり、研究実測ではない。

全5手法で同一Rの案と、分散・費用に応じたR_aの案を直接比較する追加集計（ソルバーを実行しない）:

```bash
"$PY" scripts/run_comparison_design_supplement.py \
  --root output/toc_delivery/comparison_design_20261116_v1 \
  --output output/toc_delivery/comparison_design_20261116_v1/design_supplement
```

初期`CANDIDATES`のequalはC/D間の均等配分である。全手法均等は追加表の`uniform_all`を使用する。
追加表は実測の試行間gap、親+子メモリの保守的proxy、明示的な準備/回収予備費用を分けて示す。
ディスク・共有ホストの絶対上界を証明する値ではない。分散不明行のRは率だけの候補で、連続品質の精度達成を主張しない。
追加集計コード自体のhashと入力登録hashを保存し、固定した実行コードを変更しない。

最終数値・報告の再生成（既存実験出力へ変更を加えない）:

```bash
"$PY" docs/research/comparison_design_20261116_v1/summarize_measurements.py
"$PY" docs/research/comparison_design_20261116_v1/write_final_report.py
```

全出力hash監査（FINAL_AUDITの保存先が未作成の場合。既存監査は保全し、再実施時は保存先を別にする）:

```bash
"$PY" docs/research/comparison_design_20261116_v1/audit_results.py \
  --output docs/research/comparison_design_20261116_v1/FINAL_AUDIT_reproduction.json
```

監査は全計時終了後に読み取り専用の8スレッドでhashを照合する。手法間の同時計時には使わない。
