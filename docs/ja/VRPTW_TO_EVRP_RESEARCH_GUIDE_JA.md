<a id="vrptwからevrpへstructured-initial-state研究の目的現在地次の実験"></a>

# 時間窓付き配送経路問題から電気自動車配送経路問題へ：Structured 初期状態研究の目的・現在地・次の実験

更新日：2026-09-22 JST。研究者本人が判断の流れを読み直すためのガイドである。

> **今どこにいるか：時間窓付き配送経路問題 Structured scientific 標本抽出開始直前である。**
>
> 完了：時間窓付き配送経路問題の定式化・古典参照・Uniform Standard 量子近似最適化アルゴリズム 調査、道路経路の検証・可視化、Candidate Aのoffline 検証、direct-構築検証、clean Git 基準、NFS4 台帳 固定検証。
>
> 未実施：Structured S01／S02／S03のscientific 標本抽出、電気自動車配送経路問題、電気自動車電力消費・経済評価。
>
> 次：**S01 N003 WIDE × 3 反復回数**を、改めてfresh 判定基準から開始する。
>
> 科学コード基準：`6ccbadbd42bdad6c95e22f7420aff6ee787c8997`。この文書は実験開始の指示ではない。

このガイドの数値は既存成果物を読んだ記録である。以下では、**確認済みの事実・次に実行する固定済み計画・将来の設計案**を区別する。将来案を現在の実装・検証結果として読んではならない。末尾の参照案内はローカル成果物の所在も示す。

## 1. この研究で何をしたいのか

**要点。** 需要条件の変化が配送計画を通じて電気自動車の運用や経済的結果へどう波及するかを、段階ごとに検証可能な形でつなぐことが研究全体の目的である。

```text
需要条件
  ↓
配送最適化
  ↓
配送ルート
  ↓
道路edge走行
  ↓
EV電力消費
  ↓
充電需要
  ↓
経済的結果
```

現在はこのうち**配送最適化の時間窓付き配送経路問題 基準／structured initialization 検証**にいる。量子計算は配送問題を解く候補手段であり、量子優位性や実運用での便益を前提としない。

**なぜ重要か。** 最終的な電力・経済指標だけを先に計算しても、その入力となる配送ルートが制約を満たさなければ意味が変わってしまう。まずルートの正しさ、解法の挙動、計算資源、結果の再現性を分けて検証する必要がある。

**現在の結論。** 最終的な連鎖は研究の目標であり、現時点で電力削減や経済的利益を検証したわけではない。

<a id="2-現在はevrpではなくvrptwである"></a>

## 2. 現在は電気自動車配送経路問題ではなく時間窓付き配送経路問題である

時間窓付き配送経路問題（車両 Routing Problem with 時間窓）は、時間窓付き配送経路問題である。現在のモデルは次を扱う。

| 現在扱うもの | 意味 |
|---|---|
| Customer visit | 必要な顧客訪問を満たすこと |
| Vehicle capacity | 車両の配送容量を超えないこと |
| 配送拠点 | 出発・帰着地点とその扱い |
| Route／slot structure | 車両・訪問順序・割当ての整合 |
| 時間窓 | 顧客サービス開始等の許容時刻に関する既存ルール |
| Travel time／reachability | 保存済み出発地・到着地移動時間と道路到達可能性を正本にすること |

まだ扱っていないのは、電池 容量、充電率、充電 station、充電 判断、充電 時間、電気自動車 electrical 電力量 consumptionである。**車両容量は配送物の容量であり、バッテリー容量ではない。** 到達可能な道路経路があることと、バッテリー残量で走り切れることも別である。

<a id="3-cvrpvrptwevrpの関係"></a>

## 3. 容量制約付き配送経路問題・時間窓付き配送経路問題・電気自動車配送経路問題の関係

| 段階 | 加わる主な制約・状態 | この研究での位置づけ |
|---|---|---|
| 容量制約付き配送経路問題 | 顧客訪問・配送容量・経路 | Structured設計原理の出発点 |
| 時間窓付き配送経路問題 | 容量制約付き配送経路問題に時間窓を追加 | 現在の検証対象 |
| EVRP／EVRPTW | バッテリー・充電率・充電等を追加 | 時間窓付き配送経路問題結果固定後の将来フェーズ |

```text
CVRP ──＋Time Window──> VRPTW ──＋Battery / SOC / Charging──> EVRPTW
```

