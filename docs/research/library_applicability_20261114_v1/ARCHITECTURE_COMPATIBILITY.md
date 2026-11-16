# 条件Dのコード監査とアーキテクチャ適合性

調査日2026-11-14。**ライブラリの機能不足よりも、通常DWTで受理する経路ドメインと量子Pricingへの双対更新方法が、顧客集合を変える新経路生成を制限している。** 下記は現在の実装と設定を根拠とする。

## 直接確認した依存・実行経路

パスはリポジトリルート基準。ファイル内容の識別は `evidence/preservation_before.json` のSHA256を参照。

|箇所|実際の役割と根拠|
|---|---|
|[column_generation/aoa.py](../../../src/kmd_toc/column_generation/aoa.py):14–19, 183–200, 223–308|NumPyによる係数・tensor・乱数、SciPy expm/COBYLA、Qiskit QuantumCircuit/UnitaryGate/Statevector/transpile。Aer・実機・Runtimeは使用しない|
|[column_generation/master.py](../../../src/kmd_toc/column_generation/master.py):6以降|SciPy HiGHS linprogでcover/partition RMPと双対、milpで最終partition整数選択|
|[vehicle_day/master.py](../../../src/kmd_toc/vehicle_day/master.py):6以降|SciPy LP/IP。顧客・車両・バース・ε制約の行と双対、Phase I/II、真day RC整合性検査|
|[pipeline/hybrid.py](../../../src/kmd_toc/pipeline/hybrid.py):15–74, 103–128|sparse event interval master、HiGHS LP/IP。固定候補内で負RC列を追加しLPを再求解。整数解の補強・zero faceも古典処理|
|[pipeline/classical.py](../../../src/kmd_toc/pipeline/classical.py):40以降|OR-Tools Routing。Cのrouting pool生成|
|[pipeline/completion.py](../../../src/kmd_toc/pipeline/completion.py):58以降|OR-Tools CP-SAT。車両、1/2便、積込start、バース、勤務、ε制約付き共通完成処理|
|[dwt/methods.py](../../../src/kmd_toc/dwt/methods.py):71–107, 110以降|B/C/Dは各呼出し内でdirected CWを独立生成。Dは自分のseed completionからday初期列を作る。C/Bが保存した計画を読む処理はない。D内の古典CW共用関数は許容条件に合う|
|[dwt/setup.py](../../../src/kmd_toc/dwt/setup.py)|全方式共通のNumPy/SciPy/OR-Tools/Qiskit import準備。問題固有計算や需要読込はここにない|
|[dwt/parallel.py](../../../src/kmd_toc/dwt/parallel.py)、[worker.py](../../../src/kmd_toc/dwt/worker.py)|4プロセス内部multistart、各branchでnative threads1/affinity、seedと全候補の量子資源を集約|

`src/`, `configs/`, `tests/` 内でQamomile/QunaSys/QURI/Qulacsの既存実装利用は検索で見つからなかった。旧 `kmd_quantitative/quantum/protocol_v2/science.py` にもQiskit/SciPy利用があるが、旧EV研究とToC条件Dを混ぜない。依存定義はルートpyprojectではなく `reproducibility/environment/{huang_cg_aoa_v1,vehicle_day_v1}/requirements.lock.txt` 等を確認した。両参考環境はPython3.12.11、NumPy2.3.1/SciPy1.16.0/Qiskit2.1.1。通常DWTで必要なOR-Toolsも含め、今回の部品venvのfreezeを本番環境の同一性の証拠にしない。

## QAOAnsatzの実装

`PricingAOA` は地点i・位置tのone-hot binary変数を持つ。固定depot位置t=0は消去し、量子ビット数は **q=(顧客ノード数+depot)×(slots−1)**。各可変位置を最初はdepotの1にするXゲートから始める。

代理目的は巡回距離−各訪問顧客の双対に、`lambda_capacity*(h+h²)`（h=総需要−容量）と `lambda_visit*Σ_i n_i(n_i−1)` を加える。binaryのx²=xを用いて二次式を組み、x=(1−Z)/2でIsingにする（aoa.py:123–158）。容量項はALiM由来の誘導項であり、容量以下なら一律0となる通常の違反量ペナルティではない。例えばh=−2でも値2、h=−1/0で0となる。実行可能性はdecodeで別途判定する。

