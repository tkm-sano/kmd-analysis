# 経路1：資源の評価範囲

根拠：S各PROTOCOL.json、SOURCE_SNAPSHOT、P/B_RESOURCES_PER_FIT.csv、B_SAVED_RESOURCES_LONG.csv。実験環境S/ENVIRONMENT.jsonはPython3.11.15、NumPy2.2.5、SciPy1.15.3、Qiskit2.1.2/Aer0.17.2、Linux/x86_64・hostname hayate、worker内1thread、GPU/QPU実行false。記録は実験群単位であり、全fitのCPU機種・負荷・実行時刻が統一記録されているわけではない。

|要因分類|確認できること|採用しない推測・HOLD|
|---|---|---|
|問題符号化|旧A位置符号化はn²二値（3/4顧客で9/16）。B mirrorはfloor(n/2)二値方向、支持2^floor(n/2)。Groverはn!の全順列支持。activeは局所labelネットワーク|支持の情報量と実装論理量子ビット数は異なる。B全8設定に旧n²を当てはめない|
|アルゴリズム|mirror p2のcost phase/partial SWAP、Grover p2/p3のcost phase/projector mixer、active p3の隣接parity SWAP。8192shots/測定rep×10、3680fit|layer数pはcompiled depthではない。COBYLAのmaxiterは関数呼出制限、実反復数ではない|
|計算アーキテクチャ|mirror binary MPS bond≤256/cutoff1e−13（精度検査1e−14）、active label MPS rank64、Grover subset DP(n≤25)/certified MC(n>25)|two_site_gates、QR_moves、DP/MC samples等はbackend処理回数。nativeゲート数へ換算しない|
|ハードウェア|CPUの理想化/数値誤差制御シミュレーション。保存hardware_qubits/compiled_gate_count/compiled_depthは未記録|native gate set・接続・noise・誤り訂正・物理量子ビット数・QPU秒はHOLD|

mirrorの二値方向はR0..R5で1/2/2/12/50/62。これを完成実装の論理qubit数とは呼ばない。元旧Grover構築には2n²−2という論理回路記述もあるが、現行staged p2/p3の補助qubit・状態準備・projector・展開回路まで同じ資源で実装された証拠ではないため現行必要量へ移植しない。

学習：mirror≤64 unique評価（basis9点またはcoherent12点＋2 COBYLA starts×24）、Grover≤68（2starts×32＋初期点、最終beta解析式）、active3grid（t0は解析的初期点、t.5/1を数値評価）。trace長はunique評価数、optimizer反復実数は全fit未保存。CVAR学習のみ1024shots/評価、Grover学習65,536 cost poolはQPU shotsではない。主系列は一学習fit当たり10測定反復。代表点の3学習seed再試行は全460の独立10学習とは異なる。

層・量子ビット・ゲート・shots・反復の依存は問題規模、支持、学習目的、精度、コンパイル先で変わる。現行保存値から一意の全学習回路shots総数、compiled資源、物理qubitを算定しない。Step2ではコードからの論理回路資源と実行backend工程の双方を分離して追加記録する候補とする。
