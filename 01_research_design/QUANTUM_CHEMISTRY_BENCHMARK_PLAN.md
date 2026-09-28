<a id="battery関連量子化学benchmark調査計画"></a>

# 電池関連量子化学ベンチマーク調査計画

更新日：2026-09-26。文書改訂COMPLETED。文献の採用、性能抽出、時系列分析、simulationは未着手である。採択する順序は[全体の研究段階計画](RESEARCH_STAGE_ROADMAP.md)の段階14–18であり、電池条件別電気自動車配送経路問題比較と感度分析の後に位置する。本書は[二系統の研究計画](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)の量子化学側である。

## 1. 対象量と文献選択

主ベンチマークはground-状態 電力量、relative electronic 電力量、reaction 電力量である。電子構造法が直接対象とし、同じハミルトニアン・構造・基底・活性空間の参照と比較できる量を優先するためである。電池のkWh、cycle life、商用充電性能そのものを直接計算する計画ではない。redox-related 電力量やreaction barrierは必要時のderived/secondary quantityとし、反応状態、環境・熱補正、溶媒や電位基準を別途記録する。

電池との関係が説明され、実際の量子計算 computing experiment、量子計算 simulation、量子計算資源 estimationで使われた電子構造問題を採用候補とする。Li–S関連分子、Li–O2表面反応、Li-ion正極材料等は調査候補にすぎず、採用済みベンチマークや検証済み論文の存在を本書で断定しない。具体的な論文・系・数値は文献調査後に固定する。

採用条件は、一次論文または著者の補足資料に化学系、対象、手法、評価形態、参照の少なくとも追跡可能な記載があることである。査読論文を優先し、会議・preprintはその状態と版を明記する。著者資源 estimateは実行結果と区別する。精度や時間が欠測でも有用なサイズ・方法情報があれば収録可能であるが、欠測する比較軸には使わない。

宣伝的な電池関連性だけの例、出典のない性能値、電子構造量を扱わない経路計算最適化を主ベンチマークから除外する。一般的toy moleculeは方法論の参考のみとし、電池-relevant 根拠へ自動昇格させない。重複論文・preprint/journal版を紐付け、同じ結果を複数の技術進展として数えない。検索語・データベース・検索日・採否理由・DOI・版・page/tableを保存する。

<a id="2-三つの主要performance-metric"></a>

## 2. 三つの主要性能指標

<a id="accuracy参照からの誤差"></a>

### 精度：参照からの誤差

\[
\Delta E=|E_{method}-E_{reference}|
\]

同じ対象と単位で手法のエネルギーと参照値との差の絶対値を定義する式である。Hartree、eV、kJ/mol等の原単位を保存し、変換時は定数の出典とper particle/per mole等の境界を記録する。reaction 電力量は同じ反応式・化学量論で比較し、ground-状態 合計-電力量 誤りと混合しない。

参照 種類は厳密 結果、high-level 古典計算 結果、experimentally constrained 値、paper-specific 受入済み 参照から記録する。「厳密」は有限基底・活性空間内の厳密かを明示し、物理系全体に対する厳密としない。実験値との差には電子エネルギー以外の補正が含まれ得る。参照の不確かさ、手法の統計誤差・誤り barも保存する。chemical 精度等の閾値はproblem別に妥当性と必要な判断精度を確認し、普遍的閾値として自動適用しない。

<a id="tractable-system-size扱える電子構造系の大きさ"></a>

### 計算可能な系の規模：扱える電子構造系の大きさ

最低限electronsとorbitals、有効-space計算では有効 electronsと有効 orbitalsを記録する。全系と活性空間を区別し、orbitalが空間的なかspinか、基底、凍結中核、embedding、周期系のcell/k-point条件もnotesに保存する。原子数のみで比較しない。量子ビットは補助情報であり、logical/physical、tapering/mappingの違いを記録するが、量子ビット=chemical system 規模とはしない。

実行した系、シミュレーターで扱った系、資源 estimateで将来可能とした系は別検証方式である。「扱える」とは必要精度と時間条件が付いた状態であり、単なる回路構成や推定量子ビットから実行可能性を断定しない。

<a id="wall-clock一つの結果を得るまでの実時間"></a>

### 実経過時間：一つの結果を得るまでの実時間

原則は必要なenergy/property 結果を一つ得るまでの終了-to-終了 elapsed 時間である。状態 preparation、量子計算 実行、measurements、最適化処理 iterations、古典計算 processing、post-processingを可能な限り含める。ハミルトニアン生成・コンパイル・校正・待ち行列・反復試行を含むか、並列実行処理数、実機、stopping criterionを記録する。CPU/GPU時間の合計やshot実行時間をelapsed 時間と混同しない。