各p層はcostのRZ/RZZと、位置ごとの **exp(−iβH_XY)**。ringの隣接 `(XX+YY)/2` を密行列で正確に指数化した `UnitaryGate` を使う。隣接項の積による一回のTrotter近似とは同じでない。訓練はone-hot部分空間のテンソルで厳密に発展させ、NumPy multinomial 1000 shots/評価の期待値をSciPy COBYLAに渡す。**訓練ループはQiskit Statevectorを毎評価呼んでいない。** 最終角だけ全量Qiskit Statevectorで計算しtensorとの忠実度/漏出を検査、その後独立4096 shotsを抽出する（aoa.py:160–200, 223–285）。

現行既定は `configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json` の p=2/max_evaluations=80/restart=1/train1000/final4096、最大3断片、pricing_rounds=2、4 branches。一方参考 `huang_reference_v1.json` はmax200/restarts3、vehicle_day configはslots3であり別条件。クラスのガードq<=21、地点数<=7をライブラリ導入だけで取り払ってS1〜S3へ直接拡張できるとはしない。

`decode` は固定depot、空、顧客重複、容量を検査する。depotで区切ったwalkをtripへ分割できるが、自由車両CVRPでのRC加法性と、車両2便/バースを持つday RCの加法性は異なる。勤務や積込を量子bit列から自動保証する仕組みはない。

## 「新しい経路」の範囲と双対の接続

|実装|顧客集合・訪問順の自由度|双対・列生成の実態|
|---|---|---|
|`column_generation/runner.py` + PricingAOA|宣言した全小規模顧客/部分ドメイン内で異なる集合・順序を生成可能。slots制限あり|各反復LP→双対→量子候補→trip RCで負列追加→再LP。全列oracleは診断用で量子側へ注入しない|
|`vehicle_day/pricing.py` + runner|双対上位/近傍の最大3顧客を選ぶ古典ドメインから、量子が部分集合・順序を生成。測定tripを必ず含むdayを古典完成|各反復の全資源双対でday RCを再評価、負列追加、再LP。量子目的自体は距離/顧客双対の代理。有限grid・partnerの限界あり|
|`pipeline/hybrid.py:create_hybrid`|元の1 tripを最大3個の**向きを保った連続断片**に分け、その全断片の順列のみ採用|base LPの双対で量子を2round行い、全候補のday poolを作り直してCG。量子round間に新しいmaster双対を返していない|
|**通常 `dwt/methods.py:hybrid`**|同上。`len(small)==len(groups)` かつ全群一致のみ受理（255行）。最大3!=6順列。顧客集合の変更、群内順序変更、異なるseed trip間の顧客交換は量子生成の採用対象外|223行でbase LPの顧客双対を一度取得（失敗時0）。2round中に双対更新なし。量子後にpoolを拡張して有限day CGを再実行。pricing_roundsという名を完全な量子CG交互反復と解釈しない|

さらに通常DWTのfull fragment順列では、全候補が同じ顧客集合と総需要を持つため**顧客双対報酬と容量項は受理集合内では定数**になる（回路内で生じる未受理の部分集合の分布には影響する）。従って受理後の主な探索は既存trip内の断片順序であり、全顧客の車両割当を量子が同時に選ぶことにはならない。これはSDKの機能ではなくドメイン構成と受理条件の性質。

今回のselection部品試験は集合変更を実測するための既存小規模vehicle_day型の条件。macroとselectionの差をQURI/Qamomileへの移行効果と呼ばない。

## 11工程とライブラリ対応

凡例: 「自作」はそのSDKの回路部品を使って配送用に設計する必要がある。「なし」は配送工程の完成品として確認できない。Qulacsはsimulatorでありルート生成アルゴリズムを自動設計しない。

