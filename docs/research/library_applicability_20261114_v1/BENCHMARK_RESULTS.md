# 小規模実測結果

実施日: 2026-11-14 JST。40件すべて成功。**Qulacsは同じAOAの最終状態発展を短縮したが、解品質の向上と本研究のT_program改善は確認していない。QamomileのIsing変換併用に性能上の利点は確認できない。**

## 実行環境と証拠

Python 3.11.15、Linux 6.8.0-147-generic x86_64、AMD EPYC 9684X、CPU ID0に固定。native thread1、全案のアドレス空間上限4 GiB。NumPy2.3.1、SciPy1.16.0、Qiskit2.1.1、Qulacs0.6.14、QURI Parts circuit/core/qulacs0.28.0、Qamomile0.15.2。venvは `/tmp/kmd-library-survey-20261114`、全依存は [requirements.lock.txt](evidence/requirements.lock.txt)。既存環境にinstallしていない。

人工4顧客・2車両・2バースのみ。詳細条件は [プロトコル](BENCHMARK_PROTOCOL.md)。40独立プロセス、各案間は逐次。CPU自体は共有ホストであり排他的占有・周波数固定ではない。5 seedsは同じ需要の乱数感度で、独立需要5件ではない。単位時間が短いため順位/速度比を一般化しない。

生データ: [各測定JSON](evidence/measurements/)、[全指標CSV](evidence/benchmark_metrics.csv)、[集計JSON](evidence/benchmark_summary.json)、[PID・実行順・起動時間・stderr](evidence/benchmark_execution.json)、[ハードウェア情報](evidence/benchmark_execution.json)。共通importを計時前に行い、その起動/import/出力込み時間も別記録した。ソースコードの識別はpreservation manifest、測定前のコード/プロトコル識別は [freeze](evidence/protocol_freeze.json)。

## 時間

以下は5 seedsの中央値、単位ms。列ごとの中央値の和は総時間の中央値に一致しない。kernelは学習・回路構築・状態発展・最終sampling・Qamomile式変換。小pipelineは初期RMP・Pricing初期化・day完成・真RC・追加・再LP/IP・日程検証までを含む。本番の親4枝T_programではない。

### macro

|構成|学習|式変換追加|回路構築|状態発展|最終抽出|Pricing kernel|小pipeline|
|---|---:|---:|---:|---:|---:|---:|---:|
|Qiskit|21.5093|0.0000|0.8292|1.1785|0.0388|23.5773|44.2371|
|Qulacs直接|21.2231|0.0000|0.4601|0.0683|0.0412|21.7917|41.0693|
|QURI＋Qulacs|21.3519|0.0000|0.6775|0.5593|0.0402|22.6263|50.4365|
|Qamomile Ising＋Qiskit|21.7894|0.4743|0.7773|1.1636|0.0397|24.2966|44.2782|

|構成|kernel範囲ms|小pipeline範囲ms|最大RSS範囲KiB|プロセスCPU秒の中央値（import込み）|
|---|---:|---:|---:|---:|
|Qiskit|20.042–26.153|38.152–72.030|165888.000–165888.000|0.9231|
|Qulacs直接|18.366–24.813|36.247–96.736|165888.000–165888.000|0.9243|
|QURI＋Qulacs|19.421–25.335|40.189–65.664|165888.000–165888.000|0.9185|
|Qamomile Ising＋Qiskit|20.624–26.250|38.709–70.155|165888.000–165888.000|0.9254|

### selection

|構成|学習|式変換追加|回路構築|状態発展|最終抽出|Pricing kernel|小pipeline|
|---|---:|---:|---:|---:|---:|---:|---:|
|Qiskit|20.4972|0.0000|1.2222|5.7010|0.0497|27.4696|94.5353|
|Qulacs直接|20.8467|0.0000|0.6895|2.2736|0.0488|23.8789|113.5921|
|QURI＋Qulacs|20.5833|0.0000|0.8973|3.5884|0.0490|25.1245|87.6374|
|Qamomile Ising＋Qiskit|20.9356|2.4466|1.1811|5.6716|0.0483|30.2699|103.0813|

|構成|kernel範囲ms|小pipeline範囲ms|最大RSS範囲KiB|プロセスCPU秒の中央値（import込み）|
|---|---:|---:|---:|---:|
|Qiskit|25.819–29.651|86.538–144.521|168960.000–168960.000|0.9676|
|Qulacs直接|22.239–25.520|85.219–138.077|168960.000–168960.000|0.9663|
|QURI＋Qulacs|23.460–26.858|84.426–136.311|168960.000–168960.000|0.9727|
|Qamomile Ising＋Qiskit|28.339–31.831|89.219–208.120|168960.000–168960.000|0.9733|

Qulacs直接は最終状態発展で両ケースの中央値を短縮した。QURI経由では変換・wrapperの時間も含まれる。学習は共有のNumPy tensor/COBYLAなのでSDK変更による高速化対象ではない。小pipelineの順位はkernelの順位と一致しない。Qamomileの追加変換は同じenergyを得る処理で、改善アルゴリズムではない。

最大RSSはfresh workerの共通import込み絶対ピーク。全案で共通の依存を読み込んでいるため、ライブラリを最小構成で使った場合のメモリ優越性を示さない。6/12 qubitsの生statevectorは1024/65536 bytesで、プロセスRSSの大部分はそれ以外。上限4 GiBを使用した量と誤認しない。

## 品質・経路生成・負Reduced Cost

各seedについて4構成の最適化履歴、角度、nfev、共通samplerのcount、受理経路、実行可能率、負RC列数、IP目的、論理深さが**一致**した。下表はQiskit列で全案を代表する。式変換の丸め以外に探索条件の差はない。