| Wall-clock type | 意味 |
|---|---|
| MEASURED | 指定した終了-to-終了境界の実測経過時間 |
| ESTIMATED | モデルまたは資源 estimateによる時間。仮定・境界を保存 |
| 一部完了 | 一部工程のみの報告。notesで実測/推定、欠ける工程を明示 |
| NOT_REPORTED | 報告なし、または対象結果の時間を切り出せない |

一次状況は一つとし、部分推定なら一部完了かつnotesにestimatedとする。原論文の実行時間呼称はそのまま別記する。欠けた工程を推測して総時間に補完しない。異なる実機・並列条件の差を因果的高速化としない。

<a id="3-classicalとquantumの共通抽出"></a>

## 3. 古典計算と量子計算の共通抽出

同じ電池 problemの古典計算 手法も収録する。DFT、CCSD/CCSD(T)、CASSCF、CASCI、selected CI、HCI等は候補であり、序列を先に決めない。各論文が何を参照としたかを記録する。量子法の参照計算と、同じ問題を解く比較対象の古典計算計算は異なる役割として区別する。

一行は一つの系・対象・手法・条件・検証方式である。同論文の複数サイズは別行とする。共通コンマ区切り形式の必須列は以下である。

```csv
Study,Year,Battery-relevant problem,Chemical system,Target quantity,Method,Classical / Quantum,Hardware / simulator,Electrons,Orbitals,Active electrons,Active orbitals,Qubits,Reference method,Accuracy,Accuracy unit,Wall-clock,Wall-clock type,Notes,Source
```

Studyは論文識別子と比較群 識別子を結び、出典にDOI/URLと補足資料の位置を保存する。追加監査列としてrow_id、publication/version 日付、basis、ハミルトニアン、形状、charge/spin、orbital convention、参照 種類、不確実性、実経過時間 単位、reported 範囲、parallelism、execution/estimate 検証方式、出典 page/table、接続 日付、採否理由を用意する。主要性能指標は三つのままであり、追加列は比較条件と来歴である。

未知はNOT_REPORTED、概念的に適用されない欄はNOT_APPLICABLE（理由付き）とする。未抽出はEXTRACTION_PENDINGとして報告なしと区別する。欠測を0や推定値で埋めない。量子ビットからelectrons/orbitalsを逆算しない。実験値・推定値・図から抽出した値は区別し、図の読取りには方法と不確かさを記録する。現時点で採用済みの数値行はない。

<a id="4-accuracy-first比較と時系列分析"></a>

## 4. 精度を優先した比較と時系列分析

評価順序は「必要な精度を満たす → その条件で扱える系の大きさ → その計算の実経過時間」である。

\[
N_{max}(\epsilon,T_{max})
\]

この記号は許容誤差epsilonと時間上限T_maxを満たす範囲で扱える最大problem 規模を表す。Nは原子数や量子ビット一個の値に固定せず、定義されたproblem family内のelectrons/orbitals/active space条件として扱う。比較可能な系列が不足する場合は数値化せず、報告された達成点と欠測を示す。

比較はsame 精度→larger system、same system→higher 精度、same 精度 and system→shorter 実経過時間で行う。任意の重み付き得点に合成しない。Pareto-style 解釈では同じ対象・モデル・参照・時間境界の群内でのみ非劣位を検討する。測定/推定、欠測、不確かさが比較を妨げる場合はNOT COMPARABLEとする。

publication yearと技術世代に沿って三軸を表示し、同じ比較群で何が新たに計算可能になったかを問う。publication 日付は実行日と同一ではない。単なる量子ビット増加、異なるchemistryへの対象変更、緩い精度への変更を性能進展と断定しない。古典計算と量子計算の双方を同じ表・比較条件で追跡する。

<a id="5-rd解釈と限界"></a>

## 5. 研究開発解釈と限界

精度改善は当該電子/反応エネルギー予測の不確かさ低減、サイズ拡大はより現実的な電極・界面・反応モデルを検討できる可能性、時間短縮は同じ研究期間内の候補評価数増加の可能性として解釈する。化学モデル誤差、計算以外の研究工程、実験合成・検証等を含むため、これらは条件付きの電池 material 研究開発 capabilityである。

量子化学性能から電池容量・寿命・充電性能への直接換算は禁止である。大きい系を扱えたから20kWhが26.7kWhになる、計算時間短縮で寿命が一定割合延びる、という関係は定義しない。量子計算 advantage/speedup、商用化、普及、量子計算の因果的寄与率をこの文献計画から主張しない。

<a id="6-evrp比較からの分離"></a>

## 6. 電気自動車配送経路問題比較からの分離

古典計算 chemistry／量子計算 chemistryの比較は、[EVRPのClassical/Quantum最適化比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)とは別の対象・参照・指標を持つ。前者は電子構造電力量と三軸の計算能力、後者は同じ電池/配送条件での経路・実行可能性・EV/energy/経済結果を扱う。系の拡大・精度改善・時間短縮を電池容量/寿命/充電速度へ直接換算しない。最終的な接続は材料研究開発能力と電池技術開発との限定的関係である。