電気自動車配送経路問題は電気自動車を扱う配送経路問題の総称として用い、時間窓も維持する拡張はEVRPTWと区別できる。現在は容量制約付き配送経路問題由来のCandidate Aを既存時間窓付き配送経路問題 符号化へ移植し、その適用範囲と限界を調べている。

<a id="4-uniform-initial-stateとは何か"></a>

## 4. 一様初期状態とは何か

Uniform 初期 状態は、一様な初期状態である。全量子ビット数を (N) とすると、例えば

$$
|+\rangle^{\otimes N}
=2^{-N/2}\sum_{x\in\{0,1\}^N}|x\rangle
$$

のように、すべてのビット列へ等しい初期振幅を与える。ここで (N) は顧客数 (n) ではなく、余裕変数等を含む全量子ビット数である。

Uniformは意図的な**比較基準**であり、実装ミスではない。既存B01／B02／B03は、Uniform＋Standard パウリX型混合演算を評価した固定済みの比較参照である。

既存Standard 調査は7 nominal 条件・21 反復回数を実行済みであり、今回のsmall-条件設定では最終 標本抽出から実行可能／最適 標本を観測しなかった。これは確率が厳密に0であることや、量子近似最適化アルゴリズムで時間窓付き配送経路問題を解けないことの証明ではない。

後に問題になったのは、Structured 実行処理が一度Uniform回路を構築してから初期層を置き換えていた**構築経路**である。Uniform 基準の研究上の役割とは区別する必要がある。

<a id="5-structured-initial-statecandidate-aとは何か"></a>

## 5. Structured 初期状態／候補 Aとは何か

Structured 初期 状態は、問題の構造を初期状態に反映する設計である。Candidate Aの既存名称は次である。

```text
minimal integer visit/slot route word
+
uniform capacity slack
```

直感的には、訪問・枠を表す経路 registerには既存の決定的な規則で1つの経路 wordを置き、容量制約の余剰を表す余裕変数 registerには一様な重ね合わせを置く方式である。すべての有効ルートを重ね合わせる方式ではない。

完全に無構造なビット列空間から開始するのでなく、経路として意味のある構造を初期状態に持たせる発想である。ただし、**容量余裕変数は一様であり、需要に適合する値だけを選別していない。**

constructionへ渡す入力は、顧客数`n`、車両数`m`、固定済み変数順序の3つだけである。最適解、実行可能解の一覧、目的／電力量 ranking、sampled 結果、temporal 実行可能性、いいえ-good satisfactionは使用しない。需要や時間窓を用いて新たな経路 wordを選び直すこともしない。

これはknown-solution leakage、すなわち答えに関する情報を初期状態へ埋め込んで比較を有利にしてしまうことを避けるためである。厳密 実行可能／最適 setsは**生成後の診断**にのみ用いる。

## 6. 候補 Aで何が保証され、何が保証されないか

**確認済みの範囲。** 今回の3群では、Structured初期分布の訪問-有効、経路-有効、physical-容量-有効、配送拠点-有効 質量はいずれも1である。一方、容量-符号化-有効 質量はN002 WIDE／N003 WIDE／N002 有効-時間窓の順に`1/256`、`1/16`、`1/256`である。

physical 容量-有効は復元された配送ルートの容量充足を意味し、容量-符号化-有効は余裕変数を含む符号化上の整合を意味する。この2つは同じ指標ではない。今回の問題例でphysical 容量-有効 質量が1だったことを、任意の需要・容量に対する一般保証へ拡張してはならない。constructorは需要・容量を入力していないためである。

有効-時間窓では、さらに次が成立する。

```text
initial feasible mass = 0
initial temporal-valid mass = 0
initial no-good violation mass = 1
```

つまり、経路構造が有効でも時間窓まで満たすとは限らない。**符号化 compatibility 合格 ≠ temporal 実行可能性 合格**である。いいえ-goodとは、許されない組合せを罰則項として表現する既存の制約である。

この限界を理由にsupportを刈り込んだり、実行可能 経路を挿入したりはしない。既存容量制約付き配送経路問題由来の設計をそのまま持ち込んだときの挙動を比較することが、次の実験の問いである。また、初期状態で成り立つ構造がStandard パウリX型混合演算による量子近似最適化アルゴリズム evolution後も保存されるとは限らない。

