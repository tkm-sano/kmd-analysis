# 研究概要（stable entry）

研究タイトルの正本：[正式タイトル（固定）](RESEARCH_TITLE_AUTHORITY.md)。

現在の研究の問いと仮説の正本：[研究の問いと仮説（2026-09-28記録）](RESEARCH_QUESTION_AND_HYPOTHESIS.md)。

## 2026-09-27 Study B完了：method scaleはBLOCKED

[Minimal EVRP量子resource静的監査](reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)を完了。現行Direct表現はn5/m1でも34変数・471coupler・raw256GiBで、凍結backend上限256MiBを超える。METHOD_COMPARISON_SCALE_AUTHORITY=BLOCKED、選定nなし、S0_QUANTUM_PROTOCOL_RESOURCE_GATE=BLOCKED。n3/n4は検証・pilot/referenceのまま。MODEL_VALIDATION_SCALE_AUTHORITY=FROZEN、scenario scaleはPARTIALLY_FROZEN、main S0はNOT_AUTHORIZED。

次は物理問題を変えない代替encoding/decompositionの静的比較。Study Aは別途未実行。凍結pilot/科学成果物/ledgerを保持し、新規最適化・Aer・QAOA・optimizer評価・circuits・shotsは全て0。以下の評価規模再整理段落はStudy B前の履歴であり、method状態と次taskは本段落が優先する。

## 2026-09-27（評価規模再整理）：small-Nは検証・pilot scope

[評価規模authority](reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存pilot S0の物理・比較contract・成果物は不変。以下の旧S0_SCALE_AUTHORITY=FROZENはsmall-input scopeの値であり、main評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=FROZEN、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / mainのS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01のRandom・Clustered親sampleのnested prefix、n=3,4,5,8,10,15,20（3/4診断、5以上main候補）。最終二規模は未選定で、同じnを強制しない。量子現行Direct表現はn5/m1からmemory下限で不適合、scenario側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→Study A（controlled Classical scaling/Battery relevance）とStudy B（Minimal EVRP QUBO/resource監査）→二規模選定→main S0 authority更新。study設計は固定したが今回は実行していない。main S0はNOT_AUTHORIZED、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

## 2026-09-27：S0物理条件・共通contractの部分freeze

[S0 authority](reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件contract / metricsをFROZEN、S0_QUANTUM_PROTOCOLをBLOCKED、S0_BASELINE_AUTHORITYをPARTIALLY_FROZENとした。scenario側は既存n4・最大3台の構造pilot、method比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

CURRENTはmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全simple配送routeの消費上限がusable18 kWhを下回るため、両layerでcharger訪問decisionを除外し充電INACTIVEを固定した。実車充電出力は未解決のまま、この限定S0のblockerにはしない。経済authorityは別extensionとしてNOT_STARTED。

次作業は凍結S0条件に対するMinimal EVRP Quantum/QUBO encoding・同値性・資源監査。旧Exact/MILP sourceは保存Git treeでhash一致を確認済みだが、将来実行前の復元・runner接続は別途必要。S0/全最適化/量子実行はNOT_STARTED。本段落とS0正本が、以下の旧日付のS0未定義・経済必須記述に優先する。

## 2026-09-26：Minimal EVRP以降の研究順序改訂

VRPTW結果とMinimal EVRP設計authorityはFROZENである。既存経路EV回帰および制御10kWでの充電あり検証はPASS、Minimal EVRP classical modelもN002 WIDEの検証範囲でFROZENである。10kWはCONTROLLED_VALIDATION_CONDITIONであり実車充電性能ではない。実車の実効充電性能はUNRESOLVED/DEFERRED、S0は未実行である。

今後の順序・状態の正本は[研究段階ロードマップ](01_research_design/RESEARCH_STAGE_ROADMAP.md)である。Battery根拠・条件freeze → S0 → 同一条件の[Classical/Quantum EVRP比較](01_research_design/CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md) → S0評価/freeze → [劣化・技術向上条件の比較](01_research_design/BATTERY_SCENARIO_COMPARISON_PLAN.md) → Battery差とmethod差の分離 → 感度分析 → [量子化学/材料R&Dと二系統の統合](01_research_design/BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)へ進む。容量/SOH/技術容量・感度設計authorityはFROZENである。直近の次milestoneは完全なS0条件authorityの定義であり、S0実行ではない。実車充電出力は未解決である。

以下の日付付き全体計画・statusは各時点の記録を保持する。post-Minimal-EVRPの順序・状態が異なる場合は上記master roadmapを優先する。過去のDFR目的・未配送許容等を現在の凍結Minimal EVRPへ導入しない。凍結科学成果物を変更せず、本改訂で新しい科学実行は行わない。

文書ID: `ALIAS-RESEARCH-OVERVIEW`
役割: `PRIMARY_ENTRY`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-27`
全体背景正本: `20260903_20260903_RESEARCH_OVERVIEW.md`
post-Minimal-EVRP順序正本: `01_research_design/RESEARCH_STAGE_ROADMAP.md`

全体研究の背景・過去の段階体系は次の文書を参照する。post-Minimal-EVRPの現行順序は冒頭のmaster roadmapが正本である。

- [研究概要・ロードマップ v17](20260903_20260903_RESEARCH_OVERVIEW.md)
- [現行Research Pipeline実行・正本・検証リファレンス](RESEARCH_PIPELINE_REFERENCE.md)

## 2026-09-09の設計更新

2026-09-09時点の全体設計では[B2C配送パイプライン採択記録](RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を採択した。post-Minimal-EVRPの現行順序は冒頭のmaster roadmapに従う。当時の全体構想は住宅向け宅配を主対象に、39,956候補地点から層化・重み付き非復元抽出し、customer数nと複数seedを実験パラメータにする。主需要単位は配送件数、Baselineは単一depot、主指標はDFR_orders。OR-ToolsとQUBO→QAOA→Qiskit Aerは同一instance・共通Hard Constraintsを使用し、独立Validatorを通して比較する。技術Scenarioではcustomer・需要・Time Window・道路条件を原則固定する。

この2026-09-09方針は当時の全体設計であり、post-Minimal-EVRPでは2026-09-26 master roadmapを優先する。既存成果物の生成・受入事実は保持し、今後の設計採択を実装完了とは扱わない。

## Current reduced branch

R23の正式closure・最終結果・制約とR24 gateは[R23_STATUS.md](05_src/traffic_simulation/R23_STATUS.md)を唯一のcurrent indexとする。full EVRPとreduced route orderingのscopeは分離する。旧statusを含む元文書はarchive status_snapshotsに保持する。

本stable entryはGitHub、Portal、CLI、外部linkとの互換性のために維持する。全体背景は日付入り文書、post-Minimal-EVRPの順序・状態はRESEARCH_STAGE_ROADMAP.mdを正本とし、本文を複製しない。

<a id="stage-1--routing-baseline-next"></a>

経路基準に関する判断は、上記の日付入り正本文書で維持する。
