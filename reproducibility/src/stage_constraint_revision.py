"""Build the stage-constraint interpretation layer without altering legacy code cells."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf


OUTPUT_NAME = "quantum_transport_reproducibility_audit_stage_constraint_revised.ipynb"


def md(cell_id: str, source: str):
    return nbf.v4.new_markdown_cell(source, metadata={"audit_cell_id": cell_id})


def code(cell_id: str, source: str):
    return nbf.v4.new_code_cell(source, metadata={"audit_cell_id": cell_id})


def insert_after(cells, anchor_id: str, additions) -> None:
    index = next(i for i, cell in enumerate(cells) if cell.metadata.get("audit_cell_id") == anchor_id)
    cells[index + 1:index + 1] = additions


def revise(source: Path, destination: Path) -> None:
    notebook = nbf.read(source, as_version=4)
    original_ids = [cell.metadata.get("audit_cell_id") for cell in notebook.cells]

    rq = next(cell for cell in notebook.cells if cell.metadata.get("audit_cell_id") == "RESEARCH-QUESTION-01")
    rq.source += """

## 技術段階と制約表現に関する研究質問

既存の研究質問をアプリケーション要件の定義に関する上位の問いとして維持し，以下の主質問と補助質問によって技術段階との関係を具体化する．

**Main Research Question：** 量子計算を輸送アプリケーションへ適用する際，各技術段階において，どの運用制約をどの表現レベルで扱うべきか．

- **Sub-RQ1：** 輸送アプリケーションに含まれる制約は，どのような制約群および表現レベルへ分類できるか．
- **Sub-RQ2：** 現在の合成シナリオ分析は，各制約の段階的位置づけを検討するうえで，どのような証拠と限界を提供するか．
- **Sub-RQ3：** 制約表現の高度化は，数理定式化および量子資源要求へどのような構造的影響を与え得るか．

Sub-RQ3は，定式化別の変数数，QUBO項数，qubit数，回路深さを本Notebookで計算していないため，`CONCEPTUAL_PROPOSAL`として扱う．量子資源への定量的影響および技術段階への配置には`REQUIRES_EXPERT_REVIEW`と追加計算が必要である．
"""

    early_cells = [
        md("STAGE-BASED-RESEARCH-POSITIONING-01", """# 2.2 技術段階に基づく制約評価の位置づけ

`CELL-ID: STAGE-BASED-RESEARCH-POSITIONING-01`

本研究における制約評価の目的は，制約の実務的重要度や実配送の失敗率を最終的に推定することではない．目的は，輸送アプリケーションに含まれる各制約について，どの量子技術段階から明示的な表現を検討すべきか，各段階ではどの粒度で表現するか，表現の高度化が問題定義と計算資源要求をどのように変化させ得るかを整理するための基礎情報を構築することである．

現在の合成EV配送分析は，技術段階を確定する評価ではなく，制約候補，操作的定義，単純化によって表現できる範囲，高い表現段階で追加する要素，Stage-Constraint Mappingに必要な論点を抽出するケーススタディである．現在の計算結果は`CURRENT_NOTEBOOK_EVIDENCE`，以下の段階モデルは`CONCEPTUAL_PROPOSAL`として区別する．"""),
        md("TECHNOLOGY-STAGE-DEFINITION-01", """# 2.3 制約表現のための暫定的な技術段階（Provisional Technology Stages for Constraint Representation）

`CELL-ID: TECHNOLOGY-STAGE-DEFINITION-01`  
`STATUS: CONCEPTUAL_PROPOSAL / REQUIRES_EXPERT_REVIEW`

| Stage | Primary evaluation objective | Expected application representation | Typical constraint treatment | Evidence required | Interpretation boundary |
|---|---|---|---|---|---|
| Stage 1：Experimental Demonstration | アルゴリズム，符号化，最小問題が動作するかを確認する | 小規模で静的な最小問題 | 制約は最小限であり，省略内容を明記する | 実装，回路またはシミュレーションの実行記録 | 実運用の代表性を評価しない |
| Stage 2：Constraint-Relevant Evaluation | 主要な静的制約を加えて計算上の評価が成立するかを確認する | 積載量，運行時間上限，固定航続距離，充電アクセス，単純な時間窓 | L1-L2を中心とする静的・明示的表現 | 定式化，制約別結果，古典baseline，感度分析 | 制約間依存や逐次状態を十分に扱わない |
| Stage 3：Application-Relevant Evaluation | 対象アプリケーションに対応する制約構成と依存関係を評価する | 顧客別時間窓，逐次SOC，充電地点選択，充電時間，複数車種 | L2-L3を中心とする結合・逐次表現 | 対象業務データ，定式化検証，専門家レビュー | 実運用システムへの統合を直接示さない |
| Stage 4：Operational Integration | 実際の意思決定過程または運用システムへの統合可能性を評価する | 動的注文，交通，充電器空き，故障，遅延，待ち時間，労務，法規，周辺システム | L3-L4を中心とする動的表現 | 運用データ，システム試験，安全・法務・組織面の評価 | 特定環境での統合結果を他環境へ直接一般化しない |

