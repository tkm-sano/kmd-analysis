# Research Baseline

[リポジトリ概要](../../README.md)と[技術ガイド](../QUANTITATIVE_GUIDE.md)を併せて参照する。

研究基準日：2026年10月9日。対象はTAKUMA SANOの修士研究である。本書は研究全体を確認するための基準文書であり、修士論文本文、新しい実験報告、正式freezeの更新ではない。照合した公開実装の基準commitは `84bb50141240da5f53055c3008bdaa4a5b6e5977` である。

記述の区分は、**VERIFIED**（正式資料・保存結果から確認した事実）、**INTERPRETATION**（事実に基づく解釈）、**HYPOTHESIS**（今後検証すべき仮説）、**PLANNED**（実施予定）である。以下の参照記号は第13節の根拠資料に対応する。

## 1. 研究背景と上位目的

本研究の上位目的は、人々の生活・活動に必要な物流サービスを確保しながら、その実現に伴う社会技術システム全体のエネルギー消費を削減することである。これは研究の問題意識であり、本研究でシステム全体の削減を実証したという意味ではない。

**VERIFIED：** 完了した定量研究は、EVラストマイル配送の固定された部分問題において、経路計算手法とBatteryの比エネルギー条件が保存走行軌跡上のDC牽引電力量へどう接続するかを扱う。目的地の選択・割当から道路走行、電池・車両質量、電力量評価までを区別した限定モデルである。[G](../../docs/QUANTITATIVE_GUIDE.md)

**INTERPRETATION：** 計算技術やBattery性能の変化だけで社会全体の省エネルギーを説明することはできない。配送サービス、運用規則、インフラ、制度、他のエネルギー消費との接続条件を明示することが、定量結果から上位目的へ進むための課題である。

## 2. 正式な研究課題・仮説

**HYPOTHESIS：** 正式RQと主仮説は、Hayateに保持する `01_research_design/RESEARCH_QUESTION_AND_HYPOTHESIS.md`（記録日2026-09-28）を正本とし、以下に原文を引用する。RQは問い、主仮説は未完了の検証対象である。

正式RQ：

> 量子技術の進展は、電気自動車配送の経路計算とバッテリー性能の変化を通じて、ラストマイル配送の運用電力量にどのような影響を与えるか。

正式主仮説：

> 同一の充電を考慮した電気自動車配送問題において、古典計算を用いた場合と比較して、量子計算を用いた場合の方が、バッテリー性能の違いによる電気自動車配送の運用電力量の差が大きくなる。

原文SHA256：`abe729fc925372782bc62c5a4f3e597c09b5c214acfd31c3ec912f3efb85cb33`。正本ファイル自体は現在のGitHub配布対象ではない。引用は公開済み統合ガイドとも一致する。[G](../../docs/QUANTITATIVE_GUIDE.md)

**VERIFIED：** 主仮説は「充電を考慮した」同一配送問題を要求する。一方、今回完了した定量branchは、充電を実装せず、経路ごとの保存軌跡をBattery条件間で固定したControlled-DC評価である。[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json) 仮説を結果に合わせて無充電モデルの仮説へ書き換えず、主仮説の支持・棄却・検証完了を宣言しない。

## 3. これまでの研究経緯

**VERIFIED：** 2026-09-28にRQ・仮説を正本化した。初期の手法比較計画は、経路計算の比較と充電・Battery条件を含む主仮説評価を別の段階として定義していた。旧計画や旧R0の結果は歴史的資料であり、最終Protocol V2の結果と混在させない。

2026-10-06のmatched研究設計では、26 parent・25 groupから各3 subset replicateを定め、3・4・5・25・99・125顧客のnested部分問題を構成した。同日付のControlled-DCモデルfreezeは質量・物理係数・評価境界を固定した。その後の古典6規模評価、小規模Candidate C / Protocol V2、経路同一性、軌跡とBattery評価を経て、2026-10-08の最終freezeが共通64ブロックの統合結果を確定している。[A](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_FREEZE_AUTHORITY_CHAIN.csv)[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)

