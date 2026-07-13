"""Insert cell-level research reasoning metadata into the audit notebook."""
from __future__ import annotations

import nbformat as nbf


MAJOR = {
    "PREFLIGHT-CODE-01": ("実行前提が満たされているか", "不足を一括検出してから分析を開始する", "全入力・依存関係の検査", "事前検査表", "環境と入力の監査へ進む"),
    "DECISION-REGISTRY-CODE-01": ("主要研究判断と根拠状態を追跡できるか", "確認可能な行動と事後的再構成を分離して登録する", "18件のDecision Point Registry作成", "decision_point_registry.csv", "Research Questionと方法を接続する"),
    "QUESTION-METHOD-CODE-01": ("研究質問が具体的行動へ接続されているか", "質問・必要証拠・方法・関数・出力を一表にする", "Question–Method–Action Mapping作成", "question_method_action_mapping.csv", "反復過程と結果後の判断を整理する"),
    "ITERATION-DECISION-CODE-01": ("研究範囲と方法がどのように変化したか", "確認できる段階変化だけを再構成する", "反復表とAnalysis-to-Decision表作成", "iterative_research_process.csv; analysis_to_decision_links.csv", "未完了分析と仮定を明示する"),
    "INCOMPLETE-ASSUMPTION-CODE-01": ("不採用・未完了・仮定を残せるか", "成功結果と分離して状態付きで登録する", "未完了分析表と研究者仮定表作成", "incomplete_analysis_registry.csv; researcher_assumption_log.csv", "研究時系列を整理する"),
    "TIMELINE-CODE-01": ("研究の時系列と説明順を区別できるか", "日付不明部分はphase名で記録する", "Chronological Research Timeline作成", "chronological_research_timeline.csv", "環境・データ・計算の監査へ戻る"),
    "PROVENANCE-CODE-01": ("凍結入力を同一ファイルとして特定できるか", "SHA-256で入力同一性を検証する", "来歴表とハッシュ照合", "data_provenance.csv", "一致した入力だけを計算再現へ使用する"),
    "SOURCE-IMPORTS-01": ("比較可能なシナリオ構造をどう作るか", "確認済み実装を再利用して要因計画を構築する", "充電候補・車両・要因直積の生成", "scenario_configurations.csv", "顧客集合を生成する"),
    "CUSTOMER-GENERATE-01": ("実顧客データなしで空間条件をどう表現するか", "人口加重合成顧客をseedごとに生成する", "非復元抽出、需要・サービス時間生成", "synthetic_customers.csv", "デポとルートを構築する"),
    "ROUTE-GENERATE-01": ("最適化を実行せずルート負荷をどう比較するか", "KMeansと最近傍順序による共通プロキシを作る", "デポ選択、クラスタリング、辺・距離・充電候補評価", "route_results.csv", "制約をルート単位で評価する"),
    "CONSTRAINT-EVALUATE-01": ("どの運用制約がモデル上未充足となるか", "各制約を独立したevaluated/feasible/unmet判定へ変換する", "制約評価の縦持ち化", "constraint_evaluations_long.csv", "重み付け別に集計する"),
    "AGGREGATION-CODE-01": ("集計単位で結果がどう変わるか", "route・scenario・seed weightingを分離する", "分子・分母・率の比較", "estimand_comparison.csv", "seed依存の区間を評価する"),
    "BOOTSTRAP-CODE-01": ("対応のある合成反復の変動をどう表すか", "seedクラスタBootstrapを使用する", "1,000回のpercentile区間計算", "constraint_summary.csv", "仮定変更への感度を調べる"),
    "SENSITIVITY-CODE-01": ("基準結果が特定仮定に依存する程度はどれか", "一度に一パラメータだけ変更する", "low/base/high OAT比較", "sensitivity_detail.csv", "結果とモデル要件を解釈する"),
    "CIRCUIT-EVIDENCE-01": ("運用要件と量子資源参照をどう接続するか", "回路幅を計算結果でなく証拠レジストリとして保持する", "出典・定義・検証状態の符号化", "circuit_width_evidence.csv", "参照図を分類して作成する"),
    "RECONCILIATION-CODE-01": ("再計算値はスライド表示値と一致するか", "Notebook内で差分・丸め・許容差を計算する", "参照値との結合と判定", "result_reconciliation.csv", "自動検証へ進む"),
    "VALIDATION-CODE-01": ("生成・集計・照合が設計条件を満たすか", "ハードコードでなく条件式で検査する", "18件の動的検証", "validation_summary.csv", "結果を解釈し最終状態を判定する"),
    "FINAL-STATUS-CODE-01": ("どの再現可能性ラベルが証拠と整合するか", "入力と計算は再現できるが生データ取得は除外する", "失敗数・ハッシュ・未評価項目による規則判定", "reproducibility_status.csv", "実行マニフェストを確定する"),
}


