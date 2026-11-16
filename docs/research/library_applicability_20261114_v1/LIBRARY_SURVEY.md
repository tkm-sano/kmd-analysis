# 条件Dに対する量子ライブラリ調査

調査日: 2026-11-14 JST。対象は配送計画のD/W/T。EV・電池・量子化学の性能を配送最適化の証拠にしない。

**結論: Qiskitを継続し、Qulacsの最終状態発展とQURI Partsの実行抽象化を限定的な候補として扱う。Qamomileの全面移行を正当化する性能証拠は得られていない。** 詳細な実測と判定は [BENCHMARK_RESULTS](BENCHMARK_RESULTS.md)、[ADOPTION_DECISION](ADOPTION_DECISION.md)。

## 調査方法と時点

ルートAGENTS/README、ソース構成、依存lock、指定4モジュール群と関連config/testを探索し、コードの式・実行経路を直接読んだ。既存監査の記載を性能証拠には使っていない。ソースのSHA256は `evidence/preservation_before.json`、公式取得先・取得結果・SHA256は `evidence/sources_manifest.json` と `extended_sources_manifest.json` に保存した。外部mainの記述、安定版の実装、PyPI metadata、GitHub Releaseを分けた。保守状況は最終push/公開日という観測値であり、将来の保証ではない。

README冒頭は全体ソルバー未実装/HOLDと記載する一方、現在の `dwt/methods.py`、`parallel.py`、共通条件v1.1には実装がある。本文の過去EV研究と新ToC研究を区別した。本調査でREADMEは更新していない。実装入口は `scripts/run_dwt.py` / `scripts/run_dwt_bundle.py`、既定configは `dwt_balance_v1_4_cpu_parallel.json`。古い参考CVRP、vehicle_day小規模版、pipeline版、現在のDWTを一つの「現行D」として混ぜない。

## Qamomile