歴史的R0の経路取得40/78・同一29・異経路11は最終共通ProtocolのR0とは別authorityであり、主比較から除外されている。2026-10-09までのAPI・Notebook・文書の再編は、科学的な再実験や新しい数値の生成ではなく、保存結果の追跡と再利用のための整備である。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)[FS](../../reproducibility/release/FROZEN_RUNTIME_SOURCES.json)

## 4. 研究対象と定量モデルの構成

**VERIFIED：** 研究の接続は「需要・配送地点 → 固定割当・時間窓・道路OD → 訪問順の決定 → SUMO保存軌跡 → Battery質量条件 → Controlled-DC → 保存結果の比較」である。通常の実装入口は `src/kmd_quantitative/` のrouting、quantum、simulation、battery、energy、analysisである。Analysis APIは保存結果の読込みを行い、新しい科学的再集計を実行するものではない。[G](../../docs/QUANTITATIVE_GUIDE.md)[I](../../results/indexes/CANONICAL_RESULTS.json)

道路グラフ上のedge列と顧客訪問順、最適化に用いる道路旅行時間とSUMO観測時間、静的制約充足と実時刻診断は異なる。対象は固定顧客集合・固定一車両の巡回であり、全配送需要を同時に割当・運行する社会全体モデルではない。

正式研究入力はOSM道路データ、PLATEAU建物データ、e-Stat等を加工した合成需要に接続する。公開Notebookの3顧客入力・短い速度fixtureは小規模合成例であり、正式実験全体の入力ではない。元データの帰属・加工来歴の留保は[G](../../docs/QUANTITATIVE_GUIDE.md)第13・14節を継承する。

## 5. Path 1：経路計算

**VERIFIED：** matched設計は単一車両、デポDEP_006、容量216 parcel-equivalent、顧客サービス102秒、出発0秒、帰還期限32,400秒、時間窓幅7,200秒を基礎とする。parcel-equivalentをkgと解釈しない。固定割当を継承し、各部分問題の全顧客を一度ずつ訪問して帰着する。目的関数はデポとの両端legを含む道路旅行時間（秒）の最小化であり、待機・サービスは可行性と運行所要時間に関係するが、電力量を目的関数へ追加していない。[G](../../docs/QUANTITATIVE_GUIDE.md)[S](../../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)

古典計算は3・4・5顧客で全順列探索による最適性証明、25・99・125顧客で確定的ヒューリスティック3 sweepとHiGHS assignment LP下界によるgap評価を行う。後者を大域最適解と呼ばない。[C](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)

Candidate Cは位置二値変数 `x(customer, position)` を用いる補助変数なしPUBOである。変数数はn²で、R0は9、R1は16である。目的の道路旅行時間に、両one-hot制約と事前可行性評価に基づく違反完全順列の罰則を加える。変数順序は `(customer-1)*n+position`、罰則は固定入力の`penalty_s`に従う。qualification用の補助変数付きQUBOとは別である。[G](../../docs/QUANTITATIVE_GUIDE.md)[C](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)

正式QAOAは理想状態ベクトルシミュレーションである。Protocol V2はp=1、H初期状態、X mixer、COBYLA最大100目的評価・各2,048 shots、独立seedの最終4,096 shotsを用いる。入力構築、全順列の可行性事前評価、PUBO構築、パラメータ調整、復号・検査・選択は古典処理である。回路生成・状態標本化に量子アルゴリズムを用いるが、量子実機で実行したものではない。[Q](../../src/kmd_quantitative/quantum/protocol_v2/protocol.py)[G](../../docs/QUANTITATIVE_GUIDE.md)

最終標本のみを経路取得の根拠とし、可行表との照合と独立validatorによる検査を行う。可行経路の最小道路旅行時間を選び、同点は整数bitstringの順序で決定する。最適化途中の標本を混ぜず、未取得経路を補完しない。可行標本がないことは配送問題の不可行性証明ではない。パラメータincumbentの選択規則と最終経路の選択規則も別である。[G](../../docs/QUANTITATIVE_GUIDE.md)[Q](../../src/kmd_quantitative/quantum/protocol_v2/protocol.py)

