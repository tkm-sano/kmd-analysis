<a id="minimal-evrp以降の研究段階ロードマップ"></a>

# 最小構成の電気自動車配送経路問題以降の研究段階ロードマップ

研究タイトルの正本：[正式タイトル（固定）](RESEARCH_TITLE_AUTHORITY.md)。

更新：2026-09-27（厳密 符号化同値性監査完了）。CURRENT_MASTER_ROADMAP。規模の正本は[評価規模正本](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)。計画固定は実行許可ではない。

## 現在地と三つの研究質問

| Scale | 問い | 状態 |
|---|---|---|
| MODEL_VALIDATION_SCALE | モデルは正しく実装されているか | 既存N002/N003/N004の限定範囲を固定済みで保持 |
| METHOD_COMPARISON_SCALE | 同一電気自動車/配送条件で古典計算と量子計算の出力はどう異なるか | 最終nなし、実行不可。Direct/dense-state制限により全本番候補不適合、代替符号化比較済み。分岐 B：多項式容量制約なし二値二次最適化は固定済み。手法比較の規模はBLOCKED_BY_BACKEND。最新節参照 |
| SCENARIO_EVALUATION_SCALE | 電池条件差が経路・電気自動車の運用・電力量・経済にどう影響するか | 最終n未確定、PARTIALLY_FROZEN。古典scaling/Battery 関連性が必要、量子計算実行可能性は必須でない |

既存N004 正本はS0_PILOT、N003 正本はS0_METHOD_IMPLEMENTATION_REFERENCEである。[予備試験 第0段階正本](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)は変更していない。[範囲改訂](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/S0_SCALE_REVISION.md)により、そのS0_SCALE_AUTHORITY=固定済みを本番規模へ転用しない。本番のS0_SCALE_AUTHORITY=PARTIALLY_FROZEN、S0_MAIN_AUTHORITY=NOT_FROZEN、本番実行未許可。

検証規模・手法比較規模・想定条件/経済規模は同じである必要がない。想定条件 > 手法 > 検証は許容するが、実際の大小・一致は証拠で決める。39,930 対象条件を満たす顧客を一度に最適化する計画ではない。

<a id="保持する上流authority"></a>

## 保持する上流正本

- [時間窓付き配送経路問題統合固定](../reproducibility/outputs/traffic_simulation/r24_vrptw_structured_integrated_analysis/20260926_v1/VRPTW_CONCLUSION_FREEZE.json)：既存結果固定済み。
- [最小構成の電気自動車配送経路問題設計](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_design_authority/20260926_v1/MINIMAL_EVRP_AUTHORITY.json)と[古典計算 モデル 固定](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/MINIMAL_EVRP_CLASSICAL_FREEZE.json)：N002 WIDEの回帰・制御充電検証範囲で固定済み。一般規模電気自動車配送経路問題の受入を意味しない。
- [電池 正本](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIO_AUTHORITY.md)：現行・劣化・技術容量・感度設計固定済み。
- 実車充電性能は未解決。10kW・低初期充電率は制御検証専用。旧予備試験の充電無効は新入れ子構成規模へ自動適用しない。

## 正式な段階順序

| 順序 | 段階 | 状態・出口条件 |
|---:|---|---|
| 1 | Minimal EVRP model freeze | 固定済み（既存小規模 範囲） |
| 2 | Battery scenario authority freeze | 固定済み（実車実効Pは未解決のまま分離） |
| 3 | Pilot S0 physical/common contract | 固定済み（pilot/referenceのみ）。実行結果は未着手 |
| 4 | Evaluation-scale / scaling study | 設計固定済み、調査B・厳密 符号化同値性監査完了。調査A・正式問題例受入は未開始 |
| 5 | Method-comparison scale freeze | 実行不可。現行表現では候補なし。可行集合ビット下限も24bit超。計算方式受入後、制約なし二値二次最適化同値性/資源/実行時間/反復/独立検証/古典参照を満たす最大本番候補 |
| 6 | Scenario-evaluation scale freeze | PARTIALLY_FROZEN。古典可解性/電池 関連性/次rung確認。量子計算可否は必須でない |
| 7 | 本実験の第0段階 physical/common/execution 正本更新 | 実行不可。二規模選定後に入力・充電・実装・手順を固定。経済拡張は分離 |
| 8 | 古典参照解実行・監査・固定 | NOT_STARTED。本番実行の別作業で実施 |
| 9 | Matched 手法比較の規模で量子計算実行 | NOT_STARTED。同じ規模・同じ物理入力の古典参照と比較 |
| 10 | 想定条件 規模で電池条件比較 | NOT_STARTED。非電池入力を固定。量子計算が走れない規模の結果は古典計算 想定条件証拠として報告 |
| 11 | 電力量 / economic比較・効果分離 | NOT_STARTED。想定条件-問題例電力費、会計/価格を先に固定。異なる規模のC/Qを引き算しない |
| 12 | Battery sensitivity | NOT_STARTED。事前固定grid・同じ選定範囲、null効果を保持 |
| 13 | Quantum chemistry track | NOT_STARTED。電子構造精度/規模/終了-to-終了時間の独立比較 |
| 14 | 材料研究開発解釈・統合分析 | NOT_STARTED。量子化学能力から電池 kWhへ直接換算しない |

