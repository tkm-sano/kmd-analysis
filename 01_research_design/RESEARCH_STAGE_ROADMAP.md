# Minimal EVRP以降の研究段階ロードマップ

研究タイトルの正本：[正式タイトル（固定）](../RESEARCH_TITLE_AUTHORITY.md)。

更新：2026-09-27（exact encoding同値性監査完了）。CURRENT_MASTER_ROADMAP。規模の正本は[評価規模authority](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)。計画freezeは実行許可ではない。

## 現在地と三つの研究質問

| Scale | 問い | 状態 |
|---|---|---|
| MODEL_VALIDATION_SCALE | モデルは正しく実装されているか | 既存N002/N003/N004の限定scopeをFROZENで保持 |
| METHOD_COMPARISON_SCALE | 同一EV/配送条件でClassicalとQuantumの出力はどう異なるか | 最終nなし、BLOCKED。Direct/dense-state制限により全main候補不適合、代替encoding比較済み。Branch B：多項式容量QUBOはFROZEN。method scaleはBLOCKED_BY_BACKEND。最新節参照 |
| SCENARIO_EVALUATION_SCALE | Battery条件差が経路・EV運用・energy・経済にどう影響するか | 最終n未確定、PARTIALLY_FROZEN。古典scaling/Battery relevanceが必要、Quantum実行可能性は必須でない |

既存N004 authorityはS0_PILOT、N003 authorityはS0_METHOD_IMPLEMENTATION_REFERENCEである。[pilot S0正本](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)は変更していない。[scope改訂](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/S0_SCALE_REVISION.md)により、そのS0_SCALE_AUTHORITY=FROZENをmain規模へ転用しない。mainのS0_SCALE_AUTHORITY=PARTIALLY_FROZEN、S0_MAIN_AUTHORITY=NOT_FROZEN、main実行NOT_AUTHORIZED。

検証規模・手法比較規模・scenario/経済規模は同じである必要がない。scenario > method > validationは許容するが、実際の大小・一致は証拠で決める。39,930 eligible顧客を一度に最適化する計画ではない。

## 保持する上流authority

- [VRPTW統合freeze](../reproducibility/outputs/traffic_simulation/r24_vrptw_structured_integrated_analysis/20260926_v1/VRPTW_CONCLUSION_FREEZE.json)：既存結果FROZEN。
- [Minimal EVRP設計](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_design_authority/20260926_v1/MINIMAL_EVRP_AUTHORITY.json)と[classical model freeze](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/MINIMAL_EVRP_CLASSICAL_FREEZE.json)：N002 WIDEの回帰・制御充電検証scopeでFROZEN。一般規模EVRPの受入を意味しない。
- [Battery authority](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIO_AUTHORITY.md)：CURRENT・劣化・技術容量・感度設計FROZEN。
- 実車充電性能は未解決。10kW・低初期SOCは制御検証専用。旧pilotの充電INACTIVEは新nested規模へ自動適用しない。

## 正式な段階順序

| 順序 | 段階 | 状態・出口条件 |
|---:|---|---|
| 1 | Minimal EVRP model freeze | FROZEN（既存small-N scope） |
| 2 | Battery scenario authority freeze | FROZEN（実車実効Pは未解決のまま分離） |
| 3 | Pilot S0 physical/common contract | FROZEN（pilot/referenceのみ）。実行結果はNOT_STARTED |
| 4 | Evaluation-scale / scaling study | 設計FROZEN、Study B・exact encoding同値性監査完了。Study A・正式instance受入は未開始 |
| 5 | Method-comparison scale freeze | BLOCKED。現行表現では候補なし。可行集合bit下限も24bit超。backend受入後、QUBO同値性/資源/実行時間/反復/独立検証/古典参照を満たす最大main候補 |
| 6 | Scenario-evaluation scale freeze | PARTIALLY_FROZEN。古典可解性/Battery relevance/次rung確認。Quantum可否は必須でない |
| 7 | Main S0 physical/common/execution authority更新 | BLOCKED。二規模選定後に入力・charging・実装・protocolを固定。経済extensionは分離 |
| 8 | Classical reference実行・監査・freeze | NOT_STARTED。main実行の別taskで実施 |
| 9 | Matched method scaleでQuantum実行 | NOT_STARTED。同じ規模・同じ物理入力の古典参照と比較 |
| 10 | Scenario scaleでBattery条件比較 | NOT_STARTED。非Battery入力を固定。Quantumが走れない規模の結果はClassical scenario証拠として報告 |
| 11 | Energy / economic比較・効果分離 | NOT_STARTED。scenario-instance電力費、会計/価格を先に固定。異なる規模のC/Qを引き算しない |
| 12 | Battery sensitivity | NOT_STARTED。事前固定grid・同じ選定scope、null効果を保持 |
| 13 | Quantum chemistry track | NOT_STARTED。電子構造accuracy/規模/end-to-end時間の独立比較 |
| 14 | 材料R&D解釈・統合分析 | NOT_STARTED。量子化学能力からBattery kWhへ直接換算しない |

