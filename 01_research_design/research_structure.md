<a id="research-structure"></a>

# 研究構成

<a id="2026-09-27-study-b完了method-scaleはblocked"></a>

## 2026-09-27 調査B完了：手法比較の規模は実行不可

[最小構成の電気自動車配送経路問題量子資源静的監査](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)を完了。現行直接表現表現はn5/m1でも34変数・471coupler・raw256GiBで、凍結計算方式上限256メビバイトを超える。METHOD_COMPARISON_SCALE_AUTHORITY=実行不可、選定nなし、S0_QUANTUM_PROTOCOL_RESOURCE_GATE=実行不可。n3/n4は検証・pilot/referenceのまま。MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、想定条件評価の規模は一部固定済み、本実験の第0段階は未許可。

次は物理問題を変えない代替encoding/decompositionの静的比較。調査Aは別途未実行。凍結予備試験/科学成果物/台帳を保持し、新規最適化・Aer・量子近似最適化アルゴリズム・最適化処理評価・回路・回測定は全て0。以下の評価規模再整理段落は調査B前の履歴であり、手法状態と次作業は本段落が優先する。

<a id="2026-09-27評価規模再整理small-nは検証pilot-scope"></a>

## 2026-09-27（評価規模再整理）：小規模は検証・予備試験の範囲

