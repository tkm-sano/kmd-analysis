"""Create a Japanese-edited copy without modifying any executable cell."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import nbformat


PROFILES = {
    "PREFLIGHT-CODE-01": ("Notebookの実行前であり，入力と環境の可用性はまだ確認されていない．", "必須ファイル，必要列，Pythonモジュール，Git情報，出力先を利用できるか．", "不足項目を個別に停止させず，一覧として検査する．", "ファイル，列，モジュール，Python，Git，出力先を検査し，事前検査表を作成する．", "各検査項目のPASSまたはFAILと，失敗理由を記録した事前検査表．", "可用性の検査であり，入力データの科学的妥当性や来歴の完全性は評価しない．", "入力の同一性と来歴を確認する．"),
    "DECISION-REGISTRY-CODE-01": ("研究上の判断を証拠状態別に記録する方針を定めた．", "主要な方法選択について，確認できる行動と記録のない理由を区別できるか．", "18件の判断を共通スキーマで整理し，理由が不明な項目には`RATIONALE_NOT_DOCUMENTED`を付す．", "Decision Point Registryを作成してCSVへ保存する．", "18件の判断，根拠，結果，後続判断を含む`decision_point_registry.csv`．", "レジストリは現存資料から追跡できる範囲を示すものであり，当時の内面的な思考を復元するものではない．", "研究質問と具体的な方法・分析行動との対応を整理する．"),
    "QUESTION-METHOD-CODE-01": ("主要な研究判断18件を，証拠状態とともに整理した．", "各研究質問が，どの入力，関数，表，解釈へつながるかを追跡できるか．", "研究質問ごとに必要な証拠，採用方法，実行内容，出力，残る不確実性を対応づける．", "Question–Method–Action Mappingを作成する．", "研究質問から出力までを対応づけた`question_method_action_mapping.csv`．", "対応関係の明示は追跡可能性を高めるが，採用方法の妥当性や代替方法に対する優位性を示さない．", "研究過程の反復と，結果から後続判断への接続を整理する．"),
    "ITERATION-DECISION-CODE-01": ("研究質問と分析行動との対応を表形式で整理した．", "現存資料から確認できる研究範囲の変化と，結果後の判断をどこまで再構成できるか．", "日付を推測せず，確認できる段階変化と事後的再構成を分けて記録する．", "反復過程表とAnalysis-to-Decision Linksを作成する．", "`iterative_research_process.csv`と`analysis_to_decision_links.csv`．", "記録のない変更理由は研究史として創作せず，`NOT_DOCUMENTED`または事後的再構成として扱う．", "未完了の分析と研究上の仮定を別のレジストリへ記録する．"),
    "INCOMPLETE-ASSUMPTION-CODE-01": ("確認できる反復過程と，結果から後続判断への接続を整理した．", "実行されなかった分析，未評価項目，研究者が置いた仮定を成功結果と分けて提示できるか．", "未完了分析と研究者仮定を別表にし，根拠と反証時の影響を記録する．", "未完了分析レジストリと仮定ログを作成する．", "`incomplete_analysis_registry.csv`と`researcher_assumption_log.csv`．", "未完了という状態は失敗率0を意味せず，仮定ログは仮定の経験的妥当性を保証しない．", "日付が確認できない段階にはphase名を用いて研究時系列を整理する．"),
    "TIMELINE-CODE-01": ("未完了分析と研究者仮定を，計算結果から分離して記録した．", "研究の進行順と，読者向けに再構成したNotebookの説明順を区別できるか．", "確認できる日付だけを使用し，不明な時点は研究段階名で示す．", "Chronological Research Timelineを作成する．", "9段階の`chronological_research_timeline.csv`．", "段階の順序は現存資料に基づく再構成を含み，当時の詳細な作業順序を確定するものではない．", "実行環境と凍結入力の来歴を確認する．"),
    "PROVENANCE-CODE-01": ("事前検査により，実行に必要なファイル，列，モジュール，出力先を検査できる状態にした．", "今回使用する凍結入力が，登録済みのファイルと同一であるか．", "各入力のSHA-256を計算し，保存済みハッシュと照合する．", "入力ファイルごとにハッシュ，一致状態，取得情報を記録する．", "`data_provenance.csv`と入力ハッシュのMATCH/MISMATCH状態．", "ハッシュ一致はファイルの同一性を示すが，データ取得方法，内容の正確性，外的妥当性は示さない．", "照合済み入力からシナリオ構成要素を読み込む．"),
    "SOURCE-IMPORTS-01": ("凍結入力について，登録済みSHA-256との一致を照合した．", "顧客数，車両数，充電条件を比較するための共通シナリオ構造を構成できるか．", "確認済みのソース関数を用い，3×3×3×100の要因構成を作る．", "充電候補と車両仕様を読み込み，シナリオ設定を列挙する．", "充電条件別候補，基準車両，2,700件のシナリオ構成を記録した`scenario_configurations.csv`．", "要因構成は研究者が定めた比較設計であり，実際の配送条件の発生頻度を表さない．", "同じ顧客数とシードで共有する合成顧客を生成する．"),
    "CUSTOMER-GENERATE-01": ("顧客数，車両数，充電条件，シードからなる2,700件のシナリオ構成を定めた．", "実顧客データを用いずに，人口分布を反映した比較用顧客集合を作れるか．", "人口メッシュを重みとする非復元抽出を行い，需要とサービス時間を離散一様分布から生成する．", "顧客数とシードの組ごとに合成顧客を生成する．", "期待件数と主キーを持つ`synthetic_customers.csv`．", "顧客位置は人口加重抽出とシードに依存し，実注文の位置，頻度，需要相関を表さない．", "顧客集合に対してデポとルートプロキシを構築する．"),
    "ROUTE-GENERATE-01": ("顧客数とシードの組ごとに，人口加重の合成顧客集合を構成した．", "最適化ソルバーを用いずに，車両数と充電条件の比較に使う共通のルート負荷を計算できるか．", "デポ候補の選択，KMeansによる割当，最近傍訪問順，Haversine距離への1.25倍補正を用いる．", "各シナリオのルート，距離，時間，充電候補への近接性を計算する．", "`route_results.csv`，ルート構成員，ルート辺の各表．", "得られる距離はKMeans，最近傍法，固定距離係数に依存し，道路ネットワークの最短経路や最適EVRP解ではない．", "ルート単位で各運用制約を個別に評価する．"),
    "CONSTRAINT-EVALUATE-01": ("各シナリオについて，ルート距離，積載量，所要時間，充電候補への近接性を計算した．", "各ルートが，定義した積載量，運行時間，航続距離，充電条件を満たすか．", "制約ごとに`evaluated`，`feasible`，`unmet`を分け，SOCは未評価のまま保持する．", "ルート結果を制約別の長形式評価表へ変換する．", "`constraint_evaluations_long.csv`と，各制約の評価可能件数・未充足件数．", "未充足は選択した閾値とルートプロキシに基づく判定であり，実際の配送失敗や全制約を同時に課した実行不能を意味しない．", "ルート加重，シナリオ加重，シード加重で集計する．"),
    "AGGREGATION-CODE-01": ("個々のルートについて，制約別の評価可否と未充足状態を記録した．", "集計単位の違いが未充足率へどのように反映されるか．", "ルート，シナリオ，シードをそれぞれ等重みとする3種類の推定対象を分ける．", "分子，分母，未充足率を集計単位別に算出する．", "`estimand_comparison.csv`と集計単位別の率．", "ルート加重では車両数が多い条件ほど寄与が大きい．異なる重み付けの率は同じ推定対象ではない．", "対応関係を保ったままシード間変動の区間を計算する．"),
    "BOOTSTRAP-CODE-01": ("制約別未充足率を，ルート加重，シナリオ加重，シード加重に分けて算出した．", "固定した生成モデルの下で，シード間変動をどの範囲として要約できるか．", "同じシードに属する条件をまとめて再標本化するシード・クラスタ・ブートストラップを1,000回行う．", "制約別のpercentile区間を算出する．", "`constraint_summary.csv`に保存される点推定値と区間下限・上限．", "区間が表すのは100個の合成反復間の変動であり，モデル選択，パラメータ，実需要，交通，充電器可用性の不確実性は含まない．", "主要仮定を一つずつ変更して結果の感度を確認する．"),
    "SENSITIVITY-CODE-01": ("シード・クラスタ・ブートストラップにより，固定モデル内の反復間変動を要約した．", "基準値の未充足率が，選択した主要パラメータにどの程度依存するか．", "他の条件を固定し，一度に一つのパラメータをlow/base/highへ変更するOAT分析を行う．", "各設定の率と基準値との差を算出する．", "`sensitivity_detail.csv`と`sensitivity_summary.csv`．", "OAT分析は設定した範囲内の単独効果を示すが，パラメータ間の相互作用や範囲外の挙動は評価しない．", "運用要件と文献由来の回路幅参照値を区別して整理する．"),
    "CIRCUIT-EVIDENCE-01": ("選択した仮定の範囲について，制約別未充足率のOAT感度を算出した．", "運用制約の分析結果と，量子VRP文献で報告された回路幅を混同せずに対応づけられるか．", "回路幅を本シナリオの計算結果ではなく，出典確認状態を伴う参照証拠として登録する．", "文献，値，定義，確認状態を証拠表へ記録する．", "`circuit_width_evidence.csv`と`SOURCE_NOT_VERIFIED`状態．", "4件の回路幅はページ，式，インスタンス代入を確認できず，本Notebookの顧客・車両シナリオから導出した値ではない．", "再計算結果をスライド掲載値と照合する．"),
    "RECONCILIATION-CODE-01": ("文献由来の回路幅4値を，未確認の参照証拠として分離した．", "再計算した未充足率が，スライドに掲載された丸め値と一致するか．", "制約名で対応づけ，percentage point差と許容差を計算する．", "スライド値と再計算値を照合する．", "`result_reconciliation.csv`に保存される差分と照合状態．", "数値の一致は同じ集計経路を再計算できたことを示すが，入力や仮定の科学的妥当性は示さない．", "件数，主キー，値，保存済みCSVとの一致を自動テストする．"),
    "VALIDATION-CODE-01": ("再計算値とスライドの丸め値について，差分と許容差を算出した．", "データ生成，ルート構築，集計，照合が，コードで定義した検査条件を満たすか．", "期待件数，主キー一意性，値域，回帰的一致など18条件を式で評価する．", "各条件の期待値，観測値，PASS/FAILを記録する．", "`validation_summary.csv`に保存される18件の検査結果．", "自動テストは実装の回帰的一貫性を検査するものであり，構成概念妥当性，最適性，外的妥当性は評価しない．", "検査結果と既知の未評価項目から再現性ラベルを決定する．"),
    "FINAL-STATUS-CODE-01": ("入力ハッシュ，生成件数，主キー，保存済み結果，スライド値について，明示した検査条件を評価した．", "得られた証拠の範囲に対応する再現性ラベルは何か．", "重大な検査失敗，ハッシュ不一致，未確認資料，未評価項目を規則に従って分類する．", "最終状態，理由，失敗件数，未評価項目を表にまとめる．", "`reproducibility_status.csv`と規則に基づく`final_status`．", "`COMPUTATIONALLY_REPRODUCIBLE_FROM_FROZEN_INPUTS`は凍結入力からの計算的一致を表し，生データ取得，経験的妥当性，運用妥当性まで含む完全再現を意味しない．", "実行環境，時刻，Git状態，出力一覧をマニフェストへ記録する．"),
}


HEADING_REPLACEMENTS = {
    "# Research Premises and Disclosure Statement": "# 研究上の前提と開示事項（Research Premises and Disclosure Statement）",
    "# Research Reasoning and Action Trail": "# 研究上の判断と分析行動の記録（Research Reasoning and Action Trail）",
    "## Research Narrative Overview": "## 研究の問題意識から分析実施までの概要（Research Narrative Overview）",
    "## Research Motivation Chain": "## 研究動機の連鎖（Research Motivation Chain）",
    "## End-to-End Research Logic Diagram": "## 研究過程の全体図（End-to-End Research Logic Diagram）",
    "# 6.1 研究判断レジストリ": "# 6.1 主要な研究判断の記録（Decision Point Registry）",
    "# 27.1 Researcher Reflection": "# 27.1 研究者による振り返り（Researcher Reflection）",
    "# 28.1 Final Research Logic Summary": "# 28.1 研究過程の論理要約（Final Research Logic Summary）",
}


CELL_REPLACEMENTS = {
    "RESEARCH-FRAMEWORK-01": """# 2.1 分析枠組みと本Notebookの成果