この4段階は既存結果から推定した成熟度尺度ではなく，議論を構造化する暫定分類である．段階境界，移行条件，必要証拠は文献レビューと複数領域の専門家評価によって修正され得る．"""),
        md("CONSTRAINT-REPRESENTATION-LEVELS-01", """# 2.4 制約表現レベル（Constraint Representation Levels）

`CELL-ID: CONSTRAINT-REPRESENTATION-LEVELS-01`  
`STATUS: CONCEPTUAL_PROPOSAL / REQUIRES_EXPERT_REVIEW`

| Level | Definition | Mathematical implication | Required data | Suitable technology stage | Main limitation |
|---|---|---|---|---|---|
| L0：Not represented | 制約を数理モデルへ含めない | 追加変数・制約なし | 不要 | 主にStage 1 | 省略した運用条件を評価できない |
| L1：Static proxy | 固定閾値，固定倍率，単純上限で代理する | 事後判定または単純な境界条件 | 集計値，固定仕様，研究者仮定 | Stage 1-2 | 状態変化と依存関係を表現しない |
| L2：Explicit static representation | 明示的な変数または制約式で表すが，時間変化や不確実性を扱わない | 決定変数，補助変数，制約式が増加する | 静的な顧客・車両・施設属性 | Stage 2-3 | 逐次状態と外部変動を扱わない |
| L3：Coupled or sequential representation | 他制約との依存，状態遷移，逐次変化を含める | 時点・辺・訪問順に依存する状態変数と結合制約が必要となる | 時系列需要，エネルギー消費，時間窓，充電特性 | Stage 3-4 | 不確実性とリアルタイム変更を限定的にしか扱わない |
| L4：Dynamic operational representation | リアルタイム入力，不確実性，運用変更，外部システムとの相互作用を含める | 動的再最適化，確率・ロバスト表現，システム連携が必要となる | リアルタイム交通・注文・設備・運用データ | 主にStage 4 | データ，検証，統合コストが大きい |

レベルは制約の重要度を表す順位ではなく，モデル内での表現成熟度を表す．分類は`CONCEPTUAL_PROPOSAL`であり，定式化研究者，量子計算研究者，物流実務家による`REQUIRES_EXPERT_REVIEW`である．"""),
    ]
    insert_after(notebook.cells, "RESEARCH-FRAMEWORK-01", early_cells)

    analysis_cells = [
        code("STAGE-CONSTRAINT-BASELINE-01", """stage_baseline_files=[
    SYNTH/'synthetic_customers.csv',
    SYNTH/'route_results.csv',
    SYNTH/'constraint_summary.csv',
    TABLES/'constraint_definitions.csv',
]
stage_baseline_integrity={str(path.relative_to(HERE)):{'row_count':len(pd.read_csv(path)),'sha256':sha256_file(path)} for path in stage_baseline_files}
stage_baseline_rates=constraint_summary.set_index('constraint_name')['route_weighted_unmet_rate'].copy()"""),
        md("CURRENT-CONSTRAINT-LEVEL-AUDIT-01", """# 27.1 現行制約の表現レベル監査

`CELL-ID: CURRENT-CONSTRAINT-LEVEL-AUDIT-01`

