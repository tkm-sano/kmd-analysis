#!/usr/bin/env python3
"""Build the third-party-submission version of the audit notebook."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE_ROOT = HERE.parent
TARGET = HERE / "quantum_transport_reproducibility_audit_revised.ipynb"
sys.path.insert(0, str(HERE / "src"))
from localize_notebook_ja import localize_markdown_cells
from research_reasoning import insert_action_trails
from future_work_plan import FUTURE_WORK_ITEMS, future_work_markdown


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


input_paths = {
    "source_deck": ROOT / "07_presentations" / "current" / "0712_MDR2_v2_enriched_appendix.pptx",
    "population_mesh": ROOT / "03_data/processed/estat_tokyo_mesh_population_cells.csv",
    "charger_connections": ROOT / "03_data/processed/open_charge_map_tokyo_boundary_clipped_connections.csv",
    "depot_candidates": ARCHIVE_ROOT / "data/processed/evrp_constraint_gap_inputs/depot_candidates_public_proxy_snapshot.csv",
    "vehicle_specs": ARCHIVE_ROOT / "data/processed/evrp_constraint_gap_inputs/vehicle_specs_public_source_snapshot.csv",
    "analysis_parameters": ARCHIVE_ROOT / "data/processed/evrp_constraint_gap_inputs/analysis_parameters.csv",
    "quantum_evidence": ARCHIVE_ROOT / "data/processed/evrp_constraint_gap_inputs/quantum_vrp_evidence_registry.csv",
    "circuit_resources": ROOT / "02_literature/extraction_tables/circuit_resources.csv",
    "paper_registry": ROOT / "02_literature/references/papers.csv",
    "stored_customers": ARCHIVE_ROOT / "data/processed/scenario/synthetic_customers.csv",
    "stored_routes": ARCHIVE_ROOT / "data/processed/route_proxy/route_proxy_results.csv",
    "stored_summary": ARCHIVE_ROOT / "data/processed/constraints/constraint_summary.csv",
}
expected_hashes = {key: sha256(path) for key, path in input_paths.items()}

nb = nbf.v4.new_notebook(
    metadata={
        "kernelspec": {"display_name": "Python 3.11", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "audit_scope": "Computational Reproduction from Frozen Processed Inputs and Audit Reconstruction",
    }
)
cells = []


def md(section: str, cell_id: str, body: str) -> None:
    cells.append(
        nbf.v4.new_markdown_cell(
            f"# {section}\n\n`CELL-ID: {cell_id}`\n\n{body}",
            metadata={"audit_cell_id": cell_id},
        )
    )


def code(cell_id: str, source: str) -> None:
    cells.append(nbf.v4.new_code_cell(source, metadata={"audit_cell_id": cell_id}))


def protocol(purpose: str, inputs: str, processing: str, outputs: str, validation: str, boundary: str) -> str:
    return (
        f"**Purpose:** {purpose}  \n**Inputs:** {inputs}  \n**Processing:** {processing}  \n"
        f"**Outputs:** {outputs}  \n**Validation:** {validation}  \n"
        f"**Interpretation Boundary:** {boundary}"
    )


md(
    "1. Title and Submission Information",
    "SUBMISSION-INFO-01",
    "**Toward Evaluating Problem Scale in Quantum Computing: Focusing on Operational Constraints in Transportation**  \n"
    "Author: 82535190 Takuma Sano  \nSubmission artifact: third-party reproducibility and interpretability audit.  \n"
    "Correct source deck: `07_presentations/current/0712_MDR2_v2_enriched_appendix.pptx`.",
)
md(
    "Research Premises and Disclosure Statement",
    "PREMISES-DISCLOSURE-01",
    r"""## 1. 研究の性質

本Notebookは、量子技術評価の前段階として、輸送アプリケーションで表現すべき運用制約を構造化する**探索的・予備的分析**である。量子アルゴリズムの性能実験、EVRP最適化実験、実物流の検証実験ではない。本Notebookでは、量子回路、量子シミュレータ、量子実機、古典EVRPソルバーを実行していない。実行するのは、凍結済み公開データ由来入力からの合成顧客生成、空間クラスタリング、ルートプロキシ構築、制約別の記述的評価、BootstrapおよびOAT感度分析である。

## 2. 推定対象

- **observational unit:** 生成された合成顧客、または制約評価に用いるroute-condition行。実観測ではない。
- **analytical unit:** 指定された顧客集合、車両数、充電条件、seedから構成されるルートプロキシ。
- **aggregation unit:** 主結果は評価可能なルート。補助的にscenario-conditionおよびseed単位でも集計する。
- **numerator:** 対象制約について`unmet=True`となった評価可能ルート数。
- **denominator:** 対象制約について必要列が存在し、`evaluated=True`となったルート数。SOCは分母0である。
- **weighting rule:** 主結果はroute-weightedであり、各評価可能ルートへ等しい重みを与える。scenario-weightedとseed-weightedは別の推定量として併記する。
- **conditioning assumptions:** 凍結入力、人口加重生成、需要・サービス時間分布、デポ選択、KMeans、最近傍訪問順、道路距離係数、車両仕様、充電条件、一定速度などを固定する。
- **intended interpretation:** 現行の合成モデルとルートプロキシの下で、各運用制約が明示的なモデル表現を必要とする可能性を示す分析信号。
- **prohibited interpretation:** 実際の配送失敗率、最適EVRP解の実行不能率、企業・事業所の運用品質、EV運用可能性全体、または量子計算の優位性として解釈してはならない。

各制約は個別に評価される。したがって、個別制約の未充足率は、全制約を同時に課した場合の共同実行不能率ではない。各率の事象は重複し得るため、複数の未充足率を加算してはならない。

## 3. 合成データの位置づけ

合成顧客は実在する顧客、配送記録、企業、事業所、個人を表さない。標本母集団は、凍結済みe-Stat人口メッシュのうち、人口が正で実装上の本土座標範囲を満たすメッシュである。メッシュ人口 $P_m$ に対し、抽出確率を $p_m=P_m/\sum_jP_j$ とする。各`(customer_count, seed)`内では非復元抽出を用いるため、同一シナリオ内で同じメッシュは重複しない。乱数生成器は`numpy.random.default_rng(seed × 100000 + customer_count)`である。需要は5–30 kg、サービス時間は5–15分の離散一様分布から生成する。

空間表現は選択メッシュの近似重心であり、建物、道路、配送先住所、土地利用を保存しない。人口分布に基づく空間的重みは保存するが、実注文頻度、企業分布、貨物品目、需要相関、時間帯、顧客間依存、配送頻度は保存しない。非復元抽出は、同一メッシュに複数顧客を置かないため、高人口密度メッシュに複数注文が集中する現象を過小表現する可能性がある。

## 4. 対応のあるシナリオ設計

同一の`(customer_count, seed)`で生成された顧客集合を、異なる車両数および充電条件の間で共有する。目的は、条件比較時に顧客配置差を統制することである。このため条件間の観測は独立ではなく、対応のある設計である。同じseed番号は、同一生成規則に用いる識別子であり、実観測単位、実在する配送日、または同一の実世界状況を意味しない。Bootstrapではseedをクラスタ単位として再標本化し、条件間の対応を維持する。

## 5. プロキシの意味

| 要素 | 代理するもの | 代理しないもの |
|---|---|---|
| population mesh | 合成顧客位置の人口ベース空間重み | 注文数、企業数、貨物需要 |
| synthetic customer | 合成された配送地点・需要・サービス時間 | 実在顧客、個人、実注文 |
| depot proxy | 公開物流施設候補の地理的位置 | 実事業者のデポ、能力、所有関係 |
| route proxy | 顧客割当と訪問順を比較する幾何学的構造 | 実道路経路、最短路、最適EVRP解 |
| road-distance multiplier | 直線距離と道路移動距離の差を表す固定倍率 | 実道路網、渋滞、迂回、一方通行 |
| charger candidate | OCM connectionレコードに基づく地理的候補 | 利用可能な充電施設、空き設備 |
| charger condition | 属性・距離閾値による分析用候補選別規則 | 実際の充電サービス水準 |
| baseline vehicle | 1つの公開仕様行に基づく車両シナリオ | 実運用フリート全体、劣化・季節性能 |
| usable driving range | 静的な距離閾値81.2 km | 逐次SOC、重量・気温・道路勾配の影響 |
| operating-time estimate | 距離、一定速度、合成サービス時間の合計 | 渋滞、休憩、待機、時間窓、充電時間を含む実勤務時間 |

デポは顧客集合の重心に最も近い候補から選ぶため、シナリオ間で固定されない可能性がある。したがって顧客条件間の差には、顧客配置だけでなく選択デポの差も含まれ得る。KMeansは緯度経度上の空間クラスタリングであり、積載量、運行時間、航続距離を満たす最適車両割当ではない。最近傍訪問順はgreedyヒューリスティックであり、最短ルートまたは最適EVRP解ではない。

## 6. 充電データの意味

基礎入力の観測単位は**充電施設数ではなくOpen Charge Mapのcharger-connectionレコード**であり、東京都境界へクリップした137 connection行である。候補IDはOCM POI IDとconnection IDを組み合わせて構成する。同一施設が複数connectionを持つ可能性があるため、137件を137施設と解釈してはならない。

本分析はreal-time availability、occupancy、reservation、outage、実車との最終的なconnector compatibility、実効charging power、charging curve、実道路上のdetour route、waiting time、price、営業時間・会員制等のaccess restrictionsを評価しない。条件によって報告connectorラベルと報告powerを選別・簡略計算に使用するが、実際の互換性や供給電力を検証していない。充電候補との地理的近接性は、実際の充電可能性、充電停止の実行可能性、またはSOC実行可能性を保証しない。

## 7. 時間的・地理的整合性

- e-Stat人口メッシュ：2020年国勢調査。ローカル処理スナップショットは2026-07-05時点の研究資産。
- Open Charge Map：取得日2026-07-05。各レコードの更新日は異なり、動的データである。
- P31物流施設候補：対象年度は現在の監査証拠から一意に確認できず`MISSING`。シナリオ用スナップショットは2026-07-11。
- 車両仕様：複数の公開仕様をまとめた2026-07-11スナップショット。各仕様の対象時点・URLは一部`MISSING`。

異なる時点の人口、充電器、物流拠点、車両仕様を組み合わせており、時間的不整合が存在する。「東京都域」はデータごとに同一処理ではない。OCMはN03東京都境界ポリゴンでクリップされたconnection入力を使用する。人口メッシュ生成では、処理済み東京都メッシュに加えて緯度35.45–35.95、経度138.85–140.25の本土範囲フィルタを用いる。P31候補は処理済みmainland Tokyo proxyである。島しょ部はこの本土分析から除外される。分析用緯度経度はWGS84相当のdecimal degreesとして扱うが、各上流原データからのCRS変換過程全体は本Notebookで再実行しない。

## 8. パラメータの状態

| パラメータ | 値 | 分類 | 根拠・状態 |
|---|---:|---|---|
| 平均速度 | 25 km/h | researcher-defined assumption | 観測交通からの較正根拠は`RATIONALE_NOT_VERIFIED` |
| 道路距離係数 | 1.25 | researcher-defined assumption | 実道路比較による根拠は`RATIONALE_NOT_VERIFIED` |
| 使用可能航続距離 | 81.2 km | derived from another parameter | 116 × (0.90−0.20)。逐次SOCではない |
| 積載容量 | 2,000 kg | obtained from public data | 選択車両仕様行。原URL確認は一部`MISSING` |
| 運行時間上限 | 480分 | researcher-defined assumption | 法令・事業データとの対応は`RATIONALE_NOT_VERIFIED` |
| 顧客需要 | 5–30 kg | researcher-defined assumption | 離散一様分布。観測需要ではない |
| サービス時間 | 5–15分 | researcher-defined assumption | 離散一様分布。観測時間ではない |
| 充電条件 | conservative/balanced/broad | researcher-defined assumption | ソースコードに閾値・欠損処理を明示。実サービス区分ではない |
| 感度分析範囲 | low/base/high | researcher-defined assumption | パラメータレジストリ由来。現実的確率は`RATIONALE_NOT_VERIFIED` |
| 地球半径 | 6,371.0088 km | implementation default | Haversine計算用 |
| Bootstrap回数・seed | 1,000・20260711 | researcher-defined / implementation default | 再現可能性のため固定 |

パラメータ分類は、empirically observed、obtained from public data、obtained from literature、derived from another parameter、researcher-defined assumption、implementation defaultを区別する。本分析の主要パラメータにempirically observedな配送事業データはない。

## 9. 統計的解釈

100個のseedは100件の実運用観測ではなく、同一の合成生成モデルから得た100反復である。Bootstrap信頼区間が含むのは、固定済み入力、固定済み生成分布、固定済みモデル、固定済みパラメータの下でのseedクラスタ変動である。データ取得誤差、需要分布の選択、道路距離係数、車両劣化、充電器の可用性、モデル形式、実運用変動は含まない。

route-weighted集計では車両数が多い条件ほど多くのルートを生成するため、集計値への寄与が大きい。Section 19でroute-weighted、scenario-weighted、seed-weightedを区別して併記する。

## 10. 文献証拠のコーディング

- **search date:** `NOT_DOCUMENTED`
- **search source:** ローカル保存PDF、arXiv URL、DOI URL、既存証拠レジストリ
- **search terms:** `NOT_DOCUMENTED`
- **inclusion criteria:** スライドAppendix E/Fおよび既存レジストリに含まれる量子VRP・ベンチマーキング文献。体系的レビューとしての事前基準は`NOT_DOCUMENTED`。
- **exclusion criteria:** `NOT_DOCUMENTED`
- **coding definitions:** 表現、評価、運用検証を区別し、欠損を0へ変換しない。
- **extraction procedure:** ローカルPDF・抽出テキスト・既存レジストリの照合。ページ・式を確認できない値は参照値として保持する。
- **reviewer:** 文献一次抽出者は`NOT_DOCUMENTED`。本Notebookの監査再構成にはOpenAI Codexを使用。
- **verification procedure:** ローカル一次資料との照合および`SOURCE_NOT_VERIFIED`状態の付与。独立した第二査読者は`NOT_DOCUMENTED`。
- **missing-information policy:** `Not reported`（論文に報告なし）、`Not implemented`（実装されていないことを確認）、`Not applicable`（適用対象外）、`Insufficient information`（判定材料不足）を区別する。

論文に記載がないことだけを、当該制約が実装されていない証拠として扱わない。文献由来の回路幅・qubit数は本Notebookの合成シナリオから導出された値ではない。一次資料で位置と意味を追跡できるサーベイ値と、スライドから転記された4件の`SOURCE_NOT_VERIFIED`参照値を分離する。

## 11. 検証結果の意味

再生成データと保存済みCSVの一致は、凍結入力と現在のコードの間の**回帰的一貫性**を示す。一致はempirical validity、operational validity、construct validity、optimality、基礎仮定の正しさ、generalizabilityを証明しない。スライド集計値との一致も、同じ計算経路を再現できたことを示すだけである。

## 12. 研究プロセスの開示