`CELL-ID: RESEARCH-FRAMEWORK-01`

本研究で扱う中心的な分析単位は量子アルゴリズムそのものではなく，量子資源を推定する前に定義するアプリケーション要件である．分析上は，(i) application requirements（アプリケーション要件），(ii) mathematical representation（数理表現），(iii) quantum formulation and encoding（量子定式化と符号化），(iv) quantum-resource requirements（量子資源要件），(v) feasible technology stage（実行可能な技術段階）を順に区別する．顧客数や車両数だけを問題規模とみなすと，時間，航続距離，充電，SOCを表す変数，制約，補助変数が比較から抜け落ちるため，研究間のqubit数を単純に対応づけることはできない．

本Notebookが提供する主な成果は，公開データと明示した合成仮定を用い，輸送アプリケーションの運用制約と量子資源評価との関係を追跡可能な形で整理した点にある．分析対象は，制約別のルート加重未充足率（route-weighted unmet rate），シナリオ条件による差，仮定変更に対する感度，および量子VRP文献に記載された表現・検証情報との対応である．本研究は探索的な要件整理であり，因果効果，配送事業者母集団への一般化，量子優位性を評価していない．""",
    "RESULTS-01": """# 26. 結果

`CELL-ID: RESULTS-01`

再計算したルート加重未充足率を，分子，分母，シード・クラスタ・ブートストラップによるpercentile区間とともに示す．`SOC feasibility`は0%ではなく未評価（`NOT_EVALUATED`）である．以下の値は，固定した入力，合成規則，ルートプロキシ，パラメータの下で得られた推定値である．