Notebook02の教材QAOAは既定64 shots等の簡略条件であり、正式Protocol V2ではない。その0/64・NOT_ACQUIREDを以下のR0/R1科学結果と混同しない。計算高速化、量子優位、量子実機性能、大規模QAOAの実証はいずれも行っていない。

## 6. Path 2：Battery性能

**VERIFIED：** 名目容量は20 kWh、初期利用可能エネルギーは18 kWhで固定する。比エネルギーによるパック質量は `20,000 Wh / 比エネルギー(Wh/kg)` であり、容量増大と質量低減を混同しない。[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)

|条件|比エネルギー Wh/kg|パック質量 kg|車両質量 kg|運転者込み走行質量 kg|
|---|---:|---:|---:|---:|
|B0|180|111.111111|1100.000000|1155.000000|
|B1|220|90.909091|1079.797980|1134.797980|
|B2|250|80.000000|1068.888889|1123.888889|

表は[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)の保存値を小数点以下6桁に表示したものである。共通運転者55 kg、エネルギー側の積載質量・追加設備0 kgである。固定容量で異なる比エネルギーを与える仮定上の感度評価であり、量子材料計算による電池軽量化の達成を示すものではない。

Controlled-DCは同じ保存時刻・速度軌跡を各Battery条件へ与え、転がり抵抗、並進・回転運動、空気抵抗の仕事を評価する。1秒間隔、右端速度による抵抗仕事、隣接速度二乗差による運動エネルギー、正側wheel仕事を一定効率0.90でDCへ変換する規則である。平坦路・回生なしであり、補機、旋回損失等は評価境界外である。Crrの下限・上限条件はp_bar=4.5/2.6に対応し、信頼区間や実車の圧力変更実験ではない。[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)

18 kWhは実際の残量会計に使い、累積DC Whを差し引き、負残量を失敗として記録する。ただしSOCによる走行停止、充電、再計画は実装していない。DC牽引電力量を車両の全消費電力、充電損失込みの電力量、物流システム全体のエネルギー消費へ拡張しない。[B](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)[G](../../docs/QUANTITATIVE_GUIDE.md)

## 7. 定量評価の結果

### 7.1 経路取得と共通母集団

**VERIFIED：** 最終freezeの値は以下である。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)[P](../../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv)

|正式branch|science実行完了|経路取得|古典と同一経路|異経路|下流軌跡・Battery評価|
|---|---:|---:|---:|---:|---|
|R0・3顧客|78/78|78/78|78|0|78件|
|R1・4顧客|78/78|64/78|59|5|取得した64件のみ|

計画78ブロックを `parent_id, replicate_id` で対応させ、共通64を含め、R1未取得14を除外理由付きで保持する。共通64は26 parent・25 groupに属する。subset replicateを独立な量子seed反復や独立地理標本とはしない。64/78は経路取得の記録であり、配送サービス充足率ではない。全78science実行完了とも区別する。

### 7.2 Battery削減率とMethod×Battery

**VERIFIED：** 各scale・method・経路・Crr条件について、`Saving(%) = 100×(E_B0−E_Bk)/E_B0`、`D = Classical Saving − QAOA Saving`、`T = D_R1−D_R0`である。Tの単位はpercentage points（pp）であり、kWh差ではない。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)[T](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)

|Crr条件|Battery比較|共通ブロック数|平均T（pp、保存Decimal）|中央値|正／ゼロ／負|
|---|---|---:|---:|---:|---|
|CRR_LOWER_BOUND|B0_TO_B1|64|-0.000248222961986721875|0|1／59／4|
|CRR_LOWER_BOUND|B0_TO_B2|64|-0.0003824303659828328125|0|1／59／4|
|CRR_UPPER_BOUND|B0_TO_B1|64|-0.000219201055817571875|0|1／59／4|
|CRR_UPPER_BOUND|B0_TO_B2|64|-0.0003377541726442796875|0|1／59／4|

