# Battery関連量子化学benchmark調査計画

更新日：2026-09-26。文書改訂COMPLETED。文献の採用、performance抽出、時系列分析、simulationはNOT_STARTEDである。採択する順序は[master roadmap](RESEARCH_STAGE_ROADMAP.md)の段階14–18であり、Battery条件別EVRP比較と感度分析の後に位置する。本書は[二系統の研究計画](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)の量子化学側である。

## 1. 対象量と文献選択

主benchmarkはground-state energy、relative electronic energy、reaction energyである。電子構造法が直接対象とし、同じHamiltonian・構造・基底・active spaceの参照と比較できる量を優先するためである。BatteryのkWh、cycle life、商用充電性能そのものを直接計算する計画ではない。redox-related energyやreaction barrierは必要時のderived/secondary quantityとし、反応状態、環境・熱補正、溶媒や電位基準を別途記録する。

Batteryとの関係が説明され、実際のquantum computing experiment、quantum simulation、quantum resource estimationで使われた電子構造問題を採用候補とする。Li–S関連分子、Li–O2表面反応、Li-ion正極材料等は調査候補にすぎず、採用済みbenchmarkや検証済み論文の存在を本書で断定しない。具体的な論文・系・数値は文献調査後に固定する。

採用条件は、一次論文または著者の補足資料に化学系、target、method、評価形態、参照の少なくとも追跡可能な記載があることである。査読論文を優先し、会議・preprintはその状態と版を明記する。著者resource estimateは実行結果と区別する。accuracyや時間が欠測でも有用なサイズ・方法情報があれば収録可能であるが、欠測する比較軸には使わない。

宣伝的なBattery関連性だけの例、出典のない性能値、電子構造量を扱わないrouting最適化を主benchmarkから除外する。一般的toy moleculeは方法論の参考のみとし、Battery-relevant evidenceへ自動昇格させない。重複論文・preprint/journal版を紐付け、同じ結果を複数の技術進展として数えない。検索語・データベース・検索日・採否理由・DOI・版・page/tableを保存する。

## 2. 三つの主要performance metric

### Accuracy：参照からの誤差

\[
\Delta E=|E_{method}-E_{reference}|
\]

同じtargetと単位でmethodのエネルギーと参照値との差の絶対値を定義する式である。Hartree、eV、kJ/mol等の原単位を保存し、変換時は定数の出典とper particle/per mole等の境界を記録する。reaction energyは同じ反応式・化学量論で比較し、ground-state total-energy errorと混合しない。

reference typeはexact result、high-level classical result、experimentally constrained value、paper-specific accepted referenceから記録する。「exact」は有限基底・active space内のexactかを明示し、物理系全体に対するexactとしない。実験値との差には電子エネルギー以外の補正が含まれ得る。参照の不確かさ、methodの統計誤差・error barも保存する。chemical accuracy等の閾値はproblem別に妥当性と必要なdecision精度を確認し、普遍的閾値として自動適用しない。

### Tractable system size：扱える電子構造系の大きさ

最低限electronsとorbitals、active-space計算ではactive electronsとactive orbitalsを記録する。全系とactive spaceを区別し、orbitalがspatialかspinか、基底、凍結core、embedding、周期系のcell/k-point条件もnotesに保存する。原子数のみで比較しない。qubitsは補助情報であり、logical/physical、tapering/mappingの違いを記録するが、qubits=chemical system sizeとはしない。

実行した系、simulatorで扱った系、resource estimateで将来可能とした系は別modalityである。「扱える」とは必要精度と時間条件が付いた状態であり、単なる回路構成や推定qubitsから実行可能性を断定しない。

### Wall-clock：一つの結果を得るまでの実時間

原則は必要なenergy/property resultを一つ得るまでのend-to-end elapsed timeである。state preparation、quantum execution、measurements、optimizer iterations、classical processing、post-processingを可能な限り含める。Hamiltonian生成・コンパイル・校正・queue・反復試行を含むか、並列worker数、hardware、stopping criterionを記録する。CPU/GPU時間の合計やshot実行時間をelapsed timeと混同しない。

| Wall-clock type | 意味 |
|---|---|
| MEASURED | 指定したend-to-end境界の実測経過時間 |
| ESTIMATED | モデルまたはresource estimateによる時間。仮定・境界を保存 |
| PARTIAL | 一部工程のみの報告。notesで実測/推定、欠ける工程を明示 |
| NOT_REPORTED | 報告なし、または対象結果の時間を切り出せない |

