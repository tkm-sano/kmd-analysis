# VRPTWからEVRPへ：Structured Initial State研究の目的・現在地・次の実験

更新日：2026-09-22 JST。研究者本人が判断の流れを読み直すためのガイドである。

> **今どこにいるか：VRPTW Structured scientific sampling開始直前である。**
>
> 完了：VRPTWの定式化・古典参照・Uniform Standard QAOA study、道路経路の検証・可視化、Candidate Aのoffline validation、direct-build検証、clean Git baseline、NFS4 ledger lock検証。  
> 未実施：Structured S01／S02／S03のscientific sampling、EVRP、EV電力消費・経済評価。  
> 次：**S01 N003 WIDE × 3 repetitions**を、改めてfresh gateから開始する。  
> 科学コードbaseline：`6ccbadbd42bdad6c95e22f7420aff6ee787c8997`。この文書は実験開始の指示ではない。

このガイドの数値は既存成果物を読んだ記録である。以下では、**確認済みの事実・次に実行するfreeze済み計画・将来の設計案**を区別する。将来案を現在の実装・検証結果として読んではならない。末尾の参照案内はローカルartifactの所在も示す。

## 1. この研究で何をしたいのか

**要点。** 需要条件の変化が配送計画を通じてEV運用や経済的結果へどう波及するかを、段階ごとに検証可能な形でつなぐことが研究全体の目的である。

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

現在はこのうち**配送最適化のVRPTW baseline／structured initialization validation**にいる。量子計算は配送問題を解く候補手段であり、量子優位性や実運用での便益を前提としない。

**なぜ重要か。** 最終的な電力・経済指標だけを先に計算しても、その入力となる配送ルートが制約を満たさなければ意味が変わってしまう。まずルートの正しさ、解法の挙動、計算資源、結果の再現性を分けて検証する必要がある。

**現在の結論。** 最終的な連鎖は研究の目標であり、現時点で電力削減や経済的利益を検証したわけではない。

## 2. 現在はEVRPではなくVRPTWである

VRPTW（Vehicle Routing Problem with Time Windows）は、時間窓付き配送経路問題である。現在のモデルは次を扱う。

| 現在扱うもの | 意味 |
|---|---|
| Customer visit | 必要な顧客訪問を満たすこと |
| Vehicle capacity | 車両の配送容量を超えないこと |
| Depot | 出発・帰着地点とその扱い |
| Route／slot structure | 車両・訪問順序・割当ての整合 |
| Time Window | 顧客サービス開始等の許容時刻に関する既存ルール |
| Travel time／reachability | 保存済みOD移動時間と道路到達可能性をauthorityにすること |

まだ扱っていないのは、battery capacity、SOC、charging station、charging decision、charging time、EV electrical energy consumptionである。**車両容量は配送物の容量であり、バッテリー容量ではない。** 到達可能な道路経路があることと、バッテリー残量で走り切れることも別である。

## 3. CVRP・VRPTW・EVRPの関係

| 段階 | 加わる主な制約・状態 | この研究での位置づけ |
|---|---|---|
| CVRP | 顧客訪問・配送容量・経路 | Structured設計原理の出発点 |
| VRPTW | CVRPにTime Windowを追加 | 現在の検証対象 |
| EVRP／EVRPTW | バッテリー・SOC・充電等を追加 | VRPTW結果freeze後の将来フェーズ |

```text
CVRP ──＋Time Window──> VRPTW ──＋Battery / SOC / Charging──> EVRPTW
```

EVRPは電気自動車を扱う配送経路問題の総称として用い、Time Windowも維持する拡張はEVRPTWと区別できる。現在はCVRP由来のCandidate Aを既存VRPTW encodingへ移植し、その適用範囲と限界を調べている。

## 4. Uniform initial stateとは何か

Uniform initial stateは、一様な初期状態である。全qubit数を (N) とすると、例えば

$$
|+\rangle^{\otimes N}
=2^{-N/2}\sum_{x\in\{0,1\}^N}|x\rangle
$$

のように、すべてのbitstringへ等しい初期振幅を与える。ここで (N) は顧客数 (n) ではなく、slack等を含む全qubit数である。

Uniformは意図的な**比較baseline**であり、実装ミスではない。既存B01／B02／B03は、Uniform＋Standard X mixerを評価したfreeze済みの比較参照である。

