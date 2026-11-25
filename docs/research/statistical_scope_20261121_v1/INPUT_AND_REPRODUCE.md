# 新しい統計入口と入力登録

## コマンド

```bash
PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/verify_statistical_scope_v1.py
PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/analyze_descriptive_v1.py --registration /absolute/new/registration.json --output /absolute/new/analysis
# 同じ現行統計入口
PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/analyze_dw.py --statistics-registration /absolute/new/registration.json --output /absolute/new/analysis
```

出力先は未作成の専用ディレクトリが必要。既存結果に上書きしない。図が不要なら `--no-figures`。ソルバー・需要生成・量子処理は呼ばない。通常の `analyze_dw.py --input ... --plan ...` のFCFS評価と、`--historical-reproduction` の明示的な旧解析は維持する。新統計と履歴モードを同時指定しない。

再現用の読み取り専用監査と算術・図表検証は以下。出力先を毎回変える。

```bash
PYTHONPATH=src /tmp/kmd-p1-pricing-20261118/bin/python scripts/statistical_scope_20261121_v1/audit_and_demo.py --output /absolute/new/statistics_check
```

`current_audit/` は旧資料の適格性を記録した監査であり、新規最適化結果ではない。`synthetic_fixture/` は数値を明示した54行の算術試験用データ。配送需要を生成していない。**合成データのD/W、SD、MCSE、両立割合を配送手法の性能として引用しない。** 全図に専用の警告を付けている。

## 実データ登録の要件

JSONの `version` は `descriptive-statistics-20261121-v1`、`data_role` は `verified_outer_trials`。実データにD/Wのスカラー列だけを渡しても集計対象にならない。`synthetic_statistics_fixture` は算術検証専用で、実データの検証を迂回する用途にしない。

- `cases` はS1/S2/S3をキーとする固定問題定義。各規模の `input_path`、`base_problem_hash`、`od_hash`、`operating_version`、`comparison_profile` を登録する。通常FCFSは `FCFS_v1`、勤務版は `duty-break-20261121-v1` と明示し、勤務版では `rest_options` を指定する。1集計で1規模1問題・1運行版。複数独立問題を同じセルへ無条件にプールする入力は受けない。需要問題間の変動を評価する場合は問題別出力と別の実験設計が必要。
- `trials` は事前の実行順 `order`、一意 `trial_id`、一意 `outer_unit_id`、`unit_type: outer_trial`、`scale`、`method: B/C/D`、`status` を持つ。任意の行の並べ替えでprefixの安定性を改善しない。
- `status` はSUCCESS/INFEASIBLE/FAILED/MISSING/INCOMPLETE/NOT_STARTED。内部枝 `branch_id`、`retry_of` のある行は外側単位から除外。retryを新規の独立Jとして数えない。各statusは登録された外側試行分母で記録し、除外数・理由を別記。予定試行の欠落をこの入力だけで検知できるわけではないため、事前台帳との一致を入力責任者が確認する。
- SUCCESSには `plan: {path, sha256}` と `outer_evidence: {path, sha256}` が必要。証跡にはtrial_id/outer_unit_id/scale/method、unit_type、problem_hash/od_hash、plan_sha256、comparison_profileを持たせる。保存計画と入力・運行版を一致させ、共通物理/FCFSまたは勤務版検証器でD/Wを再計算する。Wは総積込待機分。計画中の外部D/W列を信用して集計しない。問題・OD・計画・証跡・登録のSHAを出力し、処理中の変更を拒否する。
- `comparison_profile` は全方式の共通条件を事前に識別する版名／登録ID。最適化設定・p/shots・n/K/R・期限等の適格性を検証した実行台帳を根拠とする。外側証跡ファイルを新しく作るだけで履歴データが適格になるわけではない。この統計入口自身が過去ログの全量子呼出し・収束を再監査するわけではなく、証跡の科学的内容は別途確認する。
- `seed_identity` を記録する場合は全RNG状態・生成規則を識別できるcanonicalな文字列にする。同じseed整数だけで独立・対応を認定しない。完全RNG識別の重複が判明しているセル／対には独立MCSEを付けない。資源記録は `planning_wall_s`、`CPU_s`、`max_RSS_MiB`。欠測を0にしない。

## 独立性・対応・C参照

`independence["S1/D"]` 等にconfirmed=true、reasonとSHA固定evidenceを登録する。証跡のkindは `outer_independence_design`、cellとindependent=trueが必要。記述SDは独立性未確定でも計算するが、MCSEはHOLD。実際の独立性を宣言文字列だけで証明したと主張しない。

`comparison_designs` はB-D/C-Dのscale/baseline/comparison/kind/evidenceを指定する。対応ありのkindは `paired_common_random_factors`、対応表 `pairs: [[baseline_trial_id, comparison_trial_id], ...]` を事前登録証跡にも同一で保存する。証跡にはregistered_before_results=true、具体的な共有確率要因stochastic_shared_factors、independent_pairsの根拠が必要。same_seed/same_index/same_trial_id/fixed_demandだけの対応宣言を拒否する。確率的基準試行の再使用も拒否する。

独立2群は `independent_groups`、証跡に同kindとbetween_groups_independent=trueが必要。両群個別の独立性確認と合わせ、平均差のMCSE=sqrt(sX²/JX+sY²/JY)を記録する。対応差SDは作らない。設計が未登録なら平均差の点だけを出し、改善SD/MCSE/試行別両立割合は作らない。

C参照が真に固定・決定論的である別の証明を持つ場合だけ `certified_fixed_reference` を使用できる。証跡にdeterministic_certified=true、certificate、pairs、registered_before_results=trueを含める。このとき推定対象はその固定参照条件付き。観測SD0をcertificateにしてはならない。

C-Dの正当な対応からD|Cを算出する。B|Cも必要なら `dual_designs` にC-Bの同形式の設計を登録する。AはCへ代入不可。平均値同士から計算したI_dualは `aggregate_mean_indices` に別名で保存し、試行別I_dualの平均・SDや厳密両立割合へ代用しない。

## Aの整合性監査

`A_references[scale][DまたはW]` にvalueとcomparability_auditを登録する。unit/measurement_scope/time_context/spatial_context/aggregation_targetの5項目が各status=PASSかつ根拠付きの場合だけ参照線と差を出す。根拠は実際の参照資料・換算式・集計対応を示す必要がある。自動でP=配送先数、U=研究便数とはしない。AにJやSDを付けない。Aとの差のSDはB〜D各試行と固定参照との差から計算する。

## 成果物

`SUMMARY.csv`、`COMPARISONS.csv`、`FAILURES.csv`、`TRIAL_AUDIT.csv`、`ANALYSIS.json`、`SOURCE_HASHES.json`。主要図8種類はfigures/にPNG/PDF保存、実際に指定したyerrはFIGURE_SPEC.jsonへ保存。主要バーのquantityはsample_SDのみ。

`internal/J_PREFIXES.csv` は登録順の平均・SD・MCSE等。`CONTRAST_PREFIXES.csv` と `I_DUAL_PREFIXES.csv` は正当な派生系列の推移、`RESOURCES.csv` は補助資源。prefix箱・MCSE図もinternal/へ分離する。MCSEを主要結果図の誤差バーにしない。J_DECISION.jsonはHOLDを保持し、旧30を採用せず、精度・資源・SESOIに数値を補完しない。

保全監査を新しく保存する場合は `python scripts/statistical_scope_20261121_v1/finalize_audit.py --output /absolute/new/audit`。開始時スナップショットを参照して確認し、保存済み証跡に上書きしない。