Minimal EVRP freeze → Battery authority freeze → pilot S0 authority → evaluation-scale/scaling study → method scale freeze → scenario scale freeze → main S0 authority → Classical reference → matched Quantum → scenario Battery → energy/economics → quantum chemistry → integrated analysis。

scale studyのClassical solvesは探索的な規模選定証拠であり、段階8のmain S0実行と混同しない。段階5/6のstudyは共通入力受入後に独立に進められ、main authorityで合流する。

## 次の限定task

[SCALING_STUDY_PLAN](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/SCALING_STUDY_PLAN.md)のPhase Aで、既存n20/R01 Random・Clusteredから作ったprefix n=3,4,5,8,10,15,20を受け入れる。3/4は診断、main候補は5以上。親由来TW/serviceを固定し、fleet上限のサイズ依存も明示する。

Study BのMinimal EVRP QUBO/resource静的監査は完了し、全main候補がmemory gateで停止した。代替encoding/decomposition静的比較も完了した。直近は同じ物理問題の非dense simulation backend実行可能性検証プロトコル設計で、backend変更やbenchmark実行は未許可。Study Aは入力受入後のcontrolled Classical EVRP scaling＋Battery relevanceとして独立に残す。Classical300秒/cell、memory4GiB、Quantum raw256MiB等の停止条件は[SCALING_LIMITS](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/SCALING_LIMITS.json)に事前固定した。Study BにQAOA/Aer実行は含めない。今回はStudy B後続の代替encoding静的比較まで完了し、Study A・科学実行は行っていない。

全main候補が不適合なら規模を恣意的に縮小/拡大せずNO_SUITABLE_SCALEを保存する。Battery差が出ないから容量・距離・初期SOC・sampleを変更しない。small-N量子結果の人口外挿、n4 energyの都市規模解釈、39,930/n倍の費用推計を禁止する。人口集計には別methodologyが必要である。

## 詳細正本と履歴

- [代替encoding比較・method再判定](../reproducibility/outputs/traffic_simulation/r24_alternative_encoding_decomposition_study/20260927_v1/ALTERNATIVE_ENCODING_DECOMPOSITION_STUDY.md)

- [Study B監査・BLOCKED判定](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)
- [Study B前roadmapの保存コピー](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/audit/before/01_research_design/RESEARCH_STAGE_ROADMAP.md)

- [評価規模authority・未決事項](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)
- [Battery性能根拠](BATTERY_PERFORMANCE_EVIDENCE_PLAN.md)、[Battery scenario比較](BATTERY_SCENARIO_COMPARISON_PLAN.md)
- [Classical/Quantum共通条件](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)
- [量子化学benchmark](QUANTUM_CHEMISTRY_BENCHMARK_PLAN.md)、[二系統の接続](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)
- [今回更新前のroadmap](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/audit/before/01_research_design/RESEARCH_STAGE_ROADMAP.md)、[今回manifest](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/ARTIFACT_MANIFEST.json)

旧科学成果物・pilot全directory・Battery authority・ledgerは不変。全最適化、MILP、Exact、QAOA、Aer、circuits、shotsの新規実行0。STOP。

## 最新gate：exact encoding検証

[監査結果](../reproducibility/outputs/traffic_simulation/r24_exact_encoding_backend_protocol/20260927_v1/EXACT_ENCODING_EQUIVALENCE_AUDIT.md)：384経路構造・48 B2 code words・113 temporal replayを決定論的検証。B2の同値性は元から1台の冗長制約domain限定。複数台main規模へ適用不可。B1は資源改善なし。formulation/scale/resource gate=BLOCKED。