既存Standard studyは7 nominal conditions・21 repetitionsを実行済みであり、今回のsmall-condition設定ではfinal samplingからfeasible／optimal sampleを観測しなかった。これは確率が厳密に0であることや、QAOAでVRPTWを解けないことの証明ではない。

後に問題になったのは、Structured workerが一度Uniform回路を構築してから初期層を置き換えていた**構築経路**である。Uniform baselineの研究上の役割とは区別する必要がある。

## 5. Structured initial state／Candidate Aとは何か

Structured initial stateは、問題の構造を初期状態に反映する設計である。Candidate Aの既存名称は次である。

```text
minimal integer visit/slot route word
+
uniform capacity slack
```

直感的には、訪問・slotを表すroute registerには既存の決定的な規則で1つのroute wordを置き、容量制約の余剰を表すslack registerには一様な重ね合わせを置く方式である。すべての有効ルートを重ね合わせる方式ではない。

完全に無構造なbitstring空間から開始するのでなく、routeとして意味のある構造を初期状態に持たせる発想である。ただし、**容量slackは一様であり、需要に適合する値だけを選別していない。**

constructionへ渡す入力は、顧客数`n`、車両数`m`、freeze済みvariable orderの3つだけである。最適解、feasible解の一覧、objective／energy ranking、sampled result、temporal feasibility、no-good satisfactionは使用しない。需要やTime Windowを用いて新たなroute wordを選び直すこともしない。

これはknown-solution leakage、すなわち答えに関する情報を初期状態へ埋め込んで比較を有利にしてしまうことを避けるためである。exact feasible／optimal setsは**生成後の診断**にのみ用いる。

## 6. Candidate Aで何が保証され、何が保証されないか

**確認済みの範囲。** 今回の3群では、Structured初期分布のvisit-valid、route-valid、physical-capacity-valid、depot-valid massはいずれも1である。一方、capacity-encoding-valid massはN002 WIDE／N003 WIDE／N002 active-TWの順に`1/256`、`1/16`、`1/256`である。

physical capacity-validは復元された配送ルートの容量充足を意味し、capacity-encoding-validはslackを含む符号化上の整合を意味する。この2つは同じ指標ではない。今回のinstanceでphysical capacity-valid massが1だったことを、任意の需要・容量に対する一般保証へ拡張してはならない。constructorは需要・容量を入力していないためである。

active-TWでは、さらに次が成立する。

```text
initial feasible mass = 0
initial temporal-valid mass = 0
initial no-good violation mass = 1
```

つまり、route構造が有効でもTime Windowまで満たすとは限らない。**Encoding compatibility PASS ≠ temporal feasibility PASS**である。no-goodとは、許されない組合せをpenaltyとして表現する既存の制約である。

この限界を理由にsupportを刈り込んだり、feasible routeを挿入したりはしない。既存CVRP由来の設計をそのまま持ち込んだときの挙動を比較することが、次の実験の問いである。また、初期状態で成り立つ構造がStandard X mixerによるQAOA evolution後も保存されるとは限らない。

## 7. Offline validationで確認したこと

以下は**初期状態の確率分布の診断**であり、optimizer実行後のQAOA performanceではない。massは対象state集合にある確率の総和、supportは非ゼロ振幅を持つbasis statesの数である。

| 独立QUBO群 | Structured support | Feasible initial mass | Optimal initial mass | Mean nearest-feasible distance：Uniform → Structured | Temporal-valid mass（Structured） |
|---|---:|---:|---:|---:|---:|
| N002 WIDE | 256 | 0.00390625 | 0.00390625 | 7.45343017578125 → 4 | 1 |
| N003 WIDE | 16 | 0.0625 | 0 | 6.171875 → 2 | 1 |
| N002 active-TW | 256 | 0 | 0 | 8.90625 → 7.875 | 0 |

Nearest-feasible Hamming distanceは、bitstringからそのconditionのfeasible-state setまでの最小bit反転数である。異なるTime Windowでは参照集合も異なり得るため、異なるregime間の数値を単純な性能順位にしてはならない。

normalization、support、variable order、circuit/statevector fidelity、WIDE回帰、active-TW encoding compatibility、waiting-label independence、leakageを確認済みである。v2では準備回路のfidelityが数値誤差内で1、最大振幅誤差が`1e-16`未満であった。