Minimal EVRP freeze → Battery authority freeze → pilot S0 authority → evaluation-scale/scaling study → method scale freeze → scenario scale freeze → main S0 authority → Classical reference → matched Quantum → scenario Battery → energy/economics → quantum chemistry → integrated analysis。

規模 調査の古典計算 solvesは探索的な規模選定証拠であり、段階8の本実験の第0段階実行と混同しない。段階5/6の調査は共通入力受入後に独立に進められ、本番 正本で合流する。

<a id="次の限定task"></a>

## 次の限定作業

[SCALING_STUDY_PLAN](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/SCALING_STUDY_PLAN.md)のPhase Aで、既存n20/R01 無作為・集積型から作ったprefix n=3,4,5,8,10,15,20を受け入れる。3/4は診断、本番候補は5以上。親由来TW/serviceを固定し、車両群上限のサイズ依存も明示する。

調査Bの最小構成の電気自動車配送経路問題 QUBO/resource静的監査は完了し、全本番候補がメモリー 判定基準で停止した。代替encoding/decomposition静的比較も完了した。直近は同じ物理問題の非dense simulation 計算方式実行可能性検証プロトコル設計で、計算方式変更やベンチマーク実行は未許可。調査Aは入力受入後の条件を統制した 古典計算 電気自動車配送経路問題 規模拡大＋電池 関連性として独立に残す。Classical300秒/cell、memory4GiB、量子計算 raw256MiB等の停止条件は[SCALING_LIMITS](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/SCALING_LIMITS.json)に事前固定した。調査BにQAOA/Aer実行は含めない。今回は調査B後続の代替符号化静的比較まで完了し、調査A・科学実行は行っていない。

全本番候補が不適合なら規模を恣意的に縮小/拡大せずNO_SUITABLE_SCALEを保存する。電池差が出ないから容量・距離・初期充電率・標本を変更しない。小規模量子結果の人口外挿、n4 電力量の都市規模解釈、39,930/n倍の費用推計を禁止する。人口集計には別methodologyが必要である。

## 詳細正本と履歴

- [代替符号化比較・手法再判定](../reproducibility/outputs/traffic_simulation/r24_alternative_encoding_decomposition_study/20260927_v1/ALTERNATIVE_ENCODING_DECOMPOSITION_STUDY.md)

- [調査B監査・実行不可判定](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)
- [調査B前段階計画の保存コピー](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/audit/before/01_research_design/RESEARCH_STAGE_ROADMAP.md)

- [評価規模正本・未決事項](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)
- [電池性能根拠](BATTERY_PERFORMANCE_EVIDENCE_PLAN.md)、[電池 想定条件比較](BATTERY_SCENARIO_COMPARISON_PLAN.md)
- [Classical/Quantum共通条件](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)
- [量子化学ベンチマーク](QUANTUM_CHEMISTRY_BENCHMARK_PLAN.md)、[二系統の接続](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)
- [今回更新前の段階計画](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/audit/before/01_research_design/RESEARCH_STAGE_ROADMAP.md)、[今回成果物一覧](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/ARTIFACT_MANIFEST.json)

旧科学成果物・予備試験全ディレクトリ・電池 正本・台帳は不変。全最適化、混合整数線形計画、厳密、量子近似最適化アルゴリズム、Aer、回路、回測定の新規実行0。停止。

<a id="最新gateexact-encoding検証"></a>

## 最新判定基準：厳密 符号化検証

[監査結果](../reproducibility/outputs/traffic_simulation/r24_exact_encoding_backend_protocol/20260927_v1/EXACT_ENCODING_EQUIVALENCE_AUDIT.md)：384経路構造・48 B2 コード words・113 temporal replayを決定論的検証。B2の同値性は元から1台の冗長制約領域限定。複数台本番規模へ適用不可。B1は資源改善なし。formulation/scale/resource 判定基準=実行不可。

次の順序：厳密 compact複数台符号化検証 → 計算方式 手順 固定 → 別途承認された条件を統制した ベンチマーク → 手法比較の規模 固定。現時点でベンチマーク実行ケースは0。調査Aは別系統で想定条件評価の規模を決定。本実験の第0段階は未許可。旧段階表の計算方式受入は、この符号化前提通過後に限る。