以下の分類は現行コード，制約定義，入力列から直接確認できる操作化をL0-L4へ対応づけた監査上の分類である．レベルは制約の実務的重要度を表さない．Payload capacityは静的な合計需要と容量を直接比較する点でL1-L2の境界にあるが，統一表では保守的に`L1-L2`と表記する．"""),
        code("CURRENT-CONSTRAINT-LEVEL-AUDIT-CODE-01", """current_constraint_level_audit=pd.DataFrame([
{'Constraint':'Payload capacity','Conceptual operational requirement':'車両の重量・容積・積載順序を含む積載可能性','Current operationalization':'合成需要の合計と2,000 kgの静的上限を比較','Current representation level':'L1-L2','What is represented':'ルート別の重量合計と単一車両容量','What is not represented':'複数車種，動的需要，積載順序，容積','Evidence source':'constraint_registry; route_results','Status':'CURRENT_NOTEBOOK_EVIDENCE'},
{'Constraint':'Operating time','Conceptual operational requirement':'勤務時間，時間窓，移動・サービス・待機・休憩','Current operationalization':'距離/固定速度＋合成サービス時間を480分上限と比較','Current representation level':'L1','What is represented':'固定速度の移動時間，サービス時間，全体上限','What is not represented':'顧客別時間窓，渋滞，待機，休憩，充電時間','Evidence source':'constraint_registry; parameter_registry','Status':'CURRENT_NOTEBOOK_EVIDENCE'},
{'Constraint':'Driving range','Conceptual operational requirement':'走行中のエネルギー状態と航続可能性','Current operationalization':'全ルート距離を81.2 kmの固定閾値と比較','Current representation level':'L1','What is represented':'静的な使用可能航続距離','What is not represented':'逐次SOC，積載，気温，勾配，回生','Evidence source':'constraint_registry; parameter_registry','Status':'CURRENT_NOTEBOOK_EVIDENCE'},
{'Constraint':'Charging access','Conceptual operational requirement':'運行中に利用可能な充電機会','Current operationalization':'ルートノードと候補connection間の地理距離','Current representation level':'L1','What is represented':'候補への直線距離と条件別閾値','What is not represented':'道路迂回，空き，互換性，出力，待ち時間，利用制限','Evidence source':'constraint_registry; charger candidates','Status':'CURRENT_NOTEBOOK_EVIDENCE'},
{'Constraint':'SOC','Conceptual operational requirement':'走行・充電に伴う逐次エネルギー状態','Current operationalization':'逐次状態遷移を実装していない','Current representation level':'L0','What is represented':'なし','What is not represented':'到着SOC，消費，充電，予備SOCの状態遷移','Evidence source':'constraint_registry; validation T13','Status':'NOT_EVALUATED'},
])
current_constraint_level_audit.to_csv(TABLES/'current_constraint_level_audit.csv',index=False)
display(current_constraint_level_audit)"""),
        code("CONSTRAINT-DEFINITION-ENHANCEMENT-01", """constraint_stage_metadata=pd.DataFrame([
('Payload capacity','capacity','L1-L2','L2-L3','Stage 2-3','複数車種，容積，積載順序，動的需要','CURRENT_NOTEBOOK_EVIDENCE',True),
('Operating-time limit','time','L1','L2-L3','Stage 2-3','顧客別時間窓，待機，休憩，交通，充電時間','CURRENT_NOTEBOOK_EVIDENCE',True),
('Range feasibility','energy/range','L1','L3','Stage 2-3','逐次SOC，積載・気温・勾配依存の消費','CURRENT_NOTEBOOK_EVIDENCE',True),
('SOC feasibility','energy state','L0','L1 then L3','Stage 3','固定航続距離代理の次に逐次SOC','NOT_EVALUATED',True),
('Charging-station access','charging','L1','L2-L3','Stage 2-3','道路迂回，互換性，可用性，待ち時間','CURRENT_NOTEBOOK_EVIDENCE',True),
('Charging-assisted range','charging/range','L1','L3','Stage 3','充電停止選択，到着SOC，充電後SOC','CURRENT_NOTEBOOK_EVIDENCE',True),
('Charging duration','charging/time','L1','L2-L3','Stage 2-3','充電曲線，効率，待ち時間，時間窓との結合','CURRENT_NOTEBOOK_EVIDENCE',True),
],columns=['constraint_name','constraint_family','representation_level_current','potential_representation_level_next','current_technology_stage_relevance','higher_stage_requirements','evidence_status','expert_review_required'])
constraint_definitions_stage_enhanced=constraint_registry.merge(constraint_stage_metadata,on='constraint_name',how='left',validate='one_to_one')
constraint_definitions_stage_enhanced.to_csv(TABLES/'constraint_definitions_stage_enhanced.csv',index=False)
display(constraint_definitions_stage_enhanced)"""),
        md("PROVISIONAL-STAGE-CONSTRAINT-MATRIX-01", """# 27.2 技術段階と制約表現の暫定対応（Provisional Mapping between Technology Stages and Constraint Representation）

`CELL-ID: PROVISIONAL-STAGE-CONSTRAINT-MATRIX-01`  
`STATUS: PROVISIONAL / CONCEPTUAL_PROPOSAL / REQUIRES_EXPERT_REVIEW / NOT_YET_VALIDATED`