さらに、固定route registerを持つため、今回のp=1構造ではroute marginalがgammaに依存しないという限界も記録済みである。slack側のparameter sensitivityや正のenergy varianceだけから、route探索が改善すると結論してはならない。

**現在の結論。** 意図したCandidate Aを数学的・実装的に生成できることを確認した段階である。特にN003は既存一般規則のstatic regressionであり、過去CVRP scientific executionでN003の改善を直接確認したconditionではない。

## 8. Direct-build問題とは何だったか

旧実装は次の順だった。

```text
Uniform full circuitを構築
  ↓
initial H layerをCandidate Aへ置換
```

これは「Uniform circuitを再生成しない」というcomparison条件に抵触した。sampling条件が違っていたと断定する問題ではなく、禁止された構築経路を使い、初期状態だけを差分とする構造を実装上明示できていなかった問題である。そのためscientific sampling前にSTOPした。

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

costはQUBOを反映する層、mixerは状態間の振幅を変化させる層である。両armのQAOA bodyを共有し、Structured側に別のcost／mixer実装を複製しない。v4ではUniform full／initial builderの呼び出しが0、保存済みUniform回路とのbody・parameter・measurement対応が一致し、144テストがPASSした。

## 9. Git clean baselineを作った理由

実験の再現には「どの設定だったか」に加え、「どのコードを使ったか」が必要である。working treeがdirtyだと、同じcommit名でも実際のコードが異なり得る。

そこで実行に必要なvalidated codeと依存コードをcommitし、無関係な過去作業をstashとarchiveへ保全した。削除やhistory rewriteでcleanにしたわけではない。以前のbaselineは次である。

```text
94a0fbe73c26149414f0692d3f117d7fcb4dbb9d
```

この分離により、実験時点のコードを一意に指し、実験途中の変更を検知できる。ただしGit commitだけですべてが復元できるわけではない。scientific outputsや一部authorityはrepository policy上ローカル管理であり、hash固定済みartifact bundleと実行環境も必要である。

## 10. NFS4 ledger lock問題とは何だったか

S01のfresh gateはPASSしたが、ledger初期化で次の問題が生じた。

```text
専用lock fileをread-only（rb）で開く
  ＋ exclusive flock
  ＋ 現在のNFS4 filesystem
  → EBADF（Bad file descriptor）
```

ledgerはcircuits・shots・予約・消費を管理する台帳である。排他lockは、複数processが同時に予約して二重計上や過剰予約を起こすことを防ぐ。

修正は専用lockファイルの`rb → r+b`である。ファイルを新規作成・切り詰めず、書込み可能なdescriptorで排他lockを取得する。ledger本体、accounting semantics、atomic writeは変更していない。

v6では実S01パス上で取得・解放・再取得を確認し、同じNFS4上のsynthetic test ledgerで2 processの排他、更新保持、重複予約拒否、例外後の整合性を確認した。104テストがPASSした。これは現在の環境と試験範囲での確認であり、すべてのNFS環境や複数hostの障害回復を保証するものではない。

**重要な区別。** このSTOPもr0、reservation、optimizer、backend samplingより前であり、scientific circuits／shotsは0である。実装・基盤の失敗を、Structuredの科学的性能が悪かったという結果へ読み替えてはならない。

## 11. 現在のclean scientific baseline

確認済みの科学コードbaselineは次である。

```text
6ccbadbd42bdad6c95e22f7420aff6ee787c8997
```

現在のstatusは次である。

```text
VRPTW_S01_LEDGER_LOCK_NFS4_PREFLIGHT_VALIDATED
VRPTW_PRE_S01_GIT_BASELINE_V2_FROZEN
```

| 台帳上の値 | 現在値 |
|---|---:|
| Historical scientific circuits | 363 |
| Historical scientific shots | 743,424 |
| Scientific reserved | 0 |
| Sanity circuits（別枠） | 7 |
| S01 scientific repetitions試行／完了 | 0／0 |
| S01 circuits／shots／optimizer evaluations | 0／0／0 |

363 circuitsは過去のStandard studyの累積であり、S01で消費した数ではない。今回の文書作成もscientific stateを変更しない。

**文書commitと科学baselineの区別。** この文書をcommitするとGit HEADは上記SHAより先へ進むが、検証済み科学コードbaselineを変更したことにはならない。次のcontrolled launchで指定されたHEADと実際のHEADの照合はfresh gateで行い、不一致を暗黙に許容したりbaseline manifestを書き換えたりしてはならない。