def before_card(code_id: str, values: tuple[str, str, str, str, str]) -> str:
    question, decision, action, output, next_step = values
    return f"""### コード実行前のResearch Action Trail

`CELL-ID: TRAIL-BEFORE-{code_id}`  
`RESEARCH-STAGE: method selection and execution`  
`QUESTION: {question}`  
`DECISION: {decision}`  
`ACTION: {action}`  
`INPUT: 直前の節で確認した入力・設定・生成オブジェクト`  
`OUTPUT: {output}`  
`EVIDENCE: コード出力、保存表、後続の回帰テスト`  
`NEXT-STEP: {next_step}`  
`STATUS: RETROSPECTIVE_RECONSTRUCTION（行動はコードからDIRECTLY_OBSERVABLE、当時の内的理由は記録でない）`

**Previous finding:** 前段階の入力または生成物が利用可能であることを確認した。  
**Research concern:** {question}  
**Method selected:** {decision}  
**Expected evidence:** {output}が生成され、件数・スキーマ・回帰比較を満たすこと。  

#### Problem
{question}

#### Requirement
第三者が追跡できる入力、決定的な処理、検証可能な出力が必要である。

#### Choice and Rationale
{decision}。この理由付けは現行成果物からの再構成であり、当時の思考記録ではない。

#### Action
{action}。
"""


def after_card(code_id: str, values: tuple[str, str, str, str, str]) -> str:
    question, decision, action, output, next_step = values
    return f"""### コード実行後のResearch Action Trail

`CELL-ID: TRAIL-AFTER-{code_id}`  
`RESEARCH-STAGE: validation and interpretation`  
`QUESTION: {question}`  
`DECISION: {decision}`  
`ACTION: {action}`  
`INPUT: 当該コードセルの実行結果`  
`OUTPUT: {output}`  
`EVIDENCE: 表示結果、保存ファイル、自動検証`  
`NEXT-STEP: {next_step}`  
`STATUS: DIRECTLY_OBSERVABLE for output; RETROSPECTIVE_RECONSTRUCTION for decision link`

**Observed output:** {output}を生成または更新する。  
**Validation result:** 後続の自動検証で件数、値域、主キー、保存済み結果との一致を確認する。  
**Research interpretation:** この出力は「{question}」へのモデル条件付き証拠である。  
**Alternative interpretation:** 同じ出力は、採用した仮定・プロキシ・パラメータ設定の帰結としても説明できる。  
**Decision triggered:** {next_step}。  
**Unresolved issue:** 経験的妥当性、実運用妥当性、最適性は未解決である。  

#### Validation
設計どおりの処理であることを動的テストと回帰比較で確認する。

#### Consequence
当該分析対象を評価できる一方、実データへの一般化および代替方法との優劣は確立しない。
"""


def insert_action_trails(notebook) -> None:
    """Add before/after reasoning cards around every major analysis code cell."""
    output = []
    for cell in notebook.cells:
        code_id = cell.get("metadata", {}).get("audit_cell_id")
        if cell.cell_type == "code" and code_id in MAJOR:
            output.append(
                nbf.v4.new_markdown_cell(
                    before_card(code_id, MAJOR[code_id]),
                    metadata={"audit_cell_id": f"TRAIL-BEFORE-{code_id}"},
                )
            )
            output.append(cell)
            output.append(
                nbf.v4.new_markdown_cell(
                    after_card(code_id, MAJOR[code_id]),
                    metadata={"audit_cell_id": f"TRAIL-AFTER-{code_id}"},
                )
            )
        else:
            output.append(cell)
    notebook.cells = output