<a id="7-offline-validationで確認したこと"></a>

## 7. Offline 検証で確認したこと

以下は**初期状態の確率分布の診断**であり、最適化処理実行後の量子近似最適化アルゴリズム 性能ではない。質量は対象状態集合にある確率の総和、supportは非ゼロ振幅を持つbasis statesの数である。

| 独立制約なし二値二次最適化群 | Structured support | Feasible initial mass | Optimal initial mass | Mean nearest-feasible distance：Uniform → Structured | Temporal-valid mass（Structured） |
|---|---:|---:|---:|---:|---:|
| N002 WIDE | 256 | 0.00390625 | 0.00390625 | 7.45343017578125 → 4 | 1 |
| N003 WIDE | 16 | 0.0625 | 0 | 6.171875 → 2 | 1 |
| N002 active-TW | 256 | 0 | 0 | 8.90625 → 7.875 | 0 |

Nearest-実行可能 Hamming 距離は、ビット列からその条件の実行可能-状態 setまでの最小ビット反転数である。異なる時間窓では参照集合も異なり得るため、異なるregime間の数値を単純な性能順位にしてはならない。

正規化、support、変数順序、circuit/statevector fidelity、WIDE回帰、有効-時間窓 符号化 compatibility、待機-表示名 independence、leakageを確認済みである。v2では準備回路のfidelityが数値誤差内で1、最大振幅誤差が`1e-16`未満であった。

さらに、固定経路 registerを持つため、今回のp=1構造では経路 marginalがgammaに依存しないという限界も記録済みである。余裕変数側のパラメーター 感度や正の電力量 varianceだけから、経路探索が改善すると結論してはならない。

**現在の結論。** 意図したCandidate Aを数学的・実装的に生成できることを確認した段階である。特にN003は既存一般規則の静的 regressionであり、過去容量制約付き配送経路問題 scientific 実行でN003の改善を直接確認した条件ではない。

<a id="8-direct-build問題とは何だったか"></a>

## 8. 直接表現-構築問題とは何だったか

旧実装は次の順だった。

```text
Uniform full circuitを構築
  ↓
initial H layerをCandidate Aへ置換
```

これは「Uniform 回路を再生成しない」という比較条件に抵触した。標本抽出条件が違っていたと断定する問題ではなく、禁止された構築経路を使い、初期状態だけを差分とする構造を実装上明示できていなかった問題である。そのためscientific 標本抽出前に停止した。

修正後は次である。

```text
Candidate A preparation
  ↓
shared cost layer
  ↓
shared Standard X mixer
  ↓
measurement
```

費用は制約なし二値二次最適化を反映する層、mixerは状態間の振幅を変化させる層である。両armの量子近似最適化アルゴリズム bodyを共有し、Structured側に別の費用／mixer実装を複製しない。v4ではUniform 全体／初期 builderの呼び出しが0、保存済みUniform回路とのbody・パラメーター・measurement対応が一致し、144テストが合格した。

<a id="9-git-clean-baselineを作った理由"></a>

## 9. Git clean 基準を作った理由

実験の再現には「どの設定だったか」に加え、「どのコードを使ったか」が必要である。working treeがdirtyだと、同じ変更記録名でも実際のコードが異なり得る。

そこで実行に必要な検証済み コードと依存コードを変更記録し、無関係な過去作業をstashとarchiveへ保全した。削除やhistory rewriteでcleanにしたわけではない。以前の基準は次である。

```text
94a0fbe73c26149414f0692d3f117d7fcb4dbb9d
```

この分離により、実験時点のコードを一意に指し、実験途中の変更を検知できる。ただしGit 変更記録だけですべてが復元できるわけではない。scientific 出力や一部正本はリポジトリ 方針上ローカル管理であり、ハッシュ値固定済み成果物 bundleと実行環境も必要である。

<a id="10-nfs4-ledger-lock問題とは何だったか"></a>

## 10. NFS4 台帳固定問題とは何だったか

S01のfresh 判定基準は合格したが、台帳初期化で次の問題が生じた。

```text
専用lock fileをread-only（rb）で開く
  ＋ exclusive flock
  ＋ 現在のNFS4 filesystem
  → EBADF（Bad file descriptor）
```

台帳は回路・回測定・予約・消費を管理する台帳である。排他固定は、複数processが同時に予約して二重計上や過剰予約を起こすことを防ぐ。