## 12. S01・S02・S03とは何か

| Stage | Condition | Repetitions | Uniform reference | 目的 |
|---|---|---:|---|---|
| S01 | N003 WIDE（G2） | 3 | B02 | 最初のcontrolled scientific launchと実行整合性確認 |
| S02 | N002 WIDE（G1） | 3 | B01 | 別サイズのWIDE条件で確認 |
| S03 | N002 active-TW／MODERATE（G3） | 3 | B03 | 時間制約がbindingする条件で適用範囲・限界を確認 |

代表condition IDはそれぞれ`R24-RND-N003-R01-RHO050-TW-WIDE`、`R24-RND-N002-R01-RHO050-TW-WIDE`、`R24-RND-N002-R01-RHO050-TW-MODERATE`である。

既存7 nominal conditionsは、B01↔B06、B02↔B07、B03↔B04↔B05という3つのsame-QUBO／same-seed群へ整理済みである。これらを7つの独立sampling evidenceとして二重計上しない。「3 independent QUBO groups」は重複を除いた設計単位であり、群間の統計的独立性を保証する表現ではない。

Structuredも3群を基本単位とし、waiting等のlabel差はindependent temporal replayで扱う。waiting labelだけで別initial stateを作らない。**S01→S02→S03は自動進行せず、各batchでSTOP・validation・次タスクの明示的指示を必要とする。**

## 13. なぜUniformとStructuredを比較するのか

研究問いは、初期状態にroute構造と既存のslack構造を与えたとき、Uniform initializationに比べてQAOAのsampling behaviorがどう変わるか、である。

過去CVRPではfeasibility・distance・structural validityの改善が3 basesで再現した一方、optimalityは一貫せず2 basesで改善、1 baseで悪化したと記録されている。これをVRPTW全般の性能保証に拡張せず、移植先で検証する必要がある。

比較は**initial stateの意味と限界を調べるbaseline／ablation comparison**である。Uniformは除去すべき間違いではない。既存Uniform結果をread-onlyで再利用し、再samplingしない。

初期状態以外は同じQUBO、variable order、cost、Standard X mixer、`p=1`、COBYLA、shots、paired seed policy、transpilation、validator、metricsを維持する。COBYLAはmaxiter 100、rhobeg 0.25、tol 0.01、catol `1e-8`、external training cap 99である。training／finalは各2048 shots、初期alphaは`0.5262887849165184`、betaは`0.37`、scaleは`52628.87849165184`である。

同一seedを対応させても、異なる回路が完全に同一の乱数過程をたどるとは主張しない。各群3 repetitionsを科学的単位とし、shotsを独立実験数として扱わない。主解析はpaired differencesと記述統計である。

## 14. 何を比較するのか

| 軸 | 比較するもの | 読み違えを避ける点 |
|---|---|---|
| Solution quality | Feasible／optimal rate、feasible route objective、gap | Feasibleであることとoptimalであることは別 |
| Constraint satisfaction | Visit、route、depot、physical capacity、capacity encoding、temporal validity | 復元不能はNOT_EVALUABLEとし、validや単純な違反へ混ぜない |
| Quantum optimization behavior | QUBO energy、収束履歴、sampling distribution、nearest-feasible distance | 低energyだけで良いルートとしない |
| Resource | Circuits、shots、depth、CX、optimizer evaluations、runtime、RSS | Sampling改善と追加resource costを別々に報告 |

feasible sampleが0の場合、best feasible objectiveやgapに0を入れず、null／not evaluableとする。waitingは到着後サービス開始までの待ちであり、それ自体は違反ではない。

active-TWでStructuredからfeasible sampleが出れば、初期振幅0のfeasible statesへevolution後に確率massが移った可能性を調べる。出なければ、それも変更せず記録する。temporal-validだけの改善、energyだけの改善、overall feasibilityの改善は別の結果である。どの場合も結果を見てCandidate Aを再設計しない。

## 15. QUBO energyとEV電力消費は違う

QUBOはQuadratic Unconstrained Binary Optimization、すなわち二値変数の二次式を最適化する表現である。現在のenergyは**QUBO／Hamiltonian energy**であり、routing termと各constraint penaltyを含む最適化上の量である。