このマトリクスは未充足率から直接導出した結果ではない．技術段階ごとに望ましい評価対象を整理した仮説であり，文献レビュー，定式化別資源計算，物流・OR・量子計算の専門家評価によって修正され得る．表内の全セルの根拠状態は`CONCEPTUAL_INFERENCE`であり，現行分析との接続に限って`CURRENT_NOTEBOOK_EVIDENCE`を併記する．"""),
        code("PROVISIONAL-STAGE-CONSTRAINT-MATRIX-CODE-01", """stage_constraint_matrix=pd.DataFrame([
('Payload capacity','L0-L1','L2','L2-L3','L3-L4'),
('Operating time','L0-L1','L1-L2','L3','L4'),
('Driving range','L0-L1','L1-L2','L3','L4'),
('Charging','L0','L1-L2','L3','L4'),
('SOC','L0','L1','L3','L4'),
('Traffic','L0','L0-L1','L2-L3','L4'),
('Demand uncertainty','L0','L1','L2-L3','L4'),
],columns=['Constraint','Stage 1','Stage 2','Stage 3','Stage 4'])
stage_constraint_matrix['Evidence basis']='CONCEPTUAL_INFERENCE; NOT_YET_VALIDATED'
stage_constraint_matrix['Status']='PROVISIONAL; CONCEPTUAL_PROPOSAL; REQUIRES_EXPERT_REVIEW'
stage_constraint_matrix.to_csv(TABLES/'provisional_stage_constraint_matrix.csv',index=False)
display(stage_constraint_matrix)"""),
        md("CONSTRAINT-REPRESENTATION-GAP-01", """# 27.3 現行モデルと次段階表現のギャップ

`CELL-ID: CONSTRAINT-REPRESENTATION-GAP-01`

ギャップ表は現行コードから確認できる不足を，次に検討する表現と必要データへ接続する．Candidate technology stageは確定的な配置ではなく`CONCEPTUAL_PROPOSAL`であり，`REQUIRES_EXPERT_REVIEW`である．"""),
        code("CONSTRAINT-REPRESENTATION-GAP-CODE-01", """constraint_representation_gap=pd.DataFrame([
('Payload capacity','合成需要合計と単一容量','L1-L2','複数車種・容積・積載順序を含む明示的制約','車種別容量，容積，品目，積卸順序','車両選択と訪問順との結合','Stage 2-3','OR・物流専門家レビュー，観測積載データ'),
('Operating time','固定速度＋サービス時間＋全体上限','L1','顧客別時間窓＋待機・休憩','arrival-time，waiting-time，break variables；時間窓データ','訪問順，交通，充電との時間依存','Stage 3','OR・物流専門家レビュー，運行記録'),
('Driving range','固定81.2 km閾値','L1','逐次SOCと状態依存消費','辺別消費，積載，気温，勾配，SOC変数','訪問順，積載，充電選択との状態依存','Stage 3','車両・エネルギーモデル検証'),
('Charging access','候補への地理的近接性','L1','充電停止選択＋互換性・可用性・待ち','道路迂回，connector，power，availability，queue data','SOC，時間窓，施設状態との結合','Stage 3-4','充電・物流専門家レビュー，運用データ'),
('SOC','未評価','L0','固定航続距離代理（L1），その後に逐次SOC（L3）','初期SOC，予備SOC，辺別消費，充電量，充電曲線','距離，積載，時間，充電の逐次結合','Stage 2 then Stage 3','車両・OR・物流専門家レビュー'),
],columns=['Constraint','Current representation','Current level','Next representation level','Additional variables or data required','Additional dependency introduced','Candidate technology stage','Validation required'])
constraint_representation_gap.to_csv(TABLES/'constraint_representation_gap.csv',index=False)
display(constraint_representation_gap)"""),
        md("STAGE-CONSTRAINT-FLOW-FIGURE-01", """# 27.4 制約表現と技術段階を接続する概念フロー

`CELL-ID: STAGE-CONSTRAINT-FLOW-FIGURE-01`  
`STATUS: CONCEPTUAL_PROPOSAL`

青色の範囲は本Notebookが直接扱う部分，灰色の範囲は`FUTURE_WORK`である．図は処理順序を示す概念図であり，資源量，段階到達確率，因果関係を表さない．"""),
        code("STAGE-CONSTRAINT-FLOW-FIGURE-CODE-01", """from matplotlib.patches import FancyBboxPatch