修正は専用固定ファイルの`rb → r+b`である。ファイルを新規作成・切り詰めず、書込み可能なdescriptorで排他固定を取得する。台帳本体、会計 意味、atomic writeは変更していない。

v6では実S01パス上で取得・解放・再取得を確認し、同じNFS4上の合成 試験 台帳で2 processの排他、更新保持、重複予約拒否、例外後の整合性を確認した。104テストが合格した。これは現在の環境と試験範囲での確認であり、すべてのNFS環境や複数hostの障害回復を保証するものではない。

**重要な区別。** この停止もr0、reservation、最適化処理、計算方式 標本抽出より前であり、scientific 回路／回測定は0である。実装・基盤の失敗を、Structuredの科学的性能が悪かったという結果へ読み替えてはならない。

<a id="11-現在のclean-scientific-baseline"></a>

## 11. 現在のclean 科学的な基準

確認済みの科学コード基準は次である。

```text
6ccbadbd42bdad6c95e22f7420aff6ee787c8997
```

現在の状況は次である。

```text
VRPTW_S01_LEDGER_LOCK_NFS4_PREFLIGHT_VALIDATED
VRPTW_PRE_S01_GIT_BASELINE_V2_FROZEN
```

| 台帳上の値 | 現在値 |
|---|---:|
| Historical scientific circuits | 363 |
| Historical scientific shots | 743,424 |
| Scientific reserved | 0 |
| Sanity 回路（別枠） | 7 |
| S01 scientific 反復回数試行／完了 | 0／0 |
| S01 circuits／shots／optimizer evaluations | 0／0／0 |

363 回路は過去のStandard 調査の累積であり、S01で消費した数ではない。今回の文書作成もscientific 状態を変更しない。

**文書変更記録と科学基準の区別。** この文書を変更記録するとGit HEADは上記ハッシュ値より先へ進むが、検証済み科学コード基準を変更したことにはならない。次の条件を統制した launchで指定されたHEADと実際のHEADの照合はfresh 判定基準で行い、不一致を暗黙に許容したり基準 成果物一覧を書き換えたりしてはならない。

## 12. S01・S02・S03とは何か

| 段階 | Condition | Repetitions | Uniform reference | 目的 |
|---|---|---:|---|---|
| S01 | N003 WIDE（G2） | 3 | B02 | 最初の条件を統制した scientific launchと実行整合性確認 |
| S02 | N002 WIDE（G1） | 3 | B01 | 別サイズのWIDE条件で確認 |
| S03 | N002 active-TW／MODERATE（G3） | 3 | B03 | 時間制約がbindingする条件で適用範囲・限界を確認 |

代表条件 識別子はそれぞれ`R24-RND-N003-R01-RHO050-TW-WIDE`、`R24-RND-N002-R01-RHO050-TW-WIDE`、`R24-RND-N002-R01-RHO050-TW-MODERATE`である。

既存7 nominal 条件は、B01↔B06、B02↔B07、B03↔B04↔B05という3つのsame-制約なし二値二次最適化／same-乱数の種群へ整理済みである。これらを7つの独立標本抽出 根拠として二重計上しない。「3 independent 制約なし二値二次最適化 groups」は重複を除いた設計単位であり、群間の統計的独立性を保証する表現ではない。

Structuredも3群を基本単位とし、待機等の表示名差はindependent temporal replayで扱う。待機 表示名だけで別初期 状態を作らない。**S01→S02→S03は自動進行せず、各一括処理で停止・検証・次タスクの明示的指示を必要とする。**

## 13. なぜ一様とStructuredを比較するのか

研究問いは、初期状態に経路構造と既存の余裕変数構造を与えたとき、Uniform initializationに比べて量子近似最適化アルゴリズムの標本抽出 behaviorがどう変わるか、である。

過去容量制約付き配送経路問題では実行可能性・距離・構造上の validityの改善が3 basesで再現した一方、optimalityは一貫せず2 basesで改善、1 baseで悪化したと記録されている。これを時間窓付き配送経路問題全般の性能保証に拡張せず、移植先で検証する必要がある。

比較は**初期 状態の意味と限界を調べる基準／ablation 比較**である。Uniformは除去すべき間違いではない。既存Uniform結果を読取り専用で再利用し、再標本抽出しない。

