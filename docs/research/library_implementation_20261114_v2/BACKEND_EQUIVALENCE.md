# バックエンド数値同等性

2026-11-14。前回成果は `../library_applicability_20261114_v1/` に保全し、142件のartifact hash一致を再確認した。前回の40測定/24状態検査は背景証拠として再利用し、今回の時間統計へ混ぜない。

今回、同じPricingAOAのHamiltonian、ALiM、customer_unique penalty、depot one-hot初期状態、位置別exact ring XY、同じ固定角をQiskit・Qulacs直接・QURI Parts→Qulacsで実行した。**3構成は検証範囲でグローバル位相を除き数値的に同等だった。**

## 検査範囲と誤差

地点数(depot込み)3/4、slots3/5、p1/2/4の12条件、3構成、warm-up1＋測定7の計288状態を検査した。q6/8/12/16。全2^qビット列の確率分布を比較し、one-hot外の漏出も含めた。期待値は厳密one-hotのenergy配列と標本抽出前の確率から求めた。

|指標|許容誤差|観測最大|
|---|---:|---:|
|abs(1−fidelity)|1.0e-08|7.1054e-15|
|phase_aligned_max_abs|1.0e-09|3.4844e-15|
|probability_max_abs|1.0e-09|3.3584e-15|
|probability_L1|1.0e-09|1.3116e-14|
|expectation_abs|1.0e-08|6.4837e-14|
|leakage|1.0e-08|2.4425e-15|

位相調整はoverlap `<reference|other>` の偏角を除いた最大複素振幅差。Qiskit原回路は定数Hamiltonianのglobal_phaseを入れるが、Qulacs/QURIの回路はその状態全体位相を省略する。物理的確率/期待値の差として扱わない。

## ゲート・bit対応

- indexは `b = position_block*n + node`、整数maskのbit bがqubit b。表示bitstringは幅q、左が高位、右がqubit0。標本列を逆順にして顧客IDへ渡さない。
- Qiskit RZ/RZZは `exp(−i angle*P/2)`。Qulacs直接のRZ/PauliRotationは符号を反転して渡す。QURI側はQiskitと同符号で構築し、QURIのQulacs変換が反転する。
- XYは既存 `full_xy_block(beta)` の密行列を同じ順のtargetへ作用させる。近接ペアゲート積のTrotter近似へ変えていない。論理深さは密XYを1ゲートと数え、実機native深さとしない。
- 訓練は現行どおり圧縮one-hot tensor＋COBYLA。実機、Aer、noiseは使用しない。今回のadapterの最終抽出は全構成で**現行のQiskit Statevector.sample_counts**を使用し、標本PRNG差を取り除く。前回PCG64 multinomialを使った試験とは区別する。

根拠: [adapters.py](code/adapters.py)、[既存aoa.py](../../../src/kmd_toc/column_generation/aoa.py)、[QURI変換実装](https://github.com/QunaSys/quri-sdk/blob/v0.28.0/quri-parts/packages/qulacs/quri_parts/qulacs/circuit/__init__.py)、[生データ](evidence/backend/)。明示した許容誤差を超えた比較を速度結果へ含めないようassertしている。

## 現行runとの整合性

新規契約テストでは3実行adapterについて、現行runの学習履歴・最適角・最終bit counts・経路・実行可能率の一致を確認した。追加の全体試験は [legacy_parity.json](evidence/legacy_parity.json) に4枝すべての履歴一致を保存した。Qamomileの直接式構築は数学的同等でも浮動小数点の和の順が変わるので、COBYLAの同点近傍の判断まで同一であるとは要求しない。差が生じた場合はQamomileによる品質改善と解釈しない。

容量2・1バース・最大2便の人工6顧客について、4構成の列生成接続契約も通過した。最終3便、D=4.2 km、W=2分、バースピーク1で、別実装の再計算も一致。部分計画の顧客欠落は検証で拒否した。[契約テスト](code/test_contracts.py)、[107件成功ログ](evidence/tests_four_cpu.log)、[binding結果](evidence/binding_contract_quri.json)。

最初の回帰実行は1コアに制限したため「4コアが必要」という既存テスト6件が失敗した。割当を0–3へ直した再実行では107件すべて通過した。失敗ログも `evidence/tests.log` に保全し、性能測定の反復へ数えていない。