|工程|既存実装/現在の状態|Qamomile|QURI Parts / Qulacs|Algo / VM・周辺|
|---|---|---|---|---|
|1 初期経路/列|D内部CW、completion、make_day|直接機能なし|直接機能なし|なし|
|2 RMP|SciPy linprog/HiGHS|置換不要|置換不要|なし|
|3 双対取得|eqlin/ineqlin.marginals、符号検証|自動取得しない|自動取得しない|なし|
|4 QUBO/Ising|Polynomial、ALiM/unique、contract|BinaryModel/OMMX変換は併用可。自動penaltyと現行式の同値確認必須|Operator/Pauli表現。配送QUBO生成は自作|Algo時間発展部品は使えても配送定式化を提供しない|
|5 量子新経路|PricingAOAのone-hot XY|custom qkernelなら候補。標準QAOA/FQAOAは回路変更となる|同じXY回路の構築と状態発展を実測。Qulacs DenseMatrix対応|cuQuantumはGPU別検証、VMは実行/資源分析の候補|
|6 trip検証|decode→expand→validate|decodeは元問題評価の補助、独自配送制約は残す|標本返却後は既存検証|なし|
|7 day完成|make_day/enumerate_days、現在は有限calendar + CP-SAT|完成品なし|完成品なし|化学QSCI等は対象外|
|8 真RC|全顧客・車両・バース・ε双対|自動計算なし|自動計算なし|なし|
|9 有効列追加|未知day identityかつRC<−1e−7|既存ロジック保持|既存ロジック保持|なし|
|10 再RMP/双対更新|day/referenceは交互反復、DWTの量子stage内は未実装|制御フロー自作|制御フロー自作|なし|
|11 整数選択|milp/CP-SAT、二重検証|置換不要|置換不要|なし|

day列cの真RCは、Phase IIで `primary_cost(c) − Σ顧客dual − vehicle_dual(c) − Σ占有berth_dual − epsilon_dual*other_cost(c)`。Phase Iのcostは0。`vehicle_day/master.py:41–47` と `pipeline/hybrid.py:42–50` に対応。trip距離−顧客双対が負でも、勤務・日程完成不可、資源双対を加えると非負、同一列などの理由で追加できない。新ライブラリのcost値を真day RCとして代用しない。

## 計時範囲・ボトルネック

- `PricingAOA.run` のtotalは**オブジェクト初期化後**に開始し、RMP/contract/親処理を含まない。trainingはCOBYLAとテンソル/訓練shots。qiskit_secondsには回路構築・全量状態発展・同値確認・抽出・decodeが混在する。
- DWTは `TimedAOA.circuit` で回路構築を分けるが、`sampling_only_s=None`、残りはsimulation/sampling/decode合算。samplingだけの高速化を既存ログから断定できない。今回独立adapterで測った。
- 通常T_programは `parallel.py:226–315` の親common入力読込前→各枝完了/停止→全候補の再検証と選択→最終二重検証までのwall time。4枝の未選択計算・shotsも合算する。import/待機準備、出力、全batch時間は別記される。今回の部品時間をそのT_programに混ぜない。
- 小規模実測では学習がPricing kernelの大きい部分。最終Qiskit状態発展だけをQulacs化してもテンソル/COBYLAは変わらない。通常DWTではさらにCW/CP-SAT、有限day catalogue構築、LP/IP、検証、全枝協調があり、その割合は今回は未測定。
- 状態ベクトルは16×2^q bytes、訓練は n^(slots−1) one-hot状態。小ドメインではQiskit回路dispatchや密XY構築、QURI変換の固定費が目立つ。主因の順位は規模・ケースで変わり、大規模問題の時間/メモリ改善は未確認。

## 置換する場合の具体的差分（提案のみ）

1. `column_generation/aoa.py` の式/学習/decoderを保ち、最終回路構築・状態発展・標本処理をbackend interfaceへ分離する。Qulacsの場合、RZ/PauliRotationの符号、bit順、global phase、exact XYを同値検査する。QURI経由では変換時間も含める。
2. Qamomileを定式化だけに使うならPolynomial→BinaryModel→Isingの番号/定数対応を追加する。標準converterへの全面置換は行列/初期状態/探索空間を変更するので別アルゴリズムとして登録する。
3. `vehicle_day/pricing.py`、`pipeline/hybrid.py`、`dwt/methods.py` にbackend識別と候補由来を渡す。既存day completion/真RC/検証を保持する。Qiskit fidelityを毎回両backendで実行すると本番時間を相殺するため、検証頻度の方針を新条件として明示する。
4. `dwt/setup.py`, `worker.py`, `parallel.py`, `experiment.py` の共通import、バージョン、全枝seed/shots/PID/affinity/失敗の記録を拡張する。別の環境lockと明示的な新configを作り、旧条件・結果を残す。
5. 顧客集合を変えたい場合は、以上と別にドメイン生成/受理条件と量子CG反復を設計する。SDK変更だけで達成したと記録しない。

**この調査ではこれら本番ファイルを変更していない。** 独立実装は `code/benchmark.py` に限定した。