次の順序：exact compact複数台encoding検証 → backend protocol freeze → 別途承認されたcontrolled benchmark → method scale freeze。現時点でbenchmark実行ケースは0。Study Aは別系統でscenario scaleを決定。main S0はNOT_AUTHORIZED。旧段階表のbackend受入は、このencoding前提通過後に限る。

## 最新fleet policy / multi-vehicle gate

[車両台数authority](../reproducibility/outputs/traffic_simulation/r24_fleet_size_multi_vehicle_authority/20260927_v1/FLEET_SIZE_AUTHORITY.md)：M=利用可能上限、m_used=使用台数。AT_MOST_M保持。単一車両はroute-order subproblemのみ。複数台写像の同値性はsmall-Nで確認、主要規模の資源gateはBLOCKED。

Minimal EVRP freeze → Battery authority → evaluation-scale studies → multi-vehicle formulation/resource authority → method scale freeze → Study A scenario scale/M確定 → Main S0・m0確定 → Battery固定使用台数比較(Stage A) → 同じM内の適応比較(Stage B) → energy/economic分析 → quantum chemistry track。Study Aは独立に準備可能だが本taskでは未実行。

Battery両protocolの方針はFROZEN、M_scenario/m0は未定。Stage Aのinfeasibleを増車で救済しない。Stage Bのm_used変化と電力費を全fleet costと混同しない。次はseparator表現のexact容量制約を多項式規模で表す静的設計。backend/main S0はNOT_AUTHORIZED。前節の「複数台写像未検証」という旧gateはこの最新節で更新する。

## 最新Branch Bとcompute-energy段階

[多項式容量formulation決定](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/MULTI_VEHICLE_FORMULATION_DECISION.md)：312変数のexact multi-vehicle CURRENT formulationをFROZEN。容量の全経路no-goodは不要になった。主blockerはbackend/resource。以前の「容量encoding未解決」という次taskは更新される。

Quantum track: formulation freeze → controlled alternative-backend protocol freeze → 別taskの許可済みbenchmark → method scale freeze → **COMPUTE_ENERGY_ACCOUNTING_PROTOCOL** → Main S0 Classical/Quantum科学実行。compute-energy protocolはmethod scaleが利用可能になった後、S0実行より前に必須。[会計境界](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/COMPUTE_ENERGY_ROADMAP_EXTENSION.md)を参照。E_system,m=E_EV,m+E_compute,m。Aer電力はclassical simulator電力であり実QPU電力ではない。

Battery track: [Study A readiness](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/STUDY_A_READINESS.md)のPhase A/validator/protocol不足を解決 → full Classical EVRP scaling/Battery relevance → scenario scale/M → Main S0/m0 → fixed-fleet Stage A → adaptive-fleet Stage B → energy/economic分析 → quantum chemistry/integrated analysis。Quantum可否によってscenario規模を縮小しない。今回Study Aは未実行。

将来問うこと：最適化手法による配送電力の変化は、計算の運用電力を相殺するか。今回は測定・計算・回答しない。全科学実行delta0、Main S0はNOT_AUTHORIZED。

## 最新backend protocol freeze / Phase1限定

[Backend protocol](../reproducibility/outputs/traffic_simulation/r24_backend_feasibility_benchmark_protocol/20260927_v1/BACKEND_FEASIBILITY_BENCHMARK_AUTHORITY.md)=FROZEN。Branch B formulationは変更なし。次taskは最小nested n3/M1のdense/MPS・固定parameter・optimizerなし、最大4 circuits/128 shots → integrity audit → STOP。Phase2以降は別許可、n8/n10は既存CX上限で事前STOP。今回simulation/transpilation実行0。

usable method scale/backend → scientific Quantum protocol → COMPUTE_ENERGY_ACCOUNTING_PROTOCOL → Main S0 Classical/Quantum実行という境界を保持。Aer/MPS電力はclassical simulator電力。将来のE_QPU_break_even=E_EV,C+E_compute,C−E_EV,Qはreal-QPU energy-to-solutionの許容上限を定義し、今は計算しない。[metadata/boundary hook](../reproducibility/outputs/traffic_simulation/r24_backend_feasibility_benchmark_protocol/20260927_v1/COMPUTE_ENERGY_METADATA_HOOK.md)。Study A readinessはBLOCKEDのまま独立、Main S0はNOT_AUTHORIZED。