$$
\text{低いQUBO energy}\not\Rightarrow\text{feasible route}
$$

$$
\text{QUBO energy}\neq\text{EVの電力消費量（kWh）}
$$

現在はEV電力モデル自体がないため、QUBO energy低下を省電力・充電削減・経済利益へ換算してはならない。

## 16. S01で次に何をするのか

次のscientific taskは**N003 WIDE／Structured × 3 repetitions**だけである。

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

r0のperformanceが悪いことはSTOP理由ではない。freeze violation、ledger mismatch、wrong seed／QUBO／shots、output corruption、resource／backend異常等がSTOP理由である。technical failureでも勝手にretryせず、既存policyに従い記録・停止する。

S01最大は`3 × (99 training + 1 final) = 300 circuits`、614,400 shotsである。未使用予約を消費するための追加runはしない。S01完了はN003 WIDEのbatch完了であり、Structuredの一般的優越性やVRPTW全体の完了を意味しない。

## 17. VRPTW終了後は何をするのか

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

ここで初めて、WIDEでのtransferとactive-TWでの限界をまとめる。対象は小規模instance、限られたbases、Uniform／Candidate A、Standard X、p=1という範囲である。large-instance performance、quantum advantage、real-world deployment価値は未検証である。

道路networkへの接続基盤は既にclassical exact／proven-optimal MILP routeをauthorityとしてmaterialize・validate・visualize済みである。これはQAOAがそのルートをsampleした証拠ではない。既存成果物を保持し、将来のEVRPで利用できる経路表現として位置づける。

## 18. その後の最小EVRP

**以下は将来の設計案であり、今回freeze・実装・検証した仕様ではない。** VRPTW結果freeze後に、battery capacity、SOC、充電判断、充電時間、energy consumptionを初めて導入する。

最初のenergy baseline候補は距離比例モデルである。

$$
E_{ij}=r\,d_{ij}
$$

(d_{ij}) は移動距離、(r) は単位距離当たり電力消費、(E_{ij}) はその移動の電力消費である。例えば距離をkm、(r)をkWh/kmで定義すれば結果はkWhとなる。係数、単位、vehicle条件、SOC更新、充電rate・場所・利用条件・Time Windowとの関係は、次フェーズで別途設計・検証する。数式だけでEVRPが完成するわけではない。

## 19. なぜ最初は距離比例でよいのか

距離比例で十分に現実を説明できると主張するためではない。**EV制約追加の影響とenergy model高度化の影響を分離するための単純なbaseline案**だからである。

最初からspeed、payload、gradient、acceleration、regenerative braking、trafficをすべて導入すると、結果差の原因と入力データの不確実性を追いにくくなる。

```text
VRPTW：配送・時間制約
  ↓
EVRP-1：distance-proportional energy＋最小の電池・充電制約
  ↓
EVRP-2：road-edge-level energy modelの詳細化
```

各段階で同一入力に対するvalidationと比較条件を設ける方針案である。現時点ではEVRP-1も未実施である。

## 20. 将来のroad-edge-level energy model

将来は、道路edgeごとの走行条件を使うモデルを検討する。

$$
E_{ij}=f(d_{ij},v_{ij},t_{ij},\mathrm{payload},\mathrm{gradient},\mathrm{acceleration})
$$

ここで式の添字をstop間legとする場合、その内側でroad-edge単位の量を積み上げる必要がある。速度・勾配・加減速等を表現できるデータと、係数・単位・calibration／validation authorityは別途必要である。既存distance／travel timeだけから未保存の車両挙動を推測して補わない。

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

この図は研究フェーズの接続であり、量子解法が唯一のrouting authorityになるという意味ではない。古典参照とindependent validatorを保持し、配送解の正しさとその先の電力・経済モデルの正しさを段階ごとに確認する。

**次にすることはS01である。** 現在のreadinessは実行を許可できる準備状態を表すだけであり、sampling完了や科学的優越性を意味しない。

## 参照案内：どの記録を読めばよいか

次のパスはrepository rootからの相対パスである。`reproducibility/outputs/`以下はローカル管理を含むため、GitHub上の文書だけをcloneしても全artifactが揃うとは限らない。更新されたコードreceiptと過去の結果receiptも区別する。

