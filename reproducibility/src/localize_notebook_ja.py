"""Japanese localization for explanatory Markdown in the audit notebook."""
from __future__ import annotations


HEADINGS = {
    "SUBMISSION-INFO-01": "1. 表題および提出情報",
    "RESEARCH-QUESTION-01": "2. 研究質問と目的",
    "RESEARCH-FRAMEWORK-01": "2.1 分析枠組みと研究上の貢献",
    "SCOPE-01": "3. 再現範囲",
    "BOUNDARY-01": "4. 解釈上の境界",
    "EXECUTION-01": "5. 実行手順",
    "PREFLIGHT-01": "6. 事前検査",
    "ENVIRONMENT-01": "7. リポジトリおよび実行環境情報",
    "PROVENANCE-01": "8. 入力データと来歴",
    "DATA-DICTIONARY-01": "9. データ辞書",
    "TRACEABILITY-01": "10. 主張・証拠・出力トレーサビリティ表",
    "PARAMETERS-01": "11. パラメータレジストリ",
    "PARAMETERS-EXPLANATION-01": "11.1 パラメータの認識論的位置づけ",
    "SCENARIO-DESIGN-01": "12. シナリオ設計",
    "COUNT-DERIVATION-01": "13. 期待レコード件数の導出",
    "METHOD-CUSTOMER-01": "14. 合成顧客の生成",
    "METHOD-CUSTOMER-FORMAL-01": "14.1 標本抽出手続きの形式化",
    "METHOD-DEPOT-01": "15. デポ選択",
    "METHOD-ROUTE-01": "16. ルートプロキシの構築",
    "METHOD-ROUTE-FORMAL-01": "16.1 ルートプロキシのアルゴリズムと距離定義",
    "METHOD-CONSTRAINT-01": "17. 制約の定義",
    "METHOD-CONSTRAINT-FORMAL-01": "17.1 制約の数理的定義",
    "METHOD-EVALUATION-01": "18. 制約評価",
    "METHOD-AGGREGATION-01": "19. 集計方法と統計的推定対象",
    "METHOD-ESTIMAND-FORMAL-01": "19.1 推定対象の定義",
    "METHOD-BOOTSTRAP-01": "20. ブートストラップ手続き",
    "METHOD-BOOTSTRAP-FORMAL-01": "20.1 ブートストラップ推定",
    "METHOD-SENSITIVITY-01": "21. 感度分析",
    "METHOD-SENSITIVITY-FORMAL-01": "21.1 感度推定量と分析範囲",
    "REFERENCE-CIRCUIT-01": "22.2 Circuit Width Evidence Registry",
    "OUTPUT-REGISTRY-01": "23. 図表の生成",
    "RECONCILIATION-01": "24. スライド結果との照合",
    "VALIDATION-01": "25. 自動検証テスト",
    "RESULTS-01": "26. 結果",
    "INTERPRETATION-01": "27. 解釈",
    "LIMITATIONS-01": "28. 限界と妥当性への脅威",
    "FUTURE-WORK-OVERVIEW-01": "29. Future Work: 段階的検証・資源評価計画",
    "FUTURE-WORK-ROADMAP-01": "29.12 Future Work Roadmap and Artifact Controls",
    "FUTURE-WORK-BOUNDARY-01": "29.13 Future Work Interpretation Boundary",
    "FINAL-STATUS-01": "30. 再現可能性の判定",
    "RUN-MANIFEST-01": "31. 実行マニフェスト",
}


def protocol(purpose: str, inputs: str, processing: str, outputs: str, validation: str, boundary: str) -> str:
    return (
        f"**目的:** {purpose}  \n"
        f"**入力:** {inputs}  \n"
        f"**処理:** {processing}  \n"
        f"**出力:** {outputs}  \n"
        f"**検証:** {validation}  \n"
        f"**解釈上の境界:** {boundary}"
    )


