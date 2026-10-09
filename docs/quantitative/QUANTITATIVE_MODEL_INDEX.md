# Quantitative Model Index

2026-10-09。正式な定量モデルの参照入口。表のVerificationは保存検証の所在/方法で、今回の全科学テストPASSではない。

| Component | Canonical Source | Input | Output | Verification | Freeze Reference |
|---|---|---|---|---|---|
|Demand | demand.py（Hayate保存参照: `05_src/research_cli/demand.py`、公開ツリー非同梱） | baseline_demand.yml（Hayate保存参照: `reproducibility/config/traffic_simulation/baseline_demand.yml`、公開ツリー非同梱） | daily_requests.csv（Hayate保存参照: `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv`、公開ツリー非同梱） | 保存入力のみ;生成build未提供 | INPUT_AUTHORITY_MANIFEST.csv（Hayate保存参照: `01_research_design/scenario_evaluation/classical_vrptw_baseline_20261005/INPUT_AUTHORITY_MANIFEST.csv`、公開ツリー非同梱）|
|Assignment | baseline_capacity_fleet_assignment_20260930（Hayate保存参照: `01_research_design/scenario_evaluation/baseline_capacity_fleet_assignment_20260930`、公開ツリー非同梱） | CUSTOMER_DEMAND_39956.csv（Hayate保存参照: `01_research_design/scenario_evaluation/vehicle_capacity_assignment_20260930/CUSTOMER_DEMAND_39956.csv`、公開ツリー非同梱） | CUSTOMER_VEHICLE_ASSIGNMENT_39956.csv（Hayate保存参照: `01_research_design/scenario_evaluation/baseline_capacity_fleet_assignment_20260930/CUSTOMER_VEHICLE_ASSIGNMENT_39956.csv`、公開ツリー非同梱） | prepare.pyの需要・容量照合 | CAPACITY_FREEZE_MANIFEST.json（Hayate保存参照: `01_research_design/scenario_evaluation/baseline_capacity_fleet_assignment_20260930/CAPACITY_FREEZE_MANIFEST.json`、公開ツリー非同梱）|
|OD | sumo_od_selective_routing_resume_v4_20261004（Hayate保存参照: `01_research_design/scenario_evaluation/sumo_od_selective_routing_resume_v4_20261004`、公開ツリー非同梱） | FROZEN_ENDPOINTS.parquet（Hayate保存参照: `01_research_design/scenario_evaluation/sumo_od_baseline_20260930/FROZEN_ENDPOINTS.parquet`、公開ツリー非同梱） | PARTITION_MANIFEST.csv（Hayate保存参照: `01_research_design/scenario_evaluation/sumo_od_final_validation_20261005/PARTITION_MANIFEST.csv`、公開ツリー非同梱） | partition provenance/hash | SUMO_OD_BASELINE_FREEZE.json（Hayate保存参照: `01_research_design/scenario_evaluation/sumo_od_final_validation_20261005/SUMO_OD_BASELINE_FREEZE.json`、公開ツリー非同梱）|
|Classical Routing | [solver.py](../../src/kmd_quantitative/routing/solver.py) | instances（Hayate保存参照: `01_research_design/scenario_evaluation/classical_vrptw_baseline_20261005/instances`、公開ツリー非同梱） | RESULTS_MANIFEST.csv（Hayate保存参照: `01_research_design/scenario_evaluation/classical_vrptw_baseline_20261005/RESULTS_MANIFEST.csv`、公開ツリー非同梱） | [independent.py](../../src/kmd_quantitative/routing/independent.py);可行性/厳密探索/dual | CLASSICAL_VRPTW_BASELINE_FREEZE.json（Hayate保存参照: `01_research_design/scenario_evaluation/classical_vrptw_baseline_20261005/CLASSICAL_VRPTW_BASELINE_FREEZE.json`、公開ツリー非同梱）|
|PUBO / QAOA | [builder.py: PUBO API](../../src/kmd_quantitative/quantum/builder.py) | R0_COMMON_PROTOCOL_FULL_RUN_PLAN.json（Hayate保存参照: `01_research_design/scenario_evaluation/matched_quantum_r0_common_protocol_full_v2_20261007/R0_COMMON_PROTOCOL_FULL_RUN_PLAN.json`、公開ツリー非同梱） | R1_FULL_RUN_FINAL_STATUS.json（Hayate保存参照: `01_research_design/scenario_evaluation/matched_quantum_r1_full_v2_20261007/R1_FULL_RUN_FINAL_STATUS.json`、公開ツリー非同梱） | qualification/full worker/独立可行性 | [FINAL_FREEZE_AUTHORITY_CHAIN.csv](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_FREEZE_AUTHORITY_CHAIN.csv)|
|SUMO | generate_canonical_delivery_trajectories.py（Hayate保存参照: `05_src/literature_analysis/generate_canonical_delivery_trajectories.py`、公開ツリー非同梱） | GENERATION_PLAN.json（Hayate保存参照: `01_research_design/scenario_evaluation/canonical_delivery_trajectories_20261006/GENERATION_PLAN.json`、公開ツリー非同梱） | MATCHED_CLASSICAL_TRAJECTORY_MANIFEST.csv（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_MANIFEST.csv`、公開ツリー非同梱） | 保存native/trajectory hash;matchedはfork使用 | [MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json](../../01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json)|
|Battery | [CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json) | [CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json) | MATCHED_CLASSICAL_BATTERY_EFFECTS.csv（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_EFFECTS.csv`、公開ツリー非同梱） | 固定容量からパック・車両質量 | MATCHED_CLASSICAL_BATTERY_VALIDATION.json（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_VALIDATION.json`、公開ツリー非同梱）|
|Controlled-DC | [run_full_controlled_dc.py](../../05_src/literature_analysis/run_full_controlled_dc.py) | MATCHED_CLASSICAL_TRAJECTORY_MANIFEST.csv（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_MANIFEST.csv`、公開ツリー非同梱） | MATCHED_CLASSICAL_BATTERY_LOGICAL_RESULTS.csv（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_LOGICAL_RESULTS.csv`、公開ツリー非同梱） | scalar_check/会計;評価は保存区間Wh | [CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)|
|Method × Battery | apply_r0_common_protocol_method_battery.py（Hayate保存参照: `05_src/literature_analysis/apply_r0_common_protocol_method_battery.py`、公開ツリー非同梱） | R0_COMMON_PROTOCOL_METHOD_TRAJECTORY_MANIFEST.csv（Hayate保存参照: `01_research_design/scenario_evaluation/matched_quantum_r0_common_protocol_trajectories_20261008/R0_COMMON_PROTOCOL_METHOD_TRAJECTORY_MANIFEST.csv`、公開ツリー非同梱） | [FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv) | R1→旧R0 AST依存;parent+replicate対応 | [FINAL_QUANTITATIVE_RESULT_FREEZE.json](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)|
|Scale Analysis | analyze_classical_scale_battery.py（Hayate保存参照: `05_src/literature_analysis/analyze_classical_scale_battery.py`、公開ツリー非同梱） | LOGICAL_BINDINGS.json（Hayate保存参照: `01_research_design/scenario_evaluation/matched_classical_route_scale_20261007/MANIFESTS/LOGICAL_BINDINGS.json`、公開ツリー非同梱） | classical_scale_battery_interaction_20261007（Hayate保存参照: `01_research_design/scenario_evaluation/classical_scale_battery_interaction_20261007`、公開ツリー非同梱） | 6規模logical/physical/親重みを区別 | MATCHED_CLASSICAL_BATTERY_VALIDATION.json（Hayate保存参照: `01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_VALIDATION.json`、公開ツリー非同梱）|

## 接続とauthority

需要/地点→固定割当・時間窓・OD→古典baseline→nested 6規模→R0/R1共通Protocol V2→経路取得/同一性→SUMO→固定Battery質量条件とControlled-DC→Method×Battery→最終freeze。古典6規模分析は別の集計枝。

- 古典6規模runner（Hayate保存参照: `01_research_design/scenario_evaluation/matched_classical_route_scale_20261007/runner.py`、公開ツリー非同梱）：凍結solverコピーを利用。
- R0 common worker（Hayate保存参照: `05_src/traffic_simulation/matched_quantum_r0_common_protocol_full_v2/worker.py`、公開ツリー非同梱） / R1 worker（Hayate保存参照: `05_src/traffic_simulation/matched_quantum_r1_full_v2/worker.py`、公開ツリー非同梱）：単体science.pyではなくqualificationと監督処理を含む入口。
- R1 plan（Hayate保存参照: `01_research_design/scenario_evaluation/matched_quantum_r1_full_v2_20261007/R1_FULL_RUN_PLAN.json`、公開ツリー非同梱）：R0 planとは次元・PID/seedを区別。
- R1 Battery adapter（Hayate保存参照: `05_src/literature_analysis/apply_r1_method_battery.py`、公開ツリー非同梱）は[旧R0計算ソース](../../05_src/literature_analysis/apply_r0_method_battery.py)のASTを利用。旧結果を除外しても旧ソースを削除しない。
- 統合解析（Hayate保存参照: `01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/analyze_frozen_results.py`、公開ツリー非同梱）：保存結果を読むが出力書込みあり。検証専用CLIではない。
- 道路network・端点等の詳細（Hayate保存参照: `reproducibility/release/RELEASE_ARTIFACT_REGISTER.csv`、公開ツリー非同梱）と全module契約（Hayate保存参照: `reproducibility/release/RELEASE_MANIFEST.json`、公開ツリー非同梱）を参照。

## 結果と復元

[最終結果報告](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)を数値の参照先とする。historical R0、最終R0common、最終R1、古典6規模、全域465担当集合を混同しない。

Release authority（Hayate保存参照: `reproducibility/release/RELEASE_AUTHORITY.md`、公開ツリー非同梱） / 復元手順（Hayate保存参照: `reproducibility/release/RESTORE_PROCEDURE.md`、公開ツリー非同梱） / 保存上の不足（Hayate保存参照: `reproducibility/release/RELEASE_TRACKING_GAPS.md`、公開ツリー非同梱） / 現行実行ガイド（Hayate保存参照: `00_project_management/CURRENT_EXECUTION.md`、公開ツリー非同梱）。保存先未確定につきP0-A PARTIAL。

## GitHubで取得できる範囲とHayate保持データ

[管理方針](GITHUB_AND_HAYATE.md)と追跡候補一覧（Hayate保存参照: `docs/audits/hayate_github_repository_cleanup_20261009/02_GITHUB_KEEP_FILELIST.csv`、公開ツリー非同梱）を参照。上表のsource/input/outputリンクはHayate上の所在を示し、すべてがGitHub収録済みという意味ではない。大容量入力・軌跡・結果へのリンクはGitHubでは未収録になり得る。

Hayate保持一覧（Hayate保存参照: `docs/audits/hayate_github_repository_cleanup_20261009/03_HAYATE_ONLY_FILELIST.csv`、公開ツリー非同梱）でサイズ・hash・再実行への影響を区別する。現役の旧R0 Battery source、凍結INPUTSのsource、正式freezeは維持する。第1段階では古典solver/独立検証だけを `src/kmd_quantitative/routing/` へ移行し、旧パスの相対互換リンクで内容hashと既存参照を保持する。他の正本・凍結スナップショットは原位置を維持する。

[静的Quick Start](CURRENT_EXECUTION_GUIDE.md#github向け静的quick-start)は最終モデルの全再実行ではない。文書Index（Hayate保存参照: `docs/README.md`、公開ツリー非同梱）から研究文書・修論・監査を区別する。

## 段階的な構造移行

移行対応表（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/02_FILE_MIGRATION_MAP.csv`、公開ツリー非同梱）は344件の旧位置と第1段階後の位置を記録する。release manifestは凍結時点の来歴として変更しない。新しい正式sourceと旧パスの内容hashは同一。Gitで互換リンクを扱う際はsymlinkを保持できる環境が必要で、Windows等の非対応checkoutは未検証。