<a id="最新fleet-policy--multi-vehicle-gate"></a>

## 最新車両群の方針 / 複数車両 判定基準

[車両台数正本](../reproducibility/outputs/traffic_simulation/r24_fleet_size_multi_vehicle_authority/20260927_v1/FLEET_SIZE_AUTHORITY.md)：M=利用可能上限、m_used=使用台数。車両数は利用可能台数以下保持。単一車両は経路-順序 subproblemのみ。複数台写像の同値性は小規模で確認、主要規模の資源判定基準は実行不可。

最小構成の電気自動車配送経路問題 固定 → 電池 正本 → evaluation-規模 studies → 複数車両 formulation/resource 正本 → 手法比較の規模 固定 → 調査A 想定条件 scale/M確定 → 本実験の第0段階・m0確定 → 電池固定使用台数比較(段階 A) → 同じM内の適応比較(段階 B) → energy/economic分析 → 量子計算 chemistry track。調査Aは独立に準備可能だが本作業では未実行。

電池両手順の方針は固定済み、M_scenario/m0は未定。段階 Aのinfeasibleを増車で救済しない。段階 Bのm_used変化と電力費を全車両群 費用と混同しない。次はseparator表現の厳密容量制約を多項式規模で表す静的設計。backend/main 第0段階は未許可。前節の「複数台写像未検証」という旧判定基準はこの最新節で更新する。

<a id="最新branch-bとcompute-energy段階"></a>

## 最新分岐 Bと計算電力量段階

[多項式容量定式化決定](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/MULTI_VEHICLE_FORMULATION_DECISION.md)：312変数の厳密 複数車両 現行 定式化を固定済み。容量の全経路いいえ-goodは不要になった。主阻害要因はbackend/resource。以前の「容量符号化未解決」という次作業は更新される。

量子計算 track: 定式化 固定 → 条件を統制した alternative-計算方式 手順 固定 → 別作業の許可済みベンチマーク → 手法比較の規模 固定 → **COMPUTE_ENERGY_ACCOUNTING_PROTOCOL** → 本実験の第0段階 Classical/Quantum科学実行。計算電力量 手順は手法比較の規模が利用可能になった後、第0段階実行より前に必須。[会計境界](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/COMPUTE_ENERGY_ROADMAP_EXTENSION.md)を参照。E_system,m=E_EV,m+E_compute,m。Aer電力は古典計算 シミュレーター電力であり実量子処理装置電力ではない。

電池 track: [調査A 準備状況](../reproducibility/outputs/traffic_simulation/r24_polynomial_capacity_formulation_decision/20260927_v1/STUDY_A_READINESS.md)のPhase A/validator/protocol不足を解決 → 全体 古典計算 電気自動車配送経路問題 scaling/Battery 関連性 → 想定条件 scale/M → Main S0/m0 → 固定済み-車両群 段階 A → adaptive-車両群 段階 B → energy/economic分析 → 量子計算 chemistry/integrated analysis。量子計算可否によって想定条件規模を縮小しない。今回調査Aは未実行。

将来問うこと：最適化手法による配送電力の変化は、計算の運用電力を相殺するか。今回は測定・計算・回答しない。全科学実行delta0、本実験の第0段階は未許可。

<a id="最新backend-protocol-freeze--phase1限定"></a>

## 最新計算方式手順固定 / Phase1限定

[Backend 手順](../reproducibility/outputs/traffic_simulation/r24_backend_feasibility_benchmark_protocol/20260927_v1/BACKEND_FEASIBILITY_BENCHMARK_AUTHORITY.md)=固定済み。分岐 B 定式化は変更なし。次作業は最小入れ子構成 n3/M1のdense/MPS・固定パラメーター・最適化処理なし、最大4 circuits/128 回測定 → 整合性 監査 → 停止。第2段階以降は別許可、n8/n10は既存CX上限で事前停止。今回simulation/transpilation実行0。

利用可能な 手法 scale/backend → scientific 量子計算 手順 → COMPUTE_ENERGY_ACCOUNTING_PROTOCOL → 本実験の第0段階 Classical/Quantum実行という境界を保持。Aer/MPS電力は古典計算 シミュレーター電力。将来のE_QPU_break_even=E_EV,C+E_compute,C−E_EV,Qはreal-量子処理装置 電力量-to-solutionの許容上限を定義し、今は計算しない。[metadata/boundary hook](../reproducibility/outputs/traffic_simulation/r24_backend_feasibility_benchmark_protocol/20260927_v1/COMPUTE_ENERGY_METADATA_HOOK.md)。調査A 準備状況は実行不可のまま独立、本実験の第0段階は未許可。