再計算の結果，積載容量の未充足率は0.0%，運行時間は33.5185%，航続距離は64.4444%，充電アクセスは10.6914%，充電支援航続距離は33.2950%，充電時間は15.3021%であった．各値を小数第1位に丸めると，スライド掲載値との差は0.05 percentage point以内であった．SOCは評価対象となる分母が0であり，未充足率を算出していない．この照合結果は，凍結入力と現在の実装からスライド集計値を再計算できたことを示す．入力データ，閾値，ルートプロキシの科学的妥当性や，実運用への適合性は評価していない．""",
    "INTERPRETATION-01": """# 27. 解釈

`CELL-ID: INTERPRETATION-01`

本シナリオの設定では，積載容量よりも運行時間と航続距離に関する未充足が多く観察された．ただし，積載容量が0%であったことは，一般の配送問題で容量制約が不要であることを意味しない．合成需要の上限と2,000 kgという容量の組合せでは，積載容量が未充足にならなかったという結果である．航続距離の64.4%は実際のEV配送の失敗率ではなく，Haversine距離を1.25倍したルートプロキシが，静的な81.2 kmの閾値を超えた割合である．

充電アクセスの10.7%は，分析用の充電候補までの地理的近接性に基づく．公共利用の可否，車両との互換性，稼働状況，混雑，営業時間は評価していない．充電支援条件による未充足率の変化についても，充電地点に到着した時点のSOCや逐次的なエネルギー収支を計算していないため，SOC実行可能性の証拠とはならない．時間，距離，充電を量子定式化へ追加する場合には，訪問順，資源状態，充電判断を表す変数や制約が増えると考えられるが，本Notebookはqubit数，回路深さ，ゲート数，補助変数，ペナルティ調整への増分を計算していない．文献に記載された回路幅が小さいことだけから，解品質，実行時間，ノイズ耐性，古典手法に対する優位性を判断することはできない．""",
    "RESEARCHER-REFLECTION-01": """# 27.1 研究者による振り返り（Researcher Reflection）