## 第2段階の量子入口

[decoder](../../src/kmd_quantitative/quantum/decoder.py) と [qualification_builder](../../src/kmd_quantitative/quantum/qualification_builder.py) は旧qualification実装から内容不変で移行した。後者のbuildはQUBOであり、Candidate C PUBOではない。新 [builder](../../src/kmd_quantitative/quantum/builder.py) は共有science.pyの4関数をhash検証付きで読むAPI。R0はshared science、R1は資格済みworker内の同一ASTを利用し、最終標本は可行経路表と独立validatorで判定する。単独decoderが最終workerから直接呼ばれるとは扱わない。

第2段階対応表（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/10_PHASE2_FILE_MIGRATION_MAP.csv`、公開ツリー非同梱）と移植性報告（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/13_SYMLINK_PORTABILITY_REPORT.md`、公開ツリー非同梱）を参照。科学freeze/実験workerの位置とbytesは維持した。

## Phase 3：正式最終標本の再利用入口

[formal.py](../../src/kmd_quantitative/quantum/formal.py) → 凍結science内の可行表・count変換・独立再検査・最終min。入力は正式model/instanceと最終標本、出力は取得経路またはNone。[契約と凍結実装との関係](QUANTUM_API_AND_FROZEN_PROTOCOL.md)。qualification用decoderは別用途として維持します。