| 項目 | 開示内容 |
|---|---|
| analysis author | 82535190 Takuma Sano |
| code author | リポジトリ原コードの著者情報は`NOT_DOCUMENTED`。監査Notebook改訂コードはOpenAI Codex支援を含む |
| data reviewer | `NOT_DOCUMENTED` |
| literature reviewer | `NOT_DOCUMENTED` |
| generative AI / coding assistant | OpenAI CodexをNotebook生成、コード修正、日本語解説、監査支援に使用 |
| human verification procedure | `NOT_DOCUMENTED`。提出前の人手確認が必要 |
| analysis plan / preregistration | `NOT_DOCUMENTED` / `NOT_PREREGISTERED` |
| planned vs post-hoc | 原スライド分析と提出用監査強化を区別。個別変更の事前・事後区分は`NOT_DOCUMENTED` |
| funding | `NOT_DOCUMENTED` |
| conflicts of interest | `NOT_DOCUMENTED` |
| ethics review | `NOT_DOCUMENTED`。合成データと公開集計・施設データを使用するが、正式な審査要否判断は記録されていない |
| personal-data status | 実在個人を表す顧客データは使用しない。公開施設名等を含む可能性はある |
| submission version | `quantum_transport_reproducibility_audit_revised.ipynb` |
| creation date | 2026-07-13。実行日時はRun ManifestにUTCで記録 |
| Git commit | 実行時にSection 7で取得。未コミット変更の有無も記録 |
| authoritative document | 不整合時に優先する文書は`NOT_DOCUMENTED` |

## 前提一覧

| Premise | Current setting | Evidence | Consequence for interpretation | Status |
|---|---|---|---|---|
| 研究種別 | 運用制約を構造化する探索的予備分析 | 研究目的・実行コード | 最適化性能や量子性能を主張できない | `CONFIRMED` |
| 主要推定対象 | 個別制約のroute-weighted未充足率 | 制約評価・集計コード | 実配送失敗率ではなく、率を加算できない | `CONFIRMED` |
| 顧客データ | 人口加重・非復元抽出による合成顧客 | e-Stat処理入力・生成コード | 実顧客・注文へ直接一般化できない | `CONFIRMED` |
| 対応設計 | 顧客集合を車両・充電条件間で共有 | seed・configuration ID | 条件間観測は独立ではない | `CONFIRMED` |
| デポ | 顧客重心に最も近いP31候補 | 実装コード・候補表 | デポ差がシナリオ差へ混入し得る | `CONFIRMED` |
| ルート | KMeans＋最近傍訪問順 | 実装コード・route edges | 最短路・最適EVRP解ではない | `CONFIRMED` |
| 道路距離 | Haversine×1.25 | パラメータレジストリ | 実道路・交通を表現しない | `ASSUMPTION` |
| 充電データ | 137 connectionレコード | OCM入力スキーマ | 137施設や利用可能充電器を意味しない | `CONFIRMED` |
| SOC | 逐次状態遷移なし | 制約レジストリ | EV運用可能性全体を判定できない | `NOT_EVALUATED` |
| データ時点 | 2020人口と2026取得・スナップショット等を結合 | 来歴表 | 時間的不整合を含む | `CONFIRMED` |
| seed | 合成生成モデルの100反復 | 乱数レジストリ | 100件の実観測ではない | `CONFIRMED` |
| Bootstrap CI | seedクラスタ変動のみ | Bootstrap実装 | モデル・運用不確実性を含まない | `CONFIRMED` |
| 文献回路幅 | 一次資料の構造化サーベイ値とスライド由来4参照値 | 詳細サーベイ表・証拠レジストリ | 本シナリオから導出された値ではなく、Width単独で性能を示さない | `DIRECTLY_REPORTED`と`SOURCE_NOT_VERIFIED`を分離 |
| 回帰検証 | 再生成結果と保存CSVの一致 | 自動検証表 | 経験的・運用的妥当性を証明しない | `CONFIRMED` |
| 人手確認 | 手続きの記録なし | 研究プロセス記録 | 提出前に研究者確認が必要 | `NOT_DOCUMENTED` |
| 倫理・資金・COI | 記録なし | 研究プロセス記録 | 提出先要件に応じ追加開示が必要 | `NOT_DOCUMENTED` |""",
)
md(
    "Research Reasoning and Action Trail",
    "RESEARCH-REASONING-OVERVIEW-01",
    r"""## 記述原則

本節は研究者の内面的思考を創作せず、スライド、コード、データ、出力、Notebook構成および限定的なGit履歴から確認できる行動と判断を再構成する。状態は次の意味で使用する。

- `CONTEMPORANEOUS_RECORD`：当時のスライド、コードコメント、研究資産に明示された判断。
- `DIRECTLY_OBSERVABLE`：現在のコード、データ、出力から直接確認できる行動。
- `RETROSPECTIVE_RECONSTRUCTION`：現在の成果物から再構成した論理であり、当時の思考記録ではない。
- `NOT_DOCUMENTED`：理由または判断を確認できない。
- `UNCERTAIN`：複数の説明が可能で一意に特定できない。

## Research Narrative Overview

1. **Initial observation:** スライド2、5–7は、量子技術評価が問題規模、回路幅、解品質等の技術指標だけでは社会実装条件を十分説明しないという問題設定を示す。`CONTEMPORANEOUS_RECORD`
2. **Perceived problem:** 同程度の問題規模でも、定式化、符号化、補助変数、評価形態により量子資源が異なり、運用要件が表現されているかを別に確認する必要がある。`CONTEMPORANEOUS_RECORD`
3. **Research question:** 輸送固有のインスタンス規模と運用要件をどのように定義すれば、量子資源要件を意味のある形で解釈できるか。`CONTEMPORANEOUS_RECORD`
4. **Analytical need:** 問題規模だけでなく、積載、時間、航続距離、充電、SOC等を明示的な評価対象へ変換する必要が生じた。`RETROSPECTIVE_RECONSTRUCTION`
5. **Methodological choice:** 完全なEVRP最適化ではなく、公開データを空間・技術条件に用い、合成顧客と共通ルートプロキシで個別制約を比較した。行動は`DIRECTLY_OBSERVABLE`、当時の選択理由は一部`RETROSPECTIVE_RECONSTRUCTION`。
6. **Implementation:** 人口加重顧客、デポプロキシ、KMeans車両割当、最近傍訪問順、Haversine×1.25、条件別充電候補、制約評価を実装した。`DIRECTLY_OBSERVABLE`
7. **Validation:** seed固定、件数検査、入力ハッシュ、保存済みCSVとの回帰比較、Bootstrap、OAT、スライド値照合を実行した。`DIRECTLY_OBSERVABLE`
8. **Result:** 距離・時間関連制約が現行シナリオで未充足となり、積載は非拘束的、SOCは未評価だった。`DIRECTLY_OBSERVABLE`
9. **Interpretation:** 結果は運用要件を定式化へ含める必要性を検討する分析信号であり、配送失敗率やEVRP最適解の実行可能率ではない。`CONTEMPORANEOUS_RECORD`および`RETROSPECTIVE_RECONSTRUCTION`
10. **Next decision:** スライド16は、運用現実性を高める方向と、アプリケーション要件・量子技術段階を接続する枠組みの方向を次段階の判断として残す。`CONTEMPORANEOUS_RECORD`

## Research Motivation Chain

| Stage | Researcher observation | Concern or gap | Consequence for the study | Evidence | Status |
|---:|---|---|---|---|---|
| 1 | 技術進歩が単線的な性能向上として提示され得る | 技術能力、適用条件、社会的判断条件が分離されない | 評価枠組みを技術指標以外へ拡張 | slides 2, 5 | `CONTEMPORANEOUS_RECORD` |
| 2 | 量子ルーティング研究は規模・幅・評価形態を報告 | 運用制約の表現と検証が比較可能でない | scale・representation・evidence gapを区別 | slides 6–9 | `CONTEMPORANEOUS_RECORD` |
| 3 | 回路幅は定式化と符号化で大きく変わる | qubit数だけでは応用上の意味を判定できない | 回路幅を参照証拠として限定的に扱う | slide 7; evidence registry | `CONTEMPORANEOUS_RECORD` |
| 4 | 輸送では顧客、車両、デポ、制約を列挙できる | 社会実装条件が未定義のまま資源推定できない | 輸送を初期適用領域に選ぶ | slides 3–4 | `CONTEMPORANEOUS_RECORD` |
| 5 | EV配送では距離・充電・SOCが問題となる | 通常VRP規模だけではEV固有要件を表せない | EVRP側の探索分析を設定 | slides 8–12 | `RETROSPECTIVE_RECONSTRUCTION` |
| 6 | 実配送注文は研究資産に存在しない | 観測顧客による比較を実行できない | 人口加重合成顧客を生成 | input inventory; source code | `DIRECTLY_OBSERVABLE` |
| 7 | 完全最適化・道路経路・SOC実装がない | 統合実行可能性を評価できない | 共通ルートプロキシと個別制約率に限定 | source code; slide 10 | `DIRECTLY_OBSERVABLE` |
| 8 | 基準結果が仮定へ依存する | 単一設定だけでは頑健性が不明 | seed BootstrapとOATを実行 | source code; slide 14 | `DIRECTLY_OBSERVABLE`; rationale partly reconstructed |

## 代替方法の位置づけ

以下の「代替方法」は、当時に実際に比較検討した記録がない限り`POTENTIAL_ALTERNATIVE`であり、「研究者が当時棄却した方法」を意味しない。

| Analytical need | Adopted method | Alternative method | Reason not adopted | Consequence | Status |
|---|---|---|---|---|---|
| 顧客配置 | 人口加重合成 | 実配送注文 | 観測注文が研究資産にない。実際の検討記録はない | 外的妥当性が限定 | `POTENTIAL_ALTERNATIVE` |
| 車両割当 | KMeans | 容量・時間・距離制約付き最適化 | 完全EVRP最適化は現行範囲外 | 最適割当ではない | `CONTEMPORANEOUS_RECORD` for scope; alternative `POTENTIAL_ALTERNATIVE` |
| 訪問順 | greedy最近傍 | TSP/VRP最適化 | 採否理由は`RATIONALE_NOT_DOCUMENTED` | 距離はヒューリスティック | `DIRECTLY_OBSERVABLE` |
| 移動距離 | Haversine×1.25 | 道路ネットワーク最短路 | road-network data unavailableと出力に記録 | 実道路距離ではない | `DIRECTLY_OBSERVABLE` |
| デポ | P31最近傍候補 | 実事業者デポ | 実デポデータがない | シナリオ間でデポが変化 | `DIRECTLY_OBSERVABLE` |
| 評価 | 個別制約未充足 | 統合EVRP実行可能性 | SOC・時間窓・充電動態が未実装 | 共同実行不能率を示さない | `DIRECTLY_OBSERVABLE` |
| 不確実性 | seed-cluster Bootstrap | モデル・パラメータ不確実性の統合 | 現行実装範囲外。採否記録なし | CIの範囲が限定 | `POTENTIAL_ALTERNATIVE` |
| 感度 | OAT | factorial/global sensitivity | 採否理由は`RATIONALE_NOT_DOCUMENTED` | 相互作用を評価しない | `DIRECTLY_OBSERVABLE` |

## End-to-End Research Logic Diagram

`CLASSIFICATION: CONCEPTUAL_RECONSTRUCTION`

```text
Observation                  [Slides 2, 5–7 / CLM-S02, CLM-S07]
    ↓
Research concern             [Section 2 / RESEARCH-QUESTION-01]
    ↓
Research question            [Slide 4 / RESEARCH-QUESTION-01]
    ↓
Required evidence            [Sections 8–11 / provenance, parameters, evidence]
    ↓
Methodological choice        [Sections 12–21 / METHOD-* cells]
    ↓
Data construction            [CUSTOMER-GENERATE-01, ROUTE-GENERATE-01]
    ↓
Computation                  [CONSTRAINT-EVALUATE-01, AGGREGATION-CODE-01]
    ↓
Validation                   [RECONCILIATION-CODE-01, VALIDATION-CODE-01]
    ↓
Result                       [Section 26 / constraint_summary.csv]
    ↓
Interpretation               [Sections 27–28]
    ↓
Method revision / next issue [Slide 16 / operational realism vs application-stage framework]
```

## 研究時系列と説明順序の分離

現在のNotebookは第三者が理解しやすい**expository order**へ再構成されている。この順序を、研究者が当初から完全に計画していたresearch chronologyとして扱ってはならない。確認可能な大まかな段階は、Initial framing → Literature and metric review → Problem-scale comparison → Transportation scenario definition → Synthetic data construction → Constraint operationalization → Sensitivity analysis → Reproducibility audit → Current revisionである。正確な日付と各段階の内部順序は、2026-07-13のリポジトリ再構成コミット以外は`NOT_DOCUMENTED`である。
""",
)
md(
    "2. Research Question and Objective",
    "RESEARCH-QUESTION-01",
    "**Question:** How should transport-specific problem-instance scale and operational requirements be defined so that reported quantum-resource requirements can be meaningfully interpreted?\n\n"
    "The computational objective is to identify model-conditional operational constraints in synthetic EVRP-side scenarios before interpreting formulation-specific quantum resources. It is not an EVRP optimizer, operational performance study, or demonstration of quantum advantage.",
)
md(
    "2.1 Analytical Framework and Contribution",
    "RESEARCH-FRAMEWORK-01",
    "本研究の分析単位は、量子アルゴリズムそのものではなく、量子資源推定に先立って定義されるべき**アプリケーション要件**である。論理構造は、(i) application requirements、(ii) mathematical representation、(iii) quantum formulation and encoding、(iv) quantum-resource requirements、(v) feasible technology stage の順に構成される。顧客数や車両数のみを問題規模とみなすと、時間、航続距離、充電、SOCなどの表現に必要な変数・制約・補助変数を捨象するため、異なる研究間のqubit数を直接比較する根拠が失われる。\n\n"
    "本Notebookの学術的貢献は、量子資源量を新たに推定することではなく、公開データと明示的な合成仮定を用いて、どの運用制約が定式化上無視できない可能性を持つかを監査可能な形で示す点にある。したがって、主要な検証対象は、制約別のモデル条件付き未充足率、そのシナリオ依存性、仮定変更への感度、および現行量子VRP文献における表現・検証証拠との対応である。これは探索的な要件同定研究であり、因果効果の推定、配送事業者母集団への統計的一般化、または量子優位性の検定ではない。",
)
md(
    "3. Scope of Reproduction",
    "SCOPE-01",
    "**Mode: `Computational Reproduction from Frozen Processed Inputs and Audit Reconstruction`.**\n\n"
    "| Reproduction target | Method | Input | Status | Why not broader | Evidence |\n"
    "|---|---|---|---|---|---|\n"
    "| Synthetic customers | Re-execute source function | Frozen e-Stat processed mesh | REPRODUCED | Raw e-Stat acquisition is not rerun | row-level comparison |\n"
    "| Routes and constraints | Re-execute source functions | Frozen processed inputs | REPRODUCED | Not a road-network optimizer | row-level comparison |\n"
    "| Aggregates/bootstrap/OAT | Recalculate | regenerated route evaluations | REPRODUCED | Fixed model and parameters | dynamic tests |\n"
    "| Open-data acquisition | Inspect provenance | local snapshots/scripts | DERIVED | historical requests not fully archived | hashes and scripts |\n"
    "| Circuit-width evidence | Structured survey plus separated slide references | local primary-source corpus and slides | LITERATURE_DERIVED / REFERENCE_ONLY | survey is non-exhaustive; four slide values remain unverified | survey tables and evidence registry |\n"
    "| SOC feasibility | none | none | NOT_EVALUATED | sequential model absent | constraint registry |",
)
md(
    "4. Interpretation Boundaries",
    "BOUNDARY-01",
    "> 本Notebookで算出する未充足率は、合成シナリオおよびルートプロキシの仮定に条件づけられた分析指標である。実際の配送失敗率、最適化されたEVRP解の実行可能率、または観測された事業運用実績を表すものではない。\n\n"
    "The route proxy is neither a road-network path nor an optimized solution. Range feasibility is not complete EV operability. `NOT_EVALUATED` is never converted to zero.",
)
md(
    "5. Execution Instructions",
    "EXECUTION-01",
    "From `reproducibility/`: create Python 3.11 environment, install `requirements-lock.txt`, then execute this notebook from the first cell. All generated files are written below `outputs/`; frozen inputs remain read-only.",
)
md(
    "6. Preflight Check",
    "PREFLIGHT-01",
    protocol(
        "collect every missing dependency/input before stopping",
        "repository sentinels, required files/columns, Python modules",
        "root discovery, existence/schema/import/Git/write checks",
        "preflight table",
        "all ERROR-level checks must pass",
        "availability does not establish provenance or scientific validity",
    ),
)
code(
    "PREFLIGHT-CODE-01",
    f"""from pathlib import Path