|項目|確認結果|
|---|---|
|主体|**Jij Inc. / Jij-Inc**。QunaSys製ライブラリとは区別する。[公式リポジトリ](https://github.com/Jij-Inc/Qamomile)|
|最新安定版|PyPI **0.15.2**、2026-10-30公開。GitHub安定タグv0.15.2。新しいpre-release **v0.16.0-rc.1**は2026-11-02。安定版と混同しない。[PyPI JSON](https://pypi.org/pypi/qamomile/json)、[Release API](https://api.github.com/repos/Jij-Inc/Qamomile/releases?per_page=5)|
|Python|安定版 `>=3.11`。main `>=3.11,<4`。[安定版pyproject](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/pyproject.toml)|
|保守|非archive、観測した最終pushは2026-11-13T23:15:38Z。[repo API](https://api.github.com/repos/Jij-Inc/Qamomile)|
|ライセンス|Apache-2.0。[LICENSE](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/LICENSE.txt)|

安定版の提供機能と実装根拠:

- `BinaryModel` / `BinaryExpr` はQUBO、Ising、HUBO、binary/spin変換、energy評価を提供する。非連続変数番号を詰める機能があるため、配送顧客・時刻変数との対応を保存する必要がある。[model.py](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/binary_model/model.py)
- OMMX入力からの制約のペナルティ化・元問題へのdecodeを扱う。自動変換は既存ALiM式・ペナルティ重み・slackの扱いが同一である保証ではない。[converter.py](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/converter.py)
- `QAOAConverter` はIsing/HUBO cost circuit生成と結果decodeを提供する。標準回路はHで作るplus状態とX mixer。現行Dのone-hot depot初期状態・位置別exact ring XYの代用品にはそのまま使えない。[converter](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/qaoa.py)、[回路実装](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/circuit/algorithm/qaoa.py)
- `FQAOAConverter` は粒子数保存のFermionic QAOA。全レジスターの粒子数固定は位置ごとのone-hot、顧客重複禁止、車両容量とは別条件。初期状態とhoppingも既存XYと同一ではない。[FQAOA](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/fqaoa.py)、[回路](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/circuit/algorithm/fqaoa.py)
- QRAO（QRAC複数方式とrounding）、PCE、GAS、QSVT eigenstate filter等の最適化モジュールが存在する。例えばQRAOは緩和Hamiltonianとroundingを変えるので、同一QAOAnsatzのライブラリ比較から外れる。配送D/W/Tへの改善は未測定。[optimization](https://github.com/Jij-Inc/Qamomile/tree/v0.15.2/qamomile/optimization)、[QRAC31](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/qrao/qrao31.py)
- 型付き `qkernel`、IR、資源解析、複数SDKへのtranspileとexecutorがある。安定版の公式導入例はQiskit、QURI Parts、CUDA-Q、Braket、qBraid、HUGR等。これはライブラリ単体が量子ハードウェアを提供する意味ではない。[安定版README](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/README.md)

**版による相違:** mainはPythonからRust所有のQCoreへコンパイルする構成と `qm.build/specialize/compile/submit/run` を説明する。安定版0.15.2の `qamomile.circuit` / `QiskitTranspiler` ワークフローをmainの新APIへ読み替えない。mainのCirq/Reference/QIR等の説明も、今回インストールした安定版の実測機能としない。[main README](https://github.com/Jij-Inc/Qamomile/blob/main/README.md)、[main pyproject](https://github.com/Jij-Inc/Qamomile/blob/main/pyproject.toml)

**Qiskit併用:** 安定版の公式 `qiskit` extraは `qiskit>=2.3.0,<3`、Aer、IBM Runtimeを要求する。研究の履歴lockのQiskit2.1.1をそのまま保った公式extra導入は不可。本調査ではextraを入れず、BinaryModelだけを既存Ising回路へ接続する限定アダプターを実測した。QURI Partsへの標準QAOA transpile/実行確認は別試験であり、同等XY回路の性能比較とは区別した。

**テスト・例・ベンチマーク:** upstreamにはbinary/spin energy、HUBO QAOA、decode、FQAOA/QRAO、QURI seed等のテストがあり、MaxCut/graph partitionやOMMX quantum benchmarks連携例がある。これらは本配送問題の2便・バース付きday PricingやS1〜S3の性能ベンチマークではない。[tests](https://github.com/Jij-Inc/Qamomile/tree/v0.15.2/tests/optimization)、[seed tests](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/tests/quri_parts/test_seed.py)、[benchmark連携例](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/docs/en/integration/ommx_quantum_benchmarks_qaoa.py)

**提供を確認できなかった機能:** この研究のRMP、全資源双対入りのday Pricing、積込バースと勤務制約を同時に満たす車両2便日程の自動生成、S1〜S3向けの全域経路生成、負RCの完全探索証明。これらをQamomile導入効果として数えない。

## QunaSys関連の公開ライブラリ

QunaSysの [公式サービス](https://qunasys.com/en/services/)、[QURI公表](https://qunasys.com/en/news/posts/quri-parts-release/)、[公式organization API](https://api.github.com/orgs/QunaSys/repos?per_page=100)、[QURI SDK構成](https://quri-sdk.qunasys.com/docs/concepts/overview/)を起点に、下記の具体名を確認した。

### 主要候補

|名称・公式URL|主体・用途|公開・保守・版/Python|QAOA・Qiskit・backend|license / 条件Dでの役割|
|---|---|---|---|---|
|[QURI SDK](https://github.com/QunaSys/quri-sdk)|QunaSys。Parts/Algo/VMの互換版を束ねるmeta package|0.28.0、2026-10-29。Python>=3.10,<4。repo push 2026-11-13、非archive|実行抽象化全体。配送solverは含まない|構成別license。条件Dの全面置換理由はない|
|[QURI Parts](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-parts)|QunaSys。回路・状態・Pauli演算子・sampler・estimator・transpiler・NISQ optimizer|0.28.0。同上。旧 `QunaSys/quri-parts` はSDKへ統合/転送|自作のIsing cost＋XY unitaryが可能。quri-parts-qulacs/Qiskit/Braket/Cirq等の接続。Cirqは回路/演算子変換と実行を区別する|Apache-2.0。工程4〜5の表現と実行、既存検証への出力接続|
|[Qulacs](https://github.com/qulacs/qulacs)|QunaSys・大阪大学・NTT・富士通の共同開発。C++/Python状態ベクトル/ノイズ/parametric回路|0.6.14、2026-07-29。push 2026-11-02、非archive。PyPI requires_pythonは**未指定**、本検証Python3.11で動作|任意unitaryとPauli rotationで現行AOAを実行可能。直接API、QURI adapter。直接Qiskit回路の無変更実行を提供するとはしない|MIT。最終Statevector発展の置換候補。CPUで実測。GPU版は未測定|
|[quri-parts-qulacs](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-parts/packages/qulacs)|QunaSys。QURI回路→Qulacs、状態・sampler/estimator|0.28.0、Python>=3.10,<4|Qulacs CPUを実測。回路変換overheadも計時。native samplerはseed指定あり|Apache-2.0。複数backend比較が必要な場合の限定的な接続層|
|[quri-parts-qiskit](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-parts/packages/qiskit)|QunaSys。Qiskit回路/演算子変換とbackend/Runtime接続|0.28.0。Qiskit>=2.2,<2.6、Python>=3.10,<4|古いDojoにある「Qiskit実行未対応」は最新SDKには当てはめない。変換とbackendのソースあり|Apache-2.0。2.1.1とのresolver衝突を実測。今回は使用せず|
|[QURI Algo](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-algo)|QunaSys。時間発展factory、phase estimation、Hadamard test、QAQC等(E)FTQCアルゴリズム|0.28.0、Python>=3.10,<4。単独旧repoはarchive、SDK内が現行|QURI/VMによる実行。独自AOA実装は組めるが配送QAOA/Pricing一式を確認できない|MIT。現在の配送AOAに追加の必須役割なし|
|[QURI VM](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-vm)|QunaSys。アーキテクチャ/デバイス抽象、資源解析・推定|0.28.0、Python>=3.10,<4。旧repoはarchive|既定のideal simulationはQulacs。回路・ゲート数・深さ/想定latency等。デバイスモデルと実測実機時間は別|MIT。将来の資源感度分析候補。現在のT_program高速化は未測定|

版・公開日の一次資料: [SDK release](https://github.com/QunaSys/quri-sdk/releases/tag/v0.28.0)、[Parts PyPI](https://pypi.org/pypi/quri-parts/json)、[Qulacs PyPI](https://pypi.org/pypi/qulacs/json)、[SDK READMEとlicense区分](https://github.com/QunaSys/quri-sdk/blob/v0.28.0/README.md)、[VM説明](https://quri-sdk.qunasys.com/docs/tutorials/quri-vm/introduction)。

Partsのほかのbackend群にはStim、ITensor、TKet、IonQ、Quantinuum、OpenQASM、tensornetwork等がある（各subpackageの機能範囲は別々）。一般の非Clifford XY/Ising回路がStimだけで効率良く動くとはしない。CUDA/GPU、ノイズ、実機の性能は今回未測定。公式の一般回路benchmarkは配送day Pricingの根拠に転用しない。[Qulacs benchmarkの公開先](https://github.com/qulacs/benchmark-qulacs)

### 周辺・除外候補

|具体名・公式URL|確認した主体・公開/保守・license|用途・接続 / 今回の判定理由|
|---|---|---|
|[QURI Parts cuQuantum](https://github.com/QunaSys/quri-parts-cuquantum)|QunaSys org、非archive、push2026-07-17、Python>=3.10、Apache-2.0。sourceから導入。PyPI同名は404|QURI回路をNVIDIA cuQuantumへ接続するGPU候補。QiskitはQURI変換経由。CPU条件同一の本試験には入れず、GPU速度は未測定・継続調査|
|[QURI Parts QSCI](https://github.com/QunaSys/quri-parts-qsci)|QunaSys、非archive、push2026-08-18、Python>=3.10、**QSAL-1.0 (source available)**|量子選択配置間相互作用・Hamiltonian低エネルギー近似。QURIの化学例。公開ソースでもApache/MITと同一扱いしない。配送経路QAOAの置換根拠なし・不採用|
|[quri-parts-chem / pyscf / openfermion](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-parts/packages)|QunaSys SDK内の化学モジュール、同SDKの公開系列、Apache-2.0|電子積分・fermion-qubit mapping・化学ansatz。QURI backendを使用できても、配送制約を解くモジュールではない・不採用|
|[Quration / PyQret](https://github.com/QunaSys/quration)|QunaSys orgの**fork**。READMEはRIKEN企画、RIKEN/Fixstars開発と記載。push2026-10-19。core等MIT、algorithm generatorsは研究用途限定、externals別license。PyPI pyqret 1.1.0|FTQC回路コンパイル/資源推定、surface-code/lattice-surgery等。QURI qsubやQamomile mainの接続をQunaSys単独製・安定版の実証と誤認しない。現行CPU Pricing改善の証拠なし・継続調査は資源研究に限る|
|[Qurs](https://github.com/QunaSys/qurs)|QunaSys org、非archive、最終push2022-10-26、MIT|Rust実装Qulacs、single processor、Qulacs C依存。Qiskit直接接続は未確認。Python既存AOAへ足す合理的な利点なし・不採用|
|[Qulacs Visualizer / qulacsvis](https://github.com/QunaSys/qulacs-visualizer)|QunaSys orgのfork、非archive、push2026-01-06、MIT。PyPI0.7.6、Python>=3.9|Qulacs回路可視化。最適化・samplerではない。図作成の役割に限られ今回導入不要|
|[qiskit-qube-backend](https://github.com/QunaSys/qiskit-qube-backend)|QunaSys、非archive、push2024-01-12、Apache-2.0|QuBE校正・pulse接続の試作。Qiskit Dynamics例。配送AOA向け本番実機アクセスや高速simulationの根拠なし・不採用|
|[ActiveSpaceFinder](https://github.com/QunaSys/ActiveSpaceFinder)|QunaSysのmodified fork。README上の開発主体HQS Quantum Simulations、Apache-2.0。push2025-01-07|分子の活性軌道選択、PySCF/BLOCK等。配送と直接関連なし・不採用|
|[QURI / QURI Chemistry](https://qunasys.com/en/news/posts/fldp4xshu-5b/)|QunaSysの化学Webサービス/Qiskit Functions。一般公開OSS libraryのlicenseは未確認|IBM接続の存在を配送solver提供と同一視しない。契約付き化学サービスを本CPU試験へ導入しない・不採用|

[QSCIの公式説明とlicense](https://quri-sdk.qunasys.com/docs/howto/applying_algorithms/quantum_selected_configuration_interaction.html)。周辺repoのmetadata/README/licenseはevidenceにも保存済み。push日だけで放棄・安全・高速を断定しない。

追加照合した [Quket](https://github.com/quket/quket) は電子Hamiltonian emulator（Apache-2.0、最終push2022-09-16）、[QuantestPy](https://github.com/QuantestPy/quantestpy) は量子回路検証（PyPI0.1.2、Apache-2.0）。今回の公式資料からQunaSysの現行提供物と断定する根拠は**未確認**。前者は配送目的外、後者も現行Qiskit/テンソル同値検査に対する追加の有効性が未実証で、採用対象に含めない。

## Huangらとの直接関係

[Huangら (2025), arXiv:2503.17051v1, §IV](https://arxiv.org/html/2503.17051v1) は、**Hamiltonian構築/ALiMにQamomile、アルゴリズム実装にQURI Partsを使用した**と記載している。したがって両ライブラリと「量子で新経路を生成する列生成」の技術的・文献上の整合性はある。ただし論文の小規模CVRP（最大6顧客）、one-hot XY、COBYLA/1000 shotsの証拠は、本研究の複数車両2便・積込バース・D/W/Tや最新ライブラリ版の優越性を示さない。論文で使用した依存版・本配送問題との同条件性能は未確認。本調査の既存Qiskitは独立実装で、著者の実装を同一再現したという扱いにしない。
