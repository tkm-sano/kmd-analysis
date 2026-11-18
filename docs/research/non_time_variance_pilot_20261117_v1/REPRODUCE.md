# 再現・継続入口

既存環境を使う（install/updateしない）。実行前にFINAL_AUDIT/REGISTRATION_LOCK/現行プロセスを確認する。

```bash
cd /home/takuma/kmd-analysis
export PYTHONPATH=/opt/miniconda/envs/qgpu/lib/python3.12/site-packages:src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
pilot_python=/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python
pilot_entry=docs/research/non_time_variance_pilot_20261117_v1/pilot.py
pilot_output=output/toc_delivery/non_time_variance_pilot_20261117_v1
"$pilot_python" -B -m pytest docs/research/non_time_variance_pilot_20261117_v1/test_pilot.py tests/toc_termination_v1 -q
"$pilot_python" -B "$pilot_entry" validate "$pilot_output"
"$pilot_python" -B "$pilot_entry" run "$pilot_output"
"$pilot_python" -B "$pilot_entry" aggregate "$pilot_output"
"$pilot_python" -B docs/research/non_time_variance_pilot_20261117_v1/finalize.py "$pilot_output"
```

registerは初回のみ。既存成果物があると拒否する。同IDを作り直したり完了試行を再実行しない。runは登録75件以外を起動せず、完了失敗も含めskip、開始済み未回収は拒否する。flock/残存子チェックは二重起動防止用。未完了がある場合は生ログ/子PIDの回収状況を先に監査し、同じ試行の再起動で埋めない。登録改変/設定不一致は拒否。ソルバーtimeoutのオプションはなく、ツールpollが切れてもソルバー打切りにはしない。

aggregate/finalizeは既存の結果を読み新IDの集計・報告だけを更新する。旧audit_termination_rules.pyは各cell1件のA参照と未開始の扱いが本予備に合わないため、新集計へ直接適用しない。枝カウンタ・物理二重検査は既存形式を再利用する。SOURCE_SNAPSHOTは別ディレクトリへ復元しhash検査する。元workspace/旧成果へ上書き展開しない。凍結入力/ODはREGISTEREDの既存パスを読み、別環境では同版依存とVeRyPy source資産も必要。異なるホスト/コア/依存条件は同条件のT標本へ混合しない。

MAIN_MANIFEST.jsonは非実行。正式R/精度/比較family/seed/順序/A時間参照会員をnullに保つ。本入口では本実験を開始できない。