`CELL-ID: RESEARCHER-REFLECTION-01`

**当初の想定：** 当初の内的な想定を直接記録した研究メモは`NOT_DOCUMENTED`である．スライドから確認できるのは，問題規模と回路幅の比較だけではアプリケーション要件を解釈しにくいという問題設定である．

**分析で確認した事項：** 凍結入力と現在のルートプロキシの下では，積載容量の未充足は0件であり，運行時間，航続距離，簡略化した充電関連指標には未充足が生じた．SOCは未評価である．検査対象とした主キーおよび列について，再生成結果は保存済みCSVと一致した．`DIRECTLY_OBSERVABLE`

**想定との差：** 当初の想定と分析結果との差を判定できる同時期の記録は`NOT_DOCUMENTED`である．積載容量の未充足が0件であったことを研究者が予想外と捉えた証拠もない．

**認識している方法上の限界：** スライド13–16と現在のコードは，道路ネットワーク，観測需要，時間窓，逐次SOC，充電動態，古典最適化のbaseline，実運用による確認を分析範囲に含めていない．`CONTEMPORANEOUS_RECORD`

**次の分析で検討する変更：** スライド16は，運用上の現実性を高める方向と，application-stage framework（アプリケーションと技術段階を結ぶ枠組み）を構築する方向を提示している．優先順位は決定されていない．`CONTEMPORANEOUS_RECORD`