import json, os, platform, subprocess, sys, time, warnings
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

START_TIME=datetime.now(timezone.utc)
candidate=Path.cwd().resolve()
support_candidates=[candidate/'src',candidate/'legacy/non_sumo_route_proxy_analysis/reproducibility/src',candidate.parent/'src']
support_dir=next((p for p in support_candidates if (p/'audit_support.py').is_file()),None)
if support_dir is None:
    raise FileNotFoundError(f'audit_support.py not found from {{candidate}}; checked {{support_candidates}}')
sys.path.insert(0,str(support_dir))
from audit_support import *
ROOT=find_repository_root(candidate)
HERE=ROOT/'legacy/non_sumo_route_proxy_analysis/reproducibility'
OUTPUTS=HERE/'outputs'
FIGURES=OUTPUTS/'figures'; TABLES=OUTPUTS/'tables'; LOGS=OUTPUTS/'logs'; MANIFESTS=OUTPUTS/'manifests'; SYNTH=OUTPUTS/'synthesized'
for directory in [FIGURES,TABLES,LOGS,MANIFESTS,SYNTH]: directory.mkdir(parents=True,exist_ok=True)

required_files={{
 'source_deck':(ROOT/'07_presentations/current/0712_MDR2_v2_enriched_appendix.pptx',None),
 'population_mesh':(ROOT/'03_data/processed/estat_tokyo_mesh_population_cells.csv',['mesh_code','total_population']),
 'charger_connections':(ROOT/'03_data/processed/open_charge_map_tokyo_boundary_clipped_connections.csv',['connection_id','latitude','longitude','connection_type','power_kw']),
 'depot_candidates':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/depot_candidates_public_proxy_snapshot.csv',['scenario_depot_id','latitude','longitude','selection_rule']),
 'vehicle_specs':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/vehicle_specs_public_source_snapshot.csv',['scenario_vehicle_id','battery_kwh','catalog_range_km','payload_kg']),
 'analysis_parameters':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/analysis_parameters.csv',['parameter','low','base','high','unit']),
 'quantum_evidence':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/quantum_vrp_evidence_registry.csv',['reference_id','paper_title','url']),
 'circuit_resources':(ROOT/'02_literature/extraction_tables/circuit_resources.csv',['paper_id','problem','instance_or_scope','circuit_width_qubits','source_location']),
 'paper_registry':(ROOT/'02_literature/references/papers.csv',['id','title','authors','year','problem','url','doi']),
 'stored_customers':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/scenario/synthetic_customers.csv',['customer_configuration_id','seed','customer_id']),
 'stored_routes':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/route_proxy/route_proxy_results.csv',['scenario_id','seed','route_proxy_distance_km']),
 'stored_summary':(ROOT/'legacy/non_sumo_route_proxy_analysis/data/processed/constraints/constraint_summary.csv',['constraint_name','route_weighted_unmet_rate']),
}}
required_modules=['numpy','pandas','scipy','sklearn','matplotlib','geopandas','shapely','pyproj','requests','pydantic','pptx','nbformat','pytest']
preflight=preflight_check(ROOT,OUTPUTS,required_files,required_modules)
display(preflight)
preflight.to_csv(TABLES/'preflight_check.csv',index=False)
if preflight.status.eq('FAIL').any():
    raise RuntimeError('Preflight failed. Review all FAIL rows above; no analysis was started.')""",
)
md(
    "6.1 研究判断レジストリ",
    "REASONING-REGISTRY-01",
    "以下の表は、現在のスライド、コード、入力、出力から研究判断を再構成したものである。`RETROSPECTIVE_RECONSTRUCTION`は当時の思考記録ではない。理由を確認できない判断は`RATIONALE_NOT_DOCUMENTED`とする。証拠区分はpublic dataset、literature evidence、code output、visual inspection、regression test、sensitivity result、researcher assumption、implementation constraint、unavailable evidenceを区別する。",
)
code(
    "DECISION-REGISTRY-CODE-01",
    """decision_columns=['decision_id','date_or_stage','question_faced','available_information','options_considered','selected_option','rationale','action_taken','expected_consequence','observed_consequence','validation','subsequent_decision','evidence','status']
decision_rows=[
('D01','Initial framing','なぜ交通・配送を対象としたか','スライド3の適用領域比較','交通; 他領域','交通・配送','問題インスタンスと運用要件を複数水準で定義可能','輸送を初期領域に設定','適用要件と資源解釈を具体化','公開データと制約を構造化','slide trace','EV配送条件へ具体化','slide 3','CONTEMPORANEOUS_RECORD'),
('D02','Scenario definition','なぜEV配送条件を扱うか','range・SOC・charging gap','通常VRP; EVRP','EV配送側の制約','EV固有要件を明示するため（再構成）','航続距離・充電等を評価対象化','運用要件の追加負荷を示す','距離・充電関連の未充足を算出','constraint registry','SOC未評価を分離','slides 8–13; code','RETROSPECTIVE_RECONSTRUCTION'),
('D03','Data construction','なぜ合成顧客か','実注文データなし; 人口メッシュあり','実注文; 合成','人口加重合成','RATIONALE_NOT_DOCUMENTED（可用資産から合理的に再構成可能）','17,500行を生成','比較可能な顧客集合','保存済み結果と一致','regression test','実需要較正を将来課題化','public dataset; code','DIRECTLY_OBSERVABLE'),
('D04','Geographic scope','なぜ東京都域か','東京の人口・充電・P31処理資産','東京; 他地域','東京都本土プロキシ','RATIONALE_NOT_DOCUMENTED','東京入力を統合','共通地理範囲','東京合成シナリオを生成','bounds/hash tests','一般化限界を明記','public dataset','NOT_DOCUMENTED'),
('D05','Factor design','なぜ顧客数25/50/100か','スライド設定','他水準を含む','25/50/100','RATIONALE_NOT_DOCUMENTED','3水準を直積化','規模応答を比較','27構造を生成','count test','規模別集計','slide 18; config','CONTEMPORANEOUS_RECORD'),
('D06','Factor design','なぜ車両数1/3/5か','スライド設定','他水準を含む','1/3/5','RATIONALE_NOT_DOCUMENTED','3水準を直積化','ルート分割応答を比較','1/3/5ルートを生成','route count test','重み付け差を明記','slide 18; config','CONTEMPORANEOUS_RECORD'),
('D07','Randomization','なぜ100 seedか','スライド設定','他反復数','100','RATIONALE_NOT_DOCUMENTED','100顧客集合を生成','合成空間変動を観察','各顧客数100集合','seed completeness test','cluster Bootstrap','slide 18; code','CONTEMPORANEOUS_RECORD'),
('D08','Depot','なぜデポプロキシか','P31候補; 実デポなし','実デポ; 固定点; proxy','最近傍P31候補','RATIONALE_NOT_DOCUMENTED','顧客重心最近傍を選択','各集合に出発点を付与','シナリオでデポが変化','coordinate tests','デポ依存を限界化','public dataset; code','DIRECTLY_OBSERVABLE'),
('D09','Assignment','なぜKMeansか','顧客座標; 車両数','最適割当; random; KMeans','KMeans','RATIONALE_NOT_DOCUMENTED','seed固定n_init=20','空間的に近い顧客を群分け','車両数と同数のクラスタ','route count regression','制約評価へ進む','code','DIRECTLY_OBSERVABLE'),
('D10','Visit order','なぜ最近傍順か','クラスタ内座標','TSP最適化; 道路順; greedy','greedy最近傍','RATIONALE_NOT_DOCUMENTED','デポ往復順を生成','共通距離proxy','非最適距離を生成','stored route comparison','道路・最適性限界を明記','code','DIRECTLY_OBSERVABLE'),
('D11','Distance','なぜ道路ネットワークを使わないか','network distance unavailable記録','network; Haversine','Haversine×係数','network data unavailable; 係数根拠は未確認','距離に1.25を適用','道路迂回を粗く近似','route_proxy_distanceを生成','nonnegative/regression tests','road-networkを次段階へ','code output','DIRECTLY_OBSERVABLE'),
('D12','Constraints','なぜrange/payload/time/accessか','slides 8–13','他制約を含む','個別4領域＋簡略充電','スライド研究範囲','各feasible flagを評価','拘束的要件を識別','制約別率を生成','rate tests','SOCを別扱い','slides; code','CONTEMPORANEOUS_RECORD'),
('D13','Scope limit','なぜSOC/待ちを評価しないか','状態遷移・queueデータなし','実装; 未評価','NOT_EVALUATED','必要実装・データが存在しない','分母0として保持','過剰主張を回避','SOC rateはNaN','T13 test','将来課題へ移す','code; limitation','DIRECTLY_OBSERVABLE'),
('D14','Evaluation unit','なぜルート単位か','車両別route proxy','顧客; scenario; route','route','RATIONALE_NOT_DOCUMENTED','route feasible flagsを作成','車両ルートごとの負荷比較','車両数で寄与が変化','estimand table','他weightingを併記','code','DIRECTLY_OBSERVABLE'),
('D15','Uncertainty','なぜBootstrapか','100 paired seeds','解析式; row bootstrap; cluster bootstrap','seed-cluster Bootstrap','対応設計維持（実装docstring）','1,000回復元抽出','seed変動区間','percentile CI','stored summary comparison','OATへ進む','code comments/output','DIRECTLY_OBSERVABLE'),
('D16','Sensitivity','なぜOATか','low/base/high registry','global/factorial; OAT','OAT','RATIONALE_NOT_DOCUMENTED','一変数ずつ変更','仮定別応答を分離','234行の応答','sensitivity table','相互作用を未解決化','code','DIRECTLY_OBSERVABLE'),
('D17','Literature','なぜ回路幅を残すか','slide 7 values; source uncertainty','削除; 計算値扱い; reference','REFERENCE_ONLY','研究論理との接点を残し過剰主張を避ける（再構成）','証拠レジストリ化','量子側との限定的接続','4値SOURCE_NOT_VERIFIED','status audit','page/equation検証を課題化','slides; local papers','RETROSPECTIVE_RECONSTRUCTION'),
('D18','Audit revision','なぜ再現性監査を追加したか','提出用監査要件; frozen outputs','結果提示のみ; audit','第三者監査Notebook','現ユーザー要求','preflight/manifest/testsを追加','再実行・追跡可能性','18 tests PASS','clean execution','説明と研究時系列を分離','current revision','CONTEMPORANEOUS_RECORD')]
decision_registry=pd.DataFrame(decision_rows,columns=decision_columns)
decision_registry.to_csv(TABLES/'decision_point_registry.csv',index=False)
display(decision_registry)""",
)
code(
    "QUESTION-METHOD-CODE-01",
    """question_method_mapping=pd.DataFrame([
('規模・車両数で制約負荷はどう変わるか','資源解釈前に規模応答が必要','対応付けた顧客集合とroute flags','3×3×3 factorial＋100 seeds','build_analysis_configurations; construct_route_proxies','scenario/estimand tables','モデル条件付き規模応答','水準根拠・外的妥当性'),
('充電条件で地理的アクセスはどう変わるか','EV固有要件の一側面','OCM connection属性と距離','3 screening conditions','build_eligible_charger_candidates; evaluate_routes_by_condition','charger candidates; access rates','地理的候補アクセス','実利用・SOC・queue'),
('どの制約が未充足か','量子定式化へ含める要件を検討','route-level numerator/denominator','個別制約評価','build_constraint_evaluations','constraint_summary','拘束性の分析信号','共同実行可能性'),
('結果はseedで安定するか','合成配置差を把握','paired seed clusters','cluster Bootstrap','cluster_bootstrap_constraint_summary','95% CI','固定モデル下seed変動','モデル不確実性'),
('結果は仮定に依存するか','単一基準値の過剰解釈回避','low/base/high response','OAT','run_oat_sensitivity','sensitivity_detail','局所モデル応答','相互作用')],columns=['research_question','why_it_mattered','required_evidence','selected_method','concrete_action','output','interpretation','remaining_uncertainty'])
question_method_mapping.to_csv(TABLES/'question_method_action_mapping.csv',index=False)
display(question_method_mapping)""",
)
code(
    "ITERATION-DECISION-CODE-01",
    """iterative_process=pd.DataFrame([
('Framing','技術性能を中心に評価','文献・スライド整理','応用要件が別軸として必要','scale/representation/evidence gapを導入','slides 2–9が変更後構造を示す','slides; exact chronology uncertain'),
('Application definition','問題規模中心','輸送適用条件を整理','大規模でも代表的とは限らない','規模×制約カバレッジへ拡張','slide 9','CONTEMPORANEOUS_RECORD'),
('Exploratory computation','公開データの地理可視化','合成scenario/route/constraint計算','SOC・道路経路・実需要が不足','proxy境界とNOT_EVALUATEDを明示','slides 10–14; code','RETROSPECTIVE_RECONSTRUCTION'),
('Interpretation','主要未充足率を提示','OAT・文献比較','仮定と証拠形態が比較を左右','次段階をoperational realism/frameworkに分岐','slides 14–16','CONTEMPORANEOUS_RECORD'),
('Audit','結果提示中心','再生成・hash・tests','生データ取得と出典に不足','frozen-input reproductionへ限定','current notebook','CONTEMPORANEOUS_RECORD')],columns=['iteration','initial_assumption','analysis_performed','finding_or_problem','revision_made','reason_for_revision','evidence'])
result_links=pd.DataFrame([
('R1','Payload 0%','現設定内で非拘束。設定が緩い可能性もある','モデル内では高; 外部は低','一般に不要とは判断しない','OATと限界記述','需要較正なし'),
('R2','Time 33.5%','時間表現が結果へ影響','モデル内中','時間関連変数を要件候補として維持','感度分析','traffic/break/windowsなし'),
('R3','Range 64.4%','静的距離閾値が頻繁に超過','モデル内中','rangeを省略しない','OAT; SOC課題化','実エネルギーなし'),
('R4','SOC not evaluated','rangeだけでEV実行可能性を判定不能','高','過剰解釈を禁止','NOT_EVALUATED','状態遷移未実装'),
('R5','Circuit values unverified','資源接続は参照段階','低','REFERENCE_ONLYを維持','証拠レジストリ','page/equation不足')],columns=['result_id','result','interpretation','confidence','decision_enabled','action_taken','unresolved_concern'])
iterative_process.to_csv(TABLES/'iterative_research_process.csv',index=False); result_links.to_csv(TABLES/'analysis_to_decision_links.csv',index=False)
display(iterative_process); display(result_links)""",
)
code(
    "INCOMPLETE-ASSUMPTION-CODE-01",
    """incomplete_analyses=pd.DataFrame([
('A01','逐次SOC実行可能性','未実装','NOT_EVALUATED','状態・energy/charging eventモデルなし','range結果はSOCを証明しない','constraint registry','INCOMPLETE'),
('A02','道路ネットワーク経路','network mode','未使用','データ unavailable記録','距離はHaversine×係数','route output','INCOMPLETE'),
('A03','古典EVRP最適化baseline','solver comparison','未実行','研究範囲外; solverなし','optimality不明','scope statement','NOT_IMPLEMENTED'),
('A04','観測需要・実配送検証','operational validation','未実行','事業データなし','外的妥当性不明','input inventory','MISSING_DATA'),
('A05','回路幅4値の再導出','paper formula substitution','未完了','page/equation/instance対応未確認','reference only','circuit evidence','SOURCE_NOT_VERIFIED'),
('A06','充電待ち・混雑・価格','operational charger model','未実行','属性・時系列なし','accessは地理のみ','limitations','NOT_IMPLEMENTED'),
('A07','削除・不採用・仮説不一致分析','repository/history review','確認不能','記録なし','研究史を創作しない','Git history limited','NOT_DOCUMENTED')],columns=['attempt_id','intended_purpose','method_attempted','outcome','reason_not_used','implication','evidence','status'])
assumption_log=pd.DataFrame([
('AS1','人口分布を配送需要位置の代理とする','実注文位置がない','population mesh; code','実注文/企業データ','空間結果が変わる',False,'RESEARCHER_ASSUMPTION'),
('AS2','地理距離×1.25で道路距離を近似','network distanceなし','BaselineAssumptions','road shortest path','time/range率が変わる',True,'RATIONALE_NOT_VERIFIED'),
('AS3','空間クラスタを車両割当の代理とする','車両別routeが必要','KMeans code','constrained assignment','route負荷が変わる',False,'RESEARCHER_ASSUMPTION'),
('AS4','最近傍順がroute負荷proxyとなる','共通訪問順が必要','route code','TSP/VRP optimum','distanceが変わる',False,'RESEARCHER_ASSUMPTION'),
('AS5','固定25 km/hで時間を近似','traffic dataを使用しない','config','observed/network time','time率が変わる',True,'RATIONALE_NOT_VERIFIED'),
('AS6','候補距離がcharging accessの一側面','利用データなし','OCM geography','availability model','access解釈が変わる',True,'RESEARCHER_ASSUMPTION'),
('AS7','選択車両仕様をbaselineに使える','比較車両が必要','vehicle snapshot','fleet distribution','range/payloadが変わる',True,'SOURCE_PARTLY_VERIFIED'),
('AS8','個別制約率が実装gapの予備情報になる','統合EVRP未実装','study logic','joint feasibility','要件優先順位が変わる',False,'RETROSPECTIVE_RECONSTRUCTION')],columns=['assumption_id','assumption','why_needed','evidence','alternative','impact_if_false','tested','status'])
incomplete_analyses.to_csv(TABLES/'incomplete_analysis_registry.csv',index=False); assumption_log.to_csv(TABLES/'researcher_assumption_log.csv',index=False)
display(incomplete_analyses); display(assumption_log)""",
)
code(
    "TIMELINE-CODE-01",
    """research_timeline=pd.DataFrame([
('Initial framing','技術指標だけで社会実装を評価できるか','slides 2–5','応用要件を先に定義','研究論理を構成','core logic','開始点'),
('Literature and metric review','規模・幅を比較できるか','slides 6–8; papers','gapを3分類','evidence extraction','gap framework','metric focusから拡張'),
('Problem-scale comparison','代表性とは何か','slide 9','規模×制約coverage','application definition','concept figure','規模単独から変更'),
('Transportation scenario definition','要件を計算可能にするには','slides 10–12; public inputs','synthetic proxyを採用','factorial design','27 structures','応用定義を具体化'),
('Synthetic data construction','比較顧客をどう作るか','mesh/code','paired population sampling','17,500 customers','customer CSV','データ作成'),
('Constraint operationalization','どの制約が未充足か','route/code','individual route flags','56,700 evaluations','constraint tables','計算へ移行'),
('Sensitivity analysis','仮定依存はどれか','parameter registry','Bootstrap/OAT','CI/sensitivity','summary tables','単一値から拡張'),
('Reproducibility audit','第三者が再計算できるか','frozen files/code','hash/regression/tests','audit notebook','validation tables','監査層を追加'),
('Current revision','なぜ分析したか追跡できるか','user requirements/artifacts','reasoning/action trail追加','registries/metadata','current notebook','説明責任を追加')],columns=['date_or_phase','question','evidence_available','decision','action','output','change_from_previous_phase'])
research_timeline.to_csv(TABLES/'chronological_research_timeline.csv',index=False); display(research_timeline)""",
)
md(
    "7. Repository and Environment Information",
    "ENVIRONMENT-01",
    protocol("record computational identity", "runtime and Git", "query versions and Git", "environment tables", "dirty state is reported, not hidden", "a recorded environment is not itself a lock"),
)
code(
    "ENVIRONMENT-CODE-01",
    """git_info=git_information(ROOT)
