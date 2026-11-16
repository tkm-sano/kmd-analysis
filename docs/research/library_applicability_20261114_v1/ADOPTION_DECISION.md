# 条件Dへの導入判定

2026-11-14 JST。対象: 単一拠点・複数車両・最大2便・バース/容量/勤務制約の配送計画、評価D/W/T。根拠は [ソース監査と11工程対応](ARCHITECTURE_COMPATIBILITY.md)、[公式資料調査](LIBRARY_SURVEY.md)、[プロトコル](BENCHMARK_PROTOCOL.md)、[実測結果](BENCHMARK_RESULTS.md)。

**Qiskitを継続する。QulacsとQURI Partsには最終量子シミュレーション・backend比較に限定した技術的合理性がある。Qamomileにも論文準拠のモデル表現を共通化する学術的合理性はあるが、現行Dの置換やD/W/T改善を正当化する証拠はない。全面移行は推奨しない。**

## 判定

「限定的採用」は独立検証backendとしての役割を指す。本調査で本番依存・既存実装へ導入済みという意味ではない。「採用推奨」に必要な通常D全体の改善は、いずれの新ライブラリでも未確認。

|対象・使い方|分類|根拠と採否の範囲|
|---|---|---|
|Qiskit現行AOA|**継続（既存の比較基準）**|式・tensor同値検査・decoder・監査の既存経路を保つ。現在の顧客集合制限を解決したとみなさない|
|Qulacs CPU 最終状態発展|**限定的採用**|同じexact XYの状態同値を確認し部分時間を短縮。selectionの状態発展中央値5.701→2.274 ms、kernel27.470→23.879 ms。全体DWT T_program/D/Wと最小依存RSSの改善は未確認|
|QURI Parts＋Qulacs|**限定的採用**|同じ回路を表現しbackend抽象化できる。selection状態発展3.588 ms、kernel25.125 ms。複数実行基盤比較に役立つがQulacsへの変換費を含む。直接Qulacsより速いとは言わない|
|Qamomile BinaryModel/Isingの限定併用|**継続調査**|QUBO/Isingの全基底同値と接続動作を確認。selection変換追加2.447 ms、kernel30.270 msで改善なし。モデル共有・論文対照が必要な場合の候補に留める|
|Qamomile標準QAOA/FQAOAへの全面置換|**不採用（現時点）**|標準X mixer/plus、FQAOAの粒子数保存は現行位置別exact XYとは異なる。公平な置換にはcustom回路設計と再検証が必要。全面移行による改善は未測定|
|Qamomile QRAO/PCE/GAS/QSVT等|**継続調査（別アルゴリズム）**|機能は存在するが探索空間/回路/rounding/予算を変える。配送での有効性・実行可能率・RC改善は未測定|
|QURI Algo|**不採用（今回のD）**|汎用量子アルゴリズム部品はあるが、現在の配送AOAを置換する追加の利点は確認できない|
|QURI VM|**継続調査**|デバイス/FTQC資源の分析には適合する。推定latencyを実測T_programと混同しない。現在のD/W/T改善は未測定|
|QURI Parts cuQuantum|**継続調査**|GPU用の公開接続を確認。今回のCPU同条件から外れる。GPUを含む別資源条件の実測が必要|
|Quration/PyQret|**継続調査（資源研究のみ）**|FTQCコンパイル/資源推定の補助。QunaSys orgのforkを同社単独製としない。現行配送生成の性能証拠はない|
|QSCI・化学Parts・ActiveSpaceFinder・QURI Chemistry|**不採用**|用途は電子/分子/化学計算。配送制約・day Pricingの直接機能ではない。QSCIは独自source available license。EV制約を対象外とする本研究への導入理由なし|
|Qurs・Qulacs Visualizer・qiskit-qube-backend|**不採用（最適化経路への導入）**|それぞれRust実装/図/校正試作。現在の配送AOAの計算・品質を改善する根拠なし|
|Quket・QuantestPy|**採用対象から除外**|QunaSysの現行提供物という一次資料上の帰属は未確認。Quketは化学用途、検証ライブラリも既存同値検査に追加する有効性が未実証|