**維持する判断：** 未充足率を設定したモデルに依存する結果として扱い，SOCを未評価，回路幅を参照証拠，route proxyを非最適な近似経路として明記する．`DIRECTLY_OBSERVABLE`

**保留する判断：** 実配送への一般化，EV運用全体の実行可能性，量子資源の増分，quantum utility（量子的有用性），次段階の優先順位は，本Notebookから判断できないか未評価である．""",
    "LIMITATIONS-01": """# 28. 限界と妥当性への脅威

`CELL-ID: LIMITATIONS-01`

**構成概念妥当性：** 未充足率は，設定した制約とルートプロキシの関係を表す指標であり，配送の成功または失敗を直接測定していない．ルートプロキシは道路経路や最適化解ではなく，circuit width（回路幅）は量子計算に必要な資源全体を表さない．

**内的妥当性：** 結果は，シード，KMeansによる分割，最近傍のデポ選択，greedy訪問順，道路距離係数1.25，合成需要，合成サービス時間，一定速度，充電器属性の欠損処理に依存する．OAT分析はパラメータ間の相互作用を扱わず，ブートストラップ区間はモデル形式の不確実性を含まない．

**外的妥当性：** 東京都の公開データ，単一の基準車両，人口加重の顧客配置から得た結果を，他地域，季節，車種，配送事業者，観測交通条件へ直接適用することはできない．

**計算再現性：** 凍結した処理済み入力から同じ計算を再実行し，検査対象の結果と照合できる．一方，生データ取得時のリクエスト，車両仕様のURL，ライセンス情報の一部は不足している．動的APIの内容は取得時点によって変化し得る．回路幅4値は，該当ページ，式，インスタンスの代入過程を確認できないため，`SOURCE_NOT_VERIFIED`である．""",
    "FINAL-RESEARCH-LOGIC-01": """# 28.1 研究過程の論理要約（Final Research Logic Summary）

`CELL-ID: FINAL-RESEARCH-LOGIC-01`