初期状態以外は同じ制約なし二値二次最適化、変数順序、費用、Standard パウリX型混合演算、`p=1`、COBYLA、回測定、paired 乱数の種 方針、transpilation、検証器、評価指標を維持する。COBYLAはmaxiter 100、rhobeg 0.25、tol 0.01、catol `1e-8`、外部 training cap 99である。training／最終は各2048 回測定、初期alphaは`0.5262887849165184`、betaは`0.37`、規模は`52628.87849165184`である。

同一乱数の種を対応させても、異なる回路が完全に同一の乱数過程をたどるとは主張しない。各群3 反復回数を科学的単位とし、回測定を独立実験数として扱わない。主解析はpaired differencesと記述統計である。

## 14. 何を比較するのか

| 軸 | 比較するもの | 読み違えを避ける点 |
|---|---|---|
| Solution quality | Feasible／optimal rate、feasible route objective、gap | Feasibleであることと最適であることは別 |
| Constraint satisfaction | Visit、route、depot、physical capacity、capacity encoding、temporal validity | 復元不能はNOT_EVALUABLEとし、有効や単純な違反へ混ぜない |
| Quantum optimization behavior | 制約なし二値二次最適化 電力量、収束履歴、標本抽出 distribution、nearest-実行可能 距離 | 低電力量だけで良いルートとしない |
| Resource | Circuits、shots、depth、CX、optimizer evaluations、runtime、RSS | Sampling改善と追加資源 費用を別々に報告 |

実行可能 標本が0の場合、best 実行可能 目的や隔たりに0を入れず、null／not evaluableとする。待機は到着後サービス開始までの待ちであり、それ自体は違反ではない。

有効-時間窓でStructuredから実行可能 標本が出れば、初期振幅0の実行可能 statesへevolution後に確率質量が移った可能性を調べる。出なければ、それも変更せず記録する。temporal-有効だけの改善、電力量だけの改善、overall 実行可能性の改善は別の結果である。どの場合も結果を見てCandidate Aを再設計しない。

<a id="15-qubo-energyとev電力消費は違う"></a>

## 15. 制約なし二値二次最適化 電力量と電気自動車電力消費は違う

制約なし二値二次最適化はQuadratic Unconstrained Binary 最適化、すなわち二値変数の二次式を最適化する表現である。現在の電力量は**制約なし二値二次最適化／ハミルトニアン 電力量**であり、経路計算 termと各constraint 罰則項を含む最適化上の量である。

$$
\text{低いQUBO energy}\not\Rightarrow\text{feasible route}
$$

$$
\text{QUBO energy}\neq\text{EVの電力消費量（kWh）}
$$

現在は電気自動車電力モデル自体がないため、制約なし二値二次最適化 電力量低下を省電力・充電削減・経済利益へ換算してはならない。

## 16. S01で次に何をするのか

次のscientific 作業は**N003 WIDE／Structured × 3 反復回数**だけである。

```text
fresh gate（baseline・hash・設定・seed・実lock・resource・ledger）
  ↓
r0
  ↓
r0 integrity / ledger gate＋残時間・消費量の再見積もり
  ↓ PASSの場合のみ
r1 → integrity確認 → r2
  ↓
STOP scientific execution
  ↓
S01 integrity audit
  ↓
保存済みUniform B02とのbaseline comparison
```

r0の性能が悪いことは停止理由ではない。固定 violation、台帳 mismatch、wrong 乱数の種／制約なし二値二次最適化／回測定、出力 corruption、資源／計算方式異常等が停止理由である。技術的な 不具合でも勝手に再試行せず、既存方針に従い記録・停止する。

S01最大は`3 × (99 training + 1 final) = 300 circuits`、614,400 回測定である。未使用予約を消費するための追加実行はしない。S01完了はN003 WIDEの一括処理完了であり、Structuredの一般的優越性や時間窓付き配送経路問題全体の完了を意味しない。

<a id="17-vrptw終了後は何をするのか"></a>

## 17. 時間窓付き配送経路問題終了後は何をするのか

```text
S01 → 個別validation
  ↓ 別途指示
S02 → 個別validation
  ↓ 別途指示
S03 → 個別validation
  ↓
Uniform vs Structured integrated analysis
  ↓
VRPTW results freeze
```

ここで初めて、WIDEでのtransferと有効-時間窓での限界をまとめる。対象は小規模問題例、限られたbases、Uniform／Candidate A、Standard X、p=1という範囲である。large-問題例 性能、量子優位性、real-world deployment価値は未検証である。