flow_nodes=['Application\\nrequirement','Constraint\\nfamily','Current proxy\\nrepresentation','Mathematical\\nformulation','Resource\\nimplication','Technology-stage\\nsuitability']
fig,ax=plt.subplots(figsize=(13,3.2)); ax.set_xlim(0,13); ax.set_ylim(0,3); ax.axis('off')
for i,label in enumerate(flow_nodes):
    x=0.25+i*2.1; current=i<3
    box=FancyBboxPatch((x,1.05),1.65,0.9,boxstyle='round,pad=0.04',facecolor='#d9edf7' if current else '#eeeeee',edgecolor='#2c6f93' if current else '#777777',linestyle='-' if current else '--',linewidth=1.4)
    ax.add_patch(box); ax.text(x+0.825,1.5,label,ha='center',va='center',fontsize=9)
    if i<len(flow_nodes)-1: ax.annotate('',xy=(x+2.05,1.5),xytext=(x+1.65,1.5),arrowprops=dict(arrowstyle='->',color='#555555'))
ax.text(2.35,0.55,'CURRENT NOTEBOOK EVIDENCE',ha='center',color='#2c6f93',weight='bold')
ax.text(9.25,0.55,'FUTURE WORK: formulation-specific resources, expert validation, probabilistic propagation',ha='center',color='#666666',fontsize=8)
fig.tight_layout(); fig.savefig(FIGURES/'stage_constraint_flow.png',dpi=320,bbox_inches='tight'); fig.savefig(FIGURES/'stage_constraint_flow.svg',bbox_inches='tight'); plt.show()"""),
        md("MAIN-RESULTS-STAGE-INTERPRETATION-01", """# 27.5 主要結果への段階関連情報の付加

`CELL-ID: MAIN-RESULTS-STAGE-INTERPRETATION-01`

既存の未充足率，分子，分母，信頼区間は変更せず，現在の表現レベル，現時点で可能な解釈，禁止される解釈，次に必要な証拠を付加する．"""),
        code("MAIN-RESULTS-STAGE-INTERPRETATION-CODE-01", """result_stage_rows=[
('Payload capacity','L1-L2','現在の需要・容量設定では非拘束的','現行設定で未充足が0件だった','容量制約が不要とはいえない','複数車種・容積・観測積載と専門家評価'),
('Operating-time limit','L1','Stage 2以降の静的時間表現を検討する材料','固定仮定下で未充足が生じた','Stage 2配置を確定できない','時間窓・交通・待機・休憩を含む定式化'),
('Range feasibility','L1','Stage 2以降の静的航続距離表現を検討する材料','固定閾値超過を確認した','実EV配送失敗率や段階配置ではない','逐次SOCと状態依存消費'),
('SOC feasibility','L0','Stage 3相当の逐次状態表現に未到達','SOCを未評価として保持した','SOC未充足率0%とはいえない','逐次SOC実装と車両・OR専門家検証'),
('Charging-station access','L1','地理的アクセス代理の限界を確認','候補への近接性を評価した','利用可能性・互換性・待ちを示さない','道路迂回，可用性，互換性，待ち時間'),
('Charging-assisted range','L1','簡略充電支援代理の感度を検討する材料','条件付き代理値を算出した','SOC実行可能性を示さない','充電停止選択と到着・出発SOC'),
('Charging-duration feasibility','L1','固定power代理の限界を確認','簡略化した時間判定を算出した','実充電所要時間を示さない','充電曲線，効率，待ち，時間窓'),
]
result_stage_map=pd.DataFrame(result_stage_rows,columns=['constraint_name','Current representation level','Stage-related interpretation','What can be concluded now','What cannot be concluded','Required next evidence'])
constraint_summary_stage_interpretation=constraint_summary.merge(result_stage_map,on='constraint_name',how='left',validate='one_to_one')
constraint_summary_stage_interpretation.to_csv(TABLES/'constraint_summary_stage_interpretation.csv',index=False)
display(constraint_summary_stage_interpretation)"""),
        md("DISCUSSION-CURRENT-EVIDENCE-01", """# 27.6 現行計算結果が段階的位置づけへ提供する証拠

`CELL-ID: DISCUSSION-CURRENT-EVIDENCE-01`

現在の未充足率は，制約の社会実装上の重要度を確定する値ではない．現行の単純化されたシナリオでも未充足が生じる制約，現在の設定では非拘束的な制約，現在のモデルでは評価できない制約を区別する補助証拠である．

積載容量の未充足が0件であったことは，合成需要分布と2,000 kg容量の組合せに条件づけられており，積載制約が不要であることを意味しない．運行時間と航続距離の未充足は，Stage 2以降で静的な表現を検討する理由になるが，配置を直接決定しない．充電アクセスは地理的近接性の代理であり，Stage 3-4で論点となる充電時間，互換性，待ち時間，可用性を含まない．SOCが`NOT_EVALUATED`であることは，現行分析がStage 3相当の逐次エネルギー状態表現へ到達していないことを示す．