時間は1つの人工入力、5 seedsの探索的中央値である。ホスト共有、サブms固定費、学習が共通という範囲を超えて優越性を主張しない。macroではkernel中央値がQiskit23.577 ms、Qulacs21.792 ms、QURI22.626 ms、Qamomile併用24.297 msだった。小pipelineの順位はケースによって変わり、いずれも全件IP距離2.1 km・W0分で改善なし。

## 3案の比較

|評価項目|案1 Qiskit継続|案2 Qamomile|案3 QURI Parts / Qulacs|
|---|---|---|---|
|機能適合性|現行one-hot XYを実装済み|Ising表現は適合。標準converterへの単純置換不可|同じ回路と状態発展を実装・検証できた|
|経路生成能力|小規模AOAは集合/順序選択可能。通常DWT受理条件は集合固定|同じ符号化なら同じ範囲。導入だけで集合を広げない|同じ符号化なら同じ範囲。通常macroでは集合変更0|
|制約表現|one-hotはmixer、容量/重複はpenalty＋decode、運行は古典完成|OMMXの変換は利用可能だが、ALiMや各制約の同値を要確認|汎用回路/演算子。配送制約処理は従来どおり必要|
|計算時間|比較基準。学習は既にNumPy/SciPy|式変換併用は追加費のみ。全面custom回路未測定|最終状態発展の部分短縮を実測。D全体未測定|
|解品質|今回の基準|同じenergy/回路では同じ結果|同じ角度/共通samplingで同じ結果|
|計算資源|q6/12、statevector16×2^q|Isingだけではqubit/探索空間を削減しない|同じstatevectorサイズ。最小構成RSS・大規模資源優位は未確認|
|実装変更量|新規SDK導入は不要。計測とドメイン改善は別作業|式変換のみなら小、custom qkernel＋全面移行は複数層の再設計|最終実行adapterは限定的。4枝ログ・依存・回帰検査まで含めると複数ファイル|
|再現性|既存lock/seed/量子会計を継続|0.15.2固定が必要。main/0.16系API差が大きい|0.28.0/0.6.14固定、rotation符号・bit順・PRNGを保存|
|保守性|既存契約テスト・独立実装がある|upstreamテスト/日本語資料はあるがactive API変更あり|upstreamテスト/SDK統合がある。adapter/shot API更新に注意|
|研究上の妥当性|比較条件を保ちアルゴリズム差を調べやすい|Huang論文のモデル構築との対照に有益。ライブラリ変更を量子優位としない|実行基盤の感度/クロスチェックに有益。simulator高速化は量子優位の証拠ではない|

変更量は作業範囲による定性的評価。実装していない本番移行の行数・工数を数値で作らない。

## 判定の主要根拠