packages=['numpy','pandas','scipy','scikit-learn','geopandas','shapely','pyproj','matplotlib','requests','pydantic','python-pptx','nbformat','nbconvert','pytest']
versions=package_versions(packages)
environment=pd.DataFrame([{'python':sys.version,'operating_system':platform.platform(),'architecture':platform.machine(),**git_info}])
display(environment); display(versions)
environment.to_csv(TABLES/'environment.csv',index=False); versions.to_csv(TABLES/'package_versions.csv',index=False)""",
)
md(
    "8. Input Data and Provenance",
    "PROVENANCE-01",
    protocol("identify frozen inputs and verify identity", "required input files and frozen expected hashes", "recompute SHA-256 and compare", "data_provenance.csv", "MATCH requires exact hash equality", "processed snapshots do not recreate historical acquisition"),
)
code(
    "PROVENANCE-CODE-01",
    f"""expected_hashes={expected_hashes!r}
provenance_specs=[
{{'dataset_id':'source_deck','formal_name':'Research presentation','provider':'Takuma Sano','source_url':'MISSING','acquisition_date':'2026-07-13','period':'study snapshot','region':'N/A','license':'MISSING','acquisition_method':'local file','api_parameters':'N/A','crs':'N/A','raw_file':'MISSING','preprocessing_script':'N/A','processed_file':str(required_files['source_deck'][0]),'expected_sha256':expected_hashes['source_deck'],'notebook_use':'slides, references, claims','notes':'Corrected source path'}},
{{'dataset_id':'population_mesh','formal_name':'2020 Population Census Grid Square Statistics','provider':'Statistics Bureau of Japan / e-Stat','source_url':'https://www.e-stat.go.jp/gis/statmap-search?page=1&toukeiCode=00200521&type=1','acquisition_date':'recorded snapshot 2026-07-05','period':'2020 census','region':'Tokyo','license':'MISSING—verify e-Stat terms','acquisition_method':'processed local snapshot','api_parameters':'MISSING','crs':'mesh-code derived WGS84 coordinates in analysis','raw_file':'MISSING/dataless at prior audit','preprocessing_script':'05_src/data_processing/process_tokyo_public_data_inputs.py','processed_file':str(required_files['population_mesh'][0]),'expected_sha256':expected_hashes['population_mesh'],'notebook_use':'population-weighted customer generation','notes':'5,448 input rows'}},
{{'dataset_id':'charger_connections','formal_name':'Open Charge Map Tokyo clipped connections','provider':'Open Charge Map contributors','source_url':'https://www.openchargemap.org/develop/api','acquisition_date':'2026-07-05','period':'snapshot date','region':'Tokyo N03 boundary','license':'MISSING—verify OCM terms','acquisition_method':'API snapshot then spatial clip','api_parameters':'historical exact request MISSING','crs':'WGS84 latitude/longitude','raw_file':'03_data/raw/charging_infrastructure/open_charge_map/tokyo (availability varies)','preprocessing_script':'05_src/data_processing/fetch_open_charge_map_tokyo.py','processed_file':str(required_files['charger_connections'][0]),'expected_sha256':expected_hashes['charger_connections'],'notebook_use':'charger screening and nearest candidate','notes':'137 connection rows; availability not established'}},
{{'dataset_id':'depot_candidates','formal_name':'National Land Numerical Information Logistics Facilities P31 proxy','provider':'MLIT Japan','source_url':'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P31.html','acquisition_date':'snapshot recorded 2026-07-11','period':'MISSING','region':'Tokyo mainland proxy','license':'MISSING—verify MLIT terms','acquisition_method':'processed local snapshot','api_parameters':'N/A','crs':'WGS84 latitude/longitude in snapshot','raw_file':'MISSING/dataless at prior audit','preprocessing_script':'05_src/data_processing/process_mlit_logistics_hubs.py','processed_file':str(required_files['depot_candidates'][0]),'expected_sha256':expected_hashes['depot_candidates'],'notebook_use':'nearest depot proxy','notes':'440 candidates; not operator depots'}},
{{'dataset_id':'vehicle_specs','formal_name':'Public vehicle specification scenario snapshot','provider':'manufacturer/public pages','source_url':'MISSING—source URLs require verification','acquisition_date':'snapshot 2026-07-11','period':'N/A','region':'Japan','license':'MISSING','acquisition_method':'curated snapshot','api_parameters':'N/A','crs':'N/A','raw_file':'03_data/raw/vehicle_specs/ev_vehicle_specs_sources.csv','preprocessing_script':'05_src/data_processing/process_ev_vehicle_specs.py','processed_file':str(required_files['vehicle_specs'][0]),'expected_sha256':expected_hashes['vehicle_specs'],'notebook_use':'vehicle selection and constraints','notes':'source-chain incomplete'}},
]
data_provenance=provenance_table(provenance_specs)
display(data_provenance)
data_provenance.to_csv(TABLES/'data_provenance.csv',index=False)""",
)
md("9. Data Dictionary", "DATA-DICTIONARY-01", protocol("define tables/columns/units", "principal input frames", "inspect schema and attach unit/range policy", "data_dictionary.csv", "dictionary coverage tested", "descriptions are structural, not semantic proof"))
code(
    "DATA-LOAD-01",
    """population_mesh=pd.read_csv(required_files['population_mesh'][0])
charger_connections=pd.read_csv(required_files['charger_connections'][0])
depot_candidates=pd.read_csv(required_files['depot_candidates'][0])
vehicle_specs=pd.read_csv(required_files['vehicle_specs'][0])
analysis_parameters=pd.read_csv(required_files['analysis_parameters'][0])
quantum_evidence=pd.read_csv(required_files['quantum_evidence'][0])
input_tables={'input_population_mesh':population_mesh,'input_charger_connections':charger_connections,'input_depot_candidates':depot_candidates,'input_vehicle_specs':vehicle_specs,'input_analysis_parameters':analysis_parameters,'input_quantum_evidence':quantum_evidence}
data_dictionary=build_data_dictionary(input_tables)
data_dictionary.to_csv(TABLES/'data_dictionary.csv',index=False)
display(data_dictionary.head(20))""",
)
md("10. Claim–Evidence–Output Traceability Matrix", "TRACEABILITY-01", protocol("link slides, claims, inputs, functions, and outputs", "source deck", "extract 22 slides and create stable-ID mappings", "claim_evidence_traceability.csv", "22-slide completeness", "conceptual claims remain conceptual"))
code(
    "TRACEABILITY-CODE-01",
    """slides=extract_slide_text(required_files['source_deck'][0])
claim_text={1:'Study identity',5:'Requirements determine representation and resources',7:'Width cannot be interpreted from scale alone',8:'Three gaps coexist',9:'Relevance combines scale and constraint coverage',13:'Constraint results imply modeling requirements',14:'Sensitivity to assumptions',16:'Two future directions'}
traceability=[]
for row in slides.itertuples(index=False):
    claim_id=f'CLM-S{row.slide_number:02d}'
    traceability.append({'claim_id':claim_id,'slide_number':row.slide_number,'slide_element':row.slide_title,'claim_text':claim_text.get(row.slide_number,row.slide_title),'notebook_section':'Sections 1–29','notebook_cell_label':f'TRACE-S{row.slide_number:02d}','input_files':'source deck; relevant frozen inputs','processing_function':'extract_slide_text / study functions','output_table':'claim_evidence_traceability.csv','output_figure':f'figure as applicable to slide {row.slide_number}','evidence_status':'REFERENCE_ONLY' if row.slide_number==7 else 'DERIVED','reproducibility_status':'REPRODUCED' if row.slide_number in [11,12,13,14,17,18,19,20] else 'CONCEPTUAL_SYNTHESIS','limitation':'See section-specific boundary'})
claim_evidence_traceability=pd.DataFrame(traceability)
claim_evidence_traceability.to_csv(TABLES/'claim_evidence_traceability.csv',index=False)
display(claim_evidence_traceability)""",
)
md("11. Parameter Registry", "PARAMETERS-01", protocol("centralize every influential constant", "source dataclass, source files, deck settings", "classify source and uncertainty", "parameter_registry.csv", "values checked against configuration", "assumptions are not calibrated observations"))
md(
    "11.1 Parameter Epistemic Status",
    "PARAMETERS-EXPLANATION-01",
    "パラメータは観測値、公開仕様、研究者仮定、実装既定値、確認済み値からの導出値を区別する。特に道路距離係数1.25、需要5–30 kg、サービス時間5–15分、一定速度25 km/hは、観測配送データから推定されたパラメータではない。これらはモデル内部の比較可能性を確保するための分析条件であり、推定結果の外的妥当性を保証しない。\n\n"
    r"使用可能航続距離は、選択車両のカタログ航続距離116 kmに対し、初期SOC比率0.90と予備SOC比率0.20の差を適用した導出量である。すなわち、$R_{usable}=116\times(0.90-0.20)=81.2$ kmである。この計算は逐次SOCモデルではなく、全ルート距離と単一閾値を比較するための静的近似である。",
)
code(
    "PARAMETERS-CODE-01",
    """parameter_rows=[
('P01','customer_counts','25; 50; 100','customers','list','scenario','RESEARCHER_ASSUMPTION','slide/config','factorial levels','generation',True,'not calibrated'),('P02','vehicle_counts','1; 3; 5','vehicles','list','scenario','RESEARCHER_ASSUMPTION','slide/config','factorial levels','routing',True,'not calibrated'),('P03','charger_conditions','conservative; balanced; broad','condition','list','scenario','RESEARCHER_ASSUMPTION','source function','screening policies','charger evaluation',True,'attribute missingness'),('P04','n_seeds',100,'seeds','integer','randomness','RESEARCHER_ASSUMPTION','slide/config','spatial variation','all stochastic stages',False,'finite Monte Carlo'),('P05','road_distance_multiplier',1.25,'ratio','float','route','RESEARCHER_ASSUMPTION','BaselineAssumptions','straight-line proxy adjustment','distance/time/range',True,'not calibrated'),('P06','demand_min_max','5–30','kg/customer','integer range','demand','RESEARCHER_ASSUMPTION','BaselineAssumptions','synthetic demand','payload',False,'not observed'),('P07','service_time_min_max','5–15','minutes/customer','integer range','time','RESEARCHER_ASSUMPTION','BaselineAssumptions','synthetic service','operating time',True,'not observed'),('P08','travel_speed',25,'km/h','float','time','RESEARCHER_ASSUMPTION','slide/config','constant proxy speed','operating time',True,'no traffic'),('P09','usable_range',81.2,'km','float','vehicle','DERIVED','116 km × (0.90−0.20)','scenario range','range',True,'source URL incomplete'),('P10','payload_capacity',2000,'kg','float','vehicle','PUBLIC_DATA','vehicle snapshot','selected row','payload',True,'not observed fleet'),('P11','operating_limit',480,'minutes','float','time','RESEARCHER_ASSUMPTION','slide/config','daily proxy limit','operating time',True,'breaks omitted'),('P12','earth_radius',6371.0088,'km','float','geodesy','IMPLEMENTATION_DEFAULT','scenario_utils.py','Haversine mean Earth radius','distance',False,'spherical Earth'),('P13','bootstrap_iterations',1000,'iterations','integer','statistics','RESEARCHER_ASSUMPTION','slide/config','percentile CI','bootstrap',False,'Monte Carlo error'),('P14','bootstrap_seed',20260711,'integer','integer','randomness','IMPLEMENTATION_DEFAULT','analysis code','deterministic bootstrap','bootstrap',False,'none conditional on implementation')]
parameter_registry=pd.DataFrame(parameter_rows,columns=['parameter_id','parameter_name','value','unit','data_type','category','source_type','source','rationale','used_in','sensitivity_tested','uncertainty'])
parameter_registry.to_csv(TABLES/'parameter_registry.csv',index=False)
display(parameter_registry)""",
)
md("12. Scenario Design", "SCENARIO-DESIGN-01", protocol("construct the factorial design", "frozen inputs and registered parameters", "charger screening, vehicle selection, Cartesian product", "27 scenario structures", "unique IDs and factor completeness", "scenario settings are analytical assumptions"))
code(
    "SOURCE-IMPORTS-01",
    """for directory in [ROOT/'legacy/non_sumo_route_proxy_analysis/src/scenario_generation',ROOT/'legacy/non_sumo_route_proxy_analysis/src/sensitivity']:
    if str(directory) not in sys.path: sys.path.insert(0,str(directory))