量子最適化の技術報告に示される問題規模や回路幅だけでは，輸送アプリケーションの運用要件がどこまで表現されているかを判断しにくいという観察から，量子資源を解釈する前に定義すべき運用要件を研究課題として設定した．その検討に用いる比較可能な輸送シナリオを構成するため，公開データから固定した入力，人口加重の合成顧客，デポとルートのプロキシ，個別の制約評価を採用した．具体的には，顧客生成，空間割当，距離・時間・充電に関する近似計算，シード・クラスタ・ブートストラップ，OAT感度分析を実行するコードを整備した．分析からは，制約別未充足率，区間推定，感度表，文献証拠表が得られる．これらは，本シナリオの設定内で運行時間や航続距離を分析対象から除外しない理由を示す一方，実配送の失敗率，全制約を同時に課したEVRPの実行可能性，最適性，quantum utility（量子的有用性）を示すものではない．次段階には，運用上の現実性を高める研究と，アプリケーション要件を量子技術段階へ接続する枠組みの検討が残る．問題設定と次段階の記述はスライドに残る同時期記録（`CONTEMPORANEOUS_RECORD`）に基づき，方法間の接続は事後的再構成（`RETROSPECTIVE_RECONSTRUCTION`）である．""",
}


PHRASES = {
    "本Notebookは，": "本Notebookは，",
    "量子技術評価の前段階として，": "量子技術を評価する前段階として，",
    "凍結済み公開データ由来入力": "公開データから作成し，分析用に固定した入力データ",
    "Bootstrap": "ブートストラップ",
    "ルート加重（route-weighted） unmet rate": "ルート加重未充足率（route-weighted unmet rate）",
    "route-weighted未充足率": "ルート加重未充足率（route-weighted unmet rate）",
    "主結果はroute-weighted": "主結果はルート加重（route-weighted）",
    "route-weighted集計": "ルート加重（route-weighted）集計",
    "route-weighted，scenario-weighted，seed-weighted": "ルート加重（route-weighted），シナリオ加重（scenario-weighted），シード加重（seed-weighted）",
    "モデル条件付き合成推定量": "固定したモデルと合成条件の下で得られた推定値",
    "分析信号": "分析上の示唆",
    "検証証拠": "検査結果",
    "完全再現": "取得過程を含む再現",
    "第三者審査向け再現可能性・解釈可能性監査Notebook": "第三者審査に向けて，再現性と解釈可能性を検証するNotebook",
    "参照した正しいスライド資料": "参照したスライド資料",
    "量子資源を解釈する前段階として，合成EVRPシナリオにおいてモデル条件付きで未充足となる運用制約を同定する": "量子資源を解釈する前段階として，合成EVRPシナリオの設定下で未充足となる運用制約を評価対象として整理する",
    "本研究はEVRP最適化器の性能評価，実配送の運用評価，または量子優位性の実証を目的としない": "本研究は，EVRP最適化器の性能，実配送の運用実績，量子優位性を評価しない",
    "報告された量子資源要件を意味のある形で解釈するために，輸送固有の問題インスタンス規模と運用要件をどのように定義すべきか": "報告された量子資源要件を，輸送問題に固有のインスタンス規模および運用要件と対応づけて解釈するには，両者をどのように定義すべきか",
    "積載，時間，航続距離，充電，SOC等を明示的な評価対象へ変換する必要が生じた": "問題規模だけでは捉えにくい条件を検討するため，積載量，運行時間，航続距離，充電，SOCを評価対象として扱う方針を採用した",
    "問題規模だけでなく，問題規模だけでは捉えにくい条件": "問題規模だけでは捉えにくい条件",
    "運用要件を定式化へ含める必要性を検討する分析上の示唆": "運用要件を定式化へ含めるかを検討するための分析結果",
    "どの運用制約が明示的なモデル表現を必要とする可能性を示す分析上の示唆": "設定したモデルの下で，どの運用制約に未充足が生じるかを示す結果",
    "**Initial observation:**": "**当初の観察（Initial observation）：**",
    "**Perceived problem:**": "**認識した問題（Perceived problem）：**",
    "**Research question:**": "**研究質問（Research question）：**",
    "**Analytical need:**": "**分析上の要請（Analytical need）：**",
    "**Methodological choice:**": "**方法の選択（Methodological choice）：**",
    "**Implementation:**": "**実装（Implementation）：**",
    "**Validation:**": "**整合性の確認（Validation）：**",
    "**Result:**": "**結果（Result）：**",
    "**Interpretation:**": "**解釈（Interpretation）：**",
    "**Next decision:**": "**次の判断（Next decision）：**",
    "| Stage | Researcher observation | Concern or gap | Consequence for the study | Evidence | Status |": "| 段階 | 研究者が観察した事項 | 懸念または不足 | 本研究への反映 | 証拠 | 状態 |",
    "| Analytical need | Adopted method | Alternative method | Reason not adopted | Consequence | Status |": "| 分析上の要請 | 採用した方法 | 代替方法 | 採用しなかった理由 | 解釈への影響 | 状態 |",
    "| Premise | Current setting | Evidence | Consequence for interpretation | Status |": "| 前提 | 現在の設定 | 証拠 | 解釈への影響 | 状態 |",
    "seedから構成される": "乱数シード（seed）から構成される",
    "同じseed番号": "同じシード番号",
    "100個のseed": "100個のシード",
    "seedクラスタ": "シード・クラスタ",
    "seed固定": "乱数シード（seed）の固定",
    "100 seedクラスタ": "100個のシード・クラスタ",
    "100 seed": "100個のシード",
    "各seedに属する": "各シードに属する",
    "seed間で平均": "シード間で平均",
    "同一seedから": "同一シードから",
    "100個のseed ID": "100個のシードID",
    "選択されたseedに属する": "選択されたシードに属する",
}


def action_card(trail_id: str, code_id: str, before: bool) -> str:
    previous, question, decision, action, evidence, boundary, next_step = PROFILES[code_id]
    phase = "実行前" if before else "実行後"
    evidence_text = ("実行時に作成する証拠は，" + evidence + "である．") if before else ("実行後の確認対象は，" + evidence + "である．")
    return f"""### 分析行動の記録：{phase}