|case|seed|実nfev|raw実行可能率|受理異経路|集合変更経路|新規負RC day列|最良raw energy|最良trip代理RC|最良day真RC|最終IP km|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|macro|1101|38|0.782715|2|0|80|-0.600000|-0.000000|-0.600000|2.100000|
|macro|1102|41|0.771973|2|0|80|-0.600000|-0.000000|-0.600000|2.100000|
|macro|1103|34|0.783203|2|0|80|-0.600000|-0.000000|-0.600000|2.100000|
|macro|1104|34|0.686523|2|0|80|-0.600000|-0.000000|-0.600000|2.100000|
|macro|1105|30|0.650146|2|0|80|-0.600000|-0.000000|-0.600000|2.100000|
|selection|1101|31|0.610596|9|7|560|-1.500000|-1.500000|-1.500000|2.100000|
|selection|1102|34|0.645996|9|7|560|-1.500000|-1.500000|-1.500000|2.100000|
|selection|1103|29|0.623535|9|7|560|-1.500000|-1.500000|-1.500000|2.100000|
|selection|1104|32|0.596436|9|7|560|-1.500000|-1.500000|-1.500000|2.100000|
|selection|1105|35|0.557373|9|7|560|-1.500000|-1.500000|-1.500000|2.100000|

raw energyはmacroの全断片受理filterより前のVALID標本を含む。VALID標本の最良energyはこの入力では最良raw値と同じ。trip代理RCはfilter後の受理経路、day真RCは古典partner/車両/時刻を完成後の列の値。これらを同じ目的値として比較しない。負RC day列80/560は、同じ経路でも車両/積込時刻が異なれば別列。既存経路を含む測定tripと古典partner/時刻の組合せも含むので、すべてを量子による新経路改善と帰属しない。

各測定は最大20負列を追加した後LPを再求解しIPを選択。全件、初期LP=更新LP=最終IP=2.1 km、日程検証成功、W=0分。負RC列を見つけてもこの1 batchで最終目的は改善していない。マスターは有限列の選択で、全域最適・完全Pricingの証明ではない。

macro: 6 qubits、one-hot9状態、論理depth15、受理2経路、集合変更0。selection: 12 qubits、one-hot64状態、depth33、受理9経路、集合変更7。この差は**ドメインと受理filterの変更**に起因する。ライブラリの効果ではない。両方とも密XYを1論理ゲートとした深さで、実機native回路深さは未測定。

全40件の訓練shots相当は1,352,000、最終shotsは163,840。すべて古典Statevector/圧縮tensorシミュレーションであり、実機shotsではない。各seed/構成の実nfev×1000を保存し、未選択候補の計算を省いていない。

## 同値検査と既存runの確認

[検査結果](evidence/equivalence_checks.json)、[ログ](evidence/equivalence.log)。Qamomile BinaryModel/Isingと既存Polynomialの全計算基底64＋4096個を比較した。最大energy差はmacro 3.56e−15以下、selection 3.56e−14以下。4角度×3backend×2caseの24状態検査で1−忠実度の絶対値は6.7e−15以下、one-hot漏出は1e−8未満。

既存 `PricingAOA.run()` を両ケースseed1101でそのまま実行し、学習履歴と最適角がadapterと完全一致した。既存の最終 `Statevector.sample_counts` と今回の共通PCG64 samplingは同じ標本列ではない。元runの実行可能率はmacro0.786133/selection0.598633、adapterは0.782715/0.610596。samplerの差による標本変動であり、改善の証拠ではない。元runのtotalは参照値としてJSONに保存し、adapter時間との速度比に使わない。

Qamomile標準 `QAOAConverter` → QURI Parts → Qulacsも同じselection QUBO、p2、固定角、4096 shots、seed1101で実行できた。one-hotに該当した標本は6/4096。標準回路はplus初期状態/X mixerであり、本来one-hot XYの下で使う同じQUBOにはone-hotペナルティを追加していないため、同等問題空間の比較にならない。適切に定式化した標準QAOAの品質評価やQamomileの性能欠陥という結論には使わない。標準converterをそのまま現行Dへ置換できないことの確認である。

## 失敗・未実施項目

- 最初の隔離pip解決では `quri-parts-qiskit==0.28.0` のQiskit>=2.2要求と既存2.1.1が衝突した（[install.log](evidence/install.log)）。そのadapterを外し、直接の回路構築で比較した。Qamomile公式qiskit extraも>=2.3要求なので使用しない。任意の `--no-deps` 強制導入をしていない。成功した導入ログは [install_core.log](evidence/install_core.log)。
- 初回4 GiB制限下のnative solver abort(-6)を [別ログ](evidence/benchmark_execution_resource_attempt.json) に保全した。原因確定には至らないが、独立プロセス内のHiGHS明示threads1 adapter適用後は全40件成功。SciPyのoptions転送warningはstderrに保存した。
- Qamomile custom qkernelによる既存**exact** XY全置換の性能、FQAOA/QRAO/GAS/QSVT、QURI Algo/VM/cuQuantum、GPU、noise、実機は未測定。Qamomile定式化併用試験をこれらの性能実証にしない。
- 通常DWTの4並列全体T_program、S1〜S3、凍結需要/実OD、本研究D/Wの優越性、最小依存構成別RSS、複数ホストでの再現、native hardware depthは未測定。
- 独立需要を使う統計的なRQ/仮説検定は実施していない。5 seedsから信頼区間や有意な優越性を主張しない。

既存の小規模回帰テストは [regression_tests.log](evidence/regression_tests.log)。保全確認は [preservation_check.json](evidence/preservation_check.json)。