from scenario_utils import BaselineAssumptions, prepare_population_mesh, generate_synthetic_customers, build_charger_condition_definitions, build_eligible_charger_candidates, select_baseline_vehicle, build_analysis_configurations, construct_route_proxies, evaluate_routes_by_condition, EARTH_RADIUS_KM
from monte_carlo_utils import build_constraint_evaluations, build_case_rates, cluster_bootstrap_constraint_summary, run_oat_sensitivity
assumptions=BaselineAssumptions()
CUSTOMER_COUNTS=[25,50,100]; VEHICLE_COUNTS=[1,3,5]; SEEDS=list(range(1,101))
definitions=build_charger_condition_definitions()
charger_candidates,charger_definitions=build_eligible_charger_candidates(charger_connections,definitions)
baseline_vehicle=select_baseline_vehicle(vehicle_specs)
scenario_configurations=build_analysis_configurations(CUSTOMER_COUNTS,VEHICLE_COUNTS,charger_definitions,baseline_vehicle,assumptions,len(SEEDS))
scenario_configurations.to_csv(SYNTH/'scenario_configurations.csv',index=False)
display(scenario_configurations.head())""",
)
code(
    "FUNCTION-REGISTRY-01",
    """tracked_functions=[prepare_population_mesh,generate_synthetic_customers,build_eligible_charger_candidates,select_baseline_vehicle,build_analysis_configurations,construct_route_proxies,evaluate_routes_by_condition,build_constraint_evaluations,build_case_rates,cluster_bootstrap_constraint_summary,run_oat_sensitivity]
functions=function_registry(tracked_functions,ROOT,git_info['git_commit'])
functions.to_csv(TABLES/'function_registry.csv',index=False)
display(functions)""",
)
md("13. Expected Record-count Derivation", "COUNT-DERIVATION-01", "Scenario structures = 3 customer sizes × 3 vehicle counts × 3 charger conditions = **27**.  \nConditional evaluations = 27 structures × 100 seeds = **2,700**.  \nSynthetic customers = (25 + 50 + 100) customers × 100 seeds = **17,500** because customer sets are shared across vehicle/charger conditions.  \nRoute-condition evaluations = (1 + 3 + 5 routes) × 3 customer sizes × 100 seeds × 3 charger conditions = **8,100**.  \nBootstrap = **1,000** seed-cluster resamples per constraint.")
code("COUNT-CODE-01", """expected_counts=pd.DataFrame([('scenario_structures',3*3*3,27),('conditional_evaluations',27*100,2700),('synthetic_customer_records',(25+50+100)*100,17500),('route_condition_evaluations',(1+3+5)*3*100*3,8100),('bootstrap_iterations',1000,1000)],columns=['quantity','derived_value','expected_value']); expected_counts['status']=np.where(expected_counts.derived_value.eq(expected_counts.expected_value),'PASS','FAIL'); display(expected_counts)""")
md("14. Synthetic Customer Generation", "METHOD-CUSTOMER-01", protocol("generate paired synthetic customer sets", "positive-population mesh cells", "weighted sampling without replacement; RNG seed = seed×100000+customer_count; demand U{5,…,30}; service U{5,…,15}", "17,500 customer rows", "probability sum, row counts, bounds, repeatability, stored comparison", "synthetic locations/demand/service are not orders"))
md(
    "14.1 Formal Sampling Procedure",
    "METHOD-CUSTOMER-FORMAL-01",
    r"人口が正であり、実装上の東京都本土緯度経度範囲を満たすメッシュ集合を $M$ とする。メッシュ $m\in M$ の人口を $P_m$ とすると、抽出確率は次式で定義される。" "\n\n"
    r"$$p_m=\frac{P_m}{\sum_{j\in M}P_j},\qquad \sum_{m\in M}p_m=1.$$" "\n\n"
    r"各顧客数 $n\in\{25,50,100\}$ とseed $s\in\{1,\ldots,100\}$ に対し、局所乱数生成器 `default_rng(100000s+n)` を生成し、$p_m$ に比例した非復元抽出で $n$ メッシュを選択する。顧客座標は選択メッシュの実装上の近似重心であり、メッシュ内の連続一様点ではない。需要 $d_i$ は離散一様分布 $U\{5,\ldots,30\}$ kg、サービス時間 $q_i$ は $U\{5,\ldots,15\}$ 分から同じ局所生成器で抽出する。" "\n\n"
    "顧客集合は `(customer_count, seed)` ごとに一度だけ生成され、車両数および充電条件の比較で共有される。この対応付けにより条件差を同一顧客集合上で比較できる一方、結果は人口分布、離散需要分布、メッシュ重心近似に条件づけられる。",
)
code(
    "CUSTOMER-GENERATE-01",
    """prepared_mesh=prepare_population_mesh(population_mesh,assumptions)
synthetic_customers,randomization_registry=generate_synthetic_customers(population_mesh,CUSTOMER_COUNTS,SEEDS,assumptions)
synthetic_customers.to_csv(SYNTH/'synthetic_customers.csv',index=False)
randomization_registry.to_csv(SYNTH/'randomization_registry.csv',index=False)
stored_customers=pd.read_csv(required_files['stored_customers'][0]); stored_customers['mesh_code']=stored_customers.mesh_code.astype(str)
customers_match,customers_match_detail=compare_frames(synthetic_customers,stored_customers)
display(synthetic_customers.head()); print(customers_match,customers_match_detail)""",
)
md("15. Depot Selection", "METHOD-DEPOT-01", protocol("select a depot proxy for each customer set", "440 P31-derived candidates", "choose candidate nearest by Haversine distance to customer-set centroid; np.nanargmin gives first positional minimum", "one depot per customer set", "valid coordinates and selected ID", "public facility proxy, not an operator depot"))
code("DEPOT-DISPLAY-01", "display(depot_candidates[['scenario_depot_id','selection_rule','limitation']].head())")
md("16. Route-proxy Construction", "METHOD-ROUTE-01", protocol("construct comparable route proxies", "synthetic customers, depot candidates, vehicle counts", "KMeans(random_state=seed,n_init=20), greedy nearest-neighbor order, depot return, Haversine ×1.25, nearest screened charger", "base routes, edges, members, 8,100 condition routes", "route count, nonnegative distances, stored comparison", "not optimized; not road-network routing; greedy O(n²) ordering per cluster"))
md(
    "16.1 Route-proxy Algorithm and Distance Definition",
    "METHOD-ROUTE-FORMAL-01",
    "各顧客集合の平均緯度経度を重心とし、その重心までのHaversine距離が最小となるP31候補をデポプロキシとして選択する。車両数 $K>1$ の場合、顧客緯度経度を `KMeans(n_clusters=K, random_state=seed, n_init=20)` で分割する。各クラスタではデポから開始し、未訪問顧客のうち現在地点からHaversine距離が最小の顧客を逐次選択し、最後にデポへ戻る。`numpy.argmin`のため同距離時は配列上で最初の候補が選ばれる。\n\n"
    r"2点 $(\phi_1,\lambda_1)$、$(\phi_2,\lambda_2)$ 間の距離は、地球半径 $R_E=6371.0088$ kmとして、" "\n\n"
    r"$$a=\sin^2\left(\frac{\Delta\phi}{2}\right)+\cos\phi_1\cos\phi_2\sin^2\left(\frac{\Delta\lambda}{2}\right),$$" "\n"
    r"$$d_H=2R_E\arcsin(\sqrt{a})$$" "\n\n"
    r"で計算する。ルート距離プロキシは、往路・顧客間移動・デポ帰着を含むHaversine距離合計に道路距離係数 $\alpha=1.25$ を乗じた $D_r=\alpha\sum_e d_{H,e}$ である。最近傍訪問順の探索はクラスタ当たり概ね $O(n_r^2)$ であり、大規模最適化手法ではない。道路の接続性、一方通行、標高、渋滞、時間窓、SOCを考慮しないため、図示された線は訪問順序の幾何学的表現に限定される。",
)
code(
    "ROUTE-GENERATE-01",
    """base_routes,route_edges,route_members=construct_route_proxies(synthetic_customers,depot_candidates,CUSTOMER_COUNTS,VEHICLE_COUNTS,SEEDS,assumptions)
route_results=evaluate_routes_by_condition(base_routes,route_members,scenario_configurations,charger_candidates,baseline_vehicle,assumptions)
for name,frame in {'base_routes':base_routes,'route_edges':route_edges,'route_members':route_members,'route_results':route_results}.items(): frame.to_csv(SYNTH/f'{name}.csv',index=False)
stored_routes=pd.read_csv(required_files['stored_routes'][0])
routes_match,routes_match_detail=compare_frames(route_results,stored_routes)
print(route_results.shape,routes_match,routes_match_detail)""",
)
code(
    "ROUTE-FIGURE-01",
    """scenario_id='C025_V03_CHG_balanced_SPEED25_T480'; selected_seed=1
sample_edges=route_edges.query('customer_count==25 and vehicle_count==3 and seed==@selected_seed')
sample_results=route_results.query('scenario_id==@scenario_id and seed==@selected_seed')
fig,ax=plt.subplots(figsize=(9,7))
for route_id,edges in sample_edges.groupby('base_route_proxy_id'):
    ordered=edges.sort_values('proxy_edge_order')
    ax.plot(np.r_[ordered.from_longitude.iloc[0],ordered.to_longitude],np.r_[ordered.from_latitude.iloc[0],ordered.to_latitude],marker='o',label=f'{route_id}: {sample_results.loc[sample_results.base_route_proxy_id.eq(route_id),"route_proxy_distance_km"].iloc[0]:.1f} km')
for row in sample_edges[sample_edges.to_node_type.eq('synthetic_customer')].itertuples(): ax.annotate(str(row.proxy_edge_order),(row.to_longitude,row.to_latitude),fontsize=7)
selected_depots=depot_candidates[depot_candidates.scenario_depot_id.isin(sample_results.depot_candidate_id)]
ax.scatter(selected_depots.longitude,selected_depots.latitude,marker='s',s=90,c='black',label='Depot proxy')
ax.scatter(charger_candidates.query('charger_condition=="balanced"').longitude,charger_candidates.query('charger_condition=="balanced"').latitude,marker='^',s=18,facecolors='none',edgecolors='gray',label='Eligible chargers')
chosen=charger_candidates[charger_candidates.charger_candidate_id.isin(sample_results.nearest_candidate_charger_id.dropna())]
ax.scatter(chosen.longitude,chosen.latitude,marker='*',s=130,c='black',label='Selected nearest chargers')
unmet=[]
for r in sample_results.itertuples(): unmet.append(f'R{r.route_index}: '+', '.join(x for x,v in [('time',r.operating_time_feasible),('range',r.range_feasible),('access',r.charger_geographically_accessible)] if v is False))
ax.set(title=f'{scenario_id}; seed={selected_seed}; '+ ' | '.join(unmet),xlabel='Longitude',ylabel='Latitude'); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(FIGURES/'representative_route_proxy.png',dpi=320); fig.savefig(FIGURES/'representative_route_proxy.svg'); plt.show()""",
)
md("17. Constraint Definitions", "METHOD-CONSTRAINT-01", protocol("define evaluation semantics", "route result columns", "map feasible/evaluated columns to numerator and denominator", "constraint_definition.csv", "NOT_EVALUATED remains missing", "geographic/range proxies do not prove EV operability"))
md(
    "17.1 Mathematical Definitions",
    "METHOD-CONSTRAINT-FORMAL-01",
    r"ルート $r$ の顧客集合を $N_r$、需要を $d_i$、サービス時間を $q_i$、距離を $D_r$ とする。積載未充足指標は $U_{payload,r}=\mathbf{1}[\sum_{i\in N_r}d_i>C]$ である。運行時間は $T_r=(D_r/v)\times60+\sum_{i\in N_r}q_i$ とし、$U_{time,r}=\mathbf{1}[T_r>T_{max}]$ とする。ここで $v=25$ km/h、$T_{max}=480$ 分であり、休憩、待機、充電イベントは含まれない。" "\n\n"
    r"航続距離指標は $U_{range,r}=\mathbf{1}[D_r>R_{usable}]$ である。充電アクセスは、ルートプロキシのいずれかのノードから条件別候補までの最近傍地理距離と閾値を比較する。充電支援航続距離と充電時間は、航続距離超過ルートの一部に対する簡略化判定であり、充電地点到着時SOC、充電曲線、待ち時間、営業時間を表現しない。逐次SOC $SOC_{k+1}=SOC_k-E(d_{k,k+1},w_k)+Q_k$ は概念上必要だが、本分析では $E$ と $Q_k$ が実装されていないため、SOCは全件 `NOT_EVALUATED` とする。",
)
code(
    "CONSTRAINT-REGISTRY-01",
    """constraint_rows=[
('C-PAYLOAD','Payload capacity','route proxy','unmet evaluated routes','all complete routes','route_total_demand_kg > payload_capacity_kg','route_total_demand_kg; payload_capacity_kg','kg','missing demand/capacity','synthetic demand','capacity signal','real loading rules'),
('C-TIME','Operating-time limit','route proxy','routes above limit','complete distance/speed/service routes','estimated_operating_time_min > operating_time_limit_min','route_proxy_distance_km; assumed_speed_kmh; route_service_time_min','minutes','missing inputs','constant speed; no charging/wait','time signal','traffic, breaks, windows'),
('C-RANGE','Range feasibility','route proxy','routes above usable range','complete route/range','route_proxy_distance_km > usable_range_km','route_proxy_distance_km; usable_range_km','km','missing inputs','fixed usable range','range signal','SOC transition, load/weather'),
('C-SOC','SOC feasibility','route sequence','NOT_EVALUATED','NOT_EVALUATED','NOT_EVALUATED','SOC state trajectory','kWh/SOC','all cases','model absent','none','all sequential SOC behavior'),
('C-ACCESS','Charging-station access','route proxy','no candidate within threshold','all condition routes','nearest_charger_distance_km > threshold','nearest_charger_distance_km; maximum_charger_access_distance_km','km','none','route-node geography','geographic access signal','availability, queue, hours'),
('C-ASSIST','Charging-assisted range','range-infeasible route','unsupported evaluable routes','range-infeasible routes','simplified two-range/access rule fails','distance; range; compatible candidate','km','range-feasible excluded','one simplified support event','support proxy','SOC/stop feasibility'),
('C-DURATION','Charging duration','evaluable assisted route','duration above limit','known positive power and accessible candidate','supplemental duration > limit','energy proxy; power; duration limit','minutes','unknown power/incompatible','constant power','duration proxy','taper, efficiency, queues')]
constraint_registry=pd.DataFrame(constraint_rows,columns=['constraint_id','constraint_name','evaluation_unit','numerator','denominator','unmet_condition','required_columns','unit','excluded_cases','assumptions','interpretation','not_captured'])
constraint_registry.to_csv(TABLES/'constraint_definitions.csv',index=False); display(constraint_registry)""",
)
md("18. Constraint Evaluation", "METHOD-EVALUATION-01", protocol("evaluate each defined constraint", "regenerated route results", "wide-to-long evaluated/feasible/unmet transformation", "56,700 constraint rows", "boolean domain and missingness rules", "unmet is conditional on model assumptions"))
code("CONSTRAINT-EVALUATE-01", """constraint_evaluations=build_constraint_evaluations(route_results); case_rates=build_case_rates(constraint_evaluations); constraint_evaluations.to_csv(SYNTH/'constraint_evaluations_long.csv',index=False); case_rates.to_csv(SYNTH/'constraint_case_rates.csv',index=False); display(constraint_evaluations.head())""")
md("19. Aggregation and Statistical Estimand", "METHOD-AGGREGATION-01", protocol("separate route/scenario/seed weighting", "long constraint evaluations", "calculate numerator, denominator, exclusions, rate by weighting method", "estimand_comparison.csv", "rates within [0,1] and numerator≤denominator", "route weighting gives greater contribution to multi-route conditions"))
md(
    "19.1 Estimand Definition",
    "METHOD-ESTIMAND-FORMAL-01",
    r"制約 $c$ が評価可能なルート集合を $\mathcal{R}_c$ とし、未充足指標を $U_{r,c}\in\{0,1\}$ とする。主結果のroute-weighted未充足率は、" "\n\n"
    r"$$\hat p_c^{route}=\frac{\sum_{r\in\mathcal{R}_c}U_{r,c}}{|\mathcal{R}_c|}$$" "\n\n"
    "である。この推定量では5車両条件が1車両条件より多くのルートを持つため、より大きな重みを持つ。scenario-weighted率は各 `(scenario_id, seed)` 内のルート率を同じ重みで平均し、seed-weighted率は各seedに属する全評価可能ルートの率を先に計算してseed間で平均する。したがって三者は同じ母数の別表現ではなく、異なる重み付け規則に基づく記述的推定量である。解釈対象は、固定された合成データ生成機構、ルートプロキシ、パラメータ集合の下で生成される分析対象ルートであり、東京都の実配送母集団ではない。",
)
code(
    "AGGREGATION-CODE-01",
    """evaluated=constraint_evaluations[constraint_evaluations.evaluated.astype(bool)].copy(); evaluated['unmet_int']=evaluated.unmet.astype(bool).astype(int)