[評価規模正本](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存予備試験 第0段階の物理・比較取り決め・成果物は不変。以下の旧S0_SCALE_AUTHORITY=固定済みはsmall-入力 範囲の値であり、本番評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / 本番のS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01の無作為・集積型親標本の入れ子構成の先頭部分、n=3,4,5,8,10,15,20（3/4診断、5以上本番候補）。最終二規模は未選定で、同じnを強制しない。量子現行直接表現表現はn5/m1からメモリー下限で不適合、想定条件側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→調査A（条件を統制した 古典計算 scaling/Battery 関連性）と調査B（最小構成の電気自動車配送経路問題 QUBO/resource監査）→二規模選定→本実験の第0段階 正本更新。調査設計は固定したが今回は実行していない。本実験の第0段階は未許可、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

<a id="2026-09-27s0物理条件共通contractの部分freeze"></a>

## 2026-09-27：第0段階物理条件・共通取り決めの部分固定

[第0段階 正本](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件取り決め / 評価指標を固定済み、S0_QUANTUM_PROTOCOLを実行不可、S0_BASELINE_AUTHORITYを一部固定済みとした。想定条件側は既存n4・最大3台の構造予備試験、手法比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

現行はmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全単純な配送経路の消費上限がusable18 kWhを下回るため、両層で充電設備訪問判断を除外し充電無効を固定した。実車充電出力は未解決のまま、この限定第0段階の阻害要因にはしない。経済正本は別拡張として未着手。

次作業は凍結第0段階条件に対する最小構成の電気自動車配送経路問題 Quantum/QUBO 符号化・同値性・資源監査。旧Exact/MILP 出典は保存Git treeでハッシュ値一致を確認済みだが、将来実行前の復元・実行器接続は別途必要。S0/全最適化/量子実行は未着手。本段落と第0段階正本が、以下の旧日付の第0段階未定義・経済必須記述に優先する。

<a id="2026-09-26minimal-evrp以降の研究順序改訂"></a>

## 2026-09-26：最小構成の電気自動車配送経路問題以降の研究順序改訂

時間窓付き配送経路問題結果と最小構成の電気自動車配送経路問題設計正本は固定済みである。既存経路電気自動車回帰および制御10kWでの充電あり検証は合格、最小構成の電気自動車配送経路問題 古典計算 モデルもN002 WIDEの検証範囲で固定済みである。10kWはCONTROLLED_VALIDATION_CONDITIONであり実車充電性能ではない。実車の実効充電性能はUNRESOLVED/DEFERRED、第0段階は未実行である。

今後の順序・状態の正本は[研究段階ロードマップ](RESEARCH_STAGE_ROADMAP.md)である。電池根拠・条件固定 → 第0段階 → 同一条件の[Classical/Quantum EVRP比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md) → 第0段階評価/固定 → [劣化・技術向上条件の比較](BATTERY_SCENARIO_COMPARISON_PLAN.md) → 電池差と手法差の分離 → 感度分析 → [量子化学/材料R&Dと二系統の統合](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)へ進む。容量/健全度/技術容量・感度設計正本は固定済みである。直近の次milestoneは完全な第0段階条件正本の定義であり、第0段階実行ではない。実車充電出力は未解決である。

以下の日付付き全体計画・状況は各時点の記録を保持する。最小構成の電気自動車配送経路問題以降の順序・状態が異なる場合は上記全体の研究段階計画を優先する。過去の配送需要充足率目的・未配送許容等を現在の凍結最小構成の電気自動車配送経路問題へ導入しない。凍結科学成果物を変更せず、本改訂で新しい科学実行は行わない。

## 2026-09-09の設計更新

2026-09-09時点の全体設計では[B2C配送パイプライン採択記録](../RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を採択した。最小構成の電気自動車配送経路問題以降の現行順序は冒頭の全体の研究段階計画に従う。当時の全体構想は住宅向け宅配を主対象に、39,956候補地点から層化・重み付き非復元抽出し、顧客数nと複数乱数の種を実験パラメータにする。主需要単位は配送件数、基準は単一配送拠点、主指標はDFR_orders。OR-Toolsと制約なし二値二次最適化→量子近似最適化アルゴリズム→Qiskit Aerは同一問題例・共通必須制約を使用し、独立検証器を通して比較する。技術想定条件では顧客・需要・時間窓・道路条件を原則固定する。

最小構成の電気自動車配送経路問題以降の順序・状態・比較条件は2026-09-26 全体の研究段階計画を優先する。既存成果物の生成・受入事実は保持し、今後の設計採択を実装完了とは扱わない。

<a id="current-reduced-quantum-method-branch-2026-09-10"></a>

## 現在の縮約量子手法の系統 (2026-09-10)

現在の量子側実装は完全な電気自動車配送経路問題ではなく、固定配送拠点・単一車両の訪問順序を条件を統制した部分問題とする。
顧客-only `n x n` 位置 制約なし二値二次最適化はR20 定式化 判定基準、R21 厳密 制約なし二値二次最適化 検証、R22 厳密
制約なし二値二次最適化-to-Ising 検証を通過した。R23 Aer/QAOA 基盤は実装の動作確認まで完了し、
正式な予備試験前の `READY_FOR_PILOT` である。正式 量子近似最適化アルゴリズム 性能 結果はまだ存在しない。

この分岐で得るalgorithm/simulator 根拠は、後に容量、時間窓、battery/SOC、充電、
到達可能性、車両群の制約を備えた全体 EVRP/Hayate評価へ戻して解釈する。Aer simulationはソフトウェア
根拠であり、将来の量子処理装置 実行時間や量子優位性を直接示さない。

<a id="motivation-and-research-question"></a>

## 研究の背景と問い

交通分野での応用評価には、小規模な経路定式化だけでなく、問題例、運用制約、検証方式、量子計算資源の根拠を結び付ける必要がある。本研究では、交通に関係する問題規模と制約が量子経路研究でどのように表現され、その根拠が東京の合成電気自動車配送問題とどう対応するかを問う。

<a id="literature-review-and-circuit-width-extraction"></a>

## 文献調査と回路幅の抽出

文献調査では、問題例、数理定式化、量子符号化、報告された回路幅、記載があれば深さの定義、実機・シミュレーターの別、評価状態を記録する。量子近似最適化の層数、試行状態の層数、コンパイル後の深さ、論理量子ビット数、物理資源見積りを区別する。応用志向の性能評価、量子計算の有用性、実用的な量子優位性に関する文献は、導入実績の主張ではなく方法論の背景として使う。

<a id="application-side-requirements"></a>

## 応用側の要件

比較では、要件を表現しているかどうかと、その評価・検証方法を区別する。現在の要件区分は、規模、積載量、稼働時間、航続距離、充電率、充電設備への接続、根拠の種類、古典計算との比較である。

<a id="synthetic-tokyo-evrp-analysis"></a>

## 東京の合成電気自動車配送問題の分析

人口メッシュから合成顧客を抽出し、公開物流施設を配送拠点の代理、充電記録を候補位置の代理として使う。車両諸元から想定条件のパラメーターを定め、経路の代理表現で探索的な制約評価を行う。出力を観測需要、最適化済みの実経路、充電設備利用率、電力系統負荷、運用失敗率と解釈してはならない。

<a id="discussion-and-next-stage"></a>

## 考察と次の段階

今後の検討方向は次のとおり。

1. Reduced-手法 検証: 管理対象の R23 予備試験を実行し、検証済み Ising ハミルトニアンからAer 厳密-期待値 量子近似最適化アルゴリズム、二値 実行可能性、経路 評価指標までの再現性を確認する。
2. Real-world 最適化: 道路網 移動 times, calibrated or observed demand, 時間窓, sequential 充電率 and 充電 dynamics, 古典計算 最適化 baselines, and operational 検証を全体 EVRP/Hayateへ統合する。
3. Application-stage framework: problem 問題例・constraint・シミュレーター 根拠をexpected 量子計算-technology stagesと分離して接続する。

<a id="current-limitations"></a>

## 現在の限界

- 顧客需要と位置は合成値または代理指標に基づく。
- 経路構築は、検証済みの道路網最適化の基準ではない。
- 充電率の逐次変化、充電設備到着時の充電率、一般利用可否、混雑、営業時間、接続端子の互換性は未完成または未評価。
- 回路幅の根拠は符号化・検証方式によって異なる。
- 制約を表現していることと、応用上の妥当性を検証したことは同じではない。