| 確認したいこと | Authority／参照先 |
|---|---|
| 初期状態の数値・限界 | `reproducibility/outputs/traffic_simulation/r24_vrptw_structured_initial_state/20260922_v2/DESIGN_VALIDATION_REPORT.md` |
| 初回worker統合（旧構築経路） | 同上rootの`20260922_v3_implementation_preflight/IMPLEMENTATION_PREFLIGHT_REPORT.md` |
| Direct-build検証 | 同上rootの`20260922_v4_direct_build_preflight/DIRECT_BUILD_PREFLIGHT_REPORT.md` |
| 過去作業の保全・旧baseline | 同上rootの`20260922_v5_pre_s01_git_baseline/GIT_CLEANUP_REPORT.md`、`PRE_S01_GIT_BASELINE.json` |
| NFS4によるS01実行前STOP | 同上rootの`20260922_s01_n003_wide_controlled_launch_v2/S01_EXECUTION_REPORT.md` |
| 現行lock検証・新baseline | 同上rootの`20260922_v6_ledger_lock_preflight/LEDGER_LOCK_PREFLIGHT_REPORT.md`、`PRE_S01_BASELINE_V2.json` |
| 比較条件のfreeze | `reproducibility/outputs/traffic_simulation/r24_vrptw_uniform_vs_structured_comparison_spec/20260922_v1/` |
| Standard studyと重複除外 | `reproducibility/outputs/traffic_simulation/r24_vrptw_qaoa_execution/20260921_v1/study_synthesis/SCIENTIFIC_FINDINGS.json` |
| Classical道路経路のauthority | `reproducibility/outputs/traffic_simulation/r24_vrptw_road_network_routes/20260921_v1/EXECUTION_SUMMARY.json` |
| Historical scientific ledger | `reproducibility/outputs/traffic_simulation/r24_vrptw_qaoa_scientific/20260921_v1/CIRCUIT_RESERVATION_LEDGER.json` |

コードの入口は[Candidate A constructor](../../05_src/traffic_simulation/r24_vrptw_structured_initial_state/construction.py)、[Structured worker](../../05_src/traffic_simulation/r24_vrptw_structured_worker/worker.py)、[shared QAOA body](../../05_src/traffic_simulation/r24_vrptw_qaoa_worker/circuit.py)、[ledger adapter](../../05_src/traffic_simulation/r24_vrptw_structured_worker/ledger.py)、[NFS4検証](../../05_src/traffic_simulation/r24_vrptw_ledger_lock_preflight/checks.py)である。背景の需要・データ設計は[2026-09-15時点の研究設計ガイド](R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)を参照する。そちらの「現在」は当時のCVRP段階を指す。

## 用語集

| 用語 | この研究での意味 |
|---|---|
| CVRP | 配送容量制約付き車両経路問題 |
| VRPTW | Time Window付き車両経路問題 |
| EVRP／EVRPTW | 電池・充電等を扱う電気自動車の経路問題／時間窓付き拡張 |
| QUBO | 二値変数の二次式による最適化表現。制約はpenaltyとして含む |
| QAOA | Quantum Approximate Optimization Algorithm。cost層とmixer層を用いる量子最適化手法 |
| Uniform initial state | 全bitstringへ等しい初期確率を与える一様状態 |
| Structured initial state | 問題構造を反映した初期状態 |
| Candidate A | 固定route word＋uniform capacity slackという今回選択済みの構築規則 |
| Feasible mass | すべての必要制約を満たすstate集合の確率総和 |
| Optimal mass | 古典参照の最適性定義を満たすstate集合の確率総和 |
| Temporal-valid mass | 独立temporal replayで時間条件を満たすstate集合の確率総和。NOT_EVALUABLEとは区別 |
| SOC | State of Charge。バッテリー残量の状態。現在のVRPTWには未導入 |
| Ledger | circuits・shotsの予約、開始、消費、失敗等を記録する永続台帳 |
| Freeze | 比較前に条件・authority・解釈ルール等を固定すること |
| Fresh gate | 実行直前にhash・設定・seed・resource・ledger等を再照合する検査 |
| Support | 非ゼロ振幅を持つbasis statesの集合 |
| Slack | 容量等の制約を符号化する際の余剰を表す補助変数 |
| No-good | 禁止する変数組合せを表す制約 |
| NOT_EVALUABLE | 構造上replay等を評価できない状態。validや単純な違反とは別 |
| Repetition | 固定されたseed対応で繰り返す1回の科学実験。shotとは異なる |