道路道路網への接続基盤は既に古典計算 厳密／proven-最適 混合整数線形計画 経路を正本として具体化・検証・visualize済みである。これは量子近似最適化アルゴリズムがそのルートを標本した証拠ではない。既存成果物を保持し、将来の電気自動車配送経路問題で利用できる経路表現として位置づける。

<a id="18-その後の最小evrp"></a>

## 18. その後の最小電気自動車配送経路問題

**以下は将来の設計案であり、今回固定・実装・検証した仕様ではない。** 時間窓付き配送経路問題結果固定後に、電池 容量、充電率、充電判断、充電時間、電力量 consumptionを初めて導入する。

最初の電力量 基準候補は距離比例モデルである。

$$
E_{ij}=r\,d_{ij}
$$

(d_{ij}) は移動距離、(r) は単位距離当たり電力消費、(E_{ij}) はその移動の電力消費である。例えば距離をkm、(r)をkWh/kmで定義すれば結果はkWhとなる。係数、単位、車両条件、充電率更新、充電rate・場所・利用条件・時間窓との関係は、次フェーズで別途設計・検証する。数式だけで電気自動車配送経路問題が完成するわけではない。

## 19. なぜ最初は距離比例でよいのか

距離比例で十分に現実を説明できると主張するためではない。**電気自動車制約追加の影響と電力量 モデル高度化の影響を分離するための単純な基準案**だからである。

最初から速度、積載量、gradient、acceleration、regenerative braking、交通をすべて導入すると、結果差の原因と入力データの不確実性を追いにくくなる。

```text
VRPTW：配送・時間制約
  ↓
EVRP-1：distance-proportional energy＋最小の電池・充電制約
  ↓
EVRP-2：road-edge-level energy modelの詳細化
```

各段階で同一入力に対する検証と比較条件を設ける方針案である。現時点では電気自動車配送経路問題-1も未実施である。

<a id="20-将来のroad-edge-level-energy-model"></a>

## 20. 将来のroad-道路区間-level 電力量モデル

将来は、道路道路区間ごとの走行条件を使うモデルを検討する。

$$
E_{ij}=f(d_{ij},v_{ij},t_{ij},\mathrm{payload},\mathrm{gradient},\mathrm{acceleration})
$$

ここで式の添字を配送地点間往復の各区間とする場合、その内側でroad-道路区間単位の量を積み上げる必要がある。速度・勾配・加減速等を表現できるデータと、係数・単位・較正／検証 正本は別途必要である。既存距離／移動 時間だけから未保存の車両挙動を推測して補わない。

既存の`stop sequence → road-node／edge sequence → distance／travel time`の検証基盤へ車両挙動を接続し、その後に電力消費へ進む。回生や充電需要、経済換算もそれぞれ独立した仮定と検証を要する。

## 21. 研究全体の最終像

```text
需要
  ↓
VRPTW routing
  ↓
Structured / quantum optimization
  ★ 現在：VRPTW Structured scientific sampling開始直前
  ↓
EVRP
  ↓
road-edge vehicle behavior
  ↓
EV energy consumption
  ↓
charging demand
  ↓
economic outcome
```

この図は研究フェーズの接続であり、量子解法が唯一の経路計算 正本になるという意味ではない。古典参照と独立検証器を保持し、配送解の正しさとその先の電力・経済モデルの正しさを段階ごとに確認する。

**次にすることはS01である。** 現在の準備状況は実行を許可できる準備状態を表すだけであり、標本抽出完了や科学的優越性を意味しない。

## 参照案内：どの記録を読めばよいか

次のパスはリポジトリの最上位からの相対パスである。`reproducibility/outputs/`以下はローカル管理を含むため、GitHub上の文書だけを複製しても全成果物が揃うとは限らない。更新されたコードreceiptと過去の結果receiptも区別する。