一次statusは一つとし、部分推定ならPARTIALかつnotesにestimatedとする。原論文のruntime呼称はそのまま別記する。欠けた工程を推測して総時間に補完しない。異なるhardware・並列条件の差を因果的speedupとしない。

## 3. Classicalとquantumの共通抽出

同じBattery problemのclassical methodも収録する。DFT、CCSD/CCSD(T)、CASSCF、CASCI、selected CI、HCI等は候補であり、序列を先に決めない。各論文が何を参照としたかを記録する。量子法の参照計算と、同じ問題を解く比較対象のclassical計算は異なる役割として区別する。

一行は一つの系・target・method・条件・modalityである。同論文の複数サイズは別行とする。共通CSVの必須列は以下である。

```csv
Study,Year,Battery-relevant problem,Chemical system,Target quantity,Method,Classical / Quantum,Hardware / simulator,Electrons,Orbitals,Active electrons,Active orbitals,Qubits,Reference method,Accuracy,Accuracy unit,Wall-clock,Wall-clock type,Notes,Source
```

Studyは論文IDと比較group IDを結び、SourceにDOI/URLと補足資料の位置を保存する。追加監査列としてrow_id、publication/version date、basis、Hamiltonian、geometry、charge/spin、orbital convention、reference type、uncertainty、wall-clock unit、reported scope、parallelism、execution/estimate modality、source page/table、access date、採否理由を用意する。主要performance metricは三つのままであり、追加列は比較条件と来歴である。

未知はNOT_REPORTED、概念的に適用されない欄はNOT_APPLICABLE（理由付き）とする。未抽出はEXTRACTION_PENDINGとして報告なしと区別する。欠測を0や推定値で埋めない。qubitsからelectrons/orbitalsを逆算しない。実験値・推定値・図から抽出した値は区別し、図の読取りには方法と不確かさを記録する。現時点で採用済みの数値行はない。

## 4. Accuracy-first比較と時系列分析

評価順序は「必要なaccuracyを満たす → その条件で扱える系の大きさ → その計算のwall-clock」である。

\[
N_{max}(\epsilon,T_{max})
\]

この記号は許容誤差epsilonと時間上限T_maxを満たす範囲で扱える最大problem sizeを表す。Nは原子数やqubits一個の値に固定せず、定義されたproblem family内のelectrons/orbitals/active space条件として扱う。比較可能な系列が不足する場合は数値化せず、報告された達成点と欠測を示す。

比較はsame accuracy→larger system、same system→higher accuracy、same accuracy and system→shorter wall-clockで行う。任意の重み付きscoreに合成しない。Pareto-style interpretationでは同じtarget・モデル・参照・時間境界のgroup内でのみ非劣位を検討する。測定/推定、欠測、不確かさが比較を妨げる場合はNOT COMPARABLEとする。

publication yearと技術世代に沿って三軸を表示し、同じ比較groupで何が新たに計算可能になったかを問う。publication dateは実行日と同一ではない。単なるqubit増加、異なるchemistryへの対象変更、緩いaccuracyへの変更を性能進展と断定しない。classicalとquantumの双方を同じ表・比較条件で追跡する。

## 5. R&D解釈と限界

accuracy改善は当該電子/反応エネルギー予測の不確かさ低減、サイズ拡大はより現実的な電極・界面・反応モデルを検討できる可能性、時間短縮は同じ研究期間内の候補評価数増加の可能性として解釈する。化学model誤差、計算以外の研究工程、実験合成・検証等を含むため、これらは条件付きのBattery material R&D capabilityである。

量子化学performanceからBattery容量・寿命・充電性能への直接換算は禁止である。大きい系を扱えたから20kWhが26.7kWhになる、計算時間短縮で寿命が一定割合延びる、という関係は定義しない。quantum advantage/speedup、商用化、普及、量子計算の因果的寄与率をこの文献計画から主張しない。

## 6. EVRP比較からの分離

Classical chemistry／Quantum chemistryの比較は、[EVRPのClassical/Quantum最適化比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)とは別の対象・参照・指標を持つ。前者は電子構造energyと三軸の計算能力、後者は同じBattery/配送条件でのroute・feasibility・EV/energy/経済結果を扱う。系の拡大・精度改善・時間短縮をBattery容量/寿命/充電速度へ直接換算しない。最終的な接続は材料R&D能力とBattery技術開発との限定的関係である。