## Phase 4：保存軌跡とControlled-DCの接続

[Simulation / Trajectory API](SIMULATION_AND_TRAJECTORY_API.md)に、正式CSV読込み、単位、時刻境界、SUMO外部依存を記載しました。`src/kmd_quantitative/simulation/trajectory_io.py` は保存軌跡の時刻・速度をそのまま返します。Notebook03の入力を接続し、`python -B tests/test_simulation_api.py` で小規模検証できます。SUMO全量再実行は行わず、生成worker・凍結sourceは原位置で保持しています。

## Phase 5：Battery / Energy API

[質量・Controlled-DCの正式入口](BATTERY_AND_ENERGY_API.md)を追加しました。`battery.mass` は元計算文、`battery.scenarios` は既存freeze、`energy.controlled_dc` は元DC関数へ接続します。Notebook03はSimulation→Battery/Energyを利用します。`python -B tests/test_battery_energy_api.py` で数値回帰を確認できます。18 kWhは残量会計に使いますが、SOC・充電モデルではありません。科学sourceとfreezeは維持し、全量SUMO移植・公開許諾は未完了です。

## Phase 6：Analysis API

[method_battery.py](../../src/kmd_quantitative/analysis/method_battery.py) と [scale_analysis.py](../../src/kmd_quantitative/analysis/scale_analysis.py) が保存済み結果の正式な再利用入口です。上表の生成・分析ソースは原位置で保全し、APIからimportしません。[比較条件・指標・母数・入出力契約](ANALYSIS_API_AND_FROZEN_RESULTS.md)を参照してください。Notebook04・05は読込み専用APIに接続しました。

## Phase 7：設定・入力・結果の参照

[Configs](../../configs/README.md)・[Data](../../data/README.md)・[Results](../../results/README.md)を整備しました。正式設定・freezeは原位置で保持し、小規模合成fixtureだけをバイト一致コピーで配置しています。Notebook01/02/03は設定例から入力を取得し、04/05は既存Analysis APIを継続利用します。`python -B tests/test_distribution_layout.py` と `python -B notebooks/test_notebooks.py` をrootで実行できます。配布技術候補と公開許諾は別で、権利確認・独立永続保存・全量SUMO再現は未完了です。

## 小規模再利用の環境とCI

[新規Python環境](../../reproducibility/environment/QUICKSTART_ENVIRONMENT.md) / [依存範囲](../../reproducibility/environment/DEPENDENCY_SCOPE.md)。環境構築後、`python -B scripts/verify_quickstart.py`。科学source・freezeを変更せず、全量実験と独立したAPI/Notebook検証です。CIの実行と公開権利は別途確認が必要です。