rows=[]
for constraint,group in constraint_evaluations.groupby('constraint_name'):
    eg=group[group.evaluated.astype(bool)].copy(); route_rate=eg.unmet.astype(bool).mean() if len(eg) else np.nan
    cases=case_rates.query('constraint_name==@constraint').dropna(subset=['case_unmet_rate'])
    seed_counts=eg.assign(unmet_int=eg.unmet.astype(bool).astype(int)).groupby('seed').agg(unmet_count=('unmet_int','sum'),evaluated_count=('unmet_int','size')); seed_rates=seed_counts.unmet_count/seed_counts.evaluated_count
    for method,rate,n in [('route-weighted',route_rate,len(eg)),('scenario-weighted',cases.case_unmet_rate.mean() if len(cases) else np.nan,len(cases)),('seed-weighted',seed_rates.mean() if len(seed_rates) else np.nan,len(seed_rates))]: rows.append({'constraint_name':constraint,'weighting_method':method,'evaluated_count':n,'excluded_count':len(group)-len(eg) if method=='route-weighted' else np.nan,'unmet_count':int(eg.unmet.astype(bool).sum()) if len(eg) else 0,'unmet_rate':rate,'confidence_interval':'computed for route-weighted seed-cluster estimand in Section 20'})
estimand_comparison=pd.DataFrame(rows); estimand_comparison.to_csv(TABLES/'estimand_comparison.csv',index=False); display(estimand_comparison)""",
)
md("20. Bootstrap Procedure", "METHOD-BOOTSTRAP-01", protocol("quantify synthetic seed variation", "all route/condition evaluations grouped by seed", "sample 100 seed clusters with replacement, retain paired conditions, 1,000 iterations, percentile 2.5/97.5%, seed 20260711", "constraint summary and CI", "reproduced stored summary", "CI excludes data-source, model, parameter, and operational uncertainty"))
md(
    "20.1 Bootstrap Estimation",
    "METHOD-BOOTSTRAP-FORMAL-01",
    r"同一seedから生成された顧客集合は、車両数・充電条件を横断して共有されるため、個々のroute-condition行を独立標本として再標本化しない。反復 $b$ ごとに100個のseed IDを復元抽出し、選択されたseedに属する全条件・全ルートを保持して $\hat p_c^{(b)}$ を再計算する。95%区間は1,000個の有限な反復値の2.5および97.5パーセンタイルである。" "\n\n"
    "この区間が表すのは、凍結済み人口メッシュ、固定分布、固定パラメータ、固定ルートアルゴリズムの下でのseedクラスタ変動である。データ取得誤差、需要分布のモデル不確実性、道路距離係数の妥当性、車両仕様の誤差、充電器の実利用可能性は区間に含まれない。したがって区間幅を研究全体の不確実性と解釈してはならない。",
)
code(
    "BOOTSTRAP-CODE-01",
    """constraint_summary=cluster_bootstrap_constraint_summary(constraint_evaluations,case_rates,iterations=1000,random_seed=20260711)
constraint_summary.to_csv(SYNTH/'constraint_summary.csv',index=False)
stored_summary=pd.read_csv(required_files['stored_summary'][0]); summary_match,summary_match_detail=compare_frames(constraint_summary,stored_summary)
display(constraint_summary[['constraint_name','unmet_route_count','evaluated_route_count','route_weighted_unmet_rate','confidence_interval_lower','confidence_interval_upper']]); print(summary_match,summary_match_detail)""",
)
md("21. Sensitivity Analysis", "METHOD-SENSITIVITY-01", protocol("measure one-at-a-time response", "regenerated route results and low/base/high registry", "change one parameter while others remain fixed", "sensitivity_detail.csv", "baseline and alternative differences computed", "interactions and calibration uncertainty are not evaluated"))
md(
    "21.1 Sensitivity Estimand and Scope",
    "METHOD-SENSITIVITY-FORMAL-01",
    r"パラメータ $\theta_j$ の代替水準 $a$ に対する感度は、他のパラメータを基準値に固定した未充足率差 $\Delta_{c,j,a}=\hat p_c(\theta_j=a)-\hat p_c(\theta_j=base)$ として記録する。相対差は基準率が0でない場合のみ $\Delta_{c,j,a}/\hat p_c(base)$ とする。OATは局所的なモデル応答を可視化する設計であり、例えば速度と道路距離係数、航続距離と充電条件の相互作用を推定しない。また、代替水準の確率や現実性を評価しないため、感度の大きさは政策効果や因果効果ではない。",
)
code(
    "SENSITIVITY-CODE-01",
    """sensitivity_raw,parameter_response=run_oat_sensitivity(route_results,analysis_parameters,baseline_vehicle)
sensitivity_detail=sensitivity_raw.rename(columns={'parameter_value':'alternative_value','base_unmet_rate':'baseline_result','route_weighted_unmet_rate':'sensitivity_result','unmet_rate_change_from_base':'absolute_change'}).copy()
sensitivity_detail['baseline_value']=sensitivity_detail.parameter.map(analysis_parameters.set_index('parameter')['base'])
sensitivity_detail['unit']=sensitivity_detail.parameter.map(analysis_parameters.set_index('parameter')['unit'])
sensitivity_detail['direction_of_change']=sensitivity_detail.level
sensitivity_detail['affected_metric']=sensitivity_detail.constraint_name
sensitivity_detail['relative_change']=sensitivity_detail.absolute_change/sensitivity_detail.baseline_result.replace(0,np.nan)
sensitivity_detail['interpretation']='OAT model response under frozen synthetic data'
sensitivity_detail['limitation']='No parameter interaction or operational calibration'
sensitivity_detail.to_csv(TABLES/'sensitivity_detail.csv',index=False); display(sensitivity_detail.head(20))""",
)
md(
    "22. Related Work / Survey Method",
    "CIRCUIT-SURVEY-METHOD-01",
    r"""本節は、研究スライドとローカルに保存された一次資料を起点として、輸送・経路最適化に関する量子定式化のCircuit Widthを整理した**探索的な構造化サーベイ**である。網羅的なsystematic reviewまたはscoping reviewではない。過去の検索式、全検索結果、採択判断の同時期記録は完全には保存されていないため、検索史全体は`NOT_DOCUMENTED`である。2026-07-13の改訂では、ローカルPDF、arXiv一次記録、出版社ページを用い、既存候補文献の表題、著者、arXiv ID、DOI、本文中の`qubit`、`width`、`route`、式、表、図を対象とする一次資料の標的確認を行った。後方・前方引用検索は実施していない。

採択対象は、輸送・経路・配送問題を扱い、量子アルゴリズム、QAOA、VQA、QUBO、HOBOまたはIsing定式化を用い、Width、qubit数、またはその式と問題規模を確認できる一次資料である。輸送問題に対応しない基礎論文、ベンチマーク方法論のみの論文、二次レビュー、および対象インスタンスとWidthの対応を確認できない文献は値の統合から除外し、理由を`circuit_width_excluded_studies.csv`へ記録する。論文に記載がない制約は`Not reported`とし、`Not implemented`とは判定しない。検索・採択基準、抽出項目、可視化および品質基準は事前登録されておらず、本改訂で`DEFINED_DURING_ANALYSIS`として構造化した。""",
)
md(
    "22.1 Circuit Width Survey Summary",
    "CIRCUIT-SURVEY-SUMMARY-01",
    r"""## 1. Survey objective

本サーベイは量子輸送最適化研究の性能順位を決定せず、最小qubit数を報告した方法を優れた手法として選定しない。目的は、報告Widthがどの問題規模、定式化、符号化、制約表現に対応するかを追跡し、文献間で直接比較できる範囲を限定することである。

## 2. Scope of literature

対象は現在のローカル一次資料群に含まれるVRP、CVRP、VRPTW、HVRPおよびCVRPから分解されたTSP定式化である。現在の文献集合を量子VRP研究全体へ一般化してはならない。

## 3. Search and screening method

検索日、検索源、実際に確認した語、採択・除外基準、重複処理、未実施の引用検索、reviewerおよびmissing-information policyは`circuit_width_search_protocol.csv`に記録する。履歴がない項目は推測せず`NOT_DOCUMENTED`とする。

## 4. Definition of Circuit Width

原則としてCircuit Widthは量子回路で同時に使用されるqubit数である。ただし、logical qubits、physical qubits、problem/binary/decision variables、ancilla、slack、penalty auxiliary、embedding qubits、device qubitsを区別する。文献が単にqubitsと記載し論理・物理を区別しない場合、その不確実性を保持する。Widthは必要資源の一側面であり、小さいWidthは浅い回路、少ないゲート、高い解品質、短い実行時間、ノイズ耐性、物理qubit削減、古典優位または社会実装可能性を意味しない。

## 5. Data-extraction protocol

文献単位で問題形式、インスタンス規模、車両数、定式化、符号化、制約、Width値または式、論理・物理区分、深さ、ゲート、実機実行、出典位置、抽出方法、検証状態、reviewer、注記を保持する。概念的には $W=n_{decision}+n_{auxiliary}+n_{slack}+n_{ancilla}$ と分解できるが、実文献の式を優先し、確認不能な内訳を推測しない。

## 6. Survey results

数値、式、文献数、検証状態の集計は下のコードで詳細表から自動生成する。式のみを報告する行は、任意のインスタンスを代入して架空の数値へ変換しない。

## 7. Cross-study comparison

同じ顧客数でも、エッジ、ノード・時刻、車両添字、容量、時間窓、サブツアー除去、SOC、充電、高次項の二次化、slack、ancillaによりWidthは変化する。routes、customers、nodes、locationsの異なる規模定義を一つの回帰線で結ばない。

## 8. Relationship to application requirements

Width値が小さくても、時間窓、SOC、充電、異種車両等が表現されているとは限らない。本Notebookの制約評価は確認項目を与えるが、制約追加によるWidth増分を算出しない。

## 9. Evidence-quality assessment

Grade Aは一次資料の値・位置・問題規模・定義を追跡できる行、Bは式または一部定義を追跡できる行、Cは本文・図の値のみで定義が不十分な行、Dはスライド・二次資料転記、Eは出典または定義を確認できない行である。このGradeは研究手法の優劣ではなく抽出情報の追跡可能性を表す。

## 10. Limitations of the survey

対象文献集合は便宜的なローカルコーパスから開始しており網羅性を保証しない。独立した人手の第二reviewer、完全な検索ログ、事前登録、全式の再実装、物理qubit変換は存在しない。

## 11. Implications for the present study

本Notebookの合成輸送シナリオから文献Widthを導出していない。運用制約の未充足率とWidthとの因果的・定量的関係も推定していない。""",
)
md(
    "22.2 Circuit Width Evidence Registry",
    "REFERENCE-CIRCUIT-01",
    protocol("一次資料で追跡できるサーベイ値とスライド転記値を分離する", "local circuit_resources.csv, papers.csv, primary-source PDFs, slides", "詳細表から要約・検証・制約被覆表を生成し、未確認4値はSOURCE_NOT_VERIFIEDを維持する", "circuit_width_survey_full.csvほか指定表・図", "一意性、正値、単位、出典位置、状態分離、集計整合を自動検証する", "Widthは総計算費用、物理資源、性能順位または本Notebookシナリオの導出値ではない"),
)
code(
    "CIRCUIT-EVIDENCE-01",
    """from circuit_width_survey import build_survey_outputs
circuit_survey=build_survey_outputs(required_files['circuit_resources'][0],required_files['paper_registry'][0],TABLES,FIGURES)
circuit_width_survey_full=circuit_survey['full']; circuit_evidence=circuit_survey['registry']
circuit_width_survey_summary=circuit_survey['summary']; circuit_width_verification_summary=circuit_survey['verification']
circuit_width_constraint_coverage=circuit_survey['coverage']; circuit_width_excluded_studies=circuit_survey['excluded']
circuit_width_survey_flow=circuit_survey['flow']; circuit_width_search_protocol=circuit_survey['search_protocol']
circuit_width_survey_validation=circuit_survey['validation']
display(circuit_width_search_protocol)
display(circuit_width_survey_flow)
display(circuit_width_survey_summary)
display(circuit_width_verification_summary)
display(circuit_evidence)
display(circuit_width_survey_validation)
if circuit_width_survey_validation.status.eq('FAIL').any():
    raise AssertionError('Circuit-width survey validation failed')""",
)
md(
    "22.3 Application-Requirement Analysis",
    "CIRCUIT-APPLICATION-LINK-01",
    "文献は問題規模とWidthまたはqubit数を報告するが、その規模だけではどの運用制約を表現した値か判断できない場合がある。本Notebookは積載、運行時間、航続距離、充電アクセス、充電時間、SOC等を個別に整理し、Width証拠を解釈する際のアプリケーション要件チェック項目を提供する。制約未充足率が高い条件は、その制約をアプリケーションモデルから除外した場合に対象シナリオの運用条件を十分に表現できない可能性を示す。ただし、当該制約を量子定式化へ追加した場合の変数数、Width、Depth、ゲート数の増分は算出していない。したがって、未充足率が高いことから必要qubit数が増加すると結論してはならない。",
)
md("23. Figure and Table Generation", "OUTPUT-REGISTRY-01", protocol("classify outputs and preserve interpretation", "executed data objects", "generate figures and registry", "figures and figure_table_registry.csv", "files must exist and be nonempty", "conceptual/reference plots are not reproduced empirical results"))
code(
    "FIGURE-GENERATE-01",
    """fig,ax=plt.subplots(figsize=(9,4)); plot_data=constraint_summary.dropna(subset=['route_weighted_unmet_rate']); ax.barh(plot_data.constraint_name,plot_data.route_weighted_unmet_rate*100,facecolor='white',edgecolor='black',hatch='//'); ax.set(xlabel='Route-weighted unmet rate (%)',title='Reproduced model-conditional constraint results'); fig.tight_layout(); fig.savefig(FIGURES/'constraint_rates_reproduced.png',dpi=320); fig.savefig(FIGURES/'constraint_rates_reproduced.svg'); plt.show()