OAT感度分析は未充足率が選択した仮定に依存することを示すため，単一の率から制約配置を決定してはならない．現在の分析はStage 1からStage 2へ移る際の静的制約表現を検討するケーススタディとして利用できるが，Stage 3またはStage 4の妥当性を評価していない．"""),
        md("DISCUSSION-STAGE-BASED-INTERPRETATION-01", """# Discussion：技術段階に基づく制約表現の解釈

`CELL-ID: DISCUSSION-STAGE-BASED-INTERPRETATION-01`

## 9.1 Problem scale should include constraint representation

輸送問題の規模は顧客数，車両数，qubit数だけでは記述できない．同じ顧客数でも，時間窓，逐次SOC，充電停止，交通をL0-L4のどのレベルで含むかによって，決定変数，補助変数，制約式，目的関数，ペナルティ項が変化し得る．したがって問題規模の比較には，制約群と表現レベルを併記することが望ましい．

## 9.2 Constraint representation should be stage-dependent

Stage 1の最小実証へ実運用上の全制約を含めることは，本提案の要件ではない．ただし，各段階で何を含め，何を省略し，省略によってどの解釈ができなくなるかを明示する必要がある．段階が高くなるにつれて，静的代理から明示的制約，逐次状態，動的運用へ証拠要求を高めるという整理である．

## 9.3 Binary constraint coverage is insufficient

制約が「ある／ない」という二値だけでは，固定航続距離と逐次SOC，地理的充電アクセスと動的な充電器可用性を区別できない．L0-L4は，制約の重要度ではなく，表現の粒度と依存関係を記録するための暫定尺度である．

## 9.4 Interpretation of the current synthetic analysis

現行分析はStage-Constraint Matrixの最終検証ではない．L1を中心とする静的・代理的表現で，未充足がどのように顕在化するか，どの仮定に依存するか，何が未評価として残るかを示すケーススタディである．

## 9.5 Relationship with quantum computing

本Notebookが扱うのは，制約表現の高度化が数理モデルの構造と量子資源要求へ影響し得るという概念的関係である．実機性能，成功確率，量子優位性，実行時間比較，ノイズ耐性，定式化別の正確なqubit増加，技術段階到達確率は評価していない．

## 9.6 Evidence requirements for stage assignment

制約を特定段階へ配置するには，文献上の表現事例，数理定式化上の必要性，現在のケーススタディ，専門家評価，計算資源への影響，実運用上の必要性，証拠の不確実性を統合する必要がある．現時点では一部のケーススタディ証拠と未確認を含む文献レジストリしかなく，配置は`PROVISIONAL`である．

## 9.7 Main implication

主要な含意は，直ちに最も現実的なEVRPを構築すべきということではない．量子技術の発展段階に応じて，評価対象とする制約の種類，表現粒度，必要証拠を段階的に定義する研究枠組みが必要である，という概念提案である．"""),
    ]
    insert_after(notebook.cells, "INTERPRETATION-01", analysis_cells)

    future = md("FUTURE-WORK-STAGE-CONSTRAINT-01", """# Future Work：Stage-Constraint Mappingの検証手順

`CELL-ID: FUTURE-WORK-STAGE-CONSTRAINT-01`  
`STATUS: FUTURE_WORK`

1. **Refine constraint taxonomy：** 制約群と表現レベルの定義を改善し，文献から制約表現事例を体系的に抽出する．
2. **Expert review：** 技術段階，制約配置，表現レベル，移行条件，省略可能性を，量子計算，OR，物流，車両・充電分野の複数専門家が評価する．
3. **Formulation and resource linkage：** 代表的制約について変数数，補助変数数，制約数，QUBO項数を算出する．目的は量子実機性能ではなくresource implicationの構造を評価することである．
4. **Stage assignment validation：** 文献証拠，専門家評価，定式化規模，ケーススタディを統合し，暫定マトリクスを更新する．
5. **Probabilistic propagation：** 技術段階の変化が制約処理可能性とアプリケーション実現可能性へ波及する条件を確率的に表現する．

Step 5は専門家レビュー前には実施しない．将来予測ではなく条件付きシナリオ分析として設計し，制約間依存を扱い，単純な独立確率の乗算を避ける．""")
    insert_after(notebook.cells, "LIMITATIONS-01", [future])

    conclusion = next(cell for cell in notebook.cells if cell.metadata.get("audit_cell_id") == "FINAL-RESEARCH-LOGIC-01")
    conclusion.source = """# Conclusion

