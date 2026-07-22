"""Executable, auditable Future Work plan for the transport/quantum study."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


FUTURE_WORK_ITEMS = [
    {
        "fw_id": "FW-01",
        "title": "制約定義の専門家妥当性評価",
        "priority": 1,
        "phase": 1,
        "sequence": 1,
        "current_limitation": "現行制約は公開データ、文献、研究者仮定から構成され、実配送での重要性、閾値、単位、依存関係について実務専門家の検証がない。",
        "research_question": "航続距離、積載、運行時間、充電アクセス等はEV配送計画の評価項目として妥当か。不足制約と修正すべき定義は何か。",
        "required_work": "配送事業者、配車・運行管理者、EV車両管理者、充電事業者、VRP研究者、量子最適化研究者を対象に、重要度、頻度、影響、測定可能性、データ入手性、定式化可能性、依存関係、閾値妥当性を評価する。採用・修正・保留・除外と理由を記録する。",
        "data_inputs": "現行constraint_definitions.csv、parameter_registry.csv、評価票、自由記述、専門家属性。対象者数・選定基準・利益相反・同意手続は実施前に確定する。",
        "proposed_method": "半構造化レビューまたはDelphi型反復、5段階尺度と自由記述。複数評価者について中央値、四分位範囲、評価者間一致度を算出し、専門家分類別の差を記述する。",
        "comparison": "現行定義対専門家改訂案、専門家分類間、初回対合意形成後。",
        "expected_output": "expert_constraint_review.csv; constraint_priority_matrix.csv; constraint_definition_revision_log.csv; 重要度×測定可能性図; 重要度×定式化難易度図; 分類別比較; 制約依存関係図",
        "required_artifact": "expert_constraint_review.csv",
        "completion_criteria": "各制約に複数評価があり、不足制約、定義、閾値、単位をレビューし、採用・修正・保留・除外と根拠を第三者が追跡できる。",
        "dependency": "なし。ただし専門家アクセス、研究倫理・同意手続の確認が必要。",
        "impact": "現行制約を研究者定義の暫定集合から、専門家証拠付きの候補集合へ更新し、削除・追加・再定義された制約を以後のモデル入力とする。",
        "limitations": "便宜抽出、回答者数、職種偏り、合意形成圧力、企業秘密により外的妥当性が制限され得る。",
    },
    {
        "fw_id": "FW-02",
        "title": "実データによる合成シナリオの妥当性評価",
        "priority": 1,
        "phase": 1,
        "sequence": 2,
        "current_limitation": "顧客位置、需要、サービス時間が合成値であり、実配送需要の空間・業務特性をどの程度保持するか未確認である。",
        "research_question": "合成シナリオは実配送データまたは集計統計の主要な統計的・地理的特徴をどの程度保持するか。",
        "required_work": "実配送個票または集計統計を取得し、空間密度、顧客間・デポ間距離、ルート顧客数、需要、サービス時間、ルート距離、運行時間、積載率、配送面積を同一定義・単位へ整合する。個票がなければ行政統計、事業者公開値、文献分布を用いる。",
        "data_inputs": "匿名化配送記録または集計統計、データ辞書、地理境界、現行synthetic_customers.csvとroute_results、取得日・対象期間・欠損規則。",
        "proposed_method": "要約統計差、分布図、Wasserstein距離、適用可能な場合のKS統計、空間密度・自己相関、クラスタ構造比較。サンプル数と依存構造に応じ方法を選び、多重検定を安易に行わない。",
        "comparison": "合成対観測、地域別、期間別、顧客規模別。定義が一致しない外部値は別系列とする。",
        "expected_output": "synthetic_observed_comparison.csv; 分布比較図; 地理密度比較; 変数別representativeness score; synthetic-data revision recommendations",
        "required_artifact": "synthetic_observed_comparison.csv",
        "completion_criteria": "保持する特徴と保持しない特徴を変数単位で示し、比較不能項目と一般化可能範囲を明示する。",
        "dependency": "実データまたは比較可能な集計統計の取得、利用許諾、匿名化・倫理確認。",
        "impact": "未充足率を純粋な合成モデル信号としてのみ扱う現行主張を維持するか、較正範囲内の限定的代表性を付与できるかを更新する。",
        "limitations": "単一事業者・短期間データ、秘匿化、定義差、選択バイアスにより東京都配送全体を代表しない可能性がある。",
    },
    {
        "fw_id": "FW-03",
        "title": "ルートプロキシと最適化解の比較",
        "priority": 1,
        "phase": 2,
        "sequence": 3,
        "current_limitation": "KMeansと最近傍法による経路は、積載、時間、航続距離等を同時に扱う最適化解ではなく、制約率への偏りが不明である。",
        "research_question": "現行プロキシは古典VRPソルバー解に比べ、距離・時間・制約評価をどの程度過大または過小評価するか。",
        "required_work": "同一顧客・デポ・車両条件で現行法、CVRP、VRPTW、EVRP/E-VRPTWを実装し、25顧客から開始して50、100顧客へ計算可能性を確認しながら拡張する。使用ソルバー、版、停止条件、seedを固定する。",
        "data_inputs": "FW-01で改訂した制約、FW-02で評価したシナリオ、道路距離または時間行列、時間窓、車両仕様、solver設定。",
        "proposed_method": "同一インスタンスの対応比較。厳密解法または明示したheuristic/metaheuristicを用い、距離、最大距離、ルート分散、最大時間、違反、充電必要数、計算時間、optimality gap、feasible rateを測る。",
        "comparison": "KMeans＋最近傍、CVRP、VRPTW、EVRP/E-VRPTW。異なる目的関数・制約集合の結果を同一最適性指標として扱わない。",
        "expected_output": "proxy_solver_comparison.csv; route maps; constraint-rate differences; proxy bias estimate; solver runtime report",
        "required_artifact": "proxy_solver_comparison.csv",
        "completion_criteria": "各指標の対応差と不確実性を示し、プロキシが利用可能な目的と利用不能な目的を定義する。",
        "dependency": "FW-01、FW-02。道路ネットワーク入力と古典ソルバー実装。",
        "impact": "現行proxy条件付き未充足率の方向・大きさの偏りを評価し、必要なら全制約結果を最適化解ベースで再計算する。",
        "limitations": "solver timeout、定式化差、heuristic gap、道路時間データの時間帯不整合が比較を制約する。",
    },
    {
        "fw_id": "FW-04",
        "title": "SOCと充電行動を含む制約評価",
        "priority": 1,
        "phase": 2,
        "sequence": 4,
        "current_limitation": "充電候補への地理的近接性のみを評価し、区間SOC、充電出力・時間・待ち・迂回・互換性を扱わない。SOCはNOT_EVALUATEDである。",
        "research_question": "逐次SOCと充電行動を導入すると、静的航続距離および充電アクセス判定はどの程度変化するか。",
        "required_work": "初期・最低・上限SOC、距離当たり消費、積載影響、充電器出力、充電時間、迂回距離、営業時間、利用可能性、互換性を区間単位で定義し、SOC_j=SOC_i-E_ij+C_jをコードと一致させる。",
        "data_inputs": "FW-01の制約定義、FW-03の経路、車両電池・消費仕様、充電器位置・出力・接続規格・営業時間、可能なら稼働・待ちデータ。",
        "proposed_method": "区間状態遷移シミュレーションと、必要に応じた充電停止スケジューリング。単純近接判定をbaselineとし、パラメータ感度と欠損属性シナリオを分離する。",
        "comparison": "現行静的range/access proxy対SOC逐次モデル、充電条件別、車両・積載・初期SOC別。",
        "expected_output": "route_soc_profiles.csv; charging-stop schedules; SOC infeasibility rate; charging-time distribution; detour-distance distribution; current proxyとの比較",
        "required_artifact": "route_soc_profiles.csv",
        "completion_criteria": "全区間でエネルギー収支を追跡し、分母を定義したSOC実行不能率を算出し、近接性とSOC実行可能性の差を定量化する。",
        "dependency": "FW-01、FW-03。車両・充電器仕様と道路経路が必要。",
        "impact": "SOCをNOT_EVALUATEDからモデル条件付き評価へ更新し、静的range/accessをEV実行可能性とみなさない現行境界を定量的比較へ拡張する。",
        "limitations": "劣化、気温、勾配、交通、充電曲線、待ち・故障のデータ不足により実運用SOCを完全再現しない。",
    },
    {
        "fw_id": "FW-05",
        "title": "制約間の共同実行可能性評価",
        "priority": 1,
        "phase": 2,
        "sequence": 5,
        "current_limitation": "制約を個別に評価し、全制約を同時に満たす割合、重複、条件付き関係を示していない。個別率は加算できない。",
        "research_question": "積載、時間、航続距離、充電、SOCを同時に考えると、どの制約組合せがシナリオの実行可能性を制限するか。",
        "required_work": "共通の評価可能ルート集合と制約ベクトルを定義し、全充足、1件以上未充足、単独・同時未充足、組合せ頻度、条件付き確率を算出する。欠損・NOT_EVALUATEDを0へ変換しない。",
        "data_inputs": "FW-01の採択制約、FW-03の比較可能経路、FW-04のSOC評価、制約ごとの評価可能性と分母定義。",
        "proposed_method": "joint indicator、intersection frequency、UpSet表現、constraint-overlap matrix、条件付き確率。seed・scenario対応を保持した不確実性評価を行う。",
        "comparison": "個別未充足率対共同実行可能性、顧客数・車両数・充電条件別、proxy対最適化解。",
        "expected_output": "joint_constraint_feasibility.csv; constraint-overlap matrix; UpSet plot; conditional-probability table; scenario bottleneck table",
        "required_artifact": "joint_constraint_feasibility.csv",
        "completion_criteria": "個別評価との差を示し、シナリオ別の支配的組合せを分母・欠損規則とともに特定する。",
        "dependency": "FW-01、FW-03、FW-04。FW-04未完了時はSOCを除く暫定分析と明記する。",
        "impact": "制約別signalに限定した現行主張を、定義された制約集合についての共同モデル実行可能性へ拡張できるかを判断する。",
        "limitations": "共同率もモデル条件付きであり、未観測制約、パラメータ相関、最適化方針を含まなければ実配送成功率ではない。",
    },
    {
        "fw_id": "FW-06",
        "title": "制約の数理定式化と変数数への変換",
        "priority": 2,
        "phase": 3,
        "sequence": 6,
        "current_limitation": "運用制約の未充足性は評価したが、制約を最適化モデルへ追加した際のdecision、auxiliary、slack、ancilla変数とWidth増分を算出していない。",
        "research_question": "M0基本経路からM9複数デポまで制約を段階追加すると、変数、制約、QUBO項、高次項、ancilla、推定Widthはどう増えるか。",
        "required_work": "M0経路、M1複数車両、M2容量、M3運行時間、M4時間窓、M5航続距離、M6充電選択、M7 SOC、M8異種車両、M9複数デポを定式化し、変数型、添字集合、制約式、slack/ancilla、二次化を登録する。",
        "data_inputs": "FW-01〜FW-05で確定した要件、問題規模、定式化文献、QUBO/Ising/制約付きモデル仕様、符号化規則。",
        "proposed_method": "段階別数理モデルと小規模列挙による変数・制約件数検算。複数符号化は別系列とし、式とコード生成数を照合する。",
        "comparison": "M0〜M9、顧客25/50/100、QUBO・HOBO・制約付きモデル、符号化方式別。",
        "expected_output": "constraint_to_formulation_registry.csv; stagewise_variable_count.csv; stagewise_constraint_count.csv; stagewise_width_estimate.csv; 増分図",
        "required_artifact": "stagewise_variable_count.csv",
        "completion_criteria": "各制約の数理式、実装変数、資源増分、仮定、検算結果を追跡できる。",
        "dependency": "FW-01〜FW-05。実務妥当性未確認の制約を実運用モデルとして解釈しない。",
        "impact": "制約未充足率とWidthを直接結ばず、アプリケーション要件→数理表現→変数増分という中間層を新設する。",
        "limitations": "定式化・符号化の選択に依存し、変数数が計算性能や物理qubit数を単独で決定しない。",
    },
    {
        "fw_id": "FW-07",
        "title": "Widthサーベイと本研究の定式化の接続",
        "priority": 2,
        "phase": 3,
        "sequence": 7,
        "current_limitation": "文献Widthと本Notebookの制約評価は並列であり、文献値がM0〜M9のどの表現段階に対応するか未分類である。",
        "research_question": "各文献Widthは、どの問題規模、制約集合、変数構成、実行・推定状態に対応し、本研究のどのモデル段階へ配置できるか。",
        "required_work": "サーベイ文献の車両、容量、時間窓、range、charging、SOC、異種車両、複数デポ、subtour、auxiliary、reported/executed/estimated Widthを再コードし、FW-06のM0〜M9へ根拠付き配置する。",
        "data_inputs": "circuit_width_survey_full.csv、constraint coverage、一次資料、FW-06の定式化レジストリ。",
        "proposed_method": "二者独立コーディングが可能なら一致確認を行い、Reported、Not reported、Not applicable、Insufficient informationを区別したstage mappingを作る。複数段階にまたがる研究は単一ラベルへ強制しない。",
        "comparison": "文献間、M0〜M9、reported/executed/estimated、logical/physical区分。",
        "expected_output": "literature_model_stage_mapping.csv; constraint-coverage matrix; width-by-stage plot; missing-constraint summary; comparability assessment",
        "required_artifact": "literature_model_stage_mapping.csv",
        "completion_criteria": "各Widthについて、規模だけでなく表現した制約段階、証拠状態、比較可能範囲を説明できる。",
        "dependency": "FW-06。一次資料の不足はSOURCE_NOT_VERIFIEDまたはInsufficient informationとして保持する。",
        "impact": "現在の文献別Width一覧を、アプリケーション要件段階付きの比較証拠へ更新する。",
        "limitations": "文献の報告不足、定式化差、実装非公開により段階配置が不確実または複数候補となり得る。",
    },
    {
        "fw_id": "FW-08",
        "title": "古典計算による段階的基準評価",
        "priority": 2,
        "phase": 3,
        "sequence": 8,
        "current_limitation": "M0〜M9を古典ソルバーでどの規模・品質・時間まで解けるかという基準性能がない。",
        "research_question": "各制約段階は古典計算でどの規模まで、どのfeasible rate、gap、時間、メモリで解けるか。",
        "required_work": "M0〜M9を顧客25、50、100で実行し、必要なら小規模から増加する。solver、hardware、thread、時間制限、seed、presolve、停止条件、失敗理由を固定・記録する。",
        "data_inputs": "FW-03のsolver環境、FW-06の段階モデル、同一インスタンス、計算環境情報、比較可能な古典heuristicと厳密解法。",
        "proposed_method": "対応インスタンスのbenchmark。feasible rate、objective、gap、wall time、memory、timeout、model build time、violationを記録し、censored timeoutを成功値と混同しない。",
        "comparison": "M0〜M9、25/50/100顧客、solver/algorithm、厳密解法対heuristic。",
        "expected_output": "classical_baseline_results.csv; scale-runtime plot; stage-runtime plot; feasible-scale frontier; timeout/failure log",
        "required_artifact": "classical_baseline_results.csv",
        "completion_criteria": "各段階の古典基準と、指定時間・品質条件下で解ける規模、timeout/失敗範囲を明示する。",
        "dependency": "FW-03、FW-06。FW-09より前に完了する。",
        "impact": "量子資源を論じる比較基準を新設し、古典比較なしにutilityまたはadvantageを示唆しない。",
        "limitations": "solver tuning、hardware、license、時間制限に依存し、古典計算全体の限界を証明しない。",
    },
    {
        "fw_id": "FW-09",
        "title": "量子資源見積り",
        "priority": 2,
        "phase": 3,
        "sequence": 9,
        "current_limitation": "現行Widthは文献参照であり、本研究のM0〜M9を回路またはアニーリング表現へ変換した独自資源見積りではない。",
        "research_question": "段階モデルを選定した量子方式へ実装すると、logical Width、ancilla込みWidth、Depth、2-qubit gates、shots、iterations、総回路評価はどの程度か。",
        "required_work": "小規模インスタンスで回路または埋込みを生成し、数理式のWidthと実装値を照合する。方式別にコンパイル条件、connectivity、gate set、optimizer、shotsを記録し、規模増加を仮定付きで外挿する。",
        "data_inputs": "FW-06モデル、FW-07比較定義、FW-08古典baseline、量子SDK/annealer仕様、backend・transpiler設定、誤り訂正仮定を用いる場合の根拠。",
        "proposed_method": "QAOA、VQA、量子アニーリングを別系列でresource accountingし、理論式対生成回路を小規模で検算する。推定、simulator、実機を区別する。",
        "comparison": "M0〜M9、規模、encoding、algorithm、logical/physical、estimated/executed、およびFW-08古典条件。",
        "expected_output": "quantum_resource_estimates.csv; theoretical-versus-implemented width table; depth/gate/shot curves; assumption registry",
        "required_artifact": "quantum_resource_estimates.csv",
        "completion_criteria": "モデルから回路への変換、Width式と実装値、Width以外の資源、推定対実行、古典比較条件を明示する。",
        "dependency": "FW-06、FW-07、FW-08。Priority 1未完了時は実運用資源評価と表現しない。",
        "impact": "文献参照だけの現行量子側証拠を、本研究の段階モデルに条件づけた資源見積りへ拡張する。",
        "limitations": "SDK・compiler・hardware世代、回路最適化、誤り訂正仮定、optimizer収束に強く依存し、外挿は実行可能性を保証しない。",
    },
    {
        "fw_id": "FW-10",
        "title": "技術段階別評価モデルの構築",
        "priority": 3,
        "phase": 4,
        "sequence": 10,
        "current_limitation": "量子技術段階と、輸送アプリケーションが要求する問題規模・制約集合を共通の移行基準で統合していない。",
        "research_question": "T0定式化からT7継続利用、A0基本経路からA9実データ統合の各組合せで、何を満たせば次段階へ進めるか。",
        "required_work": "T0〜T7とA0〜A9を定義し、各セルの評価可能規模、入力、資源、古典比較、成功基準、証拠水準、未解決制約、移行条件を登録する。空欄を推測値で埋めない。",
        "data_inputs": "FW-01〜FW-09の制約、代表性、solver、定式化、サーベイ、古典・量子資源結果、技術成熟度文献、専門家レビュー。",
        "proposed_method": "二軸stage-gate matrixとevidence-level registry。移行条件を測定可能な判定規則として定義し、感度・技術更新時の版管理を行う。",
        "comparison": "T0〜T7、A0〜A9、古典/量子、evidence level、実行可能/未評価/不十分。",
        "expected_output": "technology_application_stage_matrix.csv; stage transition criteria; evidence-level registry; evaluation roadmap; gap visualization",
        "required_artifact": "technology_application_stage_matrix.csv",
        "completion_criteria": "各セルの規模・制約・証拠・成功条件を定義し、次段階への移行判定を第三者が再適用できる。",
        "dependency": "FW-07、FW-08、FW-09。Priority 1・2の証拠を統合する。",
        "impact": "二方向だった次段階を、運用現実性の検証結果を入力として技術段階枠組みへ接続する一つの順序付き計画へ更新する。",
        "limitations": "技術進歩と要件変化により陳腐化し、stage境界には規範的判断が残る。継続的版更新が必要である。",
    },
    {
        "fw_id": "FW-11",
        "title": "制約充足確率の段階的波及分析",
        "priority": 3,
        "phase": 4,
        "sequence": 11,
        "current_limitation": "制約率や技術性能の改善が後続段階の共同実行可能性へどう波及するかを評価していない。",
        "research_question": "P(F|T_s,A_k)を定義したとき、どの制約・技術要因の改善が共同実行可能性へ最も影響し、その不確実性は何に由来するか。",
        "required_work": "F、T_s、A_k、依存辺を定義し、観測推定、シミュレーション、専門家判断、未知を別状態で登録する。根拠のない確率を設定せず、更新規則と欠損処理を明示する。",
        "data_inputs": "FW-05共同評価、FW-10段階行列、実データ・simulation・専門家確率、出典・不確実性・更新日。",
        "proposed_method": "決定木、ベイズネットワーク、Monte Carloの候補を依存表現、データ量、識別可能性で比較し、選択理由を記録する。感度と不確実性分解を行う。",
        "comparison": "model候補、T/A段階、観測/シミュレーション/専門家/未知、代替依存構造。",
        "expected_output": "stage_transition_probability_model.csv; dependency graph; conditional probability registry; transition simulation; sensitivity ranking; uncertainty decomposition",
        "required_artifact": "stage_transition_probability_model.csv",
        "completion_criteria": "確率の根拠区分と依存仮定を保持し、主要感度要因と不確実性を再計算可能な形で示す。",
        "dependency": "FW-05、FW-10。確率証拠不足時はモデル構造のみを提示し数値をMISSINGとする。",
        "impact": "個別未充足率の記述から、証拠区分付きの段階遷移シナリオ分析へ拡張する。ただし因果効果または実運用成功確率とは表現しない。",
        "limitations": "依存構造の誤指定、少数専門家、識別不能確率、未知の技術変化により結果が仮定支配となり得る。",
    },
]


ROADMAP = [
    (1, "制約の専門家評価", "現行制約表", "半構造化レビュー/Delphi", "改訂制約表", "採否判断完了", "なし"),
    (1, "合成データ妥当性", "実データ・合成データ", "分布・空間比較", "代表性評価", "保持特徴を特定", "データ取得"),
    (2, "古典最適化比較", "同一シナリオ", "VRP solver比較", "比較表", "proxy偏差を算出", "Phase 1"),
    (2, "SOCモデル", "車両・充電仕様", "状態遷移", "SOC評価", "充電実行可能性評価", "Phase 1"),
    (3, "段階的定式化", "改訂制約", "QUBO等", "変数数表", "制約別増分を算出", "Phase 2"),
    (3, "古典基準・資源見積り", "段階的モデル", "solver benchmark後に回路生成", "baselineとWidth/Depth", "実装値と式を照合", "定式化、古典基準"),
    (4, "統合枠組み・波及分析", "全成果", "段階モデル・確率候補比較", "評価行列・依存モデル", "移行基準と証拠区分を定義", "Phase 3"),
]


CURRENT_IMPROVEMENTS = [
    ("制約定義と数式", "IMPLEMENTED", "Sections 17/17.1 and constraint_definitions.csv"),
    ("分子・分母・除外規則", "IMPLEMENTED", "Sections 19/19.1"),
    ("route/scenario/seed-weighted比較", "IMPLEMENTED", "estimand_comparison.csv"),
    ("Width証拠状態と一次資料分離", "IMPLEMENTED", "circuit_width_survey_full.csv and circuit_width_evidence.csv"),
    ("事前定義・post-hoc状態", "IMPLEMENTED", "Research Premises and survey protocol"),
    ("出力件数と回帰検算", "IMPLEMENTED", "validation_summary.csv"),
    ("proxyと実運用の区別", "IMPLEMENTED", "Premises, Methods, Interpretation"),
    ("データ来歴・MISSING表示", "IMPLEMENTED", "data_provenance.csv and missing-information policies"),
]


def future_work_frame() -> pd.DataFrame:
    frame = pd.DataFrame(FUTURE_WORK_ITEMS)
    frame["status"] = "PLANNED_NOT_EXECUTED"
    frame["claim_boundary"] = "Future work plan only; no result or completed artifact is claimed"
    return frame


def roadmap_frame() -> pd.DataFrame:
    return pd.DataFrame(ROADMAP, columns=["phase", "work_package", "input", "method", "output", "completion_criterion", "dependency"])


def artifact_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["fw_id", "required_artifact", "status"]].rename(columns={"fw_id": "FW-ID", "required_artifact": "Required artifact"})


def current_improvements_frame() -> pd.DataFrame:
    return pd.DataFrame(CURRENT_IMPROVEMENTS, columns=["improvement", "current_status", "evidence"])


def validate_future_work(frame: pd.DataFrame, artifacts: pd.DataFrame) -> pd.DataFrame:
    tests = []
    add = lambda test_id, description, passed, observed: tests.append({"test_id": test_id, "description": description, "status": "PASS" if passed else "FAIL", "observed": str(observed)})
    required = ["current_limitation", "research_question", "required_work", "data_inputs", "proposed_method", "comparison", "expected_output", "completion_criteria", "dependency", "impact", "limitations"]
    add("FWV01", "FW IDs are unique", frame.fw_id.is_unique, int(frame.fw_id.duplicated().sum()))
    add("FWV02", "exactly FW-01 through FW-11 are present", set(frame.fw_id) == {f"FW-{i:02d}" for i in range(1, 12)}, sorted(frame.fw_id.tolist()))
    add("FWV03", "all required planning fields are populated", frame[required].apply(lambda col: col.astype(str).str.strip().ne("").all()).all(), int(frame[required].isna().sum().sum()))
    add("FWV04", "priority mapping follows 1-5/6-9/10-11", frame.set_index("fw_id").priority.to_dict() == {**{f"FW-{i:02d}": 1 for i in range(1, 6)}, **{f"FW-{i:02d}": 2 for i in range(6, 10)}, **{f"FW-{i:02d}": 3 for i in range(10, 12)}}, frame.groupby("priority").size().to_dict())
    add("FWV05", "classical baseline precedes quantum resource estimation", int(frame.loc[frame.fw_id.eq("FW-08"), "sequence"].iloc[0]) < int(frame.loc[frame.fw_id.eq("FW-09"), "sequence"].iloc[0]), frame.set_index("fw_id").loc[["FW-08", "FW-09"], "sequence"].to_dict())
    add("FWV06", "validity work precedes resource/framework work", frame.loc[frame.priority.eq(1), "sequence"].max() < frame.loc[frame.priority.eq(2), "sequence"].min() < frame.loc[frame.priority.eq(3), "sequence"].min(), frame.groupby("priority").sequence.agg(["min", "max"]).to_dict())
    add("FWV07", "one required artifact is registered per FW", len(artifacts) == 11 and artifacts["FW-ID"].is_unique, len(artifacts))
    add("FWV08", "all work remains explicitly unexecuted", frame.status.eq("PLANNED_NOT_EXECUTED").all(), frame.status.value_counts().to_dict())
    prohibited = ["実用化を実現する", "量子優位性を証明する", "社会実装可能性を確立する", "最適な枠組みを構築する"]
    joined = " ".join(frame.astype(str).to_numpy().ravel())
    add("FWV09", "prohibited overclaim phrases are absent", not any(term in joined for term in prohibited), [term for term in prohibited if term in joined])
    add("FWV10", "every item states impact on present study", frame.impact.str.len().gt(20).all(), int(frame.impact.str.len().le(20).sum()))
    add("FWV11", "every item states anticipated limitations", frame.limitations.str.len().gt(20).all(), int(frame.limitations.str.len().le(20).sum()))
    return pd.DataFrame(tests)


def build_future_work_outputs(tables: Path) -> dict[str, pd.DataFrame]:
    frame = future_work_frame()
    roadmap = roadmap_frame()
    artifacts = artifact_frame(frame)
    current = current_improvements_frame()
    validation = validate_future_work(frame, artifacts)
    frame.to_csv(tables / "future_work_registry.csv", index=False)
    roadmap.to_csv(tables / "future_work_roadmap.csv", index=False)
    artifacts.to_csv(tables / "future_work_required_artifacts.csv", index=False)
    current.to_csv(tables / "current_improvements_not_deferred.csv", index=False)
    validation.to_csv(tables / "future_work_validation.csv", index=False)
    return {"registry": frame, "roadmap": roadmap, "artifacts": artifacts, "current": current, "validation": validation}


def future_work_markdown(item: dict) -> str:
    return f"""#### Current limitation

{item['current_limitation']}

#### Research question

{item['research_question']}

#### Required work

{item['required_work']}

#### Data and inputs

{item['data_inputs']}

#### Proposed method

{item['proposed_method']}

#### Comparison

{item['comparison']}

#### Expected output

{item['expected_output']}

#### Completion criteria

{item['completion_criteria']}

#### Dependency

{item['dependency']}

#### Impact on the present study

{item['impact']}

#### Anticipated limitations

{item['limitations']}

**Priority:** {item['priority']}　**Phase:** {item['phase']}　**Status:** `PLANNED_NOT_EXECUTED`"""
