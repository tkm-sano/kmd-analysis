# 道路・経路・計測契約の独立レビュー — 2026-11-02

判定：A・Bの地域代表試行はともに **NO-GO**。今回の成果は静的診断、保存元経路の回収、モデル計測契約、算術単体検証である。新規SUMO/native実行0、経路探索0、地域代表試行0、全件実行0、QAOA再学習0。N2道路網は作成していない。

## 版と保全

HEAD `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。開始時と終了時のtracked差分は空。前2レビューの成果物875件を開始時に照合し、不一致0。終了時は `FINAL_SOURCE_HASH_CHECK.csv` の4,728ファイルを再ハッシュし、不一致0。`GIT_DIFF_FINAL.patch`、`GIT_STATUS_FINAL.txt` に最終状態を保存した。検査対象外の全バックアップについて変更なしを証明したとの主張ではない。

実体の所在を区別する。

|略号|所在|取扱い|
|---|---|---|
|R|`/home/takuma/kmd-analysis`|現在の作業木。Git追跡状態はgit statusと照合|
|U|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked`|外部の未追跡保全コピー。公開Gitに含まれると扱わない|
|B|`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup`|外部保存用バックアップ|
|L|`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated`|移設保全領域|

全参照元・実装・入力のSHA256、所在区分、旧期待ハッシュは `COMBINED_SOURCE_FILES.csv`。新規生成物は `ARTIFACT_MANIFEST.json`。行証拠にsource_path/SHAまたはpartition/rowがある場合、この台帳と結合する。

## 旧状態の再確認

|項目|旧報告|今回のreadback|差異|
|---|---:|---:|---|
|A運用判断／政策候補|2,808／303|2,808／303|なし|
|A機構追加／union|15／318|15／318|なし|
|B参照／候補|36,800／4,987|36,800／4,987|なし|
|B既知完全／不足|37／4,950|37／4,950|なし|
|B位置付き区間要求|219,211|219,211|なし|
|前回単体／readback／合成native|26／6,605／7|26／6,605／7|なし・再実行せず|
|受入済み既存A/B走行|0／0|0／0|道路受入不成立を保持|

今回の2,323元OD回収候補は新発見の保存証拠であり、旧37という当時の台帳値を誤りとして置換しない。2つの旧既知入力について元OD同一性を保留したことも明示する。

## 主要生成経路

1. A：D10採用判断→D11 `operations_2808.csv`・`logical_candidates.csv`→前回 `A_OPERATION_RUN_LINKS.csv`、303政策＋15機構入力。政策・仮想利用可能時刻・出発を変更していない。
2. B：staged 3familyの `ALL_SEEDS.csv`＋460入力NPZ／MANIFEST→初回 `independent_audit.py` が8設定・OPTIMIZED・rep0…9を抽出→`B_PLAN_REFERENCES.csv`→前回 `build_run_ledger.py` が4,987候補、219,211不足区間、37既知入力を保存。
3. 今回：NPZのnodes/partition/travel/distance→`CHECKPOINT_ROWS.json`／`ROUTE_NUMERIC_PARTITIONS.json`→元parquet行→保存 `lane_feasible_routes.rou.xml`／補正・loop記録→ `RECOVERED_OD_LEGS.jsonl.gz`→新しい全B経路payload。既存の全B走行結果を発見したという意味ではない。
4. 道路：run2→外部lane端点・長さの変更→N0。N1はrun2への復帰、左側通行再構築、局所・信号補修を含むB6。差分と保存nativeイベントを独立readback。
5. 計測：凍結DC＋SUMO公式資料／1.24.0ソース→今回の `measurement_contract.py`＋別算術→35fixture。既存FREEZE変更なし。

主要起点：

- `/home/takuma/kmd-analysis/review_outputs/integrated_causal_audit_20261102/run01/B_PLAN_REFERENCES.csv` — SHA256 `556cf3187be2d9aba42bc2410bb74a79d3d830c901d45e7754ee09e712c89145`
- `/home/takuma/kmd-analysis/review_outputs/integrated_causal_audit_20261102/run01/independent_audit.py` — SHA256 `b4b04f5da368b1fca7187c5abc9a4d281905ab428b19a16a38602365336953c9`
- `/home/takuma/kmd-analysis/review_outputs/complete_run_validation_20261102/run01/build_run_ledger.py` — SHA256 `cb44e3f3536b74c47e5bb043159d0b0760e0715f758a5147b3c995d8fea0b418`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md` — SHA256 `87731d8c211fcc0968a58198cd28447f011be1376fec32d3edf79a6268769ea2`
- `/home/takuma/kmd-analysis/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json` — SHA256 `b37fd532a5a7daf84f07924d954d6f8e2584f51d218506eeb14e70c53538cf78`

## 再実行入口

すべて今回のレビュー領域のみへ出力する。Python/pyarrowは既存 `.conda/bin/python`、pyarrow19.0.1。依存関係追加なし。前2レビューが必要な外部保全データを含むため、公開Git単独で完全再現できるとは判定しない。

```bash
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/evidence.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/recover_routes.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/review_recovery.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/diagnose_network.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/network_supplement.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/missing_feasibility.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/validate_measurements.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/final_review.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/write_reports.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/seal_artifacts.py
```

出力先が既にある再実行では今回の診断出力を更新するため、第三者はレビュー一式を別ディレクトリへ複製し、保全先をread-onlyにして実行する。元の科学runnerは実行しない。`final_review.py` は集計コードの数値転記でなく、参照結合・payloadハッシュ・道路接続・stop順・保全を別手順で検査する。

## 修正と残存状態

独立レビューで134制御区間のうち欠落1行が中間台帳から落ちていたため、HOLD行を復帰。133PASS＋1HOLDを正式分母とした。修正前コード・CSV、差分、再検証は `revisions/`。経路回収の初回は同一大ファイルの反復ハッシュで遅くなり中断し、キャッシュ化後に実行完了した。初回ログを保持。計算式・元データの改変なし。

Cは前回の条件付き成果を継承：T08差5.448297415kg、下側Crrの総量加重削減0.412579010%、T09完成パック183行HOLD、全面対向1行FAIL、未知部材相殺境界、量子材料改善未実証。新しい材料値・完成質量を設定せず、旧B0/B1/B2を材料主入力へ復活させていない。