- 現行実装: `column_generation/aoa.py:123–200,223–285`（式/XY/学習/最終Statevector）、`dwt/methods.py:223–268`（固定双対、全断片受理）、`vehicle_day/master.py:41–47`（真RC）、`pipeline/hybrid.py:103–128`（有限poolのLP反復）、`dwt/parallel.py:226–315`（T_program境界）。詳しいリンク・差分は [監査](ARCHITECTURE_COMPATIBILITY.md)。
- [Huangら §IV](https://arxiv.org/html/2503.17051v1) はQamomile/ALiM、QURI Parts実装を明記。学術的な対照理由はあるが、この配送問題におけるSDK比較試験ではない。
- [Qamomile QAOA回路](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/circuit/algorithm/qaoa.py) は標準X mixer。FQAOAを同じXYと扱わない。[公式依存](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/pyproject.toml) のQiskit要求>=2.3は現行2.1.1と異なる。
- [QURI Parts Qulacs回路接続](https://github.com/QunaSys/quri-sdk/tree/v0.28.0/quri-parts/packages/qulacs/quri_parts/qulacs)、[Qulacs公式](https://github.com/qulacs/qulacs) の任意unitaryを、独立adapterで同じexact XYへ接続した。
- 40測定すべて成功、同一seedの全案で経路/目的/実行可能率一致。全基底64＋4096のenergy一致、24状態検査、既存runの学習履歴一致を確認した。既存回帰 **41件passed**。性能・等価性・回帰ログは [結果](BENCHMARK_RESULTS.md) に連結した。

## RQ・仮説への影響

RQは総距離D、積込待機W、計画計算時間Tの差とトレードオフである。同じ回路を別の古典simulatorで速く計算する効果は、**条件Dを古典計算機上で模擬する実装効率**の差として報告できる。一方、現行量子アルゴリズムが古典Cより良い経路を探索したことや実機が速いことを示さない。共通samplingを使う今回の品質一致は、実行基盤を替えても同じ理想状態を得られるという整合性確認である。

通常DWTでは元tripの全断片順列のみ採用するため、量子部分は異なる顧客集合を持つ経路を受理しない。小規模selectionでは全SDK共通で7件の集合変更経路を受理できたが、最終D/Wの改善には至らなかった。Huang型の「更新された双対から集合/順序の異なる列を生成する」機構を検証するには、SDKよりもドメインと制御フローを先に研究対象として明示する必要がある。

新ToC研究の仮説の正式な統計的判定条件はこの調査で確定していない。README内の過去EV研究H1〜H3を流用せず、今回の結果で支持/棄却を主張しない。独立需要、外側反復、D_CLASSICAL_CONTROL、同じ資源・wall予算を用いる設計が必要である。

## 次に必要な実装・検証（今回未実施）

1. **アルゴリズムを先に定義:** 通常DWTに対し、異なるseed tripをまたぐ重複しない顧客/fragmentドメイン、部分集合受理、勤務/容量に適合する古典完成を別variantとして設計する。新顧客集合/訪問順/既存列重複/資源完成をログで区別する。
2. **量子CGを明示:** RMP→更新双対→量子Pricing→day完成→全資源の真RC→負列追加→再RMPを交互反復する。量子で見つからない停止を全域非負RCの証明にしない。proxyと真RCの不一致率も測る。
3. **実行基盤を分離:** `column_generation/aoa.py` に最終simulation interfaceを追加する案を作り、Qulacs/QURI adapterをoptionalにする。Qiskit状態チェックを開発時に行い、本番で毎回二重simulationするかを明示してTへ含める。`vehicle_day/pricing.py`, `pipeline/hybrid.py`, `dwt/methods.py` の式/decoder/真RC契約を維持する。
4. **実験会計を接続:** `dwt/{setup,worker,parallel,experiment}.py` と別config/lockにbackend/version、変換/構築/学習/抽出/検証、全枝のseed/PID/affinity/失敗/量子会計を接続する。共通import/待機準備と出力時間を別記し、通常4 branchesの親T_programで比較する。
5. **小規模から比較:** 合成/既存小規模入力でbackendだけの差とドメインだけの差を別軸に比較し、同じ探索空間を古典的に解くcontrolを置く。全候補を同じ停止条件・予算で測り、完了planのD/W/T、未選択枝も含めた資源を保存する。今回の41件回帰と同値契約を拡張する。
6. **Qamomileを再評価する条件:** 共有する定式化が増えて独立Polynomial維持の負担が具体化した場合、またはcustom one-hot XYのbackend共通実装を実測した場合に限定する。0.15.2と0.16系の移行差、公式extraのQiskit更新を隔離環境で検証する。FQAOA/QRAO等は別アルゴリズム実験として比較する。

S1〜S3の実行はこの作業に含めない。既存実装・依存・README・凍結入力・旧結果の変更、commit/pushは実施していない。成果物と検証コード・ログだけをこの独立ディレクトリへ保存した。