四条件とも非ゼロ5件はR1の異経路5件と一致する。4条件×64=256行を256独立標本とは数えない。R0では全78同一経路・同一軌跡で両methodの電力量・Battery効果差は全条件exact zeroである。R1の同一59件も対応する保存値が一致する。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)[R](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)

Battery感度の記述例として、古典R0全78論理経路・Crr下限条件の平均削減率はB0→B1で1.4655076004617063%、B0→B2で2.2567503061108614%である。これは[BS](../../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)の保存meanであり、共通64のT、量子計算の効果、独立標本平均ではない。

### 7.3 DC電力量と差分の意味

**VERIFIED：** [E](../../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv)は共通64×2 Crr×3 Battery=384行の両scale・両methodの保存Whを保持する。直接電力量差は `Quantum − Classical`（Wh）であり、削減率の差D・T（pp）とは別である。例として保存表先頭ブロック（replicate_id=0、Crr下限、B0）ではR0の両methodが1,228.8725296535952 Wh、R1の両methodが1,262.7541023281183 Whである。これは一つのI→Iブロックの値であり、研究全体の平均・総量ではない。

異経路5件では、各Battery/Crr条件で直接電力量差の絶対値がBattery saving interactionの絶対値より大きい。同一59件では両差ともゼロである。平均Tは少数例に敏感であり、保存leave-one-outでは最大影響ブロックを除くと共通64平均の絶対値は約60–62%低下する。符号維持を一般的な頑健性や統計的有意差と解釈しない。[R](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)

### 7.4 古典6規模と配送診断

**VERIFIED：** [C](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)[S](../../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)[L](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)に基づく条件と保存診断は以下である。

|顧客数|論理問題数|異なる実体数|古典解法の保証|遅延停止／該当経路|帰還期限超過経路|
|---:|---:|---:|---|---:|---:|
|3|78|78|厳密最適|0／0|0|
|4|78|78|厳密最適|0／0|0|
|5|78|78|厳密最適|0／0|0|
|25|78|78|下界とのgap評価|0／0|0|
|99|78|78|下界とのgap評価|73／61|1|
|125|78|70|下界とのgap評価|63／55|3|

計468論理問題・460実体である。125顧客の重複を独立実行としない。保存検証では静的制約と全460実体のnative走行完了を確認しているが、SUMO観測時刻の診断では遅延136停止・116経路、帰還期限超過4経路がある。これらを消去せず、現実の全配送需要の充足とは区別する。実行可否と電力量を計算できることも別である。

顧客数に加えて顧客構成・地理・時間窓・解法が変わるため、規模別の旅行時間や電力量の差を顧客数単独の因果効果とは呼ばない。大規模側のQAOA結果は存在しない。[C](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)[L](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)

## 8. 得られた知見と解釈

**INTERPRETATION：** 共通Protocol下での「経路選択 → 走行軌跡 → DC電力量 → Battery質量感度」という接続を、保存結果を用いて追跡できた。同一経路・同一軌跡・同一物理条件で効果が一致することはモデル内部の対照となるが、古典・量子の計算性能一般が同等である証明ではない。[R](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)

R1の5異経路でのみ小さなBattery感度差が観測されたことは、技術名そのものより、取得する経路と運動履歴を介した条件を調べる必要性を示唆する。負のTは本定義上R1のQuantum由来軌跡で相対Battery削減率が大きいことを示すが、運用電力量が常に少ないこと、求解性能が高いこと、主仮説の成立を意味しない。

**VERIFIED：** 最終判定は共通Protocolの変更交絡をRESOLVEDとする一方、全78母集団の効果は補完なしに識別できず、純粋な因果的規模効果もNOT_ESTABLISHEDとする。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json) 本書はこの判定を維持する。

## 9. 研究上の限界・未検証事項