slide_refs=circuit_evidence[circuit_evidence.verification_status.eq('SOURCE_NOT_VERIFIED')]
fig,ax=plt.subplots(figsize=(8,3.5)); ax.barh(slide_refs.evidence_id,slide_refs.reported_value,facecolor='none',edgecolor='black',hatch='xx'); ax.set_xscale('log'); ax.set(xlabel='Slide-transcribed qubit value (log scale; source value not verified)',title='Unverified slide references — excluded from verified survey results'); fig.tight_layout(); fig.savefig(FIGURES/'circuit_width_reference_replotted.png',dpi=320); fig.savefig(FIGURES/'circuit_width_reference_replotted.svg'); plt.show()
output_registry=pd.DataFrame([
('FIG-ROUTE','Representative route proxy','MODEL_DERIVED','route_edges; route_results','ROUTE-FIGURE-01','matplotlib','outputs/figures/representative_route_proxy.png','Shows algorithmic route proxy','Not road route/optimum'),
('FIG-CONSTRAINT','Constraint unmet rates','REPRODUCED','constraint_summary','FIGURE-GENERATE-01','matplotlib','outputs/figures/constraint_rates_reproduced.png','Shows route-weighted synthetic rates','Not operational failures'),
('FIG-CIRCUIT-UNVERIFIED','Unverified circuit-width slide references','REFERENCE_REPLOTTED','circuit_evidence','FIGURE-GENERATE-01','matplotlib','outputs/figures/circuit_width_reference_replotted.png','Shows only SOURCE_NOT_VERIFIED slide values','Excluded from verified survey synthesis'),
('FIG-CIRCUIT-SIZE','Circuit width versus instance size','LITERATURE_DERIVED','circuit_width_survey_full','CIRCUIT-EVIDENCE-01','circuit_width_survey.plot_width_vs_size','outputs/figures/circuit_width_vs_instance_size.png','Compares values only in panels with a shared size unit','No cross-unit regression or performance ranking'),
('FIG-CIRCUIT-CONSTRAINT','Constraint reporting coverage','LITERATURE_DERIVED','circuit_width_constraint_coverage','CIRCUIT-EVIDENCE-01','circuit_width_survey.plot_constraint_coverage','outputs/figures/circuit_width_constraint_coverage.png','Distinguishes Reported, Not reported, Not applicable, and Insufficient information','Not reported is not evidence of non-implementation'),
('FIG-CIRCUIT-COMPONENTS','Circuit-width components','LITERATURE_DERIVED','circuit_width_survey_full','CIRCUIT-EVIDENCE-01','circuit_width_survey.plot_components','outputs/figures/circuit_width_components.png','Shows reported routing/capacity components for eligible HVRP rows','No inferred decomposition for other studies'),
('TABLE-PARAM','Parameter registry','DATA_DERIVED','source/config','PARAMETERS-CODE-01','pandas','outputs/tables/parameter_registry.csv','Central constants','Includes assumptions')],columns=['figure_id_or_table_id','title','classification','source_data','generating_cell','generating_function','output_path','interpretation','limitation'])
output_registry.to_csv(TABLES/'figure_table_registry.csv',index=False); display(output_registry)""",
)
md("24. Slide-result Reconciliation", "RECONCILIATION-01", protocol("calculate agreement in-notebook", "slide references and regenerated summary", "join, difference, rounding, 0.05 percentage-point tolerance", "result_reconciliation.csv", "status calculated, never prefilled", "reference agreement does not establish external validity"))
code(
    "RECONCILIATION-CODE-01",
    """reference_values=pd.DataFrame([('M-PAYLOAD','CLM-S13',13,'Payload capacity',0.0),('M-TIME','CLM-S13',13,'Operating-time limit',33.5),('M-RANGE','CLM-S13',13,'Range feasibility',64.4),('M-SOC','CLM-S13',13,'SOC feasibility',np.nan),('M-ACCESS','CLM-S13',13,'Charging-station access',10.7),('M-ASSIST','CLM-S13',13,'Charging-assisted range feasibility',33.3),('M-DURATION','CLM-S13',13,'Charging-duration feasibility',15.3)],columns=['metric_id','claim_id','slide_number','constraint_name','reference_value'])
calculated=constraint_summary[['constraint_name','route_weighted_unmet_rate']].copy(); calculated['reproduced_value']=calculated.route_weighted_unmet_rate*100
reconciliation=reference_values.merge(calculated[['constraint_name','reproduced_value']],on='constraint_name',how='left'); reconciliation['unit']='percentage points'; reconciliation['rounding_rule']='slide displayed to 1 decimal'; reconciliation['tolerance']=0.05; reconciliation['absolute_difference']=(reconciliation.reproduced_value-reconciliation.reference_value).abs(); reconciliation['relative_difference']=reconciliation.absolute_difference/reconciliation.reference_value.abs().replace(0,np.nan); reconciliation['status']=np.where(reconciliation.constraint_name.eq('SOC feasibility'),'NOT_EVALUATED',np.where(reconciliation.absolute_difference.le(reconciliation.tolerance),'PASS','FAIL')); reconciliation['reason']=np.where(reconciliation.status.eq('PASS'),'recalculated value rounds to slide value',np.where(reconciliation.status.eq('NOT_EVALUATED'),'sequential SOC model absent','outside tolerance')); reconciliation['source_cell_id']='BOOTSTRAP-CODE-01'; reconciliation.to_csv(TABLES/'result_reconciliation.csv',index=False); display(reconciliation)""",
)
md("25. Automated Validation Tests", "VALIDATION-01", protocol("execute evidence-bearing tests", "all generated/input objects", "evaluate conditions and record expected/observed/status", "validation_summary.csv", "ERROR failures downgrade final status", "test coverage is explicit and incomplete areas remain limitations"))
code(
    "VALIDATION-CODE-01",
    """tests=[]
add=lambda *args,**kwargs: tests.append(validation_row(*args,**kwargs))
add('T01','22 slides extracted',22,len(slides),len(slides)==22)
add('T02','input hashes match',0,int(data_provenance.hash_status.ne('MATCH').sum()),data_provenance.hash_status.eq('MATCH').all())
add('T03','scenario IDs unique',0,int(scenario_configurations.scenario_id.duplicated().sum()),not scenario_configurations.scenario_id.duplicated().any())
add('T04','scenario structures',27,len(scenario_configurations),len(scenario_configurations)==27)
add('T05','customer primary key unique',0,int(synthetic_customers.duplicated(['customer_configuration_id','customer_id']).sum()),not synthetic_customers.duplicated(['customer_configuration_id','customer_id']).any())
add('T06','customer rows',17500,len(synthetic_customers),len(synthetic_customers)==17500)
add('T07','all 100 seeds present',list(range(1,101)),sorted(synthetic_customers.seed.unique().tolist()),set(synthetic_customers.seed)==set(SEEDS))
add('T08','route-condition rows',8100,len(route_results),len(route_results)==8100)
route_count_check=base_routes.groupby(['customer_configuration_id','vehicle_count']).size().reset_index(name='routes'); add('T09','vehicle count equals routes per case',0,int((route_count_check.routes!=route_count_check.vehicle_count).sum()),route_count_check.routes.eq(route_count_check.vehicle_count).all())
add('T10','distances nonnegative',0,int(route_results.route_proxy_distance_km.lt(0).sum()),route_results.route_proxy_distance_km.ge(0).all())
add('T11','unmet numerator <= denominator',0,int((constraint_summary.unmet_route_count>constraint_summary.evaluated_route_count).sum()),(constraint_summary.unmet_route_count<=constraint_summary.evaluated_route_count).all())
add('T12','rates in [0,1]',0,int((~constraint_summary.route_weighted_unmet_rate.dropna().between(0,1)).sum()),constraint_summary.route_weighted_unmet_rate.dropna().between(0,1).all())
soc=constraint_summary.query('constraint_name=="SOC feasibility"').iloc[0]; add('T13','SOC not aggregated as 0%',True,bool(pd.isna(soc.route_weighted_unmet_rate) and soc.evaluated_route_count==0),pd.isna(soc.route_weighted_unmet_rate) and soc.evaluated_route_count==0)
add('T14','regenerated customers equal stored',True,customers_match,customers_match, error_message=customers_match_detail)
add('T15','regenerated routes equal stored',True,routes_match,routes_match,error_message=routes_match_detail)
add('T16','regenerated summary equal stored',True,summary_match,summary_match,error_message=summary_match_detail)
add('T17','slide reconciliation evaluated metrics pass',0,int(reconciliation.status.eq('FAIL').sum()),not reconciliation.status.eq('FAIL').any())
required_figure_names=['representative_route_proxy.png','constraint_rates_reproduced.png','circuit_width_reference_replotted.png','circuit_width_vs_instance_size.png','circuit_width_constraint_coverage.png','circuit_width_components.png']
add('T18','required output figures generated',len(required_figure_names),sum((FIGURES/name).is_file() for name in required_figure_names),all((FIGURES/name).is_file() and (FIGURES/name).stat().st_size>0 for name in required_figure_names))
add('T19','circuit-width survey validation passed',0,int(circuit_width_survey_validation.status.eq('FAIL').sum()),not circuit_width_survey_validation.status.eq('FAIL').any())
validation_summary=pd.DataFrame(tests); validation_summary.to_csv(TABLES/'validation_summary.csv',index=False); display(validation_summary)""",
)
md("26. Results", "RESULTS-01", "The regenerated route-weighted results are displayed below with numerators, denominators, and seed-cluster percentile intervals. `SOC feasibility` remains absent rather than zero. These are model-conditional synthetic estimands.\n\n再計算では、積載容量未充足率は0.0%、運行時間は33.5185%、航続距離は64.4444%、充電アクセスは10.6914%、充電支援航続距離は33.2950%、充電時間は15.3021%となり、いずれもスライドの小数第1位表示と0.05 percentage point以内で一致した。SOCは分母0であり、未充足率を算出していない。これらの一致は、凍結入力と確認済み実装からスライド集計を計算上再現できたことを示すが、仮定の妥当性や実運用への適合を示すものではない。")
code("RESULTS-CODE-01", "display(constraint_summary[['constraint_name','unmet_route_count','evaluated_route_count','route_weighted_unmet_rate','confidence_interval_lower','confidence_interval_upper','main_assumption']])")
md(
    "26.1 Circuit Width Survey Results",
    "CIRCUIT-SURVEY-RESULTS-01",
    "サーベイ結果は詳細表から自動集計する。数値Width、式のみの記録、実機を含む研究、深さ・ゲート情報、出典未確認値を分離する。少数かつ異質な文献集合であるため、分布推定、回帰、方法順位または量子VRP研究全体への一般化は行わない。Leonidas文献で確認した128-routeは8 qubits、3964-routeは13 qubitsであり、128をWidthとして扱わない。Onah文献のGolden_5行はHOBO 7,685 qubits、QUBO 202,505 qubitsであり、スライドの6,080および14,528とは別の確認済み値である。",
)
code(
    "CIRCUIT-SURVEY-RESULTS-CODE-01",
    """survey_result_counts=pd.DataFrame([
{'metric':'included studies','value':circuit_width_survey_full.paper_id.nunique()},
{'metric':'structured instance/formula records','value':len(circuit_width_survey_full)},
{'metric':'directly traceable numeric width values','value':int(circuit_width_survey_full.reported_width.notna().sum())},
{'metric':'formula-only records','value':int(circuit_width_survey_full.reported_width.isna().sum())},
{'metric':'studies with scalar instance-size field','value':circuit_width_survey_full.dropna(subset=['instance_size_value']).paper_id.nunique()},
{'metric':'studies with some reported depth information','value':circuit_width_survey_full.loc[circuit_width_survey_full.depth_reported.ne('Not reported'),'paper_id'].nunique()},
{'metric':'studies with some reported gate/volume information','value':circuit_width_survey_full.loc[circuit_width_survey_full.gate_count_reported.ne('Not reported'),'paper_id'].nunique()},
{'metric':'studies including an identified hardware execution','value':circuit_width_survey_full.loc[circuit_width_survey_full.hardware_executed,'paper_id'].nunique()},
{'metric':'slide values retained as SOURCE_NOT_VERIFIED','value':int(circuit_evidence.verification_status.eq('SOURCE_NOT_VERIFIED').sum())},
])
survey_result_counts.to_csv(TABLES/'circuit_width_survey_result_counts.csv',index=False)
display(survey_result_counts)""",
)
md("27. Interpretation", "INTERPRETATION-01", "結果は、現行仮定の下では積載量よりも距離・時間関連条件がモデル表現上の主要論点となることを示す。ただし、Payload 0%は一般の配送問題で容量制約が不要であることを意味せず、合成需要上限と2,000 kg容量の組合せが非拘束的だったことだけを意味する。Range 64.4%は実際のEV配送の失敗率ではなく、Haversine距離×1.25のルートプロキシが静的81.2 km閾値を超えた割合である。\n\nCharging access 10.7%は候補点までの地理的近接性であり、公共利用、車両互換性、稼働、混雑、営業時間を保証しない。充電支援による未充足率の変化も、充電地点到着SOCや逐次エネルギー収支を解いていないためSOC実行可能性の証拠ではない。量子定式化の観点では、時間・距離・充電を明示すれば、順序、資源状態、充電判断に対応する変数と制約が増え、qubit数だけでなく深さ、ゲート数、補助変数、ペナルティ調整に影響し得る。しかし本研究はその増分を定量化していない。Circuit widthが小さいことは、解品質、実行時間、ノイズ耐性、古典手法に対する優位性を意味しない。")
md(
    "27.1 Circuit Width as an Application-Dependent Metric",
    "CIRCUIT-DISCUSSION-01",
    "Circuit Widthは単独の普遍的尺度ではなく、問題定義、問題規模の単位、定式化、符号化、制約、補助変数、実装方式に依存する。例えば同じrouting研究でも、route変数のfull encoding、logarithmic/minimal encoding、edge-based encoding、HOBO、QUBOでは、Widthが表す変数集合と回路構造が異なる。このため、小さいWidthをもって性能、実用性、または方法の優越性を順位づけしてはならない。",
)
md(
    "27.2 Gap Between Reported Width and Operational Representation",
    "CIRCUIT-DISCUSSION-02",
    "報告Widthが小さくても、時間窓、逐次SOC、充電判断、充電曲線、異種車両、交通、driver hours等が省略または報告されていない可能性がある。`Not reported`は`Not implemented`の証拠ではないが、第三者が当該Widthと社会実装上の問題表現を対応づけるには情報不足である。したがってWidth比較には、少なくとも問題規模、制約被覆、論理・物理区分、実行値・推定値、深さ・ゲート・解品質を併記する必要がある。",
)
md(
    "27.3 Need for Constraint-aware Resource Estimation",
    "CIRCUIT-DISCUSSION-03",
    "将来研究では、アプリケーション要件を数理制約へ変換し、各制約の追加によるdecision、auxiliary、slack、ancilla変数、Width、Depth、ゲート数、物理マッピングへの影響を段階的に見積もる必要がある。本Notebookはこの資源増分を算出しておらず、制約未充足率からqubit増分を推定することもできない。",
)
md(
    "27.4 Researcher Reflection",
    "RESEARCHER-REFLECTION-01",
    "**当初想定していたこと:** 当初の内的想定を直接示す研究メモは`NOT_DOCUMENTED`である。スライドからは、問題規模と回路幅の比較だけでは応用要件を解釈できないという問題設定が確認できる。  \n\n"
    "**実際に分析して確認されたこと:** 凍結入力と現行proxyの下で、積載は非拘束的、時間・航続距離・簡略充電関連指標は一定割合で未充足となり、SOCは評価不能だった。再生成結果は保存CSVと一致した。`DIRECTLY_OBSERVABLE`  \n\n"
    "**想定と異なったこと:** 当初想定との差を特定できる同時期記録は`NOT_DOCUMENTED`である。Payload 0%を予想外だったと記述する証拠もない。  \n\n"
    "**方法上の限界として認識したこと:** スライド13–16と現在のコードは、道路ネットワーク、観測需要、時間窓、逐次SOC、充電動態、古典baseline、運用検証の不足を明示する。`CONTEMPORANEOUS_RECORD`  \n\n"
    "**次の分析で変更すべきこと:** スライド16は運用現実性とapplication-stage frameworkの2方向を提示した。本改訂では、専門家・実データ・solver・SOC・共同評価による妥当性検証を先行し、その結果を段階的定式化、古典基準、量子資源、技術段階枠組みへ入力する順序を`DEFINED_DURING_ANALYSIS`として定めた。  \n\n"
    "**現段階で維持する判断:** 結果をmodel-conditional signalとして扱い、SOCを未評価、回路幅を参照証拠、route proxyを非最適経路として明示する。`DIRECTLY_OBSERVABLE`  \n\n"
    "**現段階で保留する判断:** 実配送への一般化、EV運用可能性、量子資源増分、量子utility、Future Workの実施日程・担当者・資金・外部データ取得可能性は保留する。各FWは`PLANNED_NOT_EXECUTED`である。",
)
md("28. Limitations and Threats to Validity", "LIMITATIONS-01", "**構成概念妥当性:** 未充足率は運用要件の重要性を近似する指標であり、配送成功・失敗を直接測定しない。ルートプロキシは道路経路や最適化解ではなく、circuit widthは量子計算コスト全体を表さない。\n\n**内的妥当性:** 結果はseed、KMeans分割、最近傍デポ、greedy訪問順、道路距離係数1.25、合成需要・サービス時間、一定速度、充電器属性欠損に依存する。OATは相互作用を扱わず、Bootstrapはモデル不確実性を含まない。\n\n**外的妥当性:** 東京都の公開データ、単一車両シナリオ、人口加重顧客配置から、他地域、季節、車種、配送事業者、観測交通条件へ直接一般化できない。\n\n**再現可能性:** 凍結処理済み入力からの計算は再現できるが、生データ取得リクエスト、車両仕様URL、ライセンス情報の一部が不足する。動的APIは研究時点と現在で変化し得る。Circuit Widthサーベイは8件のローカル候補研究を対象とする探索的構造化サーベイであり、完全検索、独立第二reviewer、事前登録を欠く。一次資料から追跡できる値と式を詳細表へ分離したが、スライドの128、256、6,080、14,528は正確なページ・式・インスタンス代入を確認できず`SOURCE_NOT_VERIFIED`である。")
md(
    "28.1 Final Research Logic Summary",
    "FINAL-RESEARCH-LOGIC-01",
    "量子最適化の技術的実証が問題規模や回路幅だけでは輸送アプリケーションの運用要件表現を示さないという観察を出発点として、研究者は量子資源解釈の前に何を運用要件として定義すべきかを問うた。この問いを検討するには、規模・車両・充電条件を変えた比較可能な輸送側証拠が必要であったため、凍結公開データ、人口加重合成顧客、デポ・ルートプロキシ、個別制約評価を採用し、顧客生成、空間割当、距離・時間・充電proxy計算、seed-cluster Bootstrap、OAT感度分析を実行した。分析は制約別未充足率、信頼区間、感度表、文献証拠表を生成し、時間・航続距離等を定式化上無視できない可能性を支持したが、実配送失敗率、共同EVRP実行可能性、最適性、量子utilityを確立しなかった。本改訂は、残った2方向を同列の選択肢として放置せず、制約・実データ・古典最適化・SOC・共同評価による運用妥当性をPriority 1とし、その証拠を段階的定式化・古典基準・量子資源へ接続し、最後に技術段階枠組みへ統合する順序付きFuture Workへ変換した。この順序は`DEFINED_DURING_ANALYSIS`であり、各作業自体は`PLANNED_NOT_EXECUTED`である。",
)
md(
    "29. Future Work: Staged Validation and Resource-Evaluation Plan",
    "FUTURE-WORK-OVERVIEW-01",
    r"""Future Workは、直ちに量子計算でEVRPを解く計画ではない。現在地点は、量子性能値を評価する前に、対象問題、必要制約、測定変数、数理表現、古典基準、制約追加による問題規模を順に確定する段階である。したがって、次の順序を変更しない。