`CELL-ID: FINAL-RESEARCH-LOGIC-01`

現行分析は，固定した入力，合成顧客，ルートプロキシ，研究者が定めたパラメータの下で，制約別の未充足がどのように生じるかを再計算可能な形で示した．この結果は，実配送の失敗率または最適EVRP解の実行可能性を示さない．

顧客数と車両数だけでは，輸送アプリケーションの問題規模を十分に記述できない．問題定義には，技術段階ごとに含める制約群と表現レベルを併記するという研究方向がある．本NotebookはStage-Constraint Mappingの最終結果ではなく，その構築に必要な制約候補，操作化，現行表現と次段階のギャップ，証拠状態を整理した予備研究である．

技術段階の定義，制約配置，量子資源との定量的関係，確率的波及は`CONCEPTUAL_PROPOSAL`または`FUTURE_WORK`であり，文献検証，定式化別計算，`REQUIRES_EXPERT_REVIEW`を必要とする．"""

    existing_id_literal = repr(original_ids)
    validation_cells = [
        md("STAGE-CONSTRAINT-VALIDATION-INTRO-01", """# Stage-Constraint改訂の自動検証

`CELL-ID: STAGE-CONSTRAINT-VALIDATION-INTRO-01`

既存成果物の不変性，追加セルの一意性，暫定分類の状態表示，SOCの未評価，DiscussionとFuture Workの分離，新規表の完全性を検査する．"""),
        code("STAGE-CONSTRAINT-VALIDATION-01", f"""stage_nb_path=HERE/'{OUTPUT_NAME}'
stage_nb=json.loads(stage_nb_path.read_text(encoding='utf-8'))
stage_cells=stage_nb['cells']
stage_ids=[cell.get('metadata',{{}}).get('audit_cell_id') for cell in stage_cells]
original_ids={existing_id_literal}
stage_source='\\n'.join(''.join(cell.get('source',[])) for cell in stage_cells if cell.get('metadata',{{}}).get('audit_cell_id')!='STAGE-CONSTRAINT-VALIDATION-01')
stage_validation=[]
def stage_check(check_id,description,expected,observed,passed):
    stage_validation.append({{'check_id':check_id,'description':description,'expected':expected,'observed':observed,'status':'PASS' if bool(passed) else 'FAIL'}})
