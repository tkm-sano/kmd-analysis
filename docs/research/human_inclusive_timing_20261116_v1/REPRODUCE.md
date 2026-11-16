# 人手を含むAの操作と再現

リポジトリrootから既存環境を使う。出力名は未使用のものにする。人手の実測は実際の計画担当者が操作し、他の作業を行うときは休止を記録する。下のコマンド例は人手計測を自動実施したという意味ではない。

開始時に全経過の上限を明示する。`--session-wall-limit-s`には観測前に登録した秒数を指定する。例では値を決めていないため、以下の必須環境変数が未設定なら起動しない。

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_a_human_v1.py start --scale S1 --operator planner_01 \
  --session-wall-limit-s "${A_HUMAN_SESSION_LIMIT_S:?事前登録した上限秒が必要}" \
  --output output/toc_delivery/a_human_v1_new_S1
```

作成されたstops.csvとvehicles.jsonを読み、**人が**assignment.csvを編集する。列は`vehicle_id,sequence,stop_id`である。各地点を一回だけ割当し、車両内sequenceを1から連番で記す。空車両には行を作らない。一車両120地点を超える入力は拒否する。訪問順をNNや旧Aの出力で自動作成して、人手作成と申告してはならない。

計算と二重検査を起動する。

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_a_human_v1.py evaluate --session output/toc_delivery/a_human_v1_new_S1
```

不正・勤務超過なら棄却結果を読み、人がCSVを修正してevaluateを再実行する。前のattemptは残る。成立後、人が計画とイベントを確認する。修正していなければ、次で人手作成と最終確認を申告する。

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  scripts/run_a_human_v1.py accept --session output/toc_delivery/a_human_v1_new_S1 \
  --attest-human-assignment-and-order
```

休止は`mark --stage PAUSED`、再開は`mark --stage HUMAN_PLANNING`、成立計画のレビューへ戻る場合は`mark --stage HUMAN_REVIEW`を使う。中止は`abort --reason 理由`で記録する。RESULT.jsonのTが人手を含む主値、T_programが機械段階合計、T_humanが申告された人手段階の経過である。人の注意時間の独立測定ではない。

S2/S3はstartのscaleと新出力名を変える。同一人物のS1作成経験が次の規模へ影響し得るため、順序・経験を別記する。今回、これらの人手実測や正式実験を実施していない。

実装検証の再現は以下である。既存結果の上書きを避け、basetemp名を新しい名前へ変更する。

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  -m pytest -q -p no:cacheprovider \
  --basetemp=output/toc_delivery/a_human_v1_reproduce_fixture_new \
  tests/toc_baseline_a/test_human_v1.py tests/toc_baseline_a/test_rule_v1.py
```

この試験では自動作成した人工CSVだけを使う。実CLIの開始・失敗・修正・検証・最終確認・既存出力拒否と短い強制上限を確認するが、人手時間を実測したとは扱わない。