```text
制約定義の検証
    ↓
実データとの整合性評価
    ↓
数理定式化への変換
    ↓
古典計算による基準評価
    ↓
制約追加による問題規模の変化
    ↓
量子資源要件の見積り
    ↓
技術段階別の評価枠組み
```

Priority 1を完了せずにPriority 2または3の結果を実運用評価として解釈しない。古典基準FW-08を量子資源見積りFW-09より先に実施する。期間・日付は承認済み計画がないため記載しない。

| FW-ID | Unresolved problem | Concrete next action | Primary output | Completion criterion | Priority |
|---|---|---|---|---|---:|
| FW-01 | 制約の実務妥当性が未確認 | 専門家レビュー | 制約優先度表 | 定義の採否判断 | 1 |
| FW-02 | 合成データの代表性が未確認 | 実データ比較 | 代表性評価 | 保持特徴の特定 | 1 |
| FW-03 | プロキシ経路の偏りが不明 | 古典解との比較 | 経路比較表 | 偏差の定量化 | 1 |
| FW-04 | SOC未評価 | SOCモデル実装 | SOC profile | 実行不能率算出 | 1 |
| FW-05 | 制約を個別評価 | 共同充足分析 | 制約重複表 | 支配的組合せ特定 | 1 |
| FW-06 | 制約とWidth未接続 | 段階的定式化 | 変数数表 | 制約別増分算出 | 2 |
| FW-07 | サーベイ値の制約段階が未分類 | 文献段階分類 | 対応表 | 各値の段階特定 | 2 |
| FW-08 | 古典基準なし | solver benchmark | 基準結果 | 解ける規模を特定 | 2 |
| FW-09 | 独自資源見積りなし | 小規模回路生成・検算 | 資源表 | Width・Depth算出 | 2 |
| FW-10 | 技術段階と要件未統合 | 二軸stage-gate model | 段階表 | 移行基準定義 | 3 |
| FW-11 | 波及関係未評価 | 証拠区分付き確率モデル | 依存関係モデル | 感度要因特定 | 3 |

ここで示す成果物名は将来作業の完了証拠として要求するファイルであり、現時点で当該分析が実行済みであることを意味しない。全項目の状態は`PLANNED_NOT_EXECUTED`である。""",
)
for item in FUTURE_WORK_ITEMS:
    md(
        f"29.{item['sequence']} {item['fw_id']}: {item['title']}",
        f"FUTURE-WORK-{item['fw_id']}",
        future_work_markdown(item),
    )
md(
    "29.12 Future Work Roadmap and Artifact Controls",
    "FUTURE-WORK-ROADMAP-01",
    r"""| Phase | Work package | Input | Method | Output | Completion criterion | Dependency |
|---:|---|---|---|---|---|---|
| 1 | 制約の専門家評価 | 現行制約表 | 半構造化レビュー/Delphi | 改訂制約表 | 採否判断完了 | なし |
| 1 | 合成データ妥当性 | 実データ・合成データ | 分布・空間比較 | 代表性評価 | 保持特徴を特定 | データ取得 |
| 2 | 古典最適化比較 | 同一シナリオ | VRP solver比較 | 比較表 | proxy偏差を算出 | Phase 1 |
| 2 | SOCモデル | 車両・充電仕様 | 状態遷移 | SOC評価 | 充電実行可能性評価 | Phase 1 |
| 3 | 段階的定式化 | 改訂制約 | QUBO等 | 変数数表 | 制約別増分を算出 | Phase 2 |
| 3 | 古典基準・資源見積り | 段階的モデル | solver benchmark後に回路生成 | baselineとWidth/Depth | 実装値と式を照合 | 定式化・古典基準 |
| 4 | 統合枠組み・波及分析 | 全成果 | 段階モデル・確率候補比較 | 評価行列・依存モデル | 移行基準と証拠区分を定義 | Phase 3 |

現在のNotebookで完了できる制約数式、分子・分母、重み付け比較、Width証拠状態、事前定義、件数検算、proxy境界、来歴、`MISSING`表示は実装済みであり、Future Workへ先送りしない。下のコードは計画レジストリ、ロードマップ、要求成果物、現在実装済み改善、計画検証のみを生成する。専門家評価、外部データ比較、solver、SOC、回路生成の結果ファイルを空ファイルとして作成しない。""",
)
code(
    "FUTURE-WORK-PLAN-CODE-01",
    """from future_work_plan import build_future_work_outputs
future_work_outputs=build_future_work_outputs(TABLES)
future_work_registry=future_work_outputs['registry']; future_work_roadmap=future_work_outputs['roadmap']
future_work_required_artifacts=future_work_outputs['artifacts']; current_improvements=future_work_outputs['current']
future_work_validation=future_work_outputs['validation']
display(future_work_registry[['fw_id','title','priority','phase','sequence','required_artifact','dependency','status']])
display(future_work_roadmap)
display(future_work_required_artifacts)
display(current_improvements)
display(future_work_validation)
if future_work_validation.status.eq('FAIL').any():
    raise AssertionError('Future Work plan validation failed')
future_registry_rows=pd.DataFrame([
('TABLE-FW-REGISTRY','Future Work registry','PLANNING_ARTIFACT','future_work_registry','FUTURE-WORK-PLAN-CODE-01','future_work_plan.build_future_work_outputs','outputs/tables/future_work_registry.csv','Records required work, inputs, methods, completion criteria, dependencies and impact','PLANNED_NOT_EXECUTED; not research results'),
('TABLE-FW-ROADMAP','Future Work roadmap','PLANNING_ARTIFACT','future_work_roadmap','FUTURE-WORK-PLAN-CODE-01','future_work_plan.build_future_work_outputs','outputs/tables/future_work_roadmap.csv','Records phase order','No dates or durations asserted'),
('TABLE-FW-ARTIFACTS','Future Work required artifacts','PLANNING_ARTIFACT','future_work_required_artifacts','FUTURE-WORK-PLAN-CODE-01','future_work_plan.build_future_work_outputs','outputs/tables/future_work_required_artifacts.csv','Defines future completion evidence','Listed future files are not generated now'),
('TABLE-FW-VALIDATION','Future Work validation','VALIDATION','future_work_validation','FUTURE-WORK-PLAN-CODE-01','future_work_plan.validate_future_work','outputs/tables/future_work_validation.csv','Checks plan completeness and order','Does not validate feasibility of future execution'),
],columns=output_registry.columns)
output_registry=pd.concat([output_registry,future_registry_rows],ignore_index=True)
output_registry.to_csv(TABLES/'figure_table_registry.csv',index=False)""",
)
md(
    "29.13 Future Work Interpretation Boundary",
    "FUTURE-WORK-BOUNDARY-01",
    "本節は研究計画であり、専門家妥当性、合成データ代表性、最適化解、SOC実行可能性、共同実行可能性、段階的変数数、古典性能、量子資源、技術段階または遷移確率について新しい結果を報告しない。各required artifactが実データと実行コードから生成され、completion criteriaを満たし、レビュー記録が残るまで、該当する主張は更新しない。制約未充足率から必要qubit数を直接推定せず、Priority 1の妥当性検証、数理表現、古典基準を経てから量子資源を評価する。",
)
md("30. Reproducibility Status", "FINAL-STATUS-01", protocol("derive final status from evidence", "preflight, hashes, dynamic validation, future-work plan validation, known missing/not-evaluated items", "rule-based classification", "final_status", "ERROR failure yields EXECUTION_FAILED; frozen-input success cannot yield FULLY_REPRODUCIBLE", "status concerns reproducibility, not substantive validity or completion of future work"))
code(
    "FINAL-STATUS-CODE-01",
    """critical_failures=validation_summary.query('severity=="ERROR" and status=="FAIL"')
future_work_failure_count=int(future_work_validation.status.eq('FAIL').sum())
hash_failures=int(data_provenance.hash_status.ne('MATCH').sum())
if len(critical_failures) or future_work_failure_count: final_status='EXECUTION_FAILED'
elif hash_failures: final_status='PARTIALLY_REPRODUCIBLE'
else: final_status='COMPUTATIONALLY_REPRODUCIBLE_FROM_FROZEN_INPUTS'
status_reason='All computational regeneration, comparison, circuit-survey, and Future Work plan tests passed from exact frozen processed inputs; raw acquisition is incomplete, the width survey is non-exhaustive with four unverified slide references, SOC is not evaluated, and every Future Work item remains PLANNED_NOT_EXECUTED.' if final_status.startswith('COMPUTATIONALLY') else 'See failed validation/provenance rows.'
final_status_table=pd.DataFrame([{'final_status':final_status,'reason':status_reason,'critical_failure_count':len(critical_failures),'future_work_failure_count':future_work_failure_count,'hash_failure_count':hash_failures,'source_not_verified_count':int(circuit_evidence.status.eq('SOURCE_NOT_VERIFIED').sum()),'not_evaluated_items':'SOC feasibility; all Future Work empirical/solver/resource tasks'}]); display(final_status_table); final_status_table.to_csv(TABLES/'reproducibility_status.csv',index=False)""",
)
md("31. Run Manifest", "RUN-MANIFEST-01", protocol("record run identity and outputs", "runtime state, warnings, files", "hash generated artifacts and serialize JSON", "outputs/manifests/run_manifest.json", "manifest and output hashes are generated at end", "the executed notebook/HTML are added by the execution wrapper after kernel completion"))
code(
    "RUN-MANIFEST-CODE-01",
    """END_TIME=datetime.now(timezone.utc)
generated_outputs=output_manifest(OUTPUTS)
generated_outputs.to_csv(MANIFESTS/'output_file_manifest.csv',index=False)
run_manifest={'scope':'Computational Reproduction from Frozen Processed Inputs and Audit Reconstruction','final_status':final_status,'execution_start_utc':START_TIME.isoformat(),'execution_end_utc':END_TIME.isoformat(),'duration_seconds':(END_TIME-START_TIME).total_seconds(),'python_version':sys.version,'operating_system':platform.platform(),'architecture':platform.machine(),'git_commit':git_info['git_commit'],'git_dirty':git_info['git_dirty'],'input_hash_status_counts':data_provenance.hash_status.value_counts().to_dict(),'validation_status_counts':validation_summary.status.value_counts().to_dict(),'warnings':'No warnings were globally suppressed; notebook-level captured warning count not implemented','errors':critical_failures.to_dict(orient='records'),'output_manifest':'outputs/manifests/output_file_manifest.csv'}
(MANIFESTS/'run_manifest.json').write_text(json.dumps(run_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
display(pd.DataFrame([run_manifest]))""",
)

nb["cells"] = cells
localize_markdown_cells(nb)
insert_action_trails(nb)
nbf.write(nb, TARGET)
print(f"Wrote {TARGET}")