BODIES = {
    "SUBMISSION-INFO-01": "**Toward Evaluating Problem Scale in Quantum Computing: Focusing on Operational Constraints in Transportation**  \n著者：82535190 Takuma Sano  \n提出物の種別：第三者審査向け再現可能性・解釈可能性監査Notebook  \n参照した正しいスライド資料：`0712_MDR2_v2_enriched_appendix.pptx`。",
    "RESEARCH-QUESTION-01": "**研究質問：** 報告された量子資源要件を意味のある形で解釈するために、輸送固有の問題インスタンス規模と運用要件をどのように定義すべきか。\n\n本計算の目的は、量子資源を解釈する前段階として、合成EVRPシナリオにおいてモデル条件付きで未充足となる運用制約を同定することである。本研究はEVRP最適化器の性能評価、実配送の運用評価、または量子優位性の実証を目的としない。",
    "SCOPE-01": "**実行モード：`凍結済み処理入力からの計算再現および監査再構成`**\n\n| 再現対象 | 再現方法 | 使用入力 | 状態 | 完全再現でない理由 | 第三者が確認できる証拠 |\n|---|---|---|---|---|---|\n| 合成顧客 | 原実装関数を再実行 | 凍結済みe-Stat処理データ | `REPRODUCED` | e-Stat生データ取得を再実行しない | 行単位比較 |\n| ルートと制約 | 原実装関数を再実行 | 凍結済み処理入力 | `REPRODUCED` | 道路ネットワーク最適化ではない | 行単位比較 |\n| 集計・Bootstrap・OAT | 再生成結果から再計算 | 再生成ルート評価 | `REPRODUCED` | モデルとパラメータを固定 | 動的テスト |\n| 公開データ取得 | 来歴を監査 | ローカルスナップショットと取得コード | `DERIVED` | 歴史的リクエストが完全保存されていない | ハッシュと処理コード |\n| 回路幅参照値 | 参照値として再描画 | スライドとローカル文献 | `REFERENCE_ONLY` | 厳密な導出を確認できない | 証拠レジストリ |\n| SOC実行可能性 | 評価なし | 該当なし | `NOT_EVALUATED` | 逐次SOCモデルが存在しない | 制約レジストリ |",
    "BOUNDARY-01": "> 本Notebookで算出する未充足率は、合成シナリオおよびルートプロキシの仮定に条件づけられた分析指標である。実際の配送失敗率、最適化されたEVRP解の実行可能率、または観測された事業運用実績を表すものではない。\n\nルートプロキシは道路ネットワーク上の経路でも最適化解でもない。航続距離判定はEV運用可能性全体を表さない。`NOT_EVALUATED`を0として扱わない。",
    "EXECUTION-01": "`reproducibility/`ディレクトリでPython 3.11環境を作成し、`requirements-lock.txt`をインストールした後、Notebookを先頭セルから順に実行する。生成物はすべて`outputs/`以下へ保存し、凍結済み入力ファイルは読み取り専用として扱う。",
    "PREFLIGHT-01": protocol("最初の不足項目だけで停止せず、依存関係と入力の不足をすべて収集する", "リポジトリ判定用ファイル、必須ファイル・列、Pythonモジュール", "ルート探索、存在・スキーマ・import・Git・書込み検査", "事前検査表", "ERRORレベルの検査がすべて合格すること", "ファイルの可用性は、来歴や科学的妥当性を証明しない"),
    "ENVIRONMENT-01": protocol("計算環境の同一性を記録する", "実行時情報とGit情報", "Python・パッケージ・OS・Git状態を取得する", "環境情報表", "未コミット変更を隠さず記録する", "環境情報の記録だけでは依存関係の固定にならない"),
    "PROVENANCE-01": protocol("凍結入力を特定し、ファイル同一性を検証する", "必須入力ファイルと凍結時の期待SHA-256", "SHA-256を再計算し期待値と比較する", "`data_provenance.csv`", "完全一致の場合だけ`MATCH`とする", "処理済みスナップショットから歴史的な取得処理全体は再現できない"),
    "DATA-DICTIONARY-01": protocol("主要テーブルの列、型、単位、欠損規則を定義する", "主要入力テーブル", "実際のスキーマを調査し単位・値域規則を付与する", "`data_dictionary.csv`", "辞書が主要列を網羅することを確認する", "構造的説明はデータ内容の意味的妥当性を証明しない"),
    "TRACEABILITY-01": protocol("スライド、主張、入力、処理、出力を対応付ける", "参照スライド資料", "22枚のスライドを抽出し安定したセルIDに対応付ける", "`claim_evidence_traceability.csv`", "22枚すべてが含まれること", "概念的主張は計算結果と区別する"),
    "PARAMETERS-01": protocol("結果へ影響する定数を一元管理する", "ソースコードのdataclass、入力ファイル、スライド設定", "出典種別、根拠、不確実性を分類する", "`parameter_registry.csv`", "実行設定との整合性を確認する", "研究者仮定は観測データで較正された値ではない"),
    "SCENARIO-DESIGN-01": protocol("要因計画に基づくシナリオを構築する", "凍結入力と登録済みパラメータ", "充電候補選別、車両選択、要因の直積を作成する", "27シナリオ構造", "IDの一意性と全要因組合せを検査する", "シナリオ設定は分析上の仮定である"),
    "COUNT-DERIVATION-01": "シナリオ構造数 ＝ 顧客数3水準 × 車両数3水準 × 充電条件3水準 ＝ **27**。  \n条件別評価数 ＝ 27構造 × 100 seed ＝ **2,700**。  \n合成顧客レコード数 ＝ (25 + 50 + 100)顧客 × 100 seed ＝ **17,500**。顧客集合を車両数・充電条件間で共有するため、これらの要因を再度乗じない。  \n条件・ルート評価数 ＝ (1 + 3 + 5ルート) × 顧客数3水準 × 100 seed × 充電条件3水準 ＝ **8,100**。  \nBootstrap反復数 ＝ 制約ごとに**1,000回**。",
    "METHOD-CUSTOMER-01": protocol("対応付けられた合成顧客集合を生成する", "人口が正の人口メッシュ", "人口加重・非復元抽出、seed規則、需要5–30 kg、サービス時間5–15分", "17,500顧客行", "確率和、件数、座標範囲、再実行一致、保存済み結果との一致", "合成位置・需要・サービス時間は観測注文ではない"),
    "METHOD-DEPOT-01": protocol("顧客集合ごとにデポプロキシを選ぶ", "P31由来の440候補", "顧客集合重心とのHaversine距離が最小の候補を選択する。同距離の場合は配列上で最初の候補を採用する", "顧客集合ごとに1デポ", "座標と選択IDを検査する", "公開物流施設の代理点であり実事業者のデポではない"),
    "METHOD-ROUTE-01": protocol("比較可能なルートプロキシを構築する", "合成顧客、デポ候補、車両数", "seed固定KMeans、greedy最近傍訪問、デポ帰着、Haversine距離×1.25、最近傍充電候補探索", "基本ルート・辺・構成員・8,100条件別ルート", "ルート件数、距離非負、保存済み結果との一致", "最適化解でも道路経路でもなく、クラスタ内訪問順の計算量は概ねO(n²)"),
    "METHOD-CONSTRAINT-01": protocol("各制約の評価意味を定義する", "ルート結果の各列", "feasible・evaluated列を分子・分母へ対応付ける", "`constraint_definitions.csv`", "`NOT_EVALUATED`を欠損のまま保持する", "地理的アクセスや静的航続距離はEV運用可能性全体を証明しない"),
    "METHOD-EVALUATION-01": protocol("定義済み制約をルート単位で評価する", "再生成したルート結果", "横持ち結果をevaluated・feasible・unmetの縦持ち形式へ変換する", "56,700制約評価行", "真偽値の値域と欠損規則を検査する", "未充足判定は現在のモデル仮定に条件づけられる"),
    "METHOD-AGGREGATION-01": protocol("route・scenario・seedの重み付けを分離する", "縦持ち制約評価", "分子、分母、除外数、重み付け別の率を計算する", "`estimand_comparison.csv`", "分子が分母以下であり率が0–1に入ること", "route-weighted集計では複数ルート条件の寄与が大きい"),
    "METHOD-BOOTSTRAP-01": protocol("合成seedによる変動を定量化する", "seedでクラスタ化した全条件・全ルート", "100 seedクラスタを復元抽出し対応関係を保持する。1,000反復、percentile 2.5/97.5%、seed 20260711", "制約集計と信頼区間", "保存済み集計との一致", "区間はデータ取得・モデル・パラメータ・実運用の不確実性を含まない"),
    "METHOD-SENSITIVITY-01": protocol("一度に一つのパラメータを変えた応答を測る", "再生成ルートとlow・base・highレジストリ", "他のパラメータを固定して対象パラメータだけを変更する", "`sensitivity_detail.csv`", "基準値との差と相対差を計算する", "パラメータ間相互作用や較正不確実性は評価しない"),
    "REFERENCE-CIRCUIT-01": protocol("文献参照値と再現計算値を分離する", "スライド7・22およびローカル一次資料", "定義と証拠状態を登録し、計算再現を主張しない", "`circuit_width_evidence.csv`", "出典箇所未確認の値を`SOURCE_NOT_VERIFIED`とする", "回路幅・qubit数は計算費用全体や物理資源量と同一ではない"),
    "OUTPUT-REGISTRY-01": protocol("図表を分類し解釈情報を保存する", "実行済みデータオブジェクト", "図表を生成し出力レジストリへ登録する", "図および`figure_table_registry.csv`", "ファイルが存在し空でないこと", "概念図・参照値再描画を再現済み実証結果として扱わない"),
    "RECONCILIATION-01": protocol("Notebook内でスライド値との一致を計算する", "スライド参照値と再生成集計", "結合、絶対差・相対差、丸め、0.05 percentage point許容差を計算する", "`result_reconciliation.csv`", "状態を事前入力せず計算条件から判定する", "参照値との一致は外的妥当性を証明しない"),
    "VALIDATION-01": protocol("実際の条件式に基づく検証を実行する", "全入力・生成オブジェクト", "期待値と観測値を比較し状態とエラーを記録する", "`validation_summary.csv`", "ERRORレベルの失敗を最終判定へ反映する", "明示されたテスト範囲外の妥当性は保証しない"),
    "RESULTS-01": "再生成したroute-weighted結果を、分子、分母、seedクラスタpercentile区間とともに示す。`SOC feasibility`は0ではなく未評価として保持する。以下はモデル条件付き合成推定量である。\n\n再計算では、積載容量未充足率は0.0%、運行時間は33.5185%、航続距離は64.4444%、充電アクセスは10.6914%、充電支援航続距離は33.2950%、充電時間は15.3021%となり、いずれもスライドの小数第1位表示と0.05 percentage point以内で一致した。SOCは分母0であり、未充足率を算出していない。この一致は凍結入力と確認済み実装からスライド集計を計算上再現できたことを示すが、仮定の妥当性や実運用への適合を示さない。",
    "FINAL-STATUS-01": protocol("証拠に基づき最終的な再現可能性状態を導出する", "事前検査、ハッシュ、動的検証、欠損・未評価項目", "規則に基づき状態を分類する", "最終状態", "ERROR失敗時は`EXECUTION_FAILED`とし、凍結入力からの再現を`FULLY_REPRODUCIBLE`としない", "判定対象は再現可能性であり研究結果の実質的妥当性ではない"),
    "RUN-MANIFEST-01": protocol("実行識別情報と出力を記録する", "実行状態、警告、生成ファイル", "生成物のハッシュを計算しJSONへ保存する", "`outputs/manifests/run_manifest.json`", "実行終了時にマニフェストと出力ハッシュを生成する", "実行済みNotebookとHTMLのハッシュはカーネル終了後に実行ラッパーが追加する"),
}


def localize_markdown_cells(notebook) -> None:
    """Translate explanatory Markdown while preserving code and stable IDs."""
    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            continue
        cell_id = cell.get("metadata", {}).get("audit_cell_id")
        if not cell_id:
            continue
        current = cell.source
        first_line, _, remainder = current.partition("\n")
        heading = HEADINGS.get(cell_id, first_line.lstrip("# "))
        marker = f"`CELL-ID: {cell_id}`"
        if cell_id in BODIES:
            body = BODIES[cell_id]
        else:
            body = remainder.split(marker, 1)[-1].lstrip("\n") if marker in remainder else remainder.lstrip("\n")
        cell.source = f"# {heading}\n\n{marker}\n\n{body}"