**VERIFIED：** 限界は、1 science seed/PID、共通乱数なし、非ランダムなR1取得subset、nested顧客課題の変化、parent/group依存、少数非ゼロcaseへの感度である。未取得14の値は補完していない。全母集団効果、量子優位、高速化、実機性能、実運用保証は識別されていない。[F](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)[R](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)

車両の同時交通、充電・SOC停止・再計画、補機、充電損失、計算機・通信・物流施設・製造等のエネルギーは今回の統合評価に含まれない。配送未充足による消費減少を省エネルギー成果と扱わない。

公開API・fixture・保存集計の検証成功と、全量科学実験の再現成功は異なる。全OD、全軌跡、専用router・native fork、全量workerの実行条件等はHayate側に残る。PLATEAUの中間加工履歴、全採用統計セル、道路変換記録の不一致、ODbL条件の一部についても既存ガイドの留保を保持する。今回新たな権利監査・許諾認定は行っていない。[G](../../docs/QUANTITATIVE_GUIDE.md)

## 10. 量子技術から物流・エネルギーへの影響

**HYPOTHESIS：** Path 1では、計算技術の進展が利用可能な求解方法や取得経路を変え、配送運用を介してエネルギーへ影響する可能性がある。ただし、計算資源・時間・取得信頼性、制約充足、運用への採用条件が成立する場合に限る。現在の理想QAOA結果だけでその将来効果を外挿しない。

**HYPOTHESIS：** Path 2では、量子技術を含む材料研究が実用Battery性能へ接続し、同容量の軽量化が運用電力量へ影響する可能性がある。材料計算から実用パック性能、安全性、寿命、生産条件への橋渡しは本定量研究では実証していない。180/220/250 Wh/kgを量子技術の実現予測値としない。

**INTERPRETATION：** 上位目的への接続には、サービスを維持する技術・制度・インフラの条件と、追加的なエネルギー負担を含む評価境界の整理が必要である。以下の研究工程は、この条件付き影響経路を具体化するために置く。

## 11. 今後の研究工程

以下は**PLANNED**であり、今回完了した活動ではない。最終freezeの次段階もPLANNED_NOT_EXECUTEDである。モデル係数の根拠として既に行った文献確認と、今後の統合的文献調査を区別する。

1. **課題抽出と関連文献調査。** 経路取得の不確実性、配送制約と観測時刻の差、Battery感度の条件依存、システム境界外の消費等を定量結果から抽出する。技術・運用・制度・インフラの知見を、出典と適用条件を付して整理する。
2. **問題の抽象化とワークショップ。** 定量モデル固有の数値やアルゴリズムをそのまま将来像とせず、サービスを確保しつつ消費を下げるための問題へ抽象化する。解決アイデアと成立条件を収集する。参加者の意見を実証済み効果と扱わない。
3. **統合と専門家インタビュー。** 文献・ワークショップの成果を統合し、技術構成、実現条件、障害、影響経路を専門家と評価する。対象選定・同意・記録・分析方法を事前に定め、第三者情報の公開範囲を管理する。
4. **条件付き影響経路と技術的要求。** 各経路について前提、作用機構、必要条件、反証・不成立条件、証拠と不足情報を整理し、社会技術システムへの要求としてまとめる。専門家の判断によって因果効果が自動的に実証されたとはしない。

自動運転車・ドローン等の詳細モードモデル、新しい大規模定量実験、System Dynamicsは必須工程としない。必要性が生じた場合に別途研究範囲を判断する。

## 12. 修士論文への接続

**PLANNED：** 論文では上位目的、正式RQ・仮説、実施した限定モデル、保存結果、解釈と限界、今後の文献・ワークショップ・インタビューを接続する。充電を含む主仮説と現評価の隔たりを明示し、未実施部分を結果章の実績へ混ぜない。正式RQを結果に合わせて変更しない。