| 確認したいこと | Authority／参照先 |
|---|---|
| 初期状態の数値・限界 | `reproducibility/outputs/traffic_simulation/r24_vrptw_structured_initial_state/20260922_v2/DESIGN_VALIDATION_REPORT.md` |
| 初回実行処理統合（旧構築経路） | 同上最上位の`20260922_v3_implementation_preflight/IMPLEMENTATION_PREFLIGHT_REPORT.md` |
| 直接表現-構築検証 | 同上最上位の`20260922_v4_direct_build_preflight/DIRECT_BUILD_PREFLIGHT_REPORT.md` |
| 過去作業の保全・旧基準 | 同上最上位の`20260922_v5_pre_s01_git_baseline/GIT_CLEANUP_REPORT.md`、`PRE_S01_GIT_BASELINE.json` |
| NFS4によるS01実行前停止 | 同上最上位の`20260922_s01_n003_wide_controlled_launch_v2/S01_EXECUTION_REPORT.md` |
| 現行固定検証・新基準 | 同上最上位の`20260922_v6_ledger_lock_preflight/LEDGER_LOCK_PREFLIGHT_REPORT.md`、`PRE_S01_BASELINE_V2.json` |
| 比較条件の固定 | `reproducibility/outputs/traffic_simulation/r24_vrptw_uniform_vs_structured_comparison_spec/20260922_v1/` |
| Standard 調査と重複除外 | `reproducibility/outputs/traffic_simulation/r24_vrptw_qaoa_execution/20260921_v1/study_synthesis/SCIENTIFIC_FINDINGS.json` |
| 古典計算道路経路の正本 | `reproducibility/outputs/traffic_simulation/r24_vrptw_road_network_routes/20260921_v1/EXECUTION_SUMMARY.json` |
| Historical scientific ledger | `reproducibility/outputs/traffic_simulation/r24_vrptw_qaoa_scientific/20260921_v1/CIRCUIT_RESERVATION_LEDGER.json` |

コードの入口は[Candidate A constructor](../../05_src/traffic_simulation/r24_vrptw_structured_initial_state/construction.py)、[Structured 実行処理](../../05_src/traffic_simulation/r24_vrptw_structured_worker/worker.py)、[shared 量子近似最適化アルゴリズム body](../../05_src/traffic_simulation/r24_vrptw_qaoa_worker/circuit.py)、[台帳 adapter](../../05_src/traffic_simulation/r24_vrptw_structured_worker/ledger.py)、[NFS4検証](../../05_src/traffic_simulation/r24_vrptw_ledger_lock_preflight/checks.py)である。背景の需要・データ設計は[2026-09-15時点の研究設計ガイド](R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)を参照する。そちらの「現在」は当時の容量制約付き配送経路問題段階を指す。

## 用語集

| 用語 | この研究での意味 |
|---|---|
| 容量制約付き配送経路問題 | 配送容量制約付き車両経路問題 |
| 時間窓付き配送経路問題 | 時間窓付き車両経路問題 |
| EVRP／EVRPTW | 電池・充電等を扱う電気自動車の経路問題／時間窓付き拡張 |
| 制約なし二値二次最適化 | 二値変数の二次式による最適化表現。制約は罰則項として含む |
| 量子近似最適化アルゴリズム | 量子計算 Approximate 最適化 Algorithm。費用層とmixer層を用いる量子最適化手法 |
| Uniform initial state | 全ビット列へ等しい初期確率を与える一様状態 |
| Structured initial state | 問題構造を反映した初期状態 |
| Candidate A | 固定経路 word＋uniform 容量 余裕変数という今回選択済みの構築規則 |
| Feasible mass | すべての必要制約を満たす状態集合の確率総和 |
| Optimal mass | 古典参照の最適性定義を満たす状態集合の確率総和 |
| Temporal-valid mass | 独立temporal replayで時間条件を満たす状態集合の確率総和。NOT_EVALUABLEとは区別 |
| 充電率 | State of Charge。バッテリー残量の状態。現在の時間窓付き配送経路問題には未導入 |
| Ledger | 回路・回測定の予約、開始、消費、失敗等を記録する永続台帳 |
| 固定 | 比較前に条件・正本・解釈ルール等を固定すること |
| Fresh gate | 実行直前にハッシュ値・設定・乱数の種・資源・台帳等を再照合する検査 |
| Support | 非ゼロ振幅を持つbasis statesの集合 |
| Slack | 容量等の制約を符号化する際の余剰を表す補助変数 |
| No-good | 禁止する変数組合せを表す制約 |
| NOT_EVALUABLE | 構造上replay等を評価できない状態。有効や単純な違反とは別 |
| Repetition | 固定された乱数の種対応で繰り返す1回の科学実験。shotとは異なる |