stage_check('SC01','CELL-ID uniqueness',len(stage_ids),len(set(stage_ids)),len(stage_ids)==len(set(stage_ids)) and None not in stage_ids)
stage_check('SC02','all original CELL-IDs retained',len(original_ids),sum(x in stage_ids for x in original_ids),set(original_ids).issubset(stage_ids))
current_integrity={{str(path.relative_to(HERE)):{{'row_count':len(pd.read_csv(path)),'sha256':sha256_file(path)}} for path in stage_baseline_files}}
stage_check('SC03','major CSV row counts and hashes unchanged',stage_baseline_integrity,current_integrity,stage_baseline_integrity==current_integrity)
stage_check('SC04','existing aggregate rates unchanged',stage_baseline_rates.to_dict(),constraint_summary.set_index('constraint_name')['route_weighted_unmet_rate'].to_dict(),stage_baseline_rates.equals(constraint_summary.set_index('constraint_name')['route_weighted_unmet_rate']))
stage_check('SC05','matrix constraint names nonempty',0,int(stage_constraint_matrix.Constraint.isna().sum()+(stage_constraint_matrix.Constraint.astype(str).str.strip()=='').sum()),stage_constraint_matrix.Constraint.notna().all() and stage_constraint_matrix.Constraint.astype(str).str.strip().ne('').all())
stage_check('SC06','current representation level assigned',len(current_constraint_level_audit),int(current_constraint_level_audit['Current representation level'].notna().sum()),current_constraint_level_audit['Current representation level'].notna().all())
soc_row=constraint_summary.query('constraint_name=="SOC feasibility"').iloc[0]
stage_check('SC07','SOC remains NOT_EVALUATED',True,bool(pd.isna(soc_row.route_weighted_unmet_rate) and soc_row.evaluated_route_count==0 and current_constraint_level_audit.query('Constraint=="SOC"').Status.iloc[0]=='NOT_EVALUATED'),pd.isna(soc_row.route_weighted_unmet_rate) and soc_row.evaluated_route_count==0 and current_constraint_level_audit.query('Constraint=="SOC"').Status.iloc[0]=='NOT_EVALUATED')
provisional_cell=next(cell for cell in stage_cells if cell.get('metadata',{{}}).get('audit_cell_id')=='PROVISIONAL-STAGE-CONSTRAINT-MATRIX-01'); provisional_text=''.join(provisional_cell['source'])
labels=['PROVISIONAL','CONCEPTUAL_PROPOSAL','REQUIRES_EXPERT_REVIEW','NOT_YET_VALIDATED']
stage_check('SC08','provisional matrix has uncertainty labels',labels,[x for x in labels if x in provisional_text],all(x in provisional_text for x in labels))
stage_check('SC09','Discussion and Future Work are separate sections',True,{{'discussion':'DISCUSSION-STAGE-BASED-INTERPRETATION-01' in stage_ids,'future':'FUTURE-WORK-STAGE-CONSTRAINT-01' in stage_ids}},'DISCUSSION-STAGE-BASED-INTERPRETATION-01' in stage_ids and 'FUTURE-WORK-STAGE-CONSTRAINT-01' in stage_ids)
forbidden=['量子優位性'+'を示した','量子計算性能'+'を評価した','実運用上必要な制約'+'を確定した']
stage_check('SC10','prohibited overclaim phrases absent',0,sum(stage_source.count(x) for x in forbidden),not any(x in stage_source for x in forbidden))
stage_check('SC11','enhanced registry has all required stage columns',7,int(constraint_definitions_stage_enhanced[['constraint_family','representation_level_current','potential_representation_level_next','current_technology_stage_relevance','higher_stage_requirements','evidence_status','expert_review_required']].notna().all(axis=1).sum()),constraint_definitions_stage_enhanced[['constraint_family','representation_level_current','potential_representation_level_next','current_technology_stage_relevance','higher_stage_requirements','evidence_status','expert_review_required']].notna().all().all())
stage_check('SC12','stage analysis reached validation without execution error',True,True,True)
stage_constraint_validation=pd.DataFrame(stage_validation)
stage_constraint_validation.to_csv(TABLES/'stage_constraint_validation.csv',index=False)
display(stage_constraint_validation)
if stage_constraint_validation.status.eq('FAIL').any(): raise AssertionError('Stage-constraint validation failed')"""),
    ]
    final_status_index = next(i for i, cell in enumerate(notebook.cells) if cell.metadata.get("audit_cell_id") == "FINAL-STATUS-01")
    notebook.cells[final_status_index:final_status_index] = validation_cells

    notebook.cells.append(md("REVISION-LOG-STAGE-CONSTRAINT-01", f"""# Stage-Constraint改訂履歴

`CELL-ID: REVISION-LOG-STAGE-CONSTRAINT-01`

- **追加したセクション：** 技術段階定義，制約表現レベル，現行制約監査，Stage-Constraint Matrix，表現ギャップ，概念フロー，Discussion，Future Work，自動検証．
- **修正した既存セクション：** Research Questionへ主質問・補助質問を追加し，既存のFinal Research Logic SummaryをConclusionへ再構成した．
- **新規表：** `current_constraint_level_audit.csv`，`constraint_definitions_stage_enhanced.csv`，`provisional_stage_constraint_matrix.csv`，`constraint_representation_gap.csv`，`constraint_summary_stage_interpretation.csv`，`stage_constraint_validation.csv`．
- **新規図：** `stage_constraint_flow.png`およびSVG版．
- **現在の結果から実施した改善：** 既存制約レジストリへのfamily・current/next level・stage relevance・evidence status・expert review列の付加，主要結果への段階関連解釈の付加．
- **Future Work：** 制約分類の精緻化，専門家レビュー，定式化別資源計算，段階配置の検証，依存関係を含む確率的波及．
- **未検証の概念提案：** 4技術段階，L0-L4，Stage-Constraint Matrix．
- **専門家レビューが必要な項目：** 段階境界，制約配置，移行条件，省略可能性，実務上の必要性．
- **実行確認結果：** 2026-07-13のクリーン実行で既存コード，新規表，新規図，`STAGE-CONSTRAINT-VALIDATION-01`を確認する．配布Notebookには実行出力を埋め込まない．
- **出力ファイル：** `{OUTPUT_NAME}`．

本改訂は，A. 現在のコードとデータから得られる結果，B. 結果に基づくDiscussion，C. 暫定的な技術段階・表現モデル，D. 専門家レビューを要する仮説，E. 将来の確率波及・量子資源評価を状態ラベルと節構成によって区別する．"""))

    destination.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, destination)