本書は執筆の基準であり、章本文や完成論文ではない。Hayateの `docs/thesis/main.tex` をLaTeX編集入口とし、テンプレート・ビルド環境はローカル用途で保持する。これらは今回のGitHub配布へ追加しない。論文で引用する図表は保存結果の正本・母数・単位を示し、説明のために値を改変しない。

## 13. 根拠資料・正式結果の参照先

以下は本書から辿れる公開済み資料である。freeze、保存集計、実装、説明を区別する。リンク先の内部参照にはHayate限定資料が含まれる場合がある。

- [F] 正式な最終結果freeze：[FINAL_QUANTITATIVE_RESULT_FREEZE.json](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)。
- [R] 凍結済み最終報告：[FINAL_QUANTITATIVE_STUDY_REPORT.md](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)。
- [A] 上流freezeのauthority・hash台帳：[FINAL_FREEZE_AUTHORITY_CHAIN.csv](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_FREEZE_AUTHORITY_CHAIN.csv)。
- [T] 凍結済みT集計：[FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)。
- [B] Controlled-DCモデルfreeze：[CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)。
- [P] 含有・除外の保存母集団：[COMMON_MATCHED_POPULATION.csv](../../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv)。
- [E] ブロック別の保存DC電力量：[DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv](../../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv)。
- [C] 古典6規模・量子比較の保存要約：[CLASSICAL_QUANTUM_SCALE_COMPARISON.csv](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)。
- [L] 配送時刻の保存診断：[LOGISTICS_SERVICE_SCOPE.csv](../../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)。
- [S] 古典経路の保存集計：[MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv](../../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)。
- [BS] 古典Battery効果の保存集計：[MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv](../../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)。
- [Q] 凍結Protocolのバイト一致実行用配置：[protocol.py](../../src/kmd_quantitative/quantum/protocol_v2/protocol.py)。
- [G] 公開API・範囲・来歴の説明資料：[QUANTITATIVE_GUIDE.md](../../docs/QUANTITATIVE_GUIDE.md)。
- [I] 結果のパス・hash・schema索引：[CANONICAL_RESULTS.json](../../results/indexes/CANONICAL_RESULTS.json)。
- [FS] 凍結原本と実行用コピーの対応台帳：[FROZEN_RUNTIME_SOURCES.json](../../reproducibility/release/FROZEN_RUNTIME_SOURCES.json)。

Hayate限定の確認資料（GitHubへのリンクではなく原位置の識別である）：

- `01_research_design/RESEARCH_QUESTION_AND_HYPOTHESIS.md`：正式RQ・仮説の正本。第2節に原文とhashを記載した。
- `01_research_design/CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md`：初期研究設計。歴史的な方式・状態を最終Protocolへ流用しない。
- `01_research_design/methodology/PREPARED_ROUTE_SCALE_EXPERIMENT_PROTOCOL.md`：2026-10-06のnested部分問題・事前設計。
- 最終結果報告と同階層の `FINAL_MECHANISM_SUMMARY.csv`、`FINAL_SPEED_DISTRIBUTION_SUMMARY.csv`、`FINAL_SENSITIVITY_VERIFICATION.csv`、`FINAL_RESULT_SUMMARY.csv`、`FINAL_IDENTIFIABILITY_AND_LIMITATIONS.md`、`FINAL_ARTIFACT_MANIFEST.csv`：詳細機構・感度・限界と証拠対応。主要結果は公開freeze・報告から確認できるが、詳細検証の全資料を配布しているわけではない。

データ帰属・道路データReleaseの取得先は[G](../../docs/QUANTITATIVE_GUIDE.md)第13節に記載されている。本書は公開済みの研究上の情報と集計値を要約し、個人情報、インタビュー内容、第三者文献本文、元地理データを転載していない。既存Apache-2.0の自作コード・Notebookへの適用を、本書や外部データへ自動拡張しない。

本書の追加は配布Manifestに記録された計算・結果ファイルの変更を伴わない。既存Manifestは従来の配布内容の照合記録として保持し、本書の版はGit commitで追跡する。今後の更新でも正式freezeと本書の解釈・計画を別に管理する。