`CELL-ID: {trail_id}`  
`STATUS: RETROSPECTIVE_RECONSTRUCTION`  
`EVIDENCE CLASS: DIRECTLY_OBSERVABLE（コードと保存先）／RETROSPECTIVE_RECONSTRUCTION（判断間の接続）`

**直前までに確認した事項（Previous finding）：** {previous}

**残る疑問（Remaining question）：** {question}

**方法上の判断（Methodological decision）：** {decision}

**分析行動（Action）：** {action}

**作成・確認する証拠（Evidence produced）：** {evidence_text}

**解釈上の範囲（Interpretation boundary）：** {boundary}

**次の段階（Next step）：** {next_step}
"""


def polish(text: str) -> str:
    text = text.replace("、", "，").replace("。", "．")
    for old, new in HEADING_REPLACEMENTS.items():
        text = text.replace(old, new)
    for old, new in PHRASES.items():
        text = text.replace(old, new)
    text = text.replace("**目的:**", "**目的：**").replace("**入力:**", "**入力：**")
    text = text.replace("**処理:**", "**処理：**").replace("**出力:**", "**出力：**")
    text = text.replace("**検証:**", "**検証：**").replace("**解釈上の境界:**", "**解釈上の境界：**")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text


def revise(source: Path, destination: Path, log_path: Path) -> None:
    nb = nbformat.read(source, as_version=4)
    rows = []
    for index, cell in enumerate(nb.cells):
        if cell.cell_type != "markdown":
            continue
        cell_id = cell.metadata.get("audit_cell_id", "MISSING")
        original = cell.source
        revised = CELL_REPLACEMENTS.get(cell_id, original)
        if cell_id.startswith("TRAIL-BEFORE-") or cell_id.startswith("TRAIL-AFTER-"):
            before = cell_id.startswith("TRAIL-BEFORE-")
            code_id = cell_id.removeprefix("TRAIL-BEFORE-").removeprefix("TRAIL-AFTER-")
            revised = action_card(cell_id, code_id, before)
        revised = polish(revised)
        if revised != original:
            issue = "REDUNDANT" if cell_id.startswith("TRAIL-") else "UNNATURAL_JAPANESE"
            if cell_id in {"RESEARCH-FRAMEWORK-01", "INTERPRETATION-01", "FINAL-RESEARCH-LOGIC-01"}:
                issue = "OVERCLAIM"
            rows.append({
                "cell_index": index,
                "cell_id": cell_id,
                "original_text": original[:500].replace("\n", " "),
                "revised_text": revised[:500].replace("\n", " "),
                "issue_type": issue,
                "claim_strength_before": "Level 1–5 mixed" if issue == "OVERCLAIM" else "UNCHANGED_OR_CONTEXT_DEPENDENT",
                "claim_strength_after": "Level 0–3, matched to recorded evidence" if issue == "OVERCLAIM" else "UNCHANGED",
                "reason": "定型文を処理固有の記述へ変更" if issue == "REDUNDANT" else "自然な学術日本語，統一用語，証拠水準に対応する主張へ修正",
            })
            cell.source = revised
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, destination)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cell_index", "cell_id", "original_text", "revised_text", "issue_type", "claim_strength_before", "claim_strength_after", "reason"])
        writer.writeheader()
        writer.writerows(rows)
